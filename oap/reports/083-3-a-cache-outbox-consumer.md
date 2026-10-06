# OAP Coding-Agent Report — 083-3-a

## Work order

- Order: `oap/orders/083-3-a-cache-outbox-consumer.md` (activated via
  `oap/active`, strategic FIFO `OK` received 2026-10-06).
- Round: `083-3-a` (increment-qualified form: 083/3 — outbox consumer
  and public-surface proof; third and final increment of the approved
  083/1-083/3 pre-split for numeric Objective 083).
- Objective: 083 (real human accept/discard promotion lifecycle); this
  increment delivers the durable cache-outbox consumer (claim/retry/
  terminal lifecycle in the review worker, no listener) and the
  public-surface honesty E2E proof (preserve + prove: no-store public
  HTML, content-addressed immutable public media, outbox consumption,
  and the full post-accept-discard sequence).
- Mode: `NNN-a` — CREATE_NEW_PR: one fresh branch + one new PR from
  authoritative remote main.
- Branch: `oap/083-3-a-cache-outbox-consumer`.
- PR: #102 (URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/102`),
  state OPEN.
- Base: main @ `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c` (PR #101
  merged, 083/2; verified via `git ls-remote` at branch creation).
- Starting remote main SHA (verified at branch creation):
  `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`.
- Commits: transcript T `5dbc7300f6c639fc8ba419098434dd07e2877a9a`
  (order + `oap/active` bytes, pushed at activation); implementation I
  `fb5e03698b05e018962c5107da6da336bc1d6436` (migration 074_001,
  outbox consumer module, worker loop, config, mandatory
  privilege-registry/bootstrap adaptations, full local test suite);
  docs D `49b3ac59e8882e6bfb6f435dab7c179d06a29c99` (R5
  current-truth flips, four surfaces); report S (SELF) `REPORTSHA`
  (report-only, first parent D).
- Implementation head SHA: `49b3ac59e8882e6bfb6f435dab7c179d06a29c99`
  (D; the head of all non-report work).
- Report publication commit: SELF (report-only; its literal SHA is the
  remote PR head, verifiable via `gh pr view 102 --json headRefOid`,
  parent = D; the SELF commit changes only the new report file).
- Pushed commits: T (already pushed at activation), I, D, SELF.
- Remote PR head after report publication: SELF (literal derived via
  GitHub).

## Status

PARTIAL — every in-scope requirement R1-R6 and R7.1/R7.2 is
implemented and locally evidenced (all local suites, the 19-project
Compose E2E roster, and the contract byte-identity gates pass); the
only unmet acceptance criterion is R7.3/criterion 11 (full CI roster
20/20 terminal green at the exact report head): one required check,
`Supply-chain evidence`, FAILED for an out-of-scope environmental
reason — a newly published Critical Chromium CVE
(CVE-2026-103628, fixed in Chrome 154.0.8037.97) now flagged against
the byte-unchanged pinned browser-worker image (details under
"GitHub CI / required checks"). Fixing it requires a browser
security refresh or a documented supply-chain exception, both
explicitly outside this order's R8 scope. Strategy independently
reviews and merges — PARTIAL never means accepted.

## Executive summary

083/3 makes the accept cache-outbox lifecycle real. 083/1 emits
exactly one durable `WORKSPACE_ACCEPTED` row inside the all-or-nothing
reviewer transaction; nothing consumed it. This increment adds:

- **R1 — migration `074_001`**: four columns on `control.cache_outbox`
  (`attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (>= 0)`,
  `last_attempt_at TIMESTAMPTZ`, `consumed_at TIMESTAMPTZ`,
  `last_error TEXT`); `control.slaif_cache_outbox_claim(p_limit
  integer)` (SECURITY DEFINER, `search_path = pg_catalog`,
  `OWNER slaif_owner`; rejects `p_limit` outside 1..64 with
  `OUTBOX_CLAIM_LIMIT_INVALID`/22023; CTE pick of
  `consumed_at IS NULL AND attempt_count < 25` in id order with
  `FOR UPDATE SKIP LOCKED`, UPDATE increments the attempt and
  RETURNs the row tuple; the 25-attempt budget is the named constant
  in this function, the single source of retry exhaustion);
  `control.slaif_cache_outbox_consume(p_id bigint, p_error text)`
  (same discipline; idempotent — an already-consumed row returns 0
  rows and changes nothing). Grants: `UPDATE` on
  `control.cache_outbox` + `EXECUTE` on both functions, all to
  `slaif_review_worker` only (the ONLY new table grant; no roles, no
  memberships, no other GRANT/REVOKE). Downgrade drops exactly the
  two functions, revokes exactly the added grants, drops exactly the
  four columns; post-downgrade state proven identical to `073_001`
  by query (round-trip, below). Bootstrap revision set at
  `074_001`; the exact ten established migration-head pin files moved
  `073_001` -> `074_001`.
- **R2 — consumer in the review worker (no listener)**: new
  `review_worker/outbox_consumer.py` with pure
  `evaluate_outbox_row(payload, current_revision)` (exactly one of
  `CONSUMED` / `SUBSUMED` / `DEAD_LETTER{PAYLOAD_INVALID,
  REVISION_AHEAD}` under exact 5-key shape validation: str-UUIDs,
  64-hex digests, int-not-bool revisions, manifest entries exactly
  `{media_id, digest, public_key}` with the canonical public key
  shape) and `consume_outbox_round(pool, settings)` (one bounded
  claim; per row: read the site's `canonical_revision`, evaluate,
  consume with `p_error` NULL/`'SUBSUMED'`/stable code; structured
  log events; transient-failure rows stay re-claimable).
  `config.py` gains `REVIEW_WORKER_OUTBOX_POLL_INTERVAL_SECONDS =
  5.0` (env, ge 0.1 le 60), `REVIEW_WORKER_OUTBOX_BATCH_SIZE = 8`
  (env, ge 1 le 64), `REVIEW_WORKER_OUTBOX_MAX_ATTEMPTS = 25`
  (documentation constant; unit-pinned equal to the SQL-side budget).
  `worker.py`'s claim loop runs one gated outbox round after each
  job-claim cycle (last-run gating; first run on worker start;
  updates on failure too). Same process, same `slaif_review_worker`
  credential, no listener, no new pool, no network calls. Crash
  semantics: the claim commits the attempt increment, so
  claim-then-death leaves the row re-claimable; consume is
  idempotent, so the row is processed exactly once in effect (single
  `consumed_at`); at the 25-attempt budget the row stops being
  claimed (terminal abandoned, operator-visible). The accept-race
  (revision advances between read and consume) flips a row to
  `SUBSUMED` — harmless by construction, documented in the module
  docstring, alongside the no-op invalidation honesty (this
  deployment has no public edge cache: public HTML is never cached,
  media is content-addressed and immutable).
- **R3 — public-surface honesty E2E (preserve + prove)**:
  `accept-lifecycle.spec.ts` extended — public `/s/<siteKey>`
  `Cache-Control` pinned byte-exact at the edge (Next.js
  force-dynamic no-cache default, strictly stronger than the
  internal render route's preserved `private, no-store` — see
  Deviation D-1); public HTML contains the renderer
  `<img class="sl-image">` with `src` exactly
  `/media/public/sha256/{h2}/{h2}/{h64}` of the accepted digest;
  that exact `src` returns 200, body re-hashes to the digest,
  `Cache-Control` exactly `public, max-age=31536000, immutable`;
  bounded psql poll (<=30 s @1 s) until the workspace's single
  outbox row is consumed, then `attempt_count >= 1`,
  `last_error IS NULL`, exactly one row for the workspace.
  `discard-lifecycle.spec.ts` gains the second test "post-accept
  discard preserves the published canonical": workspace A (unique
  heading + image) freeze->accept->published verified (public HTML
  carries A, A media 200 + re-hash + immutable headers, A's single
  outbox row consumed); workspace B on the SAME site (different
  heading + different image, distinct digest) freeze->discard (typed
  acknowledgement) -> `DISCARDED`; public HTML byte-identical to the
  post-accept bytes (nonce-normalized) containing A not B; A media
  still 200 byte-identical immutable; B media `private`/no
  `published_at` (never finalized); outbox row count exactly 1
  (discard emits nothing: B-workspace 0, site-wide 1); canonical
  revision exactly `before + 1`; `audit.promotion` exactly 1 site
  row / 0 B rows; B capability revoked; B job `SUCCEEDED`;
  observation channel clean.
- **R4 — fault-injection suite**: new
  `test_cache_outbox_consumer.py` (real PostgreSQL + foundation +
  worker pool; model `test_real_human_accept.py`): round trip,
  grant-surface delta proof, claim id-order / disjoint-concurrent /
  limit gate, crash-reclaim-exactly-once, consume idempotency,
  corrupt-payload round (24 variants), revision-relation states,
  25-budget abandon, outbox/accept coherence, the in-file pure
  evaluation matrix, gating pins, and the
  `REVIEW_WORKER_OUTBOX_MAX_ATTEMPTS == SQL constant` pin.
- **R5 — current-truth docs (four surfaces)**: the F3 flip owed
  from 083/2 (every `083-2-a` "in flight" reference becomes the
  verified merge fact: PR #101, merge commit
  `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`, merged
  2026-10-06T04:36:59Z, including the MVP-CONTRACT-AUDIT
  authoritative-source-revision line) plus 083/3 recorded as in
  flight at `083-3-a`; numeric Objective 083 stated PARTIAL (083/3
  in flight; 084+ planned); contractual MVP NOT COMPLETE; no
  ephemeral "open PR / pending merge / active means open PR"
  wording anywhere in the four surfaces.
- **R6 — contracts byte-identity**: `git diff base..head --
  contracts/ packages/` empty; zero new HTTP routes (Agent route
  policy 197 / control 35 unit-pinned unchanged; web route
  inventory unchanged — no file under `apps/web` touched);
  `infra/nginx/nginx.conf` byte-unchanged; the Agent OpenAPI
  47-path strip-identity
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
  re-proven by strategy at both base and head (contract bytes
  unchanged, so the identity is the 083/1-proven value at both).

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: #102 `OAP 083-3-a: outbox consumer and public-surface
  proof (083/3)` (exact title per order section 1), state OPEN,
  branch `oap/083-3-a-cache-outbox-consumer`, base `main`.
- Head at report time: the report-only SELF commit (verify via
  `gh pr view 102 --json headRefOid`; its parent is D
  `49b3ac59e8882e6bfb6f435dab7c179d06a29c99`).
- Remote `main` unchanged at
  `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c` (no merge by the
  executor; strategy owns acceptance/merge).
- Dependabot PRs #83, #94, #100: untouched.
- Check states per run: see "GitHub CI / required checks" below.

## Changes made

### 1. Migration `074_001_cache_outbox_consumer.py` (185/0, exactly 1)

Adds to `control.cache_outbox`: `attempt_count INTEGER NOT NULL
DEFAULT 0 CHECK (attempt_count >= 0)`, `last_attempt_at TIMESTAMPTZ`,
`consumed_at TIMESTAMPTZ`, `last_error TEXT`. Adds
`control.slaif_cache_outbox_claim(p_limit integer) RETURNS TABLE
(id bigint, site_id uuid, workspace_id uuid, event_kind text,
payload jsonb, attempt_count integer)` — plpgsql, SECURITY DEFINER,
`SET search_path = pg_catalog`, `OWNER slaif_owner`; rejects
`p_limit` outside 1..64 with `RAISE EXCEPTION USING
ERRCODE = '22023', MESSAGE = 'OUTBOX_CLAIM_LIMIT_INVALID'`; CTE
`pick` selects ids from `consumed_at IS NULL AND attempt_count <
25` (25 = the named constant `max_attempts`, the single source of
retry exhaustion) in id order with `FOR UPDATE SKIP LOCKED LIMIT
p_limit`; the outer UPDATE sets `attempt_count = attempt_count + 1,
last_attempt_at = now()` on the picked rows and RETURNs the row
tuple. Adds `control.slaif_cache_outbox_consume(p_id bigint,
p_error text) RETURNS TABLE (consumed bigint)` — same discipline;
`UPDATE ... SET consumed_at = now(), last_error = p_error WHERE id
= p_id AND consumed_at IS NULL RETURNING id` (idempotent: an
already-consumed row returns 0 rows and changes nothing). Grants:
`GRANT UPDATE ON control.cache_outbox TO slaif_review_worker` (the
ONLY new table grant) + `GRANT EXECUTE` on both functions TO
`slaif_review_worker`; no new roles, no memberships, no other
GRANT/REVOKE. Downgrade: drops both functions, revokes exactly the
added grants, drops exactly the four columns.

### 2. `review_worker/outbox_consumer.py` (285/0, new module)

Pure `evaluate_outbox_row(payload, current_revision)` ->
`CONSUMED` (valid payload AND `new_canonical_revision ==
current_revision`), `SUBSUMED` (valid payload AND `<`; terminal, not
a failure), or `DEAD_LETTER` with stable code `PAYLOAD_INVALID`
(any shape failure: keys not exactly the 5-key set, non-str-UUID
`snapshot_id`/`media_id`, non-64-hex digests, non-int-or-bool
revisions, `media_manifest` not a list of exactly
`{media_id, digest, public_key}` with `public_key` matching
`public/sha256/[0-9a-f]{2}/[0-9a-f]{2}/[0-9a-f]{64}`) or
`REVISION_AHEAD` (`>`; impossible under the accept invariants;
terminal). `consume_outbox_round(pool, settings)`: one claim of up
to `outbox_batch_size` rows through
`SELECT * FROM control.slaif_cache_outbox_claim($1)`; per row:
`SELECT canonical_revision FROM control.site WHERE id = $1`
(missing site -> row left re-claimable), evaluate (JSONB arrives as
JSON text from asyncpg and is decoded; unparseable -> dead-letter),
consume via `SELECT control.slaif_cache_outbox_consume($1, $2)`
with `p_error` NULL/`'SUBSUMED'`/stable code; structured log
events per claim/outcome; transient DB failures skip the row
(re-claimable). Pure `outbox_round_due(last, now, interval)`
(`None` first run due). Module docstring documents the crash
semantics, the accept-race -> `SUBSUMED` harmlessness, and the
no-op invalidation honesty (no public edge cache in this
deployment; the consumed/outbox contract is the future hook point).

### 3. `review_worker/worker.py` + `config.py` (loop integration; no listener)

`_worker_loop` restructured (no `continue`s): after each job-claim
cycle (including the idle-poll path) it runs
`consume_outbox_round` when `outbox_round_due(last_outbox_run,
time.monotonic(), outbox_poll_interval_seconds)`;
`last_outbox_run: float | None = None` gives the first run on
worker start; the timestamp updates on failure too. Same process,
same `slaif_review_worker` credential, existing pool, no listener,
no new pool, no network calls. `config.py` adds
`REVIEW_WORKER_OUTBOX_POLL_INTERVAL_SECONDS = 5.0` (env
`SLAIF_REVIEW_WORKER_OUTBOX_POLL_INTERVAL_SECONDS`, ge 0.1 le 60),
`REVIEW_WORKER_OUTBOX_BATCH_SIZE = 8` (env
`SLAIF_REVIEW_WORKER_OUTBOX_BATCH_SIZE`, ge 1 le 64),
`REVIEW_WORKER_OUTBOX_MAX_ATTEMPTS = 25` (documentation constant;
unit-pinned equal to the SQL-side budget), plus the two settings
fields and `__all__` entries. `__main__.py` UNCHANGED (no wiring
required).

### 4. Mandatory registry/bootstrap adaptations

`db/privileges.py` (2 spots): `slaif_review_worker` UPDATE on
`control.cache_outbox` in the registry's table-grant expectations
and both new function EXECUTE grants in `REVIEW_WORKER_FUNCTIONS`
(with the GRANT argument signatures `integer` and `bigint, text`
— the function ACL grant form); without it, every reconcile would
revoke the migration's worker grants and
`verify_database_privileges` would fail `effective-dml`.
`bootstrap/service.py` (1 line): `074_001` in the
downgrade-compatibility revision set.

### 5. E2E pins (R3)

`tests/e2e/accept-lifecycle.spec.ts` (+48/-1): the four R3.1 pins
after the existing acceptance pins (public HTML `Cache-Control`
byte-exact at the edge per Deviation D-1; `<img class="sl-image">`
with the exact content-addressed `src`; media fetch 200 + re-hash +
`Cache-Control` exactly `public, max-age=31536000, immutable`;
bounded 30 s @1 s psql poll to consumed with `attempt_count >= 1`,
`last_error IS NULL`, exactly one row for the workspace).
`tests/e2e/discard-lifecycle.spec.ts` (+310): `TINY_PNG_B`
(second valid 1x1 PNG, distinct digest) and the second test
"post-accept discard preserves the published canonical (083/3)"
(`test.setTimeout(600_000)`): full A-accept + B-discard sequence on
one dedicated site with all R3.2 assertions (public HTML
byte-identical via `normalizeCspNonce`, A present / B absent, A
media 200 byte-identical + immutable headers, B media
`private|no published_at`, outbox `0|1`, revision `+1`, audit
`1|0`, B capability revoked, B job `SUCCEEDED`, `observe` clean).
`tests/e2e/review-surface.spec.ts` UNCHANGED (its `/media/public/`
negative re-ran green in the roster).

### 6. R4 fault-injection suite (new integration file)

`services/backend/tests/integration/test_cache_outbox_consumer.py`
(1182/0): 14 top-level tests / 50 results — round trip,
grant-surface delta, claim semantics (id order, disjoint
concurrent, limit gate 0/65/NULL), crash-reclaim-exactly-once,
consume idempotency, corrupt-payload round (24 variants),
revision-relation states, 25-budget abandon, outbox/accept
coherence (fault-first + healed retry + duplicate accept), in-file
pure matrix (~40 params), gating pins, and the max-attempts
constant pin. Imports the established helpers from
`test_real_human_accept` (cross-import pattern).

### 7. Tests / evidence pins

The ten established migration-head pin files moved `073_001` ->
`074_001` (unit `test_control_database.py`,
`test_foundation_contract.py` [pin + history prepend + wheel
file-list entry]; integration `test_database_bootstrap.py`,
`test_control_database_integration.py` [L159 readiness comparison
vs `migration_heads()`], `test_agent_mutations.py` [11 sites],
`test_editable_domain_proof.py`, `test_agent_page_style.py`,
`test_human_agent_session_control.py`,
`test_review_surface_read_model.py` [docstring],
`test_real_human_discard.py` [L729/L824 only; L3/L121/L719/L971
historical, kept]). `test_real_human_discard.py` additionally:
`test_worker_grant_surface_unchanged` renamed
`test_worker_grant_surface_exact` (docstring flip;
`("control","cache_outbox"): (True, True)` added; new worker-ONLY
EXECUTE loop over the two functions). `test_review_worker.py`
(+4): the loop-test fakes answer the new outbox-claim SQL with no
pending rows.

### 8. Documentation (R5, 4 surfaces, commit D)

`README.md`: the "Objective-083/2 real human discard (merged)" row
added (PR #101, merge commit, 2026-10-06) and the Planned-product-
work row flipped (083/3 in flight at `083-3-a`).
`oap/INCREMENTS.md`: ledger paragraph + new `083/2` row + Next row
flipped. `oap/MVP-PROGRESS.md`: current-state paragraph + the 083
row flipped (083 PARTIAL until 083/3 merges).
`oap/MVP-CONTRACT-AUDIT.md`: authoritative-source-revision line
moved to `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c` (the 083/2
merge, re-verified 2026-10-06) and the §§15.9/29.1-29.3
accept/discard row appended with the 083/2 merged fact and 083/3
in flight. Adversarial grep at the report tree: `grep -n
'083-2-a\|in flight\|this PR is open\|pending strategic merge'
README.md oap/INCREMENTS.md oap/MVP-PROGRESS.md
oap/MVP-CONTRACT-AUDIT.md` returns only the four intentional
`083-3-a` in-flight references and zero stale 083/2 claims.

## Files changed

| File | Commit | Purpose |
|---|---|---|
| `oap/orders/083-3-a-cache-outbox-consumer.md` (new) + `oap/active` | T | transcript (order + active bytes as published) |
| `services/backend/src/slaif_agent_site/db/alembic/versions/074_001_cache_outbox_consumer.py` (new) | I | R1 migration (up + exact down) |
| `services/backend/src/slaif_agent_site/review_worker/outbox_consumer.py` (new) | I | R2 consumer module |
| `services/backend/src/slaif_agent_site/review_worker/worker.py` | I | R2 loop integration |
| `services/backend/src/slaif_agent_site/review_worker/config.py` | I | R2 settings constants/fields |
| `services/backend/src/slaif_agent_site/db/privileges.py` | I | adaptation 1 (registry) |
| `services/backend/src/slaif_agent_site/bootstrap/service.py` | I | adaptation 2 (downgrade-compat set) |
| `services/backend/tests/integration/test_cache_outbox_consumer.py` (new) | I | R4 fault suite + matrix + pins |
| 10 migration-head pin files (unit: `test_control_database.py`, `test_foundation_contract.py`; integration: `test_database_bootstrap.py`, `test_control_database_integration.py`, `test_agent_mutations.py`, `test_editable_domain_proof.py`, `test_agent_page_style.py`, `test_human_agent_session_control.py`, `test_review_surface_read_model.py`, `test_real_human_discard.py`) | I | `073_001` -> `074_001` (+ grant-surface rename/flip + wheel file list) |
| `services/backend/tests/unit/test_review_worker.py` | I | adaptation 4 (loop-fake) |
| `tests/e2e/accept-lifecycle.spec.ts` | I | R3.1 pins |
| `tests/e2e/discard-lifecycle.spec.ts` | I | R3.2 test |
| `README.md`, `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`, `oap/MVP-CONTRACT-AUDIT.md` | D | R5 current-truth flips |
| `oap/reports/083-3-a-cache-outbox-consumer.md` (new) | S | this report (sole path) |

## Pre-declared budget check (order Section 10 vs measured)

Cumulative base (`214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`)
-> head, grouped:

| Group | Predeclared | Actual | Itemization |
|---|---|---|---|
| Production/config files | at most 6 | 6 | `074_001_cache_outbox_consumer.py` new (185 lines; also the single migration); `review_worker/outbox_consumer.py` new (285); `review_worker/worker.py` (+55/-40); `review_worker/config.py` (+12); `db/privileges.py` (+12/-2, adaptation 1); `bootstrap/service.py` (+1, adaptation 2). `review_worker/__main__.py` UNCHANGED (loop wiring not required). |
| Migrations | exactly 1 | 1 | `074_001` (up + exact down). |
| Test/evidence files | at most 14 | 14 | `test_cache_outbox_consumer.py` new (1182); `accept-lifecycle.spec.ts` (+48/-1); `discard-lifecycle.spec.ts` (+310); the ten established pin files (itemized under "Changes made" 7; `test_foundation_contract.py` +4/-1 incl. wheel file-list adaptation 3; `test_real_human_discard.py` +39/-12 incl. grant-surface rename/flip); `test_review_worker.py` (+4, adaptation 4). |
| Generated-contract footprint | 0 | 0 | `git diff base..head -- contracts/ packages/` empty; all three generator `--check` runs zero-diff. |
| Docs footprint | 4 surfaces | 4 | `README.md` (+2/-1), `oap/INCREMENTS.md` (+8/-5), `oap/MVP-PROGRESS.md` (+2/-2), `oap/MVP-CONTRACT-AUDIT.md` (+2/-2). |
| OAP transcript footprint | order + active + one report | 3 | T (order 544 lines + `oap/active` byte flip), report S (this file). |
| Substantive implementation lines | at most 3200 | 550 | production/config added lines only: 185 + 285 + 55 + 12 + 12 + 1 (17% of the ceiling). |

REVIEW TRIGGER (~20-30 production/config files): NOT FIRED
(6 < 20; cumulative, not per-round). CLOSURE_ONLY state: never
entered. No budget gaming: nothing moved between directories, no
meaningful test excluded, generated/OAP files counted above.

## Deviations and adaptations (itemized)

### Deviation D-1 (flagged to the human, per the order's own
pre-split-reconciliation pattern): R3.1 public-HTML
`Cache-Control` pin value

The order's R3.1 pins `GET /s/<siteKey>` `Cache-Control` "exactly
`private, no-store`". That literal string is the INTERNAL render
route's header (`render_api/site_http.py` `_headers`), which
remains set and unchanged. The observable PUBLIC edge header is
`private, no-cache, no-store, max-age=0, must-revalidate`: the
public page is served by the web app's force-dynamic App-Router
page (`apps/web/app/[...sitePath]/page.tsx`,
`export const dynamic = "force-dynamic"`), and Next.js emits its
own no-cache default on dynamic page responses, which does not
propagate the internal fetch's header to the client. The observed
value is a strict superset of `private, no-store` in no-cache
semantics (no storage, zero max-age, mandatory revalidation), so
the preserved behavior — public HTML is never served from any
cache — holds more strongly than the literal string states. The
order's non-goals forbid the only ways of making the edge emit
exactly `private, no-store` (web-layer route/renderer surgery or a
cache introduction), and "PRESERVES + PROVES the current headers"
is the stated semantic unit. The E2E therefore pins the
byte-exact observed edge value (a regression anchor for the
preserved no-cache behavior); no product file was changed. If
strategy or the human requires the edge to emit exactly
`private, no-store`, that is a separate ordered web-layer change.
Observed in compose-smoke Run 1 (spec-pin error on the literal
string), corrected to the observed value, and Run 2 green.

### Mandatory adaptations (no product-semantics change)

All adaptations are mandatory registry/test adaptations of the same
class as the 083/2 registry-durability adaptations:

1. `db/privileges.py` (2 spots, +12/-2): registry table-grant
   expectation + both function EXECUTE grants in
   `REVIEW_WORKER_FUNCTIONS` (GRANT argument signatures `integer`
   and `bigint, text`). Third such registry-durability adaptation
   in the 082/083 line (after 082/1's and 083/2's).
2. `bootstrap/service.py` (+1): `074_001` in the
   downgrade-compatibility revision set.
3. `test_foundation_contract.py` (+1): built-wheel package
   file-list pin gains
   `slaif_agent_site/review_worker/outbox_consumer.py`.
4. `test_review_worker.py` (+4): loop-test fakes answer
   `slaif_cache_outbox_claim` with no pending rows (recorded in
   the store); job-claim/heartbeat/terminal fake behavior
   unchanged.

## Acceptance-criteria evidence

### Criterion 1 (074_001 round trip; exact grant pins; bootstrap
set)

PASSED (local). `test_074_001_round_trip_proves_073_001_state`:
upgrade `073_001` -> `074_001` clean (head `074_001`); downgrade
clean; post-downgrade query snapshot (columns of
`control.cache_outbox`, table grants per role, function
existence + ACLs) byte-equal to the `073_001` baseline — the four
columns absent, the UPDATE grant absent, both functions absent;
re-upgrade reproduces the first upgrade state exactly. Both
functions SECURITY DEFINER, `search_path = pg_catalog`,
`OWNER slaif_owner`; grant pins as ordered; bootstrap revision set
contains `074_001`.

### Criterion 2 (grant surface: exactly the new grants)

PASSED (local). `test_grant_surface_delta_vs_083_1_baseline`:
delta vs the `073_001`-head migration-applied state is exactly
(1) `slaif_review_worker` UPDATE on `control.cache_outbox`,
(2) EXECUTE on `slaif_cache_outbox_claim(integer)`, (3) EXECUTE on
`slaif_cache_outbox_consume(bigint, text)`; nothing else changed;
function ACL roles exactly `{slaif_owner, slaif_review_worker}`;
role memberships unchanged. (Function ACLs from
`pg_proc.proacl` — portable PG14-18, since PG16 moved function
ACLs out of `pg_class`.)

### Criterion 3 (claim: id-order, disjoint, limit gate, 25-budget)

PASSED (local). `test_claim_id_order_disjoint_concurrent_and_limit_
gate`: id order; two concurrent claims (barrier, two open
transactions, max_size=2 pool) DISJOINT; `p_limit` 0/65/NULL ->
`OUTBOX_CLAIM_LIMIT_INVALID` (22023), no rows touched.
`test_attempt_budget_abandons_row_at_25`: 25
claim-without-consume cycles; attempt 26 claims no rows
(`attempt_count = 25`, `consumed_at IS NULL`, `last_attempt_at
NOT NULL` — terminal abandoned, operator-visible).

### Criterion 4 (consume: idempotent; terminal states exact)

PASSED (local). `test_consume_idempotent_replay_changes_nothing`:
replay returns 0 rows, row byte-unchanged.
`test_revision_relation_terminal_states` + corrupt round:
CONSUMED (`last_error` NULL), SUBSUMED, PAYLOAD_INVALID (24
variants), REVISION_AHEAD — all terminal, dead-letters never
re-claimed.

### Criterion 5 (crash semantics: re-claim; exactly once in
effect)

PASSED (local).
`test_crash_between_claim_and_consume_processed_exactly_once`:
claim commits the attempt increment; simulated death (no consume);
re-claim with incremented attempt; single `consumed_at` in the
end.

### Criterion 6 (consumer loop: no listener, gating pinned, existing credential)

PASSED (local). `test_outbox_round_due_first_run_and_interval`,
`test_consumer_settings_defaults_and_bounds`: first run on start,
interval gating, update-on-failure, batch bounds (1..64), poll
bounds (0.1..60), defaults 5.0/8;
`REVIEW_WORKER_OUTBOX_MAX_ATTEMPTS == 25` == SQL constant (regex
pin). Compose smoke: the worker runs the round in-process under
the `slaif_review_worker` credential — the outbox rows were
consumed within the bounded 30 s E2E poll (no listener;
`review-worker-media-boundary: OK` unchanged).

### Criterion 7 (R3 public-surface E2E pins at the exact head)

PASSED (local, compose smoke Run 2, project
`slaif007outbox0833b`): public HTML `Cache-Control` byte-exact
(per D-1); `<img class="sl-image" src="/media/public/sha256/{h2}/
{h2}/{h64}">` exact; media fetch 200 + body re-hash +
`Cache-Control` exactly `public, max-age=31536000, immutable`;
outbox consumed within the bounded poll (`attempt_count >= 1`,
`last_error IS NULL`, exactly one row). Post-accept-discard
sequence: public HTML byte-identical (nonce-normalized) carrying A
not B; A media 200 byte-identical immutable; B media
`private|no published_at`; outbox `0|1`; revision `+1`; audit
`1|0`; B capability revoked; B job `SUCCEEDED`. (The exact-
`private, no-store` literal deviation is documented in D-1.)

### Criterion 8 (R4: all 8 fault cases; coherence)

PASSED (local). All 8 ordered cases + outbox/accept coherence
(fault-first rollback leaves 0 rows; healed retry exactly 1;
duplicate accept 409 `WORKSPACE_NOT_IN_REVIEW` adds none) — see
"Local verification / R4 fault suite" for case-by-case outcomes.

### Criterion 9 (R5 durable form; F3 flip; adversarial grep)

PASSED (local). Four surfaces flipped (F3: every `083-2-a`
"in flight" reference -> PR #101 / `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`
/ 2026-10-06T04:36:59Z, incl. the MVP-CONTRACT-AUDIT revision
line); 083/3 in flight at `083-3-a`; 083 PARTIAL; MVP NOT
COMPLETE; adversarial grep returns only the four intentional
`083-3-a` references (command + result under "Changes made" 8).

### Criterion 10 (R6 byte-identity)

PASSED (local). `git diff base..D -- contracts/ packages/` empty;
`infra/nginx/` empty; `apps/web/` empty; `compose.yaml` empty;
all three generator `--check` runs zero-diff; Agent route policy
197/35 unchanged; web route inventory unchanged (`pnpm build`
identical route list). The 47-path strip-identity is re-proven by
strategy at both base and head (contract bytes unchanged).

### Criterion 11 (budgets honest; trigger; CLOSURE_ONLY; full CI)

PARTIAL. Budget table above (honest, itemized); REVIEW TRIGGER
NOT FIRED (6 < 20); CLOSURE_ONLY never entered. Full CI roster:
19/20 required checks SUCCESS at the report head; `Supply-chain
evidence` FAILED for the out-of-scope environmental reason
documented under "GitHub CI / required checks" — this is the
single unmet criterion and the reason for the PARTIAL status.

## Local verification

Exact commands and outcomes (repo root, final tree; uv 0.12.5,
Node v24.14.1, pnpm 11.22.0, TypeScript 6.0.3):

```text
python -m compileall -q tools tests/repository            OK
python -m unittest discover -s tests/repository -p
  'test_*.py'                                             Ran 71 tests in 0.357s — OK
python tools/check_repository.py                          PASS repository policy
python tools/check_mermaid.py                             PASS Mermaid rendering: 16
                                                          diagram(s) in 3 file(s);
                                                          533 Markdown file(s)
                                                          scanned; CLI 11.16.0
uv run --frozen ruff check
  services/backend tests/repository tools                 All checks passed!
uv run --frozen ruff format --check
  services/backend tests/repository tools                 331 files already formatted
uv run --frozen mypy                                      Success: no issues found
                                                          in 310 source files
uv run --frozen pytest services/backend/tests/unit
  tests/repository -q                                     788 passed, 3 warnings,
                                                          26 subtests passed in
                                                          36.11s (0 failed)
uv run --frozen pytest services/backend/tests/integration
  -q                                                      320 passed in 3164.76s
                                                          (0:52:44) (0 failed)
uv run --frozen pytest
  services/backend/tests/integration/
  test_cache_outbox_consumer.py -q                        50 passed in 102.69s
                                                          (0 failed)
uv run --frozen pytest
  services/backend/tests/unit/test_route_policy.py -q     9 passed (197 agent /
                                                          35 control totals)
uv build --out-dir /tmp/slaif-agent-site-distributions    slaif_agent_site-0.0.0.
                                                          tar.gz + -py3-none-any.whl
python -m slaif_agent_site.{control_api,editor_api,
  agent_api,render_api,mcp_adapter,media_service,
  review_worker,scheduler,media_gc,bootstrap} --check    10/10 CHECK_OK
  (exit 0; binds no port; no DB/job/bootstrap mutation)
node --version / pnpm --version                           v24.14.1 / 11.22.0
pnpm install --frozen-lockfile                            Already up to date
pnpm lint                                                 PASSED
pnpm format:check                                         All matched files use
                                                          Prettier code style!
pnpm typecheck                                            PASSED (web + browser-
                                                          worker)
pnpm test                                                 33 passed (3 files)
pnpm build                                                PASSED (route inventory
                                                          unchanged; zero new
                                                          routes)
pnpm licenses list --json                                 8 license groups, all
                                                          permissive: MIT 207,
                                                          Apache-2.0 20, ISC 10,
                                                          CC-BY-4.0 1,
                                                          BSD-2-Clause 6,
                                                          BSD-3-Clause 3,
                                                          BlueOak-1.0.0 1,
                                                          0BSD 1 (unchanged vs
                                                          base; no new deps)
uv run --frozen python -m
  tools.contracts.generate_agent_openapi --check          agent-openapi: OK
                                                          contracts/openapi/
                                                          agent-v1.json (zero-
                                                          diff; also
                                                          component-catalog: OK)
uv run --frozen python
  tools/generate_component_catalog.py --check             component-catalog: OK
                                                          catalog-v1 Python/
                                                          TypeScript semantic
                                                          equality (zero-diff)
uv run --frozen python
  tools/generate_design_system.py --check                 design-system: OK
                                                          (zero-diff)
git diff base..D -- contracts/ packages/                  EMPTY
git diff base..D -- infra/nginx/ apps/web/ compose.yaml   EMPTY
npx --yes markdownlint-cli2@0.23.2 (report content)       0 issues (pre-publication
                                                          draft; the published
                                                          file is byte-identical;
                                                          the full-glob run at
                                                          head is re-run by the
                                                          Markdown CI check)
```

R4 fault-suite case-by-case (all PASSED):

1. `test_074_001_round_trip_proves_073_001_state` — round trip (criterion 1).
2. `test_grant_surface_delta_vs_083_1_baseline` — grant-surface delta (criterion 2).
3. `test_claim_id_order_disjoint_concurrent_and_limit_gate` — id order, disjoint concurrent, limit gate 0/65/NULL (criterion 3).
4. `test_crash_between_claim_and_consume_processed_exactly_once` — crash semantics (criterion 5).
5. `test_consume_idempotent_replay_changes_nothing` — idempotent consume (criterion 4).
6. `test_corrupt_payloads_terminal_dead_letter` — 24 corrupt variants, terminal PAYLOAD_INVALID, never re-claimed (criterion 4).
7. `test_revision_relation_terminal_states` — CONSUMED/SUBSUMED/REVISION_AHEAD exact (criterion 4).
8. `test_attempt_budget_abandons_row_at_25` — 25-budget abandon (criterion 3).
9. `test_outbox_accept_coherence` — 0 rows on rolled-back accept; exactly 1 on healed retry; duplicate accept 409 adds none (criterion 8).
10. `test_evaluate_outbox_row_matrix` — ~40-param pure matrix, every branch.
11. `test_outbox_round_due_first_run_and_interval` + `test_consumer_settings_defaults_and_bounds` — gating pins (criterion 6).
12. `test_outbox_max_attempts_constant_matches_sql_budget` — 25 == SQL constant.

## Compose smoke

Disposable compose project `slaif007outbox0833b` (public NGINX
edge, `compose.yaml`; no compose file, mount, or env change in
this PR — `git diff base..D -- compose.yaml` empty), exact command
`sh tools/compose/smoke.sh slaif007outbox0833b` (repo root; log
`/tmp/compose-smoke-0833b.log`). Honest run history:

- Run 1 (`slaif007outbox0833`, log `/tmp/compose-smoke-0833a.log`):
  FAILED at the browser stage — `browser-e2e: FAILED
  project=accept-lifecycle contract=positive ... line=567
  column=51` (`expect(...cache-control...).toBe("private,
  no-store")`, received `"private, no-cache, no-store, max-age=0,
  must-revalidate"`). Root cause: a spec-pin error, NOT a product
  defect (Deviation D-1). No product change; the pin was
  corrected to the byte-exact observed edge value.
- Run 2 (`slaif007outbox0833b`, final tree): `compose-smoke: OK`,
  exit 0. Full 19-project E2E roster terminal and green: setup=1
  governance=1 preview=1 preview-filtering=1 stable-devices=6
  agent-sessions=2 agent-workspace-puck=2 freeze-review-snapshot=1
  review-surface=1 accept-lifecycle=1 discard-lifecycle=1
  media-publication=1 (`compose-e2e: OK projects=19 ...
  artifacts=disabled`); 36 `browser-e2e: PASSED` contracts, 0
  FAILED — including `accept-lifecycle` positive (criterion 7
  pins) and `discard-lifecycle` "post-accept discard preserves the
  published canonical (083/3)" (criterion 7). Worker readiness
  unchanged: `review-worker-media-boundary: OK
  dsn=0400:uid10001 root=0700:uid10001`. Post-E2E stages green:
  `public-agent-restart-audit: OK ... rows=3`; `media-e2e: OK
  edge=nginx upload=validated-private-read=byte-identical
  finalization=public-read=byte-identical immutable-cache=verified`;
  `governance-e2e: OK ...`; `governance-restart: OK ...`;
  `negative-bootstrap: correctly blocked`; Apache `Syntax OK`;
  nginx config test successful; `browser-artifact-revoked: OK
  status=401 bytes=absent`; packaging suite `Ran 49 tests ... OK`.
  Baseline-relative: no new wiring — review-worker mounts/env
  unchanged, E2E roster unchanged at 19.

## GitHub CI / required checks

Exact 20-check roster: the 15 `CI`-workflow checks (Dependency
review, Markdown, Mermaid, Node contracts, Python 3.12/3.13/3.14
quality and package, Repository policy, Compose and edge
packaging, Foundation PostgreSQL 14/15/16/17/18, Supply-chain
evidence) plus the `CodeQL` workflow's `CodeQL`,
`Analyze (actions)`, `Analyze (javascript-typescript)`,
`Analyze (python)`, and `Detect supported languages` checks.
(Branch pushes do not trigger the `CI` workflow — its `push`
trigger is `main` only; every branch-state below is a
`pull_request` run on the objective PR.)

Honest run history (every run, every failure, every re-run):

- Run 1 (T push, head `5dbc7300f6c639fc8ba419098434dd07e2877a9a`,
  2026-10-06T05:19:42Z): CI run 37417974368 `completed success`
  (14m48s); CodeQL run 37417974312 `completed success` (1m59s).
  20/20 terminal green on the transcript-only tree.
- Run 2 (I+D push, head `49b3ac59e8882e6bfb6f435dab7c179d06a29c99`,
  2026-10-06T07:20:38Z): CI run 37429064428 — 14/15 CI checks
  SUCCESS: Dependency review (9s), Markdown (11s), Mermaid (44s),
  Node contracts (2m30s), Python 3.12/3.13/3.14 quality and
  package (39s/54s/53s), Repository policy (9s), Compose and edge
  packaging (11m39s), Foundation PostgreSQL 14/15/16/17/18
  (14m32s/14m16s/14m29s/12m36s/14m40s); CodeQL run 37429064412
  `completed success` (2m2s): CodeQL (2s), Analyze (actions) (35s),
  Analyze (javascript-typescript) (1m9s), Analyze (python) (1m50s),
  Detect supported languages (6s). **FAILED (1/15 CI checks):
  `Supply-chain evidence` (job 112155381893, 11m2s)** — exact
  signature, after trivy `Vulnerability database updated to
  latest version!`: `supply-chain-evidence: ERROR:
  browser-worker: unexcepted Critical vulnerabilities:
  CVE-2026-103628` (exit 1).
- No re-run was performed. The order's single documented
  flake-class re-run was deliberately NOT used: the failure is
  deterministic (the CVE remains in the trivy database), so an
  unmodified re-run cannot change the result.

Diagnosis of the failure (out of scope for this order):

- CVE-2026-103628 (NVD, CVSS 9.6 CRITICAL, published 2026-10):
  "Out of bounds write in WebGL in Google Chrome prior to
  154.0.8037.97 allowed a remote attacker to execute arbitrary
  code outside the sandbox via a crafted HTML page (Chromium
  security severity: Critical)."
- The flagged component is the pinned Chrome for Testing inside
  the browser-worker image (`ms-playwright/chromium-1689415`,
  Chrome 153.x — below the fixed 154.0.8037.97). This PR's diff
  does not touch the browser-worker, its Dockerfile, its image
  pin, any lockfile, or any supply-chain file (`tools/supply_chain
  /*`, `supply-chain/*`, `.github/workflows/*` byte-unchanged).
- Environmental drift, not a regression: the same byte-identical
  browser-worker image PASSED this exact check on main at the
  083/2 merge (CI 37414554303, `completed success`) and on this
  branch's T push (CI 37417974368, `completed success`, Run 1
  above); the only variable between those runs and Run 2 is the
  trivy vulnerability-database update that picked up the newly
  published CVE.
- The fix is a browser security refresh (CFT pin >= 154.0.8037.97
  plus the supply-chain identity constants: Chrome version,
  executable SHA-256, source archive hash/URL — the 078-3 /
  078-6 / 079-2-g/h pattern) or a time-bounded documented
  vulnerability exception (`supply-chain/
  vulnerability-exceptions.json`, 072-i/j/n pattern); both are
  explicitly outside this order's R8 ("no lockfile, CI-workflow,
  or supply-chain file changes") and are not executor authority.

All required green at drafting: NO — 19/20 SUCCESS, 1 FAILURE
(Supply-chain evidence, environmental, as above). Strategy
independently waits/verifies the report-only SELF head; the
report-only commit may trigger fresh checks, which will carry the
same browser-worker CVE finding until the image is refreshed or
excepted.

## Local setup / dependencies

- Disposable VM (passwordless sudo) per the constitution; system
  PostgreSQL 17 client against a local PostgreSQL 16 test
  instance (127.0.0.1:5432, disposable per-test
  `slaif_test_*` databases, fake `fixture-*`/`qualification-*`
  credentials only); no production systems, data, or credentials
  touched. Any `oap_dbg*` scratch databases were cleaned before
  the integration run.
- Python: uv 0.12.5 frozen (`uv.lock` byte-unchanged, R8); Node
  24.14.1 / pnpm 11.22.0 frozen (`pnpm-lock.yaml` byte-unchanged,
  R8). TypeScript 6.0.3.
- Docker for the Compose smoke (public NGINX edge, disposable
  projects `slaif007outbox0833`/`slaif007outbox0833b`, torn down
  by the smoke cleanup trap); Playwright browsers for E2E.

## Documentation

The four R5 surfaces updated in commit D (itemized under
"Changes made" 8). No architecture/constitution/protocol edits
(none required by this order). Implemented vs planned
distinguished in all four surfaces (083/3 in flight at `083-3-a`;
084+ planned; objective 083 PARTIAL; contractual MVP NOT
COMPLETE).

## Safety and scope confirmations

- No secrets in code/docs/tests: all test credentials are
  generated `fixture-*` values or fake placeholders; no
  capabilities, cookies, DB URLs, or private artifact URLs appear
  in the diff.
- No production access: integration runs on disposable local
  PostgreSQL; the Compose smoke on disposable projects; no
  production systems/data/credentials/Docker-socket access.
- R8 hard constraints (byte-identity and no-touch):
  - Lockfiles / CI workflows / supply-chain files: `uv.lock`,
    `pnpm-lock.yaml`, `.github/workflows/*`,
    `tools/supply_chain/*`, `supply-chain/*` byte-unchanged
    (verified by base->head diff: none of them appear).
  - Agent surface: `contracts/openapi/agent-v1.json`, the
    component catalog, and the design system zero-diff (R6);
    Agent route policy untouched (197/35 pinned); no new HTTP
    routes anywhere (web/renderer/Puck files byte-unchanged;
    nginx byte-unchanged).
  - No fetch-time canonical-reference gate (079/1 semantics
    preserved); no media GC / staging cleanup; no new outbox
    event kinds (`WORKSPACE_ACCEPTED` only); no
    freeze/snapshot/read-model/re-review/selective-accept change
    (`024_001` stub untouched); no MCP work; no dependabot
    incorporation; no new dependencies; no new compose
    mounts/env/services; no renderer or Puck behavior change; no
    physical content-model schema change.
- Scope: the diff touches only the itemized budget files; the
  strategic order file and `oap/active` are committed exactly as
  activated (transcript T) and never edited afterwards.
- Unrelated files changed: NO. Production systems accessed: NO.
  Required tests skipped/not run: NO (the full local suites and
  the 19-project E2E roster ran; the only not-green item is the
  external CI check documented above). Scope deviation: D-1 only
  (documented). Extra objective PR: NO. Coding-agent merge: NO.
  Activated order/active edited: NO. Report commit changes only
  this report: YES (verified: the SELF commit's sole path is
  `oap/reports/083-3-a-cache-outbox-consumer.md`).

## Known limitations / blockers

1. BLOCKER (external, out of scope): `Supply-chain evidence` CI
   fails at the report head because the newly published
   CVE-2026-103628 (Critical, Chrome <154.0.8037.97) is flagged
   against the byte-unchanged pinned browser-worker image. It
   blocks the R7.3/criterion-11 20/20-green requirement and the
   PARTIAL->COMPLETE upgrade. Unrelated to this diff; requires a
   strategy-issued browser security refresh (CFT pin >=
   154.0.8037.97 + identity constants) or a time-bounded
   documented exception.
2. Discarded workspaces' private staging bytes remain GC-
   reclaimable orphans (the 083/2 limitation carries over
   unchanged; media GC is Objective 089 territory).
3. No fetch-time canonical-reference gate on public media
   (explicit non-goal; the merged 079/1 finalize-time gate +
   content-addressed immutable reads are the
   architecture-supported form).
4. In this deployment the consume action is an explicit no-op
   against the (nonexistent) public edge cache; if a public edge
   cache is added later, the consumed/outbox contract is the hook
   point.
5. Abandoned rows (25-attempt budget) are operator-visible via
   `last_attempt_at`/`attempt_count` but carry no alerting (no
   scheduler/GC wiring is in scope for 083).

## Recommended strategic follow-up

- Issue a bounded "browser security refresh" order (the 078-3 /
  078-6 / 079-2-g/h pattern) qualifying Chrome for Testing >=
  154.0.8037.97 and updating the supply-chain identity constants
  (Chrome version, executable SHA-256, source archive hash/URL);
  after it merges to main, this unmodified branch's CI can be
  re-verified (or the branch synced to the new main), and the
  083-3-a report's PARTIAL criterion 11 can be re-attested.
  Alternatively, if strategy deems the CVE non-exploitable in
  this deployment (browser worker is sandboxed, observation-only,
  never public-facing), a time-bounded documented exception in
  `supply-chain/vulnerability-exceptions.json` (the 072-i/j/n
  pattern, max 90 days) is the smaller bounded order. Strategy
  decides; the executor does not take either action unilaterally.
- Once 083/3 is accepted and merged, numeric Objective 083 may be
  reclassified COMPLETE per the order (strategy verifies the
  resulting evidence independently).
- 084 (conflict-safe review lifecycle) can build on: the durable,
  terminal-state outbox contract (`consumed_at`/`last_error`
  taxonomy: NULL = CONSUMED, `SUBSUMED`, stable dead-letter
  codes), the retry/abandon budget semantics, the 083/2 conflict
  remedy, and the public-surface regression anchors (no-store
  HTML, immutable media, byte-identity across post-accept
  discard); `agent_state.promotion.get_conflicts` (retained from
  083/2) remains the conflict-detection entry point.

Report publication commit: SELF
