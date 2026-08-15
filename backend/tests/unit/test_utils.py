"""Unit tests for ``app.common.utils`` helpers."""
from app.common.utils import (
    coerce_bool,
    generate_public_id,
    generate_unique_slug,
    slugify,
)


async def test_slugify_basic():
    assert slugify("House Cleaning & Repair") == "house-cleaning-repair"


async def test_slugify_handles_extra_punctuation_and_whitespace():
    assert slugify("  ---Hello!! World---  ") == "hello-world"


async def test_slugify_handles_already_clean_text():
    assert slugify("already-clean") == "already-clean"


async def test_generate_unique_slug_returns_base_when_free():
    """Bare slug is used when nothing exists yet."""

    async def exists(_: str) -> bool:
        return False

    assert (
        await generate_unique_slug("deep-clean", exists)
        == "deep-clean"
    )


async def test_generate_unique_slug_uses_base_when_free_even_with_suffix():
    """When the bare slug is free, suffix is NOT applied."""

    taken: set[str] = set()

    async def exists(slug: str) -> bool:
        return slug in taken

    # Nothing exists yet - the suffix should be ignored
    assert (
        await generate_unique_slug(
            "new-service", exists, suffix="42"
        )
        == "new-service"
    )


async def test_generate_unique_slug_falls_back_to_suffix():
    """When the bare slug is taken, fall back to base-suffix."""

    taken: set[str] = {"deep-clean"}

    async def exists(slug: str) -> bool:
        return slug in taken

    assert (
        await generate_unique_slug(
            "deep-clean", exists, suffix="1"
        )
        == "deep-clean-1"
    )


async def test_generate_unique_slug_appends_counter_after_suffix():
    """When both bare and suffixed forms collide, append a counter."""

    taken: set[str] = {"deep-clean", "deep-clean-1"}

    async def exists(slug: str) -> bool:
        return slug in taken

    assert (
        await generate_unique_slug(
            "deep-clean", exists, suffix="1"
        )
        == "deep-clean-1-2"
    )


async def test_generate_unique_slug_counter_skips_taken_slots():
    """Counter must skip any pre-existing numbered variants."""

    taken: set[str] = {
        "deep-clean",
        "deep-clean-1",
        "deep-clean-1-2",
        "deep-clean-1-3",
    }

    async def exists(slug: str) -> bool:
        return slug in taken

    assert (
        await generate_unique_slug(
            "deep-clean", exists, suffix="1"
        )
        == "deep-clean-1-4"
    )


async def test_generate_unique_slug_uses_counter_when_no_suffix():
    """Without a suffix, counter is appended to the bare slug."""

    taken: set[str] = {"deep-clean"}

    async def exists(slug: str) -> bool:
        return slug in taken

    assert (
        await generate_unique_slug("deep-clean", exists)
        == "deep-clean-2"
    )


def test_generate_public_id_format():
    pid = generate_public_id()
    assert len(pid) == 8
    assert pid == pid.upper()


def test_generate_public_id_with_prefix():
    pid = generate_public_id("BK-")
    assert pid.startswith("BK-")
    assert len(pid) == 11  # prefix + 8 chars


def test_coerce_bool_truthy_strings():
    for value in ("1", "true", "yes", "on", "TRUE", "Yes"):
        assert coerce_bool(value) is True


def test_coerce_bool_falsy_strings():
    for value in ("0", "false", "no", "off", "anything-else"):
        assert coerce_bool(value) is False


def test_coerce_bool_none_returns_none():
    assert coerce_bool(None) is None


def test_coerce_bool_passes_through_booleans():
    assert coerce_bool(True) is True
    assert coerce_bool(False) is False


def test_coerce_bool_coerces_numbers():
    assert coerce_bool(1) is True
    assert coerce_bool(0) is False
    assert coerce_bool(0.0) is False