# app/models/communication.py
from sqlmodel import SQLModel, Field, Relationship, Column, Text, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Message types for different communication scenarios"""
    DIRECT = "direct"  # Direct message between users
    GROUP = "group"  # Group conversation
    ANNOUNCEMENT = "announcement"  # System announcement


class ConversationType(str, Enum):
    """Types of conversations"""
    DIRECT = "direct"  # 1-on-1 conversation
    GROUP = "group"  # Group conversation
    PROJECT = "project"  # Project-related conversation


class Conversation(SQLModel, table=True):
    """Conversations group messages between users"""
    __tablename__ = "conversations"

    id: Optional[int] = Field(default=None, primary_key=True)
    type: str = Field(max_length=20, default=ConversationType.DIRECT, index=True)
    title: Optional[str] = Field(default=None, max_length=200)

    # Related entity IDs (for project conversations, etc.)
    project_id: Optional[int] = Field(default=None, foreign_key="projects.id", index=True)

    is_active: bool = Field(default=True, index=True)
    last_message_at: Optional[datetime] = Field(default=None, index=True)
    created_by_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    messages: List["Message"] = Relationship(back_populates="conversation")
    participants: List["ConversationParticipant"] = Relationship(back_populates="conversation")


class ConversationParticipant(SQLModel, table=True):
    """Tracks participants in a conversation"""
    __tablename__ = "conversation_participants"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Participant status
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    left_at: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True, index=True)

    # Read tracking
    last_read_at: Optional[datetime] = Field(default=None)
    unread_count: int = Field(default=0)

    # Notification preferences for this conversation
    notifications_enabled: bool = Field(default=True)

    # Relationships
    conversation: Conversation = Relationship(back_populates="participants")


class Message(SQLModel, table=True):
    """Individual messages within conversations"""
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id", index=True)
    sender_id: int = Field(foreign_key="users.id", index=True)

    content: str = Field(sa_column=Column(Text))
    message_type: str = Field(default=MessageType.DIRECT, max_length=20)

    # Reply tracking
    reply_to_id: Optional[int] = Field(default=None, foreign_key="messages.id")

    # Attachments (stored as JSON array of file references)
    attachments: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # Message status
    is_edited: bool = Field(default=False)
    edited_at: Optional[datetime] = Field(default=None)
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")
    read_receipts: List["MessageReadReceipt"] = Relationship(back_populates="message")


class MessageReadReceipt(SQLModel, table=True):
    """Tracks who has read which messages"""
    __tablename__ = "message_read_receipts"

    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: int = Field(foreign_key="messages.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    read_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    message: Message = Relationship(back_populates="read_receipts")


class Announcement(SQLModel, table=True):
    """System-wide or targeted announcements"""
    __tablename__ = "announcements"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200, index=True)
    content: str = Field(sa_column=Column(Text))

    created_by_id: int = Field(foreign_key="users.id")

    # Targeting
    target_user_types: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))  # ["admin", "volunteer"]
    target_project_ids: Optional[List[int]] = Field(default=None, sa_column=Column(JSON))  # Specific projects
    target_user_ids: Optional[List[int]] = Field(default=None, sa_column=Column(JSON))  # Specific users

    # Scheduling
    publish_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    expire_at: Optional[datetime] = Field(default=None, index=True)

    # Priority (for sorting)
    priority: int = Field(default=0, ge=0, le=10)  # 0=low, 10=critical

    # Status
    is_published: bool = Field(default=False, index=True)
    is_pinned: bool = Field(default=False)  # Pinned announcements stay at top

    # Attachments
    attachments: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    reads: List["AnnouncementRead"] = Relationship(back_populates="announcement")


class AnnouncementRead(SQLModel, table=True):
    """Tracks who has read announcements"""
    __tablename__ = "announcement_reads"

    id: Optional[int] = Field(default=None, primary_key=True)
    announcement_id: int = Field(foreign_key="announcements.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    read_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    announcement: Announcement = Relationship(back_populates="reads")


class EmailDigestPreference(SQLModel, table=True):
    """User preferences for email digests"""
    __tablename__ = "email_digest_preferences"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)

    # Digest frequency
    enabled: bool = Field(default=True)
    frequency: str = Field(default="daily", max_length=20)  # "daily", "weekly", "never"

    # Preferred delivery time (hour in UTC)
    preferred_hour: int = Field(default=9, ge=0, le=23)  # 9 AM UTC

    # What to include
    include_messages: bool = Field(default=True)
    include_announcements: bool = Field(default=True)
    include_task_updates: bool = Field(default=True)
    include_project_updates: bool = Field(default=True)

    # Last sent
    last_digest_sent_at: Optional[datetime] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)