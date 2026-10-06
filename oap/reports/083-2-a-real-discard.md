# OAP Coding-Agent Report — 083-2-a

## Work order

- Order: `oap/orders/083-2-a-real-discard.md` (activated via
  `oap/active`, strategic FIFO `OK` received 2026-10-06).
- Round: `083-2-a` (increment-qualified form: 083/2 — real discard,
  the conflict remedy; second increment of the approved 083/1-083/3
  pre-split).
- Objective: 083 (real human accept/discard promotion lifecycle); this
  increment delivers the real human **discard** (idempotent enqueue +
  single reviewer-transaction discard + terminal `DISCARDED`) only.
- Mode: `NNN-a` — one fresh branch + one new PR from authoritative
  remote main.
- Branch: `oap/083-2-a-real-discard`.
- PR: #101 (URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/101`),
  state OPEN.
- Base: main @ `22f38c783d062a9c5352f7bdde8607d9ac299f26` (PR #99
  merged, 083/1).
- Starting remote main SHA (verified at branch creation):
  `22f38c783d062a9c5352f7bdde8607d9ac299f26`.
- Commits: transcript T `aa3f613547f4f6c5fc8972bcf586856907d660d7`
  (order + `oap/active` bytes, pushed at activation); implementation I
  `536f8d594a624b9ffa41eb60c71f3a7a07b3bbb6` (amended twice for the
  CI-found fixes, see below); docs D
  `2ffca481baaf34f7e4c0da1e8202eac07e37ac11`; E2E pin fix F
  `dce0caed112fb09d4f1e21faa944a8bd894893f1` (one file,
  `tests/e2e/discard-lifecycle.spec.ts`, +30/-3: two spec pins found by
  the local compose smoke re-run, see "GitHub CI / required checks");
  report S (SELF) `REPORTSHA` (report-only, first parent F).

## Status

COMPLETE (finite criterion list below; strategy independently reviews
and merges — COMPLETE never means accepted).

## Executive summary

083/2 makes the human discard real: a `REVIEW` or `CONFLICTED`
workspace (frozen, with an immutable COMPLETE snapshot) can be
discarded by the site's human reviewer. The control route
(`POST /api/control/v1/sites/{site_id}/workspaces/{workspace_id}/discard/`,
202) re-checks exact site binding plus the single
`workspace:discard` permission, then calls the idempotent
`control.slaif_workspace_discard(uuid, uuid)` enqueue (migration
`073_001`, replacing the inert 024_001 stub): one durable DISCARD job
with the exact payload `{site_id, origin_status, actor_user_account_id}`,
a live-job idempotency check that runs BEFORE the status gate (a
duplicate discard returns the same job id), the
`status IN ('REVIEW','CONFLICTED')` gate with stable
`WORKSPACE_NOT_DISCARDABLE` (P0002 -> 409 class), defensive idempotent
capability revocation, and the guarded `DISCARD_QUEUED` transition.
The review worker claims `["FREEZE","ACCEPT","DISCARD"]`;
`review_worker/discard_job.py` processes the job in one
`asyncpg_cow_reviewer` connection/transaction (exclusive product
advisory lock `hashtextextended(workspace_id, 280)`, `DISCARDING`
re-check under `FOR UPDATE`, the foundation `discard_session`, guarded
`DISCARDED` + `discarded_at`, job `SUCCEEDED`) — all-or-nothing, with
NO `dependencies(session_id)` closure check anywhere in the discard
path (the 083/1 foundation `get_cow_dependencies` composite-FK
limitation, ADJ-4, is therefore structurally out of the discard path;
the success fixture carries real page DML to prove it). Retryable
failures roll back and replay under the attempt budget (workspace
stays `DISCARDING`); at budget the workspace returns to its
`origin_status` (REVIEW or CONFLICTED) with
`REVIEW_JOB_STALE_AT_BUDGET` — no dead end. The admin review page
gains the discard control (REVIEW/CONFLICTED + COMPLETE snapshot; the
deliberate absence of a drift gate: discard is the drift remedy), the
corrected CONFLICTED terminal text, and terminal-state rendering;
`promotion.py::discard_workspace` is retired. E2E: new
`discard-lifecycle` Playwright project (roster 18 -> 19).
`agent_state.promotion` keeps `get_conflicts` for 084; 083/3 (outbox
consumer + public media finalization) is unchanged and remains
planned.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`.
- PR #101 `OAP 083-2-a: real discard (conflict remedy) (083/2)` OPEN,
  base `main`, head branch `oap/083-2-a-real-discard`.
- T (order transcript commit, pushed at activation):
  `aa3f613547f4f6c5fc8972bcf586856907d660d7` (exact order +
  `oap/active` bytes as published).
- I (implementation commit, literal): `536f8d594a624b9ffa41eb60c71f3a7a07b3bbb6`.
- D (docs commit, literal): `2ffca481baaf34f7e4c0da1e8202eac07e37ac11`.
- F (E2E pin-fix commit, literal):
  `dce0caed112fb09d4f1e21faa944a8bd894893f1` (one file:
  `tests/e2e/discard-lifecycle.spec.ts`, +30/-3).
- Implementation head SHA (literal 40-hex pre-report commit; first
  parent of the report commit):
  `dce0caed112fb09d4f1e21faa944a8bd894893f1` (the E2E pin-fix commit F).
- Report publication commit: SELF (report-only; its literal SHA is the
  remote PR head after publication, verified via `git ls-remote` and
  `gh pr view 101 --json headRefOid`), parent = F; the SELF commit
  changes only the new report file.
- Pushed commits: T (already pushed at activation), I, D, F, SELF.
- Head at report time: S `REPORTSHA`.
- Required 20-check roster state per run: see "GitHub CI / required
  checks" (20/20 terminal SUCCESS at the implementation head F, no
  FAILURE/CANCELLED/PENDING; the report-only S head may trigger
  fresh checks — strategy independently waits/verifies SELF per the
  protocol).

## Changes made

### 1. Migration `073_001_real_human_discard.py` (268/0, exactly 1)

- Upgrade:
  1. `control.slaif_workspace_discard(p_workspace_id uuid,
     p_actor_user_account_id uuid)` — `SECURITY DEFINER`
     (`SET search_path = pg_catalog`, owner `slaif_owner`), replacing
     the 024_001 stub: workspace row `FOR UPDATE`;
     `WORKSPACE_NOT_FOUND` (P0002); a live (QUEUED/CLAIMED) DISCARD
     job is returned unchanged BEFORE the status gate (duplicate
     discard -> same job id regardless of current status); status gate
     `status IN ('REVIEW','CONFLICTED')` with stable
     `WORKSPACE_NOT_DISCARDABLE`; defensive idempotent capability
     revocation (`revoked_at IS NULL` guard, the freeze pattern);
     enqueue through the 070_001 partial unique index
     (`ON CONFLICT (workspace_id, job_kind) WHERE status IN
     ('QUEUED','CLAIMED') DO NOTHING` + re-select guard, stable
     `DISCARD_ENQUEUE_CONFLICT`); guarded `DISCARD_QUEUED`
     transition. The 024_001 stub's `FREEZING` allowance is
     deliberately NOT carried over (FREEZING is transient and races
     the freeze worker).
  2. `control.slaif_human_agent_workspace_discard(p_workspace_id uuid,
     p_site_id uuid, p_user_id uuid)` — the human Control entry
     point: exact site binding, platform administrator OR
     effective-membership `workspace:discard` re-check, then the
     enqueue (no snapshot input). Unknown workspace, wrong binding,
     and missing authority all yield no row (uniform 404 class, no
     oracle); the enqueue's stable `WORKSPACE_NOT_DISCARDABLE`
     propagates (409 class at the route).
  3. Zero new worker grants: the migration contains NO GRANT/REVOKE
     touching `slaif_review_worker` or the `agentcow` surface. The
     function revoke loops cover every non-owner privilege role
     except the durable review worker (order R1 verbatim); the
     worker's implicit PUBLIC access to the new functions is removed
     by the `REVOKE ... FROM PUBLIC` statements, and the reconcile
     (`apply_product_privileges`) re-applies the exact registry,
     which grants these functions to `slaif_control` only.
- Downgrade: drops exactly the two functions and restores the
  BYTE-EXACT 024_001 stub `slaif_workspace_discard(uuid)` (same
  body text) plus its `GRANT EXECUTE ... TO slaif_control` pin.
  The restored stub is additionally revoked from PUBLIC and every
  long-lived role before the single grant: a bare downgrade must not
  leave the stub with the implicit PUBLIC execute that PostgreSQL
  grants to every new function (verified: without the revoke,
  `proacl` materializes `=X` on first grant and every role's
  `has_function_privilege` reports True; with it, exactly
  `slaif_owner` + `slaif_control` hold EXECUTE). This mirrors the
  072_001 claim-function downgrade pattern.
- `bootstrap/service.py`: one line — `"073_001"` added to the
  `_assert_downgrade_compatible` revision set (mechanical head pin).

### 2. Control discard route (R2)

- `control_api/route_policy.py`: one new policy line —
  `POST /api/control/v1/sites/{site_id}/workspaces/{workspace_id}/discard/`
  (mutation class, CSRF, site-scoped, SITE_PERMISSION kind, single
  permission `workspace:discard`). Route-policy total 196 -> 197
  (pin updated in `test_route_policy.py`).
- `control_api/workspace_http.py`: strict body model
  `DiscardWorkspaceRequest` (`frozen=True, extra="forbid"`;
  `acknowledge_discard` must be the boolean `true` — JSON `1`,
  `false`, and missing are rejected by the before-validator ->
  422 class) + one handler `discard_workspace`:
  `authorize_site_request(..., "workspace:discard", state_changing=True)`
  -> platform-administrator OR effective `workspace:discard` else
  uniform `ResourceNotFoundError`; `recent_auth` absent ->
  `AuthenticationError` (401 class); `WORKSPACE_NOT_DISCARDABLE` ->
  `ResourceConflictError` (409 class); any other surprise ->
  `ServiceUnavailableError` (fail closed); no row -> uniform 404.
  Response `202 {job_id, status}`.
- `control_api/database.py`: one method
  `human_agent_workspace_discard` (one SELECT of the function
  through the established `_human_agent_call` gate).
- `db/privileges.py`: the `CONTROL_FUNCTIONS` registry gains the two
  discard functions (exact signatures) so every HARDENED reconcile
  re-applies `EXECUTE ... TO slaif_control` for them — without the
  registry entries, `apply_product_privileges` (which revokes EXECUTE
  from all control-schema functions on every reconcile) strips the
  migration's one-time grant and the route fails after the first
  reconcile (proven by integration). This is the same registry the
  072_001 accept functions use; the discard functions are granted to
  `slaif_control` only (no other role, no worker).

### 3. Worker DISCARD job (R3)

- `review_worker/discard_job.py` (new, 238/0): the full sequence
  from the executive summary. Failure classes: invalid payload
  shape -> terminal `DISCARD_PAYLOAD_INVALID` (structural, not
  retryable); unexpected workspace status -> terminal
  `STATE_DRIFT` (no mutation); transient DB failure before/inside
  the reviewer transaction -> `ROLLED_BACK` (job stays CLAIMED,
  stale-claim recovery re-queues, workspace stays `DISCARDING`)
  until the attempt budget, then the workspace returns to
  `origin_status` + `REVIEW_JOB_STALE_AT_BUDGET`.
- `review_worker/worker.py`: the claim now calls
  `slaif_review_job_claim($1, $2)` with
  `["FREEZE", "ACCEPT", "DISCARD"]`.
- `review_worker/freeze_job.py`: `run_job` dispatches
  `job_kind == "DISCARD"` to `run_discard_job` (lazy import, the
  accept pattern); the docstring pin updates.

### 4. `discard_workspace` retirement (R3)

- `agent_state/promotion.py`: `discard_workspace` deleted (the
  DISCARD job is the only discard path); module docstring updated;
  `get_conflicts` remains for the 084 conflict-resolution
  increment. Unit test pins the import surface and the inventory.

### 5. Admin review page discard action (R4)

- `apps/web/src/admin/discard-action.tsx` (new, 219/0): the discard
  control — present ONLY when the read model reports status REVIEW
  or CONFLICTED with a bound COMPLETE snapshot (no drift gate by
  design: discard is the drift remedy; the server-side R2 checks
  remain the authority). Confirmation dialog (the app's
  `CspModal` pattern) requires the acknowledgement checkbox before
  the `Discard` button enables; after the 202 the existing
  workspace read route is polled (2s x 90) and the transient
  (`DISCARD_QUEUED`/`DISCARDING`) and terminal (`DISCARDED`) states
  render with stable human-facing text; the CONFLICTED state
  additionally renders the conflict banner. Rejection renders a
  retry message; the workspace is left unchanged.
- `apps/web/src/admin/workspace-review.tsx`: one `DiscardAction`
  render slot below the accept action.
- `apps/web/src/admin/accept-action.tsx`: the CONFLICTED terminal
  text corrected (R4.3) — it no longer promises a non-existent
  re-review; it states freeze is ACTIVE-only and names the real
  remedies (discard, or a fresh workspace).
- `apps/web/src/admin/api.ts`: one client method
  `discardWorkspace` (+ `DiscardWorkspaceResult` type).

### 6. E2E wiring (R7.3)

- `playwright.config.ts`: new project `discard-lifecycle`
  (`dependencies: ["governance"]`, Desktop Chrome,
  testMatch `/discard-lifecycle\.spec\.ts/`) — roster 18 -> 19.
- `tests/e2e/discard-lifecycle.spec.ts` (new, 600/0; 573/0 at D,
  +30/-3 in F for the two pin fixes below): dedicated
  run-unique site (`discardproof-<8hex>`), L2_SITE_EDITOR workspace
  - capability, content (media + components) AND real page DML
  (`PATCH /api/agent/v1/pages/{id}` title change — the ADJ-4 case,
  safe here because discard never calls `dependencies()`).
  Positive: freeze -> REVIEW -> discard with typed confirmation ->
  terminal text; durable psql pins (workspace `DISCARDED` +
  `discarded_at`, job `SUCCEEDED`, COW change tables 0|0, capability
  revoked, audit/outbox 0|0, canonical revision unchanged, pending
  page DML absent from canonical, media asset row `private|t` +
  zero public media rows for the dedicated site (hermetic
  content-addressing-agnostic pins), public render bytes
  byte-identical before/after modulo the per-request edge CSP nonce
  (NGINX `$request_id`; normalized in both the `nonce="..."`
  attribute form and the escaped RSC flight-payload form — see the
  Compose-smoke Run 1 root cause; every other byte is still pinned
  exactly); duplicate discard -> 409 pinned once; terminal state
  renders the status panel, not the control (the read model is
  re-fetched first: control presence is a function of the read model
  per the established 083/1 accept pattern, and the per-state
  control counts are pinned in the review-surface contract).
  Negatives: control absent while ACTIVE;
  ACTIVE discard -> 409; `acknowledge_discard` false/missing ->
  422; agent capability bearer on the control discard route
  (cookie-free `request` fixture) -> 401 uniform denial.
- `tools/compose/e2e.sh`: the `discard-lifecycle` stage after
  `accept-lifecycle`; final echo `projects=19 ... discard-lifecycle=1`.
- `tests/e2e/accept-lifecycle.spec.ts`: the 083/1 zero-control pin
  (REVIEW + COMPLETE: zero buttons matching `/discard|publish/i`)
  updated to exactly one — the 083/2 discard control now renders in
  that state (no publish shortcut exists, unchanged); this pin
  predates 083/2 and was found stale by the CI compose stage on the
  first D-head run.
- `tests/e2e/review-surface.spec.ts`: the 083/1 "NO discard" action
  pin corrected (REVIEW + COMPLETE now renders accept 1 +
  "Discard pending work" 1, publish 0); new per-state DOM pins at
  the end of the main test (psql-forced states: CONFLICTED ->
  discard 1 / accept 0 + the corrected conflict text rendered by
  both the accept terminal panel and the discard banner; ACTIVE /
  ACCEPTED / DISCARDED -> no controls, with the accept/discard
  terminal texts pinned); `tests/packaging/test_compose_smoke_contract.py`
  roster pins updated (governance-deps 13 -> 14; project name list).

### 7. Tests / evidence

- `services/backend/tests/integration/test_real_human_discard.py`
  (new, 1877/0, 11 tests, disposable per-test PostgreSQL through the
  established fixture; each test upgrades + reconciles to head
  `073_001`):
  1. `test_discard_migration_round_trip` — head pins (both functions
     `SECURITY DEFINER`, `search_path=pg_catalog`, owner
     `slaif_owner`); single-step downgrade to `072_001`; the 2-arg
     enqueue gone; exactly the 1-arg stub with prosrc
     BYTE-IDENTICAL to the 024_001 source (sliced verbatim from
     `024_001_workspace_lifecycle.py`); the stub's EXECUTE held by
     `slaif_control` only; re-upgrade to head.
  2. `test_worker_grant_surface_unchanged` — reviewer membership
     (worker + owner edges); the 13 `agentcow` foundation functions
     EXECUTE-holders `{slaif_owner, slaif_reviewer,
     slaif_review_worker}`; the exact control-table grant matrix for
     the worker (workspace/site S+U, capability/browser_run S,
     review_job S+I+U, review_snapshot S+I, cache_outbox S+I, outbox
     seq USAGE, promotion INSERT; promotion SELECT held by
     `slaif_reviewer`, NOT the NOINHERIT worker — the 083/1 pin);
     the discard functions EXECUTE for `slaif_control` only; grep
     pin on the 073_001 source (docstrings/comments stripped): no
     `slaif_review_worker`, no `agentcow`.
  3. `test_discard_enqueue_matrix` — exact payload for REVIEW and
     CONFLICTED origins; idempotency BEFORE the gate (live job
     returned unchanged while QUEUED and CLAIMED); capability
     revoked exactly once (revoked_at equal after the second
     enqueue); the full non-discardable set (FREEZING,
     ACCEPT_QUEUED, PROMOTING, ACTIVE, ACCEPTED, DISCARDED) ->
     `WORKSPACE_NOT_DISCARDABLE` (P0002); `WORKSPACE_NOT_FOUND`.
  4. `test_control_discard_route_authority_matrix` — 202 +
     `DISCARD_QUEUED`; duplicate same job id; platform admin;
     deny_discard / outsider / wrong binding -> uniform 404 with
     byte-equal envelopes (no oracle); stale recent_auth -> 401
     class (+ refresh restores); strict body (false / JSON 1 /
     missing / extra) -> 422; agent capability bearer -> 401; no
     cookie -> 401; terminal `DISCARDED` -> 409 (pinned once);
     FREEZING -> 409.
  5. `test_discard_worker_success_path` — media bytes + 3 COW ops
     (component update, component create, REAL page DML
     `slaif_agent_page_update` "Discarded Home" — the ADJ-4 case);
     real freeze; canonical state byte-identical before/after
     (revision, page/page-composition/locale/media base row sets,
     outbox 0, promotion audit 0); `DiscardResult` logged
     (discarded tables/operations, `no_op=False` on a live session);
     `SUCCEEDED`; `get_session_operations` empty through the
     foundation public API (adapter for the Executor protocol); COW
     change tables 0/0; `DISCARDED` + `discarded_at`; capability
     revoked; private staging bytes present, NO `public/` directory.
  6. `test_discard_worker_conflicted_origin` — the real 083/1
     conflict fixture (freeze -> concurrent canonical
     `page_composition_base` edit -> `run_accept_job` -> FAILED
     `BASE_ROW_CHANGED` -> CONFLICTED, the COW operations survive)
     -> discard with `origin_status` CONFLICTED -> DISCARDED; the
     fixture session is composition-only because the accept job's
     dependency closure walk cannot complete on a page-DML session
     (ADJ-4) and the fixture needs the clean conflict failure.
  7. `test_discard_worker_crash_replay_converges` — fixture:
     `DISCARDING` + a direct foundation `discard_session` (first
     pass: `no_op=False`, 3 operations) -> crash before the terminal
     write -> heartbeat aged past staleness -> re-claim attempt 2
     -> `SUCCEEDED`. Pins the OBSERVED foundation behavior: a
     replayed `discard_session` on the already-discarded session is
     a clean no-op (`no_op=True`, `discarded_tables == ()`,
     `discarded_operations == ()`, `has_pending_operations=False`) —
     which is what makes the replay safe.
  8. `test_discard_worker_retryable_and_budget` — the transient
     failure is a real infrastructure denial: the worker's EXECUTE
     on `agentcow.discard_cow(text,text,uuid,uuid[])` revoked
     (`REVOKE ... FROM`) / restored (`GRANT ... TO`); 3 attempts
     (max pinned 3): attempts 1-2 -> `ROLLED_BACK` (job CLAIMED,
     workspace stays `DISCARDING`), attempt 3 -> FAILED
     `REVIEW_JOB_STALE_AT_BUDGET` + workspace back to origin — from
     BOTH origins (REVIEW and CONFLICTED).
  9. `test_kind_aware_claim_discard_fifo` — FREEZE/ACCEPT/DISCARD
     enqueued in order; claim `["FREEZE","ACCEPT","DISCARD"]` ->
     FIFO x3 then empty; an invalid kinds array ->
     `REVIEW_CLAIM_KIND_INVALID` (072_001 behavior unchanged).
  10. `test_discard_path_has_no_dependencies_call` — grep pin on
     `discard_job.py` (docstrings/comments stripped): no
     `dependencies(`, has `discard_session(`; positive control:
     `accept_job.py` HAS `dependencies(`; the freeze-job dispatch
     import pin.
  11. `test_discard_workspace_retired` — `promotion.py` import
     surface + test inventory pin the removal.
- Mechanical head pins (072_001 -> 073_001), class "mechanical":
  `test_agent_mutations.py` (11 sites), `test_agent_page_style.py`
  (3), `test_control_database_integration.py` (both sites at the
  073_001 head; the deliberate matching-revision
  FOUNDATION_MISMATCH fixture preserved as matching),
  `test_database_bootstrap.py` (6 incl. `revision=073_001` CLI
  strings), `test_editable_domain_proof.py`,
  `test_human_agent_session_control.py`,
  `test_review_surface_read_model.py` (docstring),
  `test_workspace_integration.py`, `test_full_stack_integration.py`,
  `test_real_human_accept.py` (2 comments), unit:
  `test_foundation_contract.py` (file list +
  `migration_heads()==("073_001",)` + history tuple),
  `test_route_policy.py` (196->197, 34->35),
  `test_control_database.py` (fake readiness rows follow the
  dynamic head + `human_agent_workspace_discard` method-surface
  pin), `test_health_apps.py` (control app route inventory),
  `test_review_worker.py` (dispatch renamed to kind-aware; DISCARD
  dispatches via `run_discard_job`; OTHER ->
  `JOB_KIND_UNSUPPORTED`), `test_promotion.py` (retirement pin).

### 8. Documentation (R5, 4 surfaces, commit D)

- `README.md`: new `Objective-083/1 real human accept (merged)` row
  (PR #99 at `22f38c78...` on 2026-10-05); the planned row now
  names 083/2 in flight at `083-2-a` (branch + base) with the
  outbox consumer remaining planned.
- `oap/INCREMENTS.md`: header flipped (083/1 merged 2026-10-05;
  083/2 in flight with branch/base); new ledger row `083/1 ... PR
  #99 at 22f38c78... on 2026-10-05; 083/1 is closed`; Next row
  updated (083/1 closed; the superseded inert pre-plan deletion
  fact retained in that row).
- `oap/MVP-PROGRESS.md`: current-truth paragraph + 083 row flipped
  (PARTIAL — 083/1 merged; 083/2 in flight at `083-2-a`; 083/3
  planned).
- `oap/MVP-CONTRACT-AUDIT.md`: authoritative-source line ->
  `22f38c78...` on 2026-10-05 (the 083/1 merge), re-verified at the
  083/2 current-truth reconciliation (2026-10-06); the 083/1
  revision retained historical; the accept/discard evidence cell
  flipped to the 083/1 merged facts (one reviewer transaction,
  audit, one outbox event, CONFLICTED terminal, sole reviewer
  authority, E2E-proven) with 083/2 in flight.
- Adversarial grep (no "in flight at \`083-a\`"; no "this PR is
  open"/"pending strategic merge" phrasing; "in flight at
  \`083-2-a\`" present exactly where the durable form requires):
  returned nothing stale in the four surfaces.

## Files changed

Base->head (worktree measured at commit D; see budget table):

| File | +/- | Class |
| --- | --- | --- |
| `oap/orders/083-2-a-real-discard.md` (new) | 655/0 | transcript T |
| `oap/active` | 1/1 | transcript T |
| `services/backend/src/slaif_agent_site/db/alembic/versions/073_001_real_human_discard.py` (new) | 268/0 | migration |
| `services/backend/src/slaif_agent_site/review_worker/discard_job.py` (new) | 238/0 | worker |
| `services/backend/src/slaif_agent_site/review_worker/worker.py` | 1/1 | worker |
| `services/backend/src/slaif_agent_site/review_worker/freeze_job.py` | 5/1 | worker dispatch |
| `services/backend/src/slaif_agent_site/control_api/workspace_http.py` | 51/0 | route |
| `services/backend/src/slaif_agent_site/control_api/database.py` | 9/0 | route |
| `services/backend/src/slaif_agent_site/control_api/route_policy.py` | 14/0 | route |
| `services/backend/src/slaif_agent_site/db/privileges.py` | 8/0 | registry |
| `services/backend/src/slaif_agent_site/bootstrap/service.py` | 1/0 | head pin |
| `services/backend/src/slaif_agent_site/agent_state/promotion.py` | 5/18 | retirement |
| `apps/web/src/admin/discard-action.tsx` (new) | 219/0 | web |
| `apps/web/src/admin/workspace-review.tsx` | 10/6 | web |
| `apps/web/src/admin/accept-action.tsx` | 1/1 | web (text fix) |
| `apps/web/src/admin/api.ts` | 18/0 | web client |
| `playwright.config.ts` | 6/0 | e2e wiring |
| `tools/compose/e2e.sh` | 9/1 | e2e wiring |
| `tests/e2e/discard-lifecycle.spec.ts` (new) | 600/0 | e2e |
| `tests/e2e/accept-lifecycle.spec.ts` | 4/1 | e2e pin (083/1 suite) |
| `tests/e2e/review-surface.spec.ts` | 69/4 | e2e pins |
| `services/backend/tests/integration/test_real_human_discard.py` (new) | 1877/0 | integration |
| integration pin files (10) | 38/31 | mechanical pins |
| unit pin files (6) | 48/17 | mechanical pins |
| `tests/packaging/test_compose_smoke_contract.py` | 2/1 | roster pin |
| `README.md` | 2/1 | docs |
| `oap/INCREMENTS.md` | 7/4 | docs |
| `oap/MVP-CONTRACT-AUDIT.md` | 2/2 | docs |
| `oap/MVP-PROGRESS.md` | 2/2 | docs |
| `oap/reports/083-2-a-real-discard.md` (new) | SELF | report S |

## Pre-declared budget check (order Section 10 vs measured)

| Group | Predeclared | Measured (base->head) | Verdict |
| --- | --- | --- | --- |
| Production/config files | at most 15 | 16 (14 itemized-slot files + 2 non-itemized: `bootstrap/service.py`, `db/privileges.py`) | +1 over the line, each itemized below; CLOSURE_ONLY trigger (20) not crossed |
| Migrations | exactly 1 | 1 (`073_001`) | exact |
| Test/evidence files | at most 16 | 21 (new discard integration suite + new E2E spec + review-surface E2E pins + accept-lifecycle E2E pin + 10 mechanical-pin integration files + 6 unit pin files + 1 packaging roster pin) | +5 (mechanical pin class, itemized in "Files changed") |
| Generated-contract footprint | 0 | 0 | exact (R6) |
| Docs footprint | 4 surfaces | 4 | exact |
| OAP transcript | order + active + one report | 3 | exact |
| Substantive implementation lines | at most 2800 | 863 (all prod/config + migration added lines; pure Python/TypeScript code only: 854 after excluding 9 shell/compose lines in `tools/compose/e2e.sh`) | well under (31%) |

- Itemized production/config slots used (14 of 14): migration
  `073_001`, `review_worker/discard_job.py` (new),
  `review_worker/worker.py`, `review_worker/freeze_job.py`
  (dispatch), `control_api/workspace_http.py`,
  `control_api/database.py`, `control_api/route_policy.py`,
  `agent_state/promotion.py` (retirement),
  `apps/web/src/admin/discard-action.tsx` (new),
  `apps/web/src/admin/workspace-review.tsx`,
  `apps/web/src/admin/accept-action.tsx` (text fix),
  `apps/web/src/admin/api.ts`, `playwright.config.ts`,
  `tools/compose/e2e.sh`. The order's "+1 small helper" slot is NOT
  used (no `smoke.sh` baseline echo change was needed: the E2E
  roster echo line lives in `e2e.sh`, which is already itemized).
- The 2 non-itemized files, itemized:
  `bootstrap/service.py` (1 line: the `_assert_downgrade_compatible`
  revision set gains `"073_001"` — the mechanical head pin, same
  class as the 083/1 non-itemized wiring file);
  `db/privileges.py` (8 lines: the two discard functions in the
  `CONTROL_FUNCTIONS` registry — REQUIRED for R2 durability:
  `apply_product_privileges` revokes EXECUTE on all control-schema
  functions at every HARDENED reconcile and re-applies exactly the
  registry, so the migration's one-time grant would be stripped
  after the first reconcile without the entries; proven by the
  integration grant-surface test).
- The ~20 production/config file REVIEW TRIGGER: NOT FIRED
  (16 < 20).
- CLOSURE_ONLY: never entered (no trigger crossed; no scope added
  after any hypothetical trigger point).
- Variance classing: the +1 file variance is the
  reconcile-registry requirement above plus the one-line
  bootstrap head pin; the +5 test/evidence variance is the
  mechanical pin class (the established head-pin files, the
  unit route-inventory/dispatch/retirement pins, and the
  accept-lifecycle DOM pin stale since 083/2 added the control);
  no code was moved
  between directories to game the budget, no meaningful tests were
  excluded, and generated/OAP files were counted.

## Deviations and adaptations (order Section 9; one line each)

1. `db/privileges.py` `CONTROL_FUNCTIONS` registry entries (8 lines,
   non-itemized file): required so every HARDENED reconcile
   re-applies the discard functions' `slaif_control`-only EXECUTE
   (the migration's grant alone is stripped by the reconcile's
   `REVOKE EXECUTE ON ALL FUNCTIONS` sweep); same registry class as
   the 072_001 accept entries; proven by the integration
   grant-surface test.
2. 073_001 downgrade adds PUBLIC/role REVOKEs around the restored
   024_001 stub's single grant: a bare downgrade must not leave the
   stub with PostgreSQL's implicit PUBLIC execute (verified
   `proacl` materializes `=X` without the revoke; with it, exactly
   owner+control hold EXECUTE); mirrors the 072_001 claim-function
   downgrade pattern; the stub BODY remains byte-identical to
   024_001 (the byte-exact requirement is on the function body).
3. Conflict-origin integration fixture is composition-only (no page
   DML): the accept job's `dependencies()` closure walk cannot
   complete on a page-DML session (the 083/1 ADJ-4 limitation) and
   the fixture needs the clean `BASE_ROW_CHANGED` conflict failure;
   the page-DML ADJ-4 proof lives in the worker success-path
   fixture (discard never calls `dependencies()`).
4. `test_worker_grant_surface_unchanged` pins the worker's
   `audit.promotion` SELECT as FALSE (reviewer-only, NOINHERIT
   worker) per the 083/1 established pin, with the positive
   `slaif_reviewer` pin added.

## Acceptance-criteria evidence

### Criterion 1 (073_001 round trip; exact grant pins)

`test_discard_migration_round_trip` PASSED: upgrade head
`073_001`; both functions `prosecdef=True`,
`proconfig` includes `search_path=pg_catalog`, owner `slaif_owner`;
single-step downgrade to `072_001` restores exactly one
`slaif_workspace_discard` with `pronargs=1`; its `prosrc` equals the
024_001 source sliced verbatim (byte-identical — the test compares
the DB-stored body against `_stub_024_001_body()`, which slices
`024_001_workspace_lifecycle.py` at the `AS $fn$` markers); EXECUTE
on the stub: `slaif_control` True, all other long-lived roles False;
re-upgrade to head clean.

### Criterion 2 (grant surface unchanged by query)

`test_worker_grant_surface_unchanged` PASSED: reviewer membership
exactly `{slaif_review_worker, slaif_owner}` edges; the 13
`agentcow` functions' EXECUTE holders exactly `{slaif_owner,
slaif_reviewer, slaif_review_worker}`; the worker control-table
grant matrix matches the 083/1 pins (incl. outbox seq USAGE and
`audit.promotion` INSERT); discard functions: EXECUTE for
`slaif_control` only, all other long-lived roles False; grep pin:
the 073_001 source (docstrings/comments stripped) contains no
`slaif_review_worker` and no `agentcow`.

### Criterion 3 (enqueue: exact payload, non-discardable set
idempotency before the gate, revoke pinned)

`test_discard_enqueue_matrix` PASSED: REVIEW and CONFLICTED origins
enqueue with payload exactly
`{"site_id": <site>, "origin_status": <origin>, "actor_user_account_id": <actor>}`;
a live job (QUEUED and CLAIMED) is returned unchanged before the
status gate; the capability row's `revoked_at` is equal after the
second enqueue (exactly one revoke); all six non-discardable states
raise `WORKSPACE_NOT_DISCARDABLE` (P0002); unknown workspace raises
`WORKSPACE_NOT_FOUND`.

### Criterion 4 (route authority matrix)

`test_control_discard_route_authority_matrix` PASSED: 202 +
`DISCARD_QUEUED` for an authorized `workspace:discard` holder and
for a platform administrator; duplicate discard returns the same
job id; deny_discard / nonmember / wrong-site binding all yield
404 with byte-equal error envelopes (no oracle); stale
`recent_auth` -> 401 class (refresh restores 202);
`acknowledge_discard` false / JSON 1 / missing / extra field ->
422 (strict body); agent capability bearer -> 401; no session
cookie -> 401; terminal `DISCARDED` -> 409 (pinned once); FREEZING
-> 409.

### Criterion 5 (worker success end to end)

`test_discard_worker_success_path` PASSED (real PostgreSQL 16 +
foundation): COW session with media + 2 composition ops + REAL
page DML (`slaif_agent_page_update` title change, the ADJ-4 case);
the single reviewer transaction (`asyncpg_cow_reviewer`, advisory
lock `hashtextextended(workspace_id, 280)`, `DISCARDING` re-check
under `FOR UPDATE`, `discard_session`, guarded `DISCARDED` +
`discarded_at`, job `SUCCEEDED`) leaves: `get_session_operations`
empty (foundation public API via the Executor adapter); COW change
tables `page_composition_changes`/`page_changes` 0/0; canonical
state byte-identical (site revision, page/page-composition/locale
base row sets, media base rows); outbox 0; promotion audit 0;
capability revoked; private staging bytes present and NO `public/`
directory created. The advisory lock id in use: key 280
(`pg_advisory_xact_lock(hashtextextended($workspace_id, 280))`).
`DiscardResult` on the live session: `no_op=False` with the 3
pending operations discarded (logged by the job).

### Criterion 6 (CONFLICTED discard — the conflict remedy)

`test_discard_worker_conflicted_origin` PASSED: the 083/1 conflict
fixture (concurrent canonical edit of the session's
`page_composition_base` row -> `run_accept_job` FAILED
`BASE_ROW_CHANGED`, COW operations surviving, workspace terminal
CONFLICTED for accept) is discarded with
`origin_status=CONFLICTED` -> `DISCARDED`; the pending work is gone.

### Criterion 7 (crash-replay convergence; observed foundation
behavior)

`test_discard_worker_crash_replay_converges` PASSED: fixture
`DISCARDING` + direct foundation `discard_session` (first pass
`no_op=False`, 3 operations) -> crash before the terminal write ->
heartbeat aged (61s > 60s staleness) -> re-claim attempt 2 ->
`SUCCEEDED` exactly once. OBSERVED foundation behavior pinned:
the replayed `discard_session` returns `no_op=True`,
`discarded_tables == ()`, `discarded_operations == ()`,
`has_pending_operations=False` — replay-safe by construction.

### Criterion 8 (retry/budget from both origins; no dead end)

`test_discard_worker_retryable_and_budget` PASSED: with the
worker's EXECUTE on `agentcow.discard_cow(text,text,uuid,uuid[])`
revoked (a real infrastructure denial), attempts 1-2 stay
`ROLLED_BACK` (job CLAIMED, workspace `DISCARDING`); attempt 3 (max
pinned 3) -> job FAILED `REVIEW_JOB_STALE_AT_BUDGET` and the
workspace returns to its `origin_status` — proven from BOTH
REVIEW and CONFLICTED origins; after the grant is restored the
same fixture discards to `DISCARDED`.

### Criterion 9 (R4: discard control per state, DOM; confirmation
CONFLICTED text; terminal rendering; accept unchanged)

- Integration/UI: `discard-action.tsx` renders the control only for
  REVIEW/CONFLICTED + COMPLETE; the dialog's `Discard` button is
  disabled until the acknowledgement checkbox is checked
  (Playwright pins: `toBeDisabled()` -> check -> `toBeEnabled()`).
- E2E `review-surface` per-state DOM pins (3 viewports: the main
  test runs the 1280/820/375 sweep on the render mode; the action
  pins run on the default 1280x720 admin viewport): REVIEW+COMPLETE
  -> accept 1 + "Discard pending work" 1 (publish 0); CONFLICTED ->
  discard 1 / accept 0 + the corrected conflict text rendered by
  BOTH the accept terminal panel and the discard banner (count 2);
  ACTIVE / ACCEPTED / DISCARDED -> no controls (accept/discard
  terminal texts pinned).
- E2E `discard-lifecycle` positive: confirmation dialog ack-gate
  pinned; 202; terminal "Discarded — ..." text visible; duplicate
  -> 409; terminal state renders the panel, not the control.
  Negatives: control absent while ACTIVE; 409/422/401 classes
  pinned; observe() console/network clean.
- Accept control unchanged: `canAccept` (REVIEW + COMPLETE + no
  drift) behavior is 083/1's; the only accept change is the
  CONFLICTED terminal text (R4.3).

### Criterion 10 (R5 durable form; F2 flip; adversarial grep)

The four surfaces (README.md, oap/INCREMENTS.md,
oap/MVP-PROGRESS.md, oap/MVP-CONTRACT-AUDIT.md) carry the 083/1
merged facts (PR #99 at `22f38c78...` on 2026-10-05) and the 083/2
in-flight facts (branch `oap/083-2-a-real-discard`, base
`22f38c78...`); the F2 flip (the audit accept/discard evidence cell
pre-stale after 083/1) is present; the adversarial grep (no
`in flight at \`083-a\``; no "this PR is open" / "pending
strategic merge"; the current in-flight marker exactly where the
durable form requires) returned nothing stale.

### Criterion 11 (R6 byte-identity)

- `git diff 22f38c783d062a9c5352f7bdde8607d9ac299f26 -- contracts/
  packages/`: EMPTY (measured on the final tree).
- `uv run --frozen python -m tools.contracts.generate_agent_openapi
  --check`: PASSED (zero-diff, `contracts/openapi/agent-v1.json`
  unchanged).
- `python tools/generate_component_catalog.py --check`: PASSED
  (zero-diff).
- `python tools/generate_design_system.py --check`: PASSED
  (zero-diff).
- The agent OpenAPI 47-path strip-identity
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
  is re-proven by strategy at both base and head (strategy
  recomputes both sides; the contract bytes are unchanged, so the
  identity is the 083/1-proven value at both).

### Criterion 12 (budgets honest; trigger; CLOSURE_ONLY; full CI)

Budget table above (honest, itemized). REVIEW TRIGGER: NOT FIRED
(16 < 20). CLOSURE_ONLY: never entered. Full CI roster (19
projects) terminal and green at the exact report head: see "GitHub
CI / required checks".

## Local verification

Exact commands and outcomes (repo root, final tree; uv 0.12.5,
Node v24.14.1, pnpm 11.22.0, TypeScript 6.0.3):

```text
uv lock --check: PASSED (Resolved 45 packages in 1ms)
uv sync --frozen --all-groups: PASSED (Checked 44 packages)
uv run --frozen ruff check services/backend tests/repository tools: PASSED (All checks passed!)
uv run --frozen ruff format --check services/backend tests/repository tools: PASSED (328 files already formatted)
uv run --frozen mypy: PASSED (Success: no issues found in 307 source files)
uv run --frozen pytest services/backend/tests/unit tests/repository -q: PASSED (788 passed, 26 subtests passed in 34.57s)
uv run --frozen pytest services/backend/tests/integration -q: see the run history below (final clean run on the final backend tree: 270 passed in 2977.64s, 0 failed, 0 error; the only tree changes after that run are the E2E-spec edits, which the integration suite does not execute)
uv run --frozen pytest tests/packaging -q: PASSED (49 passed, 38 subtests passed in 2.20s)
uv build --out-dir /tmp/slaif-agent-site-dist-final: PASSED (sdist + wheel)
node --version / pnpm --version / uv --version: v24.14.1 / 11.22.0 / 0.12.5
pnpm install --frozen-lockfile: PASSED (Already up to date)
pnpm lint: PASSED (root eslint --max-warnings 0 + @slaif-agent-site/web filter)
pnpm format:check: PASSED (all matched files use Prettier code style)
pnpm typecheck: PASSED (scope-catalog + apps/web + services/browser-worker)
pnpm test: PASSED (browser-worker vitest RUN v4.1.10: 3 test files, 33 tests passed)
pnpm build: PASSED (Next.js: all route inventory incl. /review/[workspaceId] + proxy middleware; (Dynamic) server-rendered on demand)
pnpm licenses list --json: PASSED (root 8 licenses — 0BSD, Apache-2.0, BSD-2-Clause, BSD-3-Clause, BlueOak-1.0.0, CC-BY-4.0, ISC, MIT — over 249 packages; no AGPL/SSPL/BUSL/BSL/Commons Clause/noncommercial)
python -m slaif_agent_site.{control_api,editor_api,agent_api,render_api,mcp_adapter,media_service,review_worker,scheduler,media_gc,bootstrap} --check: PASSED (10/10 OK, via uv run --frozen python)
python -m compileall -q tools tests/repository: PASSED
python -m unittest discover -s tests/repository -p 'test_*.py': PASSED (Ran 71 tests ... OK)
python tools/check_repository.py: PASSED (PASS repository policy)
python tools/check_mermaid.py: PASSED (16 diagram(s) in 3 file(s); 529 Markdown file(s) scanned; CLI 11.16.0)
npx --yes markdownlint-cli2@0.23.2 "**/*.md": PASSED (0 issues in 523 files)
uv run --frozen python -m tools.contracts.generate_agent_openapi --check: PASSED (agent-openapi: OK zero-diff)
uv run --frozen python tools/generate_component_catalog.py --check: PASSED (catalog-v1 Python/TypeScript semantic equality OK)
uv run --frozen python tools/generate_design_system.py --check: PASSED (design-system: OK)
git diff <base> -- contracts/ packages/: PASSED (empty — R6 zero-diff)
```

Local full-run history (honest):

- Run 1 (2026-10-06 02:42-03:33, final tree except the one pin fix
  found by this run): `uv run --frozen pytest
  services/backend/tests/integration -q` -> 269 passed, 1 failed, 1
  error in 2987.51s (0:49:47).
  - FAILED `test_control_database_integration.py::
    test_control_pool_reports_exact_marker_migration_and_foundation_state`
    (`assert 'migration_mismatch' == 'foundation_mismatch'`): the
    deliberate matching-revision FOUNDATION_MISMATCH fixture still
    pinned `migration_revision = '072_001'` (a stale head pin missed by
    the mechanical-pin pass; readiness now reports the head as
    073_001, so the fixture reads as a migration mismatch). Fixed with
    the one-line pin update `072_001` -> `073_001` (same mechanical
    class; counted in the 38/31 integration-pin variance) and verified
    in isolation immediately after the fix (1 passed).
  - ERROR (teardown only; the test body passed) `
    test_database_bootstrap.py::test_empty_safe_transitions_to_first_
    and_repeated_hardened_table`: `DependentObjectsStillExistError`
    dropping a shared cluster-wide product role during fixture
    teardown — a concurrency artifact: this run overlapped a
    single-test verification probe (the per-test fixture drops
    cluster-wide roles and is not parallel-safe); no product test
    behavior involved.
  - All 11 `test_real_human_discard.py` tests PASSED within this run
    (collection indices 220-230; no anomalies after index 135).
- Run 2 (clean, sequential, no concurrent work, 2026-10-06
  03:35-04:25): `uv run --frozen pytest
  services/backend/tests/integration -q` -> 270 passed in 2977.64s
  (0:49:37), 0 failed, 0 error — including all 11
  `test_real_human_discard.py` tests and the two Run 1 anomaly tests
  (`test_control_pool_reports_exact_marker_migration_and_foundation_state`
  with the fixed pin; `test_empty_safe_transitions_to_first_and_
  repeated_hardened_table` with no teardown error). This run's tree
  is the final backend tree (the only later changes are the
  E2E-spec edits found by CI, which the integration suite does not
  execute).
- Run 3 (focused, exact final tree): `uv run --frozen pytest
  services/backend/tests/integration/test_real_human_discard.py -q`
  -> 11 passed in 111.15s (0:01:51), 0 failed, 0 error.

## Compose smoke

Disposable compose project `slaif007discard083` (public NGINX edge,
`compose.yaml`), exact command `sh tools/compose/smoke.sh
slaif007discard083` (repo root; log `/tmp/compose-smoke-0832a*.log`).

Run history (honest):

- Run 1 (2026-10-06 04:27-04:34 CEST, tree D `2ffca48`): FAILED at the
  browser stage — `browser-e2e: FAILED
  project=discard-lifecycle contract=positive ... line=503
  column=46` (`expect(await publicAfterResponse.text()).toBe(
  publicBefore)`). Root cause (reproduced locally with full diff):
  NOT a product defect — the edge sets a per-request CSP nonce from
  NGINX's `$request_id` (`infra/nginx/nginx.conf`:
  `script-src 'self' 'nonce-$request_id'`) and forwards the policy
  upstream; the Next.js 16.3.8 app embeds that nonce in the rendered
  HTML in two forms (the script/link `nonce="..."` attribute form and
  the escaped RSC flight-payload form `\"nonce\":\"...\"`), so
  ANY two requests for the same canonical page differ in exactly the
  nonce bytes. Verified: two back-to-back public fetches are
  byte-identical after normalizing both nonce forms (build id,
  RSC payload, and all content bytes equal). The second latent pin in
  the same contract (the terminal-state control-absence check asserted
  in-session without a read-model re-fetch) was also fixed: control
  presence is a function of the read model per the established 083/1
  accept pattern (the in-session dialog lifetime ends with the
  document re-fetch; per-state control counts are pinned in the
  review-surface contract), so the check re-fetches the review page
  first (fresh DISCARDED render: control count 0 + terminal text,
  verified against a real discarded workspace over HTTP before the
  spec edit). Fix = commit F (spec only, +30/-3); no product change.
  The smoke script's cleanup trap tore the stack down on exit.
- Run 2 (2026-10-06 04:44-05:09 CEST, final tree F
  `dce0cae`): `compose-smoke: OK`, exit 0. Full 19-project E2E roster
  terminal and green: setup=1 governance=1 preview=1
  preview-filtering=1 stable-devices=6 agent-sessions=2
  agent-workspace-puck=2 freeze-review-snapshot=1 review-surface=1
  accept-lifecycle=1 discard-lifecycle=1 media-publication=1
  (`compose-e2e: OK projects=19 ... artifacts=disabled`);
  35 `browser-e2e: PASSED` contracts, 0 FAILED — including
  `discard-lifecycle` positive (content+media+page-DML workspace
  freezes, discards end to end, canonical untouched) and negative
  (validation, terminal, and agent-capability denials; control absent
  off-state), and `accept-lifecycle` (unchanged, re-verified against
  the 083/2 control presence). Post-E2E stages green:
  `public-agent-restart-audit: OK ... rows=3`;
  `media-e2e: OK edge=nginx upload=validated-private-read=byte-
  identical finalization=public-read=byte-identical immutable-cache=
  verified`; governance archive/restart stage OK; broken-bootstrap
  negative correctly blocked; packaging suite `Ran 49 tests ... OK`.

## GitHub CI / required checks

Exact 20-check roster: the 15 `CI`-workflow jobs plus the `CodeQL`
workflow's `CodeQL`, `Analyze (actions)`,
`Analyze (javascript-typescript)`, `Analyze (python)`, and `Detect
supported languages` checks. (Branch pushes do not trigger the `CI`
workflow — its `push` trigger is `main` only; every branch-state
below is a `pull_request` run on the objective PR.)

CI history (honest — every run, every failure, every re-run):

- Run at transcript head T
  `aa3f613547f4f6c5fc8972bcf586856907d660d7` (CI run 37400109957,
  2026-10-06T01:37:32Z -> 01:53:22Z + CodeQL run 37400109982
  completed/success, 01:37:32Z -> 01:39:29Z): first attempt 19/20
  SUCCESS — `Python 3.12 quality and package` FAILED: its `Run unit
  and metadata qualification` step received `The runner has
  received a shutdown signal` (GitHub hosted-runner infrastructure
  shutdown; the unit suite was at 75% with every test passing at the
  interruption point). ONE documented unmodified job re-run (the
  single flake-class allowance; no push change) PASSED. T-head
  final: 20/20 SUCCESS, no FAILURE/CANCELLED/PENDING.
- Run at docs head D, first attempt
  `de38262a51a565c6c8128c7bc789d8d9e795cf7b` (CI run 37401529895,
  2026-10-06T01:54:34Z -> 02:09:09Z + CodeQL run 37401529932
  completed/success, 01:54:34Z -> 01:56:38Z): 15/20 SUCCESS; the 5
  failed CI jobs exposed latent defects fixed before the report
  (commits I/D amended for this — first amendment
  `63f34f6`/`1c8447b`, second/final
  `536f8d5`/`2ffca48`):
  - `Python 3.12/3.13/3.14 quality and package` FAILED at `Lint and
    check formatting`: `ruff format --check` flagged 3 call sites in
    `review_worker/discard_job.py` (1 file would be reformatted,
    exit 1).
  - `Node contracts` FAILED at `Lint TypeScript workspace`: eslint
    `@typescript-eslint/no-unnecessary-type-assertion` at
    `tests/e2e/discard-lifecycle.spec.ts:197` (`row_version!`
    redundant after the null-throw guard).
  - `Compose and edge packaging` FAILED at the browser stage:
    `browser-e2e: FAILED project=accept-lifecycle contract=positive:
    content+media workspace freezes, accepts end to end, publishes
    once ... detail=Error: Expected: 0 | Received: 1` — the 083/1
    zero-control pin (`/discard|publish/i` button count 0 at REVIEW
    - COMPLETE) stale because 083/2 renders the discard control in
    that state. Every E2E project before it (including the updated
    review-surface pins) PASSED; the `discard-lifecycle` stage runs
    after `accept-lifecycle` and had not yet executed.
  - Fix (amended commit I): `ruff format` on `discard_job.py`;
    redundant assertion removed; accept-lifecycle pin 0 -> 1 with
    comment. All verified locally before the force-push (`ruff
    check` + `ruff format --check` clean; `pnpm lint`,
    `pnpm format:check`, `pnpm typecheck`, `tsc -p tests/e2e`
    clean).
- Run at docs head D, first amendment
  `1c8447b653e1ebea6516e36717e8a51b4fbd685f` (CI run 37403350581,
  2026-10-06T02:16:47Z -> 02:26:45Z + CodeQL run 37403350652
  completed/success, 02:16:47Z -> 02:18:43Z): all 3 previously failed
  job classes PASSED (`Python 3.12/3.13/3.14 quality and package`,
  `Node contracts`, plus Markdown/Mermaid/Dependency review/Repository
  policy); `Compose and edge packaging` FAILED at the browser stage:
  `browser-e2e: FAILED project=discard-lifecycle contract=positive:
  content+media+page-DML workspace freezes, discards end to end,
  canonical untouched ... line=495` — the spec's `public media fetch
  -> 404` pin: the public media route resolves a digest GLOBALLY
  (`content.media_asset WHERE content_hash = p_hash AND
  public_status = 'public'`), and the `accept-lifecycle` project (run
  earlier on the same stack) had already published a byte-identical
  1x1 PNG, so the hash resolves publicly by design. The
  discard-lifecycle NEGATIVE contract PASSED, and every E2E project
  before it (including the fixed accept-lifecycle) PASSED. The run
  was CANCELLED by the second amendment push (cancel-in-progress)
  while PG 14-18 + Supply-chain were still running. Fix (second
  amendment of commit I): the 404 pin replaced by hermetic
  asset-row/site-level pins (the asset row `private|t` plus zero
  public media rows for the dedicated site) — no content-addressed
  HTTP negative on a shared stack.
- Run at docs head D, final
  `2ffca481baaf34f7e4c0da1e8202eac07e37ac11` (CI run 37404134442,
  started 2026-10-06T02:26:27Z, conclusion failure + CodeQL run
  37404134411 started 2026-10-06T02:26:27Z, conclusion success): 14/15
  CI jobs SUCCESS — `Compose and edge packaging` FAILED at the browser
  stage (`browser-e2e: FAILED project=discard-lifecycle
  contract=positive ... line=503 column=46`, 02:34:32Z) — the exact
  per-request CSP-nonce spec pin later root-caused and fixed in commit
  F (see "Compose smoke", Run 1); the discard-lifecycle NEGATIVE
  contract and every E2E project before it PASSED in that job. CodeQL
  roster at the same head: 5/5 checks success (`CodeQL`,
  `Analyze (actions)`, `Analyze (javascript-typescript)`,
  `Analyze (python)`, `Detect supported languages`). Net: 19/20
  terminal SUCCESS, 1 FAILURE (spec pin only; no product behavior
  involved).
- Run at E2E pin-fix head F
  `dce0caed112fb09d4f1e21faa944a8bd894893f1` (CI run 37406852047,
  2026-10-06T02:59:52Z -> 03:14:28Z (last job), conclusion success +
  CodeQL run 37406852031, 2026-10-06T02:59:52Z -> 03:01:53Z,
  conclusion success): 15/15 CI jobs SUCCESS — `Compose and edge
  packaging` (the job that failed at the D head), `Dependency
  review`, `Foundation PostgreSQL 14`, `Foundation PostgreSQL 15`,
  `Foundation PostgreSQL 16`, `Foundation PostgreSQL 17`,
  `Foundation PostgreSQL 18`, `Markdown`, `Mermaid`, `Node
  contracts`, `Python 3.12 quality and package`, `Python 3.13
  quality and package`, `Python 3.14 quality and package`,
  `Repository policy`, `Supply-chain evidence` — all success; CodeQL
  roster 5/5 success (`CodeQL` run + `Analyze (actions)`,
  `Analyze (javascript-typescript)`, `Analyze (python)`, `Detect
  supported languages`). Net: 20/20 terminal SUCCESS at the
  implementation head, no FAILURE/CANCELLED/PENDING.
- All required green at drafting: yes (F head `dce0cae`: 20/20
  terminal SUCCESS, no FAILURE/CANCELLED/PENDING — CI run 37406852047
  - CodeQL run 37406852031, both above).
- Report-only commit (SELF) may trigger fresh checks at the report
  head; strategy independently waits/verifies SELF per the protocol.
- Report publication: the report-only commit S is the remote PR head;
  its run state is recorded above. Strategy independently verifies
  the remote head and the required-check roster.

## Local setup / dependencies

- Disposable VM (passwordless sudo) per the constitution; system
  PostgreSQL 16 (16.15) for the integration suites (disposable
  per-test databases, fake `fixture-*` credentials only); no
  production systems, data, or credentials touched.
- Python: uv 0.12.5 frozen (`uv.lock` byte-unchanged, R8); Node
  24.14.1 / pnpm 11.22.0 frozen (`pnpm-lock.yaml` byte-unchanged,
  R8).
- Docker for the Compose smoke (public NGINX edge, disposable
  project); Playwright browsers (Chromium desktop) for E2E.

## Documentation

The four R5 surfaces updated in commit D (itemized under "Changes
made" 8). No architecture/constitution/protocol edits (none
required by this order). Implemented vs planned distinguished in
all four surfaces (083/2 in flight at `083-2-a`; 083/3 planned;
084 re-review/conflict-resolution out of scope).

## Safety and scope confirmations

- No secrets in code/docs/tests: all test credentials are
  generated `fixture-*` values or fake placeholders; no
  capabilities, cookies, DB URLs, or private artifact URLs appear
  in the diff.
- No production access: integration runs on disposable local
  PostgreSQL; the Compose smoke on a disposable project; no
  production systems/data/credentials/Docker-socket access.
- R8 hard constraints (byte-identity and no-touch):
  - Lockfiles / CI workflows / supply-chain files: `uv.lock`,
    `pnpm-lock.yaml`, `.github/workflows/*`,
    `tools/supply_chain/*` byte-unchanged (verified by
    base->head diff: none of them appear).
  - Agent surface: `contracts/openapi/agent-v1.json`, the
    component catalog, and the design system zero-diff (R6); the
    Agent route policy is untouched (the discard route is on the
    CONTROL plane only; agent capability bearer on the control
    discard route -> uniform 401, pinned in integration and E2E).
  - No re-review (CONFLICTED->REVIEW) surface, no selective accept,
    no read-model change (071_001 byte-unchanged), no
    freeze/snapshot change, no media finalization, no outbox
    events/consumer (the outbox CHECK allows `WORKSPACE_ACCEPTED`
    only), no GC changes, no renderer/Puck behavior change, no new
    compose mounts/env (the review-worker mounts/env are
    unchanged; the E2E roster echo line is the only compose-tooling
    change).
- Scope: the diff touches only the itemized budget files; the
  strategic order file and `oap/active` are committed exactly as
  activated (transcript T) and never edited afterwards.

## Known limitations / blockers

1. Pre-existing (072_001, out of this increment's scope): the
   072_001 downgrade restores the 024_001 ACCEPT stub with the same
   implicit-PUBLIC-execute gap that this increment's 073_001
   downgrade closes for the discard stub (verified: a bare
   downgrade to 072_001 leaves the accept stub with implicit
   PUBLIC execute until the next reconcile; the product downgrade
   flow marks the DB not-ready, so it cannot serve traffic, and a
   subsequent upgrade+reconcile restores the exact registry).
   Reported here for strategy; fixing it amends 072_001, which
   083/2 must not touch.
2. ADJ-4 (carried from 083/1, foundation limitation):
   `get_cow_dependencies` mishandles composite foreign keys; the
   ACCEPT path stalls/fails on page-DML sessions. Discard is
   structurally immune (no `dependencies()` call — grep-pinned);
   accept remains limited until the foundation is fixed.
3. Discarded workspaces' private staging media bytes become
   GC-reclaimable orphans handled by the existing media GC (no new
   cleanup in this increment, per the order's non-goals).

## Recommended strategic follow-up

- 083/3 (outbox consumer + public media finalization consumer)
  proceeds on top of this increment; the `WORKSPACE_ACCEPTED`
  outbox event shape is unchanged by discard (discard emits no
  outbox events).
- The 072_001 downgrade PUBLIC-execute gap (known limitation 1)
  is a candidate for a follow-up hardening increment.
- 084 (conflict-safe lifecycle: re-review / conflict resolution)
  can build on the CONFLICTED terminal state and the
  `get_conflicts` surface retained in `agent_state/promotion`.

Report publication commit: SELF
