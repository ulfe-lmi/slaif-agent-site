# ruff: noqa: E501
"""Add one-time run-bound Render browser-preview authorization."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "036_001"
down_revision: str | Sequence[str] | None = "035_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SIGNATURE = "uuid,uuid,uuid,uuid,text,text,text[],bigint,integer,text,boolean"


def _secure_function() -> None:
    function = f"control.slaif_render_browser_preview_authorize({_SIGNATURE})"
    op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
    for role in (
        "slaif_control",
        "slaif_editor_runtime",
        "slaif_agent_runtime",
        "slaif_public_reader",
        "slaif_preview_reader",
        "slaif_reviewer",
        "slaif_scheduler",
        "slaif_media",
        "slaif_gc",
    ):
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM {role}")
    op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_preview_reader")


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE control.browser_run
            ADD COLUMN preview_nonce_digest TEXT,
            ADD COLUMN preview_token_used_at TIMESTAMPTZ,
            ADD CONSTRAINT browser_run_preview_token_shape CHECK (
                (preview_nonce_digest IS NULL AND preview_token_used_at IS NULL)
                OR
                (preview_nonce_digest ~ '^[0-9a-f]{64}$'
                    AND preview_token_used_at IS NOT NULL
                    AND preview_token_used_at >= created_at)
            )
        """
    )
    op.execute(
        "ALTER TABLE audit.browser_event DROP CONSTRAINT browser_event_type_allowed"
    )
    op.execute(
        """
        ALTER TABLE audit.browser_event
            ADD CONSTRAINT browser_event_type_allowed CHECK (
                event_type IN (
                    'ENQUEUED','LEASED','LEASE_RENEWED','LEASE_RELEASED',
                    'COMPLETED','FAILED','TIMED_OUT','CANCELLED',
                    'ARTIFACT_REGISTERED','MAX_ATTEMPTS',
                    'PREVIEW_TOKEN_CONSUMED'
                )
            )
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_render_browser_preview_authorize(
            p_capability_id uuid, p_site_id uuid, p_workspace_id uuid,
            p_run_id uuid, p_route text, p_target text,
            p_evidence text[], p_artifact_bytes bigint,
            p_duration_seconds integer, p_nonce_digest text,
            p_consume boolean
        ) RETURNS TABLE (workspace_id uuid, site_id uuid, run_id uuid)
        LANGUAGE plpgsql SECURITY DEFINER VOLATILE
        SET search_path = pg_catalog ROWS 1 AS $fn$
        DECLARE
            selected_run record;
        BEGIN
            IF p_capability_id IS NULL OR p_site_id IS NULL
               OR p_workspace_id IS NULL OR p_run_id IS NULL
               OR p_route IS NULL OR p_target IS NULL
               OR p_evidence IS NULL OR array_ndims(p_evidence) <> 1
               OR p_artifact_bytes NOT BETWEEN 0 AND 1073741824
               OR p_duration_seconds NOT BETWEEN 5 AND 600
               OR p_nonce_digest !~ '^[0-9a-f]{64}$'
               OR p_consume IS NULL
            THEN
                RETURN;
            END IF;

            PERFORM pg_advisory_xact_lock_shared(
                hashtextextended(p_workspace_id::text, 280)
            );
            SELECT run.* INTO selected_run
            FROM control.browser_run AS run
            JOIN control.capability AS capability
              ON capability.id = run.capability_id
             AND capability.workspace_id = run.workspace_id
            JOIN control.workspace AS workspace
              ON workspace.id = run.workspace_id
             AND workspace.site_id = run.site_id
             AND workspace.created_by = run.delegator_id
            JOIN control.site AS site ON site.id = run.site_id
            WHERE run.id = p_run_id
              AND run.capability_id = p_capability_id
              AND run.site_id = p_site_id
              AND run.workspace_id = p_workspace_id
              AND run.route = p_route
              AND run.target = p_target
              AND run.evidence = p_evidence
              AND run.reserved_artifact_bytes = p_artifact_bytes
              AND run.max_duration_seconds = p_duration_seconds
              AND run.state IN ('QUEUED','RUNNING')
              AND run.expires_at > CURRENT_TIMESTAMP
              AND capability.revoked_at IS NULL
              AND capability.expires_at > CURRENT_TIMESTAMP
              AND jsonb_typeof(capability.scopes) = 'array'
              AND capability.scopes ? 'preview:inspect'
              AND workspace.status = 'ACTIVE'
              AND workspace.expires_at > CURRENT_TIMESTAMP
              AND site.status = 'ACTIVE'
            FOR UPDATE OF run;
            IF NOT FOUND THEN
                RETURN;
            END IF;

            IF p_consume THEN
                UPDATE control.browser_run AS run
                SET preview_nonce_digest = p_nonce_digest,
                    preview_token_used_at = CURRENT_TIMESTAMP
                WHERE run.id = p_run_id
                  AND run.preview_nonce_digest IS NULL
                  AND run.preview_token_used_at IS NULL;
                IF NOT FOUND THEN
                    RETURN;
                END IF;
                INSERT INTO audit.browser_event (
                    run_id, operation_id, capability_id, workspace_id,
                    site_id, delegator_id, event_type, attempt, details
                ) VALUES (
                    p_run_id, selected_run.operation_id, p_capability_id,
                    p_workspace_id, p_site_id, selected_run.delegator_id,
                    'PREVIEW_TOKEN_CONSUMED', selected_run.attempt_count,
                    '{}'::jsonb
                );
            ELSIF selected_run.preview_nonce_digest IS DISTINCT FROM p_nonce_digest
               OR selected_run.preview_token_used_at IS NULL
            THEN
                RETURN;
            END IF;

            RETURN QUERY SELECT p_workspace_id, p_site_id, p_run_id;
        END;
        $fn$
        """
    )
    _secure_function()


def downgrade() -> None:
    op.execute(
        f"DROP FUNCTION IF EXISTS control.slaif_render_browser_preview_authorize({_SIGNATURE})"
    )
    op.execute(
        "ALTER TABLE audit.browser_event DROP CONSTRAINT browser_event_type_allowed"
    )
    op.execute(
        """
        ALTER TABLE audit.browser_event
            ADD CONSTRAINT browser_event_type_allowed CHECK (
                event_type IN (
                    'ENQUEUED','LEASED','LEASE_RENEWED','LEASE_RELEASED',
                    'COMPLETED','FAILED','TIMED_OUT','CANCELLED',
                    'ARTIFACT_REGISTERED','MAX_ATTEMPTS'
                )
            )
        """
    )
    op.execute(
        "ALTER TABLE control.browser_run "
        "DROP CONSTRAINT IF EXISTS browser_run_preview_token_shape, "
        "DROP COLUMN IF EXISTS preview_token_used_at, "
        "DROP COLUMN IF EXISTS preview_nonce_digest"
    )
