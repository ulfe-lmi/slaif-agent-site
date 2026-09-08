# ruff: noqa: E501
"""Serialize locale changes with complete static route graph validation."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "053_001"
down_revision: str | Sequence[str] | None = "052_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_LOCALE_RETURN = """
    id uuid, site_id uuid, tag text, enabled boolean, is_default boolean,
    "position" integer, metadata jsonb, row_version integer,
    created_at timestamptz, updated_at timestamptz
"""


_AGENT_LOCALE_RETURN = _LOCALE_RETURN


def _safe_redirect_target_sql() -> str:
    """Avoid strict route resolution on rows hidden by a COW tombstone."""

    return """
        CREATE OR REPLACE FUNCTION content.slaif_redirect_static_target_exists(
            p_site_id uuid, p_target text, p_locale text, p_agent boolean
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE default_locale text; page_row record; page_route text;
        BEGIN
            SELECT l.tag INTO default_locale FROM content.site_locale l
            WHERE l.site_id=p_site_id AND l.enabled AND l.is_default;
            FOR page_row IN
                SELECT p.id FROM content.page p
                WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
                  AND p.route_template IS NULL
                  AND p.locale=coalesce(p_locale,default_locale)
                  AND EXISTS (
                      SELECT 1 FROM content.site_locale l
                      WHERE l.site_id=p.site_id AND l.tag=p.locale AND l.enabled
                  )
            LOOP
                BEGIN
                    IF p_agent AND NOT content.slaif_agent_page_accessible(
                        p_site_id,page_row.id
                    ) THEN
                        CONTINUE;
                    END IF;
                    page_route:=content.slaif_agent_page_effective_route(page_row.id);
                EXCEPTION WHEN SQLSTATE 'P0002' THEN
                    CONTINUE;
                END;
                IF page_route=p_target THEN RETURN true; END IF;
            END LOOP;
            RETURN false;
        END; $fn$
    """


def _route_exists_sql() -> str:
    return """
        CREATE FUNCTION content.slaif_locale_route_exists(
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
        END; $fn$
    """


def _graph_sql() -> str:
    return """
        CREATE FUNCTION content.slaif_locale_validate_graph(
            p_site_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE
            locale_row record; page_row record; other_page record;
            navigation_row record; item_row record; parent_row record;
            page_route text; other_route text; cursor_id uuid;
            visited uuid[]; depth integer; label_locale text;
            sibling record;
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM content.site_locale l
                WHERE l.site_id=p_site_id AND l.enabled AND l.is_default
            ) THEN
                RAISE EXCEPTION 'LOCALE_DEFAULT_REQUIRED' USING ERRCODE='P0003';
            END IF;

            FOR page_row IN
                SELECT p.* FROM content.page p
                WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
            LOOP
                IF page_row.slug !~ '^[a-z0-9][a-z0-9._~-]{0,62}$'
                   OR (page_row.route_template IS NOT NULL
                       AND page_row.route_template<>'{slug}')
                THEN
                    RAISE EXCEPTION 'PAGE_ROUTE_INVALID' USING ERRCODE='P0003';
                END IF;
                BEGIN
                    page_route:=content.slaif_agent_page_effective_route(page_row.id);
                EXCEPTION WHEN SQLSTATE 'P0002' THEN
                    RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002';
                END;
                IF content.slaif_agent_page_route_conflict(page_row.id,page_route) THEN
                    RAISE EXCEPTION 'PAGE_ROUTE_CONFLICT' USING ERRCODE='P0003';
                END IF;
                IF page_route ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)' THEN
                    RAISE EXCEPTION 'PAGE_ROUTE_RESERVED' USING ERRCODE='P0003';
                END IF;
                IF page_row.route_template='{slug}' AND EXISTS (
                    SELECT 1 FROM content.page child
                    WHERE child.site_id=p_site_id AND child.parent_id=page_row.id
                      AND child.deleted_at IS NULL
                ) THEN
                    RAISE EXCEPTION 'PAGE_DYNAMIC_PARENT' USING ERRCODE='P0003';
                END IF;
            END LOOP;

            FOR navigation_row IN
                SELECT n.* FROM content.navigation n WHERE n.site_id=p_site_id
            LOOP
                FOR label_locale IN
                    SELECT key FROM jsonb_object_keys(navigation_row.labels) AS key
                LOOP
                    IF NOT EXISTS (
                        SELECT 1 FROM content.site_locale l
                        WHERE l.site_id=p_site_id AND l.tag=label_locale AND l.enabled
                    ) THEN
                        RAISE EXCEPTION 'NAVIGATION_LABEL_LOCALE_INVALID'
                            USING ERRCODE='P0003';
                    END IF;
                END LOOP;
            END LOOP;

            FOR item_row IN
                SELECT i.* FROM content.navigation_item i
                WHERE i.site_id=p_site_id
            LOOP
                IF item_row.locale IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM content.site_locale l
                    WHERE l.site_id=p_site_id AND l.tag=item_row.locale AND l.enabled
                ) THEN
                    RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003';
                END IF;
                FOR label_locale IN
                    SELECT key FROM jsonb_object_keys(item_row.labels) AS key
                LOOP
                    IF NOT EXISTS (
                        SELECT 1 FROM content.site_locale l
                        WHERE l.site_id=p_site_id AND l.tag=label_locale AND l.enabled
                    ) THEN
                        RAISE EXCEPTION 'NAVIGATION_LABEL_LOCALE_INVALID'
                            USING ERRCODE='P0003';
                    END IF;
                END LOOP;
                IF item_row.parent_id IS NOT NULL THEN
                    SELECT i.* INTO parent_row FROM content.navigation_item i
                    WHERE i.site_id=p_site_id AND i.id=item_row.parent_id;
                    IF NOT FOUND OR parent_row.navigation_id<>item_row.navigation_id THEN
                        RAISE EXCEPTION 'NAVIGATION_PARENT_INVALID' USING ERRCODE='P0003';
                    END IF;
                    cursor_id:=item_row.parent_id; visited:=ARRAY[]::uuid[]; depth:=0;
                    LOOP
                        IF cursor_id=ANY(visited) OR depth>=8 THEN
                            RAISE EXCEPTION 'NAVIGATION_CYCLE' USING ERRCODE='P0003';
                        END IF;
                        visited:=array_append(visited,cursor_id); depth:=depth+1;
                        SELECT i.parent_id INTO cursor_id
                        FROM content.navigation_item i
                        WHERE i.site_id=p_site_id AND i.id=cursor_id;
                        EXIT WHEN cursor_id IS NULL;
                    END LOOP;
                END IF;
                IF item_row.target_kind='PAGE' THEN
                    IF item_row.page_id IS NULL
                       OR item_row.target_value<>item_row.page_id::text
                       OR NOT EXISTS (
                           SELECT 1 FROM content.page p
                           WHERE p.site_id=p_site_id AND p.id=item_row.page_id
                             AND p.deleted_at IS NULL
                       ) THEN
                        RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
                    END IF;
                ELSIF item_row.target_kind='INTERNAL' THEN
                    IF item_row.page_id IS NOT NULL
                       OR (item_row.target_value<>'/' AND item_row.target_value !~ '^/[a-z0-9][a-z0-9._~/-]*$')
                       OR item_row.target_value ~ '//|\\.\\.|%|\\\\'
                       OR item_row.target_value ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)'
                       OR NOT content.slaif_locale_route_exists(p_site_id,item_row.target_value)
                    THEN
                        RAISE EXCEPTION 'NAVIGATION_TARGET_UNSAFE' USING ERRCODE='P0003';
                    END IF;
                ELSIF item_row.target_kind='EXTERNAL' THEN
                    IF item_row.page_id IS NOT NULL
                       OR item_row.target_value !~ '^https://[^/@?#]+([/?#].*)?$'
                    THEN
                        RAISE EXCEPTION 'NAVIGATION_TARGET_UNSAFE' USING ERRCODE='P0003';
                    END IF;
                ELSE
                    RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003';
                END IF;
            END LOOP;

            FOR sibling IN
                SELECT i.navigation_id,i.parent_id,min(i.position) AS minimum,
                    max(i.position) AS maximum,count(*)::integer AS total
                FROM content.navigation_item i WHERE i.site_id=p_site_id
                GROUP BY i.navigation_id,i.parent_id
            LOOP
                IF sibling.minimum<>0 OR sibling.maximum<>sibling.total-1 THEN
                    RAISE EXCEPTION 'NAVIGATION_POSITION_LIMIT' USING ERRCODE='P0003';
                END IF;
            END LOOP;

            PERFORM content.slaif_redirect_validate_state(p_site_id,false);
        END; $fn$;
    """


def _wrap_locale_functions() -> None:
    for function, base_name in (
        (
            "content.slaif_locale_create(uuid,text,boolean,boolean,integer,jsonb)",
            "slaif_locale_create_base_053",
        ),
        (
            "content.slaif_locale_update(uuid,uuid,text,boolean,boolean,integer,jsonb,integer)",
            "slaif_locale_update_base_053",
        ),
        (
            "content.slaif_locale_delete(uuid,uuid,integer)",
            "slaif_locale_delete_base_053",
        ),
        (
            "content.slaif_agent_locale_create(uuid,text,boolean,boolean,integer,jsonb)",
            "slaif_agent_locale_create_base_053",
        ),
        (
            "content.slaif_agent_locale_update(uuid,uuid,boolean,boolean,integer,jsonb,integer)",
            "slaif_agent_locale_update_base_053",
        ),
        (
            "content.slaif_agent_locale_delete(uuid,uuid,integer)",
            "slaif_agent_locale_delete_base_053",
        ),
    ):
        op.execute(f"ALTER FUNCTION {function} RENAME TO {base_name}")

    op.execute(
        """
        CREATE FUNCTION content.slaif_locale_create(
            p_site_id uuid,p_tag text,p_enabled boolean,p_default boolean,
            p_position integer,p_metadata jsonb
        ) RETURNS SETOF content.site_locale LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT * FROM content.slaif_locale_create_base_053(
                p_site_id,p_tag,p_enabled,p_default,p_position,p_metadata
            );
            PERFORM content.slaif_locale_validate_graph(p_site_id);
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_locale_update(
            p_site_id uuid,p_id uuid,p_tag text,p_enabled boolean,p_default boolean,
            p_position integer,p_metadata jsonb,p_expected integer
        ) RETURNS SETOF content.site_locale LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT * FROM content.slaif_locale_update_base_053(
                p_site_id,p_id,p_tag,p_enabled,p_default,p_position,p_metadata,p_expected
            );
            PERFORM content.slaif_locale_validate_graph(p_site_id);
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_locale_delete(
            p_site_id uuid,p_id uuid,p_expected integer
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM content.slaif_locale_delete_base_053(p_site_id,p_id,p_expected);
            PERFORM content.slaif_locale_validate_graph(p_site_id);
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_locale_create(
            p_site_id uuid,p_tag text,p_enabled boolean,p_default boolean,
            p_position integer,p_metadata jsonb
        ) RETURNS TABLE("""
        + _AGENT_LOCALE_RETURN
        + """)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT * FROM content.slaif_agent_locale_create_base_053(
                p_site_id,p_tag,p_enabled,p_default,p_position,p_metadata
            );
            PERFORM content.slaif_locale_validate_graph(p_site_id);
        END; $fn$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_locale_update(
            p_site_id uuid,p_locale_id uuid,p_enabled boolean,p_default boolean,
            p_position integer,p_metadata jsonb,p_expected integer
        ) RETURNS TABLE("""
        + _AGENT_LOCALE_RETURN
        + """)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT * FROM content.slaif_agent_locale_update_base_053(
                p_site_id,p_locale_id,p_enabled,p_default,p_position,p_metadata,p_expected
            );
            PERFORM content.slaif_locale_validate_graph(p_site_id);
        END; $fn$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_locale_delete(
            p_site_id uuid,p_locale_id uuid,p_expected integer
        ) RETURNS TABLE("""
        + _AGENT_LOCALE_RETURN
        + """)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT * FROM content.slaif_agent_locale_delete_base_053(
                p_site_id,p_locale_id,p_expected
            );
            PERFORM content.slaif_locale_validate_graph(p_site_id);
        END; $fn$;
        """
    )


def _set_function_security() -> None:
    for function in (
        "content.slaif_locale_create_base_053(uuid,text,boolean,boolean,integer,jsonb)",
        "content.slaif_locale_update_base_053(uuid,uuid,text,boolean,boolean,integer,jsonb,integer)",
        "content.slaif_locale_delete_base_053(uuid,uuid,integer)",
        "content.slaif_agent_locale_create_base_053(uuid,text,boolean,boolean,integer,jsonb)",
        "content.slaif_agent_locale_update_base_053(uuid,uuid,boolean,boolean,integer,jsonb,integer)",
        "content.slaif_agent_locale_delete_base_053(uuid,uuid,integer)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(
            f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC, "
            "slaif_agent_runtime, slaif_editor_runtime, slaif_control"
        )
    for function, role in (
        (
            "content.slaif_locale_create(uuid,text,boolean,boolean,integer,jsonb)",
            "slaif_editor_runtime",
        ),
        (
            "content.slaif_locale_update(uuid,uuid,text,boolean,boolean,integer,jsonb,integer)",
            "slaif_editor_runtime",
        ),
        ("content.slaif_locale_delete(uuid,uuid,integer)", "slaif_editor_runtime"),
        (
            "content.slaif_agent_locale_create(uuid,text,boolean,boolean,integer,jsonb)",
            "slaif_agent_runtime",
        ),
        (
            "content.slaif_agent_locale_update(uuid,uuid,boolean,boolean,integer,jsonb,integer)",
            "slaif_agent_runtime",
        ),
        ("content.slaif_agent_locale_delete(uuid,uuid,integer)", "slaif_agent_runtime"),
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO {role}")
    for function in (
        "content.slaif_locale_route_exists(uuid,text)",
        "content.slaif_locale_validate_graph(uuid)",
        "content.slaif_redirect_static_target_exists(uuid,text,text,boolean)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")


def upgrade() -> None:
    op.execute(_safe_redirect_target_sql())
    op.execute(_route_exists_sql())
    op.execute(_graph_sql())
    _wrap_locale_functions()
    _set_function_security()


def downgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE relation_kind "char";
        BEGIN
            SELECT c.relkind INTO relation_kind
            FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n
              ON n.oid=c.relnamespace
            WHERE n.nspname='content' AND c.relname='site_locale';
            IF relation_kind='v' THEN
                RAISE EXCEPTION '053_DOWNGRADE_REQUIRES_PUBLIC_COW_DISABLE'
                    USING ERRCODE='P0003';
            END IF;
        END $$
        """
    )
    for function in (
        "content.slaif_locale_create(uuid,text,boolean,boolean,integer,jsonb)",
        "content.slaif_locale_update(uuid,uuid,text,boolean,boolean,integer,jsonb,integer)",
        "content.slaif_locale_delete(uuid,uuid,integer)",
        "content.slaif_agent_locale_create(uuid,text,boolean,boolean,integer,jsonb)",
        "content.slaif_agent_locale_update(uuid,uuid,boolean,boolean,integer,jsonb,integer)",
        "content.slaif_agent_locale_delete(uuid,uuid,integer)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function}")
    op.execute("DROP FUNCTION IF EXISTS content.slaif_locale_validate_graph(uuid)")
    op.execute("DROP FUNCTION IF EXISTS content.slaif_locale_route_exists(uuid,text)")
    for function, base_name in (
        ("content.slaif_locale_create_base_053", "slaif_locale_create"),
        ("content.slaif_locale_update_base_053", "slaif_locale_update"),
        ("content.slaif_locale_delete_base_053", "slaif_locale_delete"),
        ("content.slaif_agent_locale_create_base_053", "slaif_agent_locale_create"),
        ("content.slaif_agent_locale_update_base_053", "slaif_agent_locale_update"),
        ("content.slaif_agent_locale_delete_base_053", "slaif_agent_locale_delete"),
    ):
        op.execute(f"ALTER FUNCTION {function} RENAME TO {base_name}")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_redirect_static_target_exists(
            p_site_id uuid,p_target text,p_locale text,p_agent boolean
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE default_locale text;
        BEGIN
            SELECT l.tag INTO default_locale FROM content.site_locale l
            WHERE l.site_id=p_site_id AND l.enabled AND l.is_default;
            IF p_agent THEN
                RETURN EXISTS (
                    SELECT 1 FROM content.page p
                    WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
                      AND p.route_template IS NULL
                      AND p.locale=coalesce(p_locale,default_locale)
                      AND content.slaif_agent_page_accessible(p_site_id,p.id)
                      AND content.slaif_agent_page_effective_route(p.id)=p_target
                );
            END IF;
            RETURN EXISTS (
                SELECT 1 FROM content.page p
                WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
                  AND p.route_template IS NULL
                  AND p.locale=coalesce(p_locale,default_locale)
                  AND EXISTS (
                      SELECT 1 FROM content.site_locale l
                      WHERE l.site_id=p.site_id AND l.tag=p.locale AND l.enabled
                  )
                  AND content.slaif_agent_page_effective_route(p.id)=p_target
            );
        END; $fn$
        """
    )
