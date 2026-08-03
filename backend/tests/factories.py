"""Factories to build test records quickly.

Each helper flushes but does not commit, so tests can build a graph of related
records and then exercise the service layer (which commits itself).
"""
from datetime import date, time
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import BookingStatus, PriceUnit, UserRole
from app.common.utils import slugify
from app.core.security import hash_password
from app.models.booking import Booking
from app.models.category import Category
from app.models.provider import Provider
from app.models.service import Service
from app.models.user import User

_user_seq = 0


async def make_user(
    db: AsyncSession,
    *,
    email: str | None = None,
    full_name: str = "Alice Test",
    role: UserRole | str = UserRole.CUSTOMER,
    password: str = "secret123",
) -> User:
    global _user_seq
    _user_seq += 1
    # Callers often pass a plain string (e.g. "provider"); normalise it to the
    # enum so ``role.value`` works on the in-memory object without a re-read.
    role_value = UserRole(role) if isinstance(role, str) else role
    user = User(
        email=email or f"user{_user_seq}@example.com",
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role_value,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    return user


async def make_provider(
    db: AsyncSession,
    user: User,
    *,
    business_name: str = "Test Business",
    verified: bool = True,
    category: str = "Plumbing",
    hourly_rate: Decimal = Decimal("50.00"),
    rating: Decimal = Decimal("4.50"),
) -> Provider:
    provider = Provider(
        user_id=user.id,
        business_name=business_name,
        is_verified=verified,
        rating=rating,
        category=category,
        hourly_rate=hourly_rate,
    )
    db.add(provider)
    await db.flush()
    return provider


async def make_category(
    db: AsyncSession,
    name: str = "Cleaning",
) -> Category:
    category = Category(
        name=name,
        slug=slugify(name),
        description="A test category.",
        is_active=True,
    )
    db.add(category)
    await db.flush()
    return category


async def make_service(
    db: AsyncSession,
    *,
    provider: Provider,
    category: Category,
    title: str = "Deep Clean",
    price: Decimal = Decimal("100.00"),
    price_unit: PriceUnit = PriceUnit.PER_HOUR,
    duration_minutes: int = 120,
    is_active: bool = True,
) -> Service:
    service = Service(
        category_id=category.id,
        provider_id=provider.id,
        title=title,
        slug=slugify(title),
        price=price,
        price_unit=price_unit,
        duration_minutes=duration_minutes,
        is_active=is_active,
        images=[],
    )
    db.add(service)
    await db.flush()
    return service


async def make_booking(
    db: AsyncSession,
    *,
    customer: User,
    service: Service,
    provider: Provider,
    status: BookingStatus = BookingStatus.COMPLETED,
    scheduled_date: date | None = None,
    scheduled_start: time = None,
    scheduled_end: time = None,
    total_price: Decimal | None = None,
    reference_code: str = "BK-TEST",
) -> Booking:
    """Create a booking record directly in the given status."""
    booking = Booking(
        reference_code=reference_code,
        customer_id=customer.id,
        service_id=service.id,
        provider_id=provider.id,
        service_title=service.title,
        scheduled_date=scheduled_date or next_date(),
        scheduled_start=scheduled_start or at(10),
        scheduled_end=scheduled_end or at(12),
        total_price=total_price or service.price,
        status=status,
    )
    db.add(booking)
    await db.flush()
    return booking


def next_date() -> date:
    """A booking date safely in the future."""
    from datetime import timedelta

    return date.today() + timedelta(days=7)


def at(hour: int = 10, minute: int = 0) -> time:
    return time(hour=hour, minute=minute)
