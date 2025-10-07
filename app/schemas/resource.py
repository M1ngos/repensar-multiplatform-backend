# app/schemas/resource.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

from app.models.resource import ResourceType

# Resource Schemas
class ResourceBase(BaseModel):
    name: str = Field(..., max_length=100)
    type: ResourceType
    description: Optional[str] = None
    unit_cost: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=20)
    available_quantity: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=100)

class ResourceCreate(ResourceBase):
    pass

class ResourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit_cost: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=20)
    available_quantity: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class Resource(ResourceBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Project Resource Allocation Schemas
class ProjectResourceBase(BaseModel):
    quantity_allocated: float = Field(..., gt=0)
    allocation_date: Optional[date] = None
    notes: Optional[str] = None

class ProjectResourceCreate(ProjectResourceBase):
    resource_id: int

class ProjectResourceUpdate(BaseModel):
    quantity_allocated: Optional[float] = Field(None, gt=0)
    quantity_used: Optional[float] = Field(None, ge=0)
    allocation_date: Optional[date] = None
    notes: Optional[str] = None

class ProjectResourceAllocation(ProjectResourceBase):
    id: int
    project_id: int
    resource_id: int
    quantity_used: float
    allocated_by_id: Optional[int]
    
    # Additional fields for display
    resource_name: str
    resource_type: ResourceType
    resource_unit: Optional[str] = None
    allocated_by_name: Optional[str] = None
    utilization_percentage: float = 0.0
    
    class Config:
        from_attributes = True

class ResourceAllocationSummary(BaseModel):
    resource_id: int
    resource_name: str
    resource_type: ResourceType
    available_quantity: Optional[float]
    total_allocated: float
    total_used: float
    available_remaining: Optional[float]
    projects_count: int
    
    class Config:
        from_attributes = True

class ResourceStats(BaseModel):
    total_resources: int
    resources_by_type: dict
    total_allocations: int
    total_cost_allocated: float
    utilization_rate: float
    most_used_resources: List[dict]