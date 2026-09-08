# OAP Work Order — 078-e

## Objective and authoritative state

Repair only the overclaimed delete/dependency concurrency evidence from 078-d
on the existing Objective-078 PR. Convert the sequential leaf/page schedules
into actual two-request deterministic races and add the omitted leaf-delete
versus existing-subtree-move case. Do not add unrelated production or feature
scope.

- Numeric objective: `078`; round: `078-e`; mode: `AMEND_EXISTING_PR`.
- Repository: `ulfe-lmi/slaif-agent-site`.
- Existing PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77),
  `main` <- `oap/078-agent-composition-design-semantics`; create no new PR.
- Verified remote `main`: `ae3a4a681bb888260192b7bb1b2a337b4906828d`.
- Required starting PR head: report-only commit
  `524eaad71b7701594facc0878b06c9d2f34a397a`; its sole changed path is the
  immutable 078-d report and its parent is implementation commit
  `f6ce350d25b97dac7df30e0af3c6fcc5d3b0bdbe`.
- Preserve the valid 078-d anchored-create, competing-move, stale-PATCH,
  cancellation and independent-workspace proofs. Numeric Objective 078 remains
  open and PR #77 must not be merged this round.

## Exact deficiency

`test_agent_component_leaf_delete_and_child_create_have_both_serial_orders`
holds the structural lock, queues only the selected first request, releases and
awaits it, and starts the opposing request afterward. The page/component test
does the same. Those are useful sequential dependency checks, but they are not
races and cannot prove the second operation was already in flight behind the
same serialization boundary. The report nevertheless describes them as
concurrency proof. The required leaf delete versus an existing subtree move
was also not exercised.

Preserve the immutable report as historical evidence; correct the executable
proof and state the prior overclaim explicitly in the 078-e report.

## Required repair

Use the existing exact owner advisory-lock/`pg_locks` waiter barrier. For every
schedule below:

1. hold the production workspace+site structural advisory lock;
2. launch the request intended to acquire first and prove exactly one waiter;
3. launch the opposing request on a distinct Agent HTTP client/connection and
   prove exactly two waiters before releasing the owner lock;
4. release the owner lock, await both requests, and assert the exact ordered
   outcome and final durable state.

Do not use sleeps, process mutexes, test-only production hooks, or run the
opposing request only after the first has completed. If PostgreSQL advisory-lock
queue order itself is not an adequate deterministic primitive, use an existing
safe DB event/lock barrier that proves actual transaction order; explain it.

### 1. Leaf delete versus child create

Exercise both waiter orders against the same leaf:

- delete queued first -> exact delete success, child create absent-parent
  failure;
- child create queued first -> exact create success, leaf delete dependency
  failure.

Assert exact statuses/error codes, final parent/child presence, dense order and
row versions. Only the committed operation may add its delete/mutation quota,
idempotency row, semantic audit and foundation COW operation; the losing key
must leave no durable residue. Canonical and another workspace remain unchanged.

### 2. Leaf delete versus existing-subtree move

Build an existing movable subtree elsewhere on the page and race moving its
root beneath the candidate leaf against deleting that leaf, in both waiter
orders:

- delete first -> move fails because destination parent is absent and the
  subtree remains coherent at its original location;
- move first -> delete fails with dependency conflict and the whole subtree is
  coherently attached below the leaf.

Assert exact statuses, no lost/dangling descendants, exact parent/slot/dense
orders and all affected row versions, plus the same precise quota/idempotency/
audit/COW accounting and isolation as above.

### 3. Page delete versus component create

Exercise both waiter orders with page DELETE and component POST already in
flight before releasing the structural lock:

- page delete first -> exact delete success and component absent-page 404;
- component create first -> exact 201 and established page component-dependency
  denial, with page and component retained in the workspace.

Assert exact page/component terminal state, no cascade/orphan, exact durable
accounting for only the committed action, canonical unchanged, and another
workspace unable to see the uncommitted component.

Run each repaired focused race repeatedly (at least three executions of the
focused tests in the same environment) to prove deterministic barrier behavior.
If the real race exposes a production defect, apply only the minimum lock/check
repair and add the regression; otherwise this round should remain test/OAP-only.

## Verification and non-goals

Run the repaired focused tests with stated repetition count, the complete 078-d
race/cancellation set once, affected Python unit/repository and quality checks,
generated checks, Node suite if any shared file changed, and all current-head
GitHub checks. Report exact results and every skip/pending/failure. Do not run
the entire multi-hour local integration suite as a substitute.

No Compose/browser/restart acceptance, catalog/design/theme/global-region/
header-footer/responsive feature, media bytes, MCP, exact-workspace Puck,
freeze/review/promotion, source/sweep, site reset, dependency/image/
architecture/security exception, broad refactor, historical artifact edit,
test weakening, production access or merge. Preserve issue #67 closure and the
zero-Critical supply-chain gate.

Routine PostgreSQL/test setup belongs to the passwordless-sudo disposable
executor environment; do not transfer it to the human.

## GitHub workflow and immutable report

Fetch and verify the exact existing PR/branch/head, then amend only PR #77.
Commit this order and exact `oap/active` unchanged with the narrow repair, push,
inspect and repair only in-scope CI failures, create no PR and never merge.

Publish exactly
`oap/reports/078-e-repair-real-delete-dependency-races.md` as the final
report-only child of a literal pushed implementation SHA with `Report
publication commit: SELF`. Report exact PR/SHAs/files; the prior sequential
overclaim; exact two-waiter barrier evidence and acquisition order for every
schedule; statuses/error codes/final rows/versions/accounting/isolation;
repetitions/tests/checks/skips; any minimal production repair; remaining
Compose/design scope; and the strongest reason Objective 078 is not yet
acceptable. Make no post-report push, signal exact FIFO `OK`, then wait.
