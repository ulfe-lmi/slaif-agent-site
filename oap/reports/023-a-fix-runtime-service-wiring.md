# OAP Coding-Agent Report — 023-a

## Work order

- Identifier: `023-a`
- Work-order file: `oap/orders/023-a-fix-runtime-service-wiring.md`
- Numeric objective: `023`
- PR mode: CREATED_NEW_PR

## Status

COMPLETE

## Executive summary

Implemented the runtime service wiring for content-model operations. `ControlDatabase` now exposes a semantic `ContentModelService`; Editor API owns its database lifecycle and sets both database and service state; Agent API uses an owned bounded adapter and exposes the same service; duplicate browser routing was removed. Added integration evidence for runtime reachability and real PostgreSQL COW triplets.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#55](https://github.com/ulfe-lmi/slaif-agent-site/pull/55)
- PR state: OPEN at report drafting
- Base/head branches: `main` / `oap/023-a-fix-runtime-service-wiring`
- Starting remote SHA: `7bc7b431bc7beed9355bc9ab7a3ac25dba5b92d8`
- Implementation head SHA: `39143757931a94cc10d8ae850091370c1b8a6cad`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commits pushed before report: yes
- Report parent equals implementation SHA: yes
- New PR this turn: yes
- Amended existing PR: no
- Merge performed: NO

## Changes made

- Added `ControlDatabase.content_model_service()` and declared it on the control database protocol.
- Created an Agent-owned bounded database adapter that exposes only the semantic content-model service and fails closed when unstarted.
- Wired the service into Editor API and Agent API app state.
- Gave Editor API an explicit owned database lifespan.
- Removed the duplicate Agent API browser router include.
- Repaired the existing COW integration test to use the authoritative owner connection before enabling COW.
- Added runtime reachability/fail-closed integration proof.
- Updated bounded repository-policy and package-content expectations.
- Corrected Markdown lint issues in the existing MVP closure audit without changing its conclusions.

## Files changed

- `services/backend/src/slaif_agent_site/control_api/database.py`
- `services/backend/src/slaif_agent_site/agent_api/app.py`
- `services/backend/src/slaif_agent_site/agent_api/database.py`
- `services/backend/src/slaif_agent_site/editor_api/app.py`
- `services/backend/tests/integration/test_runtime_service_wiring.py`
- `services/backend/tests/integration/test_content_model_cow.py`
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `services/backend/tests/unit/test_health_apps.py`
- `services/backend/tests/unit/test_process_entrypoints.py`
- `oap/MVP-CLOSURE-AUDIT.md`
- `tools/check_repository.py`

## Acceptance-criteria evidence

### All existing tests pass

- Local Python quality/unit gates passed as listed under local verification.
- Focused real PostgreSQL bootstrap/auth integration suite passed 24 tests.

### ControlDatabase has `content_model_service()`

- Implemented in `control_api/database.py`.
- Unit public-boundary test now includes it.

### Agent API includes browser_router exactly once

- Source inspection shows exactly one `app.include_router(browser_router)` call.
- Existing route inventory test passes.

### Both editor and agent apps set `app.state.content_model_service`

- New `test_runtime_service_wiring.py` constructs both apps, verifies each state object is a `ContentModelService`, invokes a read operation, and proves unavailable-pool behavior is classified unavailable rather than leaking driver detail.

### No runtime AttributeError when accessing content-model routes

- Runtime reachability proof obtains the service from app state in both processes.
- The operation reaches the bounded service boundary and fails closed only because the disposable pool is intentionally unstarted.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED.
- `uv run --frozen mypy`: PASSED — 170 source files.
- `env -u SLAIF_MODE -u SLAIF_CONTROL_MODE -u SLAIF_CONTROL_DSN uv run --frozen pytest services/backend/tests/unit -q`: PASSED — 354 tests.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 53 tests.
- `python tools/check_repository.py`: PASSED after policy recognized future orders 024–035 as not yet activated.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; 187 Markdown files scanned.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 181 files, zero issues.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint && pnpm format:check && pnpm typecheck && pnpm test && pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED; output retained outside the repository.
- `uv run --frozen pytest services/backend/tests/integration/test_content_model_cow.py services/backend/tests/integration/test_runtime_service_wiring.py -q`: PASSED — 2 tests against real PostgreSQL.
- `uv run --frozen pytest services/backend/tests/integration/test_database_bootstrap.py services/backend/tests/integration/test_control_auth_http_integration.py -q`: PASSED — 24 tests.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED for sdist and wheel.

## GitHub CI / required checks

- State observed for implementation head `39143757931a94cc10d8ae850091370c1b8a6cad`.
- Analyze (actions): SUCCESS.
- Analyze (javascript-typescript): SUCCESS.
- Analyze (python): SUCCESS.
- CodeQL: SUCCESS.
- Compose and edge packaging: SUCCESS.
- Dependency review: SUCCESS.
- Detect supported languages: SUCCESS.
- Foundation PostgreSQL 14–18: SUCCESS ×5.
- Markdown: SUCCESS.
- Mermaid: SUCCESS.
- Node contracts: SUCCESS.
- Python 3.12 quality and package: SUCCESS.
- Python 3.13 quality and package: SUCCESS.
- Python 3.14 quality and package: SUCCESS.
- Repository policy: SUCCESS.
- Supply-chain evidence: SUCCESS.
- All required green at drafting: YES.
- Report-only commit may trigger fresh checks; strategy verifies SELF independently.

## Local setup / dependencies

- No production dependency changes.
- Used repository-pinned Python/Node toolchains and local disposable PostgreSQL fixtures.
- Temporary Markdownlint and Mermaid CLI execution used approved pinned tools outside dependency changes.
- Built distributions were written to `/tmp`, not committed.

## Documentation

- Fixed lint structure in `oap/MVP-CLOSURE-AUDIT.md`; no product documentation change was required by the order.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no.
- Production systems accessed: no.
- Required tests skipped/not run: no.
- Scope deviation: no.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated order edited: NO.
- Active selector edited by coding agent: NO.
- Report commit changes only this report: YES.

## Known limitations / blockers

- None within this order's bounded wiring scope.
- Capability authentication, COW mutation sessions, publication, and remaining MVP behavior remain governed by later strategic work orders.

## Recommended strategic follow-up

- Independently review PR #55 and merge if accepted.
