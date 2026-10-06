# OAP Work Order — 083-2-b (Markdown gate repair at the 083-2-a
report head; 083/2 continuation)

> **STATUS: ACTIVATED — operative order.** Published atomically by
> strategy 2026-10-06 to
> `oap/orders/083-2-b-markdown-lint-repair.md` with `oap/active` =
> `083-2-b`, as a same-PR continuation of `083-2-a` (PR #101). The
> strategic review of the exact 083-2-a report head `ce81709`
> REJECTED the `COMPLETE` claim on exactly one material criterion:
> the required `Markdown` check failed at that head. This round
> closes the finite rejection checklist below and nothing else. The
> coding agent executes under the normal OAP execution contract;
> strategy remains reviewer/acceptor/merger.

## 1. Identifier and mode

- ID: `083-2-b` (increment-qualified round ID: second round of
  semantic increment 2 of numeric Objective 083; same PR as
  `083-2-a`).
- Mode: CONTINUATION (same branch, same PR). CREATE_NEW_PR: no.
- PR: #101 (`OAP 083-2-a: real discard (conflict remedy) (083/2)`),
  branch `oap/083-2-a-real-discard`, base `main`.
- Do not create, amend, close, or touch any other PR (in particular
  the dependabot PRs #83/#94/#100: untouched).

## 2. Verified current state (strategy-verified 2026-10-06 against
live GitHub and local forensics)

- Remote `main` = `22f38c783d062a9c5352f7bdde8607d9ac299f26`
  (post-083/1 merge; unchanged; verified via `git ls-remote`).
- PR #101 is OPEN and MERGEABLE, base `main`; exact remote head
  `ce8170955cb16ebb6ce32329149aea1450b94bee` (report-only SELF;
  parent `dce0caed112fb09d4f1e21faa944a8bd894893f1` = 083-2-a
  implementation head F). Chain from base verified: T
  `aa3f613547f4f6c5fc8972bcf586856907d660d7` (transcript-only; order
  byte-identical to the activated file; `oap/active` = `083-2-a`) ->
  I `536f8d594a624b9ffa41eb60c71f3a7a07b3bbb6` -> D
  `2ffca481baaf34f7e4c0da1e8202eac07e37ac11` -> F `dce0cae` -> S
  `ce81709`.
- `oap/active` = `083-2-a`.
- Strategy review at S (2026-10-06): criteria 1 through 11 of the
  083-2-a order ALL PASS (PR identity; report-only S; transcript-only
  T; scope of 44 files all in budget categories; no
  dependabot/lockfile/workflow/supply-chain changes; R6
  `contracts/` + `packages/` diff 0 bytes and strip-identity
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
  recomputed by strategy at BOTH base and head with 47 paths; the
  four current-truth surfaces clean in durable form; flake audit:
  the single documented unmodified re-run (T head, runner-shutdown
  signature) is the only re-run and the allowance is CONSUMED).
- REQUIRED CHECKS AT THE EXACT HEAD S `ce81709`: 19/20 terminal
  SUCCESS, 1 FAILURE. All 14 other CI jobs SUCCESS and all 5 CodeQL
  checks SUCCESS (run 37408363055). The failure: CI job `Markdown`
  (run 37408363090, job 112090935394; markdownlint-cli2 v0.23.2 /
  markdownlint v0.41.1 over `**/*.md`): `Summary: 6 issues in 1
  file` — all 6 in `oap/reports/083-2-a-real-discard.md`:
  1. line 244 MD004/ul-style (list marker `+`, expected `-`);
  2. line 414 MD038/no-space-in-code (spaces inside a code span);
  3. line 559 MD026 (heading ends with `,`);
  4. line 635 MD026 (heading ends with `;`);
  5. line 866 MD004/ul-style;
  6. line 932 MD004/ul-style.
- The failure is DETERMINISTIC (markdownlint over committed bytes),
  not a flake class, and the order's single flake allowance is
  already consumed. There is therefore NO legal re-run path; the
  only path is a new commit on the same branch.
- The 083-2-a report itself is honest: it claimed 20/20 only at the
  implementation head F and explicitly deferred the SELF-head roster
  to strategy ("the report-only S head may trigger fresh checks —
  strategy independently waits/verifies SELF per the protocol"). Its
  Criterion 12 one-liner ("terminal and green at the exact report
  head") is nevertheless refuted by the terminal S-head state and is
  corrected by the 083-2-b report (checklist item R-2).

## 3. Finite rejection checklist (2026-09-14 review-unit governance
Section 4) — the COMPLETE list; no further findings are withheld

- R-1 (blocking; merge gate): the required `Markdown` check fails at
  the exact report head S `ce81709` with the 6 violations listed in
  section 2. Executable evidence required:
  1. a formatting-only repair of exactly those 6 sites in
     `oap/reports/083-2-a-real-discard.md` (no change to any claim,
     SHA, number, evidence, or sentence content; the 6 fixes are
     mechanical: list markers, code-span spacing, heading trailing
     punctuation);
  2. markdownlint (repository configuration
     `.markdownlint-cli2.jsonc`) clean on the full tree at the new
     head;
  3. the FULL fresh 20/20 terminal roster at the EXACT new
     report-only head (all 15 CI jobs + all 5 CodeQL checks
     SUCCESS; none failed/cancelled/pending/missing) — verified by
     strategy via `gh`.
- R-2 (record correction in the 083-2-b report): the 083-2-b report
  must state the terminal S-head state explicitly: head
  `ce81709`, CI run 37408363090 + CodeQL run 37408363055, 19/20,
  the 6 exact violations, and that the 083-2-a report's Criterion 12
  "terminal and green at the exact report head" wording is
  superseded by this record (20/20 was proven at implementation
  head F; the SELF-head roster was strategy-verified after the
  report and failed on `Markdown`).
- No other criterion remains open. Strategy found no defect in any
  other requirement of the 083-2-a order at the reviewed head.

## 4. Bounded scope (exactly)

- `oap/reports/083-2-a-real-discard.md`: the 6 lint-site repairs
  ONLY (formatting; no semantic change).
- `oap/reports/083-2-b-markdown-lint-repair.md`: new 083-2-b report.
- `oap/orders/083-2-b-markdown-lint-repair.md` + `oap/active`:
  transcript (executor commits the activated order and
  `active` = `083-2-b`).
- No file outside these four may be modified in this round.

## 5. Explicit non-goals

- No product change of any kind: nothing under `apps/`,
  `services/`, `tests/`, `tools/`, `contracts/`, `packages/`,
  `infra/`; no migrations; no dependencies; no lockfiles; no
  `.github/workflows/`; no supply-chain files.
- No re-run of any unmodified head (the single flake allowance is
  consumed; and a re-run cannot create the green state required at
  the exact head).
- No rewrite of the 083-2-a report content beyond the 6 lint sites
  (that report remains the immutable claim of that round; the
  record correction is carried by the 083-2-b report, not by
  rewriting history).
- No current-truth surface change (README, `oap/INCREMENTS.md`,
  `oap/MVP-PROGRESS.md`, `oap/MVP-CONTRACT-AUDIT.md`): the durable
  in-flight marker (branch + base, no merge claim) remains true on
  the same branch; strategy performs the post-merge flip.
- No change to `contracts/openapi/agent-v1.json` or any generated
  artifact (byte-identity continues to hold; strategy re-proves
  it).
- No PR title/branch/base change; no dependabot touch.

## 6. Requirements

### R1 — Lint-site repair (checklist R-1)

- Repair exactly the 6 violations listed in section 2 in
  `oap/reports/083-2-a-real-discard.md`:
  - lines 244, 866, 932 (MD004): change the unordered-list marker
    `+` to `-`, preserving indentation, nesting, and all text;
  - line 414 (MD038): remove the spaces inside the code span
    (restructure the span or move the quoted phrase out of it) so
    the rendered text is unchanged;
  - lines 559, 635 (MD026): drop the trailing `,` / `;` from the
    headings (the punctuation is not semantically load-bearing; the
    complete sentence already exists in the body).
- After the repair, run the repository markdownlint gate locally
  (same configuration as CI) on the full tree: zero issues.
- The lint-repair commit must touch ONLY that one file.

### R2 — 083-2-b report (checklist R-2)

- New report `oap/reports/083-2-b-markdown-lint-repair.md` (same
  basename as this order) containing, at minimum:
  - status line (COMPLETE only if every checklist item below was
    actually executed; otherwise PARTIAL/BLOCKED with the exact
    gap);
  - the two finite checklist items R-1/R-2 from section 3 with the
    closure evidence for each, including a before/after fragment for
    each of the 6 lint sites;
  - the honest CI record: the S-head `ce81709` terminal state
    (19/20, `Markdown` FAILURE, run/job IDs, the 6 violations) and
    the explicit supersession of the 083-2-a Criterion 12 one-liner;
    every subsequent run at this round's heads with exact outcomes;
  - the exact commit chain for this round: transcript commit (this
    order + `oap/active`), lint-repair commit (implementation
    head), report-only SELF commit (parent = lint-repair commit);
  - `Report publication commit: SELF` and the claimed remote head;
  - the full 20/20 terminal roster at the EXACT new report-only
    head (every job/check named with its conclusion);
  - proof that `git diff ce8170955cb16ebb6ce32329149aea1450b94bee..`
    to the lint-repair head touches exactly one file and only the 6
    lint sites;
  - the cumulative base->head size table grouped per the
    2026-09-14 review-unit governance Section 2 (base =
    `22f38c783d062a9c5352f7bdde8607d9ac299f26`), the predeclared
    budget check, and the CLOSURE_ONLY state (expected: never
    entered; the review trigger cannot fire in this round).

### R3 — Hard constraints

- Only the four files of section 4 are modified; no new files
  besides the 083-2-b report; no deletions.
- `uv.lock`, `pnpm-lock.yaml`, `.github/workflows/*`,
  `tools/supply_chain/*` byte-unchanged; no compose/env change.
- No merge by the executor; no re-run of unmodified heads.

## 7. Acceptance criteria (observable)

1. `git diff ce8170955cb16ebb6ce32329149aea1450b94bee..<lint-repair
   head> --stat` = exactly `oap/reports/083-2-a-real-discard.md`,
   and every hunk is one of the 6 formatting fixes (strategy
   inspects each hunk).
2. Local markdownlint (repository configuration) reports zero
   issues on the full tree at the lint-repair head.
3. `git diff 22f38c783d062a9c5352f7bdde8607d9ac299f26..<new SELF
   head> --stat` = the 44 files of the reviewed 083-2-a scope plus
   `oap/orders/083-2-b-markdown-lint-repair.md` and
   `oap/reports/083-2-b-markdown-lint-repair.md`, with
   `oap/reports/083-2-a-real-discard.md` differing from its
   083-2-a version only at the 6 lint sites.
4. Remote head = report-only SELF; its sole change versus its
   parent is the new 083-2-b report file; parent = the exact
   lint-repair head.
5. `oap/active` = `083-2-b`; the order file at the transcript commit
   is byte-identical to the published file.
6. Full 20-check roster terminal at the EXACT new report head:
   20/20 SUCCESS, none failed/cancelled/pending/missing (strategy
   verifies via `gh` at the literal head SHA).
7. The report contains every R2 item with executed evidence; the
   status is honest.
8. R6 continuation: `contracts/` and `packages/` remain 0-byte diff
   base->head; the strip-identity `921572e7...` value remains
   proven at both (strategy recomputes).

## 8. Verification and workflow

- Local authority as usual (packages, linters, tests, CI logs are
  yours).
- GitHub: push the same branch; the transcript commit may be pushed
  first — its `Markdown` job is EXPECTED to fail (the repair is not
  yet in that tree); that intermediate state is superseded and must
  be recorded honestly; do NOT re-run it.
- No merge by the executor — only strategy merges.
- Flake policy (unchanged): the single documented unmodified
  re-run allowance for PR #101 is CONSUMED (T-head runner-shutdown
  flake, 083-2-a). No re-run of any unmodified head is legal in this
  round; the exact new head must be green as-is.
- The full CI roster must be terminal and green at the exact report
  head (in this round the merge gate is the report head itself, not
  the implementation head).

## 9. Report requirements

See R2 (section 6). The report is executor-owned; publish it as a
report-only commit whose parent is the exact lint-repair head.

## 10. Predeclared review budget (2026-09-14 review-unit
governance Section 1)

- Production/config: 0 files.
- Migrations: 0.
- Tests/evidence: 0 (no new tests; no suite re-run required — the
  repair is transcript formatting).
- Generated artifacts: 0.
- Docs: 2 files (the lint-repaired 083-2-a report; the new 083-2-b
  report).
- OAP transcript: 2 (order + `active`).
- Expected substantive implementation-line scale: 0 (formatting
  only) plus report prose.
- The 20-file review trigger cannot fire; CLOSURE_ONLY is not
  entered.

## 11. Review-unit governance (2026-09-14 amendment, in force)

- Cumulative review: strategy re-reviews the FULL base->head diff
  (46 files) at the new head, not only this round's delta; the
  083-2-a reviewed state carries over for every unchanged file.
- Finite rejection: section 3 is the complete open list; this round
  is a continuation, not a new semantic family.
- No new semantic family enters this round (it cannot: the scope is
  two report files plus the transcript).
