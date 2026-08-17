# OAP Work Order — 001-b

## Objective

Amend the existing objective `001` pull request after the human-authorized
Dependency Graph enablement. Verify that Dependency Review now succeeds,
clarify the private email fallback in `SECURITY.md`, preserve the immutable
`001-a` evidence, and complete the same PR only when all final-head CI and
CodeQL checks are successful.

## GitHub objective state

- Numeric objective: `001`
- Execution round: `001-b`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#2`
- Existing PR URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/2`
- Required head branch: `oap/001-readme-ci-codeql`
- Base branch: `main`
- Verified starting PR head:
  `d26712aa59f01afff3096b5852d0348bdf4ab83f`
- Verified `001-a` implementation head:
  `4a6f600ca9103fb7bc4c63fab184d83a562e5f9d`
- Verified PR state before activation: open, non-draft, mergeable, no
  auto-merge, merge state unstable only because Dependency Review failed

## Strategic context

The `001-a` report correctly returned `PARTIAL`. Independent strategic review
verified the exact seventeen-path scope, report-only `SELF` history, README,
logo digest/provenance, documentation, policy checker and fourteen tests,
workflow hardening, SHA pins, CodeQL `actions`/`python` analysis, and zero open
CodeQL alerts.

The only failing final-head check was the official Dependency Review action:

```text
Dependency review is not supported on this repository.
Please ensure that Dependency graph is enabled.
```

The human then explicitly authorized enabling Dependency Graph. The strategic
model used GitHub's repository vulnerability-alerts endpoint, which enables
the Dependency Graph and vulnerability alerts together. Independent
post-change verification shows:

- the vulnerability-alerts endpoint succeeds;
- the Dependency Graph SBOM endpoint returns an SPDX 2.3 document;
- Dependabot automatic security-update PRs remain disabled;
- secret scanning and push protection remain disabled;
- no repository source file or PR commit was changed by that setting action.

GitHub settings are authoritative for this external change. The coding agent
must verify the current state but must not broaden or alter it.

Strategic document review also found one narrow wording problem in the new
`SECURITY.md`: it says the fallback email is only for material already public.
That makes the fallback unsuitable for a private vulnerability report. The
fallback should instead accept only a minimal, non-sensitive notification and
arrange a safer channel for any sensitive detail.

## Current verified state

- Remote `main` remains:
  `3e54c65a798ab5c2df6f2498f2197a19cb60520b`
- PR `#2` is the only objective `001` PR.
- Current PR head `d26712aa...` is the `001-a` report-only commit and has
  `4a6f600c...` as first parent.
- `001-a` order SHA-256:
  `c2dfe932b2bf8d448436226aa122e2ececdd88e1372bfc91a9adb9c211863b27`
- `001-a` report SHA-256:
  `736ab4d95d41ff41cba41543f794461da4335ae4c70e1c0d73f656c271a15a82`
- Pre-correction `SECURITY.md` SHA-256:
  `211e06c306a06b7d3c53262478f774c41aea325fb17bab78df04eebb3734e6ca`
- Final-head `001-a` checks:
  - Repository policy: success
  - Markdown: success
  - Detect supported languages: success
  - Analyze actions: success
  - Analyze python: success
  - aggregate CodeQL: success
  - Dependency review: failure due only to the then-disabled graph
- Application/runtime code and tests remain absent by design.

## Required final tracked paths

The final PR diff against `main` must contain exactly these nineteen paths:

```text
.github/dependabot.yml
.github/pull_request_template.md
.github/workflows/ci.yml
.github/workflows/codeql.yml
.markdownlint-cli2.yaml
AGENTS.md
CONTRIBUTING.md
NOTICE
README.md
SECURITY.md
docs/assets/README.md
docs/assets/slaif-logo.svg
oap/active
oap/orders/001-a-professional-readme-ci-and-codeql.md
oap/orders/001-b-verify-dependency-review-and-security-reporting.md
oap/reports/001-a-professional-readme-ci-and-codeql.md
oap/reports/001-b-verify-dependency-review-and-security-reporting.md
tests/repository/test_repository_policy.py
tools/check_repository.py
```

This list supersedes `001-a`'s seventeen-path final scope because the
append-only continuation adds one order and one report while updating the
existing active pointer and `SECURITY.md`.

## Scope

1. Verify the authorized Dependency Graph is available and the existing PR,
   branch, and head match this order.
2. Amend PR `#2` and its existing branch only.
3. Commit this strategic-authored `001-b` order and `oap/active` unchanged.
4. Make the narrow `SECURITY.md` fallback-email correction below.
5. Update the PR body to stable present-tense wording that records Dependency
   Graph availability and does not claim success before checks complete.
6. Run all local preparation validation.
7. Push the implementation commit and require the existing CI/CodeQL workflows
   to run, including Dependency Review.
8. Repair only in-scope failures on the same branch.
9. Atomically publish the `001-b` report in a final report-only `SELF` commit.
10. Wait for and inspect all checks on the report-containing head, then signal
    exact FIFO `OK` with truthful states.

## Non-goals

- Do not create another PR or branch.
- Do not edit `ARCHITECTURE.md`, the coding communication protocol, or any
  objective `000` artifact.
- Do not edit the immutable `001-a` order or report.
- Do not change README, logo, CI, CodeQL, Dependabot, policy checker, tests,
  contribution guide, notice, PR template, or Markdown configuration unless
  an actual final-head failure proves a narrowly necessary correction; if so,
  report the exact cause and keep within the original objective.
- Do not remove, skip, soften, or mark Dependency Review
  `continue-on-error`.
- Do not change GitHub security settings, enable automatic security-update
  PRs, enable secret scanning/push protection, or alter Actions/repository
  settings.
- Do not add application code, dependencies, manifests, lockfiles, Compose,
  containers, or product tests.
- Do not create an issue, release, tag, deployment, merge, or auto-merge.

## Requirements

### 1. Verify the authorized external setting

Before repository mutation, verify:

- GitHub's Dependency Graph SBOM endpoint succeeds for this repository;
- vulnerability alerts/dependency graph access is enabled;
- PR `#2` remains open with expected branch/head;
- no second objective `001` PR exists.

Do not submit a synthetic dependency snapshot and do not enable any additional
security feature.

### 2. Correct the security-reporting fallback

Keep private GitHub Security Advisories as the preferred reporting mechanism.
Replace the unusable “already public material” email wording with a clear
fallback such as:

> If the advisory form cannot be used, send a minimal notification to
> `janez.pers@fe.uni-lj.si` without exploit details, credentials, personal
> data, production data, or other sensitive material. Use that message only
> to arrange an appropriate channel for further details.

Retain:

- pre-alpha/no-supported-production-version honesty;
- no public disclosure before coordination;
- no promised response SLA;
- safe-research boundaries;
- no certification/penetration-test claim.

Do not invite sensitive vulnerability details over ordinary email.

### 3. Preserve append-only evidence

- Do not edit the `001-a` order/report; verify their hashes.
- Commit the new `001-b` order exactly as published.
- Commit `oap/active` with logical value `001-b` only.
- The new report must explain that `001-a` was partial because the Dependency
  Graph was unavailable, that the human authorized its enablement, and whether
  Dependency Review subsequently succeeded.

### 4. Final-head GitHub gate

The current workflows must run on both the `001-b` implementation commit and
the final report commit. On the final report-containing head, independently
observe and report every check. Acceptance requires success for at least:

```text
Repository policy
Markdown
Dependency review
Detect supported languages
Analyze (actions)
Analyze (python)
CodeQL
```

No required check may be failed, cancelled, missing, skipped, or pending at
strategic merge time. Do not substitute local checks for GitHub checks.

### 5. PR body

Before report publication, update PR `#2` body with stable wording that:

- retains the objective/scope/non-goals and validation summary;
- records that Dependency Graph and vulnerability alerts were enabled by an
  authorized strategic/human action;
- records that automatic security-update PRs, secret scanning, and push
  protection remain outside this objective;
- does not retain the stale disabled-graph blocker;
- does not embed a latest commit SHA or promise a future report.

### 6. Report publication

Atomically publish exactly:

```text
oap/reports/001-b-verify-dependency-review-and-security-reporting.md
```

Record the literal implementation head and
`Report publication commit: SELF`. The final commit changes only that report,
is pushed to the same PR, and is the remote PR head when FIFO `OK` is sent.

## Acceptance criteria

1. PR `#2` remains the unique objective `001` PR, open, non-draft, correct
   base/head, with no auto-merge.
2. No new branch/PR, issue, release, tag, merge, or setting change is made by
   the coding agent.
3. Dependency Graph/SBOM access succeeds and the official Dependency Review
   job succeeds on the final head.
4. Every listed CI/CodeQL check on the final head succeeds.
5. CodeQL continues to analyze `actions` and `python`; open CodeQL alerts are
   reported honestly.
6. `SECURITY.md` provides a usable minimal-notification email fallback without
   soliciting sensitive details or promising an SLA.
7. Final PR diff contains exactly the nineteen allowed paths.
8. Architecture, objective `000`, and immutable `001-a` artifacts are
   unchanged; `001-a` hashes match this order.
9. All local policy tests/checks/Markdown lint pass.
10. `oap/active` is `001-b`, with unique `001-a` and `001-b` orders/reports.
11. Final remote head is the `001-b` report-only `SELF` commit with the report's
    literal implementation head as first parent.
12. No secret, production access, hosted runtime dependency, product code,
    dependency, license drift, or architecture drift is introduced.

## Verification required

Run locally and report exact outcomes for:

```bash
python -m compileall -q tools tests/repository
python -m unittest discover -s tests/repository -p 'test_*.py'
python tools/check_repository.py
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
sha256sum docs/assets/slaif-logo.svg \
  oap/orders/001-a-professional-readme-ci-and-codeql.md \
  oap/reports/001-a-professional-readme-ci-and-codeql.md
git diff --check origin/main...HEAD
git diff --name-only origin/main...HEAD
```

Also verify:

- Dependency Graph SBOM availability;
- security-setting state without changing it;
- Markdown parse/fence balance;
- README links/logo and exact digest;
- workflow pins/contracts and zero prohibited constructs;
- exact nineteen-path scope;
- OAP active/correlation and immutable hashes;
- focused secret scan;
- PR uniqueness/body/base/head/draft/auto-merge;
- all final-head GitHub check names/conclusions;
- CodeQL alert state;
- report commit parent and report-only delta;
- clean synchronized worktree.

Application/runtime tests remain `NOT RUN — not present`, never passed.

## Documentation required

Only the narrow `SECURITY.md` correction, stable PR body, new immutable order,
and new immutable report are expected. Keep all current/planned/readiness
language mutually consistent.

## Safety / security constraints

- Never include real secrets, exploit payloads, credentials, tokens, cookies,
  database URLs, private keys, personal data, or production data.
- Do not access production systems or alter GitHub settings.
- Do not weaken workflow checks or permissions.
- Preserve architecture/OAP ownership and no-merge rules.
- Preserve unrelated work.

## Local execution capability

- Routine setup, validation, GitHub inspection, and CI-log diagnosis remain
  the coding agent's responsibility in its disposable VM.
- Passwordless `sudo` is available where safe.
- Do not transfer ordinary operations to the human/strategic model.

## GitHub workflow

1. Fetch and verify GitHub, Dependency Graph, PR `#2`, and current head.
2. Update the existing branch only.
3. Make the scoped security wording change and commit it with the unchanged
   strategic order/active pointer.
4. Push, update the same PR body, and inspect/fix implementation-head checks.
5. Record the literal implementation head and publish the report atomically.
6. Commit only the report, push, verify `SELF`, and inspect final-head checks.
7. Send exact FIFO `OK`; never merge, auto-merge, or create another PR.

## Required report

Use the full protocol 1.2 report structure. Include the external setting
history and authorization, exact SBOM/Dependency Review evidence, the security
wording change, preserved `001-a` hashes, exact nineteen-path scope, local
checks, every final-head GitHub check and CodeQL alert state, PR identity/body,
implementation/`SELF` relationship, setup, limitations, and all safety/no-new-
PR/no-merge confirmations.

Publish atomically, commit the report alone, push it, verify the remote
head/first-parent/report-only delta, then send exactly two ASCII bytes `OK` to
`response.fifo` with no newline.
