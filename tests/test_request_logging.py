import logging

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _record_by_message(records, message: str):
    return next(record for record in records if record.getMessage().startswith(message))


def test_request_logging_includes_request_id_method_path_status_and_duration(caplog):
    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        response = client.get(
            "/healthz",
            headers={"X-Request-ID": "logging-rid-123"},
        )

    assert response.status_code == 200

    started = _record_by_message(caplog.records, "request_started")
    completed = _record_by_message(caplog.records, "request_completed")

    assert started.request_id == "logging-rid-123"
    assert started.method == "GET"
    assert started.path == "/healthz"

    assert completed.request_id == "logging-rid-123"
    assert completed.method == "GET"
    assert completed.path == "/healthz"
    assert completed.status_code == 200
    assert completed.duration_ms >= 0


def test_request_logging_does_not_log_query_string_or_authorization_header(caplog):
    secret_token = "super-secret-token-value"

    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        response = client.get(
            "/auth/me?debug=true",
            headers={
                "Authorization": f"Bearer {secret_token}",
                "X-Request-ID": "logging-rid-456",
            },
        )

    assert response.status_code == 401

    rendered_logs = "\n".join(record.getMessage() for record in caplog.records)

    assert secret_token not in rendered_logs
    assert "debug=true" not in rendered_logs

    completed = _record_by_message(caplog.records, "request_completed")
    assert completed.path == "/auth/me"
    assert completed.status_code == 401
