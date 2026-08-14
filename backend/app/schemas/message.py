"""Messaging Pydantic schemas."""

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class MessageCreate(BaseModel):
    """Payload for sending a booking message."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=3000,
    )


class MessageRead(BaseModel):
    """Message returned to API consumers."""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    booking_id: int

    sender_id: int
    receiver_id: int

    content: str
    is_read: bool

    created_at: datetime


class ConversationRead(BaseModel):
    """Conversation summary for the inbox."""

    booking_id: int

    reference_code: str
    service_title: str

    other_user_id: int
    other_user_name: str

    latest_message: str | None = None
    latest_message_at: datetime | None = None

    unread_count: int = 0