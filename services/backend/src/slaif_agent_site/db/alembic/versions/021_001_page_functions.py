# ruff: noqa: E501
"""Create page table with CRUD functions."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "021_001"
down_revision: str | Sequence[str] | None = "020_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS content.page (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL REFERENCES control.site(id),
            slug TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'DRAFT',
            locale TEXT NOT NULL DEFAULT 'en',
            parent_id UUID REFERENCES content.page(id),
            row_version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_page_site_locale_slug UNIQUE (site_id, locale, slug)
        )
    """)

    op.execute("""
        CREATE FUNCTION content.slaif_page_create(
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
            RETURN QUERY SELECT * FROM content.page
            WHERE site_id = p_site_id AND locale = p_locale AND slug = p_slug LIMIT 1;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_page_create(uuid,text,text,text,text) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_page_list(
            p_site_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text,
            status text, locale text, parent_id uuid,
            row_version integer, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.page WHERE site_id = p_site_id ORDER BY slug COLLATE "C"
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_page_list(uuid) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_page_get(
            p_page_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text,
            status text, locale text, parent_id uuid,
            row_version integer, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.page WHERE id = p_page_id
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_page_get(uuid) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_page_update(
            p_page_id uuid, p_slug text, p_title text,
            p_status text, p_expected_row_version integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text,
            status text, locale text, parent_id uuid,
            row_version integer, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.page SET
                slug = COALESCE(p_slug, slug),
                title = COALESCE(p_title, title),
                status = COALESCE(p_status, status),
                row_version = row_version + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = p_page_id
              AND (p_expected_row_version IS NULL OR row_version = p_expected_row_version);
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT * FROM content.page WHERE id = p_page_id;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_page_update(uuid,text,text,text,integer) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_page_delete(
            p_page_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            DELETE FROM content.page WHERE id = p_page_id;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_page_delete(uuid) TO slaif_editor_runtime, slaif_control"
    )


def downgrade() -> None:
    for fn in (
        "slaif_page_create(uuid,text,text,text,text)",
        "slaif_page_list(uuid)",
        "slaif_page_get(uuid)",
        "slaif_page_update(uuid,text,text,text,integer)",
        "slaif_page_delete(uuid)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{fn} CASCADE")
    op.execute("""
        DO $$
        DECLARE obj record;
        BEGIN
          FOR obj IN
            SELECT c.relname, c.relkind FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace ns ON ns.oid = c.relnamespace
            WHERE ns.nspname = 'content' AND c.relname = 'page'
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
