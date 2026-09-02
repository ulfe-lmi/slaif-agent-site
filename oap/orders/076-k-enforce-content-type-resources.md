# OAP Work Order — 076-k

## Objective and verified state

Amend only PR #72 / `oap/076-agent-model-content-semantics`; no new PR/merge.
Required remote head is 076-j report
`9071d335a1518982753d5feea6cfab7a7a9fc68d`, sole parent implementation
`13f9f4a07746a7ddf7a6e8f92743db5c0ea4ebcd`; base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. The unmerged 044 helper is typed,
site/COW-bound, PUBLIC/runtime-revoked, and now checks coarse JSON shapes, but
has no executable proof and no wrapper consumer. This round completes only the
three content-type wrappers and their helper/resource/concurrency proof; field
wrappers and audit stay later.

## Production change

In revision 044, replace the existing public signatures of
`content.slaif_agent_content_type_create`, `_update`, and `_delete` without
changing arguments/return shapes.

- Each wrapper calls the owner-only typed resource helper after existing trusted
  COW/site validation. Create enforces `allowed_type_keys`; update/delete enforce
  `allowed_type_ids` and the persisted type key against `allowed_type_keys` when
  either allowlist is present. Delete also requires `delete_enabled` when that
  policy is explicitly false. Missing constraints remain unrestricted within
  scopes/quotas; malformed values fail closed before DML.
- Type create obtains a deterministic transaction advisory lock keyed from the
  trusted `app.session_id` plus a fixed content-type namespace, then counts the
  ACTIVE content types visible through the current COW overlay; reject when
  `max_content_types` is reached. Do not read base/change tables as owner or
  count another workspace. Update/delete preserve definition-version,
  dependency, validation, site and tombstone semantics.
- Complete helper element/length/integer/bound validation where tests expose
  gaps. Revoke PUBLIC on all three replacements; grant only the exact pre-044
  runtime principals. Runtime cannot call the helper or read constraints/base/
  change/audit. Downgrade restores exact pre-044 type wrapper SQL/grants and
  removes the helper.

## Focused executable proof

Add focused cases in a dedicated new integration module or a clearly isolated
section of `test_agent_mutations.py`, using its existing real DB `_seed`, COW,
Agent app and role fixtures. Prove through public HTTP and direct wrapper calls:
allowed key/ID success; disallowed create/update/delete denial with no residue;
delete-disabled denial; exact sequential maximum; tombstoned type frees a
visible slot; malformed helper values fail stably; helper/runtime privilege
denial; wrong site/workspace denial; and two independent connections racing one
remaining slot produce exactly one success, one denial, exact final count and
no residue. Also prove downgrade→upgrade restores signatures/grants.

Run Ruff on changed files and only the focused type/helper integration cases on
PostgreSQL 16 plus migration roundtrip. Use passwordless sudo/local DB and fix
focused failures autonomously. Do not run broad suites or rerun CI jobs; push
the completed slice once and inspect initial checks. Binary done is all three
type wrappers plus the public/direct/security/race proof; a helper-only change
or no-test PARTIAL is failure absent a genuine external database/tool outage.

## Non-goals and report

No field wrapper, audit/quota coupling, OpenAPI artifact, new entity/API,
dependencies, CI/docs/governance, prior transcript edit, broad refactor or
production action. Publish exactly
`oap/reports/076-k-enforce-content-type-resources.md` as report-only child of a
literal 40-hex implementation SHA, listing exact PR/start/head, 044 functions/
grants/locks/downgrade, files, commands/results/race counts, skips/pending CI,
no extra PR/no merge/no secrets, and `Report publication commit: SELF`; no
post-report push.
