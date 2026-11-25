"""083-13-a: bounded heading-props row effect pilot (migration 080_001).

Real runtime evidence for the actual mutation boundary of a successful
changed heading-props write through both trusted editorial surfaces:

- the Agent HTTP path (062 ``content.slaif_agent_component_update``);
- the Human-on-Agent Editor HTTP path (060
  ``content.slaif_composition_node_update``).

Every case runs on the owned fixture through the real HTTP envelopes,
real COW sessions, real reservations/journals and (where the canonical
row moves) the real freeze + human acceptance job lifecycle.  Public
surfaces only: the canonical content projection (view read without a
COW session GUC), the real HTTP records, the typed public conflict and
operation inspection (``CowReviewer``) and the product-owned
journals/control state.  No private foundation storage reads and no
owner writes to canonical rows anywhere in this module.

Pilot boundary (explicit, preserved by test):
- only ``Heading`` ``props`` writes through the two definers record a
  fact; every other component type and mutation family keeps the
  pre-080 behavior and records nothing;
- the Editor write contract is observed, not hardened (no version
  predicate): a stale Editor write is NOT refused by the boundary, and
  its fact still captures the exact same-statement DML image;
- the Agent row-version guard is not by itself proof of all old-row
  bytes (a concurrent committed change between the pre-read and the
  UPDATE is rejected, but the guard proves the version, not the full
  pre-image); the exact pre-image comes from the same-statement
  ``prior`` capture;
- historical heading writes (pre-080) are unknown, never backfilled:
  an old workspace without facts proves nothing about its history.
"""

from __future__ import annotations

import importlib
import json
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import UUID

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
from slaif_agent_site.agent_state.foundation import asyncpg_cow_session
from slaif_agent_site.bootstrap.service import (
    BootstrapStateError,
    downgrade,
)
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration
from slaif_agent_site.editor_api.app import create_app as create_editor_app
from slaif_agent_site.editor_api.config import (
    EditorDatabaseMode,
    EditorDatabaseSettings,
)
from slaif_agent_site.editor_api.database import EditorDatabase
from slaif_agent_site.review_worker.accept_job import MediaBoundary
from slaif_agent_site.review_worker.discard_job import run_discard_job
from sqlalchemy.exc import DBAPIError
from test_freeze_review_snapshot import (
    _accept_claim_run,
    _create_workspace,
    _freeze_claim_run,
    _public_conflicts,
    _public_operations,
    _worker_pool,
)
from test_human_agent_editor_workspace import _create_agent_workspace
from test_real_human_accept import (
    _AGGON2,
    _media_settings,
    _seed_site,
)
from test_real_human_discard import (
    _claim_discard,
    _enqueue_discard,
    _worker_settings,
)

_SCHEMA_VERSION = "heading-row-effect/v1"
_SCOPES = [
    "site:read",
    "page:read",
    "composition:read",
    "component-structure:create",
    "component-content-props:write",
    "component-variant:write",
]
_DENY_ROLES = (
    "slaif_control",
    "slaif_editor_runtime",
    "slaif_agent_runtime",
    "slaif_reviewer",
    "slaif_review_worker",
    "slaif_public_reader",
    "slaif_preview_reader",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
)


# ---------------------------------------------------------------------------
# shared helpers (public surfaces only)
# ---------------------------------------------------------------------------


async def _new_capability(owner: Any, workspace_id: UUID) -> str:
    """One fixture capability (trusted rows) with the real bearer token."""

    token, public_id, digest = generate_capability_token()
    await owner.execute(
        "INSERT INTO control.capability (workspace_id, public_id, secret_digest,"
        " scopes, expires_at) VALUES ($1,$2,$3,$4::jsonb,"
        " now() + interval '30 minutes')",
        workspace_id,
        public_id,
        digest,
        json.dumps(_SCOPES),
    )
    return token


async def _canonical_projection(
    database: AgentSiteDatabase, component_id: UUID
) -> dict[str, Any]:
    """The public canonical content projection (no COW session GUC)."""

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        row = await owner.fetchrow(
            "SELECT id, site_id, page_id, component_type, slot_key, order_key,"
            " props, row_version, updated_at"
            " FROM content.page_composition WHERE id = $1",
            component_id,
        )
    assert row is not None
    result = dict(row)
    if isinstance(result.get("props"), str):
        result["props"] = json.loads(result["props"])
    return result


async def _heading_facts(
    database: AgentSiteDatabase,
    component_id: UUID,
    workspace_id: UUID | None = None,
) -> list[dict[str, Any]]:
    """The product-owned facts (owner read, fixture verification)."""

    query = (
        "SELECT operation_id, schema_version, family, mutation_kind,"
        " site_id, workspace_id, component_id, row_version_before,"
        " row_version_after, props_before, props_after, capability_id,"
        " human_user_id, occurred_at"
        " FROM audit.heading_row_effect WHERE component_id = $1"
    )
    args: list[Any] = [component_id]
    if workspace_id is not None:
        query += " AND workspace_id = $2"
        args.append(workspace_id)
    query += " ORDER BY row_version_before"
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        rows = await owner.fetch(query, *args)
    result: list[dict[str, Any]] = []
    for row in rows:
        fact = dict(row)
        for column in ("props_before", "props_after"):
            if isinstance(fact[column], str):
                fact[column] = json.loads(fact[column])
        result.append(fact)
    return result


async def _journal_rows(
    database: AgentSiteDatabase, *operation_ids: UUID
) -> list[dict[str, Any]]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        rows = await owner.fetch(
            "SELECT operation_id, family, resource_type, resource_id,"
            " disposition FROM audit.mutation_completion"
            " WHERE operation_id = ANY($1::uuid[]) ORDER BY operation_id",
            list(operation_ids),
        )
    return [dict(row) for row in rows]


def _agent_settings(database: AgentSiteDatabase) -> AgentDatabaseSettings:
    login, password = database.credentials["slaif_agent_runtime"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return AgentDatabaseSettings(
        mode=AgentDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
            f"{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-083-13a-heading-agent",
    )


def _control_settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
    login, password = database.credentials["slaif_control"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
            f"{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-083-13a-heading-control",
    )


def _editor_db_settings(database: AgentSiteDatabase) -> EditorDatabaseSettings:
    login, password = database.credentials["slaif_editor_runtime"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return EditorDatabaseSettings(
        mode=EditorDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
            f"{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-083-13a-heading-editor",
    )


async def _agent_patch(
    database: AgentSiteDatabase,
    token: str,
    heading: UUID,
    props: dict[str, Any],
    *,
    expected_row_version: int,
    idempotency_key: str,
) -> httpx.Response:
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://agent.test",
            timeout=60,
        ) as client:
            return await client.patch(
                f"/api/agent/v1/components/{heading}",
                json={
                    "props": props,
                    "expected_row_version": expected_row_version,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": idempotency_key,
                },
            )


@pytest.mark.asyncio
async def test_agent_heading_patches_record_exact_row_effects(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Agent path: two same-resource writes keep BOTH exact transitions."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    ws1: UUID = ids["workspace_id"]
    heading: UUID = ids["heading_id"]
    del site_id, delegator_id

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        token = await _new_capability(owner, ws1)
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id = $1"
            " ORDER BY created_at DESC LIMIT 1",
            ws1,
        )

    A = await _canonical_projection(database, heading)
    assert A["props"] == {"level": 1, "text": "Accept"}
    assert A["row_version"] == 1

    r1 = await _agent_patch(
        database,
        token,
        heading,
        {"level": 2, "text": "H1"},
        expected_row_version=1,
        idempotency_key="13a-agent-1",
    )
    assert r1.status_code == 200, r1.text
    op1 = UUID(str(r1.json()["operation_id"]))

    r2 = await _agent_patch(
        database,
        token,
        heading,
        {"level": 2, "text": "H2"},
        expected_row_version=2,
        idempotency_key="13a-agent-2",
    )
    assert r2.status_code == 200, r2.text
    op2 = UUID(str(r2.json()["operation_id"]))
    assert op2 != op1

    # Both transitions retained, in order, with the exact DML images.
    facts = await _heading_facts(database, heading, ws1)
    assert len(facts) == 2
    f1, f2 = facts
    for fact in facts:
        assert fact["schema_version"] == _SCHEMA_VERSION
        assert fact["family"] == "agent"
        assert fact["mutation_kind"] == "heading_props"
        assert fact["site_id"] == ids["site_id"]
        assert fact["workspace_id"] == ws1
        assert fact["component_id"] == heading
        assert fact["capability_id"] == capability_id
        assert fact["human_user_id"] is None
        assert fact["row_version_after"] == fact["row_version_before"] + 1
    assert f1["operation_id"] == op1
    assert (f1["row_version_before"], f1["row_version_after"]) == (1, 2)
    assert f1["props_before"] == A["props"]
    assert f1["props_after"] == {"level": 2, "text": "H1"}
    assert f2["operation_id"] == op2
    assert (f2["row_version_before"], f2["row_version_after"]) == (2, 3)
    assert f2["props_before"] == f1["props_after"]
    assert f2["props_after"] == {"level": 2, "text": "H2"}

    # Same-transaction trusted completion binding: every fact operation
    # journaled exactly once, disposition completed, same resource.
    journal = await _journal_rows(database, op1, op2)
    assert len(journal) == 2
    by_op = {row["operation_id"]: row for row in journal}
    assert set(by_op) == {op1, op2}
    for row in journal:
        assert row["family"] == "agent"
        assert row["resource_type"] == "composition_node"
        assert row["resource_id"] == heading
        assert row["disposition"] == "completed"

    # The effective row shows the final value; the canonical row still
    # shows the pre-workspace value (no publication happened).
    view = await _canonical_projection(database, heading)
    assert view["props"] == A["props"]


@pytest.mark.asyncio
async def test_editor_human_on_agent_heading_patch_records_and_replay_is_inert(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Human-on-Agent Editor path: human principal from the real
    reservation, wire contract preserved, replay adds no second fact."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    heading: UUID = ids["heading_id"]
    page_id: UUID = ids["page_id"]

    # The seeded workspace is a HUMAN workspace; the Human-on-Agent
    # editor path requires a real AGENT workspace (product trusted
    # create).  role_pool is max_size=1: never hold a connection while
    # the helper acquires the same pool.
    owner_pool = await database.role_pool("slaif_owner")
    ws_agent = await _create_agent_workspace(
        owner_pool,
        site_id=site_id,
        delegator_id=delegator_id,
        title="13a heading effects agent workspace",
    )
    await owner_pool.close()

    A = await _canonical_projection(database, heading)

    control = ControlDatabase(_control_settings(database))
    editor = EditorDatabase(_editor_db_settings(database))
    app = create_editor_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST),
        database=control,
        editor_database=editor,
    )
    try:
        await control.start()
        await editor.start()
        session = await control.human_session_service().create(delegator_id)
        token = session.token.get_secret_value()
        csrf = session.csrf_token.get_secret_value()

        def _headers(extra: dict[str, str] | None = None) -> dict[str, str]:
            base = {
                "cookie": f"slaif_session={token}; slaif_csrf={csrf}",
                "x-csrf-token": csrf,
                "x-editor-workspace": str(ws_agent),
            }
            return {**base, **(extra or {})}

        comp_path = f"/api/editor/v1/sites/{site_id}/pages/{page_id}/composition"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://editor.test",
            timeout=60,
        ) as client:
            r1 = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"props": {"level": 3, "text": "E1"}},
                headers=_headers({"Idempotency-Key": "13a-editor-1"}),
            )
            assert r1.status_code == 200, r1.text
            rec1 = r1.json()
            # Pre-080 wire contract preserved: the Editor record omits
            # row_version (maps to the fixed 1), never the actual row.
            assert rec1["row_version"] == 1
            assert rec1["props"] == {"level": 3, "text": "E1"}

            # Replay: the stored body is returned; the definer never
            # re-runs, so no second fact.
            r1r = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"props": {"level": 3, "text": "E1"}},
                headers=_headers({"Idempotency-Key": "13a-editor-1"}),
            )
            assert r1r.status_code == 200
            assert r1r.json() == rec1
    finally:
        await editor.stop()
        await control.stop()

    facts = await _heading_facts(database, heading, ws_agent)
    assert len(facts) == 1
    fact = facts[0]
    assert fact["schema_version"] == _SCHEMA_VERSION
    assert fact["family"] == "human_editor"
    assert fact["mutation_kind"] == "heading_props"
    assert fact["site_id"] == site_id
    assert fact["workspace_id"] == ws_agent
    assert fact["component_id"] == heading
    assert fact["capability_id"] is None
    # The human principal comes from the actual in-progress reservation
    # row (the session's delegator), never from caller-supplied values.
    assert fact["human_user_id"] == delegator_id
    assert (fact["row_version_before"], fact["row_version_after"]) == (1, 2)
    assert fact["props_before"] == A["props"]
    assert fact["props_after"] == {"level": 3, "text": "E1"}

    # Same-transaction trusted completion for the editor family.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        journal_op = await owner.fetchval(
            "SELECT operation_id FROM audit.mutation_completion"
            " WHERE family = 'human_editor'"
            " AND resource_id = $1",
            heading,
        )
    assert journal_op is not None
    assert UUID(str(journal_op)) == fact["operation_id"]


@pytest.mark.asyncio
async def test_no_effect_and_late_refusal_leave_no_fact(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Genuine no-effect and genuine late refusal: rollback/no-effect
    semantics leave NO effect fact; the corrected retry records once."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    ws1: UUID = ids["workspace_id"]
    heading: UUID = ids["heading_id"]

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        token = await _new_capability(owner, ws1)

    # 1. HTTP-level no-effect: identical props complete with the
    #    explicit trusted no-effect disposition and NO fact.
    r0 = await _agent_patch(
        database,
        token,
        heading,
        {"level": 1, "text": "Accept"},
        expected_row_version=1,
        idempotency_key="13a-noeffect",
    )
    assert r0.status_code == 200, r0.text
    rec0 = r0.json()["record"]
    assert rec0["props"] == {"level": 1, "text": "Accept"}
    assert rec0["row_version"] == 1
    no_effect_ops = await _journal_rows_for_family(database, "agent", heading)
    assert [row["disposition"] for row in no_effect_ops] == ["no_effect"]
    assert await _heading_facts(database, heading, ws1) == []

    # 2. A real first write, then a late request at the STALE version:
    #    refused, rolled back, no fact and no completion for it.
    r1 = await _agent_patch(
        database,
        token,
        heading,
        {"level": 2, "text": "Real1"},
        expected_row_version=1,
        idempotency_key="13a-late-1",
    )
    assert r1.status_code == 200, r1.text
    op1 = UUID(str(r1.json()["operation_id"]))

    r_stale = await _agent_patch(
        database,
        token,
        heading,
        {"level": 2, "text": "Late"},
        expected_row_version=1,
        idempotency_key="13a-late-2",
    )
    assert r_stale.status_code == 409, r_stale.text

    # The stale request left no durable trace: its reservation rolled
    # back with the refused mutation, it journaled nothing, and the
    # effective row is untouched.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        stale_reservation = await owner.fetchval(
            "SELECT count(*) FROM control.agent_idempotency WHERE idempotency_key = $1",
            "13a-late-2",
        )
    assert stale_reservation == 0
    facts = await _heading_facts(database, heading, ws1)
    assert [f["operation_id"] for f in facts] == [op1]
    assert facts[0]["props_after"] == {"level": 2, "text": "Real1"}
    journal = await _journal_rows(database, op1)
    assert [row["disposition"] for row in journal] == ["completed"]
    view = await _canonical_projection(database, heading)
    assert view["props"] == {"level": 1, "text": "Accept"}

    # 3. The corrected retry at the actual version records exactly once.
    r2 = await _agent_patch(
        database,
        token,
        heading,
        {"level": 2, "text": "Real2"},
        expected_row_version=2,
        idempotency_key="13a-late-3",
    )
    assert r2.status_code == 200, r2.text
    op2 = UUID(str(r2.json()["operation_id"]))
    facts = await _heading_facts(database, heading, ws1)
    assert [f["operation_id"] for f in facts] == [op1, op2]
    assert facts[1]["props_before"] == {"level": 2, "text": "Real1"}
    assert facts[1]["props_after"] == {"level": 2, "text": "Real2"}


async def _journal_rows_for_family(
    database: AgentSiteDatabase, family: str, resource_id: UUID
) -> list[dict[str, Any]]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        rows = await owner.fetch(
            "SELECT operation_id, family, resource_id, disposition"
            " FROM audit.mutation_completion"
            " WHERE family = $1 AND resource_id = $2"
            " ORDER BY operation_id",
            family,
            resource_id,
        )
    return [dict(row) for row in rows]


@pytest.mark.asyncio
async def test_first_touch_conflict_control_case(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Item 3 control: both same-site first touches committed before the
    winner is accepted; the four distinct sources are each observed
    through a supported read path, the typed public conflict is exact,
    and both same-resource transitions keep their facts."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    ws1: UUID = ids["workspace_id"]
    heading: UUID = ids["heading_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        A = await _canonical_projection(database, heading)
        assert A["props"] == {"level": 1, "text": "Accept"}
        assert A["row_version"] == 1

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            token1 = await _new_capability(owner, ws1)
            ws2, _cap2 = await _create_workspace(
                owner, site_id, delegator_id, "13a conflict W2"
            )
            token2 = await _new_capability(owner, ws2)

        # W1 first touch (real HTTP), then W2 first touch (real HTTP) -
        # BOTH committed before the winner is accepted.
        r1 = await _agent_patch(
            database,
            token1,
            heading,
            {"level": 2, "text": "W1v1"},
            expected_row_version=1,
            idempotency_key="13a-conf-w1",
        )
        assert r1.status_code == 200, r1.text
        op1 = UUID(str(r1.json()["operation_id"]))
        r2 = await _agent_patch(
            database,
            token2,
            heading,
            {"level": 1, "text": "W2v2"},
            expected_row_version=1,
            idempotency_key="13a-conf-w2",
        )
        assert r2.status_code == 200, r2.text

        # Real W2 freeze + human accept publishes B.
        result2, _ = await _freeze_claim_run(
            database,
            workspace_id=ws2,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="13a-conf-w2f",
        )
        assert result2.status == "SUCCEEDED", result2.error
        result2a, _ = await _accept_claim_run(
            database,
            workspace_id=ws2,
            delegator_id=delegator_id,
            pool=pool,
            claimant="13a-conf-w2a",
            boundary=boundary,
        )
        assert result2a.status == "SUCCEEDED", result2a.error

        B = await _canonical_projection(database, heading)
        assert B["props"] == {"level": 1, "text": "W2v2"}
        assert B["row_version"] == 2

        conflicts_mid = await _public_conflicts(database, ws1)
        assert len(conflicts_mid) == 1
        assert conflicts_mid[0]["conflict_kind"] == "BASE_ROW_CHANGED"
        assert conflicts_mid[0]["table_name"] == "page_composition"
        assert conflicts_mid[0]["primary_key"] == {"id": str(heading)}
        assert UUID(str(conflicts_mid[0]["operation_id"])) == op1

        # W1's second edit at the actual request version (2).
        r1b = await _agent_patch(
            database,
            token1,
            heading,
            {"level": 2, "text": "W1v2"},
            expected_row_version=2,
            idempotency_key="13a-conf-w1b",
        )
        assert r1b.status_code == 200, r1b.text
        op2 = UUID(str(r1b.json()["operation_id"]))

        # Four distinct sources, each observed through a supported
        # read path: canonical at W1's first touch (A), W1's earlier
        # value (its effective row), W2's published value (canonical
        # after the real acceptance) and W1's actual new value.
        w1_ops = await _public_operations(database, ws1)
        assert op1 in w1_ops and op2 in w1_ops
        sources = {
            "canonical_at_first_touch": A["props"],
            "w1_earlier_value": {"level": 2, "text": "W1v1"},
            "w2_published_value": B["props"],
            "w1_actual_new_value": {"level": 2, "text": "W1v2"},
        }
        assert len({json.dumps(v, sort_keys=True) for v in sources.values()}) == 4

        # Both W1 transitions keep their exact facts.  The second
        # write's DML pre-image is W1's own effective COW row at write
        # time - the value W1 wrote earlier - neither the session's
        # first-touch baseline A nor the W2 value W2 published to
        # canonical: the mutation applies to W1's own copy of the row,
        # and the same-statement prior capture records exactly that
        # pre-write row.  The divergence from the published row is
        # observed through the typed public conflict above
        # (BASE_ROW_CHANGED); the baseline bookkeeping is separate
        # foundation state.  The numeric row versions agree because
        # both lineages anchor to the same first-touch baseline rv 1
        # with one write applied each.
        facts = await _heading_facts(database, heading, ws1)
        assert [f["operation_id"] for f in facts] == [op1, op2]
        assert facts[0]["props_before"] == A["props"]
        assert facts[0]["props_after"] == {"level": 2, "text": "W1v1"}
        assert facts[1]["props_before"] == {"level": 2, "text": "W1v1"}
        assert facts[1]["row_version_before"] == 2
        assert facts[1]["props_after"] == {"level": 2, "text": "W1v2"}
        assert facts[1]["row_version_after"] == 3
    finally:
        await pool.close()


async def _structural_locks(cow: Any, workspace_id: UUID, site_id: UUID) -> None:
    """The deployed 050 structural-lock body's exact statements, same
    keys and order (the agent role cannot EXECUTE the definer wrapper
    itself, so the replay issues the identical lock statements)."""

    await cow.native.execute(
        "SELECT pg_advisory_xact_lock_shared(hashtextextended($1::text, 280))",
        str(workspace_id),
    )
    await cow.native.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended("
        "$1::text || chr(58) || $2::text || chr(58) || "
        "'page-structure', 994))",
        str(workspace_id),
        str(site_id),
    )


@pytest.mark.asyncio
async def test_first_write_race_at_statement_boundary(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Item 3 separate race: the loser is paused exactly between the
    definer's pre-read and its UPDATE.  A live HTTP request cannot
    pause inside its definer, so the loser is reproduced by faithfully
    replaying the deployed definer's own statements (062
    ``slaif_agent_component_update``) as the real ``slaif_agent_runtime``
    role in real COW sessions: the exact structural lock statements,
    the exact pre-read, then the exact version-guarded UPDATE - with
    the sibling's real first touch plus REAL freeze + human acceptance
    interleaved in between.  The refused attempts prove no effect and
    no false facts; the corrected fresh write records exactly once,
    with its pre-image at the post-publish base; a third real publish
    then yields the typed conflict attributed to that fresh operation.
    """

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    ws1: UUID = ids["workspace_id"]
    heading: UUID = ids["heading_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        A = await _canonical_projection(database, heading)
        assert A["props"] == {"level": 1, "text": "Accept"}
        assert A["row_version"] == 1

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            token1 = await _new_capability(owner, ws1)
            ws2, _cap2 = await _create_workspace(
                owner, site_id, delegator_id, "13a race W2"
            )
            token2 = await _new_capability(owner, ws2)
            ws3, _cap3 = await _create_workspace(
                owner, site_id, delegator_id, "13a race W3"
            )
            token3 = await _new_capability(owner, ws3)

        # --- PAUSE POINT: W1's pre-read image at the definer boundary.
        op_pre = uuid.uuid4()
        agent_pool = await database.role_pool("slaif_agent_runtime")
        try:
            async with asyncpg_cow_session(
                agent_pool, session_id=ws1, operation_id=op_pre
            ) as cow:
                await _structural_locks(cow, ws1, site_id)
                pre_row = dict(
                    await cow.native.fetchrow(
                        "SELECT c.* FROM content.page_composition c"
                        " WHERE c.id = $1 AND c.site_id = $2",
                        heading,
                        site_id,
                    )
                )
            assert pre_row is not None
            if isinstance(pre_row.get("props"), str):
                pre_row["props"] = json.loads(pre_row["props"])
            assert pre_row["props"] == A["props"]
            assert pre_row["row_version"] == 1

            # --- PAUSE: the sibling's real first touch, then a REAL
            # freeze + human acceptance moves the canonical row.
            r2 = await _agent_patch(
                database,
                token2,
                heading,
                {"level": 1, "text": "W2v2"},
                expected_row_version=1,
                idempotency_key="13a-race-w2",
            )
            assert r2.status_code == 200, r2.text
            result2, _ = await _freeze_claim_run(
                database,
                workspace_id=ws2,
                site_id=site_id,
                delegator_id=delegator_id,
                pool=pool,
                claimant="13a-race-w2f",
            )
            assert result2.status == "SUCCEEDED", result2.error
            result2a, _ = await _accept_claim_run(
                database,
                workspace_id=ws2,
                delegator_id=delegator_id,
                pool=pool,
                claimant="13a-race-w2a",
                boundary=boundary,
            )
            assert result2a.status == "SUCCEEDED", result2a.error

            B = await _canonical_projection(database, heading)
            assert B["props"] == {"level": 1, "text": "W2v2"}
            assert B["row_version"] == 2

            # --- RESUME: W1's exact UPDATE statement with the STALE
            # version (1) from its pre-pause pre-read matches no row.
            stale_props = json.dumps({"level": 2, "text": "W1stale"}, sort_keys=True)
            op_stale = uuid.uuid4()
            async with asyncpg_cow_session(
                agent_pool, session_id=ws1, operation_id=op_stale
            ) as cow:
                await _structural_locks(cow, ws1, site_id)
                rc = await cow.native.execute(
                    "UPDATE content.page_composition c"
                    " SET props = $3::jsonb, row_version = c.row_version + 1,"
                    " updated_at = now()"
                    " WHERE c.id = $1 AND c.site_id = $2 AND c.row_version = 1",
                    heading,
                    site_id,
                    stale_props,
                )
            assert rc == "UPDATE 0", rc

            # The actual deployed definer refuses the same stale
            # expectation.
            op_def = uuid.uuid4()
            with pytest.raises(asyncpg.PostgresError) as stale_exc:
                async with asyncpg_cow_session(
                    agent_pool, session_id=ws1, operation_id=op_def
                ) as cow:
                    await cow.native.fetchrow(
                        "SELECT * FROM content.slaif_agent_component_update"
                        "($1, $2, $3::jsonb, 1)",
                        site_id,
                        heading,
                        stale_props,
                    )
            assert getattr(stale_exc.value, "sqlstate", None) == "P0004"
            assert "ROW_VERSION_MISMATCH" in str(
                getattr(stale_exc.value, "message", "")
            )

            # No effect, no false facts: W1's public view is the
            # canonical B (no overlay row), the public conflict set is
            # empty, neither refused operation journaled anything, and
            # no effect fact exists for them.
            async with asyncpg_cow_session(
                agent_pool, session_id=ws1, operation_id=uuid.uuid4()
            ) as cow:
                view = dict(
                    await cow.native.fetchrow(
                        "SELECT props, row_version"
                        " FROM content.page_composition WHERE id = $1",
                        heading,
                    )
                )
            if isinstance(view.get("props"), str):
                view["props"] = json.loads(view["props"])
            assert view["props"] == B["props"]
            assert view["row_version"] == 2
            assert await _public_conflicts(database, ws1) == []
            assert await _journal_rows(database, op_stale, op_def) == []
            assert await _heading_facts(database, heading, ws1) == []
        finally:
            await agent_pool.close()

        # The corrected fresh first write lands (expected version 2).
        r1 = await _agent_patch(
            database,
            token1,
            heading,
            {"level": 2, "text": "W1v2"},
            expected_row_version=2,
            idempotency_key="13a-race-w1",
        )
        assert r1.status_code == 200, r1.text
        op_fresh = UUID(str(r1.json()["operation_id"]))
        assert await _public_conflicts(database, ws1) == []
        facts = await _heading_facts(database, heading, ws1)
        assert len(facts) == 1
        # Its pre-image is the post-publish base B: the baseline the
        # session first touches now is B, and the exact DML pre-image
        # is B as well.
        assert facts[0]["props_before"] == B["props"]
        assert facts[0]["props_after"] == {"level": 2, "text": "W1v2"}

        # A third real publish moves the base past W1's first-touch
        # baseline: the typed conflict names the FRESH write's
        # operation, proving the refused attempts captured nothing.
        r3 = await _agent_patch(
            database,
            token3,
            heading,
            {"level": 1, "text": "W3v3"},
            expected_row_version=2,
            idempotency_key="13a-race-w3",
        )
        assert r3.status_code == 200, r3.text
        result3, _ = await _freeze_claim_run(
            database,
            workspace_id=ws3,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="13a-race-w3f",
        )
        assert result3.status == "SUCCEEDED", result3.error
        result3a, _ = await _accept_claim_run(
            database,
            workspace_id=ws3,
            delegator_id=delegator_id,
            pool=pool,
            claimant="13a-race-w3a",
            boundary=boundary,
        )
        assert result3a.status == "SUCCEEDED", result3a.error

        C = await _canonical_projection(database, heading)
        assert C["props"] == {"level": 1, "text": "W3v3"}
        assert C["row_version"] == 3
        conflicts_final = await _public_conflicts(database, ws1)
        assert len(conflicts_final) == 1
        assert conflicts_final[0]["conflict_kind"] == "BASE_ROW_CHANGED"
        assert conflicts_final[0]["table_name"] == "page_composition"
        assert conflicts_final[0]["primary_key"] == {"id": str(heading)}
        assert UUID(str(conflicts_final[0]["operation_id"])) == op_fresh
        # The committed fact survives the later publish unchanged.
        facts = await _heading_facts(database, heading, ws1)
        assert [f["operation_id"] for f in facts] == [op_fresh]
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_attribution_isolation_and_legal_discard(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Item 4: both HTTP paths attribute the same resource's transitions
    to distinct families/principals with chaining images; cross-site
    denials at the real login boundaries record nothing; a legal
    discard removes the pending COW rows but the committed effect
    facts remain; non-heading writes stay outside the pilot."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    heading: UUID = ids["heading_id"]
    page_id: UUID = ids["page_id"]

    # A real AGENT workspace carries BOTH paths for a clean attribution
    # chain (the seeded workspace is a HUMAN workspace).
    owner_pool = await database.role_pool("slaif_owner")
    ws_agent = await _create_agent_workspace(
        owner_pool,
        site_id=site_id,
        delegator_id=delegator_id,
        title="13a attribution agent workspace",
    )
    await owner_pool.close()

    A = await _canonical_projection(database, heading)

    # 1. Agent path first, then Human-on-Agent Editor on the SAME
    #    heading in the SAME workspace: the images chain exactly.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        token = await _new_capability(owner, ws_agent)
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id = $1"
            " ORDER BY created_at DESC LIMIT 1",
            ws_agent,
        )

    r1 = await _agent_patch(
        database,
        token,
        heading,
        {"level": 2, "text": "AgentSide"},
        expected_row_version=1,
        idempotency_key="13a-attr-agent",
    )
    assert r1.status_code == 200, r1.text

    control = ControlDatabase(_control_settings(database))
    editor = EditorDatabase(_editor_db_settings(database))
    app = create_editor_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST),
        database=control,
        editor_database=editor,
    )
    try:
        await control.start()
        await editor.start()
        session = await control.human_session_service().create(delegator_id)
        tok = session.token.get_secret_value()
        csrf = session.csrf_token.get_secret_value()
        comp_path = f"/api/editor/v1/sites/{site_id}/pages/{page_id}/composition"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://editor.test",
            timeout=60,
        ) as client:
            r2 = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"props": {"level": 3, "text": "HumanSide"}},
                headers={
                    "cookie": f"slaif_session={tok}; slaif_csrf={csrf}",
                    "x-csrf-token": csrf,
                    "x-editor-workspace": str(ws_agent),
                    "Idempotency-Key": "13a-attr-editor",
                },
            )
            assert r2.status_code == 200, r2.text
    finally:
        await editor.stop()
        await control.stop()

    facts = await _heading_facts(database, heading, ws_agent)
    assert len(facts) == 2
    f_agent, f_editor = facts
    assert f_agent["family"] == "agent"
    assert f_agent["capability_id"] == capability_id
    assert f_agent["human_user_id"] is None
    assert f_editor["family"] == "human_editor"
    assert f_editor["capability_id"] is None
    assert f_editor["human_user_id"] == delegator_id
    assert f_agent["operation_id"] != f_editor["operation_id"]
    # Exact chaining across families on the same resource.
    assert f_agent["props_before"] == A["props"]
    assert f_agent["props_after"] == {"level": 2, "text": "AgentSide"}
    assert f_editor["props_before"] == f_agent["props_after"]
    assert f_editor["props_after"] == {"level": 3, "text": "HumanSide"}
    assert f_editor["row_version_before"] == f_agent["row_version_after"]

    # 2. Cross-site denial at the real Agent login boundary: a
    #    capability bound to a DIFFERENT site cannot touch this
    #    component; nothing is recorded.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        other_delegator = await owner.fetchval(
            """
            INSERT INTO control.user_account (
                id, identity_kind, local_username, local_username_normalized,
                password_hash, display_name, status
            ) VALUES (
                gen_random_uuid(), 'LOCAL', 'Accept.13a.Other',
                'accept.13a.other', $1, 'Accept 13a Other', 'ACTIVE'
            ) RETURNING id
            """,
            _AGGON2,
        )
        other_site = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name,"
            " default_locale, component_catalog_version)"
            " VALUES ('accept-13a-other', 'Accept 13a Other', 'en-US',"
            " 'catalog-v1') RETURNING id"
        )
        await owner.execute(
            "INSERT INTO control.site_membership (site_id,user_account_id,"
            " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
            other_site,
            other_delegator,
        )
        other_ws, _other_cap = await _create_workspace(
            owner, other_site, other_delegator, "13a other site ws"
        )
        token_other = await _new_capability(owner, other_ws)

    r_cross = await _agent_patch(
        database,
        token_other,
        heading,
        {"level": 2, "text": "CrossSite"},
        expected_row_version=1,
        idempotency_key="13a-cross-site",
    )
    assert r_cross.status_code == 404, r_cross.text
    assert await _heading_facts(database, heading) == [f_agent, f_editor]

    # 3. Cross-site denial at the real Editor login boundary: a session
    #    enrolled on the other site cannot write this site's page.
    control = ControlDatabase(_control_settings(database))
    editor2 = EditorDatabase(_editor_db_settings(database))
    app = create_editor_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST),
        database=control,
        editor_database=editor2,
    )
    try:
        await control.start()
        await editor2.start()
        other_session = await control.human_session_service().create(other_delegator)
        otok = other_session.token.get_secret_value()
        ocsrf_token = other_session.csrf_token.get_secret_value()
        other_cookie = f"slaif_session={otok}; slaif_csrf={ocsrf_token}"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://editor.test",
            timeout=60,
        ) as client:
            r_cross_e = await client.patch(
                f"/api/editor/v1/sites/{site_id}/pages/{page_id}"
                f"/composition/components/{heading}",
                json={"props": {"level": 3, "text": "CrossSiteE"}},
                headers={
                    "cookie": other_cookie,
                    "x-csrf-token": ocsrf_token,
                    "x-editor-workspace": str(other_ws),
                    "Idempotency-Key": "13a-cross-site-e",
                },
            )
    finally:
        await editor2.stop()
        await control.stop()
    assert r_cross_e.status_code in (403, 404), r_cross_e.text
    assert await _heading_facts(database, heading) == [f_agent, f_editor]

    # 4. Pilot boundary: a non-heading props write through the SAME
    #    agent path completes normally but records NO fact.
    section_id: UUID = ids["section_id"]
    section_view = await _canonical_projection(database, section_id)
    assert section_view["component_type"] == "Section"
    section_props = dict(section_view["props"])
    section_props["variant"] = "narrow"
    r_sec = await _agent_patch(
        database,
        token,
        section_id,
        section_props,
        expected_row_version=section_view["row_version"],
        idempotency_key="13a-boundary-section",
    )
    assert r_sec.status_code == 200, r_sec.text
    assert await _heading_facts(database, heading) == [f_agent, f_editor]
    assert await _heading_facts_for_component(database, section_id) == []

    # 5. Legal discard: the real freeze + human discard lifecycle
    #    removes the pending COW rows of the workspace, but the
    #    COMMITTED effect facts remain (audit is not COW state).
    pool = await _worker_pool(database)
    try:
        ops_before = await _public_operations(database, ws_agent)
        assert len(ops_before) >= 2  # the heading ops (+ section op)
        result_f, _ = await _freeze_claim_run(
            database,
            workspace_id=ws_agent,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="13a-attr-freeze",
        )
        assert result_f.status == "SUCCEEDED", result_f.error
        rows = await _enqueue_discard(database, ws_agent, delegator_id)
        assert len(rows) == 1
        job = await _claim_discard(database, "13a-attr-discard")
        result_d = await run_discard_job(pool, _worker_settings(database), job)
        assert result_d.status == "SUCCEEDED", result_d.error
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            ws_status = await owner.fetchval(
                "SELECT status FROM control.workspace WHERE id = $1",
                ws_agent,
            )
        assert ws_status == "DISCARDED"
        # Public operation inspection: the pending COW rows are gone.
        assert await _public_operations(database, ws_agent) == []
        # The committed facts survive the discard, byte-for-byte.
        facts_after = await _heading_facts(database, heading)
        assert [f["operation_id"] for f in facts_after] == [
            f_agent["operation_id"],
            f_editor["operation_id"],
        ]
        assert facts_after[0]["props_after"] == {"level": 2, "text": "AgentSide"}
        assert facts_after[1]["props_after"] == {"level": 3, "text": "HumanSide"}
    finally:
        await pool.close()

    # 6. Old workspace without facts = unknown: a workspace that never
    #    recorded proves nothing; the facts table simply has no row for
    #    it (no synthetic history, no claim of no-effect).
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        no_fact_count = await owner.fetchval(
            "SELECT count(*) FROM audit.heading_row_effect WHERE workspace_id = $1",
            other_ws,
        )
    assert no_fact_count == 0


async def _heading_facts_for_component(
    database: AgentSiteDatabase, component_id: UUID
) -> list[dict[str, Any]]:
    return await _heading_facts(database, component_id)


def _dsn(database: AgentSiteDatabase, user: str, password: str) -> str:
    params = database.connection_parameters
    host = quote(str(params["host"]), safe="[]:.")
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return (
        f"postgresql://{quote(user, safe='')}:{quote(password, safe='')}@"
        f"{host}:{params['port']}/{database.name}"
    )


async def _real_login(database: AgentSiteDatabase, role: str) -> asyncpg.Connection:
    """One connection on the REAL provisioned login for the role
    (no SET ROLE): LOGIN-identity proof under fixture trust auth."""

    login, password = database.credentials[role]
    return await asyncpg.connect(dsn=_dsn(database, login, password))


def _split_statements(sql: str) -> list[str]:
    """Split a multi-statement DDL block on statement-ending
    semicolons outside ``$fn$`` function bodies (the same rule 080's
    own ``_execute_block`` applies)."""

    stmts: list[str] = []
    current: list[str] = []
    in_body = False
    for line in sql.splitlines(keepends=True):
        current.append(line)
        if line.count("$fn$") % 2:
            in_body = not in_body
        if line.rstrip().endswith(";") and not in_body:
            stmts.append("".join(current))
            current = []
    if "".join(current).strip():
        stmts.append("".join(current))
    return [s for s in stmts if s.strip()]


@pytest.mark.asyncio
async def test_facts_authority_boundaries_and_downgrade_ratchet(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Runtime roles cannot forge/read/update/delete the facts, the
    recorder is owner-only and context-bound (no general fact insert),
    the versioned format is bounded, and the downgrade ratchet refuses
    at both the operator and the direct Alembic level (080 first, the
    079 body still intact behind it)."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    heading: UUID = ids["heading_id"]

    # 1. Real logins: every runtime role is denied on the facts table
    #    and on the owner-only recorder.
    for role in _DENY_ROLES:
        conn = await _real_login(database, role)
        try:
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await conn.fetchval("SELECT count(*) FROM audit.heading_row_effect")
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await conn.execute(
                    "INSERT INTO audit.heading_row_effect"
                    " (operation_id, family, mutation_kind, site_id,"
                    " workspace_id, component_id, row_version_before,"
                    " row_version_after, props_before, props_after)"
                    " VALUES (gen_random_uuid(), 'agent', 'heading_props',"
                    " $1, $1, $2, 1, 2, '{}'::jsonb, '{}'::jsonb)"
                    " ON CONFLICT DO NOTHING",
                    ids["site_id"],
                    heading,
                )
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await conn.execute(
                    "SELECT control.slaif_heading_row_effect_record("
                    " gen_random_uuid(), 'agent', $1, $1, $1, $2, 1, 2,"
                    " '{}'::jsonb, '{}'::jsonb)",
                    ids["site_id"],
                    heading,
                )
        finally:
            await conn.close()

    # The recorder has no role EXECUTE at all (owner only).
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        for role in _DENY_ROLES:
            granted = await owner.fetchval(
                "SELECT has_function_privilege("
                " $1, 'control.slaif_heading_row_effect_record"
                "(uuid,text,uuid,uuid,uuid,uuid,integer,integer,jsonb,jsonb)',"
                " 'EXECUTE')",
                role,
            )
            assert granted is False
        table_grants = await owner.fetchval(
            "SELECT has_table_privilege('slaif_owner',"
            " 'audit.heading_row_effect', 'SELECT')"
        )
        assert table_grants is True

    # 2. No general fact insert: even the owner, outside the trusted
    #    COW session context, is refused before any effect.
    with pytest.raises(asyncpg.PostgresError) as no_ctx:
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "SELECT control.slaif_heading_row_effect_record("
                " gen_random_uuid(), 'agent', $1, $1, $1, $2, 1, 2,"
                " '{}'::jsonb, '{}'::jsonb)",
                ids["site_id"],
                heading,
            )
    assert getattr(no_ctx.value, "sqlstate", None) == "P0001"
    assert "HEADING_EFFECT" in str(getattr(no_ctx.value, "message", ""))

    # 3. Bounded versioned format: the props images are capped at the
    #    existing composition 16384-octet ceiling; a larger image is
    #    refused by the table itself (defense in depth behind the
    #    definer's own props validation).
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        with pytest.raises(asyncpg.PostgresError) as over:
            await owner.execute(
                "INSERT INTO audit.heading_row_effect"
                " (operation_id, family, mutation_kind, site_id,"
                " workspace_id, component_id, row_version_before,"
                " row_version_after, props_before, props_after)"
                " VALUES (gen_random_uuid(), 'agent', 'heading_props',"
                " $1, $1, $2, 1, 2, jsonb_build_object('text', $3::text),"
                " '{}'::jsonb)",
                ids["site_id"],
                heading,
                "x" * 16385,
            )
    assert getattr(over.value, "sqlstate", None) == "23514"

    # 4. Downgrade ratchet: direct Alembic 080 -> 079 refuses (080 body);
    # the operator path refuses via the bootstrap preflight; the state
    # is left exactly as found; and the 079 body still refuses 079 ->
    # 078 when staged from the released 079 head.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        before = await owner.fetchrow("SELECT version_num FROM control.alembic_version")
        assert before["version_num"] == "080_001"

    with pytest.raises(BootstrapStateError, match="heading row effect"):
        await downgrade(database.settings)
    with pytest.raises(DBAPIError) as direct_exc:
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="079_001",
        )
    underlying = direct_exc.value.orig
    assert "HEADING_ROW_EFFECT_DOWNGRADE_UNSUPPORTED" in str(underlying)
    assert getattr(underlying, "sqlstate", None) == "P0001"

    # Stage the released 079 head.  The 080 surface has no supported
    # downgrade (proved above), so a 079-era release deployment is
    # simulated at the fixture level: the owner restores the two
    # definer bodies to their original pre-080 forms from the live
    # sibling migration sources, drops the 080 recorder and facts
    # table, and stages the 079 version row.
    _m080 = importlib.import_module(
        "slaif_agent_site.db.alembic.versions.080_001_heading_row_effect"
    )
    editor_block = str(_m080._M063._legacy_composition_sql())
    _e_idx = editor_block.index(_m080._EDITOR_UPDATE_MARKER)
    _e_end = editor_block.find(_m080._EDITOR_UPDATE_END, _e_idx)
    editor_stmt = editor_block[_e_idx : _e_end + len(_m080._EDITOR_UPDATE_END)]
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        for stmt in _split_statements(str(_m080._M062._component_update_sql())):
            await owner.execute(stmt)
        await owner.execute(editor_stmt)
        await owner.execute(
            "DROP FUNCTION control.slaif_heading_row_effect_record"
            "(uuid,text,uuid,uuid,uuid,uuid,integer,integer,jsonb,jsonb)"
        )
        await owner.execute("DROP TABLE audit.heading_row_effect")
        await owner.execute(
            "UPDATE control.alembic_version SET version_num = '079_001'"
        )
        for fn in (
            "slaif_agent_component_update",
            "slaif_composition_node_update",
        ):
            src = await owner.fetchrow(
                "SELECT p.prosrc FROM pg_proc p"
                " JOIN pg_namespace n ON n.oid = p.pronamespace"
                " WHERE n.nspname = 'content' AND p.proname = $1",
                fn,
            )
            assert "slaif_heading_row_effect_record" not in src["prosrc"]
    with pytest.raises(DBAPIError) as direct_079_exc:
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="078_001",
        )
    underlying_079 = direct_079_exc.value.orig
    assert "REVIEWED_OPERATION_BINDING_DOWNGRADE_REFUSED" in str(underlying_079)
    assert getattr(underlying_079, "sqlstate", None) == "P0001"
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        after = await owner.fetchval("SELECT version_num FROM control.alembic_version")
        facts_present = await owner.fetchval(
            "SELECT to_regclass('audit.heading_row_effect') IS NULL"
        )
    assert after == "079_001"
    assert facts_present is True
