"""Provider portfolio image ORM model."""

from typing import Optional

from sqlalchemy import (
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class ProviderPortfolioImage(Base, TimestampMixin):
    """An image displayed in a provider's portfolio."""

    __tablename__ = "provider_portfolio_images"

    __table_args__ = (
        UniqueConstraint(
            "provider_id",
            "image_url",
            name="uq_provider_portfolio_image",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    provider_id: Mapped[int] = mapped_column(
        ForeignKey(
            "providers.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    image_url: Mapped[str] = mapped_column(
        String(500)
    )

    caption: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )