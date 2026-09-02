# OAP Work Order — 076-j

## Objective and verified state

Amend only PR #72 / `oap/076-agent-model-content-semantics`; no new PR/merge.
Required remote head is 076-i report
`20f07bd90a312f65b5d46d7109913c2b4e549117`, sole parent implementation
`334b35ea536c83ce2b9b1d466b078c5256084a54`; base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. Revision 044 now has typed
`control.slaif_agent_resource_constraints(uuid)` and explicit PUBLIC/runtime
revocation, but 076-i added no dedicated test and the SQL still relies on casts
instead of explicit complete shape/bound validation. Close only that evidence
and validation gap; wrappers remain out of scope.

## Tests-first required work

Add `services/backend/tests/integration/test_agent_resource_constraints.py`
using the repository's real disposable PostgreSQL/migration/role fixtures.
Before changing SQL, encode and run tests for all of these cases:

- `{}` returns empty allowlists and NULL optional limits/policy;
- a fully populated valid six-key object returns exact UUID/text arrays,
  nonnegative maxima and boolean;
- missing, empty, malformed or non-UUID session and operation settings fail
  with the stable COW-context error;
- mismatched site, unknown/expired/non-ACTIVE workspace, inactive site and
  inactive delegator/account fail closed;
- non-object constraints, unknown keys, non-array allowlists, invalid UUID,
  empty/non-string/overlong type key, wrong scalar types, boolean-as-integer,
  negative integer and values above an explicit bounded ceiling all fail with
  the stable invalid-constraints error rather than leaking a raw cast error;
- `has_function_privilege` proves PUBLIC, agent, Editor, Control, Render and
  other runtime roles cannot EXECUTE the helper, and runtime cannot SELECT the
  stored constraint column; the migration owner test path can invoke it only
  under valid trusted COW context; and
- downgrade removes the signature/grant and re-upgrade restores the same tested
  contract without residue.

Then make the minimum in-place changes to unmerged revision 044 needed to pass
those tests: explicitly validate JSON types, lengths, UUIDs, integer-ness and
bounds before conversion; preserve typed return and site/COW binding; do not
grant the helper. Use one documented numeric ceiling consistent with issuance
validation and existing product bounds, not an arbitrary unbounded cast.

Run Ruff for the migration/test and the dedicated module on PostgreSQL 16,
including its migration roundtrip. Use passwordless sudo/local DB as needed and
fix failures autonomously. Do not run broad suites or rerun GitHub jobs; push
once and report their initial state. Binary done is the dedicated test module
passing every listed case and the helper passing it; a partial without the test
module is failure absent a genuine external DB/tool outage.

## Non-goals and report

No wrapper replacement/locks/counting, HTTP, audit, OpenAPI, entities,
dependencies, CI workflow, docs/governance, prior transcript edits, or broad
refactor. Publish exactly `oap/reports/076-j-prove-resource-helper.md` as the
report-only child of a literal 40-hex implementation SHA, with exact PR/start/
head, SQL/test files, commands and exact results, migration/role proof, skips/
pending CI, no extra PR/no merge/no secrets, and `Report publication commit:
SELF`; no post-report push.
