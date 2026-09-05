# OAP Coding-Agent Report — 077-a

## Work order

- Identifier: `077-a`
- Work-order file: `oap/orders/077-a-agent-site-structure-semantics.md`
- Numeric objective: `077`
- Work-order SHA-256: `6acd1d5907f5e87492e692249ca708ab0c6f7955017879ef70cb4cc5d8f40bc9`
- `oap/active` SHA-256: `26492a62ac9e83c75ea0f11df246d802f0a3a72034dbb4c64b87e6256480bb77`
- PR mode: `CREATED_NEW_PR`

## Status

`COMPLETE`

## Executive summary

Implemented the bounded 077-a Agent page structure slice on one fresh PR. The
slice provides site-confined page CRUD, structural move and restore actions,
normalized slugs, deterministic effective routes, strict resource constraints,
COW lifecycle behavior, PostgreSQL serialization, semantic audit/idempotency/
quota enforcement, route policy, OpenAPI, documentation, and integration/race
evidence.

The first remote CI run exposed one stale acceptance-harness expectation: the
new required page create mutation produced the correctly audited
`PAGE_CREATED` event, while the harness still expected the pre-077 event set.
The only follow-up was the nine-line harness contract/defaults correction in
`tools/compose/public_agent_acceptance.py`. The product implementation was not
changed. The fresh CI and CodeQL runs for the corrected head are fully green.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74)
- PR state at verification: `OPEN`, not draft, unmerged
- Base/head: `main` / `oap/077-agent-site-structure-semantics`
- Starting remote `main` SHA: `067676314e0d9664d40cb8514ea549b966a4eb2d`
- Implementation commits pushed before the report:
  - `9453a42db7a52605d50297296943232742c3958b` — page hierarchy and route semantics
  - `9cad25f9d3d392cbd913e434bc9a616606c548d1` — acceptance audit contract correction
- Implementation head SHA: `9cad25f9d3d392cbd913e434bc9a616606c548d1`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be derived and verified after push)
- Report parent must equal implementation SHA: yes
- New PR this turn: yes
- Amended existing PR this turn: no
- Merge or auto-merge performed: NO

## Changes made

- Added the public Agent page list/get/create/update/delete/move/restore
  surface, including the permitted trailing-slash aliases for list/create.
- Added strict page slug and route-template normalization. Only the exact
  terminal literal `{slug}` is dynamic; route traversal, encoded separators,
  malformed templates, and hierarchy tricks are rejected.
- Added deterministic effective route derivation from the page tree, root/home
  handling, locale prefixing, and static/dynamic route conflict checks.
- Added site/workspace-confined page hierarchy validation, root/subtree and
  depth/visibility constraints, route-prefix constraints, and capability
  resource limits at both HTTP and trusted PostgreSQL boundaries.
- Added migration `049_001_agent_page_structure` with route-aware Agent
  wrappers, explicit legacy human-page projections, COW mutation lifecycle,
  advisory structural locking, dependency-safe delete/tombstone/restore, and
  downgrade support.
- Added exact `PAGE_CREATED`, `PAGE_UPDATED`, `PAGE_DELETED`, `PAGE_MOVED`, and
  `PAGE_RESTORED` semantic contracts with method/status/quota mappings, strict
  same-transaction audit, durable idempotency, and wrapper-owned quota charge.
- Added focused lifecycle and real PostgreSQL duplicate-create race coverage.
- Updated route policy, privileges, canonical Agent OpenAPI, and API docs.
- Updated the public Compose acceptance auditor to include the new page-create
  semantic event and the production request defaults. This is test evidence
  alignment only; no product implementation behavior was altered by the fix.

## Files changed

- `contracts/openapi/agent-v1.json`
- `docs/API.md`
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py`
- `services/backend/src/slaif_agent_site/agent_api/models.py`
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`
- `services/backend/src/slaif_agent_site/agent_state/reads.py`
- `services/backend/src/slaif_agent_site/content_model/page_models.py`
- `services/backend/src/slaif_agent_site/content_model/service.py`
- `services/backend/src/slaif_agent_site/control_api/route_policy.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/049_001_agent_page_structure.py`
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
- `tools/compose/public_agent_acceptance.py`

The exact strategy-owned `oap/active` and
`oap/orders/077-a-agent-site-structure-semantics.md` bytes were carried in the
implementation commit unchanged. They were not edited by the coding agent.

## Acceptance-criteria evidence

### Page API and typed contract

- Implemented the ordered page list/get/create/update/delete/move/restore
  routes with typed request/response models, stable error behavior, required
  mutation idempotency, and generated canonical OpenAPI.
- Route policy contains the exact public Agent inventory and the privileges
  contain the new page wrapper signatures. The OpenAPI drift check passed.

### Slug, hierarchy, and effective route semantics

- Slugs are bounded normalized path segments. Page roots, ancestors, sibling
  order, root/home omission, locale prefixes, static routes, and the exact
  terminal `{slug}` form are derived deterministically in PostgreSQL.
- Structural conflict, cycle, descendant, foreign-site, invisible-page,
  malformed-route, depth, visible-count, and route-prefix cases are rejected.

### COW lifecycle and authorization

- Integration coverage creates roots and descendants, reads from another
  workspace, updates and moves a page, rejects dependency-unsafe delete,
  creates a tombstone on valid delete, and restores the same page identity and
  hierarchy through the production Agent HTTP path.
- Site/workspace/capability scope, route-specific scope, workspace state,
  optimistic row version, delete enablement, and resource constraints remain
  enforced at trusted boundaries.

### Concurrency and durable mutation evidence

- The focused integration coverage holds the production PostgreSQL advisory
  structural lock across two concurrent Agent create requests and verifies one
  successful create, one conflict, and one final visible page.
- The full integration suite verifies semantic action/audit/idempotency/quota
  behavior, including replay without a second COW/audit/quota effect and
  stable idempotency mismatch.

### Scope preservation

- Only the 077-a page structure/route slice was implemented. Full Objective 077
  locale/nav/redirect APIs, later dynamic Render projection, and other future
  077 work remain out of scope. No 078+ work, cleanup, refactor, feature, or
  architectural expansion was added.

## Local verification

- `uv --version`: PASSED — `uv 0.12.5`
- `uv lock --check`: PASSED
- `uv sync --frozen --all-groups`: PASSED
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 264 files already formatted
- `uv run --frozen mypy`: PASSED — no issues in 247 source files
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED
  — 517 passed, 1 unrelated Starlette/httpx deprecation warning
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 140
  passed in 1035.04 seconds
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — source and
  wheel distributions built
- `python -m compileall -q tools tests/repository`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 58
  tests
- `python tools/check_repository.py`: PASSED — repository policy
- `python tools/check_mermaid.py`: PASSED — 16 diagrams, 367 Markdown files
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`:
  PASSED — canonical Agent OpenAPI is current
- All ten required process `--check` smoke commands, run through
  `uv run --frozen python`, PASSED with `CHECK_OK`: control API, editor API,
  Agent API, render API, MCP adapter, media service, review worker, scheduler,
  media GC, and bootstrap.
- An initial bare system-Python process smoke was NOT a product result because
  that interpreter lacked the package (`ModuleNotFoundError`); the required
  frozen `uv` invocation immediately above passed all ten checks.
- `node --version`: PASSED — `v24.14.1`
- `pnpm --version`: PASSED — `11.22.0`
- `pnpm install --frozen-lockfile`: PASSED
- `pnpm lint`: PASSED
- `pnpm format:check`: PASSED
- `pnpm typecheck`: PASSED
- `pnpm test`: PASSED
- `pnpm build`: PASSED
- `pnpm licenses list --json`: PASSED
- Focused public-agent audit contract check for `PAGE_CREATED` and its
  defaulted fields: PASSED.

## GitHub CI / required checks

The first CI run for implementation head `9453a42db7a52605d50297296943232742c3958b`
failed only in Compose and edge packaging because the pre-existing acceptance
harness expected 30 semantic audit records while the new ordered page-create
route correctly produced 31. The failed event was:
`PAGE_CREATED:POST:mutation:oap-page-create-2f7ddae76952`.

After the minimal acceptance-harness correction, CI run `33825776979` and
CodeQL run `33825776995` for implementation head
`9cad25f9d3d392cbd913e434bc9a616606c548d1` were terminal and green. Compose
and edge smoke passed all 11 browser projects, including public-agent
acceptance. No check was skipped, weakened, cancelled, or missing.

Required checks observed as `SUCCESS`:

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

- All required checks green while drafting this report: yes
- Report-only push may trigger a fresh check set; strategy must verify the
  literal `SELF` report head independently.

## Local setup / dependencies

- Existing locked Python and Node environments were used: uv `0.12.5`, Node
  `24.14.1`, pnpm `11.22.0`, and TypeScript `6.0.3`.
- Existing disposable PostgreSQL and fake-credential integration fixtures were
  used. Compose CI used the repository's existing disposable services and
  exact Playwright browser setup.
- No production dependency, lockfile dependency, hosted service, credential,
  or infrastructure requirement was added.

## Documentation

- Updated `docs/API.md` with the public Agent page operations, route semantics,
  and the intentionally remaining later 077 scope.
- Regenerated `contracts/openapi/agent-v1.json` from the production handlers
  and verified it with the canonical generator check.
- No architecture, constitution, communication protocol, order, or active
  policy document was edited.

## Safety and scope confirmations

- Unrelated files changed: no. Existing test/contract metadata files changed
  only where required to register the ordered migration, route inventory, and
  acceptance evidence.
- Historical strategic orders and prior reports rewritten: no.
- Production systems or data accessed: no.
- Real secrets, capabilities, cookies, private URLs, or production credentials
  printed or committed: no.
- Required tests skipped, weakened, or replaced: no.
- Scope deviation: no. The acceptance-harness correction was the minimal repair
  required by the new 077-a semantic event and did not change product behavior.
- Extra objective PR: NO.
- Coding-agent merge or auto-merge: NO.
- Activated order or `oap/active` edited: NO.
- Report commit changes only this report: yes; verified after publication.

## Known limitations / blockers

- This report covers only 077-a. Later locale, navigation, redirect, and
  dynamic Render projection behavior remains for separately activated orders.
- PR #74 is intentionally still open and unmerged. Green checks do not mean
  strategic acceptance.
- The report-only commit may cause GitHub to recalculate checks; its literal
  remote head and check state must be independently verified by strategy.

## Recommended strategic follow-up

Strategy may independently review the exact PR diff, this report, the
report-only remote head, and the green required checks. Objective 077-a / PR #74
can be declared complete only after that independent strategic review confirms
the bounded acceptance criteria and chooses the normal OAP merge path. The
coding agent does not merge or choose the next order.

Report publication commit: SELF
