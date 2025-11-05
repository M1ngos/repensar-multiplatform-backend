# app/services/notification_service.py
"""
Notification Service for creating, storing, and delivering notifications.
Integrates with EventBus for real-time delivery via SSE.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlmodel import Session, select, and_, or_

from app.models.analytics import Notification, NotificationType
from app.services.event_bus import EventType, get_event_bus

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications across the application."""

    @staticmethod
    async def create_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.info,
        related_project_id: Optional[int] = None,
        related_task_id: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        broadcast: bool = True
    ) -> Notification:
        """
        Create and store a notification, then broadcast it via EventBus.

        Args:
            db: Database session
            user_id: User to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, error, success)
            related_project_id: Optional related project ID
            related_task_id: Optional related task ID
            expires_at: Optional expiration datetime
            broadcast: Whether to broadcast via EventBus (default: True)

        Returns:
            Created Notification object
        """
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            related_project_id=related_project_id,
            related_task_id=related_task_id,
            expires_at=expires_at,
            is_read=False
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        logger.info(f"Created notification {notification.id} for user {user_id}: {title}")

        # Broadcast to SSE clients via EventBus
        if broadcast:
            try:
                event_bus = get_event_bus()
                await event_bus.publish(
                    EventType.NOTIFICATION_CREATED,
                    {
                        "notification_id": notification.id,
                        "user_id": user_id,
                        "title": title,
                        "message": message,
                        "type": notification_type.value,
                        "related_project_id": related_project_id,
                        "related_task_id": related_task_id,
                        "created_at": notification.created_at.isoformat()
                    },
                    user_id=user_id
                )
            except Exception as e:
                logger.error(f"Failed to broadcast notification: {e}")

        return notification

    @staticmethod
    async def create_bulk_notifications(
        db: Session,
        user_ids: List[int],
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.info,
        related_project_id: Optional[int] = None,
        related_task_id: Optional[int] = None,
        expires_at: Optional[datetime] = None
    ) -> List[Notification]:
        """
        Create notifications for multiple users at once.

        Args:
            db: Database session
            user_ids: List of user IDs to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            related_project_id: Optional related project ID
            related_task_id: Optional related task ID
            expires_at: Optional expiration datetime

        Returns:
            List of created Notification objects
        """
        notifications = []
        for user_id in user_ids:
            notification = await NotificationService.create_notification(
                db=db,
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                related_project_id=related_project_id,
                related_task_id=related_task_id,
                expires_at=expires_at
            )
            notifications.append(notification)

        logger.info(f"Created {len(notifications)} bulk notifications: {title}")
        return notifications

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Notification], int]:
        """
        Get notifications for a user with pagination.

        Args:
            db: Database session
            user_id: User ID
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return
            offset: Offset for pagination

        Returns:
            Tuple of (notifications list, total count)
        """
        # Build query
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read == False)

        # Filter out expired notifications
        query = query.where(
            or_(
                Notification.expires_at == None,
                Notification.expires_at > datetime.utcnow()
            )
        )

        # Get total count
        count_query = query
        total = len(db.exec(count_query).all())

        # Add ordering and pagination
        query = query.order_by(Notification.created_at.desc())
        query = query.offset(offset).limit(limit)

        notifications = db.exec(query).all()

        return list(notifications), total

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        """
        Mark a notification as read.

        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID (for authorization)

        Returns:
            Updated Notification or None if not found/unauthorized
        """
        notification = db.get(Notification, notification_id)

        if not notification or notification.user_id != user_id:
            return None

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.add(notification)
            db.commit()
            db.refresh(notification)
            logger.debug(f"Marked notification {notification_id} as read")

        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Number of notifications marked as read
        """
        query = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        notifications = db.exec(query).all()

        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.add(notification)
            count += 1

        db.commit()
        logger.info(f"Marked {count} notifications as read for user {user_id}")
        return count

    @staticmethod
    def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
        """
        Delete a notification.

        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found/unauthorized
        """
        notification = db.get(Notification, notification_id)

        if not notification or notification.user_id != user_id:
            return False

        db.delete(notification)
        db.commit()
        logger.debug(f"Deleted notification {notification_id}")
        return True

    @staticmethod
    def cleanup_expired_notifications(db: Session) -> int:
        """
        Delete all expired notifications.

        Args:
            db: Database session

        Returns:
            Number of notifications deleted
        """
        query = select(Notification).where(
            and_(
                Notification.expires_at != None,
                Notification.expires_at <= datetime.utcnow()
            )
        )
        expired_notifications = db.exec(query).all()

        count = len(expired_notifications)
        for notification in expired_notifications:
            db.delete(notification)

        db.commit()
        logger.info(f"Cleaned up {count} expired notifications")
        return count

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Count of unread notifications
        """
        query = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
                or_(
                    Notification.expires_at == None,
                    Notification.expires_at > datetime.utcnow()
                )
            )
        )
        notifications = db.exec(query).all()
        return len(notifications)


# Convenience functions for common notification patterns

async def notify_task_assigned(
    db: Session,
    user_id: int,
    task_id: int,
    task_title: str,
    project_id: Optional[int] = None
):
    """Notify a user that they've been assigned to a task."""
    return await NotificationService.create_notification(
        db=db,
        user_id=user_id,
        title="New Task Assignment",
        message=f'You have been assigned to task: "{task_title}"',
        notification_type=NotificationType.info,
        related_task_id=task_id,
        related_project_id=project_id
    )


async def notify_task_status_changed(
    db: Session,
    user_id: int,
    task_id: int,
    task_title: str,
    old_status: str,
    new_status: str,
    project_id: Optional[int] = None
):
    """Notify a user that a task status has changed."""
    return await NotificationService.create_notification(
        db=db,
        user_id=user_id,
        title="Task Status Updated",
        message=f'Task "{task_title}" status changed from {old_status} to {new_status}',
        notification_type=NotificationType.info,
        related_task_id=task_id,
        related_project_id=project_id
    )


async def notify_timelog_approved(
    db: Session,
    user_id: int,
    hours: float,
    project_id: Optional[int] = None
):
    """Notify a volunteer that their time log has been approved."""
    return await NotificationService.create_notification(
        db=db,
        user_id=user_id,
        title="Time Log Approved",
        message=f"{hours} hours of volunteer work have been approved!",
        notification_type=NotificationType.success,
        related_project_id=project_id
    )


async def notify_sync_conflict(
    db: Session,
    user_id: int,
    entity_type: str,
    entity_id: int
):
    """Notify a user about a sync conflict that needs resolution."""
    return await NotificationService.create_notification(
        db=db,
        user_id=user_id,
        title="Sync Conflict Detected",
        message=f"A conflict was detected in {entity_type} (ID: {entity_id}). Please review and resolve.",
        notification_type=NotificationType.warning,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
