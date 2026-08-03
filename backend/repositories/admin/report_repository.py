from sqlalchemy.orm import Session
from models.admin import AdminLog

class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_action(self, action: str, performed_by: int | None, details: str | None) -> AdminLog:
        log = AdminLog(
            action=action,
            performed_by=performed_by,
            details=details
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_logs(self, skip: int = 0, limit: int = 100) -> list[AdminLog]:
        return self.db.query(AdminLog).order_by(AdminLog.created_at.desc()).offset(skip).limit(limit).all()
