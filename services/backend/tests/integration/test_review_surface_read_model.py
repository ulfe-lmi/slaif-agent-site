"""Real PostgreSQL proof for the trusted read-only review document (082/2 R1)."""

from __future__ import annotations

import json
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

_SITE_KEY = "review-int"
_OTHER_SITE_KEY = "review-int-other"

# The 16 COW change tables, exactly as the read model's fixed family order.
_CHANGE_TABLES = (
    "page_changes",
    "page_composition_changes",
    "content_item_changes",
    "field_definition_changes",
    "content_type_changes",
    "content_item_translation_changes",
    "item_relation_changes",
    "collection_view_changes",
    "theme_changes",
    "navigation_changes",
    "navigation_item_changes",
    "redirect_changes",
    "media_asset_changes",
    "site_global_region_changes",
    "site_locale_changes",
    "proposed_side_effect_changes",
)

_FAMILY_KEYS = (
    "pages",
    "composition_nodes",
    "items",
    "fields",
    "content_types",
    "translations",
    "relations",
    "collection_views",
    "theme",
    "navigation",
    "navigation_items",
    "redirects",
    "media_assets",
    "global_regions",
    "locales",
    "proposed_side_effects",
)


def _walk_nodes(nodes: Any) -> list[dict[str, Any]]:
    """Flatten the snapshot's nested node tree (roots + descendants)."""

    flat: list[dict[str, Any]] = []
    for node in nodes:
        flat.append(node)
        flat.extend(_walk_nodes(node.get("children") or []))
    return flat


def _node_types(nodes: Any) -> list[str]:
    """Recursive walk of the snapshot's nested node tree (root lists)."""

    return [node["component_type"] for node in _walk_nodes(nodes)]


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


async def _control_call(
    database: AgentSiteDatabase, sql: str, *arguments: Any
) -> list[Any]:
    login, password = database.credentials["slaif_control"]
    connection = await asyncpg.connect(dsn=_dsn(database, login, password))
    try:
        return list(await connection.fetch(sql, *arguments))
    finally:
        await connection.close()


async def _read_model(
    database: AgentSiteDatabase,
    workspace_id: UUID,
    site_id: UUID,
    user_account_id: UUID,
) -> dict[str, Any]:
    rows = await _control_call(
        database,
        "SELECT * FROM control.slaif_review_read_model($1,$2,$3)",
        workspace_id,
        site_id,
        user_account_id,
    )
    assert len(rows) == 1
    document: Any = rows[0][0]
    if isinstance(document, (str, bytes)):
        parsed: Any = json.loads(document)
        assert isinstance(parsed, dict)
        return parsed
    assert isinstance(document, dict)
    result: dict[str, Any] = dict(document)
    return result


async def _seed(database: AgentSiteDatabase) -> dict[str, UUID]:
    """Upgrade to 074_001 and seed one site with renderable COW content."""

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
                gen_random_uuid(), 'LOCAL', 'Review.Integration.Delegator',
                'review.integration.delegator', $1, 'Review Delegator', 'ACTIVE'
            ) RETURNING id
            """,
            _AGGON2,
        )
        nonmember_id = await owner.fetchval(
            """
            INSERT INTO control.user_account (
                id, identity_kind, local_username, local_username_normalized,
                password_hash, display_name, status
            ) VALUES (
                gen_random_uuid(), 'LOCAL', 'Review.Integration.Nonmember',
                'review.integration.nonmember', $1, 'Review Nonmember', 'ACTIVE'
            ) RETURNING id
            """,
            _AGGON2,
        )
        admin_id = await owner.fetchval(
            """
            INSERT INTO control.user_account (
                id, identity_kind, local_username, local_username_normalized,
                password_hash, display_name, status
            ) VALUES (
                gen_random_uuid(), 'LOCAL', 'Review.Integration.Admin',
                'review.integration.admin', $1, 'Review Admin', 'ACTIVE'
            ) RETURNING id
            """,
            _AGGON2,
        )
        site_id = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name, default_locale,"
            " component_catalog_version) VALUES ($1, 'Review Int', 'en-US',"
            " 'catalog-v1') RETURNING id",
            _SITE_KEY,
        )
        await owner.execute(
            "INSERT INTO control.site_membership (site_id,user_account_id,"
            " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
            site_id,
            delegator_id,
        )
        # The delegator also owns a second site (exact site-binding probe).
        other_site_id = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name, default_locale,"
            " component_catalog_version) VALUES ($1, 'Review Int Other', 'en-US',"
            " 'catalog-v1') RETURNING id",
            _OTHER_SITE_KEY,
        )
        await owner.execute(
            "INSERT INTO control.site_membership (site_id,user_account_id,"
            " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
            other_site_id,
            delegator_id,
        )
        await owner.execute(
            "INSERT INTO control.platform_administrator (user_account_id) VALUES ($1)",
            admin_id,
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
            '  \'{"level":1,"text":"Review"}\'::jsonb),'
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
            " VALUES ($1,$2,$2,'Review Workspace','L4',"
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
        # A fresh ACTIVE workspace on the same site with no snapshot.
        fresh_workspace_id = await owner.fetchval(
            "INSERT INTO control.workspace (site_id, created_by, delegator_id,"
            " title, delegation_preset, effective_scopes, status, expires_at)"
            " VALUES ($1,$2,$2,'Fresh Workspace','L4',"
            " '[\"page:read\"]'::jsonb,'ACTIVE',now()+interval '1 hour')"
            " RETURNING id",
            site_id,
            delegator_id,
        )
    return {
        "delegator_id": UUID(str(delegator_id)),
        "nonmember_id": UUID(str(nonmember_id)),
        "admin_id": UUID(str(admin_id)),
        "site_id": UUID(str(site_id)),
        "other_site_id": UUID(str(other_site_id)),
        "workspace_id": UUID(str(workspace_id)),
        "fresh_workspace_id": UUID(str(fresh_workspace_id)),
        "page_id": page_id,
        "section_id": section_id,
    }


async def _inject_change_rows(
    database: AgentSiteDatabase,
    seeded: dict[str, UUID],
    boundary: Any = None,
    node_id: UUID | None = None,
) -> tuple[UUID, UUID]:
    """Owner-injected frozen-session COW change rows (the dedicated fixture).

    One composition-node upsert (a new Footer node) and one page upsert
    (the Home title). ``boundary`` overrides ``_cow_updated_at`` (the
    watermark-exclusion fixture uses the post-freeze boundary).
    """
    workspace_id = seeded["workspace_id"]
    site_id = seeded["site_id"]
    operation_node = uuid4()
    operation_page = uuid4()
    node = node_id or uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO content.page_composition_changes"
            " (session_id, operation_id, id, site_id, page_id, component_type,"
            "  schema_version, parent_id, slot_key, order_key, props,"
            "  _cow_deleted, _cow_updated_at, _cow_base_exists, _cow_base_row,"
            "  _cow_base_schema)"
            " VALUES ($1,$2,$3,$4,$5,'Footer','1',$6,'default',2,'{}'::jsonb,"
            "  false, coalesce($7::timestamptz, now()), false, NULL,"
            "  '{}'::jsonb)",
            workspace_id,
            operation_node,
            node,
            site_id,
            seeded["page_id"],
            seeded["section_id"],
            boundary,
        )
        await owner.execute(
            "INSERT INTO content.page_changes"
            " (session_id, operation_id, id, site_id, slug, title, status,"
            "  locale, _cow_deleted, _cow_updated_at, _cow_base_exists,"
            "  _cow_base_row, _cow_base_schema)"
            " SELECT $1,$2,t.id,t.site_id,t.slug,$3,t.status,t.locale,"
            "  false, coalesce($4::timestamptz, now()), true,"
            "  row_to_json(t)::jsonb, '{}'::jsonb"
            " FROM content.page_base AS t WHERE t.id = $5",
            workspace_id,
            operation_page,
            "Home v2",
            boundary,
            seeded["page_id"],
        )
    return operation_node, operation_page


async def _freeze_complete(
    database: AgentSiteDatabase, seeded: dict[str, UUID]
) -> None:
    rows = await _control_call(
        database,
        "SELECT * FROM control.slaif_human_agent_workspace_freeze($1,$2,$3)",
        seeded["workspace_id"],
        seeded["site_id"],
        seeded["delegator_id"],
    )
    assert len(rows) == 1
    assert str(rows[0]["status"]) == "FREEZING"
    login, password = database.credentials["slaif_review_worker"]
    pool = await asyncpg.create_pool(
        dsn=_dsn(database, login, password), min_size=1, max_size=2
    )
    try:
        claimed = await pool.fetch(
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "review-int-worker",
            ["FREEZE", "ACCEPT"],
        )
        assert len(claimed) == 1
        result = await run_freeze_job(
            pool, _worker_settings(database), dict(claimed[0])
        )
        assert result.status == "SUCCEEDED", result.error
    finally:
        await pool.close()


async def _row_counts(database: AgentSiteDatabase) -> dict[str, int]:
    rows: dict[str, int] = {}
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        for table in _CHANGE_TABLES:
            rows[table] = int(
                await owner.fetchval(
                    f"SELECT count(*) FROM content.{table}"  # noqa: S608
                )
            )
        rows["review_snapshot"] = int(
            await owner.fetchval("SELECT count(*) FROM control.review_snapshot")
        )
        rows["review_job"] = int(
            await owner.fetchval("SELECT count(*) FROM control.review_job")
        )
        rows["capability"] = int(
            await owner.fetchval("SELECT count(*) FROM control.capability")
        )
        rows["page_base"] = int(
            await owner.fetchval("SELECT count(*) FROM content.page_base")
        )
        rows["page_composition_base"] = int(
            await owner.fetchval("SELECT count(*) FROM content.page_composition_base")
        )
        rows["site_canonical_revision"] = int(
            await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE site_key = $1",
                _SITE_KEY,
            )
        )
    return rows


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
        application_name="slaif-review-read-test",
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


async def _session_cookie(adapter: Any, user_account_id: UUID) -> str:
    issued = await adapter.human_session_service().create(user_account_id)
    return f"slaif_session={issued.token.get_secret_value()}"


def _review_path(site_id: UUID, workspace_id: str | UUID) -> str:
    return f"/api/control/v1/sites/{site_id}/workspaces/{workspace_id}/review/"


@pytest.mark.asyncio
async def test_read_model_document_shape_and_frozen_content(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    seeded = await _seed(database)
    operation_node, operation_page = await _inject_change_rows(database, seeded)
    await _freeze_complete(database, seeded)

    before = await _row_counts(database)
    first = await _read_model(
        database, seeded["workspace_id"], seeded["site_id"], seeded["delegator_id"]
    )
    second = await _read_model(
        database, seeded["workspace_id"], seeded["site_id"], seeded["delegator_id"]
    )
    after = await _row_counts(database)

    # Deterministic: byte-for-byte identical documents.
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)

    # Exact top-level document shape (the R1 contract).
    assert set(first) == {
        "snapshot",
        "drift",
        "timeline",
        "resource_diff",
        "summaries",
        "validation",
        "evidence",
        "metadata",
        "normalized_state",
    }
    assert set(first["snapshot"]) == {
        "id",
        "digest",
        "state_version",
        "revision_watermark",
        "base_site_revision",
        "status",
        "created_at",
        "created_by",
        "versions",
    }
    assert first["snapshot"]["status"] == "COMPLETE"
    assert set(first["drift"]) == {
        "current_site_revision",
        "base_site_revision",
        "equal",
    }
    assert first["drift"]["equal"] is True
    assert (
        first["drift"]["current_site_revision"] == first["drift"]["base_site_revision"]
    )
    assert set(first["resource_diff"]) == set(_FAMILY_KEYS)
    assert set(first["summaries"]) == {
        "model",
        "fields",
        "mappings",
        "items",
        "resource_inventory",
        "composition_by_component_type",
        "theme",
        "navigation",
        "redirects",
        "media",
        "responsive",
    }
    assert set(first["validation"]) == {"report", "warnings"}
    assert set(first["evidence"]) == {"runs", "artifacts"}
    assert set(first["metadata"]) == {
        "workspace",
        "site",
        "capabilities",
        "quota_policy",
        "agent_session_browser",
    }
    state = first["normalized_state"]
    assert set(state) == {
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
    }
    assert set(state["site"]) == {
        "site_key",
        "display_name",
        "default_locale",
        "component_catalog_version",
    }
    assert state["site"]["site_key"] == _SITE_KEY
    assert first["metadata"]["workspace"]["status"] == "REVIEW"
    assert first["metadata"]["workspace"]["id"] == str(seeded["workspace_id"])

    # The frozen state merged the pre-freeze COW session: the Home title
    # change and the new Footer node are part of the immutable snapshot.
    pages = {page["slug"]: page for page in state["pages"]}
    assert pages["home"]["title"] == "Home v2"
    node_components = _node_types(pages["home"]["nodes"])
    assert node_components.count("Footer") == 1
    assert node_components.count("Heading") == 1
    assert node_components.count("Image") == 1

    # Semantic timeline: exactly the two pre-freeze operations, ordered.
    timeline = first["timeline"]
    assert [entry["operation_id"] for entry in timeline] == [
        str(operation_node),
        str(operation_page),
    ]
    by_operation = {entry["operation_id"]: entry for entry in timeline}
    node_entry = by_operation[str(operation_node)]
    assert node_entry["operation_type"] == "composition_nodes:upsert"
    assert node_entry["resource"] == ["composition_nodes"]
    page_entry = by_operation[str(operation_page)]
    assert page_entry["operation_type"] == "pages:upsert"
    assert page_entry["resource"] == ["pages"]
    assert "created_at" in node_entry and "created_at" in page_entry

    # Bounded resource diff: the added node and the one-level field diff.
    diff = first["resource_diff"]
    added_nodes = diff["composition_nodes"]["added"]
    assert len(added_nodes) == 1
    assert added_nodes[0]["component_type"] == "Footer"
    assert diff["composition_nodes"]["modified"] == []
    assert diff["composition_nodes"]["deleted"] == []
    modified_pages = diff["pages"]["modified"]
    assert len(modified_pages) == 1
    assert modified_pages[0]["id"] == str(seeded["page_id"])
    assert modified_pages[0]["fields"]["title"] == {
        "before": "Home",
        "after": "Home v2",
    }
    assert diff["pages"]["added"] == []
    assert diff["pages"]["deleted"] == []
    # Every other family is empty for this seed.
    for family in _FAMILY_KEYS:
        if family in ("composition_nodes", "pages"):
            continue
        assert diff[family] == {"added": [], "modified": [], "deleted": []}

    # Side-effect-free: the read model is SELECT-only and STABLE.
    assert before == after
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        volatility = await owner.fetchval(
            "SELECT p.provolatile::text FROM pg_proc AS p"
            " WHERE p.oid = to_regprocedure("
            " 'control.slaif_review_read_model(uuid, uuid, uuid)')"
        )
    assert volatility == "s"

    # EXECUTE grant matrix: exactly one allowed caller per function.
    for role in _LONG_LIVED_ROLES:
        allowed = role == "slaif_control"
        rows = await _control_call(
            database,
            "SELECT has_function_privilege($1,"
            " 'control.slaif_review_read_model(uuid,uuid,uuid)', 'EXECUTE')",
            role,
        )
        assert rows[0][0] is allowed, role
    for role in _LONG_LIVED_ROLES:
        allowed = role == "slaif_agent_runtime"
        for function in (
            "control.slaif_human_session_review_artifact_list(text,bytea,uuid)",
            "control.slaif_human_session_review_artifact_retrieve"
            "(text,bytea,uuid,uuid)",
        ):
            rows = await _control_call(
                database,
                f"SELECT has_function_privilege($1, '{function}', 'EXECUTE')",
                role,
            )
            assert rows[0][0] is allowed, (role, function)


@pytest.mark.asyncio
async def test_read_model_watermark_excludes_post_freeze_rows(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    seeded = await _seed(database)
    operation_node, operation_page = await _inject_change_rows(database, seeded)
    await _freeze_complete(database, seeded)

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        boundary = await owner.fetchval(
            "SELECT created_at FROM control.review_snapshot"
            " WHERE workspace_id = $1 AND status = 'COMPLETE'",
            seeded["workspace_id"],
        )
    late_node = uuid4()
    late_operation, _ = await _inject_change_rows(
        database,
        seeded,
        boundary=boundary + timedelta(seconds=1),
        node_id=late_node,
    )

    document = await _read_model(
        database, seeded["workspace_id"], seeded["site_id"], seeded["delegator_id"]
    )

    # The watermark-boundary operation is excluded from the timeline...
    timeline_ids = [entry["operation_id"] for entry in document["timeline"]]
    assert timeline_ids == [str(operation_node), str(operation_page)]
    # ...and from the bounded resource diff...
    assert late_node not in [
        UUID(str(node["id"]))
        for node in document["resource_diff"]["composition_nodes"]["added"]
    ]
    # ...and the immutable snapshot never contains post-freeze content.
    state = document["normalized_state"]
    assert str(late_operation) not in timeline_ids
    for page in state["pages"]:
        for node in _walk_nodes(page["nodes"]):
            assert str(node["id"]) != str(late_node)


@pytest.mark.asyncio
async def test_read_model_drift_tracks_site_revision(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    seeded = await _seed(database)
    await _freeze_complete(database, seeded)

    first = await _read_model(
        database, seeded["workspace_id"], seeded["site_id"], seeded["delegator_id"]
    )
    assert first["drift"]["equal"] is True
    base = first["drift"]["base_site_revision"]

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "UPDATE control.site SET canonical_revision = canonical_revision + 1"
            " WHERE id = $1",
            seeded["site_id"],
        )
    second = await _read_model(
        database, seeded["workspace_id"], seeded["site_id"], seeded["delegator_id"]
    )
    assert second["drift"]["equal"] is False
    assert second["drift"]["base_site_revision"] == base
    assert second["drift"]["current_site_revision"] == base + 1


@pytest.mark.asyncio
async def test_read_model_gating_matrix_is_uniform(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    seeded = await _seed(database)
    await _freeze_complete(database, seeded)

    negative = await asyncio_gather_gate(database, seeded)
    # Every denial is the identical stable internal class (no oracle).
    assert len(set(negative)) == 1
    assert "REVIEW_READ_UNAVAILABLE" in negative[0]

    # Platform administrators are allowed without site membership.
    admin_document = await _read_model(
        database, seeded["workspace_id"], seeded["site_id"], seeded["admin_id"]
    )
    assert admin_document["metadata"]["site"]["id"] == str(seeded["site_id"])


async def asyncio_gather_gate(
    database: AgentSiteDatabase, seeded: dict[str, UUID]
) -> list[str]:
    results: list[str] = []

    async def gate(workspace_id: UUID, site_id: UUID, user_id: UUID) -> str:
        try:
            await _read_model(database, workspace_id, site_id, user_id)
        except asyncpg.PostgresError as exc:
            assert exc.sqlstate == "P0002"
            return str(exc)
        raise AssertionError("gate did not fail closed")

    # Non-member on the real frozen workspace/site.
    results.append(
        await gate(seeded["workspace_id"], seeded["site_id"], seeded["nonmember_id"])
    )
    # Wrong-site binding: the workspace under another path site.
    results.append(
        await gate(
            seeded["workspace_id"], seeded["other_site_id"], seeded["delegator_id"]
        )
    )
    # Fresh ACTIVE workspace on the same site with no snapshot.
    results.append(
        await gate(
            seeded["fresh_workspace_id"], seeded["site_id"], seeded["delegator_id"]
        )
    )
    # Well-formed but unknown workspace id.
    results.append(await gate(uuid4(), seeded["site_id"], seeded["delegator_id"]))
    # Unknown site id.
    results.append(await gate(seeded["workspace_id"], uuid4(), seeded["delegator_id"]))
    return results


@pytest.mark.asyncio
async def test_review_route_http_uniform(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    seeded = await _seed(database)
    await _freeze_complete(database, seeded)
    adapter, client = await _control_http(database)
    try:
        path = _review_path(seeded["site_id"], seeded["workspace_id"])
        delegator_cookie = await _session_cookie(adapter, seeded["delegator_id"])

        # Happy path: the HTTP document is the read-model document.
        response = await client.get(path, headers={"cookie": delegator_cookie})
        assert response.status_code == 200
        http_document = response.json()
        db_document = await _read_model(
            database,
            seeded["workspace_id"],
            seeded["site_id"],
            seeded["delegator_id"],
        )
        assert http_document == db_document

        # Unauthenticated: 401.
        assert (await client.get(path)).status_code == 401
        assert (
            await client.get(path, headers={"cookie": "slaif_session=invalid"})
        ).status_code == 401

        # Every gate failure is the same uniform 404 shape (no oracle).
        denials: dict[str, dict[str, Any]] = {}
        nonmember_cookie = await _session_cookie(adapter, seeded["nonmember_id"])
        response = await client.get(path, headers={"cookie": nonmember_cookie})
        assert response.status_code == 404
        denials["nonmember"] = response.json()
        response = await client.get(
            _review_path(seeded["other_site_id"], seeded["workspace_id"]),
            headers={"cookie": delegator_cookie},
        )
        assert response.status_code == 404
        denials["wrong-site"] = response.json()
        response = await client.get(
            _review_path(seeded["site_id"], seeded["fresh_workspace_id"]),
            headers={"cookie": delegator_cookie},
        )
        assert response.status_code == 404
        denials["no-snapshot"] = response.json()
        response = await client.get(
            _review_path(seeded["site_id"], uuid4()),
            headers={"cookie": delegator_cookie},
        )
        assert response.status_code == 404
        denials["unknown-workspace"] = response.json()
        for body in denials.values():
            body["error"].pop("request_id", None)
        assert len({json.dumps(body, sort_keys=True) for body in denials.values()}) == 1

        # Platform administrator (no site membership) reads the same document.
        admin_cookie = await _session_cookie(adapter, seeded["admin_id"])
        response = await client.get(path, headers={"cookie": admin_cookie})
        assert response.status_code == 200
        assert response.json() == http_document

        # Malformed path id: the established control-plane 422 contract.
        response = await client.get(
            _review_path(seeded["site_id"], "not-a-uuid"),
            headers={"cookie": delegator_cookie},
        )
        assert response.status_code == 422
    finally:
        await client.aclose()
        await adapter.stop()
