"""Real PostgreSQL proof for Render preview touch and lock chronology."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.identity.sessions import format_session_token
from slaif_agent_site.render_api.projection import (
    RenderPreviewRequest,
    RenderProjectionService,
)
from slaif_agent_site.sites import CreateSiteRequest, SiteService
from slaif_agent_site.sites.resolver import SiteResolver

IDLE_SECONDS = 1800
TOUCH_SECONDS = 300
RECENT_AUTH_SECONDS = 900


class _RenderAdapter:
    def __init__(self, public_pool: object, preview_pool: object) -> None:
        self._public_pool = public_pool
        self._preview_pool = preview_pool
        self._resolver = SiteResolver(public_pool)  # type: ignore[arg-type]
        self.acquire_timeout = 3.0

    def resolver(self) -> SiteResolver:
        return self._resolver

    def public_pool(self) -> object:
        return self._public_pool

    def preview_pool(self) -> object:
        return self._preview_pool

    @property
    def preview_policy(self) -> tuple[int, int, int]:
        return IDLE_SECONDS, TOUCH_SECONDS, RECENT_AUTH_SECONDS


async def _wait_for_advisory_waiter(
    administrator: asyncpg.Connection[Any], pid: int
) -> None:
    for _ in range(500):
        row = await administrator.fetchrow(
            "SELECT wait_event_type, wait_event, state "
            "FROM pg_catalog.pg_stat_activity WHERE pid = $1",
            pid,
        )
        if row is not None and tuple(row) == ("Lock", "advisory", "active"):
            return
        await asyncio.sleep(0.01)
    raise AssertionError("preview connection did not wait on the workspace lock")


async def _authorize(
    connection: Any,
    *,
    public_id: str,
    secret_digest: bytes,
    workspace_id: UUID,
    site_id: UUID,
) -> Any:
    return await connection.fetchrow(
        "SELECT * FROM control.slaif_render_preview_authorize($1,$2,$3,$4,$5,$6,$7)",
        public_id,
        secret_digest,
        workspace_id,
        site_id,
        IDLE_SECONDS,
        TOUCH_SECONDS,
        RECENT_AUTH_SECONDS,
    )


async def _residue(connection: Any) -> tuple[int, int, int, int]:
    row = await connection.fetchrow(
        "SELECT (SELECT count(*) FROM content.page_changes), "
        "(SELECT count(*) FROM control.human_editor_idempotency), "
        "(SELECT count(*) FROM audit.human_editor_mutation), "
        "(SELECT count(*) FROM content.cow_dirty_tables)"
    )
    return tuple(row)


async def test_preview_touch_never_renews_recent_auth_and_locks_first(
    agent_site_database: AgentSiteDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    preview_pool = await database.role_pool("slaif_preview_reader")
    public_pool = await database.role_pool("slaif_public_reader")
    site = await SiteService(control_pool).create(
        CreateSiteRequest(
            site_key=f"lock-{uuid4().hex[:10]}",
            display_name="Preview Lock",
            default_locale="en",
        )
    )
    user_id, session_id, workspace_id = uuid4(), uuid4(), uuid4()
    secret = b"l" * 32
    public_id = f"sas2_{session_id.hex}"
    expires = datetime.now(UTC) + timedelta(hours=1)
    owner_dsn = database.settings.resolved_owner_dsn()
    try:
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO control.user_account "
                "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
                "VALUES ($1, 'OIDC', 'https://lock.test', $2, 'Lock User')",
                user_id,
                f"subject-{user_id}",
            )
            await owner.execute(
                "INSERT INTO control.site_membership "
                "(site_id, user_account_id, role_key, delegation_ceiling) "
                "VALUES ($1, $2, 'SITE_EDITOR', 2)",
                site.site_id,
                user_id,
            )
            await owner.execute(
                "INSERT INTO control.user_session "
                "(id, public_id, secret_digest, csrf_secret_digest, user_account_id, "
                "absolute_expires_at) VALUES ($1, $2, $3, $4, $5, $6)",
                session_id,
                public_id,
                hashlib.sha256(secret).digest(),
                b"c" * 32,
                user_id,
                expires,
            )
            await owner.execute(
                "INSERT INTO control.workspace "
                "(id, site_id, created_by, actor_type, title, delegation_preset, "
                "status, expires_at) VALUES ($1, $2, $3, 'HUMAN', 'Lock', "
                "'L2_SITE_EDITOR', 'ACTIVE', $4)",
                workspace_id,
                site.site_id,
                user_id,
                expires,
            )
            page_id = await owner.fetchval(
                "INSERT INTO content.page_base "
                "(site_id, slug, title, status, locale) VALUES "
                "($1, 'home', 'Lock page', 'PUBLISHED', 'en') RETURNING id",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_composition_base "
                "(site_id, page_id, component_type, schema_version, slot_key, "
                "order_key, props) VALUES ($1, $2, 'Heading', '1', 'default', "
                '0, \'{"text":"Lock","level":2}\'::jsonb)',
                site.site_id,
                page_id,
            )

        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.user_session SET "
                "created_at = CURRENT_TIMESTAMP - interval '1 hour', "
                "last_seen_at = CURRENT_TIMESTAMP - interval '10 minutes', "
                "recent_auth_at = CURRENT_TIMESTAMP - interval '20 minutes' "
                "WHERE id = $1",
                session_id,
            )
            before = await owner.fetchrow(
                "SELECT last_seen_at, recent_auth_at FROM control.user_session "
                "WHERE id = $1",
                session_id,
            )
        async with preview_pool.acquire() as preview:
            first = await _authorize(
                preview,
                public_id=public_id,
                secret_digest=hashlib.sha256(secret).digest(),
                workspace_id=workspace_id,
                site_id=site.site_id,
            )
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            after_first = await owner.fetchrow(
                "SELECT last_seen_at, recent_auth_at FROM control.user_session "
                "WHERE id = $1",
                session_id,
            )
        assert first is not None
        assert first[6] is False
        assert after_first[0] > before[0]
        assert after_first[1] == before[1]

        async with preview_pool.acquire() as preview:
            second = await _authorize(
                preview,
                public_id=public_id,
                secret_digest=hashlib.sha256(secret).digest(),
                workspace_id=workspace_id,
                site_id=site.site_id,
            )
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            after_second = await owner.fetchrow(
                "SELECT last_seen_at, recent_auth_at FROM control.user_session "
                "WHERE id = $1",
                session_id,
            )
        assert second is not None
        assert second[6] is False
        assert after_second[1] == before[1]

        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.user_session SET "
                "last_seen_at = CURRENT_TIMESTAMP - interval '10 minutes', "
                "recent_auth_at = CURRENT_TIMESTAMP - interval '1 minute' "
                "WHERE id = $1",
                session_id,
            )
            recent_before = await owner.fetchval(
                "SELECT recent_auth_at FROM control.user_session WHERE id = $1",
                session_id,
            )
        async with preview_pool.acquire() as preview:
            recent = await _authorize(
                preview,
                public_id=public_id,
                secret_digest=hashlib.sha256(secret).digest(),
                workspace_id=workspace_id,
                site_id=site.site_id,
            )
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            recent_after = await owner.fetchval(
                "SELECT recent_auth_at FROM control.user_session WHERE id = $1",
                session_id,
            )
        assert recent is not None
        assert recent[6] is True
        assert recent_after == recent_before

        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            baseline = await _residue(owner)

        async with preview_pool.acquire() as preview:
            async with owner_connection(
                owner_dsn, expected_database=database.name
            ) as lock_owner:
                async with lock_owner.transaction():
                    await lock_owner.fetchval(
                        "SELECT pg_advisory_xact_lock(hashtextextended($1, 280))",
                        str(workspace_id),
                    )
                    blocked = asyncio.create_task(
                        _authorize(
                            preview,
                            public_id=public_id,
                            secret_digest=hashlib.sha256(secret).digest(),
                            workspace_id=workspace_id,
                            site_id=site.site_id,
                        )
                    )
                    await _wait_for_advisory_waiter(
                        database.administrator, preview.get_server_pid()
                    )
                    async with owner_connection(
                        owner_dsn, expected_database=database.name
                    ) as mutator:
                        await asyncio.wait_for(
                            mutator.execute(
                                "UPDATE control.user_session SET revoked_at = "
                                "CURRENT_TIMESTAMP WHERE id = $1",
                                session_id,
                            ),
                            timeout=3,
                        )
                    assert not blocked.done()
                denied = await asyncio.wait_for(blocked, timeout=3)
        assert denied is None
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            assert await _residue(owner) == baseline

        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.user_session SET revoked_at = NULL, "
                "last_seen_at = CURRENT_TIMESTAMP WHERE id = $1",
                session_id,
            )
        adapter = _RenderAdapter(public_pool, preview_pool)
        service = RenderProjectionService(adapter)
        query_started = asyncio.Event()
        release_query = asyncio.Event()
        original_query = service._query

        async def paused_query(*args: Any, **kwargs: Any) -> Any:
            query_started.set()
            await release_query.wait()
            return await original_query(*args, **kwargs)

        monkeypatch.setattr(service, "_query", paused_query)
        preview_task = asyncio.create_task(
            service.preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path="/s/" + site.site_key + "/",
                    workspace_id=workspace_id,
                    session_token=format_session_token(public_id, secret),
                )
            )
        )
        await asyncio.wait_for(query_started.wait(), timeout=3)
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as lock_owner:
            async with lock_owner.transaction():
                lock_task = asyncio.create_task(
                    lock_owner.fetchval(
                        "SELECT pg_advisory_xact_lock(hashtextextended($1, 280))",
                        str(workspace_id),
                    )
                )
                await _wait_for_advisory_waiter(
                    database.administrator, lock_owner.get_server_pid()
                )
                assert not lock_task.done()
                release_query.set()
                projection = await asyncio.wait_for(preview_task, timeout=3)
                await asyncio.wait_for(lock_task, timeout=3)
        assert projection.render_mode == "preview"
    finally:
        await public_pool.close()
        await preview_pool.close()
        await control_pool.close()
