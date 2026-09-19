# OAP Work Order — 078-5-a: site-global regions and header/footer management

- Identifier: `078-5-a` (increment-qualified; semantic increment 5 of numeric
  Objective 078; first qualified round of increment 5)
- PR mode: CREATE_NEW_PR
- Branch: `oap/078-5-a-global-regions-header-footer`
- PR title: `OAP 078-5-a: site-global regions and header/footer management`

## Verified current state (fill at activation, from live GitHub only)

- `main` = `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba` (post-078-z merge;
  strategy-verified against live GitHub on 2026-09-17, including the
  post-merge checks on the merge commit)
- 078-z governance transition merged: dual `NNN-L`/`NNN-I-L` OAP grammar in
  force (`tools/check_repository.py`), review-unit governance in force
  (`oap/governance/2026-09-14-review-unit-governance.md`), ID amendment in
  force (`oap/governance/2026-09-14-increment-qualified-round-ids.md`)
- Increments 078/1–078/4 accepted and merged at `3cae3d6`, `a9d3e68`,
  `fe31c9f`, `26cafc1` (full SHAs in `oap/INCREMENTS.md`)
- No Objective-078 product PR open; numeric 078 PARTIAL
- Strategic audit basis: `workorders/078-remaining-scope-audit-2026-09-14.md`
  (supervision workspace, 2026-09-14): catalog 22/32; global-region scope keys
  seeded but no region data plane; theme plane closed without header/footer
  variants; page-style plane is the established site/page-level data-plane
  template; media plane is the 079 boundary.

## Objective

Implement the site-global region and header/footer management data plane per
`ARCHITECTURE.md` §§19.4, 21.7–21.9, 22.1, 22.3–22.5, 24.6 and the normative
compact edition: stored Header and Footer regions with bounded variants and
bounded content, render-time derived Breadcrumbs and LanguageSwitcher, Render
projection extension across all three render contexts, human Editor (Design)
surface with Puck controls, the exact Agent API surface
`GET /api/agent/v1/global-regions` and `PATCH /api/agent/v1/global-regions/{id}`,
Level-4 write authority through the seeded scopes, full COW/row-version/
idempotency/audit/quota semantics mirroring the page-style and theme planes,
and exactly one reversible physical migration.

## Strategic context

- This is semantic increment 5 of Objective 078. It is the first
  increment-qualified round under the 2026-09-14 amendment; 078/1–078/4 are
  historical flat increments and remain immutable.
- The 2026-09-14 review-unit governance binds this increment: predeclared
  review budget (below), cumulative base→head size at every strategic review,
  CLOSURE_ONLY rules, finite rejection checklist, early split, and the final
  acceptance record format.
- Design decisions below are binding for this order. The single recorded
  divergence from normative text: the compact edition's theme paragraph
  mentions "header/footer variants" within the theme, but variants are
  implemented on the region record, NOT in `theme-schema/v1`. Rationale:
  078/2's closed theme contract (DB validator with exact key sets) stays
  byte-identical; L4 scope split (`header-footer:write` vs `theme-global:write`)
  supports the separation; the region is the natural owner of header/footer
  appearance. Recorded here as the authoritative interpretation for 078-5.

## Binding design decisions

1. Storage: one table `content.site_global_region` (id, site_id,
   `region_key` unique per site in `{header, footer}`, `variant` closed enum,
   `content` jsonb, schema_version, row_version, timestamps). Header variants:
   `{institutional, minimal}`. Footer variants: `{multi-column, single-column}`.
   No `announcement` key in this increment; the enum and table design stay
   forward-compatible.
2. Content: bounded structured entries, validated fail-closed by a
   PostgreSQL validator function (theme pattern):
   - Header content: `nav` — ordered entries, count 1..12, each
     `{label (localized, ≤256), target}` where target is
     `{kind: page|internal|external, value}`; page targets reference existing
     pages of the same site (server-validated), external targets obey §34.2
     URL bounds (http/https only, no credentials in URL, bounded length).
   - Footer content: `links` — ordered entries, count 0..16, same target
     shape; plus optional `note` localized text ≤4096.
   - Entry lists serialized in bounded jsonb (≤16 KiB per region content).
3. Bootstrap: deterministic per-site defaults (lazy, idempotent — created on
   first read/write if absent; documented defaults: header institutional with
   site-key nav entry; footer single-column with no links and empty note),
   mirroring the theme bootstrap pattern. No migration-time seeding of
   existing sites beyond lazy defaults.
4. Authority:
   - `GET /global-regions`: new read scope `global-region:read` added to the
     READ set of all four presets (scope-catalog change, both the TS catalog
     and the Python human-authorization catalog + any seed/check that pins the
     scope set). Report must state the exact gating implemented.
   - `PATCH /global-regions/{id}`: requires `global-region:write` (L4).
     Changing `variant` additionally requires `header-footer:write` (L4).
   - Editor API mirror: same server policy over the human session; Puck
     permissions are UX only.
5. Projection and Render:
   - `PageProjection` gains a site-level `regions` section resolved per render
     context exactly the way theme is resolved (canonical / active workspace
     overlay / immutable review snapshot — report must name the exact context
     mechanism verified).
   - Renderer: site Header shell above `<main>` (variant classes + nav), site
     Footer shell below `<main>` (variant classes + links), Breadcrumbs
     derived from the current page's ancestor chain (localized titles,
     ancestor pages linked via their effective routes, current page final and
     non-linked, `aria-label="Breadcrumb"`), LanguageSwitcher derived from
     `projection.locales` (enabled locales in position order, current
     highlighted, target = same effective route under the locale tag).
   - Public, preview, and review renders use the same component tree; only
     the context differs (no approximation rule violation).
6. COW/semantics: workspace writes follow the existing site-level overlay
   mechanism (theme pattern); row-version optimistic concurrency; semantic
   audit events for every region write (bounded, idempotency-key identity);
   idempotent replay semantics identical to page-style updates; quota: region
   content size and entry counts as bounded above.
7. OpenAPI: regenerated; Agent surface grows exactly the two §24.6 routes.

## Bounded scope — allowed file set (acceptance criterion 8 pins this)

- `services/backend/src/slaif_agent_site/db/alembic/versions/` — exactly one
  new migration (region table + validator function + bootstrap support),
  reversible
- `services/backend/src/slaif_agent_site/content_model/` — one new region
  module (models + service, page_style.py pattern)
- `services/backend/src/slaif_agent_site/agent_api/` — models + routes for the
  two Agent endpoints
- `services/backend/src/slaif_agent_site/editor_api/` — Editor mirror routes
- `services/backend/src/slaif_agent_site/render_api/projection.py` — regions
  section
- `packages/scope-catalog/src/index.ts` + `services/backend/src/
  slaif_agent_site/human_authorization/catalog.py` (+ any test/seed that pins
  the scope set) — `global-region:read` addition
- `packages/composition-schema/src/` — new product-owned region schema module
  (NOT generator output; not the component catalog)
- `apps/web/src/renderer/components.tsx`, `apps/web/src/sites/render.ts`,
  `apps/web/src/sites/shell.tsx` (+ renderer styles) — region shell,
  breadcrumbs, language switcher
- `apps/web/src/admin/composition-editor.tsx` (+ admin API client) — Design
  region controls
- Tests: `services/backend/tests/` (unit + API + projection), Puck/admin
  coverage, Playwright E2E (public canonical + preview overlay + Puck save +
  hostile negatives + concurrency + restart)
- Docs: `README.md`, `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`,
  `oap/MVP-CONTRACT-AUDIT.md` (durable wording per 078-z rules: no
  merge-time-false phrasing; GitHub authoritative for live state;
  `oap/active` = last activated round until next activation)
- OAP transcript: this order, `oap/active`, the report

## Explicit non-goals

- No announcement-bar region (deferred; enum forward-compatible)
- No `theme-schema/v1` change (078/2 contract byte-identical)
- No component-catalog change (no new component types; the four global
  catalog entries stay as-is; no generator run)
- No media, collection-view/query-DSL, page composition, or page-style change
- No source tools, MCP, review/promotion/publication work, exact-workspace Puck
- No dependency, lockfile, workflow, or ruleset change; no Dependabot PR
  interaction

## Requirements

1. Implement the design decisions 1–7 exactly as binding; where an
   implementation detail is not pinned, follow the page_style/theme plane
   patterns already merged in 078/2 and 078/4.
2. Every write path validates site confinement, workspace binding, capability
   scopes (including the variant→`header-footer:write` rule), row version,
   entry bounds, URL bounds, and content-size quota — fail-closed, server-side;
   the Editor path receives identical revalidation (§14.3, §22.4).
3. PostgreSQL validator function rejects unknown keys, unknown variants,
   over-bound entries, and malformed targets (hostile-negatives tested).
4. Full idempotency/audit/concurrency semantics per decision 6.
5. OpenAPI regenerated with zero drift; repository policy, Node contracts, and
   all generated-contract checks pass.
6. Docs updated with durable wording (see scope list); the 078/5 ledger row is
  added to `oap/INCREMENTS.md` in historical-tense-safe form (increment 078/5
  opens at `078-5-a`; state recorded against verified GitHub).
7. Commit the activated order and `oap/active` byte-for-byte unchanged with
  the implementation; report-only `SELF` commit parent = implementation head.

## Observable acceptance criteria

1. Public canonical page renders site header (variant styling + nav entries
   resolving to real routes), footer (variant + links), breadcrumbs (ancestor
   chain, current non-linked), language switcher (enabled locales, current
   highlighted) — real private browser (Playwright) evidence, same class as
   078/4.
2. Active-workspace preview shows workspace-overlaid regions differing from
   canonical; review-snapshot context resolves regions from the snapshot
   (mechanism named in report).
3. Human Editor Design surface: variant select + entry editors; Save writes
   the workspace; preview reflects the change; CSRF/session per Editor policy.
4. Agent API: L4 `PATCH` succeeds with idempotent replay; `GET` returns the
   region list; L3 denied (missing scope); unknown variant rejected;
   forbidden/raw-CSS keys rejected; external non-http(s) target rejected;
   cross-site capability rejected; row-version conflict rejected; over-quota
   content rejected — all hostile negatives evidenced.
5. Migration up and down verified; restart persistence; lazy bootstrap
   defaults proven idempotent.
6. Deterministic two-distinct-waiters concurrency on the same region (one
   succeeds, the other row-version conflict).
7. Semantic audit events present for region writes with bounded,
   idempotency-identical payloads.
8. Diff touches only the allowed file set; exactly one migration; no
   dependency/lockfile/workflow/ruleset/catalog/theme-schema change.
9. Every required GitHub check successful on the exact report-only head.
10. Docs contain no claim that becomes false when this PR merges.

## Verification

Local: `python tools/check_repository.py` PASS; backend unit + API suites
including new region tests PASS; `uv run --frozen ruff` + format clean;
markdownlint zero issues on changed docs; OpenAPI generation drift-free.
Remote: full CI matrix (this is a product increment — PostgreSQL 14–18,
Compose, browser E2E, supply chain, Markdown/Mermaid/CodeQL all required).

## Security

No arbitrary CSS/JS/iframe/templates (§22.3); §34.2 URL bounds on all
external targets; closed enums and bounded counts/lengths enforced in the DB
validator and app layer; site/workspace confinement fail-closed (I-1/I-5/
I-11); agent cannot publish/promote; every write audited; no new public query
surface; no secrets in diff or report.

## GitHub workflow

Base (verified remote main, strategy-verified 2026-09-17):
`d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`. Fresh PR from that base; all
commits pushed; report-only `SELF` commit; strategy performs independent
review and is the only merger.

## Report requirements

Standard OAP report template plus explicitly:

- the exact read-scope gating implemented for `GET /global-regions`;
- the exact render-context mechanism used for regions (canonical/preview/
  snapshot);
- the bootstrap defaults as implemented;
- the cumulative base→head size grouped per review-unit governance §2;
- per-criterion evidence for acceptance criteria 1–10, with honest
  pass/fail/skip/not-run per item — `COMPLETE` may be claimed only if every
  named criterion was actually executed (governance §4).

## Predeclared review budget (review-unit governance §1)

- Production/config files: ~16 (1 migration; 1 content_model module; agent
  models+routes; editor routes; projection; scope catalogs ×2; composition-
  schema region module; renderer components+render+shell+styles; admin
  editor+client)
- Migrations: 1 (reversible)
- Test/evidence footprint: backend unit/API/projection suites, Puck/admin
  coverage, Playwright E2E set per acceptance 1–6
- Generated-contract footprint: OpenAPI regeneration only (zero new surface
  beyond the two §24.6 routes); no catalog/generator run
- Docs footprint: README, INCREMENTS, MVP-PROGRESS, MVP-CONTRACT-AUDIT
- OAP transcript footprint: order + report
- Expected substantive implementation scale: ~1.5–2.5k lines incl. tests
- Review trigger (20–30 implementation files / several thousand lines): not
  expected to fire; if scope drift crosses it, CLOSURE_ONLY applies.
