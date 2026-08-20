"""Application configuration.

All settings are loaded from environment variables (with sensible defaults)
via pydantic-settings. The corresponding defaults live in ``.env`` at the
backend root so the same code runs both locally and inside Docker.
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_list_delimiter=",",
    )

    # --- App metadata -------------------------------------------------------
    PROJECT_NAME: str = "ServiceHub AI"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # --- Security -----------------------------------------------------------
    SECRET_KEY: str = "dev-secret-key-servicehub-local-dev-123"

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- Database -----------------------------------------------------------
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR.as_posix()}/servicehub.db"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure relative SQLite paths resolve to backend BASE_DIR."""
        if v.startswith("sqlite+aiosqlite:///./"):
            db_filename = v.replace("sqlite+aiosqlite:///./", "")
            target_path = BASE_DIR / db_filename
            return f"sqlite+aiosqlite:///{target_path.as_posix()}"
        return v

    # --- Redis / messaging --------------------------------------------------
    REDIS_URL: str = "redis://redis:6379/0"
    ENABLE_REDIS: bool = False

    NOTIFICATION_CHANNEL: str = "servicehub:notifications"

    # --- CORS ---------------------------------------------------------------
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "https://service-provider-application-m8937xiks-ahad5.vercel.app", "https://service-provider-application-git-main-ahad5.vercel.app"]

    # --- Email / SMTP -------------------------------------------------------
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    EMAILS_FROM_EMAIL: str = "noreply@servicehub.ai"
    EMAILS_FROM_NAME: str = "ServiceHub AI"
    FRONTEND_URL: str = "http://localhost:5173"

    # --- Pagination defaults -----------------------------------------------
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Fail fast if using default secret key in production."""
        # During validation, DEBUG might not be available yet, so we check the data
        debug = info.data.get("DEBUG", False) if info.data else False
        if not debug and v == "change-me-in-production":
            raise ValueError(
                "SECRET_KEY must be changed from the default value in production. "
                "Set a strong random secret in your environment."
            )
        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: List[str], info) -> List[str]:
        """Warn if CORS origins contain wildcard in production."""
        debug = info.data.get("DEBUG", False) if info.data else False
        if not debug and any(origin == "*" for origin in v):
            raise ValueError(
                "CORS_ORIGINS cannot contain '*' in production. "
                "Specify explicit allowed origins."
            )
        return v


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance (fast, avoids re-reading .env)."""
    return Settings()


settings = get_settings()
