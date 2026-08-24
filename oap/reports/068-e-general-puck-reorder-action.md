# OAP Coding-Agent Report — 068-e

## Work order

- Identifier: `068-e`
- Work-order file: `oap/orders/068-e-general-puck-reorder-action.md`
- Numeric objective: `068`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

`RESULT=OK`

## Executive summary

Replaced the test-shaped first-root-pair reorder control with reusable accessible
`Move up` and `Move down` sibling controls implemented through Puck 0.20.2's
public `overrides.headerActions` and typed `createUsePuck` integration. The
controls derive the selected component's exact Puck selector, sibling zone, and
index, then dispatch Puck's same-zone `reorder` action with history recording.
They fail closed without a resolvable selection, zone, boundary move, or drag
permission.

The strict public-NGINX browser contract visibly added both Sections, selected
the first rendered component, verified `Move up` disabled and `Move down`
enabled, proved the displayed Puck order changed before save, saved visibly,
and verified stable normalized IDs, parent/slot/type/props/order after public
API reload. The accepted Compose smoke also passed the exact four-operation
HUMAN audit/idempotency/COW envelope and all recovery, authority, CSP, device,
and packaging checks.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#59](https://github.com/ulfe-lmi/slaif-agent-site/pull/59)
- PR state: `OPEN`, non-draft, mergeable
- Base/head: `main` / `oap/068-puck-editor`
- Starting remote 068-d report head: `d8c11fe7ca7e196e818c01d4df9f45694201232a`
- Implementation head SHA: `ae6505888fae78923164e823c7214f4ae17e62a2`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (verified after publication)
- Implementation commit pushed before report: `ae6505888fae78923164e823c7214f4ae17e62a2`
- Report parent must equal implementation SHA: yes
- New PR this turn: no
- Existing PR amended: yes, PR #59 only
- Merge performed: NO

## Changes made

- Added `derivePuckSiblingReorderActions`, covering root and normalized nested
  sibling zones, middle-item moves, first/last boundaries, stale selectors,
  missing selection, and unresolved zones.
- Added an exact public Puck action shape:
  `type: "reorder"`, selected `sourceIndex`, adjacent
  `destinationIndex`, exact `destinationZone`, and `recordHistory: true`.
- Added a modern Puck `headerActions` override using `createUsePuck`; it reads
  the selected item and selector from Puck, checks Puck drag permission, and
  dispatches only derived same-zone actions. Puck's ordinary header children,
  save/publish control, undo/redo, selection, and default permissions remain.
- Removed `moveFirstRootComponent`, `renderHeaderActions`, the
  `puck-action:move-first-down` coupling, and direct controlled-data replacement
  used for reorder. Server refresh retains the existing remount needed to adopt
  normalized IDs.
- Added focused composition-schema tests for no selection, stale selection,
  root boundaries, a middle item among three siblings, exact action/history
  payloads, and a nested sibling zone. The composition package test script now
  runs all its focused test files.
- Updated the strict E2E to select through the rendered Puck UI, invoke the
  visible general control, inspect Puck's native component order before save,
  and verify the persisted normalized round trip after reload.
- Updated API/testing documentation to describe the actual general interaction.

## Files changed

- `apps/web/app/styles.css`
- `apps/web/src/admin/composition-editor.tsx`
- `apps/web/tests/surface.test.mjs`
- `docs/API.md`
- `docs/TESTING.md`
- `oap/active` (committed unchanged strategic bytes: `068-e\n`)
- `oap/orders/068-e-general-puck-reorder-action.md` (committed unchanged)
- `packages/composition-schema/package.json`
- `packages/composition-schema/src/index.ts`
- `packages/composition-schema/src/puck-reorder.ts`
- `packages/composition-schema/tests/puck-adapter.test.ts`
- `tests/e2e/governance.spec.ts`

## Acceptance-criteria evidence

### General Puck sibling interaction

- PASS — `createUsePuck` reads the selected Puck item and
  `getSelectorForId` resolves the exact current zone/index.
- PASS — for a selected first root component, the dispatched Move down trace
  is `{ type: "reorder", sourceIndex: 0, destinationIndex: 1,
  destinationZone: "root:default-zone", recordHistory: true }`.
- PASS — Move up is disabled at index 0; Move down is disabled at the last
  sibling; both actions are derived for a middle item among three siblings.
- PASS — nested normalized zone proof uses the exact `root:default` zone and
  `{ sourceIndex: 1, destinationIndex: 0, destinationZone: "root:default",
  recordHistory: true }`.
- PASS — no selection, stale index, and unknown zone return no action; no
  component or zone is chosen by the helper.

### Strict browser/editor proof

- PASS — final `sudo -n tools/compose/smoke.sh slaif009aa` completed with
  `compose-e2e: OK projects=8`, including setup, governance, desktop
  Chromium/Firefox/WebKit, tablet, mobile Chromium/WebKit.
- PASS — the governance Puck contract added both Sections through the visible
  drawer, selected the first rendered component, checked the accessible
  boundary states, invoked Move down, and observed the native Puck component
  order change before save.
- PASS — after visible save and public same-origin API reload, the same first
  normalized stable ID was at order 1, the second at order 0, with parent, slot,
  type, props, and order preserved; reload returned identical persisted data.
- PASS — strict observer reported no CSP violations, console warnings/errors,
  page errors, failed requests, or server errors.

### Mutation, authority, and CSP invariants

- PASS — Compose postchecks reported exactly one page create, two component
  adds, and one component move; exactly four successful HUMAN audit,
  idempotency, and COW operations; no residue or extra move.
- PASS — accepted Compose output retained `human-editor-envelope: OK`, exact
  sequence `page-create,component-add,component-add,component-move`, and count 4.
- PASS — editor CSP remained the accepted style-only exception; scripts stayed
  nonce-bound/self-only with no `unsafe-inline` or `unsafe-eval`.
- PASS — normalized catalogue/trusted renderer remain the component boundary;
  Puck action metadata and IDs are not persisted as normalized props.

## Local verification

- `uv lock --check`: PASSED
- `uv sync --frozen --all-groups`: PASSED
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 197 files
- `uv run --frozen mypy`: PASSED — 185 source files
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED
  — 411 tests in 14.38s
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 100
  tests in 410.80s
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — sdist and
  wheel
- `python -m compileall -q tools tests/repository`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 53
- `python tools/check_repository.py`: PASSED
- `python tools/check_mermaid.py`: PASSED — 16 diagrams, 206 Markdown files
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues, 200 files
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED — 37
- `pnpm --filter @slaif-agent-site/composition-schema test`: PASSED — 2 files,
  9 tests
- `pnpm --filter @slaif-agent-site/web test`: PASSED — 9 tests
- `pnpm --filter @slaif-agent-site/web lint`: PASSED
- `pnpm --filter @slaif-agent-site/web typecheck`: PASSED
- `pnpm --filter @slaif-agent-site/web build`: PASSED
- `node --version`: PASSED — v24.14.1
- `pnpm --version`: PASSED — 11.22.0
- `pnpm install --frozen-lockfile`: PASSED
- `pnpm lint`: PASSED
- `pnpm format:check`: PASSED
- `pnpm typecheck`: PASSED
- `pnpm test`: PASSED — build, recursive package tests, and contracts
- `pnpm build`: PASSED
- `pnpm licenses list --json`: PASSED
- `uv run --frozen python -m slaif_agent_site.{control_api,editor_api,agent_api,render_api,mcp_adapter,media_service,review_worker,scheduler,media_gc,bootstrap} --check`: PASSED — all ten reported `CHECK_OK`
- `sh -n tools/compose/smoke.sh`: PASSED
- `sudo -n tools/compose/smoke.sh slaif009aa`: PASSED — full accepted-name
  Compose/browser/recovery/packaging smoke
- `git diff --check`: PASSED

### Intermediate browser attempts

Four intermediate strict Compose attempts failed before the final accepted run
while correcting test observation locators: an aggregate native Puck locator
count, a visibility assertion on Puck's overlay ID, an overlay-node count, and
an `evaluateAll` closure that omitted the test argument. These were test
contract failures before persistence/operation assertions; the final accepted
run passed the complete contract and all postchecks. The temporary diagnostic
reporter change was reverted and is not in the implementation diff.

## GitHub CI / required checks

Observed for implementation head `ae6505888fae78923164e823c7214f4ae17e62a2`;
all final states were `SUCCESS`:

- Repository policy
- Detect supported languages
- Node contracts
- Analyze (actions)
- Analyze (python)
- Analyze (javascript-typescript)
- Python 3.12 quality and package
- Python 3.13 quality and package
- Python 3.14 quality and package
- Foundation PostgreSQL 14
- Foundation PostgreSQL 15
- Foundation PostgreSQL 16
- Foundation PostgreSQL 17
- Foundation PostgreSQL 18
- Compose and edge packaging
- Supply-chain evidence
- Markdown
- Mermaid
- Dependency review
- CodeQL

All required green at report drafting: yes. No required check was missing,
pending, failed, or cancelled. The report-only commit may trigger fresh checks;
strategy independently verifies that report-head state.

## Local setup / dependencies

Used the repository's existing Node 24.14.1/pnpm 11.22.0, uv 0.12.5 project
environment, disposable PostgreSQL integration fixtures, Playwright browsers,
and disposable local Compose services. No production dependency or lockfile
change was introduced. The only package-script change makes the existing
composition-schema test command include its focused test files. No hosted
service, external account, or production credential was used.

## Documentation

Updated `docs/API.md` and `docs/TESTING.md` to describe selected-component
accessible sibling reorder through Puck's reorder/history action, exact zones,
boundary behavior, and normalized persistence evidence. No architecture,
constitution, or protocol document was edited.

## Safety and scope confirmations

- Unrelated files changed: no; all implementation paths are within 068-e scope.
- Production secrets accessed: no.
- Production systems/data accessed: no.
- Required tests skipped/not run: no for the claimed local and CI set.
- Scope deviation: no; native drag was not claimed because the accepted
  accessible Puck action path is the reliable bounded interaction.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated order/active edited: NO; exact strategic bytes were committed.
- Report commit changes only this report: yes, verified before publication.

## Known limitations / blockers

- The implementation intentionally uses the accessible Puck action controls,
  not a claim of native pointer/keyboard drag reliability. Puck 0.20.2's
  public action/history path is the tested interaction.
- Full Puck phone ergonomics remain governed by the repository's existing
  best-effort architecture limitation; the required browser device claims
  passed for this round.
- PR #59 remains open and unmerged; this report is not acceptance or release
  authorization.

## Recommended strategic follow-up

Review the exact remote PR diff, report parent, report-head checks, and the
accessible Puck action evidence independently. Strategy alone decides whether
to accept, request another same-PR continuation, merge, or otherwise dispose of
PR #59.
