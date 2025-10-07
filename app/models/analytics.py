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