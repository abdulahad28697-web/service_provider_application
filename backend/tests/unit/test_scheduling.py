"""Unit tests for the scheduling service (availability + time math)."""
import pytest

from app.common.constants import DAY_OF_WEEK_FROM_ISO
from app.core.exceptions import BadRequestError
from app.repositories.booking_repository import BookingRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.schemas.schedule import ScheduleSlot
from app.services.scheduling_service import SchedulingService
from tests import factories


def test_compute_end_time_same_day():
    assert SchedulingService.compute_end_time(factories.at(10), 120).hour == 12


def test_compute_end_time_rolls_past_midnight():
    end = SchedulingService.compute_end_time(factories.at(23), 120)
    assert end.hour == 1


@pytest.fixture
async def setup(db):
    provider_user = await factories.make_user(db, role="provider")
    provider = await factories.make_provider(db, provider_user)
    category = await factories.make_category(db)
    service = await factories.make_service(
        db, provider=provider, category=category, duration_minutes=60
    )
    return {"provider": provider, "service": service, "db": db}


@pytest.fixture
async def scheduler(db):
    return SchedulingService(db)


async def _add_schedule(db, provider, start, end):
    return await ScheduleRepository(db).create(
        provider.id,
        ScheduleSlot(
            day_of_week=DAY_OF_WEEK_FROM_ISO[factories.next_date().weekday()],
            start_time=start,
            end_time=end,
        ),
    )


async def test_available_within_schedule(scheduler, setup):
    db, provider = setup["db"], setup["provider"]
    await _add_schedule(db, provider, factories.at(9), factories.at(18))
    ok = await scheduler.provider_available(
        provider_id=provider.id,
        scheduled_date=factories.next_date(),
        scheduled_start=factories.at(10),
        scheduled_end=factories.at(11),
    )
    assert ok is True


async def test_unavailable_outside_schedule(scheduler, setup):
    db, provider = setup["db"], setup["provider"]
    await _add_schedule(db, provider, factories.at(9), factories.at(11))
    ok = await scheduler.provider_available(
        provider_id=provider.id,
        scheduled_date=factories.next_date(),
        scheduled_start=factories.at(14),
        scheduled_end=factories.at(15),
    )
    assert ok is False


async def test_strict_requires_schedule(scheduler, setup):
    db, provider = setup["db"], setup["provider"]
    ok = await scheduler.provider_available(
        provider_id=provider.id,
        scheduled_date=factories.next_date(),
        scheduled_start=factories.at(10),
        scheduled_end=factories.at(11),
        strict=True,
    )
    assert ok is False


async def test_lenient_allows_without_schedule(scheduler, setup):
    db, provider = setup["db"], setup["provider"]
    ok = await scheduler.provider_available(
        provider_id=provider.id,
        scheduled_date=factories.next_date(),
        scheduled_start=factories.at(10),
        scheduled_end=factories.at(11),
    )
    assert ok is True


async def test_ensure_available_rejects_overlap(scheduler, setup):
    db, provider, service = setup["db"], setup["provider"], setup["service"]
    day = factories.next_date()
    # First booking occupies 10:00-11:00.
    await BookingRepository(db).create(
        reference_code="BK-FIRST",
        service_id=service.id,
        customer_id=1,
        provider_id=provider.id,
        service_title=service.title,
        scheduled_date=day,
        scheduled_start=factories.at(10),
        scheduled_end=factories.at(11),
        total_price=100,
    )
    with pytest.raises(BadRequestError):
        await scheduler.ensure_available(
            provider_id=provider.id,
            scheduled_date=day,
            scheduled_start=factories.at(10, 30),
            scheduled_end=factories.at(11, 30),
        )
