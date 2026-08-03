"""Uniform response envelopes.

All JSON responses use the same shape so the frontend and other API consumers
can rely on a single contract. ``success`` + ``message`` always present; the
payload lives under ``data`` for successful responses.
"""
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class StandardResponse(BaseModel):
    """Generic envelope returned by every endpoint."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None


def success_response(
    data: Any = None,
    message: str = "OK",
    **extra: Any,
) -> dict:
    """Build a successful response body."""
    body: dict[str, Any] = {"success": True, "message": message, "data": data}
    body.update(extra)
    return body


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: Optional[Any] = None,
    success: bool = False,
) -> dict:
    """Build an error response body with a machine-readable ``code``."""
    return {
        "success": success,
        "code": code,
        "message": message,
        "details": details,
        "status_code": status_code,
    }


class MessageResponse(BaseModel):
    """Small success envelope for non-payload actions (e.g. deletes)."""

    success: bool = True
    message: str = Field(default="OK")
    data: Optional[Any] = None
