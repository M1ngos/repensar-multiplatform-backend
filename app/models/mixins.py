"""
Base mixins for models.

This module provides reusable mixins for SQLModel models, including sync functionality
for offline-first applications.
"""

from sqlmodel import Field
from typing import Optional
from datetime import datetime


class SyncMixin:
    """
    Mixin to add sync metadata to models for offline-first applications.

    This mixin adds fields necessary for implementing a robust sync mechanism
    with Last-Write-Wins (LWW) conflict resolution and soft deletes.

    Fields:
        version: Auto-incrementing version number for optimistic locking
        last_modified_at: Timestamp of last modification (used for LWW conflict resolution)
        is_deleted: Soft delete flag (True if entity is deleted)
        deleted_at: Timestamp when entity was soft-deleted
        modified_by_device_id: ID of the device/client that last modified this entity

    Usage:
        class MyModel(SQLModel, SyncMixin, table=True):
            id: Optional[int] = Field(default=None, primary_key=True)
            name: str
            # ... other fields
    """

    # Version for optimistic locking and conflict detection
    version: int = Field(default=1, description="Version number for optimistic locking")

    # Timestamp for Last-Write-Wins conflict resolution
    last_modified_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last modification timestamp for sync",
        index=True  # Indexed for efficient sync queries
    )

    # Soft delete fields
    is_deleted: bool = Field(
        default=False,
        description="Soft delete flag",
        index=True  # Indexed for filtering deleted records
    )

    deleted_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when entity was deleted"
    )

    # Track which device made the modification
    modified_by_device_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="ID of device/client that last modified this entity"
    )
