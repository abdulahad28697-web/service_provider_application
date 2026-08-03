"""Base class shared by all repositories.

Kept intentionally thin: it only holds the session so concrete repositories
don't each re-implement the ``__init__`` boilerplate. A generic CRUD base is
deliberately avoided because the queries in this project are heterogeneous —
each repository exposes exactly the operations its aggregate needs.
"""
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Hold the async session used by all queries in a repository."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @property
    def session(self) -> AsyncSession:
        """Alias for :attr:`db`, for callers that prefer a noun."""
        return self.db
