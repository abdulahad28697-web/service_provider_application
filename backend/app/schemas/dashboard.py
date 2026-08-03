"""Admin dashboard Pydantic schemas (aggregate statistics)."""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class DashboardRange(BaseModel):
    """Optional date range to scope the dashboard statistics to."""

    start_date: Optional[date] = None
    end_date: Optional[date] = None


class BookingSummary(BaseModel):
    """A recent booking as shown on the admin dashboard."""

    id: int
    customer_name: str
    service_name: str
    price: Decimal
    status: str
    scheduled_date: date


class DashboardResponse(BaseModel):
    """Aggregate statistics for the admin dashboard."""

    total_bookings: int
    total_revenue: Decimal
    total_users: int
    total_providers: int
    average_rating: Decimal
    recent_bookings: List[BookingSummary]
