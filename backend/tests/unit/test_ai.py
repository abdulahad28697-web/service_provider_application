"""Unit tests for the AI assistant service."""
import pytest

from app.common.constants import BookingStatus
from app.schemas.ai import ChatbotMessageRequest, RecommendationRequest
from app.services.ai_service import AIService
from tests import factories


@pytest.fixture
async def svc(db):
    return AIService(db)


async def test_chatbot_finds_plumbing_providers(svc, db):
    provider_user = await factories.make_user(db, role="provider")
    await factories.make_provider(db, provider_user, business_name="Bob's Plumbing")
    response = await svc.chatbot(ChatbotMessageRequest(message="I need a plumber"))
    assert "Bob's Plumbing" in response.response
    assert "plumbing" in response.response.lower()


async def test_chatbot_price_help(svc, db):
    response = await svc.chatbot(ChatbotMessageRequest(message="How much do you cost?"))
    assert "hourly rates" in response.response.lower()


async def test_chatbot_generic_greeting(svc, db):
    response = await svc.chatbot(ChatbotMessageRequest(message="hello there"))
    assert "AI Service Assistant" in response.response


async def test_recommend_providers_with_reason(svc, db):
    provider_user = await factories.make_user(db, role="provider")
    await factories.make_provider(
        db, provider_user, business_name="Top Clean", category="Cleaning", hourly_rate=40
    )
    recs = await svc.recommend(
        RecommendationRequest(query="clean", limit=5)
    )
    assert len(recs.recommendations) == 1
    rec = recs.recommendations[0]
    assert rec.business_name == "Top Clean"
    assert "budget-friendly" in rec.reason


async def test_search_providers_by_filters(svc, db):
    u1 = await factories.make_user(db, role="provider")
    u2 = await factories.make_user(db, role="provider")
    await factories.make_provider(db, u1, business_name="Cheap Fix", category="Repair", hourly_rate=30)
    await factories.make_provider(db, u2, business_name="Lux Clean", category="Cleaning", hourly_rate=150)

    cheap = await svc.search_providers(min_rate=0, max_rate=50)
    assert len(cheap) == 1
    assert cheap[0].business_name == "Cheap Fix"

    cleaning = await svc.search_providers(category="clean")
    assert len(cleaning) == 1
    assert cleaning[0].business_name == "Lux Clean"


async def test_market_trends_aggregates_bookings(svc, db):
    provider_user = await factories.make_user(db, role="provider")
    provider = await factories.make_provider(db, provider_user, category="Plumbing")
    category = await factories.make_category(db)
    service = await factories.make_service(db, provider=provider, category=category)
    customer = await factories.make_user(db)
    await factories.make_booking(
        db, customer=customer, service=service, provider=provider,
        status=BookingStatus.COMPLETED, total_price=200,
    )

    data = await svc.market_trends()
    plumbing = [t for t in data["category_trends"] if t["category"] == "Plumbing"]
    assert len(plumbing) == 1
    assert plumbing[0]["booking_count"] == 1


async def test_market_trends_fallback_when_empty(svc, db):
    data = await svc.market_trends()
    # No providers/bookings -> default trend set is returned.
    assert len(data["category_trends"]) == 3
    assert data["insights"]
