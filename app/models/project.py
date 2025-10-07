# app/models/project.py
from sqlmodel import SQLModel, Field, Relationship, Column, Text
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

class ProjectCategory(str, Enum):
    reforestation = "reforestation"
    environmental_education = "environmental_education"
    waste_management = "waste_management"
    conservation = "conservation"
    research = "research"
    community_engagement = "community_engagement"
    climate_action = "climate_action"
    biodiversity = "biodiversity"
    other = "other"

class ProjectStatus(str, Enum):
    planning = "planning"
    in_progress = "in_progress"
    suspended = "suspended"
    completed = "completed"
    cancelled = "cancelled"

class ProjectPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class Project(SQLModel, table=True):
    __tablename__ = "projects"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    category: ProjectCategory = Field(index=True)
    status: ProjectStatus = Field(default=ProjectStatus.planning, index=True)
    priority: ProjectPriority = Field(default=ProjectPriority.medium)
    start_date: Optional[date] = Field(default=None, index=True)
    end_date: Optional[date] = Field(default=None, index=True)
    budget: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    actual_cost: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    location_name: Optional[str] = Field(default=None, max_length=100)
    latitude: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=8)
    longitude: Optional[Decimal] = Field(default=None, max_digits=11, decimal_places=8)
    project_manager_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    created_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    requires_volunteers: bool = Field(default=False)
    min_volunteers: int = Field(default=0)
    max_volunteers: Optional[int] = Field(default=None)
    volunteer_requirements: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    team_members: List["ProjectTeam"] = Relationship(back_populates="project")
    tasks: List["Task"] = Relationship(back_populates="project")
    milestones: List["Milestone"] = Relationship(back_populates="project")
    resource_allocations: List["ProjectResource"] = Relationship(back_populates="project")
    environmental_metrics: List["EnvironmentalMetric"] = Relationship(back_populates="project")
    time_logs: List["VolunteerTimeLog"] = Relationship(back_populates="project")

class ProjectTeam(SQLModel, table=True):
    __tablename__ = "project_teams"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    role: Optional[str] = Field(default=None, max_length=50)
    is_volunteer: bool = Field(default=False, index=True)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    removed_at: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    
    # Relationships
    project: Project = Relationship(back_populates="team_members")

class Milestone(SQLModel, table=True):
    __tablename__ = "milestones"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    name: str = Field(max_length=150)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    target_date: date = Field(...)
    actual_date: Optional[date] = Field(default=None)
    status: str = Field(default="pending", max_length=20)  # pending, achieved, missed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    project: Project = Relationship(back_populates="milestones")

class EnvironmentalMetric(SQLModel, table=True):
    __tablename__ = "environmental_metrics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    metric_name: str = Field(max_length=100)
    metric_type: Optional[str] = Field(default=None, max_length=50)
    target_value: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=4)
    current_value: Decimal = Field(default=Decimal("0.0000"), max_digits=12, decimal_places=4)
    unit: Optional[str] = Field(default=None, max_length=20)
    measurement_date: Optional[date] = Field(default=None, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    recorded_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    project: Project = Relationship(back_populates="environmental_metrics")

# Import references for relationships
from app.models.volunteer import VolunteerTimeLog
from app.models.task import Task
from app.models.resource import ProjectResource