# OAP Coding-Agent Report — 068-g

## Work order

- Identifier: `068-g`
- Work-order file: `oap/orders/068-g-release-explicit-puck-selection.md`
- Numeric objective: `068`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

`RESULT=OK`

## Executive summary

Corrected the remaining Puck selection-lifecycle defect without changing the
accepted reorder/history action plan. The editor now tracks the last Puck data
reference and releases moved-component continuity when the selector changes to
another component while data is unchanged, which is an explicit human
selection. Data/history transitions continue to reselect the moved stable ID;
later moves can bind continuity to a new component.

The strict public-NGINX browser contract visibly moved, undid, and redid the
composition, then explicitly selected the other stable Puck component before
save. Its selection remained stable and its inverse boundary controls were
correct. Final normalized persistence and the exact four-operation HUMAN
envelope passed, as did the complete accepted Compose smoke and all fresh
implementation-head GitHub checks.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#59](https://github.com/ulfe-lmi/slaif-agent-site/pull/59)
- PR state: `OPEN`, non-draft, mergeable
- Base/head: `main` / `oap/068-puck-editor`
- Starting remote 068-f report head: `42ef4ace4a0f17fd939f6f2599d2663c701ce953`
- Implementation head SHA: `a64d173dde17e5b156c6b2ea47ccaf3285796e34`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (verified after publication)
- Implementation commit pushed before report: `a64d173dde17e5b156c6b2ea47ccaf3285796e34`
- Report parent must equal implementation SHA: yes
- New PR this turn: no
- Existing PR amended: yes, PR #59 only
- Merge performed: NO

## Changes made

- Added and tested `shouldReleasePuckMovedSelection`, which releases the
  moved-ID continuity only when a different/no selected component is observed
  without a data transition.
- Wired the existing Puck public `getItemBySelector`/`getSelectorForId` path to
  distinguish deliberate selection from reorder, Undo, and Redo transitions.
- Preserved the exact 068-f public action sequence: one `reorder` with
  `recordHistory: true`, followed by destination `setUi` with
  `recordHistory: false`.
- Extended the real browser contract to select the other component by its
  stable native Puck ID after Redo and verify inverse boundary controls before
  final save.
- Updated API/testing documentation to state that deliberate human selection
  supersedes temporary moved-component continuity.

## Files changed

- `apps/web/src/admin/composition-editor.tsx`
- `docs/API.md`
- `docs/TESTING.md`
- `oap/active` (exact strategic bytes: `068-g\n`)
- `oap/orders/068-g-release-explicit-puck-selection.md` (committed unchanged)
- `packages/composition-schema/src/puck-reorder.ts`
- `packages/composition-schema/tests/puck-adapter.test.ts`
- `tests/e2e/governance.spec.ts`

## Acceptance-criteria evidence

### Lifecycle and action plan

- PASS — focused helper tests cover: moved ID plus different explicit ID with
  unchanged data releases continuity; moved ID remains when selected; data
  transition preserves continuity; missing moved ID fails closed.
- PASS — prior action-plan tests remain green for root/nested zones, up/down,
  first/last/middle boundaries, stale/no selection, and exact ordered public
  actions.
- PASS — no `setHistories`, private Puck store mutation, direct controlled-data
  replacement, reorder remount, or temporary diagnostic remains.

### Strict browser path

- PASS — final `sudo -n tools/compose/smoke.sh slaif009aa` reported
  `compose-e2e: OK projects=8`, including setup, governance, three desktop
  engines, tablet, and two mobile engines.
- PASS — visible add, Move down, settled history, Undo, Redo, final-only save,
  public GET, reload, and normalized stable-ID/order evidence all passed.
- PASS — after Redo, the test explicitly selected the other component through
  the stable native Puck component ID. Its selection remained stable after
  effects settled; Move up was disabled and Move down enabled, inverse to the
  previously moved last component.
- PASS — the final redone order remained unchanged by explicit selection and
  saved with the same stable IDs, parent, slot, type, props, and order.
- PASS — strict observer reported zero relevant CSP violations, console/page
  errors, failed requests, and server errors.

### Backend, authority, and security invariants

- PASS — final Compose output retained exactly one page create, two component
  adds, one component move, and four successful HUMAN audit/idempotency/COW
  records with no undo/redo backend residue.
- PASS — output retained exact sequence
  `page-create,component-add,component-add,component-move` and count 4.
- PASS — editor-only CSP and strict public/API/script policies are unchanged.
- PASS — no backend, database, migration, role, privilege, dependency,
  lockfile, secret, deployment, or trust-boundary path changed.

## Local verification

- `pnpm --filter @slaif-agent-site/composition-schema test`: PASSED — 10 tests
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
- `pnpm test`: PASSED — recursive build/tests/contracts
- `pnpm build`: PASSED
- `pnpm licenses list --json`: PASSED
- `python -m compileall -q tools tests/repository`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 53
- `python tools/check_repository.py`: PASSED
- `python tools/check_mermaid.py`: PASSED — 16 diagrams, 210 Markdown files
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues, 204 files
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED — 37
- All ten frozen process `--check` commands: PASSED — all `CHECK_OK`
- `sudo -n tools/compose/smoke.sh slaif009aa`: PASSED — complete browser,
  operation, recovery, CSP, role, secret, Apache/NGINX, and packaging smoke
- `git diff --check`: PASSED

### Reused accepted backend evidence

The order explicitly authorizes reuse of complete accepted 068-f backend and
integration evidence because no backend/Python path changed. The accepted
068-f evidence remains: `uv lock --check`, frozen sync, Ruff, mypy, 411 unit/
repository tests, 100 PostgreSQL integration tests, package build, and process
checks all passed. No Python verification claim was silently presented as a
new 068-g execution.

### Intermediate failures and corrections

- The first frozen Node run found one formatter-only failure in the new helper;
  Prettier corrected it and the rerun passed.
- One enhanced Compose attempt reached all prior browser checks but failed on
  an exact-count assertion for a Puck native overlay ID. The test was narrowed
  to the first attached native overlay for the stable ID; the final accepted
  smoke passed. No product behavior or operation evidence was weakened.

## GitHub CI / required checks

Observed for implementation head `a64d173dde17e5b156c6b2ea47ccaf3285796e34`;
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
Playwright browsers, and local Compose services. No production dependency or
lockfile change, hosted service, external account, production credential, or
production-system access was introduced.

## Documentation

Updated `docs/API.md` and `docs/TESTING.md` to state that moved-component
continuity is limited to the associated data/history transition and that a
later deliberate human selection always takes precedence. No architecture,
constitution, or protocol document was edited.

## Safety and scope confirmations

- Unrelated files changed: no; all paths are within 068-g scope.
- Production secrets accessed: no.
- Production systems/data accessed: no.
- Required tests skipped/not run: no for the claimed set; accepted backend
  evidence was explicitly reused as authorized by the order.
- Scope deviation: no.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated order/active edited: NO; exact strategic bytes were committed.
- Report commit changes only this report: yes, verified before publication.

## Known limitations / blockers

- Puck 0.20.2 history recording is debounced; the strict browser contract
  waits for the documented entry before visible Undo/Redo.
- Full Puck phone ergonomics remain the existing best-effort architecture
  limitation; required device claims passed.
- PR #59 remains open and unmerged; this report is not acceptance or release
  authorization.

## Recommended strategic follow-up

Independently inspect the exact PR diff, lifecycle helper/action proof, stable
explicit-selection browser evidence, report parent/blob/head, and report-head
checks. Strategy alone decides whether to accept, request another continuation,
merge, or otherwise dispose of PR #59.
