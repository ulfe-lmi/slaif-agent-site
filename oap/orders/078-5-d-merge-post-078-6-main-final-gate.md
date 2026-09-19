# OAP Work Order — 078-5-d: merge post-078/6 main into PR #85 and re-verify the final gate

- Identifier: `078-5-d` (increment-qualified; fourth round of semantic
  increment 5 of numeric Objective 078; same-PR continuation of
  `078-5-c`)
- PR mode: AMENDED_EXISTING_PR
- Branch: `oap/078-5-a-global-regions-header-footer` (unchanged)
- PR: `#85` — `OAP 078-5-a: site-global regions and header/footer
  management`

## Verified current state (verified at activation, from live GitHub only)

- `main` = `0faebd98cc0d9b14d4e00b7da165f08b815e7df6` (merge commit of
  PR #86 / increment 078/6, `mergedAt` 2026-09-19T02:24:49Z; verified via
  `git ls-remote` at 2026-09-19 04:25 CEST). PR #86's 20/20 required
  checks were verified green on its report-only head `f6f2503`
  (including `Supply-chain evidence` with `critical=0 high=47`); the
  post-merge main branch runs are in progress and are not a gate for
  this round
- PR #85 OPEN/MERGEABLE, not a draft; head
  `2d69caecd77e01ea928adf693eca7607d3759d90` (078-5-c report-only
  commit, parent `63ca6a77567f71477bd51b9617560cfef387a224`); base
  `main`
- 078/6 merged the Chrome-for-Testing `153.0.8010.52` refresh into
  `main` (Dockerfile, `supply-chain/policy.json`,
  `tools/supply_chain/policy.py`, `tools/compose/smoke.sh`, critical
  matrix, 3 test files, 6 docs, `oap/INCREMENTS.md` 078/6 row)
- PR #85's final 20/20 merge gate was deferred to this round by the
  078-5-c order's verification section: the PR tree must contain the
  refreshed browser pin for `Supply-chain evidence` to pass

## Objective

Integrate the post-078/6 `main` into the PR #85 tree with a
history-preserving merge commit, re-verify the full 20/20 required-check
matrix on this round's exact report-only head (including
`Supply-chain evidence`, which must be green with no exception), and
bring PR #85 to a strategically mergeable state.

## Binding decisions

1. History-preserving merge: merge `origin/main`
   (`0faebd98cc0d9b14d4e00b7da165f08b815e7df6`) into
   `oap/078-5-a-global-regions-header-footer` as a merge commit with two
   parents. No rebase, no squash, no force-push, no history
   rewriting.
2. Zero non-transcript changes: this round adds no product, tooling,
   doc, config, or test change of its own beyond the merge and the
   requirement-0 ledger fact correction. If any merge conflict occurs
   outside the OAP transcript files, STOP and report BLOCKED; do not
   hand-merge code.
3. Permitted conflict resolution, transcript files only:
   - `oap/active` → `078-5-d`
   - `oap/INCREMENTS.md` → retain both the branch-side 078/5 row and the
     main-side 078/6 row in ledger order
4. Transcript fact correction (requirement 0): set the `oap/INCREMENTS.md`
   078/6 row to the accepted/merged state (merge `0faebd98`, 2026-09-19).
   This is the only doc edit permitted in this round.
5. Post-merge tree verification: the browser pin `153.0.8010.52`
   (archive URL and SHA256
   `e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9`)
   must be present in `services/browser-worker/Dockerfile`,
   `supply-chain/policy.json`, `tools/supply_chain/policy.py`, and
   `tools/compose/smoke.sh`; the 078/5 feature code and evidence pins of
   rounds a–c must be byte-identical to pre-merge head `2d69cae`.

## Bounded scope — allowed file set

- The merge commit itself (brings in main's already-accepted 078/6
  changes and its 078/6 transcript files)
- `oap/active` (`078-5-d`), this order, this report
- `oap/INCREMENTS.md` (requirement-0 078/6 row state; conflict
  resolution if the merge conflicts there)

## Explicit non-goals

- No product change, no pin re-tuning, no assertion or evidence change
- No rebase, squash, force-push, or branch history rewrite
- No Dependabot PR interaction; no change to `main`
- No modification of the 078/5 implementation or evidence pins from
  rounds a–c

## Requirements

0. Update the `oap/INCREMENTS.md` 078/6 row to the accepted/merged
   state (merge `0faebd98`, 2026-09-19), per the existing row format.
1. Create the history-preserving merge commit of binding decision 1
   (record the merge commit SHA and both parent SHAs).
2. Verify the post-merge tree per binding decision 5 and record the
   evidence: the four pin locations, plus
   `git diff 2d69caecd77e01ea928adf693eca7607d3759d90..<merge-commit> --stat`
   showing only main-brought files and transcript files.
3. Run the full local Compose smoke
   (`sh tools/compose/smoke.sh slaif0075a` run class): all browser
   projects PASS, `compose-e2e: OK`, `public-agent-acceptance: OK`. If
   the documented Puck drag VM flake class occurs, at most one
   unmodified re-run of the failed job, documented in the report.
4. `python tools/check_repository.py` PASS.
5. Push, then make the report-only `SELF` commit (parent = the merge
   commit).
6. Wait for the full CI matrix on the report-only head; every required
   check must be successful — including `Supply-chain evidence`, with no
   exception. If a documented flake-class job fails, at most one
   unmodified re-run, documented.

## Observable acceptance criteria

1. The branch head is a report-only commit whose parent is the merge
   commit with exactly two parents
   (`2d69caecd77e01ea928adf693eca7607d3759d90` and
   `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`); branch history preserved
   (no rebase/squash/force-push).
2. The merge commit's diff against `2d69cae` contains only the
   main-brought 078/6 files and OAP transcript files; no other content
   change.
3. The `oap/INCREMENTS.md` 078/6 row records the accepted/merged state
   (merge `0faebd98`, 2026-09-19).
4. The full local Compose smoke passes end-to-end (exact final status
   lines recorded), or a single documented flake-class re-run occurred.
5. On the exact report-only head, all 20 required GitHub checks are
   successful — including `Supply-chain evidence`. The report records
   every check's conclusion on the exact head.
6. The report contains per-criterion evidence and the cumulative
   base→head size grouped per review-unit governance §2 (base =
   `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`, including the merge
   commit).

## Predeclared review budget (review-unit governance §1)

- Production/config files: 0 added by this round (main-brought refresh
  only, already accepted in 078/6)
- Migrations: 0
- Test/evidence footprint: 0 new (main-brought test updates already
  reviewed in 078/6)
- Generated-contract footprint: none
- Docs footprint: 1 ledger line (`oap/INCREMENTS.md` 078/6 row state)
- OAP transcript footprint: order + active + report
- Expected substantive implementation scale: 0 lines (merge commit)
- Review trigger: cannot fire; cumulative size is 078/5 rounds a–c plus
  the already-accepted main-brought 078/6 content

## Security

No new trust surface. The merge only integrates already-accepted 078/6
changes. No gate weakening: the 20/20 requirement is strict and
`Supply-chain evidence` must pass on this head. No secrets in diff or
report.

## GitHub workflow

AMENDED_EXISTING_PR: same branch
`oap/078-5-a-global-regions-header-footer`, PR #85, base `main`. All
commits pushed; the report commit is `SELF`; Strategy is the only
merger (strategic merge of PR #85 follows Strategy's acceptance of this
round).

## Report requirements

Standard OAP report template plus explicitly:

- the merge commit SHA and both parent SHAs;
- the complete conflict list (if any) and their resolutions
  (transcript files only);
- the post-merge tree verification evidence (the four pin locations and
  the `git diff 2d69cae..<merge-commit> --stat` output);
- the `oap/INCREMENTS.md` 078/6 row state change;
- the exact final status lines of the local Compose smoke run;
- the conclusion of every one of the 20 required checks on the exact
  report-only head;
- the cumulative base→head size grouped per review-unit governance §2
  (base `d576fec`, including the merge commit).

## Local authority

Standard executor authority in the disposable VM: packages, Docker,
browser tooling, test execution, CI log retrieval. Guest sudo only if
genuinely required; record any use.
