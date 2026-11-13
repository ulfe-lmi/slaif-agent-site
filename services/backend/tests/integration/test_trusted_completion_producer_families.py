"""C2/C3 producer-family and history-shape coverage for 078_001 completions.

Real HTTP surfaces over the explicitly owned PostgreSQL: HUMAN Editor
writes in the human's own workspace and inside a genuine AGENT
workspace, repeated same-resource operations across families, one
multirow navigation move that keeps a single completion, theme
superseding, and page create+delete net-zero.  Each case asserts the
honest trusted completion plus its family audit and reservation
relationship and measures exact pending operation IDs through the
public SDK read.  Human media upload and the agent-upload-then-human-
edit mixed-asset completions are covered by the qualified
test_media_workspace_isolation.py cases in the same matrix.  The P2
legacy boundary is also proven here: the deployed 10-argument
control.slaif_agent_idempotency_complete overload (078_001 re-emits
the 047_001 body with the single outer journal record) has no
current Python caller, so its cases use the exact runtime SQL
constants inside a real public COW session on a genuine AGENT
workspace - one allowed legacy page completion (durable journal,
family audit, ledger, runtime replay, direct-duplicate refusal) and
one forbidden content-model completion (whole-transaction rollback).
Direct SQL/COW proof only; the actual HTTP surfaces are covered by
the other modules in this matrix.

Fixture honesty: the generic test_agent_mutations ``_seed`` workspace
omits ``actor_type`` and is therefore a HUMAN workspace under the
released default, despite its title.  The genuine own-human path uses
it as-is (the editor resolver lawfully returns it), while every
AGENT-family case and the explicit human-in-AGENT case act on a fresh
AGENT workspace (actor_type AGENT, L4, delegator = site owner, current
version facts) created by the owner fixture helper below, which also
returns the actual issued capability ID for journal identity checks.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
import slaif_agent_site.agent_api  # noqa: F401  product import order
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_reviewer,
    asyncpg_cow_session,
    get_session_operations,
)
from slaif_agent_site.agent_state.mutations import (
    AGENT_PAGE_CREATE_SQL,
    BEGIN_IDEMPOTENCY_SQL,
    COMPLETE_IDEMPOTENCY_SQL,
)
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.executor import AsyncpgExecutor
from slaif_agent_site.editor_api.app import create_app as create_editor_app
from slaif_agent_site.editor_api.database import EditorDatabase
from slaif_agent_site.health import ComponentStatus
from test_agent_mutations import _seed
from test_agent_theme_boundaries import _agent_client
from test_media_security_lifecycle import (
    _control_settings,
    _editor_settings,
)
from test_media_workspace_isolation import (
    _assert_completion,
    _completion_rows,
    _family_audit_rows,
    _reservation,
)
from test_real_human_accept import _CURRENT_VERSION_FACTS
from test_trusted_completion_late_failure import _create_page, _request_headers


def _cookie(session: str, csrf: str | None = None) -> str:
    value = f"slaif_session={session}"
    return value if csrf is None else f"{value}; slaif_csrf={csrf}"


def _editor_headers(
    session: str, csrf: str, key: str, workspace_id: UUID | None = None
) -> dict[str, str]:
    headers = {
        "cookie": _cookie(session, csrf),
        "x-csrf-token": csrf,
        "idempotency-key": key,
    }
    if workspace_id is not None:
        headers["x-editor-workspace"] = str(workspace_id)
    return headers


def _read_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _seed_agent_workspace(
    database: AgentSiteDatabase,
    site_id: UUID,
    delegator_id: UUID,
    scopes: list[str],
    title: str,
) -> tuple[str, UUID, UUID]:
    """Owner fixture: one genuine AGENT workspace (actor_type AGENT,
    L4, delegator = the site owner, current version facts) with one
    capability carrying the given real scopes and explicit quota
    headroom.  Returns the actual issued (token, workspace,
    capability) IDs for later identity assertions."""
    workspace_id = uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO control.workspace "
            "(id, site_id, created_by, delegator_id, actor_type, title, "
            "delegation_preset, effective_scopes, version_facts, status, "
            "expires_at) VALUES ($1, $2, $3, $3, 'AGENT', $4, 'L4', "
            "$5::jsonb, "
            + _CURRENT_VERSION_FACTS
            + ", 'ACTIVE', now() + interval '2 hours')",
            workspace_id,
            site_id,
            delegator_id,
            title,
            json.dumps(scopes),
        )
        token, public_id, secret_digest = generate_capability_token()
        await owner.execute(
            "INSERT INTO control.capability "
            "(id, workspace_id, public_id, secret_digest, scopes, "
            "request_quota, mutation_quota, delete_quota, upload_quota, "
            "expires_at, browser_max_concurrent_runs, "
            "browser_max_artifact_bytes) "
            "VALUES ($1, $2, $3, $4, $5::jsonb, 1000, 500, 100, 50, "
            "now() + interval '30 minutes', 10, 104857600)",
            uuid4(),
            workspace_id,
            public_id,
            secret_digest,
            json.dumps(scopes),
        )
        capability_id = UUID(
            str(
                await owner.fetchval(
                    "SELECT id FROM control.capability WHERE public_id = $1",
                    public_id,
                )
            )
        )
    return token, workspace_id, capability_id


@asynccontextmanager
async def _editor_stack(
    database: AgentSiteDatabase,
) -> AsyncIterator[tuple[ControlDatabase, httpx.AsyncClient]]:
    control = ControlDatabase(_control_settings(database))
    editor = EditorDatabase(_editor_settings(database))
    app = create_editor_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST),
        database=control,
        editor_database=editor,
    )
    try:
        async with app.router.lifespan_context(app):
            # The generic fixture installs its own login/credential set;
            # prove the actual pool is live before any session request.
            assert (await control.readiness()).status is ComponentStatus.OK
            assert (await editor.readiness()).status is ComponentStatus.OK
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://editor.test",
            ) as client:
                yield control, client
    finally:
        await control.stop()
        await editor.stop()


async def _human_session(control: ControlDatabase, human_id: UUID) -> tuple[str, str]:
    issued = await control.human_session_service().create(human_id)
    return (
        issued.token.get_secret_value(),
        issued.csrf_token.get_secret_value(),
    )


async def _resolve_human_workspace(
    database: AgentSiteDatabase, site_id: UUID, human_id: UUID
) -> UUID:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return UUID(
            str(
                await owner.fetchval(
                    "SELECT control.slaif_human_editor_workspace_resolve($1, $2)",
                    site_id,
                    human_id,
                )
            )
        )


async def _pending_operations(
    database: AgentSiteDatabase, workspace_id: UUID
) -> list[UUID]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        executor = AsyncpgExecutor(connection)
        operations: list[UUID] = await get_session_operations(
            executor, workspace_id, schema="content"
        )
    return operations


async def _canonical_page_count(database: AgentSiteDatabase, page_id: UUID) -> int:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        count: int = await owner.fetchval(
            "SELECT count(*) FROM content.page_base WHERE id = $1", page_id
        )
    return count


async def _agent_theme(client: httpx.AsyncClient, token: str) -> dict[str, Any]:
    response = await client.get("/api/agent/v1/theme", headers=_read_headers(token))
    assert response.status_code == 200, response.text
    payload: dict[str, Any] = response.json()
    return payload


async def _agent_patch_theme(
    client: httpx.AsyncClient,
    token: str,
    *,
    key: str,
    preset: str,
    expected_row_version: int,
) -> httpx.Response:
    return await client.patch(
        "/api/agent/v1/theme",
        json={
            "expected_row_version": expected_row_version,
            "palette": {"preset": preset},
        },
        headers=_request_headers(token, key),
    )


def _item_positions(listing: httpx.Response) -> dict[UUID, tuple[int, int]]:
    """Workspace-view (id -> (position, row_version)) from the real
    authenticated listing: the multirow proof, not an array order alone."""
    positions: dict[UUID, tuple[int, int]] = {}
    for rec in listing.json():
        positions[UUID(rec["id"])] = (rec["position"], rec["row_version"])
    return positions


@pytest.mark.asyncio
async def test_human_editor_own_workspace_write_single_completion(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """C2: a HUMAN Editor write in the human's own workspace produces
    exactly one human_editor completion with its audit + reservation,
    while canonical and a genuinely distinct AGENT sibling workspace
    stay untouched."""
    database = agent_site_database
    _token, seeded = await _seed(database)
    site_id = seeded["site_id"]
    human_id = seeded["delegator_id"]
    ws_human = await _resolve_human_workspace(database, site_id, human_id)
    # The generic seeded workspace is the delegator's HUMAN workspace
    # (released actor_type default); the resolver lawfully returns it.
    assert ws_human == seeded["workspace_id"]
    _token_sibling, ws_agent_sibling, _cap_sibling = await _seed_agent_workspace(
        database, site_id, human_id, ["site:read"], "pf own-ws agent sibling"
    )

    async with _editor_stack(database) as (control, client):
        session, csrf = await _human_session(control, human_id)
        created = await client.post(
            f"/api/editor/v1/sites/{site_id}/pages/",
            json={
                "slug": "pf-human-page",
                "title": "PF human page",
                "status": "DRAFT",
                "locale": "en-US",
            },
            headers=_editor_headers(session, csrf, "pf-human-page"),
        )
        assert created.status_code == 201, created.text
        page_id = UUID(created.json()["id"])

    rows = await _completion_rows(database, workspace_id=ws_human)
    assert len(rows) == 1, rows
    row = rows[0]
    assert row["disposition"] == "completed", row
    reservation = await _reservation(
        database, "human_editor_idempotency", row["operation_id"]
    )
    assert reservation is not None, "missing human_editor reservation"
    assert reservation["idempotency_key"] == "pf-human-page"
    audit_rows = await _family_audit_rows(database, "human_editor", row["operation_id"])
    assert len(audit_rows) == 1, audit_rows
    assert audit_rows[0]["request_digest"] == reservation["request_digest"]
    # The Editor journal records the editor domain resource type with
    # the page UUID as resource identity (response root id).
    _assert_completion(
        row,
        family="human_editor",
        site_id=site_id,
        workspace_id=ws_human,
        principal=human_id,
        capability_id=None,
        key="pf-human-page",
        digest=reservation["request_digest"],
        resource_type="editor.sites",
        resource_id=page_id,
    )
    # Public SDK pending read: the write is the only pending operation.
    assert await _pending_operations(database, ws_human) == [row["operation_id"]]
    # Canonical stays untouched and the genuinely distinct AGENT
    # sibling workspace sees no completion or pending operation.
    assert await _canonical_page_count(database, page_id) == 0
    assert await _completion_rows(database, workspace_id=ws_agent_sibling) == []
    assert await _pending_operations(database, ws_agent_sibling) == []


@pytest.mark.asyncio
async def test_human_editor_in_agent_workspace_single_completion(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """C2: a HUMAN Editor writing INSIDE a genuine AGENT workspace
    (delegator, X-Editor-Workspace) is the human_editor family, not a
    fourth family, and produces exactly one trusted completion; the
    human's own seeded workspace stays untouched."""
    database = agent_site_database
    _token, seeded = await _seed(database)
    site_id = seeded["site_id"]
    human_id = seeded["delegator_id"]
    _token_agent, ws_agent, _cap_agent = await _seed_agent_workspace(
        database, site_id, human_id, ["site:read"], "pf human-in-agent workspace"
    )

    async with _editor_stack(database) as (control, client):
        session, csrf = await _human_session(control, human_id)
        created = await client.post(
            f"/api/editor/v1/sites/{site_id}/pages/",
            json={
                "slug": "pf-agent-ws-page",
                "title": "PF agent-ws page",
                "status": "DRAFT",
                "locale": "en-US",
            },
            headers=_editor_headers(session, csrf, "pf-agent-ws-page", ws_agent),
        )
        assert created.status_code == 201, created.text
        page_id = UUID(created.json()["id"])

    rows = await _completion_rows(database, workspace_id=ws_agent)
    assert len(rows) == 1, rows
    row = rows[0]
    assert row["disposition"] == "completed", row
    reservation = await _reservation(
        database, "human_editor_idempotency", row["operation_id"]
    )
    assert reservation is not None
    assert reservation["idempotency_key"] == "pf-agent-ws-page"
    assert (
        len(await _family_audit_rows(database, "human_editor", row["operation_id"]))
        == 1
    )
    _assert_completion(
        row,
        family="human_editor",
        site_id=site_id,
        workspace_id=ws_agent,
        principal=human_id,
        capability_id=None,
        key="pf-agent-ws-page",
        digest=reservation["request_digest"],
        resource_type="editor.sites",
        resource_id=page_id,
    )
    assert await _pending_operations(database, ws_agent) == [row["operation_id"]]
    assert await _canonical_page_count(database, page_id) == 0
    # The human's own seeded HUMAN workspace is a different workspace
    # here and must stay untouched.
    assert await _completion_rows(database, workspace_id=seeded["workspace_id"]) == []
    assert await _pending_operations(database, seeded["workspace_id"]) == []


@pytest.mark.asyncio
async def test_same_resource_across_families_keeps_distinct_completions(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """C2: repeated same-resource operations across families (Agent
    creates the page in a genuine AGENT workspace, the delegating
    human edits the SAME page in that same workspace) are legal and
    keep two distinct completed histories with distinct request
    identities.  The resource UUID is identical while the resource
    TYPE is family-specific (agent "page" vs human "editor.sites")."""
    database = agent_site_database
    _token, seeded = await _seed(database)
    site_id = seeded["site_id"]
    human_id = seeded["delegator_id"]
    token, ws_agent, capability_id = await _seed_agent_workspace(
        database,
        site_id,
        human_id,
        ["site:read", "page:create", "page:read"],
        "pf cross-family workspace",
    )

    async with _agent_client(database) as client:
        created = await _create_page(
            client, token, key="pf-cross-agent", slug="pf-cross"
        )
    assert created.status_code == 201, created.text
    op_agent = UUID(created.json()["operation_id"])
    page_id = UUID(created.json()["record"]["id"])

    async with _editor_stack(database) as (control, client):
        session, csrf = await _human_session(control, human_id)
        updated = await client.patch(
            f"/api/editor/v1/sites/{site_id}/pages/{page_id}",
            json={"title": "PF cross edited", "expected_row_version": 1},
            headers=_editor_headers(session, csrf, "pf-cross-human", ws_agent),
        )
        assert updated.status_code == 200, updated.text

    # The Editor response is the resource record without an operation
    # field; the exact human operation is its durable reservation.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        op_human_raw = await owner.fetchval(
            "SELECT operation_id FROM control.human_editor_idempotency "
            "WHERE idempotency_key = $1",
            "pf-cross-human",
        )
    assert op_human_raw is not None, "missing human_editor reservation"
    op_human = UUID(str(op_human_raw))

    rows = await _completion_rows(database, workspace_id=ws_agent)
    assert len(rows) == 2, rows
    by_op = {str(row["operation_id"]): row for row in rows}
    assert set(by_op) == {str(op_agent), str(op_human)}
    agent_row = by_op[str(op_agent)]
    human_row = by_op[str(op_human)]
    # Same resource UUID, distinct family, type, and request identity.
    assert agent_row["resource_id"] == page_id
    assert human_row["resource_id"] == page_id
    assert agent_row["resource_type"] == "page"
    assert human_row["resource_type"] == "editor.sites"
    assert agent_row["request_identity"] != human_row["request_identity"]
    assert agent_row["capability_id"] == capability_id
    assert agent_row["human_user_id"] is None
    assert human_row["capability_id"] is None
    assert human_row["human_user_id"] == human_id
    assert len(await _family_audit_rows(database, "human_editor", op_human)) == 1
    pending = await _pending_operations(database, ws_agent)
    assert {str(op) for op in pending} == {str(op_agent), str(op_human)}
    assert await _canonical_page_count(database, page_id) == 0


@pytest.mark.asyncio
async def test_navigation_move_multirow_single_completion(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """C2: one navigation move in a genuine AGENT workspace reorders
    several item rows but records exactly ONE operation completion on
    the moved (primary) item - no per-row operations are invented.
    The authenticated listing proves the actual row positions and row
    versions of the non-primary rows changed before and after the
    single operation."""
    database = agent_site_database
    _token, seeded = await _seed(database)
    site_id = seeded["site_id"]
    human_id = seeded["delegator_id"]
    token, ws_agent, capability_id = await _seed_agent_workspace(
        database,
        site_id,
        human_id,
        ["site:read", "navigation:create", "navigation:write", "navigation:read"],
        "pf navigation move workspace",
    )

    targets = {
        "a": "https://example.test/alpha",
        "b": "https://example.test/beta",
        "c": "https://example.test/gamma",
    }

    async with _agent_client(database) as client:
        nav = await client.post(
            "/api/agent/v1/navigation",
            json={"key": "pf-main", "label": "PF main"},
            headers=_request_headers(token, "pf-nav"),
        )
        assert nav.status_code == 201, nav.text
        nav_id = UUID(nav.json()["record"]["id"])
        op_nav = UUID(nav.json()["operation_id"])
        item_ids: dict[str, UUID] = {}
        op_items: dict[str, UUID] = {}
        for name in ("a", "b", "c"):
            item = await client.post(
                f"/api/agent/v1/navigation/{nav_id}/items",
                json={
                    "labels": {"en": name.upper()},
                    "target_kind": "EXTERNAL",
                    "target_value": targets[name],
                },
                headers=_request_headers(token, f"pf-item-{name}"),
            )
            assert item.status_code == 201, item.text
            item_ids[name] = UUID(item.json()["record"]["id"])
            op_items[name] = UUID(item.json()["operation_id"])

        listing = await client.get(
            f"/api/agent/v1/navigation/{nav_id}/items",
            headers=_read_headers(token),
        )
        assert listing.status_code == 200, listing.text
        order_before = [UUID(rec["id"]) for rec in listing.json()]
        assert order_before == [item_ids["a"], item_ids["b"], item_ids["c"]]
        positions_before = _item_positions(listing)
        assert positions_before == {
            item_ids["a"]: (0, 1),
            item_ids["b"]: (1, 1),
            item_ids["c"]: (2, 1),
        }

        journal_before = await _completion_rows(database, workspace_id=ws_agent)
        move = await client.post(
            f"/api/agent/v1/navigation-items/{item_ids['c']}:move",
            json={
                "parent_id": None,
                "before_item_id": str(item_ids["a"]),
                "expected_row_version": 1,
            },
            headers=_request_headers(token, "pf-move-c"),
        )
        assert move.status_code == 200, move.text
        op_move = UUID(move.json()["operation_id"])

        listing_after = await client.get(
            f"/api/agent/v1/navigation/{nav_id}/items",
            headers=_read_headers(token),
        )
        assert listing_after.status_code == 200, listing_after.text
        order_after = [UUID(rec["id"]) for rec in listing_after.json()]
        positions_after = _item_positions(listing_after)
        # One operation moved c before a; the real compaction rewrote
        # the sibling rows too: three rows changed, one completion.
        assert order_after == [item_ids["c"], item_ids["a"], item_ids["b"]]
        assert positions_after == {
            item_ids["a"]: (1, 2),
            item_ids["b"]: (2, 2),
            item_ids["c"]: (0, 2),
        }
        changed = [
            item
            for item in item_ids
            if positions_after[item_ids[item]] != positions_before[item_ids[item]]
        ]
        assert len(changed) >= 2, positions_after

    journal_after = await _completion_rows(database, workspace_id=ws_agent)
    new_rows = [
        row
        for row in journal_after
        if str(row["operation_id"])
        not in {str(r["operation_id"]) for r in journal_before}
    ]
    assert len(new_rows) == 1, new_rows
    move_row = new_rows[0]
    assert move_row["disposition"] == "completed", move_row
    assert move_row["operation_id"] == op_move
    reservation = await _reservation(database, "agent_idempotency", op_move)
    assert reservation is not None
    # The primary-resource ID names the moved item; the journal holds
    # one completion per operation - never one per changed row.
    _assert_completion(
        move_row,
        family="agent",
        site_id=site_id,
        workspace_id=ws_agent,
        principal=None,
        capability_id=capability_id,
        key="pf-move-c",
        digest=reservation["request_digest"],
        resource_type="navigation_item",
        resource_id=item_ids["c"],
    )
    # Exact pending IDs: every completed write in this all-write
    # fixture is measured, not counted generically.
    pending = await _pending_operations(database, ws_agent)
    assert {str(op) for op in pending} == {
        str(op_nav),
        str(op_items["a"]),
        str(op_items["b"]),
        str(op_items["c"]),
        str(op_move),
    }
    assert {str(op) for op in pending} == {
        str(row["operation_id"]) for row in journal_after
    }


@pytest.mark.asyncio
async def test_theme_superseding_keeps_distinct_history(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """C3: superseding theme writes in a genuine AGENT workspace keep
    two distinct completed histories on the same theme resource with
    distinct request identities; both stay pending until human
    acceptance.  The first write is genuinely different from the
    actual initial default (ocean) so both writes are completed, not
    no-effect."""
    database = agent_site_database
    _token, seeded = await _seed(database)
    site_id = seeded["site_id"]
    human_id = seeded["delegator_id"]
    token, ws_agent, capability_id = await _seed_agent_workspace(
        database,
        site_id,
        human_id,
        ["site:read", "theme:read", "theme-tokens:write"],
        "pf theme superseding workspace",
    )

    async with _agent_client(database) as client:
        initial = await _agent_theme(client, token)
        # Actual product default (content_model/theme.py).
        assert initial["palette"]["preset"] == "ocean"
        first = await _agent_patch_theme(
            client,
            token,
            key="pf-theme-ember",
            preset="ember",
            expected_row_version=initial["row_version"],
        )
        assert first.status_code == 200, first.text
        op_first = UUID(first.json()["operation_id"])
        after_first = await _agent_theme(client, token)
        assert after_first["palette"]["preset"] == "ember"
        assert after_first["row_version"] == initial["row_version"] + 1
        second = await _agent_patch_theme(
            client,
            token,
            key="pf-theme-meadow",
            preset="meadow",
            expected_row_version=initial["row_version"] + 1,
        )
        assert second.status_code == 200, second.text
        op_second = UUID(second.json()["operation_id"])
        final = await _agent_theme(client, token)

    assert final["palette"]["preset"] == "meadow"
    assert final["row_version"] == initial["row_version"] + 2

    rows = await _completion_rows(database, workspace_id=ws_agent)
    assert len(rows) == 2, rows
    by_op = {str(row["operation_id"]): row for row in rows}
    assert set(by_op) == {str(op_first), str(op_second)}
    pairs = ((op_first, "pf-theme-ember"), (op_second, "pf-theme-meadow"))
    for operation, key in pairs:
        row = by_op[str(operation)]
        reservation = await _reservation(
            database, "agent_idempotency", row["operation_id"]
        )
        assert reservation is not None
        _assert_completion(
            row,
            family="agent",
            site_id=site_id,
            workspace_id=ws_agent,
            principal=None,
            capability_id=capability_id,
            key=key,
            digest=reservation["request_digest"],
            resource_type="theme",
            resource_id=UUID(initial["id"]),
        )
    first_row = by_op[str(op_first)]
    second_row = by_op[str(op_second)]
    assert first_row["resource_id"] == second_row["resource_id"]
    assert first_row["request_identity"] != second_row["request_identity"]
    pending = await _pending_operations(database, ws_agent)
    assert {str(op) for op in pending} == {str(op_first), str(op_second)}


@pytest.mark.asyncio
async def test_page_create_delete_net_zero_retains_history(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """C3: page create then delete in a genuine AGENT workspace is
    content net-zero (no canonical and no visible workspace page row)
    while both operations retain distinct honest completed histories
    with distinct request identities."""
    database = agent_site_database
    _token, seeded = await _seed(database)
    site_id = seeded["site_id"]
    human_id = seeded["delegator_id"]
    token, ws_agent, capability_id = await _seed_agent_workspace(
        database,
        site_id,
        human_id,
        ["site:read", "page:create", "page:read", "page:delete"],
        "pf net-zero workspace",
    )

    async with _agent_client(database) as client:
        created = await _create_page(client, token, key="pf-nz-create", slug="pf-nz")
        assert created.status_code == 201, created.text
        op_create = UUID(created.json()["operation_id"])
        page_id = UUID(created.json()["record"]["id"])
        deleted = await client.request(
            "DELETE",
            f"/api/agent/v1/pages/{page_id}",
            json={"expected_row_version": 1},
            headers=_request_headers(token, "pf-nz-delete"),
        )
        assert deleted.status_code == 200, deleted.text
        op_delete = UUID(deleted.json()["operation_id"])
        gone = await client.get(
            f"/api/agent/v1/pages/{page_id}", headers=_read_headers(token)
        )

    assert gone.status_code == 404, gone.text
    assert await _canonical_page_count(database, page_id) == 0

    rows = await _completion_rows(database, workspace_id=ws_agent)
    assert len(rows) == 2, rows
    by_op = {str(row["operation_id"]): row for row in rows}
    assert set(by_op) == {str(op_create), str(op_delete)}
    create_row = by_op[str(op_create)]
    delete_row = by_op[str(op_delete)]
    assert create_row["resource_id"] == delete_row["resource_id"] == page_id
    assert create_row["resource_type"] == "page"
    assert delete_row["resource_type"] == "page"
    assert create_row["request_identity"] != delete_row["request_identity"]
    assert create_row["disposition"] == "completed"
    assert delete_row["disposition"] == "completed"
    assert create_row["capability_id"] == capability_id
    assert delete_row["capability_id"] == capability_id
    pending = await _pending_operations(database, ws_agent)
    assert {str(op) for op in pending} == {str(op_create), str(op_delete)}


# ---------------------------------------------------------------------------
# P2: the deployed legacy 10-argument completion boundary.
# ---------------------------------------------------------------------------

# Full editorial-model scopes: the same qualified set the authority
# module uses for legitimately scoped agent content-model writes.
_AGENT_MODEL_SCOPES = [
    "site:read",
    "content-model:create",
    "field-definition:create",
    "content-model:read",
    "content-item:create",
    "content-item:read",
    "page:create",
    "page:read",
    "composition:read",
    "media:read",
    "component-structure:create",
]

_JOURNAL_TABLE = "audit.mutation_completion"
_JOURNAL_ROW_SQL = (
    "SELECT operation_id, family, site_id, workspace_id, capability_id, "
    "human_user_id, request_identity, request_digest, resource_type, "
    "resource_id, disposition, schema_version "
    f"FROM {_JOURNAL_TABLE} WHERE operation_id = $1"
)


@asynccontextmanager
async def _cow_session(
    pool: Any,
    *,
    session_id: UUID,
    operation_id: UUID,
    capability_id: UUID,
) -> Any:
    """A real public COW session carrying the request capability
    context, exactly as execute_agent_mutation opens it."""
    async with asyncpg_cow_session(
        pool, session_id=session_id, operation_id=operation_id
    ) as cow:
        await cow.native.execute(
            "SELECT set_config('app.capability_id', $1, true)",
            str(capability_id),
        )
        yield cow


def _legacy_digest(key: str) -> str:
    """A 64-hex request digest in the shape the envelopes require."""
    return hashlib.sha256(("083-11-a-p2:" + key).encode("utf-8")).hexdigest()


def _legacy_key_identity(key: str) -> str:
    """The journal's bounded opaque identity for a raw client key."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _legacy_response_body(operation_id: UUID, row: Any) -> str:
    """Runtime-shaped body: the executor sends the AgentMutationResponse
    JSON object (record + operation_id + action); the legacy definer
    requires a non-NULL jsonb object only."""
    record = {
        name: (str(value) if value is not None else None)
        for name, value in dict(row).items()
    }
    return json.dumps(
        {"action": None, "operation_id": str(operation_id), "record": record},
        sort_keys=True,
    )


@pytest.mark.asyncio
async def test_legacy_agent_completion_page_real_success_and_replay(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """P2: the legacy 10-argument completion of a real COW page write
    is durable (journal + legacy-shape audit + ledger) and replays per
    the existing boundary, with the direct duplicate refused."""
    database = agent_site_database
    _token, seeded = await _seed(database)
    site_id = seeded["site_id"]
    delegator_id = seeded["delegator_id"]
    _token_agent, workspace_id, capability_id = await _seed_agent_workspace(
        database,
        site_id,
        delegator_id,
        _AGENT_MODEL_SCOPES,
        "pf legacy completion workspace",
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    operation_id = uuid4()
    key = "legacy-p2-page-083-11-a"
    digest = _legacy_digest(key)
    page_id: UUID | None = None
    try:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            revision_before = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                site_id,
            )
            page_base_before = await owner.fetchval(
                "SELECT count(*) FROM content.page_base WHERE site_id = $1",
                site_id,
            )
        # One real runtime-shaped transaction: begin, COW page write,
        # and the LEGACY 10-argument completion in the same COW session.
        async with _cow_session(
            agent_pool,
            session_id=workspace_id,
            operation_id=operation_id,
            capability_id=capability_id,
        ) as cow:
            started = await cow.native.fetchrow(
                BEGIN_IDEMPOTENCY_SQL,
                capability_id,
                workspace_id,
                key,
                digest,
                operation_id,
            )
            assert started[0] == "STARTED"
            created = await cow.native.fetchrow(
                AGENT_PAGE_CREATE_SQL,
                site_id,
                "legacy-p2-page",
                "Legacy P2 Page",
                "DRAFT",
                "en-US",
                None,
                None,
            )
            assert created is not None
            page_id = created[0]
            body = _legacy_response_body(operation_id, created)
            await cow.native.fetchrow(
                COMPLETE_IDEMPOTENCY_SQL,
                capability_id,
                workspace_id,
                key,
                digest,
                operation_id,
                201,
                body,
                "page",
                page_id,
                site_id,
            )
        # The public COW session committed on scope exit.
        assert page_id is not None
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            journal = await owner.fetchrow(_JOURNAL_ROW_SQL, operation_id)
            assert journal is not None, "legacy completion must be journaled"
            assert journal["family"] == "agent"
            assert journal["site_id"] == site_id
            assert journal["workspace_id"] == workspace_id
            assert journal["capability_id"] == capability_id
            assert journal["human_user_id"] is None
            assert journal["request_identity"] == _legacy_key_identity(key)
            assert journal["request_digest"] == digest
            assert journal["resource_type"] == "page"
            assert journal["resource_id"] == page_id
            assert journal["disposition"] == "completed"
            assert journal["schema_version"] == "mutation-completion/v1"
            assert await owner.fetchval(f"SELECT count(*) FROM {_JOURNAL_TABLE}") == 1
            audit = await owner.fetchrow(
                "SELECT capability_id, workspace_id, site_id, resource_type, "
                "resource_id, request_digest, response_status, action, "
                "http_method, quota_kind "
                "FROM audit.agent_mutation WHERE operation_id = $1",
                operation_id,
            )
            assert audit is not None
            assert audit["capability_id"] == capability_id
            assert audit["workspace_id"] == workspace_id
            assert audit["site_id"] == site_id
            assert audit["resource_type"] == "page"
            assert audit["resource_id"] == page_id
            assert audit["request_digest"] == digest
            assert audit["response_status"] == 201
            # The legacy 10-arg INSERT omits the semantic columns: the
            # 041_001 default fills action; http_method/quota_kind NULL.
            assert audit["action"] == "LEGACY_MUTATION"
            assert audit["http_method"] is None and audit["quota_kind"] is None
            assert (
                await owner.fetchval("SELECT count(*) FROM audit.agent_mutation") == 1
            )
            ledger = await owner.fetchrow(
                "SELECT operation_id, workspace_id, request_digest, "
                "status_code, resource_type, resource_id, completed_at "
                "FROM control.agent_idempotency "
                "WHERE capability_id = $1 AND idempotency_key = $2",
                capability_id,
                key,
            )
            assert ledger is not None
            assert ledger["operation_id"] == operation_id
            assert ledger["workspace_id"] == workspace_id
            assert ledger["request_digest"] == digest
            assert ledger["status_code"] == 201
            assert ledger["resource_type"] == "page"
            assert ledger["resource_id"] == page_id
            assert ledger["completed_at"] is not None
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.page_base WHERE site_id = $1",
                    site_id,
                )
                == page_base_before
            ), "canonical page base unchanged: the write stays in the overlay"
            assert (
                await owner.fetchval(
                    "SELECT canonical_revision FROM control.site WHERE id = $1",
                    site_id,
                )
                == revision_before
            )
        # Public pending: exactly the one completed-pending operation id.
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            pending = await reviewer.operations(workspace_id, schema="content")
        assert pending == [operation_id]

        # Replay: begin on the same identity returns REPLAY with the
        # stored completed response (the existing runtime path).
        async with _cow_session(
            agent_pool,
            session_id=workspace_id,
            operation_id=operation_id,
            capability_id=capability_id,
        ) as cow:
            replay = await cow.native.fetchrow(
                BEGIN_IDEMPOTENCY_SQL,
                capability_id,
                workspace_id,
                key,
                digest,
                operation_id,
            )
        assert replay[0] == "REPLAY"
        assert replay[1] == operation_id
        assert replay[2] == 201
        replay_body = replay[3]
        if isinstance(replay_body, str):
            replay_body = json.loads(replay_body)
        assert replay_body["operation_id"] == str(operation_id)
        assert replay_body["record"]["id"] == str(page_id)

        # A direct duplicate legacy completion of the already-completed
        # reservation is refused; the transaction rolls back.
        with pytest.raises(asyncpg.PostgresError) as excinfo:
            async with _cow_session(
                agent_pool,
                session_id=workspace_id,
                operation_id=operation_id,
                capability_id=capability_id,
            ) as cow:
                await cow.native.fetchrow(
                    COMPLETE_IDEMPOTENCY_SQL,
                    capability_id,
                    workspace_id,
                    key,
                    digest,
                    operation_id,
                    201,
                    body,
                    "page",
                    page_id,
                    site_id,
                )
        assert excinfo.value.sqlstate == "P0002"
        assert "IDEMPOTENCY_RESERVATION_NOT_FOUND" in str(excinfo.value)

        # Durable state: still exactly one journal identity, one family
        # audit row, one public pending operation.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert await owner.fetchval(f"SELECT count(*) FROM {_JOURNAL_TABLE}") == 1
            assert (
                await owner.fetchval("SELECT count(*) FROM audit.agent_mutation") == 1
            )
            assert await owner.fetchrow(_JOURNAL_ROW_SQL, operation_id) is not None
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            assert await reviewer.operations(workspace_id, schema="content") == [
                operation_id
            ]
    finally:
        await agent_pool.close()
        await reviewer_pool.close()


@pytest.mark.asyncio
async def test_legacy_agent_completion_forbids_content_model_resource(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """P2: a content-model resource is not a legacy resource; the
    whole real transaction (begin + COW write + completion) rolls
    back through the public COW scope exit."""
    database = agent_site_database
    _token, seeded = await _seed(database)
    site_id = seeded["site_id"]
    delegator_id = seeded["delegator_id"]
    _token_agent, workspace_id, capability_id = await _seed_agent_workspace(
        database,
        site_id,
        delegator_id,
        _AGENT_MODEL_SCOPES,
        "pf legacy forbidden workspace",
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    operation_id = uuid4()
    key = "legacy-p2-forbidden-083-11-a"
    digest = _legacy_digest(key)
    try:
        with pytest.raises(asyncpg.PostgresError) as excinfo:
            async with _cow_session(
                agent_pool,
                session_id=workspace_id,
                operation_id=operation_id,
                capability_id=capability_id,
            ) as cow:
                started = await cow.native.fetchrow(
                    BEGIN_IDEMPOTENCY_SQL,
                    capability_id,
                    workspace_id,
                    key,
                    digest,
                    operation_id,
                )
                assert started[0] == "STARTED"
                created = await cow.native.fetchrow(
                    AGENT_PAGE_CREATE_SQL,
                    site_id,
                    "legacy-p2-forbidden",
                    "Legacy P2 Forbidden",
                    "DRAFT",
                    "en-US",
                    None,
                    None,
                )
                assert created is not None
                await cow.native.fetchrow(
                    COMPLETE_IDEMPOTENCY_SQL,
                    capability_id,
                    workspace_id,
                    key,
                    digest,
                    operation_id,
                    201,
                    _legacy_response_body(operation_id, created),
                    "content_item",
                    created[0],
                    site_id,
                )
        assert excinfo.value.sqlstate == "P0001"
        assert "INVALID_IDEMPOTENCY_COMPLETION" in str(excinfo.value)
        # Rolled back: no journal, no family audit, no reservation, no
        # pending COW operation.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    f"SELECT count(*) FROM {_JOURNAL_TABLE} WHERE operation_id = $1",
                    operation_id,
                )
                == 0
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM audit.agent_mutation WHERE operation_id = $1",
                    operation_id,
                )
                == 0
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.agent_idempotency "
                    "WHERE capability_id = $1 AND idempotency_key = $2",
                    capability_id,
                    key,
                )
                == 0
            )
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            assert await reviewer.operations(workspace_id, schema="content") == []
    finally:
        await agent_pool.close()
        await reviewer_pool.close()
