# OAP Work Order — 083-3-a: outbox consumer and public-surface
proof (083/3)

> **STATUS: ACTIVATED — operative order.** Published atomically by
> strategy 2026-10-06 to
> `oap/orders/083-3-a-cache-outbox-consumer.md` with `oap/active` =
> `083-3-a`, as a CREATE_NEW_PR round for semantic increment 3 of
> numeric Objective 083, from verified `main`
> `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c` (the 083/2 merge, PR #101).
> This is the final 083 increment of the human-approved 082/083
> pre-split ("Public surface + fault suite"). The coding agent executes
> under the normal OAP execution contract; strategy remains
> reviewer/acceptor/merger.

## 1. Identifier and mode

- ID: `083-3-a` (increment-qualified round ID: first round of semantic
  increment 3 of numeric Objective 083).
- Mode: CREATE_NEW_PR.
- Branch: `oap/083-3-a-cache-outbox-consumer`; base `main`.
- PR title (exact): `OAP 083-3-a: outbox consumer and public-surface
  proof (083/3)`.
- Do not create, amend, close, or touch any other PR (in particular the
  dependabot PRs #83/#94/#100: untouched).

## 2. Verified current state (strategy-verified 2026-10-06 against live
GitHub and read-only source at `214909f`)

- Remote `main` = `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c` (verified
  via `git ls-remote`); parents `22f38c783d062a9c5352f7bdde8607d9ac299f26`
  (pre-merge main) + `3c636356f29aa9a7b0956cd58dbc242087f2bd52` (accepted
  083/2 head). Post-merge main runs: CI 37414554303 and CodeQL
  37414554364, both `completed success`.
- PR #101 `OAP 083-2-a: real discard (conflict remedy) (083/2)` is
  MERGED; `mergedAt` = 2026-10-06T04:36:59Z; merge commit
  `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`.
- Open PRs: dependabot #83, #94, #100 only. No product PR open.
- `oap/active` = `083-2-b` (last activated round; protocol-correct idle).
- Migration head = `073_001_real_human_discard.py`; next number
  `074_001`.
- `control.cache_outbox` (072_001): columns `id BIGSERIAL`, `site_id`,
  `workspace_id`, `event_kind` (CHECK IN `('WORKSPACE_ACCEPTED')`),
  `payload JSONB`, `created_at`; NO consumed/attempt columns. Grants to
  `slaif_review_worker`: INSERT, SELECT + sequence USAGE.
- `review_worker/accept_job.py` (lines 562-575): inside the all-or-
  nothing reviewer transaction, one INSERT per accepted workspace with
  payload `{snapshot_id, digest, base_site_revision,
  new_canonical_revision, media_manifest}` (sort_keys, compact JSON).
  NO consumer exists anywhere in the codebase (verified by grep:
  zero read-side references to `cache_outbox` outside the INSERT and
  E2E psql assertions).
- `review_worker/worker.py` (line 99): claims
  `["FREEZE", "ACCEPT", "DISCARD"]` via `control.slaif_review_job_claim`
  with `FOR UPDATE SKIP LOCKED`; constants in `review_worker/config.py`
  (poll 1.0s, batch 1, heartbeat 20s, stale 60s, drain 30s, evidence
  120s; env-overridable `SLAIF_REVIEW_WORKER_*` pattern).
- Public media read ALREADY EXISTS end to end (merged 079/1, E2E-
  proven): anonymous route
  `GET /v1/public/sha256/{prefix1}/{prefix2}/{digest}` in
  `media_service/media_http.py` (line 134; content-addressed; malformed
  shape or non-public/absent digest -> 404 never 403;
  `Cache-Control: public, max-age=31536000, immutable`;
  digest-verified streaming via `open_public_verified`); nginx
  `location /media/public/` proxies to `slaif_media_service/v1/public/`
  (`infra/nginx/nginx.conf` line 155). `slaif_media_public_get(p_hash)`
  (068_001) is the content-addressed public lookup
  (`public_status = 'public'` only).
- The canonical-reference gate exists at FINALIZE time (merged 079/1):
  `slaif_media_public_mark` requires the review-context
  session/operation AND that the media is referenced by the accepted
  composition (`MEDIA_NOT_WORKSPACE_REFERENCED` otherwise). Architecture
  L150: media bytes are immutable/content-addressed; edits change
  references.
- `render_api/projection.py` (lines 678-714): canonical render mode
  emits the public URL `/media/public/sha256/{h[:2]}/{h[2:4]}/{h}` ONLY
  when `public_status = 'public'`; otherwise the bounded placeholder
  (no `<img>`). Preview mode uses the authenticated asset route.
- Public HTML caching: `render_api/site_http.py` lines 47 and 222 set
  `Cache-Control: private, no-store`; nginx has NO `proxy_cache`
  directive anywhere. Public media bytes cache long/immutable.
- Existing E2E pins (all green at `214909f`): `accept-lifecycle.spec.ts`
  pins exactly one `WORKSPACE_ACCEPTED` outbox row with the exact
  payload (digest, base/new revision, `media_manifest[].public_key`)
  plus the public fetch 200 with body re-hash to the digest;
  `discard-lifecycle.spec.ts` pins that discard performs NO finalization
  (workspace media stays `private`) and the public render is byte-
  identical before/after discard; `review-surface.spec.ts` line 844
  pins that the review render never contains `/media/public/`;
  `media-publication.spec.ts` pins the cross-site content-addressed
  public resolution (by design).
- Route-policy pins: 197 agent / 35 control
  (`services/backend/tests/unit/test_route_policy.py` lines 43, 58).
- E2E roster: 19 Playwright projects (`playwright.config.ts`).
- Architecture (normative compact): L556-559 acceptance step 6 "emit
  cache outbox", step 7 "finalize media idempotently; harmless
  precommit public orphan is GC'd"; L476-481 "Public immutable assets
  cache long; promotion increments site revision and emits cache
  invalidation"; L1131 "Cache outbox retries after canonical
  acceptance and temporary staleness is possible"; L619 worker "no
  listener"; L1128 "Multiple worker pools claim transactionally; only
  review worker has reviewer authority".

## 3. Strategic context

- Objective 083 (real human accept/discard promotion lifecycle) is
  human-approved as three increments: 083/1 accept (merged PR #99),
  083/2 discard (merged PR #101), 083/3 "Public surface + fault suite"
  (this order). After 083/3, numeric Objective 083 may be reclassified
  COMPLETE only after strategy independently verifies the resulting
  evidence; the next D5-path unit is 084 (conflict-safe lifecycle).
- 083/1 emits exactly one durable `WORKSPACE_ACCEPTED` outbox row inside
  the reviewer transaction, but nothing consumes it. The architecture
  requires the outbox to be RETRIED after canonical acceptance
  (L1131). This increment implements that consumer and proves the
  public surface it protects.
- Cache-honesty branch (pre-split option, chosen by strategy): the
  current deployment has NO public HTML cache (`private, no-store`;
  zero `proxy_cache` in nginx) and public media bytes are content-
  addressed and immutable. This order therefore PRESERVES + PROVES the
  current headers and makes the outbox consumer a durable
  verify-and-consume loop: in this deployment the invalidation action
  is an explicit no-op against the (nonexistent) edge cache, and the
  order does NOT pretend otherwise. If a public edge cache is added
  later, the same consumed/outbox contract is what it hooks into. No
  nginx change in this increment.
- Pre-split text reconciliation (strategy decision, flagged to the
  human in the final report): the 083/3 bullet "canonical-reference-
  gated ANONYMOUS public media reads" is already satisfied by the
  merged 079/1 design in the only form the architecture supports — the
  reference gate is at FINALIZE time (`slaif_media_public_mark`), and
  post-finalization reads are content-addressed and immutable
  (architecture L150). A fetch-time canonical-reference gate would
  regress merged, E2E-proven media semantics (cross-site resolution is
  by design per `media-publication.spec.ts`; the 083/2 discard spec
  explicitly pins that a content-addressed public-fetch 404 is not the
  leak policy) and is OUT OF SCOPE here. If the human wants fetch-time
  gating, that is a separate product decision and a separate increment.
  This order preserves and proves the current semantics.
- The 083/2 known limitation (discarded workspaces' private staging
  bytes are GC-reclaimable orphans; no cleanup in 083/2) carries over
  UNCHANGED: media GC is Objective 089 territory and is a non-goal here.

## 4. Bounded scope

Exactly six requirement groups (R1-R6), evidence (R7), and hard
constraints (R8). Nothing else. The semantic unit is: "the accept
cache-outbox lifecycle becomes real (durable claim/retry/terminal
consumer in the review worker) and the public surface it protects is
E2E-proven, including the full public accept-then-discard sequence."

## 5. Explicit non-goals

- NO fetch-time canonical-reference gate on public media fetches (the
  merged 079/1 finalize-time gate + content-addressed immutable reads
  are preserved; see section 3).
- NO new HTTP routes of any kind: the anonymous public media route, the
  nginx `/media/public/` location, and the authenticated asset routes
  are all byte-unchanged.
- NO media GC / staging cleanup (089 territory; the 083/2 known
  limitation carries over unchanged).
- NO edge/public HTML cache introduction: `infra/nginx/nginx.conf`
  byte-unchanged; public HTML stays `private, no-store`.
- NO outbox event-kind change (still `WORKSPACE_ACCEPTED` only); no
  DISCARD/FREEZE outbox events.
- NO freeze/snapshot/read-model/re-review/selective-accept change
  (082/082-2/071_001 byte-unchanged; the 024_001 stub
  `slaif_workspace_selective_accept` remains untouched and unconnected).
- NO Agent-facing surface change: Agent route policy, OpenAPI, and
  capability catalog byte-unchanged.
- NO MCP work (080, deferred after 084 per human D5); NO Objective 084+
  work; NO dependabot work; NO lockfile/CI-workflow/supply-chain file
  changes; NO new dependencies; NO new compose mounts/env/services.
- NO renderer or Puck behavior change.
- NO physical content-model schema change (content models are
  workspace data, never Alembic operations).

## 6. Requirements

### R1 — Migration 074_001 (upgrade and downgrade both exact)

1. Add to `control.cache_outbox`:
   - `attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >=
     0)`;
   - `last_attempt_at TIMESTAMPTZ` (NULL);
   - `consumed_at TIMESTAMPTZ` (NULL);
   - `last_error TEXT` (NULL; stable code or NULL).
2. New function `control.slaif_cache_outbox_claim(p_limit integer)`
   `RETURNS TABLE (id bigint, site_id uuid, workspace_id uuid,
   event_kind text, payload jsonb, attempt_count integer)`,
   `LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog`,
   `OWNER slaif_owner`: rejects `p_limit` outside 1..64 with
   `OUTBOX_CLAIM_LIMIT_INVALID` (ERRCODE `22023`); CTE `pick` selects
   `id` from `control.cache_outbox` WHERE `consumed_at IS NULL AND
   attempt_count < 25` ORDER BY id `FOR UPDATE SKIP LOCKED LIMIT
   p_limit`; the outer UPDATE sets `attempt_count = attempt_count + 1,
   last_attempt_at = now()` on the picked rows and RETURNs the row
   tuple. The 25-attempt budget is a named constant in this function
   (pinned by test), the single source of retry exhaustion.
3. New function `control.slaif_cache_outbox_consume(p_id bigint,
   p_error text)` `RETURNS TABLE (consumed bigint)`, same
   SECURITY DEFINER/search_path/owner discipline: UPDATE
   `consumed_at = now(), last_error = p_error` WHERE `id = p_id AND
   consumed_at IS NULL` RETURNING `id` (idempotent: an already-
   consumed row returns 0 rows and changes nothing).
4. Grants: `GRANT UPDATE ON control.cache_outbox TO
   slaif_review_worker` (the ONLY new table grant); `GRANT EXECUTE` on
   both new functions TO `slaif_review_worker`. No new roles, no
   memberships, no other GRANT/REVOKE.
5. Downgrade: drop both functions, revoke exactly the grants added,
   drop exactly the four columns; post-downgrade state proven identical
   to `073_001` by query (columns absent, grants absent).
6. Bootstrap revision set updates to `074_001`; the ten established
   migration-head pin files (the exact set currently grepping
   `073_001`) move to `074_001`.

### R2 — Outbox consumer in the review worker (no listener)

1. New module `services/backend/src/slaif_agent_site/review_worker/
   outbox_consumer.py`:
   - pure `evaluate_outbox_row(payload, current_revision)` returning
     exactly one of `CONSUMED` (payload valid AND
     `new_canonical_revision == current_revision`), `SUBSUMED` (payload
     valid AND `new_canonical_revision < current_revision`; a later
     acceptance supersedes this row; terminal, not a failure), or
     `DEAD_LETTER` with a stable code `PAYLOAD_INVALID` (JSON missing /
     keys not exactly `{snapshot_id, digest, base_site_revision,
     new_canonical_revision, media_manifest}` / wrong types /
     `media_manifest` not a list of `{media_id, digest, public_key}`)
     or `REVISION_AHEAD` (`new_canonical_revision > current_revision`;
     impossible under the accept invariants; terminal);
   - `consume_outbox_round(pool, settings)`: one claim of up to the
     batch size; per row: read `SELECT canonical_revision FROM
     control.site WHERE id = $1`, evaluate, consume with `p_error`
     NULL for `CONSUMED`, `'SUBSUMED'` for `SUBSUMED`, the stable code
     for `DEAD_LETTER`; structured log events per claim/outcome;
     returns the processed count. A concurrent accept racing the
     revision read may flip a row to `SUBSUMED` — harmless by
     construction and documented in the module docstring.
2. `review_worker/config.py`: new constants following the existing
   pattern — `REVIEW_WORKER_OUTBOX_POLL_INTERVAL_SECONDS = 5.0` (env
   `SLAIF_REVIEW_WORKER_OUTBOX_POLL_INTERVAL_SECONDS`, ge 0.1 le 60),
   `REVIEW_WORKER_OUTBOX_BATCH_SIZE = 8` (env
   `SLAIF_REVIEW_WORKER_OUTBOX_BATCH_SIZE`, ge 1 le 64),
   `REVIEW_WORKER_OUTBOX_MAX_ATTEMPTS = 25` (documentation constant; a
   unit test pins it equal to the SQL-side budget).
3. Loop integration in `review_worker/worker.py` (and
   `__main__.py` only if wiring requires): after each job-claim cycle,
   run `consume_outbox_round` when the outbox poll interval has
   elapsed (last-run gating; first run on worker start). Same process,
   same `slaif_review_worker` credential, no listener, no new
   connection pool beyond the existing one, no network calls.
4. Crash semantics (the normative contract, pinned by test): the claim
   commits the attempt increment; death between claim and consume
   leaves the row re-claimable (attempt incremented, `consumed_at`
   NULL); the row is processed exactly once in effect (single
   `consumed_at`); at the 25-attempt budget the row stops being
   claimed and is terminal (abandoned, operator-visible via
   `last_attempt_at`/`attempt_count`); `consumed_at NOT NULL` is the
   processed terminal (last_error NULL = `CONSUMED`, `'SUBSUMED'` =
   superseded, other stable code = dead-letter).

### R3 — Public-surface honesty E2E pins (preserve + prove; zero new
product surface)

1. `tests/e2e/accept-lifecycle.spec.ts` (existing project; no roster
   change), extended after the existing acceptance pins:
   - `GET /s/<siteKey>` response header `Cache-Control` is exactly
     `private, no-store`;
   - the public HTML contains the renderer `<img>` for the accepted
     media with `src` exactly
     `/media/public/sha256/{h[:2]}/{h[2:4]}/{h}` of the accepted
     digest (the pre-accept negative — no public `<img>` before
     acceptance — remains pinned by the existing 079/1/082 specs and
     must still hold);
   - `GET` of that exact `src`: 200, body sha256 equals the digest,
     `Cache-Control` exactly `public, max-age=31536000, immutable`;
   - outbox consumption: bounded psql poll (up to 30 s, 1 s interval)
     until the workspace's single outbox row has `consumed_at IS NOT
     NULL`; then pin `attempt_count >= 1`, `last_error IS NULL`, and
     exactly one row for the workspace.
2. `tests/e2e/discard-lifecycle.spec.ts` (existing project; no roster
   change), new second test "post-accept discard preserves the
   published canonical":
   - human session on a dedicated run-unique site: workspace A (unique
     heading + a small unique image) -> freeze -> accept via the
     worker -> published state verified (public HTML contains A's
     heading; A's media 200 + re-hash; one outbox row consumed);
   - workspace B on the SAME site (different heading + different
     small image) -> discard with typed confirmation -> `DISCARDED`;
   - assert: public HTML byte-identical to the post-accept bytes
     (existing `normalizeCspNonce` convention) and contains A's
     heading, not B's; A's media still 200 byte-identical with the
     immutable headers; B's media `public_status = 'private'` in the
     DB (never finalized); outbox row count still exactly 1 (discard
     emits nothing); B's workspace capability revoked (existing pin
     pattern); B's job `SUCCEEDED`; audit/revision/state exact.
3. `tests/e2e/review-surface.spec.ts` unchanged (its line-844
   `/media/public/` negative re-runs green).

### R4 — Fault-injection suite (new integration file)

New `services/backend/tests/integration/test_cache_outbox_consumer.py`
(real PostgreSQL + foundation + the worker pool; model:
`test_real_human_accept.py`), covering at minimum:

1. claim semantics: rows claimed in id order; two concurrent claim
   calls against overlapping pending sets return DISJOINT rows (SKIP
   LOCKED; no double claim);
2. crash between claim and consume: claim commits, no consume; the row
   is re-claimed with `attempt_count` incremented; eventual consume
   leaves exactly one `consumed_at` (processed exactly once in effect);
3. consume idempotency: a second consume of the same id returns 0 rows
   and changes nothing;
4. corrupt payloads (non-JSON, missing key, extra key, wrong type,
   malformed `media_manifest` entry) -> terminal dead-letter
   `PAYLOAD_INVALID`; never re-claimed;
5. superseded row (fixture-advanced `control.site.canonical_revision`)
   -> terminal `SUBSUMED` (not a dead-letter);
6. `REVISION_AHEAD` (fixture) -> terminal dead-letter, never
   re-claimed;
7. attempt budget: 25 claim-without-consume cycles -> the row is no
   longer claimed at attempt 26 (terminal abandoned state pinned);
8. outbox/accept coherence: after the full accept E2E flow, outbox row
   count equals successful terminal accept count; duplicate accept
   (terminal 409) adds no row (re-pins the 083/1 property at this
   head); a mid-reviewer-transaction failure (existing 083/1 fault
   pattern) leaves NO orphan outbox row.

### R5 — Current-truth documentation (four surfaces, durable form)

Update exactly these four surfaces, in the durable form established by
the 078-z governance transition:

- `README.md`
- `oap/INCREMENTS.md`
- `oap/MVP-PROGRESS.md`
- `oap/MVP-CONTRACT-AUDIT.md`

1. F3 flip (owed from 083/2): every 083/2 "in flight at `083-2-a`"
   reference becomes the verified merge fact — PR #101, merge commit
   `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`, merged
   2026-10-06T04:36:59Z — including the MVP-CONTRACT-AUDIT
   authoritative-source-revision line, which moves to
   `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`.
2. Record 083/3 as in flight at round `083-3-a` (branch
   `oap/083-3-a-cache-outbox-consumer`, base
   `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`), and state that GitHub
   is authoritative for live acceptance/merge state; `oap/active` means
   "last activated round until the next activation".
3. State that numeric Objective 083 remains PARTIAL (083/3 in flight;
   084+ planned); the contractual MVP remains NOT COMPLETE; no "this
   PR is open" / "pending strategic merge" / "active increment means
   open PR" ephemeral wording anywhere in the four surfaces.
4. The MVP-CONTRACT-AUDIT accept/discard row (currently
   §§15.9/29.1-29.3) appends the 083/2 merged fact (real discard:
   idempotent enqueue, single reviewer-transaction discard, terminal
   DISCARDED, conflict remedy, E2E-proven on the merged head) and marks
   083/3 in flight.
5. The adversarial grep (current-state stale-claim patterns) returns
   nothing in the four surfaces at the report head.

### R6 — Contracts byte-identity

- `git diff base..head -- contracts/ packages/` is empty;
- the agent OpenAPI 47-path strip-identity
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83` is
  re-proven at BOTH base and head (strategy recomputes both sides).

### R7 — Evidence (actually executed, honestly reported)

1. Local unit + integration suites (full), including at minimum:
   - `074_001` round trip: upgrades cleanly from `073_001`, downgrades
     back to the proven `073_001` state (query-verified);
   - grant-surface proof vs the 083/1 baseline: exactly one new table
     grant (UPDATE on `control.cache_outbox`) and exactly two new
     function EXECUTE grants, all to `slaif_review_worker`; nothing
     else changed;
   - `evaluate_outbox_row` unit matrix (payload variants x revision
     relation, every branch);
   - consumer loop gating pins (poll interval, batch size, first-run
     on start);
   - the R4 fault suite (all 8 cases);
   - route-policy totals UNCHANGED (197 agent / 35 control);
   - web route-inventory pin unchanged; migration-head pins moved
     `073_001` -> `074_001` in the exact ten-file set.
2. Compose smoke (`tools/compose/smoke.sh`, baseline-relative): no new
   wiring — the review-worker mounts/env are UNCHANGED; E2E roster
   unchanged at 19; worker readiness unchanged.
3. The full CI roster (19 projects) terminal and green at the exact
   report head: all 20 required checks successful, none
   failed/cancelled/pending; first attempt or one documented
   flake-class re-run max.

### R8 — Hard constraints (violation = rejection)

- Zero new HTTP routes; Agent route policy / OpenAPI / capability
  catalog byte-unchanged; `infra/nginx/nginx.conf` byte-unchanged.
- No fetch-time canonical-reference gate on public media; merged 079/1
  semantics preserved (finalize-time gate + content-addressed
  immutable reads).
- No media GC / staging cleanup; no new outbox event kinds; no
  freeze/snapshot/read-model/re-review/selective-accept change.
- No dependabot incorporation; no lockfile, CI-workflow, or supply-
  chain file changes; no new dependencies; no new compose
  mounts/env/services.
- No secrets in code/docs/tests.

## 7. Acceptance criteria (observable)

1. `074_001` round trip clean; both new functions SECURITY DEFINER with
   `search_path = pg_catalog`, `OWNER slaif_owner`, exact grant pins;
   bootstrap revision set at `074_001`.
2. Grant surface proven: exactly the one new table grant + two new
   function EXECUTE grants vs the 083/1 baseline; worker role
   memberships unchanged.
3. Claim: id-order, disjoint under concurrent claims, limit gate
   `OUTBOX_CLAIM_LIMIT_INVALID`, 25-attempt budget enforced (row
   abandoned, never re-claimed).
4. Consume: idempotent (0 rows on replay); terminal states exact
   (`CONSUMED` last_error NULL; `SUBSUMED`; `PAYLOAD_INVALID`;
   `REVISION_AHEAD`).
5. Crash semantics proven: claim-then-death re-claims with incremented
   attempt; processed exactly once in effect.
6. Consumer loop: no listener; interval/batch gating pinned; runs in
   the existing worker process under the existing credential.
7. R3: all public-surface E2E pins hold at the exact head (no-store
   public HTML header exact; public `<img>` src exact; media fetch 200
   re-hash + immutable headers exact; outbox consumed within the
   bounded poll; the full post-accept-discard sequence with byte-
   identical public HTML, A-media intact, B-media private, single
   outbox row, B capability revoked).
8. R4: all 8 fault cases pass; outbox/accept coherence pinned.
9. R5: the four surfaces match the durable form exactly; the F3 flip is
   present; the adversarial grep returns nothing.
10. R6: `git diff base..head -- contracts/ packages/` empty; strip-
    identity re-proven at both base and head (strategy recomputes both
    sides).
11. R7: full CI roster (19 projects) terminal and green at the exact
    report head, 20/20 required checks; predeclared budgets (section
    10) honest; cumulative base->head grouped size computed; the 20
    prod/config-file trigger reported explicitly fired/not-fired;
    CLOSURE_ONLY state (expected: never entered) reported; any
    variance itemized and classed.

## 8. Verification and workflow

- Strategy activates this order atomically with `oap/active` =
  `083-3-a`.
- The executor first resets the local checkout to verified remote main
  `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`, then creates branch
  `oap/083-3-a-cache-outbox-consumer` and pushes the transcript commit
  T first. T contains exactly: the order file and `oap/active` bytes as
  published.
- Implementation commits follow (I, ...); a docs commit (D) with the R5
  flips precedes the report commit (S, report-only, parent =
  implementation head).
- Local authority: the executor owns packages, browsers, databases,
  services, compose stacks, and test execution in the disposable VM
  (passwordless sudo); strategy never performs that labor.
- GitHub workflow: push the branch, open the unique objective PR (title
  per section 1), report the PR number/URL/branch/SHAs in the report.
  No merge by the executor — only strategy merges.
- Flake policy: at most ONE documented unmodified CI re-run, and only
  for a documented flake class with its exact failure signature; any
  other recurrence is a real failure — fix in code or report BLOCKED.
- The full CI roster must reach the terminal roster at the exact report
  head; do not re-run unmodified heads except the single documented
  flake-class allowance.

## 9. Report requirements

`oap/reports/083-3-a-cache-outbox-consumer.md` must contain, at
minimum:

- Order identity (round, objective, PR, branch, base, every commit
  T/I/.../D/S with SHAs), the exact report-publication convention
  (`Report publication commit: SELF`; the remote PR head must be that
  report-only commit whose parent is the literal implementation-head
  SHA).
- Authoritative GitHub state at report time (PR number, head SHA, check
  state per run).
- Honest CI history (every run, every failure, every re-run with the
  exact flake signature if the allowance is used).
- Budget table vs the predeclared budget (production/config;
  migrations; test/evidence; generated; docs; OAP transcript;
  substantive lines) with the cumulative base->head grouped size and
  the explicit trigger fired/not-fired determination.
- Every R7 evidence item with its actual executed output (counts, SHAs,
  psql baselines, hashes, the grant-surface proof query output, the
  before/after public-render byte-identity, the header values
  observed, the bounded-poll outcome, any adaptation itemized with
  rationale).
- The `074_001` round-trip proof (up + down, post-downgrade state).
- The R4 fault-suite case-by-case outcomes.
- Explicit confirmation: zero new HTTP routes; nginx byte-identical;
  Agent surface byte-identical (R6 strip-identity at both sides).
- Deviations from this order (if any) with rationale; known
  limitations; residual risks and what 084 needs from this increment.
- `Report publication commit: SELF`.

## 10. Predeclared review budget (2026-09-14 review-unit governance
in force)

- Production/config files: at most 6 — itemized: migration `074_001`
  1; `review_worker/outbox_consumer.py` new 1;
  `review_worker/worker.py` 1; `review_worker/config.py` 1;
  `review_worker/__main__.py` 1 (loop wiring, only if required); plus
  at most 1 small helper file if truly needed.
- Migrations: exactly 1 (`074_001`).
- Test/evidence files: at most 14 — itemized:
  `services/backend/tests/integration/
  test_cache_outbox_consumer.py` new 1 (R4 fault suite + R7 unit
  matrix in-file or as its stated subset);
  `tests/e2e/accept-lifecycle.spec.ts` 1;
  `tests/e2e/discard-lifecycle.spec.ts` 1; plus the ten established
  migration-head pin files moving `073_001` -> `074_001` (each a
  1-3 line mechanical change).
- Generated-contract footprint: 0 (byte-identity, R6).
- Docs footprint: 4 surfaces (R5).
- OAP transcript footprint: this order + `active` + one report.
- Substantive implementation-line scale: at most 3200 lines (honest
  estimate — report the actual).
- The ~20-30 production/config file threshold remains a REVIEW
  TRIGGER, not a quota: if the honest cumulative count crosses 20, the
  PR enters CLOSURE_ONLY — no new semantic family may enter after that
  point.
- Do not game the budget by moving code between directories, excluding
  meaningful tests, or treating generated/OAP files as if they do not
  exist.

## 11. Review-unit governance (2026-09-14 amendment, in force)

- Cumulative review size is computed base->head (not latest-round
  delta), grouped: production/config; migrations; tests/evidence;
  generated artifacts; docs; OAP transcript.
- CLOSURE_ONLY mode (if triggered): no new semantic family, no
  adjacent feature, no opportunistic scope, no next-objective work;
  only finite defects/evidence required to make already-added behavior
  safe, correct, and reviewable. Separable functionality starts from
  verified merged main in another PR.
- Finite rejection checklist: if strategy rejects the COMPLETE claim,
  the rejection publishes one finite list of unresolved criteria with
  the executable evidence required for each; a later report may claim
  COMPLETE only if every named criterion was actually executed.
