"""HTTP endpoints for booking-based messaging."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import (
    StandardResponse,
    success_response,
)
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.message import (
    ConversationRead,
    MessageCreate,
    MessageRead,
)
from app.services.message_service import MessageService


router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
)


def _service(
    db: AsyncSession = Depends(get_db),
) -> MessageService:
    """Create a MessageService for the current request."""

    return MessageService(db)


# ============================================================
# INBOX
# ============================================================


@router.get(
    "",
    response_model=StandardResponse,
    summary="List my booking conversations",
)
async def list_conversations(
    user: User = Depends(get_current_user),
    service: MessageService = Depends(_service),
):
    conversations = await service.inbox(
        user=user,
    )

    return success_response(
        data=[
            ConversationRead.model_validate(
                conversation
            )
            for conversation in conversations
        ],
        message="Conversations fetched.",
    )


# ============================================================
# UNREAD COUNT
#
# IMPORTANT:
# Keep this static route before /{booking_id}
# ============================================================


@router.get(
    "/unread-count",
    response_model=StandardResponse,
    summary="Get unread message count",
)
async def unread_message_count(
    user: User = Depends(get_current_user),
    service: MessageService = Depends(_service),
):
    count = await service.unread_count(
        user=user,
    )

    return success_response(
        data={
            "unread_count": count,
        },
        message="Unread message count fetched.",
    )


# ============================================================
# CONVERSATION HISTORY
# ============================================================


@router.get(
    "/{booking_id}",
    response_model=StandardResponse,
    summary="Get messages for a booking",
)
async def get_conversation(
    booking_id: int,
    user: User = Depends(get_current_user),
    service: MessageService = Depends(_service),
):
    messages = await service.conversation(
        booking_id=booking_id,
        user=user,
    )

    return success_response(
        data=[
            MessageRead.model_validate(
                message
            )
            for message in messages
        ],
        message="Conversation fetched.",
    )


# ============================================================
# SEND MESSAGE
# ============================================================


@router.post(
    "/{booking_id}",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message for a booking",
)
async def send_message(
    booking_id: int,
    payload: MessageCreate,
    user: User = Depends(get_current_user),
    service: MessageService = Depends(_service),
):
    message = await service.send(
        booking_id=booking_id,
        user=user,
        data=payload,
    )

    return success_response(
        data=MessageRead.model_validate(
            message
        ),
        message="Message sent.",
    )