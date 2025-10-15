# app/routers/auth_enhanced.py
"""
Enhanced authentication routes with production-grade JWT token management.
This file demonstrates the integration of all security features.
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select
from typing import Dict, Any

from app.core.auth import (
    verify_password, get_password_hash, verify_token,
    is_user_locked, increment_login_attempts, reset_login_attempts, generate_token
)
from app.core.audit_log import (
    get_audit_logger, AuditEvent, AuditEventType, AuditEventSeverity
)
from app.core.auth_helpers import (
    get_client_ip, get_user_agent, check_login_rate_limit,
    check_register_rate_limit, check_token_refresh_rate_limit,
    check_password_reset_rate_limit, reset_login_rate_limit, log_and_create_tokens
)
from app.core.token_manager import (
    get_token_blacklist, revoke_refresh_token_family,
    revoke_all_user_tokens, revoke_token
)
from app.core.audit_log import get_audit_logger
from app.core.rate_limiter import RateLimitExceeded
from app.core.deps import get_current_active_user, get_db, get_current_user
from app.core.config import settings
from app.core.email import send_verification_email, send_password_reset_email
from app.models.user import User, UserType
from app.schemas.auth import (
    LoginRequest, RegisterRequest, Token, RefreshTokenRequest,
    UserProfile, PasswordResetRequest, PasswordReset, ChangePassword,
    ResendVerificationRequest
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.

    Features:
    - Rate limiting by IP address
    - Account lockout after failed attempts
    - Audit logging
    - Token rotation with family tracking
    """
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    audit_logger = get_audit_logger()

    # Rate limiting by IP
    try:
        check_login_rate_limit(ip_address or "unknown")
    except RateLimitExceeded as e:
        audit_logger.log_login_failed(
            email=login_data.email,
            reason="Rate limit exceeded",
            ip_address=ip_address,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Retry after {e.retry_after} seconds.",
            headers={"Retry-After": str(e.retry_after)}
        )

    # Find user by email
    user = db.exec(select(User).where(User.email == login_data.email)).first()

    if not user:
        audit_logger.log_login_failed(
            email=login_data.email,
            reason="User not found",
            ip_address=ip_address,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check if user is locked
    if is_user_locked(user):
        audit_logger.log_login_failed(
            email=login_data.email,
            reason="Account locked",
            ip_address=ip_address,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked due to too many failed attempts. Try again later."
        )

    # Check if user is active
    if not user.is_active:
        audit_logger.log_login_failed(
            email=login_data.email,
            reason="Account deactivated",
            ip_address=ip_address,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )

    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        increment_login_attempts(db, user)
        audit_logger.log_login_failed(
            email=login_data.email,
            reason="Invalid password",
            ip_address=ip_address,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Reset login attempts on successful login
    reset_login_attempts(db, user)
    reset_login_rate_limit(ip_address or "unknown")

    # Create tokens with audit logging
    access_token, refresh_token, token_family = log_and_create_tokens(
        user_id=user.id,
        email=user.email,
        ip_address=ip_address,
        user_agent=user_agent
    )

    # Store refresh token family in database
    user.refresh_token_hash = get_password_hash(refresh_token)
    user.refresh_token_expires = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    user.token_family = token_family
    db.commit()

    # Log successful login
    audit_logger.log_login_success(
        user_id=user.id,
        email=user.email,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Features:
    - Token rotation (new refresh token on each use)
    - Reuse detection (revokes entire family if reused)
    - Rate limiting
    - Audit logging
    """
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    audit_logger = get_audit_logger()
    blacklist = get_token_blacklist()

    # Rate limiting
    try:
        check_token_refresh_rate_limit(ip_address or "unknown")
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many refresh attempts. Retry after {e.retry_after} seconds.",
            headers={"Retry-After": str(e.retry_after)}
        )

    # Verify refresh token
    token_data = verify_token(refresh_data.refresh_token, token_type="refresh")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Find user
    user = db.exec(select(User).where(User.id == token_data.user_id)).first()
    if not user or not user.refresh_token_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Check if refresh token is expired
    if user.refresh_token_expires and user.refresh_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )

    # Verify refresh token hash
    if not verify_password(refresh_data.refresh_token, user.refresh_token_hash):
        # Token reuse detected - revoke entire family
        if token_data.token_family:
            revoked_count = revoke_refresh_token_family(token_data.token_family)
            audit_logger.log_token_reuse_detected(
                user_id=user.id,
                token_family=token_data.token_family,
                ip_address=ip_address
            )

        # Clear user's refresh token
        user.refresh_token_hash = None
        user.refresh_token_expires = None
        user.token_family = None
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token - token reuse detected"
        )

    # Revoke old refresh token (add to blacklist)
    if token_data.jti:
        revoke_token(token_data.jti, user.refresh_token_expires)

    # Create new tokens (rotate refresh token, keep same family)
    access_token, new_refresh_token, token_family = log_and_create_tokens(
        user_id=user.id,
        email=user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        token_family=token_data.token_family  # Maintain same family
    )

    # Update stored refresh token
    user.refresh_token_hash = get_password_hash(new_refresh_token)
    user.refresh_token_expires = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    user.token_family = token_family
    db.commit()

    # Log token refresh
    audit_logger.log_token_refreshed(
        user_id=user.id,
        ip_address=ip_address
    )

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout and revoke all tokens.

    Features:
    - Revokes all tokens for the user
    - Audit logging
    """
    ip_address = get_client_ip(request)
    audit_logger = get_audit_logger()

    # Revoke all user tokens
    revoked_count = revoke_all_user_tokens(current_user.id)

    # Clear refresh token from database
    current_user.refresh_token_hash = None
    current_user.refresh_token_expires = None
    current_user.token_family = None
    db.commit()

    # Log logout
    audit_logger.log_token_revoked(
        user_id=current_user.id,
        reason="User logout",
        ip_address=ip_address
    )

    return {
        "message": "Successfully logged out",
        "tokens_revoked": revoked_count
    }


@router.post("/logout-all-devices")
async def logout_all_devices(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout from all devices by revoking all tokens.

    Features:
    - Revokes all tokens across all devices
    - Audit logging
    """
    ip_address = get_client_ip(request)
    audit_logger = get_audit_logger()

    # Revoke all user tokens
    revoked_count = revoke_all_user_tokens(current_user.id)

    # Clear refresh token from database
    current_user.refresh_token_hash = None
    current_user.refresh_token_expires = None
    current_user.token_family = None
    db.commit()

    # Log logout
    audit_logger.log_token_revoked(
        user_id=current_user.id,
        reason="Logout from all devices",
        ip_address=ip_address
    )

    return {
        "message": "Successfully logged out from all devices",
        "tokens_revoked": revoked_count
    }


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user profile."""
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


@router.get("/audit-log")
async def get_audit_log(
    current_user: User = Depends(get_current_active_user),
    limit: int = 50
):
    """
    Get audit log for the current user.

    Note: In production, this should be restricted to admins or
    implement proper authorization.
    """
    audit_logger = get_audit_logger()
    events = audit_logger.get_events(
        user_id=current_user.id,
        limit=limit
    )

    return {
        "events": [event.to_dict() for event in events],
        "count": len(events)
    }


@router.post("/register", response_model=Dict[str, str])
async def register(
    register_data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    Features:
    - Rate limiting (3 per hour per IP)
    - Email uniqueness validation
    - Password strength validation
    - Email verification token generation
    - Audit logging
    """
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    audit_logger = get_audit_logger()

    # Rate limiting
    try:
        check_register_rate_limit(ip_address or "unknown")
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many registration attempts. Retry after {e.retry_after} seconds.",
            headers={"Retry-After": str(e.retry_after)}
        )

    # Check if user already exists
    existing_user = db.exec(select(User).where(User.email == register_data.email)).first()
    if existing_user:
        # Don't reveal if email exists (prevent enumeration)
        audit_logger.log_event(

            AuditEvent(
                event_type=AuditEventType.ACCOUNT_CREATED,
                severity=AuditEventSeverity.WARNING,
                timestamp=datetime.now(timezone.utc),
                email=register_data.email,
                ip_address=ip_address,
                success=False,
                error_message="Email already registered"
            )
        )
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
        email_verification_expires=datetime.now(timezone.utc) + timedelta(hours=24)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Log account creation

    audit_logger.log_event(
        AuditEvent(
            event_type=AuditEventType.ACCOUNT_CREATED,
            severity=AuditEventSeverity.INFO,
            timestamp=datetime.now(timezone.utc),
            user_id=user.id,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            details={"user_type": register_data.user_type}
        )
    )

    # Send verification email
    try:
        await send_verification_email(
            email=user.email,
            token=user.email_verification_token,
            name=user.name
        )
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        # Continue even if email fails - user is registered

    return {"message": "User registered successfully. Please check your email to verify your account."}


@router.post("/verify-email")
async def verify_email(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verify user email address.

    Features:
    - Token validation
    - Expiration checking
    - Audit logging
    """
    ip_address = get_client_ip(request)
    audit_logger = get_audit_logger()

    user = db.exec(select(User).where(User.email_verification_token == token)).first()

    if not user or not user.email_verification_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    if user.email_verification_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )

    # Verify email and clear token
    user.is_email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    db.commit()

    # Log email verification

    audit_logger.log_event(
        AuditEvent(
            event_type=AuditEventType.EMAIL_VERIFIED,
            severity=AuditEventSeverity.INFO,
            timestamp=datetime.now(timezone.utc),
            user_id=user.id,
            email=user.email,
            ip_address=ip_address,
            success=True
        )
    )

    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(
    request_data: ResendVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Resend email verification link.

    Features:
    - Email enumeration protection
    - Already verified check
    - Token regeneration
    - Audit logging
    """
    ip_address = get_client_ip(request)
    audit_logger = get_audit_logger()

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
    user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit()

    # Send verification email
    try:
        await send_verification_email(
            email=user.email,
            token=user.email_verification_token,
            name=user.name
        )
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")

    # Log event
    audit_logger.log_event(
        AuditEvent(
            event_type=AuditEventType.EMAIL_VERIFICATION_SENT,
            severity=AuditEventSeverity.INFO,
            timestamp=datetime.now(timezone.utc),
            user_id=user.id,
            email=user.email,
            ip_address=ip_address,
            success=True
        )
    )

    return {"message": "Verification email sent successfully"}


@router.post("/forgot-password")
async def forgot_password(
    reset_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request password reset link.

    Features:
    - Rate limiting (3 per hour)
    - Email enumeration protection
    - Secure token generation
    - Audit logging
    """
    ip_address = get_client_ip(request)
    audit_logger = get_audit_logger()

    # Rate limiting
    try:
        check_password_reset_rate_limit(ip_address or "unknown")
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many password reset attempts. Retry after {e.retry_after} seconds.",
            headers={"Retry-After": str(e.retry_after)}
        )

    user = db.exec(select(User).where(User.email == reset_data.email)).first()

    if user:
        # Generate reset token
        user.password_reset_token = generate_token()
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()

        # Send password reset email
        try:
            await send_password_reset_email(
                email=user.email,
                token=user.password_reset_token,
                name=user.name
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {e}")

        # Log event
        audit_logger.log_event(
            AuditEvent(
                event_type=AuditEventType.PASSWORD_RESET_REQUESTED,
                severity=AuditEventSeverity.INFO,
                timestamp=datetime.now(timezone.utc),
                user_id=user.id,
                email=user.email,
                ip_address=ip_address,
                success=True
            )
        )

    # Always return success to prevent email enumeration
    return {"message": "If an account with this email exists, you will receive a password reset link."}


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token.

    Features:
    - Token validation
    - Expiration checking
    - Token revocation (all refresh tokens)
    - Audit logging
    """
    ip_address = get_client_ip(request)
    audit_logger = get_audit_logger()

    user = db.exec(select(User).where(User.password_reset_token == reset_data.token)).first()

    if not user or not user.password_reset_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    if user.password_reset_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    # Update password and clear reset token
    user.password_hash = get_password_hash(reset_data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None

    # Invalidate all refresh tokens for security
    user.refresh_token_hash = None
    user.refresh_token_expires = None
    user.token_family = None

    # Revoke all existing tokens
    revoke_all_user_tokens(user.id)

    db.commit()

    # Log password reset

    audit_logger.log_event(
        AuditEvent(
            event_type=AuditEventType.PASSWORD_RESET_COMPLETED,
            severity=AuditEventSeverity.INFO,
            timestamp=datetime.now(timezone.utc),
            user_id=user.id,
            email=user.email,
            ip_address=ip_address,
            success=True
        )
    )

    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change password for authenticated user.

    Features:
    - Current password verification
    - Password strength validation
    - Token revocation (all refresh tokens)
    - Audit logging
    """
    ip_address = get_client_ip(request)
    audit_logger = get_audit_logger()

    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        audit_logger.log_event(

            AuditEvent(
                event_type=AuditEventType.PASSWORD_CHANGED,
                severity=AuditEventSeverity.WARNING,
                timestamp=datetime.now(timezone.utc),
                user_id=current_user.id,
                email=current_user.email,
                ip_address=ip_address,
                success=False,
                error_message="Incorrect current password"
            )
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)

    # Invalidate all refresh tokens for security
    current_user.refresh_token_hash = None
    current_user.refresh_token_expires = None
    current_user.token_family = None

    # Revoke all existing tokens
    revoke_all_user_tokens(current_user.id)

    db.commit()

    # Log password change
    audit_logger.log_password_changed(
        user_id=current_user.id,
        email=current_user.email,
        ip_address=ip_address
    )

    return {"message": "Password changed successfully. Please login again with your new password."}


@router.get("/permissions", response_model=Dict[str, Any])
async def get_user_permissions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's permissions and dashboard configuration.

    Returns user type, permissions, and dashboard config.
    """
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


@router.get("/validate-token", response_model=Dict[str, Any])
async def validate_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate current JWT token and return user info.

    Does not require active user (just valid token).
    """
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
