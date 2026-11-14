# ruff: noqa: E501
"""Reviewed whole-session operation binding (083/12).

A logical reviewed snapshot becomes the pair: the existing immutable
``review-snapshot/v2`` domain row PLUS one immutable one-to-one companion
``control.review_operation_manifest`` row created atomically in the SAME
freeze transaction.  The manifest records the actual public foundation
operation universe U of the frozen COW session, the actual public
foundation dependency pairs (explicitly labeled foundation dependencies,
not product semantic causality), and the bounded trusted 078 completion
identities of exactly U.  Its digest covers the exact snapshot
id/digest/site/workspace plus the canonical manifest content (the exact
stored arrays), and the domain snapshot, the companion, the REVIEW
transition and the freeze job terminal commit or roll back together.

Upgrade:
1. ``control.review_operation_manifest`` - immutable companion table
   (UNIQUE snapshot_id, exact binding columns, reviewed-operations/v1
   schema pin).  Owner slaif_owner; no PUBLIC and no role DML/SELECT
   grants (access only through the new definer projections).
2. ``audit.promotion`` gains nullable ``applied_operation_ids uuid[]``,
   ``manifest_id uuid`` and ``manifest_digest text``.  Historical rows
   stay NULL (unknown, never backfilled to an empty list); new receipts
   carry the exact applied IDs and both approval digests, while the
   existing count stays honest compatibility metadata.
3. ``control.slaif_review_operation_identities(uuid, uuid, uuid[])`` -
   the narrow owner-only journal projection of the trusted 078
   completion identities for exactly the named operations of the named
   site/workspace (the nine journal fields, nothing else).  EXECUTE for
   the review worker only; no role gains any journal SELECT.
4. ``control.slaif_review_operation_provenance(uuid, uuid, uuid[])`` -
   the R2 whole-workspace + per-operation trusted provenance check,
   evaluated set-based over EVERY journal row of the site/workspace
   BEFORE any U filtering, so a filtered projection cannot conceal
   orphan or conflicting prospective facts: each U member has exactly
   one 078 journal row bound to this exact site/workspace with the
   matching family reservation (identity-hash bound), the family event
   row with the full site/workspace/principal/resource/identity
   relation, and no conflicting committed history (explicit no-effect
   in U fails closed; ordinary completed history outside U that agrees
   with its journal row stays honest history; missing provenance
   outside U remains explicitly unknown historical data).  Owner-only
   definer; EXECUTE for the review worker only (NOINHERIT direct
   grant).
5. ``control.slaif_review_snapshot_complete_with_manifest(uuid, jsonb,
   jsonb)`` - the worker-only trusted completion: it validates the
   manifest envelope (exact keys, null-safe shapes, UUID/hex strings,
   finite operation/edge/identity/byte budgets, duplicate operations
   failing before any set conversion, dependency endpoints in U, one
   completion identity per operation), then binds the caller
   completion identities field-for-field to the actual 078 journal
   rows (a narrow definer read, never a forgeable metadata path),
   calls the EXISTING trusted domain completion (fresh snapshot,
   FREEZING -> REVIEW), binds the companion to the stored snapshot row
   (id/digest/site/workspace, never caller-selected), recomputes the
   manifest digest server-side over the canonical form of the exact
   stored arrays, and inserts the companion.  Because the inner
   completion only succeeds on the live FREEZING -> REVIEW transition,
   a companion can never be created for an already-reviewed snapshot,
   and a committed REVIEW snapshot from this worker can never lack its
   companion.  EXECUTE for the review worker only; the old standalone
   ``slaif_review_snapshot_complete`` EXECUTE is revoked from the
   worker (the function remains deployed and definer-reachable, but no
   online role can create a companion-less snapshot again).
6. ``control.slaif_review_operation_manifest_read(uuid)`` - one narrow
   read-only companion projection (NULL for a historical
   companion-less snapshot).  EXECUTE for slaif_control (the human
   review document) and the review worker (the accept-time
   in-transaction binding re-verification); no role gains table
   access.
7. Accept entry points re-emitted (072 bodies are immutable history):
   the old 5-argument ``slaif_human_agent_workspace_accept`` and the
   old 2-argument inner ``slaif_workspace_accept`` are DROPPED.  The
   new 6-argument human entry point adds the manifest digest to the
   exact approval (snapshot id + domain digest + manifest digest) and
   the new 5-argument inner enqueue transports the full approval
   binding into the durable job payload.  The inner builder compares
   the incoming exact approval (snapshot id, domain digest, manifest
   digest, actor, site) against a LIVE job payload BEFORE returning the
   replayed job and after the conflict-winner lookup: a stale or
   different approval is a typed refusal, never a 202 replay and never
   a silent fill from current mutable state.  The inner function keeps
   NO role EXECUTE grants (owner-internal: the definer entry point
   reaches it as owner), closing the legacy actorless enqueue bypass
   (072 had granted the 2-argument inner to slaif_control).
8. ``content.slaif_content_type_update`` forward-only repair: the
   historical 017 body declares ``ct``-qualified expressions without
   the ``ct`` alias (every invocation fails 42P01 at entry) and
   compares unqualified names that resolve to the function's output
   columns, so the UPDATE and the returned row are wrong even if the
   declaration parsed.  The replacement keeps the exact signature,
   result shape, SECURITY DEFINER, search_path and the 017 grants
   (slaif_editor_runtime, slaif_control), and restores the documented
   partial-update semantics (a NULL argument keeps the current value);
   017 itself is immutable history.
9. Downgrade is an explicit fail-closed refusal: rolling back below 079
   would restore the companion-less completion EXECUTE and the
   digest-less accept entry points while 079-era manifest/receipt
   history persists, leaving the approval state ambiguous; the refusal
   raises before any restoration and touches no canonical, pending,
   audit, manifest or snapshot state.  The bootstrap operator path
   carries the same preflight (service.py).

This revision adds no HTTP API change beyond the accept body field, no
foundation release, no row-history capture, no selective-accept UI and
no snapshot-format change; the domain capture/render/byte contracts are
unchanged.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from alembic import op

revision: str = "079_001"
down_revision: str | Sequence[str] | None = "078_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_MANIFEST_TABLE = "control.review_operation_manifest"
_IDENTITIES_FUNCTION = "control.slaif_review_operation_identities(uuid, uuid, uuid[])"
_PROVENANCE_FUNCTION = "control.slaif_review_operation_provenance(uuid, uuid, uuid[])"
_COMPLETE_WITH_MANIFEST_FUNCTION = (
    "control.slaif_review_snapshot_complete_with_manifest(uuid, jsonb, jsonb)"
)
_MANIFEST_READ_FUNCTION = "control.slaif_review_operation_manifest_read(uuid)"
_COW_MEMBERSHIP_FUNCTION = "control.slaif_review_operation_cow_membership(uuid)"
_OLD_HUMAN_ACCEPT_FUNCTION = (
    "control.slaif_human_agent_workspace_accept(uuid, uuid, uuid, text, uuid)"
)
_OLD_INNER_ACCEPT_FUNCTION = "control.slaif_workspace_accept(uuid, uuid)"
_INNER_ACCEPT_FUNCTION = "control.slaif_workspace_accept(uuid, uuid, text, text, uuid)"
_HUMAN_ACCEPT_FUNCTION = (
    "control.slaif_human_agent_workspace_accept(uuid, uuid, uuid, text, text, uuid)"
)
_STANDALONE_COMPLETE_FUNCTION = "control.slaif_review_snapshot_complete(uuid, jsonb)"
# The historical 017_001 ``slaif_content_type_update`` declares
# ``ct``-qualified expressions in its DECLARE block without defining the
# ``ct`` alias (every invocation fails 42P01 at entry), and its
# unqualified names resolve to the function's own output columns in the
# UPDATE and result rows.  This forward-only replacement keeps the exact
# signature, result shape, security and grants; the documented
# partial-update semantics (a NULL argument keeps the current value) are
# restored.  SET targets stay unqualified (PostgreSQL requirement) while
# every value expression is ``ct``-qualified so the output-column
# variables can never shadow the table columns.
_CONTENT_TYPE_UPDATE_REPAIR_SQL = """
        CREATE OR REPLACE FUNCTION content.slaif_content_type_update(
            p_type_id uuid, p_labels jsonb, p_slug_pattern text, p_settings jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, "key" text, labels jsonb,
            slug_pattern text, status text, definition_version integer,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.content_type AS ct SET
                labels = COALESCE(p_labels, ct.labels),
                slug_pattern = COALESCE(p_slug_pattern, ct.slug_pattern),
                settings = COALESCE(p_settings, ct.settings),
                definition_version = ct.definition_version + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE ct.id = p_type_id AND ct.status <> 'DELETED';
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT ct.id, ct.site_id, ct."key", ct.labels,
                ct.slug_pattern, ct.status, ct.definition_version, ct.settings,
                ct.created_at, ct.updated_at
            FROM content.content_type AS ct
            WHERE ct.id = p_type_id;
        END;
        $fn$
"""
_CONTENT_TYPE_UPDATE_REPAIR_FUNCTION = (
    'content."slaif_content_type_update"(uuid, jsonb, text, jsonb)'
)

# Every non-owner privilege role: function/table grants are revoked from
# all of them before the exact intended grant is re-added (072/078
# pattern).
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

# Finite manifest budgets (R1): fail closed, no truncation.  Generous
# against every write-reachable workspace (bounded quotas, per-type
# family caps) while keeping the serialized companion finite.
_MAX_MANIFEST_OPERATIONS = 16384
_MAX_MANIFEST_DEPENDENCY_PAIRS = 65536
_MAX_MANIFEST_CANONICAL_BYTES = 8 * 1024 * 1024

_UUID_RE = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
_HEX64_RE = "^[0-9a-f]{64}$"

# Trusted-internal COW tables (083/12): workspace COW state written
# only by trusted control definers, never by the public mutation
# executors.  A session operation whose surviving change rows are
# confined to these tables carries no 078 completion and is bound in
# the companion manifest by the typed trusted-internal provenance
# record instead of a completion identity.
_TRUSTED_INTERNAL_COW_TABLES = ("proposed_side_effect",)
_INTERNAL_CHANGE_TABLE = f"content.{_TRUSTED_INTERNAL_COW_TABLES[0]}_changes"
_INTERNAL_TABLE_LIST_SQL = ", ".join(f"'{t}'" for t in _TRUSTED_INTERNAL_COW_TABLES)
_INTERNAL_RESOURCE_TYPES_JSON = json.dumps(list(_TRUSTED_INTERNAL_COW_TABLES))

_MANIFEST_TABLE_SQL = f"""
        CREATE TABLE control.review_operation_manifest (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            snapshot_id UUID NOT NULL UNIQUE
                REFERENCES control.review_snapshot(id),
            site_id UUID NOT NULL,
            workspace_id UUID NOT NULL,
            schema_version TEXT NOT NULL,
            snapshot_digest TEXT NOT NULL,
            manifest_digest TEXT NOT NULL,
            operation_ids UUID[] NOT NULL,
            dependency_pairs JSONB NOT NULL,
            completion_identities JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT review_operation_manifest_schema_version CHECK
                (schema_version = 'reviewed-operations/v1'),
            CONSTRAINT review_operation_manifest_digest_shape CHECK
                (snapshot_digest ~ '{_HEX64_RE}'
                 AND manifest_digest ~ '{_HEX64_RE}')
        )
"""
_COW_MEMBERSHIP_SQL = f"""
        CREATE FUNCTION control.slaif_review_operation_cow_membership(
            p_workspace_id uuid
        ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            tbl record;
            union_sql text := '';
            internal_ops uuid[];
            foreign_ops uuid[];
        BEGIN
            IF p_workspace_id IS NULL THEN
                RETURN '{{"internal_ops":[],"foreign_ops":[]}}'::jsonb;
            END IF;
            -- Distinct operations with surviving change rows in the
            -- trusted-internal tables of this workspace session.
            SELECT coalesce(array_agg(DISTINCT operation_id),
                            '{{}}'::uuid[])
            INTO internal_ops
            FROM {_INTERNAL_CHANGE_TABLE}
            WHERE session_id = p_workspace_id;
            foreign_ops := '{{}}'::uuid[];
            -- Distinct operations with surviving change rows in EVERY
            -- OTHER content change table (the dynamic set: a COW
            -- table added later is covered without a code change).
            FOR tbl IN
                SELECT c.relname
                FROM pg_class AS c
                JOIN pg_namespace AS ns ON ns.oid = c.relnamespace
                WHERE ns.nspname = 'content'
                  AND c.relkind = 'r'
                  AND c.relname ~ '_changes$'
                  AND c.relname <> 'proposed_side_effect_changes'
                ORDER BY c.relname
            LOOP
                IF union_sql <> '' THEN
                    union_sql := union_sql || ' UNION ALL ';
                END IF;
                union_sql := union_sql || format(
                    'SELECT operation_id FROM content.%I '
                    'WHERE session_id = $1', tbl.relname
                );
            END LOOP;
            IF union_sql <> '' THEN
                EXECUTE format(
                    'SELECT array_agg(DISTINCT operation_id) '
                    'FROM (%s) AS d', union_sql
                ) INTO foreign_ops USING p_workspace_id;
                foreign_ops := coalesce(foreign_ops, '{{}}'::uuid[]);
            END IF;
            RETURN jsonb_build_object(
                'internal_ops', to_jsonb(internal_ops),
                'foreign_ops', to_jsonb(foreign_ops)
            );
        END;
        $fn$
"""
_IDENTITIES_SQL = f"""
        CREATE FUNCTION control.slaif_review_operation_identities(
            p_workspace_id uuid, p_site_id uuid, p_operation_ids uuid[]
        ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            op uuid;
            n integer;
            rec jsonb;
            membership jsonb;
            internal_ops uuid[];
            foreign_ops uuid[];
            result jsonb := '[]'::jsonb;
        BEGIN
            IF p_workspace_id IS NULL OR p_site_id IS NULL
               OR p_operation_ids IS NULL
            THEN
                RETURN '[]'::jsonb;
            END IF;
            membership := control.slaif_review_operation_cow_membership(
                p_workspace_id
            );
            internal_ops := coalesce(
                (SELECT array_agg(t)::uuid[]
                 FROM jsonb_array_elements_text(membership->'internal_ops')
                 AS t),
                '{{}}'::uuid[]
            );
            foreign_ops := coalesce(
                (SELECT array_agg(t)::uuid[]
                 FROM jsonb_array_elements_text(membership->'foreign_ops')
                 AS t),
                '{{}}'::uuid[]
            );
            FOR op IN
                SELECT u.op FROM unnest(p_operation_ids) AS u(op)
                ORDER BY u.op::text
            LOOP
                SELECT count(*) INTO n
                FROM audit.mutation_completion AS j
                WHERE j.operation_id = op
                  AND j.site_id = p_site_id
                  AND j.workspace_id = p_workspace_id;
                IF n = 1 THEN
                    SELECT jsonb_build_object(
                        'operation_id', j.operation_id::text,
                        'family', j.family,
                        'principal_type',
                            CASE WHEN j.family = 'agent' THEN 'capability'
                                 ELSE 'human_user' END,
                        'principal_id',
                            CASE WHEN j.family = 'agent'
                                 THEN j.capability_id::text
                                 ELSE j.human_user_id::text END,
                        'request_identity', j.request_identity,
                        'request_digest', j.request_digest,
                        'resource_type', j.resource_type,
                        'resource_id', j.resource_id::text,
                        'disposition', j.disposition
                    ) INTO rec
                    FROM audit.mutation_completion AS j
                    WHERE j.operation_id = op
                      AND j.site_id = p_site_id
                      AND j.workspace_id = p_workspace_id;
                    result := result || jsonb_build_array(rec);
                ELSIF n = 0
                       AND op = ANY(internal_ops)
                       AND NOT op = ANY(foreign_ops)
                THEN
                    -- Trusted-internal provenance form: the
                    -- operation's surviving COW rows are confined to
                    -- the trusted-internal tables; no 078 completion
                    -- exists or can exist for it.
                    result := result || jsonb_build_array(jsonb_build_object(
                        'operation_id', op::text,
                        'resource_types', '{_INTERNAL_RESOURCE_TYPES_JSON}'::jsonb,
                        'disposition', 'trusted_internal'
                    ));
                END IF;
                -- No journal row and no verified-internal membership:
                -- no record is emitted; the companion writer and the
                -- accept-time provenance check refuse the unbound U
                -- member fail-closed.
            END LOOP;
            RETURN result;
        END;
        $fn$
"""

_PROVENANCE_SQL = f"""
        CREATE FUNCTION control.slaif_review_operation_provenance(
            p_workspace_id uuid, p_site_id uuid, p_operation_ids uuid[]
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            n integer;
            membership jsonb;
            internal_ops uuid[];
            foreign_ops uuid[];
        BEGIN
            IF p_workspace_id IS NULL OR p_site_id IS NULL
               OR p_operation_ids IS NULL
               OR NOT EXISTS (SELECT 1 FROM control.workspace AS w
                              WHERE w.id = p_workspace_id
                                AND w.site_id = p_site_id)
            THEN
                RAISE EXCEPTION 'PROVENANCE_INPUT_INVALID'
                    USING ERRCODE = 'P0001';
            END IF;
            -- Finite whole-workspace fact budget (R1/R2): the
            -- prospective scan covers every journal/reservation/
            -- audit fact of this workspace and must be bounded,
            -- failing closed without truncation.  The bound is a
            -- finite-work guard far above every realistic
            -- workspace (it is not a semantic limit).
            SELECT
                (SELECT count(*) FROM audit.mutation_completion j
                 WHERE j.site_id = p_site_id
                   AND j.workspace_id = p_workspace_id)
              + (SELECT count(*) FROM control.agent_idempotency r
                 WHERE r.workspace_id = p_workspace_id
                   AND r.status_code IS NOT NULL)
              + (SELECT count(*) FROM control.human_editor_idempotency r
                 WHERE r.workspace_id = p_workspace_id
                   AND r.status_code IS NOT NULL)
              + (SELECT count(*) FROM control.media_idempotency r
                 WHERE r.workspace_id = p_workspace_id
                   AND r.status_code IS NOT NULL)
              + (SELECT count(*) FROM audit.agent_mutation t
                 WHERE t.workspace_id = p_workspace_id)
              + (SELECT count(*) FROM audit.human_editor_mutation t
                 WHERE t.workspace_id = p_workspace_id)
              + (SELECT count(*) FROM audit.media_mutation t
                 WHERE t.workspace_id = p_workspace_id)
              + (SELECT count(*) FROM {_INTERNAL_CHANGE_TABLE} AS c
                 WHERE c.session_id = p_workspace_id)
            INTO n;
            IF n > 1048576 THEN
                RAISE EXCEPTION 'PROVENANCE_INPUT_INVALID'
                    USING ERRCODE = 'P0001';
            END IF;
            -- Duplicate U input fails before any set conversion.
            SELECT count(*) INTO n FROM (
                SELECT u.op FROM unnest(p_operation_ids) AS u(op)
                GROUP BY u.op HAVING count(*) > 1
            ) AS dups;
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_INPUT_INVALID'
                    USING ERRCODE = 'P0001';
            END IF;
            -- Every U member is bound by exactly one verified
            -- provenance form: the 078 trusted completion (a journal
            -- row bound to this exact site/workspace; the journal
            -- primary key is site-global, so a same-site
            -- other-workspace row must never satisfy this U) OR the
            -- trusted-internal COW membership (surviving change rows
            -- confined to the trusted-internal tables, no journal).
            membership := control.slaif_review_operation_cow_membership(
                p_workspace_id
            );
            internal_ops := coalesce(
                (SELECT array_agg(t)::uuid[]
                 FROM jsonb_array_elements_text(membership->'internal_ops')
                 AS t),
                '{{}}'::uuid[]
            );
            foreign_ops := coalesce(
                (SELECT array_agg(t)::uuid[]
                 FROM jsonb_array_elements_text(membership->'foreign_ops')
                 AS t),
                '{{}}'::uuid[]
            );
            -- Conflict: a U member journaled AND carrying
            -- trusted-internal COW rows.  No product path writes
            -- both; such a fact is corrupted provenance.
            SELECT count(*) INTO n
            FROM unnest(p_operation_ids) AS u(op)
            WHERE u.op = ANY(internal_ops)
              AND EXISTS (
                  SELECT 1 FROM audit.mutation_completion AS j
                  WHERE j.operation_id = u.op
                    AND j.site_id = p_site_id
                    AND j.workspace_id = p_workspace_id
              );
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            -- Missing: a U member with neither verified form (no
            -- journal row, and not verified trusted-internal).
            SELECT count(*) INTO n
            FROM unnest(p_operation_ids) AS u(op)
            WHERE NOT EXISTS (
                  SELECT 1 FROM audit.mutation_completion AS j
                  WHERE j.operation_id = u.op
                    AND j.site_id = p_site_id
                    AND j.workspace_id = p_workspace_id
              )
              AND NOT (u.op = ANY(internal_ops)
                       AND NOT u.op = ANY(foreign_ops));
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_MISSING' USING ERRCODE = 'P0001';
            END IF;
            -- Explicit no-effect in U: a no_effect completion creates
            -- no pending COW operation, so it can never be a member of
            -- the live operation universe.
            SELECT count(*) INTO n
            FROM audit.mutation_completion AS j
            WHERE j.site_id = p_site_id
              AND j.workspace_id = p_workspace_id
              AND j.operation_id = ANY(p_operation_ids)
              AND j.disposition <> 'completed';
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_EVENT_MISMATCH'
                    USING ERRCODE = 'P0001';
            END IF;
            -- (agent) U members: the exact family reservation,
            -- identity-hash bound (078 contract re-verified).
            SELECT count(*) INTO n
            FROM audit.mutation_completion AS j
            WHERE j.site_id = p_site_id
              AND j.workspace_id = p_workspace_id
              AND j.operation_id = ANY(p_operation_ids)
              AND j.family = 'agent'
              AND NOT EXISTS (
                  SELECT 1 FROM control.agent_idempotency AS r
                  WHERE r.operation_id = j.operation_id
                    AND r.capability_id = j.capability_id
                    AND r.workspace_id = j.workspace_id
                    AND r.status_code IS NOT NULL
                    AND r.request_digest = j.request_digest
                    AND encode(sha256(convert_to(r.idempotency_key, 'UTF8')), 'hex')
                        = j.request_identity
              );
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_RESERVATION_MISMATCH'
                    USING ERRCODE = 'P0001';
            END IF;
            -- (human_editor) U members: the exact family reservation.
            SELECT count(*) INTO n
            FROM audit.mutation_completion AS j
            WHERE j.site_id = p_site_id
              AND j.workspace_id = p_workspace_id
              AND j.operation_id = ANY(p_operation_ids)
              AND j.family = 'human_editor'
              AND NOT EXISTS (
                  SELECT 1 FROM control.human_editor_idempotency AS r
                  WHERE r.operation_id = j.operation_id
                    AND r.workspace_id = j.workspace_id
                    AND r.site_id = j.site_id
                    AND r.human_user_id = j.human_user_id
                    AND r.status_code IS NOT NULL
                    AND r.request_digest = j.request_digest
                    AND encode(sha256(convert_to(r.idempotency_key, 'UTF8')), 'hex')
                        = j.request_identity
              );
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_RESERVATION_MISMATCH'
                    USING ERRCODE = 'P0001';
            END IF;
            -- (media) U members: the exact family reservation.
            SELECT count(*) INTO n
            FROM audit.mutation_completion AS j
            WHERE j.site_id = p_site_id
              AND j.workspace_id = p_workspace_id
              AND j.operation_id = ANY(p_operation_ids)
              AND j.family = 'media'
              AND NOT EXISTS (
                  SELECT 1 FROM control.media_idempotency AS r
                  WHERE r.operation_id = j.operation_id
                    AND r.workspace_id = j.workspace_id
                    AND r.site_id = j.site_id
                    AND r.human_user_id = j.human_user_id
                    AND r.status_code IS NOT NULL
                    AND r.request_digest = j.request_digest
                    AND encode(sha256(convert_to(r.idempotency_key, 'UTF8')), 'hex')
                        = j.request_identity
              );
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_RESERVATION_MISMATCH'
                    USING ERRCODE = 'P0001';
            END IF;
            -- U members: the family event row with the full
            -- site/workspace/principal/resource/identity relation
            -- (media_mutation carries no resource_type column, so the
            -- relation there stops at resource_id).
            SELECT count(*) INTO n
            FROM audit.mutation_completion AS j
            WHERE j.site_id = p_site_id
              AND j.workspace_id = p_workspace_id
              AND j.operation_id = ANY(p_operation_ids)
              AND (
                  (j.family = 'agent' AND NOT EXISTS (
                      SELECT 1 FROM audit.agent_mutation AS t
                      WHERE t.operation_id = j.operation_id
                        AND t.capability_id = j.capability_id
                        AND t.workspace_id = j.workspace_id
                        AND t.site_id = j.site_id
                        AND t.resource_type = j.resource_type
                        AND t.resource_id = j.resource_id
                        AND t.request_digest = j.request_digest
                  ))
                  OR (j.family = 'human_editor' AND NOT EXISTS (
                      SELECT 1 FROM audit.human_editor_mutation AS t
                      WHERE t.operation_id = j.operation_id
                        AND t.human_user_id = j.human_user_id
                        AND t.workspace_id = j.workspace_id
                        AND t.site_id = j.site_id
                        AND t.resource_type = j.resource_type
                        AND t.resource_id = j.resource_id
                        AND t.request_digest = j.request_digest
                  ))
                  OR (j.family = 'media' AND NOT EXISTS (
                      SELECT 1 FROM audit.media_mutation AS t
                      WHERE t.operation_id = j.operation_id
                        AND t.human_user_id = j.human_user_id
                        AND t.workspace_id = j.workspace_id
                        AND t.site_id = j.site_id
                        AND t.resource_id = j.resource_id
                        AND t.request_digest = j.request_digest
                  ))
              );
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_EVENT_MISMATCH'
                    USING ERRCODE = 'P0001';
            END IF;
            -- Whole workspace (every journal row, before any U
            -- filtering): a cross-family completed reservation or a
            -- same-family reservation that disagrees with the journal
            -- row's identity binding is conflicting prospective
            -- provenance (078 identity contract re-verified
            -- read-only).
            SELECT count(*) INTO n
            FROM audit.mutation_completion AS j
            WHERE j.site_id = p_site_id
              AND j.workspace_id = p_workspace_id
              AND (
                  EXISTS (
                      SELECT 1 FROM control.agent_idempotency AS r
                      WHERE r.operation_id = j.operation_id
                        AND r.status_code IS NOT NULL
                        AND NOT (j.family = 'agent'
                             AND r.capability_id = j.capability_id
                             AND r.workspace_id = j.workspace_id
                             AND r.request_digest = j.request_digest
                             AND encode(sha256(convert_to(r.idempotency_key, 'UTF8')), 'hex')
                                 = j.request_identity)
                  )
                  OR EXISTS (
                      SELECT 1 FROM control.human_editor_idempotency AS r
                      WHERE r.operation_id = j.operation_id
                        AND r.status_code IS NOT NULL
                        AND NOT (j.family = 'human_editor'
                             AND r.workspace_id = j.workspace_id
                             AND r.site_id = j.site_id
                             AND r.human_user_id = j.human_user_id
                             AND r.request_digest = j.request_digest
                             AND encode(sha256(convert_to(r.idempotency_key, 'UTF8')), 'hex')
                                 = j.request_identity)
                  )
                  OR EXISTS (
                      SELECT 1 FROM control.media_idempotency AS r
                      WHERE r.operation_id = j.operation_id
                        AND r.status_code IS NOT NULL
                        AND NOT (j.family = 'media'
                             AND r.workspace_id = j.workspace_id
                             AND r.site_id = j.site_id
                             AND r.human_user_id = j.human_user_id
                             AND r.request_digest = j.request_digest
                             AND encode(sha256(convert_to(r.idempotency_key, 'UTF8')), 'hex')
                                 = j.request_identity)
                  )
              );
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            -- Whole workspace (every journal row, before any U
            -- filtering): a cross-family audit row for a journal
            -- operation is always a conflicting operation identity; a
            -- same-family audit row that disagrees with the journal
            -- row's site/workspace/principal/resource binding is
            -- conflicting too.  Ordinary completed history whose
            -- audit row agrees with its journal row (discarded cycles,
            -- dedupe no-effects) stays honest history.
            SELECT count(*) INTO n
            FROM audit.mutation_completion AS j
            WHERE j.site_id = p_site_id
              AND j.workspace_id = p_workspace_id
              AND (
                  (j.family <> 'agent' AND EXISTS (
                      SELECT 1 FROM audit.agent_mutation AS t
                      WHERE t.operation_id = j.operation_id
                  ))
                  OR (j.family <> 'human_editor' AND EXISTS (
                      SELECT 1 FROM audit.human_editor_mutation AS t
                      WHERE t.operation_id = j.operation_id
                  ))
                  OR (j.family <> 'media' AND EXISTS (
                      SELECT 1 FROM audit.media_mutation AS t
                      WHERE t.operation_id = j.operation_id
                  ))
                  OR (j.family = 'agent' AND EXISTS (
                      SELECT 1 FROM audit.agent_mutation AS t
                      WHERE t.operation_id = j.operation_id
                        AND (t.capability_id IS DISTINCT FROM j.capability_id
                             OR t.workspace_id IS DISTINCT FROM j.workspace_id
                             OR t.site_id IS DISTINCT FROM j.site_id
                             OR t.resource_type IS DISTINCT FROM j.resource_type
                             OR t.resource_id IS DISTINCT FROM j.resource_id
                             OR t.request_digest IS DISTINCT FROM j.request_digest)
                  ))
                  OR (j.family = 'human_editor' AND EXISTS (
                      SELECT 1 FROM audit.human_editor_mutation AS t
                      WHERE t.operation_id = j.operation_id
                        AND (t.human_user_id IS DISTINCT FROM j.human_user_id
                             OR t.workspace_id IS DISTINCT FROM j.workspace_id
                             OR t.site_id IS DISTINCT FROM j.site_id
                             OR t.resource_type IS DISTINCT FROM j.resource_type
                             OR t.resource_id IS DISTINCT FROM j.resource_id
                             OR t.request_digest IS DISTINCT FROM j.request_digest)
                  ))
                  OR (j.family = 'media' AND EXISTS (
                      SELECT 1 FROM audit.media_mutation AS t
                      WHERE t.operation_id = j.operation_id
                        AND (t.human_user_id IS DISTINCT FROM j.human_user_id
                             OR t.workspace_id IS DISTINCT FROM j.workspace_id
                             OR t.site_id IS DISTINCT FROM j.site_id
                             OR t.resource_id IS DISTINCT FROM j.resource_id
                             OR t.request_digest IS DISTINCT FROM j.request_digest)
                  ))
              );
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            -- Both directions: prospective facts that exist
            -- WITHOUT a journal row in this workspace.  A
            -- completed reservation or family event of this
            -- workspace whose operation is journaled in ANOTHER
            -- workspace of the same site is a conflicting
            -- cross-workspace prospective fact (operation IDs are
            -- per-workspace by the 078 contract).
            SELECT count(*) INTO n
            FROM control.agent_idempotency AS r
            WHERE r.workspace_id = p_workspace_id
              AND r.status_code IS NOT NULL
              AND EXISTS (SELECT 1 FROM audit.mutation_completion AS j
                           WHERE j.operation_id = r.operation_id
                             AND j.site_id = p_site_id
                             AND j.workspace_id <> p_workspace_id);
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            SELECT count(*) INTO n
            FROM control.human_editor_idempotency AS r
            WHERE r.workspace_id = p_workspace_id
              AND r.status_code IS NOT NULL
              AND EXISTS (SELECT 1 FROM audit.mutation_completion AS j
                           WHERE j.operation_id = r.operation_id
                             AND j.site_id = p_site_id
                             AND j.workspace_id <> p_workspace_id);
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            SELECT count(*) INTO n
            FROM control.media_idempotency AS r
            WHERE r.workspace_id = p_workspace_id
              AND r.status_code IS NOT NULL
              AND EXISTS (SELECT 1 FROM audit.mutation_completion AS j
                           WHERE j.operation_id = r.operation_id
                             AND j.site_id = p_site_id
                             AND j.workspace_id <> p_workspace_id);
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            SELECT count(*) INTO n
            FROM audit.agent_mutation AS t
            WHERE t.workspace_id = p_workspace_id
              AND EXISTS (SELECT 1 FROM audit.mutation_completion AS j
                           WHERE j.operation_id = t.operation_id
                             AND j.site_id = p_site_id
                             AND j.workspace_id <> p_workspace_id);
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            SELECT count(*) INTO n
            FROM audit.human_editor_mutation AS t
            WHERE t.workspace_id = p_workspace_id
              AND EXISTS (SELECT 1 FROM audit.mutation_completion AS j
                           WHERE j.operation_id = t.operation_id
                             AND j.site_id = p_site_id
                             AND j.workspace_id <> p_workspace_id);
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            SELECT count(*) INTO n
            FROM audit.media_mutation AS t
            WHERE t.workspace_id = p_workspace_id
              AND EXISTS (SELECT 1 FROM audit.mutation_completion AS j
                           WHERE j.operation_id = t.operation_id
                             AND j.site_id = p_site_id
                             AND j.workspace_id <> p_workspace_id);
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            -- Both directions: cross-family operation identity
            -- reuse among this workspace's completed reservations
            -- and family events.  Conflicting only for
            -- PROSPECTIVE operations (an 078 journal row exists
            -- for the operation somewhere in this site); an
            -- operation with no journal row anywhere in the site
            -- is old unknown history and stays allowed (legal
            -- dedupe and pre-078 rows are never re-dated).
            SELECT count(*) INTO n
            FROM control.agent_idempotency AS r
            WHERE r.workspace_id = p_workspace_id
              AND r.status_code IS NOT NULL
              AND EXISTS (SELECT 1 FROM audit.mutation_completion AS j
                           WHERE j.operation_id = r.operation_id
                             AND j.site_id = p_site_id)
              AND (EXISTS (SELECT 1 FROM control.human_editor_idempotency AS h
                            WHERE h.operation_id = r.operation_id
                              AND h.status_code IS NOT NULL)
                   OR EXISTS (SELECT 1 FROM control.media_idempotency AS m
                            WHERE m.operation_id = r.operation_id
                              AND m.status_code IS NOT NULL));
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            SELECT count(*) INTO n
            FROM control.human_editor_idempotency AS r
            WHERE r.workspace_id = p_workspace_id
              AND r.status_code IS NOT NULL
              AND EXISTS (SELECT 1 FROM audit.mutation_completion AS j
                           WHERE j.operation_id = r.operation_id
                             AND j.site_id = p_site_id)
              AND (EXISTS (SELECT 1 FROM control.agent_idempotency AS a
                            WHERE a.operation_id = r.operation_id
                              AND a.status_code IS NOT NULL)
                   OR EXISTS (SELECT 1 FROM control.media_idempotency AS m
                            WHERE m.operation_id = r.operation_id
                              AND m.status_code IS NOT NULL));
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            SELECT count(*) INTO n
            FROM control.media_idempotency AS r
            WHERE r.workspace_id = p_workspace_id
              AND r.status_code IS NOT NULL
              AND EXISTS (SELECT 1 FROM audit.mutation_completion AS j
                           WHERE j.operation_id = r.operation_id
                             AND j.site_id = p_site_id)
              AND (EXISTS (SELECT 1 FROM control.agent_idempotency AS a
                            WHERE a.operation_id = r.operation_id
                              AND a.status_code IS NOT NULL)
                   OR EXISTS (SELECT 1 FROM control.human_editor_idempotency AS h
                            WHERE h.operation_id = r.operation_id
                              AND h.status_code IS NOT NULL));
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            SELECT count(*) INTO n
            FROM audit.agent_mutation AS t
            WHERE t.workspace_id = p_workspace_id
              AND EXISTS (SELECT 1 FROM audit.mutation_completion AS j
                           WHERE j.operation_id = t.operation_id
                             AND j.site_id = p_site_id)
              AND (EXISTS (SELECT 1 FROM audit.human_editor_mutation AS h
                            WHERE h.operation_id = t.operation_id)
                   OR EXISTS (SELECT 1 FROM audit.media_mutation AS m
                            WHERE m.operation_id = t.operation_id));
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            SELECT count(*) INTO n
            FROM audit.human_editor_mutation AS t
            WHERE t.workspace_id = p_workspace_id
              AND EXISTS (SELECT 1 FROM audit.mutation_completion AS j
                           WHERE j.operation_id = t.operation_id
                             AND j.site_id = p_site_id)
              AND (EXISTS (SELECT 1 FROM audit.agent_mutation AS a
                            WHERE a.operation_id = t.operation_id)
                   OR EXISTS (SELECT 1 FROM audit.media_mutation AS m
                            WHERE m.operation_id = t.operation_id));
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            SELECT count(*) INTO n
            FROM audit.media_mutation AS t
            WHERE t.workspace_id = p_workspace_id
              AND EXISTS (SELECT 1 FROM audit.mutation_completion AS j
                           WHERE j.operation_id = t.operation_id
                             AND j.site_id = p_site_id)
              AND (EXISTS (SELECT 1 FROM audit.agent_mutation AS a
                            WHERE a.operation_id = t.operation_id)
                   OR EXISTS (SELECT 1 FROM audit.human_editor_mutation AS h
                            WHERE h.operation_id = t.operation_id));
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
        END;
        $fn$
"""
_COMPLETE_WITH_MANIFEST_SQL = f"""
        CREATE FUNCTION control.slaif_review_snapshot_complete_with_manifest(
            p_workspace_id uuid, p_row jsonb, p_manifest jsonb
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            snapshot_id uuid;
            stored_site_id uuid;
            stored_digest text;
            stored_workspace_id uuid;
            canonical text;
            manifest_digest text;
            n integer;
            sorted_ops uuid[];
            canonical_pairs jsonb;
            canonical_identities jsonb;
            membership jsonb;
            internal_ops uuid[];
            foreign_ops uuid[];
        BEGIN
            -- Envelope invariants, staged so every guard runs on
            -- input already proven to be the type it operates on
            -- (object_keys/array_length on a scalar would be a raw
            -- datatype error, never a typed refusal): JSON nulls
            -- and missing keys fail closed at the exact stage that
            -- proves them absent.
            IF p_manifest IS NULL
               OR jsonb_typeof(p_manifest) <> 'object'
            THEN
                RAISE EXCEPTION 'MANIFEST_INPUT_INVALID' USING ERRCODE = 'P0001';
            END IF;
            IF (SELECT count(*) FROM jsonb_object_keys(p_manifest)) <> 6
               OR NOT (p_manifest ?& ARRAY[
                    'schema_version','site_id','workspace_id','operation_ids',
                    'dependency_pairs','completion_identities']::text[])
            THEN
                RAISE EXCEPTION 'MANIFEST_INPUT_INVALID' USING ERRCODE = 'P0001';
            END IF;
            -- Scalar identity fields: JSON strings with exact values
            -- (typeof before ->> - no coercion of numbers/objects).
            IF p_manifest->'schema_version' IS NULL
               OR jsonb_typeof(p_manifest->'schema_version') <> 'string'
               OR p_manifest->>'schema_version' IS DISTINCT FROM 'reviewed-operations/v1'
            THEN
                RAISE EXCEPTION 'MANIFEST_INPUT_INVALID' USING ERRCODE = 'P0001';
            END IF;
            IF p_manifest->'site_id' IS NULL
               OR jsonb_typeof(p_manifest->'site_id') <> 'string'
               OR p_manifest->>'site_id' !~ '{_UUID_RE}'
            THEN
                RAISE EXCEPTION 'MANIFEST_INPUT_INVALID' USING ERRCODE = 'P0001';
            END IF;
            IF p_manifest->'workspace_id' IS NULL
               OR jsonb_typeof(p_manifest->'workspace_id') <> 'string'
               OR p_manifest->>'workspace_id' IS DISTINCT FROM p_workspace_id::text
            THEN
                RAISE EXCEPTION 'MANIFEST_INPUT_INVALID' USING ERRCODE = 'P0001';
            END IF;
            IF jsonb_typeof(p_manifest->'operation_ids') <> 'array'
               OR jsonb_typeof(p_manifest->'dependency_pairs') <> 'array'
               OR jsonb_typeof(p_manifest->'completion_identities') <> 'array'
            THEN
                RAISE EXCEPTION 'MANIFEST_INPUT_INVALID' USING ERRCODE = 'P0001';
            END IF;
            -- Finite element budgets (safe: the arrays were staged
            -- above).
            IF jsonb_array_length(p_manifest->'operation_ids')
                   > {_MAX_MANIFEST_OPERATIONS}
               OR jsonb_array_length(p_manifest->'dependency_pairs')
                   > {_MAX_MANIFEST_DEPENDENCY_PAIRS}
               OR jsonb_array_length(p_manifest->'completion_identities')
                   > {_MAX_MANIFEST_OPERATIONS}
            THEN
                RAISE EXCEPTION 'MANIFEST_OVER_BUDGET' USING ERRCODE = 'P0001';
            END IF;
            -- Serialized byte budget: real UTF8 bytes, not
            -- characters (length(text) undercounts non-ASCII).
            IF length(convert_to(
                   control.slaif_canonical_jsonb_text(p_manifest), 'UTF8'))
                   > {_MAX_MANIFEST_CANONICAL_BYTES}
            THEN
                RAISE EXCEPTION 'MANIFEST_OVER_BUDGET' USING ERRCODE = 'P0001';
            END IF;
            -- U: every entry is a canonical lowercase UUID string.
            -- Staged guards: typeof first (so ->> extraction below is
            -- defined on strings only), then the shape regex.
            SELECT count(*) INTO n
            FROM jsonb_array_elements(p_manifest->'operation_ids') AS u(value)
            WHERE jsonb_typeof(u.value) <> 'string';
            IF n <> 0 THEN
                RAISE EXCEPTION 'MANIFEST_OPERATION_INVALID' USING ERRCODE = 'P0001';
            END IF;
            SELECT count(*) INTO n
            FROM jsonb_array_elements_text(p_manifest->'operation_ids') AS u(t)
            WHERE u.t !~ '{_UUID_RE}';
            IF n <> 0 THEN
                RAISE EXCEPTION 'MANIFEST_OPERATION_INVALID' USING ERRCODE = 'P0001';
            END IF;
            -- Duplicate operation IDs fail before any set conversion.
            SELECT count(*) INTO n
            FROM (
                SELECT u.t FROM jsonb_array_elements_text(
                    p_manifest->'operation_ids') AS u(t)
                GROUP BY u.t HAVING count(*) > 1
            ) AS dups;
            IF n <> 0 THEN
                RAISE EXCEPTION 'MANIFEST_DUPLICATE_OPERATION' USING ERRCODE = 'P0001';
            END IF;
            -- Dependency pairs: [depends_on, operation_id] UUID-string
            -- pairs (staged shape guard first), both endpoints in U
            -- (string extraction via ->>, never text = jsonb).
            SELECT count(*) INTO n
            FROM jsonb_array_elements(p_manifest->'dependency_pairs') AS pair(value)
            WHERE jsonb_typeof(pair.value) <> 'array'
               OR jsonb_array_length(pair.value) <> 2
               OR jsonb_typeof(pair.value->0) <> 'string'
               OR jsonb_typeof(pair.value->1) <> 'string';
            IF n <> 0 THEN
                RAISE EXCEPTION 'MANIFEST_DEPENDENCY_INVALID' USING ERRCODE = 'P0001';
            END IF;
            SELECT count(*) INTO n
            FROM jsonb_array_elements(p_manifest->'dependency_pairs') AS pair(value)
            WHERE pair.value->>0 !~ '{_UUID_RE}'
               OR pair.value->>1 !~ '{_UUID_RE}';
            IF n <> 0 THEN
                RAISE EXCEPTION 'MANIFEST_DEPENDENCY_INVALID' USING ERRCODE = 'P0001';
            END IF;
            SELECT count(*) INTO n
            FROM jsonb_array_elements(p_manifest->'dependency_pairs') AS pair(value)
            WHERE NOT EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(
                    p_manifest->'operation_ids') AS u(t)
                WHERE u.t = pair.value->>0
            ) OR NOT EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(
                    p_manifest->'operation_ids') AS u(t)
                WHERE u.t = pair.value->>1
            );
            IF n <> 0 THEN
                RAISE EXCEPTION 'MANIFEST_DEPENDENCY_ENDPOINT' USING ERRCODE = 'P0001';
            END IF;
            -- Completion identities: exactly the nine trusted 078
            -- identity fields, staged exactly like the envelope
            -- (non-object elements refuse before object_keys runs;
            -- string typeof guards make every ->> extraction
            -- null-safe; JSON nulls fail the typeof guard).
            SELECT count(*) INTO n
            FROM jsonb_array_elements(p_manifest->'completion_identities') AS ci(value)
            WHERE jsonb_typeof(ci.value) <> 'object';
            IF n <> 0 THEN
                RAISE EXCEPTION 'MANIFEST_IDENTITY_INVALID' USING ERRCODE = 'P0001';
            END IF;
            -- Each record is EXACTLY one of the two verified
            -- provenance forms: the nine-field 078 completion
            -- identity, or the three-field trusted-internal record
            -- (staged typeof/shape guards make every extraction
            -- null-safe; JSON nulls fail the typeof guards).
            SELECT count(*) INTO n
            FROM jsonb_array_elements(p_manifest->'completion_identities') AS ci(value)
            WHERE NOT (
                (
                    (SELECT count(*) FROM jsonb_object_keys(ci.value)) = 9
                    AND (ci.value ?& ARRAY[
                         'operation_id','family','principal_type','principal_id',
                         'request_identity','request_digest','resource_type',
                         'resource_id','disposition']::text[])
                    AND jsonb_typeof(ci.value->'operation_id') = 'string'
                    AND jsonb_typeof(ci.value->'family') = 'string'
                    AND jsonb_typeof(ci.value->'principal_type') = 'string'
                    AND jsonb_typeof(ci.value->'principal_id') = 'string'
                    AND jsonb_typeof(ci.value->'request_identity') = 'string'
                    AND jsonb_typeof(ci.value->'request_digest') = 'string'
                    AND jsonb_typeof(ci.value->'resource_type') = 'string'
                    AND jsonb_typeof(ci.value->'resource_id') = 'string'
                    AND jsonb_typeof(ci.value->'disposition') = 'string'
                    AND ci.value->>'operation_id' ~ '{_UUID_RE}'
                    AND (ci.value->>'family' IN ('agent','human_editor','media'))
                    AND (ci.value->>'principal_type' IN ('capability','human_user'))
                    AND (ci.value->>'family' = 'agent')
                           IS NOT DISTINCT FROM (ci.value->>'principal_type' = 'capability')
                    AND ci.value->>'principal_id' ~ '{_UUID_RE}'
                    AND ci.value->>'request_identity' ~ '{_HEX64_RE}'
                    AND ci.value->>'request_digest' ~ '{_HEX64_RE}'
                    AND length(ci.value->>'resource_type') BETWEEN 1 AND 128
                    AND ci.value->>'resource_id' ~ '{_UUID_RE}'
                    AND (ci.value->>'disposition' IN ('completed','no_effect'))
                )
                OR (
                    (SELECT count(*) FROM jsonb_object_keys(ci.value)) = 3
                    AND (ci.value ?& ARRAY[
                         'operation_id','resource_types','disposition']::text[])
                    AND jsonb_typeof(ci.value->'operation_id') = 'string'
                    AND ci.value->>'operation_id' ~ '{_UUID_RE}'
                    AND jsonb_typeof(ci.value->'resource_types') = 'array'
                    AND jsonb_array_length(ci.value->'resource_types') = 1
                    AND jsonb_typeof(ci.value->'resource_types'->0) = 'string'
                    AND ci.value->'resource_types' = to_jsonb(
                        ARRAY[{_INTERNAL_TABLE_LIST_SQL}]::text[])
                    AND jsonb_typeof(ci.value->'disposition') = 'string'
                    AND ci.value->>'disposition' = 'trusted_internal'
                )
            );
            IF n <> 0 THEN
                RAISE EXCEPTION 'MANIFEST_IDENTITY_INVALID' USING ERRCODE = 'P0001';
            END IF;
            IF jsonb_array_length(p_manifest->'completion_identities')
                   <> jsonb_array_length(p_manifest->'operation_ids')
            THEN
                RAISE EXCEPTION 'MANIFEST_IDENTITY_COUNT' USING ERRCODE = 'P0001';
            END IF;
            -- Bijection: the identity operation set equals U exactly
            -- (set-difference both directions; counts already equal).
            SELECT count(*) INTO n
            FROM jsonb_array_elements_text(p_manifest->'operation_ids') AS u(t)
            WHERE NOT EXISTS (
                SELECT 1 FROM jsonb_array_elements(
                    p_manifest->'completion_identities') AS ci(value)
                WHERE ci.value->>'operation_id' = u.t
            );
            IF n <> 0 THEN
                RAISE EXCEPTION 'MANIFEST_IDENTITY_MISMATCH' USING ERRCODE = 'P0001';
            END IF;
            SELECT count(*) INTO n
            FROM (
                SELECT ci.value->>'operation_id' AS t
                FROM jsonb_array_elements(
                    p_manifest->'completion_identities') AS ci(value)
                GROUP BY ci.value->>'operation_id' HAVING count(*) > 1
            ) AS dups;
            IF n <> 0 THEN
                RAISE EXCEPTION 'MANIFEST_DUPLICATE_OPERATION' USING ERRCODE = 'P0001';
            END IF;
            -- Trusted identity binding: every 078-completion-form
            -- record must be field-for-field the actual 078 journal
            -- row of this exact site/workspace (definer reads the
            -- owner-only journal; no forgeable family/principal/
            -- resource/digest metadata).
            SELECT count(*) INTO n
            FROM jsonb_array_elements(p_manifest->'completion_identities') AS ci(value)
            WHERE (SELECT count(*) FROM jsonb_object_keys(ci.value)) = 9
              AND NOT EXISTS (
                SELECT 1 FROM audit.mutation_completion AS j
                WHERE j.operation_id = (ci.value->>'operation_id')::uuid
                  AND j.site_id = (p_manifest->>'site_id')::uuid
                  AND j.workspace_id = p_workspace_id
                  AND j.family = ci.value->>'family'
                  AND (CASE WHEN j.family = 'agent' THEN 'capability'
                            ELSE 'human_user' END)
                      = ci.value->>'principal_type'
                  AND (CASE WHEN j.family = 'agent' THEN j.capability_id::text
                            ELSE j.human_user_id::text END)
                      = ci.value->>'principal_id'
                  AND j.request_identity = ci.value->>'request_identity'
                  AND j.request_digest = ci.value->>'request_digest'
                  AND j.resource_type = ci.value->>'resource_type'
                  AND j.resource_id::text = ci.value->>'resource_id'
                  AND j.disposition = ci.value->>'disposition'
            );
            IF n <> 0 THEN
                RAISE EXCEPTION 'MANIFEST_IDENTITY_MISMATCH' USING ERRCODE = 'P0001';
            END IF;
            -- Trusted-internal records: the operation must actually
            -- carry only trusted-internal COW rows and no 078
            -- completion (a completion-bound or mutation-table
            -- operation cannot be bound as internal).
            membership := control.slaif_review_operation_cow_membership(
                p_workspace_id
            );
            internal_ops := coalesce(
                (SELECT array_agg(t)::uuid[]
                 FROM jsonb_array_elements_text(membership->'internal_ops')
                 AS t),
                '{{}}'::uuid[]
            );
            foreign_ops := coalesce(
                (SELECT array_agg(t)::uuid[]
                 FROM jsonb_array_elements_text(membership->'foreign_ops')
                 AS t),
                '{{}}'::uuid[]
            );
            SELECT count(*) INTO n
            FROM jsonb_array_elements(p_manifest->'completion_identities') AS ci(value)
            WHERE (SELECT count(*) FROM jsonb_object_keys(ci.value)) = 3
              AND ci.value->>'disposition' = 'trusted_internal'
              AND (
                  NOT ((ci.value->>'operation_id')::uuid = ANY(internal_ops))
                  OR ((ci.value->>'operation_id')::uuid = ANY(foreign_ops))
                  OR EXISTS (
                      SELECT 1 FROM audit.mutation_completion AS j
                      WHERE j.operation_id = (ci.value->>'operation_id')::uuid
                        AND j.site_id = (p_manifest->>'site_id')::uuid
                        AND j.workspace_id = p_workspace_id
                  )
              );
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            -- Every U member is bound by exactly one verified
            -- provenance form (a 078 journal row, or verified
            -- trusted-internal COW membership); a member with both
            -- forms is conflicting provenance, a member with neither
            -- is missing provenance.
            SELECT count(*) INTO n
            FROM jsonb_array_elements_text(p_manifest->'operation_ids') AS u(t)
            WHERE u.t::uuid = ANY(internal_ops)
              AND EXISTS (
                  SELECT 1 FROM audit.mutation_completion AS j
                  WHERE j.operation_id = u.t::uuid
                    AND j.site_id = (p_manifest->>'site_id')::uuid
                    AND j.workspace_id = p_workspace_id
              );
            IF n <> 0 THEN
                RAISE EXCEPTION 'PROVENANCE_CONFLICT' USING ERRCODE = 'P0003';
            END IF;
            SELECT count(*) INTO n
            FROM jsonb_array_elements_text(p_manifest->'operation_ids') AS u(t)
            WHERE NOT EXISTS (
                  SELECT 1 FROM audit.mutation_completion AS j
                  WHERE j.operation_id = u.t::uuid
                    AND j.site_id = (p_manifest->>'site_id')::uuid
                    AND j.workspace_id = p_workspace_id
              )
              AND NOT (u.t::uuid = ANY(internal_ops)
                       AND NOT u.t::uuid = ANY(foreign_ops));
            IF n <> 0 THEN
                RAISE EXCEPTION 'MANIFEST_PROVENANCE_MISSING'
                    USING ERRCODE = 'P0001';
            END IF;

            -- The existing trusted domain completion: full v2 envelope
            -- validation, digest recomputation, snapshot INSERT and the
            -- FREEZING -> REVIEW transition, all in this transaction.
            snapshot_id := control.slaif_review_snapshot_complete(
                p_workspace_id, p_row
            );

            -- Bind to the stored snapshot row (trusted state, never
            -- caller-selected JSON).
            SELECT s.site_id, s.workspace_id, s.digest
            INTO stored_site_id, stored_workspace_id, stored_digest
            FROM control.review_snapshot AS s
            WHERE s.id = snapshot_id;
            IF stored_workspace_id IS DISTINCT FROM p_workspace_id
               OR (p_manifest->>'site_id')::uuid IS DISTINCT FROM stored_site_id
            THEN
                RAISE EXCEPTION 'MANIFEST_BINDING_MISMATCH' USING ERRCODE = 'P0002';
            END IF;

            -- Canonicalize the stored content exactly once: U sorted,
            -- dependency pairs unique + sorted, identities sorted by
            -- operation.  The digest below covers the identical stored
            -- arrays (never unsorted caller input).
            sorted_ops := coalesce(
                (SELECT array_agg(u.t::uuid ORDER BY u.t)
                 FROM jsonb_array_elements_text(
                     p_manifest->'operation_ids') AS u(t)),
                '{{}}'::uuid[]
            );
            canonical_pairs := coalesce(
                (SELECT jsonb_agg(v.value ORDER BY v.value->>0, v.value->>1)
                 FROM (
                     SELECT DISTINCT pair.value
                     FROM jsonb_array_elements(
                         p_manifest->'dependency_pairs') AS pair(value)
                 ) AS v
                ),
                '[]'::jsonb
            );
            canonical_identities := coalesce(
                (SELECT jsonb_agg(v.value ORDER BY v.value->>'operation_id')
                 FROM (
                     SELECT DISTINCT ci.value
                     FROM jsonb_array_elements(
                         p_manifest->'completion_identities') AS ci(value)
                 ) AS v
                ),
                '[]'::jsonb
            );

            -- Server-side manifest digest over the trusted binding
            -- plus the canonical stored content (070 canonical form).
            canonical := control.slaif_canonical_jsonb_text(jsonb_build_object(
                'schema_version', p_manifest->>'schema_version',
                'snapshot_id', snapshot_id::text,
                'snapshot_digest', stored_digest,
                'site_id', stored_site_id::text,
                'workspace_id', p_workspace_id::text,
                'operation_ids', to_jsonb(sorted_ops),
                'dependency_pairs', canonical_pairs,
                'completion_identities', canonical_identities
            ));
            manifest_digest := encode(
                sha256(convert_to(canonical, 'UTF8')), 'hex'
            );

            INSERT INTO control.review_operation_manifest (
                snapshot_id, site_id, workspace_id, schema_version,
                snapshot_digest, manifest_digest, operation_ids,
                dependency_pairs, completion_identities
            ) VALUES (
                snapshot_id, stored_site_id, p_workspace_id,
                p_manifest->>'schema_version', stored_digest, manifest_digest,
                sorted_ops,
                canonical_pairs,
                canonical_identities
            );
            RETURN snapshot_id;
        END;
        $fn$
"""
_MANIFEST_READ_SQL = """
        CREATE FUNCTION control.slaif_review_operation_manifest_read(
            p_snapshot_id uuid
        ) RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        SELECT jsonb_build_object(
            'schema_version', m.schema_version,
            'manifest_id', m.id::text,
            'manifest_digest', m.manifest_digest,
            'snapshot_digest', m.snapshot_digest,
            'site_id', m.site_id::text,
            'workspace_id', m.workspace_id::text,
            'operation_ids', to_jsonb(m.operation_ids),
            'dependency_pairs', m.dependency_pairs,
            'completion_identities', m.completion_identities
        )
        FROM control.review_operation_manifest AS m
        WHERE m.snapshot_id = p_snapshot_id
        $fn$
"""

# The new 5-argument inner enqueue (072 body re-emitted + the exact
# approval transport/comparison).  It keeps NO role EXECUTE grants:
# only the definer human entry point reaches it (owner), which closes
# the 072 actorless enqueue grant to slaif_control.
_INNER_ACCEPT_SQL = """
        CREATE FUNCTION control.slaif_workspace_accept(
            p_workspace_id uuid, p_snapshot_id uuid, p_snapshot_digest text,
            p_manifest_digest text, p_actor_user_account_id uuid
        ) RETURNS TABLE (
            job_id uuid, status text
        ) LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            ws control.workspace%ROWTYPE;
            live_id uuid;
            live_status text;
            live_payload jsonb;
        BEGIN
            SELECT * INTO ws FROM control.workspace
            WHERE id = p_workspace_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            IF p_snapshot_digest IS NULL
               OR p_snapshot_digest !~ '^[0-9a-f]{64}$'
               OR p_manifest_digest IS NULL
               OR p_manifest_digest !~ '^[0-9a-f]{64}$'
            THEN
                RAISE EXCEPTION 'ACCEPT_APPROVAL_INVALID'
                    USING ERRCODE = 'P0001';
            END IF;
            -- Idempotent replay gate: a live (QUEUED/CLAIMED) ACCEPT
            -- job is returned unchanged ONLY when the incoming exact
            -- approval (snapshot id + domain digest + manifest digest
            -- + actor + site) matches the live job payload.  A stale
            -- or different approval is a typed refusal - never a 202
            -- replay and never a silent fill from current mutable
            -- state (a legacy 3-key payload cannot match and is
            -- refused here).
            SELECT job.id, job.status, job.payload
            INTO live_id, live_status, live_payload
            FROM control.review_job AS job
            WHERE job.workspace_id = p_workspace_id
              AND job.job_kind = 'ACCEPT'
              AND job.status IN ('QUEUED','CLAIMED')
            FOR UPDATE;
            IF FOUND THEN
                -- Null-safe: a legacy/null live payload field makes
                -- the AND-chain NULL, and NULL must refuse exactly
                -- like a wrong non-null digest (never a replay).
                IF (live_payload->>'snapshot_id' = p_snapshot_id::text
                    AND live_payload->>'snapshot_digest' = p_snapshot_digest
                    AND live_payload->>'manifest_digest' = p_manifest_digest
                    AND live_payload->>'actor_user_account_id'
                        = p_actor_user_account_id::text
                    AND live_payload->>'site_id' = ws.site_id::text)
                       IS DISTINCT FROM TRUE
                THEN
                    RAISE EXCEPTION 'ACCEPT_LIVE_JOB_MISMATCH'
                        USING ERRCODE = 'P0003';
                END IF;
                -- RETURN QUERY does not terminate a plpgsql function:
                -- the explicit RETURN stops the idempotent path before
                -- the status gate (the workspace is already
                -- ACCEPT_QUEUED).
                RETURN QUERY SELECT live_id, live_status;
                RETURN;
            END IF;
            IF ws.status IS DISTINCT FROM 'REVIEW' THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_IN_REVIEW'
                    USING ERRCODE = 'P0002';
            END IF;
            IF ws.review_snapshot_id IS DISTINCT FROM p_snapshot_id
               OR NOT EXISTS (
                    SELECT 1 FROM control.review_snapshot AS s
                    WHERE s.id = p_snapshot_id
                      AND s.workspace_id = p_workspace_id
                      AND s.site_id = ws.site_id
                      AND s.status = 'COMPLETE'
                      AND s.digest = p_snapshot_digest
                )
            THEN
                RAISE EXCEPTION 'REVIEW_SNAPSHOT_NOT_FOUND'
                    USING ERRCODE = 'P0002';
            END IF;
            IF NOT EXISTS (
                    SELECT 1 FROM control.review_operation_manifest AS m
                    WHERE m.snapshot_id = p_snapshot_id
                      AND m.site_id = ws.site_id
                      AND m.workspace_id = p_workspace_id
                      AND m.snapshot_digest = p_snapshot_digest
                      AND m.manifest_digest = p_manifest_digest
                )
            THEN
                RAISE EXCEPTION 'REVIEW_MANIFEST_NOT_FOUND'
                    USING ERRCODE = 'P0002';
            END IF;
            -- The partial unique index closes the enqueue race.
            INSERT INTO control.review_job (
                workspace_id, site_id, job_kind, status, payload
            )
            VALUES (
                p_workspace_id, ws.site_id, 'ACCEPT', 'QUEUED',
                jsonb_build_object(
                    'snapshot_id', p_snapshot_id::text,
                    'site_id', ws.site_id::text,
                    'actor_user_account_id',
                        p_actor_user_account_id::text,
                    'snapshot_digest', p_snapshot_digest,
                    'manifest_digest', p_manifest_digest
                )
            )
            ON CONFLICT (workspace_id, job_kind)
                -- Qualified: the unqualified name would be ambiguous
                -- against the function's own output column (the
                -- implicit RETURNS TABLE variable) in plpgsql.
                WHERE control.review_job.status IN ('QUEUED','CLAIMED')
                    DO NOTHING;
            SELECT job.id, job.status, job.payload
            INTO live_id, live_status, live_payload
            FROM control.review_job AS job
            WHERE job.workspace_id = p_workspace_id
              AND job.job_kind = 'ACCEPT'
              AND job.status IN ('QUEUED','CLAIMED')
            FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'ACCEPT_ENQUEUE_CONFLICT'
                    USING ERRCODE = 'P0002';
            END IF;
            -- Conflict-winner lookup: the winning job must carry THIS
            -- exact approval; the race loser's different approval is
            -- never returned as the caller's replay.
            -- Null-safe: the winning job must carry this exact
            -- approval (IS DISTINCT FROM TRUE refuses a
            -- legacy/null payload exactly like a wrong digest).
            IF (live_payload->>'snapshot_id' = p_snapshot_id::text
                AND live_payload->>'snapshot_digest' = p_snapshot_digest
                AND live_payload->>'manifest_digest' = p_manifest_digest
                AND live_payload->>'actor_user_account_id'
                    = p_actor_user_account_id::text
                AND live_payload->>'site_id' = ws.site_id::text)
               IS DISTINCT FROM TRUE
            THEN
                RAISE EXCEPTION 'ACCEPT_LIVE_JOB_MISMATCH'
                    USING ERRCODE = 'P0003';
            END IF;
            UPDATE control.workspace
               SET status = 'ACCEPT_QUEUED'
             WHERE control.workspace.id = p_workspace_id
               AND control.workspace.status = 'REVIEW';
            RETURN QUERY SELECT live_id, live_status;
        END;
        $fn$
"""

# The new 6-argument human entry point (072 gates re-emitted + the
# immutable companion digest gate).  Every mismatch keeps the
# uniform silent RETURN (no oracle).
_HUMAN_ACCEPT_SQL = """
        CREATE FUNCTION control.slaif_human_agent_workspace_accept(
            p_workspace_id uuid, p_site_id uuid, p_snapshot_id uuid,
            p_snapshot_digest text, p_manifest_digest text, p_user_id uuid
        ) RETURNS TABLE (job_id uuid, status text)
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            accept_row record;
            ws_status text;
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM control.workspace AS w
                WHERE w.id = p_workspace_id
                  AND w.site_id = p_site_id
            ) THEN
                RETURN;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM control.platform_administrator
                WHERE user_account_id = p_user_id
            ) AND NOT EXISTS (
                SELECT 1
                FROM control.slaif_effective_human_membership(
                    p_user_id, p_site_id
                ) AS m
                WHERE 'workspace:accept' = ANY(m.effective_permissions)
                  AND 'site:publish' = ANY(m.effective_permissions)
            ) THEN
                RETURN;
            END IF;
            -- Snapshot expectation: the bound COMPLETE snapshot must be
            -- the named one and carry the named digest. Any mismatch is
            -- indistinguishable from the not-found case (no oracle).
            IF NOT EXISTS (
                SELECT 1
                FROM control.workspace AS w
                JOIN control.review_snapshot AS s
                    ON s.id = w.review_snapshot_id
                   AND s.status = 'COMPLETE'
                WHERE w.id = p_workspace_id
                  AND s.id = p_snapshot_id
                  AND s.digest = p_snapshot_digest
            ) THEN
                RETURN;
            END IF;
            -- The immutable companion must exist for the exact snapshot
            -- and carry the exact named manifest digest: no digest-less
            -- accept path remains after this revision.
            IF NOT EXISTS (
                SELECT 1 FROM control.review_operation_manifest AS m
                WHERE m.snapshot_id = p_snapshot_id
                  AND m.site_id = p_site_id
                  AND m.workspace_id = p_workspace_id
                  AND m.manifest_digest = p_manifest_digest
            ) THEN
                RETURN;
            END IF;
            SELECT * INTO accept_row
            FROM control.slaif_workspace_accept(
                p_workspace_id, p_snapshot_id, p_snapshot_digest,
                p_manifest_digest, p_user_id
            );
            SELECT w.status INTO ws_status
            FROM control.workspace AS w
            WHERE w.id = p_workspace_id;
            RETURN QUERY
                SELECT accept_row.job_id,
                       COALESCE(ws_status, accept_row.status);
        END;
        $fn$
"""


def upgrade() -> None:
    # 1. The immutable companion table (owner only, zero role grants).
    op.execute(_MANIFEST_TABLE_SQL)
    op.execute(f"ALTER TABLE {_MANIFEST_TABLE} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON TABLE {_MANIFEST_TABLE} FROM PUBLIC")
    for role in _LONG_LIVED_ROLES:
        op.execute(f"REVOKE ALL ON TABLE {_MANIFEST_TABLE} FROM {role}")

    # 2. The promotion receipt gains the applied-identity columns
    #    (legacy rows stay NULL: unknown, never backfilled).
    op.execute("ALTER TABLE audit.promotion ADD COLUMN applied_operation_ids uuid[]")
    op.execute("ALTER TABLE audit.promotion ADD COLUMN manifest_id uuid")
    op.execute("ALTER TABLE audit.promotion ADD COLUMN manifest_digest text")
    op.execute(
        "ALTER TABLE audit.promotion ADD CONSTRAINT "
        "promotion_manifest_digest_shape CHECK "
        "(manifest_digest IS NULL OR manifest_digest ~ "
        "'^[0-9a-f]{64}$')"
    )

    # 3. The companion surface: create, owner, revoke sweep.  The
    # COW membership helper is owner-internal (called only by the
    # definer companion functions) and keeps NO role EXECUTE grants.
    for sql in (
        _COW_MEMBERSHIP_SQL,
        _IDENTITIES_SQL,
        _PROVENANCE_SQL,
        _COMPLETE_WITH_MANIFEST_SQL,
        _MANIFEST_READ_SQL,
    ):
        op.execute(sql)
    for function in (
        _COW_MEMBERSHIP_FUNCTION,
        _IDENTITIES_FUNCTION,
        _PROVENANCE_FUNCTION,
        _COMPLETE_WITH_MANIFEST_FUNCTION,
        _MANIFEST_READ_FUNCTION,
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        for role in _LONG_LIVED_ROLES:
            op.execute(f"REVOKE ALL ON FUNCTION {function} FROM {role}")
    # Exact caller sets: the worker gets the identity projection, the
    # provenance check and the companion completion; the read
    # projection serves the human review document (control) and the
    # accept-time in-transaction binding re-verification (worker).  No
    # role gains any companion or journal table access.
    op.execute(
        f"GRANT EXECUTE ON FUNCTION {_IDENTITIES_FUNCTION} TO slaif_review_worker"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION {_PROVENANCE_FUNCTION} TO slaif_review_worker"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION {_COMPLETE_WITH_MANIFEST_FUNCTION} "
        "TO slaif_review_worker"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION {_MANIFEST_READ_FUNCTION} "
        "TO slaif_control, slaif_review_worker"
    )

    # 4. The standalone completion loses its last online EXECUTE (it
    #    remains deployed and definer-reachable by the companion
    #    completion; no online role can create a companion-less
    #    snapshot again).
    op.execute(f"REVOKE ALL ON FUNCTION {_STANDALONE_COMPLETE_FUNCTION} FROM PUBLIC")
    for role in _LONG_LIVED_ROLES:
        op.execute(
            f"REVOKE ALL ON FUNCTION {_STANDALONE_COMPLETE_FUNCTION} FROM {role}"
        )

    # 5. Forward-only repair of the 017 content-type update function
    #    (historical 017 is immutable): exact signature, result shape,
    #    security and grants; qualified identifiers; partial-update
    #    COALESCE semantics.
    op.execute(_CONTENT_TYPE_UPDATE_REPAIR_SQL)
    op.execute(
        f"REVOKE ALL ON FUNCTION {_CONTENT_TYPE_UPDATE_REPAIR_FUNCTION} FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION {_CONTENT_TYPE_UPDATE_REPAIR_FUNCTION} "
        "TO slaif_editor_runtime, slaif_control"
    )

    # 6. Accept entry points re-emitted (072 history is immutable).
    op.execute(f"DROP FUNCTION IF EXISTS {_OLD_HUMAN_ACCEPT_FUNCTION}")
    op.execute(f"DROP FUNCTION IF EXISTS {_OLD_INNER_ACCEPT_FUNCTION}")
    op.execute(_INNER_ACCEPT_SQL)
    op.execute(f"ALTER FUNCTION {_INNER_ACCEPT_FUNCTION} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_INNER_ACCEPT_FUNCTION} FROM PUBLIC")
    for role in _LONG_LIVED_ROLES:
        op.execute(f"REVOKE ALL ON FUNCTION {_INNER_ACCEPT_FUNCTION} FROM {role}")
    # The inner enqueue keeps NO role EXECUTE grants (owner-internal),
    # closing the legacy actorless enqueue bypass.
    op.execute(_HUMAN_ACCEPT_SQL)
    op.execute(f"ALTER FUNCTION {_HUMAN_ACCEPT_FUNCTION} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_HUMAN_ACCEPT_FUNCTION} FROM PUBLIC")
    for role in _LONG_LIVED_ROLES:
        op.execute(f"REVOKE ALL ON FUNCTION {_HUMAN_ACCEPT_FUNCTION} FROM {role}")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_HUMAN_ACCEPT_FUNCTION} TO slaif_control")


def downgrade() -> None:
    # Explicit fail-closed refusal (no conditional restoration path):
    # rolling back below 079 would restore the companion-less
    # completion EXECUTE and the digest-less accept entry points while
    # 079-era manifest/receipt history persists, leaving the approval
    # state ambiguous.  The refusal raises before any restoration and
    # touches no canonical, pending, audit, manifest or snapshot state.
    # The bootstrap operator path refuses this rollback earlier still
    # (before the readiness PENDING marker and the content COW
    # disable); this body is the defense for direct migration
    # invocations.
    op.execute(
        """
        DO $guard$
        BEGIN
            IF to_regclass('control.review_operation_manifest') IS NOT NULL
               OR EXISTS (SELECT 1 FROM audit.promotion
                          WHERE manifest_id IS NOT NULL)
            THEN
                RAISE EXCEPTION
                    'REVIEWED_OPERATION_BINDING_DOWNGRADE_REFUSED'
                    USING ERRCODE = 'P0001';
            END IF;
        END $guard$;
        """
    )
