# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime

def password_validator(v: str) -> str:
    if len(v) < 8:
        raise ValueError('Password must be at least 8 characters long')
    if not any(c.isupper() for c in v):
        raise ValueError('Password must contain at least one uppercase letter')
    if not any(c.islower() for c in v):
        raise ValueError('Password must contain at least one lowercase letter')
    if not any(c.isdigit() for c in v):
        raise ValueError('Password must contain at least one digit')
    return v

class TokenData(BaseModel):
    user_id: int
    email: Optional[str] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: Optional[str] = Field(None, max_length=20)
    user_type: str = Field(default="volunteer")  # Default registration type
    
    @field_validator('password')
    def validate_password(cls, v):
        return password_validator(v)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    def validate_password(cls, v):
        return password_validator(v)

class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    def validate_password(cls, v):
        return password_validator(v)

class UserProfile(BaseModel):
    id: int
    name: str
    email: str
    user_type: str
    is_active: bool
    is_email_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr
