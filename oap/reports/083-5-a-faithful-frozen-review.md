# OAP 083-5-a execution report — complete frozen inputs and faithful review rendering

## 1. Status

| Field | Value |
| --- | --- |
| Round | 083-5-a (numeric objective 083, increment 5, round letter a) |
| Order | `oap/orders/083-5-a-faithful-frozen-review.md` (364 lines) |
| Order SHA-256 | `0badfe3a05d3c04bfdb9dc789925fc183606a9bf51916d0a974191d17352ffb9` |
| `oap/active` bytes | `083-5-a\n` (8 bytes: `3038332d352d610a`) |
| PR mode | CREATED_NEW_PR |
| Status | COMPLETE |
| Human full-product goal | still active; numeric 083 remains PARTIAL (this is one bounded increment only) |

## 2. Repository and PR identity

| Field | Value |
| --- | --- |
| Repo | `ulfe-lmi/slaif-agent-site` |
| PR | #107 — <https://github.com/ulfe-lmi/slaif-agent-site/pull/107> (state OPEN at report time; exactly one new branch/PR) |
| Branch | `oap/083-5-a-faithful-frozen-review` |
| Base | `main` |
| Verified remote base (starting remote SHA) | `4bf74fdc8e74323045a7f8830cf393493e75fe0d` (re-verified against `git ls-remote origin main` at report time; equals the order-verified base of 2026-10-18) |
| Literal implementation head (I) | `565c99c5d26d4bbc99f33891392670f0c0a7b5e7` |
| Report publication commit | SELF (this report; sole path; first parent exactly I) |

## 3. Pushed commits (T → I → S)

| SHA | Time (UTC) | Content |
| --- | --- | --- |
| `e0621155e86d59af800606ca33255db2f0984703` | 2026-10-18 | T-5a transcript: activated order + active bytes (unchanged order/active) |
| `9d6a004` / `67a5305` / `565c99c5d26d4bbc99f33891392670f0c0a7b5e7` (= I) | 2026-10-19 | I: bounded implementation — production/config (22 paths), tests (26 paths), docs (6 paths = I); the generated-contract check ran at final source with zero diff (§4.4) |
| SELF (this report) | 2026-10-19 (pushed last) | S: report-only child, first parent I, sole path this file |

## 4. Exact changes at I (54 paths, grouped)

### 4.1 Production/config — 22 paths, 9,350 gross (declared ceiling 24)

| File | +/− | Change |
| --- | --- | --- |
| `services/backend/src/slaif_agent_site/db/alembic/versions/076_001_faithful_frozen_review.py` | +3133/−0 | New developer migration 076_001 (R9): retained-v2 downgrade refusal FIRST; v2 capture materializer (complete domain inventory, six supported release pins, canonical digest); completion contract; `slaif_review_snapshot_frozen_state`, `slaif_review_projection_authorize`, `slaif_review_media_authorize` (frozen media byte gate over the full trusted binding), `slaif_media_preview_read` (pre-freeze ACTIVE human read), `slaif_media_bound_preview_read` (confined run-bound private read reusing 036 no-consume + original-nonce recheck + post-lock binding invariants), `slaif_browser_preview_binding_register` (atomic trusted run binding in the 036 consume transaction); binding columns + `browser_run_preview_binding_shape` CHECK (digest/nonce sha256-hex, expiry, `attempt >= 0` — 0 is legitimate: 036 admits QUEUED runs with `attempt_count = 0`) + partial unique digest index; grants/revokes; exact 075 restoration bodies |
| `services/backend/src/slaif_agent_site/render_api/frozen_source.py` | +3472/−0 | New module: the explicit R3 data-source boundary — `DatabaseRenderSurface` (live typed raw rows, exact trusted SELECTs with overflow sentinels) and `FrozenRenderSurface` (immutable `review-snapshot/v2` admission: full document shape, digest-covered payload, six supported pins, nested site/type/page/ref uniqueness, raw-family/byte bounds before any allocation); shared 052/056/059 SQL ports executed by BOTH paths: route memo, `navigation_resolved_items`, locale-INTERNAL semantics, bounded serializer with exact N/N-1 byte bounds |
| `services/backend/src/slaif_agent_site/content_model/canonical.py` | +306/−0 | New module: canonical v2 payload construction + exact-number `parse_snapshot_text` (Decimal scale/digit preservation) + `canonical_digest` |
| `services/backend/src/slaif_agent_site/render_api/projection.py` | +609/−254 | Shared projection over the typed surface boundary: `_query(surface, ...)` single engine for canonical/preview/review; frozen `review()` (076 authorize → frozen state → exact-number parse → frozen surface → captured-facts `SiteContext._from_frozen`); browser preview 083/5 trusted run binding (036 consume + registrar in ONE transaction, exact verified expiry, full token sha256); deterministic navigation corrupted-state precedence (all parent bindings validated before sibling contiguity; the original 059 FOR loop order made this row-order-dependent) |
| `services/backend/src/slaif_agent_site/render_api/site_http.py` | +42/−0 | Internal `/review` route (x-slaif-human-session only, uniform 404 / infrastructure 503) |
| `services/backend/src/slaif_agent_site/review_worker/snapshot.py` | +312/−31 | v2 capture: complete domain inventory (site profile/locales/theme/regions/pages incl. raw style_overrides + row versions, normalized compositions, navigation, redirects, types/fields/definitions, items/translations/relations, bounded view specs, media reference closure + proposed data) and completion gate |
| `services/backend/src/slaif_agent_site/media_service/media_http.py` | +242/−2 | Media byte boundaries: human preview read (054 chain, no touch), bound worker read (token hashed only, trusted binding lookup), frozen review byte gate, credential failures 401, denials uniform 404, private stream no-store + X-Robots-Tag |
| `services/browser-worker/src/execution.ts` | +252/−1 | Run-bound document-reader: bounded same-origin fetch of bound preview document bytes, bounded DOM walk with explicit visited-node/work ceiling and first-omission limit evidence (no unbounded selector collection), first-64/limit exposure, whole-run timeout |
| `services/backend/src/slaif_agent_site/media_service/database.py` | +126/−0 | Media DB boundary for the new read routes |
| `services/browser-worker/src/url-policy.ts` | +77/−1 | Worker URL policy: single bound-document navigation; bound media subresource path inside existing preview confinement; exact same-origin/image/redirect/header denials |
| `services/backend/src/slaif_agent_site/db/privileges.py` | +127/−7 (134 gross ≤ 180 bound) | Bootstrap reconcile: the six 076 read functions into the preview/media role maps + effective verifier; named registrar key type corrected to `timestamptz`; existence-skip restricted to the six 076 objects on 075 absence (old strict GRANT failures preserved) |
| `services/backend/src/slaif_agent_site/review_worker/accept_job.py` | +102/−11 | Approval: shared exact decoder (raw Decimal digits survive `json.loads` float conversion) through real approval/replay; media finalization replay normalization for the exact flipped set (076 inventory `public_status/published_at/updated_at`); stable semantic terminal map (recognized version/validation/budget failures refuse compatibly before media effects; true transients stay retryable) |
| `apps/web/src/sites/review-projection.ts` | +59/−0 | Web v2 faithful projection consumer (frozen read route, exact retained values) |
| `services/backend/src/slaif_agent_site/bootstrap/service.py` | +32/−0 | 076 in upgrade list; retained-v2 downgrade refusal preflight BEFORE operator-path effects (bootstrap guard mirrors the migration guard; unchanged readiness/COW/revision/catalog/snapshot bytes on refusal) |
| `apps/web/src/sites/review-page.ts` | +19/−15 | Review page: v2 selector with honest v1 legacy view and unknown-format refusal (no fallback rendering) |
| `services/backend/src/slaif_agent_site/sites/models.py` | +38/−0 | `SiteContext._from_frozen`: captured site profile/status/locales/release facts + locked freeze revision (live session/membership checks stay in the 076 SQL; drift is separately named metadata) |
| `services/backend/src/slaif_agent_site/review_worker/freeze_job.py` | +25/−1 | `SNAPSHOT_VALIDATION_FAILED` domain-error code mapping (the 076 materializer RAISEs it at 23 sites; previously fell to the phase default) |
| `apps/web/src/sites/render.ts` | +22/−0 | Render wiring for the review context metadata |
| `services/backend/src/slaif_agent_site/media_service/config.py` | +7/−0 | Media route/config wiring (keyless: no new credential/holder) |
| `services/backend/src/slaif_agent_site/content_model/query_dsl.py` | +4/−1 | Query-DSL wiring for the shared path |
| `apps/web/next.config.mjs` | +18/−0 | Web build wiring for the review surface |
| `services/backend/src/slaif_agent_site/review_worker/config.py` | +1/−1 | `REVIEW_WORKER_STATE_VERSION = "review-snapshot/v2"` |

### 4.2 Tests — 26 paths, 5,663 gross (declared named 23; variance §8)

| File | +/− | Change |
| --- | --- | --- |
| `services/backend/tests/integration/test_freeze_review_snapshot.py` | +1562/−28 | v2 capture/completion/roundtrip (076→075→076 exact restore, retained-v2 refusal FIRST, separate genuine v1-only rollback fixture), frozen review endpoint real-role read (DRAFT pages, exact 23-digit fraction fidelity, no-touch proof, terminal discard before after-read), review-surface read-model v2 expectations (complete 18-key / 8-key assertions, not key-presence), media URL + role denials |
| `services/backend/tests/integration/test_media_service.py` | +1114/−2 | R2 actual private bytes: Agent uploads real PNG + PDF; human active preview AND actual confined bound worker read both before freeze; public/canonical refuse; after real terminal discard + pending cleanup the frozen review returns the same bytes; credential-shape 401 / denial 404; no-touch |
| `services/backend/tests/unit/test_render_projection.py` | +899/−1 | Shared engine pure vectors: bounded serializer exact N/N-1/N+1 (dict 7 / array 3 / nested 15), raw depth 8/9, leaf 1 / chain 17/18, 1001-digit numeric at 8 MiB, float decode vs literal stdlib reference, raw Decimal unmutated, route memo work bounds (8/16/32 links → 8/16/32 visits+derivations for repeated AND distinct hrefs), navigation semantics, frozen admission negatives |
| `services/backend/tests/unit/test_review_worker.py` | +341/−36 | Worker v2 paths, semantic terminal map, replay normalization |
| `services/browser-worker/tests/url-policy.test.mjs` | +260/−0 | Worker URL policy boundary (bound document/media navigation, denial matrix) |
| `services/backend/tests/unit/test_snapshot_v2_canonical.py` | +222/−0 | Canonical v2 payload/digest exact-number vectors |
| `services/backend/tests/unit/test_render_projection_media.py` | +219/−20 | Frozen media gate pure vectors |
| `tests/e2e/freeze-review-snapshot.spec.ts` | +262/−1 | Public NGINX E2E: active preview vs immutable review, six targets, meaningful content/order/parameters/CSS assertions |
| `tests/e2e/media-publication.spec.ts` | +17/−14 | Pre-existing spec repair (no new assertions): the 14 preview-context media-URL expectations (img src/href, byte fetch, preview-vs-canonical markup comparisons) now use the workspace-scoped 054 preview-chain URL the R6 renderer emits; the three route-level authorization negatives (cross-site / non-member / revoked-session 404s on the legacy site-level read route, which still exists) are unchanged |
| `apps/web/tests/review-surface.test.mjs` | +159/−4 | Web unit (approved in place of the optional browser-control path): real v2 client + honest v1 facts + unknown refusal |
| `tests/e2e/review-surface.spec.ts` | +105/−4 | Public E2E review-surface spec (incl. the new v2-faithful contract and the two smoke-exposed stale-expectation repairs, §6/§8) |
| `services/backend/tests/integration/test_database_bootstrap.py` | +97/−6 | Bootstrap retained-v2 preflight refusal, unchanged operator-state proof, ACL reconcile cases |
| `services/backend/tests/integration/test_review_surface_read_model.py` | +59/−4 | Read-model v2 positive path with meaningful values + auth/determinism/diff/no-effects |
| `services/backend/tests/integration/test_real_human_discard.py` | +31/−10 | Discard terminal + retained immutability |
| `services/backend/tests/integration/test_real_human_accept.py` | +20/−5 | Accept crash-replay idempotence (076 inventory flip normalization) |
| `services/backend/tests/integration/test_agent_mutations.py` | +14/−23 | `_query` shim adapted to the shared surface signature (repair; no new assertions) |
| `services/backend/tests/unit/test_control_database.py` | +5/−5 | 076 object pins |
| `services/backend/tests/unit/test_foundation_contract.py` | +5/−1 | 076 in the versioned migration set |
| `services/backend/tests/unit/test_health_apps.py` | +4/−0 | Route surface pins |
| `services/backend/tests/integration/test_render_browser_preview.py` | +3/−14 | `_query` shim + obsolete SQL probe removal (repair) |
| `services/backend/tests/integration/test_render_structure_router.py` | +13/−50 | Three `_query` shims + obsolete probe removal (repair) |
| `services/backend/tests/integration/test_cache_outbox_consumer.py` | +4/−4 | Delta pin corrected to 074_001 (the test's own docstring scope) |
| `services/backend/tests/integration/test_agent_page_style.py` | +3/−3 | 076 pin |
| `services/backend/tests/integration/test_control_database_integration.py` | +3/−3 | 076 pin |
| `services/backend/tests/integration/test_editable_domain_proof.py` | +1/−1 | 076 pin |
| `services/backend/tests/integration/test_human_agent_session_control.py` | +1/−1 | 076 pin |

### 4.3 Docs — 6 approved paths, 70 gross

`docs/API.md` (+17/−0), `docs/SECURITY.md` (+16/−0), `docs/OPERATIONS.md` (+12/−0), `docs/user-manual/README.md` (+13/−2), `oap/MVP-CONTRACT-AUDIT.md` (+3/−3), `oap/MVP-PROGRESS.md` (+2/−2)

### 4.4 Generated contracts

Zero generated contract changes: `uv run --frozen python -m tools.contracts.generate_agent_openapi --check` = 0 (zero-diff) at final source. The four-generated ceiling is untouched; `.next` output is never a versioned contract.

## 5. R1–R9 / A–F evidence map

All integration tests below ran in the fresh unfiltered final directory run
(`full-integration-final3.log`; exact counts in §6) and in the isolated
verification runs cited per item.

**A — new format capture (actual Agent AND human Editor public mutations, real retained values):**

- `test_freeze_review_snapshot.py::test_freeze_lifecycle_worker_snapshot` — idempotent freeze through the real control enqueue + real worker claim + real run; v2 payload with the complete 18-key family set.
- `test_freeze_review_snapshot.py::test_review_endpoint_frozen_read_media_urls_and_role_denials` — retained DRAFT page (active-preview candidate policy carried into frozen review), retained 23-digit fraction `0.10000000000000000000001` surviving the JSONB → exact-number round trip (stored digest equality asserted), seeded Image under the root Section with identity/type/URL assertions in the actual descendant tree.
- Committed public mutation suites (076 pins only): `test_agent_mutations.py` (Agent public builds news listing/detail, draft previews, archive refusals), `test_agent_page_style.py` (non-default page/responsive style precedence), `test_human_agent_session_control.py`, `test_editable_domain_proof.py` — the R1 families (models/fields/items/translations/relations/views/compositions/styles/media refs) are exercised through the real public APIs and retained by the capture; the roundtrip test asserts the exact retained key set `{state_version, workspace_id, site_id, site, base_site_revision, operation_watermark, workspace_versions, locales, theme, regions, navigation, redirects, pages, page_compositions, content, proposals, media_inventory, media}`.
- `test_media_service.py::test_private_media_bytes_human_preview_bound_worker_frozen_review` — Agent uploads real PNG (IMAGE) + PDF (DOCUMENT) through the real Agent HTTP API; both are in the immutable v2 typed media closure with exact digest/row binding.

**B — public NGINX E2E (active preview vs immutable review, six targets, meaningful assertions):**

- `tests/e2e/freeze-review-snapshot.spec.ts` (+246/−1) and `tests/e2e/review-surface.spec.ts` (+105/−4), executed by `sh tools/compose/smoke.sh slaif071smoke` (full public smoke, project-name chronology in §6) through public NGINX: static/list/detail routes, multiple items/locales, selected-locale + default fallback, query sort/filter/projection/pagination, related items, navigation/redirect/switcher, regions/media, non-default page-style precedence across all six stable targets; assertions inspect content/order/route parameters and computed CSS.
- `apps/web/tests/review-surface.test.mjs` (approved in place of the optional browser-control path) — real v2 client against the actual read-model document; v1 facts honest; unknown stored versions refused.

**C — post-freeze unrelated canonical publication drift:**

- `test_real_human_accept.py::test_accept_worker_drift_zero_mutation` and the freeze-snapshot drift assertions (stored payload/digest/captured values/frozen projections unchanged; separately named current revision/drift may change).
- `test_freeze_review_snapshot.py::test_review_endpoint_frozen_read_media_urls_and_role_denials` — the whole frozen read sequence happens AFTER the discard runs to its real terminal worker state (retained immutability after terminal discard + pending cleanup).

**D — counterfactual regression evidence (omitted/stubbed inputs fail):**

- `test_render_projection.py` (+899/−1) — pure-vector counterfactuals: bounded serializer exact N/N-1/N+1 (dict 7 / array 3 / nested 15), raw depth 8/9 boundary, leaf 1 / chain 17/18 counts, 1001-digit numeric at the 8 MiB bound, float decode vs literal stdlib live-JSON reference, raw Decimal scale unmutated, route-memo total-work bounds (8/16/32 links → 8/16/32 visits+derivations for repeated AND distinct hrefs), admission negatives (foreign field, deleted page, cross-page style, 1100-deep proposal, divergent normalized state, extra key, malformed proposals, foreign site), NULL-helper/final-guard depth paths.
- `test_snapshot_v2_canonical.py` (+222) — canonical payload/digest exact-number counterfactuals (digit/scale preservation; a stub decoder cannot reproduce the stored digest).
- `test_render_projection_media.py` (+219/−20) — frozen media gate vectors: six-pin exactness, row-vs-payload identity, unique inventory/site/storage-key binding, malformed shapes all empty-result.
- The 076 materializer RAISEs `SNAPSHOT_VALIDATION_FAILED` at 23 sites; `test_forced_validation_failure_leaves_freezing` proves a forced validation failure leaves the workspace in FREEZING (no partial completion) with the stable code.

**E — negative/security/lifecycle proof:**

- `test_freeze_review_snapshot.py::test_076_001_round_trip_retained_v2_and_exact_restore` — retained-v2 downgrade refusal FIRST (no effects); exact 075 restoration with a SEPARATE genuine v1-only fixture (retained v2 rows never deleted to make downgrade succeed); constructor/pin restore identity; effective-role + ACL proof.
- `test_freeze_review_snapshot.py::test_075_001_round_trip_exact_restore_and_locked_materializer` — predecessor roundtrip retained.
- Role/token/session negatives: unknown/revoked/expired/recency-failed sessions, cross-site and cross-workspace bindings, foreign digest/nonce/attempt, credential-shape 401 vs denial 404, `test_review_endpoint_frozen_read_media_urls_and_role_denials` (public reader cannot execute the 076 read functions; uniform 404 for every refusal; no-touch last_seen_at equality across the whole read sequence).
- `fn3` frozen media gate actual-SQL matrix (PG14 + PG18): 43 unique count rows each (3 declared positive / 40 negative), 0 mismatches, child psql exit 0 (logs `fn3-probe-v3-corrected-pg14-first-independent-owned.log`, `fn3-probe-v3-corrected-pg18-first-independent-owned.log`).
- Over-budget/bounds: serializer exact-N pass/N-1 refuse vectors; navigation position/parent/cycle/unreachable/label/target/scope/locale matrix (`test_render_structure_router.py::test_navigation_corruption_matrix_fails_closed`); snapshot record/byte/nesting budgets in the materializer (stable refusal, no silent truncation).
- Lock/cancellation/rollback: `test_lock_serialization_and_r4_shared_lock`, `test_freeze_site_lock_failure_rollback_no_leaked_lock`, `test_first_touch_conflict_baseline_survives_freeze`, browser preview cancel/retry matrix in `test_render_browser_preview.py` (one-time token; separately committed authorization survives read-transaction cancellation), `test_real_human_accept.py::test_accept_worker_crash_replay_idempotent` (replay idempotence incl. the 076 inventory status-flip normalization).
- Legacy v1: stored-v1 snapshots keep their honest limited view (Web selector + read-model tests), never qualify for the v2 approval contract, refuse before effects with supported recreation; unknown stored versions refuse (no v1 or live fallback).

**R9 — migration/ACL/roundtrip:**

- New migration `076_001` only (no second migration); upgrade from 075 exact; ownership/`search_path`/ACL deltas asserted in the roundtrip test (function identity fields + expected grant set per role + effective `has_function_privilege` matrix); downgrade refused FIRST when retained v2 rows exist (migration body AND bootstrap preflight, both tested: `test_database_bootstrap.py` retained-v2 preflight refusal with unchanged readiness/COW/revision/catalog/snapshot bytes); foundation stays exact frozen PyPI 0.2.0 (`test_foundation_contract.py` pins).
- Binding invariant correction (this session): `browser_run_preview_binding_shape` requires `preview_credential_attempt >= 0` (was `>= 1`); 0 is a legitimate first-bind value because 036 admits QUEUED runs with `attempt_count = 0` (035 increments only on worker lease). The bound read's post-lock recheck (`attempt_count <> preview_credential_attempt → refuse`) is unchanged — an attempt rotation still invalidates the binding.

**R1–R8:** see §4.1 itemization (R1 inventory in `snapshot.py`/076 materializer; R2 trace in `canonical.py` + roundtrip digest assertions + `media` closure binding; R3 shared engine = `projection.py::_query` over `frozen_source.py` surfaces, both paths execute the same helpers, no second engine, no SQL-string fakes; R4 route/locale/nav/regions/style fidelity in the shared port + B E2E; R5 frozen read boundary = 076 read functions + frozen surface, no live fallback, media bytes immutable with authorized reads; R6 typed media closure + idempotent finalization replay (`accept_job.py`); R7 supported-format gates at capture/read/approval + legacy reader + stable refusal; R8 083/4 lock order retained + snapshot/query budgets + per-request route memo).

## 6. Gate results

All at final source, repo root, pinned tools: uv 0.12.5, venv Python 3.13.14 (host 3.14.4 for the non-venv preparation commands), Node v24.22.0, pnpm 11.22.0, PostgreSQL 18 container `slaif-integration-pg-0833b` (integration), PostgreSQL 14.24 + 18.6 (fn3 matrix).

| # | Command | Exit | Result |
| --- | --- | --- | --- |
| 1 | `uv lock --check` | 0 | Resolved 45 packages (final-gates-lock-sync.log) |
| 2 | `uv sync --frozen --all-groups` | 0 | Checked 44 packages |
| 3 | `uv run --frozen ruff check services/backend tests/repository tools` | 0 | All checks passed |
| 4 | `uv run --frozen ruff format --check services/backend tests/repository tools` | 0 | All formatted |
| 5 | `uv run --frozen mypy` | 0 | Success: no issues found in 315 source files |
| 6 | `uv run --frozen pytest services/backend/tests/unit tests/repository` | 0 | 850 passed, 3 warnings, 26 subtests (unit-full-rerun2.log) |
| 7 | `uv build --out-dir /tmp/slaif-agent-site-distributions` | 0 | wheel + sdist built (final-gates-build-checks.log) |
| 8-17 | 10 x `python -m slaif_agent_site.<module> --check` | 0 | all CHECK_OK (final-gates-module-checks.log) |
| 18 | `node --version` | 0 | v24.22.0 |
| 19 | `pnpm --version` | 0 | 11.22.0 |
| 20 | `pnpm install --frozen-lockfile` | 0 | Done (final-gates-node.log) |
| 21 | `pnpm lint` | 2 | LOCAL-ENV ONLY: untracked `.codex/plugins/cache/.../vinext-starter/eslint.config.mjs` scanned by root `eslint .`, imports `eslint-config-next` not installed at that level (pnpm-lint-full.log). Scoped: `pnpm --filter @slaif-agent-site/web lint` = 0; root eslint with `--ignore-pattern .codex/**` = 0 (pnpm-lint-scoped.log). Committed tree/CI clean; `.codex` preserved per order, untouched |
| 22 | `pnpm format:check` | 0 | (final-gates-node.log) |
| 23 | `pnpm typecheck` | 0 | (final-gates-node.log) |
| 24 | `pnpm test` | 0 | all web + browser-worker suites pass (final-gates-node.log) |
| 25 | `pnpm build` | 0 | (final-gates-node.log) |
| 26 | `pnpm licenses list --json` | 0 | licenses-final.json; only MIT/Apache/ISC/BSD/CC-BY/0BSD/BlueOak families |
| 27 | `python -m compileall -q tools tests/repository` | 0 | (final-gates-repo-checks.log) |
| 28 | `python -m unittest discover -s tests/repository -p 'test_*.py'` | 0 | Ran 71 tests - OK |
| 29 | `python tools/check_repository.py` | 1 | LOCAL-ENV ONLY: exactly 4 errors, all in untracked `.codex/packages/**` license files; 0 in repository files (check-repo-final-full.txt) |
| 30 | `python tools/check_mermaid.py` | 0 | PASS 16 diagrams in 3 files; 959 Markdown scanned |
| 31 | `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` | 1 | LOCAL-ENV ONLY: 2,580 errors, all under untracked `.codex/**`; 0 in repository files (markdownlint-final-rerun.log) |
| +1 | `uv run --frozen pytest services/backend/tests/integration` (fresh, complete, unfiltered, plugin-free) | 0 | FINAL (final4): **329 passed / 4244.32s (1:10:44) / PYTEST_EXIT:0** (`full-integration-final4.log`). Superseded: final2 320P/9F exit 1; final3 328P/1F exit 1 (media-test review-path contract, fixed; all ten failures itemized in §8) |
| +2 | `sh tools/compose/smoke.sh slaif0835smoke` (full stack rebuilt from final source, public NGINX, 19 playwright projects incl. the two new specs, negative project, restart/acceptance) | PENDING | Chronology (all attempts preserved; all failures test-side or repro-state, product unchanged): **attempt 1** (compose-smoke-final.log) SMOKE_EXIT:1 — 28 projects PASSED, then `review-surface` contract `review-surface-review-render-and-summary` at `review-surface.spec.ts:821` expected the legacy-v1 `data-render-mode="preview"` while the faithful v2 frozen read renders `"review"` (stale expectation, inconsistent with the sibling assertion at line 1353 of the same spec and with `freeze-review-snapshot.spec.ts`); the project's fail-closed-negatives and v2-faithful contracts PASSED. Fixed the spec to `"review"` (web lint+typecheck 0). **attempt 2** (compose-smoke-final2.log) SMOKE_EXIT:1 — same contract, next assertion at line 837: the spec expected the pre-R6 site-level private media URL while the renderer now emits the workspace-scoped 054 preview-chain URL; fixed the spec expectation (new `snapshotId` psql fact) — the same class of stale expectation later found in `media-publication.spec.ts` (§9). **attempt 3** (compose-smoke-final3.log) SMOKE_EXIT:1 — all review-surface contracts PASSED; `freeze-review-snapshot-faithful-frozen-review-v2` at line 1063 got 403 on the Heading POST: the spec's fixture workspace used the L1 preset, which lacks `component-structure:create` (an L2 scope); fixed the fixture preset to L2_SITE_EDITOR (product was correct). **attempt 4** (compose-smoke-final4.log) SMOKE_EXIT:1 — same contract's psql, five test-side SQL bugs (the contract had never run before): PG `->`/`\|\|` precedence (parenthesized each extraction), JSONPath digit-leading key (PG JSONPath requires double-quoting such keys), `jsonb_path_exists` booleans cast to text, `::text` boolean rendering `"truetrue"`, anonymous media read is 401 not 404, and anonymous `/review/` needs the no-trailing-slash + `maxRedirects:0` form. Fixed in the spec; verified by the isolated contract run `isolated-v2-contract9.log` (1 passed / ISO_EXIT:0). Isolated insurance on the warm repro stack: `accept-lifecycle` (2) + `discard-lifecycle` (3) contracts PASSED (`isolated-remaining-projects.log`); `media-publication` failed on its stale pre-R6 URL expectations and then on repro-stack residue, was repaired, and PASSES after residue cleanup (`isolated-media-publication3.log` 1 passed / MEDIA3_EXIT:0, §9); the whole `freeze-review-snapshot` project PASSES 4/4 (`isolated-freeze-project5.log` / FREEZE5_EXIT:0). **attempt 5** (compose-smoke-final5.log) SMOKE_EXIT:1 — the full 19-project public e2e suite PASSED on the fresh stack (`compose-e2e` OK, projects=19, incl. media-publication 1/1, freeze-review-snapshot 4/4, review-surface 3/3, accept/discard-lifecycle, six stable devices, agent sessions), then the smoke's own final `public-agent-acceptance` phase refused the project name: the acceptance tool's pre-existing safe-name whitelist (accepting only the older `007`/`009`/`010`/`071` project prefixes) predates this increment's `0835` naming — a tooling gap, not a product or e2e failure. Fixed the tool's whitelist (one regex alternative) and re-ran the complete smoke fresh: **attempt 6** (compose-smoke-final6.log) SMOKE_EXIT:1 — the full 19-project public e2e suite PASSED again on the fresh stack, `public-agent-acceptance: OK` (whitelist fix effective, full acceptance proof passed), the browser-worker/artifact/outage/restart phases all PASSED, then a THIRD pre-existing safe-name whitelist (`tools/compose/control_readiness.py`, accepting only the `007`/`009`/`071` prefixes, called by the smoke's final `control-readiness-fixture` phase) refused `slaif0835smoke`. Adding that prefix to the third tool would have required a 25th production path (ceiling 24), so the tool edits were REVERTED (zero tools/ diff at final source) and the final smoke ran under the base-allowed name `slaif071smoke` — the same runner, the same 19 projects + acceptance + all later phases, isolated disposable fixtures/volumes (the order's literal `slaif0835` name cannot be executed against the pre-existing runners' safe-name whitelists; precedent: the 083-4 smoke also ran under a base-allowed name, `SMOKE_4A_EXIT:0`). **attempt 7** (compose-smoke-final7.log) — FINAL: fresh stack under the base-allowed name `slaif071smoke`, launched 2026-10-19T10:56:46Z, `compose-e2e: OK projects=19` (all 19 public projects: 39 browser-e2e contracts, 0 failures, incl. media-publication, freeze-review-snapshot 4/4, review-surface 3/3, six stable devices), `public-agent-acceptance` OK (full acceptance proof: types/fields/items/translations/relations/views/pages/components/locales/redirects/navigations/theme/openapi-exact/restart/nginx-outage/crud/quotas/canonical-independence/render-restart), `control-readiness-fixture` OK (mount=isolated identity=exact failures=6 recovery=clean), browser-worker dispatch/artifact/outage/restart phases OK, `compose-smoke` OK, **SMOKE_EXIT:0** (log finalized 2026-10-19T11:12:17Z). Note: the base smoke whitelist did not accept this increment's first chosen project name (the first launch was refused as an unsafe project name); attempts 1-6 therefore used `slaif0835smoke` after a temporary whitelist entry, and attempt 7 uses the base-allowed name `slaif071smoke` with zero tools/ changes. |

Generated contract check: `uv run --frozen python -m tools.contracts.generate_agent_openapi --check` = 0 (zero-diff) at final source; zero generated contract changes.

## 7. GitHub required checks

### 7.1 At I (literal implementation head)

Workflow runs at head `565c99c` (PR #107): CI `39243413638` (event `pull_request`, started 2026-10-19T11:16:09Z) and CodeQL `39243413388` (COMPLETED/SUCCESS 11:18:08Z; its four Analyze sub-checks all COMPLETED/SUCCESS).

CI attempt 1 (17 of 20 COMPLETED/SUCCESS): Analyze (actions) / (javascript-typescript) / (python) via CodeQL, CodeQL, Compose and edge packaging, Dependency review, Detect supported languages, Foundation PostgreSQL 17 (SUCCESS 11:24:15Z), Foundation PostgreSQL 18 (SUCCESS 11:27:49Z), Markdown, Mermaid, Node contracts, Python 3.12/3.13/3.14 quality and package, Repository policy, Supply-chain evidence — all COMPLETED/SUCCESS.

Three Foundation PostgreSQL jobs did not qualify on attempt 1: PG 14 (job 118029412731), PG 15 (job 118029412814), PG 16 (job 118029412524) were CANCELLED by the job's own `timeout-minutes: 15` budget (annotations: "The job has exceeded the maximum execution time of 15m0s" + "The operation was canceled."; cancellations at 11:31:21/27/28, i.e. 15:10-15:17 after the 11:16:11 start; same chronic tightness as the base-side run 39118686133 and the 083-4-era run 39109484677). No test failed in any of them: every completed pytest session in the preserved job logs is green (PG14: 81P/573.57s bootstrap+privilege gate, 24P/170.30s component authority+concurrency, 9P/58.59s theme + 1 quick session, page-style session still running at the budget edge; PG15: five green sessions; PG16: four green sessions). Cause: shared-CI runner wall-clock slowdown against the pre-existing 15-minute job budget, not a product or test failure.

One genuine documented re-run (the order's single permitted re-run; original logs, cause and exact attempt preserved in `/tmp/oap-083-5-a/ci-pg14-job118029412731.log`, `ci-pg15-job118029412814.log`, `ci-pg16-job118029412524.log`, `ci-rerun-decision.txt`): `gh run rerun 39243413638 --failed` re-executed exactly the three cancelled jobs at the same head (attempt 2).

Attempt-2 terminal states: Foundation PostgreSQL 14 COMPLETED/SUCCESS (job 118038446887, re-executed at the same head), Foundation PostgreSQL 16 COMPLETED/SUCCESS (job 118038447209), Foundation PostgreSQL 15 CANCELLED again by the same 15-minute job budget — and this time with the ENTIRE five-step test suite green: bootstrap/privilege 573.02s, component 166.85s, theme 57.52s, page-style 82.81s, the last session finishing 11:54:08Z and the 15:00 budget expiring at 11:54:11Z during container teardown (job 118038447552; preserved log `/tmp/oap-083-5-a/ci-pg15-attempt2-job118038447552.log`). Zero test failures in any PG job at either attempt.

Observed at I: **19 of 20 required names COMPLETED/SUCCESS**; the single non-qualifying name is Foundation PostgreSQL 15 (cancelled job-timeout, twice, both documented, no test failure, one after a fully green suite). The order's 20-check mandate is at the **final report-only SHA** (S), which triggers a fresh CI run with its own job clocks; that run is verified externally after push (see §7.2) and this report is not amended for it. Context for the chronic tightness: at the 083-4 head, the same matrix's PG15/PG17 jobs ran 14:23/14:22 against this same 15-minute budget (run 39109952661), i.e. <40s of headroom before shared-CI variance.

### 7.2 At S (final report-only head)

At the moment this report is committed and pushed, S is the just-pushed
report-only head; its required checks have not run to completion and no
conclusion exists yet, so this immutable report records **no CI state at S**
(PENDING at publication). The order's 20-check mandate at the exact final
report SHA is verified externally by the executor after the push — by
polling the workflow runs for head S to all-20 COMPLETED/SUCCESS (run_attempt
= 1) and recording the result in `/tmp/oap-083-5-a/ci-jobs-S.log` — and is
independently gated by strategy. This report is not amended for later-observed
CI; the observed CI recorded above (§7.1, head I) is the only in-report CI
evidence.

## 8. Budget and variance

- Prod+test gross: 15,013 ≤ 17,500 (2,487 headroom).
- Production paths: 22 ≤ 24 declared (the conditional 25th `render_api/app.py` was never needed).
- `db/privileges.py`: 134 gross ≤ its 180 bound.
- **Test-path variance: 26 changed test paths vs 23 named.** The three beyond the named set are PRE-EXISTING committed test files: `test_render_structure_router.py` (+13/−50) and `test_render_browser_preview.py` (+3/−14) — their `_query` monkeypatch shims carried the pre-refactor signature and broke when the order-approved shared projection refactor changed the `_query` surface signature; the repair adapts the shims and removes the obsolete hand-rolled `slaif_render_page_resolve` probes (net −48 lines; no new assertions, no new families, no scope added); and `tests/e2e/media-publication.spec.ts` (+17/−14) — the pre-existing media E2E spec asserted the pre-R6 site-level private byte URL in its preview-context expectations; the R6 wiring changed the preview renderer to emit the workspace-scoped 054 preview-chain URL, so the 14 preview-context expectations were updated to the emitted URL (the legacy route still exists and is unchanged; the spec's three route-level authorization negatives keep testing it). No new assertions, no weakened checks, no scope added. Flagged for the strategic final cumulative review; no self-waiver.
- Docs: 6 approved paths. Transcripts: 2 (order + active, bytes unchanged).

## 9. Preserved failures and honest chronology

All logs in `/tmp/oap-083-5-a/`; every failed attempt preserved with its exact
tested identity/command/exit/count. No partial run is aggregated into a full
pass; the final full integration result is §6 (final4).

**Integration (final2, superseded by final3/final4):** `full-integration-final2.log` — 9 failed / 320 passed / 4255.75s / PYTEST_EXIT:1. The nine failures and their proven fixes:

1. `test_cache_outbox_consumer.py::test_grant_surface_delta_vs_083_1_baseline` — the delta pin had drifted to head (076) while the test's own docstring scopes the delta 073_001→074_001; 076 grants leaked into the measured delta. Fixed in-test (scoped to its documented 074_001 scope). Verified: isolated PYTEST_EXIT:0.
2. `test_freeze_review_snapshot.py::test_forced_validation_failure_leaves_freezing` — the 076 materializer RAISEs literal `SNAPSHOT_VALIDATION_FAILED` (23 sites) but `freeze_job._DOMAIN_ERROR_CODES` lacked the key, so the worker fell through to the phase default. Fixed product-side (code mapping). Verified: isolated PYTEST_EXIT:0.
3. `test_real_human_accept.py::test_accept_worker_crash_replay_idempotent` — 076 v2 `media_inventory` docs carry `public_status/published_at/updated_at`; finalization (068 `slaif_media_public_mark`) flips exactly `public_status` + `published_at` (+trigger `updated_at`); the replay normalization only flipped the `media` map, so the re-materialized doc diverged from the stored digest. Fixed in `accept_job._verify_snapshot` (restore the three fields from the stored capture for exactly the flipped set). Verified: `accept-replay-fix-verify.log` 1 passed / 21.43s / PYTEST_EXIT:0.
4. `test_agent_mutations.py::test_public_agent_builds_news_dynamic_listing_and_detail_render` — the test's `_query` monkeypatch shim carried the pre-refactor signature (`connection, *, context, request, render_mode`); the shared surface signature adds `preview_workspace_id`/`preview_bound`/`snapshot_id` → TypeError. Shim adapted (`surface, **kwargs`); no assertion changes. Verified: PYTEST_EXIT:0.
5. `test_render_structure_router.py::test_dynamic_collection_detail_route_binds_exact_published_item` — the shim probed `connection.fetchrow` on the surface (AttributeError) with an obsolete hand-rolled `slaif_render_page_resolve` call; the repeatable-read snapshot is already established by the resolver query inside `canonical()` before `_query` runs, so the probe is obsolete and the pause-at-`_query` is the race window. Fixed (probe removed, shim adapted). Verified: PYTEST_EXIT:0.
6. `test_render_structure_router.py::test_public_agent_cow_structure_is_visible_only_to_authorized_preview` — same pattern (two shims: human-preview and canonical). Fixed. Verified: PYTEST_EXIT:0.
7. `test_render_structure_router.py::test_navigation_corruption_matrix_fails_closed` — the ported raw item fetch orders `ORDER BY id`; the original 059 `FOR item IN SELECT ... (no ORDER BY)` iterated the physical row set, so in a corrupted state (item re-parented into a foreign navigation) the cross-navigation `navigation_parent` check fired before the now-non-contiguous `navigation_position` group only when the corrupted row was inserted first. The port made the corrupted-state precedence row-order-dependent (`navigation_position` first under UUID order). Fixed product-side: deterministic two-pass precedence (every parent binding validated before any sibling contiguity), matching the original de-facto behavior; both codes remain fail-closed 404s. Verified: PYTEST_EXIT:0.
8. `test_freeze_review_snapshot.py::test_review_endpoint_frozen_read_media_urls_and_role_denials` — 404 on the first POST: `_frozen_local_match_prefix` required the external `/s/<site_key>/...` localhost addressing form, but the actual review contract (the Web review-page consumer and this test) passes the SITE-LOCAL route with the request host as authority; the site is bound by the trusted authorize row, never by the authority. Fixed product-side: the helper validates both client strings (malformed authority/path or reserved top-level segment → uniform 404) and returns the empty prefix so the local route is used verbatim. Verified: `review-fix-verify.log` 1 passed / 14.05s / PYTEST_EXIT:0.
9. `test_render_browser_preview.py::test_browser_token_projects_only_bound_overlay_and_is_one_time` — 503: the 076 CHECK `browser_run_preview_binding_shape` required `preview_credential_attempt >= 1`, but the registrar records `run.attempt_count`, which is 0 for a run consumed while QUEUED (036 admits QUEUED; 035 increments only on lease) → `browser_run_preview_binding_shape` violation on the first legitimate bind. Fixed product-side (CHECK `>= 0`). The same test's later stage then exposed its stale `pause_after_dynamic_snapshot` shim (same `_query` signature drift; timeout at the dynamic-snapshot wait). Shim adapted. Verified: `browser-fix2-verify.log` 1 passed / 18.04s / PYTEST_EXIT:0.

**Full unfiltered run final3 (the first full run after the nine fixes):** `full-integration-final3.log` — 1 failed / 328 passed / 5368.83s (1:29:28) / PYTEST_EXIT:1. The single failure: `test_media_service.py::test_private_media_bytes_human_preview_bound_worker_frozen_review` at its phase-6/8 frozen review byte read — 404 instead of 200. Root cause: that test's `review_request` addressed the internal review route with the EXTERNALLY-addressed path `f"/s/{site_key}/"`, while the actual Web review-page consumer (and the product contract, fixed this session in `_frozen_local_match_prefix`) uses the SITE-LOCAL route; the site is bound by the trusted authorize row, never by the authority. The other frozen-read test in this increment already used the local form (`/`, `/draft/`). Fixed in-test: `review_request["path"] = "/"` (the local form of the test's site root `route`; all other assertions untouched). This is the tenth integration failure of the increment, fixed and re-verified: `media-fix-verify.log`. The FINAL full unfiltered directory run is final4 (§6).

**Isolated intermediate runs (preserved):**

- `isolated-media-publication.log` — the pre-existing `media-publication` E2E (never previously executed in any smoke) failed at line 313: it expected the pre-R6 legacy site-level private byte URL `/media/v1/sites/{site}/assets/{id}/content` while the R6 preview renderer emits the workspace-scoped 054 preview-chain URL. Repaired the 14 preview-context expectations (img src/href, authenticated byte fetch, preview-vs-canonical markup comparisons); the three route-level authorization negatives (cross-site / non-member / revoked-session 404s) still exercise the unchanged legacy route.
- `isolated-media-publication2.log` — re-run on the warm repro stack still failed at the human-image assertion: the two prior failed runs had left stale Image composition rows in the parity workspace's COW overlay (media is content-addressed, so the same two media IDs recurred across runs) and three `MEDIA_UPLOADED` audit rows for the agent media, which the spec's end-of-contract `count(*) = 1` audit assertion is designed to detect on a fresh stack. Repro-state residue was removed (6 overlay rows + 3 audit rows) — environment maintenance on a disposable repro stack, no test or product change — and the re-run `isolated-media-publication3.log` PASSES (1 passed / 21.7s / MEDIA3_EXIT:0). On the fresh smoke stack these counts are naturally 1.
- `full-integration-9failed-isolated.log` — 8 failed / 1 passed / 133.42s / PYTEST_EXIT:1 (re-run of the nine; the navigation-corruption case passed there before the port-ordering regression was understood — the same-source rerun `isolated-6fix-verify.log` 3 failed / 3 passed / 120.69s / PYTEST_EXIT:1 captured the two shim timeouts and the precedence failure; all three then fixed and re-verified, §6).
- `review-diag3.log` / `review-diag4.log` — diagnostic re-runs of failure 8 with step instrumentation (authorize OK → frozen_state OK → admission OK → failure inside the prefix helper). The `1 failed, 1 error` in these logs includes a fixture-teardown `could not find tuple for role 8398488`: an artifact of running multiple integration tests in PARALLEL against the shared PG instance (the cluster-wide `slaif_*` product roles are dropped by each run's teardown while sibling runs still use them). The final unfiltered run is sequential; no product defect claimed from this artifact.
- `browser-diag1.log` — diagnostic re-run of failure 9 capturing the exact PostgresError (`new row for relation "browser_run" violates check constraint "browser_run_preview_binding_shape"`; failing row tail `digest, expiry, attempt=0`).
- `isolated-6fix-verify.log` — 3 failed / 3 passed / 120.69s / PYTEST_EXIT:1 (see above).

**Unit:**

- `patchC-unit-full-proof.log` (23:13:18Z launch, source set e062115+…) — UNIT_EXIT:1 with the child output lost (3-line log); count and cause UNKNOWN, preserved as-is.
- `patchC-unit-full-proof-2.log` (23:16:44Z) — 1 failed / 841 passed / 31.12s / UNIT_EXIT:1 against source `ad06aeb9…`; the subsequent run `patchC-unit-full-proof-3.log` 842 passed / UNIT_EXIT:0 (separate events, not aggregated).
- Final full unit at final source: `unit-full-rerun2.log` — 850 passed, 3 warnings, 26 subtests / PYTEST_EXIT:0.

**Environment (non-product, preserved):**

- CI Foundation PostgreSQL 14/15/16 attempt-1 job-timeout cancellations (run 39243413638, head `565c99c`, 2026-10-19T11:31Z): not test failures — every completed pytest session green in the preserved job logs; the pre-existing 15-minute job budget expired on shared-CI runner slowdown (PG17/18 of the same matrix finished 8.4/11.6 min in). Single documented `--failed` re-run (attempt 2, same head); outcome recorded in §7.1.
- `full-integration-final.log` — the first full run was killed mid-test; the kill left `slaif_test_*` databases whose grants blocked fixture `DROP ROLE`, producing a teardown E-storm in that run's tail. Orphan DBs were dropped and verified zero before `final2`. Retained as a failed run.
- `check-mermaid-final.log` / `check-mermaid-final2.log` — AppArmor `unprivileged_userns` profile denied Chrome's userns sandbox; fixed with the runtime-only `sysctl -w kernel.apparmor_restrict_unprivileged_userns=0`; final `check_mermaid.py` PASS 16 diagrams / exit 0.
- `pnpm lint` exit 2 (×2 observations, `final-gates-node.log` + `pnpm-lint-full.log`) — the untracked `.codex/plugins/cache/…/vinext-starter/eslint.config.mjs` is scanned by root `eslint .` and imports `eslint-config-next` which is not installed at that level; untracked `.codex` is preserved per order and not touched. Scoped evidence: `pnpm --filter @slaif-agent-site/web lint` = 0 and root eslint with `--ignore-pattern .codex/**` = 0 (`pnpm-lint-scoped.log`). Committed tree/CI clean.
- `tools/check_repository.py` exit 1 — exactly 4 errors, all in untracked `.codex/packages/**` license files; 0 errors in repository files (`check-repo-final-full.txt`).
- markdownlint gate exit 1 — 2,580 errors, all under untracked `.codex/**`; 0 in repository files (`markdownlint-final-full.log`).
- Pre-activation base observation reconciled at delivery (order: "reconcile its terminal outcome before delivery"): workflow run 39118686136 (CodeQL) attempt 1 = completed/success; workflow run 39118686133 (CI) attempt 1 = completed/**cancelled**; its only non-success job is `Foundation PostgreSQL 15` (started 2026-10-18T10:17:51Z, cancelled 10:33:07Z, all other PG jobs 14/16/17/18 success; `Dependency review` skipped on the merge commit). Terminal state is not `failed` — no strategy notification triggered; recorded as a base-side observation on the immutable predecessor. No unchanged-base rerun performed.

## 10. Limitations

1. **Legacy v1 honest view.** Stored `review-snapshot/v1` snapshots keep their existing limited read-model view (whose reader already carries the v1 media facts). The view is incomplete by construction and is labeled as such; no omitted data is inferred from current content; v1 bytes cannot qualify for the v2 complete-input approval contract and receive a stable compatibility refusal before any media/canonical effect, with supported recovery through a freshly created/reapplied workspace. Unknown stored versions are refused (no v1 fallback, no live fallback).
2. **Review surface is private.** The frozen review page is no-store/noindex with private media URLs; canonical/public rendering never serves frozen-only content.
3. **Run-bound private bytes are pre-freeze only.** The confined bound-worker private IMAGE+DOCUMENT byte path exists for the live bound run (real 036 consume + trusted binding + 036 no-consume recheck with the ORIGINAL nonce and post-lock invariants); after freeze the read is the immutable snapshot byte gate (076 `slaif_review_media_authorize`), not the run binding.
4. **Composite-FK public dependency-inspection defect** remains disclosed (pre-existing); no patch/monkeypatch/private SQL/Git dependency/upgrade/workaround enters this increment.
5. **PG matrix scope.** CI's foundation PG matrix does not currently select the freeze module; no claim is made that new cases ran all PG versions from unrelated matrix success. The local frozen-media-gate SQL matrix was qualified on PostgreSQL 14.24 and 18.6 containers (independent logs in `/tmp/oap-083-5-a/fn3-probe-v3-corrected-pg14-first-independent-owned.log` / `...pg18...`).
6. **Numeric 083 / MVP / product / release are NOT complete.** Exhaustive immutable operation/dependency/audit binding, durable semantic timeline/resource diff after pending cleanup, generic full-session page-DML publication qualification and re-review remain subsequent separately ordered increments, per the order's explicit non-goals.
7. **Environmental local-gate notes.** `pnpm lint` (exact command) exits 2 locally only because of the untracked `.codex/` plugin cache (scoped lints 0; committed tree/CI clean); `tools/check_repository.py` exit 1 and the markdownlint gate exit 1 are entirely untracked-`.codex` artifacts (0 errors in repository files). The pre-activation base CI run's `Foundation PostgreSQL 15` job cancellation is a base-side observation, reconciled in §8.
