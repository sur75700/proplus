import pytest

import app.core.emailer as emailer


def test_redact_email_body_hides_verify_token_query_value():
    raw_token = "verify-token-abcdefghijklmnopqrstuvwxyz123456"
    html = f'<a href="https://app.example.com/verify-email?token={raw_token}">Verify</a>'

    redacted = emailer.redact_email_body(html)

    assert raw_token not in redacted
    assert "token=[REDACTED]" in redacted
    assert "verify-email" in redacted


def test_redact_email_body_hides_reset_token_query_value_with_extra_params():
    raw_token = "reset-token-abcdefghijklmnopqrstuvwxyz123456"
    html = f"https://app.example.com/reset-password?next=/home&token={raw_token}"

    redacted = emailer.redact_email_body(html)

    assert raw_token not in redacted
    assert "token=[REDACTED]" in redacted
    assert "reset-password" in redacted


@pytest.mark.asyncio
async def test_send_email_dev_mode_logs_redacted_body(monkeypatch, capsys):
    raw_token = "dev-token-abcdefghijklmnopqrstuvwxyz123456"
    html = f'<a href="https://app.example.com/verify-email?token={raw_token}">Verify</a>'

    monkeypatch.setattr(emailer.settings, "email_dev_mode", True)

    result = await emailer.send_email(
        to="user@example.com",
        subject="Verify your email",
        html=html,
    )

    captured = capsys.readouterr().out

    assert result is True
    assert "TO: user@example.com" in captured
    assert "SUBJECT: Verify your email" in captured
    assert raw_token not in captured
    assert "token=[REDACTED]" in captured
