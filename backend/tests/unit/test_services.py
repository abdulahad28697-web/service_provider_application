"""Unit tests for the Service service layer."""
from decimal import Decimal

import pytest

from app.common.pagination import PageParams
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.repositories.service_filters import ServiceFilters
from app.schemas.booking import BookingCreate
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.services.booking_service import BookingService
from app.services.service_service import ServiceService
from tests import factories


@pytest.fixture
async def service(db):
    return ServiceService(db)


@pytest.fixture
async def setup(db):
    category = await factories.make_category(db, name="Cleaning")
    owner_user = await factories.make_user(db, full_name="Owner", role="provider")
    owner = await factories.make_provider(db, owner_user)
    return category, owner_user, owner


async def test_create_service(service, setup):
    category, _, owner = setup
    created = await service.create(
        ServiceCreate(category_id=category.id, title="Deep Clean", price=Decimal("120")),
        owner,
    )
    assert created.provider_id == owner.id
    assert created.slug == "deep-clean"


async def test_create_service_missing_category(service, setup):
    _, _, owner = setup
    with pytest.raises(NotFoundError):
        await service.create(ServiceCreate(category_id=9999, title="X"), owner)


async def test_search_by_query(service, db, setup):
    category, _, owner = setup
    await service.create(
        ServiceCreate(category_id=category.id, title="Carpet Cleaning"), owner
    )
    await service.create(
        ServiceCreate(category_id=category.id, title="Plumbing Repair"), owner
    )
    page = await service.list(
        PageParams(page=1, page_size=10),
        ServiceFilters(query="carpet"),
    )
    assert page.total == 1
    assert page.items[0].title == "Carpet Cleaning"


async def test_filter_by_category(service, db, setup):
    category, _, owner = setup
    other_cat = await factories.make_category(db, name="Repair")
    await service.create(
        ServiceCreate(category_id=category.id, title="Carpet Cleaning"), owner
    )
    await service.create(
        ServiceCreate(category_id=other_cat.id, title="Plumbing"), owner
    )
    page = await service.list(
        PageParams(page=1, page_size=10), ServiceFilters(category_id=category.id)
    )
    assert page.total == 1
    assert page.items[0].title == "Carpet Cleaning"


async def test_update_forbidden_for_non_owner(service, db, setup):
    category, owner_user, owner = setup
    created = await service.create(
        ServiceCreate(category_id=category.id, title="Deep Clean"), owner
    )
    intruder = await factories.make_user(db, full_name="Intruder", role="provider")
    with pytest.raises(ForbiddenError):
        await service.update(created.id, ServiceUpdate(title="Hacked"), intruder)


async def test_update_owner_can_edit(service, setup):
    category, owner_user, owner = setup
    created = await service.create(
        ServiceCreate(category_id=category.id, title="Deep Clean"), owner
    )
    # update() takes a User (the acting user), not the Provider record.
    updated = await service.update(
        created.id, ServiceUpdate(title="Premium Clean"), owner_user
    )
    assert updated.title == "Premium Clean"


async def test_delete_service_with_active_booking_conflict(service, db, setup):
    category, owner_user, owner = setup
    created = await service.create(
        ServiceCreate(category_id=category.id, title="Deep Clean", duration_minutes=60),
        owner,
    )
    # Create a pending booking so deletion must be blocked.
    customer = await factories.make_user(db, full_name="Customer")
    booking_service = BookingService(db)
    await booking_service.book(
        customer,
        BookingCreate(
            service_id=created.id,
            scheduled_date=factories.next_date(),
            scheduled_start=factories.at(10),
        ),
    )
    with pytest.raises(ConflictError):
        await service.delete(created.id, owner_user)
