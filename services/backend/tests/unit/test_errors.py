"""Stable, correlated, secret-safe application error envelopes."""

from __future__ import annotations

import httpx
import pytest
from fastapi import HTTPException
from slaif_agent_site.agent_api import create_app
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.errors import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    DomainValidationError,
    MalformedRequestError,
    QuotaExceededError,
    RequestTooLargeError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)


@pytest.mark.parametrize(
    ("error_type", "status"),
    (
        (MalformedRequestError, 400),
        (AuthenticationError, 401),
        (AuthorizationError, 403),
        (ResourceNotFoundError, 404),
        (ResourceConflictError, 409),
        (RequestTooLargeError, 413),
        (DomainValidationError, 422),
        (QuotaExceededError, 429),
        (ServiceUnavailableError, 503),
    ),
)
def test_error_hierarchy_has_architecture_status_mapping(
    error_type: type[AppError], status: int
) -> None:
    assert error_type.status_code == status
    assert error_type.code.isupper()
    assert error_type.public_message


async def test_app_error_is_correlated_and_recursively_redacted() -> None:
    app = create_app(settings=ServiceSettings.for_test())
    secret = "local-fixture-sensitive-value"

    @app.get("/test/app-error")
    async def app_error() -> None:
        raise AuthorizationError(
            details={"required_scope": "page:write", "capability_token": secret}
        )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get(
            "/test/app-error", headers={"X-Request-ID": "req_caller-safe"}
        )
    assert response.status_code == 403
    assert response.headers["X-Request-ID"] == "req_caller-safe"
    assert response.json() == {
        "error": {
            "code": "AUTHORIZATION_DENIED",
            "message": "The operation is not permitted.",
            "request_id": "req_caller-safe",
            "operation_id": None,
            "details": {
                "required_scope": "page:write",
                "capability_token": "[REDACTED]",
            },
        }
    }
    assert secret not in response.text


async def test_validation_http_and_internal_errors_suppress_inputs_and_details() -> (
    None
):
    app = create_app(settings=ServiceSettings.for_test())
    secret = "local-fixture-sensitive-value"

    @app.get("/test/validation")
    async def validation(count: int) -> dict[str, int]:
        return {"count": count}

    @app.get("/test/http")
    async def http_error() -> None:
        raise HTTPException(418, detail=f"password={secret}")

    @app.get("/test/internal")
    async def internal_error() -> None:
        raise RuntimeError(f"database_url=postgresql://user:{secret}@db/example")

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        validation_response = await client.get(
            "/test/validation", params={"count": f"password={secret}"}
        )
        http_response = await client.get("/test/http")
        internal_response = await client.get("/test/internal")

    assert validation_response.status_code == 422
    assert validation_response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "input" not in validation_response.text
    assert secret not in validation_response.text
    assert http_response.status_code == 418
    assert http_response.json()["error"]["code"] == "HTTP_ERROR"
    assert secret not in http_response.text
    assert internal_response.status_code == 500
    assert internal_response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert secret not in internal_response.text
