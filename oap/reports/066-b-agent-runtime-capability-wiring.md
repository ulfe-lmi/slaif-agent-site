# OAP Coding-Agent Report — 066-b

## Work order

- Identifier: `066-b`
- Work-order file: `oap/orders/066-b-agent-runtime-capability-wiring.md`
- Numeric objective: `066`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Closed the 066-a runtime-wiring gap on the existing PR #57. A normally
constructed Agent API now owns a bounded capability-authentication dependency,
starts and stops it through the application lifespan, exposes its readiness,
and delegates only capability authentication through the AgentDatabase seam.

The real PostgreSQL/ASGI regression now creates the Agent API through its
production factory with disposable Control database settings, starts the app
lifespan, and exercises valid, malformed, unknown, wrong-secret, revoked,
expired, and unavailable-control-state cases without replacing
`app.state.database` after construction.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#57](https://github.com/ulfe-lmi/slaif-agent-site/pull/57)
- PR state: `OPEN`
- Base/head branches: `main` / `oap/066-capability-auth`
- Starting remote SHA for this continuation: `039583c6df5f893a07eb625ab4949edb97ebc532`
- Base remote SHA: `6552ee74e9046bb86e57d68acdef6acd0b0d1c07`
- Implementation head SHA: `0d75fe2664b47274bbce5d3130279b9152b3a4c9`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified after publication)
- Implementation commit pushed this round: `0d75fe2664b47274bbce5d3130279b9152b3a4c9`
- Prior 066-a implementation/report history preserved: yes
- Report parent must equal implementation SHA: yes
- New PR this turn: no
- Amended existing PR: yes, PR #57 only
- Merge performed: NO

## Changes made

- Added a narrow `CapabilityDatabase`/`AgentDatabaseAdapter` seam with
  lifecycle, readiness, and capability-authentication methods.
- Added the server-owned Agent-State capability dependency factory, with the
  existing Control database authority hidden behind an adapter exposing only
  capability authentication to Agent API code.
- Updated `agent_api.create_app()` to construct the dependency, install the
  AgentDatabase once, expose a database readiness probe, and manage start/stop
  through the normal FastAPI lifespan.
- Updated health and package-content contracts for the new runtime module.
- Replaced the 066-a test-only state substitution with production factory,
  configured disposable PostgreSQL, and lifecycle-managed ASGI evidence.
- Committed the exact strategic 066-b order and selector bytes unchanged.

## Files changed this round

- `oap/active` (strategic-authored selector committed byte-for-byte)
- `oap/orders/066-b-agent-runtime-capability-wiring.md` (strategic-authored order committed byte-for-byte)
- `services/backend/src/slaif_agent_site/agent_api/app.py`
- `services/backend/src/slaif_agent_site/agent_api/database.py`
- `services/backend/src/slaif_agent_site/agent_state/capability_auth.py`
- `services/backend/tests/integration/test_capability_authentication.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `services/backend/tests/unit/test_health_apps.py`

## Acceptance-criteria evidence

### Criterion 1 — Normally constructed and started Agent API authenticates a valid capability

- PASSED. The real PostgreSQL test calls `create_agent_app()` with configured
  disposable Control database settings, enters `app.router.lifespan_context`,
  and requests `/api/agent/v1/session` with a seeded capability.
- The response is HTTP 200 and exactly matches the seeded site, workspace,
  scopes, catalog, composition, and content-model context.

### Criterion 2 — Factory-wired 401/503 behavior remains fail-closed

- PASSED. The same lifecycle-managed app returns HTTP 401 for malformed,
  unknown, wrong-secret, revoked, and expired credentials.
- A second factory-created app configured against an unavailable disposable
  database returns HTTP 503; no token or database locator is present in the
  response.

### Criterion 3 — No post-construction database substitution

- PASSED. The regression test passes ordinary capability database settings to
  `create_agent_app()`, enters its normal lifespan, and never assigns
  `app.state.database` after construction.
- The production factory itself installs the selected bounded AgentDatabase
  before the app is returned.

### Criterion 4 — Bounded authority is preserved

- PASSED. Agent API code depends on the narrow capability protocol and has no
  raw asyncpg import, SQL, pool/native handle, user-management, mint/revoke,
  migration, publication, or infrastructure API.
- Existing 066-a two-table SELECT grant is unchanged; no new grant or schema
  migration was added in this continuation.
- Existing process-boundary and authority tests pass.

### Criterion 5 — Scope is limited to runtime wiring, tests, and OAP evidence

- PASSED. The diff changes only the activated continuation, Agent capability
  dependency/lifecycle wiring, package/health contracts, and its regression
  test. No dependency, migration, MCP, browser, content mutation, review,
  publication, or unrelated trust-boundary change appears.

## Local verification

- `uv --version`: PASSED — uv `0.12.5`.
- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED — 184 files formatted.
- `uv run --frozen mypy`: PASSED — 172 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`: PASSED — 407 tests, 26 subtests.
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED — 94 tests.
- Focused health/process/capability regression command: PASSED — 44 tests.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-066b.doVeIB`: PASSED — sdist and wheel built.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 53 tests.
- `python tools/check_repository.py`: PASSED — repository policy.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; 190 Markdown files scanned.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 184 files, 0 issues.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- Frozen package-aware process smoke for all ten prescribed modules using
  `uv run --frozen python -m ... --check`: PASSED — all ten returned `CHECK_OK`.

## GitHub CI / required checks

State observed for implementation head `0d75fe2664b47274bbce5d3130279b9152b3a4c9`:

- Analyze (actions): PASS
- Analyze (javascript-typescript): PASS
- Analyze (python): PASS
- CodeQL: PASS
- Compose and edge packaging: PASS
- Dependency review: PASS
- Detect supported languages: PASS
- Foundation PostgreSQL 14: PASS
- Foundation PostgreSQL 15: PASS
- Foundation PostgreSQL 16: PASS
- Foundation PostgreSQL 17: PASS
- Foundation PostgreSQL 18: PASS
- Markdown: PASS
- Mermaid: PASS
- Node contracts: PASS
- Python 3.12 quality and package: PASS
- Python 3.13 quality and package: PASS
- Python 3.14 quality and package: PASS
- Repository policy: PASS
- Supply-chain evidence: PASS
- All required checks green at drafting: YES.
- Report-only commit may trigger fresh checks; strategy must verify SELF independently.

## Local setup / dependencies

- Used uv `0.12.5`, Node `24.14.1`, and pnpm `11.22.0`.
- Used disposable local PostgreSQL fixtures; no production systems or data.
- No production dependency, lockfile, migration, hosted service, secret, or
  infrastructure change.
- Temporary package distributions were written under `/tmp` and not committed.

## Documentation

- No durable product documentation change was required by this runtime-wiring
  continuation.
- The immutable OAP report is the required evidence artifact.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no.
- Production systems accessed: no.
- Required tests skipped/not run: no.
- Scope deviation: no.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated order content edited by coding agent: NO.
- Active selector content edited by coding agent: NO.
- Report commit changes only this report: YES.

## Known limitations / blockers

- The generic `agent_api.__main__` check runner remains the existing health-only
  entrypoint shape; this continuation specifically closes the constructed
  Agent API factory/lifespan seam required by the order. A future process-level
  startup wiring order should reconcile that runner with the full factory if
  the deployment contract requires it.
- Agent content mutations, COW sessions, publication, review, and promotion
  remain outside this objective.

## Recommended strategic follow-up

Independently review PR #57, the 066-a limitation closure, report ancestry, and
the bounded capability dependency before acceptance/merge. Do not treat this
coding-agent report or green CI as strategic acceptance.
