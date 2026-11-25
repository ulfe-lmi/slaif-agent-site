# 083-12-c — complete reviewed publication and repair the failing gates

- Order: `oap/orders/083-12-c-complete-reviewed-publication.md`
  (9932B/150L, SHA256 `4438585f0e9d4d122ad484d644245fd3b44b07075418a668b3a11b669f016a4e`,
  committed byte-exact with this round's `oap/active` = `083-12-c`).
- Mode: `AMENDED_EXISTING_PR` — PR #118 (OPEN/DRAFT, never merged by the
  executor), branch `oap/083-12-a-reviewed-operation-binding`, base `main`
  `d129c02c9ec398e09f012041d38e39ed9984344d`.
- Starting remote head: `f5c59a795d71cf0b16c2450dccfaf73d7bd753cb`
  (b SELF, sole parent implementation
  `574fc4f28d8bbcc56fbb23f0bdf029e3c9276e15`).
- Literal implementation SHA: `79221f4cbb52ccc4f211df0d80532e7cd9a47939`
  (74 cumulative paths vs base, +16486/−709; pushed and verified remote).
- Report publication commit: SELF
- Result: COMPLETE for c1..c5 and the carried a/b criteria at the
  local-gate and implementation-checkpoint-CI level; the final
  SELF's own CI run (report-only commit) PENDING at publication.
  The implementation head's CI 45558675762/45558675761 is SUCCESS
  across all 20 required matching-app checks, all ten PG14–18
  matrix children (30 check runs), full Compose and fresh six-image
  supply-chain evidence.

## Round c pushed commits (diagnostic implementation checkpoints, then
final implementation head)

1. `521a009` — diagnostic checkpoint (browser gates: Chrome for Testing
   158.0.8127.88 pin/guards + Compose fixture files for c4/c5).
2. `8c6d682` — diagnostic checkpoint 2 (Alpine OpenSSL 3.5.9-r1 pin).
3. `f95cefe` — diagnostic checkpoint 3 (accept-lifecycle delimiter
   fixture + NGINX 1.30.8 base pin).
4. `4ab1ee2` — diagnostic checkpoint 4 (c1/c2/c3 publication, B3 finite
   budgets, Next 16.4.6 pin).
5. `f16a8f4` — diagnostic checkpoint 5 (third-party notices regeneration
   for the Next 16.4.6 closure; OAP current-status references b→c).
6. `79221f4cbb52ccc4f211df0d80532e7cd9a47939` — final implementation
   head (c2 commit-boundary settlement for the SDK state invariant
   and no-transport interface
   faults, closed-pool reconciliation read probe, exact final
   site-lock observer).

## c1 — approval verified in the actual promotion transaction

`accept_job`'s reviewer transaction now re-verifies, under its own row
locks and BEFORE any publication step: the exact workspace→site binding
and PROMOTING status, the site row ACTIVE at the approved base revision
(the active-site preflight can become stale: `slaif_site_archive` holds
the row lock without advancing `canonical_revision`), the durable claim
(status/kind/claimant/attempt/workspace/site), and the EXACT claimed
payload decoded with explicit JSONB types — snapshot id, actor, BOTH
canonical digests as typed strings (a numeric or object digest cannot
publish), and the site id bound in the JSON approval against the
relational job kind. After the real `commit_session`: duplicate-free
exact applied U, correct session/schema, `has_pending_operations IS
FALSE`, and the public pending inspection empty in the SAME
transaction. Stored domain and companion contents, versions, both
canonical digests, strict shapes, approved identities, live U, exact
foundation dependency pairs and the FULL workspace provenance are
re-validated in the locked reviewer transaction (provenance BEFORE
selected-U identity use; the 076 live materializer preflight stays in
its separate scope). Null/malformed/duplicate/mismatched data refuses
before publication (`STATE_DRIFT`/`SITE_REVISION_CHANGED`/
`SNAPSHOT_VALIDATION_FAILED`/`PROVENANCE_VERIFICATION_FAILED`,
fail-closed, no partial state). Receipt, publication, revision,
workspace, job, media metadata and outbox remain one atomic transaction.
Genuine empty U stays legal; legacy receipt IDs remain NULL.

Proven on owned PG18 (final source): the corrected full integration
run below plus the focused between-phase deviations
(`test_real_human_accept.py` T5/T7/T9 family: stale A after B re-claim
leaves B's exact state untouched, stored-payload mutation reaching the
actual reviewer approval gate, exact-publication-facts decode) — all
passed in `primary-c-full-integration-corrected.log`
(453 passed in 4435.90s, rc0).

## c2 — transaction loss vs uncertain outcome

`_reviewer_failure_class` classifies BEFORE any recovery mutation:
transport-grade faults (lost backend, native cancellation, timeout —
including a post-failure rollback masking one in the exception chain)
are `retry` while the native PostgreSQL COMMIT has not run (a native
cancel/backend loss before COMMIT — including after the SDK's
`commit_session` in-transaction application — leaves the native
commit proven absent, so no receipt read) and `uncertain` at the
commit/cleanup boundary; transient SQL faults (55P03/40P01/40001)
keep the bounded retry; server-declared DETERMINISTIC faults
(42P01/42501/P0001, a deferred integrity rejection at COMMIT, the
SDK's post-commit cleanup SQL after a SUCCESSFUL native commit), the
SDK's public state invariant (`CowPromotionStateError` — raised
BOTH before the native COMMIT when the owned transaction ended
unexpectedly and AFTER it when a COW context survives the post-
commit cleanup; the type alone cannot tell the boundaries apart),
and a completed-body `InterfaceError` with NO transport evidence in
its chain are `programming`. Every completed-body fault in the
handled reviewer classes (driver `PostgresError`, `TimeoutError`/
`OSError`, client-mechanism `InterfaceError`, the SDK state
invariant) settles the possible publication durably FIRST (success
ONLY on the exact terminal receipt fingerprint: the exact receipt,
workspace ACCEPTED, job SUCCEEDED, the exact claimed payload and
exactly one exact WORKSPACE_ACCEPTED outbox row); the class selects
only the proven-absence policy (bounded retry for transport
evidence, terminal mark for a deterministic fault). The real
landed-commit recovery is preserved as its separate proof (the
post-commit reset seam and the post-commit state-invariant test
below). Unreadable or contradictory durable state is `unknown` → the explicit nonterminal `DEFERRED`
result (`UNCERTAIN_OUTCOME`) with NO durable write — an unproven
transaction outcome is never labelled a rollback in the structured
finish log. The reconciliation read boundary maps
`asyncpg.InterfaceError` (a sibling of `PostgresError`, e.g. a closed
pool's acquire) to unknown. Bounded retry for real transport-chain
evidence, native cancellation/backend-loss retry, and the exact
receipt recovery are preserved; the SDK is used unmodified (0.2.1
registry wheel).

Proven on owned PG18 (final source): `test_accept_worker_state_error_
proven_absence_terminal_no_retry` (real pre-commit rollback path,
terminal, no requeue, fresh attempt publishes), `test_accept_worker_
state_error_after_landed_commit_recovers_success` (real landed commit,
recovered SUCCEEDED from the exact fingerprint, no second
publication), `test_accept_worker_post_commit_reset_error_recovers_
success` (public pool-reset seam), `test_accept_worker_deferred_commit_
rejection_terminal_no_retry` (fixture-owned deferred UNIQUE at the
native COMMIT), `test_accept_worker_body_deterministic_fault_terminal_
no_retry` (P0001 body guard), `test_accept_worker_lock_timeout_
requeues_then_succeeds` (real 55P03), `test_reconcile_uncertain_
outcome_matrix` (exact fingerprint + every contradiction + the
closed-pool read failure), cancellation/backend-loss witnesses —
all passed in the corrected run (453 passed in 4435.90s, rc0); the
8-case targeted probe batch passed native 0 in 100.65s
(`primary-c2-targeted-probes.log`) before the full corrected run.

## c3 — trusted producer freeze boundary and binding

The actual Control-only constructor acquires the product shared
workspace lifecycle lock (transaction-scoped ShareLock) BEFORE the
ACTIVE/expiry checks and before ANY COW/prospective-completion write;
drain and late-write refusal proven with the real Control login and
public COW session (`test_freeze_drains_open_control_proposal_and_
denies_late_write`, real ExclusiveLock wait on the same bigint key,
role, PID and fixture). The original constructor interface, suppressed
`proposed_side_effect`, narrow resolution/execute grants, stored
site/resource and honest server service identity are preserved; 078
historical bytes unchanged. Exact duplicate-free resource equality at
the trusted SQL boundary: staged object/array/string checks before
shape-specific functions, typed UUID ordering, direct submitted-array
equality against ordered actual stored resources, and the 078
write-time operation-conflict guard (either order, same operation
advisory lock, owner-only INVOKER trigger, no grants). Cross-
site/workspace/principal/family operation collisions from local facts
in both directions; finite work/UTF-8 budgets (16,384 operation/
identity, 65,536 pair, 8 MiB canonical manifest, 1,048,576 provenance
facts) with a cheap pre-serialization lower bound (070's canonical
encoder ASCII-escapes Unicode; the bound is never tighter than the
exact check, so in-budget manifests are never refused), literal
constants in the 079 DDL mirrored in the runtime (boundary sync test),
and named over-limit probes including the below-character/above-
UTF8-byte case. Real trusted-producer freeze/accept, malformed
dependency/identity refusal probes (P0001), sorted-duplicate resource
substitution, distinct-binding trusted rows, oversized array and
budget probes all passed on owned PG18 in the corrected run.

## c4 — real Compose fixture through supported editorial authority

`tools/compose/e2e.sh` now seeds the preview workspace through a REAL
editor session: the fixed 13-argument in-container envelope uses the
installed product `EditorDatabase.request_content_service(...) /
complete_request(...)` seam (public CowSession, real login
verification, trusted editor assertion, idempotency bindings), with
DSNs read in-process inside the already-authorized editor-api
container (never on host `docker exec`/`psql` argv), fixed fixture
SQL/arguments only, and bounded sanitized results. Control's
`slaif_create_human_session` is consumed as `SELECT *` (named
`session_id`), the digest covers the parsed body actually applied
(page/props/redirect arguments bound to the parsed values), `POST
/redirects` asserted at its real 201 (PATCH 200), and the unused
selector slot is required empty for page/composition. The nine overlay
mutations keep the exact page/heading/redirect fixture; parity,
privacy and media assertions are unchanged; owner-only baseline and
post-commit audit reads stay separate.

Proven by CI on the final source: Compose and edge packaging SUCCESS
at `f16a8f4` (run 45554573532, job 139003576950) — all 19 projects /
six engine pairings, the positive B6 companion removal/restore, real
acceptance, the THIRD real media HTTP cycle freezing and accepting the
formerly failing workspace through public NGINX, two separate
sandboxed Chrome worker runs and isolated readiness; Apache config
check and NGINX actual HTTP verified. Re-proven at the final
implementation head: Compose and edge packaging SUCCESS (job
139016811299 in run 45558675762; native log verified: 19
projects/six targets, the exact media test through public NGINX,
two sandboxed worker runs and isolated readiness, Apache syntax).

## c5 — browser-worker Critical scan failure resolved defensively

The 15 Critical findings were the browser-worker's Chrome. The
coordinated pin: official Chrome for Testing Stable
158.0.8127.88 revision 1727472 (Google origin, archive SHA256
`59e3b43f8b3aaa292238fbdcfb36a93127debd53e212510dcdc2cc8812b4b57e`,
208,082,347 bytes, Google MD5 matched; executable member
`chrome-linux64/chrome` mode 0755, 309,493,064 bytes, SHA256
`1ce7865c612bd8a55b4a07b2df89350e408d603a52763b5902b48143b8033903`),
six standalone pin/guard source files, vendor fixed-version and Google
release evidence recorded; the new binary is proven to run through the
worker's OWN launch/readiness/sandbox path in the real Compose run
(two sandboxed runs at f16a8f4). Playwright stays pinned (compatibility
demonstrated; no coordinated change needed). The supply-chain gate's
other findings were repaired the same way: NGINX 1.30.6-r1 (5
Critical) → verified `nginx:1.30.8-alpine3.24@sha256:6437a63b…`
base; Alpine 3.23's missing pinned OpenSSL pair → exact paired
3.5.9-r1 plus the vendor security revisions. The Next closure (7
moderate advisories ending 16.4.4) → Next 16.4.6 (MIT, official dist
integrity `sha512-QZJiYhaZ…x8HwcwtA==`, locked closure limited to
next/@next/env/8×SWC; the two unrelated deprecation annotation lines
restored byte-for-byte; `THIRD_PARTY_NOTICES.md` regenerated and
checked). No severity exception, disablement, skip, stale scan
database, unsupported binary swap or suppression anywhere.

Proven by CI: supply-chain evidence SUCCESS at `f16a8f4` (run
45554573532, job 139003576641) — six actual images, zero Critical /
zero exceptions, all 77 artifact checksums verified, installed CfT
158.0.8127.88 and Next 16.4.6 confirmed in the worker builds
(artifact 14995562818). Re-proven at the final implementation head:
supply-chain evidence SUCCESS (job 139016811739 in run
45558675762; artifact 14997388252: synthetic base/head match, all
77 checksums, six images zero Critical / zero exceptions).

## Carried a/b criteria

R1..R6, B1..B7 and the C-series criteria of the immutable a/b orders
remain in force and were requalified on the final source by the full
integration suite (453 passed in 4435.90s, rc0); the a and b reports
remain the immutable evidence for their rounds.

## Honest failed / repaired record (this round)

1. b-composed Compose quoting (job 136254335916): `psql -Atc` returns
   `|`, the companion split expected tabs → one-line delimiter
   fixture correction (reviewed, applied at checkpoint 3).
2. 15 browser-worker Critical CVEs → CfT 158 pin; 5 NGINX Critical →
   1.30.8 base; absent Alpine OpenSSL r0 pair → 3.5.9-r1 pin
   (checkpoints 2/3).
3. 079 byte-probe stall: 070's canonical encoder is O(n²) per string;
   a multi-MB probe string was pathological before the exact check.
   Fixed with the conservative pre-serialization lower bound (never
   tighter than the exact 070 check); probe requalified in 17.28s.
4. Budget-test fixture bugs (default `ensure_ascii`, 2-byte character,
   PostgreSQL array-literal strings for `uuid[]` parameters) — fixture
   corrections only; the product guards were not changed.
5. Sync-test rendered-SQL containment assertion dropped (its
   `split()` masked spaces inside quoted literals); versioned literal
   equality assertions kept.
6. Foundation public-API contract: `CowPromotionStateError` (used by
   the real accept worker) added to the qualified public surface and
   its doc line.
7. Node gate: `next@16.4.1` 7 moderate advisories (unauthenticated
   public npm bulk endpoint) → bounded 16.4.6 closure refresh
   (ROOT-verified archive/lock/SRI); the failing 16.4.1 run and its
   embedded upgrade nudge (data only, never executed) preserved.
8. `test_same_site_accept_freeze_serialization_both_orderings`: the
   ordering-2 observer matched only the preflight site SELECT, not
   the final reviewer's exact `canonical_revision, status` lock →
   separate precise matcher, both waiter edges preserved (single
   failure of the 451-case pre-fix full run; passed native in the
   corrected probe batch).
9. c2 classifier: a completed-body `CowPromotionStateError` settled
   with requeue-on-absence (re-firing a deterministic invariant), a
   completed-body `InterfaceError` unconditionally `uncertain`, and
   the reconciliation read missing the `InterfaceError` sibling →
   corrected at the final implementation head (this report's
   checkpoint 6), with the native boundary regressions.
10. Environmental (no product change): stale owned-fixture teardown
    residue → fresh owned disposable PG18; `MediaSettings`
    accepts only port 5432 → the owned cluster restarted on the
    exact IPv6 loopback 5432 (data directory preserved, foreign
    services untouched); a mis-named asyncpg exception class in a
    new test → corrected (`SerializationError`).

## Local gates (final source, exact natives)

Owned PG18 (postmaster PID 1170762, uid 1001, `[::1]:5432`, datadir
`/tmp/oap-083-12-c-pg/pg18/data`, owned Unix socket; trust HBA,
superuser `postgres` fixture role, fake fixture password):

- `uv lock --check` rc0; `uv sync --frozen --all-groups` rc0;
  `uv run --frozen ruff check` (services/backend tests/repository
  tools) rc0; `uv run --frozen ruff format --check` rc0 (355 files);
  `uv run --frozen mypy` "Success: no issues found in 333 source
  files".
- `uv run --frozen pytest services/backend/tests/unit
  tests/repository`: 902 passed + 29 subtests, rc0
  (`primary-c2-unit-gate.log`).
- Full frozen integration on the ORIGINAL pre-fix subject (collected
  before the checkpoint-6 runtime change; kept as diagnostic
  evidence): 450 passed, 1 failed in 4323.46s, rc1
  (`primary-c-full-integration.log`) — the single failure is the
  ordering-2 stale-observer test repaired at the final head (item 8
  above).
- 8-case targeted corrected probes (the serialization observer, both
  new state-error boundary tests, the closed-pool reconciliation
  matrix and the four adjacent c2 boundary tests): 8 passed in
  100.65s, rc0
  (`primary-c2-targeted-probes.log`).
- `uv run --frozen pytest services/backend/tests/integration` on the
  CORRECTED implementation (same owned PG18, single runner):
  453 passed in 4435.90s, rc0
  (`primary-c-full-integration-corrected.log`).
- 10 process `--check` smokes: the initial batch recorded all ten
  as FAIL because it invoked the bare system `python` instead of the
  frozen venv (an executor environment error, no product effect; the
  same log's other non-PG checks all passed, NONPG_RC=0); the exact
  frozen retry (`uv run --frozen python -m ... --check`) at 06:25
  produced all ten OK (`primary-c-final-smokes2.log`, SHA256
  `e8169f96c5625f18b8febf91a29fc53a0f5c50d16675ed1f0067d774f02be877`).
  `compileall` rc0; `unittest discover -s tests/repository` 94
  tests OK; `tools/check_repository.py` PASS;
  `tools/check_mermaid.py` PASS (16 diagrams); markdownlint (repo
  config) 0 issues (`primary-c-final-nonpg-gates.log`).
- Node 24.22.1 + pnpm 11.22.0 (pinned, frozen): `pnpm install
  --frozen-lockfile` rc0; `pnpm lint` rc0; `pnpm format:check` rc0;
  `pnpm typecheck` rc0; `pnpm test` rc0; `pnpm build` rc0; `pnpm
  licenses list --json` rc0 (Next 16.4.6 closure;
  `primary-c-final-node-gates.log`).
- `uv build --out-dir /tmp/slaif-agent-site-distributions` rc0
  (sdist + wheel).

## GitHub CI (per-subject runs; GitHub is authoritative)

- b SELF `f5c59a7` — CI 44726202028: 28/30 SUCCESS; Compose
  136254335916 FAILED (the quoting defect, item 1) and supply-chain
  136254335927 FAILED (15 Critical, item 2). The root-preserved
  failure excerpts remain in the c evidence directory.
- `521a009` — Compose 45518298336/138883356506 FAILED before
  application startup (Alpine v3.23 no longer offers the pinned
  OpenSSL pair 3.5.9-r0; item 2).
- `8c6d682` — CI 45521754677: supply-chain 138895089743 FAILED
  (5 Critical in NGINX 1.30.6-r1; exact diagnostic artifact
  14981276305, six raw scans, zero worker Critical).
- `f95cefe` — CI 45526629025: Compose 138911496382 SUCCESS and
  supply-chain 138911495899 SUCCESS (artifact 14982798357, 77
  checksums, six images zero Critical).
- `4ab1ee2` — CI 45553832778: supply-chain FAILED on generated
  `THIRD_PARTY_NOTICES.md` drift after the Next closure pin (exact
  log preserved, SHA256 `c61d58a6…`); superseded.
- `f16a8f4` — CI 45554573532: Compose 139003576950 SUCCESS (19
  projects / six pairings / third real media accept / isolated
  worker / NGINX; Apache syntax) and supply-chain 139003576641
  SUCCESS (artifact 14995562818, 77 checksums, six images zero
  Critical / zero exceptions); CodeQL 45554573533 SUCCESS; all five
  Foundation PG Group B children (PG14–18) FAILED on only the single
  ordering-2 stale-observer test (item 8; all five raw logs
  confirmed; Group A PG14–18 all SUCCESS) — repaired at the final
  head.
- Final implementation head `79221f4` — CI 45558675762 and
  CodeQL 45558675761, both SUCCESS: all 20 required matching-app
  checks, all ten actual PG14–18 matrix children (30 check runs),
  full Compose and fresh six-image supply-chain evidence as cited
  above.

## Grouped cumulative scope (vs base `d129c02c`)

74 tracked paths at the implementation head (+16486/−709);
grouped:

- Migration:
  `services/backend/src/slaif_agent_site/db/alembic/versions/079_001_
  reviewed_operation_binding.py` (+2382) — the only new migration
  (≤078 immutable and byte-unchanged).
- Product: `review_worker/{accept_job,freeze_job,operation_manifest}.
  py`, `agent_state/foundation.py`, `bootstrap/service.py`,
  `control_api/{database,workspace_http}.py`, `db/privileges.py`.
- Web: `accept-action.tsx`, `api.ts`, `review-projection.ts`,
  `review-surface.test.mjs`.
- E2E/Compose/orchestration: `tests/e2e/{accept-lifecycle,
  freeze-review-snapshot,frozen-review-parity,media-publication}`,
  `tools/compose/e2e.sh` (+557), `tools/compose/smoke.sh`,
  `.github/workflows/ci.yml`, `tests/repository/test_foundation_ci.py`.
- Packaging/security pins: `apps/web/Dockerfile`,
  `apps/web/package.json`, `pnpm-lock.yaml`,
  `services/backend/Dockerfile`, `services/browser-worker/Dockerfile`,
  `infra/nginx/Dockerfile`, `infra/postgres/Dockerfile`,
  `supply-chain/policy.json`, `THIRD_PARTY_NOTICES.md`,
  `tests/packaging/test_oci_contract.py`,
  `tests/supply_chain/test_policy.py`,
  `tools/supply_chain/{evidence,policy}.py`.
- Tests: new `test_reviewed_operation_binding.py` (+3944) and
  `test_reviewed_operation_binding_authority.py` (+1789);
  `test_real_human_accept.py` (+2358), `test_freeze_review_snapshot.
  py` (+400), 17 modified integration modules, 3 modified unit
  modules.
- Docs/ledgers: `docs/{SECURITY,TESTING,FOUNDATION_INTEGRATION,
  DEPLOYMENT,SUPPLY_CHAIN,CONFIGURATION,LICENSE_POLICY}.md`,
  `migrations/bootstrap/README.md`, `README.md`,
  `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`, `oap/active`, the a/b/c
  orders, the a/b reports.

## Docs, setup, security, risks

- Docs updated prospectively in the same PR (079 provenance/budget
  semantics, c2 settlement policy and the `CowPromotionStateError`
  public-surface line, CfT/NGINX/Alpine/Next pin evidence, in-flight
  083-12-c truth); immutable a/b history untouched.
- Setup: owned disposable PG18 fixtures only (the stopped
  083-10-a fixture preserved untouched; foreign 127.0.0.1:5432/5433,
  Docker, services and credentials untouched); no global process
  scans; no new external service.
- Security: DSNs never leave the authorized editor-api container
  (no host argv exposure); no new authority except the documented
  worker-only `slaif_review_promotion_receipt_read` SELECT
  definer (079) and the 078 write-time guard (owner-only INVOKER,
  no grants); no secrets committed (fake fixture credentials only);
  all scan findings repaired with coordinated pins, zero
  exceptions/suppressions.
- Risks/remaining: see limitations; final acceptance/merge belongs
  to ROOT.

## Confirmations

- Exact bounded diff on the existing PR/branch; no second PR, no
  merge/auto-merge/close, no history rewrite, no force push.
- No new OAP order, ID, activation, or b-FIFO replay; the c
  handshake was consumed once and the response is sent once at
  delivery.
- No push after this SELF; no scope expansion beyond c1..c5 (the
  Next 16.4.6 closure, notices regeneration and OAP current-status
  references are the ROOT-authorized bounded extensions recorded
  above).
- No production system/data/credential access; no secret in argv,
  logs, URLs or this report.
- Skip/pending/not-run is reported truthfully above; no "all passed"
  beyond the complete claimed sets.
- No D5, 083, MVP or release completion claim; the foundation stays
  registry-only PyPI 0.2.1 with frozen hashes.

## Limitations and remaining acceptance gaps

- The final SELF's own CI (the report-only commit) is PENDING at
  publication; GitHub is authoritative for it and no acceptance is
  claimed (the implementation head's CI is fully SUCCESS as cited
  above).
- The original pre-fix 451-case full run (450 passed, 1 failed,
  rc1) is preserved diagnostic evidence for the single known
  observer defect (item 8), not the final subject; the corrected
  453-case run is the final local PG result.
- Carried from the immutable b report: full semantic causal closure,
  durable snapshot-specific before/after history with first-touch
  baselines, and the remaining D5 work stay required subsequent
  bounded work.
