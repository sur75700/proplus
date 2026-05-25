from dataclasses import dataclass

from bson import ObjectId
from fastapi.testclient import TestClient

import app.admin_v1 as admin_v1
from app.core.admin_deps import admin_required
from app.main import app


client = TestClient(app)


def assert_error(response, status_code: int, message: str):
    body = response.json()

    assert response.status_code == status_code
    assert body["error"]["code"] == "http_error"
    assert body["error"]["status_code"] == status_code
    assert body["error"]["message"] == message
    assert body["error"]["request_id"]


async def fake_admin_required():
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "email": "admin@example.com",
        "role": "admin",
    }


@dataclass
class FakeUpdateResult:
    matched_count: int


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *args, **kwargs):
        return self

    def skip(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def __aiter__(self):
        self._iter = iter(self.docs)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class FakeUsersCollection:
    def __init__(self, docs=None, matched_count=1):
        self.docs = docs or []
        self.matched_count = matched_count
        self.update_calls = []

    async def count_documents(self, filt):
        self.last_count_filter = filt
        return len(self.docs)

    def find(self, filt):
        self.last_find_filter = filt
        return FakeCursor(self.docs)

    async def find_one(self, filt):
        self.last_find_one_filter = filt
        return self.docs[0] if self.docs else None

    async def update_one(self, filt, update):
        self.update_calls.append((filt, update))
        return FakeUpdateResult(matched_count=self.matched_count)


class FakeEventsCollection:
    def __init__(self, docs=None):
        self.docs = docs or []

    async def count_documents(self, filt):
        self.last_count_filter = filt
        return len(self.docs)

    def find(self, filt):
        self.last_find_filter = filt
        return FakeCursor(self.docs)


def setup_function():
    app.dependency_overrides[admin_required] = fake_admin_required


def teardown_function():
    app.dependency_overrides.clear()


def test_admin_users_list_returns_items(monkeypatch):
    uid = ObjectId("507f1f77bcf86cd799439012")
    fake_users = FakeUsersCollection(
        docs=[
            {
                "_id": uid,
                "email": "user@example.com",
                "role": "user",
                "email_verified": True,
                "locked_until": 0,
                "created_at": 123,
            }
        ]
    )

    monkeypatch.setattr(admin_v1, "users", fake_users)

    response = client.get("/admin/users")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == str(uid)
    assert body["items"][0]["email"] == "user@example.com"


def test_admin_get_user_bad_object_id_returns_400():
    response = client.get("/admin/users/not-a-valid-object-id")

    assert_error(response, 400, "invalid object id")


def test_admin_get_user_not_found_returns_404(monkeypatch):
    fake_users = FakeUsersCollection(docs=[])
    monkeypatch.setattr(admin_v1, "users", fake_users)

    response = client.get("/admin/users/507f1f77bcf86cd799439012")

    assert_error(response, 404, "User not found")


def test_admin_set_role_updates_user_role(monkeypatch):
    fake_users = FakeUsersCollection(matched_count=1)
    monkeypatch.setattr(admin_v1, "users", fake_users)

    uid = "507f1f77bcf86cd799439012"
    response = client.post(f"/admin/users/{uid}/role", json={"role": "admin"})

    assert response.status_code == 200
    assert response.json() == {"ok": True, "role": "admin"}
    assert fake_users.update_calls[0][1] == {"$set": {"role": "admin"}}


def test_admin_set_role_rejects_invalid_role():
    uid = "507f1f77bcf86cd799439012"
    response = client.post(f"/admin/users/{uid}/role", json={"role": "owner"})

    assert_error(response, 400, "role must be 'admin' or 'user'")


def test_admin_lock_user_sets_locked_until(monkeypatch):
    fake_users = FakeUsersCollection(matched_count=1)
    monkeypatch.setattr(admin_v1, "users", fake_users)

    uid = "507f1f77bcf86cd799439012"
    response = client.post(f"/admin/users/{uid}/lock", json={"minutes": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["locked_until"] > 0
    assert "$set" in fake_users.update_calls[0][1]
    assert "locked_until" in fake_users.update_calls[0][1]["$set"]


def test_admin_unlock_user_resets_locked_until(monkeypatch):
    fake_users = FakeUsersCollection(matched_count=1)
    monkeypatch.setattr(admin_v1, "users", fake_users)

    uid = "507f1f77bcf86cd799439012"
    response = client.post(f"/admin/users/{uid}/unlock")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert fake_users.update_calls[0][1] == {"$set": {"locked_until": 0}}


def test_admin_auth_events_returns_items(monkeypatch):
    fake_events = FakeEventsCollection(
        docs=[
            {
                "ts": 123,
                "kind": "login_success",
                "user_id": "507f1f77bcf86cd799439012",
                "meta": {"ip": "127.0.0.1"},
            }
        ]
    )

    monkeypatch.setattr(admin_v1, "auth_events", fake_events)

    response = client.get("/admin/auth-events?kind=login_success")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["kind"] == "login_success"
    assert body["items"][0]["meta"] == {"ip": "127.0.0.1"}
