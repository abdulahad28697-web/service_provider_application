"""Shared enums and domain constants.

Enums that span multiple modules (roles, booking lifecycle) live here so no
single module owns them. Module-specific enums may still be defined locally
where it makes the code clearer.
"""
from enum import Enum


class UserRole(str, Enum):
    """User roles supported by the platform."""

    CUSTOMER = "customer"
    PROVIDER = "provider"
    ADMIN = "admin"


class BookingStatus(str, Enum):
    """Lifecycle of a booking."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Valid one-step transitions for BookingStatus. Guards the state machine in the
# bookings service so bookings cannot skip states or move backwards.
BOOKING_STATUS_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING: {
        BookingStatus.ACCEPTED,
        BookingStatus.REJECTED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.ACCEPTED: {BookingStatus.COMPLETED, BookingStatus.CANCELLED},
    BookingStatus.REJECTED: set(),
    BookingStatus.COMPLETED: set(),
    BookingStatus.CANCELLED: set(),
}


class PriceUnit(str, Enum):
    """Unit the service price is denominated in."""

    PER_HOUR = "per_hour"
    PER_VISIT = "per_visit"
    FIXED = "fixed"


class DayOfWeek(str, Enum):
    """Provider schedule days. ISO ordering: Monday = 0 ... Sunday = 6."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


# Map a Python weekday (Monday=0) to the DayOfWeek enum value.
DAY_OF_WEEK_FROM_ISO: dict[int, DayOfWeek] = {
    0: DayOfWeek.MONDAY,
    1: DayOfWeek.TUESDAY,
    2: DayOfWeek.WEDNESDAY,
    3: DayOfWeek.THURSDAY,
    4: DayOfWeek.FRIDAY,
    5: DayOfWeek.SATURDAY,
    6: DayOfWeek.SUNDAY,
}
