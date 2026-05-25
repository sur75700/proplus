from fastapi.testclient import TestClient

import app.auth_v2 as auth_v2
from app.main import app


client = TestClient(app)


def assert_error(response, status_code: int, message: str):
    body = response.json()

    assert response.status_code == status_code
    assert body["error"]["code"] == "http_error"
    assert body["error"]["status_code"] == status_code
    assert body["error"]["message"] == message
    assert body["error"]["request_id"]


async def noop_async(*args, **kwargs):
    return None


def test_auth_me_without_bearer_returns_401():
    response = client.get("/auth/me")

    assert_error(response, 401, "No bearer token")


def test_register_success_uses_email_verification_flow(monkeypatch):
    sent = {}

    async def fake_create_user(email: str, password: str) -> str:
        assert email == "new-user@example.com"
        assert password == "StrongPass12345"
        return "user-123"

    async def fake_create_email_verify_token(user_id: str, email: str) -> str:
        assert user_id == "user-123"
        assert email == "new-user@example.com"
        return "verify-token-123"

    async def fake_send_email(to: str, subject: str, html: str):
        sent["to"] = to
        sent["subject"] = subject
        sent["html"] = html

    monkeypatch.setattr(auth_v2, "create_user", fake_create_user)
    monkeypatch.setattr(auth_v2, "create_email_verify_token", fake_create_email_verify_token)
    monkeypatch.setattr(auth_v2, "send_email", fake_send_email)
    monkeypatch.setattr(auth_v2, "log_event", noop_async)

    response = client.post(
        "/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "StrongPass12345",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": "user-123",
        "email": "new-user@example.com",
        "verify_sent": True,
    }
    assert sent["to"] == "new-user@example.com"
    assert "Verify your email" in sent["subject"]
    assert "verify-token-123" in sent["html"]


def test_register_existing_email_returns_409(monkeypatch):
    async def fake_create_user(email: str, password: str) -> str:
        return ""

    monkeypatch.setattr(auth_v2, "create_user", fake_create_user)

    response = client.post(
        "/auth/register",
        json={
            "email": "existing@example.com",
            "password": "StrongPass12345",
        },
    )

    assert_error(response, 409, "email already exists")


def test_login_unknown_user_returns_401(monkeypatch):
    async def fake_rate_limit_or_429(key: str, limit: int, window_sec: int):
        return None

    async def fake_get_user_by_email(email: str):
        return None

    monkeypatch.setattr(auth_v2, "rate_limit_or_429", fake_rate_limit_or_429)
    monkeypatch.setattr(auth_v2, "get_user_by_email", fake_get_user_by_email)

    response = client.post(
        "/auth/login",
        json={
            "email": "missing@example.com",
            "password": "StrongPass12345",
        },
    )

    assert_error(response, 401, "invalid credentials")


def test_refresh_rejects_access_token():
    access_token = auth_v2.create_access("507f1f77bcf86cd799439011")

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": access_token,
        },
    )

    assert_error(response, 400, "not a refresh token")
