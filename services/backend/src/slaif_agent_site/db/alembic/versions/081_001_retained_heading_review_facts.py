# ruff: noqa: E501
"""Retain the recorded heading row effects in the immutable review.

The 083/13 pilot recorded one exact ``heading-row-effect/v1`` row per
successful changed heading-props write (062 Agent definer and 060
Human-on-Agent Editor definer) in the same transaction as the COW
write.  Those facts live in ``audit.heading_row_effect`` bound to the
workspace - but a COW workspace's pending rows are consumed by
acceptance (canonical publication) or rolled back by discard, so the
per-operation images of a reviewed session are only recoverable
through the immutable review this migration adds.

Two functions and one table, nothing else:

1. ``control.heading_review_retention`` - at most one row per review
   snapshot, owner-only (no PUBLIC, no role grants; the two definers
   below run as the owner).  The row binds the retained facts to the
   EXACT immutable review identity:

   - the snapshot id (primary key, referencing
     ``control.review_snapshot``), plus the snapshot's own digest and
     the site/workspace the snapshot names;
   - the reviewed-operations companion's ``manifest_digest``
     (``control.review_operation_manifest`` for the same snapshot),
     so the retained set is bound to the exact reviewed operation set
     as well as the exact frozen content;
   - ``schema_version`` ``retained-heading-facts/v1``, the ordered
     ``facts`` JSON array, its count, its exact canonical UTF-8 byte
     count and its SHA-256 ``facts_digest`` over the 070 canonical
     serialization - an explicit version and digest for
     deterministic exact read and replay;

   The snapshot digest is over the frozen content only; the retained
   facts are review evidence attached to the immutable review, never
   an input to the existing accept approval (snapshot id + domain
   digest + manifest digest), which is preserved byte-for-byte.

2. ``control.slaif_review_retain_heading_facts(uuid, uuid)`` -
   owner-only SECURITY DEFINER, EXECUTE for ``slaif_review_worker``
   only, called by the freeze worker INSIDE the one locked freeze
   transaction, after the snapshot + companion + REVIEW transition
   and before the job's SUCCEEDED terminal, so the capture is atomic
   with the review it describes: any refusal below rolls back the
   snapshot row, the companion row, the pointer and the job state
   together (no partial freeze or review state, the workspace stays
   FREEZING, the earlier committed mutation facts are untouched).

   The capture selects from the ACTUAL reviewed operation set: the
   exact companion's stored ``operation_ids`` for this snapshot.
   The retained set is that reviewed selection only - never "every
   prior workspace fact" - and every selected fact requires the
   existing trusted binding to the manifest's completion
   identities: the record's family, principal (capability for
   ``agent``, human user for ``human_editor``) and resource (the
   component id) field-for-field the identity's.  A selected fact
   without that binding is a known inconsistent state and is refused
   (``HEADING_RETENTION_BINDING_MISMATCH``) before any write; a fact
   whose operation is outside the reviewed set is not retained and
   not claimed as reviewed.  The manifest companion is re-resolved
   from the stored snapshot row (id/digest/site/workspace,
   column-qualified predicates, never caller-selected).

   Stored bytes are derived entirely on the trusted path from the
   stored rows; the caller supplies only the workspace and site.
   Every record preserves the full checked image pair
   (``props_before``/``props_after``), the row versions
   (``row_version_before``/``row_version_after``) and the exact
   operation identity (``operation_id``, ``family``,
   ``principal_type``/``principal_id``) - including intermediate
   facts for reviewed operations when the final props return to their
   original value (each recorded write keeps its own row, so a
   v1 -> v2 -> v1 session retains both transitions).

   Ordering is deterministic WITHOUT a causal claim: the known
   per-row transition orders each component's facts by
   ``row_version_before``, and the tie-break across unrelated
   components is the native UUID order of ``component_id`` (then
   ``operation_id``) - stable and locale-independent, but explicitly
   not a statement about when unrelated components were edited.

   Budgets are checked BEFORE materialization or aggregation:

   - at most 256 records per review, checked on the whole genuine
     080 fact set of the exact site/workspace BEFORE selection and
     materialization (a superset of the retained reviewed selection;
     in a coherent state the two counts coincide, and the superset
     bound can only be stricter, never looser);
   - each stored props image of a selected record at most 16384
     octets (re-asserted on the trusted path; the 080 table
     constraint already bounds the source);
   - a total-byte bound on the EXACT selected records measured BEFORE
     materialization or aggregation: the UTF-8 codepoint count of the
     two variable-size props images of each selected fact (every
     canonical byte of a props value costs at least one canonical
     byte per codepoint, since 070 ASCII-escapes non-ASCII, so the
     codepoint sum can never overstate the canonical size), refused
     when it alone exceeds the ceiling;
   - the whole ordered facts array at most 1048576 exact canonical
     UTF-8 bytes (070 canonical serialization), with the same cheap
     conservative lower-bound pre-check the 079 companion uses so an
     over-budget set is refused before the per-codepoint canonical
     serializer runs (the authoritative exact measurement).

   A budget violation is a stable terminal refusal
   (``HEADING_RETENTION_OVER_BUDGET``) that rolls back the entire
   freeze transaction.

3. ``control.slaif_review_heading_effects_read(uuid, uuid, uuid,
   uuid)`` - owner-only SECURITY DEFINER, STABLE, EXECUTE for
   ``slaif_control`` only (the existing authorized review boundary;
   the Control process calls it behind the same human membership
   gate as the 071 review read model).  Current human membership (or
   platform administration) is re-checked, and the resolved
   snapshot row's OWN site and workspace are bound to the authorized
   site and workspace.  The third argument names the exact retained
   snapshot: absent (NULL), the CURRENT review follows the trusted
   pointer (``control.workspace.review_snapshot_id``); present, the
   retained lookup binds the EXACT requested snapshot, whose
   site/workspace association is checked against the snapshot row
   itself.  The served row is additionally bound to its exact
   companion (manifest digest, site, workspace) and every served
   record is re-checked at read time against the companion's
   completion identities (operation, family, principal, resource),
   so the served set is exactly the retained reviewed-operation
   subset.  A pre-feature
   snapshot (frozen before this revision, no retention row) is
   represented as ``status: unavailable`` with the reason
   ``pre_feature_snapshot``; a genuinely captured empty set is
   ``status: captured`` with an empty facts array - the two are
   distinguished in the response, and only gate failures (not a
   member, wrong site, unknown id, no review) take the existing
   uniform 404 behavior, exactly like the 071 read model.  The
   document is narrow (binding + digest + the retained facts) and is
   never echoed into error responses (every refusal is the one stable
   class the HTTP layer maps to the uniform 404); the worker and this
   read are the only exposure of the owner-restricted table.

The new ``control`` table receives no grants at all: the worker
inserts through its one definer and the human review read goes
through its own; no other role gains any access to the retained
facts.

Downgrade is an explicit fail-closed refusal (no conditional path):
retained rows reference snapshot rows and re-derive from 080 facts
that later migrations' definer bodies no longer interpret; the
bootstrap operator path refuses the rollback before any operator
effect, and this migration's own downgrade body is the second line of
defense.  This revision adds no new grant surface beyond the two
narrow definers and no foundation change.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "081_001"
down_revision: str | Sequence[str] | None = "080_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Finite work budgets (historical literals of this migration; the
# freeze worker and the tests mirror the exact values).
_MAX_RETAINED_RECORDS = 256
_MAX_RETAINED_VALUE_BYTES = 16384
_MAX_RETAINED_FACTS_BYTES = 1048576
_HEX64_RE = "^[0-9a-f]{64}$"

_RETENTION_TABLE = "control.heading_review_retention"
_CAPTURE_FUNCTION = "control.slaif_review_retain_heading_facts(uuid, uuid)"
_READ_FUNCTION = "control.slaif_review_heading_effects_read(uuid, uuid, uuid, uuid)"
_ROLES_WITHOUT_RETENTION_ACCESS = (
    "slaif_control",
    "slaif_editor_runtime",
    "slaif_agent_runtime",
    "slaif_reviewer",
    "slaif_review_worker",
    "slaif_public_reader",
    "slaif_preview_reader",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
)

_RETENTION_TABLE_SQL = f"""
        CREATE TABLE {_RETENTION_TABLE} (
            snapshot_id uuid PRIMARY KEY
                REFERENCES control.review_snapshot(id),
            site_id uuid NOT NULL,
            workspace_id uuid NOT NULL,
            schema_version text NOT NULL
                DEFAULT 'retained-heading-facts/v1',
            snapshot_digest text NOT NULL,
            operation_manifest_digest text NOT NULL,
            facts jsonb NOT NULL,
            fact_count integer NOT NULL,
            facts_bytes integer NOT NULL,
            facts_digest text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT heading_review_retention_schema_version CHECK (
                schema_version = 'retained-heading-facts/v1'
            ),
            CONSTRAINT heading_review_retention_digest_shape CHECK (
                snapshot_digest ~ '{_HEX64_RE}'
                AND operation_manifest_digest ~ '{_HEX64_RE}'
                AND facts_digest ~ '{_HEX64_RE}'
            ),
            CONSTRAINT heading_review_retention_facts_array CHECK (
                jsonb_typeof(facts) = 'array'
            ),
            CONSTRAINT heading_review_retention_count_shape CHECK (
                fact_count >= 0 AND fact_count = jsonb_array_length(facts)
            ),
            CONSTRAINT heading_review_retention_bytes_shape CHECK (
                facts_bytes >= 0
                AND facts_bytes <= {_MAX_RETAINED_FACTS_BYTES}
            )
        )
"""

_CAPTURE_SQL = f"""
        CREATE FUNCTION control.slaif_review_retain_heading_facts(
            p_workspace_id uuid, p_site_id uuid
        ) RETURNS text LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            v_snapshot_id uuid;
            snap_id uuid;
            snap_digest text;
            snap_site uuid;
            snap_workspace uuid;
            snap_status text;
            man_snapshot_digest text;
            man_digest text;
            man_site uuid;
            man_workspace uuid;
            man_ops uuid[];
            man_identities jsonb;
            n integer;
            facts jsonb;
            facts_bytes bigint;
        BEGIN
            IF p_workspace_id IS NULL OR p_site_id IS NULL
            THEN RAISE EXCEPTION 'HEADING_RETENTION_INPUT'
                USING ERRCODE = 'P0001';
            END IF;
            -- Trusted pointer: the snapshot this freeze transaction
            -- just completed (never caller-selected).
            SELECT control.workspace.review_snapshot_id
              INTO v_snapshot_id
            FROM control.workspace WHERE id = p_workspace_id;
            IF NOT FOUND OR v_snapshot_id IS NULL THEN
                RAISE EXCEPTION 'HEADING_RETENTION_NOT_READY'
                    USING ERRCODE = 'P0001';
            END IF;
            SELECT id, digest, site_id, workspace_id, status
              INTO snap_id, snap_digest, snap_site, snap_workspace,
                   snap_status
            FROM control.review_snapshot WHERE id = v_snapshot_id;
            IF NOT FOUND
               OR snap_status IS DISTINCT FROM 'COMPLETE'
               OR snap_site IS DISTINCT FROM p_site_id
               OR snap_workspace IS DISTINCT FROM p_workspace_id
            THEN RAISE EXCEPTION 'HEADING_RETENTION_BINDING'
                USING ERRCODE = 'P0001';
            END IF;
            -- The companion of that exact snapshot: re-resolved
            -- from the stored row with a column-qualified predicate
            -- against the v_snapshot_id variable (never a same-name
            -- column), binding the exact reviewed operation set.
            SELECT snapshot_digest, manifest_digest, site_id,
                   workspace_id, operation_ids, completion_identities
              INTO man_snapshot_digest, man_digest, man_site,
                   man_workspace, man_ops, man_identities
            FROM control.review_operation_manifest
            WHERE control.review_operation_manifest.snapshot_id
                  = v_snapshot_id;
            IF NOT FOUND
               OR man_snapshot_digest IS DISTINCT FROM snap_digest
               OR man_site IS DISTINCT FROM p_site_id
               OR man_workspace IS DISTINCT FROM p_workspace_id
            THEN RAISE EXCEPTION 'HEADING_RETENTION_BINDING'
                USING ERRCODE = 'P0001';
            END IF;
            -- Record budget BEFORE selection, materialization or
            -- aggregation: the bound covers the whole genuine 080
            -- fact set of this exact site/workspace, a superset of
            -- the reviewed selection below (in a coherent state
            -- every recorded heading fact's operation is a member
            -- of the workspace's session universe, so the two
            -- counts coincide; out-of-set facts can only make the
            -- bound stricter, never looser).
            SELECT count(*) INTO n
            FROM audit.heading_row_effect AS f
            WHERE f.site_id = p_site_id
              AND f.workspace_id = p_workspace_id;
            IF n > {_MAX_RETAINED_RECORDS} THEN
                RAISE EXCEPTION 'HEADING_RETENTION_OVER_BUDGET'
                    USING ERRCODE = 'P0001';
            END IF;
            -- Trusted binding of the RETAINED set: the capture
            -- selects from the actual reviewed operation set (the
            -- exact companion's stored operation_ids), and every
            -- selected fact must carry the existing trusted
            -- completion identity of its operation - family,
            -- principal (capability for agent, human user for
            -- human_editor) and the family-specific resource
            -- binding (composition_node for agent, editor.sites for
            -- human_editor) plus the resource (the component).  A
            -- selected fact without that binding is a known
            -- inconsistent state: refuse before any write.  Facts
            -- whose operation is outside the reviewed set are not
            -- retained and are not claimed as reviewed.
            SELECT count(*) INTO n
            FROM audit.heading_row_effect AS f
            WHERE f.site_id = p_site_id
              AND f.workspace_id = p_workspace_id
              AND f.operation_id = ANY(man_ops)
              AND NOT EXISTS (
                  SELECT 1
                  FROM jsonb_array_elements(man_identities)
                       AS ci(value)
                  WHERE (SELECT count(*)
                          FROM jsonb_object_keys(ci.value)) = 9
                    AND ci.value->>'operation_id'
                        = f.operation_id::text
                    AND ci.value->>'family' = f.family
                    AND (CASE WHEN f.family = 'agent'
                              THEN 'capability'
                              ELSE 'human_user' END)
                        = ci.value->>'principal_type'
                    AND (CASE WHEN f.family = 'agent'
                              THEN f.capability_id::text
                              ELSE f.human_user_id::text END)
                        = ci.value->>'principal_id'
                    AND ci.value->>'resource_id'
                        = f.component_id::text
                    AND ci.value->>'resource_type'
                        = (CASE WHEN f.family = 'agent'
                                THEN 'composition_node'
                                ELSE 'editor.sites' END)
              );
            IF n <> 0 THEN
                RAISE EXCEPTION 'HEADING_RETENTION_BINDING_MISMATCH'
                    USING ERRCODE = 'P0001';
            END IF;
            -- Value budget re-asserted on the trusted path for
            -- exactly the selected records that will be stored
            -- (the 080 table constraint already bounds every
            -- source image): an out-of-shape selected row is
            -- refused, never stored.
            IF EXISTS (
                SELECT 1 FROM audit.heading_row_effect AS f
                WHERE f.site_id = p_site_id
                  AND f.workspace_id = p_workspace_id
                  AND f.operation_id = ANY(man_ops)
                  AND (octet_length(f.props_before::text)
                       > {_MAX_RETAINED_VALUE_BYTES}
                       OR octet_length(f.props_after::text)
                       > {_MAX_RETAINED_VALUE_BYTES})
            ) THEN
                RAISE EXCEPTION 'HEADING_RETENTION_OVER_BUDGET'
                    USING ERRCODE = 'P0001';
            END IF;
            -- Total-byte bound on the EXACT selected records BEFORE
            -- materialization or aggregation: every UTF-8 codepoint
            -- of a props value costs at least one canonical byte
            -- (070 ASCII-escapes non-ASCII, so the codepoint count
            -- can never overstate the canonical size), and the
            -- remaining record fields are non-negative, so this
            -- sum is a conservative total-byte lower bound.  It can
            -- only refuse a set whose canonical serialization must
            -- exceed the ceiling - never an in-budget one.
            SELECT coalesce(sum(length(f.props_before::text)
                                + length(f.props_after::text)), 0)
              INTO n
            FROM audit.heading_row_effect AS f
            WHERE f.site_id = p_site_id
              AND f.workspace_id = p_workspace_id
              AND f.operation_id = ANY(man_ops);
            IF n > {_MAX_RETAINED_FACTS_BYTES} THEN
                RAISE EXCEPTION 'HEADING_RETENTION_OVER_BUDGET'
                    USING ERRCODE = 'P0001';
            END IF;
            -- Deterministic ordering without a causal claim: the
            -- known per-row transition orders each component's
            -- facts by row_version_before; the tie-break across
            -- unrelated components is the native UUID order of
            -- component_id, then operation_id.  The complete checked
            -- image pair, versions and exact operation identity are
            -- preserved, including intermediate facts when the final
            -- props return to their original value.
            SELECT coalesce(
                jsonb_agg(rec ORDER BY component_id,
                          row_version_before, operation_id),
                '[]'::jsonb
            ) INTO facts
            FROM (
                SELECT jsonb_build_object(
                    'operation_id', f.operation_id::text,
                    'family', f.family,
                    'component_id', f.component_id::text,
                    'row_version_before', f.row_version_before,
                    'row_version_after', f.row_version_after,
                    'props_before', f.props_before,
                    'props_after', f.props_after,
                    'principal_type',
                        CASE WHEN f.family = 'agent'
                             THEN 'capability'
                             ELSE 'human_user' END,
                    'principal_id',
                        CASE WHEN f.family = 'agent'
                             THEN f.capability_id::text
                             ELSE f.human_user_id::text END
                ) AS rec,
                f.component_id,
                f.row_version_before,
                f.operation_id
                FROM audit.heading_row_effect AS f
                WHERE f.site_id = p_site_id
                  AND f.workspace_id = p_workspace_id
                  AND f.operation_id = ANY(man_ops)
            ) AS rows(rec, component_id, row_version_before,
                      operation_id);
            -- Cheap conservative canonical-byte LOWER BOUND before
            -- the expensive serialization (the 079 companion
            -- pattern): native jsonb text minus the separator space
            -- after each structural ':' and ','; literal
            -- replacement, so identical patterns inside string
            -- values only make the bound tighter.  The exact 070
            -- canonical check below measures the actual canonical
            -- encoding (070 ASCII-escapes Unicode) and can never be
            -- shorter than this bound, so an in-budget set can never
            -- be refused here.
            IF octet_length(convert_to(
                   replace(replace(facts::text, ': ', ':'), ', ', ','),
                   'UTF8')) > {_MAX_RETAINED_FACTS_BYTES}
            THEN
                RAISE EXCEPTION 'HEADING_RETENTION_OVER_BUDGET'
                    USING ERRCODE = 'P0001';
            END IF;
            facts_bytes := length(convert_to(
                control.slaif_canonical_jsonb_text(facts), 'UTF8'));
            IF facts_bytes > {_MAX_RETAINED_FACTS_BYTES} THEN
                RAISE EXCEPTION 'HEADING_RETENTION_OVER_BUDGET'
                    USING ERRCODE = 'P0001';
            END IF;
            INSERT INTO {_RETENTION_TABLE} (
                snapshot_id, site_id, workspace_id,
                snapshot_digest, operation_manifest_digest, facts,
                fact_count, facts_bytes, facts_digest
            ) VALUES (
                v_snapshot_id, p_site_id, p_workspace_id,
                snap_digest, man_digest, facts,
                jsonb_array_length(facts), facts_bytes,
                encode(sha256(convert_to(
                    control.slaif_canonical_jsonb_text(facts), 'UTF8'
                )), 'hex')
            );
            RETURN encode(sha256(convert_to(
                control.slaif_canonical_jsonb_text(facts), 'UTF8'
            )), 'hex');
        END;
        $fn$
"""

_READ_SQL = """
        CREATE FUNCTION control.slaif_review_heading_effects_read(
            p_workspace_id uuid, p_site_id uuid, p_snapshot_id uuid,
            p_user_account_id uuid
        ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER STABLE
        SET search_path = pg_catalog AS $fn$
        DECLARE
            ws_site uuid;
            v_snapshot_id uuid;
            snap control.review_snapshot%ROWTYPE;
            man_digest text;
            man_site uuid;
            man_workspace uuid;
            man_identities jsonb;
            row control.heading_review_retention%ROWTYPE;
            n bigint;
        BEGIN
            -- The existing authorized review boundary: the same
            -- uniform gate class as the 071 review read model, so
            -- the HTTP layer maps every gate failure to the same
            -- uniform 404 (no oracle distinguishes "not a member",
            -- "unknown id", "wrong site" and "no review").
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
            SELECT site_id INTO ws_site
            FROM control.workspace WHERE id = p_workspace_id;
            IF NOT FOUND OR ws_site IS DISTINCT FROM p_site_id THEN
                RAISE EXCEPTION 'REVIEW_READ_UNAVAILABLE'
                    USING ERRCODE = 'P0002';
            END IF;
            -- Absent named snapshot: the CURRENT review follows the
            -- trusted pointer.  Present: the retained lookup binds
            -- the EXACT requested snapshot, independent of the
            -- pointer.
            IF p_snapshot_id IS NULL THEN
                SELECT control.workspace.review_snapshot_id
                  INTO v_snapshot_id
                FROM control.workspace WHERE id = p_workspace_id;
                IF NOT FOUND OR v_snapshot_id IS NULL THEN
                    RAISE EXCEPTION 'REVIEW_READ_UNAVAILABLE'
                        USING ERRCODE = 'P0002';
                END IF;
            ELSE
                v_snapshot_id := p_snapshot_id;
            END IF;
            SELECT * INTO snap FROM control.review_snapshot
            WHERE id = v_snapshot_id;
            IF NOT FOUND
               OR snap.status IS DISTINCT FROM 'COMPLETE'
               OR snap.site_id IS DISTINCT FROM p_site_id
               OR snap.workspace_id IS DISTINCT FROM p_workspace_id
            THEN
                RAISE EXCEPTION 'REVIEW_READ_UNAVAILABLE'
                    USING ERRCODE = 'P0002';
            END IF;
            SELECT * INTO row FROM control.heading_review_retention
            WHERE control.heading_review_retention.snapshot_id
                  = v_snapshot_id;
            IF NOT FOUND THEN
                -- A snapshot frozen before this revision has no
                -- retention row: its missing evidence is
                -- unavailable (distinct from a captured empty set).
                RETURN jsonb_build_object(
                    'status', 'unavailable',
                    'reason', 'pre_feature_snapshot',
                    'schema_version', 'retained-heading-facts/v1',
                    'snapshot_id', v_snapshot_id::text,
                    'snapshot_digest', snap.digest
                );
            END IF;
            -- Defensive binding integrity: a row whose binding
            -- diverges from the resolved snapshot is never served.
            IF row.site_id IS DISTINCT FROM p_site_id
               OR row.workspace_id IS DISTINCT FROM p_workspace_id
               OR row.snapshot_digest IS DISTINCT FROM snap.digest
            THEN
                RAISE EXCEPTION 'REVIEW_READ_UNAVAILABLE'
                    USING ERRCODE = 'P0002';
            END IF;
            -- The exact companion of the resolved snapshot
            -- (column-qualified predicate): the stored row must
            -- bind the same manifest digest, site and workspace.
            SELECT manifest_digest, site_id, workspace_id,
                   completion_identities
              INTO man_digest, man_site, man_workspace, man_identities
            FROM control.review_operation_manifest
            WHERE control.review_operation_manifest.snapshot_id
                  = v_snapshot_id;
            IF NOT FOUND
               OR man_digest IS DISTINCT FROM row.operation_manifest_digest
               OR man_site IS DISTINCT FROM p_site_id
               OR man_workspace IS DISTINCT FROM p_workspace_id
            THEN
                RAISE EXCEPTION 'REVIEW_READ_UNAVAILABLE'
                    USING ERRCODE = 'P0002';
            END IF;
            -- The served set is exactly the retained
            -- reviewed-operation subset: every stored record is
            -- re-checked at read time against the companion's
            -- completion identities (operation, family, principal,
            -- resource type and id).  A divergence from the
            -- immutable review identity is a uniform refusal, never
            -- served, and the served set never claims every prior
            -- workspace fact was reviewed.
            SELECT count(*) INTO n
            FROM jsonb_array_elements(row.facts) AS fact(value)
            WHERE NOT EXISTS (
                SELECT 1
                FROM jsonb_array_elements(man_identities)
                     AS ci(value)
                WHERE (SELECT count(*)
                        FROM jsonb_object_keys(ci.value)) = 9
                  AND ci.value->>'operation_id'
                      = fact.value->>'operation_id'
                  AND ci.value->>'family' = fact.value->>'family'
                  AND ci.value->>'principal_type'
                      = fact.value->>'principal_type'
                  AND ci.value->>'principal_id'
                      = fact.value->>'principal_id'
                  AND ci.value->>'resource_id'
                      = fact.value->>'component_id'
                  AND ci.value->>'resource_type'
                      = (CASE WHEN fact.value->>'family' = 'agent'
                              THEN 'composition_node'
                              ELSE 'editor.sites' END)
            );
            IF n <> 0 THEN
                RAISE EXCEPTION 'REVIEW_READ_UNAVAILABLE'
                    USING ERRCODE = 'P0002';
            END IF;
            RETURN jsonb_build_object(
                'status', 'captured',
                'schema_version', row.schema_version,
                'snapshot_id', v_snapshot_id::text,
                'snapshot_digest', row.snapshot_digest,
                'operation_manifest_digest',
                    row.operation_manifest_digest,
                'fact_count', row.fact_count,
                'facts_bytes', row.facts_bytes,
                'facts_digest', row.facts_digest,
                'facts', row.facts
            );
        END;
        $fn$
"""


def upgrade() -> None:
    op.execute(_RETENTION_TABLE_SQL)
    op.execute(f"ALTER TABLE {_RETENTION_TABLE} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON TABLE {_RETENTION_TABLE} FROM PUBLIC")
    for role in _ROLES_WITHOUT_RETENTION_ACCESS:
        op.execute(f"REVOKE ALL ON TABLE {_RETENTION_TABLE} FROM {role}")

    op.execute(_CAPTURE_SQL)
    op.execute(f"ALTER FUNCTION {_CAPTURE_FUNCTION} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_CAPTURE_FUNCTION} FROM PUBLIC")
    for role in _ROLES_WITHOUT_RETENTION_ACCESS:
        op.execute(f"REVOKE ALL ON FUNCTION {_CAPTURE_FUNCTION} FROM {role}")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_CAPTURE_FUNCTION} TO slaif_review_worker")

    op.execute(_READ_SQL)
    op.execute(f"ALTER FUNCTION {_READ_FUNCTION} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_READ_FUNCTION} FROM PUBLIC")
    for role in _ROLES_WITHOUT_RETENTION_ACCESS:
        op.execute(f"REVOKE ALL ON FUNCTION {_READ_FUNCTION} FROM {role}")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_READ_FUNCTION} TO slaif_control")


def downgrade() -> None:
    # Explicit fail-closed refusal (no conditional path): the retained
    # rows reference snapshot rows and re-derive from 080 facts that
    # no later definer body re-interprets, and no supported path can
    # re-derive which historical reviews carried retained facts.  The
    # refusal raises before any removal and touches no canonical,
    # pending, audit, snapshot or retention state.  The bootstrap
    # operator path refuses this rollback earlier still; this body is
    # the defense for direct migration invocations.
    op.execute(
        """
        DO $guard$
        BEGIN
            RAISE EXCEPTION
                'HEADING_RETENTION_DOWNGRADE_UNSUPPORTED'
                USING ERRCODE = 'P0001';
        END $guard$;
        """
    )
