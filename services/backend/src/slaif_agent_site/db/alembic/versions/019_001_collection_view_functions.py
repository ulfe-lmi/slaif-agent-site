# ruff: noqa: E501
"""Create SECURITY DEFINER functions for collection view CRUD."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "019_001"
down_revision: str | Sequence[str] | None = "018_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE FUNCTION content.slaif_collection_view_create(
            p_type_id uuid, p_key text, p_filter jsonb,
            p_sort jsonb, p_projection jsonb, p_pagination jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, type_id uuid, "key" text,
            filter_spec jsonb, sort_spec jsonb, projection_spec jsonb,
            pagination_spec jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            INSERT INTO content.collection_view (type_id, "key", filter_spec, sort_spec, projection_spec, pagination_spec)
            VALUES (p_type_id, p_key, p_filter, p_sort, p_projection, p_pagination);
            RETURN QUERY SELECT * FROM content.collection_view WHERE type_id = p_type_id AND "key" = p_key LIMIT 1;
        END;
        $fn$
    """)
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_collection_view_create(uuid,text,jsonb,jsonb,jsonb,jsonb) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_collection_view_create(uuid,text,jsonb,jsonb,jsonb,jsonb) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_collection_view_list(
            p_type_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, type_id uuid, "key" text,
            filter_spec jsonb, sort_spec jsonb, projection_spec jsonb,
            pagination_spec jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.collection_view WHERE type_id = p_type_id ORDER BY "key" COLLATE "C"
        $fn$
    """)
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_collection_view_list(uuid) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_collection_view_list(uuid) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_collection_view_get(
            p_view_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, type_id uuid, "key" text,
            filter_spec jsonb, sort_spec jsonb, projection_spec jsonb,
            pagination_spec jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.collection_view WHERE id = p_view_id
        $fn$
    """)
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_collection_view_get(uuid) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_collection_view_get(uuid) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_collection_view_update(
            p_view_id uuid, p_filter jsonb, p_sort jsonb,
            p_projection jsonb, p_pagination jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, type_id uuid, "key" text,
            filter_spec jsonb, sort_spec jsonb, projection_spec jsonb,
            pagination_spec jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.collection_view SET
                filter_spec = COALESCE(p_filter, filter_spec),
                sort_spec = COALESCE(p_sort, sort_spec),
                projection_spec = COALESCE(p_projection, projection_spec),
                pagination_spec = COALESCE(p_pagination, pagination_spec),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = p_view_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT * FROM content.collection_view WHERE id = p_view_id;
        END;
        $fn$
    """)
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_collection_view_update(uuid,jsonb,jsonb,jsonb,jsonb) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_collection_view_update(uuid,jsonb,jsonb,jsonb,jsonb) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_collection_view_delete(
            p_view_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            DELETE FROM content.collection_view WHERE id = p_view_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
        END;
        $fn$
    """)
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_collection_view_delete(uuid) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_collection_view_delete(uuid) TO slaif_editor_runtime, slaif_control"
    )


def downgrade() -> None:
    for fn in (
        "slaif_collection_view_create(uuid,text,jsonb,jsonb,jsonb,jsonb)",
        "slaif_collection_view_list(uuid)",
        "slaif_collection_view_get(uuid)",
        "slaif_collection_view_update(uuid,jsonb,jsonb,jsonb,jsonb)",
        "slaif_collection_view_delete(uuid)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{fn} CASCADE")
