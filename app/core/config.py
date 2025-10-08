# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mongo_url: str
    access_exp_minutes: int = 15
    refresh_exp_days: int = 30
    jwt_alg: str = "RS256"
    private_key_path: str = "/run/secrets/jwt_private_key"
    public_key_path: str = "/run/secrets/jwt_public_key"

    redis_url: str = "redis://redis:6379/0"
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: str | None = None
    smtp_pass: str | None = None
    smtp_from: str = "ProPlus <noreply@proplus.local>"
    frontend_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"

    # ✅ Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",     # ավելցուկ env-երը safe-ignore
    )

settings = Settings()
