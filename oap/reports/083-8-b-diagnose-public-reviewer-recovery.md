# OAP Coding-Agent Report — 083-8-b

## Work order

- Identifier: 083-8-b (objective 083, increment 8); work-order file
  `oap/orders/083-8-b-diagnose-public-reviewer-recovery.md` (257L,
  16433B, SHA256
  ff14b18bc76bb13e8d0e5eb7cc112d5178b053d44157a97b7e16df529776e463),
  FULL-read including the exact report-handoff section.
- Activated `oap/active`: 8 bytes, hex 3038332d382d620a
  ("083-8-b" + LF), committed unchanged at Ib.
- PR mode: AMENDED_EXISTING_PR (PR 112, same named branch).
- Mode: DIAGNOSTIC_ONLY_PUBLIC_P6. The original increment remains
  PARTIAL/unaccepted; no production or qualification-test repair is
  authorized or performed in this round.

## Status
PARTIAL — the approved diagnostic cohort produced ZERO P6 data:
both approved invocations were NOT RUN (first = preflight
subject-drift refusal; second = harness NameError before the first
runner child was ever created). The original P6 safety-contract
failure at frozen I3 (unchanged at Ib) remains unresolved; per the
root close decision this round makes no third launch, no source fix,
no rerun, and no workaround. All original a final gates and the
full-product roadmap remain unqualified.

## Executive summary
Ran the b diagnostic exactly as root approved: Phase A produced the
frozen five-file scratch bundle (995 diagnostic lines + 1176 harness
lines, all root FULL-reviewed, final native statics native 0), and
root approved exactly ONE invocation of `sh
/tmp/oap-083-8-b/p6diag-launch.sh` (no pipe) for the fixed cohort of
ONE direct-driver control plus EXACTLY THREE SDK-path attempts on
owned PG16, SERIAL, fresh owned fixture per attempt, 180s each.

Invocation 1 (09:52:38.817..09:52:39.165Z) was refused by the
controller preflight: the isolated gate-wt still sat at stale I3
while the declared subject was Ib (launcher native 1; zero
fixture/driver/SDK cases; zero resources). Under the root-approved
finite setup correction (09:57:24.574558Z) the clean gate-wt was
aligned to Ib (`git checkout 53895c15`, native 0; only three
transcript leaves differ I3->Ib). Invocation 2
(09:59:31.062..09:59:34.457Z) passed preflight at Ib, built the whole
owned PG16.15 fixture (labeled volume + container, identity,
sysid), and then hit a harness NameError (`arm` undefined at
`p6diag-controller.py` line 783) BEFORE the runner child argv
completed. The controller correctly classified
`harness-exception`/`body_exception=True`, PREVENTED the remaining
attempts, and cleaned up safely in budget (PG stop0/rm0/absence
proven; labeled volume label+Mounts captured pre-deletion, rm0,
absence proven). Actual driver children started: 0. Actual SDK
children started: 0. No P6/SDK/driver causal data exists from this
round; the original P6 cause remains UNKNOWN.

Fresh live CI at Ib (23 success / 7 failure / 0 pending at report
drafting): the two actual engine failures are Group B PG17/PG18
(each 1 failed, 15 passed, 1 error in the 16-test module — the same
known I3 P6 failure); the five "Foundation PostgreSQL 14..18" jobs
are the documented fail-closed aggregators. This report corrects the
a-report errors listed in the order (D5) without editing the
immutable a-report, carries all a errata, and records the two b
invocations with full native/log/status/cleanup evidence.

## Authoritative GitHub state

- Repository: ulfe-lmi/slaif-agent-site; PR 112
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/112>, state
  OPEN, unmerged (merge performed NO by coding); mergeable at
  report drafting.
- Base branch main; verified remote main
  d18b6e4c9423f61de99b516be90619bf2ab5d3e0 (PR #111 merge, 083-7-b).
- Head branch oap/083-8-a-qualify-public-whole-session.
- Implementation head SHA: 53895c15d36ef0766cd81a69938d0e20db0aac9a
  (tree 79ccba1fb155f24027209a7111c2ee5aa51b2a3e); pushed;
  `git ls-remote` equals local HEAD, re-verified at report
  drafting. This round adds zero product/test/CI/docs bytes, so the
  b transcript commit is the literal implementation head Ib.
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via
  GitHub)
- Append-only history since accepted main: the full a implementation
  commit list is recorded in the immutable a-report. b adds exactly
  two commits: e7b15f97fe7fc0b353590012ff956407013ca952 (S_a: a
  report publication, sole path a-report, 627 insertions, parent I3
  f6f32c08c4d340c17d5db6bacc08a4852c562bc9) and Ib
  53895c15d36ef0766cd81a69938d0e20db0aac9a (b-order 257 insertions +
  active 1+/1-, parent S_a). No amend/reset/rebase/force-push.
- New PR this turn: no. Amended existing PR: yes (report only).
  Merge performed: NO.

## Changes made

- ZERO product, test, CI, docs, lock, migration, dependency, image,
  or behavior changes in this round. The only new committed b path
  is this report (SELF commit); the b-order and active are already
  committed/pushed at Ib.
- Uniform minimal accounting (git numstat = CHANGED LINES, per D5
  correction 1): at S_a the PR touched 11 paths — code 1896
  (ci.yml 10 + module 1844 + test_foundation_ci.py 42), docs 154
  (docs/ 145 + oap/INCREMENTS.md 5 + oap/MVP-PROGRESS.md 4),
  transcript 1099 (a-order 470 + active 2 + a-report 627). Ib adds
  the b-order (257) and rewrites active (1+/1-): 12 paths. This SELF
  commit adds this b-report: 13 cumulative paths, exactly the
  order's "cumulative 13 paths without helper" (11 previous + 2 new
  transcript paths).
- All eight a code/CI/docs delta paths are BYTE/MODE/TYPE unchanged
  at Ib (root-verified complete leaf mode/type/blob maps I3->Ib;
  the frozen P6 module equals I3 bytes
  45cf79671261212c19143315daeaecfc1b01b1e48d0b3c2cdf9e85cf881563a8
  at both heads).

## Phase A: reviewed frozen diagnostic bundle (D1)

- Frozen five-file scratch bundle in /tmp/oap-083-8-b (outside Git),
  re-verified byte-identical at report drafting:

| file | lines | SHA256 |
| --- | --- | --- |
| p6diag-common.py | 325 | a0fd629f0f20f9b9357b7b018b7227b385ed6c29b0883721819da6a3ddfc90a2 |
| p6diag-driver-arm.py | 263 | b5af2868bbf0288f1eac6b064cfa4441d4813b16280eea8d22509eed56dac87d |
| p6diag-sdk-arm.py | 407 | 2ec67cccf403bfeb1958a7dbacf77ed5b85373c29a0e33eccd7e7629929eb250 |
| p6diag-controller.py | 1170 | bc381dae4ddf627b7504b4ad68b031a05e9c08c01b84243556f429751b07a3dc |
| p6diag-launch.sh | 6 | 0f1e69ec2378d54392a26f6e677718d48c52b3869a75b031e197b0235ece8e7d |

- Line accounting (root-approved, no packing): diagnostics
  common+driver+SDK = 995 within the prospective 1000; harness
  controller 1170 + launcher 6 = 1176 within the prospective 1250.
- Review history: root FULL-read every controller revision (six) and
  all arm deltas; the final 1170L bc381dae controller passed as
  full bases plus all intervening deltas. Final native statics
  (44L receipt SHA256
  a6f98e4fe9f3100f7713534be9ce4a1148226d5f9fe0f7f09e4eb9485a132866,
  actual 09:42:47Z tool call): target venv CPython 3.13.14
  `py_compile` on all four .py files, `sh -n` and `dash -n` on the
  launcher, plus the limited AST pass — each individual native 0.
  Host 3.14.4 statics are recorded separately. Syntax/AST/source
  review is NOT runtime qualification.
- Root execution approval 2026-10-27T09:49:46.502671Z
  (strategic-b-final-bundle-execution-approval.md): exactly ONE
  invocation, fixed cohort 1 driver + 3 SDK on owned PG16, SERIAL,
  fresh owned fixture per attempt, 180s absolute outer budget EACH
  including fixture/observations/cleanup, original 30s phases,
  aux <=5s, hard cleanup reserve 30s inside 180s, ANY
  unsafe/setup/evidence/unknown STOP, no fifth attempt or variant.

## Diagnostic execution record (both approved invocations)

Both invocations are NOT-RUN as diagnostic cases. ZERO
P6/SDK/driver causal data was produced this round. All timestamps
UTC. The fixed cohort (1 driver + 3 SDK) ran 1 of 4 attempt slots,
which itself produced no case data (harness failure before runner
creation); the remaining slots were PREVENTED by the controller
fail-stop.

### Invocation 1 — preflight subject-drift refusal (not-run)

- Approved invocation `sh /tmp/oap-083-8-b/p6diag-launch.sh` (no
  pipe), executed ONCE; launch-pre 09:52:32.440783491Z; actual
  session window 09:52:38.817..09:52:39.165Z; immediate
  LAUNCHER_NATIVE_EXIT=1. The surrounding echo shell exited 0 —
  that is NOT launcher 0.
- Controller rid 20261027T095238Z-2029253: internal START
  09:52:38.932Z, END 09:52:39.139Z, OVERALL=1.
- Preflight FAILED (fail-closed, by design): isolated gate-wt HEAD
  f6f32c08.../tree 9051dfd5... (stale I3) against declared subject
  Ib 53895c15.../tree 79ccba1f... — `PREFLIGHT_OK=False`,
  `END_SOURCE_GUARD=FAIL`, "PREFLIGHT FAILED: no attempt launched".
- Accounting: 0 fixture setups, 0 driver cases, 0 SDK cases;
  resource ledger RES run/pg/vol all None; no container, volume, or
  runner created; before-start authoritative Docker list native
  0/empty.
- Classification: harness setup failure (subject drift). It is not
  a test result and was not relabeled as PASS or as a
  driver/SDK failure.
- Evidence: run-20261027T095238Z-2029253/ (hashes below); end.txt
  SHA256 4270320d31d16825c270f61cc75ce26553a6b9c34c4457eee35e5d05a9ab082c.

### Root-approved finite setup correction (09:57:24.574558Z)

- Root independently compared the COMPLETE Git leaf mode/type/blob
  maps I3->Ib: ONLY three transcript leaves differ —
  `oap/active`, the b ORDER, and the immutable a REPORT. Every
  other path (code, locks, migrations, runtime/setup/harness
  inputs) is EXACTLY equal. (The first-invocation receipt's
  "083-8-a order" label for the third leaf is a mislabel; see
  Errata.)
- Approved action: align the EXISTING CLEAN isolated gate-wt to the
  already-required Ib — routine preparation for the originally
  declared subject, not product implementation. Executed as
  `git checkout 53895c15` (native rc=0; no reset/force/clean/
  rebase/amend).
- Post-alignment record: HEAD 53895c15 / tree 79ccba1f / clean;
  frozen module 45cf7967... unchanged; target venv CPython 3.13.14
  intact; all five approved script hashes unchanged.

### Invocation 2 — preflight passed; harness NameError before runner (not-run)

- Same approved invocation, executed ONCE (second of max two);
  actual session window 09:59:31.062..09:59:34.457Z; immediate
  LAUNCHER_NATIVE_EXIT=1; surrounding echo shell 0 (not launcher 0).
- Controller rid 20261027T095931Z-2035102: internal START
  09:59:31.180Z, END 09:59:34.440Z, OVERALL=1; `PREFLIGHT_OK=True`
  at Ib; `END_SOURCE_GUARD=ok`; frozen 5-hash manifest re-asserted
  in start.txt.
- Attempt 1 (direct-driver arm) — owned fixture setup COMPLETED:
  - Owned labeled volume
    `0838b-20261027T095931Z-2035102-pg1`
    (label `oap0838b.rid=20261027T095931Z-2035102`) created native
    0.
  - Owned PG16 container
    a5418a083c49057bd9f6ac015175b1d5da39da2cef0989e1bad583b57168d646
    created native 0 from image
    sha256:0cefaabd882e42bcb2a2f3dc56d3ce4770560ba62fd7f197f1a2e008fd5731ab
    (postgres:16-alpine); State.Running=true; container image
    equality verified.
  - pg_isready: rc=2 for probes 0..6, rc=0 at probe 7
    (09:59:33.720Z).
  - Identity via owned admin psql (native 0):
    version=16.15 db=postgres user=postgres port=5432;
    `pg_control_system().system_identifier` = 7701285121614880808.
  - Runner baseline read: absent (create=not-attempted).
- BODY-EXCEPTION raised BEFORE the runner child argv completed
  (full traceback retained in driver-attempt1.log):

```text
Traceback (most recent call last):
  File "/tmp/oap-083-8-b/p6diag-controller.py", line 595, in attempt
    attempt_body(ctl, b, log, res, vol, pgc, runc)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/oap-083-8-b/p6diag-controller.py", line 783, in attempt_body
    RUNNER_EXPECT_ID, RUNNER_PY, f"{SCRATCH}/p6diag-{arm}-arm.py"]
                                                     ^^^
NameError: name 'arm' is not defined
```

- Root cause: harness/controller defect, NOT a product or SDK
  failure. `attempt_body` (line 650) has no `arm` parameter and its
  call site (line 595) does not pass it, while line 783
  interpolates `f"{SCRATCH}/p6diag-{arm}-arm.py"` into the runner
  argv; `arm` exists only in the caller `attempt(ctl, n, arm)`
  (line 562). The latent undefined name is invisible to py_compile
  and to source review; it surfaced only on execution. The
  identified 2-line arm-plumbing fix is DEFERRED to root's next
  bounded round and was NOT applied in b (no scratch repair in b
  per the close decision).
- Accounting: fixture-setup attempts 1; ACTUAL driver children
  started 0 (the runner was never created); ACTUAL SDK children
  started 0; no P6/SDK/driver causal data; original P6 cause
  remains UNKNOWN.
- Controller fail-stop classification (worked as designed):
  `state=harness-exception`, `body_exception=True`,
  `continue=False`, "remaining attempts PREVENTED",
  `child_exit=None`, `wait_cli=None` — recorded None because no
  runner was ever created (not UNKNOWN), `OVERALL=1`.
- Raw streams: both PG rescue streams retained pre-deletion
  (cli-stdout 2304B SHA256
  74c54f235292678163e1fa6886e7d83e61ecd98f2a8c98669d0f1fbc05ef29d4;
  cli-stderr 897B SHA256
  95450248099a6746b8e5f0e5af95e2f83923a47e417d62057270c0c2ce718805);
  full per-step receipts (cmd/rc/stdout/stderr/timestamp) in
  driver-attempt1-raw-receipts.log.
- Evidence: run-20261027T095931Z-2035102/ (hashes below); end.txt
  SHA256 613acd1d0e6dd577c1ca64df5170b8a79231061374f60235d337e75c975c22e1.

## Cleanup and residual state (owned only)

- Invocation-2 cleanup was SAFE and complete, within the SAME
  attempt deadline (`cleanup_safe=True`, `in_budget=True`), every
  command native 0:
  - PG: rescue logs + Mounts captured BEFORE deletion; `docker
    stop` 0; `docker rm` 0; post-deletion presence check =
    successful list read with exact empty result (ABSENCE PROVEN).
  - Volume: labels + Mountpoint captured BEFORE deletion
    (`oap0838b.rid=20261027T095931Z-2035102`;
    /var/lib/docker/volumes/0838b-20261027T095931Z-2035102-pg1/_data);
    `docker volume rm` 0; post-deletion list empty (ABSENCE PROVEN).
  - Runner: not attempted; never touched.
  - Final residual-name Docker lists native 0/empty; finalize
    recorded "no residual owned/attempted resources; no
    post-deadline recovery performed"; END source guard re-read
    Ib/tree clean.
- Read-only absence re-verified at report drafting (~10:15Z):
  `docker ps -aq --filter name=0838b-` empty (rc=0); `docker volume
  ls -q --filter name=0838b-` empty (rc=0). No residual owned
  resources from either invocation.
- The 23 earlier unattributed anonymous volumes (a round) remain
  UNTOUCHED; no global prune, no foreign volume, no foreign PID, no
  foreign DB/role touched in this round.

## Evidence inventory

- /tmp/oap-083-8-b/run-20261027T095238Z-2029253/ (invocation 1):

| file | bytes | SHA256 |
| --- | --- | --- |
| start.txt | 1817 | aa25b158256d06bfab86c6b9251cd089f2e6d0b14922f75c255238732655a7c0 |
| overall.log | 1079 | dbcae1520c0460d260548d2992baacb8a4d71cf9f5682a68d27ce7d85b3b3ba5 |
| preflight-raw-receipts.log | 1228 | 9bdc6197c106c506a3c886234ef1db5228f4d780f3fe38285d85980572d41e9d |
| end.txt | 139 | 4270320d31d16825c270f61cc75ce26553a6b9c34c4457eee35e5d05a9ab082c |
| finalize.log | 724 | 1222a41290f689f9742c380749dfd29a540efbe5568b776e00dcfa55d3d655e9 |
| finalize-raw-receipts.log | 606 | e307abb7351630f0770e5caef14b8f03304b6834ae38ff6d279dfcf3cd971f98 |

- /tmp/oap-083-8-b/run-20261027T095931Z-2035102/ (invocation 2):

| file | bytes | SHA256 |
| --- | --- | --- |
| start.txt | 1816 | ed1989717422e28875d99c587aac40f4537c5fad363454c52cebbd00fb06e229 |
| overall.log | 1257 | d64a4b0af5c6dafc410a269f56246ed9fce087b5ca8e4f9fcb0f5912f84cec19 |
| preflight-raw-receipts.log | 1228 | 2a3e3a50593f204cafc05792ed6d888a074e02ed3fc96db48cd813cebadb78b4 |
| driver-attempt1.log | 4928 | 83e42ac766a45edf3f53057a90b3c34d7fd2360144406211b965e2d6bb0abb0b |
| driver-attempt1-raw-receipts.log | 7203 | a8591fc7d299a14ae9ac2ac4f5bcee01659adb1d9dc7ce5ebc7c20854dba9bbc |
| rescue-driver-attempt1-pg.cli-stdout | 2304 | 74c54f235292678163e1fa6886e7d83e61ecd98f2a8c98669d0f1fbc05ef29d4 |
| rescue-driver-attempt1-pg.cli-stderr | 897 | 95450248099a6746b8e5f0e5af95e2f83923a47e417d62057270c0c2ce718805 |
| end.txt | 663 | 613acd1d0e6dd577c1ca64df5170b8a79231061374f60235d337e75c975c22e1 |
| finalize.log | 464 | 398f43d34d9a9b84c827f13a58854a3375968b91563b1df1c4e1875b71c91910 |
| finalize-raw-receipts.log | 606 | 0b9968ccb722d104171eb47db1000ec7a35ff4c25d388997fb94515e6735b392 |

- Root manifests: strategic-b-second-invocation-harness-failure-
  review.json (invocation-2 independent review, 10:07:08.894712Z),
  strategic-b-actual-not-run-receipt.txt (invocation 1),
  strategic-b-actual-2nd-invocation-receipt.txt (invocation 2),
  strategic-b-phaseA-native-statics-receipt.txt,
  p6diag-phaseA-forecast.md, strategic-b-Ib-current-checks.json +
  strategic-b-Ib-checks-summary.json (07:30:55Z CI snapshot),
  strategic-Ib-CI-job-122057296148.log (171298B) and
  strategic-Ib-CI-job-122057295646.log (172489B) raw job logs.

## D1-D5 deliverable accounting

- D1 (exact reviewed script/harness identities, actual frozen
  source, passive observation boundaries, fixed four-attempt
  accounting): DONE (identity only) — five hashes/lines/argv/env/
  budgets above; passive observation boundaries preserved in frozen
  source (no frame locals/credentials ever dumped; admin SQL
  read-only on owned connection; counter/PID/listener observations
  bounded); fixed cohort 1 driver + 3 SDK with honest early stop:
  attempt slot 1 (driver) = harness-exception NOT-RUN (0 cases);
  slots 2-4 (SDK) PREVENTED by controller fail-stop; no fifth
  attempt, no variant, no adaptive rerun.
- D2 (each arm's original window evidence, exception, public
  recovery/pending/replacement outcomes, actual await/cleanup
  phase): NOT RUN — no DB case executed in either invocation; no
  await or cleanup phase observed; recorded UNKNOWN, not inferred.
  The only exception captured is the harness NameError above, which
  is not a P6/SDK/driver exception.
- D3 (evidence separating already-observed rollback from
  still-unproven pending/lock/GUC/recovery safety): unchanged from
  a — in the I3 failure the earlier canonical-absence/rollback
  assertions within the same test reached PASS before the
  restoration window; pending retention, clean replacement, and
  post-termination lock/GUC checks remain UNQUALIFIED. b reproduced
  nothing and non-reproduced nothing; per the order,
  non-reproduction does NOT close the original failure.
- D4 (exact native/log/status/source/cleanup accounting; no
  lucky-PASS erasure, no private SDK/SQL/workaround, no unapproved
  mutation, no foreign cleanup): DONE for this round — both
  invocations fully accounted above (windows, natives, logs,
  guards, IDs, cleanup, residual); the five frozen hashes
  re-verified unchanged at report drafting; gate-wt at Ib clean
  before and after; module bytes unchanged; zero committed path
  changes beyond this report; cleanup owned-only with absence
  proven; no prune/foreign resource touched.
- D5 (b report corrects the a-report errors WITHOUT editing the
  a-report): DONE — the six order-listed corrections are recorded
  in Errata below; a-report 627L/34043B SHA256
  6dfd6f536ab3c6550564df76ec2537390e4a3114cce1062d6f5bd3f14b036128
  remains immutable.

## Errata (recorded, not rewritten)

Carried from the immutable a-report (unchanged):

1. A pre-push --amend superseded a5f05 by 9dc0eb without
   authorization — both objects and their failed evidence are
   preserved, and the forward join J is the recovery, not a
   retroapproval.
2. The root forecast line "transcript 472" vs measured order 470L +
   active 8B = 478 (arithmetic). METRIC CORRECTION via D5.1 below:
   git numstat counts CHANGED LINES, and active is 1 add + 1 delete
   = 2 lines, so 470 + 2 = 472 pre-report was correct; the a
   erratum's byte-based 478 figure is superseded.
3. Draft clocks near 06:20Z were future guesses — actual tool times
   are recorded in the helper receipt (06:04:30Z import FAIL native
   1; 06:04:44.482..48.599Z native 0; commit I3 06:06:12Z).

D5 corrections from the b-order (applied in this report; a-report
not edited):

1. The uniform minimal numstat counts CHANGED LINES, not lines plus
   bytes. Verified here with `git diff --numstat d18..S_a`: a-order
   470 + active 1+1 = 472 pre-report; + a-report 627 = 1099
   transcript gross. The a SELF (e7b15f97) sits on 11 paths
   including the report, not 10. b cumulative listed separately:
   Ib = 12 paths; after this SELF commit = 13 paths.
2. CI15 job 122039337259 raw is 169648B / SHA256
   631d007fe2f7f1245dd1f989ef5b40eb6392657bb861483c9bc22c0cffd8590b;
   CI16 job 122039337087 raw is 171694B / SHA256
   64a4269ed9e94d9c93f84bb1532b5a356b02a8449b2d8cb0a1b2797c6b89f685.
   The a-report (lines 227-230) swapped the two byte sizes; the
   hashes and job identities remain distinct as recorded there.
3. The a-report P1 description ("asserts the installed public
   sources against the order-anchored wheel ... plus official
   metadata/non-yanked/license/artifact provenance") overstates the
   test. The actual P1 test (verified in the frozen module source)
   asserts: installed distribution version
   (importlib.metadata.version), metadata Name/Version/
   License-Expression fields, every qualified public API name on
   the product re-export surface, and the uv.lock package block
   (version 0.2.0, registry pypi.org/simple, wheel + sdist
   hash+size, no git/editable/directory). It does NOT assert live
   registry (non-yanked) metadata, and does NOT assert installed
   artifact byte identity. Official wheel/sdist provenance beyond
   the order anchors and the uv.lock pins is NOT re-verified in
   this round (and is not asserted at runtime).
4. The actual fresh-I3 supply-chain test units (within ALL31's
   unittest discover / pytest unit) and the broader CI ruff
   commands (`uv run --frozen ruff check` / `ruff format --check`
   over services/backend, tests/repository, tools) RAN as part of
   the fresh I3 ALL31 (31/31 EXIT=0, each named argv root-
   verified; indexed in the a-report "Local verification"). No
   separate fresh gate was executed at I3 merely to fill an old
   receipt.
5. P7 was NOT RUN; the 16-test module does not qualify P1-P7
   collectively. The public manager entry timeout does not by
   itself prove a pool.acquire await: root independently read
   asyncpg 0.31.0 pool.py — `acquire(self, *, timeout=None)`
   awaits the queue get with NO default deadline, and the SDK
   `asyncpg_cow_reviewer` calls `pool.acquire()` without a
   timeout; a generic timeout localizes neither holder-release
   nor connection-close.
6. The a-round wrong `oap/response.fifo` (product-repo path) open
   FAILED BEFORE any bytes were written; the actual strategic
   response.fifo (inode 4470112) received exactly ONE 2-byte OK
   (2026-10-27T06:50:25.788148Z; root reader 5883 TERMINAL0). No
   rewrite of the immutable a-report and no re-sent signal.

New b errata (recorded, prior receipts preserved immutable):

1. The first-invocation receipt
   (strategic-b-actual-not-run-receipt.txt) labels the third
   I3->Ib leaf "083-8-a order". The root-verified complete leaf
   mode/type/blob maps prove the three leaves are `oap/active`,
   the b ORDER, and the a REPORT — NOT the a-order. Corrected
   here.
2. In both invocations the surrounding echo shell exited 0 while
   the launcher immediate native exit was 1; the parent shell
   native must not be read as "launcher 0".

## Original P6/recovery and outstanding a gates

- Original P6 failure (frozen I3; unchanged at Ib — zero product
  bytes differ): after the test's pg_terminate_backend kills the
  reviewer pool's only connection, the public reviewer manager's
  post-termination restoration re-acquire
  (p6-restored-pending-enter) does not complete within the 30s
  bounded window, and the subsequent reviewer pool.close exceeds
  30s. Reproduced in CI I3 Group B PG15/PG16 and local QPG5 PG16;
  reproduced again in CI Ib Group B PG17/PG18 (below). The earlier
  canonical-absence/probe0 assertions in the same test reached
  PASS. Pending retention, clean replacement, and post-termination
  lock/GUC checks remain UNQUALIFIED. Cause remains UNKNOWN; the
  SDK (agent-cow-postgresql 0.2.0 / asyncpg 0.31.0) is unchanged
  and unpatched.
- This diagnostic round changes none of that boundary: zero cases
  executed, zero await-phase observations, zero reproduction or
  non-reproduction.
- All original a final gates remain required and UNMET: 20 strict
  required checks + 10 actual PG children + strategic satisfaction
  before eventual acceptance; fresh FULL PG18 NOT RUN (root STOP);
  P7 NOT RUN; green CI alone is insufficient.
- The full-product roadmap remains unqualified, retained verbatim
  from the a-report: immutable pending U / true closure /
  complete 3-family audit / exact in-transaction promotion /
  durable history; human D5 / 084 / 080 / 085..091; all 18 fields
  including repeatable_object; common desktop/phone forms /
  reviewer-only UI; actual Apache HTTP contract; lifecycle
  byteGC/recovery/backup; human release criteria. No preview-only
  substitute and no product-completion claim.

## GitHub CI / required checks (honest live state at Ib)

At report drafting (~10:15Z), at literal implementation head Ib
53895c15:

- CI run 40464700870 (workflow CI): completed/FAILURE 07:20:09Z.
- CodeQL run 40464700732: completed/success 07:04:35Z.
- Commit check-runs on Ib: 23 success / 7 failure / 0 pending.
- ACTUAL engine test failures (each: 1 failed, 15 passed, 1 error
  in the 16-test module, native 1, same P6 signature):
  - Group B PG17 job 122057296148 — 62.20s; raw 171298B retained.
  - Group B PG18 job 122057295646 — 62.25s; raw 172489B retained.
- The five "Foundation PostgreSQL 14..18" jobs are the documented
  fail-closed aggregators (each requires the complete A+B set for
  that engine); Group B PG14/15/16 PASSED at Ib, so these five
  failures are the barrier, not five engine test failures.
- Passing at Ib: Group A PostgreSQL 14..18, Group B PostgreSQL
  14/15/16, all CodeQL analyzers, Python 3.12/3.13/3.14 quality and
  package, Compose and edge packaging, Node contracts, Mermaid,
  Markdown, Repository policy, Dependency review, Supply-chain
  evidence.
- No acceptance, no merge, no qualification claim from any check;
  these states do not cure the independently proven P6 failure.

## Local setup / dependencies

- gate-wt /tmp/oap-083-8-a/gate-wt: detached Ib 53895c15 / tree
  79ccba1f, raw status empty at both invocation pre/post; .venv
  CPython 3.13.14 (uv cpython-3.13.14-linux-x86_64-gnu); frozen
  module bytes 45cf7967... (equal at I3 and Ib).
- Host python 3.14.4 was used for static checks only and is kept
  DISTINCT from the target 3.13.14 validation.
- Docker images: postgres:16-alpine
  sha256:0cefaabd882e42bcb2a2f3dc56d3ce4770560ba62fd7f197f1a2e008fd5731ab;
  python:3.13-slim
  sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f
  (runner base, never instantiated).
- uv 0.12.5, Node v24.22.0, pnpm 11.22.0 unchanged; no
  dependency, lock, plugin, image, service, role, or egress change;
  no installers run; no new tool in the frozen environment.

## Documentation

- Zero documentation changes in b. The five a-round docs
  reconciliations (docs/FOUNDATION_INTEGRATION.md,
  docs/SUPPLY_CHAIN.md, docs/TESTING.md, oap/INCREMENTS.md,
  oap/MVP-PROGRESS.md) are byte-identical at Ib. No new docs lines
  (round docs gross = 0); the 500-line docs cap is untouched.

## Safety and scope confirmations

- NO third launcher invocation; NO new test/experiment; NO
  controller/arm/source/test repair in b (the identified arm
  plumbing fix is deferred to root's next bounded round).
- The five frozen bundle hashes are unchanged (re-verified at
  report drafting); bc381dae controller kept stable.
- ZERO product/test/CI/docs/lock/dependency changes; the only new
  committed b paths are the b-report (this SELF commit) plus the
  b-order + active already at Ib.
- human3 preserved: `.codex/`, CODEX-SESSIONS.md, codex.sh are
  untouched and NOT committed; the product worktree is clean with
  only untracked `.codex/` environment artifacts, which are
  excluded from gates but never broad-excluded from raw status.
- No secret printed (PGPASSWORD rendered `<redacted:set>` in
  start.txt); no production/protected credentials; Docker used only
  for owned disposable containers/volumes; no shared host 5432; no
  foreign PID/DB/role/volume touched.
- No SDK patch/monkeypatch/proxy/fork/upgrade; no private
  foundation tables/SQL; no xfail/skip/catch-to-PASS; no pool
  replacement/size/reset/recreate; no assertion weakening.
- No merge/auto-merge/close; no next ID/PR/branch/acceptance
  chosen by coding; this report makes no selection.
- No FIFO replay: the sole root b response reader 7231 was never
  touched by the executor; no new reader/control; exactly ONE
  2-byte OK (no LF) is sent to the ACTUAL strategic
  /home/janezp/codex-supervision/slaif-agent-site/response.fifo
  (inode 4470112, verified) after remote verification, then close.

## Known limitations / blockers

- Blocker: the original P6 safety contract is NOT met at frozen I3
  (unchanged at Ib); this round produced ZERO diagnostic data
  (both invocations not-run); the P6 cause is UNKNOWN; root
  decides the next bounded round (arm-plumbing repair +
  meaningful undefined-name static checking + the diagnostic
  cohort).
- Invocation 1 is a setup failure (subject drift), not a
  diagnostic result; invocation 2 is a harness failure (line 783
  NameError), not a P6/SDK/driver result. No driver-test native 1
  and no successful diagnostic is claimed.
- Carried from a (full text in the immutable a-report): QPG4
  runner pytest/container exit UNKNOWN (never invented); QPG5
  local PG15 pass vs CI PG15 fail is timing-dependent with no
  causal claim; 23 unattributed anonymous volumes untouched; the
  QPG5 evidence directory name carries a sed typo (f6f3159 vs
  f6f32c0, internal guards exact I3); ALL31 launcher tee pipe
  parent native UNKNOWN (31 named child natives are the proof);
  the five Foundation PostgreSQL aggregator failures are the
  fail-closed barrier; advisory GHSA-6q48-6c7w-9gw2 remains ACTIVE
  (repo alert 17 withdrawn; no fixed-by-merge, no release claim).
- Phase A statics and root source reviews are NOT runtime
  qualification; the frozen bundle was never runtime-qualified
  (its first and only execution ended in harness failure).
- This report references the immutable a-report (627L, SHA256
  6dfd6f536ab3c6550564df76ec2537390e4a3114cce1062d6f5bd3f14b036128)
  without rewriting or repeating it.

## Recommended strategic follow-up

Factual only; no selection made. The identified defect is a 2-line
arm-plumbing fix in the frozen scratch controller (pass `arm`
through to `attempt_body`, or interpolate it from already-passed
state); the next bounded round — authorized by root after this
handoff and independent review — adds that fix, meaningful
undefined-name static checking, and the fixed 1-driver + 3-SDK
diagnostic cohort on the same frozen module. Coding proposes no
workaround, no pin change, no new feature, and no release or
acceptance claim. Root alone independently reviews this partial
handoff, chooses the continuation, and eventually accepts/merges.
