# ruff: noqa: E501
"""Harden Media workspace locking and repair Editor media COW functions."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "031_001"
down_revision: str | Sequence[str] | None = "030_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_media_workspace_assert(
            p_workspace_id uuid, p_human_user_id uuid, p_site_id uuid,
            p_human_session_id uuid, p_permission text, p_operation_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE session_text text;
        DECLARE operation_text text;
        DECLARE session_uuid uuid;
        DECLARE operation_uuid uuid;
        BEGIN
            session_text := NULLIF(current_setting('app.session_id', true), '');
            operation_text := NULLIF(current_setting('app.operation_id', true), '');
            BEGIN
                session_uuid := session_text::uuid;
                operation_uuid := operation_text::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'MEDIA_COW_CONTEXT_INVALID'
                    USING ERRCODE = '22023';
            END;
            IF session_uuid IS DISTINCT FROM p_workspace_id
               OR operation_uuid IS DISTINCT FROM p_operation_id
            THEN
                RAISE EXCEPTION 'MEDIA_COW_CONTEXT_INVALID' USING ERRCODE = '22023';
            END IF;
            PERFORM pg_advisory_xact_lock(
                hashtextextended(p_workspace_id::text, 280)
            );
            IF NOT EXISTS (
                SELECT 1
                FROM control.workspace AS workspace
                JOIN control.site AS site ON site.id = workspace.site_id
                JOIN control.user_account AS account ON account.id = workspace.created_by
                JOIN control.user_session AS session
                  ON session.id = p_human_session_id
                 AND session.user_account_id = p_human_user_id
                WHERE workspace.id = p_workspace_id
                  AND workspace.site_id = p_site_id
                  AND workspace.created_by = p_human_user_id
                  AND workspace.actor_type = 'HUMAN'
                  AND workspace.status = 'ACTIVE'
                  AND workspace.expires_at > CURRENT_TIMESTAMP
                  AND site.status = 'ACTIVE'
                  AND account.status = 'ACTIVE'
                  AND session.revoked_at IS NULL
                  AND session.absolute_expires_at > CURRENT_TIMESTAMP
                  AND (
                      EXISTS (
                          SELECT 1 FROM control.platform_administrator AS administrator
                          WHERE administrator.user_account_id = p_human_user_id
                      )
                      OR EXISTS (
                          SELECT 1
                          FROM control.slaif_effective_human_membership(
                              p_human_user_id, p_site_id
                          ) AS membership
                          WHERE p_permission = ANY(membership.effective_permissions)
                      )
                  )
            ) THEN
                RAISE EXCEPTION 'MEDIA_WORKSPACE_NOT_AUTHORIZED' USING ERRCODE = 'P0002';
            END IF;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_media_update(
            p_media_id uuid, p_alt_text text, p_metadata jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, uploaded_by uuid, filename text,
            mime_type text, size_bytes bigint, content_hash text,
            storage_key text, alt_text text, metadata jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.media_asset AS media_asset SET
                alt_text = COALESCE(p_alt_text, media_asset.alt_text),
                metadata = COALESCE(p_metadata, media_asset.metadata),
                updated_at = CURRENT_TIMESTAMP
            WHERE media_asset.id = p_media_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT media_asset.* FROM content.media_asset AS media_asset
            WHERE media_asset.id = p_media_id;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_media_delete(
            p_media_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            DELETE FROM content.media_asset AS media_asset
            WHERE media_asset.id = p_media_id;
        END;
        $fn$
        """
    )


def downgrade() -> None:
    # The replacement is compatible with 023_001; the 030_001 downgrade then
    # removes the Media-only objects while the original Editor functions remain
    # usable until their own migration is downgraded.
    pass
