from pydantic import BaseModel
from datetime import datetime

class DashboardRangeRequest(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
