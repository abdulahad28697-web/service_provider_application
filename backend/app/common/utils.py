"""Small, dependency-free helpers shared across modules."""
import re
import uuid
from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """Return the current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def slugify(text: str) -> str:
    """Convert arbitrary text to a URL-safe slug.

    Example: ``"House Cleaning & Repair" -> "house-cleaning-repair"``
    """
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def generate_public_id(prefix: str = "") -> str:
    """Return a short, unguessable public id (used for booking reference codes)."""
    suffix = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{suffix}" if prefix else suffix


def coerce_bool(value) -> Optional[bool]:
    """Coerce common truthy/falsy representations into a bool, else None."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).lower() in {"1", "true", "yes", "on"}
