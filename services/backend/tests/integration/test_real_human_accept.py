"""Real PostgreSQL proof for the real human accept path (083/1).

Evidence for order R7.1: the reviewer grant matrix, the kind-aware
claim (both kinds FIFO, DISCARD never claimed by the worker set,
invalid arrays rejected, stale recovery unchanged), the idempotent
REVIEW -> ACCEPT_QUEUED enqueue with its stable codes, the control
accept route authority matrix, and the worker ACCEPT job against a
real PostgreSQL + real foundation + real media store: the success
path (single reviewer transaction, canonical revision +1, exact
audit and outbox rows, public media verified against the digest),
the drift path (SITE_REVISION_CHANGED before any mutation), the
conflict path (structured BASE_ROW_* with full rollback), the
retry/budget behavior, and the crash-replay idempotency (a re-claim
after finalization re-validates and commits exactly once).
"""

# ruff: noqa: E501 -- explicit fixture and SQL contracts

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.agent_state import promotion as promotion_module
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.foundation import asyncpg_cow_session
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.control_api.app import create_app as create_control_app
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.human_authorization import (
    HumanAuthorizationService,
    MembershipChange,
)
from slaif_agent_site.media_service.config import MediaDatabaseMode, MediaSettings
from slaif_agent_site.media_service.database import MediaDatabase
from slaif_agent_site.media_service.finalize import (
    MediaFinalizationRepository,
    finalize_media_for_promotion,
)
from slaif_agent_site.media_service.store import MediaStore, StagedMedia
from slaif_agent_site.review_worker.accept_job import MediaBoundary, run_accept_job
from slaif_agent_site.review_worker.config import (
    ReviewWorkerDatabaseMode,
    ReviewWorkerSettings,
)
from slaif_agent_site.review_worker.freeze_job import run_freeze_job

_AGGON2 = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "AAAAAAAAAAAAAAAAAAAAAA$"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
)
_PNG = b"\x89PNG\r\n\x1a\nreal-human-accept-media"
_WORKER_KINDS = ["FREEZE", "ACCEPT"]

_LONG_LIVED_ROLES = (
    "slaif_control",
    "slaif_editor_runtime",
    "slaif_agent_runtime",
    "slaif_public_reader",
    "slaif_preview_reader",
    "slaif_reviewer",
    "slaif_review_worker",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
)


def _dsn(database: AgentSiteDatabase, user: str, password: str) -> str:
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    return (
        f"postgresql://{quote(user, safe='')}:{quote(password, safe='')}"
        f"@{host}:{database.connection_parameters['port']}/{database.name}"
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


def _control_settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
    login, password = database.credentials["slaif_control"]
    return ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(_dsn(database, login, password)),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=3,
        application_name="accept-integration-control",
    )


def _media_settings(database: AgentSiteDatabase, media_root: Path) -> MediaSettings:
    login, password = database.credentials["slaif_media"]
    return MediaSettings(
        mode=MediaDatabaseMode.TEST,
        dsn=SecretStr(_dsn(database, login, password)),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        media_root=media_root,
        pool_min_size=1,
        pool_max_size=2,
        application_name="accept-integration-media",
    )


def _error_envelope(response: httpx.Response) -> dict[str, Any]:
    """The stable error envelope without the per-request id."""

    body = response.json()
    error = body.get("error", {})
    return {key: value for key, value in error.items() if key != "request_id"} | {
        "operation_id": body.get("operation_id"),
        "details": body.get("details"),
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


def _seed_media_object(media_root: Path) -> tuple[str, str]:
    """Publish the fixture bytes through the real store; (digest, key)."""

    media_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    store = MediaStore(media_root)
    staged_path = store.create_staging_path()
    staged_path.write_bytes(_PNG)
    digest = hashlib.sha256(_PNG).hexdigest()
    key = store.publish(StagedMedia(staged_path, digest, len(_PNG), "image/png"))
    return digest, key


async def _seed_site(
    database: AgentSiteDatabase,
    *,
    media_root: Path | None,
    with_ops: bool,
) -> dict[str, Any]:
    """One site with renderable content; optionally real COW operations.

    ``media_root=None`` seeds the media record without on-disk bytes
    (the enqueue/route/claim tests never finalize media).
    """

    await upgrade(database.settings)
    await reconcile(database.settings)
    media_id = uuid4()
    page_id = uuid4()
    section_id = uuid4()
    heading_id = uuid4()
    image_id = uuid4()
    if media_root is not None:
        media_digest, storage_key = _seed_media_object(media_root)
    else:
        media_digest, storage_key = "cd" * 32, "sha256/cd/d0/" + "cd" * 32
    scopes = [
        "site:read",
        "page:read",
        "component-structure:create",
        "component-content-props:write",
    ]
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        delegator_id = await owner.fetchval(
            """
            INSERT INTO control.user_account (
                id, identity_kind, local_username, local_username_normalized,
                password_hash, display_name, status
            ) VALUES (
                gen_random_uuid(), 'LOCAL', 'Accept.Integration.Delegator',
                'accept.integration.delegator', $1, 'Accept Delegator', 'ACTIVE'
            ) RETURNING id
            """,
            _AGGON2,
        )
        site_id = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name, default_locale,"
            " component_catalog_version) VALUES ('accept-int', 'Accept Int',"
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
        await owner.execute(
            "INSERT INTO content.media_asset_base (id, site_id, uploaded_by,"
            " filename, mime_type, size_bytes, content_hash, storage_key,"
            " alt_text, metadata) VALUES ($1,$2,$3,'accept.png','image/png',$4,"
            " $5, $6, 'Alt', '{}'::jsonb)",
            media_id,
            site_id,
            delegator_id,
            len(_PNG),
            media_digest,
            storage_key,
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
            '  \'{"level":1,"text":"Accept"}\'::jsonb),'
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
            " VALUES ($1,$2,$2,'Accept Workspace','L4',$3::jsonb,'ACTIVE',"
            " now()+interval '1 hour') RETURNING id",
            site_id,
            delegator_id,
            json.dumps(scopes),
        )
        token, public_id, secret_digest = generate_capability_token()
        await owner.execute(
            "INSERT INTO control.capability (workspace_id, public_id,"
            " secret_digest, scopes, expires_at) VALUES ($1,$2,$3,$4::jsonb,"
            " now()+interval '30 minutes')",
            workspace_id,
            public_id,
            secret_digest,
            json.dumps(scopes),
        )
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE public_id = $1", public_id
        )
    ids: dict[str, Any] = {
        "delegator_id": UUID(str(delegator_id)),
        "site_id": UUID(str(site_id)),
        "workspace_id": UUID(str(workspace_id)),
        "capability_id": UUID(str(capability_id)),
        "page_id": page_id,
        "section_id": section_id,
        "heading_id": heading_id,
        "image_id": image_id,
        "media_id": media_id,
        "media_digest": media_digest,
    }
    if with_ops:
        await _apply_cow_operations(database, ids)
    return ids


async def _apply_cow_operations(
    database: AgentSiteDatabase, ids: dict[str, Any]
) -> None:
    """Real agent COW operations: an update + a create (two operations)."""

    agent_pool = await database.role_pool("slaif_agent_runtime")
    try:
        # Operation 1: the update (its own COW session scope).
        async with asyncpg_cow_session(
            agent_pool,
            session_id=ids["workspace_id"],
            operation_id=uuid4(),
        ) as cow:
            await cow.native.execute(
                "SELECT set_config('app.capability_id', $1, true)",
                str(ids["capability_id"]),
            )
            updated = await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_component_update("
                " $1, $2, $3::jsonb, $4)",
                ids["site_id"],
                ids["heading_id"],
                json.dumps({"level": 2, "text": "Promoted heading"}),
                1,
            )
            assert updated is not None
        # Operation 2: the create (a separate COW session scope, so the
        # workspace carries exactly two operations).
        async with asyncpg_cow_session(
            agent_pool,
            session_id=ids["workspace_id"],
            operation_id=uuid4(),
        ) as cow:
            await cow.native.execute(
                "SELECT set_config('app.capability_id', $1, true)",
                str(ids["capability_id"]),
            )
            created = await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_component_create("
                " $1, $2, 'Heading', $3, 'default', NULL, NULL, $4::jsonb)",
                ids["site_id"],
                ids["page_id"],
                ids["section_id"],
                json.dumps({"level": 3, "text": "New promoted node"}),
            )
            assert created is not None
            ids["created_heading_id"] = UUID(str(created["id"]))
    finally:
        await agent_pool.close()


async def _freeze_workspace(
    database: AgentSiteDatabase,
    ids: dict[str, Any],
    pool: asyncpg.Pool[Any],
) -> UUID:
    """Enqueue + claim + run the real freeze job; returns the snapshot id."""

    rows = await _control_call(
        database,
        "SELECT * FROM control.slaif_human_agent_workspace_freeze($1,$2,$3)",
        ids["workspace_id"],
        ids["site_id"],
        ids["delegator_id"],
    )
    assert len(rows) == 1
    job = dict(rows[0])
    claimed = await _worker_call(
        database,
        "SELECT * FROM control.slaif_review_job_claim($1, $2)",
        "accept-test-freeze",
        _WORKER_KINDS,
    )
    assert len(claimed) == 1 and str(claimed[0]["id"]) == str(job["job_id"])
    result = await run_freeze_job(pool, _worker_settings(database), dict(claimed[0]))
    assert result.status == "SUCCEEDED", result.error
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        snapshot_id = await owner.fetchval(
            "SELECT review_snapshot_id FROM control.workspace WHERE id = $1",
            ids["workspace_id"],
        )
    assert snapshot_id is not None
    return UUID(str(snapshot_id))


async def _seed_review_state(
    database: AgentSiteDatabase,
    ids: dict[str, Any],
    *,
    status: str = "REVIEW",
    snapshot_digest: str | None = None,
) -> UUID:
    """Direct COMPLETE snapshot + workspace binding (enqueue/route tests)."""

    snapshot_id = uuid4()
    digest = snapshot_digest or "ab" * 32
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO control.review_snapshot (id, workspace_id, site_id,"
            " status, revision_watermark, versions, normalized_state,"
            " validation_report, media_references, browser_evidence, payload,"
            " digest, created_by) VALUES ($1,$2,$3,'COMPLETE',0,'{}'::jsonb,"
            " '{}'::jsonb,'{}'::jsonb,'[]'::jsonb,'[]'::jsonb,'{}'::jsonb,"
            " $4,'accept-test')",
            snapshot_id,
            ids["workspace_id"],
            ids["site_id"],
            digest,
        )
        await owner.execute(
            "UPDATE control.workspace SET status = $2, review_snapshot_id = $1"
            " WHERE id = $3",
            snapshot_id,
            status,
            ids["workspace_id"],
        )
    return snapshot_id


async def _enqueue_accept(
    database: AgentSiteDatabase, workspace_id: UUID, actor: UUID
) -> list[Any]:
    return await _control_call(
        database,
        "SELECT * FROM control.slaif_workspace_accept($1, $2)",
        workspace_id,
        actor,
    )


async def _claim(
    database: AgentSiteDatabase, claimant: str, kinds: list[str] | None
) -> list[Any]:
    return await _worker_call(
        database,
        "SELECT * FROM control.slaif_review_job_claim($1, $2)",
        claimant,
        kinds,
    )


async def _age_heartbeat(
    database: AgentSiteDatabase, job_id: UUID, seconds: float = 61.0
) -> None:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "UPDATE control.review_job SET last_heartbeat = now() - $1::interval"
            " WHERE id = $2",
            timedelta(seconds=seconds),
            job_id,
        )


async def _workspace_state(
    database: AgentSiteDatabase, workspace_id: UUID
) -> tuple[str, UUID | None]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        row = await owner.fetchrow(
            "SELECT status, review_snapshot_id FROM control.workspace WHERE id = $1",
            workspace_id,
        )
    return str(row["status"]), row["review_snapshot_id"]


async def _manual_finalize(
    database: AgentSiteDatabase,
    media_root: Path,
    ids: dict[str, Any],
) -> list[dict[str, str]]:
    """Crash-replay fixture: finalize the media through the real boundary."""

    media_database = MediaDatabase(_media_settings(database, media_root))
    await media_database.start()
    try:
        repository = MediaFinalizationRepository(media_database)
        manifest = await finalize_media_for_promotion(
            ids["site_id"],
            ids["workspace_id"],
            [ids["media_id"]],
            store=MediaStore(media_root),
            repository=repository,
        )
    finally:
        await media_database.stop()
    return manifest.to_list()


@pytest.mark.asyncio
async def test_reviewer_grant_matrix(agent_site_database: AgentSiteDatabase) -> None:
    """R1: reviewer membership exact (worker + owner-ADMIN); grants exact."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        members = await owner.fetch(
            "SELECT r.rolname, r.rolcanlogin, am.admin_option"
            " FROM pg_auth_members am"
            " JOIN pg_roles m ON m.oid = am.roleid"
            " JOIN pg_roles r ON r.oid = am.member"
            " WHERE m.rolname = 'slaif_reviewer'"
        )
        # Product (non-login) membership is EXACTLY: the worker edge and
        # the owner edge. The owner edge (WITH ADMIN OPTION) is the
        # provisioning invariant that lets migrations running as
        # slaif_owner manage reviewer membership (documented deviation:
        # the only other MEMBER of slaif_reviewer is the owner). Fixture
        # logins holding the reviewer role are test scaffolding.
        product_members = {
            (str(row["rolname"]), bool(row["admin_option"]))
            for row in members
            if not row["rolcanlogin"]
        }
        assert product_members == {
            ("slaif_review_worker", False),
            ("slaif_owner", True),
        }

        for role in _LONG_LIVED_ROLES:
            promotion_insert = await owner.fetchval(
                "SELECT has_table_privilege($1, 'audit.promotion', 'INSERT')",
                role,
            )
            promotion_select = await owner.fetchval(
                "SELECT has_table_privilege($1, 'audit.promotion', 'SELECT')",
                role,
            )
            promotion_update = await owner.fetchval(
                "SELECT has_table_privilege($1, 'audit.promotion', 'UPDATE')",
                role,
            )
            promotion_delete = await owner.fetchval(
                "SELECT has_table_privilege($1, 'audit.promotion', 'DELETE')",
                role,
            )
            assert promotion_insert is (role == "slaif_review_worker")
            # The worker holds its INSERT directly; the SELECT is granted
            # to slaif_reviewer and is NOT visible to the worker because
            # the worker role is NOINHERIT (effective authority of the
            # worker login is checked separately via has_function/table
            # privileges on the granted objects).
            assert promotion_select is (role == "slaif_reviewer")
            assert promotion_update is False
            assert promotion_delete is False
            outbox_insert = await owner.fetchval(
                "SELECT has_table_privilege($1, 'control.cache_outbox', 'INSERT')",
                role,
            )
            outbox_select = await owner.fetchval(
                "SELECT has_table_privilege($1, 'control.cache_outbox', 'SELECT')",
                role,
            )
            assert outbox_insert is (role == "slaif_review_worker")
            assert outbox_select is (role == "slaif_review_worker")

        for role in _LONG_LIVED_ROLES:
            sequence_usage = await owner.fetchval(
                "SELECT has_sequence_privilege($1,"
                " 'control.cache_outbox_id_seq', 'USAGE')",
                role,
            )
            assert sequence_usage is (role == "slaif_review_worker")

        for table in ("promotion", "cache_outbox"):
            public_grants = await owner.fetch(
                "SELECT grantee FROM information_schema.table_privileges"
                " WHERE table_name = $1 AND grantee = 'PUBLIC'",
                table,
            )
            assert public_grants == []

        for role in _LONG_LIVED_ROLES + ("public",):
            claim_execute = await owner.fetchval(
                "SELECT has_function_privilege($1,"
                " 'control.slaif_review_job_claim(text, text[])', 'EXECUTE')",
                role,
            )
            assert claim_execute is (role == "slaif_review_worker")
            accept_execute = await owner.fetchval(
                "SELECT has_function_privilege($1,"
                " 'control.slaif_workspace_accept(uuid, uuid)', 'EXECUTE')",
                role,
            )
            assert accept_execute is (role == "slaif_control")
            human_accept_execute = await owner.fetchval(
                "SELECT has_function_privilege($1,"
                " 'control.slaif_human_agent_workspace_accept(uuid, uuid,"
                " uuid, text, uuid)', 'EXECUTE')",
                role,
            )
            assert human_accept_execute is (role == "slaif_control")

        # The exact R1.6 additions on the worker (SELECTs pre-date 072_001).
        assert (
            await owner.fetchval(
                "SELECT has_table_privilege('slaif_review_worker',"
                " 'control.workspace', 'UPDATE')"
            )
            is True
        )
        assert (
            await owner.fetchval(
                "SELECT has_table_privilege('slaif_review_worker',"
                " 'control.site', 'UPDATE')"
            )
            is True
        )
        assert (
            await owner.fetchval(
                "SELECT has_table_privilege('slaif_review_worker',"
                " 'control.review_snapshot', 'SELECT')"
            )
            is True
        )

        # The worker's foundation reviewer surface (072_001 section 7):
        # the same agentcow USAGE + 13 controlled function EXECUTEs the
        # hardening grants to slaif_reviewer, held by NO other
        # long-lived role (the owner is the function/schema owner and
        # holds implicit privileges).
        foundation_functions = (
            "agentcow.get_cow_dirty_tables(text, uuid)",
            "agentcow.get_cow_primary_key_columns(text, text)",
            "agentcow.get_cow_session_operations(text, uuid)",
            "agentcow.get_cow_dependencies(text, uuid)",
            "agentcow._cow_fk_edges(text, text[])",
            "agentcow.get_cow_conflicts(text, text, text[], uuid, uuid[], boolean)",
            "agentcow.commit_cow(text, text, text[], uuid, uuid[], text)",
            "agentcow.commit_cow_upsert(text, text, text[], uuid, uuid[], text)",
            "agentcow.commit_cow_delete(text, text, text[], uuid, uuid[], text)",
            "agentcow.commit_cow_cleanup(text, text, uuid, uuid[])",
            "agentcow.discard_cow(text, text, uuid, uuid[])",
            "agentcow._cow_lock_session(text, uuid)",
            "agentcow._cow_operation_tables(text, uuid, uuid[])",
        )
        for function in foundation_functions:
            holders = {
                str(row["rolname"])
                for row in await owner.fetch(
                    "SELECT r.rolname FROM pg_roles r"
                    " WHERE r.rolname LIKE 'slaif%'"
                    " AND has_function_privilege(r.rolname, $1, 'EXECUTE')",
                    function,
                )
            }
            assert holders == {
                "slaif_owner",
                "slaif_reviewer",
                "slaif_review_worker",
            }, function
        usage_holders = {
            str(row["rolname"])
            for row in await owner.fetch(
                "SELECT r.rolname FROM pg_roles r"
                " WHERE r.rolname LIKE 'slaif%'"
                " AND has_schema_privilege(r.rolname, 'agentcow', 'USAGE')"
            )
        }
        assert usage_holders == {
            "slaif_owner",
            "slaif_reviewer",
            "slaif_review_worker",
        }


@pytest.mark.asyncio
async def test_kind_aware_claim_and_stale_recovery(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R1.2: both kinds FIFO, DISCARD unclaimed, invalid arrays rejected."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    workspace_id = ids["workspace_id"]
    freeze_job = uuid4()
    accept_job = uuid4()
    discard_job = uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.executemany(
            "INSERT INTO control.review_job (id, workspace_id, site_id,"
            " job_kind, status, created_at) VALUES ($1,$2,$3,$4,'QUEUED',$5)",
            [
                (
                    freeze_job,
                    workspace_id,
                    ids["site_id"],
                    "FREEZE",
                    datetime.fromisoformat("2026-10-05 00:00:01+00"),
                ),
                (
                    accept_job,
                    workspace_id,
                    ids["site_id"],
                    "ACCEPT",
                    datetime.fromisoformat("2026-10-05 00:00:02+00"),
                ),
                (
                    discard_job,
                    workspace_id,
                    ids["site_id"],
                    "DISCARD",
                    datetime.fromisoformat("2026-10-05 00:00:03+00"),
                ),
            ],
        )

    rows = await _claim(database, "kind-test-1", _WORKER_KINDS)
    assert [str(row["id"]) for row in rows] == [str(freeze_job)]
    assert rows[0]["attempt_count"] == 1

    rows = await _claim(database, "kind-test-2", _WORKER_KINDS)
    assert [str(row["id"]) for row in rows] == [str(accept_job)]

    rows = await _claim(database, "kind-test-3", _WORKER_KINDS)
    assert rows == []
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert (
            await owner.fetchval(
                "SELECT status FROM control.review_job WHERE id = $1", discard_job
            )
            == "QUEUED"
        )

    # The worker set never claims DISCARD; an explicit DISCARD-only set may.
    rows = await _claim(database, "kind-test-4", ["DISCARD"])
    assert [str(row["id"]) for row in rows] == [str(discard_job)]

    for bad_kinds in (["FREEZE", "BOGUS"], ["BOGUS"], [], None):
        with pytest.raises(asyncpg.PostgresError) as excinfo:
            await _claim(database, "kind-test-5", bad_kinds)
        assert "REVIEW_CLAIM_KIND_INVALID" in str(excinfo.value)
    with pytest.raises(asyncpg.PostgresError) as excinfo:
        await _claim(database, "bad claimant!", _WORKER_KINDS)
    assert "REVIEW_CLAIMANT_INVALID" in str(excinfo.value)

    # Stale recovery is unchanged: the claimed ACCEPT job re-queues.
    await _age_heartbeat(database, accept_job)
    rows = await _claim(database, "kind-recover-1", _WORKER_KINDS)
    assert [str(row["id"]) for row in rows] == [str(accept_job)]
    assert rows[0]["attempt_count"] == 2
    assert rows[0]["claimed_by"] == "kind-recover-1"


@pytest.mark.asyncio
async def test_accept_enqueue_idempotency_and_stable_codes(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R1.3: idempotent enqueue, exact payload, every stable code."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    workspace_id = ids["workspace_id"]
    actor = ids["delegator_id"]
    snapshot_id = await _seed_review_state(database, ids)

    rows = await _enqueue_accept(database, workspace_id, actor)
    assert len(rows) == 1
    job_id = UUID(str(rows[0]["job_id"]))
    # The enqueue returns the JOB status (R1.3: (job_id, status)); the
    # workspace transition is asserted separately below.
    assert str(rows[0]["status"]) == "QUEUED"
    status, bound = await _workspace_state(database, workspace_id)
    assert (status, bound) == ("ACCEPT_QUEUED", snapshot_id)

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        payload = await owner.fetchval(
            "SELECT payload FROM control.review_job WHERE id = $1", job_id
        )
    assert json.loads(payload) == {
        "snapshot_id": str(snapshot_id),
        "site_id": str(ids["site_id"]),
        "actor_user_account_id": str(actor),
    }

    # Idempotent while QUEUED.
    again = await _enqueue_accept(database, workspace_id, actor)
    assert str(again[0]["job_id"]) == str(job_id)

    # Idempotent while CLAIMED.
    claimed = await _claim(database, "enqueue-test-claim", _WORKER_KINDS)
    assert len(claimed) == 1 and str(claimed[0]["id"]) == str(job_id)
    claimed_again = await _enqueue_accept(database, workspace_id, actor)
    assert str(claimed_again[0]["job_id"]) == str(job_id)

    # WORKSPACE_NOT_IN_REVIEW for every non-REVIEW status (P0002 = the
    # uniform 404 class at the route).
    for target_status in ("ACTIVE", "ACCEPTED", "CONFLICTED"):
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.review_job SET status = 'SUCCEEDED' WHERE id = $1",
                job_id,
            )
            await owner.execute(
                "UPDATE control.workspace SET status = $1 WHERE id = $2",
                target_status,
                workspace_id,
            )
        with pytest.raises(asyncpg.PostgresError) as excinfo:
            await _enqueue_accept(database, workspace_id, actor)
        assert excinfo.value.sqlstate == "P0002"
        assert "WORKSPACE_NOT_IN_REVIEW" in str(excinfo.value)

    # WORKSPACE_NOT_FOUND for an unknown workspace.
    with pytest.raises(asyncpg.PostgresError) as excinfo:
        await _enqueue_accept(database, uuid4(), actor)
    assert excinfo.value.sqlstate == "P0002"
    assert "WORKSPACE_NOT_FOUND" in str(excinfo.value)

    # REVIEW_SNAPSHOT_NOT_FOUND: REVIEW without a bound COMPLETE snapshot.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "UPDATE control.workspace SET status = 'REVIEW',"
            " review_snapshot_id = NULL WHERE id = $1",
            workspace_id,
        )
    with pytest.raises(asyncpg.PostgresError) as excinfo:
        await _enqueue_accept(database, workspace_id, actor)
    assert excinfo.value.sqlstate == "P0002"
    assert "REVIEW_SNAPSHOT_NOT_FOUND" in str(excinfo.value)

    # REVIEW_SNAPSHOT_NOT_FOUND: bound to a non-existent snapshot.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "UPDATE control.workspace SET review_snapshot_id = $1 WHERE id = $2",
            uuid4(),
            workspace_id,
        )
    with pytest.raises(asyncpg.PostgresError) as excinfo:
        await _enqueue_accept(database, workspace_id, actor)
    assert "REVIEW_SNAPSHOT_NOT_FOUND" in str(excinfo.value)


def _accept_headers(session: Any) -> dict[str, str]:
    return {
        "cookie": (
            f"slaif_session={session.token.get_secret_value()}; "
            f"slaif_csrf={session.csrf_token.get_secret_value()}"
        ),
        "X-CSRF-Token": session.csrf_token.get_secret_value(),
    }


async def _create_user(database: AgentSiteDatabase, name: str) -> UUID:
    user_id = uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO control.user_account (id, identity_kind,"
            " oidc_issuer, oidc_subject, display_name, status)"
            " VALUES ($1, 'OIDC', 'accept-int', $2, $3, 'ACTIVE')",
            user_id,
            str(uuid4()),
            name,
        )
    return user_id


@pytest.mark.asyncio
async def test_control_accept_route_authority_matrix(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R2.2-R2.4: dual permission, recent auth, binding, strict body."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    site_id = ids["site_id"]
    workspace_id = ids["workspace_id"]
    digest = "ef" * 32
    snapshot_id = await _seed_review_state(database, ids, snapshot_digest=digest)

    # A second site (wrong-binding case) and an ACTIVE workspace (409 case).
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        other_site = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name, default_locale,"
            " component_catalog_version) VALUES ('accept-int-other', 'Other',"
            " 'en-US', 'catalog-v1') RETURNING id"
        )
        active_ws = await owner.fetchval(
            "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
            " title, delegation_preset, effective_scopes, status, expires_at)"
            " VALUES ($1,$2,$2,'Accept Active WS','L4','[\"page:read\"]'::jsonb,"
            " 'ACTIVE', now()+interval '1 hour') RETURNING id",
            site_id,
            ids["delegator_id"],
        )
        # 409 fixture: bound COMPLETE snapshot but no live ACCEPT job and a
        # non-REVIEW status (the enqueue's status gate must fire).
        conflict_ws = await owner.fetchval(
            "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
            " title, delegation_preset, effective_scopes, status, expires_at)"
            " VALUES ($1,$2,$2,'Accept Conflict WS','L4','[\"page:read\"]'::jsonb,"
            " 'REVIEW', now()+interval '1 hour') RETURNING id",
            site_id,
            ids["delegator_id"],
        )
        conflict_snapshot = uuid4()
        await owner.execute(
            "INSERT INTO control.review_snapshot (id, workspace_id, site_id,"
            " status, revision_watermark, versions, normalized_state,"
            " validation_report, media_references, browser_evidence, payload,"
            " digest, created_by) VALUES ($1,$2,$3,'COMPLETE',0,'{}'::jsonb,"
            " '{}'::jsonb,'{}'::jsonb,'[]'::jsonb,'[]'::jsonb,'{}'::jsonb,"
            " $4,'accept-test')",
            conflict_snapshot,
            conflict_ws,
            site_id,
            digest,
        )
        await owner.execute(
            "UPDATE control.workspace SET status = 'ACCEPT_QUEUED',"
            " review_snapshot_id = $1 WHERE id = $2",
            conflict_snapshot,
            conflict_ws,
        )

    users: dict[str, UUID] = {}
    for key in ("owner", "deny_accept", "deny_publish", "outsider", "admin"):
        users[key] = await _create_user(database, f"Accept {key}")
    control_pool = await database.role_pool("slaif_control")
    authorization = HumanAuthorizationService(control_pool)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO control.platform_administrator (user_account_id) VALUES ($1)",
            users["admin"],
        )
    await authorization.put_membership(
        users["admin"],
        site_id,
        users["owner"],
        MembershipChange(role_key="SITE_OWNER", delegation_ceiling=4),
    )
    await authorization.put_membership(
        users["admin"],
        site_id,
        users["deny_accept"],
        MembershipChange(
            role_key="SITE_OWNER",
            delegation_ceiling=4,
            deny_permissions=frozenset({"workspace:accept"}),
        ),
    )
    await authorization.put_membership(
        users["admin"],
        site_id,
        users["deny_publish"],
        MembershipChange(
            role_key="SITE_OWNER",
            delegation_ceiling=4,
            deny_permissions=frozenset({"site:publish"}),
        ),
    )
    adapter = ControlDatabase(_control_settings(database))
    await adapter.start()
    control_app = create_control_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST), database=adapter
    )
    sessions: dict[str, Any] = {}
    try:
        for key in users:
            sessions[key] = await adapter.human_session_service().create(users[key])

        async def post(
            session: Any,
            body: dict[str, Any],
            *,
            site: UUID = site_id,
            workspace: UUID = workspace_id,
            bearer: str | None = None,
        ) -> httpx.Response:
            headers = (
                {"Authorization": f"Bearer {bearer}"}
                if bearer is not None
                else _accept_headers(session)
            )
            path = f"/api/control/v1/sites/{site}/workspaces/{workspace}/accept/"
            return await client.post(path, json=body, headers=headers)

        valid_body = {
            "snapshot_id": str(snapshot_id),
            "digest": digest,
            "acknowledge_summary": True,
        }
        async with control_app.router.lifespan_context(control_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=control_app),
                base_url="http://control.test",
            ) as client:
                # Positive: dual permission + recent auth -> 202.
                response = await post(sessions["owner"], valid_body)
                assert response.status_code == 202, response.text
                first_body = response.json()
                job_id = first_body["job_id"]
                assert first_body["status"] == "ACCEPT_QUEUED"
                status, bound = await _workspace_state(database, workspace_id)
                assert (status, bound) == ("ACCEPT_QUEUED", snapshot_id)

                # Idempotent duplicate while the job is live: SAME job id.
                duplicate = await post(sessions["owner"], valid_body)
                assert duplicate.status_code == 202, duplicate.text
                assert duplicate.json() == first_body

                # The platform administrator path reaches the same job.
                admin_post = await post(sessions["admin"], valid_body)
                assert admin_post.status_code == 202, admin_post.text
                assert admin_post.json()["job_id"] == job_id

                # Each permission individually missing -> uniform 404.
                for key in ("deny_accept", "deny_publish", "outsider"):
                    denied = await post(sessions[key], valid_body)
                    assert denied.status_code == 404, (key, denied.text)

                # Recent auth absent -> 401 class.
                stale_user = users["owner"]
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    # Backdate created_at as well: the session was
                    # created seconds ago, and user_session_time_order
                    # requires created_at <= recent_auth_at.
                    await owner.execute(
                        "UPDATE control.user_session SET"
                        " created_at = now() - interval '1 hour',"
                        " recent_auth_at = now() - interval '901 seconds'"
                        " WHERE user_account_id = $1",
                        stale_user,
                    )
                stale = await post(sessions["owner"], valid_body)
                assert stale.status_code == 401, stale.text
                # Refresh recent auth for the remaining cases.
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    await owner.execute(
                        "UPDATE control.user_session SET recent_auth_at = now()"
                        " WHERE user_account_id = $1",
                        stale_user,
                    )

                # Wrong site binding -> uniform 404.
                binding = await post(
                    sessions["owner"], valid_body, site=UUID(str(other_site))
                )
                assert binding.status_code == 404, binding.text

                # Snapshot/digest mismatch -> uniform 404, pairwise
                # indistinguishable from the not-found cases.
                bad_snapshot = await post(
                    sessions["owner"],
                    {**valid_body, "snapshot_id": str(uuid4())},
                )
                bad_digest = await post(
                    sessions["owner"],
                    {**valid_body, "digest": "00" * 32},
                )
                assert bad_snapshot.status_code == 404, bad_snapshot.text
                assert bad_digest.status_code == 404, bad_digest.text
                # Indistinguishable apart from the per-request id: the
                # stable envelope (code/message/details) is byte-identical.
                assert _error_envelope(bad_snapshot) == _error_envelope(bad_digest)
                assert _error_envelope(bad_snapshot) == _error_envelope(binding)

                # Strict body: 422 for every malformed acknowledgement.
                for bad_body in (
                    {**valid_body, "acknowledge_summary": False},
                    {**valid_body, "acknowledge_summary": 1},
                    {
                        "snapshot_id": str(snapshot_id),
                        "digest": digest,
                    },
                    {**valid_body, "extra": True},
                ):
                    rejected = await post(sessions["owner"], bad_body)
                    assert rejected.status_code == 422, (bad_body, rejected.text)

                # No agent-facing accept: a capability Bearer token on the
                # control route is a uniform authentication denial.
                token, _public_id, _secret_digest = generate_capability_token()
                agent_bearer = await post(sessions["owner"], valid_body, bearer=token)
                assert agent_bearer.status_code == 401, agent_bearer.text
                no_cookie = await client.post(
                    f"/api/control/v1/sites/{site_id}"
                    f"/workspaces/{workspace_id}/accept/",
                    json=valid_body,
                )
                assert no_cookie.status_code == 401, no_cookie.text

                # WORKSPACE_NOT_IN_REVIEW -> 409 through the route.
                conflict = await post(
                    sessions["owner"],
                    {
                        "snapshot_id": str(conflict_snapshot),
                        "digest": digest,
                        "acknowledge_summary": True,
                    },
                    workspace=UUID(str(conflict_ws)),
                )
                assert conflict.status_code == 409, conflict.text

                # An ACTIVE workspace without a snapshot: the snapshot
                # expectation fails closed to the uniform 404 class.
                active_ws_response = await post(
                    sessions["owner"],
                    {**valid_body, "snapshot_id": str(uuid4())},
                    workspace=UUID(str(active_ws)),
                )
                assert active_ws_response.status_code == 404, active_ws_response.text
    finally:
        await adapter.stop()
        await control_pool.close()


async def _worker_pool(database: AgentSiteDatabase) -> asyncpg.Pool[Any]:
    login, password = database.credentials["slaif_review_worker"]
    return await asyncpg.create_pool(
        dsn=_dsn(database, login, password), min_size=1, max_size=2
    )


async def _claim_accept(database: AgentSiteDatabase, claimant: str) -> dict[str, Any]:
    rows = await _claim(database, claimant, _WORKER_KINDS)
    assert len(rows) == 1
    assert rows[0]["job_kind"] == "ACCEPT"
    return dict(rows[0])


def _public_path(media_root: Path, digest: str) -> Path:
    return media_root / "public" / "sha256" / digest[:2] / digest[2:4] / digest


def _private_path(media_root: Path, digest: str) -> Path:
    return media_root / "sha256" / digest[:2] / digest[2:4] / digest


@pytest.mark.asyncio
async def test_accept_worker_success_path(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """R3.9/R7.1: the single reviewer transaction publishes for real."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            base_revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
        assert base_revision == 0

        snapshot_id = await _freeze_workspace(database, ids, pool)
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            snapshot = await owner.fetchrow(
                "SELECT digest, versions, media_references FROM"
                " control.review_snapshot WHERE id = $1",
                snapshot_id,
            )
        stored_digest = str(snapshot["digest"])
        stored_versions = json.loads(snapshot["versions"])
        media_references = json.loads(snapshot["media_references"])
        assert [ref["id"] for ref in media_references] == [str(ids["media_id"])]

        rows = await _enqueue_accept(database, ids["workspace_id"], ids["delegator_id"])
        job_id = UUID(str(rows[0]["job_id"]))
        job = await _claim_accept(database, "accept-success-1")
        assert str(job["id"]) == str(job_id)
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "SUCCEEDED", result.error

        digest = ids["media_digest"]
        public_key = f"public/sha256/{digest[:2]}/{digest[2:4]}/{digest}"
        manifest = [
            {
                "media_id": str(ids["media_id"]),
                "digest": digest,
                "public_key": public_key,
            }
        ]
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            workspace = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                ids["workspace_id"],
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
            audit_rows = await owner.fetch("SELECT * FROM audit.promotion ORDER BY id")
            outbox_rows = await owner.fetch(
                "SELECT * FROM control.cache_outbox ORDER BY id"
            )
            media_row = await owner.fetchrow(
                "SELECT public_status, published_at FROM"
                " content.media_asset_base WHERE id = $1",
                ids["media_id"],
            )
            heading_props = await owner.fetchval(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
            created_row = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["created_heading_id"],
            )
        assert revision == base_revision + 1
        assert str(workspace["status"]) == "ACCEPTED"
        assert workspace["accepted_at"] is not None
        assert job_row["status"] == "SUCCEEDED"
        assert job_row["error"] is None

        # Exactly one promotion audit row, with the exact R1.4 fields.
        assert len(audit_rows) == 1
        audit = audit_rows[0]
        assert str(audit["site_id"]) == str(ids["site_id"])
        assert str(audit["workspace_id"]) == str(ids["workspace_id"])
        assert str(audit["snapshot_id"]) == str(snapshot_id)
        assert str(audit["job_id"]) == str(job_id)
        assert str(audit["digest"]) == stored_digest
        assert audit["base_site_revision"] == base_revision
        assert audit["new_canonical_revision"] == base_revision + 1
        assert audit["committed_operations"] == 2
        assert json.loads(audit["versions"]) == stored_versions
        assert str(audit["actor_user_account_id"]) == str(ids["delegator_id"])
        assert audit["created_at"] is not None

        # Exactly one unconsumed cache-outbox row with the exact payload.
        assert len(outbox_rows) == 1
        outbox = outbox_rows[0]
        assert str(outbox["site_id"]) == str(ids["site_id"])
        assert str(outbox["workspace_id"]) == str(ids["workspace_id"])
        assert outbox["event_kind"] == "WORKSPACE_ACCEPTED"
        assert json.loads(outbox["payload"]) == {
            "snapshot_id": str(snapshot_id),
            "digest": stored_digest,
            "base_site_revision": base_revision,
            "new_canonical_revision": base_revision + 1,
            "media_manifest": manifest,
        }

        # The session's COW operations landed in canonical.
        assert json.loads(heading_props) == {
            "level": 2,
            "text": "Promoted heading",
        }
        assert created_row is not None
        assert json.loads(created_row["props"]) == {
            "level": 3,
            "text": "New promoted node",
        }

        # Media finalization: canonical row public + verified public bytes.
        assert str(media_row["public_status"]) == "public"
        assert media_row["published_at"] is not None
        public_path = _public_path(media_root, digest)
        assert public_path.is_file()
        assert hashlib.sha256(public_path.read_bytes()).hexdigest() == digest
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_accept_worker_drift_zero_mutation(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """R3.8a/R7.1: SITE_REVISION_CHANGED before any mutation."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, tmp_path / "media"))
    try:
        snapshot_id = await _freeze_workspace(database, ids, pool)
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            stored_digest = await owner.fetchval(
                "SELECT digest FROM control.review_snapshot WHERE id = $1",
                snapshot_id,
            )
            await owner.execute(
                "UPDATE control.site SET canonical_revision = canonical_revision"
                " + 1 WHERE id = $1",
                ids["site_id"],
            )
            bumped = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )

        rows = await _enqueue_accept(database, ids["workspace_id"], ids["delegator_id"])
        job_id = UUID(str(rows[0]["job_id"]))
        job = await _claim_accept(database, "accept-drift-1")
        assert str(job["id"]) == str(job_id)
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "FAILED"
        assert result.error == "SITE_REVISION_CHANGED"

        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            workspace = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                ids["workspace_id"],
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
            audit_count = await owner.fetchval("SELECT count(*) FROM audit.promotion")
            outbox_count = await owner.fetchval(
                "SELECT count(*) FROM control.cache_outbox"
            )
            snapshot_digest = await owner.fetchval(
                "SELECT digest FROM control.review_snapshot WHERE id = $1",
                snapshot_id,
            )
            media_row = await owner.fetchrow(
                "SELECT public_status, published_at FROM"
                " content.media_asset_base WHERE id = $1",
                ids["media_id"],
            )
        # Zero mutation: the manual bump stands alone; nothing else moved.
        assert revision == bumped
        assert str(workspace["status"]) == "REVIEW"
        assert workspace["accepted_at"] is None
        assert job_row["status"] == "FAILED"
        assert job_row["error"] == "SITE_REVISION_CHANGED"
        assert audit_count == 0
        assert outbox_count == 0
        assert snapshot_digest == stored_digest
        assert str(media_row["public_status"]) == "private"
        assert media_row["published_at"] is None
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_accept_worker_conflict_full_rollback(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """R3.8d/R7.1: structured BASE_ROW_* code, full rollback."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        await _freeze_workspace(database, ids, pool)
        rows = await _enqueue_accept(database, ids["workspace_id"], ids["delegator_id"])
        job_id = UUID(str(rows[0]["job_id"]))
        job = await _claim_accept(database, "accept-conflict-1")
        assert str(job["id"]) == str(job_id)

        # A concurrent canonical edit to the exact row the session's update
        # operation touched: invisible to the session's COW view (the digest
        # still matches), detected by the foundation at commit.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "UPDATE content.page_composition_base SET props ="
                ' \'{"level":1,"text":"Concurrent canonical edit"}\'::jsonb'
                " WHERE id = $1",
                ids["heading_id"],
            )
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "FAILED"
        assert result.error == "BASE_ROW_CHANGED"

        digest = ids["media_digest"]
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            workspace = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                ids["workspace_id"],
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
            audit_count = await owner.fetchval("SELECT count(*) FROM audit.promotion")
            outbox_count = await owner.fetchval(
                "SELECT count(*) FROM control.cache_outbox"
            )
            heading_props = await owner.fetchval(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
            change_count = await owner.fetchval(
                "SELECT count(*) FROM content.page_composition_changes WHERE"
                " session_id = $1",
                ids["workspace_id"],
            )
            media_row = await owner.fetchrow(
                "SELECT public_status, published_at FROM"
                " content.media_asset_base WHERE id = $1",
                ids["media_id"],
            )
        # Full rollback: canonical untouched, no audit, no outbox.
        assert revision == 0
        assert str(workspace["status"]) == "CONFLICTED"
        assert workspace["accepted_at"] is None
        assert job_row["status"] == "FAILED"
        assert job_row["error"] == "BASE_ROW_CHANGED"
        assert audit_count == 0
        assert outbox_count == 0
        assert json.loads(heading_props) == {
            "level": 1,
            "text": "Concurrent canonical edit",
        }
        # The session's COW operations survive for re-freeze (083/2).
        assert change_count >= 2
        # Finalization already ran before the commit (079/1 semantics): the
        # public bytes exist, at most unreferenced public objects for GC.
        assert str(media_row["public_status"]) == "public"
        assert media_row["published_at"] is not None
        assert _public_path(media_root, digest).is_file()
    finally:
        await boundary.stop()
        await pool.close()


def _restore_media_object(media_root: Path) -> tuple[str, str]:
    """Re-publish identical bytes after a fixture deletion (idempotent)."""

    store = MediaStore(media_root)
    staged_path = store.create_staging_path()
    staged_path.write_bytes(_PNG)
    digest = hashlib.sha256(_PNG).hexdigest()
    store.publish(StagedMedia(staged_path, digest, len(_PNG), "image/png"))
    return digest, f"sha256/{digest[:2]}/{digest[2:4]}/{digest}"


@pytest.mark.asyncio
async def test_accept_worker_retryable_rollback_and_budget(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """R3.8b/R7.1: retryable failure re-queues; budget terminates safe."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        await _freeze_workspace(database, ids, pool)
        rows = await _enqueue_accept(database, ids["workspace_id"], ids["delegator_id"])
        job_id = UUID(str(rows[0]["job_id"]))
        digest = ids["media_digest"]

        # Attempt 1: the private bytes are missing -> store_unavailable is
        # retryable: NO terminal, the job stays CLAIMED, the workspace goes
        # back to ACCEPT_QUEUED for stale-claim recovery.
        job = await _claim_accept(database, "accept-retry-1")
        assert str(job["id"]) == str(job_id)
        _private_path(media_root, digest).unlink()
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "ROLLED_BACK"
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
            workspace_status = await owner.fetchval(
                "SELECT status FROM control.workspace WHERE id = $1",
                ids["workspace_id"],
            )
        assert job_row["status"] == "CLAIMED"
        assert job_row["error"] is None
        assert workspace_status == "ACCEPT_QUEUED"

        # Restore the bytes (the healed retry state), then walk the attempt
        # budget: 1 -> 2 -> 3 (= max_attempts).
        _restore_media_object(media_root)
        await _age_heartbeat(database, job_id)
        job = await _claim_accept(database, "accept-retry-2")
        assert job["attempt_count"] == 2
        await _age_heartbeat(database, job_id)
        job = await _claim_accept(database, "accept-retry-3")
        assert job["attempt_count"] == 3

        # Attempt 3 = max: a retryable failure now terminates at the budget
        # with the workspace returned to REVIEW (no dead end).
        _private_path(media_root, digest).unlink()
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "FAILED"
        assert result.error == "REVIEW_JOB_STALE_AT_BUDGET"
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
            workspace_status = await owner.fetchval(
                "SELECT status FROM control.workspace WHERE id = $1",
                ids["workspace_id"],
            )
            audit_count = await owner.fetchval("SELECT count(*) FROM audit.promotion")
            outbox_count = await owner.fetchval(
                "SELECT count(*) FROM control.cache_outbox"
            )
        assert job_row["status"] == "FAILED"
        assert job_row["error"] == "REVIEW_JOB_STALE_AT_BUDGET"
        assert workspace_status == "REVIEW"
        assert audit_count == 0
        assert outbox_count == 0
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_accept_worker_crash_replay_idempotent(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """R3.10/R7.1: crash between finalize and commit replays once.

    The fixture simulates the real crash window: the claimed worker marks
    the workspace PROMOTING, finalizes the media (public bytes exist, the
    canonical media row is marked public), and then dies before the
    promotion transaction. Stale-claim recovery re-queues the job; the
    replay must re-validate (the private -> public media flip is the
    idempotent signature) and commit exactly once.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        await _freeze_workspace(database, ids, pool)
        rows = await _enqueue_accept(database, ids["workspace_id"], ids["delegator_id"])
        job_id = UUID(str(rows[0]["job_id"]))
        digest = ids["media_digest"]

        job = await _claim_accept(database, "accept-crash-1")
        assert str(job["id"]) == str(job_id)
        # The crashed worker's last durable action: PROMOTING + finalization.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "UPDATE control.workspace SET status = 'PROMOTING' WHERE id = $1",
                ids["workspace_id"],
            )
        manual_manifest = await _manual_finalize(database, media_root, ids)
        assert manual_manifest == [
            {
                "media_id": str(ids["media_id"]),
                "digest": digest,
                "public_key": (f"public/sha256/{digest[:2]}/{digest[2:4]}/{digest}"),
            }
        ]
        assert _public_path(media_root, digest).is_file()

        # The crash: no terminal, the heartbeat goes stale, recovery
        # re-queues, a second worker claims (attempt 2) and replays.
        await _age_heartbeat(database, job_id)
        job = await _claim_accept(database, "accept-replay-2")
        assert str(job["id"]) == str(job_id)
        assert job["attempt_count"] == 2
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "SUCCEEDED", result.error

        public_key = f"public/sha256/{digest[:2]}/{digest[2:4]}/{digest}"
        manifest = [
            {
                "media_id": str(ids["media_id"]),
                "digest": digest,
                "public_key": public_key,
            }
        ]
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            workspace = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                ids["workspace_id"],
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
            audit_rows = await owner.fetch("SELECT * FROM audit.promotion ORDER BY id")
            outbox_rows = await owner.fetch(
                "SELECT * FROM control.cache_outbox ORDER BY id"
            )
            media_row = await owner.fetchrow(
                "SELECT public_status, published_at FROM"
                " content.media_asset_base WHERE id = $1",
                ids["media_id"],
            )
        # Single commit: one audit row, one outbox row, revision +1 once.
        assert revision == 1
        assert str(workspace["status"]) == "ACCEPTED"
        assert workspace["accepted_at"] is not None
        assert job_row["status"] == "SUCCEEDED"
        assert job_row["error"] is None
        assert len(audit_rows) == 1
        assert len(outbox_rows) == 1
        assert json.loads(outbox_rows[0]["payload"])["media_manifest"] == manifest
        # Identical public state: the bytes re-hash; exactly one object was
        # published (the replay added nothing new).
        public_path = _public_path(media_root, digest)
        assert hashlib.sha256(public_path.read_bytes()).hexdigest() == digest
        published = sorted(p.name for p in public_path.parent.iterdir())
        assert published == [digest]
        assert str(media_row["public_status"]) == "public"
        assert media_row["published_at"] is not None
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_promote_workspace_retired(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R3.12/R7.1: the detached promotion wrapper is gone for good."""

    assert not hasattr(promotion_module, "promote_workspace")
    assert "promote_workspace" not in vars(promotion_module)
    assert callable(promotion_module.discard_workspace)
    assert callable(promotion_module.get_conflicts)

    # Test inventory pin: the unit suite pins the removal.
    inventory = (
        Path(__file__).resolve().parent.parent / "unit" / "test_promotion.py"
    ).read_text(encoding="utf-8")
    assert 'not hasattr(promotion, "promote_workspace")' in inventory
