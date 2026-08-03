"""User ORM model.

A registered user of the platform (customer, provider or admin). This schema is
deliberately lean and is expected to be expanded by the authentication team
(verification documents, password-reset fields, etc.). Keep it focused on what
the core platform needs so foreign keys stay stable.
"""
from typing import List

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.constants import UserRole
from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """A registered user of the platform (customer, provider or admin)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.CUSTOMER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships to other modules' models (populated as those land).
    bookings: Mapped[List["Booking"]] = relationship(  # noqa: F821
        back_populates="customer", foreign_keys="Booking.customer_id"
    )

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"<User id={self.id} email={self.email} role={self.role.value}>"
