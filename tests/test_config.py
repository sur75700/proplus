from app.core.config import Settings


def test_settings_accepts_legacy_access_token_expire_alias():
    settings = Settings(
        MONGO_URL="mongodb://localhost:27017/proplus_test",
        ACCESS_TOKEN_EXPIRE_MINUTES=42,
    )

    assert settings.mongo_url == "mongodb://localhost:27017/proplus_test"
    assert settings.access_exp_minutes == 42


def test_settings_accepts_legacy_refresh_token_expire_alias():
    settings = Settings(
        MONGO_URL="mongodb://localhost:27017/proplus_test",
        REFRESH_TOKEN_EXPIRE_DAYS=9,
    )

    assert settings.refresh_exp_days == 9


def test_settings_defaults_are_production_safe_shapes():
    settings = Settings(MONGO_URL="mongodb://localhost:27017/proplus_test")

    assert settings.jwt_alg == "RS256"
    assert settings.access_exp_minutes > 0
    assert settings.refresh_exp_days > 0
    assert settings.private_key_path
    assert settings.public_key_path
    assert settings.redis_url
    assert settings.email_dev_mode is True


def test_settings_accepts_private_and_public_key_path_aliases():
    settings = Settings(
        MONGO_URL="mongodb://localhost:27017/proplus_test",
        PRIVATE_KEY_PATH="secrets/test_private.pem",
        PUBLIC_KEY_PATH="secrets/test_public.pem",
    )

    assert settings.private_key_path == "secrets/test_private.pem"
    assert settings.public_key_path == "secrets/test_public.pem"
