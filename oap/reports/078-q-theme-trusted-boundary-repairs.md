# OAP Coding-Agent Report — 078-q

## Work order

- Identifier: `078-q`; work-order file: `oap/orders/078-q-theme-trusted-boundary-repairs.md`; numeric objective: 078, increment 078/2.
- PR mode: `AMENDED_EXISTING_PR`.
- Existing PR: [#79](https://github.com/ulfe-lmi/slaif-agent-site/pull/79); branch `oap/078-2-site-theme-tokens`; base `main`.
- Starting remote implementation/report head: `e89ff37ee3debc69d9c780d746ec4b098ceb4318`.
- The strategy order, audit record, and `oap/active` were committed exactly as supplied; their content was not edited.

## Status

PARTIAL

## Executive summary

The finite 078-q trusted-boundary repair is implemented and verified on the
existing PR. D1 closes SQL three-valued-logic and scalar/group validation gaps;
D2 makes no-effect authority conditional on the actual trusted value change;
D3 preserves the complete pre-theme helper and exact legacy function metadata
through downgrade; and D4 adds direct PostgreSQL hostile, lifecycle, isolation,
purity, cancellation, migration, and deterministic lock-barrier evidence. The
PostgreSQL component readiness failure is also repaired with an exact lock
identity and bounded readiness deadline.

The round deliberately does not claim Objective 078 completion. V1–V2 rendering
proof and the previously observed Firefox browser-response criterion remain
reserved/deferred by the immutable order for a later bounded rendering round.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: [#79](https://github.com/ulfe-lmi/slaif-agent-site/pull/79), `OPEN`.
- Base/head: `main` / `oap/078-2-site-theme-tokens`.
- Starting remote SHA: `e89ff37ee3debc69d9c780d746ec4b098ceb4318`.
- Implementation commits pushed before report: `14b84b00c259a8210fb71871a039f86c631c5733`, `8c0b36bc50b136d027fc1f37c7b5ab9e3c8d0401`.
- Implementation head SHA: `8c0b36bc50b136d027fc1f37c7b5ab9e3c8d0401`.
- Report publication commit: `SELF`.
- Remote PR head after report publication: `SELF` (literal SHA to be derived from GitHub after publication).
- New objective PR this round: NO. Existing PR amended: YES. Merge/auto-merge performed: NO.
- No existing final `078-q` report was present before publication.

## Changes made

- Hardened migration 065 trusted theme validation with explicit object/scalar
  type checks, `IS DISTINCT FROM` handling, validation before `jsonb_each`,
  closed enum/unknown-key checks, and fail-closed theme resource arrays.
- Changed Agent theme PATCH authority to require `theme:read` for the route and
  `theme-tokens:write` only after the locked SQL comparison proves a real
  change. The caller-supplied no-effect flag cannot authorize changed data.
- Routed trusted theme resource validation through the complete owner-defined
  resource helper, preserving all pre-theme type, array, bound, route, and
  lifecycle checks.
- Preserved pre-065 resource/theme function objects in a private migration
  schema and moved them back on downgrade, retaining exact body, signature,
  owner, ACL, and volatility without `CASCADE` deletion.
- Added dedicated `test_agent_theme_boundaries.py` evidence for all four theme
  groups, direct runtime calls, no-effect accounting, resource/scope/lifecycle
  negatives, read purity, workspace/site isolation, pending-COW migration
  safety, deterministic first-materialization/existing-row races, cancellation,
  and restart.
- Repaired `_wait_for_page_structure_waiters` to identify the blocker’s exact
  granted advisory lock and wait to a bounded deadline.
- Added the focused theme test file to CI and regenerated the canonical Agent
  OpenAPI conditional-scope metadata.
- Reconciled the current OAP truth ledgers to identify 078-q as active and to
  retain V1–V2/Firefox as outstanding.

## Files changed and size

The 078-q implementation round changes 16 unique paths across its two pushed
implementation commits, with net `+1297/-165` lines:

- Runtime and migration: 4 paths, `+162/-135`; the migration itself is
  `+142/-127`.
- Tests: 4 paths, `+864/-5`.
- Generated contract: 1 path, `+15/-2`.
- CI workflow: 1 path, `+4/-0`.
- OAP governance/ledger transcript: 6 paths, `+252/-23`.

The pre-existing PR diff was 55 paths; after this continuation the cumulative
PR diff is 59 paths. No unrelated product family was added.

## Acceptance-criteria evidence

### D1 — trusted SQL validation

- `services/backend/tests/integration/test_agent_theme_boundaries.py::test_theme_invalid_values_fail_at_http_and_trusted_sql_without_residue` is a four-group parameterized matrix.
- Public HTTP rejects null nested tokens with `422`.
- Direct `slaif_agent_runtime` calls reject JSON null, wrong group/scalar type,
  unknown keys, and raw style/font-like values with stable theme errors.
- After every HTTP and direct-SQL attempt, physical base rows, pending change
  rows, row version/timestamp, mutation quota, idempotency, audit, operation
  count, and workspace watermark remain unchanged.

### D2 — conditional no-effect authority

- `test_theme_no_effect_is_read_authorized_and_changed_value_is_not_forgable`
  proves a current-version unchanged PATCH succeeds with `theme:read` alone,
  returns no semantic action, creates no theme/COW/audit/quota effect, and
  records exactly one durable idempotency result for replay.
- The same test proves missing-read, changed read-only, forged `p_no_effect`,
  narrowed L3 resource, unrelated `theme-global:write`, exact replay,
  idempotency mismatch, and stale-version outcomes.
- Route policy, generated OpenAPI, handler coverage, and bidirectional metadata
  checks declare `theme:read` plus a changed-value conditional
  `theme-tokens:write` requirement.

### D3 — helper and migration preservation

- `test_agent_065_theme_data_round_trip_preserves_legacy_state` captures fresh
  064 `pg_get_functiondef`, signatures, owners, ACLs, and volatility for the
  shared resource helper and legacy theme wrappers, then compares exact
  restoration after a data-bearing 065 downgrade.
- The same test confirms valid theme data survives 064 → 065 → 064 → 065.
- `test_theme_downgrade_rejects_pending_cow_without_data_loss` proves a live
  theme COW change blocks downgrade with `THEME_MIGRATION_PENDING_COW` and is
  still readable unchanged afterward.
- The extended helper is derived from migration 060, so pre-theme validation
  remains present; direct runtime access to the helper remains privilege-denied.

### D4 — hostile, isolation, lifecycle, purity, and concurrency proof

- `test_theme_lifecycle_foreign_context_read_purity_and_reconnect` proves
  absent/existing read purity, malformed resource rejection, direct helper
  privilege denial, foreign-site/workspace denial, independent workspace
  visibility, expiry, revocation, freezing, archived-site denial, quota
  exhaustion, and fresh-process read recovery.
- `test_theme_races_use_database_barrier_and_cancel_without_residue` holds the
  exact PostgreSQL theme advisory lock, proves both intended transactions are
  waiting in `pg_locks` before release, and proves one `200`/one `409` for both
  first materialization and existing-row same-version races. Cancellation after
  idempotency reservation leaves no additional durable state.
- The CI-selected component regression’s exact lock barrier now passes on the
  completed PostgreSQL matrix.

### Existing CI failure repair

- The prior PostgreSQL 15 failure was confirmed as the unscoped global waiter
  count in `_wait_for_page_structure_waiters`; the helper now uses the exact
  blocker lock identity and an 8-second monotonic readiness deadline.
- The prior Firefox `browser-response` failure was preserved as historical
  deferred evidence per order. No browser test was suppressed or weakened;
  the current remote Compose check and local smoke both pass, but this report
  does not claim the separately reserved Firefox criterion closed.

### Scope and remaining acceptance

- V1 global theme precedence/default/reset and V2 same-Agent-workspace visual
  proof were not implemented in this round.
- Global regions, page-style/catalog expansion, exact-workspace Puck, media,
  MCP, review, promotion, publication, and later objectives were not touched.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED.
- `uv run --frozen mypy`: PASSED — no issues in 271 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED — 540 passed, 1 warning, 24.01s.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED on final head — 214 passed in 1993.91s (33:13).
- `uv run --frozen pytest services/backend/tests/integration/test_agent_theme_boundaries.py -q`: PASSED on final head — 8 passed in 76.99s.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -k component -q`: PASSED — 24 passed, 50 deselected, 245.94s.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -k 'theme or 065_theme_data_round_trip' -q`: PASSED — 3 passed, 71 deselected, 36.99s.
- `uv run --frozen python -m compileall -q tools tests/repository`: PASSED.
- `uv run --frozen python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 58 passed.
- `uv run --frozen python tools/check_repository.py`: PASSED.
- `uv run --frozen python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues.
- `uv run --frozen python tools/generate_theme_schema.py --check`: PASSED.
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`: PASSED.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — sdist and wheel.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- All ten process `--check` entrypoints: PASSED.
- `uv run --frozen python -m tools.supply_chain.policy validate`: PASSED.
- `sh tools/compose/smoke.sh slaif007q10`: PASSED — `compose-smoke: OK`, 11 browser projects and 48 smoke tests.
- An initial invalid local project name was rejected by the smoke allowlist before
  execution; no containers/tests ran for that attempt. The valid retry above is
  the only Compose result claimed.

## GitHub CI / required checks

Final current-head run: CI workflow `34417528496`; CodeQL workflow
`34417528479`; CodeQL aggregate
`https://github.com/ulfe-lmi/slaif-agent-site/runs/102685759753`.

Every observed check was `SUCCESS` on implementation head
`8c0b36bc50b136d027fc1f37c7b5ab9e3c8d0401`:

- Repository policy — job `102685600969`.
- Node contracts — job `102685601049`.
- Python 3.12 quality and package — job `102685601181`.
- Python 3.13 quality and package — job `102685601115`.
- Python 3.14 quality and package — job `102685601102`.
- Foundation PostgreSQL 14 — job `102685601261`.
- Foundation PostgreSQL 15 — job `102685601269`.
- Foundation PostgreSQL 16 — job `102685601285`.
- Foundation PostgreSQL 17 — job `102685601161`.
- Foundation PostgreSQL 18 — job `102685601167`.
- Compose and edge packaging — job `102685601069`.
- Supply-chain evidence — job `102685601163`.
- Markdown — job `102685601206`.
- Mermaid — job `102685601154`.
- Dependency review — job `102685601165`.
- Detect supported languages — CodeQL job `102685601044`.
- Analyze actions — CodeQL job `102685633360`.
- Analyze Python — CodeQL job `102685633129`.
- Analyze JavaScript/TypeScript — CodeQL job `102685633185`.
- CodeQL aggregate — check run `102685759753`.

All required green at report drafting: YES. The report-only commit may trigger
fresh checks; strategy must independently verify those report-head checks.

## Local setup / dependencies

- Used the repository’s existing frozen uv 0.12.5 environment, Node 24.14.1,
  pnpm 11.22.0, local PostgreSQL fixtures, disposable Compose volumes, and
  existing Playwright/browser tooling.
- No production systems, production credentials, real secrets, capabilities,
  cookies, or private artifact URLs were accessed or printed.
- No new production dependency was added.

## Documentation and governance

- Updated the current OAP increment/progress/contract ledgers to record 078-q,
  its bounded D1–D4 result, and the remaining V1–V2/Firefox scope.
- Committed `oap/audits/078-2-theme-increment-review.md` and
  `oap/orders/078-q-theme-trusted-boundary-repairs.md` exactly as strategy
  supplied; no historical order or report was rewritten.
- Generated OpenAPI was regenerated from the route registry and verified
  bidirectionally.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production systems or secrets accessed: NO.
- Required tests skipped or weakened: NO. The known Firefox criterion remains
  explicitly deferred, not suppressed.
- Scope deviation: NO.
- Extra objective PR: NO.
- Coding-agent merge/auto-merge: NO.
- Activated order or active content edited by coding: NO; exact strategy bytes
  were committed unchanged.
- Final report commit changes only this report: YES.

## Known limitations / blockers

- PR #79 remains open and is not accepted or merged by the coding agent.
- V1 global precedence/default/reset repair, V2 same-Agent-workspace visual
  proof, and the separately deferred Firefox browser-response criterion remain
  unproven for strategy’s later bounded rendering/evidence decision.
- This report’s `SELF` values become literal only after the report-only commit
  is created and verified as the remote PR head.

## Recommended strategic follow-up

Strategy should independently verify the report-only SELF commit and PR-head
checks, review the D1–D4 evidence, and issue the next bounded rendering order
only if it chooses to address V1–V2/Firefox. Objective 078 must not be declared
complete from this partial continuation alone.
