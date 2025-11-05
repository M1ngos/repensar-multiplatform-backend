# app/routers/notifications.py
"""
Notifications API with Server-Sent Events (SSE) support for real-time delivery.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from pydantic import BaseModel

from app.core.deps import get_current_user, get_db
from app.core.sse_manager import get_sse_manager
from app.models.user import User
from app.models.analytics import Notification, NotificationType
from app.services.notification_service import NotificationService
from app.services.event_bus import EventType, get_event_bus

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)


# Pydantic schemas for request/response
class NotificationCreate(BaseModel):
    """Schema for creating a notification."""
    user_id: int
    title: str
    message: str
    type: NotificationType = NotificationType.info
    related_project_id: Optional[int] = None
    related_task_id: Optional[int] = None


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: int
    user_id: int
    title: str
    message: str
    type: NotificationType
    related_project_id: Optional[int] = None
    related_task_id: Optional[int] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for paginated notification list."""
    notifications: List[NotificationResponse]
    total: int
    limit: int
    offset: int
    unread_count: int


class MarkAsReadRequest(BaseModel):
    """Schema for marking notification as read."""
    is_read: bool = True


@router.get("/stream")
async def notification_stream(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Server-Sent Events (SSE) endpoint for real-time notifications.

    This endpoint establishes a persistent connection and streams notifications
    as they are created. Clients should listen for 'notification' events.

    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/notifications/stream');

    eventSource.addEventListener('notification', (event) => {
        const notification = JSON.parse(event.data);
        console.log('New notification:', notification);
    });

    eventSource.addEventListener('ping', (event) => {
        console.log('Heartbeat:', event.data);
    });
    ```
    """
    sse_manager = get_sse_manager()
    event_bus = get_event_bus()

    # Generate unique connection ID
    connection_id = str(uuid.uuid4())

    # Register connection
    connection = await sse_manager.connect(current_user.id, connection_id)

    async def event_generator():
        """Generate SSE events for this connection."""
        try:
            # Send initial connection success event
            yield f"event: connected\n"
            yield f"data: {json.dumps({'user_id': current_user.id, 'connection_id': connection_id})}\n\n"

            logger.info(f"SSE stream started for user {current_user.id}")

            # Stream events from the connection queue
            while True:
                try:
                    # Wait for events with timeout to allow periodic checks
                    event = await asyncio.wait_for(connection.queue.get(), timeout=1.0)

                    # Format as SSE
                    event_type = event.get("event", "message")
                    event_data = json.dumps(event.get("data", {}))

                    yield f"event: {event_type}\n"
                    yield f"data: {event_data}\n\n"

                except asyncio.TimeoutError:
                    # No events in queue, continue waiting
                    continue
                except asyncio.CancelledError:
                    logger.info(f"SSE stream cancelled for user {current_user.id}")
                    break

        except Exception as e:
            logger.error(f"Error in SSE stream for user {current_user.id}: {e}")
        finally:
            # Clean up connection
            await sse_manager.disconnect(current_user.id, connection_id)
            logger.info(f"SSE stream closed for user {current_user.id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notifications for the current user with pagination.

    - **unread_only**: If true, only return unread notifications
    - **limit**: Maximum number of notifications to return (default: 50, max: 100)
    - **offset**: Offset for pagination (default: 0)
    """
    # Validate limit
    if limit > 100:
        limit = 100

    # Get notifications
    notifications, total = NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )

    # Get unread count
    unread_count = NotificationService.get_unread_count(db, current_user.id)

    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        limit=limit,
        offset=offset,
        unread_count=unread_count
    )


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the count of unread notifications for the current user."""
    count = NotificationService.get_unread_count(db, current_user.id)
    return {"unread_count": count}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a specific notification as read."""
    notification = NotificationService.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )

    return NotificationResponse.model_validate(notification)


@router.post("/mark-all-read")
async def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read for the current user."""
    count = NotificationService.mark_all_as_read(db, current_user.id)
    return {"marked_as_read": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific notification."""
    deleted = NotificationService.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )

    return {"message": "Notification deleted successfully"}


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific notification by ID."""
    notification = db.get(Notification, notification_id)

    if not notification or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )

    return NotificationResponse.model_validate(notification)


# Admin/System endpoints (for creating notifications programmatically)

@router.post("/create", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a notification (admin/system use).

    Note: In production, this should be restricted to admin users or system processes.
    For regular user-to-user notifications, implement specific endpoints.
    """
    # TODO: Add admin permission check
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Admin access required")

    notification = await NotificationService.create_notification(
        db=db,
        user_id=notification_data.user_id,
        title=notification_data.title,
        message=notification_data.message,
        notification_type=notification_data.type,
        related_project_id=notification_data.related_project_id,
        related_task_id=notification_data.related_task_id
    )

    return NotificationResponse.model_validate(notification)
