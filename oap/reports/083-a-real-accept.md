# OAP Coding-Agent Report — 083-a

## Work order

- Order: `oap/orders/083-a-real-accept.md` (activated via
  `oap/active`, strategic FIFO `OK` received 2026-10-05).
- Round: `083-a` (increment-qualified form: 083/1 — real human accept,
  the first increment of the approved 083/1-083/3 pre-split).
- Objective: 083 (real human accept/discard promotion lifecycle); this
  increment delivers the real human **accept** (reviewer transaction +
  promotion) only.
- Mode: `NNN-a` — one fresh branch + one new PR from authoritative remote
  main.
- Branch: `oap/083-a-real-accept`.
- PR: #99 (URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/99`),
  state OPEN.
- Base: main @ `f754e075364b56571307a41abc4b9dcf3f6f6af0` (PR #98 merged,
  082/2).
- Starting remote main SHA (verified at branch creation):
  `f754e075364b56571307a41abc4b9dcf3f6f6af0`.

## Status

COMPLETE (finite criterion list below; strategy independently reviews and
merges — COMPLETE never means accepted).

## Executive summary

083-1 makes the human accept real: the frozen 082/1 review snapshot is
promoted to canonical by exactly one durable ACCEPT job processed by the
review worker, in ONE all-or-nothing `asyncpg_cow_reviewer` transaction.
The worker process becomes the sole holder of reviewer authority
(`GRANT slaif_reviewer TO slaif_review_worker`, the only reviewer
membership added anywhere; the cluster provisioning edge
`slaif_reviewer TO slaif_owner WITH ADMIN OPTION` makes the migration
edge possible and the owner remains setup-only). Migration `072_001`
rebuilds `control.slaif_review_job_claim` as kind-aware
(`(p_claimant text, p_kinds text[])`, stale-claim recovery
byte-identical to 070_001), rebuilds `control.slaif_workspace_accept` as
the idempotent REVIEW -> ACCEPT_QUEUED enqueue (a live QUEUED/CLAIMED job
is returned unchanged — duplicate accept returns the SAME job id), adds
the human Control entry point `control.slaif_human_agent_workspace_accept`
(exact site binding, dual `workspace:accept` + `site:publish` re-check,
snapshot/digest expectation — every gate failure yields no row: uniform
404 class, no oracle; only the enqueue's stable
`WORKSPACE_NOT_IN_REVIEW` propagates as the 409 class), and creates
`audit.promotion` (append-only promotion audit) +
`control.cache_outbox` (event kind `WORKSPACE_ACCEPTED`; no consumer in
this increment) with exact minimal grants (PUBLIC revoked; the BIGSERIAL
sequence `control.cache_outbox_id_seq` USAGE granted to the worker only).
The worker's foundation reviewer surface (USAGE on the `agentcow`
schema plus EXECUTE on the exact 13 foundation functions the
hardening grants to `slaif_reviewer`) is re-applied by
`apply_product_privileges` on every
HARDENED reconcile — not in the migration, because the `agentcow` schema
does not exist at migration time (documented deviation). The Control
accept route is one dual-permission policy line + one strict handler
(exact three-field body: `snapshot_id`/`digest`/
`acknowledge_summary`, `extra="forbid"`, JSON `1` does not coerce to the
boolean acknowledgement). The admin review page gains the single accept
action (REVIEW + COMPLETE + no drift only; confirmation dialog requires
the acknowledgement; zero discard/publish/Puck affordances remain absent,
grep-pinned and E2E-pinned). The accept job sequence: re-read
(ACCEPT_QUEUED/PROMOTING only) -> PROMOTING -> locked verification
(workspace lifecycle advisory lock key 280, drift gate on the locked
site row under FOR UPDATE, re-materialization + digest re-validation) ->
media finalization FIRST (bytes re-hashed to the digest, public path
`public/sha256/xx/yy/<digest>`, `published_at` set) -> ONE reviewer
transaction: advisory lock, PROMOTING re-check, authoritative drift
gate, foundation watermark closure, `commit_session(conflict_policy=
'error')`, canonical revision +1, `audit.promotion` row, workspace
ACCEPTED + accepted_at, job SUCCEEDED, `control.cache_outbox` row — any
failure rolls back ALL of it. Terminal failure classes: drift ->
REVIEW + `SITE_REVISION_CHANGED` (zero mutation proven); validation ->
REVIEW + `SNAPSHOT_VALIDATION_FAILED`; conflict -> CONFLICTED +
structured `BASE_ROW_*`/`BASE_SCHEMA_CHANGED` (full rollback proven: COW
change tables + audit + outbox all empty); crash (no terminal) -> job
stays CLAIMED, stale-claim recovery re-queues, replay commits exactly
once (identical public state); at budget -> REVIEW +
`REVIEW_JOB_STALE_AT_BUDGET` (no dead end). `agent_state.promotion.
promote_workspace` is retired (the accept job is the only promotion
path); module import surface + test inventory pin the removal.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: #99, OPEN, head branch `oap/083-a-real-accept`, base `main`.
- T (order transcript commit, pushed at activation):
  `24f93317296c8d9361a30cdc41e8858036d775cb` (exact order + active bytes
  as published + deletion of the superseded inert pre-plan
  `oap/orders/083-a-real-accept-discard-promotion.md`).
- I (implementation commit, literal): d18b17809fa4b0591231eb0d2d277e3579e67f12.
- D (docs commit, literal): 2dc77334a36d59b0ba333992e366d26a0fd9b9dc.
- I2 (verification-driven fix commit, literal):
  8d4a79b8f51472da58e9a959b0afb529bd442708 (dedicated-site accept
  proof, bootstrap re-run convergence, roster site-selection fixes;
  full iteration history in the Compose smoke section).
- Implementation head SHA (literal 40-hex pre-report commit; first parent
  of the report commit): 8d4a79b8f51472da58e9a959b0afb529bd442708 (the
  fix commit I2).
- Report publication commit: SELF (report-only; its literal SHA is the
  remote PR head after publication, verified via `git ls-remote` and
  `gh pr view 99 --json headRefOid`), parent = I2; the SELF commit
  changes only the new report file.
- Pushed commits: T (already pushed at activation), I, D, I2, SELF.

## Changes made

### 1. Migration `072_001_real_human_accept.py` (537/0, exactly 1)

- `GRANT slaif_reviewer TO slaif_review_worker`: the worker process
  becomes the sole process holding reviewer authority (architecture
  section 4: "review worker = sole reviewer DB role"). Runs as
  `slaif_owner`; possible only via the new provisioning edge below.
- `control.slaif_review_job_claim` rebuilt as
  `slaif_review_job_claim(p_claimant text, p_kinds text[])`: the
  stale-claim recovery block stays byte-identical to 070_001; the claim
  selects `status='QUEUED' AND job_kind = ANY(p_kinds)`; the 070_001
  single-argument definition is dropped.
- `control.slaif_workspace_accept(p_workspace_id uuid,
  p_actor_user_account_id uuid)` rebuilt as the idempotent REVIEW ->
  ACCEPT_QUEUED enqueue (replacing the 024_001 stub): a live
  QUEUED/CLAIMED ACCEPT job is returned unchanged BEFORE the status gate
  (duplicate accept returns the SAME job id); the actor is carried in
  the job payload for the promotion audit row; stable codes
  `WORKSPACE_NOT_FOUND` / `WORKSPACE_NOT_IN_REVIEW` /
  `REVIEW_SNAPSHOT_NOT_FOUND` (all `P0002`); payload =
  `{workspace_id, site_id, actor_user_account_id, snapshot_id,
  snapshot_digest, versions, media_manifest}` (exact, verified).
- `control.slaif_human_agent_workspace_accept(p_workspace_id,
  p_site_id, p_user_account_id, p_expected_snapshot_id,
  p_expected_digest)`: exact site binding (workspace.site_id must equal
  the bound site), dual `workspace:accept` + `site:publish` re-check,
  snapshot/digest expectation against the workspace's COMPLETE
  snapshot; every failure yields NO row (uniform 404 class, no oracle);
  the enqueue's `WORKSPACE_NOT_IN_REVIEW` propagates (409 class).
- `audit.promotion` (append-only: workspace/site/snapshot/digest/
  actor/result fields; `id BIGSERIAL`) and `control.cache_outbox`
  (`event_kind` CHECK `WORKSPACE_ACCEPTED`, jsonb `payload`,
  `id BIGSERIAL`) with the exact minimal grant sets:
  `audit.promotion` INSERT worker + SELECT reviewer; `control.
  cache_outbox` INSERT, SELECT worker; PUBLIC revoked on both;
  `USAGE ON SCHEMA audit` worker; `USAGE ON SEQUENCE
  control.cache_outbox_id_seq` worker (BIGSERIAL nextval for the
  worker INSERT; no other role gets the sequence).
- Exact additional worker grants: UPDATE on `control.workspace` and
  `control.site` (SELECT already present since 070_001), the
  `control.review_snapshot` SELECT re-pin.
- The worker's foundation (`agentcow`) reviewer surface is NOT granted
  here: the `agentcow` schema does not exist at migration time
  (`deploy_cow_functions` runs during bootstrap reconcile, after the
  Alembic head is reached). It is applied and re-applied by
  `apply_product_privileges` on every HARDENED reconcile (item 3 below);
  the promotion transaction runs `asyncpg_cow_reviewer` as the worker
  login, and the product privilege roles are NOINHERIT, so the
  transitive worker -> reviewer membership carries no effective
  authority — the surface must be granted directly to the worker role
  (documented deviation 4). All 13 functions are SECURITY DEFINER owned
  by `slaif_owner`, so no content/agentcow table grants are required or
  granted.
- Downgrade drops exactly the two tables, revokes exactly the grants
  added, drops the two rebuilt functions + the human entry point,
  revokes the reviewer membership, and restores the exact 070_001 claim
  and 024_001 accept definitions (round trip verified).

### 2. Cluster provisioning edges (`db/roles.py`, 24/0)

- `provision_database_roles` re-establishes the two non-login
  privilege-role memberships AFTER the privilege-role REVOKE loop, so
  re-provisioning converges (idempotent; the later login REVOKE loops
  only touch `LOGIN_NAMES`):
  1. `slaif_reviewer TO slaif_owner WITH ADMIN OPTION` — the owner is
     setup-only, never a product process credential; this lets the
     migration (running as `slaif_owner`) manage reviewer membership.
  2. `slaif_reviewer TO slaif_review_worker` — the review worker is
     the sole reviewer process. The edge is also granted by the
     `072_001` migration (and removed by its downgrade); the
     provisioning re-grant is what makes bootstrap re-runs converge
     (I2; root cause and verification in the Compose smoke section —
     without it, every re-provision dropped the migration-only edge
     and the reconcile privilege validation failed).
- `verify_database_privileges` documents the exact two-edge
  membership contract (comment update, no behavior change).

### 3. Worker foundation surface re-application (`db/privileges.py`)

- The HARDENED block of `apply_product_privileges` now re-applies, on
  every reconcile: `USAGE ON SCHEMA agentcow` + EXECUTE on the exact 13
  foundation functions the hardening grants to `slaif_reviewer`
  (`get_cow_dirty_tables`, `get_cow_primary_key_columns`,
  `get_cow_session_operations`, `get_cow_dependencies`, `_cow_fk_edges`,
  `get_cow_conflicts`, `commit_cow`, `commit_cow_upsert`,
  `commit_cow_delete`, `commit_cow_cleanup`, `discard_cow`,
  `_cow_lock_session`, `_cow_operation_tables`) — to `slaif_review_worker`.
  Mirrors how the hardening re-grants the reviewer; keeps the future
  083/2 `discard_cow` need covered without any table grant.
- The expected-privilege manifest records the new exact state: the
  worker joins the agentcow USAGE / 13-function EXECUTE holder set
  (holders per function: `slaif_owner`, `slaif_reviewer`,
  `slaif_review_worker`); the `effective-sequence` check carve-out allows
  exactly `has_sequence_privilege = (SELECT=False, UPDATE=False,
  USAGE=True)` for the worker on `control.cache_outbox_id_seq` (PG16
  reports sequence USAGE as the USAGE flag only; `has_table_privilege`
  on the sequence reports all-false).

### 4. Control accept route (R2)

- `control_api/route_policy.py`: one new policy line —
  `POST /api/control/v1/sites/{site_id}/workspaces/{workspace_id}/accept/`
  (mutation class, CSRF, site-scoped, SITE_PERMISSION kind, dual
  permission tuple `("workspace:accept", "site:publish")`). Route-policy
  total 195 -> 196 (pin updated).
- `control_api/workspace_http.py`: strict body model
  `AcceptWorkspaceRequest` (`frozen=True, extra="forbid"`;
  `snapshot_id: UUID`; `digest` = exact 64-hex lowercase;
  `acknowledge_summary` must be the boolean `true` — JSON `1` is
  rejected by the before-validator) + one handler `accept_workspace`:
  `authorize_site_request(..., "workspace:accept", state_changing=True)`
  -> platform-administrator OR `site:publish` effective permission else
  uniform `ResourceNotFoundError`; `recent_auth` absent ->
  `AuthenticationError` (401 class); SQL entry point call;
  `WORKSPACE_NOT_IN_REVIEW` -> `ResourceConflictError` (409 class); any
  other surprise -> `ServiceUnavailableError` (fail closed); no row ->
  uniform 404. Response `202 {job_id, status}`.
- `control_api/database.py`: one method `human_agent_workspace_accept`
  (one SELECT of the function through the established
  `_human_agent_call` gate).

### 5. Worker ACCEPT job (R3)

- `review_worker/accept_job.py` (new, 600/0): the full sequence from the
  executive summary. Media boundary: `MediaBoundary` built lazily from
  the worker process environment on first ACCEPT use (compose mounts
  the media secret + data volume); freeze jobs never touch it;
  `store_unavailable`/`repository_unavailable` are retryable, an
  unresolvable media reference is a validation failure. The
  re-materialization runs in the locked verification transaction (the
  materializer sets a transaction-local COW context GUC), never inside
  the reviewer transaction. `run_accept_job` returns the structured
  `JobResult`; `shutdown_media_boundary` closes the lazy boundary on
  worker stop.
- `review_worker/worker.py`: the claim now calls
  `slaif_review_job_claim($1, $2)` with `["FREEZE", "ACCEPT"]`;
  dispatch on `job_kind` (FREEZE -> `run_job`, ACCEPT ->
  `run_accept_job`); shutdown closes the media boundary.
- `review_worker/freeze_job.py`: the `JobResult` terminal-writing
  helper (`_mark_terminal`) is shared by both job kinds (no behavior
  change to freeze semantics; stale-recovery fixture unchanged).

### 6. `promote_workspace` retirement (R3)

- `agent_state/promotion.py`: `promote_workspace` deleted (the accept
  job is the only promotion path); module docstring updated;
  `discard_workspace`/conflict inspection remain for the discard
  increment. Unit test pins the import surface (no `promote_workspace`
  attribute; no `PromotionResult` re-export) and the inventory.

### 7. Admin review page accept action (R4)

- `apps/web/src/admin/workspace-review.tsx`: one accept action in the
  actions area — rendered ONLY when the read model says REVIEW +
  COMPLETE snapshot + no drift; confirmation dialog requires the
  acknowledgement (the exact boolean `true` in the body); digest +
  snapshot id come from the read model; on 202 the page shows the
  terminal state (QUEUED/ACCEPTED); zero discard/publish/Puck
  affordances (grep-pinned + E2E-pinned).
- `apps/web/src/admin/api.ts`: one `acceptWorkspace` client method
  (202 `{job_id, status}`).
- `apps/web/src/admin/accept-action.tsx` (new): the bounded UI helper
  (button + confirmation dialog + result state), the one small UI
  helper slot from the predeclared budget. The confirmation dialog
  uses the app's `CspModal` (Radix `modal=false` + inert background +
  Tab containment) rather than a modal Radix Dialog: modal Radix
  renders inline-styled focus guards (`el.style.outline = "none"`
  etc.) that the strict `style-src 'self'` CSP blocks (proven by the
  E2E strict-console observer during development); the site-switcher
  and membership dialogs already use the same `CspModal` pattern.
- `tests/e2e/review-surface.spec.ts`: the 082/2 "NO accept/discard"
  pin becomes "accept present exactly once (REVIEW + COMPLETE + no
  drift), NO discard/publish" at the same three viewports.

### 8. Compose wiring (R7.2)

- `compose.yaml`: the review-worker service carries the media
  finalization boundary — `SLAIF_MEDIA_MODE/DSN_FILE/EXPECTED_LOGIN/
  EXPECTED_PRIVILEGE_ROLE/ROOT` environment (the established
  mounted-secret pattern) + `media-secret:/run/slaif-media:ro` +
  `media-data:/var/lib/slaif/media` volumes. No new service, no new
  image, no host port change.
- `tools/compose/smoke.sh`: one new mode/ownership assertion — the
  worker container has `/run/slaif-media/media-dsn` `400:uid10001`
  readable and the media root `700:uid10001` present (no content
  printed): `review-worker-media-boundary: OK dsn=0400:uid10001
  root=0700:uid10001`.
- `tools/compose/e2e.sh`: the `accept-lifecycle` project runs after
  `freeze-review-snapshot` and before `media-publication`; the OK line
  counts `projects=18 ... accept-lifecycle=1`.
- `tools/compose/verify.py`: the pre-existing policy baseline pins are
  extended for the review-worker media boundary (no policy
  relaxation): `EXPECTED_MOUNTS["review-worker"]` +=
  `("media-secret","/run/slaif-media",True)` +
  `("media-data","/var/lib/slaif/media",False)`;
  `MEDIA_SECRET_MOUNT_SERVICES` += `"review-worker"`;
  `safe_environment` admits `SLAIF_MEDIA_DSN_FILE` for
  `{media-service, review-worker}` and the five `SLAIF_MEDIA_*` keys
  for review-worker; the foreign-Media-setting check excludes
  `{media-service, review-worker}`.
- `compose.yaml` (review-worker env): `SLAIF_MEDIA_EXPECTED_DATABASE:
  slaif` (parity with media-service; the established pinned style).

### 9. Tests / evidence

- `services/backend/tests/integration/test_real_human_accept.py` (new,
  1728/0): the 10 acceptance-criteria tests (grant matrix; kind-aware
  claim + stale recovery; enqueue idempotency + stable codes; route
  authority matrix; worker success path; drift zero-mutation; conflict
  full rollback; retryable rollback + budget; crash replay idempotent;
  `promote_workspace` retired). Real disposable PostgreSQL 16 + the
  real foundation (0.2.0 public API) + real media root (0700).
- `tests/e2e/accept-lifecycle.spec.ts` (new): Playwright project
  `accept-lifecycle` (roster 17 -> 18, `dependencies:
  ["governance"]`), real browser + real PostgreSQL through public
  NGINX. The proof runs on a DEDICATED RUN-UNIQUE SITE seeded by the
  spec via test-authority psql (same fixture pattern as the e2e.sh
  parity seed): `control.site` (`acceptproof-<8hex>`, ACTIVE) +
  `SITE_OWNER` membership for compose.admin + `content.site_locale_base`
  (`en`) + a PUBLISHED `home` `content.page_base` with empty
  composition. Rationale (I2; full history in the Compose smoke
  section): the proof must not mutate the canonical demo home (the
  later public agent theme browser proof derives a fresh workspace
  from it and requires the bootstrap composition to stay inside the
  browser-worker URL policy), and it must not run page DML in the COW
  session (the foundation 0.2.0 `get_cow_dependencies` composite-FK
  cross-product bug fails any page-DML session's accept; see Known
  limitations). The agent performs composition-only operations on the
  pre-seeded home. Positive: agent workspace (L2_SITE_EDITOR) ->
  capability -> media upload -> Image+Heading components on `home` ->
  freeze -> REVIEW + COMPLETE snapshot -> accept with typed
  confirmation -> canonical revision increment, canonical nodes equal
  the snapshot content (psql count on the dedicated site, `p.slug =
  'home'` + run-unique heading text), public canonical home
  `GET /s/<site_key>` (the localhost-only render convention; the home
  page is the site root) 200 + contains the run-unique heading, public
  media bytes re-hash to the frozen digest with `public_status` +
  `published_at` asserted via psql (CASE `t`/`f` boolean render),
  `audit.promotion` row via psql, `control.cache_outbox` row via psql,
  workspace ACCEPTED, duplicate accept POST -> 409 stable conflict
  class. Negatives: digest mismatch -> 404; unknown snapshot id ->
  same uniform 404; agent capability on the control accept route ->
  uniform 401 via the cookie-free `request` fixture;
  `acknowledge_summary=false`/missing -> 422; drift after manual
  revision bump via test authority (on the dedicated site) -> accept
  control absent + re-review message. Both tests set
  `test.setTimeout(300_000)` (the established worker-wait convention;
  the global 30s project budget is too tight for the promotion wait).
- `tests/e2e/media-publication.spec.ts` (3/1): the cross-site hostile
  target selection was positional (`sites.find(site_key !==
  "parity")`, intended demo); run-unique fixture sites that sort
  before `demo` in `/me/sites` (platform administrators see every
  site, ordered by site_key) displace it — the first such site has no
  human workspace, so the human media upload 404s. Now selects
  `site_key === "demo"` explicitly (one line + comment), matching
  every other roster consumer.
- `tests/packaging/test_compose_smoke_contract.py` (2/1): mechanical
  roster pin — `dependencies: ["governance"]` count 12 -> 13 and
  `accept-lifecycle` added to the presence tuple.
- `tools/compose/smoke.sh` (9/1 vs base): the earlier +6 media
  boundary check plus (I2) the media stage's site selection — the
  first element of `/me/sites` is now resolved by explicit
  `site_key === "demo"` (same hermeticity fix as above; the old
  positional pick hit the run-unique accept-proof sites and failed
  the human upload with 404).
- Unit pins: route-policy total 195 -> 196; promotion-retirement import
  surface; worker dispatch; foundation contract; control database;
  health apps; review worker config.
- Mechanical pin class: migration head `071_001` -> `072_001` across
  the established integration files; bootstrap downgrade-compatibility
  revision set (+`072_001`); smoke baseline.

### 10. Documentation (R5, 4 surfaces, commit D)

- `README.md`: new Objective-082/2 (merged) row (PR #98,
  `f754e075364b56571307a41abc4b9dcf3f6f6af0`, 2026-10-05) + planned
  product work = real human accept (083/1, in flight at `083-a`),
  discard (083/2), outbox consumer and public media finalization
  (083/3), approved-source and responsive-sweep orchestration,
  reconstruction, remaining hardening.
- `oap/INCREMENTS.md`: header flip (082/2 merged; 083/1 in flight at
  `083-a`, branch + base), 082/2 ledger row, Next row -> 083 after
  082/2 with the inert pre-plan 083 order record (superseded by the
  approved 083/1-083/3 pre-split, deleted in this PR, content preserved
  in git history).
- `oap/MVP-PROGRESS.md`: sequence paragraph flip; 082 PARTIAL ->
  COMPLETE (082/1 PR #97 + 082/2 PR #98); 083 SCAFFOLD ONLY -> PARTIAL
  (083/1 in flight; 083/2 + 083/3 planned).
- `oap/MVP-CONTRACT-AUDIT.md`: audited source revision -> verified
  merged main `f754e075364b56571307a41abc4b9dcf3f6f6af0` (083/1
  current-truth reconciliation); shared-renderer row (082/2 merged
  fact); freeze row PARTIAL -> COMPLETE (snapshot rendering delivered
  by 082/2, completing the invariant); accept/discard row note -> 083/1
  in flight at `083-a` (083/2 + 083/3 planned). Contractual MVP
  NOT COMPLETE (unchanged verdict).

## Files changed

Base `f754e075364b56571307a41abc4b9dcf3f6f6af0` -> head (T + I + D +
I2):

```text
 2   1  README.md
229   0  apps/web/src/admin/accept-action.tsx
 20   0  apps/web/src/admin/api.ts
  9   5  apps/web/src/admin/workspace-review.tsx
 10   0  compose.yaml
  8   4  oap/INCREMENTS.md
  4   4  oap/MVP-CONTRACT-AUDIT.md
  3   3  oap/MVP-PROGRESS.md
  1   1  oap/active
  0  55  oap/orders/083-a-real-accept-discard-promotion.md (deleted, T)
648   0  oap/orders/083-a-real-accept.md (T)
  6   0  playwright.config.ts
  5  28  services/backend/src/slaif_agent_site/agent_state/promotion.py
  1   0  services/backend/src/slaif_agent_site/bootstrap/service.py
  9   0  services/backend/src/slaif_agent_site/control_api/database.py
 14   0  services/backend/src/slaif_agent_site/control_api/route_policy.py
 62   0  services/backend/src/slaif_agent_site/control_api/workspace_http.py
537   0  services/backend/src/slaif_agent_site/db/alembic/versions/072_001_real_human_accept.py
193  30  services/backend/src/slaif_agent_site/db/privileges.py
 24   0  services/backend/src/slaif_agent_site/db/roles.py
600   0  services/backend/src/slaif_agent_site/review_worker/accept_job.py
 11   7  services/backend/src/slaif_agent_site/review_worker/freeze_job.py
  4   1  services/backend/src/slaif_agent_site/review_worker/worker.py
 11  11  services/backend/tests/integration/test_agent_mutations.py
  3   3  services/backend/tests/integration/test_agent_page_style.py
  1   1  services/backend/tests/integration/test_browser_run_control_plane.py
  3   3  services/backend/tests/integration/test_control_database_integration.py
 18   8  services/backend/tests/integration/test_database_bootstrap.py
  1   1  services/backend/tests/integration/test_editable_domain_proof.py
 11   5  services/backend/tests/integration/test_freeze_review_snapshot.py
  5   4  services/backend/tests/integration/test_full_stack_integration.py
  1   1  services/backend/tests/integration/test_human_agent_session_control.py
1728  0  services/backend/tests/integration/test_real_human_accept.py
  3   2  services/backend/tests/integration/test_review_surface_read_model.py
  5   2  services/backend/tests/integration/test_workspace_integration.py
  6   5  services/backend/tests/unit/test_control_database.py
  4   1  services/backend/tests/unit/test_foundation_contract.py
  1   0  services/backend/tests/unit/test_health_apps.py
 49  60  services/backend/tests/unit/test_promotion.py
 32   4  services/backend/tests/unit/test_review_worker.py
  2   2  services/backend/tests/unit/test_route_policy.py
639   0  tests/e2e/accept-lifecycle.spec.ts
  3   1  tests/e2e/media-publication.spec.ts
  5   5  tests/e2e/review-surface.spec.ts
  2   1  tests/packaging/test_compose_smoke_contract.py
  9   1  tools/compose/e2e.sh
  9   1  tools/compose/smoke.sh
 22   4  tools/compose/verify.py
```

(additions/removals per file; the report file itself is added by the
SELF commit and is counted in the OAP transcript group below)

## Pre-declared budget check (order Section 10 vs measured)

| Group | Predeclared | Measured (base->head) | Verdict |
| --- | --- | --- | --- |
| Production/config files | at most 15 | 19 (13 itemized-slot files + 6 non-itemized: `apps/web/src/admin/api.ts`, `bootstrap/service.py`, `db/privileges.py`, `db/roles.py`, `review_worker/freeze_job.py`, `tools/compose/verify.py`) | +4 over the line; each itemized below; CLOSURE_ONLY trigger (20) not crossed |
| Migrations | exactly 1 | 1 (`072_001`) | exact |
| Test/evidence files | at most 16 | 22 (new integration spec + 11 mechanical-pin integration updates + 6 unit pins + new E2E spec + review-surface E2E update + media-publication E2E hermeticity fix + packaging roster pin) | +6 (mechanical pin-class updates beyond the slot list, incl. the 083/1 signature pins in the two files found by the first full run and the two I2 roster-hermeticity test fixes) |
| Generated-contract footprint | 0 | 0 | exact (R6) |
| Docs footprint | 4 surfaces | 4 | exact |
| OAP transcript | order + active + one report | 3 (order + active + report; the inert pre-plan deletion is part of the transcript) | exact |
| Substantive implementation lines | at most 3400 | 1774 (all prod/config + migration added lines; pure Python/TypeScript code only: 1746 after excluding 28 shell/compose/yaml lines) | well under (52%) |

- Itemized production/config slots used: migration (1),
  `review_worker/accept_job.py` (1), `review_worker/worker.py` (1),
  `control_api/workspace_http.py` (1), `control_api/route_policy.py`
  (1), `control_api/database.py` (1), `agent_state/promotion.py`
  retirement (1), `compose.yaml` (1), admin review page (1), + 1 small
  UI helper (`accept-action.tsx`) (1), `playwright.config.ts` (1),
  `tools/compose/e2e.sh` (1), `tools/compose/smoke.sh` (1) = 13 of 14
  itemized slots; `review_worker/config.py` slot unused (the media
  settings reuse the existing `MediaSettings` locator, no worker config
  change needed). The 6 non-itemized files are the itemized deviations
  below (deviations 4, 5 plus the mechanical wiring files).
- The ~20 production/config file REVIEW TRIGGER: NOT FIRED (19 < 20).
- CLOSURE_ONLY: never entered (no trigger crossed; no scope added after
  any hypothetical trigger point).
- Variance classing: the +2 file variance is the documented
  foundation-surface re-application deviation (1 file,
  `db/privileges.py`) plus the provisioning edge it requires (1 file,
  `db/roles.py`); the 2 remaining non-itemized files are one-line
  mechanical wiring (`apps/web/src/admin/api.ts` client method,
  `bootstrap/service.py` revision-set entry) and the shared-terminal
  helper extraction (`review_worker/freeze_job.py`) and the compose
  policy-baseline extension for the review-worker media boundary
  (`tools/compose/verify.py`); the +4
  test/evidence variance is the mechanical pin class (incl. the
  rebuilt-function signature pins in
  `test_freeze_review_snapshot.py` and
  `test_browser_run_control_plane.py`, found by the first full local
  run and fixed before commit I); no code was moved
  between directories to game the budget, no meaningful tests were
  excluded, and generated/OAP files were counted.

## Deviations and adaptations (order Section 9; one line each)

1. `#variable_conflict use_column` in `072_001`: Alembic SQL-template
   marker inside the PL/pgSQL bodies so `SELECT * INTO ws` column
   names take precedence over same-named local variables in
   `op.execute` rendering (mechanical Alembic requirement; zero
   semantic effect on the installed function text).
2. Explicit `RETURN;` after `RETURN QUERY SELECT live_id, live_status;`
   in the idempotent path of `control.slaif_workspace_accept`: PL/pgSQL
   `RETURN QUERY` does not terminate the function, so the explicit
   `RETURN` stops the idempotent path before the status gate
   (semantics identical to a terminating return; without it execution
   would fall through to the REVIEW gate and raise
   `WORKSPACE_NOT_IN_REVIEW` on a duplicate accept).
3. JSONB decode of `versions` AND of `doc` in
   `accept_job._verify_snapshot` (and the materializer path): asyncpg
   0.31.0 returns jsonb columns as str, so the snapshot-document decode
   happens BEFORE the media private -> public replay normalization
   (the earlier `isinstance(doc, dict)` guard silently skipped the
   normalization and produced `SNAPSHOT_VALIDATION_FAILED` in
   crash-replay; `build_snapshot_document` decodes internally, which
   is why the first-commit verification passed).
4. Worker foundation surface (USAGE on `agentcow` + EXECUTE on the 13
   `FOUNDATION_REVIEWER_FUNCTIONS`) granted in
   `apply_product_privileges` HARDENED re-application instead of
   migration `072_001`: the `agentcow` schema does not exist at
   migration time (`deploy_cow_functions` runs during bootstrap
   reconcile after the Alembic head); the product privilege roles are
   NOINHERIT, so the transitive worker -> reviewer membership carries
   no effective authority and `SET ROLE` is infeasible; the direct
   grant to `slaif_review_worker` is the same documented deviation
   class as the owner ADMIN edge (migration docstring item 7).
5. `USAGE ON SEQUENCE control.cache_outbox_id_seq TO
   slaif_review_worker` (migration upgrade + downgrade + manifest):
   the `cache_outbox` id is BIGSERIAL and the worker INSERT needs the
   sequence; proven required by the 42501 `permission denied for
   sequence cache_outbox_id_seq` on the first un-granted run.
6. Enqueue signature `control.slaif_workspace_accept(uuid, uuid)`
   (workspace + actor) vs the order's 1-argument prose: the actor is
   carried in the job payload because the `audit.promotion` row records
   the acting human account (R3 audit-field exactness).
7. Accept confirmation dialog rendered with `CspModal` (Radix
   `modal=false`) instead of a modal Radix Dialog: the modal variant's
   inline-styled focus guards violate the strict `style-src 'self'`
   CSP (each `el.style.x = ...` is blocked and console-logged); the
   non-modal CspModal is the app's established CSP-safe dialog
   (site switcher, membership) and preserves the required
   acknowledgement semantics (ack resets on every open, exact text
   pins unchanged).
8. Roster hermeticity fixes (I2): the accept-lifecycle proof runs on
   a dedicated run-unique site, and two pre-existing positional
   site selections (`media-publication.spec.ts` first-non-parity;
   `smoke.sh` media stage first element) were made explicit
   `site_key === "demo"` — run-unique fixture sites sort before
   `demo` in `/me/sites` for platform administrators and would have
   been picked as the cross-site/media target (the fixture sites
   have no human workspace -> uniform 404). No product behavior
   changed; `public_agent_acceptance.py`'s first-non-demo "other"
   selection was audited and is read-only (workspace-list equality +
   cross-site 404 probe), so it needed no change.
9. The `slaif_reviewer -> slaif_review_worker` edge is re-established
   by `provision_database_roles` (I2) in addition to the `072_001`
   migration grant: `docker compose start nginx` re-executes the
   one-shot bootstrap (compose re-runs `service_completed_successfully`
   one-shot dependencies), and `provision_database_roles`' REVOKE loop
   drops every privilege-role membership; without the re-grant, every
   bootstrap re-run left the worker without its inherited reviewer
   privileges and the reconcile validation failed (see Compose smoke
   section, root cause 3). The `072_001` migration and its downgrade
   are unchanged.

## Acceptance-criteria evidence

All local runs used the disposable local PostgreSQL 16
(`127.0.0.1:5432`, fake credentials) with `uv 0.12.5`; system
PostgreSQL was stopped for the whole session and restored at the end.

### Criterion 1 (072_001 up/down clean; R1 privilege gate)

- `test_database_bootstrap` (integration): full fresh upgrade from an
  empty cluster to `072_001` then downgrade back to `071_001` and
  re-upgrade (round trip, exact drop/revoke/restore set) — passed in
  the full run below; the bootstrap downgrade-compatibility revision
  set now includes `072_001` (`bootstrap/service.py` one line).
- All new/changed functions are `SECURITY DEFINER` with
  `search_path = pg_catalog`, owner `slaif_owner`, PUBLIC revoked,
  exact grant pins: verified by `test_reviewer_grant_matrix` (grant
  matrix query output in Criterion 2) and the manifest reconciliation
  inside `apply_product_privileges` (any drift -> HARDENED refuses).

### Criterion 2 (grant matrix proven by query)

- `test_reviewer_grant_matrix` (integration, real PostgreSQL):
  `rolname` member scan — `slaif_review_worker` is the ONLY member of
  `slaif_reviewer` (no other long-lived role/login); the owner ADMIN
  edge is the only setup-only membership.
  - `audit.promotion` / `control.cache_outbox`: PUBLIC revoked;
    exact holder sets as granted in `072_001` (INSERT worker; SELECT
    reviewer on promotion; INSERT,SELECT worker on outbox).
  - agentcow: USAGE holders = `{slaif_owner, slaif_reviewer,
    slaif_review_worker}`; per-function EXECUTE holders the same set
    for all 13 `FOUNDATION_REVIEWER_FUNCTIONS` (the mirror surface,
    deviation 4).
  - `has_sequence_privilege('slaif_review_worker', 'control.
    cache_outbox_id_seq', 'USAGE')` = true; every other long-lived
    role = false (the (False, False, True) manifest carve-out).
  - worker effective surface: the 5 functions the success path calls
    (`get_cow_session_operations`, `get_cow_dependencies`,
    `get_cow_conflicts`, `_cow_lock_session`, `commit_cow`) + pure
    `pg_catalog` (`get_table_pk_cols_sql` via `get_cow_primary_key_
    columns`, `get_context`).
- Output (exact query results) recorded in the full integration run
  log `/tmp/int-full-083a-final.log` (test PASSED; the manifest re-assertion runs on
  every test-database reconcile in the suite).

### Criterion 3 (kind-aware claim)

- `test_kind_aware_claim_and_stale_recovery`: `ARRAY['FREEZE','ACCEPT']`
  claims both kinds FIFO by (created_at, id); a pre-seeded `DISCARD`
  job is NEVER claimed by the worker kind array; an invalid kind array
  (`ARRAY['BOGUS']` / wrong type) is rejected at the function layer;
  the stale-claim recovery block is byte-identical to 070_001 and the
  stale-recovery fixture behaves unchanged (stale CLAIMED re-queued
  under the attempt budget).

### Criterion 4 (enqueue idempotency + stable codes, DB AND route)

- `test_accept_enqueue_idempotency_and_stable_codes`: first enqueue ->
  job row (payload exact: workspace/site/actor/snapshot/digest/
  versions/media_manifest); second call -> SAME job id returned
  unchanged (idempotent before the status gate); `WORKSPACE_NOT_IN_
  REVIEW` for ACTIVE / ACCEPTED / CONFLICTED workspaces;
  `REVIEW_SNAPSHOT_NOT_FOUND` for missing snapshot and for non-
  COMPLETE snapshot; `WORKSPACE_NOT_FOUND` for a foreign/missing
  workspace id.
- Route class: the same stable codes surface through
  `POST .../accept/` as uniform 404 (all not-found/mismatch cases,
  pairwise indistinguishable — the 404-indistinguishability asserts
  compare the full error envelope minus the per-request
  `request_id`/`operation_id` correlation fields, so bad_snapshot
  vs bad_digest vs binding-failure bodies are byte-identical) and the
  409 class (WORKSPACE_NOT_IN_REVIEW only).

### Criterion 5 (route authority matrix)

- `test_control_accept_route_authority_matrix`: both permissions
  required (each individually missing -> uniform denial, no oracle);
  `recent_auth` absent -> 401 class (the route refuses without the
  fresh auth); CSRF/state-changing policy enforced (non-GET verbs on
  the review path 405; the accept POST requires the CSRF gate);
  wrong site binding -> uniform 404; snapshot id mismatch and digest
  mismatch -> uniform 404 pairwise indistinguishable from not-found;
  `acknowledge_summary` false / missing / JSON `1` -> strict body
  rejection (422 class at the body layer, no row, no side effect);
  agent capability token on the control accept route -> uniform
  denial (no accept surface exists for agent credentials; the Agent
  route policy / OpenAPI are byte-unchanged, R8).

### Criterion 6 (worker success path end to end)

- `test_accept_worker_success_path` (integration, real PostgreSQL +
  foundation 0.2.0 + real 0700 media root): freeze -> enqueue ->
  claim (`['FREEZE','ACCEPT']`) -> `run_accept_job` SUCCEEDED:
  - canonical revision +1 (0 -> 1) in the single reviewer
    transaction; fault-injection property proven separately in the
    retry test (no partial state);
  - `audit.promotion` row fields exact (one row; workspace/site/
    snapshot/digest/actor/result as granted);
  - `control.cache_outbox` row present (`event_kind =
    'WORKSPACE_ACCEPTED'`, payload `media_manifest` exact);
  - workspace `ACCEPTED` + `accepted_at` set; job `SUCCEEDED`,
    error NULL;
  - media public: the published bytes re-hash to the digest
    (`sha256(public bytes) == digest`), the public path
    `public/sha256/xx/yy/<digest>` exists, `published_at` set,
    `public_status = 'public'`; manifest == published set (exactly
    one object).
  - advisory lock: the reviewer transaction holds
    `pg_advisory_xact_lock(hashtextextended(<workspace lifecycle key>,
    280))` — the same key 280 usage the freeze worker already uses
    (one workspace lifecycle key per workspace).

### Criterion 7 (drift path)

- `test_accept_worker_drift_zero_mutation`: the site canonical
  revision is bumped (test authority) between enqueue and the worker
  run -> `SITE_REVISION_CHANGED` BEFORE any mutation; zero mutation
  proven by exact row counts + revision unchanged (COW change tables,
  `audit.promotion`, `control.cache_outbox` all empty; media private
  state untouched); workspace back to `REVIEW`; the COMPLETE snapshot
  intact. E2E rendering: the accept-lifecycle drift test (manual
  revision bump via test authority, re-freeze) asserts the accept
  control ABSENT + re-review message on the admin page.

### Criterion 8 (conflict path)

- `test_accept_worker_conflict_full_rollback`: a pre-seeded
  conflicting canonical row (the snapshot's base row changed outside
  the COW session) -> the foundation raises `CowConflictError` with
  the structured `BASE_ROW_CHANGED` code inside the reviewer
  transaction -> FULL rollback: no partial state (COW change tables +
  `audit.promotion` + `control.cache_outbox` all empty, canonical
  revision unchanged); workspace `CONFLICTED`; snapshot intact; job
  terminal FAILED with the structured code.

### Criterion 9 (retry/budget)

- `test_accept_worker_retryable_rollback_and_budget`: a failure
  inside the reviewer transaction rolls back (retryable), and the
  stale-claim recovery path exhausts the attempt budget (3) ->
  workspace `REVIEW` + job code `REVIEW_JOB_STALE_AT_BUDGET` (no dead
  end).
- `test_accept_worker_crash_replay_idempotent`: the fixture simulates
  the real crash window (the claimed worker marks PROMOTING,
  finalizes the media — public bytes exist, canonical media row
  public — then dies before the promotion transaction, no terminal);
  stale-claim recovery re-queues; the replay (attempt 2) re-validates
  (the private -> public media flip is the idempotent signature) and
  commits EXACTLY once: one `audit.promotion` row, one
  `control.cache_outbox` row, revision +1 once (== 1), workspace
  `ACCEPTED`, job `SUCCEEDED`, identical public state (bytes re-hash
  to the digest; exactly one object in the public directory; the
  replay added nothing new).

### Criterion 10 (R4: accept control per state, 3 viewports)

- E2E `review-surface` (updated): the admin review page is driven at
  the three viewports (desktop 1280x800, tablet 820x1180, mobile
  375x667) through public NGINX; the accept button count is pinned to
  exactly 1 (REVIEW + COMPLETE + no drift), `discard|publish` count 0,
  no Puck affordances (grep-pinned in the component + DOM-pinned in
  E2E).
- E2E `accept-lifecycle` positive: confirmation dialog requires the
  acknowledgement; typed confirmation with the digest from the read
  model; terminal state rendered (QUEUED after 202; ACCEPTED after
  worker completion); keyboard-accessible (role/label-driven
  interactions, the established admin pattern).
- Terminal-state rendering: `test_control_accept_route_authority_
  matrix` + E2E pin the 409 terminal behavior (duplicate accept on a
  live job -> idempotent 202 SAME job id; on ACCEPTED -> the
  terminal-state 409 class per R2.4, pinned once).

### Criterion 11 (R5 durable form; adversarial grep)

- The four surfaces updated in commit D (DRAFT: see the Documentation
  section) with verified immutable merge facts only (082/2 accepted
  and merged in PR #98 at
  `f754e075364b56571307a41abc4b9dcf3f6f6af0` on 2026-10-05) and the
  standard in-flight form for 083/1 at `083-a` (branch
  `oap/083-a-real-accept`, base `f754e07`).
- Adversarial grep at the report head:
  `grep -n 'in flight at 082-2-a|this PR is open|pending strategic
  merge' README.md oap/INCREMENTS.md oap/MVP-PROGRESS.md
  oap/MVP-CONTRACT-AUDIT.md` -> no matches (verified 2026-10-05).
- Contractual MVP NOT COMPLETE: the audit verdict is unchanged; the
  promotion path (real accept) is the increment in flight.

### Criterion 12 (R6 byte-identity)

- `git diff f754e075364b56571307a41abc4b9dcf3f6f6af0..HEAD --
  contracts/ packages/`: empty (0 lines, verified at drafting AND
  re-verified on the final tree before S).
- Agent OpenAPI 47-path strip-identity re-proven at BOTH base and
  head (canonical JSON after removing every `x-slaif-*` key, sorted
  keys, compact separators): sha256 base
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83` =
  sha256 head `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
  (47 paths at base and head; the raw files are byte-identical).
- Generator gates zero-diff: `uv run --frozen python -m
  tools.contracts.generate_agent_openapi --check` PASSED; `python
  tools/generate_component_catalog.py --check` PASSED; `python
  tools/generate_design_system.py --check` PASSED (final tree).

### Criterion 13 (budgets honest; trigger; CLOSURE_ONLY; full CI)

- Budget table above: measured honestly base->head, grouped; the
  20-prod/config-file trigger reported NOT FIRED (19 < 20);
  CLOSURE_ONLY never entered; every variance itemized and classed
  (deviations 1-9).
- Full CI roster (20 checks) terminal and green at the exact report
  head I2 `8d4a79b8f51472da58e9a959b0afb529bd442708`: CI run
  37377010413 completed/success (2026-10-05T21:36:56Z -> 22:08:55Z,
  15/15 CI-workflow jobs) + CodeQL run 37377010529 completed/success
  (2026-10-05T21:36:56Z -> 21:39:07Z, 4/4 checks); the single failed
  first attempt of `Compose and edge packaging` (one device-variant
  WebKit timeout flake) was re-run unchanged at the same head and
  passed (details in the GitHub CI section).

## Local verification

Exact commands and outcomes (repo root, final tree; uv 0.12.5, Node
v24.14.1, pnpm 11.22.0, TypeScript 6.0.3):

```text
uv lock --check: PASSED (Resolved 45 packages in 1ms)
uv sync --frozen --all-groups: PASSED (Checked 44 packages in 0.76ms)
uv run --frozen ruff check services/backend tests/repository tools: PASSED (All checks passed!)
uv run --frozen ruff format --check services/backend tests/repository tools: PASSED (all files already formatted)
uv run --frozen mypy: PASSED (Success: no issues found)
uv run --frozen pytest services/backend/tests/unit tests/repository -q: PASSED (788 passed, 26 subtests passed)
uv run --frozen pytest services/backend/tests/integration -q: see the run history below (first full run 255 passed / 4 failed in 3519.91s — all four deterministic test-pin bugs, fixed; final full clean run on the FINAL tree (incl. I2): 259 passed in 3544.35s, 0 failed)
uv build --out-dir /tmp/slaif-agent-site-distributions: PASSED (sdist + wheel)
node --version / pnpm --version: v24.14.1 / 11.22.0
pnpm install --frozen-lockfile: PASSED (already up to date)
pnpm lint: PASSED (root eslint --max-warnings 0 + web filter)
pnpm format:check: PASSED (all matched files use Prettier code style)
pnpm typecheck: PASSED (scope-catalog + apps/web + services/browser-worker)
pnpm test: PASSED (browser-worker vitest fail 0; RUN v4.1.10: 3 test files, 33 tests passed)
pnpm build: PASSED (Next.js: /health/ready /login /preview/[workspaceId] /review/[workspaceId] /setup + proxy middleware)
pnpm licenses list --json: PASSED (root 8 licenses; recursive workspace scan: no AGPL/SSPL/BUSL/BSL/Commons Clause/noncommercial strings)
python -m slaif_agent_site.{control_api,editor_api,agent_api,render_api,mcp_adapter,media_service,review_worker,scheduler,media_gc,bootstrap} --check: PASSED (10/10 OK, via uv run --frozen python)
python -m compileall -q tools tests/repository: PASSED
python -m unittest discover -s tests/repository -p 'test_*.py': PASSED
python tools/check_repository.py: PASSED (PASS repository policy)
python tools/check_mermaid.py: PASSED (16 diagrams; 527 Markdown files scanned)
npx --yes markdownlint-cli2@0.23.2 "**/*.md": PASSED (0 issues in 521 files, final tree)
uv run --frozen python -m tools.contracts.generate_agent_openapi --check: PASSED (zero-diff)
python tools/generate_component_catalog.py --check: PASSED (zero-diff)
python tools/generate_design_system.py --check: PASSED (zero-diff)
```

Local full-run history (honest):

- First full run (final tree, disposable PostgreSQL 16): `4 failed,
  255 passed in 3519.91s (0:58:39)`. All four failures were
  deterministic test-pin bugs in this PR's mechanical updates (no
  product code involved):
  1. `test_freeze_review_snapshot.py` (3 tests): the
     `slaif_review_job_claim($1, $2)` call sites passed the claimant
     argument twice (3 arguments for 2 placeholders ->
     asyncpg InterfaceError). Fixed by removing the duplicated
     claimant at all four call sites.
  2. `test_browser_run_control_plane.py`
     (1 test, exact-privilege negative matrix): still pinned the
     retired 1-argument `control.slaif_workspace_accept(NULL::uuid)`
     signature (UndefinedFunctionError). Fixed by pinning the rebuilt
     2-argument signature `control.slaif_workspace_accept(NULL::uuid,
     NULL::uuid)`.
  - Verified fix: the 6 `test_freeze_review_snapshot.py` tests + the
    browser exact-privileges test + the timing-sensitive
    `test_agent_theme_boundaries.py` barrier test re-ran green
    (7 passed in 101.19s).
- Final full run on the final tree (after the pin fixes), disposable
  local PostgreSQL 16: `2 failed, 257 passed in 3572.65s (0:59:32)`.
  The two failures are pre-existing tests not touched by this PR
  (neither file is in the PR's mechanical-pin set for that test):
  `test_agent_mutations.py::test_agent_content_item_crud_is_strict_
  idempotent_and_tombstoned` and
  `test_site_control_http_integration.py::test_site_http_authentication_
  csrf_administrator_and_failure_contract`, both raising
  `HumanSessionError: Human session unavailable` while the 40-minute
  compose smoke ran in parallel on the same VM (the first full run,
  also under stack load, passed both). Flake-class re-run, no parallel
  load: the same two tests alone — `2 passed in 28.30s` (log
  `/tmp/int-flake-rerun-083a.log`). With that re-run, the full
  integration suite is green on the final tree.
- FINAL full integration run on the FINAL tree (after I2), disposable
  local PostgreSQL 16: `259 passed in 3544.35s (0:59:04)`, 0 failed —
  includes `test_database_bootstrap.py` with the updated two-edge
  role-manifest assertion and `test_real_human_accept.py` (10/10).
  (Ran partially in parallel with the early stages of the final
  compose smoke; the suite is DB-isolated from the compose stack.)

Target file (the 10 acceptance-criteria tests), final tree:

```text
uv run --frozen pytest services/backend/tests/integration/test_real_human_accept.py -v: 10 passed in 122.73s
  test_reviewer_grant_matrix PASSED
  test_kind_aware_claim_and_stale_recovery PASSED
  test_accept_enqueue_idempotency_and_stable_codes PASSED
  test_control_accept_route_authority_matrix PASSED
  test_accept_worker_success_path PASSED
  test_accept_worker_drift_zero_mutation PASSED
  test_accept_worker_conflict_full_rollback PASSED
  test_accept_worker_retryable_rollback_and_budget PASSED
  test_accept_worker_crash_replay_idempotent PASSED
  test_promote_workspace_retired PASSED
```

## Compose smoke

Development iteration (honest): the `accept-lifecycle` E2E was first
debugged on a reused disposable stack (several accepted workspaces
from earlier iterations). That iteration proved and fixed three
spec-side issues (agent API body has no `order_key`; the workspace
preset needs `L2_SITE_EDITOR` for the structure scope; the terminal
render matches the exact accept text) and one product-side issue:
the confirmation dialog was a modal Radix Dialog whose inline-styled
focus guards the strict `style-src 'self'` CSP blocks (proven by the
E2E strict-console observer); it now uses the app's established
`CspModal` pattern (deviation 7). The debug stack was then torn down
because an accidental bootstrap re-run on the already-bootstrapped
stack is one-shot by design (setup token cannot be re-issued; exit 1)
and its idempotent role re-provisioning (pre-existing: it revokes all
non-login privilege edges) left the 072 worker -> reviewer edge
un-restored, so the debug stack could no longer run the accept path.
No final evidence was taken on the dirty stack.

Final runs: fresh disposable stack per run, public NGINX, real
PostgreSQL 18, `uv`/`pnpm` frozen.

Run 1 (`sh tools/compose/smoke.sh slaif007accept083`, fresh
stack; the first full integration suite ran in parallel on a
separate disposable PostgreSQL 16): all compose stages green
through the full 18-project browser roster, incl. the new
project:

```text
review-worker-media-boundary: OK dsn=0400:uid10001 root=0700:uid10001
browser-e2e: PASSED project=review-surface contract=review-surface-review-render-and-summary stage=unknown
browser-e2e: PASSED project=review-surface contract=review-surface-fail-closed-negatives stage=unknown
browser-e2e: PASSED project=accept-lifecycle contract=positive: content+media workspace freezes, accepts end to end, publishes once stage=unknown
browser-e2e: PASSED project=accept-lifecycle contract=negative: digest mismatch and agent capability are uniform denials; drift removes the control stage=unknown
browser-e2e: PASSED project=media-publication contract=media-publication-core-human-agent-preview-finalize-public-hostile stage=unknown
compose-e2e: OK projects=18 setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2 agent-workspace-puck=2 freeze-review-snapshot=1 review-surface=1 accept-lifecycle=1 media-publication=1 artifacts=disabled
public-agent-acceptance: FAILED reason=theme-browser-failed-request-summary
```

Root cause 1 (test-fixture pollution; product behavior correct):
the accept-lifecycle proof published an Image component
(referencing public media) to the CANONICAL DEMO HOME. The later
pre-existing `tools/compose/public_agent_acceptance.py` theme
browser proof creates a fresh workspace from that canonical and
its browser run on `/preview/<ws>/s/demo` rendered
`<img src="/media/v1/sites/...">`; the browser-worker URL policy
(`services/browser-worker/src/url-policy.ts`, unchanged in this
PR) allows only `/_next/static/`, `/_next/image`,
`/renderer-v1.css`, `/slaif-logo.svg` plus the first document, so
the media request was blocked and the stage's
`failed-request-summary` expectation
(`{"blocked": 0, "entries": []}`) failed. The stage expectation
was NOT weakened.

Run 2 (fresh stack, no parallel load): same deterministic
`theme-browser-failed-request-summary` failure (parallel load
ruled out).

Fix attempt 1: move the proof content to a run-unique dedicated
PAGE on demo (agent `page:create`). The accept-lifecycle positive
then timed out (300 s): the ACCEPT job failed all 3 attempts ->
`REVIEW_JOB_STALE_AT_BUDGET`.

Root cause 2 (FOUNDATION BUG, out of scope this round; flagged in
Known limitations): `agent-cow-postgresql==0.2.0`
`agentcow.get_cow_dependencies`
(`agentcow/postgres/cow_sql_functions.py`) decomposes composite
foreign keys as a cartesian cross-product of column pairs without
ordinal matching; `page_base (site_id, locale) ->
site_locale_base (site_id, tag)` yields the bogus predicate
`site_id (uuid) = locale (text)` ->
`asyncpg.exceptions.UndefinedFunctionError: operator does not
exist: uuid = text`. It triggers iff the COW session carries page
DML (`page_changes` dirty); composition-only sessions are
unaffected. Reproduced with a traceback on the disposable stack
(`docker exec` + a repro script invoking the foundation function
on the seeded page rows). The order's L304-306 mandates the
foundation `dependencies(session_id)` closure check in the accept
job, so the call cannot be dropped; the foundation is pinned at
0.2.0 (R8: no dependency/lockfile changes), so it cannot be fixed
upstream this round.

Final fix (I2, dedicated-site design): the proof runs on a
DEDICATED RUN-UNIQUE SITE (`acceptproof-<8hex>`, seeded by the
spec via test-authority psql exactly like the e2e.sh parity
fixture: `control.site` + `SITE_OWNER` membership +
`content.site_locale_base` + a PUBLISHED `home`
`content.page_base` with empty composition). The agent performs
composition-only operations on the pre-seeded home (no page DML),
so the session never carries `page_changes` and the foundation
closure check stays on clean composition tables. Isolation: the
canonical demo home is untouched (the theme browser proof is green
again) and the parity fixture is untouched (media-publication
green).

Run 3 (fresh stack): accept-lifecycle positive+negative PASSED;
media-publication FAILED (`Expected: 201 / Received: 404` on the
human media upload).
Root cause 4a (roster hermeticity, spec-side): the spec's
cross-site target selection was positional
(`sites.find(site_key !== "parity")`, intended demo); `/me/sites`
lists every site for platform administrators ordered by site_key,
and the run-unique `acceptproof-*` site sorts before `demo` and
has no human workspace (the human media upload requires one) ->
uniform 404. Fix (I2): explicit `site_key === "demo"` selection
(one line + comment, matching every other consumer in the
roster).

Run 4 (fresh stack, no load): ALL 18 e2e projects PASSED (incl.
accept-lifecycle + media-publication) and the pre-existing theme
browser proof PASSED (root cause 1 fixed); then
`public-agent-acceptance: FAILED reason=compose-start-nginx-
failed` — the first run to reach the nginx-outage scenario this
round (r1/r2 and the D-head CI failed earlier at the theme stage;
base-main CI at the T head had passed it).

Root cause 3 (deterministic; reproduced and fixed): `docker
compose start nginx` re-executes the one-shot `bootstrap` service
(compose 2.40.3 re-runs `service_completed_successfully` one-shot
dependencies when starting a dependent). On an initialized
installation the bootstrap re-run failed:
`provision_database_roles` revokes ALL privilege-role membership
edges (the REVOKE loop) and re-establishes only the static login
edges + the owner's ADMIN-option reviewer edge; the
`slaif_reviewer -> slaif_review_worker` edge existed ONLY in the
one-shot `072_001` migration, so every re-provision dropped it and
`reconcile`'s HARDENED privilege validation failed (worker lost
the inherited reviewer SELECT on `audit.promotion`, content-view
SELECTs and content-schema USAGE) -> bootstrap exit 1 -> nginx
would not start. Traceback captured by invoking
`compose_bootstrap` directly in a container (the safe-failure
boundary hides details by design): `BootstrapStateError: database
privilege validation failed:
relation/audit.promotion/slaif_review_worker/effective-dml:insert;
... schema/content/slaif_review_worker/missing-usage`.

Fix (I2, bootstrap re-run convergence):
`provision_database_roles` now re-establishes
`GRANT slaif_reviewer TO slaif_review_worker` after the REVOKE
loop (same provisioning-invariant pattern as the owner's
ADMIN-option edge), so re-provisioning converges; the `072_001`
migration keeps its idempotent GRANT (unchanged). The
`verify_database_privileges` contract comment and the role-manifest
integration assertion were updated to the two-edge invariant.
Verified on the initialized disposable stack: bootstrap re-run
converges (`compose-bootstrap: OK revision=072_001
state=HARDENED safe=true`), a manual `docker compose stop nginx` +
`start nginx` cycle exits 0, and standalone
`python tools/compose/public_agent_acceptance.py --project
slaif007accept083` -> `public-agent-acceptance: OK ...
restart=verified nginx-outage=verified ...` (exit 0).

Run 5 (fresh stack, no load): ALL 18 e2e projects PASSED and
`public-agent-acceptance: OK ... restart=verified nginx-outage=
verified ...` (root causes 1, 3 and 4a fixed); then the smoke
media stage failed with no success marker (exit 1).
Root cause 4b (roster hermeticity, smoke.sh-side): the stage
selected the first element of `/me/sites`
(`json.load(...)[0]`, intended demo), i.e. the run-unique
`acceptproof-*` site (sorted before `demo`); the human media
upload on that site 404s (no human workspace), so the stage's
`test "$media_upload_status" = 201` assertion failed and the
script aborted silently under `set -e` (no marker, no product log
line). Fix (I2): explicit `site_key == "demo"` selection
(2 lines + comment), matching every other consumer.

Run 6 (FINAL; fresh stack, clean un-instrumented image): executed
on the exact working tree committed as I2 (working tree verified
clean at commit time; the run completed 35 s before the commit and
nothing was modified in between; the FINAL full integration
suite's tail overlapped its early stages on the same VM — load
benign, the suite is DB-isolated to a separate disposable
PostgreSQL 16 container). FULLY GREEN:

```text
compose-e2e: OK projects=18 setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2 agent-workspace-puck=2 freeze-review-snapshot=1 review-surface=1 accept-lifecycle=1 media-publication=1 artifacts=disabled
public-agent-acceptance: OK workspace=22d01533-1240-4c6b-88f9-8b2c5a1d252f types=2 fields=3 items=2 translations=1 relations=1 views=1 pages=1 components=1 locales=1 redirects=1 navigations=1 navigation-items=3 theme=schema-default-patch-read-replay openapi=exact restart=verified nginx-outage=verified crud=public quotas=mutation-429,max-delete-429 dependency-delete=422 page-delete-restore=verified canonical-independence=verified render-restart=verified
media-e2e: OK edge=nginx upload=validated-private-read=byte-identical finalization=public-read=byte-identical immutable-cache=verified
render-locator-failure: correctly blocked render=unhealthy web=503 nginx=unhealthy
render-locator-recovery: restored render=healthy web=healthy nginx=healthy
negative-bootstrap: correctly blocked
compose-smoke: OK
SMOKE_EXIT=0
```

Baseline-relative: the review-worker container carries the media
DSN file (0400:uid10001) and the media root (0700:uid10001); no
content is printed; worker readiness unchanged.

## GitHub CI / required checks

Exact 20-check roster: the 15 `CI`-workflow jobs plus the `CodeQL`
workflow's `CodeQL`, `Analyze (actions)`,
`Analyze (javascript-typescript)`, `Analyze (python)`, and `Detect
supported languages` checks.

- State observed for transcript head T
  `24f93317296c8d9361a30cdc41e8858036d775cb` (pushed at activation;
  CI run 37292113037 completed/success, 2026-10-05T09:45:13Z ->
  10:00:16Z + CodeQL run 37292112921 completed/success,
  2026-10-05T09:45:13Z -> 09:46:40Z): 20/20 SUCCESS
  (transcript-only commit: exact order + active bytes).
- State observed for docs head D
  `2dc77334a36d59b0ba333992e366d26a0fd9b9dc` (CI run 37353914285
  completed/FAILURE, 2026-10-05T18:10:12Z -> 18:24:57Z + CodeQL run
  37353913771 completed/success, 2026-10-05T18:10:12Z -> 18:12:03Z):
  18/20 SUCCESS, 2 FAILURE — `Compose and edge packaging`: FAILED
  at the public-agent-acceptance stage
  (`public-agent-acceptance: FAILED reason=theme-browser-failed-
  request-summary`, root cause 1, fixed in I2); `Repository
  policy`: FAILED packaging-contract pin
  (`test_compose_smoke_contract.py::test_governance_project_orders_
  all_six_stable_devices`: `dependencies: ["governance"]` count
  13 != pinned 12 — the new accept-lifecycle project; pin and
  device-project name list updated in I2). All Foundation
  PostgreSQL 14-18, Python 3.12/3.13/3.14 quality and package, Node
  contracts, Markdown, Mermaid, Dependency review and Supply-chain
  evidence jobs and all 4 CodeQL checks SUCCESS.
- Commit I `d18b17809fa4b0591231eb0d2d277e3579e67f12` was pushed in
  the same push as D (no separate CI run at head I; the branch run
  list contains exactly the T-head and D-head runs before I2).
- State observed for implementation head I2
  `8d4a79b8f51472da58e9a959b0afb529bd442708` (CI run 37377010413
  completed/success, 2026-10-05T21:36:56Z -> 22:08:55Z + CodeQL run
  37377010529 completed/success, 2026-10-05T21:36:56Z -> 21:39:07Z):
  all 20 checks SUCCESS — `Analyze (actions)`: SUCCESS, `Analyze
  (javascript-typescript)`: SUCCESS, `Analyze (python)`: SUCCESS,
  `CodeQL`: SUCCESS, `Compose and edge packaging`: SUCCESS,
  `Dependency review`: SUCCESS, `Detect supported languages`:
  SUCCESS, `Foundation PostgreSQL 14`: SUCCESS, `Foundation
  PostgreSQL 15`: SUCCESS, `Foundation PostgreSQL 16`: SUCCESS,
  `Foundation PostgreSQL 17`: SUCCESS, `Foundation PostgreSQL 18`:
  SUCCESS, `Markdown`: SUCCESS, `Mermaid`: SUCCESS, `Node contracts`:
  SUCCESS, `Python 3.12 quality and package`: SUCCESS, `Python 3.13
  quality and package`: SUCCESS, `Python 3.14 quality and package`:
  SUCCESS, `Repository policy`: SUCCESS, `Supply-chain evidence`:
  SUCCESS — no FAILURE/CANCELLED/PENDING remaining. The first
  attempt of `Compose and edge packaging` failed on a single
  device-variant timeout: `browser-e2e: FAILED project=desktop-webkit
  contract=responsive-admin-keyboard-read-states-and-logout
  stage=site-overview-read detail=Test timeout of 30000ms exceeded`,
  while the same contract PASSED on the other five stable device
  variants (desktop-chromium, desktop-firefox, tablet,
  mobile-chromium, mobile-webkit) in the same attempt and on the full
  local matrix (compose smoke run 6); the failed attempt was re-run
  unchanged at head I2 after the run completed (no push change) and
  PASSED.
- All required green at drafting: yes (I2: 20/20 terminal SUCCESS,
  no FAILURE/CANCELLED/PENDING).
- Report-only commit (SELF) may trigger fresh checks at the report
  head; strategy independently waits/verifies SELF per the
  protocol.

## Local setup / dependencies

- Disposable VM (passwordless sudo) per the constitution; system
  PostgreSQL STOPPED for the whole session, restored at the end
  (`sudo systemctl start postgresql`); all test databases on the
  disposable local PostgreSQL 16 container (`127.0.0.1:5432`, fake
  credentials — the six adapter config classes accept TEST-mode DSN
  ports in {None, 5432}).
- uv 0.12.5 (editable install — source edits live), pnpm 11.22.0,
  Node v24.14.1, TypeScript 6.0.3, asyncpg 0.31.0 (jsonb -> str, see
  deviation 3), agent-cow-postgresql 0.2.0 (public API only).
- Media roots 0700; fake credentials only; no production system,
  credential, or unrelated host file touched.

## Documentation

- R5: the four current-truth surfaces updated in commit D (exact
  changes in the Changes-made item 10); adversarial grep clean at the
  report head; contractual MVP NOT COMPLETE (verdict unchanged).
- Durable in-code docs: the migration docstring (7 numbered items,
  incl. the NOT-granted-here foundation rationale + NOINHERIT), the
  `accept_job` module docstring (the full job sequence + terminal
  failure classes), the `roles.py` provisioning-edge comment, the
  compose wiring comment (mounted-secret pattern), and the
  `promotion.py` retirement docstring.

## Safety and scope confirmations

- R8 zero Agent-facing accept path: the Agent route policy, OpenAPI,
  and capability catalog are byte-unchanged (R6 diff empty +
  strip-identity re-proven); the accept surface exists only on the
  human Control boundary with the dual-permission + recent-auth gate.
- No discard implementation, no selective accept, no outbox consumer,
  no anonymous public-media behavior change (the outbox has no
  consumer in this increment; the anonymous public read path is
  untouched).
- No freeze/snapshot/renderer/Puck behavior change (the 082/1 and
  082/2 code paths are unchanged except the shared `_mark_terminal`
  helper extraction pinned by the unchanged freeze suite).
- No dependabot incorporation; `git diff base..head --
  services/backend/uv.lock pnpm-lock.yaml .github/ supply-chain/`
  empty (no lockfile, CI-workflow, or supply-chain file changes); no
  new dependencies (Python direct runtime deps unchanged; the web
  work reuses existing imports).
- Secrets: no secrets in code/docs/tests; the worker media wiring uses
  the established mounted-secret pattern only (`SLAIF_MEDIA_DSN_FILE`
  -> `/run/slaif-media/media-dsn` 0400:uid10001, volume-mounted; the
  smoke asserts mode/ownership and prints no content).
- No merge, no auto-merge, no PR close by the executor; one objective
  PR (#99); no second-objective PR; `oap/orders/083-a-real-accept.md`
  and `oap/active` bytes committed unchanged with the implementation
  (verified: `git diff T..I -- oap/orders/083-a-real-accept.md
  oap/active` empty).

## Known limitations / blockers

- The `control.cache_outbox` event has no consumer in this increment
  (083/3 scope): the row is durable and exact, but cache invalidation
  on accept is not wired.
- Discard and conflict-resolution product surfaces are 083/2 scope
  (the foundation `discard_cow` surface is already granted to the
  worker, ready for that increment).
- The drift-gate re-check happens under the locked site row inside
  the reviewer transaction (authoritative) and in the pre-locked
  verification transaction (early exit before media finalization); a
  revision bump between the two gates is caught by the in-transaction
  gate (zero mutation).
- E2E coverage of the accept lifecycle is Desktop-Chrome project
  based (roster pattern); the admin-page accept control is
  additionally pinned at the three viewports by the updated
  review-surface project.
- Foundation `agent-cow-postgresql==0.2.0` bug (upstream; out of
  scope for 083/1; flag for strategy):
  `agentcow.get_cow_dependencies` decomposes composite foreign keys
  as a cartesian cross-product of column pairs (no ordinal
  matching), so any COW session carrying page DML (create/update/
  delete) makes the accept job's order-mandated
  `dependencies(session_id)` closure check fail with `operator does
  not exist: uuid = text`; such workspaces currently stall at
  `REVIEW_JOB_STALE_AT_BUDGET` after the 3-attempt retry budget.
  Composition-only sessions on pre-existing pages are unaffected
  (this is how the 083/1 e2e proof is constructed).

## Recommended strategic follow-up

- 083/2 (discard): reuse the kind-aware claim + the already-granted
  `discard_cow` surface + the shared terminal-writing helper.
- 083/3 (outbox consumer + public media finalization consumer):
  consume `control.cache_outbox` `WORKSPACE_ACCEPTED` events for cache
  invalidation; public-namespace retention/GC remains the 079-excluded
  083-bound scope.
- After 083/1-083/3: 084 conflict-safe review lifecycle (immediately
  after 083 per the audit).

## Report publication convention

`Report publication commit: SELF` — this report-only commit changes
only `oap/reports/083-a-real-accept.md`; its first parent is the
literal implementation-head SHA (commit I2,
8d4a79b8f51472da58e9a959b0afb529bd442708); the remote PR head after
push is verified to be this SELF commit (`git ls-remote` +
`gh pr view 99 --json headRefOid`).

Report publication commit: SELF
