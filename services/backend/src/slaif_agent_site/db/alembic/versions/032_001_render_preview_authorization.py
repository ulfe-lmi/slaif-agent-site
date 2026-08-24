"""Add the narrow Render-owned human preview authorization boundary."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "032_001"
down_revision: str | Sequence[str] | None = "031_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION control.slaif_render_preview_authorize(
            p_public_id text,
            p_secret_digest bytea,
            p_workspace_id uuid,
            p_site_id uuid
        ) RETURNS TABLE (
            user_account_id uuid,
            session_id uuid,
            workspace_id uuid,
            site_id uuid
        ) LANGUAGE sql SECURITY DEFINER STABLE
        SET search_path = pg_catalog
        ROWS 1 AS $fn$
            SELECT account.id, session.id, workspace.id, workspace.site_id
            FROM control.user_session AS session
            JOIN control.user_account AS account
              ON account.id = session.user_account_id
            JOIN control.workspace AS workspace
              ON workspace.id = p_workspace_id
             AND workspace.site_id = p_site_id
            JOIN control.site AS site
              ON site.id = workspace.site_id
            WHERE session.public_id = p_public_id
              AND session.secret_digest = p_secret_digest
              AND session.revoked_at IS NULL
              AND session.absolute_expires_at > CURRENT_TIMESTAMP
              AND account.status = 'ACTIVE'
              AND site.status = 'ACTIVE'
              AND workspace.actor_type = 'HUMAN'
              AND workspace.status = 'ACTIVE'
              AND workspace.expires_at > CURRENT_TIMESTAMP
              AND (
                  EXISTS (
                      SELECT 1
                      FROM control.platform_administrator AS administrator
                      WHERE administrator.user_account_id = account.id
                  )
                  OR EXISTS (
                      SELECT 1
                      FROM control.slaif_effective_human_membership(
                          account.id, workspace.site_id
                      ) AS membership
                      WHERE 'preview:inspect' = ANY(membership.effective_permissions)
                  )
              )
              AND (
                  workspace.created_by = account.id
                  OR EXISTS (
                      SELECT 1
                      FROM control.slaif_effective_human_membership(
                          account.id, workspace.site_id
                      ) AS membership
                      WHERE 'workspace:read-all' = ANY(membership.effective_permissions)
                  )
              )
        $fn$
        """
    )
    op.execute(
        "ALTER FUNCTION control.slaif_render_preview_authorize(text,bytea,uuid,uuid) "
        "OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION "
        "control.slaif_render_preview_authorize(text,bytea,uuid,uuid) "
        "FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION "
        "control.slaif_render_preview_authorize(text,bytea,uuid,uuid) "
        "TO slaif_preview_reader"
    )


def downgrade() -> None:
    op.execute(
        "DROP FUNCTION IF EXISTS "
        "control.slaif_render_preview_authorize(text,bytea,uuid,uuid)"
    )
