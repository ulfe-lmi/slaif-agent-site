"""Unit proofs for the internal, capability-confined artifact retrieval seam."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI, Request
from slaif_agent_site.agent_api import browser_http
from slaif_agent_site.agent_api.browser_service import (
    AgentBrowserRunService,
    BrowserArtifactRetrieval,
    BrowserRunServiceError,
    BrowserRunServiceReason,
)
from slaif_agent_site.agent_api.models import AgentCapabilityContext
from slaif_agent_site.browser_worker_client import BrowserWorkerClientError

IDS = {
    "capability_id": UUID("00000000-0000-4000-8000-000000000001"),
    "site_id": UUID("00000000-0000-4000-8000-000000000002"),
    "workspace_id": UUID("00000000-0000-4000-8000-000000000003"),
    "delegator_id": UUID("00000000-0000-4000-8000-000000000004"),
    "run_id": UUID("00000000-0000-4000-8000-000000000005"),
    "artifact_id": UUID("00000000-0000-4000-8000-000000000006"),
    "request_id": UUID("00000000-0000-4000-8000-000000000007"),
}


class _Acquire:
    def __init__(self, connection: object) -> None:
        self.connection = connection

    async def __aenter__(self) -> object:
        return self.connection

    async def __aexit__(self, *_args: object) -> None:
        return None


class _Pool:
    def __init__(self, connection: object) -> None:
        self.connection = connection

    def acquire(self, *, timeout: float) -> _Acquire:
        assert timeout > 0
        return _Acquire(self.connection)


class _Database:
    acquire_timeout = 0.25

    def __init__(self, connection: object) -> None:
        self.pool = _Pool(connection)

    def cow_pool(self) -> _Pool:
        return self.pool


class _Connection:
    def __init__(self, row: dict[str, object] | None) -> None:
        self.row = row
        self.arguments: tuple[object, ...] | None = None

    async def fetchrow(self, _sql: str, *arguments: object) -> dict[str, object] | None:
        self.arguments = arguments
        return self.row


class _Worker:
    def __init__(self, content: bytes | Exception) -> None:
        self.content = content
        self.request_id: UUID | None = None

    async def retrieve(self, request_id: UUID, _metadata: object) -> bytes:
        self.request_id = request_id
        if isinstance(self.content, Exception):
            raise self.content
        return self.content


def _context() -> AgentCapabilityContext:
    now = datetime.now(UTC)
    return AgentCapabilityContext(
        capability_id=IDS["capability_id"],
        site_id=IDS["site_id"],
        workspace_id=IDS["workspace_id"],
        delegator_id=IDS["delegator_id"],
        scopes=frozenset({"preview:inspect"}),
        created_at=now,
        expires_at=now + timedelta(hours=1),
    )


def _row(content: bytes) -> dict[str, object]:
    now = datetime.now(UTC)
    return {
        "worker_request_id": IDS["request_id"],
        "run_id": IDS["run_id"],
        "site_id": IDS["site_id"],
        "workspace_id": IDS["workspace_id"],
        "artifact_id": IDS["artifact_id"],
        "kind": "screenshot",
        "mime_type": "image/png",
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
        "target": "desktop-chromium",
        "route_digest": "a" * 64,
        "created_at": now,
        "expires_at": now + timedelta(minutes=10),
        "visibility": "PRIVATE",
    }


@pytest.mark.asyncio
async def test_retrieval_uses_exact_binding_and_returns_safe_metadata() -> None:
    content = b"png-bytes"
    connection = _Connection(_row(content))
    worker = _Worker(content)
    service = AgentBrowserRunService(_Database(connection), worker_client=worker)  # type: ignore[arg-type]

    result = await service.retrieve_artifact(
        context=_context(), run_id=IDS["run_id"], artifact_id=IDS["artifact_id"]
    )

    assert result.content == content
    assert result.mime_type == "image/png"
    assert result.sha256 == hashlib.sha256(content).hexdigest()
    assert result.size_bytes == len(content)
    assert connection.arguments == (
        IDS["capability_id"],
        IDS["site_id"],
        IDS["workspace_id"],
        IDS["delegator_id"],
        IDS["run_id"],
        IDS["artifact_id"],
    )
    assert worker.request_id == IDS["request_id"]


@pytest.mark.asyncio
async def test_retrieval_missing_binding_is_non_leaking_not_found() -> None:
    service = AgentBrowserRunService(
        _Database(_Connection(None)),
        worker_client=_Worker(b"unused"),  # type: ignore[arg-type]
    )
    with pytest.raises(BrowserRunServiceError) as error:
        await service.retrieve_artifact(
            context=_context(), run_id=IDS["run_id"], artifact_id=IDS["artifact_id"]
        )
    assert error.value.reason is BrowserRunServiceReason.NOT_FOUND


@pytest.mark.asyncio
async def test_retrieval_worker_failure_is_unavailable_and_digest_is_verified() -> None:
    connection = _Connection(_row(b"png-bytes"))
    service = AgentBrowserRunService(
        _Database(connection),
        worker_client=_Worker(BrowserWorkerClientError("down")),  # type: ignore[arg-type]
    )
    with pytest.raises(BrowserRunServiceError) as error:
        await service.retrieve_artifact(
            context=_context(), run_id=IDS["run_id"], artifact_id=IDS["artifact_id"]
        )
    assert error.value.reason is BrowserRunServiceReason.UNAVAILABLE

    bad_connection = _Connection(_row(b"png-bytes"))
    bad_service = AgentBrowserRunService(
        _Database(bad_connection),
        worker_client=_Worker(b"wrong"),  # type: ignore[arg-type]
    )
    with pytest.raises(BrowserRunServiceError) as bad_error:
        await bad_service.retrieve_artifact(
            context=_context(), run_id=IDS["run_id"], artifact_id=IDS["artifact_id"]
        )
    assert bad_error.value.reason is BrowserRunServiceReason.UNAVAILABLE


class _PublicService:
    async def retrieve_artifact(self, **_kwargs: object) -> BrowserArtifactRetrieval:
        content = b"private-png"
        return BrowserArtifactRetrieval(
            content=content,
            mime_type="image/png",
            sha256=hashlib.sha256(content).hexdigest(),
            size_bytes=len(content),
        )


@pytest.mark.asyncio
async def test_public_artifact_response_is_exact_private_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    app.state.browser_run_service = _PublicService()
    app.include_router(browser_http.router)

    async def authenticate(_request: Request) -> object:
        return object()

    monkeypatch.setattr(browser_http, "_authenticate", authenticate)
    monkeypatch.setattr(browser_http, "_require_scope", lambda *_args: None)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
    ) as client:
        response = await client.get(
            f"/api/agent/v1/preview-runs/{IDS['run_id']}/artifacts/{IDS['artifact_id']}"
        )
    assert response.status_code == 200
    assert response.content == b"private-png"
    assert response.headers["content-type"] == "image/png"
    assert response.headers["content-length"] == str(len(response.content))
    assert (
        response.headers["etag"] == f'"{hashlib.sha256(response.content).hexdigest()}"'
    )
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
    assert response.headers["x-content-type-options"] == "nosniff"
