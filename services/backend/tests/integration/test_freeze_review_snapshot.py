"""Real PostgreSQL proof for durable freeze jobs and the immutable snapshot."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import importlib
import json
import re
import time
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_reviewer,
    asyncpg_cow_session,
    get_session_operations,
)
from slaif_agent_site.bootstrap.service import (
    BootstrapStateError,
    reconcile,
    upgrade,
)
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.content_model.canonical import (
    canonical_digest,
    parse_snapshot_text,
)
from slaif_agent_site.content_model.design_system import (
    CATALOG_VERSION,
    COMPOSITION_SCHEMA_VERSION,
    DESIGN_SYSTEM_VERSION,
    RENDERER_VERSION,
)
from slaif_agent_site.control_api.app import create_app
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration
from slaif_agent_site.db.roles import ROLE_NAMES
from slaif_agent_site.identity.sessions import format_session_token
from slaif_agent_site.render_api.app import create_app as create_render_app
from slaif_agent_site.review_worker.accept_job import (
    MediaBoundary,
    run_accept_job,
)
from slaif_agent_site.review_worker.config import (
    REVIEW_WORKER_CONTENT_MODEL_SCHEMA_VERSION,
    ReviewWorkerDatabaseMode,
    ReviewWorkerSettings,
)
from slaif_agent_site.review_worker.discard_job import run_discard_job
from slaif_agent_site.review_worker.freeze_job import run_freeze_job
from slaif_agent_site.review_worker.snapshot import (
    PUCK_VERSION_PIN,
    build_snapshot_document,
    canonical_json,
)
from test_real_human_accept import (
    _claim_accept,
    _enqueue_accept,
    _media_settings,
    _seed_site,
)
from test_render_projection_integration import _RestartableRenderAdapter

_CURRENT_VERSION_FACTS = r""" '{"catalog":"catalog-v1",'

    '"composition_schema":"site-composition/v1",'
    '"content_model":"content-model/v1","design_system":"design-system/v1",'
    '"puck":"0.20.2","renderer":"renderer-v1"}'::jsonb"""
_AGGON2 = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "AAAAAAAAAAAAAAAAAAAAAA$"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
)


def _dsn(database: AgentSiteDatabase, user: str, password: str) -> str:
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    return (
        f"postgresql://{quote(user, safe='')}:{quote(password, safe='')}@"
        f"{host}:{database.connection_parameters['port']}/{database.name}"
    )


def _worker_settings(database: AgentSiteDatabase) -> ReviewWorkerSettings:
    login, password = database.credentials["slaif_review_worker"]
    return ReviewWorkerSettings(
        mode=ReviewWorkerDatabaseMode.TEST,
        dsn=SecretStr(_dsn(database, login, password)),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        staleness_seconds=60.0,
        drain_lock_timeout_seconds=30.0,
        evidence_deadline_seconds=120.0,
    )


async def _worker_pool(database: AgentSiteDatabase) -> asyncpg.Pool[Any]:
    login, password = database.credentials["slaif_review_worker"]
    return await asyncpg.create_pool(
        dsn=_dsn(database, login, password), min_size=1, max_size=2
    )


async def _seed(database: AgentSiteDatabase) -> dict[str, UUID]:
    """Upgrade to head and seed one site with renderable content."""

    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        delegator_id = await owner.fetchval(
            """
            INSERT INTO control.user_account (
                id, identity_kind, local_username, local_username_normalized,
                password_hash, display_name, status
            ) VALUES (
                gen_random_uuid(), 'LOCAL', 'Freeze.Integration.Delegator',
                'freeze.integration.delegator', $1, 'Freeze Delegator', 'ACTIVE'
            ) RETURNING id
            """,
            _AGGON2,
        )
        site_id = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name, default_locale,"
            " component_catalog_version) VALUES ('freeze-int', 'Freeze Int',"
            " 'en-US', 'catalog-v1') RETURNING id"
        )
        await owner.execute(
            "INSERT INTO control.site_membership (site_id,user_account_id,"
            " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
            site_id,
            delegator_id,
        )
        await owner.execute(
            "INSERT INTO content.site_locale_base (site_id,tag,enabled,is_default,"
            " position) VALUES ($1,'en-US',true,true,0)",
            site_id,
        )
        await owner.execute(
            "INSERT INTO content.theme_base (id, site_id, schema_version,"
            " renderer_version, palette, typography, layout, shape) VALUES"
            " (gen_random_uuid(), $1, 'theme-schema/v1', 'renderer-v1',"
            ' \'{"preset":"ocean"}\'::jsonb,'
            ' \'{"family":"system",'
            '"scale":"balanced","weight":"regular"}\'::jsonb,'
            ' \'{"content_width":"md",'
            '"spacing":"md","grid_gap":"md"}\'::jsonb,'
            ' \'{"radius":"md","shadow":"sm"}\'::jsonb)',
            site_id,
        )
        media_id = uuid4()
        await owner.execute(
            "INSERT INTO content.media_asset_base (id, site_id, uploaded_by,"
            " filename, mime_type, size_bytes, content_hash, storage_key,"
            " alt_text, metadata) VALUES ($1,$2,$3,'int.png','image/png',128,"
            " $4, 'sha256/' || substring($4, 1, 2) || '/' ||"
            " substring($4, 3, 2) || '/' || $4, 'Alt', '{}'::jsonb)",
            media_id,
            site_id,
            delegator_id,
            "a" * 64,
        )
        page_id = uuid4()
        await owner.execute(
            "INSERT INTO content.page_base (id, site_id, slug, title, status,"
            " locale) VALUES ($1,$2,'home','Home','PUBLISHED','en-US')",
            page_id,
            site_id,
        )
        section_id = uuid4()
        heading_id = uuid4()
        image_id = uuid4()
        await owner.execute(
            "INSERT INTO content.page_composition_base (id, site_id, page_id,"
            " component_type, schema_version, parent_id, slot_key, order_key,"
            " props) VALUES"
            " ($1,$2,$3,'Section','1',NULL,'default',0,'{}'::jsonb),"
            " ($4,$2,$3,'Heading','1',$1,'default',0,"
            '  \'{"level":1,"text":"Freeze"}\'::jsonb),'
            " ($5,$2,$3,'Image','1',$1,'default',1,"
            "  jsonb_build_object('mediaId',$6::text,'alt','Alt'))",
            section_id,
            site_id,
            page_id,
            heading_id,
            image_id,
            str(media_id),
        )
        workspace_id = await owner.fetchval(
            "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
            " title, delegation_preset, effective_scopes, version_facts,"
            " status, expires_at)"
            " VALUES ($1,$2,$2,'Freeze Workspace','L4',"
            " '[\"page:read\"]'::jsonb," + _CURRENT_VERSION_FACTS + ","
            " 'ACTIVE',now()+interval '1 hour')"
            " RETURNING id",
            site_id,
            delegator_id,
        )
        token, public_id, digest = generate_capability_token()
        await owner.execute(
            "INSERT INTO control.capability (workspace_id, public_id,"
            " secret_digest, scopes, expires_at) VALUES ($1,$2,$3,"
            " '[\"page:read\"]'::jsonb, now()+interval '30 minutes')",
            workspace_id,
            public_id,
            digest,
        )
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE public_id = $1", public_id
        )
    return {
        "delegator_id": UUID(str(delegator_id)),
        "site_id": UUID(str(site_id)),
        "workspace_id": UUID(str(workspace_id)),
        "capability_id": UUID(str(capability_id)),
        "page_id": page_id,
        "section_id": section_id,
        "media_id": media_id,
    }


class _ConnExecutor:
    """The narrow executor surface the foundation operations API takes."""

    def __init__(self, connection: asyncpg.Connection[Any]) -> None:
        self._connection = connection

    async def execute(self, sql: str) -> list[tuple[Any, ...]]:
        return [tuple(row) for row in await self._connection.fetch(sql)]


async def _control_call(
    database: AgentSiteDatabase, sql: str, *arguments: Any
) -> list[Any]:
    login, password = database.credentials["slaif_control"]
    connection = await asyncpg.connect(dsn=_dsn(database, login, password))
    try:
        return list(await connection.fetch(sql, *arguments))
    finally:
        await connection.close()


async def _worker_call(
    database: AgentSiteDatabase, sql: str, *arguments: Any
) -> list[Any]:
    login, password = database.credentials["slaif_review_worker"]
    connection = await asyncpg.connect(dsn=_dsn(database, login, password))
    try:
        return list(await connection.fetch(sql, *arguments))
    finally:
        await connection.close()


async def _freeze(
    database: AgentSiteDatabase,
    seeded: dict[str, UUID],
) -> tuple[UUID, str]:
    rows = await _control_call(
        database,
        "SELECT * FROM control.slaif_human_agent_workspace_freeze($1,$2,$3)",
        seeded["workspace_id"],
        seeded["site_id"],
        seeded["delegator_id"],
    )
    assert len(rows) == 1
    return UUID(str(rows[0]["job_id"])), str(rows[0]["status"])


@pytest.mark.asyncio
async def test_concurrent_claim_and_stale_recovery(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    seeded = await _seed(database)
    job_id, status = await _freeze(database, seeded)
    assert status == "FREEZING"

    settings = _worker_settings(database)

    async def claim(claimant: str) -> list[Any]:
        login, password = database.credentials["slaif_review_worker"]
        connection = await asyncpg.connect(dsn=_dsn(database, login, password))
        try:
            return list(
                await connection.fetch(
                    "SELECT * FROM control.slaif_review_job_claim($1, $2)",
                    claimant,
                    ["FREEZE", "ACCEPT"],
                )
            )
        finally:
            await connection.close()

    # Two worker connections race for the single QUEUED job: exactly one wins.
    first, second = await asyncio.gather(claim("race-1"), claim("race-2"))
    claimed = [rows for rows in (first, second) if rows]
    assert len(claimed) == 1
    row = claimed[0][0]
    assert UUID(str(row["id"])) == job_id
    assert row["status"] == "CLAIMED"
    assert row["attempt_count"] == 1
    assert row["claimed_by"] in {"race-1", "race-2"}

    async def age_heartbeat(seconds: float = 61.0) -> None:
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "UPDATE control.review_job SET last_heartbeat = now() - $1::interval"
                " WHERE id = $2",
                timedelta(seconds=seconds),
                job_id,
            )

    # Stale CLAIMED job is re-queued while attempts remain (attempt 2).
    await age_heartbeat()
    rows = await claim("recover-1")
    assert len(rows) == 1
    assert rows[0]["id"] == job_id
    assert rows[0]["attempt_count"] == 2
    assert rows[0]["claimed_by"] == "recover-1"

    # Second stale recovery consumes the last attempt (attempt 3 = max).
    await age_heartbeat()
    rows = await claim("recover-2")
    assert len(rows) == 1
    assert rows[0]["attempt_count"] == 3

    # At the budget the stale job is FAILED, not re-queued.
    await age_heartbeat()
    rows = await claim("recover-3")
    assert rows == []
    async with owner_connection(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
    ) as owner:
        terminal = await owner.fetchrow(
            "SELECT status, error, attempt_count FROM control.review_job WHERE id = $1",
            job_id,
        )
    assert terminal["status"] == "FAILED"
    assert terminal["error"] == "REVIEW_JOB_STALE_AT_BUDGET"
    assert terminal["attempt_count"] == 3
    assert settings.staleness_seconds == 60.0


@pytest.mark.asyncio
async def test_freeze_lifecycle_worker_snapshot(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    seeded = await _seed(database)

    # Idempotent freeze: two calls, one live job, one job row.
    job_id, status = await _freeze(database, seeded)
    again_id, again_status = await _freeze(database, seeded)
    assert (again_id, again_status) == (job_id, "FREEZING")
    async with owner_connection(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
    ) as owner:
        jobs = await owner.fetchval(
            "SELECT count(*) FROM control.review_job WHERE workspace_id = $1",
            seeded["workspace_id"],
        )
        revoked = await owner.fetchval(
            "SELECT count(*) FROM control.capability WHERE workspace_id = $1"
            " AND revoked_at IS NULL",
            seeded["workspace_id"],
        )
        workspace_status = await owner.fetchval(
            "SELECT status FROM control.workspace WHERE id = $1",
            seeded["workspace_id"],
        )
    assert jobs == 1
    assert revoked == 0
    assert workspace_status == "FREEZING"

    # The real worker path: narrow credential, durable claim, locked job run.
    pool = await _worker_pool(database)
    try:
        rows = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "integration-worker-1",
            ["FREEZE", "ACCEPT"],
        )
        assert len(rows) == 1
        job = dict(rows[0])
        assert str(job["id"]) == str(job_id)
        result = await run_freeze_job(pool, _worker_settings(database), job)
        assert result.status == "SUCCEEDED", result.error
    finally:
        await pool.close()

    async with owner_connection(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
    ) as owner:
        snapshot = await owner.fetchrow(
            "SELECT * FROM control.review_snapshot WHERE workspace_id = $1",
            seeded["workspace_id"],
        )
        snapshot_count = await owner.fetchval(
            "SELECT count(*) FROM control.review_snapshot WHERE workspace_id = $1",
            seeded["workspace_id"],
        )
        digest_ok = await owner.fetchval(
            "SELECT digest = encode(sha256(convert_to("
            " control.slaif_canonical_jsonb_text(payload),'UTF8')),'hex')"
            " FROM control.review_snapshot WHERE id = $1",
            snapshot["id"],
        )
        same_state = await owner.fetchval(
            "SELECT normalized_state = payload FROM control.review_snapshot"
            " WHERE id = $1",
            snapshot["id"],
        )
        workspace = await owner.fetchrow(
            "SELECT status, review_snapshot_id FROM control.workspace WHERE id = $1",
            seeded["workspace_id"],
        )
        job = await owner.fetchrow(
            "SELECT status, error FROM control.review_job WHERE id = $1", job_id
        )
    assert snapshot_count == 1
    assert digest_ok is True
    assert same_state is True
    assert workspace["status"] == "REVIEW"
    assert workspace["review_snapshot_id"] == snapshot["id"]
    assert job["status"] == "SUCCEEDED"
    assert job["error"] is None
    # asyncpg jsonb binding delivers canonical JSON text; decode for asserts.
    versions = json.loads(snapshot["versions"])
    assert versions["puck"] == PUCK_VERSION_PIN
    assert versions["renderer"] == "renderer-v1"
    payload = json.loads(snapshot["payload"])
    assert payload["state_version"] == "review-snapshot/v2"
    media_refs = json.loads(snapshot["media_references"])
    assert len(media_refs) == 1
    assert media_refs[0]["mime_type"] == "image/png"

    # The revoked capability is unusable (uniform P0002 denial).
    login, password = database.credentials["slaif_agent_runtime"]
    agent = await asyncpg.connect(dsn=_dsn(database, login, password))
    try:
        async with agent.transaction():
            await agent.execute(
                "SELECT set_config('app.session_id',$1,true)",
                str(seeded["workspace_id"]),
            )
            await agent.execute(
                "SELECT set_config('app.operation_id',$1,true)", str(uuid4())
            )
            await agent.execute(
                "SELECT set_config('app.capability_id',$1,true)",
                str(seeded["capability_id"]),
            )
            with pytest.raises(asyncpg.PostgresError) as excinfo:
                await agent.fetchval(
                    "SELECT count(*) FROM content.slaif_agent_page_list($1)",
                    seeded["site_id"],
                )
        assert excinfo.value.sqlstate == "P0002"
    finally:
        await agent.close()

    # Snapshot immutability: no long-lived role but the owner may
    # UPDATE/DELETE; the worker is INSERT-only.
    for role in ROLE_NAMES:
        expected_update = role == "slaif_owner"
        expected_delete = role == "slaif_owner"
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            can_update = await owner.fetchval(
                "SELECT has_table_privilege($1,'control.review_snapshot', 'UPDATE')",
                role,
            )
            can_delete = await owner.fetchval(
                "SELECT has_table_privilege($1,'control.review_snapshot', 'DELETE')",
                role,
            )
            job_update = await owner.fetchval(
                "SELECT has_table_privilege($1,'control.review_job','UPDATE')",
                role,
            )
        assert can_update is expected_update, role
        assert can_delete is expected_delete, role
        # Owner (table ownership) and worker (explicit grant) only.
        assert job_update is (role in ("slaif_owner", "slaif_review_worker")), role

    with pytest.raises(asyncpg.InsufficientPrivilegeError):
        await _worker_call(
            database,
            "UPDATE control.review_snapshot SET digest = digest WHERE id = $1",
            snapshot["id"],
        )


@pytest.mark.asyncio
async def test_forced_validation_failure_leaves_freezing(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    seeded = await _seed(database)
    job_id, _ = await _freeze(database, seeded)

    # Break the frozen composition: an unknown component type in the base.
    evil_node = uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
    ) as owner:
        await owner.execute(
            "INSERT INTO content.page_composition_base (id, site_id, page_id,"
            " component_type, schema_version, parent_id, slot_key, order_key,"
            " props) VALUES ($1,$2,$3,'EvilComponent','1',NULL,'default',5,"
            " '{}'::jsonb)",
            evil_node,
            seeded["site_id"],
            seeded["page_id"],
        )

    pool = await _worker_pool(database)
    try:
        rows = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "integration-worker-2",
            ["FREEZE", "ACCEPT"],
        )
        assert len(rows) == 1
        result = await run_freeze_job(pool, _worker_settings(database), dict(rows[0]))
        assert result.status == "FAILED"
        assert result.error == "SNAPSHOT_VALIDATION_FAILED"
    finally:
        await pool.close()

    async with owner_connection(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
    ) as owner:
        await owner.execute(
            "DELETE FROM content.page_composition_base WHERE id = $1", evil_node
        )
        workspace_status = await owner.fetchval(
            "SELECT status FROM control.workspace WHERE id = $1",
            seeded["workspace_id"],
        )
        snapshot_count = await owner.fetchval(
            "SELECT count(*) FROM control.review_snapshot WHERE workspace_id = $1",
            seeded["workspace_id"],
        )
        job = await owner.fetchrow(
            "SELECT status, error FROM control.review_job WHERE id = $1", job_id
        )
    # No REVIEW, no snapshot row, workspace remains FREEZING.
    assert workspace_status == "FREEZING"
    assert snapshot_count == 0
    assert job["status"] == "FAILED"
    assert job["error"] == "SNAPSHOT_VALIDATION_FAILED"

    # Tamper proof: a hand-built row with a wrong digest is rejected and
    # cannot reach REVIEW; then the repaired freeze completes for real.
    login, password = database.credentials["slaif_review_worker"]
    worker = await asyncpg.connect(dsn=_dsn(database, login, password))
    try:
        doc = await worker.fetchval(
            "SELECT control.slaif_review_workspace_state($1)",
            seeded["workspace_id"],
        )
        row = build_snapshot_document(doc, created_by="tamper-worker")
        row["digest"] = "0" * 64
        with pytest.raises(asyncpg.PostgresError) as excinfo:
            await worker.fetchval(
                "SELECT control.slaif_review_snapshot_complete($1,$2)",
                seeded["workspace_id"],
                canonical_json(row),
            )
        assert "SNAPSHOT_DIGEST_MISMATCH" in excinfo.value.message
        assert excinfo.value.sqlstate == "P0002"
    finally:
        await worker.close()

    # The corrected freeze (idempotent new live job) completes to REVIEW.
    new_job_id, status = await _freeze(database, seeded)
    assert status == "FREEZING"
    pool = await _worker_pool(database)
    try:
        rows = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "integration-worker-3",
            ["FREEZE", "ACCEPT"],
        )
        assert len(rows) == 1
        assert str(rows[0]["id"]) == str(new_job_id)
        result = await run_freeze_job(pool, _worker_settings(database), dict(rows[0]))
        assert result.status == "SUCCEEDED", result.error
    finally:
        await pool.close()
    async with owner_connection(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
    ) as owner:
        workspace_status = await owner.fetchval(
            "SELECT status FROM control.workspace WHERE id = $1",
            seeded["workspace_id"],
        )
        snapshot_count = await owner.fetchval(
            "SELECT count(*) FROM control.review_snapshot WHERE workspace_id = $1",
            seeded["workspace_id"],
        )
    assert workspace_status == "REVIEW"
    assert snapshot_count == 1
    assert new_job_id != job_id


@pytest.mark.asyncio
async def test_lock_serialization_and_r4_shared_lock(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    seeded = await _seed(database)
    workspace_key = str(seeded["workspace_id"])

    # Drain proof: a mutation transaction holding the shared 280 lock blocks
    # the exclusive freeze lock until it commits (bounded by lock_timeout).
    owner_login, owner_password = database.credentials["slaif_owner"]
    blocker = await asyncpg.connect(dsn=_dsn(database, owner_login, owner_password))
    await blocker.execute("SET ROLE slaif_owner")
    contender = await asyncpg.connect(dsn=_dsn(database, owner_login, owner_password))
    await contender.execute("SET ROLE slaif_owner")
    try:
        async with blocker.transaction():
            await blocker.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended($1::text, 280))",
                workspace_key,
            )
            started = time.monotonic()

            async def try_exclusive() -> str | None:
                try:
                    async with contender.transaction():
                        await contender.execute("SET LOCAL lock_timeout = '1500ms'")
                        await contender.execute(
                            "SELECT pg_advisory_xact_lock("
                            "hashtextextended($1::text, 280))",
                            workspace_key,
                        )
                    return None
                except asyncpg.PostgresError as error:
                    sqlstate = error.sqlstate
                    return sqlstate if isinstance(sqlstate, str) else None

            sqlstate = await try_exclusive()
            assert sqlstate == "55P03"  # lock_timeout, no deadlock
            await asyncio.sleep(1.0)
            # The blocker still holds the lock; release lets the contender in.
        # Blocker committed: the same exclusive lock now acquires at once.
        sqlstate = await try_exclusive()
        assert sqlstate is None
        assert time.monotonic() - started >= 1.0

        # R4 proof: a real Agent data-plane gate transaction holds the
        # shared 280 lock (observable in pg_locks) until it commits.
        agent_login, agent_password = database.credentials["slaif_agent_runtime"]
        agent = await asyncpg.connect(dsn=_dsn(database, agent_login, agent_password))
        try:
            agent_pid = await agent.fetchval("SELECT pg_backend_pid()")
            key = await agent.fetchval(
                "SELECT hashtextextended($1::text, 280)", workspace_key
            )
            # pg_locks stores advisory keys as unsigned 32-bit halves.
            key_high = int(key) >> 32 & 0xFFFFFFFF
            key_low = int(key) & 0xFFFFFFFF
            async with agent.transaction():
                await agent.execute(
                    "SELECT set_config('app.session_id',$1,true)",
                    workspace_key,
                )
                await agent.execute(
                    "SELECT set_config('app.operation_id',$1,true)", str(uuid4())
                )
                await agent.execute(
                    "SELECT set_config('app.capability_id',$1,true)",
                    str(seeded["capability_id"]),
                )
                await agent.fetchval(
                    "SELECT count(*) FROM content.slaif_agent_page_list($1)",
                    seeded["site_id"],
                )
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as observer:
                    count = await observer.fetchval(
                        "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory'"
                        " AND mode = 'ShareLock' AND pid = $1"
                        " AND classid = $2 AND objid = $3",
                        agent_pid,
                        key_high,
                        key_low,
                    )
            assert count >= 1
        finally:
            await agent.close()
    finally:
        await blocker.close()
        await contender.close()


async def _control_http(
    database: AgentSiteDatabase,
) -> tuple[Any, httpx.AsyncClient]:
    """Control-plane app over the scratch database (established pattern)."""

    login, password = database.credentials["slaif_control"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    settings = ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
            f"{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=4,
        application_name="slaif-freeze-http-test",
    )
    adapter = ControlDatabase(settings)
    await adapter.start()
    app = create_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST), database=adapter
    )
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://control.test"
    )
    return adapter, client


async def _session_cookie(adapter: Any, user_account_id: UUID) -> tuple[str, str]:
    issued = await adapter.human_session_service().create(user_account_id)
    cookie = f"slaif_session={issued.token.get_secret_value()}"
    return cookie, issued.csrf_token.get_secret_value()


def _mutation_headers(cookie: str, csrf: str) -> dict[str, str]:
    return {"cookie": f"{cookie}; slaif_csrf={csrf}", "x-csrf-token": csrf}


@pytest.mark.asyncio
async def test_freeze_endpoint_http_authorization_csrf_and_state_matrix(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    seeded = await _seed(database)
    adapter, client = await _control_http(database)
    try:
        cookie, csrf = await _session_cookie(adapter, seeded["delegator_id"])
        base = (
            f"/api/control/v1/sites/{seeded['site_id']}/workspaces/"
            f"{seeded['workspace_id']}/freeze/"
        )
        happy = _mutation_headers(cookie, csrf)

        # Unauthenticated and invalid-session attempts are uniform 401.
        for headers in ({}, {"cookie": "slaif_session=invalid"}):
            response = await client.post(base, headers=headers)
            assert response.status_code == 401

        # State-changing route without/with wrong/duplicate CSRF: 403.
        response = await client.post(base, headers={"cookie": cookie})
        assert response.status_code == 403
        response = await client.post(
            base,
            headers={"cookie": f"{cookie}; slaif_csrf=wrong", "x-csrf-token": "wrong"},
        )
        assert response.status_code == 403
        response = await client.post(
            base,
            headers=[
                ("cookie", f"{cookie}; slaif_csrf={csrf}"),
                ("x-csrf-token", csrf),
                ("x-csrf-token", csrf),
            ],
        )
        assert response.status_code == 403

        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            editor_id = await owner.fetchval(
                "INSERT INTO control.user_account (id, identity_kind, "
                "local_username, local_username_normalized, password_hash, "
                "display_name, status) VALUES (gen_random_uuid(), 'LOCAL', "
                "'Freeze.Integration.Editor', 'freeze.integration.editor', $1, "
                "'Freeze Editor', 'ACTIVE') RETURNING id",
                _AGGON2,
            )
            nonmember_id = await owner.fetchval(
                "INSERT INTO control.user_account (id, identity_kind, "
                "local_username, local_username_normalized, password_hash, "
                "display_name, status) VALUES (gen_random_uuid(), 'LOCAL', "
                "'Freeze.Integration.Nonmember', 'freeze.integration.nonmember', "
                "$1, 'Freeze Nonmember', 'ACTIVE') RETURNING id",
                _AGGON2,
            )
            await owner.execute(
                "INSERT INTO control.site_membership (site_id,user_account_id,"
                " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_EDITOR',2)",
                seeded["site_id"],
                editor_id,
            )
            # Second site for the exact-binding probe: the delegator owns it.
            other_site_id = await owner.fetchval(
                "INSERT INTO control.site (site_key, display_name, "
                "default_locale, component_catalog_version) VALUES "
                "('freeze-other', 'Freeze Other', 'en-US', 'catalog-v1') "
                "RETURNING id"
            )
            await owner.execute(
                "INSERT INTO control.site_membership (site_id,user_account_id,"
                " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
                other_site_id,
                seeded["delegator_id"],
            )

        # A member without workspace:freeze and a non-member are denied
        # with the same uniform 404 shape (the established control-plane
        # no-oracle pattern: permission denial is indistinguishable from
        # not-found).
        editor_cookie, editor_csrf = await _session_cookie(adapter, editor_id)
        editor_denial = await client.post(
            base, headers=_mutation_headers(editor_cookie, editor_csrf)
        )
        assert editor_denial.status_code == 404
        nonmember_cookie, nonmember_csrf = await _session_cookie(adapter, nonmember_id)
        nonmember_denial = await client.post(
            base, headers=_mutation_headers(nonmember_cookie, nonmember_csrf)
        )
        assert nonmember_denial.status_code == 404
        editor_shape = editor_denial.json()
        nonmember_shape = nonmember_denial.json()
        editor_shape["error"].pop("request_id")
        nonmember_shape["error"].pop("request_id")
        assert editor_shape == nonmember_shape

        # Malformed path id follows the established control-plane 422
        # validation contract; unknown (well-formed) ids are 404.
        response = await client.post(
            f"/api/control/v1/sites/{seeded['site_id']}/workspaces/not-a-uuid/freeze/",
            headers=happy,
        )
        assert response.status_code == 422
        response = await client.post(
            f"/api/control/v1/sites/{seeded['site_id']}/workspaces/{uuid4()}/freeze/",
            headers=happy,
        )
        assert response.status_code == 404

        # Exact site binding: the workspace under another path site is 404
        # even for its owner (fail-closed, no cross-site substitution).
        response = await client.post(
            f"/api/control/v1/sites/{other_site_id}/workspaces/"
            f"{seeded['workspace_id']}/freeze/",
            headers=happy,
        )
        assert response.status_code == 404

        # Happy path: 202 with the live job; idempotent while FREEZING.
        response = await client.post(base, headers=happy)
        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "FREEZING"
        job_id = body["job_id"]
        response = await client.post(base, headers=happy)
        assert response.status_code == 202
        assert response.json() == {"job_id": job_id, "status": "FREEZING"}

        # After the worker completes the snapshot, re-freeze is 409.
        pool = await _worker_pool(database)
        try:
            rows = await _worker_call(
                database,
                "SELECT * FROM control.slaif_review_job_claim($1, $2)",
                "freeze-http-worker",
                ["FREEZE", "ACCEPT"],
            )
            assert len(rows) == 1
            result = await run_freeze_job(
                pool, _worker_settings(database), dict(rows[0])
            )
            assert result.status == "SUCCEEDED", result.error
        finally:
            await pool.close()
        response = await client.post(base, headers=happy)
        assert response.status_code == 409
    finally:
        await client.aclose()
        await adapter.stop()


# ---------------------------------------------------------------------
# 083/4: freeze-time canonical revision coherence
# ---------------------------------------------------------------------

_WORKER_KINDS_0834 = ["FREEZE", "ACCEPT"]
_MUTATION_SCOPES = [
    "site:read",
    "page:read",
    "component-structure:create",
    "component-content-props:write",
]
_FUNCTION_LOOKUP = (
    "SELECT pg_get_functiondef(p.oid) FROM pg_proc AS p"
    " JOIN pg_namespace AS n ON n.oid = p.pronamespace"
    " WHERE n.nspname = 'control'"
    " AND p.proname = 'slaif_review_workspace_state'"
)
_ACL_LOOKUP = (
    "SELECT r.rolname, has_function_privilege(r.rolname,"
    " 'control.slaif_review_workspace_state(uuid)', 'EXECUTE')"
    " FROM pg_roles AS r"
)
# Waiter detection is activity-based: a row-lock wait is frequently
# satisfied/queued through fast-path structures that never appear in
# pg_locks, so candidates are identified through pg_stat_activity
# (active state + current query) and the REAL blocking relationship is
# proven with pg_blocking_pids against the observed blocker PID.
_ACTIVITY_SQL = (
    "SELECT a.pid AS pid, a.query AS query"
    " FROM pg_catalog.pg_stat_activity AS a"
    " WHERE a.datname = current_database()"
    " AND a.pid <> pg_backend_pid()"
    " AND a.state = 'active'"
)
_BLOCKING_PIDS_SQL = "SELECT pg_catalog.pg_blocking_pids($1)"


async def _seed_raw(database: AgentSiteDatabase, owner: Any) -> dict[str, Any]:
    """One renderable site + L4 workspace + capability (no upgrade call)."""

    media_id = uuid4()
    page_id = uuid4()
    section_id = uuid4()
    heading_id = uuid4()
    image_id = uuid4()
    delegator_id = await owner.fetchval(
        """
        INSERT INTO control.user_account (
            id, identity_kind, local_username, local_username_normalized,
            password_hash, display_name, status
        ) VALUES (
            gen_random_uuid(), 'LOCAL', 'Repro083.4.Delegator',
            'repro083.4.delegator', $1, '083/4 Delegator', 'ACTIVE'
        ) RETURNING id
        """,
        _AGGON2,
    )
    site_id = await owner.fetchval(
        "INSERT INTO control.site (site_key, display_name, default_locale,"
        " component_catalog_version) VALUES ('083-4-repro', '083/4 Repro',"
        " 'en-US', 'catalog-v1') RETURNING id"
    )
    await owner.execute(
        "INSERT INTO control.site_membership (site_id,user_account_id,"
        " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
        site_id,
        delegator_id,
    )
    await owner.execute(
        "INSERT INTO content.site_locale_base (site_id,tag,enabled,is_default,"
        " position) VALUES ($1,'en-US',true,true,0)",
        site_id,
    )
    await owner.execute(
        "INSERT INTO content.theme_base (id, site_id, schema_version,"
        " renderer_version, palette, typography, layout, shape) VALUES"
        " (gen_random_uuid(), $1, 'theme-schema/v1', 'renderer-v1',"
        ' \'{"preset":"ocean"}\'::jsonb,'
        ' \'{"family":"system",'
        '"scale":"balanced","weight":"regular"}\'::jsonb,'
        ' \'{"content_width":"md",'
        '"spacing":"md","grid_gap":"md"}\'::jsonb,'
        ' \'{"radius":"md","shadow":"sm"}\'::jsonb)',
        site_id,
    )
    await owner.execute(
        "INSERT INTO content.media_asset_base (id, site_id, uploaded_by,"
        " filename, mime_type, size_bytes, content_hash, storage_key,"
        " alt_text, metadata) VALUES ($1,$2,$3,'repro.png','image/png',128,"
        " $4, 'sha256/' || substring($4, 1, 2) || '/' ||"
        " substring($4, 3, 2) || '/' || $4, 'Alt', '{}'::jsonb)",
        media_id,
        site_id,
        delegator_id,
        "a" * 64,
    )
    await owner.execute(
        "INSERT INTO content.page_base (id, site_id, slug, title, status,"
        " locale) VALUES ($1,$2,'home','Home','PUBLISHED','en-US')",
        page_id,
        site_id,
    )
    await owner.execute(
        "INSERT INTO content.page_composition_base (id, site_id, page_id,"
        " component_type, schema_version, parent_id, slot_key, order_key,"
        " props) VALUES"
        " ($1,$2,$3,'Section','1',NULL,'default',0,'{}'::jsonb),"
        " ($4,$2,$3,'Heading','1',$1,'default',0,"
        '  \'{"level":1,"text":"Repro"}\'::jsonb),'
        " ($5,$2,$3,'Image','1',$1,'default',1,"
        "  jsonb_build_object('mediaId',$6::text,'alt','Alt'))",
        section_id,
        site_id,
        page_id,
        heading_id,
        image_id,
        str(media_id),
    )
    workspace_id = await owner.fetchval(
        "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
        " title, delegation_preset, effective_scopes, status, expires_at)"
        " VALUES ($1,$2,$2,'083/4 Repro Workspace','L4',$3::jsonb,'ACTIVE',"
        " now()+interval '1 hour') RETURNING id",
        site_id,
        delegator_id,
        json.dumps(_MUTATION_SCOPES),
    )
    token, public_id, digest = generate_capability_token()
    await owner.execute(
        "INSERT INTO control.capability (workspace_id, public_id,"
        " secret_digest, scopes, expires_at) VALUES ($1,$2,$3,$4::jsonb,"
        " now()+interval '30 minutes')",
        workspace_id,
        public_id,
        digest,
        json.dumps(_MUTATION_SCOPES),
    )
    capability_id = await owner.fetchval(
        "SELECT id FROM control.capability WHERE public_id = $1", public_id
    )
    return {
        "delegator_id": UUID(str(delegator_id)),
        "site_id": UUID(str(site_id)),
        "workspace_id": UUID(str(workspace_id)),
        "capability_id": UUID(str(capability_id)),
        "page_id": page_id,
        "section_id": section_id,
        "heading_id": heading_id,
    }


def _0834_settings(
    database: AgentSiteDatabase, *, drain_seconds: float
) -> ReviewWorkerSettings:
    login, password = database.credentials["slaif_review_worker"]
    return ReviewWorkerSettings(
        mode=ReviewWorkerDatabaseMode.TEST,
        dsn=SecretStr(_dsn(database, login, password)),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        staleness_seconds=60.0,
        drain_lock_timeout_seconds=drain_seconds,
        evidence_deadline_seconds=120.0,
    )


async def _create_workspace(
    owner: Any, site_id: UUID, delegator_id: UUID, title: str
) -> tuple[UUID, UUID]:
    """One further L4 workspace + full-scope capability (trusted rows)."""

    workspace_id = await owner.fetchval(
        "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
        " title, delegation_preset, effective_scopes, version_facts,"
        " status, expires_at)"
        " VALUES ($1,$2,$2,$3,'L4', $4::jsonb," + _CURRENT_VERSION_FACTS + ","
        " 'ACTIVE', now() + interval '1 hour') RETURNING id",
        site_id,
        delegator_id,
        title,
        json.dumps(_MUTATION_SCOPES),
    )
    token, public_id, digest = generate_capability_token()
    await owner.execute(
        "INSERT INTO control.capability (workspace_id, public_id,"
        " secret_digest, scopes, expires_at) VALUES ($1,$2,$3,$4::jsonb,"
        " now() + interval '30 minutes')",
        workspace_id,
        public_id,
        digest,
        json.dumps(_MUTATION_SCOPES),
    )
    capability_id = await owner.fetchval(
        "SELECT id FROM control.capability WHERE public_id = $1", public_id
    )
    return UUID(str(workspace_id)), UUID(str(capability_id))


async def _cow_create(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    capability_id: UUID,
    site_id: UUID,
    page_id: UUID,
    parent_id: UUID,
    text: str,
) -> UUID:
    """One real agent COW create operation on the given workspace."""

    agent_pool = await database.role_pool("slaif_agent_runtime")
    try:
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            await cow.native.execute(
                "SELECT set_config('app.capability_id', $1, true)",
                str(capability_id),
            )
            created = await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_component_create("
                " $1, $2, 'Heading', $3, 'default', NULL, NULL, $4::jsonb)",
                site_id,
                page_id,
                parent_id,
                json.dumps({"level": 3, "text": text}),
            )
            assert created is not None
            return UUID(str(created["id"]))
    finally:
        await agent_pool.close()


async def _cow_update(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    capability_id: UUID,
    site_id: UUID,
    component_id: UUID,
    props: dict[str, Any],
) -> None:
    """One real agent COW update operation on the given workspace."""

    agent_pool = await database.role_pool("slaif_agent_runtime")
    try:
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            await cow.native.execute(
                "SELECT set_config('app.capability_id', $1, true)",
                str(capability_id),
            )
            updated = await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_component_update("
                " $1, $2, $3::jsonb, $4)",
                site_id,
                component_id,
                json.dumps(props),
                1,
            )
            assert updated is not None
    finally:
        await agent_pool.close()


async def _freeze_enqueue_claim(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    site_id: UUID,
    delegator_id: UUID,
    claimant: str,
) -> tuple[UUID, dict[str, Any]]:
    """Real freeze enqueue + worker claim without executing the job.

    The enqueue itself serializes on the canonical site row (the
    site-governance authority re-check), so callers staging a controlled
    race must request/claim while the row is free and only then start the
    worker RUN whose trusted materializer races on the row.
    """

    rows = await _control_call(
        database,
        "SELECT * FROM control.slaif_human_agent_workspace_freeze($1,$2,$3)",
        workspace_id,
        site_id,
        delegator_id,
    )
    assert len(rows) == 1
    job_id = UUID(str(rows[0]["job_id"]))
    claimed = await _worker_call(
        database,
        "SELECT * FROM control.slaif_review_job_claim($1, $2)",
        claimant,
        _WORKER_KINDS_0834,
    )
    assert len(claimed) == 1 and str(claimed[0]["id"]) == str(job_id)
    return job_id, dict(claimed[0])


async def _freeze_claim_run(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    site_id: UUID,
    delegator_id: UUID,
    pool: Any,
    claimant: str,
    settings: ReviewWorkerSettings | None = None,
) -> tuple[Any, UUID]:
    """Freeze enqueue + real worker claim + run; returns (result, job_id)."""

    job_id, job = await _freeze_enqueue_claim(
        database,
        workspace_id=workspace_id,
        site_id=site_id,
        delegator_id=delegator_id,
        claimant=claimant,
    )
    result = await run_freeze_job(pool, settings or _worker_settings(database), job)
    return result, job_id


async def _claim_accept_job(
    database: AgentSiteDatabase, *, claimant: str, expected_job_id: UUID
) -> dict[str, Any]:
    """Claim the real ACCEPT job and verify it is the expected one."""

    claimed = await _worker_call(
        database,
        "SELECT * FROM control.slaif_review_job_claim($1, $2)",
        claimant,
        _WORKER_KINDS_0834,
    )
    assert len(claimed) == 1, claimed
    assert str(claimed[0]["id"]) == str(expected_job_id), claimed
    assert str(claimed[0]["job_kind"]) == "ACCEPT", claimed
    return dict(claimed[0])


async def _accept_claim_run(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    delegator_id: UUID,
    pool: Any,
    claimant: str,
    boundary: Any,
    job_id: UUID | None = None,
) -> tuple[Any, UUID]:
    """Accept (enqueue if needed) + real worker claim + run.

    Returns (result, job_id). Pass ``job_id`` when the caller already
    enqueued the accept job (controlled race ordering).
    """

    if job_id is None:
        rows = await _enqueue_accept(database, workspace_id, delegator_id)
        job_id = UUID(str(rows[0]["job_id"]))
    job = await _claim_accept(database, claimant)
    assert str(job["id"]) == str(job_id)
    result = await run_accept_job(pool, _worker_settings(database), job, media=boundary)
    return result, job_id


async def _snapshot_row(database: AgentSiteDatabase, workspace_id: UUID) -> Any:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return await owner.fetchrow(
            "SELECT * FROM control.review_snapshot WHERE workspace_id = $1",
            workspace_id,
        )


async def _digest_is_valid(database: AgentSiteDatabase, snapshot_id: UUID) -> bool:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return bool(
            await owner.fetchval(
                "SELECT digest = encode(sha256(convert_to("
                " control.slaif_canonical_jsonb_text(payload),'UTF8')),'hex')"
                " FROM control.review_snapshot WHERE id = $1",
                snapshot_id,
            )
        )


def _node_heading_texts(node: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    if node.get("component_type") == "Heading":
        props = node.get("props")
        if isinstance(props, dict) and "text" in props:
            texts.append(str(props["text"]))
    children = node.get("children")
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                texts.extend(_node_heading_texts(child))
    return texts


def _page_heading_texts(page: dict[str, Any]) -> list[str]:
    """Heading texts from the persisted nested production tree.

    The snapshot payload stores ``pages[].nodes`` as the normalized
    projection roots (``children`` nested); this walks the actual tree
    so Heading children under the seeded Section are included.
    """

    nodes = page.get("nodes")
    assert isinstance(nodes, list), "page nodes missing"
    texts: list[str] = []
    for root in nodes:
        if isinstance(root, dict):
            texts.extend(_node_heading_texts(root))
    return texts


async def _snapshot_heading_texts(
    database: AgentSiteDatabase, snapshot_id: UUID
) -> list[str]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        document = await owner.fetchval(
            "SELECT payload FROM control.review_snapshot WHERE id = $1",
            snapshot_id,
        )
    payload = json.loads(document)
    texts: list[str] = []
    for page in payload["pages"]:
        texts.extend(_page_heading_texts(page))
    return texts


async def _active_queries(database: AgentSiteDatabase) -> list[tuple[int, str]]:
    """(pid, query) of every active backend on the fixture database.

    The observer logs in as the review-worker role itself: PostgreSQL
    masks ``pg_stat_activity`` state/query for sessions of other roles
    from non-superuser observers that are not members of those roles,
    so the owner observer cannot see the worker-pool backends that hold
    the freeze/accept lock waits.
    """

    login, password = database.credentials["slaif_review_worker"]
    observer = await asyncpg.connect(dsn=_dsn(database, login, password))
    try:
        rows = await observer.fetch(_ACTIVITY_SQL)
    finally:
        await observer.close()
    return [(int(row["pid"]), str(row["query"] or "")) for row in rows]


async def _blocking_pids(database: AgentSiteDatabase, pid: int) -> list[int]:
    """The real backends blocking ``pid`` (pg_blocking_pids)."""

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as observer:
        row = await observer.fetchrow(_BLOCKING_PIDS_SQL, pid)
    values = row[0] if row is not None else []
    return [int(value) for value in (values or [])]


def _task_diagnostic(task: asyncio.Task[Any] | None) -> str:
    if task is None:
        return "<not started>"
    if task.cancelled():
        return "<cancelled>"
    if task.done():
        exc = task.exception()
        if exc is not None:
            return f"<completed with exception: {exc!r}>"
        return f"<completed: {task.result()!r}>"
    return "<running>"


async def _wait_for_blocked_waiter(
    database: AgentSiteDatabase,
    *,
    query_predicate: Any,
    expected_blockers: set[int] | None = None,
    blockers_match: Callable[[list[int]], bool] | None = None,
    label: str,
    timeout: float = 30.0,
    diagnostic: Any = None,
) -> int:
    """Wait until an active backend whose current query matches
    ``query_predicate`` shows the expected ``pg_blocking_pids`` blocker
    chain; return its PID.

    ``pg_blocking_pids`` reports the DIRECT lock-queue edges of the
    current lock request, not a transitive closure: a second waiter
    queued behind a first waiter is blocked by the first waiter itself
    (which is itself blocked by the fixture holder).  The ordered
    second -> first -> holder chain is therefore proven by the first
    waiter's exact ``{holder}`` edge plus the second waiter's direct edge
    containing the first waiter (some PostgreSQL releases additionally
    report the holder on a queued edge, so ``blockers_match`` accepts the
    two observed direct shapes only).  Exact phase/PID identity is kept;
    never weakened to any blocked PID.  Finite deadline: raises
    AssertionError with the last observed candidates, the full
    active-backend dump, and the optional task diagnostic.
    """

    assert (expected_blockers is None) != (blockers_match is None), (
        "provide exactly one of expected_blockers / blockers_match"
    )
    deadline = time.monotonic() + timeout
    last: list[tuple[int, str, list[int]]] = []

    def _matches(blockers: list[int]) -> bool:
        if expected_blockers is not None:
            return set(blockers) == expected_blockers
        # The XOR assert above guarantees exactly one of the two is set;
        # mypy cannot retain that narrowing inside the closure.
        assert blockers_match is not None
        return blockers_match(blockers)

    while True:
        last = []
        for pid, query in await _active_queries(database):
            if query_predicate(query):
                last.append((pid, query, await _blocking_pids(database, pid)))
        for pid, _query, blockers in last:
            if _matches(blockers):
                return pid
        if time.monotonic() >= deadline:
            detail = _task_diagnostic(diagnostic) if diagnostic is not None else ""
            expected_desc = (
                sorted(expected_blockers)
                if expected_blockers is not None
                else "direct-edge match"
            )
            raise AssertionError(
                f"{label}: no active backend with the expected blocker "
                f"chain {expected_desc}"
                + (f"; task: {detail}" if detail else "")
                + f"; candidates: {last}"
                + f"; active: {await _active_queries(database)}"
            )
        await asyncio.sleep(0.05)


def _accept_site_lock(query: str) -> bool:
    """The acceptance preflight/promotion canonical-revision site lock."""

    return "canonical_revision FROM control.site" in query and "FOR UPDATE" in query


def _freeze_materializer_wait(query: str) -> bool:
    """The freeze transaction inside the trusted materializer call."""

    return "slaif_review_workspace_state" in query


async def _public_conflicts(
    database: AgentSiteDatabase, session_id: UUID
) -> list[dict[str, Any]]:
    """Public frozen foundation conflict inspection (CowReviewer)."""

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        async with asyncpg_cow_reviewer(owner) as reviewer:
            conflicts = await reviewer.conflicts(session_id, schema="content")
    return [dict(conflict) for conflict in conflicts]


async def _public_operations(
    database: AgentSiteDatabase, session_id: UUID
) -> list[UUID]:
    """Public frozen foundation session-operation inspection (sorted)."""

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        async with asyncpg_cow_reviewer(owner) as reviewer:
            operations = await reviewer.operations(session_id, schema="content")
    return sorted(operations)


class _PausingMediaBoundary:
    """A fixture seam around the REAL MediaBoundary (083/4 ordering 2).

    ``arm()`` arms a one-shot barrier: the wrapped finalize call runs its
    complete real finalization work, then waits at the barrier until
    ``release()``.  No finalization work is mocked or skipped; the barrier
    only delays the accept job's NEXT step (the final reviewer
    transaction), which makes that transaction's canonical site-row wait
    observable and deterministically ordered ahead of the competing
    freeze.
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self._barrier: asyncio.Event | None = None
        self._entered: asyncio.Event | None = None

    def arm(self) -> tuple[asyncio.Event, asyncio.Event]:
        barrier = asyncio.Event()
        entered = asyncio.Event()
        self._barrier = barrier
        self._entered = entered
        return barrier, entered

    def release(self) -> None:
        # Releasable from arm() until the gate is passed; a second call
        # (e.g. from a failure-cleanup finally) is a harmless no-op.
        if self._barrier is not None:
            self._barrier.set()

    async def finalize(
        self,
        site_id: UUID,
        workspace_id: UUID,
        media_ids: list[UUID],
    ) -> Any:
        barrier = self._barrier
        entered = self._entered
        # The real finalization work runs in full; only the return to the
        # caller (the next accept step) is gated.  The gate stays
        # releasable until the job reaches it, then is disarmed one-shot.
        manifest = await self._inner.finalize(site_id, workspace_id, media_ids)
        if barrier is not None:
            assert entered is not None
            entered.set()
            await barrier.wait()
            # Disarm only once the gate has actually been passed, so
            # release() stays effective from arm() until the gate is
            # passed (a second call afterwards is a harmless no-op).
            if self._barrier is barrier:
                self._barrier = None
                self._entered = None
        return manifest

    async def stop(self) -> None:
        await self._inner.stop()


async def _call_materializer(
    database: AgentSiteDatabase, workspace_id: UUID
) -> dict[str, Any]:
    document = await _worker_call(
        database,
        "SELECT control.slaif_review_workspace_state($1)",
        workspace_id,
    )
    doc = document[0][0]
    return json.loads(doc) if isinstance(doc, (str, bytes)) else dict(doc)


async def _materializer_with_timeout(
    worker: Any, workspace_id: UUID, lock_timeout: str
) -> Any:
    async with worker.transaction():
        await worker.execute(f"SET LOCAL lock_timeout = '{lock_timeout}'")
        return await worker.fetchval(
            "SELECT control.slaif_review_workspace_state($1)",
            workspace_id,
        )


@pytest.mark.asyncio
async def test_075_001_round_trip_exact_restore_and_locked_materializer(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """083/4 F + source reproduction.

    The fixture database boots at the new head (076_001).  This test
    downgrades to 074_001 (through 076_001 and 075_001), proves the
    pre-fix materializer behavior at runtime, re-upgrades, and proves
    the head materializer locks the site row, re-checks ACTIVE against
    the locked row, and reports the locked canonical revision.  The
    074-era workspace is version-unknown after the round trip and must
    be refused by the v2 materializer (honest legacy behavior); the
    head-behalf proofs run on a workspace created through the trusted
    076 constructor.
    """

    database = agent_site_database
    dsn = database.settings.resolved_owner_dsn()

    # The fixture provisions roles only; boot the intended 076_001 head
    # through the existing product helpers (as _seed does) before
    # inspecting the head state.
    await upgrade(database.settings)
    await reconcile(database.settings)

    # --- 076_001 head state ---------------------------------------------
    async with owner_connection(dsn, expected_database=database.name) as owner:
        def_head = await owner.fetchval(_FUNCTION_LOOKUP)
        acl_head = {str(row[0]): bool(row[1]) for row in await owner.fetch(_ACL_LOOKUP)}
    assert "FROM control.site WHERE id = ws.site_id FOR UPDATE" in def_head
    assert "'base_site_revision', site_revision," in def_head
    assert "site_status IS DISTINCT FROM 'ACTIVE'" in def_head

    # --- downgrade to 074_001: the exact 070_001 body is restored -------
    await run_migration(
        dsn,
        expected_database=database.name,
        operation="downgrade",
        revision="074_001",
    )
    async with owner_connection(dsn, expected_database=database.name) as owner:
        def_074 = await owner.fetchval(_FUNCTION_LOOKUP)
        acl_074 = {str(row[0]): bool(row[1]) for row in await owner.fetch(_ACL_LOOKUP)}
    assert "'base_site_revision', ws.base_site_revision," in def_074
    assert "FROM control.site WHERE id = ws.site_id FOR UPDATE" not in def_074
    assert acl_074 == acl_head

    # Seed a renderable site + workspace at the pre-fix revision.
    async with owner_connection(dsn, expected_database=database.name) as owner:
        ids = await _seed_raw(database, owner)
    ws074 = ids["workspace_id"]
    await _cow_create(
        database,
        workspace_id=ws074,
        capability_id=ids["capability_id"],
        site_id=ids["site_id"],
        page_id=ids["page_id"],
        parent_id=ids["section_id"],
        text="083/4 repro W1",
    )

    doc_before_bump = await _call_materializer(database, ws074)
    async with owner_connection(dsn, expected_database=database.name) as owner:
        await owner.execute(
            "UPDATE control.site SET canonical_revision = canonical_revision"
            " + 1 WHERE id = $1",
            ids["site_id"],
        )
        revision_after_bump = await owner.fetchval(
            "SELECT canonical_revision FROM control.site WHERE id = $1",
            ids["site_id"],
        )
    doc_after_bump = await _call_materializer(database, ws074)

    # Pre-fix reproduction: the materializer reports the workspace
    # creation-time revision (A=0) even after the site advanced to B=1.
    assert doc_before_bump["base_site_revision"] == 0
    assert doc_after_bump["base_site_revision"] == 0
    assert revision_after_bump == 1

    # Pre-fix reproduction: no canonical site-row lock around the read.
    owner_login, owner_password = database.credentials["slaif_owner"]
    blocker = await asyncpg.connect(dsn=_dsn(database, owner_login, owner_password))
    await blocker.execute("SET ROLE slaif_owner")
    try:
        async with blocker.transaction():
            await blocker.execute(
                "SELECT id FROM control.site WHERE id = $1 FOR UPDATE",
                ids["site_id"],
            )
            # The 074_001 materializer completes while the site row lock
            # is held: it never waits on it.
            doc_while_locked = await _call_materializer(database, ws074)
        assert doc_while_locked["base_site_revision"] == 0
    finally:
        await blocker.close()

    # --- re-upgrade to head: byte-exact round trip -----------------------
    await run_migration(
        dsn,
        expected_database=database.name,
        operation="upgrade",
        revision="head",
    )
    await reconcile(database.settings)
    async with owner_connection(dsn, expected_database=database.name) as owner:
        def_reup = await owner.fetchval(_FUNCTION_LOOKUP)
        acl_reup = {str(row[0]): bool(row[1]) for row in await owner.fetch(_ACL_LOOKUP)}
    assert def_reup == def_head
    assert acl_reup == acl_head

    # Legacy honesty: ws074 was created under 074, before version_facts
    # existed. The 076 downgrade legitimately dropped the column on the
    # round trip, so the workspace is version-unknown ('{}') and the v2
    # materializer must refuse it: no invented backfill, no weakened gate
    # (its only supported freeze path after upgrade is recreation).
    with pytest.raises(asyncpg.PostgresError) as legacy_exc:
        await _call_materializer(database, ws074)
    assert legacy_exc.value.sqlstate == "P0002"
    assert "REVIEW_WORKSPACE_VERSION_UNKNOWN" in str(legacy_exc.value)

    # Genuinely supported current workspace: created through the trusted
    # 076 constructor (the only product path that stamps the version
    # facts the v2 materializer requires).
    async with owner_connection(dsn, expected_database=database.name) as owner:
        ws_head = await owner.fetchval(
            "SELECT (control.slaif_workspace_create("
            "$1, $2, '083/4 Head Workspace',"
            " '083/5 faithful frozen review head workspace', 'L4', $3::jsonb, 1)).id",
            ids["site_id"],
            ids["delegator_id"],
            json.dumps(_MUTATION_SCOPES),
        )
        await owner.execute(
            "UPDATE control.site SET canonical_revision = canonical_revision"
            " + 1 WHERE id = $1",
            ids["site_id"],
        )
        revision_head = await owner.fetchval(
            "SELECT canonical_revision FROM control.site WHERE id = $1",
            ids["site_id"],
        )
        ws_base = await owner.fetchval(
            "SELECT base_site_revision FROM control.workspace WHERE id = $1",
            ws_head,
        )
    # The generic 024 constructor does not stamp base_site_revision
    # (column default 0); the site already advanced to 2 by now.
    assert ws_base == 0
    assert revision_head == 2

    # New behavior: the materializer reports the LOCKED current site
    # revision (2), differing from the workspace creation-baseline
    # column (0).
    doc_at_head = await _call_materializer(database, ws_head)
    assert doc_at_head["base_site_revision"] == 2

    # New behavior: it waits on the site row, bounded by lock_timeout.
    blocker = await asyncpg.connect(dsn=_dsn(database, owner_login, owner_password))
    await blocker.execute("SET ROLE slaif_owner")
    try:
        async with blocker.transaction():
            await blocker.execute(
                "SELECT id FROM control.site WHERE id = $1 FOR UPDATE",
                ids["site_id"],
            )
            worker_login, worker_password = database.credentials["slaif_review_worker"]
            worker = await asyncpg.connect(
                dsn=_dsn(database, worker_login, worker_password)
            )
            try:
                with pytest.raises(asyncpg.PostgresError) as excinfo:
                    await _materializer_with_timeout(worker, ws_head, "2s")
                assert excinfo.value.sqlstate == "55P03"
            finally:
                await worker.close()
    finally:
        await blocker.close()

    # New behavior: the pre-lock ACTIVE check can go stale if the wait
    # spans an authorized status change; the locked-row re-check stays
    # fail-closed.  The blocker holds the row lock; the materializer's
    # pre-lock EXISTS sees the committed ACTIVE and queues on the site
    # row; the blocker then archives under the held lock and commits.
    blocker = await asyncpg.connect(dsn=_dsn(database, owner_login, owner_password))
    await blocker.execute("SET ROLE slaif_owner")
    blocker_pid = await blocker.fetchval("SELECT pg_backend_pid()")
    worker_login, worker_password = database.credentials["slaif_review_worker"]
    worker = await asyncpg.connect(dsn=_dsn(database, worker_login, worker_password))
    task: asyncio.Task[Any] | None = None
    try:
        async with blocker.transaction():
            await blocker.execute(
                "SELECT id FROM control.site WHERE id = $1 FOR UPDATE",
                ids["site_id"],
            )
            task = asyncio.create_task(
                _materializer_with_timeout(worker, ws_head, "30s")
            )
            # The materializer is queued on the blocked site row, really
            # blocked by the observed blocker PID.
            await _wait_for_blocked_waiter(
                database,
                query_predicate=_freeze_materializer_wait,
                expected_blockers={blocker_pid},
                label="head materializer (stale-ACTIVE guard)",
                timeout=15.0,
                diagnostic=task,
            )
            # Archive under the held lock; the commit (context exit)
            # releases the row lock and makes the archive visible.
            await blocker.execute(
                "UPDATE control.site SET status = 'ARCHIVED' WHERE id = $1",
                ids["site_id"],
            )
        with pytest.raises(asyncpg.PostgresError) as excinfo:
            await task
        assert excinfo.value.sqlstate == "P0002"
        assert "REVIEW_SITE_NOT_ACTIVE" in str(excinfo.value)
    finally:
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await worker.close()
        await blocker.close()


# ---------------------------------------------------------------------------
# 083/5 R9: the full 076_001 roundtrip at runtime - 075 -> 076 -> 075 ->
# 076 with the retained-v2 downgrade refusal proven FIRST, genuine legacy
# v1 retention, exact constructor/ACL/OID restoration and the reconciled
# grant policy.  The comparison framework is the same catalog capture the
# source-review probes used (pg_proc identity + aclexplode grants); the
# expected EXECUTE policy is computed from the product's own declarative
# privilege maps, never hardcoded.
# ---------------------------------------------------------------------------
M076 = importlib.import_module(
    "slaif_agent_site.db.alembic.versions.076_001_faithful_frozen_review"
)
from slaif_agent_site.db import privileges as PRIV  # noqa: E402

_RT_HELPER_KEYS = (
    "slaif_review_string_cost{text}",
    "slaif_review_value_cost{jsonb,bigint,bigint}",
    "slaif_review_value_depth{jsonb,integer}",
    "slaif_review_media_append{uuid,uuid,jsonb}",
)
# The 083/5 frozen read/binding surface added by 076 beside the four
# cost/media helpers: (catalog key, M076 body constant, exact
# pre-reconcile grants = owner + the single targeted caller role,
# volatility char).
_RT_MEDIA_SURFACE = (
    (
        "slaif_review_snapshot_frozen_state{uuid}",
        "_FROZEN_STATE_SQL",
        ["slaif_owner:EXECUTE", "slaif_preview_reader:EXECUTE"],
        "s",
    ),
    (
        "slaif_review_projection_authorize{text,bytea,uuid}",
        "_PROJECTION_AUTHORIZE_SQL",
        ["slaif_owner:EXECUTE", "slaif_preview_reader:EXECUTE"],
        "v",
    ),
    (
        "slaif_review_media_authorize{text,bytea,uuid,uuid}",
        "_MEDIA_AUTHORIZE_SQL",
        ["slaif_media:EXECUTE", "slaif_owner:EXECUTE"],
        "v",
    ),
    (
        "slaif_media_preview_read{text,bytea,uuid,uuid,uuid,integer,integer,integer}",
        "_MEDIA_PREVIEW_READ_SQL",
        ["slaif_media:EXECUTE", "slaif_owner:EXECUTE"],
        "v",
    ),
    (
        'slaif_browser_preview_binding_register{uuid,text,"timestamp with time zone"}',
        "_BINDING_REGISTER_SQL",
        ["slaif_owner:EXECUTE", "slaif_preview_reader:EXECUTE"],
        "v",
    ),
    (
        "slaif_media_bound_preview_read{text,uuid}",
        "_BOUND_PREVIEW_READ_SQL",
        ["slaif_media:EXECUTE", "slaif_owner:EXECUTE"],
        "v",
    ),
)
_RT_MEDIA_KEYS = tuple(k for k, _, _, _ in _RT_MEDIA_SURFACE)
_RT_NEW_076_KEYS = _RT_HELPER_KEYS + _RT_MEDIA_KEYS
_RT_CTOR_024_KEY = "slaif_workspace_create{uuid,uuid,text,text,text,jsonb,integer}"
_RT_CTOR_028_KEY = "slaif_human_editor_workspace_resolve{uuid,uuid}"
_RT_CTOR_038_KEY = (
    "slaif_human_agent_workspace_create"
    "{uuid,uuid,text,text,text,text[],jsonb,text[],integer,integer,"
    "integer,integer,integer,integer}"
)
_RT_SC_KEY = "slaif_review_snapshot_complete{uuid,jsonb}"
_RT_MAT_KEY = "slaif_review_workspace_state{uuid}"
_RT_IDENTITY_FIELDS = (
    "signature",
    "prosrc_sha",
    "owner",
    "proconfig",
    "prosecdef",
    "provolatile",
    "language",
)
_RT_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?")
_RT_EFFECTIVE_ROLES = (*ROLE_NAMES, "public")
_CURRENT_VERSION_FACTS_JSON = (
    '{"catalog":"catalog-v1","composition_schema":"site-composition/v1",'
    '"content_model":"content-model/v1","design_system":"design-system/v1",'
    '"puck":"0.20.2","renderer":"renderer-v1"}'
)

_RT_POLICY_ROLES: dict[tuple[str, str], set[str]] = {}


def _rt_norm_sig(sig: str) -> str:
    # Catalog signatures arrive as array-literal text in which elements
    # containing whitespace are quoted ("timestamp with time zone"); map
    # signatures are plain comma lists, some using type aliases
    # (timestamptz).  Normalize both to bare canonical tokens.
    bare = sig.replace(" ", "").strip("{}").replace('"', "")
    for alias, canonical in (
        ("timestampwithtimezone", "timestamptz"),
        ("timewithtimezone", "timetz"),
        ("doubleprecision", "float8"),
    ):
        bare = bare.replace(alias, canonical)
    return bare


def _rt_register(mapping: dict[tuple[str, str], str], roles: set[str]) -> None:
    for (name, _identity), sig in mapping.items():
        _RT_POLICY_ROLES.setdefault((name, _rt_norm_sig(sig)), set()).update(roles)


_register = _rt_register
_register(PRIV.CONTROL_FUNCTIONS, {"slaif_control"})
_register(PRIV.AGENT_CONTROL_FUNCTIONS, {"slaif_agent_runtime"})
_register(PRIV.MEDIA_CONTROL_FUNCTIONS, {"slaif_media"})
_register(PRIV.REVIEW_WORKER_FUNCTIONS, {"slaif_review_worker"})
_register(
    PRIV.PUBLIC_RESOLVER_FUNCTIONS,
    {"slaif_public_reader", "slaif_preview_reader"},
)
_register(PRIV.PREVIEW_RENDER_FUNCTIONS, {"slaif_preview_reader"})
_register(
    PRIV.RENDER_METADATA_FUNCTIONS,
    {"slaif_public_reader", "slaif_preview_reader"},
)
for (name, _identity), sig in PRIV.HUMAN_EDITOR_FUNCTIONS.items():
    _register(
        {(name, _identity): sig},
        {"slaif_control"}
        if name == "slaif_human_editor_workspace_resolve"
        else {"slaif_editor_runtime"},
    )


def _rt_expected_grants(name: str, sig: str) -> list[str]:
    roles = sorted(_RT_POLICY_ROLES.get((name, _rt_norm_sig(sig)), set()))
    return ["slaif_owner:EXECUTE"] + [f"{r}:EXECUTE" for r in roles]


def _rt_sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _rt_extract_body(sql: str) -> str:
    i = sql.index("AS $fn$") + len("AS $fn$")
    j = sql.rindex("$fn$")
    return sql[i:j]


def _rt_norm_argtypes(text: str) -> str:
    # regtype[]::text carries an array-bounds prefix ([0:N]=) on some
    # PostgreSQL versions; normalize to the bare {..} form.
    if "{" in text:
        return text[text.index("{") :]
    return text


def _rt_split_key(key: str) -> tuple[str, str]:
    i = key.index("{")
    return key[:i], key[i:]


def _rt_diff_catalogs(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    return [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


async def _rt_capture_catalog(conn: Any) -> dict[str, Any]:
    """The complete control-schema function catalog (ordered by OID)."""

    rows = await conn.fetch(
        """
        SELECT p.proname AS name,
               p.proargtypes::regtype[]::text AS argtypes,
               p.prorettype::regtype::text AS rettype,
               p.oid,
               p.prosrc,
               pg_get_userbyid(p.proowner) AS owner,
               p.proconfig,
               p.prosecdef,
               p.provolatile,
               l.lanname AS language
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        JOIN pg_language l ON l.oid = p.prolang
        WHERE n.nspname = 'control'
        ORDER BY p.oid
        """
    )
    funcs: dict[str, Any] = {}
    for row in rows:
        name = row["name"]
        argt = _rt_norm_argtypes(row["argtypes"])
        grants = await conn.fetch(
            """
            SELECT a.grantee::regrole::text AS g,
                   array_agg(a.privilege_type ORDER BY a.privilege_type) AS privs
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace,
                 aclexplode(p.proacl) a
            WHERE n.nspname = 'control' AND p.proname = $1
              AND regexp_replace(
                  p.proargtypes::regtype[]::text, '^\\[[0-9:]+\\]=', '') = $2
            GROUP BY a.grantee ORDER BY a.grantee::regrole::text
            """,
            name,
            argt,
        )
        funcs[f"{name}{argt}"] = {
            "signature": f"{argt} -> {row['rettype']}",
            "oid": int(row["oid"]),
            "prosrc_sha": _rt_sha(row["prosrc"]),
            "owner": row["owner"],
            "proconfig": row["proconfig"],
            "prosecdef": row["prosecdef"],
            "provolatile": row["provolatile"],
            "language": row["language"],
            "grants": [f"{r['g']}:{','.join(r['privs'])}" for r in grants],
        }
    return funcs


def _rt_normalize_row(text: str | None, seed: dict[str, Any]) -> str | None:
    if text is None:
        return None
    for token, key in (
        ("$WSID", "workspace_id"),
        ("$SITEID", "site_id"),
        ("$USERID", "user_id"),
    ):
        text = text.replace(seed[key], token)
    return _RT_TS_RE.sub("$TS", text)


async def _rt_capture_state(conn: Any, seed: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "alembic_version": await conn.fetchval(
            "SELECT version_num::text FROM control.alembic_version"
        ),
        "workspace_columns": [
            r[0]
            for r in await conn.fetch(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='control' AND table_name='workspace' "
                "ORDER BY ordinal_position"
            )
        ],
        "tables": {
            name: await conn.fetchval(
                "SELECT to_regclass('control.' || $1) IS NOT NULL", name
            )
            for name in ("review_snapshot", "review_job", "workspace", "site")
        },
        "marker": await conn.fetchrow(
            "SELECT readiness_state, safe, migration_revision "
            "FROM control.bootstrap_readiness WHERE singleton"
        ),
        "baseline_workspace_row": _rt_normalize_row(
            await conn.fetchval(
                "SELECT row_to_json(w)::text FROM control.workspace w WHERE w.id = $1",
                seed["workspace_id"],
            ),
            seed,
        ),
    }
    out["control_functions"] = await _rt_capture_catalog(conn)
    return out


async def _rt_seed_baseline(owner: Any) -> dict[str, Any]:
    """Committed 075-era baseline data through the original 024 constructor."""

    user_id = await owner.fetchval(
        """
        INSERT INTO control.user_account (
            id, identity_kind, local_username, local_username_normalized,
            password_hash, display_name, status
        ) VALUES (gen_random_uuid(), 'LOCAL', 'Roundtrip.Delegator',
            'roundtrip.delegator', $1, 'Roundtrip Delegator', 'ACTIVE')
        RETURNING id
        """,
        _AGGON2,
    )
    site_id = await owner.fetchval(
        "INSERT INTO control.site (site_key, display_name, default_locale,"
        " component_catalog_version) VALUES ('roundtrip-rt','Roundtrip',"
        " 'en-US', 'catalog-v1') RETURNING id"
    )
    await owner.execute(
        "INSERT INTO control.site_membership (site_id,user_account_id,"
        " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
        site_id,
        user_id,
    )
    created = await owner.fetchrow(
        "SELECT * FROM control.slaif_workspace_create($1,$2,"
        "'Roundtrip Baseline WS','roundtrip baseline','L2_SITE_EDITOR',"
        "'[]'::jsonb,2)",
        site_id,
        user_id,
    )
    assert created is not None
    return {
        "user_id": str(user_id),
        "site_id": str(site_id),
        "workspace_id": str(created["id"]),
    }


async def _rt_invoke_constructors(
    owner: Any, site_id: str, user_id: str, *, check_version_facts: bool
) -> dict[str, Any]:
    """All three INSERT-path constructors in one rolled-back transaction."""

    results: dict[str, Any] = {}
    txn = owner.transaction()
    await txn.start()
    try:
        created = await owner.fetchrow(
            "SELECT * FROM control.slaif_workspace_create($1,$2,'RT V2 WS',"
            " 'roundtrip','L2_SITE_EDITOR','[]'::jsonb,2)",
            site_id,
            user_id,
        )
        results["ws_create"] = str(created["id"]) if created else None
        user2_id = await owner.fetchval(
            """
            INSERT INTO control.user_account (
                id, identity_kind, local_username, local_username_normalized,
                password_hash, display_name, status
            ) VALUES (gen_random_uuid(), 'LOCAL', 'Roundtrip.Editor2',
                'roundtrip.editor2', $1, 'Roundtrip Editor 2', 'ACTIVE')
            RETURNING id
            """,
            _AGGON2,
        )
        await owner.execute(
            "INSERT INTO control.site_membership (site_id,user_account_id,"
            " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
            site_id,
            user2_id,
        )
        resolved = await owner.fetchval(
            "SELECT control.slaif_human_editor_workspace_resolve($1,$2)",
            site_id,
            user2_id,
        )
        results["editor_resolve_insert_path"] = str(resolved) if resolved else None
        scope = await owner.fetchval(
            "SELECT permission_key FROM control.permission "
            "WHERE site_assignable AND agent_delegation_level IS NOT NULL "
            "AND agent_delegation_level <= 4 ORDER BY permission_key LIMIT 1"
        )
        results["chosen_scope"] = scope
        agent = None
        if scope is not None:
            agent = await owner.fetchrow(
                "SELECT * FROM control.slaif_human_agent_workspace_create("
                "$1,$2,'RT Agent','roundtrip','L4_SITE_ARCHITECT',ARRAY[$3],"
                "'{}'::jsonb,ARRAY['127.0.0.1'],100,10,0,0,0,2)",
                site_id,
                user2_id,
                scope,
            )
        results["agent_ws_create"] = str(agent["id"]) if agent is not None else None
        if check_version_facts:
            for label, row_id in (
                ("ws_create", created["id"] if created else None),
                ("agent_ws_create", agent["id"] if agent is not None else None),
                ("editor_resolve", resolved if resolved else None),
            ):
                if row_id is None:
                    continue
                results[f"{label}_vf"] = await owner.fetchval(
                    "SELECT version_facts IS NOT NULL "
                    "AND version_facts = $2::jsonb FROM control.workspace "
                    "WHERE id = $1::uuid",
                    str(row_id),
                    _CURRENT_VERSION_FACTS_JSON,
                )
    finally:
        await txn.rollback()
    return results


async def _rt_create_probe_workspace(
    owner: Any, site_id: str, user_id: str, title: str
) -> str:
    ws = await owner.fetchrow(
        "SELECT * FROM control.slaif_workspace_create($1,$2,$3,$4,"
        "'L2_SITE_EDITOR','[]'::jsonb,2)",
        site_id,
        user_id,
        title,
        "roundtrip probe",
    )
    assert ws is not None
    return str(ws["id"])


async def _rt_set_freezing(owner: Any, workspace_id: str) -> None:
    n = await owner.execute(
        "UPDATE control.workspace SET status='FREEZING' "
        "WHERE id=$1 AND status='ACTIVE'",
        workspace_id,
    )
    assert n == "UPDATE 1", n


async def _rt_materialize_payload(owner: Any, workspace_id: str) -> dict[str, Any]:
    raw = await owner.fetchval(
        "SELECT control.slaif_review_workspace_state($1::uuid)", workspace_id
    )
    doc = json.loads(raw)
    assert isinstance(doc, dict)
    return doc


async def _rt_canonical_digest(owner: Any, payload: dict[str, Any]) -> str:
    return str(
        await owner.fetchval(
            "SELECT encode(sha256(convert_to("
            "control.slaif_canonical_jsonb_text($1::jsonb),'UTF8')),'hex')",
            json.dumps(payload),
        )
    )


def _rt_complete_row(
    workspace_id: str,
    payload: dict[str, Any],
    *,
    digest: str,
    site_id: str | None = None,
) -> str:
    versions = payload.get("workspace_versions")
    if versions is None:
        # Genuine legacy v1 row: the base-era worker
        # (build_snapshot_document) built ``versions`` from the six trusted
        # pin constants; v1 payloads carry no workspace_versions key.
        versions = {
            "catalog": CATALOG_VERSION,
            "design_system": DESIGN_SYSTEM_VERSION,
            "composition_schema": COMPOSITION_SCHEMA_VERSION,
            "renderer": RENDERER_VERSION,
            "puck": PUCK_VERSION_PIN,
            "content_model": REVIEW_WORKER_CONTENT_MODEL_SCHEMA_VERSION,
        }
    return json.dumps(
        {
            "workspace_id": workspace_id,
            "site_id": site_id if site_id is not None else payload["site_id"],
            "status": "COMPLETE",
            "revision_watermark": (
                payload["base_site_revision"] + payload["operation_watermark"]
            ),
            "versions": versions,
            "normalized_state": payload,
            "validation_report": {
                "state_version": payload.get("state_version"),
                "pages_validated": len(payload.get("pages", [])),
                "errors": [],
                "cancelled_by_freeze": [],
            },
            "media_references": list(payload.get("media", {}).values()),
            "browser_evidence": [],
            "payload": payload,
            "digest": digest,
            "created_by": "roundtrip",
        }
    )


async def _rt_effect_snapshot(
    conn: Any, workspace_id: str, site_id: str
) -> dict[str, Any]:
    return {
        "snap_rows": await conn.fetchval(
            "SELECT count(*) FROM control.review_snapshot WHERE workspace_id=$1",
            workspace_id,
        ),
        "ws_state": await conn.fetchval(
            "SELECT status || '/' || coalesce(review_snapshot_id::text,'null') "
            "FROM control.workspace WHERE id=$1",
            workspace_id,
        ),
        "promo_rows": await conn.fetchval("SELECT count(*) FROM audit.promotion"),
        "page_rows": await conn.fetchval(
            "SELECT count(*) FROM content.page WHERE site_id=$1", site_id
        ),
        "composition_rows": await conn.fetchval(
            "SELECT count(*) FROM content.page_composition_base"
        ),
    }


_RT_SNAPSHOT_ROW_BYTES = (
    "SELECT row_to_json(r)::text FROM control.review_snapshot r WHERE r.workspace_id=$1"
)


@pytest.mark.asyncio
async def test_076_001_round_trip_retained_v2_and_exact_restore(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """083/5 R9: the complete 075 -> 076 -> 075 -> 076 runtime roundtrip.

    S0 captures the true 075 catalog/ACL/OID state (after a real
    downgrade of the fixture head) with a genuine legacy v1 snapshot
    created through the real v1 materializer + v1 completion contract.
    The upgrade to 076 preserves the identity+grants of every
    non-replaced function exactly and carries the exact v2 bodies for
    the five replaced functions.  Reconcile applies the normal
    bootstrap hardening, after which every control function matches
    the product's declarative privilege policy.  The completion guards
    are proven with real materialized v2 payloads in FREEZING
    (co-tampered site, corrupted digest, co-tampered version facts,
    and the valid path).  The downgrade with BOTH retained v2 and v1
    rows is refused FIRST (SNAPSHOT_DOWNGRADE_RETAINED_V2) with zero
    effects; with the v2 row removed the downgrade restores the exact
    075 catalog (identity incl. OID), the reconciled grant policy, the
    byte-identical v1 row, and working 075 constructors.  The
    re-upgrade reproduces the reconciled head exactly, with the
    recreated 076 helpers keeping identity+grants at legitimately
    fresh OIDs.
    """

    database = agent_site_database
    dsn = database.settings.resolved_owner_dsn()
    db_name = database.name
    expected = {
        "sc_v2_body_sha": _rt_sha(_rt_extract_body(M076._SNAPSHOT_COMPLETE_V2_SQL)),
        "sc_v1_body_sha": _rt_sha(_rt_extract_body(M076._SNAPSHOT_COMPLETE_070_SQL)),
        "mat_v2_body_sha": _rt_sha(_rt_extract_body(M076._MATERIALIZER_V2_SQL)),
        "mat_075_body_sha": _rt_sha(_rt_extract_body(M076._MATERIALIZER_075)),
        "ctor_024_body_sha": _rt_sha(_rt_extract_body(M076._WORKSPACE_CREATE_024_SQL)),
        "ctor_028_body_sha": _rt_sha(
            _rt_extract_body(M076._HUMAN_EDITOR_RESOLVE_028_SQL)
        ),
        "ctor_038_body_sha": _rt_sha(
            _rt_extract_body(M076._AGENT_WORKSPACE_CREATE_038_SQL)
        ),
        "ctor_024_v2_body_sha": _rt_sha(
            _rt_extract_body(M076._WORKSPACE_CREATE_V2_SQL)
        ),
        "ctor_028_v2_body_sha": _rt_sha(
            _rt_extract_body(M076._HUMAN_EDITOR_RESOLVE_V2_SQL)
        ),
        "ctor_038_v2_body_sha": _rt_sha(
            _rt_extract_body(M076._AGENT_WORKSPACE_CREATE_V2_SQL)
        ),
        "string_cost_body_sha": _rt_sha(_rt_extract_body(M076._STRING_COST_SQL)),
        "value_cost_body_sha": _rt_sha(_rt_extract_body(M076._VALUE_COST_SQL)),
        "value_depth_body_sha": _rt_sha(_rt_extract_body(M076._VALUE_DEPTH_SQL)),
        "media_append_body_sha": _rt_sha(_rt_extract_body(M076._MEDIA_APPEND_SQL)),
    }
    assert M076._SNAPSHOT_COMPLETE_070_SQL.lstrip().startswith(
        "CREATE OR REPLACE FUNCTION control.slaif_review_snapshot_complete"
    )

    # Framework non-vacuity (wrong-expectation counterfactual): a
    # tampered prosrc MUST be detected by the exact comparison, and a
    # clean copy MUST pass it.
    probe = {"f{t}": {"prosrc_sha": "0" * 64}}
    tampered = {**probe, "f{t}": {"prosrc_sha": _rt_sha("wrong-body")}}
    assert _rt_diff_catalogs(probe, probe) == []
    assert _rt_diff_catalogs(tampered, probe) == ["f{t}"]

    # --- S0: the true 075 pre-upgrade baseline ---------------------------
    # The fixture boots at the 076 head; the single-step downgrade
    # (no snapshot rows exist yet, so the retained-v2 guard is inert)
    # restores the exact 075 constructors before the baseline capture.
    await upgrade(database.settings)
    await run_migration(
        dsn, expected_database=db_name, operation="downgrade", revision="075_001"
    )
    with pytest.raises(BootstrapStateError, match="not at the required migration"):
        await reconcile(database.settings)
    async with owner_connection(dsn, expected_database=db_name) as owner:
        seed = await _rt_seed_baseline(owner)
    s0: dict[str, Any] = {}
    async with owner_connection(dsn, expected_database=db_name) as owner:
        s0 = await _rt_capture_state(owner, seed)
    assert s0["alembic_version"] == "075_001"
    assert "version_facts" not in s0["workspace_columns"]
    base = s0["control_functions"]
    sc = base.get(_RT_SC_KEY)
    mat = base.get(_RT_MAT_KEY)
    c024 = base.get(_RT_CTOR_024_KEY)
    c028 = base.get(_RT_CTOR_028_KEY)
    c038 = base.get(_RT_CTOR_038_KEY)
    assert sc is not None and sc["prosrc_sha"] == expected["sc_v1_body_sha"]
    assert mat is not None and mat["prosrc_sha"] == expected["mat_075_body_sha"]
    assert (
        c024 is not None
        and c024["prosrc_sha"] == expected["ctor_024_body_sha"]
        and c028 is not None
        and c028["prosrc_sha"] == expected["ctor_028_body_sha"]
        and c038 is not None
        and c038["prosrc_sha"] == expected["ctor_038_body_sha"]
    )
    assert all(k not in base for k in _RT_NEW_076_KEYS)
    assert s0["baseline_workspace_row"] is not None

    # --- S0b: genuine legacy v1 snapshot (075 state, v1 contract) --------
    async with owner_connection(dsn, expected_database=db_name) as owner:
        ws_legacy = await _rt_create_probe_workspace(
            owner, seed["site_id"], seed["user_id"], "RT Legacy v1"
        )
        await _rt_set_freezing(owner, ws_legacy)
        v1_payload = await _rt_materialize_payload(owner, ws_legacy)
        assert v1_payload.get("state_version") == "review-snapshot/v1"
        v1_digest = await _rt_canonical_digest(owner, v1_payload)
        v1_snap_id = await owner.fetchval(
            "SELECT control.slaif_review_snapshot_complete($1::uuid,$2::jsonb)",
            ws_legacy,
            _rt_complete_row(ws_legacy, v1_payload, digest=v1_digest),
        )
        assert v1_snap_id is not None
        v1_row_bytes = await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_legacy)
        v1_ws_state = await owner.fetchval(
            "SELECT status || '/' || coalesce(review_snapshot_id::text,'null') "
            "FROM control.workspace WHERE id=$1",
            ws_legacy,
        )
        assert v1_ws_state == f"REVIEW/{v1_snap_id}", v1_ws_state
        v1_row_check = await owner.fetchrow(
            "SELECT payload = $2::jsonb AND digest = $3 "
            "FROM control.review_snapshot WHERE workspace_id=$1",
            ws_legacy,
            json.dumps(v1_payload),
            v1_digest,
        )
        assert v1_row_check[0] is True

    # --- S1: upgrade to head, migration effect ONLY (no reconcile) ------
    await run_migration(
        dsn, expected_database=db_name, operation="upgrade", revision="head"
    )
    s1: dict[str, Any] = {}
    async with owner_connection(dsn, expected_database=db_name) as owner:
        s1 = await _rt_capture_state(owner, seed)
    assert s1["alembic_version"] == "076_001"
    assert "version_facts" in s1["workspace_columns"]
    head = s1["control_functions"]
    assert set(head) - set(base) == set(_RT_NEW_076_KEYS) and set(base) <= set(head)
    replaced_v2_bodies = {
        _RT_SC_KEY: expected["sc_v2_body_sha"],
        _RT_MAT_KEY: expected["mat_v2_body_sha"],
        _RT_CTOR_024_KEY: expected["ctor_024_v2_body_sha"],
        _RT_CTOR_028_KEY: expected["ctor_028_v2_body_sha"],
        _RT_CTOR_038_KEY: expected["ctor_038_v2_body_sha"],
    }
    # Every NON-replaced pre-existing function keeps identity+OID+grants.
    for k in base:
        if k in replaced_v2_bodies:
            continue
        for f in (*_RT_IDENTITY_FIELDS, "oid", "grants"):
            assert base[k][f] == head[k][f], (k, f, base[k][f], head[k][f])
    # The five replaced functions carry the exact v2 bodies with
    # owner/security/config/volatility/language/signature/oid/grants
    # preserved.
    for k, body_sha in replaced_v2_bodies.items():
        assert head[k]["prosrc_sha"] == body_sha, k
        assert head[k]["oid"] == base[k]["oid"], k
        assert head[k]["owner"] == base[k]["owner"] == "slaif_owner", k
        for f in (
            "prosecdef",
            "proconfig",
            "provolatile",
            "language",
            "signature",
            "grants",
        ):
            assert head[k][f] == base[k][f], (k, f)
    for key, body_sha in (
        ("slaif_review_string_cost{text}", expected["string_cost_body_sha"]),
        (
            "slaif_review_value_cost{jsonb,bigint,bigint}",
            expected["value_cost_body_sha"],
        ),
        ("slaif_review_value_depth{jsonb,integer}", expected["value_depth_body_sha"]),
        (
            "slaif_review_media_append{uuid,uuid,jsonb}",
            expected["media_append_body_sha"],
        ),
    ):
        f = head[key]
        assert f["prosrc_sha"] == body_sha, key
        assert f["owner"] == "slaif_owner", key
        assert f["grants"] == ["slaif_owner:EXECUTE"], (key, f["grants"])
        assert f["proconfig"] == ["search_path=pg_catalog"], (key, f["proconfig"])
        assert f["prosecdef"] is False, key
    # The six frozen read/binding functions: exact bodies, owner
    # slaif_owner, SECURITY DEFINER, pg_catalog search_path, and the
    # single targeted caller role per the 076 grant convention.
    for key, const, grants, vol in _RT_MEDIA_SURFACE:
        f = head[key]
        assert f["prosrc_sha"] == _rt_sha(_rt_extract_body(getattr(M076, const))), key
        assert f["owner"] == "slaif_owner", key
        assert f["grants"] == grants, (key, f["grants"])
        assert f["proconfig"] == ["search_path=pg_catalog"], (key, f["proconfig"])
        assert f["prosecdef"] is True, key
        assert f["provolatile"] == vol.encode("ascii"), (key, f["provolatile"])
    async with owner_connection(dsn, expected_database=db_name) as owner:
        vf = await owner.fetchval(
            "SELECT version_facts::text FROM control.workspace WHERE id=$1",
            seed["workspace_id"],
        )
        assert vf == "{}", f"got={vf}"
        with pytest.raises(asyncpg.PostgresError) as err:
            await owner.fetchval(
                "SELECT control.slaif_review_workspace_state($1::uuid)",
                seed["workspace_id"],
            )
        assert err.value.sqlstate == "P0002"
        assert "REVIEW_WORKSPACE_VERSION_UNKNOWN" in (err.value.message or "")

    # 076 constructors: all three INSERT paths, version-facts stamping.
    async with owner_connection(dsn, expected_database=db_name) as owner:
        inv66 = await _rt_invoke_constructors(
            owner, seed["site_id"], seed["user_id"], check_version_facts=True
        )
        ws_pinned = await _rt_create_probe_workspace(
            owner, seed["site_id"], seed["user_id"], "RT P1 Pinned"
        )
        pinned_payload = await _rt_materialize_payload(owner, ws_pinned)
        unpinned = {
            r[0]
            for r in await owner.fetch(
                "SELECT id::text FROM control.workspace WHERE site_id=$1::uuid "
                "AND version_facts IS NOT DISTINCT FROM '{}'::jsonb",
                seed["site_id"],
            )
        }
    assert inv66["ws_create"] is not None
    assert inv66["editor_resolve_insert_path"] is not None
    assert inv66["agent_ws_create"] is not None
    assert unpinned == {seed["workspace_id"], ws_legacy}, f"unpinned={unpinned}"
    assert inv66.get("ws_create_vf") is True
    assert inv66.get("agent_ws_create_vf") is True
    assert inv66.get("editor_resolve_vf") is True
    assert pinned_payload.get("state_version") == "review-snapshot/v2"
    assert set(pinned_payload) == {
        "state_version",
        "workspace_id",
        "site_id",
        "site",
        "base_site_revision",
        "operation_watermark",
        "workspace_versions",
        "locales",
        "theme",
        "regions",
        "navigation",
        "redirects",
        "pages",
        "page_compositions",
        "content",
        "proposals",
        "media_inventory",
        "media",
    }, f"keys={sorted(pinned_payload)}"

    # --- S2: reconcile = normal bootstrap hardening ----------------------
    await reconcile(database.settings)
    s2: dict[str, Any] = {}
    async with owner_connection(dsn, expected_database=db_name) as owner:
        s2 = await _rt_capture_state(owner, seed)
    s2f = s2["control_functions"]
    for k in head:
        for f in _RT_IDENTITY_FIELDS:
            assert head[k][f] == s2f[k][f], (k, f)
    for k in s2f:
        name, sig = _rt_split_key(k)
        assert sorted(s2f[k]["grants"]) == sorted(_rt_expected_grants(name, sig)), (
            k,
            s2f[k]["grants"],
            _rt_expected_grants(name, sig),
        )
    eff_placeholders = ", ".join(
        f"${i}" for i in range(1, len(_RT_EFFECTIVE_ROLES) + 1)
    )
    async with owner_connection(dsn, expected_database=db_name) as eff:
        eff_rows = await eff.fetch(
            "SELECT r.rolname AS role, f.oid AS oid, "
            "has_function_privilege(r.rolname, f.oid, 'EXECUTE') AS has "
            "FROM pg_proc f "
            "JOIN pg_namespace n ON n.oid = f.pronamespace "
            f"CROSS JOIN (VALUES ({eff_placeholders})) AS r(rolname) "
            "WHERE n.nspname = 'control' ORDER BY r.rolname, f.oid",
            *_RT_EFFECTIVE_ROLES,
        )
    oid_to_key = {v["oid"]: k for k, v in s2f.items()}
    for row in eff_rows:
        name_sig = oid_to_key.get(row["oid"])
        assert name_sig is not None, f"unknown oid {row['oid']}"
        name, sig = _rt_split_key(name_sig)
        roles = _RT_POLICY_ROLES.get((name, _rt_norm_sig(sig)), set())
        expect = row["role"] in roles or row["role"] == "slaif_owner"
        assert bool(row["has"]) == expect, (name_sig, row["role"], row["has"])
    assert s2["marker"] is not None and s2["marker"]["readiness_state"] == "HARDENED"

    # --- P2B: completion/context guards at head (FREEZING, real data) ----
    async with owner_connection(dsn, expected_database=db_name) as owner:
        site_b = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name,"
            " default_locale, component_catalog_version) VALUES "
            "('roundtrip-rt-b','Roundtrip B','en-US','catalog-v1') "
            "RETURNING id"
        )
        ws_a = await _rt_create_probe_workspace(
            owner, seed["site_id"], seed["user_id"], "RT Probe Site"
        )
        ws_c = await _rt_create_probe_workspace(
            owner, seed["site_id"], seed["user_id"], "RT Probe Digest"
        )
        ws_b = await _rt_create_probe_workspace(
            owner, seed["site_id"], seed["user_id"], "RT Probe Version"
        )
        ws_s = await _rt_create_probe_workspace(
            owner, seed["site_id"], seed["user_id"], "RT Probe Valid"
        )
        for w in (ws_a, ws_c, ws_b, ws_s):
            await _rt_set_freezing(owner, w)
        before = {
            w: await _rt_effect_snapshot(owner, w, seed["site_id"])
            for w in (ws_a, ws_c, ws_b, ws_s)
        }
        # (A) co-tampered site: the DIGEST-COVERED payload.site_id AND
        #     row.site_id both move to the SAME foreign VALID site and
        #     the digest is recomputed over the modified payload, so
        #     every invariant before the context binding holds (incl.
        #     payload-vs-row site equality and digest match) and only
        #     the actual-workspace guard can refuse.
        payload_a = await _rt_materialize_payload(owner, ws_a)
        payload_a_t = dict(payload_a)
        payload_a_t["site_id"] = str(site_b)
        digest_a = await _rt_canonical_digest(owner, payload_a_t)
        try:
            await owner.fetchval(
                "SELECT control.slaif_review_snapshot_complete($1::uuid, $2::jsonb)",
                ws_a,
                _rt_complete_row(
                    ws_a, payload_a_t, digest=digest_a, site_id=str(site_b)
                ),
            )
            raise AssertionError("co-tampered site completion did not refuse")
        except asyncpg.PostgresError as error:
            assert error.sqlstate == "P0002"
            assert "SNAPSHOT_SITE_MISMATCH" in (error.message or "")
        # (C) real payload, digest recomputed then corrupted.
        payload_c = await _rt_materialize_payload(owner, ws_c)
        digest_c = await _rt_canonical_digest(owner, payload_c)
        assert re.fullmatch(r"[0-9a-f]{64}", digest_c), digest_c[:16]
        corrupted = ("1" if digest_c[0] != "1" else "0") + digest_c[1:]
        try:
            await owner.fetchval(
                "SELECT control.slaif_review_snapshot_complete($1::uuid, $2::jsonb)",
                ws_c,
                _rt_complete_row(ws_c, payload_c, digest=corrupted),
            )
            raise AssertionError("corrupted digest completion did not refuse")
        except asyncpg.PostgresError as error:
            assert error.sqlstate == "P0002"
            assert "SNAPSHOT_DIGEST_MISMATCH" in (error.message or "")
        # (B) real payload, workspace version facts co-tampered to '{}'.
        payload_b = await _rt_materialize_payload(owner, ws_b)
        row_b = _rt_complete_row(
            ws_b, payload_b, digest=await _rt_canonical_digest(owner, payload_b)
        )
        await owner.execute(
            "UPDATE control.workspace SET version_facts='{}'::jsonb WHERE id=$1",
            ws_b,
        )
        try:
            await owner.fetchval(
                "SELECT control.slaif_review_snapshot_complete($1::uuid, $2::jsonb)",
                ws_b,
                row_b,
            )
            raise AssertionError("co-tampered version facts did not refuse")
        except asyncpg.PostgresError as error:
            assert error.sqlstate == "P0002"
            assert "SNAPSHOT_WORKSPACE_VERSIONS_MISMATCH" in (error.message or "")
        # (S) fully valid row: successful completion, real valid path.
        payload_s = await _rt_materialize_payload(owner, ws_s)
        digest_s = await _rt_canonical_digest(owner, payload_s)
        snap_s = await owner.fetchval(
            "SELECT control.slaif_review_snapshot_complete($1::uuid, $2::jsonb)",
            ws_s,
            _rt_complete_row(ws_s, payload_s, digest=digest_s),
        )
        assert snap_s is not None
        row_s = await owner.fetchrow(
            "SELECT payload = $2::jsonb AND digest = $3 "
            "AND site_id = $4::uuid AND status = 'COMPLETE' "
            "FROM control.review_snapshot WHERE workspace_id=$1",
            ws_s,
            json.dumps(payload_s),
            digest_s,
            seed["site_id"],
        )
        assert row_s[0] is True
        v2_row_bytes = await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_s)
        ws_s_state = await owner.fetchval(
            "SELECT status || '/' || coalesce(review_snapshot_id::text,'null') "
            "FROM control.workspace WHERE id=$1",
            ws_s,
        )
        assert ws_s_state == f"REVIEW/{snap_s}", ws_s_state
        for w in (ws_a, ws_c, ws_b):
            after = await _rt_effect_snapshot(owner, w, seed["site_id"])
            assert before[w] == after, (w, before[w], after)
        after_s = await _rt_effect_snapshot(owner, ws_s, seed["site_id"])
        assert after_s["snap_rows"] == 1
        assert after_s["ws_state"] == f"REVIEW/{snap_s}"
        assert after_s["promo_rows"] == before[ws_s]["promo_rows"]
        assert after_s["page_rows"] == before[ws_s]["page_rows"]
        assert after_s["composition_rows"] == before[ws_s]["composition_rows"]

    # --- P3a: BOTH genuine retained rows block the downgrade FIRST ------
    try:
        await run_migration(
            dsn,
            expected_database=db_name,
            operation="downgrade",
            revision="075_001",
        )
        raise AssertionError("retained-v2 downgrade did not refuse")
    except Exception as error:  # noqa: BLE001 - exact text asserted below
        assert "SNAPSHOT_DOWNGRADE_RETAINED_V2" in str(error), str(error)[:300]
    s_refused: dict[str, Any] = {}
    async with owner_connection(dsn, expected_database=db_name) as owner:
        s_refused = await _rt_capture_state(owner, seed)
    assert s_refused["alembic_version"] == "076_001"
    assert s_refused["control_functions"] == s2f
    assert "version_facts" in s_refused["workspace_columns"]
    async with owner_connection(dsn, expected_database=db_name) as owner:
        assert await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_s) == v2_row_bytes
        assert await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_legacy) == v1_row_bytes
        # Documented fixture resolution of the retained v2 snapshot: the
        # migration never rewrites/deletes immutable history; the owner
        # removes the v2 row so the roundtrip can exercise the supported
        # downgrade path (the separate v1 rollback fixture is ws_legacy).
        assert (
            await owner.execute(
                "DELETE FROM control.review_snapshot WHERE workspace_id=$1",
                ws_s,
            )
            == "DELETE 1"
        )

    # --- P3b: downgrade with the genuine legacy v1 row retained ---------
    await run_migration(
        dsn, expected_database=db_name, operation="downgrade", revision="075_001"
    )
    s3: dict[str, Any] = {}
    async with owner_connection(dsn, expected_database=db_name) as owner:
        s3 = await _rt_capture_state(owner, seed)
    s3f, s0f = s3["control_functions"], s0["control_functions"]
    assert set(s3f) == set(s0f)
    for k in s0f:
        for f in (*_RT_IDENTITY_FIELDS, "oid"):
            assert s3f[k][f] == s0f[k][f], (k, f, s3f[k][f], s0f[k][f])
    # Restored grant state == the reconciled policy (hardening
    # legitimately persists; raw baseline vs policy delta was disclosed
    # in S2 above, not compared to S0 here).
    for k in s0f:
        assert s3f[k]["grants"] == s2f[k]["grants"], (k, s3f[k]["grants"])
    for key in (
        "alembic_version",
        "workspace_columns",
        "tables",
        "baseline_workspace_row",
    ):
        assert s3[key] == s0[key], (key, s3[key], s0[key])
    async with owner_connection(dsn, expected_database=db_name) as owner:
        assert await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_legacy) == v1_row_bytes
        inv65 = await _rt_invoke_constructors(
            owner, seed["site_id"], seed["user_id"], check_version_facts=False
        )
    assert inv65["ws_create"] is not None
    assert inv65["editor_resolve_insert_path"] is not None
    assert inv65["agent_ws_create"] is not None

    # --- P4: upgrade back to head + reconcile ---------------------------
    await run_migration(
        dsn, expected_database=db_name, operation="upgrade", revision="head"
    )
    await reconcile(database.settings)
    s4: dict[str, Any] = {}
    async with owner_connection(dsn, expected_database=db_name) as owner:
        s4 = await _rt_capture_state(owner, seed)
    s4f = s4["control_functions"]
    non_helper_bad = [
        k for k in s2f if k not in _RT_NEW_076_KEYS and s4f.get(k) != s2f[k]
    ]
    assert not non_helper_bad, non_helper_bad[:5]
    for k in _RT_NEW_076_KEYS:
        for f in _RT_IDENTITY_FIELDS:
            assert s4f[k][f] == s2f[k][f], (k, f)
        assert s4f[k]["grants"] == s2f[k]["grants"], k
    assert all(s4f[k]["oid"] == s0f[k]["oid"] for k in s0f)
    for key in (
        "alembic_version",
        "workspace_columns",
        "tables",
        "baseline_workspace_row",
        "marker",
    ):
        assert s4[key] == s2[key], (key, s4[key], s2[key])


@pytest.mark.asyncio
async def test_two_workspace_revision_coherence_and_stale_refusal(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """083/4 A (integration half) + C.

    W1 is edited at A; a different authorized workspace publishes an
    unrelated change to B; W1 then freezes with B as its coherent review
    base.  A later publication C makes the old W1 review stale: approval
    is refused with SITE_REVISION_CHANGED (not a digest error) and with
    zero canonical/audit/outbox effect; W1's pending public operations
    are retained exactly.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        site_id = ids["site_id"]
        delegator_id = ids["delegator_id"]
        ws1 = ids["workspace_id"]

        async def revision() -> int:
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                return int(
                    await owner.fetchval(
                        "SELECT canonical_revision FROM control.site WHERE id = $1",
                        site_id,
                    )
                )

        async def composition_fingerprint() -> str:
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                return str(
                    await owner.fetchval(
                        "SELECT encode(sha256(convert_to(string_agg("
                        " component_type || '|' || props::text || '|'"
                        " || row_version::text, '' ORDER BY id),'UTF8')),"
                        " 'hex') FROM content.page_composition_base"
                    )
                )

        A = await revision()
        assert A == 0

        # W1 edits at A (one real COW operation).
        w1_marker = "083/4 W1 marker"
        await _cow_create(
            database,
            workspace_id=ws1,
            capability_id=ids["capability_id"],
            site_id=site_id,
            page_id=ids["page_id"],
            parent_id=ids["section_id"],
            text=w1_marker,
        )

        # W2: a different authorized workspace publishes an unrelated
        # change to B through the real freeze + human accept path.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            ws2, cap2 = await _create_workspace(
                owner, site_id, delegator_id, "083/4 W2"
            )
        w2_marker = "083/4 W2 marker"
        await _cow_create(
            database,
            workspace_id=ws2,
            capability_id=cap2,
            site_id=site_id,
            page_id=ids["page_id"],
            parent_id=ids["section_id"],
            text=w2_marker,
        )
        result2, _job2 = await _freeze_claim_run(
            database,
            workspace_id=ws2,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-f2",
        )
        assert result2.status == "SUCCEEDED", result2.error
        result2a, _job2a = await _accept_claim_run(
            database,
            workspace_id=ws2,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-a2",
            boundary=boundary,
        )
        assert result2a.status == "SUCCEEDED", result2a.error
        B = await revision()
        assert B == A + 1

        # W1's creation-time provenance is preserved (still A).
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            w1_creation_base = int(
                await owner.fetchval(
                    "SELECT base_site_revision FROM control.workspace WHERE id = $1",
                    ws1,
                )
            )
        assert w1_creation_base == A

        # W1 freezes after B: coherent review base B with B+W content.
        result1, _job1 = await _freeze_claim_run(
            database,
            workspace_id=ws1,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-f1",
        )
        assert result1.status == "SUCCEEDED", result1.error
        snap1 = await _snapshot_row(database, ws1)
        assert snap1 is not None
        snap1_id = UUID(str(snap1["id"]))
        assert UUID(str(snap1["workspace_id"])) == ws1
        assert UUID(str(snap1["site_id"])) == site_id
        payload1 = json.loads(snap1["payload"])
        assert payload1["base_site_revision"] == B
        assert await _digest_is_valid(database, snap1_id)
        texts1 = await _snapshot_heading_texts(database, snap1_id)
        assert w2_marker in texts1  # B's published content is retained
        assert w1_marker in texts1  # W's own visible overlay is retained
        # The displayed reviewed/current revisions agree before another
        # publication (the trusted review read model, control role).
        review_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_review_read_model($1,$2,$3)",
            ws1,
            site_id,
            delegator_id,
        )
        review1 = json.loads(review_rows[0][0])
        assert int(review1["snapshot"]["base_site_revision"]) == B
        assert int(review1["drift"]["current_site_revision"]) == B
        assert review1["drift"]["equal"] is True

        # C: a valid different workspace publishes C (B -> C).
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            ws3, cap3 = await _create_workspace(
                owner, site_id, delegator_id, "083/4 W3"
            )
        w3_marker = "083/4 W3 marker"
        await _cow_create(
            database,
            workspace_id=ws3,
            capability_id=cap3,
            site_id=site_id,
            page_id=ids["page_id"],
            parent_id=ids["section_id"],
            text=w3_marker,
        )
        result3, _job3 = await _freeze_claim_run(
            database,
            workspace_id=ws3,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-f3",
        )
        assert result3.status == "SUCCEEDED", result3.error
        result3a, _job3a = await _accept_claim_run(
            database,
            workspace_id=ws3,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-a3",
            boundary=boundary,
        )
        assert result3a.status == "SUCCEEDED", result3a.error
        C = await revision()
        assert C == B + 1
        before_refusal = await composition_fingerprint()
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            audit_before = int(
                await owner.fetchval("SELECT count(*) FROM audit.promotion")
            )
            outbox_before = int(
                await owner.fetchval("SELECT count(*) FROM control.cache_outbox")
            )
        ops_before = await _public_operations(database, ws1)
        assert len(ops_before) == 1
        review_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_review_read_model($1,$2,$3)",
            ws1,
            site_id,
            delegator_id,
        )
        review1b = json.loads(review_rows[0][0])
        assert int(review1b["drift"]["current_site_revision"]) == C
        assert review1b["drift"]["equal"] is False

        # Approval of the old W1 snapshot: refused with the stable drift
        # code, never a digest error (the preflight checks the trusted
        # stored revision before re-materialization).
        result_stale, job_stale = await _accept_claim_run(
            database,
            workspace_id=ws1,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-stale",
            boundary=boundary,
        )
        assert result_stale.status == "FAILED"
        assert result_stale.error == "SITE_REVISION_CHANGED"

        # Zero mutation by the refused attempt.
        after_refusal = await composition_fingerprint()
        assert after_refusal == before_refusal
        assert await revision() == C
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            assert (
                int(await owner.fetchval("SELECT count(*) FROM audit.promotion"))
                == audit_before
            )
            assert (
                int(await owner.fetchval("SELECT count(*) FROM control.cache_outbox"))
                == outbox_before
            )
            workspace1 = await owner.fetchrow(
                "SELECT status, accepted_at, review_snapshot_id"
                " FROM control.workspace WHERE id = $1",
                ws1,
            )
            snap1_digest = await owner.fetchval(
                "SELECT digest FROM control.review_snapshot WHERE id = $1",
                snap1_id,
            )
        # W1's pending operations survive exactly (public foundation
        # inspection, not a private changes-table probe).
        ops_after = await _public_operations(database, ws1)
        assert ops_after == ops_before
        assert str(workspace1["status"]) == "REVIEW"
        assert workspace1["accepted_at"] is None
        assert UUID(str(workspace1["review_snapshot_id"])) == snap1_id
        assert str(snap1_digest) == str(snap1["digest"])
        assert await _digest_is_valid(database, snap1_id)
        # The refused job carries the stable code on its terminal row.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_stale,
            )
        assert str(job_row["status"]) == "FAILED"
        assert str(job_row["error"]) == "SITE_REVISION_CHANGED"
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_same_site_accept_freeze_serialization_both_orderings(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """083/4 B: controlled same-site accept/freeze races, both orderings.

    Synchronization is on the real production lock surface (the canonical
    site row ``FOR UPDATE``).  Row waits are frequently fast-path and
    invisible in pg_locks, so waiters are identified as active backends
    by their real current query (pg_stat_activity) and every blocking
    relationship is proven with ``pg_blocking_pids`` against the observed
    blocker PID; there is no sleep-only race.

    Both competing jobs are real requests: enqueue + claim happen while
    the canonical row is still free (the freeze enqueue itself
    serializes on the site row through its site-governance authority
    re-check, so it must not be staged against a held row); only the
    worker RUNS join the race on the row.  ``pg_blocking_pids`` reports
    direct lock-queue edges, so a queued second waiter proves its
    ordered chain through the first waiter's exact ``{holder}`` edge
    plus its own direct edge containing the first waiter.

    Ordering 1 (freeze wins): the freeze's materializer queues on the
    site row before the accept's preflight does, so after release the
    row-lock wait queue grants the row to the freeze first; it completes
    coherently and the accept then publishes.

    Ordering 2 (accept wins): a fixture barrier around the REAL media
    finalization pauses the accept job between the committed preflight
    and the final reviewer transaction.  While a fixture blocker holds
    the canonical row, the barrier releases and the ACTUAL final
    promotion transaction is observed queued on the site row (its PID
    blocked by the blocker PID) BEFORE the competing freeze starts.
    After the blocker releases, the promotion acquires the row first (its
    request queued ahead) and the freeze then materializes at the NEW
    revision.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    owner_dsn = database.settings.resolved_owner_dsn()
    owner_login, owner_password = database.credentials["slaif_owner"]
    try:
        site_id = ids["site_id"]
        delegator_id = ids["delegator_id"]

        async def revision() -> int:
            async with owner_connection(
                owner_dsn, expected_database=database.name
            ) as owner:
                return int(
                    await owner.fetchval(
                        "SELECT canonical_revision FROM control.site WHERE id = $1",
                        site_id,
                    )
                )

        async def seed_workspace(title: str, marker: str) -> tuple[UUID, UUID]:
            async with owner_connection(
                owner_dsn, expected_database=database.name
            ) as owner:
                workspace_id, capability_id = await _create_workspace(
                    owner, site_id, delegator_id, title
                )
            await _cow_create(
                database,
                workspace_id=workspace_id,
                capability_id=capability_id,
                site_id=site_id,
                page_id=ids["page_id"],
                parent_id=ids["section_id"],
                text=marker,
            )
            return workspace_id, capability_id

        async def blocker_hold_site_row() -> tuple[Any, Any, int]:
            """Fixture blocker: a real open transaction holding the row.

            Returns (connection, transaction, pid); the caller must
            commit (release) or roll back the real transaction handle.
            """

            blocker = await asyncpg.connect(
                dsn=_dsn(database, owner_login, owner_password)
            )
            await blocker.execute("SET ROLE slaif_owner")
            await blocker.execute("SET lock_timeout = '30s'")
            transaction = blocker.transaction()
            await transaction.start()
            await blocker.execute(
                "SELECT id FROM control.site WHERE id = $1 FOR UPDATE",
                site_id,
            )
            return (
                blocker,
                transaction,
                int(await blocker.fetchval("SELECT pg_backend_pid()")),
            )

        A = await revision()
        assert A == 0

        # --- Ordering 1: freeze wins ------------------------------------
        # W3 is frozen at A (accept candidate); W4 (frozen during the race)
        # is the freeze candidate.
        ws3, _cap3 = await seed_workspace("083/4 W3", "083/4 W3 marker")
        ws4, _cap4 = await seed_workspace("083/4 W4", "083/4 W4 marker")
        result3, _job3 = await _freeze_claim_run(
            database,
            workspace_id=ws3,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-f3",
        )
        assert result3.status == "SUCCEEDED", result3.error
        snap3 = await _snapshot_row(database, ws3)
        assert snap3 is not None
        assert int(json.loads(snap3["payload"])["base_site_revision"]) == A

        # W4's freeze and W3's accept are real jobs requested while the
        # canonical row is still free; only their worker runs race on
        # the row.
        _job4_id, job4_claimed = await _freeze_enqueue_claim(
            database,
            workspace_id=ws4,
            site_id=site_id,
            delegator_id=delegator_id,
            claimant="083-4-f4",
        )
        rows = await _enqueue_accept(database, ws3, delegator_id)
        job3_accept = UUID(str(rows[0]["job_id"]))
        job3_claimed = await _claim_accept_job(
            database, claimant="083-4-a3", expected_job_id=job3_accept
        )

        blocker, blocker_txn, blocker_pid = await blocker_hold_site_row()
        released1 = False
        freeze_task = asyncio.create_task(
            run_freeze_job(pool, _worker_settings(database), job4_claimed)
        )
        accept_task: asyncio.Task[Any] | None = None
        try:
            # The freeze's materializer queues on the blocked site row,
            # really blocked by the blocker PID.
            freeze_pid = await _wait_for_blocked_waiter(
                database,
                query_predicate=_freeze_materializer_wait,
                expected_blockers={blocker_pid},
                label="ordering-1 freeze materializer",
                timeout=30.0,
                diagnostic=freeze_task,
            )
            accept_task = asyncio.create_task(
                run_accept_job(
                    pool,
                    _worker_settings(database),
                    job3_claimed,
                    media=boundary,
                )
            )
            # The accept's preflight queues behind the same site row
            # (its request entered the wait queue after the freeze's).
            # The direct lock-queue edge is the first waiter itself; the
            # ordered preflight -> freeze -> blocker chain is proven by
            # the freeze's exact {blocker} edge above.
            preflight_pid = await _wait_for_blocked_waiter(
                database,
                query_predicate=_accept_site_lock,
                blockers_match=lambda blockers: (
                    set(blockers) in ({freeze_pid}, {freeze_pid, blocker_pid})
                ),
                label="ordering-1 accept preflight",
                timeout=30.0,
                diagnostic=accept_task,
            )
            assert preflight_pid != freeze_pid
            # Release: the row-lock wait queue grants the row to the
            # first queued waiter (the freeze), then to the preflight.
            await blocker_txn.commit()
            released1 = True
            result4, result3a = await asyncio.wait_for(
                asyncio.gather(freeze_task, accept_task), timeout=180.0
            )
        except BaseException:
            for task in (accept_task, freeze_task):
                if task is not None and not task.done():
                    task.cancel()
            await asyncio.gather(
                *(t for t in (accept_task, freeze_task) if t is not None),
                return_exceptions=True,
            )
            raise
        finally:
            if not released1:
                with contextlib.suppress(Exception):
                    await blocker_txn.rollback()
            await blocker.close()
        assert result4.status == "SUCCEEDED", result4.error
        assert result3a.status == "SUCCEEDED", result3a.error
        B1 = await revision()
        assert B1 == A + 1

        # The freeze snapshot completed coherently BEFORE the accept's
        # promotion: it carries A + exactly W4's overlay, byte-valid.
        snap4 = await _snapshot_row(database, ws4)
        assert snap4 is not None
        snap4_id = UUID(str(snap4["id"]))
        assert int(json.loads(snap4["payload"])["base_site_revision"]) == A
        assert await _digest_is_valid(database, snap4_id)
        texts4 = await _snapshot_heading_texts(database, snap4_id)
        assert "083/4 W4 marker" in texts4
        assert "083/4 W3 marker" not in texts4
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            snapshot_at = snap4["created_at"]
            promotion_at = await owner.fetchval(
                "SELECT created_at FROM audit.promotion WHERE workspace_id = $1",
                ws3,
            )
            audit_row = await owner.fetchrow(
                "SELECT base_site_revision, new_canonical_revision"
                " FROM audit.promotion WHERE workspace_id = $1",
                ws3,
            )
        assert snapshot_at < promotion_at
        assert int(audit_row["base_site_revision"]) == A
        assert int(audit_row["new_canonical_revision"]) == B1

        # --- Ordering 2: accept wins ------------------------------------
        # W5 frozen at B1 (accept candidate); W6's freeze runs during the
        # accept and must record the NEW revision + content.
        ws5, _cap5 = await seed_workspace("083/4 W5", "083/4 W5 marker")
        ws6, _cap6 = await seed_workspace("083/4 W6", "083/4 W6 marker")
        result5, _job5 = await _freeze_claim_run(
            database,
            workspace_id=ws5,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-f5",
        )
        assert result5.status == "SUCCEEDED", result5.error
        snap5 = await _snapshot_row(database, ws5)
        assert snap5 is not None
        assert int(json.loads(snap5["payload"])["base_site_revision"]) == B1

        # W6's freeze is a real job requested while the canonical row is
        # still free; only its worker run joins the race.
        _job6_id, job6_claimed = await _freeze_enqueue_claim(
            database,
            workspace_id=ws6,
            site_id=site_id,
            delegator_id=delegator_id,
            claimant="083-4-f6",
        )

        # Barrier seam: the accept pauses after its real media
        # finalization, before the final reviewer transaction.
        pausing_boundary = _PausingMediaBoundary(boundary)
        _barrier, entered = pausing_boundary.arm()
        rows = await _enqueue_accept(database, ws5, delegator_id)
        job5_accept = UUID(str(rows[0]["job_id"]))
        accept_task = asyncio.create_task(
            _accept_claim_run(
                database,
                workspace_id=ws5,
                delegator_id=delegator_id,
                pool=pool,
                claimant="083-4-a5",
                boundary=pausing_boundary,
                job_id=job5_accept,
            )
        )
        freeze_task2: asyncio.Task[Any] | None = None
        blocker2: Any = None
        blocker2_txn: Any = None
        released2 = False
        try:
            try:
                await asyncio.wait_for(entered.wait(), timeout=60.0)
            except BaseException:
                accept_task.cancel()
                await asyncio.gather(accept_task, return_exceptions=True)
                raise
            # The accept job is parked between the committed preflight
            # and the final reviewer transaction; the row is free.  Hold
            # it with a fixture blocker, then release the barrier so the
            # actual final promotion transaction queues on the blocked
            # row.
            blocker2, blocker2_txn, blocker_pid = await blocker_hold_site_row()
            pausing_boundary.release()
            # The ACTUAL final promotion transaction is queued on the
            # blocked row; its real blocker is the fixture holder PID.
            promotion_pid = await _wait_for_blocked_waiter(
                database,
                query_predicate=_accept_site_lock,
                expected_blockers={blocker_pid},
                label="ordering-2 final promotion transaction",
                timeout=30.0,
                diagnostic=accept_task,
            )
            # Now (and only now) the competing freeze run starts; its
            # materializer queues behind the promotion's request.
            freeze_task2 = asyncio.create_task(
                run_freeze_job(pool, _worker_settings(database), job6_claimed)
            )
            try:
                # The freeze queued behind the promotion's request: the
                # direct lock-queue edge is the promotion waiter itself;
                # the ordered freeze -> promotion -> holder chain is
                # proven by the promotion's exact {blocker} edge above.
                freeze_pid = await _wait_for_blocked_waiter(
                    database,
                    query_predicate=_freeze_materializer_wait,
                    blockers_match=lambda blockers: (
                        set(blockers) in ({promotion_pid}, {promotion_pid, blocker_pid})
                    ),
                    label="ordering-2 freeze materializer",
                    timeout=30.0,
                    diagnostic=freeze_task2,
                )
                assert freeze_pid != promotion_pid
                # Release: the promotion's request is queued first, so it
                # acquires the row and publishes before the freeze's
                # materialization can run.
                await blocker2_txn.commit()
                released2 = True
                result6, (result5a, _job5a) = await asyncio.wait_for(
                    asyncio.gather(freeze_task2, accept_task), timeout=180.0
                )
            except BaseException:
                for task in (freeze_task2, accept_task):
                    if task is not None and not task.done():
                        task.cancel()
                await asyncio.gather(
                    *(t for t in (freeze_task2, accept_task) if t is not None),
                    return_exceptions=True,
                )
                raise
        finally:
            pausing_boundary.release()
            if blocker2 is not None:
                if not released2:
                    with contextlib.suppress(Exception):
                        await blocker2_txn.rollback()
                await blocker2.close()
            for task in (freeze_task2, accept_task):
                if task is not None and not task.done():
                    task.cancel()
            await asyncio.gather(
                *(t for t in (freeze_task2, accept_task) if t is not None),
                return_exceptions=True,
            )
        assert result5a.status == "SUCCEEDED", result5a.error
        assert result6.status == "SUCCEEDED", result6.error
        B2 = await revision()
        assert B2 == B1 + 1

        # The accept won: the snapshot records the NEW revision B2 and its
        # content (W5's promotion is present, W6's overlay is present).
        snap6 = await _snapshot_row(database, ws6)
        assert snap6 is not None
        snap6_id = UUID(str(snap6["id"]))
        assert int(json.loads(snap6["payload"])["base_site_revision"]) == B2
        assert await _digest_is_valid(database, snap6_id)
        texts6 = await _snapshot_heading_texts(database, snap6_id)
        assert "083/4 W5 marker" in texts6
        assert "083/4 W6 marker" in texts6
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            audit_row = await owner.fetchrow(
                "SELECT base_site_revision, new_canonical_revision"
                " FROM audit.promotion WHERE workspace_id = $1",
                ws5,
            )
            ws5_state = await owner.fetchval(
                "SELECT status FROM control.workspace WHERE id = $1", ws5
            )
        assert int(audit_row["base_site_revision"]) == B1
        assert int(audit_row["new_canonical_revision"]) == B2
        assert str(ws5_state) == "ACCEPTED"
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_first_touch_conflict_baseline_survives_freeze(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """083/4 D: the public frozen foundation conflict inspection.

    W1 touches a row at A; a different authorized workspace changes the
    SAME row and publishes B; the public inspection already reports
    BASE_ROW_CHANGED for W1.  W1's real B freeze leaves that first-touch
    baseline unchanged: the identical public conflict remains before and
    after the freeze, and with no later drift the accept probe passes
    the new revision gate and reaches the foundation row-conflict gate
    (the stable BASE_ROW_CHANGED code) with zero canonical mutation.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    owner_dsn = database.settings.resolved_owner_dsn()
    try:
        site_id = ids["site_id"]
        delegator_id = ids["delegator_id"]
        ws1 = ids["workspace_id"]

        async def revision() -> int:
            async with owner_connection(
                owner_dsn, expected_database=database.name
            ) as owner:
                return int(
                    await owner.fetchval(
                        "SELECT canonical_revision FROM control.site WHERE id = $1",
                        site_id,
                    )
                )

        async def composition_fingerprint() -> str:
            async with owner_connection(
                owner_dsn, expected_database=database.name
            ) as owner:
                return str(
                    await owner.fetchval(
                        "SELECT encode(sha256(convert_to(string_agg("
                        " component_type || '|' || props::text || '|'"
                        " || row_version::text, '' ORDER BY id),'UTF8')),"
                        " 'hex') FROM content.page_composition_base"
                    )
                )

        A = await revision()
        assert A == 0

        # W1 touches the seeded heading at A (its first-touch baseline is
        # the base row at version 1).
        await _cow_update(
            database,
            workspace_id=ws1,
            capability_id=ids["capability_id"],
            site_id=site_id,
            component_id=ids["heading_id"],
            props={"level": 2, "text": "083/4 W1 touched"},
        )
        assert await _public_conflicts(database, ws1) == []

        # A genuinely concurrent change to the SAME row: another
        # authorized workspace updates the heading and publishes B
        # through the real freeze + human accept path.
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            ws2, cap2 = await _create_workspace(
                owner, site_id, delegator_id, "083/4 W2"
            )
        await _cow_update(
            database,
            workspace_id=ws2,
            capability_id=cap2,
            site_id=site_id,
            component_id=ids["heading_id"],
            props={"level": 1, "text": "083/4 W2 concurrent"},
        )
        result2, _job2 = await _freeze_claim_run(
            database,
            workspace_id=ws2,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-fd2",
        )
        assert result2.status == "SUCCEEDED", result2.error
        result2a, _job2a = await _accept_claim_run(
            database,
            workspace_id=ws2,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-ad2",
            boundary=boundary,
        )
        assert result2a.status == "SUCCEEDED", result2a.error
        B = await revision()
        assert B == A + 1
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            assert (
                int(
                    await owner.fetchval(
                        "SELECT row_version FROM content.page_composition_base"
                        " WHERE id = $1",
                        ids["heading_id"],
                    )
                )
                == 2
            )

        # The public inspection already reports the touched-row conflict
        # BEFORE W1 freezes.
        conflicts_before_freeze = await _public_conflicts(database, ws1)
        assert len(conflicts_before_freeze) == 1
        conflict = conflicts_before_freeze[0]
        assert conflict["conflict_kind"] == "BASE_ROW_CHANGED"
        assert conflict["table_name"] == "page_composition"
        assert conflict["primary_key"]["id"] == str(ids["heading_id"])

        # W1's real B freeze must leave the first-touch baseline
        # unchanged: the identical public conflict remains after it.
        result1, _job1 = await _freeze_claim_run(
            database,
            workspace_id=ws1,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-fd1",
        )
        assert result1.status == "SUCCEEDED", result1.error
        snap1 = await _snapshot_row(database, ws1)
        assert snap1 is not None
        snap1_id = UUID(str(snap1["id"]))
        assert int(json.loads(snap1["payload"])["base_site_revision"]) == B
        assert await _digest_is_valid(database, snap1_id)
        conflicts_after_freeze = await _public_conflicts(database, ws1)
        assert conflicts_after_freeze == conflicts_before_freeze
        ops_before = await _public_operations(database, ws1)
        assert len(ops_before) == 1

        # No later drift: the accept probe passes the new revision gate
        # and reaches the foundation row-conflict gate.
        before_refusal = await composition_fingerprint()
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            audit_before = int(
                await owner.fetchval("SELECT count(*) FROM audit.promotion")
            )
            outbox_before = int(
                await owner.fetchval("SELECT count(*) FROM control.cache_outbox")
            )
        result_stale, _job_stale = await _accept_claim_run(
            database,
            workspace_id=ws1,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-astale",
            boundary=boundary,
        )
        assert result_stale.status == "FAILED"
        assert result_stale.error == "BASE_ROW_CHANGED"
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            workspace1 = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                ws1,
            )
            assert (
                int(await owner.fetchval("SELECT count(*) FROM audit.promotion"))
                == audit_before
            )
            assert (
                int(await owner.fetchval("SELECT count(*) FROM control.cache_outbox"))
                == outbox_before
            )
        # Zero canonical mutation; W1's pending operations survive
        # exactly (public foundation inspection).
        assert await composition_fingerprint() == before_refusal
        assert await revision() == B
        assert await _public_operations(database, ws1) == ops_before
        assert str(workspace1["status"]) == "CONFLICTED"
        assert workspace1["accepted_at"] is None
        assert await _digest_is_valid(database, snap1_id)
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_freeze_site_lock_failure_rollback_no_leaked_lock(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """083/4 E: DB failure mid-freeze.

    A blocked site-row wait (lock timeout) rolls the whole freeze
    transaction back: no snapshot row, no REVIEW state, terminal FAILED
    job, and no leaked site lock (no worker backend left on the site
    statement and the row is immediately re-acquirable).  The reclaim is
    idempotent, and an earlier immutable snapshot stays byte-identical.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    owner_dsn = database.settings.resolved_owner_dsn()
    owner_login, owner_password = database.credentials["slaif_owner"]
    try:
        site_id = ids["site_id"]
        delegator_id = ids["delegator_id"]
        ws1 = ids["workspace_id"]

        async def snapshot_row_fingerprint(workspace_id: UUID) -> str:
            async with owner_connection(
                owner_dsn, expected_database=database.name
            ) as owner:
                return str(
                    await owner.fetchval(
                        "SELECT coalesce(encode(sha256(convert_to("
                        " digest || '|' || payload::text || '|'"
                        " || normalized_state::text,'UTF8')),'hex'),'none')"
                        " FROM control.review_snapshot"
                        " WHERE workspace_id = $1",
                        workspace_id,
                    )
                )

        # Baseline: a second workspace freezes successfully first.
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            ws2, _cap2 = await _create_workspace(
                owner, site_id, delegator_id, "083/4 W2"
            )
        result2, _job2 = await _freeze_claim_run(
            database,
            workspace_id=ws2,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-fe2",
        )
        assert result2.status == "SUCCEEDED", result2.error
        fingerprint2_before = await snapshot_row_fingerprint(ws2)
        assert fingerprint2_before != "none"

        # W1's freeze is a real job requested while the canonical row is
        # free (the enqueue itself serializes on the site row); the run
        # is what fails on the blocked site row (bounded lock timeout).
        job1, job1_claimed = await _freeze_enqueue_claim(
            database,
            workspace_id=ws1,
            site_id=site_id,
            delegator_id=delegator_id,
            claimant="083-4-fe1",
        )

        # W1's freeze fails on a blocked site row (bounded lock timeout).
        blocker = await asyncpg.connect(dsn=_dsn(database, owner_login, owner_password))
        await blocker.execute("SET ROLE slaif_owner")
        await blocker.execute("SET lock_timeout = '30s'")
        try:
            async with blocker.transaction():
                await blocker.execute(
                    "SELECT id FROM control.site WHERE id = $1 FOR UPDATE",
                    site_id,
                )
                result1 = await run_freeze_job(
                    pool,
                    _0834_settings(database, drain_seconds=5.0),
                    job1_claimed,
                )
        finally:
            await blocker.close()
        assert result1.status == "FAILED"
        assert result1.error == "SNAPSHOT_MATERIALIZE_FAILED"

        # Rollback effects: no snapshot, no REVIEW, terminal FAILED job.
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            snapshot_count = int(
                await owner.fetchval(
                    "SELECT count(*) FROM control.review_snapshot"
                    " WHERE workspace_id = $1",
                    ws1,
                )
            )
            workspace_status = await owner.fetchval(
                "SELECT status FROM control.workspace WHERE id = $1", ws1
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job1,
            )
        assert snapshot_count == 0
        assert str(workspace_status) == "FREEZING"
        assert str(job_row["status"]) == "FAILED"
        assert str(job_row["error"]) == "SNAPSHOT_MATERIALIZE_FAILED"

        # No leaked site lock: no worker backend remains on the site or
        # materializer statement, and a fresh owner FOR UPDATE acquires
        # the row immediately.
        active = await _active_queries(database)
        assert not any(
            _freeze_materializer_wait(query) or _accept_site_lock(query)
            for _pid, query in active
        ), active
        releaser = await asyncpg.connect(
            dsn=_dsn(database, owner_login, owner_password)
        )
        await releaser.execute("SET ROLE slaif_owner")
        await releaser.execute("SET lock_timeout = '10s'")
        try:
            async with releaser.transaction():
                acquired = await releaser.fetchval(
                    "SELECT id FROM control.site WHERE id = $1 FOR UPDATE",
                    site_id,
                )
            assert UUID(str(acquired)) == site_id
        finally:
            await releaser.close()

        # The earlier immutable snapshot is byte-identical.
        assert await snapshot_row_fingerprint(ws2) == fingerprint2_before

        # Reclaim: the FREEZING workspace accepts exactly one new job and
        # it completes (idempotent retry semantics).
        result1b, job1b = await _freeze_claim_run(
            database,
            workspace_id=ws1,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-4-fe1b",
        )
        assert result1b.status == "SUCCEEDED", result1b.error
        assert job1b != job1
        snap1 = await _snapshot_row(database, ws1)
        assert snap1 is not None
        snap1_id = UUID(str(snap1["id"]))
        assert await _digest_is_valid(database, snap1_id)
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            assert (
                int(
                    await owner.fetchval(
                        "SELECT count(*) FROM control.review_snapshot"
                        " WHERE workspace_id = $1",
                        ws1,
                    )
                )
                == 1
            )
            workspace_status = await owner.fetchval(
                "SELECT status FROM control.workspace WHERE id = $1", ws1
            )
            revision = int(
                await owner.fetchval(
                    "SELECT canonical_revision FROM control.site WHERE id = $1",
                    site_id,
                )
            )
        assert str(workspace_status) == "REVIEW"
        assert int(json.loads(snap1["payload"])["base_site_revision"]) == revision
    finally:
        await boundary.stop()
        await pool.close()


def _review_http_body(snapshot_id: UUID, path: str) -> dict[str, Any]:
    return {
        "authority": "localhost",
        "path": path,
        "snapshot_id": str(snapshot_id),
    }


def _walk_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Depth-first walk of the actual composition tree (test-side)."""

    walked: list[dict[str, Any]] = []
    for node in nodes:
        walked.append(node)
        walked.extend(_walk_nodes(node.get("children") or []))
    return walked


async def test_review_endpoint_frozen_read_media_urls_and_role_denials(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Faithful frozen review read on the real role/driver boundary.

    A current human session reads the COMPLETE v2 snapshot through the
    internal render route (ASGI, real role pools, standard driver):
    DRAFT pages stay resolvable (active-preview candidate policy over
    the captured workspace), captured media resolves to the
    snapshot-authorized byte URL for BOTH stored publication statuses,
    and exact fractional digits survive the JSONB -> admission round
    trip.  The public reader cannot execute the 076 read functions,
    every invalid input is a stable 404, and the read touches nothing
    (last_seen_at equality across the whole read sequence).  The
    discard runs to its real terminal worker state before the
    after-read.  This case is owner-seeded canonical fixture evidence
    at the internal route only: it does not prove public Web/NGINX
    serving, Agent/Editor writes, or actual private media bytes; those
    keep their real-workflow obligations.
    """
    from decimal import Decimal

    database = agent_site_database
    seeded = await _seed(database)
    workspace_id = seeded["workspace_id"]
    site_id = seeded["site_id"]

    # A DRAFT page (active-preview candidate policy must carry into
    # frozen review) and a MapBlock carrying a 23-digit fraction whose
    # float64 round trip would change the canonical text.
    draft_page_id = uuid4()
    draft_section_id = uuid4()
    draft_map_id = uuid4()
    exact_fraction = "0.10000000000000000000001"
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO content.page_base (id, site_id, slug, title, status,"
            " locale) VALUES ($1,$2,'draft','Draft page','DRAFT','en-US')",
            draft_page_id,
            site_id,
        )
        await owner.execute(
            "INSERT INTO content.page_composition_base (id, site_id, page_id,"
            " component_type, schema_version, parent_id, slot_key, order_key,"
            " props) VALUES"
            " ($1,$2,$3,'Section','1',NULL::uuid,'default',0,'{}'::jsonb),"
            " ($4,$2,$3,'MapBlock','1',$1,'default',0,"
            "  jsonb_build_object('title','Exact',"
            "   'bbox', jsonb_build_object("
            "     'west',$5::numeric,"
            "     'south',-1,'east',1,'north',1)))",
            draft_section_id,
            site_id,
            draft_page_id,
            draft_map_id,
            exact_fraction,
        )
        # The frozen review human session for the seeded SITE_OWNER.
        session_id = uuid4()
        review_secret = b"r" * 32
        review_public_id = f"sas2_{session_id.hex}"
        await owner.execute(
            "INSERT INTO control.user_session (id, public_id, secret_digest,"
            " csrf_secret_digest, user_account_id, absolute_expires_at)"
            " VALUES ($1,$2,$3,$4,$5, now() + interval '1 hour')",
            session_id,
            review_public_id,
            hashlib.sha256(review_secret).digest(),
            b"c" * 32,
            seeded["delegator_id"],
        )
    review_token = format_session_token(
        review_public_id, review_secret
    ).get_secret_value()

    # Freeze: real control enqueue + real worker claim + real run.
    job_id, _ = await _freeze(database, seeded)
    pool = await _worker_pool(database)
    try:
        rows = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "review-endpoint-worker",
            ["FREEZE", "ACCEPT"],
        )
        assert len(rows) == 1
        assert str(rows[0]["id"]) == str(job_id)
        result = await run_freeze_job(pool, _worker_settings(database), dict(rows[0]))
        assert result.status == "SUCCEEDED", result.error
    finally:
        await pool.close()

    snapshot = await _snapshot_row(database, workspace_id)
    assert snapshot is not None and snapshot["status"] == "COMPLETE"
    snapshot_id: UUID = snapshot["id"]

    # Exact-digit fidelity through the real JSONB storage round trip:
    # the stored payload must still carry the 23-digit fraction and the
    # exact-number decode must reproduce the stored digest.
    stored_payload: Any = parse_snapshot_text(
        json.dumps(snapshot["payload"])
        if not isinstance(snapshot["payload"], str)
        else snapshot["payload"]
    )
    assert isinstance(stored_payload, dict)
    captured_map = None
    for row in stored_payload["page_compositions"]:
        if str(row.get("id")) == str(draft_map_id):
            captured_map = row
            break
    assert captured_map is not None
    assert captured_map["props"]["bbox"]["west"] == Decimal(exact_fraction), (
        "JSONB round trip must retain every written digit"
    )
    assert canonical_digest(stored_payload) == str(snapshot["digest"])

    # No-touch baseline: the 010 session row carries a NOT NULL
    # last_seen_at, so the proof is before/after equality across the
    # entire review read sequence, never a NULL assertion.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        before_last_seen = await owner.fetchval(
            "SELECT last_seen_at FROM control.user_session WHERE id = $1",
            session_id,
        )
        assert before_last_seen is not None

    render_adapter = _RestartableRenderAdapter(database)
    await render_adapter.start()
    render_app = create_render_app(
        settings=ServiceSettings.for_test(),
        database=render_adapter,
    )
    try:
        async with render_app.router.lifespan_context(render_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=render_app),
                base_url="http://render.test",
            ) as client:
                # PUBLISHED page: frozen bytes, snapshot media URL.
                response = await client.post(
                    "/internal/render/v1/review",
                    headers={"X-SLAIF-Human-Session": review_token},
                    json=_review_http_body(snapshot_id, "/"),
                )
                assert response.status_code == 200, response.text
                body = response.json()
                assert body["render_mode"] == "review"
                assert body["page"]["title"] == "Home"
                # The seeded Image hangs below the root Section: walk
                # the actual descendant tree (the product hierarchy is
                # never flattened) and assert identity, type and the
                # frozen byte URL.
                home_nodes = _walk_nodes(body["composition"]["nodes"])
                media_nodes = [
                    node for node in home_nodes if node.get("media") is not None
                ]
                assert len(media_nodes) == 1
                media_node = media_nodes[0]
                assert media_node["component_type"] == "Image"
                assert media_node["props"]["mediaId"] == str(seeded["media_id"])
                assert media_node["media"] == {
                    "url": (
                        f"/media/v1/review/{snapshot_id}"
                        f"/assets/{seeded['media_id']}/content"
                    ),
                    "mime_type": "image/png",
                    "size_bytes": 128,
                }
                # The frozen media map is exactly the seeded asset.
                assert set(stored_payload["media"].keys()) == {str(seeded["media_id"])}
                assert response.headers["Cache-Control"] == "private, no-store"
                assert (
                    response.headers["X-Robots-Tag"] == "noindex, nofollow, noarchive"
                )

                # DRAFT page: the active-preview candidate policy is
                # preserved for the captured workspace in review.
                draft_response = await client.post(
                    "/internal/render/v1/review",
                    headers={"X-SLAIF-Human-Session": review_token},
                    json=_review_http_body(snapshot_id, "/draft/"),
                )
                assert draft_response.status_code == 200, draft_response.text
                draft_body = draft_response.json()
                assert draft_body["page"]["title"] == "Draft page"
                map_node = next(
                    node
                    for node in _walk_nodes(draft_body["composition"]["nodes"])
                    if node["component_type"] == "MapBlock"
                )
                assert map_node["id"] == str(draft_map_id)
                assert float(map_node["props"]["bbox"]["west"]) == float(
                    Decimal(exact_fraction)
                )

                # The frozen read is immutable input: enqueue the
                # discard, run the real discard worker to its terminal
                # state, and the same review read returns the same
                # bytes.
        discard_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_human_agent_workspace_discard($1,$2,$3)",
            workspace_id,
            site_id,
            seeded["delegator_id"],
        )
        assert len(discard_rows) == 1
        discard_job_id = UUID(str(discard_rows[0]["job_id"]))
        discard_pool = await _worker_pool(database)
        try:
            discard_claimed = await _worker_call(
                database,
                "SELECT * FROM control.slaif_review_job_claim($1, $2)",
                "review-endpoint-worker-discard",
                ["DISCARD"],
            )
            assert len(discard_claimed) == 1
            assert str(discard_claimed[0]["id"]) == str(discard_job_id)
            discard_result = await run_discard_job(
                discard_pool, _worker_settings(database), dict(discard_claimed[0])
            )
            assert discard_result.status == "SUCCEEDED", discard_result.error
        finally:
            await discard_pool.close()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            discarded = await owner.fetchrow(
                "SELECT status, discarded_at FROM control.workspace WHERE id = $1",
                workspace_id,
            )
            discard_job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                discard_job_id,
            )
            pending_operations = await get_session_operations(
                _ConnExecutor(owner), workspace_id, schema="content"
            )
        assert str(discarded["status"]) == "DISCARDED"
        assert discarded["discarded_at"] is not None
        assert discard_job_row["status"] == "SUCCEEDED"
        assert discard_job_row["error"] is None
        assert pending_operations == []
        async with render_app.router.lifespan_context(render_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=render_app),
                base_url="http://render.test",
            ) as client:
                after = await client.post(
                    "/internal/render/v1/review",
                    headers={"X-SLAIF-Human-Session": review_token},
                    json=_review_http_body(snapshot_id, "/"),
                )
                assert after.status_code == 200, after.text
                assert after.json() == body
    finally:
        await render_adapter.stop()

    # Role boundary: only the preview reader may execute the 076 read
    # surface; the public reader cannot, directly or effectively.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        for function in (
            "control.slaif_review_projection_authorize(text,bytea,uuid)",
            "control.slaif_review_snapshot_frozen_state(uuid)",
        ):
            preview_ok = await owner.fetchval(
                "SELECT has_function_privilege('slaif_preview_reader', $1, 'EXECUTE')",
                function,
            )
            public_ok = await owner.fetchval(
                "SELECT has_function_privilege('slaif_public_reader', $1, 'EXECUTE')",
                function,
            )
            assert preview_ok is True
            assert public_ok is False
        direct_call_error = None
        async with (
            await database.role_pool("slaif_public_reader")
        ).acquire() as public_connection:
            try:
                await public_connection.fetchval(
                    "SELECT * FROM control.slaif_review_projection_authorize($1,$2,$3)",
                    review_public_id,
                    hashlib.sha256(review_secret).digest(),
                    snapshot_id,
                )
            except asyncpg.InsufficientPrivilegeError as error:
                direct_call_error = error
            assert direct_call_error is not None

    # Stable refusals: every invalid input is one uniform 404.
    async with render_app.router.lifespan_context(render_app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=render_app),
            base_url="http://render.test",
        ) as client:
            negative_cases = [
                # no session header at all
                ({}, _review_http_body(snapshot_id, "/")),
                # body-supplied session token
                (
                    {"X-SLAIF-Human-Session": review_token},
                    {
                        **_review_http_body(snapshot_id, "/"),
                        "session_token": review_token,
                    },
                ),
                # browser run token header on the human route
                (
                    {
                        "X-SLAIF-Human-Session": review_token,
                        "X-SLAIF-Browser-Run-Token": "tok",
                    },
                    _review_http_body(snapshot_id, "/"),
                ),
            ]
            for headers, payload in negative_cases:
                refused = await client.post(
                    "/internal/render/v1/review", headers=headers, json=payload
                )
                assert refused.status_code == 404, refused.text
            # unknown snapshot id
            refused = await client.post(
                "/internal/render/v1/review",
                headers={"X-SLAIF-Human-Session": review_token},
                json=_review_http_body(uuid4(), "/"),
            )
            assert refused.status_code == 404, refused.text
    # Revoked and expired sessions refuse with the same uniform 404,
    # and the read touched nothing (no session touch, no audit row).
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        session_row = await owner.fetchrow(
            "SELECT last_seen_at, revoked_at FROM control.user_session WHERE id = $1",
            session_id,
        )
        assert session_row["revoked_at"] is None
        assert session_row["last_seen_at"] == before_last_seen
        audit_rows = await owner.fetchval(
            "SELECT count(*) FROM audit.human_editor_mutation"
        )
        assert audit_rows == 0
        # Coherent legacy sessions: every 010 timestamp no later than
        # expiry, and unique secret/CSRF digests (both columns UNIQUE).
        expired_raw_secret = b"e" * 32
        revoked_raw_secret = b"v" * 32
        expired_session_id = uuid4()
        expired_public_id = f"sas2_{expired_session_id.hex}"
        revoked_session_id = uuid4()
        revoked_public_id = f"sas2_{revoked_session_id.hex}"
        # Isolate the named guards: the expired row is NOT idle
        # (last_seen inside the trusted 1800s window) so only the
        # expiry disjunct fires; the revoked row is fresh and
        # unexpired so only the revocation disjunct fires.
        await owner.execute(
            "INSERT INTO control.user_session (id, public_id, secret_digest,"
            " csrf_secret_digest, user_account_id, created_at, last_seen_at,"
            " recent_auth_at, absolute_expires_at, revoked_at) VALUES"
            " ($1,$2,$3,$4,$5, now() - interval '20 minutes',"
            "  now() - interval '20 minutes', now() - interval '20 minutes',"
            "  now() - interval '5 minutes', NULL),"
            " ($6,$7,$8,$9,$10, now() - interval '5 minutes',"
            "  now() - interval '5 minutes', now() - interval '5 minutes',"
            "  now() + interval '1 hour', now() - interval '1 minute')",
            expired_session_id,
            expired_public_id,
            hashlib.sha256(expired_raw_secret).digest(),
            hashlib.sha256(b"review-endpoint-expired-csrf").digest(),
            seeded["delegator_id"],
            revoked_session_id,
            revoked_public_id,
            hashlib.sha256(revoked_raw_secret).digest(),
            hashlib.sha256(b"review-endpoint-revoked-csrf").digest(),
            seeded["delegator_id"],
        )
    for expired_token in (
        format_session_token(expired_public_id, expired_raw_secret).get_secret_value(),
        format_session_token(revoked_public_id, revoked_raw_secret).get_secret_value(),
    ):
        async with render_app.router.lifespan_context(render_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=render_app),
                base_url="http://render.test",
            ) as client:
                refused = await client.post(
                    "/internal/render/v1/review",
                    headers={"X-SLAIF-Human-Session": expired_token},
                    json=_review_http_body(snapshot_id, "/"),
                )
                assert refused.status_code == 404, refused.text
