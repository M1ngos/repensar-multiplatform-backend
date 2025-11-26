# app/models/newsletter.py
from sqlmodel import SQLModel, Field, Relationship, Column, Text, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class SubscriptionStatus(str, Enum):
    pending = "pending"           # Awaiting email confirmation
    active = "active"             # Confirmed and active
    unsubscribed = "unsubscribed" # User unsubscribed
    bounced = "bounced"           # Email bounced
    complained = "complained"     # Marked as spam


class CampaignStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    sending = "sending"
    sent = "sent"
    cancelled = "cancelled"


class RecipientStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    opened = "opened"
    clicked = "clicked"
    bounced = "bounced"
    unsubscribed = "unsubscribed"


# Contact Form Submission
class ContactSubmission(SQLModel, table=True):
    __tablename__ = "contact_submissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    email: str = Field(max_length=255, index=True)
    message: str = Field(sa_column=Column(Text))
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_read: bool = Field(default=False, index=True)
    read_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


# Newsletter Tag for segmentation
class NewsletterTag(SQLModel, table=True):
    __tablename__ = "newsletter_tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True)
    slug: str = Field(max_length=50, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=255)
    color: Optional[str] = Field(default=None, max_length=7)  # Hex color
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    subscribers: List["SubscriberTag"] = Relationship(back_populates="tag")


# Newsletter Subscriber
class Subscriber(SQLModel, table=True):
    __tablename__ = "newsletter_subscribers"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, unique=True, index=True)
    name: Optional[str] = Field(default=None, max_length=100)
    status: SubscriptionStatus = Field(default=SubscriptionStatus.pending, index=True)

    # Optional link to User model
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)

    # Double opt-in
    confirmation_token: Optional[str] = Field(default=None, max_length=255, index=True)
    confirmation_expires: Optional[datetime] = Field(default=None)
    confirmed_at: Optional[datetime] = Field(default=None)

    # Unsubscribe token (secure, never expires)
    unsubscribe_token: str = Field(max_length=255, unique=True, index=True)

    # Tracking
    ip_address: Optional[str] = Field(default=None, max_length=45)
    subscribed_at: datetime = Field(default_factory=datetime.utcnow)
    unsubscribed_at: Optional[datetime] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tags: List["SubscriberTag"] = Relationship(back_populates="subscriber")
    campaign_recipients: List["CampaignRecipient"] = Relationship(back_populates="subscriber")


# Junction table for Subscriber-Tag relationship
class SubscriberTag(SQLModel, table=True):
    __tablename__ = "subscriber_tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    subscriber_id: int = Field(foreign_key="newsletter_subscribers.id", index=True)
    tag_id: int = Field(foreign_key="newsletter_tags.id", index=True)
    added_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    subscriber: Subscriber = Relationship(back_populates="tags")
    tag: NewsletterTag = Relationship(back_populates="subscribers")


# Email Template for reusable newsletter designs
class EmailTemplate(SQLModel, table=True):
    __tablename__ = "email_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    slug: str = Field(max_length=100, unique=True, index=True)
    subject: str = Field(max_length=255)
    html_content: str = Field(sa_column=Column(Text))
    text_content: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Template variables metadata (for documentation/UI)
    variables: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    is_active: bool = Field(default=True, index=True)
    created_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Newsletter Campaign
class Campaign(SQLModel, table=True):
    __tablename__ = "newsletter_campaigns"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    subject: str = Field(max_length=255)
    preview_text: Optional[str] = Field(default=None, max_length=255)

    # Content
    html_content: str = Field(sa_column=Column(Text))
    text_content: Optional[str] = Field(default=None, sa_column=Column(Text))
    template_id: Optional[int] = Field(default=None, foreign_key="email_templates.id")

    # Status and scheduling
    status: CampaignStatus = Field(default=CampaignStatus.draft, index=True)
    scheduled_at: Optional[datetime] = Field(default=None, index=True)
    sent_at: Optional[datetime] = Field(default=None)

    # Targeting
    send_to_all: bool = Field(default=True)
    target_tag_ids: Optional[List[int]] = Field(default=None, sa_column=Column(JSON))

    # Statistics
    total_recipients: int = Field(default=0)
    total_sent: int = Field(default=0)
    total_delivered: int = Field(default=0)
    total_opened: int = Field(default=0)
    total_clicked: int = Field(default=0)
    total_bounced: int = Field(default=0)
    total_unsubscribed: int = Field(default=0)

    # Metadata
    created_by_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    recipients: List["CampaignRecipient"] = Relationship(back_populates="campaign")


# Campaign Recipient for tracking individual sends
class CampaignRecipient(SQLModel, table=True):
    __tablename__ = "campaign_recipients"

    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="newsletter_campaigns.id", index=True)
    subscriber_id: int = Field(foreign_key="newsletter_subscribers.id", index=True)

    status: RecipientStatus = Field(default=RecipientStatus.pending, index=True)
    sent_at: Optional[datetime] = Field(default=None)
    delivered_at: Optional[datetime] = Field(default=None)
    opened_at: Optional[datetime] = Field(default=None)
    clicked_at: Optional[datetime] = Field(default=None)

    # Tracking tokens
    open_token: str = Field(max_length=255, unique=True, index=True)
    click_token: str = Field(max_length=255, unique=True, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    campaign: Campaign = Relationship(back_populates="recipients")
    subscriber: Subscriber = Relationship(back_populates="campaign_recipients")
    link_clicks: List["CampaignLinkClick"] = Relationship(back_populates="recipient")


# Link Click Tracking
class CampaignLinkClick(SQLModel, table=True):
    __tablename__ = "campaign_link_clicks"

    id: Optional[int] = Field(default=None, primary_key=True)
    recipient_id: int = Field(foreign_key="campaign_recipients.id", index=True)
    original_url: str = Field(max_length=2000)
    clicked_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Relationships
    recipient: CampaignRecipient = Relationship(back_populates="link_clicks")
