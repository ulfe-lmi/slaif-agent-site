# ruff: noqa: E501
"""Add the bounded Agent COW mutation and durable idempotency surface."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "025_001"
down_revision: str | Sequence[str] | None = "024_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Idempotency is control-plane state, not content/COW state.  It is
    # completed in the same transaction as the COW operation by two narrow
    # SECURITY DEFINER functions; the Agent role receives no table DML.
    op.execute(
        """
        CREATE TABLE control.agent_idempotency (
            capability_id UUID NOT NULL REFERENCES control.capability(id),
            workspace_id UUID NOT NULL REFERENCES control.workspace(id),
            idempotency_key TEXT NOT NULL,
            request_digest TEXT NOT NULL,
            operation_id UUID NOT NULL UNIQUE,
            status_code INTEGER,
            response_body JSONB,
            resource_type TEXT,
            resource_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            PRIMARY KEY (capability_id, idempotency_key),
            CONSTRAINT agent_idempotency_digest_shape
                CHECK (request_digest ~ '^[0-9a-f]{64}$'),
            CONSTRAINT agent_idempotency_completion_shape
                CHECK (
                    (status_code IS NULL AND response_body IS NULL
                        AND resource_type IS NULL AND resource_id IS NULL
                        AND completed_at IS NULL)
                    OR
                    (status_code BETWEEN 200 AND 299
                        AND response_body IS NOT NULL
                        AND resource_type IS NOT NULL
                        AND resource_id IS NOT NULL
                        AND completed_at IS NOT NULL)
                )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE audit.agent_mutation (
            operation_id UUID PRIMARY KEY,
            capability_id UUID NOT NULL,
            workspace_id UUID NOT NULL,
            site_id UUID NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id UUID NOT NULL,
            request_digest TEXT NOT NULL,
            response_status INTEGER NOT NULL,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT agent_mutation_digest_shape
                CHECK (request_digest ~ '^[0-9a-f]{64}$'),
            CONSTRAINT agent_mutation_status_shape
                CHECK (response_status BETWEEN 200 AND 299)
        )
        """
    )

    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_idempotency_begin(
            p_capability_id uuid, p_workspace_id uuid, p_idempotency_key text,
            p_request_digest text, p_operation_id uuid
        ) RETURNS TABLE (
            state text, operation_id uuid, status_code integer, response_body jsonb
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
            expected_workspace uuid;
            inserted_count integer;
            existing control.agent_idempotency%ROWTYPE;
        BEGIN
            IF length(p_idempotency_key) NOT BETWEEN 1 AND 128
               OR p_idempotency_key !~ '^[A-Za-z0-9._~-]+$'
               OR p_request_digest !~ '^[0-9a-f]{64}$'
            THEN
                RAISE EXCEPTION 'INVALID_IDEMPOTENCY_INPUT' USING ERRCODE = 'P0001';
            END IF;

            SELECT capability.workspace_id
            INTO expected_workspace
            FROM control.capability AS capability
            JOIN control.workspace AS workspace
              ON workspace.id = capability.workspace_id
            WHERE capability.id = p_capability_id
              AND capability.workspace_id = p_workspace_id
              AND capability.revoked_at IS NULL
              AND (capability.expires_at IS NULL
                   OR capability.expires_at > CURRENT_TIMESTAMP)
              AND workspace.status = 'ACTIVE'
              AND workspace.expires_at > CURRENT_TIMESTAMP;
            IF expected_workspace IS NULL THEN
                RAISE EXCEPTION 'CAPABILITY_WORKSPACE_NOT_ACTIVE'
                    USING ERRCODE = 'P0002';
            END IF;

            INSERT INTO control.agent_idempotency (
                capability_id, workspace_id, idempotency_key,
                request_digest, operation_id
            ) VALUES (
                p_capability_id, p_workspace_id, p_idempotency_key,
                p_request_digest, p_operation_id
            ) ON CONFLICT (capability_id, idempotency_key) DO NOTHING;
            GET DIAGNOSTICS inserted_count = ROW_COUNT;
            IF inserted_count = 1 THEN
                RETURN QUERY SELECT
                    'STARTED'::text, p_operation_id, NULL::integer, NULL::jsonb;
                RETURN;
            END IF;

            SELECT *
            INTO existing
            FROM control.agent_idempotency
            WHERE capability_id = p_capability_id
              AND idempotency_key = p_idempotency_key
            FOR UPDATE;
            IF existing.request_digest <> p_request_digest THEN
                RETURN QUERY SELECT
                    'MISMATCH'::text, existing.operation_id,
                    NULL::integer, NULL::jsonb;
                RETURN;
            END IF;
            IF existing.status_code IS NULL THEN
                RAISE EXCEPTION 'IDEMPOTENCY_IN_PROGRESS'
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
        CREATE FUNCTION control.slaif_agent_idempotency_complete(
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

    # These wrappers are the only content mutation functions granted to the
    # Agent role.  Each requires the foundation's trusted session/operation
    # context and checks site/resource relationships before invoking the
    # existing semantic function.
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_create(
            p_site_id uuid, p_key text, p_labels jsonb,
            p_slug_pattern text, p_settings jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, key text, labels jsonb,
            slug_pattern text, status text, definition_version integer,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            IF NULLIF(current_setting('app.session_id', true), '') IS NULL
               OR NULLIF(current_setting('app.operation_id', true), '') IS NULL
            THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE = '22023';
            END IF;
            INSERT INTO content.content_type
                (site_id, "key", labels, slug_pattern, settings)
            VALUES (p_site_id, p_key, p_labels, p_slug_pattern, p_settings);
            RETURN QUERY SELECT content_type.* FROM content.content_type
                AS content_type
            WHERE content_type.site_id = p_site_id
              AND content_type."key" = p_key
            ORDER BY content_type.created_at DESC LIMIT 1;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_create(
            p_site_id uuid, p_type_id uuid, p_key text, p_label text,
            p_field_type text, p_required boolean, p_localized boolean,
            p_cardinality integer, p_position integer, p_validation jsonb,
            p_ui_options jsonb
        ) RETURNS TABLE (
            id uuid, type_id uuid, "key" text, label text, field_type text,
            required boolean, localized boolean, cardinality integer,
            "position" integer, validation jsonb, ui_options jsonb,
            definition_version integer, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            IF NULLIF(current_setting('app.session_id', true), '') IS NULL
               OR NULLIF(current_setting('app.operation_id', true), '') IS NULL
               OR NOT EXISTS (
                   SELECT 1 FROM content.content_type AS content_type
                   WHERE content_type.id = p_type_id
                     AND content_type.site_id = p_site_id
                     AND content_type.status = 'ACTIVE'
               )
            THEN
                RAISE EXCEPTION 'FIELD_TYPE_SITE_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            INSERT INTO content.field_definition (
                type_id, "key", label, field_type, required, localized,
                cardinality, "position", validation, ui_options
            ) VALUES (
                p_type_id, p_key, p_label, p_field_type, p_required,
                p_localized, p_cardinality, p_position, p_validation,
                p_ui_options
            );
            RETURN QUERY SELECT field_definition.* FROM content.field_definition
                AS field_definition
            WHERE field_definition.type_id = p_type_id
              AND field_definition."key" = p_key
            ORDER BY field_definition.created_at DESC LIMIT 1;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_item_create(
            p_site_id uuid, p_type_id uuid, p_slug text, p_status text,
            p_values jsonb, p_type_definition_version integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, type_id uuid, slug text, status text,
            type_definition_version integer, "values" jsonb, row_version integer,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            IF NULLIF(current_setting('app.session_id', true), '') IS NULL
               OR NULLIF(current_setting('app.operation_id', true), '') IS NULL
               OR NOT EXISTS (
                   SELECT 1 FROM content.content_type AS content_type
                   WHERE content_type.id = p_type_id
                     AND content_type.site_id = p_site_id
                     AND content_type.status = 'ACTIVE'
               )
            THEN
                RAISE EXCEPTION 'ITEM_TYPE_SITE_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            INSERT INTO content.content_item (
                site_id, type_id, slug, status, "values", type_definition_version
            ) VALUES (
                p_site_id, p_type_id, p_slug, p_status, p_values,
                p_type_definition_version
            );
            RETURN QUERY SELECT content_item.* FROM content.content_item
                AS content_item
            WHERE content_item.site_id = p_site_id
              AND content_item.type_id = p_type_id
              AND content_item.slug = p_slug
            ORDER BY content_item.created_at DESC LIMIT 1;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_page_create(
            p_site_id uuid, p_slug text, p_title text, p_status text,
            p_locale text, p_parent_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text, status text,
            locale text, parent_id uuid, row_version integer,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
            created_id uuid;
        BEGIN
            IF NULLIF(current_setting('app.session_id', true), '') IS NULL
               OR NULLIF(current_setting('app.operation_id', true), '') IS NULL
               OR (
                   p_parent_id IS NOT NULL AND NOT EXISTS (
                       SELECT 1 FROM content.page AS parent_page
                       WHERE parent_page.id = p_parent_id
                         AND parent_page.site_id = p_site_id
                   )
               )
            THEN
                RAISE EXCEPTION 'PAGE_PARENT_SITE_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            created_id := gen_random_uuid();
            INSERT INTO content.page
                (id, site_id, slug, title, status, locale, parent_id)
            VALUES (
                created_id, p_site_id, p_slug, p_title, p_status, p_locale,
                p_parent_id
            );
            RETURN QUERY SELECT page.* FROM content.page AS page
            WHERE page.id = created_id;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_composition_node_add(
            p_site_id uuid, p_page_id uuid, p_component_type text,
            p_parent_id uuid, p_slot_key text, p_order_key integer, p_props jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, page_id uuid, component_type text,
            schema_version text, parent_id uuid, slot_key text,
            order_key integer, props jsonb, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
            created_id uuid;
        BEGIN
            IF NULLIF(current_setting('app.session_id', true), '') IS NULL
               OR NULLIF(current_setting('app.operation_id', true), '') IS NULL
               OR NOT EXISTS (
                   SELECT 1 FROM content.page AS page
                   WHERE page.id = p_page_id AND page.site_id = p_site_id
               )
               OR (
                   p_parent_id IS NOT NULL AND NOT EXISTS (
                       SELECT 1 FROM content.page_composition AS parent_node
                       WHERE parent_node.id = p_parent_id
                         AND parent_node.page_id = p_page_id
                         AND parent_node.site_id = p_site_id
                   )
               )
            THEN
                RAISE EXCEPTION 'COMPOSITION_PARENT_SITE_NOT_FOUND'
                    USING ERRCODE = 'P0002';
            END IF;
            created_id := gen_random_uuid();
            INSERT INTO content.page_composition (
                id, site_id, page_id, component_type, parent_id, slot_key,
                order_key, props
            ) VALUES (
                created_id, p_site_id, p_page_id, p_component_type,
                p_parent_id, p_slot_key, p_order_key, p_props
            );
            RETURN QUERY SELECT page_composition.*
            FROM content.page_composition AS page_composition
            WHERE page_composition.id = created_id;
        END;
        $fn$
        """
    )

    op.execute(
        """
        GRANT EXECUTE ON FUNCTION control.slaif_agent_idempotency_begin(
            uuid,uuid,text,text,uuid
        ) TO slaif_agent_runtime
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION control.slaif_agent_idempotency_complete(
            uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid
        ) TO slaif_agent_runtime
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_content_type_create(
            uuid,text,jsonb,text,jsonb
        ) TO slaif_agent_runtime
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_field_definition_create(
            uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb
        ) TO slaif_agent_runtime
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_content_item_create(
            uuid,uuid,text,text,jsonb,integer
        ) TO slaif_agent_runtime
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_page_create(
            uuid,text,text,text,text,uuid
        ) TO slaif_agent_runtime
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_composition_node_add(
            uuid,uuid,text,uuid,text,integer,jsonb
        ) TO slaif_agent_runtime
        """
    )


def downgrade() -> None:
    for function in (
        "content.slaif_agent_composition_node_add(uuid,uuid,text,uuid,text,integer,jsonb)",
        "content.slaif_agent_page_create(uuid,text,text,text,text,uuid)",
        "content.slaif_agent_content_item_create(uuid,uuid,text,text,jsonb,integer)",
        "content.slaif_agent_field_definition_create(uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb)",
        "content.slaif_agent_content_type_create(uuid,text,jsonb,text,jsonb)",
        "control.slaif_agent_idempotency_complete(uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid)",
        "control.slaif_agent_idempotency_begin(uuid,uuid,text,text,uuid)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function} CASCADE")
    op.execute("DROP TABLE IF EXISTS audit.agent_mutation")
    op.execute("DROP TABLE IF EXISTS control.agent_idempotency")
