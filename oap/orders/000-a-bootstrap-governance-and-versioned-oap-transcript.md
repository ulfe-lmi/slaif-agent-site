# OAP Work Order — 000-a

## Objective

Create exactly one new GitHub pull request that bootstraps the SLAIF
Agent-Site repository governance and its **versioned OAP transcript**.

This is the first protocol integration test. The result must place the
canonical architecture and coding-agent governance in the repository and must
submit this activated order, `oap/active`, and the coding-agent report to
GitHub on the same objective PR.

## GitHub objective state

- Numeric objective: `000`
- Execution round: `000-a`
- PR mode: `CREATE_NEW_PR`
- Existing PR: N/A
- Required head branch: `oap/000-bootstrap-governance`
- Base branch: `main`
- Required PR title: `[OAP 000] Bootstrap architecture and versioned orchestration`
- Required PR readiness: non-draft (`draft: false`)
- Repository: `ulfe-lmi/slaif-agent-site`
- Repository URL: `https://github.com/ulfe-lmi/slaif-agent-site`

## Strategic context

The human has explicitly decided that this repository versions its OAP
orchestration transcript. Orders, reports, and `oap/active` are therefore
submitted by the coding agent to the objective PR rather than ignored as
local-only operational state.

This policy requires a verifiable solution to Git commit self-reference. A
report cannot contain the literal SHA of the commit that contains that report.
For this repository, every committed report therefore records:

```text
Implementation head SHA: <literal 40-hex commit before the report commit>
Report publication commit: SELF
```

`SELF` means the GitHub commit containing that exact immutable report. At the
time the coding agent sends FIFO `OK`, the remote PR head must be that
report-only commit, and its first parent must equal the literal implementation
head SHA recorded in the report. The strategic model derives and verifies the
literal report-publication SHA from GitHub.

The corresponding strategic-side communication protocol is now version 1.2.
This work order must submit the aligned coding-side version 1.2 policy.

## Current verified state

The strategic model independently verified the following before activation:

- Remote default branch: `main`
- Remote `main` SHA: `8a9d32ac11d6b1d75c87f016a73d732cd082b9c7`
- Remote `main` commit message: `Initial commit`
- Open pull requests: none
- Classic branch protection on `main`: not enabled
- Repository rulesets: none
- Tracked root files on `main`: `.gitignore`, `LICENSE`, and `README.md`
- No product code, CI workflow, or prior OAP transcript is tracked yet.
- The coding checkout is intentionally on local `main` and contains these
  pre-positioned, untracked governance artifacts:
  - `AGENTS.md`
  - `ARCHITECTURE.md`
  - `OAP-COMMUNICATION-coding-agent.md`
  - `oap/orders/000-a-bootstrap-governance-and-versioned-oap-transcript.md`
  - `oap/active`
- `oap/reports/` exists and is intentionally empty before execution.
- `ARCHITECTURE.md` is an exact copy of strategic Revision 2.1 with SHA-256:
  `a6e05a2aa67dcb43d7a4c94ada7037b33a4d1f0202f5f919cc780b2900e390a0`.

Preserve the pre-positioned files. Do not reset, clean, discard, overwrite, or
silently regenerate them. Reconcile remote state before editing; if GitHub now
differs materially from the verified state, report the difference and proceed
only when the objective remains safe and unambiguous.

## Scope

Only the repository-governance and OAP bootstrap below is in scope:

1. Create the required branch from authoritative `origin/main` while
   preserving the intentional untracked bootstrap artifacts.
2. Add the canonical `ARCHITECTURE.md` byte-for-byte.
3. Add and align the coding-agent `AGENTS.md`.
4. Add and align `OAP-COMMUNICATION-coding-agent.md` as protocol version 1.2.
5. Create `oap/README.md` documenting the repository's versioned-transcript
   policy and directory contract.
6. Commit this activated work order and `oap/active` unchanged.
7. Push the implementation/governance commit(s), create exactly one new
   non-draft PR, and verify its GitHub identity.
8. Atomically publish the required coding-agent report, commit it as the final
   report-only commit, push it, verify the PR head, and only then signal the
   strategic model.

## Required tracked files

The final PR diff against `main` must contain exactly these paths:

```text
AGENTS.md
ARCHITECTURE.md
OAP-COMMUNICATION-coding-agent.md
oap/README.md
oap/active
oap/orders/000-a-bootstrap-governance-and-versioned-oap-transcript.md
oap/reports/000-a-bootstrap-governance-and-versioned-oap-transcript.md
```

Do not add `.gitkeep` files: the committed order and report make both
directories durable. Do not add ignore rules for `oap/active`, orders, or
reports; these files are intentionally versioned.

## Non-goals

- Do not create the product monorepo skeleton from Architecture Section 12.
- Do not add application code, tests, dependencies, lockfiles, Compose,
  containers, CI workflows, or deployment files.
- Do not change `README.md`, `LICENSE`, or `.gitignore`.
- Do not edit the content of this activated work order or `oap/active`.
- Do not edit `ARCHITECTURE.md`; preserve it byte-for-byte.
- Do not copy the strategic-only constitution or strategic communication
  protocol into the coding repository.
- Do not implement any Agent-Site feature.
- Do not create an issue, release, tag, second branch, or second PR.
- Do not merge or enable auto-merge.

## Requirements

### 1. Preserve the architecture exactly

- Track the pre-positioned root `ARCHITECTURE.md` unchanged.
- Verify its complete SHA-256 is
  `a6e05a2aa67dcb43d7a4c94ada7037b33a4d1f0202f5f919cc780b2900e390a0`.
- Do not reformat, normalize, summarize, or regenerate the document.

### 2. Align the coding-agent constitution

Keep the existing coding-role prefix, architecture guardrails, and OAP role
separation. Replace the prior default/local-only OAP commit wording with an
explicit project rule that:

- the coding agent commits and pushes every activated order, `oap/active`, and
  corresponding report on the objective PR;
- the strategic model retains content ownership of orders and `oap/active`;
- the coding agent does not edit activated orders or `oap/active` but commits
  the already-published files;
- the coding agent owns and atomically publishes report content;
- committed reports use the `Implementation head SHA` plus
  `Report publication commit: SELF` convention;
- the report commit is final for that execution round and changes only the new
  report file;
- the coding agent still never merges.

### 3. Upgrade and align the coding communication protocol

Set `OAP-COMMUNICATION-coding-agent.md` to protocol version `1.2`. Preserve all
existing version 1.1 safety, FIFO, authority, PR-identity, immutability, and
anti-control-inversion rules, while making the versioned-transcript policy
internally consistent throughout the document.

At minimum, update the normal loop, `NNN-a`/continuation procedures, report
publication rules, report template, OAP-Git policy, and invariant list so they
require:

1. commit/push the activated order and `oap/active` without editing them;
2. create/amend the correct PR before the report;
3. record the exact literal implementation head SHA in the report;
4. use `Report publication commit: SELF` for the self-containing commit;
5. atomically publish the report locally;
6. create a final report-only Git commit whose first parent is the recorded
   implementation head;
7. push that commit and verify it is the remote PR head;
8. send exact FIFO `OK` only after the report commit is remote;
9. allow CI triggered by the report-only commit to be reported as pending and
   independently verified by the strategic model without rewriting the
   immutable report.

Remove or revise statements that say OAP artifacts are ignored or not
committed by default for this repository. Do not weaken any other rule.

### 4. Add `oap/README.md`

Keep it concise and document:

- `oap/active` as the sole active-order selector;
- `oap/orders/` as strategic-model-authored immutable orders;
- `oap/reports/` as coding-agent-authored immutable reports;
- `NNN-a` creates one PR and `NNN-b` through `NNN-z` amend it;
- all three artifact classes are committed on the objective PR;
- FIFO `OK` is synchronization only and the FIFO objects live outside the
  repository;
- the `SELF` report-publication convention and how it is verified;
- no secrets may appear in OAP artifacts.

Reference the root coding protocol for full behavior rather than duplicating
it in full.

### 5. Preserve the activated order and pointer

- Commit this order byte-for-byte at its current final path.
- Commit `oap/active` with the logical value `000-a` only; one final LF is
  permitted.
- Do not edit either after the strategic FIFO signal.

### 6. GitHub publication sequence

1. Fetch and verify authoritative GitHub state.
2. Create `oap/000-bootstrap-governance` from current `origin/main` while
   preserving the pre-positioned bootstrap files.
3. Make only the required governance/protocol/README edits.
4. Stage only the explicit required paths; never use `git add .`, `git add -A`,
   or `git add --all`.
5. Commit and push the governance implementation.
6. Create exactly one non-draft PR with the required title, base, and head.
7. Verify the PR number, URL, base/head, remote implementation head, changed
   files, and current check state.
8. Atomically publish the report at the exact required report path.
9. Commit only that report file in a final report-publication commit.
10. Push it and verify the remote PR head is the containing `SELF` commit and
    its first parent is the report's literal implementation head SHA.
11. Do not modify or push anything else after the report commit.
12. Send exact FIFO `OK` with no newline.

## Acceptance criteria

1. Exactly one open, non-draft PR exists for objective `000`, with base
   `main`, head `oap/000-bootstrap-governance`, and the required title.
2. The PR diff against `main` contains exactly the seven paths listed under
   **Required tracked files** and no others.
3. `ARCHITECTURE.md` is byte-identical to the pre-positioned Revision 2.1 and
   has the required SHA-256.
4. The root `AGENTS.md` is unmistakably coding-agent-specific and accurately
   states the versioned OAP transcript/`SELF` policy.
5. The coding communication protocol is version 1.2, preserves all earlier
   control and safety invariants, and consistently specifies versioned orders,
   active pointer, and reports.
6. `oap/README.md` accurately describes ownership, selection, immutability,
   Git submission, FIFO separation, and `SELF` verification.
7. `oap/active` contains only logical identifier `000-a`, and exactly one
   `000-a-*` order and one `000-a-*` report exist.
8. The activated order and active pointer are present unchanged in the PR.
9. The report records the literal implementation head SHA and
   `Report publication commit: SELF`.
10. The remote PR head is the report-only commit; that commit changes only the
    new report file, and its first parent is the reported implementation head.
11. No secret, credential, token, unrelated file, product code, dependency,
    CI workflow, or extra PR is introduced.
12. The coding agent does not merge or enable auto-merge.

## Verification required

Run and report exact results for at least:

```bash
git diff --check origin/main...HEAD
sha256sum ARCHITECTURE.md
git diff --name-only origin/main...HEAD
git ls-files AGENTS.md ARCHITECTURE.md OAP-COMMUNICATION-coding-agent.md oap
test "$(tr -d '\n' < oap/active)" = "000-a"
test "$(find oap/orders -maxdepth 1 -type f -name '000-a-*.md' | wc -l)" -eq 1
test "$(find oap/reports -maxdepth 1 -type f -name '000-a-*.md' | wc -l)" -eq 1
rg -n '/codex-work/slaif-agent-site' AGENTS.md OAP-COMMUNICATION-coding-agent.md oap/README.md || true
```

The stale-path scan must find no bare legacy root in the coding constitution,
coding protocol, or OAP README; the authoritative repository root begins with
`/home/ubuntu`.

Also:

- parse all added Markdown with `pandoc --from gfm --to html` when available;
- inspect Markdown fence balance or report why the parser check is sufficient;
- inspect the final commit and its parent;
- inspect the PR with `gh pr view`, `gh pr diff`, and `gh pr checks`;
- report absent checks as absent, pending as pending, and failures as failures;
- confirm the final working tree has no uncommitted changes.

No application/runtime test suite exists yet. Do not invent one and do not
describe documentation validation as product testing.

## Documentation required

The documentation deliverable is the complete scoped PR itself:

- canonical `ARCHITECTURE.md`;
- coding-agent `AGENTS.md`;
- coding communication protocol version 1.2;
- concise `oap/README.md`;
- versioned order, active pointer, and report.

Do not update general product documentation in this objective.

## Safety / security constraints

- Never include capability tokens, credentials, cookies, database URLs,
  private keys, environment files, or unrelated host data.
- Do not access production systems or production data.
- Do not alter repository settings, branch protection, rulesets, secrets,
  collaborators, releases, or deployments.
- Preserve all user/strategic pre-positioned files and unrelated work.
- Do not weaken the architecture or OAP authority boundaries.
- Do not merge or enable auto-merge.

## Local execution capability

- Routine local setup is the coding agent's responsibility.
- Passwordless `sudo` is available in the disposable execution VM.
- Install a Markdown validator locally if needed; do not transfer ordinary
  setup or command execution to the human or strategic model.

## GitHub workflow

- Reconcile GitHub before editing.
- Start the required fresh branch from `origin/main`.
- Stage only explicit paths with `git add -- <paths>`.
- Push all intended commits before reporting.
- Create exactly one new non-draft PR before reporting.
- The final report-only commit must be pushed before signaling.
- Never merge, close, replace, or enable auto-merge on the PR.
- Do not create an extra PR for objective `000`.

## Required report

Atomically publish exactly:

```text
oap/reports/000-a-bootstrap-governance-and-versioned-oap-transcript.md
```

Use the full protocol report structure, adapted to include:

- Identifier and exact work-order file.
- Status: `COMPLETE`, `PARTIAL`, `BLOCKED`, or `FAILED`.
- PR mode: `CREATED_NEW_PR`.
- Repository, PR number/URL/state, base/head branch, and starting remote SHA.
- `Implementation head SHA: <literal 40-hex SHA>`.
- `Report publication commit: SELF`.
- Commits pushed before the report commit.
- Exact file/change summary.
- Evidence for every acceptance criterion.
- Exact local verification commands and outcomes.
- GitHub check state actually observed, with pending/missing distinguished.
- Local setup performed.
- Documentation impact.
- Safety/scope confirmations.
- Known limitations/blockers.
- Explicit confirmations that exactly one PR was created, no merge was
  performed, and the report-publication commit changes only the report file.

The report must explain that `SELF` is verified from GitHub rather than
embedding its impossible self-hash. Publish it atomically, commit it without
editing any earlier OAP artifact, push it, verify the remote head/parent/tree,
and then send exactly two ASCII bytes `OK` to `response.fifo` with no newline.
