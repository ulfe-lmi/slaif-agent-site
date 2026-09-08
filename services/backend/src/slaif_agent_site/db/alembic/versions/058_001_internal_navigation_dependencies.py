# ruff: noqa: E501
"""Keep fixed INTERNAL navigation targets coherent with page routes."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "058_001"
down_revision: str | Sequence[str] | None = "057_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_AGENT_APPLY_SIGNATURE = (
    "uuid,uuid,uuid,uuid,uuid,text,text,jsonb,text,uuid,uuid,integer,boolean"
)
_AGENT_UPDATE_SIGNATURE = "uuid,uuid,uuid,uuid,text,text,jsonb,text,integer"
_PAGE_VALIDATE_SIGNATURE = "uuid,uuid"
_PAGE_DELETE_SIGNATURE = "uuid,uuid,integer"
_EDITOR_CREATE_SIGNATURE = "uuid,uuid,uuid,uuid,text,text,jsonb,text,integer"
_EDITOR_UPDATE_SIGNATURE = "uuid,uuid,uuid,uuid,text,text,jsonb,text,integer,integer"
_PAGE_RETURN = """
    id uuid, site_id uuid, slug text, title text, status text, locale text,
    parent_id uuid, route_template text, effective_route text,
    deleted_at timestamptz, row_version integer, created_at timestamptz,
    updated_at timestamptz
"""
_ITEM_RETURN = """
    id uuid, site_id uuid, navigation_id uuid, parent_id uuid, page_id uuid,
    target_kind text, target_value text, labels jsonb, locale text,
    "position" integer, row_version integer, created_at timestamptz,
    updated_at timestamptz
"""


def _internal_route_helpers_sql() -> str:
    return """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_internal_target_exists(
            p_site_id uuid, p_target_value text
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE page_row record; page_route text;
        BEGIN
            IF p_site_id IS NULL OR p_target_value IS NULL
               OR NOT (p_target_value='/' OR p_target_value ~ '^/[A-Za-z0-9][A-Za-z0-9._~/-]*$')
               OR p_target_value ~ '//|\\\\|\\.\\.'
               OR p_target_value ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)'
            THEN RETURN false; END IF;
            FOR page_row IN
                SELECT p.id FROM content.page p
                WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
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
                IF page_route=p_target_value THEN RETURN true; END IF;
            END LOOP;
            RETURN false;
        END;
        $fn$

        CREATE OR REPLACE FUNCTION content.slaif_navigation_internal_target_validate(
            p_site_id uuid, p_target_value text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            IF NOT content.slaif_navigation_internal_target_exists(
                p_site_id,p_target_value
            ) THEN
                RAISE EXCEPTION 'NAVIGATION_TARGET_UNSAFE' USING ERRCODE='P0003';
            END IF;
        END;
        $fn$

        CREATE OR REPLACE FUNCTION content.slaif_navigation_validate_internal_targets(
            p_site_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE item record;
        BEGIN
            FOR item IN
                SELECT i.target_value FROM content.navigation_item i
                WHERE i.site_id=p_site_id AND i.target_kind='INTERNAL'
            LOOP
                PERFORM content.slaif_navigation_internal_target_validate(
                    p_site_id,item.target_value
                );
            END LOOP;
        END;
        $fn$

        CREATE OR REPLACE FUNCTION content.slaif_render_internal_target_exists(
            p_site_id uuid, p_target_value text, p_locale text, p_statuses text[]
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE page_row record; page_route text; found boolean:=false;
        BEGIN
            IF p_site_id IS NULL OR p_target_value IS NULL OR p_locale IS NULL
               OR p_statuses IS NULL OR cardinality(p_statuses)=0
               OR EXISTS (
                   SELECT 1 FROM unnest(p_statuses) AS selected(status)
                   WHERE selected.status NOT IN ('PUBLISHED','DRAFT')
               )
               OR NOT (p_target_value='/' OR p_target_value ~ '^/[A-Za-z0-9][A-Za-z0-9._~/-]*$')
               OR p_target_value ~ '//|\\\\|\\.\\.'
            THEN RETURN false; END IF;
            FOR page_row IN
                SELECT p.id FROM content.page p
                WHERE p.site_id=p_site_id AND p.locale=p_locale
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


def _locale_route_sql(*, restored: bool) -> str:
    if restored:
        return """
            CREATE OR REPLACE FUNCTION content.slaif_locale_route_exists(
                p_site_id uuid, p_target text
            ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
            SET search_path=pg_catalog AS $fn$
            DECLARE page_row record; page_route text;
            BEGIN
                FOR page_row IN
                    SELECT p.id FROM content.page p
                    WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
                      AND p.route_template IS NULL
                LOOP
                    BEGIN
                        page_route:=content.slaif_agent_page_effective_route(page_row.id);
                    EXCEPTION WHEN SQLSTATE 'P0002' THEN
                        CONTINUE;
                    END;
                    IF page_route=p_target THEN RETURN true; END IF;
                END LOOP;
                RETURN false;
            END;
            $fn$
        """
    return """
        CREATE OR REPLACE FUNCTION content.slaif_locale_route_exists(
            p_site_id uuid, p_target text
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT content.slaif_navigation_internal_target_exists(
                p_site_id,p_target
            )
        $fn$
    """


def _agent_target_sql(*, restored: bool) -> str:
    if restored:
        internal_check = """
                IF NOT EXISTS (
                    SELECT 1 FROM content.page p
                    WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
                      AND p.route_template IS NULL
                      AND content.slaif_agent_page_accessible(p_site_id,p.id)
                      AND content.slaif_agent_page_effective_route(p.id)=p_target_value
                ) THEN RAISE EXCEPTION 'NAVIGATION_TARGET_UNSAFE' USING ERRCODE='P0003'; END IF;
        """
    else:
        internal_check = """
                PERFORM content.slaif_navigation_internal_target_validate(
                    p_site_id,p_target_value);
        """
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
                PERFORM content.slaif_navigation_page_target_validate(
                    p_site_id,p_page_id,p_target_value);
                IF NOT content.slaif_agent_page_accessible(p_site_id,p_page_id)
                THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
            ELSIF p_page_id IS NOT NULL THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            ELSIF p_target_kind='INTERNAL' THEN
                IF NOT (p_target_value='/' OR p_target_value ~ '^/[A-Za-z0-9][A-Za-z0-9._~/-]*$')
                   OR p_target_value ~ '//|\\\\|\\.\\.'
                   OR p_target_value ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)'
                THEN RAISE EXCEPTION 'NAVIGATION_TARGET_UNSAFE' USING ERRCODE='P0003'; END IF;
{internal_check}
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


def _render_navigation_sql(*, restored: bool) -> str:
    internal_check = (
        """
                ELSIF item.target_kind='INTERNAL' THEN
                    IF item.page_id IS NOT NULL
                       OR NOT content.slaif_render_internal_target_exists(
                           p_site_id,item.target_value,
                           coalesce(item.locale,p_locale),p_statuses)
                    THEN
                        RAISE EXCEPTION 'RENDER_NAVIGATION_TARGET_INVALID'
                            USING ERRCODE='P0003';
                    END IF;
        """
        if not restored
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
                    BEGIN
                        PERFORM content.slaif_navigation_page_target_validate(
                            p_site_id,item.page_id,item.target_value);
                        item_target:=content.slaif_agent_page_effective_route(page_row.id);
                    EXCEPTION WHEN OTHERS THEN
                        RAISE EXCEPTION 'RENDER_NAVIGATION_PAGE_INVALID'
                            USING ERRCODE='P0003';
                    END;
{internal_check}                ELSIF item.target_kind NOT IN ('INTERNAL','EXTERNAL')
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


def _rename(function: str, renamed: str) -> None:
    op.execute(f"ALTER FUNCTION {function} RENAME TO {renamed}")


def _drop(function: str) -> None:
    op.execute(f"DROP FUNCTION IF EXISTS {function}")


def _agent_page_validate_sql(*, restored: bool) -> str:
    body = (
        "            PERFORM content.slaif_redirect_page_guard(p_site_id);\n"
        if restored
        else "            PERFORM content.slaif_redirect_page_guard(p_site_id);\n"
        "            PERFORM content.slaif_navigation_validate_internal_targets(p_site_id);\n"
    )
    if restored:
        body = "            PERFORM content.slaif_redirect_page_guard(p_site_id);\n"
    return f"""
        CREATE FUNCTION content.slaif_agent_page_validate(
            p_site_id uuid, p_page_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM content.slaif_agent_page_validate_base_051(p_site_id,p_page_id);
{body}        END; $fn$
    """


def _agent_page_delete_sql(*, restored: bool) -> str:
    graph = (
        "            PERFORM content.slaif_navigation_validate_internal_targets(p_site_id);\n"
        if not restored
        else ""
    )
    return f"""
        CREATE FUNCTION content.slaif_agent_page_delete(
            p_site_id uuid, p_page_id uuid, p_expected integer
        ) RETURNS TABLE(
{_PAGE_RETURN}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old_route text;
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT content.slaif_agent_page_effective_route(p.id)
                INTO old_route
            FROM content.page p
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.deleted_at IS NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF content.slaif_redirect_page_target_dependency(
                p_site_id,old_route,p_page_id
            ) THEN
                RAISE EXCEPTION 'REDIRECT_DEPENDENCY' USING ERRCODE='P0003';
            END IF;
            RETURN QUERY SELECT * FROM content.slaif_agent_page_delete_base_051(
                p_site_id,p_page_id,p_expected
            );
            PERFORM content.slaif_redirect_page_guard(p_site_id);
{graph}        END; $fn$
    """


def _editor_page_sql(*, restored: bool) -> tuple[str, str, str]:
    graph = (
        "            PERFORM content.slaif_navigation_validate_internal_targets(p_site_id);\n"
        if not restored
        else ""
    )
    create = f"""
        CREATE FUNCTION content.slaif_page_create(
            p_site_id uuid, p_slug text, p_title text, p_status text, p_locale text
        ) RETURNS TABLE(
            id uuid, site_id uuid, slug text, title text, status text, locale text,
            parent_id uuid, row_version integer, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT * FROM content.slaif_page_create_base_051(
                p_site_id,p_slug,p_title,p_status,p_locale
            );
            PERFORM content.slaif_redirect_page_guard(p_site_id);
{graph}        END; $fn$
    """
    update = f"""
        CREATE FUNCTION content.slaif_page_update(
            p_page_id uuid, p_slug text, p_title text, p_status text,
            p_expected_row_version integer
        ) RETURNS TABLE(
            id uuid, site_id uuid, slug text, title text, status text, locale text,
            parent_id uuid, row_version integer, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE target_site uuid;
        BEGIN
            SELECT p.site_id INTO target_site FROM content.page p
            WHERE p.id=p_page_id;
            RETURN QUERY SELECT * FROM content.slaif_page_update_base_051(
                p_page_id,p_slug,p_title,p_status,p_expected_row_version
            );
            IF target_site IS NOT NULL THEN
                PERFORM content.slaif_redirect_page_guard(target_site);
{("                PERFORM content.slaif_navigation_validate_internal_targets(target_site);" if not restored else "")}
            END IF;
        END; $fn$
    """
    delete = f"""
        CREATE FUNCTION content.slaif_page_delete(p_page_id uuid)
        RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE target_site uuid; old_route text;
        BEGIN
            SELECT p.site_id,content.slaif_agent_page_effective_route(p.id)
                INTO target_site,old_route
            FROM content.page p WHERE p.id=p_page_id;
            IF target_site IS NULL THEN RETURN; END IF;
            PERFORM control.slaif_agent_structural_lock(target_site);
            IF content.slaif_redirect_page_target_dependency(
                target_site,old_route,p_page_id
            ) THEN
                RAISE EXCEPTION 'REDIRECT_DEPENDENCY' USING ERRCODE='P0003';
            END IF;
            PERFORM content.slaif_page_delete_base_051(p_page_id);
            PERFORM content.slaif_redirect_page_guard(target_site);
{("            PERFORM content.slaif_navigation_validate_internal_targets(target_site);" if not restored else "")}
        END; $fn$
    """
    return create, update, delete


def _editor_navigation_wrapper_sql(*, update: bool) -> str:
    if not update:
        return """
            CREATE FUNCTION content.slaif_navigation_item_create(
                p_site_id uuid,p_navigation_id uuid,p_parent_id uuid,p_page_id uuid,
                p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,
                p_position integer
            ) RETURNS SETOF content.navigation_item
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            BEGIN
                IF p_target_kind='INTERNAL' THEN
                    PERFORM content.slaif_navigation_internal_target_validate(
                        p_site_id,p_target_value);
                END IF;
                RETURN QUERY SELECT * FROM content.slaif_navigation_item_create_base_058(
                    p_site_id,p_navigation_id,p_parent_id,p_page_id,p_target_kind,
                    p_target_value,p_labels,p_locale,p_position);
                PERFORM content.slaif_navigation_validate_internal_targets(p_site_id);
            END; $fn$
        """
    return """
        CREATE FUNCTION content.slaif_navigation_item_update(
            p_site_id uuid,p_id uuid,p_parent_id uuid,p_page_id uuid,
            p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,
            p_position integer,p_expected integer
        ) RETURNS SETOF content.navigation_item
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old content.navigation_item; new_kind text; new_value text;
        BEGIN
            SELECT i.* INTO old FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.id=p_id;
            IF FOUND THEN
                new_kind:=coalesce(p_target_kind,old.target_kind);
                new_value:=coalesce(p_target_value,old.target_value);
                IF new_kind='INTERNAL' THEN
                    PERFORM content.slaif_navigation_internal_target_validate(
                        p_site_id,new_value);
                END IF;
            END IF;
            RETURN QUERY SELECT * FROM content.slaif_navigation_item_update_base_058(
                p_site_id,p_id,p_parent_id,p_page_id,p_target_kind,p_target_value,
                p_labels,p_locale,p_position,p_expected);
            PERFORM content.slaif_navigation_validate_internal_targets(p_site_id);
        END; $fn$
    """


def _agent_apply_wrapper_sql() -> str:
    return f"""
        CREATE FUNCTION content.slaif_agent_navigation_item_apply(
            p_site_id uuid,p_item_id uuid,p_navigation_id uuid,p_parent_id uuid,
            p_page_id uuid,p_target_kind text,p_target_value text,p_labels jsonb,
            p_locale text,p_before uuid,p_after uuid,p_expected integer,
            p_is_create boolean
        ) RETURNS TABLE(
{_ITEM_RETURN}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT * FROM content.slaif_agent_navigation_item_apply_base_058(
                p_site_id,p_item_id,p_navigation_id,p_parent_id,p_page_id,
                p_target_kind,p_target_value,p_labels,p_locale,p_before,p_after,
                p_expected,p_is_create);
            PERFORM content.slaif_navigation_validate_internal_targets(p_site_id);
        END; $fn$
    """


def _agent_update_wrapper_sql() -> str:
    return f"""
        CREATE FUNCTION content.slaif_agent_navigation_item_update(
            p_site_id uuid,p_item_id uuid,p_navigation_id uuid,p_page_id uuid,
            p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,
            p_expected integer
        ) RETURNS TABLE(
{_ITEM_RETURN}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT * FROM content.slaif_agent_navigation_item_update_base_058(
                p_site_id,p_item_id,p_navigation_id,p_page_id,p_target_kind,
                p_target_value,p_labels,p_locale,p_expected);
            PERFORM content.slaif_navigation_validate_internal_targets(p_site_id);
        END; $fn$
    """


def _execute_editor_pages(*, restored: bool) -> None:
    values = _editor_page_sql(restored=restored)
    for value in values:
        op.execute(value)


def _execute_internal_route_helpers() -> None:
    sql = _internal_route_helpers_sql()
    marker = "\n\n        CREATE OR REPLACE FUNCTION "
    statements = sql.split(marker)
    op.execute(statements[0])
    for statement in statements[1:]:
        op.execute("        CREATE OR REPLACE FUNCTION " + statement)


def _set_security() -> None:
    for function in (
        "content.slaif_agent_page_delete_base_058(uuid,uuid,integer)",
        "content.slaif_agent_navigation_item_update_base_058(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer)",
        "content.slaif_page_create_base_058(uuid,text,text,text,text)",
        "content.slaif_page_update_base_058(uuid,text,text,text,integer)",
        "content.slaif_page_delete_base_058(uuid)",
        "content.slaif_navigation_item_create_base_058(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer)",
        "content.slaif_navigation_item_update_base_058(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer,integer)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(
            f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC, "
            "slaif_agent_runtime, slaif_editor_runtime, slaif_control"
        )
    for function in (
        "content.slaif_navigation_internal_target_exists(uuid,text)",
        "content.slaif_navigation_internal_target_validate(uuid,text)",
        "content.slaif_navigation_validate_internal_targets(uuid)",
        "content.slaif_render_internal_target_exists(uuid,text,text,text[])",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
    for function in (
        "content.slaif_agent_page_validate(uuid,uuid)",
        "content.slaif_agent_navigation_item_apply(uuid,uuid,uuid,uuid,uuid,text,text,jsonb,text,uuid,uuid,integer,boolean)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(
            f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC, slaif_agent_runtime"
        )
    for function in (
        "content.slaif_agent_page_delete(uuid,uuid,integer)",
        "content.slaif_agent_navigation_item_update(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_agent_runtime")
    for function in (
        "content.slaif_page_create(uuid,text,text,text,text)",
        "content.slaif_page_update(uuid,text,text,text,integer)",
        "content.slaif_page_delete(uuid)",
        "content.slaif_navigation_item_create(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer)",
        "content.slaif_navigation_item_update(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer,integer)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(
            f"GRANT EXECUTE ON FUNCTION {function} TO slaif_editor_runtime, slaif_control"
        )


def _restore_security() -> None:
    for function in (
        "content.slaif_agent_page_validate(uuid,uuid)",
        "content.slaif_agent_navigation_item_apply(" + _AGENT_APPLY_SIGNATURE + ")",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(
            f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC, slaif_agent_runtime"
        )
    for function in (
        "content.slaif_agent_page_delete(" + _PAGE_DELETE_SIGNATURE + ")",
        "content.slaif_agent_navigation_item_update(" + _AGENT_UPDATE_SIGNATURE + ")",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_agent_runtime")
    for function in (
        "content.slaif_page_create(uuid,text,text,text,text)",
        "content.slaif_page_update(uuid,text,text,text,integer)",
        "content.slaif_page_delete(uuid)",
        "content.slaif_navigation_item_create(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer)",
        "content.slaif_navigation_item_update(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer,integer)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(
            f"GRANT EXECUTE ON FUNCTION {function} TO slaif_editor_runtime, slaif_control"
        )


def upgrade() -> None:
    _execute_internal_route_helpers()
    op.execute(_locale_route_sql(restored=False))
    op.execute(_agent_target_sql(restored=False))
    op.execute(_render_navigation_sql(restored=False))

    _rename(
        "content.slaif_agent_page_validate(uuid,uuid)",
        "slaif_agent_page_validate_base_058",
    )
    op.execute(_agent_page_validate_sql(restored=False))
    _rename(
        "content.slaif_agent_page_delete(uuid,uuid,integer)",
        "slaif_agent_page_delete_base_058",
    )
    op.execute(_agent_page_delete_sql(restored=False))

    _rename(
        "content.slaif_agent_navigation_item_apply(" + _AGENT_APPLY_SIGNATURE + ")",
        "slaif_agent_navigation_item_apply_base_058",
    )
    op.execute(_agent_apply_wrapper_sql())
    _rename(
        "content.slaif_agent_navigation_item_update(" + _AGENT_UPDATE_SIGNATURE + ")",
        "slaif_agent_navigation_item_update_base_058",
    )
    op.execute(_agent_update_wrapper_sql())

    for function, renamed in (
        (
            "content.slaif_page_create(uuid,text,text,text,text)",
            "slaif_page_create_base_058",
        ),
        (
            "content.slaif_page_update(uuid,text,text,text,integer)",
            "slaif_page_update_base_058",
        ),
        ("content.slaif_page_delete(uuid)", "slaif_page_delete_base_058"),
    ):
        _rename(function, renamed)
    _execute_editor_pages(restored=False)

    _rename(
        "content.slaif_navigation_item_create(" + _EDITOR_CREATE_SIGNATURE + ")",
        "slaif_navigation_item_create_base_058",
    )
    _rename(
        "content.slaif_navigation_item_update(" + _EDITOR_UPDATE_SIGNATURE + ")",
        "slaif_navigation_item_update_base_058",
    )
    op.execute(_editor_navigation_wrapper_sql(update=False))
    op.execute(_editor_navigation_wrapper_sql(update=True))
    _set_security()


def downgrade() -> None:
    _drop("content.slaif_navigation_item_update(" + _EDITOR_UPDATE_SIGNATURE + ")")
    _drop("content.slaif_navigation_item_create(" + _EDITOR_CREATE_SIGNATURE + ")")
    _rename(
        "content.slaif_navigation_item_create_base_058("
        + _EDITOR_CREATE_SIGNATURE
        + ")",
        "slaif_navigation_item_create",
    )
    _rename(
        "content.slaif_navigation_item_update_base_058("
        + _EDITOR_UPDATE_SIGNATURE
        + ")",
        "slaif_navigation_item_update",
    )
    for function in (
        "content.slaif_page_delete(uuid)",
        "content.slaif_page_update(uuid,text,text,text,integer)",
        "content.slaif_page_create(uuid,text,text,text,text)",
    ):
        _drop(function)
    for base_name, function in (
        ("slaif_page_create_base_058", "slaif_page_create"),
        ("slaif_page_update_base_058", "slaif_page_update"),
        ("slaif_page_delete_base_058", "slaif_page_delete"),
    ):
        _rename("content." + base_name, function)

    _drop("content.slaif_agent_navigation_item_update(" + _AGENT_UPDATE_SIGNATURE + ")")
    _rename(
        "content.slaif_agent_navigation_item_update_base_058("
        + _AGENT_UPDATE_SIGNATURE
        + ")",
        "slaif_agent_navigation_item_update",
    )
    _drop("content.slaif_agent_navigation_item_apply(" + _AGENT_APPLY_SIGNATURE + ")")
    _rename(
        "content.slaif_agent_navigation_item_apply_base_058("
        + _AGENT_APPLY_SIGNATURE
        + ")",
        "slaif_agent_navigation_item_apply",
    )

    _drop("content.slaif_agent_page_delete(" + _PAGE_DELETE_SIGNATURE + ")")
    _rename(
        "content.slaif_agent_page_delete_base_058(" + _PAGE_DELETE_SIGNATURE + ")",
        "slaif_agent_page_delete",
    )
    _drop("content.slaif_agent_page_validate(" + _PAGE_VALIDATE_SIGNATURE + ")")
    _rename(
        "content.slaif_agent_page_validate_base_058(" + _PAGE_VALIDATE_SIGNATURE + ")",
        "slaif_agent_page_validate",
    )
    op.execute(_locale_route_sql(restored=True))
    op.execute(_agent_target_sql(restored=True))
    op.execute(_render_navigation_sql(restored=True))
    for function in (
        "content.slaif_render_internal_target_exists(uuid,text,text,text[])",
        "content.slaif_navigation_validate_internal_targets(uuid)",
        "content.slaif_navigation_internal_target_validate(uuid,text)",
        "content.slaif_navigation_internal_target_exists(uuid,text)",
    ):
        _drop(function)
    _restore_security()
