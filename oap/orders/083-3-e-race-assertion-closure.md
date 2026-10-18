# OAP Work Order — 083-3-e: structural race assertion closure

> STATUS: ACTIVATED strategic continuation. Operative only after exact
> active083-3-e and this round's control FIFO OK. Timing is in the ledger.

## 1. Identity, authority and independently verified state

- ID: `083-3-e`; Objective083, increment3; CLOSURE_ONLY since b activation.
- Mode: AMEND_EXISTING_PR. NO NEW PR, merge, auto-merge or closure.
- PR: [#102](https://github.com/ulfe-lmi/slaif-agent-site/pull/102).
- Branch: `oap/083-3-a-cache-outbox-consumer`; base `main`.
- Starting report-only S-d: `69d43347cb9f7060bee2edac0de94d58513b3fee`.
- S-d first parent / implementation I-d:
  `fe79b3af3a345df869e20fbfa0557e6b03ce7c9f`.
- Verified main at2026-10-18T02:55:37Z:
  `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`.
- At02:54:52Z current I-d has20 COMPLETED/SUCCESS checks. CI39087639095
  and CodeQL39087639081 are both attempt1. This does not prove the full
  local integration collection or future final report head.

Exact d response4f4b received2026-10-18T02:58:19.875772Z; strategy read all488
report lines and independently verified S-d is report-only, parent I-d and
remote bytes match. At 2026-10-18T03:01:22.053484+00:00 S-d
check states: 7 IN_PROGRESS, 13 SUCCESS. No acceptance or merge;
the failed full suite requires this finite correction regardless of pending CI.

The human authorized the browser refresh and resumed the full planned OAP
goal. This is a finite evidence correction needed to close that same PR,
without product behavior or security-policy changes. Keep the sole coding
executor visible in the same tmux window's other pane, exactly
`codex --yolo --profile qwen-neumann`, no model/provider override.

Actual coding repo `/home/janezp/codex-work/slaif-agent-site`; strategic
workspace `/home/janezp/codex-supervision/slaif-agent-site`. Verified control
and response FIFOs are in the strategic workspace. Read control/write response,
exact ASCII OK (`4f4b`), no LF. Read coding AGENTS/protocol, compact architecture,
governance and all a/b/c/d orders/reports. Never load full ARCHITECTURE.md.
Execute only after this round's exact signal and active083-3-e.

## 2. Finite rejection and actual failure

C-2 Apache repair and the d Python/browser qualification are supported by
successful measured evidence. C-1 final20/20 still applies. C-4 is the missing
clean full integration result and its two precisely identified assertion bugs.

The first d full run returned316 PASSED/4 setupERRORS due to stale disposable
foundation ownership. That failure, cleanup and rerun remain historical facts.
The fresh complete rerun started01:45:07Z and ended02:53:13Z with actual
`INTEG_FINAL_EXIT:1`: **1 failed,319 passed in4081.34s**. No full PASS exists.
Root independently checked and archived the complete log:

```text
/tmp/oap-083-3-d/integration-final.log
sha256:5f94be98b491434ed67b05f99743d19c5cefd89a965d0c9cab910bf3c74e63b7
failed node: services/backend/tests/integration/test_human_editor_production_http.py::test_editor_agent_structural_races_share_workspace_site_lock
```

At line1405 the actual endpoint-ordered result is restore409,
redirect-create201. Sorting gives `[201,409]`, while the assertion expects
either `[200,409]` or `[409,201]`. Its second alternative is unreachable as a
sorted output. The valid redirect-winning branch is rejected by the test.
This traceback establishes an expected-pair ordering defect, not broken
product locking. Do not call the whole failed run passing or a CI flake.

Root inspected the remaining same-function assertions and found the same
unreachable `[409,201]` sorted alternative at lines1581-1586 for redirect
deletion versus dependent redirect creation. That later assertion was not
reached in the failed run. Correct both named defects; preserve all other
concurrency, state and hostile-negative expectations. Any d isolated
diagnostic result must remain distinct from the failed complete run.

## 3. Closed implementation scope and non-goals

Only ONE non-transcript file may change:
`services/backend/tests/integration/test_human_editor_production_http.py`.
Only the two assertion expressions identified above may change, with local
formatting required for those expressions. Preserve the test's name, fixture,
setup, calls, payloads, barrier/lock mechanism, all later cases and assertions.

Use endpoint-ordered status-pair assertions with exactly these allowed sets:

1. Page restore versus competing redirect creation:
   `(restore, redirect_create)` in `{(200,409),(409,201)}`.
2. Source redirect deletion versus dependent redirect creation:
   `(delete, dependent_create)` in `{(200,409),(200,422),(409,201)}`.

No swapped endpoint meanings, double success, double conflict,5xx or other
status may be accepted. Preserve response-body diagnostics. Do not add toy
tests that merely repeat these constants. Run the existing production-boundary
test completely, including its cases after the first corrected assertion.

No application code, migration, fixture, role/grant, capability, lock function,
timeout/barrier helper, test filter/skip/xfail, dependency, lockfile, runtime
pin, Dockerfile, policy, scanner, exception, matrix history, workflow, generated
contract, product documentation or other test changes. No adjacent objective,
new semantic family, dependabot work, new issue/comment/PR or old transcript
rewrite. Preserve untracked `.codex/`, `CODEX-SESSIONS.md`, `codex.sh` unstaged.

The test corrects its representation of existing allowed outcomes; it does
not change product authority. Agent context remains server-owned and site/
workspace-bound; publication human-only and reviewer-atomic; media immutable;
artifacts private; browser observational and confined without DB/reviewer/
human authority. Foundation remains registry-only0.2.0 with exact uv.lock
hashes. All previous runtime/security/lifecycle non-goals remain in force.

## 4. Execution, verification and observable acceptance

1. Reconcile exact open PR/base/start S-d and its report-only parent, no
   duplicate increment PR or existing e report. Commit T-e first, unchanged
   activated order and active bytes only. Preserve historical artifacts.
2. Reproduce the predicate mismatch from retained actual d evidence and read
   both complete surrounding test cases. Apply only the two named assertion
   corrections. Review proves exact allowed ordered pairs, preserved rejection
   behavior and no production/security change. No random rerun erases a failure.
3. Run the focused race test to completion, including all its later assertions,
   with actual exit0. Then obtain a completed isolated FULL
   `uv run --frozen pytest services/backend/tests/integration -q` result:
  320 PASSED,0 failed/errors/skips, actual exit0. No filtering, aggregate
  319+1 substitute, xfail, reduced collection or concurrent pytest against the
   same fixture. Preserve every real failure and process-cleanup result.
4. Run all mandatory Python, process, Node and preparation checks from coding
   AGENTS, with real command exits. Existing clean-copy tooling may be reused;
   prove its tracked tree equals I-e. Serialize colliding builds, retain
   PIPESTATUS and restore temporary host settings on every exit. Executor owns
   disposable packages, DBs, services and browsers; no human/strategy setup.
5. Existing successful d six-image qualification, candidate8, full19-project
   Compose/six-device smoke and runtime/security measurements may be adopted
   only for byte-identical unaffected production/build inputs, explicitly
   naming tested I-d, hashes and exact outcomes. Verify runtime source/pins/
   locks and packaged code remain identical. Do not pretend adopted tests were
   rerun or relabel failed integration as adopted PASS. Final GitHub CI still
   runs the complete20-check roster; no new local security exception or pin.
6. Contracts/packages, Agent route policy, capabilities, NGINX and deployment
   wiring remain byte-identical. Reprove recursive x-slaif-* stripped OpenAPI
   digest `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
   using the a/d canonicalization convention. No generated change.
7. Push only this branch, inspect implementation checks and update the existing
   PR description truthfully. Explain the complete local-suite result and
   correction; separate anonymous canonical public content from private
   authorized review/workspace surfaces. Public HTML is dynamic with the
   existing private/no-store headers; only content-addressed public media is
   digest-verified and immutable. Human workspace/review access uses human
   authentication/RBAC; the Agent API uses workspace-bound agent capabilities.
   Do not call human review capability-scoped or public HTML immutable. Current
   d PR-body wording conflates those distinctions; fix the metadata. No broad
   MVP-completion claim.
8. All20 required names in b5/R3 must be terminal SUCCESS on the FINAL e
   report-only head. Strategy verifies independently. Pending report-head
   checks are pending, never green. No deterministic rerun; the one documented
   CI-flake allowance remains unused. Local diagnostics are not CI reruns.

## 5. Publication, report, budget and merge gate

Publish exactly `oap/reports/083-3-e-race-assertion-closure.md`: complete final
content linted with exact repo config/--no-globs before atomic same-filesystem
rename. Report-only S-e has first parent exactly the literal40-hex
`Implementation head SHA` and changes only this new report. Include
`Report publication commit: SELF`, exact T/I SHAs, order hash, active bytes/hex,
all per-criterion evidence, commands/real exits, retained failed-run diagnosis,
any isolated diagnostic, precise adopted-versus-rerun evidence, each observed
CI SHA/run/attempt and complete grouped budget. One honest status enum.

Evidence limits: d's historical attribution of the stale foundation role to b
is inferential timing analysis, not a retained session-ID match independently
proven by strategy. Describe the established cause as an earlier interrupted
fixture session; do not upgrade that inference into a directly observed fact.
Preserve all earlier reports unchanged and correct current PR metadata only.

Push and verify remote S-e, exact bytes/parent/sole path before exact response
OK. No repository mutation follows S-e. End only this bounded goal and block
on control again. If another out-of-scope failure arises, preserve complete
diagnostics and return an honest report; do not expand scope or waive a gate.

Predeclared e budget:0 production/config,0 migrations,1 test/evidence,
0 generated,0 docs,3 transcript paths (active overlaps). Only two local
assertion hunks, expected fewer than20 substantive changed lines. After d's
expected49-file publication, expected cumulative52 unique files:12 production/
config +1 migration,19 tests/evidence,0 generated,9 docs,11 transcript.
Recompute actual d baseline/final counts and itemize every variance. Production
review trigger remains NOT_FIRED at13 including migration; CLOSURE_ONLY remains
in force. No new semantic family or budget gaming.

Strategy alone accepts/merges after independent all-round identity/scope/
architecture/security/docs/evidence review, successful full integration and
all20 required exact-S checks. Merge-commit mode, guarded by accepted head;
verify merged PR, remote main and post-merge checks before advancing. No084
activation or whole-product readiness claim follows merely from this report.
