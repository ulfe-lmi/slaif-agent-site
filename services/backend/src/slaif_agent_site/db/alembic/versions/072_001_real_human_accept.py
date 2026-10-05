# ruff: noqa: E501
"""Real human accept: reviewer grant, kind-aware claim, accept enqueue,
promotion audit and cache outbox (083/1).

Upgrade:
1. ``GRANT slaif_reviewer TO slaif_review_worker`` - the worker process
   becomes the sole process holding reviewer authority (architecture
   section 4: "review worker = sole reviewer DB role"). The grant runs
   as ``slaif_owner`` and is only possible because cluster provisioning
   (``db/roles.py``) permanently grants the owner the ADMIN option on
   the reviewer role (``GRANT slaif_reviewer TO slaif_owner WITH ADMIN
   OPTION``); the owner is setup-only and never a product credential.
2. ``control.slaif_review_job_claim`` is rebuilt as
   ``slaif_review_job_claim(p_claimant text, p_kinds text[])``: the
   stale-claim recovery block stays byte-identical to 070_001; the claim
   now selects ``status='QUEUED' AND job_kind = ANY(p_kinds)``. The
   070_001 single-argument definition is replaced (dropped).
3. ``control.slaif_workspace_accept`` is rebuilt as the idempotent
   REVIEW -> ACCEPT_QUEUED enqueue (replacing the 024_001 stub; the
   actor is carried in the job payload for the promotion audit row;
   a live QUEUED/CLAIMED job is returned unchanged before the status
   gate, so a duplicate accept returns the SAME job id).
4. ``control.slaif_human_agent_workspace_accept`` - the human Control
   entry point: exact site binding, the dual
   ``workspace:accept`` + ``site:publish`` re-check, and the
   snapshot/digest expectation, then the enqueue. Unknown workspace,
   wrong binding, missing authority, snapshot or digest mismatch all
   yield no row (uniform 404 class, no oracle); the enqueue's stable
   ``WORKSPACE_NOT_IN_REVIEW`` propagates (409 class).
5. ``audit.promotion`` (append-only promotion audit) and
   ``control.cache_outbox`` (event kind ``WORKSPACE_ACCEPTED``; no
   consumer in this increment) with the exact minimal grant sets.
6. Exact additional worker grants: UPDATE on ``control.workspace`` and
   ``control.site`` (SELECT already present since 070_001),
   ``INSERT ON audit.promotion``, ``INSERT, SELECT ON
   control.cache_outbox``, USAGE on the audit schema, and the
   ``control.review_snapshot`` SELECT re-pin.
7. The worker's foundation (``agentcow``) reviewer surface is NOT
   granted here: the ``agentcow`` schema does not exist at migration
   time (``deploy_cow_functions`` runs during bootstrap reconcile,
   after the Alembic head is reached). It is applied and re-applied
   by ``apply_product_privileges`` on every HARDENED reconcile (see
   ``db/privileges.py``): USAGE on the ``agentcow`` schema plus
   EXECUTE on the exact 13 foundation functions the hardening grants
   to ``slaif_reviewer`` (the foundation's controlled reviewer set).
   The promotion transaction runs ``asyncpg_cow_reviewer`` as the
   worker login, and the product privilege roles are NOINHERIT, so
   the transitive worker -> reviewer membership carries no effective
   authority; the surface must be granted directly to the worker
   role (documented deviation from the R1.6 table-only grant list).
   All 13 functions are SECURITY DEFINER owned by ``slaif_owner``,
   so no direct content/agentcow table grants are required or
   granted.

Downgrade drops exactly the two tables, revokes exactly the grants
added, drops the two rebuilt/new functions, revokes the reviewer
membership, and restores the exact 070_001 claim and 024_001 accept
definitions.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "072_001"
down_revision: str | Sequence[str] | None = "071_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CLAIM_FUNCTION = "control.slaif_review_job_claim(text, text[])"
_ACCEPT_FUNCTION = "control.slaif_workspace_accept(uuid, uuid)"
_HUMAN_ACCEPT_FUNCTION = (
    "control.slaif_human_agent_workspace_accept(uuid, uuid, uuid, text, uuid)"
)

# Every non-owner privilege role: function/table grants are revoked from
# all of them before the exact intended grant is re-added (070/071
# pattern).
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


def upgrade() -> None:
    # 1. The ONLY reviewer authority added anywhere: the worker process
    #    becomes the sole member of the reviewer group.
    op.execute("GRANT slaif_reviewer TO slaif_review_worker")

    # 2. Kind-aware claim (replaces the 070_001 single-argument
    #    definition; the stale-recovery block is EXACTLY the 070_001
    #    logic and applies to all kinds).
    op.execute("DROP FUNCTION IF EXISTS control.slaif_review_job_claim(text)")
    op.execute(
        """
        CREATE FUNCTION control.slaif_review_job_claim(
            p_claimant text, p_kinds text[]
        ) RETURNS TABLE (
            id uuid, workspace_id uuid, site_id uuid, job_kind text,
            status text, attempt_count integer, max_attempts integer,
            claimed_by text, claimed_at timestamptz,
            last_heartbeat timestamptz, payload jsonb, error text,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            selected control.review_job%ROWTYPE;
        BEGIN
            IF p_claimant IS NULL
               OR p_claimant !~ '^[A-Za-z0-9._:-]{1,128}$'
            THEN
                RAISE EXCEPTION 'REVIEW_CLAIMANT_INVALID' USING ERRCODE = '22023';
            END IF;
            IF p_kinds IS NULL
               OR array_length(p_kinds, 1) IS NULL
               OR NOT (p_kinds <@ ARRAY['FREEZE','ACCEPT','DISCARD'])
            THEN
                RAISE EXCEPTION 'REVIEW_CLAIM_KIND_INVALID'
                    USING ERRCODE = '22023';
            END IF;
            -- Stale-claim recovery: a CLAIMED job without a fresh heartbeat
            -- is re-queued while attempts remain, and FAILED at the budget.
            UPDATE control.review_job
               SET status = 'QUEUED', claimed_by = NULL, claimed_at = NULL,
                   last_heartbeat = NULL, updated_at = CURRENT_TIMESTAMP
             WHERE control.review_job.status = 'CLAIMED'
               AND control.review_job.last_heartbeat
                   < CURRENT_TIMESTAMP - interval '60 seconds'
               AND control.review_job.attempt_count
                   < control.review_job.max_attempts;
            UPDATE control.review_job
               SET status = 'FAILED', error = 'REVIEW_JOB_STALE_AT_BUDGET',
                   updated_at = CURRENT_TIMESTAMP
             WHERE control.review_job.status = 'CLAIMED'
               AND control.review_job.last_heartbeat
                   < CURRENT_TIMESTAMP - interval '60 seconds'
               AND control.review_job.attempt_count
                   >= control.review_job.max_attempts;
            SELECT * INTO selected
            FROM control.review_job AS job
            WHERE job.status = 'QUEUED'
              AND job.job_kind = ANY(p_kinds)
            ORDER BY job.created_at, job.id
            LIMIT 1
            FOR UPDATE SKIP LOCKED;
            IF NOT FOUND THEN
                RETURN;
            END IF;
            UPDATE control.review_job
               SET status = 'CLAIMED', claimed_by = p_claimant,
                   claimed_at = CURRENT_TIMESTAMP,
                   last_heartbeat = CURRENT_TIMESTAMP,
                   attempt_count = control.review_job.attempt_count + 1,
                   updated_at = CURRENT_TIMESTAMP
             WHERE control.review_job.id = selected.id;
            RETURN QUERY SELECT job.id, job.workspace_id, job.site_id,
                job.job_kind, job.status, job.attempt_count, job.max_attempts,
                job.claimed_by, job.claimed_at, job.last_heartbeat,
                job.payload, job.error, job.created_at, job.updated_at
            FROM control.review_job AS job
            WHERE job.id = selected.id;
        END;
        $fn$
        """
    )

    # 3. Idempotent REVIEW -> ACCEPT_QUEUED enqueue (replaces the 024_001
    #    stub). The actor is carried in the job payload: the promotion
    #    audit row records the human account that enqueued the accept.
    #    The live-job idempotency check runs before the status gate: a
    #    second accept while the job is QUEUED/CLAIMED (the workspace
    #    already ACCEPT_QUEUED or PROMOTING) returns the SAME job id.
    op.execute("DROP FUNCTION IF EXISTS control.slaif_workspace_accept(uuid)")
    op.execute(
        """
        CREATE FUNCTION control.slaif_workspace_accept(
            p_workspace_id uuid, p_actor_user_account_id uuid
        ) RETURNS TABLE (
            job_id uuid, status text
        ) LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        #variable_conflict use_column
        DECLARE
            ws control.workspace%ROWTYPE;
            live_id uuid;
            live_status text;
        BEGIN
            SELECT * INTO ws FROM control.workspace
            WHERE id = p_workspace_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            -- Idempotent: a live (QUEUED/CLAIMED) ACCEPT job is returned
            -- unchanged regardless of the current workspace status.
            SELECT job.id, job.status INTO live_id, live_status
            FROM control.review_job AS job
            WHERE job.workspace_id = p_workspace_id
              AND job.job_kind = 'ACCEPT'
              AND job.status IN ('QUEUED','CLAIMED')
            FOR UPDATE;
            IF FOUND THEN
                -- RETURN QUERY does not terminate a plpgsql function: the
                -- explicit RETURN stops the idempotent path before the
                -- status gate (the workspace is already ACCEPT_QUEUED).
                RETURN QUERY SELECT live_id, live_status;
                RETURN;
            END IF;
            IF ws.status IS DISTINCT FROM 'REVIEW' THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_IN_REVIEW'
                    USING ERRCODE = 'P0002';
            END IF;
            IF ws.review_snapshot_id IS NULL
               OR NOT EXISTS (
                    SELECT 1 FROM control.review_snapshot AS s
                    WHERE s.id = ws.review_snapshot_id
                      AND s.status = 'COMPLETE'
                )
            THEN
                RAISE EXCEPTION 'REVIEW_SNAPSHOT_NOT_FOUND'
                    USING ERRCODE = 'P0002';
            END IF;
            -- The partial unique index closes the enqueue race.
            INSERT INTO control.review_job (
                workspace_id, site_id, job_kind, status, payload
            )
            VALUES (
                p_workspace_id, ws.site_id, 'ACCEPT', 'QUEUED',
                jsonb_build_object(
                    'snapshot_id', ws.review_snapshot_id::text,
                    'site_id', ws.site_id::text,
                    'actor_user_account_id',
                        p_actor_user_account_id::text
                )
            )
            ON CONFLICT (workspace_id, job_kind)
                WHERE status IN ('QUEUED','CLAIMED') DO NOTHING;
            SELECT job.id, job.status INTO live_id, live_status
            FROM control.review_job AS job
            WHERE job.workspace_id = p_workspace_id
              AND job.job_kind = 'ACCEPT'
              AND job.status IN ('QUEUED','CLAIMED')
            FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'ACCEPT_ENQUEUE_CONFLICT'
                    USING ERRCODE = 'P0002';
            END IF;
            UPDATE control.workspace
               SET status = 'ACCEPT_QUEUED'
             WHERE control.workspace.id = p_workspace_id
               AND control.workspace.status = 'REVIEW';
            RETURN QUERY SELECT live_id, live_status;
        END;
        $fn$
        """
    )

    # 4. Human Control entry point: exact site binding + dual authority
    #    re-check + snapshot/digest expectation, then the enqueue.
    op.execute(
        """
        CREATE FUNCTION control.slaif_human_agent_workspace_accept(
            p_workspace_id uuid, p_site_id uuid, p_snapshot_id uuid,
            p_digest text, p_user_id uuid
        ) RETURNS TABLE (job_id uuid, status text)
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            accept_row record;
            ws_status text;
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM control.workspace AS w
                WHERE w.id = p_workspace_id
                  AND w.site_id = p_site_id
            ) THEN
                RETURN;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM control.platform_administrator
                WHERE user_account_id = p_user_id
            ) AND NOT EXISTS (
                SELECT 1
                FROM control.slaif_effective_human_membership(
                    p_user_id, p_site_id
                ) AS m
                WHERE 'workspace:accept' = ANY(m.effective_permissions)
                  AND 'site:publish' = ANY(m.effective_permissions)
            ) THEN
                RETURN;
            END IF;
            -- Snapshot expectation: the bound COMPLETE snapshot must be
            -- the named one and carry the named digest. Any mismatch is
            -- indistinguishable from the not-found case (no oracle).
            IF NOT EXISTS (
                SELECT 1
                FROM control.workspace AS w
                JOIN control.review_snapshot AS s
                    ON s.id = w.review_snapshot_id
                   AND s.status = 'COMPLETE'
                WHERE w.id = p_workspace_id
                  AND s.id = p_snapshot_id
                  AND s.digest = p_digest
            ) THEN
                RETURN;
            END IF;
            SELECT * INTO accept_row
            FROM control.slaif_workspace_accept(
                p_workspace_id, p_user_id
            );
            SELECT w.status INTO ws_status
            FROM control.workspace AS w
            WHERE w.id = p_workspace_id;
            RETURN QUERY
                SELECT accept_row.job_id,
                       COALESCE(ws_status, accept_row.status);
        END;
        $fn$
        """
    )

    # 5. Append-only promotion audit + the (unconsumed) cache outbox.
    op.execute(
        """
        CREATE TABLE audit.promotion (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL,
            workspace_id UUID NOT NULL,
            snapshot_id UUID NOT NULL,
            job_id UUID NOT NULL,
            digest TEXT NOT NULL,
            base_site_revision BIGINT NOT NULL,
            new_canonical_revision BIGINT NOT NULL,
            committed_operations INTEGER NOT NULL,
            versions JSONB NOT NULL,
            actor_user_account_id UUID NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT promotion_digest_shape CHECK (digest ~ '^[0-9a-f]{64}$'),
            CONSTRAINT promotion_revisions_nonnegative CHECK (
                base_site_revision >= 0 AND new_canonical_revision > 0
            ),
            CONSTRAINT promotion_operations_nonnegative CHECK (
                committed_operations >= 0
            )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE control.cache_outbox (
            id BIGSERIAL PRIMARY KEY,
            site_id UUID NOT NULL,
            workspace_id UUID NOT NULL,
            event_kind TEXT NOT NULL
                CHECK (event_kind IN ('WORKSPACE_ACCEPTED')),
            payload JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # Function grants: exact caller sets (070/071 pattern).
    for function in (_CLAIM_FUNCTION, _ACCEPT_FUNCTION, _HUMAN_ACCEPT_FUNCTION):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        for role in _LONG_LIVED_ROLES:
            op.execute(f"REVOKE ALL ON FUNCTION {function} FROM {role}")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_CLAIM_FUNCTION} TO slaif_review_worker")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_ACCEPT_FUNCTION} TO slaif_control")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_HUMAN_ACCEPT_FUNCTION} TO slaif_control")

    # Table grants: minimal sets, PUBLIC and every long-lived role
    # revoked first (070/071 pattern).
    for relation in ("audit.promotion", "control.cache_outbox"):
        op.execute(f"REVOKE ALL ON TABLE {relation} FROM PUBLIC")
        for role in _LONG_LIVED_ROLES:
            op.execute(f"REVOKE ALL ON TABLE {relation} FROM {role}")
    op.execute("GRANT USAGE ON SCHEMA audit TO slaif_review_worker")
    op.execute("GRANT INSERT ON audit.promotion TO slaif_review_worker")
    op.execute("GRANT SELECT ON audit.promotion TO slaif_reviewer")
    op.execute("GRANT INSERT, SELECT ON control.cache_outbox TO slaif_review_worker")
    # BIGSERIAL default: the worker's INSERT needs the sequence.
    op.execute(
        "GRANT USAGE ON SEQUENCE control.cache_outbox_id_seq TO slaif_review_worker"
    )

    # 6. Exact additional worker grants (SELECT on workspace/site and
    #    review_snapshot already present since 070_001 - re-pinned).
    op.execute("GRANT UPDATE ON control.workspace TO slaif_review_worker")
    op.execute("GRANT UPDATE ON control.site TO slaif_review_worker")
    op.execute("GRANT SELECT ON control.review_snapshot TO slaif_review_worker")


def downgrade() -> None:
    # Drop exactly the functions created/replaced by the upgrade.
    op.execute(
        "DROP FUNCTION IF EXISTS control.slaif_human_agent_workspace_accept("
        "uuid, uuid, uuid, text, uuid)"
    )
    op.execute("DROP FUNCTION IF EXISTS control.slaif_workspace_accept(uuid, uuid)")
    op.execute("DROP FUNCTION IF EXISTS control.slaif_review_job_claim(text, text[])")

    # Restore the exact 070_001 single-argument claim definition.
    op.execute(
        """
        CREATE FUNCTION control.slaif_review_job_claim(p_claimant text)
        RETURNS TABLE (
            id uuid, workspace_id uuid, site_id uuid, job_kind text,
            status text, attempt_count integer, max_attempts integer,
            claimed_by text, claimed_at timestamptz,
            last_heartbeat timestamptz, payload jsonb, error text,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            selected control.review_job%ROWTYPE;
        BEGIN
            IF p_claimant IS NULL
               OR p_claimant !~ '^[A-Za-z0-9._:-]{1,128}$'
            THEN
                RAISE EXCEPTION 'REVIEW_CLAIMANT_INVALID' USING ERRCODE = '22023';
            END IF;
            -- Stale-claim recovery: a CLAIMED job without a fresh heartbeat
            -- is re-queued while attempts remain, and FAILED at the budget.
            UPDATE control.review_job
               SET status = 'QUEUED', claimed_by = NULL, claimed_at = NULL,
                   last_heartbeat = NULL, updated_at = CURRENT_TIMESTAMP
             WHERE control.review_job.status = 'CLAIMED'
               AND control.review_job.last_heartbeat
                   < CURRENT_TIMESTAMP - interval '60 seconds'
               AND control.review_job.attempt_count
                   < control.review_job.max_attempts;
            UPDATE control.review_job
               SET status = 'FAILED', error = 'REVIEW_JOB_STALE_AT_BUDGET',
                   updated_at = CURRENT_TIMESTAMP
             WHERE control.review_job.status = 'CLAIMED'
               AND control.review_job.last_heartbeat
                   < CURRENT_TIMESTAMP - interval '60 seconds'
               AND control.review_job.attempt_count
                   >= control.review_job.max_attempts;
            SELECT * INTO selected
            FROM control.review_job AS job
            WHERE job.status = 'QUEUED'
            ORDER BY job.created_at, job.id
            LIMIT 1
            FOR UPDATE SKIP LOCKED;
            IF NOT FOUND THEN
                RETURN;
            END IF;
            UPDATE control.review_job
               SET status = 'CLAIMED', claimed_by = p_claimant,
                   claimed_at = CURRENT_TIMESTAMP,
                   last_heartbeat = CURRENT_TIMESTAMP,
                   attempt_count = control.review_job.attempt_count + 1,
                   updated_at = CURRENT_TIMESTAMP
             WHERE control.review_job.id = selected.id;
            RETURN QUERY SELECT job.id, job.workspace_id, job.site_id,
                job.job_kind, job.status, job.attempt_count, job.max_attempts,
                job.claimed_by, job.claimed_at, job.last_heartbeat,
                job.payload, job.error, job.created_at, job.updated_at
            FROM control.review_job AS job
            WHERE job.id = selected.id;
        END;
        $fn$
        """
    )
    op.execute(
        "ALTER FUNCTION control.slaif_review_job_claim(text) OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_review_job_claim(text) FROM PUBLIC"
    )
    for role in _LONG_LIVED_ROLES:
        op.execute(
            f"REVOKE ALL ON FUNCTION control.slaif_review_job_claim(text) FROM {role}"
        )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_review_job_claim(text) "
        "TO slaif_review_worker"
    )

    # Restore the exact 024_001 accept stub.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_workspace_accept(
            p_workspace_id uuid
        ) RETURNS TABLE (
            id uuid, status text, accepted_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
            ws_status text;
        BEGIN
            SELECT status INTO ws_status FROM control.workspace WHERE id = p_workspace_id;
            IF ws_status IS NULL THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            IF ws_status NOT IN ('REVIEW') THEN
                RAISE EXCEPTION 'NOT_IN_REVIEW' USING ERRCODE = 'P0002';
            END IF;
            UPDATE control.workspace SET
                status = 'ACCEPTED',
                accepted_at = CURRENT_TIMESTAMP
            WHERE id = p_workspace_id AND status = 'REVIEW';
            RETURN QUERY SELECT w.id, w.status, w.accepted_at
            FROM control.workspace w WHERE w.id = p_workspace_id;
        END;
        $fn$
        """
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_workspace_accept(uuid) TO slaif_control"
    )

    # Revoke the worker's cache_outbox sequence usage before the table
    # (and its implicit sequence) drop.
    op.execute(
        "REVOKE USAGE ON SEQUENCE control.cache_outbox_id_seq FROM slaif_review_worker"
    )

    # Drop exactly the tables created by the upgrade.
    op.execute("DROP TABLE IF EXISTS control.cache_outbox")
    op.execute("DROP TABLE IF EXISTS audit.promotion")

    # Revoke exactly the grants added by the upgrade.
    op.execute("REVOKE UPDATE ON control.workspace FROM slaif_review_worker")
    op.execute("REVOKE UPDATE ON control.site FROM slaif_review_worker")
    op.execute("REVOKE USAGE ON SCHEMA audit FROM slaif_review_worker")
    op.execute("REVOKE slaif_reviewer FROM slaif_review_worker")
