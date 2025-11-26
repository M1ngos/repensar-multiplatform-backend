# app/services/campaign_service.py
"""
Campaign Service for managing newsletter campaigns, sending, and tracking.
"""
import logging
import asyncio
from typing import Optional, List, Tuple
from datetime import datetime
from sqlmodel import Session

from app.crud.newsletter import newsletter_crud
from app.models.newsletter import (
    Campaign, CampaignRecipient, Subscriber, CampaignStatus, RecipientStatus
)
from app.core.email import send_newsletter_email
from app.core.config import settings

logger = logging.getLogger(__name__)

# 1x1 transparent GIF for open tracking
TRACKING_PIXEL = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x21,
    0xf9, 0x04, 0x01, 0x00, 0x00, 0x00, 0x00, 0x2c, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3b
])


class CampaignService:
    """Service for managing newsletter campaigns."""

    @staticmethod
    def schedule_campaign(
        db: Session,
        campaign_id: int,
        scheduled_at: datetime
    ) -> Optional[Campaign]:
        """
        Schedule a campaign for future sending.

        Args:
            db: Database session
            campaign_id: Campaign ID
            scheduled_at: Scheduled send time

        Returns:
            Updated Campaign or None if not found/invalid
        """
        campaign = newsletter_crud.get_campaign(db, campaign_id)
        if not campaign or campaign.status != CampaignStatus.draft:
            logger.warning(f"Cannot schedule campaign {campaign_id}: not found or not in draft status")
            return None

        if scheduled_at <= datetime.utcnow():
            logger.warning(f"Cannot schedule campaign {campaign_id}: scheduled time is in the past")
            return None

        # Create recipients
        CampaignService._create_campaign_recipients(db, campaign)

        # Schedule the campaign
        scheduled = newsletter_crud.schedule_campaign(db, campaign_id, scheduled_at)
        logger.info(f"Campaign {campaign_id} scheduled for {scheduled_at}")

        return scheduled

    @staticmethod
    def _create_campaign_recipients(db: Session, campaign: Campaign) -> int:
        """
        Create recipient records for a campaign based on targeting.

        Returns:
            Number of recipients created
        """
        # Get target subscribers
        tag_ids = campaign.target_tag_ids if not campaign.send_to_all else None
        subscribers = newsletter_crud.get_active_subscribers(db, tag_ids)

        count = 0
        for subscriber in subscribers:
            try:
                newsletter_crud.create_campaign_recipient(
                    db=db,
                    campaign_id=campaign.id,
                    subscriber_id=subscriber.id
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to create recipient for subscriber {subscriber.id}: {e}")

        # Update campaign total recipients
        campaign.total_recipients = count
        db.commit()

        logger.info(f"Created {count} recipients for campaign {campaign.id}")
        return count

    @staticmethod
    async def send_campaign_now(db: Session, campaign_id: int) -> Optional[Campaign]:
        """
        Start sending a campaign immediately.

        Args:
            db: Database session
            campaign_id: Campaign ID

        Returns:
            Campaign in sending status or None if error
        """
        campaign = newsletter_crud.get_campaign(db, campaign_id)
        if not campaign:
            return None

        if campaign.status not in [CampaignStatus.draft, CampaignStatus.scheduled]:
            logger.warning(f"Cannot send campaign {campaign_id}: status is {campaign.status}")
            return None

        # Create recipients if not already created
        if campaign.total_recipients == 0:
            CampaignService._create_campaign_recipients(db, campaign)

        # Mark as sending
        sending = newsletter_crud.start_campaign_sending(db, campaign_id)
        logger.info(f"Campaign {campaign_id} started sending")

        return sending

    @staticmethod
    async def process_campaign_batch(
        db: Session,
        campaign_id: int,
        batch_size: int = 50,
        delay_seconds: float = 1.0
    ) -> Tuple[int, int]:
        """
        Process a batch of pending campaign recipients.

        Args:
            db: Database session
            campaign_id: Campaign ID
            batch_size: Number of emails to send in this batch
            delay_seconds: Delay between emails (for rate limiting)

        Returns:
            Tuple of (sent_count, remaining_count)
        """
        campaign = newsletter_crud.get_campaign(db, campaign_id)
        if not campaign or campaign.status != CampaignStatus.sending:
            return 0, 0

        # Get pending recipients
        pending = newsletter_crud.get_pending_recipients(db, campaign_id, batch_size)

        if not pending:
            # No more pending recipients - mark campaign as complete
            newsletter_crud.complete_campaign(db, campaign_id)
            logger.info(f"Campaign {campaign_id} completed - all emails sent")
            return 0, 0

        sent_count = 0
        for recipient in pending:
            subscriber = newsletter_crud.get_subscriber(db, recipient.subscriber_id)
            if not subscriber:
                continue

            # Build tracking URLs
            base_url = settings.BACKEND_URL
            unsubscribe_url = f"{settings.FRONTEND_URL}/newsletter/unsubscribe/{subscriber.unsubscribe_token}"
            open_tracking_url = f"{base_url}/newsletter/track/open/{recipient.open_token}"

            # Send email
            try:
                success = await send_newsletter_email(
                    to_email=subscriber.email,
                    subject=campaign.subject,
                    html_content=campaign.html_content,
                    text_content=campaign.text_content,
                    subscriber_name=subscriber.name,
                    unsubscribe_url=unsubscribe_url,
                    open_tracking_url=open_tracking_url,
                    preview_text=campaign.preview_text
                )

                if success:
                    newsletter_crud.update_recipient_status(db, recipient.id, RecipientStatus.sent)
                    newsletter_crud.update_campaign_stats(db, campaign_id, 'total_sent', 1)
                    sent_count += 1
                else:
                    newsletter_crud.update_recipient_status(db, recipient.id, RecipientStatus.bounced)
                    newsletter_crud.update_campaign_stats(db, campaign_id, 'total_bounced', 1)

            except Exception as e:
                logger.error(f"Failed to send to {subscriber.email}: {e}")
                newsletter_crud.update_recipient_status(db, recipient.id, RecipientStatus.bounced)
                newsletter_crud.update_campaign_stats(db, campaign_id, 'total_bounced', 1)

            # Rate limiting delay
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)

        # Count remaining
        remaining_recipients, _ = newsletter_crud.get_campaign_recipients(
            db, campaign_id, status=RecipientStatus.pending
        )

        logger.info(f"Campaign {campaign_id}: sent {sent_count} emails, {len(remaining_recipients)} remaining")
        return sent_count, len(remaining_recipients)

    @staticmethod
    def track_open(
        db: Session,
        open_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bytes:
        """
        Track an email open and return the tracking pixel.

        Args:
            db: Database session
            open_token: Open tracking token
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            Tracking pixel (1x1 transparent GIF)
        """
        recipient = newsletter_crud.get_recipient_by_open_token(db, open_token)

        if recipient:
            # Only count first open
            if not recipient.opened_at:
                newsletter_crud.update_recipient_status(db, recipient.id, RecipientStatus.opened)
                newsletter_crud.update_campaign_stats(db, recipient.campaign_id, 'total_opened', 1)
                logger.debug(f"Tracked open for recipient {recipient.id}")

        return TRACKING_PIXEL

    @staticmethod
    def track_click(
        db: Session,
        click_token: str,
        original_url: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[str]:
        """
        Track a link click and return the redirect URL.

        Args:
            db: Database session
            click_token: Click tracking token
            original_url: Original destination URL
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            Original URL to redirect to, or None if invalid token
        """
        recipient = newsletter_crud.get_recipient_by_click_token(db, click_token)

        if not recipient:
            logger.warning(f"Invalid click token: {click_token[:10]}...")
            return None

        # Record the click
        newsletter_crud.record_link_click(
            db=db,
            recipient_id=recipient.id,
            original_url=original_url,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Update recipient status if first click
        if not recipient.clicked_at:
            newsletter_crud.update_recipient_status(db, recipient.id, RecipientStatus.clicked)
            newsletter_crud.update_campaign_stats(db, recipient.campaign_id, 'total_clicked', 1)

        logger.debug(f"Tracked click for recipient {recipient.id}: {original_url}")
        return original_url

    @staticmethod
    def get_campaign_stats(db: Session, campaign_id: int) -> Optional[dict]:
        """
        Get detailed statistics for a campaign.

        Args:
            db: Database session
            campaign_id: Campaign ID

        Returns:
            Dictionary with campaign statistics
        """
        campaign = newsletter_crud.get_campaign(db, campaign_id)
        if not campaign:
            return None

        # Calculate rates
        total = campaign.total_recipients or 1  # Avoid division by zero
        sent = campaign.total_sent or 1

        return {
            "total_recipients": campaign.total_recipients,
            "total_sent": campaign.total_sent,
            "total_delivered": campaign.total_delivered,
            "total_opened": campaign.total_opened,
            "total_clicked": campaign.total_clicked,
            "total_bounced": campaign.total_bounced,
            "total_unsubscribed": campaign.total_unsubscribed,
            "open_rate": round((campaign.total_opened / sent) * 100, 2) if sent > 0 else 0,
            "click_rate": round((campaign.total_clicked / sent) * 100, 2) if sent > 0 else 0,
            "bounce_rate": round((campaign.total_bounced / total) * 100, 2) if total > 0 else 0,
            "unsubscribe_rate": round((campaign.total_unsubscribed / sent) * 100, 2) if sent > 0 else 0,
        }

    @staticmethod
    async def send_test_email(
        db: Session,
        campaign_id: int,
        test_email: str
    ) -> bool:
        """
        Send a test email for a campaign.

        Args:
            db: Database session
            campaign_id: Campaign ID
            test_email: Email address to send test to

        Returns:
            True if test email was sent successfully
        """
        campaign = newsletter_crud.get_campaign(db, campaign_id)
        if not campaign:
            return False

        try:
            success = await send_newsletter_email(
                to_email=test_email,
                subject=f"[TEST] {campaign.subject}",
                html_content=campaign.html_content,
                text_content=campaign.text_content,
                subscriber_name="Test Subscriber",
                unsubscribe_url=f"{settings.FRONTEND_URL}/newsletter/unsubscribe/test-token",
                preview_text=campaign.preview_text
            )
            logger.info(f"Test email for campaign {campaign_id} sent to {test_email}")
            return success
        except Exception as e:
            logger.error(f"Failed to send test email: {e}")
            return False

    @staticmethod
    def get_due_campaigns(db: Session) -> List[Campaign]:
        """
        Get campaigns that are due to be sent.

        Returns:
            List of scheduled campaigns with scheduled_at <= now
        """
        return newsletter_crud.get_scheduled_campaigns(db, datetime.utcnow())

    @staticmethod
    def get_sending_campaigns(db: Session) -> List[Campaign]:
        """
        Get campaigns that are currently in sending status.

        Returns:
            List of campaigns with sending status
        """
        return newsletter_crud.get_sending_campaigns(db)


# Singleton instance
campaign_service = CampaignService()
