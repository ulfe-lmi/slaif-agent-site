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
import re
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
from slaif_agent_site.agent_api.models import AgentCapabilityContext
from slaif_agent_site.agent_state import promotion as promotion_module
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_reviewer,
    get_operation_dependencies,
    get_session_operations,
)
from slaif_agent_site.agent_state.mutations import (
    AgentCowContentModelService,
    execute_agent_mutation,
    mutation_digest,
)
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.content_model.composition_models import (
    AgentCreateCompositionNodeRequest,
    AgentUpdateCompositionNodeRequest,
)
from slaif_agent_site.control_api.app import create_app as create_control_app
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.executor import AsyncpgExecutor
from slaif_agent_site.db.roles import quote_identifier
from slaif_agent_site.editor_api.app import create_app as create_editor_app
from slaif_agent_site.editor_api.database import EditorDatabase
from slaif_agent_site.human_authorization import (
    HumanAuthorizationService,
    MembershipChange,
)
from slaif_agent_site.media_service.app import create_app as create_media_app
from slaif_agent_site.media_service.config import MediaDatabaseMode, MediaSettings
from slaif_agent_site.media_service.database import MediaDatabase
from slaif_agent_site.media_service.finalize import (
    FinalizationManifest,
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
from test_human_editor_production_http import (
    CONTROL_LOGIN,
    CONTROL_PASSWORD,
    CONTROL_ROLE,
    EDITOR_LOGIN,
    EDITOR_PASSWORD,
    EDITOR_ROLE,
    _assert_private,
    _cookie,
    _editor_settings,
    _mutation_headers,
)

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
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
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


_CURRENT_VERSION_FACTS = r""" '{"catalog":"catalog-v1","composition_schema":"site-composition/v1","content_model":"content-model/v1","design_system":"design-system/v1","puck":"0.20.2","renderer":"renderer-v1"}'::jsonb"""


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
            ' \'{"preset":"ocean"}\'::jsonb,'
            ' \'{"family":"system","scale":"balanced","weight":"regular"}\'::jsonb,'
            ' \'{"content_width":"md","spacing":"md","grid_gap":"md"}\'::jsonb,'
            ' \'{"radius":"md","shadow":"sm"}\'::jsonb)',
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
            " title, delegation_preset, effective_scopes, version_facts,"
            " status, expires_at)"
            " VALUES ($1,$2,$2,'Accept Workspace','L4',$3::jsonb,"
            + _CURRENT_VERSION_FACTS
            + ",'ACTIVE',"
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
        "scopes": scopes,
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


class _CowPoolAdapter:
    """Minimal database surface for ``execute_agent_mutation``: the
    fixture's real ``slaif_agent_runtime`` COW role pool, unwrapped."""

    def __init__(self, pool: asyncpg.Pool[Any]) -> None:
        self._pool = pool

    def cow_pool(self) -> asyncpg.Pool[Any]:
        return self._pool


async def _apply_cow_operations(
    database: AgentSiteDatabase, ids: dict[str, Any]
) -> None:
    """Real agent COW operations through the product mutation executor
    (an update + a create: two operations, each with its real 078
    completion journal row - the manifest identity binding reads it)."""

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        capability = await owner.fetchrow(
            "SELECT created_at, expires_at FROM control.capability WHERE id = $1",
            ids["capability_id"],
        )
    assert capability is not None
    context = AgentCapabilityContext(
        capability_id=ids["capability_id"],
        site_id=ids["site_id"],
        workspace_id=ids["workspace_id"],
        delegator_id=ids["delegator_id"],
        scopes=frozenset(ids["scopes"]),
        created_at=capability["created_at"],
        expires_at=capability["expires_at"],
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")

    async def update_heading(
        service: AgentCowContentModelService,
    ) -> Any:
        return await service.update_component_for_site(
            ids["site_id"],
            ids["heading_id"],
            AgentUpdateCompositionNodeRequest(
                props={"level": 2, "text": "Promoted heading"},
                expected_row_version=1,
            ),
        )

    async def create_heading(
        service: AgentCowContentModelService,
    ) -> Any:
        return await service.add_component_for_site(
            ids["site_id"],
            ids["page_id"],
            AgentCreateCompositionNodeRequest(
                component_type="Heading",
                parent_id=str(ids["section_id"]),
                slot_key="default",
                props={"level": 3, "text": "New promoted node"},
            ),
        )

    try:
        # Operation 1: the update (its own COW transaction with the real
        # reservation, COW write, audit and completion journal).
        updated = await execute_agent_mutation(
            database=_CowPoolAdapter(agent_pool),
            context=context,
            key="083-12-accept-int-update-heading",
            digest=mutation_digest(
                method="PATCH",
                path=f"/sites/{ids['site_id']}/components/{ids['heading_id']}",
                body={"level": 2, "text": "Promoted heading"},
            ),
            mutate=update_heading,
            resource_type="composition_node",
            status_code=200,
            quota_kind="mutation",
            action="COMPONENT_UPDATED",
            method="PATCH",
        )
        assert updated.operation_id is not None
        # Operation 2: the create (a separate COW transaction, so the
        # workspace carries exactly two operations).
        created = await execute_agent_mutation(
            database=_CowPoolAdapter(agent_pool),
            context=context,
            key="083-12-accept-int-create-heading",
            digest=mutation_digest(
                method="POST",
                path=(f"/sites/{ids['site_id']}/pages/{ids['page_id']}/components"),
                body={
                    "component_type": "Heading",
                    "parent_id": str(ids["section_id"]),
                    "slot_key": "default",
                    "props": {"level": 3, "text": "New promoted node"},
                },
            ),
            mutate=create_heading,
            resource_type="composition_node",
            status_code=201,
            quota_kind="mutation",
            action="COMPONENT_CREATED",
            method="POST",
        )
        assert created.operation_id is not None
        ids["created_heading_id"] = UUID(str(created.record["id"]))
    finally:
        await agent_pool.close()


class _CountingMediaBoundary(MediaBoundary):
    """Counting boundary over a REAL MediaBoundary (never a mock).

    A true subtype of the worker boundary: ``finalize`` is the only
    finalization entry point the accept job calls (accept_job.py
    L599); counting it is runtime call evidence (0 calls after the
    refused run, exactly 1 after the untampered positive), and both
    ``finalize`` and ``stop`` delegate to the real boundary.  The
    subclass constructor initializes its own lazy machinery with no
    settings so it can never be used directly - only the delegated
    methods are ever invoked.
    """

    def __init__(self, inner: MediaBoundary) -> None:
        super().__init__(settings=None)
        self._inner = inner
        self.finalize_calls = 0

    async def finalize(
        self, site_id: UUID, workspace_id: UUID, media_ids: list[UUID]
    ) -> FinalizationManifest:
        self.finalize_calls += 1
        return await self._inner.finalize(site_id, workspace_id, media_ids)

    async def stop(self) -> None:
        await self._inner.stop()


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
        # 083/12: the seeded COMPLETE snapshot carries the companion a
        # real freeze would have created, built from the ACTUAL public
        # session state (no invented operations).
        operations, dependencies, identities = await _capture_session(
            owner, ids["workspace_id"], ids["site_id"]
        )
        await _seed_companion(
            owner,
            workspace_id=ids["workspace_id"],
            site_id=ids["site_id"],
            snapshot_id=snapshot_id,
            digest=digest,
            operations=operations,
            dependencies=dependencies,
            identities=identities,
        )
    return snapshot_id


async def _capture_session(
    owner: Any, workspace_id: UUID, site_id: UUID
) -> tuple[list[UUID], list[tuple[UUID, UUID]], list[dict[str, str]]]:
    """The actual public foundation session state (083/12 R1 input)."""
    executor = AsyncpgExecutor(owner)
    operations = await get_session_operations(executor, workspace_id, schema="content")
    dependencies = await get_operation_dependencies(
        executor, workspace_id, schema="content"
    )
    doc = await owner.fetchval(
        "SELECT control.slaif_review_operation_identities($1, $2, $3)",
        workspace_id,
        site_id,
        operations,
    )
    if isinstance(doc, str):
        doc = json.loads(doc)
    return list(operations), list(dependencies), list(doc or [])


async def _seed_companion(
    owner: Any,
    *,
    workspace_id: UUID,
    site_id: UUID,
    snapshot_id: UUID,
    digest: str,
    operations: list[UUID],
    dependencies: list[tuple[UUID, UUID]],
    identities: list[dict[str, str]],
) -> tuple[UUID, str]:
    """Trusted OWNER fixture: one companion row in the exact form the
    trusted completion function stores (canonical arrays + the product's
    own canonical digest expression).  Returns (manifest_id, digest)."""
    manifest_id = uuid4()
    canonical = {
        "schema_version": "reviewed-operations/v1",
        "snapshot_id": str(snapshot_id),
        "snapshot_digest": digest,
        "site_id": str(site_id),
        "workspace_id": str(workspace_id),
        "operation_ids": sorted(str(operation) for operation in operations),
        "dependency_pairs": sorted(
            {
                [str(depends_on), str(operation_id)]
                for depends_on, operation_id in dependencies
            }
        ),
        "completion_identities": sorted(
            identities, key=lambda item: item["operation_id"]
        ),
    }
    manifest_digest = await owner.fetchval(
        "SELECT encode(sha256(convert_to("
        "control.slaif_canonical_jsonb_text($1::jsonb), 'UTF8')), 'hex')",
        json.dumps(canonical),
    )
    await owner.execute(
        "INSERT INTO control.review_operation_manifest "
        "(id, snapshot_id, site_id, workspace_id, schema_version, "
        " snapshot_digest, manifest_digest, operation_ids, "
        " dependency_pairs, completion_identities) "
        "VALUES ($1,$2,$3,$4,'reviewed-operations/v1',$5,$6,$7::uuid[],"
        "$8::jsonb,$9::jsonb)",
        manifest_id,
        snapshot_id,
        site_id,
        workspace_id,
        digest,
        manifest_digest,
        canonical["operation_ids"],
        json.dumps(canonical["dependency_pairs"]),
        json.dumps(canonical["completion_identities"]),
    )
    return manifest_id, str(manifest_digest)


async def _read_manifest(
    database: AgentSiteDatabase, snapshot_id: UUID
) -> dict[str, Any] | None:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        raw: Any = await owner.fetchval(
            "SELECT control.slaif_review_operation_manifest_read($1)", snapshot_id
        )
    if isinstance(raw, str):
        raw = json.loads(raw)
    if raw is None:
        return None
    assert isinstance(raw, dict)
    return raw


async def _accept_approval(
    database: AgentSiteDatabase, workspace_id: UUID
) -> tuple[UUID, str, str]:
    """(snapshot_id, snapshot_digest, manifest_digest) of the bound
    REVIEW snapshot + its companion (the exact 083/12 approval)."""
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        snapshot_id = await owner.fetchval(
            "SELECT review_snapshot_id FROM control.workspace WHERE id = $1",
            workspace_id,
        )
        stored_digest = await owner.fetchval(
            "SELECT digest::text FROM control.review_snapshot WHERE id = $1",
            snapshot_id,
        )
    manifest = await _read_manifest(database, snapshot_id)
    assert manifest is not None
    return UUID(str(snapshot_id)), str(stored_digest), str(manifest["manifest_digest"])


async def _enqueue_accept(
    database: AgentSiteDatabase,
    workspace_id: UUID,
    actor: UUID,
    *,
    snapshot_id: UUID,
    snapshot_digest: str,
    manifest_digest: str,
) -> list[Any]:
    # 083/12: the inner enqueue is owner-internal (no role EXECUTE
    # grants), so the whitebox stable-code tests exercise it as the
    # owner fixture; the slaif_control path is the 6-argument human
    # entry point (route tests).
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return list(
            await owner.fetch(
                "SELECT * FROM control.slaif_workspace_accept($1, $2, $3, $4, $5)",
                workspace_id,
                snapshot_id,
                snapshot_digest,
                manifest_digest,
                actor,
            )
        )


async def _enqueue_bound_accept(
    database: AgentSiteDatabase, workspace_id: UUID, actor: UUID
) -> list[Any]:
    """Enqueue with the exact approval of the bound snapshot +
    companion (the normal freeze -> accept flow)."""
    snapshot_id, snapshot_digest, manifest_digest = await _accept_approval(
        database, workspace_id
    )
    return await _enqueue_accept(
        database,
        workspace_id,
        actor,
        snapshot_id=snapshot_id,
        snapshot_digest=snapshot_digest,
        manifest_digest=manifest_digest,
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
            # 083/12: the 072 digest-less accept pair is dropped at 079;
            # the new inner enqueue is owner-internal (NO role EXECUTE -
            # this is what closes the actorless enqueue bypass) and the
            # new human entry point keeps the control grant.
            old_inner_exists = await owner.fetchval(
                "SELECT to_regprocedure("
                "'control.slaif_workspace_accept(uuid, uuid)') IS NOT NULL"
            )
            old_human_exists = await owner.fetchval(
                "SELECT to_regprocedure("
                "'control.slaif_human_agent_workspace_accept(uuid, uuid,"
                " uuid, text, uuid)') IS NOT NULL"
            )
            assert old_inner_exists is False
            assert old_human_exists is False
            accept_execute = await owner.fetchval(
                "SELECT has_function_privilege($1,"
                " 'control.slaif_workspace_accept(uuid, uuid, text, text,"
                " uuid)', 'EXECUTE')",
                role,
            )
            assert accept_execute is False, role
            human_accept_execute = await owner.fetchval(
                "SELECT has_function_privilege($1,"
                " 'control.slaif_human_agent_workspace_accept(uuid, uuid,"
                " uuid, text, text, uuid)', 'EXECUTE')",
                role,
            )
            assert human_accept_execute is (role == "slaif_control"), role
            # The 079 companion surface: the worker holds the identity
            # projection, the provenance check and the companion
            # completion; the read projection serves control + worker.
            # The standalone completion keeps NO online EXECUTE anymore.
            for function, expected in (
                (
                    "control.slaif_review_operation_identities(uuid, uuid, uuid[])",
                    "slaif_review_worker",
                ),
                (
                    "control.slaif_review_operation_provenance(uuid, uuid, uuid[])",
                    "slaif_review_worker",
                ),
                (
                    "control.slaif_review_snapshot_complete_with_manifest("
                    "uuid, jsonb, jsonb)",
                    "slaif_review_worker",
                ),
                (
                    "control.slaif_review_operation_manifest_read(uuid)",
                    "slaif_control,slaif_review_worker",
                ),
                ("control.slaif_review_snapshot_complete(uuid, jsonb)", None),
            ):
                holders = {
                    str(row["rolname"])
                    for row in await owner.fetch(
                        "SELECT r.rolname FROM pg_roles r"
                        " WHERE r.rolname LIKE 'slaif%' AND r.rolname <> 'slaif_owner'"
                        " AND has_function_privilege(r.rolname, $1, 'EXECUTE')",
                        function,
                    )
                }
                expected_set = set(expected.split(",")) if expected else set()
                assert holders == expected_set, (function, holders)

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
    manifest = await _read_manifest(database, snapshot_id)
    assert manifest is not None
    snapshot_digest = "ab" * 32
    manifest_digest = str(manifest["manifest_digest"])

    rows = await _enqueue_accept(
        database,
        workspace_id,
        actor,
        snapshot_id=snapshot_id,
        snapshot_digest=snapshot_digest,
        manifest_digest=manifest_digest,
    )
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
    # The durable payload carries the EXACT approval (083/12): both
    # digests plus the identity trio, nothing else.
    assert json.loads(payload) == {
        "snapshot_id": str(snapshot_id),
        "site_id": str(ids["site_id"]),
        "actor_user_account_id": str(actor),
        "snapshot_digest": snapshot_digest,
        "manifest_digest": manifest_digest,
    }

    # Idempotent while QUEUED (the same exact approval replays).
    again = await _enqueue_accept(
        database,
        workspace_id,
        actor,
        snapshot_id=snapshot_id,
        snapshot_digest=snapshot_digest,
        manifest_digest=manifest_digest,
    )
    assert str(again[0]["job_id"]) == str(job_id)

    # A DIFFERENT approval on the same live job is a typed refusal
    # (R4: never a 202 replay, never a silent fill).
    with pytest.raises(asyncpg.PostgresError) as mismatch:
        await _enqueue_accept(
            database,
            workspace_id,
            actor,
            snapshot_id=snapshot_id,
            snapshot_digest=snapshot_digest,
            manifest_digest="cd" * 32,
        )
    assert mismatch.value.sqlstate == "P0003"
    assert "ACCEPT_LIVE_JOB_MISMATCH" in str(mismatch.value)

    # Idempotent while CLAIMED.
    claimed = await _claim(database, "enqueue-test-claim", _WORKER_KINDS)
    assert len(claimed) == 1 and str(claimed[0]["id"]) == str(job_id)
    claimed_again = await _enqueue_accept(
        database,
        workspace_id,
        actor,
        snapshot_id=snapshot_id,
        snapshot_digest=snapshot_digest,
        manifest_digest=manifest_digest,
    )
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
            await _enqueue_accept(
                database,
                workspace_id,
                actor,
                snapshot_id=snapshot_id,
                snapshot_digest=snapshot_digest,
                manifest_digest=manifest_digest,
            )
        assert excinfo.value.sqlstate == "P0002"
        assert "WORKSPACE_NOT_IN_REVIEW" in str(excinfo.value)

    # WORKSPACE_NOT_FOUND for an unknown workspace.
    with pytest.raises(asyncpg.PostgresError) as excinfo:
        await _enqueue_accept(
            database,
            uuid4(),
            actor,
            snapshot_id=snapshot_id,
            snapshot_digest=snapshot_digest,
            manifest_digest=manifest_digest,
        )
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
        await _enqueue_accept(
            database,
            workspace_id,
            actor,
            snapshot_id=snapshot_id,
            snapshot_digest=snapshot_digest,
            manifest_digest=manifest_digest,
        )
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
        await _enqueue_accept(
            database,
            workspace_id,
            actor,
            snapshot_id=snapshot_id,
            snapshot_digest=snapshot_digest,
            manifest_digest=manifest_digest,
        )
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
    binding_manifest = await _read_manifest(database, snapshot_id)
    assert binding_manifest is not None
    manifest_digest = str(binding_manifest["manifest_digest"])

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
            " title, delegation_preset, effective_scopes, version_facts,"
            " status, expires_at)"
            " VALUES ($1,$2,$2,'Accept Active WS','L4','[\"page:read\"]'::jsonb,"
            + _CURRENT_VERSION_FACTS
            + ","
            " 'ACTIVE', now()+interval '1 hour') RETURNING id",
            site_id,
            ids["delegator_id"],
        )
        # 409 fixture: bound COMPLETE snapshot but no live ACCEPT job and a
        # non-REVIEW status (the enqueue's status gate must fire).
        conflict_ws = await owner.fetchval(
            "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
            " title, delegation_preset, effective_scopes, version_facts,"
            " status, expires_at)"
            " VALUES ($1,$2,$2,'Accept Conflict WS','L4','[\"page:read\"]'::jsonb,"
            + _CURRENT_VERSION_FACTS
            + ","
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
        # 083/12: the 409 case must pass the companion gate to reach
        # the inner status gate: seed the companion a real freeze would
        # have created (the conflict workspace has no pending session
        # state: an empty approval is its honest shape).
        _conflict_manifest_id, conflict_manifest_digest = await _seed_companion(
            owner,
            workspace_id=conflict_ws,
            site_id=site_id,
            snapshot_id=conflict_snapshot,
            digest=digest,
            operations=[],
            dependencies=[],
            identities=[],
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
            "manifest_digest": manifest_digest,
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

                # 083/12: the platform administrator's identical body
                # carries a DIFFERENT actor in the exact approval, so
                # the live-job gate refuses the replay (typed P0003,
                # mapped to the safe 503 class): the original owner job
                # is untouched (no second job, no actor substitution).
                admin_post = await post(sessions["admin"], valid_body)
                assert admin_post.status_code == 503, admin_post.text
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    admin_jobs = await owner.fetch(
                        "SELECT id, status, payload->>"
                        "'actor_user_account_id' AS actor"
                        " FROM control.review_job"
                        " WHERE workspace_id = $1 AND job_kind = 'ACCEPT'"
                        " ORDER BY id",
                        workspace_id,
                    )
                assert len(admin_jobs) == 1
                assert admin_jobs[0]["id"] == UUID(str(job_id))
                assert admin_jobs[0]["status"] == "QUEUED"
                assert admin_jobs[0]["actor"] == str(users["owner"])
                status, bound = await _workspace_state(database, workspace_id)
                assert (status, bound) == ("ACCEPT_QUEUED", snapshot_id)

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
                bad_manifest = await post(
                    sessions["owner"],
                    {**valid_body, "manifest_digest": "00" * 32},
                )
                assert bad_snapshot.status_code == 404, bad_snapshot.text
                assert bad_digest.status_code == 404, bad_digest.text
                # 083/12: a valid snapshot + digest with a WRONG manifest
                # digest is a companion mismatch: the same uniform 404
                # class, no manifest oracle at the route.
                assert bad_manifest.status_code == 404, bad_manifest.text
                # Indistinguishable apart from the per-request id: the
                # stable envelope (code/message/details) is byte-identical.
                assert _error_envelope(bad_snapshot) == _error_envelope(bad_digest)
                assert _error_envelope(bad_snapshot) == _error_envelope(binding)
                assert _error_envelope(bad_manifest) == _error_envelope(bad_digest)

                # Strict body: 422 for every malformed acknowledgement.
                for bad_body in (
                    {**valid_body, "acknowledge_summary": False},
                    {**valid_body, "acknowledge_summary": 1},
                    {
                        "snapshot_id": str(snapshot_id),
                        "digest": digest,
                    },
                    {
                        "snapshot_id": str(snapshot_id),
                        "digest": digest,
                        "acknowledge_summary": True,
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
                        "manifest_digest": conflict_manifest_digest,
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

        rows = await _enqueue_bound_accept(
            database, ids["workspace_id"], ids["delegator_id"]
        )
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
        # 083/12 R5: the promotion receipt names the exact approved
        # binding: the companion a real freeze created and the applied
        # operation ids, equal to the frozen U.
        binding_manifest = await _read_manifest(database, snapshot_id)
        assert binding_manifest is not None
        assert str(audit["manifest_id"]) == str(binding_manifest["manifest_id"])
        assert str(audit["manifest_digest"]) == str(binding_manifest["manifest_digest"])
        assert [
            str(operation) for operation in audit["applied_operation_ids"]
        ] == sorted(str(operation) for operation in binding_manifest["operation_ids"])

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


async def _seed_typed_media_references(
    owner: Any, site_id: UUID, media_ids: list[UUID]
) -> None:
    """Trusted OWNER fixture: canonical typed field/item/translation
    references to the given pending media ids (no page composition
    reference).  Covers the 076 v2 typed media closure's reference
    modes: scalar base, localized scalar, base many, localized many,
    and the document field_type.  Fixture data only, like every other
    owner-seeded base row in this module.
    """

    media_type_id = uuid4()
    photo_field_id = uuid4()
    gallery_field_id = uuid4()
    item_1_id = uuid4()
    item_2_id = uuid4()
    doc_type_id = uuid4()
    doc_field_id = uuid4()
    item_3_id = uuid4()
    translation_1_id = uuid4()
    translation_2_id = uuid4()
    scalar_base, localized_scalar, base_many, localized_many, document = (
        str(value) for value in media_ids
    )
    await owner.execute(
        "INSERT INTO content.content_type_base "
        '(id,site_id,"key",labels,slug_pattern,status,'
        "definition_version,settings) VALUES "
        "($1,$2,'typed-media','{\"en\":\"Typed media\"}'::jsonb,"
        "'/typed-media/{slug}','ACTIVE',1,'{}'::jsonb),"
        "($3,$2,'typed-document','{\"en\":\"Typed document\"}'::jsonb,"
        "'/typed-document/{slug}','ACTIVE',1,'{}'::jsonb)",
        media_type_id,
        site_id,
        doc_type_id,
    )
    await owner.execute(
        "INSERT INTO content.field_definition_base "
        '(id,site_id,type_id,"key",label,field_type,required,'
        'localized,cardinality,"position",validation,ui_options,'
        "definition_version) VALUES "
        "($1,$2,$3,'photo','Photo','media',false,false,1,0,"
        "'{}'::jsonb,'{}'::jsonb,1),"
        "($4,$2,$3,'gallery','Gallery','media',false,true,2,1,"
        "'{}'::jsonb,'{}'::jsonb,1),"
        "($5,$2,$6,'doc','Document','document',false,false,1,0,"
        "'{}'::jsonb,'{}'::jsonb,1)",
        photo_field_id,
        site_id,
        media_type_id,
        gallery_field_id,
        doc_field_id,
        doc_type_id,
    )
    await owner.execute(
        "INSERT INTO content.content_item_base "
        "(id,site_id,type_id,slug,status,type_definition_version,"
        '"values",row_version) VALUES '
        "($1,$2,$3,'typed-item-scalar','DRAFT',1,$4::jsonb,1),"
        "($5,$2,$3,'typed-item-many','DRAFT',1,$6::jsonb,1),"
        "($7,$2,$8,'typed-item-document','DRAFT',1,$9::jsonb,1)",
        item_1_id,
        site_id,
        media_type_id,
        json.dumps({"photo": scalar_base}),
        item_2_id,
        json.dumps({"gallery": [base_many]}),
        item_3_id,
        doc_type_id,
        json.dumps({"doc": document}),
    )
    await owner.execute(
        "INSERT INTO content.content_item_translation_base "
        "(id,site_id,item_id,locale,localized_values,row_version) VALUES "
        "($1,$2,$3,'fr',$4::jsonb,1), ($5,$2,$6,'fr',$7::jsonb,1)",
        translation_1_id,
        site_id,
        item_1_id,
        json.dumps({"photo": localized_scalar}),
        translation_2_id,
        item_2_id,
        json.dumps({"gallery": [localized_many]}),
    )


async def _seed_scalar_media_reference(
    owner: Any,
    site_id: UUID,
    media_id: UUID,
    *,
    uppercase: bool = False,
) -> None:
    """Trusted OWNER fixture: exactly one canonical typed media field
    reference (scalar base ``content_item`` value) to the given pending
    media id; no page composition reference and no other reference
    mode.  ``uppercase`` stores the declared reference in the accepted
    non-canonical uppercase UUID spelling (product validators accept
    and preserve it; the 076 materializer normalizes it by UUID cast),
    so the publicize guard must match by UUID identity, not raw text.
    Fixture data only, like every other owner-seeded base row here.
    """

    media_type_id = uuid4()
    photo_field_id = uuid4()
    item_id = uuid4()
    reference = str(media_id).upper() if uppercase else str(media_id)
    await owner.execute(
        "INSERT INTO content.content_type_base "
        '(id,site_id,"key",labels,slug_pattern,status,'
        "definition_version,settings) VALUES "
        "($1,$2,'typed-media','{\"en\":\"Typed media\"}'::jsonb,"
        "'/typed-media/{slug}','ACTIVE',1,'{}'::jsonb)",
        media_type_id,
        site_id,
    )
    await owner.execute(
        "INSERT INTO content.field_definition_base "
        '(id,site_id,type_id,"key",label,field_type,required,'
        'localized,cardinality,"position",validation,ui_options,'
        "definition_version) VALUES "
        "($1,$2,$3,'photo','Photo','media',false,false,1,0,"
        "'{}'::jsonb,'{}'::jsonb,1)",
        photo_field_id,
        site_id,
        media_type_id,
    )
    await owner.execute(
        "INSERT INTO content.content_item_base "
        "(id,site_id,type_id,slug,status,type_definition_version,"
        '"values",row_version) VALUES '
        "($1,$2,$3,'typed-item-scalar','DRAFT',1,$4::jsonb,1)",
        item_id,
        site_id,
        media_type_id,
        json.dumps({"photo": reference}),
    )


@pytest.mark.asyncio
async def test_accept_worker_field_referenced_media_publishes_atomically(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Typed field closure: a NEW pending asset referenced ONLY by a
    canonical media field_definition/content_item pair (no page
    composition reference) is in the frozen typed media closure and
    must be published atomically with its promotion.  The declared
    reference uses an accepted non-canonical uppercase UUID spelling,
    so the publicize guard must compare UUID identity, not raw text.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_pending_media_site(
        database,
        media_root,
        workspace_count=1,
        media_per_workspace=1,
        with_composition=False,
    )
    entry = ids["workspaces"][0]
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await _seed_scalar_media_reference(
                owner, ids["site_id"], entry["media_ids"][0], uppercase=True
            )
            base_revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
        assert base_revision == 0

        ids_one = {**ids, "workspace_id": entry["workspace_id"]}
        await _freeze_workspace(database, ids_one, pool)
        rows = await _enqueue_bound_accept(
            database, entry["workspace_id"], ids["delegator_id"]
        )
        job_id = UUID(str(rows[0]["job_id"]))
        job = await _claim_accept(database, "field-accept-1")
        assert str(job["id"]) == str(job_id)
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "SUCCEEDED", result.error

        digest = entry["media_digest"]
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            media_row = await owner.fetchrow(
                "SELECT public_status, published_at, content_hash FROM"
                " content.media_asset_base WHERE id = $1",
                entry["media_id"],
            )
            audit_rows = await owner.fetch("SELECT * FROM audit.promotion ORDER BY id")
            outbox_rows = await owner.fetch(
                "SELECT * FROM control.cache_outbox ORDER BY id"
            )
        assert revision == base_revision + 1
        assert media_row is not None
        assert str(media_row["public_status"]) == "public"
        assert media_row["published_at"] is not None
        assert media_row["content_hash"] == digest
        assert len(audit_rows) == 1
        assert len(outbox_rows) == 1
        outbox_payload = json.loads(outbox_rows[0]["payload"])
        assert [e["media_id"] for e in outbox_payload["media_manifest"]] == [
            str(entry["media_id"])
        ]
        public_path = _public_path(media_root, digest)
        assert public_path.is_file()
        assert hashlib.sha256(public_path.read_bytes()).hexdigest() == digest
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_accept_worker_typed_media_closure_all_reference_modes_publish(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """All typed reference modes publish atomically: scalar base,
    localized scalar, base many, localized many and the document
    field_type (no page composition reference for any of them); an
    unrelated canonical inventory row keeps its prior private state.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_pending_media_site(
        database,
        media_root,
        workspace_count=1,
        media_per_workspace=5,
        with_composition=False,
    )
    entry = ids["workspaces"][0]
    unreferenced_id = uuid4()
    unreferenced_hash = "ab" * 32
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await _seed_typed_media_references(
                owner, ids["site_id"], entry["media_ids"]
            )
            # Unrelated canonical inventory: promoted by nothing,
            # referenced by nothing; must keep its prior private state.
            await owner.execute(
                "INSERT INTO content.media_asset_base (id, site_id, "
                "uploaded_by, filename, mime_type, size_bytes, content_hash,"
                " storage_key, alt_text, metadata) VALUES"
                " ($1,$2,$3,'unreferenced.png','image/png',1,$4,"
                " $5,'unreferenced','{}'::jsonb)",
                unreferenced_id,
                ids["site_id"],
                ids["delegator_id"],
                unreferenced_hash,
                f"sha256/{unreferenced_hash[:2]}/"
                f"{unreferenced_hash[2:4]}/{unreferenced_hash}",
            )
            base_revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
        assert base_revision == 0

        ids_one = {**ids, "workspace_id": entry["workspace_id"]}
        await _freeze_workspace(database, ids_one, pool)
        rows = await _enqueue_bound_accept(
            database, entry["workspace_id"], ids["delegator_id"]
        )
        job_id = UUID(str(rows[0]["job_id"]))
        job = await _claim_accept(database, "typed-accept-1")
        assert str(job["id"]) == str(job_id)
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "SUCCEEDED", result.error

        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            media_rows = await owner.fetch(
                "SELECT id, public_status, published_at, content_hash FROM"
                " content.media_asset_base WHERE site_id = $1 ORDER BY id",
                ids["site_id"],
            )
            audit_rows = await owner.fetch("SELECT * FROM audit.promotion ORDER BY id")
            outbox_rows = await owner.fetch(
                "SELECT * FROM control.cache_outbox ORDER BY id"
            )
        assert revision == base_revision + 1
        by_id = {str(row["id"]): row for row in media_rows}
        # Every typed-referenced pending asset is promoted AND public.
        for media_id, digest in zip(
            entry["media_ids"], entry["media_digests"], strict=True
        ):
            row = by_id[str(media_id)]
            assert str(row["public_status"]) == "public", (
                f"typed-referenced media {media_id} must be public"
            )
            assert row["published_at"] is not None
            assert row["content_hash"] == digest
            public_path = _public_path(media_root, digest)
            assert public_path.is_file()
            assert hashlib.sha256(public_path.read_bytes()).hexdigest() == digest
        # The unrelated canonical inventory row is untouched.
        unreferenced = by_id[str(unreferenced_id)]
        assert str(unreferenced["public_status"]) == "private"
        assert unreferenced["published_at"] is None
        # Exactly one promotion; the manifest is the sorted typed closure.
        assert len(audit_rows) == 1
        assert len(outbox_rows) == 1
        outbox_payload = json.loads(outbox_rows[0]["payload"])
        assert [e["media_id"] for e in outbox_payload["media_manifest"]] == [
            str(media_id) for media_id in sorted(entry["media_ids"])
        ]
    finally:
        await boundary.stop()
        await pool.close()


_PENDING_PNG = b"\x89PNG\r\n\x1a\na5-a6-new-pending-media"


def _pending_png(index: int) -> bytes:
    return b"\x89PNG\r\n\x1a\na5-a6-pending-" + index.to_bytes(4, "big")


def _publish_pending_bytes(media_root: Path, payload: bytes) -> tuple[str, str]:
    """Real store publish of the pending bytes; (digest, storage_key)."""

    store = MediaStore(media_root)
    staged_path = store.create_staging_path()
    staged_path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    store.publish(StagedMedia(staged_path, digest, len(payload), "image/png"))
    return digest, f"sha256/{digest[:2]}/{digest[2:4]}/{digest}"


async def _seed_pending_media_site(
    database: AgentSiteDatabase,
    media_root: Path,
    *,
    workspace_count: int,
    media_per_workspace: int = 1,
    with_composition: bool = True,
) -> dict[str, Any]:
    """Site + N workspaces, each with NEW pending media uploads.

    Every pending asset is created through the real product registration
    SQL (``slaif_agent_media_register``) inside a genuine COW session with
    the real capability context, and its bytes are stored through the real
    MediaStore publish path.  No canonical media row exists before a
    promotion.  With ``with_composition`` (the default) each workspace's
    composition references its first pending asset, so the frozen media
    closure is exactly that asset; otherwise the assets carry no page
    composition reference (field-reference regressions).

    A single-workspace multi-media seed uses distinct bytes (the
    workspace-visible registration dedupe would otherwise collapse them
    into one pending row); the default one-per-workspace seed keeps the
    same bytes across workspaces (the A5 same-hash scenario).
    """

    await upgrade(database.settings)
    await reconcile(database.settings)
    if media_per_workspace == 1:
        payloads = [_PENDING_PNG] * workspace_count
    else:
        payloads = [
            _pending_png(index)
            for index in range(workspace_count * media_per_workspace)
        ]
    published = [_publish_pending_bytes(media_root, payload) for payload in payloads]
    scopes = [
        "site:read",
        "page:read",
        "component-structure:create",
        "component-content-props:write",
        "media:upload",
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
                gen_random_uuid(), 'LOCAL', 'PendingMedia.Delegator',
                'pendingmedia.delegator', $1, 'Pending Media Delegator', 'ACTIVE'
            ) RETURNING id
            """,
            _AGGON2,
        )
        site_id = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name, default_locale,"
            " component_catalog_version) VALUES ('pending-media-int', 'Pending"
            " Media Int', 'en-US', 'catalog-v1') RETURNING id"
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
            ' \'{"family":"system","scale":"balanced","weight":"regular"}\'::jsonb,'
            ' \'{"content_width":"md","spacing":"md","grid_gap":"md"}\'::jsonb,'
            ' \'{"radius":"md","shadow":"sm"}\'::jsonb)',
            site_id,
        )
        page_id = await owner.fetchval(
            "INSERT INTO content.page_base (id, site_id, slug, title, status,"
            " locale) VALUES (gen_random_uuid(), $1,'home','Home','PUBLISHED',"
            " 'en-US') RETURNING id",
            site_id,
        )
        section_id = await owner.fetchval(
            "INSERT INTO content.page_composition_base (id, site_id, page_id,"
            " component_type, schema_version, parent_id, slot_key, order_key,"
            " props) VALUES (gen_random_uuid(), $1,$2,'Section','1',NULL,"
            " 'default',0,'{}'::jsonb) RETURNING id",
            site_id,
            page_id,
        )
        workspaces: list[dict[str, Any]] = []
        for index in range(workspace_count):
            workspace_id = await owner.fetchval(
                "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
                " title, delegation_preset, effective_scopes, version_facts,"
                " status, expires_at) VALUES ($1,$2,$2,'Pending Media W' || $3,"
                "'L4',$4::jsonb,"
                + _CURRENT_VERSION_FACTS
                + ",'ACTIVE', now()+interval '1 hour') RETURNING id",
                site_id,
                delegator_id,
                str(index),
                json.dumps(scopes),
            )
            token, public_id, secret_digest = generate_capability_token()
            # The product issues capabilities with explicit quotas
            # (039 create surface); the raw fixture mirrors it for the
            # upload quota (column default 0 would exhaust at once).
            capability_id = await owner.fetchval(
                "INSERT INTO control.capability (workspace_id, public_id,"
                " secret_digest, scopes, upload_quota, expires_at)"
                " VALUES ($1,$2,$3,$4::jsonb, 16, now()+interval '30 minutes')"
                " RETURNING id",
                workspace_id,
                public_id,
                secret_digest,
                json.dumps(scopes),
            )
            workspaces.append(
                {
                    "workspace_id": UUID(str(workspace_id)),
                    "capability_id": UUID(str(capability_id)),
                }
            )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        capability_rows = await owner.fetch(
            "SELECT workspace_id, id, created_at, expires_at"
            " FROM control.capability WHERE id = ANY($1::uuid[])",
            [str(w["capability_id"]) for w in workspaces],
        )
    contexts: dict[UUID, AgentCapabilityContext] = {
        UUID(str(row["workspace_id"])): AgentCapabilityContext(
            capability_id=UUID(str(row["id"])),
            site_id=UUID(str(site_id)),
            workspace_id=UUID(str(row["workspace_id"])),
            delegator_id=UUID(str(delegator_id)),
            scopes=frozenset(scopes),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )
        for row in capability_rows
    }
    assert len(contexts) == len(workspaces)
    agent_pool = await database.role_pool("slaif_agent_runtime")
    try:
        payload_index = 0
        for entry in workspaces:
            context = contexts[entry["workspace_id"]]
            media_ids: list[UUID] = []
            media_digests: list[str] = []
            storage_keys: list[str] = []
            for media_slot in range(media_per_workspace):
                digest, storage_key = published[payload_index]
                payload = payloads[payload_index]
                payload_index += 1
                # Real product upload mutation (genuine COW session with
                # the real reservation, registration SQL, audit and 078
                # completion journal).
                key = f"083-12-pending-media-{entry['workspace_id']}-m{media_slot}"
                upload_digest = hashlib.sha256(
                    json.dumps(
                        {
                            "method": "POST",
                            "path": "/api/agent/v1/media/assets",
                            "key": key,
                            "digest": digest,
                            "filename": "pending.png",
                            "mime_type": "image/png",
                            "size_bytes": len(payload),
                            "alt_text": f"Pending media {entry['workspace_id']}",
                            "metadata": {},
                        },
                        sort_keys=True,
                    ).encode()
                ).hexdigest()

                async def register_media(
                    service: AgentCowContentModelService,
                    digest: str = digest,
                    storage_key: str = storage_key,
                    payload: bytes = payload,
                    workspace_id: UUID = entry["workspace_id"],
                ) -> Any:
                    return await service.create_media_asset(
                        site_id=UUID(str(site_id)),
                        uploaded_by=UUID(str(delegator_id)),
                        filename="pending.png",
                        mime_type="image/png",
                        size_bytes=len(payload),
                        content_hash=digest,
                        storage_key=storage_key,
                        alt_text=f"Pending media {workspace_id}",
                        metadata={},
                    )

                registered = await execute_agent_mutation(
                    database=_CowPoolAdapter(agent_pool),
                    context=context,
                    key=key,
                    digest=upload_digest,
                    mutate=register_media,
                    resource_type="media_asset",
                    status_code=201,
                    quota_kind="upload",
                    action="MEDIA_UPLOADED",
                    method="POST",
                )
                assert registered.operation_id is not None
                media_ids.append(UUID(str(registered.record["id"])))
                media_digests.append(digest)
                storage_keys.append(storage_key)
            entry["media_ids"] = media_ids
            entry["media_id"] = media_ids[0]
            entry["media_digests"] = media_digests
            entry["storage_keys"] = storage_keys
            entry["media_digest"] = media_digests[0]
            entry["storage_key"] = storage_keys[0]
            if with_composition:
                # A composition node that references exactly the first
                # pending asset, so the frozen media closure is exactly
                # that asset (real product create mutation).
                image_props = {
                    "mediaId": str(media_ids[0]),
                    "alt": f"Pending image {entry['workspace_id']}",
                }

                async def create_image(
                    service: AgentCowContentModelService,
                    props: dict[str, Any] = image_props,
                ) -> Any:
                    return await service.add_component_for_site(
                        UUID(str(site_id)),
                        UUID(str(page_id)),
                        AgentCreateCompositionNodeRequest(
                            component_type="Image",
                            parent_id=str(section_id),
                            slot_key="default",
                            props=props,
                        ),
                    )

                created = await execute_agent_mutation(
                    database=_CowPoolAdapter(agent_pool),
                    context=context,
                    key=f"083-12-pending-media-{entry['workspace_id']}-image",
                    digest=mutation_digest(
                        method="POST",
                        path=f"/sites/{site_id}/pages/{page_id}/components",
                        body={
                            "component_type": "Image",
                            "parent_id": str(section_id),
                            "slot_key": "default",
                            "props": image_props,
                        },
                    ),
                    mutate=create_image,
                    resource_type="composition_node",
                    status_code=201,
                    quota_kind="mutation",
                    action="COMPONENT_CREATED",
                    method="POST",
                )
                assert created.operation_id is not None
                entry["image_id"] = UUID(str(created.record["id"]))
            else:
                entry["image_id"] = None
    finally:
        await agent_pool.close()
    return {
        "delegator_id": UUID(str(delegator_id)),
        "site_id": UUID(str(site_id)),
        "page_id": UUID(str(page_id)),
        "section_id": UUID(str(section_id)),
        "media_digest": published[0][0],
        "storage_key": published[0][1],
        "workspaces": workspaces,
    }


@pytest.mark.asyncio
async def test_accept_worker_new_pending_same_hash_conflict(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """A5: two NEW pending same-hash uploads; the first promotion commits
    the canonical row, the second promotion deterministically reaches the
    (site, content_hash) unique key and terminates as a typed conflict
    with the whole transaction rolled back (no partial canonical effect).
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_pending_media_site(database, media_root, workspace_count=2)
    first = ids["workspaces"][0]
    second = ids["workspaces"][1]
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

        # Workspace 1: the real NEW-pending acceptance succeeds and
        # publishes its own asset inside the single reviewer transaction.
        ids_a = {**ids, "workspace_id": first["workspace_id"]}
        await _freeze_workspace(database, ids_a, pool)
        rows = await _enqueue_bound_accept(
            database, first["workspace_id"], ids["delegator_id"]
        )
        job_a = UUID(str(rows[0]["job_id"]))
        job = await _claim_accept(database, "a5-accept-1")
        assert str(job["id"]) == str(job_a)
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "SUCCEEDED", result.error
        digest = ids["media_digest"]
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            media_a = await owner.fetchrow(
                "SELECT id, public_status, published_at, content_hash FROM"
                " content.media_asset_base WHERE id = $1",
                first["media_id"],
            )
            audit_rows = await owner.fetch("SELECT * FROM audit.promotion ORDER BY id")
            outbox_rows = await owner.fetch(
                "SELECT * FROM control.cache_outbox ORDER BY id"
            )
        assert revision == base_revision + 1
        assert media_a is not None
        assert str(media_a["id"]) == str(first["media_id"])
        assert str(media_a["public_status"]) == "public"
        assert media_a["published_at"] is not None
        assert media_a["content_hash"] == digest
        assert len(audit_rows) == 1
        assert len(outbox_rows) == 1
        outbox_payload = json.loads(outbox_rows[0]["payload"])
        assert [e["media_id"] for e in outbox_payload["media_manifest"]] == [
            str(first["media_id"])
        ]
        public_path = _public_path(media_root, digest)
        assert public_path.is_file()
        assert hashlib.sha256(public_path.read_bytes()).hexdigest() == digest

        # Workspace 2: frozen AFTER the first promotion.  Its NEW pending
        # asset keeps a distinct id but the same (site, content_hash); the
        # promotion must reach that unique key deterministically.
        ids_b = {**ids, "workspace_id": second["workspace_id"]}
        await _freeze_workspace(database, ids_b, pool)
        rows = await _enqueue_bound_accept(
            database, second["workspace_id"], ids["delegator_id"]
        )
        job_b = UUID(str(rows[0]["job_id"]))
        job = await _claim_accept(database, "a5-accept-2")
        assert str(job["id"]) == str(job_b)
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "FAILED", result.error
        assert result.error == "UNIQUE_CONSTRAINT_CONFLICT"

        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            media_a = await owner.fetchrow(
                "SELECT id, public_status, content_hash FROM"
                " content.media_asset_base WHERE id = $1",
                first["media_id"],
            )
            media_b = await owner.fetchrow(
                "SELECT id FROM content.media_asset_base WHERE id = $1",
                second["media_id"],
            )
            audit_count = await owner.fetchval(
                "SELECT count(*) FROM audit.promotion WHERE workspace_id = $1",
                second["workspace_id"],
            )
            outbox_count = await owner.fetchval(
                "SELECT count(*) FROM control.cache_outbox WHERE workspace_id = $1",
                second["workspace_id"],
            )
            workspace_b = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                second["workspace_id"],
            )
            job_b_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_b,
            )
            pending_b = await owner.fetchval(
                "SELECT count(*) FROM content.media_asset_changes WHERE"
                " session_id = $1",
                second["workspace_id"],
            )
        # Full rollback of the refused promotion: nothing canonical
        # changed for workspace 2; the first asset is untouched.
        assert revision == base_revision + 1
        assert str(media_a["id"]) == str(first["media_id"])
        assert str(media_a["public_status"]) == "public"
        assert media_a["content_hash"] == digest
        assert media_b is None
        assert audit_count == 0
        assert outbox_count == 0
        assert str(workspace_b["status"]) == "CONFLICTED"
        assert workspace_b["accepted_at"] is None
        assert job_b_row["status"] == "FAILED"
        assert job_b_row["error"] == "UNIQUE_CONSTRAINT_CONFLICT"
        # The refused session's pending state survives for re-freeze.
        assert pending_b >= 1
        # The shared public bytes were not overwritten by the refused run.
        assert hashlib.sha256(public_path.read_bytes()).hexdigest() == digest
    finally:
        await boundary.stop()
        await pool.close()


_A6_WITNESS_SQL = (
    "CREATE SCHEMA a6witness;",
    "CREATE SEQUENCE a6witness.a6_reached_seq;",
    "CREATE TABLE a6witness.a6_reached ("
    " id bigint GENERATED ALWAYS AS IDENTITY,"
    " reached_at timestamptz NOT NULL DEFAULT now(),"
    " site_id uuid NOT NULL,"
    " workspace_id uuid NOT NULL,"
    " media_id uuid NOT NULL,"
    " observed_public_status text NOT NULL"
    ");",
    """
    CREATE FUNCTION a6witness.a6_injection() RETURNS trigger AS $fn$
    DECLARE
        reference_count integer;
        media_id uuid;
        observed_status text;
    BEGIN
        SELECT count(*) INTO reference_count
        FROM content.page_composition_base AS c
        JOIN content.media_asset_base AS m
          ON m.site_id = c.site_id AND m.id = (c.props ->> 'mediaId')::uuid
        WHERE c.site_id = NEW.site_id;
        SELECT m.id, m.public_status
        INTO media_id, observed_status
        FROM content.page_composition_base AS c
        JOIN content.media_asset_base AS m
          ON m.site_id = c.site_id AND m.id = (c.props ->> 'mediaId')::uuid
        WHERE c.site_id = NEW.site_id
        LIMIT 1;
        IF reference_count <> 1 OR media_id IS NULL THEN
            RAISE EXCEPTION 'A6_INJECTION_GUARD_NO_REFERENCE'
                USING ERRCODE = 'P0001';
        END IF;
        IF observed_status <> 'public' THEN
            RAISE EXCEPTION 'A6_INJECTION_GUARD_NOT_PUBLIC'
                USING ERRCODE = 'P0001';
        END IF;
        PERFORM nextval('a6witness.a6_reached_seq');
        INSERT INTO a6witness.a6_reached
            (site_id, workspace_id, media_id, observed_public_status)
        VALUES (NEW.site_id, NEW.workspace_id, media_id, observed_status);
        RAISE EXCEPTION 'A6_FORCED_FAILURE' USING ERRCODE = 'P0001';
    END
    $fn$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog;
    """,
    "CREATE TRIGGER a6_forced_failure BEFORE INSERT ON audit.promotion"
    " FOR EACH ROW EXECUTE FUNCTION a6witness.a6_injection();",
)

_A6_WITNESS_DROP_SQL = (
    "DROP TRIGGER IF EXISTS a6_forced_failure ON audit.promotion;",
    "DROP FUNCTION IF EXISTS a6witness.a6_injection();",
    "DROP TABLE IF EXISTS a6witness.a6_reached;",
    "DROP SEQUENCE IF EXISTS a6witness.a6_reached_seq;",
    "DROP SCHEMA IF EXISTS a6witness;",
)


async def _a6_witness_start(database: AgentSiteDatabase) -> None:
    """Trusted disposable AFTER-both witness (test-only, owner-created).

    The trigger fires on the promotion audit INSERT, i.e. inside the
    single reviewer transaction AFTER the foundation promotion and the
    in-transaction publication mark.  Its guards therefore raise (and the
    test fails on the missing witness) if either real effect is absent.
    The sequence is non-transactional, so it is the independent witness
    that the guarded point was reached before the forced rollback.
    """

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        for statement in _A6_WITNESS_SQL:
            await owner.execute(statement)
        # Consume one value so the trigger's own nextval is observable.
        await owner.fetchval("SELECT nextval('a6witness.a6_reached_seq')")


async def _a6_witness_stop(database: AgentSiteDatabase) -> None:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        for statement in _A6_WITNESS_DROP_SQL:
            await owner.execute(statement)


async def _a6_public_read(
    database: AgentSiteDatabase, media_root: Path, digest: str
) -> httpx.Response:
    """One actual sessionless public digest read on the real media app.

    Real application wiring (real media DB role, real store on the same
    root) so the test proves what the public route actually serves; an
    object-path check alone cannot establish that.
    """

    store = MediaStore(media_root)
    media_database = MediaDatabase(_media_settings(database, store.root))
    media_app = create_media_app(
        settings=ServiceSettings.for_test(),
        media_settings=media_database.settings,
        database=media_database,
        store=store,
    )
    async with media_app.router.lifespan_context(media_app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=media_app),
            base_url="http://a6-public-read.test",
        ) as client:
            return await client.get(
                f"/v1/public/sha256/{digest[:2]}/{digest[2:4]}/{digest}"
            )


async def _pending_change_rows(
    owner: Any, session_id: UUID
) -> tuple[list[asyncpg.Record], list[asyncpg.Record]]:
    """Exact APP-owned pending COW change rows for one session.

    Full rows (operation identities included) from the media and
    composition change tables in deterministic order, for exact
    before/after preservation comparison.
    """

    media_rows = await owner.fetch(
        "SELECT * FROM content.media_asset_changes WHERE session_id = $1"
        " ORDER BY operation_id, 3",
        session_id,
    )
    composition_rows = await owner.fetch(
        "SELECT * FROM content.page_composition_changes WHERE session_id = $1"
        " ORDER BY operation_id, 3",
        session_id,
    )
    return media_rows, composition_rows


@pytest.mark.asyncio
async def test_accept_worker_after_both_effects_rollback_and_recovery(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """A6: failure AFTER both the real foundation promotion and the real
    in-transaction publication mark rolls the single reviewer
    transaction back (canonical media, content, revision, promotion
    audit, job success and outbox all absent), the pending state and the
    phase-1 byte copy survive, and the same job re-claimed after the
    trusted disposable failure is removed promotes for real.  The
    surviving pending COW change rows are asserted exactly, the promoted
    composition node is absent from the base, and actual sessionless
    public reads prove the orphan object is not served before recovery
    and serves the exact stored bytes after it.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_pending_media_site(database, media_root, workspace_count=1)
    entry = ids["workspaces"][0]
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        # Exact APP-owned pending rows before the injection attempt; the
        # rolled-back attempt must preserve them exactly.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            media_before, composition_before = await _pending_change_rows(
                owner, entry["workspace_id"]
            )
        ids_one = {**ids, "workspace_id": entry["workspace_id"]}
        await _freeze_workspace(database, ids_one, pool)
        rows = await _enqueue_bound_accept(
            database, entry["workspace_id"], ids["delegator_id"]
        )
        job_id = UUID(str(rows[0]["job_id"]))
        job = await _claim_accept(database, "a6-accept-1")
        assert str(job["id"]) == str(job_id)

        await _a6_witness_start(database)
        try:
            result = await run_accept_job(pool, settings, job, media=boundary)
        finally:
            # Remove the injection before the recovery attempt; the
            # sequence/table remain until the witness assertions below.
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.execute(_A6_WITNESS_DROP_SQL[0])

        assert result.status == "ROLLED_BACK", (result.status, result.error)
        digest = ids["media_digest"]
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            media_row = await owner.fetchrow(
                "SELECT id FROM content.media_asset_base WHERE id = $1",
                entry["media_id"],
            )
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            audit_count = await owner.fetchval("SELECT count(*) FROM audit.promotion")
            outbox_count = await owner.fetchval(
                "SELECT count(*) FROM control.cache_outbox"
            )
            workspace_row = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                entry["workspace_id"],
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
            # Independent non-transactional witness: exactly one advance
            # proves the guarded point (after BOTH real effects) was
            # actually reached inside the rolled-back transaction.
            sequence = await owner.fetchrow(
                "SELECT last_value, is_called FROM a6witness.a6_reached_seq"
            )
            # The trigger's own in-transaction row must have rolled back.
            witness_rows = await owner.fetchval(
                "SELECT count(*) FROM a6witness.a6_reached"
            )
            # The session's pending COW change rows (the media
            # registration and the Image composition node) must survive
            # the rolled-back transaction exactly as before the attempt.
            media_pending, composition_pending = await _pending_change_rows(
                owner, entry["workspace_id"]
            )
            promoted_composition = await owner.fetchval(
                "SELECT count(*) FROM content.page_composition_base WHERE id = $1",
                entry["image_id"],
            )
        assert media_row is None
        assert revision == 0
        assert audit_count == 0
        assert outbox_count == 0
        assert str(workspace_row["status"]) == "ACCEPT_QUEUED"
        assert workspace_row["accepted_at"] is None
        assert job_row["status"] == "CLAIMED"
        assert job_row["error"] is None
        assert sequence["is_called"] is True
        assert sequence["last_value"] == 2
        assert witness_rows == 0
        # Exact pending preservation: the full pre-attempt rows,
        # including the supported public operation identities, are
        # unchanged by the rolled-back attempt (positive counts kept).
        assert len(media_pending) == 1
        assert len(composition_pending) == 1
        assert media_pending == media_before
        assert composition_pending == composition_before
        assert promoted_composition == 0
        # Phase-1 byte preparation ran before the transaction: the orphan
        # public object exists but no canonical row references or serves it.
        public_path = _public_path(media_root, digest)
        assert public_path.is_file()
        assert hashlib.sha256(public_path.read_bytes()).hexdigest() == digest

        # Actual public read of the orphan: the object exists on disk,
        # but with no canonical public row it must not be served.
        orphan_read = await _a6_public_read(database, media_root, digest)
        assert orphan_read.status_code == 404

        # Recovery: the trusted disposable failure is gone; the same
        # pending state promotes for real through the same single
        # reviewer transaction.
        await _age_heartbeat(database, job_id)
        job = await _claim_accept(database, "a6-accept-2")
        assert str(job["id"]) == str(job_id)
        assert job["attempt_count"] == 2
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "SUCCEEDED", result.error
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            media_row = await owner.fetchrow(
                "SELECT id, public_status, published_at, content_hash FROM"
                " content.media_asset_base WHERE id = $1",
                entry["media_id"],
            )
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            audit_rows = await owner.fetch("SELECT * FROM audit.promotion ORDER BY id")
            outbox_rows = await owner.fetch(
                "SELECT * FROM control.cache_outbox ORDER BY id"
            )
            workspace_row = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                entry["workspace_id"],
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
        assert media_row is not None
        assert str(media_row["public_status"]) == "public"
        assert media_row["published_at"] is not None
        assert media_row["content_hash"] == digest
        assert revision == 1
        assert len(audit_rows) == 1
        assert len(outbox_rows) == 1
        assert str(workspace_row["status"]) == "ACCEPTED"
        assert workspace_row["accepted_at"] is not None
        assert job_row["status"] == "SUCCEEDED"
        assert job_row["error"] is None
        # The recovered promotion really published: the same sessionless
        # public route now serves the exact stored bytes.
        recovered_read = await _a6_public_read(database, media_root, digest)
        assert recovered_read.status_code == 200
        assert recovered_read.content == _PENDING_PNG
    finally:
        await _a6_witness_stop(database)
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

        rows = await _enqueue_bound_accept(
            database, ids["workspace_id"], ids["delegator_id"]
        )
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
        rows = await _enqueue_bound_accept(
            database, ids["workspace_id"], ids["delegator_id"]
        )
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
        # Byte preparation (step 4) already ran before the commit, so the
        # public bytes exist (at most unreferenced public objects for
        # GC); the in-transaction publication mark (step 5) rolled back
        # with everything else, so the canonical row stays private.
        assert str(media_row["public_status"]) == "private"
        assert media_row["published_at"] is None
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
        rows = await _enqueue_bound_accept(
            database, ids["workspace_id"], ids["delegator_id"]
        )
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
    """R7.1: crash between byte preparation and the reviewer TX replays once.

    The fixture simulates the real crash window: the claimed worker marks
    the workspace PROMOTING, runs the step-4 byte preparation (public
    bytes exist; no database status mutation), and then dies before the
    step-5 reviewer transaction.  Stale-claim recovery re-queues the job;
    the replay must re-validate the frozen closure, run the in-transaction
    publication mark and commit exactly once.  The canonical row is still
    private while the crashed worker's effects are on disk only; the
    private -> public transition happens inside the replay's transaction.
    (Retained pre-077 persisted-mark replay is covered separately by
    ``test_accept_worker_crash_replay_legacy_persisted_mark``.)
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        await _freeze_workspace(database, ids, pool)
        rows = await _enqueue_bound_accept(
            database, ids["workspace_id"], ids["delegator_id"]
        )
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
        # Pre-transaction private: step 4 copied bytes only; the canonical
        # row cannot be public before the reviewer transaction.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            pre_tx = await owner.fetchrow(
                "SELECT public_status, published_at FROM"
                " content.media_asset_base WHERE id = $1",
                ids["media_id"],
            )
        assert str(pre_tx["public_status"]) == "private"
        assert pre_tx["published_at"] is None

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
async def test_accept_worker_crash_replay_legacy_persisted_mark(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """R3.10 retained legacy compatibility: a pre-077 persisted mark replays once.

    A worker interrupted between the pre-077 pre-transaction mark and the
    promotion transaction persisted a private -> public flip on the
    canonical base that the current in-transaction mark never creates.
    The legacy state is seeded here by trusted owner UPDATE as a fixture
    (reproducing exactly that historical row state; the seed itself is not
    a product mark); the replay itself runs the REAL worker/reviewer/COW
    path.  The re-materialized doc must be normalized back to the
    freeze-time private status before the digest comparison so the
    replay re-validates and commits exactly once.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        await _freeze_workspace(database, ids, pool)
        rows = await _enqueue_bound_accept(
            database, ids["workspace_id"], ids["delegator_id"]
        )
        job_id = UUID(str(rows[0]["job_id"]))
        digest = ids["media_digest"]

        job = await _claim_accept(database, "accept-legacy-1")
        assert str(job["id"]) == str(job_id)
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
        # Retained pre-077 state (trusted fixture seed): the interrupted
        # old worker's pre-transaction mark persisted before its crash.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "UPDATE content.media_asset_base SET public_status = 'public',"
                " published_at = now() WHERE id = $1",
                ids["media_id"],
            )
            legacy_row = await owner.fetchrow(
                "SELECT public_status, published_at FROM"
                " content.media_asset_base WHERE id = $1",
                ids["media_id"],
            )
        assert str(legacy_row["public_status"]) == "public"
        assert legacy_row["published_at"] is not None

        # The crash: no terminal, the heartbeat goes stale, recovery
        # re-queues, a second worker claims (attempt 2) and replays the
        # REAL promotion over the retained legacy state.
        await _age_heartbeat(database, job_id)
        job = await _claim_accept(database, "accept-legacy-2")
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
        # Single commit over the retained legacy state: the legacy flip
        # normalized, the in-transaction mark re-established the same
        # public row idempotently, one audit row, one outbox row.
        assert revision == 1
        assert str(workspace["status"]) == "ACCEPTED"
        assert workspace["accepted_at"] is not None
        assert job_row["status"] == "SUCCEEDED"
        assert job_row["error"] is None
        assert len(audit_rows) == 1
        assert len(outbox_rows) == 1
        assert json.loads(outbox_rows[0]["payload"])["media_manifest"] == manifest
        public_path = _public_path(media_root, digest)
        assert hashlib.sha256(public_path.read_bytes()).hexdigest() == digest
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
    # 083/2: discard_workspace retired (the DISCARD job is the only
    # discard path); get_conflicts stays for 084.
    assert not hasattr(promotion_module, "discard_workspace")
    assert "discard_workspace" not in vars(promotion_module)
    assert callable(promotion_module.get_conflicts)

    # Test inventory pin: the unit suite pins the removal.
    inventory = (
        Path(__file__).resolve().parent.parent / "unit" / "test_promotion.py"
    ).read_text(encoding="utf-8")
    assert 'not hasattr(promotion, "promote_workspace")' in inventory


@pytest.mark.asyncio
async def test_accept_worker_stored_digest_cotamper_refused(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """G13/E-D1: a co-tampered STORED snapshot digest is refused at
    ENQUEUE time (the immutable companion binding) BEFORE any ACCEPT
    job exists, with full no-effects.

    Co-tamper: the digest column becomes the TRUSTED recomputed digest
    of a coordinated altered document (a well-formed sha256 of a
    well-formed canonical document), while the stored payload is left
    untouched; the target is proven by independent digest
    recomputation.  Owner tampering is a test threat fixture only.

    083/12: the companion froze the ORIGINAL digest at freeze time, so
    an approval naming the tampered stored digest cannot satisfy both
    the stored-row and the immutable-companion gates: the enqueue
    raises REVIEW_MANIFEST_NOT_FOUND (the uniform 404 class), no job
    is created, and the worker never runs.  The untampered twin
    digest then accepts the SAME snapshot through the same qualified
    path (the worker-level stored-payload digest guard remains as
    defense in depth; the enqueue gate is the one reached here).

    The negative proves full no-effects including the canonical
    promotion facts (heading props, created-node absence, pending COW
    operations), hashed private bytes, and an ACTUAL finalizer call
    count of 0 via a counting wrapper that delegates to the REAL
    MediaBoundary (the positive then calls it exactly once).
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    counting = _CountingMediaBoundary(boundary)
    try:
        snapshot_id = await _freeze_workspace(database, ids, pool)
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            stored = await owner.fetchrow(
                "SELECT r.digest, r.payload, r.normalized_state,"
                " r.versions, row_to_json(r)::text AS rowbytes"
                " FROM control.review_snapshot r WHERE r.id = $1",
                snapshot_id,
            )
            original_digest = str(stored["digest"])
            stored_versions = json.loads(stored["versions"])
            # Independent recomputation: the pre-tamper row is
            # internally consistent (stored digest == trusted canonical
            # digest of the stored payload).
            recomputed = await owner.fetchval(
                "SELECT encode(sha256(convert_to("
                " control.slaif_canonical_jsonb_text($1::jsonb),'UTF8')),"
                " 'hex')",
                stored["payload"],
            )
            assert recomputed == original_digest
            # Prior identity/revision bindings valid: the DIGEST guard,
            # not an earlier binding refusal, is the one reached.
            normalized = json.loads(stored["normalized_state"])
            base_revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            assert int(normalized["base_site_revision"]) == int(base_revision)
            assert stored_versions == {
                "catalog": "catalog-v1",
                "composition_schema": "site-composition/v1",
                "content_model": "content-model/v1",
                "design_system": "design-system/v1",
                "puck": "0.20.2",
                "renderer": "renderer-v1",
            }
            # Co-tamper: a well-formed sha256 of a well-formed altered
            # canonical document, not a corrupted field.
            altered = json.loads(stored["payload"])
            altered["site"]["display_name"] = "Co-Tampered"
            tampered_digest = await owner.fetchval(
                "SELECT encode(sha256(convert_to("
                " control.slaif_canonical_jsonb_text($1::jsonb),'UTF8')),"
                " 'hex')",
                json.dumps(altered),
            )
            assert len(tampered_digest) == 64
            assert set(tampered_digest) <= set("0123456789abcdef")
            assert tampered_digest != original_digest
            await owner.execute(
                "UPDATE control.review_snapshot SET digest = $1 WHERE id = $2",
                tampered_digest,
                snapshot_id,
            )
            # The stored payload is untouched: its trusted digest still
            # recomputes to the ORIGINAL digest, so the digest column is
            # the single inconsistent field.
            still = await owner.fetchval(
                "SELECT encode(sha256(convert_to("
                " control.slaif_canonical_jsonb_text(payload),'UTF8')),"
                " 'hex') FROM control.review_snapshot WHERE id = $1",
                snapshot_id,
            )
            assert still == original_digest != tampered_digest
            pre_rowbytes = await owner.fetchval(
                "SELECT row_to_json(r)::text FROM control.review_snapshot r"
                " WHERE r.id = $1",
                snapshot_id,
            )
            # Canonical promotion facts BEFORE the refused run: the
            # canonical heading still holds its original (pre-promotion)
            # props, the COW-created node is absent from canonical, and
            # the two qualified COW operations are still pending.
            pre_heading_props = await owner.fetchval(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
            assert json.loads(pre_heading_props) == {
                "level": 1,
                "text": "Accept",
            }
            pre_created_row = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["created_heading_id"],
            )
            assert pre_created_row is None
            pre_pending_ops = sorted(
                row[0]
                for row in await owner.fetch(
                    "SELECT row_to_json(r)::text"
                    " FROM content.page_composition_changes r"
                    " WHERE r.session_id = $1"
                    " ORDER BY r.operation_id::text, r._cow_order",
                    ids["workspace_id"],
                )
            )
            assert len(pre_pending_ops) == 2

        pre_private_sha = hashlib.sha256(
            _private_path(media_root, ids["media_digest"]).read_bytes()
        ).hexdigest()
        assert pre_private_sha == ids["media_digest"]

        # 083/12: the co-tamper is caught at ENQUEUE, not in the
        # worker.  The companion froze the ORIGINAL digest at freeze
        # time, so an approval naming the tampered stored digest (with
        # the real manifest digest, the only one a genuine approval
        # could carry) cannot satisfy both the stored-row and the
        # immutable-companion gates: a typed refusal, no job.
        binding_manifest = await _read_manifest(database, snapshot_id)
        assert binding_manifest is not None
        assert str(binding_manifest["snapshot_digest"]) == original_digest
        binding_manifest_digest = str(binding_manifest["manifest_digest"])
        with pytest.raises(asyncpg.PostgresError) as cotamper_refusal:
            await _enqueue_accept(
                database,
                ids["workspace_id"],
                ids["delegator_id"],
                snapshot_id=snapshot_id,
                snapshot_digest=tampered_digest,
                manifest_digest=binding_manifest_digest,
            )
        assert cotamper_refusal.value.sqlstate == "P0002"
        assert "REVIEW_MANIFEST_NOT_FOUND" in str(cotamper_refusal.value)

        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            after_rowbytes = await owner.fetchval(
                "SELECT row_to_json(r)::text FROM control.review_snapshot r"
                " WHERE r.id = $1",
                snapshot_id,
            )
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
            workspace = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                ids["workspace_id"],
            )
            accept_job_count = await owner.fetchval(
                "SELECT count(*) FROM control.review_job"
                " WHERE workspace_id = $1 AND job_kind = 'ACCEPT'",
                ids["workspace_id"],
            )
            audit_count = await owner.fetchval("SELECT count(*) FROM audit.promotion")
            outbox_count = await owner.fetchval(
                "SELECT count(*) FROM control.cache_outbox"
            )
            media_row = await owner.fetchrow(
                "SELECT public_status, published_at, content_hash"
                " FROM content.media_asset_base WHERE id = $1",
                ids["media_id"],
            )
            heading_props_after = await owner.fetchval(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
            created_row_after = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["created_heading_id"],
            )
            pending_ops_after = sorted(
                row[0]
                for row in await owner.fetch(
                    "SELECT row_to_json(r)::text"
                    " FROM content.page_composition_changes r"
                    " WHERE r.session_id = $1"
                    " ORDER BY r.operation_id::text, r._cow_order",
                    ids["workspace_id"],
                )
            )
        # Full actual no-effects: the refusal hit the companion
        # binding at ENQUEUE, before any ACCEPT job existed; nothing
        # ran and nothing moved.  The co-tamper stands untouched (no
        # path repaired or consumed it), and the media never flipped
        # (no finalizer call: status, published_at, digest and private
        # bytes all stand, and no public artifact exists).
        assert after_rowbytes == pre_rowbytes
        assert revision == base_revision
        assert str(workspace["status"]) == "REVIEW"
        assert workspace["accepted_at"] is None
        assert accept_job_count == 0
        assert audit_count == 0
        assert outbox_count == 0
        assert json.loads(heading_props_after) == json.loads(pre_heading_props)
        assert created_row_after is None
        assert pending_ops_after == pre_pending_ops
        private_sha_after = hashlib.sha256(
            _private_path(media_root, ids["media_digest"]).read_bytes()
        ).hexdigest()
        assert private_sha_after == pre_private_sha == ids["media_digest"]
        assert str(media_row["public_status"]) == "private"
        assert media_row["published_at"] is None
        assert media_row["content_hash"] == ids["media_digest"]
        assert not _public_path(media_root, ids["media_digest"]).exists()
        assert _private_path(media_root, ids["media_digest"]).is_file()
        # ACTUAL finalizer call count: the real MediaBoundary.finalize
        # (accept_job.py L599) was never called by the refused run.
        assert counting.finalize_calls == 0

        # Positive control: restoring the exact original digest makes
        # the SAME snapshot accept through the SAME qualified path.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "UPDATE control.review_snapshot SET digest = $1 WHERE id = $2",
                original_digest,
                snapshot_id,
            )
        rows = await _enqueue_bound_accept(
            database, ids["workspace_id"], ids["delegator_id"]
        )
        job_id = UUID(str(rows[0]["job_id"]))
        job = await _claim_accept(database, "accept-cotamper-2")
        assert str(job["id"]) == str(job_id)
        result = await run_accept_job(pool, settings, job, media=counting)
        assert result.status == "SUCCEEDED", result.error
        # The untampered digest runs the real finalizer exactly once.
        assert counting.finalize_calls == 1

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
                "SELECT public_status, published_at"
                " FROM content.media_asset_base WHERE id = $1",
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
        assert len(audit_rows) == 1
        audit = audit_rows[0]
        assert str(audit["site_id"]) == str(ids["site_id"])
        assert str(audit["workspace_id"]) == str(ids["workspace_id"])
        assert str(audit["snapshot_id"]) == str(snapshot_id)
        assert str(audit["job_id"]) == str(job_id)
        assert str(audit["digest"]) == original_digest
        assert audit["base_site_revision"] == base_revision
        assert audit["new_canonical_revision"] == base_revision + 1
        assert audit["committed_operations"] == 2
        assert json.loads(audit["versions"]) == stored_versions
        assert str(audit["actor_user_account_id"]) == str(ids["delegator_id"])
        # 083/12 R5: the receipt names the exact approved binding.
        assert str(audit["manifest_id"]) == str(binding_manifest["manifest_id"])
        assert str(audit["manifest_digest"]) == binding_manifest_digest
        assert [
            str(operation) for operation in audit["applied_operation_ids"]
        ] == sorted(str(operation) for operation in binding_manifest["operation_ids"])
        assert len(outbox_rows) == 1
        outbox = outbox_rows[0]
        assert str(outbox["site_id"]) == str(ids["site_id"])
        assert str(outbox["workspace_id"]) == str(ids["workspace_id"])
        assert outbox["event_kind"] == "WORKSPACE_ACCEPTED"
        assert json.loads(outbox["payload"]) == {
            "snapshot_id": str(snapshot_id),
            "digest": original_digest,
            "base_site_revision": base_revision,
            "new_canonical_revision": base_revision + 1,
            "media_manifest": manifest,
        }
        assert json.loads(heading_props) == {
            "level": 2,
            "text": "Promoted heading",
        }
        assert created_row is not None
        assert json.loads(created_row["props"]) == {
            "level": 3,
            "text": "New promoted node",
        }
        assert str(media_row["public_status"]) == "public"
        assert media_row["published_at"] is not None
        public_path = _public_path(media_root, digest)
        assert public_path.is_file()
        assert hashlib.sha256(public_path.read_bytes()).hexdigest() == digest
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_accept_worker_human_page_edit_mixed_composite_fk(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """A real human Editor page title edit carries the mixed UUID/TEXT
    composite FK content.page (site_id, locale) -> content.site_locale
    (site_id, tag).

    While the edit is still PENDING, the public reviewer context the
    accept worker uses (asyncpg_cow_reviewer -> operations/dependencies)
    returns the normal pending graph: exactly the one pending operation
    recorded for the human mutation, and no dependencies.  The
    0.2.0 dependency getter failed at EXECUTE with SQLSTATE 42883 on
    that same pending mixed-composite-FK page (retained narrower
    getter probe, not rerun).  The canonical title is still the
    original while the edit is pending; the real freeze/accept worker
    then promotes the canonical title with the exact revision,
    promotion audit and outbox facts, and the accepted title is
    visible through the human Editor HTTP read path.
    """
    database = agent_site_database
    media_root = tmp_path / "media"
    owner_pool = await database.role_pool("slaif_owner")
    site_id = uuid4()
    human_id = uuid4()
    page_id = uuid4()
    site_key = f"human-fk-accept-{uuid4().hex[:12]}"
    fixed_logins = (
        (CONTROL_LOGIN, CONTROL_PASSWORD, CONTROL_ROLE),
        (EDITOR_LOGIN, EDITOR_PASSWORD, EDITOR_ROLE),
    )
    pool: asyncpg.Pool[Any] | None = None
    boundary: MediaBoundary | None = None
    created_logins: list[str] = []
    try:
        await upgrade(database.settings)
        async with owner_pool.acquire() as owner:
            await owner.execute(
                "INSERT INTO control.user_account "
                "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
                "VALUES ($1, 'OIDC', 'https://human-fk-accept.test', $2, "
                "'Human FK Accept Human')",
                human_id,
                str(human_id),
            )
            await owner.execute(
                "INSERT INTO control.platform_administrator (user_account_id) "
                "VALUES ($1)",
                human_id,
            )
            await owner.execute(
                "INSERT INTO control.site "
                "(id, site_key, display_name, default_locale, "
                "component_catalog_version) VALUES ($1, $2, 'Human FK Accept', "
                "'en', 'catalog-v1')",
                site_id,
                site_key,
            )
            await owner.execute(
                "INSERT INTO content.page "
                "(id, site_id, slug, title, status, locale) "
                "VALUES ($1, $2, 'canonical', 'Canonical title', 'DRAFT', 'en')",
                page_id,
                site_id,
            )
        await reconcile(database.settings)

        for login, password, role in fixed_logins:
            password_literal = await database.administrator.fetchval(
                "SELECT pg_catalog.quote_literal($1::text)", password
            )
            await database.administrator.execute(
                f"CREATE ROLE {quote_identifier(login)} LOGIN PASSWORD "
                f"{password_literal} "
                "NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT "
                "NOREPLICATION NOBYPASSRLS"
            )
            created_logins.append(login)
            await database.administrator.execute(
                f"GRANT {quote_identifier(role)} TO {quote_identifier(login)}"
            )

        settings = _worker_settings(database)
        control = ControlDatabase(_control_settings(database))
        editor = EditorDatabase(_editor_settings(database))
        app = create_editor_app(
            settings=ServiceSettings(mode=EnvironmentMode.TEST),
            database=control,
            editor_database=editor,
        )
        async with app.router.lifespan_context(app):
            issued = await control.human_session_service().create(human_id)
            session = issued.token.get_secret_value()
            csrf = issued.csrf_token.get_secret_value()
            pages_path = f"/api/editor/v1/sites/{site_id}/pages/"
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://public-editor.test",
            ) as client:
                update = await client.patch(
                    f"{pages_path}{page_id}",
                    headers=_mutation_headers(session, csrf, "human-page-fk-title"),
                    json={
                        "title": "Human FK regression title",
                        "expected_row_version": 1,
                    },
                )
                assert update.status_code == 200
                _assert_private(update)
                assert update.json()["title"] == "Human FK regression title"

            async with owner_pool.acquire() as owner:
                workspace_row = await owner.fetchrow(
                    "SELECT id, delegator_id, created_by FROM control.workspace "
                    "WHERE site_id = $1",
                    site_id,
                )
                base_revision = await owner.fetchval(
                    "SELECT canonical_revision FROM control.site WHERE id = $1",
                    site_id,
                )
                mutation_rows = await owner.fetch(
                    "SELECT * FROM audit.human_editor_mutation "
                    "WHERE site_id = $1 ORDER BY occurred_at",
                    site_id,
                )
                canonical_title = await owner.fetchval(
                    "SELECT title FROM content.page_base WHERE id = $1",
                    page_id,
                )
            assert workspace_row is not None
            workspace_id = UUID(str(workspace_row["id"]))
            # A HUMAN editor workspace has no delegator: the creator is
            # the actor the freeze/accept functions authorize.
            creator_id = UUID(str(workspace_row["created_by"]))
            assert workspace_row["delegator_id"] is None
            assert str(creator_id) == str(human_id)
            assert base_revision == 0
            # COW isolation: the pending edit does not touch canonical.
            assert canonical_title == "Canonical title"
            # The Editor boundary recorded exactly the successful PATCH.
            assert len(mutation_rows) == 1
            mutation = mutation_rows[0]
            operation_id = UUID(str(mutation["operation_id"]))
            assert str(mutation["human_user_id"]) == str(human_id)
            assert str(mutation["workspace_id"]) == str(workspace_id)
            assert str(mutation["site_id"]) == str(site_id)
            assert mutation["action"] == (f"PATCH {pages_path}{page_id}")
            assert mutation["resource_type"] == "editor.sites"
            assert str(mutation["resource_id"]) == str(page_id)
            assert re.fullmatch(r"[0-9a-f]{64}", mutation["request_digest"])
            assert mutation["response_status"] == 200
            assert mutation["occurred_at"] is not None

            ids = {
                "workspace_id": workspace_id,
                "site_id": site_id,
                "delegator_id": creator_id,
            }

            pool = await _worker_pool(database)
            boundary = MediaBoundary(settings=_media_settings(database, media_root))
            try:
                # The public reviewer context the accept worker uses,
                # exercised while the mixed-composite-FK page edit is
                # still PENDING.
                async with pool.acquire() as connection:
                    async with asyncpg_cow_reviewer(connection) as reviewer:
                        operations = await reviewer.operations(
                            workspace_id, schema="content"
                        )
                        dependencies = await reviewer.dependencies(
                            workspace_id, schema="content"
                        )
                assert operations == [operation_id]
                assert dependencies == []

                snapshot_id = await _freeze_workspace(database, ids, pool)
                async with owner_pool.acquire() as owner:
                    stored_digest = await owner.fetchval(
                        "SELECT digest::text FROM control.review_snapshot "
                        "WHERE id = $1",
                        snapshot_id,
                    )
                assert stored_digest is not None

                rows = await _enqueue_bound_accept(database, workspace_id, creator_id)
                job_id = UUID(str(rows[0]["job_id"]))
                job = await _claim_accept(database, "accept-human-page-fk-1")
                assert str(job["id"]) == str(job_id)
                result = await run_accept_job(pool, settings, job, media=boundary)
                assert result.status == "SUCCEEDED", result.error

                async with owner_pool.acquire() as owner:
                    revision = await owner.fetchval(
                        "SELECT canonical_revision FROM control.site WHERE id = $1",
                        site_id,
                    )
                    workspace = await owner.fetchrow(
                        "SELECT status, accepted_at FROM control.workspace "
                        "WHERE id = $1",
                        workspace_id,
                    )
                    job_row = await owner.fetchrow(
                        "SELECT status, error FROM control.review_job WHERE id = $1",
                        job_id,
                    )
                    audit_rows = await owner.fetch(
                        "SELECT * FROM audit.promotion ORDER BY id"
                    )
                    outbox_rows = await owner.fetch(
                        "SELECT * FROM control.cache_outbox ORDER BY id"
                    )
                    promoted_title = await owner.fetchval(
                        "SELECT title FROM content.page_base WHERE id = $1",
                        page_id,
                    )

                assert revision == base_revision + 1
                assert str(workspace["status"]) == "ACCEPTED"
                assert workspace["accepted_at"] is not None
                assert job_row["status"] == "SUCCEEDED"
                assert job_row["error"] is None
                assert promoted_title == "Human FK regression title"

                # Exactly one promotion audit row with the exact fields.
                assert len(audit_rows) == 1
                audit = audit_rows[0]
                assert str(audit["site_id"]) == str(site_id)
                assert str(audit["workspace_id"]) == str(workspace_id)
                assert str(audit["snapshot_id"]) == str(snapshot_id)
                assert str(audit["job_id"]) == str(job_id)
                assert str(audit["digest"]) == stored_digest
                assert audit["base_site_revision"] == base_revision
                assert audit["new_canonical_revision"] == base_revision + 1
                assert audit["committed_operations"] == 1
                assert str(audit["actor_user_account_id"]) == str(human_id)
                assert audit["created_at"] is not None

                # Exactly one unconsumed outbox row; no media was touched.
                assert len(outbox_rows) == 1
                outbox = outbox_rows[0]
                assert str(outbox["site_id"]) == str(site_id)
                assert str(outbox["workspace_id"]) == str(workspace_id)
                assert outbox["event_kind"] == "WORKSPACE_ACCEPTED"
                assert json.loads(outbox["payload"]) == {
                    "snapshot_id": str(snapshot_id),
                    "digest": stored_digest,
                    "base_site_revision": base_revision,
                    "new_canonical_revision": base_revision + 1,
                    "media_manifest": [],
                }

                # The canonical read through the human Editor HTTP path
                # shows the accepted title.
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app),
                    base_url="http://public-editor.test",
                ) as client:
                    read = await client.get(
                        f"{pages_path}{page_id}",
                        headers={"cookie": _cookie(session, csrf)},
                    )
                    assert read.status_code == 200
                    _assert_private(read)
                    assert read.json()["title"] == "Human FK regression title"
            finally:
                if boundary is not None:
                    await boundary.stop()
                if pool is not None:
                    await pool.close()
    finally:
        await owner_pool.close()
        for login, _, role in fixed_logins:
            if login not in created_logins:
                continue
            await database.administrator.execute(
                f"REVOKE {quote_identifier(role)} FROM {quote_identifier(login)}"
            )
            await database.administrator.execute(
                f"DROP ROLE IF EXISTS {quote_identifier(login)}"
            )
