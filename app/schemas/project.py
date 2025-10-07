# app/schemas/project.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from app.models.project import ProjectCategory, ProjectStatus, ProjectPriority

# Milestone Schemas
class MilestoneStatus(str, Enum):
    pending = "pending"
    achieved = "achieved"
    missed = "missed"
    cancelled = "cancelled"

class MilestoneBase(BaseModel):
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    target_date: date
    status: MilestoneStatus = MilestoneStatus.pending

class MilestoneCreate(MilestoneBase):
    project_id: int

class MilestoneUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    target_date: Optional[date] = None
    actual_date: Optional[date] = None
    status: Optional[MilestoneStatus] = None

class Milestone(MilestoneBase):
    id: int
    project_id: int
    actual_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Environmental Metrics Schemas
class EnvironmentalMetricBase(BaseModel):
    metric_name: str = Field(..., max_length=100)
    metric_type: Optional[str] = Field(None, max_length=50)
    target_value: Optional[float] = Field(None, ge=0)
    current_value: float = Field(0.0, ge=0)
    unit: Optional[str] = Field(None, max_length=20)
    measurement_date: Optional[date] = None
    description: Optional[str] = None

class EnvironmentalMetricCreate(EnvironmentalMetricBase):
    project_id: int
    recorded_by_id: Optional[int] = None

class EnvironmentalMetricUpdate(BaseModel):
    metric_name: Optional[str] = Field(None, max_length=100)
    metric_type: Optional[str] = Field(None, max_length=50)
    target_value: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=20)
    measurement_date: Optional[date] = None
    description: Optional[str] = None

class EnvironmentalMetric(EnvironmentalMetricBase):
    id: int
    project_id: int
    recorded_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # Additional fields for display
    recorded_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Project Team Schemas
class ProjectTeamBase(BaseModel):
    role: Optional[str] = Field(None, max_length=50)
    is_volunteer: bool = False

class ProjectTeamCreate(ProjectTeamBase):
    user_id: int

class ProjectTeamUpdate(BaseModel):
    role: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

class ProjectTeamMember(ProjectTeamBase):
    id: int
    project_id: int
    user_id: int
    assigned_at: datetime
    removed_at: Optional[datetime]
    is_active: bool
    
    # User information
    name: str
    email: str
    user_type: Optional[str] = None
    
    class Config:
        from_attributes = True

# Project Schemas
class ProjectBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    category: ProjectCategory
    status: ProjectStatus = ProjectStatus.planning
    priority: ProjectPriority = ProjectPriority.medium
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = Field(None, ge=0)
    location_name: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    requires_volunteers: bool = False
    min_volunteers: int = Field(0, ge=0)
    max_volunteers: Optional[int] = Field(None, ge=0)
    volunteer_requirements: Optional[str] = None

class ProjectCreate(ProjectBase):
    project_manager_id: Optional[int] = None
    created_by_id: Optional[int] = None
    
    @field_validator('end_date')
    def validate_end_date(cls, v, info):
        if v and info.data.get('start_date') and v < info.data.get('start_date'):
            raise ValueError('End date must be after start date')
        return v
    
    @field_validator('max_volunteers')
    def validate_max_volunteers(cls, v, info):
        min_vol = info.data.get('min_volunteers', 0)
        if v is not None and v < min_vol:
            raise ValueError('Maximum volunteers must be greater than or equal to minimum volunteers')
        return v

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[ProjectCategory] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = Field(None, ge=0)
    actual_cost: Optional[float] = Field(None, ge=0)
    location_name: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    project_manager_id: Optional[int] = None
    requires_volunteers: Optional[bool] = None
    min_volunteers: Optional[int] = Field(None, ge=0)
    max_volunteers: Optional[int] = Field(None, ge=0)
    volunteer_requirements: Optional[str] = None
    
    @field_validator('end_date')
    def validate_end_date(cls, v, info):
        if v and info.data.get('start_date') and v < info.data.get('start_date'):
            raise ValueError('End date must be after start date')
        return v

class Project(ProjectBase):
    id: int
    actual_cost: float
    project_manager_id: Optional[int]
    created_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProjectSummary(BaseModel):
    id: int
    name: str
    category: ProjectCategory
    status: ProjectStatus
    priority: ProjectPriority
    start_date: Optional[date]
    end_date: Optional[date]
    budget: Optional[float]
    actual_cost: float
    location_name: Optional[str]
    requires_volunteers: bool
    project_manager_name: Optional[str] = None
    team_size: int = 0
    volunteers_count: int = 0
    progress_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True

class ProjectDetail(Project):
    # Manager information
    project_manager_name: Optional[str] = None
    created_by_name: Optional[str] = None
    
    # Team and statistics
    team_members: List[ProjectTeamMember] = []
    milestones: List[Milestone] = []
    environmental_metrics: List[EnvironmentalMetric] = []
    
    # Summary statistics
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percentage: float = 0.0
    volunteer_hours: float = 0.0
    
    class Config:
        from_attributes = True

class ProjectDashboard(BaseModel):
    id: int
    name: str
    status: ProjectStatus
    category: ProjectCategory
    start_date: Optional[date]
    end_date: Optional[date]
    budget: Optional[float]
    actual_cost: float
    team_size: int
    volunteers_count: int
    total_tasks: int
    completed_tasks: int
    volunteer_hours: float
    progress_percentage: float = 0.0
    days_remaining: Optional[int] = None
    budget_utilization: Optional[float] = None
    
    class Config:
        from_attributes = True

class ProjectStats(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    projects_by_status: Dict[str, int]
    projects_by_category: Dict[str, int]
    total_budget: float
    total_spent: float
    total_volunteer_hours: float
    average_team_size: float