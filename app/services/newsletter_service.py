# app/services/newsletter_service.py
"""
Newsletter Service for managing subscriptions with double opt-in.
"""
import logging
from typing import Optional, List
from datetime import datetime
from sqlmodel import Session

from app.crud.newsletter import newsletter_crud
from app.models.newsletter import Subscriber, SubscriptionStatus
from app.core.email import send_subscription_confirmation, send_unsubscribe_confirmation
from app.core.config import settings

logger = logging.getLogger(__name__)


class NewsletterService:
    """Service for managing newsletter subscriptions."""

    @staticmethod
    async def subscribe(
        db: Session,
        email: str,
        name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> tuple[Subscriber, bool]:
        """
        Subscribe an email to the newsletter with double opt-in.

        Args:
            db: Database session
            email: Email address to subscribe
            name: Subscriber's name (optional)
            ip_address: Client IP address
            user_id: Optional user ID if subscriber has an account

        Returns:
            Tuple of (Subscriber, is_new) - is_new is False if already subscribed
        """
        # Check if already subscribed
        existing = newsletter_crud.get_subscriber_by_email(db, email)

        if existing:
            if existing.status == SubscriptionStatus.active:
                logger.info(f"Email {email} is already actively subscribed")
                return existing, False

            if existing.status == SubscriptionStatus.pending:
                # Resend confirmation email
                logger.info(f"Resending confirmation to pending subscriber {email}")
                await NewsletterService._send_confirmation_email(existing)
                return existing, False

            if existing.status == SubscriptionStatus.unsubscribed:
                # Re-activate with pending status for double opt-in
                logger.info(f"Re-subscribing previously unsubscribed email {email}")
                from datetime import timedelta
                import secrets

                existing.status = SubscriptionStatus.pending
                existing.confirmation_token = secrets.token_urlsafe(32)
                existing.confirmation_expires = datetime.utcnow() + timedelta(hours=24)
                existing.name = name or existing.name
                existing.updated_at = datetime.utcnow()

                db.commit()
                db.refresh(existing)

                await NewsletterService._send_confirmation_email(existing)
                return existing, True

        # Create new subscriber
        subscriber = newsletter_crud.create_subscriber(
            db=db,
            email=email,
            name=name,
            status=SubscriptionStatus.pending,
            ip_address=ip_address,
            user_id=user_id
        )

        logger.info(f"New subscriber {email} created with pending status")

        # Send confirmation email
        await NewsletterService._send_confirmation_email(subscriber)

        return subscriber, True

    @staticmethod
    async def _send_confirmation_email(subscriber: Subscriber) -> bool:
        """Send double opt-in confirmation email."""
        try:
            success = await send_subscription_confirmation(
                email=subscriber.email,
                confirmation_token=subscriber.confirmation_token,
                name=subscriber.name
            )
            if success:
                logger.info(f"Confirmation email sent to {subscriber.email}")
            return success
        except Exception as e:
            logger.error(f"Failed to send confirmation email to {subscriber.email}: {e}")
            return False

    @staticmethod
    def confirm_subscription(
        db: Session,
        token: str
    ) -> Optional[Subscriber]:
        """
        Confirm a subscription via token.

        Args:
            db: Database session
            token: Confirmation token

        Returns:
            Confirmed Subscriber or None if token is invalid/expired
        """
        subscriber = newsletter_crud.get_subscriber_by_confirmation_token(db, token)

        if not subscriber:
            logger.warning(f"Invalid confirmation token: {token[:10]}...")
            return None

        # Check if token has expired
        if subscriber.confirmation_expires and subscriber.confirmation_expires < datetime.utcnow():
            logger.warning(f"Confirmation token expired for {subscriber.email}")
            return None

        # Confirm the subscription
        confirmed = newsletter_crud.confirm_subscriber(db, subscriber.id)
        logger.info(f"Subscription confirmed for {subscriber.email}")

        return confirmed

    @staticmethod
    async def unsubscribe(
        db: Session,
        token: str,
        send_confirmation: bool = True
    ) -> Optional[Subscriber]:
        """
        Unsubscribe a subscriber via token.

        Args:
            db: Database session
            token: Unsubscribe token
            send_confirmation: Whether to send confirmation email

        Returns:
            Unsubscribed Subscriber or None if token is invalid
        """
        subscriber = newsletter_crud.get_subscriber_by_unsubscribe_token(db, token)

        if not subscriber:
            logger.warning(f"Invalid unsubscribe token: {token[:10]}...")
            return None

        if subscriber.status == SubscriptionStatus.unsubscribed:
            logger.info(f"Subscriber {subscriber.email} is already unsubscribed")
            return subscriber

        # Unsubscribe
        unsubscribed = newsletter_crud.unsubscribe(db, subscriber.id)
        logger.info(f"Subscriber {subscriber.email} unsubscribed")

        # Send confirmation email
        if send_confirmation:
            try:
                await send_unsubscribe_confirmation(email=subscriber.email)
            except Exception as e:
                logger.error(f"Failed to send unsubscribe confirmation to {subscriber.email}: {e}")

        return unsubscribed

    @staticmethod
    def get_active_subscribers(
        db: Session,
        tag_ids: Optional[List[int]] = None
    ) -> List[Subscriber]:
        """
        Get all active subscribers, optionally filtered by tags.

        Args:
            db: Database session
            tag_ids: Optional list of tag IDs to filter by

        Returns:
            List of active subscribers
        """
        return newsletter_crud.get_active_subscribers(db, tag_ids)

    @staticmethod
    def get_subscriber_by_email(db: Session, email: str) -> Optional[Subscriber]:
        """Get subscriber by email address."""
        return newsletter_crud.get_subscriber_by_email(db, email)

    @staticmethod
    def link_subscriber_to_user(
        db: Session,
        email: str,
        user_id: int
    ) -> Optional[Subscriber]:
        """
        Link an existing subscriber to a user account.

        Args:
            db: Database session
            email: Subscriber's email
            user_id: User ID to link

        Returns:
            Updated Subscriber or None if not found
        """
        subscriber = newsletter_crud.get_subscriber_by_email(db, email)
        if not subscriber:
            return None

        subscriber.user_id = user_id
        subscriber.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(subscriber)

        logger.info(f"Linked subscriber {email} to user {user_id}")
        return subscriber


# Singleton instance
newsletter_service = NewsletterService()
