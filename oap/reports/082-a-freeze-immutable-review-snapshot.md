# OAP Coding-Agent Report — 082-a

## Work order

- Order: `oap/orders/082-a-freeze-immutable-review-snapshot.md` (activated via
  `oap/active`, strategic FIFO `OK` received 2026-10-04).
- Mode: `NNN-a` — one fresh branch + one new PR from authoritative remote main.
- Branch: `oap/082-a-freeze-immutable-review-snapshot`.
- PR: #97 (URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/97`), state OPEN.
- Base: main @ `c48849f149417fccf5cc0a152bc3ca39aaaf49ba` (PR #96 merged, 081-a).
- T commit (order + active bytes + preplan supersession):
  `b702a5f037994b3752c3ddf480cf9aa3c394762d`.

## Status

COMPLETE (finite criterion list below; strategy independently reviews and
merges — COMPLETE never means accepted).

## Executive summary

082-a makes freeze real: a human Control endpoint freezes an active workspace
atomically (FREEZING + full capability revocation + one durable FREEZE job),
a newly implemented review worker drains outstanding 072 durable browser runs
under a bounded 120 s evidence deadline (attach completed runs, bounded-cancel
the rest with `FREEZE_CANCEL`), materializes one immutable review snapshot
through a trusted SQL surface with a recomputable canonical digest, and moves
the workspace to REVIEW only inside the same locked transaction that writes the
SUCCEEDED job terminal row. The increment's single new migration
(`070_001`, 1065 insertions) adds the tables, functions, and
least-privilege worker role; the review worker becomes a real durable
loop (named config, claim/staleness recovery, heartbeats) behind a
narrow worker credential. R4 is verified, not
reworked: every live product-mutation family already takes the shared
workspace-lifecycle advisory lock (key 280) before its in-transaction ACTIVE
recheck; the freeze job is the only long-lived exclusive-280 acquirer (30 s
bounded). R5 freeze policy is bounded-cancel with no state-machine widening
(CANCELLED is written only from QUEUED/RUNNING, the terminal shape 035_001
already permits). New E2E Playwright project `freeze-review-snapshot` (2
contracts, 16th roster project) drives real browser + real PostgreSQL:
freeze-to-review with digest recompute and fail-closed negatives (CSRF-less
403, non-member no-oracle 404, wrong-site 404, malformed 422, re-freeze 409,
post-FREEZING agent denial 401 uniform for forged and revoked tokens).

Investigation note (verified root causes, no in-scope code change): the live
browser pipeline fails preview-document navigation with
`BROWSER_NAVIGATION_FAILED` because Next.js 308-redirects
`/preview/<wsId>/` to `/preview/<wsId>` and the worker's request confinement
authorizes only the first document hop; and, because freeze revokes the
capability within ~1 s, the dispatcher's terminal finalization for that run
fails the capability authorization gate and cannot land, so the run stays
RUNNING until the bounded cancel. Both are pre-existing 072-surface behaviors
(browser tooling is an explicit non-goal of this order) and make the E2E
freeze-policy outcome deterministically the bounded-cancel branch; both are
recorded as residual risks for 082/2 / 083.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: #97, OPEN, head branch `oap/082-a-freeze-immutable-review-snapshot`.
- Base: main @ `c48849f149417fccf5cc0a152bc3ca39aaaf49ba`.
- Starting remote main SHA (verified at branch creation):
  `c48849f149417fccf5cc0a152bc3ca39aaaf49ba`.
- T (order transcript commit): `b702a5f037994b3752c3ddf480cf9aa3c394762d`.
- I (first implementation push, superseded by F):
  `88a9315959586c0939a5fa910b2c71457c13ab54`.
- F (implementation head after the CI-surfaced lint repair, superseded
  by F2): `286e8bb4d7f8e6fe404808322a7796cafa0474a7`.
- F2 (implementation head after the CI-surfaced E2E race repair,
  literal): `7863989d544d474bd87fad1789fdb32f88cd8a26`.
- D (docs commit, literal): `987c0a2cb0e94116173dba22741a7e9bca9eba8a`.
- Report publication commit: SELF (report-only; its literal SHA is the
  remote PR head after publication, verified via `git ls-remote` and
  `gh pr view 97 --json headRefOid`), parent = D; the SELF commit
  changes only the new report file.
- Pushed commits: T (already pushed at activation), I, F, F2, D, SELF.
- Remote PR head verified to be the SELF SHA via `git ls-remote` and
  `gh pr view 97 --json headRefOid`.

## Changes made

### 1. Migration `070_001_freeze_immutable_review_snapshot.py` (1065/0)

- Tables: `control.review_job` (durable FREEZE jobs, partial unique index: at
  most one live job per workspace; CHECK-pinned claim shape),
  `control.review_snapshot` (immutable snapshot rows: workspace/site binding,
  status, revision watermark, pinned versions, normalized state, validation
  report, media references, browser evidence, payload, digest, created_by).
- `control.workspace.review_snapshot_id` (set only on the REVIEW transition).
- `control.slaif_workspace_freeze(uuid)` — replaces the 024_001 stub:
  ACTIVE -> FREEZING + `frozen_at`, revokes every unrevoked capability of the
  workspace, enqueues exactly one FREEZE job (idempotent under the partial
  unique index; retry path for a FREEZING workspace with no live job after a
  semantic job failure). `WORKSPACE_NOT_FOUND` / `WORKSPACE_NOT_ACTIVE`
  stable error codes.
- `control.slaif_human_agent_workspace_freeze(uuid, uuid, uuid)` — Control
  endpoint boundary: site-confined workspace lookup (missing -> empty result
  -> 404), platform-administrator or `workspace:freeze` membership permission
  gate (missing -> empty -> 404), delegates to the freeze function.
- `control.slaif_review_job_claim(text)` / `_heartbeat(uuid)` /
  `_terminal(uuid, text, text)` — worker job lifecycle; stale-claim recovery
  (CLAIMED without fresh heartbeat re-queues within the attempt budget, fails
  at budget). EXECUTE granted to `slaif_review_worker` only.
- `control.slaif_review_browser_runs_cancel(uuid)` — bounded cancel: every
  QUEUED/RUNNING run of the workspace -> CANCELLED with
  `error_code='FREEZE_CANCEL'`, `summary->>'cancelled_by_freeze'='true'`,
  terminal_lease_id kept (RUNNING) or minted (QUEUED), `audit.browser_event`
  CANCELLED row. The CANCELLED terminal shape is exactly what 035_001's CHECK
  constraints already permit; no 035_001 state machine is widened.
- `control.slaif_canonical_jsonb_text(jsonb)` (+ deterministic helpers) —
  canonical JSON text for digest computation.
- `control.slaif_review_workspace_state(uuid)` — trusted materializer:
  rebuilds the complete normalized state document (pages/compositions,
  collections/items, navigation, redirects, media, versions) under the
  exclusive product lock.
- `control.slaif_review_snapshot_complete(uuid, jsonb)` — the ONLY path into
  REVIEW: validates the row shape, recomputes and compares the canonical
  digest, inserts the immutable snapshot, transitions the workspace
  FREEZING -> REVIEW with `review_snapshot_id` set, atomically in one
  transaction.
- Role `slaif_review_worker` + login `slaif_review_worker_login`: SELECT on
  the read surfaces only, no UPDATE/DELETE on `review_snapshot` (grant-proof
  in the integration spec), EXECUTE only on the worker functions.

### 2. Review worker (real implementation, `review_worker/`)

- `config.py` (229): named config (`SLAIF_REVIEW_WORKER_*` env prefix,
  `extra=forbid`, `frozen`): poll 1.0 s, batch 1, staleness 60.0 s,
  drain-lock 30.0 s, evidence deadline 120.0 s, heartbeat 20 s, evidence poll
  2.0 s; narrow worker credential via mounted DSN file with expected
  database/login/privilege-role identity checks; mode development/test/
  production validation.
- `worker.py` (180): durable loop — claim (batch 1), heartbeat cadence,
  stale-claim recovery via the claim function, terminal handling, clean
  startup/shutdown; no listener, no Uvicorn.
- `freeze_job.py` (274): one locked database transaction per claimed job:
  exclusive product lock (`pg_advisory_xact_lock(hashtextextended(ws,280))`
  with `SET LOCAL lock_timeout = 30s`), in-transaction FREEZING recheck,
  `_drain_browser_runs` (poll outstanding QUEUED/RUNNING every 2 s until 0 or
  the 120 s bounded deadline, then `slaif_review_browser_runs_cancel`),
  materialization through `slaif_review_workspace_state`, snapshot document
  build (pinned versions, browser evidence from COMPLETED runs, cancelled-run
  report), `slaif_review_snapshot_complete`, job SUCCEEDED in the same
  transaction. Semantic failure paths mark the job FAILED with stable
  structured codes after rollback (workspace stays FREEZING, zero snapshot
  rows, REVIEW unreachable); 55P03 drain-lock timeout retries within the
  attempt budget (DRAIN_TIMEOUT at budget).
- `snapshot.py` (276): deterministic snapshot document assembly + validation
  (exact key set, canonical digest parity with the SQL recomputation).
- `__main__.py` / `__init__.py`: entrypoint wiring (`--check` stays
  health-only, binds no port, performs no mutation).

### 3. Control freeze endpoint (`control_api/`)

- `workspace_http.py` (+30): `POST /api/control/v1/sites/{siteId}/
  workspaces/{workspaceId}/freeze/` -> 202 `{job_id, status:"FREEZING"}`
  (idempotent: live FREEZING job -> same job 202; REVIEW/terminal ->
  409 `RESOURCE_CONFLICT`; unknown ids -> 404 `RESOURCE_NOT_FOUND`;
  malformed UUIDs -> 422 `VALIDATION_ERROR` at the path layer).
- `route_policy.py` (+6): route registered with the bound-session-CSRF
  mutation policy (human session + CSRF + `workspace:freeze` permission)
  exactly like the existing workspace routes.
- `database.py` (+9): `human_agent_workspace_freeze` adapter over the SQL
  boundary.
- `authority.py` (+4/-2), `bootstrap/service.py` (+1): revision-set and
  authority-surface bookkeeping for the new worker role/credential.

### 4. R4 shared-lock retrofit — verified, no function change

Every live product-mutation family already acquires
`pg_advisory_xact_lock_shared(hashtextextended(workspace_id::text, 280))`
before its in-transaction ACTIVE recheck; see the R4 compliance table below.
No function body, signature, or lock order was changed by this increment
(serialization-only requirement satisfied by verification).

### 5. Compose / local secrets / verify pins

- `compose.yaml` (+16): review-worker explicit `environment:` re-lists the
  four common keys (`SLAIF_LOG_FORMAT/LOG_LEVEL/MODE/PUBLIC_URL`) — the
  explicit block replaces the YAML-merge anchor env, so the four keys must be
  re-listed (media-service pattern) — plus the review-worker service wiring
  and the `review-worker-secret` volume.
- `tools/local_secrets/initialize.py` (+69): review-worker login + service
  DSN secret generation (24 -> 26 pins; 11 -> 12 pins in the packaging tests).
- `tools/compose/verify.py` (+52): exact-topology pins updated for the
  review-worker (volume inventory, secrets-init command
  `--review-worker-directory /run/slaif-review-worker`, EXPECTED_MOUNTS
  secrets-init writable + review-worker read-only, per-service secret
  mounting, safe-environment allowlist for the five
  `SLAIF_REVIEW_WORKER_*` keys, exact env assertion in `validate_config`).

### 6. Tests / evidence

- `tests/unit/test_review_worker.py` (583): named-config matrix, freeze-job
  transaction phase errors, snapshot document validation, worker loop
  semantics (claim/heartbeat/staleness/terminal).
- `tests/integration/test_freeze_review_snapshot.py` (856): full HTTP
  authorization/CSRF/state matrix (uniform 404 shape for no-permission and
  non-member, 409 post-REVIEW, 403 CSRF), durable job behavior (idempotency,
  one live job), drain policy (attach COMPLETED evidence; bounded cancel with
  FREEZE_CANCEL + cancelled_by_freeze), digest recompute parity, REVIEW-only-
  via-snapshot-complete (forced validation failure -> job FAILED, workspace
  FREEZING, zero snapshot rows), grant proofs (`has_table_privilege`
  UPDATE/DELETE false for every long-lived role, true for `slaif_owner`).
- `tests/e2e/freeze-review-snapshot.spec.ts` (619 after the F2 repair; 614 after the F repair; 616 as first pushed at I): new Playwright project
  (registered in `playwright.config.ts`, `tools/compose/e2e.sh` roster,
  `test_compose_smoke_contract.py` pin — 16th project): (1)
  `freeze-to-review`: real AGENT workspace + capability + real (long-running)
  browser run outstanding; human freeze via authenticated control API;
  policy outcome branch (attach or bounded cancel); REVIEW only after the
  snapshot exists; `review_snapshot_id` set; snapshot digest recomputed via
  psql; capabilities fully revoked (post-FREEZING Agent REST write ->
  uniform 401 `AUTHENTICATION_REQUIRED` for unknown and revoked tokens);
  canonical psql baselines (relative counts/digests). (2)
  `fail-closed-negatives`: CSRF-less state-changing freeze -> 403
  `AUTHORIZATION_DENIED`; non-member (no demo-site membership) -> uniform
  404 `RESOURCE_NOT_FOUND` across real and random workspace ids (no oracle);
  wrong site -> uniform 404; malformed ids -> 422 `VALIDATION_ERROR`;
  re-freeze of REVIEW -> 409 `RESOURCE_CONFLICT`; exactly one job + one
  snapshot for the probed workspace.
- Role/roster/pin updates (existing test files): `test_browser_run_control_
  plane.py` (order R1 mandates worker SELECT on `control.browser_run`; role-
  loop pin now asserts the worker's table-level SELECT succeeds while the
  other three relations stay denied — site confinement remains the
  functions' job), `test_process_entrypoints.py`, `test_foundation_contract.
  py`, `test_control_database.py`, `test_authority.py`, `test_sites.py`,
  `test_database_bootstrap.py` (bootstrap revision set +070_001),
  `test_control_database_integration.py`, `test_agent_mutations.py`,
  `test_agent_page_style.py`, `test_route_policy.py`,
  `test_human_agent_session_control.py`, `test_editable_domain_proof.py`,
  `test_local_roles.py`, `test_health_apps.py`, `test_local_secrets.py`
  (24->26, 11->12), `test_compose_policy.py` (review-worker env block +
  volume), `test_compose_smoke_contract.py` (e2e roster pin).

### 7. Documentation (R6, 4 surfaces)

- `README.md` (+2/-1): review worker + freeze capability in the current-
  truth service list.
- `oap/INCREMENTS.md` (+8/-2), `oap/MVP-PROGRESS.md` (+3/-3),
  `oap/MVP-CONTRACT-AUDIT.md` (+5/-5): 082/1 landed state, audit row updates.

## Files changed

I commit (implementation + evidence, diff T -> I): 41 files, +4503/-64:

| group | files | insertions | deletions |
| --- | ---: | ---: | ---: |
| production/config | 16 | +1247 | -5 |
| migrations | 1 | +1065 | -0 |
| tests/evidence | 24 | +2191 | -59 |
| generated | 0 | +0 | -0 |

F commit (in-scope CI repair, diff I -> F): 1 file, +0/-2 — removes
the dead `hex` helper in `tests/e2e/freeze-review-snapshot.spec.ts`
that CI `Node contracts` flagged (`@typescript-eslint/no-unused-vars`);
pure dead-code removal, no behavior change.
F2 commit (in-scope CI repair, diff F -> F2): 1 file, +18/-13 —
`waitForReview`'s no-snapshot-while-FREEZING invariant, which CI
`Compose and edge packaging` tripped via a read-skew race (the status
HTTP read and the psql count read straddled the snapshot transaction's
commit), is now enforced by a single atomic statement that observes the
snapshot row and the workspace status in one consistent read; same
invariant, race-free form. Implementation head (diff T -> F2): 41
files, +4506/-64.

D commit (R6 docs, diff F2 -> D): 4 files, +18/-11 (docs group).

Substantive implementation lines (production/config + migration insertions):
**2312** (budget 3500; the 20 production/config file review trigger NOT
fired: 16 measured).

Cumulative base -> head (base
`c48849f149417fccf5cc0a152bc3ca39aaaf49ba` -> SELF): the 45
implementation/docs files above (+4524/-75) plus the T transcript (order +
active + superseded-preplan note, 4 files, +547/-3, already pushed at T)
plus this report (1 file, added by SELF): 50 files, +5785/-78
(including the +714 lines of this report itself).

## Pre-declared budget check (order Section 10 vs measured)

| bucket | pre-declared | measured | status |
| --- | ---: | ---: | --- |
| production/config files | at most 18 | 16 | within (trigger at 20 NOT fired) |
| migrations | exactly 1 | 1 | exact |
| test/evidence files | at most 12 | 24 | EXCEEDED by 12 — disclosed and itemized below |
| generated-contract footprint | 0 | 0 | exact (R7 byte-identity) |
| docs footprint | 4 surfaces | 4 | exact |
| OAP transcript | order + active + report | order + active (T) + report (SELF) | exact |
| substantive lines | at most 3500 | 2312 | within |

Test/evidence overage (24 vs 12), itemized per the 081 precedent:
the pre-declared 12 assumed the new unit matrix, the integration spec, the
E2E spec, and a few roster pins. The honest footprint grew because (a) the
freeze surface touches every long-lived role/permission/route inventory
(`test_local_roles.py`, `test_health_apps.py`,
`test_foundation_contract.py`, `test_control_database.py`,
`test_process_entrypoints.py`, `test_authority.py`,
`test_route_policy.py` — 7 files), (b) the bootstrap revision-set pin
(`test_database_bootstrap.py`, `test_control_database_integration.py`),
(c) the compose/local-secrets topology pins (`test_local_secrets.py`,
`test_compose_policy.py`, `test_compose_smoke_contract.py`), (d) the order
R1 worker-SELECT pin (`test_browser_run_control_plane.py`), (e)
mutation-matrix pins whose expected error shapes were re-verified against
the new role surface (`test_agent_mutations.py`,
`test_agent_page_style.py`, `test_sites.py`,
`test_human_agent_session_control.py`, `test_editable_domain_proof.py` —
5 files), and (f) the E2E harness mechanical pins (`playwright.config.ts`
project registration, `tools/compose/e2e.sh` invocation + OK line,
`tools/compose/smoke.sh` login/secret roster 10 -> 11 and 23 -> 25 plus
`slaif_review_worker` in the database privilege matrix). Each is a pin
update, not new test logic beyond the three new files.

## Deviations and adaptations (order Section 9; one line each)

- E2E roster pins (`playwright.config.ts`, `tools/compose/e2e.sh`): new
  16th roster project `freeze-review-snapshot` registered and invoked —
  required for R8 E2E evidence; no behavior change.
- Bootstrap revision set (`bootstrap/service.py`): `070_001` added to the
  downgrade-compatible set — the established pattern R1 requires.
- Smoke service roster pins (`tools/compose/smoke.sh`, +5/-5): login-role
  count 10 -> 11 in the pg_auth_members membership pin, the connlimit
  matrix, the privilege matrix (whose role list gains
  `slaif_review_worker`), and the `exact-roles` OK line; secret-volume
  file count 23 -> 25 and unique postgres/login values 11 -> 12 — the
  order's new narrow credential follows the existing service-credential
  pattern (R1), and the hardcoded roster predates it; no security
  expectation weakened (checks retain their exact shape).
- Worker env in `compose.yaml`: `SLAIF_REVIEW_WORKER_*` block + dedicated
  `review-worker-secret` volume on the pre-existing `review-worker`
  service — explicitly allowed by the order ("new env for the worker
  credential is allowed and must be disclosed").
- New-test-file pins fixed during development (test-file-only edits, no
  product change): the integration role-loop pin shape and the
  uniform-404 body comparison stripping the per-request `request_id`
  (after the first full integration run), and the E2E spec's
  non-member no-oracle uniform-404 assertion (fast-iteration runs 3-4
  failed at that assertion, run 5 green 2/2; the final expectation
  matches the implemented uniform 404 no-oracle behavior).
- CI-surfaced in-scope repair (commit F): `pnpm lint` flagged the dead
  `hex` helper in the new E2E spec (`@typescript-eslint/no-unused-vars`
  at the I head's `Node contracts`); pure 2-line dead-code removal, no
  behavior change; full local Node gate re-run green at the F byte.
- CI-surfaced in-scope repair (commit F2): the F head's `Compose and
  edge packaging` failed both freeze contracts at
  `freeze-review-snapshot.spec.ts:247` (`expect(count).toBe(0)`,
  received 1) — a read-skew race in the NEW spec's
  no-snapshot-while-FREEZING check: the control-API status read and the
  psql count read are separate statements and can legally straddle the
  snapshot transaction's commit (the row and the FREEZING -> REVIEW
  transition commit atomically in `slaif_review_snapshot_complete`, so
  no product state is ever violated). Not the documented browser-flake
  class, so no re-run: the check was rewritten as one atomic statement
  (row + status observed in a single consistent read); same invariant,
  race-free form; full local Node gate green and the freeze project
  re-verified 2/2 PASSED on a fresh fixture-initialized stack at the
  F2 byte.

## Acceptance-criteria evidence

### Criterion 1 (migration up/down clean; R1 predicate matrix; privilege gate)

- `uv run --frozen pytest services/backend/tests/integration` full run
  (clean cluster): **244 items collected, 242 passed, 2 failed in
  2715.95 s (45:15)**; the 2 failures were in new-file assertions (role-loop
  pin shape; uniform-404 body comparison not stripping per-request
  `request_id`), both fixed in the test files; re-run of the two files:
  **7 passed in 82.22 s** -> full integration suite green
  (242 + re-run 7; the other 237 tests are unaffected by test-file-only
  edits).
- Unit suite: `uv run --frozen pytest services/backend/tests/unit
  tests/repository`: **786 passed**.
- Privilege gate: integration spec asserts EXECUTE on the worker functions
  for `slaif_review_worker` only, SELECT on `control.browser_run` for the
  worker (order R1), and `has_table_privilege` UPDATE/DELETE on
  `review_snapshot` false for every long-lived role / true for
  `slaif_owner`.

### Criterion 2 (freeze endpoint R3: states, auth, CSRF, idempotency)

- Integration HTTP matrix (242/7 green above): ACTIVE -> 202
  `{job_id, status:"FREEZING"}`; FREEZING with live job -> idempotent 202
  same job; REVIEW -> 409 `RESOURCE_CONFLICT`; unknown workspace/site ids ->
  uniform 404 `RESOURCE_NOT_FOUND` (no oracle); malformed UUIDs ->
  422 `VALIDATION_ERROR`; CSRF-less state-changing -> 403
  `AUTHORIZATION_DENIED`; no-permission member and non-member -> uniform
  404 shape (per-request `request_id` stripped before comparison).
- E2E negatives contract (live stack, real PostgreSQL): all named
  assertions passed — CSRF-less 403; non-member uniform 404 (real + random
  id); wrong-site uniform 404; malformed ids 422; re-freeze of REVIEW 409.

### Criterion 3 (review worker R2: durable job, drain, snapshot, REVIEW)

- E2E `freeze-to-review` (live stack): freeze with a real outstanding
  browser run; policy outcome = **bounded cancel** (see R5 decision record +
  investigation note); `waitForReview` deadline 240 s covers the 120 s
  evidence deadline; workspace reached REVIEW only after the snapshot row
  existed (asserted on every FREEZING sample: `count(*) review_snapshot =
  0`); `review_snapshot_id` set (`t`); snapshot digest recomputed via psql
  over `control.slaif_canonical_jsonb_text(payload)` matches (`t`);
  capabilities fully revoked (`count(*) revoked_at IS NULL = 0`); post-
  FREEZING Agent REST write -> uniform 401 `AUTHENTICATION_REQUIRED` for an
  unknown token and the (revoked) real token; canonical baselines (relative
  agent-workspace count, base-node count, browser-run count) unchanged.
- Integration: forced `slaif_review_snapshot_complete` validation failure ->
  job FAILED (stable code), workspace FREEZING, zero snapshot rows, REVIEW
  unreachable; drain attach branch (COMPLETED run ->
  `browser_evidence=[{"id": "<runId>"}]`) and bounded-cancel branch
  (`error_code=FREEZE_CANCEL`, `cancelled_by_freeze=true`,
  `browser_evidence="[]"`) both asserted.

### Criterion 4 (R4 lock retrofit: verified compliance, no change)

- R4 compliance table (family -> function/file -> lock before/after):

| mutation family | entry function(s) | shared-280 lock | before 082-a | after 082-a |
| --- | --- | --- | --- | --- |
| Agent REST data plane (all 074/078-era mutations) | `control.slaif_agent_require_capability` (before every 994-family lock) | shared 280 | since 050_001 | unchanged (verified) |
| Human editor mutations | `slaif_human_editor_workspace_assert` (exclusive 280 under `p_lock`, re-asserted 069_001) | shared (exclusive under p_lock) | since 028_001 / 069_001 | unchanged (verified) |
| Media mutations (068/079-1 upload + references) | `control.slaif_media_workspace_assert` (before 702/913 locks) | shared 280 | since 030_001 / 031_001 | unchanged (verified) |
| Browser control plane (runs/artifacts) | 035_001–037_001 claim/begin/complete/release family | shared 280 | since 035_001 | unchanged (verified) |
| Batch/collection operations | via the Agent REST require-capability boundary | shared 280 | since 050_001 | unchanged (verified) |

- The freeze job (`slaif_review_workspace_state` drain/materialize/complete
  transaction) is the ONLY long-lived exclusive-280 acquirer; it is bounded
  by `SET LOCAL lock_timeout = 30s` and retries within the attempt budget on
  55P03. No lock order is inverted anywhere by this change: every mutation
  takes shared 280 first, then finer-grained 994-family locks; the freeze
  takes exclusive 280 only, no 994 lock inside the transaction.

### Criterion 5 (R5 freeze-policy decision record)

- Decision: freeze = drain then materialize. Outstanding 072 durable runs
  are waited on for up to the evidence deadline (named config default 120 s,
  poll 2 s); runs reaching COMPLETED before the deadline are attached as
  browser evidence; runs still QUEUED/RUNNING at the deadline are bounded-
  cancelled (`FREEZE_CANCEL`, `cancelled_by_freeze=true`) and contribute no
  evidence. Cancelled-only-from-QUEUED/RUNNING: the 035_001 state machine is
  not widened (CANCELLED is already a permitted terminal; the CHECK pins
  were verified, no migration of 035_001 objects).
- Named config (R5 decision record): poll 1.0 s, batch 1, staleness 60.0 s,
  drain-lock 30.0 s, evidence deadline 120.0 s, heartbeat 20 s, evidence
  poll 2.0 s — all via `SLAIF_REVIEW_WORKER_*` with `extra=forbid`; compose
  sets no deadline override (defaults apply).
- Deterministic live outcome: because the freeze revokes the capability
  within ~1 s of run creation, the dispatcher's terminal finalization for
  that run fails the `slaif_agent_browser_authorized` gate (complete and
  release both raise `BROWSER_AUTHORITY_DENIED` /
  `BROWSER_LEASE_NOT_CURRENT`), the run stays RUNNING with an expired lease
  (never re-claimable: claim requires an ACTIVE workspace + unrevoked
  capability — by design), and the bounded cancel is the only exit. The E2E
  asserts both policy outcomes; the observed outcome is bounded cancel
  (documented, not a spec weakening).

### Criterion 6 (R8 evidence: all actually executed)

- Local full unit + repository suites: 786 passed (exact commands in Local
  verification).
- Local full integration suite: 244 items, 242 passed in 45:15 + 2 fixed ->
  re-run 7/7 passed (82.22 s).
- Fast-iteration compose stack `slaif007a082f` (same code byte): freeze E2E
  project final run **2/2 PASSED** (contracts
  `freeze-review-snapshot-freeze-to-review`,
  `freeze-review-snapshot-fail-closed-negatives`).
- Canonical full compose smoke at the final byte: `sh
  tools/compose/smoke.sh slaif007b082` — fully green, `SMOKE_EXIT=0`
  (16 projects; freeze-review-snapshot = 1 project, 2 contracts). Final
  lines:

  ```text
  compose-e2e: OK projects=16 setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2 agent-workspace-puck=2 freeze-review-snapshot=1 media-publication=1 artifacts=disabled
  compose-smoke: OK
  SMOKE_EXIT=0
  ```

- Canonical smoke run history (same command every time, disclosed): runs
  1-3 stopped in the pre-existing `database-login-policy` block because
  its hardcoded roster pins predated the order's 11th login (10 login
  roles / 23 secret files), run 3 additionally catching the
  privilege-matrix count pin that a first partial fix had missed; run 4
  (instrumented) passed the database/secret blocks and stopped in the
  browser-E2E stage with `compose-e2e: FAILED stage=browser
  reason=setup-governance-contract` — the documented Puck-drag flake
  class (081-a report); a standalone E2E re-execution during diagnosis
  passed setup+governance and tripped the same documented render-timing
  class on the pre-existing preview contract `renderer theme tokens
  preserve local precedence and semantic contrast` (`page.evaluate`
  `missing-theme-primary`) — non-deterministic timing, no product-
  behavior failure; run 5, after the complete pin fix (deviation
  above), is the fully green canonical run recorded above. Run 5 carried
  a temporary debug-echo instrumentation in the login block only
  (byte-identical check sequence, disclosed); after reverting to the
  committed clean byte, the complete login block (9 checks plus the
  unrelated-login create/connect/deny/drop) was re-executed green under
  `set -eu` on a fresh live stack, ending
  `database-login-policy: OK public-connect=denied exact-roles=11
  direct-default-owner-drift=none unrelated-connect=denied`. The new
  freeze project's contracts passed every run from the first green
  fast-iteration run (run 5, 2/2) onward.
- GitHub CI (exact 20-check roster of the base commit; details in the
  GitHub CI section):

  | head | CI result |
  | --- | --- |
  | I `88a9315` (superseded by F) | 12/20 SUCCESS; `Node contracts` FAILURE (in-scope lint defect, fixed by F); 7 CANCELLED by the F push |
  | F `286e8bb` (superseded by F2) | 19/20 SUCCESS; `Compose and edge packaging` FAILURE (in-scope spec read-skew, fixed by F2; not the documented browser-flake class — no re-run invoked) |
  | F2 `7863989` (implementation head) | 20/20 SUCCESS (CI run 37244718233 + CodeQL run 37244718232) |
  | D `987c0a2` (docs head) | 20/20 SUCCESS (CI run 37245765136 + CodeQL run 37245765203, both completed/success) |

### Criterion 7 (R7 byte-identity; no new public surface)

- No OpenAPI/generated-contract changes: generated footprint 0 (no route
  schema diff beyond the new control route registered in the existing
  policy; no browser/Agent surface change; no new scope, capability shape,
  or credential exposed to browser/Agent — the worker credential exists only
  server-side in the mounted secret volume).

### Criterion 8 (R9 hard constraints)

- Lockfiles byte-identical (no dependency or version change; `uv lock
  --check` and `pnpm install --frozen-lockfile` green at final byte).
- No raw-SQL/admin-tool bypass paths; no secrets in the repository or this
  report (fake placeholders only; capability/session values never logged).
- No data migration of existing rows (schema + functions only).
- No changes outside the increment's semantic family.

## Local verification

Exact commands and outcomes (repo root, uv 0.12.5, Node 24.14.1,
pnpm 11.22.0, TypeScript 6.0.3):

```text
uv lock --check                                  OK
uv sync --frozen --all-groups                    OK
uv run --frozen ruff check services/backend tests/repository tools   OK
uv run --frozen ruff format --check services/backend tests/repository tools  OK
uv run --frozen mypy                             OK (299 files)
uv run --frozen pytest services/backend/tests/unit tests/repository
                                                 786 passed
uv run --frozen pytest services/backend/tests/integration
                                                 242 passed, 2 failed (new-file
                                                 pins) in 2715.95s -> fixed in
                                                 test files -> re-run: 7 passed
                                                 (82.22s); full suite green
python -m compileall -q tools tests/repository   OK
python -m unittest discover -s tests/repository -p 'test_*.py'  OK
python tools/check_repository.py                 OK
python tools/check_mermaid.py                    OK
npx --yes markdownlint-cli2@0.23.2 "**/*.md"     OK (at final byte)
node --version                                   v24.14.1
pnpm --version                                   11.22.0
pnpm install --frozen-lockfile                   OK
pnpm lint                                        OK
pnpm format:check                                OK
pnpm typecheck                                   OK (incl. tests/e2e tsconfig)
pnpm test                                        OK (recursive build + 33 contracts)
pnpm build                                       OK
pnpm licenses list --json                        249 deps, all permissive groups
```

Node-gate history note (disclosed): the first local Node-gate pass was
on an intermediate spec byte; the final pre-commit spec byte (I head)
carried the dead `hex` helper that `pnpm lint` flags — reproduced
locally and surfaced by CI `Node contracts` at the I head. After the F
repair, `pnpm lint`, `pnpm format:check`, `pnpm typecheck`,
`pnpm test` (33/33), `pnpm build`, and `pnpm licenses list --json`
(249 deps, 8 permissive groups) were all re-run green at the F byte;
after the F2 repair the Node gate was re-run green at the F2 byte and
the freeze E2E project was re-verified on a fresh stack (smoke.sh
fixture SQL + setup project, both contracts PASSED).

Process smoke (all ten `--check` entrypoints): OK, health-only, no port
bound, no DB/job/bootstrap mutation (including the now-real review worker).

## GitHub CI / required checks

Exact 20-check roster of the base commit: 15 `CI`-workflow jobs plus the
`CodeQL` workflow's `CodeQL`, `Analyze (actions)`,
`Analyze (javascript-typescript)`, `Analyze (python)`, and `Detect
supported languages` checks.

- State observed for superseded implementation head I
  `88a9315959586c0939a5fa910b2c71457c13ab54` (run 37242440011, pushed
  2026-10-04T23:04:57Z): `Node contracts` FAILURE (job 111553669041) at
  `freeze-review-snapshot.spec.ts:81` — `@typescript-eslint/no-unused-
  vars`, the dead `hex` helper (in-scope defect, fixed by F); the 5
  `CodeQL`-workflow checks and `Dependency review`, `Markdown`,
  `Mermaid`, `Python 3.12 quality and package`, `Python 3.13 quality and
  package`, `Python 3.14 quality and package`, `Repository policy` all
  SUCCESS (12/20); the remaining 7 jobs (`Compose and edge packaging`,
  `Foundation PostgreSQL 14-18`, `Supply-chain evidence`) CANCELLED by
  GitHub supersession on the F push (no recorded results; not used as
  evidence).
- State observed for superseded implementation head F
  `286e8bb4d7f8e6fe404808322a7796cafa0474a7` (run 37242876093, fully
  terminal before the F2 push): 19/20 SUCCESS; `Compose and edge
  packaging` FAILURE (job 111554951149, failed 2026-10-04T23:19:21Z with
  `compose-e2e: FAILED stage=browser reason=freeze-review-snapshot-
  contract`: both new freeze contracts at
  `freeze-review-snapshot.spec.ts:247`, `expect(count).toBe(0)` received
  1 — the spec's read-skew race, an in-scope defect fixed by F2; not the
  documented browser-flake class, so no re-run was invoked).
- State observed for implementation head F2
  `7863989d544d474bd87fad1789fdb32f88cd8a26` (CI run 37244718233
  completed/success + CodeQL run 37244718232 completed/success): all 20
  checks SUCCESS — `Analyze (actions)`: SUCCESS, `Analyze
  (javascript-typescript)`: SUCCESS, `Analyze (python)`: SUCCESS,
  `CodeQL`: SUCCESS, `Compose and edge packaging`: SUCCESS, `Dependency
  review`: SUCCESS, `Detect supported languages`: SUCCESS, `Foundation
  PostgreSQL 14`: SUCCESS, `Foundation PostgreSQL 15`: SUCCESS,
  `Foundation PostgreSQL 16`: SUCCESS, `Foundation PostgreSQL 17`:
  SUCCESS, `Foundation PostgreSQL 18`: SUCCESS, `Markdown`: SUCCESS,
  `Mermaid`: SUCCESS, `Node contracts`: SUCCESS, `Python 3.12 quality and
  package`: SUCCESS, `Python 3.13 quality and package`: SUCCESS, `Python
  3.14 quality and package`: SUCCESS, `Repository policy`: SUCCESS,
  `Supply-chain evidence`: SUCCESS — no FAILURE/CANCELLED/PENDING
  remaining at the implementation head.
- State observed for docs head D `987c0a2cb0e94116173dba22741a7e9bca9eba8a`
  (CI run 37245765136 + CodeQL run 37245765203, both completed/success):
  20/20 SUCCESS — no FAILURE/CANCELLED/PENDING (docs-only diff over F2;
  no code change).
- All required green at drafting: yes (F2: 20/20 terminal SUCCESS, no
  FAILURE/CANCELLED/PENDING).
- Report-only commit (SELF) may trigger fresh checks at the report head;
  strategy independently waits/verifies SELF per the protocol.

## Local setup / dependencies

- Disposable local PostgreSQL (scratch) for integration; fake credentials
  only; cluster left clean (0 `slaif_test_%` databases, 0 `fixture_%`
  roles) after every run.
- Compose smoke stacks built from local OCI images (pinned base digests,
  exact artifact hashes); no hosted services; NGINX is the only host-port
  publisher.

## Documentation

- R6 four surfaces updated in-commit (D): README.md, oap/INCREMENTS.md,
  oap/MVP-PROGRESS.md, oap/MVP-CONTRACT-AUDIT.md. Implemented vs planned
  distinguished in each; no architecture/constitution/protocol edits
  (none required by this order).

## Safety and scope confirmations

- Scope: exactly the activated order; no second-objective PR; no next-order
  choice; no merge/auto-merge/close (PR #97 left OPEN for strategy).
- Secrets: none in the diff, report, or logs; fake placeholders only; no
  capability/session/token values printed (verification probes printed
  status codes and redacted identifiers only).
- Production: no production systems, data, or credentials touched; no
  Docker socket access; unrelated host files untouched.
- Pre-existing human changes preserved; no reset/overwrite/clean for
  convenience.
- No extra PRs; single PR #97; report published atomically by the SELF
  commit whose only change is the report file (parent = D = docs head,
  first parent chain I -> D -> SELF).
- Skips: none. Nothing required by R8 was skipped, pending, or left
  blocked; the two environmental notes below are disclosed, not skipped.

## Known limitations / blockers

1. **Browser preview-document navigation fails on live stacks (pre-existing
   072 surface; out of scope by order non-goal).** Verified root cause:
   `BROWSER_WORKER_PREVIEW_ORIGIN=http://web:3000`; the worker navigates to
   `/preview/<workspaceId>/`; Next.js (App Router) answers 308 ->
   `/preview/<workspaceId>` (trailing-slash normalization); the worker's
   request confinement authorizes exactly the first document hop
   (`redirectedFrom() === null`) and aborts every later document hop, so the
   redirected navigation is aborted -> `BROWSER_NAVIGATION_FAILED` (observed
   deterministically: non-frozen probe run claimed in ~300 ms, terminal
   FAILED in ~2 s, `audit.browser_event` ENQUEUED/LEASED/FAILED). No E2E
   before this order ever exercised a real browser run, so this was never
   observed previously. Candidate fixes for strategy (082/2 or 083):
   worker-side — allow the initial document's redirect chain, or request the
   canonical (trailing-slash-free) URL when `route == "/"`; web-side — serve
   the trailing-slash variant without redirecting.
2. **Post-freeze terminal finalization of the frozen run cannot land
   (pre-existing 035_001 gate interaction).** The dispatcher's
   `slaif_agent_browser_run_complete` and `..._release` both require
   `slaif_agent_browser_authorized` (unrevoked capability + ACTIVE
   workspace); the freeze revokes both within ~1 s, so the worker's terminal
   result for that run is dropped (agent-api logs: `browser dispatcher
   attempt unavailable` + `browser dispatcher lease release unavailable`),
   the run stays RUNNING until the bounded cancel. This is fail-safe (the
   run can never mutate or complete post-freeze) and makes the E2E policy
   outcome deterministically bounded-cancel, but it means the attach branch
   (evidence from a COMPLETED run) is only reachable when a run completes
   and finalizes before the freeze's revocation. Residual risk: the
   COMPLETED-attach evidence path is covered by the integration suite, not
   the live E2E.
3. **Timestamp semantics in the frozen job transaction.**
   `CURRENT_TIMESTAMP` is transaction-scoped; rows written late in the ~120 s
   drain transaction (cancel, snapshot, terminal) carry the transaction-start
   timestamp. Immutability and digest integrity are unaffected (digests are
   content-based; audit rows are complete); ordering-sensitive consumers
   should use the job's `claimed_at`/heartbeat fields, not row
   `completed_at`/`occurred_at`, for wall-clock timing.
4. **Local integration run 1's "462 items" is superseded**: run 1's log was
   truncated when an interrupted second run aborted the session; run 3 is
   authoritative (244 items = `pytest --collect-only` count of the current
   suite). Reported honestly per the order.

## Recommended strategic follow-up

- 082/2 (review surface): consume `review_snapshot` (immutable inspection,
  diff against canonical, accept/discard) — the snapshot shape and digest
  recomputation are production-ready as landed.
- 082/2 or 083 (browser pipeline): fix the preview-document navigation
  (root cause verified above) so the attach branch is reachable in live E2E;
  consider making post-revocation terminal finalization explicit (a
  dedicated "abandoned by freeze" terminal, or a capability-scoped complete
  path) so abandoned runs do not depend on the drain deadline for
  observability.
- 083 (operational): document the transaction-scoped timestamp semantics for
  audit consumers; optionally add a worker-side preview-navigation contract
  test that pins the redirect behavior.
