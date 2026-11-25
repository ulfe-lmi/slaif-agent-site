# OAP Coding-Agent Report — 083-12-a

## Work order

- Identifier `083-12-a` (increment-qualified: objective 083, increment 12, round a); work-order file `oap/orders/083-12-a-reviewed-operation-binding.md` (305 lines), committed byte-exact with this round; `oap/active` = `083-12-a` committed unchanged
- PR mode: CREATED_NEW_PR

## Status

COMPLETE — all R1..R6 implemented and all C1..C6 criteria executed locally on
owned PG18; full local backend integration 434 PASS on final source with
direct native 0. GitHub CI (20 named/app checks + 10 actual PG14..18
children + CodeQL + full 19-project Compose/fresh six-image) is PENDING at
report time and authoritative — nothing remote is claimed as passed. Not
strategic acceptance: ROOT reviews/merges.

## Executive summary

Whole-session human acceptance now names BOTH the immutable domain snapshot
and a new immutable `reviewed-operations/v1` companion manifest, created
atomically in the SAME freeze transaction (migration 079; 070..078 immutable).
U is captured from the public qualified 0.2.1 foundation getters
(`get_session_operations` / `get_operation_dependencies`) through the product
`AsyncpgExecutor` on the same connection/transaction under the actual freeze
locks; foundation dependency pairs are captured verbatim and explicitly
labeled (not a complete semantic graph). Two-form trusted provenance: each U
member needs exactly one prospective 078 trusted completion — the nine-field
078 identity or a typed three-field trusted-internal record; whole-workspace
prospective facts are validated before U selection; no-effect-in-U, missing/
mismatched/duplicate/conflicting identities and forged internal records fail
closed. Human acceptance supplies the manifest digest alongside snapshot ID +
domain digest (dual-digest transport through Control request/database/
contracts, review view/form, worker consumers); old inner/outer accept
overloads cannot bypass (IS DISTINCT FROM live-payload comparison — NULL
legacy fields refuse, no silent digest fill — typed refusal, reconcile
revocation). Inside the real public reviewer transaction, approved vs live
operation IDs/foundation pairs/provenance are re-verified and
`committed_operations == U` exactly plus public no-pending confirmation are
required before the business commit; an append-only promotion receipt stores
the exact applied IDs and both digest bindings. R6 rollback/cancellation/
owned-connection-loss/pool-cleanup behavior is preserved and tested. Also:
forward-only repair of the 017 `content.slaif_content_type_update` defect
(missing `ct` FROM-clause entry; real HTTP HUMAN-on-AGENT regression) and
worker login `slaif_review_worker_login` with NOINHERIT direct grants plus
narrow SECURITY DEFINER projections/writer. Full semantic causality closure
and durable snapshot-specific before/after timelines with original first-touch
baselines remain REQUIRED subsequent bounded work; no D5/083/MVP/product/
release completion claim. 083 remains PARTIAL.

## Authoritative GitHub state

- Repository: <https://github.com/ulfe-lmi/slaif-agent-site>
- PR118 <https://github.com/ulfe-lmi/slaif-agent-site/pull/118> state OPEN, DRAFT (reviewable delivery; CI running in parallel)
- Base `main` @ `d129c02c9ec398e09f012041d38e39ed9984344d` (PR117 merge 2026-11-13 20:50:29Z, verified remote)
- Starting remote SHA (round start): `d129c02c9ec398e09f012041d38e39ed9984344d`
- Branch `oap/083-12-a-reviewed-operation-binding`; implementation SHA `c5448be29c9c6c6b454b903dd32a3e65f1fc9d81` (sole parent `d129c02c…`); 1 implementation commit pushed; report parent = implementation SHA
- Report publication commit: SELF; new PR this round: YES (#118); merge performed: NO

## Changes made (grouped, `d129c02c..c5448be`; 45 files, 8922+/476−)

- **Migration (1, new 1687 L):** `db/alembic/versions/079_001_reviewed_operation_binding.py` — reviewed-operations/v1 companion storage + digest binding (snapshot ID/digest/site/workspace + canonical content); freeze-time U capture via public 0.2.1 getters with finite op/edge/identity/byte budgets; two-form provenance validation (whole-workspace prospective scan first); non-bypassable accept (both legacy signatures, IS DISTINCT FROM comparisons, typed refusals); narrow definer projections/writer (review worker + authorized human read); worker login NOINHERIT direct grants; 078 early durable-feature downgrade refusal preserved; 017 CT forward-only repair (signature/grants/result shape preserved); 079 downgrade/pending guards.
- **Product (6):** `review_worker/operation_manifest.py` (new 213 L: manifest build/canonical digest/two-form validation); `review_worker/freeze_job.py` (companion step in the same locked freeze TX); `review_worker/accept_job.py` (dual-digest verification + in-TX R5 checks + receipt); `control_api/database.py`, `control_api/workspace_http.py` (digest transport, read-model manifest projection); `bootstrap/service.py`, `db/privileges.py` (reconcile maps + direct grants).
- **Web/e2e (8):** `accept-action.tsx`, `api.ts`, `review-projection.ts`, `review-surface.test.mjs` (digest transport); 4 e2e specs (accept/freeze/parity/media exercise the new real approval path in CI).
- **Tests (new 2, updated 14):** `test_reviewed_operation_binding.py` (2644 L, 14 cases: C2 family freeze/accept incl. HUMAN-on-AGENT + human media, dedupe/replay/two workspaces/empty U, in-flight drain + later-write denial, re-review/stale-approval refusal, mixed-family superseding/net-zero/multirow, trusted-internal proposal op, forged-internal refusal, legacy/cross-workspace digest denials, unreviewed-pending refusal, cancellation + backend-loss after commit, CT-017 HTTP regression); `test_reviewed_operation_binding_authority.py` (1225 L, 6 cases: 079-head DML/read denials, allow matrix, old accept entry points non-bypassable, R2 discarded-vs-orphan outside-U provenance, envelope/shape/budget/legacy refusals, legacy live payload refusal); `test_freeze_review_snapshot.py` (pre-079 grant stage map, P0002 oracle); upgrade-preservation module extended with 078→079 upgrade + companion NULL/forward cases; read-model/accept/discard/media/bootstrap/foundation-contract units updated.
- **CI (2):** `.github/workflows/ci.yml` + `tests/repository/test_foundation_ci.py` — two new modules appended to the existing GroupB TC set (now seven exact module paths, PG14..18); old selectors/matrices/check names/budgets/aggregators unchanged.
- **Docs (5):** `docs/SECURITY.md`, `docs/TESTING.md`, `migrations/bootstrap/README.md` (two-form provenance, grants, 079 verification semantics); `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md` (083/12 in flight; PR117 accepted recorded; 083 PARTIAL preserved).

Footprint note: order forecast ~20..30 paths / 2000..4500 substantive gross; actual 45 paths / 8922+ is larger due to the CI-wired authority module (1225 L), the 078→079 upgrade-preservation cases, and full dual-digest consumer updates — grouped scope above; no adjacent D5/SDK/lifecycle work.

## Evidence (exact commands, direct natives)

Python gates, clone root, `uv run --frozen`, owned PG18 `::1:5432` (disposable fixture DBs per test):

- `pytest services/backend/tests/integration` → **434 passed, 0 failed, 4097.03s, native 0** (full backend integration on final source). First full run on the prior source: 430 passed / 4 failed, 4098.00s, native 1 — the four exact subjects were this increment's own adapted historical fixtures: (1) A7 media preservation froze at the released 076 head where the current 079-companion worker cannot complete → test now uses real freeze enqueue/claim + the 076 head's own v2 completion definer with the real trusted materializer (same bounded pattern as the 077-era quiescent case); (2-3) read-model test mirrored the product manifest projection without the product's JSON parse and asserted a stale 9-key shape → mirror now parses and the shape asserts the 10-key document; (4) quiescent 077→078 fixture counts (agent audit 1→2, agent idempotency 2→3) did not include the frozen workspace's genuine COW create → oracles corrected with rationale. All four fixes test-side only; no product source change in that round; focused re-runs green (14 passed fixed modules + 1 passed targeted test, native 0), then the full suite re-run green as above.
- `pytest services/backend/tests/unit tests/repository` → 898 passed, 29.16s, native 0
- `ruff check services/backend tests/repository tools` → All checks passed! (native 0); `ruff format --check …` → 355 files already formatted (native 0)
- `mypy` → Success: no issues found in 333 source files (native 0)
- `uv build --out-dir /tmp/slaif-agent-site-distributions` → sdist + wheel (native 0)

Preparation checks: `python -m compileall -q tools tests/repository` (0); `python -m unittest discover -s tests/repository -p 'test_*.py'` (0); `python tools/check_repository.py` (0); `python tools/check_mermaid.py` → PASS 16 diagram(s) in 3 file(s), 644 Markdown file(s) scanned, CLI 11.16.0 (0; fresh verified 083-11 Node toolchain, isolated npm cache, read-only binary reuse); markdownlint-cli2 0.23.2 `--no-globs` repo config on the 3 touched docs → 0 issues (0).

Process smoke: all 10 `python -m slaif_agent_site.<module> --check` → native 0 each.

Focused integration (direct native = PIPESTATUS[0]): binding module 14 passed 155.59s (0); freeze module 20 passed 236.59s (0); authority module 6 passed 68.17s final-source (0); rc1 internal-form 1 passed 15.07s (0); forged-internal 1 passed 12.02s (0).

Node/TS: 8 files changed. Local chain after the last Node edit (02:56): `pnpm install --frozen-lockfile`, `lint`, `format:check`, `typecheck`, `test`, `build`, `licenses list --json` → NODE_GATE_RC=0. No Node file changed since; GitHub CI remains authoritative for Node.

## GitHub checks at publication

PR118 CI running at publication; all checks PENDING. The final report-only
head (SELF) requires its OWN 20 named/app checks + 10 actual PG children +
CodeQL + full 19-project Compose / six stable engine pairings / three real
media cycles / late browser / isolated readiness and fresh six-image
evidence. Nothing remote is claimed as passed here.

## Setup, dependencies, safety

- Fresh standalone clone `/home/janezp/codex-work/slaif-agent-site-083-12-a` from verified remote main; `uv 0.12.5` frozen; owned disposable PG18 fixture `::1:5432` (PID 3397505, owned datadir); no foreign DB/Docker/service actions.
- Foundation `agent-cow-postgresql==0.2.1` PyPI registry pin unchanged (pyproject/uv.lock untouched); no new dependencies; no lock changes; no foundation release or private SQL. Chrome 157.0.8103.78 / PW 1.62.1 pins unchanged.
- No secret/credential commit; fake fixture credentials only; no capability enters URL/storage/log.
- Prior foreign Docker/containerd/IPv4 effects and production classification remain UNKNOWN; no no-impact/no-production claim; no compensating cleanup performed.

## Scope confirmations

- No skips/pending/missing as pass: every suite above ran to completion with exact counts/natives; mid-increment failed attempts are retained in the private log root, not rewritten.
- No extra PR, no executor merge/auto-merge, no next-ID choice; order + active committed unchanged.
- No D5/083/MVP/product/release completion claim; remaining D5 causality/history obligations recorded in the OAP ledgers as required subsequent bounded work.

## Limitations / not-run

- GitHub CI (all children, Compose, six-image): PENDING at publication — executing in parallel on this DRAFT.
- Browser E2E through public-NGINX (C6 browser evidence): qualified by the CI Compose job scope (e2e specs updated to the real dual-digest path); no local Playwright run this round — CI is the executing gate.
