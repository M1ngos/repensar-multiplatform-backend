# app/routers/newsletter.py
"""
Newsletter Router - Handles contact form, subscriptions, and campaign management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response, RedirectResponse
from fastapi.security import HTTPBearer
from sqlmodel import Session
from typing import List, Optional

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.newsletter import SubscriptionStatus, CampaignStatus, RecipientStatus
from app.crud.newsletter import newsletter_crud
from app.services.contact_service import contact_service
from app.services.newsletter_service import newsletter_service
from app.services.campaign_service import campaign_service
from app.schemas.newsletter import (
    # Contact schemas
    ContactFormCreate, ContactSubmission, ContactSubmissionListResponse,
    # Tag schemas
    NewsletterTagCreate, NewsletterTagUpdate, NewsletterTag, NewsletterTagListResponse,
    # Subscriber schemas
    SubscribeRequest, SubscribeResponse, SubscriberCreate, SubscriberUpdate,
    Subscriber, SubscriberSummary, SubscriberListResponse, AddTagsRequest,
    ConfirmationResponse, UnsubscribeResponse,
    # Template schemas
    EmailTemplateCreate, EmailTemplateUpdate, EmailTemplate, EmailTemplateListResponse,
    # Campaign schemas
    CampaignCreate, CampaignUpdate, CampaignScheduleRequest, CampaignTestRequest,
    Campaign, CampaignSummary, CampaignListResponse, CampaignStats,
    CampaignRecipient, CampaignRecipientListResponse,
)

router = APIRouter(
    tags=["newsletter"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()


def require_admin(current_user: User) -> User:
    """Check if user is an admin or staff."""
    if current_user.user_type.name not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action"
        )
    return current_user


# ========================================
# CONTACT FORM ENDPOINTS (Public)
# ========================================

@router.post("/contact", status_code=status.HTTP_201_CREATED)
async def submit_contact_form(
    data: ContactFormCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Submit a contact form from the landing page.

    - Saves submission to database
    - Sends auto-reply to user
    - Notifies admin

    **Permissions**: Public (no authentication required)
    """
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        submission = await contact_service.submit_contact_form(
            db=db,
            data=data,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {"message": "Thank you for your message. We'll get back to you soon!", "id": submission.id}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit contact form: {str(e)}"
        )


# ========================================
# CONTACT FORM ADMIN ENDPOINTS
# ========================================

@router.get("/contact/submissions", response_model=ContactSubmissionListResponse)
def get_contact_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all contact form submissions.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    submissions, total = newsletter_crud.get_contact_submissions(
        db, skip=skip, limit=limit, unread_only=unread_only
    )

    return ContactSubmissionListResponse(
        items=[ContactSubmission.model_validate(s) for s in submissions],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/contact/submissions/{submission_id}", response_model=ContactSubmission)
def get_contact_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific contact submission.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    submission = newsletter_crud.get_contact_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    return ContactSubmission.model_validate(submission)


@router.patch("/contact/submissions/{submission_id}/read", response_model=ContactSubmission)
def mark_submission_read(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a contact submission as read.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    submission = newsletter_crud.mark_submission_read(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    return ContactSubmission.model_validate(submission)


@router.delete("/contact/submissions/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a contact submission.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    if not newsletter_crud.delete_contact_submission(db, submission_id):
        raise HTTPException(status_code=404, detail="Submission not found")


# ========================================
# NEWSLETTER SUBSCRIPTION ENDPOINTS (Public)
# ========================================

@router.post("/newsletter/subscribe", response_model=SubscribeResponse)
async def subscribe_to_newsletter(
    data: SubscribeRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Subscribe to the newsletter (double opt-in).

    A confirmation email will be sent to the provided email address.

    **Permissions**: Public
    """
    try:
        ip_address = request.client.host if request.client else None

        subscriber, is_new = await newsletter_service.subscribe(
            db=db,
            email=data.email,
            name=data.name,
            ip_address=ip_address
        )

        if is_new:
            return SubscribeResponse(
                message="Please check your email to confirm your subscription.",
                requires_confirmation=True
            )
        else:
            return SubscribeResponse(
                message="You are already subscribed to our newsletter.",
                requires_confirmation=False
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process subscription: {str(e)}"
        )


@router.get("/newsletter/confirm/{token}", response_model=ConfirmationResponse)
def confirm_subscription(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Confirm newsletter subscription via token.

    **Permissions**: Public
    """
    subscriber = newsletter_service.confirm_subscription(db, token)

    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired confirmation link. Please try subscribing again."
        )

    return ConfirmationResponse(
        message="Your subscription has been confirmed. Thank you!",
        email=subscriber.email
    )


@router.get("/newsletter/unsubscribe/{token}")
def get_unsubscribe_page(token: str, db: Session = Depends(get_db)):
    """
    Get unsubscribe confirmation page info.

    **Permissions**: Public
    """
    subscriber = newsletter_crud.get_subscriber_by_unsubscribe_token(db, token)

    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid unsubscribe link")

    return {
        "email": subscriber.email,
        "status": subscriber.status.value,
        "message": "Are you sure you want to unsubscribe?"
    }


@router.post("/newsletter/unsubscribe/{token}", response_model=UnsubscribeResponse)
async def unsubscribe_from_newsletter(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Unsubscribe from newsletter via token.

    **Permissions**: Public
    """
    subscriber = await newsletter_service.unsubscribe(db, token)

    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid unsubscribe link"
        )

    return UnsubscribeResponse(
        message="You have been successfully unsubscribed.",
        email=subscriber.email
    )


# ========================================
# SUBSCRIBER MANAGEMENT ENDPOINTS (Admin)
# ========================================

@router.get("/newsletter/subscribers", response_model=SubscriberListResponse)
def get_subscribers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[SubscriptionStatus] = None,
    tag_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all newsletter subscribers with filtering.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    subscribers, total = newsletter_crud.get_subscribers(
        db, skip=skip, limit=limit, status=status, tag_id=tag_id, search=search
    )

    items = []
    for s in subscribers:
        tag_count = newsletter_crud.get_subscriber_tag_count(db, s.id)
        items.append(SubscriberSummary(
            id=s.id,
            email=s.email,
            name=s.name,
            status=s.status,
            subscribed_at=s.subscribed_at,
            tag_count=tag_count
        ))

    return SubscriberListResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("/newsletter/subscribers", response_model=Subscriber, status_code=status.HTTP_201_CREATED)
def create_subscriber(
    data: SubscriberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually add a subscriber (admin only, skips double opt-in).

    **Permissions**: Admin only
    """
    require_admin(current_user)

    # Check if already exists
    existing = newsletter_crud.get_subscriber_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already subscribed"
        )

    subscriber = newsletter_crud.create_subscriber(
        db=db,
        email=data.email,
        name=data.name,
        status=data.status,
        tag_ids=data.tag_ids
    )

    return Subscriber.model_validate(subscriber)


@router.get("/newsletter/subscribers/{subscriber_id}", response_model=Subscriber)
def get_subscriber(
    subscriber_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific subscriber.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    subscriber = newsletter_crud.get_subscriber(db, subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    return Subscriber.model_validate(subscriber)


@router.patch("/newsletter/subscribers/{subscriber_id}", response_model=Subscriber)
def update_subscriber(
    subscriber_id: int,
    data: SubscriberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a subscriber.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    subscriber = newsletter_crud.update_subscriber(db, subscriber_id, data)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    return Subscriber.model_validate(subscriber)


@router.delete("/newsletter/subscribers/{subscriber_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscriber(
    subscriber_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a subscriber.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    if not newsletter_crud.delete_subscriber(db, subscriber_id):
        raise HTTPException(status_code=404, detail="Subscriber not found")


@router.post("/newsletter/subscribers/{subscriber_id}/tags", response_model=Subscriber)
def add_tags_to_subscriber(
    subscriber_id: int,
    data: AddTagsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add tags to a subscriber.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    subscriber = newsletter_crud.add_tags_to_subscriber(db, subscriber_id, data.tag_ids)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    return Subscriber.model_validate(subscriber)


@router.delete("/newsletter/subscribers/{subscriber_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tag_from_subscriber(
    subscriber_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a tag from a subscriber.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    if not newsletter_crud.remove_tag_from_subscriber(db, subscriber_id, tag_id):
        raise HTTPException(status_code=404, detail="Subscriber or tag not found")


# ========================================
# TAG MANAGEMENT ENDPOINTS (Admin)
# ========================================

@router.get("/newsletter/tags", response_model=NewsletterTagListResponse)
def get_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all newsletter tags.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    tags, total = newsletter_crud.get_tags(db)

    items = []
    for t in tags:
        count = newsletter_crud.get_tag_subscriber_count(db, t.id)
        items.append(NewsletterTag(
            id=t.id,
            name=t.name,
            slug=t.slug,
            description=t.description,
            color=t.color,
            created_at=t.created_at,
            subscriber_count=count
        ))

    return NewsletterTagListResponse(items=items, total=total)


@router.post("/newsletter/tags", response_model=NewsletterTag, status_code=status.HTTP_201_CREATED)
def create_tag(
    data: NewsletterTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new tag.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    tag = newsletter_crud.create_tag(db, data)
    return NewsletterTag(
        id=tag.id,
        name=tag.name,
        slug=tag.slug,
        description=tag.description,
        color=tag.color,
        created_at=tag.created_at,
        subscriber_count=0
    )


@router.patch("/newsletter/tags/{tag_id}", response_model=NewsletterTag)
def update_tag(
    tag_id: int,
    data: NewsletterTagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a tag.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    tag = newsletter_crud.update_tag(db, tag_id, data)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    count = newsletter_crud.get_tag_subscriber_count(db, tag.id)
    return NewsletterTag(
        id=tag.id,
        name=tag.name,
        slug=tag.slug,
        description=tag.description,
        color=tag.color,
        created_at=tag.created_at,
        subscriber_count=count
    )


@router.delete("/newsletter/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a tag.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    if not newsletter_crud.delete_tag(db, tag_id):
        raise HTTPException(status_code=404, detail="Tag not found")


# ========================================
# EMAIL TEMPLATE ENDPOINTS (Admin)
# ========================================

@router.get("/newsletter/templates", response_model=EmailTemplateListResponse)
def get_templates(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all email templates.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    templates, total = newsletter_crud.get_templates(db, active_only=active_only)
    return EmailTemplateListResponse(
        items=[EmailTemplate.model_validate(t) for t in templates],
        total=total
    )


@router.post("/newsletter/templates", response_model=EmailTemplate, status_code=status.HTTP_201_CREATED)
def create_template(
    data: EmailTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new email template.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    template = newsletter_crud.create_template(db, data, current_user.id)
    return EmailTemplate.model_validate(template)


@router.get("/newsletter/templates/{template_id}", response_model=EmailTemplate)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific template.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    template = newsletter_crud.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return EmailTemplate.model_validate(template)


@router.patch("/newsletter/templates/{template_id}", response_model=EmailTemplate)
def update_template(
    template_id: int,
    data: EmailTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a template.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    template = newsletter_crud.update_template(db, template_id, data)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return EmailTemplate.model_validate(template)


@router.delete("/newsletter/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a template.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    if not newsletter_crud.delete_template(db, template_id):
        raise HTTPException(status_code=404, detail="Template not found")


# ========================================
# CAMPAIGN ENDPOINTS (Admin)
# ========================================

@router.get("/newsletter/campaigns", response_model=CampaignListResponse)
def get_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[CampaignStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all campaigns.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    campaigns, total = newsletter_crud.get_campaigns(db, skip=skip, limit=limit, status=status)

    items = [CampaignSummary(
        id=c.id,
        name=c.name,
        subject=c.subject,
        status=c.status,
        scheduled_at=c.scheduled_at,
        sent_at=c.sent_at,
        total_recipients=c.total_recipients,
        total_opened=c.total_opened,
        total_clicked=c.total_clicked,
        created_at=c.created_at
    ) for c in campaigns]

    return CampaignListResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("/newsletter/campaigns", response_model=Campaign, status_code=status.HTTP_201_CREATED)
def create_campaign(
    data: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new campaign.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    campaign = newsletter_crud.create_campaign(db, data, current_user.id)
    return Campaign.model_validate(campaign)


@router.get("/newsletter/campaigns/{campaign_id}", response_model=Campaign)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific campaign.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    campaign = newsletter_crud.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return Campaign.model_validate(campaign)


@router.patch("/newsletter/campaigns/{campaign_id}", response_model=Campaign)
def update_campaign(
    campaign_id: int,
    data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a campaign (draft only).

    **Permissions**: Admin only
    """
    require_admin(current_user)

    campaign = newsletter_crud.update_campaign(db, campaign_id, data)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign not found or cannot be updated (not in draft status)"
        )

    return Campaign.model_validate(campaign)


@router.delete("/newsletter/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a campaign (draft only).

    **Permissions**: Admin only
    """
    require_admin(current_user)

    if not newsletter_crud.delete_campaign(db, campaign_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign not found or cannot be deleted (not in draft status)"
        )


@router.post("/newsletter/campaigns/{campaign_id}/schedule", response_model=Campaign)
def schedule_campaign(
    campaign_id: int,
    data: CampaignScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Schedule a campaign for future sending.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    campaign = campaign_service.schedule_campaign(db, campaign_id, data.scheduled_at)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign not found, not in draft status, or scheduled time is invalid"
        )

    return Campaign.model_validate(campaign)


@router.post("/newsletter/campaigns/{campaign_id}/send-now", response_model=Campaign)
async def send_campaign_now(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a campaign immediately.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    campaign = await campaign_service.send_campaign_now(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign not found or cannot be sent"
        )

    return Campaign.model_validate(campaign)


@router.post("/newsletter/campaigns/{campaign_id}/cancel", response_model=Campaign)
def cancel_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a scheduled campaign.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    campaign = newsletter_crud.cancel_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign not found or cannot be cancelled"
        )

    return Campaign.model_validate(campaign)


@router.post("/newsletter/campaigns/{campaign_id}/test")
async def send_test_email(
    campaign_id: int,
    data: CampaignTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a test email for a campaign.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    success = await campaign_service.send_test_email(db, campaign_id, data.test_email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email"
        )

    return {"message": f"Test email sent to {data.test_email}"}


@router.get("/newsletter/campaigns/{campaign_id}/stats", response_model=CampaignStats)
def get_campaign_stats(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed statistics for a campaign.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    stats = campaign_service.get_campaign_stats(db, campaign_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return CampaignStats(**stats)


@router.get("/newsletter/campaigns/{campaign_id}/recipients", response_model=CampaignRecipientListResponse)
def get_campaign_recipients(
    campaign_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[RecipientStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recipients for a campaign with their status.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    recipients, total = newsletter_crud.get_campaign_recipients(
        db, campaign_id, skip=skip, limit=limit, status=status
    )

    items = []
    for r in recipients:
        subscriber = newsletter_crud.get_subscriber(db, r.subscriber_id)
        items.append(CampaignRecipient(
            id=r.id,
            subscriber_email=subscriber.email if subscriber else "Unknown",
            subscriber_name=subscriber.name if subscriber else None,
            status=r.status,
            sent_at=r.sent_at,
            opened_at=r.opened_at,
            clicked_at=r.clicked_at
        ))

    return CampaignRecipientListResponse(items=items, total=total, skip=skip, limit=limit)


# ========================================
# TRACKING ENDPOINTS (Public, no auth)
# ========================================

@router.get("/newsletter/track/open/{token}")
def track_email_open(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Track email open (returns 1x1 transparent pixel).

    **Permissions**: Public (called by email clients)
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    pixel = campaign_service.track_open(
        db, token, ip_address=ip_address, user_agent=user_agent
    )

    return Response(content=pixel, media_type="image/gif")


@router.get("/newsletter/track/click/{token}")
def track_link_click(
    token: str,
    url: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Track link click and redirect to destination.

    **Permissions**: Public (called by email clients)
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    redirect_url = campaign_service.track_click(
        db, token, url, ip_address=ip_address, user_agent=user_agent
    )

    if not redirect_url:
        raise HTTPException(status_code=404, detail="Invalid tracking link")

    return RedirectResponse(url=redirect_url)
