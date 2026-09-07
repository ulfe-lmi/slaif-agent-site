# ruff: noqa: E501
"""Close dynamic page references in navigation and Render projection."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "057_001"
down_revision: str | Sequence[str] | None = "056_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_PAGE_RETURN = """
    id uuid, site_id uuid, slug text, title text, status text, locale text,
    parent_id uuid, route_template text, effective_route text,
    deleted_at timestamptz, row_version integer, created_at timestamptz,
    updated_at timestamptz
"""


def _page_target_helper_sql() -> str:
    return """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_page_target_validate(
            p_site_id uuid, p_page_id uuid, p_target_value text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE page_route text;
        BEGIN
            IF p_site_id IS NULL OR p_page_id IS NULL
               OR p_target_value IS NULL
               OR p_target_value IS DISTINCT FROM p_page_id::text
            THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM content.page p
                WHERE p.site_id=p_site_id AND p.id=p_page_id
                  AND p.deleted_at IS NULL AND p.route_template IS NULL
                  AND EXISTS (
                      SELECT 1 FROM content.site_locale l
                      WHERE l.site_id=p.site_id AND l.tag=p.locale AND l.enabled
                  )
            ) THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END IF;
            BEGIN
                page_route:=content.slaif_agent_page_effective_route(p_page_id);
            EXCEPTION WHEN OTHERS THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END;
            IF page_route IS NULL
               OR page_route !~ '^/[A-Za-z0-9._~/-]*$'
               OR page_route ~ '//|\\\\|%|\\.\\.'
            THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END IF;
        END;
        $fn$
    """


def _agent_navigation_validator_sql(*, enforce: bool) -> str:
    page_check = (
        """
            PERFORM content.slaif_navigation_page_target_validate(
                p_site_id,p_page_id,p_target_value);
        """
        if enforce
        else ""
    )
    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_agent_navigation_validate_target(
            p_site_id uuid,p_page_id uuid,p_target_kind text,p_target_value text,
            p_labels jsonb,p_locale text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record;
        BEGIN
            IF p_target_kind NOT IN ('PAGE','INTERNAL','EXTERNAL')
               OR p_target_value IS NULL OR octet_length(p_target_value)>2048
               OR p_target_value ~ '[[:cntrl:] ]'
            THEN RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003'; END IF;
            PERFORM content.slaif_agent_navigation_validate_labels(p_site_id,p_labels);
            IF p_target_kind='PAGE' THEN
                IF p_page_id IS NULL OR p_target_value<>p_page_id::text
                THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
{page_check}
                IF NOT content.slaif_agent_page_accessible(p_site_id,p_page_id)
                THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
            ELSIF p_page_id IS NOT NULL THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            ELSIF p_target_kind='INTERNAL' THEN
                IF NOT (p_target_value='/' OR p_target_value ~ '^/[a-z0-9][a-z0-9._~/-]*$')
                   OR p_target_value ~ '//|\\\\|\\.\\.'
                   OR p_target_value ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)'
                THEN RAISE EXCEPTION 'NAVIGATION_TARGET_UNSAFE' USING ERRCODE='P0003'; END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM content.page p
                    WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
                      AND p.route_template IS NULL
                      AND content.slaif_agent_page_accessible(p_site_id,p.id)
                      AND content.slaif_agent_page_effective_route(p.id)=p_target_value
                ) THEN RAISE EXCEPTION 'NAVIGATION_TARGET_UNSAFE' USING ERRCODE='P0003'; END IF;
            ELSE
                IF p_target_value !~ '^https://[^/@?#]+([/?#].*)?$'
                   OR p_target_value ~ '[[:cntrl:] ]'
                THEN RAISE EXCEPTION 'NAVIGATION_TARGET_UNSAFE' USING ERRCODE='P0003'; END IF;
            END IF;
            IF p_locale IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.site_locale l
                WHERE l.site_id=p_site_id AND l.tag=p_locale AND l.enabled
            ) THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            SELECT * INTO STRICT constraints
            FROM control.slaif_agent_resource_constraints(p_site_id);
            IF p_locale IS NOT NULL AND cardinality(constraints.allowed_locales)>0
               AND NOT p_locale=ANY(constraints.allowed_locales)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_LOCALE_DENIED' USING ERRCODE='P0007'; END IF;
            IF NOT EXISTS (SELECT 1 FROM jsonb_object_keys(coalesce(p_labels,'{{}}'::jsonb)))
               AND p_locale IS NULL THEN
                RAISE EXCEPTION 'NAVIGATION_LABEL_REQUIRED' USING ERRCODE='P0003';
            END IF;
        END;
        $fn$
    """


def _agent_page_update_sql(*, enforce: bool) -> str:
    dependency_check = (
        """
            IF p_route_template_set AND p_route_template='{slug}'
               AND EXISTS (
                   SELECT 1 FROM content.navigation_item n
                   WHERE n.site_id=p_site_id AND n.page_id=p_page_id
               ) THEN
                RAISE EXCEPTION 'PAGE_NAVIGATION_DEPENDENCY' USING ERRCODE='P0003';
            END IF;
        """
        if enforce
        else ""
    )
    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_agent_page_update(
            p_site_id uuid,p_page_id uuid,p_slug text,p_title text,p_status text,
            p_locale text,p_route_template text,p_route_template_set boolean,
            p_expected integer
        ) RETURNS TABLE(
{_PAGE_RETURN}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old_page record;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'page:write');
            IF p_slug IS NOT NULL OR p_locale IS NOT NULL OR p_route_template_set THEN
                PERFORM control.slaif_agent_require_capability(p_site_id,'route:write');
            END IF;
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text || chr(58) || p_site_id::text || chr(58) || 'page-structure',994));
            IF p_locale IS NOT NULL THEN
                PERFORM content.slaif_agent_page_ensure_locale(p_site_id,p_locale);
            END IF;
            IF p_expected IS NULL OR p_expected <= 0 THEN
                RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003';
            END IF;
            SELECT p.* INTO old_page FROM content.page p
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.deleted_at IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old_page.row_version <> p_expected THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            PERFORM content.slaif_agent_page_ensure_locale(p_site_id,old_page.locale);
{dependency_check}
            IF p_slug IS NULL AND p_title IS NULL AND p_status IS NULL AND p_locale IS NULL AND NOT p_route_template_set THEN
                RAISE EXCEPTION 'PAGE_UPDATE_EMPTY' USING ERRCODE='P0003';
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.page p SET
                slug=coalesce(p_slug,p.slug), title=coalesce(p_title,p.title),
                status=coalesce(p_status,p.status), locale=coalesce(p_locale,p.locale),
                route_template=CASE WHEN p_route_template_set THEN p_route_template ELSE p.route_template END,
                row_version=p.row_version+1, updated_at=now()
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_agent_page_validate_subtree(p_site_id,p_page_id);
            RETURN QUERY SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.route_template,content.slaif_agent_page_effective_route(p.id),
                p.deleted_at,p.row_version,p.created_at,p.updated_at
            FROM content.page p WHERE p.id=p_page_id AND p.site_id=p_site_id;
        END;
        $fn$;
    """


def _editor_navigation_sql(*, enforce: bool) -> str:
    create_check = (
        "            IF p_target_kind='PAGE' THEN\n"
        "                PERFORM content.slaif_navigation_page_target_validate(\n"
        "                    p_site_id,p_page_id,p_target_value);\n"
        "            END IF;\n"
        if enforce
        else ""
    )
    update_check = (
        "            IF target_page IS NOT NULL AND new_target_kind='PAGE' THEN\n"
        "                PERFORM content.slaif_navigation_page_target_validate(\n"
        "                    p_site_id,target_page,new_target_value);\n"
        "            END IF;\n"
        if enforce
        else ""
    )
    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_navigation_item_create(
            p_site_id uuid,p_navigation_id uuid,p_parent_id uuid,p_page_id uuid,
            p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,
            p_position integer
        ) RETURNS SETOF content.navigation_item
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE parent_nav uuid; created content.navigation_item;
            created_id uuid; desired_position integer; sibling_count integer;
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            IF NOT EXISTS (SELECT 1 FROM content.navigation n WHERE n.id=p_navigation_id AND n.site_id=p_site_id) THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF p_parent_id IS NOT NULL THEN
                SELECT i.navigation_id INTO parent_nav FROM content.navigation_item i
                WHERE i.id=p_parent_id AND i.site_id=p_site_id;
                IF parent_nav IS NULL OR parent_nav<>p_navigation_id THEN
                    RAISE EXCEPTION 'NAVIGATION_PARENT_INVALID' USING ERRCODE='P0003';
                END IF;
            END IF;
            IF p_target_kind='PAGE' AND (p_page_id IS NULL OR p_target_value<>p_page_id::text) THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_target_kind<>'PAGE' AND p_page_id IS NOT NULL THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_page_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.page p
                WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.deleted_at IS NULL
            ) THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END IF;
{create_check}            IF p_locale IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.site_locale l
                WHERE l.site_id=p_site_id AND l.tag=p_locale AND l.enabled
            ) THEN
                RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_target_kind NOT IN ('PAGE','INTERNAL','EXTERNAL')
               OR p_position NOT BETWEEN 0 AND 999
               OR jsonb_typeof(p_labels)<>'object' THEN
                RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003';
            END IF;
            PERFORM content.slaif_agent_navigation_validate_labels(p_site_id,p_labels);
            SELECT count(*)::integer INTO sibling_count
            FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.navigation_id=p_navigation_id
              AND i.parent_id IS NOT DISTINCT FROM p_parent_id;
            IF sibling_count>=1000 THEN
                RAISE EXCEPTION 'NAVIGATION_POSITION_LIMIT' USING ERRCODE='P0003';
            END IF;
            desired_position:=least(p_position,sibling_count);
            UPDATE content.navigation_item i SET position=i.position+1,
                row_version=i.row_version+1,updated_at=now()
            WHERE i.site_id=p_site_id AND i.navigation_id=p_navigation_id
              AND i.parent_id IS NOT DISTINCT FROM p_parent_id
              AND i.position>=desired_position;
            INSERT INTO content.navigation_item(
                id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,
                target_value,labels,locale,position
            ) VALUES (
                gen_random_uuid(),p_site_id,p_navigation_id,p_parent_id,
                coalesce(p_parent_id,'00000000-0000-0000-0000-000000000000'::uuid),
                p_page_id,p_target_kind,p_target_value,p_labels,p_locale,desired_position
            ) RETURNING id INTO created_id;
            SELECT i.* INTO created FROM content.navigation_item i WHERE i.id=created_id;
            RETURN NEXT created;
        END; $fn$

        CREATE OR REPLACE FUNCTION content.slaif_navigation_item_update(
            p_site_id uuid,p_id uuid,p_parent_id uuid,p_page_id uuid,
            p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,
            p_position integer,p_expected integer
        ) RETURNS SETOF content.navigation_item
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old content.navigation_item; parent_nav uuid;
            target_parent uuid; target_page uuid; new_target_kind text;
            new_target_value text; new_target_labels jsonb; new_target_locale text;
            cursor_id uuid; desired_position integer; sibling_count integer;
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT i.* INTO old FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.id=p_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            IF p_parent_id IS NOT NULL THEN
                SELECT i.navigation_id INTO parent_nav FROM content.navigation_item i
                WHERE i.site_id=p_site_id AND i.id=p_parent_id;
                IF parent_nav IS NULL OR parent_nav<>old.navigation_id OR p_parent_id=p_id THEN
                    RAISE EXCEPTION 'NAVIGATION_PARENT_INVALID' USING ERRCODE='P0003';
                END IF;
                cursor_id:=p_parent_id;
                LOOP
                    IF cursor_id=p_id THEN
                        RAISE EXCEPTION 'NAVIGATION_CYCLE' USING ERRCODE='P0003';
                    END IF;
                    SELECT i.parent_id INTO cursor_id FROM content.navigation_item i
                    WHERE i.site_id=p_site_id AND i.id=cursor_id;
                    EXIT WHEN cursor_id IS NULL;
                END LOOP;
            END IF;
            target_parent:=p_parent_id;
            target_page:=CASE WHEN p_target_kind IS NOT NULL AND p_target_kind<>'PAGE'
                THEN NULL ELSE coalesce(p_page_id,old.page_id) END;
            new_target_kind:=coalesce(p_target_kind,old.target_kind);
            new_target_value:=coalesce(p_target_value,old.target_value);
            new_target_labels:=coalesce(p_labels,old.labels);
            new_target_locale:=p_locale;
            IF new_target_kind='PAGE'
               AND (target_page IS NULL OR new_target_value<>target_page::text)
            THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
            IF new_target_kind<>'PAGE' AND target_page IS NOT NULL
            THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
            IF target_page IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.page p
                WHERE p.id=target_page AND p.site_id=p_site_id AND p.deleted_at IS NULL
            ) THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
{update_check}            IF new_target_locale IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.site_locale l
                WHERE l.site_id=p_site_id AND l.tag=new_target_locale AND l.enabled
            ) THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            IF new_target_kind NOT IN ('PAGE','INTERNAL','EXTERNAL')
               OR p_position IS NOT NULL AND p_position NOT BETWEEN 0 AND 999
               OR jsonb_typeof(new_target_labels)<>'object'
            THEN RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003'; END IF;
            PERFORM content.slaif_agent_navigation_validate_labels(p_site_id,new_target_labels);
            SELECT count(*)::integer INTO sibling_count
            FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.navigation_id=old.navigation_id
              AND i.parent_id IS NOT DISTINCT FROM target_parent AND i.id<>p_id;
            desired_position:=least(coalesce(p_position,old.position),sibling_count);
            UPDATE content.navigation_item i SET position=999
            WHERE i.site_id=p_site_id AND i.id=p_id;
            WITH ranked AS (
                SELECT i.id,(row_number() OVER (ORDER BY i.position,i.id)-1)::integer AS compact_position
                FROM content.navigation_item i
                WHERE i.site_id=p_site_id AND i.navigation_id=old.navigation_id
                  AND i.parent_id IS NOT DISTINCT FROM old.parent_id AND i.id<>p_id
            ) UPDATE content.navigation_item i SET position=ranked.compact_position,
                row_version=CASE WHEN i.position IS DISTINCT FROM ranked.compact_position
                    THEN i.row_version+1 ELSE i.row_version END,
                updated_at=CASE WHEN i.position IS DISTINCT FROM ranked.compact_position
                    THEN now() ELSE i.updated_at END
            FROM ranked WHERE i.id=ranked.id;
            WITH ranked AS (
                SELECT i.id,(row_number() OVER (ORDER BY i.position,i.id)-1)::integer AS compact_position
                FROM content.navigation_item i
                WHERE i.site_id=p_site_id AND i.navigation_id=old.navigation_id
                  AND i.parent_id IS NOT DISTINCT FROM target_parent AND i.id<>p_id
            ) UPDATE content.navigation_item i SET position=ranked.compact_position+1,
                row_version=i.row_version+1,updated_at=now()
            FROM ranked WHERE i.id=ranked.id
              AND ranked.compact_position>=desired_position;
            UPDATE content.navigation_item AS i SET
                parent_id=target_parent,
                parent_key=coalesce(target_parent,'00000000-0000-0000-0000-000000000000'::uuid),
                page_id=target_page,target_kind=new_target_kind,target_value=new_target_value,
                labels=new_target_labels,locale=new_target_locale,position=desired_position,
                row_version=i.row_version+1,updated_at=now()
            WHERE i.site_id=p_site_id AND i.id=p_id AND i.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            RETURN QUERY SELECT i.* FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.id=p_id;
        END; $fn$
    """


def _render_navigation_sql(*, enforce: bool) -> str:
    page_check = (
        """
                    BEGIN
                        PERFORM content.slaif_navigation_page_target_validate(
                            p_site_id,item.page_id,item.target_value);
                    EXCEPTION WHEN OTHERS THEN
                        RAISE EXCEPTION 'RENDER_NAVIGATION_PAGE_INVALID'
                            USING ERRCODE='P0003';
                    END;
        """
        if enforce
        else ""
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
{page_check}                    BEGIN
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


def _execute_editor_navigation(*, enforce: bool) -> None:
    sql = _editor_navigation_sql(enforce=enforce)
    marker = (
        "\n        CREATE OR REPLACE FUNCTION content.slaif_navigation_item_update("
    )
    create_sql, update_sql = sql.split(marker, maxsplit=1)
    op.execute(create_sql)
    op.execute(marker + update_sql)


def _drop_editor_navigation() -> None:
    for function in (
        "content.slaif_navigation_item_update(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer,integer)",
        "content.slaif_navigation_item_create(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function}")


def _secure() -> None:
    for function, signature in (
        (
            "content.slaif_navigation_page_target_validate",
            "uuid,uuid,text",
        ),
    ):
        op.execute(f"ALTER FUNCTION {function}({signature}) OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function}({signature}) FROM PUBLIC")


def upgrade() -> None:
    op.execute(_page_target_helper_sql())
    op.execute(_agent_navigation_validator_sql(enforce=True))
    op.execute(_agent_page_update_sql(enforce=True))
    _execute_editor_navigation(enforce=True)
    op.execute(_render_navigation_sql(enforce=True))
    _secure()


def downgrade() -> None:
    op.execute(_render_navigation_sql(enforce=False))
    _drop_editor_navigation()
    _execute_editor_navigation(enforce=False)
    for function in (
        "content.slaif_navigation_item_create(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer)",
        "content.slaif_navigation_item_update(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer,integer)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_editor_runtime")
    op.execute(_agent_page_update_sql(enforce=False))
    op.execute(_agent_navigation_validator_sql(enforce=False))
    op.execute(
        "DROP FUNCTION IF EXISTS content.slaif_navigation_page_target_validate(uuid,uuid,text)"
    )
