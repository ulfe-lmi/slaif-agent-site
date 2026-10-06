# ruff: noqa: E501
"""Real discard (conflict remedy): idempotent DISCARD enqueue + human
Control entry (083/2).

Upgrade:
1. ``control.slaif_workspace_discard(p_workspace_id uuid,
   p_actor_user_account_id uuid)`` is rebuilt as the idempotent
   REVIEW/CONFLICTED -> DISCARD_QUEUED enqueue (replacing the 024_001
   stub ``slaif_workspace_discard(uuid)``), mirroring the 072_001 accept
   enqueue EXACTLY: workspace row ``FOR UPDATE``;
   ``WORKSPACE_NOT_FOUND``; a live (QUEUED/CLAIMED) DISCARD job is
   returned unchanged BEFORE the status gate, so a duplicate discard
   returns the SAME job id; the status gate
   ``status IN ('REVIEW','CONFLICTED')`` with the stable
   ``WORKSPACE_NOT_DISCARDABLE`` code; defensive idempotent capability
   revocation (the freeze pattern, ``revoked_at IS NULL`` guard); the
   enqueue through the partial unique index plus re-select guard
   (stable ``DISCARD_ENQUEUE_CONFLICT``); the guarded
   ``DISCARD_QUEUED`` transition. The 024_001 stub's ``FREEZING``
   allowance is deliberately NOT carried over: FREEZING is transient
   and races the freeze worker (the report states the rationale).
2. ``control.slaif_human_agent_workspace_discard(p_workspace_id uuid,
   p_site_id uuid, p_user_id uuid)`` - the human Control entry point:
   exact site binding, platform administrator OR effective-membership
   ``workspace:discard`` re-check, then the enqueue (discard takes no
   snapshot input). Unknown workspace, wrong binding, and missing
   authority all yield no row (uniform 404 class, no oracle); the
   enqueue's stable ``WORKSPACE_NOT_DISCARDABLE`` propagates (409
   class).
3. Zero new worker grants: this migration contains no GRANT/REVOKE
   touching ``slaif_review_worker`` or the ``agentcow`` surface. The
   worker already holds everything the DISCARD job needs (SELECT,
   INSERT, UPDATE on ``control.review_job``; UPDATE on
   ``control.workspace`` and ``control.site``; the 072_001 reviewer
   delegation; and the foundation reviewer surface re-applied by
   ``apply_product_privileges`` on every HARDENED reconcile, which
   includes ``discard_cow``).

Downgrade drops exactly the two functions created/rebuilt and restores
the BYTE-EXACT 024_001 stub ``slaif_workspace_discard(uuid)`` plus its
``GRANT EXECUTE ... TO slaif_control`` pin.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "073_001"
down_revision: str | Sequence[str] | None = "072_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DISCARD_FUNCTION = "control.slaif_workspace_discard(uuid, uuid)"
_HUMAN_DISCARD_FUNCTION = (
    "control.slaif_human_agent_workspace_discard(uuid, uuid, uuid)"
)

# Every non-owner privilege role EXCEPT the durable review worker:
# function grants are revoked from all of them before the exact
# intended grant is re-added (070/071/072 pattern).  The 083/2 order
# requires ZERO GRANT/REVOKE statements touching the review worker in
# this migration: the worker's implicit PUBLIC access to the new
# functions is removed by the PUBLIC revokes below, and the privilege
# reconcile re-applies the exact registry, which grants these
# functions to the control caller only.
_REVOKE_ROLES = (
    "slaif_control",
    "slaif_editor_runtime",
    "slaif_agent_runtime",
    "slaif_public_reader",
    "slaif_preview_reader",
    "slaif_reviewer",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
)


def upgrade() -> None:
    # 1. Idempotent REVIEW/CONFLICTED -> DISCARD_QUEUED enqueue
    #    (replaces the 024_001 stub). The actor is carried in the job
    #    payload and ``origin_status`` records the pre-discard state so
    #    a retryable failure can return the workspace to it (REVIEW or
    #    CONFLICTED). The live-job idempotency check runs before the
    #    status gate: a second discard while the job is QUEUED/CLAIMED
    #    returns the SAME job id.
    op.execute("DROP FUNCTION IF EXISTS control.slaif_workspace_discard(uuid)")
    op.execute(
        """
        CREATE FUNCTION control.slaif_workspace_discard(
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
            -- Idempotent: a live (QUEUED/CLAIMED) DISCARD job is
            -- returned unchanged regardless of the current workspace
            -- status.
            SELECT job.id, job.status INTO live_id, live_status
            FROM control.review_job AS job
            WHERE job.workspace_id = p_workspace_id
              AND job.job_kind = 'DISCARD'
              AND job.status IN ('QUEUED','CLAIMED')
            FOR UPDATE;
            IF FOUND THEN
                -- RETURN QUERY does not terminate a plpgsql function:
                -- the explicit RETURN stops the idempotent path before
                -- the status gate (the workspace is already
                -- DISCARD_QUEUED/DISCARDING/DISCARDED).
                RETURN QUERY SELECT live_id, live_status;
                RETURN;
            END IF;
            IF ws.status NOT IN ('REVIEW','CONFLICTED') THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_DISCARDABLE'
                    USING ERRCODE = 'P0002';
            END IF;
            -- Defensive idempotent capability revocation (the freeze
            -- pattern): discard removes pending work; the workspace's
            -- capability rows are revoked exactly once.
            UPDATE control.capability
               SET revoked_at = CURRENT_TIMESTAMP
             WHERE workspace_id = p_workspace_id
               AND revoked_at IS NULL;
            -- The partial unique index closes the enqueue race.
            INSERT INTO control.review_job (
                workspace_id, site_id, job_kind, status, payload
            )
            VALUES (
                p_workspace_id, ws.site_id, 'DISCARD', 'QUEUED',
                jsonb_build_object(
                    'site_id', ws.site_id::text,
                    'origin_status', ws.status,
                    'actor_user_account_id',
                        p_actor_user_account_id::text
                )
            )
            ON CONFLICT (workspace_id, job_kind)
                WHERE status IN ('QUEUED','CLAIMED') DO NOTHING;
            SELECT job.id, job.status INTO live_id, live_status
            FROM control.review_job AS job
            WHERE job.workspace_id = p_workspace_id
              AND job.job_kind = 'DISCARD'
              AND job.status IN ('QUEUED','CLAIMED')
            FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'DISCARD_ENQUEUE_CONFLICT'
                    USING ERRCODE = 'P0002';
            END IF;
            UPDATE control.workspace
               SET status = 'DISCARD_QUEUED'
             WHERE control.workspace.id = p_workspace_id
               AND control.workspace.status IN ('REVIEW','CONFLICTED');
            RETURN QUERY SELECT live_id, live_status;
        END;
        $fn$
        """
    )

    # 2. Human Control entry point: exact site binding + authority
    #    re-check, then the enqueue (no snapshot input).
    op.execute(
        """
        CREATE FUNCTION control.slaif_human_agent_workspace_discard(
            p_workspace_id uuid, p_site_id uuid, p_user_id uuid
        ) RETURNS TABLE (job_id uuid, status text)
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            discard_row record;
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
                WHERE 'workspace:discard' = ANY(m.effective_permissions)
            ) THEN
                RETURN;
            END IF;
            SELECT * INTO discard_row
            FROM control.slaif_workspace_discard(
                p_workspace_id, p_user_id
            );
            SELECT w.status INTO ws_status
            FROM control.workspace AS w
            WHERE w.id = p_workspace_id;
            RETURN QUERY
                SELECT discard_row.job_id,
                       COALESCE(ws_status, discard_row.status);
        END;
        $fn$
        """
    )

    # Function grants: exact caller sets (070/071/072 pattern).
    for function in (_DISCARD_FUNCTION, _HUMAN_DISCARD_FUNCTION):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        for role in _REVOKE_ROLES:
            op.execute(f"REVOKE ALL ON FUNCTION {function} FROM {role}")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_DISCARD_FUNCTION} TO slaif_control")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_HUMAN_DISCARD_FUNCTION} TO slaif_control")


def downgrade() -> None:
    # Drop exactly the functions created/replaced by the upgrade.
    op.execute(
        "DROP FUNCTION IF EXISTS control.slaif_human_agent_workspace_discard("
        "uuid, uuid, uuid)"
    )
    op.execute("DROP FUNCTION IF EXISTS control.slaif_workspace_discard(uuid, uuid)")

    # Restore the exact 024_001 discard stub (byte-identical body).
    op.execute(
        """
        CREATE FUNCTION control.slaif_workspace_discard(
            p_workspace_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE control.workspace SET
                status = 'DISCARDED',
                discarded_at = CURRENT_TIMESTAMP
            WHERE id = p_workspace_id AND status IN ('REVIEW', 'CONFLICTED', 'FREEZING');
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND_OR_WRONG_STATE' USING ERRCODE = 'P0002';
            END IF;
        END;
        $fn$
    """
    )
    # A bare downgrade must not leave the restored stub with the implicit
    # PUBLIC execute that PostgreSQL grants to every new function: revoke
    # from PUBLIC and every long-lived role, then grant exactly the 024_001
    # caller set (the 072_001 claim-function downgrade pattern).
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_workspace_discard(uuid) FROM PUBLIC"
    )
    for role in _REVOKE_ROLES:
        op.execute(
            f"REVOKE ALL ON FUNCTION control.slaif_workspace_discard(uuid) FROM {role}"
        )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_workspace_discard(uuid) TO slaif_control"
    )
