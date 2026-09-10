# OAP Execution Report — 078-x: page-style proof closure

## Identity and status

- Objective: 078; increment: 078/4; round: 078-x.
- Mode: `AMEND_EXISTING_PR`.
- Status: `COMPLETE` for the bounded 078-x execution scope.
- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: [#81](https://github.com/ulfe-lmi/slaif-agent-site/pull/81), open; no merge or auto-merge performed.
- Branch: `oap/078-4-page-style-overrides`.
- Verified base: `fe31c9f30a7797d0916ad7f8fb56344bc61526f3`.
- Starting remote head: `a65d184674d34261be8cc681aaccbd8f3edeb76d`.
- Pushed implementation SHA: `d2bc4fbee42fb78bf92f8c10ff93bc4bda681e67`.
- Implementation parent: `a65d184674d34261be8cc681aaccbd8f3edeb76d`.
- Report-only parent: `d2bc4fbee42fb78bf92f8c10ff93bc4bda681e67`.
- Report publication commit: `SELF`.
- Active bytes committed unchanged: ASCII `078-x\n`.
- Active SHA-256: `e03d6f3025185b40396cac65ec8f345997e3d157a4d70c380a3c5e6918275166`.
- Exact 078-x order SHA-256:
  `c4deabab709dd7c13307230b6b21aa3eac0406305564a037b93af9ca96b65319`.

Objective 078 remains `PARTIAL` at the numeric-objective level. Strategy alone
reviews, accepts, and merges the bounded increment. This report’s
`COMPLETE` status means the activated 078-x proof-closure order was executed
and delivered; it does not mean accepted or merged.

## Decision and scope

The 078-w report’s remaining claims were insufficient because its migration
test began at head 066 rather than a fresh 065 baseline, cancellation happened
before style DML, structural races did not exercise both operation orderings or
winner state, and several authority/visual/human assertions were indirect or
missing. The x order required those exact proof repairs without reimplementing
the passing page-style data plane or expanding Objective 078.

The x implementation preserves the 078-v and 078-w orders/reports and adds only
the required proof and restoration corrections: exact 065 downgrade source
restoration, explicit null reset rejection, fresh migration/audit tests,
post-DML cancellation rollback, complete resource and raw-authority tests,
both lock orderings, concurrent theme/reset serialization, exact accounting
identity, human mixed reset/update and denial evidence, and current truth.

## Authoritative GitHub state

- Before report publication, PR #81 read back open with implementation head
  `d2bc4fbee42fb78bf92f8c10ff93bc4bda681e67` and the verified base above.
- The PR description was updated and read back to identify 078-x, its exact
  remaining proof gaps, implementation lineage, bounded scope, and no-merge
  rule.
- Final x pull-request workflow `34518406988` was green on the implementation
  head, and CodeQL workflow `34518406975` was green. The report-only commit is
  the final head and must retain equivalent green required checks after its
  publication.

### Required remote checks

The x implementation workflow completed successfully for every required check:

- Repository policy — `pass`.
- Detect supported languages — `pass`.
- Node contracts — `pass`.
- Python 3.12 quality and package — `pass`.
- Python 3.13 quality and package — `pass`.
- Python 3.14 quality and package — `pass`.
- Foundation PostgreSQL 14 — `pass`.
- Foundation PostgreSQL 15 — `pass`.
- Foundation PostgreSQL 16 — `pass`.
- Foundation PostgreSQL 17 — `pass`.
- Foundation PostgreSQL 18 — `pass`.
- Compose and edge packaging — `pass`.
- Supply-chain evidence — `pass`.
- Markdown — `pass`.
- Mermaid — `pass`.
- Dependency review — `pass`.
- CodeQL — `pass`.
- Analyze (actions) — `pass`.
- Analyze (python) — `pass`.
- Analyze (javascript-typescript) — `pass`.

GitHub remains authoritative if a later check or branch-head state changes.

## Changes delivered

### Migration and trusted authority

- `066_001_page_style_overrides.py` now emits the exact 065 semantic
  completion, no-effect completion, and audit-constraint restoration strings
  on downgrade, while retaining the 066 page-style contract. Null reset
  entries are rejected as `PAGE_STYLE_RESET_INVALID`.
- The prior x resource/version/overlap/theme-lock repairs remain intact.

### Focused verification

- `test_agent_page_style.py` now contains named tests for fresh 065→066→065→066
  restoration, audit-only downgrade refusal, cancellation after real style DML,
  exact audit/idempotency identity, raw-equal write authority, denied family
  and reset destinations, route/root/locale/depth bounds, both structural race
  orderings with winner state, and concurrent theme-change/reset serialization.
- `test_human_editor_production_http.py` now proves crafted viewer Editor style
  denial and human mixed typography update/reset through the actual Editor API.
- `tests/e2e/governance.spec.ts` exercises the human page-style controls with a
  same-group update/reset and confirms persistence across Puck save/move/reload.
- Existing browser/Compose page-style evidence remains in place and is rerun
  on the x head; no fake DOM injection or ASGI-client restart is claimed as a
  process restart.
- Current README, testing guide, increment ledger, MVP progress, and contract
  audit identify 078-x as active and preserve earlier artifacts as immutable.

The cumulative PR from verified merged base is 51 files, approximately
+5,523/−115. This growth is categorized as the existing page-style production
and migration boundary plus its required focused verification, generated or
current docs/OAP truth; no new semantic family was added. No global regions,
catalog expansion, media/MCP, lifecycle/publication, dependency, or unrelated
cleanup scope entered PR #81.

## Criterion-by-criterion evidence

1. **Fresh migration baseline and safe downgrade.**
   `test_page_style_fresh_065_baseline_restores_exactly_through_066` starts on
   the fixture’s base, upgrades to 065 before any 066 application, inserts a
   real legacy site/page, captures function definitions plus owner/ACL/
   volatility/configuration and the audit constraint, applies 066, downgrades
   to 065, and compares every captured value exactly. It then re-upgrades 066,
   reconciles COW, and verifies legacy fields and empty page-style defaults.
   `test_page_style_downgrade_rejects_style_audit_without_data_loss` separately
   proves an empty-style page with style audit history is rejected with
   `PAGE_STYLE_MIGRATION_AUDIT_PRESENT`; the existing data-bearing and
   pending-COW guards remain covered.

2. **Post-DML cancellation.**
   `test_page_style_cancellation_after_dml_rolls_back_everything` calls the
   trusted Agent SQL wrapper directly inside a real COW session, observes the
   returned row after style DML, blocks before transaction exit, cancels the
   actual task, and verifies raw state/version, mutation quota, idempotency,
   semantic audit, and COW operations equal the baseline. A public Agent retry
   then succeeds at the original version.

3. **Both structural lock orderings.**
   `test_page_style_structural_races_serialize_with_page_operations` uses the
   PostgreSQL advisory lock table, never a sleep, and proves one winner for
   style-v-style plus style-first and page-first update, move, and delete
   races. It asserts resulting title, parent, deleted visibility, raw style,
   and loser response rather than only sorted status codes.

4. **Theme/style serialization.**
   `test_page_style_reset_serializes_with_concurrent_theme_change` queues a
   real Agent theme PATCH before a page-style reset behind the 995 theme lock,
   then asserts both successful results, the changed site theme, empty raw page
   overrides, and the reset response’s effective `meadow` destination. The
   lifecycle/theme barrier test separately proves the 280 and 995 waits.

5. **Raw-state authority.**
   `test_page_style_raw_changes_require_write_when_pixels_are_equal` proves a
   read-only set-to-current-inherited request is denied, a read-only reset of an
   explicit value equal to the inherited value is denied, and a raw no-effect
   reset remains read-authorized. The same file proves denied typography-family
   selection, denied reset destination, direct narrowed-resource/no-effect
   denial, forbidden human-wrapper EXECUTE, and stable trusted-SQL null,
   duplicate, and unknown reset errors.

6. **Complete page resource bounds.**
   The repaired visibility test covers excluded route-prefix pages, foreign
   pages/sites, locale narrowing, an allowed root and child subtree, and depth
   rejection of a grandchild. HTTP GET/PATCH and direct runtime calls fail
   closed before raw/no-effect return or mutation, with no residue.

7. **Accounting and identity.**
   `test_page_style_accounting_constraints_lifecycle_restart_and_restore`
   verifies no-effect idempotency without mutation quota/audit/COW charge,
   exactly one changed mutation/audit result, and exact capability, delegator,
   workspace, site, operation, resource, action, method, and quota identities.
   It covers quota, expired/frozen/archived/revoked GET and PATCH denial,
   restart with non-empty overrides, and unchanged state after failures.

8. **Lifecycle, isolation, and preservation.**
   The accounting test verifies page style survives Agent delete/restore,
   remains hidden while deleted, and stays isolated from another workspace and
   site/page. The focused tests retain COW rollback, version, replay, mismatch,
   stale, and no-effect semantics.

9. **Renderer and human evidence.**
   The x Compose run passed all 11 browser projects and the public Agent
   acceptance path. It exercised all nine distinguishable page-style classes
   and computed output through the same NGINX preview, retained component-local
   gap precedence, reset to inherited site-theme output, and verified restart
   readback. The human production test passed viewer denial and mixed
   same-group update/reset; governance smoke recorded the exact sequence
   `page-create,theme-update,page-style-update,page-style-update,component-add,component-add,component-move`
   with count 8.

## Exact local verification

- `uv run --frozen pytest -q services/backend/tests/integration/test_agent_page_style.py`
  — 11 passed in 1m56s.
- `uv run --frozen pytest -q services/backend/tests/integration/test_human_editor_production_http.py::test_fixed_production_logins_run_public_editor_http_chain`
  — 1 passed, including viewer denial and mixed human reset/update.
- `uv run --frozen ruff check services/backend tests/repository tools` and
  `ruff format --check` — pass.
- `uv run --frozen mypy` — no issues in 274 files.
- E2E TypeScript, Prettier, ESLint/web lint, and Markdownlint — pass.
- Prior broad x-ancestor evidence remains green: 221 backend integration tests
  and 541 unit/repository tests passed; the x order explicitly required focused
  proof closure and did not require repeating the 35-minute broad integration
  run solely by habit.
- `sh tools/compose/smoke.sh slaif007v` — `compose-smoke: OK`; all 11 browser
  projects, public Agent acceptance, human mixed-reset audit sequence, page-
  style preview/reset, media/edge, readiness, recovery, negative bootstrap,
  Apache/NGINX validation, artifact revocation, and 48 packaging tests passed.
- Exact source comparison of the 065 and 066 downgrade helper outputs reported
  `completion exact=True`, `no_effect exact=True`, and `constraint exact=True`.

## Governance and safety confirmations

- Only the unique order selected by `oap/active` was executed.
- The exact x order and active bytes were committed unchanged. Historical
  orders and reports were not edited.
- Only existing PR #81 and its branch were used. No extra PR, branch, merge,
  auto-merge, release, or acceptance action was performed.
- No production systems, production data, credentials, cookies, capabilities,
  private artifact URLs, or database locators were exposed.
- No required gate was weakened, skipped, suppressed, or replaced by a local
  result. Current remote checks were green before report publication.

## Completion condition

Objective 078/PR #81 may be declared complete only after strategy independently
confirms that the exact remote PR head is this report-only `SELF` commit,
confirms all required checks on that head remain green, reviews the preserved
078-v/078-w evidence together with the x closure, confirms scope containment,
and accepts/merges PR #81 under OAP authority. The coding agent does not merge
the PR.
