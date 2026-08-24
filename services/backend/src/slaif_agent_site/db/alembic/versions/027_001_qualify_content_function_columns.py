# ruff: noqa: E501
"""Qualify content function columns for PL/pgSQL output-variable safety."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "027_001"
down_revision: str | Sequence[str] | None = "026_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_page_create(
            p_site_id uuid, p_slug text, p_title text,
            p_status text, p_locale text
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text,
            status text, locale text, parent_id uuid,
            row_version integer, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            INSERT INTO content.page (site_id, slug, title, status, locale)
            VALUES (p_site_id, p_slug, p_title, p_status, p_locale);
            RETURN QUERY SELECT page.* FROM content.page AS page
            WHERE page.site_id = p_site_id
              AND page.locale = p_locale
              AND page.slug = p_slug
            LIMIT 1;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_page_list(
            p_site_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text,
            status text, locale text, parent_id uuid,
            row_version integer, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT page.* FROM content.page AS page
            WHERE page.site_id = p_site_id
            ORDER BY page.slug COLLATE "C"
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_page_get(
            p_page_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text,
            status text, locale text, parent_id uuid,
            row_version integer, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT page.* FROM content.page AS page WHERE page.id = p_page_id
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_page_update(
            p_page_id uuid, p_slug text, p_title text,
            p_status text, p_expected_row_version integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text,
            status text, locale text, parent_id uuid,
            row_version integer, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.page AS page SET
                slug = COALESCE(p_slug, page.slug),
                title = COALESCE(p_title, page.title),
                status = COALESCE(p_status, page.status),
                row_version = page.row_version + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE page.id = p_page_id
              AND (p_expected_row_version IS NULL
                   OR page.row_version = p_expected_row_version);
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT page.* FROM content.page AS page
            WHERE page.id = p_page_id;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_page_delete(
            p_page_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            DELETE FROM content.page AS page WHERE page.id = p_page_id;
        END;
        $fn$
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_composition_node_add(
            p_site_id uuid, p_page_id uuid, p_component_type text,
            p_parent_id uuid, p_slot_key text, p_order_key integer, p_props jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, page_id uuid, component_type text,
            schema_version text, parent_id uuid, slot_key text,
            order_key integer, props jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            INSERT INTO content.page_composition
                (site_id, page_id, component_type, parent_id, slot_key, order_key, props)
            VALUES (p_site_id, p_page_id, p_component_type, p_parent_id,
                    p_slot_key, p_order_key, p_props);
            RETURN QUERY SELECT composition.*
            FROM content.page_composition AS composition
            WHERE composition.site_id = p_site_id
              AND composition.page_id = p_page_id
              AND composition.component_type = p_component_type
              AND composition.slot_key = p_slot_key
              AND composition.order_key = p_order_key
            ORDER BY composition.created_at DESC LIMIT 1;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_composition_node_update(
            p_node_id uuid, p_props jsonb, p_slot_key text, p_order_key integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, page_id uuid, component_type text,
            schema_version text, parent_id uuid, slot_key text,
            order_key integer, props jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.page_composition AS composition SET
                props = COALESCE(p_props, composition.props),
                slot_key = COALESCE(p_slot_key, composition.slot_key),
                order_key = COALESCE(p_order_key, composition.order_key),
                updated_at = CURRENT_TIMESTAMP
            WHERE composition.id = p_node_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT composition.*
            FROM content.page_composition AS composition
            WHERE composition.id = p_node_id;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_composition_node_move(
            p_node_id uuid, p_new_parent_id uuid, p_new_slot_key text,
            p_new_order_key integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, page_id uuid, component_type text,
            schema_version text, parent_id uuid, slot_key text,
            order_key integer, props jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.page_composition AS composition SET
                parent_id = COALESCE(p_new_parent_id, composition.parent_id),
                slot_key = COALESCE(p_new_slot_key, composition.slot_key),
                order_key = p_new_order_key,
                updated_at = CURRENT_TIMESTAMP
            WHERE composition.id = p_node_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT composition.*
            FROM content.page_composition AS composition
            WHERE composition.id = p_node_id;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_composition_node_delete(
            p_node_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE child record;
        BEGIN
            FOR child IN
                SELECT composition.id FROM content.page_composition AS composition
                WHERE composition.parent_id = p_node_id
            LOOP
                PERFORM content.slaif_composition_node_delete(child.id);
            END LOOP;
            DELETE FROM content.page_composition AS composition
            WHERE composition.id = p_node_id;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_composition_list(
            p_page_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, page_id uuid, component_type text,
            schema_version text, parent_id uuid, slot_key text,
            order_key integer, props jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT composition.* FROM content.page_composition AS composition
            WHERE composition.page_id = p_page_id
            ORDER BY composition.slot_key COLLATE "C", composition.order_key
        $fn$
        """
    )


def downgrade() -> None:
    # The prior definitions are unsafe for calls with PL/pgSQL output variables;
    # retaining the qualified definitions is the only safe downgrade behavior.
    pass
