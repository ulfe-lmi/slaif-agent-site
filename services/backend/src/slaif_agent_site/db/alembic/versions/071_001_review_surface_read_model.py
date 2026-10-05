# ruff: noqa: E501
"""Trusted read-only review surface (082/2).

Creates exactly three functions and nothing else:

1. ``control.slaif_review_read_model`` - one deterministic, read-only
   review document (snapshot identity + drift + semantic timeline +
   bounded resource diff + summaries + frozen validation + evidence +
   metadata, plus the verbatim snapshot ``normalized_state`` so the web
   review render mode can build its projection from the read path only).
   EXECUTE for ``slaif_control`` only; SELECT only; no table-grant
   changes.
2. ``control.slaif_human_session_review_artifact_list`` and
   ``control.slaif_human_session_review_artifact_retrieve`` - the
   minimal read-only 072 retrieval gating extension: the same artifact
   rows/worker bindings as the capability-scoped routes, additionally
   reachable by a valid human session whose user is a site member (or
   platform administrator) of a site whose workspace is in REVIEW.
   EXECUTE for ``slaif_agent_runtime`` only.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "071_001"
down_revision: str | Sequence[str] | None = "070_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_READ_MODEL_FUNCTION = "control.slaif_review_read_model(uuid, uuid, uuid)"
_HUMAN_ARTIFACT_LIST_FUNCTION = (
    "control.slaif_human_session_review_artifact_list(text, bytea, uuid)"
)
_HUMAN_ARTIFACT_RETRIEVE_FUNCTION = (
    "control.slaif_human_session_review_artifact_retrieve(text, bytea, uuid, uuid)"
)

# Every non-owner privilege role: EXECUTE must be revoked from all of
# them; the grants below re-add exactly one allowed caller per function.
_LONG_LIVED_ROLES = (
    "slaif_control",
    "slaif_editor_runtime",
    "slaif_agent_runtime",
    "slaif_public_reader",
    "slaif_preview_reader",
    "slaif_reviewer",
    "slaif_review_worker",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
)

# The 16 COW change tables (foundation per-session operation log) in a
# fixed family order.  Family keys are the stable document keys used by
# the timeline ``resource`` lists and the ``resource_diff`` object.
_CHANGE_FAMILIES: tuple[tuple[str, str], ...] = (
    ("pages", "page_changes"),
    ("composition_nodes", "page_composition_changes"),
    ("items", "content_item_changes"),
    ("fields", "field_definition_changes"),
    ("content_types", "content_type_changes"),
    ("translations", "content_item_translation_changes"),
    ("relations", "item_relation_changes"),
    ("collection_views", "collection_view_changes"),
    ("theme", "theme_changes"),
    ("navigation", "navigation_changes"),
    ("navigation_items", "navigation_item_changes"),
    ("redirects", "redirect_changes"),
    ("media_assets", "media_asset_changes"),
    ("global_regions", "site_global_region_changes"),
    ("locales", "site_locale_changes"),
    ("proposed_side_effects", "proposed_side_effect_changes"),
)

# Foundation change-table columns that never belong to the product row.
_RESERVED_CHANGE_KEYS = (
    "'session_id','operation_id','_cow_deleted','_cow_updated_at',"
    "'_cow_order','_cow_base_exists','_cow_base_row','_cow_base_schema'"
)

# Write-time bookkeeping that changes on every rewrite; excluded from the
# field-level diff (still present in the full added/deleted rows).
_DIFF_NOISE_KEYS = "'updated_at','row_version'"


def _timeline_ops_all_sql() -> str:
    parts = []
    for family, changes_table in _CHANGE_FAMILIES:
        parts.append(
            "SELECT $family$ AS family, operation_id, _cow_order,"
            " _cow_updated_at, _cow_deleted FROM content.{table} "
            "WHERE session_id = p_workspace_id AND _cow_updated_at"
            " <= p_boundary".replace("$family$", repr(family)).format(
                table=changes_table
            )
        )
    return "\n            UNION ALL ".join(parts)


def _family_entry_sql(family: str, changes_table: str) -> str:
    """One ``'family_key', <scalar subquery>`` argument pair.

    Levels: ``final_row`` (latest change row per id, watermark-bounded)
    -> ``shaped`` (product-only ``current_json``) -> ``diffed`` (adds the
    one-level ``field_diff`` against ``_cow_base_row``; a separate level
    because a SELECT-list alias cannot be referenced by another
    expression of the same SELECT list).  The three buckets are one
    aggregate pass with CASE (a SELECT-list subquery cannot put the
    outer query's own FROM item in its own FROM clause).
    """

    return (
        repr(family)
        + ", "
        + f"""(
            SELECT jsonb_build_object(
                'added', coalesce(
                    jsonb_agg(current_json ORDER BY id)
                        FILTER (
                            WHERE NOT _cow_base_exists
                              AND NOT _cow_deleted),
                    '[]'::jsonb),
                'modified', coalesce(
                    jsonb_agg(
                        jsonb_build_object('id', id, 'fields', field_diff)
                        ORDER BY id)
                        FILTER (
                            WHERE _cow_base_exists
                              AND NOT _cow_deleted
                              AND field_diff <> '{{}}'::jsonb),
                    '[]'::jsonb),
                'deleted', coalesce(
                    jsonb_agg(current_json ORDER BY id)
                        FILTER (
                            WHERE _cow_deleted AND _cow_base_exists),
                    '[]'::jsonb)
            )
            FROM (
                SELECT id, _cow_deleted, _cow_base_exists, current_json,
                    (SELECT coalesce(
                        jsonb_object_agg(
                            kk.k,
                            jsonb_build_object(
                                'before',
                                coalesce(_cow_base_row, '{{}}'::jsonb) -> kk.k,
                                'after', diff_after -> kk.k
                            ) ORDER BY kk.k
                        ), '{{}}'::jsonb)
                     FROM (
                        SELECT k FROM jsonb_object_keys(
                            coalesce(_cow_base_row, '{{}}'::jsonb)) AS k
                            WHERE k NOT IN ({_DIFF_NOISE_KEYS})
                        UNION
                        SELECT k FROM jsonb_object_keys(diff_after) AS k
                     ) AS kk(k)
                     WHERE coalesce(_cow_base_row, '{{}}'::jsonb) -> kk.k
                           IS DISTINCT FROM diff_after -> kk.k
                    ) AS field_diff
                FROM (
                    SELECT id, _cow_deleted, _cow_base_exists, _cow_base_row,
                        (SELECT jsonb_object_agg(kv.k, kv.v)
                         FROM jsonb_each(full_row) AS kv(k, v)
                         WHERE kv.k NOT IN ({_RESERVED_CHANGE_KEYS})
                        ) AS current_json,
                        (SELECT jsonb_object_agg(kv.k, kv.v)
                         FROM jsonb_each(full_row) AS kv(k, v)
                         WHERE kv.k NOT IN ({_RESERVED_CHANGE_KEYS})
                           AND kv.k NOT IN ({_DIFF_NOISE_KEYS})
                        ) AS diff_after
                    FROM (
                        SELECT DISTINCT ON (id) id, _cow_deleted,
                            _cow_base_exists, _cow_base_row,
                            row_to_json(r)::jsonb AS full_row
                        FROM content.{changes_table} AS r
                        WHERE session_id = p_workspace_id
                          AND _cow_updated_at <= p_boundary
                        ORDER BY id, _cow_order DESC
                    ) AS final_row
                ) AS shaped
            ) AS diffed
        )"""
    )


def _read_model_function_sql() -> str:
    ops_all = _timeline_ops_all_sql()
    family_entries = ",\n        ".join(
        _family_entry_sql(family, changes_table)
        for family, changes_table in _CHANGE_FAMILIES
    )
    return f"""
        CREATE FUNCTION control.slaif_review_read_model(
            p_workspace_id uuid, p_site_id uuid, p_user_account_id uuid
        ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER STABLE
        SET search_path = pg_catalog AS $fn$
        DECLARE
            ws control.workspace%ROWTYPE;
            snapshot_row control.review_snapshot%ROWTYPE;
            site_row record;
            current_revision bigint;
            p_boundary timestamptz;
            timeline_json jsonb;
            drift_equal boolean;
            composition_counts jsonb := '{{}}'::jsonb;
            component_types text[] := ARRAY[]::text[];
            page_doc jsonb;
            node_doc jsonb;
            doc jsonb;
        BEGIN
            -- ------------------------------------------------------------------
            -- Gating: fail closed with one stable internal class; the HTTP
            -- layer maps every gate failure to the same uniform 404, so no
            -- oracle distinguishes "not a member", "unknown id", "wrong
            -- site", and "no snapshot".
            -- ------------------------------------------------------------------
            IF p_workspace_id IS NULL OR p_site_id IS NULL
               OR p_user_account_id IS NULL
               OR NOT EXISTS (
                   SELECT 1 FROM control.site WHERE id = p_site_id
               ) THEN
                RAISE EXCEPTION 'REVIEW_READ_UNAVAILABLE'
                    USING ERRCODE = 'P0002';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM control.platform_administrator
                WHERE user_account_id = p_user_account_id
            ) AND NOT EXISTS (
                SELECT 1 FROM control.slaif_effective_human_membership(
                    p_user_account_id, p_site_id
                )
            ) THEN
                RAISE EXCEPTION 'REVIEW_READ_UNAVAILABLE'
                    USING ERRCODE = 'P0002';
            END IF;
            SELECT * INTO ws FROM control.workspace
            WHERE id = p_workspace_id;
            IF NOT FOUND OR ws.site_id IS DISTINCT FROM p_site_id THEN
                RAISE EXCEPTION 'REVIEW_READ_UNAVAILABLE'
                    USING ERRCODE = 'P0002';
            END IF;
            SELECT * INTO snapshot_row FROM control.review_snapshot
            WHERE workspace_id = p_workspace_id AND status = 'COMPLETE';
            IF NOT FOUND THEN
                RAISE EXCEPTION 'REVIEW_READ_UNAVAILABLE'
                    USING ERRCODE = 'P0002';
            END IF;

            -- ------------------------------------------------------------------
            -- Consistent read: the workspace is out of ACTIVE (frozen), so
            -- the COW session is closed; a short shared advisory lock (the
            -- workspace lifecycle key 280, shared variant only - never
            -- exclusive) keeps the COW view read consistent with any
            -- future transition and the established materializer pattern.
            -- ------------------------------------------------------------------
            PERFORM pg_advisory_xact_lock_shared(
                hashtextextended(p_workspace_id::text, 280)
            );
            PERFORM set_config('app.session_id', p_workspace_id::text, true);

            SELECT site_key INTO site_row FROM control.site
            WHERE id = p_site_id;
            SELECT canonical_revision INTO current_revision
            FROM control.site WHERE id = p_site_id;
            p_boundary := snapshot_row.created_at;
            drift_equal := current_revision
                = (snapshot_row.normalized_state->>'base_site_revision')::bigint;

            -- Deterministic composition-by-component-type counts sourced
            -- from the frozen snapshot node trees.
            FOR page_doc IN
                SELECT * FROM jsonb_array_elements(
                    snapshot_row.normalized_state->'pages')
            LOOP
                FOR node_doc IN
                    SELECT * FROM jsonb_path_query(
                        page_doc, '$.nodes[*].**')
                LOOP
                    IF jsonb_typeof(node_doc) = 'object'
                       AND node_doc ? 'component_type'
                       AND jsonb_typeof(node_doc->'component_type') = 'string'
                    THEN
                        component_types := array_append(
                            component_types,
                            node_doc->>'component_type'
                        );
                    END IF;
                END LOOP;
            END LOOP;
            SELECT coalesce(
                jsonb_object_agg(
                    t.component_type, t.n ORDER BY t.component_type
                ), '{{}}'::jsonb
            ) INTO composition_counts
            FROM (SELECT component_type, count(*) AS n
                  FROM unnest(component_types) AS component_type
                  GROUP BY component_type) AS t;

            -- Semantic timeline: one entry per distinct operation of the
            -- frozen COW session, ordered by the foundation's shared
            -- deterministic operation-order sequence, then operation id.
            -- Watermark boundary: an operation is included only when every
            -- one of its change rows was written at or before the snapshot
            -- row committed (the freeze transaction holds the exclusive
            -- workspace lifecycle lock, so real operations cannot straddle
            -- the boundary).
            WITH ops_all AS (
                {ops_all}
            )
            SELECT coalesce(jsonb_agg(
                jsonb_build_object(
                    'operation_id', ops.operation_id,
                    'operation_type', (
                        SELECT string_agg(entry, ', ' ORDER BY entry)
                        FROM (
                            SELECT DISTINCT family || ':' ||
                                CASE WHEN _cow_deleted
                                     THEN 'delete' ELSE 'upsert' END
                                AS entry
                            FROM ops_all
                            WHERE operation_id = ops.operation_id
                        ) AS entries
                    ),
                    'resource', (
                        SELECT coalesce(
                            jsonb_agg(family ORDER BY family),
                            '[]'::jsonb
                        )
                        FROM (
                            SELECT DISTINCT family FROM ops_all
                            WHERE operation_id = ops.operation_id
                        ) AS fams
                    ),
                    'created_at', ops.created_at
                ) ORDER BY ops.min_order, ops.operation_id
            ), '[]'::jsonb) INTO timeline_json
            FROM (
                SELECT operation_id,
                    min(_cow_order) AS min_order,
                    min(_cow_updated_at) AS created_at
                FROM ops_all
                GROUP BY operation_id
                HAVING max(_cow_updated_at) <= p_boundary
            ) AS ops;

            doc := jsonb_build_object(
                'snapshot', jsonb_build_object(
                    'id', snapshot_row.id,
                    'digest', snapshot_row.digest,
                    'state_version',
                        snapshot_row.normalized_state->>'state_version',
                    'revision_watermark', snapshot_row.revision_watermark,
                    'base_site_revision',
                        (snapshot_row.normalized_state
                            ->>'base_site_revision')::bigint,
                    'status', snapshot_row.status,
                    'created_at', to_jsonb(snapshot_row.created_at),
                    'created_by', snapshot_row.created_by,
                    'versions', snapshot_row.versions
                ),
                'drift', jsonb_build_object(
                    'current_site_revision', current_revision,
                    'base_site_revision',
                        (snapshot_row.normalized_state
                            ->>'base_site_revision')::bigint,
                    'equal', drift_equal
                ),
                'timeline', timeline_json,
                'resource_diff', jsonb_build_object(
        {family_entries}
                ),
                'summaries', jsonb_build_object(
                    'model', jsonb_build_object(
                        'content_types',
                        (SELECT count(*) FROM content.content_type
                         WHERE site_id = p_site_id)
                    ),
                    'fields', jsonb_build_object(
                        'total',
                            (SELECT count(*) FROM content.field_definition
                             WHERE site_id = p_site_id),
                        'by_type', (
                            SELECT coalesce(
                                jsonb_object_agg(
                                    type_id::text, n ORDER BY type_id::text
                                ), '{{}}'::jsonb
                            )
                            FROM (SELECT type_id, count(*) AS n
                                  FROM content.field_definition
                                  WHERE site_id = p_site_id
                                  GROUP BY type_id) AS ft
                        )
                    ),
                    'mappings', jsonb_build_object(
                        'type_field_mappings',
                        (SELECT count(*) FROM content.field_definition
                         WHERE site_id = p_site_id)
                    ),
                    'items', jsonb_build_object(
                        'items',
                            (SELECT count(*) FROM content.content_item
                             WHERE site_id = p_site_id),
                        'relations',
                            (SELECT count(*) FROM content.item_relation
                             WHERE site_id = p_site_id),
                        'translations',
                            (SELECT count(*)
                             FROM content.content_item_translation
                             WHERE site_id = p_site_id),
                        'collection_views',
                            (SELECT count(*) FROM content.collection_view
                             WHERE site_id = p_site_id)
                    ),
                    'resource_inventory', jsonb_build_object(
                        'pages',
                            (SELECT count(*) FROM content.page
                             WHERE site_id = p_site_id),
                        'composition_nodes',
                            (SELECT count(*) FROM content.page_composition
                             WHERE site_id = p_site_id),
                        'media_assets',
                            (SELECT count(*) FROM content.media_asset
                             WHERE site_id = p_site_id),
                        'navigation_definitions',
                            (SELECT count(*) FROM content.navigation
                             WHERE site_id = p_site_id),
                        'navigation_items',
                            (SELECT count(*) FROM content.navigation_item
                             WHERE site_id = p_site_id),
                        'redirects',
                            (SELECT count(*) FROM content.redirect
                             WHERE site_id = p_site_id),
                        'global_regions',
                            (SELECT count(*) FROM content.site_global_region
                             WHERE site_id = p_site_id),
                        'locales',
                            (SELECT count(*) FROM content.site_locale
                             WHERE site_id = p_site_id)
                    ),
                    'composition_by_component_type', composition_counts,
                    'theme', jsonb_build_object(
                        'token_groups', (
                            SELECT coalesce(
                                jsonb_agg(g.k ORDER BY g.k), '[]'::jsonb
                            )
                            FROM (VALUES ('palette'), ('typography'),
                                  ('layout'), ('shape')) AS g(k)
                            WHERE coalesce(
                                    snapshot_row.normalized_state->'theme',
                                    '{{}}'::jsonb) ? g.k
                              AND jsonb_typeof(
                                  coalesce(
                                      snapshot_row.normalized_state
                                          ->'theme',
                                      '{{}}'::jsonb) -> g.k)
                                  IN ('object', 'array')
                        )
                    ),
                    'navigation', jsonb_build_object(
                        'definitions', jsonb_array_length(
                            coalesce(
                                snapshot_row.normalized_state
                                    ->'navigation'->'definitions',
                                '[]'::jsonb)),
                        'items', jsonb_array_length(
                            coalesce(
                                snapshot_row.normalized_state
                                    ->'navigation'->'items',
                                '[]'::jsonb))
                    ),
                    'redirects', jsonb_array_length(
                        coalesce(
                            snapshot_row.normalized_state->'redirects',
                            '[]'::jsonb)
                    ),
                    'media', jsonb_build_object(
                        'assets', (
                            SELECT count(*)
                            FROM jsonb_object_keys(
                                coalesce(
                                    snapshot_row.normalized_state
                                        ->'media', '{{}}'::jsonb))
                        ),
                        'by_public_status', (
                            SELECT coalesce(
                                jsonb_object_agg(
                                    m.status, m.n ORDER BY m.status
                                ), '{{}}'::jsonb
                            )
                            FROM (SELECT (value->>'public_status')
                                      AS status, count(*) AS n
                                  FROM jsonb_each(
                                      coalesce(
                                          snapshot_row.normalized_state
                                              ->'media', '{{}}'::jsonb))
                                  GROUP BY 1) AS m
                        ),
                        'references', jsonb_array_length(
                            coalesce(
                                snapshot_row.media_references,
                                '[]'::jsonb))
                    ),
                    'responsive', jsonb_build_object(
                        'enabled_locales', jsonb_array_length(
                            coalesce(
                                snapshot_row.normalized_state->'locales',
                                '[]'::jsonb)),
                        'default_locale',
                            snapshot_row.normalized_state->'site'
                                ->>'default_locale'
                    )
                ),
                'validation', jsonb_build_object(
                    'report', snapshot_row.validation_report,
                    'warnings', (
                        SELECT coalesce(
                            jsonb_agg(
                                w.warning ORDER BY
                                w.warning->>'kind',
                                w.warning->>'detail'
                            ), '[]'::jsonb
                        )
                        FROM (
                            SELECT jsonb_build_object(
                                'kind', 'validation_error',
                                'detail', err
                            ) AS warning
                            FROM jsonb_array_elements(
                                coalesce(
                                    snapshot_row.validation_report
                                        ->'errors', '[]'::jsonb)) AS err
                            UNION ALL
                            SELECT jsonb_build_object(
                                'kind', 'cancelled_by_freeze',
                                'detail', c->>'id'
                            ) AS warning
                            FROM jsonb_array_elements(
                                coalesce(
                                    snapshot_row.validation_report
                                        ->'cancelled_by_freeze',
                                    '[]'::jsonb)) AS c
                        ) AS w
                    )
                ),
                'evidence', jsonb_build_object(
                    'runs', snapshot_row.browser_evidence,
                    'artifacts', (
                        SELECT coalesce(
                            jsonb_agg(
                                jsonb_build_object(
                                    'run_id', ev.run_id,
                                    'artifacts', (
                                        SELECT coalesce(
                                            jsonb_agg(
                                                jsonb_build_object(
                                                    'contract_version',
                                                        run.contract_version,
                                                    'artifact_id',
                                                        artifact.id,
                                                    'run_id',
                                                        artifact.run_id,
                                                    'kind',
                                                        artifact.kind,
                                                    'mime_type',
                                                        artifact.mime_type,
                                                    'sha256',
                                                        artifact.sha256,
                                                    'size_bytes',
                                                        artifact.size_bytes,
                                                    'target',
                                                        artifact.target,
                                                    'route_digest',
                                                        artifact.route_digest,
                                                    'created_at',
                                                        to_jsonb(
                                                            artifact.created_at),
                                                    'expires_at',
                                                        to_jsonb(
                                                            artifact.expires_at),
                                                    'visibility',
                                                        artifact.visibility
                                                )
                                                ORDER BY
                                                    artifact.created_at,
                                                    artifact.id
                                            ), '[]'::jsonb
                                        )
                                        FROM control.browser_artifact
                                            AS artifact
                                        JOIN control.browser_run AS run
                                            ON run.id = artifact.run_id
                                        WHERE artifact.run_id = ev.run_id
                                          AND run.site_id = p_site_id
                                          AND artifact.visibility
                                              = 'PRIVATE'
                                          AND run.expires_at
                                              > CURRENT_TIMESTAMP
                                          AND artifact.expires_at
                                              > CURRENT_TIMESTAMP
                                    )
                                )
                                ORDER BY ev.run_id
                            ), '[]'::jsonb
                        )
                        FROM (
                            SELECT (value->>'id')::uuid AS run_id
                            FROM jsonb_array_elements(
                                snapshot_row.browser_evidence)
                        ) AS ev
                    )
                ),
                'metadata', jsonb_build_object(
                    'workspace', jsonb_build_object(
                        'id', ws.id,
                        'title', ws.title,
                        'actor_type', ws.actor_type,
                        'status', ws.status
                    ),
                    'site', jsonb_build_object(
                        'id', p_site_id,
                        'key', site_row.site_key
                    ),
                    'capabilities', (
                        SELECT coalesce(
                            jsonb_agg(
                                jsonb_build_object(
                                    'id', capability.id,
                                    'scopes', capability.scopes,
                                    'created_at',
                                        to_jsonb(capability.created_at),
                                    'expires_at',
                                        to_jsonb(capability.expires_at),
                                    'revoked_at',
                                        to_jsonb(capability.revoked_at)
                                )
                                ORDER BY capability.id
                            ), '[]'::jsonb
                        )
                        FROM control.capability
                        WHERE workspace_id = p_workspace_id
                    ),
                    'quota_policy', jsonb_build_object(
                        'request_quota', ws.request_quota,
                        'mutation_quota', ws.mutation_quota,
                        'delete_quota', ws.delete_quota,
                        'upload_quota', ws.upload_quota,
                        'browser_quota', ws.browser_quota,
                        'resource_constraints', ws.resource_constraints
                    ),
                    'agent_session_browser', jsonb_build_object(
                        'versions', snapshot_row.versions,
                        'review_jobs', (
                            SELECT coalesce(
                                jsonb_agg(
                                    jsonb_build_object(
                                        'id', job.id,
                                        'job_kind', job.job_kind,
                                        'status', job.status,
                                        'attempt_count',
                                            job.attempt_count,
                                        'error', job.error,
                                        'created_at',
                                            to_jsonb(job.created_at),
                                        'updated_at',
                                            to_jsonb(job.updated_at)
                                    )
                                    ORDER BY job.id
                                ), '[]'::jsonb
                            )
                            FROM control.review_job AS job
                            WHERE job.workspace_id = p_workspace_id
                        )
                    )
                ),
                'normalized_state', snapshot_row.normalized_state
            );
            RETURN doc;
        END;
        $fn$
    """


def _human_artifact_list_function_sql() -> str:
    return """
        CREATE FUNCTION control.slaif_human_session_review_artifact_list(
            p_public_id text, p_secret_digest bytea, p_run_id uuid
        ) RETURNS TABLE (
            contract_version text, artifact_id uuid, run_id uuid, kind text,
            mime_type text, sha256 text, size_bytes bigint, target text,
            route_digest text, created_at timestamptz, expires_at timestamptz,
            visibility text
        ) LANGUAGE plpgsql SECURITY DEFINER STABLE
        SET search_path = pg_catalog AS $fn$
        DECLARE
            session_row record;
            user_id uuid;
            run_site uuid;
            run_workspace uuid;
        BEGIN
            -- Validated human session (exact product read policy: digest
            -- match, account ACTIVE, not revoked, idle/absolute expiry).
            -- ANY failure yields no row (uniform, no oracle).
            SELECT * INTO session_row
            FROM control.slaif_finalize_human_session(
                p_public_id, p_secret_digest, 1800, 300, 900
            );
            IF NOT FOUND THEN
                RETURN;
            END IF;
            user_id := session_row.user_account_id;
            -- The run's own site is the only site considered (no
            -- client-supplied site): the run must belong to a workspace
            -- frozen in REVIEW of that same site.
            SELECT run.site_id, run.workspace_id
                INTO run_site, run_workspace
            FROM control.browser_run AS run
            WHERE run.id = p_run_id;
            IF NOT FOUND THEN
                RETURN;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM control.workspace AS workspace
                WHERE workspace.id = run_workspace
                  AND workspace.site_id = run_site
                  AND workspace.status = 'REVIEW'
            ) THEN
                RETURN;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM control.platform_administrator
                WHERE user_account_id = user_id
            ) AND NOT EXISTS (
                SELECT 1 FROM control.slaif_effective_human_membership(
                    user_id, run_site
                )
            ) THEN
                RETURN;
            END IF;
            RETURN QUERY
                SELECT run.contract_version, artifact.id, artifact.run_id,
                    artifact.kind, artifact.mime_type, artifact.sha256,
                    artifact.size_bytes, artifact.target,
                    artifact.route_digest, artifact.created_at,
                    artifact.expires_at, artifact.visibility
                FROM control.browser_artifact AS artifact
                JOIN control.browser_run AS run
                    ON run.id = artifact.run_id
                WHERE run.id = p_run_id
                  AND run.site_id = run_site
                  AND run.expires_at > CURRENT_TIMESTAMP
                  AND artifact.expires_at > CURRENT_TIMESTAMP
                  AND artifact.visibility = 'PRIVATE'
                ORDER BY artifact.created_at, artifact.id;
        END;
        $fn$
    """


def _human_artifact_retrieve_function_sql() -> str:
    return """
        CREATE FUNCTION control.slaif_human_session_review_artifact_retrieve(
            p_public_id text, p_secret_digest bytea, p_run_id uuid,
            p_artifact_id uuid
        ) RETURNS TABLE (
            worker_request_id uuid, run_id uuid, site_id uuid,
            workspace_id uuid, artifact_id uuid, kind text, mime_type text,
            sha256 text, size_bytes bigint, target text, route_digest text,
            created_at timestamptz, expires_at timestamptz, visibility text
        ) LANGUAGE plpgsql SECURITY DEFINER STABLE
        SET search_path = pg_catalog AS $fn$
        DECLARE
            session_row record;
            user_id uuid;
            run_site uuid;
            run_workspace uuid;
        BEGIN
            SELECT * INTO session_row
            FROM control.slaif_finalize_human_session(
                p_public_id, p_secret_digest, 1800, 300, 900
            );
            IF NOT FOUND THEN
                RETURN;
            END IF;
            user_id := session_row.user_account_id;
            SELECT run.site_id, run.workspace_id
                INTO run_site, run_workspace
            FROM control.browser_run AS run
            WHERE run.id = p_run_id;
            IF NOT FOUND THEN
                RETURN;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM control.workspace AS workspace
                WHERE workspace.id = run_workspace
                  AND workspace.site_id = run_site
                  AND workspace.status = 'REVIEW'
            ) THEN
                RETURN;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM control.platform_administrator
                WHERE user_account_id = user_id
            ) AND NOT EXISTS (
                SELECT 1 FROM control.slaif_effective_human_membership(
                    user_id, run_site
                )
            ) THEN
                RETURN;
            END IF;
            RETURN QUERY
                SELECT artifact.worker_request_id, artifact.run_id,
                    artifact.site_id, artifact.workspace_id, artifact.id,
                    artifact.kind, artifact.mime_type, artifact.sha256,
                    artifact.size_bytes, artifact.target,
                    artifact.route_digest, artifact.created_at,
                    artifact.expires_at, artifact.visibility
                FROM control.browser_artifact AS artifact
                JOIN control.browser_run AS run
                    ON run.id = artifact.run_id
                WHERE artifact.id = p_artifact_id
                  AND run.id = p_run_id
                  AND artifact.run_id = p_run_id
                  AND artifact.site_id = run_site
                  AND run.site_id = run_site
                  AND run.workspace_id = artifact.workspace_id
                  AND run.state = 'COMPLETED'
                  AND run.expires_at > CURRENT_TIMESTAMP
                  AND artifact.expires_at > CURRENT_TIMESTAMP
                  AND artifact.visibility = 'PRIVATE';
        END;
        $fn$
    """


def upgrade() -> None:
    op.execute(_read_model_function_sql())
    op.execute(_human_artifact_list_function_sql())
    op.execute(_human_artifact_retrieve_function_sql())

    op.execute(f"ALTER FUNCTION {_READ_MODEL_FUNCTION} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_READ_MODEL_FUNCTION} FROM PUBLIC")
    for role in _LONG_LIVED_ROLES:
        op.execute(f"REVOKE ALL ON FUNCTION {_READ_MODEL_FUNCTION} FROM {role}")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_READ_MODEL_FUNCTION} TO slaif_control")

    for function in (
        _HUMAN_ARTIFACT_LIST_FUNCTION,
        _HUMAN_ARTIFACT_RETRIEVE_FUNCTION,
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        for role in _LONG_LIVED_ROLES:
            op.execute(f"REVOKE ALL ON FUNCTION {function} FROM {role}")
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_agent_runtime")


def downgrade() -> None:
    # Drop exactly what this migration created.
    op.execute(f"DROP FUNCTION IF EXISTS {_HUMAN_ARTIFACT_RETRIEVE_FUNCTION}")
    op.execute(f"DROP FUNCTION IF EXISTS {_HUMAN_ARTIFACT_LIST_FUNCTION}")
    op.execute(f"DROP FUNCTION IF EXISTS {_READ_MODEL_FUNCTION}")
