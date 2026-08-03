"""Unit tests for the Booking service lifecycle and rules."""
import pytest

from app.common.constants import BookingStatus
from app.common.pagination import PageParams
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.schemas.booking import BookingCreate
from app.services.booking_service import BookingService
from tests import factories


@pytest.fixture
async def setup(db):
    customer = await factories.make_user(db, full_name="Customer")
    provider_user = await factories.make_user(db, full_name="Provider", role="provider")
    provider = await factories.make_provider(db, provider_user)
    category = await factories.make_category(db)
    service = await factories.make_service(
        db,
        provider=provider,
        category=category,
        price=100,
        duration_minutes=120,  # per_hour -> total = 200
    )
    return {
        "customer": customer,
        "provider_user": provider_user,
        "provider": provider,
        "service": service,
    }


@pytest.fixture
async def svc(db):
    return BookingService(db)


async def _book(svc, customer, service):
    return await svc.book(
        customer,
        BookingCreate(
            service_id=service.id,
            scheduled_date=factories.next_date(),
            scheduled_start=factories.at(10),
        ),
    )


async def test_book_creates_pending_and_prices_by_hour(svc, db, setup):
    booking = await _book(svc, setup["customer"], setup["service"])
    assert booking.status == BookingStatus.PENDING
    assert booking.reference_code.startswith("BK-")
    assert booking.total_price == 200  # 100/hr * 120min
    assert booking.scheduled_end.hour == 12


async def test_book_inactive_service_not_found(svc, setup):
    service = setup["service"]
    service.is_active = False
    await svc.db.flush()
    with pytest.raises(NotFoundError):
        await _book(svc, setup["customer"], service)


async def test_accept_flow(svc, setup):
    booking = await _book(svc, setup["customer"], setup["service"])
    accepted = await svc.accept(booking.id, setup["provider_user"])
    assert accepted.status == BookingStatus.ACCEPTED


async def test_complete_pending_is_invalid_transition(svc, setup):
    booking = await _book(svc, setup["customer"], setup["service"])
    with pytest.raises(ConflictError):
        await svc.complete(booking.id, setup["provider_user"])


async def test_complete_after_accept(svc, setup):
    booking = await _book(svc, setup["customer"], setup["service"])
    await svc.accept(booking.id, setup["provider_user"])
    completed = await svc.complete(booking.id, setup["provider_user"])
    assert completed.status == BookingStatus.COMPLETED
    assert completed.completed_at is not None


async def test_reject_flow(svc, setup):
    booking = await _book(svc, setup["customer"], setup["service"])
    rejected = await svc.reject(booking.id, setup["provider_user"], "Not available")
    assert rejected.status == BookingStatus.REJECTED
    assert rejected.reject_reason == "Not available"


async def test_accept_by_stranger_forbidden(svc, db, setup):
    booking = await _book(svc, setup["customer"], setup["service"])
    stranger_user = await factories.make_user(db, full_name="Stranger", role="provider")
    await factories.make_provider(db, stranger_user, business_name="Other")
    with pytest.raises(ForbiddenError):
        await svc.accept(booking.id, stranger_user)


async def test_cancel_by_customer(svc, setup):
    booking = await _book(svc, setup["customer"], setup["service"])
    cancelled = await svc.cancel(booking.id, setup["customer"], "Changed my mind")
    assert cancelled.status == BookingStatus.CANCELLED
    assert cancelled.cancelled_by == "customer"


async def test_stranger_cannot_view(svc, db, setup):
    booking = await _book(svc, setup["customer"], setup["service"])
    stranger = await factories.make_user(db, full_name="Stranger")
    with pytest.raises(ForbiddenError):
        await svc.get(booking.id, stranger)


async def test_overlapping_booking_rejected(svc, db, setup):
    customer2 = await factories.make_user(db, full_name="Customer Two")
    await _book(svc, setup["customer"], setup["service"])  # 10:00-12:00
    with pytest.raises(BadRequestError):
        await _book(svc, customer2, setup["service"])


async def test_history_returns_user_bookings(svc, setup):
    await _book(svc, setup["customer"], setup["service"])
    page = await svc.list_history(setup["customer"], PageParams(page=1, page_size=10))
    assert page.total == 1
