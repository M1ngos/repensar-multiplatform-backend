# app/models/volunteer.py
from sqlmodel import SQLModel, Field, Relationship, Column, Text, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from decimal import Decimal
import datetime as dt

class VolunteerSkill(SQLModel, table=True):
    __tablename__ = "volunteer_skills"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    category: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    skill_assignments: List["VolunteerSkillAssignment"] = Relationship(back_populates="skill")

class Volunteer(SQLModel, table=True):
    __tablename__ = "volunteers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    volunteer_id: str = Field(max_length=20, unique=True, index=True)
    date_of_birth: Optional[dt.date] = Field(default=None)
    gender: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = Field(default=None, sa_column=Column(Text))
    city: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    emergency_contact_name: Optional[str] = Field(default=None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(default=None, max_length=50)
    availability: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    volunteer_status: str = Field(default="active", max_length=20, index=True)
    background_check_status: str = Field(default="pending", max_length=20)
    orientation_completed: bool = Field(default=False)
    orientation_date: Optional[dt.date] = Field(default=None)
    total_hours_contributed: Decimal = Field(default=Decimal("0.00"), max_digits=8, decimal_places=2)
    joined_date: dt.date = Field(..., index=True)
    motivation: Optional[str] = Field(default=None, sa_column=Column(Text))
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    skill_assignments: List["VolunteerSkillAssignment"] = Relationship(back_populates="volunteer")
    time_logs: List["VolunteerTimeLog"] = Relationship(back_populates="volunteer")
    training_records: List["VolunteerTrainingRecord"] = Relationship(back_populates="volunteer")
    task_assignments: List["TaskVolunteer"] = Relationship(back_populates="volunteer")

class VolunteerSkillAssignment(SQLModel, table=True):
    __tablename__ = "volunteer_skill_assignments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    volunteer_id: int = Field(foreign_key="volunteers.id", index=True)
    skill_id: int = Field(foreign_key="volunteer_skills.id", index=True)
    proficiency_level: str = Field(default="beginner", max_length=20)
    years_experience: int = Field(default=0, ge=0)
    certified: bool = Field(default=False)
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    volunteer: Volunteer = Relationship(back_populates="skill_assignments")
    skill: VolunteerSkill = Relationship(back_populates="skill_assignments")

class VolunteerTimeLog(SQLModel, table=True):
    __tablename__ = "volunteer_time_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    volunteer_id: int = Field(foreign_key="volunteers.id", index=True)
    project_id: Optional[int] = Field(default=None, foreign_key="projects.id", index=True)
    task_id: Optional[int] = Field(default=None, foreign_key="tasks.id")
    date: dt.date = Field(..., index=True)
    start_time: Optional[time] = Field(default=None)
    end_time: Optional[time] = Field(default=None)
    hours: Decimal = Field(..., max_digits=4, decimal_places=2, gt=0)
    activity_description: Optional[str] = Field(default=None, sa_column=Column(Text))
    supervisor_id: Optional[int] = Field(default=None, foreign_key="users.id")
    approved: bool = Field(default=False, index=True)
    approved_at: Optional[datetime] = Field(default=None)
    approved_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    volunteer: "Volunteer" = Relationship(back_populates="time_logs")
    project: Optional["Project"] = Relationship(back_populates="time_logs")
    task: Optional["Task"] = Relationship(back_populates="time_logs")

class VolunteerTraining(SQLModel, table=True):
    __tablename__ = "volunteer_training"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=150)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_mandatory: bool = Field(default=False)
    duration_hours: Optional[Decimal] = Field(default=None, max_digits=4, decimal_places=2, ge=0)
    valid_for_months: Optional[int] = Field(default=None, ge=0)
    category: Optional[str] = Field(default=None, max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    training_records: List["VolunteerTrainingRecord"] = Relationship(back_populates="training")

class VolunteerTrainingRecord(SQLModel, table=True):
    __tablename__ = "volunteer_training_records"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    volunteer_id: int = Field(foreign_key="volunteers.id", index=True)
    training_id: int = Field(foreign_key="volunteer_training.id")
    completed_date: Optional[dt.date] = Field(default=None)
    expires_date: Optional[dt.date] = Field(default=None, index=True)
    score: Optional[Decimal] = Field(default=None, max_digits=5, decimal_places=2, ge=0, le=100)
    trainer_id: Optional[int] = Field(default=None, foreign_key="users.id")
    certificate_issued: bool = Field(default=False)
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    volunteer: Volunteer = Relationship(back_populates="training_records")
    training: VolunteerTraining = Relationship(back_populates="training_records")

# Models for project integration (referenced in volunteer models)
class TaskVolunteer(SQLModel, table=True):
    __tablename__ = "task_volunteers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="tasks.id", index=True)
    volunteer_id: int = Field(foreign_key="volunteers.id", index=True)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    removed_at: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    hours_contributed: Decimal = Field(default=Decimal("0.00"), max_digits=6, decimal_places=2)
    performance_rating: Optional[int] = Field(default=None, ge=1, le=5)
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Relationships
    volunteer: Volunteer = Relationship(back_populates="task_assignments")
    task: "Task" = Relationship(back_populates="volunteer_assignments")

# Import references for relationships
from app.models.project import Project
from app.models.task import Task
