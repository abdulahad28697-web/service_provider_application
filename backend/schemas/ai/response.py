from pydantic import BaseModel
from typing import List
from schemas.admin.response import ProviderResponse

class ChatbotResponse(BaseModel):
    response: str
    suggested_actions: List[str] = []

class RecommendedProvider(BaseModel):
    provider_id: int
    business_name: str | None
    category: str
    hourly_rate: float
    rating: float
    reason: str  # Why this provider was recommended by AI

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendedProvider]
