"""Bounded durable browser-run dispatcher owned by the Agent API."""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

import asyncpg
from pydantic import SecretStr

from ..browser_contracts import (
    BrowserEvidence,
    BrowserTarget,
    InternalPreviewRunSpecification,
)
from ..browser_preview_credentials import BrowserPreviewCredentialSigner
from ..browser_worker_client import (
    BrowserWorkerClient,
    BrowserWorkerClientError,
    BrowserWorkerResult,
    BrowserWorkerSubmitRequest,
)
from ..health import ProbeResult
from .config import AgentDispatcherSettings

LOGGER = logging.getLogger(__name__)
CLAIM_SQL = "SELECT * FROM control.slaif_agent_browser_run_claim($1,$2)"
RENEW_SQL = "SELECT control.slaif_agent_browser_run_renew($1,$2,$3)"
RELEASE_SQL = "SELECT control.slaif_agent_browser_run_release($1,$2)"
COMPLETE_SQL = "SELECT control.slaif_agent_browser_run_complete($1,$2,$3,$4,$5,$6)"
ARTIFACT_REGISTER_SQL = (
    "SELECT control.slaif_agent_browser_artifact_register("
    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)"
)


@dataclass(frozen=True, slots=True)
class BrowserDispatchClaim:
    specification: InternalPreviewRunSpecification
    lease_id: UUID
    lease_expires_at: datetime
    run_expires_at: datetime | None = None


@dataclass(slots=True)
class _ActiveAttempt:
    claim: BrowserDispatchClaim
    task: asyncio.Task[None] | None = None
    finalized: bool = False
    released: bool = False
    lease_lost: asyncio.Event | None = None


def _utc_timestamp(value: int) -> datetime:
    return datetime.fromtimestamp(value, UTC)


class AgentBrowserDispatcher:
    """Claim, execute, and atomically finalize queued browser runs."""

    def __init__(
        self,
        *,
        database: Any,
        signer: BrowserPreviewCredentialSigner | None,
        worker_client: BrowserWorkerClient | None,
        settings: AgentDispatcherSettings,
    ) -> None:
        self._database = database
        self._signer = signer
        self._worker_client = worker_client
        self._settings = settings
        self._stop = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._active: set[asyncio.Task[None]] = set()
        self._attempts: dict[asyncio.Task[None], _ActiveAttempt] = {}
        self._started = False

    @property
    def enabled(self) -> bool:
        return self._settings.enabled

    async def readiness(self) -> ProbeResult:
        if not self._settings.enabled:
            return ProbeResult.ready()
        if self._signer is None or self._worker_client is None:
            return ProbeResult.unavailable("dispatcher_dependency_unavailable")
        if not self._started:
            return ProbeResult.unavailable("dispatcher_not_started")
        return ProbeResult.ready()

    def _pool(self) -> Any:
        return self._database.cow_pool()

    async def start(self) -> None:
        if self._started or not self._settings.enabled:
            return
        if self._signer is None or self._worker_client is None:
            return
        self._stop.clear()
        self._started = True
        self._task = asyncio.create_task(self._run(), name="agent-browser-dispatcher")

    async def stop(self) -> None:
        self._stop.set()
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            await self._wait_task(task)
        active = tuple(self._active)
        for attempt_task in active:
            attempt_task.cancel()
        if active:
            await asyncio.gather(*active, return_exceptions=True)
        self._active.clear()
        self._attempts.clear()
        self._started = False

    async def _wait_task(self, task: asyncio.Task[Any]) -> None:
        try:
            await asyncio.wait_for(
                asyncio.shield(task), self._settings.shutdown_timeout_seconds
            )
        except (asyncio.CancelledError, TimeoutError):
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def _run(self) -> None:
        while not self._stop.is_set():
            self._drain_finished()
            if len(self._active) >= self._settings.concurrency:
                await self._sleep(self._settings.poll_interval_seconds)
                continue
            try:
                claim = await self._claim()
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.warning("browser dispatcher claim unavailable")
                await self._sleep(self._settings.backoff_seconds)
                continue
            if claim is None:
                await self._sleep(self._settings.poll_interval_seconds)
                continue
            active = _ActiveAttempt(claim=claim, lease_lost=asyncio.Event())
            attempt_task = asyncio.create_task(
                self._process(active), name=f"browser-run-{claim.specification.run_id}"
            )
            active.task = attempt_task
            self._active.add(attempt_task)
            self._attempts[attempt_task] = active
        self._drain_finished()

    async def _sleep(self, seconds: float) -> None:
        try:
            await asyncio.wait_for(self._stop.wait(), seconds)
        except TimeoutError:
            pass

    def _drain_finished(self) -> None:
        for task in tuple(self._active):
            if task.done():
                self._active.discard(task)
                self._attempts.pop(task, None)
                try:
                    task.result()
                except (asyncio.CancelledError, Exception):
                    pass

    async def _claim(self) -> BrowserDispatchClaim | None:
        lease_id = uuid4()
        async with self._pool().acquire(
            timeout=getattr(self._database, "acquire_timeout", 1.5)
        ) as connection:
            row = await connection.fetchrow(
                CLAIM_SQL, lease_id, self._settings.lease_seconds
            )
        if row is None:
            return None
        specification = InternalPreviewRunSpecification(
            version=row["contract_version"],
            run_id=row["run_id"],
            operation_id=row["operation_id"],
            site_id=row["site_id"],
            workspace_id=row["workspace_id"],
            capability_id=row["capability_id"],
            delegator_id=row["delegator_id"],
            route=row["route"],
            route_digest=row["route_digest"],
            target=row["target"],
            evidence=tuple(row["evidence"]),
            reserved_screenshots=row["reserved_screenshots"],
            reserved_artifact_bytes=row["reserved_artifact_bytes"],
            max_duration_seconds=row["max_duration_seconds"],
            attempt=row["attempt"],
        )
        return BrowserDispatchClaim(
            specification=specification,
            lease_id=row["lease_id"],
            lease_expires_at=row["lease_expires_at"],
            run_expires_at=await self._run_expiry(specification),
        )

    async def _run_expiry(
        self, specification: InternalPreviewRunSpecification
    ) -> datetime:
        """Read the trusted run expiry through the Agent-owned function boundary."""

        try:
            async with self._pool().acquire(
                timeout=getattr(self._database, "acquire_timeout", 1.5)
            ) as connection:
                row = await connection.fetchrow(
                    "SELECT expires_at FROM control.slaif_agent_browser_run_get("
                    "$1,$2,$3,$4,$5)",
                    specification.capability_id,
                    specification.site_id,
                    specification.workspace_id,
                    specification.delegator_id,
                    specification.run_id,
                )
            if row is None:
                raise BrowserWorkerClientError("browser run expiry unavailable")
            return cast(datetime, row[0])
        except asyncio.CancelledError:
            raise

    async def _renew(self, active: _ActiveAttempt) -> None:
        assert active.lease_lost is not None
        while not self._stop.is_set() and not active.lease_lost.is_set():
            try:
                await asyncio.wait_for(
                    self._stop.wait(), self._settings.renewal_interval_seconds
                )
                return
            except TimeoutError:
                pass
            try:
                async with self._pool().acquire(
                    timeout=getattr(self._database, "acquire_timeout", 1.5)
                ) as connection:
                    await connection.fetchval(
                        RENEW_SQL,
                        active.claim.specification.run_id,
                        active.claim.lease_id,
                        self._settings.lease_seconds,
                    )
            except asyncio.CancelledError:
                raise
            except Exception:
                active.lease_lost.set()
                return

    def _request(
        self, claim: BrowserDispatchClaim, now: int
    ) -> BrowserWorkerSubmitRequest:
        assert self._signer is not None
        specification = claim.specification
        duration = min(
            specification.max_duration_seconds,
            int(self._settings.worker_timeout_seconds),
        )
        ttl = min(30, duration)
        preview_credential = self._signer.issue(
            capability_id=specification.capability_id,
            site_id=specification.site_id,
            workspace_id=specification.workspace_id,
            run_id=specification.run_id,
            route=specification.route,
            target=BrowserTarget(specification.target),
            evidence=tuple(BrowserEvidence(item) for item in specification.evidence),
            artifact_bytes_limit=min(specification.reserved_artifact_bytes, 16_777_216),
            duration_seconds=duration,
            now=now,
            ttl_seconds=ttl,
            nonce=secrets.token_hex(16),
        )
        return BrowserWorkerSubmitRequest(
            request_id=uuid4(),
            run_id=specification.run_id,
            site_id=specification.site_id,
            workspace_id=specification.workspace_id,
            capability_id=specification.capability_id,
            operation_id=specification.operation_id,
            lease_id=claim.lease_id,
            attempt=specification.attempt,
            route=specification.route,
            route_digest=specification.route_digest,
            target=BrowserTarget(specification.target),
            evidence=tuple(BrowserEvidence(item) for item in specification.evidence),
            artifact_bytes_limit=min(specification.reserved_artifact_bytes, 16_777_216),
            duration_seconds=duration,
            issued_at=now,
            expires_at=now + ttl,
            preview_credential=SecretStr(preview_credential),
        )

    async def _process(self, active: _ActiveAttempt) -> None:
        assert active.lease_lost is not None
        renew_task: asyncio.Task[None] | None = None
        try:
            request = self._request(active.claim, int(time.time()))
            renew_task = asyncio.create_task(self._renew(active))
            assert self._worker_client is not None
            result = await self._worker_client.submit(request, now=int(time.time()))
            if active.lease_lost.is_set() or self._stop.is_set():
                return
            if result.state == "COMPLETED":
                await self._complete_success(active, request, result)
            else:
                await self._complete_terminal(active, result)
            active.finalized = True
        except asyncio.CancelledError:
            raise
        except (BrowserWorkerClientError, OSError, TimeoutError, asyncpg.PostgresError):
            LOGGER.warning("browser dispatcher attempt unavailable")
            if not active.lease_lost.is_set() and not self._stop.is_set():
                await self._release(active)
        except Exception:
            LOGGER.exception("browser dispatcher attempt failed")
            if not active.lease_lost.is_set() and not self._stop.is_set():
                await self._release(active)
        finally:
            if renew_task is not None:
                renew_task.cancel()
                await asyncio.gather(renew_task, return_exceptions=True)
            if (
                not active.finalized
                and not active.released
                and not active.lease_lost.is_set()
            ):
                await self._release(active)

    async def _release(self, active: _ActiveAttempt) -> None:
        if active.released:
            return
        active.released = True
        try:
            async with self._pool().acquire(
                timeout=getattr(self._database, "acquire_timeout", 1.5)
            ) as connection:
                await connection.fetchval(
                    RELEASE_SQL,
                    active.claim.specification.run_id,
                    active.claim.lease_id,
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            LOGGER.warning("browser dispatcher lease release unavailable")

    async def _complete_terminal(
        self, active: _ActiveAttempt, result: BrowserWorkerResult
    ) -> None:
        error = result.error
        if result.state == "COMPLETED" or error is None:
            raise BrowserWorkerClientError("browser terminal result is invalid")
        await self._complete(
            active,
            result.state,
            result.summary,
            error.code,
            error.message,
        )

    async def _complete_success(
        self,
        active: _ActiveAttempt,
        request: BrowserWorkerSubmitRequest,
        result: BrowserWorkerResult,
    ) -> None:
        assert active.lease_lost is not None
        specification = active.claim.specification
        artifacts = result.artifacts
        kinds = tuple(artifact.kind for artifact in artifacts)
        expected = tuple(BrowserEvidence(item) for item in specification.evidence)
        if (
            len(kinds) != len(set(kinds))
            or set(kinds) != set(expected)
            or len(artifacts) > 16
            or sum(artifact.size_bytes for artifact in artifacts)
            > specification.reserved_artifact_bytes
            or sum(
                artifact.kind is BrowserEvidence.SCREENSHOT for artifact in artifacts
            )
            > specification.reserved_screenshots
        ):
            raise BrowserWorkerClientError("browser artifacts are invalid")
        assert self._worker_client is not None
        for artifact in artifacts:
            if (
                artifact.run_id != request.run_id
                or artifact.site_id != request.site_id
                or artifact.workspace_id != request.workspace_id
                or artifact.target != request.target
                or artifact.route_digest != request.route_digest
                or artifact.expires_at <= int(time.time())
                or artifact.kind is BrowserEvidence.SCREENSHOT
                and artifact.mime_type != "image/png"
                or artifact.kind is not BrowserEvidence.SCREENSHOT
                and artifact.mime_type not in {"application/json", "text/plain"}
            ):
                raise BrowserWorkerClientError("browser artifact binding is invalid")
            await self._worker_client.retrieve(request.request_id, artifact)
        if active.lease_lost.is_set() or self._stop.is_set():
            return
        await self._complete(
            active,
            result.state,
            result.summary,
            None,
            None,
            artifacts,
            worker_request_id=request.request_id,
        )

    async def _complete(
        self,
        active: _ActiveAttempt,
        state: str,
        summary: dict[str, Any],
        error_code: str | None,
        error_message: str | None,
        artifacts: tuple[Any, ...] = (),
        worker_request_id: UUID | None = None,
    ) -> None:
        if active.lease_lost is not None and active.lease_lost.is_set():
            return
        async with self._pool().acquire(
            timeout=getattr(self._database, "acquire_timeout", 1.5)
        ) as connection:
            async with connection.transaction():
                run_expiry = active.claim.run_expires_at
                for artifact in artifacts:
                    await connection.fetchval(
                        ARTIFACT_REGISTER_SQL,
                        artifact.run_id,
                        active.claim.lease_id,
                        artifact.artifact_id,
                        worker_request_id,
                        artifact.kind.value,
                        artifact.mime_type,
                        artifact.sha256,
                        artifact.size_bytes,
                        artifact.target.value,
                        artifact.route_digest,
                        _utc_timestamp(
                            min(
                                artifact.expires_at,
                                int(run_expiry.timestamp())
                                if run_expiry is not None
                                else artifact.expires_at,
                            )
                        ),
                    )
                await connection.fetchval(
                    COMPLETE_SQL,
                    active.claim.specification.run_id,
                    active.claim.lease_id,
                    state,
                    json.dumps(summary, ensure_ascii=False, separators=(",", ":")),
                    error_code,
                    error_message,
                )


__all__ = ["AgentBrowserDispatcher", "BrowserDispatchClaim"]
