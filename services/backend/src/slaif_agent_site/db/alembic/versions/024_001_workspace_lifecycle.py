# ruff: noqa: E501
"""Create workspace table with lifecycle functions."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "024_001"
down_revision: str | Sequence[str] | None = "023_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Workspace lives in control schema (not COW) per architecture §10
    op.execute("""
        CREATE TABLE IF NOT EXISTS control.workspace (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL REFERENCES control.site(id),
            created_by UUID NOT NULL REFERENCES control.user_account(id),
            actor_type TEXT NOT NULL DEFAULT 'HUMAN',
            title TEXT NOT NULL,
            task_description TEXT NOT NULL DEFAULT '',
            delegation_preset TEXT NOT NULL,
            effective_scopes JSONB NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'CREATING',
            base_site_revision BIGINT NOT NULL DEFAULT 0,
            operation_watermark BIGINT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL,
            frozen_at TIMESTAMPTZ,
            accepted_at TIMESTAMPTZ,
            discarded_at TIMESTAMPTZ
        )
    """)

    # Create workspace
    op.execute("""
        CREATE FUNCTION control.slaif_workspace_create(
            p_site_id uuid, p_created_by uuid, p_title text,
            p_description text, p_preset text, p_scopes jsonb,
            p_duration_hours integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, created_by uuid, title text,
            status text, delegation_preset text,
            effective_scopes jsonb, created_at timestamptz, expires_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            INSERT INTO control.workspace
                (site_id, created_by, title, task_description, delegation_preset,
                 effective_scopes, status, expires_at)
            VALUES (p_site_id, p_created_by, p_title, p_description, p_preset,
                    p_scopes, 'ACTIVE', now() + make_interval(hours => p_duration_hours));
            RETURN QUERY SELECT w.id, w.site_id, w.created_by, w.title,
                w.status, w.delegation_preset, w.effective_scopes,
                w.created_at, w.expires_at
            FROM control.workspace w
            WHERE w.site_id = p_site_id AND w.created_by = p_created_by
              AND w.title = p_title
            ORDER BY w.created_at DESC LIMIT 1;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_workspace_create(uuid,uuid,text,text,text,jsonb,integer) TO slaif_control"
    )

    # Get workspace
    op.execute("""
        CREATE FUNCTION control.slaif_workspace_get(
            p_workspace_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, created_by uuid, title text,
            status text, delegation_preset text,
            effective_scopes jsonb, created_at timestamptz, expires_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT id, site_id, created_by, title,
                   status, delegation_preset, effective_scopes,
                   created_at, expires_at
            FROM control.workspace WHERE id = p_workspace_id
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_workspace_get(uuid) TO slaif_control, slaif_editor_runtime"
    )

    # Freeze workspace (transition to FREEZING then REVIEW)
    op.execute("""
        CREATE FUNCTION control.slaif_workspace_freeze(
            p_workspace_id uuid
        ) RETURNS TABLE (
            id uuid, status text
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE control.workspace SET
                status = 'FREEZING',
                frozen_at = CURRENT_TIMESTAMP
            WHERE id = p_workspace_id AND status = 'ACTIVE';
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND_OR_NOT_ACTIVE' USING ERRCODE = 'P0002';
            END IF;
            UPDATE control.workspace SET status = 'REVIEW' WHERE id = p_workspace_id;
            RETURN QUERY SELECT w.id, w.status FROM control.workspace w WHERE w.id = p_workspace_id;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_workspace_freeze(uuid) TO slaif_control"
    )

    # Discard workspace
    op.execute("""
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
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_workspace_discard(uuid) TO slaif_control"
    )


def downgrade() -> None:
    for fn in (
        "slaif_workspace_create(uuid,uuid,text,text,text,jsonb,integer)",
        "slaif_workspace_get(uuid)",
        "slaif_workspace_freeze(uuid)",
        "slaif_workspace_discard(uuid)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS control.{fn} CASCADE")
    op.execute("DROP TABLE IF EXISTS control.workspace CASCADE")
