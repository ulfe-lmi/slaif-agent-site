# OAP Work Order — 078-c

## Objective and authoritative state

Complete the sequential component-integrity layer on the existing Objective
078 PR: replace source-text assertions with executable catalog/Puck/Web render
proof, and repair semantic create/move/delete ordering, affected row versions,
and component resource/depth bounds before the required concurrency round.

- Numeric objective: `078`; round: `078-c`; mode: `AMEND_EXISTING_PR`.
- Repository: `ulfe-lmi/slaif-agent-site`.
- Existing PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77),
  `main` <- `oap/078-agent-composition-design-semantics`; create no new PR.
- Verified remote `main`: `ae3a4a681bb888260192b7bb1b2a337b4906828d`.
- Required starting PR head: report-only commit
  `1f6aea32338218f57c6324c9f94f9cab8ac8fb29`; its sole changed path is the
  immutable 078-b report and its parent is implementation commit
  `a0622be0588268b8cca6ac1878391e10412bb079`.
- Preserve accepted 078-b catalog-v1 authority/hash/generator, exact typed
  Agent contract, deterministic migration snapshot, nested validation,
  design-prop DB denial, Editor compatibility and supply-chain posture.
- Numeric Objective 078 remains open and PR #77 must not be merged this round.

## Why another repair is required

Independent review found that 078-b's sole Web evidence in
`apps/web/tests/surface.test.mjs` reads `components.tsx` as text and matches
regexes. It never executes the React renderer or asserts output, so it would
pass if canonical RichText still rendered blank or structured arrays emitted
wrong semantics. The Puck tests likewise do not round-trip the new structured
catalog fixtures or prove malformed nested data is rejected.

The existing `content.slaif_agent_component_move` also captures an anchor's
`order_key` before removing the moving row. For siblings `[A,B,C]`, moving A
before C or after B therefore uses a stale index and lands in the wrong final
position. Current create/move/delete dense-order updates change affected
sibling `order_key` values without advancing their row versions, leaving a
stale client version apparently current. Resource checking also treats
`max_visible_components` as another per-page limit and a subtree move checks
only the moved root's new depth, not the deepest descendant.

## Required repair

### 1. Executable catalog-to-Puck-to-Web parity

Replace or supplement source-text regex checks with executable tests that use
the production catalog/Puck adapter and the actual trusted React renderer.

- Round-trip catalog-valid RichText, Statistics, Timeline and FAQ fixtures
  through the production Puck adapter without losing stable normalized IDs,
  hierarchy, slots, order, schema version or exact props.
- Execute the production React component renderer (SSR/static markup or an
  equivalent real rendering boundary) for those exact fixtures and assert the
  expected visible semantic text and safe element structure. Merely importing,
  reading or regex-matching source is not behavioral evidence.
- Prove malformed nested keys/types/required fields, executable schemes and
  unknown shapes fail in the Puck adapter and do not reach rendered output.
- Prove catalog-valid data accepted by Python/PostgreSQL is accepted by Puck
  and Web, while catalog-invalid data is rejected consistently. Use the
  canonical catalog artifact as the expected basis; do not hand-copy another
  fixture schema.
- Preserve safe escaping: fixture text that resembles markup must render as
  text, never raw HTML/script/style/event behavior.

### 2. Exact semantic ordering

Repair create/move/delete ordering at the trusted PostgreSQL boundary.

- Resolve before/after anchors against the destination sibling sequence after
  logically removing the moving row, or use an equivalent algorithm that
  produces exact intent for both forward and backward same-parent moves.
- Preserve exact cross-parent/cross-slot moves, append-without-anchor behavior,
  no duplicates/gaps, anchor same-site/page/parent/slot confinement, cycle
  denial and at-most-one-anchor input.
- Define deterministic no-op behavior: an already-satisfied semantic move must
  either return an explicit idempotent unchanged result without quota/audit/COW
  mutation, or perform one documented versioned mutation consistently. Do not
  accidentally reorder or create gaps.
- Preserve the public Agent API's semantic anchors only; do not reintroduce raw
  rank/order input.

Through public Agent HTTP against real PostgreSQL, cover at minimum `[A,B,C]`
for A-before-C, A-after-B, C-before-A, C-after-A, adjacent forward/backward,
same-position/no-op, append, and cross-parent/cross-slot moves. Assert the exact
ordered IDs and dense `0..n-1` keys after every operation, not only the moved
record's returned `order_key`.

### 3. Row-version truth for implicit sibling changes

Every `component_instance` row whose durable parent, slot, order or props is
changed by create/move/delete rebalancing must receive a monotonically advanced
positive `row_version` and updated timestamp. Unchanged rows must not advance.

- A client holding an affected sibling's old version must receive the stable
  stale-version conflict on its next PATCH/move/delete.
- Returned/listed records must expose the new versions consistently across
  Agent, Render and Puck reads.
- Replay of the originating idempotency key must return the original stored
  response and make no second sibling/version/quota/audit/COW change.
- Preserve one semantic audit event for the requested component action; do not
  invent misleading separate user actions for deterministic sibling rebalance.

Add focused assertions for before/after row versions, timestamps, mutation and
delete quota, idempotency records, semantic audit and foundation operation
counts for create-before-anchor, same-parent move, cross-parent move and delete.

### 4. Distinct component resource/depth bounds

Make the two limits non-redundant and fail closed:

- `max_components_per_page` bounds the destination page.
- `max_visible_components` bounds all components visible to the capability in
  its site/workspace resource envelope, across accessible pages rather than
  silently resetting per page.
- `max_component_depth` and the architecture hard maximum apply to the deepest
  resulting descendant when moving an existing subtree, not only the moved
  root.

Check limits after the structural lock and against the transaction's current
COW view. Add public Agent/real-PostgreSQL tests with two accessible pages and
with a multi-level subtree. Assert denial leaves tree, row versions, quotas,
idempotency, audit and COW operations exactly unchanged. Also prove unrelated
inaccessible/foreign site or workspace components cannot be counted or used to
infer hidden resources.

## Verification and evidence

Run the focused executable Web/Puck/catalog tests; focused public Agent real-
PostgreSQL sequential component tests; migration/privilege tests affected by
SQL changes; generated catalog/OpenAPI drift checks; Python unit/repository and
Node suites; formatting/type checks; and all current-head GitHub checks. Exact
test names/counts and terminal results are required. Pending/skipped is not
pass. Do not spend the turn rerunning the entire multi-hour local integration
suite as a substitute for the focused proofs; broad PostgreSQL CI remains the
qualification matrix.

## Non-goals and continuing requirements

- Do not add the five concurrent component race cases in this round. They are
  the next required dependency-correct proof once sequential semantics are
  sound; this is not a waiver.
- No full clean Compose/NGINX/browser/restart/isolation scenario yet; it remains
  required after focused concurrency.
- No new catalog breadth, design-system/theme/global-region/header-footer/
  responsive mutation, media bytes, MCP, exact-workspace Puck workflow,
  freeze/review/promotion, source/sweep, site reset, release claim, dependency,
  image, architecture or security exception.
- No broad refactor, historical order/report edit, test/Markdown/security
  weakening, production system/data/credential or merge. Preserve issue #67
  closure and zero-Critical supply-chain policy.

Routine Node/PostgreSQL/test setup belongs to the passwordless-sudo disposable
executor environment; do not transfer it to the human.

## GitHub workflow and immutable report

Fetch and verify the exact existing PR/branch/head, then amend only PR #77.
Commit this order and exact `oap/active` unchanged with the bounded repair,
push, inspect and repair only in-scope CI failures, create no PR and never merge.

Publish exactly
`oap/reports/078-c-complete-sequential-component-integrity.md` as the final
report-only child of a literal pushed implementation SHA with `Report
publication commit: SELF`. Report exact PR/branch/base/SHAs/files; executable
Puck/Web fixtures and output; each ordered move case; row-version/no-op/replay
semantics; cross-page/deep-subtree limits; unchanged-state evidence; exact
tests/checks/skips; safety/scope; remaining concurrency/Compose/design scope;
and the strongest reason this round or Objective 078 should not yet be
accepted. Make no post-report push, signal exact FIFO `OK`, then wait.
