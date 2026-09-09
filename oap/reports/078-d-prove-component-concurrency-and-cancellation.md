# OAP Coding-Agent Report — 078-d

## Work order

- Identifier: `078-d`
- Work-order file: `oap/orders/078-d-prove-component-concurrency-and-cancellation.md`
- Work-order SHA-256: `5988b7bed03a0e38be692a58e49dd5efc13bc86c8d68b566cd13b6983a997a08`
- `oap/active` bytes: `078-d\n`
- `oap/active` SHA-256: `b329f326ffd770f816ba9f641f0c9c7508d98664bcbc66016410eddd629ba4f3`
- Numeric objective: `078` (this report completes only the activated `078-d` round)
- PR mode: `AMEND_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Completed the focused real-PostgreSQL concurrency and cancellation proof for
the Objective-078 component data plane on the existing PR. No production code
change was required: the 078-c trusted component path already uses the
transaction-scoped workspace lifecycle/shared lock followed by the
workspace+site structural lock, and all six new race tests pass against it.

The tests use separate public Agent HTTP clients and real PostgreSQL
connections. An owner connection holds the exact production advisory lock;
the tests release requests only after a `pg_locks` barrier proves they are
waiting. This proves serial behavior without elapsed-time correctness,
application mutexes, sleeps for ordering, or test-only production hooks.

The proof covers concurrent anchored creates, competing cycle and valid moves,
stale PATCH, both delete/create serialization orders, page-delete/component-
create serialization, cancellation rollback and pool reuse, and independent
workspace lock progress. Final sequences are dense and acyclic, row versions
are truthful, losing requests leave no durable reservation/audit/quota/COW
residue, and idempotent replay has no second effect.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77) — `OPEN`
- Base/head branches: `main` / `oap/078-agent-composition-design-semantics`
- Required starting remote SHA: `1c9f33f431ab731163a10b7971e1d34363e5709d`
- Base remote SHA: `ae3a4a681bb888260192b7bb1b2a337b4906828d`
- Implementation head SHA: `f6ce350d25b97dac7df30e0af3c6fcc5d3b0bdbe`
- Implementation commit pushed: `f6ce350`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal verified from GitHub after publication)
- New PR this round: NO; existing PR amended: YES
- Merge or auto-merge performed: NO

## Changes made

- Added reusable test-only capture of mutation/delete quota, idempotency,
  semantic audit, and foundation COW operation state.
- Added a test-only owner barrier for the exact production
  `workspace_id:site_id:page-structure` advisory key. It uses
  `pg_locks` to prove waiting requests before releasing the owner transaction.
- Added public Agent concurrent-create proof: two different components before
  one anchor both succeed serially, the anchor remains after both, and replay
  of one key has no second effect.
- Added public Agent competing-move proof: one of two mutually cyclic moves
  succeeds and the serialized loser receives cycle/domain denial; two valid
  moves of one component yield one winner and one stale-version conflict.
- Added public Agent stale-PATCH proof: one expected-version winner, one stable
  `409`, winner-only props/version/audit/quota/COW state, and successful
  follow-up use of the pool.
- Added deterministic public Agent leaf delete/child create schedules in both
  serialization orders, with exact `200/404` and `201/409` outcomes.
- Added deterministic public Agent page delete/component create schedules in
  both serialization orders, with exact `200/404` and `201/422` outcomes and
  other-workspace canonical isolation.
- Added lock-wait cancellation proof with no component, version, quota,
  idempotency, audit, or COW residue; a retry succeeds afterward. A different
  workspace completes while the first workspace/site lock is held.
- Preserved all 078-b/078-c catalog, schema, renderer, semantic-ordering,
  row-version, resource-limit, legacy Editor/Puck, supply-chain, and scope
  boundaries. No production implementation or dependency was added.

## Files changed

The exact implementation diff from the required starting report head to
`f6ce350` contains only these paths:

- `oap/active`
- `oap/orders/078-d-prove-component-concurrency-and-cancellation.md`
- `services/backend/tests/integration/test_agent_mutations.py`

## Lock and barrier evidence

- PASS — Component Agent mutations enter `prelocked_cow_session`, which takes
  the lifecycle shared advisory lock before the site structural lock; all
  component dependency/count/mutation checks occur after serialization in the
  current COW view.
- PASS — New concurrent tests hold the exact owner advisory key derived from
  `hashtextextended(f"{workspace_id}:{site_id}:page-structure", 994)`.
- PASS — `_wait_for_page_structure_waiters` confirms the exact number of
  advisory waiters in `pg_locks` before release. It is the repository’s
  established deterministic database barrier, not a duration assertion.
- PASS — No application-process mutex, production test hook, elapsed-time
  ordering, or new dependency was introduced.

## Race-by-race evidence

### Concurrent anchored creates

- PASS — Two independent Agent clients concurrently create distinct Quotes
  before the same Heading anchor; both return `201`.
- PASS — Final IDs are unique, both new IDs precede the anchor, order keys are
  exactly `[0,1,2]`, new rows remain version `1`, and the anchor advances to
  the truthful affected version `3`.
- PASS — Mutation quota, idempotency records, semantic audit events, and COW
  operations each increase by exactly two. Replaying one idempotency key
  returns the original response and changes none of those durable values.

### Competing moves and would-be cycle

- PASS — Two nested parent candidates are moved concurrently under each other
  from separate holder branches. Exactly one request returns `200`; the
  serialized loser reaches the cycle check and returns `422`.
- PASS — The final four-node tree is explicitly traversed for every node and
  contains no cycle. The winner’s parent is exact, the winner advances to
  version `2`, the loser and both holders retain their exact unaffected
  versions, and the loser has no idempotency record.
- PASS — Two valid moves of one component with the same expected version race
  concurrently. Exactly one returns `200` and one stable `409`; the final
  `[b,a,c]` or `[b,c,a]` order is derived from the winning request, with dense
  keys and exact expected versions. Only one mutation quota, idempotency
  record, semantic audit event, and COW operation is added.

### Concurrent stale PATCH

- PASS — Two content-prop PATCH requests with expected row version `1` race;
  exactly one returns `200` and one returns `409`.
- PASS — Final props equal the successful response only and the row version is
  exactly `2`; the losing key has no durable idempotency record.
- PASS — Mutation quota, semantic audit, and COW operation each increase once.
  A follow-up PATCH using version `2` succeeds with version `3`, and the Agent
  pool connection is reusable and outside a transaction.

### Leaf delete versus child create

- PASS — In the delete-first schedule, the delete request is serialized first
  and returns `200`; the subsequent child create against the absent parent
  returns `404`. Only the delete’s delete quota, idempotency, audit, and COW
  operation are durable.
- PASS — In the child-first schedule, the child create returns `201`; the
  subsequent leaf delete returns exact dependency conflict `409`. The parent
  and child remain coherent, and only the create’s mutation quota,
  idempotency, audit, and COW operation are durable.
- PASS — Both schedules assert the failed request’s idempotency key is absent
  and no dangling parent or partial tree state exists.

### Page delete versus component create

- PASS — In the page-delete-first schedule, page deletion returns `200` and
  component creation against the deleted page returns invisible/not-found
  `404`; no component-side durable state is created.
- PASS — In the component-first schedule, component creation returns `201` and
  page deletion returns the established component dependency denial `422`; the
  page and component remain intact in the authoring workspace.
- PASS — The other workspace sees the canonical base page but not the
  uncommitted component overlay, proving workspace isolation and no canonical
  orphan/erase behavior. Failed requests add no durable reservation, audit,
  quota, or COW operation.

### Cancellation and lock independence

- PASS — A public component create is proven waiting on the exact structural
  lock, canceled while blocked, and leaves no component, sibling/version,
  mutation quota, idempotency, audit, or COW residue.
- PASS — A fresh component create succeeds after cancellation; an acquired
  Agent pool connection is not left in a transaction.
- PASS — While workspace A’s site structural lock is held, a component create
  in independent workspace B completes successfully. Workspace A sees only
  its own retry component and workspace B sees its own overlay.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED — 44 packages checked.
- Focused 078-d race suite: PASSED — 6 passed in 62.44s.
- Prior affected sequential 078-c component suite on the same production tree:
  PASSED — 43 passed, 1 warning.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED — 531 passed, 1 warning, 22.68s.
- `uv run --frozen ruff check services/backend tools tests/repository`: PASSED.
- `uv run --frozen ruff format --check services/backend tools tests/repository`: PASSED — 280 files formatted.
- `uv run --frozen mypy`: PASSED — 262 source files.
- `uv run --frozen python -m tools.generate_component_catalog --check`: PASSED.
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`: PASSED.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 58 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; 424 Markdown files scanned.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues in 418 files.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED — all 10 workspace projects.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — all workspace package tests, web tests, browser-worker
  tests, and 3 root contract files/7 root contract tests.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `git diff --check`: PASSED.

The full multi-hour local backend integration suite was intentionally not
rerun; the active order explicitly requires focused race/cancellation proofs
and says not to substitute the full integration suite. No focused required
test was skipped or left pending at implementation-head drafting.

## GitHub CI / required checks

Observed for implementation head
`f6ce350d25b97dac7df30e0af3c6fcc5d3b0bdbe` on PR #77; all current-head
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

- Added durable focused concurrency/cancellation test evidence and the exact
  078-d OAP transcript artifacts.
- No architecture, constitution, protocol, prior order, or prior report was
  edited.

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

- This report completes only `078-d`; numeric Objective 078 remains open and
  PR #77 remains `OPEN` for strategic acceptance.
- The full clean Compose/NGINX/browser/restart/isolation scenario remains the
  next required acceptance layer.
- New catalog breadth, theme/design-system/global-region work, media bytes,
  MCP, exact-workspace Puck workflow, freeze/review/promotion, site reset,
  release claims, and merge remain outside this order.

The strongest reason not to accept numeric Objective 078 yet is that the
broader Compose/browser/restart/isolation acceptance scenario remains
unimplemented by explicit order, even though the focused component concurrency
and cancellation contract is now proven.

## Completion condition

This coding round is complete when this report-only `SELF` commit is pushed as
the direct child of implementation SHA `f6ce350`, verified as the sole changed
path and the remote PR #77 head, and the exact FIFO response `OK` is sent.
Objective 078 is not accepted or merged by this agent; strategy retains sole
authority to review, accept, and merge.
