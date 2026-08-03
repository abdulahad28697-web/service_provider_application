from pydantic import BaseModel

class ChatbotMessageRequest(BaseModel):
    message: str
    session_id: str | None = None

class RecommendationRequest(BaseModel):
    query: str
    category: str | None = None
    max_price: float | None = None
    limit: int = 5
