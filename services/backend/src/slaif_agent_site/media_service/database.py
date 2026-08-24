"""Least-privileged Media database pool and COW boundary."""

from __future__ import annotations

import asyncio
import json
from contextlib import suppress
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import asyncpg

from slaif_agent_site.agent_state.foundation import asyncpg_cow_session
from slaif_agent_site.health import ProbeResult

from .config import MediaDatabaseConfigurationError, MediaSettings

IDENTITY_SQL = (
    "SELECT current_database()::text, session_user::text, current_user::text, "
    "ARRAY(SELECT target.rolname::text FROM pg_catalog.pg_roles target "
    "WHERE target.rolname = ANY($1::text[]) AND "
    "pg_catalog.pg_has_role(session_user, target.oid, 'MEMBER') "
    "ORDER BY target.rolname)"
)
MEDIA_AUTHORIZE_SQL = "SELECT * FROM control.slaif_media_authorize($1,$2,$3,$4,$5,$6)"
MEDIA_REGISTER_SQL = (
    "SELECT * FROM content.slaif_media_asset_register("
    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)"
)
MEDIA_GET_SQL = "SELECT * FROM content.slaif_media_asset_get($1,$2,$3,$4,$5,$6)"
MEDIA_IDEMPOTENCY_BEGIN_SQL = (
    "SELECT * FROM control.slaif_media_idempotency_begin($1,$2,$3,$4,$5,$6,$7,$8)"
)
MEDIA_IDEMPOTENCY_COMPLETE_SQL = (
    "SELECT control.slaif_media_idempotency_complete("
    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)"
)


@dataclass(frozen=True, slots=True)
class MediaAuthContext:
    session_id: UUID
    human_user_id: UUID
    site_id: UUID
    workspace_id: UUID
    permission: str


@dataclass(frozen=True, slots=True)
class MediaRecord:
    id: UUID
    site_id: UUID
    uploaded_by: UUID
    filename: str
    mime_type: str
    size_bytes: int
    content_hash: str
    storage_key: str
    alt_text: str
    metadata: dict[str, Any]
    created_at: Any
    updated_at: Any


class MediaIdempotencyMismatchError(RuntimeError):
    """An idempotency key was reused with another upload."""


class MediaDatabase:
    def __init__(
        self, settings: MediaSettings, *, pool_factory: Any = asyncpg.create_pool
    ) -> None:
        self.settings = settings
        self._pool_factory = pool_factory
        self._pool: Any = None
        self._reason = "connection_unavailable"

    async def _initialize(self, connection: Any) -> None:
        row = await connection.fetchrow(
            IDENTITY_SQL, [self.settings.expected_privilege_role]
        )
        if (
            row is None
            or tuple(row[:3])
            != (
                self.settings.expected_database,
                self.settings.expected_login,
                self.settings.expected_login,
            )
            or tuple(row[3]) != (self.settings.expected_privilege_role,)
        ):
            raise RuntimeError("identity_mismatch")

    async def start(self) -> None:
        if self._pool is not None:
            return
        try:
            dsn = self.settings.resolved_dsn()
            self._pool = await self._pool_factory(
                dsn=dsn.get_secret_value(),
                min_size=self.settings.pool_min_size,
                max_size=self.settings.pool_max_size,
                timeout=self.settings.connect_timeout_seconds,
                command_timeout=self.settings.command_timeout_seconds,
                max_inactive_connection_lifetime=self.settings.max_inactive_connection_lifetime_seconds,
                server_settings=self.settings.server_settings,
                init=self._initialize,
            )
        except asyncio.CancelledError:
            raise
        except MediaDatabaseConfigurationError:
            self._reason = "configuration_invalid"
        except TimeoutError:
            self._reason = "timeout"
        except Exception as error:
            self._reason = (
                str(error)
                if str(error) == "identity_mismatch"
                else "connection_unavailable"
            )

    async def stop(self) -> None:
        pool, self._pool = self._pool, None
        self._reason = "shutdown"
        if pool is None:
            return
        task = asyncio.create_task(pool.close())
        try:
            await asyncio.wait_for(
                asyncio.shield(task), self.settings.shutdown_timeout_seconds
            )
        except asyncio.CancelledError:
            try:
                await asyncio.wait_for(
                    asyncio.shield(task), self.settings.shutdown_timeout_seconds
                )
            except TimeoutError:
                pool.terminate()
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            raise
        except TimeoutError:
            pool.terminate()
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    async def readiness(self) -> ProbeResult:
        if self._pool is None:
            return ProbeResult.unavailable(self._reason)
        try:
            async with self._pool.acquire(
                timeout=self.settings.acquire_timeout_seconds
            ) as connection:
                await connection.fetchval("SELECT 1")
            return ProbeResult.ready()
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            return ProbeResult.unavailable("timeout")
        except Exception:
            return ProbeResult.unavailable("connection_unavailable")

    def cow_pool(self) -> Any:
        if self._pool is None:
            raise RuntimeError("media database unavailable")
        return self._pool

    async def authorize(
        self,
        *,
        public_id: str,
        session_digest: bytes,
        csrf_digest: bytes,
        site_id: UUID,
        permission: str,
        state_changing: bool,
    ) -> MediaAuthContext | None:
        try:
            async with self.cow_pool().acquire(
                timeout=self.settings.acquire_timeout_seconds
            ) as connection:
                row = await connection.fetchrow(
                    MEDIA_AUTHORIZE_SQL,
                    public_id,
                    session_digest,
                    csrf_digest,
                    site_id,
                    permission,
                    state_changing,
                )
        except asyncio.CancelledError:
            raise
        except Exception as error:
            raise RuntimeError("media authorization unavailable") from error
        if row is None:
            return None
        return MediaAuthContext(
            session_id=row[0],
            human_user_id=row[1],
            site_id=row[2],
            workspace_id=row[3],
            permission=permission,
        )

    async def register(
        self,
        *,
        context: MediaAuthContext,
        idempotency_key: str,
        request_digest: str,
        filename: str,
        mime_type: str,
        size_bytes: int,
        content_hash: str,
        storage_key: str,
        alt_text: str,
        metadata: dict[str, Any],
    ) -> tuple[MediaRecord, UUID, bool]:
        operation_id = uuid4()
        async with asyncpg_cow_session(
            self.cow_pool(), session_id=context.workspace_id, operation_id=operation_id
        ) as cow:
            reservation = await cow.native.fetchrow(
                MEDIA_IDEMPOTENCY_BEGIN_SQL,
                context.workspace_id,
                context.human_user_id,
                context.site_id,
                context.session_id,
                context.permission,
                idempotency_key,
                request_digest,
                operation_id,
            )
            state = str(reservation[0]) if reservation is not None else "UNAVAILABLE"
            if state == "MISMATCH":
                raise MediaIdempotencyMismatchError()
            if state == "REPLAY":
                body = reservation[3]
                if isinstance(body, str):
                    body = json.loads(body)
                return _record_from_dict(body["record"]), reservation[1], True
            if state != "STARTED":
                raise RuntimeError("media idempotency unavailable")
            row = await cow.native.fetchrow(
                MEDIA_REGISTER_SQL,
                context.site_id,
                context.human_user_id,
                context.session_id,
                context.permission,
                filename,
                mime_type,
                size_bytes,
                content_hash,
                storage_key,
                alt_text,
                json.dumps(metadata, sort_keys=True),
                context.workspace_id,
                context.human_user_id,
            )
            if row is None:
                raise RuntimeError("media registration unavailable")
            record = _record(row)
            response_body = json.dumps(
                {"record": record_to_dict(record), "operation_id": str(reservation[1])},
                sort_keys=True,
            )
            await cow.native.fetchrow(
                MEDIA_IDEMPOTENCY_COMPLETE_SQL,
                context.workspace_id,
                context.human_user_id,
                context.site_id,
                context.session_id,
                context.permission,
                idempotency_key,
                request_digest,
                reservation[1],
                201,
                response_body,
                "POST /media/v1/assets",
                "media_asset",
                record.id,
            )
            return record, reservation[1], False

    async def get(
        self, *, context: MediaAuthContext, media_id: UUID
    ) -> MediaRecord | None:
        async with asyncpg_cow_session(
            self.cow_pool(), session_id=context.workspace_id
        ) as cow:
            row = await cow.native.fetchrow(
                MEDIA_GET_SQL,
                context.site_id,
                media_id,
                context.human_user_id,
                context.session_id,
                context.permission,
                context.workspace_id,
            )
            return None if row is None else _record(row)


def _record(row: Any) -> MediaRecord:
    import json

    return MediaRecord(
        id=row[0],
        site_id=row[1],
        uploaded_by=row[2],
        filename=row[3],
        mime_type=row[4],
        size_bytes=row[5],
        content_hash=row[6],
        storage_key=row[7],
        alt_text=row[8],
        metadata=json.loads(row[9]) if isinstance(row[9], str) else row[9],
        created_at=row[10],
        updated_at=row[11],
    )


def _record_from_dict(value: dict[str, Any]) -> MediaRecord:
    from datetime import datetime

    return MediaRecord(
        id=UUID(value["id"]),
        site_id=UUID(value["site_id"]),
        uploaded_by=UUID(value["uploaded_by"]),
        filename=value["filename"],
        mime_type=value["mime_type"],
        size_bytes=value["size_bytes"],
        content_hash=value["content_hash"],
        storage_key=value["storage_key"],
        alt_text=value["alt_text"],
        metadata=value["metadata"],
        created_at=datetime.fromisoformat(value["created_at"]),
        updated_at=datetime.fromisoformat(value["updated_at"]),
    )


def record_to_dict(record: MediaRecord) -> dict[str, Any]:
    return {
        "id": str(record.id),
        "site_id": str(record.site_id),
        "uploaded_by": str(record.uploaded_by),
        "filename": record.filename,
        "mime_type": record.mime_type,
        "size_bytes": record.size_bytes,
        "content_hash": record.content_hash,
        "storage_key": record.storage_key,
        "alt_text": record.alt_text,
        "metadata": record.metadata,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
    }


__all__ = [
    "MediaAuthContext",
    "MediaDatabase",
    "MediaIdempotencyMismatchError",
    "MediaRecord",
    "record_to_dict",
]
