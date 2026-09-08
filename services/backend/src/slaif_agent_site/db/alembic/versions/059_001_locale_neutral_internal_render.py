# ruff: noqa: E501
"""Correct locale-neutral fixed INTERNAL Render target resolution."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "059_001"
down_revision: str | Sequence[str] | None = "058_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _render_internal_target_exists_sql(*, locale_neutral: bool) -> str:
    locale_guard = "" if locale_neutral else " OR p_locale IS NULL"
    locale_filter = "" if locale_neutral else " AND p.locale=p_locale"
    reserved_guard = (
        "\n               OR p_target_value ~ "
        "'^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)'"
        if locale_neutral
        else ""
    )
    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_render_internal_target_exists(
            p_site_id uuid, p_target_value text, p_locale text, p_statuses text[]
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE page_row record; page_route text; found boolean:=false;
        BEGIN
            IF p_site_id IS NULL OR p_target_value IS NULL{locale_guard}
               OR p_statuses IS NULL OR cardinality(p_statuses)=0
               OR EXISTS (
                   SELECT 1 FROM unnest(p_statuses) AS selected(status)
                   WHERE selected.status NOT IN ('PUBLISHED','DRAFT')
               )
               OR NOT (p_target_value='/' OR p_target_value ~ '^/[A-Za-z0-9][A-Za-z0-9._~/-]*$')
               OR p_target_value ~ '//|\\\\|\\.\\.'{reserved_guard}
            THEN RETURN false; END IF;
            FOR page_row IN
                SELECT p.id FROM content.page p
                WHERE p.site_id=p_site_id{locale_filter}
                  AND p.deleted_at IS NULL AND p.status=ANY(p_statuses)
                  AND p.route_template IS NULL
                  AND EXISTS (
                      SELECT 1 FROM content.site_locale l
                      WHERE l.site_id=p.site_id AND l.tag=p.locale AND l.enabled
                  )
            LOOP
                BEGIN
                    page_route:=content.slaif_agent_page_effective_route(page_row.id);
                EXCEPTION WHEN OTHERS THEN
                    CONTINUE;
                END;
                IF page_route=p_target_value THEN
                    IF found THEN RETURN false; END IF;
                    found:=true;
                END IF;
            END LOOP;
            RETURN found;
        END;
        $fn$
    """


def _render_navigation_sql(*, locale_neutral: bool) -> str:
    target_locale = (
        "item.locale" if locale_neutral else "coalesce(item.locale,p_locale)"
    )
    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_render_navigation_items(
            p_site_id uuid, p_locale text, p_statuses text[]
        ) RETURNS TABLE(
            id uuid, site_id uuid, navigation_id uuid, parent_id uuid,
            page_id uuid, target_kind text, target_value text,
            labels jsonb, locale text, "position" integer,
            resolved_target text
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE item content.navigation_item; page_row content.page;
            item_target text;
        BEGIN
            IF p_site_id IS NULL OR p_locale IS NULL OR p_statuses IS NULL
               OR cardinality(p_statuses)=0
               OR EXISTS (
                   SELECT 1 FROM unnest(p_statuses) AS selected(status)
                   WHERE selected.status NOT IN ('PUBLISHED','DRAFT')
               ) THEN
                RETURN;
            END IF;
            FOR item IN
                SELECT i.* FROM content.navigation_item AS i
                WHERE i.site_id=p_site_id
            LOOP
                item_target:=item.target_value;
                IF item.target_kind='PAGE' THEN
                    IF item.page_id IS NULL
                       OR item.target_value IS DISTINCT FROM item.page_id::text THEN
                        RAISE EXCEPTION 'RENDER_NAVIGATION_PAGE_INVALID'
                            USING ERRCODE='P0003';
                    END IF;
                    SELECT p.* INTO page_row FROM content.page AS p
                    WHERE p.id=item.page_id AND p.site_id=p_site_id
                      AND p.deleted_at IS NULL AND p.status=ANY(p_statuses)
                      AND EXISTS (
                          SELECT 1 FROM content.site_locale AS l
                          WHERE l.site_id=p.site_id AND l.tag=p.locale AND l.enabled
                      );
                    IF NOT FOUND THEN
                        RAISE EXCEPTION 'RENDER_NAVIGATION_PAGE_INVALID'
                            USING ERRCODE='P0003';
                    END IF;
                    BEGIN
                        PERFORM content.slaif_navigation_page_target_validate(
                            p_site_id,item.page_id,item.target_value);
                        item_target:=content.slaif_agent_page_effective_route(page_row.id);
                    EXCEPTION WHEN OTHERS THEN
                        RAISE EXCEPTION 'RENDER_NAVIGATION_PAGE_INVALID'
                            USING ERRCODE='P0003';
                    END;
                ELSIF item.target_kind='INTERNAL' THEN
                    IF item.page_id IS NOT NULL
                       OR NOT content.slaif_render_internal_target_exists(
                           p_site_id,item.target_value,{target_locale},p_statuses)
                    THEN
                        RAISE EXCEPTION 'RENDER_NAVIGATION_TARGET_INVALID'
                            USING ERRCODE='P0003';
                    END IF;
                ELSIF item.target_kind NOT IN ('INTERNAL','EXTERNAL')
                   OR item.page_id IS NOT NULL THEN
                    RAISE EXCEPTION 'RENDER_NAVIGATION_TARGET_INVALID'
                        USING ERRCODE='P0003';
                END IF;
                id:=item.id; site_id:=item.site_id;
                navigation_id:=item.navigation_id; parent_id:=item.parent_id;
                page_id:=item.page_id; target_kind:=item.target_kind;
                target_value:=item.target_value; labels:=item.labels;
                locale:=item.locale; "position":=item."position";
                resolved_target:=item_target;
                RETURN NEXT;
            END LOOP;
        END;
        $fn$
    """


def upgrade() -> None:
    op.execute(_render_internal_target_exists_sql(locale_neutral=True))
    op.execute(_render_navigation_sql(locale_neutral=True))


def downgrade() -> None:
    op.execute(_render_internal_target_exists_sql(locale_neutral=False))
    op.execute(_render_navigation_sql(locale_neutral=False))
