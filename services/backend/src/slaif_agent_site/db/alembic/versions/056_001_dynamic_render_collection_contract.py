# ruff: noqa: E501
"""Add bounded dynamic Render routes and localized collection projections."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "056_001"
down_revision: str | Sequence[str] | None = "055_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PAGE_SIGNATURE = "uuid,text,text,text[]"
_QUERY_SIGNATURE = "uuid,jsonb,jsonb,jsonb,jsonb"


def _dynamic_page_resolver() -> str:
    return """
        CREATE OR REPLACE FUNCTION content.slaif_render_page_resolve(
            p_site_id uuid, p_route text, p_locale text, p_statuses text[]
        ) RETURNS TABLE(
            id uuid, site_id uuid, slug text, title text, status text,
            locale text, parent_id uuid, route_template text,
            effective_route text, row_version integer,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE candidate content.page; candidate_route text;
            found boolean:=false; dynamic_prefix text; dynamic_slug text;
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

            -- Exact static routes always win over a dynamic page.
            FOR candidate IN
                SELECT p.* FROM content.page AS p
                WHERE p.site_id=p_site_id AND p.locale=p_locale
                  AND p.deleted_at IS NULL AND p.status=ANY(p_statuses)
                  AND p.route_template IS DISTINCT FROM '{slug}'
            LOOP
                BEGIN
                    candidate_route:=content.slaif_agent_page_effective_route(candidate.id);
                EXCEPTION WHEN OTHERS THEN
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
                END IF;
            END LOOP;
            FOR candidate IN
                SELECT p.* FROM content.page AS p
                WHERE p.site_id=p_site_id AND p.locale=p_locale
                  AND p.deleted_at IS NULL AND p.status=ANY(p_statuses)
                  AND p.route_template='{slug}'
            LOOP
                BEGIN
                    candidate_route:=content.slaif_agent_page_effective_route(candidate.id);
                EXCEPTION WHEN OTHERS THEN
                    -- A corrupt dynamic hierarchy is unroutable and must not
                    -- make an unrelated static route unavailable.
                    CONTINUE;
                END;
                IF right(candidate_route,6) <> '{slug}' THEN
                    RAISE EXCEPTION 'RENDER_ROUTE_INVALID' USING ERRCODE='P0003';
                END IF;
                dynamic_prefix:=left(candidate_route,length(candidate_route)-6);
                IF right(dynamic_prefix,1) <> '/' THEN
                    RAISE EXCEPTION 'RENDER_ROUTE_INVALID' USING ERRCODE='P0003';
                END IF;
                IF left(lower(p_route),length(dynamic_prefix))
                       = lower(dynamic_prefix)
                THEN
                    dynamic_slug:=substr(p_route,length(dynamic_prefix)+1);
                    IF dynamic_slug ~ '^[a-z0-9][a-z0-9._~-]{0,254}$'
                       AND position('/' in dynamic_slug)=0
                    THEN
                        IF found THEN
                            RAISE EXCEPTION 'RENDER_ROUTE_AMBIGUOUS'
                                USING ERRCODE='P0003';
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
                    END IF;
                END IF;
            END LOOP;
            IF found THEN RETURN NEXT; END IF;
        END;
        $fn$
    """


def _static_page_resolver() -> str:
    return """
        CREATE OR REPLACE FUNCTION content.slaif_render_page_resolve(
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
                EXCEPTION WHEN OTHERS THEN CONTINUE;
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


def upgrade() -> None:
    op.execute(
        "ALTER FUNCTION content.slaif_agent_collection_view_query_validate("
        "uuid,jsonb,jsonb,jsonb,jsonb) RENAME TO "
        "slaif_agent_collection_view_query_validate_base_056"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_collection_view_query_validate(
            p_type_id uuid,p_filter jsonb,p_sort jsonb,p_projection jsonb,
            p_pagination jsonb
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE name text; field record; filtered_projection jsonb;
            serialized text; projection jsonb;
        BEGIN
            IF jsonb_typeof(p_filter)<>'object'
               OR jsonb_typeof(p_sort)<>'object'
               OR jsonb_typeof(p_projection)<>'object'
               OR jsonb_typeof(p_pagination)<>'object'
            THEN
                RAISE EXCEPTION 'QUERY_INVALID' USING ERRCODE='P0003';
            END IF;
            serialized := jsonb_build_array(
                p_filter,p_sort,p_projection,p_pagination
            )::text;
            IF octet_length(serialized)>16384
               OR serialized ~* '(;|--|/\\*|\\*/|<script|javascript:|__proto__|constructor|prototype)'
            THEN
                RAISE EXCEPTION 'QUERY_INVALID' USING ERRCODE='P0003';
            END IF;
            IF EXISTS (
                WITH RECURSIVE nodes(value,depth) AS (
                    SELECT jsonb_build_array(
                        p_filter,p_sort,p_projection,p_pagination
                    ),0
                    UNION ALL
                    SELECT child.value,n.depth+1
                    FROM nodes n
                    CROSS JOIN LATERAL (
                        SELECT a.value
                        FROM jsonb_array_elements(
                            CASE WHEN jsonb_typeof(n.value)='array'
                                 THEN n.value ELSE '[]'::jsonb END
                        ) a
                        UNION ALL
                        SELECT e.value
                        FROM jsonb_each(
                            CASE WHEN jsonb_typeof(n.value)='object'
                                 THEN n.value ELSE '{}'::jsonb END
                        ) e
                    ) child
                )
                SELECT 1 FROM nodes WHERE depth>4
            ) THEN
                RAISE EXCEPTION 'QUERY_DEPTH' USING ERRCODE='P0003';
            END IF;
            IF (
                WITH RECURSIVE nodes(value) AS (
                    SELECT jsonb_build_array(
                        p_filter,p_sort,p_projection,p_pagination
                    )
                    UNION ALL
                    SELECT child.value
                    FROM nodes n
                    CROSS JOIN LATERAL (
                        SELECT a.value
                        FROM jsonb_array_elements(
                            CASE WHEN jsonb_typeof(n.value)='array'
                                 THEN n.value ELSE '[]'::jsonb END
                        ) a
                        UNION ALL
                        SELECT e.value
                        FROM jsonb_each(
                            CASE WHEN jsonb_typeof(n.value)='object'
                                 THEN n.value ELSE '{}'::jsonb END
                        ) e
                    ) child
                )
                SELECT count(*) FROM nodes
            ) > 256 THEN
                RAISE EXCEPTION 'QUERY_NODES' USING ERRCODE='P0003';
            END IF;
            IF jsonb_typeof(p_projection)='object'
               AND jsonb_typeof(p_projection->'fields')='array'
            THEN
                IF EXISTS (
                    SELECT 1 FROM jsonb_object_keys(p_projection) key
                    WHERE key <> 'fields'
                ) THEN
                    RAISE EXCEPTION 'QUERY_PROJECTION' USING ERRCODE='P0003';
                END IF;
                projection := p_projection->'fields';
                IF jsonb_array_length(projection)>16
                   OR EXISTS (
                       SELECT 1 FROM jsonb_array_elements(projection) value
                       WHERE jsonb_typeof(value)<>'string'
                   )
                THEN
                    RAISE EXCEPTION 'QUERY_PROJECTION' USING ERRCODE='P0003';
                END IF;
                IF EXISTS (
                    SELECT value FROM jsonb_array_elements(projection)
                    GROUP BY value HAVING count(*)>1
                ) THEN
                    RAISE EXCEPTION 'QUERY_PROJECTION' USING ERRCODE='P0003';
                END IF;
                FOR name IN
                    SELECT value #>> '{}' FROM jsonb_array_elements(projection)
                LOOP
                    SELECT f.* INTO field FROM content.field_definition f
                    WHERE f.type_id=p_type_id AND f."key"=name;
                    IF NOT FOUND OR name IN ('id','site_id','type_id','slug','status','values')
                    THEN
                        RAISE EXCEPTION 'QUERY_PROJECTION_FIELD' USING ERRCODE='P0003';
                    END IF;
                    IF field.localized IS TRUE THEN CONTINUE; END IF;
                END LOOP;
                SELECT jsonb_build_object(
                    'fields', coalesce(jsonb_agg(value), '[]'::jsonb)
                ) INTO filtered_projection
                FROM jsonb_array_elements(projection)
                WHERE NOT EXISTS (
                    SELECT 1 FROM content.field_definition f
                    WHERE f.type_id=p_type_id AND f."key"=value #>> '{}'
                      AND f.localized
                );
                PERFORM content.slaif_agent_collection_view_query_validate_base_056(
                    p_type_id,p_filter,p_sort,filtered_projection,p_pagination
                );
                RETURN;
            END IF;
            PERFORM content.slaif_agent_collection_view_query_validate_base_056(
                p_type_id,p_filter,p_sort,p_projection,p_pagination
            );
        END; $fn$
        """
    )
    op.execute(
        "ALTER FUNCTION content.slaif_agent_collection_view_query_validate("
        f"{_QUERY_SIGNATURE}) OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_agent_collection_view_query_validate("
        f"{_QUERY_SIGNATURE}) FROM PUBLIC, slaif_agent_runtime"
    )
    op.execute(_dynamic_page_resolver())
    op.execute(
        f"ALTER FUNCTION content.slaif_render_page_resolve({_PAGE_SIGNATURE}) "
        "OWNER TO slaif_owner"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION content.slaif_render_page_resolve({_PAGE_SIGNATURE}) "
        "FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION content.slaif_render_page_resolve({_PAGE_SIGNATURE}) "
        "TO slaif_public_reader, slaif_preview_reader"
    )


def downgrade() -> None:
    op.execute(
        f"DROP FUNCTION IF EXISTS content.slaif_render_page_resolve({_PAGE_SIGNATURE})"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS content.slaif_agent_collection_view_query_validate("
        f"{_QUERY_SIGNATURE})"
    )
    op.execute(
        "ALTER FUNCTION content.slaif_agent_collection_view_query_validate_base_056("
        f"{_QUERY_SIGNATURE}) RENAME TO slaif_agent_collection_view_query_validate"
    )
    op.execute(_static_page_resolver())
    op.execute(
        f"ALTER FUNCTION content.slaif_render_page_resolve({_PAGE_SIGNATURE}) "
        "OWNER TO slaif_owner"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION content.slaif_render_page_resolve({_PAGE_SIGNATURE}) "
        "FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION content.slaif_render_page_resolve({_PAGE_SIGNATURE}) "
        "TO slaif_public_reader, slaif_preview_reader"
    )
