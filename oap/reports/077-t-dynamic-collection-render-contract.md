# OAP Coding-Agent Report — 077-t

## Work order

- Identifier: 077-t
- Work-order file: oap/orders/077-t-dynamic-collection-render-contract.md
- Work-order SHA-256: ee1730b5827c5f9900cea8c048afd562300ca7325dbe44842a23bfcf101e5044
- Active SHA-256: 49dfc606e177f2d39dfb067d9fca0f66ce925b11cd2a62e6309c681d9c142ab3
- Numeric objective: 077
- PR mode: AMENDED_EXISTING_PR

## Status

COMPLETE

## Executive summary

Implemented the bounded dynamic collection listing/detail contract on PR #74.
The same trusted Render resolver preserves static exact-route behavior and also
resolves a terminal literal {slug} page route with one bounded ASCII item-slug
segment. Dynamic pages are leaves and require exactly one trusted
CollectionDetail node. That node binds one same-site active collection view,
type definition version, filter, status, and declared projection to the exact
routed item.

Collection projections now permit declared localized fields while keeping
localized filtering and sorting forbidden. Render validates base and
translation values, selects the requested locale and then explicit default
fallback per field, and fails closed on missing or corrupt required output.
Published canonical rendering excludes DRAFT and ARCHIVED details; authorized
preview includes DRAFT but not ARCHIVED.

Migration 055 now has a real downgrade restoration for its 054-state human
editor lock and 051 redirect dependency helper. Migration 056 supplies the
dynamic resolver and localized-projection validation wrapper without rewriting
historical migration bytes.

## Authoritative GitHub state

- Repository: ulfe-lmi/slaif-agent-site
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), OPEN, not
  merged
- Base/head: main / oap/077-agent-site-structure-semantics
- Starting remote report head: a12bd51f22a70f10f0851d524695a96bd097941e
- Implementation head SHA: b76bf2f7379460658c39176fe6c058dd0515edb0
- Implementation commits pushed before report:
  598af7f, b44a5dd, d41c2a5, 036c021, b76bf2f
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- New PR: no; existing PR amended: yes; merge/auto-merge: NO

## Changes made

- Added migration 056_001_dynamic_render_collection_contract.py:
  dynamic static-first page resolver with bounded terminal slug grammar;
  ambiguity and malformed dynamic-route fail-closed behavior; localized
  projection validation wrapper; and public/preview reader grants.
- Corrected migration 055 downgrade to restore the exact pre-055 exclusive
  human-editor lifecycle lock, the 051 redirect page-target dependency helper,
  owner-only helper privileges, editor-runtime lock privilege, and data across
  the 054-to-055-to-054-to-055 round trip.
- Extended Render projection with typed route parameters, exact CollectionDetail
  item binding, same-site active view/type/version/filter/status checks,
  localized translation selection/default fallback, and fail-closed malformed
  or missing required output.
- Allowed localized fields only in declared collection projection fields;
  localized filters and sorts remain rejected.
- Added public Agent News fixture coverage and dynamic/static Render tests.
- Updated API, testing, MVP, and migration-head documentation/contracts.

## Files changed

- apps/web/src/sites/render.ts
- docs/API.md
- docs/TESTING.md
- oap/MVP-PROGRESS.md
- oap/active
- oap/orders/077-t-dynamic-collection-render-contract.md
- services/backend/src/slaif_agent_site/agent_state/mutations.py
- services/backend/src/slaif_agent_site/bootstrap/service.py
- services/backend/src/slaif_agent_site/content_model/query_dsl.py
- services/backend/src/slaif_agent_site/content_model/service.py
- services/backend/src/slaif_agent_site/db/alembic/versions/055_001_redirect_dependency_cow_tombstone.py
- services/backend/src/slaif_agent_site/db/alembic/versions/056_001_dynamic_render_collection_contract.py
- services/backend/src/slaif_agent_site/render_api/projection.py
- affected integration/unit contract tests under services/backend/tests/

## Acceptance-criteria evidence

### Dynamic routing and exact detail binding

- Public Agent integration creates the News type, localized title/summary
  fields, sortable rank field, PUBLISHED/DRAFT/ARCHIVED items, exact locale
  translations, bounded collection view, /news listing page, literal {slug}
  detail leaf, trusted CollectionList/CollectionDetail nodes, and navigation
  entirely through Agent HTTP.
- Preview listing is sorted and localized.
- Preview /news/published-item binds exactly that item and exposes the typed
  slug route parameter.
- Preview /news/draft-item succeeds; ARCHIVED and unknown detail routes return
  not-found.
- Canonical listing/detail do not see Agent-created workspace rows.
- Agent slug rename moves preview availability to the new route and removes the
  old route.
- Direct Render integration independently proves localized projection,
  static/dynamic precedence, exact binding, and canonical status isolation.

### Localization and bounded DSL

- Declared localized projection fields are accepted through the public Agent
  collection-view create path and rendered with selected-locale/default-locale
  semantics.
- Localized filter and sort fields remain rejected.
- Projection fields remain declared-only; identity keys, unknown fields,
  duplicates, raw SQL/JS markers, oversized/complex queries, and invalid
  pagination remain rejected.
- Base values and translation values use trusted primitive validators;
  malformed or missing required localized output fails the whole route rather
  than returning an empty detail shell.

### 055 downgrade and security

- Real PostgreSQL test passes 054-to-055-to-054-to-055.
- Downgrade restores the exclusive human-editor lock, 051 helper function,
  owners, PUBLIC/runtime/editor grants, and persisted page data.
- Upgrade restores the shared lock and tombstone-aware helper.
- Pre-070 migration bytes remain immutable.
- No raw SQL, executable component/query input, arbitrary route/query
  parameter, cross-site UUID substitution, capability leakage, or production
  credential access was introduced.

## Local verification

- Full backend integration: PASSED — 173 passed in 1493.49 seconds.
- Python unit/repository suite: PASSED — 522 passed, one existing Starlette
  deprecation warning.
- uv lock check, frozen sync, Ruff, format, mypy, and uv build: PASSED.
- Repository preparation: PASSED — 58 tests, repository policy, 16 Mermaid
  diagrams in 3 files, and Markdownlint 399 files with 0 issues.
- Node: PASSED on Node 24.14.1 and pnpm 11.22.0: frozen install, lint,
  format, typecheck, tests, build, and license inventory.
- Supply-chain policy/evidence tests: PASSED — 35 tests.
- Full supply-chain evidence: PASSED — 6 images, 0 Critical, 42 High;
  checksums, reproducibility, clean builds, Apache, and Postgres libcurl
  overlay all passed.
- A separate local NGINX HTML capture was not rerun independently of the
  existing Compose/edge path; current remote Compose and edge packaging is
  successful and existing Web renderer contracts remain green.

## GitHub CI / required checks

For implementation head b76bf2f7379460658c39176fe6c058dd0515edb0, all observed
required checks are SUCCESS:

- Repository policy
- Node contracts
- Python 3.12, 3.13, and 3.14 quality and package
- Foundation PostgreSQL 14, 15, 16, 17, and 18
- Compose and edge packaging
- Supply-chain evidence
- Markdown
- Mermaid
- Dependency review
- CodeQL and all language analyses

PR merge state is CLEAN; PR #74 remains open and unmerged.

## Local setup / dependencies

No new dependency, image, hosted service, credential, or infrastructure
requirement was added. Existing uv, pnpm, Node, PostgreSQL, and Docker tooling
was used.

## Documentation

Updated docs/API.md, docs/TESTING.md, and oap/MVP-PROGRESS.md for the
implemented dynamic route, collection detail, localization, migration, and
evidence boundaries. No architecture or constitution bytes were changed.

## Safety and scope confirmations

- Activated order and active content were edited by strategy only and committed
  unchanged by the coding agent.
- Historical orders and reports were not edited.
- Production secrets, systems, and data were not accessed.
- No required verification was omitted; the separate local NGINX capture is
  explicitly identified above and remote Compose/edge CI is green.
- No component update/move/delete/design/Puck, media/MCP/freeze/review/
  promotion, source tools, new primitive/operator, dependency, architecture,
  or release work was added.
- Extra objective PR: NO.
- Coding-agent merge/auto-merge: NO.
- Report-only commit changes only this report: YES.

## Known limitations / blockers

The final hostile whole-objective audit and strategic acceptance/merge remain
outstanding by design. The coding agent has completed 077-t and will not merge
PR #74.

Objective 077 / PR #74 is eligible for strategic completion only after strategy
independently reviews the complete 077 transcript, confirms the bounded scope
and evidence, and makes the separate merge decision.
