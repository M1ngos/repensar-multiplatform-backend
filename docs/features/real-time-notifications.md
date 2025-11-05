# Real-Time Notifications Feature

## Overview

The Real-Time Notifications system enables instant delivery of notifications to users through Server-Sent Events (SSE) with fallback to REST API polling. The system is built on an event-driven architecture using Redis pub/sub for scalability across multiple servers.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Actions                             │
│  (Task assigned, Project updated, Time log approved, etc.)  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  API Endpoints                               │
│  /tasks, /projects, /volunteers, /sync                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              NotificationService                             │
│  • Creates notification in database                          │
│  • Publishes event to EventBus                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  EventBus                                    │
│  • Redis Pub/Sub (distributed)                              │
│  • In-memory fallback (single server)                       │
│  • Event broadcasting to all subscribers                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 SSEManager                                   │
│  • Manages active SSE connections                            │
│  • Multi-device/tab support per user                        │
│  • Heartbeat every 30s                                      │
│  • Broadcasts to specific users or all                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Web Clients (SSE)                               │
│  EventSource connection receiving real-time updates         │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. NotificationService (`app/services/notification_service.py`)

Central service for all notification operations.

**Key Methods:**
- `create_notification()` - Create and broadcast a notification
- `create_bulk_notifications()` - Send to multiple users
- `get_user_notifications()` - Get paginated notifications
- `mark_as_read()` - Mark notification as read
- `mark_all_as_read()` - Mark all notifications as read
- `cleanup_expired_notifications()` - Remove expired notifications

**Example Usage:**
```python
from app.services.notification_service import NotificationService
from app.models.analytics import NotificationType

# Create a notification
await NotificationService.create_notification(
    db=db,
    user_id=123,
    title="Task Assigned",
    message='You have been assigned to task: "Build API"',
    notification_type=NotificationType.info,
    related_task_id=456,
    related_project_id=789
)
```

### 2. EventBus (`app/services/event_bus.py`)

Event-driven communication system using Redis pub/sub.

**Supported Events:**
```python
class EventType(str, Enum):
    # Task events
    TASK_ASSIGNED = "task.assigned"
    TASK_STATUS_CHANGED = "task.status_changed"
    TASK_COMPLETED = "task.completed"

    # Project events
    PROJECT_STATUS_CHANGED = "project.status_changed"
    MILESTONE_COMPLETED = "milestone.completed"
    TEAM_MEMBER_ADDED = "team_member.added"

    # Volunteer events
    TIMELOG_APPROVED = "timelog.approved"
    TIMELOG_REJECTED = "timelog.rejected"

    # Sync events
    SYNC_CONFLICT_DETECTED = "sync.conflict_detected"
    SYNC_CONFLICT_RESOLVED = "sync.conflict_resolved"

    # System events
    NOTIFICATION_CREATED = "notification.created"
```

**Example Usage:**
```python
from app.services.event_bus import get_event_bus, EventType

event_bus = get_event_bus()

# Publish an event
await event_bus.publish(
    EventType.TASK_ASSIGNED,
    {
        "task_id": 456,
        "task_title": "Build API",
        "user_id": 123,
        "assigned_by": 789
    },
    user_id=123
)

# Subscribe to events
def handle_task_assigned(event_payload):
    print(f"Task assigned: {event_payload}")

event_bus.subscribe(EventType.TASK_ASSIGNED, handle_task_assigned)
```

### 3. SSEManager (`app/core/sse_manager.py`)

Manages Server-Sent Events connections for real-time delivery.

**Features:**
- Multiple connections per user (different devices/tabs)
- Automatic heartbeat (30s interval)
- Stale connection cleanup (5 min timeout)
- Connection pool management

**Example Usage:**
```python
from app.core.sse_manager import get_sse_manager

sse_manager = get_sse_manager()

# Broadcast to specific user
await sse_manager.broadcast_to_user(
    user_id=123,
    event_type="notification",
    data={
        "id": 1,
        "title": "New Task",
        "message": "You have a new task"
    }
)

# Broadcast to all users
await sse_manager.broadcast_to_all(
    event_type="system_announcement",
    data={"message": "System maintenance in 1 hour"}
)
```

### 4. AnalyticsService (`app/services/analytics_service.py`)

Tracks metrics and activity logs automatically.

**Key Methods:**
- `log_activity()` - Log user actions
- `record_metric()` - Record metric snapshots
- `track_task_completion()` - Track task metrics
- `track_volunteer_hours()` - Track volunteer hours
- `track_project_progress()` - Track project progress

**Example Usage:**
```python
from app.services.analytics_service import track_volunteer_hours

# Automatically track when time log is approved
await track_volunteer_hours(
    db=db,
    volunteer_id=123,
    hours=4.5,
    project_id=789,
    task_id=456
)
```

## API Endpoints

### REST Endpoints

#### Get Notifications
```http
GET /notifications?unread_only=false&limit=50&offset=0
Authorization: Bearer {token}

Response 200:
{
  "notifications": [
    {
      "id": 1,
      "user_id": 123,
      "title": "Task Assigned",
      "message": "You have been assigned to task: \"Build API\"",
      "type": "info",
      "related_project_id": 789,
      "related_task_id": 456,
      "is_read": false,
      "created_at": "2025-11-05T10:00:00Z"
    }
  ],
  "total": 10,
  "limit": 50,
  "offset": 0,
  "unread_count": 3
}
```

#### Get Unread Count
```http
GET /notifications/unread-count
Authorization: Bearer {token}

Response 200:
{
  "unread_count": 3
}
```

#### Mark as Read
```http
PATCH /notifications/1/read
Authorization: Bearer {token}

Response 200:
{
  "id": 1,
  "is_read": true,
  "read_at": "2025-11-05T10:30:00Z"
}
```

#### Mark All as Read
```http
POST /notifications/mark-all-read
Authorization: Bearer {token}

Response 200:
{
  "marked_as_read": 3
}
```

#### Delete Notification
```http
DELETE /notifications/1
Authorization: Bearer {token}

Response 200:
{
  "message": "Notification deleted successfully"
}
```

### Server-Sent Events (SSE)

#### Stream Notifications
```http
GET /notifications/stream
Authorization: Bearer {token}
Accept: text/event-stream

Response: (streaming)
event: connected
data: {"user_id": 123, "connection_id": "abc-123"}

event: notification
data: {"notification_id": 1, "title": "New Task", "message": "..."}

event: ping
data: {"timestamp": "2025-11-05T10:00:00Z"}
```

## Client Integration

### JavaScript/TypeScript

```javascript
// Establish SSE connection
const eventSource = new EventSource('/notifications/stream', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

// Listen for connection
eventSource.addEventListener('connected', (event) => {
  const data = JSON.parse(event.data);
  console.log('Connected:', data.connection_id);
});

// Listen for notifications
eventSource.addEventListener('notification', (event) => {
  const notification = JSON.parse(event.data);

  // Show notification to user
  showNotification(notification.title, notification.message);

  // Update notification badge
  updateUnreadCount();
});

// Listen for heartbeat
eventSource.addEventListener('ping', (event) => {
  console.log('Heartbeat:', event.data);
});

// Handle errors
eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  // Implement exponential backoff reconnection
};

// Close connection when done
eventSource.close();
```

### React Hook Example

```typescript
import { useEffect, useState } from 'react';

interface Notification {
  id: number;
  title: string;
  message: string;
  type: string;
  created_at: string;
}

export function useNotifications(accessToken: string) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!accessToken) return;

    const eventSource = new EventSource('/notifications/stream', {
      headers: { Authorization: `Bearer ${accessToken}` }
    });

    eventSource.addEventListener('notification', (event) => {
      const notification = JSON.parse(event.data);

      // Add to notifications list
      setNotifications(prev => [notification, ...prev]);

      // Increment unread count
      setUnreadCount(prev => prev + 1);

      // Show browser notification
      if (Notification.permission === 'granted') {
        new Notification(notification.title, {
          body: notification.message,
          icon: '/logo.png'
        });
      }
    });

    return () => {
      eventSource.close();
    };
  }, [accessToken]);

  return { notifications, unreadCount };
}
```

## Notification Triggers

### Task Notifications

| Event | Trigger | Recipients | Location |
|-------|---------|-----------|----------|
| Task Assigned | Volunteer assigned to task | Volunteer | `tasks.py:417` |
| Task Status Changed | Task status updated | Assignees, volunteers, project manager | `tasks.py:300` |
| Task Completed | Task marked as completed | All stakeholders | `tasks.py:387` |

### Project Notifications

| Event | Trigger | Recipients | Location |
|-------|---------|-----------|----------|
| Project Status Changed | Project status updated | All team members | `projects.py:255` |
| Team Member Added | User added to project | New team member | `projects.py:411` |
| Milestone Completed | Milestone marked complete | All team members | `projects.py:639` |

### Volunteer Notifications

| Event | Trigger | Recipients | Location |
|-------|---------|-----------|----------|
| Time Log Approved | Manager approves hours | Volunteer | `volunteers.py:620` |
| Time Log Rejected | Manager rejects hours | Volunteer | `volunteers.py:620` |

### Sync Notifications

| Event | Trigger | Recipients | Location |
|-------|---------|-----------|----------|
| Conflict Resolved | User resolves sync conflict | User | `sync.py:646` |

## Database Schema

```sql
-- Notifications table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(20) NOT NULL,  -- info, warning, error, success
    related_project_id INTEGER REFERENCES projects(id),
    related_task_id INTEGER REFERENCES tasks(id),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX ix_notifications_user_read_created
ON notifications (user_id, is_read, created_at);

CREATE INDEX ix_notifications_expires_at
ON notifications (expires_at);

CREATE INDEX ix_notifications_project_id
ON notifications (related_project_id);

CREATE INDEX ix_notifications_task_id
ON notifications (related_task_id);
```

## Configuration

### Environment Variables

```bash
# Redis (required for distributed SSE)
REDIS_URL=redis://localhost:6379

# Notification settings
NOTIFICATION_CLEANUP_INTERVAL=3600  # seconds (1 hour)
SSE_HEARTBEAT_INTERVAL=30  # seconds
SSE_CONNECTION_TIMEOUT=300  # seconds (5 minutes)
```

### Application Settings

```python
# app/core/config.py
class Settings(BaseSettings):
    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379"

    # Notifications
    NOTIFICATION_RETENTION_DAYS: int = 30
    MAX_NOTIFICATIONS_PER_USER: int = 1000
    SSE_HEARTBEAT_INTERVAL: int = 30
```

## Background Tasks

The system includes automatic cleanup tasks:

### Notification Cleanup
- **Frequency:** Every 1 hour
- **Action:** Deletes expired notifications
- **Location:** `app/core/background_tasks.py`

### SSE Connection Cleanup
- **Frequency:** Every 5 minutes
- **Action:** Removes stale connections
- **Location:** `app/core/background_tasks.py`

## Performance Considerations

### Scalability

**Horizontal Scaling:**
- Redis pub/sub allows multiple Uvicorn workers
- SSE connections distributed across workers
- Database queries optimized with composite indexes

**Connection Limits:**
- Each SSE connection is lightweight (< 1KB/connection)
- Can handle 10,000+ concurrent connections per server
- Use load balancer sticky sessions for SSE endpoints

### Database Optimization

**Indexes:**
```sql
-- Most important index for user queries
(user_id, is_read, created_at)  -- Covers 90% of queries

-- Cleanup queries
(expires_at)

-- Join queries
(related_project_id), (related_task_id)
```

**Query Patterns:**
```python
# Good: Uses composite index
SELECT * FROM notifications
WHERE user_id = 123 AND is_read = false
ORDER BY created_at DESC
LIMIT 50;

# Bad: Missing user_id in WHERE clause
SELECT * FROM notifications
WHERE is_read = false
ORDER BY created_at DESC;
```

## Testing

### Unit Tests

```python
# tests/unit/test_notification_service.py
import pytest
from app.services.notification_service import NotificationService

@pytest.mark.asyncio
async def test_create_notification(db_session, test_user):
    notification = await NotificationService.create_notification(
        db=db_session,
        user_id=test_user.id,
        title="Test",
        message="Test message",
        broadcast=False  # Don't broadcast in tests
    )

    assert notification.id is not None
    assert notification.user_id == test_user.id
    assert notification.is_read is False
```

### Integration Tests

```python
# tests/integration/test_sse.py
import pytest
from fastapi.testclient import TestClient

def test_sse_stream(client: TestClient, auth_headers):
    with client.stream("GET", "/notifications/stream", headers=auth_headers) as response:
        # Should receive connected event
        line = next(response.iter_lines())
        assert b"event: connected" in line
```

## Monitoring

### Metrics to Track

1. **Notification Metrics:**
   - Notifications created per minute
   - Average notification delivery time
   - Unread notification count per user

2. **SSE Metrics:**
   - Active SSE connections
   - Connection duration
   - Heartbeat failures

3. **EventBus Metrics:**
   - Events published per minute
   - Event processing time
   - Redis pub/sub latency

### Logging

```python
# Logs to monitor
logger.info(f"Created notification {notification.id} for user {user_id}")
logger.info(f"SSE connection established for user {user_id}")
logger.error(f"Failed to broadcast notification: {error}")
```

## Troubleshooting

### Common Issues

**1. SSE Connection Drops:**
- Check nginx/proxy timeout settings (should be > 5 minutes)
- Verify firewall allows long-lived connections
- Check client reconnection logic

**2. Notifications Not Delivered:**
- Verify Redis is running: `redis-cli ping`
- Check EventBus initialization in logs
- Verify SSEManager is started

**3. Slow Notification Queries:**
- Run `EXPLAIN ANALYZE` on slow queries
- Verify indexes are created: `\d notifications`
- Check notification cleanup is running

**4. Memory Usage Growing:**
- Check for connection leaks in SSEManager
- Verify cleanup tasks are running
- Monitor Redis memory usage

## Future Enhancements

1. **Mobile Push Notifications:**
   - FCM (Firebase Cloud Messaging) for Android
   - APNS (Apple Push Notification Service) for iOS
   - Device tokens already stored in `Device` model

2. **Notification Preferences:**
   - User settings for notification types
   - Digest mode (batch notifications)
   - Do Not Disturb schedules

3. **Rich Notifications:**
   - Action buttons (Approve/Reject inline)
   - Images and attachments
   - Interactive elements

4. **Advanced Features:**
   - Read receipts
   - Notification threading
   - Priority levels
   - Scheduled notifications

## References

- [Server-Sent Events Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [Redis Pub/Sub Documentation](https://redis.io/docs/manual/pubsub/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
