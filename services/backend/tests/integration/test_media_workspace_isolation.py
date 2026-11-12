"""077_001 workspace-isolated media: A2 upload visibility regressions.

Baseline provenance (independent clone at unmodified product M
d888b37f, round 083-10-a; donor test
c262a9d87c85e5a70df4e9190a2e902bb33b0eafdb869697ae8922ef67ea3af1,
retained donor diff
ba27ffac03004711f0e8166194075a21cddf0f347e0e917bbff2026c7b6c8326,
R3 run log
f1066995d784cbe2c14c366950b053275885d82d88582f1d090fbe09c0aa39fa):
both actual uploads succeeded (201, human and agent), both same-site B
content reads returned the uploaded bytes (200), and one canonical
private media_asset_base row existed per hash.  Both executed assertion
failures were at the B-404 desired oracle (observed 200); the
canonical-0 assertion sits after it and did not execute, and the public
digest 404 was an unasserted baseline sanity observation.  Private
records: a2-baseline-red-human.json
SHA 6d2867ad41e6e986d1bf22b284da73e11a50bd082bab6c4fce03363d5b6476a3,
a2-baseline-red-agent.json
SHA 9078fc9e60c84a89dfa94f92988e508fa5b8198eaa421443f9d53d8ccfc3bbfc.

Against the 077_001 implementation these oracles must hold GREEN:

1. the actual upload really succeeds (201) and the uploading workspace
   reads its own pending asset back with exact bytes;
2. a different-workspace member B of the SAME site cannot read the
   just-uploaded private asset (404) before human promotion;
3. no canonical content.media_asset_base row exists at upload time;
4. the sessionless public digest route stays 404 (nothing published;
   newly asserted here, an unasserted baseline observation).

This module covers the A2 upload-visibility subset and the first A3
case: a lawful delegating human Editor PATCH/DELETE on a pending
AGENT-workspace asset through the real X-Editor-Workspace envelope,
with the HUMAN_EDITOR audit family (audit.human_editor_mutation) and
the untouched agent MEDIA_UPLOADED audit row (audit.agent_mutation).
The remaining A3 human-workspace and canonical-media variants, the
A5 NEW-pending worker acceptance/replay and AFTER-BOTH rollback proof,
and the A6..A8 evidence stay in the companion modules.

The Control pool uses its real start/stop lifetime; media/agent pools are
owned by their app lifespans, as in the proven fixtures.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.editor_api.app import create_app as create_editor_app
from slaif_agent_site.editor_api.database import EditorDatabase
from slaif_agent_site.media_service.app import create_app as create_media_app
from slaif_agent_site.media_service.database import MediaDatabase
from slaif_agent_site.media_service.store import MediaStore
from test_media_security_lifecycle import (
    _control_settings,
    _cookie,
    _editor_settings,
    _headers,
    _media_settings,
    _seed_ordinary_fixture,
)
from test_media_service import AGENT_SCOPES, _agent_settings
from test_real_human_accept import _CURRENT_VERSION_FACTS

HUMAN_PNG = b"\x89PNG\r\n\x1a\na2-baseline-human-red"
AGENT_PNG = b"\x89PNG\r\n\x1a\na2-baseline-agent-red"

_CANONICAL_SQL = (
    "SELECT count(*) AS rows_, "
    "coalesce(string_agg(DISTINCT public_status::text, ','), '') AS statuses, "
    "coalesce(min(alt_text), '') AS alt_text "
    "FROM content.media_asset_base WHERE content_hash = $1"
)


async def _canonical(database: AgentSiteDatabase, content_hash: str) -> dict[str, Any]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        row = await owner.fetchrow(_CANONICAL_SQL, content_hash)
    return {
        "rows": int(row["rows_"]),
        "statuses": [s for s in str(row["statuses"]).split(",") if s],
        "alt_text": str(row["alt_text"]),
    }


async def _read_b(
    client: httpx.AsyncClient, session_b: Any, site_id: UUID, asset_id: UUID
) -> int:
    resp = await client.get(
        f"/v1/sites/{site_id}/assets/{asset_id}/content",
        headers={"cookie": _cookie(session_b)},
    )
    return resp.status_code


@pytest.mark.asyncio
async def test_media_workspace_isolation_human_upload(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """A2 human channel: same-site B is 404, canonical base stays empty."""

    database = agent_site_database
    ids = await _seed_ordinary_fixture(database)  # upgrade + reconcile inside
    store = MediaStore(tmp_path / "media")
    control = ControlDatabase(_control_settings(database))
    media_database = MediaDatabase(_media_settings(database, store.root))
    media_app = create_media_app(
        settings=ServiceSettings.for_test(),
        media_settings=media_database.settings,
        database=media_database,
        store=store,
    )
    await control.start()
    try:
        async with media_app.router.lifespan_context(media_app):
            session_a = await control.human_session_service().create(ids["user_a"])
            session_b = await control.human_session_service().create(ids["user_b"])
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=media_app),
                base_url="http://isolation-human.test",
            ) as client:
                uploaded = await client.post(
                    f"/v1/sites/{ids['site_a']}/assets",
                    headers=_headers(session_a, "isolation-human-upload"),
                    data={"alt_text": "A2 private alt", "metadata": "{}"},
                    files={"file": ("a2.png", HUMAN_PNG, "image/png")},
                )
                assert uploaded.status_code == 201, uploaded.text
                record = uploaded.json()["record"]
                asset_id = UUID(record["id"])
                content_hash = str(record["content_hash"])

                # Positive own-workspace read stays intact: A sees its own
                # pending asset.
                own_read = await client.get(
                    f"/v1/sites/{ids['site_a']}/assets/{asset_id}/content",
                    headers={"cookie": _cookie(session_a)},
                )
                assert own_read.status_code == 200
                assert own_read.content == HUMAN_PNG

                b_status = await _read_b(client, session_b, ids["site_a"], asset_id)
                canonical = await _canonical(database, content_hash)
                public = await client.get(
                    f"/v1/public/sha256/{content_hash[:2]}/"
                    f"{content_hash[2:4]}/{content_hash}"
                )

                # Desired A2 workspace isolation (B-404 proven RED at M).
                assert b_status == 404, (
                    "same-site different-workspace read must be 404, "
                    f"observed {b_status}"
                )
                assert canonical["rows"] == 0, (
                    "no canonical media_asset_base row may exist at upload, "
                    f"observed {canonical}"
                )
                assert public.status_code == 404
    finally:
        await control.stop()


async def _seed_agent_fixture(database: AgentSiteDatabase) -> dict[str, Any]:
    """upgrade+reconcile; site_a with SITE_OWNER user_a + SITE_EDITOR user_b;
    one AGENT workspace (delegator user_a, media scopes) + its capability."""

    await upgrade(database.settings)
    await reconcile(database.settings)
    ids: dict[str, Any] = {
        "user_a": uuid4(),
        "user_b": uuid4(),
        "site_a": uuid4(),
        "workspace_a": uuid4(),
        "workspace_b": uuid4(),
        "agent_workspace": uuid4(),
    }
    capability_token, capability_public, capability_digest = generate_capability_token()
    expires = datetime.now(UTC) + timedelta(minutes=30)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.executemany(
            "INSERT INTO control.user_account "
            "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
            "VALUES ($1, 'OIDC', 'https://a2.test', $2, $3)",
            [
                (ids["user_a"], str(ids["user_a"]), "A2 Owner"),
                (ids["user_b"], str(ids["user_b"]), "A2 Editor B"),
            ],
        )
        await owner.execute(
            "INSERT INTO control.site "
            "(id, site_key, display_name, default_locale, component_catalog_version) "
            "VALUES ($1, $2, $3, 'en', 'catalog-v1')",
            ids["site_a"],
            f"a2-a-{ids['site_a'].hex[:10]}",
            "A2 Site",
        )
        await owner.executemany(
            "INSERT INTO control.site_membership "
            "(site_id, user_account_id, role_key, delegation_ceiling) "
            "VALUES ($1, $2, $3, $4)",
            [
                (ids["site_a"], ids["user_a"], "SITE_OWNER", 4),
                (ids["site_a"], ids["user_b"], "SITE_EDITOR", 2),
            ],
        )
        for ws_key, user_key in (
            ("workspace_a", "user_a"),
            ("workspace_b", "user_b"),
        ):
            await owner.execute(
                "INSERT INTO control.workspace "
                "(id, site_id, created_by, actor_type, title, "
                "delegation_preset, effective_scopes, status, expires_at) "
                "VALUES ($1, $2, $3, 'HUMAN', $4, 'L2_SITE_EDITOR', "
                "'[]'::jsonb, 'ACTIVE', now() + interval '1 hour')",
                ids[ws_key],
                ids["site_a"],
                ids[user_key],
                ws_key,
            )
        await owner.execute(
            "INSERT INTO control.workspace "
            "(id, site_id, created_by, delegator_id, actor_type, title, "
            "delegation_preset, effective_scopes, version_facts, status, "
            "expires_at) VALUES ($1,$2,$3,$3,'AGENT',"
            " 'a2 agent workspace','L4',$4::jsonb,"
            + _CURRENT_VERSION_FACTS
            + ", 'ACTIVE', now() + interval '2 hours')",
            ids["agent_workspace"],
            ids["site_a"],
            ids["user_a"],
            json.dumps(list(AGENT_SCOPES)),
        )
        await owner.execute(
            "INSERT INTO control.capability "
            "(id, workspace_id, public_id, secret_digest, scopes, "
            "request_quota, mutation_quota, delete_quota, upload_quota, "
            "expires_at, browser_max_concurrent_runs, browser_max_artifact_bytes) "
            "VALUES ($1,$2,$3,$4,$5::jsonb,1000,500,100,50,$6,10,104857600)",
            uuid4(),
            ids["agent_workspace"],
            capability_public,
            capability_digest,
            json.dumps(list(AGENT_SCOPES)),
            expires,
        )
    ids["capability_token"] = capability_token
    return ids


@pytest.mark.asyncio
async def test_media_workspace_isolation_agent_upload(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """A2 agent channel: same-site human B is 404, canonical base empty."""

    database = agent_site_database
    ids = await _seed_agent_fixture(database)
    store = MediaStore(tmp_path / "media")
    control = ControlDatabase(_control_settings(database))
    media_database = MediaDatabase(_media_settings(database, store.root))
    media_app = create_media_app(
        settings=ServiceSettings.for_test(),
        media_settings=media_database.settings,
        database=media_database,
        store=store,
    )
    agent_app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database, store.root),
    )
    await control.start()
    try:
        session_b = await control.human_session_service().create(ids["user_b"])
        async with media_app.router.lifespan_context(media_app):
            async with agent_app.router.lifespan_context(agent_app):
                async with (
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=agent_app),
                        base_url="http://isolation-agent.test",
                    ) as agent_client,
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=media_app),
                        base_url="http://isolation-human.test",
                    ) as media_client,
                ):
                    uploaded = await agent_client.post(
                        "/api/agent/v1/media/assets",
                        headers={
                            "Authorization": f"Bearer {ids['capability_token']}",
                            "Idempotency-Key": "isolation-agent-upload",
                        },
                        data={"alt_text": "A2 agent alt", "metadata": "{}"},
                        files={"file": ("a2.png", AGENT_PNG, "image/png")},
                    )
                    assert uploaded.status_code == 201, uploaded.text
                    record = uploaded.json()["record"]
                    asset_id = UUID(record["id"])
                    content_hash = str(record["content_hash"])

                    # Positive own-workspace read: the agent capability
                    # reads its own pending upload back pre-freeze.
                    own_read = await agent_client.get(
                        f"/api/agent/v1/media/assets/{asset_id}/content",
                        headers={"Authorization": f"Bearer {ids['capability_token']}"},
                    )
                    assert own_read.status_code == 200, own_read.text
                    assert own_read.content == AGENT_PNG

                    b_status = await _read_b(
                        media_client, session_b, ids["site_a"], asset_id
                    )
                    canonical = await _canonical(database, content_hash)
                    public = await media_client.get(
                        f"/v1/public/sha256/{content_hash[:2]}/"
                        f"{content_hash[2:4]}/{content_hash}"
                    )

                    # Desired A2 workspace isolation (B-404 proven RED at M).
                    assert b_status == 404, (
                        "same-site different-workspace read must be 404, "
                        f"observed {b_status}"
                    )
                    assert canonical["rows"] == 0, (
                        "no canonical media_asset_base row may exist at upload, "
                        f"observed {canonical}"
                    )
                    assert public.status_code == 404
    finally:
        await control.stop()


def _human_editor_headers(session: Any, key: str, workspace_id: UUID) -> dict[str, str]:
    """Editor envelope for a lawful human Editor targeting a workspace."""
    return {**_headers(session, key), "x-editor-workspace": str(workspace_id)}


async def _audit_dicts(rows: Any) -> list[dict[str, Any]]:
    return [{key: row[key] for key in row.keys()} for row in rows]


async def _human_editor_audit(
    database: AgentSiteDatabase, site_id: UUID, workspace_id: UUID
) -> list[dict[str, Any]]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        rows = await owner.fetch(
            "SELECT operation_id, human_user_id, workspace_id, site_id, action, "
            "resource_type, resource_id, request_digest, response_status "
            "FROM audit.human_editor_mutation "
            "WHERE site_id = $1 AND workspace_id = $2",
            site_id,
            workspace_id,
        )
    return await _audit_dicts(rows)


async def _agent_media_upload_audit(
    database: AgentSiteDatabase, site_id: UUID, workspace_id: UUID
) -> list[dict[str, Any]]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        rows = await owner.fetch(
            "SELECT operation_id, capability_id, workspace_id, site_id, "
            "resource_type, resource_id, request_digest, response_status, "
            "action, http_method, quota_kind "
            "FROM audit.agent_mutation "
            "WHERE site_id = $1 AND workspace_id = $2 "
            "AND action = 'MEDIA_UPLOADED'",
            site_id,
            workspace_id,
        )
    return await _audit_dicts(rows)


@pytest.mark.asyncio
async def test_media_human_editor_on_agent_workspace_patch_delete(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """A3 first case: human Editor PATCH/DELETE on a pending AGENT asset.

    The upload exists only in the AGENT workspace COW overlay.  The
    delegating SITE_OWNER edits/deletes it through the real
    X-Editor-Workspace envelope; the same-site non-delegator is safely
    denied; no canonical base row ever appears; both human mutations
    land in the HUMAN_EDITOR audit family, and the agent upload keeps
    its own MEDIA_UPLOADED audit row.
    """

    database = agent_site_database
    ids = await _seed_agent_fixture(database)
    store = MediaStore(tmp_path / "media")
    control = ControlDatabase(_control_settings(database))
    editor = EditorDatabase(_editor_settings(database))
    media_database = MediaDatabase(_media_settings(database, store.root))
    media_app = create_media_app(
        settings=ServiceSettings.for_test(),
        media_settings=media_database.settings,
        database=media_database,
        store=store,
    )
    editor_app = create_editor_app(
        settings=ServiceSettings.for_test(), database=control, editor_database=editor
    )
    agent_app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database, store.root),
    )

    async with editor_app.router.lifespan_context(editor_app):
        async with media_app.router.lifespan_context(media_app):
            async with agent_app.router.lifespan_context(agent_app):
                session_a = await control.human_session_service().create(ids["user_a"])
                session_b = await control.human_session_service().create(ids["user_b"])
                async with (
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=agent_app),
                        base_url="http://isolation-a3-agent.test",
                    ) as agent_client,
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=media_app),
                        base_url="http://isolation-a3-media.test",
                    ) as media_client,
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=editor_app),
                        base_url="http://isolation-a3-editor.test",
                    ) as editor_client,
                ):
                    uploaded = await agent_client.post(
                        "/api/agent/v1/media/assets",
                        headers={
                            "Authorization": f"Bearer {ids['capability_token']}",
                            "Idempotency-Key": "a3-agent-upload",
                        },
                        data={"alt_text": "A3 agent alt", "metadata": "{}"},
                        files={"file": ("a3.png", AGENT_PNG, "image/png")},
                    )
                    assert uploaded.status_code == 201, uploaded.text
                    record = uploaded.json()["record"]
                    asset_id = UUID(record["id"])
                    content_hash = str(record["content_hash"])

                    own_read = await agent_client.get(
                        f"/api/agent/v1/media/assets/{asset_id}/content",
                        headers={"Authorization": f"Bearer {ids['capability_token']}"},
                    )
                    assert own_read.status_code == 200, own_read.text
                    assert own_read.content == AGENT_PNG

                    assert (await _canonical(database, content_hash))["rows"] == 0
                    upload_audit = await _agent_media_upload_audit(
                        database, ids["site_a"], ids["agent_workspace"]
                    )
                    assert len(upload_audit) == 1, upload_audit
                    upload_row = upload_audit[0]
                    assert upload_row["capability_id"] is not None
                    assert upload_row["workspace_id"] == ids["agent_workspace"]
                    assert upload_row["site_id"] == ids["site_a"]
                    assert upload_row["resource_type"] == "media_asset"
                    assert upload_row["resource_id"] == asset_id
                    assert upload_row["response_status"] == 201
                    assert upload_row["http_method"] == "POST"
                    assert upload_row["quota_kind"] == "upload"

                    # Lawful delegator human Editor PATCH in the AGENT ws.
                    patch_action = (
                        f"PATCH /api/editor/v1/sites/{ids['site_a']}/media/{asset_id}"
                    )
                    patch = await editor_client.patch(
                        f"/api/editor/v1/sites/{ids['site_a']}/media/{asset_id}",
                        headers=_human_editor_headers(
                            session_a, "a3-human-patch", ids["agent_workspace"]
                        ),
                        json={"alt_text": "A3 human patched"},
                    )
                    assert patch.status_code == 200, patch.text
                    assert patch.json()["alt_text"] == "A3 human patched"

                    # Same-workspace positive read shows the pending edit;
                    # the agent's own byte read is unaffected by it.
                    patched_read = await editor_client.get(
                        f"/api/editor/v1/sites/{ids['site_a']}/media/{asset_id}",
                        headers=_human_editor_headers(
                            session_a, "a3-patched-read", ids["agent_workspace"]
                        ),
                    )
                    assert patched_read.status_code == 200, patched_read.text
                    assert patched_read.json()["alt_text"] == "A3 human patched"
                    bytes_after_patch = await agent_client.get(
                        f"/api/agent/v1/media/assets/{asset_id}/content",
                        headers={"Authorization": f"Bearer {ids['capability_token']}"},
                    )
                    assert bytes_after_patch.status_code == 200, bytes_after_patch.text
                    assert bytes_after_patch.content == AGENT_PNG

                    # The human's own workspace does not see the agent's
                    # pending asset, and a non-delegator is safely denied.
                    own_ws_read = await editor_client.get(
                        f"/api/editor/v1/sites/{ids['site_a']}/media/{asset_id}",
                        headers=_headers(session_a, "a3-own-ws-read"),
                    )
                    assert own_ws_read.status_code == 404
                    denied = await editor_client.patch(
                        f"/api/editor/v1/sites/{ids['site_a']}/media/{asset_id}",
                        headers=_human_editor_headers(
                            session_b, "a3-b-deny", ids["agent_workspace"]
                        ),
                        json={"alt_text": "B must not write"},
                    )
                    assert denied.status_code == 503, denied.text
                    b_content = await media_client.get(
                        f"/v1/sites/{ids['site_a']}/assets/{asset_id}/content",
                        headers={"cookie": _cookie(session_b)},
                    )
                    assert b_content.status_code == 404

                    assert (await _canonical(database, content_hash))["rows"] == 0
                    patch_rows = await _human_editor_audit(
                        database, ids["site_a"], ids["agent_workspace"]
                    )
                    assert len(patch_rows) == 1, patch_rows
                    patch_row = patch_rows[0]
                    assert patch_row["human_user_id"] == ids["user_a"]
                    assert patch_row["workspace_id"] == ids["agent_workspace"]
                    assert patch_row["site_id"] == ids["site_a"]
                    assert patch_row["action"] == patch_action
                    assert patch_row["resource_type"] == "editor.sites"
                    assert patch_row["resource_id"] == asset_id
                    assert patch_row["response_status"] == 200
                    assert patch_row["request_digest"]

                    # Lawful human Editor DELETE in the AGENT ws.
                    delete_action = (
                        f"DELETE /api/editor/v1/sites/{ids['site_a']}/media/{asset_id}"
                    )
                    deleted = await editor_client.delete(
                        f"/api/editor/v1/sites/{ids['site_a']}/media/{asset_id}",
                        headers=_human_editor_headers(
                            session_a, "a3-human-delete", ids["agent_workspace"]
                        ),
                    )
                    assert deleted.status_code == 204, deleted.text

                    agent_after = await agent_client.get(
                        f"/api/agent/v1/media/assets/{asset_id}/content",
                        headers={"Authorization": f"Bearer {ids['capability_token']}"},
                    )
                    assert agent_after.status_code == 404
                    human_after = await editor_client.get(
                        f"/api/editor/v1/sites/{ids['site_a']}/media/{asset_id}",
                        headers=_human_editor_headers(
                            session_a, "a3-after-delete", ids["agent_workspace"]
                        ),
                    )
                    assert human_after.status_code == 404

                    assert (await _canonical(database, content_hash))["rows"] == 0
                    final_rows = await _human_editor_audit(
                        database, ids["site_a"], ids["agent_workspace"]
                    )
                    assert len(final_rows) == 2, final_rows
                    by_action = {row["action"]: row for row in final_rows}
                    assert set(by_action) == {patch_action, delete_action}, by_action
                    assert (
                        by_action[patch_action]["operation_id"]
                        == patch_row["operation_id"]
                    )
                    delete_row = by_action[delete_action]
                    assert delete_row["human_user_id"] == ids["user_a"]
                    assert delete_row["workspace_id"] == ids["agent_workspace"]
                    assert delete_row["site_id"] == ids["site_a"]
                    assert delete_row["resource_type"] == "editor.sites"
                    assert delete_row["resource_id"] == asset_id
                    assert delete_row["response_status"] == 204

                    # The agent upload's own audit row is untouched.
                    unchanged = await _agent_media_upload_audit(
                        database, ids["site_a"], ids["agent_workspace"]
                    )
                    assert unchanged == upload_audit
