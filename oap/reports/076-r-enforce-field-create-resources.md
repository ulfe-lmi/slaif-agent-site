# OAP Coding-Agent Report — 076-r

## Work order

- Identifier: `076-r`
- Work-order file: `oap/orders/076-r-enforce-field-create-resources.md`
- Numeric objective: `076`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Implemented the ordered trusted-database resource enforcement and concurrency
safety for Agent field-definition creation. The existing 14-column Agent
wrapper now validates and locks the visible ACTIVE parent type, reads the
trusted COW workspace, enforces persisted parent ID/key allowlists and the
per-type field limit, and serializes the count-plus-insert decision with a
transaction advisory lock. Rejected calls do not leave COW, idempotency,
audit, or quota residue. The pre-044 wrapper body/grants are restored on
downgrade and enforcement returns on upgrade.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72)
- PR state: `OPEN`; base `main`; head `oap/076-agent-model-content-semantics`
- Starting remote PR/report head: `cbbe4d9e47744e9ddb187cecd84a304cc5ae2b7d`
- Starting base `origin/main`: `0e83b26bf9a9f63bff6756d65cbfd527d215ec51`
- Implementation head SHA: `422e240831dabdc596a18f6684ea38744f66d06c`
- Implementation commit pushed: `422e240831dabdc596a18f6684ea38744f66d06c`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- Current remote status before report publication: `MERGEABLE`, `CLEAN`
- New PR this turn: NO; amended existing PR: YES; merge performed: NO

## Changes made

- Replaced the 044 field-definition Agent wrapper with the same established
  14-column return shape and explicit `site_id` insert.
- Required trusted COW context from `app.session_id`, locked the visible
  same-site ACTIVE parent type, and invoked the owner-only typed resource
  helper.
- Enforced nonempty persisted parent ID and key allowlists and
  `max_fields_per_type` over the workspace COW overlay.
- Added a deterministic transaction advisory lock over workspace and parent
  type before count and insert, making a one-slot race exactly one success and
  one stable resource-limit denial.
- Restricted the upgraded wrapper to `slaif_agent_runtime` and restored the
  pre-044 field wrapper body/grants in downgrade order.
- Added real Agent HTTP, direct runtime-wrapper, migration round-trip, replay,
  residue, isolation, and two-connection PostgreSQL proof.

## Files changed

- `services/backend/src/slaif_agent_site/db/alembic/versions/044_001_agent_resource_constraints.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `oap/orders/076-r-enforce-field-create-resources.md` (exact strategic bytes)
- `oap/active` (exact active identifier `076-r`)

## Acceptance-criteria evidence

### Criterion 1

Passed. A real capability creates the parent and fields through Agent HTTP
under matching persisted parent ID/key constraints. The sequential maximum
allows the final slot and rejects the next with `QUOTA_EXCEEDED`; the rejected
request leaves durable idempotency/audit/quota counts, COW operation count,
and visible fields unchanged.

### Criterion 2

Passed. Direct `slaif_agent_runtime` wrapper calls reject an ID-disallowed
parent and a key-disallowed parent after bypassing HTTP, with no additional
COW operation.

### Criterion 3

Passed. Two distinct runtime connections and operation IDs racing one remaining
slot produce exactly one created field and one
`AGENT_RESOURCE_FIELD_DEFINITION_LIMIT` denial, one visible field, and one
additional COW operation.

### Criterion 4

Passed. The locked parent lookup requires the requested site, persisted parent
ID, and ACTIVE status. Direct proof covers wrong site/type, deleted parent,
and another workspace's parent; all fail closed and canonical field storage
remains unchanged.

### Criterion 5

Passed. HTTP create/replay responses are byte-identical; the replay does not
create a second visible field or additional durable residue. Migration
downgrade restores the pre-044 signature/body/grant state, and upgrade
re-enforces the field limit while COW remains enabled.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 255 files.
- `uv run --frozen mypy`: PASSED — 241 source files.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -k field_create_resources_are_db_enforced_and_concurrency_safe -q`:
  PASSED — 1 test.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -k content_type_create_resource_limits_are_db_serialized -q`:
  PASSED — 1 test.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -q`:
  PASSED — 10 tests.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`:
  PASSED — 514 tests, 26 subtests.
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED — 125
  tests in 815.77s.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 58
  tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 344 files, 0
  issues.
- `node --version; pnpm --version`: PASSED — Node 24.14.1, pnpm 11.22.0.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: initial parallel invocation preceded Next type generation;
  serialized rerun PASSED.
- `pnpm test`: initial parallel invocation collided with the standalone Next
  build lock; serialized rerun PASSED, including package, web, worker, and
  contract tests.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `git diff --check`: PASSED.
- Local Compose/CI simulation: NOT RUN; remote CI was inspected as required by
  the order.

## GitHub CI / required checks

Implementation SHA `422e240831dabdc596a18f6684ea38744f66d06c` passed fresh CI
run `33347810015` and CodeQL run `33347810022`:

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
- Field update/delete, audit schema, HTTP/OpenAPI shape, dependencies,
  workflows, cleanup, and unrelated hardening: NOT CHANGED.
- Activated order and active file were committed with exact bytes: YES.
- Report commit changes only this report: YES.
- Post-report push: NONE will follow report publication.

## Completion condition

Objective 076 / PR #72 may be declared complete by strategy only when this
report-only commit is the verified remote PR head, all required checks for that
head are green, and strategy independently reviews and accepts the objective.
The coding agent does not merge or accept the PR.
