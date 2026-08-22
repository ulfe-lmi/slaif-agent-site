# ruff: noqa: E501
"""Create media asset table with CRUD functions."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "023_001"
down_revision: str | Sequence[str] | None = "022_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS content.media_asset (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL REFERENCES control.site(id),
            uploaded_by UUID REFERENCES control.user_account(id),
            filename TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            size_bytes BIGINT NOT NULL,
            content_hash TEXT NOT NULL,
            storage_key TEXT NOT NULL,
            alt_text TEXT NOT NULL DEFAULT '',
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_media_site_hash UNIQUE (site_id, content_hash)
        )
    """)

    op.execute("""
        CREATE FUNCTION content.slaif_media_create(
            p_site_id uuid, p_uploaded_by uuid, p_filename text,
            p_mime_type text, p_size_bytes bigint, p_content_hash text,
            p_storage_key text, p_alt_text text, p_metadata jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, uploaded_by uuid, filename text,
            mime_type text, size_bytes bigint, content_hash text,
            storage_key text, alt_text text, metadata jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            INSERT INTO content.media_asset
                (site_id, uploaded_by, filename, mime_type, size_bytes,
                 content_hash, storage_key, alt_text, metadata)
            VALUES (p_site_id, p_uploaded_by, p_filename, p_mime_type,
                    p_size_bytes, p_content_hash, p_storage_key, p_alt_text, p_metadata);
            RETURN QUERY SELECT * FROM content.media_asset
            WHERE site_id = p_site_id AND content_hash = p_content_hash LIMIT 1;
        END;
        $fn$
    """)
    op.execute("GRANT EXECUTE ON FUNCTION content.slaif_media_create(uuid,uuid,text,text,bigint,text,text,text,jsonb) TO slaif_editor_runtime, slaif_control")

    op.execute("""
        CREATE FUNCTION content.slaif_media_list(
            p_site_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, uploaded_by uuid, filename text,
            mime_type text, size_bytes bigint, content_hash text,
            storage_key text, alt_text text, metadata jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.media_asset WHERE site_id = p_site_id
            ORDER BY created_at DESC
        $fn$
    """)
    op.execute("GRANT EXECUTE ON FUNCTION content.slaif_media_list(uuid) TO slaif_editor_runtime, slaif_control")

    op.execute("""
        CREATE FUNCTION content.slaif_media_get(
            p_media_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, uploaded_by uuid, filename text,
            mime_type text, size_bytes bigint, content_hash text,
            storage_key text, alt_text text, metadata jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.media_asset WHERE id = p_media_id
        $fn$
    """)
    op.execute("GRANT EXECUTE ON FUNCTION content.slaif_media_get(uuid) TO slaif_editor_runtime, slaif_control")

    op.execute("""
        CREATE FUNCTION content.slaif_media_update(
            p_media_id uuid, p_alt_text text, p_metadata jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, uploaded_by uuid, filename text,
            mime_type text, size_bytes bigint, content_hash text,
            storage_key text, alt_text text, metadata jsonb,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.media_asset SET
                alt_text = COALESCE(p_alt_text, alt_text),
                metadata = COALESCE(p_metadata, metadata),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = p_media_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT * FROM content.media_asset WHERE id = p_media_id;
        END;
        $fn$
    """)
    op.execute("GRANT EXECUTE ON FUNCTION content.slaif_media_update(uuid,text,jsonb) TO slaif_editor_runtime, slaif_control")

    op.execute("""
        CREATE FUNCTION content.slaif_media_delete(
            p_media_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            DELETE FROM content.media_asset WHERE id = p_media_id;
        END;
        $fn$
    """)
    op.execute("GRANT EXECUTE ON FUNCTION content.slaif_media_delete(uuid) TO slaif_editor_runtime, slaif_control")


def downgrade() -> None:
    for fn in (
        "slaif_media_create(uuid,uuid,text,text,bigint,text,text,text,jsonb)",
        "slaif_media_list(uuid)",
        "slaif_media_get(uuid)",
        "slaif_media_update(uuid,text,jsonb)",
        "slaif_media_delete(uuid)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{fn} CASCADE")
    op.execute("""
        DO $$
        DECLARE obj record;
        BEGIN
          FOR obj IN
            SELECT c.relname, c.relkind FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace ns ON ns.oid = c.relnamespace
            WHERE ns.nspname = 'content' AND c.relname = 'media_asset'
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
