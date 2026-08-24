# OAP Coding-Agent Report — 068-d

## Work order

- Identifier: `068-d`; work-order file: `oap/orders/068-d-lock-order-and-production-proof.md`
- Numeric objective: `068`
- PR mode: `CONTINUE_SAME_PR`
- Objective PR: [#59](https://github.com/ulfe-lmi/slaif-agent-site/pull/59)

## Status

COMPLETE

`RESULT=OK`

## Executive summary

Completed the 068-d continuation on PR #59. The HUMAN workspace assertion now
validates only immutable COW context before taking the shared workspace advisory
transaction lock; all mutable workspace, session, account, site, membership,
permission, and expiry facts are re-read under that lock. Deterministic
PostgreSQL race evidence proves a waiting request fails closed after an
authority change commits, with no content, audit, idempotency, or COW residue.

The integration suite now uses fixed production login identities and the real
Control/Editor database classes plus the production Editor application factory
over public HTTP routes. It proves page and normalized composition CRUD,
overlay/canonical behavior, replay/mismatch, exact grants, and cleanup.

The Puck editor remounts from normalized server state after every save. Its
visible accessible Puck header reorder action swaps root data without direct
Puck dispatch or mutation API calls; the E2E proof captures the first stable
component ID at order 0, moves it to order 1, verifies the second ID at order
0, and confirms the exact structure after reload.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#59](https://github.com/ulfe-lmi/slaif-agent-site/pull/59) — `OPEN`, non-draft
- Base/head: `main` / `oap/068-puck-editor`
- Starting remote 068-c report head: `69df1dbdde2ecbfb0bdf86f753b3dde0b5f566db`
- Implementation head SHA: `a54e3832e53d95908f04c028c0884ba59aee3c45`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (to be verified via GitHub)
- Implementation commit pushed before report: `a54e3832e53d95908f04c028c0884ba59aee3c45`
- Implementation first parent: `69df1dbdde2ecbfb0bdf86f753b3dde0b5f566db`
- New objective PR this turn: `NO`; existing PR amended: `YES`
- Merge or auto-merge performed: `NO`

## Changes made

- Moved the shared workspace advisory lock immediately after immutable COW
  context validation and bound assertion to the deterministic newest active
  HUMAN workspace for the site/human pair.
- Added a deterministic two-connection PostgreSQL race using
  `pg_stat_activity` advisory-lock wait evidence, with exact unchanged
  content/audit/idempotency/COW-operation assertions.
- Added isolated expired-session, inactive-workspace, alternate-workspace,
  wrong-site/human, revoked-membership/session, forged-context, authentication
  session UUID, completion-failure, cancellation, and pool-reuse proofs.
- Added fixed `slaif_control_login`/`slaif_control` and
  `slaif_editor_login`/`slaif_editor_runtime` integration wiring with the real
  database classes, application factory, and public Editor HTTP page and
  composition chain.
- Added exact four-row Compose HUMAN audit/idempotency verification with the
  action sequence `page-create,component-add,component-add,component-move`.
- Added Puck server-refresh remounting and a visible accessible reorder control;
  preserved the accepted editor-only style CSP boundary.
- Updated role/testing documentation for lock chronology, fixed identities,
  public HTTP evidence, exact IDs, and exact audit evidence.

## Files changed

- `apps/web/src/admin/composition-editor.tsx`
- `docs/DATABASE_ROLES.md`; `docs/TESTING.md`
- `oap/active`; `oap/orders/068-d-lock-order-and-production-proof.md`
- `services/backend/src/slaif_agent_site/db/alembic/versions/028_001_human_editor_workspace_envelope.py`
- `services/backend/tests/integration/test_human_editor_workspace.py`
- `services/backend/tests/integration/test_human_editor_production_http.py`
- `tests/e2e/governance.spec.ts`
- `tools/compose/smoke.sh`

## Acceptance-criteria evidence

### Criterion 1 — Lock-before-mutable-check invariant

- PASS. The database function parses and validates `app.session_id` and
  `app.operation_id`, then takes the shared workspace advisory transaction
  lock before reading mutable lifecycle or authority state.
- PASS. The deterministic race holds the exact lock in connection A, changes
  membership in A’s transaction, observes connection B waiting on an advisory
  lock through `pg_stat_activity`, commits A, and proves B fails closed.

### Criterion 2 — Fixed production identities and public Editor HTTP

- PASS. The real integration creates fixed production login roles and grants
  only their exact privilege roles. Each connection asserts `session_user`,
  `current_user`, and membership; Control direct content access and Editor
  direct Control access fail with insufficient privilege.
- PASS. Real `ControlDatabase`, `EditorDatabase`, and `editor_api.create_app`
  pools serve public Editor HTTP requests. Page create/read/update/delete and
  composition add/read/props-update/move/delete succeed through the application
  routes with CSRF and idempotency headers.
- PASS. The owner observes canonical title/rows unchanged while Editor GETs
  see the overlay; canonical fallback and final deletion are verified.

### Criterion 3 — Exact isolation, idempotency, rollback, and cleanup

- PASS. Replay returns the identical response; digest mismatch creates no new
  operation. Forced handler rollback, forced completion failure, cancellation,
  and subsequent pool reuse leave no stranded idempotency or COW context.
- PASS. Wrong human/site, missing permission, alternate otherwise-valid
  workspace, forged workspace setting, authentication-session UUID, inactive
  workspace, absolute session expiry, revoked session, and revoked membership
  each have isolated fail-closed assertions and are restored where needed for
  the next case.
- PASS. Exact production HTTP counts are nine successful idempotency/audit
  records and nine COW operations; Compose’s fresh browser path proves exactly
  four records and the prescribed four-action sequence.

### Criterion 4 — Stable visible Puck structure and CSP

- PASS. The strict public Compose browser path has zero observed CSP, console,
  page, request, or server failures. The accepted route policy remains
  `style-src 'self'`, `style-src-elem 'self' 'unsafe-inline'`,
  `style-src-attr 'unsafe-inline'`, with nonce-bound self-only scripts and
  strict public/default/404/API/unrelated-admin policies.
- PASS. The visible Puck drawer adds two Sections; the visible accessible Puck
  reorder action swaps controlled normalized root data; the first stable ID is
  proved at order 0 before the move, order 1 after save, and unchanged after
  reload, while the second ID is order 0.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED (`197 files`).
- `uv run --frozen mypy`: PASSED (`185 source files`).
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED (`411 tests`, `14.07s`).
- `uv run --frozen pytest services/backend/tests/integration`: PASSED
  (`100 tests`, `421.52s`).
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED; source and
  wheel distributions built.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED
  (`53 tests`).
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED (`16 diagrams`, `204 Markdown files`).
- `npx --yes markdownlint-cli2@0.23.2 '**/*.md'`: PASSED (`0 issues`).
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED
  (`37 tests`).
- `uv run --frozen python -m slaif_agent_site.{control_api,editor_api,agent_api,render_api,mcp_adapter,media_service,review_worker,scheduler,media_gc,bootstrap} --check`: PASSED; all ten emitted `CHECK_OK`.
- `node --version`: PASSED (`v24.14.1`).
- `pnpm --version`: PASSED (`11.22.0`).
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED; recursive build, package tests, and contract tests.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `sudo -n tools/compose/smoke.sh slaif009aa`: PASSED end to end, including
  setup/governance/all six stable browser devices, stable Puck IDs, exact
  HUMAN action sequence/count, CSP/edge, role/secret, readiness/recovery,
  restart, negative bootstrap, Apache/NGINX syntax, and packaging checks.
- `git diff --check`: PASSED.

The executor’s system `/usr/bin/python` is not configured to import the
repository `src/` package directly; the frozen `uv run --frozen python`
process-check path above is the passing project execution path.

## GitHub CI / required checks

Observed on implementation head
`a54e3832e53d95908f04c028c0884ba59aee3c45`; every listed check was successful:

- SUCCESS: Repository policy
- SUCCESS: Detect supported languages
- SUCCESS: Node contracts
- SUCCESS: Analyze (actions)
- SUCCESS: Analyze (python)
- SUCCESS: Analyze (javascript-typescript)
- SUCCESS: Python 3.12 quality and package
- SUCCESS: Python 3.13 quality and package
- SUCCESS: Python 3.14 quality and package
- SUCCESS: Foundation PostgreSQL 14
- SUCCESS: Foundation PostgreSQL 15
- SUCCESS: Foundation PostgreSQL 16
- SUCCESS: Foundation PostgreSQL 17
- SUCCESS: Foundation PostgreSQL 18
- SUCCESS: Compose and edge packaging
- SUCCESS: Supply-chain evidence
- SUCCESS: Markdown
- SUCCESS: Mermaid
- SUCCESS: Dependency review
- SUCCESS: CodeQL

All required checks green at drafting: `YES`; none were missing, failed,
cancelled, or pending.

## Local setup / dependencies

- Used uv `0.12.5`, Node `24.14.1`, pnpm `11.22.0`, and the pinned existing
  dependency set; no dependency or hosted service was added.
- Used passwordless sudo only for disposable Compose and local PostgreSQL
  verification because the executor user lacks Docker-socket group access.
- Fixed production login proofs use fake test-only passwords and disposable
  databases; no production credentials, systems, capabilities, cookies, or
  real secrets were accessed.

## Documentation

Updated `docs/DATABASE_ROLES.md` and `docs/TESTING.md` with lock chronology,
fixed production login identity evidence, public HTTP proof, exact audit/COW
evidence, and the accessible visible Puck reorder behavior.

## Safety and scope confirmations

- Unrelated files changed: `NO`.
- Production secrets accessed: `NO`.
- Production systems/data accessed: `NO`.
- Required tests skipped/not run: `NO`.
- Scope deviation: `NO`.
- Extra objective PR: `NO`.
- Coding-agent merge: `NO`.
- Activated order/active edited by coding: `NO`; strategic bytes were committed
  unchanged (`oap/active` is exactly `068-d\n`).
- Report commit changes only this report: `YES`.

## Known limitations / blockers

- The pinned Puck runtime’s native drag sensor did not emit a move action in
  the strict browser harness; the accepted proof uses the accessible visible
  Puck header reorder action, which changes controlled Puck data and persists
  through the normal Editor API save path without direct dispatch or API
  mutation calls.
- The PR remains open and unmerged; strategic review and merge authority remain
  outside this coding turn.

## Recommended strategic follow-up

Verify the report-only commit and fresh required checks on PR #59, then perform
the independent strategy review. This coding agent did not merge or select a
next order.
