# OAP 083-4-a execution report — freeze-time canonical revision coherence

## 1. Status

| Field | Value |
| --- | --- |
| Round | 083-4-a (numeric objective 083, increment 4, round letter a) |
| Order | `oap/orders/083-4-a-freeze-revision-coherence.md` (195 lines) |
| Order SHA-256 | `0fceb3bf6408d45da9c4eb212a73aa2331c9c6ebbd3df99445280118cdee1633` |
| `oap/active` bytes | `083-4-a\n` (8 bytes: `3038332d342d610a`) |
| Control FIFO receipt | exact ASCII `OK` (2 bytes `4f4b`, no LF) delivered 2026-10-18T04:55:00.951186Z |
| PR mode | CREATED_NEW_PR |
| Status | COMPLETE |
| Human full-product goal | still active; numeric 083 remains PARTIAL (this is one prerequisite only) |

## 2. Repository and PR identity

| Field | Value |
| --- | --- |
| Repo | `ulfe-lmi/slaif-agent-site` |
| PR | #106 — <https://github.com/ulfe-lmi/slaif-agent-site/pull/106> (state OPEN at report time) |
| Branch | `oap/083-4-a-freeze-revision-coherence` (exactly one new branch/PR) |
| Base | `main` |
| Verified remote base (starting remote SHA) | `c5b5d425b9600ef7ee85c22453bb4122bf1fbfa9` at 2026-10-18T04:54:28Z (PR #102 merge `c5b5d425`, 04:38:55Z; post-merge CI `39097820342` + CodeQL `39097820344` SUCCESS, run_attempt 1, per activated order) |
| Literal implementation head (I) | `fc6752b42056f23465e8d8770af13eff7cea3ca3` |
| Report publication commit | SELF (this report; sole path; first parent exactly I) |
| Final report-only head (S) | `SELF` — the commit of this report (sole path `oap/reports/083-4-a-freeze-revision-coherence.md`, first parent exactly I). Remote identity verified externally after the push (head = SELF, parent = I, sole path, report bytes == pushed blob); the verification records live in `/tmp/oap-083-4-a/`, not in this immutable report |

## 3. Pushed commits (T → I → S)

| SHA | Time (UTC) | Content |
| --- | --- | --- |
| `afd08590b830f078be0719575bc74bad2ad3d1b4` | 2026-10-18T04:59:02Z | T-4a transcript: activated order + active bytes (unchanged order) |
| `aeaa884dafeac03cea00efb082d683dff483bd1c` | 2026-10-18T07:53:16Z | Implementation (4 production files) |
| `0bba84fc6de941402eed923a9e322e8f1251946b` | 2026-10-18T07:53:24Z | Tests (13 test/pin files) |
| `31a6cd1af4114180dbe7696b225c61aa819f4af3` | 2026-10-18T07:53:30Z | Current-truth docs (4 files) |
| `fc6752b42056f23465e8d8770af13eff7cea3ca3` | 2026-10-18T08:02:44Z | I: typed blocker-match closure guard (mypy `[misc]` found by CI at `31a6cd1`) |
| `SELF` (this report) | 2026-10-18 (pushed last) | S: report-only child, first parent I, sole path this file |

## 4. Exact changes at I (23 files, +3360/−58)

### 4.1 Production/config — 4 files (budget ≤6 incl. 1 migration)

| File | +/− | Change |
| --- | --- | --- |
| `services/backend/src/slaif_agent_site/db/alembic/versions/075_001_freeze_revision_coherence.py` | +562/−0 | New developer migration: swaps only `control.slaif_review_workspace_state(uuid)`. Itemization: 52-line module docstring; `_MATERIALIZER_070` exact 070_001 body (lines 53–285, 233 lines — the necessary exact SQL downgrade restoration, counted separately per order); 4 comment lines; `_MATERIALIZER_075` new body (lines 290–542, 253 lines, two surgical changes only); ownership/ACL re-assert + upgrade/downgrade (lines 543–562, 20 lines) |
| `services/backend/src/slaif_agent_site/review_worker/accept_job.py` | +55/−9 | Acceptance preflight: stored snapshot/site/workspace binding + trusted stored revision validated against the locked current revision BEFORE replay normalization/digest comparison; stable `SITE_REVISION_CHANGED` with no canonical mutation/media finalization/revision/terminal-accept/audit/outbox effect |
| `services/backend/src/slaif_agent_site/review_worker/freeze_job.py` | +10/−0 | Docstring: lock-order explanation (workspace row → advisory 280 → site row, held through snapshot completion and job terminal) |
| `services/backend/src/slaif_agent_site/bootstrap/service.py` | +1/−0 | `075_001` added to the downgrade-compatibility list |

Production lines excluding the 233-line downgrade restoration: +395/−9 (raw
git counts; see §4.5 for the line-count convention).

The two surgical 075 SQL changes (every other statement byte-identical to 070_001):

1. After the workspace-row `FOR UPDATE` and the established workspace lifecycle
   advisory lock (key 280), the canonical site row is locked `FOR UPDATE` in the
   same workspace-then-site order the acceptance path already uses; its
   `canonical_revision` and `status` are captured in that single locked read
   before the COW context/content read. The pre-lock `ACTIVE` `EXISTS` remains a
   fast fail only, and the same `REVIEW_SITE_NOT_ACTIVE` fail-closed guard is
   re-asserted against the locked row after the wait (a status change spanning
   the lock wait cannot go stale).
2. The materialized document reports that locked canonical revision as
   `base_site_revision` (previously the workspace-creation-time
   `workspace.base_site_revision`).

Lock ordering: workspace row → advisory 280 → canonical site row, identical to
the acceptance verification order, so no same-site freeze/accept deadlock; waits
are bounded by the existing statement lock-timeout surface and the row lock is
xact-level, released atomically on rollback/job terminal. No new runtime
authority: no tables, roles, or other function bodies change; signature/owner/
ACL re-asserted unchanged.

Downgrade identity: `_MATERIALIZER_070` restores the exact 070_001 body
(sha256 `b0dbd30cdadcf444c8806068693d6f94960ed1438ebd1b56a5dc0e0fe46dcd8a`,
`CREATE OR REPLACE` keyword normalization only); independently verified by
strategy via Python-AST selection of the 070 SQL constant and the 075
assignment (`/tmp/oap-083-4-a/current-downgrade-AST-independent-review.json`).

### 4.2 Test/pin — 13 files (budget ≤12; variance +1, itemized below)

| File | +/− | Role |
| --- | --- | --- |
| `services/backend/tests/integration/test_freeze_review_snapshot.py` | +1910/−0 | 5 new criterion tests (below) appended to the existing 083/1..3 module (5 pre-existing tests unchanged) |
| `services/backend/tests/unit/test_review_worker.py` | +204/−0 | 3 new mutation-sensitive unit tests for the preflight ordering |
| `tests/e2e/freeze-review-snapshot.spec.ts` | +344/−0 | Pure addition (single hunk from base line 619 onward; the 2 original contracts `freeze-to-review` (line 261) and `fail-closed-negatives` (line 508) are byte-unchanged): 6 helper functions + exactly 1 added contract `freeze-review-snapshot-two-workspace-revision-coherence` (the A proof) |
| 10 head-pin files (`test_agent_mutations.py` +11/−11, `test_agent_page_style.py` +3/−3, `test_cache_outbox_consumer.py` +3/−3, `test_control_database_integration.py` +3/−3, `test_database_bootstrap.py` +6/−6, `test_editable_domain_proof.py` +1/−1, `test_human_agent_session_control.py` +1/−1, `test_real_human_discard.py` +3/−3, `tests/unit/test_control_database.py` +5/−5, `tests/unit/test_foundation_contract.py` +3/−1) | +39/−37 | Mechanical required head pins `074_001` → `075_001` after the new migration; no behavior change |

Variance explanation: 13 = 10 mechanically required pin updates (the migration
head advanced) + 3 evidence files touched (new integration criterion tests in
the existing module, new unit tests in the existing module, appended E2E
coherence case + helpers in the existing spec). The order's criterion F
itself mandates "complete unfiltered integration directory including new
cases" and the A–E criteria; the pin count was not knowable before the head
advanced.

### 4.3 Docs — 4 files (budget ≤6)

| File | +/− | Change |
| --- | --- | --- |
| `docs/FOUNDATION_INTEGRATION.md` | +31/−0 | New "Review revision and first-touch baseline" section: distinguishes frozen review revision (B, locked at freeze) from workspace-creation/first-touch baseline (A preserved, no rebase, `BASE_ROW_CHANGED` intact) for readers, plus named remaining closure families |
| `oap/INCREMENTS.md` | +3/−6 | 083/3 row → merged PR #102 @ `c5b5d425` 2026-10-18; 083/4 in flight |
| `oap/MVP-CONTRACT-AUDIT.md` | +3/−3 | Complete-snapshot/render invariant row: 082 scoped delivery COMPLETE but full invariant PARTIAL with named closure families (frozen model/content/style inputs, dynamic query/binding/render fidelity, immutable operation/dependency/audit binding, re-review/multiple-snapshot, generic page-DML, foundation-row conflicts); 29.4 row PARTIAL |
| `oap/MVP-PROGRESS.md` | +2/−2 | Current-truth rows for 083/4 |

### 4.4 Transcript — 3 paths (budget 3)

`oap/orders/083-4-a-freeze-revision-coherence.md` (+195/−0, unchanged bytes),
`oap/active` (+1/−1), this report at S (+N/−0, sole path of S).

### 4.5 Budget variance summary

- Production/config: 4 ≤ 6 ✓ (1 migration ✓); generated: 0 ✓; docs: 4 ≤ 6 ✓; transcript: 3 = 3 ✓
- Test/pin: 13 vs ≤12 → **variance +1** (itemized in 4.2)
- Line-count convention and totals: these are raw git line counts, not an
  exact semantic "substantive line" measurement — they include comment,
  docstring, fixture-helper, and test-scaffolding lines, and deletions are
  counted separately. Excluding only the necessary exact-SQL downgrade
  restoration: production +395 (628 additions − 233-line `_MATERIALIZER_070`
  assignment span) + tests +2497 = **2892 raw additions vs target ≤1600
  (+1292 over)**. Root's independent cumulative cross-check: 3171 raw
  production+test add+del (628+9+2497+37); minus 231 SQL statement lines
  = 2940, or minus the 233-line assignment span = 2938. Both conventions
  exceed the estimate; the variance is disclosed and was reviewed
  pre-publication; no scope waiver is claimed. Itemized drivers: new
  integration criterion tests +1910 (B/C/D/E/F proof, the dominant share,
  ordered by criteria A–F), new unit tests +204, added E2E coherence case +
  helpers +344, pin updates +39/−37. No size was hidden through
  continuations; the single increment stays coherent.

## 5. Per-criterion evidence (A–F)

### A — public authenticated two-workspace revision coherence

- Source: the single E2E contract added by this round,
  `freeze-review-snapshot-two-workspace-revision-coherence`
  (`tests/e2e/freeze-review-snapshot.spec.ts:808`, appended to the existing
  spec; line numbers are head-relative) plus the DB-level twin
  `test_two_workspace_revision_coherence_and_stale_refusal`
  (`test_freeze_review_snapshot.py:1725`).
- Proof shape: W created/edited at A; a different authorized human workspace
  publishes an unrelated composition change to B via the existing Editor API /
  069 authorization with the legitimate authenticated CSRF contract
  (`adminCsrf`; no test-only actor, no hidden canonical SQL mutation — fixture
  seed code only where privileged setup is allowed); W then freezes through the
  real worker flow. The frozen document retains B and the meaningful visible
  B-plus-W content with a byte-valid digest; the real public `/review/<ws>/`
  render (through public NGINX in the Compose stack) shows the B+W headings and
  displayed reviewed/current revisions agree before another publication.
- Local: contract PASSED in the complete 19-project Compose smoke run 3
  (`/tmp/oap-083-4-a/compose-smoke-3.log:821`), part of `SMOKE_4A_EXIT:0`
  2026-10-18T07:51:47Z.
- CI: covered by `Node contracts` + `Compose and edge packaging` (both SUCCESS
  at I; see §8).

### B — same-site accept/freeze serialization, both orderings

- Source: `test_same_site_accept_freeze_serialization_both_orderings`
  (`test_freeze_review_snapshot.py:2004`) — real production lock surface
  (row locks + advisory lock), no sleep-only race: a fixture blocker holds the
  site row, real accept and freeze tasks queue on it, ordered release, and
  direct-edge blocker chains are asserted via `pg_blocking_pids` (25514→25513
  →25512-style edges; no transitive-closure assumption). Finite wait deadlines
  and guaranteed barrier/task/connection cleanup on every failure.
- Accept-wins: snapshot records the new revision and its content. Freeze-wins:
  snapshot completes coherently before acceptance progresses. No mixed
  revision/content, no deadlock, bounded runtime.
- Local: passed inside full run 1 (within its 324 passed) and full run 2
  (`/tmp/oap-083-4-a/logs/integ-full-2.log`: `325 passed in 4409.84s
  (1:13:29)`, `PYTEST_EXIT:0`, 08:35:07Z→09:48:41Z); preserved
  draft-iteration history in §6.5.

### C — post-freeze drift refused before digest rematerialization

- Source: integration `test_two_workspace_revision_coherence_and_stale_refusal`
  (`:1725`, second phase): after freeze at B, a different valid workspace
  accepts C; approval of the old snapshot is refused with
  `SITE_REVISION_CHANGED` (not a digest error); canonical
  bytes/revision/audit/outbox are proven unchanged by the refused attempt;
  pending W rows remain; the safe recovery state is preserved (no re-review
  feature added).
- Unit (mutation-sensitive by design — they assert the drift error is reported
  BEFORE the rematerialization step executes, and binding mismatch is
  classified as validation): `test_verify_snapshot_drift_reported_before_rematerialization`,
  `test_verify_snapshot_matching_revision_rematerializes`,
  `test_verify_snapshot_binding_mismatch_is_validation`
  (`tests/unit/test_review_worker.py:749/783/814`); all passed at I
  (31-gate clean copy: 791 unit+repo passed). Mutation-negative check
  (performed on the disposable clean copy, restored byte-identical
  afterward, working tree untouched): with the preflight revision guard
  (accept_job.py:309-310) removed, `test_verify_snapshot_drift_reported_before_rematerialization`
  FAILED — `AssertionError: materializer ran before the stored-revision
  check`, `1 failed, 2 passed`, `PYTEST_EXIT:1`
  (`/tmp/oap-083-4-a/mutation-negative.log`) — proving the tests bind the
  guard's behavior, not merely matching constants.

### D — first-touch baseline survives freeze (public conflicts API)

- Source: `test_first_touch_conflict_baseline_survives_freeze`
  (`test_freeze_review_snapshot.py:2396`): public frozen foundation inspection
  `CowReviewer.conflicts(session_id, schema="content")` before and after the B
  freeze for a genuinely concurrently changed touched row; `BASE_ROW_CHANGED`
  is still reported; original first-touch baselines unchanged (no rebase, no
  private `_changes`/`_cow_*` substitution). Human/capability/site-negative
  tests preserved.
- Local: passed inside full run 1 (within its 324 passed) and full run 2
  (`/tmp/oap-083-4-a/logs/integ-full-2.log`: `325 passed in 4409.84s
  (1:13:29)`, `PYTEST_EXIT:0`, 08:35:07Z→09:48:41Z).

### E — lock failure rolls back together; no leaked site lock

- Source: `test_freeze_site_lock_failure_rollback_no_leaked_lock`
  (`test_freeze_review_snapshot.py:2592`): cancellation/DB failure before
  completion rolls back snapshot insertion and REVIEW/job terminal together;
  no site lock leaked (verified with the catalog after rollback); reclaimed
  freeze remains idempotent; existing browser evidence drain/cancel and worker
  retry semantics exercised; old snapshot byte-identical.
- Local: passed inside full run 1 (within its 324 passed) and full run 2
  (`/tmp/oap-083-4-a/logs/integ-full-2.log`: `325 passed in 4409.84s
  (1:13:29)`, `PYTEST_EXIT:0`, 08:35:07Z→09:48:41Z).

### F — migration roundtrip, gates, full integration, smoke, CI

- Migration roundtrip + exact privilege delta:
  `test_075_001_round_trip_exact_restore_and_locked_materializer`
  (`test_freeze_review_snapshot.py:1545`): upgrade applies 075; downgrade
  restores the exact 070 body (byte-identity asserted), ownership/search_path/
  grants re-asserted, no extra roles; locked materializer behavior asserted on
  the post-upgrade function. Passed in the full runs.
- Clean tracked verification copy `/tmp/slaif-verify-4a` at I: identity
  1086/1086 tracked entries blob-verified
  (`/tmp/oap-083-4-a/verify-4a-identity.json`, tree
  `93ed935bc3ac402c473d31773aa199a179b0aabe`); then all 31 standing gates
  EXIT 0 (`/tmp/oap-083-4-a/verify-4a-gates.log`): uv lock/sync, ruff
  check/format, mypy (311 files), unit+repo pytest (791 passed), uv build,
  10× `--check` process smoke, node/pnpm versions, pnpm
  install/lint/format:check/typecheck/test/build/licenses, compileall,
  unittest repository, `tools/check_repository.py`, `tools/check_mermaid.py`
  (with temporary `kernel.apparmor_restrict_unprivileged_userns` 1→0→1,
  restored and recorded in-log), markdownlint-cli2@0.23.2 `**/*.md` clean.
- Complete unfiltered integration directory (disposable PostgreSQL 18.6,
  fresh DB per case via plain `CREATE DATABASE`, fixture lifecycle
  `services/backend/tests/conftest.py:106-183`): run 1 FAILED once
  (`PYTEST_EXIT:1`, 1 failed/324 passed in 4018.76s — §6.4); run 2 — one
  complete unfiltered run, actual result (`/tmp/oap-083-4-a/logs/integ-full-2.log`):
  `325 passed in 4409.84s (1:13:29)`, `PYTEST_EXIT:0`
  (2026-10-18T08:35:07Z→09:48:41Z). The required complete-run exit 0 rests
  on run 2 alone; run 1's 324 passed are not aggregated with it.
- Complete public Compose six-device smoke: run 3 `SMOKE_4A_EXIT:0`
  2026-10-18T07:51:47Z, 19 projects
  (setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6
  agent-sessions=2 agent-workspace-puck=2 freeze-review-snapshot=1
  review-surface=1 accept-lifecycle=1 discard-lifecycle=1 media-publication=1)
  with the freeze-review-snapshot project executing all 3 of its contracts —
  the added coherence case plus the 2 unchanged originals — earlier failed
  runs disclosed in §6.2/§6.3.
- GitHub required checks: 20/20 SUCCESS at I (wf run IDs `39109952661` CI,
  `39109952660` CodeQL, both run_attempt 1 — §7). At S: PENDING/not-yet-
  observed at publication (see §8); verified externally before the response
  is sent; this report is never amended for later observations.
- Contracts/packages/locks/pins unchanged (not in the I diff); recursively
  stripped OpenAPI digest (all `x-slaif-` keys removed at every nesting level,
  lists recursed, `sort_keys=True` compact separators, UTF-8, no trailing
  newline) recomputed at I on `contracts/openapi/agent-v1.json` (47 paths) =
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83` exactly.

## 6. Failed attempts and their disposition (all preserved, none hidden)

### 6.1 mypy at `31a6cd1` (fixed before I)

CI Python 3.13 job `117622318846` at head `31a6cd1`:
`mypy services/backend/tests/integration/test_freeze_review_snapshot.py:1395`
error `"None" not callable [misc]`, checked 311 files, exit 1 (exact log
`/tmp/oap-083-4-a/ci-first-head-python313.log`; Python 3.12/3.14 jobs failed
with the same finding; long jobs were cancelled, fast jobs succeeded). Local
31-gate run at `31a6cd1`: 30/31 with mypy EXIT:1
(`/tmp/oap-083-4-a/verify-4a-gates-run-31a6cd1.log`). Fix at I (`fc6752b`):
typed the blocker-match closure guard (`blockers_match` parameter with
`Optional` narrowing) preserving the exact phase/blocker assertions; no
ignore/exclude/weakening. Verified: local 31/31 at I and CI Python 3.12/3.13/
3.14 SUCCESS at I.

### 6.2 Compose smoke run 1 (fixed in-spec, no product change)

`/tmp/oap-083-4-a/compose-smoke.log`: strict-mode violation in the new spec —
the heading locator `"Freeze coherence"` also matched the page title; fixed
with `exact: true` (spec line ~945). Run 2 aborted in `review-surface` before
the `freeze-review-snapshot` project was reached (§6.3), so only the complete
run 3 proves the fixed locator.

### 6.3 Compose smoke run 2 (transient 503; run 3 complete pass)

`/tmp/oap-083-4-a/compose-smoke-2.log:810`: `review-surface` project, contract
`review-surface-review-render-and-summary`, line 479,
`POST /api/agent/v1/preview-runs` expected 202, received 503; the smoke then
aborted (`SMOKE_4A_EXIT:1` 2026-10-18T07:31:34Z) before the
`freeze-review-snapshot` project ran. Service logs were not captured (sidecar
script bug: `docker compose ps` exited 0 for the missing project), so the
original exception was NOT captured; the cause is UNPROVEN. Hypotheses only
(not established): a pre-existing client-side 503 branch (e.g. pool-acquire
timeout/OSError or an unmapped `PostgresError`) in the preview-run creation
path — the 503 mapping also covers broader authentication/read error paths,
and absence of any one server-side error does not select a specific
exception. No product path by which 083/4 changes that surface (surface
untouched by this round, fresh workspace, preceding requests in the project
OK). Not labeled a flake or root-caused; the subsequent complete run 3 passed
(`SMOKE_4A_EXIT:0`), which is the required evidence.

### 6.4 Full integration run 1 (single 503; run 2 is the required result)

`/tmp/oap-083-4-a/logs/integ-full-1.log` (2026-10-18 ~07:14Z→08:21Z):
`PYTEST_EXIT:1`, `1 failed, 324 passed in 4018.76s`. Failed node
`tests/integration/test_agent_mutations.py::test_agent_relation_and_view_hostile_matrix_and_races`
at line 13097: after `_set_resource_constraints` (allowed `matrix-target`
only), `GET /api/agent/v1/content-items/{source_id}/relations` expected 403,
received 503
`{"error":{"code":"SERVICE_UNAVAILABLE",...,"request_id":"req_7fa8540cb8b44deabbdbe66e0b389889"}}`.

Bounded observation performed (no security/timeout/quota changes):

1. Server-side window: PG container log for 07:31:20–07:31:52Z (logged at
   `warning` at the time) contains NO error on the failed read path — only
   expected hostile-matrix assertion errors from neighboring sub-cases and two
   `checkpoint starting: immediate force wait` / complete pairs at 07:31:26.284
   and 07:31:38.351, observed during the per-case CREATE/DROP DATABASE
   lifecycle (the fixture issues plain `CREATE DATABASE` with no strategy
   clause — PG 18's default copy strategy is WAL_LOG — so the copy method of
   those checkpoints is not asserted, and they are not attributed to the
   failed read).
2. Unchanged-code proof (root/strategy): the failing test's AST and the Agent
   HTTP + read-service blobs are unchanged versus main `c5b5d425`; this round
   touches no route on that surface (the 503 is produced only by
   `OSError`/`TimeoutError` or an unmapped `PostgresError` in the pre-existing
   `_fetch` mapping — P0007 would have returned 403).
3. Targeted repro in isolation with the same disposable DB:
   `PYTEST_EXIT:0`, `1 passed in 29.81s`
   (`/tmp/oap-083-4-a/logs/integ-single-1.log`). A passing isolated retry is
   recorded as observation, not as flake/root-cause proof.
4. Full directory rerun with server-side capture enabled on the disposable
   test host only (`log_min_messages=debug1`, `log_disconnections=on`,
   `log_statement=mod`, `log_lock_waits=on`, `log_min_duration_statement=1000`;
   reversible `ALTER SYSTEM`, no product change): actual terminal result
   `325 passed in 4409.84s (1:13:29)`, `PYTEST_EXIT:0`
   (2026-10-18T08:35:07Z→09:48:41Z) — the previously failing
   hostile-matrix test passed in run 2 under the same conditions, with no
   server-side error recurrence for it in the captured log.

Honest classification at publication time: the original exception/SQLSTATE
for the run-1 503 was NOT observed — the app's pre-existing 503 handler
returns a generic body (unchanged by this round) and the server logged at
`warning` at the time. The product's 503 mapping covers multiple
client-side/exception paths (e.g. `OSError`/`TimeoutError` and unmapped
`PostgresError` in the read path, plus broader authentication/read error
paths); the absence of a server-side error in the window does not identify a
specific one. Every path named above is a hypothesis, not an established
cause. The cause remains UNPROVEN and is disclosed, not explained away; the
required complete-run exit 0 is evidenced by run 2 alone (its actual
terminal result is recorded verbatim in F and in item 4 below; a passing
rerun is not labeled root-cause proof).

### 6.5 New-test draft iterations (test-side only, all preserved)

While developing the five new integration tests (before finalization, all
against pre-commit working-tree code; no product file changed after the
implementation commit), focused iterations failed and were repaired on the
test side only:

- `integ-0834-focused.log` (06:24Z): 5 failed / 5 passed — initial drafts of
  the five new tests (B observer/transaction handling, roundtrip seed data).
- `integ-0834-focused2.log` (06:40Z): 3 failed / 7 passed.
- `integ-0834-focused3.log` (07:10Z): 1 failed / 9 passed — only the roundtrip
  test failed, from seeding a local username violating the pre-existing
  `user_account_local_username_shape` check constraint (test fixture data, not
  product); repaired in the test.
- Disposable B diagnostic harness `_diag_b.py` (never committed, removed
  before commit): 4 failed diagnostics — asyncpg `InterfaceError` (harness
  connection lifecycle), `AttributeError: 'Pool' object has no attribute
  get_queued` (observer API), missing `await`, `AttributeError` on
  `Connection` (commit lives on `Transaction`, not `Connection`) — then PASS
  in 31.00s with correct transaction lifecycle and real lock evidence
  (`diag-b-5.log`: tuple `AccessShareLock`, `RowShareLock`/`RowExclusiveLock`
  granted rows). All four are diagnostic-harness bugs, not product failures.
- Roundtrip reruns: `integ-0834-roundtrip-2.log` 1 failed →
  `integ-0834-roundtrip-3.log` 1 passed in 29.77s.

Final committed form: all five new tests green inside full run 1 (within its
324 passed) and in full run 2 (see F/§6.4). No product code was changed in
response to any of these failures.

## 7. GitHub required checks at I `fc6752b` (20/20 SUCCESS)

Workflow runs (head `fc6752b`, event `pull_request`, run_attempt 1,
independently verified 2026-10-18T08:34Z): CI `39109952661` completed SUCCESS;
CodeQL `39109952660` completed SUCCESS.

| # | Check | Job/check-run ID | State at I |
| --- | --- | --- | --- |
| 1 | Analyze (actions) | 117623757573 | SUCCESS |
| 2 | Analyze (javascript-typescript) | 117623757607 | SUCCESS |
| 3 | Analyze (python) | 117623757528 | SUCCESS |
| 4 | CodeQL (aggregate) | wf 39109952660 | SUCCESS |
| 5 | Compose and edge packaging | 117623790132 | SUCCESS |
| 6 | Dependency review | 117623790194 | SUCCESS |
| 7 | Detect supported languages | 117623733945 | SUCCESS |
| 8 | Foundation PostgreSQL 14 | 117623790258 | SUCCESS |
| 9 | Foundation PostgreSQL 15 | 117623790302 | SUCCESS |
| 10 | Foundation PostgreSQL 16 | 117623790253 | SUCCESS |
| 11 | Foundation PostgreSQL 17 | 117623790273 | SUCCESS |
| 12 | Foundation PostgreSQL 18 | 117623790294 | SUCCESS |
| 13 | Markdown | 117623790288 | SUCCESS |
| 14 | Mermaid | 117623789967 | SUCCESS |
| 15 | Node contracts | 117623790264 | SUCCESS |
| 16 | Python 3.12 quality and package | 117623790265 | SUCCESS |
| 17 | Python 3.13 quality and package | 117623790221 | SUCCESS |
| 18 | Python 3.14 quality and package | 117623790261 | SUCCESS |
| 19 | Repository policy | 117623790152 | SUCCESS |
| 20 | Supply-chain evidence | 117623790257 | SUCCESS |

No missing/neutral/skipped/cancelled/pending at I. No CI rerun was used at I.

## 8. GitHub required checks at S (final report-only head)

At the moment this report is committed and pushed, S is the just-pushed
report-only head; its required checks have not run to completion and no
conclusion exists yet, so this immutable report records **no CI state at S**
(PENDING at publication). The order's 20-check mandate at the exact final
report SHA is verified externally by the executor after the push — by
polling the workflow runs for head S to all-20 COMPLETED/SUCCESS (run_attempt
1, integration application 15368, CodeQL aggregate 57789) and recording the
result in `/tmp/oap-083-4-a/ci-jobs-S-*.log` — and is independently gated by
strategy. This report is not amended for later-observed CI; the observed CI
recorded above (§7, head I) is the only in-report CI evidence.

## 9. Environment, setup, dependencies

- uv 0.12.5; Python 3.13.14 (uv-managed); Node 24.x; pnpm 11.22.0; TypeScript
  6.0.3. All gates ran `--frozen`.
- Integration DB: local disposable PostgreSQL 18.6 container
  `slaif-integration-pg-0833b` (Alpine; created 2026-10-17T22:24Z; locally
  generated non-production credentials, not printed). Per-case fresh
  `slaif_test_<uuid10>` databases via plain `CREATE DATABASE` (no strategy
  clause; PG 18 default copy strategy — the copy method is not asserted
  here), product `provision()` in TEST mode, per-case login roles, teardown
  `pg_terminate_backend` + `DROP DATABASE` + role drops
  (`services/backend/tests/conftest.py:106-183`). No production system
  touched.
- Clean verification copy `/tmp/slaif-verify-4a` (git blob-verified 1086/1086
  at I) is authoritative for the standing gates because the in-place working
  tree has untracked runtime artifacts (`.codex/`, `CODEX-SESSIONS.md`,
  `codex.sh`) that break in-place `pnpm lint`'s eslint config resolution;
  those untracked files were preserved, never committed or modified.
- Mermaid check: temporary `kernel.apparmor_restrict_unprivileged_userns`
  1→0→1 (sudo, recorded in the gate log with restoration).
- Diagnostic logging on the disposable test PG (§6.4.4) is test-host only and
  reversible; no product configuration changed.
- `rm -rf` was unavailable in this executor environment (sandbox rejects it);
  fresh directories were used instead — no impact on results.

## 10. Docs updated (same PR)

`docs/FOUNDATION_INTEGRATION.md` (new reader-facing section: frozen review
revision B vs creation/first-touch baseline A — no rebase,
`BASE_ROW_CHANGED` intact — plus named remaining closure families: frozen
model/content/style inputs, dynamic query/binding/render fidelity, immutable
operation/dependency/audit binding, re-review/multiple-snapshot lifecycle,
generic page-DML promotion, foundation-row conflicts), `oap/INCREMENTS.md`,
`oap/MVP-CONTRACT-AUDIT.md` (082 scoped delivery COMPLETE but the full
frozen-snapshot/render invariant PARTIAL; numeric 083 PARTIAL),
`oap/MVP-PROGRESS.md`. No architecture/constitution/protocol edits. No numeric
083 COMPLETE, no MVP/release-ready, no generic-page-DML acceptance claim.

## 11. Security and known limitations

- No new credentials/outbound/telemetry/license; no new runtime authority;
  foundation remains public registry `agent-cow-postgresql==0.2.0` with frozen
  locks; no private SQL, monkeypatch, or relaxed FK/overwrite policy.
- Server-owned context preserved; the only behavioral change is the materializer
  lock/capture ordering plus the preflight revision gate, both fail-closed.
- Known disclosed limits (unchanged, per order): foundation composite-FK
  dependency limitation (composition-only proof is scoped); old snapshots
  remain viewable and stale (never rewritten); the full snapshot/render/
  operation/dependency/audit invariant remains PARTIAL (083/4 is one
  prerequisite, not completion of generic immutable review/publication).
- The run-1 integration 503 cause is UNPROVEN (disclosed in §6.4); it does not
  alter the required-run evidence (run 2) or the CI results.

## 12. Confirmations

- Scope: exactly the activated order's bounded areas; no scope expansion, no
  adjacent work, no new semantic family; out-of-scope items left untouched.
- Secrets: no real secrets, capabilities, cookies, or production credentials
  in this report, the diff, or pushed artifacts; locally generated disposable
  test credentials not printed.
- Production: no production system/data/credential accessed; all DB work on
  the disposable test container and Compose smoke containers.
- Skips/pending/missing: none claimed as pass; every skipped/pending/failed
  item is disclosed (§6, §8). No test skipped.
- GitHub: exactly one PR (#106); no second PR, no auto-merge, no merge, no
  close; executor did not advance the roadmap. Order/active bytes committed
  unchanged; no historical report/order edits.
- No repository mutation follows S; this report is the final pushed content
  until strategy acts.
