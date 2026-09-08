# OAP Coding-Agent Report — 077-y

## Work order

- Identifier: `077-y`.
- Work-order file: `oap/orders/077-y-close-internal-navigation-dependencies.md`.
- Numeric objective: `077`.
- PR mode: `AMENDED_EXISTING_PR`.
- Scope authority: exact `oap/active` value `077-y`.

## Status

COMPLETE

## Executive summary

This round repaired the bounded internal-navigation dependency defect. Fixed
`INTERNAL` targets are now validated against the current same-site static route
graph under the existing workspace/site structural lock. Agent and trusted
human Editor route-affecting page operations validate the complete affected
graph before commit, so an operation that would orphan an `INTERNAL` target is
rejected atomically. Navigation creation/update uses the same route law.

Render now performs a status-aware existence check for `INTERNAL` targets and
fails closed for dangling or owner-corrupt state. The existing 057 PAGE
identity behavior remains in place: valid PAGE targets follow static route
moves, while dynamic PAGE targets remain rejected. No new product or 078+
scope was added.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), state `OPEN`.
- Base branch: `main`; base SHA: `067676314e0d9664d40cb8514ea549b966a4eb2d`.
- Head branch: `oap/077-agent-site-structure-semantics`.
- Required starting remote report head:
  `452c938f7b0f4575afc85f93f9378fef6287849a`.
- Implementation head SHA: `227eaa1e78f35b4d9bedb685f0a0a5514dcc4c29`.
- Report publication commit: SELF.
- Remote PR head after report publication: SELF, verified after publication.
- Implementation commits pushed before report:
  `a692950570a1baa36eeeccbe7eb2068c0b084935`,
  `227eaa1e78f35b4d9bedb685f0a0a5514dcc4c29`.
- Report parent will equal the implementation head SHA.
- New PR this turn: NO; existing PR amended: YES; merge performed: NO.

## Changes made

- Added append-only migration
  `058_001_internal_navigation_dependencies.py`, down-revision `057_001`.
- Added owner-only shared static INTERNAL route existence and graph validation
  helpers, with bounded normalization, same-site/current-workspace route
  resolution, reserved/dynamic rejection, and fail-closed behavior.
- Replaced the Agent and trusted navigation validators with the shared route
  law while preserving the 057 PAGE validator and PAGE identity semantics.
- Wrapped Agent and human Editor page route-affecting operations and trusted
  navigation operations so the graph is validated under the existing
  structural lock before an operation can commit.
- Added status-aware Render INTERNAL validation for canonical/preview output;
  dangling, owner-corrupt, unpublished-relevant, and foreign state fails
  closed without a partial projection.
- Preserved function ownership, `SECURITY DEFINER`, `search_path`, and
  role-confined grants. Downgrade restores the prior helper/function surface,
  security, and composite-return compatibility without rewriting migrations
  049–057.
- Updated migration-head/readiness and compatibility expectations for 058.
- Added real PostgreSQL Agent, human Editor production-path, Render, migration,
  privilege, and deterministic concurrency evidence.

## Files changed

- `services/backend/src/slaif_agent_site/db/alembic/versions/058_001_internal_navigation_dependencies.py`
- `services/backend/src/slaif_agent_site/bootstrap/service.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_control_database_integration.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/integration/test_editable_domain_proof.py`
- `services/backend/tests/integration/test_human_agent_session_control.py`
- `services/backend/tests/integration/test_human_editor_production_http.py`
- `services/backend/tests/integration/test_render_structure_router.py`
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `oap/orders/077-y-close-internal-navigation-dependencies.md` (strategic
  bytes committed unchanged)
- `oap/active` (strategic bytes committed unchanged; value `077-y`)

## Acceptance-criteria evidence

### Criterion 1 — valid fixed INTERNAL target

- Real public Agent HTTP created a valid fixed INTERNAL item to a static page.
- The shared migration helper accepted only normalized, concrete, static,
  same-site/current-workspace routes; absent, dynamic, foreign,
  wrong-workspace, reserved, and invalid targets were denied.

### Criterion 2 — route-affecting operations cannot orphan INTERNAL

- Real Agent PostgreSQL-backed HTTP rejected slug, locale, template, direct
  move, ancestor move, and delete operations that would orphan a fixed
  INTERNAL target.
- Rejected operations preserved page/subtree/navigation state, quota,
  idempotency, audit, and COW state; rejected idempotency keys were absent.
- Descendant INTERNAL coverage was exercised: an INTERNAL target to a
  descendant blocked the ancestor move.
- Equivalent human Editor production HTTP page slug mutation was rejected with
  the same dependency boundary and left the page unchanged.

### Criterion 3 — removing dependency and PAGE continuity

- Removing or retargeting the INTERNAL item permitted the otherwise valid page
  route operation.
- A PAGE navigation item continued to follow a static page route move by page
  identity; the 057 dynamic PAGE rejection remained enforced.

### Criterion 4 — shared navigation and Render route law

- Agent/trusted navigation create and update used the common route helper;
  invalid static targets and dynamic/arbitrary paths were denied.
- Render’s owner-seeded dangling INTERNAL fixture returned the production
  fail-closed HTTP error with no identifier, binding, navigation, or partial
  page leakage.
- A relevant unpublished target was unavailable to canonical output while the
  permitted preview status path remained status-aware.
- Render foreign, wrong-workspace, malformed, and owner-corrupt INTERNAL
  states failed closed, and the Render pool remained reusable.

### Criterion 5 — deterministic concurrency

- A real PostgreSQL barrier test raced INTERNAL creation against a page route
  move without timing sleeps. The final graph was exactly coherent: either
  static page plus INTERNAL navigation, or moved/dynamic page plus no invalid
  navigation.
- Exact durable quota, idempotency, audit, and COW deltas were asserted for
  the terminal result; no UUID-order or timing-based winner was selected.

### Criterion 6 — subtree coverage

- An INTERNAL target to a descendant blocked an ancestor subtree move, proving
  validation covers affected descendants rather than only the directly moved
  page.

### Criterion 7 — migration, privileges, and recovery

- 058 upgrade/downgrade/re-upgrade and the historical 057 round-trip passed on
  real PostgreSQL fixtures.
- Ownership, `SECURITY DEFINER`, `pg_catalog` search path, runtime execute
  grants, COW compatibility, and downgrade restoration were verified.
- Render owner-corruption HTTP evidence failed closed and subsequent pool use
  passed; Agent and Editor isolation and cross-site/workspace negatives passed.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 275 files already formatted.
- `uv run --frozen mypy`: PASSED — 258 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED
  — 522 tests; one existing Starlette deprecation warning.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-077-y`: PASSED —
  source distribution and wheel.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 178
  tests in 1670.90 seconds.
- Focused Agent/Editor/Render dependency and corruption evidence: PASSED —
  the new Agent dependency test, Editor production-path test, and Render
  matrix passed together; 057/058 migration round-trip and privilege tests
  passed.
- `uv run --frozen python -m compileall -q tools tests/repository`: PASSED.
- `uv run --frozen python -m unittest discover -s tests/repository -p 'test_*.py'`:
  PASSED — 58 tests.
- `uv run --frozen python tools/check_repository.py`: PASSED — repository
  policy.
- `uv run --frozen python tools/check_mermaid.py`: PASSED — 16 diagrams in 3
  files; CLI 11.16.0.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues in 409
  linted files; 415 Markdown files scanned by the Mermaid preparation check.
- Required process smoke under the frozen environment (`uv run --frozen
  python -m slaif_agent_site.{control_api,editor_api,agent_api,render_api,
  mcp_adapter,media_service,review_worker,scheduler,media_gc,bootstrap}
  --check`): PASSED — all ten reported `CHECK_OK`.
- Initial plain-system-Python smoke invocation stopped before the first module
  because the src package was not on that interpreter’s import path; no test
  or service ran. The corrected frozen-environment invocation above passed.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`, `pnpm lint`, `pnpm format:check`,
  `pnpm typecheck`, `pnpm test`, `pnpm build`, and `pnpm licenses list --json`:
  PASSED as one chained gate; license output was written only to disposable
  `/tmp/slaif-077-y-licenses.json`.
- `sh tools/compose/smoke.sh slaif007ydbg9`: PASSED — clean five-image
  Compose/NGINX run; 11 browser projects, public acceptance, human Editor,
  restart/outage/recovery, policy, and final 48 packaging tests all passed.
- `sh tools/supply_chain/run.sh /tmp/slaif-077-y-supply-20260908`: PASSED —
  six images, zero Critical findings, 42 High findings under the repository
  threshold, checksum verified.

## GitHub CI / required checks

Observed for implementation head
`227eaa1e78f35b4d9bedb685f0a0a5514dcc4c29` before report publication:

- Repository policy: SUCCESS.
- Node contracts: SUCCESS.
- Python 3.12 quality and package: SUCCESS.
- Python 3.13 quality and package: SUCCESS.
- Python 3.14 quality and package: SUCCESS.
- Foundation PostgreSQL 14: SUCCESS.
- Foundation PostgreSQL 15: SUCCESS.
- Foundation PostgreSQL 16: SUCCESS.
- Foundation PostgreSQL 17: SUCCESS.
- Foundation PostgreSQL 18: SUCCESS.
- Compose and edge packaging: SUCCESS.
- Supply-chain evidence: SUCCESS.
- Markdown: SUCCESS.
- Mermaid: SUCCESS.
- Dependency review: SUCCESS.
- Detect supported languages: SUCCESS.
- Analyze actions: SUCCESS.
- Analyze javascript-typescript: SUCCESS.
- Analyze python: SUCCESS.
- CodeQL: SUCCESS.

No required check was pending, skipped, cancelled, missing, or failed at the
implementation-head observation. The report-only commit may trigger a fresh
check run; strategy independently verifies that report-head state.

## Local setup / dependencies

- Used the repository-pinned `uv 0.12.5`, frozen lock/sync, Node 24.14.1, and
  pnpm 11.22.0.
- Integration and Compose evidence used disposable local PostgreSQL,
  containers, fake credentials, and isolated temporary evidence directories.
- No production service, credential store, Docker socket authority, or real
  secret was accessed. No durable dependency or image change was made.

## Documentation

- No durable product/architecture/API/setup/security documentation required
  change; this was a bounded migration and verification repair.
- The immutable strategic order and `oap/active` were included in the
  implementation commit byte-for-byte and were not edited by coding.

## Safety and scope confirmations

- Unrelated files changed: NO; all implementation changes are the migration,
  required compatibility wiring, and focused/affected tests for 077-y.
- Production secrets accessed: NO; production systems accessed: NO.
- Required tests skipped/not run: NO. The initial wrong-interpreter smoke
  command failed before execution and was corrected; its required checks all
  passed under the frozen repository environment.
- Scope deviation: NO. No 078+ behavior, feature, cleanup, refactor,
  dependency/image/architecture/media/MCP/composition/review/promotion,
  ledger, or PR-body work was added.
- Extra objective PR: NO. Coding-agent merge: NO.
- Activated order/active edited: NO.
- Report commit changes only this report: YES.

## Known limitations / blockers

Coding order `077-y` is complete. Objective 077 is not accepted by this
report: PR #74 remains open and unmerged, and the strategy-owned 077-z final
audit/truth reconciliation and acceptance decision remain. The strongest
remaining reason not to accept Objective 077 is that reserved strategic final
audit and truth-ledger reconciliation, not an implementation failure, has not
yet been performed.

## Recommended strategic follow-up

Strategy should independently review this report, the remote PR head and
checks, and the preserved 077-a through 077-y transcript, then decide the
reserved 077-z audit/reconciliation and eventual acceptance/merge. Coding does
not choose or perform that transition.

## Final protocol state

- Report publication commit must be the single report-only child of
  implementation head `227eaa1e78f35b4d9bedb685f0a0a5514dcc4c29`.
- Report publication commit: SELF.
- No repository mutation or push follows the report-only commit.
- After remote report-head verification, coding sends exact ASCII `OK`
  (two bytes, no newline) on the response FIFO and returns to a fresh blocking
  control FIFO wait.
