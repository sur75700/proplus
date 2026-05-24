import pytest
from pydantic import ValidationError

from app.schemas import LoginIn, RegisterIn, TokenOut


def test_register_requires_valid_email():
    with pytest.raises(ValidationError):
        RegisterIn(email="not-an-email", password="StrongPass12345")


def test_register_requires_minimum_password_length():
    with pytest.raises(ValidationError):
        RegisterIn(email="user@example.com", password="short")


def test_login_schema_accepts_email_and_password():
    payload = LoginIn(email="user@example.com", password="StrongPass12345")

    assert payload.email == "user@example.com"
    assert payload.password == "StrongPass12345"


def test_token_out_defaults_to_bearer():
    token = TokenOut(access_token="access", refresh_token="refresh")

    assert token.token_type == "bearer"
