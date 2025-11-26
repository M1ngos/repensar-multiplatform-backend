# app/services/contact_service.py
"""
Contact Form Service for handling landing page contact submissions.
Sends auto-reply to user and notification to admin.
"""
import logging
from typing import Optional
from sqlmodel import Session

from app.crud.newsletter import newsletter_crud
from app.schemas.newsletter import ContactFormCreate
from app.models.newsletter import ContactSubmission
from app.core.email import send_contact_autoreply, send_contact_admin_notification
from app.core.config import settings

logger = logging.getLogger(__name__)


class ContactService:
    """Service for handling contact form submissions."""

    @staticmethod
    async def submit_contact_form(
        db: Session,
        data: ContactFormCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ContactSubmission:
        """
        Process a contact form submission.

        1. Save submission to database
        2. Send auto-reply to user
        3. Send notification to admin

        Args:
            db: Database session
            data: Contact form data
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created ContactSubmission object
        """
        # 1. Save to database
        submission = newsletter_crud.create_contact_submission(
            db=db,
            data=data,
            ip_address=ip_address,
            user_agent=user_agent
        )

        logger.info(f"Contact form submission #{submission.id} created from {data.email}")

        # 2. Send auto-reply to user
        try:
            await send_contact_autoreply(
                email=data.email,
                name=data.name,
                message=data.message,
                submission_id=submission.id
            )
            logger.info(f"Auto-reply sent to {data.email}")
        except Exception as e:
            logger.error(f"Failed to send auto-reply to {data.email}: {e}")

        # 3. Send notification to admin
        admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', None) or settings.EMAIL_FROM
        if admin_email:
            try:
                await send_contact_admin_notification(
                    admin_email=admin_email,
                    name=data.name,
                    email=data.email,
                    message=data.message,
                    submission_id=submission.id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                logger.info(f"Admin notification sent to {admin_email}")
            except Exception as e:
                logger.error(f"Failed to send admin notification: {e}")
        else:
            logger.warning("No admin email configured for contact notifications")

        return submission


# Singleton instance
contact_service = ContactService()
