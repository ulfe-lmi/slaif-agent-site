# ruff: noqa: E501
"""Add the narrow Render route and navigation projection surface."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "052_001"
down_revision: str | Sequence[str] | None = "051_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_PAGE_SIGNATURE = "uuid,text,text,text[]"
_NAVIGATION_SIGNATURE = "uuid,text,text[]"


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION content.slaif_render_page_resolve(
            p_site_id uuid, p_route text, p_locale text, p_statuses text[]
        ) RETURNS TABLE(
            id uuid, site_id uuid, slug text, title text, status text,
            locale text, parent_id uuid, route_template text,
            effective_route text, row_version integer,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE candidate content.page; candidate_route text; found boolean:=false;
        BEGIN
            IF p_site_id IS NULL OR p_locale IS NULL OR p_route IS NULL
               OR p_route !~ '^/[a-z0-9._~/-]*$'
               OR p_route ~ '//|\\\\|%|\\.\\.'
               OR p_statuses IS NULL OR cardinality(p_statuses)=0
               OR EXISTS (
                   SELECT 1 FROM unnest(p_statuses) AS selected(status)
                   WHERE selected.status NOT IN ('PUBLISHED','DRAFT')
               ) THEN
                RETURN;
            END IF;
            FOR candidate IN
                SELECT p.* FROM content.page AS p
                WHERE p.site_id=p_site_id AND p.locale=p_locale
                  AND p.deleted_at IS NULL AND p.status=ANY(p_statuses)
                  AND p.route_template IS DISTINCT FROM '{slug}'
            LOOP
                BEGIN
                    candidate_route:=content.slaif_agent_page_effective_route(candidate.id);
                EXCEPTION WHEN OTHERS THEN
                    -- A corrupt or dynamic hierarchy is not routable. It must
                    -- not make unrelated static pages unavailable.
                    CONTINUE;
                END;
                IF lower(candidate_route)=lower(p_route) THEN
                    IF found THEN
                        RAISE EXCEPTION 'RENDER_ROUTE_AMBIGUOUS' USING ERRCODE='P0003';
                    END IF;
                    found:=true;
                    id:=candidate.id; site_id:=candidate.site_id;
                    slug:=candidate.slug; title:=candidate.title;
                    status:=candidate.status; locale:=candidate.locale;
                    parent_id:=candidate.parent_id;
                    route_template:=candidate.route_template;
                    effective_route:=candidate_route;
                    row_version:=candidate.row_version;
                    created_at:=candidate.created_at;
                    updated_at:=candidate.updated_at;
                    RETURN NEXT;
                END IF;
            END LOOP;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_render_navigation_items(
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
                        item_target:=content.slaif_agent_page_effective_route(page_row.id);
                    EXCEPTION WHEN OTHERS THEN
                        RAISE EXCEPTION 'RENDER_NAVIGATION_PAGE_INVALID'
                            USING ERRCODE='P0003';
                    END;
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
    )
    for function, signature in (
        ("content.slaif_render_page_resolve", _PAGE_SIGNATURE),
        ("content.slaif_render_navigation_items", _NAVIGATION_SIGNATURE),
    ):
        op.execute(f"ALTER FUNCTION {function}({signature}) OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function}({signature}) FROM PUBLIC")
        op.execute(
            f"GRANT EXECUTE ON FUNCTION {function}({signature}) "
            "TO slaif_public_reader, slaif_preview_reader"
        )


def downgrade() -> None:
    for function, signature in (
        ("content.slaif_render_navigation_items", _NAVIGATION_SIGNATURE),
        ("content.slaif_render_page_resolve", _PAGE_SIGNATURE),
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function}({signature}) CASCADE")
