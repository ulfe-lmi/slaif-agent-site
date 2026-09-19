# OAP Work Order — 078-7-a: catalog content and collection components (five new types)

- Identifier: `078-7-a` (increment-qualified; first round of semantic
  increment 7 of numeric Objective 078)
- PR mode: CREATE_NEW_PR
- Branch: `oap/078-7-a-catalog-content-collection-components` (new, from
  verified main)
- PR title: `OAP 078-7-a: catalog content and collection components
  (CallToAction, ContactBlock, CollectionSearch, CollectionFilter,
  RelatedItems)`

## Verified current state (verified at activation, from live GitHub and the
current main tree only)

- `main` = `2746c9f08c00fd84dff59bfd1536ce7319e16ff9` (merge commit of
  PR #85 / increment 078/5, merged 2026-09-19T03:24:39Z; PR #86 /
  increment 078/6 merged at `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`
  before it). Post-merge main branch CI runs CI 35418462017 and
  CodeQL 35418462112 are verified green on that head
- Catalog: `packages/component-catalog/src/catalog-v1.json` contains
  exactly 22 component types; `CallToAction`, `ContactBlock`,
  `CollectionSearch`, `CollectionFilter`, and `RelatedItems` are absent
  (architecture minimum is 32)
- R-doc-1 current-truth residual (bound to this order): the 078/5 merge
  fact is missing on five surfaces, which still carry "PR pending"
  wording: `oap/INCREMENTS.md` lines 6 and 18, `README.md` lines 72–73,
  `oap/MVP-PROGRESS.md` line 25, `oap/MVP-CONTRACT-AUDIT.md` lines 37 and
  99
- Render projection: `_collection_bindings` (projection.py) resolves
  `viewId` props only for `{CollectionList, CollectionGrid,
  CollectionDetail}`; no relation traversal exists anywhere in the
  projection; CollectionDetail resolves the current item by
  `route_parameter` (slug)
- Query DSL: per-primitive operator vocabulary exists
  (`content_model/query_dsl.py` `_OPS`: short_text eq/contains/prefix;
  long_text/rich_text/url/email eq/contains; integer/decimal/date/
  datetime eq/lt/lte/gt/gte; boolean eq; enum eq/in)
- Puck adapter (`packages/composition-schema/src/puck-adapter.ts`) is
  fully catalog-driven: new catalog types automatically receive Puck
  controls; forbidden-prop-key blocking is generic
- Catalog change mechanism: `tools/generate_component_catalog.py`
  regenerates four targets — backend `component_catalog.py`,
  `packages/component-catalog/src/index.ts`,
  `packages/composition-schema/src/catalog-v1.json`, and the in-place
  migration `060_001_agent_component_semantics.py` (baked catalog JSON +
  DB guard `control.slaif_component_catalog()`;
  `allowed_component_types` derives from the same JSON). In-place
  regeneration of `060_001` has precedent: commits `370dd7b`, `a0622be`,
  `bdfa80e` (legacy rounds 078-b/078-c). No new alembic migration is
  created for catalog changes
- Renderer (`apps/web/src/renderer/components.tsx`, 700 lines) is fully
  stateless (no `useState`/`useEffect` anywhere in the renderer tree);
  data components share one `<Collection mode=.../>` implementation
- Composition write-time validation: site-scoped view resolution exists
  (`service.get_view_for_site`); the DB guard
  (`control.slaif_agent_component_validate`) validates component
  type/props/view references
- Objective 078 state: increments 078/1–078/6 accepted and merged;
  numeric 078 remains PARTIAL

## Strategic context

Per the 2026-09-19 re-plan (`workorders/078-remaining-scope-audit-2026-09-14.md`
§6), this increment delivers the five dependency-ready catalog
components. The three media-dependent components (Gallery, LogoGrid,
DocumentList) and real Image rendering remain 079-bound; VideoEmbed and
MapBlock remain a separate 078/8 embed-safety increment. This PR
introduces exactly one new renderer capability (bounded client-side
filtering over pre-fetched bounded bindings) and no new public query
endpoint, keeping the §24.6 surface closed.

## Objective

Add `CallToAction`, `ContactBlock`, `CollectionSearch`,
`CollectionFilter`, and `RelatedItems` to the component catalog (22→27),
with bounded prop schemas, renderers, projection support, write-time
binding validation, Puck exposure, acceptance-journey E2E coverage, and
the R-doc-1 current-truth remediation — all on a fresh PR from verified
main.

## Binding decisions

1. **CallToAction** (category basic, authority content, binding none,
   no slots, max_children 0): props — `heading` (string, localized,
   required, max_length 256); `text` (string, localized, optional,
   max_length 1024); `label` (string, localized, required, max_length
   64); `href` (string, required, max_length 4096); `variant` (enum
   [primary, secondary, ghost], optional).
2. **ContactBlock** (category institutional, authority content, binding
   none, no slots, max_children 0): props — `organization` (string,
   localized, required, max_length 256); `address` (string, localized,
   optional, max_length 512); `phone` (string, optional, max_length 32);
   `email` (string, optional, max_length 254); `hours` (string,
   localized, optional, max_length 512). Flat string props only; no map
   embed (MapBlock is 078/8).
3. **CollectionSearch** (category data, authority content, binding
   `collection_view`, no slots, max_children 0): props — `viewId`
   (reference, format uuid, required); `limit` (number, minimum 1,
   maximum 100, optional, renderer default 50); `placeholder` (string,
   localized, optional, max_length 64). Render: single text input; the
   client filters the pre-fetched bounded item array with
   case-insensitive `contains` over the item title and every short/long
   text value; no new public query endpoint; input processing caps at
   256 characters.
4. **CollectionFilter** (category data, authority content, binding
   `collection_view`, no slots, max_children 0): props — `viewId`
   (reference, format uuid, required); `limit` (number, minimum 1,
   maximum 100, optional, renderer default 50); `facets` (array,
   required, min_items 1, max_items 4; item: object with `fieldKey`
   (string, required, max_length 64), `operator` (enum [eq, contains,
   prefix, lt, lte, gt, gte, in], required), `value` (string, required,
   max_length 4096); for `in`, value is a comma-separated list of at
   most 8 entries of at most 256 characters each). Write-time
   validation: resolve the site-scoped view, then reject any facet whose
   `fieldKey` is not a field of the view's content type or whose
   `operator` is not in that field's per-primitive DSL vocabulary
   (`query_dsl._OPS`). Render: apply the facets with fixed operator
   semantics (numeric/date comparisons for numeric/date primitives;
   case-insensitive text for text primitives; case-insensitive match for
   enum `in`) over the pre-fetched bounded item array.
5. **RelatedItems** (category data, authority content, binding
   `collection_view`, no slots, max_children 0): props — `viewId`
   (reference, format uuid, required); `limit` (number, minimum 1,
   maximum 20, optional, renderer default 8); `heading` (string,
   localized, optional, max_length 256). Semantics pinned: same-view
   fallback only — on a detail route the projection pre-fetches items
   from the bound view (view filter/sort applied) excluding the current
   route item; on non-detail pages it renders nothing; relation-driven
   relatedness is out of scope (no relation traversal in this increment).
6. **Projection change, minimal**: extend `_collection_bindings` to the
   five binding types (three new: CollectionSearch, CollectionFilter,
   RelatedItems); honor each component's `limit` prop capped by the
   view's pagination; the CS/CF binding payload additionally carries a
   bounded `filter_fields` descriptor (key + primitive, derived from the
   view's content type, at most 32 entries) used by the renderer for
   fixed-operator comparisons; RI exclusion of the current route item
   happens server-side.
7. **Renderer, one new bounded-interactivity pattern**: the first and
   only client-state components in the renderer (CS/CF). Documented
   pattern: local state only (input text and facet values), no network
   I/O, no persistence, no URL mutation, fixed operators, capped input
   processing. CT/CB/RI are static renderers. No arbitrary HTML, no
   raw CSS (catalog props only), no iframes.
8. **No new public endpoints, no new scopes, no OpenAPI growth**: the
   versioned OpenAPI must be byte-identical after this increment (the
   component types ride the generic composition CRUD surface); if
   regeneration changes anything, STOP and report BLOCKED.
9. **No new migration**: catalog changes regenerate the four generator
   targets including the in-place `060_001` baked JSON (precedent
   078-b/078-c). No other migration file changes.
10. **R-doc-1 remediation (requirement 0)**: replace the stale 078/5
    "PR pending" wording on the five identified surfaces with the
    verified merge fact — "accepted and merged in PR #85 at
    `2746c9f08c00fd84dff59bfd1536ce7319e16ff9` on 2026-09-19" — using
    durable wording (GitHub is authoritative for live acceptance/merge
    state; record immutable merge facts). No other prose restructuring.

## Bounded scope — allowed file set

- `packages/component-catalog/src/catalog-v1.json` (5 new component
  entries, exact binding-decision schemas)
- Generator targets (regenerated, no hand edits):
  `services/backend/src/slaif_agent_site/content_model/component_catalog.py`,
  `packages/component-catalog/src/index.ts`,
  `packages/composition-schema/src/catalog-v1.json`,
  `services/backend/src/slaif_agent_site/db/alembic/versions/060_001_agent_component_semantics.py`
- `services/backend/src/slaif_agent_site/render_api/projection.py`
  (binding extension per decision 6)
- `services/backend/src/slaif_agent_site/` composition write-time
  validation path (facet fieldKey/operator validation per decision 4;
  placement at the executor's discretion consistent with existing
  pre-checks, fail-closed)
- `apps/web/src/renderer/components.tsx` + at most one new small
  renderer module for the bounded-filter pattern (decision 7)
- `tools/compose/public_agent_acceptance.py` (journey: the five
  components end-to-end) and at most one new Playwright spec file for
  the browser-side filtering contracts
- Docs: `README.md`, `oap/INCREMENTS.md` (078/5 line correction + 078/7
  row), `oap/MVP-PROGRESS.md`, `oap/MVP-CONTRACT-AUDIT.md`
  (R-doc-1 lines + 078/7 row, durable wording)
- OAP transcript: this order, `oap/active`, this report

If the audit finds further files requiring change (e.g. a shared
renderer helper, journey fixture), include them only if strictly
necessary for this semantic and list them in the report.

## Explicit non-goals

- No VideoEmbed/MapBlock or any embed/iframe surface (078/8)
- No Gallery/LogoGrid/DocumentList, no real Image/media rendering (079)
- No theme-schema change, no page-style change, no region change
- No new public query endpoint, no client-side querying beyond the
  bounded in-memory pattern
- No relation traversal, no new scope, no OpenAPI route, no new
  migration, no dependency change
- No Dependabot PR interaction; no change to `main`

## Requirements

0. Apply the R-doc-1 remediation of decision 10 to exactly the five
   identified surfaces (plus the 078/7 ledger row per existing format).
1. Add the five catalog entries of decisions 1–5 and regenerate all four
   generator targets; the generated `060_001` file differs only in the
   baked catalog JSON.
2. Implement the projection extension of decision 6.
3. Implement the renderers of decision 7 (static CT/CB/RI; bounded
   client filtering CS/CF with the documented pattern).
4. Implement the fail-closed facet validation of decision 4 (server
   rejects unknown fieldKey and out-of-vocabulary operator at
   composition write time, for both Agent and human Puck paths).
5. Extend the acceptance journey so it proves, end-to-end: the five
   components created via the Agent API render on the public canonical
   with the expected bounded markup; the bound view contains at least
   one short-text and one integer field (extend the journey's type
   definition if needed) and at least three items; CollectionSearch
   filters in the browser (input → filtered list, empty-result state,
   256-char cap); CollectionFilter facets filter correctly (text and
   integer operators; `in` on the enum or rejected per vocabulary);
   RelatedItems renders only on the detail route (excluding the current
   item) and nothing on the top level; hostile writes are rejected
   (unknown fieldKey, out-of-vocabulary operator, 5th facet, 9-entry
   `in`, limit 101, cross-site viewId); the Puck path creates at least
   one of the new components and saves; preview shows the workspace
   overlay; restart persistence holds.
6. Local verification: full Compose smoke
   (`sh tools/compose/smoke.sh slaif0075a` run class) end-to-end;
   `python tools/check_repository.py` PASS; generator run leaves the
   versioned OpenAPI byte-identical (record the check); focused unit
   suites for the changed backend modules.
7. Commit the implementation (with this order and `oap/active`
   byte-for-byte unchanged), push, open the PR, then make the
   report-only `SELF` commit (parent = this round's implementation
   head). If a documented Puck drag VM flake class occurs in local or
   CI runs, at most one unmodified re-run, documented.

## Observable acceptance criteria

1. Catalog is exactly 27 types; the five new entries match binding
   decisions 1–5 byte-for-byte in `catalog-v1.json` and in all four
   regenerated targets; the `060_001` diff is the baked JSON only.
2. No new migration files; no OpenAPI route change (versioned OpenAPI
   byte-identical); no new scope; no lockfile change.
3. The five R-doc-1 surfaces carry the verified 078/5 merge fact
   (SHA `2746c9f08c00fd84dff59bfd1536ce7319e16ff9`, 2026-09-19) with
   durable wording; no other prose restructuring.
4. Write-time validation is fail-closed: every hostile case of
   requirement 5 is rejected with a bounded error, proven in tests and
   the journey.
5. The full local Compose smoke passes end-to-end (exact final status
   lines recorded) or a single documented flake-class re-run occurred.
6. On the exact report-only head, all 20 required GitHub checks are
   successful; the report records every check's conclusion.
7. The report contains per-criterion evidence and the cumulative
   base→head size grouped per review-unit governance §2 (base =
   `2746c9f08c00fd84dff59bfd1536ce7319e16ff9`).

## Predeclared review budget (review-unit governance §1)

- Production/config files: ~10 (catalog source + 4 generated targets,
  projection, validation path, renderer + at most 1 new module)
- Migrations: 0 (in-place `060_001` regeneration only, precedent
  078-b/078-c)
- Test/evidence footprint: journey extension, at most 1 new Playwright
  spec, focused unit suites
- Generated-contract footprint: 0 (OpenAPI byte-identical; verified)
- Docs footprint: 4 files (R-doc-1 corrections + 078/7 rows)
- OAP transcript footprint: order + active + report
- Expected substantive implementation scale: 1.5–2.5k lines including
  tests
- Review trigger: not expected to fire; if scope drift pushes it,
  CLOSURE_ONLY per governance §3

## Security

No new authority surface: the five types are composition content under
existing site/workspace confinement and existing scopes; view references
remain site-scoped; the client-filtering pattern performs no I/O and
cannot widen data access (it filters what the projection already
delivered, bounded); no arbitrary HTML/CSS/iframe; hostile-input
rejection is fail-closed and E2E-proven. No secrets in diff or report.

## GitHub workflow

CREATE_NEW_PR: new branch
`oap/078-7-a-catalog-content-collection-components` from
`2746c9f08c00fd84dff59bfd1536ce7319e16ff9`; open the PR with the title
above and a body referencing this order per repository convention; push
all commits; the report commit is `SELF`; Strategy is the only merger.

## Report requirements

Standard OAP report template plus explicitly:

- the five catalog entries as committed (JSON) and confirmation that the
  four regenerated targets match the generator output (re-run the
  generator locally and show zero diff);
- the `060_001` diff limited to the baked JSON;
- the OpenAPI byte-identity check result;
- the R-doc-1 before/after for each of the five surfaces;
- the hostile-case rejection evidence (request → bounded error), for
  both the Agent API and the Puck path;
- the exact final status lines of the local Compose smoke run;
- the browser-side filtering proof (CS input, CF facets, RI
  detail-route-only) from the journey or spec logs;
- the conclusion of every one of the 20 required checks on the exact
  report-only head;
- the cumulative base→head size grouped per review-unit governance §2.

## Local authority

Standard executor authority in the disposable VM: packages, Docker,
browser tooling, test execution, CI log retrieval. Guest sudo only if
genuinely required; record any use.
