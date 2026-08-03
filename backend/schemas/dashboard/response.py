from pydantic import BaseModel
from typing import List

class BookingSummary(BaseModel):
    id: int
    client_name: str
    service_name: str
    price: float
    status: str
    scheduled_at: str

class DashboardResponse(BaseModel):
    total_bookings: int
    total_revenue: float
    total_users: int
    total_providers: int
    average_rating: float
    recent_bookings: List[BookingSummary]

    class Config:
        from_attributes = True
