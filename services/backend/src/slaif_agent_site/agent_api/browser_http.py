"""Capability-authenticated public Agent preview-run routes."""

from __future__ import annotations

import re
from typing import Annotated, Any, Never, cast
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response

from ..browser_contracts import (
    PreviewRunCreateRequest,
    PreviewRunResult,
    PreviewRunStatus,
    PrivateBrowserArtifactMetadata,
)
from ..errors import (
    AuthenticationError,
    DomainValidationError,
    IdempotencyKeyInvalidError,
    IdempotencyKeyRequiredError,
    IdempotencyMismatchError,
    QuotaExceededError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from ..identity.sessions import SessionCredentialError, parse_session_token
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


_SESSION_COOKIE_NAMES = ("slaif_session", "__Host-slaif_session")
_COOKIE_NAME = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_COOKIE_VALUE = re.compile(r"^[\x21\x23-\x2B\x2D-\x3A\x3C-\x5B\x5D-\x7E]*$")


def _session_cookie_values(request: Request) -> dict[str, str]:
    """Strict single-Cookie-header parse (the established control policy)."""
    headers = request.scope.get("headers", [])
    raw_headers = [value for name, value in headers if name.lower() == b"cookie"]
    if len(raw_headers) != 1:
        raise AuthenticationError()
    try:
        raw = raw_headers[0].decode("ascii")
    except UnicodeDecodeError:
        raise AuthenticationError() from None
    if not raw:
        raise AuthenticationError()
    values: dict[str, str] = {}
    for part in raw.split(";"):
        pair = part.strip()
        if not pair or pair.count("=") != 1:
            raise AuthenticationError()
        name, value = pair.split("=", 1)
        if (
            not _COOKIE_NAME.fullmatch(name)
            or not _COOKIE_VALUE.fullmatch(value)
            or name in values
        ):
            raise AuthenticationError()
        values[name] = value
    return values


def _present_header_names(request: Request) -> frozenset[bytes]:
    headers = request.scope.get("headers", [])
    return frozenset(name.lower() for name, _ in headers)


async def _artifact_credential(
    request: Request,
) -> tuple[str, Any]:
    """Dual credential for private artifact reads (082/2).

    ``("capability", context)`` whenever an Authorization header is
    presented (the existing path, quota included).  Without one, a
    request carrying exactly one trusted session cookie (the 082/2
    read-only extension) resolves to ``("human", (public_id, secret))``;
    every other credential state takes the established no-credential
    path and fails exactly as before 082/2.  No capability token is
    consulted and no agent quota is consumed on the human path.
    """
    names = _present_header_names(request)
    if b"authorization" in names:
        return ("capability", await _authenticate(request))
    if b"cookie" in names:
        values = _session_cookie_values(request)
        session_names = [name for name in _SESSION_COOKIE_NAMES if name in values]
        if len(session_names) == 1:
            try:
                return ("human", parse_session_token(values[session_names[0]]))
            except SessionCredentialError:
                raise AuthenticationError() from None
    return ("capability", await _authenticate(request))


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
    kind, credential = await _artifact_credential(request)
    if kind == "capability":
        context = credential
        _require_scope(context, "preview:inspect")
        try:
            result = await _service(request).artifacts(context=context, run_id=run_id)
        except BrowserRunServiceError as error:
            _map_error(error)
    else:
        public_id, secret = credential
        try:
            result = await _service(request).human_session_artifacts(
                public_id=public_id, secret=secret, run_id=run_id
            )
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
    kind, credential = await _artifact_credential(request)
    if kind == "capability":
        context = credential
        _require_scope(context, "preview:inspect")
        try:
            artifact = await _service(request).retrieve_artifact(
                context=context, run_id=run_id, artifact_id=artifact_id
            )
        except BrowserRunServiceError as error:
            _map_error(error)
    else:
        public_id, secret = credential
        try:
            artifact = await _service(request).human_session_retrieve_artifact(
                public_id=public_id,
                secret=secret,
                run_id=run_id,
                artifact_id=artifact_id,
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
