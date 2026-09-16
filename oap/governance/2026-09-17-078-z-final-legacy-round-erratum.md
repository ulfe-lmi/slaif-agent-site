# OAP Governance Record — 2026-09-17 — One-off Human-Authorized Erratum for Final Legacy Round 078-z

## Status and classification

- One-off, human-authorized erratum record. This document is not a general
  governance amendment and not an OAP work order. It creates no new
  identifier, no new order, and no new report.
- This document is strategic-owned: the coding agent commits these exact
  bytes unchanged as part of the erratum commit and must not edit them.
- This is the first instance of the final-legacy-round erratum mechanism. The
  prospective rule is codified by the erratum commit itself (appended to
  `oap/governance/2026-09-14-increment-qualified-round-ids.md`).

## Authority and trigger

- On 2026-09-17 strategy independently rejected the 078-z completion claim
  with a finite checklist (R-1 three false 078/4 merge dates; R-2
  qualified-ID branch/PR topology not normative in executor-facing docs; R-3
  no legal rejection-continuation after the final legacy round). Green CI
  (20/20 on head `48105bd409e1c51393ec2af19284ac445bc675f1`) does not cure
  false current-truth facts or a protocol gap.
- Governance gap: `078-z` is the final legacy-format round of Objective 078.
  The legacy `a..z` sequence is exhausted, the 2026-09-14 amendment provides
  no letter continuation after a rejected final-legacy-round completion
  claim, and `078-5-a` is explicitly reserved for the first product
  increment after the 078-z merge. The protocol therefore required
  escalation to the human.
- The human owner authorized this one-off bounded erratum on 2026-09-17 in a
  continuation directive following the strategic rejection report. This
  document records that authorization.

## Why this is the only legal path (recorded)

- Re-activating 078-z is impossible: the order and report are immutable and
  one report per identifier is enforced by the repository policy gate.
- A further legacy letter is impossible: `a..z` is exhausted and the
  protocol prohibits inventing wider suffixes.
- `078-5-a` is not available: it is reserved for the next product
  increment and bound to the 078-z transition being accepted and merged.
- The human-authorized one-off erratum on the existing PR #82 is therefore
  the minimal legal repair, with the protocol exception recorded here and in
  the strategic acceptance record.

## Turn contract (sole scope authority for the next coding turn)

Preconditions — verify all; if any fails, follow the Blocked path:

1. PR #82 is open, base `main`, branch
   `oap/078-z-id-namespace-and-truth-transition`.
2. Remote PR head is exactly `48105bd409e1c51393ec2af19284ac445bc675f1`
   (the immutable 078-z report commit).
3. Remote `main` is exactly `26cafc1c0c91de5eee8406e8d477c50ea0208058`.
4. Local checkout is on that branch at that head with a clean tree.

Turn mechanics:

- No new identifier, no new order file, no new report. Do not create any
  `oap/reports/078-z-*` file: a second report is protocol-prohibited and is
  rejected by the repository policy gate.
- `oap/active` remains exactly `078-z` (byte-identical, no change).
- `oap/orders/078-z-oap-id-namespace-and-truth-transition.md` remains
  byte-identical: sha256
  `125198d721432adfb247cddc6cb8d44c8438a81d4e3a181574276d45a5cf8ad3`.
- `oap/reports/078-z-oap-id-namespace-and-truth-transition.md` remains
  byte-identical: sha256
  `33a53480a4b30ffa7bfd1dddb0e9190e3d42909d9b1ded328dc575b63d0f5714`.
- Exactly one erratum commit on top of `48105bd409e1c51393ec2af19284ac445bc675f1`;
  its first parent must be that SHA. This is the explicitly recorded
  exception to the report-only-head pattern; the 078-z report remains the
  sole immutable report for this round.
- This erratum document is committed as part of that single commit,
  byte-identical.
- Commit message starts with `078-z erratum:`.
- Push to the same branch; PR #82 head updates to the erratum commit.
  Verify remote head, first parent, and changed paths before signaling.
- No merge, no close, no PR title/body/label change, no Dependabot
  interaction, no other PR.

## Bounded scope — do exactly this

### (a) Current-truth merge dates (three corrections, nothing else)

- `README.md`: "The increment was accepted and merged at
  `26cafc1c0c91de5eee8406e8d477c50ea0208058` on 2026-09-14." — change
  `2026-09-14` to `2026-09-10` (GitHub `mergedAt` for PR #81 is
  2026-09-10T20:53:04Z).
- `README.md` summary-table row "Objective-078/4 page-style data plane
  (merged)": "accepted and merged in PR #81 on 2026-09-14 at" — change
  `2026-09-14` to `2026-09-10`.
- `oap/INCREMENTS.md` table row 078/4: "at
  `26cafc1c0c91de5eee8406e8d477c50ea0208058` on 2026-09-14" — change
  `2026-09-14` to `2026-09-10`.
- After these three corrections, the only remaining `2026-09-14` mentions in
  `README.md`, `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`, and
  `oap/MVP-CONTRACT-AUDIT.md` must be legitimate non-merge uses (references
  to the 2026-09-14 ID-namespace amendment; the 2026-09-14 audit/reconcilia-
  tion date in `oap/MVP-CONTRACT-AUDIT.md`). Verify by grep.

### (b) Qualified-ID branch/PR topology in executor-facing docs (four files)

Files: root `AGENTS.md`, root `OAP-COMMUNICATION-coding-agent.md`,
`oap/strategic-instructions/AGENTS-coding-agent.md`, and
`oap/strategic-instructions/OAP-COMMUNICATION-coding-agent.md`.

Required final semantics, stated explicitly and consistently in each of the
four files:

- Both ID forms remain valid (legacy `NNN-L`, qualified `NNN-I-L`) per the
  2026-09-14 ID-namespace amendment.
- Legacy: `NNN-a` creates one fresh branch and one new PR for objective
  `NNN`; `NNN-b..z` amend that same branch/PR.
- Qualified: the first round of an increment-qualified namespace, `NNN-I-a`,
  creates one fresh branch and exactly one new PR for that semantic
  increment from verified remote main (or the order-named base); later
  rounds `NNN-I-b..z` amend that same branch/PR.
- One bounded semantic increment equals one PR. A new PR for a new increment
  of the same numeric objective uses the new increment ID and does not
  require a new numeric objective.
- Coding never invents or chooses an ID or a continuation-vs-next
  transition; escalate on exhaustion; no `aa`.

Required removal: every occurrence of the sentence "Only a new numeric
`NNN+1-a` creates another PR" (present in root
`OAP-COMMUNICATION-coding-agent.md` and its `oap/strategic-instructions/`
mirror) must be removed or replaced so that no file asserts that only a new
numeric objective can create another PR.

Make no other change in these four files.

### (c) Prospective final-legacy-round rejection clause

Append one clearly labeled section to
`oap/governance/2026-09-14-increment-qualified-round-ids.md` (for example
"## Final-legacy-round rejection (prospective, effective 2026-09-17)")
stating at minimum:

1. If strategy rejects the completion claim of a final legacy-format
   transition round (such as `078-z`) and the objective's legacy round
   letter sequence is exhausted, no letter continuation exists under this
   amendment and the protocol requires escalation to the human.
2. The only legal repair is a human-authorized one-off bounded erratum on
   that round's existing PR: documentation/protocol/tooling-only changes;
   one erratum commit on top of the existing report-only head (explicitly
   recorded exception to the report-only-head pattern); no new identifier,
   no new order, no new report; `oap/active` unchanged; the erratum recorded
   as a governance record under `oap/governance/` and cross-referenced from
   this amendment and from the strategic acceptance record.
3. This clause does not amend the ID grammar, does not permit wider
   suffixes, and does not permit using `078-5-a` before the 078-z merge.
4. The 2026-09-17 078-z erratum
   (`oap/governance/2026-09-17-078-z-final-legacy-round-erratum.md`) is the
   first instance.

### (d) CRITICAL.md historical labeling

- Insert a short header block (two to five lines) directly under the title
  stating: this queue is a historical record of PRs #28 through #54
  (objectives 015 through 041, August 2026), preserved as immutable
  evidence; it is not a live queue; entries superseded by later merged work
  are annotated; GitHub and `oap/MVP-CONTRACT-AUDIT.md` are authoritative
  for current state.
- Annotate, by appending to the existing cell text without rewriting the
  row, at minimum:
  - The #36 row: superseded — capability authentication is no longer a
    placeholder; real `sas2_` capability authentication is implemented
    (`agent_state/capability_auth.py`; SECURITY DEFINER control-schema
    lookup).
  - The #45 row: partially addressed — path/method allowlists exist; real
    MCP protocol parity remains unproven (Objective 080 scope).
  - The #54 row: superseded — "MVP declared complete" contradicts the
    contract audit; the contractual MVP is not complete (see
    `oap/MVP-CONTRACT-AUDIT.md`).
- Do not edit any other row or prose in `CRITICAL.md`.

### (e) Merge-fact ledger consistency machine check

- `oap/INCREMENTS.md`: add one table row recording the 077 cross-reference
  merge fact (PR #74 merged
  `ae3a4a681bb888260192b7bb1b2a337b4906828d` on 2026-09-08) in the existing
  table format, and state in the introduction that the table is the
  authoritative ledger of verified merge facts referenced from
  current-state documents.
- `tools/check_repository.py`: add a repository-policy check that:
  1. Parses the `oap/INCREMENTS.md` table for (40-hex SHA, `on YYYY-MM-DD`)
     merge-fact pairs forming the ledger set.
  2. Scans `README.md`, `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`, and
     `oap/MVP-CONTRACT-AUDIT.md` by paragraph (blank-line separated). For
     each paragraph containing the word `merged` (case-insensitive) with
     exactly one distinct 40-hex SHA and at least one `YYYY-MM-DD` date,
     take the date closest in characters to the SHA; if that distance is
     120 characters or fewer, require the (SHA, date) pair to be in the
     ledger set, else report a policy error.
  3. Skips (does not flag) paragraphs containing two or more distinct 40-hex
     SHAs, where pairing is ambiguous (for example the
     `oap/MVP-CONTRACT-AUDIT.md` audited-source-revision line).
- `tests/repository/test_repository_policy.py`: following the existing
  fixture pattern, add at minimum:
  - a pass case: current-shape documents plus ledger produce no merge-fact
    errors;
  - a fail case: a document asserting a ledgered SHA with a wrong date
    (`26cafc1c0c91de5eee8406e8d477c50ea0208058` on 2026-09-14 while the
    ledger row says 2026-09-10) produces an error;
  - a fail case: an unknown 40-hex SHA with a date inside a `merged`
    paragraph produces an error;
  - a pass case: a paragraph with two 40-hex SHAs and one date produces no
    error (skip rule).
- Existing dual-grammar OAP behavior is unchanged; no other repository
  policy behavior changes.

### (f) Non-goals (strict)

- No product code, migration, dependency/lockfile, workflow, ruleset, or
  compose changes.
- No PR merge/close/label; no Dependabot interaction; no other PR.
- No new OAP identifier, order, or report; no `oap/active` change.
- No edit of the 078-z order, the 078-z report, or this erratum document.

## Verification (local, focused)

- `python tools/check_repository.py` — PASS repository policy.
- `python -m unittest discover -s tests/repository -p 'test_*.py'` — all
  pass, including the new merge-fact tests.
- `uv run --frozen ruff check tools/check_repository.py
  tests/repository/test_repository_policy.py` — clean.
- `python -m compileall -q tools tests/repository` — clean.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` — zero issues.
- Grep evidence: `grep -rn "Only a new numeric" AGENTS.md
  OAP-COMMUNICATION-coding-agent.md oap/strategic-instructions/` returns
  zero matches; `grep -n "2026-09-14" README.md oap/INCREMENTS.md
  oap/MVP-PROGRESS.md oap/MVP-CONTRACT-AUDIT.md` returns only legitimate
  non-merge uses; `sha256sum` of the order file and report file matches the
  pinned digests above.
- Do not run product suites (no product changes). The required remote CI
  (all 20 ruleset checks) must be green on the pushed erratum head.

## Blocked path

If any precondition fails or any in-scope item is ambiguous or blocked: do
not commit, do not push, do not signal OK. Write the exact observed state
(remote head, remote main SHA, the blocker) to
`oap/erratum/078-z-blocked-<UTC-timestamp>.md` (do not commit that file) and
stop. Strategy detects the missing response and investigates.

## Wire contract

After the erratum commit is pushed and the remote head, first parent, and
changed paths are verified: write exactly `OK` (ASCII bytes `4f 4b`, no
newline) to `response.fifo` and return to blocking on `control.fifo`.

## Post-merge

After strategy acceptance and merge: `oap/active` remains `078-z` until the
next activation. `078-5-a` activates only from a fresh strategic order on
verified post-merge main.
