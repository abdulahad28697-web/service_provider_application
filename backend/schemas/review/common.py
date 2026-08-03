from pydantic import BaseModel, Field

class ReviewBase(BaseModel):
    booking_id: int
    rating: float = Field(..., ge=1.0, le=5.0, description="Rating must be between 1.0 and 5.0")
    comment: str | None = None
