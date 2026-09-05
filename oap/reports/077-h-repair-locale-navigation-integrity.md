# OAP Coding-Agent Report — 077-h

## Work order

- Identifier: `077-h`
- Work-order file: `oap/orders/077-h-repair-locale-navigation-integrity.md`
- Numeric objective: `077`
- Work-order SHA-256: `451ac35cf4759240e03f5c5bd3d2f6c236332f4a880cd830400196d5f817d2ab`
- `oap/active` bytes: `077-h` followed by LF (`30 37 37 2d 68 0a`)
- `oap/active` SHA-256: `e4e72e2caa11623bee1853a4aaa90d3179b954ffcce7163becde6eeb2f4b1e22`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`COMPLETE`

## Executive summary

The active 077-h order is complete. The existing Objective 077 branch now
repairs the locale and navigation integrity defects found in 077-g without
reimplementing or broadening the already-passing structural concurrency
solution.

The implementation is committed and pushed as
`ec4414feea10549b2bfbfdc9c21ea085e01d9cfe`, directly on the required 077-g
report head `6ca6977420e76dbda5ef0f8d53b78c3e3b39ac5e`. Focused tests, the full
integration suite, all local Python and Node gates, clean Compose acceptance,
and current GitHub CI and CodeQL are green.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74)
- PR state: `OPEN`, unmerged
- Base/head: `main` / `oap/077-agent-site-structure-semantics`
- Starting remote report head: `6ca6977420e76dbda5ef0f8d53b78c3e3b39ac5e`
- Starting remote `main`: `067676314e0d9664d40cb8514ea549b966a4eb2d`
- Implementation head SHA: `ec4414feea10549b2bfbfdc9c21ea085e01d9cfe`
- Implementation head parent: `6ca6977420e76dbda5ef0f8d53b78c3e3b39ac5e`
- Implementation commit pushed before this report:
  `ec4414feea10549b2bfbfdc9c21ea085e01d9cfe`
- Remote branch before report publication:
  `ec4414feea10549b2bfbfdc9c21ea085e01d9cfe`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (literal derived via GitHub)
- New PR this turn: `NO`
- Amended existing PR this turn: `YES`
- Merge or auto-merge performed: `NO`

## Changes made

- Repaired Agent locale and navigation request models so locale/item PATCHes
  reject empty bodies, locale PATCH cannot alter the immutable tag, item PATCH
  cannot alter parent or anchors, and move requires an explicit nullable
  parent.
- Added strict Agent target validation: PAGE targets are same-site visible
  pages, INTERNAL targets are exact effective routes of visible non-tombstoned
  static pages, and EXTERNAL targets are HTTPS only. Labels are bounded and
  must reference enabled same-site locales permitted by the capability.
- Applied resource constraints consistently to locale, navigation, and item
  list/get/create/update/move/delete operations, including visible-count
  enforcement over the constrained sets.
- Made default-locale switching version and timestamp the previous default;
  kept locale dependency checks and constrained navigation semantics
  transactionally fail-closed.
- Made navigation item create/update/move/delete maintain dense sibling order,
  preserve item parent/order on Agent PATCH, require explicit parent on move,
  and version/timestamp shifted siblings.
- Unified Editor page, locale, navigation, and item writes under the ordered
  workspace+site structural lock. Added real PostgreSQL Agent/Editor HTTP race
  coverage for page/item, locale/page, and competing navigation moves.
- Updated unreleased migration `050_001`, models/services, privileges,
  OpenAPI, API/testing docs, integration tests, and the public Compose
  acceptance fixture. The migration downgrade list now also removes the label
  helper during 049/050 round trips.

## Files changed

The implementation commit changed exactly:

- `contracts/openapi/agent-v1.json`
- `docs/API.md`
- `docs/TESTING.md`
- `oap/active`
- `oap/orders/077-h-repair-locale-navigation-integrity.md`
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`
- `services/backend/src/slaif_agent_site/content_model/service.py`
- `services/backend/src/slaif_agent_site/content_model/site_data_models.py`
- `services/backend/src/slaif_agent_site/content_model/site_data_validators.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/050_001_agent_locale_navigation.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_human_editor_production_http.py`
- `tools/compose/public_agent_acceptance.py`

## Acceptance-criteria evidence

### Resource and locale integrity

- Locale, navigation, and navigation-item list/get/mutation functions enforce
  both allowed keys and allowed IDs, and visible maxima count only the
  constrained resources. Cross-site and disallowed-resource lookups fail
  closed.
- Agent locale PATCH has no `tag` field; empty locale and navigation PATCHes
  are rejected at the typed HTTP boundary before quota, idempotency, or audit
  work. The default switch versions and timestamps the former default, and
  the Compose acceptance verifies the 1→2→3 transition through restore/delete.
- Navigation labels are bounded JSON objects whose keys are enabled,
  same-site, capability-allowed locale tags. Invalid, disabled, foreign, and
  disallowed label locales are rejected.

### Target, item, and ordering integrity

- PAGE targets require the exact same-site visible page UUID; INTERNAL targets
  require an exact effective route for a visible static page and reject
  traversal, reserved paths, dynamic routes, and unknown routes; EXTERNAL
  targets require HTTPS. The public acceptance uses a real static page and
  its effective `/en/docs-...` route after switching the site default locale.
- Agent item PATCH changes only target/page/labels/locale and preserves
  parent/order. Move accepts explicit nullable parent plus mutually exclusive
  anchors. Create, move, and delete compact sibling positions; every shifted
  sibling receives a row-version and `updated_at` change.
- Parent references are same-navigation, cycle-safe, depth-bounded, and
  resource-constrained. Page and locale dependency deletes remain fail-closed.

### Shared lock and races

- Agent and Editor page, locale, navigation, and item structural writes
  acquire one deterministic workspace+site structural advisory lock after the
  workspace lifecycle lock.
- The real production HTTP race test passed for concurrent Agent page delete
  versus Editor item create, Agent locale disable versus Editor localized page
  create, and Agent move versus Editor move/reorder. Outcomes were serialized
  with stable conflict behavior and no residual mutation state.

### Migration and contract evidence

- Unreleased migration `050_001` was updated in place, with explicit grants,
  downgrade compatibility, and no new migration revision. The focused 049/050
  data-bearing downgrade/upgrade selection passed `2` tests.
- Canonical Agent OpenAPI was regenerated and its exact check passed. API and
  testing documentation describe the corrected target, label, PATCH, move,
  and ordering contracts.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 265 files already formatted.
- `uv run --frozen mypy`: PASSED — 248 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 160
  tests in 21m27s.
- Full Agent mutation suite: PASSED — 38 tests in 6m10s.
- Full human Editor production HTTP suite: PASSED — 4 tests in 39.78s.
- Focused Agent journey/race checks: PASSED — 2 tests.
- Focused resource-constraint check: PASSED — 1 test.
- Focused migration downgrade/upgrade checks: PASSED — 2 tests.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  58 tests.
- `python tools/check_repository.py`: PASSED — repository policy.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; CLI
  11.16.0.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 375 files, 0
  issues.
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`:
  PASSED.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — source
  and wheel distributions built.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- All ten required process smoke checks via
  `uv run --frozen python -m <process> --check`: PASSED with `CHECK_OK`.
  The initial bare-interpreter invocation was an environment-path negative
  (`ModuleNotFoundError`); the required frozen project invocation was rerun and
  is the recorded pass evidence.
- `sudo -n sh tools/compose/smoke.sh slaif071localtest`: PASSED — final
  `compose-smoke: OK`, including public Agent acceptance, restart/recovery,
  edge, packaging, security, database-role, browser, and secret-policy
  checks.

No required local gate was skipped, weakened, replaced, or treated as passed
from an incomplete run.

## GitHub CI / required checks

For implementation head
`ec4414feea10549b2bfbfdc9c21ea085e01d9cfe`, CI workflow run
`33914128236` and CodeQL workflow run `33914128237` completed successfully.
Every current check was terminal `pass`:

- Analyze (actions)
- Analyze (javascript-typescript)
- Analyze (python)
- CodeQL
- Compose and edge packaging
- Dependency review
- Detect supported languages
- Foundation PostgreSQL 14
- Foundation PostgreSQL 15
- Foundation PostgreSQL 16
- Foundation PostgreSQL 17
- Foundation PostgreSQL 18
- Markdown
- Mermaid
- Node contracts
- Python 3.12 quality and package
- Python 3.13 quality and package
- Python 3.14 quality and package
- Repository policy
- Supply-chain evidence

`gh pr checks 74` was inspected at the implementation head and showed all
listed checks as `pass`. PR #74 remains `OPEN`, and the coding agent did not
merge or auto-merge it.

## Local setup / dependencies

- Existing frozen uv and pnpm environments were used.
- Disposable PostgreSQL fixtures and clean Compose stacks used passwordless
  sudo only for routine test infrastructure.
- No production dependency, image, lockfile, exception, or foundation version
  changed. Foundation use remains through qualified `agentcow.postgres` public
  APIs.
- No production systems, data, credentials, capabilities, cookies, or private
  artifact URLs were accessed, printed, or committed.

## Documentation and governance

- `oap/active` and the exact 077-h order bytes were committed byte-for-byte as
  supplied by strategy. Coding did not author, rewrite, or supersede either
  strategic artifact.
- No architecture, constitution, communication protocol, historical report,
  prior order, or unrelated strategic artifact was rewritten.
- This report is the sole report publication file and must be committed as a
  report-only child of the literal implementation SHA.

## Safety and scope confirmations

- Unrelated files changed: `NO`.
- Production systems/data accessed: `NO`.
- Real secrets/capabilities/cookies/private credentials printed or committed:
  `NO`; tests used disposable fixtures and fake credentials.
- Required checks skipped, weakened, or replaced: `NO`.
- Scope deviation: `NO`; no new feature, cleanup, refactor, dependency,
  architecture, media, browser authority, publication, merge, or unrelated
  objective work was added.
- Extra objective PR: `NO`.
- Coding-agent merge or auto-merge: `NO`.
- Report publication commit changes only this report: `YES`.

## Known limitations / completion condition

No 077-h implementation blocker remains. PR #74 remains open because coding
agents never merge objective PRs and `COMPLETE` is not strategic acceptance.
Objective 077 remains open until this slice and the remaining ordered 077
scope are accepted through repository governance.

Objective 077 / PR #74 may be declared complete only when strategy
independently verifies this report-only `SELF` child, its exact parent/path,
and all fresh report-head checks, then obtains the required human review,
merges PR #74 to verified remote `main`, and verifies the merged main state.
Until that strategic/human merge and verification occurs, this is a delivered
077-h implementation round, not objective acceptance.

Report publication commit: SELF
