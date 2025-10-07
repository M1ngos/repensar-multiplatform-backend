# app/models/task.py
from sqlmodel import SQLModel, Field, Relationship, Column, Text, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

class TaskStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class DependencyType(str, Enum):
    finish_to_start = "finish_to_start"
    start_to_start = "start_to_start"
    finish_to_finish = "finish_to_finish"
    start_to_finish = "start_to_finish"

class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    parent_task_id: Optional[int] = Field(default=None, foreign_key="tasks.id")
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    status: TaskStatus = Field(default=TaskStatus.not_started, index=True)
    priority: TaskPriority = Field(default=TaskPriority.medium)
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    estimated_hours: Optional[Decimal] = Field(default=None, max_digits=6, decimal_places=2)
    actual_hours: Decimal = Field(default=Decimal("0.00"), max_digits=6, decimal_places=2)
    progress_percentage: int = Field(default=0, ge=0, le=100)
    assigned_to_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    created_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    suitable_for_volunteers: bool = Field(default=False, index=True)
    required_skills: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    volunteer_spots: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    project: "Project" = Relationship(back_populates="tasks")
    parent_task: Optional["Task"] = Relationship(back_populates="subtasks", sa_relationship_kwargs={"remote_side": "Task.id"})
    subtasks: List["Task"] = Relationship(back_populates="parent_task")
    volunteer_assignments: List["TaskVolunteer"] = Relationship(back_populates="task")
    time_logs: List["VolunteerTimeLog"] = Relationship(back_populates="task")
    predecessor_dependencies: List["TaskDependency"] = Relationship(back_populates="predecessor_task", sa_relationship_kwargs={"foreign_keys": "TaskDependency.predecessor_task_id"})
    successor_dependencies: List["TaskDependency"] = Relationship(back_populates="successor_task", sa_relationship_kwargs={"foreign_keys": "TaskDependency.successor_task_id"})

class TaskDependency(SQLModel, table=True):
    __tablename__ = "task_dependencies"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    predecessor_task_id: int = Field(foreign_key="tasks.id")
    successor_task_id: int = Field(foreign_key="tasks.id")
    dependency_type: DependencyType = Field(default=DependencyType.finish_to_start)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    predecessor_task: Task = Relationship(back_populates="predecessor_dependencies", sa_relationship_kwargs={"foreign_keys": "TaskDependency.predecessor_task_id"})
    successor_task: Task = Relationship(back_populates="successor_dependencies", sa_relationship_kwargs={"foreign_keys": "TaskDependency.successor_task_id"})

# Import references for relationships (already exists in volunteer.py)
from app.models.volunteer import TaskVolunteer, VolunteerTimeLog
from app.models.project import Project