from sqlalchemy.orm import Session
from schemas.ai.request import ChatbotMessageRequest
from schemas.ai.response import ChatbotResponse
from repositories.ai.ai_repository import AIRepository

class ChatbotService:
    def __init__(self, db: Session):
        self.ai_repo = AIRepository(db)

    def process_message(self, request: ChatbotMessageRequest) -> ChatbotResponse:
        msg = request.message.lower()
        suggested_actions = ["Ask about providers", "Get price estimates", "Book a service"]
        
        if "plumber" in msg or "plumbing" in msg:
            providers = self.ai_repo.search_providers_by_keyword("plumbing", limit=2)
            if providers:
                names = ", ".join([p.business_name or "Unnamed Provider" for p in providers])
                response = f"I found some plumbing providers for you: {names}. Would you like me to show their details?"
                suggested_actions = [f"View details for {providers[0].business_name}", "Search other categories"]
            else:
                response = "I couldn't find any plumbing service providers available right now."
        elif "price" in msg or "cost" in msg:
            response = "Standard hourly rates for our top service providers range from $20 to $150 depending on experience and category. Would you like a list of affordable options?"
            suggested_actions = ["Show services under $50", "Show top rated providers"]
        elif "book" in msg:
            response = "Sure, I can help you schedule a booking. Please specify the service category or provider you would like to book."
            suggested_actions = ["View all services", "Talk to support"]
        else:
            response = "Hello! I am your AI Service Assistant. How can I help you today? You can ask me to find service providers, check pricing, or help with bookings."

        return ChatbotResponse(response=response, suggested_actions=suggested_actions)
