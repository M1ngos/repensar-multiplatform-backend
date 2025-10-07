# app/routers/resources.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session
from typing import List, Optional

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.crud.resource import resource_crud, project_resource_crud
from app.crud.project import project_crud
from app.schemas.resource import (
    ResourceCreate, ResourceUpdate, Resource, ResourceStats,
    ProjectResourceCreate, ProjectResourceUpdate, ProjectResourceAllocation
)

router = APIRouter(
    prefix="/resources",
    tags=["resources"],
    responses={404: {"description": "Not found"}},
)

# ========================================
# RESOURCE ENDPOINTS
# ========================================

@router.post("/", response_model=Resource)
def create_resource(
    resource_data: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new resource."""
    if current_user.user_type.name not in ["admin", "project_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create resources"
        )
    
    resource = resource_crud.create_resource(db, resource_data)
    return Resource(**resource.model_dump())

@router.get("/", response_model=List[Resource])
def get_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    resource_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of resources."""
    resources = resource_crud.get_resources(db, skip=skip, limit=limit, resource_type=resource_type)
    return [Resource(**r.model_dump()) for r in resources]

@router.get("/stats", response_model=ResourceStats)
def get_resource_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get resource statistics."""
    stats = resource_crud.get_resource_stats(db)
    return ResourceStats(**stats)

@router.get("/{resource_id}", response_model=Resource)
def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get resource by ID."""
    resource = resource_crud.get_resource(db, resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    return Resource(**resource.model_dump())

# ========================================
# PROJECT RESOURCE ALLOCATION ENDPOINTS
# ========================================

@router.get("/projects/{project_id}/resources", response_model=List[ProjectResourceAllocation])
def get_project_resources(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get resources allocated to a project."""
    project = project_crud.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    resources_data = project_resource_crud.get_project_resources(db, project_id)
    
    allocations = []
    for data in resources_data:
        allocation = data["allocation"]
        resource = data["resource"]
        allocated_by = data["allocated_by"]
        
        utilization = 0.0
        if allocation.quantity_allocated > 0:
            utilization = (allocation.quantity_used / allocation.quantity_allocated) * 100
        
        allocations.append(ProjectResourceAllocation(
            **allocation.model_dump(),
            resource_name=resource.name,
            resource_type=resource.type,
            resource_unit=resource.unit,
            allocated_by_name=allocated_by.name if allocated_by else None,
            utilization_percentage=utilization
        ))
    
    return allocations

@router.post("/projects/{project_id}/resources", response_model=ProjectResourceAllocation)
def allocate_resource_to_project(
    project_id: int,
    allocation_data: ProjectResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Allocate resource to project."""
    project = project_crud.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if current_user.user_type.name not in ["admin", "project_manager"] and project.project_manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to allocate resources to this project"
        )
    
    resource = resource_crud.get_resource(db, allocation_data.resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    allocation = project_resource_crud.allocate_resource(db, project_id, allocation_data, current_user.id)
    
    return ProjectResourceAllocation(
        **allocation.model_dump(),
        resource_name=resource.name,
        resource_type=resource.type,
        resource_unit=resource.unit,
        allocated_by_name=current_user.name,
        utilization_percentage=0.0
    )