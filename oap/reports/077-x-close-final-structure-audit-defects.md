# OAP Coding-Agent Report — 077-x

## Work order

- Identifier: `077-x`.
- Work-order file: `oap/orders/077-x-close-final-structure-audit-defects.md`.
- Numeric objective: `077`.
- PR mode: `AMENDED_EXISTING_PR`.
- Scope authority: exact `oap/active` value `077-x`.

## Status

COMPLETE

## Executive summary

Objective 077 had two remaining structural-integrity gaps. Agent and trusted
navigation mutation paths accepted PAGE targets whose pages used the dynamic
`{slug}` route template, and a referenced static page could be changed to a
dynamic template while retaining a PAGE navigation item. Render therefore
could receive a navigation state that could not represent one concrete route.

This round added migration `057_001` as an append-only repair. It validates
site-bound, enabled, static, concrete PAGE targets; rejects static-to-dynamic
page changes while referenced; makes the Render navigation boundary fail closed
for owner-corrupt dynamic references; and preserves the existing structural
advisory lock so navigation-create versus page-template PATCH has one coherent
terminal state. It also added the required real PostgreSQL Agent and Render
hostile evidence without adding product behavior.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), state `OPEN`.
- Base branch: `main`.
- Head branch: `oap/077-agent-site-structure-semantics`.
- Starting remote report head: `f9843388264753ccd0379495f8f51ef101bd4c4c`.
- Starting remote `main`: `067676314e0d9664d40cb8514ea549b966a4eb2d`.
- Implementation head SHA: `f7627ce794db80f3e6d735648ada5cbf9b9b01a2`.
- Report publication commit: SELF.
- Remote PR head after report publication: SELF, verified after publication.
- Implementation commits pushed before report: `f89c47c`, `afd3662`, `f7627ce`.
- New PR this round: no.
- Existing PR amended: yes.
- Merge performed: NO.

## Changes made

- Added `057_001_navigation_dynamic_route_integrity.py`, down-revision
  `056_001`.
- Added the owner-only helper
  `content.slaif_navigation_page_target_validate(uuid,uuid,text)`. It requires
  exact page identity, same-site non-tombstoned content, an enabled locale, a
  static route, a successfully resolved concrete route, and bounded route
  characters.
- Replaced the Agent PAGE target validator to call the helper before the
  existing Agent visibility/resource checks. INTERNAL and EXTERNAL semantics
  remain unchanged.
- Replaced the Agent page update wrapper so a
  `PAGE_NAVIGATION_DEPENDENCY` validation error occurs before quota consumption,
  COW writes, audit completion, or idempotency completion when a referenced
  page is changed to `{slug}`.
- Applied the same concrete PAGE boundary to the existing trusted navigation
  create/update functions.
- Updated the Render navigation function to convert a dynamic/corrupt PAGE
  reference into `RENDER_NAVIGATION_PAGE_INVALID` rather than returning a
  placeholder route.
- Preserved function ownership, `search_path=pg_catalog`, and role grants.
- Made the 057 downgrade drop/recreate the composite-returning legacy editor
  functions inside the migration transaction, then restore owner and
  `slaif_editor_runtime` execute privileges. This preserves older migration
  preflight atomicity across COW view/table composite types.
- Updated migration-head, readiness, bootstrap, package inventory, and
  compatibility expectations from `056_001` to `057_001`.
- Added public-Agent navigation/page concurrency and residue evidence.
- Added a real PostgreSQL Render hostile matrix and production Render HTTP
  error-envelope evidence.

## Files changed

- `services/backend/src/slaif_agent_site/db/alembic/versions/057_001_navigation_dynamic_route_integrity.py`
- `services/backend/src/slaif_agent_site/bootstrap/service.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_control_database_integration.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/integration/test_editable_domain_proof.py`
- `services/backend/tests/integration/test_human_agent_session_control.py`
- `services/backend/tests/integration/test_render_structure_router.py`
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `oap/orders/077-x-close-final-structure-audit-defects.md` (strategic bytes,
  committed unchanged)
- `oap/active` (strategic bytes, committed unchanged; value `077-x`)

## Acceptance-criteria evidence

### Criterion 1 — concrete PAGE navigation targets

- Public Agent create targeting a dynamic page: `422`.
- Public Agent update targeting a dynamic page: `422`.
- Both rejected requests left mutation quota, idempotency rows, audit rows, and
  COW change-operation inventory unchanged; rejected idempotency keys were
  absent.
- A valid static PAGE item remained bound by page identity after a static slug
  move. Authenticated production preview rendered the moved page and resolved
  the item target to the moved concrete route.
- Static-to-dynamic PATCH of a referenced page: `422`; page row, row version,
  navigation item, and target identity remained unchanged.

### Criterion 2 — deterministic navigation-create/page-PATCH race

- A database advisory-lock barrier released concurrent public-Agent
  navigation-create and static-to-dynamic page PATCH operations together.
- Exactly one operation succeeded. The final state was exactly one of:
  static page plus PAGE navigation, or dynamic page plus no navigation.
- No UUID-order selection or timing sleep was used as concurrency evidence.

### Criterion 3 — hostile dynamic-detail Render matrix

- A detail item excluded by the stored bounded filter returned HTTP `404`.
- Dynamic pages with zero detail nodes, multiple detail nodes, a non-detail
  node, malformed detail props, or a missing/wrong view returned HTTP `404`.
- Static/dynamic overlap and multiple matching dynamic candidates returned the
  deterministic bounded integrity failure HTTP `503` with no page or binding
  body; no UUID-order candidate was selected.
- Foreign-site and wrong-type view associations, stale view/type/item
  definitions, and deleted-item state failed closed.
- Valid selected-locale translation rendered; missing selected translation
  fell back to the valid default translation; missing default or malformed
  required translation failed closed.
- Canonical DRAFT, ARCHIVED, and unknown item routes returned `404`; preview
  ARCHIVED and unknown routes returned `404`.
- Extra path segments, encoded traversal, overlong slugs, script/template
  payloads, query strings, localized filter/sort attempts, and undeclared
  projection members returned `404` without widening selection or executing
  behavior.
- Error responses contained neither fixture identifiers nor partial
  `bindings`; public and preview pools remained reusable after the matrix.
- An owner-seeded dynamic PAGE navigation reference produced the Render
  integrity failure and no partial projection.

### Criterion 4 — migration, grants, and compatibility

- `057_001` upgraded and downgraded on real PostgreSQL with COW disabled and
  restored the boundary on upgrade.
- The helper was verified `slaif_owner`-owned, `SECURITY DEFINER`, and
  `search_path=pg_catalog`, with no PUBLIC, Agent-runtime, or Editor-runtime
  execute grant.
- Agent page update, Editor navigation create, and public Render navigation
  grants remained present and correctly role-confined.
- Existing 049/046/047/048/semantic-audit downgrade and round-trip tests passed
  after the COW composite-type rollback repair.

## Local verification

- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  58 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; CLI
  11.16.0.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues in 407
  files.
- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository
  tools`: PASSED.
- `uv run --frozen mypy`: PASSED — no issues in 257 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED
  — 522 tests; one existing Starlette deprecation warning.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — wheel and
  source distribution.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 176
  tests in 1609.44 seconds.
- Focused navigation, Render, migration, privilege, and adjacent structural
  regressions: PASSED — 8 tests; the new navigation, hostile matrix, and 057
  migration tests were rerun successfully.
- `node --version`: `v24.14.1`.
- `pnpm --version`: `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — workspace and contract tests.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED; output was written only to disposable
  `/tmp/slaif-077-x-licenses.json`.
- `sh tools/compose/smoke.sh slaif007xdbg8`: PASSED — clean Compose/NGINX
  smoke, 11 browser projects, public acceptance, restart/outage/recovery,
  edge/security checks, and 48 packaging tests.
- `sh tools/supply_chain/run.sh /tmp/slaif-077-x-supply-20260908`: PASSED —
  six images, zero Critical findings, 42 High findings, checksum verified.

## GitHub CI / required checks

Observed for implementation head `f7627ce794db80f3e6d735648ada5cbf9b9b01a2`
before report publication:

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
- CodeQL — Detect supported languages: SUCCESS.
- CodeQL — Analyze actions: SUCCESS.
- CodeQL — Analyze javascript-typescript: SUCCESS.
- CodeQL — Analyze python: SUCCESS.
- CodeQL aggregate: SUCCESS.

No required check was pending, skipped, cancelled, missing, or failed at the
implementation head observation.

## Scope and governance confirmations

- Only PR #74 was amended; no extra PR was created.
- No merge, close, or auto-merge was performed.
- No dependency, lockfile, image, architecture, API, media, MCP, composition,
  review/promotion, or 078+ feature was added.
- No final MVP truth ledger or PR body was modified.
- Earlier migrations and reports were not rewritten.
- The activated order and `oap/active` bytes were committed unchanged.
- No real secrets, capabilities, cookies, credentials, or production data were
  committed or printed.
- Owner corruption in tests was bounded to disposable local PostgreSQL
  fixtures and was restored or isolated by fixture teardown.

## Limitations and remaining authority

This report completes coding order `077-x`; it does not accept or merge
Objective 077. PR #74 remains open and unmerged. Per the active order,
077-y remains reserved for the final strategic audit/truth-document
reconciliation, and strategy alone decides acceptance and merge.

Strongest remaining reason not to accept Objective 077 in this round: the
strategic final audit and truth-ledger reconciliation reserved for 077-y have
not yet been performed by strategy. No substantive implementation blocker was
observed in 077-x.

## Final protocol state

- Report publication commit must be the single report-only child of
  implementation head `f7627ce794db80f3e6d735648ada5cbf9b9b01a2`.
- Report publication commit: SELF.
- No repository mutation or push follows the report-only commit.
- After remote report-head verification, the coding agent sends exact ASCII
  `OK` (two bytes, no newline) on the response FIFO and blocks on the control
  FIFO again.
