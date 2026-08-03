"""Unit tests for the repository layer.

Repositories are exercised directly (bypassing services) to cover the
data-access layer in isolation — the layer that sits between the HTTP/service
code and the database.
"""
from app.common.pagination import PageParams
from app.repositories.booking_repository import BookingRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.service_filters import ServiceFilters
from app.repositories.service_repository import ServiceRepository
from app.schemas.category import CategoryCreate
from tests import factories


async def test_category_repository_create_and_get(db):
    repo = CategoryRepository(db)
    created = await repo.create(CategoryCreate(name="Cleaning", slug="cleaning"), "cleaning")
    fetched = await repo.get(created.id)
    assert fetched is not None
    assert fetched.name == "Cleaning"
    assert (await repo.get_by_slug("cleaning")).id == created.id


async def test_category_repository_list_excludes_inactive(db):
    repo = CategoryRepository(db)
    await repo.create(CategoryCreate(name="Cleaning", slug="cleaning"), "cleaning")
    await repo.create(CategoryCreate(name="Hidden", slug="hidden", is_active=False), "hidden")

    active_items, active_total = await repo.list(PageParams(page=1, page_size=10))
    assert active_total == 1
    assert active_items[0].name == "Cleaning"

    _, all_total = await repo.list(PageParams(page=1, page_size=10), include_inactive=True)
    assert all_total == 2


async def test_service_repository_list_with_filters(db):
    category = await factories.make_category(db, name="Cleaning")
    provider_user = await factories.make_user(db, role="provider")
    provider = await factories.make_provider(db, provider_user)
    await factories.make_service(
        db, provider=provider, category=category, title="Carpet Cleaning", price=80
    )
    await factories.make_service(
        db, provider=provider, category=category, title="Plumbing", price=200
    )

    repo = ServiceRepository(db)
    # Search filter.
    items, total = await repo.list(
        PageParams(page=1, page_size=10), ServiceFilters(query="carpet")
    )
    assert total == 1
    assert items[0].title == "Carpet Cleaning"

    # Price ceiling.
    items, total = await repo.list(
        PageParams(page=1, page_size=10), ServiceFilters(max_price=100)
    )
    assert total == 1
    assert items[0].title == "Carpet Cleaning"


async def test_booking_repository_count_overlaps(db):
    provider_user = await factories.make_user(db, role="provider")
    provider = await factories.make_provider(db, provider_user)
    category = await factories.make_category(db)
    service = await factories.make_service(
        db, provider=provider, category=category, duration_minutes=60
    )

    day = factories.next_date()
    booking_repo = BookingRepository(db)
    await booking_repo.create(
        reference_code="BK-ONE",
        service_id=service.id,
        customer_id=1,
        provider_id=provider.id,
        service_title=service.title,
        scheduled_date=day,
        scheduled_start=factories.at(10),
        scheduled_end=factories.at(11),
        total_price=100,
    )

    # 10:30-11:30 overlaps the 10:00-11:00 booking.
    assert (
        await booking_repo.count_overlaps(
            provider_id=provider.id,
            scheduled_date=day,
            scheduled_start=factories.at(10, 30),
            scheduled_end=factories.at(11, 30),
        )
        == 1
    )
    # 13:00-14:00 does not overlap anything.
    assert (
        await booking_repo.count_overlaps(
            provider_id=provider.id,
            scheduled_date=day,
            scheduled_start=factories.at(13),
            scheduled_end=factories.at(14),
        )
        == 0
    )


async def test_schedule_repository_upsert_day(db):
    provider_user = await factories.make_user(db, role="provider")
    provider = await factories.make_provider(db, provider_user)

    schedule_repo = ScheduleRepository(db)
    slot = await schedule_repo.create(
        provider.id,
        factories_slot(),
    )
    assert (await schedule_repo.get(slot.id)).provider_id == provider.id
    assert (await schedule_repo.get_for_day(provider.id, slot.day_of_week)).id == slot.id


def factories_slot():
    from app.common.constants import DAY_OF_WEEK_FROM_ISO
    from app.schemas.schedule import ScheduleSlot

    return ScheduleSlot(
        day_of_week=DAY_OF_WEEK_FROM_ISO[factories.next_date().weekday()],
        start_time=factories.at(9),
        end_time=factories.at(17),
    )
