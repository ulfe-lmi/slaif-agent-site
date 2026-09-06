# ruff: noqa: E501
"""Skip hidden COW iterator rows during redirect page dependency checks."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "055_001"
down_revision: str | Sequence[str] | None = "054_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Keep the pre-070 migration byte-immutable while aligning the human
    # editor's lifecycle lock with the shared Agent lifecycle lock.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_human_editor_workspace_assert(
            p_workspace_id uuid, p_human_user_id uuid, p_site_id uuid,
            p_human_session_id uuid, p_permission_key text, p_lock boolean
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            session_text text;
            operation_text text;
            session_uuid uuid;
            operation_uuid uuid;
        BEGIN
            session_text := NULLIF(current_setting('app.session_id', true), '');
            operation_text := NULLIF(current_setting('app.operation_id', true), '');
            BEGIN
                session_uuid := session_text::uuid;
                operation_uuid := operation_text::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'HUMAN_EDITOR_COW_CONTEXT_INVALID'
                    USING ERRCODE = '22023';
            END;
            IF session_uuid IS DISTINCT FROM p_workspace_id
               OR operation_uuid IS NULL
            THEN
                RAISE EXCEPTION 'HUMAN_EDITOR_COW_CONTEXT_INVALID'
                    USING ERRCODE = '22023';
            END IF;
            IF p_lock THEN
                PERFORM pg_advisory_xact_lock_shared(
                    hashtextextended(p_workspace_id::text, 280)
                );
            END IF;
            IF NOT EXISTS (
                SELECT 1
                FROM control.workspace AS workspace
                JOIN control.user_account AS account
                  ON account.id = workspace.created_by
                JOIN control.site AS site ON site.id = workspace.site_id
                JOIN control.user_session AS session
                  ON session.id = p_human_session_id
                 AND session.user_account_id = p_human_user_id
                WHERE workspace.id = p_workspace_id
                  AND workspace.site_id = p_site_id
                  AND workspace.created_by = p_human_user_id
                  AND workspace.actor_type = 'HUMAN'
                  AND workspace.status = 'ACTIVE'
                  AND workspace.expires_at > CURRENT_TIMESTAMP
                  AND workspace.id = (
                      SELECT selected.id
                      FROM control.workspace AS selected
                      WHERE selected.site_id = p_site_id
                        AND selected.created_by = p_human_user_id
                        AND selected.actor_type = 'HUMAN'
                        AND selected.status = 'ACTIVE'
                        AND selected.expires_at > CURRENT_TIMESTAMP
                      ORDER BY selected.created_at DESC, selected.id DESC
                      LIMIT 1
                  )
                  AND account.status = 'ACTIVE'
                  AND site.status = 'ACTIVE'
                  AND session.revoked_at IS NULL
                  AND session.absolute_expires_at > CURRENT_TIMESTAMP
            ) THEN
                RAISE EXCEPTION 'HUMAN_EDITOR_WORKSPACE_NOT_ACTIVE'
                    USING ERRCODE = 'P0002';
            END IF;
            IF NOT (
                EXISTS (
                    SELECT 1
                    FROM control.platform_administrator AS administrator
                    WHERE administrator.user_account_id = p_human_user_id
                )
                OR EXISTS (
                    SELECT 1
                    FROM control.slaif_effective_human_membership(
                        p_human_user_id, p_site_id
                    ) AS membership
                    WHERE p_permission_key = ANY(membership.effective_permissions)
                )
            ) THEN
                RAISE EXCEPTION 'HUMAN_EDITOR_PERMISSION_REVOKED'
                    USING ERRCODE = 'P0002';
            END IF;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_redirect_page_target_dependency(
            p_site_id uuid, p_route text, p_page_id uuid
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE incoming record; candidate record; default_locale text;
        BEGIN
            SELECT l.tag INTO default_locale FROM content.site_locale l
            WHERE l.site_id=p_site_id AND l.enabled AND l.is_default;
            FOR incoming IN
                SELECT r.* FROM content.redirect r
                WHERE r.site_id=p_site_id AND r.target=p_route
            LOOP
                FOR candidate IN
                    SELECT p.id FROM content.page p
                    WHERE p.site_id=p_site_id AND p.id<>p_page_id
                      AND p.deleted_at IS NULL AND p.route_template IS NULL
                      AND p.locale=coalesce(incoming.locale,default_locale)
                LOOP
                    BEGIN
                        IF content.slaif_agent_page_effective_route(candidate.id)=p_route
                        THEN
                            CONTINUE;
                        END IF;
                    EXCEPTION WHEN SQLSTATE 'P0002' THEN
                        -- A concurrent COW tombstone is not a live alternate
                        -- route and must not escape as top-level PAGE_NOT_FOUND.
                        CONTINUE;
                    END;
                END LOOP;
                IF EXISTS (
                    SELECT 1 FROM content.redirect alternate
                    WHERE alternate.site_id=p_site_id
                      AND alternate.source_route=p_route
                      AND (
                        (incoming.locale IS NOT NULL AND
                         (alternate.locale=incoming.locale OR alternate.locale IS NULL))
                        OR (incoming.locale IS NULL AND alternate.locale IS NULL)
                      )
                ) THEN
                    CONTINUE;
                END IF;
                RETURN true;
            END LOOP;
            RETURN false;
        END; $fn$
        """
    )
    for function in ("content.slaif_redirect_page_target_dependency(uuid,text,uuid)",):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")


def downgrade() -> None:
    # 051's implementation is recreated by the preceding immutable migration
    # only on a full fresh downgrade path; keep the function owner restricted.
    op.execute(
        "DROP FUNCTION IF EXISTS content.slaif_redirect_page_target_dependency(uuid,text,uuid)"
    )
