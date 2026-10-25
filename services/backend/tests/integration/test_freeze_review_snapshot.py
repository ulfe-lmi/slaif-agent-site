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
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_api.config import (
    AgentDatabaseMode,
    AgentDatabaseSettings,
)
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.foundation import (
    FOUNDATION_DISTRIBUTION,
    FOUNDATION_VERSION,
    asyncpg_cow_reviewer,
    asyncpg_cow_session,
    deploy_cow_functions,
    enable_cow_schema,
    get_cow_status,
    get_session_operations,
    harden_cow_schema,
    validate_cow_schema_privileges,
)
from slaif_agent_site.agent_state.workspace_models import DelegationPreset
from slaif_agent_site.bootstrap.service import (
    BootstrapStateError,
    downgrade,
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
from slaif_agent_site.db.executor import AsyncpgExecutor
from slaif_agent_site.db.migrations import run_migration
from slaif_agent_site.db.privileges import (
    apply_product_privileges,
    content_inventory_fingerprint,
    content_object_inventory,
    foundation_object_inventory,
    revoke_public_foundation_access,
    verify_database_privileges,
)
from slaif_agent_site.db.readiness import ReadinessState
from slaif_agent_site.db.roles import (
    REVIEWER_ROLES,
    ROLE_NAMES,
    RUNTIME_ROLES,
)
from slaif_agent_site.editor_api.app import create_app as create_editor_app
from slaif_agent_site.editor_api.config import (
    EditorDatabaseMode,
    EditorDatabaseSettings,
)
from slaif_agent_site.editor_api.database import EditorDatabase
from slaif_agent_site.human_authorization.catalog import (
    L1_SCOPES,
    L2_SCOPES,
    L3_SCOPES,
    L4_SCOPES,
    READ_SCOPES,
)
from slaif_agent_site.identity.sessions import format_session_token
from slaif_agent_site.media_service.finalize import FinalizationManifest
from slaif_agent_site.render_api.app import create_app as create_render_app
from slaif_agent_site.render_api.frozen_source import DatabaseRenderSurface
from slaif_agent_site.render_api.projection import (
    ProjectionError,
    RenderPageRequest,
    RenderProjectionService,
    _node_tree,
)
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
        "image_id": image_id,
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
        # 083-5-b hostile-lane extension (shared, counted once): the full
        # no-effect dimensions the G9/G12/E-D3 refusal tests compare
        # around a refused run.  The original five dimensions above are
        # preserved verbatim; these are additive only.
        "snap_bytes": sorted(
            row[0]
            for row in await conn.fetch(
                "SELECT row_to_json(r)::text FROM control.review_snapshot r"
                " WHERE r.workspace_id = $1 ORDER BY r.id::text",
                workspace_id,
            )
        ),
        "ws_accepted": await conn.fetchval(
            "SELECT coalesce(accepted_at::text, 'null')"
            " FROM control.workspace WHERE id = $1",
            workspace_id,
        ),
        "site_revision": await conn.fetchval(
            "SELECT canonical_revision || ':' || content_model_revision"
            " FROM control.site WHERE id = $1",
            site_id,
        ),
        "page_bytes": sorted(
            row[0]
            for row in await conn.fetch(
                "SELECT row_to_json(p)::text FROM content.page p"
                " WHERE p.site_id = $1 ORDER BY p.id::text",
                site_id,
            )
        ),
        "composition_site_rows": await conn.fetchval(
            "SELECT count(*) FROM content.page_composition_base WHERE site_id = $1",
            site_id,
        ),
        "promo_site_rows": await conn.fetchval(
            "SELECT count(*) FROM audit.promotion WHERE site_id = $1",
            site_id,
        ),
        "outbox_rows": await conn.fetchval("SELECT count(*) FROM control.cache_outbox"),
        "outbox_site_rows": await conn.fetchval(
            "SELECT count(*) FROM control.cache_outbox WHERE site_id = $1",
            site_id,
        ),
        "media_bytes": sorted(
            row[0]
            for row in await conn.fetch(
                "SELECT row_to_json(m)::text FROM content.media_asset m"
                " WHERE m.site_id = $1 ORDER BY m.id::text",
                site_id,
            )
        ),
        # Exact canonical row bytes for the dimensions the hostile
        # vectors tamper: composition, content model (type + field
        # definition), items, translations, and the component catalog.
        "composition_site_bytes": sorted(
            row[0]
            for row in await conn.fetch(
                "SELECT row_to_json(r)::text"
                " FROM content.page_composition_base r"
                " WHERE r.site_id = $1 ORDER BY r.id::text",
                site_id,
            )
        ),
        "type_site_bytes": sorted(
            row[0]
            for row in await conn.fetch(
                "SELECT row_to_json(r)::text"
                " FROM content.content_type_base r"
                " WHERE r.site_id = $1 ORDER BY r.id::text",
                site_id,
            )
        ),
        "field_site_bytes": sorted(
            row[0]
            for row in await conn.fetch(
                "SELECT row_to_json(r)::text"
                " FROM content.field_definition_base r"
                " WHERE r.site_id = $1 ORDER BY r.id::text",
                site_id,
            )
        ),
        "item_site_bytes": sorted(
            row[0]
            for row in await conn.fetch(
                "SELECT row_to_json(r)::text"
                " FROM content.content_item_base r"
                " WHERE r.site_id = $1 ORDER BY r.id::text",
                site_id,
            )
        ),
        "translation_site_bytes": sorted(
            row[0]
            for row in await conn.fetch(
                "SELECT row_to_json(r)::text"
                " FROM content.content_item_translation_base r"
                " WHERE r.site_id = $1 ORDER BY r.id::text",
                site_id,
            )
        ),
        "catalog_bytes": await conn.fetchval(
            "SELECT row_to_json(r)::text FROM control.component_catalog r"
        ),
        "locale_site_bytes": sorted(
            row[0]
            for row in await conn.fetch(
                "SELECT row_to_json(r)::text FROM content.site_locale_base r"
                " WHERE r.site_id = $1 ORDER BY r.id::text",
                site_id,
            )
        ),
    }


_RT_SNAPSHOT_ROW_BYTES = (
    "SELECT row_to_json(r)::text FROM control.review_snapshot r WHERE r.workspace_id=$1"
)


async def _rt_refusal_state(conn: Any, seed: dict[str, Any]) -> dict[str, Any]:
    """Exact no-effects capture at a refusal boundary (083/5 RC7).

    Raw row bytes and un-normalized privilege state: any unintended
    write by a refused operation must surface as a before/after
    difference.  Covers the complete readiness row, COW state, the
    site canonical/content-model revisions, every relevant workspace
    row, every retained snapshot row, and the effective EXECUTE
    matrix across all product roles.
    """

    role_rows = ", ".join(f"(${i})" for i in range(1, len(_RT_EFFECTIVE_ROLES) + 1))
    eff_rows = await conn.fetch(
        "SELECT r.rolname AS role, f.oid AS oid, "
        "has_function_privilege(r.rolname, f.oid, 'EXECUTE') AS has "
        "FROM pg_proc f "
        "JOIN pg_namespace n ON n.oid = f.pronamespace "
        f"CROSS JOIN (VALUES {role_rows}) AS r(rolname) "
        "WHERE n.nspname = 'control' ORDER BY r.rolname, f.oid",
        *_RT_EFFECTIVE_ROLES,
    )
    return {
        "readiness": await conn.fetchval(
            "SELECT row_to_json(r)::text "
            "FROM control.bootstrap_readiness r WHERE r.singleton"
        ),
        "cow": dict(await get_cow_status(AsyncpgExecutor(conn), schema="content")),
        "site": await conn.fetchval(
            "SELECT row_to_json(s)::text FROM control.site s WHERE s.id = $1",
            seed["site_id"],
        ),
        "workspaces": sorted(
            row[0]
            for row in await conn.fetch(
                "SELECT row_to_json(w)::text FROM control.workspace w "
                "WHERE w.site_id = $1::uuid ORDER BY w.id::text",
                seed["site_id"],
            )
        ),
        "snapshots": sorted(
            row[0]
            for row in await conn.fetch(
                "SELECT row_to_json(r)::text FROM control.review_snapshot r "
                "WHERE r.site_id = $1::uuid "
                "ORDER BY r.workspace_id::text, r.id::text",
                seed["site_id"],
            )
        ),
        "effective_execute": [
            (row["role"], int(row["oid"]), bool(row["has"])) for row in eff_rows
        ],
    }


def _rt_expected_bodies() -> dict[str, str]:
    """Exact body digests of every 075/076 replacement candidate."""

    return {
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
    effects; the real bootstrap operator path (bootstrap downgrade) is
    refused FIRST as well, before its readiness-PENDING/COW-disable
    operator-path effects, leaving readiness, COW, revision, catalog,
    owner, search_path, direct/effective ACLs and both retained rows
    unchanged.  The retained-v2 fixture is kept INTACT: no retained v2
    history is deleted to let a downgrade pass.  The supported 075
    restore + 076 re-upgrade (byte-identical v1 row, working 075
    constructors, exact reconciled head) is proven in the separate
    genuine v1-only disposable database roundtrip test.
    """

    database = agent_site_database
    dsn = database.settings.resolved_owner_dsn()
    db_name = database.name
    expected = _rt_expected_bodies()
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
    eff_role_rows = ", ".join(f"(${i})" for i in range(1, len(_RT_EFFECTIVE_ROLES) + 1))
    async with owner_connection(dsn, expected_database=db_name) as eff:
        eff_rows = await eff.fetch(
            "SELECT r.rolname AS role, f.oid AS oid, "
            "has_function_privilege(r.rolname, f.oid, 'EXECUTE') AS has "
            "FROM pg_proc f "
            "JOIN pg_namespace n ON n.oid = f.pronamespace "
            f"CROSS JOIN (VALUES {eff_role_rows}) AS r(rolname) "
            "WHERE n.nspname = 'control' ORDER BY r.rolname, f.oid",
            *_RT_EFFECTIVE_ROLES,
        )
    oid_to_key = {v["oid"]: k for k, v in s2f.items()}
    observed_roles: set[str] = set()
    observed_oids: set[int] = set()
    for row in eff_rows:
        name_sig = oid_to_key.get(row["oid"])
        assert name_sig is not None, f"unknown oid {row['oid']}"
        name, sig = _rt_split_key(name_sig)
        roles = _RT_POLICY_ROLES.get((name, _rt_norm_sig(sig)), set())
        expect = row["role"] in roles or row["role"] == "slaif_owner"
        assert bool(row["has"]) == expect, (name_sig, row["role"], row["has"])
        observed_roles.add(row["role"])
        observed_oids.add(int(row["oid"]))
    # Full intended matrix coverage: every product role (including public)
    # and every control function must appear; a silent VALUES collapse to
    # the first role only would fail these checks.
    assert observed_roles == set(_RT_EFFECTIVE_ROLES), (
        sorted(observed_roles),
        sorted(_RT_EFFECTIVE_ROLES),
    )
    assert observed_oids == {v["oid"] for v in s2f.values()}
    assert len(eff_rows) == len(_RT_EFFECTIVE_ROLES) * len(s2f)
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
    pre_mig: dict[str, Any] = {}
    async with owner_connection(dsn, expected_database=db_name) as owner:
        pre_mig = await _rt_refusal_state(owner, seed)
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
        assert await _rt_refusal_state(owner, seed) == pre_mig

    # --- P3a2: the real bootstrap operator path refuses FIRST ----------
    # The operator downgrade would commit readiness PENDING and disable
    # content COW before running the migration; the retained-v2
    # preflight checks the same product control snapshot fact before
    # any of those operator-path effects, so the refusal must leave
    # readiness, COW, revision, catalog, ACLs and both retained rows
    # unchanged.
    pre_op: dict[str, Any] = {}
    async with owner_connection(dsn, expected_database=db_name) as owner:
        pre_op = await _rt_refusal_state(owner, seed)
    with pytest.raises(BootstrapStateError, match="retained review-snapshot/v2"):
        await downgrade(database.settings)
    s_oprefused: dict[str, Any] = {}
    async with owner_connection(dsn, expected_database=db_name) as owner:
        s_oprefused = await _rt_capture_state(owner, seed)
    assert s_oprefused["alembic_version"] == "076_001"
    assert s_oprefused["control_functions"] == s2f
    assert s_oprefused["marker"] is not None
    assert s_oprefused["marker"]["readiness_state"] == "HARDENED"
    async with owner_connection(dsn, expected_database=db_name) as owner:
        assert (await get_cow_status(AsyncpgExecutor(owner), schema="content"))[
            "enabled"
        ] is True
        assert await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_s) == v2_row_bytes
        assert await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_legacy) == v1_row_bytes
        assert await _rt_refusal_state(owner, seed) == pre_op

    # --- P3z: the retained-v2 fixture is kept INTACT --------------------
    # RC7: retained v2 history is never deleted to let a downgrade pass;
    # the supported 075 restore + 076 re-upgrade roundtrip runs in a
    # separate genuine v1-only disposable database.  This fixture ends
    # with BOTH genuine retained rows at the reconciled 076 head.
    async with owner_connection(dsn, expected_database=db_name) as owner:
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM control.review_snapshot "
                "WHERE payload->>'state_version' = 'review-snapshot/v2'"
            )
            == 1
        )
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM control.review_snapshot "
                "WHERE payload->>'state_version' = 'review-snapshot/v1'"
            )
            == 1
        )
        assert (
            await owner.fetchval(
                "SELECT status || '/' || coalesce(review_snapshot_id::text,'null') "
                "FROM control.workspace WHERE id=$1",
                ws_s,
            )
            == f"REVIEW/{snap_s}"
        )


@pytest.mark.asyncio
async def test_075_001_v1_only_downgrade_roundtrip_disposable(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """083/5 RC7: the supported 075 restore + 076 re-upgrade in a
    SEPARATE genuine v1-only disposable database.

    This database never materializes a review-snapshot/v2 row: the one
    retained snapshot is a genuine legacy v1 payload completed under
    the real 075 contract, so the 076 retained-v2 downgrade guard is
    inactive BY CONSTRUCTION (there is no v2 history to delete).  The
    upgrade carries the exact v2 bodies while the retained v1 row stays
    byte-identical; the downgrade restores the exact 075 catalog
    (identity incl. OID), the reconciled grant policy, the
    byte-identical v1 row and working 075 constructors; the re-upgrade
    reproduces the reconciled head exactly.
    """

    database = agent_site_database
    dsn = database.settings.resolved_owner_dsn()
    db_name = database.name
    expected = _rt_expected_bodies()

    # --- S0: the true 075 pre-upgrade baseline (no snapshot rows at all)
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

    # --- S0b: the genuine legacy v1 snapshot - the ONLY retained row ----
    async with owner_connection(dsn, expected_database=db_name) as owner:
        ws_v1 = await _rt_create_probe_workspace(
            owner, seed["site_id"], seed["user_id"], "V1-Only Retained"
        )
        await _rt_set_freezing(owner, ws_v1)
        v1_payload = await _rt_materialize_payload(owner, ws_v1)
        assert v1_payload.get("state_version") == "review-snapshot/v1"
        v1_digest = await _rt_canonical_digest(owner, v1_payload)
        v1_snap_id = await owner.fetchval(
            "SELECT control.slaif_review_snapshot_complete($1::uuid,$2::jsonb)",
            ws_v1,
            _rt_complete_row(ws_v1, v1_payload, digest=v1_digest),
        )
        assert v1_snap_id is not None
        v1_row_bytes = await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_v1)
        assert (
            await owner.fetchval(
                "SELECT status || '/' || coalesce(review_snapshot_id::text,'null') "
                "FROM control.workspace WHERE id=$1",
                ws_v1,
            )
            == f"REVIEW/{v1_snap_id}"
        )
        row_v1_check = await owner.fetchrow(
            "SELECT payload = $2::jsonb AND digest = $3 "
            "FROM control.review_snapshot WHERE workspace_id=$1",
            ws_v1,
            json.dumps(v1_payload),
            v1_digest,
        )
        assert row_v1_check[0] is True
        assert await owner.fetchval("SELECT count(*) FROM control.review_snapshot") == 1
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM control.review_snapshot "
                "WHERE payload->>'state_version' = 'review-snapshot/v2'"
            )
            == 0
        )

    # --- S1: upgrade to head with the v1 row retained -------------------
    await run_migration(
        dsn, expected_database=db_name, operation="upgrade", revision="head"
    )
    s1: dict[str, Any] = {}
    async with owner_connection(dsn, expected_database=db_name) as owner:
        s1 = await _rt_capture_state(owner, seed)
        assert await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_v1) == v1_row_bytes
        assert (
            await owner.fetchval(
                "SELECT version_facts::text FROM control.workspace WHERE id=$1",
                ws_v1,
            )
            == "{}"
        )
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
    for k in base:
        if k in replaced_v2_bodies:
            continue
        for f in (*_RT_IDENTITY_FIELDS, "oid", "grants"):
            assert base[k][f] == head[k][f], (k, f, base[k][f], head[k][f])
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

    # --- S2: reconcile = normal bootstrap hardening ----------------------
    await reconcile(database.settings)
    s2: dict[str, Any] = {}
    async with owner_connection(dsn, expected_database=db_name) as owner:
        s2 = await _rt_capture_state(owner, seed)
        assert await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_v1) == v1_row_bytes
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
    assert s2["marker"] is not None and s2["marker"]["readiness_state"] == "HARDENED"

    # --- P3: downgrade with ONLY the genuine v1 row retained ------------
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
        assert await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_v1) == v1_row_bytes
        inv65 = await _rt_invoke_constructors(
            owner, seed["site_id"], seed["user_id"], check_version_facts=False
        )
    assert inv65["ws_create"] is not None
    assert inv65["editor_resolve_insert_path"] is not None
    assert inv65["agent_ws_create"] is not None

    # --- P4: upgrade back to head + reconcile ----------------------------
    await run_migration(
        dsn, expected_database=db_name, operation="upgrade", revision="head"
    )
    await reconcile(database.settings)
    s4: dict[str, Any] = {}
    async with owner_connection(dsn, expected_database=db_name) as owner:
        s4 = await _rt_capture_state(owner, seed)
        assert await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_v1) == v1_row_bytes
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


# The 18 named logical reads of the live surface (RenderReadSurface).
# Sealing them reversibly makes every process-local live content and
# media-descriptor retrieval unavailable for the duration of one test.
_RETRIEVAL_SEAL_NAMES: tuple[str, ...] = (
    "fetch_locales",
    "fetch_enabled_locale_tags",
    "fetch_pages",
    "fetch_redirects",
    "fetch_navigation_definitions",
    "fetch_navigation_items",
    "fetch_theme",
    "fetch_page_style",
    "fetch_catalog_version",
    "fetch_regions",
    "fetch_composition",
    "resolve_media",
    "fetch_collection_view",
    "fetch_content_type",
    "fetch_field_definitions",
    "count_content_items",
    "fetch_content_items",
    "fetch_content_item_translations",
)


def _seal_live_retrieval(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reversibly refuse every live surface read (exact per-test restore)."""

    for name in _RETRIEVAL_SEAL_NAMES:
        original = getattr(DatabaseRenderSurface, name, None)
        assert callable(original), name

        async def _refused(*args: Any, _name: str = name, **kwargs: Any) -> Any:
            raise RuntimeError(f"LIVE_RETRIEVAL_SEALED:{_name}")

        monkeypatch.setattr(DatabaseRenderSurface, name, _refused)


@pytest.mark.asyncio
async def test_frozen_drift_invariance_offline_live_and_discard_repeat(
    agent_site_database: AgentSiteDatabase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """083/5 RC3: drift, offline live retrieval, terminal discard.

    W1 carries one real pending COW operation at freeze time.  An
    unrelated authorized publication from W2 (real freeze + human
    accept) advances the canonical revision: the stored payload bytes
    and digest stay exact, and only the separately named drift
    metadata of the review read model moves.  With ALL 18 live
    surface reads sealed (reversible process-local instrumentation,
    exact per-test restore), the frozen internal ASGI projection
    output stays byte-identical, proving the frozen read performs no
    live content or media-descriptor retrieval.  Finally W1 is
    discarded to its real terminal worker state with pending cleanup,
    and the same frozen read repeats unchanged.

    Scope: this case proves the internal review read (projection
    JSON), offline live retrieval, drift invariance and terminal
    discard for the seeded static home page.  It is NOT the actual
    browser/React rendered output and does not close the dynamic
    route/query/domain frozen invariance or the rendered-output half
    of RC3; those remain with the public six-target parity workflow
    (tests/e2e/frozen-review-parity.spec.ts) in its existing named
    path.
    """
    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    site_id = ids["site_id"]
    delegator_id = ids["delegator_id"]
    workspace_id = ids["workspace_id"]
    dsn = database.settings.resolved_owner_dsn()

    # W1's real pending COW operation (drained into the snapshot at
    # freeze; retained pending until the terminal discard below).
    await _cow_create(
        database,
        workspace_id=workspace_id,
        capability_id=ids["capability_id"],
        site_id=site_id,
        page_id=ids["page_id"],
        parent_id=ids["section_id"],
        text="083/5 RC3 W1 marker",
    )

    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    render_adapter = _RestartableRenderAdapter(database)
    await render_adapter.start()
    render_app = create_render_app(
        settings=ServiceSettings.for_test(),
        database=render_adapter,
    )
    try:
        result, _job = await _freeze_claim_run(
            database,
            workspace_id=workspace_id,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-5-rc3-f1",
        )
        assert result.status == "SUCCEEDED", result.error
        snapshot = await _snapshot_row(database, workspace_id)
        assert snapshot is not None and snapshot["status"] == "COMPLETE"
        snap_id: UUID = snapshot["id"]
        async with owner_connection(dsn, expected_database=database.name) as owner:
            payload_before = await owner.fetchval(
                "SELECT payload::text FROM control.review_snapshot WHERE id = $1",
                snap_id,
            )
            digest_before = await owner.fetchval(
                "SELECT digest FROM control.review_snapshot WHERE id = $1",
                snap_id,
            )

        # Current human review session for the seeded SITE_OWNER.
        session_id = uuid4()
        review_secret = b"r" * 32
        review_public_id = f"sas2_{session_id.hex}"
        async with owner_connection(dsn, expected_database=database.name) as owner:
            await owner.execute(
                "INSERT INTO control.user_session (id, public_id,"
                " secret_digest, csrf_secret_digest, user_account_id,"
                " absolute_expires_at) VALUES ($1,$2,$3,$4,$5,"
                " now() + interval '1 hour')",
                session_id,
                review_public_id,
                hashlib.sha256(review_secret).digest(),
                b"c" * 32,
                delegator_id,
            )
        review_token = format_session_token(
            review_public_id, review_secret
        ).get_secret_value()

        async def review_body(path: str) -> dict[str, Any]:
            async with render_app.router.lifespan_context(render_app):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=render_app),
                    base_url="http://render.test",
                ) as client:
                    response = await client.post(
                        "/internal/render/v1/review",
                        headers={"X-SLAIF-Human-Session": review_token},
                        json=_review_http_body(snap_id, path),
                    )
                    assert response.status_code == 200, response.text
                    body: dict[str, Any] = response.json()
                    return body

        async def read_model_drift() -> dict[str, Any]:
            rows = await _control_call(
                database,
                "SELECT * FROM control.slaif_review_read_model($1,$2,$3)",
                workspace_id,
                site_id,
                delegator_id,
            )
            document: dict[str, Any] = json.loads(rows[0][0])
            drift: dict[str, Any] = document["drift"]
            return drift

        body_before = await review_body("/")
        # Independent baseline oracles: the equality proofs below are
        # only meaningful because the baseline itself is verified
        # (W1 marker, seeded content, exact frozen media map).
        before_nodes = _walk_nodes(body_before["composition"]["nodes"])
        before_headings = [
            str(n["props"]["text"])
            for n in before_nodes
            if n.get("component_type") == "Heading"
        ]
        assert "083/5 RC3 W1 marker" in before_headings
        assert "Accept" in before_headings
        assert body_before["page"]["title"] == "Home"
        media_nodes = [n for n in before_nodes if n.get("media") is not None]
        assert len(media_nodes) == 1
        assert media_nodes[0]["component_type"] == "Image"
        assert media_nodes[0]["props"]["mediaId"] == str(ids["media_id"])
        assert media_nodes[0]["media"]["url"] == (
            f"/media/v1/review/{snap_id}/assets/{ids['media_id']}/content"
        )
        assert media_nodes[0]["media"]["mime_type"] == "image/png"
        drift_before = await read_model_drift()
        assert drift_before["equal"] is True
        assert int(drift_before["current_site_revision"]) == 0

        # Seal every live surface read; the probe proves the seal is
        # live (a real live-path fetch would hit it), not vacuous.
        _seal_live_retrieval(monkeypatch)
        probe = DatabaseRenderSurface(connection=None)
        with pytest.raises(RuntimeError, match="LIVE_RETRIEVAL_SEALED"):
            await probe.fetch_pages(site_id=site_id)

        # Offline live retrieval: the frozen projection is identical.
        body_offline = await review_body("/")
        assert body_offline == body_before

        # W2: an unrelated authorized publication to C (the qualified
        # composition publication path: real freeze + human accept).
        async with owner_connection(dsn, expected_database=database.name) as owner:
            ws2, cap2 = await _create_workspace(
                owner, site_id, delegator_id, "083/5 RC3 W2"
            )
        await _cow_create(
            database,
            workspace_id=ws2,
            capability_id=cap2,
            site_id=site_id,
            page_id=ids["page_id"],
            parent_id=ids["section_id"],
            text="083/5 RC3 W2 marker",
        )
        result2, _job2 = await _freeze_claim_run(
            database,
            workspace_id=ws2,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-5-rc3-f2",
        )
        assert result2.status == "SUCCEEDED", result2.error
        result2a, _job2a = await _accept_claim_run(
            database,
            workspace_id=ws2,
            delegator_id=delegator_id,
            pool=pool,
            claimant="083-5-rc3-a2",
            boundary=boundary,
        )
        assert result2a.status == "SUCCEEDED", result2a.error

        async with owner_connection(dsn, expected_database=database.name) as owner:
            revision_c = int(
                await owner.fetchval(
                    "SELECT canonical_revision FROM control.site WHERE id=$1",
                    site_id,
                )
            )
            payload_after = await owner.fetchval(
                "SELECT payload::text FROM control.review_snapshot WHERE id = $1",
                snap_id,
            )
            digest_after = await owner.fetchval(
                "SELECT digest FROM control.review_snapshot WHERE id = $1",
                snap_id,
            )
        assert revision_c == 1

        # Exact stored invariance: payload bytes and digest untouched.
        assert payload_after == payload_before
        assert digest_after == digest_before
        assert await _digest_is_valid(database, snap_id)
        # Only the separately named current-revision/drift metadata
        # moved (the review read model), never the stored state.
        drift_after = await read_model_drift()
        assert drift_after["equal"] is False
        assert int(drift_after["current_site_revision"]) == revision_c
        # Frozen projection output: still byte-identical, still with
        # every live read sealed.
        body_drift = await review_body("/")
        assert body_drift == body_before

        # Real terminal discard + pending cleanup.
        discard_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_human_agent_workspace_discard($1,$2,$3)",
            workspace_id,
            site_id,
            delegator_id,
        )
        assert len(discard_rows) == 1
        discard_job_id = UUID(str(discard_rows[0]["job_id"]))
        discard_claimed = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "083-5-rc3-d1",
            ["DISCARD"],
        )
        assert len(discard_claimed) == 1 and str(discard_claimed[0]["id"]) == str(
            discard_job_id
        )
        discard_result = await run_discard_job(
            pool, _worker_settings(database), dict(discard_claimed[0])
        )
        assert discard_result.status == "SUCCEEDED", discard_result.error
        async with owner_connection(dsn, expected_database=database.name) as owner:
            discarded = await owner.fetchrow(
                "SELECT status, discarded_at FROM control.workspace WHERE id = $1",
                workspace_id,
            )
            pending_operations = await get_session_operations(
                _ConnExecutor(owner), workspace_id, schema="content"
            )
        assert str(discarded["status"]) == "DISCARDED"
        assert discarded["discarded_at"] is not None
        assert pending_operations == []

        # Repeated frozen read after terminal discard/cleanup: the
        # same exact bytes, live retrieval still sealed.
        body_final = await review_body("/")
        assert body_final == body_before
    finally:
        await boundary.stop()
        await pool.close()
        await render_adapter.stop()


# ---------------------------------------------------------------------------
# 083/5 RC6: TEST-OWNED isolated copy of the base-4bf74fdc review worker
# 075 snapshot builder (genuine legacy production semantics).
#
# Source of record (byte-copied, no runtime git dependency):
#   git show 4bf74fdc:services/backend/src/slaif_agent_site/review_worker/snapshot.py
# artifact: /tmp/oap-083-5-b/base075-snapshot.py
#
# Only module-private names are renamed (``_rc6_`` prefix); the base-era
# STATE_VERSION constant ("review-snapshot/v1") is inlined because the
# current config constant is its v2 successor.  The six trusted pins
# (catalog/design_system/composition_schema/renderer/puck/content_model)
# are byte-identical between 4bf74fdc and the current tree (verified), so
# the current constants ARE the base-era values.  ``_node_tree``/
# ``ProjectionError`` come from the current shared projection module --
# the same import the base module used (signature-verified identical,
# see /tmp/oap-083-5-b/075-normalizer-block-source-comparison.json).
# The base module's local canonical serializer/digest were plain
# ``json.dumps`` (sorted, compact, ensure_ascii) + SHA-256; the current
# ``content_model.canonical`` serializers are NOT byte-identical to them
# (float/-0.0 rendering differs; see
# /tmp/oap-083-5-b/075-current-canonicalization-independent-comparison.json),
# so the test-owned ``_rc6_canonical_json``/``_rc6_canonical_digest``
# below ARE the actual 075-local definitions, and the legacy build never
# claims the current v2 canonicalization semantics.
# ---------------------------------------------------------------------------


class _Rc6SnapshotBuildError(ValueError):
    """A stable, non-leaking snapshot build failure (base-075 semantics)."""

    def __init__(self, code: str, *, reason: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.reason = reason


_RC6_STATE_VERSION = "review-snapshot/v1"  # base-era REVIEW_WORKER_STATE_VERSION
_RC6_REQUIRED_DOC_KEYS = (
    "state_version",
    "workspace_id",
    "site_id",
    "site",
    "base_site_revision",
    "operation_watermark",
    "locales",
    "theme",
    "regions",
    "navigation",
    "redirects",
    "pages",
    "media",
)
_RC6_REQUIRED_PAGE_KEYS = (
    "id",
    "site_id",
    "slug",
    "title",
    "status",
    "locale",
    "parent_id",
    "route_template",
    "effective_route",
    "row_version",
    "nodes",
)
# Renderer composition SELECT column order (id, site_id, page_id,
# component_type, schema_version, parent_id, slot_key, order_key, props,
# created_at, updated_at).
_RC6_NODE_COLUMNS = 11
# The exact columns the 076 upgrade ADDS to control.browser_run (the only
# browser_run schema delta in 071/076; workspace gains one version_facts
# column); the legacy retention comparison excludes only these.
_RC6_076_BROWSER_RUN_COLUMNS = (
    "preview_credential_digest",
    "preview_credential_nonce_digest",
    "preview_credential_expires_at",
    "preview_credential_attempt",
)


def _rc6_canonical_json(value: Any) -> str:
    """Base-075 canonical JSON (the module-local json.dumps form)."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _rc6_canonical_digest(payload: dict[str, Any]) -> str:
    """Base-075 SHA-256 hex over the module-local canonical text."""

    return hashlib.sha256(_rc6_canonical_json(payload).encode("utf-8")).hexdigest()


def _rc6_node_rows(page_nodes: list[Any]) -> list[tuple[Any, ...]]:
    """Convert materialized ``row_to_json`` node rows to positional rows."""

    rows: list[tuple[Any, ...]] = []
    for node in page_nodes:
        if not isinstance(node, dict):
            raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
        parent = node.get("parent_id")
        rows.append(
            (
                UUID(str(node["id"])),
                UUID(str(node["site_id"])),
                UUID(str(node["page_id"])),
                str(node["component_type"]),
                str(node["schema_version"]),
                UUID(str(parent)) if parent is not None else None,
                str(node["slot_key"]),
                int(node["order_key"]),
                node.get("props"),
                node.get("created_at"),
                node.get("updated_at"),
            )
        )
    return rows


def _rc6_normalized_nodes(page: dict[str, Any], site_id: UUID) -> list[dict[str, Any]]:
    rows = _rc6_node_rows(page["nodes"])
    if len(rows) != len(page["nodes"]) or any(
        len(row) != _RC6_NODE_COLUMNS for row in rows
    ):
        raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    try:
        roots = _node_tree(rows, page_id=UUID(str(page["id"])), site_id=site_id)
    except ProjectionError as error:
        raise _Rc6SnapshotBuildError(
            "SNAPSHOT_VALIDATION_FAILED", reason=error.reason
        ) from None
    except (KeyError, TypeError, ValueError):
        raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED") from None
    return [node.model_dump(mode="json") for node in roots]


def _rc6_media_references(media: Any) -> list[dict[str, Any]]:
    if not isinstance(media, dict):
        raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    references: list[dict[str, Any]] = []
    for key, descriptor in sorted(media.items()):
        if not isinstance(descriptor, dict):
            raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
        reference = {
            "id": str(descriptor.get("id", key)),
            "mime_type": descriptor.get("mime_type"),
            "size_bytes": descriptor.get("size_bytes"),
            "content_hash": descriptor.get("content_hash"),
            "public_status": descriptor.get("public_status"),
        }
        if (
            reference["id"] != key
            or not isinstance(reference["mime_type"], str)
            or not isinstance(reference["size_bytes"], int)
            or not isinstance(reference["content_hash"], str)
            or not isinstance(reference["public_status"], str)
        ):
            raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
        references.append(reference)
    return references


def _rc6_build_snapshot_document(
    doc: Any,
    *,
    created_by: str,
    browser_evidence: list[dict[str, Any]] | None = None,
    cancelled_runs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Base-4bf74fdc builder: validate doc, nest node trees, build row.

    Returns the exact row the base-era worker passed to
    ``control.slaif_review_snapshot_complete``; the canonical ``digest``
    is recomputable from the stored ``payload`` by any party.
    """

    if isinstance(doc, (str, bytes, bytearray)):
        try:
            doc = json.loads(doc)
        except ValueError:
            raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED") from None
    if not isinstance(doc, dict) or any(
        key not in doc for key in _RC6_REQUIRED_DOC_KEYS
    ):
        raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    if doc["state_version"] != _RC6_STATE_VERSION:
        raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    try:
        workspace_id = UUID(str(doc["workspace_id"]))
        site_id = UUID(str(doc["site_id"]))
        base_site_revision = int(doc["base_site_revision"])
        operation_watermark = int(doc["operation_watermark"])
    except (KeyError, TypeError, ValueError):
        raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED") from None
    if base_site_revision < 0 or operation_watermark < 0:
        raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    if not isinstance(doc["pages"], list) or not isinstance(doc["site"], dict):
        raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")

    pages: list[dict[str, Any]] = []
    for page in doc["pages"]:
        if not isinstance(page, dict) or any(
            key not in page for key in _RC6_REQUIRED_PAGE_KEYS
        ):
            raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
        if str(page["site_id"]) != str(site_id) or not isinstance(page["nodes"], list):
            raise _Rc6SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
        normalized = dict(page)
        normalized["nodes"] = _rc6_normalized_nodes(page, site_id)
        pages.append(normalized)

    versions = {
        "catalog": CATALOG_VERSION,
        "design_system": DESIGN_SYSTEM_VERSION,
        "composition_schema": COMPOSITION_SCHEMA_VERSION,
        "renderer": RENDERER_VERSION,
        "puck": PUCK_VERSION_PIN,
        "content_model": REVIEW_WORKER_CONTENT_MODEL_SCHEMA_VERSION,
    }
    validation_report = {
        "state_version": _RC6_STATE_VERSION,
        "pages_validated": len(pages),
        "errors": [],
        "cancelled_by_freeze": [
            {
                "id": str(item["id"]),
                "previous_state": item.get("previous_state"),
            }
            for item in (cancelled_runs or [])
            if isinstance(item, dict) and "id" in item
        ],
    }
    media_references = _rc6_media_references(doc["media"])
    evidence = [
        {"id": str(item["id"])}
        for item in (browser_evidence or [])
        if isinstance(item, dict) and "id" in item
    ]
    payload: dict[str, Any] = {
        "state_version": _RC6_STATE_VERSION,
        "workspace_id": str(workspace_id),
        "site_id": str(site_id),
        "site": doc["site"],
        "base_site_revision": base_site_revision,
        "operation_watermark": operation_watermark,
        "locales": doc["locales"],
        "theme": doc["theme"],
        "regions": doc["regions"],
        "navigation": doc["navigation"],
        "redirects": doc["redirects"],
        "pages": pages,
        "media": doc["media"],
    }
    return {
        "workspace_id": str(workspace_id),
        "site_id": str(site_id),
        "status": "COMPLETE",
        "revision_watermark": base_site_revision + operation_watermark,
        "versions": versions,
        "normalized_state": payload,
        "validation_report": validation_report,
        "media_references": media_references,
        "browser_evidence": evidence,
        "payload": payload,
        "digest": _rc6_canonical_digest(payload),
        "created_by": created_by,
    }


def _rc6_walk_node_texts(pages: list[dict[str, Any]]) -> list[str]:
    """All node props texts in a built (nested) payload page list."""

    texts: list[str] = []

    def walk(nodes: list[Any]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            props = node.get("props")
            if isinstance(props, dict) and props.get("text") is not None:
                texts.append(str(props["text"]))
            children = node.get("children")
            if isinstance(children, list):
                walk(children)

    for page in pages:
        walk(page.get("nodes", []) or [])
    return texts


class _Rc6CountingMediaBoundary(MediaBoundary):
    """Reversible test-local seam around the real MediaBoundary.

    A MediaBoundary subtype that counts every real ``finalize`` call
    (with its site/workspace/media arguments) and delegates unchanged;
    ``stop`` releases the real boundary exactly once.  The wrapper's
    own lazy state is never built (it always delegates), and it owns no
    product state of its own, so restoration is implicit.
    """

    def __init__(self, real: MediaBoundary) -> None:
        super().__init__()
        self._real = real
        self.finalize_calls: list[tuple[str, str, list[str]]] = []

    async def finalize(
        self, site_id: UUID, workspace_id: UUID, media_ids: list[UUID]
    ) -> FinalizationManifest:
        self.finalize_calls.append(
            (str(site_id), str(workspace_id), [str(m) for m in media_ids])
        )
        return await self._real.finalize(site_id, workspace_id, media_ids)

    async def stop(self) -> None:
        await self._real.stop()


_RC6_075_GRANT_FUNCTIONS = (
    "slaif_content_type_create(uuid,text,jsonb,text,jsonb)",
    "slaif_content_type_list(uuid)",
    "slaif_content_type_get(uuid)",
    "slaif_content_type_update(uuid,jsonb,text,jsonb)",
    "slaif_content_type_delete(uuid)",
    "slaif_field_definition_create(uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb)",
    "slaif_field_definition_list(uuid)",
    "slaif_field_definition_get(uuid)",
    "slaif_field_definition_update(uuid,text,boolean,boolean,integer,integer,jsonb,jsonb)",
    "slaif_field_definition_delete(uuid)",
    "slaif_content_item_create(uuid,uuid,text,text,jsonb,integer)",
    "slaif_content_item_list(uuid,uuid)",
    "slaif_content_item_get(uuid)",
    "slaif_content_item_update(uuid,text,text,jsonb,integer,text)",
    "slaif_content_item_delete(uuid,integer)",
    "slaif_collection_view_create(uuid,text,jsonb,jsonb,jsonb,jsonb)",
    "slaif_collection_view_list(uuid)",
    "slaif_collection_view_get(uuid)",
    "slaif_collection_view_update(uuid,jsonb,jsonb,jsonb,jsonb)",
    "slaif_collection_view_delete(uuid)",
    "slaif_navigation_create(uuid,text,text,jsonb)",
    "slaif_navigation_list(uuid)",
    "slaif_navigation_get(uuid)",
    "slaif_navigation_update(uuid,text,jsonb)",
    "slaif_navigation_delete(uuid)",
    "slaif_locale_create(uuid,text,boolean,boolean,integer,jsonb)",
    "slaif_locale_list(uuid)",
    "slaif_locale_get(uuid,uuid)",
    "slaif_locale_update(uuid,uuid,text,boolean,boolean,integer,jsonb,integer)",
    "slaif_locale_delete(uuid,uuid,integer)",
    "slaif_navigation_item_create(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer)",
    "slaif_navigation_item_list(uuid,uuid)",
    "slaif_navigation_item_get(uuid,uuid)",
    "slaif_navigation_item_update(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer,integer)",
    "slaif_navigation_item_delete(uuid,uuid,integer)",
    "slaif_redirect_create(uuid,text,text,integer,text)",
    "slaif_redirect_list(uuid)",
    "slaif_redirect_get(uuid,uuid)",
    "slaif_redirect_update(uuid,uuid,text,text,integer,text,integer)",
    "slaif_redirect_delete(uuid,uuid,integer)",
    "slaif_proposed_side_effect_create(uuid,uuid,text,jsonb)",
    "slaif_proposed_side_effect_list(uuid,uuid)",
    "slaif_theme_get(uuid)",
    "slaif_theme_update(uuid,jsonb,jsonb,jsonb,jsonb)",
    "slaif_theme_validate_groups(jsonb,jsonb,jsonb,jsonb)",
    "slaif_theme_default(uuid)",
    "slaif_theme_project(uuid)",
    "slaif_page_style_get(uuid,uuid)",
    "slaif_page_style_update(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[])",
    "slaif_page_create(uuid,text,text,text,text)",
    "slaif_page_list(uuid)",
    "slaif_page_get(uuid)",
    "slaif_page_update(uuid,text,text,text,integer)",
    "slaif_page_delete(uuid)",
    "slaif_composition_node_add(uuid,uuid,text,uuid,text,integer,jsonb)",
    "slaif_composition_node_update(uuid,jsonb,text,integer)",
    "slaif_composition_node_move(uuid,uuid,text,integer)",
    "slaif_composition_node_delete(uuid)",
    "slaif_composition_list(uuid)",
    "slaif_media_create(uuid,uuid,text,text,bigint,text,text,text,jsonb)",
    "slaif_media_list(uuid)",
    "slaif_media_get(uuid)",
    "slaif_media_update(uuid,text,jsonb)",
    "slaif_media_delete(uuid)",
)


async def _rc6_establish_075_runtime(dsn: SecretStr, db_name: str) -> None:
    """Genuine 075_001 COW runtime in an isolated test-owned context.

    Provenance: test-owned faithful copy of the base-4bf74fdc bootstrap
    reconcile recipe (AST-identical to the current reconcile body, see
    /tmp/oap-083-5-b/075-bootstrap-source-comparison.json), replayed in
    its OWN historical context because the 075 release migration graph
    and privilege context differ from the current 076 head.  The
    adapter refuses any database that is not actually at 075_001; the
    current production reconcile guard is untouched and is asserted to
    keep refusing 075 before and after this setup.

    The recipe executes, on the exact frozen PyPI
    agent-cow-postgresql 0.2.0 public interfaces only (no private
    foundation tables/SQL): deploy foundation functions -> revoke
    PUBLIC foundation access -> enable COW on content (deferred FKs,
    no unsafe canonical writes) -> nonempty foundation + content
    inventory -> harden with the product runtime/reviewer roles ->
    apply the head-aware product privilege policy (the current
    verifier conditions only the new 076 required read-surface
    objects on the actual migration revision, so at 075_001 it
    reproduces the old required-object context) -> the exact base
    reconcile content-function grants -> validate foundation +
    product privileges -> publish the readiness marker with the
    ACTUAL 075_001 revision LAST, inside the same transaction.
    """
    async with owner_connection(dsn, expected_database=db_name) as owner:
        assert (
            await owner.fetchval(
                "SELECT version_num::text FROM control.alembic_version"
            )
            == "075_001"
        )
        async with owner.transaction():
            executor = AsyncpgExecutor(owner)
            await deploy_cow_functions(executor)
            await revoke_public_foundation_access(owner)
        async with owner.transaction():
            executor = AsyncpgExecutor(owner)
            await enable_cow_schema(
                executor,
                schema="content",
                allow_deferred_fks=True,
                allow_unsafe_canonical_writes=False,
            )
            inventory = await content_object_inventory(owner)
            foundation_inventory = await foundation_object_inventory(owner)
            assert foundation_inventory, "foundation deployment inventory is empty"
            assert inventory, "content inventory unexpectedly empty"
            hardened = await harden_cow_schema(
                executor,
                schema="content",
                runtime_roles=list(RUNTIME_ROLES),
                reviewer_roles=list(REVIEWER_ROLES),
            )
            assert hardened["safe"], hardened["violations"]
            await apply_product_privileges(
                owner, readiness_state=ReadinessState.HARDENED
            )
            for fn in _RC6_075_GRANT_FUNCTIONS:
                await executor.execute(
                    f"GRANT EXECUTE ON FUNCTION content.{fn} "
                    "TO slaif_editor_runtime, slaif_control"
                )
            foundation = await validate_cow_schema_privileges(
                executor,
                schema="content",
                runtime_roles=list(RUNTIME_ROLES),
                reviewer_roles=list(REVIEWER_ROLES),
            )
            product = await verify_database_privileges(
                owner, readiness_state=ReadinessState.HARDENED
            )
            assert foundation["safe"] and product.safe, (
                foundation["violations"],
                product.violations,
            )
            final_inventory = await content_object_inventory(owner)
            assert final_inventory
            await owner.execute(
                "UPDATE control.bootstrap_readiness SET "
                "migration_revision = $1, foundation_distribution = $2, "
                "foundation_version = $3, readiness_state = $4, "
                "content_object_count = $5, content_object_fingerprint = $6, "
                "foundation_object_count = $7, foundation_object_fingerprint = $8, "
                "foundation_deployed = TRUE, foundation_hardened = TRUE, "
                "foundation_privileges_validated = TRUE, "
                "product_privileges_validated = TRUE, safe = TRUE, "
                "updated_at = CURRENT_TIMESTAMP WHERE singleton",
                "075_001",
                FOUNDATION_DISTRIBUTION,
                FOUNDATION_VERSION,
                ReadinessState.HARDENED.value,
                len(final_inventory),
                content_inventory_fingerprint(final_inventory),
                len(foundation_inventory),
                content_inventory_fingerprint(foundation_inventory),
            )
        status = await get_cow_status(AsyncpgExecutor(owner), schema="content")
        assert status["enabled"] and status["cow_functions_deployed"]
        for table in ("page", "page_composition"):
            assert table in status["tables_with_cow"], status


@pytest.mark.asyncio
async def test_v1_stored_workflow_read_refusal_discard_recreation(
    agent_site_database: AgentSiteDatabase,
    tmp_path: Path,
) -> None:
    """083/5 RC6: genuine stored v1 bytes through the real review flow.

    A meaningful site (page + composition) plus one real COW desired
    change are captured as a genuine legacy v1 snapshot through the
    real 075 materializer + the test-owned verbatim base-4bf74fdc
    075 builder + the 075 completion contract on an isolated fixture
    database, entered through the real 075 freeze constructor /
    claim / terminal job flow: the stored row is the BUILT row
    (nested node trees, six trusted pins, selected browser evidence,
    075-local canonical digest), never the unchecked raw materializer
    payload.  The
    selected legacy browser reference is TRUSTED FIXTURE DATA (one
    control-plane COMPLETED browser_run row, honestly labeled -- not
    an observed browser execution), selected with the exact base
    freeze evidence query; its retention is asserted explicitly, so
    the retained-evidence claim is nonvacuous.  A reversible
    test-local seam counts real MediaBoundary.finalize calls: ZERO
    after each refusal, exactly one (site/workspace-scoped) after the
    successful reapplication (nonvacuous observer).  The upgrade to
    the 076 head keeps the v1 row byte-identical.  The honest
    limited read (071 read model) reports the stored v1 facts
    without reinterpretation; the 076 v2-supported-format gate
    refuses the frozen render; the real accept is refused with the
    stable compatibility code BEFORE any media/canonical/
    page_base/revision/audit/outbox/accepted effect (each asserted
    explicitly).  The pre-existing legacy terminal history
    (workspace row, terminal FREEZE job row, and the selected
    COMPLETED browser run row with all stored facts) is captured
    before the upgrade and compared unchanged after the upgrade and
    after the terminal discard, excluding only the 076-added columns
    (four preview_credential_* on browser_run, one version_facts on
    workspace).  The real discard reaches its terminal state with
    the v1 row AND the post-upgrade terminal job history retained.
    An
    unknown stored format (review-snapshot/v9, trusted fixture row at
    the actual current revision so drift cannot mask the gate) is
    reported as stored, refused by the 076 read gate and by the real
    accept with zero effects, never falling back to v1 or live
    interpretation.  Finally a fresh supported v2 workspace
    REAPPLIES the same legacy desired change and is frozen + accepted
    (supported recreation/reapplication), with the v1 row still
    byte-identical.
    """
    database = agent_site_database
    dsn = database.settings.resolved_owner_dsn()
    db_name = database.name
    media_root = tmp_path / "media"
    legacy_marker = "083/5 RC6 legacy marker"

    # --- meaningful site + genuine v1 under the real 075 contract -----
    await upgrade(database.settings)
    await run_migration(
        dsn, expected_database=db_name, operation="downgrade", revision="075_001"
    )
    ws_v1: str
    page_id_v1: Any
    section_id_v1: Any
    with pytest.raises(BootstrapStateError, match="not at the required migration"):
        await reconcile(database.settings)
    async with owner_connection(dsn, expected_database=db_name) as owner:
        seed = await _rt_seed_baseline(owner)
    # Historical 075_001 COW runtime (isolated test-owned context;
    # provenance in the adapter docstring).  The current production
    # guard must still refuse 075 AFTER the historical setup too, so
    # the setup is an isolated context, never a product bypass.
    await _rc6_establish_075_runtime(dsn, db_name)
    with pytest.raises(BootstrapStateError, match="not at the required migration"):
        await reconcile(database.settings)
    async with owner_connection(dsn, expected_database=db_name) as owner:
        # Trusted fixture rows (setup, not editorial paths): one
        # renderable page + composition for the v1 capture.
        page_id_v1 = await owner.fetchval(
            "INSERT INTO content.page_base (id, site_id, slug, title,"
            " status, locale) VALUES (gen_random_uuid(), $1, 'home',"
            " 'RC6 home', 'PUBLISHED', 'en-US') RETURNING id",
            seed["site_id"],
        )
        section_id_v1 = await owner.fetchval(
            "INSERT INTO content.page_composition_base (id, site_id, page_id,"
            " component_type, schema_version, parent_id, slot_key,"
            " order_key, props) VALUES (gen_random_uuid(), $1, $2,"
            " 'Section', '1', NULL, 'default', 0, '{}'::jsonb) RETURNING id",
            seed["site_id"],
            page_id_v1,
        )
        # Trusted fixture workspace + capability (mutation scopes) for
        # the real COW desired change under 075.
        ws_v1 = str(
            await owner.fetchval(
                "INSERT INTO control.workspace (site_id, created_by,"
                " delegator_id, title, delegation_preset, effective_scopes,"
                " status, expires_at) VALUES ($1, $2, $2,"
                " 'RC6 V1 Workflow', 'L4', $3::jsonb, 'ACTIVE',"
                " now() + interval '1 hour') RETURNING id",
                seed["site_id"],
                seed["user_id"],
                json.dumps(_MUTATION_SCOPES),
            )
        )
        token, public_id, secret_digest = generate_capability_token()
        await owner.execute(
            "INSERT INTO control.capability (workspace_id, public_id,"
            " secret_digest, scopes, expires_at) VALUES ($1, $2, $3, $4::jsonb,"
            " now() + interval '30 minutes')",
            ws_v1,
            public_id,
            secret_digest,
            json.dumps(_MUTATION_SCOPES),
        )
        cap_v1 = str(
            await owner.fetchval(
                "SELECT id FROM control.capability WHERE public_id = $1",
                public_id,
            )
        )
    await _cow_create(
        database,
        workspace_id=UUID(ws_v1),
        capability_id=UUID(cap_v1),
        site_id=UUID(seed["site_id"]),
        page_id=UUID(str(page_id_v1)),
        parent_id=UUID(str(section_id_v1)),
        text=legacy_marker,
    )
    async with owner_connection(dsn, expected_database=db_name) as owner:
        # Trusted legacy FIXTURE data (control-plane record, not an
        # observed browser execution): one COMPLETED browser run bound
        # to the v1 workspace, so the legacy capture carries a real
        # selected-browser reference.
        legacy_run_id = await owner.fetchval(
            "INSERT INTO control.browser_run (id, operation_id,"
            " capability_id, workspace_id, site_id, delegator_id,"
            " contract_version, route, route_digest, target, evidence,"
            " request_digest, state, reserved_screenshots,"
            " reserved_artifact_bytes, reserved_routes, reserved_evidence,"
            " max_duration_seconds, max_attempts, attempt_count,"
            " created_at, completed_at, summary, terminal_lease_id,"
            " expires_at) VALUES (gen_random_uuid(), gen_random_uuid(),"
            " $1, $2, $3, $4, 'browser-preview/v1', '/', $5,"
            " 'desktop-chromium', ARRAY['screenshot','structure-summary'],"
            " $6, 'COMPLETED', 1, 0, 1, 2, 120, 3, 1,"
            " now() - interval '10 minutes', now() - interval '5 minutes',"
            " '{}'::jsonb, gen_random_uuid(),"
            " now() + interval '1 hour') RETURNING id",
            cap_v1,
            ws_v1,
            seed["site_id"],
            seed["user_id"],
            hashlib.sha256(b"/").hexdigest(),
            hashlib.sha256(b"083-5-rc6-legacy-run").hexdigest(),
        )
        # Real 075 freeze flow through the human-authorized constructor
        # (exact site binding + workspace:freeze check): ACTIVE ->
        # FREEZING, capability revoked, FREEZE job enqueued.
        freeze_rows = await owner.fetch(
            "SELECT * FROM control.slaif_human_agent_workspace_freeze($1,$2,$3)",
            ws_v1,
            seed["site_id"],
            seed["user_id"],
        )
        assert len(freeze_rows) == 1
        v1_freeze_job_id = str(freeze_rows[0]["job_id"])
        assert str(freeze_rows[0]["status"]) == "FREEZING"
        freeze_claimed = await owner.fetch(
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "rc6-v1-freeze",
            ["FREEZE"],
        )
        assert len(freeze_claimed) == 1
        assert str(freeze_claimed[0]["id"]) == v1_freeze_job_id
        assert str(freeze_claimed[0]["job_kind"]) == "FREEZE"
        raw_v1_doc = await _rt_materialize_payload(owner, ws_v1)
        assert raw_v1_doc.get("state_version") == "review-snapshot/v1"
        # The genuine v1 capture carries the real desired change.  The
        # 075 materializer emits FLAT pages[].nodes rows; the marker
        # lives on the COW-created Heading node's props.
        captured_texts = [
            str(node.get("props", {}).get("text"))
            for page in raw_v1_doc.get("pages", [])
            for node in page.get("nodes", [])
            if isinstance(node, dict)
        ]
        assert legacy_marker in captured_texts
        # Genuine base-4bf74fdc freeze evidence selection: COMPLETED
        # runs for the workspace, ordered by id (the exact base
        # _drain_browser_runs evidence query).
        legacy_runs = await owner.fetch(
            "SELECT id FROM control.browser_run WHERE workspace_id = $1"
            " AND state = 'COMPLETED' ORDER BY id",
            ws_v1,
        )
        assert [str(r["id"]) for r in legacy_runs] == [str(legacy_run_id)]
        # Build the stored row with the TEST-OWNED verbatim copy of the
        # base-4bf74fdc 075 builder -- not the raw materializer payload.
        v1_row = _rc6_build_snapshot_document(
            raw_v1_doc,
            created_by="rc6-v1-freeze",
            browser_evidence=[{"id": str(r["id"])} for r in legacy_runs],
        )
        built_pages = v1_row["payload"]["pages"]
        flat_node_count = sum(
            len(page.get("nodes", [])) for page in raw_v1_doc.get("pages", [])
        )
        root_node_count = sum(len(page.get("nodes", [])) for page in built_pages)
        # Source/byte-equivalence evidence: the base builder re-nests
        # the flat COW rows (Section root + Heading child), keeps the
        # desired change, and retains the selected legacy reference.
        assert flat_node_count == 2 and root_node_count == 1
        assert v1_row["browser_evidence"] == [{"id": str(legacy_run_id)}]
        heading_children = [
            child
            for page in built_pages
            for root in page.get("nodes", [])
            for child in root.get("children", [])
            if child.get("component_type") == "Heading"
        ]
        assert len(heading_children) == 1
        assert heading_children[0]["props"]["text"] == legacy_marker
        assert legacy_marker in _rc6_walk_node_texts(built_pages)
        # The 075-local digest recomputes from the stored payload and
        # matches the 075-era SQL canonical form byte-for-byte.
        v1_digest = await _rt_canonical_digest(owner, v1_row["payload"])
        assert _rc6_canonical_digest(v1_row["payload"]) == v1_row["digest"]
        assert v1_digest == v1_row["digest"]
        v1_snap_id = await owner.fetchval(
            "SELECT control.slaif_review_snapshot_complete($1::uuid,$2::jsonb)",
            ws_v1,
            json.dumps(v1_row, sort_keys=True, separators=(",", ":")),
        )
        assert v1_snap_id is not None
        v1_row_bytes = await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_v1)
        # Base-worker step 7: the terminal record closes the claimed
        # FREEZE job (pre-existing legacy terminal history, nonempty).
        assert (
            await owner.fetchval(
                "SELECT control.slaif_review_job_terminal($1::uuid, 'SUCCEEDED', NULL)",
                v1_freeze_job_id,
            )
            is True
        )
        # Pre-existing legacy terminal history facts, captured BEFORE
        # the 076 upgrade: the workspace row (REVIEW + snapshot id +
        # frozen_at), the terminal FREEZE job row, and the selected
        # COMPLETED browser run row with all its stored facts.
        ws_pre = json.loads(
            await owner.fetchval(
                "SELECT row_to_json(w)::text FROM control.workspace w WHERE w.id = $1",
                ws_v1,
            )
        )
        job_pre = json.loads(
            await owner.fetchval(
                "SELECT row_to_json(j)::text FROM control.review_job j WHERE j.id = $1",
                v1_freeze_job_id,
            )
        )
        run_pre = json.loads(
            await owner.fetchval(
                "SELECT row_to_json(r)::text FROM control.browser_run r"
                " WHERE r.id = $1",
                legacy_run_id,
            )
        )
    site_id = UUID(seed["site_id"])
    user_id = UUID(seed["user_id"])
    ws_v1_uuid = UUID(ws_v1)
    snap_v1 = UUID(str(v1_snap_id))

    # --- upgrade to head: the v1 row stays byte-identical ---------------
    await run_migration(
        dsn, expected_database=db_name, operation="upgrade", revision="head"
    )
    await reconcile(database.settings)
    async with owner_connection(dsn, expected_database=db_name) as owner:
        assert await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_v1) == v1_row_bytes
        assert (
            await owner.fetchval(
                "SELECT version_facts::text FROM control.workspace WHERE id=$1",
                ws_v1,
            )
            == "{}"
        )
        run_post = json.loads(
            await owner.fetchval(
                "SELECT row_to_json(r)::text FROM control.browser_run r"
                " WHERE r.id = $1",
                legacy_run_id,
            )
        )
        ws_post = json.loads(
            await owner.fetchval(
                "SELECT row_to_json(w)::text FROM control.workspace w WHERE w.id = $1",
                ws_v1,
            )
        )
        job_post = json.loads(
            await owner.fetchval(
                "SELECT row_to_json(j)::text FROM control.review_job j WHERE j.id = $1",
                v1_freeze_job_id,
            )
        )
    # The 076 upgrade adds exactly four preview_credential_* columns
    # to browser_run and one version_facts column to workspace; only
    # those 076-added columns are excluded, so every stored legacy
    # fact must survive the upgrade unchanged.
    for col in _RC6_076_BROWSER_RUN_COLUMNS:
        run_post.pop(col)
    ws_post.pop("version_facts")
    assert run_post == run_pre
    assert ws_post == ws_pre
    assert job_post == job_pre

    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    counting = _Rc6CountingMediaBoundary(boundary)
    try:

        async def effect_baseline() -> dict[str, Any]:
            async with owner_connection(dsn, expected_database=db_name) as owner:
                return {
                    "revision": int(
                        await owner.fetchval(
                            "SELECT canonical_revision FROM control.site WHERE id=$1",
                            site_id,
                        )
                    ),
                    "audit": int(
                        await owner.fetchval("SELECT count(*) FROM audit.promotion")
                    ),
                    "outbox": int(
                        await owner.fetchval(
                            "SELECT count(*) FROM control.cache_outbox"
                        )
                    ),
                    "composition": await owner.fetchval(
                        "SELECT encode(sha256(convert_to(string_agg("
                        " component_type || '|' || props::text || '|'"
                        " || row_version::text, '' ORDER BY id), 'UTF8')),"
                        " 'hex') FROM content.page_composition_base"
                    ),
                    "page_base": await owner.fetchval(
                        "SELECT count(*) || '/' || encode(sha256("
                        "convert_to(string_agg(row_to_json(p)::text, ''"
                        " ORDER BY p.id), 'UTF8')), 'hex')"
                        " FROM content.page_base p"
                    ),
                    "media": await owner.fetchval(
                        "SELECT count(*) || '/' || encode(sha256("
                        " convert_to(string_agg(content_hash, ','"
                        " ORDER BY content_hash), 'UTF8')), 'hex')"
                        " FROM content.media_asset WHERE site_id = $1",
                        site_id,
                    ),
                    "v1_row": await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_v1),
                }

        # Honest limited read: the 071 read model reports the STORED v1
        # facts (state_version + versions + drift), never a v2/live
        # reinterpretation.
        read_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_review_read_model($1,$2,$3)",
            ws_v1_uuid,
            site_id,
            user_id,
        )
        # The 071 read-model contract: snapshot facts (incl.
        # state_version) are NESTED under "snapshot"; drift is
        # top-level.  The stored v1 state_version is reported verbatim.
        read_doc: dict[str, Any] = json.loads(read_rows[0][0])
        assert read_doc["snapshot"]["state_version"] == "review-snapshot/v1"
        assert read_doc["drift"]["equal"] is True

        # The 076 v2-supported-format gate (the frozen render's single
        # authority) refuses the v1 snapshot: authorize returns null.
        session_id = uuid4()
        review_secret = b"v" * 32
        review_public_id = f"sas2_{session_id.hex}"
        async with owner_connection(dsn, expected_database=db_name) as owner:
            await owner.execute(
                "INSERT INTO control.user_session (id, public_id,"
                " secret_digest, csrf_secret_digest, user_account_id,"
                " absolute_expires_at) VALUES ($1,$2,$3,$4,$5,"
                " now() + interval '1 hour')",
                session_id,
                review_public_id,
                hashlib.sha256(review_secret).digest(),
                b"c" * 32,
                user_id,
            )
            authorize_row = await owner.fetchrow(
                "SELECT * FROM control.slaif_review_projection_authorize($1,$2,$3)",
                review_public_id,
                hashlib.sha256(review_secret).digest(),
                snap_v1,
            )
        assert authorize_row is None or authorize_row[0] is None

        # Real accept of the v1 snapshot: refused with the stable
        # compatibility code BEFORE any effect (each asserted).
        baseline = await effect_baseline()
        accept_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_workspace_accept($1,$2)",
            ws_v1_uuid,
            user_id,
        )
        assert len(accept_rows) == 1
        v1_job_id = UUID(str(accept_rows[0]["job_id"]))
        v1_job = await _claim_accept(database, claimant="083-5-rc6-v1")
        assert str(v1_job["id"]) == str(v1_job_id)
        v1_result = await run_accept_job(
            pool, _worker_settings(database), v1_job, media=counting
        )
        assert v1_result.status == "FAILED"
        assert v1_result.error == "SNAPSHOT_COMPATIBILITY_REFUSED"
        async with owner_connection(dsn, expected_database=db_name) as owner:
            ws_row = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                ws_v1_uuid,
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                v1_job_id,
            )
        after = await effect_baseline()
        assert after == baseline
        assert str(ws_row["status"]) == "REVIEW"
        assert ws_row["accepted_at"] is None
        assert str(job_row["status"]) == "FAILED"
        assert str(job_row["error"]) == "SNAPSHOT_COMPATIBILITY_REFUSED"
        # The refusal happened BEFORE media finalization: zero real
        # finalize calls (the successful reapplication below must
        # produce exactly one, so the observer is nonvacuous).
        assert counting.finalize_calls == []

        # Real discard of the v1 workspace: terminal state, snapshot
        # row retained (terminal actions retain snapshots).
        discard_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_human_agent_workspace_discard($1,$2,$3)",
            ws_v1_uuid,
            site_id,
            user_id,
        )
        assert len(discard_rows) == 1
        discard_job_id = UUID(str(discard_rows[0]["job_id"]))
        discard_claimed = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "083-5-rc6-d1",
            ["DISCARD"],
        )
        assert len(discard_claimed) == 1 and str(discard_claimed[0]["id"]) == str(
            discard_job_id
        )
        discard_result = await run_discard_job(
            pool, _worker_settings(database), dict(discard_claimed[0])
        )
        assert discard_result.status == "SUCCEEDED", discard_result.error
        async with owner_connection(dsn, expected_database=db_name) as owner:
            discarded = await owner.fetchrow(
                "SELECT status, discarded_at FROM control.workspace WHERE id = $1",
                ws_v1_uuid,
            )
            # Retained v1 bytes/evidence/history after terminal discard.
            assert await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_v1) == (v1_row_bytes)
            # The selected legacy browser reference is retained
            # verbatim (nonvacuous retained-evidence assertion).
            retained_row = json.loads(
                await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_v1)
            )
            assert retained_row["browser_evidence"] == [{"id": str(legacy_run_id)}]
            # Retained history: both terminal job rows survive.
            retained_accept = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                v1_job_id,
            )
            retained_discard = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                discard_job_id,
            )
            # The pre-existing (pre-upgrade) legacy terminal history
            # also survives the terminal discard verbatim: the FREEZE
            # job row and the selected COMPLETED browser run row (all
            # stored facts; 076-added columns excluded).
            retained_freeze = json.loads(
                await owner.fetchval(
                    "SELECT row_to_json(j)::text FROM control.review_job j"
                    " WHERE j.id = $1",
                    v1_freeze_job_id,
                )
            )
            retained_run = json.loads(
                await owner.fetchval(
                    "SELECT row_to_json(r)::text FROM control.browser_run r"
                    " WHERE r.id = $1",
                    legacy_run_id,
                )
            )
        assert str(discarded["status"]) == "DISCARDED"
        assert discarded["discarded_at"] is not None
        assert retained_freeze == job_pre
        for col in _RC6_076_BROWSER_RUN_COLUMNS:
            retained_run.pop(col)
        assert retained_run == run_pre
        assert str(retained_accept["status"]) == "FAILED"
        assert str(retained_accept["error"]) == "SNAPSHOT_COMPATIBILITY_REFUSED"
        assert str(retained_discard["status"]) == "SUCCEEDED"
        assert retained_discard["error"] is None

        # Unknown stored format at the ACTUAL current revision (0; the
        # drift gate cannot mask it): trusted fixture row, never a
        # product path (the 076 completion contract refuses non-v2).
        unknown_baseline = await effect_baseline()
        async with owner_connection(dsn, expected_database=db_name) as owner:
            ws3, _cap3 = await _create_workspace(
                owner, site_id, user_id, "083/5 RC6 Unknown format"
            )
            unknown_payload = {
                "state_version": "review-snapshot/v9",
                "workspace_id": str(ws3),
                "site_id": str(site_id),
                "base_site_revision": 0,
                "operation_watermark": 0,
                "site": {},
                "pages": [],
                "workspace_versions": {},
            }
            unknown_digest = await _rt_canonical_digest(owner, unknown_payload)
            unknown_snap_id = await owner.fetchval(
                "INSERT INTO control.review_snapshot (workspace_id, site_id,"
                " status, revision_watermark, versions, normalized_state,"
                " validation_report, media_references, browser_evidence,"
                " payload, digest, created_by)"
                " VALUES ($1, $2, 'COMPLETE', 0, '{}'::jsonb, $3::jsonb,"
                " $4::jsonb, '[]'::jsonb, '[]'::jsonb, $5::jsonb, $6,"
                " 'rc6-unknown-format') RETURNING id",
                ws3,
                site_id,
                json.dumps(unknown_payload),
                json.dumps(
                    {
                        "state_version": "review-snapshot/v9",
                        "pages_validated": 0,
                        "errors": [],
                        "cancelled_by_freeze": [],
                    }
                ),
                json.dumps(unknown_payload),
                unknown_digest,
            )
            assert unknown_snap_id is not None
            await owner.execute(
                "UPDATE control.workspace SET status = 'REVIEW',"
                " review_snapshot_id = $2"
                " WHERE id = $1 AND status = 'ACTIVE'",
                ws3,
                unknown_snap_id,
            )
            # The 076 read gate maps the actual reader refusal: the
            # v2-supported-format gate refuses the v9 snapshot.
            unknown_authorize = await owner.fetchrow(
                "SELECT * FROM control.slaif_review_projection_authorize($1,$2,$3)",
                review_public_id,
                hashlib.sha256(review_secret).digest(),
                unknown_snap_id,
            )
        assert unknown_authorize is None or unknown_authorize[0] is None
        unknown_read_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_review_read_model($1,$2,$3)",
            ws3,
            site_id,
            user_id,
        )
        unknown_read: dict[str, Any] = json.loads(unknown_read_rows[0][0])
        assert unknown_read["snapshot"]["state_version"] == "review-snapshot/v9"
        unknown_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_workspace_accept($1,$2)",
            ws3,
            user_id,
        )
        assert len(unknown_rows) == 1
        unknown_job_id = UUID(str(unknown_rows[0]["job_id"]))
        unknown_job = await _claim_accept(database, claimant="083-5-rc6-u1")
        assert str(unknown_job["id"]) == str(unknown_job_id)
        unknown_result = await run_accept_job(
            pool, _worker_settings(database), unknown_job, media=counting
        )
        assert unknown_result.status == "FAILED"
        # Stable pre-effect validation refusal (never a v1/live
        # fallback, never a crash or retryable transient).
        assert unknown_result.error == "SNAPSHOT_VALIDATION_FAILED"
        # Still zero real finalize calls after the second refusal.
        assert counting.finalize_calls == []
        unknown_after = await effect_baseline()
        assert unknown_after == unknown_baseline
        async with owner_connection(dsn, expected_database=db_name) as owner:
            unknown_ws = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                ws3,
            )
            unknown_job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id=$1",
                unknown_job_id,
            )
        assert str(unknown_ws["status"]) == "REVIEW"
        assert unknown_ws["accepted_at"] is None
        assert str(unknown_job_row["status"]) == "FAILED"
        assert str(unknown_job_row["error"]) == "SNAPSHOT_VALIDATION_FAILED"

        # Supported fresh recreation/reapplication: a new supported v2
        # workspace REAPPLIES the same legacy desired change and is
        # frozen + accepted through the real paths.
        async with owner_connection(dsn, expected_database=db_name) as owner:
            ws2, cap2 = await _create_workspace(
                owner, site_id, user_id, "083/5 RC6 Fresh v2"
            )
        await _cow_create(
            database,
            workspace_id=ws2,
            capability_id=cap2,
            site_id=site_id,
            page_id=UUID(str(page_id_v1)),
            parent_id=UUID(str(section_id_v1)),
            text=legacy_marker,
        )
        fresh_freeze, _jf = await _freeze_claim_run(
            database,
            workspace_id=ws2,
            site_id=site_id,
            delegator_id=user_id,
            pool=pool,
            claimant="083-5-rc6-f2",
        )
        assert fresh_freeze.status == "SUCCEEDED", fresh_freeze.error
        fresh_snap = await _snapshot_row(database, ws2)
        assert fresh_snap is not None and fresh_snap["status"] == "COMPLETE"
        fresh_payload_text = (
            fresh_snap["payload"]
            if isinstance(fresh_snap["payload"], str)
            else json.dumps(fresh_snap["payload"])
        )
        assert json.loads(fresh_payload_text)["state_version"] == ("review-snapshot/v2")
        fresh_accept, _ja = await _accept_claim_run(
            database,
            workspace_id=ws2,
            delegator_id=user_id,
            pool=pool,
            claimant="083-5-rc6-a2",
            boundary=counting,
        )
        assert fresh_accept.status == "SUCCEEDED", fresh_accept.error
        # Nonvacuous observer: exactly one real finalize call, scoped
        # to the successful reapplication's site/workspace, after
        # verification (both refusals above produced zero).
        assert len(counting.finalize_calls) == 1
        assert counting.finalize_calls[0][:2] == (str(site_id), str(ws2))
        async with owner_connection(dsn, expected_database=db_name) as owner:
            fresh_ws = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                ws2,
            )
            fresh_revision = int(
                await owner.fetchval(
                    "SELECT canonical_revision FROM control.site WHERE id=$1",
                    site_id,
                )
            )
            fresh_promotions = int(
                await owner.fetchval(
                    "SELECT count(*) FROM audit.promotion WHERE workspace_id = $1",
                    ws2,
                )
            )
            promoted_markers = int(
                await owner.fetchval(
                    "SELECT count(*) FROM content.page_composition_base"
                    " WHERE site_id = $1 AND component_type = 'Heading'"
                    " AND props->>'text' = $2",
                    site_id,
                    legacy_marker,
                )
            )
            # The genuine v1 bytes/evidence/history survive the fresh
            # work untouched.
            assert await owner.fetchval(_RT_SNAPSHOT_ROW_BYTES, ws_v1) == (v1_row_bytes)
        assert str(fresh_ws["status"]) == "ACCEPTED"
        assert fresh_ws["accepted_at"] is not None
        assert fresh_revision == 1
        assert fresh_promotions == 1
        # The reapplication of the legacy desired change is canonical.
        assert promoted_markers == 1
    finally:
        await counting.stop()
        await pool.close()


# SCRATCH ONLY - 083-5-b RC1 drop-in test block.
# Target: services/backend/tests/integration/test_freeze_review_snapshot.py
# (append at end of file; extra module imports listed in rc1-imports.py).
# Apply via /tmp/oap-083-5-b/rc1/rc1-apply.py AFTER the recorded prospective
# size decision. NOT a product landing, runtime result, order, report or
# acceptance artifact. Honest labels throughout: owner-seeded rows are
# trusted fixture setup; every editorial mutation asserted below is an
# ACTUAL public HTTP call (Agent capability surface or the 069_001
# authorized human Editor surface) into the SAME candidate workspace that
# the REAL freeze worker freezes.
#
# Corrections vs the 83fb6a4a240d scratch (strategic source review
# 2026-10-22T17:54Z), each mapped to its finding:
#   F1  G5 distinctness: the SELECTED typed reference closure is
#       proven with assets reachable ONLY through one branch each - the
#       two component-referenced assets (Image top-level mediaId,
#       DocumentList array-item mediaId) are distinct from the nine
#       FIELD-ONLY assets spanning the complete finite field-closure
#       shape map (base media scalar, base media MULTI array, localized
#       media MULTI array, base document scalar, localized document
#       scalar, base document MULTI array on typed media/document
#       fields).  Omitting the field-closure branch - or any single
#       scalar/multi-value, base/localized variant - would drop that
#       shape's field-only asset from the stored frozen media map and
#       the resolve_media consumer positives below would break;
#       duplicate references alone would not prove the branch.  A
#       twelfth, UNRELATED private asset is uploaded and never
#       referenced, so the selected closure is also asserted against
#       the full media_inventory (unrelated-private exclusion).
#   F2  the vacuous `... or True` raw-number assertion is removed; the
#       public values keep exact raw canonical-text assertions for the
#       FULL numeric map (42/0.1/3.75/7/1.5/1).  The existing qualified
#       exact-number coverage is
#       test_review_endpoint_frozen_read_media_urls_and_role_denials
#       (exact-number section at line ~4237 onward,
#       parse_snapshot_text + Decimal(0.10000000000000000000001) through
#       capture/digest/reader); its capture/read proof alone is NOT
#       approval revalidation.  The numeric APPROVAL proof lives in the
#       SEPARATE qualified composition-only workspace test appended below
#       (real freeze + real accept over honest canonical fixture values
#       carrying the SAME full exact-number map); accepting this
#       all-family public-mutation candidate would promote generic
#       page/model DML, which stays out of scope, so this candidate is
#       capture/read/consumer only.  No generic page-DML or new public
#       precision capability is claimed.
#   F3  version facts: after ALL mutations the test reads the live public
#       GET records back (BOTH surfaces) and pins the captured
#       definition_version / type_definition_version / row_version values
#       to those ACTUAL public read results; exact retained definitions
#       and view specifications are asserted, not key presence, and both
#       views carry MEANINGFUL supported filters (view_a: status PUBLISHED
#       AND rank >= 2 via the real query DSL; view_b: status PUBLISHED).
#   F4  the site profile is asserted from the CAPTURED payload["site"]
#       itself (exact _SITE_PROFILE_KEYS values) as well as from the live
#       control row (unchanged revision).
#   F5  the sixteen-family map is explicit (see FAMILY_MAP assertions):
#       types/fields/items/translations/relations/views/locales/theme/
#       regions/navigation definitions/navigation items/redirects/pages/
#       page compositions/media inventory/proposals + control site
#       profile, with actual media_inventory values, BOTH surfaces' field
#       definitions, and real nonrenderable/deleted states: a DRAFT item
#       (gamma), a DRAFT-status filter exclusion, and a page DELETED via
#       the public Agent API (tombstone retained with deleted_at set and
#       effective_route NULL). A missing translation (gamma sl-SI) is
#       asserted as an absent retained row, not a deletion test.
#   F6  proposal non-execution: honest trusted setup (the typed internal
#       create function; no public Agent/Editor handler exists), the
#       retained kind/payload/state asserted, and actual no-effects
#       oracles: the row state stays PROPOSED (the 042_001 CHECK
#       constraint permits ONLY 'PROPOSED'), the site canonical_revision
#       is unchanged, control.cache_outbox has zero rows for the site,
#       and no audit row of any side-effect kind exists.
#   F7  sibling shapes corrected to the ACTUAL builder output
#       (review_worker/snapshot.py _media_references, lines 202-231):
#       media_references is a LIST of {id, mime_type, size_bytes,
#       content_hash, public_status} sorted by key; payload media is a
#       DICT keyed by id. Both directions are compared entry-for-entry,
#       duplicate ids are refused, and the frozen admission re-check
#       (render_api/frozen_source.py ~2096-2100: list length equals media
#       map length) is the same-shape consumer proof. browser_evidence is
#       honestly [] here (no browser run is seeded by RC1); the
#       NON-EMPTY selected-COMPLETED evidence binding is the existing
#       qualified coverage: freeze_job evidence ingestion of claimed
#       terminal runs into the immutable snapshot row, the snapshot ACL
#       grants (076_001 privileges), and the nonempty legacy cases at
#       test_freeze_review_snapshot.py lines ~5618/5629/5893
#       (browser_evidence == [{"id": legacy_run_id}]) - cited, with the
#       RC4 actual-worker proof as the runtime owner.
#   F8  raw/resolved responsive values verified against the actual
#       schema/common consumer: page style rows carry raw overrides
#       (page style_overrides + style.overrides) AND the resolved
#       projection (style.resolved, the slaif_page_style_project output),
#       asserted on BOTH surfaces' pages.
#   F9  fixture/shape repairs: distinct expected-vs-captured maps (no
#       variable reuse), every SQL literal parameterized ($n), actual
#       response shapes (AgentMutationResponse {record, operation_id,
#       action}; style/theme/locale GETs return the record directly;
#       editor POSTs return the record directly; media upload record
#       MediaAssetRecord; navigation payload is {definitions, items}),
#       and the capability table is control.capability (the
#       control.control_capability table does not exist).
#   F10 header region seeded with ONE valid nav entry (the closed region
#       schema requires 1-12 header nav entries; an empty nav is not a
#       valid fixture, not a weaker validator).

# ---------------------------------------------------------------------------
# Module-level helper bundle (drop-in; names are rc1_-prefixed so they
# cannot collide with the target file's existing helpers).
# ---------------------------------------------------------------------------

RC1_PNG_BYTES = b"\x89PNG\r\n\x1a\nrc1-private-image-fixture"
RC1_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]>> endobj\n"
    b"trailer <</Root 1 0 R>>\n"
    b"%%EOF\n"
)
RC1_PDF2_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 200 200]>> endobj\n"
    b"trailer <</Root 1 0 R>>\n"
    b"%%EOF\n"
)
# G5: the nine FIELD-ONLY fixtures covering the COMPLETE finite
# field-closure shape map - base media scalar (cover), base media MULTI
# pair (photo base), localized media MULTI pair (photo sl), base
# document scalar + localized document scalar (summary_doc), and the
# base document MULTI pair (doc) - distinct content, hence distinct
# hashes, from the two component-referenced and the unrelated fixtures.
RC1_PNG2_BYTES = b"\x89PNG\r\n\x1a\nrc1-field-photo-base-fixture"
RC1_PNG3_BYTES = b"\x89PNG\r\n\x1a\nrc1-field-photo-sl-fixture"
RC1_PDF3_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 300 400]>> endobj\n"
    b"trailer <</Root 1 0 R>>\n"
    b"%%EOF\n"
)
RC1_PNG4_BYTES = b"\x89PNG\r\n\x1a\nrc1-field-photo2-base-fixture"
RC1_PNG5_BYTES = b"\x89PNG\r\n\x1a\nrc1-field-photo2-sl-fixture"
RC1_PDF4_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 240 320]>> endobj\n"
    b"trailer <</Root 1 0 R>>\n"
    b"%%EOF\n"
)
RC1_PNG6_BYTES = b"\x89PNG\r\n\x1a\nrc1-field-cover-scalar-fixture"
RC1_PDF5_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 260 340]>> endobj\n"
    b"trailer <</Root 1 0 R>>\n"
    b"%%EOF\n"
)
RC1_PDF6_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 280 360]>> endobj\n"
    b"trailer <</Root 1 0 R>>\n"
    b"%%EOF\n"
)
# The REAL existing L4 preset derivation pinned from the product source
# (control_api/workspace_http._PRESET_SCOPES); importing the private name
# in-test is deliberate so a future preset change breaks this test
# visibly instead of silently widening the seeded authority.
RC1_L4_SCOPES = sorted(
    __import__(
        "slaif_agent_site.control_api.workspace_http", fromlist=["_PRESET_SCOPES"]
    )._PRESET_SCOPES[DelegationPreset.L4_SITE_ARCHITECT]
)


def _rc1_agent_settings(
    database: AgentSiteDatabase, media_root: Path
) -> AgentDatabaseSettings:
    login, password = database.credentials["slaif_agent_runtime"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    return AgentDatabaseSettings(
        mode=AgentDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
            f"{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        media_root=media_root,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="rc1-capture-agent-fixture",
    )


def _rc1_walk_nodes(nodes: Any) -> Any:
    for node in nodes:
        yield node
        yield from _rc1_walk_nodes(node.children)


def _rc1_node_id(route: Any, component: str) -> str:
    for node in _rc1_walk_nodes(route.composition.nodes):
        if node.component_type == component:
            return str(node.id)
    raise AssertionError(f"component not found in frozen projection: {component}")


async def _rc1_frozen_positive(
    database: AgentSiteDatabase,
    snapshot_row: Any,
    *,
    site_id: UUID,
    workspace_id: UUID,
) -> dict[str, Any]:
    """The frozen common consumer re-derives the retained bindings.

    This is the shared RenderProjectionService engine driven by the
    FrozenRenderSurface over the ACTUAL stored v2 row (same code path the
    review route executes; no shadow engine, no SQL-string fake).
    """
    from slaif_agent_site.render_api import frozen_source as _fs
    from slaif_agent_site.sites.models import SiteContext as _SiteContext

    surface = _fs.FrozenRenderSurface(
        dict(snapshot_row),
        expected_snapshot_id=snapshot_row["id"],
        expected_site_id=site_id,
        expected_workspace_id=workspace_id,
    )
    frozen_ctx = _SiteContext._from_frozen(
        site_id=site_id,
        site_key=surface.site_key,
        status=surface.site_status,
        base_site_revision=surface.base_site_revision,
        default_locale=surface.default_locale,
        matched_path_prefix=None,
    )
    service = RenderProjectionService(surface)

    async def query(path: str) -> Any:
        return await service._query(
            surface,
            context=frozen_ctx,
            request=RenderPageRequest(authority="localhost", path=path),
            render_mode="review",
            snapshot_id=snapshot_row["id"],
        )

    def items(route: Any, component: str) -> list[dict[str, Any]]:
        return [dict(item) for item in route.bindings[_rc1_node_id(route, component)]]

    news = await query("/rc1news")
    press = await query("/rc1press")
    detail = await query("/rc1news/alpha")
    home = await query("/")
    return {
        "news_list_slugs": [i["slug"] for i in items(news, "CollectionList")],
        "news_list_ranks": [i["values"]["rank"] for i in items(news, "CollectionList")],
        "press_list_slugs": [i["slug"] for i in items(press, "CollectionList")],
        # Real contract: the detail route resolves to the detail PAGE
        # (ProjectionPage.slug = the page row slug, e.g. "rc1item");
        # the addressed ITEM slug is the route parameter.
        "detail_slug": detail.page.slug,
        "detail_page_id": str(detail.page.id),
        "detail_route_parameters": dict(detail.route_parameters),
        "detail_related_slugs": [i["slug"] for i in items(detail, "RelatedItems")],
        "home_image_media": (
            dict(
                next(
                    iter(
                        [
                            n
                            for n in _rc1_walk_nodes(home.composition.nodes)
                            if n.component_type == "Image"
                        ]
                    )
                ).media
            )
            if any(
                n.component_type == "Image"
                for n in _rc1_walk_nodes(home.composition.nodes)
            )
            else None
        ),
        "news_doclist_items": [
            dict(m)
            for m in next(
                iter(
                    [
                        n
                        for n in _rc1_walk_nodes(news.composition.nodes)
                        if n.component_type == "DocumentList"
                    ]
                )
            ).media_items
        ],
    }


# Exact retained-shape key sets, copied from the verified frozen consumer
# (render_api/frozen_source.py lines 653-950) so a product shape change
# fails this test visibly instead of silently weakening the pin.
RC1_SNAPSHOT_ROW_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "workspace_id",
        "site_id",
        "status",
        "revision_watermark",
        "versions",
        "normalized_state",
        "validation_report",
        "media_references",
        "browser_evidence",
        "payload",
        "digest",
        "created_by",
        "created_at",
    }
)
RC1_PAYLOAD_KEYS: frozenset[str] = frozenset(
    {
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
    }
)
RC1_VALIDATION_REPORT_KEYS: frozenset[str] = frozenset(
    {"state_version", "pages_validated", "errors", "cancelled_by_freeze"}
)
RC1_MEDIA_REFERENCE_KEYS: frozenset[str] = frozenset(
    {"id", "mime_type", "size_bytes", "content_hash", "public_status"}
)
RC1_MEDIA_ENTRY_KEYS: frozenset[str] = frozenset(
    {"id", "mime_type", "size_bytes", "content_hash", "public_status"}
)
RC1_SITE_PROFILE_KEYS: frozenset[str] = frozenset(
    {
        "site_key",
        "display_name",
        "status",
        "default_locale",
        "component_catalog_version",
        "content_model_revision",
        "created_at",
        "updated_at",
    }
)
RC1_CONTENT_KEYS: frozenset[str] = frozenset(
    {"types", "fields", "items", "translations", "relations", "views"}
)
RC1_TYPE_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "key",
        "labels",
        "slug_pattern",
        "status",
        "definition_version",
        "settings",
        "created_at",
        "updated_at",
    }
)
RC1_FIELD_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "type_id",
        "key",
        "label",
        "field_type",
        "required",
        "localized",
        "cardinality",
        "position",
        "validation",
        "ui_options",
        "definition_version",
        "created_at",
        "updated_at",
    }
)
RC1_ITEM_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "type_id",
        "slug",
        "status",
        "type_definition_version",
        "values",
        "row_version",
        "created_at",
        "updated_at",
    }
)
RC1_TRANSLATION_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "item_id",
        "locale",
        "localized_values",
        "row_version",
        "created_at",
        "updated_at",
    }
)
RC1_RELATION_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "source_item_id",
        "field_definition_id",
        "target_item_id",
        "position",
        "metadata",
        "row_version",
        "created_at",
        "updated_at",
    }
)
RC1_VIEW_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "type_id",
        "key",
        "filter_spec",
        "sort_spec",
        "projection_spec",
        "pagination_spec",
        "created_at",
        "updated_at",
        "definition_version",
        "row_version",
    }
)
RC1_LOCALE_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "tag",
        "enabled",
        "is_default",
        "position",
        "metadata",
        "row_version",
        "created_at",
        "updated_at",
    }
)
RC1_THEME_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "schema_version",
        "renderer_version",
        "row_version",
        "palette",
        "typography",
        "layout",
        "shape",
        "created_at",
        "updated_at",
    }
)
RC1_PAGE_STYLE_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "page_id",
        "site_id",
        "schema_version",
        "row_version",
        "overrides",
        "resolved",
        "created_at",
        "updated_at",
    }
)
RC1_REGION_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "region_key",
        "variant",
        "content",
        "schema_version",
        "row_version",
        "created_at",
        "updated_at",
    }
)
RC1_NAV_DEFINITION_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "key",
        "label",
        "settings",
        "created_at",
        "updated_at",
        "labels",
        "row_version",
    }
)
RC1_NAV_ITEM_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "navigation_id",
        "parent_id",
        "page_id",
        "target_kind",
        "target_value",
        "labels",
        "locale",
        "position",
        "row_version",
        "created_at",
        "updated_at",
        "parent_key",
    }
)
RC1_REDIRECT_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "source_route",
        "target",
        "status_code",
        "locale",
        "row_version",
        "created_at",
        "updated_at",
    }
)
RC1_PAGE_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "slug",
        "title",
        "status",
        "locale",
        "parent_id",
        "route_template",
        "effective_route",
        "row_version",
        "created_at",
        "updated_at",
        "deleted_at",
        "style_overrides",
        "style",
        "nodes",
    }
)
RC1_COMPOSITION_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "page_id",
        "component_type",
        "schema_version",
        "parent_id",
        "slot_key",
        "order_key",
        "props",
        "catalog_version",
        "created_at",
        "updated_at",
        "row_version",
    }
)
RC1_PROPOSAL_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "workspace_id",
        "kind",
        "payload",
        "state",
        "created_at",
        "updated_at",
    }
)
RC1_MEDIA_INVENTORY_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "site_id",
        "uploaded_by",
        "filename",
        "mime_type",
        "size_bytes",
        "content_hash",
        "storage_key",
        "alt_text",
        "metadata",
        "created_at",
        "updated_at",
        "public_status",
        "published_at",
    }
)


@pytest.mark.asyncio
async def test_rc1_public_agent_and_editor_capture_retained_families(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """RC1: actual public Agent AND authorized human Editor capture.

    HONEST SCOPE (no claim is wider than its setup):
    * Trusted fixture setup (owner-seeded, labeled, NOT public work):
      site + two locale rows + theme + membership + one stored header
      region row (with one valid nav entry) + the L4 candidate
      workspace/capability + the one proposal row (proposals have a typed
      internal creation function only - no public Agent/Editor handler
      exists; the design treats them as retained read-only data that must
      never execute).
    * ACTUAL public AGENT HTTP (real capability, real endpoints):
      content type + eight fields (short_text/long_text/integer/decimal/
      media-MULTI-localized/media-base-scalar/media-base-MULTI/reference),
      three items (one DRAFT, exact raw base numbers, one carrying both
      base media field shapes), four en translations + two sl-SI
      translations (one carrying a localized media MULTI array),
      a relation, a view with a meaningful supported filter + sort +
      projection + pagination, four pages + one page deleted through
      the public API (tombstone), seven composition components
      (including the selected Image/DocumentList typed media
      references), a non-default raw page style, theme, locale,
      redirect, navigation + item, a global-region variant, and twelve
      media uploads (two component-referenced, nine FIELD-ONLY, one
      UNRELATED private).
    * ACTUAL authorized human EDITOR HTTP through the 069_001 envelope
      (X-Editor-Workspace + human session/CSRF + idempotency + request
      digest -> control.slaif_human_agent_workspace_editor_assert):
      content type + five fields (including a MULTI document field, a
      base scalar document field, and a localized scalar document
      field), two items (one with both document field shapes), an en +
      sl-SI translation pair (sl-SI carrying the localized scalar
      document value) plus a second en translation, a
      relation, a view with its own meaningful filter, a page +
      component, a non-default page style, theme palette, and the media
      alt_text PATCH on the Agent-uploaded image.
    * The REAL freeze worker (narrow credential claim + run_freeze_job)
      freezes this SAME candidate workspace.  This candidate is
      capture/read/consumer only: accepting it would promote generic
      page/model DML, so the numeric approval proof is a SEPARATE
      qualified composition-only workspace test (appended below).
    * READ-BOUNDARY assertions on the actual stored v2 document:
      sibling bindings (digest over canonical text, normalized_state
      identity, workspace_versions pins, media_references LIST vs media
      DICT both directions, browser_evidence honest), the explicit
      sixteen-family retained map with versions pinned to the public
      read-back records, exact raw-number canonical text, retained
      nonrenderable/deleted states, non-executed proposal with actual
      no-effects oracles, the captured site profile, and the frozen
      common-consumer positive re-derivation.
    """
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    tag = uuid4().hex[:8]
    site_key = f"rc1int-{tag}"
    png_hash = hashlib.sha256(RC1_PNG_BYTES).hexdigest()
    png2_hash = hashlib.sha256(RC1_PNG2_BYTES).hexdigest()
    png3_hash = hashlib.sha256(RC1_PNG3_BYTES).hexdigest()
    pdf_hash = hashlib.sha256(RC1_PDF_BYTES).hexdigest()
    pdf2_hash = hashlib.sha256(RC1_PDF2_BYTES).hexdigest()
    pdf3_hash = hashlib.sha256(RC1_PDF3_BYTES).hexdigest()
    png4_hash = hashlib.sha256(RC1_PNG4_BYTES).hexdigest()
    png5_hash = hashlib.sha256(RC1_PNG5_BYTES).hexdigest()
    pdf4_hash = hashlib.sha256(RC1_PDF4_BYTES).hexdigest()
    png6_hash = hashlib.sha256(RC1_PNG6_BYTES).hexdigest()
    pdf5_hash = hashlib.sha256(RC1_PDF5_BYTES).hexdigest()
    pdf6_hash = hashlib.sha256(RC1_PDF6_BYTES).hexdigest()

    assert sorted(RC1_L4_SCOPES) == sorted(
        READ_SCOPES | L1_SCOPES | L2_SCOPES | L3_SCOPES | L4_SCOPES
    )

    seeded: dict[str, Any] = {}
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        # Trusted identity/site substrate (labeled setup, not public work).
        delegator_id = await owner.fetchval(
            "INSERT INTO control.user_account (id, identity_kind,"
            " local_username, local_username_normalized, password_hash,"
            " display_name, status) VALUES (gen_random_uuid(),'LOCAL',"
            " 'Rc1.Delegator','rc1.delegator',$1,'Rc1 Delegator','ACTIVE')"
            " RETURNING id",
            _AGGON2,
        )
        site_id = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name, default_locale,"
            " component_catalog_version) VALUES ($1,'Rc1 Int','en','catalog-v1')"
            " RETURNING id",
            site_key,
        )
        await owner.execute(
            "INSERT INTO control.site_membership (site_id,user_account_id,"
            " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
            site_id,
            delegator_id,
        )
        # Trusted locale setup (the Agent PATCHes one, below).
        for locale, is_default, position in (("en", True, 0), ("sl-SI", False, 1)):
            await owner.execute(
                "INSERT INTO content.site_locale_base (site_id,tag,enabled,"
                " is_default,position) VALUES ($1,$2,true,$3,$4)",
                site_id,
                locale,
                is_default,
                position,
            )
        await owner.execute(
            "INSERT INTO content.theme_base (id, site_id, schema_version,"
            " renderer_version, palette, typography, layout, shape) VALUES"
            " (gen_random_uuid(), $1, 'theme-schema/v1', 'renderer-v1',"
            ' \'{"preset":"ocean"}\'::jsonb,'
            ' \'{"family":"system","scale":"balanced","weight":"regular"}\'::jsonb,'
            ' \'{"content_width":"md","spacing":"md","grid_gap":"md"}\'::jsonb,'
            ' \'{"radius":"md","shadow":"sm"}\'::jsonb)',
            site_id,
        )
        # F10: one stored header region with ONE VALID nav entry (the
        # closed region schema requires 1-12 header nav entries).
        region_id = await owner.fetchval(
            "INSERT INTO content.site_global_region_base (id, site_id,"
            " region_key, variant, content, schema_version) VALUES"
            " (gen_random_uuid(), $1,'header',"
            " 'institutional', $2::jsonb, 'global-region/v1') RETURNING id",
            site_id,
            json.dumps(
                {
                    "nav": [
                        {
                            "label": "News",
                            "target": {"kind": "internal", "value": "/rc1news"},
                        }
                    ]
                },
                sort_keys=True,
            ),
        )
        # The real existing L4 authority (RC1_L4_SCOPES pin above), the
        # pinned version facts, one candidate workspace, one capability.
        # Human-chosen bounded quotas (076_001 creation contract: request
        # 1..10000, mutation 0..5000, delete 0..5000, upload 0..1000);
        # production issues the capability inheriting exactly these
        # workspace quotas (038_001), so both rows carry the same values.
        workspace_id = await owner.fetchval(
            "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
            " actor_type, title, delegation_preset, effective_scopes,"
            " version_facts,"
            " request_quota, mutation_quota, delete_quota, upload_quota,"
            " status, expires_at) VALUES ($1,$2,$2,'AGENT','RC1 Candidate',"
            " 'L4_SITE_ARCHITECT', $3::jsonb, " + _CURRENT_VERSION_FACTS + ","
            " 1000, 500, 8, 32,"
            " 'ACTIVE', now()+interval '1 hour') RETURNING id",
            site_id,
            delegator_id,
            json.dumps(RC1_L4_SCOPES),
        )
        token, public_id, digest = generate_capability_token()
        await owner.execute(
            "INSERT INTO control.capability (workspace_id, public_id,"
            " secret_digest, scopes, expires_at, request_quota,"
            " mutation_quota, delete_quota, upload_quota) VALUES"
            " ($1,$2,$3,$4::jsonb, now()+interval '30 minutes',"
            " 1000, 500, 8, 32)",
            workspace_id,
            public_id,
            digest,
            json.dumps(RC1_L4_SCOPES),
        )
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE public_id = $1",
            public_id,
        )
        # F6: one trusted proposal (typed internal creation; NO public
        # Agent/Editor handler exists to create one; must be retained
        # and NEVER executed).
        # The trusted creation contract (042_001) requires the caller's
        # trusted COW context: app.session_id must parse to exactly the
        # candidate workspace UUID, and the foundation COW write trigger
        # requires app.operation_id whenever a session is bound
        # (production sets both from the foundation COW session).  The
        # row therefore lands in this workspace's COW session layer,
        # exactly where the 076 freeze (which binds the same session
        # context) captures it.
        proposal_operation_id = uuid4()
        await owner.execute(
            "SELECT set_config('app.session_id', $1::text, false),"
            " set_config('app.operation_id', $2::text, false)",
            str(workspace_id),
            str(proposal_operation_id),
        )
        try:
            # Honest fixture boundary: the COW INSTEAD-OF write trigger
            # returns a NEW whose id is NULL (the generated UUID is
            # materialized in the session change row via the table
            # default), so the constructor's RETURNING composite cannot
            # supply the row identity.  This is a trusted INTERNAL
            # fixture - no public proposal API exists or is claimed.
            await owner.execute(
                "SELECT content.slaif_proposed_side_effect_create($1,$2,"
                " 'cache_purge',$3::jsonb)",
                site_id,
                workspace_id,
                json.dumps({"scope": "rc1-retained-proposal"}),
            )
            # The row identity is read back through the EXISTING product
            # list contract (trusted site/workspace) under the same
            # bound workspace session: exactly one row with this unique
            # kind+payload; no newest/mtime guess, no foundation-table
            # coupling.
            listed = await owner.fetch(
                "SELECT * FROM content.slaif_proposed_side_effect_list($1,$2)",
                site_id,
                workspace_id,
            )
        finally:
            await owner.execute(
                "SELECT set_config('app.session_id', '', false),"
                " set_config('app.operation_id', '', false)"
            )
        matching = [
            row
            for row in listed
            if row["kind"] == "cache_purge"
            and (
                row["payload"]
                if isinstance(row["payload"], dict)
                else json.loads(row["payload"])
            )
            == {"scope": "rc1-retained-proposal"}
        ]
        assert len(matching) == 1, [dict(row) for row in listed]
        proposal_id = str(matching[0]["id"])
        seeded = {
            "delegator_id": UUID(str(delegator_id)),
            "site_id": UUID(str(site_id)),
            "workspace_id": UUID(str(workspace_id)),
            "capability_token": token,
            "region_id": region_id,
            "proposal_id": proposal_id,
        }
    assert capability_id is not None
    revision_before_freeze = None  # set after the editor surface, before freeze

    # ------------------------------------------------------------ Agent app
    agent_settings = _rc1_agent_settings(database, tmp_path / "rc1-media")
    agent_app = create_agent_app(
        settings=ServiceSettings.for_test(), database_settings=agent_settings
    )

    # -------------------------------------------- Editor app (069 envelope)
    control_login, control_password = database.credentials["slaif_control"]
    editor_login, editor_password = database.credentials["slaif_editor_runtime"]
    control_settings = ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(_dsn(database, control_login, control_password)),
        dsn_file=None,
        expected_database=database.name,
        expected_login=database.credentials["slaif_control"][0],
        pool_min_size=1,
        pool_max_size=4,
        application_name="rc1-editor-http",
    )
    editor_settings = EditorDatabaseSettings(
        mode=EditorDatabaseMode.TEST,
        dsn=SecretStr(_dsn(database, editor_login, editor_password)),
        dsn_file=None,
        expected_database=database.name,
        expected_login=database.credentials["slaif_editor_runtime"][0],
        pool_min_size=1,
        pool_max_size=2,
        application_name="rc1-editor-db",
    )
    control = ControlDatabase(control_settings)
    editor = EditorDatabase(editor_settings)

    ids: dict[str, Any] = {}
    try:
        await control.start()
        await editor.start()
        editor_app = create_editor_app(
            settings=ServiceSettings(mode=EnvironmentMode.TEST),
            database=control,
            editor_database=editor,
        )
        session = await control.human_session_service().create(seeded["delegator_id"])
        ws_header = {"x-editor-workspace": str(seeded["workspace_id"])}

        def editor_headers(*, idempotency: str | None = None) -> dict[str, str]:
            value = {
                "cookie": f"slaif_session={session.token.get_secret_value()};"
                f" slaif_csrf={session.csrf_token.get_secret_value()}",
                "x-csrf-token": session.csrf_token.get_secret_value(),
                **ws_header,
            }
            if idempotency is not None:
                value["idempotency-key"] = idempotency
            return value

        async with agent_app.router.lifespan_context(agent_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=agent_app),
                base_url="http://agent.test",
            ) as ag:
                ah = {"Authorization": f"Bearer {seeded['capability_token']}"}

                def agent_idem(op: str) -> dict[str, str]:
                    return {"Idempotency-Key": f"rc1-{tag}-{op}"}

                async def agent_record(
                    path: str, body: dict[str, Any], op: str
                ) -> dict[str, Any]:
                    resp = await ag.post(
                        path, headers={**ah, **agent_idem(op)}, json=body
                    )
                    assert resp.status_code == 201, resp.text
                    record: dict[str, Any] = resp.json()["record"]
                    return record

                # ---- Agent surface: media uploads FIRST (L1 upload)

                # G5: each typed reference branch is proven with DISTINCT
                # assets - the two component-referenced assets (Image
                # top-level mediaId, DocumentList array-item mediaId)
                # differ from the nine field-only assets spanning the
                # complete finite closure shape map (base media scalar,
                # base media MULTI pair, localized media MULTI pair,
                # base document scalar, base document MULTI pair,
                # localized document scalar); the twelfth UNRELATED
                # private asset is never
                # referenced, so the selected closure is asserted
                # against the full media_inventory (unrelated-private
                # exclusion).
                uploads = (
                    (
                        "media-img",
                        "rc1.png",
                        RC1_PNG_BYTES,
                        "image/png",
                        "RC1 photo",
                        "media_img",
                        png_hash,
                    ),
                    (
                        "media-pdf-comp",
                        "rc1.pdf",
                        RC1_PDF_BYTES,
                        "application/pdf",
                        "RC1 document",
                        "media_pdf_comp",
                        pdf_hash,
                    ),
                    (
                        "media-photo-en",
                        "rc1-photo-en.png",
                        RC1_PNG2_BYTES,
                        "image/png",
                        "RC1 base photo",
                        "media_photo_en",
                        png2_hash,
                    ),
                    (
                        "media-photo2-en",
                        "rc1-photo2-en.png",
                        RC1_PNG4_BYTES,
                        "image/png",
                        "RC1 base photo 2",
                        "media_photo2_en",
                        png4_hash,
                    ),
                    (
                        "media-photo-sl",
                        "rc1-photo-sl.png",
                        RC1_PNG3_BYTES,
                        "image/png",
                        "RC1 sl photo",
                        "media_photo_sl",
                        png3_hash,
                    ),
                    (
                        "media-photo2-sl",
                        "rc1-photo2-sl.png",
                        RC1_PNG5_BYTES,
                        "image/png",
                        "RC1 sl photo 2",
                        "media_photo2_sl",
                        png5_hash,
                    ),
                    (
                        "media-pdf-doc",
                        "rc1-doc-field.pdf",
                        RC1_PDF3_BYTES,
                        "application/pdf",
                        "RC1 document field",
                        "media_pdf_doc",
                        pdf3_hash,
                    ),
                    (
                        "media-pdf-doc2",
                        "rc1-doc-field2.pdf",
                        RC1_PDF4_BYTES,
                        "application/pdf",
                        "RC1 document field 2",
                        "media_pdf_doc2",
                        pdf4_hash,
                    ),
                    (
                        "media-cover",
                        "rc1-cover.png",
                        RC1_PNG6_BYTES,
                        "image/png",
                        "RC1 cover scalar",
                        "media_cover",
                        png6_hash,
                    ),
                    (
                        "media-doc-base",
                        "rc1-doc-base.pdf",
                        RC1_PDF5_BYTES,
                        "application/pdf",
                        "RC1 document scalar base",
                        "media_doc_base",
                        pdf5_hash,
                    ),
                    (
                        "media-doc-sl",
                        "rc1-doc-sl.pdf",
                        RC1_PDF6_BYTES,
                        "application/pdf",
                        "RC1 document scalar localized",
                        "media_doc_sl",
                        pdf6_hash,
                    ),
                    (
                        "media-pdf-unrelated",
                        "rc1-unrelated.pdf",
                        RC1_PDF2_BYTES,
                        "application/pdf",
                        "RC1 unrelated private doc",
                        "media_pdf_unrelated",
                        pdf2_hash,
                    ),
                )
                for (
                    op,
                    filename,
                    data,
                    mime,
                    alt_text,
                    id_key,
                    content_hash,
                ) in uploads:
                    upload = await ag.post(
                        "/api/agent/v1/media/assets",
                        headers={**ah, **agent_idem(op)},
                        data={"alt_text": alt_text, "metadata": "{}"},
                        files={"file": (filename, data, mime)},
                    )
                    assert upload.status_code == 201, upload.text
                    record = upload.json()["record"]
                    assert record["content_hash"] == content_hash
                    assert record["public_status"] == "private"
                    ids[id_key] = record["id"]

                # ---- Agent surface: model / fields (real L4 scopes)
                type_a = await agent_record(
                    "/api/agent/v1/content-model/types",
                    {
                        "key": f"rc1_news_{tag}",
                        "labels": {"en": "RC1 news"},
                        "slug_pattern": f"/rc1news/{tag}/{{slug}}",
                        "settings": {},
                    },
                    "type-a",
                )
                ids["type_a"] = type_a["id"]
                # F1: the typed media fields (IMAGE references) join the
                # real eight-field definition closure; the reference
                # field carries its declared target in the actual
                # creation contract (bounded validation dict).
                # G5: photo is a MULTI-value (cardinality 2) localized
                # media field (localized array branch), gallery is the
                # BASE MULTI media field (base array branch) and cover
                # is the BASE scalar media field - together they cover
                # the complete media-field closure shape map.
                field_specs = [
                    ("title", "short_text", True, True, 0, 1),
                    ("summary", "long_text", False, True, 1, 1),
                    ("rank", "integer", True, False, 2, 1),
                    ("ratio", "decimal", True, False, 3, 1),
                    ("photo", "media", False, True, 4, 2),
                    ("cover", "media", False, False, 5, 1),
                    ("gallery", "media", False, False, 6, 2),
                    ("related", "reference", False, False, 7, 1),
                ]
                for (
                    key,
                    prim,
                    required,
                    localized,
                    position,
                    cardinality,
                ) in field_specs:
                    field = await agent_record(
                        f"/api/agent/v1/content-model/types/{ids['type_a']}/fields",
                        {
                            "key": key,
                            "label": key.title(),
                            "field_type": prim,
                            "required": required,
                            "localized": localized,
                            "cardinality": cardinality,
                            "position": position,
                            "validation": (
                                {"target_type_id": ids["type_a"]}
                                if key == "related"
                                else {}
                            ),
                        },
                        f"field-a-{key}",
                    )
                    ids[f"field_{key}"] = field["id"]

                # ---- Agent surface: items / translations / relation
                # F5: gamma is DRAFT - a real nonrenderable retained
                # state (the live/frozen list excludes it; the payload
                # keeps it). F2: the exact raw numbers 42/0.1/3.75 are
                # written through the ACTUAL public path as BASE field
                # values (rank/ratio) and must keep their exact
                # canonical digits below.  The public contract stores
                # localized field values ONLY in translation rows, so
                # the base values carry the non-localized fields.
                item_values: dict[str, dict[str, Any]] = {
                    "alpha": {
                        "rank": 42,
                        "ratio": 0.1,
                        # G5: the BASE media MULTI field value is a
                        # MULTI array (cardinality 2) of FIELD-ONLY
                        # assets (distinct from the component image).
                        "gallery": [
                            ids["media_photo_en"],
                            ids["media_photo2_en"],
                        ],
                        # G5: the BASE scalar media field value is its
                        # own FIELD-ONLY asset.
                        "cover": ids["media_cover"],
                    },
                    "beta": {
                        "rank": 7,
                        "ratio": 1.5,
                    },
                    "gamma": {
                        "rank": 1,
                        "ratio": 3.75,
                    },
                }
                item_statuses = {
                    "alpha": "PUBLISHED",
                    "beta": "PUBLISHED",
                    "gamma": "DRAFT",
                }
                for slug, values in item_values.items():
                    item = await agent_record(
                        f"/api/agent/v1/content-items/types/{ids['type_a']}",
                        {
                            "type_id": ids["type_a"],
                            "slug": slug,
                            "status": item_statuses[slug],
                            "values": values,
                        },
                        f"item-{slug}",
                    )
                    ids[f"item_{slug}"] = item["id"]
                # G5: alpha's sl-SI translation carries the LOCALIZED
                # media MULTI array - FIELD-ONLY assets (the 076 field
                # closure reads every base value AND every localized
                # value); gamma deliberately has NO translation at all:
                # the absent rows are retained facts.  The public
                # contract stores localized field values ONLY in
                # translation rows, so each PUBLISHED item's en text
                # also lives in an en translation.
                translations_expected: dict[str, dict[str, dict[str, Any]]] = {
                    "alpha": {
                        "en": {
                            "title": "Alpha rc1",
                            "summary": "Alpha povz en",
                        },
                        "sl-SI": {
                            "title": "Alfa rc1",
                            "summary": "Alfa povz",
                            "photo": [
                                ids["media_photo_sl"],
                                ids["media_photo2_sl"],
                            ],
                        },
                    },
                    "beta": {
                        "en": {"title": "Beta rc1", "summary": "Beta povz en"},
                        "sl-SI": {"title": "Beta rc1", "summary": "Beta povz"},
                    },
                }
                for slug, locales in translations_expected.items():
                    for locale, localized_values in locales.items():
                        await agent_record(
                            f"/api/agent/v1/content-items/{ids[f'item_{slug}']}"
                            "/translations",
                            {
                                "locale": locale,
                                "localized_values": localized_values,
                            },
                            f"translation-{slug}-{locale}",
                        )
                relation = await agent_record(
                    f"/api/agent/v1/content-items/{ids['item_alpha']}/relations",
                    {
                        "field_definition_id": ids["field_related"],
                        "target_item_id": ids["item_beta"],
                        "position": 0,
                        "metadata": {"note": "retained"},
                    },
                    "relation",
                )
                ids["relation"] = relation["id"]

                # ---- Agent surface: full view spec (F3: MEANINGFUL
                # supported filter, real query DSL: status PUBLISHED AND
                # rank >= 2, so gamma (DRAFT, rank 1) is excluded by a
                # real content effect; projection is non-localized only,
                # which the actual contract requires).
                view_a_spec = {
                    "filter_spec": {
                        "and": [
                            {"status": "PUBLISHED"},
                            {"field": "rank", "op": "gte", "value": 2},
                        ]
                    },
                    "sort_spec": {"field": "rank", "direction": "desc"},
                    "projection_spec": {"fields": ["rank", "ratio"]},
                    "pagination_spec": {"limit": 10, "offset": 0},
                }
                view = await agent_record(
                    f"/api/agent/v1/collection-views/types/{ids['type_a']}",
                    {
                        "type_id": ids["type_a"],
                        "key": f"rc1view_{tag}",
                        **view_a_spec,
                    },
                    "view",
                )
                ids["view"] = view["id"]

                # ---- Agent surface: pages + composition
                home = await agent_record(
                    "/api/agent/v1/pages",
                    {"slug": "home", "title": "RC1 home", "status": "PUBLISHED"},
                    "page-home",
                )
                news = await agent_record(
                    "/api/agent/v1/pages",
                    {
                        "slug": "rc1news",
                        "title": "RC1 news",
                        "status": "PUBLISHED",
                        "parent_id": home["id"],
                    },
                    "page-news",
                )
                detail = await agent_record(
                    "/api/agent/v1/pages",
                    {
                        "slug": "rc1item",
                        "title": "RC1 item",
                        "status": "PUBLISHED",
                        "parent_id": news["id"],
                        "route_template": "{slug}",
                    },
                    "page-detail",
                )
                # F5: the deleted-record retention row - created through
                # the public API, deleted through the public API, and the
                # tombstone must be retained in the frozen payload.
                gone = await agent_record(
                    "/api/agent/v1/pages",
                    {
                        "slug": "rc1gone",
                        "title": "RC1 gone",
                        "status": "PUBLISHED",
                        "parent_id": home["id"],
                    },
                    "page-gone",
                )
                ids["page_home"] = home["id"]
                ids["page_news"] = news["id"]
                ids["page_detail"] = detail["id"]
                ids["page_gone"] = gone["id"]

                async def component(
                    page_id: str,
                    component_type: str,
                    props: dict[str, Any],
                ) -> None:
                    resp = await ag.post(
                        f"/api/agent/v1/pages/{page_id}/components",
                        headers={**ah, **agent_idem(component_type)},
                        json={
                            "component_type": component_type,
                            "slot_key": "default",
                            "props": props,
                        },
                    )
                    assert resp.status_code == 201, resp.text

                for page_id, component_type in (
                    (ids["page_home"], "CollectionSearch"),
                    (ids["page_news"], "CollectionList"),
                    (ids["page_detail"], "CollectionDetail"),
                    (ids["page_detail"], "RelatedItems"),
                ):
                    await component(page_id, component_type, {"viewId": ids["view"]})
                # G5: the SELECTED typed media references - the Image
                # component (top-level mediaId) and the DocumentList
                # component (declared array-item mediaId) - use the
                # COMPONENT-referenced assets (distinct from the field-
                # only assets); these are the real supported reference
                # positions the 076 closure walks.
                await component(
                    ids["page_home"],
                    "Image",
                    {"mediaId": ids["media_img"], "alt": "RC1 photo"},
                )
                await component(
                    ids["page_news"],
                    "DocumentList",
                    {
                        "items": [
                            {
                                "mediaId": ids["media_pdf_comp"],
                                "label": "RC1 document",
                            }
                        ]
                    },
                )

                # ---- Agent surface: non-default page style (L3 scope)
                style_get = await ag.get(
                    f"/api/agent/v1/pages/{ids['page_news']}/style", headers=ah
                )
                assert style_get.status_code == 200, style_get.text
                style_row_version = style_get.json()["row_version"]
                style_patch = await ag.patch(
                    f"/api/agent/v1/pages/{ids['page_news']}/style",
                    headers={**ah, **agent_idem("style")},
                    json={
                        "layout": {"content_width": "xl"},
                        "expected_row_version": style_row_version,
                    },
                )
                assert style_patch.status_code == 200, style_patch.text
                assert style_patch.json()["record"]["overrides"] == {
                    "layout": {"content_width": "xl"}
                }

                # ---- Agent surface: theme (L4 theme-global:write)
                theme_get = await ag.get("/api/agent/v1/theme", headers=ah)
                assert theme_get.status_code == 200, theme_get.text
                theme_row_version = theme_get.json()["row_version"]
                theme_patch = await ag.patch(
                    "/api/agent/v1/theme",
                    headers={**ah, **agent_idem("theme")},
                    json={
                        "typography": {"family": "mono"},
                        "expected_row_version": theme_row_version,
                    },
                )
                assert theme_patch.status_code == 200, theme_patch.text
                assert theme_patch.json()["record"]["typography"]["family"] == "mono"

                # ---- Agent surface: locale (L4 locale:configure)
                locale_rows = (await ag.get("/api/agent/v1/locales", headers=ah)).json()
                sl_locale = next(row for row in locale_rows if row["tag"] == "sl-SI")
                locale_patch = await ag.patch(
                    f"/api/agent/v1/locales/{sl_locale['id']}",
                    headers={**ah, **agent_idem("locale")},
                    json={
                        "metadata": {"note": "rc1-agent-locale"},
                        "expected_row_version": sl_locale["row_version"],
                    },
                )
                assert locale_patch.status_code == 200, locale_patch.text

                # ---- Agent surface: redirect (L2)
                redirect = await agent_record(
                    "/api/agent/v1/redirects",
                    {
                        "source_route": f"/rc1old-{tag}",
                        "target": "/rc1news",
                        "status_code": 301,
                    },
                    "redirect",
                )
                ids["redirect"] = redirect["id"]

                # ---- Agent surface: navigation + item (L2)
                nav = await agent_record(
                    "/api/agent/v1/navigation",
                    {"key": "main", "label": "RC1 main"},
                    "navigation",
                )
                nav_item = await agent_record(
                    f"/api/agent/v1/navigation/{nav['id']}/items",
                    {
                        "navigation_id": nav["id"],
                        "target_kind": "INTERNAL",
                        "target_value": "/rc1news",
                        "labels": {"en": "News"},
                    },
                    "nav-item",
                )
                ids["nav"] = nav["id"]
                ids["nav_item"] = nav_item["id"]

                # ---- Agent surface: global-region variant (L4)
                region_rows = (
                    await ag.get("/api/agent/v1/global-regions", headers=ah)
                ).json()
                region_row = next(
                    row for row in region_rows if row["id"] == str(seeded["region_id"])
                )
                region_patch = await ag.patch(
                    f"/api/agent/v1/global-regions/{seeded['region_id']}",
                    headers={**ah, **agent_idem("region")},
                    json={
                        "variant": "minimal",
                        "expected_row_version": region_row["row_version"],
                    },
                )
                assert region_patch.status_code == 200, region_patch.text
                assert region_patch.json()["record"]["variant"] == "minimal"

                # ---- F5: PUBLIC page deletion (tombstone retained)
                gone_get = await ag.get(
                    f"/api/agent/v1/pages/{ids['page_gone']}", headers=ah
                )
                assert gone_get.status_code == 200, gone_get.text
                gone_delete = await ag.request(
                    "DELETE",
                    f"/api/agent/v1/pages/{ids['page_gone']}",
                    headers={**ah, **agent_idem("page-delete")},
                    json={"expected_row_version": gone_get.json()["row_version"]},
                )
                assert gone_delete.status_code == 200, gone_delete.text

            # ---- Editor surface: the SAME named operations through the
            # 069_001 envelope into the SAME candidate workspace.
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=editor_app),
                base_url="http://editor.test",
            ) as ed:
                site = str(seeded["site_id"])
                base = f"/api/editor/v1/sites/{site}"

                async def ed_record(
                    path: str, body: dict[str, Any], op: str
                ) -> dict[str, Any]:
                    resp = await ed.post(
                        path,
                        headers=editor_headers(idempotency=f"rc1-{tag}-{op}"),
                        json=body,
                    )
                    assert resp.status_code == 201, resp.text
                    record: dict[str, Any] = resp.json()
                    return record

                # Editor model/field (content-model:create / field-def).
                # F1: type_b carries a typed document field (base value)
                # beside the localized title + reference field; brief
                # adds the BASE scalar document field so the complete
                # finite document shape map is covered.
                type_b = await ed_record(
                    f"{base}/content-model/types",
                    {
                        "key": f"rc1_press_{tag}",
                        "labels": {"en": "RC1 press"},
                        "slug_pattern": f"/rc1press/{tag}/{{slug}}",
                        "settings": {},
                    },
                    "ed-type",
                )
                ids["type_b"] = type_b["id"]
                # G5: doc is a MULTI-value (cardinality 2) non-localized
                # document field (base array branch), brief is the BASE
                # scalar document field and summary_doc is the localized
                # scalar document field (localized scalar branch) -
                # together they cover the complete document-field
                # closure shape map.
                for (
                    key,
                    prim,
                    required,
                    localized,
                    position,
                    cardinality,
                ) in (
                    ("title", "short_text", True, True, 0, 1),
                    ("doc", "document", False, False, 1, 2),
                    ("summary_doc", "document", False, True, 2, 1),
                    ("brief", "document", False, False, 3, 1),
                    ("related", "reference", False, False, 4, 1),
                ):
                    field = await ed_record(
                        f"{base}/content-model/types/{type_b['id']}/fields",
                        {
                            "key": key,
                            "label": key.title(),
                            "field_type": prim,
                            "required": required,
                            "localized": localized,
                            "cardinality": cardinality,
                            "position": position,
                            "validation": (
                                {"target_type_id": type_b["id"]}
                                if key == "related"
                                else {}
                            ),
                        },
                        f"ed-field-{key}",
                    )
                    ids[f"ed_field_{key}"] = field["id"]
                # Editor items + translation + relation (same workspace).
                # G5: pressone's BASE document field value is a MULTI
                # array (cardinality 2) of FIELD-ONLY DOCUMENT assets
                # (distinct from the DocumentList component reference).
                press_one = await ed_record(
                    f"{base}/content-items/",
                    {
                        "type_id": type_b["id"],
                        "slug": "pressone",
                        "status": "PUBLISHED",
                        "values": {
                            "doc": [
                                ids["media_pdf_doc"],
                                ids["media_pdf_doc2"],
                            ],
                            # G5: the BASE scalar document field value.
                            "brief": ids["media_doc_base"],
                        },
                    },
                    "ed-item-1",
                )
                press_two = await ed_record(
                    f"{base}/content-items/",
                    {
                        "type_id": type_b["id"],
                        "slug": "presstwo",
                        "status": "PUBLISHED",
                        "values": {},
                    },
                    "ed-item-2",
                )
                ids["ed_item_one"] = press_one["id"]
                ids["ed_item_two"] = press_two["id"]
                await ed_record(
                    f"{base}/content-items/{press_one['id']}/translations",
                    {
                        "locale": "en",
                        "localized_values": {"title": "Press one"},
                    },
                    "ed-trans-one-en",
                )
                await ed_record(
                    f"{base}/content-items/{press_one['id']}/translations",
                    {
                        "locale": "sl-SI",
                        "localized_values": {
                            "title": "Tiskovna ena",
                            # G5: the LOCALIZED scalar document field.
                            "summary_doc": ids["media_doc_sl"],
                        },
                    },
                    "ed-trans-one-sl",
                )
                await ed_record(
                    f"{base}/content-items/{press_two['id']}/translations",
                    {
                        "locale": "en",
                        "localized_values": {"title": "Press two"},
                    },
                    "ed-trans-two-en",
                )
                await ed_record(
                    f"{base}/content-items/{press_one['id']}/relations",
                    {
                        "field_definition_id": ids["ed_field_related"],
                        "target_item_id": press_two["id"],
                        "position": 0,
                        "metadata": {},
                    },
                    "ed-relation",
                )
                # Editor view (full spec, distinct from the Agent view;
                # F3: its own meaningful supported filter).
                view_b_spec = {
                    "filter_spec": {"status": "PUBLISHED"},
                    "sort_spec": {"field": "slug", "direction": "asc"},
                    "projection_spec": {"fields": []},
                    "pagination_spec": {"limit": 5, "offset": 0},
                }
                ed_view = await ed_record(
                    f"{base}/collection-views/types/{type_b['id']}",
                    {
                        "type_id": type_b["id"],
                        "key": f"rc1edview_{tag}",
                        **view_b_spec,
                    },
                    "ed-view",
                )
                ids["ed_view"] = ed_view["id"]
                # Editor page + component.
                ed_page = await ed_record(
                    f"{base}/pages/",
                    {"slug": "rc1press", "title": "RC1 press", "status": "PUBLISHED"},
                    "ed-page",
                )
                ids["ed_page"] = ed_page["id"]
                ed_component = await ed.post(
                    f"{base}/pages/{ed_page['id']}/composition/components",
                    headers=editor_headers(idempotency=f"rc1-{tag}-ed-comp"),
                    json={
                        "component_type": "CollectionList",
                        "slot_key": "default",
                        "props": {"viewId": ed_view["id"]},
                    },
                )
                assert ed_component.status_code == 201, ed_component.text
                # Idempotency replay: byte-identical stored response.
                ed_component_replay = await ed.post(
                    f"{base}/pages/{ed_page['id']}/composition/components",
                    headers=editor_headers(idempotency=f"rc1-{tag}-ed-comp"),
                    json={
                        "component_type": "CollectionList",
                        "slot_key": "default",
                        "props": {"viewId": ed_view["id"]},
                    },
                )
                assert ed_component_replay.status_code == 201
                assert ed_component_replay.json() == ed_component.json()
                # Editor page style (distinct page + distinct token).
                ed_style_get = await ed.get(
                    f"{base}/pages/{ed_page['id']}/style",
                    headers=editor_headers(),
                )
                assert ed_style_get.status_code == 200, ed_style_get.text
                ed_style_patch = await ed.patch(
                    f"{base}/pages/{ed_page['id']}/style",
                    headers=editor_headers(idempotency=f"rc1-{tag}-ed-style"),
                    json={
                        "layout": {"content_width": "sm"},
                        "expected_row_version": ed_style_get.json()["row_version"],
                    },
                )
                assert ed_style_patch.status_code == 200, ed_style_patch.text
                # Editor theme (distinct token: palette).
                ed_theme_get = await ed.get(f"{base}/theme", headers=editor_headers())
                assert ed_theme_get.status_code == 200, ed_theme_get.text
                # The human Editor theme surface takes NO optimistic
                # version token (only the Agent surface adds
                # expected_row_version); the GET keeps the real
                # read-back record.
                ed_theme_patch = await ed.patch(
                    f"{base}/theme",
                    headers=editor_headers(idempotency=f"rc1-{tag}-ed-theme"),
                    json={"palette": {"preset": "ember"}},
                )
                assert ed_theme_patch.status_code == 200, ed_theme_patch.text
                # Editor media metadata (uploads are Agent-only; the
                # authorized human mutation here is the real Editor
                # media PATCH on the same workspace asset).
                ed_media_patch = await ed.patch(
                    f"{base}/media/{ids['media_img']}",
                    headers=editor_headers(idempotency=f"rc1-{tag}-ed-media"),
                    json={"alt_text": "RC1 photo (reviewed)"},
                )
                assert ed_media_patch.status_code == 200, ed_media_patch.text

        # ---- HUMAN audit + canonical isolation for the Editor surface.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            audit = await owner.fetch(
                "SELECT * FROM audit.human_editor_mutation"
                " WHERE workspace_id = $1"
                " ORDER BY occurred_at, operation_id",
                seeded["workspace_id"],
            )
            assert len(audit) >= 12, len(audit)
            assert {str(row["human_user_id"]) for row in audit} == {
                str(seeded["delegator_id"])
            }
            canonical_types = await owner.fetchval(
                "SELECT count(*) FROM content.content_type_base WHERE site_id = $1",
                seeded["site_id"],
            )
            assert canonical_types == 0, "canonical base must stay untouched"
            # Logical isolation: with the workspace session bound, the
            # COW view (base + this workspace's changes) shows EXACTLY
            # the two candidate types created on the two surfaces and
            # nothing else workspace-visible.  The foundation's
            # append-history row count in content_type_changes mirrors
            # per-operation version storage; it is NOT the logical
            # criterion and is deliberately not asserted.  Exact public
            # version pins for both types are the read-back results
            # below (observed["type_a"]/observed["ed_type_b"]), pinned
            # into the frozen payload.
            await owner.execute(
                "SELECT set_config('app.session_id', $1::text, false)",
                str(seeded["workspace_id"]),
            )
            try:
                visible_types = await owner.fetch(
                    "SELECT id FROM content.content_type WHERE site_id = $1",
                    seeded["site_id"],
                )
            finally:
                await owner.execute("SELECT set_config('app.session_id', '', false)")
            assert {str(row["id"]) for row in visible_types} == {
                str(ids["type_a"]),
                str(ids["type_b"]),
            }
            assert len(visible_types) == 2, len(visible_types)

        # ================= F3: public version read-back (BOTH surfaces)
        # Every mutation is complete.  These live public GETs (Agent
        # capability surface AND the 069_001 authorized human Editor
        # surface) read the candidate rows back BEFORE the freeze pins
        # them; the retained payload values are pinned to these ACTUAL
        # read results below (no self-referential expected maps).  The
        # Agent app pool re-opens under a fresh lifespan context for the
        # read-back.
        observed: dict[str, Any] = {}
        ah = {"Authorization": f"Bearer {seeded['capability_token']}"}
        async with agent_app.router.lifespan_context(agent_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=agent_app),
                base_url="http://agent.test",
            ) as ag:

                async def ag_get(path: str) -> Any:
                    resp = await ag.get(path, headers=ah)
                    assert resp.status_code == 200, resp.text
                    return resp.json()

                observed["type_a"] = await ag_get(
                    f"/api/agent/v1/content-model/types/{ids['type_a']}"
                )
                observed["type_a_fields"] = await ag_get(
                    f"/api/agent/v1/content-model/types/{ids['type_a']}/fields"
                )
                observed["type_b"] = await ag_get(
                    f"/api/agent/v1/content-model/types/{ids['type_b']}"
                )
                observed["type_b_fields"] = await ag_get(
                    f"/api/agent/v1/content-model/types/{ids['type_b']}/fields"
                )
                for slug in ("alpha", "beta", "gamma"):
                    observed[f"item_{slug}"] = await ag_get(
                        f"/api/agent/v1/content-items/{ids[f'item_{slug}']}"
                    )
                observed["translations_alpha"] = await ag_get(
                    f"/api/agent/v1/content-items/{ids['item_alpha']}/translations"
                )
                observed["translations_beta"] = await ag_get(
                    f"/api/agent/v1/content-items/{ids['item_beta']}/translations"
                )
                observed["view_a"] = await ag_get(
                    f"/api/agent/v1/collection-views/{ids['view']}"
                )
                observed["view_b"] = await ag_get(
                    f"/api/agent/v1/collection-views/{ids['ed_view']}"
                )
                observed["locales"] = await ag_get("/api/agent/v1/locales")
                observed["nav"] = await ag_get(f"/api/agent/v1/navigation/{ids['nav']}")
                observed["nav_item"] = await ag_get(
                    f"/api/agent/v1/navigation-items/{ids['nav_item']}"
                )
                observed["redirect"] = await ag_get(
                    f"/api/agent/v1/redirects/{ids['redirect']}"
                )

        site = str(seeded["site_id"])
        base = f"/api/editor/v1/sites/{site}"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=editor_app),
            base_url="http://editor.test",
        ) as ed:

            async def ed_get(path: str) -> Any:
                resp = await ed.get(path, headers=editor_headers())
                assert resp.status_code == 200, resp.text
                return resp.json()

            observed["ed_type_b"] = await ed_get(
                f"{base}/content-model/types/{ids['type_b']}"
            )
            observed["ed_type_b_fields"] = await ed_get(
                f"{base}/content-model/types/{ids['type_b']}/fields"
            )
            for label, key in (("one", "ed_item_one"), ("two", "ed_item_two")):
                observed[f"ed_item_{label}"] = await ed_get(
                    f"{base}/content-items/{ids[key]}"
                )
            observed["ed_trans_one"] = await ed_get(
                f"{base}/content-items/{ids['ed_item_one']}/translations"
            )
            observed["ed_trans_two"] = await ed_get(
                f"{base}/content-items/{ids['ed_item_two']}/translations"
            )
            observed["ed_view_b"] = await ed_get(
                f"{base}/collection-views/{ids['ed_view']}"
            )

        # Cross-surface pin: BOTH surfaces read the SAME workspace rows,
        # so their public records agree on the versioned fields.
        assert (
            observed["type_b"]["definition_version"]
            == observed["ed_type_b"]["definition_version"]
        )
        assert (
            observed["view_b"]["definition_version"]
            == observed["ed_view_b"]["definition_version"]
        )
        assert observed["view_b"]["row_version"] == observed["ed_view_b"]["row_version"]
        assert (
            observed["ed_item_one"]["type_definition_version"]
            == observed["ed_type_b"]["definition_version"]
        )

        # ================= Real freeze (narrow-credential worker) =====
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            revision_before_freeze = int(
                await owner.fetchval(
                    "SELECT canonical_revision FROM control.site WHERE id = $1",
                    seeded["site_id"],
                )
            )
        pool = await _worker_pool(database)
        freeze_result, freeze_job_id = await _freeze_claim_run(
            database,
            workspace_id=seeded["workspace_id"],
            site_id=seeded["site_id"],
            delegator_id=seeded["delegator_id"],
            pool=pool,
            claimant=f"rc1-freeze-{tag}",
        )
        assert freeze_result.status == "SUCCEEDED", freeze_result
        snapshot = await _snapshot_row(database, seeded["workspace_id"])
        assert snapshot is not None
        assert set(snapshot.keys()) == RC1_SNAPSHOT_ROW_KEYS
        assert str(snapshot["workspace_id"]) == str(seeded["workspace_id"])
        assert str(snapshot["site_id"]) == str(seeded["site_id"])
        assert str(snapshot["status"]) == "COMPLETE"
        # Real contract: run_freeze_job records the claiming worker's
        # job identity (claimed_by) as the snapshot's created_by, per
        # freeze_job.py and the review_snapshot_created_by_shape
        # constraint. This asserts the narrow-credential worker that
        # actually claimed + ran this freeze, not a human/delegator.
        assert str(snapshot["created_by"]) == f"rc1-freeze-{tag}"

        # ============ READ-BOUNDARY: the immutable stored v2 row ======
        # asyncpg jsonb binding over the owner connection delivers
        # canonical JSON text; decode for asserts (the target file
        # documents the same pattern at its first snapshot read).
        def j(value: Any) -> Any:
            return json.loads(value) if isinstance(value, str) else value

        payload = j(snapshot["payload"])
        assert isinstance(payload, dict)
        normalized_state = j(snapshot["normalized_state"])
        row_versions = j(snapshot["versions"])
        assert set(payload) == RC1_PAYLOAD_KEYS
        assert payload["state_version"] == "review-snapshot/v2"
        assert str(payload["workspace_id"]) == str(seeded["workspace_id"])
        assert str(payload["site_id"]) == str(seeded["site_id"])
        assert payload["base_site_revision"] == revision_before_freeze
        assert isinstance(payload["operation_watermark"], int)
        assert payload["operation_watermark"] >= 0
        # The trusted six-pin set: workspace-creation facts on the row
        # AND in the payload, with the exact expected content.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            ws_version_facts = await owner.fetchval(
                "SELECT version_facts FROM control.workspace WHERE id = $1",
                seeded["workspace_id"],
            )
        assert payload["workspace_versions"] == j(ws_version_facts)
        assert row_versions == j(ws_version_facts)
        assert j(ws_version_facts) == {
            "catalog": "catalog-v1",
            "composition_schema": "site-composition/v1",
            "content_model": "content-model/v1",
            "design_system": "design-system/v1",
            "puck": "0.20.2",
            "renderer": "renderer-v1",
        }
        # Digest recomputes exactly over the canonical payload text; the
        # normalized state is canonically identical to the payload.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            canonical_text = await owner.fetchval(
                "SELECT control.slaif_canonical_jsonb_text($1::jsonb)",
                json.dumps(payload),
            )
        assert canonical_text is not None
        assert (
            snapshot["digest"]
            == hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
        )
        assert normalized_state == payload
        # F2: the FULL numeric map keeps its exact raw canonical digits
        # in the stored payload (no vacuous `or True`; the qualified
        # 23-digit exact-vector capture/read proof is the existing
        # coverage in test_review_endpoint_frozen_read_media_urls_and_
        # role_denials (exact-number section, line ~4237 onward) and is
        # NOT re-invented here).
        for raw in (
            '"rank":42',
            '"ratio":0.1',
            '"ratio":3.75',
            '"rank":7',
            '"ratio":1.5',
            '"rank":1',
        ):
            assert raw in canonical_text, raw
        validation_report = j(snapshot["validation_report"])
        assert set(validation_report) == RC1_VALIDATION_REPORT_KEYS
        assert validation_report["state_version"] == "review-snapshot/v2"
        assert validation_report["errors"] == []
        assert validation_report["pages_validated"] == 5
        assert validation_report["cancelled_by_freeze"] == []
        # Honest: RC1 seeds NO browser run, so the evidence list is
        # empty.  The NON-EMPTY selected-completed evidence binding is
        # existing qualified coverage (freeze_job evidence ingestion of
        # claimed terminal runs; the nonempty legacy cases at
        # test_freeze_review_snapshot.py lines ~5618/5629/5893) with the
        # RC4 actual-worker proof as runtime owner.
        assert j(snapshot["browser_evidence"]) == []
        # F4: the captured site profile (exact values) and the live
        # control row (the freeze itself changes no canonical state).
        assert set(payload["site"]) == RC1_SITE_PROFILE_KEYS
        assert payload["site"]["site_key"] == site_key
        assert payload["site"]["display_name"] == "Rc1 Int"
        assert payload["site"]["status"] == "ACTIVE"
        assert payload["site"]["default_locale"] == "en"
        assert payload["site"]["component_catalog_version"] == "catalog-v1"
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            site_row = await owner.fetchrow(
                "SELECT * FROM control.site WHERE id = $1", seeded["site_id"]
            )
        assert int(site_row["canonical_revision"]) == revision_before_freeze
        assert payload["site"]["content_model_revision"] == int(
            site_row["content_model_revision"]
        )
        assert isinstance(payload["site"]["created_at"], str)
        assert isinstance(payload["site"]["updated_at"], str)

        # ---- F1/G5: selected typed media closure (sibling shapes) ----
        # media_references is a LIST (sorted by id) of five-key refs;
        # payload media is a DICT keyed by id; both directions match
        # entry-for-entry (the frozen admission re-checks list length
        # equals map length - the same-shape consumer proof).
        media_references = j(snapshot["media_references"])
        media_map = payload["media"]
        assert isinstance(media_references, list)
        assert isinstance(media_map, dict)
        selected_ids = {
            str(ids[k])
            for k in (
                "media_img",
                "media_pdf_comp",
                "media_photo_en",
                "media_photo2_en",
                "media_photo_sl",
                "media_photo2_sl",
                "media_cover",
                "media_pdf_doc",
                "media_pdf_doc2",
                "media_doc_base",
                "media_doc_sl",
            )
        }
        # G5: the selected set is EXACTLY the eleven distinct typed
        # references (two component + nine field-only covering the
        # complete finite shape map); the unrelated private upload is
        # retained in the inventory (below) but excluded from the
        # closure.
        assert {ref["id"] for ref in media_references} == selected_ids
        assert [ref["id"] for ref in media_references] == sorted(selected_ids)
        for ref in media_references:
            assert set(ref) == RC1_MEDIA_REFERENCE_KEYS
            entry = media_map[ref["id"]]
            assert set(entry) == RC1_MEDIA_ENTRY_KEYS
            for key in (
                "id",
                "mime_type",
                "size_bytes",
                "content_hash",
                "public_status",
            ):
                assert entry[key] == ref[key], (key, ref, entry)
        expected_media: dict[str, tuple[str, int, str]] = {
            str(ids["media_img"]): ("image/png", len(RC1_PNG_BYTES), png_hash),
            str(ids["media_pdf_comp"]): (
                "application/pdf",
                len(RC1_PDF_BYTES),
                pdf_hash,
            ),
            str(ids["media_photo_en"]): (
                "image/png",
                len(RC1_PNG2_BYTES),
                png2_hash,
            ),
            str(ids["media_photo2_en"]): (
                "image/png",
                len(RC1_PNG4_BYTES),
                png4_hash,
            ),
            str(ids["media_photo_sl"]): (
                "image/png",
                len(RC1_PNG3_BYTES),
                png3_hash,
            ),
            str(ids["media_photo2_sl"]): (
                "image/png",
                len(RC1_PNG5_BYTES),
                png5_hash,
            ),
            str(ids["media_pdf_doc"]): (
                "application/pdf",
                len(RC1_PDF3_BYTES),
                pdf3_hash,
            ),
            str(ids["media_pdf_doc2"]): (
                "application/pdf",
                len(RC1_PDF4_BYTES),
                pdf4_hash,
            ),
            str(ids["media_cover"]): (
                "image/png",
                len(RC1_PNG6_BYTES),
                png6_hash,
            ),
            str(ids["media_doc_base"]): (
                "application/pdf",
                len(RC1_PDF5_BYTES),
                pdf5_hash,
            ),
            str(ids["media_doc_sl"]): (
                "application/pdf",
                len(RC1_PDF6_BYTES),
                pdf6_hash,
            ),
        }
        for media_id, (mime, size, content_hash) in expected_media.items():
            entry = media_map[media_id]
            assert entry["mime_type"] == mime
            assert entry["size_bytes"] == size
            assert entry["content_hash"] == content_hash
            assert entry["public_status"] == "private"

        # ---- G5 consumer positives: the FIELD-ONLY assets resolve ----
        # through the trusted frozen consumer from the STORED frozen
        # media map.  A materializer that omitted the field-closure
        # branch - or any scalar/multi-value, base/localized variant -
        # would not store that shape's field-only asset and these nine
        # distinct positive resolves would break; the component-
        # referenced assets are proven separately through the projection
        # media URLs below.
        from slaif_agent_site.render_api import frozen_source as _fs

        decoded_row = dict(snapshot)
        for key in (
            "versions",
            "normalized_state",
            "validation_report",
            "media_references",
            "browser_evidence",
            "payload",
        ):
            decoded_row[key] = j(decoded_row[key])
        surface = _fs.FrozenRenderSurface(
            decoded_row,
            expected_snapshot_id=snapshot["id"],
            expected_site_id=seeded["site_id"],
            expected_workspace_id=seeded["workspace_id"],
        )
        for media_id, (mime, size, content_hash) in expected_media.items():
            row = await surface.resolve_media(
                site_id=seeded["site_id"], media_id=UUID(media_id)
            )
            assert row is not None, media_id
            assert tuple(row) == (mime, size, content_hash, "private"), media_id
        # The unrelated private asset is NOT in the frozen map: the
        # frozen surface cannot resolve it even though the inventory
        # retains it (no public/frozen leak).
        assert (
            await surface.resolve_media(
                site_id=seeded["site_id"],
                media_id=UUID(str(ids["media_pdf_unrelated"])),
            )
            is None
        )

        # ---- Frozen common-consumer positive re-derivation ----------
        positive = await _rc1_frozen_positive(
            database,
            decoded_row,
            site_id=seeded["site_id"],
            workspace_id=seeded["workspace_id"],
        )
        # The real view filter (status PUBLISHED AND rank >= 2) excludes
        # gamma (DRAFT, rank 1) by an actual content effect; sort is
        # rank desc.  The press view (status PUBLISHED, slug asc) lists
        # both editor items.
        assert positive["news_list_slugs"] == ["alpha", "beta"]
        assert positive["news_list_ranks"] == [42, 7]
        assert positive["press_list_slugs"] == ["pressone", "presstwo"]
        # Real contract: the detail route resolves to the detail PAGE
        # (rc1item); the addressed item slug is the route parameter.
        assert positive["detail_slug"] == "rc1item"
        assert positive["detail_page_id"] == str(ids["page_detail"])
        assert positive["detail_route_parameters"] == {"slug": "alpha"}
        assert positive["detail_related_slugs"] == ["beta"]
        snapshot_url = f"/media/v1/review/{snapshot['id']}/assets"
        # Component-referenced assets render through the component
        # reference branch (distinct from the field-only assets above).
        assert positive["home_image_media"] == {
            "url": f"{snapshot_url}/{ids['media_img']}/content",
            "mime_type": "image/png",
            "size_bytes": len(RC1_PNG_BYTES),
        }
        assert positive["news_doclist_items"] == [
            {
                "url": f"{snapshot_url}/{ids['media_pdf_comp']}/content",
                "mime_type": "application/pdf",
                "size_bytes": len(RC1_PDF_BYTES),
            }
        ]

        # ================== the explicit sixteen-family map ==========
        content = payload["content"]
        assert set(content) == RC1_CONTENT_KEYS
        # ---- types (BOTH surfaces) ----
        assert len(content["types"]) == 2
        assert all(set(row) == RC1_TYPE_KEYS for row in content["types"])
        type_a_row = next(
            row for row in content["types"] if row["key"] == f"rc1_news_{tag}"
        )
        type_b_row = next(
            row for row in content["types"] if row["key"] == f"rc1_press_{tag}"
        )
        assert type_a_row["id"] == str(ids["type_a"])
        assert type_a_row["site_id"] == str(seeded["site_id"])
        assert type_a_row["labels"] == {"en": "RC1 news"}
        assert type_a_row["slug_pattern"] == f"/rc1news/{tag}/{{slug}}"
        assert type_a_row["status"] == "ACTIVE"
        assert type_a_row["settings"] == {}
        assert (
            type_a_row["definition_version"] == observed["type_a"]["definition_version"]
        )
        assert type_b_row["id"] == str(ids["type_b"])
        assert type_b_row["labels"] == {"en": "RC1 press"}
        assert type_b_row["slug_pattern"] == f"/rc1press/{tag}/{{slug}}"
        assert type_b_row["status"] == "ACTIVE"
        assert type_b_row["settings"] == {}
        assert (
            type_b_row["definition_version"]
            == observed["ed_type_b"]["definition_version"]
        )
        # ---- fields (BOTH surfaces; per-key domain values + the
        # ACTUAL public read-back version pins) ----
        field_a_rows = [
            row for row in content["fields"] if row["type_id"] == str(ids["type_a"])
        ]
        field_b_rows = [
            row for row in content["fields"] if row["type_id"] == str(ids["type_b"])
        ]
        assert len(field_a_rows) == 8 and len(field_b_rows) == 5
        assert all(set(row) == RC1_FIELD_KEYS for row in content["fields"])
        expected_a_fields = {
            "title": ("short_text", True, True, 0, {}, 1),
            "summary": ("long_text", False, True, 1, {}, 1),
            "rank": ("integer", True, False, 2, {}, 1),
            "ratio": ("decimal", True, False, 3, {}, 1),
            # G5: photo is a MULTI-value (cardinality 2) localized
            # media field.
            "photo": ("media", False, True, 4, {}, 2),
            # G5: cover is the BASE scalar media field.
            "cover": ("media", False, False, 5, {}, 1),
            # G5: gallery is the BASE MULTI media field.
            "gallery": ("media", False, False, 6, {}, 2),
            "related": (
                "reference",
                False,
                False,
                7,
                {"target_type_id": str(ids["type_a"])},
                1,
            ),
        }
        observed_a_fields = {row["key"]: row for row in observed["type_a_fields"]}
        for row in field_a_rows:
            (
                prim,
                required,
                localized,
                position,
                validation,
                cardinality,
            ) = expected_a_fields[row["key"]]
            assert row["field_type"] == prim
            assert row["required"] is required
            assert row["localized"] is localized
            assert row["position"] == position
            assert row["cardinality"] == cardinality
            assert row["validation"] == validation
            assert row["label"] == row["key"].title()
            observed_row = observed_a_fields[row["key"]]
            assert row["id"] == observed_row["id"]
            assert row["definition_version"] == observed_row["definition_version"]
        expected_b_fields = {
            "title": ("short_text", True, True, 0, {}, 1),
            # G5: doc is a MULTI-value (cardinality 2) document field.
            "doc": ("document", False, False, 1, {}, 2),
            # G5: summary_doc is the localized scalar document field.
            "summary_doc": ("document", False, True, 2, {}, 1),
            # G5: brief is the BASE scalar document field.
            "brief": ("document", False, False, 3, {}, 1),
            "related": (
                "reference",
                False,
                False,
                4,
                {"target_type_id": str(ids["type_b"])},
                1,
            ),
        }
        observed_b_fields = {row["key"]: row for row in observed["ed_type_b_fields"]}
        for row in field_b_rows:
            (
                prim,
                required,
                localized,
                position,
                validation,
                cardinality,
            ) = expected_b_fields[row["key"]]
            assert row["field_type"] == prim
            assert row["required"] is required
            assert row["localized"] is localized
            assert row["position"] == position
            assert row["cardinality"] == cardinality
            assert row["validation"] == validation
            observed_row = observed_b_fields[row["key"]]
            assert row["id"] == observed_row["id"]
            assert row["definition_version"] == observed_row["definition_version"]
        # ---- items (exact values; G5 field-only references; F5 DRAFT)
        assert len(content["items"]) == 5
        assert all(set(row) == RC1_ITEM_KEYS for row in content["items"])
        items_by_slug = {row["slug"]: row for row in content["items"]}
        assert set(items_by_slug) == {
            "alpha",
            "beta",
            "gamma",
            "pressone",
            "presstwo",
        }
        alpha_row = items_by_slug["alpha"]
        assert alpha_row["status"] == "PUBLISHED"
        assert alpha_row["type_id"] == str(ids["type_a"])
        # F2: the exact raw numbers stay in the BASE values; G5: the
        # BASE media MULTI + scalar field values are FIELD-ONLY assets.
        assert alpha_row["values"] == {
            "rank": 42,
            "ratio": 0.1,
            "gallery": [
                str(ids["media_photo_en"]),
                str(ids["media_photo2_en"]),
            ],
            "cover": str(ids["media_cover"]),
        }
        assert alpha_row["row_version"] == observed["item_alpha"]["row_version"]
        assert (
            alpha_row["type_definition_version"]
            == observed["type_a"]["definition_version"]
        )
        beta_row = items_by_slug["beta"]
        assert beta_row["status"] == "PUBLISHED"
        assert beta_row["values"] == {"rank": 7, "ratio": 1.5}
        assert beta_row["row_version"] == observed["item_beta"]["row_version"]
        gamma_row = items_by_slug["gamma"]
        # F5: DRAFT is a real nonrenderable retained state.
        assert gamma_row["status"] == "DRAFT"
        assert gamma_row["values"] == {"rank": 1, "ratio": 3.75}
        assert gamma_row["row_version"] == observed["item_gamma"]["row_version"]
        press_one_row = items_by_slug["pressone"]
        assert press_one_row["status"] == "PUBLISHED"
        assert press_one_row["type_id"] == str(ids["type_b"])
        assert press_one_row["values"] == {
            # G5: the BASE document field value is a MULTI array of
            # FIELD-ONLY assets beside the BASE scalar document asset.
            "doc": [
                str(ids["media_pdf_doc"]),
                str(ids["media_pdf_doc2"]),
            ],
            "brief": str(ids["media_doc_base"]),
        }
        assert press_one_row["row_version"] == observed["ed_item_one"]["row_version"]
        press_two_row = items_by_slug["presstwo"]
        assert press_two_row["status"] == "PUBLISHED"
        assert press_two_row["values"] == {}
        assert press_two_row["row_version"] == observed["ed_item_two"]["row_version"]
        for row in content["items"]:
            observed_type = (
                observed["type_a"]
                if row["type_id"] == str(ids["type_a"])
                else observed["ed_type_b"]
            )
            assert row["type_definition_version"] == observed_type["definition_version"]
        # ---- translations (G5 localized field-only value; F5 absence)
        assert len(content["translations"]) == 7
        assert all(set(row) == RC1_TRANSLATION_KEYS for row in content["translations"])
        translations_by_item_locale = {
            (row["item_id"], row["locale"]): row for row in content["translations"]
        }
        assert set(translations_by_item_locale) == {
            (str(ids["item_alpha"]), "en"),
            (str(ids["item_alpha"]), "sl-SI"),
            (str(ids["item_beta"]), "en"),
            (str(ids["item_beta"]), "sl-SI"),
            (str(ids["ed_item_one"]), "en"),
            (str(ids["ed_item_one"]), "sl-SI"),
            (str(ids["ed_item_two"]), "en"),
        }
        # F5: gamma has NO translation at all - absent retained rows.
        assert not any(
            row["item_id"] == str(ids["item_gamma"]) for row in content["translations"]
        )
        alpha_en_t = translations_by_item_locale[(str(ids["item_alpha"]), "en")]
        assert alpha_en_t["localized_values"] == {
            "title": "Alpha rc1",
            "summary": "Alpha povz en",
        }
        observed_alpha_en_t = next(
            row
            for row in observed["translations_alpha"]
            if row["id"] == alpha_en_t["id"]
        )
        assert alpha_en_t["row_version"] == observed_alpha_en_t["row_version"]
        alpha_t = translations_by_item_locale[(str(ids["item_alpha"]), "sl-SI")]
        assert alpha_t["locale"] == "sl-SI"
        assert alpha_t["localized_values"] == {
            "title": "Alfa rc1",
            "summary": "Alfa povz",
            # G5: the LOCALIZED media value is a MULTI array of
            # FIELD-ONLY assets.
            "photo": [
                str(ids["media_photo_sl"]),
                str(ids["media_photo2_sl"]),
            ],
        }
        observed_alpha_t = next(
            row for row in observed["translations_alpha"] if row["id"] == alpha_t["id"]
        )
        assert alpha_t["row_version"] == observed_alpha_t["row_version"]
        beta_en_t = translations_by_item_locale[(str(ids["item_beta"]), "en")]
        assert beta_en_t["localized_values"] == {
            "title": "Beta rc1",
            "summary": "Beta povz en",
        }
        observed_beta_en_t = next(
            row for row in observed["translations_beta"] if row["id"] == beta_en_t["id"]
        )
        assert beta_en_t["row_version"] == observed_beta_en_t["row_version"]
        beta_t = translations_by_item_locale[(str(ids["item_beta"]), "sl-SI")]
        assert beta_t["locale"] == "sl-SI"
        assert beta_t["localized_values"] == {
            "title": "Beta rc1",
            "summary": "Beta povz",
        }
        observed_beta_t = next(
            row for row in observed["translations_beta"] if row["id"] == beta_t["id"]
        )
        assert beta_t["row_version"] == observed_beta_t["row_version"]
        press_en_t = translations_by_item_locale[(str(ids["ed_item_one"]), "en")]
        assert press_en_t["localized_values"] == {"title": "Press one"}
        observed_press_en_t = next(
            row for row in observed["ed_trans_one"] if row["id"] == press_en_t["id"]
        )
        assert press_en_t["row_version"] == observed_press_en_t["row_version"]
        press_t = translations_by_item_locale[(str(ids["ed_item_one"]), "sl-SI")]
        assert press_t["locale"] == "sl-SI"
        assert press_t["localized_values"] == {
            "title": "Tiskovna ena",
            # G5: the LOCALIZED scalar document field value.
            "summary_doc": str(ids["media_doc_sl"]),
        }
        observed_press_t = next(
            row for row in observed["ed_trans_one"] if row["id"] == press_t["id"]
        )
        assert press_t["row_version"] == observed_press_t["row_version"]
        press_two_en_t = translations_by_item_locale[(str(ids["ed_item_two"]), "en")]
        assert press_two_en_t["localized_values"] == {"title": "Press two"}
        observed_press_two_en_t = next(
            row for row in observed["ed_trans_two"] if row["id"] == press_two_en_t["id"]
        )
        assert press_two_en_t["row_version"] == observed_press_two_en_t["row_version"]
        # ---- relations (BOTH surfaces) ----
        assert len(content["relations"]) == 2
        assert all(set(row) == RC1_RELATION_KEYS for row in content["relations"])
        rel_a = next(
            row
            for row in content["relations"]
            if row["source_item_id"] == str(ids["item_alpha"])
        )
        assert rel_a["target_item_id"] == str(ids["item_beta"])
        assert rel_a["field_definition_id"] == str(ids["field_related"])
        assert rel_a["position"] == 0
        assert rel_a["metadata"] == {"note": "retained"}
        rel_b = next(
            row
            for row in content["relations"]
            if row["source_item_id"] == str(ids["ed_item_one"])
        )
        assert rel_b["target_item_id"] == str(ids["ed_item_two"])
        assert rel_b["field_definition_id"] == str(ids["ed_field_related"])
        assert rel_b["position"] == 0
        assert rel_b["metadata"] == {}
        # ---- views (exact specs + ACTUAL public read-back pins) ----
        assert len(content["views"]) == 2
        assert all(set(row) == RC1_VIEW_KEYS for row in content["views"])
        view_a_row = next(
            row for row in content["views"] if row["id"] == str(ids["view"])
        )
        assert view_a_row["type_id"] == str(ids["type_a"])
        assert view_a_row["key"] == f"rc1view_{tag}"
        assert view_a_row["filter_spec"] == {
            "and": [
                {"status": "PUBLISHED"},
                {"field": "rank", "op": "gte", "value": 2},
            ]
        }
        assert view_a_row["sort_spec"] == {"field": "rank", "direction": "desc"}
        assert view_a_row["projection_spec"] == {"fields": ["rank", "ratio"]}
        assert view_a_row["pagination_spec"] == {"limit": 10, "offset": 0}
        assert (
            view_a_row["definition_version"] == observed["view_a"]["definition_version"]
        )
        assert view_a_row["row_version"] == observed["view_a"]["row_version"]
        view_b_row = next(
            row for row in content["views"] if row["id"] == str(ids["ed_view"])
        )
        assert view_b_row["type_id"] == str(ids["type_b"])
        assert view_b_row["key"] == f"rc1edview_{tag}"
        assert view_b_row["filter_spec"] == {"status": "PUBLISHED"}
        assert view_b_row["sort_spec"] == {"field": "slug", "direction": "asc"}
        assert view_b_row["projection_spec"] == {"fields": []}
        assert view_b_row["pagination_spec"] == {"limit": 5, "offset": 0}
        assert (
            view_b_row["definition_version"]
            == observed["ed_view_b"]["definition_version"]
        )
        assert view_b_row["row_version"] == observed["ed_view_b"]["row_version"]
        # ---- locales (pinned to the ACTUAL public read-back) ----
        assert len(payload["locales"]) == 2
        assert all(set(row) == RC1_LOCALE_KEYS for row in payload["locales"])
        observed_locales = {row["tag"]: row for row in observed["locales"]}
        assert set(observed_locales) == {row["tag"] for row in payload["locales"]}
        for row in payload["locales"]:
            assert row["site_id"] == str(seeded["site_id"])
            observed_row = observed_locales[row["tag"]]
            assert row["enabled"] == observed_row["enabled"]
            assert row["is_default"] == observed_row["is_default"]
            assert row["position"] == observed_row["position"]
            assert row["metadata"] == observed_row["metadata"]
            assert row["row_version"] == observed_row["row_version"]
        sl_row = next(row for row in payload["locales"] if row["tag"] == "sl-SI")
        # The Agent locale PATCH is retained.
        assert sl_row["metadata"] == {"note": "rc1-agent-locale"}
        en_row = next(row for row in payload["locales"] if row["tag"] == "en")
        assert en_row["is_default"] is True
        # ---- theme (base + Agent typography + Editor palette) ----
        theme = payload["theme"]
        assert set(theme) == RC1_THEME_KEYS
        assert theme["site_id"] == str(seeded["site_id"])
        assert theme["schema_version"] == "theme-schema/v1"
        assert theme["renderer_version"] == "renderer-v1"
        assert theme["palette"] == {"preset": "ember"}
        assert theme["typography"] == {
            "family": "mono",
            "scale": "balanced",
            "weight": "regular",
        }
        assert theme["layout"] == {
            "content_width": "md",
            "spacing": "md",
            "grid_gap": "md",
        }
        assert theme["shape"] == {"radius": "md", "shadow": "sm"}
        assert theme["row_version"] > 0
        # ---- regions (trusted model: BOTH keys always projected) ----
        # The trusted region read (067_001 slaif_region_list) projects
        # header + footer; a missing stored row falls back to the
        # deterministic trusted DEFAULT (footer: single-column,
        # {'links': [], 'note': ''}, md5-derived deterministic id (non-security
        # identifier, usedforsecurity=False), row_version 1).
        # The capture must retain both rows, sorted by region_key.
        assert len(payload["regions"]) == 2
        assert all(set(row) == RC1_REGION_KEYS for row in payload["regions"])
        footer_row, header_row = payload["regions"]
        assert header_row["site_id"] == str(seeded["site_id"])
        assert header_row["region_key"] == "header"
        assert header_row["id"] == str(seeded["region_id"])
        # The Agent region PATCH is retained on the stored header.
        assert header_row["variant"] == "minimal"
        assert header_row["schema_version"] == "global-region/v1"
        assert header_row["content"] == {
            "nav": [
                {
                    "label": "News",
                    "target": {"kind": "internal", "value": "/rc1news"},
                }
            ]
        }
        assert footer_row["site_id"] == str(seeded["site_id"])
        assert footer_row["region_key"] == "footer"
        # The trusted default footer: deterministic id + closed shape.
        assert footer_row["id"] == str(
            UUID(
                hashlib.md5(
                    f"{seeded['site_id']}:footer".encode(),
                    usedforsecurity=False,
                ).hexdigest()
            )
        )
        assert footer_row["variant"] == "single-column"
        assert footer_row["schema_version"] == "global-region/v1"
        assert footer_row["content"] == {"links": [], "note": ""}
        assert footer_row["row_version"] == 1
        # ---- navigation (definitions + items; read-back pins) ----
        navigation = payload["navigation"]
        assert set(navigation) == {"definitions", "items"}
        nav_definitions = navigation["definitions"]
        nav_items = navigation["items"]
        assert len(nav_definitions) == 1 and len(nav_items) == 1
        assert all(set(row) == RC1_NAV_DEFINITION_KEYS for row in nav_definitions)
        assert all(set(row) == RC1_NAV_ITEM_KEYS for row in nav_items)
        nav_def = nav_definitions[0]
        assert nav_def["site_id"] == str(seeded["site_id"])
        assert nav_def["key"] == "main"
        assert nav_def["label"] == "RC1 main"
        assert nav_def["id"] == str(ids["nav"])
        assert nav_def["labels"] == observed["nav"]["labels"]
        assert nav_def["settings"] == observed["nav"]["settings"]
        assert nav_def["row_version"] == observed["nav"]["row_version"]
        nav_item_row = nav_items[0]
        assert nav_item_row["id"] == str(ids["nav_item"])
        assert nav_item_row["site_id"] == str(seeded["site_id"])
        assert nav_item_row["navigation_id"] == str(ids["nav"])
        assert nav_item_row["target_kind"] == "INTERNAL"
        assert nav_item_row["target_value"] == "/rc1news"
        # Real contract (052_001): INTERNAL/EXTERNAL targets carry a
        # route string and MUST have page_id NULL (only PAGE targets
        # bind a page).  The captured row retains that discriminator.
        assert nav_item_row["page_id"] is None
        assert nav_item_row["labels"] == {"en": "News"}
        assert nav_item_row["parent_id"] is None
        # Real contract (050_001): parent_key is NOT NULL - top-level
        # items carry the null-UUID sentinel (coalesce(parent_id, ...)).
        assert nav_item_row["parent_key"] == "00000000-0000-0000-0000-000000000000"
        assert nav_item_row["position"] == 0
        assert nav_item_row["row_version"] == observed["nav_item"]["row_version"]
        # ---- redirects ----
        assert len(payload["redirects"]) == 1
        assert all(set(row) == RC1_REDIRECT_KEYS for row in payload["redirects"])
        redirect_row = payload["redirects"][0]
        assert redirect_row["site_id"] == str(seeded["site_id"])
        assert redirect_row["source_route"] == f"/rc1old-{tag}"
        assert redirect_row["target"] == "/rc1news"
        assert redirect_row["status_code"] == 301
        assert redirect_row["row_version"] == observed["redirect"]["row_version"]
        assert redirect_row["locale"] == observed["redirect"]["locale"]
        # ---- pages (F5 tombstone; F8 raw + resolved styles) ----
        assert len(payload["pages"]) == 5
        assert all(set(row) == RC1_PAGE_KEYS for row in payload["pages"])
        pages_by_slug = {row["slug"]: row for row in payload["pages"]}
        assert set(pages_by_slug) == {
            "home",
            "rc1news",
            "rc1item",
            "rc1press",
            "rc1gone",
        }
        for row in payload["pages"]:
            assert row["site_id"] == str(seeded["site_id"])
            assert row["locale"] == "en"
        home_row = pages_by_slug["home"]
        news_row = pages_by_slug["rc1news"]
        detail_row = pages_by_slug["rc1item"]
        press_row = pages_by_slug["rc1press"]
        gone_row = pages_by_slug["rc1gone"]
        # The top-level 'home' segment is elided by the trusted route
        # builder, so the home page owns "/".
        assert home_row["parent_id"] is None
        assert home_row["route_template"] is None
        assert home_row["effective_route"] == "/"
        assert home_row["status"] == "PUBLISHED"
        assert home_row["deleted_at"] is None
        assert home_row["style_overrides"] == {}
        # Real contract (066_001): every NON-DELETED page projects a
        # page-style row; empty overrides resolve to the captured
        # theme unchanged.  Only deleted pages carry style NULL.
        home_style = home_row["style"]
        assert set(home_style) == RC1_PAGE_STYLE_KEYS
        assert home_style["page_id"] == str(ids["page_home"])
        assert home_style["overrides"] == {}
        assert home_style["resolved"] == theme
        assert news_row["parent_id"] == str(ids["page_home"])
        assert news_row["effective_route"] == "/rc1news"
        assert detail_row["parent_id"] == str(ids["page_news"])
        assert detail_row["route_template"] == "{slug}"
        assert detail_row["effective_route"] == "/rc1news/{slug}"
        assert detail_row["style_overrides"] == {}
        detail_style = detail_row["style"]
        assert set(detail_style) == RC1_PAGE_STYLE_KEYS
        assert detail_style["page_id"] == str(ids["page_detail"])
        assert detail_style["overrides"] == {}
        assert detail_style["resolved"] == theme
        assert press_row["parent_id"] is None
        assert press_row["effective_route"] == "/rc1press"
        # F5: the public-deleted page is retained as a tombstone.
        assert gone_row["deleted_at"] is not None
        assert gone_row["effective_route"] is None
        assert gone_row["style"] is None
        assert gone_row["nodes"] == []
        # F8: the Agent-surface page style keeps raw overrides AND the
        # resolved projection (theme tokens with the layout override).
        assert news_row["style_overrides"] == {"layout": {"content_width": "xl"}}
        news_style = news_row["style"]
        assert set(news_style) == RC1_PAGE_STYLE_KEYS
        assert news_style["page_id"] == str(ids["page_news"])
        assert news_style["site_id"] == str(seeded["site_id"])
        assert news_style["schema_version"] == "page-style/v1"
        assert news_style["overrides"] == {"layout": {"content_width": "xl"}}
        assert news_style["row_version"] > 0
        assert news_style["resolved"] == {
            **theme,
            "layout": {"content_width": "xl", "spacing": "md", "grid_gap": "md"},
        }
        # F8: the Editor-surface page style (distinct page + token).
        assert press_row["style_overrides"] == {"layout": {"content_width": "sm"}}
        press_style = press_row["style"]
        assert press_style["page_id"] == str(ids["ed_page"])
        assert press_style["overrides"] == {"layout": {"content_width": "sm"}}
        assert press_style["resolved"] == {
            **theme,
            "layout": {"content_width": "sm", "spacing": "md", "grid_gap": "md"},
        }
        # ---- page compositions (exact props for all seven nodes) ----
        compositions = payload["page_compositions"]
        assert len(compositions) == 7
        assert all(set(row) == RC1_COMPOSITION_KEYS for row in compositions)
        comp = {(row["page_id"], row["component_type"]): row for row in compositions}
        assert set(comp) == {
            (str(ids["page_home"]), "CollectionSearch"),
            (str(ids["page_home"]), "Image"),
            (str(ids["page_news"]), "CollectionList"),
            (str(ids["page_news"]), "DocumentList"),
            (str(ids["page_detail"]), "CollectionDetail"),
            (str(ids["page_detail"]), "RelatedItems"),
            (str(ids["ed_page"]), "CollectionList"),
        }
        for row in compositions:
            assert row["site_id"] == str(seeded["site_id"])
            assert row["catalog_version"] == "catalog-v1"
            assert row["schema_version"] == "1"
            assert row["slot_key"] == "default"
        assert comp[(str(ids["page_home"]), "CollectionSearch")]["props"] == {
            "viewId": str(ids["view"])
        }
        assert comp[(str(ids["page_home"]), "Image")]["props"] == {
            "mediaId": str(ids["media_img"]),
            "alt": "RC1 photo",
        }
        assert comp[(str(ids["page_news"]), "CollectionList")]["props"] == {
            "viewId": str(ids["view"])
        }
        assert comp[(str(ids["page_news"]), "DocumentList")]["props"] == {
            "items": [
                {
                    "mediaId": str(ids["media_pdf_comp"]),
                    "label": "RC1 document",
                }
            ]
        }
        assert comp[(str(ids["page_detail"]), "CollectionDetail")]["props"] == {
            "viewId": str(ids["view"])
        }
        assert comp[(str(ids["page_detail"]), "RelatedItems")]["props"] == {
            "viewId": str(ids["view"])
        }
        assert comp[(str(ids["ed_page"]), "CollectionList")]["props"] == {
            "viewId": str(ids["ed_view"])
        }

        def node_components(page_row: dict[str, Any]) -> set[str]:
            return {node["component_type"] for node in page_row["nodes"]}

        assert node_components(home_row) == {"CollectionSearch", "Image"}
        assert node_components(news_row) == {"CollectionList", "DocumentList"}
        assert node_components(detail_row) == {"CollectionDetail", "RelatedItems"}
        assert node_components(press_row) == {"CollectionList"}
        # ---- proposals (F6: retained, never executed) ----
        assert len(payload["proposals"]) == 1
        assert all(set(row) == RC1_PROPOSAL_KEYS for row in payload["proposals"])
        proposal_doc = payload["proposals"][0]
        assert proposal_doc["id"] == str(seeded["proposal_id"])
        assert proposal_doc["site_id"] == str(seeded["site_id"])
        assert proposal_doc["workspace_id"] == str(seeded["workspace_id"])
        assert proposal_doc["kind"] == "cache_purge"
        assert proposal_doc["payload"] == {"scope": "rc1-retained-proposal"}
        # 042_001 CHECK permits ONLY 'PROPOSED' - it can never move.
        assert proposal_doc["state"] == "PROPOSED"
        # ---- media inventory (ALL twelve assets, metadata only) ----
        inventory = payload["media_inventory"]
        assert len(inventory) == 12
        assert all(set(row) == RC1_MEDIA_INVENTORY_KEYS for row in inventory)
        inventory_by_id = {row["id"]: row for row in inventory}
        expected_inventory: dict[str, tuple[str, str, int, str, str]] = {
            str(ids["media_img"]): (
                "rc1.png",
                "image/png",
                len(RC1_PNG_BYTES),
                png_hash,
                "RC1 photo (reviewed)",
            ),
            str(ids["media_pdf_comp"]): (
                "rc1.pdf",
                "application/pdf",
                len(RC1_PDF_BYTES),
                pdf_hash,
                "RC1 document",
            ),
            str(ids["media_photo_en"]): (
                "rc1-photo-en.png",
                "image/png",
                len(RC1_PNG2_BYTES),
                png2_hash,
                "RC1 base photo",
            ),
            str(ids["media_photo2_en"]): (
                "rc1-photo2-en.png",
                "image/png",
                len(RC1_PNG4_BYTES),
                png4_hash,
                "RC1 base photo 2",
            ),
            str(ids["media_photo_sl"]): (
                "rc1-photo-sl.png",
                "image/png",
                len(RC1_PNG3_BYTES),
                png3_hash,
                "RC1 sl photo",
            ),
            str(ids["media_photo2_sl"]): (
                "rc1-photo2-sl.png",
                "image/png",
                len(RC1_PNG5_BYTES),
                png5_hash,
                "RC1 sl photo 2",
            ),
            str(ids["media_pdf_doc"]): (
                "rc1-doc-field.pdf",
                "application/pdf",
                len(RC1_PDF3_BYTES),
                pdf3_hash,
                "RC1 document field",
            ),
            str(ids["media_pdf_doc2"]): (
                "rc1-doc-field2.pdf",
                "application/pdf",
                len(RC1_PDF4_BYTES),
                pdf4_hash,
                "RC1 document field 2",
            ),
            str(ids["media_cover"]): (
                "rc1-cover.png",
                "image/png",
                len(RC1_PNG6_BYTES),
                png6_hash,
                "RC1 cover scalar",
            ),
            str(ids["media_doc_base"]): (
                "rc1-doc-base.pdf",
                "application/pdf",
                len(RC1_PDF5_BYTES),
                pdf5_hash,
                "RC1 document scalar base",
            ),
            str(ids["media_doc_sl"]): (
                "rc1-doc-sl.pdf",
                "application/pdf",
                len(RC1_PDF6_BYTES),
                pdf6_hash,
                "RC1 document scalar localized",
            ),
            str(ids["media_pdf_unrelated"]): (
                "rc1-unrelated.pdf",
                "application/pdf",
                len(RC1_PDF2_BYTES),
                pdf2_hash,
                "RC1 unrelated private doc",
            ),
        }
        assert set(inventory_by_id) == set(expected_inventory)
        for media_id, (
            filename,
            mime,
            size,
            content_hash,
            alt_text,
        ) in expected_inventory.items():
            row = inventory_by_id[media_id]
            assert row["site_id"] == str(seeded["site_id"])
            assert row["filename"] == filename
            assert row["mime_type"] == mime
            assert row["size_bytes"] == size
            assert row["content_hash"] == content_hash
            assert row["alt_text"] == alt_text
            assert row["metadata"] == {}
            assert row["public_status"] == "private"
            assert row["published_at"] is None
        # The Editor alt_text PATCH is retained on the image asset.

        # ---- F6 trusted no-effects oracles ---------------------------
        # The freeze (and the review surface it creates) never
        # executes the proposal: the row state stays PROPOSED, the
        # site canonical_revision is unchanged, and the cache outbox
        # is empty for the site.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            # The proposal row lives in this workspace's COW session
            # layer; the workspace-scoped read (the same context the
            # 076 freeze binds) sees base + session changes.
            await owner.execute(
                "SELECT set_config('app.session_id', $1::text, false)",
                str(seeded["workspace_id"]),
            )
            try:
                proposal_row = await owner.fetchrow(
                    "SELECT * FROM content.proposed_side_effect WHERE id = $1",
                    seeded["proposal_id"],
                )
                assert proposal_row is not None
                assert str(proposal_row["state"]) == "PROPOSED"
                assert str(proposal_row["kind"]) == "cache_purge"
                # The owner connection delivers jsonb as canonical
                # text (the same boundary that decodes the payload
                # above); decode for the exact proposal document.
                assert j(proposal_row["payload"]) == {"scope": "rc1-retained-proposal"}
            finally:
                await owner.execute("SELECT set_config('app.session_id', '', false)")
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.cache_outbox WHERE site_id = $1",
                    seeded["site_id"],
                )
                == 0
            )
            assert (
                int(
                    await owner.fetchval(
                        "SELECT canonical_revision FROM control.site WHERE id = $1",
                        seeded["site_id"],
                    )
                )
                == revision_before_freeze
            )
    finally:
        await control.stop()
        await editor.stop()


async def _rc1n_projection(
    snapshot_row: Any, *, site_id: UUID, workspace_id: UUID
) -> dict[str, Any]:
    """The REAL frozen common projection of the numeric-approval page.

    Shared RenderProjectionService engine over a FrozenRenderSurface on
    the ACTUAL stored v2 row (the SAME qualified consumer pattern the
    frozen parity cases use; no shadow engine, no SQL-string fake).
    The engine sees the retained values as int/float exactly as the
    live path always receives them (frozen_source._render_value's
    qualified behavior); the retained raw document keeps every digit,
    which the canonical-text/parse_snapshot_text oracles prove.
    """
    from slaif_agent_site.render_api import frozen_source as _fs
    from slaif_agent_site.sites.models import SiteContext as _SiteContext

    def _decode_raw(value: Any) -> Any:
        # parse_snapshot_text is the product's qualified raw-retention
        # reader (parse_float=Decimal): the stored payload must be
        # decoded with it so the admitted digest recomputes exactly.
        return parse_snapshot_text(value) if isinstance(value, str) else value

    def _decode(value: Any) -> Any:
        return json.loads(value) if isinstance(value, str) else value

    decoded = dict(snapshot_row)
    for key in ("payload", "normalized_state"):
        decoded[key] = _decode_raw(decoded[key])
    for key in (
        "versions",
        "validation_report",
        "media_references",
        "browser_evidence",
    ):
        decoded[key] = _decode(decoded[key])
    surface = _fs.FrozenRenderSurface(
        decoded,
        expected_snapshot_id=snapshot_row["id"],
        expected_site_id=site_id,
        expected_workspace_id=workspace_id,
    )
    frozen_ctx = _SiteContext._from_frozen(
        site_id=site_id,
        site_key=surface.site_key,
        status=surface.site_status,
        base_site_revision=surface.base_site_revision,
        default_locale=surface.default_locale,
        matched_path_prefix=None,
    )
    from slaif_agent_site.render_api.projection import (
        RenderPageProjection as _RenderPageProjection,
    )

    service = RenderProjectionService(surface)
    route = await service._query(
        surface,
        context=frozen_ctx,
        request=RenderPageRequest(authority="localhost", path="/exactmap"),
        render_mode="review",
        snapshot_id=snapshot_row["id"],
    )
    assert isinstance(route, _RenderPageProjection)
    items = [
        dict(item) for item in route.bindings[_rc1_node_id(route, "CollectionList")]
    ]
    map_node = next(
        node
        for node in _rc1_walk_nodes(route.composition.nodes)
        if node.component_type == "MapBlock"
    )
    return {
        "page_slug": route.page.slug,
        "items": items,
        "west": map_node.props["bbox"]["west"],
    }


@pytest.mark.asyncio
async def test_rc1_numeric_approval_composition_only_workspace(
    agent_site_database: AgentSiteDatabase,
    tmp_path: Path,
) -> None:
    """F2: numeric approval via a REAL accept on a qualified
    composition-only workspace.

    The numeric approval proof must not be mixed with the all-family
    public-mutation candidate (accepting that candidate would exercise
    deferred generic page/model DML promotion, out of scope).  This
    workspace is COMPOSITION-ONLY: its single COW change is one trusted
    composition node via content.slaif_agent_component_create in a real
    agent COW session (the SAME qualified composition path the 083/4
    serialization cases use).  The FULL exact-number map is carried by
    HONESTLY LABELED canonical fixture values (owner-seeded canonical
    rows, not public writes): three PUBLISHED items with the exact map
    42/0.1, 7/1.5, 1/3.75 (every value written through a numeric cast so
    the stored canonical text keeps each digit) plus the existing
    long-digit vector 0.10000000000000000000001 in a canonical MapBlock
    prop (the SAME numeric-cast mechanism the qualified exact-digit
    coverage uses).  The site carries NO media at all, so the selected
    media closure is empty and the accept's media finalization is a real
    no-op over an empty set - not a mock, not a monkeypatch.

    The real freeze + real accept (narrow worker credential, real
    re-materialization and digest/versions re-validation through the
    exact 082/1 snapshot path) must succeed, and the stored snapshot must
    retain the FULL exact-number map (raw canonical text plus
    parse_snapshot_text + Decimal) after approval.

    The SAME complete raw exact-number map/digest must remain byte and
    value exact before AND after the real common projection and the real
    approval, and the REAL frozen common projection (FrozenRenderSurface
    + shared RenderProjectionService engine over the stored row) must
    serve the full map through its qualified int/float rendering
    contract (frozen_source._render_value behavior - the engine always
    sees int/float exactly as the live path receives asyncpg jsonb
    decoding) before and after approval, with identical derived output
    on both sides.  No product render boundary is changed and no public
    precision capability is claimed.
    """
    from decimal import Decimal

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    tag = uuid4().hex[:8]
    exact_fraction = "0.10000000000000000000001"

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        # Honest trusted fixture substrate.  NO media anywhere on this
        # site: the selected media closure is empty by construction, so
        # approval finalizes exactly zero media (a real no-op).
        delegator_id = await owner.fetchval(
            "INSERT INTO control.user_account (id, identity_kind,"
            " local_username, local_username_normalized, password_hash,"
            " display_name, status) VALUES (gen_random_uuid(),'LOCAL',"
            " 'Rc1n.Delegator','rc1n.delegator',$1,'Rc1n Delegator','ACTIVE')"
            " RETURNING id",
            _AGGON2,
        )
        site_id = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name,"
            " default_locale, component_catalog_version) VALUES ($1,"
            " 'Rc1 Numeric','en','catalog-v1') RETURNING id",
            f"rc1num-{tag}",
        )
        await owner.execute(
            "INSERT INTO control.site_membership (site_id,user_account_id,"
            " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
            site_id,
            delegator_id,
        )
        await owner.execute(
            "INSERT INTO content.site_locale_base (site_id,tag,enabled,"
            " is_default,position) VALUES ($1,'en',true,true,0)",
            site_id,
        )
        await owner.execute(
            "INSERT INTO content.theme_base (id, site_id, schema_version,"
            " renderer_version, palette, typography, layout, shape) VALUES"
            " (gen_random_uuid(), $1, 'theme-schema/v1', 'renderer-v1',"
            ' \'{"preset":"ocean"}\'::jsonb,'
            ' \'{"family":"system","scale":"balanced","weight":"regular"}'
            "'::jsonb,"
            ' \'{"content_width":"md","spacing":"md","grid_gap":"md"}'
            "'::jsonb,"
            ' \'{"radius":"md","shadow":"sm"}\'::jsonb)',
            site_id,
        )
        # The FULL exact-number map as canonical fixture values (honest
        # trusted setup, NOT public writes): 42/0.1, 7/1.5, 1/3.75 -
        # every value through a numeric cast so each digit is stored.
        type_id = uuid4()
        rank_field_id = uuid4()
        ratio_field_id = uuid4()
        alpha_id = uuid4()
        beta_id = uuid4()
        gamma_id = uuid4()
        await owner.execute(
            "INSERT INTO content.content_type_base (id, site_id, key,"
            " labels, slug_pattern, status, definition_version, settings)"
            " VALUES ($1,$2,'exactnum','{\"en\":\"Exact num\"}'::jsonb,"
            " '/exactnum/{slug}','ACTIVE',1,'{}'::jsonb)",
            type_id,
            site_id,
        )
        await owner.execute(
            "INSERT INTO content.field_definition_base (id, site_id,"
            " type_id, key, label, field_type, required, localized,"
            " cardinality, position, validation, ui_options,"
            " definition_version) VALUES"
            " ($1,$2,$3,'rank','Rank','integer',true,false,1,0,"
            "  '{}'::jsonb,'{}'::jsonb,1),"
            " ($4,$2,$3,'ratio','Ratio','decimal',true,false,1,1,"
            "  '{}'::jsonb,'{}'::jsonb,1)",
            rank_field_id,
            site_id,
            type_id,
            ratio_field_id,
        )
        await owner.execute(
            "INSERT INTO content.content_item_base (id, site_id, type_id,"
            " slug, status, type_definition_version, values, row_version)"
            " VALUES"
            " ($1,$2,$3,'alpha','PUBLISHED',1,"
            "  jsonb_build_object('rank',$4::numeric,'ratio',$5::numeric),1),"
            " ($6,$2,$3,'beta','PUBLISHED',1,"
            "  jsonb_build_object('rank',$7::numeric,'ratio',$8::numeric),1),"
            " ($9,$2,$3,'gamma','PUBLISHED',1,"
            "  jsonb_build_object('rank',$10::numeric,'ratio',$11::numeric),1)",
            alpha_id,
            site_id,
            type_id,
            "42",
            "0.1",
            beta_id,
            "7",
            "1.5",
            gamma_id,
            "1",
            "3.75",
        )
        # Canonical collection view over the exactnum items (trusted
        # fixture): the real frozen collection query serves the FULL
        # exact-number map to the common projector.
        view_id = uuid4()
        await owner.execute(
            "INSERT INTO content.collection_view_base (id, site_id,"
            " type_id, key, filter_spec, sort_spec, projection_spec,"
            " pagination_spec, definition_version) VALUES ($1,$2,$3,"
            " 'exactnum','{\"status\":\"PUBLISHED\"}'::jsonb,"
            ' \'{"field":"rank","direction":"desc"}\'::jsonb,'
            ' \'{"fields":["rank","ratio"]}\'::jsonb,'
            ' \'{"limit":10,"offset":0}\'::jsonb,1)',
            view_id,
            site_id,
            type_id,
        )
        # Canonical page + the existing long-digit vector (the SAME
        # numeric-cast-into-jsonb-prop mechanism the qualified
        # exact-digit coverage uses).
        page_id = uuid4()
        section_id = uuid4()
        map_block_id = uuid4()
        list_block_id = uuid4()
        await owner.execute(
            "INSERT INTO content.page_base (id, site_id, slug, title,"
            " status, locale) VALUES ($1,$2,'exactmap','Exact map',"
            " 'PUBLISHED','en')",
            page_id,
            site_id,
        )
        await owner.execute(
            "INSERT INTO content.page_composition_base (id, site_id,"
            " page_id, component_type, schema_version, parent_id,"
            " slot_key, order_key, props) VALUES"
            " ($1,$2,$3,'Section','1',NULL::uuid,'default',0,'{}'::jsonb),"
            " ($4,$2,$3,'MapBlock','1',$1,'default',0,"
            "  jsonb_build_object('title','Exact',"
            "   'bbox', jsonb_build_object("
            "     'west',$5::numeric,"
            "     'south',-1,'east',1,'north',1))),"
            " ($6,$2,$3,'CollectionList','1',$1,'default',1,"
            "  jsonb_build_object('viewId',$7::text))",
            section_id,
            site_id,
            page_id,
            map_block_id,
            exact_fraction,
            list_block_id,
            str(view_id),
        )
        # One composition-only candidate workspace (the real L4 preset,
        # pinned version facts) with one capability for the COW change.
        workspace_id = await owner.fetchval(
            "INSERT INTO control.workspace (site_id, created_by,"
            " delegator_id, title, delegation_preset, effective_scopes,"
            " version_facts, status, expires_at) VALUES ($1,$2,$2,"
            " 'Rc1 Numeric Candidate','L4_SITE_ARCHITECT', $3::jsonb, "
            + _CURRENT_VERSION_FACTS
            + ", 'ACTIVE', now()+interval '1 hour') RETURNING id",
            site_id,
            delegator_id,
            json.dumps(RC1_L4_SCOPES),
        )
        token, public_id, digest = generate_capability_token()
        await owner.execute(
            "INSERT INTO control.capability (workspace_id, public_id,"
            " secret_digest, scopes, expires_at) VALUES ($1,$2,$3,"
            " $4::jsonb, now()+interval '30 minutes')",
            workspace_id,
            public_id,
            digest,
            json.dumps(RC1_L4_SCOPES),
        )
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE public_id = $1",
            public_id,
        )
    seeded = {
        "delegator_id": UUID(str(delegator_id)),
        "site_id": UUID(str(site_id)),
        "workspace_id": UUID(str(workspace_id)),
        "capability_id": UUID(str(capability_id)),
        "page_id": page_id,
        "section_id": section_id,
        "map_block_id": map_block_id,
    }
    # The single workspace change: one trusted composition node (the
    # SAME qualified composition path the 083/4 serialization cases use).
    await _cow_create(
        database,
        workspace_id=seeded["workspace_id"],
        capability_id=seeded["capability_id"],
        site_id=seeded["site_id"],
        page_id=seeded["page_id"],
        parent_id=seeded["section_id"],
        text=f"rc1-approval-{tag}",
    )
    # Real freeze: enqueue + narrow-credential claim + run.
    job_id, _ = await _freeze(database, seeded)
    pool = await _worker_pool(database)
    snapshot: Any = None
    try:
        rows = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            f"rc1-numeric-freeze-{tag}",
            ["FREEZE", "ACCEPT"],
        )
        assert len(rows) == 1
        assert str(rows[0]["id"]) == str(job_id)
        result = await run_freeze_job(pool, _worker_settings(database), dict(rows[0]))
        assert result.status == "SUCCEEDED", result
        snapshot = await _snapshot_row(database, seeded["workspace_id"])
        assert snapshot is not None
        assert str(snapshot["status"]) == "COMPLETE"
        # The REAL common projection over the stored frozen row BEFORE
        # approval: the FULL exact-number map served through the real
        # frozen collection query and the projected MapBlock props, on
        # the engine's qualified int/float rendering contract.
        projection_before = await _rc1n_projection(
            snapshot,
            site_id=seeded["site_id"],
            workspace_id=seeded["workspace_id"],
        )
        assert projection_before["page_slug"] == "exactmap"
        assert [
            (item["slug"], item["values"]["rank"], item["values"]["ratio"])
            for item in projection_before["items"]
        ] == [
            ("alpha", 42, 0.1),
            ("beta", 7, 1.5),
            ("gamma", 1, 3.75),
        ]
        assert projection_before["west"] == 0.1
        # The FULL exact-number map in the stored canonical text BEFORE
        # approval (raw digits, no float round trip).
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            canonical_text = await owner.fetchval(
                "SELECT control.slaif_canonical_jsonb_text($1)",
                snapshot["payload"],
            )
        assert canonical_text is not None
        for raw in (
            '"rank":42',
            '"ratio":0.1',
            '"rank":7',
            '"ratio":1.5',
            '"rank":1',
            '"ratio":3.75',
            f'"west":{exact_fraction}',
        ):
            assert raw in canonical_text, raw
        # The selected media closure is EMPTY (the site has no media):
        # approval finalizes exactly zero media - a real no-op, not a
        # mock.
        media_references_raw = snapshot["media_references"]
        media_references = (
            json.loads(media_references_raw)
            if isinstance(media_references_raw, str)
            else media_references_raw
        )
        assert media_references == []
        # Real accept: the only promotion path; re-materializes and
        # re-validates the stored digest/versions through the exact
        # 082/1 path under qualified reviewer authority.
        accept_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_workspace_accept($1,$2)",
            seeded["workspace_id"],
            seeded["delegator_id"],
        )
        assert len(accept_rows) == 1
        accept_job_id = UUID(str(accept_rows[0]["job_id"]))
        accept_claims = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            f"rc1-numeric-accept-{tag}",
            ["FREEZE", "ACCEPT"],
        )
        assert len(accept_claims) == 1
        assert str(accept_claims[0]["id"]) == str(accept_job_id)
        boundary = MediaBoundary(
            settings=_media_settings(database, tmp_path / "rc1n-media")
        )
        try:
            accept_result = await run_accept_job(
                pool,
                _worker_settings(database),
                dict(accept_claims[0]),
                media=boundary,
            )
            assert accept_result.status == "SUCCEEDED", accept_result
        finally:
            await boundary.stop()
    finally:
        await pool.close()
    assert snapshot is not None
    # Post-approval effect oracles: exactly one promotion, the canonical
    # revision advanced once, the workspace ACCEPTED with the snapshot
    # binding, and the canonical numeric fixtures committed unchanged.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        ws_row = await owner.fetchrow(
            "SELECT status, accepted_at, review_snapshot_id"
            " FROM control.workspace WHERE id = $1",
            seeded["workspace_id"],
        )
        assert str(ws_row["status"]) == "ACCEPTED"
        assert ws_row["accepted_at"] is not None
        assert str(ws_row["review_snapshot_id"]) == str(snapshot["id"])
        revision_after = int(
            await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                seeded["site_id"],
            )
        )
        assert revision_after == 1
        promotion_rows = await owner.fetch(
            "SELECT * FROM audit.promotion WHERE site_id = $1",
            seeded["site_id"],
        )
        assert len(promotion_rows) == 1
        assert int(promotion_rows[0]["new_canonical_revision"]) == 1
        assert str(promotion_rows[0]["snapshot_id"]) == str(snapshot["id"])
        assert str(promotion_rows[0]["job_id"]) == str(accept_job_id)
        values_rows = await owner.fetch(
            "SELECT slug, values FROM content.content_item"
            " WHERE site_id = $1 ORDER BY slug",
            seeded["site_id"],
        )
        decoded_values = [
            (
                row["slug"],
                json.loads(row["values"])
                if isinstance(row["values"], str)
                else row["values"],
            )
            for row in values_rows
        ]
        assert decoded_values == [
            ("alpha", {"rank": 42, "ratio": 0.1}),
            ("beta", {"rank": 7, "ratio": 1.5}),
            ("gamma", {"rank": 1, "ratio": 3.75}),
        ]
    # The stored snapshot is IMMUTABLE across the approval; the frozen
    # consumer re-reads the FULL exact-number map after approval.
    snapshot_after = await _snapshot_row(database, seeded["workspace_id"])
    assert snapshot_after is not None
    assert str(snapshot_after["id"]) == str(snapshot["id"])
    assert snapshot_after["digest"] == snapshot["digest"]
    assert snapshot_after["payload"] == snapshot["payload"]
    payload_text = snapshot_after["payload"]
    stored_payload: Any = parse_snapshot_text(
        payload_text if isinstance(payload_text, str) else json.dumps(payload_text)
    )
    assert canonical_digest(stored_payload) == str(snapshot_after["digest"])
    captured_map = None
    for row in stored_payload["page_compositions"]:
        if str(row.get("id")) == str(seeded["map_block_id"]):
            captured_map = row
            break
    assert captured_map is not None
    # Every written digit survives approval (the long-digit vector).
    assert captured_map["props"]["bbox"]["west"] == Decimal(exact_fraction)
    items_by_slug = {row["slug"]: row for row in stored_payload["content"]["items"]}
    assert items_by_slug["alpha"]["values"] == {
        "rank": 42,
        "ratio": Decimal("0.1"),
    }
    assert items_by_slug["beta"]["values"] == {
        "rank": 7,
        "ratio": Decimal("1.5"),
    }
    assert items_by_slug["gamma"]["values"] == {
        "rank": 1,
        "ratio": Decimal("3.75"),
    }
    # The SAME real common projection re-executed AFTER approval over
    # the re-read stored row is identical: the snapshot is immutable
    # (raw digest/payload equality asserted above) and the derived
    # projector values match the qualified int/float contract on both
    # sides of the real approval.
    projection_after = await _rc1n_projection(
        snapshot_after,
        site_id=seeded["site_id"],
        workspace_id=seeded["workspace_id"],
    )
    assert projection_after == projection_before


# ---------------------------------------------------------------------------
# 083-5-b hostile freeze lane (G9 / G12 / E-D3+E-M2): real worker refusals
# over trusted stored-row fixtures with full before/after no-effects.
#
# Owner tampering is a test threat fixture only: the public/agent writers
# already reject these shapes at admission, so the materializer branches
# are reachable by stored-row corruption only (hostile stored-row
# fixtures, NOT newly admitted public mutations).
# ---------------------------------------------------------------------------


async def _hostile_effect_snapshot(
    database: AgentSiteDatabase, *, workspace_id: UUID, site_id: UUID
) -> dict[str, Any]:
    """The shared extended freeze oracle over one owner connection."""

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return await _rt_effect_snapshot(owner, str(workspace_id), str(site_id))


async def _materializer_refusal_detail(
    database: AgentSiteDatabase, *, workspace_id: UUID
) -> tuple[str, str | None]:
    """Direct trusted materializer call (worker role).

    Returns the (message, detail) of the stable SQL refusal the real
    freeze job just hit: branch-level proof of WHICH materializer gate
    fired, without a second job run or any product change.
    """

    login, password = database.credentials["slaif_review_worker"]
    connection = await asyncpg.connect(dsn=_dsn(database, login, password))
    try:
        with pytest.raises(asyncpg.PostgresError) as excinfo:
            await connection.fetchval(
                "SELECT control.slaif_review_workspace_state($1)",
                workspace_id,
            )
        return excinfo.value.message, excinfo.value.detail
    finally:
        await connection.close()


async def _freeze_refusal_state(
    database: AgentSiteDatabase, *, workspace_id: UUID, job_id: UUID
) -> tuple[Any, str]:
    """Legitimate refusal bookkeeping, shown SEPARATELY from the oracle.

    Returns (job_row, '<workspace status>/<snapshot count>').
    """

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        job_row = await owner.fetchrow(
            "SELECT status, error, attempt_count FROM control.review_job WHERE id = $1",
            job_id,
        )
        state = await owner.fetchval(
            "SELECT w.status || '/' || ("
            " SELECT count(*) FROM control.review_snapshot s"
            " WHERE s.workspace_id = w.id)::text"
            " FROM control.workspace w WHERE w.id = $1",
            workspace_id,
        )
    return job_row, str(state)


@pytest.mark.asyncio
async def test_freeze_over_budget_content_types_refused_no_effects(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """G9/E-B1: the ACTUAL capture/preflight count bound at freeze.

    64 content types (exactly MAX_CONTENT_TYPES) freeze clean in a
    control workspace; the 65th type makes a second workspace refuse
    with the stable budget code, zero snapshot rows, and full
    no-effects.  Not a synthetic admission call or attempt exhaustion.
    """

    database = agent_site_database
    seeded = await _seed(database)
    site_id = seeded["site_id"]
    pool = await _worker_pool(database)
    try:
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            # 64 valid distinct content types: exactly at the cap.
            await owner.execute(
                "INSERT INTO content.content_type_base"
                ' (id, site_id, "key", labels, slug_pattern, status,'
                " definition_version, settings) SELECT"
                "  gen_random_uuid(), $1,"
                "  'g9-type-' || lpad(g::text, 2, '0'),"
                "  jsonb_build_object('en',"
                "   'G9 type ' || lpad(g::text, 2, '0')),"
                "  'g9/g9-type-' || lpad(g::text, 2, '0'),"
                "  'ACTIVE', 1, '{}'::jsonb"
                " FROM generate_series(0, 63) AS g",
                site_id,
            )
            type_count = await owner.fetchval(
                "SELECT count(*) FROM content.content_type WHERE site_id = $1",
                site_id,
            )
            control_ws, _cap = await _create_workspace(
                owner, site_id, seeded["delegator_id"], "G9 Control"
            )
        assert type_count == 64

        # Within-bound control: exactly 64 types PASS for real.
        result, _control_job = await _freeze_claim_run(
            database,
            workspace_id=control_ws,
            site_id=site_id,
            delegator_id=seeded["delegator_id"],
            pool=pool,
            claimant="g9-control-1",
        )
        assert result.status == "SUCCEEDED", result.error
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            control_state = await owner.fetchval(
                "SELECT w.status || '/' || ("
                " SELECT count(*) FROM control.review_snapshot s"
                " WHERE s.workspace_id = w.id)::text"
                " FROM control.workspace w WHERE w.id = $1",
                control_ws,
            )
        assert control_state == "REVIEW/1"

        # The 65th type crosses the actual preflight boundary.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "INSERT INTO content.content_type_base"
                ' (id, site_id, "key", labels, slug_pattern, status,'
                " definition_version, settings) VALUES"
                " (gen_random_uuid(), $1, 'g9-type-64',"
                "  '{\"en\":\"G9 type 64\"}'::jsonb, 'g9/g9-type-64',"
                "  'ACTIVE', 1, '{}'::jsonb)",
                site_id,
            )
            over_ws, _cap = await _create_workspace(
                owner, site_id, seeded["delegator_id"], "G9 Over"
            )

        job_id, job = await _freeze_enqueue_claim(
            database,
            workspace_id=over_ws,
            site_id=site_id,
            delegator_id=seeded["delegator_id"],
            claimant="g9-over-1",
        )
        # The enqueue's lifecycle write (FREEZING + job row) is the
        # expected change, shown separately; the oracle captured after
        # the enqueue must be byte-identical after the refused run.
        pre = await _hostile_effect_snapshot(
            database, workspace_id=over_ws, site_id=site_id
        )
        result = await run_freeze_job(pool, _worker_settings(database), job)
        post = await _hostile_effect_snapshot(
            database, workspace_id=over_ws, site_id=site_id
        )
        assert result.status == "FAILED"
        assert result.error == "SNAPSHOT_OVER_BUDGET"
        # Branch proof: the real preflight count gate fired (not a
        # later cap, not an admission shortcut).
        message, detail = await _materializer_refusal_detail(
            database, workspace_id=over_ws
        )
        assert message == "REVIEW_SNAPSHOT_OVER_BUDGET"
        assert detail == "content type cap"
        # Full no-effects around the refused run.
        assert post == pre
        # Legitimate failed-job bookkeeping, shown separately.
        job_row, state = await _freeze_refusal_state(
            database, workspace_id=over_ws, job_id=job_id
        )
        assert job_row["status"] == "FAILED"
        assert job_row["error"] == "SNAPSHOT_OVER_BUDGET"
        assert state == "FREEZING/0"
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_freeze_stale_catalog_schema_version_refused_no_effects(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """G12/E-S1: trusted stale/malformed component-catalog schema-version
    row -> real freeze SNAPSHOT_VALIDATION_FAILED + no-effects; the
    restored catalog then freezes clean (the gate is distinguished).

    The projection CONSUMER's stale model/view checks are a DIFFERENT
    boundary and are NOT claimed here.  No catalog relaxation: the
    fixture catalog is restored exactly.
    """

    database = agent_site_database
    seeded = await _seed(database)
    site_id = seeded["site_id"]
    workspace_id = seeded["workspace_id"]
    pool = await _worker_pool(database)
    try:
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            original = await owner.fetchval(
                "SELECT definitions FROM control.component_catalog"
            )
        definitions = json.loads(original)
        assert isinstance(definitions, list) and definitions

        async def _catalog_vector(*, tampered: str, claimant: str, detail: str) -> None:
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.execute(
                    "UPDATE control.component_catalog SET definitions = $1::jsonb",
                    tampered,
                )
            job_id, job = await _freeze_enqueue_claim(
                database,
                workspace_id=workspace_id,
                site_id=site_id,
                delegator_id=seeded["delegator_id"],
                claimant=claimant,
            )
            pre = await _hostile_effect_snapshot(
                database, workspace_id=workspace_id, site_id=site_id
            )
            result = await run_freeze_job(pool, _worker_settings(database), job)
            post = await _hostile_effect_snapshot(
                database, workspace_id=workspace_id, site_id=site_id
            )
            assert result.status == "FAILED"
            assert result.error == "SNAPSHOT_VALIDATION_FAILED"
            message, mat_detail = await _materializer_refusal_detail(
                database, workspace_id=workspace_id
            )
            assert message == "SNAPSHOT_VALIDATION_FAILED"
            assert mat_detail == detail
            # Full no-effects around the refused run.
            assert post == pre
            job_row, state = await _freeze_refusal_state(
                database, workspace_id=workspace_id, job_id=job_id
            )
            # Legitimate failed-job bookkeeping, shown separately.
            assert job_row["status"] == "FAILED"
            assert job_row["error"] == "SNAPSHOT_VALIDATION_FAILED"
            assert state == "FREEZING/0"

        # (1) Stale entry schema_version: the stored Image composition
        #     row (schema_version '1') no longer matches the catalog.
        stale = json.loads(original)
        for entry in stale:
            if isinstance(entry, dict) and entry.get("type") == "Image":
                entry["schema_version"] = "2"
        await _catalog_vector(
            tampered=json.dumps(stale, separators=(",", ":")),
            claimant="g12-stale-1",
            detail="composition schema version mismatch",
        )

        # (2) Malformed catalog row: definitions is not the component
        #     array at all.
        await _catalog_vector(
            tampered="{}",
            claimant="g12-malformed-1",
            detail="component catalog missing or malformed",
        )

        # Restore the fixture catalog safely; the real freeze then
        # completes clean, proving the catalog was the only gate.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "UPDATE control.component_catalog SET definitions = $1::jsonb",
                original,
            )
        result, _recover_job = await _freeze_claim_run(
            database,
            workspace_id=workspace_id,
            site_id=site_id,
            delegator_id=seeded["delegator_id"],
            pool=pool,
            claimant="g12-recover-1",
        )
        assert result.status == "SUCCEEDED", result.error
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_freeze_media_reference_row_tamper_matrix(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """E-D3/E-M2 (freeze side): hostile STORED-ROW media-reference
    fixtures.  The public/agent writers already reject these shapes at
    admission; stored-row tampering is the only reach, so these are
    threat fixtures, NOT admitted mutations.

    Each vector: real freeze worker stable refusal (SNAPSHOT_
    VALIDATION_FAILED at the job level) + full before/after no-effects;
    the materializer branch is proven by its own DETAIL.

      (a) required top ref missing       (Image without mediaId)
      (b) non-uuid top ref               (Image.mediaId = 'not-a-uuid')
      (c) dangling same-site typed ref   (valid uuid, no media row)
      (d) nested array-item dangling ref (Gallery items[0].mediaId)
      (d2) malformed nested container    (items not an array)
      (d3) malformed nested item         (items[0] not an object)
      (e) localized field value shape    (translation localized_values;
          properly declared localized field, enabled locale, valid base
          value; only the target translation malformed)
    """

    database = agent_site_database
    seeded = await _seed(database)
    site_id = seeded["site_id"]
    workspace_id = seeded["workspace_id"]
    image_id = seeded["image_id"]
    media_id = seeded["media_id"]
    pool = await _worker_pool(database)
    try:

        async def _image_props(props: dict[str, Any]) -> None:
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.execute(
                    "UPDATE content.page_composition_base"
                    " SET props = $1::jsonb WHERE id = $2",
                    json.dumps(props),
                    image_id,
                )

        async def _tamper_refusal(
            *, claimant: str, expected_message: str, expected_detail: str
        ) -> None:
            job_id, job = await _freeze_enqueue_claim(
                database,
                workspace_id=workspace_id,
                site_id=site_id,
                delegator_id=seeded["delegator_id"],
                claimant=claimant,
            )
            pre = await _hostile_effect_snapshot(
                database, workspace_id=workspace_id, site_id=site_id
            )
            result = await run_freeze_job(pool, _worker_settings(database), job)
            post = await _hostile_effect_snapshot(
                database, workspace_id=workspace_id, site_id=site_id
            )
            assert result.status == "FAILED"
            assert result.error == "SNAPSHOT_VALIDATION_FAILED"
            message, detail = await _materializer_refusal_detail(
                database, workspace_id=workspace_id
            )
            assert message == expected_message
            assert detail == expected_detail
            # Full no-effects around the refused run.
            assert post == pre
            job_row, state = await _freeze_refusal_state(
                database, workspace_id=workspace_id, job_id=job_id
            )
            # Legitimate failed-job bookkeeping, shown separately.
            assert job_row["status"] == "FAILED"
            assert job_row["error"] == "SNAPSHOT_VALIDATION_FAILED"
            assert state == "FREEZING/0"

        # (a) required top ref missing.
        await _image_props({"alt": "Alt"})
        await _tamper_refusal(
            claimant="ed3-a-1",
            expected_message="SNAPSHOT_VALIDATION_FAILED",
            expected_detail="required media reference missing",
        )
        await _image_props({"mediaId": str(media_id), "alt": "Alt"})

        # (b) non-uuid top ref.
        await _image_props({"mediaId": "not-a-uuid", "alt": "Alt"})
        await _tamper_refusal(
            claimant="ed3-b-1",
            expected_message="SNAPSHOT_VALIDATION_FAILED",
            expected_detail="declared media reference not a uuid",
        )
        await _image_props({"mediaId": str(media_id), "alt": "Alt"})

        # (c) dangling same-site typed ref (valid uuid, no media row):
        #     REVIEW_MEDIA_REF_UNRESOLVED mapped to the stable code.
        await _image_props({"mediaId": str(uuid4()), "alt": "Alt"})
        await _tamper_refusal(
            claimant="ed3-c-1",
            expected_message="REVIEW_MEDIA_REF_UNRESOLVED",
            expected_detail=("typed media reference without media_asset row"),
        )
        await _image_props({"mediaId": str(media_id), "alt": "Alt"})

        # (d) nested array-item dangling ref (Gallery).
        gallery_id = uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "INSERT INTO content.page_composition_base (id, site_id,"
                " page_id, component_type, schema_version, parent_id,"
                " slot_key, order_key, props) VALUES ($1,$2,$3,'Gallery',"
                " '1',NULL,'default',9,jsonb_build_object("
                "  'items',jsonb_build_array(jsonb_build_object("
                "   'mediaId',$4::text,'alt','Nested'))))",
                gallery_id,
                site_id,
                seeded["page_id"],
                str(uuid4()),
            )
        await _tamper_refusal(
            claimant="ed3-d-1",
            expected_message="REVIEW_MEDIA_REF_UNRESOLVED",
            expected_detail=("typed media reference without media_asset row"),
        )

        # (d2) malformed nested CONTAINER: items is not an array.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "UPDATE content.page_composition_base"
                " SET props = $1::jsonb WHERE id = $2",
                json.dumps({"items": "not-an-array"}),
                gallery_id,
            )
        await _tamper_refusal(
            claimant="ed3-d2-1",
            expected_message="SNAPSHOT_VALIDATION_FAILED",
            expected_detail="declared media array not an array",
        )

        # (d3) malformed nested ITEM: the array element is not an object.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "UPDATE content.page_composition_base"
                " SET props = $1::jsonb WHERE id = $2",
                json.dumps({"items": ["not-an-object"]}),
                gallery_id,
            )
        await _tamper_refusal(
            claimant="ed3-d3-1",
            expected_message="SNAPSHOT_VALIDATION_FAILED",
            expected_detail="media array item not an object",
        )

        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "DELETE FROM content.page_composition_base WHERE id = $1",
                gallery_id,
            )

        # (e) localized field value malformed shape (translation row):
        #     the base value resolves; the LOCALIZED value is not a
        #     uuid, so the localized closure branch is the one entered.
        type_id = uuid4()
        field_id = uuid4()
        item_id = uuid4()
        translation_id = uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            # Enabled non-default locale for the localized value (the
            # default en-US locale is already enabled by the seed).
            await owner.execute(
                "INSERT INTO content.site_locale_base (site_id, tag,"
                " enabled, is_default, position) VALUES"
                " ($1,'fr',true,false,1)",
                site_id,
            )
            await owner.execute(
                "INSERT INTO content.content_type_base (id, site_id,"
                ' "key", labels, slug_pattern, status,'
                " definition_version, settings) VALUES"
                " ($1,$2,'ed3-media-type',"
                ' \'{"en":"Ed3 media type"}\'::jsonb,'
                " 'ed3/%s','ACTIVE',1,'{}'::jsonb)",
                type_id,
                site_id,
            )
            # The media field is PROPERLY DECLARED localized: a valid
            # enabled locale, a valid base value on the item; ONLY the
            # target translation value is malformed, so the localized
            # closure branch is the one entered.
            await owner.execute(
                "INSERT INTO content.field_definition_base (id, site_id,"
                " type_id, key, label, field_type, required, localized,"
                " cardinality, position, validation, ui_options,"
                " definition_version) VALUES ($1,$2,$3,'media_one','Media',"
                " 'media',true,true,1,0,'{}'::jsonb,'{}'::jsonb,1)",
                field_id,
                site_id,
                type_id,
            )
            await owner.execute(
                "INSERT INTO content.content_item_base (id, site_id,"
                " type_id, slug, status, type_definition_version, values,"
                " row_version) VALUES ($1,$2,$3,'ed3-item','PUBLISHED',1,"
                " jsonb_build_object('media_one',$4::text),1)",
                item_id,
                site_id,
                type_id,
                str(media_id),
            )
            await owner.execute(
                "INSERT INTO content.content_item_translation_base (id,"
                " site_id, item_id, locale, localized_values) VALUES"
                " ($1,$2,$3,'fr',jsonb_build_object("
                "  'media_one','not-a-uuid'))",
                translation_id,
                site_id,
                item_id,
            )
        await _tamper_refusal(
            claimant="ed3-e-1",
            expected_message="SNAPSHOT_VALIDATION_FAILED",
            expected_detail="localized media field value not a uuid",
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "DELETE FROM content.content_item_translation_base WHERE id = $1",
                translation_id,
            )
            await owner.execute(
                "DELETE FROM content.content_item_base WHERE id = $1",
                item_id,
            )
            await owner.execute(
                "DELETE FROM content.field_definition_base WHERE id = $1",
                field_id,
            )
            await owner.execute(
                "DELETE FROM content.content_type_base WHERE id = $1",
                type_id,
            )
            await owner.execute(
                "DELETE FROM content.site_locale_base"
                " WHERE site_id = $1 AND tag = 'fr'",
                site_id,
            )

        # All vectors restored: the real freeze completes clean.
        result, _recover_job = await _freeze_claim_run(
            database,
            workspace_id=workspace_id,
            site_id=site_id,
            delegator_id=seeded["delegator_id"],
            pool=pool,
            claimant="ed3-recover-1",
        )
        assert result.status == "SUCCEEDED", result.error
    finally:
        await pool.close()
