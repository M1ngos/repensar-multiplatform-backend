# app/services/event_bus.py
"""
Event Bus Service using Redis Pub/Sub for cross-module communication.
Enables decoupled, event-driven architecture for real-time notifications.
"""
import json
import asyncio
import logging
from typing import Callable, Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Supported event types for the application."""
    # Task events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_STATUS_CHANGED = "task.status_changed"
    TASK_COMPLETED = "task.completed"
    TASK_DEADLINE_APPROACHING = "task.deadline_approaching"
    TASK_DEPENDENCY_COMPLETED = "task.dependency_completed"

    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_STATUS_CHANGED = "project.status_changed"
    MILESTONE_COMPLETED = "milestone.completed"
    TEAM_MEMBER_ADDED = "team_member.added"
    TEAM_MEMBER_REMOVED = "team_member.removed"
    ENVIRONMENTAL_METRICS_UPDATED = "environmental_metrics.updated"

    # Volunteer events
    VOLUNTEER_REGISTERED = "volunteer.registered"
    TIMELOG_SUBMITTED = "timelog.submitted"
    TIMELOG_APPROVED = "timelog.approved"
    TIMELOG_REJECTED = "timelog.rejected"
    TRAINING_COMPLETED = "training.completed"
    SKILL_ADDED = "skill.added"

    # Sync events
    SYNC_CONFLICT_DETECTED = "sync.conflict_detected"
    SYNC_CONFLICT_RESOLVED = "sync.conflict_resolved"
    SYNC_COMPLETED = "sync.completed"

    # System events
    NOTIFICATION_CREATED = "notification.created"
    METRIC_RECORDED = "metric.recorded"


class EventBus:
    """
    Event bus for publishing and subscribing to application events.
    Uses Redis pub/sub for distributed event handling across workers.
    """

    def __init__(self, redis_client: Optional[Any] = None):
        """
        Initialize the event bus.

        Args:
            redis_client: Redis connection (optional, falls back to in-memory)
        """
        self.redis = redis_client
        self.subscribers: Dict[EventType, list] = {}
        self._pubsub = None
        self._listener_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize Redis pub/sub if Redis is available."""
        if self.redis:
            try:
                self._pubsub = self.redis.pubsub()
                logger.info("EventBus initialized with Redis pub/sub")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis pub/sub: {e}. Using in-memory events only.")
                self.redis = None

    async def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        user_id: Optional[int] = None
    ):
        """
        Publish an event to all subscribers.

        Args:
            event_type: Type of event being published
            data: Event payload data
            user_id: Optional user ID associated with the event
        """
        event_payload = {
            "event_type": event_type.value,
            "data": data,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Publish to Redis if available
        if self.redis and self._pubsub:
            try:
                channel = f"events:{event_type.value}"
                await self.redis.publish(
                    channel,
                    json.dumps(event_payload, default=str)
                )
                logger.debug(f"Published event {event_type.value} to Redis channel {channel}")
            except Exception as e:
                logger.error(f"Failed to publish event to Redis: {e}")

        # Call local in-memory subscribers
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_payload)
                    else:
                        callback(event_payload)
                except Exception as e:
                    logger.error(f"Error in event subscriber for {event_type}: {e}")

    def subscribe(self, event_type: EventType, callback: Callable):
        """
        Subscribe to an event type with a callback function.

        Args:
            event_type: Event type to subscribe to
            callback: Function to call when event is published (sync or async)
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event {event_type.value}")

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """
        Unsubscribe a callback from an event type.

        Args:
            event_type: Event type to unsubscribe from
            callback: Callback function to remove
        """
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            logger.debug(f"Unsubscribed from event {event_type.value}")

    async def listen_redis_events(self):
        """
        Background task to listen for Redis pub/sub events.
        Should be started as a background task on application startup.
        """
        if not self.redis or not self._pubsub:
            logger.warning("Redis not available, skipping Redis event listener")
            return

        try:
            # Subscribe to all event channels
            for event_type in EventType:
                channel = f"events:{event_type.value}"
                await self._pubsub.subscribe(channel)

            logger.info("Redis event listener started")

            # Listen for messages
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    try:
                        channel = message["channel"].decode("utf-8")
                        event_type_str = channel.replace("events:", "")
                        event_type = EventType(event_type_str)

                        payload = json.loads(message["data"])

                        # Call local subscribers
                        if event_type in self.subscribers:
                            for callback in self.subscribers[event_type]:
                                try:
                                    if asyncio.iscoroutinefunction(callback):
                                        await callback(payload)
                                    else:
                                        callback(payload)
                                except Exception as e:
                                    logger.error(f"Error in Redis event subscriber: {e}")
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
        except Exception as e:
            logger.error(f"Redis event listener error: {e}")

    async def start_listener(self):
        """Start the background Redis event listener."""
        if self.redis and not self._listener_task:
            self._listener_task = asyncio.create_task(self.listen_redis_events())
            logger.info("Redis event listener task started")

    async def stop_listener(self):
        """Stop the background Redis event listener."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None

        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()

        logger.info("Redis event listener stopped")


# Global event bus instance (will be initialized in main.py)
event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    if event_bus is None:
        raise RuntimeError("EventBus not initialized. Call initialize_event_bus() first.")
    return event_bus
