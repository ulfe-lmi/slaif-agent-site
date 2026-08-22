# ruff: noqa: E501
"""Create page composition table with CRUD functions."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "022_001"
down_revision: str | Sequence[str] | None = "021_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS content.page_composition (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL REFERENCES control.site(id),
            page_id UUID NOT NULL REFERENCES content.page(id),
            component_type TEXT NOT NULL,
            schema_version TEXT NOT NULL DEFAULT '1',
            parent_id UUID REFERENCES content.page_composition(id),
            slot_key TEXT NOT NULL DEFAULT 'default',
            order_key INTEGER NOT NULL DEFAULT 0,
            props JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE INDEX idx_page_composition_page ON content.page_composition (page_id)
    """)

    # Add node
    op.execute("""
        CREATE FUNCTION content.slaif_composition_node_add(
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
            VALUES (p_site_id, p_page_id, p_component_type, p_parent_id, p_slot_key, p_order_key, p_props);
            RETURN QUERY SELECT * FROM content.page_composition
            WHERE site_id = p_site_id AND page_id = p_page_id
              AND component_type = p_component_type AND slot_key = p_slot_key
              AND order_key = p_order_key
            ORDER BY created_at DESC LIMIT 1;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_composition_node_add(uuid,uuid,text,uuid,text,integer,jsonb) TO slaif_editor_runtime, slaif_control"
    )

    # Update node
    op.execute("""
        CREATE FUNCTION content.slaif_composition_node_update(
            p_node_id uuid, p_props jsonb, p_slot_key text, p_order_key integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, page_id uuid, component_type text,
            schema_version text, parent_id uuid, slot_key text,
            order_key integer, props jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.page_composition SET
                props = COALESCE(p_props, props),
                slot_key = COALESCE(p_slot_key, slot_key),
                order_key = COALESCE(p_order_key, order_key),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = p_node_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT * FROM content.page_composition WHERE id = p_node_id;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_composition_node_update(uuid,jsonb,text,integer) TO slaif_editor_runtime, slaif_control"
    )

    # Move node (change parent/slot/order)
    op.execute("""
        CREATE FUNCTION content.slaif_composition_node_move(
            p_node_id uuid, p_new_parent_id uuid, p_new_slot_key text, p_new_order_key integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, page_id uuid, component_type text,
            schema_version text, parent_id uuid, slot_key text,
            order_key integer, props jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.page_composition SET
                parent_id = COALESCE(p_new_parent_id, parent_id),
                slot_key = COALESCE(p_new_slot_key, slot_key),
                order_key = p_new_order_key,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = p_node_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT * FROM content.page_composition WHERE id = p_node_id;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_composition_node_move(uuid,uuid,text,integer) TO slaif_editor_runtime, slaif_control"
    )

    # Delete node and descendants
    op.execute("""
        CREATE FUNCTION content.slaif_composition_node_delete(
            p_node_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE child record;
        BEGIN
            FOR child IN SELECT id FROM content.page_composition WHERE parent_id = p_node_id LOOP
                PERFORM content.slaif_composition_node_delete(child.id);
            END LOOP;
            DELETE FROM content.page_composition WHERE id = p_node_id;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_composition_node_delete(uuid) TO slaif_editor_runtime, slaif_control"
    )

    # List nodes for a page
    op.execute("""
        CREATE FUNCTION content.slaif_composition_list(
            p_page_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, page_id uuid, component_type text,
            schema_version text, parent_id uuid, slot_key text,
            order_key integer, props jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.page_composition
            WHERE page_id = p_page_id
            ORDER BY slot_key COLLATE "C", order_key
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_composition_list(uuid) TO slaif_editor_runtime, slaif_control"
    )


def downgrade() -> None:
    for fn in (
        "slaif_composition_node_add(uuid,uuid,text,uuid,text,integer,jsonb)",
        "slaif_composition_node_update(uuid,jsonb,text,integer)",
        "slaif_composition_node_move(uuid,uuid,text,integer)",
        "slaif_composition_node_delete(uuid)",
        "slaif_composition_list(uuid)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{fn} CASCADE")
    op.execute("""
        DO $$
        DECLARE obj record;
        BEGIN
          FOR obj IN
            SELECT c.relname, c.relkind FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace ns ON ns.oid = c.relnamespace
            WHERE ns.nspname = 'content' AND c.relname = 'page_composition'
              AND c.relkind IN ('r','v','S')
          LOOP
            IF obj.relkind = 'v' THEN
              EXECUTE format('DROP VIEW IF EXISTS content.%I CASCADE', obj.relname);
            ELSE
              EXECUTE format('DROP TABLE IF EXISTS content.%I CASCADE', obj.relname);
            END IF;
          END LOOP;
        END $$;
    """)
