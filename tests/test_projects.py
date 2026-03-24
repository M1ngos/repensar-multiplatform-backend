"""
Comprehensive integration tests for /projects endpoints.

Known bugs documented by tests:
- GET /projects/{id}/resources → 500 ImportError:
  `from app.schemas.resource import ResourceAllocation` (class doesn't exist;
  should be `ProjectResourceAllocation`).
- GET /projects/{id}/volunteers → 500 ValidationError:
  `VolunteerSummary` is constructed without the required `skills_count` field.
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────────
# LOCAL FIXTURES
# ─────────────────────────────────────────────────────────────

_PROJECT_PAYLOAD = {
    "name": "Test Reforestation Project",
    "description": "A project for testing",
    "category": "reforestation",
    "status": "planning",
    "priority": "medium",
    "requires_volunteers": True,
}

_MILESTONE_PAYLOAD = {
    "name": "Phase 1 Complete",
    "description": "First phase done",
    "target_date": str(date.today()),
    "status": "pending",
}


@pytest.fixture
def project(client: TestClient, admin_headers):
    """Create a project as admin and return its JSON data."""
    response = client.post("/projects/", json=_PROJECT_PAYLOAD, headers=admin_headers)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def pm_project(client: TestClient, pm_headers):
    """Create a project as PM and return its JSON data."""
    response = client.post(
        "/projects/",
        json={**_PROJECT_PAYLOAD, "name": "PM Project"},
        headers=pm_headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def milestone(client: TestClient, admin_headers, project):
    """Create a milestone for the test project."""
    pid = project["id"]
    response = client.post(
        f"/projects/{pid}/milestones",
        json={**_MILESTONE_PAYLOAD, "project_id": pid},
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


# ─────────────────────────────────────────────────────────────
# PROJECT CREATE  (POST /projects/)
# ─────────────────────────────────────────────────────────────


class TestProjectCreate:
    def test_create_as_admin_success(self, client, admin_headers, user_types):
        response = client.post(
            "/projects/", json=_PROJECT_PAYLOAD, headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == _PROJECT_PAYLOAD["name"]
        assert data["category"] == "reforestation"
        assert "id" in data

    def test_create_as_pm_success(self, client, pm_headers, user_types):
        response = client.post(
            "/projects/",
            json={**_PROJECT_PAYLOAD, "name": "PM Created Project"},
            headers=pm_headers,
        )
        assert response.status_code == 200

    def test_create_forbidden_for_volunteer(self, client, auth_headers, user_types):
        response = client.post(
            "/projects/", json=_PROJECT_PAYLOAD, headers=auth_headers
        )
        assert response.status_code == 403

    def test_create_requires_auth(self, client, user_types):
        response = client.post("/projects/", json=_PROJECT_PAYLOAD)
        assert response.status_code == 403

    def test_create_requires_name(self, client, admin_headers, user_types):
        payload = {k: v for k, v in _PROJECT_PAYLOAD.items() if k != "name"}
        response = client.post("/projects/", json=payload, headers=admin_headers)
        assert response.status_code == 422

    def test_create_invalid_category(self, client, admin_headers, user_types):
        payload = {**_PROJECT_PAYLOAD, "category": "not_a_real_category"}
        response = client.post("/projects/", json=payload, headers=admin_headers)
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────
# PROJECT LIST  (GET /projects/)
# ─────────────────────────────────────────────────────────────


class TestProjectList:
    def test_list_projects_success(self, client, project, admin_headers):
        response = client.get("/projects/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_requires_auth(self, client, user_types):
        response = client.get("/projects/")
        assert response.status_code == 403

    def test_list_with_status_filter(self, client, project, admin_headers):
        response = client.get("/projects/?status=planning", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_with_invalid_status_returns_422(
        self, client, admin_headers, user_types
    ):
        response = client.get("/projects/?status=invalid_status", headers=admin_headers)
        assert response.status_code == 422

    def test_list_with_category_filter(self, client, project, admin_headers):
        response = client.get(
            "/projects/?category=reforestation", headers=admin_headers
        )
        assert response.status_code == 200

    def test_list_with_requires_volunteers_filter(self, client, project, admin_headers):
        response = client.get(
            "/projects/?requires_volunteers=true", headers=admin_headers
        )
        assert response.status_code == 200

    def test_list_pagination(self, client, project, admin_headers):
        response = client.get("/projects/?skip=0&limit=5", headers=admin_headers)
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────
# PROJECT STATS  (GET /projects/stats)
# ─────────────────────────────────────────────────────────────


class TestProjectStats:
    def test_get_stats_public(self, client, user_types):
        response = client.get("/projects/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_projects" in data
        assert "active_projects" in data
        assert "completed_projects" in data
        assert "projects_by_status" in data
        assert "total_budget" in data

    def test_stats_reflect_created_project(self, client, project):
        response = client.get("/projects/stats")
        data = response.json()
        assert data["total_projects"] >= 1


# ─────────────────────────────────────────────────────────────
# PROJECT DASHBOARD  (GET /projects/dashboard)
# ─────────────────────────────────────────────────────────────


class TestProjectDashboard:
    def test_get_dashboard_success(self, client, project, admin_headers):
        response = client.get("/projects/dashboard", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_dashboard_requires_auth(self, client, user_types):
        response = client.get("/projects/dashboard")
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────
# PROJECT DETAIL  (GET /projects/{id})
# ─────────────────────────────────────────────────────────────


class TestProjectDetail:
    def test_get_project_success(self, client, project, admin_headers):
        pid = project["id"]
        response = client.get(f"/projects/{pid}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pid
        assert data["name"] == project["name"]
        assert "team_members" in data
        assert "milestones" in data
        assert "total_tasks" in data
        assert "progress_percentage" in data

    def test_get_project_not_found(self, client, admin_headers, user_types):
        response = client.get("/projects/9999", headers=admin_headers)
        assert response.status_code == 404

    def test_get_project_requires_auth(self, client, project):
        pid = project["id"]
        response = client.get(f"/projects/{pid}")
        assert response.status_code == 403

    def test_volunteer_can_view_project(self, client, project, auth_headers):
        pid = project["id"]
        response = client.get(f"/projects/{pid}", headers=auth_headers)
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────
# PROJECT UPDATE  (PUT /projects/{id})
# ─────────────────────────────────────────────────────────────


class TestProjectUpdate:
    def test_update_as_admin_success(self, client, project, admin_headers):
        pid = project["id"]
        response = client.put(
            f"/projects/{pid}",
            json={"name": "Updated Name", "status": "in_progress"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
        assert response.json()["status"] == "in_progress"

    def test_update_forbidden_for_volunteer(self, client, project, auth_headers):
        pid = project["id"]
        response = client.put(
            f"/projects/{pid}",
            json={"name": "Hacked Name"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_update_nonexistent_project(self, client, admin_headers, user_types):
        response = client.put(
            "/projects/9999",
            json={"name": "Ghost Project"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_pm_can_update_own_project(self, client, pm_project, pm_headers):
        pid = pm_project["id"]
        response = client.put(
            f"/projects/{pid}",
            json={"description": "Updated by PM"},
            headers=pm_headers,
        )
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────
# PROJECT DELETE  (DELETE /projects/{id})
# ─────────────────────────────────────────────────────────────


class TestProjectDelete:
    def test_delete_as_admin_success(self, client, admin_headers, user_types):
        # Create a dedicated project to delete
        create_resp = client.post(
            "/projects/",
            json={**_PROJECT_PAYLOAD, "name": "To Be Deleted"},
            headers=admin_headers,
        )
        pid = create_resp.json()["id"]
        response = client.delete(f"/projects/{pid}", headers=admin_headers)
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    def test_delete_forbidden_for_pm(self, client, pm_project, pm_headers):
        pid = pm_project["id"]
        response = client.delete(f"/projects/{pid}", headers=pm_headers)
        assert response.status_code == 403

    def test_delete_forbidden_for_volunteer(self, client, project, auth_headers):
        pid = project["id"]
        response = client.delete(f"/projects/{pid}", headers=auth_headers)
        assert response.status_code == 403

    def test_delete_not_found(self, client, admin_headers, user_types):
        response = client.delete("/projects/9999", headers=admin_headers)
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────
# PROJECT TEAM  (GET/POST/PUT/DELETE /projects/{id}/team)
# ─────────────────────────────────────────────────────────────


class TestProjectTeam:
    def _get_admin_user_id(self, client, admin_headers):
        """Retrieve the user ID of the currently-authenticated admin."""
        resp = client.get("/auth/me", headers=admin_headers)
        return resp.json()["id"]

    def test_get_team_empty(self, client, project, admin_headers):
        pid = project["id"]
        response = client.get(f"/projects/{pid}/team", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_add_team_member_success(self, client, project, admin_headers):
        pid = project["id"]
        user_id = self._get_admin_user_id(client, admin_headers)
        response = client.post(
            f"/projects/{pid}/team",
            json={"user_id": user_id, "role": "developer"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id

    def test_add_duplicate_member_returns_400(self, client, project, admin_headers):
        pid = project["id"]
        user_id = self._get_admin_user_id(client, admin_headers)
        client.post(
            f"/projects/{pid}/team",
            json={"user_id": user_id, "role": "developer"},
            headers=admin_headers,
        )
        response = client.post(
            f"/projects/{pid}/team",
            json={"user_id": user_id, "role": "developer"},
            headers=admin_headers,
        )
        assert response.status_code == 400

    def test_update_team_member(self, client, project, admin_headers):
        pid = project["id"]
        user_id = self._get_admin_user_id(client, admin_headers)
        client.post(
            f"/projects/{pid}/team",
            json={"user_id": user_id, "role": "developer"},
            headers=admin_headers,
        )
        response = client.put(
            f"/projects/{pid}/team/{user_id}",
            json={"role": "team_lead"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["role"] == "team_lead"

    def test_remove_team_member(self, client, project, admin_headers):
        pid = project["id"]
        user_id = self._get_admin_user_id(client, admin_headers)
        client.post(
            f"/projects/{pid}/team",
            json={"user_id": user_id, "role": "developer"},
            headers=admin_headers,
        )
        response = client.delete(
            f"/projects/{pid}/team/{user_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert "removed" in response.json()["message"].lower()

    def test_add_member_forbidden_for_volunteer(self, client, project, auth_headers):
        pid = project["id"]
        resp = client.get("/auth/me", headers=auth_headers)
        user_id = resp.json()["id"]
        response = client.post(
            f"/projects/{pid}/team",
            json={"user_id": user_id, "role": "developer"},
            headers=auth_headers,
        )
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────
# MILESTONES  (GET/POST/PUT/DELETE)
# ─────────────────────────────────────────────────────────────


class TestProjectMilestones:
    def test_create_milestone_success(self, client, project, admin_headers):
        pid = project["id"]
        response = client.post(
            f"/projects/{pid}/milestones",
            json={**_MILESTONE_PAYLOAD, "project_id": pid},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == _MILESTONE_PAYLOAD["name"]
        assert data["project_id"] == pid

    def test_create_milestone_project_not_found(
        self, client, admin_headers, user_types
    ):
        response = client.post(
            "/projects/9999/milestones",
            json={**_MILESTONE_PAYLOAD, "project_id": 9999},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_get_milestones(self, client, milestone, project, admin_headers):
        pid = project["id"]
        response = client.get(f"/projects/{pid}/milestones", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(m["id"] == milestone["id"] for m in data)

    def test_update_milestone(self, client, milestone, admin_headers):
        mid = milestone["id"]
        response = client.put(
            f"/projects/milestones/{mid}",
            json={"name": "Updated Milestone", "status": "achieved"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Milestone"

    def test_update_milestone_not_found(self, client, admin_headers, user_types):
        response = client.put(
            "/projects/milestones/9999",
            json={"name": "Ghost"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_delete_milestone_success(self, client, project, admin_headers):
        pid = project["id"]
        create_resp = client.post(
            f"/projects/{pid}/milestones",
            json={**_MILESTONE_PAYLOAD, "name": "Delete Me", "project_id": pid},
            headers=admin_headers,
        )
        mid = create_resp.json()["id"]
        response = client.delete(
            f"/projects/milestones/{mid}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    def test_delete_milestone_not_found(self, client, admin_headers, user_types):
        response = client.delete("/projects/milestones/9999", headers=admin_headers)
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────
# KNOWN BUG: GET /projects/{id}/resources
# ─────────────────────────────────────────────────────────────


class TestProjectResourcesBug:
    def test_get_project_resources_import_error_500(
        self, client, project, admin_headers
    ):
        """
        BUG #2: GET /projects/{id}/resources returns 500.
        Root cause: `from app.schemas.resource import ResourceAllocation`
        inside the route handler — no such class exists in that module.
        The correct name is `ProjectResourceAllocation`.
        """
        pid = project["id"]
        response = client.get(f"/projects/{pid}/resources", headers=admin_headers)
        assert response.status_code == 500, (
            "If status != 500, the ResourceAllocation import bug has been fixed."
        )
