# app/crud/communication.py
"""
CRUD operations for messaging, announcements, and email digest preferences.
"""

from sqlmodel import Session, select, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.communication import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageReadReceipt,
    Announcement,
    AnnouncementRead,
    EmailDigestPreference,
)
from app.models.user import User
from app.schemas.communication import (
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
    MessageUpdate,
    AnnouncementCreate,
    AnnouncementUpdate,
    EmailDigestPreferenceBase,
)


class ConversationCRUD:
    """CRUD operations for conversations."""

    def create(
        self,
        db: Session,
        data: ConversationCreate,
        created_by_id: int,
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            type=data.type.value,
            title=data.title,
            project_id=data.project_id,
            created_by_id=created_by_id,
            last_message_at=datetime.utcnow(),
        )
        db.add(conversation)
        db.flush()  # Get conversation.id

        # Add creator as first participant
        participant = ConversationParticipant(
            conversation_id=conversation.id,
            user_id=created_by_id,
            last_read_at=datetime.utcnow(),
        )
        db.add(participant)

        # Add other participants
        for user_id in data.participant_ids:
            if user_id != created_by_id:  # Don't duplicate creator
                p = ConversationParticipant(
                    conversation_id=conversation.id,
                    user_id=user_id,
                )
                db.add(p)

        db.commit()
        db.refresh(conversation)
        return conversation

    def get(self, db: Session, conversation_id: int) -> Optional[Conversation]:
        """Get conversation by ID."""
        return db.exec(
            select(Conversation).where(Conversation.id == conversation_id)
        ).first()

    def get_with_participants(
        self, db: Session, conversation_id: int
    ) -> Optional[Conversation]:
        """Get conversation with participants."""
        return db.exec(
            select(Conversation).where(Conversation.id == conversation_id)
        ).first()

    def get_by_user(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Conversation]:
        """Get all conversations for a user."""
        query = (
            select(Conversation)
            .join(ConversationParticipant)
            .where(
                and_(
                    ConversationParticipant.user_id == user_id,
                    ConversationParticipant.is_active == True,
                    Conversation.is_active == True,
                )
            )
            .order_by(Conversation.last_message_at.desc().nullslast())
            .offset(skip)
            .limit(limit)
        )
        return list(db.exec(query).all())

    def count_by_user(self, db: Session, user_id: int) -> int:
        """Count conversations for a user."""
        query = (
            select(func.count(Conversation.id))
            .join(ConversationParticipant)
            .where(
                and_(
                    ConversationParticipant.user_id == user_id,
                    ConversationParticipant.is_active == True,
                    Conversation.is_active == True,
                )
            )
        )
        return db.exec(query).one()

    def is_participant(self, db: Session, conversation_id: int, user_id: int) -> bool:
        """Check if user is a participant."""
        query = select(ConversationParticipant).where(
            and_(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.is_active == True,
            )
        )
        return db.exec(query).first() is not None

    def add_participant(
        self, db: Session, conversation_id: int, user_id: int
    ) -> ConversationParticipant:
        """Add a participant to a conversation."""
        participant = ConversationParticipant(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        db.add(participant)
        db.commit()
        db.refresh(participant)
        return participant

    def remove_participant(
        self, db: Session, conversation_id: int, user_id: int
    ) -> bool:
        """Remove a participant from a conversation."""
        query = select(ConversationParticipant).where(
            and_(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
        )
        participant = db.exec(query).first()
        if participant:
            participant.is_active = False
            participant.left_at = datetime.utcnow()
            db.add(participant)
            db.commit()
            return True
        return False

    def update(
        self,
        db: Session,
        conversation_id: int,
        data: ConversationUpdate,
    ) -> Optional[Conversation]:
        """Update a conversation."""
        conversation = self.get(db, conversation_id)
        if not conversation:
            return None

        if data.title is not None:
            conversation.title = data.title
        if data.is_active is not None:
            conversation.is_active = data.is_active

        conversation.updated_at = datetime.utcnow()
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    def get_unread_count(self, db: Session, conversation_id: int, user_id: int) -> int:
        """Get unread message count for a user in a conversation."""
        query = select(ConversationParticipant).where(
            and_(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
        )
        participant = db.exec(query).first()
        return participant.unread_count if participant else 0


class MessageCRUD:
    """CRUD operations for messages."""

    def create(
        self,
        db: Session,
        data: MessageCreate,
        sender_id: int,
    ) -> Message:
        """Create a new message."""
        message = Message(
            conversation_id=data.conversation_id,
            sender_id=sender_id,
            content=data.content,
            message_type=data.message_type.value,
            reply_to_id=data.reply_to_id,
            attachments=data.attachments,
        )
        db.add(message)

        # Update conversation's last_message_at
        conversation = db.exec(
            select(Conversation).where(Conversation.id == data.conversation_id)
        ).first()
        if conversation:
            conversation.last_message_at = datetime.utcnow()

        # Update unread count for other participants
        participants = db.exec(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == data.conversation_id,
                    ConversationParticipant.user_id != sender_id,
                    ConversationParticipant.is_active == True,
                )
            )
        ).all()
        for p in participants:
            p.unread_count += 1

        db.commit()
        db.refresh(message)
        return message

    def get(self, db: Session, message_id: int) -> Optional[Message]:
        """Get message by ID."""
        return db.exec(select(Message).where(Message.id == message_id)).first()

    def get_by_conversation(
        self,
        db: Session,
        conversation_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[Message], int]:
        """Get messages for a conversation with pagination."""
        base_query = select(Message).where(
            and_(
                Message.conversation_id == conversation_id,
                Message.is_deleted == False,
            )
        )
        total = db.exec(select(func.count()).select_from(base_query.subquery())).one()

        query = base_query.order_by(Message.created_at.desc()).offset(skip).limit(limit)
        messages = list(db.exec(query).all())
        messages.reverse()  # Oldest first
        return messages, total

    def update(
        self,
        db: Session,
        message_id: int,
        data: MessageUpdate,
    ) -> Optional[Message]:
        """Update a message (edit)."""
        message = self.get(db, message_id)
        if not message:
            return None

        if data.content is not None:
            message.content = data.content
            message.is_edited = True
            message.edited_at = datetime.utcnow()

        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def delete(self, db: Session, message_id: int) -> bool:
        """Soft delete a message."""
        message = self.get(db, message_id)
        if not message:
            return False

        message.is_deleted = True
        message.deleted_at = datetime.utcnow()
        db.add(message)
        db.commit()
        return True

    def mark_as_read(
        self, db: Session, conversation_id: int, message_id: int, user_id: int
    ) -> bool:
        """Mark a message as read."""
        # Check for existing receipt
        existing = db.exec(
            select(MessageReadReceipt).where(
                and_(
                    MessageReadReceipt.message_id == message_id,
                    MessageReadReceipt.user_id == user_id,
                )
            )
        ).first()

        if not existing:
            receipt = MessageReadReceipt(
                message_id=message_id,
                user_id=user_id,
            )
            db.add(receipt)

        # Update participant's last_read_at and reset unread
        participant = db.exec(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
        ).first()
        if participant:
            participant.last_read_at = datetime.utcnow()
            participant.unread_count = 0
            db.add(participant)

        db.commit()
        return True


class AnnouncementCRUD:
    """CRUD operations for announcements."""

    def create(
        self,
        db: Session,
        data: AnnouncementCreate,
        created_by_id: int,
    ) -> Announcement:
        """Create a new announcement."""
        announcement = Announcement(
            title=data.title,
            content=data.content,
            created_by_id=created_by_id,
            target_user_types=data.target_user_types,
            target_project_ids=data.target_project_ids,
            target_user_ids=data.target_user_ids,
            publish_at=data.publish_at or datetime.utcnow(),
            expire_at=data.expire_at,
            priority=data.priority,
            is_pinned=data.is_pinned,
            is_published=data.is_published,
            attachments=data.attachments,
        )
        db.add(announcement)
        db.commit()
        db.refresh(announcement)
        return announcement

    def get(self, db: Session, announcement_id: int) -> Optional[Announcement]:
        """Get announcement by ID."""
        return db.exec(
            select(Announcement).where(Announcement.id == announcement_id)
        ).first()

    def get_published(
        self,
        db: Session,
        user_id: int,
        user_type: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Announcement], int]:
        """Get published announcements visible to a user."""
        now = datetime.utcnow()

        base_query = select(Announcement).where(
            and_(
                Announcement.is_published == True,
                Announcement.publish_at <= now,
                or_(
                    Announcement.expire_at == None,
                    Announcement.expire_at > now,
                ),
            )
        )

        # Filter by targeting (if no targeting, it's for everyone)
        # Handle JSON columns properly - use cast to text for comparison
        from sqlalchemy import cast, Text, or_ as sql_or_, and_ as sql_and_

        targeting_filter = sql_or_(
            Announcement.target_user_types == None,
            cast(Announcement.target_user_types, Text).in_(["[]", "null", ""]),
            cast(Announcement.target_user_types, Text).like(f'%"{user_type}"%'),
            cast(Announcement.target_user_ids, Text).like(f'%"{user_id}"%'),
        )
        base_query = base_query.where(targeting_filter)

        total = db.exec(select(func.count()).select_from(base_query.subquery())).one()

        query = (
            base_query.order_by(
                Announcement.is_pinned.desc(),
                Announcement.priority.desc(),
                Announcement.publish_at.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(db.exec(query).all()), total

    def update(
        self,
        db: Session,
        announcement_id: int,
        data: AnnouncementUpdate,
    ) -> Optional[Announcement]:
        """Update an announcement."""
        announcement = self.get(db, announcement_id)
        if not announcement:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(announcement, field, value)

        announcement.updated_at = datetime.utcnow()
        db.add(announcement)
        db.commit()
        db.refresh(announcement)
        return announcement

    def publish(self, db: Session, announcement_id: int) -> Optional[Announcement]:
        """Publish an announcement."""
        announcement = self.get(db, announcement_id)
        if not announcement:
            return None

        announcement.is_published = True
        announcement.publish_at = datetime.utcnow()
        announcement.updated_at = datetime.utcnow()
        db.add(announcement)
        db.commit()
        db.refresh(announcement)
        return announcement

    def delete(self, db: Session, announcement_id: int) -> bool:
        """Delete an announcement."""
        announcement = self.get(db, announcement_id)
        if not announcement:
            return False

        db.delete(announcement)
        db.commit()
        return True

    def is_read_by_user(self, db: Session, announcement_id: int, user_id: int) -> bool:
        """Check if user has read an announcement."""
        query = select(AnnouncementRead).where(
            and_(
                AnnouncementRead.announcement_id == announcement_id,
                AnnouncementRead.user_id == user_id,
            )
        )
        return db.exec(query).first() is not None

    def mark_as_read(self, db: Session, announcement_id: int, user_id: int) -> bool:
        """Mark an announcement as read."""
        if self.is_read_by_user(db, announcement_id, user_id):
            return True

        read = AnnouncementRead(
            announcement_id=announcement_id,
            user_id=user_id,
        )
        db.add(read)
        db.commit()
        return True


class EmailDigestPreferenceCRUD:
    """CRUD operations for email digest preferences."""

    def get_or_create(self, db: Session, user_id: int) -> EmailDigestPreference:
        """Get or create preferences for a user."""
        query = select(EmailDigestPreference).where(
            EmailDigestPreference.user_id == user_id
        )
        prefs = db.exec(query).first()

        if not prefs:
            prefs = EmailDigestPreference(user_id=user_id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)

        return prefs

    def get(self, db: Session, user_id: int) -> Optional[EmailDigestPreference]:
        """Get preferences for a user."""
        return db.exec(
            select(EmailDigestPreference).where(
                EmailDigestPreference.user_id == user_id
            )
        ).first()

    def update(
        self,
        db: Session,
        user_id: int,
        data: Dict[str, Any],
    ) -> Optional[EmailDigestPreference]:
        """Update preferences."""
        prefs = self.get_or_create(db, user_id)

        for field, value in data.items():
            if hasattr(prefs, field) and value is not None:
                setattr(prefs, field, value)

        prefs.updated_at = datetime.utcnow()
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
        return prefs


# Singleton instances
conversation_crud = ConversationCRUD()
message_crud = MessageCRUD()
announcement_crud = AnnouncementCRUD()
email_digest_crud = EmailDigestPreferenceCRUD()
