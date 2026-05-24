from app.core import jwt_utils


def test_create_access_decodes_as_access_token():
    token = jwt_utils.create_access("user-123")
    payload = jwt_utils.decode_token(token)

    assert payload["sub"] == "user-123"
    assert payload["typ"] == "access"
    assert "jti" in payload
    assert "iat" in payload
    assert "exp" in payload
    assert jwt_utils.is_refresh(payload) is False


def test_create_refresh_decodes_as_refresh_token():
    token = jwt_utils.create_refresh("user-123", "refresh-jti-123")
    payload = jwt_utils.decode_token(token)

    assert payload["sub"] == "user-123"
    assert payload["typ"] == "refresh"
    assert payload["jti"] == "refresh-jti-123"
    assert "iat" in payload
    assert "exp" in payload
    assert jwt_utils.is_refresh(payload) is True


def test_access_token_expires_before_refresh_token():
    access = jwt_utils.decode_token(jwt_utils.create_access("user-123"))
    refresh = jwt_utils.decode_token(jwt_utils.create_refresh("user-123", "refresh-jti-456"))

    assert access["exp"] > access["iat"]
    assert refresh["exp"] > refresh["iat"]
    assert refresh["exp"] > access["exp"]
