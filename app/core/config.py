from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ShopFlow"
    app_version: str = "0.2.0"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://shopflow:shopflow@localhost:5432/shopflow"
    secret_key: str = "change-me-in-production"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
