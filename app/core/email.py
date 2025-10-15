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
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            use_tls=True if settings.SMTP_PORT == 587 else False,
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
