from pydantic import BaseModel
from datetime import datetime
from schemas.review.common import ReviewBase

class ReviewResponse(ReviewBase):
    id: int
    client_id: int
    created_at: datetime

    class Config:
        from_attributes = True
