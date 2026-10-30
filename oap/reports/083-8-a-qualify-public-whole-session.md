# OAP Coding-Agent Report — 083-8-a

## Work order

- Identifier: 083-8-a (objective 083, increment 8); work-order file
  `oap/orders/083-8-a-qualify-public-whole-session.md` (470L, 30112B,
  SHA256 843a6acd56c223ad396c6c14b945c7dbcc2c6756ef3e085a877d2ccf8699b3e5),
  FULL-read including the exact report-handoff section (lines 429-470).
- Activated `oap/active`: 8 bytes, hex 3038332d382d610a ("083-8-a" + LF),
  committed unchanged.
- PR mode: CREATED_NEW_PR (PR 112, fresh named branch from verified
  accepted main).

## Status
PARTIAL — real, root-adjudicated P6 safety-contract failure at frozen
final implementation I3 (CI Group B PG15/PG16 plus local QPG5 PG16);
root-ordered STOP before FULL PG18 and P7; no source fix, no rerun,
and no workaround in this round per order. P1-P5 qualified in every
executed context at I3; P7 not run.

## Executive summary
Executed the PUBLIC_API_QUALIFICATION_ONLY increment at one frozen
final implementation I3: a new 16-test session-scoped integration
module qualifying the public whole-session promotion mechanism of
agent-cow-postgresql==0.2.0 through the public
asyncpg_cow_session/asyncpg_cow_reviewer APIs only (P1 anchored
metadata, P2 mixed-FK whole-session promotion with exact canonical
oracles and representative media-reference facts, P3 session-edge
semantics, P4 row AND schema conflict refusal, P5 deferred-FK commit
stages including the required physical two-table deferrable cycle,
P6 post-promotion failure windows including reviewer-connection
loss, P7 composite-FK dependencies() gap documented via source anchor
and prepared scratch diagnostic), plus the exact fourth complete-
module pytest command appended to CI Group B (B becomes 45+Q,
Q measured 16 per version), the extended hostile CI predicates,
and five docs reconciliations.

The P6 criterion is NOT met at I3: after the test's
pg_terminate_backend kills the reviewer pool's only connection, the
restoration-phase re-acquire through the public reviewer manager does
not complete within the 30s test-side bounded diagnostic (asyncpg
0.31.0 pool.acquire has no default timeout; the SDK is unchanged). CI
(Group B PG15/PG16) and local QPG5 (PG16) reproduce the identical
single-test failure; the other 15 tests pass in every executed
context. Root ordered STOP before FULL/P7; this round makes no source
change, no rerun-until-green, no pool-replacement, no SDK patch, no
pin change, and no assertion weakening.

Fresh ALL31 at I3: 31/31 exact argv native 0 (root independently
verified). Fresh serial QPG at I3: PG14/15/17/18 all 16 passed, PG16
failed (P6). CI at I3: green except the two Group B P6 failures, the
five fail-closed Foundation PostgreSQL aggregators (documented A/B
barrier, not five engine failures), and the still-pending "Compose
and edge packaging" job at drafting. The conditional carry of
083-7-b local WHOLE/LOCAL6 from I7 to I3 holds: complete leaf maps and
the raw no-rename diff prove no builder-input path changed.

## Authoritative GitHub state

- Repository: ulfe-lmi/slaif-agent-site; PR 112
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/112>, state OPEN,
  unmerged (merge performed NO by coding).
- Base branch main; verified starting remote main
  d18b6e4c9423f61de99b516be90619bf2ab5d3e0 (PR #111 merge, 083-7-b).
- Head branch oap/083-8-a-qualify-public-whole-session.
- Implementation head SHA: f6f32c08c4d340c17d5db6bacc08a4852c562bc9
  (tree 9051dfd558aab30bc8db9cc98a85e5e5c041cb34); pushed and
  remote-verified (ls-remote equal to local) before the final gates.
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via
  GitHub)
- Implementation commits pushed before report (append-only; no
  amend/reset/rebase/force-push after the incident recovery):
  d3d6f0355f54b7ec9696a0c60c261ceaf38a69e6 (activation: order + active
  exact bytes); a5f05bcb4ab2e63332558e2fb1131a638af08088 (initial
  implementation); 9dc0eb52243d0760d8d62288c656720760754597 (pre-push
  amend incident; both objects and their failed evidence preserved);
  e9ce68fd43a51b768b12af0f7bdf11e782a0bf2c (J: forward provenance join
  preserving both heads, tree exactly
  069ce435f6bc4d3b167d9c5453df907b5466e508); 2b37159fe088b271a0d232cab4a845af10694353
  (I2: DDL index-name + P4 order-semantics repair, tree
  8ffc1c43267edb304e32bfa1bf9c652b63473ab4); f6f32c08c4d340c17d5db6bacc08a4852c562bc9
  (I3 final). Report parent = implementation SHA.
- New PR this turn yes; amended existing PR no; merge performed NO.

## Changes made

- New 16-test module (1844L, committed blob SHA256
  45cf79671261212c19143315daeaecfc1b01b1e48d0b3c2cdf9e85cf881563a8)
  qualifying P1-P7 through public APIs only, on a session-scoped
  owned disposable database/schema/roles mirroring the actual product
  bootstrap (enable_cow_schema allow_deferred_fks=True,
  fail-closed canonical writes). conftest.py unchanged (order
  forbids); no helper module (cap discipline; 10 of max 11 paths).
- .github/workflows/ci.yml: appended the exact fourth complete-module
  Group B command (uv run --frozen pytest
  services/backend/tests/integration/test_foundation_whole_session_qualification.py,
  no -k/selection filter); B is now 45+Q, grand total 650+sum(Q14..18);
  original five A/B argv/order/85+45 counts, both PG14..18 matrices,
  isolated services, 15m child budgets, 5m aggregators, job-level
  always, and the entire-needs exact-success barrier unchanged.
- tests/repository/test_foundation_ci.py: predicates requiring the
  fourth exact complete-module invocation (missing or weakened
  invocation must fail); all old negative cases, security,
  scheduling, matrix, budget, and argv assertions retained.
- Five docs reconciled (154/500 gross): actual P1-P7 scope/results,
  accepted 083/7 vs current 083/8 in-flight, current advisory truth
  (withdrawn repo alert 17 vs active global GHSA), CI workflow
  extension distinguished from unchanged product runtime.
- oap/orders/083-8-a-qualify-public-whole-session.md (A) and oap/active
  (M) committed as the exact activated bytes.

## Files changed

- A services/backend/tests/integration/test_foundation_whole_session_qualification.py
  (+1844/-0)
- M .github/workflows/ci.yml (+8/-2)
- M tests/repository/test_foundation_ci.py (+38/-4)
- M docs/FOUNDATION_INTEGRATION.md (+87/-9)
- M docs/SUPPLY_CHAIN.md (+14/-7)
- M docs/TESTING.md (+28/-0)
- M oap/INCREMENTS.md (+3/-2)
- M oap/MVP-PROGRESS.md (+2/-2)
- A oap/orders/083-8-a-qualify-public-whole-session.md
- M oap/active

Gross size vs order budgets: implementation 1896/3000 (1844 new
module + 42 predicate +38/-4 + 10 workflow +8/-2); docs 154/500;
transcript identities separately counted: order 470L/30112B +
active 8B (measured combined 478; the root forecast line "472"
is an arithmetic erratum, recorded below, no scope effect). No cap
crossed; no packing.

## Acceptance-criteria evidence

### Criterion P1: anchored public sources and metadata

- Result: PASSED in every executed context.
- Evidence: frozen uv.lock unchanged (uv lock --check native 0); the
  module P1 test asserts the installed public sources against the
  order-anchored wheel 106280B SHA
  c469d24700fabb93a58f464d3539a32e936097f93035a95f193062859546f5b1 and
  sdist eae8d434d2fc03c4faa08b44b4863fc8f8efb44ee33eaad3adc22e7eb96a062c
  plus official metadata/non-yanked/license/artifact provenance.
  P1 passed in local PG14/15/17/18 and in every completed CI Group B
  job (B14/17/18 pass; P1 among the 15 passed in B15/B16). No Git,
  local/editable, or fork dependency; no patch/monkeypatch/upgrade;
  public APIs only. Source inspection is not runtime qualification;
  the runtime portion is the P1 test passing.

### Criterion P2: real mixed-FK whole-session promotion

- Result: PASSED in every executed context.
- Evidence: real mixed-table success through public
  asyncpg_cow_session/reviewer with source-backed geometry:
  content.site_locale (UUID id, site UUID, TEXT tag,
  UNIQUE(site_id,tag)) with mixed UUID+TEXT FKs alongside UUID+UUID
  references, self/row references, and page/model/field/item/
  translation/relation/navigation/composition facts. Representative
  media-reference facts use the actual d18 component catalog: Hero
  root (required heading, content slot allowed) holding an Image leaf
  whose props carry the referenced same-site asset as a JSON STRING
  UUID (props.mediaId, per 060_001 lines 526..527) with full canonical
  JSON oracles; labeled generic mechanism, not actual renderer,
  upload, or domain validation. Distinct known operation IDs; one
  operation touching multiple tables; session isolation proven;
  untouched canonical/other-session facts unchanged before approval;
  exact public pending ID set with unique IDs; whole
  commit(error, defer_fk_constraints=True) returns exact expected
  committed_operations/committed_tables and
  has_pending_operations=False; EVERY intended final canonical row/
  value oracle verified independently after scope exit; fresh public
  reviewer inspection returns no pending operations. Counts alone
  never pass; committed_operations is the PRE-promotion locked tuple
  and independent oracles back it. The I2 oracle defects (content_item
  JSONB returned '{}' string vs expected {} dict; row primary_key
  {'id': UUIDTEXT} vs expected UUID object) were repaired in I3 by
  decoding ONLY the known jsonb oracle columns and comparing the
  exact public serialized UUID text — no broad stringification and no
  loss of row/value checks.

### Criterion P3: whole-session edge semantics

- Result: PASSED in every executed context.
- Evidence: empty session, same-value/no-effective-change, repeated
  writes/coalescing, and insert-delete net-zero all asserted with
  exact public pending ID/operation/row semantics and exact final
  state; separate positive controls preserved; no selective
  commit_operations/visibility feature; no overwrite
  characterization; actual result divergence from product needs is a
  reported gap, not a desired-behavior or expected-bug assertion.

### Criterion P4: real row AND schema conflict refusals

- Result: PASSED in every executed context.
- Evidence: row conflict — both competing sessions first-touch the
  same original row BEFORE A commits, then B refuses with structured
  public CowConflictError facts, exact zero promoted effects, and all
  pending changes preserved. Schema conflict — genuine fingerprint
  drift via the order-directed owned probe (ALTER COLUMN title SET
  DEFAULT bounded literal on canonical_relation items_base;
  DROP DEFAULT restores), public error-mode refusal with
  BASE_SCHEMA_CHANGED, not a setup re-enable/pending guard; one
  benign owned index-only positive control retained. I2's absolute
  order==1 expectation (invalid under the shared session-scoped
  fixture, conftest.py:188) was replaced in I3 with source-backed
  public positive-integer/1-based order handling; no semantic
  assertion was dropped. No private foundation metadata access, no
  private SQL promotion, no privilege broadening.

### Criterion P5: deferred-FK commit stages

- Result: PASSED in every executed context.
- Evidence: valid cyclic/deferred reordering succeeds completely,
  including the REQUIRED physical two-table deferrable-FK cycle
  (explicitly owned synthetic pair, labeled generic, alongside the
  actual product geometry and self/row-reference cases); a genuinely
  invalid FINAL FK state refuses at promotion/scope-commit time with
  the exact public exception class/sqlstate/source/failure stage
  recorded, and write-time refusal is distinguished from it; no
  dangling-final-state success was turned into whatever-outcome PASS.

### Criterion P6: actual post-promotion failure windows

- Result: FAILED — safety contract not met at frozen I3.
- Concrete evidence (identical signature CI and local):
  - CI run 40459137893: Group B PG15 job 122039337259 (raw 171694B,
    SHA256 631d007fe2f7f1245dd1f989ef5b40eb6392657bb861483c9bc22c0cffd8590b)
    and PG16 job 122039337087 (raw 169648B,
    SHA256 64a4269ed9e94d9c93f84bb1532b5a356b02a8449b2d8cb0a1b2797c6b89f685):
    each 16 collected / 15 passed / 1 FAILED + 1 teardown ERROR, step
    native 1, test 62.55s/62.62s:
    test_p6_reviewer_termination_rolls_back_promotion —
    AssertionError "p6-restored-pending-enter: owned task did not
    reach a terminal state within 30s; suspended at ...
    _AsyncGeneratorContextManager.__aenter__ ...; task ended
    cancelled after the deadline"; teardown RuntimeError "owned
    fixture cleanup failed: reviewer-pool: pool.close() failed within
    30s: TimeoutError".
  - Local QPG5 at I3 (qpg-serial5.sh; owned container-namespace
    clusters; per-version image/PG cid/runner rcid, exact
    network_mode=`container:<PGCID>` assert, pg_isready, and
    SERVER_IDENTITY with system_identifier recorded per log): PG16
    "1 failed, 15 passed, 1 error in 65.27s", QPG_CHILD_EXIT=1
    (raw 20437B, SHA256
    4cb8d3dacc7e152d43ba9cf8a876e445d2592482a6ce11a872cac0b38e8d3959);
    PG14/15/17/18 all 16 passed with child native 0.
- Diagnostic vs mechanism vs actual product:
  - Diagnostic (new in I3, test-side only): builtin asyncio bounded
    awaits (P6_BOUND_SECONDS=30.0) at the public context entry/exit,
    window-task sites, restoration pool acquires, and the owned
    fixture pool.close; pre-cancel print_stack capture on the owned
    task; the target's own native TimeoutError is preserved with its
    actual traceback (not reclassified); honest drain outcomes
    (cancelled-drained vs still-pending NOT drained); a deadline miss
    is a REAL failed safety test, never cleanup. asyncpg 0.31.0
    pool.acquire(timeout=None) has no default deadline (root/peer
    read pool.py); the SDK asyncpg_cow_reviewer acquires without a
    timeout — the bound is test-side observation, not an SDK change.
  - Mechanism (observed; cause NOT attributed): after
    pg_terminate_backend kills the reviewer pool's only connection
    (max_size=1), the restoration-phase re-acquire through the public
    manager does not complete; the bounded entry guard fires, then
    the bounded teardown close fires, then the public
    pool.terminate() fallback runs. No SDK-defect claim; no data-loss
    claim.
  - Actual product: SDK, pins, and production behavior unchanged; no
    failpoint/hook/worker logic added; no overwrite or authority
    change.
- Qualified within P6 before the failure: commit_session ran to
  completion inside its transaction-owning reviewer body; real
  uncommitted effects proven; escaped-postcondition refusal and
  actual Task.cancel/CancelledError windows exercised; the
  pre-wait canonical/probe rollback assertions inside the failing
  test held.
- NOT qualified: pending retention after termination, independent
  restored-state observation, clean reusable/replacement
  connections, and the no-leaked lock/transaction/GUC checks (the
  bounded teardown close timed out).

### Criterion P7: composite-FK dependencies() gap

- Result: NOT RUN (root STOP after the P6 failure).
- The module documents the known composite-FK dependencies() failure
  through source anchors; the scratch-only diagnostic
  (p7-scratch-diagnostic.py, with the exact oriented known-op UUID
  pair characterization fix applied; no committed path, no xfail, no
  passing-bug assertion) was prepared but not executed under the STOP
  order. An actual failure would be recorded as a nonzero native
  result with safe traceback/source, never hidden or caught into
  PASS.

## Local verification

Fresh final-I3 gates, serial, source/setup/checkout frozen, in a clean
detached worktree of I3 (/tmp/oap-083-8-a/gate-wt; human3 not copied):

- ALL31 (order-exact argv and order from the worktree root): 31/31
  EXIT=0, OVERALL=0 (overall.txt 10B, SHA256
  7e91207a2893df0db997e0640a2eddad65166aa2cd73b8a9d885351fa1fe1b85);
  per-command START/END/CMD in summary.txt (SHA256
  803a11dd392290de2667f05a66a188ba2bfe24c9358e5269871d84d2a2bb3909);
  snapshots START 2026-10-27T06:08:35.393802Z / PRE-COMMANDS
  06:08:35.438198Z / END 06:13:30.137790Z — 12 lines / 3 blocks, all
  HEAD f6f32c0, tree 9051dfd, raw full status empty (SHA256
  7b7ce8065af2d81bd06886e31031e7e0dc905a61e28ab659d1c3d2d71ce4aa3f);
  provenance: uv 0.12.5, Python 3.13.14 (gate-wt .venv), Node
  v24.22.0, pnpm 11.22.0. Root independently verified EACH of the 31
  named argv, each native 0, and the 3 clean snapshots (receipt
  strategic-I3-ALL31-independent-named-command-review.json).
  Erratum: the launcher was `bash all31-runner5.sh 2>&1 | tee` and
  PIPESTATUS was not captured, so the runner PARENT native exit is
  recorded UNKNOWN; the 31 named child natives are the proof; it was
  not rerun for a parent receipt. Future owned gate launchers capture
  the immediate RC before any pipe.
- QPG5 fresh serial complete-module PG14..18 at I3 (exact CI fourth
  command `uv run --frozen pytest
  services/backend/tests/integration/test_foundation_whole_session_qualification.py`):
  - PG14: 16 passed in 4.84s, child native 0 (log 1939B, SHA256
    cd31f4e1a9c0f3e087fb0fc39ea4981a4230cc240849ee5124e7e68366efa269)
  - PG15: 16 passed in 5.05s, child native 0 (1941B, SHA256
    ca224778bf4970b9f0090be53bad4fb0612d2be4c67b70232fddd850fd011ea3)
  - PG16: 1 failed, 15 passed, 1 error in 65.27s, child native 1
    (20437B, SHA256
    4cb8d3dacc7e152d43ba9cf8a876e445d2592482a6ce11a872cac0b38e8d3959)
    — P6, see Criterion P6
  - PG17: 16 passed in 4.65s, child native 0 (1941B, SHA256
    99d4098bc908797e5029b76b37bdc4399344d5940cb95c5df23cae34ede3cff2)
  - PG18: 16 passed in 4.69s, child native 0 (1940B, SHA256
    9a7b450da5b00fac997ad37faabc0d579612e65a9ea1231257d7dfc20a7cdf44)
  - overall.txt OVERALL=1 (SHA256
    054ad49289e33a1fd26efdcde238bdb404f55cb67c6381c90c0e8d6b902d0317);
    snapshots START 06:14:01.095255Z / END 06:15:50.607907Z, same
    HEAD/tree (SHA256
    1c9027c1895606d48d143cad7e0990d35a3d3cbf5633d432ab562aad1abdbbcd);
    per-version START/END in summary.txt (SHA256
    666d2ddfc6a148a9b2f67c605538655ded3f689766ea267d19c0be42bbb19e81).
  - Per-version cleanup: rm-runner=0 and rm-pg=0 with both cids
    echoed in each log.
  - Erratum: the evidence directory name carries a sed typo
    qpg-I-f6f3159-attempt1 (f6f3159, not f6f32c0); the internal I=/
    TREE= guards are exactly I3; the path is preserved, not renamed,
    and it is not a failed preflight.
- Scratch P6 helper check (root-authorized; pure asyncio; no DB/SDK/
  network; no committed path): attempt1 06:04:30Z import FAIL native
  1 (preserved); attempt2 06:04:44.482Z..06:04:48.599Z native 0 with
  all four scenarios PASS (normal return; own native TimeoutError
  preserved as the same instance with actual traceback; pending to
  guard deadline with phase + pre-cancel stack + cancelled-drain;
  suppressed cancel recorded "still pending / NOT drained"). This is
  NOT a qualification gate and is not QPG/FULL/P7.
- FULL PG18 (complete unfiltered backend integration directory):
  NOT RUN — root STOP after the P6 safety failure.
- P7 scratch diagnostic: NOT RUN — root STOP.

History (all failures preserved, none relabeled):

- a5f05 ALL31 (early runner): steps 08..17 native 1 (plain python in
  the wrong env) plus a leading-zero printf log-name collision;
  original logs/exits/runner preserved.
- 9dc nohup-style runner: stopped after CMD4/5, native UNKNOWN,
  partial — not attributed to J.
- QPG-J preflight 1 (nested
  qpg-I-e9ce68f-attempt1-portparse-fail/qpg-I-e9ce68f, START
  04:29:45.767..49.572) and preflight 2 (top-level
  qpg-I-e9ce68f-attempt2-dockerport-empty-fail, START
  04:30:11.257..15.071): both OVERALL=1, no pytest invocations; the
  `docker port | awk field2 | cut field1` arrow parser extracted
  "-" (parser failure, not a host-capability diagnosis); preflight 2
  is an unchanged duplicate of preflight 1 (retained honestly, not
  retroapproved).
- QPG3 at J (attempt3): FAILED — fixture CREATE INDEX name
  schema-qualified (invalid per PostgreSQL 18 CREATE INDEX
  parameters), 14 setup errors per version plus the P4 order
  1-vs-0 assertion, the harness rc-capture defect (docker wait CLI
  0 recorded instead of the wait stdout integer), and the vacuous
  empty-equals-empty sandbox ID equality; 5x QPG_CHILD_EXIT=1, all
  five logs preserved.
- I2 CI (run 40452411586): B18 job 122018090531 (raw 172359B,
  SHA256 ea658ff9073bfabbb7c103c66af2a63bc6b73e198169e64416dc3378744b801f):
  16 collected, 2 failed / 14 passed — P2 content_item JSONB '{}'
  string vs {} dict; P4 row primary_key {'id': UUIDTEXT} vs UUID
  object. B14 job 122018090575 and B16 job 122018091451 CANCELLED
  (raw logs preserved, 121225B/141448B; cancellation cause not
  explicitly proven); B15/B17 FAILED per CI state.
- QPG4 at I2: INCOMPLETE/HUNG, root finite stop (receipt
  strategic-I2-QPG4-finite-stop-and-I3-diagnostic-decision.json):
  owned DB idle, no blocked locks, no CPU delta; py-spy 0.4.2 at
  05:17:31Z shows MainThread in select/event-loop inside pytest
  runtest_call (2126B, SHA256
  c7a6b8a859d448c43b5a279fb3dd57de621b6e0b735a63af9691f7c0f9e6f458) —
  does not identify the suspended coroutine; cause UNKNOWN. Wrapper
  exit 143 (stop); actor handle 22824 reaped 05:23:38.882Z native 0
  (outer shell after echo, not pytest 0); runner pytest/container
  exit UNKNOWN (docker rm -f preceded post-stop inspect/wait; never
  invented as 137/143); the exactly owned anonymous PG volume
  removed native 0 (IDs retained); all five old owned PIDs verified
  gone; PG15..18 never launched locally.
- J CI: Group B PG18 job 122014700942 (raw 226359B, SHA256
  a5396a66fd5a209b71c820121106742e02b8232c357a4d74432096188d873934):
  14 syntax errors + P4 order + step native 1 — independently
  reproducing the QPG3 defect.

## Conditional carry (083-7-b WHOLE and LOCAL6)

- Old actual subjects (executed at I7
  b0538981eb70ca3593db71a54bddfb22d8f841a6, tree
  431fa2eab08448f87956b9a43243fab6f5fd1578):
  - WHOLE `sh tools/compose/smoke.sh slaif0835`, native 0,
    2026-10-26T06:54:47.210032..07:13:05.266093Z, 64305B log SHA256
    60fa93d551770d91cc7f80539133c28db5924f4f88027767b847bfbcab9752e8.
  - LOCAL6 `GITHUB_SHA=I7 sh tools/supply_chain/run.sh
    UNIQUE_ABSOLUTE_DIRECTORY`, native 0,
    2026-10-26T07:13:40.534074..07:41:13.987959Z, 106395B log SHA256
    8576e04c1e30f7991fff5a33d80c34a3e3a12ab0978d671e58beb3a7f0c266e0.
- I7->S7->d18 adds ONLY the accepted 083-7-b report after I7; root
  verified the merge tree.
- New complete equivalence I7 -> I3 (receipt
  strategic-I3-carry-I7-to-I3-leafmap-review.json, leaf maps
  carry-leafmap-I7.txt 1116 lines / carry-leafmap-I3.txt 1119 lines):
  complete Git leaf maps mode/type/blob plus raw no-rename diff give
  exactly 11 paths — M .github/workflows/ci.yml, M
  docs/FOUNDATION_INTEGRATION.md, M docs/SUPPLY_CHAIN.md, M
  docs/TESTING.md, M oap/INCREMENTS.md, M oap/MVP-PROGRESS.md, M
  oap/active, A oap/orders/083-8-a-qualify-public-whole-session.md, A
  oap/reports/083-7-b-complete-installer-remediation.md (present via
  d18, absent from I7 by construction), A
  services/backend/tests/integration/test_foundation_whole_session_qualification.py,
  M tests/repository/test_foundation_ci.py. Of the 1116 common
  paths: 8 blob-changed (exactly the non-builder rows above), 0
  mode/type changes, 0 deletions; the 3 added paths are order/report/
  test module.
- Builder-input proof: `git diff --name-only I7 I3` restricted to
  compose.yaml, .dockerignore, uv.lock, pnpm-lock.yaml,
  pyproject.toml, package.json, migrations/, services/backend/src,
  tools/compose, tools/supply_chain, and web/ is EMPTY. Backend
  image copies services/backend/src (not tests); web/docs/assets,
  locks, and all other build inputs remain byte/mode/type identical.
- Conclusion: the 083-7-b WHOLE/LOCAL6 passes remain ACTUALLY TESTED
  AT I7 with byte-identical builder inputs at I3 (conditional carry
  holds); they are not claimed to have run at I3. Root independently
  checks this evidence; secondary did not approve carry. ALL31, Q,
  FULL, P7, SELF CI, actual CI Compose, and the fresh six-image
  artifact are NOT carried.

## GitHub CI / required checks

- Implementation head f6f32c0, run 40459137893, status in_progress at
  drafting (24 of 25 jobs completed):
  - Foundation PG Group A PostgreSQL 14/15/16/17/18 (jobs
    122039337097/122039336822/122039337069/122039337217/122039337183):
    SUCCESS.
  - Foundation PG Group B PostgreSQL 14 (122039336946): SUCCESS.
  - Foundation PG Group B PostgreSQL 15 (122039337259): FAILURE —
    P6, 16 collected / 15 passed / 1 failed + 1 teardown error,
    native 1.
  - Foundation PG Group B PostgreSQL 16 (122039337087): FAILURE —
    P6, same signature.
  - Foundation PG Group B PostgreSQL 17 (122039337031): SUCCESS.
  - Foundation PG Group B PostgreSQL 18 (122039337288): SUCCESS.
  - Foundation PostgreSQL 14/15/16/17/18 (jobs
    122042527194/122042527187/122042527166/122042527145/122042527433):
    FAILURE — the documented fail-closed required aggregators whose
    needs span the entire A/B group; any Group A/B failure blocks
    them. These are the barrier failing closed, NOT five additional
    engine test failures; the only underlying engine test failures
    are Group B PG15 and PG16. Their small logs are complete (few KB
    is not truncation).
  - Python 3.12 / 3.13 / 3.14 quality and package: SUCCESS.
  - Node contracts, Markdown, Mermaid, Repository policy,
    Supply-chain evidence, Dependency review: SUCCESS.
  - Compose and edge packaging (job 122039336500): PENDING /
    in_progress at drafting (root independently tracks the six-image
    artifact; no local runtime was started for it).
- CodeQL (separate run 40459137818 at head f6f32c0): Detect
  supported languages SUCCESS; Analyze (actions), Analyze
  (javascript-typescript), Analyze (python) SUCCESS; CodeQL check
  SUCCESS.
- All required green at drafting: NO (two Group B P6 failures, five
  fail-closed aggregators, Compose pending).
- Report-only commit may trigger fresh checks; strategy verifies
  SELF.

## Local setup / dependencies

- No dependency added or changed; uv.lock, pyproject.toml, and
  pnpm-lock.yaml byte-identical (I7->I3 diff).
- Gate worktree: clean detached checkout of I3 at
  /tmp/oap-083-8-a/gate-wt (.venv gitignored; human3 not copied);
  uv 0.12.5; Python 3.13.14; Node v24.22.0; pnpm 11.22.0.
- Disposable Docker images (per-version IDs in QPG5 logs):
  postgres:14-alpine sha256:862ffc2556a2db763f0439c8323490000cd01975d2798a845e4a8dd3a905862f;
  postgres:15-alpine sha256:54e0dd8e8cddcdbb9156c2486eed5a43eccb7214d7c6828097d41ce049fb3984;
  postgres:16-alpine sha256:0cefaabd882e42bcb2a2f3dc56d3ce4770560ba62fd7f197f1a2e008fd5731ab;
  postgres:17-alpine sha256:266d3c257594e195b309ae9d1805e54c788f1d7b375f56bf6c367aac6c917e7b;
  postgres:18-alpine sha256:10a5c69a83035ab5239f5620d708520e8b28f5aa1f2b20143e6024532edadfb5;
  runner base sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f.
- Host tooling: py-spy 0.4.2 installed under /tmp (VM-local, outside
  the project/runner frozen env) for one authorized read-only stack
  capture; no image, source, or package change to any frozen env.
- Routine VM setup only (docker, uv sync). No production/protected
  system, no host port 5432, no foreign roles/connections; all DB
  access through owned disposable containers (container network
  namespace; internal 5432 only).

## Documentation

- Five allowed docs, 154/500 gross, no sixth doc:
  docs/FOUNDATION_INTEGRATION.md (+87/-9), docs/SUPPLY_CHAIN.md
  (+14/-7), docs/TESTING.md (+28/-0), oap/INCREMENTS.md (+3/-2),
  oap/MVP-PROGRESS.md (+2/-2).
- Historical Aug 17 foundation result preserved verbatim;
  scaffold-era claims corrected against the actual merged baseline
  without claiming all APIs complete; accepted 083/7 vs current
  083/8 in-flight reconciled in the last three docs.
- Advisory truth (verified, dated): repo dependabot alert 17 returns
  410 withdrawn via the exact endpoint
  repos/ulfe-lmi/slaif-agent-site/dependabot/alerts/17; global
  GHSA-6q48-6c7w-9gw2 remains ACTIVE (withdrawn_at null; updated
  2026-10-26T16:02:13Z; first-patched metadata 2026.10.18, range
  <2026.10.18; official text recommends 2026.10.19); 13 other open
  repo alerts, 0 Critical. No dismissal, suppression, security
  approval, or global release-closure claim; no fixed-by-merge claim.
- The ci.yml change is an actual CI workflow extension, explicitly
  distinguished from unchanged product runtime.

## Safety and scope confirmations

- Unrelated files changed: no — exactly 10 paths (order allows max
  11 without a helper); human3 (.codex/, CODEX-SESSIONS.md, codex.sh)
  preserved untracked, never copied into the gate worktree, never
  modified.
- Production secrets accessed: no. Production systems accessed: no.
- Required tests skipped/not run: yes — FULL PG18 and P7 NOT RUN by
  explicit root STOP after the P6 safety failure; no other
  skip/xfail/partial aggregation/substitution; no test of the 16 is
  excluded from CI or from local runs.
- Scope deviation: no.
- Extra objective PR: NO. Coding-agent merge: NO.
- Activated order/active edited: NO (exact bytes committed).
- Report commit changes only this report: verified at commit time
  (staged diff exactly one new report path).
- No SDK patch/monkeypatch/pool proxy/connection-mode workaround/pin
  change/assertion weakening; no new test family, path, or
  dependency; conftest.py unchanged; no history rewrite after the
  forward join.

## Cleanup and residual state (owned only)

- Containers: QPG5 per-version rm-runner=0 and rm-pg=0 with both
  cids in each log; no 083-8-a named containers remain (read-only
  docker ps -a name filters show only older unrelated slaif PG
  containers, untouched). QPG4 stop: wrapper 143, actor reaped,
  runner rm -f before post-stop inspect (exit UNKNOWN), PG15..18
  never launched.
- PIDs: every owned gate child terminal/reaped; exact old-PID checks
  per the QPG4 receipt show no residual owned process.
- Volumes (honest, corrected record): the official postgres images
  declare VOLUME /var/lib/postgresql/data, so every owned PG
  container created one anonymous volume, and docker rm without -v
  leaves it behind. QPG4's exactly owned anonymous PG volume was
  explicitly removed native 0 (IDs retained in the stop receipt).
  An earlier "no stale volumes" statement derived from an awk filter
  (`awk $2 >= "2026-10-27 06:1"`, which compared the date-only field
  2 against a date+time) is RETRACTED: its empty output does not
  prove absence. Read-only inventory at report writing (docker
  volume ls / inspect CreatedAt; 106 volumes total on the host): 23
  created on 2026-10-27 fall in this round's gate windows — 5 at
  04:29:46-49 (preflight 1), 5 at 04:30:11-14 (preflight 2), 1 at
  04:31:10 (qw8 portcheck window), 5 at 04:44:34-45:00 (QPG3
  attempt3), 2 at 04:47:30/04:49:40 (ddl-debug runs), 5 at
  06:14:01-06:15:41 (QPG5). Ownership IDs are not recoverable
  (containers deleted before Mounts could be retained; anonymous
  volumes unlink from deleted containers), so these 23 are recorded
  as UNKNOWN/unattributed (probable ownership by creation-window
  correlation only). Per the standing order, none were deleted in
  this round; no global prune, no foreign volume touched;
  disposition is a strategic/root decision.

## Known limitations / blockers

- Blocker: the P6 safety contract is not met at frozen I3 (Criterion
  P6). Pending retention and clean replacement after reviewer
  termination are NOT qualified. Root decides the next formal round;
  this round contains no workaround, no rerun, and no source change.
- QPG4 runner pytest/container exit UNKNOWN (never invented); hang
  cause UNKNOWN (the py-spy select stack does not identify the
  suspended coroutine).
- QPG5 local PG15 passed while CI PG15 failed: timing-dependent; no
  causal claim, no rerun to change the result.
- 23 unattributed anonymous volumes from this round's gate attempts
  (Cleanup section); the earlier awk-based absence claim retracted.
- QPG5 evidence directory name carries a sed typo (f6f3159 instead
  of f6f32c0); internal I=/TREE= guards are exactly I3; path
  preserved.
- ALL31 launcher tee pipe: runner parent native UNKNOWN (the 31
  named child natives are the proof); no rerun for the receipt.
- The five Foundation PostgreSQL aggregator failures are the
  documented fail-closed barrier, not five engine test failures.
- Compose and edge packaging pending at drafting; the fresh
  six-image artifact is not reviewed in this round (root tracks).
- P7 not run; the composite-FK dependencies() gap remains documented
  (module source anchors + prepared scratch diagnostic).
- Advisory GHSA-6q48-6c7w-9gw2 remains ACTIVE (repo alert 17
  withdrawn); no fixed-by-merge and no release claim.
- Errata (recorded, not rewritten): (1) a pre-push --amend
  superseded a5f05 by 9dc0eb without authorization — both objects
  and their failed evidence are preserved, and the forward join J is
  the recovery, not a retroapproval; (2) the root forecast line
  "transcript 472" vs measured order 470L + active 8B = 478
  (arithmetic); (3) draft clocks near 06:20Z were future guesses —
  actual tool times are recorded in the helper receipt
  (06:04:30Z import FAIL native 1; 06:04:44.482..48.599Z native 0;
  commit I3 06:06:12Z).

## Recommended strategic follow-up

Factual only; no selection made: the P6 failure is a real boundary in
the public whole-session mechanism (post-termination restoration
re-acquire does not complete within the bounded window at the frozen
SDK version). The next formal round — further diagnosis of the
restoration path, a foundation-side fix, or scope re-decision — is
root's decision. This report proposes no workaround, no pin change,
and no new feature. After this increment is resolved, root's next
public 0.2 qualification remains INERT/unassigned until the actual
final order. No release, acceptance, or next-order claim is made by
coding.
