"""Business logic for the admin dashboard."""
from datetime import date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardResponse


class DashboardService:
    """Builds the aggregate statistics shown on the admin dashboard."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.stats = DashboardRepository(db)

    async def get_dashboard_data(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> DashboardResponse:
        """Return dashboard aggregates, optionally scoped to a date range."""
        data = await self.stats.get_stats(start_date, end_date)
        return DashboardResponse(**data)
