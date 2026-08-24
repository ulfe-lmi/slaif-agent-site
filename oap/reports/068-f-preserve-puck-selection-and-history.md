# OAP Coding-Agent Report — 068-f

## Work order

- Identifier: `068-f`
- Work-order file: `oap/orders/068-f-preserve-puck-selection-and-history.md`
- Numeric objective: `068`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

`RESULT=OK`

## Executive summary

Preserved selection continuity for the reusable Puck sibling reorder action.
Each accessible Move up/Move down operation now dispatches one history-recording
Puck `reorder` action followed by one destination `setUi` action with
`recordHistory: false`. The editor retains the moved stable component ID and
reselects that component's current selector after Puck data transitions,
including visible Undo and Redo restores. No controlled-data replacement or
Puck remount is used for reorder, selection, undo, or redo.

The strict public-NGINX browser contract proves visible add/select/move, moved
selection boundary state, visible Undo and Redo order/selection restoration,
final-only save, normalized stable-ID persistence after reload, and the exact
four-operation HUMAN envelope. The final accepted Compose smoke and all local
and implementation-head remote checks passed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#59](https://github.com/ulfe-lmi/slaif-agent-site/pull/59)
- PR state: `OPEN`, non-draft, mergeable
- Base/head: `main` / `oap/068-puck-editor`
- Starting remote 068-e report head: `149d387319eb395aa83f56bbe6ed66ca5237f4ef`
- Implementation head SHA: `e46c89ba52090eb4cd3ee353756d2390962d555c`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (verified after publication)
- Implementation commit pushed before report: `e46c89ba52090eb4cd3ee353756d2390962d555c`
- Report parent must equal implementation SHA: yes
- New PR this turn: no
- Existing PR amended: yes, PR #59 only
- Merge performed: NO

## Changes made

- Extended the normalized Puck reorder helper to return a typed ordered plan:
  one `reorder` action with `recordHistory: true`, followed by one `setUi`
  action targeting the exact destination selector with `recordHistory: false`.
- Kept root and nested-zone, boundary, stale-selector, no-selection, and
  multi-sibling fail-closed derivation behavior.
- Updated the Puck header override to retain the moved component's stable ID
  and reselect its current zone/index after data changes. Undo and Redo therefore
  select the same moved component at its restored boundary without a second
  history entry.
- Extended the strict browser contract to wait for Puck's debounced history
  entry after each visible add/move, then prove visible Undo/Redo continuity.
  Undo/Redo occur before the single final save and create no backend operation.
- Updated API/testing documentation to state selection continuity and visible
  undo/redo behavior.

## Files changed

- `apps/web/src/admin/composition-editor.tsx`
- `apps/web/tests/surface.test.mjs`
- `docs/API.md`
- `docs/TESTING.md`
- `oap/active` (exact strategic bytes: `068-f\n`)
- `oap/orders/068-f-preserve-puck-selection-and-history.md` (committed unchanged)
- `packages/composition-schema/src/puck-reorder.ts`
- `packages/composition-schema/tests/puck-adapter.test.ts`
- `tests/e2e/governance.spec.ts`

## Acceptance-criteria evidence

### Ordered public action plan

- PASS — focused tests assert the exact ordered tuple for both directions:
  `reorder` with source index, destination index, same destination zone, and
  `recordHistory: true`, then `setUi` with the destination `itemSelector` and
  `recordHistory: false`.
- PASS — root boundary, nested same-zone, middle-of-three, stale selection,
  missing selection, and unresolved-zone cases remain covered.
- PASS — the editor uses only public typed Puck dispatch actions; selection
  updates never replace controlled data or remount Puck.

### Move, selection, Undo, and Redo browser proof

- PASS — final `sudo -n tools/compose/smoke.sh slaif009aa` reported
  `compose-e2e: OK projects=8` and all setup/governance plus six stable-device
  projects passed.
- PASS — after the second visible add, the test waits for the add history entry;
  after Move down, it waits for Puck's 250 ms history debounce before Undo.
- PASS — Move down changes displayed order, leaves the moved first component
  selected at the last boundary (`Move up` enabled, `Move down` disabled).
- PASS — visible Undo restores displayed order and selection boundary
  (`Move up` disabled, `Move down` enabled).
- PASS — visible Redo restores moved order and selection boundary; only the
  final redone state is saved.
- PASS — public Editor GET and reload preserve the same normalized stable IDs,
  parent, slot, type, props, and order; exactly one component move is persisted.
- PASS — strict observer saw zero relevant CSP violations, console warnings or
  errors, page errors, failed requests, or server errors.

### Mutation, authority, and CSP invariants

- PASS — Compose postchecks report exactly one page create, two component adds,
  one component move, four successful HUMAN audit/idempotency/COW operations,
  and no undo/redo backend residue.
- PASS — accepted output reports the exact sequence
  `page-create,component-add,component-add,component-move` and count 4.
- PASS — editor CSP remains the accepted style-only exception; scripts remain
  nonce-bound/self-only with no `unsafe-inline` or `unsafe-eval`.
- PASS — normalized catalogue/trusted renderer remain the only component
  boundary; Puck IDs/actions do not enter normalized props.

## Local verification

- `uv lock --check`: PASSED
- `uv sync --frozen --all-groups`: PASSED
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 197 files
- `uv run --frozen mypy`: PASSED — 185 source files
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED
  — 411 tests in 14.52s
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 100
  tests in 402.82s
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — sdist/wheel
- `python -m compileall -q tools tests/repository`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 53
- `python tools/check_repository.py`: PASSED
- `python tools/check_mermaid.py`: PASSED — 16 diagrams, 208 Markdown files
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues, 202 files
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED — 37
- `pnpm --filter @slaif-agent-site/composition-schema test`: PASSED — 9 tests
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
- All ten frozen process `--check` commands: PASSED — each reported `CHECK_OK`
- `sudo -n tools/compose/smoke.sh slaif009aa`: PASSED — complete accepted-name
  browser, CSP, operation, recovery, role, secret, Apache/NGINX, and packaging
  smoke
- `git diff --check`: PASSED

### Intermediate failures and corrections

- One disposable Compose bootstrap attempt deadlocked in an owner transaction
  while login authentication/catalog locks waited; the disposable project was
  stopped and cleaned, then a fresh accepted-name run completed.
- Early browser attempts exposed the intended defect and test timing: the
  first implementation's history rewrite interfered with Undo, and a move made
  before Puck's 250 ms debounce caused Undo to remove the preceding visible add.
  The history rewrite was removed; the browser contract now waits for the add
  and reorder history entries. A separate run also had a transient governance
  membership-workflow failure and a control-readiness recovery timeout; both
  were followed by a complete passing accepted smoke.
- One focused surface assertion initially looked for `recordHistory: false` in
  the web file instead of the shared helper; it was corrected and the full Node
  gate passed. Temporary diagnostics/reporting changes were reverted.

## GitHub CI / required checks

Observed for implementation head `e46c89ba52090eb4cd3ee353756d2390962d555c`;
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

Used Node 24.14.1/pnpm 11.22.0, uv 0.12.5, disposable PostgreSQL fixtures,
Playwright browsers, and disposable local Compose services. No production
dependency or lockfile change was introduced. No hosted service, external
account, production credential, or production system was accessed.

## Documentation

Updated `docs/API.md` and `docs/TESTING.md` for moved-component selection
continuity, visible Undo/Redo, history behavior, and final normalized evidence.
No architecture, constitution, or protocol document was edited.

## Safety and scope confirmations

- Unrelated files changed: no; all paths are within 068-f scope.
- Production secrets accessed: no.
- Production systems/data accessed: no.
- Required tests skipped/not run: no for the claimed local and CI set.
- Scope deviation: no.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated order/active edited: NO; exact strategic bytes were committed.
- Report commit changes only this report: yes, verified before publication.

## Known limitations / blockers

- Puck 0.20.2 history recording is debounced; the strict browser proof waits
  for that documented runtime behavior before invoking visible Undo/Redo.
- Full Puck phone ergonomics remain the existing architecture's best-effort
  limitation; the required device claims for this round passed.
- PR #59 remains open and unmerged; this report is not acceptance or release
  authorization.

## Recommended strategic follow-up

Independently inspect the exact PR diff, ordered action/history proof, remote
report parent/blob/head, and current report-head checks. Strategy alone decides
whether to accept, request another continuation, merge, or otherwise dispose of
PR #59.
