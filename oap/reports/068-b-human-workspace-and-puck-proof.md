# OAP Coding-Agent Report — 068-b

## Work order

- Identifier: `068-b`; work-order file: `oap/orders/068-b-human-workspace-and-puck-proof.md`
- Numeric objective: `068`
- PR mode: `CONTINUE_SAME_PR`
- Objective PR: [#59](https://github.com/ulfe-lmi/slaif-agent-site/pull/59)

## Status

BLOCKED

`RESULT=BLOCKED`

## Executive summary

Implemented the server-side HUMAN workspace and Editor mutation-envelope
correction on PR #59. Editor requests now resolve a real ACTIVE, unexpired
HUMAN `control.workspace` owned by the authenticated user and route site,
enter COW with that workspace UUID, reassert the human session/user/site
binding inside PostgreSQL, and use Editor-only workspace, idempotency, and
audit functions. The ordinary app-level Editor content-service fallback was
removed. State-changing Editor requests require a bounded idempotency key;
completion and the HUMAN audit row are intended to commit in the same COW
transaction.

The order is blocked by the explicit CSP gate. With the 068-b console-error
allowlist removed, the real Compose browser path fails on an actual Puck
runtime violation under the enforced `style-src 'self'` policy. The installed
`@measured/puck@0.20.2` distribution contains multiple unconditional React
inline `style` props, including canvas, DropZone, overlay, loader, sidebar, and
layout paths. No nonce-compatible Puck option exists in this package, and the
order forbids `unsafe-inline`, report-only policy, suppression, monkey-patching,
or a test bypass. I therefore stopped without claiming the visible Puck
add/move proof.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#59](https://github.com/ulfe-lmi/slaif-agent-site/pull/59) — `OPEN`
- Base/head: `main` / `oap/068-puck-editor`
- Starting remote 068-a report head: `f1511075937e66fe2fba9b80947c9027411e63f8`
- Implementation head SHA: `a9db9faab5492783059637b940c760d2f116b800`
- Report publication commit: `SELF`
- Report parent will equal the implementation SHA above.
- Implementation commits pushed for 068-b before report: `a9db9faab5492783059637b940c760d2f116b800`
- Remote PR head before report: `a9db9faab5492783059637b940c760d2f116b800`
- PR was observed `OPEN` with `UNSTABLE` merge state because the required
  Compose/edge check correctly fails on the unresolved CSP violation.
- No second objective PR exists.

## Changes made

- Added migration `028_001_human_editor_workspace_envelope` with:
  `slaif_human_editor_workspace_resolve`,
  `slaif_human_editor_workspace_assert`,
  `slaif_human_editor_idempotency_begin`, and
  `slaif_human_editor_idempotency_complete`.
- Added `control.human_editor_idempotency` and
  `audit.human_editor_mutation`; Editor receives only exact SECURITY DEFINER
  function grants and Control receives only workspace resolution.
- Added server-owned workspace resolution per authenticated human/site,
  workspace/session/user/site/expiry assertions, advisory workspace locking,
  server-generated operation UUIDs, replay/mismatch handling, response
  completion, and same-transaction audit integration.
- Removed the ordinary Editor `ContentModelService` fallback. Handlers require
  a successfully established request-scoped workspace service.
- Added per-connection Editor/Control authority support and updated privilege
  verification for the narrow HUMAN Editor function set.
- Added CSRF-preserving `Idempotency-Key` headers to web Editor mutations and
  replay/mismatch coverage to the edge E2E setup path.
- Added smoke assertions for active HUMAN workspace ownership and completed
  HUMAN audit/idempotency rows; the assertions are not reached when the Puck
  CSP error aborts the browser contract.
- Updated workspace/Editor API, database-role, and connection documentation.
- Exact activated `oap/active` and `oap/orders/068-b-human-workspace-and-puck-proof.md`
  transcript bytes are committed.

### Files changed

- `apps/web/src/admin/api.ts`
- `docs/API.md`; `docs/DATABASE_CONNECTIONS.md`; `docs/DATABASE_ROLES.md`
- `oap/active`; `oap/orders/068-b-human-workspace-and-puck-proof.md`
- `services/backend/src/slaif_agent_site/control_api/database.py`
- `services/backend/src/slaif_agent_site/control_api/site_authority.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/028_001_human_editor_workspace_envelope.py`
- `services/backend/src/slaif_agent_site/editor_api/{app.py,composition_http.py,content_http.py,database.py,item_http.py,media_http.py,mutations.py,media_http.py,nav_theme_http.py,page_http.py,view_http.py}`
- `services/backend/tests/integration/{test_control_database_integration.py,test_database_bootstrap.py,test_runtime_service_wiring.py}`
- `services/backend/tests/unit/{test_control_database.py,test_foundation_contract.py,test_health_apps.py}`
- `tests/e2e/governance.spec.ts`
- `tools/compose/smoke.sh`

## Acceptance-criteria evidence

### Criterion 1 — Real HUMAN workspace authority

- PASS for implementation evidence. The resolver creates/reuses a persisted
  `actor_type='HUMAN'` workspace keyed by site and authenticated user; the
  Editor COW session uses the workspace UUID, never the human authentication
  session UUID. PostgreSQL assertion checks workspace state/expiry/site/user,
  active account/site, live human session ownership, COW session UUID, and
  operation UUID; mutations obtain a transaction advisory workspace lock.
- PASS for direct local diagnostic. A real `slaif_editor_runtime` connection
  successfully asserted the workspace and began an Editor envelope; no
  Control credential was used for content calls.

### Criterion 2 — Durable idempotency and HUMAN audit

- PASS for implementation wiring and direct local diagnostic. Page creation,
  component, page, and composition state-changing routes all enter the common
  envelope through `authorize_site_request`; the SQL completion function writes
  the audit row and marks idempotency complete before COW commit. Direct local
  PostgreSQL execution successfully completed a page mutation and completion.
- NOT PROVEN end-to-end. The browser contract aborts on CSP before the smoke
  script reaches its post-browser audit/idempotency assertions. A future run
  after the CSP decision must prove replay/mismatch, forced rollback, and
  audit counts through the real edge flow.

### Criterion 3 — Visible Puck add/move/save/reload under CSP

- BLOCKED. The allowlist from 068-a was removed. The local Compose run fails
  the Puck test at the final browser-error assertion. GitHub Compose/edge
  packaging fails at the same browser contract; all setup/governance routes
  before Puck pass.
- Exact browser evidence: the console message is
  `Applying inline style violates the following Content Security Policy
  directive style-src 'self'`; its source is a generated Next static chunk
  under `http://localhost:8080/_next/static/chunks/`. The browser blocks the
  action under the enforced edge CSP.
- Exact installed-runtime evidence: `@measured/puck@0.20.2/dist/index.js`
  contains runtime inline style objects at the Loader, DraggableComponent,
  DropZone, overlay, SidebarSection, Canvas, and Puck layout paths. The
  package exposes no nonce/style-attribute adaptation. The edge configs remain
  `style-src 'self'` with no `unsafe-inline`.
- No Puck package fork, patch exception, CSP weakening, console suppression, or
  test-only bypass was introduced.

### Criterion 4 — Scope and authority boundaries

- PASS for implemented server boundaries. No Agent route, capability, review,
  publication, canonical, setup, responsive-preview, or new content type was
  added. Editor has no direct Control/Audit table DML and uses only exact
  function grants.
- BLOCKED for final acceptance because the required browser/CSP proof is
  missing, and the order explicitly makes that proof mandatory.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED (`195 files`).
- `uv run --frozen mypy`: PASSED (`183` source files).
- Focused backend unit/metadata/health/control tests: PASSED (`37 tests`).
- `uv run --frozen pytest services/backend/tests/integration/test_database_bootstrap.py -x`: PASSED (`23 tests`) with migration 028 and grants.
- `python tools/check_repository.py`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED (`53 tests`).
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED (`0 issues`).
- `pnpm typecheck`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm install --frozen-lockfile`: PASSED.
- `python tools/compose/verify.py`: PASSED before the browser contract.
- `sudo sh tools/compose/smoke.sh slaif007puck`: BLOCKED/FAILED at the
  required Puck browser CSP assertion; setup/governance and all earlier stack
  health checks passed. The disposable stack was cleaned by the smoke trap.
- Direct local PostgreSQL diagnostic with actual Editor role: workspace assert,
  idempotency begin, page COW write, and idempotency/audit completion PASSED.

## GitHub CI / required checks

Observed for implementation head
`a9db9faab5492783059637b940c760d2f116b800`:

- SUCCESS: Repository policy
- SUCCESS: Detect supported languages
- SUCCESS: Node contracts
- SUCCESS: Analyze (actions)
- SUCCESS: Analyze (python)
- SUCCESS: Analyze (javascript-typescript)
- SUCCESS: Python 3.12 quality and package
- SUCCESS: Python 3.13 quality and package
- SUCCESS: Python 3.14 quality and package
- SUCCESS: Foundation PostgreSQL 14
- SUCCESS: Foundation PostgreSQL 15
- SUCCESS: Foundation PostgreSQL 16
- SUCCESS: Foundation PostgreSQL 17
- SUCCESS: Foundation PostgreSQL 18
- FAILURE: Compose and edge packaging — Puck browser CSP violation
- SUCCESS: Supply-chain evidence
- SUCCESS: Markdown
- SUCCESS: Mermaid
- SUCCESS: Dependency review
- CodeQL: report-head state not required for the blocker decision; prior 068-a
  CodeQL was green and no CSP exception was introduced.

## Local setup / dependencies

- Existing `@measured/puck@0.20.2`, MIT license, and `uuid: 11.1.1` security
  override preserved. No new dependency or hosted service was added in 068-b.
- uv `0.12.5`, Node `24.14.1`, and pnpm `11.22.0` were used.
- Passwordless `sudo` was used only for disposable Compose and local
  PostgreSQL diagnostics. No production credentials, systems, data,
  capabilities, or cookies were accessed.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production secrets accessed: NO.
- Extra objective PR: NO; PR #59 remains the unique 068 PR.
- Coding-agent merge: NO.
- CSP weakened: NO.
- CSP violation allowlisted in committed E2E: NO.
- Report commit changes only this new report: YES.

## Blocker and required human/strategic decision

The pinned Puck runtime cannot satisfy the repository's enforced CSP through
configuration alone. Strategy must choose a reviewed bounded package adaptation
that removes all supported-path inline styles, or explicitly order a different
CSP-compatible editor implementation/replacement. Until that decision and
implementation exist, the required Puck visible add/move/save proof cannot be
honestly marked complete. This report intentionally does not claim acceptance,
publication, or production readiness.
