"""
Comprehensive integration tests for /volunteers endpoints.

Known bugs documented by tests:
- POST /volunteers/hours/{id}/approve → always 500 due to `approval_data.is_approved`
  (schema field is `approved`, not `is_approved`) + `approved_log.hours_worked`
  (model field is `hours`).
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.volunteer import VolunteerSkill


# ─────────────────────────────────────────────────────────────
# LOCAL FIXTURES
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def registered_volunteer(client: TestClient, user_types):
    """Register a volunteer via the public endpoint and return auth details."""
    reg_resp = client.post(
        "/volunteers/register",
        json={
            "name": "Jane Volunteer",
            "email": "jane.vol@example.com",
            "password": "SecurePass1",
            "skill_ids": [],
        },
    )
    assert reg_resp.status_code == 200, reg_resp.text
    data = reg_resp.json()

    login_resp = client.post(
        "/auth/login",
        json={
            "email": "jane.vol@example.com",
            "password": "SecurePass1",
        },
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]

    return {
        "id": data["id"],
        "volunteer_id": data["volunteer_id"],
        "user_id": data["user_id"],
        "auth_headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def second_volunteer(client: TestClient, user_types):
    """A second registered volunteer (different user)."""
    client.post(
        "/volunteers/register",
        json={
            "name": "Bob Vol",
            "email": "bob.vol@example.com",
            "password": "SecurePass1",
            "skill_ids": [],
        },
    )
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "bob.vol@example.com",
            "password": "SecurePass1",
        },
    )
    token = login_resp.json()["access_token"]
    return {"auth_headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def skill(session: Session):
    """Seed a VolunteerSkill directly in the test DB."""
    s = VolunteerSkill(name="Python Programming", category="technical")
    session.add(s)
    session.commit()
    session.refresh(s)
    return s


# ─────────────────────────────────────────────────────────────
# REGISTRATION
# ─────────────────────────────────────────────────────────────


class TestVolunteerRegistration:
    def test_register_success(self, client: TestClient, user_types):
        response = client.post(
            "/volunteers/register",
            json={
                "name": "New Volunteer",
                "email": "newvol@example.com",
                "password": "Password1",
                "skill_ids": [],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "volunteer_id" in data
        assert data["volunteer_id"].startswith("VLT")
        assert "user_id" in data
        assert "registered successfully" in data["message"].lower()

    def test_register_duplicate_email(self, client: TestClient, user_types):
        payload = {
            "name": "Dup User",
            "email": "dupvol@example.com",
            "password": "Password1",
            "skill_ids": [],
        }
        client.post("/volunteers/register", json=payload)
        response = client.post("/volunteers/register", json=payload)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_with_skills(self, client: TestClient, user_types, skill):
        response = client.post(
            "/volunteers/register",
            json={
                "name": "Skilled Vol",
                "email": "skilled@example.com",
                "password": "Password1",
                "skill_ids": [skill.id],
            },
        )
        assert response.status_code == 200

    def test_register_missing_name_fails(self, client: TestClient, user_types):
        response = client.post(
            "/volunteers/register",
            json={
                "email": "noname@example.com",
                "password": "Password1",
                "skill_ids": [],
            },
        )
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────
# MY PROFILE  (GET /volunteers/me)
# ─────────────────────────────────────────────────────────────


class TestVolunteerMe:
    def test_get_my_profile_success(self, client, registered_volunteer):
        response = client.get(
            "/volunteers/me",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == registered_volunteer["id"]
        assert "name" in data
        assert "email" in data
        assert "skills" in data

    def test_get_my_profile_no_auth(self, client):
        response = client.get("/volunteers/me")
        assert response.status_code == 403

    def test_get_my_profile_not_volunteer_user(self, client, admin_headers):
        """A user without a Volunteer DB row gets 404."""
        response = client.get("/volunteers/me", headers=admin_headers)
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────
# VOLUNTEER LIST  (GET /volunteers/)
# ─────────────────────────────────────────────────────────────


class TestVolunteerList:
    def test_list_volunteers_success(self, client, registered_volunteer):
        response = client.get(
            "/volunteers/",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_requires_auth(self, client, user_types):
        response = client.get("/volunteers/")
        assert response.status_code == 403

    def test_list_with_status_filter(self, client, registered_volunteer):
        response = client.get(
            "/volunteers/?status=active",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_with_invalid_status_filter(self, client, registered_volunteer):
        """Invalid status regex value should fail validation."""
        response = client.get(
            "/volunteers/?status=unknown_status",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 422

    def test_list_pagination(self, client, registered_volunteer):
        response = client.get(
            "/volunteers/?skip=0&limit=5",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────
# VOLUNTEER STATS  (GET /volunteers/stats)
# ─────────────────────────────────────────────────────────────


class TestVolunteerStats:
    def test_get_stats_public(self, client, user_types):
        response = client.get("/volunteers/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_volunteers" in data
        assert "active_volunteers" in data
        assert "total_hours" in data
        assert "volunteers_by_status" in data
        assert "volunteers_by_skill" in data
        assert "recent_registrations" in data

    def test_stats_reflect_registered_volunteer(self, client, registered_volunteer):
        response = client.get("/volunteers/stats")
        data = response.json()
        assert data["total_volunteers"] >= 1
        assert data["active_volunteers"] >= 1


# ─────────────────────────────────────────────────────────────
# VOLUNTEER PROFILE BY ID  (GET /volunteers/{id})
# ─────────────────────────────────────────────────────────────


class TestVolunteerProfileById:
    def test_get_profile_success(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.get(
            f"/volunteers/{vid}",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == vid

    def test_get_profile_not_found(self, client, registered_volunteer):
        response = client.get(
            "/volunteers/9999",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 404

    def test_get_profile_requires_auth(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.get(f"/volunteers/{vid}")
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────
# UPDATE PROFILE  (PUT /volunteers/{id})
# ─────────────────────────────────────────────────────────────


class TestVolunteerUpdate:
    def test_update_own_profile_success(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.put(
            f"/volunteers/{vid}",
            json={"city": "Madrid", "motivation": "I love volunteering!"},
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Madrid"

    def test_update_other_volunteer_forbidden(
        self, client, registered_volunteer, second_volunteer
    ):
        vid = registered_volunteer["id"]
        response = client.put(
            f"/volunteers/{vid}",
            json={"city": "Barcelona"},
            headers=second_volunteer["auth_headers"],
        )
        assert response.status_code == 403

    def test_update_nonexistent_volunteer(self, client, registered_volunteer):
        response = client.put(
            "/volunteers/9999",
            json={"city": "Madrid"},
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 404

    def test_admin_can_update_any_volunteer(
        self, client, registered_volunteer, admin_headers
    ):
        vid = registered_volunteer["id"]
        response = client.put(
            f"/volunteers/{vid}",
            json={"notes": "Updated by admin"},
            headers=admin_headers,
        )
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────
# DEACTIVATE  (DELETE /volunteers/{id})
# ─────────────────────────────────────────────────────────────


class TestVolunteerDeactivate:
    def test_deactivate_by_admin(self, client, registered_volunteer, admin_headers):
        vid = registered_volunteer["id"]
        response = client.delete(
            f"/volunteers/{vid}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert "deactivated" in response.json()["message"].lower()

    def test_deactivate_forbidden_for_volunteer(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.delete(
            f"/volunteers/{vid}",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 403

    def test_deactivate_not_found(self, client, admin_headers, user_types):
        response = client.delete("/volunteers/9999", headers=admin_headers)
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────
# SKILLS  (GET /volunteers/skills/available, etc.)
# ─────────────────────────────────────────────────────────────


class TestVolunteerSkills:
    def test_get_available_skills(self, client, skill, user_types):
        response = client.get("/volunteers/skills/available")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(s["id"] == skill.id for s in data)

    def test_get_volunteer_skills_requires_auth(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.get(f"/volunteers/{vid}/skills")
        assert response.status_code == 403

    def test_get_volunteer_skills_success(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.get(
            f"/volunteers/{vid}/skills",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_assign_skill_success(self, client, registered_volunteer, skill):
        vid = registered_volunteer["id"]
        response = client.post(
            f"/volunteers/{vid}/skills",
            json={
                "skill_id": skill.id,
                "proficiency_level": "beginner",
                "years_experience": 1,
            },
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["skill_id"] == skill.id

    def test_assign_nonexistent_skill(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.post(
            f"/volunteers/{vid}/skills",
            json={
                "skill_id": 9999,
                "proficiency_level": "beginner",
                "years_experience": 0,
            },
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 404

    def test_assign_duplicate_skill_returns_400(
        self, client, registered_volunteer, skill
    ):
        vid = registered_volunteer["id"]
        payload = {
            "skill_id": skill.id,
            "proficiency_level": "beginner",
            "years_experience": 0,
        }
        client.post(
            f"/volunteers/{vid}/skills",
            json=payload,
            headers=registered_volunteer["auth_headers"],
        )
        response = client.post(
            f"/volunteers/{vid}/skills",
            json=payload,
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 400

    def test_remove_skill_success(self, client, registered_volunteer, skill):
        vid = registered_volunteer["id"]
        # Assign first
        client.post(
            f"/volunteers/{vid}/skills",
            json={
                "skill_id": skill.id,
                "proficiency_level": "beginner",
                "years_experience": 0,
            },
            headers=registered_volunteer["auth_headers"],
        )
        # Remove
        response = client.delete(
            f"/volunteers/{vid}/skills/{skill.id}",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        assert "removed" in response.json()["message"].lower()

    def test_remove_nonexistent_skill_assignment(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.delete(
            f"/volunteers/{vid}/skills/9999",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 404

    def test_other_volunteer_cannot_assign_skill(
        self, client, registered_volunteer, second_volunteer, skill
    ):
        vid = registered_volunteer["id"]
        response = client.post(
            f"/volunteers/{vid}/skills",
            json={
                "skill_id": skill.id,
                "proficiency_level": "beginner",
                "years_experience": 0,
            },
            headers=second_volunteer["auth_headers"],
        )
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────
# TIME LOGS  (hours endpoints)
# ─────────────────────────────────────────────────────────────


class TestVolunteerHours:
    def test_get_own_hours(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.get(
            f"/volunteers/{vid}/hours",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_other_volunteer_hours_forbidden(
        self, client, registered_volunteer, second_volunteer
    ):
        vid = registered_volunteer["id"]
        response = client.get(
            f"/volunteers/{vid}/hours",
            headers=second_volunteer["auth_headers"],
        )
        assert response.status_code == 403

    def test_log_hours_success(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.post(
            f"/volunteers/{vid}/hours",
            json={
                "volunteer_id": vid,
                "date": str(date.today()),
                "hours": 3.5,
                "activity_description": "Community cleanup",
            },
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert float(data["hours"]) == 3.5

    def test_log_hours_zero_fails_validation(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.post(
            f"/volunteers/{vid}/hours",
            json={
                "volunteer_id": vid,
                "date": str(date.today()),
                "hours": 0,
            },
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 422

    def test_log_hours_for_nonexistent_volunteer(self, client, registered_volunteer):
        response = client.post(
            "/volunteers/9999/hours",
            json={
                "volunteer_id": 9999,
                "date": str(date.today()),
                "hours": 2.0,
            },
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code in (403, 404)

    def test_update_pending_hours(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        # Create a time log
        create_resp = client.post(
            f"/volunteers/{vid}/hours",
            json={
                "volunteer_id": vid,
                "date": str(date.today()),
                "hours": 2.0,
            },
            headers=registered_volunteer["auth_headers"],
        )
        log_id = create_resp.json()["id"]

        update_resp = client.put(
            f"/volunteers/hours/{log_id}",
            json={"hours": 4.0, "activity_description": "Extended work"},
            headers=registered_volunteer["auth_headers"],
        )
        assert update_resp.status_code == 200
        assert float(update_resp.json()["hours"]) == 4.0

    def test_update_nonexistent_time_log(self, client, registered_volunteer):
        response = client.put(
            "/volunteers/hours/9999",
            json={"hours": 1.0},
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 404

    def test_delete_pending_time_log(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        create_resp = client.post(
            f"/volunteers/{vid}/hours",
            json={
                "volunteer_id": vid,
                "date": str(date.today()),
                "hours": 1.0,
            },
            headers=registered_volunteer["auth_headers"],
        )
        log_id = create_resp.json()["id"]
        del_resp = client.delete(
            f"/volunteers/hours/{log_id}",
            headers=registered_volunteer["auth_headers"],
        )
        assert del_resp.status_code == 200
        assert "deleted" in del_resp.json()["message"].lower()

    def test_delete_nonexistent_time_log(self, client, registered_volunteer):
        response = client.delete(
            "/volunteers/hours/9999",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 404

    # BUG DOCUMENTATION TEST
    def test_approve_hours_bug_returns_500(
        self, client, registered_volunteer, pm_headers
    ):
        """
        BUG #1: POST /volunteers/hours/{id}/approve always returns 500.
        Root cause: router accesses `approval_data.is_approved` but the
        VolunteerTimeLogApproval schema field is named `approved`.
        Also: `approved_log.hours_worked` — the model field is `hours`.
        The CRUD correctly approves the record, but the notification
        code raises AttributeError, which is caught and returned as 500.
        """
        vid = registered_volunteer["id"]
        create_resp = client.post(
            f"/volunteers/{vid}/hours",
            json={
                "volunteer_id": vid,
                "date": str(date.today()),
                "hours": 2.0,
            },
            headers=registered_volunteer["auth_headers"],
        )
        assert create_resp.status_code == 200
        log_id = create_resp.json()["id"]

        approve_resp = client.post(
            f"/volunteers/hours/{log_id}/approve",
            json={"approved": True},
            headers=pm_headers,
        )
        # BUG: Should be 200, but is 500 due to schema attribute mismatch
        assert approve_resp.status_code == 500, (
            "If this assertion now fails (i.e., status != 500), "
            "the is_approved / hours_worked bug has been fixed."
        )

    def test_approve_hours_forbidden_for_volunteer(self, client, registered_volunteer):
        """Volunteer should get 403 when trying to approve time logs."""
        vid = registered_volunteer["id"]
        create_resp = client.post(
            f"/volunteers/{vid}/hours",
            json={
                "volunteer_id": vid,
                "date": str(date.today()),
                "hours": 1.0,
            },
            headers=registered_volunteer["auth_headers"],
        )
        log_id = create_resp.json()["id"]
        response = client.post(
            f"/volunteers/hours/{log_id}/approve",
            json={"approved": True},
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 403

    def test_get_hours_summary(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.get(
            f"/volunteers/{vid}/hours/summary",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_hours" in data
        assert "total_entries" in data

    def test_get_other_volunteer_hours_summary_forbidden(
        self, client, registered_volunteer, second_volunteer
    ):
        vid = registered_volunteer["id"]
        response = client.get(
            f"/volunteers/{vid}/hours/summary",
            headers=second_volunteer["auth_headers"],
        )
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────
# TASKS, PROJECTS, ACTIVITY (relation endpoints)
# ─────────────────────────────────────────────────────────────


class TestVolunteerRelations:
    def test_get_volunteer_tasks_empty(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.get(
            f"/volunteers/{vid}/tasks",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_volunteer_tasks_forbidden(
        self, client, registered_volunteer, second_volunteer
    ):
        vid = registered_volunteer["id"]
        response = client.get(
            f"/volunteers/{vid}/tasks",
            headers=second_volunteer["auth_headers"],
        )
        assert response.status_code == 403

    def test_get_volunteer_tasks_not_found(self, client, registered_volunteer):
        response = client.get(
            "/volunteers/9999/tasks",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 404

    def test_get_volunteer_projects_empty(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.get(
            f"/volunteers/{vid}/projects",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_volunteer_activity_empty(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.get(
            f"/volunteers/{vid}/activity",
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_activity_forbidden(
        self, client, registered_volunteer, second_volunteer
    ):
        vid = registered_volunteer["id"]
        response = client.get(
            f"/volunteers/{vid}/activity",
            headers=second_volunteer["auth_headers"],
        )
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────
# ONBOARDING  (PATCH /volunteers/{id}/onboarding)
# ─────────────────────────────────────────────────────────────


class TestVolunteerOnboarding:
    def test_update_own_onboarding(self, client, registered_volunteer):
        vid = registered_volunteer["id"]
        response = client.patch(
            f"/volunteers/{vid}/onboarding",
            json={"city": "Berlin", "onboarding_completed": True},
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_completed"] is True

    def test_update_other_volunteer_onboarding_forbidden(
        self, client, registered_volunteer, second_volunteer
    ):
        vid = registered_volunteer["id"]
        response = client.patch(
            f"/volunteers/{vid}/onboarding",
            json={"city": "London"},
            headers=second_volunteer["auth_headers"],
        )
        assert response.status_code == 403

    def test_update_onboarding_not_found(self, client, registered_volunteer):
        response = client.patch(
            "/volunteers/9999/onboarding",
            json={"city": "Paris"},
            headers=registered_volunteer["auth_headers"],
        )
        assert response.status_code == 404
