# OAP Coding-Agent Report — 077-f

## Work order

- Identifier: `077-f`
- Work-order file: `oap/orders/077-f-make-page-downgrade-preflight-atomic.md`
- Numeric objective: `077`
- Work-order SHA-256: `c292c69963b53a100e77eb968181f918da3d4a21fa00090a63455e3a366b25a9`
- `oap/active` SHA-256: `9022e61bf55e7182d24060d853f9d241319fed22a56ee72198ee258ef4e7b518`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`COMPLETE`

## Executive summary

The active 077-f order closes the remaining bootstrap downgrade atomicity
defect. When the database is at migration `049_001`, bootstrap now preflights
active or pending workspace COW operations, route-template pages, tombstones,
and PAGE audit rows through application-owned relations before it changes
readiness or calls the public COW-disable API. Each incompatible state returns
one stable operator-facing `BootstrapStateError` with no state change. A
compatible downgrade uses the public disable path, and a later migration
failure leaves readiness unsafe with explicit recovery guidance.

The substantive implementation is complete and unchanged after local and
remote verification. It is committed and pushed as
`0943df0b46a8bbeeafbfbedf1cd331987cf44beb`, directly on the required 077-e
report head `502f8856c3f40d96c5084086a4bb91a4490c74a3`.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74)
- PR state: `OPEN`, unmerged
- Base/head: `main` / `oap/077-agent-site-structure-semantics`
- Starting remote report head: `502f8856c3f40d96c5084086a4bb91a4490c74a3`
- Starting remote `main`: `067676314e0d9664d40cb8514ea549b966a4eb2d`
- Implementation head SHA: `0943df0b46a8bbeeafbfbedf1cd331987cf44beb`
- Implementation head parent: `502f8856c3f40d96c5084086a4bb91a4490c74a3`
- Implementation commit pushed before this report: `0943df0b46a8bbeeafbfbedf1cd331987cf44beb`
- Remote branch before report publication: `0943df0b46a8bbeeafbfbedf1cd331987cf44beb`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- New PR this turn: `NO`
- Amended existing PR this turn: `YES`
- Merge or auto-merge performed: `NO`

## Changes made

- Added migration-`049_001` downgrade preflight for active/pending public COW
  operations, non-null `content.page.route_template` or `deleted_at` state,
  and PAGE audit rows. The checks use application-owned relations and the
  exported `get_session_operations` API; no private foundation relation or
  function name was added.
- Unified incompatible-state rejection behind one stable
  `bootstrap downgrade refused` error before the readiness marker or public
  `disable_cow_schema` call changes anything.
- Marked readiness pending before the compatible public disable step and
  wrapped the subsequent Alembic downgrade. A failure after disable raises a
  precise unsafe-readiness error directing the operator to fix the migration
  and run bootstrap reconcile before serving traffic.
- Added real PostgreSQL tests for each incompatible state, a compatible
  public disable/downgrade/re-upgrade/reconcile round trip, and the
  failure-after-disable fail-closed path. The tests capture revision, COW
  status, readiness, content, audit, workspace operations, functions, and
  privilege/hardening evidence; incompatible cases monkeypatch and prove the
  public disable function is not called.

## Files changed

The implementation commit changed exactly:

- `oap/active`
- `oap/orders/077-f-make-page-downgrade-preflight-atomic.md`
- `services/backend/src/slaif_agent_site/bootstrap/service.py`
- `services/backend/tests/integration/test_database_bootstrap.py`

No generated OpenAPI, product documentation, lockfile, dependency, image,
architecture, constitution, or historical report changed.

## Acceptance-criteria evidence

### Atomic incompatible-state preflight

- `test_bootstrap_downgrade_049_preflight_is_atomic` passed for
  `pending_operations`, `route_template`, `tombstone`, and `page_audit`.
- The focused downgrade selection passed with `6 passed, 23 deselected`.
- For every incompatible fixture, the before/after snapshot remained equal
  for migration revision, public COW status, readiness, content, audit,
  functions, workspace operations, and public privilege validation; the
  disable-call count remained zero.

### Compatible and failure paths

- The compatible integration test passed through the public COW disable call,
  downgrade, upgrade, reconcile, hardening, and safe privilege validation.
- The failure-after-disable integration test passed with COW disabled,
  readiness `PENDING`/unsafe, invalid readiness validation, and the precise
  reconcile recovery message. It did not claim a ready runtime against
  unprotected content.
- The full bootstrap integration module passed: `29 passed`.
- The full integration suite passed: `156 passed`.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 264 files already formatted.
- `uv run --frozen mypy`: PASSED — 247 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`:
  PASSED — 521 tests, 26 subtests, 1 existing Starlette/httpx deprecation
  warning.
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED —
  156 tests.
- `python -m compileall -q tools tests/repository services/backend/src`:
  PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  58 tests.
- `python tools/check_repository.py`: PASSED — repository policy.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 371 files, 0
  issues.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — source
  and wheel distributions built.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — production build, workspace tests, web tests,
  browser-worker tests, and contract tests.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- All ten `uv run --frozen python -m <process> --check` smoke commands for
  control API, Editor API, Agent API, Render API, MCP adapter, media service,
  review worker, scheduler, media GC, and bootstrap: PASSED with `CHECK_OK`.
- `sudo -n sh tools/compose/smoke.sh slaif071e`: PASSED — clean Compose
  deployment, public acceptance, recovery, edge, packaging, security, and 47
  repository tests; final `compose-smoke: OK`.

No required check was skipped, weakened, replaced, or treated as passed from
an incomplete run.

## GitHub CI / required checks

For implementation head `0943df0b46a8bbeeafbfbedf1cd331987cf44beb`, CI workflow
run `33877541637` and CodeQL run `33877541609` were inspected. Every required
check was terminal `pass`:

- Analyze (actions)
- Analyze (javascript-typescript)
- Analyze (python)
- CodeQL
- Compose and edge packaging
- Dependency review
- Detect supported languages
- Foundation PostgreSQL 14
- Foundation PostgreSQL 15
- Foundation PostgreSQL 16
- Foundation PostgreSQL 17
- Foundation PostgreSQL 18
- Markdown
- Mermaid
- Node contracts
- Python 3.12 quality and package
- Python 3.13 quality and package
- Python 3.14 quality and package
- Repository policy
- Supply-chain evidence

All required checks at the implementation head were green: `YES`. The
report-only commit creates a fresh check set; strategy must independently
verify that its `SELF` report is the remote PR head and that its current
checks are terminal success.

## Local setup / dependencies

- Existing frozen uv and pnpm environments were used.
- Disposable PostgreSQL fixtures and the clean Compose stack were operated
  with passwordless sudo for routine test infrastructure only.
- No production dependency, image, lockfile, exception, or foundation version
  changed.
- Foundation use remains through qualified `agentcow.postgres` public APIs.
- No production systems, data, credentials, capabilities, cookies, or private
  artifact URLs were accessed, printed, or committed.

## Documentation and governance

- `oap/active` was committed byte-for-byte as the strategic activation
  supplied by the order; the order file was committed byte-for-byte and was
  not authored or rewritten by coding.
- No architecture, constitution, communication protocol, historical report,
  prior order, or unrelated strategic artifact was rewritten.
- This report is the sole intended report publication file and is published
  as the report-only child of the literal implementation SHA.

## Safety and scope confirmations

- Unrelated files changed: `NO`.
- Production systems/data accessed: `NO`.
- Real secrets/capabilities/cookies/private credentials printed or committed:
  `NO`; tests used disposable fixtures, fake credentials, and opaque
  in-memory tokens.
- Required checks skipped, weakened, or replaced: `NO`.
- Scope deviation: `NO`; no page API/route behavior, locale CRUD, navigation,
  redirect, dynamic Render, composition/design/Puck, media/MCP,
  freeze/review/promotion, 078+, cleanup, refactor, dependency, image,
  exception, architecture, or historical-artifact work was added.
- Extra objective PR: `NO`.
- Coding-agent merge or auto-merge: `NO`.
- Report publication commit changes only this report: `YES`.

## Known limitations / completion condition

No 077-f implementation blocker remains. PR #74 remains open because coding
agents never merge objective PRs and `COMPLETE` is not strategic acceptance.
The broader remaining Objective 077 scope outside this bounded bootstrap
downgrade slice is not implemented by this order.

Objective 077 / PR #74 may be declared complete only when strategy
independently verifies this report-only `SELF` child, its exact parent/path,
and all fresh report-head checks, then obtains the required human review,
merges PR #74 to remote `main`, and verifies the merged main state. Until
that strategic/human merge and verification occurs, this is a delivered
077-f implementation round, not objective acceptance.

Report publication commit: SELF
