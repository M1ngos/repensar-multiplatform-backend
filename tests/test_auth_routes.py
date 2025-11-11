import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.models.user import User
from app.core.auth import generate_token

class TestAuthRegistration:
    def test_register_success(self, client: TestClient, user_types):
        register_data = {
            "name": "New User",
            "email": "newuser@example.com",
            "password": "TestPassword123",
            "user_type": "volunteer"
        }
        
        response = client.post("/auth/register", json=register_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "registered successfully" in data["message"]
    
    def test_register_duplicate_email(self, client: TestClient, test_user, user_types):
        register_data = {
            "name": "Duplicate User",
            "email": "test@example.com",  # Same as test_user
            "password": "TestPassword123", 
            "user_type": "volunteer"
        }
        
        response = client.post("/auth/register", json=register_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Email already registered" in data["detail"]
    
    def test_register_invalid_user_type(self, client: TestClient, user_types):
        register_data = {
            "name": "Invalid Type User",
            "email": "invalidtype@example.com",
            "password": "TestPassword123",
            "user_type": "invalid_type"
        }
        
        response = client.post("/auth/register", json=register_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid user type" in data["detail"]
    
    def test_register_weak_password(self, client: TestClient, user_types):
        register_data = {
            "name": "Weak Password User",
            "email": "weakpass@example.com",
            "password": "weak",
            "user_type": "volunteer"
        }
        
        response = client.post("/auth/register", json=register_data)
        
        assert response.status_code == 422

class TestAuthLogin:
    def test_login_success(self, client: TestClient, test_user):
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_wrong_password(self, client: TestClient, test_user):
        login_data = {
            "email": "test@example.com",
            "password": "WrongPassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Incorrect email or password" in data["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        login_data = {
            "email": "nonexistent@example.com",
            "password": "TestPassword123"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Incorrect email or password" in data["detail"]
    
    def test_login_inactive_user(self, client: TestClient, session, test_user):
        # Deactivate user
        test_user.is_active = False
        session.commit()
        
        login_data = {
            "email": "test@example.com", 
            "password": "TestPassword123"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Account is deactivated" in data["detail"]

class TestTokenRefresh:
    def test_refresh_token_success(self, client: TestClient, test_user):
        # First login to get tokens
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123"
        }
        login_response = client.post("/auth/login", json=login_data)
        login_data = login_response.json()
        
        # Use refresh token
        refresh_data = {
            "refresh_token": login_data["refresh_token"]
        }
        
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_invalid_token(self, client: TestClient):
        refresh_data = {
            "refresh_token": "invalid_token"
        }
        
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid refresh token" in data["detail"]

class TestUserProfile:
    def test_get_current_user_success(self, client: TestClient, test_user):
        login_data = {"email": test_user.email, "password": "TestPassword123"}
        response = client.post("/auth/login", json=login_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "email" in data
        assert "user_type" in data
        assert "is_active" in data
    
    def test_get_current_user_no_token(self, client: TestClient):
        response = client.get("/auth/me")
        
        assert response.status_code == 403

class TestLogout:
    def test_logout_success(self, client: TestClient, test_user):
        login_data = {"email": test_user.email, "password": "TestPassword123"}
        response = client.post("/auth/login", json=login_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post("/auth/logout", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully logged out" in data["message"]
    
    def test_logout_no_token(self, client: TestClient):
        response = client.post("/auth/logout")
        
        assert response.status_code == 403

class TestPasswordChange:
    def test_change_password_success(self, client: TestClient, test_user):
        login_data = {"email": test_user.email, "password": "TestPassword123"}
        response = client.post("/auth/login", json=login_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        password_data = {
            "current_password": "TestPassword123",
            "new_password": "NewPassword123"
        }
        
        response = client.post("/auth/change-password", json=password_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Password changed successfully" in data["message"]
    
    def test_change_password_wrong_current(self, client: TestClient, test_user):
        login_data = {"email": test_user.email, "password": "TestPassword123"}
        response = client.post("/auth/login", json=login_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        password_data = {
            "current_password": "WrongPassword",
            "new_password": "NewPassword123"
        }
        
        response = client.post("/auth/change-password", json=password_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "Incorrect current password" in data["detail"]

class TestPasswordReset:
    def test_forgot_password_success(self, client: TestClient, test_user):
        reset_data = {
            "email": "test@example.com"
        }
        
        response = client.post("/auth/forgot-password", json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "password reset link" in data["message"]
    
    def test_forgot_password_nonexistent_email(self, client: TestClient):
        reset_data = {
            "email": "nonexistent@example.com"
        }
        
        response = client.post("/auth/forgot-password", json=reset_data)
        
        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        data = response.json()
        assert "password reset link" in data["message"]
    
    def test_reset_password_success(self, client: TestClient, session, test_user):
        # Set reset token for user
        test_user.password_reset_token = "valid_reset_token"
        test_user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        session.commit()

        reset_data = {
            "token": "valid_reset_token",
            "new_password": "NewResetPassword123"
        }

        response = client.post("/auth/reset-password", json=reset_data)

        assert response.status_code == 200
        data = response.json()
        assert "Password reset successfully" in data["message"]
    
    def test_reset_password_invalid_token(self, client: TestClient):
        reset_data = {
            "token": "invalid_token",
            "new_password": "NewResetPassword123"
        }
        
        response = client.post("/auth/reset-password", json=reset_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid or expired reset token" in data["detail"]

class TestEmailVerification:
    def test_verify_email_success(self, client: TestClient, session, unverified_user):
        unverified_user.email_verification_token = generate_token()
        unverified_user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        session.add(unverified_user)
        session.commit()
        session.refresh(unverified_user)

        response = client.post(f"/auth/verify-email?token={unverified_user.email_verification_token}")

        assert response.status_code == 200
        data = response.json()
        assert "Email verified successfully" in data["message"]

        # Refresh user and check verification status
        session.refresh(unverified_user)
        assert unverified_user.is_email_verified
    
    def test_verify_email_invalid_token(self, client: TestClient):
        response = client.post("/auth/verify-email?token=invalid_token")
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid or expired verification token" in data["detail"]
    
    def test_resend_verification_success(self, client: TestClient, unverified_user):
        response = client.post("/auth/resend-verification", json={"email": unverified_user.email})
        
        assert response.status_code == 200
        data = response.json()
        assert "Verification email sent successfully" in data["message"]
    
    def test_resend_verification_already_verified(self, client: TestClient, test_user):
        response = client.post("/auth/resend-verification", json={"email": test_user.email})
        
        assert response.status_code == 400
        data = response.json()
        assert "Email is already verified" in data["detail"]

class TestAuthValidateToken:
    def test_validate_token_success(self, client: TestClient, test_user):
        # Login to get token
        login_data = {"email": test_user.email, "password": "TestPassword123"}
        response = client.post("/auth/login", json=login_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/auth/validate-token", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "user" in data
        assert data["user"]["email"] == test_user.email

    def test_validate_token_invalid(self, client: TestClient):
        response = client.get("/auth/validate-token", headers={"Authorization": "Bearer invalidtoken"})
        assert response.status_code == 401

    def test_validate_token_no_token(self, client: TestClient):
        response = client.get("/auth/validate-token")
        assert response.status_code == 403

class TestAuthStatus:
    def test_auth_status_authenticated(self, client: TestClient, test_user):
        # Login to get token
        login_data = {"email": test_user.email, "password": "TestPassword123"}
        response = client.post("/auth/login", json=login_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/auth/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user"]["email"] == test_user.email
        assert "permissions" in data["user"]
        assert "dashboard_config" in data["user"]

    def test_auth_status_no_token(self, client: TestClient):
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert data["user"] is None
        assert data["message"] == "No token provided"

    def test_auth_status_invalid_token(self, client: TestClient):
        response = client.get("/auth/status", headers={"Authorization": "Bearer invalidtoken"})
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert data["user"] is None
        assert data["message"] == "Invalid token"

class TestAuthPermissions:
    def test_get_user_permissions_success(self, client: TestClient, test_user):
        login_data = {"email": test_user.email, "password": "TestPassword123"}
        response = client.post("/auth/login", json=login_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/auth/permissions", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_type" in data
        assert "permissions" in data
        assert "dashboard_config" in data
        assert "description" in data

    def test_get_user_permissions_no_token(self, client: TestClient):
        response = client.get("/auth/permissions")
        
        assert response.status_code == 403