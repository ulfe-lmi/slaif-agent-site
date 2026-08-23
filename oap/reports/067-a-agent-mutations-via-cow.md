# OAP Coding-Agent Report — 067-a

## Work order

- Identifier: `067-a`; work-order file: `oap/orders/067-a-agent-mutations-via-cow.md`
- Numeric objective: `067`
- PR mode: `CREATED_NEW_PR`

## Status

COMPLETE

`RESULT=OK`

## Executive summary

Replaced the five Agent API write stubs with capability-authenticated,
validated semantic create mutations executed inside the public
`asyncpg_cow_session` API. The server derives site, workspace/session, and
operation identity from the authenticated capability, reserves and completes
durable idempotency in the control plane, and writes an append-only audit
event in the same transaction. Agent-only COW-guarded semantic wrappers keep
the runtime role away from canonical/base/change tables, direct control-table
DML, reviewer authority, SQL/DDL, and lifecycle/publication authority.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#58](https://github.com/ulfe-lmi/slaif-agent-site/pull/58) — `OPEN`
- Base/head: `main` / `oap/067-agent-mutations`
- Starting remote main SHA: `e647fb850f963bf0e9793273b28fccf6e8811bc7`
- Implementation head SHA: `118a4b479bb5203fdd69663fdc12219ec43bc492`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commit pushed before report: `118a4b479bb5203fdd69663fdc12219ec43bc492`
- Report parent will equal the implementation SHA above.
- New PR this turn: YES; amended existing: NO; merge performed: NO
- PR was observed `MERGEABLE` with `CLEAN` merge state; coding agent did not merge.

## Changes made

- Added `POST` mutations for content types, fields, content items, pages, and
  page composition nodes.
- Added a COW-bound semantic executor that uses one Agent-owned pool
  connection and validates COW context before each semantic call.
- Added revision `025_001` with control-plane idempotency reservation/completion,
  audit evidence, and five site/resource/parent-validating COW wrappers.
- Added exact Agent least-privilege function declarations/grants and verifier
  coverage; no arbitrary control-table DML was granted.
- Added bounded idempotency-key validation, stable error codes, operation IDs,
  replay/mismatch behavior, and response persistence.
- Updated route-policy inventory, package/migration contract fixtures, API and
  authority documentation, and migration-head expectations.

## Files changed

- Runtime: `agent_api/agent_http.py`, `agent_api/database.py`,
  `agent_api/models.py`, `agent_state/mutations.py`,
  `agent_state/idempotency.py`, `content_model/service.py`,
  `content_model/composition_models.py`, `errors.py`.
- Database/policy: `db/alembic/versions/025_001_agent_mutation_surface.py`,
  `db/privileges.py`, `control_api/route_policy.py`.
- Tests: `tests/integration/test_agent_mutations.py`, migration-head and
  package-contract updates, Agent route inventory updates, and route-policy
  updates.
- Docs: `docs/API.md`, `docs/DATABASE_CONNECTIONS.md`,
  `docs/DATABASE_ROLES.md`, `docs/DEPLOYMENT.md`,
  `docs/FOUNDATION_INTEGRATION.md`, `docs/SERVICE_AUTHORITY.md`.
- Transcript: exact activated `oap/active` and
  `oap/orders/067-a-agent-mutations-via-cow.md` bytes were committed unchanged.

## Acceptance-criteria evidence

### Criterion 1 — Real COW-backed semantic mutations

- PASS. All five bounded routes return `201` and semantic records plus a UUID
  `operation_id`. `AgentCowContentModelService` binds calls to the active
  `CowSession`; it does not acquire a second ordinary pool connection.

### Criterion 2 — Workspace-only content type and canonical isolation

- PASS. Real PostgreSQL integration creates a workspace and capability through
  the actual Agent runtime role and authenticated HTTP route, observes the
  created type in the workspace overlay, observes the operation through the
  trusted reviewer helper, finds no row in `content.content_type_base`,
  discards the COW session through the trusted reviewer fixture, and confirms
  canonical remains unchanged.

### Criterion 3 — Durable idempotency and operation identity

- PASS. Same capability/key/route/digest replays the exact stored response and
  operation UUID without a second pending COW operation. A changed digest
  returns `409 IDEMPOTENCY_MISMATCH` without mutation. Missing and malformed
  keys have stable errors. Reservation, semantic write, audit, and completion
  are transactionally coupled; cancellation rolls back the reservation and
  leaves a clean reusable pool connection.

### Criterion 4 — Security and validation boundaries

- PASS. Site/workspace/operation identity is trusted server state. Type,
  field, item, page, parent, composition, scope, body, and path validation is
  enforced. Integration negatives prove Agent cannot read content base/change
  tables or reviewer/control lifecycle functions and cannot invoke a mutation
  wrapper without COW context. No public freeze, accept, discard, publish,
  capability/user-management, SQL/DDL, or infrastructure route was added.

### Criterion 5 — Documentation and contracts

- PASS. API response/idempotency/workspace-only semantics, connection and role
  boundaries, deployment surface, foundation limitations, route policy, and
  package/migration contract fixtures are updated truthfully. Documentation
  does not claim promotion, publication, full Agent API completion, or
  production readiness.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED.
- `uv run --frozen mypy`: PASSED (`177` source files).
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED (`411 passed, 26 subtests`).
- `uv run --frozen pytest services/backend/tests/integration`: PASSED (`97 passed`).
- `uv build --out-dir /tmp/slaif-agent-site-distributions-067a`: PASSED (wheel and sdist).
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED (`53 tests`).
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED (`16 diagrams`, `195 Markdown files`).
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED (`189 files`, 0 issues).
- `node --version`: PASSED (`v24.14.1`).
- `pnpm --version`: PASSED (`11.22.0`).
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED after the required build generated `.next` types.
- `pnpm test`: PASSED (build, workspace tests, and contract tests).
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- All ten `uv run --frozen python -m slaif_agent_site.<process> --check`
  commands: PASSED.
- `python tools/compose/verify.py`: PASSED.
- `sudo sh tools/compose/smoke.sh slaif007gci`: PASSED (`compose-smoke: OK`),
  including setup/governance/desktop/tablet/mobile browser projects, edge
  headers, database-login and secret policies, recovery, negative bootstrap,
  Apache syntax, and 35 repository tests. Disposable resources were cleaned
  by the smoke trap.

An initial concurrent Node invocation was not used as evidence: typecheck ran
before generated `.next` types and the concurrent test build contended for
Next's lock. The mandated commands were rerun sequentially and passed. The
initial `sudo sh tools/compose/smoke.sh slaif067ci` invocation was rejected by
the script's project-name safety validator before execution; the allowed
disposable project `slaif007gci` passed completely.

## GitHub CI / required checks

Observed for implementation head `118a4b479bb5203fdd69663fdc12219ec43bc492`:

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

All required implementation-head checks were green at drafting. The
report-only commit may trigger a fresh check run; strategy independently
verifies that report-head state.

## Local setup / dependencies

- Used the existing locked Python/Node dependencies only; no production
  dependency or hosted service was added.
- Used the repository's uv `0.12.5`, Node `24.14.1`, and pnpm `11.22.0`.
- Used passwordless `sudo` only for the explicitly authorized disposable
  Docker/Compose smoke because the unprivileged Docker socket is unavailable.
- No production credentials, systems, data, capabilities, cookies, or private
  artifact URLs were accessed.

## Documentation

Updated `docs/API.md`, `docs/DATABASE_CONNECTIONS.md`,
`docs/DATABASE_ROLES.md`, `docs/DEPLOYMENT.md`,
`docs/FOUNDATION_INTEGRATION.md`, and `docs/SERVICE_AUTHORITY.md` to describe
the bounded implementation and its remaining lifecycle/publication limits.

## Safety and scope confirmations

- Unrelated files changed: NO; all changes are the activated mutation,
  migration/privilege, contract/test, documentation, and transcript scope.
- Production secrets accessed: NO.
- Production systems accessed: NO.
- Required tests skipped/not run: NO for the ordered local and CI sets; the
  initial concurrent Node attempt was superseded by sequential passing runs.
- Scope deviation: NO; no promotion, publication, reviewer, identity,
  infrastructure, arbitrary SQL/DDL, or extra dependency work was added.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated order/active edited: NO; exact strategic bytes were preserved.
- Report commit changes only this new report: YES.

## Known limitations / blockers

This round does not implement workspace creation, freeze, review snapshot,
accept/selective accept, discard as a public Agent route, promotion,
publication, media binary upload, Puck UI, or the remaining Agent API surface.
The product remains pre-alpha and does not claim production readiness or
hostile-public-SaaS isolation.

## Recommended strategic follow-up

Strategy should independently review PR #58, this evidence, and report-head
checks before deciding whether to accept/merge or issue the next bounded order.
