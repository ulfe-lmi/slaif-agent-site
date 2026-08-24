# ruff: noqa: E501
"""Add site-bound, least-privileged Agent semantic read wrappers."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "029_001"
down_revision: str | Sequence[str] | None = "028_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_FUNCTIONS = (
    ("content.slaif_agent_content_type_list", "uuid"),
    ("content.slaif_agent_content_type_get", "uuid,uuid"),
    ("content.slaif_agent_field_definition_list", "uuid,uuid"),
    ("content.slaif_agent_content_item_list", "uuid,uuid"),
    ("content.slaif_agent_page_list", "uuid"),
    ("content.slaif_agent_composition_list", "uuid,uuid"),
    ("content.slaif_agent_media_list", "uuid"),
)


def _secure(function: str, signature: str) -> None:
    qualified = f"{function}({signature})"
    op.execute(f"ALTER FUNCTION {qualified} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {qualified} FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION {qualified} TO slaif_agent_runtime")


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_list(
            p_site_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, "key" text, labels jsonb,
            slug_pattern text, status text, definition_version integer,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY
            SELECT content_type.*
            FROM content.content_type AS content_type
            WHERE content_type.site_id = p_site_id
              AND content_type.status != 'DELETED'
            ORDER BY content_type."key" COLLATE "C";
        END;
        $fn$
        """
    )
    _secure("content.slaif_agent_content_type_list", "uuid")

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_get(
            p_site_id uuid, p_type_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, "key" text, labels jsonb,
            slug_pattern text, status text, definition_version integer,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY
            SELECT content_type.*
            FROM content.content_type AS content_type
            WHERE content_type.id = p_type_id
              AND content_type.site_id = p_site_id
              AND content_type.status != 'DELETED';
        END;
        $fn$
        """
    )
    _secure("content.slaif_agent_content_type_get", "uuid,uuid")

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_list(
            p_site_id uuid, p_type_id uuid
        ) RETURNS TABLE (
            id uuid, type_id uuid, "key" text, label text, field_type text,
            required boolean, localized boolean, cardinality integer,
            "position" integer, validation jsonb, ui_options jsonb,
            definition_version integer, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            IF NOT EXISTS (
                SELECT 1
                FROM content.content_type AS content_type
                WHERE content_type.id = p_type_id
                  AND content_type.site_id = p_site_id
                  AND content_type.status != 'DELETED'
            ) THEN
                RAISE EXCEPTION 'AGENT_TYPE_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY
            SELECT field_definition.*
            FROM content.field_definition AS field_definition
            JOIN content.content_type AS content_type
              ON content_type.id = field_definition.type_id
             AND content_type.site_id = p_site_id
             AND content_type.status != 'DELETED'
            WHERE field_definition.type_id = p_type_id
            ORDER BY field_definition."position", field_definition."key" COLLATE "C";
        END;
        $fn$
        """
    )
    _secure("content.slaif_agent_field_definition_list", "uuid,uuid")

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_item_list(
            p_site_id uuid, p_type_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, type_id uuid, slug text, status text,
            type_definition_version integer, "values" jsonb,
            row_version integer, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            IF NOT EXISTS (
                SELECT 1
                FROM content.content_type AS content_type
                WHERE content_type.id = p_type_id
                  AND content_type.site_id = p_site_id
                  AND content_type.status != 'DELETED'
            ) THEN
                RAISE EXCEPTION 'AGENT_TYPE_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY
            SELECT content_item.*
            FROM content.content_item AS content_item
            JOIN content.content_type AS content_type
              ON content_type.id = content_item.type_id
             AND content_type.site_id = p_site_id
             AND content_type.status != 'DELETED'
            WHERE content_item.site_id = p_site_id
              AND content_item.type_id = p_type_id
              AND content_item.status != 'DELETED'
            ORDER BY content_item.slug COLLATE "C";
        END;
        $fn$
        """
    )
    _secure("content.slaif_agent_content_item_list", "uuid,uuid")

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_page_list(
            p_site_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text, status text,
            locale text, parent_id uuid, row_version integer,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY
            SELECT page.*
            FROM content.page AS page
            WHERE page.site_id = p_site_id
            ORDER BY page.slug COLLATE "C";
        END;
        $fn$
        """
    )
    _secure("content.slaif_agent_page_list", "uuid")

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_composition_list(
            p_site_id uuid, p_page_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, page_id uuid, component_type text,
            schema_version text, parent_id uuid, slot_key text,
            order_key integer, props jsonb, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            IF NOT EXISTS (
                SELECT 1
                FROM content.page AS page
                WHERE page.id = p_page_id
                  AND page.site_id = p_site_id
            ) THEN
                RAISE EXCEPTION 'AGENT_PAGE_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY
            SELECT composition.*
            FROM content.page_composition AS composition
            JOIN content.page AS page
              ON page.id = composition.page_id
             AND page.site_id = p_site_id
            WHERE composition.site_id = p_site_id
              AND composition.page_id = p_page_id
            ORDER BY composition.slot_key COLLATE "C", composition.order_key;
        END;
        $fn$
        """
    )
    _secure("content.slaif_agent_composition_list", "uuid,uuid")

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_media_list(
            p_site_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, uploaded_by uuid, filename text,
            mime_type text, size_bytes bigint, content_hash text,
            storage_key text, alt_text text, metadata jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY
            SELECT media_asset.*
            FROM content.media_asset AS media_asset
            WHERE media_asset.site_id = p_site_id
            ORDER BY media_asset.created_at DESC;
        END;
        $fn$
        """
    )
    _secure("content.slaif_agent_media_list", "uuid")


def downgrade() -> None:
    for function, signature in reversed(_FUNCTIONS):
        op.execute(f"DROP FUNCTION IF EXISTS {function}({signature}) CASCADE")
