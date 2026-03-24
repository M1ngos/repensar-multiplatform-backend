# app/models/user_preferences.py
"""User preferences model for storing user settings."""

from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional


class UserPreferences(SQLModel, table=True):
    """User preferences for notifications and appearance settings."""

    __tablename__ = "user_preferences"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)

    # Notification preferences
    email_task_assigned: bool = Field(default=True)
    email_task_completed: bool = Field(default=True)
    email_project_updates: bool = Field(default=True)
    email_weekly_digest: bool = Field(default=False)
    in_app_all: bool = Field(default=True)
    in_app_task_updates: bool = Field(default=True)
    in_app_project_updates: bool = Field(default=True)
    in_app_gamification: bool = Field(default=True)

    # Appearance preferences
    theme: str = Field(default="system")  # light, dark, system
    compact_mode: bool = Field(default=False)
    show_tutorials: bool = Field(default=True)
    language: str = Field(default="en")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship to User
    user: "User" = Relationship(back_populates="preferences")
