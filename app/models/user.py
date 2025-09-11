from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserType(SQLModel, table=True):
    __tablename__ = "user_types"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    users: List["User"] = Relationship(back_populates="user_type")

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    department: Optional[str] = Field(default=None, max_length=50)
    employee_id: Optional[str] = Field(default=None, max_length=50)
    
    # User type relationship
    user_type_id: int = Field(foreign_key="user_types.id")
    user_type: UserType = Relationship(back_populates="users")
    
    # Account status
    is_active: bool = Field(default=True)
    is_email_verified: bool = Field(default=False)
    
    # Email verification
    email_verification_token: Optional[str] = Field(default=None, max_length=255)
    email_verification_expires: Optional[datetime] = Field(default=None)
    
    # Password reset
    password_reset_token: Optional[str] = Field(default=None, max_length=255)
    password_reset_expires: Optional[datetime] = Field(default=None)
    
    # Security
    login_attempts: Optional[int] = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)
    
    # Token management
    refresh_token_hash: Optional[str] = Field(default=None, max_length=255)
    refresh_token_expires: Optional[datetime] = Field(default=None)
    
    # Timestamps
    last_login: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)