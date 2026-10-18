# ruff: noqa: E501
"""Freeze-time canonical revision coherence (083/4-a).

The only behavioral change in 083/4-a's SQL surface is the trusted review
snapshot materializer ``control.slaif_review_workspace_state(uuid)``:

1. after the workspace-row ``FOR UPDATE`` and the established workspace
   lifecycle advisory lock (key 280), the canonical site row is locked
   (``FOR UPDATE``) in the same workspace-then-site order the acceptance
   verification path already uses, and its ``canonical_revision`` and
   ``status`` are captured in that single locked read before the COW
   context/content read; the pre-lock ``ACTIVE`` ``EXISTS`` stays as a
   fast fail only, and the same ``REVIEW_SITE_NOT_ACTIVE`` fail-closed
   guard is re-asserted against the locked row after the wait, so a
   status change spanning the lock wait cannot go stale;
2. the materialized document reports that locked canonical revision as
   ``base_site_revision`` (previously the workspace-creation-time
   ``workspace.base_site_revision``).

The row lock is xact-level, so the freeze worker holds it through
snapshot completion and the job terminal, and the acceptance preflight
holds it through the re-validation. No tables, roles, grants, or other
function bodies change; the function signature, owner, and ACL are
re-asserted unchanged. The downgrade restores the exact 070_001 body,
ownership, and grants.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "075_001"
down_revision: str | Sequence[str] | None = "074_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_WORKSPACE_STATE = "control.slaif_review_workspace_state(uuid)"
_REVOKE_ROLES = (
    "slaif_control",
    "slaif_editor_runtime",
    "slaif_agent_runtime",
    "slaif_public_reader",
    "slaif_preview_reader",
    "slaif_reviewer",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
)

# The exact 070_001 materializer body (downgrade restoration).
_MATERIALIZER_070 = r"""
        CREATE OR REPLACE FUNCTION control.slaif_review_workspace_state(p_workspace_id uuid)
        RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            ws control.workspace%ROWTYPE;
            site_row record;
            page_row record;
            nodes_row jsonb;
            node_props jsonb;
            route text;
            media_key text;
            media_id uuid;
            media_row record;
            page_docs jsonb := '[]'::jsonb;
            media_docs jsonb := '{}'::jsonb;
            doc jsonb;
        BEGIN
            SELECT * INTO ws FROM control.workspace
            WHERE id = p_workspace_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'REVIEW_WORKSPACE_NOT_FOUND'
                    USING ERRCODE = 'P0002';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM control.site AS site
                WHERE site.id = ws.site_id AND site.status = 'ACTIVE'
            ) THEN
                RAISE EXCEPTION 'REVIEW_SITE_NOT_ACTIVE'
                    USING ERRCODE = 'P0002';
            END IF;
            PERFORM pg_advisory_xact_lock(
                hashtextextended(p_workspace_id::text, 280)
            );
            PERFORM set_config('app.session_id', p_workspace_id::text, true);
            SELECT site_key, display_name, default_locale,
                   component_catalog_version
              INTO site_row
              FROM control.site WHERE id = ws.site_id;

            FOR page_row IN
                SELECT p.*
                FROM content.page AS p
                WHERE p.site_id = ws.site_id
                  AND p.deleted_at IS NULL
                  AND p.status IN ('PUBLISHED','DRAFT')
                ORDER BY p.locale COLLATE "C", p.slug COLLATE "C", p.id
            LOOP
                BEGIN
                    route := content.slaif_agent_page_effective_route(
                        page_row.id
                    );
                EXCEPTION WHEN OTHERS THEN
                    route := NULL;
                END;
                SELECT coalesce(
                    jsonb_agg(row_to_json(c) ORDER BY c.slot_key, c.order_key,
                               c.id),
                    '[]'::jsonb
                ) INTO nodes_row
                FROM (SELECT * FROM content.page_composition AS c
                      WHERE c.site_id = ws.site_id
                        AND c.page_id = page_row.id) AS c;
                -- Collect the media references of this page's composition.
                IF nodes_row IS NOT NULL THEN
                    FOR node_props IN
                        SELECT c2.props FROM content.page_composition AS c2
                        WHERE c2.site_id = ws.site_id
                          AND c2.page_id = page_row.id
                    LOOP
                        IF node_props IS NULL THEN
                            CONTINUE;
                        END IF;
                        IF jsonb_typeof(node_props -> 'mediaId') = 'string' THEN
                            BEGIN
                                media_id := (node_props ->> 'mediaId')::uuid;
                                media_key := media_id::text;
                                IF not (media_docs ? media_key) THEN
                                    SELECT * INTO media_row
                                    FROM content.slaif_render_media_resolve(
                                        ws.site_id, media_id
                                    );
                                    IF FOUND THEN
                                        media_docs := media_docs || jsonb_build_object(
                                            media_key, jsonb_build_object(
                                                'id', media_id,
                                                'mime_type', media_row.mime_type,
                                                'size_bytes',
                                                    media_row.size_bytes,
                                                'content_hash',
                                                    media_row.content_hash,
                                                'public_status',
                                                    media_row.public_status
                                            )
                                        );
                                    END IF;
                                END IF;
                            EXCEPTION WHEN invalid_text_representation THEN
                                NULL;
                            END;
                        END IF;
                        IF jsonb_typeof(node_props -> 'items') = 'array' THEN
                            FOR media_key IN
                                SELECT item ->> 'mediaId'
                                FROM jsonb_array_elements(
                                    node_props -> 'items'
                                ) AS item
                                WHERE jsonb_typeof(item -> 'mediaId')
                                      = 'string'
                            LOOP
                                BEGIN
                                    media_id := media_key::uuid;
                                    media_key := media_id::text;
                                    IF not (media_docs ? media_key) THEN
                                        SELECT * INTO media_row
                                        FROM content.slaif_render_media_resolve(
                                            ws.site_id, media_id
                                        );
                                        IF FOUND THEN
                                            media_docs := media_docs || jsonb_build_object(
                                                media_key, jsonb_build_object(
                                                    'id', media_id,
                                                    'mime_type',
                                                        media_row.mime_type,
                                                    'size_bytes',
                                                        media_row.size_bytes,
                                                    'content_hash',
                                                        media_row.content_hash,
                                                    'public_status',
                                                        media_row.public_status
                                                )
                                            );
                                        END IF;
                                    END IF;
                                EXCEPTION WHEN invalid_text_representation THEN
                                    NULL;
                                END;
                            END LOOP;
                        END IF;
                    END LOOP;
                END IF;
                page_docs := page_docs || jsonb_build_object(
                    'id', page_row.id,
                    'site_id', page_row.site_id,
                    'slug', page_row.slug,
                    'title', page_row.title,
                    'status', page_row.status,
                    'locale', page_row.locale,
                    'parent_id', page_row.parent_id,
                    'route_template', page_row.route_template,
                    'effective_route', route,
                    'row_version', page_row.row_version,
                    'nodes', nodes_row
                );
            END LOOP;

            doc := jsonb_build_object(
                'state_version', 'review-snapshot/v1',
                'workspace_id', p_workspace_id,
                'site_id', ws.site_id,
                'site', jsonb_build_object(
                    'site_key', site_row.site_key,
                    'display_name', site_row.display_name,
                    'default_locale', site_row.default_locale,
                    'component_catalog_version',
                        site_row.component_catalog_version
                ),
                'base_site_revision', ws.base_site_revision,
                'operation_watermark', ws.operation_watermark,
                'locales', (
                    SELECT coalesce(
                        jsonb_agg(jsonb_build_object(
                            'tag', l.tag, 'enabled', l.enabled,
                            'is_default', l.is_default, 'position', l.position
                        ) ORDER BY l.position, l.tag COLLATE "C"),
                        '[]'::jsonb
                    )
                    FROM content.site_locale AS l
                    WHERE l.site_id = ws.site_id
                ),
                'theme', (
                    SELECT row_to_json(t)
                    FROM content.slaif_theme_project(ws.site_id) AS t
                ),
                'regions', (
                    SELECT coalesce(
                        jsonb_agg(row_to_json(r)
                            ORDER BY r.region_key, r.variant),
                        '[]'::jsonb
                    )
                    FROM content.slaif_region_list(ws.site_id) AS r
                ),
                'navigation', jsonb_build_object(
                    'definitions', (
                        SELECT coalesce(
                            jsonb_agg(row_to_json(d)
                                ORDER BY d.key COLLATE "C"),
                            '[]'::jsonb
                        )
                        FROM content.navigation AS d
                        WHERE d.site_id = ws.site_id
                    ),
                    'items', (
                        SELECT coalesce(
                            jsonb_agg(row_to_json(n)
                                ORDER BY n.navigation_id, n."position", n.id),
                            '[]'::jsonb
                        )
                        FROM content.slaif_render_navigation_items(
                            ws.site_id, site_row.default_locale,
                            ARRAY['PUBLISHED','DRAFT']
                        ) AS n
                    )
                ),
                'redirects', (
                    SELECT coalesce(
                        jsonb_agg(row_to_json(rd)
                            ORDER BY rd.source_route COLLATE "C",
                                     rd.locale NULLS FIRST),
                        '[]'::jsonb
                    )
                    FROM (SELECT id, site_id, source_route, target,
                                 status_code, locale
                          FROM content.redirect
                          WHERE site_id = ws.site_id) AS rd
                ),
                'pages', page_docs,
                'media', media_docs
            );
            RETURN doc;
        END;
        $fn$
        """


# The 083/4 materializer: the two surgical changes described in the module
# docstring; every other statement byte-identical to 070_001.
_MATERIALIZER_075 = r"""
        CREATE OR REPLACE FUNCTION control.slaif_review_workspace_state(p_workspace_id uuid)
        RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            ws control.workspace%ROWTYPE;
            site_row record;
            site_revision bigint;
            site_status text;
            page_row record;
            nodes_row jsonb;
            node_props jsonb;
            route text;
            media_key text;
            media_id uuid;
            media_row record;
            page_docs jsonb := '[]'::jsonb;
            media_docs jsonb := '{}'::jsonb;
            doc jsonb;
        BEGIN
            SELECT * INTO ws FROM control.workspace
            WHERE id = p_workspace_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'REVIEW_WORKSPACE_NOT_FOUND'
                    USING ERRCODE = 'P0002';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM control.site AS site
                WHERE site.id = ws.site_id AND site.status = 'ACTIVE'
            ) THEN
                RAISE EXCEPTION 'REVIEW_SITE_NOT_ACTIVE'
                    USING ERRCODE = 'P0002';
            END IF;
            PERFORM pg_advisory_xact_lock(
                hashtextextended(p_workspace_id::text, 280)
            );
            -- 083/4 freeze-time coherence: lock the canonical site row
            -- after the workspace lock (the same workspace-then-site
            -- order the acceptance verification path uses) and capture
            -- its revision and status in this single locked read,
            -- before the COW context/content read. The pre-lock ACTIVE
            -- EXISTS above is a fast fail only: if this wait spans an
            -- authorized archive/status change, the locked-row
            -- re-check below is the fail-closed guard.
            SELECT canonical_revision, status
              INTO site_revision, site_status
              FROM control.site WHERE id = ws.site_id FOR UPDATE;
            IF site_status IS DISTINCT FROM 'ACTIVE' THEN
                RAISE EXCEPTION 'REVIEW_SITE_NOT_ACTIVE'
                    USING ERRCODE = 'P0002';
            END IF;
            -- The row lock is xact-level: the caller holds it through
            -- snapshot completion and the job terminal (freeze) or the
            -- preflight re-validation (acceptance).
            PERFORM set_config('app.session_id', p_workspace_id::text, true);
            SELECT site_key, display_name, default_locale,
                   component_catalog_version
              INTO site_row
              FROM control.site WHERE id = ws.site_id;

            FOR page_row IN
                SELECT p.*
                FROM content.page AS p
                WHERE p.site_id = ws.site_id
                  AND p.deleted_at IS NULL
                  AND p.status IN ('PUBLISHED','DRAFT')
                ORDER BY p.locale COLLATE "C", p.slug COLLATE "C", p.id
            LOOP
                BEGIN
                    route := content.slaif_agent_page_effective_route(
                        page_row.id
                    );
                EXCEPTION WHEN OTHERS THEN
                    route := NULL;
                END;
                SELECT coalesce(
                    jsonb_agg(row_to_json(c) ORDER BY c.slot_key, c.order_key,
                               c.id),
                    '[]'::jsonb
                ) INTO nodes_row
                FROM (SELECT * FROM content.page_composition AS c
                      WHERE c.site_id = ws.site_id
                        AND c.page_id = page_row.id) AS c;
                -- Collect the media references of this page's composition.
                IF nodes_row IS NOT NULL THEN
                    FOR node_props IN
                        SELECT c2.props FROM content.page_composition AS c2
                        WHERE c2.site_id = ws.site_id
                          AND c2.page_id = page_row.id
                    LOOP
                        IF node_props IS NULL THEN
                            CONTINUE;
                        END IF;
                        IF jsonb_typeof(node_props -> 'mediaId') = 'string' THEN
                            BEGIN
                                media_id := (node_props ->> 'mediaId')::uuid;
                                media_key := media_id::text;
                                IF not (media_docs ? media_key) THEN
                                    SELECT * INTO media_row
                                    FROM content.slaif_render_media_resolve(
                                        ws.site_id, media_id
                                    );
                                    IF FOUND THEN
                                        media_docs := media_docs || jsonb_build_object(
                                            media_key, jsonb_build_object(
                                                'id', media_id,
                                                'mime_type', media_row.mime_type,
                                                'size_bytes',
                                                    media_row.size_bytes,
                                                'content_hash',
                                                    media_row.content_hash,
                                                'public_status',
                                                    media_row.public_status
                                            )
                                        );
                                    END IF;
                                END IF;
                            EXCEPTION WHEN invalid_text_representation THEN
                                NULL;
                            END;
                        END IF;
                        IF jsonb_typeof(node_props -> 'items') = 'array' THEN
                            FOR media_key IN
                                SELECT item ->> 'mediaId'
                                FROM jsonb_array_elements(
                                    node_props -> 'items'
                                ) AS item
                                WHERE jsonb_typeof(item -> 'mediaId')
                                      = 'string'
                            LOOP
                                BEGIN
                                    media_id := media_key::uuid;
                                    media_key := media_id::text;
                                    IF not (media_docs ? media_key) THEN
                                        SELECT * INTO media_row
                                        FROM content.slaif_render_media_resolve(
                                            ws.site_id, media_id
                                        );
                                        IF FOUND THEN
                                            media_docs := media_docs || jsonb_build_object(
                                                media_key, jsonb_build_object(
                                                    'id', media_id,
                                                    'mime_type',
                                                        media_row.mime_type,
                                                    'size_bytes',
                                                        media_row.size_bytes,
                                                    'content_hash',
                                                        media_row.content_hash,
                                                    'public_status',
                                                        media_row.public_status
                                                )
                                            );
                                        END IF;
                                    END IF;
                                EXCEPTION WHEN invalid_text_representation THEN
                                    NULL;
                                END;
                            END LOOP;
                        END IF;
                    END LOOP;
                END IF;
                page_docs := page_docs || jsonb_build_object(
                    'id', page_row.id,
                    'site_id', page_row.site_id,
                    'slug', page_row.slug,
                    'title', page_row.title,
                    'status', page_row.status,
                    'locale', page_row.locale,
                    'parent_id', page_row.parent_id,
                    'route_template', page_row.route_template,
                    'effective_route', route,
                    'row_version', page_row.row_version,
                    'nodes', nodes_row
                );
            END LOOP;

            doc := jsonb_build_object(
                'state_version', 'review-snapshot/v1',
                'workspace_id', p_workspace_id,
                'site_id', ws.site_id,
                'site', jsonb_build_object(
                    'site_key', site_row.site_key,
                    'display_name', site_row.display_name,
                    'default_locale', site_row.default_locale,
                    'component_catalog_version',
                        site_row.component_catalog_version
                ),
                'base_site_revision', site_revision,
                'operation_watermark', ws.operation_watermark,
                'locales', (
                    SELECT coalesce(
                        jsonb_agg(jsonb_build_object(
                            'tag', l.tag, 'enabled', l.enabled,
                            'is_default', l.is_default, 'position', l.position
                        ) ORDER BY l.position, l.tag COLLATE "C"),
                        '[]'::jsonb
                    )
                    FROM content.site_locale AS l
                    WHERE l.site_id = ws.site_id
                ),
                'theme', (
                    SELECT row_to_json(t)
                    FROM content.slaif_theme_project(ws.site_id) AS t
                ),
                'regions', (
                    SELECT coalesce(
                        jsonb_agg(row_to_json(r)
                            ORDER BY r.region_key, r.variant),
                        '[]'::jsonb
                    )
                    FROM content.slaif_region_list(ws.site_id) AS r
                ),
                'navigation', jsonb_build_object(
                    'definitions', (
                        SELECT coalesce(
                            jsonb_agg(row_to_json(d)
                                ORDER BY d.key COLLATE "C"),
                            '[]'::jsonb
                        )
                        FROM content.navigation AS d
                        WHERE d.site_id = ws.site_id
                    ),
                    'items', (
                        SELECT coalesce(
                            jsonb_agg(row_to_json(n)
                                ORDER BY n.navigation_id, n."position", n.id),
                            '[]'::jsonb
                        )
                        FROM content.slaif_render_navigation_items(
                            ws.site_id, site_row.default_locale,
                            ARRAY['PUBLISHED','DRAFT']
                        ) AS n
                    )
                ),
                'redirects', (
                    SELECT coalesce(
                        jsonb_agg(row_to_json(rd)
                            ORDER BY rd.source_route COLLATE "C",
                                     rd.locale NULLS FIRST),
                        '[]'::jsonb
                    )
                    FROM (SELECT id, site_id, source_route, target,
                                 status_code, locale
                          FROM content.redirect
                          WHERE site_id = ws.site_id) AS rd
                ),
                'pages', page_docs,
                'media', media_docs
            );
            RETURN doc;
        END;
        $fn$
        """


def _assert_ownership_and_acl() -> None:
    """Re-assert the exact 070_001 ownership/ACL (unchanged by the swap)."""

    op.execute(f"ALTER FUNCTION {_WORKSPACE_STATE} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_WORKSPACE_STATE} FROM PUBLIC")
    for role in _REVOKE_ROLES:
        op.execute(f"REVOKE ALL ON FUNCTION {_WORKSPACE_STATE} FROM {role}")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_WORKSPACE_STATE} TO slaif_review_worker")


def upgrade() -> None:
    op.execute(_MATERIALIZER_075)
    _assert_ownership_and_acl()


def downgrade() -> None:
    op.execute(_MATERIALIZER_070)
    _assert_ownership_and_acl()
