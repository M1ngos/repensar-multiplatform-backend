# app/schemas/user.py
"""User schemas for API responses and requests."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserTypeResponse(BaseModel):
    """User type information for responses."""
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    """Base user information (safe for public exposure)."""
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    department: Optional[str] = None
    employee_id: Optional[str] = None
    is_active: bool
    is_email_verified: bool
    profile_picture: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    """Minimal user information for listings."""
    id: int
    name: str
    email: EmailStr
    user_type_name: str
    department: Optional[str] = None
    is_active: bool
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True


class UserDetail(UserBase):
    """Detailed user information including user type."""
    user_type: UserTypeResponse
    oauth_provider: Optional[str] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=50)
    employee_id: Optional[str] = Field(None, max_length=50)
    profile_picture: Optional[str] = Field(None, max_length=500)

    class Config:
        from_attributes = True
