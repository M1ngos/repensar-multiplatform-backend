# app/schemas/communication.py
"""
Communication schemas for messaging, announcements, and email digest preferences.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    DIRECT = "direct"
    GROUP = "group"
    ANNOUNCEMENT = "announcement"


class ConversationType(str, Enum):
    DIRECT = "direct"
    GROUP = "group"
    PROJECT = "project"


# ============================================
# Conversation Schemas
# ============================================


class ConversationBase(BaseModel):
    type: ConversationType = ConversationType.DIRECT
    title: Optional[str] = Field(None, max_length=200)
    project_id: Optional[int] = None


class ConversationCreate(ConversationBase):
    participant_ids: List[int] = Field(
        ..., min_length=1, description="User IDs to add as participants"
    )


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None


class ConversationParticipantResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    joined_at: datetime
    last_read_at: Optional[datetime]
    unread_count: int
    notifications_enabled: bool

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    type: str
    title: Optional[str]
    project_id: Optional[int]
    is_active: bool
    last_message_at: Optional[datetime]
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    participants: List[ConversationParticipantResponse] = []
    unread_total: int = 0

    class Config:
        from_attributes = True


# ============================================
# Message Schemas
# ============================================


class MessageBase(BaseModel):
    content: str = Field(..., min_length=1)
    message_type: MessageType = MessageType.DIRECT
    reply_to_id: Optional[int] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class MessageCreate(MessageBase):
    conversation_id: Optional[int] = None  # Optional since it comes from URL path


class MessageUpdate(BaseModel):
    content: Optional[str] = None


class MessageReadReceiptResponse(BaseModel):
    id: int
    message_id: int
    user_id: int
    read_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    content: str
    message_type: str
    reply_to_id: Optional[int]
    attachments: Optional[List[Dict[str, Any]]]
    is_edited: bool
    edited_at: Optional[datetime]
    is_deleted: bool
    created_at: datetime
    read_receipts: List[MessageReadReceiptResponse] = []
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================
# Announcement Schemas
# ============================================


class AnnouncementBase(BaseModel):
    title: str = Field(..., max_length=200)
    content: str = Field(..., min_length=1)
    target_user_types: Optional[List[str]] = None
    target_project_ids: Optional[List[int]] = None
    target_user_ids: Optional[List[int]] = None
    publish_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    priority: int = Field(0, ge=0, le=10)
    is_pinned: bool = False
    attachments: Optional[List[Dict[str, Any]]] = None


class AnnouncementCreate(AnnouncementBase):
    is_published: bool = False


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_user_types: Optional[List[str]] = None
    target_project_ids: Optional[List[int]] = None
    target_user_ids: Optional[List[int]] = None
    publish_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=0, le=10)
    is_pinned: Optional[bool] = None
    is_published: Optional[bool] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    created_by_id: int
    target_user_types: Optional[List[str]]
    target_project_ids: Optional[List[int]]
    target_user_ids: Optional[List[int]]
    publish_at: datetime
    expire_at: Optional[datetime]
    priority: int
    is_published: bool
    is_pinned: bool
    attachments: Optional[List[Dict[str, Any]]]
    created_at: datetime
    updated_at: datetime
    is_read: bool = False
    creator_name: Optional[str] = None

    class Config:
        from_attributes = True


class AnnouncementListResponse(BaseModel):
    announcements: List[AnnouncementResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================
# Email Digest Preference Schemas
# ============================================


class EmailDigestPreferenceBase(BaseModel):
    enabled: bool = True
    frequency: str = Field("daily", pattern="^(daily|weekly|never)$")
    preferred_hour: int = Field(9, ge=0, le=23)
    include_messages: bool = True
    include_announcements: bool = True
    include_task_updates: bool = True
    include_project_updates: bool = True


class EmailDigestPreferenceCreate(EmailDigestPreferenceBase):
    pass


class EmailDigestPreferenceUpdate(BaseModel):
    enabled: Optional[bool] = None
    frequency: Optional[str] = Field(None, pattern="^(daily|weekly|never)$")
    preferred_hour: Optional[int] = Field(None, ge=0, le=23)
    include_messages: Optional[bool] = None
    include_announcements: Optional[bool] = None
    include_task_updates: Optional[bool] = None
    include_project_updates: Optional[bool] = None


class EmailDigestPreferenceResponse(BaseModel):
    id: int
    user_id: int
    enabled: bool
    frequency: str
    preferred_hour: int
    include_messages: bool
    include_announcements: bool
    include_task_updates: bool
    include_project_updates: bool
    last_digest_sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
