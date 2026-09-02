# OAP Coding-Agent Report — 076-q

## Work order

- Identifier: `076-q`
- Work-order file: `oap/orders/076-q-enforce-type-update-delete-resources.md`
- Numeric objective: `076`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Implemented the ordered trusted-database resource enforcement and conflict-safe
update/delete slice for content types. Both Agent wrappers now lock the visible
ACTIVE type, recheck the expected definition version after locking, invoke the
owner-only resource helper, enforce persisted ID/key allowlists, and fail closed
for disabled deletes. Update/delete races are serialized so one stale operation
cannot also commit. The focused and complete Agent mutation proofs pass.

The implementation is complete, but the fresh remote workflow has one unrelated
failure in the existing governance browser contract. The PR remains open and
must not be declared complete until that required check is green.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72)
- PR state: `OPEN`; base `main`; head `oap/076-agent-model-content-semantics`
- Starting remote PR/report head: `4c148cfd2f4e2fd5770ab70ae0a9d67242493de4`
- Starting base `origin/main`: `0e83b26bf9a9f63bff6756d65cbfd527d215ec51`
- Implementation head SHA: `6e89e1b22ad3fc7ece312a8d74f7fc6e7c59c432`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- Implementation commits pushed before report: `6e89e1b22ad3fc7ece312a8d74f7fc6e7c59c432`
- New PR this turn: NO; amended existing PR: YES; merge performed: NO

## Changes made

- Extended migration `044_001_agent_resource_constraints.py` with guarded
  content-type update/delete wrappers.
- Added a transaction-scoped type-definition advisory lock in addition to the
  visible-row `FOR UPDATE` lock, which closes same-workspace first-touch races.
- Enforced persisted type ID/key constraints after the locked version check.
- Added fail-closed `delete_enabled=false` handling while preserving dependency
  denial and leaving `max_deletes` to the later audit/quota round.
- Restored the pre-044 update/delete bodies and grants in downgrade order, then
  restored type-create and removed the helper; upgrade/downgrade/upgrade proof
  passes with COW enabled.
- Added real PostgreSQL Agent HTTP/direct-wrapper/idempotency/quota/audit,
  cross-site, dependency, and two-connection race coverage.

## Files changed

- `services/backend/src/slaif_agent_site/db/alembic/versions/044_001_agent_resource_constraints.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `oap/orders/076-q-enforce-type-update-delete-resources.md` (strategic bytes
  committed unchanged)
- `oap/active` (strategic bytes committed unchanged)

## Acceptance-criteria evidence

### Criterion 1

Passed. A real capability creates through Agent HTTP, updates through Agent HTTP
under matching ID/key allowlists, returns the expected version/action/resource/
status, replays byte-identically, and rejects changed payload under the same
idempotency key without extra COW/audit residue.

### Criterion 2

Passed. Direct runtime wrapper calls deny ID-disallowed/key-allowed and
ID-allowed/key-disallowed cases after the HTTP boundary is bypassed. Stale,
wrong-site, and foreign-type calls fail closed; denied calls leave no COW
operation.

### Criterion 3

Passed locally. Public and direct delete calls are denied when
`delete_enabled=false`; enabling it permits exact-version Agent HTTP deletion,
increments only delete quota among mutation/delete quotas, records one delete
action, creates the workspace tombstone, and leaves canonical/other-workspace
state unchanged.

### Criterion 4

Passed. Two distinct PostgreSQL connections racing the same workspace/type and
expected version produce exactly one success and one `STALE_DEFINITION` denial,
one version increment, and one COW operation.

### Criterion 5

Passed locally. Existing item dependencies deny deletion; stale and wrong-site/
type calls fail closed; downgrade and re-upgrade restore the pre-044 and guarded
function/grant states and re-enable resource enforcement.

## Local verification

- `PGHOST=127.0.0.1 PGDATABASE=postgres PGUSER=postgres psql -Atqc 'SELECT version()'`:
  PASSED — PostgreSQL 16.15.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py::test_content_type_update_resources_are_db_enforced_and_idempotent services/backend/tests/integration/test_agent_mutations.py::test_content_type_delete_resource_and_dependency_guards_are_atomic services/backend/tests/integration/test_agent_mutations.py::test_content_type_update_version_lock_allows_one_racing_operation -q`:
  PASSED — 3 tests.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -q`:
  PASSED — 9 tests.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 255 files.
- `uv run --frozen mypy`: PASSED — 241 source files.
- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`:
  PASSED — 514 tests, 26 subtests.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 58
  tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 342 files, 0
  issues.
- `node --version; pnpm --version`: PASSED — Node 24.14.1, pnpm 11.22.0.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: first parallel invocation failed before Next generated
  `.next/types`; required serialized rerun PASSED.
- `pnpm test`: first parallel invocation hit the Next build lock; required
  serialized rerun PASSED, including package, web, browser-worker, and contract
  tests.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `git diff --check`: PASSED.
- Broad local Compose/CI rerun: NOT RUN, as explicitly prohibited by 076-q;
  authoritative remote CI was inspected instead.

## GitHub CI / required checks

Observed after implementation SHA `6e89e1b22ad3fc7ece312a8d74f7fc6e7c59c432`
on workflow run `33344901934` and CodeQL run `33344901885`:

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
- `Markdown`: SUCCESS
- `Mermaid`: SUCCESS
- `Dependency review`: SUCCESS
- `Supply-chain evidence`: SUCCESS
- `CodeQL`: SUCCESS
- `Compose and edge packaging`: FAILURE — the clean deployment, topology,
  setup, and Puck governance stages passed; the existing governance browser
  contract failed at `tests/e2e/governance.spec.ts:385`, waiting for the archive
  dialog to become hidden. The failure is outside 076-q’s database scope and no
  unrelated E2E repair was made.

All required checks green at report drafting: NO — 19 SUCCESS, 1 FAILURE.

## Local setup / dependencies

Used the existing frozen uv and pnpm environments and disposable local
PostgreSQL 16.15 fixture database. No dependency, migration revision, service,
Compose, or production configuration outside the ordered 044 revision changed.

## Documentation

No durable product/API/architecture behavior documentation changed; this order
explicitly forbids documentation and governance changes for this round.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production secrets accessed: NO.
- Production systems accessed: NO.
- Required ordered focused tests skipped/not run: NO.
- Scope deviation: NO; the failed governance browser check was not repaired
  because it is unrelated to this order.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated order/active edited: NO; exact strategic bytes were committed.
- Report commit changes only this report: YES.
- Post-report push: NONE will follow report publication.

## Known limitations / blockers

The implementation is ready for strategic review, but PR #72 cannot be declared
complete or merged while `Compose and edge packaging` is failed. The observed
failure is an existing governance E2E archive-dialog timing/visibility failure,
not evidence of a 076-q update/delete implementation failure.

## Recommended strategic follow-up

Strategy should independently decide whether to rerun or separately repair the
unrelated governance E2E failure. Objective 076-q itself requires no additional
coding unless that review identifies a causal regression.
