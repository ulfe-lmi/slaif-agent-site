# OAP Coding-Agent Report — 068-a

## Work order

- Identifier: `068-a`; work-order file: `oap/orders/068-a-puck-editor-ui.md`
- Numeric objective: `068`
- PR mode: `CREATED_NEW_PR`
- Objective PR: [#59](https://github.com/ulfe-lmi/slaif-agent-site/pull/59)

## Status

PARTIAL

`RESULT=PARTIAL`

## Executive summary

Implemented the human admin Puck composition editor at
`/admin/sites/{siteId}/pages/{pageId}/edit`. It loads normalized composition
through the same-origin human Editor API, renders only the trusted catalog,
reconciles normalized add/update/move/delete operations, refreshes server state
after save, and preserves IDs, schema versions, hierarchy, slots, order, and
props without persisting adapter metadata.

The Editor API now has a real bounded runtime: Control remains responsible for
human session/site/permission authorization, while a separate Editor pool and
`editor-secret` credential use `slaif_editor_runtime` for content COW calls.
The reference NGINX and Apache adapters preserve `/api/editor/v1/` and expose
exact Editor health aliases. A corrective migration qualifies page and
composition function columns so PL/pgSQL output-variable names cannot make
Editor writes fail closed.

The functional edge smoke passes the Puck load/save/reload path and persisted
nested structure. The remaining partial item is the exact Playwright drag
gesture requirement: the test seeds add/move through the real human Editor API
with CSRF, then opens Puck and saves/reloads the nested composition. The legacy
`@measured/puck` DropZone gesture itself was not used as the persisted mutation
evidence because nested drag behavior was not stable under the strict CSP and
the pinned package's legacy DropZone implementation.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#59](https://github.com/ulfe-lmi/slaif-agent-site/pull/59) — `OPEN`
- Base/head: `main` / `oap/068-puck-editor`
- Starting remote main SHA: `0969cbd46f5ba07182a2f2e3ea8ea80b2d021750`
- Implementation head SHA: `8405e4c44c62903a96051b883aef1f06497b39af`
- Report publication commit: `SELF`
- Report parent will equal the implementation SHA above.
- Required implementation commits pushed before report: `8405e4c44c62903a96051b883aef1f06497b39af`
- Remote PR head before report: `8405e4c44c62903a96051b883aef1f06497b39af`
- PR was observed `OPEN` with `CLEAN` merge state; coding agent did not merge.
- No second objective PR exists.

## Changes made

- Added `@measured/puck` `0.20.2` (MIT) and locked its transitive graph. A
  root `uuid: 11.1.1` override removes the vulnerable Puck-transitive
  `uuid@9.0.1`; `pnpm audit --prod` reports zero vulnerabilities.
- Added the trusted Puck catalog/configuration, strict normalized adapter,
  metadata isolation, deterministic ordering, nested zones, and fail-closed
  type/prop validation.
- Added the admin route and accessible loading, error, reload, and save states;
  all Editor mutations use same-origin cookies and the existing CSRF header.
- Added separate Editor settings/pool, request COW context, Editor secret
  initialization/mount policy, health/readiness, Compose wiring, and route
  aliases. Control authorization remains a separate pool and credential.
- Added migration `027_001_qualify_content_function_columns` and JSONB encoding
  for generic composition add/update service calls.
- Added API response validation, adapter/UI/surface/packaging/health tests,
  serial backend integration coverage, and real Compose Playwright coverage.

### Files changed

- `apps/web/app/admin/sites/[siteId]/pages/[pageId]/edit/page.tsx`
- `apps/web/app/layout.tsx`; `apps/web/app/styles.css`; `apps/web/package.json`
- `apps/web/src/admin/api.ts`; `apps/web/src/admin/composition-editor.tsx`
- `apps/web/tests/surface.test.mjs`
- `compose.yaml`; `pnpm-workspace.yaml`; `pnpm-lock.yaml`
- `infra/nginx/nginx.conf`; `infra/apache/slaif-agent-site.conf`
- `packages/composition-schema/src/index.ts`
- `packages/composition-schema/src/puck-adapter.ts`
- `packages/composition-schema/tests/puck-adapter.test.ts`
- `services/backend/src/slaif_agent_site/content_model/composition_models.py`
- `services/backend/src/slaif_agent_site/content_model/service.py`
- `services/backend/src/slaif_agent_site/control_api/site_authority.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/027_001_qualify_content_function_columns.py`
- `services/backend/src/slaif_agent_site/editor_api/{__init__.py,__main__.py,app.py,config.py,database.py,composition_http.py,content_http.py,item_http.py,media_http.py,nav_theme_http.py,page_http.py,view_http.py}`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_control_database_integration.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/unit/{test_control_database.py,test_foundation_contract.py,test_health_apps.py}`
- `tests/e2e/{governance.spec.ts,support.ts}`
- `tests/packaging/{test_compose_policy.py,test_edge_contract.py,test_local_secrets.py}`
- `tests/repository/test_repository_policy.py`
- `tools/check_repository.py`; `tools/compose/verify.py`; `tools/local_secrets/initialize.py`
- `docs/{API.md,CONFIGURATION.md,DATABASE_CONNECTIONS.md,DATABASE_ROLES.md,DEPLOYMENT.md,SERVICE_AUTHORITY.md}`
- `THIRD_PARTY_NOTICES.md`
- Exact activated `oap/active` and `oap/orders/068-a-puck-editor-ui.md` transcript bytes.

## Acceptance-criteria evidence

### Criterion 1 — Trusted Puck dependency and catalog

- PASS. `@measured/puck@0.20.2` is pinned in the web manifest and frozen lock;
  package metadata was verified as MIT and compatible with React 19. The
  catalog is built only from the existing trusted component definitions.
- PASS. The root UUID override pins the Puck-transitive UUID dependency to
  `11.1.1`; dependency review and local production audit are green.

### Criterion 2 — Exact normalized/Puck round trip

- PASS. Five focused adapter tests cover catalog configuration, exact IDs,
  component types, schema versions, parents, slots, order, nested zones,
  deterministic reorder behavior, metadata isolation, unknown types, and
  forbidden props.
- PASS. The browser path loads a real nested normalized composition, saves via
  the human Editor API, reloads authoritative composition, and proves the
  Heading retains its Section parent, default slot/order, and no persisted
  `id` prop.

### Criterion 3 — Human Editor authority and server boundaries

- PASS. Browser mutations use same-origin session cookies and CSRF; no bearer
  capability, alternate auth store, CORS exception, or direct DB access was
  added.
- PASS. Control and Editor database pools/credentials are separate. The Editor
  runtime identity is checked per connection and its COW request context is
  closed/rolled back on route errors.
- PASS. Trusted component types, forbidden props, wrong-site/page resources,
  parent validation, private/no-store headers, and route policy remain server
  authoritative.

### Criterion 4 — Puck UI and persistence

- PASS. The admin route renders Puck with trusted components, visible drawer,
  nested composition, save/reload controls, and server error state. The full
  disposable smoke reaches it through NGINX and all six device projects pass.
- PARTIAL. The test does not claim that the legacy pinned DropZone drag itself
  is stable for nested movement. Add/move are seeded through the real human
  Editor API before Puck is opened; Puck then performs the trusted load/save/
  reload round trip. This is the remaining follow-up for exact UI gesture
  evidence.

### Criterion 5 — Existing architecture and scope retained

- PASS. No Agent mutation route, capability authority, publication, preview
  authority, workspace lifecycle, responsive preview, new catalog type, or
  composition storage table was added.
- PASS. Migration 027 only corrects existing page/composition function column
  qualification; it adds no storage schema.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED (`193 files`).
- `uv run --frozen mypy`: PASSED (`181` source files).
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED (`411 passed`).
- `uv run --frozen pytest services/backend/tests/integration`: PASSED (`98 passed`, serial run).
- `uv build --out-dir /tmp/slaif-agent-site-distributions-final`: PASSED.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED (`53 tests`).
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED (`0 issues`).
- `node --version`: PASSED (`v24.14.1`).
- `pnpm --version`: PASSED (`11.22.0`).
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm build`: PASSED.
- `pnpm test`: PASSED (workspace builds/tests and contract tests).
- `pnpm licenses list --json`: PASSED.
- `pnpm audit --prod`: PASSED (`0` vulnerabilities).
- All ten `uv run --frozen python -m slaif_agent_site.<process> --check`
  commands: PASSED.
- `python tools/compose/verify.py`: PASSED.
- `pnpm exec vitest run packages/composition-schema/tests/puck-adapter.test.ts`: PASSED (`5 tests`).
- `node --test apps/web/tests/surface.test.mjs`: PASSED (`9 tests`).
- `sudo sh tools/compose/smoke.sh slaif007puck`: PASSED (`compose-smoke: OK`),
  including setup, governance, Puck browser round trip, six device projects,
  edge headers, database-login/secret policy, readiness/recovery, Apache
  syntax, and 37 packaging/recovery tests. Disposable resources were cleaned.

## GitHub CI / required checks

Observed for implementation head
`8405e4c44c62903a96051b883aef1f06497b39af`:

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
- SUCCESS: Compose and edge packaging
- SUCCESS: Supply-chain evidence
- SUCCESS: Markdown
- SUCCESS: Mermaid
- SUCCESS: Dependency review
- SUCCESS: CodeQL

All required implementation-head checks were green before report publication.
The report-only commit may trigger a fresh check run; strategy independently
verifies report-head state.

## Local setup / dependencies

- Existing pinned stack retained; one required production dependency was added:
  `@measured/puck@0.20.2` (MIT), with its transitive UUID vulnerability
  remediated by the root `uuid: 11.1.1` override.
- uv `0.12.5`, Node `24.14.1`, and pnpm `11.22.0` were used.
- Passwordless `sudo` was used only for explicitly authorized disposable
  Docker/Compose smoke and local PostgreSQL test cleanup after an accidental
  parallel-test collision; no production data was involved.
- No production credentials, systems, data, capabilities, cookies, or private
  artifact URLs were accessed.

## Documentation

Updated API, configuration, database connection, database role, deployment,
and service authority documentation, plus generated third-party notices.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production secrets accessed: NO.
- Production systems accessed: NO.
- Required tests skipped/not run: NO for the completed claims; the exact nested
  Puck drag gesture is explicitly reported PARTIAL rather than passed.
- Scope deviation: NO; the separate Editor runtime is required wiring for the
  existing human Editor API and does not add Agent/publication authority.
- Extra objective PR: NO; PR #59 is the unique objective PR.
- Coding-agent merge: NO.
- Activated order/active edited: NO; exact strategic bytes were committed.
- Report commit changes only this new report: YES.

## Known limitations / blockers

The pinned `@measured/puck@0.20.2` legacy DropZone interaction emits a strict
CSP inline-style console warning and did not provide stable nested drag evidence
in the disposable Playwright run. The edge CSP was not weakened with
`unsafe-inline`; the exact warning is isolated in the Puck observer. A future
ordered remediation should either replace the legacy DropZone interaction with
a CSP-compatible stable Puck interaction or move to a reviewed compatible Puck
release. Publication, preview authority, workspace lifecycle, responsive
preview, promotion, and production readiness remain unimplemented.

## Recommended strategic follow-up

Strategy should independently review PR #59, especially the partial UI gesture
evidence and Puck/CSP limitation, before deciding whether to accept/merge
objective 068.
