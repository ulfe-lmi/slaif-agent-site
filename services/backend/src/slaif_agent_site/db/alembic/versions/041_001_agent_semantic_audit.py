# ruff: noqa: E501
"""Persist semantic Agent mutation actions alongside durable audit rows."""

from __future__ import annotations

from alembic import op

revision = "041_001"
down_revision = "040_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE audit.agent_mutation ADD COLUMN IF NOT EXISTS action text NOT NULL DEFAULT 'LEGACY_MUTATION'"
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_idempotency_complete(
            p_capability_id uuid, p_workspace_id uuid, p_idempotency_key text,
            p_request_digest text, p_operation_id uuid, p_status_code integer,
            p_response_body jsonb, p_resource_type text, p_resource_id uuid,
            p_site_id uuid, p_action text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            IF p_action NOT IN ('CONTENT_TYPE_CREATED','CONTENT_TYPE_UPDATED','CONTENT_TYPE_DELETED',
                                'FIELD_DEFINITION_CREATED','FIELD_DEFINITION_UPDATED','FIELD_DEFINITION_DELETED')
               OR p_status_code NOT BETWEEN 200 AND 299 THEN
                RAISE EXCEPTION 'INVALID_IDEMPOTENCY_COMPLETION' USING ERRCODE='P0001';
            END IF;
            PERFORM control.slaif_agent_idempotency_complete(
                p_capability_id,p_workspace_id,p_idempotency_key,p_request_digest,
                p_operation_id,p_status_code,p_response_body,p_resource_type,
                p_resource_id,p_site_id
            );
            UPDATE audit.agent_mutation SET action=p_action
            WHERE operation_id=p_operation_id;
        END;
        $fn$
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP FUNCTION IF EXISTS control.slaif_agent_idempotency_complete(uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text)"
    )
    op.execute("ALTER TABLE audit.agent_mutation DROP COLUMN IF EXISTS action")
