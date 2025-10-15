from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import secrets
import string

from app.core.config import settings
from app.schemas.auth import TokenData
from app.core.token_manager import (
    generate_jti,
    generate_token_family,
    TokenMetadata,
    TokenStatus,
    get_token_blacklist,
    is_token_revoked,
    revoke_token,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> str:
    """
    Create an access token with enhanced security claims.

    Args:
        data: Token payload data (must include 'sub' for user ID)
        expires_delta: Custom expiration time
        ip_address: Client IP address for tracking
        user_agent: Client user agent for tracking

    Returns:
        Encoded JWT access token
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Generate unique JWT ID
    jti = generate_jti()

    # Ensure 'sub' is a string as required by JWT spec
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    # Add security claims
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": jti,
        "type": "access",
    })

    # Store token metadata for tracking and revocation
    user_id = int(data.get("sub", 0))
    if user_id:
        metadata = TokenMetadata(
            jti=jti,
            user_id=user_id,
            token_family="",  # Access tokens don't use families
            issued_at=now,
            expires_at=expire,
            token_type="access",
            issued_from_ip=ip_address,
            user_agent=user_agent,
            status=TokenStatus.ACTIVE
        )
        blacklist = get_token_blacklist()
        blacklist.store_token_metadata(metadata)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    token_family: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> tuple[str, str]:
    """
    Create a refresh token with rotation support.

    Args:
        data: Token payload data (must include 'sub' for user ID)
        expires_delta: Custom expiration time
        token_family: Token family ID for rotation tracking (auto-generated if not provided)
        ip_address: Client IP address for tracking
        user_agent: Client user agent for tracking

    Returns:
        Tuple of (encoded_jwt, token_family)
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Generate unique JWT ID and token family
    jti = generate_jti()
    if not token_family:
        token_family = generate_token_family()

    # Ensure 'sub' is a string as required by JWT spec
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    # Add security claims
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": jti,
        "type": "refresh",
        "family": token_family,
    })

    # Store token metadata for tracking and revocation
    user_id = int(data.get("sub", 0))
    if user_id:
        metadata = TokenMetadata(
            jti=jti,
            user_id=user_id,
            token_family=token_family,
            issued_at=now,
            expires_at=expire,
            token_type="refresh",
            issued_from_ip=ip_address,
            user_agent=user_agent,
            status=TokenStatus.ACTIVE
        )
        blacklist = get_token_blacklist()
        blacklist.store_token_metadata(metadata)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, token_family

def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """
    Verify a JWT token and check if it has been revoked.

    Args:
        token: The JWT token to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: Optional[str] = payload.get("sub")
        email: Optional[str] = payload.get("email")
        token_type_payload: Optional[str] = payload.get("type")
        jti: Optional[str] = payload.get("jti")

        if user_id_str is None or token_type_payload != token_type:
            return None

        # Check if token has been revoked
        if jti and is_token_revoked(jti):
            return None

        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            return None

        # Return token data with jti and family for rotation support
        token_data = TokenData(user_id=user_id, email=email)
        token_data.jti = jti
        token_data.token_family = payload.get("family")
        return token_data
    except JWTError:
        return None

def generate_token() -> str:
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def is_user_locked(user) -> bool:
    if not user.locked_until:
        return False
    return user.locked_until > datetime.now(timezone.utc)

def increment_login_attempts(db: Session, user):
    user.login_attempts = (user.login_attempts or 0) + 1

    if user.login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)

    db.commit()

def reset_login_attempts(db: Session, user):
    user.login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    db.commit()

def create_user_with_type(db: Session, user_data: Dict[str, Any]):
    """Create a new user with specified user type."""
    from sqlmodel import select
    from app.models.user import User, UserType
    
    # Check if email already exists
    existing_user = db.exec(select(User).where(User.email == user_data["email"])).first()
    if existing_user:
        return None
    
    # Get user type
    user_type = db.exec(select(UserType).where(UserType.name == user_data.get("user_type", "volunteer"))).first()
    if not user_type:
        return None
    
    # Create user
    user = User(
        name=user_data["name"],
        email=user_data["email"],
        password_hash=user_data["password_hash"],
        phone=user_data.get("phone"),
        user_type_id=user_type.id,
        is_active=True,
        is_email_verified=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
