# OAP Coding-Agent Report — 076-u

## Work order

- Identifier: `076-u`
- Work-order file: `oap/orders/076-u-complete-agent-content-item-crud.md`
- Numeric objective: `076`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Completed the bounded Agent content-item CRUD slice on the existing Objective
076 branch. Agent now exposes exact item GET, PATCH, and DELETE operations in
addition to the existing list/create surface. Creation derives the current
definition version server-side; update requires a positive row-version token;
delete is a COW tombstone with dependency checks and durable `200` replay.
All item mutations use the strict semantic audit contract and the trusted
database resource/quota boundary. Existing page/component legacy behavior and
the prior six-action type/field audit contract are preserved.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72), `OPEN`
- Base/head branches: `main` / `oap/076-agent-model-content-semantics`
- Starting remote SHA: `7dfeab7d9f3b20ed322cac4e959d7538f27431f2`
- Implementation head SHA: `b66d9ff56e91a2a6c80c37a4b7e309d90740ab54`
- Implementation parent: `7dfeab7d9f3b20ed322cac4e959d7538f27431f2`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (verified after push)
- Implementation commit pushed before report: `b66d9ff56e91a2a6c80c37a4b7e309d90740ab54`
- New PR this turn: NO
- Amended existing PR: YES
- Merge performed: NO

## Changes made

- Added reversible migration `046_001` from `045_001`.
- Added Agent item GET, PATCH, and DELETE routes with exact read/write/delete
  scopes, strict request models, positive row-version validation, stable
  typed error mapping, and durable idempotency.
- Added shared Agent item service operations using the existing bounded
  `ContentItemMixin` validation path and `validators.validate_values`.
- Item creation now obtains the active type definition version inside the
  trusted wrapper; caller-supplied definition versions are not accepted by
  the Agent wrapper signature.
- Item update locks and rechecks the item/type definition and exact row
  version; item delete locks the item, denies visible translation or inbound/
  outbound relation dependencies, and writes a `DELETED` tombstone.
- Extended strict semantic audit identity with `CONTENT_ITEM_CREATED`,
  `CONTENT_ITEM_UPDATED`, and `CONTENT_ITEM_DELETED` mappings.
- Moved type, field, and item mutation/delete budget consumption into their
  SECURITY DEFINER wrappers, including resource allowlists, type/field limits,
  delete enablement, max-deletes, capability/workspace/site/delegator state,
  and transaction rollback behavior. Page/component wrappers retain their
  executor-owned legacy quota path.
- Added capability-bound Agent read wrappers for type, field, and item
  allowlists, including exact item GET, and added the current `046_001` head
  to readiness, packaging, privilege, and repository fixtures.
- Added real PostgreSQL Agent item CRUD proof and adapted direct-wrapper test
  setup to establish the same authenticated capability context as HTTP.

## Files changed

- `oap/active`
- `oap/orders/076-u-complete-agent-content-item-crud.md`
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py`
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`
- `services/backend/src/slaif_agent_site/agent_state/reads.py`
- `services/backend/src/slaif_agent_site/content_model/item_models.py`
- `services/backend/src/slaif_agent_site/content_model/service.py`
- `services/backend/src/slaif_agent_site/control_api/route_policy.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/046_001_complete_agent_content_item_crud.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_control_database_integration.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/integration/test_editable_domain_proof.py`
- `services/backend/tests/integration/test_human_agent_session_control.py`
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `services/backend/tests/unit/test_health_apps.py`
- `services/backend/tests/unit/test_route_policy.py`

## Acceptance-criteria evidence

### Criterion 1 — complete Agent item REST

- Real capability-authenticated Agent ASGI HTTP proof passed list/create/get/
  update/delete with exact response versions and stable `200` delete replay.
- PATCH and DELETE require a positive `expected_row_version`; stale writes
  return conflict without durable mutation or quota residue.
- Item create uses the active type definition version from the trusted
  database type row and does not accept a caller-selected version.
- Wrong body/path/type, wrong site/workspace, missing scope, revoked/expired
  capability, frozen state, and delegator failure remain fail-closed.

### Criterion 2 — shared bounded validation and definition safety

- Create and update use the shared `ContentItemMixin` validation helper and
  `content_model/validators.py` against the active type’s field definitions.
- Required, unknown, localized, cardinality, primitive, executable-string,
  and bounded-value validation remains server authoritative.
- Definition-version changes fail closed for existing items; row locks and
  transaction advisory locks serialize same-workspace races.

### Criterion 3 — trusted database resource and quota authority

- Migration `046_001` binds every Agent type/field/item wrapper to the
  authenticated capability context and existing `044_001` resource helper.
- Type-ID/key allowlists and type/field resource limits are enforced inside
  wrappers; HTTP pre-counts were removed so no route can bypass or race the
  database authority.
- Mutation/delete quota consumption occurs inside the wrapper transaction;
  validation, stale, dependency, quota, and cancellation failures roll back
  the charge. Replays bypass the mutation wrapper and do not recharge.
- Old six-argument Agent item-create authority is removed at `046_001`; the
  old wrapper is restored only by downgrade to the pre-046 state.

### Criterion 4 — strict item audit and idempotency

- Item POST/PATCH/DELETE produce, respectively, `CONTENT_ITEM_CREATED`,
  `CONTENT_ITEM_UPDATED`, and `CONTENT_ITEM_DELETED` with exact resource,
  method, status, quota, operation, and response-record identity.
- Replay returns the original response without a second audit row, COW
  operation, mutation charge, or delete charge; digest mismatch is rejected.
- The legacy ten-argument completion boundary rejects `content_item` after
  `046_001`; the strict thirteen-argument boundary validates all nine
  semantic mappings and response identities.

### Criterion 5 — COW, deletion, and canonical independence

- Delete writes a private workspace tombstone and excludes it from Agent
  reads; the canonical `content_item_base` remains unchanged.
- Visible translations and inbound/outbound relation rows deny deletion;
  no translation/relation routes or unrelated collection-view routes were
  added in this slice.
- Direct Agent runtime table access remains denied, and direct wrapper calls
  without the authenticated capability context fail closed.

### Criterion 6 — reversible migration and privilege safety

- Live migration proofs exercised the `045_001`/`046_001` graph and existing
  downgrade paths with exact migration-head, owner, grant, privilege, and
  hardened-COW checks.
- All new database functions use `SECURITY DEFINER` and fixed
  `SET search_path = pg_catalog`; no dynamic SQL or foundation-private API
  was introduced.

## Local verification

- `uv lock --check`: PASSED — 45 packages resolved.
- `uv sync --frozen --all-groups`: PASSED — 44 packages checked.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`:
  PASSED — 514 tests, 26 subtests.
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED —
  129 tests in 869.10s.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -q`:
  PASSED — 14 tests in 117.96s on the final focused pass.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 257 files.
- `uv run --frozen mypy`: PASSED — 243 source files.
- `python -m compileall -q services/backend/src tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  58 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 350 files,
  0 issues.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-final`: PASSED —
  wheel and source distribution built.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED serially, including recursive package tests and four
  contract tests.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.

## GitHub CI / required checks

Observed on implementation head
`b66d9ff56e91a2a6c80c37a4b7e309d90740ab54`:

- CI run `33362265698`: SUCCESS — Compose and edge packaging; Dependency
  review; Detect supported languages; Foundation PostgreSQL 14, 15, 16, 17,
  and 18; Markdown; Mermaid; Node contracts; Python 3.12, 3.13, and 3.14
  quality/package; Repository policy; and Supply-chain evidence.
- CodeQL run `33362265707`: SUCCESS — Detect supported languages and Analyze
  actions, JavaScript/TypeScript, and Python.
- `gh pr checks 72`: all 20 listed checks were `pass`; no pending, missing,
  cancelled, failed, or skipped check remained at final capture.
- PR state at final capture: `OPEN`, base `main`, exact head branch, and
  successful remote checks. The PR was not merged.

## Local setup / dependencies

- No dependency, lockfile, workflow, architecture, or production package
  change was made.
- PostgreSQL proof used disposable local fixture databases and the existing
  fake role/credential setup; no production system, secret, capability, or
  private artifact was accessed.
- Remote CI supplied the required PostgreSQL 14–18 and clean Compose/edge /
  supply-chain evidence.

## Documentation

- No durable product documentation contract changed; the activated order and
  this report are the required OAP transcript artifacts.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production secrets accessed: NO.
- Production systems/data accessed: NO.
- Required tests skipped/not run: NO.
- Scope deviation: NO.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated order/active edited: NO; strategy-owned bytes were committed
  exactly as authored.
- Report commit changes only this report: YES.
- No translations, relations, collection-view routes, page/component CRUD
  expansion, media, MCP, browser, review, promotion, public OpenAPI/NGINX
  final proof, architecture, dependency, workflow, or release work was added.

## Known limitations / blockers

No blocker remains for this `076-u` execution round. Objective 076 remains
open for later translation, relation, collection-view, and consolidated public
OpenAPI/NGINX proof orders. This report does not claim strategic acceptance or
merge.

## Completion condition

Objective 070/PR #61 is not the active objective in this cycle. For the active
Objective 076 / PR #72, execution is complete because the exact `076-u` order
was implemented, all required local and remote checks are green, the report
will be published as the sole child of the implementation SHA, and the exact
FIFO response will be sent. Strategy alone independently reviews, accepts, and
merges the PR or chooses a later continuation.
