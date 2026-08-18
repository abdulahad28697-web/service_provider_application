"""Domain exceptions and their FastAPI exception handlers.

Modules raise the semantic exceptions below; a central handler maps each to the
appropriate HTTP status + a consistent JSON body so controllers stay thin.
"""
import logging
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.responses import error_response

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for all domain errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "error"
    message: str = "An error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> None:
        self.message = message or self.message
        self.code = code or self.code
        self.details = details
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"


def _build_payload(status_code: int, code: str, message: str, details=None) -> dict:
    """Build a uniform error envelope."""
    return error_response(
        success=False,
        code=code,
        message=message,
        details=details,
        status_code=status_code,
    )


def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(
        "%s %s failed: %s (%s)",
        request.method,
        request.url.path,
        exc.message,
        exc.code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_build_payload(exc.status_code, exc.code, exc.message, exc.details),
    )


def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    details = []
    for err in errors:
        loc = ".".join(str(part) for part in err.get("loc", []) if part != "body")
        details.append({"field": loc, "message": err.get("msg")})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_build_payload(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            "Request validation failed.",
            details,
        ),
    )


def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Log an unhandled error and keep the uniform response envelope."""
    logger.exception(
        "Unhandled error on %s %s.",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_build_payload(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "An unexpected error occurred. Please try again.",
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all domain exception handlers to a FastAPI instance."""
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
