# OAP Work Order — 083-2-a: real discard (conflict remedy) (083/2)

## 1. Identifier and mode

- Round ID: `083-2-a` (the SECOND semantic increment of numeric Objective 083
  uses the increment-qualified `NNN-I-L` form per
  `oap/governance/2026-09-14-increment-qualified-round-ids.md`; the first
  increment used the legacy flat `083-a`; a third increment would use
  `083-3-a`).
- Objective: 083 (083/2 — real discard: atomically discarding the pending
  workspace work; the MVP conflict remedy).
- Mode: CREATE_NEW_PR — one fresh PR from verified main; one bounded semantic
  family (the real discard path). Strategy anticipates a single round; if a
  completion claim is rejected, the SAME PR continues at `083-2-b` with a new
  order.
- Branch: `oap/083-2-a-real-discard`, created from verified remote main
  `22f38c783d062a9c5352f7bdde8607d9ac299f26`.
- PR title: `OAP 083-2-a: real discard (conflict remedy) (083/2)`.
- PR number: whatever GitHub assigns at creation (expected #101; report the
  actual number; never assume it in documentation — reference the increment,
  branch, and SHAs, and the PR number as GitHub reports it).
- The dependabot PRs #83/#94/#100 are out of scope and are never touched.

## 2. Verified current state (strategy-verified 2026-10-06 against live
GitHub)

- Remote `main` = `22f38c783d062a9c5352f7bdde8607d9ac299f26` (the 083/1 merge,
  PR #99, merged 2026-10-05T22:30:42Z; parents
  `f754e075364b56571307a41abc4b9dcf3f6f6af0` +
  `b8e1c0bf8f79c3d595ef65743a9c7d4e27ddc366` verified). Post-merge checks at
  22f38c7: CI run 37382943168 success (14 success + 1 skipped Dependency
  review), CodeQL run 37382943108 success; none failed/cancelled/pending. No
  product PR is open; dependabot #83/#94/#100 are open and out of scope.
- Migration head is `072_001` (bootstrap downgrade-compat list includes it);
  this increment adds exactly one new migration, `073_001`.
- 083/1 (PR #99) facts for the F2 flip: real human accept — branch
  `oap/083-a-real-accept`, base
  `f754e075364b56571307a41abc4b9dcf3f6f6af0`, report SELF head
  `b8e1c0bf8f79c3d595ef65743a9c7d4e27ddc366`, merge commit
  `22f38c783d062a9c5352f7bdde8607d9ac299f26`, merged
  2026-10-05T22:30:42Z.
- 083/1 KNOWN LIMITATION (recorded in the 083-a report; this order must
  address it BY DESIGN): foundation `agent-cow-postgresql==0.2.0`
  `agentcow.get_cow_dependencies` decomposes composite foreign keys as a
  cartesian cross-product of column pairs without ordinal matching
  (`page_base (site_id, locale) -> site_locale_base (site_id, tag)` yields
  the bogus predicate `site_id (uuid) = locale (text)` ->
  `operator does not exist: uuid = text`), so any COW session carrying page
  DML fails the order-mandated accept-job `dependencies(session_id)` closure
  check and the accept job stalls at `REVIEW_JOB_STALE_AT_BUDGET`.
  Composition-only sessions are unaffected. The fix requires a foundation
  release + `uv.lock` change (its own scoped increment; separate human
  decision, pending). Therefore: the DISCARD path in this increment MUST NOT
  call `dependencies(session_id)` anywhere (discard commits nothing); the
  report states the rationale and confirms by grep.
- `control.review_job` (070_001): `job_kind CHECK IN
  ('FREEZE','ACCEPT','DISCARD')` — the DISCARD kind is already legal.
  `slaif_review_job_claim(p_claimant text, p_kinds text[])` (072_001) is
  kind-aware (invalid arrays rejected; stale-recovery block unchanged). The
  worker currently claims `["FREEZE", "ACCEPT"]`
  (`services/backend/src/slaif_agent_site/review_worker/worker.py`, line 99);
  dispatch `run_job` (`review_worker/freeze_job.py`) branches on kind with a
  lazy import for ACCEPT. This increment adds `DISCARD` to the claim array
  and one dispatch branch.
- `control.workspace` (024_001): `status TEXT` with NO CHECK constraint. The
  024_001 stub `slaif_workspace_discard(p_workspace_id uuid) RETURNS void`
  sets status `DISCARDED` + `discarded_at` when
  `status IN ('REVIEW','CONFLICTED','FREEZING')` (else
  `NOT_FOUND_OR_WRONG_STATE`); EXECUTE `slaif_control` only. The 072_001
  `slaif_workspace_accept(p_workspace_id uuid, p_actor_user_account_id uuid)
  RETURNS TABLE (job_id uuid, status text)` is the idempotent-enqueue pattern
  this increment mirrors exactly: workspace row `FOR UPDATE`;
  `WORKSPACE_NOT_FOUND`; a live QUEUED/CLAIMED job returned unchanged BEFORE
  the status gate; status gate; guarded INSERT ... `ON CONFLICT
  (workspace_id, job_kind) WHERE status IN ('QUEUED','CLAIMED') DO NOTHING` +
  re-select guard; guarded status UPDATE; `OWNER TO slaif_owner` + REVOKE
  PUBLIC and all ten long-lived roles + EXECUTE `slaif_control` only.
- Freeze gate (070_001 `slaif_workspace_freeze`): ACTIVE-only (`status =
  'ACTIVE' AND expires_at > CURRENT_TIMESTAMP`) plus capability revocation at
  freeze enqueue (`UPDATE control.capability SET revoked_at =
  CURRENT_TIMESTAMP WHERE workspace_id = $1 AND revoked_at IS NULL`). Discard
  must NOT admit `FREEZING` (transient; races the freeze worker) — a
  deliberate deviation from the 024_001 stub's FREEZING allowance, pinned in
  R1.
- Read model (071_001 `slaif_review_read_model`) has NO workspace-status gate
  (gates: site, admin/membership, workspace+site binding, bound COMPLETE
  snapshot); `CONFLICTED` workspaces already render on the 082/2 review page
  (`metadata.workspace.status = 'CONFLICTED'`). The two `status = 'REVIEW'`
  gates in 071_001 (lines 727, 798) sit only in the human-session
  review-artifact list/retrieve functions (frozen browser evidence remains
  REVIEW-only — acceptable; note it in the report). This increment therefore
  needs NO read-model change.
- 083/1 admin review page (`apps/web/src/admin/workspace-review.tsx` +
  `accept-action.tsx`): the accept control is present only for
  REVIEW+COMPLETE+drift.equal (`canAccept`); the CONFLICTED terminal text
  (`accept-action.tsx` lines 32-33) currently reads "Promotion conflict: the
  canonical content changed while the promotion was in flight. Re-review is
  required: freeze a new snapshot and accept again." — inaccurate (freeze is
  ACTIVE-only, so a CONFLICTED workspace cannot be re-frozen); R4.3 corrects
  it to name discard / a fresh workspace as the available remedy.
- Human RBAC catalog (014_001 line 36; `human_authorization/catalog.py` line
  54): `workspace:discard` EXISTS. `authority.session.recent_auth` is
  available (recent-auth window default 900s).
- `agent_state/promotion.py`: `discard_workspace(pool, session_id, schema, *,
  acquire_timeout)` exists with ZERO callers (verified by grep; kept for this
  increment, retired in R3.7); `get_conflicts` exists for 084.
- Worker foundation surface: `apply_product_privileges`
  (`db/privileges.py`) grants `slaif_review_worker` USAGE on `agentcow` +
  EXECUTE on the exact 13-function foundation reviewer set
  (`FOUNDATION_REVIEWER_FUNCTIONS`), which includes
  `discard_cow(text, text, uuid, uuid[])`; the Python API entry is
  `CowReviewer.discard_session(session_id, *, schema='content') ->
  DiscardResult` (via `asyncpg_cow_reviewer`, re-exported by
  `slaif_agent_site/agent_state/foundation.py`). The worker already holds
  `SELECT, INSERT, UPDATE ON control.review_job`, `SELECT, INSERT ON
  control.review_snapshot`, `UPDATE ON control.workspace`, `UPDATE ON
  control.site`. 083/2 requires ZERO new worker grants — the report proves
  the grant surface unchanged by query.
- Control route template (083/1 accept route,
  `control_api/workspace_http.py` + `control_api/database.py`): `POST
  /api/control/v1/sites/{siteId}/workspaces/{workspaceId}/accept/` -> 202;
  session + CSRF + state-changing + dual permission + `recent_auth`; strict
  body with a boolean-typed `acknowledge_*` field validator (JSON `1` must
  not coerce); uniform no-oracle 404; 409 for the wrong state; the human
  entry DB function enforces exact site binding + permission re-check.
- Control route policy: 196 keys (control 34; agent 88; editor 74) pinned in
  `services/backend/tests/unit/test_route_policy.py`; this increment adds
  exactly ONE control line (196 -> 197 keys, control 34 -> 35).
- E2E roster: 18 Playwright projects (`tools/compose/e2e.sh` echo line,
  incl. `accept-lifecycle=1`); next is 19 with `discard-lifecycle`.
- `oap/orders/` contains the complete historical order set incl.
  `083-a-real-accept.md`; there is NO inert pre-plan 083/2 file, so the
  transcript commit T needs no deletion.
- Architecture (ARCHITECTURE-for-agents.md, normative compact edition):
  discard lifecycle `REVIEW -> DISCARD_QUEUED -> DISCARDING -> DISCARDED`
  (terminal); the MVP conflict remedy is discard; "Discard atomically discards
  pending operations, marks DISCARDED, revokes tokens, schedules
  staging/artifact cleanup, retains audit"; "MVP remedies are discard,
  fresh/reapplied workspace, manual workspace correction, or selective
  non-conflicting closure"; invariants "discard restores absence of pending
  work" and "Discard removes pending content/staging; accepted media cannot
  overwrite"; the review worker remit includes discard; `slaif_reviewer`
  carries controlled discard.
- The local coding checkout is on `oap/083-a-real-accept` @
  `b8e1c0bf8f79c3d595ef65743a9c7d4e27ddc366` (the merged 083/1 head;
  tree-identical to main `22f38c7`); the executor MUST first reset the local
  checkout to verified remote main
  `22f38c783d062a9c5352f7bdde8607d9ac299f26`.

## 3. Strategic context

- Objectives 078/079/081/082 are COMPLETE and merged; 083/1 (real human
  accept) is merged as PR #99 at `22f38c783d062a9c5352f7bdde8607d9ac299f26`
  (2026-10-05T22:30:42Z). Numeric Objective 083 remains PARTIAL: 083/2 (real
  discard) and 083/3 (outbox consumer + public media finalization consumer)
  remain.
- 083/2 delivers the other half of the human-governed review lifecycle: when
  a freeze conflicts, or the human simply does not want the pending work, the
  reviewer can atomically discard the pending workspace work — canonical site
  untouched, audit retained, terminal state `DISCARDED` — making discard a
  real, safe, reviewer-executed MVP remedy instead of a status-only stub.
- Sequence approved by the human (D5): 083/1 (done) -> 083/2 (this increment)
  -> 083/3 -> 084 conflict-safe lifecycle -> 080 MCP parity -> 085+.
- This increment deliberately excludes re-review (CONFLICTED->REVIEW) and
  conflict-resolution semantics (084): freeze is ACTIVE-only, so a bare
  re-review flip would be a dead end; 084 owns re-freeze/review conflict
  resolution.

## 4. Bounded scope

One semantic family: the real discard path, end to end within its trust
boundaries.

- R1 — migration `073_001`: rebuild `slaif_workspace_discard` as the
  idempotent enqueue (REVIEW/CONFLICTED only); human entry
  `slaif_human_agent_workspace_discard` with exact site binding +
  `workspace:discard` re-check; byte-exact 024_001 stub restoration on
  downgrade; zero new worker grants; mechanical head pin 072_001 -> 073_001.
- R2 — control discard route `POST .../discard/` (202) with the strict
  `acknowledge_discard` body.
- R3 — worker DISCARD job (`review_worker/discard_job.py`): claim kinds
  +`DISCARD`; single `asyncpg_cow_reviewer` transaction with
  `discard_session`; NO `dependencies()` closure check; retry/budget back to
  origin status; retire `promotion.py::discard_workspace`.
- R4 — admin review page: the discard control (REVIEW/CONFLICTED + COMPLETE
  snapshot), the CONFLICTED terminal-text correction, terminal-state
  rendering.
- R5 — current-truth docs: four surfaces, including the 083/1 F2 flip.
- R6 — contracts byte-identity (strip-identity re-proven both sides).
- R7 — evidence: local suites, compose smoke, new E2E project
  `discard-lifecycle` (roster 18 -> 19).
- R8 — hard constraints (section 6.8).

## 5. Explicit non-goals

- No re-review (CONFLICTED->REVIEW) surface; no re-freeze or
  conflict-resolution semantics (084); no selective accept (the 024_001 stub
  `slaif_workspace_selective_accept` remains untouched and unconnected).
- No freeze, snapshot-shape, snapshot-digest, or 082/2 read-model change
  (071_001 byte-unchanged, incl. the two REVIEW-only review-artifact gates).
- No media processing: no finalization, no outbox events (the outbox CHECK
  allows `WORKSPACE_ACCEPTED` only), no GC changes — private staging bytes of
  a discarded workspace become GC-reclaimable orphans handled by the existing
  media GC; canonical media rows are untouched.
- No cache-outbox CONSUMER and no anonymous public media behavior (083/3); an
  unconsumed outbox row is NOT cache invalidation; web surfaces remain
  force-dynamic/no-store.
- No renderer or Puck behavior change (the admin review page is the only web
  surface touched).
- No Agent-facing discard of any kind: the Agent route policy, OpenAPI, and
  capability catalog are byte-unchanged for this increment.
- No MCP work, no Objective 084+ work, no dependabot work, no
  lockfile/CI-workflow/supply-chain file changes, no new dependencies, no
  physical content-model schema change (content models are workspace data,
  never Alembic operations).

## 6. Requirements

### R1 — Migration 073_001 (upgrade and downgrade both exact)

1. Rebuild `control.slaif_workspace_discard(p_workspace_id uuid,
   p_actor_user_account_id uuid)` as the idempotent enqueue (replacing the
   024_001 stub `slaif_workspace_discard(uuid)`), mirroring the 072_001
   `slaif_workspace_accept(uuid, uuid)` pattern EXACTLY:
   - `RETURNS TABLE (job_id uuid, status text)`, `LANGUAGE plpgsql SECURITY
     DEFINER SET search_path = pg_catalog`;
   - workspace row `SELECT ... FOR UPDATE`; `WORKSPACE_NOT_FOUND` (ERRCODE
     `P0002`) when absent;
   - idempotency BEFORE the status gate: a live (`QUEUED` or `CLAIMED`)
     DISCARD job is returned unchanged regardless of the current workspace
     status;
   - status gate: require `status IN ('REVIEW','CONFLICTED')`, else stable
     `WORKSPACE_NOT_DISCARDABLE` (`P0002`). Deliberate deviation from the
     024_001 stub's FREEZING allowance: FREEZING is transient and races the
     freeze worker; the report states this;
   - defensive idempotent capability revocation (the freeze pattern):
     `UPDATE control.capability SET revoked_at = CURRENT_TIMESTAMP WHERE
     workspace_id = $1 AND revoked_at IS NULL`;
   - enqueue: INSERT one DISCARD job (`status='QUEUED'`,
     `payload = jsonb_build_object('site_id', ..., 'origin_status',
     <'REVIEW'|'CONFLICTED'>, 'actor_user_account_id', ...)`) with `ON
     CONFLICT (workspace_id, job_kind) WHERE status IN ('QUEUED','CLAIMED')
     DO NOTHING` + re-select guard (stable `DISCARD_ENQUEUE_CONFLICT` when
     not found), mirroring the 072_001 accept enqueue;
   - `UPDATE control.workspace SET status = 'DISCARD_QUEUED' WHERE id = $1
     AND status IN ('REVIEW','CONFLICTED')`;
   - return `(live_id, live_status)`;
   - `ALTER FUNCTION ... OWNER TO slaif_owner`; REVOKE ALL from PUBLIC and
     all ten long-lived roles; `GRANT EXECUTE` for `slaif_control` only.
2. New human entry `control.slaif_human_agent_workspace_discard(p_workspace_id
   uuid, p_site_id uuid, p_user_id uuid) RETURNS TABLE (job_id uuid, status
   text)`, mirroring the 072_001 `slaif_human_agent_workspace_accept` shape
   (minus the snapshot/digest expectation — discard takes no snapshot
   input):
   - exact site binding (workspace exists with that `site_id`), else no row;
   - platform administrator OR effective-membership `workspace:discard`
     re-check via `control.slaif_effective_human_membership`, else no row
     (uniform 404 class at the route — no oracle);
   - delegates to `slaif_workspace_discard(p_workspace_id, p_user_id)`; the
     enqueue's stable `WORKSPACE_NOT_DISCARDABLE` propagates (409 class);
   - returns the same `COALESCE(ws_status, row.status)` response
     construction as the 083/1 human entry;
   - same OWNER/REVOKE/GRANT treatment: EXECUTE `slaif_control` only.
3. Downgrade: drop exactly the two functions created/rebuilt
   (`slaif_human_agent_workspace_discard(uuid,uuid,uuid)`,
   `slaif_workspace_discard(uuid,uuid)`) and restore the BYTE-EXACT 024_001
   stub `slaif_workspace_discard(uuid) RETURNS void` plus its
   `GRANT EXECUTE ... TO slaif_control` pin (the report byte-diffs the
   restored function body against the 024_001 source). Round trip proven.
4. Bootstrap downgrade-compat list + `073_001`; mechanical migration-head
   pins 072_001 -> 073_001 across the established integration files.
5. Zero new worker grants: no GRANT/REVOKE in this migration touches
   `slaif_review_worker` or the `agentcow` surface; the report proves the
   worker grant surface unchanged by query.

### R2 — Control discard route

1. `POST /api/control/v1/sites/{siteId}/workspaces/{workspaceId}/discard/`
   -> 202 `{"job_id": <uuid>, "status": <workspace status after enqueue>}`
   (a live existing job returns the SAME job id — idempotent), mirroring the
   083/1 accept-route response construction exactly.
2. Authority: human session + CSRF + state-changing + `workspace:discard`
   (missing -> the established uniform denial class, 404 class) +
   `authority.session.recent_auth` required (absent -> the established 401
   class; L4 high-delete action).
3. Body, strict: exactly `{"acknowledge_discard": true}`;
   `acknowledge_discard` must be boolean `true` (the established
   field-validator pattern — JSON `1` must NOT coerce); missing/extra/mistyped
   fields -> the established request-validation rejection class.
4. Resolution mapping (uniform, no oracles):
   - unknown site/workspace or wrong site binding -> uniform 404;
   - missing `workspace:discard` authority -> uniform 404 (pairwise
     indistinguishable from not-found; proven by an integration pair);
   - workspace exists but not discardable (incl. terminal `DISCARDED`, and
     `FREEZING`) -> 409 `WORKSPACE_NOT_DISCARDABLE`;
   - a live job -> idempotent 202 with the same job id;
   - real DB error -> 503 from None (the established class).
5. No Agent-facing discard exists or can be created: the Agent route policy
   and capability catalog are untouched (grep-pinned).
6. Route policy: exactly ONE new control line (SITE_PERMISSION, mutation
   class MUTATION, `workspace:discard` per the established mechanism);
   totals move 196 -> 197 keys, control 34 -> 35.

### R3 — Worker DISCARD job (the real discard)

1. Dispatch: the worker loop claims with `["FREEZE", "ACCEPT", "DISCARD"]`
   (the `worker.py` line-99 array); `FREEZE` -> existing `run_freeze_job`
   (behavior byte-unchanged); `ACCEPT` -> existing `run_accept_job`
   (unchanged); `DISCARD` -> new `review_worker/discard_job.py::
   run_discard_job` (lazy import, mirroring the ACCEPT branch); the
   unreachable other-kind branch stays as-is (terminal FAILED stable code).
2. `run_discard_job` sequence (all state transitions via the existing grant
   surface inside explicit transactions; no partial visibility):
   1. re-read the workspace `status`: `DISCARD_QUEUED` (fresh claim) or
      `DISCARDING` (crash replay) only, else terminal failure with the
      stable `STATE_DRIFT` code, no mutation;
   2. mark `DISCARDING` (guarded `UPDATE ... WHERE id = $1 AND status IN
      ('DISCARD_QUEUED','DISCARDING')`, require exactly 1 row; 0 rows ->
      `STATE_DRIFT` terminal);
   3. acquire the established exclusive product advisory lock EXACTLY as
      `accept_job.py` does: `SELECT pg_advisory_xact_lock(
      hashtextextended($1, 280))` on `str(workspace_id)`;
   4. verification transaction: workspace row `FOR UPDATE`, re-check
      `status = 'DISCARDING'` (else `STATE_DRIFT` terminal, no mutation);
   5. SUCCESS — ONE `asyncpg_cow_reviewer` connection/transaction,
      all-or-nothing:
      1. `discard_session(session_id=workspace_id, schema='content')`
         (foundation Python API over the already-granted `discard_cow`
         surface; the report records the returned `DiscardResult` fields
         `discarded_tables` / `discarded_operations` / `no_op`);
      2. workspace -> `DISCARDED` (+ `discarded_at`), guarded `UPDATE ...
         WHERE id = $1 AND status = 'DISCARDING'`, require exactly 1 row;
      3. job -> `SUCCEEDED` via the established terminal-writing helper (the
         083/1 shared path);
      4. COMMIT (a failure anywhere rolls back ALL of 1-3).
      Explicit order requirement: NO `dependencies(session_id)` closure
      check anywhere in the discard path — discard commits nothing, so the
      083/1 known foundation `get_cow_dependencies` limitation must not
      affect it; the report states the rationale and confirms by grep that
      the discard path calls only `discard_session` + control-table updates.
      No media processing: private staging bytes of the discarded workspace
      become GC-reclaimable orphans handled by the existing media GC; no
      finalization, no outbox event, no canonical media touch.
   6. Retry/terminal mappings (mirroring the 083/1 accept-job mappings):
      - transient/infrastructure failure (DB error, crash): job
        `ROLLED_BACK` (stays CLAIMED; stale-claim recovery re-queues under
        the attempt budget) — the workspace stays `DISCARDING` and a
        re-claim replays from step 1;
      - retryable failure: workspace back to the origin status from the job
        payload (`origin_status`: `REVIEW` or `CONFLICTED`) + job terminal
        FAILED with the stable code (stale-claim recovery re-queues under
        budget); at budget -> origin status + `REVIEW_JOB_STALE_AT_BUDGET`
        (no dead end);
      - crash replay (`discard_session` completed, terminal not yet written):
        must converge idempotently — the executor documents the foundation's
        OBSERVED behavior for `discard_session` on an already-discarded
        session (`no_op=True` / empty operations, or a clean stable error)
        and pins it in a test (deviation with evidence acceptable).
3. Retire `agent_state/promotion.py::discard_workspace` (no callers after
   wiring): delete it and convert its unit-test coverage to the real path;
   keep `get_conflicts` untouched for 084.

### R4 — Admin review page discard control

1. The 083/1 admin review page (`workspace-review.tsx` + the accept control)
   gains the discard control, and ONLY the discard control: no Puck, no other
   controls. New `apps/web/src/admin/discard-action.tsx` following the
   `csp-modal.tsx` / `accept-action.tsx` pattern; `api.ts` gains the discard
   POST.
2. The discard control is present ONLY when the read model reports
   `status IN {'REVIEW','CONFLICTED'}` AND a bound COMPLETE snapshot — NO
   drift gate on discard (discard is the drift remedy); the accept control
   is unchanged (`canAccept` remains REVIEW-only + drift-gated; the review-
   surface pin proves per-state presence/absence of both controls).
3. CONFLICTED -> a conflict banner with stable human-facing text naming
   discard (and a fresh workspace) as the available remedy; AND correct the
   083/1 `accept-action.tsx` CONFLICTED terminal text (currently "...Re-
   review is required: freeze a new snapshot and accept again." —
   unavailable: freeze is ACTIVE-only) to name discard / a fresh workspace
   as the remedy.
4. Confirmation dialog: a REQUIRED acknowledgement checkbox (default
   unchecked) explaining that discard deletes the pending workspace work and
   the canonical site is untouched; submit POSTs the R2 body with CSRF;
   `acknowledge_discard` is sent `true` only when the checkbox is ticked.
5. Terminal rendering: after 202, poll the existing read route (the
   established 083/1 terminal-render polling pattern, same interval/count
   constants, pinned in the spec) and render `DISCARD_QUEUED` / `DISCARDING`
   (transient) and `DISCARDED` (terminal) with stable human-facing text.
6. Responsive at the three established viewports; keyboard accessible; the
   web unit route-inventory pin updates for the new page state; the
   review-surface E2E pins update (discard control count per state:
   REVIEW+COMPLETE -> 1 (accept also 1), CONFLICTED -> 1 (accept 0),
   ACTIVE/ACCEPTED/DISCARDED -> 0); frozen browser evidence remains REVIEW-
   only (the 071_001 artifact gates are unchanged — note it in the report).

### R5 — Current-truth documentation (four surfaces, durable form)

Update exactly these four surfaces, in the durable form established by the
078-z governance transition:

- `README.md`
- `oap/INCREMENTS.md`
- `oap/MVP-PROGRESS.md`
- `oap/MVP-CONTRACT-AUDIT.md`

1. F2 flip (owed from 083/1): every 083/1 "in flight" reference becomes the
   verified merge fact — PR #99, merge commit
   `22f38c783d062a9c5352f7bdde8607d9ac299f26`, merged
   2026-10-05T22:30:42Z (including the MVP-CONTRACT-AUDIT authoritative-
   source-revision line, which moves to
   `22f38c783d062a9c5352f7bdde8607d9ac299f26`).
2. Record 083/2 as in flight at round `083-2-a` (branch
   `oap/083-2-a-real-discard`, base
   `22f38c783d062a9c5352f7bdde8607d9ac299f26`), and state that GitHub is
   authoritative for live acceptance/merge state; `oap/active` means "last
   activated round until the next activation".
3. State that numeric Objective 083 remains PARTIAL (083/3 = outbox consumer
   and the public media finalization consumer remains planned); the
   MVP remains NOT COMPLETE; no "this PR is open" / "pending strategic
   merge" / "active increment means open PR" ephemeral wording anywhere in
   the four surfaces.
4. The adversarial grep (current-state stale-claim patterns) returns nothing
   in the four surfaces at the report head.

### R6 — Contracts byte-identity

- `git diff base..head -- contracts/ packages/` is empty;
- the agent OpenAPI 47-path strip-identity
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83` is
  re-proven at BOTH base and head (strategy recomputes both sides).

### R7 — Evidence (actually executed, honestly reported)

1. Local unit + integration suites (full), including at minimum:
   - grant-surface-unchanged proof: `slaif_review_worker` memberships/grants
     (incl. the 13-function `agentcow` surface and the control-table grants)
     identical to the 083/1 pins by query;
   - `073_001` round trip: upgrades cleanly from `072_001`, downgrades back,
     restored `slaif_workspace_discard(uuid)` byte-identical to the 024_001
     stub (byte diff proven);
   - enqueue matrix: `REVIEW` and `CONFLICTED` each enqueue with the exact
     payload (`origin_status` correct, `actor_user_account_id` correct,
     `site_id` correct); the full non-discardable set (`FREEZING`,
     `ACCEPT_QUEUED`, `PROMOTING`, `ACTIVE`, `ACCEPTED`, `DISCARDED`) ->
     `WORKSPACE_NOT_DISCARDABLE`; the capability-revoke side effect pinned
     (workspace capability rows revoked exactly once; no double revoke);
     idempotency BEFORE the gate (a live job is returned unchanged
     regardless of status);
   - route authority matrix: `workspace:discard` missing -> uniform 404
     (pairwise indistinguishable from not-found); `recent_auth` absent ->
     401 class; binding 404; `acknowledge_discard` false/missing/mistyped
     (incl. JSON `1`) -> the request-validation rejection class; terminal
     `DISCARDED` -> 409 (pinned once); live job -> idempotent 202 same job
     id; agent capability token on the control discard route -> uniform
     denial (no discard surface);
   - worker success path (integration, real PostgreSQL + foundation): a COW
     session with content incl. media AND real page DML (the ADJ-4
     limitation is deliberately outside the discard path) ->
     `DiscardResult` recorded; COW session clean (`get_session_operations`
     empty, dirty tables 0); workspace `DISCARDED` + `discarded_at`; job
     `SUCCEEDED`; canonical untouched (canonical revision unchanged,
     canonical row counts unchanged, public render bytes identical before/
     after); private media bytes not public; canonical media rows untouched;
     audit rows retained;
   - CONFLICTED discard: the 083/1 conflict-fixture workspace (`CONFLICTED`)
     -> discard -> `DISCARDED` (the conflict remedy works);
   - crash-replay convergence: interrupt after `discard_session`, before the
     terminal write -> re-claim converges to `DISCARDED` exactly once
     (foundation behavior documented);
   - budget exhaustion from BOTH origin statuses (REVIEW and CONFLICTED) ->
     back to the origin status + at-budget job code (no dead end);
   - kinds-array pin: `["FREEZE","ACCEPT","DISCARD"]` claims all three kinds
     FIFO; an invalid array is rejected (072_001 behavior unchanged);
   - `discard_workspace` retirement: module import surface + test inventory
     pin the removal.
2. Compose smoke (`tools/compose/smoke.sh`, baseline-relative): no new
   wiring — the review-worker mounts/env are UNCHANGED; the E2E roster echo
   line moves 18 -> 19 (`discard-lifecycle=1`); worker readiness unchanged.
3. New E2E project `discard-lifecycle` (roster 18 -> 19,
   `dependencies: ["governance"]`, Desktop Chrome, dedicated run-unique
   site):
   - positive: human session -> workspace with content + media AND real page
     DML (fine here — discard never calls `dependencies()`) -> freeze ->
     REVIEW + COMPLETE snapshot -> discard with typed confirmation ->
     `DISCARDED`, all durable effects verified (psql: workspace row +
     `discarded_at`, job `SUCCEEDED`; canonical revision unchanged; public
     render bytes identical before/after; media bytes not public) -> a
     duplicate discard POST -> terminal 409 (pinned once);
   - negatives (E2E where the boundary is the real one):
     `acknowledge_discard` false/missing -> the validation rejection class;
     ACTIVE workspace discard -> 409; agent capability on the control
     discard route -> uniform denial; control-absence pins.
4. The full CI roster (19 projects) terminal and green at the exact report
   head: all 20 required checks successful, none failed/cancelled/pending;
   first attempt or one documented flake-class re-run max.

### R8 — Hard constraints (violation = rejection)

- Zero Agent-facing discard path; Agent route policy / OpenAPI / capability
  catalog byte-unchanged.
- No re-review (CONFLICTED->REVIEW); no selective accept; no read-model
  change; no freeze/snapshot change.
- No media finalization; no outbox events/consumer; no GC changes; no
  anonymous public media behavior change.
- No dependabot incorporation; no lockfile, CI-workflow, or supply-chain
  file changes; no new dependencies; no new compose mounts/env.
- No secrets in code/docs/tests.

## 7. Acceptance criteria (observable)

1. `073_001` upgrades cleanly from `072_001` and downgrades back (round
   trip; restored stub byte-identical to the 024_001 source); all new/
   changed functions are `SECURITY DEFINER` with `search_path = pg_catalog`,
   `OWNER slaif_owner`, and the exact grant pins; the bootstrap revision set
   updates.
2. Grant surface proven unchanged by query (worker role memberships/grants
   identical to the 083/1 pins; no new GRANT/REVOKE in `073_001`).
3. Enqueue: both discardable states enqueue with the exact payload; the full
   non-discardable set -> `WORKSPACE_NOT_DISCARDABLE`; idempotency before the
   gate; capability-revoke side effect pinned.
4. Route authority matrix complete (permission, recent auth, CSRF, binding,
   strict body incl. no `1`-as-boolean coercion, uniform 404/409/401 classes,
   idempotent 202, terminal 409, agent denial) with honest pins.
5. Worker success proven end to end in real PostgreSQL + foundation: single
   reviewer transaction (fault injection mid-transaction leaves NO partial
   state), `DiscardResult` recorded, `DISCARDED` + `discarded_at`, job
   `SUCCEEDED`, canonical untouched (revision + row counts + public render
   bytes identical), private media not public, audit retained.
6. CONFLICTED discard proven (fixture-based): the conflict remedy works; the
   workspace is terminal `DISCARDED`.
7. Crash-replay convergence documented + pinned (idempotent, single
   terminal).
8. Budget exhaustion from BOTH origin statuses -> origin status + at-budget
   code; no dead end.
9. R4: discard control presence/absence per state pinned in the DOM at three
   viewports; confirmation dialog requires the acknowledgement; CONFLICTED
   text corrected; terminal states render; accept control unchanged
   (`canAccept` pinned); no Puck.
10. R5: the four surfaces match the durable form exactly; the F2 flip is
    present; the adversarial grep returns nothing in the four surfaces.
11. R6: `git diff base..head -- contracts/ packages/` empty; strip-identity
    sha256 re-proven at both base and head (strategy recomputes both sides).
12. R7: full CI roster (19 projects) terminal and green at the exact report
    head, 20/20 required checks; predeclared budgets (section 10) honest;
    cumulative base->head grouped size computed; the 20 prod/config-file
    trigger reported explicitly fired/not-fired; CLOSURE_ONLY state
    (expected: never entered) reported; any variance itemized and classed.

## 8. Verification and workflow

- Strategy activates this order atomically with `oap/active` = `083-2-a`.
- The executor first resets the local checkout to verified remote main
  `22f38c783d062a9c5352f7bdde8607d9ac299f26`, then creates branch
  `oap/083-2-a-real-discard` and pushes the transcript commit T first. T
  contains exactly: the order file and `oap/active` bytes as published (no
  deletion needed — there is no inert pre-plan 083/2 file).
- Implementation commits follow (I, ...); a docs commit (D) with the R5
  flips precedes the report commit (S, report-only, parent = implementation
  head).
- Local authority: the executor owns packages, browsers, databases,
  services, compose stacks, and test execution in the disposable VM
  (passwordless sudo); strategy never performs that labor.
- GitHub workflow: push the branch, open the unique objective PR (title per
  section 1), report the PR number/URL/branch/SHAs in the report. No merge
  by the executor — only strategy merges.
- Flake policy: at most ONE documented unmodified CI re-run, and only for a
  documented flake class with its exact failure signature; any other
  recurrence is a real failure — fix in code or report BLOCKED.
- The full CI roster must reach the terminal roster at the exact report head;
  do not re-run unmodified heads except the single documented flake-class
  allowance.

## 9. Report requirements

`oap/reports/083-2-a-real-discard.md` must contain, at minimum:

- Order identity (round, objective, PR, branch, base, every commit
  T/I/.../D/S with SHAs), the exact report-publication convention
  (`Report publication commit: SELF`; the remote PR head must be that
  report-only commit whose parent is the literal implementation-head SHA).
- Authoritative GitHub state at report time (PR number, head SHA, check
  state per run).
- Honest CI history (every run, every failure, every re-run with the exact
  flake signature if the allowance is used).
- Budget table vs the predeclared budget (production/config; migrations;
  test/evidence; generated; docs; OAP transcript; substantive lines) with
  the cumulative base->head grouped size and the explicit trigger
  fired/not-fired determination.
- Every R7 evidence item with its actual executed output (counts, SHAs,
  psql baselines, hashes, the advisory lock id used, the `DiscardResult`
  fields, the before/after public-render byte-identity, the viewport list,
  any adaptation itemized with rationale).
- The grant-surface-unchanged proof query output.
- The 024_001 byte-diff restoration proof.
- Explicit confirmation that the discard path contains NO
  `dependencies(session_id)` call (grep + the ADJ-4 rationale).
- The foundation's observed behavior for `discard_session` on an already-
  discarded session (crash-replay evidence).
- Deviations from this order (if any) with rationale; known limitations;
  residual risks and what 083/3 needs from this increment.
- R8 hard-constraint confirmation (lockfiles/workflows/supply-chain byte-
  identity; Agent surface byte-identity; no re-review/selective-accept/read-
  model/media/outbox work; no new compose mounts/env).
- `Report publication commit: SELF`.

## 10. Predeclared review budget (2026-09-14 review-unit governance
in force)

- Production/config files: at most 15 — itemized: migration `073_001` 1;
  `review_worker/discard_job.py` new 1; `review_worker/worker.py` 1;
  `review_worker/freeze_job.py` (dispatch branch) 1;
  `control_api/workspace_http.py` 1; `control_api/database.py` 1;
  `control_api/route_policy.py` 1; `agent_state/promotion.py` (retirement)
  1; `apps/web/src/admin/discard-action.tsx` new 1;
  `apps/web/src/admin/workspace-review.tsx` 1;
  `apps/web/src/admin/accept-action.tsx` (text fix) 1;
  `apps/web/src/admin/api.ts` 1; `playwright.config.ts` 1;
  `tools/compose/e2e.sh` 1; plus at most 1 small helper/UI file if truly
  needed (e.g. a `tools/compose/smoke.sh` baseline echo line).
- Migrations: exactly 1 (`073_001`).
- Test/evidence files: at most 16 (the new discard integration suite file
  class: enqueue matrix, worker success/CONFLICTED/crash-replay/budget,
  route authority, kinds pin, retirement pin; the new `discard-lifecycle`
  E2E spec; the mechanical pin class: migration head 072_001 -> 073_001
  across the established integration files, route-policy totals 196 -> 197,
  web route-inventory pin, review-surface DOM pins, smoke baseline if
  touched).
- Generated-contract footprint: 0 (byte-identity, R6).
- Docs footprint: 4 surfaces (R5).
- OAP transcript footprint: this order + `active` + one report.
- Substantive implementation-line scale: at most 2800 lines (honest
  estimate — report the actual).
- The ~20-30 production/config file threshold remains a REVIEW TRIGGER, not
  a quota: if the honest cumulative count crosses 20, the PR enters
  CLOSURE_ONLY — no new semantic family may enter after that point.
- Do not game the budget by moving code between directories, excluding
  meaningful tests, or treating generated/OAP files as if they do not exist.

## 11. Review-unit governance (2026-09-14 amendment, in force)

- Cumulative review size is computed base->head (not latest-round delta),
  grouped: production/config; migrations; tests/evidence; generated
  artifacts; docs; OAP transcript.
- CLOSURE_ONLY mode (if triggered): no new semantic family, no adjacent
  feature, no opportunistic scope, no next-objective work; only finite
  defects/evidence required to make already-added behavior safe, correct,
  and reviewable. Separable functionality starts from verified merged main
  in another PR.
- If Strategy rejects COMPLETE, one finite checklist of unresolved criteria
  with the executable evidence required for each; a later report may claim
  COMPLETE only if every named criterion was actually executed; an omitted
  required browser/PostgreSQL/concurrency/public-boundary proof makes the
  report PARTIAL/BLOCKED, never COMPLETE.
- If remaining work is semantically separable, it is split BEFORE being
  added to this PR.
