"""Agent-owned durable browser preview-run service.

This service reserves and reads database state only. It never dispatches a
worker, mints a public token, marks a run running/terminal, or stores bytes.
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

import asyncpg

from ..browser_contracts import (
    BROWSER_CONTRACT_VERSION,
    BrowserEvidence,
    BrowserRunError,
    BrowserRunState,
    BrowserTerminalState,
    PreviewRunCreateRequest,
    PreviewRunResult,
    PreviewRunStatus,
    PrivateBrowserArtifactMetadata,
    preview_run_request_digest,
)
from .models import AgentCapabilityContext

BEGIN_SQL = """
SELECT * FROM control.slaif_agent_browser_run_begin(
    $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17
)
"""
GET_SQL = "SELECT * FROM control.slaif_agent_browser_run_get($1,$2,$3,$4,$5)"
ARTIFACT_LIST_SQL = (
    "SELECT * FROM control.slaif_agent_browser_artifact_list($1,$2,$3,$4,$5)"
)
SCREENSHOT_RESERVATION_BYTES = 5 * 1024 * 1024
SUMMARY_RESERVATION_BYTES = 256 * 1024

type BrowserPublicRun = PreviewRunStatus | PreviewRunResult


class BrowserRunServiceReason(StrEnum):
    MISMATCH = "mismatch"
    QUOTA = "quota"
    NOT_FOUND = "not_found"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"


class BrowserRunServiceError(RuntimeError):
    def __init__(self, reason: BrowserRunServiceReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class BrowserRunCreation:
    outcome: str
    run: BrowserPublicRun


def _artifact_reservation(evidence: tuple[BrowserEvidence, ...]) -> int:
    return sum(
        SCREENSHOT_RESERVATION_BYTES
        if item is BrowserEvidence.SCREENSHOT
        else SUMMARY_RESERVATION_BYTES
        for item in evidence
    )


def _status(row: Any) -> PreviewRunStatus:
    try:
        return PreviewRunStatus(
            version=row["contract_version"],
            run_id=row["run_id"],
            state=row["state"],
            route=row["route"],
            target=row["target"],
            evidence=tuple(row["evidence"]),
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            expires_at=row["expires_at"],
        )
    except (KeyError, TypeError, ValueError):
        raise BrowserRunServiceError(BrowserRunServiceReason.UNAVAILABLE) from None


def _artifact(row: Any) -> PrivateBrowserArtifactMetadata:
    try:
        return PrivateBrowserArtifactMetadata(
            version=row["contract_version"],
            artifact_id=row["artifact_id"],
            run_id=row["run_id"],
            kind=row["kind"],
            mime_type=row["mime_type"],
            sha256=row["sha256"],
            size_bytes=row["size_bytes"],
            target=row["target"],
            route_digest=row["route_digest"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            visibility=row["visibility"],
        )
    except (KeyError, TypeError, ValueError):
        raise BrowserRunServiceError(BrowserRunServiceReason.UNAVAILABLE) from None


class AgentBrowserRunService:
    def __init__(self, database: Any) -> None:
        self._database = database

    @property
    def _acquire_timeout(self) -> float:
        return float(getattr(self._database, "acquire_timeout", 1.5))

    def _pool(self) -> Any:
        try:
            return self._database.cow_pool()
        except Exception:
            raise BrowserRunServiceError(BrowserRunServiceReason.UNAVAILABLE) from None

    async def create(
        self,
        *,
        context: AgentCapabilityContext,
        key: str,
        request: PreviewRunCreateRequest,
    ) -> BrowserRunCreation:
        operation_id = uuid4()
        run_id = uuid4()
        evidence = tuple(request.evidence)
        try:
            async with self._pool().acquire(
                timeout=self._acquire_timeout
            ) as connection:
                async with connection.transaction():
                    result = await connection.fetchrow(
                        BEGIN_SQL,
                        context.capability_id,
                        context.site_id,
                        context.workspace_id,
                        context.delegator_id,
                        key,
                        preview_run_request_digest(request),
                        operation_id,
                        run_id,
                        BROWSER_CONTRACT_VERSION,
                        request.route,
                        hashlib.sha256(request.route.encode("utf-8")).hexdigest(),
                        request.target.value,
                        [item.value for item in evidence],
                        1 if BrowserEvidence.SCREENSHOT in evidence else 0,
                        _artifact_reservation(evidence),
                        1,
                        context.browser_limits.max_duration_seconds,
                    )
        except asyncio.CancelledError:
            raise
        except (TimeoutError, OSError):
            raise BrowserRunServiceError(BrowserRunServiceReason.UNAVAILABLE) from None
        except asyncpg.PostgresError as error:
            message = str(error)
            if "BROWSER_QUOTA_EXCEEDED" in message:
                raise BrowserRunServiceError(BrowserRunServiceReason.QUOTA) from None
            if "BROWSER_AUTHORITY_DENIED" in message:
                raise BrowserRunServiceError(
                    BrowserRunServiceReason.NOT_FOUND
                ) from None
            if "INVALID_BROWSER_RUN_INPUT" in message:
                raise BrowserRunServiceError(BrowserRunServiceReason.INVALID) from None
            raise BrowserRunServiceError(BrowserRunServiceReason.UNAVAILABLE) from None
        if result is None:
            raise BrowserRunServiceError(BrowserRunServiceReason.UNAVAILABLE)
        outcome = result["result"]
        if outcome == "MISMATCH":
            raise BrowserRunServiceError(BrowserRunServiceReason.MISMATCH)
        if outcome not in {"STARTED", "REPLAY"} or not isinstance(
            result["run_id"], UUID
        ):
            raise BrowserRunServiceError(BrowserRunServiceReason.UNAVAILABLE)
        return BrowserRunCreation(
            outcome=outcome,
            run=await self.get(context=context, run_id=result["run_id"]),
        )

    async def _get_row(self, *, context: AgentCapabilityContext, run_id: UUID) -> Any:
        try:
            async with self._pool().acquire(
                timeout=self._acquire_timeout
            ) as connection:
                return await connection.fetchrow(
                    GET_SQL,
                    context.capability_id,
                    context.site_id,
                    context.workspace_id,
                    context.delegator_id,
                    run_id,
                )
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise BrowserRunServiceError(BrowserRunServiceReason.UNAVAILABLE) from None

    async def get(
        self, *, context: AgentCapabilityContext, run_id: UUID
    ) -> BrowserPublicRun:
        row = await self._get_row(context=context, run_id=run_id)
        if row is None:
            raise BrowserRunServiceError(BrowserRunServiceReason.NOT_FOUND)
        status = _status(row)
        if status.state not in {
            BrowserRunState.COMPLETED,
            BrowserRunState.FAILED,
            BrowserRunState.TIMED_OUT,
            BrowserRunState.CANCELLED,
        }:
            return status
        if status.completed_at is None or row["summary"] is None:
            raise BrowserRunServiceError(BrowserRunServiceReason.UNAVAILABLE)
        error = None
        if status.state is not BrowserRunState.COMPLETED:
            try:
                error = BrowserRunError(
                    code=row["error_code"], message=row["error_message"]
                )
            except (KeyError, TypeError, ValueError):
                raise BrowserRunServiceError(
                    BrowserRunServiceReason.UNAVAILABLE
                ) from None
        artifacts = await self.artifacts(context=context, run_id=run_id)
        return PreviewRunResult(
            version="browser-preview/v1",
            run_id=run_id,
            state=BrowserTerminalState(status.state.value),
            summary=row["summary"],
            error=error,
            artifacts=artifacts,
            completed_at=status.completed_at,
        )

    async def artifacts(
        self, *, context: AgentCapabilityContext, run_id: UUID
    ) -> tuple[PrivateBrowserArtifactMetadata, ...]:
        # Require the exact run first so a foreign/random run and an empty
        # authorized run share no distinguishable list behavior.
        if await self._get_row(context=context, run_id=run_id) is None:
            raise BrowserRunServiceError(BrowserRunServiceReason.NOT_FOUND)
        try:
            async with self._pool().acquire(
                timeout=self._acquire_timeout
            ) as connection:
                rows = await connection.fetch(
                    ARTIFACT_LIST_SQL,
                    context.capability_id,
                    context.site_id,
                    context.workspace_id,
                    context.delegator_id,
                    run_id,
                )
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise BrowserRunServiceError(BrowserRunServiceReason.UNAVAILABLE) from None
        return tuple(_artifact(row) for row in rows)


__all__ = [
    "AgentBrowserRunService",
    "BrowserPublicRun",
    "BrowserRunCreation",
    "BrowserRunServiceError",
    "BrowserRunServiceReason",
]
