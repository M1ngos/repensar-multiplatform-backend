# app/schemas/user_preferences.py
"""Pydantic schemas for user preferences."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserPreferencesBase(BaseModel):
    """Base schema for user preferences."""

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
    theme: str = Field(default="system")
    compact_mode: bool = Field(default=False)
    show_tutorials: bool = Field(default=True)
    language: str = Field(default="en")


class UserPreferencesCreate(UserPreferencesBase):
    """Schema for creating user preferences."""

    user_id: int


class UserPreferencesUpdate(BaseModel):
    """Schema for full update of user preferences (PUT)."""

    email_task_assigned: Optional[bool] = None
    email_task_completed: Optional[bool] = None
    email_project_updates: Optional[bool] = None
    email_weekly_digest: Optional[bool] = None
    in_app_all: Optional[bool] = None
    in_app_task_updates: Optional[bool] = None
    in_app_project_updates: Optional[bool] = None
    in_app_gamification: Optional[bool] = None
    theme: Optional[str] = None
    compact_mode: Optional[bool] = None
    show_tutorials: Optional[bool] = None
    language: Optional[str] = None


class UserPreferencesPatch(BaseModel):
    """Schema for partial update of user preferences (PATCH)."""

    email_task_assigned: Optional[bool] = None
    email_task_completed: Optional[bool] = None
    email_project_updates: Optional[bool] = None
    email_weekly_digest: Optional[bool] = None
    in_app_all: Optional[bool] = None
    in_app_task_updates: Optional[bool] = None
    in_app_project_updates: Optional[bool] = None
    in_app_gamification: Optional[bool] = None
    theme: Optional[str] = None
    compact_mode: Optional[bool] = None
    show_tutorials: Optional[bool] = None
    language: Optional[str] = None


class UserPreferencesResponse(UserPreferencesBase):
    """Schema for user preferences response."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
