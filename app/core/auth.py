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


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Ensure 'sub' is a string as required by JWT spec
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Ensure 'sub' is a string as required by JWT spec
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: Optional[str] = payload.get("sub")
        email: Optional[str] = payload.get("email")
        token_type_payload: Optional[str] = payload.get("type")
        
        if user_id_str is None or token_type_payload != token_type:
            return None
        
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            return None
            
        return TokenData(user_id=user_id, email=email)
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
