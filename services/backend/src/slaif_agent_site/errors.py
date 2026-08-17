"""Stable public application errors and secret-safe FastAPI handlers."""

from __future__ import annotations

from typing import ClassVar

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from .correlation import current_request_id
from .logging import JSONValue, redact_log_value


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{1,63}$")
    message: str = Field(min_length=1, max_length=256)
    request_id: str = Field(min_length=1, max_length=64)
    operation_id: str | None = Field(default=None, max_length=64)
    details: dict[str, JSONValue] | None = None


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    error: ErrorBody


class AppError(Exception):
    """Base class whose public code/message are fixed by trusted code."""

    code: ClassVar[str] = "APPLICATION_ERROR"
    status_code: ClassVar[int] = 400
    public_message: ClassVar[str] = "The request could not be completed."

    def __init__(
        self,
        *,
        details: dict[str, object] | None = None,
        operation_id: str | None = None,
    ) -> None:
        super().__init__(self.public_message)
        redacted = redact_log_value(details) if details is not None else None
        self.details = redacted if isinstance(redacted, dict) else None
        self.operation_id = operation_id[:64] if operation_id is not None else None


class MalformedRequestError(AppError):
    code = "MALFORMED_REQUEST"
    status_code = 400
    public_message = "The request is malformed."


class AuthenticationError(AppError):
    code = "AUTHENTICATION_REQUIRED"
    status_code = 401
    public_message = "Authentication is required."


class AuthorizationError(AppError):
    code = "AUTHORIZATION_DENIED"
    status_code = 403
    public_message = "The operation is not permitted."


class ResourceNotFoundError(AppError):
    code = "RESOURCE_NOT_FOUND"
    status_code = 404
    public_message = "The resource is not available."


class ResourceConflictError(AppError):
    code = "RESOURCE_CONFLICT"
    status_code = 409
    public_message = "The request conflicts with current state."


class RequestTooLargeError(AppError):
    code = "REQUEST_TOO_LARGE"
    status_code = 413
    public_message = "The request is too large."


class DomainValidationError(AppError):
    code = "DOMAIN_VALIDATION_FAILED"
    status_code = 422
    public_message = "The request failed domain validation."


class QuotaExceededError(AppError):
    code = "QUOTA_EXCEEDED"
    status_code = 429
    public_message = "The request exceeds an enforced limit."


class ServiceUnavailableError(AppError):
    code = "SERVICE_UNAVAILABLE"
    status_code = 503
    public_message = "The service is temporarily unavailable."


def _request_id(request: Request) -> str:
    state_id = getattr(request.state, "request_id", None)
    if isinstance(state_id, str):
        return state_id
    return current_request_id() or "req_unavailable"


def _response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, JSONValue] | None = None,
    operation_id: str | None = None,
) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            request_id=_request_id(request),
            operation_id=operation_id,
            details=details,
        )
    )
    return JSONResponse(
        status_code=status_code, content=envelope.model_dump(mode="json")
    )


async def _app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):
        return _response(
            request,
            status_code=500,
            code="INTERNAL_ERROR",
            message="An internal error occurred.",
        )
    return _response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.public_message,
        details=exc.details,
        operation_id=exc.operation_id,
    )


async def _validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return await _app_error_handler(request, exc)
    issues: list[JSONValue] = []
    for error in exc.errors()[:20]:
        issues.append(
            {
                "location": [str(part)[:64] for part in error.get("loc", ())[:8]],
                "type": str(error.get("type", "validation_error"))[:64],
            }
        )
    return _response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="The request failed validation.",
        details={"issues": issues},
    )


async def _http_error_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code = exc.status_code if isinstance(exc, HTTPException) else 500
    return _response(
        request,
        status_code=status_code,
        code="HTTP_ERROR" if status_code < 500 else "INTERNAL_ERROR",
        message=(
            "The HTTP request could not be completed."
            if status_code < 500
            else "An internal error occurred."
        ),
    )


async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return _response(
        request,
        status_code=500,
        code="INTERNAL_ERROR",
        message="An internal error occurred.",
    )


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(HTTPException, _http_error_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)


__all__ = [
    "AppError",
    "AuthenticationError",
    "AuthorizationError",
    "DomainValidationError",
    "ErrorBody",
    "ErrorEnvelope",
    "MalformedRequestError",
    "QuotaExceededError",
    "RequestTooLargeError",
    "ResourceConflictError",
    "ResourceNotFoundError",
    "ServiceUnavailableError",
    "install_error_handlers",
]
