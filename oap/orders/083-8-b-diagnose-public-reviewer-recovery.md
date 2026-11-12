# OAP Work Order — 083-8-b: diagnose public reviewer recovery

## Identity and verified state

Numeric objective083; semantic increment8; round083-8-b.
PR mode: AMEND_EXISTING_PR. NO NEW PR.
PR112: <https://github.com/ulfe-lmi/slaif-agent-site/pull/112>.
Required branch: oap/083-8-a-qualify-public-whole-session. Base: main.
Required starting remote head: e7b15f97fe7fc0b353590012ff956407013ca952.
Required remote main: d18b6e4c9423f61de99b516be90619bf2ab5d3e0.
Repository: ulfe-lmi/slaif-agent-site.
Product: /home/janezp/codex-work/slaif-agent-site.
Strategic: /home/janezp/codex-supervision/slaif-agent-site.
Order/report basename: 083-8-b-diagnose-public-reviewer-recovery.md.
Actual strategic control.fifo inode4470111; response.fifo inode4470112.
Both are IN THE STRATEGIC DIRECTORY, not product/oap. Verify actual FIFO objects.
Primary alone consumes control and writes response; root alone does inverse.

Read applicable coding AGENTS.md, OAP-COMMUNICATION-coding-agent.md, compact
ARCHITECTURE-for-agents.md and complete activated083-8-a order/report.
No permission to load full ARCHITECTURE.md. Explicit increment-qualified mode
controls; no next objective, branch, PR, acceptance or merge chosen by executor.

Root received a exact2byteOK+EOF2026-10-27T06:50:25.788148Z. Root5883 is
TERMINAL0: never poll/replay it. No current root response reader at drafting.
Root FULL-read immutable a-report627L/34043B SHA256
6dfd6f536ab3c6550564df76ec2537390e4a3114cce1062d6f5bd3f14b036128.
Live GitHub06:51:38Z verified unique PR112 OPEN, exact required head S_a,
sole parent I3 f6f32c08c4d340c17d5db6bacc08a4852c562bc9, sole path a-report,
exact remote bytes. S_a tree bfe8ed29c63714dffdbfe5c34661be2c0d400991.
Main remains d18. S_a checks are pending/neutral/success at that observation;
NOT all green. Reconcile live GitHub before mutation; do not wait for a lucky
S_a run or treat it as curing the independently proven I3 failure.

Frozen I3 module1844L SHA256
45cf79671261212c19143315daeaecfc1b01b1e48d0b3c2cdf9e85cf881563a8.
I3 tree9051dfd558aab30bc8db9cc98a85e5e5c041cb34. Uniform minimal base diff:
code1896, docs154, a-transcript1099 INCLUDING a-report; total11 paths.
Full raw status preserved; ONLY exact human3 .codex/, CODEX-SESSIONS.md,
codex.sh excluded from source-clean gates. Never broad-exclude untracked paths.

## Decision and bounded purpose

Mode: DIAGNOSTIC_ONLY_PUBLIC_P6. Original increment remains PARTIAL/unaccepted.
No production or qualification-test repair is authorized in this round.
Establish the actual await phase of the observed post-termination restoration
stall and compare a bounded direct-driver recovery control. Distinguish
observations from hypotheses; non-reproduction does not resolve the failure.

I3 CI PG15job122039337259 and PG16job122039337087, plus local QPG5 PG16,
fail with15PASSED/1FAILED/1teardownERROR/native1: the public reviewer manager's
p6-restored-pending entry exceeds30s, then reviewer-pool close exceeds30s.
Earlier canonical absence/probe0 assertions reached PASS. Pending retention,
clean replacement and post-termination lock/GUC checks remain unqualified.
LocalPG15 passed while CI15 failed. No determinism, data-loss, SDK/driver/test
causal claim is established. FULL/P7 were NOT RUN under root stop.

Do not promote hypotheses into facts. Pool.close has BOTH holder-release and
connection-close awaits; a generic timeout localizes neither. SDK acquire
precedes its try block, so cancellation there does not enter that finally;
there is no inferred UnboundLocalError contradiction. Cancelling anext normally
propagates into its generator; do not assert abandoned finally blocks.
No-backend SQL snapshots and public pool counters alone do not identify the
await phase or prove a leaked slot. A thread/select stack or cr_frame.f_back
alone does not identify suspended asynchronous awaits.

## Exact scope and non-goals

The ONLY new committed paths this round are this b-order and its b-report;
update oap/active with strategic-owned exact b bytes. Keep all eight existing
code/CI/docs delta paths from a BYTE/MODE/TYPE UNCHANGED. Keep prior orders and
reports immutable. S_a plus the b transcript is the diagnostic source baseline.
No new helper/module/test family, conftest change, test selection in CI, docs
rewrite, generated contract, migration, dependency/lock/image/browser/action/
scanner/service/role/authority/egress/license-policy or product behavior change.

Existing aggregate caps3000 code/500 docs remain; this round adds ZERO code/
docs gross. Prospective transcript extension is exactly b-order+b-report plus
active; cumulative13 paths without helper (11 previous +2 new transcript paths).
No helper is authorized here. New b order/report gross is separately recorded.
All other mode/type/blob entries must equal S_a. Preserve human3 untouched.
Before any other path/family/source or budget change STOP for root; no packing.

Use bounded SCRATCH scripts outside Git; forecast at most350 lines diagnostic
and150 lines harness, not additional product implementation. Reuse the owned
module fixture via standard test-owned fixture unwrapping if useful; that is
not permission to invoke private SDK adapters/functions or private metadata SQL.
Only existing product-reexported public foundation APIs may execute. Frozen
agent-cow-postgresql0.2.0 and asyncpg0.31.0 remain unchanged and unpatched.

Forbidden: SDK patch/monkeypatch/proxy/fork/upgrade; direct foundation private
runtime/SQL; overwrite; FK/assertion weakening; xfail/skip/catch-to-PASS;
changing pool size/reset/expire/recreating the original pool to cure the
failure; replacing the tested SDK path with a direct connection; sleeps or
waiting for a termination listener before the original restoration step.
No implementation workaround, publication change, conservative-U decision,
new feature, release claim or acceptance. Direct-driver control is DIAGNOSTIC,
not replacement qualification of COW or the failed SDK path.

## Phase A: complete prospective diagnostic design

Prepare exact complete scratch scripts/harness and source/hash/argv/phase-
budget/cleanup forecast for root review BEFORE ANY diagnostic runtime.
Routine setup, read-only source inspection and scratch syntax checks belong
to primary. No new DB/test/runtime experiment or trial run before root review.
Root's bounded in-scope script approval is not a new FIFO or next order.
Secondary may independently read this exact design but never holds primary.

Required design preserves the original termination path: actual public
commit_session(error,defer_fk_constraints=True) returns inside reviewer scope;
exact uncommitted canonical effect and ordinary txn_probe established; owned
reviewer PID identified; independent canonical invisibility and live transaction/
locks observed; event barrier; terminate ONLY that owned PID; release the same
barrier; preserve exact actual driver exception class/message/sqlstate safely;
then original public pool-based reviewer entry and pending/replacement/GUC/
lock assertions. Do not remove the post-promotion window or pending retention.

Add passive observations without repairing the connection or changing event
order: termination listener registered on the original public connection,
public is_closed/pool size/idle/closing counters, actual connection PID and
phase timestamps. Do not wait for the listener before recovery. Listener state
is observation, not proof of queue state. Capture public driver errors exactly.

On a real entry deadline miss, BEFORE cancellation/cleanup preserve:

- Exact owned task state and suspended coroutine/async-generator source frames.
  Standard read-only Python introspection of owned tasks/generators is allowed;
  for this diagnostic only, inspect the standard-library contextmanager's
  driven gen reference and ag_frame/ag_await/cr_await as necessary. No SDK
  private function invocation, mutation or monkeypatch. Emit only type,
  function, source path/line and phase; NEVER dump frame locals/credentials.
  If a chain cannot be obtained, label unavailable rather than invent it.
- Bounded read-only SQL on existing owned admin connection: reviewer-role
  pg_stat_activity PID/state/wait_event_type/wait_event/backend_start and
  owned-PID pg_locks, at stall and after task drain. No foreign role/cluster.
  Ensure no concurrent commands share that connection. Server absence is
  compatible with multiple acquisition phases; do not call it causal proof.
- Public pool counters/listener/connection state at both observations.

Then cancel and bounded-drain the exact owned task, retaining native outcome,
CancelledError/other exception/stack or still-pending NOT DRAINED. Capture
teardown phase/task evidence before owned cleanup. If necessary public
pool.terminate is failed-fixture cleanup ONLY after evidence, never PASS.
No speculative aclose/repair as a substitute for observing the failure.

The separate direct-driver arm uses original asyncpg public pool APIs and an
ordinary owned transaction/probe, with the same max_size1, owned backend
termination and bounded borrow/release/recovery observations. It does not
pretend to run whole-session COW promotion or establish SDK causation merely
because it differs. Label all structural differences from the SDK arm.

## Phase B: fixed execution budget after root script review

Use ONE frozen diagnostic source and environment throughout. SERIAL only:
first ONE direct-driver control, then EXACTLY THREE SDK-path diagnostic
attempts on owned PG16, each with a fresh owned fixture. Fixed attempts are
prospective characterization, not adaptive rerun-until-green. Retain every
pass/failure/native/timeout; no fourth SDK attempt or new variant without root.
No new ALL31/Q-five-version/FULL/P7/WHOLE/LOCAL6 or other runtime this round.
Those final acceptance gates remain required by a and are not satisfied here.

Each attempt has180s outer wall-clock budget including its fixture lifecycle;
existing30s entry/drain/close bounds remain, auxiliary observations at most5s
each. Preserve actual cause if auxiliary collection fails; do not replace the
primary failure. The outer watchdog must stop/reap ONLY exact owned children
and prevent another attempt if cleanup is unsafe. Record actual forced/native/
unknown outcomes; a killed runner is not pytest PASS. Never infer child exit
from a tee pipe or docker-wait CLI status. Return PARTIAL on setup/ownership/
boundary failure instead of trying variants. No source/setup edits while any
owned child lives. Primary owns all setup and test labor; never human/root.

Use only owned disposable containers/clusters; no sharedhost5432/foreign PIDs/
DBs/roles. Internal5432/container namespace is allowed. Record exact image IDs,
nonempty network-mode ownership, server version/DB/user/system_identifier,
runner/PG/container/PID identities. Retain Mounts/volume ownership BEFORE
removing containers; use labeled owned volumes or rm-v only for proven owned
resources. Keep the23 earlier unattributed anonymous volumes UNTOUCHED; creation
window is not deletion authority. No global prune/foreign resource cleanup.

Commit/push exact b-order+active FIRST, capturing literal Ib and tree. Diagnostic
module bytes must equal I3 above; scratch scripts get their own frozen hashes.
Record full raw START/END status, literal Ib/tree, exact argv/tool versions,
UTC clocks, raw complete logs/sizes/hashes, individual immediate child exits,
outer/watchdog status and cleanup per attempt. Setup/source freeze before run;
all children terminal/reaped before any later work/report publication.

## Observable deliverables and report corrections

D1. Exact reviewed script/harness identities and actual frozen source; passive
observation boundaries and fixed four-attempt accounting (or honest early stop).
D2. Each arm's original window evidence, exception and public recovery/pending/
replacement outcomes, actual await/cleanup phase if observed, otherwise UNKNOWN.
D3. Evidence separates rollback already observed from still-unproven pending/
lock/GUC/recovery safety. No reproduction does NOT close the original failure.
D4. Exact native/log/status/source/cleanup accounting; no lucky-PASS erasure,
private SDK/SQL/workaround, unapproved mutation or foreign cleanup.
D5. The b report corrects these a-report errors WITHOUT editing a-report:

- Uniform minimal numstat counts CHANGED LINES, not lines plus bytes. a order470
  plus active1add+1delete is472 pre-report; plus a-report627 gives1099 transcript
  gross. a SELF has11 paths including report, not10. List b cumulative separately.
- CI15job122039337259 raw169648B/SHA631d007fe2f7f1245dd1f989ef5b40eb6392657bb861483c9bc22c0cffd8590b;
  CI16job122039337087 raw171694B/SHA64a4269ed9e94d9c93f84bb1532b5a356b02a8449b2d8cb0a1b2797c6b89f685.
  a report swapped the byte sizes; hashes/job identities remain distinct.
- P1 test asserts installed distribution metadata/reexports and frozen lock
  hashes/registry, not live non-yanked metadata or installed artifact byte
  identity. Index actual metadata/artifact source evidence or state unverified.
- Index actual fresh-I3 supply_chain units/broader CI ruff commands if run;
  otherwise NOT RUN at I3. No fresh gate merely to fill an old receipt.
- P7 was NOT RUN; the16-test module does not qualify P1-P7 collectively.
  Public manager entry timeout does not by itself prove pool.acquire await.
- a wrong oap/response.fifo open failed before any bytes; actual strategic FIFO
  got exactly ONE OK. No need to rewrite an immutable report or resend a signal.

All original P1-P7/final-current-SELF checks/actual CI Compose and six-image
artifact/full-product requirements remain. This diagnostic round closes none
by inference; no need to rerun unrelated full gates merely for this diagnosis.
All20 strict required checks+10 actual PG children and strategic satisfaction
are still mandatory BEFORE eventual acceptance; green CI alone is insufficient.
Report current b implementation-head checks honestly, including pending/failures.

## Reporting, ownership and handoff

Primary pane17 alone runtime/Git/report/executor FIFO; secondary21 read-only
source/scratch/CI audit, no runtime/import tests/install/DB/Git-fetch/product/OAP/
FIFO mutation or hold. Root owns roadmap/scope/orders/acceptance/merge. Human
owns intent/domain/risk/release. Healthy wait/slow/compaction is NOT crash.
Actual crash startup ONLY codex --yolo --profile early-beta; no resume/wrapper/
extra flags or hidden coding_083_3_b. Never merge/auto-merge/close the PR.

Keep original whole planned product goal and remaining a-order work intact:
immutable pendingU/true closure/complete3-family audit/exact inside-transaction
promotion/durable history; humanD5/084/080/085..091, all18 fields including
repeatable_object, common desktop/phone forms/reviewer-only UI, actual Apache
HTTP contract, lifecycle byteGC/recovery/backup and human release criteria.
No preview-only substitute or product-completion claim.

Final status PARTIAL while the original qualification remains unresolved,
even if every diagnostic deliverable ran. FULL coding report contract applies:
AMENDED_EXISTING_PR112; exact branch/base; literal40hex implementation Ib;
Report publication commit: SELF; per-D1-D5 facts/limits/errata and original
outstanding gates; every attempt/source/command/native/log/time/cleanup; setup,
docs unchanged, scope/security/human3 confirmations and honest live CI state.
Reference immutable a history without rewriting/repeating its entire report.
No implementation selection/next ID or SDK-causal assertion without evidence.

All non-report claims must be pushed first. Complete b-report TEMP INSIDE
product/oap/reports, same filesystem. Exact repo Markdownlint --no-globs on
that SAME COMPLETE file: native0/onefile/zeroissues; relint after ANY edit.
Preserve prehash/inode/time before Git; close/fsync/SAME-file atomicrename and
parentfsync/posthash/sameinode. Before report commit HEAD=literalIb; ALL staged
paths ONLY new b-report. S_b sole parentIb/solepathb-report. Push and verify
actual REMOTE head/parent/path/exactbytes BEFORE ONE exact2byteASCII OK4f4b,
noLF, close ACTUAL /home/janezp/codex-supervision/slaif-agent-site/response.fifo.
Never guess product/oap paths or replay after a successful write. No mutation
or push after report commit. Then block on actual strategic control.fifo.
Root independently receives/reads/reviews; PARTIAL/OK is never acceptance.
