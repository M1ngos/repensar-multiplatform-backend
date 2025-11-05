# app/services/analytics_service.py
"""
Analytics Service for automatic metric tracking and activity logging.
Integrates with EventBus to record metrics when key events occur.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlmodel import Session, select

from app.models.analytics import (
    ActivityLog,
    MetricSnapshot,
    MetricType
)
from app.services.event_bus import EventType, get_event_bus

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for tracking metrics and activity logs."""

    @staticmethod
    async def log_activity(
        db: Session,
        action: str,
        description: Optional[str] = None,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        volunteer_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        broadcast: bool = False
    ) -> ActivityLog:
        """
        Create an activity log entry.

        Args:
            db: Database session
            action: Action performed (e.g., "task.created", "volunteer.registered")
            description: Human-readable description
            user_id: User who performed the action
            project_id: Related project ID
            task_id: Related task ID
            volunteer_id: Related volunteer ID
            old_values: Previous state (for updates)
            new_values: New state (for updates)
            ip_address: IP address of the user
            user_agent: User agent string
            broadcast: Whether to broadcast event (default: False for logs)

        Returns:
            Created ActivityLog object
        """
        activity_log = ActivityLog(
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            volunteer_id=volunteer_id,
            action=action,
            description=description,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )

        db.add(activity_log)
        db.commit()
        db.refresh(activity_log)

        logger.debug(f"Logged activity: {action} - {description}")

        if broadcast:
            try:
                event_bus = get_event_bus()
                await event_bus.publish(
                    EventType.METRIC_RECORDED,
                    {
                        "activity_id": activity_log.id,
                        "action": action,
                        "description": description,
                        "user_id": user_id,
                        "project_id": project_id,
                        "task_id": task_id
                    },
                    user_id=user_id
                )
            except Exception as e:
                logger.error(f"Failed to broadcast activity log: {e}")

        return activity_log

    @staticmethod
    async def record_metric(
        db: Session,
        metric_type: MetricType,
        metric_name: str,
        value: float,
        unit: Optional[str] = None,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        volunteer_id: Optional[int] = None,
        recorded_by_id: Optional[int] = None,
        metric_metadata: Optional[Dict[str, Any]] = None,
        snapshot_date: Optional[datetime] = None
    ) -> MetricSnapshot:
        """
        Record a metric snapshot.

        Args:
            db: Database session
            metric_type: Type of metric
            metric_name: Human-readable metric name
            value: Numeric value
            unit: Unit of measurement (e.g., "hours", "percentage")
            project_id: Related project ID
            task_id: Related task ID
            volunteer_id: Related volunteer ID
            recorded_by_id: User who recorded this metric
            metric_metadata: Additional contextual data
            snapshot_date: Date/time of the snapshot (defaults to now)

        Returns:
            Created MetricSnapshot object
        """
        metric = MetricSnapshot(
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            unit=unit,
            project_id=project_id,
            task_id=task_id,
            volunteer_id=volunteer_id,
            recorded_by_id=recorded_by_id,
            metric_metadata=metric_metadata,
            snapshot_date=snapshot_date or datetime.utcnow()
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        logger.debug(f"Recorded metric: {metric_name} = {value} {unit or ''}")

        # Broadcast metric event
        try:
            event_bus = get_event_bus()
            await event_bus.publish(
                EventType.METRIC_RECORDED,
                {
                    "metric_id": metric.id,
                    "metric_type": metric_type.value,
                    "metric_name": metric_name,
                    "value": value,
                    "unit": unit,
                    "project_id": project_id,
                    "task_id": task_id,
                    "volunteer_id": volunteer_id
                },
                user_id=recorded_by_id
            )
        except Exception as e:
            logger.error(f"Failed to broadcast metric event: {e}")

        return metric

    @staticmethod
    def get_metrics(
        db: Session,
        metric_type: Optional[MetricType] = None,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        volunteer_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MetricSnapshot]:
        """
        Query metrics with filters.

        Args:
            db: Database session
            metric_type: Filter by metric type
            project_id: Filter by project
            task_id: Filter by task
            volunteer_id: Filter by volunteer
            start_date: Start date for time range
            end_date: End date for time range
            limit: Maximum number of results

        Returns:
            List of MetricSnapshot objects
        """
        query = select(MetricSnapshot)

        if metric_type:
            query = query.where(MetricSnapshot.metric_type == metric_type)
        if project_id:
            query = query.where(MetricSnapshot.project_id == project_id)
        if task_id:
            query = query.where(MetricSnapshot.task_id == task_id)
        if volunteer_id:
            query = query.where(MetricSnapshot.volunteer_id == volunteer_id)
        if start_date:
            query = query.where(MetricSnapshot.snapshot_date >= start_date)
        if end_date:
            query = query.where(MetricSnapshot.snapshot_date <= end_date)

        query = query.order_by(MetricSnapshot.snapshot_date.desc()).limit(limit)

        metrics = db.exec(query).all()
        return list(metrics)

    @staticmethod
    def get_activity_logs(
        db: Session,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        volunteer_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[ActivityLog], int]:
        """
        Query activity logs with filters and pagination.

        Args:
            db: Database session
            user_id: Filter by user
            project_id: Filter by project
            task_id: Filter by task
            volunteer_id: Filter by volunteer
            action: Filter by action type
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            Tuple of (activity logs list, total count)
        """
        query = select(ActivityLog)

        if user_id:
            query = query.where(ActivityLog.user_id == user_id)
        if project_id:
            query = query.where(ActivityLog.project_id == project_id)
        if task_id:
            query = query.where(ActivityLog.task_id == task_id)
        if volunteer_id:
            query = query.where(ActivityLog.volunteer_id == volunteer_id)
        if action:
            query = query.where(ActivityLog.action == action)

        # Get total count
        total = len(db.exec(query).all())

        # Add ordering and pagination
        query = query.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit)

        logs = db.exec(query).all()
        return list(logs), total


# Convenience functions for common analytics patterns

async def track_task_completion(db: Session, task_id: int, project_id: Optional[int] = None):
    """Track a task completion metric."""
    return await AnalyticsService.record_metric(
        db=db,
        metric_type=MetricType.task_completion,
        metric_name="Task Completed",
        value=1.0,
        unit="count",
        task_id=task_id,
        project_id=project_id
    )


async def track_volunteer_hours(
    db: Session,
    volunteer_id: int,
    hours: float,
    project_id: Optional[int] = None,
    task_id: Optional[int] = None
):
    """Track volunteer hours worked."""
    return await AnalyticsService.record_metric(
        db=db,
        metric_type=MetricType.volunteer_hours,
        metric_name="Volunteer Hours",
        value=hours,
        unit="hours",
        volunteer_id=volunteer_id,
        project_id=project_id,
        task_id=task_id
    )


async def track_project_progress(
    db: Session,
    project_id: int,
    progress_percentage: float,
    recorded_by_id: Optional[int] = None
):
    """Track project progress percentage."""
    return await AnalyticsService.record_metric(
        db=db,
        metric_type=MetricType.project_progress,
        metric_name="Project Progress",
        value=progress_percentage,
        unit="percentage",
        project_id=project_id,
        recorded_by_id=recorded_by_id
    )


async def log_volunteer_registration(
    db: Session,
    volunteer_id: int,
    user_id: int,
    ip_address: Optional[str] = None
):
    """Log a volunteer registration event."""
    return await AnalyticsService.log_activity(
        db=db,
        action="volunteer.registered",
        description="New volunteer registered",
        user_id=user_id,
        volunteer_id=volunteer_id,
        ip_address=ip_address
    )


async def log_task_assignment(
    db: Session,
    task_id: int,
    volunteer_id: int,
    assigned_by_id: int,
    project_id: Optional[int] = None
):
    """Log a task assignment event."""
    return await AnalyticsService.log_activity(
        db=db,
        action="task.assigned",
        description=f"Task assigned to volunteer",
        user_id=assigned_by_id,
        task_id=task_id,
        volunteer_id=volunteer_id,
        project_id=project_id
    )
