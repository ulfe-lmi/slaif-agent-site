# OAP Coding-Agent Report — 078-5-a

## Work order

- Identifier: `078-5-a` (increment-qualified; semantic increment 5 of numeric
  Objective 078, first qualified round under the 2026-09-14 amendment)
- Work-order file: `oap/orders/078-5-a-global-regions-header-footer.md`
- Numeric objective: 078 (increment 5)
- PR mode: CREATED_NEW_PR

## Status
BLOCKED (implementation complete and locally verified; one strategic
decision required — see Blocker B-1)

## Executive summary
Implemented the site-global region and header/footer management data plane
exactly per order 078-5-a binding decisions 1–7, following the merged
page-style/theme plane patterns:

- Exactly one reversible migration `067_001_global_region_data_plane.py`:
  COW `content.site_global_region_base` + `content.site_global_region_changes`
  (foundation overlay mechanism, view merge with INSTEAD OF write triggers),
  closed-enum variant and bounded-content DB validators (fail-closed),
  ancestor-chain and page-target resolution helpers, the
  `global-region:read` permission seed (level 0, site-assignable, granted to
  all seven human roles), and the semantic audit-shape extension that makes
  `GLOBAL_REGION_UPDATED` first-class in `audit.agent_mutation`.
- Product-owned `region_models.py` (models + service) and
  `composition-schema/src/region-schema.ts` (TypeScript mirror of the bounded
  shapes) with unit tests on both sides.
- Agent API: exactly `GET /api/agent/v1/global-regions` and
  `PATCH /api/agent/v1/global-regions/{id}` with full idempotency/audit/
  quota/row-version semantics; write scopes deferred to the trusted SQL
  barrier and charged only on a real state change.
- Editor (Design) mirror over the human session with identical server
  revalidation, Puck Design surface (variant select + entry editors), and
  admin API client support.
- Render projection gains a site-level `regions` section resolved per render
  context with the same mechanism as theme; the trusted renderer renders the
  Header/Footer shells, derived Breadcrumbs, and the server-resolved,
  fail-closed Language Switcher in one shared component tree across public,
  preview, and review contexts. Region hrefs are absolute site-rooted in
  canonical renders and relative (site-root hop count) in preview renders so
  the private workspace identifier never enters preview HTML (privacy
  contract); unresolvable language-switch targets render as inert tags,
  never broken links.
- Lazy, deterministic, idempotent per-site bootstrap defaults (institutional
  header with one site-key nav entry; single-column footer with no links and
  empty note); regions are virtual until first write.
- OpenAPI regenerated with zero drift; scope catalogs (TS + Python) and all
  seed/checks pinning the scope set updated for `global-region:read`.
- Durable docs (README, INCREMENTS, MVP-PROGRESS, MVP-CONTRACT-AUDIT) and the
  activated order + `oap/active` committed byte-for-byte unchanged.

One recorded implementation note (not a deviation): `page` targets are
server-validated for same-site existence; `internal` targets are
format-validated (absolute route, reserved-prefix and traversal rejection)
without existence resolution, because the order pins server validation only
for `page` targets and the default header's internal `/` target must remain
valid before any page write. See Known limitations.

**Blocker B-1 (status BLOCKED):** the ordered header-nav contract
structurally breaks two frozen structure pins
(`"navigation": 0` → renders 2) in `tools/compose/public_agent_acceptance.py`
(lines 1335, 2067), a file the order's allowed set excludes ("No source
tools"). All 11 browser E2E projects (local and CI) and 19/20 required
GitHub checks pass; the sole failing required check is the Compose
`public-agent-acceptance` stage. Minimal fix: the two listed lines
(`0` → `2`); requested via amendment round (078-5-b, amend same
branch/PR) or explicit strategic authorization.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #85 — <https://github.com/ulfe-lmi/slaif-agent-site/pull/85> (state OPEN)
- Base branch: `main`; head branch:
  `oap/078-5-a-global-regions-header-footer`
- Starting remote SHA (base): `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`
- Implementation head SHA: `64dea09f49c39acdcd65a84ce9f4968b6268b304`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commits pushed before report: exactly one — `64dea09f49c39acdcd65a84ce9f4968b6268b304` (`078-5-a: site-global regions and header/footer management`, 48 files, +5146/−74)
- Report parent = implementation SHA: yes
- New PR this turn: yes; amended existing: no; merge performed: NO

## Changes made
### Data plane (backend)

- `db/alembic/versions/067_001_global_region_data_plane.py` (new, reversible):
  base + overlay tables with exact column sets, variant CHECK per
  `slaif_region_variant_valid` (header `{institutional, minimal}`; footer
  `{multi-column, single-column}`), content CHECK per
  `slaif_region_content_valid`, entry/target validator functions,
  `slaif_region_project` (canonical/virtual), `slaif_region_list`,
  `slaif_agent_region_list` (capability-gated read), `slaif_region_apply`
  (COW-context-required, advisory-locked, deferred-scope, row-version,
  no-effect early-return, quota and audit), `slaif_page_ancestor_chain`,
  `slaif_region_page_targets_valid` (site-confined existence for `page`
  targets), permission + role-permission seeds, audit semantic-shape
  extension; downgrade removes everything in reverse order with
  data-presence guards.
- `content_model/region_models.py` (new): `GlobalRegionRecord`,
  `UpdateGlobalRegionRequest`, `AgentUpdateGlobalRegionRequest`, record
  serializer returning the exact stored content document.
- `content_model/service.py`: `list_global_regions`, `get_global_region`,
  `update_global_region` (editor, optional row version),
  `update_global_region_for_site` (agent, required row version) with COW
  session/operation binding and reason mapping.
- `bootstrap/service.py`: region defaults wired into the lazy bootstrap path
  (no migration-time seeding of existing sites).
- `db/privileges.py`: content role grants for the new tables/functions.
- `control_api/route_policy.py`: declarative route-policy entries for the
  two Agent routes (read-gated; SQL barrier remains authoritative).
- `human_authorization/catalog.py`: `global-region:read` added to
  `READ_SCOPES` (inherited by all four presets).
- `agent_state/reads.py` + `agent_state/mutations.py`: read and mutation
  plumbing for the region surface (quota action, audit action
  `GLOBAL_REGION_UPDATED`, idempotency identity).
- `agent_api/agent_http.py`: the two §24.6 routes exactly.
- `editor_api/global_region_http.py` (new) + `editor_api/app.py`: Editor
  mirror (list/get/patch) with `global-region:read` / `global-region:write`
  HTTP gates and the deferred `header-footer:write` variant-change check.

### Scope catalog (Node)

- `packages/scope-catalog/src/index.ts`: `global-region:read` added to
  `AGENT_READ_SCOPES` (14 → 15); test pin updated to length 15 and exact
  order.

### Composition schema (Node)

- `packages/composition-schema/src/region-schema.ts` (new, product-owned,
  not generator output): bounded header/footer content + target types with
  the exact bounds; exported from `src/index.ts`.
- `packages/composition-schema/tests/region-schema.test.ts` (new).

### Render (Node)

- `render_api/projection.py`: `regions`, `ancestors`, `default_locale`
  sections resolved per render context with the same trusted path as theme
  (canonical public read; preview repeatable-read COW workspace session;
  immutable review snapshot), including page-target href resolution and
  fail-closed missing-page behavior. Language switcher targets are resolved
  server-side per locale: the current page is re-rooted under the target
  locale tag per the effective-route contract (default-locale targets carry
  no locale prefix), the candidate route is resolved case-insensitively on
  lowercased input mirroring `normalize_request_path` (tagged routes keep
  their stored tag case, e.g. `sl-SI`), and each enabled locale carries
  `switcher_href` (the resolved page's `effective_route`) or stays
  `null` — fail-closed, so the renderer can never emit a broken switch
  link.
- `apps/web/src/renderer/components.tsx`: Header/Footer region shells
  (variant classes), brand link, site nav, language switcher nav (current
  locale `span[aria-current]`, resolvable targets as links, unresolvable
  targets as inert `aria-disabled` spans — server decides), derived
  Breadcrumbs (`nav[aria-label="Breadcrumb"]`, rendered only when the page
  has ancestors), note paragraph. `regionHref` maps a target route to the
  correct href per context: external targets as-is; canonical (non-preview)
  absolute site-rooted; preview relative — depth 0 (site root) `siteKey` /
  `siteKey/target`, depth k>0 `"../".repeat(k-1)` + target (page URLs never
  carry a trailing slash, so the browser's relative base directory already
  excludes the page's own last segment; one fewer `../` hop than the
  site-path depth). The workspace identifier therefore never appears in
  preview page HTML.
- `apps/web/src/sites/render.ts`, `shell.tsx`,
  `preview/[workspaceId]/[[...sitePath]]/route.tsx`,
  `preview-page.tsx`: projection pass-through for the new sections.
- `apps/web/public/renderer-v1.css`: region shell, variant, breadcrumb, and
  language-switcher styles (responsive + reduced-motion safe).
- `apps/web/tests/renderer-behavior.test.ts`: region rendering assertions.

### Admin (Puck/Design)

- `apps/web/src/admin/composition-editor.tsx`: Design surface region panel
  (variant select + nav/links entry editors + note), preview-scoped save
  flow.
- `apps/web/src/admin/api.ts`: region list/patch client.

### Contracts

- `contracts/openapi/agent-v1.json`: regenerated; grows exactly the two §24.6
  routes (schemas + parameters), zero drift (`tools/contracts` `--check` OK).

### Tests

- `services/backend/tests/unit/test_region_models.py` (new, 30 tests):
  model/serializer/bound semantics.
- `services/backend/tests/integration/test_agent_global_region.py`
  (new, 7 tests on real disposable PostgreSQL): hostile matrix (15 × 422),
  cross-site 404, stale row version 409, missing row version 422,
  idempotent replay (bounded, audited once), L3 delegation denial via the
  real control-API workspace/capability path, migration downgrade guards
  (`REGION_MIGRATION_PENDING_COW`, `REGION_MIGRATION_DATA_PRESENT`,
  `REGION_MIGRATION_AUDIT_PRESENT`), deterministic two-distinct-waiters
  concurrency (advisory + transactionid lock-waiter overlap proven via
  `pg_locks`; exactly one 200 and one 409).
- `services/backend/tests/integration/test_render_projection_integration.py`:
  new regression test `test_canonical_language_switcher_resolves_mixed_case_locale`
  (real disposable PostgreSQL): from the default-locale page, the mixed-case
  `sl-SI` switcher target resolves to the stored-case `effective_route`
  (`/sl-SI/guide`) while a mirror-less locale (`de-DE`) stays inert; from
  the tagged mirror page, the default-locale target resolves without any
  locale prefix (`/guide`).
- Updated pinned fixtures in `test_agent_mutations.py`,
  `test_agent_page_style.py`, `test_control_database_integration.py`,
  `test_database_bootstrap.py`, `test_editable_domain_proof.py`,
  `test_human_agent_session_control.py`, `test_control_database.py`,
  `test_foundation_contract.py`, `test_health_apps.py`, `test_route_policy.py`
  for the new table/scope/route surface (byte-exact pins only; no assertion
  weakened).
- `tests/e2e/preview.spec.ts`: two new Playwright tests (public canonical
  defaults + fail-closed inert switcher + editor preview-scoped save/restore
  with relative preview hrefs; agent patch + page-target render + relative
  nav click-through + breadcrumb click-through + language-switcher
  round-trip in both directions with resolvable/inert cases + workspace
  isolation + reload persistence).

### Docs

- `README.md`, `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`,
  `oap/MVP-CONTRACT-AUDIT.md`: durable wording per 078-z rules (GitHub
  authoritative for live state; no merge-time-false phrasing).

## Files changed
New files (8):

- `oap/orders/078-5-a-global-regions-header-footer.md` (activated order,
  committed byte-for-byte unchanged, 252 lines)
- `services/backend/src/slaif_agent_site/db/alembic/versions/067_001_global_region_data_plane.py` (738)
- `services/backend/src/slaif_agent_site/content_model/region_models.py` (294)
- `services/backend/src/slaif_agent_site/editor_api/global_region_http.py` (117)
- `packages/composition-schema/src/region-schema.ts` (206)
- `packages/composition-schema/tests/region-schema.test.ts` (108)
- `services/backend/tests/integration/test_agent_global_region.py` (809)
- `services/backend/tests/unit/test_region_models.py` (223)

Modified files (40, base→head insertions/deletions):

- `README.md` +8/−6
- `apps/web/app/preview/[workspaceId]/[[...sitePath]]/route.tsx` +6/−2
- `apps/web/public/renderer-v1.css` +190/−0
- `apps/web/src/admin/api.ts` +32/−0
- `apps/web/src/admin/composition-editor.tsx` +254/−1
- `apps/web/src/renderer/components.tsx` +202/−13
- `apps/web/src/sites/preview-page.tsx` +6/−1
- `apps/web/src/sites/render.ts` +25/−0
- `apps/web/src/sites/shell.tsx` +3/−2
- `apps/web/tests/renderer-behavior.test.ts` +110/−0
- `contracts/openapi/agent-v1.json` +477/−0 (regenerated)
- `oap/INCREMENTS.md` +4/−3
- `oap/MVP-CONTRACT-AUDIT.md` +5/−5
- `oap/MVP-PROGRESS.md` +3/−2
- `oap/active` +1/−1 (activated round pointer, committed unchanged content)
- `packages/composition-schema/src/index.ts` +1/−0
- `packages/scope-catalog/src/index.ts` +1/−0
- `packages/scope-catalog/tests/index.test.ts` +2/−1
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py` +46/−0
- `services/backend/src/slaif_agent_site/agent_state/mutations.py` +37/−0
- `services/backend/src/slaif_agent_site/agent_state/reads.py` +11/−0
- `services/backend/src/slaif_agent_site/bootstrap/service.py` +1/−0
- `services/backend/src/slaif_agent_site/content_model/service.py` +43/−0
- `services/backend/src/slaif_agent_site/control_api/route_policy.py` +40/−0
- `services/backend/src/slaif_agent_site/db/privileges.py` +10/−0
- `services/backend/src/slaif_agent_site/editor_api/app.py` +2/−0
- `services/backend/src/slaif_agent_site/human_authorization/catalog.py` +2/−2
- `services/backend/src/slaif_agent_site/render_api/projection.py` +270/−0
- `services/backend/tests/integration/test_agent_mutations.py` +11/−11
- `services/backend/tests/integration/test_agent_page_style.py` +4/−4
- `services/backend/tests/integration/test_control_database_integration.py` +3/−3
- `services/backend/tests/integration/test_database_bootstrap.py` +6/−6
- `services/backend/tests/integration/test_editable_domain_proof.py` +1/−1
- `services/backend/tests/integration/test_human_agent_session_control.py` +1/−1
- `services/backend/tests/integration/test_render_projection_integration.py` +95/−0
- `services/backend/tests/unit/test_control_database.py` +5/−5
- `services/backend/tests/unit/test_foundation_contract.py` +6/−1
- `services/backend/tests/unit/test_health_apps.py` +4/−0
- `services/backend/tests/unit/test_route_policy.py` +3/−3
- `tests/e2e/preview.spec.ts` +468/−0

Cumulative base→head size grouped per review-unit governance §2
(`git diff --stat d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba..HEAD`,
intent-to-add working-tree diff at drafting):

- OAP transcript (order + active): 252 + 1/1
- Data plane (migration, region models, service, bootstrap, privileges,
  route_policy, Python catalog, agent_state reads/mutations, agent_http):
  738 + 294 + 43 + 1 + 10 + 40 + 2/2 + 37 + 11 + 46 = 1222
- Render projection (Python): 270
- Scope catalog (TS + test): 1 + 2/1
- Composition schema (module + export + test): 206 + 1 + 108
- Web renderer/shell/styles/tests: 190 + 202/13 + 25 + 3/2 + 6/1 + 6/2 + 110
- Admin/Puck (editor + api client): 254/1 + 32
- Generated contracts (OpenAPI): 477
- Tests (backend unit new + pin updates, integration new + pin updates,
  Playwright): 223 + 809 + 468 + 36 pin-change lines
- Docs (README + 3 OAP ledgers): 8/6 + 4/3 + 5/5 + 3/2

Total: 40 modified + 8 new files; `git diff --numstat` totals 5146
insertions + 74 deletions across the 48 files (working-tree diff at
drafting; CI `--stat` on the committed implementation SHA is the exact
figure of record).

## Acceptance-criteria evidence
### Criterion 1 (public canonical render, real private browser)
Compose smoke project `preview` (real private Chromium through public
NGINX), test `global-regions-render-canonical-defaults-and-editor-save-is-preview-scoped`:
public canonical `/s/parity/` (status 200) rendered the institutional header
(class `renderer-region-header--institutional`), brand link
`a.renderer-region-brand` text `parity` href `/s/parity`, exactly one site
nav link (`header nav[aria-label="Site"] a`) resolving to the real site root,
language switcher `header nav[aria-label="Language"]` with
`span[aria-current="true"]` = `en` and the enabled `sl-SI` locale rendered
fail-closed as an inert tag (`.renderer-region-language-inert`, zero
`header nav[aria-label="Language"] a` links — the fixture's only sl-SI page
is the tagged route `/sl-SI/parity`, so no page exists at the tagged root
`/sl-SI` and the switcher must not emit a broken link), single-column
footer (class
`renderer-region-footer--single-column`, zero `footer nav[aria-label="Footer"]`
links per the empty default, zero `.renderer-region-note`), and no
`nav[aria-label="Breadcrumb"]` on the parentless root page. Console/pageerror
observation clean. Breadcrumbs specifically: the same shared component tree
renders the derived ancestor chain in the workspace preview context (criterion
2/4 evidence: one ancestor link + current page `li[aria-current="page"]`
non-linked) — a public-canonical ancestor chain additionally requires
promoted (canonical) pages, which are outside this increment's non-goals
(no review/promotion/publication work); the mechanism is the identical
projection pass documented under Render-context mechanism.

- Result: PASSED (canonical header/footer/language-switcher directly in
  public browser; breadcrumb chain proven in preview through the same tree;
  canonical-chain rendering gated on promotion scope outside this increment)

### Criterion 2 (preview overlay + review-snapshot context)

- Preview overlay: Compose `preview` project, same test as criterion 1:
  after the Editor save (variant `minimal`, 2 nav entries, footer note),
  `/preview/<parity-workspace>/s/parity/` rendered class
  `renderer-region-header--minimal`, exactly 2 nav links (`Parity Home` →
  `/preview/.../s/parity/`, `Docs` → `https://docs.example.org/`), footer
  note `E2E footer note` — differing from canonical, which re-rendered
  unchanged (institutional, 1 nav link, no note) in the same browser run.
- Editor preview hrefs (same test): the saved minimal header's nav links
  render as relative preview hrefs — `Parity Home` (internal `/`) →
  `href="parity"`, `Docs` (external) → the validated absolute URL — and the
  page HTML contains no private workspace identifier (privacy contract;
  independently asserted by the pre-existing
  `authenticated-preview-renders-overlay-and-keeps-canonical-unchanged`
  no-UUID test).
- Agent preview: test `global-regions-agent-patch-renders-in-the-same-authorized-workspace`:
  agent PATCH (variant `minimal`, then page target) rendered in
  `/preview/<agent-workspace>/s/parity/` with the page-target nav href
  relative `parity/region-parent/region-child` (site-root hop from the
  preview root); the test clicks the link and asserts the resolved URL
  `${previewBase}/region-parent/region-child`. On the child page the
  derived breadcrumb renders one ancestor link with relative href
  `../region-parent`; clicking it resolves to
  `${previewBase}/region-parent` (where no breadcrumb nav renders, the
  parent having no ancestors). The language switcher then proves the
  server-resolved round-trip in both directions: from the en parent page
  (after creating the sl-SI mirror page) the switcher renders
  `a[href="sl-SI/region-parent"]` (click → `${previewBase}/sl-SI/region-parent`),
  and from the sl-SI page the back link renders
  `a[href="../region-parent"]` (click → `${previewBase}/region-parent`),
  with the current locale always `span[aria-current="true"]`. The second
  (default) workspace preview rendered the unchanged institutional default;
  reload persisted the overlay.
- Review-snapshot context: the projection resolves regions from the
  reviewer-frozen immutable snapshot's base rows (frozen at promotion) via
  the same `regions` section — mechanism named under Render-context
  mechanism; no snapshot promotion is exercised in this increment (non-goal).
- Result: PASSED (preview overlay + workspace isolation in real browser;
  snapshot context mechanism implemented and named; snapshot rendering
  itself not browser-executed this increment)

### Criterion 3 (human Editor Design surface)
Compose `preview` project, test `global-regions-render-canonical-defaults-and-editor-save-is-preview-scoped`:
logged-in human (Compose.Admin fixture credential) saved via
`PATCH /api/editor/v1/sites/{site}/global-regions/{id}` with CSRF +
Idempotency headers (header: variant `minimal` + 2 nav entries → 200,
row_version 2; footer: note update → 200); the change appeared only in the
preview workspace (criterion 2) and canonical stayed unchanged. The Puck
Design surface panel (variant select + entry editors + note) ships in
`composition-editor.tsx` with the admin API client; server policy (CSRF,
session, `global-region:write`, deferred `header-footer:write` on variant
change) is identical to the Agent path and proven by the integration suite
(editor mirror revalidation is the same service call).

- Result: PASSED (browser save→preview reflection + canonical isolation
  evidenced; Puck panel present and server-gated, Puck-UI save itself is the
  exact-workspace-Puck non-goal boundary — the Design surface writes through
  the Editor API as implemented)

### Criterion 4 (Agent API surface + hostile negatives)

- Integration (`test_agent_global_region.py`, real disposable PostgreSQL,
  L4 capability via the real control-API workspace+capability path):
  - `GET /global-regions` returns the region list (header+footer records,
    row_version 1, virtual defaults).
  - L4 `PATCH` succeeds (200, row_version 2) and idempotent replay returns
    the identical bounded payload (criterion 7).
  - Hostile matrix, all 422 (15 cases): unknown variant; empty `nav`;
    13-entry `nav` (over bound 12); `javascript:` external target;
    non-http(s) external; over-length label/note; over-bound footer links;
    unknown content keys; malformed targets (extra keys, non-UUID page
    value, reserved-prefix internal `/api/x`, traversal `//`/`..`); over-
    quota content; missing row version on Agent PATCH.
  - Cross-site capability: 404 (P0002) on the other site's region id;
    cross-site `page` target rejected 422 (site confinement).
  - Stale `expected_row_version`: 409.
  - L3 delegation denial: real control-API L3 workspace → capability lacks
    `global-region:write`/`header-footer:write` (038 filter) → Agent PATCH
    403 (P0007); L3 GET allowed via `global-region:read`.
- Compose `preview` project (public NGINX, real browser run): 5 hostile
  Agent PATCHes (bogus variant; empty nav; 13-entry nav; `javascript:`
  target; missing row version) all 422 with state unchanged (row_version
  1), then successful minimal PATCH 200 → row_version 2 and rendered in the
  bound workspace preview.
- Result: PASSED

### Criterion 5 (migration up/down, restart persistence, lazy bootstrap)

- Up: migration `067_001` applied by the integration bootstrap fixture and
  by the Compose stack bootstrap (real PostgreSQL) in both local runs.
- Down: integration downgrade test — with COW enabled, (a) after an agent
  footer write (audit row + overlay row) the downgrade is refused with
  `REGION_MIGRATION_PENDING_COW` and rolls back; (b) after the owner removes
  the overlay row and inserts a canonical base row, the downgrade is refused
  with `REGION_MIGRATION_DATA_PRESENT`; (c) after the base row is removed,
  the downgrade is refused with `REGION_MIGRATION_AUDIT_PRESENT`; with all
  region data gone the downgrade removes tables/functions/seeds and returns
  to the pre-067 state (re-run-able; verified by the subsequent upgrade in
  the same suite).
- Restart persistence: Compose `public_agent_restart` stage (process
  restart) plus the E2E reload-persistence assertion (overlay state survives
  a page reload; canonical rows persist across the full multi-project run).
- Lazy bootstrap idempotency: integration + unit — repeated reads create no
  base rows (virtual defaults), the first write materializes exactly one
  base row, repeated no-effect replays create no further rows; Compose E2E
  proves the virtual-defaults render before any write (criterion 1).
- Result: PASSED

### Criterion 6 (two-distinct-waiters concurrency)
Integration two-distinct-waiters test (deterministic): two Agent PATCH
tasks on the same region with a real lock handoff — waiter-2 blocks on the
capability quota row lock held by waiter-1's open transaction while waiter-1
holds the workspace/site `global-region` advisory lock; overlap proven via
`pg_locks` (advisory waiter on the exact key JOIN a `locktype='transactionid'`
waiter of a different pid). After waiter-1 commits: exactly one 200 (winner
row_version 2) and one 409 (row-version conflict); exactly one audit row.
Advisory key split verified empirically (`objsubid=1`, `classid` =
`(key>>32)&4294967295`, `objid` = `key&4294967295`).

- Result: PASSED

### Criterion 7 (semantic audit, bounded idempotency-identical payloads)
Integration idempotent-replay test: identical Agent PATCH (same
idempotency key, same body) replays return the identical bounded response
payload; `audit.agent_mutation` gains exactly one
`GLOBAL_REGION_UPDATED` row with bounded, key-identical payload fields
(action, workspace/site/region identity, row_version transition,
idempotency key); the semantic-shape constraint (extended in 067) accepts
region rows and rejects malformed ones (constraint re-added after the
upgrade, pinned by the suite).

- Result: PASSED

### Criterion 8 (diff only allowed file set; one migration; no
dependency/lockfile/workflow/ruleset/catalog/theme-schema change)

- `git diff --name-status d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba..HEAD`
  lists exactly the 40 modified + 8 new files enumerated under Files
  changed; every path is inside the order's bounded allowed file set
  (migration dir, content_model, agent_api, editor_api,
  render_api/projection.py, scope catalogs ×2 + pinning test,
  composition-schema module, renderer components/render/shell/styles,
  admin editor + client, services/backend/tests (unit + API + projection),
  Playwright E2E, README + 3 OAP ledgers, order + active).
- Exactly one new migration (`067_001`); no other file under
  `db/alembic/versions/` touched.
- `uv.lock`, `pnpm-lock.yaml`, `.github/` workflows, tooling rulesets, the
  component catalog, and `theme-schema/v1` are byte-identical to the base
  (verified by diff; OpenAPI growth is exactly the two §24.6 routes).
- Result: PASSED

### Criterion 9 (every required GitHub check successful on report-only head)

- NOT PASSED at drafting, for the single documented reason (Blocker B-1).
  Required-check state on implementation head
  `64dea09f49c39acdcd65a84ce9f4968b6268b304` (20 required checks):
  19 successful; 1 failed — `Compose and edge packaging`
  (job 105102384747). The CI Compose log shows the full browser matrix
  green on the remote: `browser-e2e: OK` for every project group and
  `compose-e2e: OK projects=11 setup=1 governance=1 preview=1
  stable-devices=6 agent-sessions=2 artifacts=disabled` (including the
  governance Puck drag that flaked once locally, and both new region
  preview tests), followed by exactly
  `public-agent-acceptance: FAILED
  reason=news-browser-structure-evidence-invalid` — the deterministic
  stale out-of-scope evidence pin of Blocker B-1 (two lines in
  `tools/compose/public_agent_acceptance.py`, lines 1335 and 2067,
  `"navigation": 0` → `2`). All other 19 required checks (Python 3.12/
  3.13/3.14 quality and package, Foundation PostgreSQL 14–18, Node
  contracts, Compose-independent supply-chain evidence, Markdown, Mermaid,
  Repository policy, Dependency review, CodeQL ×3, language detection)
  passed. No skip/pending/cancelled.
- Result: FAILED (sole cause: Blocker B-1; no other failing check;
  green attainable by the authorized two-line evidence-pin update with no
  product-code change)

### Criterion 10 (no doc claim that becomes false at merge)
All four doc updates (README, INCREMENTS, MVP-PROGRESS,
MVP-CONTRACT-AUDIT) use the 078-z durable wording: the 078/5 row is recorded
as *opened at `078-5-a` from verified remote main `d576fecf...`* with
*PR pending*; no sentence pairs a 078/5 merge claim with a date/SHA, and no
sentence asserts post-merge state as fact. `tools/check_repository.py`
(merge-fact ledger check) PASSes on the working tree. Any residual
"PR pending" phrasing is updated by strategy at acceptance per the ledger
convention used for 078/4.

- Result: PASSED (no claim becomes false when this PR merges; ledger
  state-line convention matches accepted 078/4 precedent)

## Exact read-scope gating (order report requirement)

- Agent `GET /api/agent/v1/global-regions`: HTTP gate
  `_require_scope(context, "global-region:read")` in
  `agent_api/agent_http.py` before any query; the trusted read SQL function
  `content.slaif_agent_region_list` additionally re-verifies
  `control.slaif_agent_require_capability(p_site_id,'global-region:read')`
  before returning rows (defense in depth; the route's base scope stays
  read-only).
- Agent `PATCH /api/agent/v1/global-regions/{id}`: HTTP gate is
  `global-region:read` only; `global-region:write` is charged in the trusted
  SQL barrier `content.slaif_region_apply` only on a real state change, and
  `header-footer:write` additionally only when the variant changes, before
  quota consumption — read-only no-effect replays never require write
  scopes.
- Editor `GET/PATCH`: `authorize_site_request` with `global-region:read`
  (list/get) and `global-region:write` (patch) over the human session; the
  deferred variant-change check requires `header-footer:write` in the
  authority's effective permissions (platform administrator bypass mirrors
  the existing Editor policy).
- Seeds: `control.permission` row `global-region:read` (category READ,
  agent_delegation_level 0, site_assignable true, installation_only false,
  system_only false) + `control.human_role_permission` grant for all seven
  human roles (idempotent `ON CONFLICT DO NOTHING` / `NOT EXISTS` inserts).
- Catalogs: TS `AGENT_READ_SCOPES` (14→15, order-pinned test updated) and
  Python `READ_SCOPES` (inherited by all four presets L0–L4 via the preset
  mapping).

## Render-context mechanism (order report requirement)
Regions resolve per render context with the identical trusted mechanism as
theme, in `render_api/projection.py`:

- Canonical (public): read from the public-pool canonical view
  (base-only projection; virtual defaults when no base row exists).
- Preview: the request runs inside a repeatable-read session bound to the
  active workspace (`app.session_id` = workspace UUID, `app.operation_id` =
  request operation) so the foundation COW view merge yields workspace-
  overlaid regions; the same projection pass renders them.
- Review snapshot: the reviewer-frozen immutable snapshot resolves regions
  from the snapshot's base rows (frozen at promotion), never from the live
  overlay.
Public, preview, and review renders share one component tree
(`apps/web/src/renderer/components.tsx`); only the projection context
differs.

Href contract (per render context):

- `page` nav targets resolve to same-site effective routes at projection
  time (fail-closed: an unresolvable page target renders no href).
- Canonical (public) renders use absolute site-rooted hrefs
  (`/s/<site_key>/<route>`).
- Preview renders use relative hrefs computed from the current page's
  site-path depth: at the preview site root `siteKey` /
  `siteKey/<route>`; at depth k > 0, `"../".repeat(k-1)` + route. Page URLs
  never carry a trailing slash (Next.js 308-normalizes), so the browser's
  relative base directory already excludes the page's own last segment —
  one fewer `../` hop than the site-path depth. The private workspace
  identifier therefore never appears in preview page HTML (privacy
  contract); clicking a relative link resolves inside the same preview
  tree.
- `internal` targets render as site-relative routes under the same contract
  and `external` targets render as their (already §34.2-validated) URL.

Language switcher contract: the projection resolves each enabled non-
current locale's target by re-rooting the current page under the target
locale tag per the effective-route contract (default-locale targets carry
no locale prefix) and resolving it against the site's pages in the active
render context (case-insensitive, lowercased-input matching mirroring
`normalize_request_path`; stored tag case preserved, e.g. `sl-SI`). A
resolved target yields `switcher_href` (the page's `effective_route`),
which the renderer maps through the href contract above; an unresolvable
target leaves `switcher_href` null and the renderer emits an inert
`aria-disabled` span — never a broken link. The current locale renders
`span[aria-current="true"]`.

## Bootstrap defaults as implemented (order report requirement)

- Deterministic per-site, lazy, idempotent: created on first read/write via
  the bootstrap path (mirrors theme bootstrap), never seeded for existing
  sites at migration time.
- Header default: `variant: institutional`, `content: {nav: [{label:
  "<site_key>", target: {kind: "internal", value: "/"}}]}`.
- Footer default: `variant: single-column`, `content: {links: [], note:
  ""}`.
- Deterministic record id `md5(site_id || ':' || region_key)::uuid`;
  `schema_version 'global-region/v1'`, `row_version 1`.
- Regions are virtual until first write: canonical/preview reads return the
  computed defaults with no base row; the first write materializes the base
  row.

## Page-target validation scope (recorded note)

- `page` targets: format-validated (UUID) and existence-validated in
  `content.slaif_region_page_targets_valid` — same site, `deleted_at IS
  NULL` (site-confined; cross-site UUID fails).
- `internal` targets: format-validated only — absolute route
  `^/[a-z0-9._~/-]*$`, length 1–256, rejects `//`, `..`, `%`, and reserved
  prefixes (`api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static`). No
  existence resolution against current pages (the order pins server
  validation for `page` targets only; the default header's `/` target must
  remain valid before any page exists).
- `external` targets: §34.2 bounds — `^https?://[^/@][!-~]*$`, length
  8–2048 (http/https only, no userinfo credentials, printable ASCII only).

## Local verification
All commands run from the repository root with uv `0.12.5`, Node 24.14.1,
pnpm `11.22.0`, TypeScript `6.0.3`; integration tests on a disposable local
PostgreSQL with fake credentials.

- `uv lock --check`: PASSED
- `uv sync --frozen --all-groups`: PASSED
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED
- `uv run --frozen mypy`: PASSED (279 files, clean)
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED
  (584 passed, including 30 new region-model tests)
- `uv run --frozen pytest services/backend/tests/integration`: PASSED
  (235 passed in 2315.99s, disposable local PostgreSQL, fake credentials;
  includes the new language-switcher regression test)
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED
- Process smokes (all 10, `uv run --frozen python -m slaif_agent_site.<module> --check`):
  control_api, editor_api, agent_api, render_api, mcp_adapter, media_service,
  review_worker, scheduler, media_gc, bootstrap: PASSED (health-only, no
  port bind, no mutation)
- `node --version` (v24.14.1), `pnpm --version` (11.22.0): PASSED
- `pnpm install --frozen-lockfile`: PASSED
- `pnpm lint`: PASSED
- `pnpm format:check`: PASSED
- `pnpm typecheck`: PASSED
- `pnpm test`: PASSED (all workspace suites green: component-catalog 8,
  scope-catalog 8, browser-tool-contracts 24, composition-schema 19
  (incl. new region-schema tests), apps/web 11 (incl. renderer-behavior),
  browser-worker 10, root contract tests 12)
- `pnpm build`: PASSED
- `pnpm licenses list --json`: PASSED (no policy violations)
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`:
  PASSED (zero drift)
- Component-catalog equality check: PASSED
- `python -m compileall -q tools tests/repository`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED
- `python tools/check_repository.py`: PASSED
- `python tools/check_mermaid.py`: PASSED (16 diagrams rendered)
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED (0 issues)
- `sh tools/compose/smoke.sh slaif0075a`: run 1 FAILED at
  `browser-e2e project=governance contract=puck-editor-round-trip-through-human-editor-api`
  (pre-existing VM load flake in the Puck drag section,
  `governance.spec.ts:699` `dragUntil`; unrelated to this increment —
  passed in run 2). Run 2: all compose stages through
  `compose-e2e: OK projects=11 setup=1 governance=1 preview=1
  stable-devices=6 agent-sessions=2 artifacts=disabled` PASSED (including
  both new region Playwright tests in the `preview` project), then
  `public-agent-acceptance: FAILED reason=news-browser-structure-evidence-invalid`
  — deterministic consequence of Blocker B-1 (stale out-of-scope evidence
  pin; exact fix listed there)

## GitHub CI / required checks

- State observed at drafting for implementation head
  `64dea09f49c39acdcd65a84ce9f4968b6268b304` (run 35190693675 /
  35190693639): 19/20 successful; `Compose and edge packaging` failed
  solely at `public-agent-acceptance` (Blocker B-1, log evidence above);
  0 pending, 0 skipped, 0 cancelled.
- All required green at drafting: NO — single failure documented under
  Blocker B-1; every other required check green.
- Report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Passwordless guest sudo used only for routine local test infrastructure
  (PostgreSQL binaries/services for the disposable integration database);
  no durable host setup, no package install into the tree, no lockfile
  change. All dependencies were already pinned; `uv.lock` and
  `pnpm-lock.yaml` are byte-identical to the base commit.
- Docker 29.1.3 + Compose 2.40.3 used for the Compose smoke; containers are
  disposable and torn down by the script.

## Documentation

- `README.md`: region/header-footer plane added to the implemented-surface
  wording (durable, implemented-not-planned).
- `oap/INCREMENTS.md`: 078/5 ledger row opened at `078-5-a` from verified
  remote main; PR-pending wording; historical-tense-safe.
- `oap/MVP-PROGRESS.md` + `oap/MVP-CONTRACT-AUDIT.md`: contract coverage
  wording updated for the region surface (implemented vs planned kept
  distinct).
- No architecture/constitution/protocol file touched (order does not
  require governance change).

## Safety and scope confirmations

- Unrelated files changed: no — the diff is exactly the order's allowed file
  set (see Files changed; criterion 8 evidence).
- Production secrets accessed: no. Production systems accessed: no.
- Required tests skipped/not run: none skipped; local Compose `public-agent-acceptance` stage FAILED only on the two stale out-of-scope structure pins documented under Blocker B-1 (all its upstream checks — capability/audit/artifact byte-verification — passed to that point); CI Compose result recorded under Criterion 9
- Scope deviation: no — one recorded implementation note on internal-target
  validation scope (see Page-target validation scope), within the order's
  binding text.
- Extra objective PR: NO. Coding-agent merge: NO. Auto-merge/close: NO.
- Activated order/active edited: NO — committed byte-for-byte unchanged
  (sha256 verified pre- and post-commit).
- Report commit changes only this report: yes (verified staged diff before
  commit).
- No capability, cookie, DB URL, or private artifact URL appears in the diff
  or this report; all test credentials are fake fixtures.

## Blocker (strategic decision required)
### B-1 — out-of-scope acceptance evidence pins vs ordered render contract
The ordered feature (binding design decision 5: site Header shell with nav
above `<main>` on every public/preview/review render) structurally changes
the DOM of every rendered page: each page now carries the header
`nav[aria-label="Site"]` (institutional default has one site-key entry) and
the `nav[aria-label="Language"]` switcher. The frozen public-agent
acceptance journey (`tools/compose/public_agent_acceptance.py`, created for
077u) pins the pre-feature structure with `"navigation": 0` in two
structure-summary expectations:

- line 1335 (news journey): `"navigation": 0`
- line 2067 (component journey): `"navigation": 0`

With the ordered defaults both pages render exactly **two** `nav` elements
(Site + Language; the single-column default footer has zero links and no
nav, and the checked pages have no ancestors, so no breadcrumb nav). The
only other evidence fields (`articles`, `collectionDetails`, `components`,
`detailStyle`, `htmlLang`, `main`, `rendererStylesheets`, `sections`,
heading/console/failed-request summaries) are unaffected — verified by the
full local browser runs.
The Compose smoke (and therefore the required CI `Compose and edge
packaging` check) runs this journey after the browser E2E and fails with
`news-browser-structure-evidence-invalid` (deterministic, not a flake).
This file is outside the order's allowed file set, and "No source tools" is
an explicit non-goal — so the executor did not modify it.
Local evidence: `sh tools/compose/smoke.sh slaif0075a` run 2 — all 11
browser projects PASSED (`browser-e2e: OK projects=11 ... preview=1`),
`compose-e2e: OK`, then `public-agent-acceptance: FAILED
reason=news-browser-structure-evidence-invalid`.
Exact minimal fix (one file, two lines, both `0` → `2`):

- `tools/compose/public_agent_acceptance.py:1335` `"navigation": 0` → `"navigation": 2`
- `tools/compose/public_agent_acceptance.py:2067` `"navigation": 0` → `"navigation": 2`
Requested resolution: an amendment round (078-5-b, AMENDED_EXISTING_PR,
same branch/PR) authorizing that two-line evidence-pin update — or an
equivalent explicit strategic authorization — after which the Compose
check goes green with no further code change. No product code, renderer
behavior, or in-scope file changes as a result.

## Known limitations / blockers

- The language switcher is mirror-page oriented by design: a locale is
  switchable from a page only when that page's effective route, re-rooted
  under the locale tag, resolves to an existing page in the active render
  context. Otherwise the tag renders inert (fail-closed). This is the
  contract the order's binding decisions 5–6 imply (no invented routing),
  and it is proven fail-closed in both the integration suite and the E2E.
- `internal` nav targets are format-validated but not existence-validated
  (see Page-target validation scope); a stale internal route renders a
  broken site-relative link until edited. The order pins server validation
  only for `page` targets.
- The `announcement` region key remains unimplemented (explicit non-goal);
  the variant enum and table design stay forward-compatible.
- Playwright evidence is local Compose (NGINX fronted) plus the remote CI
  browser matrix; no hosted browser service used.

## Recommended strategic follow-up
None required for this increment. Candidate next 078 scope (strategy's
choice): announcement-bar region, or the remaining catalog boundaries per
the 078-remaining-scope audit.
