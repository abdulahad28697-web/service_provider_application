from sqlalchemy.orm import Session
from repositories.dashboard.dashboard_repository import DashboardRepository
from schemas.dashboard.response import DashboardResponse
from datetime import datetime

class DashboardService:
    def __init__(self, db: Session):
        self.dashboard_repo = DashboardRepository(db)

    def get_dashboard_data(self, start_date: datetime | None = None, end_date: datetime | None = None) -> DashboardResponse:
        data = self.dashboard_repo.get_stats(start_date, end_date)
        return DashboardResponse(**data)
