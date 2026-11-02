# OAP 083-9-g execution report: finish diagnostics, closed PARTIAL (source preserved at Gg; local N3 protocol unmet)

## 0. Header facts

- Round: 083-9-g of unresolved numeric objective 083, semantic
  increment 083/9, mode `AMENDED_EXISTING_PR`. Status PARTIAL: N1
  MET (scoped source preserved, both defects fixed, within budget,
  ROOT-verified), N2/N4 MET (ROOT image-input equivalence vs Fd),
  N3 UNMET (local quality protocol violation: tail-masked receipts,
  no retrocredit), N5 UNMET (fresh SELF CI/six not run; Gg CI not
  awaited), N6 MET via this publication. Not accepted; not merged.
- Order: `oap/orders/083-9-g-finish-diagnostics.md` (187 lines,
  12538 bytes, SHA256
  `b1b7de51105c0bc25bde7b320d8215c77dfb493c047f0d2ce1aa4348a71edf9f`),
  committed byte-exact at Gg. Activated 2026-11-02T03:23:53.835491Z,
  control close 03:23:53.914790Z; one exact control OK (2 bytes
  `4f4b`, no LF) retained by reader 87343/PID 3414247 to actual
  terminal/EOF at 03:23:53.914885Z (bytes retained).
- PR: `AMENDED_EXISTING_PR` #113
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/113>, state
  OPEN, base main `d18b6e4c9423f61de99b516be90619bf2ab5d3e0` (D18),
  head branch `oap/083-9-a-remediate-node-brotli-runtime`, worktree
  `/home/janezp/codex-work/slaif-agent-site-083-9-a`, canonical OAP
  root `/home/janezp/codex-work/slaif-agent-site/oap`.
- Round-start head: SELFf
  `085f82900e7744174779731df872cf9e08807c84` (sole parent Ff).
- Pushed commits this round (no amend, force-push, or rebase):
  - Gg `4f48fa38f21d14a9249a988fc724f43b9d7977f2` (PARTIAL
    preservation checkpoint: 2 changed test files, 2 status docs,
    exact g order + active; 6 paths; tree
    `2fcad46847515816fa5953f1f9011dae52bc584d`; sole parent SELFf;
    ROOT independent review PASSED, preservation only)
- Report publication commit: SELF (this report; sole parent Gg;
  sole new path `oap/reports/083-9-g-finish-diagnostics.md`).

## 1. Source completed at Gg (preservation only)

- Baseline: Ff source (g starting 249 gross); old e-191 WIP hashes
  were historical entry conditions only, not restored. Pre-edit
  hashes verified exactly per the order.
- Defect 1 fixed: provider attribution now requires the actual
  `https:` protocol in addition to exact origin equality
  (`blob:https://approved-provider` stays other when not
  same-origin); legitimate same-origin classification and the
  opaque-"null" rejection preserved.
- Defect 2 fixed: the false "excludes every prefix below" comment
  replaced with the truthful statement (other-browser-error
  excludes only the `Failed to load resource:` prefix and the
  space-terminated `Uncaught` prefix; CSP/CORS and other new hints
  can retain the old other
  class; len-79/HTTPS cause remains UNKNOWN).
- Meaningful tests: blob provider negatives
  (`blob:https://player.vimeo.com`, `blob:https://www.youtube-
  nocookie.com`) plus the actual-helper behavior that a blob whose
  embedded origin equals the page stays same-origin; exact-
  origin/default-port/userinfo/hostile-suffix cases preserved.
- Exact 4 status-line replacements (2 per doc: `oap/INCREMENTS.md`,
  `oap/MVP-PROGRESS.md`): active f-to-g, rounds a-e to a-f closed
  PARTIAL; PR112 ON HOLD/083-8-j condition kept.
- Original four classifiers, support.ts, all original media
  assertions/actions/verdicts/counters and 16/4 caps unchanged;
  media-publication.spec.ts byte-unchanged vs SELFf (blob
  `636d3961…8176` carried). Finer JSON dedup by new fields
  permitted as in f, disclosed.
- Budget (actual): family gross 260 vs SELFd (259+1) within HARD
  350; cumulative gross 846 / 20 source paths vs D18 (excluding
  only the activated orders/reports/active transcripts) within
  HARD 1000. Gg: 6 paths, 207 insertions / 9 deletions, bare push
  native 0; clean tree. ROOT Gg review: all 1130 remote/local
  mode/type/blob leaves equal, all 382 actual image inputs equal
  Fd (receipt `root-Gg-remote-and-image-input-independent-review.
  json`, SHA256 `2760a86973ab4481023840fd318006f6c973fda54772bc4b74558d0dd52dcc1c`).

## 2. Local quality attempts: N3 protocol UNMET

- Protocol violation (mine): every g quality exec command ended
  with a trailing `tail`, so the tool exit status was tail's 0 in
  all cases — the same masking class as f's run_gate printf0 that
  g explicitly forbids. Per-gate child natives were captured
  correctly (immediately after the timeout), but the tool-level
  status does not prove them; full child-status and per-file
  hash receipts are incomplete. No retroactive N3 credit.
- Pass 1 (candidate source3 `70a0a608…4bc0186`): lint captured
  0 (36.0 s); format:check captured 0 (6.8 s); typecheck captured
  0 (25.1 s); test captured **1** (70.1 s; 35/36 passed — my new
  blob case wrongly expected "other"; Node 24 parses blob:
  embedded origins, so a same-embedded-origin blob is same-
  origin). Stream 13447 B `d8f52703…efaf64e`.
- In-scope repair (same 3 files, authorized): one test
  expectation + comment corrected to actual helper behavior.
  New candidate source3 `b60fde33…adf03`; family gross 260
  unchanged.
- Pass 2 (unchanged candidate `b60fde33…`, before/after hash
  equal at every gate): lint, format:check, typecheck, test all
  captured **0** (34.8/6.7/24.4/69.0 s; test 3 files / 36 tests
  passed). Tool exits masked as above.
- All 8 gate streams + the failed pass-1 test preserved 0600 under
  0700 at `/tmp/oap-083-9-g/affected/` (pass1-1…4, pass2-1…4);
  deviation/source review receipt
  `root-g-local-deviation-and-source-review.json`. No reruns, no
  further repairs; future qualification will use the official CI
  Node contracts steps (per ROOT), not local repeats.

## 3. Carry (exact subjects, by reference; not re-run)

- d31: 31/31 quality wrapper natives 0 at clean Fd
  `d53035fa527993332aa420fe2aeabcaf850e744c`, fixed anchor run-
  state `703f90ae81117751f06cd8f74e8c414c9f61e751301403fd23d976ce60c66c4e`;
  per-command table in the immutable d report (not duplicated);
  new gates qualify changed inputs only, never a full-31 claim.
- Runtime carry: Pc1 backend/worker + P1 web, qualified only via
  ROOT-proved input equivalence (all 382 actual image inputs
  equal Fd through Gg); no Fc/Fd/Ff/Gg image or local runtime
  run (no-Fc/Fd/Ff-runtime means LOCAL probes, not CI image
  builds).
- d-SELF history: CI 29 SUCCESS / 1 Compose FAILURE (job
  125045957647, len-79 tuple, cause UNKNOWN) and six-image
  artifact 13109259873 stand as qualified history, not future
  final-SELF evidence. f deviation (failed lint, unauthorized
  post-STOP line + gates, UNQUALIFIED) stands in the immutable f
  report; no retrocredit here.

## 4. Forward errata (recorded here; no history edits)

- e: timing (activation rename 00:28:20.578118Z vs control close
  00:28:25.837407Z), audit f2b12e vs final source fcd100, d
  publication d525c2 different-TEMP/inode, e jq tree-field
  erratum (`.commit.tree.sha` vs `.tree.sha`, my query field, not
  API), e "no code" qualification (e did draft 191 gross), Ee
  "CI pending" was an older observation (ROOT verified 30
  SUCCESS before e publication).
- f: publication tool 847146 aggregate 1 came only from a
  trailing shell hash query using a Python-only variable; the
  actual Python atomic publication was native 0 and both copies
  reverified exactly before wire — no republication. f budget
  receipt f248 described an earlier 248/834 snapshot; final
  249/835 proof is `root-Ff-remote-independent-review.json`.
- g: my tree-map return (tool e88166) showed only 6 changed
  entries + leaf counts; ROOT independently proved all 1130
  mode/type/blob leaves equal. Budget exclusions are the exact
  activated transcript paths (orders/reports/active), not broad
  general directories.

## 5. Wire, confirmations, limitations

- Control: exactly one OK (2 bytes `4f4b`, no LF) received by own
  reader 87343/PID 3414247 (terminal; bytes retained); no replay,
  no extra reader.
- Response: exactly ONE `OK` (2 bytes, no LF) to response.fifo
  (inode 4470112) after the remote proofs; no FIFO fsync; then ONE
  byte-retaining next-control reader on control.fifo (inode
  4470111) with actual handle/PID retained.
- Confirmations: no new source beyond Gg; no local checks/tests
  after the authorized passes; no Docker/browser/runtime; no CI
  rerun (Gg auto CI observation only); no acceptance/merge; no
  secret/credential output; no force/amend/rebase/new branch/PR;
  PR #112 (083-8-a) remains OPEN ON HOLD/INACTIVE (only ROOT
  083-8-j may resume); this round amends PR #113 only.
- Limitations: local N3 protocol unmet (masked receipts); Gg
  source is preserved, not locally qualified; final SELF strict
  CI (15368 except CodeQL 57789) + 10 PG children + fresh six-
  image PENDING, will be independently qualified without waiting
  on Gg CI; len-79 cause UNKNOWN; 12 inherited High unchanged; no
  zero-vuln/all-permissive/MVP/release/acceptance claim.
