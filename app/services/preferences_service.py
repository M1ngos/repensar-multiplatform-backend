# app/services/preferences_service.py
"""
User preferences helper service.

Provides utilities to check user notification preferences before
sending emails or creating in-app notifications.
"""

import logging
from typing import Optional

from sqlmodel import Session, select

from app.models.user_preferences import UserPreferences

logger = logging.getLogger(__name__)


def get_user_preferences(db: Session, user_id: int) -> Optional[UserPreferences]:
    """Get user's preferences, returns None if not found (don't auto-create)."""
    return db.exec(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    ).first()


def get_or_create_user_preferences(db: Session, user_id: int) -> UserPreferences:
    """Get existing preferences or create defaults for a user."""
    preferences = get_user_preferences(db, user_id)
    if not preferences:
        preferences = UserPreferences(user_id=user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    return preferences


class NotificationPreferences:
    """Helper class to check notification preferences."""

    def __init__(self, preferences: Optional[UserPreferences]):
        self.preferences = preferences

    @property
    def can_send_email_task_assigned(self) -> bool:
        """Check if user wants email notifications for task assignments."""
        if not self.preferences:
            return True  # Default to allowing
        return self.preferences.email_task_assigned

    @property
    def can_send_email_task_completed(self) -> bool:
        """Check if user wants email notifications for task completion."""
        if not self.preferences:
            return True
        return self.preferences.email_task_completed

    @property
    def can_send_email_project_updates(self) -> bool:
        """Check if user wants email notifications for project updates."""
        if not self.preferences:
            return True
        return self.preferences.email_project_updates

    @property
    def can_send_email_weekly_digest(self) -> bool:
        """Check if user wants weekly digest emails."""
        if not self.preferences:
            return False
        return self.preferences.email_weekly_digest

    @property
    def in_app_notifications_enabled(self) -> bool:
        """Check if master in-app notifications toggle is enabled."""
        if not self.preferences:
            return True
        return self.preferences.in_app_all

    @property
    def can_show_in_app_task_updates(self) -> bool:
        """Check if user wants in-app notifications for task updates."""
        if not self.preferences:
            return True
        return self.preferences.in_app_task_updates and self.preferences.in_app_all

    @property
    def can_show_in_app_project_updates(self) -> bool:
        """Check if user wants in-app notifications for project updates."""
        if not self.preferences:
            return True
        return self.preferences.in_app_project_updates and self.preferences.in_app_all

    @property
    def can_show_in_app_gamification(self) -> bool:
        """Check if user wants in-app notifications for gamification."""
        if not self.preferences:
            return True
        return self.preferences.in_app_gamification and self.preferences.in_app_all

    @property
    def theme(self) -> str:
        """Get user's preferred theme."""
        if not self.preferences:
            return "system"
        return self.preferences.theme or "system"

    @property
    def compact_mode(self) -> bool:
        """Check if user prefers compact mode."""
        if not self.preferences:
            return False
        return self.preferences.compact_mode

    @property
    def show_tutorials(self) -> bool:
        """Check if user wants to see tutorials."""
        if not self.preferences:
            return True
        return self.preferences.show_tutorials

    @property
    def language(self) -> str:
        """Get user's preferred language."""
        if not self.preferences:
            return "en"
        return self.preferences.language or "en"


def get_notification_preferences(db: Session, user_id: int) -> NotificationPreferences:
    """Get notification preferences helper for a user."""
    preferences = get_user_preferences(db, user_id)
    return NotificationPreferences(preferences)
