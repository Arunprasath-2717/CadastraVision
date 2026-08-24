"""
app/core/errors.py
───────────────────
RFC 9457 Problem Details for HTTP APIs — exception classes and
FastAPI exception handlers.

Usage in route handlers:
    raise NotFoundError("Parcel", parcel_id)
    raise ValidationError("Invalid file type", instance="/v1/imagery/upload")

Register the handlers in main.py:
    from app.core.errors import register_exception_handlers
    register_exception_handlers(app)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# ── RFC 9457 base type URI prefix ─────────────────────────────────────────────
_BASE_TYPE = "https://cadastravision.io/errors"


def _problem(
    status_code: int,
    title: str,
    detail: str,
    type_slug: str,
    instance: str | None = None,
    **extra: Any,
) -> dict:
    body: dict[str, Any] = {
        "type": f"{_BASE_TYPE}/{type_slug}",
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        body["instance"] = instance
    body.update(extra)
    return body


# ── Exception hierarchy ───────────────────────────────────────────────────────

class CadastraVisionError(Exception):
    """Base class for all application errors."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    title: str = "Internal Server Error"
    type_slug: str = "internal-error"

    def __init__(self, detail: str, instance: str | None = None, **extra: Any):
        self.detail = detail
        self.instance = instance
        self.extra = extra
        super().__init__(detail)

    def to_problem(self) -> dict:
        return _problem(
            self.status_code,
            self.title,
            self.detail,
            self.type_slug,
            self.instance,
            **self.extra,
        )


class NotFoundError(CadastraVisionError):
    """Resource not found — 404."""
    status_code = status.HTTP_404_NOT_FOUND
    title = "Not Found"
    type_slug = "not-found"

    def __init__(self, resource_or_detail: str = "Resource", resource_id: str | None = None, instance: str | None = None, detail: str | None = None):
        if detail:
            msg = detail
        elif resource_id:
            msg = f"{resource_or_detail} '{resource_id}' was not found."
        else:
            msg = resource_or_detail
        super().__init__(detail=msg, instance=instance)



class ConflictError(CadastraVisionError):
    """Resource conflict — 409."""
    status_code = status.HTTP_409_CONFLICT
    title = "Conflict"
    type_slug = "conflict"


class UnprocessableError(CadastraVisionError):
    """Business rule violation — 422."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    title = "Unprocessable Entity"
    type_slug = "unprocessable"


class InvalidTransitionError(CadastraVisionError):
    """Invalid workflow state transition — 422."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    title = "Invalid State Transition"
    type_slug = "invalid-transition"


class AuthenticationError(CadastraVisionError):
    """Authentication failed — 401."""
    status_code = status.HTTP_401_UNAUTHORIZED
    title = "Unauthorized"
    type_slug = "unauthorized"


class PermissionError(CadastraVisionError):  # noqa: A001
    """Authorization failed — 403."""
    status_code = status.HTTP_403_FORBIDDEN
    title = "Forbidden"
    type_slug = "forbidden"


class BadRequestError(CadastraVisionError):
    """Malformed request — 400."""
    status_code = status.HTTP_400_BAD_REQUEST
    title = "Bad Request"
    type_slug = "bad-request"


class ValidationError(BadRequestError):
    """Validation failed — 400."""
    title = "Validation Error"
    type_slug = "validation-error"


class SyncConflictError(CadastraVisionError):
    """Offline sync action conflicts with server state — 409."""
    status_code = status.HTTP_409_CONFLICT
    title = "Sync Conflict"
    type_slug = "sync-conflict"


# ── FastAPI exception handlers ─────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Register all application-level exception handlers on the FastAPI app."""

    @app.exception_handler(CadastraVisionError)
    async def _app_error_handler(
        request: Request, exc: CadastraVisionError
    ) -> JSONResponse:
        if exc.status_code >= 500:
            logger.exception("Application error on %s %s", request.method, request.url)
        else:
            logger.warning(
                "%s on %s %s: %s",
                type(exc).__name__,
                request.method,
                request.url,
                exc.detail,
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_problem(),
            headers={"Content-Type": "application/problem+json"},
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_problem(
                500,
                "Internal Server Error",
                "An unexpected error occurred. Please try again.",
                "internal-error",
                str(request.url),
            ),
            headers={"Content-Type": "application/problem+json"},
        )
