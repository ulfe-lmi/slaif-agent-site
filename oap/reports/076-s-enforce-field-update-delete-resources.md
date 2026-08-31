# OAP Coding-Agent Report — 076-s

## Work order

- Identifier: `076-s`
- Work-order file: `oap/orders/076-s-enforce-field-update-delete-resources.md`
- Numeric objective: `076`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Implemented the ordered trusted-database resource and optimistic-version
enforcement for Agent field-definition update/delete. Both wrappers now take a
deterministic workspace/type/field transaction lock, lock the visible field
under an ACTIVE same-site parent, check the expected definition version after
locking, enforce persisted parent ID/key constraints, and preserve dependency
and delete-enabled guards. The upgraded wrappers emit the established typed
15-column Agent row shape. Downgrade restores the pre-044 wrappers and grants;
upgrade restores guarded enforcement.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72)
- PR state: `OPEN`; base `main`; head `oap/076-agent-model-content-semantics`
- Starting remote PR/report head: `2acc1bef79c056a96e21b6258321c4cefcd006d0`
- Starting base `origin/main`: `0e83b26bf9a9f63bff6756d65cbfd527d215ec51`
- Implementation head SHA: `f27e8336cbd73cc7c13802efed74f0619a7a7b16`
- Implementation commit pushed: `f27e8336cbd73cc7c13802efed74f0619a7a7b16`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- Current remote status before report publication: `MERGEABLE`, `CLEAN`
- New PR this turn: NO; amended existing PR: YES; merge performed: NO

## Changes made

- Replaced the Agent field-definition update and delete wrappers in
  `044_001_agent_resource_constraints.py` with guarded SECURITY DEFINER
  functions using the fixed `pg_catalog` search path.
- Parsed workspace identity only from trusted `app.session_id`, acquired the
  deterministic workspace/type/field advisory lock, and locked the exact
  visible field joined to an ACTIVE same-site parent before version checks.
- Enforced persisted parent ID/key allowlists through the owner-only resource
  helper and retained fail-closed stale, wrong-site/type/field, and deleted
  parent behavior.
- Preserved field semantic update behavior, `delete_enabled=false` denial,
  visible-item dependency denial, COW deletion tombstones, and exact typed
  Agent return rows.
- Restricted upgraded wrappers to `slaif_agent_runtime`; downgrade recreates
  the exact pre-044 wrapper bodies/grants in dependency-safe order.
- Added real Agent HTTP/direct-wrapper, replay/audit/quota, isolation,
  dependency, migration round-trip, and two-connection race proof.

## Files changed

- `services/backend/src/slaif_agent_site/db/alembic/versions/044_001_agent_resource_constraints.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `oap/orders/076-s-enforce-field-update-delete-resources.md` (exact strategic bytes)
- `oap/active` (exact active identifier `076-s`)

## Acceptance-criteria evidence

### Criterion 1

Passed. A real capability creates the parent and field through Agent HTTP,
PATCHes the field under matching parent ID/key constraints, receives the exact
updated action/record/version response, replays byte-identically, and receives
`IDEMPOTENCY_MISMATCH` for changed-body reuse without additional durable or
COW residue.

### Criterion 2

Passed. Direct runtime-wrapper calls reject ID-disallowed and
key-disallowed parents, wrong site/type/field, a deleted parent, and another
workspace’s field without disclosure or a COW operation. The wrapper’s ACTIVE
same-site parent predicate covers all non-active parent states.

### Criterion 3

Passed. Public and direct deletion with `delete_enabled=false` are denied.
After enabling deletion, Agent HTTP deletes the exact-version field, produces
`FIELD_DEFINITION_DELETED`, increments delete quota and audit/idempotency only
once, and leaves mutation quota unchanged. The field is absent from the
workspace overlay, absent from other workspaces, and absent from canonical
base storage; replay is byte-identical.

### Criterion 4

Passed. Two distinct PostgreSQL connections and operation IDs racing the same
field at definition version 1 produce exactly one update and one
`STALE_DEFINITION` denial, one version increment, and one additional COW
operation. The final label is one of the two submitted labels.

### Criterion 5

Passed. A visible content item using the field blocks deletion with
`FIELD_DEPENDENCIES` and leaves the field unchanged. Migration downgrade
restores the pre-044 field update/delete signatures, bodies, and effective
grants; upgrade restores guarded enforcement and runtime-only privileges with
COW enabled.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 255 files.
- `uv run --frozen mypy`: PASSED — 241 source files.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -k field_update_delete_resources_are_db_enforced_and_concurrency_safe -q`:
  PASSED — 1 test.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -k content_type_create_resource_limits_are_db_serialized -q`:
  PASSED — 1 test.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -q`:
  PASSED — 11 tests.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`:
  PASSED — 514 tests, 26 subtests.
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED — 126
  tests in 818.36s.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED.
- `python -m compileall -q tools tests/repository services/backend`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 58
  tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 346 files, 0
  issues.
- `node --version; pnpm --version`: PASSED — Node 24.14.1, pnpm 11.22.0.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED in the serialized gate.
- `pnpm test`: PASSED in the serialized gate, including package, web,
  browser-worker, and contract tests.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `git diff --check`: PASSED.
- Local Compose/CI simulation: NOT RUN; fresh remote CI was inspected instead.

During focused development, preliminary wrapper probes exposed and corrected
the established row-order mismatch, an unqualified PL/pgSQL column reference,
and a test fixture delete-quota setup. The final focused and complete gates
listed above pass with no remaining local failure.

## GitHub CI / required checks

Implementation SHA `f27e8336cbd73cc7c13802efed74f0619a7a7b16` passed fresh CI
run `33350704288` and CodeQL run `33350704270`:

- `Repository policy`: SUCCESS
- `Detect supported languages`: SUCCESS
- `Node contracts`: SUCCESS
- `Analyze (actions)`: SUCCESS
- `Analyze (python)`: SUCCESS
- `Analyze (javascript-typescript)`: SUCCESS
- `Python 3.12 quality and package`: SUCCESS
- `Python 3.13 quality and package`: SUCCESS
- `Python 3.14 quality and package`: SUCCESS
- `Foundation PostgreSQL 14`: SUCCESS
- `Foundation PostgreSQL 15`: SUCCESS
- `Foundation PostgreSQL 16`: SUCCESS
- `Foundation PostgreSQL 17`: SUCCESS
- `Foundation PostgreSQL 18`: SUCCESS
- `Compose and edge packaging`: SUCCESS
- `Supply-chain evidence`: SUCCESS
- `Markdown`: SUCCESS
- `Mermaid`: SUCCESS
- `Dependency review`: SUCCESS
- `CodeQL`: SUCCESS

All 20 required checks were green before report publication.

## Local setup / dependencies

Used the existing frozen uv and pnpm environments and disposable local
PostgreSQL 16.15. No dependency, migration revision, service, Compose, or
production configuration outside the ordered 044 revision changed.

## Documentation

No product/API/architecture documentation changed; this order forbids
documentation and governance changes beyond the exact strategic order and
active activation.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production secrets accessed: NO.
- Production systems accessed: NO.
- Required ordered tests skipped/not run: NO.
- Scope deviation: NO.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Audit schema, HTTP/OpenAPI shape, dependencies, workflows, cleanup, and
  unrelated hardening: NOT CHANGED.
- Activated order and active file were committed with exact bytes: YES.
- Report commit changes only this report: YES.
- Post-report push: NONE will follow report publication.

## Completion condition

Objective 076 / PR #72 may be declared complete by strategy only when this
report-only commit is the verified remote PR head, all required checks for that
head are green, and strategy independently reviews and accepts the objective.
The coding agent does not merge or accept the PR.
