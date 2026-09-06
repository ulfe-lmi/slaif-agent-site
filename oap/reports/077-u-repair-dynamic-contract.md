# OAP Coding-Agent Report — 077-u

## Work order

- Identifier: 077-u
- Work-order file: `oap/orders/077-u-repair-dynamic-contract.md`
- Work-order SHA-256: `650358599616eac83d714b77e8eda0ff2833841166170ee9ff6dbaa8ce2712db`
- Active SHA-256: `14ffbaa042914fc4771b1ecf94d933e0c669163fffb49d1ce01eb6b0074eb714`
- Numeric objective: 077
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Repaired the accepted 077-t implementation and supplied the missing intended-interface and concurrency evidence on PR #74. The trusted database validator now checks the original four-document query contract, including localized-only projections, hostile markers, recursive bounds, duplicates, and the total projection-field limit. Render now fails closed on stale item/type/view definitions, supports normalized non-default-locale dynamic routes, preserves static CollectionDetail behavior, and removes internal identifiers from rendered HTML.

The Compose acceptance path now creates a localized News model, pages, dynamic detail route, navigation, and mutations exclusively through public Agent HTTP, then verifies default and non-default NGINX/Web HTML, browser preview, canonical isolation, exact route/status behavior, and Agent/Render/Web restart recovery. Deterministic PostgreSQL race and cancellation tests cover the required dynamic snapshot boundaries.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), OPEN, not merged
- Base/head: `main` / `oap/077-agent-site-structure-semantics`
- Required starting remote report head: `1704b312b13f6d8b3aa1714305d40d11a6cac309`
- Implementation head SHA: `ec04054d8b1f319ec04b79307c4c670350c00df5`
- Implementation commits pushed before this report: `0dd81bb`, `8690bb4`, `71f8d5e`, `14f8742`, `a70df5f`, `c046594`, `d27a7a8`, `2679c8c`, `ccd34f1`, `eba678f`, `cdbff9b`, `ef37178`, `e440cf0`, `06cc0a5`, `e874317`, `abc8e67`, `d5a9e2b`, `19b94da`, `723802a`, `85bed54`, `7a61d82`, `a2273a9`, `ca6fc1d`, `b4afd23`, `3d01975`, `58f27db`, `5d16f67`, `ec04054`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- New PR: no; existing PR amended: yes; merge/auto-merge: NO

## Production corrections

- Migration 056 now validates the original filter, sort, projection, and pagination documents before any localized projection delegation. It rejects extra projection keys, unknown/reserved fields, duplicate fields, non-string fields, more than 16 total fields, oversized localized-only input, recursive/deep/node-heavy input, and executable/SQL-like markers. Direct trusted SQL invocation is covered, and rejected projections leave no view, quota, idempotency, or audit residue.
- Render selects and compares `content_item.type_definition_version` with both the active type and collection view definition versions; stale items fail closed in list and detail projections.
- Dynamic route extraction now compares the already database-resolved route prefix case-insensitively, while preserving the database slug grammar and strict single-segment behavior. Stored `sl-SI` pages therefore resolve normalized `/sl-si/...` requests.
- Static pages retain their prior CollectionDetail behavior. Dynamic pages still require exactly one CollectionDetail and bind exactly one exact-slug item.
- Public and preview renderer HTML no longer serializes `data-site-id`, `data-node-id`, or other internal UUID attributes. The preview route now returns trusted static HTML without Next Flight route metadata, preventing the workspace UUID from entering the response body; the external preview URL and browser credential contract remain unchanged.

## Intended-interface evidence

- Public Agent HTTP creates the News type, localized fields, PUBLISHED/DRAFT/ARCHIVED items, `en` and `sl-SI` translations, bounded view, default and localized listing/detail pages, trusted CollectionList/CollectionDetail nodes, and navigation.
- NGINX/Web HTML verifies sorted default listing, default-locale detail, normalized non-default-locale detail, selected/default localized values, route/status/slug/translation mutations, archived/filter-excluded/unknown/extra/encoded paths, trusted renderer markup, canonical byte stability after removing only Next per-response `nonce` and `ce` response-context fields, and absence of capability tokens, browser credentials, UUIDs, and raw projection JSON.
- A real public Agent browser-preview run is submitted for the dynamic detail route and required to reach `COMPLETED`; its durable artifact rows/files are removed as bounded acceptance-fixture cleanup before the independent generic Compose artifact-count policy runs. Existing focused PostgreSQL browser tests prove exact site/workspace/route binding, one-use/replay rejection, wrong-workspace rejection, and canonical isolation.
- Agent, Render, and Web restarts are exercised with bounded readiness polling and the same workspace dynamic result. No correctness assertion relies on a timing sleep.

## Race and cancellation evidence

The PostgreSQL `test_dynamic_collection_detail_route_binds_exact_published_item` integration test uses repeatable-read transactions and `asyncio.Event` barriers to prove:

- detail render versus item slug/status/translation mutation returns one coherent before snapshot and a later durable 404;
- detail render versus item deletion returns the coherent before snapshot and a later 404;
- listing render versus collection-view projection change and type-definition change does not mix versions and fails closed after the mutation;
- detail render versus dynamic page-parent route move returns the old snapshot and then only the new route;
- cancellation after the exact route snapshot closes cleanly, and a later render proves the pool and session are reusable.

The public Agent News integration also proves direct database projection rejection and durable residue invariants.

## Files changed in this repair

- `services/backend/src/slaif_agent_site/db/alembic/versions/056_001_dynamic_render_collection_contract.py`
- `services/backend/src/slaif_agent_site/render_api/projection.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_render_structure_router.py`
- `apps/web/src/renderer/components.tsx`
- `apps/web/src/sites/preview-page.tsx`
- `apps/web/proxy.ts`
- `apps/web/app/preview/[workspaceId]/[[...sitePath]]/route.tsx`
- `apps/web/tests/surface.test.mjs`
- `tests/e2e/preview.spec.ts`
- `tools/compose/public_agent_acceptance.py`

Historical orders, reports, the constitution, architecture, and `oap/active`
were not edited.

## Local verification

- Complete backend integration suite: PASSED — 173 passed in 1476.34 seconds (24:36), isolated from all other integration processes.
- Focused dynamic PostgreSQL race/render test: PASSED.
- Focused public-Agent News and direct database validator/residue test: PASSED.
- Python: frozen environment, Ruff, format, mypy (256 source files), unit/repository baseline (522 passed), and package build passed.
- Node/Web: lint, format, typecheck, surface tests (10 passed), and production Next build passed.
- Repository preparation: repository policy passed; Mermaid passed; Markdownlint passed with 0 issues.
- Full supply-chain evidence passed previously on the 077-u head: six images, zero Critical findings, 42 High findings, reproducibility/checksum/SBOM evidence, and clean artifact policy.

## GitHub required checks

For implementation head `ec04054d8b1f319ec04b79307c4c670350c00df5`, the authoritative PR checks are SUCCESS:

- Repository policy
- Node contracts
- Python 3.12, 3.13, and 3.14 quality and package
- Foundation PostgreSQL 14, 15, 16, 17, and 18
- Compose and edge packaging
- Supply-chain evidence
- Markdown
- Mermaid
- Dependency review
- CodeQL and actions/Python/JavaScript analyses

PR #74 remains open, clean, and unmerged.

## Scope and safety confirmations

- No new dependency, image, hosted service, production credential, or infrastructure requirement was added.
- No production system, data, credential store, Docker socket, capability token, browser token, cookie, or private artifact URL was accessed outside the disposable Compose/test scope.
- No 078+ composition/Puck scope, media, MCP, workspace review/promotion, source sweep, primitive/operator, dependency, architecture, or unrelated cleanup work was added.
- No extra PR was created. The coding agent did not merge or auto-merge PR #74.
- The report-only commit changes only this report and has literal implementation SHA `ec04054d8b1f319ec04b79307c4c670350c00df5` as its first parent.

## Completion condition

Objective 077 / PR #74 is complete from the coding-agent side when this report-only commit is the verified remote PR head. Strategy must still independently review the immutable transcript and decide acceptance/merge; the coding agent does not merge the PR.
