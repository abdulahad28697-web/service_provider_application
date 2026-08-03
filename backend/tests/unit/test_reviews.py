"""Unit tests for the review service."""
from decimal import Decimal

import pytest

from app.common.constants import BookingStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.review import ReviewCreate
from app.services.review_service import ReviewService
from tests import factories


@pytest.fixture
async def setup(db):
    customer = await factories.make_user(db, full_name="Customer")
    provider_user = await factories.make_user(db, role="provider")
    provider = await factories.make_provider(db, provider_user, rating=0)
    category = await factories.make_category(db)
    service = await factories.make_service(db, provider=provider, category=category)
    booking = await factories.make_booking(
        db,
        customer=customer,
        service=service,
        provider=provider,
        status=BookingStatus.COMPLETED,
    )
    return {
        "customer": customer,
        "provider": provider,
        "booking": booking,
    }


@pytest.fixture
async def svc(db):
    return ReviewService(db)


async def test_create_review_updates_provider_rating(svc, db, setup):
    review = await svc.create(
        setup["customer"],
        ReviewCreate(booking_id=setup["booking"].id, rating=5, comment="Great!"),
    )
    assert review.rating == 5
    await db.refresh(setup["provider"])
    assert float(setup["provider"].rating) == 5.0


async def test_duplicate_review_for_booking_conflict(svc, db, setup):
    await svc.create(
        setup["customer"],
        ReviewCreate(booking_id=setup["booking"].id, rating=4),
    )
    with pytest.raises(ConflictError):
        await svc.create(
            setup["customer"],
            ReviewCreate(booking_id=setup["booking"].id, rating=3),
        )


async def test_review_requires_booking_ownership(svc, db, setup):
    stranger = await factories.make_user(db, full_name="Stranger")
    with pytest.raises(NotFoundError):
        await svc.create(
            stranger,
            ReviewCreate(booking_id=setup["booking"].id, rating=4),
        )


async def test_review_missing_booking_not_found(svc, db, setup):
    with pytest.raises(NotFoundError):
        await svc.create(
            setup["customer"],
            ReviewCreate(booking_id=9999, rating=4),
        )


async def test_list_reviews(svc, db, setup):
    await svc.create(
        setup["customer"],
        ReviewCreate(booking_id=setup["booking"].id, rating=5, comment="Nice"),
    )
    reviews = await svc.list()
    assert len(reviews) == 1
    assert reviews[0].rating == Decimal("5.00")
