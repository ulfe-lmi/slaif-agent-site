# OAP Coding-Agent Report — 083-8-c

## Work order

- Identifier: 083-8-c (objective 083, increment 8); work-order file
  `oap/orders/083-8-c-repair-diagnostic-controller-plumbing.md` (250L,
  16464B, SHA256
  352488a2006a78a46d570d13c0b1889c71bfa03add3dfc3ee2a4319dadb9d169),
  FULL-read including the exact report-handoff section. Line 16 of the
  order file contains a literal `\n` backslash-n formatting sequence
  (drafting artifact); every clause was read as-is and the immutable
  order was not edited.
- Activated `oap/active`: 8 bytes, hex 3038332d382d630a ("083-8-c" +
  LF), committed unchanged at Ic.
- PR mode: AMENDED_EXISTING_PR (PR 112, same named branch).
- Mode: DIAGNOSTIC_ONLY_PUBLIC_P6_CONTROLLER_REPAIR. The original
  increment remains PARTIAL/unaccepted; as in b, no production or
  qualification-test repair is authorized or performed in this round.
- Control sync: root wrote exact 2 bytes 4f4b, no LF, closed, to the
  ACTUAL strategic control.fifo (inode 4470111) at
  2026-10-27T10:52:17.183522Z (control-written.json, pid 2167937). My
  existing reader session 18377 ended TERMINAL1 with empty output
  because a shell `read` without LF returns 1 at EOF and the `&&` chain
  suppressed display: a documented byte-observation limitation of that
  reader, not a lost signal. Root's write receipt, the activated order,
  and the order content reconcile (strategic-c-control-reader-shell-
  EOF-reconciliation.json). No replay, no new control reader. The sole
  root response reader for this round is 27620 (pending).

## Status

PARTIAL — the approved diagnostic cohort produced the increment's
FIRST actual P6 data: attempt 1 (direct-driver control) actually ran
and completed (child native 0, NO_REPRODUCTION), and attempt 2 (SDK
path) actually ran and reproduced the stall (child native 5, codes
[5,7], plus the arm's own fixture pool.close 30s timeout marked
DIAG_UNSAFE_CLEANUP). Attempts 3 and 4 (SDK) were PREVENTED by the
controller fail-stop and are NOT RUN. The original I3 P6 safety
contract failure remains unresolved and qualification is not met; all
original a final gates (20 strict required checks, 10 actual PG
children, strategic satisfaction, fresh FULL PG18, P7) remain
outstanding. Per the root close decision: NO third launch, NO source
fix, NO new gate, NO workaround.

## Executive summary

Phase A repaired the b harness defect (the undefined `arm` name at
frozen b controller line 783) with a 2-line arm binding plus literal
Ic subject guards and identity updates; the frozen five-file c bundle
(diagnostics 995 + harness 1195, TOTAL runtime inputs 2190) was
root-FULL-reviewed, and the required historical F821 baseline on the
frozen b controller failed with native 1 at exactly 783:63
("F821 Undefined name `arm`") — the b defect is now statically
proven, while all four corrected c Python inputs pass F821, target
3.13.14 py_compile, and sh/dash -n with native 0.

Phase B ran the root-approved single launcher invocation at
11:12:57.043Z (root-observed) at Ic. Preflight PASSED at Ic. The
direct-driver control case ran to completion (native 0, no
reproduction). The SDK case reproduced the P6 stall on local PG16.15:
the public reviewer manager's post-termination restoration entry
missed the original 30s deadline at t_mono 32.91, and the PRE-CANCEL
observation caught the suspended owned task at the manager's
acquisition expression — async generator `asyncpg_cow_reviewer`,
safe_promotion.py line 483, awaiting an opaque coroutine wrapper —
with pool public state size=0/idle=0/closing=false, the pool
connection proxy closed, an empty listener event list, and no owned
role backend rows or locks. The fixture then failed its own
reviewer-pool close (30s TimeoutError, frozen module line 613), which
the controller marked DIAG_UNSAFE_CLEANUP and stopped the schedule:
attempts 3-4 PREVENTED. The asyncpg-internal reason for the stall
remains UNKNOWN; the driver arm's non-reproduction is a structural
contrast (that arm has no SDK/COW/reviewer/commit_session) and is not
causal proof. Controller-owned disposal was SAFE and in budget for
BOTH attempts (all commands native 0, absence proven); the unsafe
marker is the arm's own fixture cleanup failure, distinct from
controller disposal. Live CI at Ic: 23 success / 7 failure / 0
pending, the two actual engine failures being Group B PG14 and PG15
(same P6 signature); the five Foundation PostgreSQL 14..18 jobs are
the documented fail-closed aggregators.

## Authoritative GitHub state

- Repository: ulfe-lmi/slaif-agent-site; PR 112
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/112>, state OPEN,
  unmerged (merge performed NO by coding); mergeStateStatus BLOCKED at
  report drafting (required checks failing).
- Base branch main; verified remote main
  d18b6e4c9423f61de99b516be90619bf2ab5d3e0 (PR #111 merge, 083-7-b).
- Head branch oap/083-8-a-qualify-public-whole-session.
- Implementation head SHA: f3b266e9f0c4adc6771111d1584375dc6ade68fb
  (Ic; tree e54f2303066bddda7ec68bd205b72fa1a336fd91); pushed.
  Push receipt honesty: the Ic push was executed through a pipeline
  whose native was NOT captured (PIPESTATUS not retained), so the
  ACTUAL push pipeline status is UNKNOWN. A subsequent `git
  rev-parse Ic` returned 128 ("unknown revision") because "Ic" is a
  scratch label, not a repository ref (reproduced at report drafting,
  RC=128). Independent remote proof succeeded in both directions
  (root strategic-Ic-remote-scope-review.json at 10:58:35Z and a full
  `git ls-remote origin` re-verification at drafting: remote branch
  head = f3b266e9...). No push was repeated to obtain a prettier
  receipt.
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified: remote
  branch head == S_c, sole parent Ic, sole path this report; S_c
  derived via GitHub after push)
- Append-only history since accepted main: the a implementation
  commits are recorded in the immutable a-report. c adds exactly two
  commits: Ic f3b266e9f0c4adc6771111d1584375dc6ade68fb (c-order 250
  insertions + active 1+/1-, sole parent S_b
  3c876d92bc9e8033fd8d59681378145851f491b7) and S_c (this report, sole
  parent Ic, sole path the c-report). No amend/reset/rebase/force-push.
- New PR this turn: no. Amended existing PR: yes (report only).
  Merge performed: NO.

## Changes made

- ZERO product, test, CI, docs, lock, migration, dependency, image, or
  behavior changes in this round. The only new committed c path is
  this report (the S_c commit); the c-order and active are already
  committed/pushed at Ic.
- Uniform minimal accounting (git numstat = CHANGED LINES): at Ic the
  PR touches 14 paths — code 1896 (ci.yml 10 + module 1844 +
  test_foundation_ci.py 42), docs 154 (docs/ 145,
  oap/INCREMENTS.md 5, oap/MVP-PROGRESS.md 4), transcript 2204 (active
  2, a-order 470, b-order 257, c-order 250, a-report 627, b-report
  598). This S_c
  commit adds the c-report, bringing the cumulative total to 15 paths
  and transcript 2204 + (c-report lines) — exactly the order's
  "cumulative 15 paths after c-report".
- All a code/CI/docs delta paths are BYTE/MODE/TYPE unchanged at Ic
  (root-verified complete leaf mode/type/blob maps S_b->Ic; the frozen
  P6 module equals I3 bytes
  45cf79671261212c19143315daeaecfc1b01b1e48d0b3c2cdf9e85cf881563a8 at
  every head since I3).

## Subject preparation (order section, completed FIRST)

- Ic committed/pushed on the existing branch before any final review
  or runtime: c-order + active only (numstat 250 + 1/1). Remote
  expected baseline S_b and unique PR 112 reconciled; root
  independently verified remote Ic (sole parent S_b, only c-order +
  active differ; 1121 old leaves exact; remote order/active bytes
  equal local) — strategic-Ic-remote-scope-review.json.
- The existing clean isolated gate-wt
  /tmp/oap-083-8-a/gate-wt was prepared to EXACT Ic
  (f3b266e9f0c4adc6771111d1584375dc6ade68fb / tree
  e54f2303066bddda7ec68bd205b72fa1a336fd91) with full raw status EMPTY
  (0 lines; raw 0-byte file retained), module 1844L / 45cf7967...
  unchanged, venv CPython 3.13.14 intact (final-source-environment-
  record.txt). No force/reset/clean/rebase/amend; venv, human3 and
  local changes preserved.
- Controller subject guard updated to literal Ic/tree constants at
  BOTH check sites (preflight line 528, END source guard line 1049).
- Complete leaf mode/type/blob maps S_b (1122 leaves) -> Ic (1123
  leaves): ONLY oap/active (blob swap) and the new c-order differ; all
  1121 other old leaves exact (leafmap-Sb.txt / leafmap-Ic.txt).
- Root independently checked the subject/environment BEFORE approval
  (strategic-c-final-source-environment-review.json at 11:10:36Z):
  full 5-file hashes, gate status empty, original full status only
  exact human3 (132624B, SHA256
  2822a3ec6f3a154f091df6d42d681620f4273cc6bec563c1a2241f97f3a64eb8),
  main d18, live PR OPEN/head Ic.

## Phase A: repaired frozen diagnostic bundle

- Frozen five-file scratch bundle in /tmp/oap-083-8-c (outside Git),
  re-verified byte-identical at report drafting:

| file | lines | SHA256 |
| --- | --- | --- |
| p6diag-common.py | 325 | 58c8c207ff045e122c61283169d65658b7fdc59f0c1f707fa2a6bbeef50f439d |
| p6diag-driver-arm.py | 263 | 13e8b238c8ea4e6e107de294c36687a7c79dfa52539683fba34e9b7c8949b35f |
| p6diag-sdk-arm.py | 407 | d18464d178b31eff769ce97d3670f3a9256de836af5a8f7dd84d04cebbf6ac29 |
| p6diag-controller.py | 1189 | 2ac099650ae7aec8269f86fcc9b539bb2dc0e6948ed18720cde0000cd7b64062 |
| p6diag-launch.sh | 6 | 2b0e10b89fb195f5d3b37016b1764a60b210cf5c0ce2075f2009a69e4a438740 |

- Line accounting (no packing): diagnostics common+driver+SDK = 995
  within the prospective 1000; harness controller 1189 + launcher 6 =
  1195 within the prospective 1250; TOTAL runtime inputs 2190.
- b->c delta (fully enumerated in c-bundle-b-to-c-changed-lines.txt):
  exactly 76 changed non-blank lines; the complete scratch gross
  delta measured by numstat is 77 (76 + one blank line; per-file gross
  common 2 / driver 4 / sdk 4 / controller 63 / launcher 4). The
  changes are: (1) the arm bound explicitly into attempt_body —
  signature line 669, sole caller line 614, argv interpolation line
  802 (case 1 -> p6diag-driver-arm.py; cases 2..4 ->
  p6diag-sdk-arm.py); (2) subject guard constants Ic/tree at both
  sites; (3) SCRATCH=/tmp/oap-083-8-c, VOL_LABEL=oap0838c.rid, 0838c-
  volume/container/runner prefixes, launcher path; (4) arm
  P6DIAG_SCRATCH fallback defaults; (5) four MANIFEST hashes updated
  to the actual c bytes (root caught the stale b hashes before final
  freeze; corrected at 2ac09965 — no runtime impact). No other
  behavior change; the reviewed b stop/deadline/ownership/native/
  evidence law is preserved, and the known F1/F2 fail-stop
  limitations remain (no rewrite).
- Review history: root FULL-read the controller bases and every c
  delta (strategic-c-first-WIP-source-review.json, strategic-c-
  manifest-and-statics-review.json, strategic-c-final-source-
  environment-review.json); the final 1189L 2ac09965 controller is
  the approved and frozen version.

## Statics and statics disclosure

- PASS 1 (SUPERSEDED, procedural deviation) at 11:04:42Z piped the
  ruff baseline through tee; the echoed "BASELINE_NATIVE=0" was TEE's
  native, not ruff's (ruff child native UNKNOWN), and pass 1 also
  duplicated the supplementary b-arm check and its on-disk logs were
  overwritten by pass 2. Preserved in statics-procedure-disclosure.txt
  as a deviation record; NOT re-run again.
- PASS 2 (VALID, authoritative) at 11:05:28.698..11:05:28.855Z, each
  command directly redirected, immediate native captured:
  - REQUIRED historical baseline, frozen b controller (b bytes
    unchanged, approved hashes re-verified after the run):
    `ruff check --select F821 --no-cache --output-format=concise
    /tmp/oap-083-8-b/p6diag-controller.py` -> NATIVE 1, exactly one
    finding: `p6diag-controller.py:783:63: F821 Undefined name
    arm` (the b defect, now statically proven; log retained).
  - Supplementary read-only, 3 frozen b arm files -> native 0.
  - FINAL c check, all 4 c runtime Python inputs -> native 0, zero
    undefined-name issues.
  - TARGET 3.13.14 py_compile, all 4 c Python files (gate-wt venv)
    -> native 0.
  - Launcher syntax: sh -n native 0; dash -n native 0 (both resolve
    to /usr/bin/dash on this host).
  - Natives ledger (statics-natives.txt):
    BASELINE_b_controller_native=1, BASELINE_b_arms_native=0,
    FINAL_c_all4_native=0, TARGET_py_compile_c_all4_native=0,
    LAUNCHER_sh-n_native=0, LAUNCHER_dash-n_native=0.
- Tools: ruff 0.16.3 (locked uv 0.12.5 project venv
  /tmp/oap-083-8-a/gate-wt/.venv/bin/ruff); target python CPython
  3.13.14; host python 3.14.4 ran the controller at runtime (as in b)
  and is recorded separately, never substituted for target.
- AST/syntax/lint is NOT execution qualification. The undefined name
  was invisible to py_compile and to prior source review, but NOT
  invisible to static analysis: the F821 baseline above is the new
  proof (truth correction 4 below).

## Diagnostic execution record (ONE approved invocation)

- Root execution approval 2026-10-27T11:11:58.230446Z (strategic-c-
  one-cohort-execution-approval.md): exactly ONE invocation
  `sh /tmp/oap-083-8-c/p6diag-launch.sh`, no pipe; fixed cohort
  SERIAL owned PG16: 1 direct-driver control THEN 3 SDK-path cases,
  fresh owned fixture each, 180s EACH including lifecycle/
  observations/cleanup, original 30s entry/drain/close, aux <=5s,
  reserve 30 INSIDE 180; ANY unsafe/setup/evidence/unknown STOP; no
  fifth case, variant, or relaunch.
- Deviation (disclosed, receipt run1-exec-wrapper-receipt.txt): the
  approved launcher was executed through an 11-line `sh` wrapper
  run1-exec.sh (SHA256
  73e1584e1e6675d2c62f9269c2dbf3b3807ccdea47c3836a82f7f2cf56420695)
  that captures the immediate launcher native into a file. The wrapper
  was added AFTER the submitted five-file manifest and is NOT part of
  the root-reviewed bundle: TOTAL harness is therefore 1206/1250
  (1195 + 11) and total runtime inputs 2201. The wrapper header
  comment "this sh's exit IS the launcher/controller native" is
  FALSE: the wrapper's final command is `date`, so the wrapper's own
  outer exit is date's rc (0). The launcher native was captured
  separately and correctly by the immediate `rc=$?` right after
  `sh p6diag-launch.sh` (run1-launch-native.txt:
  LAUNCHER_NATIVE_EXIT=1). The wrapper outer 0 never substitutes for
  the launcher native. No edit, no relaunch.
- Invocation chronology (all UTC; file mtimes at nanosecond
  precision): root observed the launch at 11:12:57.043Z; wrapper
  created 11:12:57.069632760Z; pre-date write 11:12:57.079632535Z;
  controller 11:12:57.160..11:14:08.362 (own log); launcher native
  write 11:14:08.381034273Z (value 1); end-date write
  11:14:08.386034161Z. The wrapper's RECORDED date strings
  ("2026-10-27T11:12:57.79793546Z" / "2026-10-27T11:14:08.385865518Z")
  have corrupted sub-second fields (8/9-digit fractions) because
  %6N is mishandled by this host's date; their seconds fields are
  correct and the strings are preserved as-is. The controller log and
  the file mtimes are the authoritative chronology. The launcher is
  exec-only (native launcher = native controller);
  LAUNCHER_NATIVE_EXIT=1 reflects the controller OVERALL=1.
- Preflight PASSED at Ic (preflight-raw-receipts.log): gate-wt raw
  status empty, HEAD/tree exact Ic, no 0838c- named containers, image
  IDs postgres:16-alpine sha256:0cefaabd882e42bcb2a2f3dc56d3ce477056
  0ba62fd7f197f1a2e008fd5731ab and python:3.13-slim
  sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a56
  78c2f; `PREFLIGHT_OK=True`.

### Attempt 1 (arm=driver) — actual case 1, child native 0

- Owned fixture (11:12:57.362..01.188Z): labeled volume
  0838c-20261027T111257Z-2180425-pg1 (label oap0838c.rid=
  20261027T111257Z-2180425) created native 0; PG16 container
  422604687de3880684d62c0d4721f14ecffc363b7dfd2ccf213036907f179720
  created native 0, running, image equality verified; pg_isready rc=2
  probes 0..6 then rc=0 at probe 7; identity version=16.15
  db=postgres user=postgres port=5432; system_identifier
  7701304045290938408; runner container
  a9a06c4005dfdd1935b7cd7c81c670c15df16373f9ec2acb72e9885073164d96,
  network `container:<PG-cid>` verified equal, one-shot state
  checked honestly.
- Case (raw runner stream, t_mono 0.045..0.109s): structural label
  "no SDK/no COW/no reviewer manager/no commit_session", max_size 1;
  probe table created (autocommit); window-open backend pid 122;
  in-window observation "idle in transaction", 4 locks; owned pid 122
  terminated; expected driver exceptions — dead-checkout
  ConnectionDoesNotExistError "connection was closed in the middle of
  operation" (sqlstate 08003 from asyncpg .sqlstate) and unwind
  InterfaceError "cannot call Transaction.rollback(): the underlying
  connection is closed" (client-side, sqlstate absent); dead checkout
  released ok; recovery: new backend pid 124, probe_count 0 (the
  uncommitted probe row is ABSENT after backend termination +
  rollback); recovered checkout released ok; probe table dropped;
  public pool close ok. Outcome NO_REPRODUCTION, codes [], exit 0.
- Controller: child_exit=0, wait_cli=0 (docker wait stdout "0"),
  terminal status exited/exit 0, cleanup_safe=True, in_budget=True,
  body_exception=False, unsafe_marker=False, pg_evidence=ok,
  mount_evidence=proven, continue=True. Raw BOTH streams + Mounts
  rescued BEFORE deletion; volume labels + Mountpoint before volume
  deletion; stop/rm/volume-rm all native 0 with ABSENCE PROVEN.
- Interpretation: this arm has no SDK/COW/reviewer/commit_session;
  its clean recovery is a structural contrast. It is NOT causal proof
  about the SDK, and non-reproduction does NOT cure the known I3/Ib
  failures.

### Attempt 2 (arm=sdk) — actual case 2, child native 5, STALL_REPRODUCED

- Owned fixture (11:13:01.188..08.344Z): labeled volume
  0838c-20261027T111257Z-2180425-pg2 (same label value) created
  native 0; PG16 container
  5d13956c19d79b8ef406fa49c64501a5a4443cfe7982d59e5f7e26c095ee98b2
  created native 0, running, image equality verified; pg_isready rc=2
  probes 0..6 then rc=0 at probe 7; identity version=16.15
  db=postgres user=postgres port=5432; system_identifier
  7701304061626810408; runner container
  d6e3cbfd5917e37f4339e49ed89a2667c9f4226964482136db6f12c24688102e,
  network `container:<PG-cid>` verified equal.
- Setup (raw runner stream): fixture-ready schema
  qw8_2d77be7f9c45, reviewer role qw8_reviewer_2d77be7f9c45
  (t_mono 2.681); server-identity matches (sysid
  7701304061626810408); public post-promotion window-open backend
  pid 125 (t_mono 2.849); in-window observation "idle in
  transaction", 71 locks.
- Termination and expected error: owned pid 125 terminated
  (t_mono 2.877); the arm's driver-exception is InterfaceError
  "cannot call Transaction.rollback(): the underlying connection is
  closed" (client-side, sqlstate absent) — the expected driver
  exception for a dead checkout. Canonical state independently
  re-verified (canonical-restored, t_mono 2.880).
- THE STALL: the public reviewer manager's restoration entry task
  did not complete within the original 30s bounded window; the guard
  deadline fired at t_mono 32.91 (diag-restored-pending-enter-stall).
  PRE-CANCEL observation (captured BEFORE any cancel, no frame
  locals, no credentials):
  - task-state: done=false, cancelled=false (task pending).
  - task-stack: single frame `__aenter__`,
    cpython-3.13.14 contextlib.py line 214 (the stdlib async
    contextmanager machinery).
  - gen-chain: depth 0 async_generator `asyncpg_cow_reviewer` at
    /tmp/oap-083-8-a/gate-wt/.venv/lib/python3.13/site-packages/
    agentcow/postgres/safe_promotion.py line 483, awaiting
    `coroutine_wrapper`; depth 1 terminal await target — the
    coroutine wrapper is opaque to read-only observation (no inner
    coroutine/generator frame reachable).
  - pool-counters: size=0, idle=0, closing=false.
  - conn-state: closed=true, type PoolConnectionProxy (auxiliary
    observation on the owned proxy).
  - listener-state: events=[] (passive only; never waited on).
  - admin-activity (owned admin connection, read-only): role
    qw8_reviewer_2d77be7f9c45 pids [125], rows [] (no backend
    activity), locks {"125": 0}, role_locks 0.
- Exact bounded drain of the SAME owned task: done=true, cancelled=
  true ("task ended cancelled after the deadline"); post-drain
  observations unchanged (pool 0/0/false, proxy closed, listener
  empty, no role rows/locks); canonical absence re-checked after
  drain; reap-terminal for both finally arms (reentry cancelled=true,
  window cancelled=false).
- Fixture cleanup failure (the unsafe marker): the arm's OWN
  fixture teardown then ran its reviewer-pool close and it failed:
  RuntimeError "owned fixture cleanup failed: reviewer-pool:
  pool.close() failed within 30s: TimeoutError" raised at frozen
  module line 613 (t_mono 63.355..63.36, arm sdk-fixture-aclose /
  fixture-aclose). DIAG_UNSAFE_CLEANUP=1 was emitted. Outcome
  STALL_REPRODUCED, codes [5, 7], unsafe_cleanup=true, exit_code 5.
- Controller: child_exit=5, wait_cli=0 (docker wait stdout "5"),
  terminal status exited/exit 5, cleanup_safe=True, in_budget=True,
  body_exception=False, unsafe_marker=True, pg_evidence=ok,
  mount_evidence=proven, continue=False; "ATTEMPT 2: remaining
  attempts PREVENTED"; CONTROLLER_DONE OVERALL=1 EXIT=1.
- Interpretation: the observed await chain localizes the stall to
  the public reviewer manager's ENTRY ACQUISITION expression —
  safe_promotion.py line 483 awaiting pool.acquire inside
  asyncpg_cow_reviewer — with the public pool state facts above. The
  next await target (coroutine_wrapper) is opaque: NO inner
  queue/holder/socket/connect mechanism is observed, and NO causal
  SDK or driver defect is claimed. The asyncpg-internal reason
  remains UNKNOWN. The pool.size=0/idle=0, closed proxy, empty
  listener, and no owned role backend/locks are observations only,
  not explanations.

### Attempts 3 and 4 (arm=sdk) — PREVENTED, NOT RUN

- Stopped by the controller fail-stop at the unsafe marker after
  attempt 2; no fixture, container, volume, or runner was created for
  either. NOT RUN is literal: they produced no data, no exit, no
  observation, and no substitute value was recorded for them.

## Cleanup and residual state (owned only)

- Controller-owned disposal for BOTH attempts was SAFE and within the
  SAME attempt deadlines (cleanup_safe=True, in_budget=True, every
  command native 0): raw BOTH Docker streams + Mounts captured
  BEFORE each container deletion; volume labels + Mountpoint
  captured BEFORE each volume deletion; stop/rm/volume-rm native 0
  each; post-deletion presence checks are successful list reads with
  exact empty results (ABSENCE PROVEN); finalize: "no residual owned/
  attempted resources; no post-deadline recovery performed";
  END_SOURCE_GUARD=ok; EVIDENCE_DEGRADED=False.
- Distinction (honest flag): DIAG_UNSAFE_CLEANUP marks the ARM'S OWN
  fixture teardown failure (reviewer-pool pool.close 30s timeout,
  code 7 within codes [5,7]) — the SDK fixture's cleanup FAILED,
  while all controller-owned resources were cleared and absence-
  proven. On this evidence no residual cleanup action is authorized
  or needed, and none was taken; the marker is presented for root's
  finite decision if it deems one required. The known F1 generic
  open-error label and F2 finalizer-logging fail-stop limits are
  preserved; this report does NOT claim global exception safety or
  unconditional cleanup success.
- Exact-owned residual receipt (11:31:10.610444Z, read-only, run1-
  owned-residual-receipt.txt): no p6diag/run1-exec processes
  (grep RC=1); `docker ps -aq --filter name=0838c-` empty (RC=0);
  `docker volume ls -q --filter name=0838c-` empty (RC=0); full
  mtime chronology recorded.
- The 23 earlier unattributed anonymous volumes (a round) remain
  UNTOUCHED; no global prune, no foreign volume, no foreign PID, no
  foreign DB/role touched; running foreign slaif-* containers never
  touched.

## Evidence inventory

- /tmp/oap-083-8-c/run-20261027T111257Z-2180425/ — all 18 files
  re-verified byte-identical to the root artifact manifest
  (strategic-c-run1-artifact-manifest.json) at report drafting:

| file | bytes | SHA256 |
| --- | --- | --- |
| start.txt | 1816 | 3a627cefa2b73d36d5aecc7b7be0739313a2a52cb59d2de337cf863632cd95ba |
| overall.log | 1518 | f6653a3b4d13c77af5542c50be93fa83308bc06b4585d2ec6ac96ca1f6224975 |
| preflight-raw-receipts.log | 1228 | 43ee5302de74f6548573bfbe4cb29d2e9d7e97423a1ed36f6846e587fdf0cb05 |
| driver-attempt1.log | 7046 | c595d346486e16210b99e74f282aac5952b9419af9de369eab46396ac5ee4e96 |
| driver-attempt1-raw-receipts.log | 11306 | ce08a311dce4a7047c170f47082131c195ccdeb5f4169eaab912fbb58fa59ad9 |
| rescue-driver-attempt1-pg.cli-stdout | 2304 | 0c39093826f820a512183b9e7b38c1b12252dbc3518320b27df21d3fee4c4cd7 |
| rescue-driver-attempt1-pg.cli-stderr | 991 | 85e3e744982022db6585534b4879c58d5eb4320f82b20ccfd2565ba03a2fb552 |
| rescue-driver-attempt1-run.cli-stdout | 3617 | efe492c62e7cfab3e97fea0ba9cff503ad5e33a9b6c1d0b0ad0821200134e306 |
| rescue-driver-attempt1-run.cli-stderr | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| sdk-attempt2.log | 7307 | 9f257d8da30a5d54d9a75ca3b1d49830d3043d117f35dc388fca8a8b23805b69 |
| sdk-attempt2-raw-receipts.log | 11303 | 8e7938c5fc015c4e09c294d6c958892e6502fc9c831adffc7f91ab9a432edf04 |
| rescue-sdk-attempt2-pg.cli-stdout | 2304 | fca988a09b519d58b85a25125f2e8545c115d00dae0ea03c75e44c4f3b765a03 |
| rescue-sdk-attempt2-pg.cli-stderr | 1364 | 28b32486ae978409f08daeacd7585d4627e76ef02160532add4a84d57ff5aedf |
| rescue-sdk-attempt2-run.cli-stdout | 6179 | efd19e598311ad85e0911f0cb2f5068b2461e59ef7c5c40b47c6ea5c98473cc2 |
| rescue-sdk-attempt2-run.cli-stderr | 85 | 2beaee4b8fa7c0554fd70ef7e53ebd0f055850f2bb4bfbdc4c32add74cba4511 |
| end.txt | 879 | adfb53b41f5ffc8dd5a04bfc54c34aedcca2515cab499cbfe7f4dca6c5100870 |
| finalize.log | 464 | 0c2b4335a3a4331a667860860e41f1c8e172ebb198033fa990410986db231057 |
| finalize-raw-receipts.log | 606 | b347148581e7649eed826d1da9e470b5b34986032da987e1c6e0605f4edd970f |

- Launcher-level receipts (wrapper deviation, §Diagnostic execution):
  run1-exec.sh 535B
  73e1584e1e6675d2c62f9269c2dbf3b3807ccdea47c3836a82f7f2cf56420695;
  run1-exec-wrapper-receipt.txt 858B
  1ba0e871feee6bbc3fa3ffc5af5d62f555650832b4612811bae694ef47b12ba1;
  run1-owned-residual-receipt.txt 1057B
  6b1529ffaa83596d6d09099fa021bbc6dd4155eff4a203bfc5f5b7b6eb923e74;
  run1-launch-pre-utc.txt 30B
  a30c76f64b24e1ca3b5cc626749f7d3fd797f7b05010b26c6e49eb6096582a24;
  run1-launch-native.txt 23B
  bfca631886f734ef7b2cac219657feb30bcc14cf9be6659c54de90b8cfa6d624;
  run1-launch-end-utc.txt 31B
  90fa93620916c649d4d6e1cd3efc4c7105d204edb44188cd11692d79a56569c5;
  run1-launch-stdout.log 0B
  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.
- Statics: statics-natives.txt 160B
  1be1040cb45c5af7f4ccd0214336ff17fbb09542b3e9343bed20d41cd14bdbc9;
  statics-procedure-disclosure.txt 3452B
  9ddaf2f81c3dfe4e0cda9bb9f8aeaccc1b09916015adc4859c9a32c781e3627b;
  baseline-F821-b-controller.log 87B
  8557c841b0625c26a51c5d65fbeb8f29e68e3c79e7209bf9698875af68ba85f1;
  baseline-F821-b-arms.log 19B
  82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18;
  final-F821-c-all4.log 19B (same hash as b-arms: "All checks
  passed!"); target-py_compile-c-all4.log, launcher-sh-n.log,
  launcher-dash-n.log all 0B (native 0, no output).
- Subject/scope: leafmap-Sb.txt 118695B
  b9d65dcc8408acacd686fb57c2fc591eed058530e9435982d7c5ed61cab376ad;
  leafmap-Ic.txt 118808B
  bdcb76449c62ee8805593342afcdc4366c2ceaf66aa1c168ea12372b1a549fb0;
  gate-wt-raw-status-Ic.txt 0B (clean); c-bundle-b-to-c-changed-
  lines.txt 6616B 7db4c7dd6e30790e8dd7484909e724b46724b92c658731755a0f
  d0dacddbec7e; final-source-environment-record.txt 789B
  ae866bdc9f993d078e7dd15457e7075683028a55b6ce74598867b6c901a9e036;
  frozen-bundle-manifest.txt 1633B
  87069df2f28a82e43d32f7fe35667a92f6f5c9536c5e94ffc83e5325f428bc2c;
  p6diag-phaseA-forecast.md 5262B
  9dd3cf76d787e00b438206128dbe2e62acf1a6ea6b6c05335725e36c7eefd04c.
- CI raw logs (this round, read-only): strategic-Ic-CI-job-
  122149623100.log (Group B PG14) 150855B
  9e86510a0b271d08105b0ee6845fc75804fb5bee6a3f07765e722f0d071785c8;
  strategic-Ic-CI-job-122149623054.log (Group B PG15) 169702B
  a0266edddf7822384f38c9b43b33ae76d6431cc56a63bac31dcc28c6537c3b6a;
  strategic-Ic-CI-job-<S_b-PG17>.raw peer-ci-Sb-PG17.raw 171243B
  d59982e730c8304c271922f5bec0fc8cf01d963afcb65a009b028cb3e35a02f4
  (S_b, from the order/peer review).
- Root receipts (immutable): strategic-c-one-cohort-execution-
  approval.md/.json (11:11:58.230446Z), strategic-c-final-source-
  environment-review.json (11:10:36.175730Z), strategic-Ic-remote-
  scope-review.json (10:58:35.286155Z), strategic-c-run1-and-close-
  partial-review.json (11:17:19.360446Z), strategic-c-run1-artifact-
  manifest.json, strategic-c-close-partial-report-direction.md
  (11:17:19.360446Z), control-written.json, strategic-c-control-
  reader-shell-EOF-reconciliation.json, strategic-first-c-WIP/
  (WIP snapshots), activation.json, preparation.json.

## Truth corrections (b-report claims corrected here; b never rewritten)

1. D5.4 (a-report supply-chain claim) is NOT supported by ALL31: the
   actual I3 ALL31 CMD3/4 ruff scopes were services/backend
   tests/repository tools, CMD6 pytest unit+repository, and CMD28
   unittest repository. Those do not include the dedicated
   supply-chain test units or the broader CI ruff scopes (tests/
   packaging, tests/supply_chain, migrations). The required
   additional local commands at I3 are NOT INDEXED and NOT RUN; no
   actual source-bound CI receipts for them were indexed in this
   round, so they remain UNVERIFIED. No new local gate was executed
   to fill the old receipt.
2. Host python 3.14.4 executed BOTH b controllers (both b
   invocations) AND the b statics; the target 3.13.14 scripts were
   compiled but no driver/SDK child ran in b. The host was NOT
   statics-only.
3. b added Ib 53895c15d36ef0766cd81a69938d0e20db0aac9a and S_b
   3c876d92bc9e8033fd8d59681378145851f491b7 — not S_a + Ib. S_a
   (e7b15f97fe7fc0b353590012ff956407013ca952) belongs to the a round.
4. The b arm-undefined defect was not caught by prior review or
   py_compile, but it was NOT invisible to static/source analysis:
   the required F821 baseline on the frozen b controller returns
   native 1 at 783:63. The actual F821 result is preserved as the new
   proof (see Statics).
5. There were TWO b controller invocations, ONE fixture-setup slot
   (invocation 2 only), and ZERO driver/SDK cases. The late b-report
   wording "its first and only execution ended in harness failure"
   is corrected: both invocations were not-run as cases, and
   invocation 2 was the only one to reach fixture setup.
6. Publication receipts in this round use actual timezone-aware UTC;
   st_mtime_ns is preserved raw and converted with /1e9 (nanoseconds
   to seconds, e.g. the 11:12:57.069632760Z mtime above). The b
   private helper's invalid "future 58790" mtime string is not
   repeated; the actual tool UTC/lint-before-rename-before-commit
   chronology is authoritative.

## New c errata (recorded here; prior receipts preserved immutable)

1. Statics pass 1 (11:04:42Z) was piped through tee: the echoed
   "BASELINE_NATIVE=0" is TEE's native (ruff child native UNKNOWN),
   the check was duplicated, and pass-1 on-disk logs were overwritten
   by pass 2. Disclosed, preserved, never re-run for a prettier
   receipt (statics-procedure-disclosure.txt).
2. The 11-line run1-exec.sh wrapper (SHA256 73e1584e...) was added
   after the submitted five-file manifest and is not part of it;
   TOTAL harness 1206/1250 (1195+11), total runtime inputs 2201. Its
   header comment equating the wrapper exit with the launcher native
   is false (the wrapper ends with date, outer 0); the immediate
   `rc=$?` file correctly preserves LAUNCHER_NATIVE_EXIT=1, and the
   wrapper outer never substitutes.
3. Forecast arithmetic corrections carried from root review: S_b
   1122 -> Ic 1123 leaves with 1121 old leaves unchanged (NOT "1122
   other leaves"); the complete scratch gross delta is 77 (76
   non-blank changed lines + 1 blank line).
4. Ic push: actual push pipeline status UNKNOWN (pipeline native not
   captured); a later `git rev-parse Ic` returned 128 (label, not a
   ref); independent remote proof succeeded; no push repeated for a
   receipt.
5. The wrapper's recorded %6N date strings carry corrupted
   sub-second fields on this host (8/9-digit fractions, e.g.
   "11:12:57.79793546Z"); seconds fields are correct and the strings
   are preserved as-is; file mtimes (ns) and the controller's own log
   are the authoritative chronology.
6. Control reader 18377 ended TERMINAL1/empty (shell read without LF
   returns 1 at EOF; `&&` suppressed display) while root's exact
   2-byte write to inode 4470111 succeeded and closed at
   10:52:17.183522Z. The byte-observation limitation is preserved; no
   replay, no new reader; future readers must capture bytes and
   status separately.

## Original P6/recovery and outstanding a gates

- Original P6 failure (frozen I3 module 1844L / 45cf7967...,
  unchanged at Ib and Ic — zero product bytes differ): after the
  test's pg_terminate_backend kills the reviewer pool's only
  connection, the public reviewer manager's post-termination
  restoration re-acquire (p6-restored-pending-enter) does not
  complete within the 30s bounded window, and the subsequent
  reviewer pool.close exceeds 30s. The earlier canonical-absence/
  probe-0 assertions in the same test reach PASS. Pending retention,
  clean replacement, and post-termination lock/GUC checks remain
  UNQUALIFIED.
- CI reproductions at the unchanged module: I3 Group B PG15/PG16;
  Ib Group B PG17/PG18 (raw 171298B/172489B, b-report); S_b Group B
  PG17 job 122135401086 (raw 171243B, SHA256 d59982e7...); Ic Group
  B PG14 job 122149623100 and PG15 job 122149623054 (raws retained
  above). Which engine shows the failure VARIES between runs
  (PG15/16, then PG17/18, then PG14/15) — timing-dependent, with NO
  causal claim.
- This round adds the first PRE-CANCEL localization (local PG16.15,
  SDK path): the suspended owned entry task sits in the manager's
  acquisition expression (safe_promotion.py:483 awaiting
  coroutine_wrapper; pool public state 0/0/false, proxy closed,
  listener empty, no owned role backend/locks). The asyncpg-internal
  reason is UNKNOWN; the SDK (agent-cow-postgresql 0.2.0 / asyncpg
  0.31.0) is unchanged and unpatched. Non-reproduction (driver arm)
  does NOT cure the known failures; reproduction here does NOT
  resolve qualification.
- All original a final gates remain required and UNMET: 20 strict
  required checks + 10 actual PG children + strategic satisfaction
  before eventual acceptance; fresh FULL PG18 NOT RUN (root STOP);
  P7 NOT RUN; green CI alone is insufficient — even a later green
  CI does not cure the known source failure.
- The full-product roadmap remains unqualified, retained from the
  c-order: pending U / true closure / complete 3-family audit /
  committed==U with no pending inside reviewer / durable timeline +
  diff after pending cleanup; unapproved conservative full U, real
  Agent 025 / Editor 028069 / Media 030, drift/history/stale tabs/
  original first touch; human D5 / 084 / 080 MCP / 085 News / 086
  destructive / 087 approved source / 088 full reconstruction / 089
  expiry-revoke-cancel-byteGC-recovery / 090 backup-restore / 091
  full hostile MVP + human release criteria; all 18 fields including
  repeatable_object/storage-validation-render-localization-
  references-forms/Reviewer-without-create desktop+phone/common
  forms/discovery/truthful navigation/actual Apache HTTP adapter/
  failed-FREEZING recovery/leases/retention/byteGC/backups. No
  preview-only or single-PR/qualification-only definition of done.

## GitHub CI / required checks (honest live state)

At literal implementation head Ic f3b266e9... (report drafting,
~11:3xZ, read-only gh api):

- CI run 40492492927: completed/FAILURE (created 10:57:35Z).
- CodeQL run 40492492955: completed/success.
- Commit check-runs on Ic: 30 total = 23 success / 7 failure / 0
  pending.
- ACTUAL engine test failures (each "1 failed, 15 passed, 1 error in
  ~62s", native 1, phase p6-restored-pending-enter 30s deadline +
  fixture pool.close 30s RuntimeError — the same P6 signature):
  - Group B PG14, job 122149623100, 10:57:38Z->11:04:14Z (62.59s);
    raw 150855B retained (SHA256 9e86510a...).
  - Group B PG15, job 122149623054, 10:57:38Z->11:03:02Z (62.20s);
    raw 169702B retained (SHA256 a0266edd...).
- The five "Foundation PostgreSQL 14..18" jobs (jobs
  122154036968/122154037009/122154037034/122154037127/122154037176,
  each failing in ~3s at 11:07:5xZ) are the documented fail-closed
  aggregators requiring the complete A+B set per engine; they are
  the barrier, not five extra independently failing engines.
- Passing at Ic: Group A PostgreSQL 14..18, Group B PostgreSQL
  16/17/18, all CodeQL analyzers, Python 3.12/3.13/3.14 quality and
  package, Compose and edge packaging, Node contracts, Mermaid,
  Markdown, Repository policy, Dependency review, Supply-chain
  evidence.
- S_b state (correcting the order's stale "pending" drafting
  wording): run 40488260199 COMPLETED with 24 success / 6 failure /
  0 pending; its actual engine failure was Group B PG17 job
  122135401086 (15 passed / 1 failed / 1 error, native 1, raw
  171243B SHA256 d59982e7...).
- No acceptance, no merge, no qualification claim from any check;
  these states do not cure the independently proven P6 failure.

## Local setup / dependencies

- gate-wt /tmp/oap-083-8-a/gate-wt: detached Ic f3b266e9 / tree
  e54f2303, full raw status EMPTY (0 lines) at preflight and at END;
  .venv CPython 3.13.14 (uv cpython-3.13.14-linux-x86_64-gnu); frozen
  module 1844L / 45cf7967... unchanged.
- Host python 3.14.4 ran the controller and the statics (disclosed,
  as in b); the target 3.13.14 ran both arm children (RUNNER_PY) and
  the py_compile statics. Kept DISTINCT.
- Docker 29.1.3; images postgres:16-alpine
  sha256:0cefaabd882e42bcb2a2f3dc56d3ce4770560ba62fd7f197f1a2e008fd57
  31ab (PG 16.15) and python:3.13-slim
  sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a56
  78c2f (runner base). uv 0.12.5, ruff 0.16.3 (project venv), Node
  v24.22.0, pnpm 11.22.0 unchanged. No dependency, lock, plugin,
  image, service, role, or egress change; no installers run.

## Documentation

- Zero documentation changes in c. The five a-round docs
  reconciliations are byte-identical at Ic; docs gross remains 154
  (docs/ 145 + oap/INCREMENTS.md 5 + oap/MVP-PROGRESS.md 4); the
  500-line docs cap is untouched.

## Safety and scope confirmations

- ONE launcher invocation executed (the root-approved single Phase B
  call); NO third launch, NO relaunch, NO variant, NO new gate, NO
  extra SDK attempt, NO ALL31/QPG/FULL/P7/WHOLE/LOCAL6 or unrelated
  runtime.
- NO source/controller/arm repair after the freeze; the five frozen
  bundle hashes are unchanged (re-verified at report drafting); the
  b bundle at its approved hashes is preserved unmodified.
- ZERO product/test/CI/docs/lock/dependency changes; the only new
  committed c paths are the c-report (this S_c commit) plus the
  c-order + active already at Ic; cumulative 15 paths.
- human3 preserved: `.codex/`, CODEX-SESSIONS.md, codex.sh are
  untouched, untracked, and NOT committed; the product worktree is
  clean with only the exact human3 untracked artifacts (raw status
  1069 lines, SHA256 2822a3ec..., root-verified equal to the
  pre-round original).
- No secret printed (PGPASSWORD rendered `<redacted:set>` in
  start.txt; fake test credential only); no production/protected
  credentials; Docker used only for owned disposable
  containers/volumes on the internal 5432 container network; no
  shared host 5432; no foreign PID/DB/role/volume touched; the 23
  unattributed volumes and running foreign containers untouched.
- No SDK patch/monkeypatch/proxy/fork/upgrade; no private foundation
  tables/SQL; no xfail/skip/catch-to-PASS; no pool replacement/size/
  reset/recreate; no listener wait/sleep; no assertion weakening.
- No merge/auto-merge/close; no next ID/PR/branch/acceptance chosen
  by coding; this report makes no selection.
- No FIFO replay: the sole root c response reader 27620 is pending
  and untouched; no new reader or control opened; exactly ONE
  2-byte ASCII OK (4f4b, no LF) will be written to the ACTUAL
  strategic /home/janezp/codex-supervision/slaif-agent-site/
  response.fifo (inode 4470112, verified) after remote verification,
  then closed.

## Known limitations / blockers

- Blocker: the original P6 safety contract is NOT met at frozen I3
  (unchanged at Ib/Ic); this round reproduced it on local PG16 (SDK
  arm) with the first pre-cancel localization (manager acquisition
  expression, safe_promotion.py:483 -> opaque coroutine wrapper),
  but the asyncpg-internal cause remains UNKNOWN; root decides the
  next bounded round.
- The SDK cases 3 and 4 are NOT RUN (PREVENTED); no data, no
  substitute. The driver arm result is a structural contrast, not a
  causal proof.
- The unsafe marker (arm fixture pool.close 30s failure, code 7) is
  preserved for root's finite decision; F1/F2 fail-stop limits
  remain; no global exception safety is claimed.
- The Ic push pipeline native is UNKNOWN (not re-pushed for a
  receipt); the wrapper %6N date strings are corrupted
  sub-second-only (preserved as-is); statics pass 1 is a disclosed
  deviation; the wrapper is outside the submitted manifest (1206/
  1250 total harness).
- Carried from a/b (full text in the immutable reports): QPG4
  runner pytest/container exit UNKNOWN; QPG5 local PG15 pass vs CI
  PG15 fail is timing-dependent with no causal claim; 23
  unattributed anonymous volumes untouched; the QPG5 evidence
  directory name carries a sed typo (internal guards exact I3); the
  ALL31 launcher tee pipe parent native UNKNOWN (31 named child
  natives are the proof); the five Foundation PostgreSQL aggregator
  failures are the fail-closed barrier; advisory GHSA-6q48-6c7w-9gw2
  remains ACTIVE (repo alert 17 withdrawn; no fixed-by-merge, no
  release claim).
- Phase A statics and root source reviews are NOT runtime
  qualification; the frozen c bundle's ONE execution is the first
  actual diagnostic data of the increment.
- This report references the immutable a-report (627L, 34043B,
  SHA256 6dfd6f536ab3c6550564df76ec2537390e4a3114cce1062d6f5bd3f14b036
  128) and b-report (598L, 31528B, SHA256
  d9613a5952b23fdc2b51559b5423ac56d3b0811061673bd12c70df3a5c7dd460)
  without rewriting or repeating them.

## Recommended strategic follow-up

Factual only; no selection made. The c diagnostic achieved its
bounded purpose: the first pre-cancel observation of the P6 stall
localizes it to the public reviewer manager's entry acquisition
expression (safe_promotion.py:483, awaiting an opaque coroutine
wrapper over pool.acquire, with pool public state 0/0/false and no
owned role backend/locks). A root-authorized next bounded round
could extend observation of the inner coroutine-wrapper / pool.
acquire mechanism (and the fixture pool.close path) within the same
DIAGNOSTIC_ONLY scope. Coding proposes no workaround, no pin change,
no new feature, and no release or acceptance claim. Root alone
independently reviews this partial handoff, chooses the
continuation, and eventually accepts/merges.
