# OAP Work Order — 000-b

## Objective

Amend the existing objective `000` pull request to correct one factual error
in the durable evidence trail and remove two ambiguities in the newly
versioned OAP transcript policy. Preserve the immutable `000-a` order and
report; record the correction in the new `000-b` report.

## GitHub objective state

- Numeric objective: `000`
- Execution round: `000-b`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#1`
- Existing PR URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/1`
- Required head branch: `oap/000-bootstrap-governance`
- Base branch: `main`
- Verified remote PR head before `000-b`:
  `0631b4de5bb290e0d0e3c82e71905fe5bde8858a`
- Verified `000-a` implementation head:
  `f0b460f5126c1bc52d95f98fea4fb5fd54aa8c23`
- Verified PR state: `OPEN`, non-draft, `MERGEABLE`, merge state `CLEAN`
- Verified checks: none configured or reported

## Strategic context

The strategic review independently verified the `000-a` PR identity,
seven-path scope, architecture hash, report-only `SELF` commit, first-parent
relationship, Markdown parsing, focused secret scan, and absence of a second
PR. The implementation is structurally sound.

However, the immutable `000-a` report contains a factual counting error:

```text
claimed: exactly eleven trailing-whitespace warnings
actual:  exactly ten trailing-whitespace warnings
source:  ARCHITECTURE.md lines 4 through 13 inclusive
```

The warnings are the canonical architecture's intentional Markdown hard
breaks. They must remain because `ARCHITECTURE.md` is byte-immutable in this
objective. The defect is the report's count, not the architecture.

Two wording ambiguities also need correction before the governance foundation
is merged:

1. `AGENTS.md` requests “starting and final remote SHAs” even though the
   committed-report convention deliberately replaces the impossible literal
   final self-SHA with a literal implementation head plus
   `Report publication commit: SELF`.
2. `oap/README.md` says reviewers verify a `SELF` commit “is the PR head”
   without limiting that condition to the time that round sends `OK`. A later
   continuation necessarily moves the PR head while preserving the earlier
   report commit in history.

The current PR body also says the coding agent “will append” the `000-a`
report even though it has already been appended. Replace that temporal wording
with stable, round-independent wording before publishing the `000-b` report.

## Current verified state

The strategic model verified:

- Remote default branch `main` remains
  `8a9d32ac11d6b1d75c87f016a73d732cd082b9c7`.
- PR `#1` is the only PR in the repository.
- PR `#1` has exactly three commits before `000-b`:
  - `d3e3a69406691145e5afd5d3ae76a09aaf3737f8`
  - `f0b460f5126c1bc52d95f98fea4fb5fd54aa8c23`
  - `0631b4de5bb290e0d0e3c82e71905fe5bde8858a`
- `0631b4de...` changes only the `000-a` report and has
  `f0b460f5...` as its first parent.
- `ARCHITECTURE.md` SHA-256 remains
  `a6e05a2aa67dcb43d7a4c94ada7037b33a4d1f0202f5f919cc780b2900e390a0`.
- Immutable `000-a` order SHA-256 is
  `ee63bf4b45f3b5205cb50a843ec4409823fdd0cd1a1a0e476dcf795b303a3f64`.
- Immutable `000-a` report SHA-256 is
  `35bb5610c8e3a353cc5efc198f89f7a991734d2970e5d6894c2022722fda4cef`.
- Independent `git diff --check origin/main...0631b4de...` exits `2`
  and emits exactly ten warnings, all at `ARCHITECTURE.md:4` through
  `ARCHITECTURE.md:13`.
- No branch protection, ruleset, workflow, or required check currently exists.

## Scope

1. Fetch and verify the named PR remains open with the expected branch/head.
2. Use the same branch and same PR; do not create another.
3. Commit this activated `000-b` order and updated `oap/active` unchanged.
4. Make only these governance corrections:
   - clarify the report identity fields in `AGENTS.md`;
   - clarify historical continuation behavior in
     `OAP-COMMUNICATION-coding-agent.md` and `oap/README.md`;
   - update PR `#1` body to stable, non-future wording.
5. Push the correction implementation and record its literal implementation
   head SHA.
6. Atomically publish a new `000-b` report that explicitly corrects the
   `000-a` warning count without modifying the earlier report.
7. Commit only the `000-b` report in the final `SELF` commit, push it, verify
   the remote PR head/parent/tree, and send exact FIFO `OK`.

## Required final tracked paths

The final PR diff against `main` must contain exactly these nine paths:

```text
AGENTS.md
ARCHITECTURE.md
OAP-COMMUNICATION-coding-agent.md
oap/README.md
oap/active
oap/orders/000-a-bootstrap-governance-and-versioned-oap-transcript.md
oap/orders/000-b-correct-bootstrap-evidence-and-transcript-wording.md
oap/reports/000-a-bootstrap-governance-and-versioned-oap-transcript.md
oap/reports/000-b-correct-bootstrap-evidence-and-transcript-wording.md
```

This nine-path list supersedes the seven-path final-diff criterion from
`000-a` because an append-only continuation necessarily adds one order and one
report while updating the existing active pointer.

## Non-goals

- Do not edit `ARCHITECTURE.md`.
- Do not edit, replace, delete, rename, or amend the `000-a` order or report.
- Do not change the meaning of any product architecture rule.
- Do not add product code, application tests, dependencies, CI, lockfiles,
  Compose, containers, or deployment files.
- Do not change `README.md`, `LICENSE`, or `.gitignore`.
- Do not add a new OAP mechanism beyond the narrow clarification requested.
- Do not create another branch, PR, issue, release, or tag.
- Do not merge or enable auto-merge.

## Requirements

### 1. Correct `AGENTS.md` report identity wording

In the minimum required-report list, remove the ambiguous request for both
“starting and final remote SHAs.” Require instead:

```text
starting remote SHA
literal implementation head SHA
Report publication commit: SELF
commits pushed
```

Keep the existing no-merge and remote-verification rules intact.

### 2. Clarify current versus historical `SELF` commits

In the coding protocol and `oap/README.md`, state unambiguously:

- when a round sends FIFO `OK`, its `SELF` report commit must be the current
  remote PR head;
- the next activated continuation adds commits to the same PR, so the earlier
  report commit will no longer be the current PR head;
- earlier `SELF` commits remain immutable and reachable in PR/Git history;
- historical verification checks the containing report commit and its first
  parent, not whether that old commit is still the latest PR head.

Do not change protocol version `1.2`; this is a clarification and evidence
repair within its first bootstrap PR.

### 3. Stabilize the PR body

Update PR `#1` body before report publication. It must no longer say a report
“will” be appended. Use stable wording that says the PR contains the canonical
architecture, coding governance, protocol 1.2, and an append-only versioned OAP
transcript, and that the coding agent never merges or enables auto-merge.

Do not include a literal latest head SHA in the body.

### 4. Preserve and submit strategic artifacts

- Commit the pre-published `000-b` order without editing its bytes.
- Commit `oap/active` with logical value `000-b` only; one LF is permitted.
- Preserve the verified hashes of the `000-a` order/report and architecture.

### 5. Correct the evidence trail append-only

The `000-b` report must explicitly state:

- the `000-a` report's “eleven warnings” statement was incorrect;
- independent and repeated execution shows exactly ten warnings;
- every warning is an intentional two-space Markdown hard break in the
  byte-immutable architecture at lines 4–13;
- no warning comes from another file;
- the earlier immutable report was not edited;
- the architecture was not edited;
- this `000-b` report is the durable correction.

Do not describe `git diff --check` as passing. Its expected result remains
exit `2`, with exactly ten understood architecture warnings.

### 6. Git and report sequence

1. Fetch and verify PR `#1` and its current head.
2. Stay on/update `oap/000-bootstrap-governance` safely.
3. Make the three scoped governance/PR-body corrections.
4. Stage only `AGENTS.md`, `OAP-COMMUNICATION-coding-agent.md`,
   `oap/README.md`, `oap/active`, and this `000-b` order.
5. Commit, push, and record the literal correction implementation head SHA.
6. Verify the same PR updated and no second PR exists.
7. Atomically publish the exact `000-b` report path.
8. Commit only that report as the final round commit.
9. Push and verify that commit is the remote PR head at response time, its
   first parent is the recorded implementation head, and its delta contains
   only the `000-b` report.
10. Do not mutate or push afterward; send exact FIFO `OK`.

## Acceptance criteria

1. PR `#1` remains the only objective PR, open, non-draft, based on `main`,
   and headed by `oap/000-bootstrap-governance`.
2. No second branch or PR is created.
3. The final PR diff contains exactly the nine required paths and no others.
4. `ARCHITECTURE.md`, the `000-a` order, and the `000-a` report retain their
   verified SHA-256 hashes.
5. `oap/active` contains logical value `000-b` only.
6. Exactly one order/report exists for `000-a`, and exactly one exists for
   `000-b`.
7. `AGENTS.md` no longer requests an impossible literal final self-SHA.
8. The coding protocol and OAP README correctly distinguish the current
   report-head requirement from later historical verification.
9. PR `#1` body uses stable present-tense wording and contains no stale
   “will append” promise.
10. The `000-b` report accurately and explicitly corrects ten versus eleven
    warnings and preserves the prior transcript.
11. The final remote PR head at response time is the `000-b` report-only
    `SELF` commit; its first parent is the recorded literal implementation
    head and its delta contains only the `000-b` report.
12. No secret, unrelated file, merge, or auto-merge is introduced.

## Verification required

Run and report exact outcomes for:

```bash
git diff --check origin/main...HEAD
sha256sum ARCHITECTURE.md \
  oap/orders/000-a-bootstrap-governance-and-versioned-oap-transcript.md \
  oap/reports/000-a-bootstrap-governance-and-versioned-oap-transcript.md
git diff --name-only origin/main...HEAD
git ls-files AGENTS.md ARCHITECTURE.md OAP-COMMUNICATION-coding-agent.md oap
test "$(tr -d '\n' < oap/active)" = "000-b"
test "$(find oap/orders -maxdepth 1 -type f -name '000-a-*.md' | wc -l)" -eq 1
test "$(find oap/reports -maxdepth 1 -type f -name '000-a-*.md' | wc -l)" -eq 1
test "$(find oap/orders -maxdepth 1 -type f -name '000-b-*.md' | wc -l)" -eq 1
test "$(find oap/reports -maxdepth 1 -type f -name '000-b-*.md' | wc -l)" -eq 1
```

For `git diff --check`, record the exit code, output, and a mechanically
derived warning count. Verify exactly ten warnings and verify every diagnostic
path is `ARCHITECTURE.md`. A nonzero exit is expected and must not be hidden.

Also:

- parse all scoped Markdown with `pandoc --from gfm --to html`;
- verify fence balance;
- run the focused stale-root and secret scans from `000-a`;
- inspect the same PR with `gh pr view`, `gh pr diff`, and `gh pr checks`;
- verify PR body, PR uniqueness, final report commit parent, and report-only
  delta;
- report no configured checks as absent, not successful;
- confirm a clean, synchronized working tree after the report push.

No application/runtime suite exists. Do not invent one or call documentation
validation product testing.

## Documentation required

The scoped governance clarifications and append-only correction report are the
documentation changes. Do not change general product documentation.

## Safety / security constraints

- Never include secrets, credentials, tokens, cookies, database URLs, private
  keys, or unrelated host data.
- Do not access production systems or data.
- Do not alter repository settings, protections, rulesets, secrets,
  collaborators, releases, tags, or deployments.
- Preserve all immutable transcript artifacts and unrelated work.
- Do not merge or enable auto-merge.

## Local execution capability

- Routine local setup is the coding agent's responsibility.
- Passwordless `sudo` remains available in the disposable VM.
- Do not transfer ordinary validation or GitHub inspection to the human or
  strategic model.

## GitHub workflow

- Amend PR `#1` and its existing branch only.
- Stage explicit paths only; never use broad `git add` forms.
- Push all correction implementation commits before composing the report.
- Update the PR body before report publication.
- Push the final report-only commit before signaling.
- Never create another PR, merge, close, replace, or enable auto-merge.

## Required report

Atomically publish exactly:

```text
oap/reports/000-b-correct-bootstrap-evidence-and-transcript-wording.md
```

Use the full protocol 1.2 report structure. In addition to normal identity,
scope, evidence, test/check, setup, documentation, and safety fields, include:

- `PR mode: AMENDED_EXISTING_PR`;
- PR `#1` URL and existing branch;
- starting head `0631b4de5bb290e0d0e3c82e71905fe5bde8858a`;
- literal correction implementation head SHA;
- `Report publication commit: SELF`;
- explicit ten-versus-eleven correction;
- hashes proving the earlier order/report and architecture stayed unchanged;
- evidence that the final nine-path scope is exact;
- evidence that the PR body is stable;
- exact absent/pending GitHub check state;
- confirmation that no new PR, merge, or auto-merge occurred;
- confirmation that the final commit changes only the `000-b` report.

Publish and commit the report without modifying earlier transcript artifacts,
push it, verify the remote head/first-parent/report-only delta, then send
exactly two ASCII bytes `OK` to `response.fifo` with no newline.
