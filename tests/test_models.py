import pytest
from datetime import datetime, timezone
from sqlmodel import Session

from app.models.user import User, UserType

class TestUserTypeModel:
    def test_create_user_type(self, session: Session):
        user_type = UserType(
            name="test_type",
            description="Test user type"
        )
        
        session.add(user_type)
        session.commit()
        session.refresh(user_type)
        
        assert user_type.id is not None
        assert user_type.name == "test_type"
        assert user_type.description == "Test user type"
        assert user_type.created_at is not None
    
    def test_user_type_name_unique(self, session: Session):
        # Create first user type
        user_type1 = UserType(name="unique_type", description="First type")
        session.add(user_type1)
        session.commit()
        
        # Try to create second user type with same name
        user_type2 = UserType(name="unique_type", description="Second type")
        session.add(user_type2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            session.commit()

class TestUserModel:
    def test_create_user(self, session: Session, user_types):
        user = User(
            name="Test User",
            email="test@example.com",
            password_hash="hashed_password",
            user_type_id=user_types["volunteer"].id,
            phone="1234567890"
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        assert user.id is not None
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.phone == "1234567890"
        assert user.user_type_id == user_types["volunteer"].id
        assert user.is_active is True
        assert user.is_email_verified is False
        assert user.failed_login_attempts == 0
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_email_unique(self, session: Session, user_types):
        # Create first user
        user1 = User(
            name="User One",
            email="unique@example.com",
            password_hash="hash1",
            user_type_id=user_types["volunteer"].id
        )
        session.add(user1)
        session.commit()
        
        # Try to create second user with same email
        user2 = User(
            name="User Two",
            email="unique@example.com",
            password_hash="hash2",
            user_type_id=user_types["volunteer"].id
        )
        session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            session.commit()
    
    def test_user_type_relationship(self, session: Session, user_types):
        user = User(
            name="Relationship Test User",
            email="relationship@example.com",
            password_hash="hashed_password",
            user_type_id=user_types["organization"].id
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Test relationship
        assert user.user_type.name == "organization"
        assert user.user_type.description == "Organization user"
        
        # Test reverse relationship
        org_type = user_types["organization"]
        session.refresh(org_type)
        assert user in org_type.users
    
    def test_user_optional_fields(self, session: Session, user_types):
        user = User(
            name="Minimal User",
            email="minimal@example.com",
            password_hash="hashed_password",
            user_type_id=user_types["volunteer"].id
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Check optional fields have default values
        assert user.phone is None
        assert user.email_verification_token is None
        assert user.email_verification_expires is None
        assert user.password_reset_token is None
        assert user.password_reset_expires is None
        assert user.account_locked_until is None
        assert user.refresh_token_hash is None
        assert user.refresh_token_expires is None
        assert user.last_login is None
    
    def test_user_security_fields(self, session: Session, user_types):
        now = datetime.now(timezone.utc)
        user = User(
            name="Security Test User",
            email="security@example.com",
            password_hash="hashed_password",
            user_type_id=user_types["volunteer"].id,
            failed_login_attempts=3,
            account_locked_until=now,
            email_verification_token="verify_token",
            password_reset_token="reset_token"
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        assert user.failed_login_attempts == 3
        assert user.account_locked_until == now
        assert user.email_verification_token == "verify_token"
        assert user.password_reset_token == "reset_token"
    
    def test_user_token_fields(self, session: Session, user_types):
        now = datetime.now(timezone.utc)
        user = User(
            name="Token Test User",
            email="token@example.com",
            password_hash="hashed_password",
            user_type_id=user_types["volunteer"].id,
            refresh_token_hash="refresh_hash",
            refresh_token_expires=now,
            last_login=now
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        assert user.refresh_token_hash == "refresh_hash"
        assert user.refresh_token_expires == now
        assert user.last_login == now