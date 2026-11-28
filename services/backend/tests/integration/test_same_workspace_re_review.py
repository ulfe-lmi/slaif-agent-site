"""084/1: the same-workspace overlapping Heading conflict gate.

One whole-session scenario: two same-site workspaces W and X edit the
same Heading differently at canonical revision A through actual Agent
mutation contexts (distinct capability contexts and operation IDs),
both freeze against A, X publishes B, and W's A approval fails with
the durable SITE_REVISION_CHANGED drift.  A real human re-review of W
then re-freezes W against B through the verified stale-revision
transition (both snapshots retained), and W's B approval reaches the
existing whole-session conflict_policy="error" promotion boundary
(BASE_ROW_CHANGED, CONFLICTED) with zero canonical effect.  The
endpoint gate matrix, the legacy-freeze retry guard, the
concurrent-replay single-live-job property and the guarded downgrade
round out the increment.

The scenario edits, freeze, re-review and accept all run through the
product surfaces (real Control definer entry points for the human
authority, the real Agent mutation executor for the COW edits, the
real review worker claim + run for both job kinds); independent
owner reads observe the exact evidence only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.bootstrap.service import (
    BootstrapStateError,
    downgrade,
)
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration
from slaif_agent_site.review_worker.accept_job import MediaBoundary, run_accept_job
from slaif_agent_site.review_worker.freeze_job import run_freeze_job
from sqlalchemy.exc import DBAPIError
from test_freeze_review_snapshot import (
    _AGGON2,
    _control_call,
    _control_http,
    _cow_update,
    _create_workspace,
    _digest_is_valid,
    _freeze_claim_run,
    _mutation_headers,
    _public_conflicts,
    _public_operations,
    _session_cookie,
    _snapshot_heading_texts,
    _worker_call,
    _worker_pool,
    _worker_settings,
)
from test_real_human_accept import (
    _claim_accept,
    _media_settings,
    _seed_site,
)


def _values(rows: list[Any]) -> list[tuple[Any, ...]]:
    return [tuple(row) for row in rows]


async def _snapshots(database: AgentSiteDatabase, workspace_id: UUID) -> list[Any]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return list(
            await owner.fetch(
                "SELECT * FROM control.review_snapshot"
                " WHERE workspace_id = $1 ORDER BY created_at, id",
                workspace_id,
            )
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
    assert row is not None
    return str(row["status"]), row["review_snapshot_id"]


async def _retention_rows(database: AgentSiteDatabase, snapshot_id: UUID) -> list[Any]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return list(
            await owner.fetch(
                "SELECT * FROM control.heading_review_retention WHERE snapshot_id = $1",
                snapshot_id,
            )
        )


async def _heading_row_effects(
    database: AgentSiteDatabase,
    site_id: UUID,
    workspace_id: UUID,
    component_id: UUID,
) -> list[tuple[Any, ...]]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        rows = await owner.fetch(
            "SELECT * FROM audit.heading_row_effect"
            " WHERE site_id = $1 AND workspace_id = $2"
            " AND component_id = $3 ORDER BY operation_id",
            site_id,
            workspace_id,
            component_id,
        )
    return _values(rows)


def _props_obj(value: Any) -> dict[str, Any]:
    """Canonical props arrive as jsonb or its JSON text form."""
    if isinstance(value, str):
        parsed: dict[str, Any] = json.loads(value)
        return parsed
    return dict(value)


async def _revision(database: AgentSiteDatabase, site_id: UUID) -> int:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return int(
            await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                site_id,
            )
        )


async def _composition_fingerprint(database: AgentSiteDatabase) -> str:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return str(
            await owner.fetchval(
                "SELECT encode(sha256(convert_to(string_agg("
                " component_type || '|' || props::text || '|'"
                " || row_version::text, '' ORDER BY id),'UTF8')),"
                " 'hex') FROM content.page_composition_base"
            )
        )


async def _publication_counters(database: AgentSiteDatabase) -> tuple[int, int]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        audit = int(await owner.fetchval("SELECT count(*) FROM audit.promotion"))
        outbox = int(await owner.fetchval("SELECT count(*) FROM control.cache_outbox"))
    return audit, outbox


async def _manifest_digest(database: AgentSiteDatabase, snapshot_id: UUID) -> str:
    rows = await _control_call(
        database,
        "SELECT control.slaif_review_operation_manifest_read($1)",
        snapshot_id,
    )
    document = rows[0][0]
    if isinstance(document, (str, bytes)):
        document = json.loads(
            document.decode() if isinstance(document, bytes) else document
        )
    return str(document["manifest_digest"])


async def _freeze_run(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    site_id: UUID,
    delegator_id: UUID,
    pool: Any,
    claimant: str,
) -> UUID:
    result, job_id = await _freeze_claim_run(
        database,
        workspace_id=workspace_id,
        site_id=site_id,
        delegator_id=delegator_id,
        pool=pool,
        claimant=claimant,
    )
    assert result.status == "SUCCEEDED", result.error
    return job_id


async def _human_accept_enqueue(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    site_id: UUID,
    actor: UUID,
    snapshot_id: UUID,
    snapshot_digest: str,
    manifest_digest: str,
) -> list[Any]:
    """The real human Control accept entry (slaif_control login)."""

    return await _control_call(
        database,
        "SELECT * FROM control.slaif_human_agent_workspace_accept($1,$2,$3,$4,$5,$6)",
        workspace_id,
        site_id,
        snapshot_id,
        snapshot_digest,
        manifest_digest,
        actor,
    )


async def _human_re_review(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    site_id: UUID,
    actor: UUID,
    snapshot_id: UUID,
) -> list[Any]:
    """The real human Control re-review entry (slaif_control login)."""

    return await _control_call(
        database,
        "SELECT * FROM control.slaif_human_agent_workspace_re_review($1,$2,$3,$4)",
        workspace_id,
        site_id,
        snapshot_id,
        actor,
    )


@pytest.mark.asyncio
async def test_same_workspace_overlap_re_review_conflict_lifecycle(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """The whole-session overlapping Heading scenario (criteria 1-4)."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    owner_dsn = database.settings.resolved_owner_dsn()
    try:
        site_id: UUID = ids["site_id"]
        delegator_id: UUID = ids["delegator_id"]
        w_ws: UUID = ids["workspace_id"]
        w_cap: UUID = ids["capability_id"]
        heading_id: UUID = ids["heading_id"]

        A = await _revision(database, site_id)
        assert A == 0

        # ---------------- criterion 1: W and X edit the SAME heading
        # differently at A through actual Agent mutation contexts
        # (distinct capabilities -> distinct operation IDs).
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            x_ws, x_cap = await _create_workspace(
                owner, site_id, delegator_id, "084/1 X"
            )
        await _cow_update(
            database,
            workspace_id=w_ws,
            capability_id=w_cap,
            site_id=site_id,
            component_id=heading_id,
            props={"level": 2, "text": "084/1 W edit"},
        )
        await _cow_update(
            database,
            workspace_id=x_ws,
            capability_id=x_cap,
            site_id=site_id,
            component_id=heading_id,
            props={"level": 1, "text": "084/1 X edit"},
        )
        w_ops = await _public_operations(database, w_ws)
        x_ops = await _public_operations(database, x_ws)
        assert len(w_ops) == 1
        assert len(x_ops) == 1
        assert w_ops[0] != x_ops[0]

        # Human freezes both against A (real human definer + worker).
        await _freeze_run(
            database,
            workspace_id=w_ws,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="084-1-freeze-w",
        )
        await _freeze_run(
            database,
            workspace_id=x_ws,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="084-1-freeze-x",
        )
        w_state, w_pointer = await _workspace_state(database, w_ws)
        x_state, x_pointer = await _workspace_state(database, x_ws)
        assert w_state == "REVIEW" and x_state == "REVIEW"
        assert w_pointer is not None and x_pointer is not None
        snap_w = await _snapshots(database, w_ws)
        snap_x = await _snapshots(database, x_ws)
        assert len(snap_w) == 1 and len(snap_x) == 1
        snap_w_id: UUID = UUID(str(snap_w[0]["id"]))
        snap_x_id: UUID = UUID(str(snap_x[0]["id"]))
        assert w_pointer == snap_w_id and x_pointer == snap_x_id
        w_digest = str(snap_w[0]["digest"])
        x_digest = str(snap_x[0]["digest"])
        assert json.loads(snap_w[0]["payload"])["base_site_revision"] == A
        assert json.loads(snap_x[0]["payload"])["base_site_revision"] == A
        assert await _digest_is_valid(database, snap_w_id)
        assert await _digest_is_valid(database, snap_x_id)
        w_texts = await _snapshot_heading_texts(database, snap_w_id)
        x_texts = await _snapshot_heading_texts(database, snap_x_id)
        assert "084/1 W edit" in w_texts
        assert "084/1 X edit" in x_texts
        w_retention = await _retention_rows(database, snap_w_id)
        x_retention = await _retention_rows(database, snap_x_id)
        assert len(w_retention) == 1 and len(x_retention) == 1
        w_retention_facts_digest = str(w_retention[0]["facts_digest"])
        w_payload_before = str(snap_w[0]["payload"])
        w_effects_before = await _heading_row_effects(
            database, site_id, w_ws, heading_id
        )
        assert len(w_effects_before) == 1

        # And the no-matching-failure negative: a fresh workspace that
        # froze but never had a failed accept cannot be re-reviewed
        # (pointer alone proves eligibility, never staleness).
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            fresh_ws, fresh_cap = await _create_workspace(
                owner, site_id, delegator_id, "084/1 fresh"
            )
        await _cow_update(
            database,
            workspace_id=fresh_ws,
            capability_id=fresh_cap,
            site_id=site_id,
            component_id=heading_id,
            props={"level": 3, "text": "084/1 fresh edit"},
        )
        await _freeze_run(
            database,
            workspace_id=fresh_ws,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="084-1-freeze-fresh",
        )
        fresh_pointer = (await _workspace_state(database, fresh_ws))[1]
        assert fresh_pointer is not None
        with pytest.raises(asyncpg.PostgresError) as unverified_exc:
            async with owner_connection(
                owner_dsn, expected_database=database.name
            ) as owner:
                await owner.fetch(
                    "SELECT * FROM control.slaif_workspace_re_review($1,$2)",
                    fresh_ws,
                    fresh_pointer,
                )
        assert "RE_REVIEW_STALE_REVISION_UNVERIFIED" in str(unverified_exc.value)
        assert unverified_exc.value.sqlstate == "P0003"
        with pytest.raises(asyncpg.PostgresError) as unverified_human_exc:
            await _human_re_review(
                database,
                workspace_id=fresh_ws,
                site_id=site_id,
                actor=delegator_id,
                snapshot_id=fresh_pointer,
            )
        assert "RE_REVIEW_STALE_REVISION_UNVERIFIED" in str(unverified_human_exc.value)
        assert unverified_human_exc.value.sqlstate == "P0003"
        assert (await _workspace_state(database, fresh_ws))[0] == "REVIEW"

        # ---------------- criterion 2: approve X (real human entry +
        # real worker); the canonical B reflects ONLY X's edit.
        x_approval_rows = await _human_accept_enqueue(
            database,
            workspace_id=x_ws,
            site_id=site_id,
            actor=delegator_id,
            snapshot_id=snap_x_id,
            snapshot_digest=x_digest,
            manifest_digest=await _manifest_digest(database, snap_x_id),
        )
        assert len(x_approval_rows) == 1
        x_job_id = UUID(str(x_approval_rows[0]["job_id"]))
        x_job = await _claim_accept(database, "084-1-accept-x")
        assert UUID(str(x_job["id"])) == x_job_id
        x_result = await run_accept_job(
            pool, _worker_settings(database), x_job, media=boundary
        )
        assert x_result.status == "SUCCEEDED", x_result.error
        B = await _revision(database, site_id)
        assert B == A + 1
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            canonical = await owner.fetchrow(
                "SELECT props, row_version FROM content.page_composition_base"
                " WHERE id = $1",
                heading_id,
            )
        assert canonical is not None
        assert _props_obj(canonical["props"]) == {"level": 1, "text": "084/1 X edit"}
        assert int(canonical["row_version"]) == 2
        x_state2, _ = await _workspace_state(database, x_ws)
        assert x_state2 == "ACCEPTED"

        # W's pending op now conflicts on the first-touched row.
        w_conflicts = await _public_conflicts(database, w_ws)
        assert len(w_conflicts) == 1
        assert w_conflicts[0]["conflict_kind"] == "BASE_ROW_CHANGED"
        assert w_conflicts[0]["table_name"] == "page_composition"
        assert w_conflicts[0]["primary_key"]["id"] == str(heading_id)

        # Attempt the same real approval path for W's A snapshot: the
        # durable outcome is SITE_REVISION_CHANGED, W is back in
        # read-only review, its edit and original snapshot are intact,
        # and nothing was published from W.
        audit_before_w, outbox_before_w = await _publication_counters(database)
        w_approval_rows = await _human_accept_enqueue(
            database,
            workspace_id=w_ws,
            site_id=site_id,
            actor=delegator_id,
            snapshot_id=snap_w_id,
            snapshot_digest=w_digest,
            manifest_digest=await _manifest_digest(database, snap_w_id),
        )
        assert len(w_approval_rows) == 1
        w_job_id = UUID(str(w_approval_rows[0]["job_id"]))
        w_job = await _claim_accept(database, "084-1-accept-w-stale")
        assert UUID(str(w_job["id"])) == w_job_id
        w_stale_result = await run_accept_job(
            pool, _worker_settings(database), w_job, media=boundary
        )
        assert w_stale_result.status == "FAILED", w_stale_result.error
        assert w_stale_result.error == "SITE_REVISION_CHANGED"
        w_state, w_pointer2 = await _workspace_state(database, w_ws)
        assert w_state == "REVIEW"
        assert w_pointer2 == snap_w_id
        assert await _revision(database, site_id) == B
        audit_after_w, outbox_after_w = await _publication_counters(database)
        assert (audit_after_w, outbox_after_w) == (
            audit_before_w,
            outbox_before_w,
        )
        assert await _public_operations(database, w_ws) == w_ops
        w_snap_still = await _snapshots(database, w_ws)
        assert len(w_snap_still) == 1
        assert str(w_snap_still[0]["payload"]) == w_payload_before
        assert await _digest_is_valid(database, snap_w_id)
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            w_job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                w_job_id,
            )
        assert w_job_row is not None
        assert str(w_job_row["status"]) == "FAILED"
        assert str(w_job_row["error"]) == "SITE_REVISION_CHANGED"

        # ---------------- criterion 3: the human re-review of W.
        # Negative first: naming a snapshot that is not the trusted
        # current pointer is a typed stale refusal (X's snapshot),
        # propagated typed at the human surface and whitebox-verifiable
        # as the owner on the owner-internal helper.
        with pytest.raises(asyncpg.PostgresError) as stale_exc:
            await _human_re_review(
                database,
                workspace_id=w_ws,
                site_id=site_id,
                actor=delegator_id,
                snapshot_id=snap_x_id,
            )
        assert "REVIEW_REVIEW_SNAPSHOT_STALE" in str(stale_exc.value)
        assert stale_exc.value.sqlstate == "P0003"
        with pytest.raises(asyncpg.PostgresError) as stale_inner_exc:
            async with owner_connection(
                owner_dsn, expected_database=database.name
            ) as owner:
                await owner.fetch(
                    "SELECT * FROM control.slaif_workspace_re_review($1,$2)",
                    w_ws,
                    snap_x_id,
                )
        assert "REVIEW_REVIEW_SNAPSHOT_STALE" in str(stale_inner_exc.value)
        assert stale_inner_exc.value.sqlstate == "P0003"

        # The real re-review of W (verified stale: the durable
        # SITE_REVISION_CHANGED job for the exact snapshot + digests).
        re_review_rows = await _human_re_review(
            database,
            workspace_id=w_ws,
            site_id=site_id,
            actor=delegator_id,
            snapshot_id=snap_w_id,
        )
        assert len(re_review_rows) == 1
        assert str(re_review_rows[0]["status"]) == "FREEZING"
        rr_job_id = UUID(str(re_review_rows[0]["job_id"]))
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            rr_payload = await owner.fetchval(
                "SELECT payload FROM control.review_job WHERE id = $1",
                rr_job_id,
            )
        rr_payload_doc = json.loads(rr_payload)
        assert rr_payload_doc["re_review"] is True
        assert rr_payload_doc["previous_snapshot_id"] == str(snap_w_id)

        # Concurrent repeat while FREEZING: the SAME live job is
        # returned; no second live job is created.  A different
        # snapshot name in this state is still stale.
        repeat_rows = await _human_re_review(
            database,
            workspace_id=w_ws,
            site_id=site_id,
            actor=delegator_id,
            snapshot_id=snap_w_id,
        )
        assert len(repeat_rows) == 1
        assert UUID(str(repeat_rows[0]["job_id"])) == rr_job_id
        with pytest.raises(asyncpg.PostgresError) as stale_rr_exc:
            await _human_re_review(
                database,
                workspace_id=w_ws,
                site_id=site_id,
                actor=delegator_id,
                snapshot_id=snap_x_id,
            )
        assert "REVIEW_REVIEW_SNAPSHOT_STALE" in str(stale_rr_exc.value)
        assert stale_rr_exc.value.sqlstate == "P0003"

        # The legacy freeze retry cannot queue a replacement unbound
        # FREEZE for the re-review in flight (pointer set).
        with pytest.raises(asyncpg.PostgresError) as legacy_human_exc:
            await _control_call(
                database,
                "SELECT * FROM control.slaif_human_agent_workspace_freeze($1,$2,$3)",
                w_ws,
                site_id,
                delegator_id,
            )
        assert "WORKSPACE_NOT_ACTIVE" in str(legacy_human_exc.value)
        assert legacy_human_exc.value.sqlstate == "P0002"
        with pytest.raises(asyncpg.PostgresError) as legacy_exc:
            await _control_call(
                database,
                "SELECT * FROM control.slaif_workspace_freeze($1)",
                w_ws,
            )
        assert "WORKSPACE_NOT_ACTIVE" in str(legacy_exc.value)
        assert legacy_exc.value.sqlstate == "P0002"

        # Roll the finalization back for real: a broken base node
        # refuses the whole locked freeze (labeled fixture
        # corruption, removed before the retry).
        evil_node = uuid4()
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.page_composition_base (id, site_id,"
                " page_id, component_type, schema_version, parent_id,"
                " slot_key, order_key, props) VALUES ($1,$2,$3,"
                " 'EvilComponent','1',NULL,'default',5,'{}'::jsonb)",
                evil_node,
                site_id,
                ids["page_id"],
            )
        rr_freeze_rows = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "084-1-rr-worker",
            ["FREEZE", "ACCEPT"],
        )
        assert len(rr_freeze_rows) == 1
        assert UUID(str(rr_freeze_rows[0]["id"])) == rr_job_id
        rr_failed = await run_freeze_job(
            pool, _worker_settings(database), dict(rr_freeze_rows[0])
        )
        assert rr_failed.status == "FAILED", rr_failed.error
        assert rr_failed.error == "SNAPSHOT_VALIDATION_FAILED"
        # Atomic rollback: no new snapshot, pointer unchanged, no
        # REVIEW state; the job is terminal FAILED.
        w_state, w_pointer3 = await _workspace_state(database, w_ws)
        assert w_state == "FREEZING"
        assert w_pointer3 == snap_w_id
        assert len(await _snapshots(database, w_ws)) == 1
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            await owner.execute(
                "DELETE FROM content.page_composition_base WHERE id = $1",
                evil_node,
            )

        # Operational retry: the same re-review request (same
        # snapshot) accepts exactly one new job after the rollback.
        retry_rows = await _human_re_review(
            database,
            workspace_id=w_ws,
            site_id=site_id,
            actor=delegator_id,
            snapshot_id=snap_w_id,
        )
        assert len(retry_rows) == 1
        retry_job_id = UUID(str(retry_rows[0]["job_id"]))
        assert retry_job_id != rr_job_id
        rr_retry_rows = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "084-1-rr-worker-retry",
            ["FREEZE", "ACCEPT"],
        )
        assert len(rr_retry_rows) == 1
        assert UUID(str(rr_retry_rows[0]["id"])) == retry_job_id
        rr_retry_result = await run_freeze_job(
            pool, _worker_settings(database), dict(rr_retry_rows[0])
        )
        assert rr_retry_result.status == "SUCCEEDED", rr_retry_result.error

        # The new snapshot: pointer advanced atomically, coherent
        # base B, W's edit retained; the A snapshot, payload, digest
        # and per-snapshot companion evidence are byte-for-byte
        # retained.
        w_state, w_pointer4 = await _workspace_state(database, w_ws)
        assert w_state == "REVIEW"
        assert w_pointer4 is not None
        snap_w_rows = await _snapshots(database, w_ws)
        assert len(snap_w_rows) == 2
        snap_w2_id: UUID = w_pointer4
        assert snap_w2_id != snap_w_id
        snap_w2 = next(s for s in snap_w_rows if s["id"] == snap_w2_id)
        snap_w0 = next(s for s in snap_w_rows if s["id"] == snap_w_id)
        assert str(snap_w0["payload"]) == w_payload_before
        assert str(snap_w0["digest"]) == w_digest
        assert await _digest_is_valid(database, snap_w2_id)
        assert json.loads(snap_w2["payload"])["base_site_revision"] == B
        w2_texts = await _snapshot_heading_texts(database, snap_w2_id)
        assert "084/1 W edit" in w2_texts
        # The freeze reads the composition under the workspace
        # session: W's overlay row replaces the canonical B row for
        # that component (X's published edit stays canonical but is
        # covered here).  The new snapshot shows exactly W's pending
        # props for the shared Heading.
        w2_compositions = json.loads(snap_w2["payload"])["page_compositions"]
        w2_heading_rows = [
            row for row in w2_compositions if row["id"] == str(heading_id)
        ]
        assert len(w2_heading_rows) == 1
        assert _props_obj(w2_heading_rows[0]["props"]) == {
            "level": 2,
            "text": "084/1 W edit",
        }
        w2_retention = await _retention_rows(database, snap_w2_id)
        assert len(w2_retention) == 1
        w0_retention_after = await _retention_rows(database, snap_w_id)
        assert len(w0_retention_after) == 1
        assert str(w0_retention_after[0]["facts_digest"]) == (w_retention_facts_digest)
        # The first-touch row effects persist for W's operation.
        w_effects_now = await _heading_row_effects(database, site_id, w_ws, heading_id)
        assert w_effects_now == w_effects_before
        # Capabilities stay revoked; the workspace stays closed.
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            live_caps = await owner.fetchval(
                "SELECT count(*) FROM control.capability"
                " WHERE workspace_id = $1 AND revoked_at IS NULL",
                w_ws,
            )
        assert live_caps == 0

        # The regular human review read follows the trusted current
        # pointer (the 082 read-model revision).
        review_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_review_read_model($1,$2,$3)",
            w_ws,
            site_id,
            delegator_id,
        )
        review_doc = json.loads(review_rows[0][0])
        assert review_doc["snapshot"]["id"] == str(snap_w2_id)
        assert int(review_doc["snapshot"]["base_site_revision"]) == B
        assert review_doc["drift"]["equal"] is True
        # The unqualified heading-effects read follows the pointer;
        # the exact prior snapshot still renders with its ORIGINAL
        # retention evidence (081 exact-snapshot read, unchanged).
        effects_now = json.loads(
            (
                await _control_call(
                    database,
                    "SELECT * FROM control.slaif_review_heading_effects_read"
                    "($1,$2,$3,$4)",
                    w_ws,
                    site_id,
                    None,
                    delegator_id,
                )
            )[0][0]
        )
        assert effects_now["status"] == "captured"
        assert effects_now["snapshot_id"] == str(snap_w2_id)
        effects_old = json.loads(
            (
                await _control_call(
                    database,
                    "SELECT * FROM control.slaif_review_heading_effects_read"
                    "($1,$2,$3,$4)",
                    w_ws,
                    site_id,
                    snap_w_id,
                    delegator_id,
                )
            )[0][0]
        )
        assert effects_old["status"] == "captured"
        assert effects_old["snapshot_id"] == str(snap_w_id)
        # Both snapshots reviewed the SAME operation, so both retain
        # the same recorded facts (per-snapshot rows, same evidence).
        assert effects_old["facts"] == effects_now["facts"]
        # A missing pointer fails closed (uniform gate): a workspace
        # with no snapshot never renders a review document.
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            bare_ws = await owner.fetchval(
                "INSERT INTO control.workspace (site_id, created_by,"
                " delegator_id, title, delegation_preset,"
                " effective_scopes, version_facts, status, expires_at)"
                " VALUES ($1,$2,$2,'084/1 bare','L4','[\"page:read\"]'::jsonb,"
                ' \'{"catalog":"catalog-v1",'
                ' "composition_schema":"site-composition/v1",'
                ' "content_model":"content-model/v1",'
                ' "design_system":"design-system/v1",'
                ' "puck":"0.20.2","renderer":"renderer-v1"}\'::jsonb,'
                " 'REVIEW', now()+interval '1 hour') RETURNING id",
                site_id,
                delegator_id,
            )
        with pytest.raises(asyncpg.PostgresError) as closed_exc:
            await _control_call(
                database,
                "SELECT * FROM control.slaif_review_read_model($1,$2,$3)",
                bare_ws,
                site_id,
                delegator_id,
            )
        assert "REVIEW_READ_UNAVAILABLE" in str(closed_exc.value)

        # ---------------- criterion 4: old identity refused WITHOUT a
        # new approval job; the B snapshot approval reaches the
        # existing conflict_policy="error" boundary.
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            job_count_before = int(
                await owner.fetchval(
                    "SELECT count(*) FROM control.review_job"
                    " WHERE workspace_id = $1 AND job_kind = 'ACCEPT'",
                    w_ws,
                )
            )
        old_rows = await _human_accept_enqueue(
            database,
            workspace_id=w_ws,
            site_id=site_id,
            actor=delegator_id,
            snapshot_id=snap_w_id,
            snapshot_digest=w_digest,
            manifest_digest=await _manifest_digest(database, snap_w_id),
        )
        assert old_rows == []  # uniform silent refusal (HTTP 404)
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            job_count_after_old = int(
                await owner.fetchval(
                    "SELECT count(*) FROM control.review_job"
                    " WHERE workspace_id = $1 AND job_kind = 'ACCEPT'",
                    w_ws,
                )
            )
        assert job_count_after_old == job_count_before

        audit_before_c, outbox_before_c = await _publication_counters(database)
        fingerprint_b = await _composition_fingerprint(database)
        w2_rows = await _human_accept_enqueue(
            database,
            workspace_id=w_ws,
            site_id=site_id,
            actor=delegator_id,
            snapshot_id=snap_w2_id,
            snapshot_digest=str(snap_w2["digest"]),
            manifest_digest=await _manifest_digest(database, snap_w2_id),
        )
        assert len(w2_rows) == 1
        w2_job_id = UUID(str(w2_rows[0]["job_id"]))
        w2_job = await _claim_accept(database, "084-1-accept-w-b")
        assert UUID(str(w2_job["id"])) == w2_job_id
        w2_result = await run_accept_job(
            pool, _worker_settings(database), w2_job, media=boundary
        )
        assert w2_result.status == "FAILED", w2_result.error
        assert w2_result.error == "BASE_ROW_CHANGED"
        w_state, w_pointer5 = await _workspace_state(database, w_ws)
        assert w_state == "CONFLICTED"
        assert w_pointer5 == snap_w2_id
        # Zero canonical mutation from W; the B row is exact.
        assert await _composition_fingerprint(database) == fingerprint_b
        assert await _revision(database, site_id) == B
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            canonical2 = await owner.fetchrow(
                "SELECT props, row_version FROM content.page_composition_base"
                " WHERE id = $1",
                heading_id,
            )
        assert canonical2 is not None
        assert _props_obj(canonical2["props"]) == {"level": 1, "text": "084/1 X edit"}
        assert int(canonical2["row_version"]) == 2
        audit_after_c, outbox_after_c = await _publication_counters(database)
        assert (audit_after_c, outbox_after_c) == (
            audit_before_c,
            outbox_before_c,
        )
        # Pending operations + first-touch evidence survive exactly.
        assert await _public_operations(database, w_ws) == w_ops
        w_conflicts_end = await _public_conflicts(database, w_ws)
        assert w_conflicts_end == w_conflicts
        # Both snapshot records + retained facts persist for W.
        assert len(await _snapshots(database, w_ws)) == 2
        assert await _digest_is_valid(database, snap_w_id)
        assert await _digest_is_valid(database, snap_w2_id)
        assert len(await _retention_rows(database, snap_w_id)) == 1
        assert len(await _retention_rows(database, snap_w2_id)) == 1
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_re_review_endpoint_http_gates_and_stale_matrix(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Criterion 5 gates: auth, CSRF, body, roles, site, states."""

    database = agent_site_database
    seeded = await _seed_site(database, media_root=None, with_ops=False)
    adapter, client = await _control_http(database)
    pool = await _worker_pool(database)
    try:
        site_id = seeded["site_id"]
        workspace_id = seeded["workspace_id"]
        delegator_id = seeded["delegator_id"]
        cookie, csrf = await _session_cookie(adapter, delegator_id)
        base = f"/api/control/v1/sites/{site_id}/workspaces/{workspace_id}/re-review/"
        happy = _mutation_headers(cookie, csrf)
        body = {"snapshot_id": str(uuid4())}

        # Unauthenticated and invalid-session attempts are uniform 401.
        for headers in ({}, {"cookie": "slaif_session=invalid"}):
            response = await client.post(base, headers=headers, json=body)
            assert response.status_code == 401

        # State-changing route without/with wrong CSRF: 403.
        response = await client.post(base, headers={"cookie": cookie}, json=body)
        assert response.status_code == 403
        response = await client.post(
            base,
            headers={"cookie": f"{cookie}; slaif_csrf=wrong", "x-csrf-token": "wrong"},
            json=body,
        )
        assert response.status_code == 403

        # Strict body: the exact one field, nothing else (422 shapes).
        response = await client.post(
            base, headers=happy, json={"snapshot_id": "not-a-uuid"}
        )
        assert response.status_code == 422
        response = await client.post(base, headers=happy, json={"snapshot_id": None})
        assert response.status_code == 422
        response = await client.post(base, headers=happy, json={**body, "extra": 1})
        assert response.status_code == 422

        # Unknown (well-formed) ids are 404; malformed path ids are 422.
        response = await client.post(
            f"/api/control/v1/sites/{site_id}/workspaces/{uuid4()}/re-review/",
            headers=happy,
            json=body,
        )
        assert response.status_code == 404
        response = await client.post(
            f"/api/control/v1/sites/{site_id}/workspaces/not-a-uuid/re-review/",
            headers=happy,
            json=body,
        )
        assert response.status_code == 422

        # A member without workspace:freeze and a non-member are denied
        # with the same uniform 404 shape (no oracle).
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            editor_id = await owner.fetchval(
                "INSERT INTO control.user_account (id, identity_kind, "
                "local_username, local_username_normalized, password_hash, "
                "display_name, status) VALUES (gen_random_uuid(), 'LOCAL', "
                "'ReReview.Integration.Editor', 'rereview.integration.editor', "
                "$1, 'ReReview Editor', 'ACTIVE') RETURNING id",
                _AGGON2,
            )
            nonmember_id = await owner.fetchval(
                "INSERT INTO control.user_account (id, identity_kind, "
                "local_username, local_username_normalized, password_hash, "
                "display_name, status) VALUES (gen_random_uuid(), 'LOCAL', "
                "'ReReview.Integration.Nonmember', "
                "'rereview.integration.nonmember', $1, 'ReReview Nonmember', "
                "'ACTIVE') RETURNING id",
                _AGGON2,
            )
            await owner.execute(
                "INSERT INTO control.site_membership (site_id,user_account_id,"
                " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_EDITOR',2)",
                site_id,
                editor_id,
            )
            other_site_id = await owner.fetchval(
                "INSERT INTO control.site (site_key, display_name, "
                "default_locale, component_catalog_version) VALUES "
                "('rereview-other', 'ReReview Other', 'en-US', 'catalog-v1') "
                "RETURNING id"
            )
            await owner.execute(
                "INSERT INTO control.site_membership (site_id,user_account_id,"
                " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
                other_site_id,
                delegator_id,
            )
        editor_cookie, editor_csrf = await _session_cookie(adapter, editor_id)
        editor_denial = await client.post(
            base, headers=_mutation_headers(editor_cookie, editor_csrf), json=body
        )
        assert editor_denial.status_code == 404
        nonmember_cookie, nonmember_csrf = await _session_cookie(adapter, nonmember_id)
        nonmember_denial = await client.post(
            base,
            headers=_mutation_headers(nonmember_cookie, nonmember_csrf),
            json=body,
        )
        assert nonmember_denial.status_code == 404
        editor_shape = editor_denial.json()
        nonmember_shape = nonmember_denial.json()
        editor_shape["error"].pop("request_id")
        nonmember_shape["error"].pop("request_id")
        assert editor_shape == nonmember_shape

        # Exact site binding: the workspace under another path site is
        # 404 even for its owner (fail-closed, no cross-site
        # substitution).
        response = await client.post(
            f"/api/control/v1/sites/{other_site_id}/workspaces/"
            f"{workspace_id}/re-review/",
            headers=happy,
            json=body,
        )
        assert response.status_code == 404

        # An ACTIVE (never-frozen) workspace has no current trusted
        # snapshot: any named snapshot is stale (typed 409).
        response = await client.post(base, headers=happy, json=body)
        assert response.status_code == 409
        with pytest.raises(asyncpg.PostgresError) as active_exc:
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.fetch(
                    "SELECT * FROM control.slaif_workspace_re_review($1,$2)",
                    workspace_id,
                    body["snapshot_id"],
                )
        assert "REVIEW_REVIEW_SNAPSHOT_STALE" in str(active_exc.value)

        # NULL snapshot input is a typed refusal before any state read
        # or row lock: a legacy null-pointer (pre-snapshot) FREEZING
        # workspace must never be selectable for re-review.
        with pytest.raises(asyncpg.PostgresError) as null_exc:
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.fetch(
                    "SELECT * FROM control.slaif_workspace_re_review($1, NULL)",
                    workspace_id,
                )
        assert null_exc.value.sqlstate == "P0002"
        assert "RE_REVIEW_SNAPSHOT_NULL" in str(null_exc.value)

        # A frozen-but-never-stale workspace (no failed SITE_
        # REVISION_CHANGED accept) refuses the unverified transition.
        result, _job_id = await _freeze_claim_run(
            database,
            workspace_id=workspace_id,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="084-1-gates-freeze",
        )
        assert result.status == "SUCCEEDED", result.error
        state, pointer = await _workspace_state(database, workspace_id)
        assert state == "REVIEW"
        assert pointer is not None
        response = await client.post(
            base, headers=happy, json={"snapshot_id": str(pointer)}
        )
        assert response.status_code == 409
        with pytest.raises(asyncpg.PostgresError) as unverified_exc:
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.fetch(
                    "SELECT * FROM control.slaif_workspace_re_review($1,$2)",
                    workspace_id,
                    str(pointer),
                )
        assert "RE_REVIEW_STALE_REVISION_UNVERIFIED" in str(unverified_exc.value)
        assert unverified_exc.value.sqlstate == "P0003"
        # Nothing transitioned.
        assert (await _workspace_state(database, workspace_id)) == (
            "REVIEW",
            pointer,
        )
        # A different named snapshot is stale, not unverified.
        with pytest.raises(asyncpg.PostgresError) as other_exc:
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.fetch(
                    "SELECT * FROM control.slaif_workspace_re_review($1,$2)",
                    workspace_id,
                    str(uuid4()),
                )
        assert "REVIEW_REVIEW_SNAPSHOT_STALE" in str(other_exc.value)
    finally:
        await pool.close()
        await client.aclose()
        await adapter.stop()


async def _reach_retained_two_snapshots(
    database: AgentSiteDatabase,
    *,
    media_root: Path,
    pool: Any,
    boundary: MediaBoundary,
) -> dict[str, Any]:
    """W and X edit one heading at A; X publishes B; W's A approval
    fails SITE_REVISION_CHANGED; W re-reviews to B.  Returns the W
    identity with two retained snapshots.  Raises with the workspace
    left FREEZING (re-review in flight) when ``leave_freezing`` is
    True (the worker run is the caller's)."""

    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    owner_dsn = database.settings.resolved_owner_dsn()
    site_id = ids["site_id"]
    delegator_id = ids["delegator_id"]
    w_ws = ids["workspace_id"]
    heading_id = ids["heading_id"]
    async with owner_connection(owner_dsn, expected_database=database.name) as owner:
        x_ws, x_cap = await _create_workspace(
            owner, site_id, delegator_id, "084/1 X-dg"
        )
    await _cow_update(
        database,
        workspace_id=w_ws,
        capability_id=ids["capability_id"],
        site_id=site_id,
        component_id=heading_id,
        props={"level": 2, "text": "084/1-dg W edit"},
    )
    await _cow_update(
        database,
        workspace_id=x_ws,
        capability_id=x_cap,
        site_id=site_id,
        component_id=heading_id,
        props={"level": 1, "text": "084/1-dg X edit"},
    )
    await _freeze_run(
        database,
        workspace_id=w_ws,
        site_id=site_id,
        delegator_id=delegator_id,
        pool=pool,
        claimant="084-1-dg-freeze-w",
    )
    await _freeze_run(
        database,
        workspace_id=x_ws,
        site_id=site_id,
        delegator_id=delegator_id,
        pool=pool,
        claimant="084-1-dg-freeze-x",
    )
    w_pointer = (await _workspace_state(database, w_ws))[1]
    x_pointer = (await _workspace_state(database, x_ws))[1]
    assert w_pointer is not None and x_pointer is not None
    async with owner_connection(owner_dsn, expected_database=database.name) as owner:
        w_digest = str(
            await owner.fetchval(
                "SELECT digest FROM control.review_snapshot WHERE id = $1",
                w_pointer,
            )
        )
        x_digest = str(
            await owner.fetchval(
                "SELECT digest FROM control.review_snapshot WHERE id = $1",
                x_pointer,
            )
        )
    x_rows = await _human_accept_enqueue(
        database,
        workspace_id=x_ws,
        site_id=site_id,
        actor=delegator_id,
        snapshot_id=x_pointer,
        snapshot_digest=x_digest,
        manifest_digest=await _manifest_digest(database, x_pointer),
    )
    assert len(x_rows) == 1
    x_job = await _claim_accept(database, "084-1-dg-accept-x")
    x_result = await run_accept_job(
        pool, _worker_settings(database), x_job, media=boundary
    )
    assert x_result.status == "SUCCEEDED", x_result.error
    w_rows = await _human_accept_enqueue(
        database,
        workspace_id=w_ws,
        site_id=site_id,
        actor=delegator_id,
        snapshot_id=w_pointer,
        snapshot_digest=w_digest,
        manifest_digest=await _manifest_digest(database, w_pointer),
    )
    assert len(w_rows) == 1
    w_job = await _claim_accept(database, "084-1-dg-accept-w")
    w_result = await run_accept_job(
        pool, _worker_settings(database), w_job, media=boundary
    )
    assert w_result.status == "FAILED", w_result.error
    assert w_result.error == "SITE_REVISION_CHANGED"
    rr_rows = await _human_re_review(
        database,
        workspace_id=w_ws,
        site_id=site_id,
        actor=delegator_id,
        snapshot_id=w_pointer,
    )
    assert len(rr_rows) == 1
    rr_job_id = UUID(str(rr_rows[0]["job_id"]))
    return {
        "ids": ids,
        "x_ws": x_ws,
        "w_ws": w_ws,
        "snap_w_id": w_pointer,
        "rr_job_id": rr_job_id,
    }


async def _run_claimed_freeze(
    database: AgentSiteDatabase,
    *,
    pool: Any,
    claimant: str,
    expected_job_id: UUID,
) -> Any:
    rows = await _worker_call(
        database,
        "SELECT * FROM control.slaif_review_job_claim($1, $2)",
        claimant,
        ["FREEZE", "ACCEPT"],
    )
    assert len(rows) == 1
    assert UUID(str(rows[0]["id"])) == expected_job_id
    return await run_freeze_job(pool, _worker_settings(database), dict(rows[0]))


@pytest.mark.asyncio
async def test_re_review_downgrade_refuses_multi_snapshot_atomic(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """The guarded downgrade: atomic refusal, state left exactly as
    found, for both the in-flight and the retained-multi-snapshot
    shapes (direct Alembic; the operator path refuses no later)."""

    database = agent_site_database
    media_root = tmp_path / "media"
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    owner_dsn = database.settings.resolved_owner_dsn()
    try:
        facts = await _reach_retained_two_snapshots(
            database,
            media_root=media_root,
            pool=pool,
            boundary=boundary,
        )
        w_ws = facts["w_ws"]
        assert (await _workspace_state(database, w_ws))[0] == "FREEZING"

        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            before = await owner.fetchrow(
                "SELECT version_num FROM control.alembic_version"
            )
            assert str(before["version_num"]) == "082_001"
            snapshot_bytes = await owner.fetch(
                "SELECT id, digest, payload FROM control.review_snapshot"
                " WHERE workspace_id = $1 ORDER BY id",
                w_ws,
            )
        assert len(snapshot_bytes) == 1  # in-flight: only the A snapshot

        # In-flight re-review (FREEZING with a current pointer):
        # refused before any effect.
        with pytest.raises(DBAPIError) as in_flight_exc:
            await run_migration(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
                operation="downgrade",
                revision="081_001",
            )
        assert "RE_REVIEW_DOWNGRADE_IN_FLIGHT" in str(in_flight_exc.value.orig)
        assert getattr(in_flight_exc.value.orig, "sqlstate", None) == "P0002"

        # Complete the re-review (two retained snapshots for W).
        result = await _run_claimed_freeze(
            database,
            pool=pool,
            claimant="084-1-dg-rr-worker",
            expected_job_id=facts["rr_job_id"],
        )
        assert result.status == "SUCCEEDED", result.error
        assert (await _workspace_state(database, w_ws))[0] == "REVIEW"
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            retained_bytes = await owner.fetch(
                "SELECT id, digest, payload FROM control.review_snapshot"
                " WHERE workspace_id = $1 ORDER BY id",
                w_ws,
            )
        assert len(retained_bytes) == 2

        # Retained multi-snapshot: refused before any effect, at the
        # same step, with the state left exactly as found.
        with pytest.raises(DBAPIError) as multi_exc:
            await run_migration(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
                operation="downgrade",
                revision="081_001",
            )
        underlying = multi_exc.value.orig
        assert "RE_REVIEW_DOWNGRADE_RETAINED_MULTI_SNAPSHOT" in str(underlying)
        assert getattr(underlying, "sqlstate", None) == "P0002"

        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            after = await owner.fetchrow(
                "SELECT version_num FROM control.alembic_version"
            )
            assert str(after["version_num"]) == "082_001"
            snapshot_bytes_after = await owner.fetch(
                "SELECT id, digest, payload FROM control.review_snapshot"
                " WHERE workspace_id = $1 ORDER BY id",
                w_ws,
            )
            assert snapshot_bytes_after == retained_bytes
            assert await owner.fetchval(
                "SELECT to_regprocedure('control.slaif_workspace_re_review"
                "(uuid,uuid)') IS NOT NULL"
            )
            assert await owner.fetchval(
                "SELECT to_regprocedure("
                "'control.slaif_human_agent_workspace_re_review"
                "(uuid,uuid,uuid,uuid)') IS NOT NULL"
            )
            read_model_src = await owner.fetchval(
                "SELECT pg_get_functiondef(p.oid) FROM pg_proc AS p"
                " JOIN pg_namespace AS n ON n.oid = p.pronamespace"
                " WHERE n.nspname = 'control' AND p.proname ="
                " 'slaif_review_read_model'"
            )
        assert "id = ws.review_snapshot_id" in str(read_model_src)

        # The operator path refuses no later than the direct path
        # (its preflight or the wrapped migration refusal), and the
        # state is left exactly as found either way.
        with pytest.raises(BootstrapStateError):
            await downgrade(database.settings)
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            after_op = await owner.fetchrow(
                "SELECT version_num FROM control.alembic_version"
            )
            assert str(after_op["version_num"]) == "082_001"
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_re_review_downgrade_safe_rollback_single_snapshot(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """The compatible rollback: single-snapshot state restores the
    exact 071/070 bodies (function-only), and the 081 ratchet remains
    the next line of defense."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    pool = await _worker_pool(database)
    owner_dsn = database.settings.resolved_owner_dsn()
    try:
        site_id = ids["site_id"]
        workspace_id = ids["workspace_id"]
        await _cow_update(
            database,
            workspace_id=workspace_id,
            capability_id=ids["capability_id"],
            site_id=site_id,
            component_id=ids["heading_id"],
            props={"level": 2, "text": "084/1-dg safe"},
        )
        await _freeze_run(
            database,
            workspace_id=workspace_id,
            site_id=site_id,
            delegator_id=ids["delegator_id"],
            pool=pool,
            claimant="084-1-dg-safe-freeze",
        )
        pointer = (await _workspace_state(database, workspace_id))[1]
        assert pointer is not None
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            snapshot_bytes = await owner.fetch(
                "SELECT id, digest, payload FROM control.review_snapshot"
                " WHERE workspace_id = $1 ORDER BY id",
                workspace_id,
            )
            assert len(snapshot_bytes) == 1

        # The compatible step runs: 082 -> 081, function-only.
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="081_001",
        )
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            after = await owner.fetchrow(
                "SELECT version_num FROM control.alembic_version"
            )
            assert str(after["version_num"]) == "081_001"
            snapshot_bytes_after = await owner.fetch(
                "SELECT id, digest, payload FROM control.review_snapshot"
                " WHERE workspace_id = $1 ORDER BY id",
                workspace_id,
            )
            assert snapshot_bytes_after == snapshot_bytes
            assert not await owner.fetchval(
                "SELECT to_regprocedure('control.slaif_workspace_re_review"
                "(uuid,uuid)') IS NOT NULL"
            )
            assert not await owner.fetchval(
                "SELECT to_regprocedure("
                "'control.slaif_human_agent_workspace_re_review"
                "(uuid,uuid,uuid,uuid)') IS NOT NULL"
            )
            read_model_src = str(
                await owner.fetchval(
                    "SELECT pg_get_functiondef(p.oid) FROM pg_proc AS p"
                    " JOIN pg_namespace AS n ON n.oid = p.pronamespace"
                    " WHERE n.nspname = 'control' AND p.proname ="
                    " 'slaif_review_read_model'"
                )
            )
            freeze_src = str(
                await owner.fetchval(
                    "SELECT pg_get_functiondef(p.oid) FROM pg_proc AS p"
                    " JOIN pg_namespace AS n ON n.oid = p.pronamespace"
                    " WHERE n.nspname = 'control' AND p.proname ="
                    " 'slaif_workspace_freeze'"
                )
            )
        # The restored 071 selection and 070 body (no 082 bytes).
        assert "id = ws.review_snapshot_id" not in read_model_src
        assert (
            "WHERE workspace_id = p_workspace_id AND status = 'COMPLETE';"
            in read_model_src
        )
        assert "082 guard" not in freeze_src
        assert "FOR UPDATE" not in freeze_src
        assert "SELECT status INTO ws_status" in freeze_src

        # The 081 ratchet remains the next line of defense.
        with pytest.raises(DBAPIError) as ratchet_exc:
            await run_migration(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
                operation="downgrade",
                revision="080_001",
            )
        assert "HEADING_RETENTION_DOWNGRADE_UNSUPPORTED" in str(ratchet_exc.value.orig)
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            after = await owner.fetchrow(
                "SELECT version_num FROM control.alembic_version"
            )
            assert str(after["version_num"]) == "081_001"
    finally:
        await pool.close()
