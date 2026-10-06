"""Real PostgreSQL proof for the real human discard path (083/2).

Evidence for order R7.1: the ``073_001`` round trip (upgrade from
``072_001``, single-step downgrade restoring the BYTE-IDENTICAL 024_001
stub, re-upgrade), the unchanged worker grant surface (query-proven),
the idempotent REVIEW/CONFLICTED -> DISCARD_QUEUED enqueue with its
exact payload and stable codes, the control discard route authority
matrix, the worker DISCARD job against a real PostgreSQL + real
foundation: the success path (single reviewer transaction, COW session
clean, canonical byte-identical, private media never publicized, no
outbox), the CONFLICTED-origin discard (the conflict remedy, the
session's surviving COW operations removed), the crash-replay
convergence (the foundation no-op on an already-discarded session,
pinned), retry/budget exhaustion from BOTH origin statuses (no dead
end), the kind-aware claim with ``["FREEZE", "ACCEPT", "DISCARD"]``
claiming all three kinds FIFO, the grep pin that the discard path
contains NO ``dependencies(session_id)`` call (the ADJ-4 limitation is
deliberately outside the discard path), and the
``promotion.discard_workspace`` retirement surface.
"""

# ruff: noqa: E501 -- explicit fixture and SQL contracts

from __future__ import annotations

import ast
import hashlib
import json
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
from slaif_agent_site.agent_state import promotion as promotion_module
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_reviewer,
    asyncpg_cow_session,
    get_session_operations,
)
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.control_api.app import create_app as create_control_app
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration
from slaif_agent_site.db.privileges import FOUNDATION_REVIEWER_FUNCTIONS
from slaif_agent_site.human_authorization import (
    HumanAuthorizationService,
    MembershipChange,
)
from slaif_agent_site.media_service.config import (
    MediaDatabaseMode,
    MediaSettings,
)
from slaif_agent_site.media_service.store import MediaStore, StagedMedia
from slaif_agent_site.review_worker.accept_job import MediaBoundary, run_accept_job
from slaif_agent_site.review_worker.config import (
    ReviewWorkerDatabaseMode,
    ReviewWorkerSettings,
)
from slaif_agent_site.review_worker.discard_job import run_discard_job
from slaif_agent_site.review_worker.freeze_job import run_freeze_job

_AGGON2 = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "AAAAAAAAAAAAAAAAAAAAAA$"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
)
_PNG = b"\x89PNG\r\n\x1a\nreal-human-discard-media"
# The worker's current claim array (worker.py line 99) pinned here: the
# 083/2 worker claims all three review-job kinds.
_WORKER_KINDS = ["FREEZE", "ACCEPT", "DISCARD"]

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

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_STUB_024_001_PATH = (
    _BACKEND_ROOT
    / "src"
    / "slaif_agent_site"
    / "db"
    / "alembic"
    / "versions"
    / "024_001_workspace_lifecycle.py"
)
_DISCARD_JOB_PATH = (
    _BACKEND_ROOT / "src" / "slaif_agent_site" / "review_worker" / "discard_job.py"
)
_ACCEPT_JOB_PATH = (
    _BACKEND_ROOT / "src" / "slaif_agent_site" / "review_worker" / "accept_job.py"
)
_DISCARD_MIGRATION_PATH = (
    _BACKEND_ROOT
    / "src"
    / "slaif_agent_site"
    / "db"
    / "alembic"
    / "versions"
    / "073_001_real_human_discard.py"
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
        application_name="discard-integration-control",
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
        application_name="discard-integration-media",
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


def _stub_024_001_body() -> str:
    """The 024_001 discard-stub prosrc, sliced exactly as PostgreSQL stores it."""

    source = _STUB_024_001_PATH.read_text(encoding="utf-8")
    start = source.index("CREATE FUNCTION control.slaif_workspace_discard(")
    marker = "AS $fn$"
    open_marker = source.index(marker, start)
    close_marker = source.index("$fn$", open_marker + len(marker))
    return source[open_marker + len(marker) : close_marker]


def _code_only(source: str) -> str:
    """The source minus docstrings and comments (grep-pin surface)."""

    tree = ast.parse(source)
    lines = source.splitlines()
    drop: set[int] = set()

    def _drop_docstring(node: Any) -> None:
        body = getattr(node, "body", None)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            doc = body[0]
            for line in range(doc.lineno, (doc.end_lineno or doc.lineno) + 1):
                drop.add(line)

    _drop_docstring(tree)  # module docstring (Module is ast.mod, not ast.stmt)
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt):
            _drop_docstring(node)
    for line_number, line_text in enumerate(lines, start=1):
        if line_number in drop or line_text.lstrip().startswith("#"):
            lines[line_number - 1] = ""
    return "\n".join(lines)


def _private_path(media_root: Path, digest: str) -> Path:
    return media_root / "sha256" / digest[:2] / digest[2:4] / digest


async def _seed_site(
    database: AgentSiteDatabase,
    *,
    media_root: Path | None,
    with_ops: bool,
    with_page_dml: bool = True,
) -> dict[str, Any]:
    """One site with renderable content; optionally real COW operations.

    ``media_root=None`` seeds the media record without on-disk bytes
    (the enqueue/route/claim tests never touch media bytes).  The
    workspace carries ``page:write`` so the success fixture can include
    real page DML (the ADJ-4 limitation case, deliberately outside the
    discard path).
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
        "page:write",
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
                gen_random_uuid(), 'LOCAL', 'Discard.Integration.Delegator',
                'discard.integration.delegator', $1, 'Discard Delegator', 'ACTIVE'
            ) RETURNING id
            """,
            _AGGON2,
        )
        site_id = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name, default_locale,"
            " component_catalog_version) VALUES ('discard-int', 'Discard Int',"
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
            " alt_text, metadata) VALUES ($1,$2,$3,'discard.png','image/png',$4,"
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
            '  \'{"level":1,"text":"Discard"}\'::jsonb),'
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
            " VALUES ($1,$2,$2,'Discard Workspace','L4',$3::jsonb,'ACTIVE',"
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
        await _apply_cow_operations(database, ids, with_page_dml=with_page_dml)
    return ids


async def _apply_cow_operations(
    database: AgentSiteDatabase,
    ids: dict[str, Any],
    *,
    with_page_dml: bool = True,
) -> None:
    """Real agent COW operations: an update + a create (+ real page DML).

    The page title update is the ADJ-4 limitation case (a composite
    ``page_base (site_id, locale)`` foreign key that the foundation's
    ``get_cow_dependencies`` closure walk mishandles): it is present in
    the discard success fixture precisely because the discard path
    never calls ``dependencies()``.  Fixtures that run the ACCEPT job
    (the 083/1 conflict origin) keep the session composition-only,
    because accept's dependency closure walk cannot complete on a
    page-DML session (the known foundation limitation).
    """

    agent_pool = await database.role_pool("slaif_agent_runtime")
    try:
        # Operation 1: the component update (its own COW session scope).
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
                json.dumps({"level": 2, "text": "Discarded heading"}),
                1,
            )
            assert updated is not None
        # Operation 2: the component create (a separate COW session
        # scope, so the workspace carries multiple operations).
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
                json.dumps({"level": 3, "text": "New discarded node"}),
            )
            assert created is not None
            ids["created_heading_id"] = UUID(str(created["id"]))
        if not with_page_dml:
            return
        # Operation 3: real page DML (a title change) in its own scope.
        async with asyncpg_cow_session(
            agent_pool,
            session_id=ids["workspace_id"],
            operation_id=uuid4(),
        ) as cow:
            await cow.native.execute(
                "SELECT set_config('app.capability_id', $1, true)",
                str(ids["capability_id"]),
            )
            row_version = await cow.native.fetchval(
                "SELECT row_version FROM content.page WHERE id = $1",
                ids["page_id"],
            )
            page_row = await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_page_update("
                " $1, $2, NULL, 'Discarded Home', NULL, NULL, NULL, false, $3)",
                ids["site_id"],
                ids["page_id"],
                row_version,
            )
            assert page_row is not None
            assert str(page_row["title"]) == "Discarded Home"
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
        "discard-test-freeze",
        ["FREEZE"],
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
) -> UUID:
    """Direct COMPLETE snapshot + workspace binding (enqueue/route tests)."""

    snapshot_id = uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO control.review_snapshot (id, workspace_id, site_id,"
            " status, revision_watermark, versions, normalized_state,"
            " validation_report, media_references, browser_evidence, payload,"
            " digest, created_by) VALUES ($1,$2,$3,'COMPLETE',0,'{}'::jsonb,"
            " '{}'::jsonb,'{}'::jsonb,'[]'::jsonb,'[]'::jsonb,'{}'::jsonb,"
            " repeat('ab', 32), 'discard-test')",
            snapshot_id,
            ids["workspace_id"],
            ids["site_id"],
        )
        await owner.execute(
            "UPDATE control.workspace SET status = $2, review_snapshot_id = $1"
            " WHERE id = $3",
            snapshot_id,
            status,
            ids["workspace_id"],
        )
    return snapshot_id


async def _enqueue_discard(
    database: AgentSiteDatabase, workspace_id: UUID, actor: UUID
) -> list[Any]:
    return await _control_call(
        database,
        "SELECT * FROM control.slaif_workspace_discard($1, $2)",
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


async def _claim_discard(database: AgentSiteDatabase, claimant: str) -> dict[str, Any]:
    rows = await _claim(database, claimant, _WORKER_KINDS)
    assert len(rows) == 1
    assert rows[0]["job_kind"] == "DISCARD"
    return dict(rows[0])


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


async def _worker_pool(database: AgentSiteDatabase) -> asyncpg.Pool[Any]:
    login, password = database.credentials["slaif_review_worker"]
    return await asyncpg.create_pool(
        dsn=_dsn(database, login, password), min_size=1, max_size=2
    )


class _ConnExecutor:
    """The foundation Executor protocol over one asyncpg connection."""

    def __init__(self, connection: asyncpg.Connection[Any]) -> None:
        self._connection = connection

    async def execute(self, sql: str) -> list[tuple[Any, ...]]:
        return [tuple(row) for row in await self._connection.fetch(sql)]


async def _session_operations(
    pool: asyncpg.Pool[Any], workspace_id: UUID
) -> list[UUID]:
    """The COW session's pending operations through the foundation API."""

    async with pool.acquire() as connection:
        operations = await get_session_operations(
            _ConnExecutor(connection), workspace_id, schema="content"
        )
    return [UUID(str(operation)) for operation in operations]


async def _canonical_state(
    database: AgentSiteDatabase, ids: dict[str, Any]
) -> dict[str, Any]:
    """The canonical site state: revision, row counts, and row bytes."""

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return {
            "canonical_revision": await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            ),
            "page_base": sorted(
                (
                    f"{str(r['id'])}|{r['slug']}|{r['title']}|{r['status']}"
                    f"|{r['row_version']}"
                )
                for r in await owner.fetch(
                    "SELECT id, slug, title, status, row_version"
                    " FROM content.page_base WHERE site_id = $1",
                    ids["site_id"],
                )
            ),
            "page_composition_base": sorted(
                (f"{str(r['id'])}|{r['component_type']}|{r['order_key']}|{r['props']}")
                for r in await owner.fetch(
                    "SELECT id, component_type, order_key, props"
                    " FROM content.page_composition_base WHERE site_id = $1",
                    ids["site_id"],
                )
            ),
            "site_locale_base": sorted(
                str(r["id"])
                for r in await owner.fetch(
                    "SELECT id FROM content.site_locale_base WHERE site_id = $1",
                    ids["site_id"],
                )
            ),
            "media_asset_base": sorted(
                (
                    f"{str(r['id'])}|{r['public_status']}|{r['published_at']}"
                    f"|{r['content_hash']}|{r['storage_key']}"
                )
                for r in await owner.fetch(
                    "SELECT id, public_status, published_at, content_hash,"
                    " storage_key FROM content.media_asset_base"
                    " WHERE site_id = $1",
                    ids["site_id"],
                )
            ),
            "outbox_count": await owner.fetchval(
                "SELECT count(*) FROM control.cache_outbox WHERE site_id = $1",
                ids["site_id"],
            ),
            "promotion_audit_count": await owner.fetchval(
                "SELECT count(*) FROM audit.promotion WHERE site_id = $1",
                ids["site_id"],
            ),
        }


@pytest.mark.asyncio
async def test_discard_migration_round_trip(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R1.3/R7.1: 073_001 upgrades, downgrades, and restores byte-exactly."""

    database = agent_site_database
    dsn = database.settings.resolved_owner_dsn()
    await upgrade(database.settings)
    await reconcile(database.settings)

    async with owner_connection(dsn, expected_database=database.name) as owner:
        assert (
            await owner.fetchval("SELECT version_num FROM control.alembic_version")
            == "074_001"
        )
        # Both new/rebuilt functions: SECURITY DEFINER, search_path pinned,
        # owned by slaif_owner.
        for args in (
            "p_workspace_id uuid, p_actor_user_account_id uuid",
            "p_workspace_id uuid, p_site_id uuid, p_user_id uuid",
        ):
            row = await owner.fetchrow(
                "SELECT p.prosecdef, p.proconfig, r.rolname AS owner"
                " FROM pg_proc p"
                " JOIN pg_namespace n ON n.oid = p.pronamespace"
                " JOIN pg_roles r ON r.oid = p.proowner"
                " WHERE n.nspname = 'control'"
                " AND pg_get_function_arguments(p.oid) = $1"
                " AND p.proname LIKE 'slaif%workspace_discard'",
                args,
            )
            assert row is not None, args
            assert row["prosecdef"] is True
            assert "search_path=pg_catalog" in list(row["proconfig"])
            assert row["owner"] == "slaif_owner"

    # Downgrade to 072_001 (steps through 074_001, then 073_001).
    await run_migration(
        dsn, expected_database=database.name, operation="downgrade", revision="072_001"
    )
    async with owner_connection(dsn, expected_database=database.name) as owner:
        assert (
            await owner.fetchval("SELECT version_num FROM control.alembic_version")
            == "072_001"
        )
        # The two-argument enqueue is gone; exactly the one-argument stub
        # remains, with the BYTE-IDENTICAL 024_001 body.
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM pg_proc p"
                " JOIN pg_namespace n ON n.oid = p.pronamespace"
                " WHERE n.nspname = 'control'"
                " AND p.proname = 'slaif_workspace_discard' AND p.pronargs = 2"
            )
            == 0
        )
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM pg_proc p"
                " JOIN pg_namespace n ON n.oid = p.pronamespace"
                " WHERE n.nspname = 'control'"
                " AND p.proname = 'slaif_workspace_discard' AND p.pronargs = 1"
            )
            == 1
        )
        prosrc = await owner.fetchval(
            "SELECT p.prosrc FROM pg_proc p"
            " JOIN pg_namespace n ON n.oid = p.pronamespace"
            " WHERE n.nspname = 'control'"
            " AND p.proname = 'slaif_workspace_discard' AND p.pronargs = 1"
        )
        assert prosrc == _stub_024_001_body()
        assert (
            await owner.fetchval(
                "SELECT has_function_privilege("
                " 'slaif_control', 'control.slaif_workspace_discard(uuid)',"
                " 'EXECUTE')"
            )
            is True
        )
        for role in _LONG_LIVED_ROLES:
            if role == "slaif_control":
                continue
            assert (
                await owner.fetchval(
                    "SELECT has_function_privilege($1,"
                    " 'control.slaif_workspace_discard(uuid)', 'EXECUTE')",
                    role,
                )
                is False
            )
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM pg_proc p"
                " JOIN pg_namespace n ON n.oid = p.pronamespace"
                " WHERE n.nspname = 'control'"
                " AND p.proname = 'slaif_human_agent_workspace_discard'"
            )
            == 0
        )

    # Re-upgrade to the head.
    await run_migration(
        dsn, expected_database=database.name, operation="upgrade", revision="head"
    )
    async with owner_connection(dsn, expected_database=database.name) as owner:
        assert (
            await owner.fetchval("SELECT version_num FROM control.alembic_version")
            == "074_001"
        )
        assert (
            await owner.fetchval(
                "SELECT has_function_privilege("
                " 'slaif_control', 'control.slaif_workspace_discard(uuid, uuid)',"
                " 'EXECUTE')"
            )
            is True
        )


@pytest.mark.asyncio
async def test_worker_grant_surface_exact(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R1.5/R7.1: the worker grant surface (083/1 pins + the 083/3
    outbox consumer grants)."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        # Reviewer membership: exactly the worker edge + the owner edge.
        members = await owner.fetch(
            "SELECT r.rolname, r.rolcanlogin, am.admin_option"
            " FROM pg_auth_members am"
            " JOIN pg_roles m ON m.oid = am.roleid"
            " JOIN pg_roles r ON r.oid = am.member"
            " WHERE m.rolname = 'slaif_reviewer'"
        )
        product_members = {
            (str(row["rolname"]), bool(row["admin_option"]))
            for row in members
            if not row["rolcanlogin"]
        }
        assert product_members == {
            ("slaif_review_worker", False),
            ("slaif_owner", True),
        }

        # The exact 13-function foundation reviewer surface (083/1 pin).
        for function, arguments in FOUNDATION_REVIEWER_FUNCTIONS:
            assert (
                await owner.fetchval(
                    "SELECT has_function_privilege('slaif_review_worker', $1,"
                    " 'EXECUTE')",
                    f"agentcow.{function}({arguments})",
                )
                is True
            )
        assert (
            await owner.fetchval(
                "SELECT has_schema_privilege('slaif_review_worker','agentcow', 'USAGE')"
            )
            is True
        )

        # The exact control-table grants (083/1 pins + the 083/3 outbox
        # UPDATE): (SELECT, UPDATE) on workspace and site, (SELECT) on
        # capability and browser_run, (SELECT, INSERT, UPDATE) on
        # review_job, (SELECT, INSERT) on review_snapshot, (SELECT,
        # INSERT, UPDATE) on cache_outbox, the outbox sequence, and INSERT
        # on audit.promotion (+ SELECT through the reviewer delegation).
        expectations = {
            ("control", "workspace"): (True, True),
            ("control", "site"): (True, True),
            ("control", "capability"): (True, False),
            ("control", "browser_run"): (True, False),
            ("control", "review_job"): (True, True),
            ("control", "review_snapshot"): (True, False),
            ("control", "cache_outbox"): (True, True),
        }
        for (schema, table), (select_expected, update_expected) in expectations.items():
            select = await owner.fetchval(
                "SELECT has_table_privilege('slaif_review_worker', $1, 'SELECT')",
                f"{schema}.{table}",
            )
            update = await owner.fetchval(
                "SELECT has_table_privilege('slaif_review_worker', $1, 'UPDATE')",
                f"{schema}.{table}",
            )
            insert = await owner.fetchval(
                "SELECT has_table_privilege('slaif_review_worker', $1, 'INSERT')",
                f"{schema}.{table}",
            )
            assert select is select_expected, (schema, table)
            assert update is update_expected, (schema, table)
            assert insert is (
                table in {"review_job", "review_snapshot", "cache_outbox"}
            ), (schema, table)
        assert (
            await owner.fetchval(
                "SELECT has_sequence_privilege('slaif_review_worker',"
                " 'control.cache_outbox_id_seq', 'USAGE')"
            )
            is True
        )
        assert (
            await owner.fetchval(
                "SELECT has_table_privilege('slaif_review_worker',"
                " 'audit.promotion', 'INSERT')"
            )
            is True
        )
        # The worker holds INSERT directly; SELECT belongs to
        # slaif_reviewer (the worker role is NOINHERIT, 083/1 pin).
        assert (
            await owner.fetchval(
                "SELECT has_table_privilege('slaif_review_worker',"
                " 'audit.promotion', 'SELECT')"
            )
            is False
        )
        assert (
            await owner.fetchval(
                "SELECT has_table_privilege('slaif_reviewer',"
                " 'audit.promotion', 'SELECT')"
            )
            is True
        )

        # The new discard functions: EXECUTE for slaif_control ONLY.
        for signature in (
            "control.slaif_workspace_discard(uuid, uuid)",
            "control.slaif_human_agent_workspace_discard(uuid, uuid, uuid)",
        ):
            assert (
                await owner.fetchval(
                    "SELECT has_function_privilege('slaif_control', $1, 'EXECUTE')",
                    signature,
                )
                is True
            )
            for role in _LONG_LIVED_ROLES:
                if role == "slaif_control":
                    continue
                assert (
                    await owner.fetchval(
                        "SELECT has_function_privilege($1, $2, 'EXECUTE')",
                        role,
                        signature,
                    )
                    is False
                )

        # The 083/3 outbox consumer functions: EXECUTE for
        # slaif_review_worker ONLY.
        for signature in (
            "control.slaif_cache_outbox_claim(integer)",
            "control.slaif_cache_outbox_consume(bigint, text)",
        ):
            assert (
                await owner.fetchval(
                    "SELECT has_function_privilege('slaif_review_worker', $1,"
                    " 'EXECUTE')",
                    signature,
                )
                is True
            )
            for role in _LONG_LIVED_ROLES:
                if role == "slaif_review_worker":
                    continue
                assert (
                    await owner.fetchval(
                        "SELECT has_function_privilege($1, $2, 'EXECUTE')",
                        role,
                        signature,
                    )
                    is False
                )

    # No GRANT/REVOKE in 073_001 touches the worker or the foundation
    # surface (grep pin on the migration SQL, docstring/comments stripped).
    source = _DISCARD_MIGRATION_PATH.read_text(encoding="utf-8")
    sql_only = _code_only(source)
    assert "slaif_review_worker" not in sql_only
    assert "agentcow" not in sql_only


@pytest.mark.asyncio
async def test_discard_enqueue_matrix(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R1.1/R7.1: exact payload, idempotency before the gate, stable codes."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    workspace_id = ids["workspace_id"]
    actor = ids["delegator_id"]
    snapshot_id = await _seed_review_state(database, ids)  # REVIEW + COMPLETE

    # REVIEW enqueues with the exact payload.
    rows = await _enqueue_discard(database, workspace_id, actor)
    assert len(rows) == 1
    job_id = UUID(str(rows[0]["job_id"]))
    assert str(rows[0]["status"]) == "QUEUED"
    status, bound = await _workspace_state(database, workspace_id)
    assert (status, bound) == ("DISCARD_QUEUED", snapshot_id)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        payload = await owner.fetchval(
            "SELECT payload FROM control.review_job WHERE id = $1", job_id
        )
        first_revoked_at = await owner.fetchval(
            "SELECT revoked_at FROM control.capability WHERE id = $1",
            ids["capability_id"],
        )
    assert json.loads(payload) == {
        "site_id": str(ids["site_id"]),
        "origin_status": "REVIEW",
        "actor_user_account_id": str(actor),
    }
    # The enqueue's defensive capability revocation fired exactly once.
    assert first_revoked_at is not None

    # Idempotency BEFORE the status gate: the workspace is no longer
    # discardable (DISCARD_QUEUED), yet the live job is returned unchanged.
    again = await _enqueue_discard(database, workspace_id, actor)
    assert str(again[0]["job_id"]) == str(job_id)
    # And while CLAIMED.
    claimed = await _claim(database, "discard-enqueue-claim", _WORKER_KINDS)
    assert len(claimed) == 1 and str(claimed[0]["id"]) == str(job_id)
    claimed_again = await _enqueue_discard(database, workspace_id, actor)
    assert str(claimed_again[0]["job_id"]) == str(job_id)

    # Terminate the job and prove the CONFLICTED origin status.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "UPDATE control.review_job SET status = 'SUCCEEDED' WHERE id = $1",
            job_id,
        )
        await owner.execute(
            "UPDATE control.workspace SET status = 'CONFLICTED' WHERE id = $1",
            workspace_id,
        )
    conflicted_rows = await _enqueue_discard(database, workspace_id, actor)
    assert len(conflicted_rows) == 1
    conflicted_job_id = UUID(str(conflicted_rows[0]["job_id"]))
    assert str(conflicted_job_id) != str(job_id)
    assert str((await _workspace_state(database, workspace_id))[0]) == "DISCARD_QUEUED"
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        payload = await owner.fetchval(
            "SELECT payload FROM control.review_job WHERE id = $1",
            conflicted_job_id,
        )
        second_revoked_at = await owner.fetchval(
            "SELECT revoked_at FROM control.capability WHERE id = $1",
            ids["capability_id"],
        )
    assert json.loads(payload) == {
        "site_id": str(ids["site_id"]),
        "origin_status": "CONFLICTED",
        "actor_user_account_id": str(actor),
    }
    # No double revoke: the guarded UPDATE touched nothing the second time.
    assert second_revoked_at == first_revoked_at

    # Claim the CONFLICTED job so the loop's terminal writes are claim-shaped
    # (a non-QUEUED row requires claimed_by/claimed_at/last_heartbeat).
    claimed_conflicted = await _claim(
        database, "discard-conflicted-claim", _WORKER_KINDS
    )
    assert len(claimed_conflicted) == 1
    assert str(claimed_conflicted[0]["id"]) == str(conflicted_job_id)

    # The full non-discardable set -> WORKSPACE_NOT_DISCARDABLE (P0002).
    for target_status in (
        "FREEZING",
        "ACCEPT_QUEUED",
        "PROMOTING",
        "ACTIVE",
        "ACCEPTED",
        "DISCARDED",
    ):
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.review_job SET status = 'SUCCEEDED' WHERE id = $1",
                conflicted_job_id,
            )
            await owner.execute(
                "UPDATE control.workspace SET status = $1 WHERE id = $2",
                target_status,
                workspace_id,
            )
        with pytest.raises(asyncpg.PostgresError) as excinfo:
            await _enqueue_discard(database, workspace_id, actor)
        assert excinfo.value.sqlstate == "P0002"
        assert "WORKSPACE_NOT_DISCARDABLE" in str(excinfo.value)

    # WORKSPACE_NOT_FOUND for an unknown workspace.
    with pytest.raises(asyncpg.PostgresError) as excinfo:
        await _enqueue_discard(database, uuid4(), actor)
    assert excinfo.value.sqlstate == "P0002"
    assert "WORKSPACE_NOT_FOUND" in str(excinfo.value)


def _discard_headers(session: Any) -> dict[str, str]:
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
            " VALUES ($1, 'OIDC', 'discard-int', $2, $3, 'ACTIVE')",
            user_id,
            str(uuid4()),
            name,
        )
    return user_id


@pytest.mark.asyncio
async def test_control_discard_route_authority_matrix(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R2/R7.1: permission, recent auth, binding, strict body, classes."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    site_id = ids["site_id"]
    workspace_id = ids["workspace_id"]
    await _seed_review_state(database, ids)

    # A second site (wrong-binding), a terminal DISCARDED workspace (409),
    # and a FREEZING workspace (409): direct owner fixtures.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        other_site = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name, default_locale,"
            " component_catalog_version) VALUES ('discard-int-other','Other',"
            " 'en-US', 'catalog-v1') RETURNING id"
        )
        discarded_ws = await owner.fetchval(
            "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
            " title, delegation_preset, effective_scopes, status, expires_at)"
            " VALUES ($1,$2,$2,'Discard Terminal WS','L4','[\"page:read\"]'::jsonb,"
            " 'DISCARDED', now()+interval '1 hour') RETURNING id",
            site_id,
            ids["delegator_id"],
        )
        freezing_ws = await owner.fetchval(
            "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
            " title, delegation_preset, effective_scopes, status, expires_at)"
            " VALUES ($1,$2,$2,'Discard Freezing WS','L4','[\"page:read\"]'::jsonb,"
            " 'FREEZING', now()+interval '1 hour') RETURNING id",
            site_id,
            ids["delegator_id"],
        )
        for workspace in (discarded_ws, freezing_ws):
            snapshot = uuid4()
            await owner.execute(
                "INSERT INTO control.review_snapshot (id, workspace_id, site_id,"
                " status, revision_watermark, versions, normalized_state,"
                " validation_report, media_references, browser_evidence,"
                " payload, digest, created_by) VALUES ($1,$2,$3,'COMPLETE',0,"
                "'{}'::jsonb,'{}'::jsonb,'{}'::jsonb,'[]'::jsonb,'[]'::jsonb,"
                "'{}'::jsonb, repeat('ab', 32), 'discard-test')",
                snapshot,
                workspace,
                site_id,
            )
            await owner.execute(
                "UPDATE control.workspace SET review_snapshot_id = $1 WHERE id = $2",
                snapshot,
                workspace,
            )

    users: dict[str, UUID] = {}
    for key in ("owner", "deny_discard", "outsider", "admin"):
        users[key] = await _create_user(database, f"Discard {key}")
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
        users["deny_discard"],
        MembershipChange(
            role_key="SITE_OWNER",
            delegation_ceiling=4,
            deny_permissions=frozenset({"workspace:discard"}),
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
                else _discard_headers(session)
            )
            path = f"/api/control/v1/sites/{site}/workspaces/{workspace}/discard/"
            return await client.post(path, json=body, headers=headers)

        valid_body = {"acknowledge_discard": True}
        async with control_app.router.lifespan_context(control_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=control_app),
                base_url="http://control.test",
            ) as client:
                # Positive: permission + recent auth -> 202.
                response = await post(sessions["owner"], valid_body)
                assert response.status_code == 202, response.text
                first_body = response.json()
                job_id = first_body["job_id"]
                assert first_body["status"] == "DISCARD_QUEUED"
                status, _bound = await _workspace_state(database, workspace_id)
                assert status == "DISCARD_QUEUED"

                # Idempotent duplicate while the job is live: SAME job id.
                duplicate = await post(sessions["owner"], valid_body)
                assert duplicate.status_code == 202, duplicate.text
                assert duplicate.json() == first_body

                # The platform administrator path reaches the same job.
                admin_post = await post(sessions["admin"], valid_body)
                assert admin_post.status_code == 202, admin_post.text
                assert admin_post.json()["job_id"] == job_id

                # Missing workspace:discard (and no membership at all)
                # -> uniform 404, pairwise indistinguishable from the
                # wrong-site binding 404.
                denied = await post(sessions["deny_discard"], valid_body)
                assert denied.status_code == 404, denied.text
                outsider = await post(sessions["outsider"], valid_body)
                assert outsider.status_code == 404, outsider.text
                binding = await post(
                    sessions["owner"], valid_body, site=UUID(str(other_site))
                )
                assert binding.status_code == 404, binding.text
                assert _error_envelope(denied) == _error_envelope(outsider)
                assert _error_envelope(denied) == _error_envelope(binding)

                # Recent auth absent -> 401 class.
                stale_user = users["owner"]
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    await owner.execute(
                        "UPDATE control.user_session SET"
                        " created_at = now() - interval '1 hour',"
                        " recent_auth_at = now() - interval '901 seconds'"
                        " WHERE user_account_id = $1",
                        stale_user,
                    )
                stale = await post(sessions["owner"], valid_body)
                assert stale.status_code == 401, stale.text
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    await owner.execute(
                        "UPDATE control.user_session SET recent_auth_at = now()"
                        " WHERE user_account_id = $1",
                        stale_user,
                    )

                # Strict body: 422 for every malformed acknowledgement.
                for bad_body in (
                    {"acknowledge_discard": False},
                    {"acknowledge_discard": 1},
                    {},
                    {"acknowledge_discard": True, "extra": True},
                ):
                    rejected = await post(sessions["owner"], bad_body)
                    assert rejected.status_code == 422, (bad_body, rejected.text)

                # No agent-facing discard: a capability Bearer token on
                # the control route is a uniform authentication denial.
                token, _public_id, _secret_digest = generate_capability_token()
                agent_bearer = await post(sessions["owner"], valid_body, bearer=token)
                assert agent_bearer.status_code == 401, agent_bearer.text
                no_cookie = await client.post(
                    f"/api/control/v1/sites/{site_id}"
                    f"/workspaces/{workspace_id}/discard/",
                    json=valid_body,
                )
                assert no_cookie.status_code == 401, no_cookie.text

                # Terminal DISCARDED -> 409 (pinned once).
                terminal = await post(
                    sessions["owner"], valid_body, workspace=UUID(str(discarded_ws))
                )
                assert terminal.status_code == 409, terminal.text

                # FREEZING -> 409 (the deliberate 024_001 deviation).
                freezing = await post(
                    sessions["owner"], valid_body, workspace=UUID(str(freezing_ws))
                )
                assert freezing.status_code == 409, freezing.text
    finally:
        await adapter.stop()
        await control_pool.close()


@pytest.mark.asyncio
async def test_discard_worker_success_path(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """R3.2/R7.1: the single reviewer transaction discards for real.

    The session carries content incl. media AND real page DML: the ADJ-4
    foundation limitation is deliberately outside the discard path, so
    the discard commits nothing and never runs the closure check.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    try:
        # Before: three real COW operations (update, create, page DML)
        # and a byte-exact canonical baseline.
        before_operations = await _session_operations(pool, ids["workspace_id"])
        assert len(before_operations) == 3
        before = await _canonical_state(database, ids)

        await _freeze_workspace(database, ids, pool)
        assert (
            str((await _workspace_state(database, ids["workspace_id"]))[0]) == "REVIEW"
        )
        rows = await _enqueue_discard(
            database, ids["workspace_id"], ids["delegator_id"]
        )
        assert len(rows) == 1
        job_id = UUID(str(rows[0]["job_id"]))
        job = await _claim_discard(database, "discard-success-1")
        assert str(job["id"]) == str(job_id)
        result = await run_discard_job(pool, settings, job)
        assert result.status == "SUCCEEDED", result.error

        digest = ids["media_digest"]
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            workspace = await owner.fetchrow(
                "SELECT status, discarded_at FROM control.workspace WHERE id = $1",
                ids["workspace_id"],
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
            capability_revoked = await owner.fetchval(
                "SELECT revoked_at IS NOT NULL FROM control.capability WHERE id = $1",
                ids["capability_id"],
            )
            cow_change_counts = await owner.fetchrow(
                "SELECT (SELECT count(*) FROM content.page_composition_changes"
                " WHERE session_id = $1) AS composition,"
                " (SELECT count(*) FROM content.page_changes"
                " WHERE session_id = $1) AS pages",
                ids["workspace_id"],
            )
        # Workspace terminal, job terminal, session fully clean.
        assert str(workspace["status"]) == "DISCARDED"
        assert workspace["discarded_at"] is not None
        assert job_row["status"] == "SUCCEEDED"
        assert job_row["error"] is None
        after_operations = await _session_operations(pool, ids["workspace_id"])
        assert after_operations == []
        assert tuple(cow_change_counts) == (0, 0)
        # The enqueue's capability revocation persisted.
        assert capability_revoked is True

        # Canonical byte-identical: revision, row sets, and bytes all
        # unchanged; no outbox event, no promotion audit.
        after = await _canonical_state(database, ids)
        assert after == before
        # Private staging bytes remain private: no public bytes were
        # created and the canonical media row is untouched (covered by
        # the _canonical_state media byte-identity above).
        assert _private_path(media_root, digest).is_file()
        assert not (media_root / "public").exists()
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_discard_worker_conflicted_origin(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """R7.1: the 083/1 conflict fixture is a real CONFLICTED origin.

    The 083/1 conflict remedy path: the accept job detects the canonical
    drift (BASE_ROW_CHANGED, full rollback, the session's COW operations
    survive) and the workspace is terminal CONFLICTED for accept; the
    discard then removes the pending work for real.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    # Composition-only session: the accept job's dependency closure walk
    # cannot complete on a page-DML session (ADJ-4), and this fixture
    # needs the clean BASE_ROW_CHANGED conflict failure.
    ids = await _seed_site(
        database, media_root=media_root, with_ops=True, with_page_dml=False
    )
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        await _freeze_workspace(database, ids, pool)
        accept_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_workspace_accept($1, $2)",
            ids["workspace_id"],
            ids["delegator_id"],
        )
        assert len(accept_rows) == 1
        accept_job_id = UUID(str(accept_rows[0]["job_id"]))
        accept_claim = await _claim(database, "discard-conflict-accept", ["ACCEPT"])
        assert len(accept_claim) == 1
        assert str(accept_claim[0]["id"]) == str(accept_job_id)

        # The 083/1 conflict fixture: a concurrent canonical edit to the
        # exact row the session's update operation touched.
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
            before_change_count = await owner.fetchval(
                "SELECT count(*) FROM content.page_composition_changes"
                " WHERE session_id = $1",
                ids["workspace_id"],
            )
        accept_result = await run_accept_job(
            pool, settings, dict(accept_claim[0]), media=boundary
        )
        assert accept_result.status == "FAILED"
        assert accept_result.error == "BASE_ROW_CHANGED"
        assert (
            str((await _workspace_state(database, ids["workspace_id"]))[0])
            == "CONFLICTED"
        )
        assert before_change_count >= 2  # the COW operations survived

        # The conflict remedy: discard the CONFLICTED workspace.
        rows = await _enqueue_discard(
            database, ids["workspace_id"], ids["delegator_id"]
        )
        assert len(rows) == 1
        job_id = UUID(str(rows[0]["job_id"]))
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            payload = await owner.fetchval(
                "SELECT payload FROM control.review_job WHERE id = $1", job_id
            )
        assert json.loads(payload)["origin_status"] == "CONFLICTED"
        job = await _claim_discard(database, "discard-conflict-1")
        assert str(job["id"]) == str(job_id)
        result = await run_discard_job(pool, settings, job)
        assert result.status == "SUCCEEDED", result.error

        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            workspace = await owner.fetchrow(
                "SELECT status, discarded_at FROM control.workspace WHERE id = $1",
                ids["workspace_id"],
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            change_count = await owner.fetchval(
                "SELECT count(*) FROM content.page_composition_changes"
                " WHERE session_id = $1",
                ids["workspace_id"],
            )
        assert str(workspace["status"]) == "DISCARDED"
        assert workspace["discarded_at"] is not None
        assert job_row["status"] == "SUCCEEDED"
        assert job_row["error"] is None
        # The conflict remedy worked: the pending work is gone, the
        # canonical revision never moved (the accept committed nothing).
        assert change_count == 0
        assert revision == 0
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_discard_worker_crash_replay_converges(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """R3.2.7/R7.1: crash after discard_session converges idempotently.

    The fixture simulates the real crash window: the claimed worker marks
    the workspace DISCARDING, runs the foundation discard_session, and
    dies before the terminal write. Stale-claim recovery re-queues the
    job; the replay must converge to exactly one DISCARDED terminal.  The
    foundation's OBSERVED behavior on an already-discarded session is a
    clean no-op (``no_op=True``, empty operations) — pinned below.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    try:
        await _freeze_workspace(database, ids, pool)
        rows = await _enqueue_discard(
            database, ids["workspace_id"], ids["delegator_id"]
        )
        job_id = UUID(str(rows[0]["job_id"]))
        job = await _claim_discard(database, "discard-crash-1")
        assert str(job["id"]) == str(job_id)

        # The crashed worker's last durable actions: DISCARDING + the
        # foundation discard (committing nothing), then the crash.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.workspace SET status = 'DISCARDING' WHERE id = $1",
                ids["workspace_id"],
            )
        async with pool.acquire() as connection:
            async with asyncpg_cow_reviewer(connection) as reviewer:
                first = await reviewer.discard_session(
                    ids["workspace_id"], schema="content"
                )
        # The first discard removed the real pending operations.
        assert first.no_op is False
        assert len(first.discarded_operations) == 3

        # The crash: no terminal written; the heartbeat goes stale;
        # recovery re-queues; the replay converges.
        await _age_heartbeat(database, job_id)
        replay = await _claim_discard(database, "discard-crash-2")
        assert str(replay["id"]) == str(job_id)
        assert replay["attempt_count"] == 2
        result = await run_discard_job(pool, settings, replay)
        assert result.status == "SUCCEEDED", result.error

        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            workspace = await owner.fetchrow(
                "SELECT status, discarded_at FROM control.workspace WHERE id = $1",
                ids["workspace_id"],
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
        assert str(workspace["status"]) == "DISCARDED"
        assert workspace["discarded_at"] is not None
        assert job_row["status"] == "SUCCEEDED"
        assert job_row["error"] is None

        # The foundation's OBSERVED behavior, pinned: a discard_session
        # on an already-discarded session is a clean no-op (empty
        # operations, no_op=True), which is what made the replay safe.
        async with pool.acquire() as connection:
            async with asyncpg_cow_reviewer(connection) as reviewer:
                replay_result = await reviewer.discard_session(
                    ids["workspace_id"], schema="content"
                )
        assert replay_result.no_op is True
        assert replay_result.discarded_tables == ()
        assert replay_result.discarded_operations == ()
        assert replay_result.has_pending_operations is False
    finally:
        await pool.close()


async def _set_worker_discard_grant(database: AgentSiteDatabase, granted: bool) -> None:
    """Deterministic transient-failure lever: the worker's discard_cow."""

    verb = "GRANT" if granted else "REVOKE"
    relation = "TO" if granted else "FROM"
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            f"{verb} EXECUTE ON FUNCTION"
            " agentcow.discard_cow(text, text, uuid, uuid[])"
            f" {relation} slaif_review_worker"
        )


@pytest.mark.asyncio
async def test_discard_worker_retryable_and_budget(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R3.2.6/R7.1: transient stays replayable; budget terminates safe.

    The transient failure is a real infrastructure denial (the worker's
    EXECUTE on ``agentcow.discard_cow`` revoked): the job stays CLAIMED,
    the workspace stays DISCARDING, and a re-claim replays.  At the
    attempt budget the job terminates with REVIEW_JOB_STALE_AT_BUDGET and
    the workspace returns to its ORIGIN status — proven from BOTH
    REVIEW and CONFLICTED origins (no dead end).
    """

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=True)
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    try:
        await _freeze_workspace(database, ids, pool)

        async def exhaust_budget(origin: str) -> str:
            """Walk three failed attempts; return the final workspace status."""

            rows = await _enqueue_discard(
                database, ids["workspace_id"], ids["delegator_id"]
            )
            job_id = UUID(str(rows[0]["job_id"]))
            last_status = "DISCARDING"
            for attempt in (1, 2, 3):
                job = await _claim_discard(
                    database, f"discard-budget-{origin}-{attempt}"
                )
                assert str(job["id"]) == str(job_id)
                assert job["attempt_count"] == attempt
                assert job["max_attempts"] == 3
                await _set_worker_discard_grant(database, granted=False)
                result = await run_discard_job(pool, settings, job)
                if attempt < 3:
                    # Transient: no terminal, the workspace stays
                    # DISCARDING (the replay converges).
                    assert result.status == "ROLLED_BACK", (attempt, result.error)
                    await _set_worker_discard_grant(database, granted=True)
                    await _age_heartbeat(database, job_id)
                    async with owner_connection(
                        database.settings.resolved_owner_dsn(),
                        expected_database=database.name,
                    ) as owner:
                        last_status = await owner.fetchval(
                            "SELECT status FROM control.workspace WHERE id = $1",
                            ids["workspace_id"],
                        )
                        row = await owner.fetchrow(
                            "SELECT status, error FROM control.review_job"
                            " WHERE id = $1",
                            job_id,
                        )
                    assert last_status == "DISCARDING"
                    assert row["status"] == "CLAIMED"
                    assert row["error"] is None
                else:
                    # At budget: terminal + the workspace back to origin.
                    assert result.status == "FAILED"
                    assert result.error == "REVIEW_JOB_STALE_AT_BUDGET"
                    await _set_worker_discard_grant(database, granted=True)
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                final_status = await owner.fetchval(
                    "SELECT status FROM control.workspace WHERE id = $1",
                    ids["workspace_id"],
                )
                job_row = await owner.fetchrow(
                    "SELECT status, error FROM control.review_job WHERE id = $1",
                    job_id,
                )
            assert job_row["status"] == "FAILED"
            assert job_row["error"] == "REVIEW_JOB_STALE_AT_BUDGET"
            return str(final_status)

        # Origin REVIEW.
        assert (
            str((await _workspace_state(database, ids["workspace_id"]))[0]) == "REVIEW"
        )
        assert await exhaust_budget("REVIEW") == "REVIEW"

        # Origin CONFLICTED (the conflict-remedy origin).
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.workspace SET status = 'CONFLICTED' WHERE id = $1",
                ids["workspace_id"],
            )
        assert await exhaust_budget("CONFLICTED") == "CONFLICTED"
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_kind_aware_claim_discard_fifo(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R3.1/R7.1: the worker set claims all three kinds, FIFO."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        # A second (REVIEW + snapshot) workspace for the ACCEPT job and a
        # third for the DISCARD job.
        accept_ws = await owner.fetchval(
            "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
            " title, delegation_preset, effective_scopes, status, expires_at)"
            " VALUES ($1,$2,$2,'Kind Accept WS','L4','[\"page:read\"]'::jsonb,"
            " 'REVIEW', now()+interval '1 hour') RETURNING id",
            ids["site_id"],
            ids["delegator_id"],
        )
        discard_ws = await owner.fetchval(
            "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
            " title, delegation_preset, effective_scopes, status, expires_at)"
            " VALUES ($1,$2,$2,'Kind Discard WS','L4','[\"page:read\"]'::jsonb,"
            " 'REVIEW', now()+interval '1 hour') RETURNING id",
            ids["site_id"],
            ids["delegator_id"],
        )
        for workspace in (accept_ws, discard_ws):
            snapshot = uuid4()
            await owner.execute(
                "INSERT INTO control.review_snapshot (id, workspace_id, site_id,"
                " status, revision_watermark, versions, normalized_state,"
                " validation_report, media_references, browser_evidence,"
                " payload, digest, created_by) VALUES ($1,$2,$3,'COMPLETE',0,"
                "'{}'::jsonb,'{}'::jsonb,'{}'::jsonb,'[]'::jsonb,'[]'::jsonb,"
                "'{}'::jsonb, repeat('ef', 32), 'discard-test')",
                snapshot,
                workspace,
                ids["site_id"],
            )
            await owner.execute(
                "UPDATE control.workspace SET review_snapshot_id = $1 WHERE id = $2",
                snapshot,
                workspace,
            )
    # Enqueue in FIFO order: FREEZE, ACCEPT, DISCARD.
    freeze_rows = await _control_call(
        database,
        "SELECT * FROM control.slaif_human_agent_workspace_freeze($1,$2,$3)",
        ids["workspace_id"],
        ids["site_id"],
        ids["delegator_id"],
    )
    assert len(freeze_rows) == 1
    freeze_job_id = UUID(str(freeze_rows[0]["job_id"]))
    accept_rows = await _control_call(
        database,
        "SELECT * FROM control.slaif_workspace_accept($1, $2)",
        UUID(str(accept_ws)),
        ids["delegator_id"],
    )
    assert len(accept_rows) == 1
    accept_job_id = UUID(str(accept_rows[0]["job_id"]))
    discard_rows = await _control_call(
        database,
        "SELECT * FROM control.slaif_workspace_discard($1, $2)",
        UUID(str(discard_ws)),
        ids["delegator_id"],
    )
    assert len(discard_rows) == 1
    discard_job_id = UUID(str(discard_rows[0]["job_id"]))

    # The 083/2 worker set claims all three kinds, in FIFO order.
    for expected in (freeze_job_id, accept_job_id, discard_job_id):
        rows = await _claim(database, "discard-fifo", _WORKER_KINDS)
        assert len(rows) == 1
        assert str(rows[0]["id"]) == str(expected)
    assert await _claim(database, "discard-fifo-empty", _WORKER_KINDS) == []

    # Invalid arrays are rejected (072_001 behavior unchanged).
    for bad_kinds in (["FREEZE", "BOGUS"], ["BOGUS"], [], None):
        with pytest.raises(asyncpg.PostgresError) as excinfo:
            await _claim(database, "discard-fifo-bad", bad_kinds)
        assert "REVIEW_CLAIM_KIND_INVALID" in str(excinfo.value)


@pytest.mark.asyncio
async def test_discard_path_has_no_dependencies_call() -> None:
    """R3.2.5: the discard path never calls dependencies(session_id).

    The 083/1 KNOWN LIMITATION (the foundation's composite-FK closure
    cross-product) cannot affect discard because discard commits
    nothing; the grep pin proves the discard module calls only
    ``discard_session`` plus control-table updates.
    """

    discard_code = _code_only(_DISCARD_JOB_PATH.read_text(encoding="utf-8"))
    assert "dependencies(" not in discard_code
    assert "discard_session(" in discard_code
    # Positive control: the same grep method detects the closure check
    # where it legitimately lives (the accept path).
    accept_code = _code_only(_ACCEPT_JOB_PATH.read_text(encoding="utf-8"))
    assert "dependencies(" in accept_code
    # The dispatch carries DISCARD to the discard job only.
    freeze_code = _code_only(
        (
            _BACKEND_ROOT
            / "src"
            / "slaif_agent_site"
            / "review_worker"
            / "freeze_job.py"
        ).read_text(encoding="utf-8")
    )
    assert "from .discard_job import run_discard_job" in freeze_code


@pytest.mark.asyncio
async def test_discard_workspace_retired() -> None:
    """R3.3: promotion.discard_workspace is gone; get_conflicts stays."""

    assert not hasattr(promotion_module, "discard_workspace")
    assert "discard_workspace" not in vars(promotion_module)
    assert callable(promotion_module.get_conflicts)
    # Test inventory pin: the unit suite pins the removal.
    unit_source = (
        Path(__file__).resolve().parents[1] / "unit" / "test_promotion.py"
    ).read_text(encoding="utf-8")
    assert 'not hasattr(promotion, "discard_workspace")' in unit_source
    assert '"discard_workspace" not in vars(promotion)' in unit_source
