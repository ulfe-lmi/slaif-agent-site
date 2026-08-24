# ruff: noqa: E501
"""Harden Render preview session semantics and transaction rechecks."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "033_001"
down_revision: str | Sequence[str] | None = "032_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "DROP FUNCTION IF EXISTS "
        "control.slaif_render_preview_authorize(text,bytea,uuid,uuid)"
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_render_preview_authorize(
            p_public_id text,
            p_secret_digest bytea,
            p_workspace_id uuid,
            p_site_id uuid,
            p_idle_seconds integer,
            p_touch_interval_seconds integer,
            p_recent_auth_seconds integer
        ) RETURNS TABLE (
            user_account_id uuid,
            session_id uuid,
            workspace_id uuid,
            site_id uuid,
            last_seen_at timestamptz,
            absolute_expires_at timestamptz,
            recent_auth boolean
        ) LANGUAGE plpgsql SECURITY DEFINER VOLATILE
        SET search_path = pg_catalog
        ROWS 1 AS $fn$
        DECLARE
            selected_session control.user_session%ROWTYPE;
            selected_workspace control.workspace%ROWTYPE;
            account_status text;
            site_status text;
            now_at timestamptz;
            touched_at timestamptz;
        BEGIN
            IF p_public_id IS NULL
               OR p_secret_digest IS NULL
               OR octet_length(p_secret_digest) IS DISTINCT FROM 32
               OR p_idle_seconds <= 0
               OR p_touch_interval_seconds <= 0
               OR p_recent_auth_seconds <= 0
               OR p_public_id !~ '^sas2_[0-9a-f]{32}$'
            THEN
                RETURN;
            END IF;

            SELECT session.* INTO selected_session
            FROM control.user_session AS session
            WHERE session.public_id = p_public_id
              AND session.secret_digest = p_secret_digest
            FOR UPDATE;
            IF NOT FOUND THEN
                RETURN;
            END IF;

            SELECT account.status INTO account_status
            FROM control.user_account AS account
            WHERE account.id = selected_session.user_account_id;
            SELECT site.status INTO site_status
            FROM control.site AS site
            WHERE site.id = p_site_id;
            SELECT workspace.* INTO selected_workspace
            FROM control.workspace AS workspace
            WHERE workspace.id = p_workspace_id
              AND workspace.site_id = p_site_id
            FOR UPDATE;
            now_at := CURRENT_TIMESTAMP;
            IF account_status IS DISTINCT FROM 'ACTIVE'
               OR site_status IS DISTINCT FROM 'ACTIVE'
               OR selected_session.revoked_at IS NOT NULL
               OR selected_session.absolute_expires_at <= now_at
               OR selected_session.last_seen_at
                    + make_interval(secs => p_idle_seconds) <= now_at
               OR selected_workspace.id IS NULL
               OR selected_workspace.actor_type NOT IN ('HUMAN', 'AGENT', 'IMPORT')
               OR selected_workspace.status <> 'ACTIVE'
               OR selected_workspace.expires_at <= now_at
            THEN
                RETURN;
            END IF;

            IF selected_workspace.created_by <> selected_session.user_account_id
               AND NOT EXISTS (
                   SELECT 1
                   FROM control.slaif_effective_human_membership(
                       selected_session.user_account_id, p_site_id
                   ) AS membership
                   WHERE 'workspace:read-all' = ANY(membership.effective_permissions)
               )
            THEN
                RETURN;
            END IF;
            IF NOT (
                EXISTS (
                    SELECT 1
                    FROM control.platform_administrator AS administrator
                    WHERE administrator.user_account_id = selected_session.user_account_id
                )
                OR EXISTS (
                    SELECT 1
                    FROM control.slaif_effective_human_membership(
                        selected_session.user_account_id, p_site_id
                    ) AS membership
                    WHERE 'preview:inspect' = ANY(membership.effective_permissions)
                )
            )
            THEN
                RETURN;
            END IF;

            touched_at := selected_session.last_seen_at;
            IF selected_session.last_seen_at
                    + make_interval(secs => p_touch_interval_seconds) <= now_at
            THEN
                UPDATE control.user_session
                SET last_seen_at = now_at,
                    recent_auth_at = CASE
                        WHEN recent_auth_at + make_interval(secs => p_recent_auth_seconds)
                             <= now_at THEN now_at
                        ELSE recent_auth_at
                    END
                WHERE id = selected_session.id
                RETURNING last_seen_at INTO touched_at;
            END IF;

            -- This shared lock is held through the caller's COW transaction.
            PERFORM pg_advisory_xact_lock_shared(
                hashtextextended(p_workspace_id::text, 280)
            );
            RETURN QUERY SELECT selected_session.user_account_id,
                selected_session.id, selected_workspace.id, selected_workspace.site_id,
                touched_at, selected_session.absolute_expires_at,
                selected_session.recent_auth_at + make_interval(secs => p_recent_auth_seconds)
                    > now_at;
        END;
        $fn$
        """
    )
    op.execute(
        "ALTER FUNCTION control.slaif_render_preview_authorize(text,bytea,uuid,uuid,integer,integer,integer) "
        "OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_render_preview_authorize(text,bytea,uuid,uuid,integer,integer,integer) "
        "FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_render_preview_authorize(text,bytea,uuid,uuid,integer,integer,integer) "
        "TO slaif_preview_reader"
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_site_render_catalog(
            p_site_id uuid
        ) RETURNS text LANGUAGE sql SECURITY DEFINER STABLE
        SET search_path = pg_catalog AS $fn$
            SELECT site.component_catalog_version
            FROM control.site AS site
            WHERE site.id = p_site_id AND site.status = 'ACTIVE'
        $fn$
        """
    )
    op.execute(
        "ALTER FUNCTION control.slaif_site_render_catalog(uuid) OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_site_render_catalog(uuid) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_site_render_catalog(uuid) "
        "TO slaif_public_reader, slaif_preview_reader"
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS control.slaif_site_render_catalog(uuid)")
    op.execute(
        "DROP FUNCTION IF EXISTS "
        "control.slaif_render_preview_authorize(text,bytea,uuid,uuid,integer,integer,integer)"
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_render_preview_authorize(
            p_public_id text, p_secret_digest bytea, p_workspace_id uuid, p_site_id uuid
        ) RETURNS TABLE (user_account_id uuid, session_id uuid, workspace_id uuid, site_id uuid)
        LANGUAGE sql SECURITY DEFINER STABLE SET search_path = pg_catalog ROWS 1 AS $fn$
            SELECT account.id, session.id, workspace.id, workspace.site_id
            FROM control.user_session AS session
            JOIN control.user_account AS account ON account.id = session.user_account_id
            JOIN control.workspace AS workspace ON workspace.id = p_workspace_id
            JOIN control.site AS site ON site.id = workspace.site_id
            WHERE session.public_id = p_public_id AND session.secret_digest = p_secret_digest
              AND workspace.site_id = p_site_id AND session.revoked_at IS NULL
              AND session.absolute_expires_at > CURRENT_TIMESTAMP
              AND account.status = 'ACTIVE' AND site.status = 'ACTIVE'
              AND workspace.actor_type = 'HUMAN' AND workspace.status = 'ACTIVE'
              AND workspace.expires_at > CURRENT_TIMESTAMP
        $fn$
        """
    )
    op.execute(
        "ALTER FUNCTION control.slaif_render_preview_authorize(text,bytea,uuid,uuid) "
        "OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_render_preview_authorize(text,bytea,uuid,uuid) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_render_preview_authorize(text,bytea,uuid,uuid) TO slaif_preview_reader"
    )
