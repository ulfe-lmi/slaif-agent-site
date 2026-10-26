# OAP 083-6-a execution report — restore frozen-review control reliability (PARTIAL)

## 0. Status

| Field | Value |
| --- | --- |
| Round | 083-6-a (numeric objective 083, increment 6, round letter a) — FROZEN_REVIEW_CONTROL_RELIABILITY |
| Order | `oap/orders/083-6-a-restore-frozen-review-controls.md` (298 lines, committed unchanged with the activation commit) |
| Order SHA-256 | `9363a6678c1b1c7d23ab29bc2e379822edfe0571c18e8cc285f2da8a9c99ae54` |
| `oap/active` bytes | `083-6-a` + LF (8 bytes, hex `3038332d362d610a`) |
| PR mode | CREATED_NEW_PR (PR #110; branch `oap/083-6-a-stabilize-frozen-review-controls`; base verified remote main `f35ec75319afd966d02ee2b7b8cb1db1eb4cd144`) |
| Status | **PARTIAL** at literal implementation I `9d580cb49f1b8e76873a0f5bce50ca82c7a5d8f1`. Qualified at I: clean-isolated-worktree complete ALL31 (31/31 native 0), two full focused parity runs (native 0), R5 baseline trials 2/2 at 76ef, R6 controlled transport proof attempt3 (native 0). FAILED at I: fresh literal WHOLE 0835 (governance Puck drag over-adding, expected 2 received 5, cause UNKNOWN); all later WHOLE projects NOT RUN. Outer teardown primary-error-preservation finding remains UNFIXED (section 11). Original post-merge 600s CI stall: unreproduced, cause UNKNOWN. Current-S CI recorded only as actually observed/pending (section 10.4). PARTIAL is a handoff, not acceptance. |
| Report publication commit | SELF (this report; sole path; first parent exactly I `9d580cb49f1b8e76873a0f5bce50ca82c7a5d8f1`) |

## 1. Identity, control handshake

- ID: 083-6-a, numeric objective 083, increment 6, CREATE_NEW_PR, same objective family as
  merged PR #107 (083/5 at `f35ec753`, merged 2026-10-25T20:30:05Z).

- Order (read FULL, immutable): 298 lines, SHA-256
  `9363a6678c1b1c7d23ab29bc2e379822edfe0571c18e8cc285f2da8a9c99ae54`,
  `oap/orders/083-6-a-restore-frozen-review-controls.md`.

- Active: `oap/active` = `083-6-a` + LF, 8 bytes, hex `3038332d362d610a` (verified byte-exact
  at activation and still so at publication).

- The ONE root control OK for this round: root writer PID 4143625 (session 12690) wrote exactly
  2 bytes `4f4b` (no LF) to strategic `control.fifo` at 2026-10-25T21:31:00.086566Z and closed
  (receipts `/tmp/oap-083-6-a/control-written.json`, `control-native-session.json`
  TERMINAL_0/writer_closed). Consumed ONCE at that instant by the primary reader; no control
  replay. No `response.fifo` write of any kind occurred during the round until this final
  publication; the sole root response reader (85158) remains in place per root.

- Prospective root workorders read FULL during the round (all under
  `/home/janezp/codex-supervision/slaif-agent-site/workorders/`): R6 controlled-transport
  proof (24L), R6 preflight correction, R6 observed-transport adjudication and attempt3,
  ALL31 clean-worktree verification decision, WHOLE failure and PARTIAL publication decision
  (this report's governing correction set). No order/active rewrite, no new activation.

## 2. PR and source identities

- PR #110 (OPEN, unique 083/6), URL
  `https://github.com/ulfe-lmi/slaif-agent-site/pull/110`, base `main` at
  `f35ec75319afd966d02ee2b7b8cb1db1eb4cd144` (remote main independently re-verified before
  push), head branch `oap/083-6-a-stabilize-frozen-review-controls`.

- Implementation I (literal): `9d580cb49f1b8e76873a0f5bce50ca82c7a5d8f1`, tree
  `324b2480bd306b16c7cce016d1724fa13264a763`.

- Implementation commits (7, base f35 excluded):

  | Commit | Content |
  | --- | --- |
  | `2f4b482` | activate round: order + active (sole change set, exact bytes) |
  | `4fc68d0` | R2/R3 baseline instrumentation: bounded op-level control diagnostics + fresh-document sentinel |
  | `d3ef754` | R2: close-failure guard with body>collector>close failure priority |
  | `76ef96a` | R2: persist observed response facts (status/navreq/mainframe) into common submit state |
  | `425a166` | R3: bind the control POST response to the main-frame navigation request |
  | `36cd237` | R7: document the diagnostics in `docs/TESTING.md` + `oap/MVP-PROGRESS.md` |
  | `9d580cb` | R2: explicit failure-presence flag for the pairing cleanup (= I) |

- Diff `f35ec753..9d580cb` (`git diff --minimal`): EXACTLY 5 paths —
  `tests/e2e/frozen-review-parity.spec.ts` (368 lines: 345/23),
  `docs/TESTING.md` (45: 45/0), `oap/MVP-PROGRESS.md` (4: 2/2),
  `oap/orders/083-6-a-restore-frozen-review-controls.md` (298: 298/0),
  `oap/active` (2: 1/1). Total +691/-26. Zero production paths;
  `tests/e2e/reporter.mjs` never touched; no workflow/lock/pin/config change.

## 3. R1 — reconciliation, baseline, and timeout-propagation audit

- Subject of the round: the post-merge CI failure on main `f35ec753` — run 40231055425,
  Compose job 121282677173. Original log preserved:
  `/tmp/oap-postmerge-107-20261025/compose-job121282677173-original.log` (251273B, SHA-256
  `6c3d97862dce9727ae269067f7b8c04a2c152eb7aadecb0795df5cc919b377d5`). Failure:
  `frozen-review-parity-six-stable-pairings` hit its explicit 600000ms test timeout; last
  logged stage `phaseB/firefox/DesktopFirefox/controls` (38868ms cumulative — an entered
  timestamp, not a stage duration). ALL19 E2E records before it (including the six frozen
  pairings of other stages) passed.

- Reconciliation: remote main verified `f35ec753` (PR #107 merged 2026-10-25T20:30:05Z,
  tree = fS); the failing spec file at main is byte-identical to the baseline this round
  instrumented (R1 baseline hashes in `/tmp/oap-083-6-a/r1-baseline-hashes.txt`).

- Pinned Playwright 1.62.1 timeout-propagation audit (source-backed; receipts and the peer
  adjudication preserved under `/tmp/oap-083-6-a/`): the runner's auto fixture sets
  `_defaultTimeout`/`_defaultNavigationTimeout` to 0 for the test context
  (`playwright/lib/index.js` 341..354); manually launched contexts DO receive runner global
  timeout defaults through the `_didCreateContext` -> `_setupBrowserContext` ->
  `setDefaultTimeout` chain (coreBundle 62287..62304 and the navigation analogue); the
  30000ms core fallback applies only absent an override. Consequently the spec's action-level
  APIs were UNBOUNDED except the 8s `expect` timeouts and the 600s test timeout.
  CORRECTION PRESERVED: an earlier steering claim that "manually launched contexts do NOT
  inherit runner action/navigation defaults" was overbroad/wrong; the corrected statement
  above is source-backed, while the exact stalled leg (A/B/C), the wait that hung, and the
  root cause of the 600s stall remain UNKNOWN. No flake/infrastructure/fixed-cause label is
  attached anywhere in this round.

- R5 baseline: the parity spec at baseline commit `76ef96a36f700522842dc06719be8563bf927096`
  (spec blob `3b30d167d0d8fac41308055ac6fb32c7678a4799`).

## 4. R2 — bounded op-level instrumentation (committed) and its history

Committed design (all in `tests/e2e/frozen-review-parity.spec.ts`; `tests/e2e/reporter.mjs`
UNCHANGED — it reads the first `type=stage` annotation via `find`):

- ONE shared `type=stage` annotation extended with `op` + `flags`; fixed enums/booleans/
  numeric status/relative ms ONLY. No URLs, IDs, tokens, nonces, bodies, DOM, or raw call
  logs cross to output.
- Per-leg explicit diagnostic deadlines <= 30000ms (R4) with a real `AbortController`;
  pending sibling waits are rejected through the signal and drained via bounded
  `Promise.allSettled`.
- FIRST-FAILURE PRESERVATION: on first failure the operation freezes — the first-failure leg
  state is snapshotted BEFORE abort/drain so no late leg or cleanup can overwrite it;
  heartbeat annotations stop.
- Sanitized rethrow: `controls submit-X failed leg=<resp|nav|click|status>
  class=<timeout|target-closed|aborted|error|unknown> [r= n= c=] [status= navreq=
  mainframe=] t=<ms>`. Class is a fixed whitelist derived from `error.name`
  (TimeoutError/TargetClosedError/AbortError); the raw error message/cause/Playwright call
  log is NEVER stored, serialized, or attached (it can carry private URLs); the sanitized
  error is thrown from function scope without `cause:`.
- Observed response facts (numeric status + two booleans) are persisted into common submit
  state so the heartbeat, freeze, and first-failure lines retain
  `status/navreq/mainframe` after the transient submit-response marker is replaced.
- Freshness sentinel `__slaif_fpar_doc`: per-document `crypto.randomUUID()` via context init
  script on all run-phase contexts; the pre-click value must be proven a non-empty string
  (safe rejection, no fallback); post-POST comparison via `page.evaluate` with ONE
  serialized object argument `{key, before}`; only the booleans `{installed, changed}` cross
  back; the raw marker is never logged.
- Cleanup failure priority BODY > COLLECTOR > CLOSE (commit `d3ef754`): a close failure
  still fails the test when body and collector passed; the original collector assertion is
  retained on successful body.
- Explicit failure-PRESENCE flag `failureCaptured` (commit `9d580cb` = I): the pairing
  cleanup distinguishes "no failure captured" from "an arbitrary `undefined` throw" so
  cleanup cannot turn any captured failure into success. (The outer test-level teardown
  finding in section 11 is a SEPARATE, still-UNFIXED requirement.)
- Statics at every commit: prettier / tsc (`tests/e2e/tsconfig.json`) / eslint on the spec
  all actual native child exit 0 (logs `/tmp/oap-083-6-a/statics/`, `.exit` files = actual
  child exits). HISTORY PRESERVED: the earliest statics attempts (`tsc-1`, `tsc-2`,
  `eslint-1`, `prettier-write1/2`) carry NO valid native-exit capture — an earlier
  `tsc ... | head -20; echo TSC_EXIT=$?` captured the HEAD pipe exit, not tsc's; those are
  recorded as FAILED/native-UNKNOWN, never as TSC pass 0. All later numbered attempts
  (`tsc-3..9`, `eslint-2..8`, `prettier-write3..9`) include real native exits.

Preflight fixture failures (3, preserved; harness gap, NOT product defect — root
source-verified `tools/compose/smoke.sh` 217..239):

- `/tmp/oap-083-6-a/r5-diag-run1.log`, `r5-gov-rerun1.log` (invalid: re-ran the one-shot
  setup on an already initialized stack), `r5-gov-freshcheck1.log` — governance
  `governance-visible-workflows-negatives-and-privacy` stage `membership-add-visible`
  (line 143) strict-mode violation (2 `role=status` elements). Root cause: the early
  harness omitted the EXACT fixed two-account OIDC fixture seed that smoke.sh performs
  before setup/governance (byte-exact scratch copy
  `/tmp/oap-083-6-a/fixture-seed-0836a.sql`, SHA-256 `f432566e...`, strict
  uninitialized-DB precondition). DB existence booleans recorded on the dirty stack.
  Preserved; no status-selector relaxation, no product-bug claim.

## 5. R3 — main-frame navigation binding (committed `425a166`)

- The POST-response waiter predicate now requires, in addition to POST method and same
  expected URL: `request().isNavigationRequest()` AND `response.frame() ===
  page.mainFrame()`. An iframe/fetch or unrelated same-URL response is NOT accepted.
- Extracted source evidence for the controlled proof (section 8): old `76ef96a` predicate
  lacks the binding (blob `3b30d167...`); new `425a166` predicate contains it (blob
  `61238ad7...`); the two helper extractions differ ONLY in the R3 binding and its comments
  (verified diff; no reimplementation).

## 6. R4 — bounds invariants (unchanged)

- The parity test timeout remains EXACTLY 600000ms; `retries: 0`; `workers: 1`;
  `expect.timeout` 8000ms; no config/CI/workflow/pin/lock change anywhere in the diff.
- The per-leg <= 30000ms deadlines are DIAGNOSTIC bounds inside the test: any pending stall
  now yields an attributed leg error (leg/class/flags) before the global budget.
- Timeout alone is NOT the repair: the repair is the main-frame/navigation binding plus
  fresh-document identity (R3) with bounded, first-failure-preserving diagnostics (R2).

## 7. R5 — baseline trials 1+2 at 76ef (budget 2/2 consumed)

- Trial 1: fresh owned stack `slaif0835` + EXACT smoke.sh 217..239 fixture seed +
  setup+governance prerequisites (all native 0) + the exact focused parity command
  (`pnpm exec playwright test tests/e2e/frozen-review-parity.spec.ts --no-deps
  --project=freeze-review-snapshot` with `SLAIF_E2E_SECRET_FILE` /
  `SLAIF_E2E_COMPOSE_PROJECT` / `SLAIF_E2E_OUTPUT_DIR`). Parity NATIVE 0, 141830ms.
  Log `/tmp/oap-083-6-a/r5-trial1.log` (14423B, SHA-256
  `d0bb5dab730db0ad78f715ba7578862dd9223a75ddecae9ab856ea69d130aca8`); RAW START/END
  snapshots in-log show same HEAD/tree `76ef96a...` and source clean except the exact
  human3. Output dir preserved.
- Trial 2: same I, same harness, distinct attempt: parity NATIVE 0, 142929ms
  (`r5-trial2.log`, SHA-256
  `2e7f1a3ebdc52293c76c8a926f6e56c8282455b2634008549bdc77b1dfe5723d`).
- Image provenance (both trials): `docker compose up` without `--build` reuses cached
  images; the 5 selected opaque image IDs EXACTLY match the qualified I24a G3 export
  manifest (root-verified). Label as actually recorded: cached subject proven, NOT built at
  the trial HEAD; `tests/e2e` appears in no Dockerfile COPY, so spec-only source changes
  cannot alter image content.
- SIDEcar CAVEAT (preserved, not relabeled): the trial1/trial2 sidecars recompute
  `head_start`/`tree_start` at END (harness proof bug); the independent RAW START/END
  snapshots inside each log control and qualify the trials. The f1/f2 driver (section
  10.2) captures the start variables at launch.
- The original CI 600s stall did NOT reproduce in either trial. Two green trials alone
  establish NO repair and NO cause: the 600s failure remains UNKNOWN/unreproduced. No
  third baseline run exists (budget 2/2). These are BASELINE trials at 76ef — NOT final-I
  trials.

## 8. R6 — controlled native transport proof (three preserved attempts)

Purpose (root-adjudicated): prove the pre-existing transport-oracle gap in the old
predicate and that the R3 binding fixes it on a controlled counterfactual — NOT a claim
about the historical 600s cause. One finite suite per authorized attempt; pinned Playwright
1.62.1 Firefox (firefox-1538); disposable 127.0.0.1 HTTP fixture; ACTUAL unmodified helper
extractions with exact source hashes (`extraction-manifest.json`): old `76ef96a`
extracted SHA-256 `3a5c83c735cdad24639ce60761f7abaa44c2c6d1c4c6fa6115205bd5f9d9d18d`,
new `425a166` extracted SHA-256
`7e81c73baaf05369b5aa7eb9c44e3c340bb3a171cf4b9ccfb39d033d2c8eb1e6` (byte-identical across
all three attempts; no helper mutation). Four operations in one browser suite:
old-valid / new-valid (same-URL native MAIN-frame form POST, expected accept) and
old-invalid / new-invalid (same-URL form POST targeting an IFRAME + a separate
MAIN-frame GET coordinated from the real form-submit + iframe-load events; no timers,
sleeps, or fabricated responses).

- v1 (`/tmp/oap-083-6-a/transport-suite/`): ZERO-OPERATION preflight failure — the driver
  read the sentinel on the initial `about:blank` page BEFORE `page.goto` (no secure
  context, so `crypto.randomUUID()` never populated the marker). TSC native 0, suite
  native 1 at 22:57:49Z; no helper invocation or fixture POST occurred. Preserved intact.
- attempt2 prep-run1 (`transport-suite-attempt2/prep-run1-compile-fail.log` +
  `driver-prep-run1.ts` + `prep-run1-hashes.txt`): zero-operation TSC failure TS18048
  (`e.eventRe` possibly undefined across a closure; fixed with a local const capture).
  Compiler preparation only — not a browser behavior run.
- attempt2 suite (ONE browser execution, 23:10:32..23:11:11Z): TSC native 0, SUITE native
  1, `SUITE_VERDICT=FAIL failed_ops=old-invalid,new-invalid`. Core behavior matched the
  predicted property on ALL four operations (old-valid/new-valid accept with MAIN POST 200
  `navreq=1 mainframe=1` and fresh document; old-invalid ACCEPT despite
  `MAINPOST0/iframePOST2/MAINGET2/status200` with the helper's own observation
  `navreq=1 mainframe=0` — the oracle gap; new-invalid REJECT sanitized
  `leg=resp class=timeout r=2 n=1 c=1 t=30016ms`, overall 30397ms). The FAIL verdict is
  due to two driver-side artifacts: an unjustified exact `framePosts==1` assumption (actual
  2 in both invalid ops — the browser resubmits the form to the POST-navigated subframe on
  the main-frame reload; WHY is NOT established and NOT claimed) and a cosmetic
  `flags= r=...` double-space in the driver-built result string (the helper's actual
  sanitized message was exactly the expected fixed form). Logs: `run.log` (438B, SHA-256
  `3d5f2b10d662d02b2c518ae7c19cc4399f559f8f4efd5702b6309049d172b041`), `suite.log` (3049B,
  SHA-256 `8684dcac6e465cd2e630ab564edb6d1a07ade52e68fdcf8f5643e9660d7fe4c4`),
  `results-index.md`; full directory hashes in
  `/tmp/oap-083-6-a/attempt2-preservation-hashes.txt`. NOT relabeled PASS.
- attempt3 (per root adjudication
  `083-6a-R6-observed-transport-adjudication-and-attempt3-2026-10-25.md` — the contract
  requires rejection of responses from ANY iframe while an independent MAIN GET changes the
  main document; stronger independent identity observations; structured rejection fields;
  server/browser count agreement; invalid: MAIN POST 0, iframe POST >= 1, ALL observed
  POSTs same-URL/native-navigation/foreign-frame, independent MAIN GET (initial + reload =
  2), status 200, exactly one native click per op; valid cases exact; no assertion on WHY
  the invalid fixture produced additional iframe requests): ONE TSC compile attempt
  (native 0) + ONE browser suite execution, 23:34:04..23:34:43Z (~39s <= 120s watchdog).
  **SUITE_NATIVE_EXIT=0, SUITE_VERDICT=PASS, all four `expectation_met=1`**:
  old-valid `accept` (server `docposts=1 frameposts=0 docgets=1 poststatus=200`; browser
  `mainposts=1 foreignposts=0 otherposts=0`; agreement; click_transitions=1; helper
  `status=200 navreq=1 mainframe=1`); new-valid identical exact positive transport;
  old-invalid `accept` (server `docposts=0 frameposts=2 docgets=2 poststatus=200`; browser
  `mainposts=0 foreignposts=2 otherposts=0`; agreement; helper `status=200 navreq=1
  mainframe=0`) — the pre-existing transport-oracle gap DEMONSTRATED; new-invalid
  `reject` with structured fields `leg=resp class=timeout r=2 n=1 c=1 status_evidence=0
  t=30004ms` (safe bounded refusal at the 30s diagnostic deadline; no raw message/cause),
  same server/browser transport observations, duration 30394ms < 60000. Evidence:
  `transport-suite-attempt3/` — `run.log` (419B, SHA-256
  `c287f438829dde36421a23b7d2dfd79d094cd8f3dff97a4d037ad387b3728004`), `suite.log` (3367B,
  SHA-256 `1b9943cc1e8fdf1536d5844d2257dc6bffd8b34d2db77e88530c83a4953f94ab`),
  `suite-sidecar.json` (finalized after logs), `results-index.md`, `setup-history.md`.
  Root independently reviewed (receipt
  `strategic-R6-attempt3-native-transport-proof-independent-review.json`).

R6 scope statements (binding for downstream claims): this experiment proves the
pre-existing transport-oracle defect in the old predicate and that the R3 binding fixes it
on this controlled counterfactual. It does NOT establish the singular cause of the original
CI Firefox 600s stall (still UNKNOWN/unreproduced), does NOT establish why the invalid
fixture produced two iframe POSTs, and authorizes NO flake/infrastructure/root-cause-fixed
label. Scratch only: zero product/test/doc/workflow source changes; final I stays `9d580cb`.

## 9. R7 — documentation (committed `36cd237`)

- `docs/TESTING.md` (+45 lines): describes the R2 bounded diagnostics and the R3 binding,
  records the two ACTUAL passed baseline trials (141830/142929ms at 76ef), states the CI
  600s stall as unreproduced/cause-UNKNOWN, and preserves the corrected manual-context
  timeout-propagation statement.
- `oap/MVP-PROGRESS.md` (2/2): 083/5 marked accepted and merged in PR #107 at `f35ec753`
  on 2026-10-25; 083/6 in flight at 083-6-a on base `f35ec753`.
- Scope/inflight state kept accurate; no new lifecycle, feature, or readiness claims.

## 10. Final gates at literal I `9d580cb`

### 10.1 ALL31 — working-tree attempt FAILED (human3 only); clean-worktree complete run QUALIFIED

- Runner: `/tmp/oap-083-6-a/all31-runner-0836a.sh` (bash; decimal `08`/`09` labels via `10#`
  arithmetic; immediate native child exit per command with no pipeline substitution;
  provenance snapshots at start/end; the timestamp stamp was corrected to Python UTC
  isoformat with zero-padded 6-digit microseconds because uutils `date %6N` emits
  variable-width fractions (083-5e adjudication) — EXACT 31 argvs and order unchanged;
  the runner now REFUSES any pre-existing manifest/attempt artifacts instead of
  truncating prior logs).
- Working-tree attempt (`/tmp/oap-083-6-a/all31-final-I9d58`, 23:14:17.987513Z ..
  23:19:00.946342Z; start/end snapshots HEAD `9d580cb` / tree `324b2480` + exact human3):
  **28/31 native 0, overall exit 1 — FAILED**. Failures, all exclusively untracked human
  `.codex/` files (human files untouched):
  - CMD 21 `pnpm lint` exit 2: ESLint 10.8.1 `ERR_MODULE_NOT_FOUND` — cannot find package
    `eslint-config-next` imported from the untracked human
    `.codex/plugins/cache/.../vinext-starter/eslint.config.mjs` (known user-cache config
    traversal; zero repo files implicated).
  - CMD 29 `python tools/check_repository.py` exit 1: 4 trailing-whitespace errors, all in
    untracked `.codex/packages/.../voice/licenses/*.txt`.
  - CMD 31 `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` exit 1: all 2587 issues across
    397 files under `.codex/`; 0 issues in repo files.
  - CMD 06 unit: 867 passed, 3 warnings, 34.60s.
  This original run REMAINS FAILED; it is preserved and never aggregated with the clean
  runs below.
- Clean-archive focused remediation (NOT a full run; root classification): `git archive
  9d580cb` -> `/tmp/oap-083-6-a/i9d58-clean` + actual `pnpm install --frozen-lockfile`
  (native 0); CMD 29 PASS 0, CMD 31 550 files / 0 issues / 0, CMD 21 0 (evidence
  `i9d58-clean/clean-cmds.log`). This proves the committed tree clean on the three failed
  commands only.
- Fresh CLEAN ISOLATED WORKTREE complete ALL31 (root decision
  `083-6a-ALL31-clean-worktree-verification-decision`): `git worktree add --detach
  /tmp/oap-083-6-a/i9d58-worktree 9d580cb` (status EMPTY — no human3 at all), frozen setup
  inside the literal sequence, 23:27:57.858085Z .. 23:33:49.580321Z: **ALL 31 native 0,
  ALL31_OVERALL_EXIT=0**; CMD 06 867 passed, 3 warnings, 34.60s; start/end HEAD/tree with
  empty status. QUALIFIED at I (root receipt
  `/tmp/oap-083-6-a/strategic-clean-I9d580-ALL31-independent-review.json`). Human files
  unchanged.

### 10.2 Two FULL focused parity runs at I (serial, unique evidence)

- Harness: `/tmp/oap-083-6-a/r5-trial.sh` (f1/f2 cases added; refuses existing attempt
  log/sidecar; full unfiltered git status at start AND end; sidecar written AFTER the log
  finalizes; the f1/f2 driver start variables are captured at LAUNCH — the earlier
  trial1/2 sidecar `head_start`-recomputed-end caveat (section 7) applies to the old
  sidecars only, and the independent RAW START/END snapshots control in all cases).
- f1 (`r5-trialf1.log`, 14423B, SHA-256
  `6b08778d19bf2695db8c47dcf309082f70af437ca953ed7d8d700dfc3961566f`; 23:36:01Z ..
  23:39:19Z): fixture seed native 0 (EXACT smoke.sh 217..239 contract on a fresh DB),
  setup+governance native 0, **PARITY_NATIVE_EXIT=0**, final stage
  `frozen-review-parity-six-stable-pairings` elapsed 120705ms; start/end HEAD/tree
  `9d580cb`/`324b2480`, source clean excluding human3 at both ends; output dir
  `/tmp/r5o.tUGLHv` preserved.
- f2 (`r5-trialf2.log`, 14423B, SHA-256
  `e55abd1e0a46784424ad81c8103dfadffa2415caf11814c07e2f21e1af09c10d`; 23:39:42Z ..
  23:43:02Z): same prerequisites native 0, **PARITY_NATIVE_EXIT=0**, final stage elapsed
  123538ms; same provenance shape; output dir `/tmp/r5o.Q4p0ox` preserved.
- Both are FINAL-I trials of the exact order command
  `pnpm exec playwright test tests/e2e/frozen-review-parity.spec.ts --no-deps
  --project=freeze-review-snapshot`; image provenance as in section 7 (cached subject
  proven, not built at I; `tests/e2e` in no image COPY).

### 10.3 WHOLE 0835 — FAILED (failure index; preserved; no retry)

- Gate: literal `sh tools/compose/smoke.sh slaif0835` via
  `/tmp/oap-083-6-a/whole-run.sh` (refuses existing log/sidecar; immediate native child
  exit; start/end provenance). Window 23:43:45Z .. 23:47:17Z; **WHOLE_NATIVE_EXIT=1**;
  log 42439B / 918 lines, SHA-256
  `7cdf1c5bf11493d095f11f8563dbe4940a580c4969b756fd83ee3a82930bc2d8`; sidecar
  `whole-0835-final-I9d58.sidecar.json`; start/end snapshots HEAD/tree + clean excluding
  human3.
- Passed phases before the failure: compose-policy OK; membership-fixtures OK
  (count=2 kind=OIDC authenticatable=no, strict uninitialized precondition);
  compose-mode-policy OK; review-worker-media-boundary OK; browser-worker-runtime-policy
  OK; browser-worker-image-policy OK (product worker: playwright 1.62.1, CfT 156.0.8078.47
  rev 1706539, chromium-only, package-manager absent — a separate confined service, NOT
  the e2e browser); browser-e2e PASSED project=setup
  contract=setup-desktop-phone-and-initialize; browser-e2e PASSED project=governance
  contract=governance-visible-workflows-negatives-and-privacy.
- FAILURE: browser-e2e FAILED project=governance
  contract=puck-editor-round-trip-through-human-editor-api stage=unknown line=810
  column=34: `expect(locator('.puck-trusted-component')).toHaveCount(2)` — Expected 2,
  Received 5, 8000ms expect timeout. `compose-e2e: FAILED stage=browser
  reason=setup-governance-contract`; `set -eu` abort; ALL later projects (preview,
  preview-filtering, auth matrix x6, agent x2, media-publication, agent-workspace-puck x2,
  review-surface, freeze-review-snapshot, accept-lifecycle, discard-lifecycle, packaging)
  NOT RUN in this attempt — no later parity/full/security/recovery/packaging pass exists.
- Source-backed index (read-only; no new runtime after the failure): the test
  (`tests/e2e/governance.spec.ts:430`) drags `drawer-item:Section` onto the root drop zone
  via `pointerDragUntil` (lines 690..724) — up to FOUR full side-effectful pointer
  gestures, with the ready predicate (count===2) checked ONLY after the fixed
  100/150/300ms post-gesture waits; the failing assertion is line 810. Expected 2 /
  Received 5 is consistent with over-adding across the side-effectful gestures; the
  per-gesture mechanism (duplicate insertion vs delayed insertions crossing the check
  boundary) is UNKNOWN — not established, and the unsafe repeated-gesture helper is a
  source-backed HYPOTHESIS, not established runtime causation.
- Attribution and environment facts: the f35->I9d diff does not touch the governance
  spec, Puck editor, or render/editor APIs; the same contract PASSED in post-merge CI at
  f35 (job 121282677173, 20:33:46.762Z). A past PASS alone cannot exclude a latent
  defect, and an environmental explanation is not established either — cause UNKNOWN, no
  flake/infrastructure label. Browser parity for the e2e phase is known: host-side
  `pnpm exec playwright test` (tools/compose/e2e.sh:38) with pinned Playwright 1.62.1 ->
  chromium revision 1234 (CFT 151.0.7922.34), the same pinned build CI installed.
- Post-failure: the owned stack was removed by smoke.sh's `trap cleanup EXIT`
  (line 175) — no post-failure stack/DB state exists. The over-added components were
  client-side Puck in-memory state; the failure precedes the test's next explicit
  composition save (proved for this test), while the universal "never persisted" claim is
  NOT independently proved and is NOT asserted.

### 10.4 Current-S CI — actually observed only

- After pushing I `9d580cb`, GitHub runs 40247213657 / 40247213688 started. As actually
  observed at the last check (2026-10-26, ~00:05Z): PASS (12) — Markdown, Mermaid,
  Repository policy, Dependency review, Detect supported languages, Analyze (actions),
  Analyze (javascript-typescript), Analyze (python), CodeQL aggregate, Python 3.12 / 3.13 /
  3.14 quality and package. PENDING (11) — Compose and edge packaging, Node contracts,
  Supply-chain evidence, Foundation PG Group A PG14/15/16/17/18, Foundation PG Group B
  PG14/15/16/17/18.
- At the instant this S report is published, the S checks are honestly PENDING; per the
  order, the report is NEVER amended after S to fill future-S results, and no CI rerun or
  retry of any unchanged head was performed.

## 11. Outer teardown primary-error-preservation finding — UNFIXED at I

- Location: `tests/e2e/frozen-review-parity.spec.ts` lines 1792
  (`let bodyCompleted = false;`), 3023 (`bodyCompleted = true;`), 3024..3027 (outer
  `finally`): line 3025 `if (bodyCompleted) stage("cleanup", { action: "close" });` and
  line 3026 `for (const browser of Object.values(browsers)) await browser.close();`.
- Root requirement (adjudicated; the current I does NOT implement it): the outer teardown
  must (a) preserve the FIRST body exception — including an arbitrary captured value — as
  the reported failure; (b) attempt EVERY browser close even after one close rejects;
  (c) retain a failure when the body passed but a cleanup close failed; (d) preserve the
  real failed-stage marker; and (e) avoid raw cleanup-error leakage (no raw
  message/cause/call-log text). The pinned core (coreBundle ~62350..70) suppresses only
  `TargetClosedError` on close, so any other close rejection today would replace the
  body's primary error and abort the remaining closes (leak). The pairing-level
  `failureCaptured` flag (section 4) does NOT protect this outer finally. The
  `stage("cleanup")` annotation does not preserve exceptions.
- This is an existing R2 diagnostic error-path requirement, NOT an observed close failure
  in any executed trial and NOT a claim about the original 600s cause. It remains UNFIXED
  at I `9d580cb`; per root, the fix (within the already-named parity TS; forecast +15..35
  lines, test gross <= 403 < 500) is governed prospectively in the NEXT round on this same
  PR (AMEND_EXISTING_PR), together with a bounded evidence-led governance drag diagnosis.
  No production path expansion is authorized.

## 12. Historical carry scopes (exact named-path evidence only)

- The 083-5-e qualified gates at I24a — FULL unfiltered G2 (347/347 unique PASSED,
  3688.19s, G2_CHILD_EXIT=0) with coherent RC7 (retained-v2-FIRST plus separate v1-only,
  both PASSED within that full run), generated Agent OpenAPI zero-diff, and fresh local
  ALL6 six-image — are carried into this increment ONLY by exact named-path/mode/blob
  equivalence between `f35ec753` and `9d580cb` (the only differences are the parity spec,
  the two docs, and order/active). They are NOT new executions at I9d and NOT new
  security/browser/CI evidence for this round.
- PR #107 (083/5) merged into main at `f35ec753` on 2026-10-25T20:30:05Z; remote main
  independently re-verified before this round's push.
- Current-S CI checks and scans: pending or actually observed only (section 10.4).

## 13. Footprint, budget, transcript identities (actual, measured)

- Measured with `git diff --minimal` on `f35ec753..9d580cb` (exact allowed paths;
  immutable transcript):
  - Test paths: `tests/e2e/frozen-review-parity.spec.ts` 368 lines (345/23) — the ONLY
    test path; `tests/e2e/reporter.mjs` unchanged. Test gross **368 <= 500** cap.
  - Docs: `docs/TESTING.md` (45/0) + `oap/MVP-PROGRESS.md` (2/2) — docs gross **49 <=
    100** cap.
  - Production: **0** lines, 0 paths.
  - Transcript: order (298 lines) + `oap/active` (8 bytes) committed byte-exact in
    `2f4b482`; this report at S (sole path).
- No new file, new test identity, new dependency, new pin, new workflow, or new scope
  exists in this round. Any future scope/letter/roadmap belongs to root.

## 14. Owned runtime state at publication

- No live owned 083-6-a processes or pipelines at publication: ALL31 runners terminal,
  transport suite terminal (browsers closed), focused trials terminal, and the owned
  `slaif0835` stack torn down (smoke.sh EXIT trap after the WHOLE failure). No owned
  compose project is live.
- A foreign, non-interfering process observed during the round — pytest PIDs
  121033/121034 in `/home/janezp/codex-work/slaif-local-coding` (tmux pane %19, started
  2026-10-25T22:46:53Z, separate session/venv/directory) — was recorded with exact
  PID/time/cwd and NEVER touched; it was absent at publication time. No further runtime
  inventory or foreign-container probing was performed (per root).

## 15. Strongest reason not to merge

1. The fresh literal WHOLE 0835 at I FAILED (governance Puck drag over-adding, expected 2
   received 5, mechanism UNKNOWN); every later WHOLE project is NOT RUN, so the real
   product browser/security/recovery/packaging gates have NO pass at I.
2. The outer teardown primary-error-preservation requirement (section 11) is UNFIXED at
   I — the R2 diagnostic error-path contract is incomplete.
3. The original post-merge 600s CI stall remains UNKNOWN/unreproduced; nothing in this
   round establishes its cause.
4. Current-S CI is pending; no final-S green table exists at publication.
5. The full remaining product/foundation/U/audit/closure/re-review/MVP/operations/
   recovery/release criteria remain incomplete (section 17).

## 16. Confirmations

- CREATED_NEW_PR: exactly ONE new PR (#110) for 083/6 from verified remote main
  `f35ec753`; merged PR #107 never touched; no duplicate PR; no merge, auto-merge,
  settings change, or self-acceptance; root alone accepts/merges.
- Scope: zero production paths; the only source delta is the named parity spec + two
  named docs + order/active; no workflow/lock/pin/config/CI change; no selector,
  assertion, or product edit of any out-of-map file; the failed WHOLE contract and the
  outer teardown were NOT edited this round.
- Secrets: the private 0600 secret channel was constructed exactly as
  `tools/compose/e2e.sh` does (setup token from bootstrap logs; fake fixture
  credentials); no setup token, cookie, capability, DB URL, source/preview credential, or
  private artifact URL appears in this report or in any preserved log; the bash-x trace
  privacy rule (0600, outside git, never published) was honored.
- No skip/pending/missing/blocked/not-run is claimed as pass: explicit NOT RUN (later
  WHOLE projects; current-S CI pending); explicit FAILED preserved (working-tree ALL31
  21/29/31; WHOLE 0835; R6 v1 zero-op preflight; R6 attempt2 prep-run1; R6 attempt2 suite
  verdict FAIL); explicit UNKNOWN preserved (original 600s cause; Puck over-adding
  mechanism; why two invalid iframe POSTs occurred).
- Order/active bytes unchanged since `2f4b482`; the single control OK consumed once, no
  control replay; no early response ACK at any point; the exact 2-byte `OK` response is
  sent ONLY after this S is pushed and remotely verified.
- Publication protocol note (honest): the complete report draft was first created
  directly at the formal path `oap/reports/083-6-a-restore-frozen-review-controls.md` as
  a working file (284 lines) before publication; this was detected before any publication
  or OK, and the incomplete bytes were moved byte-exact to a private scratch draft
  (`/tmp/oap-083-6-a/report-draft-v1.md`, SHA-256
  `fca23785012c3021ca59a80dd2cd325161794b2c2f7d4514aa47348b22359d27`). That partial file
  creation is NOT, and is never claimed to be, an atomic publication: no OK had been sent
  and no immutable report existed until this S. The actual publication is a single atomic
  operation: the complete draft linted to 0 under the repository's exact markdownlint
  config, written to a same-filesystem temp file, closed and fsynced, then renamed once
  to the final path.
- No CI rerun of any unchanged head; no silent repair of out-of-map failures; no
  repeat-until-green anywhere in the round.

## 17. Limitations, blockers, remaining criteria

- This round is a PARTIAL execution handoff at literal I `9d580cb` — not acceptance,
  abandonment, or product completion.
- Remaining within 083 (governed by root, next round AMEND on PR #110): (a) outer
  teardown primary-error-preservation fix within the parity TS (forecast +15..35 lines;
  test gross <= 403 < 500; no new file); (b) bounded evidence-led governance
  `puck-editor-round-trip-through-human-editor-api` drag diagnosis/repair, including any
  exact additional test identity, complete cumulative gross forecast, and fresh
  final-source gates (clean-worktree ALL31, two focused parity, literal WHOLE, current-S
  CI all checks).
- The full remaining product / foundation / U / audit / closure / re-review / MVP /
  operations / recovery / release criteria remain incomplete; no completion claim is made
  for any of them. The old public-API qualification draft (083/6 candidate) remains INERT
  and deferred per root; no next increment ID is chosen by the coding agent.
- Known scratch artifacts (all private, outside git, hashes recorded in sections 3-10 and
  in `/tmp/oap-083-6-a/`): r5 harness/logs/sidecars, transport-suite v1/attempt2/attempt3
  (with preservation hash files), all31 attempt dirs (working-tree FAILED + clean
  QUALIFIED), i9d58-clean archive, i9d58-worktree, WHOLE log/sidecar, statics,
  failure-index/forecast documents, and the report draft version.
