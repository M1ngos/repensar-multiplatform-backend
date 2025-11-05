"""
Sync router for offline-first functionality
Supports incremental sync for desktop and mobile platforms
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, and_, or_, col
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Type
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.analytics import NotificationType
from app.models.sync import Device, DeviceSyncState, SyncConflict, DeviceType, DevicePlatform, ConflictResolution
from app.models.volunteer import Volunteer, VolunteerSkill, VolunteerSkillAssignment, VolunteerTimeLog, VolunteerTraining, VolunteerTrainingRecord
from app.models.project import Project, ProjectTeam, Milestone, EnvironmentalMetric
from app.models.task import Task, TaskDependency
from app.models.resource import Resource, ProjectResource
from app.schemas.sync import (
    DeviceRegistration,
    DeviceRegistrationResponse,
    DeviceListResponse,
    DeviceInfo,
    SyncPullRequest,
    SyncPullResponse,
    SyncPushRequest,
    SyncPushResponse,
    EntityChange,
    EntityOperation,
    ConflictData,
    ConflictResolutionRequest,
    ConflictResolutionStrategy,
    SyncStatusResponse,
    EntitySyncState,
    ConflictListResponse
)
from app.services.notification_service import NotificationService, notify_sync_conflict
from app.services.event_bus import EventType, get_event_bus

router = APIRouter(prefix="/sync", tags=["Sync & Offline"])


# ===========================
# Entity Type Mapping
# ===========================

# Map entity type strings to SQLModel classes
# Add all models that support offline sync here
ENTITY_MODELS: Dict[str, Type] = {
    "volunteer": Volunteer,
    "volunteer_skill": VolunteerSkill,
    "volunteer_skill_assignment": VolunteerSkillAssignment,
    "volunteer_time_log": VolunteerTimeLog,
    "volunteer_training": VolunteerTraining,
    "volunteer_training_record": VolunteerTrainingRecord,
    "project": Project,
    "project_team": ProjectTeam,
    "milestone": Milestone,
    "environmental_metric": EnvironmentalMetric,
    "task": Task,
    "task_dependency": TaskDependency,
    "resource": Resource,
    "project_resource": ProjectResource,
}


def get_timestamp_field(model: Type) -> str:
    """
    Get the timestamp field name for a model
    Prefers: last_modified_at > updated_at > created_at
    """
    if hasattr(model, 'last_modified_at'):
        return 'last_modified_at'
    elif hasattr(model, 'updated_at'):
        return 'updated_at'
    elif hasattr(model, 'created_at'):
        return 'created_at'
    else:
        raise ValueError(f"Model {model} has no timestamp field")


def get_version_field(model: Type) -> Optional[str]:
    """Get the version field name if it exists"""
    if hasattr(model, 'version'):
        return 'version'
    return None


def get_soft_delete_fields(model: Type) -> tuple[Optional[str], Optional[str]]:
    """Get soft delete field names if they exist (is_deleted, deleted_at)"""
    is_deleted = 'is_deleted' if hasattr(model, 'is_deleted') else None
    deleted_at = 'deleted_at' if hasattr(model, 'deleted_at') else None
    return is_deleted, deleted_at


# ===========================
# Device Management
# ===========================

@router.post("/device/register", response_model=DeviceRegistrationResponse)
async def register_device(
    device_data: DeviceRegistration,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register or update a device for sync.

    Each client app should call this endpoint on first launch and when app metadata changes.
    The device_id should be a persistent UUID stored in the client's secure storage.
    """
    # Check if device exists
    device = db.exec(
        select(Device).where(Device.device_id == device_data.device_id)
    ).first()

    now = datetime.now(timezone.utc)

    if device:
        # Update existing device
        if device.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device belongs to another user"
            )

        device.device_name = device_data.device_name
        device.device_type = DeviceType(device_data.device_type)
        device.platform = DevicePlatform(device_data.platform)
        device.os_version = device_data.os_version
        device.app_version = device_data.app_version
        device.push_token = device_data.push_token
        device.last_seen_at = now
        device.is_active = True
        message = "Device updated successfully"
    else:
        # Create new device
        device = Device(
            device_id=device_data.device_id,
            user_id=current_user.id,
            device_name=device_data.device_name,
            device_type=DeviceType(device_data.device_type),
            platform=DevicePlatform(device_data.platform),
            os_version=device_data.os_version,
            app_version=device_data.app_version,
            push_token=device_data.push_token,
            last_seen_at=now,
            is_active=True,
            registered_at=now
        )
        db.add(device)
        message = "Device registered successfully"

    db.commit()
    db.refresh(device)

    return DeviceRegistrationResponse(
        device_id=device.device_id,
        registered_at=device.registered_at,
        last_sync_at=device.last_sync_at,
        message=message
    )


@router.get("/device/list", response_model=DeviceListResponse)
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_inactive: bool = Query(default=False)
):
    """
    List all devices registered to the current user.
    Useful for device management and revocation.
    """
    query = select(Device).where(Device.user_id == current_user.id)

    if not include_inactive:
        query = query.where(Device.is_active == True)

    devices = db.exec(query.order_by(Device.last_seen_at.desc())).all()

    device_infos = [
        DeviceInfo(
            device_id=d.device_id,
            device_name=d.device_name,
            device_type=d.device_type.value,
            platform=d.platform.value,
            os_version=d.os_version,
            app_version=d.app_version,
            last_sync_at=d.last_sync_at,
            last_seen_at=d.last_seen_at,
            is_active=d.is_active,
            registered_at=d.registered_at
        )
        for d in devices
    ]

    return DeviceListResponse(
        devices=device_infos,
        total=len(device_infos)
    )


@router.post("/device/{device_id}/revoke", status_code=status.HTTP_200_OK)
async def revoke_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a device (e.g., lost phone, stolen laptop).

    This will:
    - Mark the device as inactive
    - Force re-authentication on that device
    - Prevent future sync operations
    """
    device = db.exec(
        select(Device).where(
            and_(
                Device.device_id == device_id,
                Device.user_id == current_user.id
            )
        )
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    device.is_active = False
    db.commit()

    return {
        "message": f"Device '{device.device_name}' revoked successfully",
        "device_id": device_id
    }


# ===========================
# Sync Pull (Server → Client)
# ===========================

@router.post("/pull", response_model=SyncPullResponse)
async def pull_changes(
    request: SyncPullRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pull changes from server since last sync (incremental sync).

    This endpoint returns all entities modified after the 'since' timestamp.
    Clients should:
    1. Store the returned sync_token
    2. Use it as 'since' in the next pull request
    3. Apply changes to local database
    4. Handle conflicts if any

    The endpoint supports:
    - Incremental sync (only changed entities)
    - Soft deletes (is_deleted flag)
    - Pagination (limit parameter)
    - Per-device sync state tracking
    """
    # Verify device belongs to user and is active
    device = db.exec(
        select(Device).where(
            and_(
                Device.device_id == request.device_id,
                Device.user_id == current_user.id,
                Device.is_active == True
            )
        )
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device not registered or inactive. Please register device first."
        )

    all_changes: List[EntityChange] = []
    limit = request.limit or 100

    for entity_type in request.entity_types:
        if entity_type not in ENTITY_MODELS:
            continue

        model = ENTITY_MODELS[entity_type]
        timestamp_field = get_timestamp_field(model)
        version_field = get_version_field(model)
        is_deleted_field, deleted_at_field = get_soft_delete_fields(model)

        # Get last sync state for this entity type
        sync_state = db.exec(
            select(DeviceSyncState).where(
                and_(
                    DeviceSyncState.device_id == request.device_id,
                    DeviceSyncState.entity_type == entity_type
                )
            )
        ).first()

        # Determine since timestamp
        since = request.since
        if not since and sync_state and sync_state.last_synced_at:
            since = sync_state.last_synced_at

        # Build query for changes
        query = select(model)

        # Filter by timestamp if specified
        if since:
            timestamp_col = getattr(model, timestamp_field)
            query = query.where(timestamp_col > since)

        # TODO: Add user-specific filters based on permissions
        # For example: filter volunteers by projects user has access to

        # Order by timestamp and limit
        timestamp_col = getattr(model, timestamp_field)
        query = query.order_by(timestamp_col).limit(limit)

        entities = db.exec(query).all()

        # Convert to EntityChange format
        for entity in entities:
            # Determine operation type
            if is_deleted_field and getattr(entity, is_deleted_field, False):
                operation = EntityOperation.DELETE
                data = {}  # Don't send data for deleted entities
            else:
                operation = EntityOperation.UPDATE  # Could be CREATE or UPDATE

            # Get version and timestamp
            version = getattr(entity, version_field, 1) if version_field else 1
            modified_at = getattr(entity, timestamp_field)

            # Get modified_by_device_id if available
            modified_by = getattr(entity, 'modified_by_device_id', None) if hasattr(entity, 'modified_by_device_id') else None

            # Convert entity to dict (only if not deleted)
            entity_data = {}
            if operation != EntityOperation.DELETE:
                entity_dict = entity.model_dump()
                # Convert datetime objects to ISO format
                for key, value in entity_dict.items():
                    if isinstance(value, datetime):
                        entity_dict[key] = value.isoformat()
                entity_data = entity_dict

            all_changes.append(
                EntityChange(
                    entity_type=entity_type,
                    entity_id=str(entity.id),
                    operation=operation,
                    data=entity_data,
                    version=version,
                    modified_at=modified_at,
                    modified_by_device_id=modified_by
                )
            )

        # Update sync state for this entity type
        if not sync_state:
            sync_state = DeviceSyncState(
                device_id=request.device_id,
                entity_type=entity_type,
                last_synced_at=datetime.now(timezone.utc),
                last_synced_version=max([getattr(e, version_field, 1) for e in entities], default=0) if version_field else 0
            )
            db.add(sync_state)
        else:
            sync_state.last_synced_at = datetime.now(timezone.utc)
            if version_field and entities:
                sync_state.last_synced_version = max([getattr(e, version_field, 1) for e in entities])

    # Update device last_seen_at and last_sync_at
    now = datetime.now(timezone.utc)
    device.last_seen_at = now
    device.last_sync_at = now

    db.commit()

    return SyncPullResponse(
        changes=all_changes,
        sync_token=now,
        has_more=len(all_changes) >= limit,
        total_changes=len(all_changes)
    )


# ===========================
# Sync Push (Client → Server)
# ===========================

@router.post("/push", response_model=SyncPushResponse)
async def push_changes(
    request: SyncPushRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Push local changes to server with conflict detection.

    This endpoint:
    1. Validates each change
    2. Detects conflicts using optimistic locking (version field)
    3. Applies changes that don't conflict
    4. Returns conflicts for client resolution

    Conflict resolution strategies:
    - Version mismatch: Server version > client version
    - Last-Write-Wins: Timestamp-based (automatic)
    - Manual: Client decides (returned in response)
    """
    # Verify device
    device = db.exec(
        select(Device).where(
            and_(
                Device.device_id == request.device_id,
                Device.user_id == current_user.id,
                Device.is_active == True
            )
        )
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device not registered or inactive. Please register device first."
        )

    conflicts: List[ConflictData] = []
    applied_count = 0
    failed_count = 0

    for change in request.changes:
        if change.entity_type not in ENTITY_MODELS:
            failed_count += 1
            continue

        model = ENTITY_MODELS[change.entity_type]
        version_field = get_version_field(model)
        timestamp_field = get_timestamp_field(model)
        is_deleted_field, deleted_at_field = get_soft_delete_fields(model)

        try:
            # Fetch current server version
            server_entity = db.exec(
                select(model).where(model.id == int(change.entity_id))
            ).first()

            # Conflict detection using version field
            if server_entity and version_field:
                server_version = getattr(server_entity, version_field, 1)

                if server_version > change.version:
                    # CONFLICT: Server has newer version
                    server_timestamp = getattr(server_entity, timestamp_field)

                    # Create conflict record
                    conflict_record = SyncConflict(
                        device_id=request.device_id,
                        entity_type=change.entity_type,
                        entity_id=change.entity_id,
                        conflict_type="version_mismatch",
                        client_version=change.version,
                        server_version=server_version,
                        client_data=change.data,
                        server_data=server_entity.model_dump(),
                        client_timestamp=change.modified_at,
                        server_timestamp=server_timestamp,
                        resolution=ConflictResolution.SERVER_WINS  # Default
                    )
                    db.add(conflict_record)
                    db.flush()  # Get the ID

                    # Add to response conflicts
                    conflicts.append(
                        ConflictData(
                            conflict_id=str(conflict_record.id),
                            entity_type=change.entity_type,
                            entity_id=change.entity_id,
                            client_version=change.version,
                            server_version=server_version,
                            client_data=change.data,
                            server_data=server_entity.model_dump(),
                            client_modified_at=change.modified_at,
                            server_modified_at=server_timestamp,
                            conflict_type="version_mismatch",
                            suggested_resolution=ConflictResolutionStrategy.SERVER_WINS
                        )
                    )
                    continue  # Skip applying this change

            # Apply change based on operation
            if change.operation == EntityOperation.CREATE:
                # Create new entity
                new_entity = model(**change.data)
                if version_field:
                    setattr(new_entity, version_field, 1)
                setattr(new_entity, timestamp_field, datetime.now(timezone.utc))
                if hasattr(new_entity, 'modified_by_device_id'):
                    new_entity.modified_by_device_id = request.device_id

                db.add(new_entity)
                applied_count += 1

            elif change.operation == EntityOperation.UPDATE:
                if not server_entity:
                    # Entity doesn't exist on server, treat as CREATE
                    new_entity = model(**change.data)
                    if version_field:
                        setattr(new_entity, version_field, 1)
                    setattr(new_entity, timestamp_field, datetime.now(timezone.utc))
                    if hasattr(new_entity, 'modified_by_device_id'):
                        new_entity.modified_by_device_id = request.device_id
                    db.add(new_entity)
                else:
                    # Update existing entity
                    for key, value in change.data.items():
                        if hasattr(server_entity, key) and key not in ['id', 'created_at']:
                            # Skip read-only fields
                            if key in ['version', 'updated_at', 'last_modified_at', 'modified_by_device_id']:
                                continue
                            setattr(server_entity, key, value)

                    # Increment version
                    if version_field:
                        current_version = getattr(server_entity, version_field, 0)
                        setattr(server_entity, version_field, current_version + 1)

                    # Update timestamp
                    setattr(server_entity, timestamp_field, datetime.now(timezone.utc))

                    # Track device
                    if hasattr(server_entity, 'modified_by_device_id'):
                        server_entity.modified_by_device_id = request.device_id

                applied_count += 1

            elif change.operation == EntityOperation.DELETE:
                if server_entity:
                    if is_deleted_field:
                        # Soft delete
                        setattr(server_entity, is_deleted_field, True)
                        if deleted_at_field:
                            setattr(server_entity, deleted_at_field, datetime.now(timezone.utc))
                        if version_field:
                            current_version = getattr(server_entity, version_field, 0)
                            setattr(server_entity, version_field, current_version + 1)
                        setattr(server_entity, timestamp_field, datetime.now(timezone.utc))
                    else:
                        # Hard delete
                        db.delete(server_entity)

                    applied_count += 1

        except Exception as e:
            # Log error and continue
            print(f"Error applying change for {change.entity_type} {change.entity_id}: {str(e)}")
            failed_count += 1

    # Update device
    now = datetime.now(timezone.utc)
    device.last_seen_at = now
    device.last_sync_at = now

    db.commit()

    return SyncPushResponse(
        applied=applied_count,
        conflicts=conflicts,
        failed=failed_count,
        sync_token=now
    )


# ===========================
# Conflict Resolution
# ===========================

@router.get("/conflicts", response_model=ConflictListResponse)
async def get_conflicts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    device_id: Optional[str] = Query(None),
    unresolved_only: bool = Query(True)
):
    """
    Get sync conflicts for user's devices.

    Useful for:
    - Displaying conflicts to users
    - Manual conflict resolution UI
    - Debugging sync issues
    """
    # Get user's devices
    user_devices = db.exec(
        select(Device.device_id).where(Device.user_id == current_user.id)
    ).all()

    query = select(SyncConflict).where(
        SyncConflict.device_id.in_(user_devices)
    )

    if device_id:
        query = query.where(SyncConflict.device_id == device_id)

    if unresolved_only:
        query = query.where(SyncConflict.resolved_at.is_(None))

    conflicts_db = db.exec(query.order_by(SyncConflict.created_at.desc())).all()

    conflicts = [
        ConflictData(
            conflict_id=str(c.id),
            entity_type=c.entity_type,
            entity_id=c.entity_id,
            client_version=c.client_version,
            server_version=c.server_version,
            client_data=c.client_data,
            server_data=c.server_data,
            client_modified_at=c.client_timestamp,
            server_modified_at=c.server_timestamp,
            conflict_type=c.conflict_type,
            suggested_resolution=ConflictResolutionStrategy.SERVER_WINS
        )
        for c in conflicts_db
    ]

    total = len(conflicts)
    unresolved = sum(1 for c in conflicts_db if c.resolved_at is None)

    return ConflictListResponse(
        conflicts=conflicts,
        total=total,
        unresolved=unresolved
    )


@router.post("/conflicts/{conflict_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_conflict(
    conflict_id: str,
    resolution_request: ConflictResolutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually resolve a sync conflict.

    Resolution strategies:
    - CLIENT_WINS: Use client data (overwrite server)
    - SERVER_WINS: Keep server data (discard client changes)
    - MANUAL: Use custom merged data provided in request
    """
    conflict = db.exec(
        select(SyncConflict).where(SyncConflict.id == int(conflict_id))
    ).first()

    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conflict not found"
        )

    # Verify ownership
    device = db.exec(
        select(Device).where(Device.device_id == conflict.device_id)
    ).first()

    if not device or device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to resolve this conflict"
        )

    # Get entity model
    if conflict.entity_type not in ENTITY_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown entity type: {conflict.entity_type}"
        )

    model = ENTITY_MODELS[conflict.entity_type]
    entity = db.exec(
        select(model).where(model.id == int(conflict.entity_id))
    ).first()

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found"
        )

    # Apply resolution
    version_field = get_version_field(model)
    timestamp_field = get_timestamp_field(model)

    if resolution_request.resolution == ConflictResolutionStrategy.CLIENT_WINS:
        # Apply client data
        for key, value in conflict.client_data.items():
            if hasattr(entity, key) and key not in ['id', 'created_at', 'version', 'updated_at', 'last_modified_at']:
                setattr(entity, key, value)

        if version_field:
            current_version = getattr(entity, version_field, 0)
            setattr(entity, version_field, current_version + 1)
        setattr(entity, timestamp_field, datetime.now(timezone.utc))

    elif resolution_request.resolution == ConflictResolutionStrategy.SERVER_WINS:
        # Keep server data (no changes)
        pass

    elif resolution_request.resolution == ConflictResolutionStrategy.MANUAL:
        # Apply merged data
        if not resolution_request.merged_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="merged_data required for MANUAL resolution"
            )

        for key, value in resolution_request.merged_data.items():
            if hasattr(entity, key) and key not in ['id', 'created_at']:
                setattr(entity, key, value)

        if version_field:
            current_version = getattr(entity, version_field, 0)
            setattr(entity, version_field, current_version + 1)
        setattr(entity, timestamp_field, datetime.now(timezone.utc))

    # Mark conflict as resolved
    conflict.resolution = ConflictResolution(resolution_request.resolution.value)
    conflict.resolved_at = datetime.now(timezone.utc)

    db.commit()

    # Notify user that conflict was resolved
    await NotificationService.create_notification(
        db=db,
        user_id=current_user.id,
        title="Sync Conflict Resolved",
        message=f"Conflict in {conflict.entity_type} (ID: {conflict.entity_id}) has been resolved using {resolution_request.resolution.value} strategy.",
        notification_type=NotificationType.success
    )

    # Publish event
    try:
        event_bus = get_event_bus()
        await event_bus.publish(
            EventType.SYNC_CONFLICT_RESOLVED,
            {
                "conflict_id": conflict_id,
                "entity_type": conflict.entity_type,
                "entity_id": conflict.entity_id,
                "resolution": resolution_request.resolution.value,
                "device_id": conflict.device_id,
                "resolved_by": current_user.id
            },
            user_id=current_user.id
        )
    except Exception as e:
        pass

    return {
        "message": "Conflict resolved successfully",
        "conflict_id": conflict_id,
        "resolution": resolution_request.resolution,
        "entity_type": conflict.entity_type,
        "entity_id": conflict.entity_id
    }


# ===========================
# Sync Status & Diagnostics
# ===========================

@router.get("/status", response_model=SyncStatusResponse)
async def sync_status(
    device_id: str = Query(..., description="Device ID to check status for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive sync status for a device.

    Returns:
    - Device information
    - Sync state for each entity type
    - Pending conflicts count
    - Whether sync is needed
    """
    device = db.exec(
        select(Device).where(
            and_(
                Device.device_id == device_id,
                Device.user_id == current_user.id
            )
        )
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Get sync states
    sync_states = db.exec(
        select(DeviceSyncState).where(
            DeviceSyncState.device_id == device_id
        )
    ).all()

    entity_sync_states = [
        EntitySyncState(
            entity_type=s.entity_type,
            last_synced_at=s.last_synced_at,
            last_synced_version=s.last_synced_version
        )
        for s in sync_states
    ]

    # Get pending conflicts count
    pending_conflicts_count = db.exec(
        select(SyncConflict).where(
            and_(
                SyncConflict.device_id == device_id,
                SyncConflict.resolved_at.is_(None)
            )
        )
    ).all()

    # Determine if sync is needed (hasn't synced in over 1 hour)
    needs_sync = (
        device.last_sync_at is None or
        (datetime.now(timezone.utc) - device.last_sync_at).total_seconds() > 3600
    )

    device_info = DeviceInfo(
        device_id=device.device_id,
        device_name=device.device_name,
        device_type=device.device_type.value,
        platform=device.platform.value,
        os_version=device.os_version,
        app_version=device.app_version,
        last_sync_at=device.last_sync_at,
        last_seen_at=device.last_seen_at,
        is_active=device.is_active,
        registered_at=device.registered_at
    )

    return SyncStatusResponse(
        device=device_info,
        sync_states=entity_sync_states,
        pending_conflicts=len(pending_conflicts_count),
        needs_sync=needs_sync,
        last_successful_sync=device.last_sync_at
    )
