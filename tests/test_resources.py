"""
Comprehensive integration tests for /resources endpoints.

The resources router exposes:
  POST   /resources/                            → create resource (admin/PM)
  GET    /resources/                            → list resources (authenticated)
  GET    /resources/stats                       → resource stats (authenticated)
  GET    /resources/{id}                        → get resource by ID (authenticated)
  GET    /resources/projects/{project_id}/resources  → allocations for project
  POST   /resources/projects/{project_id}/resources  → allocate to project

Note: PUT /resources/{id} and DELETE /resources/{id} are NOT present in the
current router implementation. Tests verify the endpoints that DO exist.
"""

import pytest
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────────
# LOCAL FIXTURES
# ─────────────────────────────────────────────────────────────

_RESOURCE_PAYLOAD = {
    "name": "Steel Pipes",
    "type": "material",
    "description": "Construction material for fencing",
    "unit": "meters",
    "available_quantity": 500.0,
    "unit_cost": 3.50,
    "location": "Warehouse A",
}

_PROJECT_PAYLOAD = {
    "name": "Resource Test Project",
    "category": "reforestation",
    "status": "planning",
    "priority": "medium",
}


@pytest.fixture
def resource(client: TestClient, admin_headers):
    """Create a resource as admin and return its data."""
    resp = client.post("/resources/", json=_RESOURCE_PAYLOAD, headers=admin_headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture
def project(client: TestClient, admin_headers):
    """Create a project and return its data."""
    resp = client.post("/projects/", json=_PROJECT_PAYLOAD, headers=admin_headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ─────────────────────────────────────────────────────────────
# RESOURCE CREATE  (POST /resources/)
# ─────────────────────────────────────────────────────────────


class TestResourceCreate:
    def test_create_resource_as_admin(self, client, admin_headers, user_types):
        response = client.post(
            "/resources/", json=_RESOURCE_PAYLOAD, headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == _RESOURCE_PAYLOAD["name"]
        assert data["type"] == "material"
        assert "id" in data
        assert data["is_active"] is True

    def test_create_resource_as_pm(self, client, pm_headers, user_types):
        response = client.post(
            "/resources/",
            json={**_RESOURCE_PAYLOAD, "name": "PM Resource"},
            headers=pm_headers,
        )
        assert response.status_code == 200

    def test_create_resource_forbidden_for_volunteer(
        self, client, auth_headers, user_types
    ):
        response = client.post(
            "/resources/", json=_RESOURCE_PAYLOAD, headers=auth_headers
        )
        assert response.status_code == 403

    def test_create_resource_requires_auth(self, client, user_types):
        response = client.post("/resources/", json=_RESOURCE_PAYLOAD)
        assert response.status_code == 403

    def test_create_resource_requires_name(self, client, admin_headers, user_types):
        payload = {k: v for k, v in _RESOURCE_PAYLOAD.items() if k != "name"}
        response = client.post("/resources/", json=payload, headers=admin_headers)
        assert response.status_code == 422

    def test_create_resource_requires_type(self, client, admin_headers, user_types):
        payload = {k: v for k, v in _RESOURCE_PAYLOAD.items() if k != "type"}
        response = client.post("/resources/", json=payload, headers=admin_headers)
        assert response.status_code == 422

    def test_create_resource_invalid_type(self, client, admin_headers, user_types):
        payload = {**_RESOURCE_PAYLOAD, "type": "not_a_real_type"}
        response = client.post("/resources/", json=payload, headers=admin_headers)
        assert response.status_code == 422

    def test_create_resource_all_types(self, client, admin_headers, user_types):
        for rtype in ["human", "equipment", "material", "financial"]:
            response = client.post(
                "/resources/",
                json={**_RESOURCE_PAYLOAD, "name": f"{rtype} Resource", "type": rtype},
                headers=admin_headers,
            )
            assert response.status_code == 200


# ─────────────────────────────────────────────────────────────
# RESOURCE LIST  (GET /resources/)
# ─────────────────────────────────────────────────────────────


class TestResourceList:
    def test_list_resources_empty(self, client, auth_headers, user_types):
        response = client.get("/resources/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_resources_with_data(self, client, resource, auth_headers):
        response = client.get("/resources/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert any(r["id"] == resource["id"] for r in data)

    def test_list_requires_auth(self, client, user_types):
        response = client.get("/resources/")
        assert response.status_code == 403

    def test_list_with_type_filter(self, client, resource, auth_headers):
        response = client.get(
            "/resources/?resource_type=material", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_pagination(self, client, resource, auth_headers):
        response = client.get("/resources/?skip=0&limit=5", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) <= 5


# ─────────────────────────────────────────────────────────────
# RESOURCE STATS  (GET /resources/stats)
# ─────────────────────────────────────────────────────────────


class TestResourceStats:
    def test_get_resource_stats_authenticated(self, client, resource, auth_headers):
        response = client.get("/resources/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_resources" in data
        assert "resources_by_type" in data
        assert "total_allocations" in data
        assert "utilization_rate" in data
        assert "most_used_resources" in data

    def test_resource_stats_requires_auth(self, client, user_types):
        response = client.get("/resources/stats")
        assert response.status_code == 403

    def test_stats_reflect_created_resource(self, client, resource, auth_headers):
        response = client.get("/resources/stats", headers=auth_headers)
        data = response.json()
        assert data["total_resources"] >= 1


# ─────────────────────────────────────────────────────────────
# RESOURCE DETAIL  (GET /resources/{id})
# ─────────────────────────────────────────────────────────────


class TestResourceDetail:
    def test_get_resource_success(self, client, resource, auth_headers):
        rid = resource["id"]
        response = client.get(f"/resources/{rid}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rid
        assert data["name"] == resource["name"]
        assert data["type"] == resource["type"]

    def test_get_resource_not_found(self, client, auth_headers, user_types):
        response = client.get("/resources/9999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_resource_requires_auth(self, client, resource):
        rid = resource["id"]
        response = client.get(f"/resources/{rid}")
        assert response.status_code == 403

    def test_volunteer_can_view_resource(self, client, resource, auth_headers):
        rid = resource["id"]
        response = client.get(f"/resources/{rid}", headers=auth_headers)
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────
# PROJECT RESOURCE ALLOCATION  (GET/POST /resources/projects/{id}/resources)
# ─────────────────────────────────────────────────────────────


class TestProjectResourceAllocation:
    def test_get_project_resources_empty(self, client, project, auth_headers):
        pid = project["id"]
        response = client.get(
            f"/resources/projects/{pid}/resources",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_allocate_resource_to_project(
        self, client, project, resource, admin_headers
    ):
        pid = project["id"]
        rid = resource["id"]
        response = client.post(
            f"/resources/projects/{pid}/resources",
            json={
                "resource_id": rid,
                "quantity_allocated": 50.0,
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resource_id"] == rid
        assert data["project_id"] == pid
        assert float(data["quantity_allocated"]) == 50.0
        assert "resource_name" in data
        assert "utilization_percentage" in data

    def test_allocate_forbidden_for_volunteer(
        self, client, project, resource, auth_headers
    ):
        pid = project["id"]
        rid = resource["id"]
        response = client.post(
            f"/resources/projects/{pid}/resources",
            json={"resource_id": rid, "quantity_allocated": 10.0},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_allocate_to_nonexistent_project(
        self, client, resource, admin_headers, user_types
    ):
        rid = resource["id"]
        response = client.post(
            "/resources/projects/9999/resources",
            json={"resource_id": rid, "quantity_allocated": 10.0},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_allocate_nonexistent_resource(self, client, project, admin_headers):
        pid = project["id"]
        response = client.post(
            f"/resources/projects/{pid}/resources",
            json={"resource_id": 9999, "quantity_allocated": 10.0},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_get_project_resources_after_allocation(
        self, client, project, resource, admin_headers
    ):
        pid = project["id"]
        rid = resource["id"]
        client.post(
            f"/resources/projects/{pid}/resources",
            json={"resource_id": rid, "quantity_allocated": 25.0},
            headers=admin_headers,
        )
        response = client.get(
            f"/resources/projects/{pid}/resources",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert any(a["resource_id"] == rid for a in data)

    def test_allocate_requires_auth(self, client, project, resource):
        pid = project["id"]
        rid = resource["id"]
        response = client.post(
            f"/resources/projects/{pid}/resources",
            json={"resource_id": rid, "quantity_allocated": 10.0},
        )
        assert response.status_code == 403
