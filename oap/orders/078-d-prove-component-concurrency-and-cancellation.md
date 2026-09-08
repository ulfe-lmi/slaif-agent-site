# OAP Work Order — 078-d

## Objective and authoritative state

Complete the focused real-PostgreSQL concurrency and cancellation contract for
the Objective-078 component data plane on the existing PR. Exercise the actual
public Agent semantic operations and trusted structural locking so races cannot
produce duplicate order, cycles, dangling children, stale-version success,
unsafe page deletion, quota/audit/idempotency drift or residual cancelled work.

- Numeric objective: `078`; round: `078-d`; mode: `AMEND_EXISTING_PR`.
- Repository: `ulfe-lmi/slaif-agent-site`.
- Existing PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77),
  `main` <- `oap/078-agent-composition-design-semantics`; create no new PR.
- Verified remote `main`: `ae3a4a681bb888260192b7bb1b2a337b4906828d`.
- Required starting PR head: report-only commit
  `1c9f33f431ab731163a10b7971e1d34363e5709d`; its sole changed path is the
  immutable 078-c report and its parent is implementation commit
  `bdfa80e091bcc01f52209044ec94f68d6fff9ebd`.
- Preserve accepted 078-b/078-c catalog, schema, Render/Puck, semantic ordering,
  row-version, resource-limit and legacy Editor behavior.
- Numeric Objective 078 remains open and PR #77 must not be merged this round.

## Required production and proof contract

Use the established transaction-scoped workspace lifecycle/shared lock followed
by the workspace+site structural lock, or an equivalently deterministic order.
All dependency checks and counts must occur after serialization and against the
current COW view. Do not add sleeps, probabilistic timing, application-process
mutexes, test-only hooks in production code, or broad acceptable-status sets.

Neutral owner/test connections may create fixtures, hold/release the exact
advisory locks, inspect `pg_locks`/activity and assert final state. They may not
perform a mutation claimed as Agent behavior. Reuse the deterministic patterns
in the existing 077 page/navigation race tests, especially
`test_agent_locale_navigation_structural_races_and_cancellation`,
`test_agent_page_duplicate_create_race_is_serialized_by_postgres`,
`test_agent_page_dynamic_parent_race_keeps_valid_leaf_or_child_tree`, and
`test_agent_page_cancellation_while_structural_lock_waits_leaves_no_residue`.

### 1. Concurrent creates at one semantic position

Through two independent Agent HTTP clients/connections in the same workspace,
race two different component creates before the same sibling (and, if needed,
an append case). Both valid operations may succeed serially, but each response
must be exact and the final durable sequence must contain each ID once, keep the
anchor after both, and have dense unique order keys with truthful row versions.
Assert exact quota, two idempotency records, two semantic audit events and two
foundation operations. Repeat/replay one key and prove no second effect.

### 2. Competing moves and would-be cycle

Build sibling parents A and B, then concurrently request A under B and B under
A with the same current expected versions. Exactly one move may succeed; the
serialized loser must receive the stable cycle/domain denial. Assert the exact
status pair, final acyclic tree, parent/slot/order, all affected row versions,
one consumed mutation/audit/idempotency/foundation operation and no residue from
the loser. Also race competing valid moves of one component with the same
expected version: exactly one succeeds and the loser receives stale-version
conflict, with final order matching the winner.

### 3. Concurrent stale PATCH

Race two content-prop PATCH requests for the same node and expected row version.
Exactly one returns 200 and one returns the stable 409 optimistic conflict.
Final props must equal the winner only; row version advances once; exactly one
mutation quota, completed idempotency record, semantic audit and foundation
operation is added. The loser must not reserve durable quota/idempotency/audit
state, and each connection/pool remains reusable.

### 4. Leaf delete versus child create/move

Deterministically exercise both lock-acquisition orders for deleting a leaf
while another request creates a child under it or moves an existing subtree
under it:

- if delete serializes first, the child/move request must fail because the
  destination parent is absent;
- if child creation/move serializes first, delete must fail with the exact
  dependency denial.

For each schedule assert exact responses and one coherent final tree: never a
dangling parent, lost subtree, duplicate/gapped order, partial sibling-version
change or cross-page reference. Assert exact delete/mutation quotas,
idempotency, audit and COW operations for only the committed action.

### 5. Page delete versus component create

Deterministically exercise both serialization orders through public Agent page
DELETE and component POST:

- page deletion first makes component creation fail invisibly/not-found;
- component creation first makes page deletion follow the established 077
  component dependency policy rather than silently orphaning or erasing the
  new node.

Assert the exact page/component terminal state, no dangling composition,
canonical/other-workspace isolation, and exact quotas/idempotency/audit/COW
operations. Preserve the existing page/navigation/redirect lock order and page
delete semantics; do not solve the race with cascade loss.

### 6. Cancellation and lock independence

Hold the exact structural advisory lock, start a public Agent component
mutation, prove it is waiting using a deterministic DB barrier, cancel the
request/task, release the lock, and assert no component/sibling-version/quota/
idempotency/audit/COW residue. Reuse the same Agent pool/connection for a valid
operation afterward and verify COW context cleanup.

Separately prove a held structural lock for one workspace/site does not block a
component mutation in a different workspace or site. Use an event/DB barrier,
not elapsed-time thresholds as the correctness assertion; bounded timeouts may
only prevent a hung test.

## Acceptance and verification

Focused tests must name and independently cover every case above. For each
race record which request acquired the serialized state first and assert exact
winner/loser responses plus terminal database state; no assertion such as
`status in {200,409,422}` without deriving and checking the corresponding final
state is acceptable.

If a race exposes a production defect, repair the minimum trusted lock/check/
mutation path and add the regression. Preserve server-derived site/workspace/
operation context, strict COW, catalog validation, semantic anchors, optimistic
versions, wrapper-owned quotas/idempotency/audit, cancellation rollback and
legacy Editor/Puck compatibility.

Run the focused race/cancellation tests repeatedly enough to establish their
deterministic barrier behavior, affected migration/privilege tests, Python
unit/repository and Node suites, formatting/type/generated checks, and all
current-head GitHub checks. Report exact commands/counts/repetitions and every
skip/pending/failure. Do not rerun the entire multi-hour local integration suite
as a substitute for these focused cases; the PostgreSQL 14–18 CI matrix remains
the broad qualification.

## Non-goals and continuing requirements

- No clean Compose/NGINX/browser/restart/isolation acceptance scenario yet; it
  remains the next acceptance layer after these races.
- No new catalog breadth, design-system/theme/global-region/header-footer/
  responsive mutation, media bytes, MCP, exact-workspace Puck workflow,
  freeze/review/promotion, source/sweep, site reset or release claim.
- No dependency/image/architecture/security exception, broad refactor,
  historical order/report edit, test/Markdown/security weakening, production
  system/data/credential or merge. Preserve issue #67 closure and the
  zero-Critical supply-chain gate.

Routine PostgreSQL/test setup belongs to the passwordless-sudo disposable
executor environment; do not transfer it to the human.

## GitHub workflow and immutable report

Fetch and verify the exact existing PR/branch/head, then amend only PR #77.
Commit this order and exact `oap/active` unchanged with the bounded repair and
proof, push, inspect and repair only in-scope CI failures, create no PR and
never merge.

Publish exactly
`oap/reports/078-d-prove-component-concurrency-and-cancellation.md` as the final
report-only child of a literal pushed implementation SHA with `Report
publication commit: SELF`. Report exact PR/branch/base/SHAs/files; lock order;
barrier mechanism; each race's exact request/status/order/final rows/versions/
quota/idempotency/audit/COW evidence; cancellation cleanup and independent-lock
proof; exact commands/repetitions/checks/skips; safety/scope; remaining Compose
and design scope; and the strongest reason this round or Objective 078 should
not yet be accepted. Make no post-report push, signal exact FIFO `OK`, then
wait.
