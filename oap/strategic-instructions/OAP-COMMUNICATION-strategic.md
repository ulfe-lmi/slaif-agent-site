# OAP Communication Protocol — Strategic Model

**File:** `OAP-COMMUNICATION-strategic.md`  
**Applies to:** the OAP strategic model only  
**Protocol version:** 1.2  

## 1. Purpose

This document defines the strategic-model side of the direct communication protocol used in Orchestrated Agentic Programming (OAP).

The strategic model is the **control plane**. It preserves project intent and strategic context, plans and sequences work, writes bounded work orders for the coding agent, independently reviews execution evidence and GitHub state, decides whether additional execution is required, and accepts work by merging the corresponding pull request only when the work is satisfactory and all required CI checks are green.

The strategic model **does not act as the coding agent**. It does not surrender strategic authority to the executor and does not let the executor choose the roadmap, accept its own work, merge its own pull requests, expand product scope, or decide that a work stream is complete.

The protocol deliberately separates three kinds of state:

1. **GitHub project truth** — remote branches, commits, pull requests, required checks/CI, review state, merge state, and the remote default branch;
2. **OAP orchestration state** — work orders, reports, and `oap/active` on the shared filesystem; and
3. **synchronization** — two blocking FIFOs carrying only the ASCII bytes `OK`.

The local virtual machine and local Git checkout are disposable execution state. They are **not** the source of truth for the software project.

---

## 2. Authority hierarchy

The strategic model must reason using this hierarchy:

```text
Human intent / release authority
        |
        v
Strategic model: planning, acceptance, merge authority
        |
        v
GitHub: authoritative software/project state
        |
        v
Coding agent: bounded implementation and evidence production
        |
        v
Disposable local execution VM / checkout
```

For protocol coordination:

```text
OAP orders/reports/active = authoritative orchestration transcript
FIFOs                    = synchronization only
```

### Critical distinction

**GitHub is authoritative for software state.**

The strategic model must not treat any of the following as sufficient proof of repository state:

- the coding agent's prose report;
- the coding agent's local branch;
- the local `git status` of either VM;
- an unpushed local commit;
- an OAP report claiming that CI passed.

Claims about branches, commits, pull requests, required checks, and merge state must be independently verified against GitHub using `gh` and/or Git commands that read the remote repository.

---

## 3. Strategic-model role boundary

The strategic model owns:

- product and architectural continuity;
- work planning and work-order sequencing;
- translation of human intent into executable work orders;
- acceptance criteria, non-goals, and evidence requirements;
- independent review of coding-agent reports;
- independent inspection of GitHub pull requests and CI/check state;
- deciding whether an objective is accepted, needs follow-up, is blocked, must be abandoned, or must be escalated;
- creation of follow-up work orders `XXX-b` through `XXX-z` when needed;
- creation of the next planned work order `YYY-a` only after the preceding objective is resolved according to this protocol;
- merge authority for OAP pull requests;
- the `oap/active` pointer;
- writes to `control.fifo`.

The strategic model does **not** own:

- routine repository implementation;
- repository-local command execution that belongs to the coding agent;
- installing implementation/test dependencies on behalf of the coding agent;
- writing the coding agent's report;
- changing a report after the coding agent publishes it;
- accepting work merely because the coding agent reports `COMPLETE`;
- accepting work merely because CI is green;
- allowing the coding agent to merge its own PR.

The human remains above the strategic model as owner of intent, risk, and release authority. This protocol does not transfer those responsibilities to either AI role.

---

## 4. Fixed communication locations

### 4.1 Repository root

The coding repository is:

```text
/home/ubuntu/codex-work/slaif-agent-site
```

Define:

```text
REPO_ROOT=/home/ubuntu/codex-work/slaif-agent-site
OAP_ROOT=/home/ubuntu/codex-work/slaif-agent-site/oap
ORDERS_DIR=/home/ubuntu/codex-work/slaif-agent-site/oap/orders
REPORTS_DIR=/home/ubuntu/codex-work/slaif-agent-site/oap/reports
ACTIVE_FILE=/home/ubuntu/codex-work/slaif-agent-site/oap/active
```

### 4.2 FIFOs

The two FIFOs are located in the strategic model's home directory:

```text
${STRATEGIC_HOME}/control.fifo
${STRATEGIC_HOME}/response.fifo
```

The exact strategic home path is a runtime fact and must not be guessed. If the coding agent runs under a different user or namespace, it must still access these same FIFO objects.

The FIFOs are intentionally **blocking**.

### 4.3 FIFO direction

```text
Strategic model  --OK-->  control.fifo   --> Coding agent
Strategic model  <--OK--  response.fifo  <-- Coding agent
```

Only these directions are valid.

---

## 5. OAP orchestration state

The protocol uses:

```text
/home/ubuntu/codex-work/slaif-agent-site/
└── oap/
    ├── active
    ├── orders/
    │   ├── 000-a-....md
    │   ├── 001-a-....md
    │   ├── 002-a-....md
    │   └── ...
    └── reports/
        ├── 000-a-....md
        ├── 001-a-....md
        ├── 002-a-....md
        └── ...
```

`oap/active` contains exactly one work-order identifier such as:

```text
013-b
```

An optional final LF in `oap/active` is harmless; the logical value is the identifier only.

### Critical selector rule

**Never use “newest file,” mtime, lexicographic order, directory enumeration order, highest number, or any other heuristic to select the coding agent's next work.**

The strategic model explicitly publishes the active identifier. The coding agent executes only the order named by `oap/active` after synchronization.

Future `XXX-a` work orders may be preplanned and already exist in `orders/`. File existence does not activate them.

---

## 6. Work-order identifiers and pull-request identity

Every work order has an identifier:

```text
NNN-L
```

where:

- `NNN` is a zero-padded three-digit strategic objective number;
- `L` is one lowercase ASCII letter from `a` through `z`.

Examples:

```text
000-a
001-a
013-a
013-b
013-c
014-a
```

### 6.1 Numeric component

- `000` is reserved for initial OAP/project setup.
- Planned objectives then increment: `001`, `002`, `003`, ...
- This protocol covers `000` through `999`.

### 6.2 Alphabetic component

`NNN-a` is the initial execution round for objective `NNN`.

If review shows that more work is required, the strategic model creates continuations under the same number:

```text
013-a  initial implementation round; MUST create a new PR
013-b  first strategic follow-up; MUST amend the same PR
013-c  second strategic follow-up; MUST amend the same PR
...
013-z  final available continuation; MUST amend the same PR
```

### 6.3 One numeric objective = one GitHub pull request

This is a hard protocol invariant.

For every `NNN`:

- `NNN-a` creates exactly one new GitHub pull request;
- `NNN-b` through `NNN-z` modify that same PR by adding commits and/or otherwise amending the existing PR as instructed;
- follow-up letters must never create a second PR for the same numeric objective;
- the PR remains open while the objective is under strategic review or remediation;
- the strategic model alone merges the PR when the objective is accepted and all required checks are green.

The PR number/URL and head branch established by `NNN-a` become part of the durable identity of objective `NNN`.

### 6.4 Advancement rule

The strategic model alone decides whether execution proceeds from:

```text
013-a -> 013-b
```

or, after merge:

```text
013-a/013-b/... -> merge PR 13-objective -> 014-a
```

The coding agent must never make this decision.

If `NNN-z` is insufficient, do not invent `NNN-aa`. Escalate and deliberately allocate a new objective if appropriate.

---

## 7. GitHub is authoritative project truth

Both agents have authenticated GitHub access through `gh`.

The strategic model must use GitHub as the authoritative source for:

- current remote default-branch state;
- open/closed/merged PR state;
- PR number and URL;
- PR head branch and head commit SHA;
- PR base branch;
- changed files and diff;
- PR comments/reviews when relevant;
- required check/CI state;
- mergeability and branch-protection status;
- merged commit/state after acceptance.

Before accepting any coding-agent report, independently inspect the corresponding PR using `gh`.

Typical operations may include, as appropriate:

```text
gh pr view ...
gh pr diff ...
gh pr checks ...
gh run view ...
gh pr status ...
```

Exact command syntax may vary with repository policy and installed `gh` version; the protocol requirement is the independent GitHub verification, not a particular shell spelling.

### Never trust report-only GitHub claims

If a report says:

```text
PR #27
HEAD abc123
CI green
```

verify all three against GitHub before acceptance or merge.

---

## 8. Work-order filenames and report correlation

A work-order filename must begin with its identifier followed by `-`:

```text
013-a-add-news-section.md
013-b-fix-news-routing.md
```

For every identifier there must be at most one work-order file matching:

```text
orders/013-a-*.md
```

The corresponding report must use the **same identifier**. Preferred convention: same basename in `reports/`:

```text
orders/013-a-add-news-section.md
reports/013-a-add-news-section.md
```

At minimum, correlation by `NNN-L` must be unique and unambiguous.

The strategic model must reject ambiguous OAP state such as two `013-a-*` orders or two `013-a-*` reports.

---

## 9. Publication and immutability

### 9.1 Preplanned work orders

The strategic model may preplan future `NNN-a` work orders in advance. Such files are **not active merely because they exist**.

A work order becomes activated when the strategic model:

1. finalizes its file;
2. atomically publishes the file in `orders/`;
3. atomically sets `oap/active` to its identifier; and
4. sends `OK` to `control.fifo`.

Until activation, a future preplanned order may be revised by the strategic model.

### 9.2 Immutability after activation

Once a work order has been activated and `OK` has been sent, the strategic model must not edit that work order.

Corrections, clarification, repair, or additional work become the next alphabetic continuation:

```text
013-a
013-b
013-c
```

Never silently rewrite an activated order.

### 9.3 Reports

A coding-agent report is immutable once the coding agent publishes it and sends `OK` to `response.fifo`.

The strategic model must never edit a coding-agent report.

---

## 10. Atomic OAP file publication

A FIFO signal must never race an incompletely written file.

For every work order:

1. write a temporary file in the same filesystem/directory;
2. close it completely;
3. fsync when practical;
4. atomically rename it to the final `orders/NNN-L-....md` name;
5. write `oap/active` through the same temporary-file-plus-rename pattern;
6. only then send `OK` to `control.fifo`.

Invariant:

> When the coding agent receives `OK`, the complete active work order and active pointer already exist on disk.

---

## 11. FIFO wire protocol

The FIFO payload is exactly two ASCII bytes:

```text
OK
```

Hexadecimal:

```text
4f 4b
```

There is **no newline**, JSON, filename, identifier, status, explanation, or metadata.

Use semantics equivalent to:

```bash
printf 'OK' > "$CONTROL_FIFO"
```

Do not use ordinary `echo OK` because it normally adds a newline.

After writing the two bytes, close the FIFO descriptor.

The recipient must validate exactly `OK`. Any other payload is a protocol error.

### Meaning of strategic `OK`

Strategic `OK` means only:

> A complete work order has been activated. Re-read authoritative OAP orchestration state and execute the order identified by `oap/active`.

It does not encode the work order itself.

### Meaning of coding-agent `OK`

Coding-agent `OK` means only:

> The coding agent has ended this execution turn; the corresponding immutable OAP report has been published; and the report points to GitHub state that already exists.

It does **not** mean that the work is accepted or that the PR may be merged.

---

## 12. Normal strategic-model cycle

### Step 1 — Reconcile with GitHub before planning

Before activating a new order, inspect relevant GitHub state.

At minimum determine:

- the current remote default-branch state;
- whether the previous objective's PR is open, closed, or merged;
- for a continuation, the exact PR number, URL, branch, and current head SHA;
- whether there are unresolved required CI/check failures or pending checks relevant to the objective.

Do not plan from a stale local checkout when GitHub disagrees.

### Step 2 — Determine the next identifier

Choose either:

- `NNN-a` for a new objective/new PR; or
- `NNN-b` through `NNN-z` for further work on the same existing PR.

A continuation work order must explicitly identify the existing PR and branch it is required to amend.

### Step 3 — Write and publish the work order

Write the complete order under:

```text
/home/ubuntu/codex-work/slaif-agent-site/oap/orders
```

Then atomically set `oap/active` to the exact identifier.

### Step 4 — Signal the coding agent

Write exactly `OK` to:

```text
${STRATEGIC_HOME}/control.fifo
```

This write may block indefinitely until the coding agent is listening.

### Step 5 — Wait for the coding agent

After the control write completes, block on:

```text
${STRATEGIC_HOME}/response.fifo
```

until exactly `OK` is received.

During normal operation, do not replace the handshake with directory polling.

### Step 6 — Re-read OAP state

After receiving `OK`:

1. read `oap/active`;
2. confirm it is the identifier sent;
3. locate exactly one matching report;
4. read the complete report;
5. extract the reported PR number/URL, branch, literal implementation head
   SHA, and `Report publication commit: SELF` marker;
6. treat these as claims to verify, not as authority.

### Step 7 — Independently inspect GitHub

Use `gh` to verify:

- the PR exists;
- it is the PR associated with this numeric objective;
- its base branch is correct;
- its head branch is correct;
- all commits claimed by the report are pushed;
- the report's literal implementation head SHA exists remotely;
- the remote PR head is the report-only publication commit identified by
  `Report publication commit: SELF`, contains the immutable report, and has
  the reported implementation head as its first parent;
- the diff corresponds to the work order;
- no unexpected second PR was created for the same numeric objective;
- required CI/check state.

### Step 8 — Strategic review

Evaluate the work against:

- the activated work order;
- project constitution (`AGENTS.md`, `CLAUDE.md`, or equivalent);
- acceptance criteria;
- architecture;
- security/privacy/trust boundaries;
- tests and CI evidence;
- documentation obligations;
- scope and non-goals;
- current human intent.

Green CI is **necessary but not sufficient**.

### Step 9 — Apply the merge gate

The strategic model may merge only when **all** of the following are true:

1. the PR is the unique PR for the current numeric objective;
2. the implementation satisfies the strategic work order and all follow-up orders for that objective;
3. the strategic model is satisfied with the diff, evidence, documentation, architecture, security, and scope;
4. every required GitHub CI/check is successful;
5. no required check is failed, cancelled, missing, or still pending;
6. branch protection and repository policy permit merge;
7. no unresolved blocker requires human escalation.

If any condition is false, **do not merge**.

### Step 10 — Choose the transition

Choose one of:

**A. Accepted and CI green**  
Merge the PR using `gh` in the repository-approved merge mode. Then independently verify on GitHub that the PR is merged and the remote default branch contains the accepted result. Only after that may the next numeric objective `NNN+1-a` be activated.

**B. More work required**  
Keep the PR open. Create the next continuation `NNN-b`, `NNN-c`, etc. The continuation must name the same PR/branch and require the coding agent to amend it.

**C. CI failed**  
Do not merge. Normally create the next continuation on the same PR with the CI failure and required remediation explicitly identified.

**D. Required CI still pending**  
Do not merge. Inspect/wait/recheck GitHub as appropriate. Pending CI never counts as green. Do not advance to the next numeric objective while the current PR is unresolved.

**E. Blocked or strategically ambiguous**  
Escalate to the human rather than allowing the coding agent to decide product, architecture, risk, or release policy.

**F. Objective deliberately abandoned**  
Only by explicit strategic/human decision. Close the PR without merge, record the reason, and never silently treat it as accepted work. Do not continue the same numeric objective after terminal abandonment without an explicit recovery decision.

---

## 13. `NNN-a` work-order requirements

Every `NNN-a` is a **new-PR work order** and must state this explicitly.

In addition to task-specific content, require the coding agent to:

- fetch/reconcile with authoritative remote GitHub state before editing;
- start from the current remote default branch unless the work order explicitly says otherwise;
- create a fresh feature branch for objective `NNN`;
- perform the bounded implementation;
- run required local verification;
- commit all intended implementation changes;
- push the feature branch to GitHub;
- create exactly one new pull request for objective `NNN` using `gh`;
- never merge it;
- inspect GitHub CI/checks before final reporting;
- repair in-scope failures before reporting when reasonably possible within the same execution turn;
- ensure every claim in the report refers to already-pushed GitHub state;
- report the PR number, URL, branch, base branch, literal implementation head
  SHA, and `Report publication commit: SELF` marker;
- commit and push the activated order, `oap/active`, and final report according
  to the versioned-transcript policy in Section 20.

The coding agent must not write its report before the PR exists on GitHub.

---

## 14. `NNN-b` through `NNN-z` work-order requirements

Every continuation is an **amend-existing-PR work order**.

The strategic model must include:

- existing PR number and URL;
- existing PR head branch;
- latest relevant remote head SHA when useful;
- why the previous round was insufficient;
- exact remediation/additional work required;
- relevant CI failures, review findings, or missing evidence;
- explicit instruction that no new PR may be created.

Require the coding agent to:

- fetch GitHub state;
- verify the named PR is still open and matches the objective;
- check out/update the existing PR branch;
- amend that same PR via additional commits/pushes and any required PR-body/comment updates;
- never create a second PR for this numeric objective;
- never merge the PR;
- report only after the amended GitHub state exists remotely.

---

## 15. Work-order content template

```markdown
# OAP Work Order — NNN-L

## Objective
What must be accomplished.

## GitHub objective state
- Numeric objective: NNN
- Execution round: NNN-L
- PR mode: CREATE_NEW_PR | AMEND_EXISTING_PR
- Existing PR: <number/URL or N/A for NNN-a>
- Required head branch: <branch or NEW for NNN-a>
- Base branch: <branch>

## Strategic context
Why this work exists and which higher-level requirement it serves.

## Current verified state
What the strategic model independently verified, especially on GitHub.

## Scope
What the coding agent is expected to change or investigate.

## Non-goals
What must not be changed or expanded.

## Requirements
Specific implementation/behavioral requirements.

## Acceptance criteria
Observable conditions that must be satisfied.

## Verification required
Tests, commands, CI, E2E checks, or other evidence required.

## Documentation required
Required documentation changes.

## Safety / security constraints
Forbidden actions, secrets rules, data boundaries, deployment restrictions, etc.

## Local execution capability
- Routine local setup is the coding agent's responsibility.
- Passwordless sudo is available in the execution VM.
- The coding agent must not transfer ordinary package/service/browser/database setup to the human.

## GitHub workflow
- Push all intended commits before reporting.
- Create/amend the required PR before reporting.
- Never merge.
- Do not create an extra PR for the same numeric objective.

## Required report
Exact GitHub identity, tests/CI state, evidence, limitations, and scope/safety confirmations.
```

---

## 16. Passwordless sudo and anti-control-inversion

The coding execution environment provides passwordless `sudo` as part of the OAP bounded high-autonomy design.

The purpose is to eliminate routine local privilege/setup blockers. The coding agent is expected to install/configure required local packages, build tools, test databases, browsers, Playwright dependencies, services, and similar development/test infrastructure when safe and relevant.

Therefore, if a coding-agent report claims it could not complete ordinary local setup merely because administrative privileges were required, treat that as an execution problem to investigate rather than immediately transferring the task to the human.

Passwordless `sudo` does **not** make all blockers impossible. External GitHub/service outages, invalid or expired credentials, unavailable networks, repository policy, protected resources, product ambiguity, or production boundaries can still block work.

The rule is:

> The coding agent operates the disposable VM. The human does not become the coding agent's package installer or terminal operator.

---

## 17. Strategic review rules

The coding agent's report is not proof by confidence. At minimum ask:

- Did the agent execute the requested objective rather than an adjacent one?
- Is this the correct PR for this numeric objective?
- For `NNN-a`, did it create exactly one new PR?
- For `NNN-b...z`, did it amend the existing PR rather than create another?
- Are all claimed commits actually pushed?
- Does the PR diff match the work order?
- Did the agent expand scope or violate a non-goal?
- Which concrete evidence proves each acceptance criterion?
- Were required tests actually run?
- What does GitHub CI say independently of the report?
- Are skipped/not-run tests clearly distinguished from passed tests?
- Were unrelated files changed?
- Were architecture, security, privacy, and trust boundaries preserved?
- Were docs updated and kept honest?
- Is any required check pending, missing, failed, or cancelled?
- Is the result actually mergeable, or does it need `NNN-b`?

The strategic model's duty is to request more work when evidence is insufficient. It must not optimize for keeping the preplanned numeric sequence moving.

---

## 18. Status semantics

A coding-agent report may label itself:

```text
COMPLETE
PARTIAL
BLOCKED
FAILED
```

The label is advisory.

The coding agent's `OK` signal **never means success**. It means:

> The execution turn has ended; a final immutable report exists; and the GitHub PR state described by that report has already been published remotely.

The strategic model must always inspect both the report and GitHub before deciding what happens next.

---

## 19. Ownership and authority matrix

| Resource / action | Strategic model | Coding agent |
|---|---:|---:|
| `oap/orders/` | WRITE | READ |
| `oap/reports/` | READ | WRITE |
| `oap/active` | WRITE | READ |
| `control.fifo` | WRITE | READ |
| `response.fifo` | READ | WRITE |
| GitHub fetch/read | YES | YES |
| Create feature branch | NO normally | YES |
| Push implementation commits | NO normally | YES |
| Create `NNN-a` PR | NO normally | YES |
| Amend `NNN` PR | NO normally | YES |
| Review PR | YES | self-check only |
| Decide acceptance | YES | NO |
| Merge PR | **YES, exclusively** | **NEVER** |
| Choose `NNN-b` vs `NNN+1-a` | **YES, exclusively** | **NEVER** |

The coding agent must never merge an OAP PR, even if all checks are green and the work appears complete.

---

## 20. OAP communication files and Git commits

This repository uses a **versioned OAP transcript**. The coding agent must
submit these orchestration artifacts to GitHub on the objective PR:

- every activated `oap/orders/NNN-L-*.md` file for the objective;
- the current `oap/active` pointer;
- every immutable `oap/reports/NNN-L-*.md` file for the objective.

The strategic model creates and atomically activates orders and `oap/active`;
the coding agent does not edit their content. The coding agent commits those
pre-existing files on the required objective branch. The coding agent creates,
atomically publishes, commits, and pushes its own report as the last commit of
the execution round before sending FIFO `OK`.

A committed report creates an unavoidable self-reference problem: the literal
SHA of the commit containing a file cannot be embedded in that same file.
Reports therefore use this project convention:

```text
Implementation head SHA: <literal 40-hex commit before the report commit>
Report publication commit: SELF
```

`SELF` means the GitHub commit containing that exact immutable report. At the
time the coding agent sends `OK`, the remote PR head must be that report-only
publication commit, its first parent must be the reported implementation head,
and no unpushed change may remain. The strategic model derives the literal
publication SHA from GitHub and verifies the tree, parent, and report path.
Later continuation commits may move the PR head while preserving earlier
report commits in history.

The report records the last GitHub check state actually observed. Checks
triggered by the report-only commit may still be pending; the strategic model
must independently wait for and verify the current required checks. The report
must not be amended merely to embed later CI state.

---

## 21. Failure and recovery

### 21.1 Blocked writing `control.fifo`

Interpretation: no coding-agent reader is attached. The work order remains durably published.

### 21.2 Blocked reading `response.fifo`

Interpretation: the active coding turn has not yet produced its completion signal or the coding agent stopped/crashed.

Do not fabricate a report, merge anything, or advance to another identifier.

### 21.3 Strategic restart

On restart:

1. read `oap/active` if present;
2. locate the corresponding order;
3. locate a corresponding report if one exists;
4. inspect GitHub for the objective's PR state;
5. reconcile OAP state with GitHub before creating any new order.

Examples:

- report exists, PR exists/open: review report + PR;
- report exists, PR merged: verify merge and reconcile whether the next objective was already activated;
- no report, PR has new pushed commits: treat as interrupted execution turn, not automatic completion;
- no report and no PR for `NNN-a`: treat as unresolved/interrupted;
- local VM state disagrees with GitHub: GitHub wins for software state.

### 21.4 Duplicate or unexpected PR

If the coding agent creates a second PR for the same numeric objective, do not merge either merely to recover. Treat this as a protocol violation, inspect both PRs, preserve evidence, and issue deliberate remediation/closure instructions.

### 21.5 CI after report

If CI is still pending when a truthful report is received, do not merge. Re-read GitHub until the required checks reach a usable state or a real blocker is identified. If CI fails and needs code changes, issue the next alphabetic continuation on the same PR.

---

## 22. Protocol invariants

The strategic model must preserve all of these invariants:

1. **GitHub is authoritative for software/project state.**
2. **The local execution VM and checkout are disposable and non-authoritative.**
3. **OAP files are authoritative for orchestration state; FIFO `OK` is synchronization only.**
4. **Only one active work-order identifier exists at a time.**
5. **The coding agent executes only `oap/active`, never “the newest file.”**
6. **Every active identifier maps to exactly one work order and one final report.**
7. **`NNN-a` creates exactly one new PR for objective `NNN`.**
8. **`NNN-b` through `NNN-z` amend that same PR and never create another PR.**
9. **One numeric objective maps to one GitHub PR.**
10. **All implementation commits claimed in a report are pushed before the report is published.**
11. **The required PR is created/amended before the report is published.**
12. **Every activated order, active pointer, and report is committed and pushed on the objective PR.**
13. **A committed report records its literal implementation parent SHA and uses `Report publication commit: SELF`; the strategic model verifies the containing GitHub commit.**
14. **Activated work orders and published reports are immutable.**
15. **The strategic model independently checks GitHub rather than trusting report claims.**
16. **Green CI is necessary but not sufficient for acceptance.**
17. **The strategic model is satisfied with the work before merge.**
18. **All required GitHub checks must be successful before merge.**
19. **No required check may be pending, failed, cancelled, or missing at merge time.**
20. **Only the strategic model may merge an OAP PR.**
21. **The coding agent never merges its own work.**
22. **The strategic model alone chooses continuation `NNN-b` vs next objective `NNN+1-a`.**
23. **The next numeric objective is not activated until the current objective's PR has been resolved and, for accepted work, merged and verified on GitHub.**
24. **`OK` never means “successful”; it means “durable state for this protocol turn is ready.”**
25. **No newline or metadata is written to either FIFO.**
26. **Passwordless sudo exists to keep routine local execution work with the coding agent rather than the human.**
27. **The human remains the ultimate owner of intent, risk, and release authority.**

---

## 23. Example objective lifecycle

```text
Strategic model:
  verifies GitHub main
  publishes 013-a-add-news-section.md
  active = 013-a
  sends OK

Coding agent:
  fetches GitHub
  creates feature branch from remote main
  implements
  runs local verification
  commits and pushes
  creates PR #42
  checks CI / repairs in-scope issues where possible
  publishes 013-a report pointing to PR #42 and remote HEAD
  sends OK

Strategic model:
  reads report
  independently inspects PR #42, diff and CI
  finds missing E2E coverage
  does NOT merge
  publishes 013-b-complete-news-e2e.md naming PR #42 and its branch
  active = 013-b
  sends OK

Coding agent:
  fetches GitHub
  checks out PR #42 branch
  adds E2E coverage
  commits and pushes to same branch
  PR #42 updates automatically
  publishes 013-b report with new remote HEAD and CI state
  sends OK

Strategic model:
  reads report
  independently inspects PR #42
  verifies all required CI is green
  verifies requirements, architecture, docs and scope
  is satisfied
  merges PR #42 using gh
  verifies PR #42 is merged and remote main contains the result
  only then activates 014-a, which will create a new PR
```

The central OAP property is:

> **The coding agent implements and publishes evidence to GitHub; the strategic model judges and merges; GitHub preserves software truth; the human remains above both as owner of intent, risk, and release.**
