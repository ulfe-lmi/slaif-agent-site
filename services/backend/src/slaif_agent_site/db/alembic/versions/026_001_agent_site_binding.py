# ruff: noqa: E501
"""Bind Agent semantic wrappers to the active workspace site in PostgreSQL."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "026_001"
down_revision: str | Sequence[str] | None = "025_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_FUNCTIONS = (
    (
        "content.slaif_agent_content_type_create",
        "content.slaif_agent_unchecked_content_type_create",
        "uuid,text,jsonb,text,jsonb",
    ),
    (
        "content.slaif_agent_field_definition_create",
        "content.slaif_agent_unchecked_field_definition_create",
        "uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb",
    ),
    (
        "content.slaif_agent_content_item_create",
        "content.slaif_agent_unchecked_content_item_create",
        "uuid,uuid,text,text,jsonb,integer",
    ),
    (
        "content.slaif_agent_page_create",
        "content.slaif_agent_unchecked_page_create",
        "uuid,text,text,text,text,uuid",
    ),
    (
        "content.slaif_agent_composition_node_add",
        "content.slaif_agent_unchecked_composition_node_add",
        "uuid,uuid,text,uuid,text,integer,jsonb",
    ),
)


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_require_cow_site(
            p_site_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            session_text text;
            operation_text text;
            session_uuid uuid;
            operation_uuid uuid;
            workspace_site uuid;
        BEGIN
            session_text := NULLIF(current_setting('app.session_id', true), '');
            operation_text := NULLIF(current_setting('app.operation_id', true), '');
            IF session_text IS NULL OR operation_text IS NULL THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE = '22023';
            END IF;
            BEGIN
                session_uuid := session_text::uuid;
                operation_uuid := operation_text::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE = '22023';
            END;
            IF session_uuid IS NULL OR operation_uuid IS NULL THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE = '22023';
            END IF;
            SELECT workspace.site_id
            INTO workspace_site
            FROM control.workspace AS workspace
            WHERE workspace.id = session_uuid
              AND workspace.status = 'ACTIVE'
              AND workspace.expires_at > CURRENT_TIMESTAMP;
            IF workspace_site IS NULL OR workspace_site IS DISTINCT FROM p_site_id THEN
                RAISE EXCEPTION 'COW_SITE_MISMATCH' USING ERRCODE = 'P0002';
            END IF;
        END;
        $fn$
        """
    )
    op.execute(
        """
        REVOKE ALL ON FUNCTION control.slaif_agent_require_cow_site(uuid)
            FROM PUBLIC, slaif_agent_runtime
        """
    )

    for guarded, unchecked, signature in _FUNCTIONS:
        op.execute(
            f"ALTER FUNCTION {guarded}({signature}) RENAME TO {unchecked.rsplit('.', 1)[1]}"
        )
        op.execute(
            f"REVOKE ALL ON FUNCTION {unchecked}({signature}) FROM PUBLIC, slaif_agent_runtime"
        )

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
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT * FROM content.slaif_agent_unchecked_content_type_create(
                p_site_id, p_key, p_labels, p_slug_pattern, p_settings
            );
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
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT * FROM content.slaif_agent_unchecked_field_definition_create(
                p_site_id, p_type_id, p_key, p_label, p_field_type, p_required,
                p_localized, p_cardinality, p_position, p_validation,
                p_ui_options
            );
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
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT * FROM content.slaif_agent_unchecked_content_item_create(
                p_site_id, p_type_id, p_slug, p_status, p_values,
                p_type_definition_version
            );
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
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT * FROM content.slaif_agent_unchecked_page_create(
                p_site_id, p_slug, p_title, p_status, p_locale, p_parent_id
            );
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
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT * FROM content.slaif_agent_unchecked_composition_node_add(
                p_site_id, p_page_id, p_component_type, p_parent_id,
                p_slot_key, p_order_key, p_props
            );
        END;
        $fn$
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
    for guarded, unchecked, signature in _FUNCTIONS:
        op.execute(f"DROP FUNCTION IF EXISTS {guarded}({signature}) CASCADE")
        original_name = guarded.rsplit(".", 1)[1]
        op.execute(f"ALTER FUNCTION {unchecked}({signature}) RENAME TO {original_name}")
        op.execute(
            f"GRANT EXECUTE ON FUNCTION {guarded}({signature}) TO slaif_agent_runtime"
        )
    op.execute("DROP FUNCTION IF EXISTS control.slaif_agent_require_cow_site(uuid)")
