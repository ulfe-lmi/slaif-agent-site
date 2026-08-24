# ruff: noqa: E501
"""Make Render preview authorization lock-first and touch-only."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "034_001"
down_revision: str | Sequence[str] | None = "033_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_FUNCTION_SIGNATURE = "text,bytea,uuid,uuid,integer,integer,integer"


def _secure_preview_function() -> None:
    op.execute(
        f"ALTER FUNCTION control.slaif_render_preview_authorize({_FUNCTION_SIGNATURE}) "
        "OWNER TO slaif_owner"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION control.slaif_render_preview_authorize({_FUNCTION_SIGNATURE}) "
        "FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION control.slaif_render_preview_authorize({_FUNCTION_SIGNATURE}) "
        "TO slaif_preview_reader"
    )


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_render_preview_authorize(
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
               OR p_workspace_id IS NULL
               OR p_site_id IS NULL
               OR octet_length(p_secret_digest) IS DISTINCT FROM 32
               OR p_idle_seconds <= 0
               OR p_touch_interval_seconds <= 0
               OR p_recent_auth_seconds <= 0
               OR p_public_id !~ '^sas2_[0-9a-f]{32}$'
            THEN
                RETURN;
            END IF;

            -- The shared workspace lock is the first mutable-authority lock.
            -- Freeze/mutation paths take the matching exclusive lock before
            -- touching workspace/session state, preventing row-lock inversion.
            PERFORM pg_advisory_xact_lock_shared(
                hashtextextended(p_workspace_id::text, 280)
            );

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
                UPDATE control.user_session AS session
                SET last_seen_at = now_at
                WHERE session.id = selected_session.id
                RETURNING session.last_seen_at INTO touched_at;
            END IF;

            RETURN QUERY SELECT selected_session.user_account_id,
                selected_session.id, selected_workspace.id, selected_workspace.site_id,
                touched_at, selected_session.absolute_expires_at,
                selected_session.recent_auth_at + make_interval(secs => p_recent_auth_seconds)
                    > now_at;
        END;
        $fn$
        """
    )
    _secure_preview_function()


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_render_preview_authorize(
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
                UPDATE control.user_session AS session
                SET last_seen_at = now_at,
                    recent_auth_at = CASE
                        WHEN recent_auth_at + make_interval(secs => p_recent_auth_seconds)
                             <= now_at THEN now_at
                        ELSE recent_auth_at
                    END
                WHERE session.id = selected_session.id
                RETURNING session.last_seen_at INTO touched_at;
            END IF;

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
    _secure_preview_function()
