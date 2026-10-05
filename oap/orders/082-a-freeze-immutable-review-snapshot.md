# OAP Work Order — 082-a: real freeze producing the immutable review snapshot

> Strategic work order. Executor: coding agent. Reviewer/acceptor/merger:
> strategic model. This order is IMMUTABLE once activated; corrections,
> if ever needed, use the next letter (082-b) and a new order.

## 1. Identifier and mode

- Round ID: `082-a` (flat legacy format; the first semantic increment of
  numeric Objective 082 uses the legacy `NNN-L` namespace per
  `governance/2026-09-14-increment-qualified-round-ids.md`; a later second
  increment would use `082-2-a`).
- Objective: 082 (082/1 — real freeze producing the immutable review
  snapshot; durable review jobs + real review worker + shared-lock
  retrofit).
- PR mode: CREATE_NEW_PR.
- Branch: `oap/082-a-freeze-immutable-review-snapshot`, created from
  verified current `main` (see section 2; re-verify at publication).
- PR title: `OAP 082-a: real freeze producing the immutable review
  snapshot (082/1)`.
- Expected PR number: next available (GitHub assigns; create exactly one
  PR; do not create, amend, or touch any other PR; dependabot PRs
  #83/#90/#94 are out of scope and are never touched).
- Dependency position (human D5 resequencing, 2026-09-20): 079 (complete)
  -> 081 (merged) -> **082/1 (this)** -> 082/2 (read-only review surface)
  -> 083/1-3 (accept/discard/public surface) -> 084 (conflict-safe
  lifecycle) -> 080 (MCP parity). 082/1 depends on 081 (merged) only;
  080/084 are NOT prerequisites.

## 2. Verified current state (strategy-verified 2026-10-04 against live
GitHub and the local checkout at this exact head)

- Remote `main` = `c48849f149417fccf5cc0a152bc3ca39aaaf49ba` (081/1 merge
  commit of PR #96, merged 2026-10-04T14:52:08Z; parents
  `550c42c387bcddf12356ba2db299ef5bf99dd818` and
  `ec3410494b1cdb4368e803d484a43368110734ba`; 20/20 required checks
  successful at the exact SELF head `ec3410494b1cdb4368e803d484a43368110734ba`;
  post-merge checks at the merge commit verified green by strategy before
  this activation).
- 081/1 delivered: migration `069_001` (parallel assert + idempotency pair
  for human editing of the exact AGENT workspace via the optional
  `X-Editor-Workspace` header), Puck "Open in Puck" entry point + landing
  page + banner, R4 current-truth flips. `oap/active` = `081-a` (last
  activated round; protocol-correct idle state until this activation).
- No OAP product PR is currently open (dependabot #83/#90/#94 only; never
  touched by this order).
- Migration head: `069_001_human_agent_workspace_editor`. This order's new
  migration is `070_001`.
- Component catalog: 32/32; OpenAPI `contracts/openapi/agent-v1.json` has
  47 paths; strip-identity sha256
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
  (after stripping `x-slaif-*`) — both must remain byte-identical.
- Verified source facts at this head (082/1 premises, re-verified
  2026-10-04 against `c48849f`):
  - `control.slaif_workspace_freeze(uuid)` (migration `024_001`) is a
    STUB: plain `ACTIVE -> FREEZING -> REVIEW` SQL in one function call —
    no capability revocation, no drain, no durable job, no snapshot.
    `slaif_workspace_accept` / discard are state-flip stubs (083 scope).
    The stubs are NOT wired to any HTTP route (no freeze/accept/discard
    routes exist in `control_api/workspace_http.py`).
  - `review_worker/` and `scheduler/` are non-listening skeletons
    (`run_worker_process(ProcessKind.*)`, no job logic). `compose.yaml`
    already runs a `review-worker` service (smoke.sh service roster
    includes it) — the process becomes real; no new compose service is
    required (new env for the worker credential is allowed and must be
    disclosed).
  - `agent_state/promotion.py` is a detached `asyncpg_cow_reviewer`
    wrapper (`conflict_policy="error"`) with no site-revision lock, no
    promotion audit, no outbox, no media finalization — unchanged by this
    order (083/1 scope).
  - Shared advisory-lock contract: `agent_state/locks.py` defines
    `acquire_workspace_lifecycle_lock` =
    `pg_advisory_xact_lock_shared(hashtextextended($1, 280))` and
    `prelocked_cow_session` (session-level shared lock before the COW
    snapshot). Some mutation families already take the shared 280 lock
    (e.g. migrations 036/050/066/067 patterns); Agent REST data-plane
    Python layer (`agent_api/`) and `media_service/` do not take it in the
    Python layer today. The 028/069 human-editor asserts take the xact
    lock on key 280 under `p_lock`. The retrofit in R4 makes the shared
    280 lock BEFORE the in-transaction ACTIVE recheck the single
    uniform rule for every product mutation family.
  - `control.browser_run` (migration `035_001`, Objective 072) holds
    durable browser-run state; its state transitions and grants are
    unchanged by this order except the documented freeze-policy
    cancellation path in R5.
  - Permission registry (`014_001`): `workspace:freeze`,
    `workspace:accept`, `workspace:discard` keys already exist in the
    GOVERNANCE bundle. No new permission key is added by this order;
    verify and document which roles carry GOVERNANCE (or the needed key)
    and keep the established grant pattern.
  - 079/1 delivered `finalize_media_for_promotion(site_id, workspace_id,
    media_ids)` (idempotent, public namespace) — NOT used by this order
    (083/1 reuses it); only media REFERENCES are captured into the
    snapshot.
- E2E precedents: `tests/e2e/agent-workspace-puck.spec.ts` (081),
  `agent-sessions.spec.ts`, `governance.spec.ts`, `media-publication.
  spec.ts`; compose `e2e.sh` project roster (15 projects,
  `agent-workspace-puck=2`); `reporter.mjs` conventions.
- Flake policy: at most ONE documented unmodified CI re-run, and only for
  the documented flake class with its exact failure signature; any other
  recurrence is a real failure — fix in code or report BLOCKED.

## 3. Strategic context

- Architecture (ARCHITECTURE-for-agents.md §8, workspace lifecycle):
  promotion is atomic, conflict-safe, reviewer-only, and bound to an
  immutable human-reviewed snapshot. The REVIEW state is only reachable
  after a COMPLETE successful snapshot; the current 024_001 stub jumps
  straight to REVIEW, which is the defect this increment removes.
- Human decision D5 (2026-09-20) approved the split direction: 082 =
  082/1 (freeze -> immutable snapshot, one semantic family) + 082/2
  (read-only review surface). This order is 082/1 only.
- 082/1 is one semantic family (freeze/drain/snapshot lifecycle), so it
  stays one increment even though it is large; the predeclared budget
  (section 10) must be honest, and the 20-30 production/config file
  review trigger is monitored per the 2026-09-14 review-unit governance
  (section 11). If the trigger is crossed, CLOSURE_ONLY applies: no new
  semantic family enters this PR after that point.

## 4. Bounded scope

Exactly one semantic family — freeze/drain/snapshot lifecycle:

1. New migration `070_001`: durable review-job queue, immutable snapshot
   schema + grants, rebuilt freeze function, worker job/snapshot
   functions, narrow review-worker role/credential, bootstrap revision
   set update (R1).
2. The review worker becomes real: durable poll/claim/execute loop,
   narrow credential, exclusive product lock after shared-mutation drain,
   freeze policy for outstanding browser runs, snapshot materialization,
   REVIEW transition only after a complete verified snapshot, crash/
   retry-safe (R2, R5).
3. Human Control freeze endpoint: session auth, `workspace:freeze`
   permission, CSRF, exact site/workspace binding, idempotent,
   fail-closed (R3).
4. Shared-lock retrofit: every product mutation transaction family
   (Agent REST data plane, Editor HUMAN + Agent-workspace, Media,
   batch/collection) acquires the shared workspace lock (key 280) before
   its in-transaction ACTIVE recheck; one lock order; freeze takes the
   exclusive 280 lock (R4).
5. Current-truth documentation flips in durable wording (R6), contract
   byte-identity (R7), evidence (R8), hard constraints (R9).

## 5. Explicit non-goals

- No real accept, no real discard, no selective accept (083/1, 083/2).
- No review UI, no semantic diff, no review surface of any kind (082/2).
- No media finalization, no anonymous public media reads, no
  publication semantics (083/1, 083/3).
- No scheduler work, no media-GC work, no MCP changes.
- No catalog/component changes, no renderer changes, no Puck behavior
  changes, no browser tooling changes.
- No new public Agent routes, no new scopes, no new dependencies, no
  lockfile changes, no infrastructure changes beyond existing compose
  services.
- No changes to `contracts/openapi/agent-v1.json` or generated catalog /
  design-system artifacts (byte-identity required, R7).
- No dependabot PR activity of any kind.

## 6. Requirements

### R1 - Migration `070_001`: durable jobs, immutable snapshot, rebuilt
freeze (all in one transactional migration; downgrade drops exactly the
new objects)

- `control.review_job`: `id uuid pk`, `workspace_id uuid not null`,
  `site_id uuid not null`, `job_kind text check (job_kind in
  ('FREEZE','ACCEPT','DISCARD'))`, `status text check (status in
  ('QUEUED','CLAIMED','SUCCEEDED','FAILED'))`, `attempt_count integer
  not null default 0`, `max_attempts integer not null default 3`,
  `claimed_by text`, `claimed_at timestamptz`, `last_heartbeat
  timestamptz`, `payload jsonb`, `error text`, `created_at timestamptz
  not null default now()`, `updated_at timestamptz not null default
  now()`; partial unique index
  `unique (workspace_id, job_kind) where status in ('QUEUED','CLAIMED')`
  so at most one live job per workspace+kind; terminal rows retained
  (audit history, never deleted by this increment).
- `control.review_snapshot`: `id uuid pk`, `workspace_id uuid not
  null`, `site_id uuid not null`, `status text check (status =
  'COMPLETE')` (only complete snapshots are ever stored — a partial
  object can never exist in the table), `revision_watermark bigint not
  null`, `versions jsonb not null` (catalog-v1, design-system-v1,
  composition-schema, renderer version pin, Puck version pin,
  content-model version — the exact version surfaces the product pins),
  `normalized_state jsonb not null` (normalized editable state of the
  frozen workspace: pages, compositions, theme, navigation, global
  regions, media references — the same normalization the trusted
  renderer consumes), `validation_report jsonb not null`,
  `media_references jsonb not null` (immutable media digest objects
  referenced by the workspace; references only, no bytes),
  `browser_evidence jsonb not null` (completed run ids/artifact
  references only; may be `[]`), `payload jsonb not null` (canonical
  payload), `digest text not null` (sha256 over canonical serialization:
  `json.dumps(obj, sort_keys=True, separators=(",",":"))` applied to the
  canonical payload exactly as the OpenAPI strip-identity convention
  does; recomputable by any party holding the row), `created_by text not
  null` (worker identity), `created_at timestamptz not null default
  now()`.
- Grants: `slaif_owner` owns both tables. Create a narrow role
  `slaif_review_worker` (password managed by bootstrap, same pattern as
  existing service credentials) with ONLY: `USAGE` on `control`;
  `SELECT` on `control.workspace`, `control.site`, `control.capability`,
  `control.browser_run`; `SELECT, INSERT` on `control.review_job` and
  `UPDATE` on `control.review_job` (worker-owned lifecycle of its own
  job rows); `SELECT, INSERT` on `control.review_snapshot`. NO role
  other than `slaif_owner` may hold `UPDATE` or `DELETE` on
  `control.review_snapshot` (immutable; prove with
  `has_table_privilege` assertions in R8). The worker role must NOT
  receive access to any `content` canonical table in this increment.
- `CREATE OR REPLACE FUNCTION control.slaif_workspace_freeze(uuid)` —
  same name as the 024_001 stub, new semantics, executed in the caller's
  transaction: (a) single `UPDATE control.workspace SET status=
  'FREEZING' WHERE id=$1 AND status='ACTIVE'` (row-count checked;
  non-leaking `P0002` if not exactly one row); (b) revoke ALL
  non-revoked capabilities of the workspace (idempotent, same status
  pattern the capability table already uses); (c) enqueue the FREEZE job
  with `ON CONFLICT DO NOTHING` against the partial unique index and
  return the job id (new or pre-existing) so the operation is idempotent
  from the caller's perspective. The function must NEVER set
  `REVIEW` (that is the worker's job after a complete snapshot).
- Worker functions (EXECUTE granted to `slaif_review_worker` only):
  `control.slaif_review_job_claim(text p_claimant)` — atomic claim of the
  oldest `QUEUED` job (`FOR UPDATE SKIP LOCKED`), sets
  `CLAIMED/claimed_by/claimed_at/last_heartbeat` and increments
  `attempt_count`, returns the full job or no row;
  `control.slaif_review_job_heartbeat(uuid)`;
  `control.slaif_review_job_terminal(uuid, text p_status, text p_error)`
  — `SUCCEEDED` (error null) or `FAILED`; stale-claim recovery: a
  `CLAIMED` job whose `last_heartbeat` is older than the worker's
  configured staleness threshold (default 60s) is re-queueable while
  `attempt_count < max_attempts`; at `max_attempts` the job becomes
  `FAILED` with a distinct error.
  `control.slaif_review_snapshot_complete(uuid p_workspace_id, jsonb
  p_row)` — in the caller's (worker) transaction: validates the row
  shape, recomputes the digest from `payload` and rejects mismatch
  (non-leaking `P0002`), inserts the snapshot, and
  `UPDATE control.workspace SET status='REVIEW', review_snapshot_id=...
  WHERE id=$1 AND status='FREEZING'` — the REVIEW transition happens
  ONLY here, ONLY from FREEZING, ONLY in the same transaction as the
  snapshot insert. If the workspace row has moved on (e.g. discarded),
  fail non-leaking without inserting.
  (Add the `review_snapshot_id` column to `control.workspace` in the
  same migration if the column does not already exist; verify first and
  use the existing column if present.)
- `control.slaif_workspace_accept` / discard stubs are UNCHANGED (083).
- `bootstrap/service.py`: add `070_001` to the downgrade-compatible
  revision set (established pattern).

### R2 - The review worker becomes real (narrow credential, durable and
crash-safe)

- `review_worker` process: bounded poll loop (interval 1s, batch 1) over
  `slaif_review_job_claim`; NO `LISTEN/NOTIFY`; connect with the
  `slaif_review_worker` credential only (never owner/control credential);
  structured logging of job id/workspace/kind/attempt; clean shutdown on
  SIGTERM mid-no-job (in-flight job: let the transaction finish or
  roll back — a rolled-back claim is safe because claim + work execute
  transactionally per job).
- FREEZE job processing, in one database transaction per step group as
  needed, in this order:
  1. Re-read the workspace: must be `FREEZING` and its site `ACTIVE`;
     otherwise `FAILED` with error `STATE_DRIFT` (non-leaking).
  2. Acquire the EXCLUSIVE product lock
     `pg_advisory_xact_lock(hashtextextended(workspace_id::text, 280))`
     with a bounded `lock_timeout` (30s); on timeout retry within the
     job's attempt budget, then `FAILED` with error
     `DRAIN_TIMEOUT`.
  3. Re-check workspace still `FREEZING` inside the locked transaction.
  4. Freeze policy for outstanding durable browser runs (R5).
  5. Materialize the snapshot per R1 row contract: revision watermark
     from the workspace's current canonical/watermark state; normalized
     editable state via the product's existing normalization path (the
     same code the trusted renderer and Puck consume — no new divergent
     serializer); versions from the pinned artifacts; validation report
     by running the existing composition validation; media references
     (digest objects only); completed browser evidence only.
  6. `slaif_review_snapshot_complete` -> workspace `REVIEW` (atomic).
  7. Job `SUCCEEDED`.
- A job whose snapshot step raises (validation failure, serialization
  failure, DB error) -> transaction rolled back, job `FAILED` with a
  structured error, workspace remains `FREEZING` (NOT reviewable, NO
  snapshot row, NO REVIEW state). No retry of a semantically-failed
  snapshot (retry = new human freeze after fixing the cause); retry of
  transient claim/DB errors follows the attempt budget.
- `ProcessKind.REVIEW_WORKER` semantics preserved; `__main__` entry
  unchanged in shape; the process must be observable (health/log) like
  its sibling workers.

### R3 - Human Control freeze endpoint

- Route: `POST /api/control/v1/sites/{siteId}/workspaces/{workspaceId}/
  freeze/` (registered in `control_api` route policy exactly like the
  existing workspace routes).
- Authorization: human session auth (existing control auth), CSRF token
  required (existing CSRF mechanism), permission key
  `workspace:freeze` (already registered in `014_001` GOVERNANCE bundle;
  no new key), exact binding `workspace.site_id == path siteId`,
  workspace `actor_type` unrestricted (a human may freeze HUMAN or
  AGENT workspaces of their site — verify against the established
  control-plane membership rules and document the decision in the
  report).
- Behavior: `ACTIVE` -> execute `slaif_workspace_freeze` in one
  transaction -> `202` with `{job_id, status: "FREEZING"}`;
  `FREEZING` -> idempotent `202` with the existing live job id;
  `REVIEW`/`ACCEPTED`/`DISCARDED`/`CONFLICTED` -> `409` with a stable
  non-leaking error code; unknown ids -> `404` (existing pattern);
  malformed ids -> `400`; missing/invalid CSRF -> `403`; missing
  permission -> `403` (uniform with existing control failures, no
  oracle between "no permission" and "not found" beyond the
  established control-plane pattern).
- No new UI in this increment (the endpoint is API-level; the review
  surface is 082/2). E2E drives it via the authenticated control API.

### R4 - Shared-lock retrofit (one lock order, all mutation families)

- Rule: EVERY product mutation transaction family acquires
  `pg_advisory_xact_lock_shared(hashtextextended(workspace_id::text,
  280))` BEFORE its in-transaction ACTIVE recheck: Agent REST data-plane
  mutations (all 074/078-era mutation functions), Editor mutations
  (028/069 human-editor paths — verify the existing assert lock and
  document the before/after), Media mutations (068/079-1 upload and
  reference writes), batch/collection operations.
- Lock order is exactly: shared 280 first, then any finer-grained
  exclusive locks (key 994 family). No lock order may be inverted
  anywhere by this change. The freeze job is the only acquirer of the
  EXCLUSIVE 280 lock; because every mutation holds it only for a short
  transaction, drain terminates.
- Families already taking the shared lock (verified in R8's compliance
  table) are NOT reworked — verified and documented only.
- The retrofit must be serialization-only: no change to any function's
  predicate, idempotency, digest, or response behavior; all existing
  unit/integration/E2E suites must pass unmodified in their assertions
  (mechanical test-pin updates allowed only where a timestamp/counter
  pin legitimately moves, disclosed per the 078/7-a precedent class).

### R5 - Browser-run freeze policy (durable 072 runs)

- During step 4 of R2: for all outstanding (non-terminal)
  `control.browser_run` rows bound to the workspace/site: wait up to a
  bounded deadline (default 120s total) for them to reach a terminal
  state; on timeout, transition each still-outstanding run to the
  `CANCELLED` terminal state using ONLY state transitions that
  `035_001` already permits (if `CANCELLED` is not a valid target from a
  given run state, use the valid cancel-family transition and document
  it; never widen the state machine).
- Only `COMPLETED` runs may be attached to `browser_evidence`; cancelled
  runs are recorded in the validation report as `cancelled_by_freeze`
  but contribute no evidence. A run that completes before the deadline
  is attached normally.
- The policy constants (drain 30s, evidence deadline 120s, staleness
  60s) are named configuration with the stated defaults; changing them
  is a config matter, disclosed in the report.

### R6 - Current-truth documentation (durable wording)

- Update exactly the four current-state surfaces, in the standard
  durable form used since 078-z (identify increment/PR + source
  revision; state GitHub is authoritative for live acceptance/merge
  state; record immutable merge facts only when already known; `oap/
  active` = last activated round until next activation; NO wording that
  becomes false the instant this PR merges):
  1. `oap/INCREMENTS.md` header + add the 081/1 row (accepted and merged
     facts verified at activation: PR #96, merge commit
     `c48849f149417fccf5cc0a152bc3ca39aaaf49ba`, 2026-10-04) and the
     Next row (082/1 in flight at `082-a`).
  2. `oap/MVP-PROGRESS.md` sequence paragraph + the 081/1 row (merged
     facts) + the 082 row in the standard in-flight form.
  3. `README.md` delivery-sequence row (081/1 merged facts) and the
     planned-product-work section prepend (082/1).
  4. `oap/MVP-CONTRACT-AUDIT.md` authoritative-source revision ->
     `c48849f...` as of the 082 reconciliation; row 40 / promotion /
     lifecycle rows updated to the in-flight 082/1 form WITHOUT claiming
     this PR merged.
- An adversarial grep for stale live-state claims (pattern class:
  `081/1.*(open|pending|in flight)`, `this PR is still open`,
  `pending strategic merge` outside immutable transcripts) must return
  nothing in current-state documents.

### R7 - OpenAPI and generated contracts (byte-identity)

- `contracts/openapi/agent-v1.json` byte-identical to base (47 paths;
  strip-identity sha256
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
  unchanged) — the freeze endpoint is a human control route and adds no
  public Agent path.
- `packages/component-catalog/src/catalog-v1.json`,
  `packages/composition-schema/src/catalog-v1.json`,
  `packages/composition-schema/src/design-system-v1.json` byte-identical.
- Generator gates (`--check`) pass with zero diff. If regeneration
  surfaces ANY delta, stop: that is a scope violation — do not fix by
  absorbing product changes; report the exact delta and mark the
  affected criterion honestly.

### R8 - Evidence (all actually executed, honestly reported)

- Unit: job claim/heartbeat/terminal/stale-recovery predicate matrix
  (single claim under concurrency, attempt budget, non-leaking errors);
  snapshot digest recompute (positive + tampered payload rejected);
  freeze function state-gate matrix (ACTIVE ok, FREEZING idempotent,
  other states P0002); capability revocation matrix; R3 authorization /
  CSRF / malformed matrix (HTTP level).
- Integration (real PostgreSQL): concurrent claim (two worker
  connections, exactly one claimer); crash-safety (kill between claim
  and terminal -> stale recovery re-queues; at budget -> FAILED);
  freeze idempotency (double endpoint call -> one live job, one job
  row); REVIEW reachable ONLY via `slaif_review_snapshot_complete`
  (forced validation failure -> job FAILED, workspace FREEZING, zero
  snapshot rows); grant proof (`has_table_privilege` UPDATE/DELETE on
  `review_snapshot` false for every long-lived role, true for
  `slaif_owner`); lock retrofit proof (a mutation transaction started
  before the freeze drain blocks until the freeze transaction commits —
  observable serialization, no deadlock); regression: agent / editor /
  media mutation suites pass unmodified in assertions.
- E2E (real browser + real PostgreSQL, new Playwright project(s)
  registered in `playwright.config.ts` + `e2e.sh` roster +
  `test_compose_smoke_contract.py` pin, following the 081 pattern):
  authenticated human freezes a real AGENT workspace via the control
  API with a real (long-running) browser run outstanding; assert:
  freeze policy outcome (attach or bounded cancel), workspace reaches
  `REVIEW` only after the snapshot exists, `review_snapshot_id` set,
  snapshot row digest recomputed via psql matches, capabilities fully
  revoked (subsequent Agent REST write on the workspace -> uniform
  denial), mutation after FREEZING denied, snapshot immutability
  (UPDATE as runtime role fails), negative matrix (non-member, wrong
  site, CSRF-less, malformed ids, re-freeze of REVIEW state).
- Canonical psql baselines (counts/digests/privileges) exactly as 081.
- Local full unit + integration suites, full compose smoke at the final
  implementation commit, fresh-stack re-verification — all honestly
  reported with exact counts and any failures.

### R9 - Hard constraints

- Lockfiles byte-identical (no dependency or version change).
- No new public route, scope, credential exposed to the browser or the
  Agent surface; the worker credential exists only server-side.
- No raw-SQL or admin-tool bypass paths; no secrets in the repository.
- No data migration of existing rows (schema + functions only).
- No changes outside this increment's semantic family.

## 7. Acceptance criteria (observable)

- AC1: `070_001` applies and downgrades cleanly on a fresh stack;
  bootstrap asserts it.
- AC2: freeze endpoint matrix passes (R3) with exact status codes.
- AC3: an ACTIVE workspace frozen by a real human session reaches
  `REVIEW` with exactly one complete snapshot whose digest
  independently recomputes; capabilities are revoked; no REVIEW is
  observable at any point before the snapshot exists (E2E + psql).
- AC4: a forced snapshot validation failure leaves the workspace
  `FREEZING`, job `FAILED`, zero snapshot rows, no REVIEW (integration).
- AC5: concurrent claims yield exactly one claimer; stale claims are
  recovered and bounded (integration).
- AC6: the retrofit compliance table covers every mutation family;
  serialization proof passes; all pre-existing suites pass
  unmodified in assertions.
- AC7: snapshot immutability: UPDATE/DELETE on `review_snapshot` denied
  to every long-lived role (integration + psql).
- AC8: contracts byte-identical (R7 re-proven by strategy).
- AC9: docs (R6) verified against live GitHub at review; adversarial
  sweep clean.
- AC10: 20/20 (or the current full roster) required checks successful
  at the exact report head, first attempt or one documented flake-class
  re-run max.

## 8. Verification and workflow

- Work on `oap/082-a-freeze-immutable-review-snapshot` from the verified
  base; commit sequence: (T) order + `oap/active` exactly as activated;
  (I) implementation; (D) documentation; (S) report-only commit
  `SELF` (parent = implementation head). Push every commit; the PR head
  must be the `SELF` report commit.
- Run locally before push: `uv run --frozen python
  tools/check_repository.py`; unit + integration suites; full compose
  smoke + e2e at the final implementation commit; record exact counts.
- GitHub: exactly one PR, base `main`, title per section 1; CI must
  reach the full terminal roster; do not re-run unmodified heads except
  the single documented flake-class allowance.
- Report publication commit: `SELF`; strategy independently verifies
  head/parent/numstat/checks.

## 9. Report requirements

- Status (COMPLETE/PARTIAL/BLOCKED) with the finite criterion list per
  the 2026-09-14 review-unit governance; every R8 evidence item named
  with its actual executable result (counts, SHAs, durations, failures).
- Cumulative base->head grouped size table (production/config,
  migrations, tests/evidence, generated, docs, OAP transcript) and
  substantive implementation-line count; review-trigger status
  (fired / not fired) computed cumulatively.
- The R4 retrofit compliance table (family -> function/file -> lock
  before/after) and the R5 freeze-policy decision record.
- All deviations/adaptations with reasons (expected candidates: e2e
  roster pins, bootstrap revision set, smoke service roster, worker env
  in compose.yaml, test timestamp pins) — each one line, each justified.
- Honest CI history (every run, every failure, every re-run with the
  exact flake signature if the allowance is used).
- Residual risks and what 082/2 / 083 will need from this increment.

## 10. Predeclared review budget (2026-09-14 review-unit governance
in force)

- Production/config files: at most 18 (control freeze route + route
  policy; worker modules (loop, freeze policy, snapshot materialization);
  R4 retrofit touch points (Agent REST functions, media mutations,
  editor verification, batch); `privileges.py`; `bootstrap/service.py`;
  `compose.yaml` env; config).
- Migrations: exactly 1 (`070_001`).
- Test/evidence files: at most 12 (new unit matrix, integration spec,
  E2E spec, roster/pin updates).
- Generated-contract footprint: 0 (byte-identity, R7).
- Docs footprint: 4 surfaces (R6).
- OAP transcript footprint: this order + `active` + one report.
- Substantive implementation-line scale: at most 3500 lines.
- The ~20-30 production/config file threshold remains a REVIEW TRIGGER,
  not a quota: if the honest cumulative count crosses 20, the PR enters
  CLOSURE_ONLY per section 11 and the report must say so.

## 11. Review-unit governance (2026-09-14 amendment, in force)

- Cumulative review size is computed base -> current head at every
  review round, grouped as in section 10.
- CLOSURE_ONLY: no new semantic family, no adjacent feature, no
  opportunistic scope, no next-objective work; only finite defects/
  evidence required to make already-added behavior safe, correct and
  reviewable.
- If Strategy rejects a completion claim, Strategy publishes one finite
  checklist of unresolved criteria with the executable evidence each
  requires; a later COMPLETE claim must have actually executed every
  named criterion.
- Early split decision: if remaining work is semantically separable,
  split BEFORE adding it to this PR. 082/2 (review surface) and all 083
  work are separate increments from verified merged main regardless of
  how much room appears to remain.
