"""Business logic for booking conversations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenError,
    NotFoundError,
)
from app.models.booking import Booking
from app.models.provider import Provider
from app.models.user import User
from app.repositories.booking_repository import (
    BookingRepository,
)
from app.repositories.message_repository import (
    MessageRepository,
)
from app.repositories.provider_repository import (
    ProviderRepository,
)
from app.schemas.message import (
    ConversationRead,
    MessageCreate,
    MessageRead,
)


class MessageService:
    """Handle secure booking-based messaging."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

        self.messages = MessageRepository(db)
        self.bookings = BookingRepository(db)
        self.providers = ProviderRepository(db)


    # =========================================================
    # SEND MESSAGE
    # =========================================================

    async def send(
        self,
        *,
        booking_id: int,
        user: User,
        data: MessageCreate,
    ) -> MessageRead:
        """Send a message inside a booking conversation."""

        booking = await self.bookings.get(
            booking_id
        )

        if booking is None:
            raise NotFoundError(
                "Booking not found."
            )

        receiver_id = await self._resolve_receiver(
            booking=booking,
            user=user,
        )

        message = await self.messages.create(
            booking_id=booking.id,
            sender_id=user.id,
            receiver_id=receiver_id,
            content=data.content.strip(),
        )

        await self.db.commit()
        await self.db.refresh(message)

        return MessageRead.model_validate(
            message
        )


    # =========================================================
    # CONVERSATION HISTORY
    # =========================================================

    async def conversation(
        self,
        *,
        booking_id: int,
        user: User,
    ) -> list[MessageRead]:
        """Return all messages for a booking."""

        booking = await self.bookings.get(
            booking_id
        )

        if booking is None:
            raise NotFoundError(
                "Booking not found."
            )

        await self._assert_participant(
            booking=booking,
            user=user,
        )

        rows = await self.messages.list_for_booking(
            booking_id=booking.id,
        )

        await self.messages.mark_booking_read(
            booking_id=booking.id,
            user_id=user.id,
        )

        await self.db.commit()

        return [
            MessageRead.model_validate(
                message
            )
            for message in rows
        ]


    # =========================================================
    # INBOX / CONVERSATION SUMMARIES
    # =========================================================

    async def inbox(
        self,
        *,
        user: User,
    ) -> list[ConversationRead]:
        """Return booking conversations visible to the user."""

        messages = await self.messages.list_for_user(
            user_id=user.id,
        )

        booking_ids = []

        for message in messages:
            if (
                message.booking_id
                not in booking_ids
            ):
                booking_ids.append(
                    message.booking_id
                )

        conversations = []

        for booking_id in booking_ids:
            booking = await self.bookings.get(
                booking_id
            )

            if booking is None:
                continue

            try:
                other_user = await self._get_other_user(
                    booking=booking,
                    user=user,
                )
            except ForbiddenError:
                continue

            latest = await self.messages.latest_for_booking(
                booking_id=booking.id,
            )

            unread = (
                await self.messages.unread_count_for_booking(
                    booking_id=booking.id,
                    user_id=user.id,
                )
            )

            conversations.append(
                ConversationRead(
                    booking_id=booking.id,
                    reference_code=booking.reference_code,
                    service_title=booking.service_title,
                    other_user_id=other_user.id,
                    other_user_name=other_user.full_name,
                    latest_message=(
                        latest.content
                        if latest is not None
                        else None
                    ),
                    latest_message_at=(
                        latest.created_at
                        if latest is not None
                        else None
                    ),
                    unread_count=unread,
                )
            )

        conversations.sort(
            key=lambda item: (
                item.latest_message_at
                is not None,
                item.latest_message_at,
            ),
            reverse=True,
        )

        return conversations


    # =========================================================
    # TOTAL UNREAD COUNT
    # =========================================================

    async def unread_count(
        self,
        *,
        user: User,
    ) -> int:
        """Return unread message count for current user."""

        return await self.messages.unread_count(
            user_id=user.id,
        )


    # =========================================================
    # PARTICIPANT SECURITY
    # =========================================================

    async def _assert_participant(
        self,
        *,
        booking: Booking,
        user: User,
    ) -> None:
        """Ensure current user belongs to this booking."""

        if booking.customer_id == user.id:
            return

        provider = (
            await self.providers.get_by_user_id(
                user.id
            )
        )

        if (
            provider is not None
            and provider.id
            == booking.provider_id
        ):
            return

        if user.role.value == "admin":
            return

        raise ForbiddenError(
            "You are not allowed to access this conversation."
        )


    # =========================================================
    # RECEIVER RESOLUTION
    # =========================================================

    async def _resolve_receiver(
        self,
        *,
        booking: Booking,
        user: User,
    ) -> int:
        """
        Determine who should receive the message.

        Customer -> provider
        Provider -> customer
        """

        if booking.customer_id == user.id:
            provider = await self.providers.get(
                booking.provider_id
            )

            if provider is None:
                raise NotFoundError(
                    "Provider not found."
                )

            return provider.user_id

        provider = (
            await self.providers.get_by_user_id(
                user.id
            )
        )

        if (
            provider is not None
            and provider.id
            == booking.provider_id
        ):
            return booking.customer_id

        raise ForbiddenError(
            "You are not allowed to send messages for this booking."
        )


    # =========================================================
    # OTHER USER
    # =========================================================

    async def _get_other_user(
        self,
        *,
        booking: Booking,
        user: User,
    ) -> User:
        """Return the other booking participant."""

        if booking.customer_id == user.id:
            provider = await self.providers.get(
                booking.provider_id
            )

            if provider is None:
                raise NotFoundError(
                    "Provider not found."
                )

            result = await self.db.execute(
                select(User).where(
                    User.id == provider.user_id
                )
            )

            other_user = (
                result.scalar_one_or_none()
            )

            if other_user is None:
                raise NotFoundError(
                    "Provider user not found."
                )

            return other_user

        provider = (
            await self.providers.get_by_user_id(
                user.id
            )
        )

        if (
            provider is not None
            and provider.id
            == booking.provider_id
        ):
            result = await self.db.execute(
                select(User).where(
                    User.id == booking.customer_id
                )
            )

            other_user = (
                result.scalar_one_or_none()
            )

            if other_user is None:
                raise NotFoundError(
                    "Customer not found."
                )

            return other_user

        raise ForbiddenError(
            "You are not allowed to access this conversation."
        )