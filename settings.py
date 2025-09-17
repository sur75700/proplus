from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB: str = "proplus"
    JWT_SECRET: str = "change_me"
    JWT_EXPIRES_MIN: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
