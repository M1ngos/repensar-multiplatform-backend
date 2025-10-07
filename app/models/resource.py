# app/models/resource.py
from sqlmodel import SQLModel, Field, Relationship, Column, Text
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

class ResourceType(str, Enum):
    human = "human"
    equipment = "equipment"
    material = "material"
    financial = "financial"

class Resource(SQLModel, table=True):
    __tablename__ = "resources"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    type: ResourceType = Field(index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    unit_cost: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    unit: Optional[str] = Field(default=None, max_length=20)
    available_quantity: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    location: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    project_allocations: List["ProjectResource"] = Relationship(back_populates="resource")

class ProjectResource(SQLModel, table=True):
    __tablename__ = "project_resources"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    resource_id: int = Field(foreign_key="resources.id", index=True)
    quantity_allocated: Decimal = Field(..., max_digits=10, decimal_places=2, gt=0)
    quantity_used: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2, ge=0)
    allocation_date: Optional[date] = Field(default=None)
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    allocated_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    
    # Relationships
    project: "Project" = Relationship(back_populates="resource_allocations")
    resource: Resource = Relationship(back_populates="project_allocations")

# Import references for relationships
from app.models.project import Project