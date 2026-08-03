"""HTTP endpoints for bookings and provider schedules.

NOTE: schedule routes are declared *before* the ``/{booking_id}`` routes so the
literal path ``/bookings/schedules`` is matched before ``/bookings/{booking_id}``.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import BookingStatus
from app.common.pagination import PageParams
from app.common.responses import MessageResponse, StandardResponse, success_response
from app.core.permissions import require_customer, require_provider
from app.database.session import get_db
from app.models.user import User
from app.schemas.booking import (
    BookingAction,
    BookingCreate,
    BookingCreateResponse,
    BookingPage,
    BookingRead,
)
from app.schemas.schedule import (
    ScheduleSlot,
    ScheduleSlotRead,
    ScheduleSlotUpdate,
)
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def _service(db: AsyncSession = Depends(get_db)) -> BookingService:
    """Build a :class:`BookingService` bound to the request session."""
    return BookingService(db)


# --------------------------------------------------------------------------- #
# Provider schedule management
# --------------------------------------------------------------------------- #
@router.put(
    "/schedules",
    response_model=StandardResponse,
    summary="Create or update a weekly availability slot (provider)",
)
async def upsert_schedule(
    slot: ScheduleSlot,
    service: BookingService = Depends(_service),
    _provider: User = Depends(require_provider),
):
    schedule = await service.upsert_schedule(_provider, slot)
    return success_response(
        data=ScheduleSlotRead.model_validate(schedule), message="Schedule saved."
    )


@router.get(
    "/schedules",
    response_model=StandardResponse,
    summary="List my weekly availability (provider)",
)
async def list_schedules(
    service: BookingService = Depends(_service),
    _provider: User = Depends(require_provider),
):
    schedules = await service.list_schedules(_provider)
    return success_response(data=schedules, message="Schedules fetched.")


@router.patch(
    "/schedules/{schedule_id}",
    response_model=StandardResponse,
    summary="Update an availability slot (provider)",
)
async def update_schedule(
    schedule_id: int,
    payload: ScheduleSlotUpdate,
    service: BookingService = Depends(_service),
    _provider: User = Depends(require_provider),
):
    schedule = await service.update_schedule(_provider, schedule_id, payload)
    return success_response(
        data=ScheduleSlotRead.model_validate(schedule), message="Schedule updated."
    )


@router.delete(
    "/schedules/{schedule_id}",
    response_model=MessageResponse,
    summary="Delete an availability slot (provider)",
)
async def delete_schedule(
    schedule_id: int,
    service: BookingService = Depends(_service),
    _provider: User = Depends(require_provider),
):
    await service.delete_schedule(_provider, schedule_id)
    return MessageResponse(message="Schedule deleted.", data=None)


# --------------------------------------------------------------------------- #
# Booking lifecycle
# --------------------------------------------------------------------------- #
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
    booking = await service.book(customer, payload)
    data = BookingCreateResponse.model_validate(booking)
    data.message = "Booking request sent to the provider."
    return success_response(data=data, message="Booking created.")


@router.get(
    "",
    response_model=StandardResponse,
    summary="Booking history for the current user",
)
async def booking_history(
    params: PageParams = Depends(),
    as_provider: Optional[bool] = Query(
        default=None, description="Set true/false to view as provider/customer."
    ),
    status: Optional[BookingStatus] = Query(default=None),
    service: BookingService = Depends(_service),
    user: User = Depends(require_customer),
):
    page = await service.list_history(
        user, params, as_provider=as_provider, status=status
    )
    return success_response(
        data=BookingPage.model_validate(page), message="Bookings fetched."
    )


@router.get(
    "/{booking_id}",
    response_model=StandardResponse,
    summary="Get a booking (participant only)",
)
async def get_booking(
    booking_id: int,
    service: BookingService = Depends(_service),
    user: User = Depends(require_customer),
):
    booking = await service.get(booking_id, user)
    return success_response(
        data=BookingRead.model_validate(booking), message="Booking fetched."
    )


@router.post(
    "/{booking_id}/accept",
    response_model=StandardResponse,
    summary="Accept a booking (provider)",
)
async def accept_booking(
    booking_id: int,
    service: BookingService = Depends(_service),
    provider: User = Depends(require_provider),
):
    booking = await service.accept(booking_id, provider)
    return success_response(
        data=BookingRead.model_validate(booking), message="Booking accepted."
    )


@router.post(
    "/{booking_id}/reject",
    response_model=StandardResponse,
    summary="Reject a booking (provider)",
)
async def reject_booking(
    booking_id: int,
    payload: BookingAction = None,
    service: BookingService = Depends(_service),
    provider: User = Depends(require_provider),
):
    booking = await service.reject(booking_id, provider, payload.reason if payload else None)
    return success_response(
        data=BookingRead.model_validate(booking), message="Booking rejected."
    )


@router.post(
    "/{booking_id}/complete",
    response_model=StandardResponse,
    summary="Complete a booking (provider)",
)
async def complete_booking(
    booking_id: int,
    service: BookingService = Depends(_service),
    provider: User = Depends(require_provider),
):
    booking = await service.complete(booking_id, provider)
    return success_response(
        data=BookingRead.model_validate(booking), message="Booking completed."
    )


@router.post(
    "/{booking_id}/cancel",
    response_model=StandardResponse,
    summary="Cancel a booking (customer or provider)",
)
async def cancel_booking(
    booking_id: int,
    payload: BookingAction = None,
    service: BookingService = Depends(_service),
    user: User = Depends(require_customer),
):
    booking = await service.cancel(
        booking_id, user, payload.reason if payload else None
    )
    return success_response(
        data=BookingRead.model_validate(booking), message="Booking cancelled."
    )
