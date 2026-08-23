# OAP Coding-Agent Report — 067-b

## Work order

- Identifier: `067-b`; work-order file: `oap/orders/067-b-agent-mutation-review-remediation.md`
- Numeric objective: `067`
- PR mode: `AMENDED_EXISTING_PR`
- Existing objective PR: #58 on `oap/067-agent-mutations`

## Status

COMPLETE

`RESULT=OK`

## Executive summary

Remediated the strategic review findings for 067-a without broadening the
five-route Agent mutation surface. Revision `026_001` now places a guarded
owner-defined layer over the five Agent content wrappers. It resolves the
workspace from the trusted COW `app.session_id`, requires valid UUID-valued
session and operation context plus an active, unexpired workspace, and rejects
any supplied site UUID that differs from the workspace site before delegation.

The real PostgreSQL integration evidence now covers site-A/site-B resource
rejection, missing scopes, malformed requests, wrong relationships, direct
runtime-role wrapper misuse, replay operation-set stability, mismatch residue
stability, canonical isolation, audit/idempotency state, cancellation, and
pool cleanup.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#58](https://github.com/ulfe-lmi/slaif-agent-site/pull/58) — `OPEN`
- Base/head: `main` / `oap/067-agent-mutations`
- Starting remote report-head SHA: `2bc1213a31f179bfaaf4231b837edbbb19cba76a`
- Implementation head SHA: `d8b43f3b755ba7a789c7666dc6484d0e1b800b76`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commits pushed before report: `d8b43f3b755ba7a789c7666dc6484d0e1b800b76`
- Report parent will equal the implementation SHA above.
- PR was observed `MERGEABLE` with `CLEAN` merge state; coding agent did not merge.
- No second objective PR exists.

## Changes made

- Added migration `026_001_agent_site_binding`.
- Renamed the prior wrapper implementations behind revoked
  `slaif_agent_unchecked_*` names and installed guarded wrappers with the
  original public signatures and grants.
- Added `control.slaif_agent_require_cow_site(uuid)` with fixed
  `search_path=pg_catalog`; it validates `app.session_id`, `app.operation_id`,
  active workspace lifecycle/expiry, and workspace/site binding.
- Mapped all PostgreSQL `P0002` semantic not-found failures through the stable
  `RESOURCE_NOT_FOUND` Agent envelope while retaining conflict and unavailable
  behavior.
- Extended real integration tests with site-B canonical fixtures, limited
  capabilities, malformed HTTP requests, direct wrapper calls, and durable /
  overlay residue assertions.
- Updated migration-head/package fixtures and role-boundary documentation.
- Preserved all five 067-a routes, capability-derived identity, idempotency,
  audit, COW, canonical, reviewer, and lifecycle boundaries.

## Files changed

- `services/backend/src/slaif_agent_site/db/alembic/versions/026_001_agent_site_binding.py`
- `services/backend/src/slaif_agent_site/content_model/service.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_control_database_integration.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `docs/DATABASE_ROLES.md`
- Exact activated `oap/active` and `oap/orders/067-b-agent-mutation-review-remediation.md` transcript bytes.

Earlier 067-a implementation, report, and all prior transcript artifacts remain
unchanged and reachable in the same PR.

## Acceptance-criteria evidence

### Criterion 1 — Existing five-route surface preserved

- PASS. The full route integration test still creates a type, field, item, page,
  and composition node through the public capability-authenticated HTTP API;
  each returns `201`, a semantic record, and one durable UUID operation ID.
  No route was added or removed in this remediation.

### Criterion 2 — Database-enforced workspace/site binding

- PASS. A direct `slaif_agent_runtime` connection opens a valid COW session
  for site A and invokes an Agent wrapper with site B. PostgreSQL rejects the
  call through the guarded wrapper before the unchecked semantic function is
  reached. The reviewer sees no COW operation and control/audit state remains
  empty. The guard performs its own fully qualified `control.workspace` lookup;
  Python caller behavior is not the sole enforcement point.

### Criterion 3 — Wrong-site/resources and malformed requests

- PASS. A site-A capability using canonical type/page/parent resources from
  site B receives stable `404 RESOURCE_NOT_FOUND` responses for field, item,
  page-parent, and component operations. A body/path type mismatch is rejected
  with 404; extra fields and malformed UUID paths return `422 VALIDATION_ERROR`.
  Failed requests leave no COW operation, idempotency row, audit row, or
  canonical mutation.

### Criterion 4 — Scope enforcement

- PASS. A capability with only `site:read` receives `403 AUTHORIZATION_DENIED`
  for each of the five relevant create routes. Scope rejection occurs before
  COW/idempotency execution and leaves no durable residue.

### Criterion 5 — Replay and mismatch stability

- PASS. Replay returns byte-equivalent stored response and operation UUID while
  the reviewer operation set remains exactly the original set. Changed digest
  returns `409 IDEMPOTENCY_MISMATCH`; operation set, overlay record, canonical
  base, audit count, and idempotency count remain unchanged.

### Criterion 6 — Existing security/lifecycle boundaries retained

- PASS. Existing tests still prove Agent cannot read content base/change
  tables, invoke reviewer/control lifecycle functions, or invoke a wrapper
  without COW context. No freeze, accept, discard, publish, identity,
  capability-management, arbitrary SQL/DDL, infrastructure, or second PR path
  was added.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED.
- `uv run --frozen mypy`: PASSED (`178` source files).
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`: PASSED (`411 passed, 26 subtests`).
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED (`98 passed`).
- `uv build --out-dir /tmp/slaif-agent-site-distributions-067b`: PASSED (wheel and sdist).
- `python -m compileall -q tools tests/repository services/backend/src/slaif_agent_site`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED (`53 tests`).
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED (`16 diagrams`, `197 Markdown files`).
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED (0 issues).
- `npx --yes markdownlint-cli2@0.23.2 --no-globs oap/orders/067-b-agent-mutation-review-remediation.md`: PASSED.
- `node --version`: PASSED (`v24.14.1`).
- `pnpm --version`: PASSED (`11.22.0`).
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm build`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED (workspace builds/tests and contract tests).
- `pnpm licenses list --json`: PASSED.
- All ten `uv run --frozen python -m slaif_agent_site.<process> --check`
  commands: PASSED.
- `python tools/compose/verify.py`: PASSED.
- `sudo sh tools/compose/smoke.sh slaif007bci`: PASSED (`compose-smoke: OK`),
  including browser devices, edge headers, database-login/secret policy,
  restart/recovery, negative bootstrap, Apache syntax, and 35 repository
  tests. Disposable resources were cleaned by the smoke trap.

The first focused remediation run exposed only an expected transaction-cleanup
test issue after deliberately raising a PostgreSQL error; the test was fixed
to call the public `CowSession.rollback()` before scope exit and then passed.
One initial lint run reported test-line E501 issues; those lines were formatted
and the final full gates above passed. These were not implementation or CI
failures.

## GitHub CI / required checks

Observed for implementation head
`d8b43f3b755ba7a789c7666dc6484d0e1b800b76`:

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

All required implementation-head checks were green at drafting. The
report-only commit may trigger a fresh check run; strategy independently
verifies report-head state.

## Local setup / dependencies

- Existing locked dependencies only; no production dependency or hosted
  service was added.
- uv `0.12.5`, Node `24.14.1`, and pnpm `11.22.0` were used.
- Passwordless `sudo` was used only for the explicitly authorized disposable
  Docker/Compose smoke because unprivileged Docker access is unavailable.
- No production credentials, systems, data, capabilities, cookies, or private
  artifact URLs were accessed.

## Documentation

Updated `docs/DATABASE_ROLES.md` with revision 026’s guarded wrapper and
workspace/site-binding boundary. Existing API/authority docs from 067-a remain
truthful and unchanged in this remediation.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production secrets accessed: NO.
- Production systems accessed: NO.
- Required tests skipped/not run: NO.
- Scope deviation: NO; no lifecycle/publication or trust-expanding behavior
  was added.
- Extra objective PR: NO; PR #58 remains the unique objective PR.
- Coding-agent merge: NO.
- Activated 067-a order/report edited: NO.
- Report commit changes only this new report: YES.

## Known limitations / blockers

This remediation does not implement workspace creation, freeze, review
snapshots, accept/selective accept, public discard, promotion, publication,
media binary upload, Puck UI, or the remaining Agent API surface. The product
remains pre-alpha and does not claim production readiness or hostile-public-
SaaS isolation.

## Recommended strategic follow-up

Strategy should independently review PR #58, the new 067-b evidence, and
report-head checks before deciding whether to accept/merge objective 067.
