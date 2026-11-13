# OAP Coding-Agent Report — 083-11-a

## Work order

- Identifier `083-11-a` (increment-qualified: objective 083, increment 11, round a); work-order file `oap/orders/083-11-a-trusted-mutation-completions.md` (249 lines), committed byte-exact with this round
- PR mode: CREATED_NEW_PR

## Status

COMPLETE — all P1..P6 and C1..C6 criteria executed; full local backend 412 PASS on final source with direct native 0; initial full CI on implementation head `5af201c` 30/30 SUCCESS (CI 43496189085, CodeQL 43496188960, ROOT-verified). The final report-only head (SELF) still requires its own full 30/Compose/fresh-six-image CI evidence — pending at report time, not passed. Not strategic acceptance: ROOT reviews/merges.

## Executive summary

The journal is scoped completion provenance — no pending-U, graph, manifest, or D5 completion is claimed.

Adds trusted mutation completion provenance (migration 078): a durable owner-only `audit.mutation_completion` journal for all three audit families (`agent`, `human_editor`, `media`) and all deployed completion variants, with global operation identity (sha256 request identity; the raw idempotency key is never persisted), `completed`/`no_effect` dispositions, and COW-context binding in the private helper. Bootstrap refuses downgrade traversal through the 078 feature before any marker/COW effect (version-independent feature-presence check; 077/v2 refusals intact). The prelocked COW session wrapper is repaired to preserve the original body error/cause, keep live unlock failures visible, and release the pool reliably after actual connection death. Six new test modules (C2..C6) plus twelve head-compat/preservation test updates, CI Group B wiring for five unfiltered modules with policy negatives, and current docs/ledger updates. 083 remains PARTIAL.

## Authoritative GitHub state

- Repository: <https://github.com/ulfe-lmi/slaif-agent-site>
- PR117 <https://github.com/ulfe-lmi/slaif-agent-site/pull/117> state OPEN, DRAFT (reviewable delivery; CI parallel)
- Base `main` @ `e46ac542786e35e8c58eab507d7cfff547e74aff` (PR #116 merge, verified remote)
- Starting remote SHA (round start): `e46ac542786e35e8c58eab507d7cfff547e74aff`
- Branch `oap/083-11-a-trusted-mutation-completions`; implementation SHA `5af201c33a33464496a8d3679a12c0237ee4d5a7` (sole parent `e46ac542…`); 1 implementation commit pushed; report parent = implementation SHA
- Report publication commit: SELF; new PR this round: YES (#117); merge performed: NO

## Changes made (grouped, `e46ac542..5af201c`; 32 files, 7676+/109−)

- **Product (3):** `db/alembic/versions/078_001_trusted_mutation_completions.py` (new, 607 L: journal DDL + owner-only helper with site/reservation/COW-GUC validation and core-sha256 identity, CREATE OR REPLACE rebind of all six completion variants, downgrade refusal); `bootstrap/service.py` (+35: early feature-presence downgrade refusal); `agent_state/locks.py` (+132/−17: body-error/cause capture, strict live-unlock propagation, real-dead-connection guard, reliable pool release).
- **Tests new (6):** `test_mutation_completion_semantics.py` 414 L; `test_mutation_completion_authority.py` 1499 L; `test_trusted_completion_late_failure.py` 856 L; `test_trusted_completion_producer_families.py` 1157 L; `test_trusted_completion_upgrade_preservation.py` 1558 L; unit `test_agent_locks.py` 411 L.
- **Tests modified (12):** media isolation +377 (mixed human/agent completion oracles on the 3 existing tests); migration preservation +49/−10 (test-only 077 pin adapter; historical 076→077 real-operator proof kept at a real released 077 stage); database_bootstrap +69/−29; head-compat in `test_agent_page_style`, `test_cache_outbox_consumer`, `test_control_database_integration`, `test_human_agent_session_control`, `test_real_human_discard`, `test_editable_domain_proof`, `test_media_workspace_privileges`; unit `test_control_database.py`, `test_foundation_contract.py`.
- **CI (2):** `ci.yml` (+12/−2: five unfiltered new module paths appended to Group B PG14..18; selectors/matrices/check names/30 min/aggregator unchanged); `tests/repository/test_foundation_ci.py` (+52/−3: exact command lists + omission/selection negatives).
- **Docs (5):** `docs/DATABASE_BOOTSTRAP.md`, `docs/OPERATIONS.md`, `docs/SECURITY.md`, `docs/TESTING.md`, `migrations/bootstrap/README.md`.
- **OAP (4):** order (new, 249 L), `oap/active` (083-10-b → 083-11-a), `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md` (current-truth refresh: 083/10 merged in PR #116 at `e46ac542` on 2026-11-13; 083/11 in flight; 083 PARTIAL; historical MVP-CLOSURE-AUDIT untouched).

## Acceptance-criteria evidence (P1..P6, C1..C6)

### P1..P6 (product)

- P1 durable journal: `audit.mutation_completion` owner-only (no PUBLIC/role grants; helper EXECUTE owner-only) — C4 10-role DML/helper denial cases; fresh-install privilege assertions in `test_mutation_completion_authority.py`.
- P2 all variants rebound: all six completion bodies (agent page/navigation/theme/media, human editor, legacy 10-arg) call the helper; legacy direct-completion case in `test_trusted_completion_producer_families.py` (real reservation + COW session, no HTTP for that variant by design).
- P3 identity/privacy: `request_identity` = `encode(sha256(convert_to(key,'UTF8')),'hex')`; raw key never persisted (privacy sentinel assertion); replay/mismatch no-effect semantics in `test_mutation_completion_semantics.py`.
- P4 COW context binding: helper compares actual `current_setting('app.session_id',true)`/`('app.operation_id',true)` against the reservation workspace/operation before journal effects; missing/malformed/mismatch negatives in C4.
- P5/P6 bootstrap early refusal + upgrade preservation: feature-presence refusal before marker/COW effects (empty journal counts; later-head ratchet), quiescent 077→078 all-family/ledger/canonical/retained-snapshot byte preservation, pending-refusal case — `test_trusted_completion_upgrade_preservation.py` (7 PASS 47.22 s).
- Pool cleanup repair (bounded, standing repair authority): `locks.py` + unit `test_agent_locks.py` (16 passed, `PIPESTATUS=0`, final reverse-order assert) + real post-INSERT kill/cancel/late-failure with same-pool retry (C5, 5 PASS 48.41 s).

### C1..C6 (tests, focused direct natives, owned ::1:5432 PG18)

- C2 producers: `test_trusted_completion_producer_families.py` 8 PASS 81.12 s (agent/human/media/legacy10/multirow; media family via the extended existing isolation module).
- C3 semantics: `test_mutation_completion_semantics.py` — two actual cases (no-effect/replay/mismatch + media dedupe zero-ops, raw-key privacy sentinel); peer-qualified 2 PASS 21.95 s, integrated byte-exact. The separate 3 PASS 35.79 s result was a different pre-existing smoke subject (theme no-effect + media dedupe), not this module.
- C4 authority: `test_mutation_completion_authority.py` 6 PASS 56.87 s (incl. real blocked cross-family same-op race).
- C5 late failure: `test_trusted_completion_late_failure.py` (3 interruption cases PASS within the 5-case module).
- C6 upgrade: `test_trusted_completion_upgrade_preservation.py` 7 PASS 47.22 s (direct native UNRETAINED on that focused run — pipeline index bug, preserved honestly; module re-covered by the full 412-case run on final source).
- Mixed completion oracles on existing media isolation tests: 3 PASS 30.09 s (peer-qualified, integrated byte-exact).

## Exact tests/results (final source, direct natives)

- Full local backend integration `pytest services/backend/tests/integration -v` (412 cases, owned PG18): 412 passed in 3255.18 s (0:54:15), `PYTEST_PIPE_STATUS=0` (full-integration-attempt1.log) — covers all five new modules and every head-compat update on final source
- unit + repository: `pytest services/backend/tests/unit tests/repository` 897 passed (+29 subtests) 32.84 s, `PYTEST_PIPE_STATUS=0`
- full mypy (clean cache): 329 files, 0 issues, native 0; ruff check/format --check (services/backend tests/repository tools): 351 files, native 0; `uv lock --check` OK; `uv build` (wheel+sdist) OK; 10× process `--check` OK; compileall + check_repository OK; repository unittest discover: 93 OK (CI command policy 22 PASS incl. 3 omission/selection negatives)
- Frozen Node gate, fresh verified toolchain (node v24.22.1 official sha256 `6c172a9a…`; pnpm 11.22.0 corepack hash-pinned): install --frozen-lockfile / lint / format:check / typecheck / test / build / licenses list --json — all rc 0 (node-gate-fresh-attempt1.log)
- check_mermaid (fresh toolchain): PASS, 16 diagrams in 3 files, CLI 11.16.0, rc 0
- markdownlint-cli2 v0.23.2 repo-wide, 634 canonical files (direct node+CLI, no npm/npx): 0 issues, rc 0

## GitHub required checks (head `5af201c`)

Required-check contract: 20 named/app checks + 10 actual PG14..18 children = 30 (incl. CodeQL), plus full 19-project Compose and fresh six-image evidence (the 11 workflow job definitions are not the required-check count). Observed on head `5af201c` (initial run): all 30 required checks SUCCESS — 20 named/app (incl. CodeQL analyses; Compose includes full 19-project and fresh six-image evidence) + 10 actual PG14..18 children (Group A 5 + Group B 5) — CI 43496189085, CodeQL 43496188960, artifact 14072726743 (sha256 `1ce065cf…`); ROOT-verified from the check runs. The final report-only head (SELF) must produce its own full 30/Compose/fresh-six-image evidence — PENDING at report time, never passed; no initial-run archive is reused as final-head proof.

## Local setup / dependencies

uv 0.12.5, `uv sync --frozen --all-groups`; no dependency/lock change — the qualified registry pin `agent-cow-postgresql==0.2.1` (pyproject.toml:22 / uv.lock) is preserved unchanged. Owned disposable PostgreSQL 18.6 cluster (`::1:5432`, datadir `/tmp/oap-083-10-a-pg/pg18/data`) for all integration evidence; fake fixture credentials only. Node toolchain: fresh official v24.22.1 archive (sha256-verified) + pnpm 11.22.0 under an exclusively created owned root with task-local caches.

## Documentation

DATABASE_BOOTSTRAP (078 guard/journal), OPERATIONS (operator downgrade refusal), SECURITY (privilege posture: runtime roles have no journal SELECT/DML nor helper EXECUTE), TESTING (new module inventory, five unfiltered CI modules), bootstrap README (078 semantics); OAP ledgers refreshed to current truth (083 PARTIAL preserved).

## Confirmations

- No human intervention; no secrets, capabilities or preview credentials in diff/logs; local actions targeted identified owned PostgreSQL clusters and owned tool directories only — prior foreign Docker/containerd/implicit-IPv4-DB effects and production classification remain UNKNOWN (retained as recorded; no absence or no-impact is claimed)
- No skips; pending reported as pending; no extra PR; exactly one PR for this increment (#117); no merge/auto-merge (strategy/ROOT only)
- No new CLI/profile/FIFO/order; no adjacent D5/SDK/lifecycle/snapshot-format scope; no product grant weakening; existing release-077 historical proofs pinned, not relabeled

## Limitations / honest bounds

1. C6 retained-snapshot preservation: v2 snapshot is genuinely worker-generated (real freeze claim/run, complete v2 digest, real discard to quiesce); the v1 row is an owner-inserted fixture built with the genuine 075 contract/normalizer/canonical digest over real site rows — not a deployment of the old 075 materializer/runtime; one further legacy row is explicitly labeled unknown/raw-storage preservation.
2. C5 connection-loss case terminates the exact parked runtime backend via the disposable fixture administrator connection (runtime roles deliberately NOSUPERUSER; no product privilege change); earlier injection attempts (5) remain failed at their exact subjects.
3. Terminal replay semantics: post-terminal same-key and fresh-key attempts both 401 `AUTHENTICATION_REQUIRED` (actual product auth, unmodified); pre-freeze ACTIVE replay remains 201/exact original.
4. Legacy 10-arg completion proved via real direct SQL/COW with genuine reservations (no HTTP endpoint exists for that variant; product unchanged).
5. Media completion family covered by the three existing media isolation tests extended with completion/family/reservation/context oracles.
6. Tooling incident (own-mistake, recorded honestly): during incomplete local Node setup, `npm-cli.js` (46 B, sha256 `562e744d2e7be6b0939e8f117ac897616be993efa3a7fe1a7f52303531d48071`) was written at 2026-11-13 19:28:55Z/19:29:24Z into two prior evidence roots: `/tmp/oap-083-9-a/verify/node-v24.22.1-linux-x64/lib/node_modules/npm/bin/npm-cli.js` and `/tmp/oap-083-8-h/node-v24.22.0-linux-x64/lib/node_modules/npm/bin/npm-cli.js`. Pre-write bytes/existence UNKNOWN (not retained); no deletion/reversion/compensation. A separate earlier Mermaid attempt (19:33:53Z) used that repaired old npx tree and passed; the final reported Mermaid check (19:37:53Z) and all Node gates use the fresh verified toolchain, and repo-wide Markdownlint uses the permitted read-only direct node+CLI invocation.
7. Fixture discovery: the generic `test_agent_mutations` seed workspace is HUMAN (024 default `actor_type`) despite its title; Agent cases use dedicated `actor_type=AGENT` fixtures. No auth/069 weakening.
8. Focused-run receipt gaps preserved as-is: C6 module direct native unretained (index-3 pipeline bug); earlier attempt failures retained at their exact subjects; no green-only reruns.
