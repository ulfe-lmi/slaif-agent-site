# OAP Coding-Agent Report — 079-a

## Work order

- Identifier: 079-a (legacy flat round ID; first round of the first

  semantic increment of numeric Objective 079, increment 079/1)

- Work-order file: `oap/orders/079-a-media-publication-core.md`
- Work-order sha256: `64a0d06a228bdc58b3b44b83fb27748e7fe4b9a065dc43292cdf8d800070cecb`
- `oap/active` bytes: `079-a\n` (hex `3037392d610a`)
- Numeric objective: 079 (increment 079/1: media publication core)
- PR mode: CREATED_NEW_PR

## Status
COMPLETE

## Executive summary
Implemented the media publication core (079/1) as one bounded semantic
family in one PR: the public object namespace and public-visibility
state (one downgrade-safe migration, 068), the promotion-callable
finalization primitive (`media_service/finalize.py`), the
unauthenticated public digest route with immutable cache headers in both
edge adapters, the authorized preview read path (pinned, not redesigned),
Agent media upload/byte-read and composition media-reference
validation, the real `Image` renderer replacing the placeholder, the
OpenAPI delta, the `dragUntil` flake stabilization (test
infrastructure only), full evidence (unit, renderer, full local E2E
gate, full local gate set, full Compose smoke), and the current-truth
documentation updates with durable wording.

Design note (recorded for strategy review): media assets are
site-scoped, content-addressed, immutable records; the 068 revision
therefore points every product media write path
(`slaif_media_asset_register`, `slaif_agent_media_register`, legacy
`slaif_media_create`/`slaif_media_update`, `slaif_media_public_mark`) at
the physical `content.media_asset_base` relation directly, so the media
COW overlay stays permanently empty and every read path (COW view)
resolves to base. This is what makes R5 cross-session media visibility
(agent upload visible to the editor session's composition validation,
preview render, finalization, and the sessionless public digest route)
possible before the 083 promotion transaction exists. All read paths,
authorization boundaries, the store, `media_gc`, and the COW bootstrap
mechanics are unchanged.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#92](https://github.com/ulfe-lmi/slaif-agent-site/pull/92), state OPEN
- Base/head branches: `main` <- `oap/079-a-media-publication-core`
- Starting remote SHA (= verified remote main at activation): `d8b1d360add9d583fa2cc64c451dd5d6faad8730`
- Implementation head SHA: `1588393693d7bfb7242e1b14cfb97eb88b1d9570`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commits pushed before report: yes (implementation commit `feb28d48d281226e816a5bd35244739662d1f481`, R9 docs commit `cda62d7f919d940b4c0b729ee43823df2131d4dc`, smoke media-e2e CRLF fix commit `fa2102d912bc1495d5814b5a4940568e056b0d42`, envelope count revert commit `e31255b2f571fea39684480e7d57eadd0d77ed4a`, smoke user-census fixture-alignment commit `1588393693d7bfb7242e1b14cfb97eb88b1d9570` = implementation head)
- New PR this turn: yes; amended existing: no; merge performed: NO

## Changes made

1. R1 public namespace + visibility state: migration `068_001_media_publication_core.py` (adds `public_status ENUM('private','public') NOT NULL DEFAULT 'private'` and `published_at timestamptz NULL` to `content.media_asset`; downgrade drops both); `LocalVolumeMediaStore.publish_public` (public object namespace `<root>/public/sha256/<2>/<2>/<digest>`, idempotent hard-link with copy fallback, SHA-256 verified before/after, temp+rename atomic, never touches `.staging`/artifacts); `MediaAssetRecord` public fields + repository mapping; media write functions target `media_asset_base` directly (see design note); `media_gc` unchanged and green.
2. R2 finalization primitive: new `media_service/finalize.py` — `finalize_media_for_promotion(site_id, workspace_id, media_ids) -> FinalizationManifest` (site-owned + workspace-referenced validation, `open_verified` digest check, idempotent `publish_public`, `public_status='public'` + `published_at` via `slaif_media_public_mark`, deterministic manifest, mid-run failure leaves only GC-able unreferenced public objects).
3. R3 public digest route: `GET /v1/public/sha256/<2>/<2>/<digest>` (unauthenticated, streamed, `Content-Type` from validated record, `Content-Length`, `Cache-Control: public, max-age=31536000, immutable`, 404-not-403, no redirects, no media-id/site-id/cookie in URL); nginx `location /media/public/` + apache mirror; `tests/packaging/test_edge_contract.py` asserts the exact public line in both adapters plus `.staging`/artifact negative probes; app-level nosniff removed from the public digest route only (edge `add_header` owns the public-surface nosniff; the exact 3-line `location /media/public/` block is byte-pinned by the edge contract).
4. R4 preview read path: pinned (no redesign) — `GET /v1/sites/{site_id}/assets/{media_id}/content` with `media:read`, exact site binding, fail-closed negatives verified in the hostile suite.
5. R5 Agent media semantics: `POST /api/agent/v1/media/assets` (`media:upload`, bounded streaming through the store, `upload_quota`/`upload_used` accounting, idempotency-keyed, semantically audited `MEDIA_UPLOADED`) and `GET /api/agent/v1/media/assets/{media_id}/content` (`media:read`, digest-verified streaming); `control_api/route_policy.py` gains exactly the two ordered entries; existing `GET /api/agent/v1/media/` unchanged; composition `Image.mediaId` reference validation (exists, same site, MIME-class compatible; bounded 422 `COMPONENT_BINDING_INVALID` on both Agent and Editor paths; row version/idempotency/audit unchanged on rejection).
6. R6 real `Image` renderer: `render_api/projection.py` resolves per-Image media descriptors (preview = R4 authenticated URL; public = R3 digest URL only when `public_status='public'`; otherwise fail-closed marker); `apps/web/src/renderer/components.tsx` emits `<img class="sl-image" src alt loading="lazy" referrerpolicy="no-referrer">` for resolved descriptors and the existing placeholder pattern for fail-closed markers; `renderer-v1.css` sl-image rules; deterministic attribute order, no inline styles, no handlers; preview/public markup identical except `src` form (byte-pinned in E2E parity check).
7. R7 OpenAPI: `contracts/openapi/agent-v1.json` regenerated — diff contains only the two R5 paths; drift gate green.
8. R8 evidence: new unit suite `test_media_public_core.py` (publish_public idempotency/digest-verify/failure modes, finalization manifest positive + mid-run failure, preview authorization matrix, R5 bounded error keys); extended `renderer-behavior.test.ts` (exact `<img>` markup pins, forbidden-attribute absence, fail-closed placeholder); new `tests/e2e/media-publication.spec.ts` (human + agent uploads, preview render with byte-identical fetch, direct finalization call, public digest byte-identity + immutable headers, preview/public markup parity, 14-case hostile suite, exact COW audit rows, restart survival without re-finalization, edge contract probes); `e2e.sh` gained the 13th project; `smoke.sh` `media-e2e` contract extended to post-finalization public read with immutable-cache pin (the human-editor envelope count stays 9: the media upload is tracked in `control.media_idempotency`, not `control.human_editor_idempotency`).
9. R10 dragUntil stabilization: `tests/e2e/governance.spec.ts` deterministic drag mechanics (bounded intermediate mouse steps with waits on deterministic element state); assertion set unchanged in meaning; full local E2E gate green without re-runs.
10. Test alignment to the 068 base-write semantics: `test_media_service.py` and `test_media_security_lifecycle.py` updated where they asserted the pre-068 workspace-overlay isolation for media records (media is site-scoped/immutable; the COW overlay is empty by design); small fixture/schema updates in six integration files and four unit files for the new column/function surface.

## Files changed
Base `d8b1d360add9d583fa2cc64c451dd5d6faad8730` -> implementation head
`1588393693d7bfb7242e1b14cfb97eb88b1d9570` (52 files, +4606/-73; the
report file itself is added by the SELF commit and is not counted here):

| Category | Files | +lines | -lines |
|---|---|---|---|
| Production/config | 26 | 1078 | 12 |
| Migrations | 1 | 657 | 0 |
| Tests/evidence | 18 | 1881 | 49 |
| Generated artifacts | 1 | 312 | 1 |
| Docs | 4 | 11 | 10 |
| OAP transcript | 2 (order + active; report via SELF) | 667 | 1 |

Production/config = `media_service/{store,media_http,finalize,database}.py`,
`agent_api/{agent_http,app,config}.py`, `agent_state/{mutations,reads}.py`,
`bootstrap/service.py`, `content_model/{media_models,service}.py`,
`control_api/route_policy.py`, `db/privileges.py`,
`editor_api/composition_http.py`, `render_api/projection.py`,
`apps/web/src/renderer/components.tsx`, `apps/web/public/renderer-v1.css`,
`apps/web/src/sites/render.ts`, `infra/nginx/nginx.conf`,
`infra/apache/slaif-agent-site.conf`, `compose.yaml`,
`playwright.config.ts`, `tools/compose/{e2e,smoke,verify}.sh`.

## Acceptance-criteria evidence
### Criterion 1 (migration up/down, columns present, catalog byte-identical)

- Migration up: applied by bootstrap on every E2E/smoke stack from verified base; `content.media_asset.public_status`/`published_at` asserted by unit suite and the E2E plain-psql `public_status='public'` check (2/2 rows public with `published_at` set after the finalization call).
- Downgrade-safe: `068_001` downgrade drops both columns; `test_bootstrap_downgrade_049_preflight_is_atomic[*]` (4) and `test_bootstrap_downgrade_compatible_path_rehardens_after_round_trip` pass in the full integration run (235 passed).
- `060_001` and catalog artifacts: no catalog change in this diff (R11) — `catalog-v1.json`/`060_001` absent from the file list.

### Criterion 2 (publish_public + finalization unit suite green)

- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`: PASSED (includes `test_media_public_core.py`: idempotency, digest verification, exact failure manifests, GC-able-only residue).

### Criterion 3 (public digest route)

- Unit + E2E: unauthenticated byte-identical read with exact `Cache-Control: public, max-age=31536000, immutable`; 404 (not 403) for non-public/absent/forged digests (exact `RESOURCE_NOT_FOUND` envelope pinned); exact public line in both edge adapters asserted by `test_edge_contract.py`; `.staging`/artifact negative probes green (404, bytes never served).
- Smoke: `media-e2e: OK edge=nginx upload=validated-private-read=byte-identical finalization=public-read=byte-identical immutable-cache=verified`.

### Criterion 4 (preview authorization matrix + agent upload/byte read, COW audit exact)

- Unit: preview authorization matrix (member/foreign-site/revoked/session-less/staging-path) green.
- E2E: agent upload 201 + quota/audit; agent byte read byte-identical; cross-site private read 404 (envelope pinned, bytes never leak); COW audit rows exact (`audit.agent_mutation` `MEDIA_UPLOADED` row, `control.agent_idempotency` row, `audit.human_editor_mutation` rows) verified by plain psql in the spec.

### Criterion 5 (real Image renderer markup pins + parity + fail-closed)

- `pnpm exec vitest run apps/web/tests/renderer-behavior.test.ts`: PASSED (preview URL form, public digest URL form, alt text, lazy loading, referrerpolicy, no inline style/event handlers, fail-closed placeholder).
- E2E parity: preview/public markup identical except `src` form (byte-pinned replacement equality in the spec).

### Criterion 6 (hostile E2E suite >= 12 cases, exact keys, SVG rejected, bounds, restart)

- 14 hostile cases, all green in the clean full-gate run: cross-site private byte read (404 + `RESOURCE_NOT_FOUND` + no bytes), forged digest (404 + envelope), unknown digest (404 + envelope), staging namespace unrouteable (404), private object namespace unrouteable (404), path traversal (404/422, no bytes), SVG upload rejected (422 `DOMAIN_VALIDATION_FAILED`, not sanitized/stored), oversized upload (413 edge body limit), missing idempotency key (400 `IDEMPOTENCY_KEY_REQUIRED`), foreign-mediaId prop (422 `DOMAIN_VALIDATION_FAILED` with `details.prop_error=COMPONENT_BINDING_INVALID`), corrupt public digest read (503 while corrupted, 200 byte-identical after restore), revoked capability (401 `AUTHENTICATION_REQUIRED`), non-member preview denial (seeded non-platform-admin local user: preview 404 + private media 404; platform-admin control 200 proves the denial is membership-based), revoked human session (stale re-added token: preview 404, media 404).
- Restart: public bytes survive `docker compose restart media-service` without re-finalization (byte-identical 200 + immutable headers; bounded readiness wait, at most 30 s).

### Criterion 7 (OpenAPI exact delta + drift gate)

- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`: PASSED; diff vs base limited to the two R5 paths.

### Criterion 8 (R9 docs, durable wording, adversarial sweep)

- Six surfaces updated per R9(a)-(h) with verified merge facts only; adversarial sweep for stale live-state claims ("078/8 is opened", "PR pending" for 078/8, "Agent media in 079" as sole plan) over README, INCREMENTS, MVP-PROGRESS, MVP-CONTRACT-AUDIT, CRITICAL.md returns nothing (CRITICAL.md verified, no current-state media/078/079 claims, unedited).

### Criterion 9 (dragUntil stabilization bounds + full local E2E green)

- R10 changes confined to `tests/e2e/governance.spec.ts` (drag mechanics only; same scenarios, same assertions); full local E2E gate (all 13 projects) green without re-runs in the clean no-load run (see Local verification).

### Criterion 10 (no R11 violation)

- `uv.lock`/`pnpm-lock.yaml` byte-identical to base (verified by `git diff` at commit time); no `tools/supply_chain/`, `tests/supply_chain/`, or `.github/workflows/` changes; no new dependency; exactly one migration; endpoints limited to R3/R5; no new scope strings; no secrets in diff or report (fixture credentials are fake placeholders, compose-stack only).

### Criterion 11 (CI: all 20 required checks on the report-only head)

- All 20 required checks SUCCESS at implementation head `1588393693d7bfb7242e1b14cfb97eb88b1d9570` (CI run `35768124722` + CodeQL run `35768124796`; per-check table in the GitHub CI section below). The report-only SELF commit may trigger fresh checks; strategy verifies the SELF head independently.

## Local verification

- `uv lock --check`: PASSED
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED
- `uv run --frozen mypy`: PASSED (286 files)
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`: PASSED
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED — `235 passed in 2435.64s (0:40:35)` (gate run 2026-09-22; standalone clean run also `235 passed in 2623.49s (0:43:43)`)
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED
- `python -m compileall -q tools tests/repository`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED
- `python -m unittest discover -s tests/supply_chain -p 'test_*.py'`: PASSED
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`: PASSED
- `python tools/check_repository.py`: PASSED
- `python tools/check_mermaid.py`: PASSED
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED
- Process smokes (`python -m slaif_agent_site.{control_api,editor_api,agent_api,render_api,mcp_adapter,media_service,review_worker,scheduler,media_gc,bootstrap} --check`): all 10 PASSED
- `node --version` / `pnpm --version`: 24.x / 11.22.0
- `pnpm install --frozen-lockfile`: PASSED
- `pnpm lint`: PASSED
- `pnpm format:check`: PASSED
- `pnpm typecheck`: PASSED
- `pnpm test`: PASSED
- `pnpm build`: PASSED
- `pnpm licenses list --json`: PASSED
- Post-gate re-verification (four test-only changes after the 19:21 gate run: the E2E spec audit-scope fix, the smoke media-e2e CRLF fix, the human-editor envelope count revert to the base 9, and the smoke user-census fixture alignment for the 079-a E2E denied-user fixture): `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test` (includes `pnpm build`), and `pnpm licenses list --json` all re-run PASSED on the final tree; `uv run --frozen ruff check`/`ruff format --check` over `tools` and `tests/packaging` plus `python -m unittest tests.packaging.test_compose_smoke_contract` PASSED on the final tree; the `services/backend` Python tree is byte-identical to the gate run (verified by file-mtime scan against the gate log); the full E2E driver and the full Compose smoke were re-run on the final tree (below).
- `pnpm exec vitest run apps/web/tests/renderer-behavior.test.ts`: PASSED
- Full local E2E gate (clean no-load cycle, `docker compose -p slaif0075b down -v` then `up --build --wait` + `verify.py` + the real `sh tools/compose/e2e.sh`, all 13 projects, run r4 completed 2026-09-22 19:39:07 CEST): `browser-e2e: PASSED project=media-publication contract=media-publication-core-human-agent-preview-finalize-public-hostile` and `compose-e2e: OK projects=13 setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2 media-publication=1 artifacts=disabled` (23/23 contracts PASSED, 0 FAILED; log `/tmp/e2e-full-079a-r4.log`)
- Full Compose smoke `sh tools/compose/smoke.sh slaif0075a`: PASSED — definitive fresh-stack run (stack torn down with `docker compose -p slaif0075a down -v` first), started 2026-09-22 20:35 CEST, `SMOKE-FINAL3-WRAPPER rc=0` at 20:48 CEST (log `/tmp/smoke-079a-final3.log`). Exact key lines: `compose-e2e: OK projects=13 setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2 media-publication=1 artifacts=disabled`; `media-e2e: OK edge=nginx upload=validated-private-read=byte-identical finalization=public-read=byte-identical immutable-cache=verified`; `human-editor-envelope: OK workspace=HUMAN active audit=idempotent sequence=page-create,theme-update,page-style-update,page-style-update,component-add,component-add,component-move,component-add count=9`; `governance-e2e: OK visible=create-profile-domains-membership-archive negatives=verified devices=6 users=4`

## GitHub CI / required checks

- First CI run (head `feb28d48d281226e816a5bd35244739662d1f481`, runs 35762532468 CodeQL + 35762532600 CI): 19/20 SUCCESS; the single FAILURE was `Compose and edge packaging` — the CI-side full smoke failed at exactly the same point as local smoke: the R8 `media-e2e` immutable-cache grep (`curl -sD -` emits CRLF-terminated header lines, so the `$`-anchored match could never pass). This is the R8 test-instruction bug fixed by commit `fa2102d` (`tr -d '\r'` before the match; assertion unchanged), not a product defect: the public read itself returned 200 byte-identical with the exact header in every observed response.
- Intermediate CI runs: head `fa2102d912bc1495d5814b5a4940568e056b0d42` (runs 35765262230 CodeQL + 35765262379 CI): CodeQL SUCCESS; CI run superseded/cancelled by the next push. Head `e31255b2f571fea39684480e7d57eadd0d77ed4a` (runs 35766205309 CodeQL + 35766205215 CI): CodeQL SUCCESS; CI 14/15 jobs SUCCESS with the single FAILURE again `Compose and edge packaging` — the CI-side full smoke failed at the governance user-census check for the same deterministic reason as local smoke (the 079-a E2E spec seeds a fourth, expected, non-admin `control.user_account` row `oap079a.denied`; the pre-existing census pinned `count(*) = 3`): `media-e2e: OK` and `human-editor-envelope: OK count=9` had both printed before the exit. Fixed test-only by commit `1588393` (census extended to exactly 4 with an exact-row FILTER on the denied fixture; packaging contract test aligned); not a product defect.
- State observed for implementation head `1588393693d7bfb7242e1b14cfb97eb88b1d9570`:

| Required check | State (head 1588393) |
|---|---|
| Compose and edge packaging | SUCCESS (CI 35768124722, 11m25s) |
| Dependency review | SUCCESS (CI 35768124722, 8s) |
| Foundation PostgreSQL 14 | SUCCESS (CI 35768124722, 13m2s) |
| Foundation PostgreSQL 15 | SUCCESS (CI 35768124722, 10m34s) |
| Foundation PostgreSQL 16 | SUCCESS (CI 35768124722, 12m22s) |
| Foundation PostgreSQL 17 | SUCCESS (CI 35768124722, 13m11s) |
| Foundation PostgreSQL 18 | SUCCESS (CI 35768124722, 9m32s) |
| Markdown | SUCCESS (CI 35768124722, 10s) |
| Mermaid | SUCCESS (CI 35768124722, 57s) |
| Node contracts | SUCCESS (CI 35768124722, 2m17s) |
| Python 3.12 quality and package | SUCCESS (CI 35768124722, 40s) |
| Python 3.13 quality and package | SUCCESS (CI 35768124722, 40s) |
| Python 3.14 quality and package | SUCCESS (CI 35768124722, 48s) |
| Repository policy | SUCCESS (CI 35768124722, 10s) |
| Supply-chain evidence | SUCCESS (CI 35768124722, 12m2s) |
| Analyze (actions) | SUCCESS (CodeQL 35768124796, 34s) |
| Analyze (javascript-typescript) | SUCCESS (CodeQL 35768124796, 1m6s) |
| Analyze (python) | SUCCESS (CodeQL 35768124796, 1m49s) |
| CodeQL | SUCCESS (CodeQL 35768124796, 3s) |
| Detect supported languages | SUCCESS (CodeQL 35768124796, 5s) |

- All required green at drafting: yes — all 20 required checks SUCCESS at implementation head `1588393693d7bfb7242e1b14cfb97eb88b1d9570` (observed 2026-09-22 20:49 CEST); the report-only SELF commit may trigger fresh checks, which strategy verifies independently

## Local setup / dependencies

- No new packages/dependencies. Existing toolchain: uv 0.12.5, Node 24.x, pnpm 11.22.0, Docker Compose, PostgreSQL (scratch test cluster + compose stacks), Playwright 1.62.1 (Chromium/Firefox/WebKit), `markdownlint-cli2@0.23.2` via npx (temporary, no production dependency).
- Guest-sudo setup used for: nothing new this round (scratch PG, browsers, and packages already provisioned).
- No durable committed/documented setup change.

## Documentation

- `oap/INCREMENTS.md`: 078/9 row closed with verified PR #89 merge fact; 078 `Next` cell extended with the 079/1 in-flight fact (`079-a`, opened at verified remote main `d8b1d360add9d583fa2cc64c451dd5d6faad8730`; PR pending; strategy owns acceptance and merge); preamble extended to 078/1-078/9 with the 078/079 seam acknowledged.
- `oap/MVP-PROGRESS.md`: active-sequence paragraph + status rows 078/079 updated with verified merge facts and the 079/1 open row.
- `README.md`: capability row extended with the 078/9 merge fact, the 078/079 seam, and the 079/1 open row; GitHub-authoritative sentence preserved.
- `oap/MVP-CONTRACT-AUDIT.md`: media row Next cell updated to the 079/1 scope + 083 remainder; evidence cell unchanged at this head.
- `CRITICAL.md`: verified, no current-state media/078/079 claims, unedited.

## Safety and scope confirmations

- Unrelated files changed: no (every changed file is listed above and maps to R1-R10 or required test alignment for the 068 surface).
- Production secrets accessed: NO; production systems accessed: NO (compose dev stacks + disposable scratch PostgreSQL only; all credentials fake fixtures).
- Required tests skipped/not run: NO — every named R8/R10 evidence command ran and passed (exact outputs above); the two transient VM-timing flakes, one deterministic E2E spec bug, and the deterministic smoke-instruction bugs found mid-round are documented below (Known limitations), and the definitive clean no-load full-gate run and the definitive full Compose smoke are green.
- Scope deviation: NO beyond the predeclared budget (overage justified in the cumulative size table: production/config and test/evidence file counts exceed the predeclared numbers because the 068 base-write redesign touches existing media write surfaces and the new hostile E2E matrix required fixture alignment in eight integration files, four unit files, and one packaging-contract file — each touch is 1-11 lines except the listed core files).
- Extra objective PR: NO; coding-agent merge: NO.
- Activated order/`oap/active` edited: NO (committed byte-identical: order sha256 `64a0d06a...`, active `079-a\n`).
- Report commit changes only this report: yes.

## Cumulative base->head size (2026-09-14 review-unit governance Section 2)
Base `d8b1d360add9d583fa2cc64c451dd5d6faad8730` -> implementation head:

| Category | Files | +lines | -lines |
|---|---|---|---|
| Production/config | 26 | 1078 | 12 |
| Migrations | 1 | 657 | 0 |
| Tests/evidence | 18 | 1881 | 49 |
| Generated artifacts | 1 | 312 | 1 |
| Docs | 4 | 11 | 10 |
| OAP transcript | 2 (order + active; report via SELF) | 667 | 1 |

Predeclared budget (order Section 10) check: production/config 14 predeclared — actual 26 (justification: the disclosed 068 base-write redesign touches the existing media write surface — `content_model/{media_models,service}.py`, `agent_state/{mutations,reads}.py`, `editor_api/composition_http.py`, `control_api/route_policy.py`, `db/privileges.py`, `media_service/{database,store,media_http}.py` — plus the R4/R5 human+agent media surface (`agent_api/{agent_http,app,config}.py`, `bootstrap/service.py`), the R6 renderer (`render_api/projection.py`, `components.tsx`, `renderer-v1.css`, `render.ts`), and edge/packaging (`nginx.conf`, `slaif-agent-site.conf`, `compose.yaml`, `playwright.config.ts`, `tools/compose/{e2e,smoke,verify}.sh`); every non-core touch is 1-21 lines); migrations 1 — actual 1; tests/evidence 7 predeclared — actual 18 standalone files (justification: the 14-case hostile matrix plus 068-surface fixture alignment required small touches (1-11 lines each) in eight integration files, four unit files, and one packaging-contract file beyond the predeclared set — `test_agent_mutations`, `test_agent_page_style`, `test_control_database_integration`, `test_database_bootstrap`, `test_editable_domain_proof`, `test_human_agent_session_control`, `test_media_service`, `test_media_security_lifecycle`, `test_control_database`, `test_foundation_contract`, `test_health_apps`, `test_route_policy`, `test_compose_smoke_contract` (smoke user-census fixture alignment for the 079-a E2E denied-user fixture); the predeclared `smoke.sh` expectation line is counted under production/config above, as are `e2e.sh`/`verify.py`); generated 2 — actual 1; docs 5 — actual 4 (CRITICAL.md verified no-claim, unedited per R9(h)); substantive implementation lines <= 2.0k — actual 1735 (production/config +1078 + migration +657; generated artifact +312/-1 is a regenerated contract, test/evidence +1881 excluded from substantive scale).

## Known limitations / blockers

- Two transient local flakes (not the R10 dragUntil class): during a CPU-loaded window (parallel gate set), the pre-existing `desktop-firefox` auth contract and, in a separate clean cycle, the pre-existing preview "renderer theme tokens" contract each failed once on VM timing; both passed on re-run and in the definitive clean no-load full-gate run. No product-code change resulted.
- One deterministic E2E spec bug (found by the first full-driver run that reached the `media-publication` project, clean no-load cycle r3): the spec's editor-audit assertion counted every `POST .../composition/components` row for the shared parity fixture page and expected exactly 2, but the full driver's earlier `preview` project (bounded-embed-family contract) legitimately creates and audits two editor components on that same page, making the count 4. Fixed with a spec-only change (no product code): the assertion is scoped to the two component IDs this spec creates (`resource_id IN (...)`), still requiring exactly one `201` audited row each with the exact action and the pinned preview workspace — the order's "COW audit rows exact for agent upload + reference mutation" — and the two creates additionally pin `id` + `row_version = 1`. The definitive clean no-load full-gate run (r4) is green.
- Three deterministic smoke-instruction bugs (found by the first full smoke runs, local and CI, and fixed test-only before the final green run): (1) the R8 `media-e2e` immutable-cache grep anchored `$` against `curl -sD -` output, but curl emits CRLF-terminated header lines, so the match could never succeed — `tr -d '\r'` added before the match, assertion unchanged; (2) the human-editor envelope idempotency count was bumped 9 -> 10 on the assumption the media upload is tracked in `control.human_editor_idempotency`, but it is tracked in `control.media_idempotency` — the expected count reverted to the base 9 (8 audited POST/PATCH editor mutations plus the 1 DELETE mutation whose audit action falls outside the 8-row audit filter); (3) the pre-existing governance user census pinned `count(*) = 3` in `control.user_account`, but the 079-a E2E spec (non-member preview denial case) seeds a fourth, expected, non-platform-admin LOCAL row `oap079a.denied` (UUID `12000000-0000-4000-8000-000000000309`, fake argon2 placeholder) that legitimately persists in the disposable smoke database at census time — the census was extended to `count(*) = 4` with an additional exact-row FILTER pinning the fixture (id/usernames/normalized/hash-present/display-name/email-NULL/oidc-NULL/non-admin), never loosening the two existing exact FILTERs, and `tests/packaging/test_compose_smoke_contract.py` aligned; the new query was pre-validated against a disposable PostgreSQL with positive + three negative controls (old count, stray fifth user, tampered display name all return `f`).
- Public-byte retention/GC semantics for the public namespace remain 083/089-bound (out of scope by design); `media_gc` unchanged.

## Recommended strategic follow-up

- None required for 079/1; strategy may proceed to independent verification and acceptance. Next increments per the ledger: 079/2 (`079-2-a`) and 079/3 (`079-3-a`) for the remaining catalog types.
