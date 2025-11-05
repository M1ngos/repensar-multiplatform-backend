# Notifications Developer Guide

This guide shows you how to integrate notifications into your code when building new features.

## Quick Start

### 1. Add Notifications to Your Router

```python
# app/routers/your_feature.py
from app.services.notification_service import NotificationService
from app.models.analytics import NotificationType

@router.post("/items/{item_id}/action")
async def perform_action(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Your business logic
    item = get_item(db, item_id)
    item.status = "completed"
    db.commit()

    # Send notification
    await NotificationService.create_notification(
        db=db,
        user_id=item.owner_id,
        title="Action Completed",
        message=f"Your item '{item.name}' has been completed",
        notification_type=NotificationType.success,
        related_project_id=item.project_id  # Optional: link to project
    )

    return {"status": "success"}
```

### 2. Publish Events for Analytics

```python
from app.services.event_bus import get_event_bus, EventType

# After creating notification
try:
    event_bus = get_event_bus()
    await event_bus.publish(
        EventType.CUSTOM_EVENT,  # Add your event type to EventType enum
        {
            "item_id": item_id,
            "action": "completed",
            "user_id": current_user.id
        },
        user_id=item.owner_id
    )
except Exception as e:
    # Don't fail the request if event publishing fails
    logger.error(f"Failed to publish event: {e}")
```

---

## Common Patterns

### Pattern 1: Notify Single User

```python
await NotificationService.create_notification(
    db=db,
    user_id=123,
    title="Title",
    message="Message",
    notification_type=NotificationType.info
)
```

### Pattern 2: Notify Multiple Users

```python
user_ids = [123, 456, 789]

await NotificationService.create_bulk_notifications(
    db=db,
    user_ids=user_ids,
    title="Team Update",
    message="Project status has changed",
    notification_type=NotificationType.info,
    related_project_id=project_id
)
```

### Pattern 3: Conditional Notifications

```python
# Only notify if status changed
if old_status != new_status:
    await NotificationService.create_notification(
        db=db,
        user_id=owner_id,
        title="Status Changed",
        message=f"Status changed from {old_status} to {new_status}",
        notification_type=NotificationType.info
    )
```

### Pattern 4: Notifications with Expiration

```python
from datetime import datetime, timedelta

# Notification expires in 7 days
await NotificationService.create_notification(
    db=db,
    user_id=user_id,
    title="Action Required",
    message="Please review this by end of week",
    notification_type=NotificationType.warning,
    expires_at=datetime.utcnow() + timedelta(days=7)
)
```

### Pattern 5: Silent Notifications (No SSE Broadcast)

```python
# Store in DB but don't broadcast to SSE clients
await NotificationService.create_notification(
    db=db,
    user_id=user_id,
    title="Background Process",
    message="Data sync completed",
    notification_type=NotificationType.info,
    broadcast=False  # Don't send to SSE
)
```

---

## Notification Types

Choose the appropriate type based on the action:

```python
from app.models.analytics import NotificationType

# Info (default) - General information
NotificationType.info

# Success - Positive events (approval, completion)
NotificationType.success

# Warning - Caution required (rejection, conflict, deadline)
NotificationType.warning

# Error - Error notifications (failure, critical issues)
NotificationType.error
```

**Guidelines:**
- ✅ Use `success` for approvals, completions, achievements
- ✅ Use `warning` for rejections, conflicts, upcoming deadlines
- ✅ Use `error` for failures, critical issues requiring attention
- ✅ Use `info` for everything else (assignments, updates, general info)

---

## Getting Notified Users

### Get Team Members

```python
from app.crud.project import project_team_crud

# Get all project team members
team_members = project_team_crud.get_project_team(db, project_id)
user_ids = {member.user_id for member in team_members}

# Send to all team members
await NotificationService.create_bulk_notifications(
    db=db,
    user_ids=list(user_ids),
    title="Project Update",
    message="New milestone completed",
    notification_type=NotificationType.success,
    related_project_id=project_id
)
```

### Get Task Assignees

```python
from app.crud.task import task_volunteer_crud

# Get volunteers assigned to task
volunteer_assignments = task_volunteer_crud.get_task_volunteers(db, task_id)

user_ids = set()
for assignment in volunteer_assignments:
    volunteer = db.get(Volunteer, assignment.volunteer_id)
    if volunteer:
        user_ids.add(volunteer.user_id)

# Also notify task owner
if task.assigned_to_id:
    user_ids.add(task.assigned_to_id)

# Send notifications
for user_id in user_ids:
    await NotificationService.create_notification(
        db=db,
        user_id=user_id,
        title="Task Update",
        message=f"Task '{task.title}' has been updated",
        notification_type=NotificationType.info,
        related_task_id=task_id
    )
```

### Exclude Current User

```python
# Don't notify the user who performed the action
users_to_notify = {member.user_id for member in team_members}
users_to_notify.discard(current_user.id)  # Remove current user

for user_id in users_to_notify:
    await NotificationService.create_notification(...)
```

---

## Publishing Events

### Adding New Event Types

1. **Add to EventType enum:**

```python
# app/services/event_bus.py
class EventType(str, Enum):
    # ... existing events

    # Add your new event
    DOCUMENT_UPLOADED = "document.uploaded"
    COMMENT_ADDED = "comment.added"
    DEADLINE_APPROACHING = "deadline.approaching"
```

2. **Publish the event:**

```python
from app.services.event_bus import get_event_bus, EventType

event_bus = get_event_bus()
await event_bus.publish(
    EventType.DOCUMENT_UPLOADED,
    {
        "document_id": document.id,
        "document_name": document.name,
        "uploaded_by": current_user.id,
        "project_id": project_id
    },
    user_id=project_manager_id
)
```

### Subscribing to Events

```python
# app/main.py or your module
from app.services.event_bus import get_event_bus, EventType

async def handle_document_uploaded(event_payload):
    """Handle document upload events."""
    document_id = event_payload["data"]["document_id"]
    project_id = event_payload["data"]["project_id"]

    # Your custom logic
    print(f"Document {document_id} uploaded to project {project_id}")

    # Maybe send email, update analytics, etc.

# Subscribe during startup
event_bus = get_event_bus()
event_bus.subscribe(EventType.DOCUMENT_UPLOADED, handle_document_uploaded)
```

---

## Tracking Analytics

### Log Activity

```python
from app.services.analytics_service import AnalyticsService

await AnalyticsService.log_activity(
    db=db,
    action="task.assigned",
    description=f"Task {task.id} assigned to volunteer {volunteer.id}",
    user_id=current_user.id,
    task_id=task.id,
    project_id=task.project_id,
    volunteer_id=volunteer.id
)
```

### Record Metrics

```python
from app.services.analytics_service import AnalyticsService
from app.models.analytics import MetricType

# Track volunteer hours
await AnalyticsService.record_metric(
    db=db,
    metric_type=MetricType.volunteer_hours,
    metric_name="Volunteer Hours",
    value=4.5,
    unit="hours",
    volunteer_id=volunteer.id,
    project_id=project.id
)

# Track project progress
await AnalyticsService.record_metric(
    db=db,
    metric_type=MetricType.project_progress,
    metric_name="Project Progress",
    value=75.0,
    unit="percentage",
    project_id=project.id,
    recorded_by_id=current_user.id
)
```

### Use Convenience Functions

```python
from app.services.analytics_service import (
    track_task_completion,
    track_volunteer_hours,
    track_project_progress
)

# Track task completion
await track_task_completion(db, task_id, project_id)

# Track volunteer hours
await track_volunteer_hours(
    db=db,
    volunteer_id=volunteer.id,
    hours=4.5,
    project_id=project.id,
    task_id=task.id
)

# Track project progress
await track_project_progress(
    db=db,
    project_id=project.id,
    progress_percentage=75.0,
    recorded_by_id=current_user.id
)
```

---

## Complete Example: New Feature

Let's add notifications to a hypothetical "Document Upload" feature:

```python
# app/routers/documents.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.analytics import NotificationType
from app.services.notification_service import NotificationService
from app.services.analytics_service import AnalyticsService
from app.services.event_bus import get_event_bus, EventType
from app.crud.project import project_team_crud

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/{project_id}/upload")
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a document to a project."""

    # 1. Verify project exists
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Save file (your storage logic)
    document = save_document(file, project_id, current_user.id)

    # 3. Get team members to notify
    team_members = project_team_crud.get_project_team(db, project_id)
    users_to_notify = {member.user_id for member in team_members}
    users_to_notify.discard(current_user.id)  # Don't notify uploader

    # 4. Send notifications
    await NotificationService.create_bulk_notifications(
        db=db,
        user_ids=list(users_to_notify),
        title="New Document Uploaded",
        message=f'{current_user.name} uploaded "{file.filename}" to {project.name}',
        notification_type=NotificationType.info,
        related_project_id=project_id
    )

    # 5. Log activity
    await AnalyticsService.log_activity(
        db=db,
        action="document.uploaded",
        description=f"Document {file.filename} uploaded",
        user_id=current_user.id,
        project_id=project_id
    )

    # 6. Publish event
    try:
        event_bus = get_event_bus()
        await event_bus.publish(
            EventType.DOCUMENT_UPLOADED,
            {
                "document_id": document.id,
                "filename": file.filename,
                "project_id": project_id,
                "uploaded_by": current_user.id
            }
        )
    except Exception as e:
        # Don't fail request if event fails
        logger.error(f"Failed to publish document upload event: {e}")

    return {
        "message": "Document uploaded successfully",
        "document_id": document.id
    }
```

---

## Testing Your Notifications

### Unit Tests

```python
# tests/test_notifications.py
import pytest
from app.services.notification_service import NotificationService
from app.models.analytics import NotificationType

@pytest.mark.asyncio
async def test_create_notification(db_session, test_user):
    """Test notification creation."""
    notification = await NotificationService.create_notification(
        db=db_session,
        user_id=test_user.id,
        title="Test Notification",
        message="This is a test",
        notification_type=NotificationType.info,
        broadcast=False  # Don't broadcast in tests
    )

    assert notification.id is not None
    assert notification.user_id == test_user.id
    assert notification.title == "Test Notification"
    assert notification.is_read is False

@pytest.mark.asyncio
async def test_bulk_notifications(db_session, test_users):
    """Test bulk notification creation."""
    user_ids = [user.id for user in test_users]

    notifications = await NotificationService.create_bulk_notifications(
        db=db_session,
        user_ids=user_ids,
        title="Bulk Test",
        message="Testing bulk",
        notification_type=NotificationType.info
    )

    assert len(notifications) == len(user_ids)
```

### Integration Tests

```python
# tests/integration/test_notification_api.py
def test_get_notifications(client, auth_headers, test_user):
    """Test notification list endpoint."""
    response = client.get("/notifications", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "notifications" in data
    assert "total" in data
    assert "unread_count" in data

def test_mark_as_read(client, auth_headers, test_notification):
    """Test marking notification as read."""
    response = client.patch(
        f"/notifications/{test_notification.id}/read",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_read"] is True
    assert data["read_at"] is not None
```

---

## Common Pitfalls

### ❌ Don't: Fail Request on Notification Error

```python
# BAD - Request fails if notification fails
await NotificationService.create_notification(...)
```

```python
# GOOD - Catch exceptions, don't fail main request
try:
    await NotificationService.create_notification(...)
except Exception as e:
    logger.error(f"Failed to send notification: {e}")
    # Continue with request
```

### ❌ Don't: Notify the User Who Performed the Action

```python
# BAD - User gets notified of their own action
await NotificationService.create_notification(
    db=db,
    user_id=current_user.id,  # ← Wrong
    title="You updated the project",
    ...
)
```

```python
# GOOD - Notify others, not the actor
users_to_notify = get_team_members(project_id)
users_to_notify.discard(current_user.id)  # Remove actor

for user_id in users_to_notify:
    await NotificationService.create_notification(
        db=db,
        user_id=user_id,
        ...
    )
```

### ❌ Don't: Create Duplicate Notifications

```python
# BAD - Duplicate notifications
for i in range(10):  # Loop with same notification
    await NotificationService.create_notification(...)
```

```python
# GOOD - Use bulk or check for duplicates
await NotificationService.create_bulk_notifications(
    db=db,
    user_ids=unique_user_ids,  # Deduplicate first
    ...
)
```

### ❌ Don't: Spam Users with Notifications

```python
# BAD - Too many notifications
for task in tasks:
    await NotificationService.create_notification(
        title=f"Task {task.id} updated",
        ...
    )
```

```python
# GOOD - Batch or summarize
await NotificationService.create_notification(
    title="Multiple Tasks Updated",
    message=f"{len(tasks)} tasks were updated in project {project.name}",
    ...
)
```

---

## Performance Tips

1. **Use Bulk Operations:**
   ```python
   # Good
   await NotificationService.create_bulk_notifications(user_ids, ...)

   # Bad
   for user_id in user_ids:
       await NotificationService.create_notification(user_id, ...)
   ```

2. **Don't Block on Events:**
   ```python
   try:
       await event_bus.publish(...)
   except Exception:
       pass  # Don't block request
   ```

3. **Use Database Indexes:**
   - Notifications are indexed on `(user_id, is_read, created_at)`
   - Always filter by user_id first

4. **Clean Up Old Notifications:**
   - Set `expires_at` for temporary notifications
   - Background task cleans up every hour

---

## Checklist for New Features

When adding notifications to a new feature:

- [ ] Import `NotificationService` and `NotificationType`
- [ ] Choose appropriate notification type (info/success/warning/error)
- [ ] Determine who should be notified (exclude current user)
- [ ] Add related IDs (project_id, task_id) for context
- [ ] Wrap notification creation in try/except
- [ ] Consider bulk notifications for multiple users
- [ ] Add event publishing for analytics (optional)
- [ ] Log activity for audit trail (optional)
- [ ] Write unit tests for notification logic
- [ ] Test SSE delivery manually

---

## Need Help?

- **API Reference:** See `notifications-api-reference.md`
- **Architecture:** See `real-time-notifications.md`
- **Examples:** Check existing routers (tasks.py, projects.py, volunteers.py)
- **Issues:** https://github.com/repensar/backend/issues
