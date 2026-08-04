"""Data-access layer for providers."""

from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import (
    case,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import BookingStatus
from app.models.booking import Booking
from app.models.provider import Provider
from app.models.provider_portfolio import (
    ProviderPortfolioImage,
)
from app.models.service import Service
from app.repositories.base import BaseRepository
from app.schemas.admin import ProviderOnboard
from app.schemas.provider import (
    PortfolioImageCreate,
    ProviderProfileUpdate,
)


class ProviderRepository(BaseRepository):
    """Queries and persistence operations for providers."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        super().__init__(db)

    async def get(
        self,
        provider_id: int,
    ) -> Optional[Provider]:
        result = await self.db.execute(
            select(Provider).where(
                Provider.id == provider_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: int,
    ) -> Optional[Provider]:
        result = await self.db.execute(
            select(Provider).where(
                Provider.user_id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def get_owner_user_id(
        self,
        provider_id: int,
    ) -> Optional[int]:
        result = await self.db.execute(
            select(Provider.user_id).where(
                Provider.id == provider_id
            )
        )

        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
    ) -> Sequence[Provider]:
        statement = select(Provider).order_by(
            Provider.rating.desc()
        )

        if category:
            statement = statement.where(
                Provider.category.ilike(
                    f"%{category}%"
                )
            )

        result = await self.db.execute(
            statement.offset(skip).limit(limit)
        )

        return result.scalars().all()

    async def create(
        self,
        user_id: int,
        data: ProviderOnboard,
    ) -> Provider:
        provider = Provider(
            user_id=user_id,
            business_name=data.business_name,
            description=data.description or "",
            category=data.category,
            hourly_rate=data.hourly_rate,
            city=data.city or "",
            address=data.address or "",
            is_verified=False,
        )

        self.db.add(provider)
        await self.db.flush()

        return provider

    async def update_profile(
        self,
        provider: Provider,
        data: ProviderProfileUpdate,
    ) -> Provider:
        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(provider, field, value)

        self.db.add(provider)
        await self.db.flush()

        return provider

    async def update_verification(
        self,
        provider: Provider,
        is_verified: bool,
    ) -> Provider:
        provider.is_verified = is_verified

        self.db.add(provider)
        await self.db.flush()

        return provider

    async def update_rating(
        self,
        provider: Provider,
        new_rating,
    ) -> Provider:
        provider.rating = new_rating

        self.db.add(provider)
        await self.db.flush()

        return provider

    async def search(
        self,
        *,
        query: Optional[str] = None,
        category: Optional[str] = None,
        min_rate: Optional[float] = None,
        max_rate: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> Sequence[Provider]:
        statement = select(Provider)

        if query:
            pattern = f"%{query}%"

            statement = statement.where(
                Provider.business_name.ilike(pattern)
                | Provider.description.ilike(pattern)
                | Provider.category.ilike(pattern)
            )

        if category:
            statement = statement.where(
                Provider.category.ilike(
                    f"%{category}%"
                )
            )

        if min_rate is not None:
            statement = statement.where(
                Provider.hourly_rate >= min_rate
            )

        if max_rate is not None:
            statement = statement.where(
                Provider.hourly_rate <= max_rate
            )

        statement = statement.order_by(
            Provider.rating.desc()
        )

        if limit is not None:
            statement = statement.limit(limit)

        result = await self.db.execute(statement)

        return result.scalars().all()

    async def add_portfolio_image(
        self,
        provider_id: int,
        data: PortfolioImageCreate,
    ) -> ProviderPortfolioImage:
        image = ProviderPortfolioImage(
            provider_id=provider_id,
            image_url=data.image_url,
            caption=data.caption,
        )

        self.db.add(image)
        await self.db.flush()

        return image

    async def list_portfolio_images(
        self,
        provider_id: int,
    ) -> Sequence[ProviderPortfolioImage]:
        result = await self.db.execute(
            select(ProviderPortfolioImage)
            .where(
                ProviderPortfolioImage.provider_id
                == provider_id
            )
            .order_by(
                ProviderPortfolioImage.created_at.desc()
            )
        )

        return result.scalars().all()

    async def get_portfolio_image(
        self,
        provider_id: int,
        image_id: int,
    ) -> Optional[ProviderPortfolioImage]:
        result = await self.db.execute(
            select(ProviderPortfolioImage).where(
                ProviderPortfolioImage.id == image_id,
                ProviderPortfolioImage.provider_id
                == provider_id,
            )
        )

        return result.scalar_one_or_none()

    async def delete_portfolio_image(
        self,
        image: ProviderPortfolioImage,
    ) -> None:
        await self.db.delete(image)
        await self.db.flush()

    async def statistics(
        self,
        provider_id: int,
    ) -> dict:
        total_services = await self.db.scalar(
            select(
                func.count(Service.id)
            ).where(
                Service.provider_id == provider_id
            )
        )

        booking_result = await self.db.execute(
            select(
                func.count(Booking.id),
                func.sum(
                    case(
                        (
                            Booking.status
                            == BookingStatus.PENDING,
                            1,
                        ),
                        else_=0,
                    )
                ),
                func.sum(
                    case(
                        (
                            Booking.status
                            == BookingStatus.ACCEPTED,
                            1,
                        ),
                        else_=0,
                    )
                ),
                func.sum(
                    case(
                        (
                            Booking.status
                            == BookingStatus.COMPLETED,
                            1,
                        ),
                        else_=0,
                    )
                ),
                func.sum(
                    case(
                        (
                            Booking.status
                            == BookingStatus.CANCELLED,
                            1,
                        ),
                        else_=0,
                    )
                ),
                func.sum(
                    case(
                        (
                            Booking.status
                            == BookingStatus.COMPLETED,
                            Booking.total_price,
                        ),
                        else_=Decimal("0.00"),
                    )
                ),
            ).where(
                Booking.provider_id == provider_id
            )
        )

        (
            total_bookings,
            pending_bookings,
            accepted_bookings,
            completed_bookings,
            cancelled_bookings,
            total_revenue,
        ) = booking_result.one()

        portfolio_images = await self.db.scalar(
            select(
                func.count(
                    ProviderPortfolioImage.id
                )
            ).where(
                ProviderPortfolioImage.provider_id
                == provider_id
            )
        )

        return {
            "total_services": int(
                total_services or 0
            ),
            "total_bookings": int(
                total_bookings or 0
            ),
            "pending_bookings": int(
                pending_bookings or 0
            ),
            "accepted_bookings": int(
                accepted_bookings or 0
            ),
            "completed_bookings": int(
                completed_bookings or 0
            ),
            "cancelled_bookings": int(
                cancelled_bookings or 0
            ),
            "total_revenue": (
                total_revenue
                or Decimal("0.00")
            ),
            "portfolio_images": int(
                portfolio_images or 0
            ),
        }