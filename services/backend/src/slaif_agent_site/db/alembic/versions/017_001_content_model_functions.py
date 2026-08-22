"""Create SECURITY DEFINER functions for content model CRUD.

Architecture reference: ARCHITECTURE-for-agents.md §9 (backend/domain
service contracts). All functions use ``SET search_path = pg_catalog``
to prevent search-path hijacking. Soft deletes preserve audit trails.
"""

# ruff: noqa: E501
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "017_001"
down_revision: str | Sequence[str] | None = "016_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_GRANT_EDITOR = "GRANT EXECUTE ON FUNCTION {fn} TO slaif_editor_runtime, slaif_control"
_REVOKE_PUBLIC = "REVOKE ALL ON FUNCTION {fn} FROM PUBLIC"


def _secure(fn: str) -> None:
    op.execute(_REVOKE_PUBLIC.format(fn=fn))
    op.execute(_GRANT_EDITOR.format(fn=fn))


def upgrade() -> None:
    # Content type create
    op.execute("""
        CREATE FUNCTION content.slaif_content_type_create(
            p_site_id uuid, p_key text, p_labels jsonb,
            p_slug_pattern text, p_settings jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, "key" text, labels jsonb,
            slug_pattern text, status text, definition_version integer,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            INSERT INTO content.content_type (site_id, "key", labels, slug_pattern, settings)
            VALUES (p_site_id, p_key, p_labels, p_slug_pattern, p_settings);
            RETURN QUERY SELECT * FROM content.content_type
            WHERE site_id = p_site_id AND "key" = p_key LIMIT 1;
        END;
        $fn$
    """)
    _secure('"content"."slaif_content_type_create"(uuid,text,jsonb,text,jsonb)')

    op.execute("""
        CREATE FUNCTION content.slaif_content_type_list(
            p_site_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, "key" text, labels jsonb,
            slug_pattern text, status text, definition_version integer,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.content_type
            WHERE site_id = p_site_id AND status != 'DELETED'
            ORDER BY "key" COLLATE "C"
        $fn$
    """)
    _secure('"content"."slaif_content_type_list"(uuid)')

    op.execute("""
        CREATE FUNCTION content.slaif_content_type_get(
            p_type_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, "key" text, labels jsonb,
            slug_pattern text, status text, definition_version integer,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.content_type WHERE id = p_type_id
        $fn$
    """)
    _secure('"content"."slaif_content_type_get"(uuid)')

    op.execute("""
        CREATE FUNCTION content.slaif_content_type_update(
            p_type_id uuid, p_labels jsonb, p_slug_pattern text, p_settings jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, "key" text, labels jsonb,
            slug_pattern text, status text, definition_version integer,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
            new_labels jsonb := COALESCE(p_labels, ct.labels);
            new_slug text := COALESCE(p_slug_pattern, ct.slug_pattern);
            new_settings jsonb := COALESCE(p_settings, ct.settings);
        BEGIN
            UPDATE content.content_type SET
                labels = COALESCE(p_labels, labels),
                slug_pattern = COALESCE(p_slug_pattern, slug_pattern),
                settings = COALESCE(p_settings, settings),
                definition_version = definition_version + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = p_type_id AND status != 'DELETED';
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT * FROM content.content_type WHERE id = p_type_id;
        END;
        $fn$
    """)
    _secure('"content"."slaif_content_type_update"(uuid,jsonb,text,jsonb)')

    op.execute("""
        CREATE FUNCTION content.slaif_content_type_delete(
            p_type_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.content_type SET status = 'DELETED', updated_at = CURRENT_TIMESTAMP
            WHERE id = p_type_id AND status != 'DELETED';
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
        END;
        $fn$
    """)
    _secure('"content"."slaif_content_type_delete"(uuid)')

    # Field definition create
    op.execute("""
        CREATE FUNCTION content.slaif_field_definition_create(
            p_type_id uuid, p_key text, p_label text, p_field_type text,
            p_required boolean, p_localized boolean, p_cardinality integer,
            p_position integer, p_validation jsonb, p_ui_options jsonb
        ) RETURNS TABLE (
            id uuid, type_id uuid, "key" text, label text, field_type text,
            required boolean, localized boolean, cardinality integer,
            "position" integer, validation jsonb, ui_options jsonb,
            definition_version integer, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            INSERT INTO content.field_definition
                (type_id, "key", label, field_type, required, localized,
                 cardinality, "position", validation, ui_options)
            VALUES (p_type_id, p_key, p_label, p_field_type, p_required,
                    p_localized, p_cardinality, p_position, p_validation, p_ui_options)
            RETURNING *;
        END;
        $fn$
    """)
    _secure(
        '"content"."slaif_field_definition_create"(uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb)'
    )

    op.execute("""
        CREATE FUNCTION content.slaif_field_definition_list(
            p_type_id uuid
        ) RETURNS TABLE (
            id uuid, type_id uuid, "key" text, label text, field_type text,
            required boolean, localized boolean, cardinality integer,
            "position" integer, validation jsonb, ui_options jsonb,
            definition_version integer, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.field_definition
            WHERE type_id = p_type_id
            ORDER BY "position", "key" COLLATE "C"
        $fn$
    """)
    _secure('"content"."slaif_field_definition_list"(uuid)')

    op.execute("""
        CREATE FUNCTION content.slaif_field_definition_get(
            p_field_id uuid
        ) RETURNS TABLE (
            id uuid, type_id uuid, "key" text, label text, field_type text,
            required boolean, localized boolean, cardinality integer,
            "position" integer, validation jsonb, ui_options jsonb,
            definition_version integer, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.field_definition WHERE id = p_field_id
        $fn$
    """)
    _secure('"content"."slaif_field_definition_get"(uuid)')

    op.execute("""
        CREATE FUNCTION content.slaif_field_definition_update(
            p_field_id uuid, p_label text, p_required boolean,
            p_localized boolean, p_cardinality integer, p_position integer,
            p_validation jsonb, p_ui_options jsonb
        ) RETURNS TABLE (
            id uuid, type_id uuid, "key" text, label text, field_type text,
            required boolean, localized boolean, cardinality integer,
            "position" integer, validation jsonb, ui_options jsonb,
            definition_version integer, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.field_definition SET
                label = COALESCE(p_label, label),
                required = COALESCE(p_required, required),
                localized = COALESCE(p_localized, localized),
                cardinality = COALESCE(p_cardinality, cardinality),
                "position" = COALESCE(p_position, "position"),
                validation = COALESCE(p_validation, validation),
                ui_options = COALESCE(p_ui_options, ui_options),
                definition_version = definition_version + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = p_field_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT * FROM content.field_definition WHERE id = p_field_id;
        END;
        $fn$
    """)
    _secure(
        '"content"."slaif_field_definition_update"(uuid,text,boolean,boolean,integer,integer,jsonb,jsonb)'
    )

    op.execute("""
        CREATE FUNCTION content.slaif_field_definition_delete(
            p_field_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            DELETE FROM content.field_definition WHERE id = p_field_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
        END;
        $fn$
    """)
    _secure('"content"."slaif_field_definition_delete"(uuid)')


def downgrade() -> None:
    for fn in (
        '"content"."slaif_content_type_create"(uuid,text,jsonb,text,jsonb)',
        '"content"."slaif_content_type_list"(uuid)',
        '"content"."slaif_content_type_get"(uuid)',
        '"content"."slaif_content_type_update"(uuid,jsonb,text,jsonb)',
        '"content"."slaif_content_type_delete"(uuid)',
        '"content"."slaif_field_definition_create"(uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb)',
        '"content"."slaif_field_definition_list"(uuid)',
        '"content"."slaif_field_definition_get"(uuid)',
        '"content"."slaif_field_definition_update"(uuid,text,boolean,boolean,integer,integer,jsonb,jsonb)',
        '"content"."slaif_field_definition_delete"(uuid)',
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {fn} CASCADE")
