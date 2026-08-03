"""AdminLog ORM model.

An audit trail of administrative actions (e.g. provider verification). Kept
separate from the user/provider tables so history is preserved even if the
performing admin is later deleted (``performed_by`` is nullable + ON DELETE SET
NULL).
"""
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class AdminLog(Base, TimestampMixin):
    """An audit record of an administrative action."""

    __tablename__ = "admin_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(120), index=True)  # e.g. "VERIFY_PROVIDER"
    performed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    details: Mapped[str] = mapped_column(String(1000), default="")

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"<AdminLog id={self.id} action={self.action}>"
