# OAP Coding-Agent Report — 078-e

## Work order

- Identifier: `078-e`
- Work-order file: `oap/orders/078-e-repair-real-delete-dependency-races.md`
- Work-order SHA-256: `605e81f8c4dd455551a8f64e5202a7e04979f1a6e7a06422248436763cecdb7a`
- `oap/active` bytes: `078-e\n`
- `oap/active` SHA-256: `749bd53a125ed40a8f58ddaac52033375b7a0e7201ff8e366b65fd283523a68e`
- Numeric objective: `078` (this report completes only the activated `078-e` round)
- PR mode: `AMEND_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Corrected the overclaimed delete/dependency concurrency evidence from 078-d on
the existing Objective-078 PR. The immutable 078-d report is preserved and is
explicitly recorded as historical overclaim: its leaf/page schedules queued
only the first request, released and awaited it, and started the opposing
request afterward. This round converted both schedules into actual two-request
races and added the omitted leaf-delete versus existing-subtree-move race.

Every repaired schedule holds the exact production workspace/site structural
advisory lock, launches the intended first request, proves one waiter through
`pg_locks`, launches the opposing request on a distinct Agent client, proves
two waiters, releases the owner lock, and awaits both in-flight requests. The
three repaired race tests passed three complete executions each. No production
code change was necessary; the existing lock/check implementation produced the
required outcomes and remained unchanged.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77) — `OPEN`
- Base/head branches: `main` / `oap/078-agent-composition-design-semantics`
- Required starting remote SHA: `524eaad71b7701594facc0878b06c9d2f34a397a`
- Base remote SHA: `ae3a4a681bb888260192b7bb1b2a337b4906828d`
- Implementation head SHA: `fd63f0e0fac627a08e51bda660c2598e7b3a12af`
- Implementation commit pushed: `fd63f0e`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal verified from GitHub after publication)
- New PR this round: NO; existing PR amended: YES
- Merge or auto-merge performed: NO

## Changes made

- Repaired `test_agent_component_leaf_delete_and_child_create_have_both_serial_orders`
  so delete-first and child-first requests are both in flight and proven as
  two waiters before lock release.
- Added
  `test_agent_component_leaf_delete_and_subtree_move_have_both_race_orders`,
  covering an existing movable subtree in both delete-first and move-first
  acquisition orders.
- Repaired `test_agent_page_delete_and_component_create_have_both_serial_orders`
  so page DELETE and component POST are both in flight before release in each
  acquisition order.
- Added exact status, error, terminal tree, dense-order, row-version,
  quota/idempotency/audit/COW, and other-workspace isolation assertions for
  every repaired schedule.
- Preserved all 078-b/078-c/078-d production behavior and prior proofs. No
  production source, dependency, architecture, or security-policy change was
  made.

## Files changed

The exact implementation diff from the required starting report head to
`fd63f0e` contains only these paths:

- `oap/active`
- `oap/orders/078-e-repair-real-delete-dependency-races.md`
- `services/backend/tests/integration/test_agent_mutations.py`

## Barrier and acquisition evidence

- PASS — Each repaired case holds the exact owner advisory key derived from
  `hashtextextended(f"{workspace_id}:{site_id}:page-structure", 994)`.
- PASS — The first request is launched and the test observes exactly one
  advisory waiter before launching the opposing request.
- PASS — The opposing request is launched on a distinct Agent HTTP client and
  the test observes exactly two advisory waiters before releasing the owner
  transaction.
- PASS — The expected first-acquirer outcome and final state prove the queued
  order: delete-first schedules produce delete success; child/move-first
  schedules produce child/move success. No opposing request is started after
  the first completes.
- PASS — The barrier uses PostgreSQL lock state, not elapsed time, sleeps for
  ordering, process mutexes, or production test hooks.
- PASS — The production path’s lifecycle shared lock followed by workspace/site
  structural lock remains unchanged and no production repair was needed.

## Race-by-race evidence

### Leaf delete versus child create

- PASS — Delete-first: both requests are waiting before release; delete returns
  `200`, child creation against the absent Section returns `404`, the leaf is
  absent, and no dangling child exists.
- PASS — Child-first: both requests are waiting before release; child creation
  returns `201`, leaf deletion returns dependency conflict `409`, and the
  parent/child tree remains intact with exact row versions and dense order.
- PASS — In each schedule only the serialized winner adds its delete/mutation
  quota, idempotency record, semantic audit event, and foundation COW
  operation. The losing key leaves no durable reservation or audit residue.
- PASS — The authoring overlay is isolated; the other workspace cannot see the
  uncommitted page/component state.

### Leaf delete versus existing-subtree move

- PASS — Delete-first: both requests are waiting before release; leaf delete
  returns `200`, the queued subtree move returns absent-parent `404`, and the
  existing source root plus descendant remain coherently attached at the
  original holder with exact row versions/order.
- PASS — Move-first: both requests are waiting before release; subtree move
  returns `200`, leaf delete returns dependency conflict `409`, and the whole
  subtree is attached below the leaf without lost or dangling descendants.
- PASS — Source/destination parent IDs, slots, dense order keys, and all
  affected versions are asserted in both schedules. Only the committed action
  changes quota, idempotency, audit, and COW operation counts.
- PASS — Other-workspace reads remain isolated from the uncommitted page.

### Page delete versus component create

- PASS — Page-delete-first: both page DELETE and component POST are waiting
  before release; page delete returns `200`, component creation returns
  absent-page `404`, and no component-side durable state exists.
- PASS — Component-create-first: both requests are waiting before release;
  component creation returns `201`, page deletion returns the established
  component-dependency denial `422`, and the page/component remain intact in
  the authoring workspace.
- PASS — The other workspace sees the canonical base page but not the
  uncommitted component overlay. No cascade loss, orphan, or cross-workspace
  visibility occurs.
- PASS — Failed request keys leave no idempotency, audit, quota, or COW
  residue; only the committed action is durably accounted.

## Prior 078-d overclaim

- The immutable `oap/reports/078-d-prove-component-concurrency-and-cancellation.md`
  remains unchanged.
- Its delete/create schedules were sequential dependency checks, not actual
  races, despite the report describing them as concurrency proof.
- This round corrects the executable evidence with two in-flight requests and
  records the distinction rather than rewriting historical artifacts.

## Local verification

- Three executions of the repaired leaf-create, leaf-subtree-move, and
  page-create races: PASSED each time — `3 passed in 31.25s`, `3 passed in
  31.51s`, and `3 passed in 31.89s`.
- Complete 078-d race/cancellation set after repair: PASSED — 7 passed in
  72.80s.
- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED — 44 packages checked.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED — 531 passed, 1 warning, 22.94s.
- `uv run --frozen ruff check services/backend tools tests/repository`: PASSED.
- `uv run --frozen ruff format --check services/backend tools tests/repository`: PASSED — 280 files formatted.
- `uv run --frozen mypy`: PASSED — 262 source files.
- `uv run --frozen python -m tools.generate_component_catalog --check`: PASSED.
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`: PASSED.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 58 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; 426 Markdown files scanned.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues in 420 files.
- `git diff --check`: PASSED.

No Node source/shared contract file changed in 078-e, so no additional local
Node suite was required by this order; the current-head Node contracts check
below independently passed. The full multi-hour local backend integration
suite was not rerun, as the order explicitly requires focused races rather
than using that suite as a substitute. No focused required test was skipped or
left pending at implementation-head drafting.

## GitHub CI / required checks

Observed for implementation head
`fd63f0e0fac627a08e51bda660c2598e7b3a12af` on PR #77; all current-head
checks were terminal and green before report publication:

- Analyze (actions): SUCCESS
- Analyze (javascript-typescript): SUCCESS
- Analyze (python): SUCCESS
- CodeQL: SUCCESS
- Compose and edge packaging: SUCCESS
- Dependency review: SUCCESS
- Detect supported languages: SUCCESS
- Foundation PostgreSQL 14: SUCCESS
- Foundation PostgreSQL 15: SUCCESS
- Foundation PostgreSQL 16: SUCCESS
- Foundation PostgreSQL 17: SUCCESS
- Foundation PostgreSQL 18: SUCCESS
- Markdown: SUCCESS
- Mermaid: SUCCESS
- Node contracts: SUCCESS
- Python 3.12 quality and package: SUCCESS
- Python 3.13 quality and package: SUCCESS
- Python 3.14 quality and package: SUCCESS
- Repository policy: SUCCESS
- Supply-chain evidence: SUCCESS

- All required current-head checks green at implementation drafting: YES.
- A report-only commit may start a fresh CI run; per protocol no post-report
  check wait or repository mutation is performed.

## Local setup / dependencies

- Used exact uv 0.12.5, disposable local PostgreSQL, Node 24.14.1, and pnpm
  11.22.0.
- No production dependency, lockfile, hosted service, image, architecture, or
  security exception was added.
- No production system, credential, capability, cookie, or private artifact was
  accessed or printed.

## Documentation

- Added durable executable race evidence and the exact 078-e OAP transcript
  artifacts.
- Preserved the immutable 078-d report; no prior order/report or governance
  artifact was edited.

## Safety and scope confirmations

- Unrelated files changed: NO.
- New or extra PR: NO.
- Coding-agent merge or auto-merge: NO.
- Activated order/active content edited after selection: NO; strategy-authored
  bytes were committed unchanged.
- New dependency or hosted service: NO.
- Production secrets/systems accessed: NO.
- Test/Markdown/security policy weakened: NO.
- Report-publication commit changes only this report: YES.

## Known limitations / blockers

- This report completes only `078-e`; numeric Objective 078 remains open and
  PR #77 remains `OPEN` for strategic acceptance.
- The broader Compose/NGINX/browser/restart/isolation acceptance scenario
  remains required and is not claimed here.
- New catalog breadth, theme/design-system/global-region work, media bytes,
  MCP, exact-workspace Puck workflow, freeze/review/promotion, site reset,
  release claims, and merge remain outside this order.

The strongest reason not to accept numeric Objective 078 yet is the remaining
broader end-to-end Compose/browser/restart/isolation acceptance layer, not a
known defect in the now-corrected delete/dependency race evidence.

## Completion condition

This coding round is complete when this report-only `SELF` commit is pushed as
the direct child of implementation SHA `fd63f0e`, verified as the sole changed
path and the remote PR #77 head, and the exact FIFO response `OK` is sent.
Objective 078 is not accepted or merged by this agent; strategy retains sole
authority to review, accept, and merge.
