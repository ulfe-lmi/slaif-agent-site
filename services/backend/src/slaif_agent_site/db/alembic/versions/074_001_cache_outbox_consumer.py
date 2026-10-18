# ruff: noqa: E501
"""Outbox consumer: durable claim/retry/terminal columns + functions (083/3).

The 072_001 ``control.cache_outbox`` row emitted inside the accept
reviewer transaction had no consumer. This increment makes the outbox
lifecycle real: a durable claim (``FOR UPDATE SKIP LOCKED``, id order,
bounded attempt budget) and an idempotent terminal consume, both
callable by the review worker under its existing narrow credential.

Upgrade:
1. Four columns on ``control.cache_outbox``:
   ``attempt_count INTEGER NOT NULL DEFAULT 0
   CHECK (attempt_count >= 0)``; ``last_attempt_at TIMESTAMPTZ``;
   ``consumed_at TIMESTAMPTZ``; ``last_error TEXT`` (stable code or
   NULL).
2. ``control.slaif_cache_outbox_claim(p_limit integer)``
   ``RETURNS TABLE (id bigint, site_id uuid, workspace_id uuid,
   event_kind text, payload jsonb, attempt_count integer)``,
   ``SECURITY DEFINER SET search_path = pg_catalog``,
   ``OWNER slaif_owner``: rejects ``p_limit`` outside 1..64 with the
   stable ``OUTBOX_CLAIM_LIMIT_INVALID`` (ERRCODE ``22023``); CTE
   ``pick`` selects ``id`` from unconsumed rows with
   ``attempt_count < 25`` (the named plpgsql constant
   ``max_attempts`` — the single source of retry exhaustion) in id
   order ``FOR UPDATE SKIP LOCKED LIMIT p_limit``; the outer UPDATE
   increments ``attempt_count``, stamps ``last_attempt_at``, and
   RETURNs the row tuple. A claim therefore commits the attempt
   increment: death between claim and consume leaves the row
   re-claimable, and the row is processed exactly once in effect
   (single ``consumed_at``).
3. ``control.slaif_cache_outbox_consume(p_id bigint, p_error text)``
   ``RETURNS TABLE (consumed bigint)``, same discipline:
   ``UPDATE consumed_at = now(), last_error = p_error WHERE
   id = p_id AND consumed_at IS NULL RETURNING id`` — idempotent: an
   already-consumed row returns 0 rows and changes nothing.
4. Exact new grants: ``GRANT UPDATE ON control.cache_outbox TO
   slaif_review_worker`` (the ONLY new table grant) and
   ``GRANT EXECUTE`` on both new functions TO ``slaif_review_worker``.
   No new roles, no memberships, no other GRANT/REVOKE. Function
   grants are first revoked from PUBLIC and every long-lived role
   (070/071/072/073 pattern) so the reconcile's re-apply is the single
   source of truth; the durable re-application of both EXECUTE grants
   plus the UPDATE table grant lives in ``db/privileges.py``
   (``REVIEW_WORKER_FUNCTIONS`` + the cache_outbox table grant), which
   re-applies the exact registry on every HARDENED reconcile.

Downgrade drops both functions, revokes exactly the added grants, and
drops exactly the four columns; the post-downgrade state is the
byte-exact 073_001 ``cache_outbox`` (query-verified by the 083-3-a
round-trip test).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "074_001"
down_revision: str | Sequence[str] | None = "073_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CLAIM_FUNCTION = "control.slaif_cache_outbox_claim(integer)"
_CONSUME_FUNCTION = "control.slaif_cache_outbox_consume(bigint, text)"

# Every long-lived role (070/071/072/073 pattern): function grants are
# revoked from all of them before the exact intended grant is re-added.
# The review worker is included so the explicit GRANT below is the
# single intended grant; the privilege reconcile re-applies the same
# exact set on every HARDENED reconcile.
_REVOKE_ROLES = (
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
    # 1. Durable claim/retry/terminal columns.
    op.execute(
        "ALTER TABLE control.cache_outbox "
        "ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0 "
        "CHECK (attempt_count >= 0)"
    )
    op.execute(
        "ALTER TABLE control.cache_outbox ADD COLUMN last_attempt_at TIMESTAMPTZ"
    )
    op.execute("ALTER TABLE control.cache_outbox ADD COLUMN consumed_at TIMESTAMPTZ")
    op.execute("ALTER TABLE control.cache_outbox ADD COLUMN last_error TEXT")

    # 2. Durable claim: id order, SKIP LOCKED, bounded attempt budget.
    #    The 25-attempt budget is the named constant (pinned by test);
    #    it is the single source of retry exhaustion.
    op.execute(
        """
        CREATE FUNCTION control.slaif_cache_outbox_claim(p_limit integer)
        RETURNS TABLE (
            id bigint,
            site_id uuid,
            workspace_id uuid,
            event_kind text,
            payload jsonb,
            attempt_count integer
        ) LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        #variable_conflict use_column
        DECLARE
            max_attempts constant integer := 25;
        BEGIN
            IF p_limit IS NULL OR p_limit < 1 OR p_limit > 64 THEN
                RAISE EXCEPTION 'OUTBOX_CLAIM_LIMIT_INVALID'
                    USING ERRCODE = '22023';
            END IF;
            RETURN QUERY
            WITH pick AS (
                SELECT id FROM control.cache_outbox
                WHERE consumed_at IS NULL AND attempt_count < max_attempts
                ORDER BY id
                FOR UPDATE SKIP LOCKED
                LIMIT p_limit
            )
            UPDATE control.cache_outbox AS row
               SET attempt_count = row.attempt_count + 1,
                   last_attempt_at = now()
              FROM pick
             WHERE row.id = pick.id
            RETURNING row.id, row.site_id, row.workspace_id,
                      row.event_kind, row.payload, row.attempt_count;
        END;
        $fn$
        """
    )

    # 3. Idempotent terminal consume (0 rows on replay).
    op.execute(
        """
        CREATE FUNCTION control.slaif_cache_outbox_consume(
            p_id bigint, p_error text
        ) RETURNS TABLE (consumed bigint) LANGUAGE plpgsql
        SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            RETURN QUERY
            UPDATE control.cache_outbox
               SET consumed_at = now(), last_error = p_error
             WHERE id = p_id AND consumed_at IS NULL
            RETURNING id;
        END;
        $fn$
        """
    )

    # Function grants: exact caller sets (070/071/072/073 pattern).
    for function in (_CLAIM_FUNCTION, _CONSUME_FUNCTION):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        for role in _REVOKE_ROLES:
            op.execute(f"REVOKE ALL ON FUNCTION {function} FROM {role}")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_CLAIM_FUNCTION} TO slaif_review_worker")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_CONSUME_FUNCTION} TO slaif_review_worker")

    # The ONLY new table grant: the worker consumes rows it claims.
    op.execute("GRANT UPDATE ON control.cache_outbox TO slaif_review_worker")


def downgrade() -> None:
    # Drop exactly the two functions, then revoke exactly the grants
    # added, then drop exactly the four columns (073_001 state).
    op.execute(
        "DROP FUNCTION IF EXISTS control.slaif_cache_outbox_consume(bigint, text)"
    )
    op.execute("DROP FUNCTION IF EXISTS control.slaif_cache_outbox_claim(integer)")
    op.execute("REVOKE UPDATE ON control.cache_outbox FROM slaif_review_worker")
    op.execute(
        "ALTER TABLE control.cache_outbox DROP COLUMN attempt_count, "
        "DROP COLUMN last_attempt_at, DROP COLUMN consumed_at, "
        "DROP COLUMN last_error"
    )
