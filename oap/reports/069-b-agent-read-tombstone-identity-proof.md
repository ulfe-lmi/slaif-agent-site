# OAP Coding-Agent Report — 069-b

## Work order

- Identifier: `069-b`
- Work-order file: `oap/orders/069-b-agent-read-tombstone-identity-proof.md`
- Numeric objective: `069`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Closed the four narrow 069-a evidence gaps on the same PR #60 with integration
proof only. Production Agent read code, migration SQL, grants, routes, and
mutation behavior are unchanged.

The new proof demonstrates a genuine COW tombstone and non-resurrection,
explicit identity of the app-owned production Agent pool, denial for a forged
workspace session UUID, and direct exact-resource isolation for a retained
workspace-B overlay UUID. It preserves the accepted 069-a overlay update,
canonical fallback, scope, isolation, cleanup, and mutation evidence.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#60](https://github.com/ulfe-lmi/slaif-agent-site/pull/60)
- PR state: `OPEN`, non-draft, `MERGEABLE`
- Base/head: `main` / `oap/069-agent-semantic-reads`
- Starting 069-b remote SHA: `b563193b8313afd93fb286230ec6a86c30332808`
- Implementation head SHA: `aed0e272e2ecac5f93241ac4abc6af924b75bbcc`
- Implementation commits this round:
  - `ed5820b10ccd8cc49c36a5847aa901017c0a4180` — active/order and proof
  - `aed0e272e2ecac5f93241ac4abc6af924b75bbcc` — explicit fixture UUIDs
- Report publication commit: `SELF`
- New PR this turn: NO
- Same PR amended: YES
- Merge performed: NO

## Changes made

- Extended the existing real PostgreSQL/public HTTP Agent semantic-read test
  only.
- Added distinct canonical tombstone fixture type
  `00000000-0000-0000-0000-000000000692` alongside canonical type
  `00000000-0000-0000-0000-000000000691`.
- Retained explicit workspace-B overlay type UUID
  `00000000-0000-0000-0000-000000000693` while preserving its deliberate
  same-site `workspace-type` key collision.
- Added same-pool identity assertions, forged-session cleanup assertions, and
  exact A/B resource-ID GET assertions.
- Committed the exact strategic `069-b` order and `oap/active` bytes unchanged.

## Files changed

- `services/backend/tests/integration/test_agent_mutations.py`
- `oap/orders/069-b-agent-read-tombstone-identity-proof.md`
- `oap/active`

No production source, migration SQL, durable documentation, dependency, role,
route, or API behavior changed in this continuation.

## Acceptance-criteria evidence

### Criterion 1 — Real tombstone and canonical non-resurrection

- PASSED. The test seeds canonical type UUID
  `00000000-0000-0000-0000-000000000692` in the owner-visible
  `content.content_type_base` relation with label `Tombstone canonical`.
- Workspace A uses a real `asyncpg_cow_session` on the least-privileged Agent
  pool and executes `DELETE FROM content.content_type WHERE id = $1` through
  the foundation-managed COW view. Reviewer inspection confirms a new COW
  operation after the prior overlay-update operation.
- Workspace A public GET list excludes the tombstoned UUID, and exact GET
  returns `404 RESOURCE_NOT_FOUND`.
- Workspace B public exact GET for the same UUID returns `200` with
  `{"en":"Tombstone canonical"}` from canonical fallback.
- Owner inspection confirms the base row and label remain present and
  unchanged. This is newly proved in 069-b; 069-a only proved status filtering
  and an overlay UPDATE, not tombstone non-resurrection.

### Criterion 2 — Effective production Agent pool identity

- PASSED. During the same `create_agent_app` lifespan and on the exact
  `app.state.database.cow_pool()` used by `execute_agent_read`, the test
  asserts `current_database` equals the fixture database,
  `session_user == current_user == database.credentials["slaif_agent_runtime"][0]`,
  and the reachable product authority-role array is exactly
  `["slaif_agent_runtime"]`.
- Owner, Control, Editor, public reader, preview reader, reviewer, scheduler,
  media, and GC authority roles are not reachable from that app-owned login.

### Criterion 3 — Forged workspace context and direct B-resource isolation

- PASSED. A random forged `app.session_id` in a valid foundation COW session
  fails the Agent read wrapper with a PostgreSQL error; the following Agent
  pool connection has empty/cleared session, operation, and visible-operation
  settings.
- Existing missing-context and wrong-site context denials remain green.
- Workspace-B overlay UUID
  `00000000-0000-0000-0000-000000000693` is inserted with colliding key
  `workspace-type` and label `B only`. Workspace A exact GET returns stable
  `404 RESOURCE_NOT_FOUND`; workspace B exact GET returns `200` and `B only`.
- A and B operation lists remain unchanged across their public GETs; no foreign
  UUID is disclosed in the A failure envelope.

### Criterion 4 — Accepted contract preservation

- PASSED. The seven routes, wrapper ownership/search path/grants, overlay
  update, canonical fallback through type/page/composition/media, site and
  workspace isolation, scope/malformed/revoked/expired/inactive outcomes,
  cancellation/context cleanup, and all five 067 mutations remain green.
- No Agent generic function, base/change table, Control/audit table, reviewer,
  DDL, raw-SQL, lifecycle, or broad role authority was added.

### Criterion 5 — No read residue

- PASSED. The test records workspace-A operation state after fixture setup and
  after the COW overlay/tombstone setup; all public A/B GETs leave the final
  operation list equal to the post-tombstone state. Before/after counts for
  `control.agent_idempotency` and `audit.agent_mutation` are equal. Owner base
  rows remain intact.

## Route/service/evidence trace

`_authenticate` resolves the immutable capability context, then
`execute_agent_read` opens one `asyncpg_cow_session` with that context's
workspace UUID. `AgentSemanticReadService` calls the existing seven narrow
Agent wrappers on the same COW connection. No ordinary app-level content
service or second semantic pool is used. Foundation cleanup is asserted after
forged context, cancellation, success, and failure paths.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py`: PASSED; 5 tests.
- Focused tombstone/identity/isolation test: PASSED.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED; 101 tests.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED; 412 tests.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED; 199 files.
- `uv run --frozen mypy`: PASSED; 187 source files.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-069b`: PASSED; sdist and wheel.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED; 54 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED; 16 diagrams and 216 Markdown files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED; 210 files, 0 issues.
- Node 24.14.1 and pnpm 11.22.0: PASSED.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- Frozen process smoke for all ten backend modules: PASSED; all returned
  `CHECK_OK`.
- Direct system-Python process invocation issue from 069-a remains recorded:
  `/usr/bin/python` lacks the project import path; frozen `uv run` checks pass.
- Local Compose smoke was reused from accepted 069-a because only integration
  proof paths changed; fresh implementation-head Compose/edge CI passed.
- `git diff --check`: PASSED.

## GitHub CI / required checks

Observed for literal implementation head `aed0e272e2ecac5f93241ac4abc6af924b75bbcc`:

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

All fresh implementation-head checks were successful before report drafting.

## Local setup / dependencies

Used the existing frozen `uv` environment, local PostgreSQL fixtures, Node
24.14.1, and pnpm 11.22.0. No dependency, lockfile, production credential,
production system, hosted service, or infrastructure change was added.

## Documentation

No durable documentation change was required because production behavior and
the documented contract are unchanged. The report explicitly narrows the
069-a tombstone evidence claim to the newly proved behavior.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production source changed: NO.
- Production secrets/systems/data accessed: NO.
- Required tests skipped/not run: NO for the claimed sets; local Compose was
  honestly reused and fresh CI Compose passed.
- Scope deviation: NO.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated 069-a order/report or historical artifacts edited: NO.
- Exact 069-b order and `oap/active` bytes committed unchanged: YES.
- Final report commit changes only this report: YES.

## Known limitations / blockers

- This round proves the requested type tombstone and exact resource behavior;
  it does not broaden the route or wrapper surface to other tombstone families.
- Strategy independently reviews and merges PR #60; this report is not
  acceptance or merge authority.

## Recommended strategic follow-up

Independently verify the report SELF child and fresh report-head checks, then
choose merge or another same-PR continuation. No next objective is selected by
the coding agent.

RESULT=OK
