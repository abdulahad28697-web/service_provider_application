"""Application configuration.

All settings are loaded from environment variables (with sensible defaults)
via pydantic-settings. The corresponding defaults live in ``.env`` at the
backend root so the same code runs both locally and inside Docker.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_list_delimiter=",",
    )

    # --- App metadata -------------------------------------------------------
    PROJECT_NAME: str = "ServiceHub AI"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # --- Security -----------------------------------------------------------
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- Database -----------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/servicehub"

    # --- Redis / messaging --------------------------------------------------
    REDIS_URL: str = "redis://redis:6379/0"
    ENABLE_REDIS: bool = True
    NOTIFICATION_CHANNEL: str = "servicehub:notifications"

    # --- CORS ---------------------------------------------------------------
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # --- Pagination defaults -----------------------------------------------
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance (fast, avoids re-reading .env)."""
    return Settings()


settings = get_settings()
