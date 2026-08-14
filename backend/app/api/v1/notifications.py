"""HTTP endpoints for notifications."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import (
    StandardResponse,
    success_response,
)
from app.core.dependencies import (
    get_current_user,
)
from app.database.session import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationRead,
)
from app.services.notification_service import (
    NotificationService,
)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


def _service(
    db: AsyncSession = Depends(get_db),
) -> NotificationService:
    return NotificationService(db)


@router.get(
    "",
    response_model=StandardResponse,
    summary="List my notifications",
)
async def list_notifications(
    user: User = Depends(
        get_current_user
    ),
    service: NotificationService = Depends(
        _service
    ),
):
    notifications = (
        await service.list_for_user(
            user
        )
    )

    return success_response(
        data=[
            NotificationRead.model_validate(
                notification
            )
            for notification in notifications
        ],
        message="Notifications fetched.",
    )


@router.patch(
    "/{notification_id}/read",
    response_model=StandardResponse,
    summary="Mark notification as read",
)
async def mark_notification_read(
    notification_id: int,
    user: User = Depends(
        get_current_user
    ),
    service: NotificationService = Depends(
        _service
    ),
):
    notification = (
        await service.mark_read(
            user,
            notification_id,
        )
    )

    return success_response(
        data=NotificationRead.model_validate(
            notification
        ),
        message="Notification marked as read.",
    )


@router.patch(
    "/read-all",
    response_model=StandardResponse,
    summary="Mark all notifications as read",
)
async def mark_all_notifications_read(
    user: User = Depends(
        get_current_user
    ),
    service: NotificationService = Depends(
        _service
    ),
):
    await service.mark_all_read(
        user
    )

    return success_response(
        data=None,
        message="All notifications marked as read.",
    )