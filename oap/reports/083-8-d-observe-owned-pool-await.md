# OAP execution report — 083-8-d: observe the owned pool await

- Order: `oap/orders/083-8-d-observe-owned-pool-await.md` (213L, 13886B, SHA256
  `ac8600fcc30220eb7f0c4c4c1eccd1e245df54ed45c8e97d283952cd320e4050`, immutable)
- PR mode: `AMENDED_EXISTING_PR` — PR #112
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/112>, state `open`, title
  "083-8-a: qualify public whole-session promotion (PUBLIC_API_QUALIFICATION_ONLY)"
- Status: `PARTIAL`
- Branch: `oap/083-8-a-qualify-public-whole-session`; base `main`
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0`
- Starting remote SELF: S_c `5334e69e322eae242adb64d5f757987f77285337`
- Literal implementation SHA: Id `cc27b8ce90b2b513e02f0f1a8fd9765f6c6f1d17`
  (tree `fd0a3cff5e64e36d07e930b96cd5580dbeade9c4`), sole parent S_c;
  commit = d-order + `oap/active` only (root-verified remote scope review and
  complete 1124->1125 mode/type/blob leaf maps)
- Report publication commit: `SELF` — the single report-only commit whose
  sole parent is Id and whose sole changed path is this report; its SHA is the
  verified remote PR head (section 7)
- Pushed commits this round: Id, then this report-only SELF commit
- Cumulative PR paths: 16 at Id (measured `git diff --name-only
  d18b6e4c..cc27b8ce`, retained `report-pathcount-Id.txt`); 17 at the
  report-only commit (order expected 17 = 15 + d-order + d-report; measured
  at publication, section 7)

## 1. What this round did (DIAGNOSTIC_ONLY, zero product gross)

One scratch-only, root-approved diagnostic attempt to answer: can a bounded
READ-ONLY observation of the SOLE owned `coroutine_wrapper` reached through
the owned `task/ctx.gen/ag_await/cr_await` path expose its retained awaited
coroutine and the actual suspended inner source frame? The observation
mechanism was designed, source-frozen, statically checked, and approved; the
ONE approved runtime attempt then completed healthy and **did not reproduce
the P6 stall**, so the new observation path was **NOT exercised**. The
original qualification remains PARTIAL; nothing here is a safety pass, a
causal attribution, or a closure of the known P6 failure.

No product/backend/web/browser/media/contract/DDL/role/lock/dependency/image/
base/scanner/action/license/authority/egress/publication/policy change.
Product/test/CI/docs gross at Id: 0 new beyond the permitted d-order +
`oap/active` (and this report at the SELF commit).

## 2. Phase A — source (scratch `/tmp/oap-083-8-d/`, not committed)

### 2.1 Frozen bundle (v3, as executed)

| file | lines | SHA256 |
| --- | --- | --- |
| p6diag-common.py | 450 | `a20c9c313b165e43cc57b3411cb62896c4c105fdff00d84ffb9c05f15a778d62` |
| p6diag-driver-arm.py | 263 | `13e8b238c8ea4e6e107de294c36687a7c79dfa52539683fba34e9b7c8949b35f` |
| p6diag-sdk-arm.py | 407 | `4222f64bb273ebdc683b66a6794941e7c245a2b416f1168bbe16f0266bbacc7e` |
| p6diag-controller.py | 1219 | `e29be205196fe6d7536f233a1d7ffc82aa471eb77cb248febdf6c362c5213f84` |
| p6diag-launch.sh | 6 | `1f1023ca2c711c9aa054e320cece4a6ae04c4d82cf021d52446f382765634497` |

Footprint (measured, no packing): diagnostics (common+driver+sdk) = 1120 vs
revised prospective envelope 1140 (20 under); harness
(controller+launcher) = 1225 vs 1250 (25 under); total runtime inputs 2345.
The driver arm is NOT executed in d; its file retains frozen c bytes as
conservative footprint only. The initial 6-line overrun over the OLD 1100
envelope (observer guard/anchor documentation written before the prospective
request) remains disclosed and is NOT retroactively approved (root decision
`root-d-correction-prospective-source-envelope-decision.json`,
SHA256 `a83e0e018da71eff0dea868352f8d2a12672446f47eb5f9baac768a6e55d563d`).

### 2.2 The owned-wrapper observer (d delta in `p6diag-common.py`)

`observe_owned_wrapper` (450L file; function 76L): guarded READ-ONLY
observation invoked in `observed_entry` ONLY on the true original 30s entry
deadline, AFTER `dump_task`, BEFORE `task.cancel()`. Source anchors
(CPython v3.13.14): `Objects/genobject.c` `coro_await` ~L1062 retains the
awaited coroutine in a GC-managed wrapper whose traversal (~L1252) visits
it; `Modules/gcmodule.c` `get_referents` ~L249 builds the list from the
supplied object's traversal; `Doc/library/gc.rst` ~L152: referents are
traversal-defined. Only `gc.get_referents` on the one actual built-in
`coroutine_wrapper` is used. FORBIDDEN/unused: get_objects/get_referrers/
collect/heap scans/GC settings and callbacks, SDK private fields/invocations,
mutation, iterator stepping. Guards: actual CPython implementation
(`sys.implementation.name == "cpython"`) + exact version `(3, 13, 14)`,
actual built-in wrapper type, exactly ONE referent whose type IS
`types.CoroutineType`; anything else emits `wrapper-unknown` facts only.
The recovered coroutine is walked by the existing finite
`await_chain` (depth cap 8, no revisiting object IDs); emission is
type/function/path/line/phase + safe shape/counts only. The ENTIRE
observation body is defensively bounded (one `try/except BaseException`;
the failure-fact emission is itself nested): any observer failure records
`wrapper-observe-failure` (`status=UNKNOWN`) and returns, so the original
cancel/drain flow is never delayed, masked, or changed.

### 2.3 Correction cycle and statics (actual)

- v1 submission (1106/1225/2331) -> root FULL-read found: (a) the defensive
  boundary covered only `gc.get_referents`; (b) no CPython-implementation
  guard; (c) `isinstance` instead of exact type identity. Complete
  actual+remaining forecast v2 submitted BEFORE edits (disclosing the
  +6 initial overrun); root approved the narrow correction only (prospective
  diagnostics 1140, harness 1250 unchanged).
- v3 applied: exactly the approved observer correction in
  `p6diag-common.py` (function 62 -> 76 lines, +14; file 436 -> 450) plus
  line 181 ONLY of `p6diag-controller.py` (MANIFEST common hash; the
  authorized exception to "controller unchanged"; no behavior change).
  Applied diffs retained: `v3-applied-common-diff.txt`,
  `v3-applied-controller-diff.txt`; pre-correction bytes retained in
  `pre-v3-correction/`. Root independently verified the v3 complete-5
  hashes, full applied diffs, forecast and manifest.
- Statics (each exactly ONCE, after applied-source review; actual tool
  results, `d-v3-final-statics-record.txt` SHA256
  `5b06926849b85221fb9e5de30849d63c1ed68840989609a13a78d0afee8e4502`):
  - Ruff F821, `--no-cache`, all 4 Python inputs: native 0,
    "All checks passed!" (ruff 0.16.3, gate-wt venv; 12:47:21Z)
  - Target CPython 3.13.14 `py_compile`, all 4 inputs: native 0 (12:47:27Z)
  - Launcher `sh -n`: REUSED actual native 0 from 12:28:57Z (launcher hash
    `1f1023ca...` unchanged); NOT repeated for a new receipt.
- No baseline repeats, no import/preflight/selftest/DB trial at any point.

## 3. The ONE approved runtime (run1)

### 3.1 Approval and exact invocation

- Approval: `root-d-one-sdk-execution-approval.json` (12:48:49.379780Z):
  APPROVED_ONE_FROZEN_D_SDK_DIAGNOSTIC_LAUNCH; command_exact
  `sh /tmp/oap-083-8-d/p6diag-launch.sh`; ONE launch/ONE SDK/fresh
  proven-owned PG16/SERIAL/180s including lifecycle+observations+cleanup/
  original 30s entry-drain-close/aux<=5/reserve30; no driver, no second
  SDK, no rerun/variant/relaunch/new gate.
- Executed via the direct exec tool with EXACTLY that command: no pipeline,
  no echo, no chained command, no newly created execution wrapper (the c
  wrapper deviation, section 5, is not repeated). The launcher is
  `exec python3 .../p6diag-controller.py` (exec-only), so the tool's native
  terminal status IS the launcher/controller native.
- Tool native: **0** (terminal). Clocks: actual call 12:49:35.714Z, actual
  terminal 12:49:43.405Z (root-recorded in the independent review);
  controller START 12:49:35.842Z / START receipt 12:49:36.062Z, END
  12:49:43.389Z.
- Launcher stdout captured by the tool: **0 bytes** — the controller records
  ALL evidence into the run-directory file ledger by design (overall.log,
  raw receipts, both container streams, end.txt); natives are established
  from the tool status plus those receipts, independently FULL-reviewed by
  root. This is a design fact, not lost output.

### 3.2 Owned cluster and provenance (all rc=0, receipts retained)

| resource | identity | provenance |
| --- | --- | --- |
| PG16 container | `e268000c633a0efa09560dbd32ec8cb65d6443636590e53f1d8a98f3e17de66c` | image `sha256:0cefaabd...5731ab` (`postgres:16-alpine`), PostgreSQL 16.15, `system_identifier` 7701328950532948008, volume-backed data |
| runner container | `4621835d46d779de01d1255d2395ac21ba2cf0adf10e9fbf3652202c08eb986a` | image `sha256:70729b46...5678c2f` (`python:3.13-slim`), `NetworkMode` verified `container:<PGCID>`, ro bind mounts (gate-wt, scratch, uv), argv = gate-wt venv CPython 3.13.14 + `p6diag-sdk-arm.py` |
| volume | `0838d-20261027T124935Z-2317589-pg1` | label `oap0838d.rid=20261027T124935Z-2317589` (ownership proof), Mountpoint recorded before deletion |

Only proven absent-baseline + actual-create + positive-owned-ledger
resources were used; the 23 foreign unattributed volumes were untouched
(independent post-check: zero `0838d-` containers, zero `0838d-` volumes).
Module under test: frozen `test_foundation_whole_session_qualification.py`
1844L `45cf7967...` at exact Id (P6DIAG_MODULE + SHA env, enforced).

### 3.3 Attempt 1 (sdk) — actual observations and result

Child natives: `child_exit=0`, `docker wait` stdout `0`, terminal-inspect
`State.Status=exited`, `State.ExitCode=0`. Attempt ledger:
`cleanup_safe=True`, `cleanup_in_budget=True`, `body_exception=False`,
`unsafe_marker=False`, `pg_evidence=ok`, `mount_evidence=proven`,
`EVIDENCE_DEGRADED=False`, `OVERALL=0`, `END_SOURCE_GUARD=ok`.

SDK arm stream (t_mono from arm start, python 3.13.14, bound 30.0s):

| t_mono | phase | fact |
| --- | --- | --- |
| 0.629 | setup | arm start, bound 30.0 |
| 2.831 | fixture-ready | schema `qw8_579fbf6b32af`, reviewer role `qw8_reviewer_579fbf6b32af` |
| 2.838 | server-identity | db `postgres`, user `postgres`, `system_identifier` 7701328950532948008, version 16.15 |
| 3.000 | window-open | owned window pid 125 |
| 3.017 | in-window-obs | `idle in transaction`, 71 locks |
| 3.036 | driver-exception (terminate-window) | `asyncpg` InterfaceError: `cannot call Connection.is_in_transaction(): connection has been released back to the pool`; sqlstate absent (client-side); retained frames are the LAST 3 (`agentcow/postgres/safe_session.py:297 in_transaction` -> `asyncpg/pool.py:64 call_con_method` -> raise), NOT the original first query exception |
| 3.040 | canonical-restored | canonical/probe rollback reached |
| 3.171 | recovery-assertions | ok=true (pending op, old pid gone, actual replacement promotion, runtime/reviewer GUCs) |
| 3.171-3.172 | finally/reap terminals | cancelled=false |
| 3.518 | fixture-teardown | result `clean` |
| 3.518 | outcome | **NO_REPRODUCTION**, codes `[]`, unsafe_cleanup false, exit_code 0 |

PG-side: the window pid 125 was terminated by administrator command at
12:49:41.922 (owned kill, exact instant not logged; after the 3.017
in-window observation and before the 3.036 exception). No stall occurred:
the public reviewer entry was acquired well inside the 30s deadline, so
`observed_entry` took the healthy path and the NEW
`observe_owned_wrapper` mechanism was **NOT exercised** — no
`wrapper-guard`/`wrapper-type`/`wrapper-referent`/`wrapper-inner-chain`/
`wrapper-unknown` records exist in this run.

### 3.4 Cleanup and residue (actual)

Both container streams and Mounts were captured before each container
deletion; volume labels + Mountpoint were captured before volume deletion.
Order: runner stop/rm (rc 0, post-absent verified) -> PG stop/rm (rc 0,
post-absent verified) -> volume rm (rc 0, post-absent verified) -> final
`0838d-` name filter absent. All within the attempt budget; no
post-deadline recovery; finalize: "no residual owned/attempted resources";
END raw receipts: gate-wt status 0 lines, HEAD Id, tree exact. No foreign
resources touched. Independent post-verification (read-only): zero owned
containers/volumes/processes.

### 3.5 What this run does and does not establish

- Establishes: the d controller/ledger/cleanup law works end-to-end on a
  healthy path at Id; one complete NO_REPRODUCTION observation of the
  original post-promotion window (idle-in-transaction, 71 locks, owned
  termination, independent canonical/probe rollback, pending op, old pid
  gone, replacement promotion, GUCs, clean teardown).
- Does NOT establish: no inner acquisition-phase localization (no stall,
  no wrapper record); no causal owner (SDK vs driver vs platform); no
  timing-dependence proof (one healthy run); no closure of the known P6
  safety failure (a/local/CI/c evidence, sections 5-6). Cause remains
  UNKNOWN.

## 4. Immutable c-report corrections (carried, per d-order)

1. "Opaque" means the c walker could not reach inner frames; it does NOT
   mean all read-only observation is impossible. The guarded wrapper-GC
   source mechanism is new proof; its runtime outcome was still UNKNOWN
   before observation (and this run did not exercise it).
2. Varying outcomes across engines (14..18) do not by themselves prove
   timing dependence or a causal owner.
3. Host 3.14.4 ran the controller/mechanical helpers; the final c
   `py_compile` was target 3.13.14 and Ruff its native binary. No host c
   compile was indexed.
4. Printed date strings/controller/tool/raw-ns chronology are preserved as
   recorded. Eight/nine fractional digits alone do not prove corruption or
   a `%6N`/host-date cause.
5. Ic `git push` child native is UNKNOWN; the successful tail pipeline
   allowed the following AND command, whose bad Ic-symbol returned 128.
   These natives are NOT equated; independent remote proof succeeded and
   no push was repeated for a receipt.
6. c supplied the FIRST scratch diagnostic observations; a/local/CI already
   had P6 data.
7. SDK `t_mono 2.877` (c run) records the window exception, not an exact
   kill timestamp; the owned kill occurred after the 2.866 observation and
   before the 2.877 exception. The actual interval is kept.

## 5. Deviations and procedural record (actual)

- c: the 11-line `run1-exec.sh` wrapper (SHA256 prefix `73e1584e...`) was
  added at launch and was NOT in the submitted 5-file manifest; the
  "wrapper exit == launcher" comment was false (wrapper ends at its last
  `date`). d corrects this: the launch law is the direct exec-tool command
  EXACT, no wrapper — executed as such this round (tool native IS launcher
  native).
- c: F821 baseline was invoked twice: the first (via `tee`) printed the
  tee native 0 with the Ruff child UNKNOWN; the second (direct) was native
  1. Both records preserved; the false first "native 0" label disclosed;
  no passing/baseline check was rerun for a receipt.
- d: initial 6-line overrun over the OLD prospective 1100 envelope,
  disclosed in the v1/v2 submissions, NOT retroactively approved; the
  revised 1140 envelope is met by measured 1120. No packing/compression/
  evidence removal at any step.
- d: v2->v3 narrow source correction after root's first-submission review
  (whole-observer defensive boundary; CPython implementation guard; exact
  `type(r) is types.CoroutineType`; old inner try/except subsumed).
  Controller change limited to the MANIFEST common-hash line (authorized).
- d: static sequence differed from c by design (root-authorized): applied
  source was submitted to root BEFORE the final checks; one final
  F821/compile pass then ran; launcher `sh -n` receipt reused (unchanged
  hash), not repeated.
- d: launcher tool stdout was 0 bytes (controller file-ledger design,
  section 3.1); natives established from tool status + run receipts + root
  independent review.
- Environment disclosure: host 3.14.4 ran the controller and mechanical
  helpers (as in c); the arm ran in the runner container under gate-wt venv
  CPython 3.13.14; final compile target 3.13.14; ruff 0.16.3.

## 6. Actual full-scope gaps (why PARTIAL)

- P6 remains a REAL failure. Preserved actual failures: a-local QPG4
  (INCOMPLETE/hung attempt, native UNKNOWN preserved, no pass claim);
  I3 CI PG15+PG16, Ib CI PG17+PG18, Ic CI PG14+PG15 — each 16 collected /
  15 passed / 1 FAILED (`p6-restored-pending-enter` 30s) + 1 teardown
  ERROR (SDK fixture `pool.close` 30s) / native 1. Current Id CI: 30
  terminal checks, 22 SUCCESS / 8 FAILURE (read-only gh verification
  12:57Z, after root's 12:51:37Z review). One healthy NO_REPRODUCTION
  diagnostic run does not resolve any of this.
- The NEW observer was NOT exercised (no stall); no inner
  queue/holder/socket phase is observed or proved; no SDK/driver/platform
  causal claim is made; no data-loss or version-determinism claim.
- NOT satisfied by a diagnostic (all remain): a's P1-P7 criteria; fresh
  final ALL31 at the final I + supply-chain + broader Ruff; fresh
  QPG14..18 + FULL PG18 + P7 serial at the same I; current SELF 20
  required + 10 actual children; CI whole Compose; fresh six-image
  artifacts; carry predicates; security and docs gates.
- FULL planned product remains pending: U/true closure, complete 3-family
  audit, exact U, no-pending INSIDE reviewer, durable timeline + diff AFTER
  pending cleanup, human D5/084/080-MCP/085-News/086-destructive/
  087-source/088-full-reconstruction/089-expiry-revoke-cancel-byteGC-
  recovery/090-backup-restore/091-hostile-MVP + human release criteria,
  all 18 fields, repeatable object, common desktop/phone forms, Reviewer
  without create, actual Apache HTTP, failed FREEZING recovery, leases,
  retention, byte GC, backups. No smaller preview-only, single-PR, or
  diagnostic-only definition of "product finished" is claimed.
- No acceptance, merge, or release claim; no fixed-by-merge or release
  statement; PR112 remains PARTIAL/unaccepted. Strategy alone reviews,
  accepts, and merges; no next-order choice is made here.

## 7. Publication procedure (exact, same-file atomic)

- Temp written INSIDE `oap/reports/` (same filesystem):
  `.083-8-d-observe-owned-pool-await.md`, then exact lint
  `npx --yes markdownlint-cli2@0.23.2 --config .markdownlint-cli2.jsonc
  --no-globs <file>` with Node v24.22.0 tool PATH: native 0, 1 file,
  0 issues in 0 files (re-linted after any edit; actual receipts retained
  in `/tmp/oap-083-8-d/`).
- Pre-Git sha256/inode/size/UTC+raw-ns recorded; fsync of the temp;
  SAME-file atomic rename to `083-8-d-observe-owned-pool-await.md`; parent
  directory fsync; post-rename sha256 match.
- Staged EXACTLY one path (`git diff --cached --name-only` = this report
  only, full-line checked for M/D); HEAD asserted literal Id before commit.
- Commit message: `083-8-d: publish OAP 083-8-d execution report
  (report-only SELF, PARTIAL)`.
- S_d verified: sole parent Id; sole changed path this report; blob bytes
  equal local sha256; 17 cumulative paths at S_d (measured).
- Pushed (native captured directly, no pipe); remote proof BEFORE the
  response OK: `git ls-remote` head = S_d; gh API commit parents = [Id],
  files = [this report]; PR head = S_d; remote raw content sha256 = local.
- ONE exact 2-byte ASCII `OK` (hex `4f4b`), no LF, written and closed on
  the actual strategic response FIFO (inode 4470112 verified before write);
  no replay.

## 8. Evidence index (paths retained, immutable)

- Run1: `/tmp/oap-083-8-d/run-20261027T124935Z-2317589/` — start.txt,
  overall.log, preflight-raw-receipts.log, sdk-attempt1.log,
  sdk-attempt1-raw-receipts.log, rescue-sdk-attempt1-run.cli-stdout,
  rescue-sdk-attempt1-run.cli-stderr (0B), rescue-sdk-attempt1-pg.cli-stdout,
  rescue-sdk-attempt1-pg.cli-stderr, finalize.log,
  finalize-raw-receipts.log, end.txt (13 files; root's complete artifact
  manifest + independent review:
  `root-d-run1-independent-review-and-partial-closure.json`)
- Bundle + records: `/tmp/oap-083-8-d/` — 5 frozen sources,
  `frozen-bundle-manifest-d.txt` (v3), `p6diag-phaseA-forecast-d.md` (v1),
  `p6diag-phaseA-forecast-d-v2-actual-remaining.md`
  (`774e9629...`), `p6diag-phaseA-forecast-d-v3-actual-freeze.md`
  (`c8631066...`), `v3-applied-common-diff.txt` (`96b6c7dd...`),
  `v3-applied-controller-diff.txt` (`4f9a257f...`),
  `pre-v3-correction/` (pre-correction bytes), `d-v3-final-statics-record.txt`
  (`5b069268...`), `d-v3-F821-all4.log`, `d-v3-py_compile-all4.log` (0B),
  `d-v3-native-*.txt`, `report-pathcount-Id.txt`, and all root
  decision/review JSONs of this round.
- c evidence (immutable): `/tmp/oap-083-8-c/run-20261027T111257Z-2180425/`
  (18 files) and c-report 779L SHA256
  `5a35244c22ce69b3b661acb6888a1d20d171e6b70258b7f74217198077b0f4af`.
- Prior reports (immutable, referenced not duplicated): a-report 627L
  `6dfd6f53...`, b-report 598L `d9613a59...`, c-report (above).

## 9. Local setup and environment

- gate-wt `/tmp/oap-083-8-a/gate-wt` at exact Id (HEAD + tree verified in
  run start/END receipts), raw status 0 lines; venv CPython 3.13.14
  (uv `cpython-3.13.14-linux-x86_64-gnu`); frozen module 1844L
  `45cf7967...` unchanged by this round.
- Docker 29.1.3; PG image `sha256:0cefaabd...5731ab` (16.15); runner image
  `sha256:70729b46...5678c2f`; host controller Python 3.14.4 (disclosed);
  ruff 0.16.3; `sh` = `/usr/bin/dash`; lint Node
  `/home/janezp/.local/tools/node-v24.22.0-linux-x64/bin`.
- Credentials: `PGPASSWORD=qualification-admin` is a FAKE disposable
  credential, rendered `<redacted:set>` in reports; no real secrets,
  capabilities, cookies, DB URLs, or private artifact URLs committed or
  printed anywhere in this round.

## 10. Confirmations

- Scope: diagnostic-only order executed exactly; no source edits after the
  approved v3 freeze; no extra PR, no new numeric objective, no scope
  expansion; no ALL31/QPG/FULL/P7/WHOLE/LOCAL6/unrelated runtime this
  round; no merge/auto-merge/close.
- Secrets/production: none touched; no production systems, data, or
  credentials accessed; no egress beyond the authorized remote proof.
- Skips: no check, gate, or test was skipped, and nothing is reported as
  passed that did not run and pass; "NO_REPRODUCTION" is an observation
  result (exit 0), explicitly NOT a safety pass or qualification.
- Human files: `.codex/`, `CODEX-SESSIONS.md`, `codex.sh` preserved
  untracked/untouched, never committed (raw status clean of tracked
  changes; untracked set unchanged in kind).
- No signal replay; no duplicate FIFO readers; sole root response reader
  (80928) received exactly one 2-byte OK; next control reader (one,
  byte-retaining) opened after this publication per the d-order.

## 11. Limitations and blockers

- P6 safety failure unresolved: original qualification PARTIAL; current
  Id CI 22/8; no acceptance/merge until strategy's independent review.
- The owned-wrapper inner phase is still UNOBSERVED (no stall occurred); a
  future attempt may be needed after root's next bounded order. Known
  F1/F2 inherited fail-stop limitations preserved; no universal cleanup or
  log-sink safety certificate is claimed.
- Blocker for further work: none executor-side; awaiting root's formal
  handoff/review and next exact control.
