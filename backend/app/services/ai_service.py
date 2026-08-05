"""Business logic for the platform AI user assistant."""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.provider import Provider
from app.models.user import User
from app.repositories.ai_repository import AIRepository
from app.repositories.provider_repository import ProviderRepository
from app.schemas.ai import (
    BookingAssistanceRequest,
    BookingAssistanceResponse,
    ChatbotMessageRequest,
    ChatbotResponse,
    ComparedService,
    FAQRequest,
    FAQResponse,
    PersonalizedSuggestionResponse,
    RecommendedProvider,
    RecommendedService,
    RecommendationRequest,
    RecommendationResponse,
    ServiceComparisonRequest,
    ServiceComparisonResponse,
    ServiceRecommendationRequest,
    ServiceRecommendationResponse,
)


class AIService:
    """Provide rule-based assistance using platform data."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ai = AIRepository(db)
        self.providers = ProviderRepository(db)

    def _recommended_provider(
        self,
        provider: Provider,
    ) -> RecommendedProvider:
        """Convert a provider into a recommendation."""
        reason = (
            f"Rated {provider.rating} in "
            f"{provider.category or 'professional services'}."
        )

        if provider.hourly_rate <= Decimal("50"):
            reason += " Offers a budget-friendly hourly rate."

        if provider.is_verified:
            reason += " This provider is verified."

        return RecommendedProvider(
            provider_id=provider.id,
            business_name=provider.business_name,
            category=provider.category,
            hourly_rate=provider.hourly_rate,
            rating=provider.rating,
            reason=reason,
        )

    def _recommended_service(
        self,
        service,
    ) -> RecommendedService:
        """Convert a service into a recommendation."""
        reason = "Active service matching your request."

        if service.is_featured:
            reason += " It is featured by the platform."

        if service.price <= Decimal("50"):
            reason += " It is also budget friendly."

        price_unit = (
            service.price_unit.value
            if hasattr(service.price_unit, "value")
            else str(service.price_unit)
        )

        return RecommendedService(
            service_id=service.id,
            provider_id=service.provider_id,
            title=service.title,
            description=service.description,
            price=service.price,
            price_unit=price_unit,
            duration_minutes=service.duration_minutes,
            reason=reason,
        )

    async def chatbot(
        self,
        request: ChatbotMessageRequest,
    ) -> ChatbotResponse:
        """Answer a natural-language assistant message."""
        message = request.message.strip().lower()

        if "plumber" in message or "plumbing" in message:
            providers = await self.ai.search_providers_by_keyword(
                "plumbing",
                limit=3,
            )

            if providers:
                names = ", ".join(
                    provider.business_name or "Unnamed Provider"
                    for provider in providers
                )
                response = (
                    f"I found some plumbing providers for you: {names}. "
                    "Would you like to view their details?"
                )
            else:
                response = (
                    "I could not find any plumbing providers available "
                    "right now."
                )

            return ChatbotResponse(
                response=response,
                suggested_actions=[
                    "View provider details",
                    "Search other categories",
                ],
            )

        if any(
            word in message
            for word in ("book", "appointment", "schedule")
        ):
            return ChatbotResponse(
                response=(
                    "I can help you book a service. Choose a service, "
                    "date, start time, location and any notes."
                ),
                suggested_actions=[
                    "Search services",
                    "View provider recommendations",
                    "Start booking assistance",
                ],
            )

        if any(
            word in message
            for word in ("price", "cost", "cheap", "budget")
        ):
            services = await self.ai.search_services(
                max_price=Decimal("50"),
                limit=3,
            )

            response = (
                "Standard hourly rates depend on the service category "
                "and provider experience."
            )

            if services:
                names = ", ".join(
                    service.title
                    for service in services
                )
                response += f" Affordable options include: {names}."

            return ChatbotResponse(
                response=response,
                suggested_actions=[
                    "Show services under 50",
                    "Compare services",
                ],
            )

        if any(
            word in message
            for word in ("provider", "professional", "expert")
        ):
            providers = await self.ai.list_providers(limit=3)

            if providers:
                names = ", ".join(
                    provider.business_name
                    for provider in providers
                )
                response = f"Top provider options include: {names}."
            else:
                response = "No verified providers are currently available."

            return ChatbotResponse(
                response=response,
                suggested_actions=[
                    "Get provider recommendations",
                    "Search providers",
                ],
            )

        if any(
            word in message
            for word in ("service", "clean", "repair")
        ):
            services = await self.ai.search_services(
                query=message,
                limit=3,
            )

            if services:
                names = ", ".join(
                    service.title
                    for service in services
                )
                response = f"I found these services: {names}."
            else:
                response = (
                    "I could not find an exact service match. "
                    "Try using a category or shorter search phrase."
                )

            return ChatbotResponse(
                response=response,
                suggested_actions=[
                    "Browse services",
                    "Get personalized suggestions",
                ],
            )

        return ChatbotResponse(
            response=(
                "Hello! I am your AI Service Assistant. I can find services "
                "and providers, compare prices, answer FAQs, provide "
                "recommendations and assist with bookings."
            ),
            suggested_actions=[
                "Recommend a provider",
                "Recommend a service",
                "Compare services",
                "Help me book",
            ],
        )

    async def recommend(
        self,
        request: RecommendationRequest,
    ) -> RecommendationResponse:
        """Recommend providers matching the user's criteria."""
        providers = await self.providers.search(
            query=request.query,
            category=request.category,
            max_rate=(
                float(request.max_price)
                if request.max_price is not None
                else None
            ),
            limit=request.limit,
        )

        recommendations = [
            self._recommended_provider(provider)
            for provider in providers
            if provider.is_verified
        ]

        return RecommendationResponse(
            recommendations=recommendations
        )

    async def recommend_services(
        self,
        request: ServiceRecommendationRequest,
    ) -> ServiceRecommendationResponse:
        """Recommend services matching natural-language criteria."""
        services = await self.ai.search_services(
            query=request.query,
            category=request.category,
            max_price=request.max_price,
            limit=request.limit,
        )

        if not services:
            services = await self.ai.search_services(
                category=request.category,
                max_price=request.max_price,
                limit=request.limit,
            )

        return ServiceRecommendationResponse(
            recommendations=[
                self._recommended_service(service)
                for service in services
            ]
        )

    async def answer_faq(
        self,
        request: FAQRequest,
    ) -> FAQResponse:
        """Answer common platform questions."""
        question = request.question.strip().lower()

        if any(word in question for word in ("cancel", "cancellation")):
            return FAQResponse(
                answer=(
                    "Open your booking history, select an eligible booking "
                    "and use the cancel action. Completed or rejected "
                    "bookings cannot be cancelled."
                ),
                matched_topic="booking_cancellation",
                suggested_actions=["View booking history"],
            )

        if any(word in question for word in ("provider", "become", "professional")):
            return FAQResponse(
                answer=(
                    "Create an account and submit the Become a Provider form. "
                    "An administrator must verify the application before "
                    "provider features become available."
                ),
                matched_topic="become_provider",
                suggested_actions=["Apply to become a provider"],
            )

        if any(word in question for word in ("password", "forgot", "reset")):
            return FAQResponse(
                answer=(
                    "Use Forgot Password to request a reset token, then submit "
                    "that token with a new strong password."
                ),
                matched_topic="password_reset",
                suggested_actions=["Reset password"],
            )

        if any(word in question for word in ("book", "appointment", "schedule")):
            return FAQResponse(
                answer=(
                    "Choose an active service, select an available date and "
                    "start time, enter the location, then send the booking request."
                ),
                matched_topic="create_booking",
                suggested_actions=["Browse services", "Get booking assistance"],
            )

        if any(word in question for word in ("payment", "price", "cost")):
            return FAQResponse(
                answer=(
                    "Prices are displayed on each service. You can search by "
                    "budget or compare services before creating a booking."
                ),
                matched_topic="service_pricing",
                suggested_actions=["Compare services"],
            )

        return FAQResponse(
            answer=(
                "I could not match that question to a common topic. "
                "You can ask about bookings, providers, passwords, pricing "
                "or account management."
            ),
            matched_topic="general",
            suggested_actions=["Chat with the assistant"],
        )

    async def booking_assistance(
        self,
        request: BookingAssistanceRequest,
    ) -> BookingAssistanceResponse:
        """Guide a user through the booking process."""
        service_id = request.service_id

        if service_id is not None:
            services = await self.ai.get_services_by_ids([service_id])

            if not services:
                return BookingAssistanceResponse(
                    response="That service does not exist or is inactive.",
                    service_id=service_id,
                    next_steps=["Search for another service"],
                )

            service = services[0]
            response = (
                f"You selected {service.title}. To complete the booking, "
                "provide your preferred date, start time and location."
            )
        else:
            response = (
                "First choose an active service. After choosing it, provide "
                "the booking date, start time, location and optional notes."
            )

        return BookingAssistanceResponse(
            response=response,
            service_id=service_id,
            required_information=[
                "service_id",
                "scheduled_date",
                "scheduled_start",
                "location",
            ],
            next_steps=[
                "Check provider availability",
                "Submit the booking request",
                "Wait for provider acceptance",
            ],
        )

    async def compare_services(
        self,
        request: ServiceComparisonRequest,
    ) -> ServiceComparisonResponse:
        """Compare two to five active services."""
        unique_ids = list(dict.fromkeys(request.service_ids))

        services = await self.ai.get_services_by_ids(unique_ids)
        service_map = {
            service.id: service
            for service in services
        }

        ordered_services = [
            service_map[service_id]
            for service_id in unique_ids
            if service_id in service_map
        ]

        compared = [
            ComparedService(
                service_id=service.id,
                provider_id=service.provider_id,
                title=service.title,
                price=service.price,
                price_unit=(
                    service.price_unit.value
                    if hasattr(service.price_unit, "value")
                    else str(service.price_unit)
                ),
                duration_minutes=service.duration_minutes,
                is_featured=service.is_featured,
            )
            for service in ordered_services
        ]

        best_value = (
            min(ordered_services, key=lambda item: item.price)
            if ordered_services
            else None
        )

        if len(compared) < 2:
            summary = (
                "At least two valid active services are required "
                "for a useful comparison."
            )
        else:
            summary = (
                f"Compared {len(compared)} services. "
                f"{best_value.title} currently has the lowest listed price."
            )

        return ServiceComparisonResponse(
            services=compared,
            summary=summary,
            best_value_service_id=(
                best_value.id
                if best_value is not None
                else None
            ),
        )

    async def personalized_suggestions(
        self,
        user: User,
    ) -> PersonalizedSuggestionResponse:
        """Suggest services and providers from booking history."""
        categories = await self.ai.preferred_categories(user.id)

        preferred_category = (
            categories[0]
            if categories
            else None
        )

        services = await self.ai.search_services(
            category=preferred_category,
            limit=5,
        )
        providers = await self.ai.list_providers(
            category=preferred_category,
            limit=5,
        )

        message = (
            "Suggestions were generated from your booking history."
            if categories
            else "These are popular options for a new user."
        )

        return PersonalizedSuggestionResponse(
            preferred_categories=categories,
            service_recommendations=[
                self._recommended_service(service)
                for service in services
            ],
            provider_recommendations=[
                self._recommended_provider(provider)
                for provider in providers
            ],
            message=message,
        )

    async def market_trends(self) -> dict:
        """Return category demand trends from booking aggregates."""
        rows = (
            await self.db.execute(
                select(
                    Provider.category,
                    func.count(Booking.id).label("booking_count"),
                    func.avg(Booking.total_price).label(
                        "average_price"
                    ),
                )
                .join(
                    Booking,
                    Booking.provider_id == Provider.id,
                )
                .group_by(Provider.category)
                .order_by(func.count(Booking.id).desc())
            )
        ).all()

        trends = [
            {
                "category": category,
                "demand_level": (
                    "High"
                    if booking_count > 10
                    else "Moderate"
                ),
                "booking_count": booking_count,
                "average_price": (
                    float(average_price)
                    if average_price is not None
                    else 0.0
                ),
            }
            for category, booking_count, average_price in rows
        ]

        if not trends:
            trends = [
                {
                    "category": "Plumbing",
                    "demand_level": "High",
                    "booking_count": 0,
                    "average_price": 75.0,
                },
                {
                    "category": "Cleaning",
                    "demand_level": "High",
                    "booking_count": 0,
                    "average_price": 35.0,
                },
                {
                    "category": "Electrical",
                    "demand_level": "Moderate",
                    "booking_count": 0,
                    "average_price": 90.0,
                },
            ]

        return {
            "insights": (
                "Demand levels are calculated from platform booking history."
            ),
            "category_trends": trends,
        }

    async def search_providers(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        min_rate: Optional[float] = None,
        max_rate: Optional[float] = None,
    ):
        """Search providers using natural-language filters."""
        return await self.providers.search(
            query=query,
            category=category,
            min_rate=min_rate,
            max_rate=max_rate,
        )