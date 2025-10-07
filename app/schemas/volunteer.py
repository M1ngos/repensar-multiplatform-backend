# app/schemas/volunteer.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from enum import Enum

# Enums
class VolunteerStatus(str, Enum):
    active = "active"
    inactive = "inactive" 
    suspended = "suspended"

class BackgroundCheckStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    not_required = "not_required"

class ProficiencyLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"

# Volunteer Skills Schemas
class VolunteerSkillBase(BaseModel):
    name: str = Field(..., max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: bool = True

class VolunteerSkillCreate(VolunteerSkillBase):
    pass

class VolunteerSkill(VolunteerSkillBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Volunteer Skill Assignment Schemas
class VolunteerSkillAssignmentBase(BaseModel):
    skill_id: int
    proficiency_level: ProficiencyLevel = ProficiencyLevel.beginner
    years_experience: int = Field(0, ge=0)
    certified: bool = False
    notes: Optional[str] = None

class VolunteerSkillAssignmentCreate(VolunteerSkillAssignmentBase):
    pass

class VolunteerSkillAssignmentUpdate(BaseModel):
    proficiency_level: Optional[ProficiencyLevel] = None
    years_experience: Optional[int] = Field(None, ge=0)
    certified: Optional[bool] = None
    notes: Optional[str] = None

class VolunteerSkillAssignment(VolunteerSkillAssignmentBase):
    id: int
    volunteer_id: int
    created_at: datetime
    skill: VolunteerSkill
    
    class Config:
        from_attributes = True

# Volunteer Base Schemas
class VolunteerBase(BaseModel):
    volunteer_id: str = Field(..., max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=30)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    availability: Optional[Dict[str, Any]] = None
    volunteer_status: VolunteerStatus = VolunteerStatus.active
    background_check_status: BackgroundCheckStatus = BackgroundCheckStatus.pending
    orientation_completed: bool = False
    orientation_date: Optional[date] = None
    joined_date: date
    motivation: Optional[str] = None
    notes: Optional[str] = None

class VolunteerCreate(VolunteerBase):
    user_id: int
    
    @field_validator('volunteer_id')
    def validate_volunteer_id(cls, v):
        if not v.startswith('VLT'):
            raise ValueError('Volunteer ID must start with "VLT"')
        return v

class VolunteerUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=30)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    availability: Optional[Dict[str, Any]] = None
    volunteer_status: Optional[VolunteerStatus] = None
    background_check_status: Optional[BackgroundCheckStatus] = None
    orientation_completed: Optional[bool] = None
    orientation_date: Optional[date] = None
    motivation: Optional[str] = None
    notes: Optional[str] = None

class VolunteerProfile(VolunteerBase):
    id: int
    user_id: int
    total_hours_contributed: float
    created_at: datetime
    updated_at: datetime
    
    # User information
    name: str
    email: str
    phone: Optional[str]
    
    # Skills
    skills: List[VolunteerSkillAssignment] = []
    
    class Config:
        from_attributes = True

class Volunteer(VolunteerBase):
    id: int
    user_id: int
    total_hours_contributed: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Volunteer Time Log Schemas
class VolunteerTimeLogBase(BaseModel):
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    hours: float = Field(..., gt=0)
    activity_description: Optional[str] = None
    supervisor_id: Optional[int] = None

class VolunteerTimeLogCreate(VolunteerTimeLogBase):
    volunteer_id: int
    
    @field_validator('hours')
    def validate_hours(cls, v, values=None):
        if v <= 0:
            raise ValueError('Hours must be greater than 0')
        if v > 24:
            raise ValueError('Hours cannot exceed 24 per day')
        return v

class VolunteerTimeLogUpdate(BaseModel):
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    hours: Optional[float] = Field(None, gt=0)
    activity_description: Optional[str] = None
    supervisor_id: Optional[int] = None
    
    @field_validator('hours')
    def validate_hours(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('Hours must be greater than 0')
            if v > 24:
                raise ValueError('Hours cannot exceed 24 per day')
        return v

class VolunteerTimeLogApproval(BaseModel):
    approved: bool
    
class VolunteerTimeLog(VolunteerTimeLogBase):
    id: int
    volunteer_id: int
    approved: bool
    approved_at: Optional[datetime]
    approved_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # Related data
    project_name: Optional[str] = None
    task_title: Optional[str] = None
    supervisor_name: Optional[str] = None
    approved_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Training Schemas
class VolunteerTrainingBase(BaseModel):
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    is_mandatory: bool = False
    duration_hours: Optional[float] = Field(None, ge=0)
    valid_for_months: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=50)

class VolunteerTrainingCreate(VolunteerTrainingBase):
    pass

class VolunteerTraining(VolunteerTrainingBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class VolunteerTrainingRecordBase(BaseModel):
    training_id: int
    completed_date: Optional[date] = None
    expires_date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    trainer_id: Optional[int] = None
    certificate_issued: bool = False
    notes: Optional[str] = None

class VolunteerTrainingRecordCreate(VolunteerTrainingRecordBase):
    volunteer_id: int

class VolunteerTrainingRecord(VolunteerTrainingRecordBase):
    id: int
    volunteer_id: int
    created_at: datetime
    
    # Related data
    training_name: str
    trainer_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Registration Schema
class VolunteerRegistration(BaseModel):
    # User information
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)
    phone: Optional[str] = Field(None, max_length=20)
    
    # Volunteer specific information
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=30)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    availability: Optional[Dict[str, Any]] = None
    motivation: Optional[str] = None
    
    # Skills
    skill_ids: List[int] = []

# Summary Schemas
class VolunteerSummary(BaseModel):
    id: int
    volunteer_id: str
    name: str
    email: str
    volunteer_status: VolunteerStatus
    total_hours_contributed: float
    joined_date: date
    skills_count: int
    recent_activity: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class VolunteerStats(BaseModel):
    total_volunteers: int
    active_volunteers: int
    total_hours: float
    volunteers_by_status: Dict[str, int]
    volunteers_by_skill: Dict[str, int]
    recent_registrations: int  # Last 30 days