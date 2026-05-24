from types import SimpleNamespace

import pytest

from app.core import security_utils


class DummyRequest:
    def __init__(self, user_agent: str = "pytest-agent", host: str = "127.0.0.1"):
        self.headers = {"user-agent": user_agent}
        self.client = SimpleNamespace(host=host)


def test_fingerprint_is_deterministic_for_same_request():
    request = DummyRequest(user_agent="agent-a", host="10.0.0.1")

    fp1 = security_utils.fingerprint_from_request(request)
    fp2 = security_utils.fingerprint_from_request(request)

    assert fp1 == fp2
    assert len(fp1) == 64


def test_fingerprint_changes_when_user_agent_changes():
    fp1 = security_utils.fingerprint_from_request(DummyRequest(user_agent="agent-a"))
    fp2 = security_utils.fingerprint_from_request(DummyRequest(user_agent="agent-b"))

    assert fp1 != fp2


def test_fingerprint_handles_missing_client():
    request = DummyRequest()
    request.client = None

    fp = security_utils.fingerprint_from_request(request)

    assert len(fp) == 64


@pytest.mark.asyncio
async def test_rate_limit_or_429_delegates_to_rate_limit(monkeypatch):
    calls = []

    async def fake_rate_limit(key: str, limit: int, window_sec: int):
        calls.append((key, limit, window_sec))

    monkeypatch.setattr(security_utils, "rate_limit", fake_rate_limit)

    await security_utils.rate_limit_or_429("rl:test", 3, 60)

    assert calls == [("rl:test", 3, 60)]


@pytest.mark.asyncio
async def test_reset_login_fail_delegates_to_clear_login_fail(monkeypatch):
    calls = []

    async def fake_clear_login_fail(email: str):
        calls.append(email)

    monkeypatch.setattr(security_utils, "clear_login_fail", fake_clear_login_fail)

    await security_utils.reset_login_fail("USER@EXAMPLE.COM")

    assert calls == ["USER@EXAMPLE.COM"]
