# OAP Work Order — 078-q: close trusted theme boundary defects

- Objective078; increment078/2; round078-q; AMEND_EXISTING_PR.
- Existing [PR #79](https://github.com/ulfe-lmi/slaif-agent-site/pull/79);
  branch `oap/078-2-site-theme-tokens`; base `main`.
- Verified main/base `3cae3d6cef2a92e7068856d21bc9a47b8190c22e`.
- Starting report head `e89ff37ee3debc69d9c780d746ec4b098ceb4318`;
  exact implementation/report parent `b89ef7bce4026db8377c782e2c6bfa13ce5cc8c1`.
- One existing theme PR only. PR77 is merged/closed; no new PR or agent.

## Scope and evidence correction

Read `oap/audits/078-2-theme-increment-review.md` completely. Its D1–D4 and
PostgreSQL15 failure are this round's finite target. The substantial 078-p
implementation exists, but COMPLETE overcredits general tests and misses
explicit changed/no-effect authority, trusted validation and migration evidence.
Preserve that report; correct its claims through this new report and current
ledgers, not historical edits. Do not reproduce the no-op/PARTIAL pathology:
implement the assigned repairs and actual focused tests before returning unless
a concrete external/technical blocker genuinely prevents them.

This round does NOT repair or add renderer/theme UI behavior: V1–V2 and Firefox
closure are deliberately reserved for the next bounded rendering/proof round.
PR79 remains incomplete even if this database slice and its tests pass.

## Required production repairs

1. Migration065's trusted theme validator must fail closed for SQL NULL, JSON
   null, absent/unknown keys, wrong scalar/group types, arrays, malformed enum,
   raw executable/style/font values in every group. Do not rely on Python.
   Strategic direct-runtime probe persisted `{"preset":null}`, version2.
   Explicitly handle SQL three-valued logic; validate types before jsonb_each.
   HTTP and SQL must yield the intended stable error and zero mutation residue.
2. Implement 078-p's exact no-effect rule: a valid current-version unchanged
   PATCH is allowed with bound `theme:read` and no write scope, yields200 and
   no mutation quota/audit/COW/version change. Actual changes require exact
   `theme-tokens:write`, not theme-global substitution. Do change classification
   and authority under the trusted transaction lock; no Python pre-read race
   or caller p_no_effect flag may authorize changed data. Preserve idempotent
   replay/mismatch and stale-version behavior. Route policy/OpenAPI must express
   changed-value conditional authority exactly and remain bidirectionally checked.
3. Preserve ALL pre-theme trusted resource-helper validation. Compare the
   actual main064 `control.slaif_agent_resource_constraints` definition from
   migration060 and subsequent replacements, not just its return columns.
   Add theme constraints without deleting existing type/array/bounds/route/
   lifecycle checks. Downgrade must restore exact pre065 function definitions,
   signature, ownership, ACLs and volatility for every replaced helper/wrapper
   and semantic completion function, not the current abbreviated reconstruction.
   Preserve valid state and fail safely on incompatible/pending COW; no CASCADE
   deletion of unknown dependencies. Do not change merged migrations060–064.
   Correct the unmerged theme migration or add the minimum repair migration
   with fresh/upgrade/downgrade evidence as appropriate; no unrelated migration.
4. Keep deterministic transaction locking and shared lifecycle ordering exact
   for theme changed/no-effect paths, including first materialization and
   concurrent existing-row updates. Preserve server-owned context and canonical,
   workspace, capability, quota, idempotency and audit isolation.

## Focused proof that must exist and run

Use real PostgreSQL and existing public Agent fixtures plus direct
`slaif_agent_runtime` calls; no owner mutation as a substitute for product behavior.
Owner connections may seed fixtures and observe invariants, not execute outcomes.

- D1 regression for each token/group: invalid null/wrong type rejected at both
  public HTTP and trusted SQL; verify no row/version/quota/audit/idempotency/COW
  residue. Include direct helper privilege/foreign-site denial and p_no_effect
  forgery. Strategic reproduction is
  `/tmp/slaif-078-theme-review-FDKCkn/probe.py`; implement durable tests.
- Read-only current-version unchanged PATCH200, missing-read denial, changed
  L1/L2/read-only403, correctly narrowed L3 success, unrelated-L4 substitution
  denial, exact replay/mismatch/stale results and no-effect accounting. Do not
  require write merely because an unchanged field was supplied.
- Theme-specific invalid/malformed constraints, scope/resource, foreign
  site/workspace, expired/revoked/frozen/non-active and exhausted-quota negative
  cases. Compare actual before/after data and durable operation/audit state.
- Read purity for existing and absent themes: count actual visible/base/pending
  theme rows, compare timestamps/version/watermark/audit/quota as relevant;
  bare `SELECT count(*)` with no FROM is not a table-state assertion.
- Deterministic first-materialization and existing-row same-version races:
  prove both intended transactions reach the relevant DB wait/barrier, then
  one winner/one409/one durable effect. `asyncio.gather` alone is not proof.
  Cancellation after meaningful transaction progress rolls back everything;
  reconnect/restart and independent workspace/site checks prove isolation.
- Data-bearing064→theme→064→theme proof captures fresh064 pg_get_functiondef,
  signatures, owners/ACLs/volatility and compares exact restoration, including
  common resource helper and legacy theme wrappers. Invalid/pending state must
  reject without data loss. Keep foundation/product privilege checks intact.

Put theme-specific tests in a dedicated file if useful, without mechanically
refactoring the component suite. Wire actual theme PostgreSQL tests into CI;
the current `-k component` selection does not run them. Run the focused tests
before broad gates and retain concrete assertions/commands/results.

## Existing PostgreSQL CI failure

Run34367041990, job102518332029 fails
`test_agent_component_concurrent_creates_before_anchor_are_serialized`:
`expected 2 structural lock waiters, got 1`. Inspect actual connection/task/
lock readiness; helper `_wait_for_page_structure_waiters` currently counts
global advisory waiters for a fixed500iterations. Repair the concrete test or
production defect minimally; require exact intended blockers/participants and
a bounded readiness deadline, not reduced waiter count, timing sleeps as proof,
skips or blind reruns until green. Preserve component concurrency invariants.

The known Firefox browser-response failure is deferred to the next renderer
round. Do not suppress it or claim all PR CI green if it still fails. This is a
concrete tracked unfinished criterion, not permission to return before D1–D4
repairs and their focused proof exist. Other unexpected in-scope failures may
be repaired within this turn; report exact external blockers honestly.

## Safety, reviewability, publication

No global regions/header-footer/page-style/catalog/media/MCP/exact-workspace
Puck/lifecycle/publication, dependency/security exception, lint/scanner weakening,
or unrelated refactor. Preserve Next16.3.3 and approved scope. PR is55files with
generated/test artifacts; report production/migration/test/generated/docs counts
and substantive line changes separately. Do not expand the semantic merge unit.
Routine safe DB/tools/setup belongs to existing coder's passwordless-sudo VM.

Commit unchanged order, strategic audit record and active078-q. Update current
truth to mark this slice honestly and V1–V2/Firefox still outstanding; do not
claim full theme acceptance. Push only PR79 and observe checks. Report each
criterion using a named actual test and exercised boundary, not inherited suite
totals. State precisely what remains unproven. Do not amend old reports/orders.
Publish `oap/reports/078-q-theme-trusted-boundary-repairs.md` as report-only SELF
child of the literal pushed implementation SHA with PR/branch/base/head,
files/size, exact tests/CI results, migration/authority proof and remaining scope.
Lint Markdown before publication. Never merge/auto-merge. Signal exact FIFO OK
after publication, then wait for strategic review.
