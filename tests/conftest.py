import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from datetime import datetime, timezone

from app.main import app
from app.database.engine import get_db
from app.models.user import User, UserType
from app.core.auth import get_password_hash

# Test database setup
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    
    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="user_types")
def user_types_fixture(session: Session):
    volunteer_type = UserType(name="volunteer", description="Volunteer user")
    org_type = UserType(name="organization", description="Organization user")  
    admin_type = UserType(name="admin", description="Administrator user")
    
    session.add(volunteer_type)
    session.add(org_type)
    session.add(admin_type)
    session.commit()
    session.refresh(volunteer_type)
    session.refresh(org_type)
    session.refresh(admin_type)
    
    return {
        "volunteer": volunteer_type,
        "organization": org_type,
        "admin": admin_type
    }

@pytest.fixture(name="test_user")
def test_user_fixture(session: Session, user_types):
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash=get_password_hash("TestPassword123"),
        user_type_id=user_types["volunteer"].id,
        is_active=True,
        is_email_verified=True,
        created_at=datetime.now(timezone.utc)
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture(name="unverified_user")
def unverified_user_fixture(session: Session, user_types):
    user = User(
        name="Unverified User",
        email="unverified@example.com",
        password_hash=get_password_hash("TestPassword123"),
        user_type_id=user_types["volunteer"].id,
        is_active=True,
        is_email_verified=False,
        email_verification_token="test_verification_token",
        created_at=datetime.now(timezone.utc)
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client: TestClient, user_types):
    # Register and login to get token
    register_data = {
        "name": "Auth Test User",
        "email": "authtest@example.com", 
        "password": "TestPassword123",
        "user_type": "volunteer"
    }
    client.post("/auth/register", json=register_data)
    
    login_data = {
        "email": "authtest@example.com",
        "password": "TestPassword123"
    }
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}