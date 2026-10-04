# ruff: noqa: E501
"""Add the bounded human-authorized Editor envelope for AGENT workspaces."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "069_001"
down_revision: str | Sequence[str] | None = "068_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION control.slaif_human_agent_workspace_editor_assert(
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
                RAISE EXCEPTION 'HUMAN_AGENT_EDITOR_COW_CONTEXT_INVALID'
                    USING ERRCODE = '22023';
            END;
            IF session_uuid IS DISTINCT FROM p_workspace_id
               OR operation_uuid IS NULL
            THEN
                RAISE EXCEPTION 'HUMAN_AGENT_EDITOR_COW_CONTEXT_INVALID'
                    USING ERRCODE = '22023';
            END IF;
            IF p_lock THEN
                PERFORM pg_advisory_xact_lock(
                    hashtextextended(p_workspace_id::text, 280)
                );
            END IF;
            IF NOT EXISTS (
                SELECT 1
                FROM control.workspace AS workspace
                JOIN control.user_account AS delegator
                  ON delegator.id = COALESCE(
                      workspace.delegator_id, workspace.created_by
                  )
                JOIN control.site AS site ON site.id = workspace.site_id
                JOIN control.user_session AS session
                  ON session.id = p_human_session_id
                 AND session.user_account_id = p_human_user_id
                WHERE workspace.id = p_workspace_id
                  AND workspace.site_id = p_site_id
                  AND workspace.actor_type = 'AGENT'
                  AND workspace.status = 'ACTIVE'
                  AND workspace.expires_at > CURRENT_TIMESTAMP
                  AND site.status = 'ACTIVE'
                  AND delegator.status = 'ACTIVE'
                  AND session.revoked_at IS NULL
                  AND session.absolute_expires_at > CURRENT_TIMESTAMP
                  AND (
                      COALESCE(
                          workspace.delegator_id, workspace.created_by
                      ) = p_human_user_id
                      OR EXISTS (
                          SELECT 1
                          FROM control.platform_administrator AS administrator
                          WHERE administrator.user_account_id = p_human_user_id
                      )
                      OR EXISTS (
                          SELECT 1
                          FROM control.slaif_effective_human_membership(
                              p_human_user_id, p_site_id
                          ) AS membership
                          WHERE 'workspace:read-all'
                              = ANY(membership.effective_permissions)
                      )
                  )
                  AND (
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
                          WHERE p_permission_key
                              = ANY(membership.effective_permissions)
                      )
                  )
            ) THEN
                RAISE EXCEPTION 'HUMAN_AGENT_EDITOR_WORKSPACE_NOT_ACCESSIBLE'
                    USING ERRCODE = 'P0002';
            END IF;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_human_agent_editor_idempotency_begin(
            p_workspace_id uuid, p_human_user_id uuid, p_site_id uuid,
            p_human_session_id uuid, p_permission_key text,
            p_idempotency_key text,
            p_request_digest text, p_operation_id uuid
        ) RETURNS TABLE (
            state text, operation_id uuid, status_code integer,
            response_body jsonb
        ) LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            existing control.human_editor_idempotency%ROWTYPE;
        BEGIN
            PERFORM control.slaif_human_agent_workspace_editor_assert(
                p_workspace_id, p_human_user_id, p_site_id,
                p_human_session_id, p_permission_key, true
            );
            IF p_idempotency_key IS NULL
               OR p_idempotency_key !~ '^[A-Za-z0-9._~-]{1,128}$'
               OR p_request_digest IS NULL
               OR p_request_digest !~ '^[0-9a-f]{64}$'
               OR p_operation_id IS NULL
            THEN
                RAISE EXCEPTION 'HUMAN_AGENT_EDITOR_IDEMPOTENCY_INPUT'
                    USING ERRCODE = 'P0001';
            END IF;

            INSERT INTO control.human_editor_idempotency (
                workspace_id, human_user_id, site_id, idempotency_key,
                request_digest, operation_id
            ) VALUES (
                p_workspace_id, p_human_user_id, p_site_id, p_idempotency_key,
                p_request_digest, p_operation_id
            ) ON CONFLICT (workspace_id, idempotency_key) DO NOTHING;
            IF FOUND THEN
                RETURN QUERY SELECT
                    'STARTED'::text, p_operation_id, NULL::integer,
                    NULL::jsonb;
                RETURN;
            END IF;

            SELECT * INTO existing
            FROM control.human_editor_idempotency AS idempotency
            WHERE idempotency.workspace_id = p_workspace_id
              AND idempotency.idempotency_key = p_idempotency_key
            FOR UPDATE;
            IF existing.request_digest <> p_request_digest THEN
                RETURN QUERY SELECT
                    'MISMATCH'::text, existing.operation_id,
                    NULL::integer, NULL::jsonb;
                RETURN;
            END IF;
            IF existing.status_code IS NULL THEN
                RAISE EXCEPTION 'HUMAN_AGENT_EDITOR_IDEMPOTENCY_IN_PROGRESS'
                    USING ERRCODE = 'P0001';
            END IF;
            RETURN QUERY SELECT
                'REPLAY'::text, existing.operation_id,
                existing.status_code, existing.response_body;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_human_agent_editor_idempotency_complete(
            p_workspace_id uuid, p_human_user_id uuid, p_site_id uuid,
            p_human_session_id uuid, p_permission_key text,
            p_idempotency_key text,
            p_request_digest text, p_operation_id uuid, p_status_code integer,
            p_response_body jsonb, p_action text, p_resource_type text,
            p_resource_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_human_agent_workspace_editor_assert(
                p_workspace_id, p_human_user_id, p_site_id,
                p_human_session_id, p_permission_key, true
            );
            IF p_status_code NOT BETWEEN 200 AND 299
               OR p_resource_id IS NULL
               OR p_action IS NULL OR length(p_action) NOT BETWEEN 1 AND 256
               OR p_resource_type IS NULL
               OR length(p_resource_type) NOT BETWEEN 1 AND 128
            THEN
                RAISE EXCEPTION 'HUMAN_AGENT_EDITOR_COMPLETION_INPUT'
                    USING ERRCODE = 'P0001';
            END IF;
            INSERT INTO audit.human_editor_mutation (
                operation_id, human_user_id, workspace_id, site_id, action,
                resource_type, resource_id, request_digest, response_status
            ) VALUES (
                p_operation_id, p_human_user_id, p_workspace_id, p_site_id,
                p_action, p_resource_type, p_resource_id, p_request_digest,
                p_status_code
            );
            UPDATE control.human_editor_idempotency AS idempotency
            SET status_code = p_status_code,
                response_body = COALESCE(p_response_body, '{}'::jsonb),
                completed_at = CURRENT_TIMESTAMP
            WHERE idempotency.workspace_id = p_workspace_id
              AND idempotency.idempotency_key = p_idempotency_key
              AND idempotency.request_digest = p_request_digest
              AND idempotency.operation_id = p_operation_id
              AND idempotency.status_code IS NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'HUMAN_AGENT_EDITOR_IDEMPOTENCY_NOT_STARTED'
                    USING ERRCODE = 'P0002';
            END IF;
        END;
        $fn$
        """
    )

    for function in (
        "control.slaif_human_agent_workspace_editor_assert(uuid,uuid,uuid,uuid,text,boolean)",
        "control.slaif_human_agent_editor_idempotency_begin(uuid,uuid,uuid,uuid,text,text,text,uuid)",
        "control.slaif_human_agent_editor_idempotency_complete(uuid,uuid,uuid,uuid,text,text,text,uuid,integer,jsonb,text,text,uuid)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_editor_runtime")


def downgrade() -> None:
    for function in (
        "slaif_human_agent_editor_idempotency_complete(uuid,uuid,uuid,uuid,text,text,text,uuid,integer,jsonb,text,text,uuid)",
        "slaif_human_agent_editor_idempotency_begin(uuid,uuid,uuid,uuid,text,text,text,uuid)",
        "slaif_human_agent_workspace_editor_assert(uuid,uuid,uuid,uuid,text,boolean)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS control.{function} CASCADE")
