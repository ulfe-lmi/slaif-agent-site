# 083-12-b — repair exact approval and prospective provenance on PR118

- Order: `oap/orders/083-12-b-repair-reviewed-operation-binding.md`
  (17227B/259L, SHA256 `e0d60027cf31769e2a685ad45391d465daa0546dacb80ecbd22af01af9f5a745`,
  committed byte-exact with this round's `oap/active` = `083-12-b`).
- Mode: `AMENDED_EXISTING_PR` — PR #118 (OPEN/DRAFT, never merged by the
  executor), branch `oap/083-12-a-reviewed-operation-binding`, base `main`
  `d129c02c9ec398e09f012041d38e39ed9984344d`.
- Starting remote head: `99832e7d96da8fab6ee385196df2cd3e4b8c4cf3`
  (a-round SELF, sole parent implementation `c5448be29c9c6c6b454b903dd32a3e65f1fc9d81`).
- Literal implementation SHA: `574fc4f28d8bbcc56fbb23f0bdf029e3c9276e15`
  (17 paths, +2136/−503 over the a SELF; pushed and verified remote).
- Report publication commit: SELF
- Result: COMPLETE for all B1..B7 and the carried R1..R6/C1..C6 criteria at
  the local-gate level; final SELF CI (own 20 named/app + 10 PG children,
  CodeQL, full 19-project Compose, fresh six-image evidence) PENDING.

## B1..B7 evidence (focused natives, owned disposable PG18)

B1 — no private foundation storage inspection: 079 and its helpers read no
`*_changes` table; the a-round membership inference is gone. Proven by
`test_reviewed_operation_binding_authority.py` (6 passed, 88.44s, rc0):
role helper/table/journal denials, allow matrix, both old accept
signatures closed, standalone completion denied.

B2 — product-owned prospective completion at the real producer:
`control.proposed_effect_completion` (owner-only, zero grants) written by
the forward-re-emitted `content.slaif_proposed_side_effect_create` in the
same COW transaction (server operation context, stored site/workspace,
constant producer, service principal = calling login, exact created
resource ids; explicit `created_id` selection preserving the 042 view
re-read contract). Proven by `test_reviewed_operation_binding.py`
(15 passed, 160.13s, rc0): real Control-login public-COW producer
operation, mixed-form U freeze/accept with genuine nine-field and
proposed-effect/v1 records, and four typed forgeries — producer relabel
(`MANIFEST_IDENTITY_MISMATCH` P0001), forged principal (same), extra
resource id (same, canonical sorted form so the writer's field-for-field
binding refuses), owner-forged rows on a journaled op
(`PROVENANCE_CONFLICT` P0003) — each leaving no snapshot/companion/REVIEW
state, then legitimate completion to REVIEW with the exact un-forged
companion. `test_trusted_completion_producer_families.py` (8 cases)
requalified in the full suite.

B3 — complete whole-workspace provenance in the actual freeze
transaction: `freeze_job` invokes `slaif_review_operation_provenance`
under the lock before any U identity use, with
`PROVENANCE_VERIFICATION_FAILED` terminal codes; worker-path refusals
leave no partial state (asserted in the binding module). Known
prospective orphans/conflicts outside U refuse; agent explicit
`no_effect` outside U and honest 078 media dedupe stay legal; truly old
no-journal history stays unknown (authority module).

B4 — exact human approval verified inside the real reviewer transaction:
durable approval types/shape, explicit domain-digest comparison, live
pointer/companion/journal reread under locks, `IS DISTINCT FROM`
null/legacy payload refusals (new cases), duplicate-free exact applied U,
`has_pending_operations IS FALSE`, and public pending-empty inspection
after the real `commit_session` in the SAME transaction. Proven by the
binding accept cases (tampered durable approval refusal) and
`test_real_human_accept.py` (17 passed, 184.08s, rc0).

B5 — cancellation/owned-backend-loss/pool recovery: real late failure,
SQL cancellation, and fixture-owned exact-PID termination all settle with
all-four durable rollback + canonical stability BEFORE retry, then
same-pool exactly-once reuse (binding module, requalified on final
source). No test-control endpoint, SDK patch, or fake promotion.

B6 — companion-less ineligibility in the review UI:
`accept-action.tsx` renders an explicit explanation with the existing
discard / fresh-workspace guidance (no accept control, no re-freeze
promise); `accept-lifecycle.spec.ts` covers it; Node typecheck/lint/test
pass on the final source. Full E2E credit belongs to the final SELF
Compose run.

B7 — Compose media failure root cause and repair: the seed transaction
pinned `app.operation_id` in the shared HUMAN preview workspace and wrote
pending page/composition COW rows plus overlay redirects with NO
078 completion/reservation/family audit; the third real media-publication
accept cycle froze that workspace and the whole-workspace provenance
check correctly refused (`MANIFEST_IDENTITY_MISMATCH`). `tools/compose/
e2e.sh` now seeds through a real editor session with nine definer
envelope operations carrying real digests and journal rows; all 19
projects/six pairings/late-browser/readiness assertions retained.
Throwaway probe: 1 PASSED 6.51s (`b7-probe-attempt13.log`, kept out of
the tree); full Compose still pending for the final SELF.

R1..R6/C1..C6 (carried from the immutable a order): satisfied by the
a implementation and requalified on the corrected source by the full
435-case integration suite below; the a report remains the immutable
evidence for round a.

## New defects found and repaired in this round (honest record)

1. `privileges.py` demanded HARDENED content-schema USAGE for
   `slaif_control` at heads below 079 where the head-gated grant does not
   exist → 45/49 full-suite failures on historical-head reconciles. Fixed
   with a head-aware expectation (missing version fails closed, mirroring
   the 077 worker pattern).
2. 079 producer re-emission: with content COW already enabled (round-trip
   downgrade/re-upgrade; released 077/078 databases reconcile COW before
   any 079 step) the named rowtype `content.proposed_side_effect` points
   at the COW view OID while the 042 function's return type is pinned to
   the pre-swap table OID → `cannot change return type`. Fixed with a
   conditional DROP (only when the stored return-type OID differs from
   the current relation OID) before the re-emit; ownership and the exact
   grant surface are re-established immediately after.
3. `accept_job` early-refusal paths (non-dict payload, digest-shape
   failure) marked the job FAILED without restoring the workspace; now
   restore to REVIEW per the module contract.
4. `slaif_review_operation_identities` producer branch: missing `GROUP BY`
   on an aggregate SELECT (GroupingError on first real execution).
5. Forward-only repair of the 017 `slaif_content_type_update`
   `ct`-declaration defect (42P01 on every call) with a real
   HUMAN-on-AGENT model PATCH regression.
6. Test oracle corrections: production control login now legitimately
   holds content USAGE at the 079 head (resolution only; no table SELECT);
   forgery (c) forged list kept in canonical sorted order so the refusal
   comes from the writer, not client-side shape validation.

## Local gates (final source, exact natives)

Owned PG18 (PID 3397505, uid1001, `::1:5432`, datadir
`/tmp/oap-083-10-a-pg/pg18/data`, re-verified live before use):

- `uv lock --check` rc0; `ruff check` + `ruff format --check`
  (services/backend tests/repository tools) rc0; `uv run --frozen mypy`
  "Success: no issues found in 333 source files".
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  898 passed, rc0.
- `uv run --frozen pytest services/backend/tests/integration` (owned
  PG18): **435 passed in 3898.43s, rc0** (full-integration-attempt2.log).
- 10 process `--check` smokes: all rc0.
- `compileall` rc0; `unittest discover -s tests/repository` 94 tests OK;
  `tools/check_repository.py` PASS; `tools/check_mermaid.py` PASS (16
  diagrams, CLI 11.16.0).
- Node 24.22.1 + pnpm 11.22.0 (fresh peer-provisioned toolchain,
  read-only reuse): `pnpm install --frozen-lockfile` rc0; `pnpm lint`
  rc0; `pnpm format:check` rc0; `pnpm typecheck` rc0; `pnpm test` rc0
  (recursive builds + 8+8+24+19 web/package tests + 36 contract tests);
  `pnpm licenses list --json` rc0. NOTE: the Next.js CLI emitted a
  registry-security advisory nudge for pinned `next@16.4.1` and stopped
  the first build; the build continued via the tool's own one-time retry
  (5-minute TTL) and all Node gates passed. No dependency, lock, or
  policy change in this increment; the advisory is recorded, not
  suppressed, and upgrading Next.js is out of scope for 083/12.
- `uv build --out-dir /tmp/slaif-agent-site-distributions` rc0 (sdist +
  wheel).
- markdownlint (repo config, `--no-globs`) on the four touched docs:
  0 issues, rc0.

## Honest failed / skipped / not-run / pending

- full-integration-attempt1 (pre-fix source): 49 failed, 386 passed,
  3828.96s — single root cause (defect 1 above).
- failed-rerun1: 4 failed, 45 passed, 644.81s — three instances of
  defect 2 plus the stale grant oracle (defect 6); all four repaired and
  requalified.
- forged3-attempt5 (pre-sort): 1 FAILED 12.14s — the unsorted forged
  resource list was refused client-side by the manifest builder instead
  of reaching the writer; fixed, then 1 passed 9.39s.
- node-test attempts 1-2: SecurityFatalError advisory nudge (see above);
  attempt 3 passed.
- NOT RUN locally: full Compose (19 projects/six pairings/three media
  cycles/late browser/isolated readiness), fresh six-image evidence,
  Playwright-through-NGINX browser coverage — these belong to the final
  SELF GitHub run; no local pass is claimed for them.
- GitHub checks for head `574fc4f…`: PENDING (new run). The a-head
  (99832e7) history — 29/30 SUCCESS with Compose and edge packaging
  FAILED (CI 43574529764/job 132385874265) — is preserved in the a
  report and not reused as credit.

## Grouped cumulative scope (vs base `d129c02c`)

49 tracked paths at the implementation commit (+10705/−514); 50 paths
including this report:

- Migration: `079_001_reviewed_operation_binding.py` (+2000).
- Product: `db/privileges.py`, `db/alembic/versions/079_001…`,
  `review_worker/{accept_job,freeze_job,operation_manifest}.py`,
  `bootstrap/service.py`, `control_api/{database,workspace_http}.py`.
- Web/E2E: `accept-action.tsx`, `api.ts`, `review-projection.ts`,
  `review-surface.test.mjs`, `tests/e2e/{accept-lifecycle,
  freeze-review-snapshot,frozen-review-parity,media-publication}`.
- Compose: `tools/compose/e2e.sh`.
- CI: `.github/workflows/ci.yml`, `tests/repository/test_foundation_ci.py`
  (two 079 modules added to the existing PG14..18 Group B children;
  selectors/matrices/checknames/budgets/aggregators otherwise unchanged).
- Tests: new `test_reviewed_operation_binding{,_authority}.py`
  (+2993/+1476); modified 16 existing integration modules + 3 unit
  modules (oracles and B4/B5/B6 coverage).
- Docs/ledgers: `docs/SECURITY.md`, `docs/TESTING.md`,
  `migrations/bootstrap/README.md`, `oap/INCREMENTS.md`,
  `oap/MVP-PROGRESS.md`, `oap/active`, b order.

## Docs, setup, security, risks

- Docs updated prospectively (producer-record provenance, head-gated
  control content-USAGE, B6/B7/017 repair, in-flight 083-12-b truth);
  immutable history untouched.
- Setup: owned disposable PG18 only; no foreign 127.0.0.1:5432, Docker,
  service, or credential action; no global process/listener scans.
- Security: disclosed bounded grant — `slaif_control` direct content
  schema USAGE at and after the 079 head for resolution only (no
  table/sequence/CREATE grants, no data reachability); no other
  authority change; no secrets committed.
- Risks/remaining: full semantic causal closure, durable
  snapshot-specific before/after history with first-touch baselines, and
  full remaining D5 stay required subsequent bounded work; no D5/083/
  MVP/product/release completion is claimed. Final acceptance/merge
  belongs to ROOT; SELF CI may be pending.
