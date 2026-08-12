"""Business logic for notifications."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.notification import Notification
from app.models.user import User


class NotificationService:
    """Notification creation and management."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def create(
        self,
        *,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "general",
        reference_id: int | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            reference_id=reference_id,
            is_read=False,
        )

        self.db.add(notification)

        await self.db.flush()

        return notification

    async def list_for_user(
        self,
        user: User,
    ):
        result = await self.db.execute(
            select(Notification)
            .where(
                Notification.user_id == user.id
            )
            .order_by(
                Notification.created_at.desc()
            )
        )

        return result.scalars().all()

    async def mark_read(
        self,
        user: User,
        notification_id: int,
    ) -> Notification:
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user.id,
            )
        )

        notification = (
            result.scalar_one_or_none()
        )

        if notification is None:
            raise NotFoundError(
                "Notification not found."
            )

        notification.is_read = True

        await self.db.commit()
        await self.db.refresh(
            notification
        )

        return notification

    async def mark_all_read(
        self,
        user: User,
    ) -> None:
        notifications = await self.list_for_user(
            user
        )

        for notification in notifications:
            notification.is_read = True

        await self.db.commit()