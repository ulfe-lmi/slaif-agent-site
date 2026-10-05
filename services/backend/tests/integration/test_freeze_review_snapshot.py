"""Real PostgreSQL proof for durable freeze jobs and the immutable snapshot."""

from __future__ import annotations

import asyncio
import json
import time
from datetime import timedelta
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.control_api.app import create_app
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.roles import ROLE_NAMES
from slaif_agent_site.review_worker.config import (
    ReviewWorkerDatabaseMode,
    ReviewWorkerSettings,
)
from slaif_agent_site.review_worker.freeze_job import run_freeze_job
from slaif_agent_site.review_worker.snapshot import (
    PUCK_VERSION_PIN,
    build_snapshot_document,
    canonical_json,
)

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
            " '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb)",
            site_id,
        )
        media_id = uuid4()
        await owner.execute(
            "INSERT INTO content.media_asset_base (id, site_id, uploaded_by,"
            " filename, mime_type, size_bytes, content_hash, storage_key,"
            " alt_text, metadata) VALUES ($1,$2,$3,'int.png','image/png',128,"
            " $4, 'sha256/ab/cd/'||$4, 'Alt', '{}'::jsonb)",
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
            " title, delegation_preset, effective_scopes, status, expires_at)"
            " VALUES ($1,$2,$2,'Freeze Workspace','L4',"
            " '[\"page:read\"]'::jsonb,'ACTIVE',now()+interval '1 hour')"
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
    }


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
                    "SELECT * FROM control.slaif_review_job_claim($1)", claimant
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
            "SELECT * FROM control.slaif_review_job_claim($1)",
            "integration-worker-1",
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
    assert payload["state_version"] == "review-snapshot/v1"
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
            "SELECT * FROM control.slaif_review_job_claim($1)",
            "integration-worker-2",
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
            "SELECT * FROM control.slaif_review_job_claim($1)",
            "integration-worker-3",
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
                "SELECT * FROM control.slaif_review_job_claim($1)",
                "freeze-http-worker",
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
