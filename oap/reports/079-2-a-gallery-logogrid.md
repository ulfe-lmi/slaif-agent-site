# OAP Coding-Agent Report — 079-2-a

## Work order

- Identifier: 079-2-a (increment-qualified round ID: first round of the
  second semantic increment of numeric Objective 079, increment 079/2)
- Work-order file: `oap/orders/079-2-a-gallery-logogrid.md`
- Work-order sha256: `d2ee17f949906e939edd18316366d1dd35e6d2b41dbf1080beea8fe5b81224bf`
- `oap/active` bytes: `079-2-a\n` (hex `3037392d322d610a`)
- Numeric objective: 079 (increment 079/2: Gallery + LogoGrid media-reference
  list components)
- PR mode: CREATED_NEW_PR

## Status
BLOCKED

## Executive summary
Implemented the media-reference list component family (079/2) as one bounded
semantic increment in one PR: two new catalog types (Gallery basic, LogoGrid
institutional) with the R1 prop contracts, agent + editor list-item validation
with the exact bounded error keys, projection descriptor resolution for
list-valued media-reference props with trusted Gallery/LogoGrid renderers
(preview/public markup parity), regenerated catalog/060_001/OpenAPI artifacts
(x-slaif-* only; strip-identity proven byte-identical), the full local
evidence set (unit, renderer, E2E, full local gate, full Compose smoke rc=0),
and the R5 current-truth documentation with durable wording. Every locally
nameable R1-R7 evidence command ran and passed on the final tree.

The round is BLOCKED, not COMPLETE, on one external, pre-existing packaging
fact unrelated to this diff: the two Docker-image-build CI checks
(`Compose and edge packaging` and `Supply-chain evidence`) both fail at the
exact implementation head, with the same root cause, because the Alpine v3.23
package index rotated out the exact-version pin
`libcrypto3/libssl3=3.5.8-r0` that the repository Dockerfiles already carried
at base (introduced by merged commit `b946d26`); every Docker build of this
repository, including unmodified `main`, now fails at the `apk add` step
(reproduced directly on the pinned base image). The pin is a supply-chain
build-gate decision owned by an earlier objective and is outside this order's
bounded scope (order §4 "Nothing else"; §5 non-goals), so per protocol §10
the executor identifies the decision, publishes the exact truth, and returns
authority to strategy instead of deciding it silently. The minimal candidate
fix is documented with exact evidence in Known limitations / blockers.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#93](https://github.com/ulfe-lmi/slaif-agent-site/pull/93), state OPEN (mergeable)
- Base/head branches: `main` <- `oap/079-2-a-gallery-logogrid`
- Starting remote SHA (= verified remote main at activation, re-fetched
  immediately before push): `577509e7bc990d85a10af5954bee3c6f7c888a4f`
- Implementation head SHA: `0ab21e622e6fc5cac8bb931248332e0272ee1e28`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub by strategy)
- Implementation commits pushed before report: yes — implementation commit
  `ef2298f5f799613598f760ae3703cbd084990b95` (28 files, +2520/-66) and R5 docs
  commit `0ab21e622e6fc5cac8bb931248332e0272ee1e28` (4 files, +8/-6) =
  implementation head
- New PR this turn: yes; amended existing: no; merge performed: NO

## Changes made

1. R1 catalog +2 (29 -> 31): `content_model/component_catalog.py` declares
   `Gallery` (category basic; leaf; `title` localized 1..120 optional;
   `items` 1..12 of exactly `{mediaId reference/uuid, alt string 1..4096,
   aspectRatio enum auto|16:9|4:3|1:1 optional default auto}`; `columns` enum
   "2"|"3"|"4" optional default "3") and `LogoGrid` (category institutional;
   leaf; `title` localized 1..120 optional; `items` 2..24 of exactly
   `{mediaId reference/uuid, name string 1..120}`); no raw url/src/html/style/
   class/script input; no data binding; deterministic in-place `060_001`
   baked-catalog regeneration + `CATALOG_V1_REVIEWED_SHA256` guard (2-line
   JSON/SHA diff only); all generated artifacts regenerated and all three
   generator `--check` gates zero-diff.
2. R2 mutation + editor enforcement: `content_model/component_facets.py`
   gains `MEDIA_REFERENCE_COMPONENTS` (Gallery 1..12, LogoGrid 2..24) and
   `validate_media_reference_items` wired into BOTH the agent mutation path
   (`agent_state/mutations.py` `_validate_media_reference_props`, base-merge
   semantics preserved) and the human Editor/Puck path
   (`editor_api/composition_http.py` add/update component whole-document
   validation). Per item: exists / same site / mime in image/png|image/jpeg,
   list bounds checked before per-item, with the exact bounded error keys
   `{gallery,logogrid}.{item-missing,item-foreign-site,item-not-image,
   items-out-of-range}` (all registered in `MEDIA_REFERENCE_ERROR_KEYS`);
   `agent_api/agent_http.py` maps the media keys to bounded 422
   `details.prop_error` without user-input echo; rejection leaves tree, row
   version, idempotency, and audit unchanged.
3. R3 projection + trusted renderers: `render_api/projection.py` extends the
   079/1 media-descriptor resolution to list-valued media-reference props —
   each `mediaId` resolves to `{url, mime_type, size_bytes}` (preview: 079/1
   preview URL; public: 079/1 digest URL only when
   `public_status='public'`; else fail-closed marker) with props re-validated
   at projection time (defense in depth, 078/8 pattern);
   `apps/web/src/renderer/components.tsx` renders the exact ordered Gallery /
   LogoGrid markup (CSS grid, `<h3>` when titled, one `<li>` per item,
   079/1 `sl-image` pattern with alt/loading=lazy/referrerpolicy=no-referrer
   and `designClasses` aspect tokens, 079/1 placeholder pattern for
   fail-closed items) and `apps/web/public/renderer-v1.css` adds the
   responsive grid/square-box rules; deterministic attribute order, no JS,
   no event handlers, no inline style attributes; preview/public markup
   identical except `src` form (E2E byte-pinned).
4. R4 OpenAPI: `contracts/openapi/agent-v1.json` regenerated; the diff is
   exactly four `x-slaif-*` extension values on the two component-mutation
   operations (see Criterion 6); strip-identity proven (Criterion 6).
5. R5 current-truth docs (separate commit after PR creation, actual PR
   number per the order): `oap/INCREMENTS.md` (079/1 row closed with verified
   PR #92 merge fact; 079/2 in-flight row in the standard form; Next row
   advanced), `oap/MVP-PROGRESS.md` (sequence paragraph + 078/079 status
   rows), `README.md` (capability row), `oap/MVP-CONTRACT-AUDIT.md` (media
   row evidence + Next cells); `CRITICAL.md` verified — no current-state
   079/079-a claim, unedited. Adversarial sweep for stale 079/1 in-flight
   wording over the five surfaces returns nothing.
6. R6 evidence: new `services/backend/tests/unit/test_render_projection_media.py`
   (270 lines: list-descriptor resolution positives/negatives, mixed
   resolved + fail-closed markers, public-only-when-public, foreign-site
   marker); extended `services/backend/tests/unit/test_component_facets.py`
   (+221 lines: bounds, exact error keys, foreign-site, non-image MIME,
   duplicate items, alt/name bounds); extended
   `apps/web/tests/renderer-behavior.test.ts` (+210 lines: exact Gallery
   2/3/4-column + LogoGrid markup pins, title present/absent, mixed
   resolved/fail-closed items, forbidden-attribute absence); extended
   `tests/e2e/media-publication.spec.ts` (+573 lines: parity composition
   Gallery@22/LogoGrid@23 render at desktop 1280x720 + tablet 768x1024,
   preview/public markup parity, hostile Agent suite — 12 PATCH cases with
   exact keys and row version pinned unchanged — and hostile Editor suite —
   2 POST + 10 PATCH cases — plus the existing 079/1 sections re-verified).
   Mechanical ripple (078/7-078/8 class, disclosed per file): catalog count
   pins 29 -> 31 in `test_component_catalog.py`,
   `packages/component-catalog/tests/index.test.ts`,
   `packages/composition-schema/tests/index.test.ts`,
   `packages/composition-schema/tests/puck-adapter.test.ts`, and
   `tools/compose/public_agent_acceptance.py` (the public agent acceptance
   proof's component-catalog count assertion, same one-line assertion bumped
   22 -> 27 in 078/7 commit `137abbc` and 27 -> 29 in 078/8 commit
   `b470a1e`); property-scope pin 63 -> 68 in `test_design_system.py`;
   conditional-scope pin 62 -> 67 in `test_route_policy.py`; agent mutation
   catalog type-set 29 -> 31 in `test_agent_mutations.py`.
7. R7: no supply-chain/workflow/lockfile change; no new dependency; no new
   migration file; no new endpoint/scope; no secrets in diff or report
   (fixture credentials are declared fake, compose-stack only).

## Files changed
Base `577509e7bc990d85a10af5954bee3c6f7c888a4f` -> implementation head
`0ab21e622e6fc5cac8bb931248332e0272ee1e28` (32 files, +2528/-72; the report
file itself is added by the SELF commit and is not counted here):

| Category | Files | +lines | -lines |
|---|---|---|---|
| Production/config | 10 | 534 | 54 |
| Migrations | 0 | 0 | 0 |
| Tests/evidence | 11 | 1283 | 7 |
| Generated artifacts | 5 | 354 | 4 |
| Docs | 4 | 8 | 6 |
| OAP transcript | 2 (order + active; report via SELF) | 349 | 1 |

Production/config = `content_model/{component_catalog,component_facets,
design_system}.py`, `agent_state/mutations.py`, `agent_api/agent_http.py`,
`editor_api/composition_http.py`, `render_api/projection.py`,
`db/alembic/versions/060_001_agent_component_semantics.py` (in-place
baked-catalog regeneration counted here per the order §10 production line),
`apps/web/src/renderer/components.tsx`, `apps/web/public/renderer-v1.css`.
Migrations = none (order R1: deterministic migration N/A, in-place 060_001
only). Tests/evidence = `test_component_facets.py`,
`test_render_projection_media.py` (new), `renderer-behavior.test.ts`,
`media-publication.spec.ts`, `test_component_catalog.py`,
`index.test.ts` (component-catalog), `index.test.ts` (composition-schema),
`puck-adapter.test.ts`, `test_design_system.py`, `test_route_policy.py`,
`test_agent_mutations.py`, plus the smoke expectation
`tools/compose/public_agent_acceptance.py` (1 line). Generated artifacts =
`contracts/openapi/agent-v1.json`, `catalog-v1.json` x2,
`design-system-v1.json` x2 (design-system regeneration is the deterministic
byproduct of the catalog change).

## Acceptance-criteria evidence
### Criterion 1 (catalog 31, contracts, zero-diff, 060_001 consistent, pins)

- Catalog 31: `test_component_catalog.py` (31) and both package index tests (31) green; `puck-adapter` config keys 31 green.
- R1 prop contracts: unit suite covers exact item shape (additionalProperties false), bounds, enum values (columns strings "2"/"3"/"4"), title/alt/name lengths, optional defaults; E2E hostile suite re-proves them live (422 exact keys).
- Generator `--check` zero-diff: `python tools/generate_component_catalog.py --check` -> `component-catalog: OK catalog-v1 Python/TypeScript semantic equality`; `python tools/generate_design_system.py --check` -> `design-system: OK`; `uv run --frozen python -m tools.contracts.generate_agent_openapi --check` -> `agent-openapi: OK contracts/openapi/agent-v1.json` (final tree, 2026-10-03).
- In-place `060_001` consistent: diff is exactly the baked `_CATALOG_V1_JSON` line + `CATALOG_V1_REVIEWED_SHA256` (2 insertions / 2 deletions); bootstrap applied it on every E2E/smoke stack; integration suite green.
- All four existing catalog count pins updated (see Changes made 6) plus the acceptance-proof pin; no count pin left at 29 (verified by the green gate set and by the smoke acceptance stage passing).

### Criterion 2 (mutation/editor validation suite, exact keys, no version change)

- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`: PASSED (710 passed) including the extended `test_component_facets.py` matrix (bounds 1..12 / 2..24, exact keys, foreign-site, non-image MIME, duplicate items allowed, alt/name bounds) and `test_agent_mutations.py` (type-set 31; catalog guard behavior).
- E2E: hostile Agent PATCH suite (12 cases) and hostile Editor suite (2 POST + 10 PATCH) all 422 with the exact `details.prop_error` key; row version pinned unchanged (1) after every rejection; idempotency/audit unchanged by the spec's audit-row assertions.

### Criterion 3 (projection list-descriptor resolution)

- New `test_render_projection_media.py` (within the 710-passed unit run): preview URL form per item, public digest URL only when `public_status='public'`, fail-closed marker for missing/foreign/non-image, mixed resolved + fail-closed lists, defense-in-depth re-validation at projection time.
- E2E: after 079/1-style direct finalization, public rendering serves Gallery/LogoGrid items from the digest URLs byte-identical (spec byte-identity fetches).

### Criterion 4 (renderer markup pins, forbidden attributes, parity)

- `pnpm test` (root, includes `apps/web/tests/renderer-behavior.test.ts`): PASSED on the final tree — Gallery 2/3/4 columns, title present/absent, LogoGrid resolved + fail-closed, exact `sl-gallery`/`sl-logogrid` markup, no inline style, no event handlers, no sandbox/target.
- E2E parity: preview/public markup identical except `src` form (byte-pinned replacement equality in the spec), at desktop 1280x720 and tablet 768x1024.

### Criterion 5 (E2E green: three viewports, hostile rejections, public byte-identity)

- Clean debug-stack run (fresh `slaif007dbg2`, setup + parity seed + demo-site human workspace): `browser-e2e: PASSED project=media-publication contract=media-publication-core-human-agent-preview-finalize-public-hostile`, `browser-e2e: OK`, rc=0.
- Full Compose smoke (13 projects, including all other e2e contracts): `compose-e2e: OK projects=13 setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2 media-publication=1 artifacts=disabled`.
- Desktop/tablet viewports: the spec asserts render + parity at both (order's "desktop/tablet" requirement; phone is covered by the driver's six stable-device projects which render the canonical parity page).

### Criterion 6 (OpenAPI strip-identity + drift gate)

- Strip-identity: after stripping every `x-slaif-*` key, canonical JSON (sorted keys, compact separators) sha256 is `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83` for BOTH base `577509e` and head (recomputed on the final tree, 2026-10-03).
- Paths: 47 head = 47 base, same key set (the order's "45 paths" wording is the 078/8-era adjudication rule; 079/1 added the two media paths at merge — disclosed, unchanged by this diff).
- Scopes: no new scope strings, no removed scope strings (full-document scope inventory diff empty).
- Exact delta: no new extension keys; exactly four changed extension values — `PATCH /api/agent/v1/components/{component_id}`: `x-slaif-component-authority.properties` 63 -> 68, `x-slaif-component-property-scopes` 63 -> 68, `x-slaif-conditional-scopes` 62 -> 67; `POST /api/agent/v1/pages/{page_id}/components`: `x-slaif-component-authority.properties` 63 -> 68. The five new property entries are `Gallery.columns`, `Gallery.items`, `Gallery.title`, `LogoGrid.items`, `LogoGrid.title`, all `component-content-props:write` scalars.
- Drift gate: `uv run --frozen python -m tools.contracts.generate_agent_openapi --check` PASSED (zero-diff regeneration).

### Criterion 7 (R5 docs, durable wording, adversarial sweep)

- Five surfaces handled per R5: four edited with verified merge facts only (PR #92 at `577509e7bc990d85a10af5954bee3c6f7c888a4f` on 2026-09-22; 079/2 in-flight form; actual PR #93 where the order directs the actual number); `CRITICAL.md` verify-only — grep for `079|PR #92|079-a` returns only the historical banner, no current-state claim, unedited.
- In-flight row uses the standard ledger form with "PR pending" (079/1 precedent commit `cda62d7`: the ledger row keeps the standard form even after the PR number is known; the actual number appears in MVP-PROGRESS/README per the order's PR-number instruction).
- Adversarial sweep (`grep '079-a|079/1'` over README, INCREMENTS, MVP-PROGRESS, MVP-CONTRACT-AUDIT, CRITICAL.md minus merged/closed facts; plus all `opened at` lines): zero stale 079/1 in-flight claims; the only `opened at` lines are the 079/2 rows.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` after the docs commit: 499 files, 0 issues.

### Criterion 8 (no R7 violation)

- `uv.lock` / `pnpm-lock.yaml` byte-identical to base (absent from the diff; `uv lock --check` and `pnpm install --frozen-lockfile` PASSED on the final tree).
- No changes under `tools/supply_chain/`, `tests/supply_chain/`, or `.github/workflows/` (verified by the file list: the only `tools/` change is the 1-line smoke expectation in `tools/compose/public_agent_acceptance.py`).
- No new dependency; no new migration file (in-place 060_001 regeneration only); no new endpoint; no new scope strings (Criterion 6); no secrets in diff or report (fixture credentials only, declared fake).

### Criterion 9 (CI: all 20 required checks on the exact report-only head)

- NOT SATISFIED — BLOCKING GAP. At implementation head `0ab21e622e6fc5cac8bb931248332e0272ee1e28` (CI run `37144050390` + CodeQL run `37144050379`), 18 of 20 required checks are SUCCESS and the two Docker-image-build checks (`Compose and edge packaging`, `Supply-chain evidence`) are FAILURE with the same external, pre-existing root cause (Alpine index rotation against the base-carried Dockerfile pin; see Known limitations / blockers). All 18 product/quality gates (Python, Node, Foundation PostgreSQL 14-18, contracts, markdown, mermaid, policy, CodeQL) are green. Per protocol §9, a failure requiring strategy/scope expansion/external resolution is reported truthfully, not repaired beyond safe in-scope work; the status is therefore BLOCKED with this exact gap. Full per-check table below.

## Local verification

All on the final tree (post-docs-commit), 2026-10-03, repo root:

- `uv lock --check`: PASSED
- `uv sync --frozen --all-groups`: PASSED (44 packages checked)
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED (All checks passed)
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED (308 files already formatted)
- `uv run --frozen mypy`: PASSED (Success: no issues found in 287 source files)
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`: PASSED (710 passed, 26 subtests)
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED (235 passed in 2517.38s / 0:41:57; disposable local PostgreSQL + fake credentials)
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED (sdist + wheel)
- `uv run --frozen python -m compileall -q tools tests/repository`: PASSED
- `uv run --frozen python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED (Ran 71 tests, OK)
- `uv run --frozen python tools/check_repository.py`: PASSED (repository policy)
- `uv run --frozen python tools/check_mermaid.py`: PASSED (16 diagrams in 3 files; 505 Markdown files scanned)
- `python tools/generate_component_catalog.py --check`: PASSED (zero-diff)
- `python tools/generate_design_system.py --check`: PASSED (zero-diff)
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`: PASSED (zero-diff)
- Process smokes `uv run --frozen python -m slaif_agent_site.{control_api,editor_api,agent_api,render_api,mcp_adapter,media_service,review_worker,scheduler,media_gc,bootstrap} --check`: all 10 PASSED
- `node --version` / `pnpm --version`: v24.14.1 / 11.22.0
- `pnpm install --frozen-lockfile`: PASSED
- `pnpm lint`: PASSED
- `pnpm format:check`: PASSED
- `pnpm typecheck`: PASSED
- `pnpm test`: PASSED (root workspace tests incl. contract suites + build; re-run on the final tree after the last spec edit)
- `pnpm build`: PASSED
- `pnpm licenses list --json`: PASSED (lockfile byte-identical to base, so the license inventory is unchanged: MIT / Apache-2.0 / BSD / ISC / 0BSD / BlueOak-1.0.0 / CC-BY-4.0 only)
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED (499 files, 0 issues; run after the docs commit)
- Full Compose smoke `sh tools/compose/smoke.sh slaif0075a`: PASSED, rc=0 (final definitive run, log `/tmp/0792a-smoke-4.log`). Exact key lines: `compose-e2e: OK projects=13 setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2 media-publication=1 artifacts=disabled`; `public-agent-acceptance: OK ... components=1 ... restart=verified nginx-outage=verified ...`; `media-e2e: OK edge=nginx upload=validated-private-read=byte-identical finalization=public-read=byte-identical immutable-cache=verified`; `human-editor-envelope: OK ... count=9`; `governance-e2e: OK visible=create-profile-domains-membership-archive negatives=verified devices=6 users=4`; `compose-smoke: OK`
- Clean debug-stack verification (fresh `slaif007dbg2`): `browser-e2e: PASSED project=media-publication contract=media-publication-core-human-agent-preview-finalize-public-hostile` + `browser-e2e: OK`, rc=0 (the media-publication project, run with `--no-deps` after the setup project passed on the same fresh stack)

## GitHub CI / required checks

State observed for implementation head
`0ab21e622e6fc5cac8bb931248332e0272ee1e28` (CI run `37144050390` started
2026-10-03T18:24:09Z + CodeQL run `37144050379`; observed 2026-10-03):

| Required check | State (head 0ab21e6) |
|---|---|
| Compose and edge packaging | FAILURE (CI 37144050390, job 111264285669, 1m21s — apk cannot resolve `libcrypto3=3.5.8-r0` in the `target web` build; external Alpine index rotation vs the base-carried Dockerfile pin; exact analysis in Known limitations) |
| Dependency review | SUCCESS |
| Foundation PostgreSQL 14 | SUCCESS (CI 37144050390, 7m34s) |
| Foundation PostgreSQL 15 | SUCCESS (CI 37144050390, 7m28s) |
| Foundation PostgreSQL 16 | SUCCESS (CI 37144050390, 11m44s) |
| Foundation PostgreSQL 17 | SUCCESS (CI 37144050390, 7m0s) |
| Foundation PostgreSQL 18 | SUCCESS (CI 37144050390, 7m18s) |
| Markdown | SUCCESS |
| Mermaid | SUCCESS |
| Node contracts | SUCCESS (CI 37144050390, 2m0s) |
| Python 3.12 quality and package | SUCCESS |
| Python 3.13 quality and package | SUCCESS |
| Python 3.14 quality and package | SUCCESS |
| Repository policy | SUCCESS |
| Supply-chain evidence | FAILURE (CI 37144050390, job 111264285819, 3m3s — same apk error in the backend image build, `backend first build failed after 3 attempts`; failure-diagnostics artifact 11281991278) |
| Analyze (actions) | SUCCESS (CodeQL 37144050379) |
| Analyze (javascript-typescript) | SUCCESS (CodeQL 37144050379) |
| Analyze (python) | SUCCESS (CodeQL 37144050379, 1m43s) |
| CodeQL | SUCCESS (CodeQL 37144050379) |
| Detect supported languages | SUCCESS (CodeQL 37144050379) |

- All required green at drafting: NO — 18 SUCCESS, 2 FAILURE (same
  external root cause, see Known limitations). The run completed before
  drafting, so no check is PENDING; strategy independently verifies the
  states (including any fresh checks triggered by the report-only SELF
  commit).
- No CI re-run was invoked: the single allowed unmodified re-run is reserved
  for the documented 079/1 `dragUntil` Puck-drag flake class with its exact
  signature (order §2); the observed failure is not that class.

## Local setup / dependencies

- No new packages/dependencies (lockfiles byte-identical to base).
- Existing toolchain: uv 0.12.5, Node v24.14.1, pnpm 11.22.0, Docker Compose, local disposable PostgreSQL 16 (scratch cluster on 127.0.0.1:5432) for integration tests, Playwright 1.62.1 (Chromium/Firefox/WebKit), `markdownlint-cli2@0.23.2` via npx (temporary, no production dependency), Mermaid CLI 11.16.0 via the check tool (temporary, no production dependency).
- Guest-sudo setup used for: nothing new this round (toolchain and disposable PostgreSQL already provisioned by earlier rounds).
- Disposable compose stacks used and torn down: `slaif007dbg2` (clean debug verification) and `slaif0075a` (full smoke x2; the smoke script tears the stack down at completion). No production systems, data, or credentials touched; all credentials fake fixtures.

## Documentation

- `oap/INCREMENTS.md`: 079/1 row closed with verified PR #92 merge fact; 079/2 row added in the standard in-flight form (ledger keeps "PR pending" per the 079/1 precedent `cda62d7`); Next row advanced to the remaining 079 scope (079/3 closes 32/32; numeric 078 remains PARTIAL until 079/3 lands).
- `oap/MVP-PROGRESS.md`: active-sequence paragraph + 078/079 status rows updated with verified merge facts and the 079/2 open row (actual PR #93); OAP/GitHub-authoritative sentences preserved.
- `README.md`: Objective-078/4 capability row — 079/1 clause replaced with the verified merge fact + 079/2 open clause (actual PR #93); GitHub-authoritative sentence preserved.
- `oap/MVP-CONTRACT-AUDIT.md`: media row (42) evidence cell appended with the verified 079/1 merge facts (catalog 29 with real Image; public/preview media core E2E-proven); Next cell set to "079/2: Gallery + LogoGrid (in flight); 079/3: DocumentList + document serving; 083: ...".
- `CRITICAL.md`: verified only — historical banner only, no current-state 079 claim, unedited (R5(e) verify-only branch).

## Safety and scope confirmations

- Unrelated files changed: NO — every changed file maps to R1-R7 or to the R6-mandated mechanical pin class (disclosed per file in Changes made 6).
- Production secrets accessed: NO; production systems accessed: NO (disposable compose stacks + local scratch PostgreSQL only; all credentials fake fixtures; no secrets in diff or report).
- Required tests skipped/not run: NO — every locally nameable R6 evidence command ran and passed (exact outputs above). The sole unsatisfied named evidence is CI Criterion 9, which is not locally nameable (required GitHub gate) and is blocked by the external packaging fact documented below; it is labeled FAILURE/PENDING exactly as observed, never as pass.
- Scope deviation: NO beyond the predeclared budget (overages justified in the cumulative size table; the 1-line smoke expectation is the order §10 "smoke expectation only if changed" item).
- Extra objective PR: NO; coding-agent merge: NO.
- Activated order/`oap/active` edited: NO (committed byte-identical: order sha256 `d2ee17f949906e939edd18316366d1dd35e6d2b41dbf1080beea8fe5b81224bf`, active `079-2-a\n`).
- Report commit changes only this report: yes.

## Cumulative base->head size (2026-09-14 review-unit governance Section 2)
Base `577509e7bc990d85a10af5954bee3c6f7c888a4f` -> implementation head
`0ab21e622e6fc5cac8bb931248332e0272ee1e28`:

| Category | Files | +lines | -lines |
|---|---|---|---|
| Production/config | 10 | 534 | 54 |
| Migrations | 0 | 0 | 0 |
| Tests/evidence | 11 | 1283 | 7 |
| Generated artifacts | 5 | 354 | 4 |
| Docs | 4 | 8 | 6 |
| OAP transcript | 2 (order + active; report via SELF) | 349 | 1 |

Predeclared budget (order Section 10) check: production/config 10 predeclared
— actual 10 (the in-place `060_001` regeneration is one of the ten);
migrations 0 — actual 0; tests/evidence 5 predeclared — actual 11
(justification: the 3 predeclared core files — `test_component_facets.py`,
`renderer-behavior.test.ts`, `media-publication.spec.ts` — plus the R6
"projection descriptor resolution" unit suite `test_render_projection_media.py`,
plus the six R6-mandated mechanical pin files (078/7-078/8 class, each a
1-2-line count/scope bump, disclosed per file), plus the order §10 "smoke
expectation only if changed" item (1 line)); generated 4 predeclared — actual
5 (justification: `design-system-v1.json` x2 regeneration is the
deterministic byproduct of the catalog change; the in-place `060_001`
baked-catalog line pair is counted under production/config above per the
order's own production line, so generated standalone is 5 not 6); docs 5
predeclared — actual 4 (CRITICAL.md verified no-claim, unedited per R5(e));
substantive implementation lines 1.2k predeclared — actual 534
(production/config +534/-54 + migrations 0; generated +354 and tests/evidence
+1283 excluded from substantive scale per the 079/1 report formula). The
~20-30 file / several-thousand-line trigger is NOT crossed (32 files,
+2528/-72 cumulative, dominated by the order-mandated E2E spec extension,
unit suites, and regenerated artifacts).

## Known limitations / blockers

- BLOCKING (Criterion 9): both Docker-image-build required checks —
  `Compose and edge packaging` and `Supply-chain evidence` — fail at head
  `0ab21e6` because the Alpine v3.23 package index no longer offers the
  exact-version pin `libcrypto3=3.5.8-r0` / `libssl3=3.5.8-r0` that
  `apps/web/Dockerfile` (lines 7, 36), `infra/nginx/Dockerfile` (lines 16,
  17), and `infra/postgres/Dockerfile` (lines 20, 22 + exact-version
  assertion lines 23, 25) carry — a pin introduced by merged commit
  `b946d26` and present at base `577509e`, untouched by this diff. Exact
  evidence: (1) CI job log (run 37144050390, job 111264285669): `apk` error
  `libcrypto3-3.5.6-r0: breaks: world[libcrypto3=3.5.8-r0]` during
  `target web` builder/runtime build; (1b) CI job log (run 37144050390,
  job 111264285819): the identical apk resolution error in the backend
  image build steps, `backend first build failed after 3 attempts`,
  failure-diagnostics artifact 11281991278; (2) canonical index check
  (2026-10-03): `https://dl-cdn.alpinelinux.org/alpine/v3.23/main/x86_64/
  APKINDEX.tar.gz` lists exactly one `libcrypto3` entry, `V:3.5.9-r0` —
  `3.5.8-r0` was rotated out of the index; (3) direct reproduction on the
  pinned base image: `docker run --rm node:24.14.1-alpine3.23@sha256:8510330d3eb72c804231a834b1a8ebb55cb3796c3e4431297a24d246b8add4d5 sh -c "apk --timeout 30 add --no-cache 'libcrypto3=3.5.8-r0' 'libssl3=3.5.8-r0'"` fails with the identical resolution error; (4) main is equally affected (same Dockerfiles at base `577509e`); (5) the local full smoke passed only because the local Docker image cache predates the index rotation. This is a supply-chain build-gate decision (the pin is part of the earlier reproducible supply-chain build-gate objective; the postgres Dockerfile asserts the exact installed version), not a product defect and not this order's scope (order §4 "Nothing else"; §5 non-goals); per protocol §10 the executor does not silently decide it.
  Minimal candidate fix for strategy (NOT applied): bump the pin
  `3.5.8-r0` -> `3.5.9-r0` in the three Dockerfiles (plus the two
  `infra/postgres/Dockerfile` exact-version assertions), then rebuild all
  images and re-run the full Compose smoke + CI. Alternatively strategy may
  publish a small packaging order for it.
- Two deterministic E2E spec defects found by the first full-driver run that
  reached the new 079/2 section (both fixed spec-only, no product-code
  change; documented here per the 079/1 incident-record precedent):
  (1) bare 422 `COMPONENT_ORDER_INVALID` on the first agent component create
  on the parity home page — the 079/1 base-move carried explicit
  `order_key` 20/21 over a gap (editor Puck explicit-position semantics
  allow gaps; the agent path enforces the pre-existing contiguous
  `0..n-1` canonical invariant in
  `slaif_agent_component_tree_validate`). Fixed by an order-preserving
  renumber UPDATE of the top-level group inside the spec's base-move
  transaction, with an explanatory comment. The invariant is pre-existing
  shipped behavior; the fixture was invalid — NOT "fixed" in product DB
  code. (2) Six LogoGrid hostile single-item cases returned
  `logogrid.items-out-of-range` instead of the per-item key because
  `validate_media_reference_items` checks list bounds before per-item
  (LogoGrid min=2). Fixed by sending 2 items (one valid + the hostile
  item) in those six cases so the per-item check fires; all three agent
  variants and all three editor variants then return the exact
  `logogrid.item-*` keys. Both fixes are test-only; the deterministic
  clean debug run and the definitive full smoke are green.
- The public agent acceptance proof's component-catalog count pin (29 -> 31)
  surfaced as a smoke failure only after the E2E fixes unblocked the run
  (smoke.sh stops at the first failing stage). It is the same mechanical
  ripple class as the 078/7/078/8 pin bumps and is covered by the order
  §10 "smoke expectation only if changed" budget line.
- Public-byte retention/GC semantics for the public namespace remain
  083/089-bound (out of scope by design); `media_gc` unchanged.

## Recommended strategic follow-up

- Decide the Alpine pin question for `Compose and edge packaging`
  (candidate: `3.5.8-r0` -> `3.5.9-r0` in the three Dockerfiles + the two
  postgres exact-version assertions, with a full local smoke re-run and CI
  re-check; or a dedicated small packaging order). Until then, every PR on
  this repository — including `main` — will show that one required check red
  for the external reason documented above; this PR's own diff is otherwise
  fully delivered, verified locally (all R1-R7 named evidence), and pushed.
- No further executor work is possible this round without a strategic
  decision; per the flake policy no CI re-run was invoked.
