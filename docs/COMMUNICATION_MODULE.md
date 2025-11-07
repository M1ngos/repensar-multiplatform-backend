# Communication Module - Technical Specification

## Status
✅ **Database Models**: Complete
✅ **Migrations**: Complete (migration 008)
⏳ **API Endpoints**: Not yet implemented
⏳ **Services**: Not yet implemented

## Overview

The Communication Module provides a comprehensive messaging and announcement system for the Repensar platform. It enables users to communicate through direct messages, group conversations, project-based discussions, and system-wide announcements.

## Database Schema

### Models

#### 1. Conversation
Main container for messages between participants.

**Table**: `conversations`

**Fields**:
- `id` (int, PK): Unique identifier
- `type` (str): Conversation type - "direct", "group", or "project"
- `title` (str, optional): Conversation title (for groups/projects)
- `project_id` (int, FK, optional): Reference to associated project
- `is_active` (bool): Whether conversation is active
- `last_message_at` (datetime): Timestamp of last message
- `created_by_id` (int, FK): User who created the conversation
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

**Relationships**:
- `messages`: List of Message objects
- `participants`: List of ConversationParticipant objects

**Indexes**:
- `type`, `is_active`, `last_message_at`, `created_at`, `project_id`

---

#### 2. ConversationParticipant
Tracks users participating in conversations with read status.

**Table**: `conversation_participants`

**Fields**:
- `id` (int, PK): Unique identifier
- `conversation_id` (int, FK): Reference to conversation
- `user_id` (int, FK): Reference to user
- `joined_at` (datetime): When user joined
- `left_at` (datetime, optional): When user left (if applicable)
- `is_active` (bool): Whether participant is active
- `last_read_at` (datetime, optional): Last read timestamp
- `unread_count` (int): Number of unread messages
- `notifications_enabled` (bool): Whether notifications are enabled

**Relationships**:
- `conversation`: Parent Conversation object

**Indexes**:
- `conversation_id`, `user_id`, `is_active`

**Cascade**: DELETE on conversation deletion

---

#### 3. Message
Individual messages within conversations.

**Table**: `messages`

**Fields**:
- `id` (int, PK): Unique identifier
- `conversation_id` (int, FK): Reference to conversation
- `sender_id` (int, FK): User who sent the message
- `content` (text): Message content
- `message_type` (str): Type - "direct", "group", or "announcement"
- `reply_to_id` (int, FK, optional): Reference to parent message (for threads)
- `attachments` (JSON, optional): Array of file attachments
- `is_edited` (bool): Whether message was edited
- `edited_at` (datetime, optional): Last edit timestamp
- `is_deleted` (bool): Soft delete flag
- `deleted_at` (datetime, optional): Deletion timestamp
- `created_at` (datetime): Creation timestamp

**Relationships**:
- `conversation`: Parent Conversation object
- `read_receipts`: List of MessageReadReceipt objects

**Indexes**:
- `conversation_id`, `sender_id`, `created_at`

**Cascade**: DELETE on conversation deletion

---

#### 4. MessageReadReceipt
Tracks who has read which messages.

**Table**: `message_read_receipts`

**Fields**:
- `id` (int, PK): Unique identifier
- `message_id` (int, FK): Reference to message
- `user_id` (int, FK): User who read the message
- `read_at` (datetime): When message was read

**Relationships**:
- `message`: Parent Message object

**Indexes**:
- `message_id`, `user_id`

**Cascade**: DELETE on message deletion

---

#### 5. Announcement
System-wide or targeted announcements.

**Table**: `announcements`

**Fields**:
- `id` (int, PK): Unique identifier
- `title` (str): Announcement title
- `content` (text): Announcement content
- `created_by_id` (int, FK): User who created the announcement
- `target_user_types` (JSON, optional): Array of user types (e.g., ["admin", "volunteer"])
- `target_project_ids` (JSON, optional): Array of project IDs
- `target_user_ids` (JSON, optional): Array of specific user IDs
- `publish_at` (datetime): When to publish
- `expire_at` (datetime, optional): When announcement expires
- `priority` (int): Priority level (0-10, 0=low, 10=critical)
- `is_published` (bool): Whether announcement is published
- `is_pinned` (bool): Whether announcement is pinned to top
- `attachments` (JSON, optional): Array of file attachments
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

**Relationships**:
- `reads`: List of AnnouncementRead objects

**Indexes**:
- `title`, `publish_at`, `expire_at`, `is_published`

---

#### 6. AnnouncementRead
Tracks who has read announcements.

**Table**: `announcement_reads`

**Fields**:
- `id` (int, PK): Unique identifier
- `announcement_id` (int, FK): Reference to announcement
- `user_id` (int, FK): User who read the announcement
- `read_at` (datetime): When announcement was read

**Relationships**:
- `announcement`: Parent Announcement object

**Indexes**:
- `announcement_id`, `user_id`

**Cascade**: DELETE on announcement deletion

---

#### 7. EmailDigestPreference
User preferences for email digest notifications.

**Table**: `email_digest_preferences`

**Fields**:
- `id` (int, PK): Unique identifier
- `user_id` (int, FK, unique): Reference to user
- `enabled` (bool): Whether digests are enabled
- `frequency` (str): Frequency - "daily", "weekly", or "never"
- `preferred_hour` (int): Hour of day to send (0-23, UTC)
- `include_messages` (bool): Include unread messages
- `include_announcements` (bool): Include new announcements
- `include_task_updates` (bool): Include task updates
- `include_project_updates` (bool): Include project updates
- `last_digest_sent_at` (datetime, optional): Last digest timestamp
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

**Indexes**:
- `user_id` (unique)

---

## Enums

### MessageType
```python
DIRECT = "direct"       # Direct message between users
GROUP = "group"         # Group conversation
ANNOUNCEMENT = "announcement"  # System announcement
```

### ConversationType
```python
DIRECT = "direct"       # 1-on-1 conversation
GROUP = "group"         # Group conversation
PROJECT = "project"     # Project-related conversation
```

---

## Use Cases

### 1. Direct Messaging
- Users can send direct messages to each other
- Support for read receipts
- Message threading (replies)
- Soft delete with history preservation

### 2. Group Conversations
- Multiple participants in a conversation
- Participant management (join/leave)
- Per-user unread counts
- Configurable notifications per conversation

### 3. Project Conversations
- Conversations linked to specific projects
- Automatic participant management based on project team
- Context-aware communication

### 4. Announcements
- System-wide or targeted announcements
- Scheduling (publish_at, expire_at)
- Priority levels for importance
- Pinning critical announcements
- Targeting by user types, projects, or specific users
- Read tracking

### 5. Email Digests
- Configurable digest frequency
- User preferences for content inclusion
- Scheduled delivery at preferred times

---

## Suggested API Endpoints

### Conversations

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/conversations/` | List user's conversations | Yes |
| POST | `/conversations/` | Create new conversation | Yes |
| GET | `/conversations/{id}` | Get conversation details | Yes |
| PUT | `/conversations/{id}` | Update conversation | Yes |
| DELETE | `/conversations/{id}` | Delete/archive conversation | Yes |
| GET | `/conversations/{id}/messages` | List messages in conversation | Yes |
| POST | `/conversations/{id}/participants` | Add participant | Yes |
| DELETE | `/conversations/{id}/participants/{user_id}` | Remove participant | Yes |
| POST | `/conversations/{id}/read` | Mark conversation as read | Yes |

### Messages

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/messages/` | Send new message | Yes |
| GET | `/messages/{id}` | Get message details | Yes |
| PUT | `/messages/{id}` | Edit message | Yes |
| DELETE | `/messages/{id}` | Delete message (soft) | Yes |
| POST | `/messages/{id}/read` | Mark message as read | Yes |
| GET | `/messages/unread/count` | Get unread message count | Yes |

### Announcements

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/announcements/` | List announcements (filtered by target) | Yes |
| POST | `/announcements/` | Create announcement | Yes (admin) |
| GET | `/announcements/{id}` | Get announcement details | Yes |
| PUT | `/announcements/{id}` | Update announcement | Yes (admin) |
| DELETE | `/announcements/{id}` | Delete announcement | Yes (admin) |
| POST | `/announcements/{id}/read` | Mark announcement as read | Yes |
| POST | `/announcements/{id}/publish` | Publish announcement | Yes (admin) |
| POST | `/announcements/{id}/pin` | Pin/unpin announcement | Yes (admin) |

### Email Preferences

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/email-preferences/` | Get user's email preferences | Yes |
| PUT | `/email-preferences/` | Update email preferences | Yes |

---

## Request/Response Examples

### Create Conversation
```json
POST /conversations/
{
  "type": "direct",
  "participant_user_ids": [2, 3]
}

Response:
{
  "id": 1,
  "type": "direct",
  "title": null,
  "is_active": true,
  "created_at": "2025-11-07T10:00:00Z",
  "participants": [
    {"user_id": 1, "is_active": true, "unread_count": 0},
    {"user_id": 2, "is_active": true, "unread_count": 0}
  ]
}
```

### Send Message
```json
POST /messages/
{
  "conversation_id": 1,
  "content": "Hello, how can I help?",
  "reply_to_id": null,
  "attachments": [
    {"type": "file", "url": "/uploads/document.pdf", "name": "document.pdf"}
  ]
}

Response:
{
  "id": 1,
  "conversation_id": 1,
  "sender_id": 1,
  "content": "Hello, how can I help?",
  "message_type": "direct",
  "is_edited": false,
  "is_deleted": false,
  "created_at": "2025-11-07T10:01:00Z",
  "attachments": [...]
}
```

### Create Announcement
```json
POST /announcements/
{
  "title": "System Maintenance",
  "content": "The system will be under maintenance on Saturday.",
  "target_user_types": ["admin", "project_manager"],
  "priority": 8,
  "is_pinned": true,
  "publish_at": "2025-11-07T10:00:00Z",
  "expire_at": "2025-11-10T10:00:00Z"
}

Response:
{
  "id": 1,
  "title": "System Maintenance",
  "content": "The system will be under maintenance on Saturday.",
  "priority": 8,
  "is_published": true,
  "is_pinned": true,
  "created_by_id": 1,
  "created_at": "2025-11-07T09:00:00Z"
}
```

---

## Real-time Considerations

For real-time messaging features, consider implementing:

1. **WebSocket support** for live message delivery
2. **Push notifications** for mobile apps
3. **Online/offline status** tracking
4. **Typing indicators**
5. **Message delivery status** (sent, delivered, read)

---

## Security Considerations

1. **Authorization**: Users can only access conversations they're participants in
2. **Message Privacy**: Soft deletes preserve audit trails while hiding content
3. **Announcement Targeting**: Validate user permissions before showing announcements
4. **Rate Limiting**: Prevent message spam
5. **Content Moderation**: Consider implementing content filtering

---

## File Location

- **Models**: `app/models/communication.py`
- **Migration**: `alembic/versions/008_create_communication_tables.py`
- **Migration ID**: `008`
- **Depends on**: Migration `007`

---

## Next Steps

To complete this module:

1. ✅ Create database models
2. ✅ Create and run migrations
3. ⏳ Implement API routes in `app/routers/communication.py`
4. ⏳ Create service layer in `app/services/communication.py`
5. ⏳ Add schemas in `app/schemas/communication.py`
6. ⏳ Write tests
7. ⏳ Implement real-time WebSocket support (optional)
8. ⏳ Add push notification integration
