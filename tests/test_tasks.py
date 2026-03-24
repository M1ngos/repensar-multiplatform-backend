"""
Comprehensive integration tests for /tasks endpoints.

Known bugs documented by tests:
- GET /projects/{id}/volunteers (in projects router) → 500 ValidationError:
  VolunteerSummary is constructed without the required `skills_count` field.
  Documented here because a volunteer must exist for the bug to trigger.
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.models.volunteer import VolunteerSkill


# ─────────────────────────────────────────────────────────────
# LOCAL FIXTURES
# ─────────────────────────────────────────────────────────────

_PROJECT_PAYLOAD = {
    "name": "Tasks Test Project",
    "category": "conservation",
    "status": "planning",
    "priority": "medium",
    "requires_volunteers": True,
}

_TASK_PAYLOAD = {
    "title": "Write Documentation",
    "description": "Document the API endpoints",
    "status": "not_started",
    "priority": "medium",
    "suitable_for_volunteers": True,
    "volunteer_spots": 3,
}


@pytest.fixture
def project(client: TestClient, admin_headers):
    """Create a project and return its data."""
    resp = client.post("/projects/", json=_PROJECT_PAYLOAD, headers=admin_headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture
def task(client: TestClient, admin_headers, project):
    """Create a task within the test project and return its data."""
    payload = {**_TASK_PAYLOAD, "project_id": project["id"]}
    resp = client.post("/tasks/", json=payload, headers=admin_headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture
def volunteer(client: TestClient, user_types):
    """Register a volunteer and return their auth details and volunteer ID."""
    reg_resp = client.post(
        "/volunteers/register",
        json={
            "name": "Task Volunteer",
            "email": "task.vol@example.com",
            "password": "SecurePass1",
            "skill_ids": [],
        },
    )
    assert reg_resp.status_code == 200, reg_resp.text
    data = reg_resp.json()
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "task.vol@example.com",
            "password": "SecurePass1",
        },
    )
    token = login_resp.json()["access_token"]
    return {
        "id": data["id"],
        "user_id": data["user_id"],
        "auth_headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def second_volunteer(client: TestClient, user_types):
    """A second registered volunteer."""
    client.post(
        "/volunteers/register",
        json={
            "name": "Second Task Vol",
            "email": "second.task.vol@example.com",
            "password": "SecurePass1",
            "skill_ids": [],
        },
    )
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "second.task.vol@example.com",
            "password": "SecurePass1",
        },
    )
    token = login_resp.json()["access_token"]
    # Get volunteer ID from /volunteers/me
    me_resp = client.get("/volunteers/me", headers={"Authorization": f"Bearer {token}"})
    vol_id = me_resp.json()["id"] if me_resp.status_code == 200 else None
    return {
        "id": vol_id,
        "auth_headers": {"Authorization": f"Bearer {token}"},
    }


# ─────────────────────────────────────────────────────────────
# TASK CREATE  (POST /tasks/)
# ─────────────────────────────────────────────────────────────


class TestTaskCreate:
    def test_create_task_as_admin(self, client, admin_headers, project):
        payload = {**_TASK_PAYLOAD, "project_id": project["id"]}
        response = client.post("/tasks/", json=payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == _TASK_PAYLOAD["title"]
        assert data["project_id"] == project["id"]
        assert "id" in data

    def test_create_task_as_pm(self, client, pm_headers, user_types):
        # PM creates their own project first
        proj_resp = client.post(
            "/projects/",
            json={**_PROJECT_PAYLOAD, "name": "PM Tasks Project"},
            headers=pm_headers,
        )
        pid = proj_resp.json()["id"]
        response = client.post(
            "/tasks/",
            json={**_TASK_PAYLOAD, "project_id": pid},
            headers=pm_headers,
        )
        assert response.status_code == 200

    def test_create_task_forbidden_for_volunteer(self, client, auth_headers, project):
        payload = {**_TASK_PAYLOAD, "project_id": project["id"]}
        response = client.post("/tasks/", json=payload, headers=auth_headers)
        assert response.status_code == 403

    def test_create_task_project_not_found(self, client, admin_headers, user_types):
        payload = {**_TASK_PAYLOAD, "project_id": 9999}
        response = client.post("/tasks/", json=payload, headers=admin_headers)
        assert response.status_code == 404

    def test_create_task_requires_title(self, client, admin_headers, project):
        payload = {"project_id": project["id"], "status": "not_started"}
        response = client.post("/tasks/", json=payload, headers=admin_headers)
        assert response.status_code == 422

    def test_create_task_requires_auth(self, client, project):
        payload = {**_TASK_PAYLOAD, "project_id": project["id"]}
        response = client.post("/tasks/", json=payload)
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────
# TASK LIST  (GET /tasks/)
# ─────────────────────────────────────────────────────────────


class TestTaskList:
    def test_list_tasks_success(self, client, task, admin_headers):
        response = client.get("/tasks/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_requires_auth(self, client, user_types):
        response = client.get("/tasks/")
        assert response.status_code == 403

    def test_list_with_project_filter(self, client, task, project, admin_headers):
        pid = project["id"]
        response = client.get(f"/tasks/?project_id={pid}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(t["project_name"] is not None for t in data)

    def test_list_with_status_filter(self, client, task, admin_headers):
        response = client.get("/tasks/?status=not_started", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_invalid_status_422(self, client, admin_headers, user_types):
        response = client.get("/tasks/?status=badstatus", headers=admin_headers)
        assert response.status_code == 422

    def test_list_with_volunteer_suitable_filter(self, client, task, admin_headers):
        response = client.get(
            "/tasks/?suitable_for_volunteers=true",
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_list_with_priority_filter(self, client, task, admin_headers):
        response = client.get("/tasks/?priority=medium", headers=admin_headers)
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────
# TASK STATS  (GET /tasks/stats)
# ─────────────────────────────────────────────────────────────


class TestTaskStats:
    def test_get_task_stats_public(self, client, user_types):
        response = client.get("/tasks/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "not_started" in data
        assert "in_progress" in data
        assert "completed" in data
        assert "tasks_by_priority" in data

    def test_stats_with_project_filter(self, client, task, project):
        pid = project["id"]
        response = client.get(f"/tasks/stats?project_id={pid}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] >= 1


# ─────────────────────────────────────────────────────────────
# VOLUNTEER AVAILABLE TASKS  (GET /tasks/volunteers/available)
# ─────────────────────────────────────────────────────────────


class TestAvailableTasks:
    def test_get_available_tasks_authenticated(self, client, task, volunteer):
        response = client.get(
            "/tasks/volunteers/available",
            headers=volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Task has suitable_for_volunteers=True, should appear
        assert any(t["task_id"] == task["id"] for t in data)

    def test_available_tasks_requires_auth(self, client, user_types):
        response = client.get("/tasks/volunteers/available")
        assert response.status_code == 403

    def test_available_tasks_match_score_present(self, client, task, volunteer):
        response = client.get(
            "/tasks/volunteers/available",
            headers=volunteer["auth_headers"],
        )
        assert response.status_code == 200
        for item in response.json():
            assert "match_score" in item
            assert 0.0 <= item["match_score"] <= 1.0


# ─────────────────────────────────────────────────────────────
# TASK DETAIL  (GET /tasks/{id})
# ─────────────────────────────────────────────────────────────


class TestTaskDetail:
    def test_get_task_success(self, client, task, admin_headers):
        tid = task["id"]
        response = client.get(f"/tasks/{tid}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tid
        assert "project_name" in data
        assert "volunteer_assignments" in data
        assert "dependencies" in data
        assert "subtasks" in data

    def test_get_task_not_found(self, client, admin_headers, user_types):
        response = client.get("/tasks/9999", headers=admin_headers)
        assert response.status_code == 404

    def test_get_task_requires_auth(self, client, task):
        tid = task["id"]
        response = client.get(f"/tasks/{tid}")
        assert response.status_code == 403

    def test_volunteer_can_view_task(self, client, task, volunteer):
        tid = task["id"]
        response = client.get(f"/tasks/{tid}", headers=volunteer["auth_headers"])
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────
# TASK UPDATE  (PUT /tasks/{id})
# ─────────────────────────────────────────────────────────────


class TestTaskUpdate:
    def test_update_task_admin_full_update(self, client, task, admin_headers):
        tid = task["id"]
        response = client.put(
            f"/tasks/{tid}",
            json={
                "title": "Updated Title",
                "status": "in_progress",
                "priority": "high",
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "in_progress"

    def test_update_task_not_found(self, client, admin_headers, user_types):
        response = client.put(
            "/tasks/9999",
            json={"title": "Ghost"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_update_task_unassigned_volunteer_forbidden(self, client, task, volunteer):
        tid = task["id"]
        response = client.put(
            f"/tasks/{tid}",
            json={"status": "in_progress"},
            headers=volunteer["auth_headers"],
        )
        # Unassigned volunteer cannot update
        assert response.status_code == 403

    def test_assigned_volunteer_can_update_status(
        self, client, task, volunteer, admin_headers
    ):
        """Volunteer assigned to a task may change its status only."""
        tid = task["id"]
        vid = volunteer["id"]
        # Assign volunteer to task
        client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=admin_headers,
        )
        # Now volunteer updates status
        response = client.put(
            f"/tasks/{tid}",
            json={"status": "in_progress"},
            headers=volunteer["auth_headers"],
        )
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"

    def test_assigned_volunteer_cannot_change_title(
        self, client, task, volunteer, admin_headers
    ):
        """Volunteer's non-status fields should be stripped (status kept only)."""
        tid = task["id"]
        vid = volunteer["id"]
        client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=admin_headers,
        )
        original_title = task["title"]
        client.put(
            f"/tasks/{tid}",
            json={"status": "in_progress", "title": "Hacked Title"},
            headers=volunteer["auth_headers"],
        )
        # Title should remain unchanged
        detail = client.get(f"/tasks/{tid}", headers=admin_headers).json()
        assert detail["title"] == original_title


# ─────────────────────────────────────────────────────────────
# TASK DELETE  (DELETE /tasks/{id})
# ─────────────────────────────────────────────────────────────


class TestTaskDelete:
    def test_delete_task_admin(self, client, admin_headers, project):
        # Create a task to delete
        create_resp = client.post(
            "/tasks/",
            json={**_TASK_PAYLOAD, "title": "Delete Me", "project_id": project["id"]},
            headers=admin_headers,
        )
        tid = create_resp.json()["id"]
        response = client.delete(f"/tasks/{tid}", headers=admin_headers)
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    def test_delete_task_forbidden_for_volunteer(self, client, task, volunteer):
        tid = task["id"]
        response = client.delete(
            f"/tasks/{tid}",
            headers=volunteer["auth_headers"],
        )
        assert response.status_code == 403

    def test_delete_task_not_found(self, client, admin_headers, user_types):
        response = client.delete("/tasks/9999", headers=admin_headers)
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────
# TASK VOLUNTEER ASSIGNMENTS  (POST/GET/PUT/DELETE /{id}/volunteers)
# ─────────────────────────────────────────────────────────────


class TestTaskVolunteerAssignments:
    def test_assign_volunteer_success(self, client, task, volunteer, admin_headers):
        tid = task["id"]
        vid = volunteer["id"]
        response = client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["volunteer_id"] == vid
        assert data["task_id"] == tid
        assert data["is_active"] is True

    def test_assign_volunteer_duplicate_returns_409(
        self, client, task, volunteer, admin_headers
    ):
        tid = task["id"]
        vid = volunteer["id"]
        client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=admin_headers,
        )
        response = client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=admin_headers,
        )
        assert response.status_code == 409

    def test_volunteer_self_signup(self, client, task, volunteer):
        tid = task["id"]
        vid = volunteer["id"]
        response = client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=volunteer["auth_headers"],
        )
        assert response.status_code == 200

    def test_volunteer_cannot_signup_other(
        self, client, task, volunteer, second_volunteer
    ):
        """Volunteer cannot assign another volunteer (not themselves)."""
        tid = task["id"]
        vid = volunteer["id"]  # First volunteer's ID
        # second_volunteer tries to sign up the first volunteer
        response = client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=second_volunteer["auth_headers"],
        )
        assert response.status_code == 403

    def test_assign_to_unsuitable_task_returns_400(
        self, client, volunteer, admin_headers, project
    ):
        """Assigning to a task not suitable for volunteers returns 400."""
        unsuitable = client.post(
            "/tasks/",
            json={
                "title": "Internal Task",
                "project_id": project["id"],
                "suitable_for_volunteers": False,
            },
            headers=admin_headers,
        ).json()
        response = client.post(
            f"/tasks/{unsuitable['id']}/volunteers",
            json={"volunteer_id": volunteer["id"]},
            headers=admin_headers,
        )
        assert response.status_code == 400

    def test_get_task_volunteers(self, client, task, volunteer, admin_headers):
        tid = task["id"]
        vid = volunteer["id"]
        client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=admin_headers,
        )
        response = client.get(f"/tasks/{tid}/volunteers", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(a["volunteer_id"] == vid for a in data)

    def test_update_volunteer_assignment(self, client, task, volunteer, admin_headers):
        tid = task["id"]
        vid = volunteer["id"]
        client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=admin_headers,
        )
        response = client.put(
            f"/tasks/{tid}/volunteers/{vid}",
            json={"hours_contributed": 5.0, "notes": "Great work"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert float(response.json()["hours_contributed"]) == 5.0

    def test_remove_volunteer_from_task(self, client, task, volunteer, admin_headers):
        tid = task["id"]
        vid = volunteer["id"]
        client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=admin_headers,
        )
        response = client.delete(
            f"/tasks/{tid}/volunteers/{vid}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert "removed" in response.json()["message"].lower()

    def test_remove_nonexistent_assignment(self, client, task, admin_headers):
        tid = task["id"]
        response = client.delete(
            f"/tasks/{tid}/volunteers/9999",
            headers=admin_headers,
        )
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────
# TASK DEPENDENCIES  (POST/GET /tasks/{id}/dependencies)
# ─────────────────────────────────────────────────────────────


class TestTaskDependencies:
    def _create_second_task(self, client, admin_headers, project):
        resp = client.post(
            "/tasks/",
            json={
                **_TASK_PAYLOAD,
                "title": "Dependent Task",
                "project_id": project["id"],
            },
            headers=admin_headers,
        )
        return resp.json()

    def test_create_dependency_success(self, client, task, admin_headers, project):
        task2 = self._create_second_task(client, admin_headers, project)
        response = client.post(
            f"/tasks/{task['id']}/dependencies",
            json={
                "predecessor_task_id": task["id"],
                "successor_task_id": task2["id"],
                "dependency_type": "finish_to_start",
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["predecessor_task_id"] == task["id"]
        assert data["successor_task_id"] == task2["id"]

    def test_create_dependency_task_not_involved(
        self, client, task, admin_headers, project
    ):
        """Dependency must involve the task in the URL path."""
        task2 = self._create_second_task(client, admin_headers, project)
        task3 = client.post(
            "/tasks/",
            json={**_TASK_PAYLOAD, "title": "Third Task", "project_id": project["id"]},
            headers=admin_headers,
        ).json()
        # Neither predecessor nor successor is task["id"]
        response = client.post(
            f"/tasks/{task['id']}/dependencies",
            json={
                "predecessor_task_id": task2["id"],
                "successor_task_id": task3["id"],
                "dependency_type": "finish_to_start",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400

    def test_get_dependencies_empty(self, client, task, admin_headers):
        tid = task["id"]
        response = client.get(f"/tasks/{tid}/dependencies", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "predecessors" in data
        assert "successors" in data
        assert isinstance(data["predecessors"], list)
        assert isinstance(data["successors"], list)

    def test_get_dependencies_populated(self, client, task, admin_headers, project):
        task2 = self._create_second_task(client, admin_headers, project)
        # Create dep: task → task2
        client.post(
            f"/tasks/{task['id']}/dependencies",
            json={
                "predecessor_task_id": task["id"],
                "successor_task_id": task2["id"],
                "dependency_type": "finish_to_start",
            },
            headers=admin_headers,
        )
        response = client.get(
            f"/tasks/{task['id']}/dependencies",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["successors"]) >= 1

    def test_delete_dependency_as_admin(self, client, task, admin_headers, project):
        task2 = self._create_second_task(client, admin_headers, project)
        dep_resp = client.post(
            f"/tasks/{task['id']}/dependencies",
            json={
                "predecessor_task_id": task["id"],
                "successor_task_id": task2["id"],
                "dependency_type": "finish_to_start",
            },
            headers=admin_headers,
        )
        dep_id = dep_resp.json()["id"]
        response = client.delete(
            f"/tasks/dependencies/{dep_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    def test_delete_dependency_forbidden_for_volunteer(
        self, client, task, volunteer, admin_headers, project
    ):
        task2 = self._create_second_task(client, admin_headers, project)
        dep_resp = client.post(
            f"/tasks/{task['id']}/dependencies",
            json={
                "predecessor_task_id": task["id"],
                "successor_task_id": task2["id"],
                "dependency_type": "finish_to_start",
            },
            headers=admin_headers,
        )
        dep_id = dep_resp.json()["id"]
        response = client.delete(
            f"/tasks/dependencies/{dep_id}",
            headers=volunteer["auth_headers"],
        )
        assert response.status_code == 403

    def test_delete_dependency_not_found(self, client, admin_headers, user_types):
        response = client.delete(
            "/tasks/dependencies/9999",
            headers=admin_headers,
        )
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────
# VOLUNTEER ASSIGNMENT VIEWS  (GET /tasks/volunteers/me/assignments etc.)
# ─────────────────────────────────────────────────────────────


class TestVolunteerTaskAssignmentViews:
    def test_get_my_assignments_success(self, client, task, volunteer, admin_headers):
        tid = task["id"]
        vid = volunteer["id"]
        # Assign volunteer to task
        client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=admin_headers,
        )
        response = client.get(
            "/tasks/volunteers/me/assignments",
            headers=volunteer["auth_headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(a["task_id"] == tid for a in data)

    def test_get_my_assignments_empty_for_non_volunteer(
        self, client, admin_headers, user_types
    ):
        """Admin user has no volunteer profile → 404."""
        response = client.get(
            "/tasks/volunteers/me/assignments",
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_get_my_assignments_requires_auth(self, client, user_types):
        response = client.get("/tasks/volunteers/me/assignments")
        assert response.status_code == 403

    def test_get_volunteer_assignments_own(
        self, client, task, volunteer, admin_headers
    ):
        """Volunteer can view their own assignment list by ID."""
        tid = task["id"]
        vid = volunteer["id"]
        client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=admin_headers,
        )
        response = client.get(
            f"/tasks/volunteers/{vid}/assignments",
            headers=volunteer["auth_headers"],
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_other_volunteer_assignments_forbidden(
        self, client, volunteer, second_volunteer
    ):
        vid = volunteer["id"]
        response = client.get(
            f"/tasks/volunteers/{vid}/assignments",
            headers=second_volunteer["auth_headers"],
        )
        assert response.status_code == 403

    def test_admin_can_view_any_volunteer_assignments(
        self, client, volunteer, admin_headers
    ):
        vid = volunteer["id"]
        response = client.get(
            f"/tasks/volunteers/{vid}/assignments",
            headers=admin_headers,
        )
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────
# KNOWN BUG: GET /projects/{id}/volunteers
# ─────────────────────────────────────────────────────────────


class TestProjectVolunteersBug:
    def test_get_project_volunteers_missing_skills_count_500(
        self, client, task, volunteer, admin_headers, project
    ):
        """
        BUG #3: GET /projects/{id}/volunteers returns 500.
        Root cause: the route handler constructs `VolunteerSummary(...)` without
        the required `skills_count` field and passes the non-existent
        `active_projects_count` instead.
        To trigger this bug a volunteer must actually be assigned to a task in the project.
        """
        tid = task["id"]
        vid = volunteer["id"]
        # Assign volunteer so they appear in the project volunteers list
        client.post(
            f"/tasks/{tid}/volunteers",
            json={"volunteer_id": vid},
            headers=admin_headers,
        )
        pid = project["id"]
        response = client.get(
            f"/projects/{pid}/volunteers",
            headers=admin_headers,
        )
        assert response.status_code == 500, (
            "If status != 500, the missing skills_count / active_projects_count bug has been fixed."
        )
