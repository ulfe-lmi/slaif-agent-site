# ruff: noqa: E501
"""Couple semantic Agent audit identity and resource delete quotas."""

from __future__ import annotations

from alembic import op

revision = "045_001"
down_revision = "044_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE audit.agent_mutation
            ADD COLUMN http_method text,
            ADD COLUMN quota_kind text,
            ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
                (http_method IS NULL AND quota_kind IS NULL)
                OR (
                    action = 'CONTENT_TYPE_CREATED'
                    AND resource_type = 'content_type'
                    AND http_method = 'POST'
                    AND response_status = 201
                    AND quota_kind = 'mutation'
                )
                OR (
                    action = 'CONTENT_TYPE_UPDATED'
                    AND resource_type = 'content_type'
                    AND http_method = 'PATCH'
                    AND response_status = 200
                    AND quota_kind = 'mutation'
                )
                OR (
                    action = 'CONTENT_TYPE_DELETED'
                    AND resource_type = 'content_type'
                    AND http_method = 'DELETE'
                    AND response_status = 200
                    AND quota_kind = 'delete'
                )
                OR (
                    action = 'FIELD_DEFINITION_CREATED'
                    AND resource_type = 'field_definition'
                    AND http_method = 'POST'
                    AND response_status = 201
                    AND quota_kind = 'mutation'
                )
                OR (
                    action = 'FIELD_DEFINITION_UPDATED'
                    AND resource_type = 'field_definition'
                    AND http_method = 'PATCH'
                    AND response_status = 200
                    AND quota_kind = 'mutation'
                )
                OR (
                    action = 'FIELD_DEFINITION_DELETED'
                    AND resource_type = 'field_definition'
                    AND http_method = 'DELETE'
                    AND response_status = 200
                    AND quota_kind = 'delete'
                )
            )
        """
    )

    # The ten-argument function remains the completion boundary for the
    # existing item/page/component routes. Type and field routes must use the
    # typed contract below, so the legacy boundary fails closed for them.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_idempotency_complete(
            p_capability_id uuid, p_workspace_id uuid, p_idempotency_key text,
            p_request_digest text, p_operation_id uuid, p_status_code integer,
            p_response_body jsonb, p_resource_type text, p_resource_id uuid,
            p_site_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            expected_site uuid;
        BEGIN
            SELECT workspace.site_id
            INTO expected_site
            FROM control.capability AS capability
            JOIN control.workspace AS workspace
              ON workspace.id = capability.workspace_id
            WHERE capability.id = p_capability_id
              AND capability.workspace_id = p_workspace_id
              AND workspace.site_id = p_site_id;
            IF expected_site IS NULL
               OR p_status_code NOT BETWEEN 200 AND 299
               OR p_response_body IS NULL
               OR p_resource_id IS NULL
               OR p_resource_type NOT IN (
                   'content_type', 'field_definition', 'content_item',
                   'page', 'composition_node'
               )
               OR p_resource_type IN ('content_type', 'field_definition')
            THEN
                RAISE EXCEPTION 'INVALID_IDEMPOTENCY_COMPLETION'
                    USING ERRCODE = 'P0001';
            END IF;

            UPDATE control.agent_idempotency
            SET status_code = p_status_code,
                response_body = p_response_body,
                resource_type = p_resource_type,
                resource_id = p_resource_id,
                completed_at = CURRENT_TIMESTAMP
            WHERE capability_id = p_capability_id
              AND workspace_id = p_workspace_id
              AND idempotency_key = p_idempotency_key
              AND request_digest = p_request_digest
              AND operation_id = p_operation_id
              AND status_code IS NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'IDEMPOTENCY_RESERVATION_NOT_FOUND'
                    USING ERRCODE = 'P0002';
            END IF;

            INSERT INTO audit.agent_mutation (
                operation_id, capability_id, workspace_id, site_id,
                resource_type, resource_id, request_digest, response_status
            ) VALUES (
                p_operation_id, p_capability_id, p_workspace_id, p_site_id,
                p_resource_type, p_resource_id, p_request_digest, p_status_code
            );
        END;
        $fn$
        """
    )
    op.execute(
        """
        DROP FUNCTION control.slaif_agent_idempotency_complete(
            uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text
        )
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_idempotency_complete(
            p_capability_id uuid, p_workspace_id uuid, p_idempotency_key text,
            p_request_digest text, p_operation_id uuid, p_status_code integer,
            p_response_body jsonb, p_resource_type text, p_resource_id uuid,
            p_site_id uuid, p_action text, p_http_method text,
            p_quota_kind text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            expected_site uuid;
        BEGIN
            IF p_capability_id IS NULL
               OR p_workspace_id IS NULL
               OR p_idempotency_key IS NULL
               OR length(p_idempotency_key) NOT BETWEEN 1 AND 128
               OR p_idempotency_key !~ '^[A-Za-z0-9._~-]+$'
               OR p_request_digest IS NULL
               OR p_request_digest !~ '^[0-9a-f]{64}$'
               OR p_operation_id IS NULL
               OR p_resource_id IS NULL
               OR p_action IS NULL
               OR p_http_method IS NULL
               OR p_quota_kind IS NULL
               OR NOT (
                   (p_action = 'CONTENT_TYPE_CREATED'
                    AND p_resource_type = 'content_type'
                    AND p_http_method = 'POST'
                    AND p_status_code = 201
                    AND p_quota_kind = 'mutation')
                   OR (p_action = 'CONTENT_TYPE_UPDATED'
                    AND p_resource_type = 'content_type'
                    AND p_http_method = 'PATCH'
                    AND p_status_code = 200
                    AND p_quota_kind = 'mutation')
                   OR (p_action = 'CONTENT_TYPE_DELETED'
                    AND p_resource_type = 'content_type'
                    AND p_http_method = 'DELETE'
                    AND p_status_code = 200
                    AND p_quota_kind = 'delete')
                   OR (p_action = 'FIELD_DEFINITION_CREATED'
                    AND p_resource_type = 'field_definition'
                    AND p_http_method = 'POST'
                    AND p_status_code = 201
                    AND p_quota_kind = 'mutation')
                   OR (p_action = 'FIELD_DEFINITION_UPDATED'
                    AND p_resource_type = 'field_definition'
                    AND p_http_method = 'PATCH'
                    AND p_status_code = 200
                    AND p_quota_kind = 'mutation')
                   OR (p_action = 'FIELD_DEFINITION_DELETED'
                    AND p_resource_type = 'field_definition'
                    AND p_http_method = 'DELETE'
                    AND p_status_code = 200
                    AND p_quota_kind = 'delete')
               )
               OR p_response_body IS NULL
               OR jsonb_typeof(p_response_body) <> 'object'
               OR jsonb_typeof(p_response_body->'record') <> 'object'
               OR p_response_body->>'action' IS DISTINCT FROM p_action
               OR p_response_body->>'operation_id' IS DISTINCT FROM
                  p_operation_id::text
               OR p_response_body->'record'->>'id' IS DISTINCT FROM
                  p_resource_id::text
            THEN
                RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION'
                    USING ERRCODE = 'P0001';
            END IF;

            SELECT workspace.site_id
            INTO expected_site
            FROM control.capability AS capability
            JOIN control.workspace AS workspace
              ON workspace.id = capability.workspace_id
            WHERE capability.id = p_capability_id
              AND capability.workspace_id = p_workspace_id
              AND workspace.site_id = p_site_id;
            IF expected_site IS NULL THEN
                RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION'
                    USING ERRCODE = 'P0001';
            END IF;

            UPDATE control.agent_idempotency
            SET status_code = p_status_code,
                response_body = p_response_body,
                resource_type = p_resource_type,
                resource_id = p_resource_id,
                completed_at = CURRENT_TIMESTAMP
            WHERE capability_id = p_capability_id
              AND workspace_id = p_workspace_id
              AND idempotency_key = p_idempotency_key
              AND request_digest = p_request_digest
              AND operation_id = p_operation_id
              AND status_code IS NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'IDEMPOTENCY_RESERVATION_NOT_FOUND'
                    USING ERRCODE = 'P0002';
            END IF;

            INSERT INTO audit.agent_mutation (
                operation_id, capability_id, workspace_id, site_id,
                resource_type, resource_id, request_digest, response_status,
                action, http_method, quota_kind
            ) VALUES (
                p_operation_id, p_capability_id, p_workspace_id, p_site_id,
                p_resource_type, p_resource_id, p_request_digest, p_status_code,
                p_action, p_http_method, p_quota_kind
            );
        END;
        $fn$
        """
    )

    # Delete reservation is serialized by the capability row update. The
    # trusted resource helper is evaluated inside the COW transaction, so a
    # malformed constraint or a context mismatch fails before any charge.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_quota_consume(
            p_capability_id uuid, p_workspace_id uuid, p_kind text
        ) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            consumed boolean := false;
            resource_max_deletes integer;
            workspace_site uuid;
            context_workspace uuid;
        BEGIN
            IF p_kind NOT IN ('request','mutation','delete','upload') THEN
                RETURN false;
            END IF;
            IF p_kind='request' THEN
                UPDATE control.capability c SET request_used=c.request_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id
                JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL
                  AND c.expires_at>CURRENT_TIMESTAMP
                  AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP
                  AND s.status='ACTIVE' AND a.status='ACTIVE'
                  AND c.request_used<c.request_quota
                  AND (EXISTS (SELECT 1 FROM control.platform_administrator pa
                       WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                    OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(
                       COALESCE(w.delegator_id,w.created_by),w.site_id) m
                       WHERE m.effective_ceiling >= CASE w.delegation_preset
                         WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1
                         WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2
                         WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3
                         WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END))
                RETURNING true INTO consumed;
            ELSIF p_kind='mutation' THEN
                UPDATE control.capability c SET mutation_used=c.mutation_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id
                JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL
                  AND c.expires_at>CURRENT_TIMESTAMP
                  AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP
                  AND s.status='ACTIVE' AND a.status='ACTIVE'
                  AND c.mutation_used<c.mutation_quota
                  AND (EXISTS (SELECT 1 FROM control.platform_administrator pa
                       WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                    OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(
                       COALESCE(w.delegator_id,w.created_by),w.site_id) m
                       WHERE m.effective_ceiling >= CASE w.delegation_preset
                         WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1
                         WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2
                         WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3
                         WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END))
                RETURNING true INTO consumed;
            ELSIF p_kind='delete' THEN
                BEGIN
                    context_workspace := NULLIF(
                        current_setting('app.session_id', true), ''
                    )::uuid;
                EXCEPTION WHEN invalid_text_representation THEN
                    RETURN false;
                END;
                IF context_workspace IS NULL
                   OR context_workspace IS DISTINCT FROM p_workspace_id
                THEN
                    RETURN false;
                END IF;
                SELECT workspace.site_id INTO workspace_site
                FROM control.workspace AS workspace
                WHERE workspace.id=p_workspace_id;
                IF workspace_site IS NULL THEN
                    RETURN false;
                END IF;
                SELECT constraints.max_deletes INTO resource_max_deletes
                FROM control.slaif_agent_resource_constraints(workspace_site)
                    AS constraints;
                UPDATE control.capability c SET delete_used=c.delete_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id
                JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL
                  AND c.expires_at>CURRENT_TIMESTAMP
                  AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP
                  AND s.status='ACTIVE' AND a.status='ACTIVE'
                  AND c.delete_used<c.delete_quota
                  AND (resource_max_deletes IS NULL
                       OR c.delete_used<resource_max_deletes)
                  AND (EXISTS (SELECT 1 FROM control.platform_administrator pa
                       WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                    OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(
                       COALESCE(w.delegator_id,w.created_by),w.site_id) m
                       WHERE m.effective_ceiling >= CASE w.delegation_preset
                         WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1
                         WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2
                         WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3
                         WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END))
                RETURNING true INTO consumed;
            ELSE
                UPDATE control.capability c SET upload_used=c.upload_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id
                JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL
                  AND c.expires_at>CURRENT_TIMESTAMP
                  AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP
                  AND s.status='ACTIVE' AND a.status='ACTIVE'
                  AND c.upload_used<c.upload_quota
                  AND (EXISTS (SELECT 1 FROM control.platform_administrator pa
                       WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                    OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(
                       COALESCE(w.delegator_id,w.created_by),w.site_id) m
                       WHERE m.effective_ceiling >= CASE w.delegation_preset
                         WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1
                         WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2
                         WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3
                         WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END))
                RETURNING true INTO consumed;
            END IF;
            RETURN COALESCE(consumed,false);
        END; $fn$
        """
    )

    for name, signature in (
        (
            "slaif_agent_idempotency_complete",
            "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid",
        ),
        (
            "slaif_agent_idempotency_complete",
            "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text",
        ),
        ("slaif_agent_quota_consume", "uuid,uuid,text"),
    ):
        op.execute(f'ALTER FUNCTION control.{name}({signature}) OWNER TO "slaif_owner"')
        op.execute(
            f"REVOKE ALL ON FUNCTION control.{name}({signature}) "
            "FROM PUBLIC, slaif_control, slaif_editor_runtime, "
            "slaif_public_reader, slaif_preview_reader, slaif_reviewer, "
            "slaif_scheduler, slaif_media, slaif_gc"
        )
        op.execute(
            f"GRANT EXECUTE ON FUNCTION control.{name}({signature}) "
            'TO "slaif_agent_runtime"'
        )
    op.execute(
        "REVOKE ALL ON TABLE audit.agent_mutation FROM PUBLIC, "
        "slaif_control, slaif_editor_runtime, slaif_agent_runtime, "
        "slaif_public_reader, slaif_preview_reader, slaif_reviewer, "
        "slaif_scheduler, slaif_media, slaif_gc"
    )


def downgrade() -> None:
    # Remove the strict completion before restoring the 044 overloads.
    op.execute(
        """
        DROP FUNCTION control.slaif_agent_idempotency_complete(
            uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text
        )
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_idempotency_complete(
            p_capability_id uuid, p_workspace_id uuid, p_idempotency_key text,
            p_request_digest text, p_operation_id uuid, p_status_code integer,
            p_response_body jsonb, p_resource_type text, p_resource_id uuid,
            p_site_id uuid, p_action text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            IF p_action NOT IN ('CONTENT_TYPE_CREATED','CONTENT_TYPE_UPDATED',
                                'CONTENT_TYPE_DELETED',
                                'FIELD_DEFINITION_CREATED',
                                'FIELD_DEFINITION_UPDATED',
                                'FIELD_DEFINITION_DELETED')
               OR p_status_code NOT BETWEEN 200 AND 299 THEN
                RAISE EXCEPTION 'INVALID_IDEMPOTENCY_COMPLETION'
                    USING ERRCODE='P0001';
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
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_idempotency_complete(
            p_capability_id uuid, p_workspace_id uuid, p_idempotency_key text,
            p_request_digest text, p_operation_id uuid, p_status_code integer,
            p_response_body jsonb, p_resource_type text, p_resource_id uuid,
            p_site_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            expected_site uuid;
        BEGIN
            SELECT workspace.site_id
            INTO expected_site
            FROM control.capability AS capability
            JOIN control.workspace AS workspace
              ON workspace.id = capability.workspace_id
            WHERE capability.id = p_capability_id
              AND capability.workspace_id = p_workspace_id
              AND workspace.site_id = p_site_id;
            IF expected_site IS NULL
               OR p_status_code NOT BETWEEN 200 AND 299
               OR p_response_body IS NULL
               OR p_resource_id IS NULL
               OR p_resource_type NOT IN (
                   'content_type', 'field_definition', 'content_item',
                   'page', 'composition_node'
               )
            THEN
                RAISE EXCEPTION 'INVALID_IDEMPOTENCY_COMPLETION'
                    USING ERRCODE = 'P0001';
            END IF;
            UPDATE control.agent_idempotency
            SET status_code = p_status_code,
                response_body = p_response_body,
                resource_type = p_resource_type,
                resource_id = p_resource_id,
                completed_at = CURRENT_TIMESTAMP
            WHERE capability_id = p_capability_id
              AND workspace_id = p_workspace_id
              AND idempotency_key = p_idempotency_key
              AND request_digest = p_request_digest
              AND operation_id = p_operation_id
              AND status_code IS NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'IDEMPOTENCY_RESERVATION_NOT_FOUND'
                    USING ERRCODE = 'P0002';
            END IF;
            INSERT INTO audit.agent_mutation (
                operation_id, capability_id, workspace_id, site_id,
                resource_type, resource_id, request_digest, response_status
            ) VALUES (
                p_operation_id, p_capability_id, p_workspace_id, p_site_id,
                p_resource_type, p_resource_id, p_request_digest, p_status_code
            );
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_quota_consume(
            p_capability_id uuid, p_workspace_id uuid, p_kind text
        ) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE consumed boolean := false;
        BEGIN
            IF p_kind NOT IN ('request','mutation','delete','upload') THEN
                RETURN false;
            END IF;
            IF p_kind='request' THEN
                UPDATE control.capability c SET request_used=c.request_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id
                JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL
                  AND c.expires_at>CURRENT_TIMESTAMP AND w.status='ACTIVE'
                  AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE'
                  AND a.status='ACTIVE' AND c.request_used<c.request_quota
                  AND (EXISTS (SELECT 1 FROM control.platform_administrator pa
                       WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                    OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(
                       COALESCE(w.delegator_id,w.created_by),w.site_id) m
                       WHERE m.effective_ceiling >= CASE w.delegation_preset
                         WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1
                         WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2
                         WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3
                         WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END))
                RETURNING true INTO consumed;
            ELSIF p_kind='mutation' THEN
                UPDATE control.capability c SET mutation_used=c.mutation_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id
                JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL
                  AND c.expires_at>CURRENT_TIMESTAMP AND w.status='ACTIVE'
                  AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE'
                  AND a.status='ACTIVE' AND c.mutation_used<c.mutation_quota
                  AND (EXISTS (SELECT 1 FROM control.platform_administrator pa
                       WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                    OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(
                       COALESCE(w.delegator_id,w.created_by),w.site_id) m
                       WHERE m.effective_ceiling >= CASE w.delegation_preset
                         WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1
                         WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2
                         WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3
                         WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END))
                RETURNING true INTO consumed;
            ELSIF p_kind='delete' THEN
                UPDATE control.capability c SET delete_used=c.delete_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id
                JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL
                  AND c.expires_at>CURRENT_TIMESTAMP AND w.status='ACTIVE'
                  AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE'
                  AND a.status='ACTIVE' AND c.delete_used<c.delete_quota
                  AND (EXISTS (SELECT 1 FROM control.platform_administrator pa
                       WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                    OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(
                       COALESCE(w.delegator_id,w.created_by),w.site_id) m
                       WHERE m.effective_ceiling >= CASE w.delegation_preset
                         WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1
                         WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2
                         WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3
                         WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END))
                RETURNING true INTO consumed;
            ELSE
                UPDATE control.capability c SET upload_used=c.upload_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id
                JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL
                  AND c.expires_at>CURRENT_TIMESTAMP AND w.status='ACTIVE'
                  AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE'
                  AND a.status='ACTIVE' AND c.upload_used<c.upload_quota
                  AND (EXISTS (SELECT 1 FROM control.platform_administrator pa
                       WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                    OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(
                       COALESCE(w.delegator_id,w.created_by),w.site_id) m
                       WHERE m.effective_ceiling >= CASE w.delegation_preset
                         WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1
                         WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2
                         WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3
                         WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END))
                RETURNING true INTO consumed;
            END IF;
            RETURN COALESCE(consumed,false);
        END; $fn$
        """
    )
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP COLUMN http_method, DROP COLUMN quota_kind"
    )

    for name, signature in (
        (
            "slaif_agent_idempotency_complete",
            "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid",
        ),
        (
            "slaif_agent_idempotency_complete",
            "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text",
        ),
        ("slaif_agent_quota_consume", "uuid,uuid,text"),
    ):
        op.execute(f'ALTER FUNCTION control.{name}({signature}) OWNER TO "slaif_owner"')
        op.execute(
            f"REVOKE ALL ON FUNCTION control.{name}({signature}) FROM PUBLIC, "
            "slaif_control, slaif_editor_runtime, slaif_public_reader, "
            "slaif_preview_reader, slaif_reviewer, slaif_scheduler, "
            "slaif_media, slaif_gc"
        )
        op.execute(
            f"GRANT EXECUTE ON FUNCTION control.{name}({signature}) "
            'TO "slaif_agent_runtime"'
        )
