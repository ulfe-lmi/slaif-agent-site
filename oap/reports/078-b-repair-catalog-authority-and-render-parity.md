# OAP Coding-Agent Report — 078-b

## Work order

- Identifier: `078-b`
- Work-order file: `oap/orders/078-b-repair-catalog-authority-and-render-parity.md`
- Work-order SHA-256: `d6f25d3c2fb6af363a1cbc35bd4e448897843e1e6f7608ec8c509ce98b3f2826`
- `oap/active` bytes: `078-b\n`
- `oap/active` SHA-256: `ae5ab93f467cf92cc2f9b5e954d981fb23a100c29ff485ad99a10830717804f4`
- Numeric objective: `078` (this report completes only the activated `078-b` repair round)
- PR mode: `AMEND_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Repaired the unaccepted `078-a` catalog/contract slice on the existing
Objective 078 PR. One committed `catalog-v1` JSON document now drives the
Python catalog, TypeScript package, Puck adapter, Agent discovery, PostgreSQL
060 snapshot/validation, Render validation, and Web renderer semantics. A
deterministic generator/check detects byte or semantic drift. Nested props are
closed and bounded, structured RichText/Statistics/Timeline/FAQ values have
deterministic meaning, and Web preserves the valid structured RichText
fixture.

The trusted database PATCH helper now rejects design-only prop additions,
changes, and removals even when invoked directly through the runtime role.
The public Agent catalog and create contracts are explicitly typed and closed;
Agent create no longer accepts legacy `order_key`, while legacy Editor/Puck
ordering remains compatible. A first remote CodeQL run found one missing
`vbscript:` URL rejection in the Puck adapter; the narrow security correction
was applied consistently to Puck, generated Python, Render, and PostgreSQL,
then the complete current-head remote matrix passed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77) — `OPEN`
- Base/head branches: `main` / `oap/078-agent-composition-design-semantics`
- Starting remote SHA: `4d81ca24e6d7bb05f78fd6d051ba2e51a988cd27`
- Base remote SHA: `ae3a4a681bb888260192b7bb1b2a337b4906828d`
- Final implementation head SHA: `a0622be0588268b8cca6ac1878391e10412bb079`
- Implementation commits pushed: `370dd7b`, `a0622be`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal verified from GitHub after publication)
- New PR this round: NO; existing PR amended: YES
- Merge performed: NO

## Changes made

- Added canonical `packages/component-catalog/src/catalog-v1.json` with 22
  current components, catalog/schema versions, categories, slots, child
  limits, binding and authority classes, and complete bounded prop schemas.
- Added `tools/generate_component_catalog.py` and generated Python,
  TypeScript, and Puck artifacts. Its check mode detects exact artifact drift,
  Python/TypeScript semantic drift, Puck-source drift, and migration snapshot
  drift. Reviewed catalog-v1 SHA-256 is
  `8e95ba57bf1ef2a77df89189fa7da4231f1bcef34aff380de59a322bf5b8085a`.
- Repaired migration `060_001` to install the fixed reviewed catalog bytes
  without importing mutable runtime catalog code, and added recursive schema
  validation for closed objects, bounded arrays, required fields, scalar
  bounds, authority, and executable-value rejection.
- Added exact nested RichText child schemas and bounded closed item schemas for
  Statistics (`label`/`value`), Timeline (`title`/`description`), and FAQ
  (`question`/`answer`). Web now renders the existing structured RichText
  object as a meaningful block rather than an empty placeholder.
- Repaired the trusted database authority check to compare the union of old and
  new prop keys against catalog authority, denying direct runtime-role design
  prop additions, changes, and removals while preserving content PATCH merge,
  conflict, quota, audit, and COW behavior.
- Replaced open Agent catalog dictionaries with frozen explicit descriptor
  models and closed nested OpenAPI schemas. Agent create is independent from
  the legacy Editor request and rejects `order_key` with no side effects.
- Kept the Puck adapter and legacy Editor/Puck request behavior compatible,
  while deriving catalog types and validation from the canonical copy.
- Closed the CodeQL-reported URL-scheme gap by rejecting `vbscript:` in all
  bounded validation layers alongside `javascript:`, `data:`, and `file:`.
- Updated Render, route/OpenAPI and acceptance-contract evidence, and added
  focused tests for generator drift, nested semantics, runtime-role denial,
  structured rendering, and public Agent behavior.

## Files changed

The exact implementation diff from the required starting report head to
`a0622be` contains only these paths:

- `apps/web/src/renderer/components.tsx`
- `apps/web/tests/surface.test.mjs`
- `contracts/openapi/agent-v1.json`
- `oap/active`
- `oap/orders/078-b-repair-catalog-authority-and-render-parity.md`
- `packages/component-catalog/src/catalog-v1.json`
- `packages/component-catalog/src/index.js`
- `packages/component-catalog/src/index.ts`
- `packages/component-catalog/tests/index.test.ts`
- `packages/composition-schema/src/catalog-v1.json`
- `packages/composition-schema/src/puck-adapter.ts`
- `packages/composition-schema/tests/puck-adapter.test.ts`
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py`
- `services/backend/src/slaif_agent_site/agent_api/models.py`
- `services/backend/src/slaif_agent_site/content_model/component_catalog.py`
- `services/backend/src/slaif_agent_site/content_model/composition_models.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/060_001_agent_component_semantics.py`
- `services/backend/src/slaif_agent_site/render_api/projection.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/unit/test_agent_openapi.py`
- `services/backend/tests/unit/test_component_catalog.py`
- `tools/check_repository.py`
- `tools/compose/public_agent_acceptance.py`
- `tools/contracts/generate_agent_openapi.py`
- `tools/generate_component_catalog.py`

## Acceptance-criteria evidence

### Catalog authority and deterministic migration

- PASS — Canonical catalog-v1 JSON is the sole authored authority for the
  Python, TypeScript, Puck, Agent, Render, Web, and PostgreSQL definitions.
- PASS — Generator check detected a deliberate one-byte Python artifact drift
  in its focused test and passed exact generated/semantic checks on the final
  tree.
- PASS — Migration 060 contains a fixed reviewed catalog-v1 snapshot and hash;
  it does not import the mutable current runtime catalog.
- PASS — Agent catalog discovery equals the canonical catalog document;
  migration round-trip preserves the reviewed catalog and existing audit/data
  contract.

### Exact schemas and renderer parity

- PASS — Every current exposed prop has explicit type, requiredness, bounds,
  enum/reference metadata, authority/localization metadata where applicable,
  and bounded closed nested object/array semantics.
- PASS — Canonical RichText object
  `{"type":"paragraph","children":[{"text":"A trusted canonical page projection."}]}`
  is accepted by Python/PostgreSQL/Puck and renders non-empty Web meaning.
- PASS — Statistics, Timeline, and FAQ item arrays enforce one-to-64 items,
  required closed keys, and bounded string values.
- PASS — Unknown nested keys, raw HTML/CSS/JS, executable URLs and handlers,
  code/template/query markers, prototype keys, and the `javascript:`, `data:`,
  `file:`, and `vbscript:` schemes fail closed at the relevant boundaries.

### Database authority and public Agent contract

- PASS — Direct `slaif_agent_runtime` design-only prop addition is denied by
  PostgreSQL; props, row version, quota, audit, and COW operation state remain
  unchanged.
- PASS — Direct runtime-role content-only PATCH succeeds; valid partial merge,
  required props, optimistic conflict, quotas, idempotency, audit, and COW
  behavior remain covered.
- PASS — Agent descriptor models are frozen/explicit and generated OpenAPI
  sets `additionalProperties: false` at descriptor layers.
- PASS — Public Agent `order_key` receives HTTP 422 and creates no record,
  quota, audit row, or COW operation; semantic before/after anchors remain.
- PASS — Legacy Editor/Puck requests and composition tests remain compatible.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED — 44 packages checked.
- `uv run --frozen ruff check services/backend tools tests/repository`: PASSED.
- `uv run --frozen ruff format --check services/backend tools tests/repository`: PASSED — 280 files formatted.
- `uv run --frozen mypy`: PASSED — 262 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED — 531 passed, 1 warning, 22.87s.
- Focused catalog/API/DB/Render/legacy suite: PASSED — 40 passed, 1 warning, 98.70s before the one-line CodeQL correction.
- Post-CodeQL focused Python suite: PASSED — 11 passed.
- Post-CodeQL focused PostgreSQL migration/nested-schema suite: PASSED — 2 passed, 24.30s.
- `pnpm install --frozen-lockfile`: PASSED — all 10 workspace projects.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — workspace package, web, browser-worker, and contract tests green.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 58 tests.
- `python tools/check_repository.py`: PASSED — repository policy.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; 420 Markdown files scanned.
- `uv run --frozen python -m tools.generate_component_catalog --check`: PASSED.
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`: PASSED.
- `git diff --check`: PASSED.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues in 414 files.

The full backend integration suite was intentionally not rerun locally in
this round, as the activated order explicitly requires focused PostgreSQL
proofs and says not to substitute a multi-hour integration rerun; the normal
current-head PostgreSQL CI matrix provides the broad qualification.

## GitHub CI / required checks

Observed for final implementation head
`a0622be0588268b8cca6ac1878391e10412bb079` on PR #77; all current-head
checks were terminal and green before report publication:

- Analyze (actions): SUCCESS
- Analyze (javascript-typescript): SUCCESS
- Analyze (python): SUCCESS
- CodeQL: SUCCESS
- Compose and edge packaging: SUCCESS
- Dependency review: SUCCESS
- Detect supported languages: SUCCESS
- Foundation PostgreSQL 14: SUCCESS
- Foundation PostgreSQL 15: SUCCESS
- Foundation PostgreSQL 16: SUCCESS
- Foundation PostgreSQL 17: SUCCESS
- Foundation PostgreSQL 18: SUCCESS
- Markdown: SUCCESS
- Mermaid: SUCCESS
- Node contracts: SUCCESS
- Python 3.12 quality and package: SUCCESS
- Python 3.13 quality and package: SUCCESS
- Python 3.14 quality and package: SUCCESS
- Repository policy: SUCCESS
- Supply-chain evidence: SUCCESS

- Initial CodeQL failure on `370dd7b`: one high-severity alert for incomplete
  URL-scheme checking at `packages/composition-schema/src/puck-adapter.ts`.
- Remediation commit `a0622be` added `vbscript:` rejection; the final CodeQL
  and complete current-head matrix are green.
- All required current-head checks green at report drafting: YES.

## Local setup / dependencies

- Used the repository’s exact uv 0.12.5 environment, disposable local
  PostgreSQL, Node 24.14.1, and pnpm 11.22.0.
- No production dependency, lockfile, hosted service, image, or architecture
  exception was added.
- No production systems, credentials, capabilities, cookies, or private
  artifacts were accessed or printed.

## Documentation

- Updated the committed public Agent OpenAPI contract and durable catalog,
  generator, renderer, migration, and test evidence.
- No architecture, constitution, protocol, or historical report was edited.

## Safety and scope confirmations

- Unrelated files changed: NO; all paths support the activated `078-b` repair,
  governance transcript, or required verification evidence.
- Production secrets accessed: NO.
- Production systems accessed: NO.
- New dependency or hosted service: NO.
- Extra objective PR: NO.
- Coding-agent merge or auto-merge: NO.
- Activated order/active content edited by coding agent after selection: NO;
  strategy-authored bytes were committed unchanged.
- Report-publication commit changes only this report: YES.
- No post-report push or signal will be made except the exact FIFO response
  required by the communication protocol.

## Known limitations / blockers

- This report completes only the activated `078-b` repair round; numeric
  Objective 078 remains open and PR #77 remains `OPEN`.
- The five focused component concurrency cases and the full Compose/
  preview/browser/restart/isolation acceptance scenario explicitly remain
  later Objective 078 work and are not claimed here.
- Theme/global-region/design-system breadth, media bytes, MCP, freeze/review/
  promotion, and release claims remain outside this order.

## Completion condition

This coding round is complete when this report-only `SELF` commit is pushed as
the direct child of implementation SHA `a0622be`, verified as the sole changed
path and the remote PR #77 head, and the exact FIFO response `OK` is sent.
Objective 078/PR #77 is not accepted or merged by this agent; strategic review
and merge remain the sole acceptance authority.
