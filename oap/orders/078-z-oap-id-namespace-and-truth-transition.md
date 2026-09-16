# Coding Agent Work Order — 078-z: OAP ID-namespace transition and current-truth reconciliation

## Objective

Objective 078, round `078-z` — the reserved final legacy-format round of numeric
Objective 078. This is a control-plane governance transition only: record the
human-approved increment-qualified round-ID amendment, make the repository
validators, parsers, tests and protocol documentation accept both legacy
`NNN-L` and qualified `NNN-I-L` identifiers, correct every stale current-truth
surface against live GitHub, and codify the prospective review-unit governance
refinement. This round contains zero product functionality.

## GitHub objective state

- Objective: 078; round: 078-z; mode: `CREATE_NEW_PR`.
- Existing objective PR: N/A. PR #77 merged `3cae3d6cef2a92e7068856d21bc9a47b8190c22e`
  (078/1, 2026-09-09T10:46:52Z); PR #79 merged
  `a9d3e6800d5e8b5fd5c9cd9e0be5010184058c6b` (078/2, 2026-09-10T07:14:24Z);
  PR #80 merged `fe31c9f30a7797d0916ad7f8fb56344bc61526f3` (078/3,
  2026-09-10T11:26:36Z); PR #81 merged `26cafc1c0c91de5eee8406e8d477c50ea0208058`
  (078/4, 2026-09-10T20:53:04Z). All four are MERGED and closed.
- Required head: NEW branch from the verified base below. No new PR may be
  created for any other objective; no second 078 PR may exist.
- Base (verified remote main, strategy-verified 2026-09-14):
  `26cafc1c0c91de5eee8406e8d477c50ea0208058`.

## Strategic context and independently verified current state

Strategy verified against live GitHub on 2026-09-14:

- Remote `main` is exactly `26cafc1c0c91de5eee8406e8d477c50ea0208058`.
- No product OAP PR is open. Only unrelated Dependabot PRs #65, #75 and #78
  exist; they are explicitly excluded from this round.
- `oap/active` is `078-y`, the last activated round; nothing is in flight.
- The default-branch ruleset `protect` (id 20934043) is active with zero
  bypass actors, a pull-request requirement, blocked force-push/non-FF, and a
  strict required-status-checks policy covering Repository policy, Node
  contracts, Python 3.12/3.13/3.14 quality and package, Foundation PostgreSQL
  14 through 18, Compose and edge packaging, Supply-chain evidence, Markdown,
  Mermaid, Dependency review, Detect supported languages, Analyze
  (actions/python/javascript-typescript) and CodeQL. Classification:
  **VERIFIED FIXED — make no ruleset mutation in this round.**
- Numeric Objective 078 remains PARTIAL. 078/1 through 078/4 are accepted and
  merged. Remaining product scope (global-region/header-footer management and
  catalog breadth) is planned only after this transition merges, under the new
  increment-qualified IDs beginning at `078-5-a`.

On 2026-09-14 the human owner issued a directive authorizing the prospective
round-ID form `NNN-I-L` (numeric objective, semantic increment number,
lowercase round letter), reserving `078-z` as the final legacy-format
transition round and starting the next Objective-078 product increment at
`078-5-a`. Historical IDs remain immutable. Objectives whose first increment
already uses flat IDs (for example future `079-a`) keep that history; a later
second increment of such an objective uses `079-2-a`. No `aa`-style suffixes;
each increment-qualified namespace has its own `a..z` sequence; increment
numbers correspond to the semantic increment ledger and are never reused or
silently renumbered.

## Bounded scope

Do exactly the following, in this order.

### A. Record the ID-namespace amendment

1. Add `oap/governance/2026-09-14-increment-qualified-round-ids.md`: a
   prospective governance amendment recording the human authorization in full
   (both forms `NNN-L` and `NNN-I-L`; historical flat IDs immutable; 078/1
   through 078/4 are historical accepted increments; `078-z` is the reserved
   final legacy transition round; after its merge the next Objective-078
   product increment starts at `078-5-a`, then `078-6-a`, `078-7-a`, etc.;
   first-increment flat history such as `079-a` remains valid with second
   increments `079-2-a`; no `aa`; per-increment `a..z`; ledger-bound increment
   numbers; escalation on exhaustion; this directive is prospective and does
   not rewrite historical orders/reports).
2. Update `tools/check_repository.py` so the OAP grammar accepts BOTH forms.
   At minimum:
   - `oap/active` fullmatch accepts `NNN-L` or `NNN-I-L` plus optional final
     newline.
   - Order/report filename matching accepts both forms and groups by the full
     identifier (legacy `NNN-L` or qualified `NNN-I-L`), preserving: exactly
     one order per active identifier; report-count rules for active vs
     historical identifiers; the inert preplanned-exception (currently
     `074-a` through `091-a`, flat form) applied without change to legacy
     files; report-without-order rejection; duplicate-file rejection;
     temporary-artifact prohibition.
   - Qualified form is `NNN-I-L` where `I` is one or more decimal digits with
     no leading zero (`078-5-a` valid; `078-0-a` and `078-05-a` invalid) and
     `L` is exactly one lowercase letter.
   - Objective extraction yields the same objective for `078-y` and `078-5-a`
     (both 078); increment extraction is explicit for qualified IDs; the round
     letter is the final character.
   Do not change any other repository-policy behavior.
3. Extend `tests/repository/test_repository_policy.py` with positive and
   negative tests covering at least: legacy `078-y` accepted; legacy `078-z`
   accepted; qualified `078-5-a` accepted; qualified `078-5-z` accepted;
   `078-6-a` accepted; malformed IDs rejected (uppercase, `078-aa`, `78-a`,
   `078-5` without letter, `078-0-a`, `078-05-a`); duplicate
   increment/round identities rejected (two order files for the same
   qualified ID; duplicate reports); objective extraction remains 078 for
   qualified IDs; increment extraction explicit; historical flat IDs and the
   inert preplanned range remain accepted unchanged; legacy and qualified
   identifiers for the same objective coexist without cross-contamination.
4. Update ONLY the current protocol/tooling documentation needed to make the
   rule operational, in these files: root `AGENTS.md` (OAP section), root
   `OAP-COMMUNICATION-coding-agent.md` (ID section and report template),
   `oap/README.md` (directory contract), and the four mirrors under
   `oap/strategic-instructions/` (`AGENTS.md`, `AGENTS-coding-agent.md`,
   `OAP-COMMUNICATION-coding-agent.md`, `OAP-COMMUNICATION-strategic.md`).
   Each updated spot must state: both ID forms exist; qualified IDs appear
   only when a strategic order activates them; coding never invents or
   chooses IDs; `078-z` is the final legacy round of Objective 078; the next
   Objective-078 product increment is `078-5-a` and later increments are
   `078-6-a`, `078-7-a`, etc.; first-increment flat history of other
   objectives remains valid.

### B. Fix current repository truth now

Correct every stale current-state surface against the verified GitHub state
above. At minimum repair, with verified full SHAs:

- `README.md`: the 078/4 paragraph currently reads "It remains pending
  strategic acceptance/merge"; PR #77 is described as "open"; "the active
  078/4 page-style authority/evidence repair is on PR #81"; the summary-table
  row "strategic acceptance/merge remains separate". State the immutable
  facts: 078/1 merged `3cae3d6cef2a92e7068856d21bc9a47b8190c22e`, 078/2 merged
  `a9d3e6800d5e8b5fd5c9cd9e0be5010184058c6b`, 078/3 merged
  `fe31c9f30a7797d0916ad7f8fb56344bc61526f3`, 078/4 merged
  `26cafc1c0c91de5eee8406e8d477c50ea0208058`; no Objective-078 product PR is
  currently open; numeric 078 remains PARTIAL with global-region and catalog
  scope remaining.
- `oap/INCREMENTS.md`: the opening line "The active semantic increment is
  078/4"; the 078/4 table row "Active 078-y proof-closure continuation on
  PR #81"; the 078-y and 078-x section closings "PR #81 remains the sole open
  PR … until strategy … merges"; the Next row (add the ID-namespace
  amendment reference and that the next product increment starts at
  `078-5-a`).
- `oap/MVP-PROGRESS.md`: the opening paragraph, which currently assigns merge
  `fe31c9f30a7797d0916ad7f8fb56344bc61526f3` to PR #79 (that SHA is PR #80's
  merge; PR #79 merged at `a9d3e6800d5e8b5fd5c9cd9e0be5010184058c6b`);
  "The active 078-y continuation is a separate 078/4 … continuation";
  "Active 078-v implements only the bounded page-style slice"; the "Active
  and remaining sequence" section; and the 078 table row.
- `oap/MVP-CONTRACT-AUDIT.md`: the "Authoritative audited source revision"
  line (currently "Active Objective 078-y … on branch
  oap/078-4-page-style-overrides"); the contract-matrix 078 row ("Active
  078-y closes …"; "Independently review and accept/merge the bounded 078/4
  page-style increment"); the narrowest-statements 078 row ("078-y is the
  active bounded page-style proof closure"); and the "ACTIVE / REMAINING"
  block that still calls 078/2 "the separate active 078-q theme-boundary
  increment" (078/2, 078/3 and 078/4 are all merged).
- Audit every other current-state document for equivalent stale claims and
  repair any found; record the audit in the report.

Structural requirement: current-state documents committed in this PR must not
contain ephemeral wording that becomes false when the PR merges (no "this PR
is open", no "pending strategic merge", no "active increment means open PR").
Use durable wording: identify the increment/PR and source revision; state
that GitHub is authoritative for live acceptance/merge state; record immutable
merge facts only when already known; explicitly define `oap/active` as "the
last activated round until the next activation" (it is `078-z` after this PR
merges). After this PR merges, no current-truth surface on main may be false.
Historical orders, reports and audits are immutable: do not rewrite them.

### C. Codify stronger review-unit governance

1. Add `oap/governance/2026-09-14-review-unit-governance.md`: a prospective
   refinement (the 2026-09-09 bounded-semantic-PR amendment remains
   historical and is not rewritten) implementing:
   - Predeclared review budget: every CREATE_NEW_PR semantic increment
     declares before coding expected production/config file count, migration
     count, test/evidence footprint, generated-contract footprint, docs
     footprint, OAP transcript footprint, and expected substantive
     implementation-line scale. The existing 20-30 implementation-file /
     several-thousand-substantive-line threshold remains a review trigger,
     not a mechanical quota; gaming by moving code, excluding meaningful
     tests, or ignoring generated/OAP files is prohibited.
   - Cumulative review size: every strategic review of a continuation
     calculates base-to-current-head cumulative PR size, recorded separately
     for production/config, migrations, tests/evidence, generated artifacts,
     docs and OAP transcript.
   - CLOSURE_ONLY mode: entered when Strategy rejects a completion claim
     after substantive implementation, or when the cumulative review trigger
     is crossed. Once entered: no new semantic family, no adjacent feature,
     no opportunistic scope, no next-objective work; only finite
     defects/evidence that make already-added behavior safe, correct and
     reviewable. Separable functionality starts from verified merged main in
     another PR.
   - Finite rejection checklist: when Strategy rejects COMPLETE it publishes
     one finite list of unresolved criteria and the executable evidence
     required for each; a later report may claim COMPLETE only if every
     named criterion was actually executed; omitted required browser,
     PostgreSQL, migration, concurrency or public-boundary proof requires
     PARTIAL/BLOCKED, never COMPLETE.
   - Early split decision: semantically separable remaining work is split
     before being added to the current PR; tiny rounds do not justify a huge
     cumulative PR.
   - Final strategic acceptance: every acceptance record states verified
     base, accepted exact head, cumulative base-to-head diff, grouped size,
     whether review triggers fired, why the unit remains reviewable, whether
     and when CLOSURE_ONLY began, and explicit confirmation that no new
     semantic family entered after CLOSURE_ONLY.
2. Add short operational pointers in the current protocol documentation so
   both roles know the rules are in force prospectively: the strategic
   communication mirror and the coding-agent communication documents (root
   and mirror) must state that CLOSURE_ONLY and the finite rejection
   checklist bind from this amendment onward, and that a coding report may
   claim COMPLETE only when every named criterion of the latest published
   rejection list (or the order's acceptance criteria when none exists) was
   actually executed.

### D. GitHub ruleset

VERIFIED FIXED: read live from GitHub before work (already done by strategy;
re-verify read-only) and record the classification in the report. Make no
ruleset, branch-protection or workflow mutation.

## Explicit non-goals

- No product functionality of any kind: no global regions, header/footer
  product behavior, catalog component breadth, media, MCP, exact-workspace
  Puck, freeze/review/promotion, publication, source tools, or any other
  product feature or repair.
- No changes under `services/`, `apps/`, `packages/` (product),
  `migrations/`, `compose.yaml`, `infra/`, or any dependency manifest or lock
  file. No new dependencies.
- No historical order/report/audit rewrite. No ruleset or workflow change.
- No interaction with Dependabot PRs #65, #75, #78. No merge, auto-merge,
  close, or label of any PR. No activation of `078-5-a` or any other future
  round (that is a separate strategic act after this merge).

## Observable acceptance criteria

1. New governance amendment exists, is prospective, and states the complete
   ID rules including the `078-z` reservation and `078-5-a` transition.
2. `python tools/check_repository.py` passes on the final tree (active
   `078-z`, order present, historical artifacts intact, inert range intact).
3. The repository test suite for repository policy passes, including the new
   positive/negative dual-grammar tests named in section A.3.
4. The Markdown gate passes with zero issues across all Markdown files.
5. Every stale claim listed in section B is corrected with the exact full
   merge SHAs; a fresh scan for "078-y … open/active/increment",
   "pending strategic", "remains the sole open PR", and the `fe31c9f`/PR #79
   misattribution finds no surviving false current-state claim.
6. No current-state surface contains wording that becomes false at merge time.
7. The review-unit governance file exists with all six rules; protocol
   pointers present in the named documents.
8. Zero product-code, migration, dependency, workflow or ruleset changes in
   the PR diff (the diff touches only: `tools/check_repository.py`,
   `tests/repository/test_repository_policy.py`, the two new
   `oap/governance/` files, the protocol docs named in A.4/C.2,
   `README.md`, `oap/README.md`, `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`,
   `oap/MVP-CONTRACT-AUDIT.md`, plus `oap/orders/078-z-*.md`, `oap/active`
   and this report).
9. All required checks succeed on the final report-only head.

## Verification (local, focused; no product ceremony)

- `python tools/check_repository.py` — must print PASS repository policy.
- `python -m unittest discover -s tests/repository -p 'test_*.py'` — all pass.
- `uv run --frozen ruff check tools/check_repository.py
  tests/repository/test_repository_policy.py` — clean.
- `python -m compileall -q tools tests/repository` — clean.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` — zero issues.
- Do NOT run the Compose, browser, PostgreSQL matrix, or other product suites
  locally; no product code changed. The required remote CI matrix (including
  all 20 ruleset checks) runs on the pushed head and must be green.

## Documentation

The documentation updates in sections A.4 and C.2 are the documentation work
of this order. Keep wording durable per section B. No user-facing docs,
CHANGELOG, or release notes exist for governance transitions.

## Safety, security and data constraints

- No secrets, credentials, tokens, cookies, database URLs or private
  artifact URLs anywhere in the diff or report.
- No production systems, no package installs beyond the already-present
  frozen toolchain; routine local setup remains executor-owned.
- This round changes repository policy validation: after the change, the
  policy gate must still reject malformed active content and malformed
  artifact filenames (negative tests prove this).

## Local capability

The executor's disposable VM owns packages, services, test databases and
tools; passwordless sudo exists for routine setup. Do not transfer setup work
to the human or strategy.

## GitHub workflow

1. Fetch and reconcile remote; verify `origin/main` is exactly
   `26cafc1c0c91de5eee8406e8d477c50ea0208058`.
2. Create fresh branch `oap/078-z-id-namespace-and-truth-transition` from
   that base.
3. Implement sections A through D; run the focused verification; commit the
   intended work (implementation commit).
4. Push and create exactly one new PR (title:
   "OAP 078-z: ID-namespace transition and current-truth reconciliation
   (governance only)") against `main`. The PR body must identify 078-z, the
   transition purpose, the zero-product-change rule, and the no-merge rule.
5. Never merge, never create a second PR, never touch other PRs.
6. Inspect checks; repair only safe in-scope failures within the turn.
7. Commit the activated order and `oap/active` (exact strategic bytes,
   unmodified) with the implementation work; then atomically publish the
   report as the final report-only commit and push, so the remote PR head is
   the report commit whose first parent is the literal implementation head.

## Exact final-report contract

Publish exactly one report `oap/reports/078-z-oap-id-namespace-and-truth-transition.md`
stating:

- Identity: Objective 078; round 078-z; mode CREATE_NEW_PR; status;
  repository; PR number and URL; branch; verified base
  `26cafc1c0c91de5eee8406e8d477c50ea0208058`; literal implementation head
  SHA; `Report publication commit: SELF`.
- SHA-256 of the exact `oap/active` bytes (`078-z` plus final newline) and of
  the exact 078-z order file.
- The ID-interpretation audit: every location examined that interprets order
  IDs, report IDs, `oap/active`, artifact filenames, objective/increment
  numbers, round ordering, uniqueness or transitions, with the disposition of
  each (changed / already correct / not applicable), including the negative
  findings in workflows, compose tooling and backend code.
- Criterion-by-criterion evidence for acceptance criteria 1 through 9,
  honest pass/fail/skip/not-run labels.
- Exact local verification commands and exact results.
- Required remote checks observed on the implementation head (state each;
  pending is honest pending, not pass).
- Confirmed ruleset classification VERIFIED FIXED with no mutation.
- Governance confirmations: only the unique activated order executed; no
  historical artifact edited; no product change; no merge/accept/ID choice;
  no Dependabot interaction; Objective 078 remains PARTIAL; `078-5-a` not
  activated.
