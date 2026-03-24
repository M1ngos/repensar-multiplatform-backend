import os

# Disable rate limiting BEFORE importing app modules
# This must come first because settings are loaded at import time
os.environ["DISABLE_RATE_LIMITING"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from datetime import datetime, timezone
from typing import Dict

from app.main import app
from app.database.engine import get_db
from app.models.user import User, UserType
from app.core.auth import get_password_hash


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the in-memory rate limiter between tests to prevent state leakage."""
    from app.core.rate_limiter import get_rate_limiter, InMemoryRateLimiter
    from app.core import rate_limiter

    # Reset the global rate limiter instance
    rate_limiter._rate_limiter = InMemoryRateLimiter()
    yield
    # Reset again after test to clean up
    rate_limiter._rate_limiter = InMemoryRateLimiter()


# Test database setup - function-scoped for isolation
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
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
    """Create user types in the test database."""
    volunteer_type = UserType(name="volunteer", description="Volunteer user")
    org_type = UserType(name="organization", description="Organization user")
    admin_type = UserType(name="admin", description="Administrator user")
    pm_type = UserType(name="project_manager", description="Project Manager")
    staff_type = UserType(name="staff_member", description="Staff Member")

    session.add(volunteer_type)
    session.add(org_type)
    session.add(admin_type)
    session.add(pm_type)
    session.add(staff_type)
    session.commit()
    session.refresh(volunteer_type)
    session.refresh(org_type)
    session.refresh(admin_type)
    session.refresh(pm_type)
    session.refresh(staff_type)

    return {
        "volunteer": volunteer_type,
        "organization": org_type,
        "admin": admin_type,
        "project_manager": pm_type,
        "staff_member": staff_type,
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
        created_at=datetime.now(timezone.utc),
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
        created_at=datetime.now(timezone.utc),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client: TestClient, user_types):
    """Auth headers for a volunteer user with unique email per test."""
    import uuid

    unique_email = f"authtest-{uuid.uuid4().hex[:8]}@example.com"

    register_data = {
        "name": "Auth Test User",
        "email": unique_email,
        "password": "TestPassword123",
        "user_type": "volunteer",
    }
    client.post("/auth/register", json=register_data)

    login_data = {"email": unique_email, "password": "TestPassword123"}
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="admin_headers")
def admin_headers_fixture(client: TestClient, user_types):
    """Auth headers for an admin user with unique email per test."""
    import uuid

    unique_email = f"admin-{uuid.uuid4().hex[:8]}@testapp.com"

    register_resp = client.post(
        "/auth/register",
        json={
            "name": "Admin User",
            "email": unique_email,
            "password": "AdminPass123",
            "user_type": "admin",
        },
    )

    # If registration fails (e.g., duplicate), try to login anyway
    if register_resp.status_code == 400:
        # User might already exist, try login
        login_resp = client.post(
            "/auth/login", json={"email": unique_email, "password": "AdminPass123"}
        )
    else:
        login_resp = client.post(
            "/auth/login", json={"email": unique_email, "password": "AdminPass123"}
        )

    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="pm_headers")
def pm_headers_fixture(client: TestClient, user_types):
    """Auth headers for a project_manager user with unique email per test."""
    import uuid

    unique_email = f"pm-{uuid.uuid4().hex[:8]}@testapp.com"

    register_resp = client.post(
        "/auth/register",
        json={
            "name": "PM User",
            "email": unique_email,
            "password": "PmPass1234",
            "user_type": "project_manager",
        },
    )

    # If registration fails, try to login anyway
    if register_resp.status_code == 400:
        login_resp = client.post(
            "/auth/login", json={"email": unique_email, "password": "PmPass1234"}
        )
    else:
        login_resp = client.post(
            "/auth/login", json={"email": unique_email, "password": "PmPass1234"}
        )

    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
