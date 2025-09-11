import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from app.core.auth import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, verify_token, generate_token,
    is_user_locked, increment_login_attempts, reset_login_attempts
)

class TestPasswordUtils:
    def test_password_hashing(self):
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

class TestTokenUtils:
    def test_create_and_verify_access_token(self):
        data = {"sub": 123, "email": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        token_data = verify_token(token, "access")
        assert token_data is not None
        assert token_data.user_id == 123
        assert token_data.email == "test@example.com"
    
    def test_create_and_verify_refresh_token(self):
        data = {"sub": 456, "email": "refresh@example.com"}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        token_data = verify_token(token, "refresh")
        assert token_data is not None
        assert token_data.user_id == 456
        assert token_data.email == "refresh@example.com"
    
    def test_verify_token_wrong_type(self):
        data = {"sub": 123, "email": "test@example.com"}
        access_token = create_access_token(data)
        
        # Try to verify access token as refresh token
        token_data = verify_token(access_token, "refresh")
        assert token_data is None
    
    def test_verify_invalid_token(self):
        token_data = verify_token("invalid_token", "access")
        assert token_data is None
    
    def test_token_with_custom_expiry(self):
        data = {"sub": 123, "email": "test@example.com"}
        custom_expiry = timedelta(minutes=5)
        token = create_access_token(data, custom_expiry)
        
        token_data = verify_token(token, "access")
        assert token_data is not None

class TestTokenGeneration:
    def test_generate_token(self):
        token1 = generate_token()
        token2 = generate_token()
        
        assert isinstance(token1, str)
        assert isinstance(token2, str)
        assert len(token1) == 32
        assert len(token2) == 32
        assert token1 != token2

class TestUserSecurity:
    def test_is_user_locked_no_lockout(self):
        user = Mock()
        user.account_locked_until = None
        
        assert not is_user_locked(user)
    
    def test_is_user_locked_expired_lockout(self):
        user = Mock()
        user.account_locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
        
        assert not is_user_locked(user)
    
    def test_is_user_locked_active_lockout(self):
        user = Mock()
        user.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=1)
        
        assert is_user_locked(user)
    
    def test_increment_login_attempts(self):
        user = Mock()
        user.failed_login_attempts = 2
        user.account_locked_until = None
        
        db = Mock()
        
        increment_login_attempts(db, user)
        
        assert user.failed_login_attempts == 3
        assert user.account_locked_until is None
        db.commit.assert_called_once()
    
    def test_increment_login_attempts_triggers_lockout(self):
        user = Mock()
        user.failed_login_attempts = 4  # One less than MAX_LOGIN_ATTEMPTS (5)
        user.account_locked_until = None
        
        db = Mock()
        
        increment_login_attempts(db, user)
        
        assert user.failed_login_attempts == 5
        assert user.account_locked_until is not None
        assert user.account_locked_until > datetime.now(timezone.utc)
        db.commit.assert_called_once()
    
    def test_reset_login_attempts(self):
        user = Mock()
        user.failed_login_attempts = 3
        user.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        user.last_login = None
        
        db = Mock()
        
        reset_login_attempts(db, user)
        
        assert user.failed_login_attempts == 0
        assert user.account_locked_until is None
        assert user.last_login is not None
        db.commit.assert_called_once()
