# app/schemas/task.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from app.models.task import TaskStatus, TaskPriority, DependencyType

# Task Dependency Schemas
class TaskDependencyBase(BaseModel):
    predecessor_task_id: int
    successor_task_id: int
    dependency_type: DependencyType = DependencyType.finish_to_start

class TaskDependencyCreate(TaskDependencyBase):
    @field_validator('successor_task_id')
    def validate_no_self_dependency(cls, v, info):
        if v == info.data.get('predecessor_task_id'):
            raise ValueError('Task cannot depend on itself')
        return v

class TaskDependency(TaskDependencyBase):
    id: int
    created_at: datetime
    
    # Related task titles for display
    predecessor_title: Optional[str] = None
    successor_title: Optional[str] = None
    
    class Config:
        from_attributes = True

# Task Volunteer Assignment Schemas
class TaskVolunteerBase(BaseModel):
    hours_contributed: float = Field(0.0, ge=0)
    performance_rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None

class TaskVolunteerCreate(BaseModel):
    volunteer_id: int

class TaskVolunteerUpdate(TaskVolunteerBase):
    is_active: Optional[bool] = None

class TaskVolunteerAssignment(TaskVolunteerBase):
    id: int
    task_id: int
    volunteer_id: int
    assigned_at: datetime
    removed_at: Optional[datetime]
    is_active: bool
    
    # Volunteer information
    volunteer_name: str
    volunteer_id_code: str
    volunteer_email: str
    
    class Config:
        from_attributes = True

# Task Schemas
class TaskBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.not_started
    priority: TaskPriority = TaskPriority.medium
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    progress_percentage: int = Field(0, ge=0, le=100)
    assigned_to_id: Optional[int] = None
    suitable_for_volunteers: bool = False
    required_skills: Optional[Dict[str, Any]] = None
    volunteer_spots: int = Field(0, ge=0)

class TaskCreate(TaskBase):
    project_id: int
    parent_task_id: Optional[int] = None
    created_by_id: Optional[int] = None
    
    @field_validator('end_date')
    def validate_end_date(cls, v, info):
        if v and info.data.get('start_date') and v < info.data.get('start_date'):
            raise ValueError('End date must be after start date')
        return v
    
    @field_validator('parent_task_id')
    def validate_parent_task(cls, v, info):
        # Note: Additional validation should be done in CRUD to ensure parent task belongs to same project
        return v

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    assigned_to_id: Optional[int] = None
    suitable_for_volunteers: Optional[bool] = None
    required_skills: Optional[Dict[str, Any]] = None
    volunteer_spots: Optional[int] = Field(None, ge=0)
    
    @field_validator('end_date')
    def validate_end_date(cls, v, info):
        if v and info.data.get('start_date') and v < info.data.get('start_date'):
            raise ValueError('End date must be after start date')
        return v

class Task(TaskBase):
    id: int
    project_id: int
    parent_task_id: Optional[int]
    actual_hours: float
    created_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TaskSummary(BaseModel):
    id: int
    title: str
    status: TaskStatus
    priority: TaskPriority
    start_date: Optional[date]
    end_date: Optional[date]
    estimated_hours: Optional[float]
    actual_hours: float
    progress_percentage: int
    suitable_for_volunteers: bool
    volunteer_spots: int
    project_name: str
    assigned_to_name: Optional[str] = None
    volunteers_assigned: int = 0
    days_remaining: Optional[int] = None
    is_overdue: bool = False
    
    class Config:
        from_attributes = True

class TaskDetail(Task):
    # Project information
    project_name: str
    project_status: str
    
    # Assignment information
    assigned_to_name: Optional[str] = None
    created_by_name: Optional[str] = None
    
    # Parent/child relationships
    parent_task_title: Optional[str] = None
    subtasks: List["TaskSummary"] = []
    
    # Volunteer assignments
    volunteer_assignments: List[TaskVolunteerAssignment] = []
    
    # Dependencies
    dependencies: List[TaskDependency] = []
    
    # Statistics
    completion_percentage: float = 0.0
    days_remaining: Optional[int] = None
    is_overdue: bool = False
    volunteer_hours: float = 0.0
    
    class Config:
        from_attributes = True

class TaskProgress(BaseModel):
    task_id: int
    title: str
    status: TaskStatus
    progress_percentage: int
    actual_hours: float
    estimated_hours: Optional[float]
    volunteer_hours: float = 0.0
    completion_date: Optional[date] = None
    
    class Config:
        from_attributes = True

class TaskStats(BaseModel):
    total_tasks: int
    not_started: int
    in_progress: int
    completed: int
    cancelled: int
    overdue_tasks: int
    volunteer_suitable_tasks: int
    total_estimated_hours: float
    total_actual_hours: float
    average_completion_time: Optional[float] = None  # in days
    completion_rate: float = 0.0  # percentage
    tasks_by_priority: Dict[str, int]
    tasks_by_project: Dict[str, int]

# Volunteer task assignment schemas for easier management
class VolunteerTaskAssignment(BaseModel):
    task_id: int
    task_title: str
    project_name: str
    status: TaskStatus
    priority: TaskPriority
    estimated_hours: Optional[float]
    start_date: Optional[date]
    end_date: Optional[date]
    required_skills: Optional[Dict[str, Any]]
    hours_contributed: float = 0.0
    assigned_at: datetime
    
    class Config:
        from_attributes = True

class TaskVolunteerMatch(BaseModel):
    task_id: int
    task_title: str
    project_name: str
    required_skills: Optional[Dict[str, Any]]
    volunteer_spots: int
    current_volunteers: int
    priority: TaskPriority
    start_date: Optional[date]
    end_date: Optional[date]
    match_score: float = 0.0  # Based on skill matching
    
    class Config:
        from_attributes = True