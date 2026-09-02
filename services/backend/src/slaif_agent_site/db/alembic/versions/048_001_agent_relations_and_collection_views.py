# ruff: noqa: E501
"""Add capability-bound Agent relation/view semantics and stale cleanup."""

from __future__ import annotations

from importlib import import_module

from alembic import op

revision = "048_001"
down_revision = "047_001"
branch_labels = None
depends_on = None


_ITEM_DELETE_SIGNATURE = "uuid,uuid,integer"
_TRANSLATION_LIST_SIGNATURE = "uuid,uuid"
_TRANSLATION_GET_SIGNATURE = "uuid,uuid,uuid"
_TRANSLATION_DELETE_SIGNATURE = "uuid,uuid,uuid,integer"
_RELATION_CREATE_SIGNATURE = "uuid,uuid,uuid,uuid,integer,jsonb"
_RELATION_LIST_SIGNATURE = "uuid,uuid"
_RELATION_GET_SIGNATURE = "uuid,uuid,uuid"
_RELATION_UPDATE_SIGNATURE = "uuid,uuid,uuid,uuid,integer,jsonb,integer"
_RELATION_DELETE_SIGNATURE = "uuid,uuid,uuid,integer"
_VIEW_CREATE_SIGNATURE = "uuid,uuid,text,jsonb,jsonb,jsonb,jsonb,integer"
_VIEW_LIST_SIGNATURE = "uuid,uuid"
_VIEW_GET_SIGNATURE = "uuid,uuid"
_VIEW_CURRENT_SIGNATURE = "uuid,uuid,text"
_VIEW_FIELDS_SIGNATURE = "uuid,uuid,text"
_VIEW_UPDATE_SIGNATURE = "uuid,uuid,jsonb,jsonb,jsonb,jsonb,integer,integer"
_VIEW_DELETE_SIGNATURE = "uuid,uuid,integer"


def _semantic_constraint_sql() -> str:
    return """
        ALTER TABLE audit.agent_mutation ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
            (http_method IS NULL AND quota_kind IS NULL)
            OR (action = 'CONTENT_TYPE_CREATED' AND resource_type = 'content_type' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'CONTENT_TYPE_UPDATED' AND resource_type = 'content_type' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'CONTENT_TYPE_DELETED' AND resource_type = 'content_type' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
            OR (action = 'FIELD_DEFINITION_CREATED' AND resource_type = 'field_definition' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'FIELD_DEFINITION_UPDATED' AND resource_type = 'field_definition' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'FIELD_DEFINITION_DELETED' AND resource_type = 'field_definition' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
            OR (action = 'CONTENT_ITEM_CREATED' AND resource_type = 'content_item' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'CONTENT_ITEM_UPDATED' AND resource_type = 'content_item' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'CONTENT_ITEM_DELETED' AND resource_type = 'content_item' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
            OR (action = 'CONTENT_ITEM_TRANSLATION_CREATED' AND resource_type = 'content_item_translation' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'CONTENT_ITEM_TRANSLATION_UPDATED' AND resource_type = 'content_item_translation' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'CONTENT_ITEM_TRANSLATION_DELETED' AND resource_type = 'content_item_translation' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
            OR (action = 'ITEM_RELATION_CREATED' AND resource_type = 'item_relation' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'ITEM_RELATION_UPDATED' AND resource_type = 'item_relation' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'ITEM_RELATION_DELETED' AND resource_type = 'item_relation' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
            OR (action = 'COLLECTION_VIEW_CREATED' AND resource_type = 'collection_view' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'COLLECTION_VIEW_UPDATED' AND resource_type = 'collection_view' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'COLLECTION_VIEW_DELETED' AND resource_type = 'collection_view' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
        )
    """


def _drop_agent_functions() -> None:
    for name, signature in (
        ("slaif_agent_item_relation_create", _RELATION_CREATE_SIGNATURE),
        ("slaif_agent_item_relation_list", _RELATION_LIST_SIGNATURE),
        ("slaif_agent_item_relation_get", _RELATION_GET_SIGNATURE),
        ("slaif_agent_item_relation_update", _RELATION_UPDATE_SIGNATURE),
        ("slaif_agent_item_relation_delete", _RELATION_DELETE_SIGNATURE),
        ("slaif_agent_collection_view_create", _VIEW_CREATE_SIGNATURE),
        ("slaif_agent_collection_view_list", _VIEW_LIST_SIGNATURE),
        ("slaif_agent_collection_view_get", _VIEW_GET_SIGNATURE),
        ("slaif_agent_collection_view_current", _VIEW_CURRENT_SIGNATURE),
        ("slaif_agent_collection_view_fields", _VIEW_FIELDS_SIGNATURE),
        ("slaif_agent_collection_view_update", _VIEW_UPDATE_SIGNATURE),
        ("slaif_agent_collection_view_delete", _VIEW_DELETE_SIGNATURE),
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{name}({signature}) CASCADE")
    for name, signature in (
        ("slaif_agent_relation_assert", "uuid,uuid,uuid,uuid,text,boolean"),
        ("slaif_agent_collection_view_query_validate", "uuid,jsonb,jsonb,jsonb,jsonb"),
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{name}({signature}) CASCADE")


def upgrade() -> None:
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(_semantic_constraint_sql())
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
               OR p_idempotency_key IS NULL OR length(p_idempotency_key) NOT BETWEEN 1 AND 128
               OR p_idempotency_key !~ '^[A-Za-z0-9._~-]+$'
               OR p_request_digest IS NULL OR p_request_digest !~ '^[0-9a-f]{64}$'
               OR p_operation_id IS NULL OR p_resource_id IS NULL
               OR p_action IS NULL OR p_http_method IS NULL OR p_quota_kind IS NULL
               OR NOT (
                   (p_action='CONTENT_TYPE_CREATED' AND p_resource_type='content_type' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_TYPE_UPDATED' AND p_resource_type='content_type' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_TYPE_DELETED' AND p_resource_type='content_type' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='FIELD_DEFINITION_CREATED' AND p_resource_type='field_definition' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='FIELD_DEFINITION_UPDATED' AND p_resource_type='field_definition' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='FIELD_DEFINITION_DELETED' AND p_resource_type='field_definition' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='CONTENT_ITEM_CREATED' AND p_resource_type='content_item' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_ITEM_UPDATED' AND p_resource_type='content_item' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_ITEM_DELETED' AND p_resource_type='content_item' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='CONTENT_ITEM_TRANSLATION_CREATED' AND p_resource_type='content_item_translation' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_ITEM_TRANSLATION_UPDATED' AND p_resource_type='content_item_translation' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_ITEM_TRANSLATION_DELETED' AND p_resource_type='content_item_translation' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='ITEM_RELATION_CREATED' AND p_resource_type='item_relation' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='ITEM_RELATION_UPDATED' AND p_resource_type='item_relation' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='ITEM_RELATION_DELETED' AND p_resource_type='item_relation' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='COLLECTION_VIEW_CREATED' AND p_resource_type='collection_view' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='COLLECTION_VIEW_UPDATED' AND p_resource_type='collection_view' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='COLLECTION_VIEW_DELETED' AND p_resource_type='collection_view' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
               )
               OR p_response_body IS NULL OR jsonb_typeof(p_response_body) <> 'object'
               OR jsonb_typeof(p_response_body->'record') <> 'object'
               OR p_response_body->>'action' IS DISTINCT FROM p_action
               OR p_response_body->>'operation_id' IS DISTINCT FROM p_operation_id::text
               OR p_response_body->'record'->>'id' IS DISTINCT FROM p_resource_id::text
            THEN RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION' USING ERRCODE='P0001'; END IF;
            SELECT workspace.site_id INTO expected_site
            FROM control.capability AS capability
            JOIN control.workspace AS workspace ON workspace.id=capability.workspace_id
            WHERE capability.id=p_capability_id AND capability.workspace_id=p_workspace_id
              AND workspace.site_id=p_site_id;
            IF expected_site IS NULL THEN RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION' USING ERRCODE='P0001'; END IF;
            UPDATE control.agent_idempotency
            SET status_code=p_status_code,response_body=p_response_body,
                resource_type=p_resource_type,resource_id=p_resource_id,completed_at=CURRENT_TIMESTAMP
            WHERE capability_id=p_capability_id AND workspace_id=p_workspace_id
              AND idempotency_key=p_idempotency_key AND request_digest=p_request_digest
              AND operation_id=p_operation_id AND status_code IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'IDEMPOTENCY_RESERVATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            INSERT INTO audit.agent_mutation(
                operation_id,capability_id,workspace_id,site_id,resource_type,resource_id,
                request_digest,response_status,action,http_method,quota_kind
            ) VALUES (
                p_operation_id,p_capability_id,p_workspace_id,p_site_id,p_resource_type,
                p_resource_id,p_request_digest,p_status_code,p_action,p_http_method,p_quota_kind
            );
        END; $fn$
        """
    )

    # Stale records are readable and deletable for cleanup, while create/update
    # paths retain the current-definition checks from 047.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_agent_content_item_delete(
            p_site_id uuid,p_item_id uuid,p_expected_row_version integer
        ) RETURNS SETOF content.content_item LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            current_item content.content_item; parent content.content_type; deleted content.content_item;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'content-item:delete');
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text||':'||p_item_id::text||'_content_item',994));
            IF p_expected_row_version IS NULL OR p_expected_row_version <= 0 THEN RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003'; END IF;
            SELECT i.* INTO current_item FROM content.content_item i
            WHERE i.id=p_item_id AND i.site_id=p_site_id AND i.status <> 'DELETED' FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT t.* INTO parent FROM content.content_type t
            WHERE t.id=current_item.type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
            IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_TYPE_SITE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
            IF constraints.delete_enabled IS FALSE THEN RAISE EXCEPTION 'AGENT_RESOURCE_DELETE_DISABLED' USING ERRCODE='P0007'; END IF;
            IF current_item.row_version <> p_expected_row_version THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            IF EXISTS (SELECT 1 FROM content.content_item_translation tr WHERE tr.site_id=p_site_id AND tr.item_id=current_item.id)
               OR EXISTS (SELECT 1 FROM content.item_relation rel WHERE rel.site_id=p_site_id AND (rel.source_item_id=current_item.id OR rel.target_item_id=current_item.id))
            THEN RAISE EXCEPTION 'ITEM_DEPENDENCIES' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            DELETE FROM content.content_item i WHERE i.id=current_item.id AND i.site_id=p_site_id AND i.row_version=current_item.row_version RETURNING i.* INTO deleted;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            RETURN NEXT deleted;
        END; $fn$
        """
    )

    for _name, body in (
        (
            "slaif_agent_content_item_translation_list",
            """
            CREATE OR REPLACE FUNCTION content.slaif_agent_content_item_translation_list(p_site_id uuid,p_item_id uuid)
            RETURNS SETOF content.content_item_translation LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            DECLARE item content.content_item; parent content.content_type; constraints record;
            BEGIN
                PERFORM control.slaif_agent_require_capability(p_site_id,'translation:read');
                SELECT i.* INTO item FROM content.content_item i WHERE i.id=p_item_id AND i.site_id=p_site_id AND i.status <> 'DELETED';
                IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
                SELECT t.* INTO parent FROM content.content_type t WHERE t.id=item.type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
                IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_TYPE_SITE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
                SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
                IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
                IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
                RETURN QUERY SELECT tr.* FROM content.content_item_translation tr WHERE tr.site_id=p_site_id AND tr.item_id=p_item_id ORDER BY tr.locale COLLATE "C";
            END; $fn$
            """,
        ),
        (
            "slaif_agent_content_item_translation_get",
            """
            CREATE OR REPLACE FUNCTION content.slaif_agent_content_item_translation_get(p_site_id uuid,p_item_id uuid,p_translation_id uuid)
            RETURNS SETOF content.content_item_translation LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            DECLARE item content.content_item; parent content.content_type; constraints record;
            BEGIN
                PERFORM control.slaif_agent_require_capability(p_site_id,'translation:read');
                SELECT i.* INTO item FROM content.content_item i WHERE i.id=p_item_id AND i.site_id=p_site_id AND i.status <> 'DELETED';
                IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
                SELECT t.* INTO parent FROM content.content_type t WHERE t.id=item.type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
                IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_TYPE_SITE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
                SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
                IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
                IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
                RETURN QUERY SELECT tr.* FROM content.content_item_translation tr WHERE tr.site_id=p_site_id AND tr.item_id=p_item_id AND tr.id=p_translation_id;
            END; $fn$
            """,
        ),
        (
            "slaif_agent_content_item_translation_delete",
            """
            CREATE OR REPLACE FUNCTION content.slaif_agent_content_item_translation_delete(p_site_id uuid,p_item_id uuid,p_translation_id uuid,p_expected_row_version integer)
            RETURNS SETOF content.content_item_translation LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            DECLARE workspace_id uuid; capability_id uuid; constraints record; item content.content_item; parent content.content_type; current_translation content.content_item_translation; deleted content.content_item_translation;
            BEGIN
                capability_id := control.slaif_agent_require_capability(p_site_id,'translation:write');
                workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
                PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text||':'||p_translation_id::text||'_content_item_translation',994));
                SELECT tr.* INTO current_translation FROM content.content_item_translation tr WHERE tr.id=p_translation_id AND tr.site_id=p_site_id AND tr.item_id=p_item_id FOR UPDATE;
                IF NOT FOUND THEN RAISE EXCEPTION 'TRANSLATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
                SELECT i.* INTO item FROM content.content_item i WHERE i.id=p_item_id AND i.site_id=p_site_id AND i.status <> 'DELETED' FOR UPDATE;
                IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
                SELECT t.* INTO parent FROM content.content_type t WHERE t.id=item.type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
                IF NOT FOUND THEN RAISE EXCEPTION 'ITEM_TYPE_SITE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
                SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
                IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
                IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
                IF constraints.delete_enabled IS FALSE THEN RAISE EXCEPTION 'AGENT_RESOURCE_DELETE_DISABLED' USING ERRCODE='P0007'; END IF;
                IF p_expected_row_version IS NULL OR p_expected_row_version <= 0 THEN RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003'; END IF;
                IF current_translation.row_version <> p_expected_row_version THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
                IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
                DELETE FROM content.content_item_translation tr WHERE tr.id=current_translation.id AND tr.site_id=p_site_id AND tr.item_id=p_item_id AND tr.row_version=current_translation.row_version RETURNING tr.* INTO deleted;
                IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
                RETURN NEXT deleted;
            END; $fn$
            """,
        ),
    ):
        op.execute(body)

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_relation_assert(
            p_site_id uuid,p_source uuid,p_field uuid,p_target uuid,
            p_scope text,p_require_current boolean
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE source content.content_item; target content.content_item;
            source_type content.content_type; target_type content.content_type;
            field content.field_definition; constraints record; allowed_type text;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,p_scope);
            SELECT i.* INTO source FROM content.content_item i WHERE i.id=p_source AND i.site_id=p_site_id AND i.status <> 'DELETED';
            IF NOT FOUND THEN RAISE EXCEPTION 'SOURCE_ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT i.* INTO target FROM content.content_item i WHERE i.id=p_target AND i.site_id=p_site_id AND i.status <> 'DELETED';
            IF NOT FOUND THEN RAISE EXCEPTION 'TARGET_ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT t.* INTO source_type FROM content.content_type t WHERE t.id=source.type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
            IF NOT FOUND THEN RAISE EXCEPTION 'SOURCE_TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT t.* INTO target_type FROM content.content_type t WHERE t.id=target.type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
            IF NOT FOUND THEN RAISE EXCEPTION 'TARGET_TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF p_require_current AND (source.type_definition_version <> source_type.definition_version OR target.type_definition_version <> target_type.definition_version) THEN
                RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003';
            END IF;
            SELECT f.* INTO field FROM content.field_definition f WHERE f.id=p_field AND f.site_id=p_site_id AND f.type_id=source.type_id;
            IF NOT FOUND OR field.field_type NOT IN ('reference','multi_reference') THEN RAISE EXCEPTION 'RELATION_FIELD_INVALID' USING ERRCODE='P0003'; END IF;
            allowed_type := field.validation->>'target_type_id';
            IF allowed_type IS NOT NULL AND target.type_id::text <> allowed_type THEN RAISE EXCEPTION 'RELATION_TARGET_TYPE_INVALID' USING ERRCODE='P0003'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT source_type.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT source_type."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT target_type.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT target_type."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_item_relation_create(
            p_site_id uuid,p_source uuid,p_field uuid,p_target uuid,p_position integer,p_metadata jsonb
        ) RETURNS SETOF content.item_relation LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; field content.field_definition; relation_count integer; created content.item_relation; created_id uuid;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'relationship:write');
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text||':'||p_source::text||':'||p_field::text||'_item_relation',994));
            IF p_position IS NULL OR p_position NOT BETWEEN 0 AND 999 OR p_metadata IS NULL OR jsonb_typeof(p_metadata)<>'object' OR octet_length(p_metadata::text)>16384 OR p_metadata::text ~* '(;|--|/\\*|\\*/|<script|javascript:|__proto__|constructor|prototype)' THEN RAISE EXCEPTION 'RELATION_INVALID' USING ERRCODE='P0003'; END IF;
            PERFORM content.slaif_agent_relation_assert(p_site_id,p_source,p_field,p_target,'relationship:write',true);
            SELECT f.* INTO field FROM content.field_definition f WHERE f.id=p_field AND f.site_id=p_site_id;
            SELECT count(*) INTO relation_count FROM content.item_relation r WHERE r.site_id=p_site_id AND r.source_item_id=p_source AND r.field_definition_id=p_field;
            IF (field.field_type='reference' AND relation_count >= 1) OR (field.field_type='multi_reference' AND relation_count >= field.cardinality) THEN RAISE EXCEPTION 'RELATION_CARDINALITY' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            created_id := gen_random_uuid();
            INSERT INTO content.item_relation(id,site_id,source_item_id,field_definition_id,target_item_id,position,metadata) VALUES(created_id,p_site_id,p_source,p_field,p_target,p_position,p_metadata);
            SELECT r.* INTO created FROM content.item_relation r WHERE r.id=created_id AND r.site_id=p_site_id;
            RETURN NEXT created;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_item_relation_list(p_site_id uuid,p_source uuid)
        RETURNS SETOF content.item_relation LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE source content.content_item; source_type content.content_type; constraints record;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'content-item:read');
            SELECT i.* INTO source FROM content.content_item i WHERE i.id=p_source AND i.site_id=p_site_id AND i.status <> 'DELETED';
            IF NOT FOUND THEN RAISE EXCEPTION 'SOURCE_ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT t.* INTO source_type FROM content.content_type t WHERE t.id=source.type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
            IF NOT FOUND THEN RAISE EXCEPTION 'SOURCE_TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT source_type.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT source_type."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
            RETURN QUERY SELECT r.* FROM content.item_relation r JOIN content.content_item target ON target.id=r.target_item_id AND target.site_id=p_site_id AND target.status <> 'DELETED' JOIN content.content_type target_type ON target_type.id=target.type_id AND target_type.site_id=p_site_id AND target_type.status='ACTIVE' JOIN content.field_definition f ON f.id=r.field_definition_id AND f.site_id=p_site_id AND f.type_id=source.type_id WHERE r.site_id=p_site_id AND r.source_item_id=p_source AND (coalesce(cardinality(constraints.allowed_type_ids),0)=0 OR target_type.id=ANY(constraints.allowed_type_ids)) AND (coalesce(cardinality(constraints.allowed_type_keys),0)=0 OR target_type."key"=ANY(constraints.allowed_type_keys)) ORDER BY r.field_definition_id,r.position,r.id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_item_relation_get(p_site_id uuid,p_source uuid,p_relation uuid)
        RETURNS SETOF content.item_relation LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE relation content.item_relation;
        BEGIN
            SELECT r.* INTO relation FROM content.item_relation r WHERE r.site_id=p_site_id AND r.source_item_id=p_source AND r.id=p_relation;
            IF NOT FOUND THEN RAISE EXCEPTION 'RELATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            PERFORM content.slaif_agent_relation_assert(p_site_id,relation.source_item_id,relation.field_definition_id,relation.target_item_id,'content-item:read',false);
            RETURN NEXT relation;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_item_relation_update(
            p_site_id uuid,p_source uuid,p_relation uuid,p_target uuid,p_position integer,p_metadata jsonb,p_expected integer
        ) RETURNS SETOF content.item_relation LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old content.item_relation; field content.field_definition; relation_count integer; updated content.item_relation;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'relationship:write');
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            SELECT r.* INTO old FROM content.item_relation r WHERE r.site_id=p_site_id AND r.source_item_id=p_source AND r.id=p_relation FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'RELATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text||':'||old.source_item_id::text||':'||old.field_definition_id::text||'_item_relation',994));
            IF p_expected IS NULL OR p_expected <= 0 THEN RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003'; END IF;
            IF old.row_version <> p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            IF (p_position IS NOT NULL AND p_position NOT BETWEEN 0 AND 999) OR (p_metadata IS NOT NULL AND (jsonb_typeof(p_metadata)<>'object' OR octet_length(p_metadata::text)>16384 OR p_metadata::text ~* '(;|--|/\\*|\\*/|<script|javascript:|__proto__|constructor|prototype)')) THEN RAISE EXCEPTION 'RELATION_INVALID' USING ERRCODE='P0003'; END IF;
            PERFORM content.slaif_agent_relation_assert(p_site_id,p_source,old.field_definition_id,coalesce(p_target,old.target_item_id),'relationship:write',true);
            SELECT f.* INTO field FROM content.field_definition f WHERE f.id=old.field_definition_id AND f.site_id=p_site_id;
            SELECT count(*) INTO relation_count FROM content.item_relation r WHERE r.site_id=p_site_id AND r.source_item_id=p_source AND r.field_definition_id=old.field_definition_id AND r.id<>p_relation;
            IF (field.field_type='reference' AND relation_count >= 1) OR (field.field_type='multi_reference' AND relation_count >= field.cardinality) THEN RAISE EXCEPTION 'RELATION_CARDINALITY' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            UPDATE content.item_relation r SET target_item_id=coalesce(p_target,r.target_item_id),position=coalesce(p_position,r.position),metadata=coalesce(p_metadata,r.metadata),row_version=r.row_version+1,updated_at=now() WHERE r.id=p_relation AND r.site_id=p_site_id AND r.source_item_id=p_source AND r.row_version=old.row_version;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            SELECT r.* INTO updated FROM content.item_relation r WHERE r.id=p_relation AND r.site_id=p_site_id;
            RETURN NEXT updated;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_item_relation_delete(p_site_id uuid,p_source uuid,p_relation uuid,p_expected integer)
        RETURNS SETOF content.item_relation LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old content.item_relation; deleted content.item_relation;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'relationship:write');
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            SELECT r.* INTO old FROM content.item_relation r WHERE r.site_id=p_site_id AND r.source_item_id=p_source AND r.id=p_relation FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'RELATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text||':'||old.source_item_id::text||':'||old.field_definition_id::text||'_item_relation',994));
            IF p_expected IS NULL OR p_expected <= 0 THEN RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003'; END IF;
            IF old.row_version <> p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_agent_relation_assert(p_site_id,old.source_item_id,old.field_definition_id,old.target_item_id,'relationship:write',false);
            DECLARE constraints record;
            BEGIN
                SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
                IF constraints.delete_enabled IS FALSE THEN RAISE EXCEPTION 'AGENT_RESOURCE_DELETE_DISABLED' USING ERRCODE='P0007'; END IF;
            END;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            deleted := old;
            DELETE FROM content.item_relation r WHERE r.id=p_relation AND r.site_id=p_site_id AND r.source_item_id=p_source AND r.row_version=old.row_version;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            RETURN NEXT deleted;
        END; $fn$
        """
    )

    # Shared bounded query validation is deliberately data-only: it never
    # constructs or executes SQL from a stored query fragment.
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_collection_view_query_validate(
            p_type_id uuid,p_filter jsonb,p_sort jsonb,p_projection jsonb,p_pagination jsonb
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE serialized text; node record; field record; name text; op_name text; value_kind text; projection jsonb;
        BEGIN
            IF jsonb_typeof(p_filter)<>'object' OR jsonb_typeof(p_sort)<>'object' OR jsonb_typeof(p_projection)<>'object' OR jsonb_typeof(p_pagination)<>'object' THEN RAISE EXCEPTION 'QUERY_INVALID' USING ERRCODE='P0003'; END IF;
            serialized := jsonb_build_array(p_filter,p_sort,p_projection,p_pagination)::text;
            IF octet_length(serialized)>16384 OR serialized ~* '(;|--|/\\*|\\*/|<script|javascript:|__proto__|constructor|prototype)' THEN RAISE EXCEPTION 'QUERY_INVALID' USING ERRCODE='P0003'; END IF;
            IF EXISTS (WITH RECURSIVE nodes(value,depth) AS (SELECT jsonb_build_array(p_filter,p_sort,p_projection,p_pagination),0 UNION ALL SELECT child.value,n.depth+1 FROM nodes n CROSS JOIN LATERAL (SELECT a.value FROM jsonb_array_elements(CASE WHEN jsonb_typeof(n.value)='array' THEN n.value ELSE '[]'::jsonb END) a UNION ALL SELECT e.value FROM jsonb_each(CASE WHEN jsonb_typeof(n.value)='object' THEN n.value ELSE '{}'::jsonb END) e) child) SELECT 1 FROM nodes WHERE depth>4) THEN RAISE EXCEPTION 'QUERY_DEPTH' USING ERRCODE='P0003'; END IF;
            IF (WITH RECURSIVE nodes(value) AS (SELECT jsonb_build_array(p_filter,p_sort,p_projection,p_pagination) UNION ALL SELECT child.value FROM nodes n CROSS JOIN LATERAL (SELECT a.value FROM jsonb_array_elements(CASE WHEN jsonb_typeof(n.value)='array' THEN n.value ELSE '[]'::jsonb END) a UNION ALL SELECT e.value FROM jsonb_each(CASE WHEN jsonb_typeof(n.value)='object' THEN n.value ELSE '{}'::jsonb END) e) child) SELECT count(*) FROM nodes)>256 THEN RAISE EXCEPTION 'QUERY_NODES' USING ERRCODE='P0003'; END IF;
            FOR node IN WITH RECURSIVE nodes(value) AS (SELECT p_filter UNION ALL SELECT child.value FROM nodes n CROSS JOIN LATERAL (SELECT a.value FROM jsonb_array_elements(CASE WHEN jsonb_typeof(n.value)='array' THEN n.value ELSE '[]'::jsonb END) a UNION ALL SELECT e.value FROM jsonb_each(CASE WHEN jsonb_typeof(n.value)='object' THEN n.value ELSE '{}'::jsonb END) e) child) SELECT value FROM nodes WHERE jsonb_typeof(value)='object' LOOP
                IF EXISTS (SELECT 1 FROM jsonb_object_keys(node.value) k WHERE k NOT IN ('status','slug','and','or','not','field','op','value')) THEN RAISE EXCEPTION 'QUERY_FILTER_SHAPE' USING ERRCODE='P0003'; END IF;
                IF node.value ? 'status' AND (jsonb_typeof(node.value->'status')<>'string' OR node.value->>'status' NOT IN ('DRAFT','PUBLISHED','ARCHIVED')) THEN RAISE EXCEPTION 'QUERY_FILTER_STATUS' USING ERRCODE='P0003'; END IF;
                IF node.value ? 'slug' AND jsonb_typeof(node.value->'slug')<>'string' THEN RAISE EXCEPTION 'QUERY_FILTER_SLUG' USING ERRCODE='P0003'; END IF;
                IF node.value ? 'and' AND (jsonb_typeof(node.value->'and')<>'array' OR jsonb_array_length(node.value->'and')>32) THEN RAISE EXCEPTION 'QUERY_FILTER_LOGIC' USING ERRCODE='P0003'; END IF;
                IF node.value ? 'or' AND (jsonb_typeof(node.value->'or')<>'array' OR jsonb_array_length(node.value->'or')>32) THEN RAISE EXCEPTION 'QUERY_FILTER_LOGIC' USING ERRCODE='P0003'; END IF;
                IF node.value ? 'not' AND jsonb_typeof(node.value->'not')<>'object' THEN RAISE EXCEPTION 'QUERY_FILTER_LOGIC' USING ERRCODE='P0003'; END IF;
                IF node.value ? 'field' OR node.value ? 'op' OR node.value ? 'value' THEN
                    IF NOT (node.value ? 'field' AND node.value ? 'op' AND node.value ? 'value') THEN RAISE EXCEPTION 'QUERY_FILTER_CLAUSE' USING ERRCODE='P0003'; END IF;
                    name := node.value->>'field'; op_name := node.value->>'op';
                    SELECT f.* INTO field FROM content.field_definition f WHERE f.type_id=p_type_id AND f."key"=name;
                    IF NOT FOUND OR field.localized THEN RAISE EXCEPTION 'QUERY_FILTER_FIELD' USING ERRCODE='P0003'; END IF;
                    IF (field.field_type IN ('short_text','url','email') AND op_name NOT IN ('eq','contains','prefix')) OR (field.field_type IN ('long_text','rich_text') AND op_name NOT IN ('eq','contains')) OR (field.field_type IN ('integer','decimal','date','datetime') AND op_name NOT IN ('eq','lt','lte','gt','gte')) OR (field.field_type='boolean' AND op_name<>'eq') OR (field.field_type='enum' AND op_name NOT IN ('eq','in')) OR field.field_type IN ('reference','multi_reference','media','document','location','object') THEN RAISE EXCEPTION 'QUERY_FILTER_OPERATOR' USING ERRCODE='P0003'; END IF;
                    value_kind := jsonb_typeof(node.value->'value');
                    IF op_name='in' THEN
                        IF field.field_type <> 'enum' OR value_kind <> 'array' THEN RAISE EXCEPTION 'QUERY_FILTER_VALUE' USING ERRCODE='P0003'; END IF;
                        IF jsonb_array_length(node.value->'value')<1 OR jsonb_array_length(node.value->'value')>32 THEN RAISE EXCEPTION 'QUERY_FILTER_VALUE' USING ERRCODE='P0003'; END IF;
                        IF EXISTS (SELECT 1 FROM jsonb_array_elements(node.value->'value') item WHERE jsonb_typeof(item.value)<>'string' OR btrim(item.value #>> '{}')='') THEN RAISE EXCEPTION 'QUERY_FILTER_VALUE' USING ERRCODE='P0003'; END IF;
                        IF coalesce(field.validation->'choices',field.validation->'values',field.validation->'enum') IS NOT NULL AND EXISTS (SELECT 1 FROM jsonb_array_elements(node.value->'value') item WHERE NOT EXISTS (SELECT 1 FROM jsonb_array_elements(coalesce(field.validation->'choices',field.validation->'values',field.validation->'enum')) choice WHERE choice #>> '{}'=item.value #>> '{}')) THEN RAISE EXCEPTION 'QUERY_FILTER_VALUE' USING ERRCODE='P0003'; END IF;
                    ELSE
                        IF value_kind IN ('object','array','null') THEN RAISE EXCEPTION 'QUERY_FILTER_VALUE' USING ERRCODE='P0003'; END IF;
                        IF field.field_type IN ('short_text','long_text','rich_text','url','email','enum') AND (value_kind<>'string' OR btrim(node.value->>'value')='') THEN RAISE EXCEPTION 'QUERY_FILTER_VALUE' USING ERRCODE='P0003'; END IF;
                        IF field.field_type='integer' AND (value_kind<>'number' OR node.value->>'value' !~ '^-?(0|[1-9][0-9]*)$') THEN RAISE EXCEPTION 'QUERY_FILTER_VALUE' USING ERRCODE='P0003'; END IF;
                        IF field.field_type='decimal' AND value_kind<>'number' THEN RAISE EXCEPTION 'QUERY_FILTER_VALUE' USING ERRCODE='P0003'; END IF;
                        IF field.field_type='boolean' AND value_kind<>'boolean' THEN RAISE EXCEPTION 'QUERY_FILTER_VALUE' USING ERRCODE='P0003'; END IF;
                        IF field.field_type='date' AND (value_kind<>'string' OR node.value->>'value' !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$') THEN RAISE EXCEPTION 'QUERY_FILTER_VALUE' USING ERRCODE='P0003'; END IF;
                        IF field.field_type='datetime' AND (value_kind<>'string' OR node.value->>'value' !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T') THEN RAISE EXCEPTION 'QUERY_FILTER_VALUE' USING ERRCODE='P0003'; END IF;
                        IF field.field_type='enum' AND coalesce(field.validation->'choices',field.validation->'values',field.validation->'enum') IS NOT NULL AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements(coalesce(field.validation->'choices',field.validation->'values',field.validation->'enum')) choice WHERE choice #>> '{}' = node.value->>'value') THEN RAISE EXCEPTION 'QUERY_FILTER_VALUE' USING ERRCODE='P0003'; END IF;
                    END IF;
                END IF;
            END LOOP;
            IF EXISTS (SELECT 1 FROM jsonb_object_keys(p_sort) k WHERE k NOT IN ('field','direction')) OR jsonb_typeof(coalesce(p_sort->'field','"slug"'::jsonb))<>'string' OR jsonb_typeof(coalesce(p_sort->'direction','"asc"'::jsonb))<>'string' OR coalesce(p_sort->>'direction','asc') NOT IN ('asc','desc') THEN RAISE EXCEPTION 'QUERY_SORT' USING ERRCODE='P0003'; END IF;
            name := coalesce(p_sort->>'field','slug');
            IF name NOT IN ('slug','id') THEN SELECT f.* INTO field FROM content.field_definition f WHERE f.type_id=p_type_id AND f."key"=name AND NOT f.localized AND f.cardinality=1 AND f.field_type NOT IN ('reference','multi_reference','media','document','location','object'); IF NOT FOUND THEN RAISE EXCEPTION 'QUERY_SORT_FIELD' USING ERRCODE='P0003'; END IF; END IF;
            projection := coalesce(p_projection->'fields','[]'::jsonb);
            IF EXISTS (SELECT 1 FROM jsonb_object_keys(p_projection) k WHERE k<>'fields') OR jsonb_typeof(projection)<>'array' OR jsonb_array_length(projection)>16 THEN RAISE EXCEPTION 'QUERY_PROJECTION' USING ERRCODE='P0003'; END IF;
            IF EXISTS (SELECT value FROM jsonb_array_elements(projection) WHERE jsonb_typeof(value)<>'string') OR EXISTS (SELECT value FROM jsonb_array_elements(projection) GROUP BY value HAVING count(*)>1) THEN RAISE EXCEPTION 'QUERY_PROJECTION' USING ERRCODE='P0003'; END IF;
            FOR name IN SELECT value #>> '{}' FROM jsonb_array_elements(projection) LOOP SELECT f.* INTO field FROM content.field_definition f WHERE f.type_id=p_type_id AND f."key"=name AND NOT f.localized; IF name IN ('id','site_id','type_id','slug','status','values') OR NOT FOUND THEN RAISE EXCEPTION 'QUERY_PROJECTION_FIELD' USING ERRCODE='P0003'; END IF; END LOOP;
            IF EXISTS (SELECT 1 FROM jsonb_object_keys(p_pagination) k WHERE k NOT IN ('limit','offset')) OR jsonb_typeof(coalesce(p_pagination->'limit','24'::jsonb))<>'number' OR jsonb_typeof(coalesce(p_pagination->'offset','0'::jsonb))<>'number' THEN RAISE EXCEPTION 'QUERY_PAGINATION' USING ERRCODE='P0003'; END IF;
            IF (p_pagination ? 'limit' AND p_pagination->>'limit' !~ '^-?[0-9]+$') OR (p_pagination ? 'offset' AND p_pagination->>'offset' !~ '^-?[0-9]+$') THEN RAISE EXCEPTION 'QUERY_PAGINATION' USING ERRCODE='P0003'; END IF;
            IF coalesce((p_pagination->>'limit')::numeric,24) NOT BETWEEN 1 AND 100 OR coalesce((p_pagination->>'offset')::numeric,0) NOT BETWEEN 0 AND 10000 THEN RAISE EXCEPTION 'QUERY_PAGINATION' USING ERRCODE='P0003'; END IF;
        END; $fn$
        """
    )
    op.execute(
        "DROP FUNCTION IF EXISTS content.slaif_agent_collection_view_fields(uuid,uuid,text)"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_collection_view_fields(p_site_id uuid,p_type_id uuid,p_scope text)
        RETURNS TABLE(id uuid,type_id uuid,"key" text,label text,field_type text,required boolean,localized boolean,cardinality integer,"position" integer,validation jsonb,ui_options jsonb,definition_version integer,created_at timestamptz,updated_at timestamptz) LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE parent content.content_type; constraints record;
        BEGIN
            IF p_scope NOT IN ('collection-view:create','collection-view:write') THEN RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007'; END IF;
            PERFORM control.slaif_agent_require_capability(p_site_id,p_scope);
            SELECT t.* INTO parent FROM content.content_type t WHERE t.id=p_type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
            IF NOT FOUND THEN RAISE EXCEPTION 'TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
            RETURN QUERY SELECT f.id,f.type_id,f."key",f.label,f.field_type,f.required,f.localized,f.cardinality,f."position",f.validation,f.ui_options,f.definition_version,f.created_at,f.updated_at FROM content.field_definition f WHERE f.site_id=p_site_id AND f.type_id=p_type_id ORDER BY f."position",f."key" COLLATE "C";
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_collection_view_current(p_site_id uuid,p_view_id uuid,p_scope text)
        RETURNS SETOF content.collection_view LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE view content.collection_view; parent content.content_type; constraints record;
        BEGIN
            IF p_scope<>'collection-view:write' THEN RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007'; END IF;
            PERFORM control.slaif_agent_require_capability(p_site_id,p_scope);
            SELECT v.* INTO view FROM content.collection_view v WHERE v.site_id=p_site_id AND v.id=p_view_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'VIEW_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT t.* INTO parent FROM content.content_type t WHERE t.id=view.type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
            IF NOT FOUND THEN RAISE EXCEPTION 'TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
            RETURN NEXT view;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_collection_view_list(p_site_id uuid,p_type_id uuid)
        RETURNS SETOF content.collection_view LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE parent content.content_type; constraints record;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'collection-view:read');
            SELECT t.* INTO parent FROM content.content_type t WHERE t.id=p_type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
            IF NOT FOUND THEN RAISE EXCEPTION 'TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
            RETURN QUERY SELECT v.* FROM content.collection_view v WHERE v.site_id=p_site_id AND v.type_id=p_type_id ORDER BY v.key COLLATE "C",v.id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_collection_view_get(p_site_id uuid,p_view_id uuid)
        RETURNS SETOF content.collection_view LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE view content.collection_view; parent content.content_type; constraints record;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'collection-view:read');
            SELECT v.* INTO view FROM content.collection_view v WHERE v.site_id=p_site_id AND v.id=p_view_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'VIEW_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT t.* INTO parent FROM content.content_type t WHERE t.id=view.type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
            IF NOT FOUND THEN RAISE EXCEPTION 'TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
            RETURN NEXT view;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_collection_view_create(
            p_site_id uuid,p_type_id uuid,p_key text,p_filter jsonb,p_sort jsonb,p_projection jsonb,p_pagination jsonb,p_expected_definition integer
        ) RETURNS SETOF content.collection_view LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; parent content.content_type; constraints record; created content.collection_view; created_id uuid;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'collection-view:create');
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text||':'||p_type_id::text||':'||coalesce(p_key,'')||'_collection_view',994));
            SELECT t.* INTO parent FROM content.content_type t WHERE t.id=p_type_id AND t.site_id=p_site_id AND t.status='ACTIVE' FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF p_expected_definition IS NOT NULL AND p_expected_definition<>parent.definition_version THEN RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
            IF p_key IS NULL OR btrim(p_key)='' OR length(p_key)>63 OR p_filter IS NULL OR p_sort IS NULL OR p_projection IS NULL OR p_pagination IS NULL THEN RAISE EXCEPTION 'VIEW_INVALID' USING ERRCODE='P0003'; END IF;
            IF EXISTS (SELECT 1 FROM content.collection_view v WHERE v.site_id=p_site_id AND v.type_id=p_type_id AND v.key=p_key) THEN RAISE EXCEPTION 'VIEW_DUPLICATE' USING ERRCODE='23505'; END IF;
            PERFORM content.slaif_agent_collection_view_query_validate(p_type_id,p_filter,p_sort,p_projection,p_pagination);
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            created_id := gen_random_uuid();
            INSERT INTO content.collection_view(id,site_id,type_id,key,filter_spec,sort_spec,projection_spec,pagination_spec,definition_version) VALUES(created_id,p_site_id,p_type_id,p_key,p_filter,p_sort,p_projection,p_pagination,parent.definition_version);
            SELECT v.* INTO created FROM content.collection_view v WHERE v.id=created_id AND v.site_id=p_site_id;
            RETURN NEXT created;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_collection_view_update(
            p_site_id uuid,p_view_id uuid,p_filter jsonb,p_sort jsonb,p_projection jsonb,p_pagination jsonb,p_expected_row_version integer,p_expected_definition integer
        ) RETURNS SETOF content.collection_view LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old content.collection_view; parent content.content_type; updated content.collection_view;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'collection-view:write');
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            SELECT v.* INTO old FROM content.collection_view v WHERE v.site_id=p_site_id AND v.id=p_view_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'VIEW_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text||':'||old.type_id::text||':'||p_view_id::text||'_collection_view',994));
            SELECT v.* INTO old FROM content.collection_view v WHERE v.site_id=p_site_id AND v.id=p_view_id FOR UPDATE;
            SELECT t.* INTO parent FROM content.content_type t WHERE t.id=old.type_id AND t.site_id=p_site_id AND t.status='ACTIVE' FOR UPDATE;
            IF NOT FOUND OR old.definition_version<>parent.definition_version THEN RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003'; END IF;
            IF p_expected_definition IS NOT NULL AND p_expected_definition<>old.definition_version THEN RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE='P0003'; END IF;
            IF p_expected_row_version IS NULL OR p_expected_row_version<=0 THEN RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003'; END IF;
            IF old.row_version<>p_expected_row_version THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_agent_collection_view_query_validate(old.type_id,coalesce(p_filter,old.filter_spec),coalesce(p_sort,old.sort_spec),coalesce(p_projection,old.projection_spec),coalesce(p_pagination,old.pagination_spec));
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            UPDATE content.collection_view v SET filter_spec=coalesce(p_filter,v.filter_spec),sort_spec=coalesce(p_sort,v.sort_spec),projection_spec=coalesce(p_projection,v.projection_spec),pagination_spec=coalesce(p_pagination,v.pagination_spec),row_version=v.row_version+1,updated_at=now() WHERE v.site_id=p_site_id AND v.id=p_view_id AND v.row_version=old.row_version;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            SELECT v.* INTO updated FROM content.collection_view v WHERE v.site_id=p_site_id AND v.id=p_view_id;
            RETURN NEXT updated;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_collection_view_delete(p_site_id uuid,p_view_id uuid,p_expected integer)
        RETURNS SETOF content.collection_view LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old content.collection_view; parent content.content_type; constraints record; deleted content.collection_view;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'collection-view:delete');
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            SELECT v.* INTO old FROM content.collection_view v WHERE v.site_id=p_site_id AND v.id=p_view_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'VIEW_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text||':'||old.type_id::text||':'||p_view_id::text||'_collection_view',994));
            SELECT t.* INTO parent FROM content.content_type t WHERE t.id=old.type_id AND t.site_id=p_site_id AND t.status='ACTIVE';
            IF NOT FOUND THEN RAISE EXCEPTION 'TYPE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF coalesce(cardinality(constraints.allowed_type_ids),0)>0 AND NOT parent.id=ANY(constraints.allowed_type_ids) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE='P0007'; END IF;
            IF coalesce(cardinality(constraints.allowed_type_keys),0)>0 AND NOT parent."key"=ANY(constraints.allowed_type_keys) THEN RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0007'; END IF;
            IF constraints.delete_enabled IS FALSE THEN RAISE EXCEPTION 'AGENT_RESOURCE_DELETE_DISABLED' USING ERRCODE='P0007'; END IF;
            IF p_expected IS NULL OR p_expected<=0 THEN RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            deleted := old;
            DELETE FROM content.collection_view v WHERE v.site_id=p_site_id AND v.id=p_view_id AND v.row_version=old.row_version;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            RETURN NEXT deleted;
        END; $fn$
        """
    )

    for name, signature in (
        ("slaif_agent_item_relation_create", _RELATION_CREATE_SIGNATURE),
        ("slaif_agent_item_relation_list", _RELATION_LIST_SIGNATURE),
        ("slaif_agent_item_relation_get", _RELATION_GET_SIGNATURE),
        ("slaif_agent_item_relation_update", _RELATION_UPDATE_SIGNATURE),
        ("slaif_agent_item_relation_delete", _RELATION_DELETE_SIGNATURE),
        ("slaif_agent_collection_view_create", _VIEW_CREATE_SIGNATURE),
        ("slaif_agent_collection_view_list", _VIEW_LIST_SIGNATURE),
        ("slaif_agent_collection_view_get", _VIEW_GET_SIGNATURE),
        ("slaif_agent_collection_view_current", _VIEW_CURRENT_SIGNATURE),
        ("slaif_agent_collection_view_fields", _VIEW_FIELDS_SIGNATURE),
        ("slaif_agent_collection_view_update", _VIEW_UPDATE_SIGNATURE),
        ("slaif_agent_collection_view_delete", _VIEW_DELETE_SIGNATURE),
    ):
        qualified = f"content.{name}({signature})"
        op.execute(f"ALTER FUNCTION {qualified} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {qualified} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {qualified} TO slaif_agent_runtime")
    for name, signature in (
        ("slaif_agent_relation_assert", "uuid,uuid,uuid,uuid,text,boolean"),
        ("slaif_agent_collection_view_query_validate", "uuid,jsonb,jsonb,jsonb,jsonb"),
    ):
        qualified = f"content.{name}({signature})"
        op.execute(f"ALTER FUNCTION {qualified} OWNER TO slaif_owner")
        op.execute(
            f"REVOKE ALL ON FUNCTION {qualified} FROM PUBLIC, slaif_agent_runtime"
        )


def downgrade() -> None:
    _drop_agent_functions()
    # Leave the current exact constraint in place while the canonical 047
    # upgrade replaces it with its forward-compatible historical shape. This
    # keeps immutable 048 audit rows valid throughout the transition without a
    # permissive intermediate CHECK or any audit-row replay.
    op.execute(
        "DROP FUNCTION IF EXISTS control.slaif_agent_require_capability(uuid,text) CASCADE"
    )
    for name, signature in (
        ("slaif_agent_content_type_list", "uuid"),
        ("slaif_agent_content_type_get", "uuid,uuid"),
        ("slaif_agent_field_definition_list", "uuid,uuid"),
        ("slaif_agent_content_item_list", "uuid,uuid"),
        ("slaif_agent_content_item_get", "uuid,uuid"),
        ("slaif_agent_content_type_create", "uuid,text,jsonb,text,jsonb"),
        ("slaif_agent_content_type_update", "uuid,uuid,jsonb,text,jsonb,integer"),
        ("slaif_agent_content_type_delete", "uuid,uuid,integer"),
        (
            "slaif_agent_field_definition_create",
            "uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb",
        ),
        (
            "slaif_agent_field_definition_update",
            "uuid,uuid,uuid,text,boolean,boolean,integer,integer,jsonb,jsonb,integer",
        ),
        ("slaif_agent_field_definition_delete", "uuid,uuid,uuid,integer"),
        ("slaif_agent_content_item_create", "uuid,uuid,text,text,jsonb"),
        ("slaif_agent_content_item_update", "uuid,uuid,text,text,jsonb,integer"),
        ("slaif_agent_content_item_delete", "uuid,uuid,integer"),
        ("slaif_agent_content_item_translation_fields_for_write", "uuid,uuid"),
        ("slaif_agent_content_item_translation_list", "uuid,uuid"),
        ("slaif_agent_content_item_translation_get", "uuid,uuid,uuid"),
        ("slaif_agent_content_item_translation_create", "uuid,uuid,text,jsonb"),
        (
            "slaif_agent_content_item_translation_update",
            "uuid,uuid,uuid,text,jsonb,integer",
        ),
        ("slaif_agent_content_item_translation_delete", "uuid,uuid,uuid,integer"),
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{name}({signature}) CASCADE")
    # 047's upgrade removes the one-argument helper from 046 before installing
    # its two-argument capability boundary. Recreate that historical symbol so
    # the canonical predecessor can perform its own reversible transition.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_require_capability(p_site_id uuid)
        RETURNS uuid LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog
        AS $$ SELECT NULL::uuid $$
        """
    )
    predecessor = import_module(
        "slaif_agent_site.db.alembic.versions.047_001_repair_item_semantics_and_translations"
    )
    predecessor.upgrade()
