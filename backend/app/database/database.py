"""Async engine and session factory.

The engine is created from ``settings.DATABASE_URL``. It supports both
PostgreSQL (production / Docker) and SQLite (local unit tests) because both are
async drivers handled by SQLAlchemy's async engine.
"""
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _build_engine() -> AsyncEngine:
    kwargs = {"pool_pre_ping": True}
    # SQLite (used by tests) cannot use the same pool options as Postgres.
    if settings.DATABASE_URL.startswith("sqlite"):
        kwargs = {"connect_args": {"check_same_thread": False}}
    return create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, **kwargs)


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
