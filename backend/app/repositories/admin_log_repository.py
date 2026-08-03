"""Data-access layer for admin audit logs."""
from typing import Optional, Sequence

from sqlalchemy import select

from app.models.admin_log import AdminLog
from app.repositories.base import BaseRepository


class AdminLogRepository(BaseRepository):
    """Queries for :class:`~app.models.admin_log.AdminLog`."""

    async def log_action(
        self, action: str, performed_by: Optional[int], details: str
    ) -> AdminLog:
        """Record an administrative action in the audit trail."""
        log = AdminLog(action=action, performed_by=performed_by, details=details)
        self.db.add(log)
        await self.db.flush()
        return log

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[AdminLog]:
        """Return audit logs, most recent first."""
        result = await self.db.execute(
            select(AdminLog).order_by(AdminLog.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()
