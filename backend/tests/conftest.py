"""Pytest configuration and shared fixtures.

Uses an in-memory SQLite database (via aiosqlite) so unit tests run without a
PostgreSQL server. The schema is rebuilt per test for isolation. The app's
global engine (``app.database.database.engine``) is intentionally *not* used —
services are exercised directly with sessions from the test engine.
"""
import os

# Override env vars BEFORE any settings import so pydantic-settings never
# touches the real .env file during the test suite.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["ENABLE_REDIS"] = "false"
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'
os.environ["SECRET_KEY"] = "test-secret-that-is-at-least-32-characters-long"

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Keep the booking scheduler from trying to reach Redis during tests.
settings.ENABLE_REDIS = False

# Import the models package so every table is registered on Base.metadata.
from app.database.base import Base  # noqa: E402

import app.models  # noqa: E402,F401


# A single shared in-memory SQLite connection shared across the "pool".
TEST_ENGINE = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSession = async_sessionmaker(
    TEST_ENGINE, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture
async def db() -> AsyncSession:
    """Fresh in-memory schema + session for each test."""
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSession() as session:
        yield session
