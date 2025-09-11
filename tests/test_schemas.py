import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.auth import (
    TokenData, Token, LoginRequest, RegisterRequest, 
    PasswordResetRequest, PasswordReset, ChangePassword,
    UserProfile, RefreshTokenRequest
)

class TestTokenData:
    def test_token_data_valid(self):
        data = TokenData(user_id=123, email="test@example.com")
        assert data.user_id == 123
        assert data.email == "test@example.com"
    
    def test_token_data_no_email(self):
        data = TokenData(user_id=123)
        assert data.user_id == 123
        assert data.email is None

class TestToken:
    def test_token_valid(self):
        token = Token(
            access_token="access_token_value",
            refresh_token="refresh_token_value",
            expires_in=3600
        )
        assert token.access_token == "access_token_value"
        assert token.refresh_token == "refresh_token_value"
        assert token.token_type == "bearer"  # default value
        assert token.expires_in == 3600

class TestLoginRequest:
    def test_login_request_valid(self):
        login = LoginRequest(
            email="test@example.com",
            password="password123"
        )
        assert login.email == "test@example.com"
        assert login.password == "password123"
    
    def test_login_request_invalid_email(self):
        with pytest.raises(ValidationError):
            LoginRequest(
                email="invalid_email",
                password="password123"
            )
    
    def test_login_request_empty_password(self):
        with pytest.raises(ValidationError):
            LoginRequest(
                email="test@example.com",
                password=""
            )

class TestRegisterRequest:
    def test_register_request_valid(self):
        register = RegisterRequest(
            name="John Doe",
            email="john@example.com",
            password="StrongPassword123",
            phone="+1234567890"
        )
        assert register.name == "John Doe"
        assert register.email == "john@example.com"
        assert register.password == "StrongPassword123"
        assert register.phone == "+1234567890"
        assert register.user_type == "volunteer"  # default value
    
    def test_register_request_name_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                name="J",  # Too short (min 2)
                email="john@example.com",
                password="StrongPassword123"
            )
    
    def test_register_request_name_too_long(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                name="J" * 101,  # Too long (max 100)
                email="john@example.com",
                password="StrongPassword123"
            )
    
    def test_register_request_password_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                name="John Doe",
                email="john@example.com",
                password="short"  # Too short (min 8)
            )
    
    def test_register_request_password_validation(self):
        # Test password without uppercase
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                name="John Doe",
                email="john@example.com",
                password="lowercase123"
            )
        assert "uppercase letter" in str(exc_info.value)
        
        # Test password without lowercase
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                name="John Doe",
                email="john@example.com",
                password="UPPERCASE123"
            )
        assert "lowercase letter" in str(exc_info.value)
        
        # Test password without digit
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                name="John Doe",
                email="john@example.com",
                password="NoDigitsHere"
            )
        assert "digit" in str(exc_info.value)

class TestPasswordResetRequest:
    def test_password_reset_request_valid(self):
        reset_req = PasswordResetRequest(email="test@example.com")
        assert reset_req.email == "test@example.com"
    
    def test_password_reset_request_invalid_email(self):
        with pytest.raises(ValidationError):
            PasswordResetRequest(email="invalid_email")

class TestPasswordReset:
    def test_password_reset_valid(self):
        reset = PasswordReset(
            token="reset_token_123",
            new_password="NewPassword123"
        )
        assert reset.token == "reset_token_123"
        assert reset.new_password == "NewPassword123"
    
    def test_password_reset_password_too_short(self):
        with pytest.raises(ValidationError):
            PasswordReset(
                token="reset_token_123",
                new_password="short"  # Too short (min 8)
            )

class TestChangePassword:
    def test_change_password_valid(self):
        change_pwd = ChangePassword(
            current_password="OldPassword123",
            new_password="NewPassword123"
        )
        assert change_pwd.current_password == "OldPassword123"
        assert change_pwd.new_password == "NewPassword123"
    
    def test_change_password_new_password_too_short(self):
        with pytest.raises(ValidationError):
            ChangePassword(
                current_password="OldPassword123",
                new_password="short"  # Too short (min 8)
            )

class TestUserProfile:
    def test_user_profile_valid(self):
        now = datetime.now()
        profile = UserProfile(
            id=1,
            name="John Doe",
            email="john@example.com",
            user_type="volunteer",
            is_active=True,
            is_email_verified=True,
            last_login=now,
            created_at=now
        )
        assert profile.id == 1
        assert profile.name == "John Doe"
        assert profile.email == "john@example.com"
        assert profile.user_type == "volunteer"
        assert profile.is_active is True
        assert profile.is_email_verified is True
        assert profile.last_login == now
        assert profile.created_at == now
    
    def test_user_profile_optional_fields(self):
        now = datetime.now()
        profile = UserProfile(
            id=1,
            name="John Doe",
            email="john@example.com",
            user_type="volunteer",
            is_active=True,
            is_email_verified=False,
            last_login=None,  # Optional
            created_at=now
        )
        assert profile.last_login is None

class TestRefreshTokenRequest:
    def test_refresh_token_request_valid(self):
        refresh_req = RefreshTokenRequest(refresh_token="refresh_token_123")
        assert refresh_req.refresh_token == "refresh_token_123"