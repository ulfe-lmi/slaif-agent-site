# OAP Coding-Agent Report — 076-v

## Work order

- Identifier: `076-v`
- Work-order file: `oap/orders/076-v-repair-item-semantics-and-add-translations.md`
- Numeric objective: `076`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Completed the bounded 076-v repair on the existing Objective 076 branch. Agent
item deletion is now a real COW delete that returns the pre-delete record and
leaves the canonical base intact. Every Agent model/field/item wrapper checks
its exact capability scope at the trusted database boundary, including
fail-closed handling of malformed scope storage. Field mutations atomically
advance the parent content-type definition version.

Added the exact Agent translation REST surface, with localized validation,
row-version and idempotency semantics, COW isolation, strict scopes, quotas,
and semantic audit mappings. Added one reversible `047_001` migration with an
exact 046 downgrade/047 upgrade proof. All required local gates and the full
remote CI/CodeQL matrix passed on the implementation head.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72), `OPEN`
- Base/head branches: `main` / `oap/076-agent-model-content-semantics`
- Required starting remote report head:
  `c52d12a84e047268ca6f40a811178ae3bc7afe6a`
- Implementation head SHA:
  `3833e994255262cd12de281a9fe1dd257662a9b9`
- Implementation parent:
  `c52d12a84e047268ca6f40a811178ae3bc7afe6a`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (to be verified after push)
- Implementation commits pushed before report:
  `3833e994255262cd12de281a9fe1dd257662a9b9`
- New PR this turn: NO
- Amended existing PR: YES
- Merge performed: NO

## Changes made

- Replaced the item soft-status delete with a real delete through the active
  COW view, including deterministic locks, dependency checks, delete quota,
  pre-delete response identity, replay, and canonical/other-workspace
  isolation.
- Added exact capability-scope checks to the Agent database wrappers for
  `content-model:read|write|delete`, `field-definition:read|write|delete`,
  `content-item:read|write|delete`, and `translation:read|write` as applicable.
  Invalid or malformed scope JSON fails closed before disclosure, charge, or
  COW mutation.
- Made field create/update/delete lock and increment the active parent content
  type definition version exactly once in the same transaction. Failed,
  stale, denied, replayed, and cancelled mutations do not increment it.
- Added Agent routes:
  `GET|POST /api/agent/v1/content-items/{item_id}/translations` and
  `GET|PATCH|DELETE /api/agent/v1/content-items/{item_id}/translations/{translation_id}`.
- Added translation wrappers, typed Agent service methods, exact route policy,
  localized value validation, site/workspace/item confinement, positive row
  versions, idempotency, mutation/delete quotas, and strict audit identity.
- Added semantic mappings for
  `CONTENT_ITEM_TRANSLATION_CREATED`,
  `CONTENT_ITEM_TRANSLATION_UPDATED`, and
  `CONTENT_ITEM_TRANSLATION_DELETED`; the legacy completion boundary rejects
  the translation resource.
- Added reversible migration `047_001` from `046_001`, updating current-head,
  readiness, privilege, package, and repository contracts. Its downgrade
  restores the exact 046 function/audit contract and its upgrade restores the
  repaired 047 contract with hardened COW behavior.
- Corrected the immutable 076-u report’s stale Objective 070 / PR #61 wording
  append-only in this report; 076-u itself was not edited.

## Files changed

- `oap/active`
- `oap/orders/076-v-repair-item-semantics-and-add-translations.md`
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py`
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`
- `services/backend/src/slaif_agent_site/agent_state/reads.py`
- `services/backend/src/slaif_agent_site/content_model/__init__.py`
- `services/backend/src/slaif_agent_site/content_model/models.py`
- `services/backend/src/slaif_agent_site/content_model/service.py`
- `services/backend/src/slaif_agent_site/control_api/route_policy.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/047_001_repair_item_semantics_and_translations.py`
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

### Criterion 1 — true COW item deletion

- Real PostgreSQL Agent HTTP and direct-wrapper tests passed for canonical and
  workspace-created item deletion. The response is the exact pre-delete
  record; the workspace view becomes absent; replay is `200` without another
  charge, operation, or audit row.
- Canonical base content, another workspace, and another site remain
  unchanged. Foundation operation classification is a real COW delete, not a
  soft-status update. Visible translation and relation dependencies continue
  to block deletion, and a now-empty type can subsequently be deleted.

### Criterion 2 — exact trusted-wrapper scopes

- Real reduced-scope capabilities were exercised directly against every
  existing type, field, item, and translation read/mutation wrapper. Wrong
  scopes fail with `AGENT_SCOPE_DENIED` before disclosure or side effects;
  malformed `{}` scope storage fails closed; a correct full capability retains
  resource and quota confinement.
- HTTP scope checks remain defense in depth. No old bypass signature or public
  execute authority was added.

### Criterion 3 — parent definition versions

- Field create/update/delete tests prove one parent version increment per
  successful mutation, including concurrent field changes without lost
  updates. Failed, stale, denied, replayed, and cancelled paths leave state
  unchanged.
- Existing items become stale after a field-model change; item and
  translation writes fail with the existing stale-definition semantics and no
  residue.

### Criterion 4 — Agent translation semantics

- Real capability-authenticated PostgreSQL HTTP tests passed translation
  create/list/get/update/delete with exact scopes, localized required/
  cardinality/primitive/bounds validation, current-definition checks,
  positive row versions, idempotency replay/mismatch, delete quota, and
  `200` delete replay.
- Cross-site, cross-workspace, wrong-parent, disallowed-parent, revoked,
  expired, frozen, delegator-loss, missing-scope, and wrong-scope cases are
  fail-closed with the established Agent envelope. Canonical and workspace
  isolation, COW operations, quota rollback, and audit identity were verified.
- The strict audit contract is exact: POST/201 uses `mutation`, PATCH/200
  uses `mutation`, and DELETE/200 uses `delete`; the legacy completion rejects
  translations.

### Criterion 5 — migration and repository contracts

- Real migration tests passed `046 -> 047 -> 046 -> 047`, preserving legacy and
  semantic audit rows, content state, owners, grants, function signatures,
  checks, readiness, and hardened COW state.
- The migration uses fixed `pg_catalog` search paths, no dynamic SQL, and no
  foundation-private API. Relations, collection views, final public
  OpenAPI/NGINX proof, and other explicitly deferred 076 slices remain open.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 258 files already formatted.
- `uv run --frozen mypy`: PASSED — no issues in 244 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 514 tests and 26 subtests.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 133
  tests in 895.98 seconds.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  58 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files using CLI
  11.16.0.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 352 files, 0
  issues.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-076v`: PASSED —
  wheel and source distribution.
- Initial grouped `python -m slaif_agent_site.* --check` invocation: FAILED
  because system Python did not expose the `src` package; no product process
  was started. The required checks were immediately rerun in the frozen
  environment and passed:
  `uv run --frozen python -m slaif_agent_site.control_api --check` —
  `CHECK_OK`; the equivalent commands for `editor_api`, `agent_api`,
  `render_api`, `mcp_adapter`, `media_service`, `review_worker`, `scheduler`,
  `media_gc`, and `bootstrap` each returned their exact `CHECK_OK` result.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — build, recursive package tests, application tests,
  browser-worker tests, and four contract tests.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- Focused Agent item, field, translation, scope, canonical-delete, migration
  round-trip, semantic-audit, and concurrency tests: PASSED.

## GitHub CI / required checks

Observed on implementation head
`3833e994255262cd12de281a9fe1dd257662a9b9`:

- CI run `33368360033`: SUCCESS — Compose and edge packaging, dependency
  review, Foundation PostgreSQL 14/15/16/17/18, Markdown, Mermaid, Node
  contracts, Python 3.12/3.13/3.14 quality and package, repository policy,
  and supply-chain evidence.
- CodeQL run `33368360052`: SUCCESS — detect supported languages and Analyze
  actions, JavaScript/TypeScript, and Python; CodeQL check run
  `99413833718` passed.
- `gh pr checks 72`: all observed checks were `pass`; no pending, missing,
  cancelled, failed, or skipped check remained at final implementation-head
  capture.
- PR state at final implementation-head capture: `OPEN`, base `main`, exact
  head branch, not merged.
- The report-only commit may trigger fresh checks; the report records the
  implementation-head state and the report head is verified separately.

## Local setup / dependencies

- No dependency, lockfile, workflow, architecture, or production package
  change was made.
- PostgreSQL proof used disposable local fixture databases and existing fake
  roles/credentials. No production system, secret, capability, or private
  artifact was accessed.
- No durable setup change was required; remote CI supplied PostgreSQL 14–18,
  clean Compose/edge, and supply-chain evidence.

## Documentation

- No durable product documentation contract changed. The activated order and
  this report are the required OAP transcript artifacts.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production secrets accessed: NO.
- Production systems/data accessed: NO.
- Required tests skipped/not run: NO. One invalid system-Python smoke
  invocation was corrected and rerun successfully; it was not treated as a
  pass.
- Scope deviation: NO.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated order/active edited: NO. Strategy-owned bytes were committed
  exactly as authored; the coding agent did not choose or rewrite them.
- Report commit changes only this report: YES.
- No relations, collection-view, page/navigation/redirect/composition/design,
  media, MCP, browser, review, promotion, final public OpenAPI/NGINX,
  dependency, architecture, governance, workflow, release, cleanup, or
  unrelated refactoring work was added.

## Known limitations / blockers

No blocker remains for this 076-v execution round. Objective 076 remains open
for the explicitly deferred relations, collection views, and consolidated
public OpenAPI/NGINX proof. The immutable 076-u report’s stale Objective 070 /
PR #61 sentence remains unchanged; this report is the append-only correction.

## Completion condition

Coding execution is complete when this report-only commit is the verified
remote head and the exact FIFO response is sent. Objective 076 / PR #72 can be
declared complete only after strategy independently reviews and accepts the
076-v evidence and merges the existing PR; the coding agent does not merge it.
