from sqlalchemy.orm import Session
from repositories.admin.report_repository import ReportRepository
from models.admin import AdminLog

class ReportService:
    def __init__(self, db: Session):
        self.report_repo = ReportRepository(db)

    def get_audit_logs(self, skip: int = 0, limit: int = 100) -> list[AdminLog]:
        return self.report_repo.get_logs(skip, limit)
