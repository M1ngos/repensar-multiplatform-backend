# app/crud/newsletter.py
from sqlmodel import Session, select, func, and_, or_
from typing import List, Optional
from datetime import datetime
import re
import secrets

from app.models.newsletter import (
    ContactSubmission, Subscriber, NewsletterTag, SubscriberTag,
    EmailTemplate, Campaign, CampaignRecipient, CampaignLinkClick,
    SubscriptionStatus, CampaignStatus, RecipientStatus
)
from app.schemas.newsletter import (
    ContactFormCreate, SubscriberCreate, SubscriberUpdate,
    NewsletterTagCreate, NewsletterTagUpdate,
    EmailTemplateCreate, EmailTemplateUpdate,
    CampaignCreate, CampaignUpdate
)


def generate_slug(text: str, db: Session, model_class) -> str:
    """Generate a unique slug from text."""
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')

    original_slug = slug
    counter = 1
    while True:
        existing = db.exec(select(model_class).where(model_class.slug == slug)).first()
        if not existing:
            break
        slug = f"{original_slug}-{counter}"
        counter += 1

    return slug


def generate_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


class NewsletterCRUD:
    # ============================================================
    # Contact Submission Operations
    # ============================================================

    def create_contact_submission(
        self,
        db: Session,
        data: ContactFormCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ContactSubmission:
        """Create a new contact form submission."""
        submission = ContactSubmission(
            name=data.name,
            email=data.email,
            message=data.message,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission

    def get_contact_submission(self, db: Session, submission_id: int) -> Optional[ContactSubmission]:
        """Get contact submission by ID."""
        return db.get(ContactSubmission, submission_id)

    def get_contact_submissions(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False
    ) -> tuple[List[ContactSubmission], int]:
        """Get contact submissions with optional filtering."""
        query = select(ContactSubmission)
        count_query = select(func.count(ContactSubmission.id))

        if unread_only:
            query = query.where(ContactSubmission.is_read == False)
            count_query = count_query.where(ContactSubmission.is_read == False)

        total = db.exec(count_query).first() or 0
        query = query.order_by(ContactSubmission.created_at.desc())
        query = query.offset(skip).limit(limit)

        submissions = db.exec(query).all()
        return list(submissions), total

    def mark_submission_read(self, db: Session, submission_id: int) -> Optional[ContactSubmission]:
        """Mark a contact submission as read."""
        submission = db.get(ContactSubmission, submission_id)
        if not submission:
            return None

        submission.is_read = True
        submission.read_at = datetime.utcnow()
        db.commit()
        db.refresh(submission)
        return submission

    def delete_contact_submission(self, db: Session, submission_id: int) -> bool:
        """Delete a contact submission."""
        submission = db.get(ContactSubmission, submission_id)
        if not submission:
            return False

        db.delete(submission)
        db.commit()
        return True

    # ============================================================
    # Newsletter Tag Operations
    # ============================================================

    def create_tag(self, db: Session, data: NewsletterTagCreate) -> NewsletterTag:
        """Create a new newsletter tag."""
        slug = generate_slug(data.name, db, NewsletterTag)

        tag = NewsletterTag(
            **data.model_dump(),
            slug=slug
        )
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag

    def get_tag(self, db: Session, tag_id: int) -> Optional[NewsletterTag]:
        """Get tag by ID."""
        return db.get(NewsletterTag, tag_id)

    def get_tag_by_slug(self, db: Session, slug: str) -> Optional[NewsletterTag]:
        """Get tag by slug."""
        return db.exec(select(NewsletterTag).where(NewsletterTag.slug == slug)).first()

    def get_tags(self, db: Session) -> tuple[List[NewsletterTag], int]:
        """Get all tags with subscriber counts."""
        query = select(NewsletterTag).order_by(NewsletterTag.name)
        count_query = select(func.count(NewsletterTag.id))

        total = db.exec(count_query).first() or 0
        tags = db.exec(query).all()
        return list(tags), total

    def update_tag(
        self,
        db: Session,
        tag_id: int,
        data: NewsletterTagUpdate
    ) -> Optional[NewsletterTag]:
        """Update a tag."""
        tag = db.get(NewsletterTag, tag_id)
        if not tag:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if 'name' in update_data and update_data['name'] != tag.name:
            update_data['slug'] = generate_slug(update_data['name'], db, NewsletterTag)

        for field, value in update_data.items():
            setattr(tag, field, value)

        db.commit()
        db.refresh(tag)
        return tag

    def delete_tag(self, db: Session, tag_id: int) -> bool:
        """Delete a tag and its associations."""
        tag = db.get(NewsletterTag, tag_id)
        if not tag:
            return False

        # Remove subscriber associations
        for st in db.exec(select(SubscriberTag).where(SubscriberTag.tag_id == tag_id)).all():
            db.delete(st)

        db.delete(tag)
        db.commit()
        return True

    def get_tag_subscriber_count(self, db: Session, tag_id: int) -> int:
        """Get number of subscribers with this tag."""
        return db.exec(
            select(func.count(SubscriberTag.id)).where(SubscriberTag.tag_id == tag_id)
        ).first() or 0

    # ============================================================
    # Subscriber Operations
    # ============================================================

    def create_subscriber(
        self,
        db: Session,
        email: str,
        name: Optional[str] = None,
        status: SubscriptionStatus = SubscriptionStatus.pending,
        ip_address: Optional[str] = None,
        user_id: Optional[int] = None,
        tag_ids: List[int] = []
    ) -> Subscriber:
        """Create a new subscriber."""
        confirmation_token = generate_token() if status == SubscriptionStatus.pending else None
        confirmation_expires = datetime.utcnow() if status == SubscriptionStatus.pending else None

        # Add 24 hours for confirmation expiry
        if confirmation_expires:
            from datetime import timedelta
            confirmation_expires = datetime.utcnow() + timedelta(hours=24)

        subscriber = Subscriber(
            email=email,
            name=name,
            status=status,
            user_id=user_id,
            confirmation_token=confirmation_token,
            confirmation_expires=confirmation_expires,
            unsubscribe_token=generate_token(),
            ip_address=ip_address,
            confirmed_at=datetime.utcnow() if status == SubscriptionStatus.active else None
        )
        db.add(subscriber)
        db.commit()
        db.refresh(subscriber)

        # Add tags
        for tag_id in tag_ids:
            subscriber_tag = SubscriberTag(
                subscriber_id=subscriber.id,
                tag_id=tag_id
            )
            db.add(subscriber_tag)

        if tag_ids:
            db.commit()
            db.refresh(subscriber)

        return subscriber

    def get_subscriber(self, db: Session, subscriber_id: int) -> Optional[Subscriber]:
        """Get subscriber by ID."""
        return db.get(Subscriber, subscriber_id)

    def get_subscriber_by_email(self, db: Session, email: str) -> Optional[Subscriber]:
        """Get subscriber by email."""
        return db.exec(select(Subscriber).where(Subscriber.email == email)).first()

    def get_subscriber_by_confirmation_token(self, db: Session, token: str) -> Optional[Subscriber]:
        """Get subscriber by confirmation token."""
        return db.exec(
            select(Subscriber).where(Subscriber.confirmation_token == token)
        ).first()

    def get_subscriber_by_unsubscribe_token(self, db: Session, token: str) -> Optional[Subscriber]:
        """Get subscriber by unsubscribe token."""
        return db.exec(
            select(Subscriber).where(Subscriber.unsubscribe_token == token)
        ).first()

    def get_subscribers(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[SubscriptionStatus] = None,
        tag_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> tuple[List[Subscriber], int]:
        """Get subscribers with filtering."""
        query = select(Subscriber)
        count_query = select(func.count(Subscriber.id))

        conditions = []

        if status:
            conditions.append(Subscriber.status == status)

        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    Subscriber.email.ilike(search_pattern),
                    Subscriber.name.ilike(search_pattern)
                )
            )

        if tag_id:
            subscriber_ids = db.exec(
                select(SubscriberTag.subscriber_id).where(SubscriberTag.tag_id == tag_id)
            ).all()
            if subscriber_ids:
                conditions.append(Subscriber.id.in_(subscriber_ids))
            else:
                return [], 0

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total = db.exec(count_query).first() or 0
        query = query.order_by(Subscriber.created_at.desc())
        query = query.offset(skip).limit(limit)

        subscribers = db.exec(query).all()
        return list(subscribers), total

    def get_active_subscribers(
        self,
        db: Session,
        tag_ids: Optional[List[int]] = None
    ) -> List[Subscriber]:
        """Get all active subscribers, optionally filtered by tags."""
        query = select(Subscriber).where(Subscriber.status == SubscriptionStatus.active)

        if tag_ids:
            subscriber_ids = db.exec(
                select(SubscriberTag.subscriber_id).where(SubscriberTag.tag_id.in_(tag_ids))
            ).all()
            if subscriber_ids:
                query = query.where(Subscriber.id.in_(subscriber_ids))
            else:
                return []

        return list(db.exec(query).all())

    def update_subscriber(
        self,
        db: Session,
        subscriber_id: int,
        data: SubscriberUpdate
    ) -> Optional[Subscriber]:
        """Update subscriber."""
        subscriber = db.get(Subscriber, subscriber_id)
        if not subscriber:
            return None

        update_data = data.model_dump(exclude_unset=True, exclude={'tag_ids'})

        for field, value in update_data.items():
            setattr(subscriber, field, value)

        subscriber.updated_at = datetime.utcnow()

        # Update tags if provided
        if data.tag_ids is not None:
            # Remove existing tags
            for st in db.exec(select(SubscriberTag).where(SubscriberTag.subscriber_id == subscriber_id)).all():
                db.delete(st)

            # Add new tags
            for tag_id in data.tag_ids:
                subscriber_tag = SubscriberTag(
                    subscriber_id=subscriber_id,
                    tag_id=tag_id
                )
                db.add(subscriber_tag)

        db.commit()
        db.refresh(subscriber)
        return subscriber

    def confirm_subscriber(self, db: Session, subscriber_id: int) -> Optional[Subscriber]:
        """Confirm subscriber's email."""
        subscriber = db.get(Subscriber, subscriber_id)
        if not subscriber:
            return None

        subscriber.status = SubscriptionStatus.active
        subscriber.confirmed_at = datetime.utcnow()
        subscriber.confirmation_token = None
        subscriber.confirmation_expires = None
        subscriber.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(subscriber)
        return subscriber

    def unsubscribe(self, db: Session, subscriber_id: int) -> Optional[Subscriber]:
        """Unsubscribe a subscriber."""
        subscriber = db.get(Subscriber, subscriber_id)
        if not subscriber:
            return None

        subscriber.status = SubscriptionStatus.unsubscribed
        subscriber.unsubscribed_at = datetime.utcnow()
        subscriber.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(subscriber)
        return subscriber

    def delete_subscriber(self, db: Session, subscriber_id: int) -> bool:
        """Delete subscriber."""
        subscriber = db.get(Subscriber, subscriber_id)
        if not subscriber:
            return False

        # Remove tag associations
        for st in db.exec(select(SubscriberTag).where(SubscriberTag.subscriber_id == subscriber_id)).all():
            db.delete(st)

        db.delete(subscriber)
        db.commit()
        return True

    def add_tags_to_subscriber(
        self,
        db: Session,
        subscriber_id: int,
        tag_ids: List[int]
    ) -> Optional[Subscriber]:
        """Add tags to a subscriber."""
        subscriber = db.get(Subscriber, subscriber_id)
        if not subscriber:
            return None

        for tag_id in tag_ids:
            # Check if association already exists
            existing = db.exec(
                select(SubscriberTag).where(
                    and_(
                        SubscriberTag.subscriber_id == subscriber_id,
                        SubscriberTag.tag_id == tag_id
                    )
                )
            ).first()

            if not existing:
                subscriber_tag = SubscriberTag(
                    subscriber_id=subscriber_id,
                    tag_id=tag_id
                )
                db.add(subscriber_tag)

        db.commit()
        db.refresh(subscriber)
        return subscriber

    def remove_tag_from_subscriber(
        self,
        db: Session,
        subscriber_id: int,
        tag_id: int
    ) -> bool:
        """Remove a tag from a subscriber."""
        subscriber_tag = db.exec(
            select(SubscriberTag).where(
                and_(
                    SubscriberTag.subscriber_id == subscriber_id,
                    SubscriberTag.tag_id == tag_id
                )
            )
        ).first()

        if not subscriber_tag:
            return False

        db.delete(subscriber_tag)
        db.commit()
        return True

    def get_subscriber_tag_count(self, db: Session, subscriber_id: int) -> int:
        """Get number of tags for a subscriber."""
        return db.exec(
            select(func.count(SubscriberTag.id)).where(SubscriberTag.subscriber_id == subscriber_id)
        ).first() or 0

    # ============================================================
    # Email Template Operations
    # ============================================================

    def create_template(
        self,
        db: Session,
        data: EmailTemplateCreate,
        created_by_id: int
    ) -> EmailTemplate:
        """Create a new email template."""
        slug = generate_slug(data.name, db, EmailTemplate)

        template = EmailTemplate(
            **data.model_dump(),
            slug=slug,
            created_by_id=created_by_id
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def get_template(self, db: Session, template_id: int) -> Optional[EmailTemplate]:
        """Get template by ID."""
        return db.get(EmailTemplate, template_id)

    def get_template_by_slug(self, db: Session, slug: str) -> Optional[EmailTemplate]:
        """Get template by slug."""
        return db.exec(select(EmailTemplate).where(EmailTemplate.slug == slug)).first()

    def get_templates(
        self,
        db: Session,
        active_only: bool = False
    ) -> tuple[List[EmailTemplate], int]:
        """Get all templates."""
        query = select(EmailTemplate)
        count_query = select(func.count(EmailTemplate.id))

        if active_only:
            query = query.where(EmailTemplate.is_active == True)
            count_query = count_query.where(EmailTemplate.is_active == True)

        total = db.exec(count_query).first() or 0
        query = query.order_by(EmailTemplate.name)

        templates = db.exec(query).all()
        return list(templates), total

    def update_template(
        self,
        db: Session,
        template_id: int,
        data: EmailTemplateUpdate
    ) -> Optional[EmailTemplate]:
        """Update template."""
        template = db.get(EmailTemplate, template_id)
        if not template:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if 'name' in update_data and update_data['name'] != template.name:
            update_data['slug'] = generate_slug(update_data['name'], db, EmailTemplate)

        for field, value in update_data.items():
            setattr(template, field, value)

        template.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(template)
        return template

    def delete_template(self, db: Session, template_id: int) -> bool:
        """Delete template."""
        template = db.get(EmailTemplate, template_id)
        if not template:
            return False

        db.delete(template)
        db.commit()
        return True

    # ============================================================
    # Campaign Operations
    # ============================================================

    def create_campaign(
        self,
        db: Session,
        data: CampaignCreate,
        created_by_id: int
    ) -> Campaign:
        """Create a new campaign."""
        campaign = Campaign(
            **data.model_dump(),
            created_by_id=created_by_id
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    def get_campaign(self, db: Session, campaign_id: int) -> Optional[Campaign]:
        """Get campaign by ID."""
        return db.get(Campaign, campaign_id)

    def get_campaigns(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[CampaignStatus] = None
    ) -> tuple[List[Campaign], int]:
        """Get campaigns with optional status filtering."""
        query = select(Campaign)
        count_query = select(func.count(Campaign.id))

        if status:
            query = query.where(Campaign.status == status)
            count_query = count_query.where(Campaign.status == status)

        total = db.exec(count_query).first() or 0
        query = query.order_by(Campaign.created_at.desc())
        query = query.offset(skip).limit(limit)

        campaigns = db.exec(query).all()
        return list(campaigns), total

    def get_scheduled_campaigns(self, db: Session, before: datetime) -> List[Campaign]:
        """Get campaigns scheduled to be sent before a certain time."""
        return list(db.exec(
            select(Campaign).where(
                and_(
                    Campaign.status == CampaignStatus.scheduled,
                    Campaign.scheduled_at <= before
                )
            )
        ).all())

    def get_sending_campaigns(self, db: Session) -> List[Campaign]:
        """Get campaigns that are currently sending."""
        return list(db.exec(
            select(Campaign).where(Campaign.status == CampaignStatus.sending)
        ).all())

    def update_campaign(
        self,
        db: Session,
        campaign_id: int,
        data: CampaignUpdate
    ) -> Optional[Campaign]:
        """Update campaign (only if draft)."""
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            return None

        # Only allow updates to draft campaigns
        if campaign.status != CampaignStatus.draft:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(campaign, field, value)

        campaign.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(campaign)
        return campaign

    def schedule_campaign(
        self,
        db: Session,
        campaign_id: int,
        scheduled_at: datetime
    ) -> Optional[Campaign]:
        """Schedule a campaign for sending."""
        campaign = db.get(Campaign, campaign_id)
        if not campaign or campaign.status != CampaignStatus.draft:
            return None

        campaign.status = CampaignStatus.scheduled
        campaign.scheduled_at = scheduled_at
        campaign.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(campaign)
        return campaign

    def start_campaign_sending(self, db: Session, campaign_id: int) -> Optional[Campaign]:
        """Mark campaign as sending."""
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            return None

        campaign.status = CampaignStatus.sending
        campaign.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(campaign)
        return campaign

    def complete_campaign(self, db: Session, campaign_id: int) -> Optional[Campaign]:
        """Mark campaign as sent."""
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            return None

        campaign.status = CampaignStatus.sent
        campaign.sent_at = datetime.utcnow()
        campaign.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(campaign)
        return campaign

    def cancel_campaign(self, db: Session, campaign_id: int) -> Optional[Campaign]:
        """Cancel a scheduled campaign."""
        campaign = db.get(Campaign, campaign_id)
        if not campaign or campaign.status not in [CampaignStatus.draft, CampaignStatus.scheduled]:
            return None

        campaign.status = CampaignStatus.cancelled
        campaign.scheduled_at = None
        campaign.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(campaign)
        return campaign

    def delete_campaign(self, db: Session, campaign_id: int) -> bool:
        """Delete campaign (only if draft)."""
        campaign = db.get(Campaign, campaign_id)
        if not campaign or campaign.status != CampaignStatus.draft:
            return False

        # Delete recipients
        for recipient in db.exec(select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign_id)).all():
            db.delete(recipient)

        db.delete(campaign)
        db.commit()
        return True

    def update_campaign_stats(
        self,
        db: Session,
        campaign_id: int,
        field: str,
        increment: int = 1
    ) -> Optional[Campaign]:
        """Increment a campaign statistic field."""
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            return None

        current_value = getattr(campaign, field, 0)
        setattr(campaign, field, current_value + increment)
        campaign.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(campaign)
        return campaign

    # ============================================================
    # Campaign Recipient Operations
    # ============================================================

    def create_campaign_recipient(
        self,
        db: Session,
        campaign_id: int,
        subscriber_id: int
    ) -> CampaignRecipient:
        """Create a campaign recipient."""
        recipient = CampaignRecipient(
            campaign_id=campaign_id,
            subscriber_id=subscriber_id,
            open_token=generate_token(),
            click_token=generate_token()
        )
        db.add(recipient)
        db.commit()
        db.refresh(recipient)
        return recipient

    def get_campaign_recipient(self, db: Session, recipient_id: int) -> Optional[CampaignRecipient]:
        """Get campaign recipient by ID."""
        return db.get(CampaignRecipient, recipient_id)

    def get_recipient_by_open_token(self, db: Session, token: str) -> Optional[CampaignRecipient]:
        """Get recipient by open tracking token."""
        return db.exec(
            select(CampaignRecipient).where(CampaignRecipient.open_token == token)
        ).first()

    def get_recipient_by_click_token(self, db: Session, token: str) -> Optional[CampaignRecipient]:
        """Get recipient by click tracking token."""
        return db.exec(
            select(CampaignRecipient).where(CampaignRecipient.click_token == token)
        ).first()

    def get_pending_recipients(
        self,
        db: Session,
        campaign_id: int,
        limit: int = 50
    ) -> List[CampaignRecipient]:
        """Get pending recipients for a campaign."""
        return list(db.exec(
            select(CampaignRecipient).where(
                and_(
                    CampaignRecipient.campaign_id == campaign_id,
                    CampaignRecipient.status == RecipientStatus.pending
                )
            ).limit(limit)
        ).all())

    def get_campaign_recipients(
        self,
        db: Session,
        campaign_id: int,
        skip: int = 0,
        limit: int = 50,
        status: Optional[RecipientStatus] = None
    ) -> tuple[List[CampaignRecipient], int]:
        """Get campaign recipients with optional status filtering."""
        query = select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign_id)
        count_query = select(func.count(CampaignRecipient.id)).where(
            CampaignRecipient.campaign_id == campaign_id
        )

        if status:
            query = query.where(CampaignRecipient.status == status)
            count_query = count_query.where(CampaignRecipient.status == status)

        total = db.exec(count_query).first() or 0
        query = query.offset(skip).limit(limit)

        recipients = db.exec(query).all()
        return list(recipients), total

    def update_recipient_status(
        self,
        db: Session,
        recipient_id: int,
        status: RecipientStatus
    ) -> Optional[CampaignRecipient]:
        """Update recipient status."""
        recipient = db.get(CampaignRecipient, recipient_id)
        if not recipient:
            return None

        recipient.status = status

        # Set timestamp based on status
        if status == RecipientStatus.sent:
            recipient.sent_at = datetime.utcnow()
        elif status == RecipientStatus.opened:
            if not recipient.opened_at:  # Only set first open
                recipient.opened_at = datetime.utcnow()
        elif status == RecipientStatus.clicked:
            if not recipient.clicked_at:  # Only set first click
                recipient.clicked_at = datetime.utcnow()

        db.commit()
        db.refresh(recipient)
        return recipient

    def record_link_click(
        self,
        db: Session,
        recipient_id: int,
        original_url: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> CampaignLinkClick:
        """Record a link click."""
        click = CampaignLinkClick(
            recipient_id=recipient_id,
            original_url=original_url,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(click)
        db.commit()
        db.refresh(click)
        return click


# Create singleton instance
newsletter_crud = NewsletterCRUD()
