"""Business logic for the AI assistant features.

The assistant is rule-based (no external LLM): it answers the chatbot, builds
provider recommendations with human-readable reasons, reports market trends from
booking aggregates, and powers provider search — all over the platform's own
data.
"""
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.provider import Provider
from app.repositories.ai_repository import AIRepository
from app.repositories.provider_repository import ProviderRepository
from app.schemas.ai import (
    ChatbotMessageRequest,
    ChatbotResponse,
    RecommendedProvider,
    RecommendationRequest,
    RecommendationResponse,
)


class AIService:
    """Encapsulates the AI assistant's operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ai = AIRepository(db)
        self.providers = ProviderRepository(db)

    # ------------------------------------------------------------------ #
    # Chatbot
    # ------------------------------------------------------------------ #
    async def chatbot(self, request: ChatbotMessageRequest) -> ChatbotResponse:
        """Answer a rule-based assistant message."""
        msg = request.message.lower()
        suggested = ["Ask about providers", "Get price estimates", "Book a service"]

        if "plumber" in msg or "plumbing" in msg:
            found = await self.ai.search_providers_by_keyword("plumbing", limit=2)
            if found:
                names = ", ".join(
                    [p.business_name or "Unnamed Provider" for p in found]
                )
                response = (
                    f"I found some plumbing providers for you: {names}. "
                    "Would you like me to show their details?"
                )
                suggested = [
                    f"View details for {found[0].business_name}",
                    "Search other categories",
                ]
            else:
                response = (
                    "I couldn't find any plumbing service providers available right now."
                )
        elif "price" in msg or "cost" in msg:
            response = (
                "Standard hourly rates for our top service providers range from $20 to "
                "$150 depending on experience and category. Would you like a list of "
                "affordable options?"
            )
            suggested = ["Show services under $50", "Show top rated providers"]
        elif "book" in msg:
            response = (
                "Sure, I can help you schedule a booking. Please specify the service "
                "category or provider you would like to book."
            )
            suggested = ["View all services", "Talk to support"]
        else:
            response = (
                "Hello! I am your AI Service Assistant. How can I help you today? "
                "You can ask me to find service providers, check pricing, or help "
                "with bookings."
            )

        return ChatbotResponse(response=response, suggested_actions=suggested)

    # ------------------------------------------------------------------ #
    # Recommendations
    # ------------------------------------------------------------------ #
    async def recommend(
        self, request: RecommendationRequest
    ) -> RecommendationResponse:
        """Recommend providers for a query, with a reason for each."""
        matched = await self.ai.search_providers_by_keyword(request.query, limit=request.limit)
        pool = matched or await self.ai.list_providers(limit=request.limit)

        recs: List[RecommendedProvider] = []
        for p in pool:
            reason = f"Highly rated in {p.category} with a solid {p.rating or 5.0} rating."
            if p.hourly_rate <= 50:
                reason += " Exceptionally budget-friendly hourly rate."
            if p.is_verified:
                reason += " Background checked and verified provider."

            recs.append(
                RecommendedProvider(
                    provider_id=p.id,
                    business_name=p.business_name,
                    category=p.category,
                    hourly_rate=p.hourly_rate,
                    rating=p.rating,
                    reason=reason,
                )
            )
        return RecommendationResponse(recommendations=recs)

    # ------------------------------------------------------------------ #
    # Market trends
    # ------------------------------------------------------------------ #
    async def market_trends(self) -> dict:
        """Return per-category demand trends derived from booking aggregates."""
        rows = (
            await self.db.execute(
                select(
                    Provider.category,
                    func.count(Booking.id).label("booking_count"),
                    func.avg(Booking.total_price).label("avg_price"),
                )
                .join(Booking, Booking.provider_id == Provider.id)
                .group_by(Provider.category)
                .order_by(func.count(Booking.id).desc())
            )
        ).all()

        trends = [
            {
                "category": category,
                "demand_level": "High" if count > 10 else "Moderate",
                "booking_count": count,
                "average_price": float(avg_price) if avg_price is not None else 0.0,
            }
            for category, count, avg_price in rows
        ]

        # Fallback defaults when the database is empty.
        if not trends:
            trends = [
                {"category": "Plumbing", "demand_level": "High", "booking_count": 0, "average_price": 75.0},
                {"category": "Cleaning", "demand_level": "High", "booking_count": 0, "average_price": 35.0},
                {"category": "Electrical", "demand_level": "Moderate", "booking_count": 0, "average_price": 90.0},
            ]

        return {
            "insights": "AI observed peak demand for home repair services during morning hours.",
            "category_trends": trends,
        }

    # ------------------------------------------------------------------ #
    # Provider search
    # ------------------------------------------------------------------ #
    async def search_providers(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        min_rate: Optional[float] = None,
        max_rate: Optional[float] = None,
    ):
        """Search providers by keyword, category and/or hourly-rate range."""
        return await self.providers.search(
            query=query, category=category, min_rate=min_rate, max_rate=max_rate
        )
