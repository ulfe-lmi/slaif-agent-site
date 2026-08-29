"""Capability-authenticated public Agent preview-run routes."""

from __future__ import annotations

from typing import Annotated, Never, cast
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response

from ..browser_contracts import (
    PreviewRunCreateRequest,
    PreviewRunResult,
    PreviewRunStatus,
    PrivateBrowserArtifactMetadata,
)
from ..errors import (
    DomainValidationError,
    IdempotencyKeyInvalidError,
    IdempotencyKeyRequiredError,
    IdempotencyMismatchError,
    QuotaExceededError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from .agent_http import _authenticate, _require_scope
from .browser_service import (
    AgentBrowserRunService,
    BrowserPublicRun,
    BrowserRunServiceError,
    BrowserRunServiceReason,
)

router = APIRouter(prefix="/api/agent/v1/preview-runs")
IdempotencyHeader = Annotated[str | None, Header(alias="Idempotency-Key")]
IDEMPOTENCY_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._~-"
)


def _private(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"


def _map_error(error: BrowserRunServiceError) -> Never:
    if error.reason is BrowserRunServiceReason.MISMATCH:
        raise IdempotencyMismatchError() from None
    if error.reason is BrowserRunServiceReason.QUOTA:
        raise QuotaExceededError() from None
    if error.reason is BrowserRunServiceReason.NOT_FOUND:
        raise ResourceNotFoundError() from None
    if error.reason is BrowserRunServiceReason.INVALID:
        raise DomainValidationError() from None
    raise ServiceUnavailableError() from None


def _key(value: str | None) -> str:
    if value is None:
        raise IdempotencyKeyRequiredError()
    if not 1 <= len(value) <= 128 or any(
        character not in IDEMPOTENCY_CHARACTERS for character in value
    ):
        raise IdempotencyKeyInvalidError()
    return value


def _service(request: Request) -> AgentBrowserRunService:
    return cast(AgentBrowserRunService, request.app.state.browser_run_service)


@router.post(
    "",
    status_code=202,
    response_model=PreviewRunStatus | PreviewRunResult,
)
async def create_preview_run(
    request: Request,
    response: Response,
    body: PreviewRunCreateRequest,
    idempotency_key: IdempotencyHeader = None,
) -> BrowserPublicRun:
    context = await _authenticate(request)
    _require_scope(context, "preview:inspect")
    try:
        created = await _service(request).create(
            context=context,
            key=_key(idempotency_key),
            request=body,
        )
    except BrowserRunServiceError as error:
        _map_error(error)
    _private(response)
    return created.run


@router.get(
    "/{run_id}",
    response_model=PreviewRunStatus | PreviewRunResult,
)
async def get_preview_run(
    run_id: UUID, request: Request, response: Response
) -> BrowserPublicRun:
    context = await _authenticate(request)
    _require_scope(context, "preview:inspect")
    try:
        result = await _service(request).get(context=context, run_id=run_id)
    except BrowserRunServiceError as error:
        _map_error(error)
    _private(response)
    return result


@router.get(
    "/{run_id}/artifacts",
    response_model=tuple[PrivateBrowserArtifactMetadata, ...],
)
async def list_preview_run_artifacts(
    run_id: UUID, request: Request, response: Response
) -> tuple[PrivateBrowserArtifactMetadata, ...]:
    context = await _authenticate(request)
    _require_scope(context, "preview:inspect")
    try:
        result = await _service(request).artifacts(context=context, run_id=run_id)
    except BrowserRunServiceError as error:
        _map_error(error)
    _private(response)
    return result


@router.get("/{run_id}/artifacts/{artifact_id}")
async def get_preview_run_artifact_bytes(
    run_id: UUID,
    artifact_id: UUID,
    request: Request,
) -> Response:
    context = await _authenticate(request)
    _require_scope(context, "preview:inspect")
    try:
        artifact = await _service(request).retrieve_artifact(
            context=context, run_id=run_id, artifact_id=artifact_id
        )
    except BrowserRunServiceError as error:
        _map_error(error)
    result = Response(
        content=artifact.content,
        media_type=None,
        headers={
            "Content-Type": artifact.mime_type,
            "Content-Length": str(artifact.size_bytes),
            "ETag": f'"{artifact.sha256}"',
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
        },
    )
    _private(result)
    return result


__all__ = ["router"]
