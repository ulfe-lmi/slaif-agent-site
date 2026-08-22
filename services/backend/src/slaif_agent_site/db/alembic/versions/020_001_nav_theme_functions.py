# ruff: noqa: E501
"""Create navigation and theme tables with CRUD functions."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "020_001"
down_revision: str | Sequence[str] | None = "019_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS content.navigation (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL REFERENCES control.site(id),
            "key" TEXT NOT NULL,
            label TEXT NOT NULL,
            settings JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_navigation_site_key UNIQUE (site_id, "key")
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS content.theme (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL REFERENCES control.site(id) UNIQUE,
            palette JSONB NOT NULL DEFAULT '{}',
            typography JSONB NOT NULL DEFAULT '{}',
            layout JSONB NOT NULL DEFAULT '{}',
            shape JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # Navigation CRUD
    op.execute("""
        CREATE FUNCTION content.slaif_navigation_create(
            p_site_id uuid, p_key text, p_label text, p_settings jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, "key" text, label text,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            INSERT INTO content.navigation (site_id, "key", label, settings)
            VALUES (p_site_id, p_key, p_label, p_settings);
            RETURN QUERY SELECT * FROM content.navigation WHERE site_id = p_site_id AND "key" = p_key LIMIT 1;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_navigation_create(uuid,text,text,jsonb) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_navigation_list(
            p_site_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, "key" text, label text,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.navigation WHERE site_id = p_site_id ORDER BY "key" COLLATE "C"
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_navigation_list(uuid) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_navigation_get(
            p_nav_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, "key" text, label text,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.navigation WHERE id = p_nav_id
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_navigation_get(uuid) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_navigation_update(
            p_nav_id uuid, p_label text, p_settings jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, "key" text, label text,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.navigation SET
                label = COALESCE(p_label, label),
                settings = COALESCE(p_settings, settings),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = p_nav_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT * FROM content.navigation WHERE id = p_nav_id;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_navigation_update(uuid,text,jsonb) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_navigation_delete(
            p_nav_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            DELETE FROM content.navigation WHERE id = p_nav_id;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_navigation_delete(uuid) TO slaif_editor_runtime, slaif_control"
    )

    # Theme get/update (singleton per site)
    op.execute("""
        CREATE FUNCTION content.slaif_theme_get(
            p_site_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid,
            palette jsonb, typography jsonb,
            layout jsonb, shape jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
        BEGIN
            INSERT INTO content.theme (site_id) VALUES (p_site_id)
            ON CONFLICT (site_id) DO NOTHING;
            RETURN QUERY SELECT * FROM content.theme WHERE site_id = p_site_id LIMIT 1;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_theme_get(uuid) TO slaif_editor_runtime, slaif_control"
    )

    op.execute("""
        CREATE FUNCTION content.slaif_theme_update(
            p_site_id uuid, p_palette jsonb, p_typography jsonb,
            p_layout jsonb, p_shape jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid,
            palette jsonb, typography jsonb,
            layout jsonb, shape jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM content.slaif_theme_get(p_site_id);
            UPDATE content.theme SET
                palette = COALESCE(p_palette, palette),
                typography = COALESCE(p_typography, typography),
                layout = COALESCE(p_layout, layout),
                shape = COALESCE(p_shape, shape),
                updated_at = CURRENT_TIMESTAMP
            WHERE site_id = p_site_id;
            RETURN QUERY SELECT * FROM content.theme WHERE site_id = p_site_id LIMIT 1;
        END;
        $fn$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_theme_update(uuid,jsonb,jsonb,jsonb,jsonb) TO slaif_editor_runtime, slaif_control"
    )


def downgrade() -> None:
    for fn in (
        "slaif_navigation_create(uuid,text,text,jsonb)",
        "slaif_navigation_list(uuid)",
        "slaif_navigation_get(uuid)",
        "slaif_navigation_update(uuid,text,jsonb)",
        "slaif_navigation_delete(uuid)",
        "slaif_theme_get(uuid)",
        "slaif_theme_update(uuid,jsonb,jsonb,jsonb,jsonb)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{fn} CASCADE")
    op.execute("DROP TABLE IF EXISTS content.theme CASCADE")
    op.execute("DROP TABLE IF EXISTS content.navigation CASCADE")
