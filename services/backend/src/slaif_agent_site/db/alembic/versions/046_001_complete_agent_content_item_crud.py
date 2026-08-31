# ruff: noqa: E501
"""Complete Agent content-item CRUD and couple all content-model wrappers to quota authority."""

from __future__ import annotations

from alembic import op

revision = "046_001"
down_revision = "045_001"
branch_labels = None
depends_on = None


_TYPE_SIGNATURE = "uuid,text,jsonb,text,jsonb"
_TYPE_UPDATE_SIGNATURE = "uuid,uuid,jsonb,text,jsonb,integer"
_TYPE_DELETE_SIGNATURE = "uuid,uuid,integer"
_FIELD_CREATE_SIGNATURE = (
    "uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb"
)
_FIELD_UPDATE_SIGNATURE = (
    "uuid,uuid,uuid,text,boolean,boolean,integer,integer,jsonb,jsonb,integer"
)
_FIELD_DELETE_SIGNATURE = "uuid,uuid,uuid,integer"
_ITEM_CREATE_SIGNATURE = "uuid,uuid,text,text,jsonb"
_ITEM_CREATE_OLD_SIGNATURE = "uuid,uuid,text,text,jsonb,integer"
_ITEM_GET_SIGNATURE = "uuid,uuid"
_ITEM_UPDATE_SIGNATURE = "uuid,uuid,text,text,jsonb,integer"
_ITEM_DELETE_SIGNATURE = "uuid,uuid,integer"


def _drop_agent_content_functions() -> None:
    for name, signature in (
        ("slaif_agent_content_type_list", "uuid"),
        ("slaif_agent_content_type_get", "uuid,uuid"),
        ("slaif_agent_field_definition_list", "uuid,uuid"),
        ("slaif_agent_content_item_list", "uuid,uuid"),
        ("slaif_agent_content_item_get", _ITEM_GET_SIGNATURE),
        ("slaif_agent_content_type_create", _TYPE_SIGNATURE),
        ("slaif_agent_content_type_update", _TYPE_UPDATE_SIGNATURE),
        ("slaif_agent_content_type_delete", _TYPE_DELETE_SIGNATURE),
        ("slaif_agent_field_definition_create", _FIELD_CREATE_SIGNATURE),
        ("slaif_agent_field_definition_update", _FIELD_UPDATE_SIGNATURE),
        ("slaif_agent_field_definition_delete", _FIELD_DELETE_SIGNATURE),
        ("slaif_agent_content_item_create", _ITEM_CREATE_OLD_SIGNATURE),
        ("slaif_agent_content_item_create", _ITEM_CREATE_SIGNATURE),
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{name}({signature}) CASCADE")


def upgrade() -> None:
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(
        """
        ALTER TABLE audit.agent_mutation
            ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
                (http_method IS NULL AND quota_kind IS NULL)
                OR (action = 'CONTENT_TYPE_CREATED' AND resource_type = 'content_type'
                    AND http_method = 'POST' AND response_status = 201
                    AND quota_kind = 'mutation')
                OR (action = 'CONTENT_TYPE_UPDATED' AND resource_type = 'content_type'
                    AND http_method = 'PATCH' AND response_status = 200
                    AND quota_kind = 'mutation')
                OR (action = 'CONTENT_TYPE_DELETED' AND resource_type = 'content_type'
                    AND http_method = 'DELETE' AND response_status = 200
                    AND quota_kind = 'delete')
                OR (action = 'FIELD_DEFINITION_CREATED'
                    AND resource_type = 'field_definition' AND http_method = 'POST'
                    AND response_status = 201 AND quota_kind = 'mutation')
                OR (action = 'FIELD_DEFINITION_UPDATED'
                    AND resource_type = 'field_definition' AND http_method = 'PATCH'
                    AND response_status = 200 AND quota_kind = 'mutation')
                OR (action = 'FIELD_DEFINITION_DELETED'
                    AND resource_type = 'field_definition' AND http_method = 'DELETE'
                    AND response_status = 200 AND quota_kind = 'delete')
                OR (action = 'CONTENT_ITEM_CREATED' AND resource_type = 'content_item'
                    AND http_method = 'POST' AND response_status = 201
                    AND quota_kind = 'mutation')
                OR (action = 'CONTENT_ITEM_UPDATED' AND resource_type = 'content_item'
                    AND http_method = 'PATCH' AND response_status = 200
                    AND quota_kind = 'mutation')
                OR (action = 'CONTENT_ITEM_DELETED' AND resource_type = 'content_item'
                    AND http_method = 'DELETE' AND response_status = 200
                    AND quota_kind = 'delete')
            )
        """
    )

    # This helper binds a COW transaction to the capability selected by the
    # authenticated server. Resource constraints remain owned by the 044
    # helper; this function only establishes the missing capability identity.
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_require_capability(p_site_id uuid)
        RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            cow_workspace_id uuid;
            capability_id uuid;
            operation_id uuid;
            expected_site uuid;
            delegator_id uuid;
            preset text;
            required_level integer;
            platform_admin boolean;
            effective_ceiling integer;
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            BEGIN
                cow_workspace_id := NULLIF(current_setting('app.session_id', true), '')::uuid;
                operation_id := NULLIF(current_setting('app.operation_id', true), '')::uuid;
                capability_id := NULLIF(current_setting('app.capability_id', true), '')::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'AGENT_CAPABILITY_CONTEXT_REQUIRED'
                    USING ERRCODE = '22023';
            END;
            IF cow_workspace_id IS NULL OR operation_id IS NULL OR capability_id IS NULL THEN
                RAISE EXCEPTION 'AGENT_CAPABILITY_CONTEXT_REQUIRED'
                    USING ERRCODE = '22023';
            END IF;
            SELECT w.site_id, COALESCE(w.delegator_id, w.created_by),
                   w.delegation_preset
              INTO expected_site, delegator_id, preset
            FROM control.capability c
            JOIN control.workspace w ON w.id = c.workspace_id
            JOIN control.site s ON s.id = w.site_id
            JOIN control.user_account a
              ON a.id = COALESCE(w.delegator_id, w.created_by)
            WHERE c.id = capability_id
              AND c.workspace_id = cow_workspace_id
              AND c.revoked_at IS NULL
              AND c.expires_at > CURRENT_TIMESTAMP
              AND w.status = 'ACTIVE'
              AND w.expires_at > CURRENT_TIMESTAMP
              AND s.status = 'ACTIVE'
              AND a.status = 'ACTIVE';
            IF expected_site IS NULL OR expected_site IS DISTINCT FROM p_site_id THEN
                RAISE EXCEPTION 'AGENT_CAPABILITY_SITE_MISMATCH'
                    USING ERRCODE = 'P0002';
            END IF;
            required_level := CASE preset
                WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1
                WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2
                WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3
                WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END;
            SELECT EXISTS (
                SELECT 1 FROM control.platform_administrator pa
                WHERE pa.user_account_id = delegator_id
            ) INTO platform_admin;
            IF NOT platform_admin THEN
                SELECT MAX(m.effective_ceiling) INTO effective_ceiling
                FROM control.slaif_effective_human_membership(delegator_id, p_site_id) m;
                IF effective_ceiling IS NULL OR effective_ceiling < required_level THEN
                    RAISE EXCEPTION 'COW_AUTHORITY_REVOKED' USING ERRCODE = 'P0002';
                END IF;
            END IF;
            RETURN capability_id;
        END;
        $fn$
        """
    )
    op.execute(
        'ALTER FUNCTION control.slaif_agent_require_capability(uuid) OWNER TO "slaif_owner"'
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_agent_require_capability(uuid) "
        "FROM PUBLIC, slaif_agent_runtime, slaif_control, slaif_editor_runtime"
    )

    # The legacy ten-argument completion boundary must not be usable for any
    # content-item mutation after item actions become strict.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_idempotency_complete(
            p_capability_id uuid, p_workspace_id uuid, p_idempotency_key text,
            p_request_digest text, p_operation_id uuid, p_status_code integer,
            p_response_body jsonb, p_resource_type text, p_resource_id uuid,
            p_site_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE expected_site uuid;
        BEGIN
            SELECT workspace.site_id INTO expected_site
            FROM control.capability AS capability
            JOIN control.workspace AS workspace
              ON workspace.id = capability.workspace_id
            WHERE capability.id = p_capability_id
              AND capability.workspace_id = p_workspace_id
              AND workspace.site_id = p_site_id;
            IF expected_site IS NULL OR p_status_code NOT BETWEEN 200 AND 299
               OR p_response_body IS NULL OR p_resource_id IS NULL
               OR p_resource_type NOT IN ('content_type','field_definition',
                                           'content_item','page','composition_node')
               OR p_resource_type IN ('content_type','field_definition','content_item')
            THEN
                RAISE EXCEPTION 'INVALID_IDEMPOTENCY_COMPLETION' USING ERRCODE = 'P0001';
            END IF;
            UPDATE control.agent_idempotency
            SET status_code = p_status_code, response_body = p_response_body,
                resource_type = p_resource_type, resource_id = p_resource_id,
                completed_at = CURRENT_TIMESTAMP
            WHERE capability_id = p_capability_id AND workspace_id = p_workspace_id
              AND idempotency_key = p_idempotency_key
              AND request_digest = p_request_digest AND operation_id = p_operation_id
              AND status_code IS NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'IDEMPOTENCY_RESERVATION_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            INSERT INTO audit.agent_mutation(
                operation_id, capability_id, workspace_id, site_id, resource_type,
                resource_id, request_digest, response_status
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
        CREATE OR REPLACE FUNCTION control.slaif_agent_idempotency_complete(
            p_capability_id uuid, p_workspace_id uuid, p_idempotency_key text,
            p_request_digest text, p_operation_id uuid, p_status_code integer,
            p_response_body jsonb, p_resource_type text, p_resource_id uuid,
            p_site_id uuid, p_action text, p_http_method text, p_quota_kind text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE expected_site uuid;
        BEGIN
            IF p_capability_id IS NULL OR p_workspace_id IS NULL
               OR p_idempotency_key IS NULL
               OR length(p_idempotency_key) NOT BETWEEN 1 AND 128
               OR p_idempotency_key !~ '^[A-Za-z0-9._~-]+$'
               OR p_request_digest IS NULL OR p_request_digest !~ '^[0-9a-f]{64}$'
               OR p_operation_id IS NULL OR p_resource_id IS NULL
               OR p_action IS NULL OR p_http_method IS NULL OR p_quota_kind IS NULL
               OR NOT (
                   (p_action='CONTENT_TYPE_CREATED' AND p_resource_type='content_type'
                    AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_TYPE_UPDATED' AND p_resource_type='content_type'
                    AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_TYPE_DELETED' AND p_resource_type='content_type'
                    AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='FIELD_DEFINITION_CREATED' AND p_resource_type='field_definition'
                    AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='FIELD_DEFINITION_UPDATED' AND p_resource_type='field_definition'
                    AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='FIELD_DEFINITION_DELETED' AND p_resource_type='field_definition'
                    AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='CONTENT_ITEM_CREATED' AND p_resource_type='content_item'
                    AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_ITEM_UPDATED' AND p_resource_type='content_item'
                    AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_ITEM_DELETED' AND p_resource_type='content_item'
                    AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
               )
               OR p_response_body IS NULL OR jsonb_typeof(p_response_body) <> 'object'
               OR jsonb_typeof(p_response_body->'record') <> 'object'
               OR p_response_body->>'action' IS DISTINCT FROM p_action
               OR p_response_body->>'operation_id' IS DISTINCT FROM p_operation_id::text
               OR p_response_body->'record'->>'id' IS DISTINCT FROM p_resource_id::text
            THEN
                RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION' USING ERRCODE = 'P0001';
            END IF;
            SELECT workspace.site_id INTO expected_site
            FROM control.capability AS capability
            JOIN control.workspace AS workspace
              ON workspace.id = capability.workspace_id
            WHERE capability.id = p_capability_id
              AND capability.workspace_id = p_workspace_id
              AND workspace.site_id = p_site_id;
            IF expected_site IS NULL THEN
                RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION' USING ERRCODE = 'P0001';
            END IF;
            UPDATE control.agent_idempotency
            SET status_code = p_status_code, response_body = p_response_body,
                resource_type = p_resource_type, resource_id = p_resource_id,
                completed_at = CURRENT_TIMESTAMP
            WHERE capability_id = p_capability_id AND workspace_id = p_workspace_id
              AND idempotency_key = p_idempotency_key
              AND request_digest = p_request_digest AND operation_id = p_operation_id
              AND status_code IS NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'IDEMPOTENCY_RESERVATION_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            INSERT INTO audit.agent_mutation(
                operation_id, capability_id, workspace_id, site_id, resource_type,
                resource_id, request_digest, response_status, action, http_method,
                quota_kind
            ) VALUES (
                p_operation_id, p_capability_id, p_workspace_id, p_site_id,
                p_resource_type, p_resource_id, p_request_digest, p_status_code,
                p_action, p_http_method, p_quota_kind
            );
        END;
        $fn$
        """
    )

    _drop_agent_content_functions()

    # Read wrappers are capability-bound and filter or deny types outside the
    # immutable allowlists before returning any content.
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_list(p_site_id uuid)
        RETURNS TABLE(id uuid, site_id uuid, "key" text, labels jsonb,
            slug_pattern text, status text, definition_version integer,
            settings jsonb, created_at timestamptz, updated_at timestamptz)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE constraints record;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id);
            SELECT * INTO STRICT constraints
            FROM control.slaif_agent_resource_constraints(p_site_id);
            RETURN QUERY SELECT t.id,t.site_id,t."key",t.labels,t.slug_pattern,t.status,
                t.definition_version,t.settings,t.created_at,t.updated_at
            FROM content.content_type t
            WHERE t.site_id=p_site_id AND t.status <> 'DELETED'
              AND (coalesce(cardinality(constraints.allowed_type_ids),0)=0
                   OR t.id=ANY(constraints.allowed_type_ids))
              AND (coalesce(cardinality(constraints.allowed_type_keys),0)=0
                   OR t."key"=ANY(constraints.allowed_type_keys))
            ORDER BY t."key" COLLATE "C";
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_get(p_site_id uuid,p_type_id uuid)
        RETURNS TABLE(id uuid, site_id uuid, "key" text, labels jsonb,
            slug_pattern text, status text, definition_version integer,
            settings jsonb, created_at timestamptz, updated_at timestamptz)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE constraints record; found_type content.content_type;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id);
            SELECT t.* INTO found_type FROM content.content_type t
            WHERE t.id=p_type_id AND t.site_id=p_site_id AND t.status <> 'DELETED';
            IF NOT FOUND THEN RAISE EXCEPTION 'AGENT_TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0
               AND NOT found_type.id=ANY(constraints.allowed_type_ids)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0003'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0
               AND NOT found_type."key"=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            RETURN QUERY SELECT found_type.id,found_type.site_id,found_type."key",
                found_type.labels,found_type.slug_pattern,found_type.status,
                found_type.definition_version,found_type.settings,found_type.created_at,
                found_type.updated_at;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_list(p_site_id uuid,p_type_id uuid)
        RETURNS TABLE(id uuid,type_id uuid,"key" text,label text,field_type text,
            required boolean,localized boolean,cardinality integer,"position" integer,
            validation jsonb,ui_options jsonb,definition_version integer,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE constraints record; parent content.content_type;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id);
            SELECT t.* INTO parent FROM content.content_type t
            WHERE t.id=p_type_id AND t.site_id=p_site_id AND t.status <> 'DELETED';
            IF NOT FOUND THEN RAISE EXCEPTION 'AGENT_TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0
               AND NOT parent.id=ANY(constraints.allowed_type_ids)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0003'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0
               AND NOT parent."key"=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            RETURN QUERY SELECT f.id,f.type_id,f."key",f.label,f.field_type,f.required,
                f.localized,f.cardinality,f."position",f.validation,f.ui_options,
                f.definition_version,f.created_at,f.updated_at
            FROM content.field_definition f
            WHERE f.site_id=p_site_id AND f.type_id=p_type_id
            ORDER BY f."position",f."key" COLLATE "C";
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_item_list(p_site_id uuid,p_type_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,type_id uuid,slug text,status text,
            type_definition_version integer,"values" jsonb,row_version integer,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE constraints record; parent content.content_type;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id);
            SELECT t.* INTO parent FROM content.content_type t
            WHERE t.id=p_type_id AND t.site_id=p_site_id AND t.status <> 'DELETED';
            IF NOT FOUND THEN RAISE EXCEPTION 'AGENT_TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0
               AND NOT parent.id=ANY(constraints.allowed_type_ids)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0003'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0
               AND NOT parent."key"=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            RETURN QUERY SELECT i.id,i.site_id,i.type_id,i.slug,i.status,
                i.type_definition_version,i."values",i.row_version,i.created_at,i.updated_at
            FROM content.content_item i
            WHERE i.site_id=p_site_id AND i.type_id=p_type_id AND i.status <> 'DELETED'
            ORDER BY i.slug COLLATE "C";
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_item_get(p_site_id uuid,p_item_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,type_id uuid,slug text,status text,
            type_definition_version integer,"values" jsonb,row_version integer,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE constraints record; item content.content_item; parent content.content_type;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id);
            SELECT i.* INTO item FROM content.content_item i
            WHERE i.id=p_item_id AND i.site_id=p_site_id AND i.status <> 'DELETED';
            IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT t.* INTO parent FROM content.content_type t
            WHERE t.id=item.type_id AND t.site_id=p_site_id AND t.status <> 'DELETED';
            IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0
               AND NOT parent.id=ANY(constraints.allowed_type_ids)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0003'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0
               AND NOT parent."key"=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            RETURN QUERY SELECT item.id,item.site_id,item.type_id,item.slug,item.status,
                item.type_definition_version,item."values",item.row_version,item.created_at,
                item.updated_at;
        END;
        $fn$
        """
    )

    # Mutation wrappers perform the full authority and quota check in the same
    # transaction as the semantic write. The wrapper never trusts a caller's
    # definition version for item creation.
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_create(
            p_site_id uuid,p_key text,p_labels jsonb,p_slug_pattern text,p_settings jsonb
        ) RETURNS TABLE(id uuid,site_id uuid,"key" text,labels jsonb,
            slug_pattern text,status text,definition_version integer,settings jsonb,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            visible_count bigint;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id);
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0
               AND NOT p_key=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text||'_content_type_create',994));
            IF constraints.max_content_types IS NOT NULL THEN
                SELECT count(*) INTO visible_count FROM content.content_type t
                WHERE t.site_id=p_site_id AND t.status='ACTIVE';
                IF visible_count >= constraints.max_content_types THEN
                    RAISE EXCEPTION 'AGENT_RESOURCE_CONTENT_TYPE_LIMIT' USING ERRCODE='P0006';
                END IF;
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            RETURN QUERY SELECT * FROM content.slaif_agent_unchecked_content_type_create(
                p_site_id,p_key,p_labels,p_slug_pattern,p_settings);
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_update(
            p_site_id uuid,p_type_id uuid,p_labels jsonb,p_slug_pattern text,
            p_settings jsonb,p_expected integer
        ) RETURNS SETOF content.content_type LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            locked content.content_type; updated content.content_type;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id);
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(
                workspace_id::text||':'||p_type_id::text||'_content_type_definition',994));
            SELECT t.* INTO locked FROM content.content_type t
            WHERE t.site_id=p_site_id AND t.id=p_type_id AND t.status='ACTIVE' FOR UPDATE;
            IF NOT FOUND OR locked.definition_version <> p_expected THEN
                RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003';
            END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0
               AND NOT locked.id=ANY(constraints.allowed_type_ids)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0003'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0
               AND NOT locked."key"=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.content_type t SET labels=coalesce(p_labels,t.labels),
                slug_pattern=coalesce(p_slug_pattern,t.slug_pattern),
                settings=coalesce(p_settings,t.settings),definition_version=t.definition_version+1,
                updated_at=now() WHERE t.id=locked.id AND t.site_id=p_site_id
                AND t.definition_version=locked.definition_version RETURNING t.* INTO updated;
            RETURN NEXT updated;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_delete(
            p_site_id uuid,p_type_id uuid,p_expected integer
        ) RETURNS SETOF content.content_type LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            locked content.content_type; deleted content.content_type;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id);
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(
                workspace_id::text||':'||p_type_id::text||'_content_type_definition',994));
            SELECT t.* INTO locked FROM content.content_type t
            WHERE t.site_id=p_site_id AND t.id=p_type_id AND t.status='ACTIVE' FOR UPDATE;
            IF NOT FOUND OR locked.definition_version <> p_expected THEN
                RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003';
            END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0
               AND NOT locked.id=ANY(constraints.allowed_type_ids)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0003'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0
               AND NOT locked."key"=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            IF constraints.delete_enabled IS FALSE THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_DELETE_DISABLED' USING ERRCODE='P0003';
            END IF;
            IF EXISTS (SELECT 1 FROM content.content_item i
                       WHERE i.site_id=p_site_id AND i.type_id=locked.id)
            THEN RAISE EXCEPTION 'TYPE_DEPENDENCIES' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN
                RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.content_type t SET status='DELETED',
                definition_version=t.definition_version+1,updated_at=now()
                WHERE t.id=locked.id AND t.site_id=p_site_id RETURNING t.* INTO deleted;
            RETURN NEXT deleted;
        END;
        $fn$
        """
    )

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_create(
            p_site_id uuid,p_type_id uuid,p_key text,p_label text,p_field_type text,
            p_required boolean,p_localized boolean,p_cardinality integer,p_position integer,
            p_validation jsonb,p_ui_options jsonb
        ) RETURNS TABLE(id uuid,type_id uuid,"key" text,label text,field_type text,
            required boolean,localized boolean,cardinality integer,"position" integer,
            validation jsonb,ui_options jsonb,definition_version integer,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            parent content.content_type; visible_count bigint;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id);
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            SELECT t.* INTO parent FROM content.content_type t
            WHERE t.id=p_type_id AND t.site_id=p_site_id AND t.status='ACTIVE' FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'FIELD_TYPE_SITE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0003'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text||':'||parent.id::text||'_field_definition_create',994));
            IF constraints.max_fields_per_type IS NOT NULL THEN
                SELECT count(*) INTO visible_count FROM content.field_definition f
                WHERE f.site_id=p_site_id AND f.type_id=parent.id;
                IF visible_count >= constraints.max_fields_per_type THEN
                    RAISE EXCEPTION 'AGENT_RESOURCE_FIELD_DEFINITION_LIMIT' USING ERRCODE='P0006';
                END IF;
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            INSERT INTO content.field_definition(site_id,type_id,"key",label,field_type,
                required,localized,cardinality,"position",validation,ui_options)
            VALUES(p_site_id,p_type_id,p_key,p_label,p_field_type,p_required,p_localized,
                p_cardinality,p_position,p_validation,p_ui_options);
            RETURN QUERY SELECT f.id,f.type_id,f."key",f.label,f.field_type,f.required,
                f.localized,f.cardinality,f."position",f.validation,f.ui_options,
                f.definition_version,f.created_at,f.updated_at
            FROM content.field_definition f WHERE f.site_id=p_site_id AND f.type_id=p_type_id
                AND f."key"=p_key ORDER BY f.created_at DESC LIMIT 1;
        END;
        $fn$
        """
    )

    # Field update/delete are kept explicit because their parent type is the
    # persisted allowlist identity and the row is a separate definition token.
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_update(
            p_site_id uuid,p_type_id uuid,p_field_id uuid,p_label text,
            p_required boolean,p_localized boolean,p_cardinality integer,p_position integer,
            p_validation jsonb,p_ui_options jsonb,p_expected integer
        ) RETURNS TABLE(id uuid,site_id uuid,type_id uuid,"key" text,label text,
            field_type text,required boolean,localized boolean,cardinality integer,
            "position" integer,validation jsonb,ui_options jsonb,
            definition_version integer,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            parent content.content_type; locked content.field_definition; updated content.field_definition;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id);
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(
                workspace_id::text||':'||p_type_id::text||':'||p_field_id::text||
                '_field_definition',994));
            SELECT t.* INTO parent FROM content.content_type t
            WHERE t.id=p_type_id AND t.site_id=p_site_id AND t.status='ACTIVE' FOR UPDATE;
            SELECT f.* INTO locked FROM content.field_definition f
            WHERE f.id=p_field_id AND f.site_id=p_site_id AND f.type_id=p_type_id
                AND parent.id IS NOT NULL AND f.definition_version=p_expected FOR UPDATE;
            IF parent.id IS NULL OR locked.id IS NULL THEN
                RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003';
            END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0003'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.field_definition f SET label=coalesce(p_label,f.label),
                required=coalesce(p_required,f.required),localized=coalesce(p_localized,f.localized),
                cardinality=coalesce(p_cardinality,f.cardinality),"position"=coalesce(p_position,f."position"),
                validation=coalesce(p_validation,f.validation),ui_options=coalesce(p_ui_options,f.ui_options),
                definition_version=f.definition_version+1,updated_at=now()
                WHERE f.id=locked.id AND f.definition_version=locked.definition_version
                RETURNING f.* INTO updated;
            RETURN QUERY SELECT updated.id,updated.site_id,updated.type_id,updated."key",
                updated.label,updated.field_type,updated.required,updated.localized,
                updated.cardinality,updated."position",updated.validation,updated.ui_options,
                updated.definition_version,updated.created_at,updated.updated_at;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_delete(
            p_site_id uuid,p_type_id uuid,p_field_id uuid,p_expected integer
        ) RETURNS TABLE(id uuid,site_id uuid,type_id uuid,"key" text,label text,
            field_type text,required boolean,localized boolean,cardinality integer,
            "position" integer,validation jsonb,ui_options jsonb,
            definition_version integer,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            parent content.content_type; locked content.field_definition; deleted content.field_definition;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id);
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(
                workspace_id::text||':'||p_type_id::text||':'||p_field_id::text||
                '_field_definition',994));
            SELECT t.* INTO parent FROM content.content_type t
            WHERE t.id=p_type_id AND t.site_id=p_site_id AND t.status='ACTIVE' FOR UPDATE;
            SELECT f.* INTO locked FROM content.field_definition f
            WHERE f.id=p_field_id AND f.site_id=p_site_id AND f.type_id=p_type_id
                AND parent.id IS NOT NULL AND f.definition_version=p_expected FOR UPDATE;
            IF parent.id IS NULL OR locked.id IS NULL THEN
                RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003';
            END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0003'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            IF constraints.delete_enabled IS FALSE THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_DELETE_DISABLED' USING ERRCODE='P0003';
            END IF;
            IF EXISTS (SELECT 1 FROM content.content_item i
                WHERE i.site_id=p_site_id AND i.type_id=p_type_id AND i."values" ? locked."key")
            THEN RAISE EXCEPTION 'FIELD_DEPENDENCIES' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN
                RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            DELETE FROM content.field_definition f WHERE f.id=locked.id
                AND f.site_id=p_site_id AND f.definition_version=locked.definition_version
                RETURNING f.* INTO deleted;
            RETURN QUERY SELECT deleted.id,deleted.site_id,deleted.type_id,deleted."key",
                deleted.label,deleted.field_type,deleted.required,deleted.localized,
                deleted.cardinality,deleted."position",deleted.validation,deleted.ui_options,
                deleted.definition_version,deleted.created_at,deleted.updated_at;
        END;
        $fn$
        """
    )

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_item_create(
            p_site_id uuid,p_type_id uuid,p_slug text,p_status text,p_values jsonb
        ) RETURNS SETOF content.content_item LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            parent content.content_type; created content.content_item;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id);
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            SELECT t.* INTO parent FROM content.content_type t
            WHERE t.id=p_type_id AND t.site_id=p_site_id AND t.status='ACTIVE' FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_TYPE_SITE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0003'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            INSERT INTO content.content_item(site_id,type_id,slug,status,"values",type_definition_version)
            VALUES(p_site_id,p_type_id,p_slug,p_status,p_values,parent.definition_version);
            RETURN QUERY SELECT i.* FROM content.content_item i
            WHERE i.site_id=p_site_id AND i.type_id=p_type_id AND i.slug=p_slug
            ORDER BY i.created_at DESC LIMIT 1;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_item_update(
            p_site_id uuid,p_item_id uuid,p_slug text,p_status text,p_values jsonb,
            p_expected_row_version integer
        ) RETURNS SETOF content.content_item LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            current_item content.content_item; parent content.content_type; updated content.content_item;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id);
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(
                workspace_id::text||':'||p_item_id::text||'_content_item',994));
            IF p_expected_row_version IS NULL OR p_expected_row_version <= 0 THEN
                RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003';
            END IF;
            SELECT i.* INTO current_item FROM content.content_item i
            WHERE i.id=p_item_id AND i.site_id=p_site_id AND i.status <> 'DELETED' FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT t.* INTO parent FROM content.content_type t
            WHERE t.id=current_item.type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
            IF NOT FOUND OR parent.definition_version <> current_item.type_definition_version THEN
                RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003';
            END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0003'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            IF current_item.row_version <> p_expected_row_version THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.content_item i SET slug=coalesce(p_slug,i.slug),
                status=coalesce(p_status,i.status),"values"=coalesce(p_values,i."values"),
                row_version=i.row_version+1,updated_at=now()
                WHERE i.id=current_item.id AND i.site_id=p_site_id
                    AND i.row_version=current_item.row_version;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            RETURN QUERY SELECT i.* FROM content.content_item i
            WHERE i.id=current_item.id AND i.site_id=p_site_id;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_item_delete(
            p_site_id uuid,p_item_id uuid,p_expected_row_version integer
        ) RETURNS SETOF content.content_item LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            current_item content.content_item; parent content.content_type; deleted content.content_item;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id);
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(
                workspace_id::text||':'||p_item_id::text||'_content_item',994));
            IF p_expected_row_version IS NULL OR p_expected_row_version <= 0 THEN
                RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003';
            END IF;
            SELECT i.* INTO current_item FROM content.content_item i
            WHERE i.id=p_item_id AND i.site_id=p_site_id AND i.status <> 'DELETED' FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT t.* INTO parent FROM content.content_type t
            WHERE t.id=current_item.type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
            IF NOT FOUND OR parent.definition_version <> current_item.type_definition_version THEN
                RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003';
            END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0003'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003'; END IF;
            IF constraints.delete_enabled IS FALSE THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_DELETE_DISABLED' USING ERRCODE='P0003';
            END IF;
            IF current_item.row_version <> p_expected_row_version THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            IF EXISTS (SELECT 1 FROM content.content_item_translation tr
                       WHERE tr.site_id=p_site_id AND tr.item_id=current_item.id)
               OR EXISTS (SELECT 1 FROM content.item_relation rel
                       WHERE rel.site_id=p_site_id AND (rel.source_item_id=current_item.id
                           OR rel.target_item_id=current_item.id))
            THEN RAISE EXCEPTION 'ITEM_DEPENDENCIES' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN
                RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.content_item i SET status='DELETED',row_version=i.row_version+1,
                updated_at=now() WHERE i.id=current_item.id AND i.site_id=p_site_id
                AND i.row_version=current_item.row_version;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            RETURN QUERY SELECT i.* FROM content.content_item i
            WHERE i.id=current_item.id AND i.site_id=p_site_id;
        END;
        $fn$
        """
    )

    for name, signature in (
        ("slaif_agent_content_type_list", "uuid"),
        ("slaif_agent_content_type_get", "uuid,uuid"),
        ("slaif_agent_field_definition_list", "uuid,uuid"),
        ("slaif_agent_content_item_list", "uuid,uuid"),
        ("slaif_agent_content_item_get", _ITEM_GET_SIGNATURE),
        ("slaif_agent_content_type_create", _TYPE_SIGNATURE),
        ("slaif_agent_content_type_update", _TYPE_UPDATE_SIGNATURE),
        ("slaif_agent_content_type_delete", _TYPE_DELETE_SIGNATURE),
        ("slaif_agent_field_definition_create", _FIELD_CREATE_SIGNATURE),
        ("slaif_agent_field_definition_update", _FIELD_UPDATE_SIGNATURE),
        ("slaif_agent_field_definition_delete", _FIELD_DELETE_SIGNATURE),
        ("slaif_agent_content_item_create", _ITEM_CREATE_SIGNATURE),
        ("slaif_agent_content_item_update", _ITEM_UPDATE_SIGNATURE),
        ("slaif_agent_content_item_delete", _ITEM_DELETE_SIGNATURE),
    ):
        qualified = f"content.{name}({signature})"
        op.execute(f"ALTER FUNCTION {qualified} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {qualified} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {qualified} TO slaif_agent_runtime")


def downgrade() -> None:
    # Remove 046-only item APIs and restore the 045 strict six-action contract.
    for name, signature in (
        ("slaif_agent_content_item_delete", _ITEM_DELETE_SIGNATURE),
        ("slaif_agent_content_item_update", _ITEM_UPDATE_SIGNATURE),
        ("slaif_agent_content_item_get", _ITEM_GET_SIGNATURE),
        ("slaif_agent_content_item_create", _ITEM_CREATE_SIGNATURE),
        ("slaif_agent_content_item_list", "uuid,uuid"),
        ("slaif_agent_field_definition_delete", _FIELD_DELETE_SIGNATURE),
        ("slaif_agent_field_definition_update", _FIELD_UPDATE_SIGNATURE),
        ("slaif_agent_field_definition_create", _FIELD_CREATE_SIGNATURE),
        ("slaif_agent_field_definition_list", "uuid,uuid"),
        ("slaif_agent_content_type_delete", _TYPE_DELETE_SIGNATURE),
        ("slaif_agent_content_type_update", _TYPE_UPDATE_SIGNATURE),
        ("slaif_agent_content_type_create", _TYPE_SIGNATURE),
        ("slaif_agent_content_type_get", "uuid,uuid"),
        ("slaif_agent_content_type_list", "uuid"),
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{name}({signature}) CASCADE")
    op.execute("DROP FUNCTION IF EXISTS control.slaif_agent_require_capability(uuid)")
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(
        """
        ALTER TABLE audit.agent_mutation ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
            (http_method IS NULL AND quota_kind IS NULL)
            OR (action='CONTENT_TYPE_CREATED' AND resource_type='content_type'
                AND http_method='POST' AND response_status=201 AND quota_kind='mutation')
            OR (action='CONTENT_TYPE_UPDATED' AND resource_type='content_type'
                AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
            OR (action='CONTENT_TYPE_DELETED' AND resource_type='content_type'
                AND http_method='DELETE' AND response_status=200 AND quota_kind='delete')
            OR (action='FIELD_DEFINITION_CREATED' AND resource_type='field_definition'
                AND http_method='POST' AND response_status=201 AND quota_kind='mutation')
            OR (action='FIELD_DEFINITION_UPDATED' AND resource_type='field_definition'
                AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
            OR (action='FIELD_DEFINITION_DELETED' AND resource_type='field_definition'
                AND http_method='DELETE' AND response_status=200 AND quota_kind='delete')
        )
        """
    )
    # The 045 function body rejects content_type/field_definition at the
    # legacy boundary, while content_item remains the pre-046 legacy action.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_idempotency_complete(
            p_capability_id uuid,p_workspace_id uuid,p_idempotency_key text,
            p_request_digest text,p_operation_id uuid,p_status_code integer,
            p_response_body jsonb,p_resource_type text,p_resource_id uuid,p_site_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE expected_site uuid;
        BEGIN
            SELECT w.site_id INTO expected_site FROM control.capability c
            JOIN control.workspace w ON w.id=c.workspace_id
            WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id AND w.site_id=p_site_id;
            IF expected_site IS NULL OR p_status_code NOT BETWEEN 200 AND 299
               OR p_response_body IS NULL OR p_resource_id IS NULL
               OR p_resource_type NOT IN ('content_type','field_definition','content_item','page','composition_node')
               OR p_resource_type IN ('content_type','field_definition')
            THEN RAISE EXCEPTION 'INVALID_IDEMPOTENCY_COMPLETION' USING ERRCODE='P0001'; END IF;
            UPDATE control.agent_idempotency SET status_code=p_status_code,response_body=p_response_body,
                resource_type=p_resource_type,resource_id=p_resource_id,completed_at=CURRENT_TIMESTAMP
            WHERE capability_id=p_capability_id AND workspace_id=p_workspace_id
              AND idempotency_key=p_idempotency_key AND request_digest=p_request_digest
              AND operation_id=p_operation_id AND status_code IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'IDEMPOTENCY_RESERVATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            INSERT INTO audit.agent_mutation(operation_id,capability_id,workspace_id,site_id,
                resource_type,resource_id,request_digest,response_status)
            VALUES(p_operation_id,p_capability_id,p_workspace_id,p_site_id,p_resource_type,
                p_resource_id,p_request_digest,p_status_code);
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_idempotency_complete(
            p_capability_id uuid,p_workspace_id uuid,p_idempotency_key text,
            p_request_digest text,p_operation_id uuid,p_status_code integer,
            p_response_body jsonb,p_resource_type text,p_resource_id uuid,p_site_id uuid,
            p_action text,p_http_method text,p_quota_kind text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            IF p_action NOT IN ('CONTENT_TYPE_CREATED','CONTENT_TYPE_UPDATED','CONTENT_TYPE_DELETED',
                'FIELD_DEFINITION_CREATED','FIELD_DEFINITION_UPDATED','FIELD_DEFINITION_DELETED')
            THEN RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION' USING ERRCODE='P0001'; END IF;
            IF p_resource_type NOT IN ('content_type','field_definition') THEN
                RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION' USING ERRCODE='P0001';
            END IF;
            UPDATE control.agent_idempotency SET status_code=p_status_code,response_body=p_response_body,
                resource_type=p_resource_type,resource_id=p_resource_id,completed_at=CURRENT_TIMESTAMP
            WHERE capability_id=p_capability_id AND workspace_id=p_workspace_id
              AND idempotency_key=p_idempotency_key AND request_digest=p_request_digest
              AND operation_id=p_operation_id AND status_code IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'IDEMPOTENCY_RESERVATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            INSERT INTO audit.agent_mutation(operation_id,capability_id,workspace_id,site_id,
                resource_type,resource_id,request_digest,response_status,action,http_method,quota_kind)
            VALUES(p_operation_id,p_capability_id,p_workspace_id,p_site_id,p_resource_type,
                p_resource_id,p_request_digest,p_status_code,p_action,p_http_method,p_quota_kind);
        END; $fn$
        """
    )
    # Restore the 045 read wrappers without allowlist coupling.
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_list(p_site_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,"key" text,labels jsonb,slug_pattern text,
            status text,definition_version integer,settings jsonb,created_at timestamptz,
            updated_at timestamptz) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT t.id,t.site_id,t."key",t.labels,t.slug_pattern,t.status,
                t.definition_version,t.settings,t.created_at,t.updated_at
            FROM content.content_type t WHERE t.site_id=p_site_id AND t.status <> 'DELETED'
            ORDER BY t."key" COLLATE "C";
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_get(p_site_id uuid,p_type_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,"key" text,labels jsonb,slug_pattern text,
            status text,definition_version integer,settings jsonb,created_at timestamptz,
            updated_at timestamptz) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT t.id,t.site_id,t."key",t.labels,t.slug_pattern,t.status,
                t.definition_version,t.settings,t.created_at,t.updated_at
            FROM content.content_type t WHERE t.site_id=p_site_id AND t.id=p_type_id
                AND t.status <> 'DELETED';
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_list(p_site_id uuid,p_type_id uuid)
        RETURNS TABLE(id uuid,type_id uuid,"key" text,label text,field_type text,
            required boolean,localized boolean,cardinality integer,"position" integer,
            validation jsonb,ui_options jsonb,definition_version integer,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT f.id,f.type_id,f."key",f.label,f.field_type,f.required,
                f.localized,f.cardinality,f."position",f.validation,f.ui_options,
                f.definition_version,f.created_at,f.updated_at
            FROM content.field_definition f WHERE f.site_id=p_site_id AND f.type_id=p_type_id
            ORDER BY f."position",f."key" COLLATE "C";
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_item_list(p_site_id uuid,p_type_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,type_id uuid,slug text,status text,
            type_definition_version integer,"values" jsonb,row_version integer,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT i.id,i.site_id,i.type_id,i.slug,i.status,
                i.type_definition_version,i."values",i.row_version,i.created_at,i.updated_at
            FROM content.content_item i WHERE i.site_id=p_site_id AND i.type_id=p_type_id
                AND i.status <> 'DELETED' ORDER BY i.slug COLLATE "C";
        END; $fn$
        """
    )

    # Restore the 045 mutation wrappers. They retain 045 resource checks but
    # do not call the 046 capability helper or charge their own quota.
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_create(
            p_site_id uuid,p_key text,p_labels jsonb,p_slug_pattern text,p_settings jsonb
        ) RETURNS TABLE(id uuid,site_id uuid,"key" text,labels jsonb,slug_pattern text,
            status text,definition_version integer,settings jsonb,created_at timestamptz,
            updated_at timestamptz) LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT * FROM content.slaif_agent_unchecked_content_type_create(
                p_site_id,p_key,p_labels,p_slug_pattern,p_settings);
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_update(
            p_site_id uuid,p_type_id uuid,p_labels jsonb,p_slug_pattern text,
            p_settings jsonb,p_expected integer
        ) RETURNS SETOF content.content_type LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE updated content.content_type;
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            IF NOT EXISTS (SELECT 1 FROM content.content_type t WHERE t.id=p_type_id
                AND t.site_id=p_site_id AND t.status='ACTIVE' AND t.definition_version=p_expected)
            THEN RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003'; END IF;
            UPDATE content.content_type SET labels=coalesce(p_labels,labels),
                slug_pattern=coalesce(p_slug_pattern,slug_pattern),settings=coalesce(p_settings,settings),
                definition_version=definition_version+1,updated_at=now()
                WHERE id=p_type_id AND site_id=p_site_id RETURNING * INTO updated;
            RETURN NEXT updated;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_delete(
            p_site_id uuid,p_type_id uuid,p_expected integer
        ) RETURNS SETOF content.content_type LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE deleted content.content_type;
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            IF NOT EXISTS (SELECT 1 FROM content.content_type t WHERE t.id=p_type_id
                AND t.site_id=p_site_id AND t.status='ACTIVE' AND t.definition_version=p_expected)
            THEN RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003'; END IF;
            IF EXISTS (SELECT 1 FROM content.content_item i WHERE i.site_id=p_site_id AND i.type_id=p_type_id)
            THEN RAISE EXCEPTION 'TYPE_DEPENDENCIES' USING ERRCODE='P0003'; END IF;
            UPDATE content.content_type SET status='DELETED',definition_version=definition_version+1,
                updated_at=now() WHERE id=p_type_id AND site_id=p_site_id RETURNING * INTO deleted;
            RETURN NEXT deleted;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_create(
            p_site_id uuid,p_type_id uuid,p_key text,p_label text,p_field_type text,
            p_required boolean,p_localized boolean,p_cardinality integer,p_position integer,
            p_validation jsonb,p_ui_options jsonb
        ) RETURNS TABLE(id uuid,type_id uuid,"key" text,label text,field_type text,
            required boolean,localized boolean,cardinality integer,"position" integer,
            validation jsonb,ui_options jsonb,definition_version integer,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            INSERT INTO content.field_definition(site_id,type_id,"key",label,field_type,
                required,localized,cardinality,"position",validation,ui_options)
            VALUES(p_site_id,p_type_id,p_key,p_label,p_field_type,p_required,p_localized,
                p_cardinality,p_position,p_validation,p_ui_options);
            RETURN QUERY SELECT f.id,f.type_id,f."key",f.label,f.field_type,f.required,
                f.localized,f.cardinality,f."position",f.validation,f.ui_options,
                f.definition_version,f.created_at,f.updated_at
            FROM content.field_definition f WHERE f.site_id=p_site_id AND f.type_id=p_type_id
                AND f."key"=p_key ORDER BY f.created_at DESC LIMIT 1;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_update(
            p_site_id uuid,p_type_id uuid,p_field_id uuid,p_label text,p_required boolean,
            p_localized boolean,p_cardinality integer,p_position integer,p_validation jsonb,
            p_ui_options jsonb,p_expected integer
        ) RETURNS TABLE(id uuid,site_id uuid,type_id uuid,"key" text,label text,
            field_type text,required boolean,localized boolean,cardinality integer,
            "position" integer,validation jsonb,ui_options jsonb,definition_version integer,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE updated content.field_definition;
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            IF NOT EXISTS (SELECT 1 FROM content.field_definition f WHERE f.id=p_field_id
                AND f.site_id=p_site_id AND f.type_id=p_type_id AND f.definition_version=p_expected)
            THEN RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003'; END IF;
            UPDATE content.field_definition f SET label=coalesce(p_label,f.label),
                required=coalesce(p_required,f.required),localized=coalesce(p_localized,f.localized),
                cardinality=coalesce(p_cardinality,f.cardinality),"position"=coalesce(p_position,f."position"),
                validation=coalesce(p_validation,f.validation),ui_options=coalesce(p_ui_options,f.ui_options),
                definition_version=f.definition_version+1,updated_at=now()
                WHERE f.id=p_field_id AND f.site_id=p_site_id RETURNING f.* INTO updated;
            RETURN QUERY SELECT updated.id,updated.site_id,updated.type_id,updated."key",updated.label,
                updated.field_type,updated.required,updated.localized,updated.cardinality,
                updated."position",updated.validation,updated.ui_options,updated.definition_version,
                updated.created_at,updated.updated_at;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_delete(
            p_site_id uuid,p_type_id uuid,p_field_id uuid,p_expected integer
        ) RETURNS TABLE(id uuid,site_id uuid,type_id uuid,"key" text,label text,
            field_type text,required boolean,localized boolean,cardinality integer,
            "position" integer,validation jsonb,ui_options jsonb,definition_version integer,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE deleted content.field_definition;
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            IF NOT EXISTS (SELECT 1 FROM content.field_definition f WHERE f.id=p_field_id
                AND f.site_id=p_site_id AND f.type_id=p_type_id AND f.definition_version=p_expected)
            THEN RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003'; END IF;
            DELETE FROM content.field_definition f WHERE f.id=p_field_id AND f.site_id=p_site_id
                RETURNING f.* INTO deleted;
            RETURN QUERY SELECT deleted.id,deleted.site_id,deleted.type_id,deleted."key",deleted.label,
                deleted.field_type,deleted.required,deleted.localized,deleted.cardinality,
                deleted."position",deleted.validation,deleted.ui_options,deleted.definition_version,
                deleted.created_at,deleted.updated_at;
        END; $fn$
        """
    )

    # Restore the old six-argument Agent item-create wrapper with no 046 quota
    # or capability helper dependency.
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_item_create(
            p_site_id uuid,p_type_id uuid,p_slug text,p_status text,p_values jsonb,
            p_type_definition_version integer
        ) RETURNS TABLE(id uuid,site_id uuid,type_id uuid,slug text,status text,
            type_definition_version integer,"values" jsonb,row_version integer,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT * FROM content.slaif_agent_unchecked_content_item_create(
                p_site_id,p_type_id,p_slug,p_status,p_values,p_type_definition_version);
        END; $fn$
        """
    )
    op.execute(
        "ALTER FUNCTION content.slaif_agent_content_item_create("
        "uuid,uuid,text,text,jsonb,integer) OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_agent_content_item_create("
        "uuid,uuid,text,text,jsonb,integer) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_agent_content_item_create("
        "uuid,uuid,text,text,jsonb,integer) TO slaif_agent_runtime"
    )
    for name, signature in (
        ("slaif_agent_content_type_list", "uuid"),
        ("slaif_agent_content_type_get", "uuid,uuid"),
        ("slaif_agent_field_definition_list", "uuid,uuid"),
        ("slaif_agent_content_item_list", "uuid,uuid"),
        ("slaif_agent_content_type_create", _TYPE_SIGNATURE),
        ("slaif_agent_content_type_update", _TYPE_UPDATE_SIGNATURE),
        ("slaif_agent_content_type_delete", _TYPE_DELETE_SIGNATURE),
        ("slaif_agent_field_definition_create", _FIELD_CREATE_SIGNATURE),
        ("slaif_agent_field_definition_update", _FIELD_UPDATE_SIGNATURE),
        ("slaif_agent_field_definition_delete", _FIELD_DELETE_SIGNATURE),
    ):
        qualified = f"content.{name}({signature})"
        op.execute(f"ALTER FUNCTION {qualified} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {qualified} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {qualified} TO slaif_agent_runtime")
