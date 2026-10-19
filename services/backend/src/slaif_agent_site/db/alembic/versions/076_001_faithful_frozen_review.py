# ruff: noqa: E501
"""Faithful frozen review: complete domain capture and frozen inputs (083/5).

Round 083-5-a increment.  This migration supersedes the 075_001 materializer
and snapshot completion contract with the explicit ``review-snapshot/v2``
format and adds the read-only frozen-review surface functions.

Patch 1: the bounded pre-aggregation helpers.  Patch 2: the trusted
version-facts pins — ``control.workspace.version_facts`` jsonb column
plus CREATE OR REPLACE of the three workspace INSERT paths (024 / 028 /
038) recording the six supported product version literals; downgrade
restores the verbatim 075-era bodies (owner/ACL preserving) and drops
the column.

``slaif_review_string_cost(p_text)`` computes the exact escaped length the
070 canonical jsonb string form would produce, by one bounded linear
traversal of the explicit UTF-8 byte stream
(``convert_to(p_text, 'UTF8')`` bytea, read with ``get_byte`` — the same
trusted PostgreSQL 14-compatible primitives the 070 canonical family
already uses).  Byte values classify directly (lead bytes 0xC2-0xDF /
0xE0-0xEF / 0xF0-0xF4 open two-/three-/four-byte characters; 0x80-0xBF are
continuations; 0x01-0x1F and 0x7F are the other control characters; 8, 9,
10, 12, 13 are the named short escapes; 34 and 92 are quote/backslash).
No regex, no collation, no character-class construction, no table, no
server-encoding reinterpretation; structural checks fail closed with
``REVIEW_STRING_COST_INVALID_UTF8``.

``slaif_review_value_cost(p_value, p_running, p_budget)`` is the exact
canonical-text length for a jsonb value accumulated from a running offset;
it returns -1 (sticky) as soon as the running total exceeds the budget so
callers short-circuit before unbounded aggregation or canonical
construction.  ``slaif_review_value_depth(p_value, p_remaining)`` counts
container nesting levels (empty object/array = 1, scalar = 0) with an
early exit returning ``p_remaining + 1``.

Provenance: the accounting and the ``value_cost``/``value_depth`` control
flow were validated by the 2026-10-18 cost probe
(``cost-probe2-source-reviewed.sql``, sha256
``930d6b15c686903d2905af7b7bbe431d3a5d7cde6b6d83493bec064e2b017bd4``,
result ``COST_PROBE_FAIL=[]``) on PostgreSQL 18, where the probe used
``regexp_count`` (PostgreSQL 15+, collation-dependent ranges) — a
probe-only method, not the production path.  The production byte-scan form
requires fresh qualified execution on PostgreSQL 14 and 18 against the
verbatim 070 canonical family (hostile vectors, over-budget/depth
behavior, owner/search_path/ACL, coherent upgrade/downgrade); that
qualification is pending, not done.  The materializer (a later same-file
patch) enforces bounded depth before recursive cost and budget before
aggregate allocation.  Upgrade/downgrade stay coherent at every patch
boundary: downgrading from this patch restores exactly the 075_001 state.

Patch 3: the ``review-snapshot/v2`` materializer.  ``upgrade`` installs the
media-closure helper ``slaif_review_media_append(uuid,uuid,jsonb)``
(owner-only: no grants; consumed exclusively inside the owner SECURITY
DEFINER materializer) and then replaces the 075 materializer body via
CREATE OR REPLACE with the v2 body, re-asserting the exact 070/075
ownership/ACL pattern (owner slaif_owner, PUBLIC and every product role
revoked, EXECUTE granted to slaif_review_worker only).

The v2 body captures the complete trusted domain per family with declared
row/cost shares (pages 4096/262144; compositions 131072/1048576 with
per-page node and cost pre-bounds; type/field/view pools 262144; items
1572864; translations 524288; relations 262144; locales 32/65536; theme
1/65536; regions 8/262144; navigation 16 + 4096 items pool 131072;
redirects 256/65536; media inventory 4096/524288; proposals
10000/262144) and a final 8 MiB total canonical-text budget.  Raw value
depth (<= 8) is refused before any recursive cost, and every cost is
measured on bounded raw inputs before aggregation (``to_jsonb`` on the
loop record, never pre-escaped JSON text).  The version-facts gate
refuses empty pins (REVIEW_WORKSPACE_VERSION_UNKNOWN) and any drift from
the six supported literals (SNAPSHOT_VALIDATION_FAILED); media closure
is composition references plus declared media/document content fields at
declared cardinality, each reference resolved same-site through the 068
helper and refused as REVIEW_MEDIA_REF_UNRESOLVED.

Provenance: v2 materializer source sha256
1d08724dd3e93851b92dcf63ca8058d9c915955267b59d8710bab2dcc06c4ac7
(1259 lines, revision 4; superseded revisions part1 afb367e0... and
full-first 476609d6... are archived in the round workspace).  Strategy
source reviews closed: part1 (3 findings), complete-first (6 findings),
rev3 preflight (raw depth before recursive cost; typed ``to_jsonb``
record access), rev4 delta (UUID parent_key ordering; restored family
caps) - "no further source correction requested at this stage".
Scratch runtime smoke on PostgreSQL 18 (2026-10-18, literal
chronology): happy path 15 checks PASS; first negative batch
(14:54:12Z) 1 pass / 13 fail (unhandled expected errors plus the
case-14 fixture bug); corrected batch (14:54:57Z) 13 pass / 1 fail
(the NEG10 message check was wrong); a subsequent harness variant that
called the non-existent get_stack() failed at 14:55:14Z; the final
corrected NEG10 depth-9 harness (SQLSTATE P0002 + message identity)
passed targeted reruns at 15:01:29Z and 15:05:33Z, with the real
first-run DETAIL "composition props raw depth" retained from the
14:54:12Z raw output.  No fresh all-14 negative pass was observed.
Media-append helper source sha256
1a5d1f95dacc3dcf5e9db9af63522b92bdb19057a3ca3ad395473dbeba1b7574.

Downgrade restores the 070_001 snapshot completion body, the 075_001
materializer body, and (re-asserting the ownership/ACL pattern at each
step) drops the four 076 functions in reverse installation order,
restores the 075-era constructor bodies, and drops the version_facts
column; the full 075->076->075 alembic roundtrip (state capture
byte-identical across the roundtrip, constructors invoked after the
downgrade) is a required F gate whose qualification is pending, as
recorded in the Patch 4 provenance below.

Patch 4: the ``review-snapshot/v2`` completion contract.
``slaif_review_snapshot_complete(uuid,jsonb)`` is replaced via CREATE
OR REPLACE with the v2 body, which keeps the 070 envelope invariants
(row shape, uuid/COMPLETE status, non-negative watermark, 64-hex
digest, created_by shape, FREEZING->REVIEW transition) and adds the v2
invariants: (a) ``normalized_state`` is the identical document to
``payload`` (jsonb value equality); (b) the payload carries the
complete trusted domain capture (state_version ``review-snapshot/v2``,
18-key set including ``workspace_versions``,
``page_compositions``, the six-part ``content`` block,
``proposals`` and ``media_inventory``); (c) ``media_references`` is the
payload media map entry for entry (reference shape, both directions,
no duplicate ids); (d) every ``browser_evidence`` id is a COMPLETED
``control.browser_run`` of this workspace; (e)
``workspace_versions`` is the exact trusted six-pin set; (f) context
binding - the row's ``site_id`` and ``workspace_versions`` must equal
the actual selected workspace's ``site_id`` and ``version_facts``
(trusted facts, not supplied-supplied agreement; read under the
existing freeze-transaction row lock).  The digest is
recomputed over the stored payload in the 070 canonical form; the v2
Python serializer is byte-identical to it for every supported value.
Downgrade first refuses when retained review-snapshot/v2 rows exist
(SNAPSHOT_DOWNGRADE_RETAINED_V2, P0002, before any destructive
restoration) and then restores the 070_001 v1 body (verbatim $fn$
body, plain CREATE FUNCTION header adjusted to CREATE OR REPLACE per
the 075_001 restoration convention) with the owner/ACL pattern
re-asserted.  The 075->076->075 alembic roundtrip with a true 075
pre-upgrade baseline is a required F gate; its qualification is
pending the final coherent migration (an earlier
printed-comparison probe did not qualify it).

Patch 5: the frozen-review read surface - the authorization/fetch
functions plus the active-preview and bound-run byte reads
(installed after snapshot completion and dropped in reverse order in
the downgrade): ``slaif_review_snapshot_frozen_state(uuid)`` (one
COMPLETE row as jsonb or NULL; EXECUTE slaif_preview_reader),
``slaif_review_projection_authorize(text,bytea,uuid)`` (no-touch
session + membership + snapshot-COMPLETE gate with the documented
frozen-read deltas: site-ACTIVE not required, workspace-ACTIVE
replaced by snapshot-COMPLETE; EXECUTE slaif_preview_reader),
``slaif_review_media_authorize(text,bytea,uuid,uuid)`` (same
predicates plus frozen ``media``-map membership returning the stored
content_hash/size/mime; EXECUTE slaif_media),
``slaif_media_preview_read(text,bytea,uuid,uuid,uuid,integer,
integer,integer)`` (delegates the full 054 active-preview chain to
``slaif_render_preview_authorize_internal`` with ``p_touch = false``,
then reads ``content.media_asset`` in the authorized workspace's
transaction-scoped COW context - the only authorized pre-freeze byte
path for Agent-pending media; EXECUTE slaif_media),
``slaif_browser_preview_binding_register(uuid,text,timestamptz)``
(trusted run binding, EXECUTE slaif_preview_reader only: first
binding records the credential sha256 digest, the ORIGINAL consumed
nonce, the verifier-checked expiry and the current attempt as
immutable ``control.browser_run`` facts - four columns plus
``browser_run_preview_binding_shape`` and the partial unique index
``browser_run_preview_binding_digest``; idempotent replay of the
exact original binding succeeds without rewriting any fact; a
rotated attempt, different expiry or foreign digest raises P0002;
called by Render atomically inside the 036 consume transaction so a
failed/rolled-back consume leaves no usable binding) and
``slaif_media_bound_preview_read(text,uuid)`` (confined run-bound
private byte read BEFORE freeze, EXECUTE slaif_media: digest-only
input, unique-indexed binding lookup with explicit non-NULL shape,
the actual 036 no-consume authorizer called with the original
binding nonce (advisory 280 before the run row lock, full binding
predicates, FOR UPDATE OF run), then a post-lock recheck of the full
digest/expiry/attempt/nonce invariants on the locked row; the
media service receives the existing credential only to hash it
(never the signing key, caller claims or a raw-token log); reads
``content.media_asset`` in the bound workspace's
transaction-scoped COW context).  All six: owner slaif_owner,
PUBLIC + every product role revoked, one targeted grant,
``search_path = pg_catalog``, fail-closed empty/NULL results.
Downgrade drops the bound functions (reverse order), the partial
unique index, the CHECK constraint and the four binding columns.
"""

from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module
from typing import Any

from alembic import op

revision: str = "076_001"
down_revision: str | Sequence[str] | None = "075_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 075_001 already holds the verbatim 070 materializer (downgrade
# restoration, byte-verified in the 083-4-a round) and the exact 070
# ownership/ACL pattern for the workspace-state function.  Import it rather
# than copy it: one source of truth for both materializer restorations.
_M075: Any = import_module(
    "slaif_agent_site.db.alembic.versions.075_001_freeze_revision_coherence"
)

_WORKSPACE_STATE = _M075._WORKSPACE_STATE
_REVOKE_ROLES = _M075._REVOKE_ROLES
_MATERIALIZER_075 = _M075._MATERIALIZER_075
_MATERIALIZER_070 = _M075._MATERIALIZER_070

_STRING_COST_SQL = r"""
        CREATE OR REPLACE FUNCTION control.slaif_review_string_cost(p_text text)
        RETURNS bigint LANGUAGE plpgsql IMMUTABLE STRICT
        SET search_path = pg_catalog AS $fn$
        DECLARE
            n bigint;
            b bytea;
            bytes bigint;
            i bigint;
            byte integer;
            pending smallint := 0;
            lead2_count bigint := 0;
            lead3_count bigint := 0;
            lead4_count bigint := 0;
            all_ctrl bigint := 0;
            short_count bigint := 0;
            meta_count bigint := 0;
            ascii_count bigint := 0;
        BEGIN
            -- Exact escaped-length accounting for the 070 canonical jsonb
            -- string form: every character costs 1, except quote and
            -- backslash and the five named short escapes (2), every other
            -- control character and every BMP character U+0080..U+FFFF
            -- (6 = \uXXXX), and every supplementary character
            -- U+10000..U+10FFFF (12 = \uXXXX\uXXXX surrogate pair).
            --
            -- One linear traversal of the explicit UTF-8 byte stream
            -- (convert_to + get_byte, the primitives the 070 canonical
            -- family already uses): lead bytes open characters,
            -- 0x80-0xBF must follow their lead, anything else structural
            -- is malformed.  convert_to output is always valid UTF-8 for
            -- PostgreSQL text, so the checks below are defensive
            -- fail-closed guards.
            n := length(p_text);
            b := convert_to(p_text, 'UTF8');
            bytes := length(b);
            FOR i IN 1..bytes LOOP
                byte := get_byte(b, i - 1);
                IF pending > 0 THEN
                    IF byte < 128 OR byte > 191 THEN
                        RAISE EXCEPTION 'REVIEW_STRING_COST_INVALID_UTF8'
                            USING ERRCODE = '22023';
                    END IF;
                    pending := pending - 1;
                ELSIF byte = 0 THEN
                    RAISE EXCEPTION 'REVIEW_STRING_COST_INVALID_UTF8'
                        USING ERRCODE = '22023';
                ELSIF byte < 128 THEN
                    ascii_count := ascii_count + 1;
                    IF (byte BETWEEN 1 AND 31) OR byte = 127 THEN
                        all_ctrl := all_ctrl + 1;
                        IF byte IN (8, 9, 10, 12, 13) THEN
                            short_count := short_count + 1;
                        END IF;
                    ELSIF byte = 34 OR byte = 92 THEN
                        meta_count := meta_count + 1;
                    END IF;
                ELSIF byte >= 194 AND byte <= 223 THEN
                    lead2_count := lead2_count + 1;
                    pending := 1;
                ELSIF byte >= 224 AND byte <= 239 THEN
                    lead3_count := lead3_count + 1;
                    pending := 2;
                ELSIF byte >= 240 AND byte <= 244 THEN
                    lead4_count := lead4_count + 1;
                    pending := 3;
                ELSE
                    RAISE EXCEPTION 'REVIEW_STRING_COST_INVALID_UTF8'
                        USING ERRCODE = '22023';
                END IF;
            END LOOP;
            IF pending > 0
               OR ascii_count + lead2_count + lead3_count + lead4_count <> n
            THEN
                RAISE EXCEPTION 'REVIEW_STRING_COST_INVALID_UTF8'
                    USING ERRCODE = '22023';
            END IF;
            RETURN n + meta_count + short_count
                + 5 * ((all_ctrl - short_count) + lead2_count
                       + lead3_count)
                + 11 * lead4_count;
        END;
        $fn$
"""

_VALUE_COST_SQL = r"""
        CREATE OR REPLACE FUNCTION control.slaif_review_value_cost(
            p_value jsonb, p_running bigint, p_budget bigint
        ) RETURNS bigint LANGUAGE plpgsql IMMUTABLE
        SET search_path = pg_catalog AS $fn$
        DECLARE
            key text;
            item jsonb;
            cost bigint;
            n integer;
        BEGIN
            IF p_running < 0 THEN RETURN -1; END IF;
            CASE jsonb_typeof(p_value)
            WHEN 'string' THEN
                cost := p_running + 2 + control.slaif_review_string_cost(
                    p_value #>> '{}'
                );
            WHEN 'number' THEN
                cost := p_running + length(p_value::text);
            WHEN 'boolean' THEN
                cost := p_running + length(p_value::text);
            WHEN 'null' THEN
                cost := p_running + 4;
            WHEN 'object' THEN
                SELECT count(*) INTO n FROM jsonb_object_keys(p_value) AS k;
                IF n = 0 THEN
                    cost := p_running + 2;
                ELSE
                    cost := p_running + n + 1;
                    FOR key IN SELECT k FROM jsonb_object_keys(p_value) AS k
                    LOOP
                        cost := cost + 3 + control.slaif_review_string_cost(key);
                        IF cost > p_budget THEN RETURN -1; END IF;
                        cost := control.slaif_review_value_cost(
                            p_value -> key, cost, p_budget
                        );
                        IF cost < 0 THEN RETURN -1; END IF;
                    END LOOP;
                END IF;
            WHEN 'array' THEN
                n := jsonb_array_length(p_value);
                IF n = 0 THEN
                    cost := p_running + 2;
                ELSE
                    cost := p_running + n + 1;
                    FOR item IN
                        SELECT value FROM jsonb_array_elements(p_value) AS e
                    LOOP
                        cost := control.slaif_review_value_cost(
                            item, cost, p_budget
                        );
                        IF cost < 0 THEN RETURN -1; END IF;
                    END LOOP;
                END IF;
            ELSE
                RETURN -1;
            END CASE;
            IF cost > p_budget THEN RETURN -1; END IF;
            RETURN cost;
        END;
        $fn$
"""

_VALUE_DEPTH_SQL = r"""
        CREATE OR REPLACE FUNCTION control.slaif_review_value_depth(
            p_value jsonb, p_remaining integer
        ) RETURNS integer LANGUAGE plpgsql IMMUTABLE
        SET search_path = pg_catalog AS $fn$
        DECLARE
            item jsonb;
            d integer;
            cd integer;
        BEGIN
            IF jsonb_typeof(p_value) IN ('object', 'array') THEN
                IF p_remaining <= 0 THEN RETURN p_remaining + 1; END IF;
                d := 1;
                IF jsonb_typeof(p_value) = 'object' THEN
                    FOR item IN
                        SELECT p_value -> k FROM jsonb_object_keys(p_value) AS k
                    LOOP
                        cd := control.slaif_review_value_depth(item, p_remaining - 1);
                        IF cd >= p_remaining THEN
                            RETURN p_remaining + 1;
                        END IF;
                        IF cd + 1 > d THEN d := cd + 1; END IF;
                    END LOOP;
                ELSE
                    FOR item IN
                        SELECT value FROM jsonb_array_elements(p_value) AS e
                    LOOP
                        cd := control.slaif_review_value_depth(item, p_remaining - 1);
                        IF cd >= p_remaining THEN
                            RETURN p_remaining + 1;
                        END IF;
                        IF cd + 1 > d THEN d := cd + 1; END IF;
                    END LOOP;
                END IF;
                RETURN d;
            END IF;
            RETURN 0;
        END;
        $fn$
"""

_HELPER_FUNCTIONS = (
    "control.slaif_review_string_cost(text)",
    "control.slaif_review_value_cost(jsonb,bigint,bigint)",
    "control.slaif_review_value_depth(jsonb,integer)",
)

_MEDIA_APPEND = "control.slaif_review_media_append(uuid,uuid,jsonb)"
_SNAPSHOT_COMPLETE = "control.slaif_review_snapshot_complete(uuid,jsonb)"

_READ_SURFACE_FUNCTIONS = (
    "control.slaif_review_snapshot_frozen_state(uuid)",
    "control.slaif_review_projection_authorize(text,bytea,uuid)",
    "control.slaif_review_media_authorize(text,bytea,uuid,uuid)",
    "control.slaif_media_preview_read("
    "text,bytea,uuid,uuid,uuid,integer,integer,integer)",
    "control.slaif_browser_preview_binding_register(uuid,text,timestamptz)",
    "control.slaif_media_bound_preview_read(text,uuid)",
)


def _assert_helper_ownership_and_acl() -> None:
    """Ownership/ACL for the bounded helpers: owner slaif_owner only.

    The helpers take no grants: they are consumed exclusively inside
    SECURITY DEFINER functions owned by slaif_owner, which execute with
    owner privilege.  PUBLIC and every product role are revoked.
    """

    for qualified in _HELPER_FUNCTIONS:
        op.execute(f"ALTER FUNCTION {qualified} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {qualified} FROM PUBLIC")
        for role in _REVOKE_ROLES:
            op.execute(f"REVOKE ALL ON FUNCTION {qualified} FROM {role}")


def upgrade() -> None:
    op.execute(_STRING_COST_SQL)
    op.execute(_VALUE_COST_SQL)
    op.execute(_VALUE_DEPTH_SQL)
    _assert_helper_ownership_and_acl()
    op.execute(_ADD_VERSION_FACTS_SQL)
    op.execute(_WORKSPACE_CREATE_V2_SQL)
    op.execute(_HUMAN_EDITOR_RESOLVE_V2_SQL)
    op.execute(_AGENT_WORKSPACE_CREATE_V2_SQL)
    op.execute(_MEDIA_APPEND_SQL)
    _assert_media_append_ownership_and_acl()
    op.execute(_MATERIALIZER_V2_SQL)
    # The v2 body replaces the same 075 function; re-assert the exact
    # 070/075 ownership/ACL (owner slaif_owner, PUBLIC + product roles
    # revoked, EXECUTE to slaif_review_worker only).
    _M075._assert_ownership_and_acl()
    op.execute(_SNAPSHOT_COMPLETE_V2_SQL)
    _assert_snapshot_complete_ownership_and_acl()
    # Patch 5: the frozen-review read surface (one narrow immutable
    # snapshot fetch + the projection/media authorization gates).
    op.execute(_FROZEN_STATE_SQL)
    op.execute(_PROJECTION_AUTHORIZE_SQL)
    op.execute(_MEDIA_AUTHORIZE_SQL)
    op.execute(_MEDIA_PREVIEW_READ_SQL)
    # 083/5 trusted run binding: the binding facts live on the run
    # row (added here), the registrar is Render-consume-only, and
    # the bound read is media-only.  Installed after the consume
    # surface exists and asserted before any grant is verified.
    op.execute(_BINDING_COLUMN_SQL)
    op.execute(_BINDING_INDEX_SQL)
    op.execute(_BINDING_REGISTER_SQL)
    op.execute(_BOUND_PREVIEW_READ_SQL)
    _assert_read_surface_ownership_and_acl()


def _assert_read_surface_ownership_and_acl() -> None:
    """Ownership/ACL for the frozen-review read surface.

    Owner slaif_owner; PUBLIC and every product role revoked; a single
    targeted EXECUTE grant per caller: the preview reader for the
    immutable snapshot fetch, the projection authorization and the
    trusted run-binding registrar, the media role for the frozen
    media authorization, the active preview byte read and the bound
    preview byte read.  All are fail-closed (NULL/empty result).
    """

    for qualified in _READ_SURFACE_FUNCTIONS:
        op.execute(f"ALTER FUNCTION {qualified} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {qualified} FROM PUBLIC")
        for role in _REVOKE_ROLES:
            op.execute(f"REVOKE ALL ON FUNCTION {qualified} FROM {role}")
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_review_snapshot_frozen_state"
        "(uuid) TO slaif_preview_reader"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_review_projection_authorize"
        "(text,bytea,uuid) TO slaif_preview_reader"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_review_media_authorize"
        "(text,bytea,uuid,uuid) TO slaif_media"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_media_preview_read("
        "text,bytea,uuid,uuid,uuid,integer,integer,integer) TO slaif_media"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_browser_preview_binding_register"
        "(uuid,text,timestamptz) TO slaif_preview_reader"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_media_bound_preview_read"
        "(text,uuid) TO slaif_media"
    )


def _assert_media_append_ownership_and_acl() -> None:
    """Ownership/ACL for the media-closure helper: owner slaif_owner only.

    No grants: the helper is consumed exclusively inside the SECURITY
    DEFINER materializer owned by slaif_owner.  PUBLIC and every product
    role are revoked.
    """

    op.execute(f"ALTER FUNCTION {_MEDIA_APPEND} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_MEDIA_APPEND} FROM PUBLIC")
    for role in _REVOKE_ROLES:
        op.execute(f"REVOKE ALL ON FUNCTION {_MEDIA_APPEND} FROM {role}")


def _assert_snapshot_complete_ownership_and_acl() -> None:
    """Ownership/ACL for snapshot completion: the exact 070_001 pattern.

    Owner slaif_owner; PUBLIC and every product role revoked; EXECUTE to
    slaif_review_worker only.
    """

    op.execute(f"ALTER FUNCTION {_SNAPSHOT_COMPLETE} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_SNAPSHOT_COMPLETE} FROM PUBLIC")
    for role in _REVOKE_ROLES:
        op.execute(f"REVOKE ALL ON FUNCTION {_SNAPSHOT_COMPLETE} FROM {role}")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_SNAPSHOT_COMPLETE} TO slaif_review_worker")


def downgrade() -> None:
    # Retained-v2 rollback safety (R9): a v2 snapshot cannot be
    # re-validated or rendered under the restored v1 contract, so the
    # downgrade refuses before any destructive restoration when
    # incompatible retained v2 snapshots exist.  The migration never
    # rewrites or deletes immutable snapshot history; the deployment
    # must resolve those snapshots through a supported path first.
    op.execute(
        """
        DO $guard$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM control.review_snapshot
                WHERE payload->>'state_version' = 'review-snapshot/v2'
            ) THEN
                RAISE EXCEPTION 'SNAPSHOT_DOWNGRADE_RETAINED_V2'
                    USING ERRCODE = 'P0002';
            END IF;
        END;
        $guard$
        """
    )
    # Restore the 070_001 snapshot completion body (075 never touched it):
    # CREATE OR REPLACE keeps the owner/ACL of the function object.
    op.execute(_SNAPSHOT_COMPLETE_070_SQL)
    _assert_snapshot_complete_ownership_and_acl()
    # Restore the 075_001 materializer body: CREATE OR REPLACE keeps
    # the owner/ACL of the function object, and the 075 body references
    # only the 070 canonical family, so it never sees the 076 helpers.
    op.execute(_MATERIALIZER_075)
    _M075._assert_ownership_and_acl()
    for qualified in reversed(_READ_SURFACE_FUNCTIONS):
        op.execute(f"DROP FUNCTION IF EXISTS {qualified}")
    op.execute("DROP INDEX IF EXISTS control.browser_run_preview_binding_digest")
    op.execute(
        "ALTER TABLE control.browser_run "
        "DROP CONSTRAINT IF EXISTS browser_run_preview_binding_shape, "
        "DROP COLUMN IF EXISTS preview_credential_attempt, "
        "DROP COLUMN IF EXISTS preview_credential_nonce_digest, "
        "DROP COLUMN IF EXISTS preview_credential_expires_at, "
        "DROP COLUMN IF EXISTS preview_credential_digest"
    )
    op.execute(f"DROP FUNCTION IF EXISTS {_MEDIA_APPEND}")
    for qualified in reversed(_HELPER_FUNCTIONS):
        op.execute(f"DROP FUNCTION IF EXISTS {qualified}")
    # CREATE OR REPLACE with the verbatim 075-era bodies: the existing
    # owner/ACL of the 076 V2 constructors (themselves inherited from the
    # 024/028/038 installations) is preserved; no DROP FUNCTION.
    op.execute(_WORKSPACE_CREATE_024_SQL)
    op.execute(_HUMAN_EDITOR_RESOLVE_028_SQL)
    op.execute(_AGENT_WORKSPACE_CREATE_038_SQL)
    op.execute(_DROP_VERSION_FACTS_SQL)


# ---------------------------------------------------------------------------
# Version facts (patch 2): trusted product version pins recorded at
# workspace creation.  The six literals are the single source of truth for
# the supported version surfaces; unit tests pin SQL == Python constants
# (review_worker/config.py, content_model/design_system.py).
#
# The three _WORKSPACE_CREATE_*/_HUMAN_EDITOR_RESOLVE_*/_AGENT_WORKSPACE_
# CREATE_038_SQL constants are the verbatim 075-era constructor DDL as it
# appears in migrations 024/028/038 (original indentation preserved; the
# two plain CREATE FUNCTION headers adjusted to CREATE OR REPLACE FUNCTION,
# header keyword only) so the downgrade restores a byte-identical prosrc
# while preserving the existing owner/ACL.  The *_V2_SQL constants are the
# same verbatim bodies with exactly one INSERT change each (the trusted
# version_facts literal).  No DROP FUNCTION is used in the downgrade.
# ---------------------------------------------------------------------------

_VERSION_FACTS_SQL = '\'{"catalog":"catalog-v1","composition_schema":"site-composition/v1","content_model":"content-model/v1","design_system":"design-system/v1","puck":"0.20.2","renderer":"renderer-v1"}\'::jsonb'

_ADD_VERSION_FACTS_SQL = (
    "ALTER TABLE control.workspace ADD COLUMN version_facts jsonb NOT NULL "
    "DEFAULT '{}'::jsonb"
)

_DROP_VERSION_FACTS_SQL = "ALTER TABLE control.workspace DROP COLUMN version_facts"

_WORKSPACE_CREATE_024_SQL = r"""
        CREATE OR REPLACE FUNCTION control.slaif_workspace_create(
            p_site_id uuid, p_created_by uuid, p_title text,
            p_description text, p_preset text, p_scopes jsonb,
            p_duration_hours integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, created_by uuid, title text,
            status text, delegation_preset text,
            effective_scopes jsonb, created_at timestamptz, expires_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            INSERT INTO control.workspace
                (site_id, created_by, title, task_description, delegation_preset,
                 effective_scopes, status, expires_at)
            VALUES (p_site_id, p_created_by, p_title, p_description, p_preset,
                    p_scopes, 'ACTIVE', now() + make_interval(hours => p_duration_hours));
            RETURN QUERY SELECT w.id, w.site_id, w.created_by, w.title,
                w.status, w.delegation_preset, w.effective_scopes,
                w.created_at, w.expires_at
            FROM control.workspace w
            WHERE w.site_id = p_site_id AND w.created_by = p_created_by
              AND w.title = p_title
            ORDER BY w.created_at DESC LIMIT 1;
        END;
        $fn$
"""

_HUMAN_EDITOR_RESOLVE_028_SQL = r"""
        CREATE OR REPLACE FUNCTION control.slaif_human_editor_workspace_resolve(
            p_site_id uuid, p_human_user_id uuid
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            resolved_workspace uuid;
        BEGIN
            PERFORM pg_advisory_xact_lock(
                hashtextextended(
                    p_site_id::text || ':' || p_human_user_id::text, 281
                )
            );
            SELECT workspace.id
            INTO resolved_workspace
            FROM control.workspace AS workspace
            JOIN control.site AS site ON site.id = workspace.site_id
            JOIN control.user_account AS account
              ON account.id = workspace.created_by
            WHERE workspace.site_id = p_site_id
              AND workspace.created_by = p_human_user_id
              AND workspace.actor_type = 'HUMAN'
              AND workspace.status = 'ACTIVE'
              AND workspace.expires_at > CURRENT_TIMESTAMP
              AND site.status = 'ACTIVE'
              AND account.status = 'ACTIVE'
            ORDER BY workspace.created_at DESC, workspace.id DESC
            LIMIT 1
            FOR UPDATE OF workspace;

            IF resolved_workspace IS NULL THEN
                INSERT INTO control.workspace (
                    site_id, created_by, actor_type, title, task_description,
                    delegation_preset, effective_scopes, status, expires_at
                ) VALUES (
                    p_site_id, p_human_user_id, 'HUMAN',
                    'Human page editor',
                    'Server-owned workspace for the human page editor.',
                    'L2_SITE_EDITOR',
                    '[]'::jsonb,
                    'ACTIVE',
                    CURRENT_TIMESTAMP + interval '8 hours'
                ) RETURNING id INTO resolved_workspace;
            END IF;
            RETURN resolved_workspace;
        END;
        $fn$
"""

_AGENT_WORKSPACE_CREATE_038_SQL = r"""
        CREATE OR REPLACE FUNCTION control.slaif_human_agent_workspace_create(
            p_site_id uuid, p_user_id uuid, p_title text, p_description text,
            p_preset text, p_requested_scopes text[], p_constraints jsonb,
            p_origins text[], p_request_quota integer, p_mutation_quota integer,
            p_delete_quota integer, p_upload_quota integer, p_browser_quota integer,
            p_duration_hours integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, created_by uuid, delegator_id uuid,
            title text, task_description text, status text,
            delegation_preset text, effective_scopes jsonb,
            resource_constraints jsonb, source_origins text[],
            request_quota integer, mutation_quota integer, delete_quota integer,
            upload_quota integer, browser_quota integer,
            base_site_revision bigint, created_at timestamptz, expires_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
            authority record;
            level smallint;
            effective text[];
            workspace_id uuid;
        BEGIN
            PERFORM set_config('app.human_user_id', p_user_id::text, true);
            IF p_duration_hours NOT BETWEEN 1 AND 8
               OR p_request_quota NOT BETWEEN 1 AND 10000
               OR p_mutation_quota NOT BETWEEN 0 AND 5000
               OR p_delete_quota NOT BETWEEN 0 AND 5000
               OR p_upload_quota NOT BETWEEN 0 AND 1000
               OR p_browser_quota NOT BETWEEN 0 AND 1000
               OR jsonb_typeof(p_constraints) <> 'object'
               OR octet_length(p_constraints::text) > 8192
               OR cardinality(p_origins) > 16
               OR EXISTS (SELECT 1 FROM unnest(p_origins) origin WHERE length(origin) > 2048)
            THEN RAISE EXCEPTION 'AGENT_WORKSPACE_INPUT_INVALID' USING ERRCODE = 'P0001'; END IF;
            level := CASE p_preset
                WHEN 'L1_CONTENT_EDITOR' THEN 1 WHEN 'L2_SITE_EDITOR' THEN 2
                WHEN 'L3_SITE_DESIGNER' THEN 3 WHEN 'L4_SITE_ARCHITECT' THEN 4
                ELSE 0 END;
            IF level = 0 THEN RAISE EXCEPTION 'AGENT_WORKSPACE_INPUT_INVALID' USING ERRCODE = 'P0001'; END IF;
            SELECT * INTO authority FROM control.slaif_effective_human_membership(p_user_id, p_site_id);
            IF (authority IS NULL AND NOT EXISTS (SELECT 1 FROM control.platform_administrator WHERE user_account_id=p_user_id))
               OR (authority IS NOT NULL AND (authority.effective_ceiling < level
               OR NOT ('workspace:create' = ANY(authority.effective_permissions))))
            THEN RAISE EXCEPTION 'AGENT_WORKSPACE_DENIED' USING ERRCODE = 'P0002'; END IF;
            SELECT COALESCE(array_agg(scope ORDER BY scope), ARRAY[]::text[]) INTO effective
            FROM unnest(COALESCE(p_requested_scopes, ARRAY[]::text[])) scope
            JOIN control.permission permission ON permission.permission_key = scope
            WHERE scope = ANY(COALESCE(authority.effective_permissions, ARRAY(SELECT permission_key FROM control.permission WHERE site_assignable)))
              AND permission.site_assignable
              AND permission.agent_delegation_level IS NOT NULL
              AND permission.agent_delegation_level <= level;
            IF cardinality(effective) <> cardinality(COALESCE(p_requested_scopes, ARRAY[]::text[]))
            THEN RAISE EXCEPTION 'AGENT_WORKSPACE_SCOPE_DENIED' USING ERRCODE = 'P0002'; END IF;
            INSERT INTO control.workspace(
                site_id, created_by, delegator_id, actor_type, title, task_description,
                delegation_preset, effective_scopes, resource_constraints, source_origins,
                request_quota, mutation_quota, delete_quota, upload_quota, browser_quota,
                status, base_site_revision, expires_at
            ) SELECT p_site_id, p_user_id, p_user_id, 'AGENT', p_title, p_description,
                p_preset, to_jsonb(effective), p_constraints, COALESCE(p_origins, ARRAY[]::text[]),
                p_request_quota, p_mutation_quota, p_delete_quota, p_upload_quota, p_browser_quota,
                'ACTIVE', site.canonical_revision, CURRENT_TIMESTAMP + make_interval(hours => p_duration_hours)
            FROM control.site site WHERE site.id = p_site_id AND site.status = 'ACTIVE'
            RETURNING workspace.id INTO workspace_id;
            IF workspace_id IS NULL THEN RAISE EXCEPTION 'AGENT_WORKSPACE_NOT_FOUND' USING ERRCODE = 'P0002'; END IF;
            RETURN QUERY SELECT w.id,w.site_id,w.created_by,w.delegator_id,w.title,w.task_description,
                w.status,w.delegation_preset,w.effective_scopes,w.resource_constraints,w.source_origins,
                w.request_quota,w.mutation_quota,w.delete_quota,w.upload_quota,w.browser_quota,
                w.base_site_revision,w.created_at,w.expires_at FROM control.workspace w WHERE w.id = workspace_id;
        END; $fn$
"""

_WORKSPACE_CREATE_V2_SQL = r"""
        CREATE OR REPLACE FUNCTION control.slaif_workspace_create(
            p_site_id uuid, p_created_by uuid, p_title text,
            p_description text, p_preset text, p_scopes jsonb,
            p_duration_hours integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, created_by uuid, title text,
            status text, delegation_preset text,
            effective_scopes jsonb, created_at timestamptz, expires_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            INSERT INTO control.workspace
                (site_id, created_by, title, task_description, delegation_preset,
                 effective_scopes, version_facts, status, expires_at)
            VALUES (p_site_id, p_created_by, p_title, p_description, p_preset,
                    p_scopes, '{"catalog":"catalog-v1","composition_schema":"site-composition/v1","content_model":"content-model/v1","design_system":"design-system/v1","puck":"0.20.2","renderer":"renderer-v1"}'::jsonb, 'ACTIVE', now() + make_interval(hours => p_duration_hours));
            RETURN QUERY SELECT w.id, w.site_id, w.created_by, w.title,
                w.status, w.delegation_preset, w.effective_scopes,
                w.created_at, w.expires_at
            FROM control.workspace w
            WHERE w.site_id = p_site_id AND w.created_by = p_created_by
              AND w.title = p_title
            ORDER BY w.created_at DESC LIMIT 1;
        END;
        $fn$
"""

_HUMAN_EDITOR_RESOLVE_V2_SQL = r"""
        CREATE OR REPLACE FUNCTION control.slaif_human_editor_workspace_resolve(
            p_site_id uuid, p_human_user_id uuid
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            resolved_workspace uuid;
        BEGIN
            PERFORM pg_advisory_xact_lock(
                hashtextextended(
                    p_site_id::text || ':' || p_human_user_id::text, 281
                )
            );
            SELECT workspace.id
            INTO resolved_workspace
            FROM control.workspace AS workspace
            JOIN control.site AS site ON site.id = workspace.site_id
            JOIN control.user_account AS account
              ON account.id = workspace.created_by
            WHERE workspace.site_id = p_site_id
              AND workspace.created_by = p_human_user_id
              AND workspace.actor_type = 'HUMAN'
              AND workspace.status = 'ACTIVE'
              AND workspace.expires_at > CURRENT_TIMESTAMP
              AND site.status = 'ACTIVE'
              AND account.status = 'ACTIVE'
            ORDER BY workspace.created_at DESC, workspace.id DESC
            LIMIT 1
            FOR UPDATE OF workspace;

            IF resolved_workspace IS NULL THEN
                INSERT INTO control.workspace (
                    site_id, created_by, actor_type, title, task_description,
                    delegation_preset, effective_scopes, version_facts, status, expires_at
                ) VALUES (
                    p_site_id, p_human_user_id, 'HUMAN',
                    'Human page editor',
                    'Server-owned workspace for the human page editor.',
                    'L2_SITE_EDITOR',
                    '[]'::jsonb,
                    '{"catalog":"catalog-v1","composition_schema":"site-composition/v1","content_model":"content-model/v1","design_system":"design-system/v1","puck":"0.20.2","renderer":"renderer-v1"}'::jsonb,
                    'ACTIVE',
                    CURRENT_TIMESTAMP + interval '8 hours'
                ) RETURNING id INTO resolved_workspace;
            END IF;
            RETURN resolved_workspace;
        END;
        $fn$
"""

_AGENT_WORKSPACE_CREATE_V2_SQL = r"""
        CREATE OR REPLACE FUNCTION control.slaif_human_agent_workspace_create(
            p_site_id uuid, p_user_id uuid, p_title text, p_description text,
            p_preset text, p_requested_scopes text[], p_constraints jsonb,
            p_origins text[], p_request_quota integer, p_mutation_quota integer,
            p_delete_quota integer, p_upload_quota integer, p_browser_quota integer,
            p_duration_hours integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, created_by uuid, delegator_id uuid,
            title text, task_description text, status text,
            delegation_preset text, effective_scopes jsonb,
            resource_constraints jsonb, source_origins text[],
            request_quota integer, mutation_quota integer, delete_quota integer,
            upload_quota integer, browser_quota integer,
            base_site_revision bigint, created_at timestamptz, expires_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
            authority record;
            level smallint;
            effective text[];
            workspace_id uuid;
        BEGIN
            PERFORM set_config('app.human_user_id', p_user_id::text, true);
            IF p_duration_hours NOT BETWEEN 1 AND 8
               OR p_request_quota NOT BETWEEN 1 AND 10000
               OR p_mutation_quota NOT BETWEEN 0 AND 5000
               OR p_delete_quota NOT BETWEEN 0 AND 5000
               OR p_upload_quota NOT BETWEEN 0 AND 1000
               OR p_browser_quota NOT BETWEEN 0 AND 1000
               OR jsonb_typeof(p_constraints) <> 'object'
               OR octet_length(p_constraints::text) > 8192
               OR cardinality(p_origins) > 16
               OR EXISTS (SELECT 1 FROM unnest(p_origins) origin WHERE length(origin) > 2048)
            THEN RAISE EXCEPTION 'AGENT_WORKSPACE_INPUT_INVALID' USING ERRCODE = 'P0001'; END IF;
            level := CASE p_preset
                WHEN 'L1_CONTENT_EDITOR' THEN 1 WHEN 'L2_SITE_EDITOR' THEN 2
                WHEN 'L3_SITE_DESIGNER' THEN 3 WHEN 'L4_SITE_ARCHITECT' THEN 4
                ELSE 0 END;
            IF level = 0 THEN RAISE EXCEPTION 'AGENT_WORKSPACE_INPUT_INVALID' USING ERRCODE = 'P0001'; END IF;
            SELECT * INTO authority FROM control.slaif_effective_human_membership(p_user_id, p_site_id);
            IF (authority IS NULL AND NOT EXISTS (SELECT 1 FROM control.platform_administrator WHERE user_account_id=p_user_id))
               OR (authority IS NOT NULL AND (authority.effective_ceiling < level
               OR NOT ('workspace:create' = ANY(authority.effective_permissions))))
            THEN RAISE EXCEPTION 'AGENT_WORKSPACE_DENIED' USING ERRCODE = 'P0002'; END IF;
            SELECT COALESCE(array_agg(scope ORDER BY scope), ARRAY[]::text[]) INTO effective
            FROM unnest(COALESCE(p_requested_scopes, ARRAY[]::text[])) scope
            JOIN control.permission permission ON permission.permission_key = scope
            WHERE scope = ANY(COALESCE(authority.effective_permissions, ARRAY(SELECT permission_key FROM control.permission WHERE site_assignable)))
              AND permission.site_assignable
              AND permission.agent_delegation_level IS NOT NULL
              AND permission.agent_delegation_level <= level;
            IF cardinality(effective) <> cardinality(COALESCE(p_requested_scopes, ARRAY[]::text[]))
            THEN RAISE EXCEPTION 'AGENT_WORKSPACE_SCOPE_DENIED' USING ERRCODE = 'P0002'; END IF;
            INSERT INTO control.workspace(
                site_id, created_by, delegator_id, actor_type, title, task_description,
                delegation_preset, effective_scopes, version_facts, resource_constraints, source_origins,
                request_quota, mutation_quota, delete_quota, upload_quota, browser_quota,
                status, base_site_revision, expires_at
            ) SELECT p_site_id, p_user_id, p_user_id, 'AGENT', p_title, p_description,
                p_preset, to_jsonb(effective), '{"catalog":"catalog-v1","composition_schema":"site-composition/v1","content_model":"content-model/v1","design_system":"design-system/v1","puck":"0.20.2","renderer":"renderer-v1"}'::jsonb, p_constraints, COALESCE(p_origins, ARRAY[]::text[]),
                p_request_quota, p_mutation_quota, p_delete_quota, p_upload_quota, p_browser_quota,
                'ACTIVE', site.canonical_revision, CURRENT_TIMESTAMP + make_interval(hours => p_duration_hours)
            FROM control.site site WHERE site.id = p_site_id AND site.status = 'ACTIVE'
            RETURNING workspace.id INTO workspace_id;
            IF workspace_id IS NULL THEN RAISE EXCEPTION 'AGENT_WORKSPACE_NOT_FOUND' USING ERRCODE = 'P0002'; END IF;
            RETURN QUERY SELECT w.id,w.site_id,w.created_by,w.delegator_id,w.title,w.task_description,
                w.status,w.delegation_preset,w.effective_scopes,w.resource_constraints,w.source_origins,
                w.request_quota,w.mutation_quota,w.delete_quota,w.upload_quota,w.browser_quota,
                w.base_site_revision,w.created_at,w.expires_at FROM control.workspace w WHERE w.id = workspace_id;
        END; $fn$
"""

# ---------------------------------------------------------------------------
# Patch 3: v2 materializer and media-closure helper (verbatim sources).
#
# _MATERIALIZER_V2_SQL is the reviewed revision-4 v2 materializer (sha256
# 1d08724dd3e93851b92dcf63ca8058d9c915955267b59d8710bab2dcc06c4ac7,
# 1259 lines); _MEDIA_APPEND_SQL is the owner-only media-closure helper
# (sha256 1a5d1f95dacc3dcf5e9db9af63522b92bdb19057a3ca3ad395473dbeba1b7574,
# 33 lines).  Both are single CREATE OR REPLACE FUNCTION statements
# executed verbatim by the migration runner as slaif_owner.
# ---------------------------------------------------------------------------

_MATERIALIZER_V2_SQL = r"""
-- =====================================================================
-- 083-5-a v2 materializer (revision 3 of the candidate).
--
-- Supersedes:
--   part 1       afb367e0e6f832edd260f9351f50a8515f091ea72254c1a4aba317fd33fe8fd7
--   full first   476609d69a1c40b9aa49d108fa92f93d6026a3236a3dbb128376acf80ba9a4ff
-- (both preserved under their reviewed names).
--
-- Revision-3 corrections (strategy complete-source review, 2026-10-18):
--   (1) No plpgsql map(...) declarations: PostgreSQL has no such type.
--       Aggregate-level bounds (per-page node count/cost pre-bounds,
--       per-(navigation, locale) item caps, duplicate-key checks) are
--       enforced by pure-SQL GROUP BY/HAVING/EXISTS preflights before
--       any row loop; reference deduplication uses the jsonb selected
--       map itself through control.slaif_review_media_append.
--   (2) Actual schema/PL/pgSQL bindings: content_type has id, not
--       type_id (duplicate check groups by key); every FOR record is
--       accessed through its own loop variable (r.*), never through the
--       inner table alias; value records are real records with non
--       reserved aliases.
--   (3) The persisted control.component_catalog.definitions value is
--       the component ARRAY (060); it is walked with
--       jsonb_array_elements directly, and the binding_kind =
--       'media_asset' gate plus declared reference/format=uuid
--       discovery are preserved (collection_view viewId references are
--       NOT media refs).
--   (4) Scalar jsonb uuid extraction uses #>> '{}' (text extraction
--       semantics); jsonb::text would retain string quotes.
--   (5) First-reference resolution is NULL-safe: membership is the
--       jsonb ? key test inside the append helper, so the first real
--       reference resolves, joins the closure and is digest-covered;
--       repeated references deduplicate.
--   (6) Navigation inventory is the complete raw site-visible
--       navigation_item row set (all locales, all 14 columns incl.
--       row_version/timestamps/parent_key), captured once under bounds;
--       the derived render locale/resolved views are not raw inventory
--       (the 059 render helper returns site items without a locale
--       WHERE filter and would duplicate them per locale).
--
-- Retained from earlier revisions: the 075 lock frame, the version-facts
-- gate, bound-before-aggregate ordering, direct (unmasked)
-- effective_route for renderable rows with explicit NULL for
-- non-renderable retained rows, and raw-value depth <= 8 enforced per
-- raw captured jsonb value (no global document depth limit).
--
-- Stable failures (all P0002):
--   REVIEW_WORKSPACE_NOT_FOUND / REVIEW_SITE_NOT_ACTIVE   (075 lock frame)
--   REVIEW_WORKSPACE_VERSION_UNKNOWN   (pre-076 empty version facts)
--   SNAPSHOT_VALIDATION_FAILED         (version mismatch, stale catalog
--                                       entry, malformed declared
--                                       reference values, structural
--                                       duplicates)
--   REVIEW_SNAPSHOT_OVER_BUDGET        (any finite bound breach: row cap,
--                                       byte share, raw nesting, total)
--   REVIEW_MEDIA_REF_UNRESOLVED        (typed ref without media_asset row)
-- =====================================================================
CREATE OR REPLACE FUNCTION control.slaif_review_workspace_state(p_workspace_id uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog AS $fn$
DECLARE
    -- lock frame (075 verbatim semantics)
    ws control.workspace%ROWTYPE;
    site_row record;
    site_revision bigint;
    site_status text;
    -- generic row assembly
    r record;
    rowj jsonb;
    n bigint;
    running bigint;
    -- family arrays
    page_docs jsonb := '[]'::jsonb;
    composition_docs jsonb := '[]'::jsonb;
    type_docs jsonb := '[]'::jsonb;
    field_docs jsonb := '[]'::jsonb;
    view_docs jsonb := '[]'::jsonb;
    item_docs jsonb := '[]'::jsonb;
    translation_docs jsonb := '[]'::jsonb;
    relation_docs jsonb := '[]'::jsonb;
    locale_docs jsonb := '[]'::jsonb;
    region_docs jsonb := '[]'::jsonb;
    nav_def_docs jsonb := '[]'::jsonb;
    nav_item_docs jsonb := '[]'::jsonb;
    redirect_docs jsonb := '[]'::jsonb;
    media_inventory_docs jsonb := '[]'::jsonb;
    proposal_docs jsonb := '[]'::jsonb;
    media_docs jsonb := '{}'::jsonb;
    theme_json jsonb;
    -- page loop
    style_row record;
    style_json jsonb;
    nodes_row jsonb;
    page_route text;
    -- catalog-driven media closure (R6)
    catalog_defs jsonb;
    comp_meta jsonb := '{}'::jsonb;
    comp_entry jsonb;
    meta_obj jsonb;
    meta jsonb;
    prop_key text;
    item_key text;
    prop jsonb;
    item_schema jsonb;
    top_ref text;
    top_req boolean;
    arr_ref_key text;
    arr_ref_name text;
    c_row record;
    ref_value jsonb;
    arr jsonb;
    arr_item jsonb;
    media_id uuid;
    f_row record;
    val record;
    doc jsonb;
BEGIN
    -- -----------------------------------------------------------------
    -- 075 lock order, verbatim: workspace row first, pre-lock ACTIVE
    -- fast fail, established workspace advisory lock (key 280), then the
    -- canonical site row in the acceptance order with the fail-closed
    -- post-wait re-check.  The row lock is xact-level: the caller holds
    -- it through snapshot completion or the preflight re-validation.
    -- -----------------------------------------------------------------
    SELECT * INTO ws FROM control.workspace
    WHERE id = p_workspace_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'REVIEW_WORKSPACE_NOT_FOUND' USING ERRCODE = 'P0002';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM control.site AS site
        WHERE site.id = ws.site_id AND site.status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION 'REVIEW_SITE_NOT_ACTIVE' USING ERRCODE = 'P0002';
    END IF;
    PERFORM pg_advisory_xact_lock(
        hashtextextended(p_workspace_id::text, 280)
    );
    SELECT canonical_revision, status
      INTO site_revision, site_status
      FROM control.site WHERE id = ws.site_id FOR UPDATE;
    IF site_status IS DISTINCT FROM 'ACTIVE' THEN
        RAISE EXCEPTION 'REVIEW_SITE_NOT_ACTIVE' USING ERRCODE = 'P0002';
    END IF;
    PERFORM set_config('app.session_id', p_workspace_id::text, true);
    SELECT site_key, display_name, status, default_locale,
           component_catalog_version, content_model_revision,
           created_at, updated_at
      INTO site_row
      FROM control.site WHERE id = ws.site_id;

    -- 083/5 version-facts gate: workspaces created before the pin
    -- capture (empty facts) cannot be frozen; any other mismatch is a
    -- validation failure.  Both fail closed before any content read.
    IF ws.version_facts IS NULL OR ws.version_facts = '{}'::jsonb THEN
        RAISE EXCEPTION 'REVIEW_WORKSPACE_VERSION_UNKNOWN'
            USING ERRCODE = 'P0002';
    END IF;
    IF ws.version_facts IS DISTINCT FROM
        '{"catalog":"catalog-v1","composition_schema":"site-composition/v1","content_model":"content-model/v1","design_system":"design-system/v1","puck":"0.20.2","renderer":"renderer-v1"}'::jsonb
    THEN
        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED' USING ERRCODE = 'P0002';
    END IF;

    -- -----------------------------------------------------------------
    -- Persisted catalog (060): definitions is the component ARRAY.
    -- Build a small metadata object per component: schema_version for
    -- the stale-entry check, and for binding_kind = 'media_asset'
    -- components the DECLARED reference-format-uuid prop positions
    -- (top-level and declared array-item schemas).  collection_view
    -- viewId references are not media refs and stay out of the closure.
    -- -----------------------------------------------------------------
    SELECT definitions INTO catalog_defs FROM control.component_catalog;
    IF catalog_defs IS NULL OR jsonb_typeof(catalog_defs) <> 'array' THEN
        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
            USING ERRCODE = 'P0002',
            DETAIL = 'component catalog missing or malformed';
    END IF;
    FOR comp_entry IN
        SELECT value FROM jsonb_array_elements(catalog_defs) AS e
    LOOP
        top_ref := NULL;
        top_req := false;
        arr_ref_key := NULL;
        arr_ref_name := NULL;
        IF comp_entry ->> 'binding_kind' = 'media_asset' THEN
            FOR prop_key IN
                SELECT k FROM jsonb_object_keys(comp_entry -> 'props') AS k
            LOOP
                prop := comp_entry -> 'props' -> prop_key;
                IF prop ->> 'type' = 'reference'
                   AND prop ->> 'format' = 'uuid'
                THEN
                    top_ref := prop_key;
                    top_req := (prop ->> 'required') = 'true';
                ELSIF prop ->> 'type' = 'array' THEN
                    item_schema := prop -> 'schema' -> 'items';
                    IF jsonb_typeof(item_schema) = 'object' THEN
                        FOR item_key IN
                            SELECT k FROM jsonb_object_keys(
                                item_schema -> 'properties'
                            ) AS k
                        LOOP
                            IF item_schema -> 'properties' -> item_key ->> 'type'
                                     = 'reference'
                               AND item_schema -> 'properties' -> item_key ->> 'format'
                                     = 'uuid'
                            THEN
                                arr_ref_key := prop_key;
                                arr_ref_name := item_key;
                            END IF;
                        END LOOP;
                    END IF;
                END IF;
            END LOOP;
        END IF;
        meta_obj := jsonb_build_object(
            'schema', comp_entry ->> 'schema_version'
        );
        IF top_ref IS NOT NULL THEN
            meta_obj := meta_obj || jsonb_build_object(
                'top', top_ref, 'req', top_req
            );
        END IF;
        IF arr_ref_key IS NOT NULL THEN
            meta_obj := meta_obj || jsonb_build_object(
                'arr', arr_ref_key, 'ref', arr_ref_name
            );
        END IF;
        comp_meta := comp_meta || jsonb_build_object(
            comp_entry ->> 'type', meta_obj
        );
    END LOOP;

    -- -----------------------------------------------------------------
    -- R8 bound preflights (pure SQL, before any row loop or aggregate
    -- allocation): total row caps, per-group caps, raw-value depth
    -- (<= 8 per raw captured jsonb value) and the per-page nodes
    -- count/cost pre-bounds.
    -- -----------------------------------------------------------------
    -- composition: 131072 total; 128 per page (write-side
    -- MAX_COMPONENTS_PER_PAGE); per-page canonical node cost pre-bounded
    -- by the pages family share before any page nodes aggregation.
    SELECT count(*) INTO n FROM content.page_composition AS c
    WHERE c.site_id = ws.site_id;
    IF n > 131072 THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'composition row cap';
    END IF;
    -- Raw-value depth refusal precedes ANY recursive cost traversal:
    -- a depth-9 raw value must hit the stable budget refusal before
    -- value_cost recurses into it (depth before cost, cost before
    -- aggregate allocation).
    IF EXISTS (
        SELECT 1 FROM content.page_composition AS c
        WHERE c.site_id = ws.site_id
          AND c.props IS NOT NULL
          AND control.slaif_review_value_depth(c.props, 8) > 8
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'composition props raw depth';
    END IF;
    IF EXISTS (
        SELECT 1 FROM (
            SELECT c.page_id
            FROM content.page_composition AS c
            WHERE c.site_id = ws.site_id
            GROUP BY c.page_id
            HAVING count(*) > 128
               OR sum(coalesce(NULLIF(
                      control.slaif_review_value_cost(
                          to_jsonb(c), 0, 1048576
                      ), -1), 1048576)) > 262144
        ) AS over
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'per-page node count or byte pre-bound';
    END IF;
    -- pages: 4096 rows; style_overrides raw depth.
    SELECT count(*) INTO n FROM content.page AS p
    WHERE p.site_id = ws.site_id;
    IF n > 4096 THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'page row cap';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.page AS p
        WHERE p.site_id = ws.site_id
          AND p.style_overrides IS NOT NULL
          AND control.slaif_review_value_depth(p.style_overrides, 8) > 8
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'page style_overrides raw depth';
    END IF;
    -- content model: duplicate type keys are structural; caps: 64 types,
    -- 64 fields/type, 64 views/type, 2000 items/type, 20000 translations
    -- total, 1000 relations per (item, field).
    IF EXISTS (
        SELECT 1 FROM (
            SELECT t.key FROM content.content_type AS t
            WHERE t.site_id = ws.site_id
            GROUP BY t.key HAVING count(*) > 1
        ) AS over
    ) THEN
        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
            USING ERRCODE = 'P0002',
            DETAIL = 'duplicate content type key';
    END IF;
    SELECT count(*) INTO n FROM content.content_type AS t
    WHERE t.site_id = ws.site_id;
    IF n > 64 THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'content type cap';
    END IF;
    IF EXISTS (
        SELECT 1 FROM (
            SELECT f.type_id FROM content.field_definition AS f
            WHERE f.site_id = ws.site_id
            GROUP BY f.type_id HAVING count(*) > 64
        ) AS over
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'fields per type cap';
    END IF;
    IF EXISTS (
        SELECT 1 FROM (
            SELECT v.type_id FROM content.collection_view AS v
            WHERE v.site_id = ws.site_id
            GROUP BY v.type_id HAVING count(*) > 64
        ) AS over
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'views per type cap';
    END IF;
    IF EXISTS (
        SELECT 1 FROM (
            SELECT i.type_id FROM content.content_item AS i
            WHERE i.site_id = ws.site_id
            GROUP BY i.type_id HAVING count(*) > 2000
        ) AS over
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'items per type cap';
    END IF;
    SELECT count(*) INTO n FROM content.content_item_translation AS t
    WHERE t.site_id = ws.site_id;
    IF n > 20000 THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'translation row cap';
    END IF;
    IF EXISTS (
        SELECT 1 FROM (
            SELECT rel.source_item_id, rel.field_definition_id
            FROM content.item_relation AS rel
            WHERE rel.site_id = ws.site_id
            GROUP BY rel.source_item_id, rel.field_definition_id
            HAVING count(*) > 1000
        ) AS over
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'relations per (item, field) cap';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.content_type AS t
        WHERE t.site_id = ws.site_id
          AND ((t.labels IS NOT NULL
                AND control.slaif_review_value_depth(t.labels, 8) > 8)
            OR (t.settings IS NOT NULL
                AND control.slaif_review_value_depth(t.settings, 8) > 8))
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'content type labels/settings raw depth';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.field_definition AS f
        WHERE f.site_id = ws.site_id
          AND ((f.validation IS NOT NULL
                AND control.slaif_review_value_depth(f.validation, 8) > 8)
            OR (f.ui_options IS NOT NULL
                AND control.slaif_review_value_depth(f.ui_options, 8) > 8))
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'field validation/ui_options raw depth';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.collection_view AS v
        WHERE v.site_id = ws.site_id
          AND ((v.filter_spec IS NOT NULL
                AND control.slaif_review_value_depth(v.filter_spec, 8) > 8)
            OR (v.sort_spec IS NOT NULL
                AND control.slaif_review_value_depth(v.sort_spec, 8) > 8)
            OR (v.projection_spec IS NOT NULL
                AND control.slaif_review_value_depth(v.projection_spec, 8) > 8)
            OR (v.pagination_spec IS NOT NULL
                AND control.slaif_review_value_depth(v.pagination_spec, 8) > 8))
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'view spec raw depth';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.content_item AS i
        WHERE i.site_id = ws.site_id
          AND i.values IS NOT NULL
          AND control.slaif_review_value_depth(i.values, 8) > 8
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'item values raw depth';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.content_item_translation AS t
        WHERE t.site_id = ws.site_id
          AND t.localized_values IS NOT NULL
          AND control.slaif_review_value_depth(t.localized_values, 8) > 8
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'translation localized_values raw depth';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.item_relation AS rel
        WHERE rel.site_id = ws.site_id
          AND rel.metadata IS NOT NULL
          AND control.slaif_review_value_depth(rel.metadata, 8) > 8
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'relation metadata raw depth';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.site_locale AS l
        WHERE l.site_id = ws.site_id
          AND l.metadata IS NOT NULL
          AND control.slaif_review_value_depth(l.metadata, 8) > 8
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'locale metadata raw depth';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.slaif_region_list(ws.site_id) AS g2
        WHERE g2.content IS NOT NULL
          AND control.slaif_review_value_depth(g2.content, 8) > 8
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'region content raw depth';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.navigation AS d
        WHERE d.site_id = ws.site_id
          AND ((d.settings IS NOT NULL
                AND control.slaif_review_value_depth(d.settings, 8) > 8)
            OR (d.labels IS NOT NULL
                AND control.slaif_review_value_depth(d.labels, 8) > 8))
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'navigation settings/labels raw depth';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.navigation_item AS ni
        WHERE ni.site_id = ws.site_id
          AND ni.labels IS NOT NULL
          AND control.slaif_review_value_depth(ni.labels, 8) > 8
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'nav item labels raw depth';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.media_asset AS m
        WHERE m.site_id = ws.site_id
          AND m.metadata IS NOT NULL
          AND control.slaif_review_value_depth(m.metadata, 8) > 8
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'media metadata raw depth';
    END IF;
    IF EXISTS (
        SELECT 1 FROM content.proposed_side_effect AS pe
        WHERE pe.site_id = ws.site_id
          AND pe.workspace_id = p_workspace_id
          AND pe.payload IS NOT NULL
          AND control.slaif_review_value_depth(pe.payload, 8) > 8
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'proposal payload raw depth';
    END IF;

    -- Site-family row caps (declared budget limits, fail closed):
    -- locales 32, regions 8, navigation definitions 16, navigation
    -- items 4096 total / 256 per (navigation, locale), redirects 256,
    -- media inventory 4096, proposals 10000.
    SELECT count(*) INTO n FROM content.site_locale AS l
    WHERE l.site_id = ws.site_id;
    IF n > 32 THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'locale cap';
    END IF;
    SELECT count(*) INTO n FROM content.slaif_region_list(ws.site_id) AS g2;
    IF n > 8 THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'region cap';
    END IF;
    SELECT count(*) INTO n FROM content.navigation AS d
    WHERE d.site_id = ws.site_id;
    IF n > 16 THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'navigation cap';
    END IF;
    SELECT count(*) INTO n FROM content.navigation_item AS ni
    WHERE ni.site_id = ws.site_id;
    IF n > 4096 THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'navigation item total cap';
    END IF;
    IF EXISTS (
        SELECT 1 FROM (
            SELECT ni.navigation_id, ni.locale
            FROM content.navigation_item AS ni
            WHERE ni.site_id = ws.site_id
            GROUP BY ni.navigation_id, ni.locale
            HAVING count(*) > 256
        ) AS over
    ) THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'nav items per (navigation, locale) cap';
    END IF;
    SELECT count(*) INTO n FROM content.redirect AS rd
    WHERE rd.site_id = ws.site_id;
    IF n > 256 THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'redirect cap';
    END IF;
    SELECT count(*) INTO n FROM content.media_asset AS m
    WHERE m.site_id = ws.site_id;
    IF n > 4096 THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'media inventory cap';
    END IF;
    SELECT count(*) INTO n FROM content.proposed_side_effect AS pe
    WHERE pe.site_id = ws.site_id
      AND pe.workspace_id = p_workspace_id;
    IF n > 10000 THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002', DETAIL = 'proposal cap';
    END IF;

    -- -----------------------------------------------------------------
    -- Row loops: bounds were preflighted above; each row is assembled
    -- explicitly (no record row_to_json), cost-checked against its
    -- family share with short-circuit refusal, then appended.
    -- -----------------------------------------------------------------
    running := 0;
    FOR r IN
        SELECT * FROM content.page_composition AS c
        WHERE c.site_id = ws.site_id
        ORDER BY c.page_id, c.slot_key COLLATE "C", c.order_key, c.id
    LOOP
        IF NOT (comp_meta ? r.component_type) THEN
            RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                USING ERRCODE = 'P0002',
                DETAIL = 'composition row references unknown component type';
        END IF;
        IF comp_meta -> r.component_type ->> 'schema'
           IS DISTINCT FROM r.schema_version
        THEN
            RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                USING ERRCODE = 'P0002',
                DETAIL = 'composition schema version mismatch';
        END IF;
        rowj := jsonb_build_object(
            'id', r.id,
            'site_id', r.site_id,
            'page_id', r.page_id,
            'component_type', r.component_type,
            'schema_version', r.schema_version,
            'parent_id', r.parent_id,
            'slot_key', r.slot_key,
            'order_key', r.order_key,
            'props', r.props,
            'catalog_version', r.catalog_version,
            'created_at', r.created_at,
            'updated_at', r.updated_at,
            'row_version', r.row_version
        );
        running := control.slaif_review_value_cost(rowj, running, 1048576);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'composition byte share';
        END IF;
        composition_docs := composition_docs || rowj;
    END LOOP;

    -- Pages: full retained inventory (tombstones and non-renderable
    -- statuses included, raw deleted_at/style_overrides).  Renderable
    -- rows resolve effective_route by direct call with the helper's
    -- stable exceptions propagated; non-renderable retained rows carry
    -- explicit effective_route = NULL.  slaif_page_style_project yields
    -- zero rows for deleted pages: explicit style = NULL.
    running := 0;
    FOR r IN
        SELECT * FROM content.page AS p
        WHERE p.site_id = ws.site_id
        ORDER BY p.locale COLLATE "C", p.slug COLLATE "C", p.id
    LOOP
        IF r.deleted_at IS NULL AND r.status IN ('PUBLISHED', 'DRAFT') THEN
            -- 049 raises PAGE_SITE_NOT_FOUND / LOCALE_INVALID /
            -- PAGE_PARENT_INVALID / PAGE_DYNAMIC_PARENT /
            -- PAGE_HIERARCHY_CYCLE for renderable rows in invalid
            -- states; those must fail the freeze, not be masked.
            page_route := content.slaif_agent_page_effective_route(r.id);
        ELSE
            page_route := NULL;
        END IF;
        SELECT s.id, s.page_id, s.site_id, s.schema_version, s.row_version,
               s.overrides, s.resolved, s.created_at, s.updated_at
          INTO style_row
          FROM content.slaif_page_style_project(r.id) AS s
         LIMIT 1;
        IF FOUND THEN
            style_json := jsonb_build_object(
                'id', style_row.id,
                'page_id', style_row.page_id,
                'site_id', style_row.site_id,
                'schema_version', style_row.schema_version,
                'row_version', style_row.row_version,
                'overrides', style_row.overrides,
                'resolved', style_row.resolved,
                'created_at', style_row.created_at,
                'updated_at', style_row.updated_at
            );
        ELSE
            style_json := NULL;
        END IF;
        SELECT coalesce(
            jsonb_agg(row_to_json(c) ORDER BY c.slot_key, c.order_key, c.id),
            '[]'::jsonb
        ) INTO nodes_row
        FROM content.page_composition AS c
        WHERE c.site_id = ws.site_id AND c.page_id = r.id;
        rowj := jsonb_build_object(
            'id', r.id,
            'site_id', r.site_id,
            'slug', r.slug,
            'title', r.title,
            'status', r.status,
            'locale', r.locale,
            'parent_id', r.parent_id,
            'route_template', r.route_template,
            'effective_route', page_route,
            'row_version', r.row_version,
            'created_at', r.created_at,
            'updated_at', r.updated_at,
            'deleted_at', r.deleted_at,
            'style_overrides', r.style_overrides,
            'style', style_json,
            'nodes', nodes_row
        );
        running := control.slaif_review_value_cost(rowj, running, 262144);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'pages byte share';
        END IF;
        page_docs := page_docs || rowj;
    END LOOP;

    -- Content model families (shared 262144-byte pool for
    -- types/fields/views; items 1572864; translations 524288;
    -- relations 262144).
    running := 0;
    FOR r IN
        SELECT * FROM content.content_type AS t
        WHERE t.site_id = ws.site_id
        ORDER BY t.key COLLATE "C", t.id
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id, 'key', r.key,
            'labels', r.labels, 'slug_pattern', r.slug_pattern,
            'status', r.status, 'definition_version', r.definition_version,
            'settings', r.settings,
            'created_at', r.created_at, 'updated_at', r.updated_at
        );
        running := control.slaif_review_value_cost(rowj, running, 262144);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'content model byte share';
        END IF;
        type_docs := type_docs || rowj;
    END LOOP;
    FOR r IN
        SELECT * FROM content.field_definition AS f
        WHERE f.site_id = ws.site_id
        ORDER BY f.type_id, f.position, f.key COLLATE "C", f.id
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id, 'type_id', r.type_id,
            'key', r.key, 'label', r.label, 'field_type', r.field_type,
            'required', r.required, 'localized', r.localized,
            'cardinality', r.cardinality, 'position', r.position,
            'validation', r.validation, 'ui_options', r.ui_options,
            'definition_version', r.definition_version,
            'created_at', r.created_at, 'updated_at', r.updated_at
        );
        running := control.slaif_review_value_cost(rowj, running, 262144);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'content model byte share';
        END IF;
        field_docs := field_docs || rowj;
    END LOOP;
    FOR r IN
        SELECT * FROM content.collection_view AS v
        WHERE v.site_id = ws.site_id
        ORDER BY v.type_id, v.key COLLATE "C", v.id
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id, 'type_id', r.type_id,
            'key', r.key, 'filter_spec', r.filter_spec,
            'sort_spec', r.sort_spec, 'projection_spec', r.projection_spec,
            'pagination_spec', r.pagination_spec,
            'created_at', r.created_at, 'updated_at', r.updated_at,
            'definition_version', r.definition_version,
            'row_version', r.row_version
        );
        running := control.slaif_review_value_cost(rowj, running, 262144);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'content model byte share';
        END IF;
        view_docs := view_docs || rowj;
    END LOOP;
    running := 0;
    FOR r IN
        SELECT * FROM content.content_item AS i
        WHERE i.site_id = ws.site_id
        ORDER BY i.type_id, i.slug COLLATE "C" NULLS LAST, i.id
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id, 'type_id', r.type_id,
            'slug', r.slug, 'status', r.status,
            'type_definition_version', r.type_definition_version,
            'values', r.values, 'row_version', r.row_version,
            'created_at', r.created_at, 'updated_at', r.updated_at
        );
        running := control.slaif_review_value_cost(rowj, running, 1572864);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'items byte share';
        END IF;
        item_docs := item_docs || rowj;
    END LOOP;
    running := 0;
    FOR r IN
        SELECT * FROM content.content_item_translation AS t
        WHERE t.site_id = ws.site_id
        ORDER BY t.item_id, t.locale COLLATE "C"
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id, 'item_id', r.item_id,
            'locale', r.locale, 'localized_values', r.localized_values,
            'row_version', r.row_version,
            'created_at', r.created_at, 'updated_at', r.updated_at
        );
        running := control.slaif_review_value_cost(rowj, running, 524288);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'translations byte share';
        END IF;
        translation_docs := translation_docs || rowj;
    END LOOP;
    running := 0;
    FOR r IN
        SELECT * FROM content.item_relation AS rel
        WHERE rel.site_id = ws.site_id
        ORDER BY rel.source_item_id, rel.field_definition_id,
                 rel.position, rel.id
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id,
            'source_item_id', r.source_item_id,
            'field_definition_id', r.field_definition_id,
            'target_item_id', r.target_item_id,
            'position', r.position, 'metadata', r.metadata,
            'row_version', r.row_version,
            'created_at', r.created_at, 'updated_at', r.updated_at
        );
        running := control.slaif_review_value_cost(rowj, running, 262144);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'relations byte share';
        END IF;
        relation_docs := relation_docs || rowj;
    END LOOP;

    -- Site families: locales (32 / 65536), theme (1 / 65536), regions
    -- (8 / 262144), navigation definitions + raw items (16 + 4096 rows,
    -- 256 per (navigation, locale), shared 131072 pool), redirects
    -- (256 / 65536).
    running := 0;
    FOR r IN
        SELECT * FROM content.site_locale AS l
        WHERE l.site_id = ws.site_id
        ORDER BY l.position, l.tag COLLATE "C"
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id, 'tag', r.tag,
            'enabled', r.enabled, 'is_default', r.is_default,
            'position', r.position, 'metadata', r.metadata,
            'row_version', r.row_version,
            'created_at', r.created_at, 'updated_at', r.updated_at
        );
        running := control.slaif_review_value_cost(rowj, running, 65536);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'locales byte share';
        END IF;
        locale_docs := locale_docs || rowj;
    END LOOP;
    SELECT count(*) INTO n FROM content.slaif_theme_project(ws.site_id) AS t;
    IF n > 1 THEN
        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
            USING ERRCODE = 'P0002', DETAIL = 'theme row count';
    END IF;
    theme_json := NULL;
    IF n = 1 THEN
        SELECT t.id, t.site_id, t.schema_version, t.renderer_version,
               t.row_version, t.palette, t.typography, t.layout, t.shape,
               t.created_at, t.updated_at
          INTO r
          FROM content.slaif_theme_project(ws.site_id) AS t;
        theme_json := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id,
            'schema_version', r.schema_version,
            'renderer_version', r.renderer_version,
            'row_version', r.row_version,
            'palette', r.palette, 'typography', r.typography,
            'layout', r.layout, 'shape', r.shape,
            'created_at', r.created_at, 'updated_at', r.updated_at
        );
        IF control.slaif_review_value_cost(theme_json, 0, 65536) < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'theme byte share';
        END IF;
    END IF;
    running := 0;
    FOR r IN
        SELECT * FROM content.slaif_region_list(ws.site_id) AS g2
        ORDER BY g2.region_key COLLATE "C", g2.variant COLLATE "C"
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id,
            'region_key', r.region_key, 'variant', r.variant,
            'content', r.content, 'schema_version', r.schema_version,
            'row_version', r.row_version,
            'created_at', r.created_at, 'updated_at', r.updated_at
        );
        running := control.slaif_review_value_cost(rowj, running, 262144);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'regions byte share';
        END IF;
        region_docs := region_docs || rowj;
    END LOOP;
    running := 0;
    FOR r IN
        SELECT * FROM content.navigation AS d
        WHERE d.site_id = ws.site_id
        ORDER BY d.key COLLATE "C", d.id
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id, 'key', r.key,
            'label', r.label, 'settings', r.settings,
            'created_at', r.created_at, 'updated_at', r.updated_at,
            'labels', r.labels, 'row_version', r.row_version
        );
        running := control.slaif_review_value_cost(rowj, running, 131072);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'navigation byte share';
        END IF;
        nav_def_docs := nav_def_docs || rowj;
    END LOOP;
    FOR r IN
        SELECT * FROM content.navigation_item AS ni
        WHERE ni.site_id = ws.site_id
        ORDER BY ni.navigation_id, ni.locale COLLATE "C", ni."position",
                 ni.parent_key NULLS LAST, ni.id
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id,
            'navigation_id', r.navigation_id, 'parent_id', r.parent_id,
            'page_id', r.page_id, 'target_kind', r.target_kind,
            'target_value', r.target_value, 'labels', r.labels,
            'locale', r.locale, 'position', r."position",
            'row_version', r.row_version,
            'created_at', r.created_at, 'updated_at', r.updated_at,
            'parent_key', r.parent_key
        );
        running := control.slaif_review_value_cost(rowj, running, 131072);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'navigation byte share';
        END IF;
        nav_item_docs := nav_item_docs || rowj;
    END LOOP;
    running := 0;
    FOR r IN
        SELECT * FROM content.redirect AS rd
        WHERE rd.site_id = ws.site_id
        ORDER BY rd.source_route COLLATE "C",
                 rd.locale COLLATE "C" NULLS FIRST, rd.id
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id,
            'source_route', r.source_route, 'target', r.target,
            'status_code', r.status_code, 'locale', r.locale,
            'row_version', r.row_version,
            'created_at', r.created_at, 'updated_at', r.updated_at
        );
        running := control.slaif_review_value_cost(rowj, running, 65536);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'redirects byte share';
        END IF;
        redirect_docs := redirect_docs || rowj;
    END LOOP;

    -- Media inventory (all site-visible rows, metadata only, no bytes)
    -- and workspace-scoped proposals.
    running := 0;
    FOR r IN
        SELECT * FROM content.media_asset AS m
        WHERE m.site_id = ws.site_id
        ORDER BY m.created_at, m.id
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id,
            'uploaded_by', r.uploaded_by, 'filename', r.filename,
            'mime_type', r.mime_type, 'size_bytes', r.size_bytes,
            'content_hash', r.content_hash, 'storage_key', r.storage_key,
            'alt_text', r.alt_text, 'metadata', r.metadata,
            'created_at', r.created_at, 'updated_at', r.updated_at,
            'public_status', r.public_status,
            'published_at', r.published_at
        );
        running := control.slaif_review_value_cost(rowj, running, 524288);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002',
                DETAIL = 'media inventory byte share';
        END IF;
        media_inventory_docs := media_inventory_docs || rowj;
    END LOOP;
    running := 0;
    FOR r IN
        SELECT * FROM content.proposed_side_effect AS pe
        WHERE pe.site_id = ws.site_id AND pe.workspace_id = p_workspace_id
        ORDER BY pe.created_at, pe.id
    LOOP
        rowj := jsonb_build_object(
            'id', r.id, 'site_id', r.site_id,
            'workspace_id', r.workspace_id, 'kind', r.kind,
            'payload', r.payload, 'state', r.state,
            'created_at', r.created_at, 'updated_at', r.updated_at
        );
        running := control.slaif_review_value_cost(rowj, running, 262144);
        IF running < 0 THEN
            RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
                USING ERRCODE = 'P0002', DETAIL = 'proposals byte share';
        END IF;
        proposal_docs := proposal_docs || rowj;
    END LOOP;

    -- -----------------------------------------------------------------
    -- R6 typed media reference closure (after every family bound).
    -- The selected `media` set is the typed resolved closure over the
    -- retained rows: the declared reference positions of
    -- binding_kind = 'media_asset' components (generic over the
    -- persisted schema: top-level and declared array-item
    -- reference/format=uuid props) plus the site's media/document
    -- field definitions at declared cardinality, base and every
    -- localized value.  No UUID-looking value outside a declared
    -- reference position is promoted; regions contribute nothing under
    -- the complete supported region schema.  control.slaif_review_media
    -- _append resolves under the held locks via the trusted same-site
    -- resolver, deduplicates on the selected map (first reference
    -- included) and RAISEs REVIEW_MEDIA_REF_UNRESOLVED for any
    -- unresolved typed reference before any return.
    -- -----------------------------------------------------------------
    FOR c_row IN
        SELECT * FROM content.page_composition AS c
        WHERE c.site_id = ws.site_id
        ORDER BY c.page_id, c.slot_key COLLATE "C", c.order_key, c.id
    LOOP
        IF c_row.props IS NULL THEN
            CONTINUE;
        END IF;
        meta := comp_meta -> c_row.component_type;
        IF meta ? 'top' THEN
            ref_value := c_row.props -> (meta ->> 'top');
            IF ref_value IS NULL THEN
                IF (meta ->> 'req') = 'true' THEN
                    RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                        USING ERRCODE = 'P0002',
                        DETAIL = 'required media reference missing';
                END IF;
            ELSE
                IF jsonb_typeof(ref_value) <> 'string' THEN
                    RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                        USING ERRCODE = 'P0002',
                        DETAIL = 'declared media reference not a string';
                END IF;
                BEGIN
                    media_id := (ref_value #>> '{}')::uuid;
                    media_docs := control.slaif_review_media_append(
                        ws.site_id, media_id, media_docs
                    );
                EXCEPTION WHEN invalid_text_representation THEN
                    RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                        USING ERRCODE = 'P0002',
                        DETAIL = 'declared media reference not a uuid';
                END;
            END IF;
        END IF;
        IF meta ? 'arr' THEN
            arr := c_row.props -> (meta ->> 'arr');
            IF arr IS NOT NULL THEN
                IF jsonb_typeof(arr) <> 'array' THEN
                    RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                        USING ERRCODE = 'P0002',
                        DETAIL = 'declared media array not an array';
                END IF;
                FOR arr_item IN
                    SELECT value FROM jsonb_array_elements(arr) AS e
                LOOP
                    IF jsonb_typeof(arr_item) <> 'object' THEN
                        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                            USING ERRCODE = 'P0002',
                            DETAIL = 'media array item not an object';
                    END IF;
                    ref_value := arr_item -> (meta ->> 'ref');
                    IF ref_value IS NULL
                       OR jsonb_typeof(ref_value) <> 'string'
                    THEN
                        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                            USING ERRCODE = 'P0002',
                            DETAIL = 'declared media item reference invalid';
                    END IF;
                    BEGIN
                        media_id := (ref_value #>> '{}')::uuid;
                        media_docs := control.slaif_review_media_append(
                            ws.site_id, media_id, media_docs
                        );
                    EXCEPTION WHEN invalid_text_representation THEN
                        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                            USING ERRCODE = 'P0002',
                            DETAIL = 'declared media item reference not a uuid';
                    END;
                END LOOP;
            END IF;
        END IF;
    END LOOP;
    FOR f_row IN
        SELECT * FROM content.field_definition AS f
        WHERE f.site_id = ws.site_id
          AND f.field_type IN ('media', 'document')
        ORDER BY f.type_id, f.position, f.key COLLATE "C"
    LOOP
        FOR val IN
            SELECT i.id AS item_id, i.values AS base_values
              FROM content.content_item AS i
             WHERE i.site_id = ws.site_id AND i.type_id = f_row.type_id
             ORDER BY i.id
        LOOP
            IF val.base_values -> f_row.key IS NOT NULL THEN
                IF f_row.cardinality = 1 THEN
                    IF jsonb_typeof(val.base_values -> f_row.key) <> 'string'
                       OR btrim(val.base_values ->> f_row.key) = ''
                    THEN
                        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                            USING ERRCODE = 'P0002',
                            DETAIL = 'media field value must be a non-empty uuid string';
                    END IF;
                    BEGIN
                        media_id := (val.base_values ->> f_row.key)::uuid;
                        media_docs := control.slaif_review_media_append(
                            ws.site_id, media_id, media_docs
                        );
                    EXCEPTION WHEN invalid_text_representation THEN
                        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                            USING ERRCODE = 'P0002',
                            DETAIL = 'media field value not a uuid';
                    END;
                ELSE
                    IF jsonb_typeof(val.base_values -> f_row.key) <> 'array'
                    THEN
                        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                            USING ERRCODE = 'P0002',
                            DETAIL = 'multi media field value must be an array';
                    END IF;
                    FOR ref_value IN
                        SELECT value FROM jsonb_array_elements(
                            val.base_values -> f_row.key
                        ) AS e
                    LOOP
                        IF jsonb_typeof(ref_value) <> 'string'
                           OR btrim(ref_value #>> '{}') = ''
                        THEN
                            RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                                USING ERRCODE = 'P0002',
                                DETAIL = 'media array value not a uuid string';
                        END IF;
                        BEGIN
                            media_id := (ref_value #>> '{}')::uuid;
                            media_docs := control.slaif_review_media_append(
                                ws.site_id, media_id, media_docs
                            );
                        EXCEPTION WHEN invalid_text_representation THEN
                            RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                                USING ERRCODE = 'P0002',
                                DETAIL = 'media array value not a uuid';
                        END;
                    END LOOP;
                END IF;
            END IF;
        END LOOP;
        FOR val IN
            SELECT t.id AS translation_id, t.item_id AS item_id,
                   t.localized_values AS localized_values
              FROM content.content_item_translation AS t
             WHERE t.site_id = ws.site_id
               AND t.item_id IN (
                   SELECT i.id FROM content.content_item AS i
                   WHERE i.site_id = ws.site_id
                     AND i.type_id = f_row.type_id
               )
             ORDER BY t.id
        LOOP
            IF val.localized_values -> f_row.key IS NOT NULL THEN
                IF f_row.cardinality = 1 THEN
                    IF jsonb_typeof(
                           val.localized_values -> f_row.key
                       ) <> 'string'
                       OR btrim(val.localized_values ->> f_row.key) = ''
                    THEN
                        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                            USING ERRCODE = 'P0002',
                            DETAIL = 'localized media field value must be a non-empty uuid string';
                    END IF;
                    BEGIN
                        media_id := (val.localized_values ->> f_row.key)::uuid;
                        media_docs := control.slaif_review_media_append(
                            ws.site_id, media_id, media_docs
                        );
                    EXCEPTION WHEN invalid_text_representation THEN
                        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                            USING ERRCODE = 'P0002',
                            DETAIL = 'localized media field value not a uuid';
                    END;
                ELSE
                    IF jsonb_typeof(
                           val.localized_values -> f_row.key
                       ) <> 'array'
                    THEN
                        RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                            USING ERRCODE = 'P0002',
                            DETAIL = 'localized multi media field value must be an array';
                    END IF;
                    FOR ref_value IN
                        SELECT value FROM jsonb_array_elements(
                            val.localized_values -> f_row.key
                        ) AS e
                    LOOP
                        IF jsonb_typeof(ref_value) <> 'string'
                           OR btrim(ref_value #>> '{}') = ''
                        THEN
                            RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                                USING ERRCODE = 'P0002',
                                DETAIL = 'localized media array value not a uuid string';
                        END IF;
                        BEGIN
                            media_id := (ref_value #>> '{}')::uuid;
                            media_docs := control.slaif_review_media_append(
                                ws.site_id, media_id, media_docs
                            );
                        EXCEPTION WHEN invalid_text_representation THEN
                            RAISE EXCEPTION 'SNAPSHOT_VALIDATION_FAILED'
                                USING ERRCODE = 'P0002',
                                DETAIL = 'localized media array value not a uuid';
                        END;
                    END LOOP;
                END IF;
            END IF;
        END LOOP;
    END LOOP;

    -- -----------------------------------------------------------------
    -- v2 document assembly.  workspace_versions is the trusted pin set
    -- recorded at workspace creation (digest-covered in the payload);
    -- the sibling versions block keeps its unchanged member set in the
    -- Python build.  The final gate is the exact canonical total-byte
    -- budget (8 MiB); raw value depth was enforced per raw value in the
    -- preflights and no global document depth limit is applied.
    -- -----------------------------------------------------------------
    doc := jsonb_build_object(
        'state_version', 'review-snapshot/v2',
        'workspace_id', p_workspace_id,
        'site_id', ws.site_id,
        'site', jsonb_build_object(
            'site_key', site_row.site_key,
            'display_name', site_row.display_name,
            'status', site_row.status,
            'default_locale', site_row.default_locale,
            'component_catalog_version',
                site_row.component_catalog_version,
            'content_model_revision', site_row.content_model_revision,
            'created_at', site_row.created_at,
            'updated_at', site_row.updated_at
        ),
        'base_site_revision', site_revision,
        'operation_watermark', ws.operation_watermark,
        'workspace_versions', ws.version_facts,
        'locales', locale_docs,
        'theme', theme_json,
        'regions', region_docs,
        'navigation', jsonb_build_object(
            'definitions', nav_def_docs,
            'items', nav_item_docs
        ),
        'redirects', redirect_docs,
        'pages', page_docs,
        'page_compositions', composition_docs,
        'content', jsonb_build_object(
            'types', type_docs,
            'fields', field_docs,
            'items', item_docs,
            'translations', translation_docs,
            'relations', relation_docs,
            'views', view_docs
        ),
        'proposals', proposal_docs,
        'media_inventory', media_inventory_docs,
        'media', media_docs
    );
    IF control.slaif_review_value_cost(doc, 0, 8388608) < 0 THEN
        RAISE EXCEPTION 'REVIEW_SNAPSHOT_OVER_BUDGET'
            USING ERRCODE = 'P0002',
            DETAIL = 'total canonical payload budget';
    END IF;
    RETURN doc;
END;
$fn$
"""

_MEDIA_APPEND_SQL = r"""
-- Fourth 076 helper: trusted same-site media reference append for the
-- v2 materializer's typed closure.  Deduplicates on the selected map
-- (jsonb ? key: NULL-safe, first reference included), resolves under
-- the caller's held locks via the 068 same-site resolver, and fails
-- closed for unresolved typed references.
CREATE OR REPLACE FUNCTION control.slaif_review_media_append(
    p_site_id uuid, p_media_id uuid, p_docs jsonb
) RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path = pg_catalog AS $fn$
DECLARE
    media_row record;
BEGIN
    IF p_docs ? p_media_id::text THEN
        RETURN p_docs;
    END IF;
    SELECT * INTO media_row
    FROM content.slaif_render_media_resolve(p_site_id, p_media_id);
    IF NOT FOUND THEN
        RAISE EXCEPTION 'REVIEW_MEDIA_REF_UNRESOLVED'
            USING ERRCODE = 'P0002',
            DETAIL = 'typed media reference without media_asset row';
    END IF;
    RETURN p_docs || jsonb_build_object(
        p_media_id::text, jsonb_build_object(
            'id', p_media_id,
            'mime_type', media_row.mime_type,
            'size_bytes', media_row.size_bytes,
            'content_hash', media_row.content_hash,
            'public_status', media_row.public_status
        )
    );
END;
$fn$
"""

# ---------------------------------------------------------------------------
# Patch 4: snapshot completion (v2 body + verbatim 070_001 v1 restoration).
#
# _SNAPSHOT_COMPLETE_070_SQL is the exact 070_001 v1 DDL statement as it
# appears in migration 070_001, with the single documented adjustment
# from the 075_001 restoration convention: the plain CREATE FUNCTION
# header is CREATE OR REPLACE FUNCTION (header keyword only; the $fn$
# body is byte-identical, so prosrc is byte-identical).  sha256 of the
# original 070_001 statement text:
# f32335a3e960da35e90159db1ef24d003a7771d91253ccc7e4de2c81c272f9e6).
# _SNAPSHOT_COMPLETE_V2_SQL is the v2 completion contract (see module
# docstring).
# ---------------------------------------------------------------------------

_SNAPSHOT_COMPLETE_070_SQL = r"""
CREATE OR REPLACE FUNCTION control.slaif_review_snapshot_complete(
            p_workspace_id uuid, p_row jsonb
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            computed text;
            snapshot_id uuid;
        BEGIN
            IF jsonb_typeof(p_row) <> 'object'
               OR NOT (p_row ?& ARRAY[
                    'workspace_id','site_id','status','revision_watermark',
                    'versions','normalized_state','validation_report',
                    'media_references','browser_evidence','payload','digest',
                    'created_by']::text[])
               OR p_row->>'workspace_id' IS DISTINCT FROM p_workspace_id::text
               OR p_row->>'status' IS DISTINCT FROM 'COMPLETE'
               OR jsonb_typeof(p_row->'revision_watermark') <> 'number'
               OR (p_row->'revision_watermark')::bigint < 0
               OR jsonb_typeof(p_row->'versions') <> 'object'
               OR jsonb_typeof(p_row->'normalized_state') <> 'object'
               OR jsonb_typeof(p_row->'validation_report') <> 'object'
               OR jsonb_typeof(p_row->'media_references') <> 'array'
               OR jsonb_typeof(p_row->'browser_evidence') <> 'array'
               OR jsonb_typeof(p_row->'payload') <> 'object'
               OR p_row->>'digest' IS NULL
               OR p_row->>'digest' !~ '^[0-9a-f]{64}$'
               OR p_row->>'created_by' IS NULL
               OR p_row->>'created_by' !~ '^[A-Za-z0-9._:-]{1,128}$'
            THEN
                RAISE EXCEPTION 'SNAPSHOT_ROW_INVALID' USING ERRCODE = 'P0002';
            END IF;
            computed := encode(
                sha256(convert_to(
                    control.slaif_canonical_jsonb_text(p_row->'payload'), 'UTF8'
                )),
                'hex'
            );
            IF computed IS DISTINCT FROM p_row->>'digest' THEN
                RAISE EXCEPTION 'SNAPSHOT_DIGEST_MISMATCH'
                    USING ERRCODE = 'P0002';
            END IF;
            INSERT INTO control.review_snapshot (
                workspace_id, site_id, status, revision_watermark, versions,
                normalized_state, validation_report, media_references,
                browser_evidence, payload, digest, created_by
            ) VALUES (
                p_workspace_id, (p_row->>'site_id')::uuid, 'COMPLETE',
                (p_row->'revision_watermark')::bigint, p_row->'versions',
                p_row->'normalized_state', p_row->'validation_report',
                p_row->'media_references', p_row->'browser_evidence',
                p_row->'payload', p_row->>'digest', p_row->>'created_by'
            ) RETURNING id INTO snapshot_id;
            UPDATE control.workspace
               SET status = 'REVIEW', review_snapshot_id = snapshot_id
             WHERE id = p_workspace_id AND status = 'FREEZING';
            IF NOT FOUND THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_FREEZING' USING ERRCODE = 'P0002';
            END IF;
            RETURN snapshot_id;
        END;
        $fn$
"""

_SNAPSHOT_COMPLETE_V2_SQL = r"""
        CREATE OR REPLACE FUNCTION control.slaif_review_snapshot_complete(
            p_workspace_id uuid, p_row jsonb
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            computed text;
            snapshot_id uuid;
            n integer;
            actual_site_id uuid;
            actual_version_facts jsonb;
        BEGIN
            -- Envelope invariants (070_001, unchanged).
            IF jsonb_typeof(p_row) <> 'object'
               OR NOT (p_row ?& ARRAY[
                    'workspace_id','site_id','status','revision_watermark',
                    'versions','normalized_state','validation_report',
                    'media_references','browser_evidence','payload','digest',
                    'created_by']::text[])
               OR p_row->>'workspace_id' IS DISTINCT FROM p_workspace_id::text
               OR p_row->>'status' IS DISTINCT FROM 'COMPLETE'
               OR p_row->>'site_id' IS NULL
               OR p_row->>'site_id' !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
               OR jsonb_typeof(p_row->'revision_watermark') <> 'number'
               OR (p_row->'revision_watermark')::bigint < 0
               OR jsonb_typeof(p_row->'versions') <> 'object'
               OR jsonb_typeof(p_row->'normalized_state') <> 'object'
               OR jsonb_typeof(p_row->'validation_report') <> 'object'
               OR jsonb_typeof(p_row->'media_references') <> 'array'
               OR jsonb_typeof(p_row->'browser_evidence') <> 'array'
               OR jsonb_typeof(p_row->'payload') <> 'object'
               OR p_row->>'digest' IS NULL
               OR p_row->>'digest' !~ '^[0-9a-f]{64}$'
               OR p_row->>'created_by' IS NULL
               OR p_row->>'created_by' !~ '^[A-Za-z0-9._:-]{1,128}$'
            THEN
                RAISE EXCEPTION 'SNAPSHOT_ROW_INVALID' USING ERRCODE = 'P0002';
            END IF;

            -- v2 invariant (context binding): the row must describe the
            -- actual selected workspace, not merely supplied values that
            -- agree with each other.  The freeze job holds this row FOR
            -- UPDATE in the same transaction (the materializer lock), so
            -- the read runs under the existing lock and changes no lock
            -- ordering or authority.
            SELECT w.site_id, w.version_facts
            INTO actual_site_id, actual_version_facts
            FROM control.workspace w
            WHERE w.id = p_workspace_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'REVIEW_WORKSPACE_NOT_FOUND'
                    USING ERRCODE = 'P0002';
            END IF;
            IF (p_row->>'site_id')::uuid IS DISTINCT FROM actual_site_id THEN
                RAISE EXCEPTION 'SNAPSHOT_SITE_MISMATCH'
                    USING ERRCODE = 'P0002';
            END IF;

            -- v2 invariant (a): the stored normalized state and payload
            -- are the identical document (jsonb value equality).
            IF p_row->'normalized_state' IS DISTINCT FROM p_row->'payload' THEN
                RAISE EXCEPTION 'SNAPSHOT_STATE_PAYLOAD_DIVERGED'
                    USING ERRCODE = 'P0002';
            END IF;

            -- v2 invariant (b): the payload carries the complete trusted
            -- domain capture (state_version review-snapshot/v2).
            IF (p_row->'payload')->>'state_version'
                   IS DISTINCT FROM 'review-snapshot/v2'
               OR NOT ((p_row->'payload') ?& ARRAY[
                    'state_version','workspace_id','site_id','site',
                    'base_site_revision','operation_watermark',
                    'workspace_versions','locales','theme','regions',
                    'navigation','redirects','pages','page_compositions',
                    'content','proposals','media_inventory','media'
                ]::text[])
               OR (p_row->'payload')->>'workspace_id'
                   IS DISTINCT FROM p_workspace_id::text
               OR (p_row->'payload')->>'site_id' IS DISTINCT FROM p_row->>'site_id'
               OR jsonb_typeof((p_row->'payload')->'site') <> 'object'
               OR jsonb_typeof((p_row->'payload')->'workspace_versions') <> 'object'
               OR jsonb_typeof((p_row->'payload')->'locales') <> 'array'
               OR jsonb_typeof((p_row->'payload')->'theme') <> 'object'
               OR jsonb_typeof((p_row->'payload')->'regions') <> 'array'
               OR jsonb_typeof((p_row->'payload')->'navigation') <> 'object'
               OR NOT ((p_row->'payload')->'navigation' ?& ARRAY['definitions','items']::text[])
               OR jsonb_typeof((p_row->'payload')->'redirects') <> 'array'
               OR jsonb_typeof((p_row->'payload')->'pages') <> 'array'
               OR jsonb_typeof((p_row->'payload')->'page_compositions') <> 'array'
               OR jsonb_typeof((p_row->'payload')->'content') <> 'object'
               OR NOT ((p_row->'payload')->'content' ?& ARRAY['types','fields','items','translations','relations','views']::text[])
               OR jsonb_typeof((p_row->'payload')->'proposals') <> 'array'
               OR jsonb_typeof((p_row->'payload')->'media_inventory') <> 'array'
               OR jsonb_typeof((p_row->'payload')->'media') <> 'object'
            THEN
                RAISE EXCEPTION 'SNAPSHOT_PAYLOAD_INVALID'
                    USING ERRCODE = 'P0002';
            END IF;

            -- v2 invariant (e): workspace_versions is the actual
            -- trusted pin set recorded on the workspace, and that set
            -- is the exact supported six-pin literal (same literal as
            -- the materializer gate).  A legacy unpinned workspace
            -- ('{}') fails the first comparison; a supplied pin that
            -- drifts from the workspace facts fails it as well.
            IF (p_row->'payload')->'workspace_versions' IS DISTINCT FROM
                actual_version_facts
            THEN
                RAISE EXCEPTION 'SNAPSHOT_WORKSPACE_VERSIONS_MISMATCH'
                    USING ERRCODE = 'P0002';
            END IF;
            IF (p_row->'payload')->'workspace_versions' IS DISTINCT FROM
                '{"catalog":"catalog-v1","composition_schema":"site-composition/v1","content_model":"content-model/v1","design_system":"design-system/v1","puck":"0.20.2","renderer":"renderer-v1"}'::jsonb
            THEN
                RAISE EXCEPTION 'SNAPSHOT_WORKSPACE_VERSIONS_UNSUPPORTED'
                    USING ERRCODE = 'P0002';
            END IF;

            -- v2 invariant (c): media_references is the payload media
            -- map entry for entry (reference shape, map equality in
            -- both directions, no duplicate ids).  The uuid-shape
            -- regex keeps the map lookup cast-free.
            SELECT count(*) INTO n
            FROM jsonb_array_elements(p_row->'media_references') AS ref
            WHERE jsonb_typeof(ref.value) <> 'object'
               OR NOT (ref.value ?& ARRAY['id','mime_type','size_bytes','content_hash','public_status']::text[])
               OR jsonb_typeof(ref.value->'id') <> 'string'
               OR ref.value->>'id' !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
               OR NOT EXISTS (
                    SELECT 1 FROM jsonb_each(p_row->'payload'->'media') AS m(k, v)
                    WHERE k = ref.value->>'id'
                      AND m.v IS NOT DISTINCT FROM ref.value
               );
            IF n <> 0 THEN
                RAISE EXCEPTION 'SNAPSHOT_MEDIA_REFERENCES_MISMATCH'
                    USING ERRCODE = 'P0002';
            END IF;
            SELECT count(*) INTO n
            FROM jsonb_each(p_row->'payload'->'media') AS m(k, v)
            WHERE NOT EXISTS (
                SELECT 1 FROM jsonb_array_elements(p_row->'media_references') AS ref
                WHERE ref.value->>'id' = k
            );
            IF n <> 0 THEN
                RAISE EXCEPTION 'SNAPSHOT_MEDIA_REFERENCES_MISMATCH'
                    USING ERRCODE = 'P0002';
            END IF;
            SELECT count(*) INTO n
            FROM (
                SELECT ref.value->>'id' AS rid
                FROM jsonb_array_elements(p_row->'media_references') AS ref
                GROUP BY ref.value->>'id' HAVING count(*) > 1
            ) AS dups;
            IF n <> 0 THEN
                RAISE EXCEPTION 'SNAPSHOT_MEDIA_REFERENCES_MISMATCH'
                    USING ERRCODE = 'P0002';
            END IF;

            -- v2 invariant (d): every browser evidence id is a COMPLETED
            -- browser run of this workspace (text comparison, so a
            -- malformed id fails the match instead of casting).
            SELECT count(*) INTO n
            FROM jsonb_array_elements(p_row->'browser_evidence') AS ev
            WHERE jsonb_typeof(ev.value) <> 'object'
               OR jsonb_typeof(ev.value->'id') <> 'string'
               OR NOT EXISTS (
                    SELECT 1 FROM control.browser_run br
                    WHERE br.workspace_id = p_workspace_id
                      AND br.state = 'COMPLETED'
                      AND br.id::text = ev.value->>'id'
               );
            IF n <> 0 THEN
                RAISE EXCEPTION 'SNAPSHOT_BROWSER_EVIDENCE_UNRESOLVED'
                    USING ERRCODE = 'P0002';
            END IF;

            -- Digest recomputation over the stored payload in the 070
            -- canonical form (the v2 Python serializer is byte-identical
            -- to it for every supported value, so the worker can
            -- recompute the same bytes).
            computed := encode(
                sha256(convert_to(
                    control.slaif_canonical_jsonb_text(p_row->'payload'), 'UTF8'
                )),
                'hex'
            );
            IF computed IS DISTINCT FROM p_row->>'digest' THEN
                RAISE EXCEPTION 'SNAPSHOT_DIGEST_MISMATCH'
                    USING ERRCODE = 'P0002';
            END IF;
            INSERT INTO control.review_snapshot (
                workspace_id, site_id, status, revision_watermark, versions,
                normalized_state, validation_report, media_references,
                browser_evidence, payload, digest, created_by
            ) VALUES (
                p_workspace_id, (p_row->>'site_id')::uuid, 'COMPLETE',
                (p_row->'revision_watermark')::bigint, p_row->'versions',
                p_row->'normalized_state', p_row->'validation_report',
                p_row->'media_references', p_row->'browser_evidence',
                p_row->'payload', p_row->>'digest', p_row->>'created_by'
            ) RETURNING id INTO snapshot_id;
            UPDATE control.workspace
               SET status = 'REVIEW', review_snapshot_id = snapshot_id
             WHERE id = p_workspace_id AND status = 'FREEZING';
            IF NOT FOUND THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_FREEZING'
                    USING ERRCODE = 'P0002';
            END IF;
            RETURN snapshot_id;
        END;
        $fn$

"""


# ---------------------------------------------------------------------------
# Patch 5: the frozen-review read surface.
#
# Three small functions, one human active-preview byte read, and one
# run-bound preview byte read instead of a per-family SQL surface:
#
# 1. ``slaif_review_snapshot_frozen_state(uuid) -> jsonb`` - the single
#    narrow immutable snapshot fetch (one COMPLETE row as a jsonb
#    document, or NULL).  EXECUTE: slaif_preview_reader.  The frozen
#    render surface calls it exactly once per request; all row
#    extraction/matching is typed Python against the stored document.
#
# 2. ``slaif_review_projection_authorize(text,bytea,uuid) -> setof
#    (workspace_id, site_id, user_account_id)`` - the session /
#    membership / snapshot-COMPLETE gate for the review projection
#    route.  Mirrors the 054 preview session predicates with the
#    documented frozen-read deltas: NO session touch (the 054
#    touch path and the 071 finalize touch are both write paths; the
#    review route is strictly read-only), site-ACTIVE is NOT required
#    (an immutable snapshot outlives later site status changes;
#    access stays membership-scoped to that site), and workspace
#    ACTIVE is replaced by snapshot COMPLETE (the workspace is REVIEW
#    after freeze; the table CHECK makes every retained row COMPLETE).
#    The idle threshold is the trusted 1800s review-surface constant
#    (the same value the 071 human-session artifact gates use).
#    Membership gate: platform administrator OR any effective site
#    membership on the snapshot's site - exactly the 071 gate.
#    EXECUTE: slaif_preview_reader.
#
# 3. ``slaif_review_media_authorize(text,bytea,uuid,uuid) -> setof
#    (site_id, content_hash, size_bytes, mime_type)`` - the frozen
#    media byte gate: the same session/membership predicates as (2)
#    plus the full trusted frozen-media binding.  The row's versions
#    column AND the payload's captured workspace_versions must each
#    be exactly the six supported release pins; the payload's own
#    site/workspace identity must be well-formed UUID text equal to
#    the trusted row columns.  The v2 payload's site block must be a
#    supported catalog/state with a non-negative integer
#    content_model_revision; the stored frozen descriptor
#    (payload->'media'-><id>) must be exactly the five-key
#    {id,mime_type,size_bytes,content_hash,public_status} shape with
#    matching id, a 068-registered mime class (PNG/JPEG/PDF), a
#    sha256-hex content_hash, a media_public_status enum value and a
#    positive size inside the bigint range (every malformed shape is
#    an empty result, never an error); the row's stored
#    media_references must contain exactly one same-id reference
#    with equal shared fields; and the retained inventory must
#    carry exactly one same-id row bound to the snapshot site,
#    agreeing field-for-field with the descriptor and carrying the
#    store's canonical storage key.  No live media_asset join: the
#    payload is digest-covered by the write-time completion gate,
#    the row identity is set by the same trusted INSERT, and the
#    bytes are content-addressed and self-proved at read time.
#    EXECUTE: slaif_media.
#
# 4. ``slaif_media_preview_read(text,bytea,uuid,uuid,uuid,integer,
#    integer,integer) -> setof (media_asset record)`` - the minimal
#    authorized ACTIVE preview byte read BEFORE freeze.  It delegates
#    the full 054 active-preview chain (active account/site/workspace,
#    session freshness, creator or workspace:read-all, preview:inspect
#    / platform-admin, shared advisory 280 + FOR SHARE recheck) to the
#    existing ``slaif_render_preview_authorize_internal`` with
#    ``p_touch = false``, then sets the transaction-scoped COW session
#    to the authorized workspace and reads ``content.media_asset`` in
#    that workspace's overlay context.  The selected workspace may be
#    the Agent workspace (054's actor_type gate admits HUMAN/AGENT/
#    IMPORT); the caller's context is the server-authorized one, so a
#    client-selected site/workspace/media pair outside the chain fails
#    closed to an empty result.  No publication, no content writes, no
#    new role/credential/topology.  EXECUTE: slaif_media.
#
# 5. ``slaif_media_bound_preview_read(uuid,uuid,uuid,uuid,text,text,
#    text[],bigint,integer,text,uuid) -> setof (media_asset record)`` -
#    the confined run-bound private byte read BEFORE freeze.  The
#    bound-run document fetch consumed the run's preview token (036,
#    p_consume = true); this recheck (p_consume = false) requires the
#    run's stored nonce to equal this token's nonce, so the read exists
#    only after the authorized document and only for the bound run.
#    036 re-verifies every claim against the run row (capability,
#    site, workspace, run, route, target, evidence, artifact quota,
#    duration, freshness, scopes, workspace/site ACTIVE, shared
#    advisory 280 + FOR UPDATE); the path contributes only the media
#    id, which is then read in the bound workspace's COW overlay.
#    No human session, no agent capability, no new credential.
#    EXECUTE: slaif_media.
# ---------------------------------------------------------------------------

_FROZEN_STATE_SQL = r"""
CREATE FUNCTION control.slaif_review_snapshot_frozen_state(
    p_snapshot_id uuid
) RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog AS $fn$
    SELECT to_jsonb(snapshot.*)
    FROM control.review_snapshot AS snapshot
    WHERE snapshot.id = p_snapshot_id
      AND snapshot.status = 'COMPLETE'
$fn$
"""

_PROJECTION_AUTHORIZE_SQL = r"""
CREATE FUNCTION control.slaif_review_projection_authorize(
    p_public_id text, p_secret_digest bytea, p_snapshot_id uuid
) RETURNS TABLE (
    workspace_id uuid, site_id uuid, user_account_id uuid
) LANGUAGE plpgsql SECURITY DEFINER VOLATILE
SET search_path = pg_catalog AS $fn$
DECLARE
    selected_session control.user_session%ROWTYPE;
    account_status text;
    snapshot_row control.review_snapshot%ROWTYPE;
    user_id uuid;
BEGIN
    IF p_public_id IS NULL OR p_secret_digest IS NULL
       OR octet_length(p_secret_digest) IS DISTINCT FROM 32
       OR p_snapshot_id IS NULL
       OR p_public_id !~ '^sas2_[0-9a-f]{32}$' THEN RETURN; END IF;

    SELECT session.* INTO selected_session
    FROM control.user_session AS session
    WHERE session.public_id = p_public_id
      AND session.secret_digest = p_secret_digest
    FOR SHARE;
    IF NOT FOUND THEN RETURN; END IF;

    SELECT account.status INTO account_status
    FROM control.user_account AS account
    WHERE account.id = selected_session.user_account_id;
    IF account_status IS DISTINCT FROM 'ACTIVE'
       OR selected_session.revoked_at IS NOT NULL
       OR selected_session.absolute_expires_at <= CURRENT_TIMESTAMP
       OR selected_session.last_seen_at
            + make_interval(secs => 1800) <= CURRENT_TIMESTAMP
    THEN RETURN; END IF;

    user_id := selected_session.user_account_id;
    SELECT snapshot.* INTO snapshot_row
    FROM control.review_snapshot AS snapshot
    WHERE snapshot.id = p_snapshot_id;
    IF NOT FOUND THEN RETURN; END IF;

    -- Supported-format gate: the faithful frozen PROJECTION reads v2
    -- documents only.  v1 (legacy) snapshots are not rejected or
    -- rewritten: they keep their existing honest read-model view
    -- (whose reader already carries v1 media facts).  Any version
    -- other than the supported v2 fails closed to a uniform 404 here,
    -- never a fallback rendering.
    IF snapshot_row.payload->>'state_version'
           IS DISTINCT FROM 'review-snapshot/v2' THEN RETURN; END IF;

    IF NOT EXISTS (
        SELECT 1 FROM control.platform_administrator AS administrator
        WHERE administrator.user_account_id = user_id
    ) AND NOT EXISTS (
        SELECT 1 FROM control.slaif_effective_human_membership(
            user_id, snapshot_row.site_id
        )
    ) THEN RETURN; END IF;

    RETURN QUERY SELECT snapshot_row.workspace_id, snapshot_row.site_id,
        user_id;
END;
$fn$
"""

_MEDIA_AUTHORIZE_SQL = r"""
CREATE FUNCTION control.slaif_review_media_authorize(
    p_public_id text, p_secret_digest bytea,
    p_snapshot_id uuid, p_media_id uuid
) RETURNS TABLE (
    site_id uuid, content_hash text, size_bytes bigint, mime_type text
) LANGUAGE plpgsql SECURITY DEFINER VOLATILE
SET search_path = pg_catalog AS $fn$
DECLARE
    selected_session control.user_session%ROWTYPE;
    account_status text;
    snapshot_row control.review_snapshot%ROWTYPE;
    site_profile jsonb;
    entry jsonb;
    reference jsonb;
    reference_matches integer;
    supported_pins jsonb;
    inventory_matches integer;
    inventory_row jsonb;
    hash_text text;
    expected_storage_key text;
    user_id uuid;
BEGIN
    IF p_public_id IS NULL OR p_secret_digest IS NULL
       OR octet_length(p_secret_digest) IS DISTINCT FROM 32
       OR p_snapshot_id IS NULL OR p_media_id IS NULL
       OR p_public_id !~ '^sas2_[0-9a-f]{32}$' THEN RETURN; END IF;

    SELECT session.* INTO selected_session
    FROM control.user_session AS session
    WHERE session.public_id = p_public_id
      AND session.secret_digest = p_secret_digest
    FOR SHARE;
    IF NOT FOUND THEN RETURN; END IF;

    SELECT account.status INTO account_status
    FROM control.user_account AS account
    WHERE account.id = selected_session.user_account_id;
    IF account_status IS DISTINCT FROM 'ACTIVE'
       OR selected_session.revoked_at IS NOT NULL
       OR selected_session.absolute_expires_at <= CURRENT_TIMESTAMP
       OR selected_session.last_seen_at
            + make_interval(secs => 1800) <= CURRENT_TIMESTAMP
    THEN RETURN; END IF;

    user_id := selected_session.user_account_id;
    SELECT snapshot.* INTO snapshot_row
    FROM control.review_snapshot AS snapshot
    WHERE snapshot.id = p_snapshot_id;
    IF NOT FOUND THEN RETURN; END IF;

    -- Supported-format gate (same as the projection gate): the
    -- faithful frozen media read binds the v2 document's typed
    -- frozen media map.  v1/legacy snapshots keep their existing
    -- honest read-model view (v1 payloads already carry media
    -- references); any version other than the supported v2 fails
    -- closed to a uniform 404 here.
    IF snapshot_row.payload->>'state_version'
           IS DISTINCT FROM 'review-snapshot/v2' THEN RETURN; END IF;

    -- (a0) Supported release versions: both the row-level versions
    --      column and the payload's captured workspace_versions must
    --      be exactly the six release pins the trusted v2 builder
    --      emits (review_worker.config + content_model constants).
    supported_pins := jsonb_build_object(
        'catalog', 'catalog-v1',
        'design_system', 'design-system/v1',
        'composition_schema', 'site-composition/v1',
        'renderer', 'renderer-v1',
        'puck', '0.20.2',
        'content_model', 'content-model/v1');
    IF jsonb_typeof(snapshot_row.versions) IS DISTINCT FROM 'object'
       OR snapshot_row.versions IS DISTINCT FROM supported_pins
       OR jsonb_typeof(snapshot_row.payload->'workspace_versions')
              IS DISTINCT FROM 'object'
       OR snapshot_row.payload->'workspace_versions'
              IS DISTINCT FROM supported_pins
    THEN RETURN; END IF;

    -- (a1) Immutable row binding: the payload's own site/workspace
    --      identity must be well-formed UUID text (pre-checked, so
    --      the comparison never raises) and equal to the trusted
    --      row columns set by the same trusted INSERT.
    IF snapshot_row.payload->>'site_id'
           !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
       OR snapshot_row.payload->>'site_id'
              IS DISTINCT FROM snapshot_row.site_id::text
       OR snapshot_row.payload->>'workspace_id'
           !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
       OR snapshot_row.payload->>'workspace_id'
              IS DISTINCT FROM snapshot_row.workspace_id::text
    THEN RETURN; END IF;

    IF NOT EXISTS (
        SELECT 1 FROM control.platform_administrator AS administrator
        WHERE administrator.user_account_id = user_id
    ) AND NOT EXISTS (
        SELECT 1 FROM control.slaif_effective_human_membership(
            user_id, snapshot_row.site_id
        )
    ) THEN RETURN; END IF;

    -- (a) Trusted captured site facts from the v2 payload: the media
    --     gate only serves snapshots whose frozen site block is a
    --     supported catalog and a supported site state.
    site_profile := snapshot_row.payload->'site';
    IF jsonb_typeof(site_profile) IS DISTINCT FROM 'object'
       OR site_profile->>'component_catalog_version'
              IS DISTINCT FROM 'catalog-v1'
       OR (site_profile->>'status' IS DISTINCT FROM 'ACTIVE'
           AND site_profile->>'status' IS DISTINCT FROM 'ARCHIVED')
       OR jsonb_typeof(site_profile->'content_model_revision')
              IS DISTINCT FROM 'number'
       OR (site_profile->'content_model_revision')::numeric
              <> floor((site_profile->'content_model_revision')::numeric)
       OR (site_profile->'content_model_revision')::numeric < 0
    THEN RETURN; END IF;

    -- (b) The stored frozen descriptor: exact five-key shape, exact
    --     id match, and the actual 068 producer/storage contract:
    --     a registered mime class (PNG/JPEG/PDF), a sha256-hex
    --     content_hash, a media_public_status enum value, and a
    --     positive integer-valued size inside the bigint range.
    --     Every malformed shape is an empty result, never an error:
    --     the size is pre-checked as plain digits so the numeric
    --     cast cannot overflow or raise.
    entry := snapshot_row.payload->'media'->p_media_id::text;
    IF jsonb_typeof(entry) IS DISTINCT FROM 'object'
       OR NOT (entry ?& array[
            'id','mime_type','size_bytes','content_hash','public_status'])
       OR (SELECT count(*) FROM jsonb_object_keys(entry)) <> 5
       OR entry->>'id' IS DISTINCT FROM p_media_id::text
       OR jsonb_typeof(entry->'mime_type') IS DISTINCT FROM 'string'
       OR jsonb_typeof(entry->'content_hash') IS DISTINCT FROM 'string'
       OR jsonb_typeof(entry->'public_status') IS DISTINCT FROM 'string'
       OR entry->>'mime_type'
              NOT IN ('image/png', 'image/jpeg', 'application/pdf')
       OR entry->>'content_hash' !~ '^[0-9a-f]{64}$'
       OR entry->>'public_status' NOT IN ('private', 'public')
       OR jsonb_typeof(entry->'size_bytes') IS DISTINCT FROM 'number'
       OR entry->>'size_bytes' !~ '^[0-9]{1,19}$'
       OR (entry->>'size_bytes')::numeric < 1
       OR (entry->>'size_bytes')::numeric > 9223372036854775807
    THEN RETURN; END IF;

    -- (c) Row-level immutable binding: the row's stored media
    --     references must contain exactly one entry for this media id
    --     with the exact five-key reference shape, and its four
    --     shared fields must equal the descriptor's.
    IF jsonb_typeof(snapshot_row.media_references)
           IS DISTINCT FROM 'array' THEN RETURN; END IF;
    SELECT count(*) INTO reference_matches
    FROM jsonb_array_elements(snapshot_row.media_references)
    WHERE value->>'id' = p_media_id::text;
    IF reference_matches <> 1 THEN RETURN; END IF;
    SELECT value INTO reference
    FROM jsonb_array_elements(snapshot_row.media_references)
    WHERE value->>'id' = p_media_id::text;
    IF reference IS NULL
       OR NOT (reference ?& array[
            'id','mime_type','size_bytes','content_hash','public_status'])
       OR (SELECT count(*) FROM jsonb_object_keys(reference)) <> 5
       OR reference->'mime_type' IS DISTINCT FROM entry->'mime_type'
       OR reference->'size_bytes' IS DISTINCT FROM entry->'size_bytes'
       OR reference->'content_hash' IS DISTINCT FROM entry->'content_hash'
       OR reference->'public_status'
              IS DISTINCT FROM entry->'public_status'
    THEN RETURN; END IF;

    -- (d) Retained inventory identity: the full capture includes
    --     every site media_asset row, so the inventory must carry
    --     exactly one row for this id; that row must be bound to
    --     the snapshot site, agree field-for-field with the
    --     descriptor, and carry the store's canonical
    --     sha256/{h[0:2]}/{h[2:4]}/{h} storage key.
    IF jsonb_typeof(snapshot_row.payload->'media_inventory')
           IS DISTINCT FROM 'array' THEN RETURN; END IF;
    SELECT count(*) INTO inventory_matches
    FROM jsonb_array_elements(snapshot_row.payload->'media_inventory')
    WHERE value->>'id' = p_media_id::text;
    IF inventory_matches <> 1 THEN RETURN; END IF;
    SELECT value INTO inventory_row
    FROM jsonb_array_elements(snapshot_row.payload->'media_inventory')
    WHERE value->>'id' = p_media_id::text;
    -- The store's canonical key from the descriptor's (already
    -- validated) sha256-hex hash.  A plain variable carries the hash
    -- into the concatenation: in PL/pgSQL a trailing
    -- entry->>'content_hash' in a || chain would re-group onto the
    -- whole left operand (->> shares || precedence in the PL
    -- parser), which is exactly what must not happen here.
    hash_text := entry->>'content_hash';
    expected_storage_key := 'sha256/'
        || substring(hash_text from 1 for 2) || '/'
        || substring(hash_text from 3 for 2) || '/'
        || hash_text;
    IF inventory_row IS NULL
       OR inventory_row->>'site_id'
              IS DISTINCT FROM snapshot_row.site_id::text
       OR inventory_row->'mime_type' IS DISTINCT FROM entry->'mime_type'
       OR inventory_row->'size_bytes' IS DISTINCT FROM entry->'size_bytes'
       OR inventory_row->'content_hash' IS DISTINCT FROM entry->'content_hash'
       OR inventory_row->'public_status'
              IS DISTINCT FROM entry->'public_status'
       OR inventory_row->>'storage_key'
              IS DISTINCT FROM expected_storage_key
    THEN RETURN; END IF;

    RETURN QUERY SELECT snapshot_row.site_id,
        entry->>'content_hash',
        (entry->>'size_bytes')::bigint,
        entry->>'mime_type';
END;
$fn$
"""

_MEDIA_PREVIEW_READ_SQL = r"""
CREATE FUNCTION control.slaif_media_preview_read(
    p_public_id text, p_secret_digest bytea,
    p_site_id uuid, p_workspace_id uuid, p_media_id uuid,
    p_idle_seconds integer, p_touch_interval_seconds integer,
    p_recent_auth_seconds integer
) RETURNS TABLE (
    id uuid, site_id uuid, uploaded_by uuid, filename text,
    mime_type text, size_bytes bigint, content_hash text,
    storage_key text, alt_text text, metadata jsonb,
    created_at timestamptz, updated_at timestamptz,
    public_status content.media_public_status, published_at timestamptz
) LANGUAGE plpgsql SECURITY DEFINER VOLATILE
SET search_path = pg_catalog AS $fn$
DECLARE
    authorized boolean;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM control.slaif_render_preview_authorize_internal(
            p_public_id, p_secret_digest, p_workspace_id, p_site_id,
            p_idle_seconds, p_touch_interval_seconds,
            p_recent_auth_seconds, false
        )
    ) INTO authorized;
    IF NOT authorized THEN RETURN; END IF;

    -- The read happens in the authorized workspace's COW context:
    -- pending (not-yet-published) rows are visible there; base rows
    -- are always visible.  Transaction-scoped; no session touch.
    PERFORM set_config('app.session_id', p_workspace_id::text, true);
    RETURN QUERY SELECT media_asset.*
    FROM content.media_asset AS media_asset
    WHERE media_asset.id = p_media_id
      AND media_asset.site_id = p_site_id;
END;
$fn$
"""

_BINDING_COLUMN_SQL = """
ALTER TABLE control.browser_run
    ADD COLUMN preview_credential_digest text,
    ADD COLUMN preview_credential_nonce_digest text,
    ADD COLUMN preview_credential_expires_at timestamptz,
    ADD COLUMN preview_credential_attempt integer,
    ADD CONSTRAINT browser_run_preview_binding_shape CHECK (
        (
            preview_credential_digest IS NULL
            AND preview_credential_nonce_digest IS NULL
            AND preview_credential_expires_at IS NULL
            AND preview_credential_attempt IS NULL
        )
        OR (
            preview_credential_digest IS NOT NULL
            AND preview_credential_digest ~ '^[0-9a-f]{64}$'
            AND preview_credential_nonce_digest IS NOT NULL
            AND preview_credential_nonce_digest ~ '^[0-9a-f]{64}$'
            AND preview_credential_expires_at IS NOT NULL
            AND preview_credential_attempt IS NOT NULL
            AND preview_credential_attempt >= 0
        )
    )
"""

# The partial unique index is a SEPARATE statement: the alembic
# SQLAlchemy/asyncpg dialect executes one prepared statement per
# op.execute, so a combined "ALTER TABLE ...; CREATE INDEX ..." string
# is a syntax failure on the product upgrade path.
_BINDING_INDEX_SQL = """
CREATE UNIQUE INDEX browser_run_preview_binding_digest
    ON control.browser_run (preview_credential_digest)
    WHERE preview_credential_digest IS NOT NULL
"""

_BINDING_REGISTER_SQL = r"""
CREATE FUNCTION control.slaif_browser_preview_binding_register(
    p_run_id uuid, p_credential_digest text, p_expires_at timestamptz
) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER VOLATILE
SET search_path = pg_catalog AS $fn$
DECLARE
    first_binding integer;
    replay_ok boolean;
BEGIN
    IF p_credential_digest IS NULL
        OR p_credential_digest !~ '^[0-9a-f]{64}$'
    THEN
        RAISE EXCEPTION 'preview credential digest is malformed'
            USING ERRCODE = 'P0001';
    END IF;
    IF p_expires_at IS NULL
        OR p_expires_at <= CURRENT_TIMESTAMP
        OR p_expires_at > CURRENT_TIMESTAMP + interval '600 seconds'
    THEN
        RAISE EXCEPTION 'preview credential lifetime is invalid'
            USING ERRCODE = 'P0001';
    END IF;

    -- First binding of this run: the 036 consume (p_consume =
    -- true) stored the original nonce in the SAME transaction
    -- (Render holds the registrar grant and calls this before
    -- committing the consume).  The binding records the original
    -- digest, original nonce, verifier-checked expiry and current
    -- attempt as immutable run facts; a failed or rolled-back
    -- consume leaves no usable binding.
    UPDATE control.browser_run AS run
    SET preview_credential_digest = p_credential_digest,
        preview_credential_nonce_digest = run.preview_nonce_digest,
        preview_credential_expires_at = p_expires_at,
        preview_credential_attempt = run.attempt_count
    WHERE run.id = p_run_id
      AND run.preview_token_used_at IS NOT NULL
      AND run.preview_nonce_digest IS NOT NULL
      AND run.preview_credential_digest IS NULL;
    GET DIAGNOSTICS first_binding = ROW_COUNT;
    IF first_binding > 0 THEN
        RETURN true;
    END IF;

    -- Idempotent replay of the exact original binding (same
    -- digest, same verified expiry, unrotated attempt): the
    -- immutable facts are left untouched, never rewritten or
    -- extended.  A rotated attempt, a different expiry or a
    -- foreign digest is refused, never adopted.
    SELECT EXISTS (
        SELECT 1 FROM control.browser_run AS run
        WHERE run.id = p_run_id
          AND run.preview_credential_digest = p_credential_digest
          AND run.preview_credential_expires_at = p_expires_at
          AND run.preview_credential_attempt = run.attempt_count
          AND run.preview_credential_nonce_digest
              = run.preview_nonce_digest
    ) INTO replay_ok;
    IF replay_ok THEN
        RETURN true;
    END IF;

    RAISE EXCEPTION 'preview run binding is not eligible'
        USING ERRCODE = 'P0002';
END;
$fn$
"""

_BOUND_PREVIEW_READ_SQL = r"""
CREATE FUNCTION control.slaif_media_bound_preview_read(
    p_credential_digest text, p_media_id uuid
) RETURNS TABLE (
    id uuid, site_id uuid, uploaded_by uuid, filename text,
    mime_type text, size_bytes bigint, content_hash text,
    storage_key text, alt_text text, metadata jsonb,
    created_at timestamptz, updated_at timestamptz,
    public_status content.media_public_status, published_at timestamptz
) LANGUAGE plpgsql SECURITY DEFINER VOLATILE
SET search_path = pg_catalog AS $fn$
DECLARE
    bound_run control.browser_run%ROWTYPE;
    authorized record;
BEGIN
    -- 083/5 confined run-bound private byte read BEFORE freeze.
    -- The media service receives only the existing run
    -- credential and presents its sha256 digest; nothing else is
    -- client-selected.  The media service receives the existing
    -- run credential only in order to hash it (sha256); it never
    -- receives the signing key, trusted caller claims or logs the
    -- raw token.  The trusted binding row (recorded atomically
    -- with the 036 consume at the Render verifier boundary;
    -- EXECUTE on the registrar is held by slaif_preview_reader
    -- only) contributes the run and the ORIGINAL consumed nonce;
    -- every other fact is derived from stored rows.
    IF p_credential_digest IS NULL
        OR p_credential_digest !~ '^[0-9a-f]{64}$'
    THEN
        RETURN;
    END IF;

    -- Indexed unique binding lookup (partial unique index on the
    -- non-NULL digest; explicit non-NULL shape: a partial or
    -- malformed binding can never authorize).
    SELECT run.*
    INTO bound_run
    FROM control.browser_run AS run
    WHERE run.preview_credential_digest = p_credential_digest
      AND run.preview_credential_nonce_digest IS NOT NULL
      AND run.preview_credential_expires_at IS NOT NULL
      AND run.preview_credential_attempt IS NOT NULL;
    IF NOT FOUND THEN RETURN; END IF;

    -- The actual 036 no-consume authorizer, called with the
    -- ORIGINAL binding nonce (not a fresh row re-read): shared
    -- advisory 280 before the run row lock, the full
    -- run/capability/workspace/site binding predicates (state,
    -- expiries, scopes, ACTIVE, delegator), the stored-nonce
    -- recheck and FOR UPDATE OF run.  After this returns, the
    -- run row is locked by this transaction.
    SELECT *
    INTO authorized
    FROM control.slaif_render_browser_preview_authorize(
        bound_run.capability_id, bound_run.site_id,
        bound_run.workspace_id, bound_run.id, bound_run.route,
        bound_run.target, bound_run.evidence,
        bound_run.reserved_artifact_bytes,
        bound_run.max_duration_seconds,
        bound_run.preview_credential_nonce_digest, false
    );
    IF NOT FOUND THEN RETURN; END IF;

    -- Post-lock recheck of the full immutable binding
    -- invariants on the now-locked row: an attempt rotation
    -- (035 retry), a credential-expiry lapse or any binding
    -- drift that
    -- happened before the lock is refused here, so the
    -- digest/expiry/attempt/nonce the lookup used are exactly
    -- the row's under the lock.
    SELECT run.*
    INTO bound_run
    FROM control.browser_run AS run
    WHERE run.id = bound_run.id;
    IF NOT FOUND THEN RETURN; END IF;
    IF bound_run.preview_credential_digest
           IS DISTINCT FROM p_credential_digest
       OR bound_run.preview_credential_nonce_digest IS NULL
       OR bound_run.preview_credential_expires_at IS NULL
       OR bound_run.preview_credential_expires_at <= CURRENT_TIMESTAMP
       OR bound_run.preview_credential_attempt IS NULL
       OR bound_run.attempt_count
           <> bound_run.preview_credential_attempt
    THEN
        RETURN;
    END IF;

    -- Same overlay rule as the human preview read: the bound
    -- run's authorized workspace is the Agent workspace; pending
    -- (not-yet-published) media is visible there, base rows
    -- always.  Transaction-scoped; no session touch.
    PERFORM set_config('app.session_id', bound_run.workspace_id::text, true);
    RETURN QUERY SELECT media_asset.*
    FROM content.media_asset AS media_asset
    WHERE media_asset.id = p_media_id
      AND media_asset.site_id = authorized.site_id;
END;
$fn$
"""
