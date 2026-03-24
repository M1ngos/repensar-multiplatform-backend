"""
Comprehensive integration tests for /notifications endpoints.

The notification router uses:
  GET    /notifications/            → list user notifications
  GET    /notifications/unread-count → {unread_count: int}
  PATCH  /notifications/{id}/read  → mark one notification as read
  POST   /notifications/mark-all-read → mark all read
  DELETE /notifications/{id}       → delete notification
  GET    /notifications/{id}       → get single notification
  POST   /notifications/create     → create notification (admin/system)
"""

import pytest
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────────
# LOCAL FIXTURES
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def second_user_headers(client: TestClient, user_types):
    """A second volunteer user's auth headers."""
    client.post(
        "/auth/register",
        json={
            "name": "Second Notif User",
            "email": "notif2@example.com",
            "password": "SecurePass1",
            "user_type": "volunteer",
        },
    )
    resp = client.post(
        "/auth/login",
        json={
            "email": "notif2@example.com",
            "password": "SecurePass1",
        },
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def created_notification(client: TestClient, auth_headers):
    """
    Create a notification for the currently authenticated user
    via POST /notifications/create and return the notification JSON.
    """
    # Get current user ID from /auth/me
    me_resp = client.get("/auth/me", headers=auth_headers)
    assert me_resp.status_code == 200, me_resp.text
    user_id = me_resp.json()["id"]

    resp = client.post(
        "/notifications/create",
        json={
            "user_id": user_id,
            "title": "Test Notification",
            "message": "This is a test notification",
            "type": "info",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ─────────────────────────────────────────────────────────────
# LIST NOTIFICATIONS  (GET /notifications)
# ─────────────────────────────────────────────────────────────


class TestListNotifications:
    def test_list_empty_for_new_user(self, client, auth_headers, user_types):
        response = client.get("/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "total" in data
        assert "unread_count" in data
        assert isinstance(data["notifications"], list)
        assert data["total"] == 0

    def test_list_with_notification(self, client, auth_headers, created_notification):
        response = client.get("/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        notif_ids = [n["id"] for n in data["notifications"]]
        assert created_notification["id"] in notif_ids

    def test_list_unread_only_filter(self, client, auth_headers, created_notification):
        response = client.get("/notifications?unread_only=true", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["notifications"], list)
        # All returned must be unread
        for notif in data["notifications"]:
            assert notif["is_read"] is False

    def test_list_requires_auth(self, client, user_types):
        response = client.get("/notifications")
        assert response.status_code == 403

    def test_list_pagination_limit(self, client, auth_headers, user_types):
        response = client.get("/notifications?limit=5&offset=0", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) <= 5

    def test_user_sees_only_own_notifications(
        self, client, auth_headers, second_user_headers, created_notification
    ):
        """A different user's list must not include this user's notifications."""
        response = client.get("/notifications", headers=second_user_headers)
        data = response.json()
        notif_ids = [n["id"] for n in data["notifications"]]
        assert created_notification["id"] not in notif_ids


# ─────────────────────────────────────────────────────────────
# UNREAD COUNT  (GET /notifications/unread-count)
# ─────────────────────────────────────────────────────────────


class TestUnreadCount:
    def test_unread_count_zero_initially(self, client, auth_headers, user_types):
        response = client.get("/notifications/unread-count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data
        assert data["unread_count"] == 0

    def test_unread_count_increments_on_notification(
        self, client, auth_headers, created_notification
    ):
        response = client.get("/notifications/unread-count", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["unread_count"] >= 1

    def test_unread_count_requires_auth(self, client, user_types):
        response = client.get("/notifications/unread-count")
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────
# MARK AS READ  (PATCH /notifications/{id}/read)
# ─────────────────────────────────────────────────────────────


class TestMarkNotificationRead:
    def test_mark_notification_read(self, client, auth_headers, created_notification):
        nid = created_notification["id"]
        # Should start as unread
        assert created_notification["is_read"] is False

        response = client.patch(
            f"/notifications/{nid}/read",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == nid
        assert data["is_read"] is True
        assert data["read_at"] is not None

    def test_mark_nonexistent_notification_404(self, client, auth_headers, user_types):
        response = client.patch(
            "/notifications/9999/read",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_mark_other_users_notification_404(
        self, client, auth_headers, second_user_headers
    ):
        """Can't mark another user's notification — should 404 (not 403)."""
        # Create notification for first user
        me_resp = client.get("/auth/me", headers=auth_headers)
        user_id = me_resp.json()["id"]
        notif_resp = client.post(
            "/notifications/create",
            json={
                "user_id": user_id,
                "title": "Private",
                "message": "Do not touch",
                "type": "info",
            },
            headers=auth_headers,
        )
        nid = notif_resp.json()["id"]

        # Second user tries to mark it as read
        response = client.patch(
            f"/notifications/{nid}/read",
            headers=second_user_headers,
        )
        assert response.status_code == 404

    def test_mark_read_requires_auth(self, client, user_types):
        response = client.patch("/notifications/1/read")
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────
# MARK ALL AS READ  (POST /notifications/mark-all-read)
# ─────────────────────────────────────────────────────────────


class TestMarkAllRead:
    def test_mark_all_read_success(self, client, auth_headers, created_notification):
        response = client.post(
            "/notifications/mark-all-read",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "marked_as_read" in data
        assert data["marked_as_read"] >= 1

        # Verify unread count is now 0
        count_resp = client.get("/notifications/unread-count", headers=auth_headers)
        assert count_resp.json()["unread_count"] == 0

    def test_mark_all_read_empty_list(self, client, auth_headers, user_types):
        """If user has no unread notifications, returns 0 marked."""
        response = client.post("/notifications/mark-all-read", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["marked_as_read"] == 0

    def test_mark_all_read_requires_auth(self, client, user_types):
        response = client.post("/notifications/mark-all-read")
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────
# DELETE NOTIFICATION  (DELETE /notifications/{id})
# ─────────────────────────────────────────────────────────────


class TestDeleteNotification:
    def test_delete_notification_success(
        self, client, auth_headers, created_notification
    ):
        nid = created_notification["id"]
        response = client.delete(f"/notifications/{nid}", headers=auth_headers)
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Confirm it's gone
        get_resp = client.get(f"/notifications/{nid}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_nonexistent_notification_404(
        self, client, auth_headers, user_types
    ):
        response = client.delete("/notifications/9999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_other_users_notification_404(
        self, client, auth_headers, second_user_headers
    ):
        nid = created_notification_for_user(client, auth_headers)
        response = client.delete(
            f"/notifications/{nid}",
            headers=second_user_headers,
        )
        assert response.status_code == 404

    def test_delete_requires_auth(self, client, user_types):
        response = client.delete("/notifications/1")
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────
# GET SINGLE NOTIFICATION  (GET /notifications/{id})
# ─────────────────────────────────────────────────────────────


class TestGetSingleNotification:
    def test_get_notification_success(self, client, auth_headers, created_notification):
        nid = created_notification["id"]
        response = client.get(f"/notifications/{nid}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == nid
        assert data["title"] == created_notification["title"]

    def test_get_notification_not_found(self, client, auth_headers, user_types):
        response = client.get("/notifications/9999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_other_users_notification_404(
        self, client, auth_headers, second_user_headers
    ):
        nid = created_notification_for_user(client, auth_headers)
        response = client.get(f"/notifications/{nid}", headers=second_user_headers)
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────
# CREATE NOTIFICATION  (POST /notifications/create)
# ─────────────────────────────────────────────────────────────


class TestCreateNotification:
    def test_create_notification_success(self, client, auth_headers, user_types):
        me_resp = client.get("/auth/me", headers=auth_headers)
        user_id = me_resp.json()["id"]

        response = client.post(
            "/notifications/create",
            json={
                "user_id": user_id,
                "title": "Hello",
                "message": "Test message",
                "type": "info",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert data["title"] == "Hello"
        assert data["is_read"] is False
        assert data["type"] == "info"

    def test_create_notification_with_related_ids(
        self, client, auth_headers, user_types
    ):
        me_resp = client.get("/auth/me", headers=auth_headers)
        user_id = me_resp.json()["id"]

        response = client.post(
            "/notifications/create",
            json={
                "user_id": user_id,
                "title": "Task Updated",
                "message": "Your task was updated",
                "type": "success",
                "related_task_id": 1,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_create_notification_requires_auth(self, client, user_types):
        response = client.post(
            "/notifications/create",
            json={
                "user_id": 1,
                "title": "Test",
                "message": "Test",
                "type": "info",
            },
        )
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────
# HELPER (module-level, not a fixture)
# ─────────────────────────────────────────────────────────────


def created_notification_for_user(client: TestClient, headers: dict) -> int:
    """Helper that creates a notification and returns its ID."""
    me_resp = client.get("/auth/me", headers=headers)
    user_id = me_resp.json()["id"]
    resp = client.post(
        "/notifications/create",
        json={
            "user_id": user_id,
            "title": "Temp",
            "message": "Temp message",
            "type": "info",
        },
        headers=headers,
    )
    return resp.json()["id"]
