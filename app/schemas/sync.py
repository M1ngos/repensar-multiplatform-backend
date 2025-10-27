"""
Sync schemas for offline-first functionality
Supports incremental sync for desktop and mobile platforms
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


# ===========================
# Enums
# ===========================

class ConflictResolutionStrategy(str, Enum):
    """Conflict resolution strategies"""
    CLIENT_WINS = "client_wins"
    SERVER_WINS = "server_wins"
    MANUAL = "manual"
    LAST_WRITE_WINS = "last_write_wins"


class EntityOperation(str, Enum):
    """Operations that can be performed on entities"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


# ===========================
# Device Management
# ===========================

class DeviceRegistration(BaseModel):
    """Request to register or update a device"""
    device_id: str = Field(..., description="Unique device identifier (UUID recommended)")
    device_name: str = Field(..., description="Human-readable device name")
    device_type: str = Field(..., description="Device type: android, ios, desktop, web")
    platform: str = Field(..., description="Platform: android, ios, macos, windows, linux, web")
    os_version: Optional[str] = Field(None, description="OS version string")
    app_version: Optional[str] = Field(None, description="App version string")
    push_token: Optional[str] = Field(None, description="FCM/APNS push token")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "550e8400-e29b-41d4-a716-446655440000",
                "device_name": "John's iPhone",
                "device_type": "ios",
                "platform": "ios",
                "os_version": "17.2",
                "app_version": "2.0.0",
                "push_token": "fcm_token_here"
            }
        }


class DeviceInfo(BaseModel):
    """Device information response"""
    device_id: str
    device_name: str
    device_type: str
    platform: str
    os_version: Optional[str]
    app_version: Optional[str]
    last_sync_at: Optional[datetime]
    last_seen_at: Optional[datetime]
    is_active: bool
    registered_at: datetime


class DeviceRegistrationResponse(BaseModel):
    """Response after device registration"""
    device_id: str
    registered_at: datetime
    last_sync_at: Optional[datetime]
    message: str = "Device registered successfully"


class DeviceListResponse(BaseModel):
    """List of user's devices"""
    devices: List[DeviceInfo]
    total: int


# ===========================
# Sync Operations
# ===========================

class EntityChange(BaseModel):
    """Represents a change to an entity"""
    entity_type: str = Field(..., description="Type of entity: volunteer, project, task, etc.")
    entity_id: str = Field(..., description="Unique identifier of the entity")
    operation: EntityOperation = Field(..., description="Operation performed")
    data: Dict[str, Any] = Field(default_factory=dict, description="Entity data (empty for DELETE)")
    version: int = Field(..., description="Version number for optimistic locking")
    modified_at: datetime = Field(..., description="When the change was made")
    modified_by_device_id: Optional[str] = Field(None, description="Device that made the change")

    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "volunteer",
                "entity_id": "vol-123",
                "operation": "UPDATE",
                "data": {
                    "id": "vol-123",
                    "name": "John Doe",
                    "email": "john@example.com"
                },
                "version": 5,
                "modified_at": "2025-10-27T12:00:00Z",
                "modified_by_device_id": "device-uuid"
            }
        }


class SyncPullRequest(BaseModel):
    """Request to pull changes from server"""
    device_id: str = Field(..., description="Device requesting sync")
    entity_types: List[str] = Field(..., description="Entity types to sync")
    since: Optional[datetime] = Field(None, description="Only get changes after this timestamp (None = full sync)")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Max number of changes per entity type")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "550e8400-e29b-41d4-a716-446655440000",
                "entity_types": ["volunteer", "project", "task"],
                "since": "2025-10-27T10:00:00Z",
                "limit": 100
            }
        }


class SyncPushRequest(BaseModel):
    """Request to push local changes to server"""
    device_id: str = Field(..., description="Device pushing changes")
    changes: List[EntityChange] = Field(..., description="List of changes to apply")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "550e8400-e29b-41d4-a716-446655440000",
                "changes": [
                    {
                        "entity_type": "volunteer",
                        "entity_id": "vol-123",
                        "operation": "UPDATE",
                        "data": {"name": "Jane Doe"},
                        "version": 3,
                        "modified_at": "2025-10-27T11:30:00Z"
                    }
                ]
            }
        }


# ===========================
# Conflict Management
# ===========================

class ConflictData(BaseModel):
    """Represents a sync conflict"""
    conflict_id: str
    entity_type: str
    entity_id: str
    client_version: int
    server_version: int
    client_data: Dict[str, Any]
    server_data: Dict[str, Any]
    client_modified_at: datetime
    server_modified_at: datetime
    conflict_type: str
    suggested_resolution: ConflictResolutionStrategy


class ConflictResolutionRequest(BaseModel):
    """Request to resolve a conflict"""
    resolution: ConflictResolutionStrategy = Field(..., description="How to resolve the conflict")
    merged_data: Optional[Dict[str, Any]] = Field(None, description="Custom merged data for manual resolution")

    class Config:
        json_schema_extra = {
            "example": {
                "resolution": "client_wins",
                "merged_data": None
            }
        }


# ===========================
# Sync Responses
# ===========================

class SyncPullResponse(BaseModel):
    """Response from pull sync operation"""
    changes: List[EntityChange] = Field(default_factory=list, description="Changes from server")
    sync_token: datetime = Field(..., description="Timestamp to use for next incremental sync")
    has_more: bool = Field(False, description="Whether there are more changes available")
    total_changes: int = Field(0, description="Total number of changes returned")

    class Config:
        json_schema_extra = {
            "example": {
                "changes": [
                    {
                        "entity_type": "volunteer",
                        "entity_id": "vol-456",
                        "operation": "UPDATE",
                        "data": {"name": "Updated Name"},
                        "version": 10,
                        "modified_at": "2025-10-27T12:00:00Z",
                        "modified_by_device_id": "other-device"
                    }
                ],
                "sync_token": "2025-10-27T12:05:00Z",
                "has_more": False,
                "total_changes": 1
            }
        }


class SyncPushResponse(BaseModel):
    """Response from push sync operation"""
    applied: int = Field(..., description="Number of changes successfully applied")
    conflicts: List[ConflictData] = Field(default_factory=list, description="Conflicts detected")
    failed: int = Field(0, description="Number of changes that failed")
    sync_token: datetime = Field(..., description="Current server timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "applied": 5,
                "conflicts": [],
                "failed": 0,
                "sync_token": "2025-10-27T12:05:00Z"
            }
        }


# ===========================
# Sync Status
# ===========================

class EntitySyncState(BaseModel):
    """Sync state for a specific entity type"""
    entity_type: str
    last_synced_at: Optional[datetime]
    last_synced_version: Optional[int]
    total_entities: Optional[int] = None


class SyncStatusResponse(BaseModel):
    """Overall sync status for a device"""
    device: DeviceInfo
    sync_states: List[EntitySyncState] = Field(default_factory=list)
    pending_conflicts: int = Field(0, description="Number of unresolved conflicts")
    needs_sync: bool = Field(False, description="Whether sync is recommended")
    last_successful_sync: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "device": {
                    "device_id": "550e8400-e29b-41d4-a716-446655440000",
                    "device_name": "John's iPhone",
                    "device_type": "ios",
                    "platform": "ios",
                    "last_sync_at": "2025-10-27T12:00:00Z",
                    "is_active": True
                },
                "sync_states": [
                    {
                        "entity_type": "volunteer",
                        "last_synced_at": "2025-10-27T12:00:00Z",
                        "last_synced_version": 150,
                        "total_entities": 45
                    }
                ],
                "pending_conflicts": 0,
                "needs_sync": False,
                "last_successful_sync": "2025-10-27T12:00:00Z"
            }
        }


class ConflictListResponse(BaseModel):
    """List of conflicts"""
    conflicts: List[ConflictData]
    total: int
    unresolved: int
