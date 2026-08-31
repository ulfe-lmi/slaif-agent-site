# OAP Coding-Agent Report — 076-t

## Work order

- Identifier: `076-t`
- Work-order file: `oap/orders/076-t-couple-semantic-audit-and-delete-quota.md`
- Numeric objective: `076`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Implemented the bounded 076-t production slice on the existing Objective 076
branch. The new 045 migration couples strict semantic audit identity to the
six content-type/field-definition actions and enforces the tighter of
`delete_quota` and the trusted immutable `max_deletes` resource bound. The
existing type/field implementation remains the only semantic production
surface changed; item/page/component create routes retain honest legacy audit
classification.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72), `OPEN`
- Base/head branches: `main` / `oap/076-agent-model-content-semantics`
- Starting remote SHA: `cbf17fe029a6e81fe1eadb23a00432eb618f2b62`
- Implementation head SHA: `c5b104f1fd567086ce9a24ecfc4bbeb5bb838c65`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (the report-only commit,
  verified after push)
- Implementation commit pushed before report: `c5b104f1fd567086ce9a24ecfc4bbeb5bb838c65`
- Implementation parent: `cbf17fe029a6e81fe1eadb23a00432eb618f2b62`
- New PR this turn: NO
- Amended existing PR: YES
- Merge performed: NO

## Changes made

- Added reversible migration `045_001` from `044_001`.
- Added nullable historical audit identity columns `http_method` and
  `quota_kind`; historical rows remain explicitly unclassified rather than
  receiving fabricated method/quota facts.
- Added a database check for supported non-null semantic combinations.
- Replaced the action-only 11-argument completion with a 13-argument strict
  completion that validates the six action/resource/method/status/quota
  combinations and response action, operation identity, and record ID before
  atomically completing idempotency and inserting one audit row.
- Made the older 10-argument completion fail closed for `content_type` and
  `field_definition` while preserving current legacy item/page/component use.
- Passed the real HTTP method and shared quota kind through the typed Python
  mutation boundary with one centralized six-action contract map.
- Reworked the database delete quota function to call the trusted resource
  constraint helper inside the matching COW context and serialize the counter
  update on the capability row.
- Updated the privilege manifest and current migration-head/package/readiness
  fixtures; no dependency, workflow, architecture, public API, or unrelated
  product changes were made.

## Files changed

- `oap/active`
- `oap/orders/076-t-couple-semantic-audit-and-delete-quota.md`
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py`
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/045_001_agent_semantic_audit_delete_quota.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_control_database_integration.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/integration/test_editable_domain_proof.py`
- `services/backend/tests/integration/test_human_agent_session_control.py`
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_contract.py`

## Acceptance-criteria evidence

### Criterion 1 — durable semantic identity and historical honesty

- `audit.agent_mutation.http_method` and `quota_kind` are persisted by 045.
- Existing rows remain nullable in both columns; the migration and round-trip
  integration proof confirm no historical method or quota fact is fabricated.
- New non-null rows are restricted to the six supported semantic combinations.

### Criterion 2 — strict completion and atomic replay

- Real Agent HTTP handlers executed all six actions and verified exact
  capability/site/workspace, request digest, resource type/ID, action, method,
  status, quota kind, and operation identity in one durable audit row each.
- Replay of every representative action returned the original body/status/
  operation without additional audit, COW, mutation, or delete residue.
- Changed-body key reuse returned `409 IDEMPOTENCY_MISMATCH` without residue.
- Adversarial runtime calls rejected action, resource, method, status, quota,
  response-action, response-operation, and response-record mismatches.

### Criterion 3 — no type/field legacy bypass and append-only audit

- The old action-only 11-argument function is absent at 045; the old 10-
  argument function rejects type/field resources and remains available for the
  current legacy item route.
- `slaif_agent_runtime` has execute only on the intended completion/quota
  functions; PUBLIC execute is absent.
- Agent runtime direct SELECT/UPDATE/DELETE on `audit.agent_mutation` is
  denied.

### Criterion 4 — typed Python wiring and preserved behavior

- `agent_http._execute_mutation` passes `request.method`; `execute_agent_mutation`
  validates one centralized six-action contract and passes the same
  `quota_kind` used for reservation.
- Existing type/field resource/version/idempotency/COW tests and the complete
  mutation module remain green.

### Criterion 5 — transactional `max_deletes`

- Two real Agent application instances/connections raced independent deletes
  with `delete_quota=2` and `max_deletes=1`: exactly one returned `200`, one
  returned stable `429 QUOTA_EXCEEDED`, `delete_used` increased once, and only
  the winner retained idempotency/audit/COW state.
- `max_deletes=0`, missing-bound fallback, replay, and malformed-constraint
  fail-closed behavior are covered by the real PostgreSQL proof.

### Criterion 6 — reversible migration and security-definer safety

- The integration proof exercised 045→044→045 with legacy and semantic rows,
  exact overload presence/absence, owners, grants, current head, and hardened
  COW readiness.
- All new/changed database functions use fixed `SET search_path = pg_catalog`;
  no function uses dynamic SQL.

## Local verification

- `uv lock --check && uv sync --frozen --all-groups`: PASSED — 45 resolved,
  44 checked.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -k semantic_audit_contract_is_strict_and_reversible -q`: PASSED — 1 test.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -k max_deletes_is_the_transactional_delete_quota_bound -q`: PASSED — 1 test.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -q`: PASSED — 13 tests.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`: PASSED — 514 tests, 26 subtests.
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED — 128 tests in 859.71s.
- An earlier complete integration run had one intermittent unrelated human-session failure (127 passed, 1 failed); its exact test rerun passed, followed by the complete 128-test green run above.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED — 256 files.
- `uv run --frozen mypy`: PASSED — 242 source files.
- `python -m compileall -q tools tests/repository services/backend`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 58 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 348 files, 0 issues.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-076-t`: PASSED —
  wheel and source distribution built.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint && pnpm format:check && pnpm typecheck && pnpm test && pnpm build && pnpm licenses list --json`: PASSED.
- `sudo -n sh tools/compose/smoke.sh slaif007076t`: PASSED — `compose-smoke: OK`,
  including clean deployment, six stable devices, Agent restart, browser/
  media/editor/security boundaries, outage/recovery, persistence, and Apache.

## GitHub CI / required checks

Observed on implementation head `c5b104f1fd567086ce9a24ecfc4bbeb5bb838c65`:

- CI run `33356285058`: SUCCESS — Compose and edge packaging; Dependency
  review; Detect supported languages; Foundation PostgreSQL 14, 15, 16, 17,
  and 18; Markdown; Mermaid; Node contracts; Python 3.12, 3.13, and 3.14
  quality/package; Repository policy; Supply-chain evidence.
- CodeQL run `33356285035`: SUCCESS — Detect supported languages and Analyze
  actions, JavaScript/TypeScript, and Python.
- `gh pr checks 72 --repo ulfe-lmi/slaif-agent-site`: all 20 listed checks
  were `pass`; no pending, missing, cancelled, or failed required check was
  observed.
- PR state at capture: `OPEN`, base `main`, mergeable `MERGEABLE`,
  `mergeStateStatus=CLEAN`.

## Local setup / dependencies

- No dependency or lockfile change.
- Routine local Docker access used the executor’s passwordless `sudo` path
  after the unprivileged socket check failed; no production system or secret
  was accessed.
- PostgreSQL integration used disposable local fixture databases and the
  repository’s existing role/credential fixtures.

## Documentation

- No durable product behavior/documentation contract required a documentation
  change; the activated order and report are the OAP transcript artifacts.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production secrets accessed: NO.
- Production systems/data accessed: NO.
- Required tests skipped/not run: NO.
- Scope deviation: NO.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated order/active edited: NO; they were committed exactly as authored.
- Report commit changes only this report: YES.
- No content-item/translation/relation/collection-view CRUD, media, MCP,
  browser, review, promotion, public OpenAPI, NGINX, architecture, dependency,
  workflow, or release work was added.

## Known limitations / blockers

No blocker remains for this 076-t round. Objective 076 remains open for the
separate content-item/translation/relation/collection-view slices and the
consolidated public-NGINX/restart/OpenAPI proof required by later strategy
orders. This report does not claim strategic acceptance or merge.

## Recommended strategic follow-up

Strategy should independently review this report and PR #72. If accepted, the
coding agent’s work for 076-t is complete; only strategy may choose the next
continuation, accept, or merge.
