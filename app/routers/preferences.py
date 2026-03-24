# app/routers/preferences.py
"""User preferences API endpoints."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.schemas.user_preferences import (
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserPreferencesPatch,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/preferences",
    tags=["preferences"],
    responses={404: {"description": "Not found"}},
)


def get_or_create_preferences(db: Session, user_id: int) -> UserPreferences:
    """Get existing preferences or create defaults for a user."""
    preferences = db.exec(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    ).first()

    if not preferences:
        preferences = UserPreferences(user_id=user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
        logger.info("Created default preferences for user_id=%s", user_id)

    return preferences


@router.get("", response_model=UserPreferencesResponse)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's preferences.

    Creates default preferences if they don't exist.
    """
    try:
        preferences = get_or_create_preferences(db, current_user.id)
        return preferences
    except Exception as e:
        logger.error(
            "Failed to retrieve preferences for user_id=%s: %s", current_user.id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences",
        )


@router.put("", response_model=UserPreferencesResponse)
def update_preferences(
    preferences_data: UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full update of user preferences (PUT).

    Replaces all preferences with the provided values.
    Missing fields will be reset to defaults.
    """
    try:
        # Get existing or create default preferences
        preferences = get_or_create_preferences(db, current_user.id)

        # Update all fields from the input
        update_data = preferences_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)

        preferences.updated_at = datetime.utcnow()

        db.add(preferences)
        db.commit()
        db.refresh(preferences)

        logger.info("Updated all preferences for user_id=%s", current_user.id)
        return preferences

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update preferences for user_id=%s: %s", current_user.id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences",
        )


@router.patch("", response_model=UserPreferencesResponse)
def patch_preferences(
    preferences_data: UserPreferencesPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partial update of user preferences (PATCH).

    Only updates the fields that are provided.
    Other fields remain unchanged.
    """
    try:
        # Get existing or create default preferences
        preferences = get_or_create_preferences(db, current_user.id)

        # Update only provided fields (exclude_unset=True for PATCH semantics)
        update_data = preferences_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)

        preferences.updated_at = datetime.utcnow()

        db.add(preferences)
        db.commit()
        db.refresh(preferences)

        logger.info("Patched preferences for user_id=%s", current_user.id)
        return preferences

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to patch preferences for user_id=%s: %s", current_user.id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences",
        )
