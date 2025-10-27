"""
Sync models for offline-first multiplatform support.

This module defines models for tracking client devices and their sync state,
enabling robust offline synchronization for Android, iOS, and Desktop clients.
"""

from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DeviceType(str, Enum):
    """Types of client devices."""
    ANDROID = "android"
    IOS = "ios"
    DESKTOP = "desktop"
    WEB = "web"


class DevicePlatform(str, Enum):
    """Device platform details."""
    ANDROID = "android"
    IOS = "ios"
    MACOS = "macos"
    WINDOWS = "windows"
    LINUX = "linux"
    WEB = "web"


class ConflictResolution(str, Enum):
    """Conflict resolution strategies."""
    CLIENT_WINS = "client_wins"
    SERVER_WINS = "server_wins"
    MANUAL = "manual"
    LAST_WRITE_WINS = "last_write_wins"


class Device(SQLModel, table=True):
    """
    Represents a client device for sync tracking.

    Each device (mobile app, desktop app) registers itself to enable
    per-device sync state tracking and push notifications.

    Attributes:
        id: Unique device identifier (usually UUID from client)
        user_id: Foreign key to user who owns this device
        device_type: Type of device (android/ios/desktop/web)
        platform: Specific platform (android/ios/macos/windows/linux)
        device_name: User-friendly device name
        device_info: Additional device metadata (OS version, app version, etc.)
        push_token: Token for push notifications (FCM, APNS, etc.)
        last_sync_at: Timestamp of last successful sync
        registered_at: When device was first registered
        last_seen_at: Last time device made any API request
        is_active: Whether device is active (for revocation)
    """
    __tablename__ = "devices"

    # Primary key is device_id (usually UUID from client)
    id: str = Field(primary_key=True, max_length=255, description="Unique device identifier")

    # Foreign key to user
    user_id: int = Field(foreign_key="users.id", index=True, description="User who owns this device")

    # Device metadata
    device_type: DeviceType = Field(description="Type of device")
    platform: Optional[DevicePlatform] = Field(default=None, description="Specific platform")
    device_name: Optional[str] = Field(default=None, max_length=255, description="User-friendly device name")
    device_info: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional device metadata (OS version, app version, etc.)"
    )

    # Push notification token
    push_token: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Token for push notifications (FCM, APNS, etc.)"
    )

    # Sync tracking
    last_sync_at: Optional[datetime] = Field(
        default=None,
        index=True,
        description="Timestamp of last successful sync"
    )

    # Timestamps
    registered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When device was first registered"
    )

    last_seen_at: Optional[datetime] = Field(
        default=None,
        description="Last time device made any API request"
    )

    # Status
    is_active: bool = Field(
        default=True,
        description="Whether device is active (for revocation)"
    )


class DeviceSyncState(SQLModel, table=True):
    """
    Per-device, per-entity-type sync state tracking.

    Tracks the last sync timestamp and version for each entity type on each device,
    enabling efficient incremental sync.

    Attributes:
        id: Primary key
        device_id: Foreign key to device
        entity_type: Type of entity (e.g., 'volunteer', 'project', 'task')
        last_synced_at: Last successful sync timestamp for this entity type
        last_synced_version: Last version number synced
        sync_metadata: Additional sync metadata (filters, preferences, etc.)
    """
    __tablename__ = "device_sync_states"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key to device
    device_id: str = Field(
        foreign_key="devices.id",
        index=True,
        max_length=255,
        description="Device identifier"
    )

    # Entity type being tracked
    entity_type: str = Field(
        max_length=100,
        index=True,
        description="Type of entity (e.g., 'volunteer', 'project', 'task')"
    )

    # Sync state
    last_synced_at: Optional[datetime] = Field(
        default=None,
        description="Last successful sync timestamp for this entity type"
    )

    last_synced_version: Optional[int] = Field(
        default=None,
        description="Last version number synced"
    )

    # Additional metadata
    sync_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional sync metadata (filters, preferences, etc.)"
    )

    # Updated timestamp
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this sync state was last updated"
    )


class SyncConflict(SQLModel, table=True):
    """
    Log of sync conflicts for analysis and debugging.

    Records conflicts that occur during sync for monitoring and debugging purposes.
    Helps identify sync issues and improve conflict resolution strategies.

    Attributes:
        id: Primary key
        device_id: Device that caused the conflict
        user_id: User who owns the conflicting data
        entity_type: Type of entity that conflicted
        entity_id: ID of the conflicting entity
        conflict_type: Type of conflict (e.g., 'version_mismatch', 'timestamp_conflict')
        client_version: Client's version of the data
        server_version: Server's version of the data
        client_timestamp: Client's last_modified_at
        server_timestamp: Server's last_modified_at
        client_data: Client's data snapshot at time of conflict
        server_data: Server's data snapshot at time of conflict
        resolution: How conflict was resolved ('client_wins', 'server_wins', 'manual')
        resolved_at: When conflict was resolved
        created_at: When conflict was detected
        conflict_metadata: Additional conflict details
    """
    __tablename__ = "sync_conflicts"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Context
    device_id: str = Field(max_length=255, index=True, description="Device that caused the conflict")
    user_id: int = Field(foreign_key="users.id", index=True, description="User who owns the data")

    # Conflict details
    entity_type: str = Field(max_length=100, index=True, description="Type of entity that conflicted")
    entity_id: int = Field(description="ID of the conflicting entity")
    conflict_type: str = Field(max_length=50, description="Type of conflict")

    # Versions
    client_version: Optional[int] = Field(default=None, description="Client's version number")
    server_version: Optional[int] = Field(default=None, description="Server's version number")

    # Timestamps
    client_timestamp: Optional[datetime] = Field(default=None, description="Client's last_modified_at")
    server_timestamp: Optional[datetime] = Field(default=None, description="Server's last_modified_at")

    # Data snapshots
    client_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Client's data at time of conflict"
    )
    server_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Server's data at time of conflict"
    )

    # Resolution
    resolution: str = Field(
        max_length=50,
        description="How conflict was resolved ('client_wins', 'server_wins', 'manual')"
    )

    resolved_at: Optional[datetime] = Field(
        default=None,
        description="When conflict was resolved"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When conflict was detected"
    )

    # Additional details
    conflict_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional conflict details"
    )
