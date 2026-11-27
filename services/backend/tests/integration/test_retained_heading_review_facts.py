"""083-14-a: retain the recorded heading row effects in the immutable
review (migration 081_001).

Real runtime evidence for the retained Heading review facts:

- a real Agent + Human-on-Agent HTTP session with distinct same-heading
  reviewed operations, including an intermediate value and a final
  return to the original props, is retained by the real freeze worker
  in the same locked transaction as the snapshot, the companion
  manifest, the pointer and the job terminal;
- the exact durable bytes/identity are verified against the product
  owned 080 facts, the trusted 078 completion journal and the public
  reviewed-operation set (the companion manifest read);
- a real human acceptance and a real discard (separate workspaces,
  real COW settlement) leave the retained review recoverable through
  the authorized product read after cleanup and a subsequent same-site
  publication, over a fresh service connection;
- a pre-feature snapshot (no retention row) answers ``unavailable``
  and a genuinely captured empty set answers ``captured`` with an
  empty facts array; the two stay distinct;
- a known inconsistent binding and an over-budget set are refused
  without partial freeze or review state; the exact pre-aggregation
  canonical byte budget (shared record projection) refuses a
  selected set that is below the record and per-value caps but over
  the 1 MiB encoded ceiling, and captures a legal under-ceiling set
  whose stored facts_bytes equals the pre-assembly total; the
  diverged companion identity makes the authorized read uniformly
  unavailable and the exact restore serves the unchanged captured
  set; a fixture-only fault after snapshot/manifest staging rolls
  the whole locked transaction back with the earlier mutation facts
  intact and a coherent supported retry;
- the owner-restricted table and the two narrow definers keep their
  exact grant surface, and the downgrade ratchet refuses at both the
  operator and the direct Alembic level.

Public surfaces and product owned journals only; fixture-only
instrumentation (one armed fault trigger, budget seed rows) is
installed and removed inside each test and adds no product surface,
no grant and no production test interface.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.bootstrap.service import (
    BootstrapStateError,
    downgrade,
)
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration
from slaif_agent_site.db.roles import ROLE_NAMES
from slaif_agent_site.editor_api.app import create_app as create_editor_app
from slaif_agent_site.editor_api.database import EditorDatabase
from slaif_agent_site.review_worker.accept_job import MediaBoundary, run_accept_job
from slaif_agent_site.review_worker.discard_job import run_discard_job
from slaif_agent_site.review_worker.freeze_job import run_freeze_job
from sqlalchemy.exc import DBAPIError
from test_freeze_review_snapshot import (
    _claim_accept_job,
    _control_call,
    _control_http,
    _freeze_claim_run,
    _freeze_enqueue_claim,
    _session_cookie,
    _worker_call,
    _worker_pool,
    _worker_settings,
)
from test_heading_row_effects import (
    _agent_patch,
    _canonical_projection,
    _control_settings,
    _editor_db_settings,
    _heading_facts,
    _new_capability,
)
from test_human_agent_editor_workspace import _create_agent_workspace
from test_real_human_accept import (
    _AGGON2,
    _enqueue_bound_accept,
    _media_settings,
    _seed_site,
)
from test_real_human_discard import (
    _claim_discard,
    _enqueue_discard,
)

_SCHEMA_VERSION = "retained-heading-facts/v1"
_FACTS_VERSION = "heading-row-effect/v1"
# Mirrors the 081_001 historical literals exactly.
_MAX_RETAINED_RECORDS = 256
_MAX_RETAINED_VALUE_BYTES = 16384
_MAX_RETAINED_FACTS_BYTES = 1048576
# 083-14-b exact pre-aggregation byte budget fixture shape: the
# binding per-prop bound is the Agent API's 16384-byte
# ensure_ascii JSON props cap, so 2726 repetitions of U+754C (6
# escaped bytes each) plus a distinct decimal suffix per edit stay
# under that cap, the 4096-codepoint schema max_length and the 080
# 16384-octet native props image, while the 070 canonical
# serializer ASCII-escapes each U+754C to a 6-byte \u sequence.
#  34 such same-heading records push the EXACT canonical encoded
# array total over the 1 MiB ceiling while 24 stay well under it;
# the a-round codepoint estimate of the two props texts passes in
# both cases, so only the exact pre-aggregation check can refuse
# the over-ceiling set.
_BUDGET_CHAR = "\u754c"
_BUDGET_CHAR_REPEATS = 2726
_OVER_CEILING_EDITS = 34
_UNDER_CEILING_EDITS = 24


# ----------------------------------------------------------------------
# Shared helpers (this module only).
# ----------------------------------------------------------------------


async def _agent_workspace(
    database: AgentSiteDatabase,
    *,
    site_id: UUID,
    delegator_id: UUID,
    title: str,
) -> UUID:
    """One real AGENT workspace through the product trusted create."""

    owner_pool = await database.role_pool("slaif_owner")
    try:
        return await _create_agent_workspace(
            owner_pool,
            site_id=site_id,
            delegator_id=delegator_id,
            title=title,
        )
    finally:
        await owner_pool.close()


def _owner(database: AgentSiteDatabase) -> Any:
    return owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    )


async def _retention_row(
    database: AgentSiteDatabase, snapshot_id: UUID
) -> dict[str, Any] | None:
    async with _owner(database) as owner:
        row = await owner.fetchrow(
            "SELECT * FROM control.heading_review_retention WHERE snapshot_id = $1",
            snapshot_id,
        )
    if row is None:
        return None
    result = dict(row)
    if isinstance(result["facts"], str):
        result["facts"] = json.loads(result["facts"])
    return result


async def _snapshot_digest_ok(database: AgentSiteDatabase, snapshot_id: UUID) -> bool:
    async with _owner(database) as owner:
        return bool(
            await owner.fetchval(
                "SELECT digest = encode(sha256(convert_to("
                " control.slaif_canonical_jsonb_text(payload),'UTF8')),'hex')"
                " FROM control.review_snapshot WHERE id = $1",
                snapshot_id,
            )
        )


async def _facts_digest_ok(
    database: AgentSiteDatabase, retention: dict[str, Any]
) -> bool:
    async with _owner(database) as owner:
        return bool(
            await owner.fetchval(
                "SELECT facts_digest = encode(sha256(convert_to("
                " control.slaif_canonical_jsonb_text(facts),'UTF8')),'hex')"
                " AND facts_bytes = length(convert_to("
                " control.slaif_canonical_jsonb_text(facts),'UTF8'))"
                " FROM control.heading_review_retention WHERE snapshot_id = $1",
                retention["snapshot_id"],
            )
        )


def _expected_record(fact: dict[str, Any]) -> dict[str, Any]:
    """The stored retained form of one product owned 080 fact."""

    if fact["family"] == "agent":
        principal_type = "capability"
        principal_id = str(fact["capability_id"])
    else:
        principal_type = "human_user"
        principal_id = str(fact["human_user_id"])
    return {
        "operation_id": str(fact["operation_id"]),
        "family": fact["family"],
        "component_id": str(fact["component_id"]),
        "row_version_before": fact["row_version_before"],
        "row_version_after": fact["row_version_after"],
        "props_before": fact["props_before"],
        "props_after": fact["props_after"],
        "principal_type": principal_type,
        "principal_id": principal_id,
    }


async def _agent_edit(
    database: AgentSiteDatabase,
    token: str,
    heading: UUID,
    props: dict[str, Any],
    expected_row_version: int,
    idempotency_key: str,
) -> UUID:
    response = await _agent_patch(
        database,
        token,
        heading,
        props,
        expected_row_version=expected_row_version,
        idempotency_key=idempotency_key,
    )
    assert response.status_code == 200, response.text
    return UUID(str(response.json()["operation_id"]))


async def _editor_edit(
    database: AgentSiteDatabase,
    *,
    site_id: UUID,
    page_id: UUID,
    heading: UUID,
    workspace_id: UUID,
    delegator_id: UUID,
    props: dict[str, Any],
    idempotency_key: str,
) -> None:
    """One real Human-on-Agent Editor HTTP edit (no row_version on the
    wire: the pre-080 Editor contract)."""

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
        headers = {
            "cookie": f"slaif_session={token}; slaif_csrf={csrf}",
            "x-csrf-token": csrf,
            "x-editor-workspace": str(workspace_id),
            "Idempotency-Key": idempotency_key,
        }
        comp_path = f"/api/editor/v1/sites/{site_id}/pages/{page_id}/composition"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://editor.test",
            timeout=60,
        ) as client:
            response = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"props": props},
                headers=headers,
            )
        assert response.status_code == 200, response.text
    finally:
        await editor.stop()
        await control.stop()


async def _heading_effects_http(
    database: AgentSiteDatabase,
    site_id: UUID,
    workspace_id: UUID,
    user_id: UUID,
    *,
    site_override: UUID | None = None,
    snapshot_id: UUID | None = None,
) -> httpx.Response:
    """The retained read through the real public Control route
    (a fresh service connection per call)."""

    adapter, client = await _control_http(database)
    try:
        cookie, csrf = await _session_cookie(adapter, user_id)
        path_site = site_override if site_override is not None else site_id
        path = (
            f"/api/control/v1/sites/{path_site}"
            f"/workspaces/{workspace_id}/review/heading-effects/"
        )
        if snapshot_id is not None:
            path = f"{path}?snapshot_id={snapshot_id}"
        return await client.get(
            path,
            headers={
                "cookie": f"{cookie}; slaif_csrf={csrf}",
                "x-csrf-token": csrf,
            },
        )
    finally:
        await client.aclose()
        await adapter.stop()


# ----------------------------------------------------------------------
# 1. The real lifecycle: capture, accept, discard, reopen.
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_real_lifecycle_retains_exact_heading_facts(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Agent + Human-on-Agent same-heading session (with an intermediate
    value and a final return to the original props) is retained in the
    immutable review, survives real accept and real discard in separate
    workspaces, and reopens through the authorized product read after
    cleanup and a subsequent same-site publication with a fresh service
    connection."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    heading: UUID = ids["heading_id"]
    page_id: UUID = ids["page_id"]

    original = await _canonical_projection(database, heading)
    assert original["props"] == {"level": 1, "text": "Accept"}
    assert original["row_version"] == 1

    # --- Real edits in one AGENT workspace: two families, one heading.
    ws_accept = await _agent_workspace(
        database,
        site_id=site_id,
        delegator_id=delegator_id,
        title="14a accept workspace",
    )
    async with _owner(database) as owner:
        token = await _new_capability(owner, ws_accept)
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id = $1"
            " ORDER BY created_at DESC LIMIT 1",
            ws_accept,
        )

    op1 = await _agent_edit(
        database, token, heading, {"level": 2, "text": "Mid"}, 1, "14a-op-1"
    )
    await _editor_edit(
        database,
        site_id=site_id,
        page_id=page_id,
        heading=heading,
        workspace_id=ws_accept,
        delegator_id=delegator_id,
        props={"level": 2, "text": "Back"},
        idempotency_key="14a-op-2",
    )
    # Final props return exactly to the original value: the
    # intermediate facts must still be retained.
    op3 = await _agent_edit(
        database,
        token,
        heading,
        {"level": 1, "text": "Accept"},
        3,
        "14a-op-3",
    )

    facts_before = await _heading_facts(database, heading, ws_accept)
    assert [fact["family"] for fact in facts_before] == [
        "agent",
        "human_editor",
        "agent",
    ]
    assert [
        (fact["row_version_before"], fact["row_version_after"]) for fact in facts_before
    ] == [(1, 2), (2, 3), (3, 4)]
    op2 = facts_before[1]["operation_id"]
    assert {fact["operation_id"] for fact in facts_before} == {
        op1,
        op2,
        op3,
    }
    assert facts_before[0]["operation_id"] == op1
    assert facts_before[2]["operation_id"] == op3
    assert facts_before[0]["props_before"] == original["props"]
    assert facts_before[2]["props_after"] == original["props"]
    assert facts_before[0]["capability_id"] == capability_id
    assert facts_before[1]["human_user_id"] == delegator_id
    assert facts_before[1]["capability_id"] is None

    # --- Real freeze: the capture is part of the locked transaction.
    pool = await _worker_pool(database)
    try:
        result, job_id = await _freeze_claim_run(
            database,
            workspace_id=ws_accept,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="retained-freeze-1",
        )
        assert result.status == "SUCCEEDED", result.error
    except BaseException:
        await pool.close()
        raise

    async with _owner(database) as owner:
        snapshot = await owner.fetchrow(
            "SELECT * FROM control.review_snapshot WHERE workspace_id = $1",
            ws_accept,
        )
        workspace = await owner.fetchrow(
            "SELECT status, review_snapshot_id FROM control.workspace WHERE id = $1",
            ws_accept,
        )
        manifest = await owner.fetchrow(
            "SELECT manifest_digest, snapshot_digest FROM"
            " control.review_operation_manifest WHERE snapshot_id = $1",
            snapshot["id"],
        )
    assert workspace["status"] == "REVIEW"
    assert workspace["review_snapshot_id"] == snapshot["id"]
    assert await _snapshot_digest_ok(database, snapshot["id"])

    retention = await _retention_row(database, snapshot["id"])
    assert retention is not None
    assert retention["site_id"] == site_id
    assert retention["workspace_id"] == ws_accept
    assert retention["schema_version"] == _SCHEMA_VERSION
    assert retention["snapshot_digest"] == snapshot["digest"]
    assert retention["operation_manifest_digest"] == manifest["manifest_digest"]
    assert retention["fact_count"] == 3
    assert await _facts_digest_ok(database, retention)

    # Exact durable bytes: every stored record is field-for-field the
    # product owned 080 fact of the same operation, in the
    # deterministic order (component, then per-row transition).
    stored = retention["facts"]
    assert [record["operation_id"] for record in stored] == [
        str(op1),
        str(op2),
        str(op3),
    ]
    for record, fact in zip(stored, facts_before, strict=True):
        assert record == _expected_record(fact)

    # Trusted completion + public operation set: every retained
    # operation is in U and bound by the manifest identity
    # (family/principal/resource field-for-field the 078 journal).
    async with _owner(database) as owner:
        journal = await owner.fetch(
            "SELECT operation_id, family, capability_id, human_user_id,"
            " resource_type, resource_id, disposition"
            " FROM audit.mutation_completion"
            " WHERE site_id = $1 AND workspace_id = $2"
            " AND operation_id = ANY($3::uuid[])",
            site_id,
            ws_accept,
            [str(op1), str(op2), str(op3)],
        )
    by_op = {row["operation_id"]: row for row in journal}
    assert set(by_op) == {op1, op2, op3}

    manifest_doc = await _control_call(
        database,
        "SELECT control.slaif_review_operation_manifest_read($1)",
        snapshot["id"],
    )
    envelope = manifest_doc[0][0]
    if isinstance(envelope, (str, bytes)):
        envelope = json.loads(envelope)
    u_ops = set(envelope["operation_ids"])
    identities = {
        record["operation_id"]: record for record in envelope["completion_identities"]
    }
    for record in stored:
        assert record["operation_id"] in u_ops
        identity = identities[record["operation_id"]]
        assert identity["family"] == record["family"]
        assert identity["principal_type"] == record["principal_type"]
        assert identity["principal_id"] == record["principal_id"]
        assert identity["resource_id"] == record["component_id"]
    for op in (op1, op2, op3):
        row = by_op[op]
        assert row["disposition"] == "completed"
        if row["family"] == "agent":
            assert row["capability_id"] == capability_id
            assert row["human_user_id"] is None
            assert row["resource_type"] == "composition_node"
        else:
            assert row["capability_id"] is None
            assert row["human_user_id"] == delegator_id
            assert row["resource_type"] == "editor.sites"
        assert row["resource_id"] == heading

    # --- Real human acceptance (this workspace).
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        enqueued = await _enqueue_bound_accept(database, ws_accept, delegator_id)
        accept_job = await _claim_accept_job(
            database,
            claimant="retained-accept-1",
            expected_job_id=UUID(str(enqueued[0]["job_id"])),
        )
        result = await run_accept_job(
            pool, _worker_settings(database), accept_job, media=boundary
        )
        assert result.status == "SUCCEEDED", result.error
    finally:
        await boundary.stop()
        await pool.close()

    # The final returned-to-original props are what got published.
    published = await _canonical_projection(database, heading)
    assert published["props"] == {"level": 1, "text": "Accept"}
    assert published["row_version"] == 4
    async with _owner(database) as owner:
        workspace = await owner.fetchrow(
            "SELECT status FROM control.workspace WHERE id = $1", ws_accept
        )
        media = await owner.fetchrow(
            "SELECT content_hash, storage_key FROM content.media_asset"
            " WHERE site_id = $1",
            site_id,
        )
    assert workspace["status"] == "ACCEPTED"
    # Rendered/media identity: the published asset keeps the seeded
    # content hash and storage key.
    assert media["content_hash"] == ids["media_digest"]

    # The review is unchanged by the publication (bytes + digest).
    retention_after = await _retention_row(database, snapshot["id"])
    assert retention_after == retention
    assert await _snapshot_digest_ok(database, snapshot["id"])
    media_references = json.loads(snapshot["media_references"])
    assert media_references[0]["mime_type"] == "image/png"

    # --- Real discard in a SEPARATE workspace (same site).
    ws_discard = await _agent_workspace(
        database,
        site_id=site_id,
        delegator_id=delegator_id,
        title="14a discard workspace",
    )
    async with _owner(database) as owner:
        token2 = await _new_capability(owner, ws_discard)
    op_discard = await _agent_edit(
        database,
        token2,
        heading,
        {"level": 3, "text": "Discarded"},
        4,
        "14a-op-discard",
    )
    pool2 = await _worker_pool(database)
    snapshot2: Any = None
    try:
        result, _ = await _freeze_claim_run(
            database,
            workspace_id=ws_discard,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool2,
            claimant="retained-freeze-2",
        )
        assert result.status == "SUCCEEDED", result.error

        async with _owner(database) as owner:
            snapshot2 = await owner.fetchrow(
                "SELECT id FROM control.review_snapshot WHERE workspace_id = $1",
                ws_discard,
            )
        retention2 = await _retention_row(database, snapshot2["id"])
        assert retention2 is not None
        assert retention2["fact_count"] == 1
        assert retention2["facts"][0]["operation_id"] == str(op_discard)
        assert retention2["facts"][0]["props_before"] == published["props"]
        assert retention2["facts"][0]["props_after"] == {
            "level": 3,
            "text": "Discarded",
        }

        enqueued = await _enqueue_discard(database, ws_discard, delegator_id)
        assert len(enqueued) == 1
        discard_job = await _claim_discard(database, "retained-discard-1")
        result = await run_discard_job(pool2, _worker_settings(database), discard_job)
        assert result.status == "SUCCEEDED", result.error
    finally:
        await pool2.close()

    async with _owner(database) as owner:
        workspace = await owner.fetchrow(
            "SELECT status FROM control.workspace WHERE id = $1", ws_discard
        )
    assert workspace["status"] == "DISCARDED"
    # Real COW settlement: the discarded change never reached the
    # canonical row.
    unchanged = await _canonical_projection(database, heading)
    assert unchanged["props"] == {"level": 1, "text": "Accept"}
    assert unchanged["row_version"] == 4
    # The discarded review's retained facts survive the settlement.
    retention2_after = await _retention_row(database, snapshot2["id"])
    assert retention2_after == retention2

    # --- Reopen both retained reviews through the authorized product
    # read: after cleanup, after the same-site publication, with a
    # fresh service connection (a brand-new Control database + client
    # per call).
    response = await _heading_effects_http(database, site_id, ws_accept, delegator_id)
    assert response.status_code == 200, response.text
    doc = response.json()
    assert doc["status"] == "captured"
    assert doc["schema_version"] == _SCHEMA_VERSION
    assert doc["snapshot_id"] == str(snapshot["id"])
    assert doc["snapshot_digest"] == snapshot["digest"]
    assert doc["operation_manifest_digest"] == manifest["manifest_digest"]
    assert doc["fact_count"] == 3
    assert doc["facts_digest"] == retention["facts_digest"]
    assert doc["facts_bytes"] == retention["facts_bytes"]
    assert doc["facts"] == retention["facts"]

    response = await _heading_effects_http(database, site_id, ws_discard, delegator_id)
    assert response.status_code == 200, response.text
    doc2 = response.json()
    assert doc2["status"] == "captured"
    assert doc2["snapshot_id"] == str(snapshot2["id"])
    assert doc2["facts"] == retention2["facts"]

    # The retained lookup binds the EXACT requested snapshot through
    # the same authorized product read: each named lookup re-checks
    # the snapshot row's own site/workspace association (independent
    # of the pointer), and a snapshot bound to the other workspace
    # of this site - or an unknown id - takes the same uniform
    # unavailable behavior (no oracle).
    response = await _heading_effects_http(
        database,
        site_id,
        ws_accept,
        delegator_id,
        snapshot_id=snapshot["id"],
    )
    assert response.status_code == 200, response.text
    doc_named = response.json()
    assert doc_named["status"] == "captured"
    assert doc_named["snapshot_id"] == str(snapshot["id"])
    assert doc_named["operation_manifest_digest"] == manifest["manifest_digest"]
    assert doc_named["facts"] == retention["facts"]
    assert doc_named["facts_digest"] == retention["facts_digest"]
    response = await _heading_effects_http(
        database,
        site_id,
        ws_discard,
        delegator_id,
        snapshot_id=snapshot2["id"],
    )
    assert response.status_code == 200, response.text
    doc2_named = response.json()
    assert doc2_named["status"] == "captured"
    assert doc2_named["snapshot_id"] == str(snapshot2["id"])
    assert doc2_named["facts"] == retention2["facts"]
    response = await _heading_effects_http(
        database,
        site_id,
        ws_accept,
        delegator_id,
        snapshot_id=snapshot2["id"],
    )
    assert response.status_code == 404, response.text
    response = await _heading_effects_http(
        database, site_id, ws_accept, delegator_id, snapshot_id=uuid4()
    )
    assert response.status_code == 404, response.text

    # The existing review document (071 read model) is preserved for
    # the same snapshot, including the companion manifest.
    adapter, client = await _control_http(database)
    try:
        cookie, csrf = await _session_cookie(adapter, delegator_id)
        review = await client.get(
            f"/api/control/v1/sites/{site_id}/workspaces/{ws_accept}/review/",
            headers={
                "cookie": f"{cookie}; slaif_csrf={csrf}",
                "x-csrf-token": csrf,
            },
        )
        assert review.status_code == 200, review.text
        review_doc = review.json()
        assert review_doc["snapshot"]["id"] == str(snapshot["id"])
        assert review_doc["snapshot"]["digest"] == snapshot["digest"]
        assert review_doc["manifest"]["manifest_digest"] == manifest["manifest_digest"]
    finally:
        await client.aclose()
        await adapter.stop()

    # Different site and unauthorized caller: the existing uniform
    # unavailable behavior (no oracle).
    async with _owner(database) as owner:
        other_site = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name,"
            " default_locale, component_catalog_version) VALUES"
            " ('retained-other', 'Other', 'en-US', 'catalog-v1')"
            " RETURNING id"
        )
        stranger_id = await owner.fetchval(
            "INSERT INTO control.user_account (id, identity_kind,"
            " local_username, local_username_normalized, password_hash,"
            " display_name, status) VALUES (gen_random_uuid(),'LOCAL',"
            " 'Retained.Stranger','retained.stranger',$1,'Stranger',"
            " 'ACTIVE') RETURNING id",
            _AGGON2,
        )
    response = await _heading_effects_http(
        database,
        site_id,
        ws_accept,
        delegator_id,
        site_override=UUID(str(other_site)),
    )
    assert response.status_code == 404, response.text
    response = await _heading_effects_http(
        database, site_id, ws_accept, UUID(str(stranger_id))
    )
    assert response.status_code == 404, response.text
    # Unknown workspace: same uniform behavior.
    response = await _heading_effects_http(database, site_id, uuid4(), delegator_id)
    assert response.status_code == 404, response.text


# ----------------------------------------------------------------------
# 2. Pre-feature unavailable vs captured empty.
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pre_feature_unavailable_and_captured_empty(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """A frozen review with no heading edits captures an empty set
    (``captured`` with an empty facts array); the same review with no
    retention row - the shape of a pre-feature snapshot - answers
    ``unavailable``; the old review document is preserved either way."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]

    ws = await _agent_workspace(
        database,
        site_id=site_id,
        delegator_id=delegator_id,
        title="14a empty capture workspace",
    )
    pool = await _worker_pool(database)
    try:
        result, _ = await _freeze_claim_run(
            database,
            workspace_id=ws,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="retained-freeze-empty",
        )
        assert result.status == "SUCCEEDED", result.error
    finally:
        await pool.close()

    async with _owner(database) as owner:
        snapshot = await owner.fetchrow(
            "SELECT id, digest FROM control.review_snapshot WHERE workspace_id = $1",
            ws,
        )
    retention = await _retention_row(database, snapshot["id"])
    assert retention is not None
    assert retention["facts"] == []
    assert retention["fact_count"] == 0
    # The exact canonical bytes of the empty array.
    assert retention["facts_bytes"] == 2
    assert retention["facts_digest"] == hashlib.sha256(b"[]").hexdigest()

    # Captured empty set: a real success document, explicitly empty.
    response = await _heading_effects_http(database, site_id, ws, delegator_id)
    assert response.status_code == 200, response.text
    doc = response.json()
    assert doc["status"] == "captured"
    assert "reason" not in doc or doc["reason"] is None
    assert doc["facts"] == []
    assert doc["fact_count"] == 0
    assert doc["facts_digest"] == retention["facts_digest"]

    # Pre-feature shape: the same snapshot with no retention row
    # (the fixture removes the row the way a pre-081 freeze never
    # wrote it) is unavailable - distinct from captured empty.
    async with _owner(database) as owner:
        await owner.execute(
            "DELETE FROM control.heading_review_retention WHERE snapshot_id = $1",
            snapshot["id"],
        )
    response = await _heading_effects_http(database, site_id, ws, delegator_id)
    assert response.status_code == 200, response.text
    doc = response.json()
    assert doc["status"] == "unavailable"
    assert doc["reason"] == "pre_feature_snapshot"
    assert doc["schema_version"] == _SCHEMA_VERSION
    assert doc["snapshot_id"] == str(snapshot["id"])
    assert doc["snapshot_digest"] == snapshot["digest"]
    assert "facts" not in doc
    assert "facts_digest" not in doc

    # The old review document (071 read model) is preserved.
    adapter, client = await _control_http(database)
    try:
        cookie, csrf = await _session_cookie(adapter, delegator_id)
        review = await client.get(
            f"/api/control/v1/sites/{site_id}/workspaces/{ws}/review/",
            headers={
                "cookie": f"{cookie}; slaif_csrf={csrf}",
                "x-csrf-token": csrf,
            },
        )
        assert review.status_code == 200, review.text
        assert review.json()["snapshot"]["id"] == str(snapshot["id"])
    finally:
        await client.aclose()
        await adapter.stop()


# ----------------------------------------------------------------------
# 3. Binding and budget refusals leave no partial state.
# ----------------------------------------------------------------------


async def _seed_over_budget_facts(
    database: AgentSiteDatabase,
    *,
    site_id: UUID,
    workspace_id: UUID,
    heading: UUID,
    capability_id: UUID,
    count: int,
) -> None:
    """Owner-seeded coherent 080 facts (each with its real 078
    completion binding in the SAME transaction so the deferred
    constraint trigger passes) to exercise the trusted budget guard.

    Fixture data only: the rows are consistent product-shaped facts,
    and only the trusted capture definer under test consumes them.
    """

    assert count > _MAX_RETAINED_RECORDS
    # The operation id is a deterministic UUID derived from the
    # series index (stable across the four statements of the one
    # transaction, so no temporary table is needed and the owner
    # login never requires CREATE on the database).
    op_expr = (
        "(substr(m.h, 1, 8) || '-' || substr(m.h, 9, 4) || '-4'"
        " || substr(m.h, 14, 3) || '-8' || substr(m.h, 18, 3) || '-'"
        " || substr(m.h, 21, 12))::uuid"
    )
    seed_from = (
        " FROM generate_series(1, $5) AS s(i)"
        " CROSS JOIN LATERAL (SELECT md5('budget-seed-' || s.i) AS h) AS m"
    )
    async with _owner(database) as owner:
        # One transaction: the 080 deferred constraint trigger
        # checks the completion binding at commit, so all four
        # statements must commit together.
        async with owner.transaction():
            await owner.execute(
                f"""
                INSERT INTO audit.heading_row_effect
              (operation_id, family, mutation_kind, site_id, workspace_id,
               component_id, row_version_before, row_version_after,
               props_before, props_after, capability_id)
            SELECT {op_expr}, 'agent', 'heading_props', $1, $2, $3,
                   s.i, s.i + 1,
                   jsonb_build_object('text', 'before-' || s.i),
                   jsonb_build_object('text', 'after-' || s.i),
                   $4
            {seed_from}
            """,
                site_id,
                workspace_id,
                heading,
                capability_id,
                count,
            )
            await owner.execute(
                f"""
                INSERT INTO audit.mutation_completion
                  (operation_id, family, site_id, workspace_id, capability_id,
                   request_identity, request_digest, resource_type,
                   resource_id, disposition)
                SELECT {op_expr}, 'agent', $1, $2, $4,
                       encode(sha256(convert_to('budget-seed-' || s.i, 'UTF8')),
                              'hex'),
                       md5((s.i + 200000)::text)
                         || md5((s.i + 300000)::text),
                       'composition_node', $3, 'completed'
                {seed_from}
                """,
                site_id,
                workspace_id,
                heading,
                capability_id,
                count,
            )
            await owner.execute(
                f"""
                INSERT INTO audit.agent_mutation
                  (operation_id, capability_id, workspace_id, site_id,
                   resource_type, resource_id, request_digest,
                   response_status)
                SELECT {op_expr}, $4, $2, $1, 'composition_node', $3,
                       md5((s.i + 200000)::text)
                         || md5((s.i + 300000)::text),
                       200
                {seed_from}
                """,
                site_id,
                workspace_id,
                heading,
                capability_id,
                count,
            )
            # Explicit FROM clause (not {seed_from}, whose $5 would
            # refer to a fifth parameter this statement does not
            # take): all four values are referenced exactly once.
            await owner.execute(
                f"""
                INSERT INTO control.agent_idempotency
                  (capability_id, workspace_id, idempotency_key,
                   request_digest, operation_id, status_code, response_body,
                   resource_type, resource_id, completed_at)
                SELECT $3, $1, 'budget-seed-' || s.i,
                       md5((s.i + 200000)::text)
                         || md5((s.i + 300000)::text),
                       {op_expr}, 200, '{{}}'::jsonb, 'composition_node', $2, now()
                FROM generate_series(1, $4) AS s(i)
                CROSS JOIN LATERAL (SELECT md5('budget-seed-' || s.i) AS h) AS m
                """,
                workspace_id,
                heading,
                capability_id,
                count,
            )


@pytest.mark.asyncio
async def test_budget_and_binding_refusals_leave_no_partial_state(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """An over-budget set refuses the whole freeze (no snapshot, no
    companion, no retention, workspace still FREEZING, facts intact);
    a known inconsistent binding refuses the capture before any write
    and leaves the existing retention row untouched, makes the
    authorized human read uniformly unavailable (read-time identity
    recheck), and serves the unchanged captured set again once the
    exact stored identity is restored."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    heading: UUID = ids["heading_id"]

    # --- (a) Over budget: more than the record ceiling, coherent.
    ws_budget = await _agent_workspace(
        database,
        site_id=site_id,
        delegator_id=delegator_id,
        title="14a budget workspace",
    )
    async with _owner(database) as owner:
        await _new_capability(owner, ws_budget)
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id = $1"
            " ORDER BY created_at DESC LIMIT 1",
            ws_budget,
        )
    await _seed_over_budget_facts(
        database,
        site_id=site_id,
        workspace_id=ws_budget,
        heading=heading,
        capability_id=UUID(str(capability_id)),
        count=_MAX_RETAINED_RECORDS + 1,
    )

    pool = await _worker_pool(database)
    try:
        result, job_id = await _freeze_claim_run(
            database,
            workspace_id=ws_budget,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="retained-freeze-budget",
        )
    finally:
        await pool.close()
    assert result.status == "FAILED"
    assert result.error == "HEADING_RETENTION_FAILED"

    async with _owner(database) as owner:
        snapshot_count = await owner.fetchval(
            "SELECT count(*) FROM control.review_snapshot WHERE workspace_id = $1",
            ws_budget,
        )
        manifest_count = await owner.fetchval(
            "SELECT count(*) FROM control.review_operation_manifest"
        )
        retention_count = await owner.fetchval(
            "SELECT count(*) FROM control.heading_review_retention"
        )
        workspace_status = await owner.fetchval(
            "SELECT status FROM control.workspace WHERE id = $1",
            ws_budget,
        )
        fact_count = await owner.fetchval(
            "SELECT count(*) FROM audit.heading_row_effect WHERE workspace_id = $1",
            ws_budget,
        )
        job = await owner.fetchrow(
            "SELECT status, error FROM control.review_job WHERE id = $1",
            job_id,
        )
    # No partial freeze or review state: the whole locked transaction
    # rolled back; the earlier mutation facts are intact.
    assert snapshot_count == 0
    assert manifest_count == 0
    assert retention_count == 0
    assert workspace_status == "FREEZING"
    assert fact_count == _MAX_RETAINED_RECORDS + 1
    assert job["status"] == "FAILED"
    assert job["error"] == "HEADING_RETENTION_FAILED"

    # --- (b) Binding mismatch: a real freeze succeeds with one real
    # fact; the stored companion identity is then made to disagree
    # with the fact's principal (fixture-owned state corruption), and
    # the trusted capture refuses before any write.
    ws_mismatch = await _agent_workspace(
        database,
        site_id=site_id,
        delegator_id=delegator_id,
        title="14a binding workspace",
    )
    async with _owner(database) as owner:
        token = await _new_capability(owner, ws_mismatch)
    op = await _agent_edit(
        database,
        token,
        heading,
        {"level": 2, "text": "Binding"},
        1,
        "14a-op-binding",
    )
    pool = await _worker_pool(database)
    try:
        result, _ = await _freeze_claim_run(
            database,
            workspace_id=ws_mismatch,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="retained-freeze-binding",
        )
        assert result.status == "SUCCEEDED", result.error
    finally:
        await pool.close()

    async with _owner(database) as owner:
        snapshot = await owner.fetchrow(
            "SELECT id FROM control.review_snapshot WHERE workspace_id = $1",
            ws_mismatch,
        )
        before = await _retention_row(database, snapshot["id"])
        assert before is not None and before["fact_count"] == 1
        identities = await owner.fetchval(
            "SELECT completion_identities FROM"
            " control.review_operation_manifest WHERE snapshot_id = $1",
            snapshot["id"],
        )
        if isinstance(identities, str):
            identities = json.loads(identities)
        # JSONB keys are text: look up by the string form of the
        # operation UUID returned by the real agent edit.
        records = {record["operation_id"]: record for record in identities}
        assert records[str(op)]["principal_id"] is not None
        # The exact stored identity, saved BEFORE the fixture-only
        # corruption so the read-time restore is byte-exact.
        original_identities = json.dumps(list(records.values()))
        records[str(op)] = dict(records[str(op)])
        records[str(op)]["principal_id"] = str(uuid4())
        await owner.execute(
            "UPDATE control.review_operation_manifest SET"
            " completion_identities = $2 WHERE snapshot_id = $1",
            snapshot["id"],
            json.dumps(list(records.values())),
        )
    with pytest.raises(asyncpg.PostgresError) as mismatch_exc:
        await _worker_call(
            database,
            "SELECT control.slaif_review_retain_heading_facts($1, $2)",
            ws_mismatch,
            site_id,
        )
    assert mismatch_exc.value.sqlstate == "P0001"
    assert "HEADING_RETENTION_BINDING_MISMATCH" in str(mismatch_exc.value.message or "")
    # No partial write: the existing retention row is untouched.
    after = await _retention_row(database, snapshot["id"])
    assert after == before
    # --- (c) Read-time negative evidence on the same bounded
    # fixture: the diverged persisted identity makes the authorized
    # human read uniformly unavailable (the served set is re-checked
    # against the companion at read time), and restoring the exact
    # stored identity serves the unchanged captured set.
    response = await _heading_effects_http(
        database,
        site_id,
        ws_mismatch,
        delegator_id,
        snapshot_id=snapshot["id"],
    )
    assert response.status_code == 404, response.text
    async with _owner(database) as owner:
        await owner.execute(
            "UPDATE control.review_operation_manifest SET"
            " completion_identities = $2 WHERE snapshot_id = $1",
            snapshot["id"],
            original_identities,
        )
    response = await _heading_effects_http(
        database,
        site_id,
        ws_mismatch,
        delegator_id,
        snapshot_id=snapshot["id"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "captured"
    assert body["snapshot_id"] == str(snapshot["id"])
    assert body["fact_count"] == after["fact_count"]
    assert body["facts_bytes"] == after["facts_bytes"]
    assert body["facts_digest"] == after["facts_digest"]
    assert body["facts"] == after["facts"]


async def _preassembly_budget_case(
    database: AgentSiteDatabase,
    *,
    site_id: UUID,
    delegator_id: UUID,
    heading: UUID,
    edits: int,
    title: str,
    claimant: str,
) -> tuple[UUID, list[UUID]]:
    """``edits`` real Agent edits of the same heading, each with a
    distinct near-maximum props value (under the Agent API props
    byte cap, the schema max_length and the 080 per-value octet
    cap); returns the workspace and the
    real operation UUIDs in edit order."""

    ws = await _agent_workspace(
        database,
        site_id=site_id,
        delegator_id=delegator_id,
        title=title,
    )
    async with _owner(database) as owner:
        token = await _new_capability(owner, ws)
    operations: list[UUID] = []
    for index in range(1, edits + 1):
        operations.append(
            await _agent_edit(
                database,
                token,
                heading,
                {
                    "level": 2,
                    "text": _BUDGET_CHAR * _BUDGET_CHAR_REPEATS + str(index - 1),
                },
                index,
                f"14b-byte-{claimant}-{index}",
            )
        )
    return ws, operations


async def _preassembly_oracle(
    database: AgentSiteDatabase,
    *,
    site_id: UUID,
    workspace_id: UUID,
    operations: list[UUID],
) -> dict[str, int]:
    """Owner-side measurement of the persisted 080 facts of exactly
    these operations (fixture verification only): the EXACT
    pre-assembly canonical encoded total the 081 capture enforces
    before aggregation - the same 9-field record shape, each
    record's exact 070 canonical UTF-8 bytes, the two array
    brackets, one comma between every pair of adjacent records -
    alongside the a-round codepoint estimate of the two props JSON
    texts and the native per-value octet maximum, so the test can
    prove the case sits under the count and value caps while only
    the exact encoded total crosses the ceiling."""

    operations_arg = [str(operation) for operation in operations]
    async with _owner(database) as owner:
        return {
            "records": await owner.fetchval(
                "SELECT count(*) FROM audit.heading_row_effect"
                " WHERE site_id = $1 AND workspace_id = $2"
                " AND operation_id = ANY($3::uuid[])",
                site_id,
                workspace_id,
                operations_arg,
            ),
            "pre_total": await owner.fetchval(
                "SELECT coalesce(sum(octet_length(convert_to("
                " control.slaif_canonical_jsonb_text(rec), 'UTF8'))), 0)"
                " + 2 + GREATEST(coalesce(count(*), 0) - 1, 0)"
                " FROM ("
                " SELECT jsonb_build_object("
                "   'operation_id', f.operation_id::text,"
                "   'family', f.family,"
                "   'component_id', f.component_id::text,"
                "   'row_version_before', f.row_version_before,"
                "   'row_version_after', f.row_version_after,"
                "   'props_before', f.props_before,"
                "   'props_after', f.props_after,"
                "   'principal_type',"
                "     CASE WHEN f.family = 'agent' THEN 'capability'"
                "          ELSE 'human_user' END,"
                "   'principal_id',"
                "     CASE WHEN f.family = 'agent'"
                "          THEN f.capability_id::text"
                "          ELSE f.human_user_id::text END"
                " ) AS rec"
                " FROM audit.heading_row_effect AS f"
                " WHERE f.site_id = $1 AND f.workspace_id = $2"
                " AND f.operation_id = ANY($3::uuid[])"
                ") AS rows(rec)",
                site_id,
                workspace_id,
                operations_arg,
            ),
            "codepoint_estimate": await owner.fetchval(
                "SELECT coalesce(sum(length(f.props_before::text)"
                " + length(f.props_after::text)), 0)"
                " FROM audit.heading_row_effect AS f"
                " WHERE f.site_id = $1 AND f.workspace_id = $2"
                " AND f.operation_id = ANY($3::uuid[])",
                site_id,
                workspace_id,
                operations_arg,
            ),
            "value_octets_max": await owner.fetchval(
                "SELECT coalesce(max(greatest("
                " octet_length(f.props_before::text),"
                " octet_length(f.props_after::text))), 0)"
                " FROM audit.heading_row_effect AS f"
                " WHERE f.site_id = $1 AND f.workspace_id = $2"
                " AND f.operation_id = ANY($3::uuid[])",
                site_id,
                workspace_id,
                operations_arg,
            ),
        }


@pytest.mark.asyncio
async def test_preassembly_canonical_byte_budget_enforced_before_aggregation(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """The exact pre-aggregation canonical byte budget on the shared
    record projection (083-14-b finding 1):

    - 34 real same-heading Agent edits sit below the record cap
      (256) and the per-value cap (16384 octets per props image),
      but their EXACT canonical encoded array total (070
      ASCII-escapes each 3-byte U+754C to a 6-byte escape) crosses
      the 1 MiB ceiling while the a-round codepoint estimate of the
      two props texts still passes - every other gate is provably
      unable to fire, so the real freeze is refused AT the
      pre-aggregation check, with no partial freeze or review state;
    - 24 such edits form the legal under-ceiling set: the real
      freeze captures it, and the stored facts_bytes equals the
      exact pre-assembly total (the post-assembly equality
      invariant the definer enforces on the shared projection).
    """

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    heading: UUID = ids["heading_id"]

    # --- (a) Over the exact encoded ceiling, under both other caps:
    # the real freeze refuses, with no partial freeze or review
    # state; only the pre-aggregation byte check can fire.
    ws_over, over_ops = await _preassembly_budget_case(
        database,
        site_id=site_id,
        delegator_id=delegator_id,
        heading=heading,
        edits=_OVER_CEILING_EDITS,
        title="14b byte-over workspace",
        claimant="over",
    )
    over = await _preassembly_oracle(
        database,
        site_id=site_id,
        workspace_id=ws_over,
        operations=over_ops,
    )
    assert over["records"] == _OVER_CEILING_EDITS
    assert over["records"] < _MAX_RETAINED_RECORDS
    assert over["value_octets_max"] <= _MAX_RETAINED_VALUE_BYTES
    assert over["pre_total"] > _MAX_RETAINED_FACTS_BYTES
    assert over["codepoint_estimate"] < _MAX_RETAINED_FACTS_BYTES

    pool = await _worker_pool(database)
    try:
        result, job_id = await _freeze_claim_run(
            database,
            workspace_id=ws_over,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="retained-freeze-byte-over",
        )
    finally:
        await pool.close()
    assert result.status == "FAILED"
    assert result.error == "HEADING_RETENTION_FAILED"

    async with _owner(database) as owner:
        snapshot_count = await owner.fetchval(
            "SELECT count(*) FROM control.review_snapshot WHERE workspace_id = $1",
            ws_over,
        )
        retention_count = await owner.fetchval(
            "SELECT count(*) FROM control.heading_review_retention"
        )
        workspace_status = await owner.fetchval(
            "SELECT status FROM control.workspace WHERE id = $1",
            ws_over,
        )
        fact_count = await owner.fetchval(
            "SELECT count(*) FROM audit.heading_row_effect WHERE workspace_id = $1",
            ws_over,
        )
        job = await owner.fetchrow(
            "SELECT status, error FROM control.review_job WHERE id = $1",
            job_id,
        )
    # No partial freeze or review state: the whole locked
    # transaction rolled back; the earlier mutation facts are intact.
    assert snapshot_count == 0
    assert retention_count == 0
    assert workspace_status == "FREEZING"
    assert fact_count == _OVER_CEILING_EDITS
    assert job["status"] == "FAILED"
    assert job["error"] == "HEADING_RETENTION_FAILED"

    # --- (b) Legal under-ceiling set: captured, with the stored
    # byte count exactly equal to the pre-assembly total.
    ws_under, under_ops = await _preassembly_budget_case(
        database,
        site_id=site_id,
        delegator_id=delegator_id,
        heading=heading,
        edits=_UNDER_CEILING_EDITS,
        title="14b byte-under workspace",
        claimant="under",
    )
    under = await _preassembly_oracle(
        database,
        site_id=site_id,
        workspace_id=ws_under,
        operations=under_ops,
    )
    assert under["records"] == _UNDER_CEILING_EDITS
    assert under["records"] < _MAX_RETAINED_RECORDS
    assert under["value_octets_max"] <= _MAX_RETAINED_VALUE_BYTES
    assert under["pre_total"] < _MAX_RETAINED_FACTS_BYTES

    pool = await _worker_pool(database)
    try:
        result, _ = await _freeze_claim_run(
            database,
            workspace_id=ws_under,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="retained-freeze-byte-under",
        )
        assert result.status == "SUCCEEDED", result.error
    finally:
        await pool.close()

    async with _owner(database) as owner:
        snapshot = await owner.fetchrow(
            "SELECT id FROM control.review_snapshot WHERE workspace_id = $1",
            ws_under,
        )
    assert snapshot is not None
    retention = await _retention_row(database, snapshot["id"])
    assert retention is not None
    assert retention["fact_count"] == _UNDER_CEILING_EDITS
    assert retention["facts_bytes"] <= _MAX_RETAINED_FACTS_BYTES
    # Post-assembly exact equality with the shared pre-assembly
    # total (the definer's new invariant, independently measured).
    assert retention["facts_bytes"] == under["pre_total"]
    assert await _facts_digest_ok(database, retention)
    # Exact durable bytes, field-for-field the product owned 080
    # facts, in the deterministic per-row transition order.
    facts = await _heading_facts(database, heading, ws_under)
    stored = retention["facts"]
    assert len(stored) == len(facts) == _UNDER_CEILING_EDITS
    for record, fact in zip(stored, facts, strict=True):
        assert record == _expected_record(fact)
    assert [record["operation_id"] for record in stored] == [
        str(operation) for operation in under_ops
    ]


# ----------------------------------------------------------------------
# 4. Fixture-only fault after manifest staging: atomic rollback +
#    coherent supported retry.
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_freeze_fault_after_manifest_staging_rolls_back_atomically(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """A fixture-only failure raised while the companion manifest is
    being staged (after the snapshot row, before the terminal job
    success) rolls back snapshot, companion, pointer, retention and
    job state together, leaves the earlier mutation facts intact, and
    the coherent supported retry produces the complete review."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    heading: UUID = ids["heading_id"]

    ws = await _agent_workspace(
        database,
        site_id=site_id,
        delegator_id=delegator_id,
        title="14a fault workspace",
    )
    async with _owner(database) as owner:
        token = await _new_capability(owner, ws)
    op = await _agent_edit(
        database,
        token,
        heading,
        {"level": 2, "text": "Fault"},
        1,
        "14a-op-fault",
    )
    fact_before = await _heading_facts(database, heading, ws)
    assert len(fact_before) == 1
    assert fact_before[0]["operation_id"] == op

    # Fixture-only armed fault trigger on the companion table: it
    # fires inside the freeze transaction when the manifest row is
    # staged (after the snapshot insert, before the job terminal).
    async with _owner(database) as owner:
        await owner.execute(
            "CREATE TABLE control.fixture_retention_fault"
            " (armed boolean NOT NULL DEFAULT false)"
        )
        # The one state row: the trigger function reads
        # (SELECT armed ...) and a NULL result on a zero-row
        # table would silently never arm the fault.
        await owner.execute(
            "INSERT INTO control.fixture_retention_fault (armed) VALUES (false)"
        )
        await owner.execute(
            "CREATE FUNCTION control.fixture_retention_fault_fn()"
            " RETURNS trigger AS $body$\nBEGIN\n"
            "    IF (SELECT armed FROM control.fixture_retention_fault) THEN\n"
            "        RAISE EXCEPTION 'FIXTURE_RETENTION_FAULT'"
            " USING ERRCODE = 'P0001';\n"
            "    END IF;\n    RETURN NEW;\nEND;\n$body$"
            " LANGUAGE plpgsql"
        )
        await owner.execute(
            "CREATE TRIGGER fixture_retention_fault_trig"
            " AFTER INSERT ON control.review_operation_manifest"
            " FOR EACH ROW EXECUTE FUNCTION"
            " control.fixture_retention_fault_fn()"
        )
    try:
        async with _owner(database) as owner:
            await owner.execute(
                "UPDATE control.fixture_retention_fault SET armed = true"
            )
        pool = await _worker_pool(database)
        try:
            result, job_id = await _freeze_claim_run(
                database,
                workspace_id=ws,
                site_id=site_id,
                delegator_id=delegator_id,
                pool=pool,
                claimant="retained-freeze-fault",
            )
        finally:
            await pool.close()
        assert result.status == "FAILED"
        assert result.error == "SNAPSHOT_COMPLETE_FAILED"

        # Atomic rollback: no snapshot, companion, retention, pointer;
        # the workspace stays FREEZING; the earlier mutation fact is
        # intact (its transaction committed long before the freeze).
        async with _owner(database) as owner:
            snapshot_count = await owner.fetchval(
                "SELECT count(*) FROM control.review_snapshot WHERE workspace_id = $1",
                ws,
            )
            manifest_count = await owner.fetchval(
                "SELECT count(*) FROM control.review_operation_manifest"
            )
            retention_count = await owner.fetchval(
                "SELECT count(*) FROM control.heading_review_retention"
            )
            workspace = await owner.fetchrow(
                "SELECT status, review_snapshot_id FROM control.workspace"
                " WHERE id = $1",
                ws,
            )
        assert snapshot_count == 0
        assert manifest_count == 0
        assert retention_count == 0
        assert workspace["status"] == "FREEZING"
        assert workspace["review_snapshot_id"] is None
        facts_intact = await _heading_facts(database, heading, ws)
        assert facts_intact == fact_before

        # Coherent supported retry: the FREEZING workspace with no
        # live job accepts exactly one new freeze job.
        async with _owner(database) as owner:
            await owner.execute(
                "UPDATE control.fixture_retention_fault SET armed = false"
            )
        pool = await _worker_pool(database)
        try:
            job_id, job = await _freeze_enqueue_claim(
                database,
                workspace_id=ws,
                site_id=site_id,
                delegator_id=delegator_id,
                claimant="retained-freeze-retry",
            )
            result = await run_freeze_job(pool, _worker_settings(database), job)
            assert result.status == "SUCCEEDED", result.error
        finally:
            await pool.close()

        async with _owner(database) as owner:
            snapshot = await owner.fetchrow(
                "SELECT * FROM control.review_snapshot WHERE workspace_id = $1",
                ws,
            )
            workspace = await owner.fetchrow(
                "SELECT status, review_snapshot_id FROM control.workspace"
                " WHERE id = $1",
                ws,
            )
        assert workspace["status"] == "REVIEW"
        assert workspace["review_snapshot_id"] == snapshot["id"]
        retention = await _retention_row(database, snapshot["id"])
        assert retention is not None
        assert retention["fact_count"] == 1
        assert retention["facts"][0]["operation_id"] == str(op)
        assert retention["facts"][0] == _expected_record(fact_before[0])
        assert await _snapshot_digest_ok(database, snapshot["id"])
        assert await _facts_digest_ok(database, retention)
    finally:
        async with _owner(database) as owner:
            await owner.execute(
                "DROP TRIGGER IF EXISTS fixture_retention_fault_trig"
                " ON control.review_operation_manifest"
            )
            await owner.execute(
                "DROP FUNCTION IF EXISTS control.fixture_retention_fault_fn()"
            )
            await owner.execute("DROP TABLE IF EXISTS control.fixture_retention_fault")


# ----------------------------------------------------------------------
# 5. Authority boundaries + downgrade ratchet.
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retention_authority_boundaries_and_downgrade_ratchet(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """The retention table stays owner-only, the capture definer is
    worker-only, the read definer is control-only, and the downgrade
    ratchet refuses at both the operator and the direct Alembic level
    with the state left exactly as found."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]

    ws = await _agent_workspace(
        database,
        site_id=site_id,
        delegator_id=delegator_id,
        title="14a authority workspace",
    )
    async with _owner(database) as owner:
        token = await _new_capability(owner, ws)
    await _agent_edit(
        database,
        token,
        ids["heading_id"],
        {"level": 2, "text": "Authority"},
        1,
        "14a-op-authority",
    )
    pool = await _worker_pool(database)
    try:
        result, _ = await _freeze_claim_run(
            database,
            workspace_id=ws,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="retained-freeze-authority",
        )
        assert result.status == "SUCCEEDED", result.error
    finally:
        await pool.close()

    # 1. The table: no role but the owner has any privilege; no role
    #    login can read or write it.
    async with _owner(database) as owner:
        for role in ROLE_NAMES:
            select_ok = await owner.fetchval(
                "SELECT has_table_privilege($1,"
                " 'control.heading_review_retention','SELECT')",
                role,
            )
            update_ok = await owner.fetchval(
                "SELECT has_table_privilege($1,"
                " 'control.heading_review_retention','UPDATE')",
                role,
            )
            insert_ok = await owner.fetchval(
                "SELECT has_table_privilege($1,"
                " 'control.heading_review_retention','INSERT')",
                role,
            )
            assert select_ok is (role == "slaif_owner"), role
            assert update_ok is (role == "slaif_owner"), role
            assert insert_ok is (role == "slaif_owner"), role

    # 2. The definers: exactly one allowed caller each; every other
    #    role (and PUBLIC) is denied.
    async with _owner(database) as owner:
        for role in ROLE_NAMES:
            capture_ok = await owner.fetchval(
                "SELECT has_function_privilege($1,"
                " 'control.slaif_review_retain_heading_facts"
                "(uuid,uuid)','EXECUTE')",
                role,
            )
            read_ok = await owner.fetchval(
                "SELECT has_function_privilege($1,"
                " 'control.slaif_review_heading_effects_read"
                "(uuid,uuid,uuid,uuid)','EXECUTE')",
                role,
            )
            assert capture_ok is (role in ("slaif_review_worker", "slaif_owner")), role
            assert read_ok is (role in ("slaif_control", "slaif_owner")), role
        for qualified in (
            "control.slaif_review_retain_heading_facts(uuid,uuid)",
            "control.slaif_review_heading_effects_read(uuid,uuid,uuid,uuid)",
        ):
            public_ok = await owner.fetchval(
                "SELECT has_function_privilege($1, $2, 'EXECUTE')",
                "public",
                qualified,
            )
            assert public_ok is False

    # 3. Direct denials through real role logins (the narrow
    #    projections are the only exposure).
    login, password = database.credentials["slaif_review_worker"]
    worker = await _worker_login(database, login, password)
    try:
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await worker.fetchval(
                "SELECT count(*) FROM control.heading_review_retention"
            )
    finally:
        await worker.close()
    login, password = database.credentials["slaif_control"]
    control = await _control_login(database, login, password)
    try:
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await control.fetchval(
                "SELECT count(*) FROM control.heading_review_retention"
            )
    finally:
        await control.close()

    # 4. Downgrade ratchet: the operator path refuses at the
    #    bootstrap preflight; the direct Alembic 081 -> 080 step is
    #    refused by this migration's own body; the state is left
    #    exactly as found.
    async with _owner(database) as owner:
        before = await owner.fetchrow("SELECT version_num FROM control.alembic_version")
        assert before["version_num"] == "081_001"
        retention_rows = await owner.fetchval(
            "SELECT count(*) FROM control.heading_review_retention"
        )
    with pytest.raises(BootstrapStateError, match="retained heading review facts"):
        await downgrade(database.settings)
    with pytest.raises(DBAPIError) as direct_exc:
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="080_001",
        )
    underlying = direct_exc.value.orig
    assert "HEADING_RETENTION_DOWNGRADE_UNSUPPORTED" in str(underlying)
    assert getattr(underlying, "sqlstate", None) == "P0001"
    async with _owner(database) as owner:
        after = await owner.fetchrow("SELECT version_num FROM control.alembic_version")
        assert after["version_num"] == "081_001"
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM control.heading_review_retention"
            )
            == retention_rows
        )
        assert await owner.fetchval(
            "SELECT to_regprocedure("
            " 'control.slaif_review_retain_heading_facts(uuid,uuid)')"
            " IS NOT NULL"
        )
        assert await owner.fetchval(
            "SELECT to_regprocedure("
            " 'control.slaif_review_heading_effects_read"
            "(uuid,uuid,uuid,uuid)') IS NOT NULL"
        )


async def _worker_login(database: AgentSiteDatabase, login: str, password: str) -> Any:
    """A real role login (fixture-owned credentials only)."""

    host = str(database.connection_parameters["host"])
    port = int(database.connection_parameters["port"])
    return await asyncpg.connect(
        host=host,
        port=port,
        user=login,
        password=password,
        database=database.name,
    )


async def _control_login(database: AgentSiteDatabase, login: str, password: str) -> Any:
    return await _worker_login(database, login, password)
