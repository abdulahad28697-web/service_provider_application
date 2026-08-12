"""Notification Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    """Notification returned to the frontend."""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    reference_id: Optional[int]
    is_read: bool
    created_at: datetime