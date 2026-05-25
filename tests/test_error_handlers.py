from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_http_error_response_is_structured_and_has_request_id():
    response = client.get("/auth/me", headers={"X-Request-ID": "test-rid-123"})

    assert response.status_code == 401
    assert response.headers["X-Request-ID"] == "test-rid-123"

    body = response.json()
    assert body["error"]["code"] == "http_error"
    assert body["error"]["status_code"] == 401
    assert body["error"]["request_id"] == "test-rid-123"
    assert body["error"]["message"] == "No bearer token"


def test_validation_error_response_is_structured():
    response = client.post(
        "/auth/register",
        headers={"X-Request-ID": "validation-rid-123"},
        json={
            "email": "not-an-email",
            "password": "short",
        },
    )

    assert response.status_code == 422
    assert response.headers["X-Request-ID"] == "validation-rid-123"

    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["status_code"] == 422
    assert body["error"]["request_id"] == "validation-rid-123"
    assert body["error"]["details"]


def test_healthz_includes_request_id_header():
    response = client.get("/healthz", headers={"X-Request-ID": "health-rid-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "health-rid-123"
    assert response.json()["ok"] is True
