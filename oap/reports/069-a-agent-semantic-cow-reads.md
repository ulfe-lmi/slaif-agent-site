# OAP Coding-Agent Report — 069-a

## Work order

- Identifier: `069-a`
- Work-order file: `oap/orders/069-a-agent-semantic-cow-reads.md`
- Numeric objective: `069`
- PR mode: `CREATED_NEW_PR`

## Status

COMPLETE

## Executive summary

Implemented the capability-authenticated Agent semantic-read contract on one
request-scoped foundation COW connection. The public Agent GET routes now read
the capability's own workspace overlay with canonical fallback, reject
cross-site and cross-workspace resource substitution, and do not use the
ordinary application `ContentModelService` or create mutation state.

The strategic transcript insertion was preserved exactly: active `069-a`, the
new 069 order, and inert future orders 070–078 are present on the objective PR.
No later objective was implemented or activated.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#60](https://github.com/ulfe-lmi/slaif-agent-site/pull/60)
- PR state: `OPEN`, non-draft, `MERGEABLE`
- Base/head: `main` / `oap/069-agent-semantic-reads`
- Starting remote SHA: `b6946d84b72b44f15548235e3936d4e4202c587e`
- Implementation head SHA: `ce45513f8f4d280a492e939563f8884f7539dca1`
- Implementation commits pushed before report:
  - `9cbb2f3143c7057ca37d3830a7d8fa7a32f3d080` — activate 069 transcript
  - `ce45513f8f4d280a492e939563f8884f7539dca1` — implementation
- Report publication commit: `SELF`
- New PR this turn: YES, exactly one
- Amended existing PR: NO
- Merge performed: NO

## Changes made

- Added `AgentSemanticReadService` and `execute_agent_read`, which bind all
  Agent semantic reads to one `asyncpg_cow_session` using the authenticated
  capability workspace UUID. The service reuses the same COW connection for
  every wrapper call and maps foreign/missing resources to stable not-found
  outcomes.
- Replaced all five existing Agent GET implementations that used the ordinary
  content service with the Agent COW read executor.
- Added the two required public routes:
  - `GET /api/agent/v1/content-model/types/{type_id}/fields`
  - `GET /api/agent/v1/pages/{page_id}/components`
- Added migration `029_001_agent_semantic_read_surface` with seven narrow
  owner-defined `SECURITY DEFINER` wrappers, fixed `search_path = pg_catalog`,
  active-workspace/site binding, parent/resource checks, overlay-view reads,
  canonical fallback, ordering, and existing deleted filtering.
- Extended privilege verification so `slaif_agent_runtime` receives only the
  seven explicit read-wrapper EXECUTEs plus its existing bounded mutation and
  idempotency/audit functions.
- Updated route policy, OpenAPI route fixtures, migration expectations,
  repository OAP future-range policy, Agent integration proof, and durable
  Agent API/database/security documentation.

## Files changed

- `services/backend/src/slaif_agent_site/agent_state/reads.py`
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py`
- `services/backend/src/slaif_agent_site/agent_api/app.py`
- `services/backend/src/slaif_agent_site/agent_api/database.py`
- `services/backend/src/slaif_agent_site/control_api/route_policy.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/029_001_agent_semantic_read_surface.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- migration, route, repository-policy, and runtime regression tests
- `docs/API.md`, `docs/DATABASE_CONNECTIONS.md`, `docs/DATABASE_ROLES.md`,
  `docs/SERVICE_AUTHORITY.md`
- strategic transcript files committed unchanged in `9cbb2f3`

## Acceptance-criteria evidence

### Criterion 1 — Public readback of all 067 families

- PASSED. Real PostgreSQL/public HTTP integration posts content type, field,
  content item, page, and composition through Agent mutations, then reads
  types, type detail, fields, items, pages, components, and media through the
  capability-authenticated Agent API. The focused route test also proves the
  immediate readback of the created chain.

### Criterion 2 — COW overlay, fallback, tombstone/filter behavior

- PASSED. The integration proof seeds canonical type, field, item, page,
  composition, and media rows; modifies the canonical type in the Agent COW
  workspace; observes the overlay label publicly while owner inspection still
  observes the canonical label; and observes unchanged canonical families as
  fallback. Wrapper queries use the foundation-managed COW views and preserve
  active/deleted filters and deterministic ordering.

### Criterion 3 — Site/workspace isolation and non-leaking errors

- PASSED. Site-A capability reads of site-B type/page resources return stable
  `RESOURCE_NOT_FOUND` without foreign IDs in the response. Two workspaces on
  one site use the deliberately colliding `workspace-type` key; each sees only
  its own overlay. The site/workspace COW operation lists remain isolated.

### Criterion 4 — Least privilege and real identity

- PASSED. The public app uses the Agent pool initialized as
  `slaif_agent_login` with only `slaif_agent_runtime`. Integration SQL proves
  every read wrapper is owned by `slaif_owner`, executable by
  `slaif_agent_runtime`, not executable by Editor or Control, and not PUBLIC.
  Generic Editor/Control content functions, `control.slaif_agent_require_cow_site`,
  content base/change tables, and direct SQL outside the wrapper surface remain
  denied.

### Criterion 5 — No durable read mutation and context cleanup

- PASSED. Before/after public GET counts for `control.agent_idempotency` and
  `audit.agent_mutation` are identical; foundation operation lists do not gain
  a read operation. Success, foreign-resource failure, malformed identifiers,
  cancellation, and pool reuse all leave no transaction or COW settings on the
  released connection. GETs use no idempotency key and no mutation audit path.

### Criterion 6 — Existing behavior remains green

- PASSED. The full Agent mutation integration file remains green, the full
  101-test PostgreSQL integration suite passes, and existing human/editor,
  migration, privilege, route, packaging, and web gates pass.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED; 199 files formatted.
- `uv run --frozen mypy`: PASSED; 187 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED; 412 tests.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED; 101 tests.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED; sdist and wheel.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED; 54 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED; 16 diagrams in 3 files and 214 Markdown files scanned.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED; 208 files, 0 issues.
- Direct `python -m slaif_agent_site.<process> --check`: FAILED before startup for all ten commands because system `/usr/bin/python` lacked the project import path (`ModuleNotFoundError`). This was an environment invocation issue, not an application failure.
- `uv run --frozen python -m slaif_agent_site.control_api --check`, `editor_api`,
  `agent_api`, `render_api`, `mcp_adapter`, `media_service`, `review_worker`,
  `scheduler`, `media_gc`, and `bootstrap`: PASSED; all ten returned `CHECK_OK`.
- `node --version`: PASSED; `v24.14.1`.
- `pnpm --version`: PASSED; `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED; recursive build/tests and contract tests.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `git diff --check`: PASSED.

## GitHub CI / required checks

Observed for literal implementation head `ce45513f8f4d280a492e939563f8884f7539dca1`:

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

All observed required checks were green at report drafting. The report-only
commit may trigger a fresh check set; strategy independently verifies SELF.

## Local setup / dependencies

Used the existing frozen `uv` environment, Node 24.14.1, pnpm 11.22.0, and
the repository's disposable PostgreSQL integration fixtures. No new production
dependency, hosted service, credential, production resource, or lockfile was
added or accessed.

## Documentation

Updated the Agent API route/scope contract, Agent connection lifecycle and
identity boundary, PostgreSQL role grants, and service-authority wording to
describe workspace overlay precedence, canonical fallback, least privilege,
and read-state cleanup. No architecture or constitution file was edited.

## Safety and scope confirmations

- Unrelated files changed: NO. Changes are bounded to Agent semantic reads,
  required migration/privilege metadata, transcript renumbering, proof, docs,
  and regression expectations.
- Production secrets accessed: NO.
- Production systems accessed: NO.
- Required tests skipped/not run: NO for the claimed local/CI sets. The direct
  system-Python process spelling failed before startup; the frozen project
  equivalent passed all ten process checks.
- Scope deviation: NO. No later objective 070–078 behavior was implemented.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated order/active content edited: NO; exact strategic bytes were
  committed unchanged.
- Final report commit changes only this report: YES.

## Known limitations / blockers

- The Agent read surface remains bounded to the exact seven wrapper families
  and routes in this order. No media upload, renderer, browser worker,
  freeze/review, promotion, or publication behavior is added.
- The direct process smoke command requires the frozen project runner in this
  checkout because the system interpreter does not expose the package path.
- Strategy must independently review and merge; this report does not mean
  accepted, approved, or merged.

## Recommended strategic follow-up

Independently review PR #60 against order 069-a, verify the report SELF child
and fresh report-head checks, then choose merge or continuation. No coding-agent
follow-up order is selected here.

RESULT=OK
