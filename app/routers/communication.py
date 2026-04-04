# app/routers/communication.py
"""
Communication API routes - messaging, announcements, and email digest preferences.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, and_, or_

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.core.email import EmailCategory, can_send_email
from app.services.notification_service import NotificationCategory
from app.models.user import User
from app.models.analytics import NotificationType
from app.models.communication import (
    Conversation,
    ConversationParticipant,
    Message,
    Announcement,
)
from app.crud.communication import (
    conversation_crud,
    message_crud,
    announcement_crud,
    email_digest_crud,
)
from app.services.notification_service import NotificationService
from app.schemas.communication import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationParticipantResponse,
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessageListResponse,
    MessageReadReceiptResponse,
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementResponse,
    AnnouncementListResponse,
    EmailDigestPreferenceResponse,
    EmailDigestPreferenceUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/communication",
    tags=["communication"],
    responses={404: {"description": "Not found"}},
)


# ============================================
# Conversation Endpoints
# ============================================


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new conversation with participants."""
    # Verify all participant IDs exist
    for user_id in data.participant_ids:
        user = db.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {user_id} not found",
            )

    conversation = conversation_crud.create(db, data, current_user.id)

    # Build response with participants
    return _build_conversation_response(db, conversation, current_user.id)


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all conversations for the current user."""
    skip = (page - 1) * page_size
    conversations = conversation_crud.get_by_user(
        db, current_user.id, skip=skip, limit=page_size
    )

    return [
        _build_conversation_response(db, conv, current_user.id)
        for conv in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific conversation."""
    # Verify participant
    if not conversation_crud.is_participant(db, conversation_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation",
        )

    conversation = conversation_crud.get(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return _build_conversation_response(db, conversation, current_user.id)


@router.delete("/conversations/{conversation_id}")
async def leave_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Leave a conversation (remove self as participant)."""
    if not conversation_crud.is_participant(db, conversation_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation",
        )

    success = conversation_crud.remove_participant(db, conversation_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found",
        )

    return {"message": "Left conversation successfully"}


@router.post("/conversations/{conversation_id}/participants/{user_id}")
async def add_participant(
    conversation_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a participant to a conversation (participants only)."""
    # Verify current user is participant
    if not conversation_crud.is_participant(db, conversation_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation",
        )

    # Verify target user exists
    user = db.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Check if already participant
    if conversation_crud.is_participant(db, conversation_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a participant",
        )

    conversation_crud.add_participant(db, conversation_id, user_id)
    return {"message": "Participant added successfully"}


# ============================================
# Message Endpoints
# ============================================


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message in a conversation."""
    # Verify participant
    if not conversation_crud.is_participant(db, conversation_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation",
        )

    # Verify conversation exists
    conversation = conversation_crud.get(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Set conversation_id from path
    data.conversation_id = conversation_id
    message = message_crud.create(db, data, current_user.id)

    # Create notifications for other participants
    try:
        for participant in conversation.participants:
            if participant.user_id != current_user.id and participant.is_active:
                # Get sender name for notification
                sender_name = current_user.name or "Someone"
                await NotificationService.create_notification(
                    db=db,
                    user_id=participant.user_id,
                    title=f"New message from {sender_name}",
                    message=f"{sender_name}: {message.content[:100]}...",
                    notification_type=NotificationType.info,
                    broadcast=False,  # Don't broadcast, just create notification
                    category=NotificationCategory.GENERAL,  # Messages are general notifications
                )
    except Exception as e:
        # Log error but don't fail the message send
        logger.error(f"Failed to create notifications for message: {e}")

    return _build_message_response(db, message)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessageListResponse,
)
async def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get messages in a conversation with pagination."""
    # Verify participant
    if not conversation_crud.is_participant(db, conversation_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation",
        )

    skip = (page - 1) * page_size
    messages, total = message_crud.get_by_conversation(
        db, conversation_id, skip=skip, limit=page_size
    )

    return MessageListResponse(
        messages=[_build_message_response(db, m) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(skip + len(messages)) < total,
    )


@router.put("/messages/{message_id}")
async def edit_message(
    message_id: int,
    data: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Edit a message (only by sender)."""
    message = message_crud.get(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only edit your own messages",
        )

    updated = message_crud.update(db, message_id, data)
    return _build_message_response(db, updated)


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a message (only by sender)."""
    message = message_crud.get(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own messages",
        )

    message_crud.delete(db, message_id)
    return {"message": "Message deleted"}


@router.put("/conversations/{conversation_id}/messages/{message_id}/read")
async def mark_message_read(
    conversation_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a message as read."""
    if not conversation_crud.is_participant(db, conversation_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation",
        )

    message_crud.mark_as_read(db, conversation_id, message_id, current_user.id)
    return {"message": "Message marked as read"}


# ============================================
# Announcement Endpoints
# ============================================


@router.post(
    "/announcements",
    response_model=AnnouncementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_announcement(
    data: AnnouncementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new announcement (admin only)."""
    if current_user.user_type.name not in ("admin", "staff_member"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create announcements",
        )

    announcement = announcement_crud.create(db, data, current_user.id)
    return _build_announcement_response(db, announcement, current_user.id)


@router.get("/announcements", response_model=AnnouncementListResponse)
async def list_announcements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List published announcements visible to the current user."""
    skip = (page - 1) * page_size
    announcements, total = announcement_crud.get_published(
        db,
        current_user.id,
        current_user.user_type.name,
        skip=skip,
        limit=page_size,
    )

    return AnnouncementListResponse(
        announcements=[
            _build_announcement_response(db, a, current_user.id) for a in announcements
        ],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(skip + len(announcements)) < total,
    )


@router.get("/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific announcement."""
    announcement = announcement_crud.get(db, announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )

    # Mark as read automatically
    announcement_crud.mark_as_read(db, announcement_id, current_user.id)

    return _build_announcement_response(db, announcement, current_user.id)


@router.put("/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: int,
    data: AnnouncementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an announcement (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update announcements",
        )

    announcement = announcement_crud.update(db, announcement_id, data)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )

    return _build_announcement_response(db, announcement, current_user.id)


@router.post(
    "/announcements/{announcement_id}/publish", response_model=AnnouncementResponse
)
async def publish_announcement(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish an announcement (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can publish announcements",
        )

    announcement = announcement_crud.publish(db, announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )

    return _build_announcement_response(db, announcement, current_user.id)


@router.delete("/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an announcement (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete announcements",
        )

    success = announcement_crud.delete(db, announcement_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )

    return {"message": "Announcement deleted"}


# ============================================
# Email Digest Preference Endpoints
# ============================================


@router.get("/email-digest-preferences", response_model=EmailDigestPreferenceResponse)
async def get_digest_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's email digest preferences."""
    prefs = email_digest_crud.get_or_create(db, current_user.id)
    return prefs


@router.put("/email-digest-preferences", response_model=EmailDigestPreferenceResponse)
async def update_digest_preferences(
    data: EmailDigestPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's email digest preferences."""
    update_data = data.model_dump(exclude_unset=True)
    prefs = email_digest_crud.update(db, current_user.id, update_data)
    return prefs


# ============================================
# Helper Functions
# ============================================


def _build_conversation_response(
    db: Session, conversation: Conversation, user_id: int
) -> ConversationResponse:
    """Build conversation response with participant info."""
    # Get participants with user details
    participants = db.exec(
        select(ConversationParticipant, User)
        .join(User, ConversationParticipant.user_id == User.id)
        .where(
            and_(
                ConversationParticipant.conversation_id == conversation.id,
                ConversationParticipant.is_active == True,
            )
        )
    ).all()

    participant_responses = []
    unread_total = 0

    for p, u in participants:
        participant_responses.append(
            ConversationParticipantResponse(
                id=p.id,
                user_id=p.user_id,
                user_name=u.name,
                user_avatar=u.profile_picture,
                joined_at=p.joined_at,
                last_read_at=p.last_read_at,
                unread_count=p.unread_count,
                notifications_enabled=p.notifications_enabled,
            )
        )
        if p.user_id == user_id:
            unread_total = p.unread_count

    return ConversationResponse(
        id=conversation.id,
        type=conversation.type,
        title=conversation.title,
        project_id=conversation.project_id,
        is_active=conversation.is_active,
        last_message_at=conversation.last_message_at,
        created_by_id=conversation.created_by_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        participants=participant_responses,
        unread_total=unread_total,
    )


def _build_message_response(db: Session, message: Message) -> MessageResponse:
    """Build message response with sender info."""
    # Get sender info
    sender = db.exec(select(User).where(User.id == message.sender_id)).first()

    # Get read receipts
    from app.models.communication import MessageReadReceipt

    receipts = db.exec(
        select(MessageReadReceipt).where(MessageReadReceipt.message_id == message.id)
    ).all()

    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        content=message.content,
        message_type=message.message_type,
        reply_to_id=message.reply_to_id,
        attachments=message.attachments,
        is_edited=message.is_edited,
        edited_at=message.edited_at,
        is_deleted=message.is_deleted,
        created_at=message.created_at,
        read_receipts=[
            MessageReadReceiptResponse(
                id=r.id,
                message_id=r.message_id,
                user_id=r.user_id,
                read_at=r.read_at,
            )
            for r in receipts
        ],
        sender_name=sender.name if sender else None,
        sender_avatar=sender.profile_picture if sender else None,
    )


def _build_announcement_response(
    db: Session, announcement: Announcement, user_id: int
) -> AnnouncementResponse:
    """Build announcement response with read status and creator info."""
    # Get creator
    creator = db.exec(select(User).where(User.id == announcement.created_by_id)).first()

    # Check if read
    is_read = announcement_crud.is_read_by_user(db, announcement.id, user_id)

    return AnnouncementResponse(
        id=announcement.id,
        title=announcement.title,
        content=announcement.content,
        created_by_id=announcement.created_by_id,
        target_user_types=announcement.target_user_types,
        target_project_ids=announcement.target_project_ids,
        target_user_ids=announcement.target_user_ids,
        publish_at=announcement.publish_at,
        expire_at=announcement.expire_at,
        priority=announcement.priority,
        is_published=announcement.is_published,
        is_pinned=announcement.is_pinned,
        attachments=announcement.attachments,
        created_at=announcement.created_at,
        updated_at=announcement.updated_at,
        is_read=is_read,
        creator_name=creator.name if creator else None,
    )
