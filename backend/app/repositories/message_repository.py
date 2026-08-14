"""Data-access layer for booking messages."""

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository):
    """Queries for booking conversations and unread messages."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        super().__init__(db)


    async def create(
        self,
        *,
        booking_id: int,
        sender_id: int,
        receiver_id: int,
        content: str,
    ) -> Message:
        """Create a new message."""

        message = Message(
            booking_id=booking_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            is_read=False,
        )

        self.db.add(message)

        await self.db.flush()

        return message


    async def list_for_booking(
        self,
        *,
        booking_id: int,
    ) -> Sequence[Message]:
        """Return all messages for one booking."""

        result = await self.db.execute(
            select(Message)
            .where(
                Message.booking_id == booking_id
            )
            .order_by(
                Message.created_at.asc()
            )
        )

        return result.scalars().all()


    async def list_for_user(
        self,
        *,
        user_id: int,
    ) -> Sequence[Message]:
        """Return all messages involving a user."""

        result = await self.db.execute(
            select(Message)
            .where(
                or_(
                    Message.sender_id == user_id,
                    Message.receiver_id == user_id,
                )
            )
            .order_by(
                Message.created_at.desc()
            )
        )

        return result.scalars().all()


    async def unread_count(
        self,
        *,
        user_id: int,
    ) -> int:
        """Return total unread messages received by a user."""

        result = await self.db.execute(
            select(
                func.count(Message.id)
            ).where(
                Message.receiver_id == user_id,
                Message.is_read.is_(False),
            )
        )

        return result.scalar_one()


    async def unread_count_for_booking(
        self,
        *,
        booking_id: int,
        user_id: int,
    ) -> int:
        """Return unread count for one booking conversation."""

        result = await self.db.execute(
            select(
                func.count(Message.id)
            ).where(
                Message.booking_id == booking_id,
                Message.receiver_id == user_id,
                Message.is_read.is_(False),
            )
        )

        return result.scalar_one()


    async def latest_for_booking(
        self,
        *,
        booking_id: int,
    ) -> Message | None:
        """Return newest message in a booking conversation."""

        result = await self.db.execute(
            select(Message)
            .where(
                Message.booking_id == booking_id
            )
            .order_by(
                Message.created_at.desc()
            )
            .limit(1)
        )

        return result.scalar_one_or_none()


    async def mark_booking_read(
        self,
        *,
        booking_id: int,
        user_id: int,
    ) -> None:
        """Mark received messages in one conversation as read."""

        result = await self.db.execute(
            select(Message).where(
                Message.booking_id == booking_id,
                Message.receiver_id == user_id,
                Message.is_read.is_(False),
            )
        )

        messages = result.scalars().all()

        for message in messages:
            message.is_read = True

        await self.db.flush()


    async def get(
        self,
        message_id: int,
    ) -> Message | None:
        """Return a single message by ID."""

        result = await self.db.execute(
            select(Message).where(
                Message.id == message_id
            )
        )

        return result.scalar_one_or_none()