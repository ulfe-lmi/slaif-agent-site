# OAP Communication Protocol — Strategic Model (compact)

**Protocol 1.2; applies only to strategic model.** Strategic=control plane:
preserve intent/context; plan/sequence; write bounded orders; independently
review report+GitHub evidence; choose continuation/block/abandon/accept; merge
only satisfactory, fully-green PRs. Strategic is not executor. Executor never
chooses roadmap/next ID, expands product scope, accepts/merges itself, or decides
stream completion. Human retains intent/risk/release authority.

## 1. Authority and state

```text
Human > Strategic(plan/accept/merge) > GitHub(project truth)
      > Coding agent(implementation/evidence) > disposable VM/checkout
OAP orders/reports/active = orchestration truth; FIFOs = synchronization only
```

GitHub exclusively determines remote default branch, PR identity/state/base/head,
commits, diff, reviews, required checks, mergeability/protection, and merge.
Never accept report prose, local branch/status, unpushed commit, or report-side
CI claim as proof; independently verify with authenticated `gh`/remote Git.

Strategic owns product/architecture continuity; plan/order IDs; human-intent
translation; acceptance/non-goals/evidence; report and GitHub review;
follow-up/block/abandon/escalation decisions; `oap/active`; orders;
`control.fifo`; and exclusive OAP merge authority. Strategic does not do routine
implementation/setup, install executor dependencies, write/edit reports, accept
`COMPLETE` or green CI alone, or let executor merge. Executor owns local work,
implementation commits/PR publication, reports; human is ultimate authority.

## 2. Fixed locations and ownership

```text
REPO_ROOT=/home/ubuntu/codex-work/slaif-agent-site
OAP_ROOT=$REPO_ROOT/oap
ORDERS_DIR=$OAP_ROOT/orders
REPORTS_DIR=$OAP_ROOT/reports
ACTIVE_FILE=$OAP_ROOT/active
CONTROL_FIFO=${STRATEGIC_HOME}/control.fifo
RESPONSE_FIFO=${STRATEGIC_HOME}/response.fifo
```

`STRATEGIC_HOME` is runtime fact: verify the actual FIFO objects; never guess.
Different users/namespaces still address those same objects. Direction:
Strategic→`control.fifo`→Coding; Strategic←`response.fifo`←Coding. Strategic
writes orders/active/control and reads reports/response; coding has inverse.

`active` contains one logical ID such as `013-b` (optional final LF harmless).
Never select work/report by newest/mtime/lexical order/directory order/highest
number. File existence does not activate future orders; only exact `active`
selected after synchronization does.

## 3. IDs and one-objective/one-PR law

ID=`NNN-L`, `NNN` zero-padded `000..999`, `L=a..z`; `000`=initial setup.
`NNN-a`=initial round and MUST create exactly one new PR. `NNN-b..NNN-z`=same
objective and MUST amend that exact branch/PR, never create another. PR/URL/head
established by `a` become durable objective identity. Strategic alone chooses
same-number next letter vs, only after accepted merge verification, `NNN+1-a`.
If `z` insufficient, escalate; no `aa`. Deliberate abandonment requires explicit
strategic/human decision, PR closure + reason; never silently accept or resume
after terminal abandonment without explicit recovery.

Order filename begins `<ID>-`, e.g. `013-a-add-news.md`; at most one
`orders/<ID>-*.md`. Preferred report same basename; at minimum exactly one
unambiguous `reports/<ID>-*.md`. Duplicate matching order/report is protocol
error.

## 4. Planning, publication, immutability

Future `NNN-a` orders may be preplanned/revised but are inert. Activation=
finalize order; atomically publish it; atomically set `active`; signal `OK`.
Once activation `OK` is sent, order is immutable; corrections/additions use next
letter. Once executor publishes report and signals `OK`, report is immutable;
strategic never edits it.

Atomic order/active publication: create temp in same directory/filesystem;
write complete; close; fsync when practical; atomic rename; signal only after
both final files exist. Invariant: reader receiving `OK` can read complete order
and active pointer.

FIFO wire payload EXACTLY two ASCII bytes `OK` = hex `4f 4b`; no newline,
filename, ID, JSON, status, explanation. Semantics `printf 'OK' > fifo`; close
descriptor. FIFOs intentionally block indefinitely. Strategic `OK` means “a
complete active order exists; reread OAP state and execute it.” Coding `OK`
means “turn ended; immutable report and claimed already-published remote state
exist.” Neither means success/acceptance.

## 5. Strategic cycle (normative)

1. Before planning, query GitHub: remote default branch; prior/current PR
   open/closed/merged; continuation PR number/URL/head/current SHA; relevant
   pending/failed checks. GitHub overrides stale checkout/handoff.
2. Choose new `NNN-a` or next same-PR letter.
3. Atomically publish complete order + exact `active`.
4. Write exact `OK` to control FIFO (may block).
5. After write returns, block on response FIFO for exact `OK`; normal protocol
   does not replace handshake with directory polling.
6. Reread `active`; require it equals sent ID; locate exactly one report; read
   completely; extract claimed PR/URL/branch/literal implementation SHA and
   `Report publication commit: SELF`.
7. Independently verify via GitHub: PR exists and uniquely maps objective;
   correct base/head; all claimed commits pushed; literal implementation SHA
   remote; current head is report-only SELF commit containing immutable report,
   first parent=reported implementation SHA; diff matches order; no duplicate
   objective PR; current required checks/reviews/mergeability/policy.
8. Review against all objective orders, constitution, architecture, human intent,
   acceptance, scope/non-goals, security/privacy/trust, tests, docs.
9. Apply merge gate.
10. Transition:
   - accepted+green: strategic merges with repository-approved mode, then
     verifies PR merged and remote default contains result; only then next ID;
   - more work: keep open, issue next letter on same PR;
   - CI failure needing code: next same-PR letter with exact failure;
   - required CI pending: do not merge/advance; wait/recheck;
   - ambiguous/blocking product/architecture/risk: human escalation;
   - explicit abandonment: close, record reason.

## 6. Merge gate and review questions

Merge iff ALL: unique correct objective PR; every initial/follow-up requirement
satisfied; diff/evidence/docs/architecture/security/privacy/scope strategically
satisfactory; every required check present+successful; none failed/cancelled/
missing/pending; protection/policy permits; no unresolved human blocker.
Green CI is necessary, never sufficient. Verify merged state afterward.

For every round establish: exact goal not adjacent work; correct PR mode and
unique PR; pushed/current reported commits; scoped diff and non-goals; concrete
file/test/CI proof per criterion; requested tests really ran; passed/failed/
skipped/not-run/blocked/pending labels honest; live required checks; no unrelated
files/deps/migrations/secrets/deployment/trust changes; docs reflect behavior;
architecture preserved; strongest reason not to merge. Insufficient evidence
requires more work, not sequence velocity.

Executor status `COMPLETE|PARTIAL|BLOCKED|FAILED` is advisory. Coding `OK` only
announces durable turn-end state.

## 7. Work-order requirements

Every order includes:

```text
Objective
GitHub objective state: NNN, NNN-L, CREATE_NEW_PR|AMEND_EXISTING_PR,
  existing PR/URL or N/A, required head or NEW, base
Strategic context; independently verified current state
Bounded scope; explicit non-goals; concrete requirements
Observable acceptance criteria; required tests/CI/E2E evidence
Documentation; safety/security/secrets/data/deployment constraints
Local capability: routine setup belongs to executor; passwordless sudo exists;
  do not transfer package/service/browser/database work to human
GitHub workflow; exact final-report contract
```

`NNN-a` explicitly says NEW PR and requires executor to: fetch/reconcile remote;
start current remote default unless instructed; create fresh objective branch;
implement bounded scope; run verification; commit intended work; push; create
exactly one new objective PR via `gh`; never merge; inspect checks and reasonably
repair in-scope failures within turn; report only already-pushed state; include
PR number/URL, branch/base, literal implementation SHA, SELF marker; commit/push
activated order, `active`, final report under transcript policy. Report cannot
precede remote PR existence.

`NNN-b..z` explicitly says AMEND EXISTING PR and names PR number/URL/head,
useful current SHA, why previous round insufficient, exact remediation/evidence/
CI finding, and NO NEW PR. Executor fetches; verifies named matching open PR;
updates/checks out its branch; adds commits/pushes/PR-body or comments as needed;
never creates second PR or merges; reports only after remote amendment exists.

## 8. Versioned transcript and report self-reference

Each objective PR contains every activated objective order, current `oap/active`,
and every immutable objective report. Strategic creates/owns order+active content;
executor commits existing copies without editing. Executor atomically creates,
publishes, commits, and pushes its report as last commit of the round before
FIFO `OK`.

Self-reference convention:

```text
Implementation head SHA: <literal 40-hex commit before report commit>
Report publication commit: SELF
```

At coding `OK`, remote PR head=commit containing that exact report only; its
first parent=literal implementation head; no unpushed change. Strategic derives
publication SHA from GitHub and verifies tree/parent/path. Later continuations
may advance PR head while retaining earlier report commits. Report records last
check state actually observed; report-commit checks may still be pending and
strategic waits independently. Never amend report merely to insert later CI.

## 9. Passwordless sudo / anti-control inversion

Executor's bounded disposable VM supplies passwordless sudo for safe routine
packages, build tools, test DBs, browsers/Playwright dependencies, services, and
test infrastructure. A report blocked only by admin privilege is an execution
problem to investigate, not work to transfer to human. Real blockers remain:
external/GitHub outage, bad/expired credentials, network, repo policy, protected
resources, product ambiguity, production boundary. Executor operates VM; human
is not package installer/terminal operator.

## 10. Ownership matrix

| Resource/action | Strategic | Coding |
|---|---:|---:|
| orders, active, control FIFO | WRITE | READ |
| reports, response FIFO | READ | WRITE |
| GitHub read/fetch | YES | YES |
| create branch, implementation commits/push, `a` PR, amend PR | normally NO | YES |
| review/accept/merge/choose next transition | exclusively YES | NO/self-check only |

## 11. Failure/restart recovery

- Blocked control write=no coding reader; published order remains durable.
- Blocked response read=turn incomplete or executor stopped/crashed. Fabricate
  nothing; merge/advance nothing.
- Strategic restart: read `active`; exact order; exact report if any; inspect
  GitHub PR. Report+open PR→review both. Report+merged PR→verify merge and whether
  next already activated. No report+new pushed commits→interrupted, not complete.
  No report/no `a` PR→unresolved/interrupted. GitHub beats local software state.
- Duplicate/unexpected PR: protocol violation; inspect/preserve both; do not
  merge either as automatic recovery; issue deliberate closure/remediation.
- CI after report: pending means wait; failure needing edits means next same-PR
  letter; never treat old/superseded checks as current-head proof.

## 12. Invariants (complete compact set)

1. GitHub=software truth; VM/checkout disposable/non-authoritative.
2. OAP files=orchestration truth; FIFO=sync only; one exact active ID.
3. Coding executes only active; exact unique order+report mapping.
4. `a` creates one PR; `b..z` amend it; one numeric objective=one PR.
5. Claimed implementation commits and required PR state are remote before report.
6. Activated orders, active pointer, reports are committed/pushed on objective PR.
7. Report has literal implementation parent+SELF; strategic verifies containing
   GitHub commit, exact report, parent.
8. Activated order/published report immutable.
9. Strategic independently verifies GitHub; report confidence is not proof.
10. Green CI necessary not sufficient; strategic satisfaction required.
11. Every required check successful; none pending/failed/cancelled/missing.
12. Only strategic merges and chooses continuation vs next objective; coding
    never merges/accepts/chooses roadmap.
13. Next numeric ID waits until current resolved; accepted work additionally
    merged and remote-main verified.
14. `OK` never means success and carries exactly no metadata/newline.
15. Passwordless sudo keeps routine work with executor.
16. Human remains ultimate intent/risk/release owner.

Canonical lifecycle example: strategic verifies main→publishes/signals `013-a`;
executor creates branch+PR42, pushes implementation+report, signals; strategic
finds missing E2E and publishes/signals `013-b`; executor amends PR42 (no PR2),
pushes report/signals; strategic independently verifies all requirements/checks,
merges PR42, verifies remote main, then and only then activates `014-a`.
