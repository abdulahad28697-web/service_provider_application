"""Unit tests for the admin dashboard service."""
import pytest

from app.common.constants import BookingStatus
from app.schemas.review import ReviewCreate
from app.services.dashboard_service import DashboardService
from app.services.review_service import ReviewService
from tests import factories


@pytest.fixture
async def svc(db):
    return DashboardService(db)


async def test_dashboard_aggregates(svc, db):
    provider_user = await factories.make_user(db, role="provider")
    provider = await factories.make_provider(db, provider_user, category="Plumbing")
    category = await factories.make_category(db)
    service = await factories.make_service(db, provider=provider, category=category, price=100)

    customer1 = await factories.make_user(db, full_name="Cust One")
    customer2 = await factories.make_user(db, full_name="Cust Two")

    booking1 = await factories.make_booking(
        db, customer=customer1, service=service, provider=provider,
        status=BookingStatus.COMPLETED, total_price=200,
    )
    booking2 = await factories.make_booking(
        db, customer=customer2, service=service, provider=provider,
        status=BookingStatus.PENDING, total_price=100, reference_code="BK-2",
    )

    # One review on the completed booking drives the average rating.
    await ReviewService(db).create(
        customer1, ReviewCreate(booking_id=booking1.id, rating=5)
    )

    data = await svc.get_dashboard_data()
    assert data.total_bookings == 2
    assert float(data.total_revenue) == 200.0  # only completed bookings
    assert data.total_users == 3
    assert data.total_providers == 1
    assert float(data.average_rating) == 5.0
    assert data.recent_bookings[0].customer_name == "Cust One"
    assert data.recent_bookings[0].service_name == service.title
