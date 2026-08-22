# ruff: noqa: E501
"""Create SECURITY DEFINER functions for content item CRUD."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "018_001"
down_revision: str | Sequence[str] | None = "017_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE FUNCTION content.slaif_content_item_create(
            p_site_id uuid, p_type_id uuid, p_slug text,
            p_status text, p_values jsonb, p_type_def_version integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, type_id uuid, slug text,
            status text, type_definition_version integer,
            values jsonb, row_version integer,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            INSERT INTO content.content_item (site_id, type_id, slug, status, values, type_definition_version)
            VALUES (p_site_id, p_type_id, p_slug, p_status, p_values, p_type_def_version);
            RETURN QUERY SELECT * FROM content.content_item
            WHERE site_id = p_site_id AND type_id = p_type_id AND slug = p_slug LIMIT 1;
        END;
        $fn$
    """)
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_content_item_create(uuid,uuid,text,text,jsonb,integer) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_content_item_create(uuid,uuid,text,text,jsonb,integer) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_content_item_list(
            p_site_id uuid, p_type_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, type_id uuid, slug text,
            status text, type_definition_version integer,
            values jsonb, row_version integer,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.content_item
            WHERE site_id = p_site_id AND type_id = p_type_id
              AND status != 'DELETED'
            ORDER BY slug COLLATE "C"
        $fn$
    """)
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_content_item_list(uuid,uuid) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_content_item_list(uuid,uuid) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_content_item_get(
            p_item_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, type_id uuid, slug text,
            status text, type_definition_version integer,
            values jsonb, row_version integer,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.content_item WHERE id = p_item_id
        $fn$
    """)
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_content_item_get(uuid) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_content_item_get(uuid) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_content_item_update(
            p_item_id uuid, p_slug text, p_status text,
            p_values jsonb, p_expected_row_version integer, _unused text
        ) RETURNS TABLE (
            id uuid, site_id uuid, type_id uuid, slug text,
            status text, type_definition_version integer,
            values jsonb, row_version integer,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            IF p_expected_row_version IS NOT NULL THEN
                UPDATE content.content_item SET
                    slug = COALESCE(p_slug, slug),
                    status = COALESCE(p_status, status),
                    values = COALESCE(p_values, values),
                    row_version = row_version + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = p_item_id AND row_version = p_expected_row_version;
            ELSE
                UPDATE content.content_item SET
                    slug = COALESCE(p_slug, slug),
                    status = COALESCE(p_status, status),
                    values = COALESCE(p_values, values),
                    row_version = row_version + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = p_item_id;
            END IF;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT * FROM content.content_item WHERE id = p_item_id;
        END;
        $fn$
    """)
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_content_item_update(uuid,text,text,jsonb,integer,text) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_content_item_update(uuid,text,text,jsonb,integer,text) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_content_item_delete(
            p_item_id uuid, p_expected_row_version integer
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            DELETE FROM content.content_item WHERE id = p_item_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
        END;
        $fn$
    """)
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_content_item_delete(uuid,integer) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_content_item_delete(uuid,integer) TO slaif_editor_runtime, slaif_control"
    )


def downgrade() -> None:
    for fn in (
        "slaif_content_item_create(uuid,uuid,text,text,jsonb,integer)",
        "slaif_content_item_list(uuid,uuid)",
        "slaif_content_item_get(uuid)",
        "slaif_content_item_update(uuid,text,text,jsonb,integer,text)",
        "slaif_content_item_delete(uuid,integer)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{fn} CASCADE")
