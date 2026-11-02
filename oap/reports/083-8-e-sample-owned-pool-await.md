# OAP execution report — 083-8-e: fixed sampling of the owned pool await

- Order: `oap/orders/083-8-e-sample-owned-pool-await.md` (239L, SHA256
  `3a23fc2def558482a6e7ac15def6a5f28f846dc84eddbe37003897c5fb78f72c`, immutable)
- PR mode: `AMENDED_EXISTING_PR` — PR #112
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/112>, state `open`
- Status: `PARTIAL`
- Branch: `oap/083-8-a-qualify-public-whole-session`; base `main`
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0`
- Starting remote SELF: S_d `8d3c8f345b9782580cd3a5231a173bc44a88cbf8`
  (tree `34bbb60e036ca1f7bace656016f05481d859d07a`), sole parent Id
  `cc27b8ce90b2b513e02f0f1a8fd9765f6c6f1d17`, sole path d-report, exact
  remote bytes; root-verified complete 1125->1126 leaf maps
- Literal implementation SHA: Ie `faec5fca695e9b6f8a0bf371e0f5ed3152151f91`
  (tree `4c4a3fba1540c5307a9e6672c4715d6a647fe2db`), sole parent S_d, only
  e-order + `oap/active` changed; root-verified complete 1126->1127 leaf
  maps, gate clean, module 1844L `45cf79671261212c19143315daeaecfc1b01b1e48d0b3c2cdf9e85cf881563a8`
- Report publication commit: `SELF` — the single report-only commit whose
  sole parent is Ie and whose sole changed path is this report; its SHA is
  the verified remote PR head (section 10)
- Pushed commits this round: Ie (Phase A; commit 13:19:33Z per
  `root-e-Ie-remote-commit.json`; 13:16Z = activation/control), then this
  report-only SELF commit
- Cumulative PR paths (measured): 17 at S_d (baseline, gross 5635);
  18 at Ie (gross 5874); 19 at SELF (order expected 19; measured, section 10)

## 1. What this round did (DIAGNOSTIC_ONLY, zero product gross)

One root-approved FIXED cohort (max three SDK cases 1,2,3, serial, fresh
owned PG16 each, 180s ABSOLUTE each) to exercise the UNOBSERVED stall-only
observation path of the d observer (d's single healthy case never
exercised it: NO_REPRODUCTION). Actual outcome: attempt 1 REPRODUCED the
P6 stall; the new guarded observer was exercised for the first time and
localized the suspended owned await to `asyncpg Pool._acquire ->
_acquire_impl -> asyncio.Queue.get` (queue-wait phase; at the snapshot this request had not yet received a
holder and had not reached ch.acquire/connect); the bounded owned-fixture `pool.close()`
(30s) then FAILED, raising the unsafe marker; the stop law correctly
PREVENTED attempts 2,3. Controller-owned disposal of every owned resource
was SAFE (native 0, in-budget, absence proven). Overall nonzero (1).
This is a diagnostic reproduction + localization, NOT a safety pass, NOT
a causal attribution, NOT qualification; the original qualification
remains PARTIAL. Root alone decides later repair/qualification scope.

Zero product/src/web/browser/media/contract/DDL/role/lock/dependency/
image/base/scanner/action/license/authority/egress/policy/publication
change; only e-order + `oap/active` at Ie and this report at SELF
(section 9 caps measured).

## 2. Phase A — subject, frozen bundle, checks, environment

### 2.1 Subject-first commit and gate

Ie committed/pushed FIRST (commit 13:19:33Z): sole parent S_d, only
e-order + `oap/active`, all other leaves S_d-equal (root 1126->1127 complete
leaf maps). gate-wt at EXACT Ie/tree with EMPTY full raw status (0B); only
the ORIGINAL product checkout carries the complete 132624B raw status
(SHA256 `2822a3ec6f3a154f091df6d42d681620f4273cc6bec563c1a2241f97f3a64eb8`)
with exact human3 exclusions (`.codex/`, `CODEX-SESSIONS.md`, `codex.sh`
untracked, intact); venv CPython 3.13.14 preserved.

### 2.2 Frozen bundle (v2, as executed)

| file | lines | SHA256 |
| --- | --- | --- |
| p6diag-common.py | 450 | `a20c9c313b165e43cc57b3411cb62896c4c105fdff00d84ffb9c05f15a778d62` (BYTE-EXACT d) |
| p6diag-driver-arm.py | 263 | `13e8b238c8ea4e6e107de294c36687a7c79dfa52539683fba34e9b7c8949b35f` (BYTE-EXACT d; NEVER ran) |
| p6diag-sdk-arm.py | 407 | `4222f64bb273ebdc683b66a6794941e7c245a2b416f1168bbe16f0266bbacc7e` (BYTE-EXACT d) |
| p6diag-controller.py | 1254 | `46366006cdd1c329a4383f04daff76d44fd98a78f1b448c97f35d40536cbb74a` (e v2) |
| p6diag-launch.sh | 6 | `14c67dc1a8a688ba587bc5bf557a5d83bce38551a3a2a90cf642f2eb4dd1ed1f` (e) |

Footprint (measured, no packing): diagnostics (common+driver+sdk) = 1120
vs cap 1140 (20 under); TOTAL harness = 1260 (controller 1254 + launcher
6) vs original envelope 1250 / prospective envelope 1270 (10 under);
all5 = 2380.

### 2.3 v1 -> v2 history (deviation disclosed, not retroapproved)

v1 (controller 1249L `7eb7e916…`) crossed the original 1250 envelope by
5 lines (1255) BEFORE the prospective request: preserved and disclosed as
deviation, NOT retrospectively approved. Root then fixed the prospective
envelope at 1270 and approved a narrow source/metadata clarification
(deadline-law docstring clause + START log-label strings; no behavior
change): the deadline-law clause now states COHORT_WORK_MAX=540s is the SUM of the
three allocated 180s attempt budgets, a PRESTART boundary only (NOT a
global deadline, NOT a running-attempt cutoff; preflight/END outside the
loop), and start.txt now writes `ATTEMPT_WORK_MAX=540s (sum of 3
allocated 180s attempt budgets)` plus `COHORT_PRESTART_BOUNDARY=540s
(prestart boundary only; …)`. Applied delta: 2 hunks, +11/-6, net +5
(within root's expected 0..6) -> 1260. v1 preserved at
`pre-v1-clarification/`; d bundle at `pre-v1/`.

### 2.4 ONE final source-check pass (13:49:18Z, authorized)

- all4 ruff 0.16.3 `check --no-cache --select F821`: native 0
  ("All checks passed!", log `82b3e6a6…`)
- all4 target CPython 3.13.14 `python -m py_compile`: native 0 (empty
  log = success)
- changed launcher `sh -n` (FRESH: e launcher `14c67dc1` changed vs d
  `1f1023ca`): native 0; actual shell identity `/usr/bin/sh -> dash`
- No baseline/help/negative-control/version/glob/lint-variant or
  passing-check repeat; no source check of the initial WIP was ever run
  (actual ledger preserved); no import/preflight/selftest/DB before the
  approved launch (outside-launch sense, correction 2)

### 2.5 Runtime metadata (read-only, immediate natives, 13:55:09Z)

- Host controller python3: `/usr/bin/python3 -> /usr/bin/python3.14`,
  `Python 3.14.4` (disclosed; runs the CONTROLLER only — runner
  containers execute arms via gate-wt venv python 3.13.14)
- Docker image IDs (read-only inspect): `postgres:16-alpine` =
  `sha256:0cefaabd882e42bcb2a2f3dc56d3ce4770560ba62fd7f197f1a2e008fd5731ab`;
  `python:3.13-slim` =
  `sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f`
  — EXACT match the embedded `PG_EXPECT_ID`/`RUNNER_EXPECT_ID` guards
- Runtime argv/env source index: launcher L6 `exec python3
  /tmp/oap-083-8-e/p6diag-controller.py`; controller constants L185-200
  (MOD/MOD_SHA/SCRATCH/PGTAG/PG_EXPECT_ID/RUNNER_BASE/
  RUNNER_EXPECT_ID/UVROOT/PGPASSWORD/VOL_LABEL/ATTEMPT_TOTAL=180/
  CLEANUP_RESERVE=30/COHORT_WORK_MAX=540/ATTEMPTS=3xSDK/RUNNER_PY); PG
  argv L777-780; runner argv L850-860 (`--network container:<pgc_id>`,
  RO mounts, P6DIAG_* env); readiness target 127.0.0.1:5432 (L808/L832)

## 3. Phase B — the ONE approved launch (actuals)

Approval `root-e-one-fixed-cohort-execution-approval.json` (13:59:44Z,
APPROVED_ONE_FROZEN_E_FIXED_SDK_COHORT). Exact command `sh
/tmp/oap-083-8-e/p6diag-launch.sh`, direct exec, NO pipe/echo/chaining/
wrapper. SAME tool handle 92486 retained to terminal; tool native 1 IS
the launcher/controller native. Launcher actual call 14:00:23.159Z,
terminal 14:01:38.237Z (root-measured); controller 14:00:23.269Z ->
14:01:30.564Z; `OVERALL=1 EXIT=1`.

### 3.1 Preflight (all native 0)

gate wt status/head/tree exact Ie; no stale 0838e names; both image IDs
exact; `PREFLIGHT_OK=True`. start.txt: HEAD/TREE = Ie exact; all 4
manifest hashes + controller-start hash exact; corrected START labels
present (section 2.3); PGPASSWORD `<redacted:set>` (fake
`qualification-admin`).

### 3.2 Attempt 1 (sdk) — STALL_REPRODUCED

Fixture (all native 0, in-budget): volume
`0838e-20261027T140023Z-2353808-pg1`, PG
`cff197d076fbd74a89dd26519d643e90a5cd6178df188ae36be7f333ccfd45c0`,
runner
`defe2233fa7c2fbcc6eba7d4cd63eefdd7d005a2da04989b700366aa36f53a11`.
PG 16.15 identity OK (db=postgres user=postgres port=5432), system
identifier `7701347192664838184`; network `container:<PGCID>` verified;
runner running.

SDK arm (runner stdout, timed phases): setup -> fixture-ready (schema
`qw8_d9ff44218983`, reviewer role `qw8_reviewer_d9ff44218983`) ->
window-open pid 125 (idle in transaction, 71 locks) -> terminate-window:
`asyncpg InterfaceError: cannot call Transaction.rollback(): the
underlying connection is closed` (sqlstate absent; LAST 3 frames, not
the original first-query exception; server-side kill logged
14:00:29.131Z) -> canonical-restored OK -> **restored-pending-enter
STALL**: owned task pending at t_mono 32.914s (`__aenter__`,
contextlib.py:214).

### 3.3 NEW actual phase — observer EXERCISED (first time)

At t_mono 32.915s, BEFORE cancel: CPython 3.13.14 + builtins
`coroutine_wrapper` type guards matched; exactly ONE owned referent,
exact `CoroutineType`, recovered. Inner chain: `asyncpg/pool.py:896
_acquire` -> `:879 _acquire_impl` -> `asyncio/queues.py:186 get` ->
`FutureIter` (terminal await target). Pool counters size=0 idle=0
closing=false; old PoolConnectionProxy closed=true; listener events [];
admin role activity rows=[], pid 125 locks 0, role locks 0 (supplementary,
not cause proof). Then cancel + bounded drain (done=true cancelled=true);
post-drain pool 0/0, proxy closed, canonical-after-drain clean. Source
identities hashed by root: `pool.py` `abc7101d…`, `queues.py` `9ce87bf6…`.

### 3.4 Unsafe cleanup marker — the authorized STOP

`DIAG_UNSAFE_CLEANUP=1`: bounded owned-fixture `pool.close()` FAILED
within its 30s bound at t_mono 63.351s (`RuntimeError: owned fixture
cleanup failed: reviewer-pool: pool.close() failed within 30s:
TimeoutError`, module L613). Arm outcome `STALL_REPRODUCED`, codes [5,
7], `exit_code=5`. Controller: `child_exit=5` (docker wait stdout `5`),
`wait_cli=0`, terminal inspect exit 5, `cleanup_safe=True`,
`in_budget=True`, `body_exception=False`, `pg_evidence=ok`,
`mount_evidence=proven`, `evidence_degraded=False`. STOP law: recorded
unsafe marker STOPS remaining cases even with primary native 5 ->
attempts 2,3 PREVENTED (fixed max 3; run-all-3-only-if-prior-safe).

### 3.5 Owned disposal (SAFE, distinct from the FAILED SDK fixture close)

Both raw streams + Mounts captured BEFORE each container deletion (run
stdout 7815B `7456c75b…` / stderr 85B `2beaee4b…`; pg stdout 2304B
`9564b22d…` / stderr 1364B `600b2cd5…`); volume label
`{"oap0838e.rid":"20261027T140023Z-2353808"}` + Mountpoint proven before
volume deletion; run/pg/vol stop+rm native 0 with ABSENCE PROVEN (empty
exact list reads); no residual; no post-deadline recovery needed; END
source guard ok (HEAD/TREE = Ie); `EVIDENCE_DEGRADED=False`. Independent
post-check: no containers/volumes/owned procs; foreign 23 volumes
untouched; all 5 source hashes exact after run.

### 3.6 Evidence

Run dir `/tmp/oap-083-8-e/run-20261027T140023Z-2353808/`, TWELVE files,
preserved with hash manifest (section 11). Root FULL-read all 12 raw
files + source (closure 14:07:18Z).

## 4. Interpretation — localization only, not cause

Established (this request, at the snapshot): the owned restoration
request was suspended in `pool._acquire` at a `Queue.get`; it had not yet
received a PoolConnectionHolder and had not reached ch.acquire/connect.
This is the ACTUAL observed queue-wait phase, not a source expectation; no
universal "never delivered" claim and no inferred queue/Future state.

Upstream source lead (informational, NOT proof): official asyncpg issue
`#1307` (connection pool deadlock) fixed in merged PR `#1324`, commit
`4a83cc2f2eb2f3445aa181d2d0da9e9559e08aa6` (2026-09-21), released in
v0.32.0 (2026-10-06); the fix closes the holder.release bare-return path
with a public `conn.terminate` then return (`asyncpg/pool.py` +4/-2).
Installed product pin `asyncpg==0.31.0` (pyproject; foundation 0.2
metadata only requires asyncpg>=0.29 for its optional sqlalchemy extra)
— UNCHANGED. Strong candidate
consistent with the observed queue-wait phase, but NOT proof of our
abort/cause: the full window exception chain was not retained (only last
3 frames), holder/queue internals unproven, and no upgrade/patch/retest/
import is authorized in e.

NOT proven (root closure): exact queue size at observation / future
resolution state / holder `_in_use`; a leaked slot or missing callback;
precise SDK vs driver vs fixture causal owner; `pool.close` inner wait
phase (the generic close timeout localizes neither); timing cause,
version determinism, data loss, final qualification. Pending/
replacement/GUC final oracles NOT qualified due to failed entry. The
I2 QPG4 hung/native-UNKNOWN episode remains a separate historical
unknown (correction 3). A real observed inner chain is localization, not
causation or qualification.

## 5. D-report corrections (applied here, never rewriting d)

1. Defensive observer containment does NOT prove no added elapsed time,
   universal 5s completion, or guaranteed log emission; failure-fact
   emission is best effort.
2. "No import/preflight/DB trial at any point" (d section 2.3) means
   OUTSIDE the approved launch; the actual approved launch included
   preflight, SDK imports and an owned DB fixture (true for e as well).
3. I2 QPG4 hung/native UNKNOWN is NOT localized P6 proof; known actual
   P6 includes I3 QPG5 PG16 and indexed CI/c failures. Failures and
   unknowns preserved, no history rewrite.
4. No-skips/order-exact confirmations are limited to the authorized d/e
   checks; the initial 6-line overrun (d) is disclosed there, e's
   initial 5-line overrun is disclosed here (section 6); original gates
   NOT RUN remain outstanding (section 8).
5. The d run has TWELVE files, not 13 (root checkpoint miscount; actual
   manifest and live count agree 12).
6. Actual d publication: initial `os.S_ISFIFO` AttributeError BEFORE
   open (0 bytes sent); corrected stat helper then sent ONE 4f4b+EOF.
   Initial contents-API 404 omitted the ref; corrected explicit S_d
   bytes proof BEFORE OK, no repeated push. Actual natives kept.
7. Per-check concrete evidence index for the current implementation head
   is provided in section 7 (names/states for all 30 checks); aggregate
   counts alone do not replace check proof.

## 6. Procedure deviations (disclosed, no retroapproval)

- e: initial 5-line harness overrun (v1 1255 vs original 1250), written
  before the prospective request; REMAINS a deviation, not
  retrospectively approved. v2 = 1260 within the prospective 1270 (delta
  +5 within root's expected 0..6).
- e: v1 forecast misstated the applied delta as +9/-6; actual +11/-6
  net +5. Metadata-only correction after root FULL-read (new artifact
  hashes disclosed in scratch); no source edit, no extra check.
- e: a standalone host helper (`e_v2_compute_common`, host python
  3.14.4) was imported ONLY to build/verify candidate text for the v2
  edit — a mechanical edit-helper import, DISTINCT from any SDK/runtime
  import; its `__pycache__/…cpython-314.pyc` preserved in scratch. No new
  runtime helper, wrapper, or execution wrapper was added in e.
- Inherited, recorded in c/d reports (not re-adjudicated): c
  run1-exec.sh 11-line runtime wrapper + duplicate baseline statics
  deviation; d publication FIFO/contents-API corrections (correction 6);
  d run file-count correction (correction 5).

## 7. CI index at implementation head Ie (live, per-check)

Per-check index at Ie from root-saved `root-e-Ie-check-index-with-apps.json` +
`raw-check-runs-with-apps.json` (observed 2026-10-27T14:27:18Z; matches root
13:53:22 counts 22/8; all 30 completed; corroborated by the executor's direct
live check-runs fetch ~14:11Z with the same 30 states):

| check | state | app |
| --- | --- | --- |
| Analyze (actions) | success | 15368 |
| Analyze (javascript-typescript) | success | 15368 |
| Analyze (python) | success | 15368 |
| CodeQL | success | 57789 |
| Compose and edge packaging | success | 15368 |
| Dependency review | success | 15368 |
| Detect supported languages | success | 15368 |
| Foundation PG Group A PostgreSQL 14 | success | 15368 |
| Foundation PG Group A PostgreSQL 15 | success | 15368 |
| Foundation PG Group A PostgreSQL 16 | success | 15368 |
| Foundation PG Group A PostgreSQL 17 | success | 15368 |
| Foundation PG Group A PostgreSQL 18 | success | 15368 |
| Foundation PG Group B PostgreSQL 14 | failure | 15368 |
| Foundation PG Group B PostgreSQL 15 | success | 15368 |
| Foundation PG Group B PostgreSQL 16 | failure | 15368 |
| Foundation PG Group B PostgreSQL 17 | failure | 15368 |
| Foundation PG Group B PostgreSQL 18 | success | 15368 |
| Foundation PostgreSQL 14 | failure | 15368 |
| Foundation PostgreSQL 15 | failure | 15368 |
| Foundation PostgreSQL 16 | failure | 15368 |
| Foundation PostgreSQL 17 | failure | 15368 |
| Foundation PostgreSQL 18 | failure | 15368 |
| Markdown | success | 15368 |
| Mermaid | success | 15368 |
| Node contracts | success | 15368 |
| Python 3.12 quality and package | success | 15368 |
| Python 3.13 quality and package | success | 15368 |
| Python 3.14 quality and package | success | 15368 |
| Repository policy | success | 15368 |
| Supply-chain evidence | success | 15368 |

The 8 failed children at Ie, named exactly: Foundation PG Group B
PostgreSQL 14/16/17 plus the five required Foundation PostgreSQL
14/15/16/17/18 aggregators (aggregators fail closed from entire A/B needs;
five aggregators failing closed is NOT "five more engine failures"). The
a/c-round raw logs are I2/I3 job evidence, NOT Ie job logs; no same-P6-
signature claim is made for the actual Ie failures here. Independently
proven P6 safety-family failures remain: I3 CI (PG15/16), S_d/c runs, and
e attempt 1 (section 3). Merge gate (effective main ruleset 20934043): 20
strict required (app 15368, except CodeQL app 57789) AND 10 actual PG
children success AND strategic satisfaction — not all green; never cured
by luck.

## 8. Original gaps (no waiver)

- Original qualification PARTIAL: a P1-P7 NOT qualified by this
  diagnostic; fresh final ALL31 + supply-chain/broader Ruff + complete
  fresh QPG14..18/FULL PG18/separate P7 remain NOT RUN in e (original
  gates outstanding).
- Known actual P6 failures preserved (immutable history, no rewrite):
  I2 CI (P2/P4 oracle + P6), I3 CI (PG15/16 P6 + 1 teardown error),
  Ie CI (section 7), I2 QPG4 hung/UNKNOWN (not P6-localized), and the
  a/b/c diagnostic rounds.
- Full planned product still pending (U TRUE closure / COMPLETE
  3-family semantic audit / exact committed==U / no pending INSIDE
  reviewer / durable timeline+resource DIFF after pending cleanup;
  084 conflict-safe through 091 hostile-MVP; 18 fields; reviewer forms;
  Apache HTTP contract; failed-FREEZING recovery; leases; safe BYTE GC;
  retained media; backups) — see a-report original-contract section; no
  re-listed wall here.
- Security: repo alert 17 withdrawn (native gh 1/HTTP 410); global
  GHSA-6q48-6c7w-9gw2 ACTIVE (first-patch 2026.10.18 / range <18;
  official text recommends 2026.10.19); 13 other open repo alerts, 0
  critical. No fixed-by-merge or release claim.
- Foundation `agent-cow-postgresql==0.2.0` registry hashes/pins
  preserved; product pin `asyncpg==0.31.0` installed UNCHANGED (upstream
  0.32.0 fix = candidate lead only, section 4); CfT-versus-host browser
  identity preserved; product release state remains pre-alpha/honest-
  unqualified (`early-beta` is the coding-agent profile, NOT a product
  release claim).

## 9. Confirmations

- `AMENDED_EXISTING_PR112`; no new PR; no merge/auto-merge/close/
  acceptance; no protected-ref edit; this report does not accept or merge.
- Scope: zero product/src/web/browser/media/contract/migration/roles/
  grants/credentials/dependency/lock/image/browser/action/scanner/
  license/authority/egress/policy/publication change; production/
  migration/lock/dependency/authority changes 0. Hard caps unchanged and
  met (measured at Ie): test/CI code 1896 <= 3000; docs 154 <= 500;
  transcript 3824 (orders 1429 + reports 2393 + active 2) counted as
  mandatory immutable orchestration; total 5874.
- human3 preserved in the ORIGINAL product checkout: `.codex/`,
  `CODEX-SESSIONS.md`, `codex.sh` untracked and untouched; original checkout
  raw status = complete 132624B `2822a3ec…` = human3 only, while gate-wt
  raw status is EMPTY 0B (root 13:53:22).
- Secrets: fake `qualification-admin` rendered `<redacted:set>`; no real
  secrets, capabilities, cookies, DB URLs, or private artifact URLs in
  this report or in committed scratch logs.
- No skip/xfail/catch-to-pass/subset/tuple-count tautology/publication
  workaround; no rerun-until-green; no rerun for old receipts; no
  baseline/help/control/variant repeats.
- No signal replay; ONE response OK after remote proof; exactly ONE
  byte-retaining control reader opened after the OK (bytes/EOF/status
  captured separately).
- This diagnostic is NOT qualification, NOT cause closure, NOT merge
  permission; root alone reviews/accepts/merges/chooses the next scope.

## 10. Publication procedure (exact, same-file atomic)

- Temp written INSIDE `oap/reports/` (same filesystem):
  `.083-8-e-sample-owned-pool-await.md`, then exact repo lint
  `npx --yes markdownlint-cli2@0.23.2 --config .markdownlint-cli2.jsonc
  --no-globs <file>` with Node v24.22.0 tool PATH: native 0, 1 file,
  0 issues in 0 files (re-linted after any edit; receipts in
  `/tmp/oap-083-8-e/`).
- Pre-Git sha256/inode/size/UTC+raw-ns recorded; fsync of the temp;
  SAME-file atomic rename to `083-8-e-sample-owned-pool-await.md`;
  parent directory fsync; post-rename sha256 match.
- Staged EXACTLY one path (`git diff --cached --name-status` full-line
  checked = this report only, no M/D); HEAD asserted literal Ie before
  commit. Commit message: `083-8-e: publish OAP 083-8-e execution report
  (report-only SELF, PARTIAL)`.
- SELF verified: sole parent Ie; sole changed path this report; blob
  bytes equal local sha256; 19 cumulative paths at SELF (measured, order
  expected 19).
- Pushed (native captured directly, no pipe); remote proof BEFORE the
  response OK: `git ls-remote` head = SELF; gh API commit parents =
  [Ie], files = [this report]; PR head = SELF; remote raw content
  sha256 = local.
- ONE exact 2-byte ASCII `OK` (hex `4f4b`), no LF, written and closed on
  the actual strategic response FIFO (inode 4470112 verified before
  write); no replay.

## 11. Evidence index (paths retained, immutable)

- Scratch `/tmp/oap-083-8-e/`: frozen 5-file bundle (section 2.2
  hashes); `pre-v1/` (d bundle `e29be205…`/`1f1023ca…`) and
  `pre-v1-clarification/` (v1 `7eb7e916…`); v1/v2 freeze records +
  forecasts; `e-v2-clarification-diff.txt`; compute/apply edit receipts
  (pre-write compute, guarded atomic apply); statics logs + native
  ledgers + env record; `e-runtime-metadata-record.txt`; all `root-*.
  json` receipts; control receipt (reader 31092, 2 bytes `4f4b` + EOF).
- Run evidence: `run-20261027T140023Z-2353808/`, TWELVE files —
  `start.txt` `0de420b1…`, `sdk-attempt1.log` `8025fae9…`,
  `sdk-attempt1-raw-receipts.log` `45910902…`, `overall.log`
  `8beb7cbf…`, `end.txt` `72534bdc…`, `finalize.log` `566ce925…`,
  `finalize-raw-receipts.log` `84c90f65…`,
  `preflight-raw-receipts.log` `a51467c5…`,
  `rescue-sdk-attempt1-run.cli-stdout` `7456c75b…` (7815B),
  `rescue-sdk-attempt1-run.cli-stderr` `2beaee4b…` (85B),
  `rescue-sdk-attempt1-pg.cli-stdout` `9564b22d…` (2304B),
  `rescue-sdk-attempt1-pg.cli-stderr` `600b2cd5…` (1364B).
- Upstream artifacts (root-provided, read-only): `upstream-1307-issue.
  json`, `upstream-1307-timeline.json`, `upstream-1324-pr.json`,
  `upstream-1324-files.json`, `upstream-1324-commit.json`,
  `upstream-latest-release.json`, `upstream-fix-in-v032-release-
  comparison.json`.
- Prior-round scratch (a/b/c/d) and all prior orders/reports preserved
  unchanged; d-report 389L `04a528d0…` immutable; foreign 23 volumes
  untouched.
