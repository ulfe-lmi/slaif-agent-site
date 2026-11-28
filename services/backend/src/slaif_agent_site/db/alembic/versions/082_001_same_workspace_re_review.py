# ruff: noqa: E501
"""Same-workspace overlapping Heading review: the human re-review.

083/4 proves stale-site-revision refusal and, separately,
``BASE_ROW_CHANGED`` when the losing workspace freezes for the FIRST
time after a sibling publication.  083/14 binds the recorded heading
row effects to each immutable snapshot with an authorized
current-pointer and exact-snapshot read.  This increment joins those
proofs through one same-workspace human re-review with both snapshots
retained:

* the workspace is in ``REVIEW`` with a trusted current pointer
  (``control.workspace.review_snapshot_id``) at snapshot A, and its
  real approval of A failed with the stable ``SITE_REVISION_CHANGED``
  drift code;
* a narrowly scoped durable transition moves it to ``FREEZING`` and
  enqueues the existing durable ``FREEZE`` job, so the existing
  exclusive workspace lock, claim, verified freeze materialization,
  snapshot-completion and retention path run unchanged;
* completion atomically points the current review at the new
  immutable snapshot (the existing 070/076 completion transition,
  unchanged), while the A snapshot, stored payload, digests and
  per-snapshot companion evidence are retained byte-for-byte;
* a stale re-review request (one naming a snapshot the trusted
  pointer no longer selects) is a typed refusal
  (``REVIEW_REVIEW_SNAPSHOT_STALE``, P0003);
* a re-review whose stale revision is not verified by the durable
  failed accept job is a typed refusal
  (``RE_REVIEW_STALE_REVISION_UNVERIFIED``, P0003);
* an operational retry after a rolled-back finalization (a FREEZING
  workspace still pointing at the named snapshot with no live FREEZE
  job) accepts exactly one new job; the partial unique index keeps at
  most one live FREEZE job, so a concurrent repeat returns the same
  live job instead of creating a second.

Smallest necessary Control and SQL changes, nothing else:

1. Two new owner-definer functions:

   - ``control.slaif_workspace_re_review(uuid, uuid)`` - the inner
     transition (owner-internal, NO role EXECUTE grants, mirroring
     the 079 inner accept).  A NULL snapshot is a typed refusal
     (``RE_REVIEW_SNAPSHOT_NULL``, P0002) before any state read or
     row lock, so a legacy null-pointer freeze is never selected for
     same-workspace re-review.  It then serializes on the workspace
     row for the whole transition (``FOR UPDATE``), verifies the
     current pointer, and - before any state change - requires the
     VERIFIED stale-revision gate: the current COMPLETE snapshot bound
     to this site/workspace plus a FAILED real ACCEPT job for that
     exact site/workspace/snapshot whose durable approval (both
     digests) matches the stored snapshot digest and the companion
     manifest digest, with the stable ``SITE_REVISION_CHANGED`` code.
     A current pointer alone proves eligibility, never staleness.

   - ``control.slaif_human_agent_workspace_re_review(uuid, uuid,
     uuid, uuid)`` - the human Control entry (EXECUTE for
     ``slaif_control`` only): the exact site binding, the SAME
     ``workspace:freeze`` authority as the original freeze (no new
     scope, no widening), then the inner transition.

2. A CREATE OR REPLACE of ``control.slaif_workspace_freeze(uuid)``
   with the documented legacy-retry guard: a workspace with a current
   snapshot pointer is not a legacy-freeze target, so the legacy
   retry can no longer queue a replacement UNBOUND FREEZE job for a
   re-review in flight (its FREEZING state is re-review-derived; only
   a pre-snapshot freeze, NULL pointer, keeps the legacy retry).  The
   post-branch read takes the workspace row with ``FOR NO KEY
   UPDATE``, serializing the retry and live-job check against the
   snapshot completion transition on the same row while coexisting
   with the foreign-key key share an in-flight COW proposal writer
   holds on that row (a full ``FOR UPDATE`` would wait on it).  The
   successful ACTIVE enqueue additionally ends with an explicit
   ``RETURN``: the unmodified legacy body would fall through (RETURN
   QUERY does not terminate the function) into the guarded
   post-branch and its re-read of that row.  All other bytes of the
   070 body are preserved.

3. A CREATE OR REPLACE of ``control.slaif_review_read_model`` whose
   ONLY change is selecting the snapshot through the trusted current
   pointer (scoped by site and workspace) instead of any COMPLETE
   snapshot of the workspace: with two retained snapshots the 071
   selection is ambiguous - PL/pgSQL ``SELECT ... INTO`` without
   ``STRICT`` silently assigns the FIRST row - while the pointer
   selection is the same fail-closed uniform-404 gate on a missing
   or mismatched pointer.

No other function, grant, table, worker path or job kind changes.

Downgrade compatibility guard: the downgrade is function-only and
never touches snapshot, retention, job, capability or workspace
state (retained rows survive byte-for-byte).  It REFUSES before any
effect (atomically) when a re-review retained multiple snapshots for
a workspace, or a re-review is still in flight (FREEZING with a
current pointer) - because the restored 071 selection would silently
render the first retained snapshot for such a workspace.  In a
single-snapshot-only state the rollback to 071 semantics is exact
(every workspace's 071 selection matches its trusted pointer), and
the 081 downgrade ratchet refuses any further step before the
earlier downgrades can see the retained snapshots.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

from alembic import op

revision = "082_001"
down_revision = "081_001"

# ---------------------------------------------------------------------------
# 071_001 read model re-emission (075/076 convention: the merged 071 bytes
# are preserved verbatim; the re-emitted statement differs only by the
# documented header keyword (CREATE FUNCTION -> CREATE OR REPLACE FUNCTION,
# so the existing object is replaced and prosrc is otherwise byte-identical
# to the 071 body) and, for the upgrade, the single documented
# snapshot-selection statement change.  The sha256 below is of the 071
# generated CREATE FUNCTION text at the verified base, so any drift of the
# historical source fails closed.
# ---------------------------------------------------------------------------

_READ_MODEL_MODULE_NAME = "071_001_review_surface_read_model.py"
_BASE_READ_MODEL_SHA256 = (
    "c2e1086d6128ca1299028ba9f4c0716504de92d7544fd52dd6681736f68e68f7"
)
_READ_MODEL_CREATE = "CREATE FUNCTION control.slaif_review_read_model("
_READ_MODEL_CREATE_OR_REPLACE = (
    "CREATE OR REPLACE FUNCTION control.slaif_review_read_model("
)

# The 071 single-snapshot selection (byte-exact at the base):
_OLD_SNAPSHOT_SELECTION = (
    "            SELECT * INTO snapshot_row FROM control.review_snapshot\n"
    "            WHERE workspace_id = p_workspace_id AND status = 'COMPLETE';"
)

# The 082 trusted-pointer selection (scoped by site and workspace):
_POINTER_SNAPSHOT_SELECTION = (
    "            SELECT * INTO snapshot_row FROM control.review_snapshot\n"
    "            WHERE id = ws.review_snapshot_id\n"
    "              AND workspace_id = p_workspace_id\n"
    "              AND site_id = ws.site_id\n"
    "              AND status = 'COMPLETE';"
)


def _read_model_sql(pointer: bool) -> str:
    """The exact 071_001 read model, or its 082 pointer revision.

    Both directions replace the EXISTING function object, so the
    generated plain ``CREATE FUNCTION`` header is re-emitted as
    ``CREATE OR REPLACE FUNCTION`` (header keyword only; the $fn$
    body is byte-identical, so prosrc is byte-identical) - the
    documented 075/076 re-emission convention.
    """

    spec = importlib.util.spec_from_file_location(
        "_071_review_surface_read_model",
        Path(__file__).with_name(_READ_MODEL_MODULE_NAME),
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("071 read-model module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sql: str = module._read_model_function_sql()
    actual = hashlib.sha256(sql.encode("utf-8")).hexdigest()
    if actual != _BASE_READ_MODEL_SHA256:
        raise RuntimeError(
            "071 read-model source moved; refusing a 082 re-emission "
            f"against unverified bytes (actual sha256 {actual})"
        )
    if sql.count(_READ_MODEL_CREATE) != 1:
        raise RuntimeError("071 read-model header moved; refusing re-emission")
    sql = sql.replace(_READ_MODEL_CREATE, _READ_MODEL_CREATE_OR_REPLACE)
    if not pointer:
        return sql
    if sql.count(_OLD_SNAPSHOT_SELECTION) != 1:
        raise RuntimeError(
            "071 read-model snapshot selection moved; refusing a 082 re-emission"
        )
    return sql.replace(_OLD_SNAPSHOT_SELECTION, _POINTER_SNAPSHOT_SELECTION)


# ---------------------------------------------------------------------------
# 070_001 freeze re-emission (075/076 convention: the merged 070 bytes are
# preserved verbatim; the re-emitted statement differs only by the
# documented header keyword and the single documented retry-path guard).
# sha256 of the exact 070 DDL statement text at the verified base:
# 4afff56d1916328f0932e3cbf3d48d733e8e4ca80d536e4d85623dc18eaffe8d
# ---------------------------------------------------------------------------

_FREEZE_070_DDL = """        CREATE FUNCTION control.slaif_workspace_freeze(
            p_workspace_id uuid
        ) RETURNS TABLE (
            id uuid, job_id uuid
        ) LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            ws_status text;
        BEGIN
            UPDATE control.workspace
               SET status = 'FREEZING', frozen_at = CURRENT_TIMESTAMP
             WHERE control.workspace.id = p_workspace_id
               AND status = 'ACTIVE'
               AND expires_at > CURRENT_TIMESTAMP;
            IF FOUND THEN
                UPDATE control.capability
                   SET revoked_at = CURRENT_TIMESTAMP
                 WHERE workspace_id = p_workspace_id
                   AND revoked_at IS NULL;
                INSERT INTO control.review_job
                    (workspace_id, site_id, job_kind, payload)
                SELECT p_workspace_id, w.site_id, 'FREEZE', '{}'::jsonb
                FROM control.workspace AS w
                WHERE w.id = p_workspace_id
                ON CONFLICT (workspace_id, job_kind)
                    WHERE status IN ('QUEUED','CLAIMED') DO NOTHING;
                RETURN QUERY
                    SELECT p_workspace_id, j.id
                    FROM control.review_job AS j
                    WHERE j.workspace_id = p_workspace_id
                      AND j.job_kind = 'FREEZE'
                      AND j.status IN ('QUEUED','CLAIMED');
            END IF;
            SELECT status INTO ws_status
            FROM control.workspace
            WHERE control.workspace.id = p_workspace_id;
            IF ws_status IS NULL THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            IF ws_status IS DISTINCT FROM 'FREEZING' THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_ACTIVE' USING ERRCODE = 'P0002';
            END IF;
            -- Retry after a semantic failure: a FREEZING workspace with no
            -- live FREEZE job accepts exactly one new job (the partial
            -- unique index still guarantees at most one live job).
            INSERT INTO control.review_job
                (workspace_id, site_id, job_kind, payload)
            SELECT p_workspace_id, w.site_id, 'FREEZE', '{}'::jsonb
            FROM control.workspace AS w
            WHERE w.id = p_workspace_id
            ON CONFLICT (workspace_id, job_kind)
                WHERE status IN ('QUEUED','CLAIMED') DO NOTHING;
            RETURN QUERY
                SELECT p_workspace_id, j.id
                FROM control.review_job AS j
                WHERE j.workspace_id = p_workspace_id
                  AND j.job_kind = 'FREEZE'
                  AND j.status IN ('QUEUED','CLAIMED');
        END;
        $fn$"""

_FREEZE_070_SHA256 = "4afff56d1916328f0932e3cbf3d48d733e8e4ca80d536e4d85623dc18eaffe8d"
_FREEZE_CREATE = "CREATE FUNCTION control.slaif_workspace_freeze("
_FREEZE_CREATE_OR_REPLACE = "CREATE OR REPLACE FUNCTION control.slaif_workspace_freeze("

# The 070 unserialized post-branch read:
_FREEZE_OLD_READ = (
    "            SELECT status INTO ws_status\n"
    "            FROM control.workspace\n"
    "            WHERE control.workspace.id = p_workspace_id;\n"
    "            IF ws_status IS NULL THEN\n"
    "                RAISE EXCEPTION 'WORKSPACE_NOT_FOUND' USING ERRCODE = 'P0002';\n"
    "            END IF;\n"
)
# The 082 serialized read + re-review guard:
_FREEZE_NEW_READ = (
    "            SELECT status, review_snapshot_id\n"
    "            INTO ws_status, ws_pointer\n"
    "            FROM control.workspace\n"
    "            WHERE control.workspace.id = p_workspace_id\n"
    "            -- FOR NO KEY UPDATE (not FOR UPDATE): the retry row\n"
    "            -- read must serialize against state UPDATEs while\n"
    "            -- coexisting with the foreign-key KEY SHARE an\n"
    "            -- in-flight COW proposal writer holds on this row\n"
    "            -- across its open (still uncommitted) transaction;\n"
    "            -- a full FOR UPDATE would wait on that key share and\n"
    "            -- stall the enqueue.\n"
    "            FOR NO KEY UPDATE;\n"
    "            IF ws_status IS NULL THEN\n"
    "                RAISE EXCEPTION 'WORKSPACE_NOT_FOUND' USING ERRCODE = 'P0002';\n"
    "            END IF;\n"
    "            -- 082 guard: a workspace with a current snapshot pointer\n"
    "            -- is not a legacy-freeze target.  Its FREEZING state is a\n"
    "            -- re-review in flight, and the unbound legacy retry would\n"
    "            -- queue a replacement FREEZE the re-review transition does\n"
    "            -- not authorize.  Only a pre-snapshot freeze (NULL\n"
    "            -- pointer) keeps the legacy retry path.\n"
    "            IF ws_pointer IS NOT NULL THEN\n"
    "                RAISE EXCEPTION 'WORKSPACE_NOT_ACTIVE' USING ERRCODE = 'P0002';\n"
    "            END IF;\n"
)
_FREEZE_DECLARE_OLD = "        DECLARE\n            ws_status text;\n"
_FREEZE_DECLARE_NEW = (
    "        DECLARE\n            ws_status text;\n            ws_pointer uuid;\n"
)


# The legacy ACTIVE branch's RETURN QUERY is directly followed by the
# post-branch in the 070 text.  RETURN QUERY does not terminate a
# PL/pgSQL function, so the guarded re-emission inserts an explicit
# RETURN after the successful enqueue; without it the flow falls
# through into the guarded post-branch and re-reads the workspace
# row.  The earlier candidate's FOR UPDATE re-read waited on an
# in-flight COW writer's foreign-key key share held on that row
# across the open proposal transaction (the observed hang); the
# chosen FOR NO KEY UPDATE mode is compatible with that key share
# and does not wait on it.
_FREEZE_ACTIVE_RETURN_OLD = (
    "                      AND j.status IN ('QUEUED','CLAIMED');\n            END IF;\n"
)
_FREEZE_ACTIVE_RETURN_NEW = (
    "                      AND j.status IN ('QUEUED','CLAIMED');\n"
    "                -- Explicit exit: RETURN QUERY does not terminate\n"
    "                -- the function, so the unmodified legacy body\n"
    "                -- would fall through into the guarded post-branch\n"
    "                -- below and its re-read of this row.\n"
    "                RETURN;\n"
    "            END IF;\n"
)


def _freeze_sql(guarded: bool) -> str:
    """The exact 070_001 freeze, or its 082 guarded revision."""

    ddl = _FREEZE_070_DDL
    actual = hashlib.sha256(ddl.encode("utf-8")).hexdigest()
    if actual != _FREEZE_070_SHA256:
        raise RuntimeError("embedded 070 freeze bytes drifted; refusing")
    if ddl.count(_FREEZE_CREATE) != 1:
        raise RuntimeError("070 freeze header moved; refusing re-emission")
    ddl = ddl.replace(_FREEZE_CREATE, _FREEZE_CREATE_OR_REPLACE)
    if not guarded:
        return ddl
    if (
        ddl.count(_FREEZE_DECLARE_OLD) != 1
        or ddl.count(_FREEZE_OLD_READ) != 1
        or ddl.count(_FREEZE_ACTIVE_RETURN_OLD) != 1
    ):
        raise RuntimeError("070 freeze body moved; refusing a 082 re-emission")
    ddl = ddl.replace(_FREEZE_DECLARE_OLD, _FREEZE_DECLARE_NEW)
    ddl = ddl.replace(_FREEZE_ACTIVE_RETURN_OLD, _FREEZE_ACTIVE_RETURN_NEW)
    return ddl.replace(_FREEZE_OLD_READ, _FREEZE_NEW_READ)


_INNER_RE_REVIEW_SQL = """
        CREATE FUNCTION control.slaif_workspace_re_review(
            p_workspace_id uuid, p_current_snapshot_id uuid
        ) RETURNS TABLE (
            id uuid, job_id uuid
        ) LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            ws_status text;
            ws_pointer uuid;
            ws_site_id uuid;
            v_snapshot_digest text;
            v_manifest_digest text;
        BEGIN
            -- A NULL snapshot is refused before any state read or row
            -- lock: a legacy (pre-snapshot) FREEZING workspace carries
            -- a NULL review_snapshot_id, and NULL IS DISTINCT FROM
            -- NULL is false, so without this guard the stale check
            -- below would pass and a legacy null-pointer freeze could
            -- be selected as the target of a same-workspace re-review.
            IF p_current_snapshot_id IS NULL THEN
                RAISE EXCEPTION 'RE_REVIEW_SNAPSHOT_NULL'
                    USING ERRCODE = 'P0002';
            END IF;
            -- Serialize against snapshot completion and every other
            -- transition on the SAME workspace row for the whole
            -- transition (the row lock is held through every branch).
            -- Qualified: the unqualified id would be ambiguous
            -- against this function's own output column (the implicit
            -- RETURNS TABLE variable) in plpgsql.
            SELECT control.workspace.status,
                   control.workspace.review_snapshot_id,
                   control.workspace.site_id
              INTO ws_status, ws_pointer, ws_site_id
            FROM control.workspace
            WHERE control.workspace.id = p_workspace_id
            FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            -- Verified stale refusal: the named snapshot must be the
            -- trusted CURRENT snapshot; a later re-review (or any other
            -- pointer change) makes the request stale, in every state.
            IF ws_pointer IS DISTINCT FROM p_current_snapshot_id THEN
                RAISE EXCEPTION 'REVIEW_REVIEW_SNAPSHOT_STALE'
                    USING ERRCODE = 'P0003';
            END IF;
            IF ws_status = 'REVIEW' THEN
                -- Criterion-3 verified stale-revision gate, checked
                -- BEFORE any state change: the current COMPLETE
                -- snapshot must be bound to this exact site/workspace
                -- with its stored digest, a companion manifest for
                -- that exact snapshot whose OWN snapshot_digest
                -- matches the stored one, and a FAILED real ACCEPT
                -- job for that exact site/workspace/snapshot
                -- carrying the stable SITE_REVISION_CHANGED code
                -- whose durable approval (site + BOTH digests)
                -- matches the stored snapshot digest and the
                -- companion manifest digest.  A current pointer alone
                -- proves eligibility, never that the review is stale.
                SELECT control.review_snapshot.digest
                  INTO v_snapshot_digest
                FROM control.review_snapshot
                WHERE control.review_snapshot.id = p_current_snapshot_id
                  AND control.review_snapshot.workspace_id = p_workspace_id
                  AND control.review_snapshot.site_id = ws_site_id
                  AND control.review_snapshot.status = 'COMPLETE';
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'REVIEW_REVIEW_SNAPSHOT_STALE'
                        USING ERRCODE = 'P0003';
                END IF;
                -- rom. qualification: an unqualified manifest_digest
                -- would resolve to the SAME-NAMED local variable in
                -- plpgsql, never the column.
                SELECT rom.manifest_digest INTO v_manifest_digest
                FROM control.review_operation_manifest AS rom
                WHERE rom.snapshot_id = p_current_snapshot_id
                  AND rom.site_id = ws_site_id
                  AND rom.workspace_id = p_workspace_id
                  AND rom.snapshot_digest = v_snapshot_digest;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'RE_REVIEW_STALE_REVISION_UNVERIFIED'
                        USING ERRCODE = 'P0003';
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM control.review_job AS job
                    WHERE job.workspace_id = p_workspace_id
                      AND job.site_id = ws_site_id
                      AND job.job_kind = 'ACCEPT'
                      AND job.status = 'FAILED'
                      AND job.error = 'SITE_REVISION_CHANGED'
                      AND job.payload->>'site_id' = ws_site_id::text
                      AND job.payload->>'snapshot_id'
                          = p_current_snapshot_id::text
                      AND job.payload->>'snapshot_digest' = v_snapshot_digest
                      AND job.payload->>'manifest_digest' = v_manifest_digest
                ) THEN
                    RAISE EXCEPTION
                        'RE_REVIEW_STALE_REVISION_UNVERIFIED'
                        USING ERRCODE = 'P0003';
                END IF;
                UPDATE control.workspace
                   SET status = 'FREEZING', frozen_at = CURRENT_TIMESTAMP
                 WHERE control.workspace.id = p_workspace_id
                   AND control.workspace.status = 'REVIEW'
                   AND control.workspace.review_snapshot_id
                       = p_current_snapshot_id;
                IF NOT FOUND THEN
                    -- Unreachable under the held row lock; fail closed.
                    RAISE EXCEPTION 'WORKSPACE_NOT_IN_REVIEW'
                        USING ERRCODE = 'P0002';
                END IF;
                -- Capability revocation is idempotent (the freeze
                -- already revoked; the workspace stays closed to
                -- editing and the capabilities stay revoked).
                UPDATE control.capability
                   SET revoked_at = CURRENT_TIMESTAMP
                 WHERE control.capability.workspace_id = p_workspace_id
                   AND control.capability.revoked_at IS NULL;
                -- Single result path: mirror the durable transition
                -- in the local state so the common FREEZE enqueue
                -- below runs once, and no later guard can re-read a
                -- stale local status and roll the transition back.
                ws_status := 'FREEZING';
            END IF;
            IF ws_status IS DISTINCT FROM 'FREEZING' THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_IN_REVIEW'
                    USING ERRCODE = 'P0002';
            END IF;
            -- One re-review FREEZE per workspace state.  Entering
            -- FREEZING from REVIEW above and the operational retry
            -- after a rolled-back finalization (a FREEZING workspace
            -- still pointing at the named snapshot, the gate
            -- verified on entry to FREEZING) both land here.
            -- Serialized on the same workspace row for the whole
            -- function, so neither can race the snapshot completion
            -- transition.  A concurrent repeat finds the live job
            -- and returns it unchanged; the partial unique index
            -- keeps at most one live FREEZE job per workspace.
            INSERT INTO control.review_job
                (workspace_id, site_id, job_kind, payload)
            SELECT p_workspace_id, ws_site_id, 'FREEZE',
                   jsonb_build_object(
                       're_review', true,
                       'previous_snapshot_id', p_current_snapshot_id::text
                   )
            ON CONFLICT (workspace_id, job_kind)
                WHERE control.review_job.status IN ('QUEUED','CLAIMED')
                DO NOTHING;
            RETURN QUERY
                SELECT p_workspace_id, j.id
                FROM control.review_job AS j
                WHERE j.workspace_id = p_workspace_id
                  AND j.job_kind = 'FREEZE'
                  AND j.status IN ('QUEUED','CLAIMED');
        END;
        $fn$
"""

_HUMAN_RE_REVIEW_SQL = """
        CREATE FUNCTION control.slaif_human_agent_workspace_re_review(
            p_workspace_id uuid, p_site_id uuid, p_snapshot_id uuid,
            p_user_id uuid
        ) RETURNS TABLE (job_id uuid, status text)
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            re_review_row record;
        BEGIN
            -- Exact site binding: unknown workspace or missing site
            -- yields no row (uniform 404, the established
            -- control-plane no-oracle pattern).
            IF NOT EXISTS (
                SELECT 1 FROM control.workspace AS w
                WHERE w.id = p_workspace_id
                  AND w.site_id = p_site_id
            ) THEN
                RETURN;
            END IF;
            -- The existing human authority: the same site-governance
            -- key as the original freeze (workspace:freeze), no new
            -- scope, no widening.  Missing authority yields no row.
            IF NOT EXISTS (
                SELECT 1 FROM control.platform_administrator
                WHERE user_account_id = p_user_id
            ) AND NOT EXISTS (
                SELECT 1
                FROM control.slaif_effective_human_membership(
                    p_user_id, p_site_id
                ) AS m
                WHERE 'workspace:freeze' = ANY(m.effective_permissions)
            ) THEN
                RETURN;
            END IF;
            SELECT * INTO re_review_row
            FROM control.slaif_workspace_re_review(p_workspace_id, p_snapshot_id);
            RETURN QUERY SELECT re_review_row.job_id, 'FREEZING';
        END;
        $fn$
"""

_DOWNGRADE_GUARD_SQL = """
        DO $guard$
        DECLARE
            multi_count integer;
        BEGIN
            -- Guarded rollback to 071 semantics: PL/pgSQL SELECT INTO
            -- without STRICT assigns the FIRST row silently, so the
            -- restored 071 read model is correct only while every
            -- workspace retains AT MOST ONE COMPLETE snapshot (its
            -- 071 selection then matches the trusted pointer exactly).
            -- Refuse BEFORE any effect (the refusal is atomic: no
            -- function or state change has run) when a re-review has
            -- retained multiple snapshots for a workspace, or when a
            -- re-review is still in flight (FREEZING with a current
            -- pointer).
            SELECT count(*) INTO multi_count
            FROM (
                SELECT workspace_id FROM control.review_snapshot
                WHERE status = 'COMPLETE'
                GROUP BY workspace_id
                HAVING count(*) > 1
            ) AS multi;
            IF multi_count > 0 THEN
                RAISE EXCEPTION
                    'RE_REVIEW_DOWNGRADE_RETAINED_MULTI_SNAPSHOT'
                    USING ERRCODE = 'P0002';
            END IF;
            IF EXISTS (
                SELECT 1 FROM control.workspace
                WHERE status = 'FREEZING' AND review_snapshot_id IS NOT NULL
            ) THEN
                RAISE EXCEPTION 'RE_REVIEW_DOWNGRADE_IN_FLIGHT'
                    USING ERRCODE = 'P0002';
            END IF;
        END;
        $guard$
"""


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Inner re-review transition (owner-internal: NO role EXECUTE
    # grants, mirroring the 079 inner accept; reachable only through
    # the human entry point below, which re-checks the site binding
    # and the workspace:freeze authority).
    # ------------------------------------------------------------------
    op.execute(_INNER_RE_REVIEW_SQL)
    op.execute(
        "ALTER FUNCTION control.slaif_workspace_re_review("
        "uuid, uuid) OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_workspace_re_review("
        "uuid, uuid) FROM PUBLIC"
    )

    # ------------------------------------------------------------------
    # Human Control re-review entry point: EXECUTE for slaif_control
    # only (the same grant surface as the real freeze).
    # ------------------------------------------------------------------
    op.execute(_HUMAN_RE_REVIEW_SQL)
    op.execute(
        "ALTER FUNCTION control.slaif_human_agent_workspace_re_review("
        "uuid, uuid, uuid, uuid) OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_human_agent_workspace_re_review("
        "uuid, uuid, uuid, uuid) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_human_agent_workspace_re_review("
        "uuid, uuid, uuid, uuid) TO slaif_control"
    )

    # ------------------------------------------------------------------
    # Legacy freeze retry guard: the merged 070 bytes are preserved
    # except the documented serialized FOR NO KEY UPDATE read, the
    # pointer guard, and the explicit ACTIVE-branch RETURN (RETURN
    # QUERY does not terminate the function), so the legacy retry can
    # no longer queue a replacement unbound FREEZE for a re-review in
    # flight.  Ownership and ACL are preserved by CREATE OR REPLACE
    # on the same object.
    # ------------------------------------------------------------------
    op.execute(_freeze_sql(guarded=True))

    # ------------------------------------------------------------------
    # Regular human review read: select the snapshot through the
    # trusted current pointer (scoped by site and workspace).  The
    # re-emitted body is byte-identical to the 071_001 text except for
    # the documented header keyword and the single documented
    # snapshot-selection statement; ownership and ACL are preserved by
    # CREATE OR REPLACE on the same object.
    # ------------------------------------------------------------------
    op.execute(_read_model_sql(pointer=True))


def downgrade() -> None:
    # Function-only: no snapshot, retention, job, capability or
    # workspace state is touched, so retained rows survive
    # byte-for-byte.  The guard refuses before any effect when the
    # 071 semantics cannot be restored exactly (multi-snapshot
    # retention or an in-flight re-review); otherwise restore the
    # exact 071_001 read model and the exact 070_001 freeze body
    # (header keyword only; prosrc byte-identical), then drop the two
    # 082 functions.  The 081 downgrade ratchet refuses any further
    # step before the earlier downgrades can see the retained
    # snapshots.
    op.execute(_DOWNGRADE_GUARD_SQL)
    op.execute(_read_model_sql(pointer=False))
    op.execute(_freeze_sql(guarded=False))
    op.execute(
        "DROP FUNCTION IF EXISTS control.slaif_human_agent_workspace_re_review("
        "uuid, uuid, uuid, uuid)"
    )
    op.execute("DROP FUNCTION IF EXISTS control.slaif_workspace_re_review(uuid, uuid)")
