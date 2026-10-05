# OAP Work Order — 083-a: real human accept (reviewer transaction +
publish) (083/1)

## 1. Identifier and mode

- Round ID: `083-a` (the FIRST semantic increment of numeric Objective 083
  uses the legacy flat `NNN-L` namespace per
  `oap/governance/2026-09-14-increment-qualified-round-ids.md`; a second
  increment of Objective 083 would use `083-2-a`, a third `083-3-a`).
- Objective: 083 (083/1 — real human accept: the reviewer transaction and
  the human publish decision).
- Mode: CREATE_NEW_PR — one fresh PR from verified main; one bounded
  semantic family (the real accept path). Strategy anticipates a single
  round; if a completion claim is rejected, the SAME PR continues at
  `083-b` with a new order.
- Branch: `oap/083-a-real-accept`, created from verified remote main
  `f754e075364b56571307a41abc4b9dcf3f6f6af0`.
- PR title: `OAP 083-a: real human accept (reviewer transaction +
  publish) (083/1)`.
- PR number: whatever GitHub assigns at creation (expected #99; report the
  actual number; never assume it in documentation — reference the
  increment, branch, and SHAs, and the PR number as GitHub reports it).
- The dependabot PRs #83/#90/#94 are out of scope and are never touched.

## 2. Verified current state (strategy-verified 2026-10-05 against live
GitHub)

- Remote `main` = `f754e075364b56571307a41abc4b9dcf3f6f6af0` (the 082/2
  merge, PR #98, merged 2026-10-05T08:54:51Z; parents `e689076cda0a882ad13f7b641ebdf8efdacba773` +
  `072f7e337b1d1592db87a6b11d5fcc7854d34873` verified). Post-merge checks
  at f754e07: CI run 37286616514 success, CodeQL run 37286616459 success;
  none failed/cancelled/pending. No product PR is open; dependabot
  #83/#90/#94 are open and out of scope.
- Migration head is `071_001`; this increment adds exactly one new
  migration, `072_001`.
- 082/2 (PR #98) facts: human read-only review surface; `071_001` read
  model (EXECUTE `slaif_control`, computes `drift.equal` from
  `base_site_revision` vs current `control.site.canonical_revision`);
  control `GET .../review/` route; flight-free snapshot-only `/review/`
  render; admin review page with ZERO accept/discard/Puck controls
  (grep-pinned); control route policy = 195 keys (control 33); agent
  OpenAPI 47 paths, strip-identity
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`.
- 082/2 documentation debt (verified in the four current-truth surfaces):
  "in flight" wording about 082/2 that became false at merge. This
  increment's R5 performs that flip (deferred from 082/2 by plan).
- `control.review_job` (070_001): `job_kind CHECK IN
  ('FREEZE','ACCEPT','DISCARD')` — the ACCEPT kind is already legal;
  `slaif_review_job_claim(p_claimant text)` is currently KIND-BLIND (claims
  any QUEUED job, FIFO by created_at,id); the worker dispatches FREEZE
  only. 083/1 makes the claim kind-aware.
- `control.workspace` (024_001): `status TEXT` with NO CHECK constraint —
  `ACCEPT_QUEUED`/`PROMOTING`/`CONFLICTED`/`ACCEPTED` are available without
  any widening. `slaif_workspace_accept` is a plain REVIEW→ACCEPTED stub
  (EXECUTE `slaif_control`); `slaif_workspace_discard` (REVIEW/
  CONFLICTED/FREEZING) and `slaif_workspace_selective_accept` exist and are
  untouched by this increment.
- `control.site` (013_001): `canonical_revision BIGINT NOT NULL DEFAULT 0`
  (nonnegative check).
- Audit schema today: `audit.agent_mutation`, `audit.human_editor_mutation`,
  `audit.media_mutation`, `audit.browser_event`, `audit.human_agent_session`
  — NO promotion audit table and NO cache outbox table anywhere; 083/1
  creates both.
- Roles (verified in `db/roles.py` + bootstrap): `REVIEWER_ROLES =
  ("slaif_reviewer",)`; logins `slaif_reviewer_login` and
  `slaif_review_worker_login` both exist; the worker currently holds only
  narrow grants (USAGE control; SELECT/INSERT/UPDATE on `control.review_job`;
  SELECT/INSERT on `control.review_snapshot`). No long-lived role other than
  none currently carries the reviewer group. 083/1 adds
  `GRANT slaif_reviewer TO slaif_review_worker` — the worker process becomes
  the SOLE process holding reviewer authority, per architecture line 199
  ("review worker = sole reviewer DB role").
- Media finalization (079/1, merged): `finalize_media_for_promotion(
  site_id, workspace_id, media_ids, *, store: MediaStore, repository:
  FinalizationRepository) -> FinalizationManifest` in
  `media_service/finalize.py`; `MediaFinalizationRepository(MediaDatabase)`
  (fetch via `content.slaif_media_public_fetch`, mark via
  `content.slaif_media_public_mark` inside `asyncpg_cow_session` with
  session_id=workspace_id); `MediaStore(root)` descriptor-confined. The
  media DB is the SAME `slaif` database over `slaif_media_login`
  (`expected_database = "slaif"`). `secrets-init` already provisions
  `/run/slaif-media` (DSN) and `/var/lib/slaif/media` (root). The
  `review-worker` compose service currently has NO media mounts or
  `SLAIF_MEDIA_*` env — 083/1 adds them.
- Worker (070/082, merged): login `slaif_review_worker_login`, privilege
  role `slaif_review_worker`, DSN file
  `/run/slaif-review-worker/review-worker-dsn`; loop constants poll 1s /
  batch 1 / heartbeat 20s / stale 60s / drain lock 30s / evidence deadline
  120s; `_verify_connection` pins exact login + privilege role; dispatch
  currently calls `freeze_job.run_job` for every claimed job.
- `agent_state/promotion.py`: `promote_workspace(pool, session_id, schema)`
  is a detached wrapper over `asyncpg_cow_reviewer.commit_session` with NO
  callers anywhere (verified by grep); `discard_workspace` and
  `get_conflicts` exist for 083/2. 083/1 retires `promote_workspace`.
- Control surface template (082/2 freeze route): `POST
  /api/control/v1/sites/{siteId}/workspaces/{workspaceId}/freeze/` → 202
  `{job_id, status}`; session + CSRF + state-changing + `workspace:freeze` +
  exact site binding; uniform 404 for not-found/binding; 409
  WORKSPACE_NOT_ACTIVE; DB wrapper
  `control_api/database.py::human_agent_workspace_freeze`.
- Human RBAC catalog (014_001): BOTH `workspace:accept` AND `site:publish`
  exist; `authority.session.recent_auth: bool` is available (recent-auth
  window default 900s).
- E2E roster: 17 Playwright projects (next: 18 with `accept-lifecycle`).
- Snapshots (082/1+082/2): `control.review_snapshot` row with
  `status='COMPLETE'`, `normalized_state` (incl. `base_site_revision`,
  `operation_watermark`), `versions`, `validation_report`, `digest` (sha256
  of the canonical JSON of `normalized_state`; recomputable in DB via
  `control.slaif_canonical_jsonb_text`), `media_references`;
  `workspace.review_snapshot_id` binds it.
- Architecture §8 (normative, compact edition): lifecycle
  `REVIEW -> ACCEPT_QUEUED -> PROMOTING -> ACCEPTED|CONFLICTED|REVIEW`;
  `CONFLICTED -> REVIEW`; `REVIEW -> DISCARDED`. Full acceptance happens in
  ONE `asyncpg_cow_reviewer` transaction: (1) claim/mark job, require
  REVIEW-origin state, exclusive product lock; (2) lock the canonical
  site-revision row and require equality with the approved snapshot;
  (3) verify digest / operation-dependency closure / audit / versions;
  (4) rerun model/item/mapping/relation/query/component-binding/route/
  locale/accessibility/site/media validation under trusted context; (5)
  inspect foundation conflicts, commit with deferred FKs and
  `conflict_policy="error"`; (6) increment canonical revision + promotion
  audit + workspace/job terminal + cache outbox, commit all or roll back
  all; (7) finalize media idempotently before the commit (pre-commit public
  orphans are GC'd). Drift stops BEFORE mutation with the 409-class
  `SITE_REVISION_CHANGED`. `CowConflictError` → rollback everything,
  structured `BASE_ROW_CHANGED|BASE_ROW_DELETED|BASE_ROW_CREATED|
  BASE_SCHEMA_CHANGED`, workspace `CONFLICTED`. Acceptance is L4: recent
  auth, explicit summary acknowledgement, typed confirmation.
- The local coding checkout is on `main` @ `f754e075364b56571307a41abc4b9dcf3f6f6af0`,
  clean.

## 3. Strategic context

- Objectives 078/079/081/082 are COMPLETE and merged (media incl.
  finalization; human Puck in the exact Agent workspace; freeze + immutable
  snapshot; read-only human review surface). Objective 083 is the remaining
  safety-critical core: real accept/discard/promotion. This increment is
  083/1, the first increment of the human-approved pre-split of the old
  inert 082/083 work orders (`workorders/082-083-presplit-analysis-
  2026-10-04.md`, directional only, contents not advance-accepted).
- 083/1 delivers the defining product moment: a human reviews a frozen
  immutable snapshot and the site is REALLY published — canonical revision
  incremented, canonical content replaced, media made public — inside one
  all-or-nothing reviewer transaction, with drift and conflict safety.
- Sequence approved by the human (D5): remaining 078 (done) → 079 (done) →
  081 (done) → 082 (done) → 083/1 → 083/2 → 083/3 → 084 → 080 MCP parity →
  085+.

## 4. Bounded scope

One semantic family: the real accept path, end to end within its trust
boundaries.

- R1 — migration `072_001`: reviewer grant for the worker; kind-aware job
  claim; idempotent REVIEW→ACCEPT_QUEUED enqueue; `audit.promotion`;
  `control.cache_outbox`; exact worker grant set; downgrade exact.
- R2 — control accept route `POST .../accept/` (202) with dual permission,
  recent auth, typed confirmation, uniform error mapping.
- R3 — worker ACCEPT job: kind dispatch, drift gate, validation rerun,
  media finalization wiring, the single `asyncpg_cow_reviewer` promotion
  transaction, conflict mapping, retry/budget behavior; retire
  `promote_workspace`.
- R4 — admin review page: the human accept action (confirmation dialog,
  digest, summary acknowledgement) and terminal state rendering.
- R5 — current-truth docs: four surfaces, including the 082/2 F2 flip.
- R6 — contracts byte-identity (strip-identity re-proven both sides).
- R7 — evidence: local suites, compose smoke, new E2E project
  `accept-lifecycle` (roster 17→18).
- R8 — hard constraints (section 6.8).

## 5. Explicit non-goals

- No discard implementation or UI (083/2): `slaif_workspace_discard`,
  `discard_workspace`, and the job kind `DISCARD` remain exactly as today;
  the worker's claimable-kind set does NOT include `DISCARD`.
- No selective accept (the 024_001 stub remains untouched and unconnected).
- No cache-outbox CONSUMER and no anonymous public media behavior (083/3);
  an unconsumed outbox row is NOT cache invalidation; web surfaces remain
  force-dynamic/no-store.
- No change to freeze, snapshot shape, snapshot digest, or the 082/2 read
  model (EXECUTE grants and behavior unchanged).
- No renderer or Puck behavior change (the admin review page is the only
  web surface touched).
- No Agent-facing accept of any kind: the Agent route policy, OpenAPI, and
  capability scopes are byte-unchanged for this increment.
- No MCP work, no Objective 084+ work, no dependabot work, no
  lockfile/CI-workflow/supply-chain file changes, no new dependencies, no
  physical content-model schema change (content models are workspace data,
  never Alembic operations).

## 6. Requirements

### R1 — Migration 072_001 (upgrade and downgrade both exact)

1. `GRANT slaif_reviewer TO slaif_review_worker;` (downgrade: `REVOKE
   slaif_reviewer FROM slaif_review_worker;`). This is the ONLY reviewer
   authority added anywhere; the report must prove by query that no other
   role/login is a MEMBER of `slaif_reviewer`.
2. Rebuild `control.slaif_review_job_claim` as
   `slaif_review_job_claim(p_claimant text, p_kinds text[])`:
   - `p_kinds` must be a non-empty subset of
     `('FREEZE','ACCEPT','DISCARD')` (else stable `REVIEW_CLAIMANT_INVALID`
     or a new stable `REVIEW_CLAIM_KIND_INVALID` code, executor's choice,
     pinned in tests);
   - the stale-claim recovery block (re-queue under budget;
     `REVIEW_JOB_STALE_AT_BUDGET` at budget) stays EXACTLY as in 070_001 and
     applies to all kinds;
   - the claim selects `status='QUEUED' AND job_kind = ANY(p_kinds)`,
     `ORDER BY created_at, id LIMIT 1 FOR UPDATE SKIP LOCKED`;
   - `SECURITY DEFINER`, `search_path = pg_catalog`, EXECUTE for
     `slaif_review_worker` only, PUBLIC revoked;
   - the 070_001 single-argument definition is replaced (CREATE OR
     REPLACE); the downgrade restores the exact 070_001 definition.
3. Rebuild `control.slaif_workspace_accept(p_workspace_id uuid)` as the
   idempotent enqueue (replacing the 024_001 stub; downgrade restores the
   exact 024_001 stub):
   - requires `status='REVIEW'`, else stable `WORKSPACE_NOT_IN_REVIEW`;
   - requires `review_snapshot_id` bound to a `control.review_snapshot`
     row with `status='COMPLETE'`, else a stable not-found code (uniform
     404 class at the route — no oracle);
   - if a live (`QUEUED` or `CLAIMED`) ACCEPT job exists for the workspace,
     return it unchanged (idempotent); else INSERT one ACCEPT job
     (`payload = {"snapshot_id": <uuid>}` plus `site_id`), set the
     workspace `status='ACCEPT_QUEUED'`, and return `(job_id, status)`;
   - `SECURITY DEFINER`, `search_path = pg_catalog`, EXECUTE for
     `slaif_control` only.
4. `CREATE TABLE audit.promotion` with columns: `id UUID PRIMARY KEY
   DEFAULT gen_random_uuid()`, `site_id UUID NOT NULL`, `workspace_id UUID
   NOT NULL`, `snapshot_id UUID NOT NULL`, `job_id UUID NOT NULL`, `digest
   TEXT NOT NULL`, `base_site_revision BIGINT NOT NULL`,
   `new_canonical_revision BIGINT NOT NULL`, `committed_operations
   INTEGER NOT NULL`, `versions JSONB NOT NULL`, `actor_user_account_id
   UUID NOT NULL`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`.
   Grants mirror the minimal 070/071 pattern: INSERT for
   `slaif_review_worker`, SELECT for `slaif_reviewer`, REVOKE ALL from
   PUBLIC, no other long-lived role.
5. `CREATE TABLE control.cache_outbox` with columns: `id BIGSERIAL
   PRIMARY KEY`, `site_id UUID NOT NULL`, `workspace_id UUID NOT NULL`,
   `event_kind TEXT NOT NULL CHECK (event_kind IN ('WORKSPACE_ACCEPTED'))`,
   `payload JSONB NOT NULL`, `created_at TIMESTAMPTZ NOT NULL DEFAULT
   now()`. Grants: INSERT/SELECT for `slaif_review_worker`; REVOKE ALL from
   PUBLIC. No consumer in this increment.
6. Exact additional worker grants (and only these): `SELECT, UPDATE ON
   control.workspace`; `SELECT, UPDATE ON control.site`;
   `SELECT ON control.review_snapshot` (already present — re-pin);
   `INSERT ON audit.promotion`; `INSERT, SELECT ON control.cache_outbox`.
   No broad table grants; no role gains raw SELECT on the snapshot beyond
   the existing worker pin.
7. Downgrade drops EXACTLY the objects created (two tables), revokes
   EXACTLY the grants added, and restores the exact 070_001 claim and
   024_001 accept definitions. Round trip proven.

### R2 — Control accept route

1. `POST /api/control/v1/sites/{siteId}/workspaces/{workspaceId}/accept/`
   → 202 `{"job_id": <uuid>, "status": "ACCEPT_QUEUED"}` (a live existing
   job returns the SAME job id — idempotent).
2. Authority: human session + CSRF + state-changing + BOTH `workspace:
   accept` AND `site:publish` (fail-closed: either missing → the
   established uniform denial class) + `authority.session.recent_auth`
   required (absent → the established 401 class).
3. Body, strict: exactly `{"snapshot_id": <uuid>, "digest": <64-hex sha256
   string>, "acknowledge_summary": true}`; `acknowledge_summary` must be
   boolean `true`; missing/extra/mistyped fields → the established request-
   validation rejection class.
4. Resolution mapping (uniform, no oracles):
   - unknown site/workspace or wrong site binding → uniform 404;
   - `snapshot_id` does not match the bound COMPLETE snapshot, or `digest`
     does not equal the stored digest → uniform 404 (indistinguishable
     from the not-found case; proven by E2E/integration pair);
   - workspace exists but `status <> 'REVIEW'` → 409
     `WORKSPACE_NOT_IN_REVIEW`;
   - the enqueue stable codes map to the same classes as the freeze route
     template.
5. No Agent-facing accept exists or can be created: the Agent route policy
   and capability catalog are untouched (grep-pinned).
6. Route policy: exactly ONE new control line (SITE_PERMISSION, mutation
   class MUTATION, the two-permission requirement encoded per the
   established conditional-scope mechanism); totals move 195 → 196 keys,
   control 33 → 34.

### R3 — Worker ACCEPT job (the real promotion)

1. Dispatch: the worker loop claims with `p_kinds = ARRAY['FREEZE',
   'ACCEPT']` (never `DISCARD` in this increment); `FREEZE` → existing
   `freeze_job.run_job` (behavior byte-unchanged except the claim call
   site); `ACCEPT` → new `review_worker/accept_job.py::run_accept_job`; an
   unreachable other kind → job terminal FAILED with a stable code.
2. `run_accept_job` sequence (all state transitions via the R1 grant
   surface inside explicit transactions; no partial visibility):
   1. re-check workspace `status='ACCEPT_QUEUED'` (else terminal failure
      with a stable code, no mutation);
   2. mark `PROMOTING` (`UPDATE ... WHERE status='ACCEPT_QUEUED'`, require
      exactly 1 row);
   3. acquire the established exclusive product lock (the same advisory
      lock id and usage pattern the freeze worker already uses — verify
      against `freeze_job.py` and mirror it exactly);
   4. `SELECT canonical_revision FROM control.site WHERE id=$1 FOR
      UPDATE`; require equality with `snapshot.normalized_state.
      base_site_revision`; mismatch → drift path (step 8a);
   5. verify the snapshot: recompute the digest over
      `normalized_state` via `control.slaif_canonical_jsonb_text` and
      require equality with the stored digest; require `versions`
      equality; require the operation watermark to be closed (foundation
      `dependencies(session_id)` shows no open dependency beyond the
      watermark; audit closure per architecture §8);
   6. rerun validation under trusted context: the snapshot shape
      validation already computed at freeze (reuse the 082/1 validator
      path, not a copy), media reference resolution (every referenced
      media id resolvable), and the route/locale contract checks from
      `content_model` (the same validators the freeze path used);
   7. media finalization FIRST (before the commit): build the media
      boundary from `MediaSettings` (worker process) — the `MediaStore`
      root, the `MediaDatabase` (worker media DSN), and the
      `MediaFinalizationRepository` — and call
      `finalize_media_for_promotion(site_id, workspace_id, media_ids,
      ...)` with the snapshot's `media_references`; on
      `FinalizationError` → retry path (step 8b);
   8. terminal mappings:
      - (a) DRIFT: workspace → `REVIEW`, job terminal FAILED
        `SITE_REVISION_CHANGED`, snapshot preserved, NO mutation of any
        kind (row counts + canonical revision proven unchanged);
      - (b) RETRYABLE failure (media store unavailable, transient DB
        error): workspace back to `ACCEPT_QUEUED`, job terminal FAILED
        with the stable code (stale-claim recovery re-queues while the
        attempt budget remains); at budget → workspace → `REVIEW` and job
        FAILED at-budget code (no dead end);
      - (c) SUCCESS: the promotion transaction (step 9);
      - (d) CONFLICT: `CowConflictError` → full rollback, workspace →
        `CONFLICTED`, job terminal FAILED with the structured code mapped
        from the error per architecture §8 (`BASE_ROW_CHANGED |
        BASE_ROW_DELETED | BASE_ROW_CREATED | BASE_SCHEMA_CHANGED`),
        snapshot preserved.
   9. SUCCESS — ONE `asyncpg_cow_reviewer` connection/transaction, all-or-
      nothing:
      1. `commit_session(session_id=workspace_id, schema='content',
         defer_fk_constraints=True, conflict_policy='error')`;
      2. inspect `conflicts(session_id, schema='content')` (non-empty →
         conflict path (d) with full rollback);
      3. `control.site.canonical_revision += 1` (on the already-locked
         row);
      4. INSERT `audit.promotion` (exact R1 columns; `committed_operations`
         from the foundation result; `actor_user_account_id` = the human
         account that enqueued the accept, carried in the job payload);
      5. workspace → `ACCEPTED` (+ `accepted_at`);
      6. job → `SUCCEEDED`;
      7. INSERT `control.cache_outbox` row (`WORKSPACE_ACCEPTED`, payload:
         snapshot_id, digest, base_site_revision,
         new_canonical_revision, media manifest list);
      8. COMMIT (a failure anywhere rolls back ALL of 1-7).
10. Idempotency: a re-claimed job after crash (finalize already ran,
    commit not yet) must replay to the SAME public media state (finalization
    is idempotent by design) and commit exactly once; duplicate enqueue
    returns the live job (R1.3).
11. Worker media wiring (minimal):
    - `review_worker/config.py` (or the established settings module): load
      the frozen `MediaSettings` in the worker process;
    - compose `review-worker` service gains: volumes
      `media-secret:/run/slaif-media:ro` and `media-data:/var/lib/slaif/
      media` (read-write; finalization publishes public bytes); env
      `SLAIF_MEDIA_MODE=development`, `SLAIF_MEDIA_DSN_FILE=/run/slaif-
      media/media-dsn`, `SLAIF_MEDIA_EXPECTED_LOGIN=slaif_media_login`,
      `SLAIF_MEDIA_EXPECTED_PRIVILEGE_ROLE=slaif_media`,
      `SLAIF_MEDIA_ROOT=/var/lib/slaif/media`;
    - NO changes to any other compose service; `secrets-init` already
      provisions both paths (verified);
    - the media pool is built lazily for ACCEPT jobs (freeze jobs never
      touch media) and shut down with the process.
12. Retire `agent_state/promotion.py::promote_workspace` (no callers):
    delete it and convert its unit-test coverage to the real path; keep
    `discard_workspace` and `get_conflicts` untouched for 083/2.

### R4 — Admin review page accept action

1. The 082/2 admin review page (the surface that is currently grep-pinned
   to contain ZERO accept/discard controls) gains the accept control, and
   ONLY the accept control: no discard, no Puck, no publish shortcut.
2. The control is present ONLY when the read model reports
   `status='REVIEW'` AND a COMPLETE snapshot AND `drift.equal == true`;
   otherwise the re-review message renders instead (the server-side
   equality check in R3.2.4 remains the authority — the UI is advisory).
3. Confirmation dialog: shows the snapshot digest (established short form)
   and a REQUIRED summary-acknowledgement checkbox (default unchecked);
   submit POSTs the R2 body with CSRF; `acknowledge_summary` is sent
   `true` only when the checkbox is ticked.
4. Terminal rendering: after 202, poll the existing workspace read route
   and render `ACCEPT_QUEUED` / `PROMOTING` (transient states) and the
   terminal `ACCEPTED` or `CONFLICTED` states with the stable human-facing
   text; `CONFLICTED` explains that re-review is required.
5. Responsive at the three established viewports; keyboard accessible; the
   web unit route-inventory pin updates for the new page state.

### R5 — Current-truth documentation (four surfaces, durable form)

Update exactly these four surfaces, in the durable form established by the
078-z governance transition:

- `README.md`
- `oap/INCREMENTS.md`
- `oap/MVP-PROGRESS.md`
- `oap/MVP-CONTRACT-AUDIT.md`

1. F2 flip (owed from 082/2): every 082/2 "in flight" reference becomes
   the verified merge fact — PR #98, merge commit
   `f754e075364b56571307a41abc4b9dcf3f6f6af0`, merged
   2026-10-05T08:54:51Z.
2. Record 083/1 as in flight at round `083-a` (branch
   `oap/083-a-real-accept`, base `f754e07`), and state that GitHub is
   authoritative for live acceptance/merge state; `oap/active` means "last
   activated round until the next activation".
3. State the contractual MVP as NOT COMPLETE; the promotion path (real
   accept) is the increment in flight; no "this PR is open" / "pending
   strategic merge" ephemeral wording anywhere in the four surfaces.
4. `oap/INCREMENTS.md` additionally records that the inert pre-plan 083
   work order (accept + discard + promotion in one increment) was
   superseded by the approved 083/1-083/3 pre-split and deleted in this
   PR (content preserved in git history); the 083 rows list 083/1 in
   flight at `083-a`.
5. The adversarial grep (current-state stale-claim patterns) returns
   nothing in the four surfaces at the report head.

### R6 — Contracts byte-identity

- `git diff base..head -- contracts/ packages/` is empty;
- the agent OpenAPI 47-path strip-identity
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83` is
  re-proven at BOTH base and head (strategy recomputes both sides).

### R7 — Evidence (actually executed, honestly reported)

1. Local unit + integration suites (full), including at minimum:
   - grant matrix: `slaif_review_worker` is a MEMBER of `slaif_reviewer`;
     NO other long-lived role/login is; `audit.promotion` and
     `control.cache_outbox` grant set exact; PUBLIC revoked;
   - claim: `ARRAY['FREEZE','ACCEPT']` claims both kinds FIFO; `DISCARD`
     never claimed; invalid kind array rejected; stale-recovery fixture
     unchanged;
   - enqueue: idempotent second call returns the same job id;
     `WORKSPACE_NOT_IN_REVIEW` for ACTIVE/ACCEPTED/CONFLICTED;
     not-found code for missing/non-COMPLETE snapshot; payload exact;
   - route authority matrix: both permissions required (each individually
     missing → uniform denial); `recent_auth` absent → 401 class; binding
     404; snapshot/digest mismatch → uniform 404 (pairwise
     indistinguishable from not-found); `acknowledge_summary` false/missing
     rejected; agent capability token → uniform denial (no accept surface);
   - worker success path (integration, real PostgreSQL + foundation):
     canonical revision +1; `audit.promotion` row fields exact;
     `cache_outbox` row present; workspace `ACCEPTED` + `accepted_at`; job
     `SUCCEEDED`; media public: bytes re-hash to the digest, public path
     exists, `published_at` set; manifest == published set;
   - drift: canonical revision bumped (test authority) before the worker
     runs → `SITE_REVISION_CHANGED`, zero mutation (row counts + revision
     proven unchanged), workspace back to `REVIEW`, snapshot intact;
   - conflict: pre-seeded conflicting canonical row → `CowConflictError`
     with the structured `BASE_ROW_*` code, full rollback (no partial
     state — COW change tables + audit + outbox all empty), workspace
     `CONFLICTED`;
   - retry: crash simulation between finalization and commit → re-claim
     replays idempotently (identical public state, single commit);
     budget exhaustion → workspace `REVIEW` + at-budget job code;
   - `promote_workspace` retired: module import surface + test inventory
     pins the removal.
2. Compose smoke (`tools/compose/smoke.sh`, baseline-relative): the
   review-worker container has the media DSN file readable and the media
   root present (no content leaked into smoke output); worker readiness
   unchanged.
3. New E2E project `accept-lifecycle` (roster 17→18, `dependencies:
   ["governance"]`):
   - positive: human session → workspace with content (Puck or API) →
     freeze → REVIEW + COMPLETE snapshot → accept with typed confirmation
     (digest from the read model) → verify canonical revision increment,
     canonical pages/nodes equal the snapshot content, public media bytes
     and public paths, `audit.promotion` row (psql), `cache_outbox` row
     (psql),
     workspace `ACCEPTED`, and a duplicate accept POST → idempotent 202
     with the same job id (or the terminal-state 409 per R2.4, pinned
     once);
   - negatives (E2E where the boundary is the real one): digest-mismatch
     POST → 404; agent capability on the control accept route → uniform
     denial; drift rendering state (workspace re-frozen after a manual
     revision bump via test authority) → accept control absent + re-review
     message.
4. The full CI roster (18 projects) terminal and green at the exact report
   head: all 20 required checks successful, none
   failed/cancelled/pending; first attempt or one documented flake-class
   re-run max.

### R8 — Hard constraints (violation = rejection)

- Zero Agent-facing accept path; Agent route policy / OpenAPI / capability
  catalog byte-unchanged.
- No discard implementation; no selective accept; no outbox consumer; no
  anonymous public media behavior change.
- No freeze/snapshot/renderer/Puck behavior change.
- No dependabot incorporation; no lockfile, CI-workflow, or supply-chain
  file changes; no new dependencies.
- No secrets in code/docs/tests; the worker media wiring uses the
  established mounted-secret pattern only.

## 7. Acceptance criteria (observable)

1. `072_001` upgrades cleanly from `071_001` and downgrades back (round
   trip, exact drop/revoke/restore set); all new/changed functions are
   `SECURITY DEFINER` with `search_path = pg_catalog` and the exact grant
   pins; the bootstrap revision set updates.
2. Grant matrix proven by query: `slaif_review_worker` is the ONLY
   member of `slaif_reviewer`; the R1.6 grant set is exact; `audit.
   promotion` / `control.cache_outbox` revoke PUBLIC.
3. Kind-aware claim proven (both kinds FIFO; DISCARD unclaimed; invalid
   array rejected; stale recovery unchanged).
4. Enqueue idempotency + every stable code proven at the DB level AND
   through the route (uniform 404 / 409 / 401 classes; no oracle between
   the not-found and mismatched-snapshot cases).
5. Route authority matrix complete (dual permission, recent auth, CSRF,
   binding, strict body, agent denial) with honest pins.
6. Worker success path proven end to end in real PostgreSQL: single
   reviewer transaction (fault injection mid-transaction leaves NO partial
   state), canonical revision +1, exact audit row, outbox row, workspace
   `ACCEPTED`, job `SUCCEEDED`, public media bytes verified against the
   digest, manifest == published set.
7. Drift path: `SITE_REVISION_CHANGED` BEFORE mutation, zero mutation
   proven, workspace `REVIEW`, snapshot intact (integration + E2E
   rendering).
8. Conflict path: structured `BASE_ROW_*` code, full rollback proven,
   workspace `CONFLICTED`, snapshot intact.
9. Retry/budget: crash-replay idempotent (single commit, identical public
   state); budget exhaustion → `REVIEW` + at-budget code.
10. R4: accept control presence/absence per state pinned in the DOM at
    three viewports; confirmation dialog requires the acknowledgement;
    terminal states render; zero discard controls (absence asserted);
    keyboard accessible.
11. R5: the four surfaces match the durable form exactly; the F2 flip is
    present; the adversarial grep returns nothing in the four surfaces.
12. R6: `git diff base..head -- contracts/ packages/` empty; strip-
    identity sha256 re-proven at both base and head (strategy recomputes
    both sides).
13. R7: full CI roster (18 projects) terminal and green at the exact
    report head, 20/20 required checks; predeclared budgets (section 10)
    honest; cumulative base→head grouped size computed; the 20 prod/
    config-file trigger reported explicitly fired/not-fired; CLOSURE_ONLY
    state (expected: never entered) reported; any variance itemized and
    classed.

## 8. Verification and workflow

- Strategy activates this order atomically with `oap/active` = `083-a`.
- The executor creates the branch from verified main
  `f754e075364b56571307a41abc4b9dcf3f6f6af0` and pushes the transcript
  commit T first. T contains exactly: the order file and `oap/active`
  bytes as published, plus the DELETION of the superseded inert pre-plan
  file `oap/orders/083-a-real-accept-discard-promotion.md`. That file was
  never activated (no `active` selection, no signal, no report — inert
  pre-plan), it is superseded by the human-approved 083/1-083/3 pre-split
  (this order is 083/1), its full content remains in git history and in
  the strategic pre-split analysis, and the repository policy requires
  exactly one order file per active identifier. T is therefore the
  minimal transcript that leaves the repository policy-consistent.
- Implementation commits follow (I, ...); a docs commit (D) with the R5
  flips precedes the report commit (S, report-only, parent =
  implementation head).
- Local authority: the executor owns packages, browsers, databases,
  services, compose stacks, and test execution in the disposable VM
  (passwordless sudo); strategy never performs that labor.
- GitHub workflow: push the branch, open the unique objective PR (title
  per section 1), report the PR number/URL/branch/SHAs in the report. No
  merge by the executor — only strategy merges.
- Flake policy: at most ONE documented unmodified CI re-run, and only for
  the documented flake class with its exact failure signature; any other
  recurrence is a real failure — fix in code or report BLOCKED.
- The full CI roster must reach the terminal roster at the exact report
  head; do not re-run unmodified heads except the single documented
  flake-class allowance.

## 9. Report requirements

`oap/reports/083-a-real-accept.md` must contain, at minimum:

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
  the cumulative base→head grouped size and the explicit trigger
  fired/not-fired determination.
- Every R7 evidence item with its actual executed output (counts, SHAs,
  psql baselines, hashes, the advisory lock id used, the media manifest,
  viewport list, any adaptation itemized with rationale).
- The reviewer-authority proof query output (members of `slaif_reviewer`).
- Deviations from this order (if any) with rationale; known limitations;
  residual risks and what 083/2 needs from this increment.
- Confirmation of R8 hard constraints (lockfiles/workflows/supply-chain
  byte-identity; Agent surface byte-identity; no discard/selective-
  accept/consumer work; secrets audit of the new worker wiring).
- `Report publication commit: SELF`.

## 10. Predeclared review budget (2026-09-14 review-unit governance
in force)

- Production/config files: at most 15 (migration `072_001` 1;
  `review_worker/accept_job.py` new 1; `review_worker/worker.py` 1;
  `review_worker/config.py` 1; `control_api/workspace_http.py` 1;
  `control_api/route_policy.py` 1; `control_api/database.py` 1;
  `agent_state/promotion.py` retirement 1; `compose.yaml` 1; admin review
  page 1 (+ at most 1 small UI helper); `playwright.config.ts` 1;
  `tools/compose/e2e.sh` 1; `tools/compose/smoke.sh` 1).
- Migrations: exactly 1 (`072_001`).
- Test/evidence files: at most 16 (integration: grant matrix, claim,
  enqueue, worker success/drift/conflict/retry, route authority — the
  established file class; unit: route-policy/worker-config/promotion-
  retirement pins; the new `accept-lifecycle` E2E spec; the mechanical
  pin class: migration head 071_001→072_001 across the established
  integration files, route-policy totals 195→196, web route-inventory
  pin, smoke baseline).
- Generated-contract footprint: 0 (byte-identity, R6).
- Docs footprint: 4 surfaces (R5).
- OAP transcript footprint: this order + `active` + one report.
- Substantive implementation-line scale: at most 3400 lines (honest
  estimate — 082/2 declared 3000 and delivered 3013, disclosed and
  accepted; declare the real estimate here and report the actual).
- The ~20-30 production/config file threshold remains a REVIEW TRIGGER,
  not a quota: if the honest cumulative count crosses 20, the PR enters
  CLOSURE_ONLY — no new semantic family may enter after that point.
- Do not game the budget by moving code between directories, excluding
  meaningful tests, or treating generated/OAP files as if they do not
  exist.

## 11. Review-unit governance (2026-09-14 amendment, in force)

- Cumulative review size is computed base→head (not latest-round delta),
  grouped: production/config; migrations; tests/evidence; generated
  artifacts; docs; OAP transcript.
- CLOSURE_ONLY mode (if triggered): no new semantic family, no adjacent
  feature, no opportunistic scope, no next-objective work; only finite
  defects/evidence required to make already-added behavior safe, correct,
  and reviewable. Separable functionality starts from verified merged main
  in another PR.
- If Strategy rejects COMPLETE, one finite checklist of unresolved
  criteria with the executable evidence required for each; a later
  report may claim COMPLETE only if every named criterion was actually
  executed; an omitted required browser/PostgreSQL/concurrency/public-
  boundary proof makes the report PARTIAL/BLOCKED, never COMPLETE.
- If remaining work is semantically separable, it is split BEFORE being
  added to this PR.
