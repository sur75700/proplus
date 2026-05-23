from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_url: str = Field(validation_alias=AliasChoices("MONGO_URL", "mongo_url"))

    access_exp_minutes: int = Field(
        default=15,
        validation_alias=AliasChoices(
            "ACCESS_EXP_MINUTES",
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "access_exp_minutes",
        ),
    )
    refresh_exp_days: int = Field(
        default=30,
        validation_alias=AliasChoices(
            "REFRESH_EXP_DAYS",
            "REFRESH_TOKEN_EXPIRE_DAYS",
            "refresh_exp_days",
        ),
    )

    jwt_alg: str = Field(default="RS256", validation_alias=AliasChoices("JWT_ALG", "jwt_alg"))
    private_key_path: str = Field(
        default="/run/secrets/jwt_private_key",
        validation_alias=AliasChoices("PRIVATE_KEY_PATH", "private_key_path"),
    )
    public_key_path: str = Field(
        default="/run/secrets/jwt_public_key",
        validation_alias=AliasChoices("PUBLIC_KEY_PATH", "public_key_path"),
    )

    redis_url: str = Field(default="redis://redis:6379/0", validation_alias=AliasChoices("REDIS_URL", "redis_url"))

    smtp_host: str = Field(default="localhost", validation_alias=AliasChoices("SMTP_HOST", "smtp_host"))
    smtp_port: int = Field(default=25, validation_alias=AliasChoices("SMTP_PORT", "smtp_port"))
    smtp_user: str | None = Field(default=None, validation_alias=AliasChoices("SMTP_USER", "smtp_user"))
    smtp_pass: str | None = Field(default=None, validation_alias=AliasChoices("SMTP_PASS", "smtp_pass"))
    smtp_from: str = Field(
        default="ProPlus <noreply@proplus.local>",
        validation_alias=AliasChoices("SMTP_FROM", "smtp_from"),
    )

    frontend_base_url: str = Field(
        default="http://localhost:3000",
        validation_alias=AliasChoices("FRONTEND_BASE_URL", "frontend_base_url"),
    )
    api_base_url: str = Field(
        default="http://localhost:8000",
        validation_alias=AliasChoices("API_BASE_URL", "api_base_url"),
    )

    email_dev_mode: bool = Field(
        default=True,
        validation_alias=AliasChoices("EMAIL_DEV_MODE", "email_dev_mode"),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
