# app/routers/auth.py
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header
from sqlmodel import Session, select
from typing import Dict, Any, Optional

from app.core.auth import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, verify_token, is_user_locked, 
    increment_login_attempts, reset_login_attempts, generate_token
)
from app.core.deps import get_current_active_user, get_db, get_current_user
from app.core.config import settings
from app.models.user import User, UserType
from app.schemas.auth import (
    LoginRequest, RegisterRequest, Token, PasswordResetRequest, 
    PasswordReset, ChangePassword, UserProfile, RefreshTokenRequest, ResendVerificationRequest
)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/validate-token", response_model=Dict[str, Any])
async def validate_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate current JWT token and return user info."""
    try:
        user_type = db.exec(select(UserType).where(UserType.id == current_user.user_type_id)).first()
        
        return {
            "valid": True,
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "user_type": user_type.name if user_type else None,
                "is_active": current_user.is_active,
                "is_email_verified": current_user.is_email_verified
            }
        }
    except Exception:
        return {"valid": False, "user": None}

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    # Check if user is already logged in with valid token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        token_data = verify_token(token)
        if token_data:
            existing_user = db.exec(select(User).where(User.id == token_data.user_id)).first()
            if existing_user and existing_user.is_active and existing_user.email == login_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already logged in with a valid token"
                )
    
    # Find user by email
    user = db.exec(select(User).where(User.email == login_data.email)).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is locked
    if is_user_locked(user):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked due to too many failed attempts. Try again later."
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        increment_login_attempts(db, user)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Reset login attempts on successful login
    reset_login_attempts(db, user)
    
    # Create tokens
    token_data = {"sub": user.id, "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Store refresh token hash
    user.refresh_token_hash = get_password_hash(refresh_token)
    user.refresh_token_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/register", response_model=Dict[str, str])
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = db.exec(select(User).where(User.email == register_data.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Get user type
    user_type = db.exec(select(UserType).where(UserType.name == register_data.user_type)).first()
    if not user_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user type"
        )
    
    # Create new user
    user = User(
        name=register_data.name,
        email=register_data.email,
        password_hash=get_password_hash(register_data.password),
        phone=register_data.phone,
        user_type_id=user_type.id,
        is_email_verified=False,
        email_verification_token=generate_token(),
        email_verification_expires=datetime.now(timezone.utc)  + timedelta(hours=24)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # TODO: Send verification email in background task
    
    return {"message": "User registered successfully. Please check your email to verify your account."}

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    # Verify refresh token
    token_data = verify_token(refresh_data.refresh_token, token_type="refresh")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Find user and verify stored refresh token
    user = db.exec(select(User).where(User.id == token_data.user_id)).first()
    if not user or not user.refresh_token_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if refresh token is expired
    if user.refresh_token_expires and user.refresh_token_expires < datetime.now(timezone.utc) :
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )
    
    # Verify refresh token hash
    if not verify_password(refresh_data.refresh_token, user.refresh_token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new tokens
    new_token_data = {"sub": user.id, "email": user.email}
    access_token = create_access_token(new_token_data)
    new_refresh_token = create_refresh_token(new_token_data)
    
    # Update stored refresh token
    user.refresh_token_hash = get_password_hash(new_refresh_token)
    user.refresh_token_expires = datetime.now(timezone.utc)  + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Clear refresh token
    current_user.refresh_token_hash = None
    current_user.refresh_token_expires = None
    db.commit()
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    user_type = db.exec(select(UserType).where(UserType.id == current_user.user_type_id)).first()
    
    return UserProfile(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        user_type=user_type.name,
        is_active=current_user.is_active,
        is_email_verified=current_user.is_email_verified,
        last_login=current_user.last_login,
        created_at=current_user.created_at
    )

@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    
    # Invalidate all refresh tokens
    current_user.refresh_token_hash = None
    current_user.refresh_token_expires = None
    
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/forgot-password")
async def forgot_password(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    user = db.exec(select(User).where(User.email == reset_data.email)).first()
    
    if user:
        # Generate reset token
        user.password_reset_token = generate_token()
        user.password_reset_expires = datetime.now(timezone.utc)  + timedelta(hours=1)
        db.commit()
        
        # TODO: Send password reset email in background task
        # background_tasks.add_task(send_password_reset_email, user.email, user.password_reset_token)
    
    # Always return success to prevent email enumeration
    return {"message": "If an account with this email exists, you will receive a password reset link."}

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    user = db.exec(select(User).where(User.password_reset_token == reset_data.token)).first()
    
    if not user or not user.password_reset_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    if user.password_reset_expires < datetime.now(timezone.utc) :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Update password and clear reset token
    user.password_hash = get_password_hash(reset_data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    
    # Invalidate all refresh tokens
    user.refresh_token_hash = None
    user.refresh_token_expires = None
    
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    user = db.exec(select(User).where(User.email_verification_token == token)).first()
    
    if not user or not user.email_verification_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    if user.email_verification_expires < datetime.now(timezone.utc) :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )
    
    # Verify email and clear token
    user.is_email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    
    db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(
    request_data: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    user = db.exec(select(User).where(User.email == request_data.email)).first()
    
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If an account with this email exists, a verification email will be sent."}
    
    if user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Generate new verification token
    user.email_verification_token = generate_token()
    user.email_verification_expires = datetime.now(timezone.utc)  + timedelta(hours=24)
    db.commit()
    
    # TODO: Send verification email in background task
    
    return {"message": "Verification email sent successfully"}

@router.get("/status", response_model=Dict[str, Any])
async def get_auth_status(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Check authentication status without requiring valid token."""
    if not authorization or not authorization.startswith("Bearer "):
        return {
            "authenticated": False,
            "user": None,
            "message": "No token provided"
        }
    
    token = authorization.split(" ")[1]
    token_data = verify_token(token)
    
    if not token_data:
        return {
            "authenticated": False,
            "user": None,
            "message": "Invalid token"
        }
    
    user = db.exec(select(User).where(User.id == token_data.user_id)).first()
    if not user:
        return {
            "authenticated": False,
            "user": None,
            "message": "User not found"
        }
    
    user_type = db.exec(select(UserType).where(UserType.id == user.user_type_id)).first()
    
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "user_type": user_type.name if user_type else None,
            "is_active": user.is_active,
            "is_email_verified": user.is_email_verified,
            "permissions": user_type.permissions if user_type else None,
            "dashboard_config": user_type.dashboard_config if user_type else None
        },
        "message": "Valid token"
    }

@router.get("/permissions", response_model=Dict[str, Any])
async def get_user_permissions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's permissions and dashboard configuration."""
    user_type = db.exec(select(UserType).where(UserType.id == current_user.user_type_id)).first()
    
    if not user_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User type not found"
        )
    
    return {
        "user_type": user_type.name,
        "permissions": user_type.permissions,
        "dashboard_config": user_type.dashboard_config,
        "description": user_type.description
    }
