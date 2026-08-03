"""Database session dependency for FastAPI routes."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a new async session per request and ensure it is closed."""
    async with AsyncSessionLocal() as session:
        yield session
