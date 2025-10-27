# app/models/analytics.py
from sqlmodel import SQLModel, Field, Relationship, Column, Text, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"
    success = "success"

class Notification(SQLModel, table=True):
    __tablename__ = "notifications"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=150)
    message: str = Field(sa_column=Column(Text))
    type: NotificationType = Field(default=NotificationType.info)
    related_project_id: Optional[int] = Field(default=None, foreign_key="projects.id")
    related_task_id: Optional[int] = Field(default=None, foreign_key="tasks.id")
    is_read: bool = Field(default=False, index=True)
    read_at: Optional[datetime] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

class ActivityLog(SQLModel, table=True):
    __tablename__ = "activity_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    project_id: Optional[int] = Field(default=None, foreign_key="projects.id")
    task_id: Optional[int] = Field(default=None, foreign_key="tasks.id")
    volunteer_id: Optional[int] = Field(default=None, foreign_key="volunteers.id")
    action: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    old_values: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    new_values: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

class MetricType(str, Enum):
    """Types of metrics that can be tracked over time."""
    volunteer_hours = "volunteer_hours"
    project_progress = "project_progress"
    task_completion = "task_completion"
    volunteer_count = "volunteer_count"
    resource_utilization = "resource_utilization"
    environmental_impact = "environmental_impact"
    budget_spent = "budget_spent"
    custom = "custom"

class MetricSnapshot(SQLModel, table=True):
    """
    Time-series data model for tracking various metrics over time.
    Enables historical analysis and trend visualization.
    """
    __tablename__ = "metric_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    metric_type: MetricType = Field(index=True, description="Type of metric being tracked")
    metric_name: str = Field(max_length=150, description="Human-readable name of the metric")
    value: float = Field(description="Numeric value of the metric at this point in time")
    unit: Optional[str] = Field(default=None, max_length=50, description="Unit of measurement (e.g., 'hours', 'percentage', 'count')")

    # Relations - link to entity being measured (all optional)
    project_id: Optional[int] = Field(default=None, foreign_key="projects.id", index=True)
    task_id: Optional[int] = Field(default=None, foreign_key="tasks.id", index=True)
    volunteer_id: Optional[int] = Field(default=None, foreign_key="volunteers.id", index=True)

    # Additional context
    metric_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Additional contextual data")
    recorded_by_id: Optional[int] = Field(default=None, foreign_key="users.id", description="User who recorded this metric")

    # Timestamps
    snapshot_date: datetime = Field(default_factory=datetime.utcnow, index=True, description="Date/time when this snapshot was taken")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Dashboard(SQLModel, table=True):
    """
    User-customizable dashboard configurations.
    Stores widget preferences and layout for personalized analytics views.
    """
    __tablename__ = "dashboards"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=150, description="Dashboard name")
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_default: bool = Field(default=False, description="Whether this is the user's default dashboard")

    # Dashboard configuration
    widgets: Dict[str, Any] = Field(sa_column=Column(JSON), description="Widget configurations and layout")
    filters: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Applied filters")

    # Sharing and visibility
    is_public: bool = Field(default=False, description="Whether this dashboard is shared with others")
    shared_with_users: Optional[List[int]] = Field(default=None, sa_column=Column(JSON), description="List of user IDs with access")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)