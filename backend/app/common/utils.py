"""Small, dependency-free helpers shared across modules."""
import re
import uuid
from datetime import datetime, timezone
from typing import Callable, Optional


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


async def generate_unique_slug(
    base_slug: str,
    exists_check: Callable[[str], bool],
    suffix: str = "",
) -> str:
    """Generate a unique slug by checking for collisions.

    Strategy:
      1. Try the bare base slug.
      2. If that exists and a suffix is provided, try ``base-suffix``.
      3. Otherwise append ``-2``, ``-3`` … until a free slot is found.

    The suffix is therefore a *fallback* that only kicks in when the bare
    slug is already taken, which keeps URLs clean when no collision exists.

    Args:
        base_slug: The base slug to start with (already slugified).
        exists_check: Async function returning ``True`` if a slug exists.
        suffix: Optional suffix (e.g. provider id) used only as a fallback.

    Returns:
        A unique slug string.

    Example:
        >>> async def check(slug): return slug in {"deep-clean"}
        >>> await generate_unique_slug("deep-clean", check, "1")
        "deep-clean-1"
        >>> await generate_unique_slug("new-service", check, "1")
        "new-service"
    """
    # 1. Bare base slug
    if not await exists_check(base_slug):
        return base_slug

    # 2. Fall back to base + suffix (only if a suffix was supplied)
    if suffix:
        candidate = f"{base_slug}-{suffix}"
        if not await exists_check(candidate):
            return candidate
        # 3. Append counter on top of the suffixed form
        counter = 2
        while await exists_check(f"{candidate}-{counter}"):
            counter += 1
        return f"{candidate}-{counter}"

    # 4. No suffix available - append counter to bare base slug
    counter = 2
    while await exists_check(f"{base_slug}-{counter}"):
        counter += 1
    return f"{base_slug}-{counter}"


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
