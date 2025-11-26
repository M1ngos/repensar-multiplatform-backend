# app/schemas/newsletter.py
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums (matching models)
class SubscriptionStatus(str, Enum):
    pending = "pending"
    active = "active"
    unsubscribed = "unsubscribed"
    bounced = "bounced"
    complained = "complained"


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


# ============================================================
# Contact Form Schemas
# ============================================================

class ContactFormCreate(BaseModel):
    """Schema for public contact form submission."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=10, max_length=5000)

    @field_validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Name cannot be empty')
        return v.strip()

    @field_validator('message')
    def validate_message(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Message must be at least 10 characters')
        return v.strip()


class ContactSubmission(BaseModel):
    """Schema for contact submission response."""
    id: int
    name: str
    email: str
    message: str
    ip_address: Optional[str]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ContactSubmissionListResponse(BaseModel):
    """Paginated list of contact submissions."""
    items: List[ContactSubmission]
    total: int
    skip: int
    limit: int


# ============================================================
# Newsletter Tag Schemas
# ============================================================

class NewsletterTagBase(BaseModel):
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')


class NewsletterTagCreate(NewsletterTagBase):
    pass


class NewsletterTagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, max_length=7)


class NewsletterTag(NewsletterTagBase):
    id: int
    slug: str
    created_at: datetime
    subscriber_count: int = 0

    class Config:
        from_attributes = True


class NewsletterTagListResponse(BaseModel):
    """List of tags."""
    items: List[NewsletterTag]
    total: int


# ============================================================
# Subscriber Schemas
# ============================================================

class SubscribeRequest(BaseModel):
    """Public subscription request (double opt-in)."""
    email: EmailStr
    name: Optional[str] = Field(None, max_length=100)


class SubscriberCreate(BaseModel):
    """Admin schema to add subscriber manually."""
    email: EmailStr
    name: Optional[str] = Field(None, max_length=100)
    status: SubscriptionStatus = SubscriptionStatus.active
    tag_ids: List[int] = []


class SubscriberUpdate(BaseModel):
    """Admin schema to update subscriber."""
    name: Optional[str] = Field(None, max_length=100)
    status: Optional[SubscriptionStatus] = None
    tag_ids: Optional[List[int]] = None


class SubscriberTagInfo(BaseModel):
    """Lightweight tag info for subscriber."""
    id: int
    name: str
    slug: str
    color: Optional[str]

    class Config:
        from_attributes = True


class Subscriber(BaseModel):
    """Subscriber response."""
    id: int
    email: str
    name: Optional[str]
    status: SubscriptionStatus
    user_id: Optional[int]
    confirmed_at: Optional[datetime]
    subscribed_at: datetime
    unsubscribed_at: Optional[datetime]
    tags: List[SubscriberTagInfo] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriberSummary(BaseModel):
    """Lightweight subscriber for list views."""
    id: int
    email: str
    name: Optional[str]
    status: SubscriptionStatus
    subscribed_at: datetime
    tag_count: int = 0

    class Config:
        from_attributes = True


class SubscriberListResponse(BaseModel):
    """Paginated list of subscribers."""
    items: List[SubscriberSummary]
    total: int
    skip: int
    limit: int


class SubscriberImportResult(BaseModel):
    """Result of bulk import."""
    total_processed: int
    imported: int
    skipped: int
    errors: List[str] = []


class AddTagsRequest(BaseModel):
    """Request to add tags to subscriber."""
    tag_ids: List[int]


# ============================================================
# Email Template Schemas
# ============================================================

class EmailTemplateBase(BaseModel):
    name: str = Field(..., max_length=100)
    subject: str = Field(..., max_length=255)
    html_content: str
    text_content: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None


class EmailTemplateCreate(EmailTemplateBase):
    pass


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    subject: Optional[str] = Field(None, max_length=255)
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class EmailTemplate(EmailTemplateBase):
    id: int
    slug: str
    is_active: bool
    created_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailTemplateListResponse(BaseModel):
    """List of templates."""
    items: List[EmailTemplate]
    total: int


class TemplatePreviewRequest(BaseModel):
    """Request to preview template with sample data."""
    sample_data: Dict[str, Any] = {}


# ============================================================
# Campaign Schemas
# ============================================================

class CampaignBase(BaseModel):
    name: str = Field(..., max_length=255)
    subject: str = Field(..., max_length=255)
    preview_text: Optional[str] = Field(None, max_length=255)
    html_content: str
    text_content: Optional[str] = None


class CampaignCreate(CampaignBase):
    template_id: Optional[int] = None
    send_to_all: bool = True
    target_tag_ids: Optional[List[int]] = None

    @field_validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Campaign name cannot be empty')
        return v.strip()

    @field_validator('subject')
    def validate_subject(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Subject cannot be empty')
        return v.strip()


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    subject: Optional[str] = Field(None, max_length=255)
    preview_text: Optional[str] = Field(None, max_length=255)
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    template_id: Optional[int] = None
    send_to_all: Optional[bool] = None
    target_tag_ids: Optional[List[int]] = None


class CampaignScheduleRequest(BaseModel):
    """Request to schedule a campaign."""
    scheduled_at: datetime

    @field_validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('Scheduled time must be in the future')
        return v


class CampaignTestRequest(BaseModel):
    """Request to send test email."""
    test_email: EmailStr


class Campaign(CampaignBase):
    id: int
    status: CampaignStatus
    template_id: Optional[int]
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    send_to_all: bool
    target_tag_ids: Optional[List[int]]
    total_recipients: int
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_bounced: int
    total_unsubscribed: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignSummary(BaseModel):
    """Lightweight campaign for list views."""
    id: int
    name: str
    subject: str
    status: CampaignStatus
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    total_recipients: int
    total_opened: int
    total_clicked: int
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Paginated list of campaigns."""
    items: List[CampaignSummary]
    total: int
    skip: int
    limit: int


class CampaignStats(BaseModel):
    """Detailed campaign statistics."""
    total_recipients: int
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_bounced: int
    total_unsubscribed: int
    open_rate: float  # percentage
    click_rate: float  # percentage
    bounce_rate: float  # percentage
    unsubscribe_rate: float  # percentage


# ============================================================
# Campaign Recipient Schemas
# ============================================================

class CampaignRecipient(BaseModel):
    """Campaign recipient with status."""
    id: int
    subscriber_email: str
    subscriber_name: Optional[str]
    status: RecipientStatus
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]

    class Config:
        from_attributes = True


class CampaignRecipientListResponse(BaseModel):
    """Paginated list of campaign recipients."""
    items: List[CampaignRecipient]
    total: int
    skip: int
    limit: int


# ============================================================
# Public Response Schemas
# ============================================================

class SubscribeResponse(BaseModel):
    """Response for public subscription."""
    message: str
    requires_confirmation: bool = True


class UnsubscribeResponse(BaseModel):
    """Response for unsubscribe."""
    message: str
    email: str


class ConfirmationResponse(BaseModel):
    """Response for email confirmation."""
    message: str
    email: str
