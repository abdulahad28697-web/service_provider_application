"""HTTP endpoints for bookings and provider schedules.

Schedule routes are declared before /{booking_id} routes so
/bookings/schedules is matched before /bookings/{booking_id}.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import BookingStatus
from app.common.pagination import PageParams
from app.common.responses import (
    MessageResponse,
    StandardResponse,
    success_response,
)
from app.core.dependencies import get_current_user
from app.core.permissions import (
    require_customer,
    require_provider,
)
from app.database.session import get_db
from app.models.user import User
from app.schemas.booking import (
    BookingAction,
    BookingCreate,
    BookingCreateResponse,
    BookingPage,
    BookingRead,
    BookingReschedule,
)
from app.schemas.schedule import (
    ScheduleSlot,
    ScheduleSlotRead,
    ScheduleSlotUpdate,
)
from app.services.booking_service import BookingService


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
)


def _service(
    db: AsyncSession = Depends(get_db),
) -> BookingService:
    """Build BookingService for the current request."""

    return BookingService(db)


# ============================================================
# PROVIDER SCHEDULE
# ============================================================


@router.put(
    "/schedules",
    response_model=StandardResponse,
    summary="Create or update provider availability",
)
async def upsert_schedule(
    slot: ScheduleSlot,
    service: BookingService = Depends(_service),
    provider: User = Depends(require_provider),
):
    schedule = await service.upsert_schedule(
        provider,
        slot,
    )

    return success_response(
        data=ScheduleSlotRead.model_validate(
            schedule
        ),
        message="Schedule saved.",
    )


@router.get(
    "/schedules",
    response_model=StandardResponse,
    summary="List provider availability",
)
async def list_schedules(
    service: BookingService = Depends(_service),
    provider: User = Depends(require_provider),
):
    schedules = await service.list_schedules(
        provider
    )

    return success_response(
        data=schedules,
        message="Schedules fetched.",
    )


@router.patch(
    "/schedules/{schedule_id}",
    response_model=StandardResponse,
    summary="Update provider availability",
)
async def update_schedule(
    schedule_id: int,
    payload: ScheduleSlotUpdate,
    service: BookingService = Depends(_service),
    provider: User = Depends(require_provider),
):
    schedule = await service.update_schedule(
        provider,
        schedule_id,
        payload,
    )

    return success_response(
        data=ScheduleSlotRead.model_validate(
            schedule
        ),
        message="Schedule updated.",
    )


@router.delete(
    "/schedules/{schedule_id}",
    response_model=MessageResponse,
    summary="Delete provider availability",
)
async def delete_schedule(
    schedule_id: int,
    service: BookingService = Depends(_service),
    provider: User = Depends(require_provider),
):
    await service.delete_schedule(
        provider,
        schedule_id,
    )

    return MessageResponse(
        message="Schedule deleted.",
        data=None,
    )


# ============================================================
# CREATE BOOKING — CUSTOMER
# ============================================================


@router.post(
    "",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a service",
)
async def create_booking(
    payload: BookingCreate,
    service: BookingService = Depends(_service),
    customer: User = Depends(require_customer),
):
    booking = await service.book(
        customer,
        payload,
    )

    data = BookingCreateResponse.model_validate(
        booking
    )

    data.message = (
        "Booking request sent to the provider."
    )

    return success_response(
        data=data,
        message="Booking created.",
    )


# ============================================================
# BOOKING HISTORY
#
# Customer -> sees customer's bookings
# Provider -> sees provider's booking requests
# ============================================================


@router.get(
    "",
    response_model=StandardResponse,
    summary="Booking history for current user",
)
async def booking_history(
    params: PageParams = Depends(),

    as_provider: Optional[bool] = Query(
        default=None,
        description=(
            "Set true to view provider bookings "
            "or false for customer bookings."
        ),
    ),

    status_filter: Optional[
        BookingStatus
    ] = Query(
        default=None,
        alias="status",
    ),

    service: BookingService = Depends(
        _service
    ),

    user: User = Depends(
        get_current_user
    ),
):
    page = await service.list_history(
        user,
        params,
        as_provider=as_provider,
        status=status_filter,
    )

    return success_response(
        data=BookingPage.model_validate(
            page
        ),
        message="Bookings fetched.",
    )


# ============================================================
# RESCHEDULE — CUSTOMER
#
# Keep action routes before /{booking_id}
# ============================================================


@router.patch(
    "/{booking_id}/reschedule",
    response_model=StandardResponse,
    summary="Reschedule a booking",
)
async def reschedule_booking(
    booking_id: int,
    payload: BookingReschedule,
    service: BookingService = Depends(_service),
    customer: User = Depends(require_customer),
):
    booking = await service.reschedule(
        booking_id,
        customer,
        payload,
    )

    return success_response(
        data=BookingRead.model_validate(
            booking
        ),
        message="Booking rescheduled successfully.",
    )


# ============================================================
# ACCEPT — PROVIDER
# ============================================================


@router.post(
    "/{booking_id}/accept",
    response_model=StandardResponse,
    summary="Accept booking request",
)
async def accept_booking(
    booking_id: int,
    service: BookingService = Depends(_service),
    provider: User = Depends(require_provider),
):
    booking = await service.accept(
        booking_id,
        provider,
    )

    return success_response(
        data=BookingRead.model_validate(
            booking
        ),
        message="Booking accepted.",
    )


# ============================================================
# REJECT — PROVIDER
# ============================================================


@router.post(
    "/{booking_id}/reject",
    response_model=StandardResponse,
    summary="Reject booking request",
)
async def reject_booking(
    booking_id: int,
    payload: Optional[BookingAction] = None,
    service: BookingService = Depends(_service),
    provider: User = Depends(require_provider),
):
    reason = (
        payload.reason
        if payload
        else None
    )

    booking = await service.reject(
        booking_id,
        provider,
        reason,
    )

    return success_response(
        data=BookingRead.model_validate(
            booking
        ),
        message="Booking rejected.",
    )


# ============================================================
# COMPLETE — PROVIDER
# ============================================================


@router.post(
    "/{booking_id}/complete",
    response_model=StandardResponse,
    summary="Mark booking completed",
)
async def complete_booking(
    booking_id: int,
    service: BookingService = Depends(_service),
    provider: User = Depends(require_provider),
):
    booking = await service.complete(
        booking_id,
        provider,
    )

    return success_response(
        data=BookingRead.model_validate(
            booking
        ),
        message="Booking completed.",
    )


# ============================================================
# CANCEL — CUSTOMER / PROVIDER
# ============================================================


@router.post(
    "/{booking_id}/cancel",
    response_model=StandardResponse,
    summary="Cancel booking",
)
async def cancel_booking(
    booking_id: int,
    payload: Optional[BookingAction] = None,
    service: BookingService = Depends(_service),
    user: User = Depends(get_current_user),
):
    reason = (
        payload.reason
        if payload
        else None
    )

    booking = await service.cancel(
        booking_id,
        user,
        reason,
    )

    return success_response(
        data=BookingRead.model_validate(
            booking
        ),
        message="Booking cancelled.",
    )


# ============================================================
# GET ONE BOOKING
#
# Keep this after all /{booking_id}/... action routes.
# ============================================================


@router.get(
    "/{booking_id}",
    response_model=StandardResponse,
    summary="Get booking details",
)
async def get_booking(
    booking_id: int,
    service: BookingService = Depends(_service),
    user: User = Depends(get_current_user),
):
    booking = await service.get(
        booking_id,
        user,
    )

    return success_response(
        data=BookingRead.model_validate(
            booking
        ),
        message="Booking fetched.",
    )