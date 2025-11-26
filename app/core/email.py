"""
Email service for sending transactional emails.
Supports async email sending with Jinja2 templates.
"""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)

# Get the templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "email"

# Initialize Jinja2 environment
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(['html', 'xml'])
)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send an email using aiosmtplib.

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML content of the email
        text_content: Plain text content (optional, falls back to stripped HTML)

    Returns:
        True if email was sent successfully, False otherwise
    """
    # Validate SMTP settings
    if not settings.SMTP_HOST or not settings.EMAIL_FROM:
        logger.error("SMTP settings not configured. Cannot send email.")
        logger.info(f"Would have sent email to {to_email} with subject: {subject}")
        logger.debug(f"Email content preview: {html_content[:200]}...")
        return False

    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        message["To"] = to_email
        message["Subject"] = subject

        # Add plain text version (simple fallback if not provided)
        if not text_content:
            # Simple HTML stripping for plain text version
            import re
            text_content = re.sub('<[^<]+?>', '', html_content)

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")

        message.attach(part1)
        message.attach(part2)

        # Send email
        # Port 587: Use STARTTLS (start_tls=True)
        # Port 465: Use implicit TLS (use_tls=True)
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            use_tls=True if settings.SMTP_PORT == 465 else False,
            start_tls=True if settings.SMTP_PORT == 587 else False,
        )

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


async def send_verification_email(
    email: str,
    token: str,
    name: str
) -> bool:
    """
    Send email verification link to user.

    Args:
        email: User's email address
        token: Verification token
        name: User's name

    Returns:
        True if email was sent successfully
    """
    # Build verification URL
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    # Render template
    template = jinja_env.get_template("verification.html")
    html_content = template.render(
        name=name,
        verification_url=verification_url,
        current_year=datetime.now().year
    )

    # Send email
    return await send_email(
        to_email=email,
        subject="Verify Your Email - Repensar",
        html_content=html_content
    )


async def send_password_reset_email(
    email: str,
    token: str,
    name: str
) -> bool:
    """
    Send password reset link to user.

    Args:
        email: User's email address
        token: Password reset token
        name: User's name

    Returns:
        True if email was sent successfully
    """
    # Build reset URL
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    # Render template
    template = jinja_env.get_template("password_reset.html")
    html_content = template.render(
        name=name,
        reset_url=reset_url,
        current_year=datetime.now().year
    )

    # Send email
    return await send_email(
        to_email=email,
        subject="Reset Your Password - Repensar",
        html_content=html_content
    )


def send_verification_email_sync(email: str, token: str, name: str) -> None:
    """
    Synchronous wrapper for send_verification_email.
    Use this for background tasks that don't support async.
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule the coroutine
            asyncio.ensure_future(send_verification_email(email, token, name))
        else:
            # If no loop is running, run it
            loop.run_until_complete(send_verification_email(email, token, name))
    except RuntimeError:
        # Create new loop if needed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_verification_email(email, token, name))
        loop.close()


def send_password_reset_email_sync(email: str, token: str, name: str) -> None:
    """
    Synchronous wrapper for send_password_reset_email.
    Use this for background tasks that don't support async.
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule the coroutine
            asyncio.ensure_future(send_password_reset_email(email, token, name))
        else:
            # If no loop is running, run it
            loop.run_until_complete(send_password_reset_email(email, token, name))
    except RuntimeError:
        # Create new loop if needed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_password_reset_email(email, token, name))
        loop.close()


# ============================================================
# Newsletter Email Functions
# ============================================================

async def send_subscription_confirmation(
    email: str,
    confirmation_token: str,
    name: Optional[str] = None
) -> bool:
    """
    Send subscription confirmation email (double opt-in).

    Args:
        email: Subscriber's email address
        confirmation_token: Confirmation token
        name: Subscriber's name (optional)

    Returns:
        True if email was sent successfully
    """
    confirmation_url = f"{settings.FRONTEND_URL}/newsletter/confirm/{confirmation_token}"

    template = jinja_env.get_template("newsletter/subscription_confirm.html")
    html_content = template.render(
        name=name,
        confirmation_url=confirmation_url,
        current_year=datetime.now().year
    )

    return await send_email(
        to_email=email,
        subject="Confirm Your Newsletter Subscription - Repensar",
        html_content=html_content
    )


async def send_contact_autoreply(
    email: str,
    name: str,
    message: str,
    submission_id: int
) -> bool:
    """
    Send auto-reply for contact form submission.

    Args:
        email: User's email address
        name: User's name
        message: Original message content
        submission_id: Database ID of the submission

    Returns:
        True if email was sent successfully
    """
    template = jinja_env.get_template("newsletter/contact_autoreply.html")
    html_content = template.render(
        name=name,
        message=message,
        submission_id=submission_id,
        submitted_at=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        frontend_url=settings.FRONTEND_URL,
        current_year=datetime.now().year
    )

    return await send_email(
        to_email=email,
        subject="Thank You for Contacting Us - Repensar",
        html_content=html_content
    )


async def send_contact_admin_notification(
    admin_email: str,
    name: str,
    email: str,
    message: str,
    submission_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> bool:
    """
    Send notification to admin about new contact form submission.

    Args:
        admin_email: Admin email address to notify
        name: Submitter's name
        email: Submitter's email
        message: Message content
        submission_id: Database ID of the submission
        ip_address: IP address of submitter
        user_agent: User agent of submitter

    Returns:
        True if email was sent successfully
    """
    template = jinja_env.get_template("newsletter/contact_admin_notification.html")
    html_content = template.render(
        name=name,
        email=email,
        message=message,
        submission_id=submission_id,
        submitted_at=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        ip_address=ip_address,
        user_agent=user_agent,
        backend_url=settings.BACKEND_URL,
        current_year=datetime.now().year
    )

    return await send_email(
        to_email=admin_email,
        subject=f"New Contact Form Submission from {name} - Repensar",
        html_content=html_content
    )


async def send_newsletter_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    subscriber_name: Optional[str] = None,
    unsubscribe_url: Optional[str] = None,
    open_tracking_url: Optional[str] = None,
    preview_text: Optional[str] = None
) -> bool:
    """
    Send a newsletter email with tracking capabilities.

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: Main HTML content
        text_content: Plain text version (optional)
        subscriber_name: Subscriber's name for personalization
        unsubscribe_url: Unsubscribe link (required for CAN-SPAM)
        open_tracking_url: URL for open tracking pixel
        preview_text: Preview text for email clients

    Returns:
        True if email was sent successfully
    """
    template = jinja_env.get_template("newsletter/newsletter_base.html")
    full_html = template.render(
        subject=subject,
        content=html_content,
        subscriber_name=subscriber_name,
        unsubscribe_url=unsubscribe_url,
        open_tracking_url=open_tracking_url,
        preview_text=preview_text,
        current_year=datetime.now().year,
        social_facebook="#",
        social_twitter="#",
        social_instagram="#"
    )

    return await send_email(
        to_email=to_email,
        subject=subject,
        html_content=full_html,
        text_content=text_content
    )


async def send_unsubscribe_confirmation(
    email: str,
    resubscribe_url: Optional[str] = None
) -> bool:
    """
    Send confirmation that user has been unsubscribed.

    Args:
        email: User's email address
        resubscribe_url: URL to re-subscribe (optional)

    Returns:
        True if email was sent successfully
    """
    if not resubscribe_url:
        resubscribe_url = f"{settings.FRONTEND_URL}/newsletter/subscribe"

    template = jinja_env.get_template("newsletter/unsubscribe_confirm.html")
    html_content = template.render(
        email=email,
        unsubscribed_at=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        resubscribe_url=resubscribe_url,
        current_year=datetime.now().year
    )

    return await send_email(
        to_email=email,
        subject="You've Been Unsubscribed - Repensar",
        html_content=html_content
    )
