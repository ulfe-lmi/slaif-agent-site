# OAP Coding-Agent Report — 077-g

## Work order

- Identifier: `077-g`
- Work-order file: `oap/orders/077-g-agent-locale-and-navigation-semantics.md`
- Numeric objective: `077`
- Work-order SHA-256: `ceaffae5d752f2a7532b0c7501a7945b62ab7d521abe4148f8485fdae365c3ce`
- `oap/active` SHA-256: `f726099bd1ccaf19e70fff4f207a161d7afbd4dfb9d403fc193250da6d1562a3`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`COMPLETE`

## Executive summary

The active 077-g order is complete. The existing Objective 077 branch now
provides capability-bound Agent locale configuration and navigation
container/item CRUD, typed semantic placement, page/internal/HTTPS-external
targets, COW isolation, idempotency, quotas, audit contracts, and one shared
PostgreSQL structural lock spanning page, locale, and navigation writes.

The implementation is committed and pushed as
`c294a8696312a0bba4a6883af094d354561a3601`, directly on the required 077-f
report head `8a7aea39211d1555baf9703cfe82ea8f99e0874c`. The full local gates,
clean Compose acceptance, PostgreSQL 14–18 matrix, and current GitHub checks
are green. No substantive implementation blocker remains.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74)
- PR state: `OPEN`, unmerged
- Base/head: `main` / `oap/077-agent-site-structure-semantics`
- Starting remote report head: `8a7aea39211d1555baf9703cfe82ea8f99e0874c`
- Starting remote `main`: `067676314e0d9664d40cb8514ea549b966a4eb2d`
- Implementation head SHA: `c294a8696312a0bba4a6883af094d354561a3601`
- Implementation head parent: `8a7aea39211d1555baf9703cfe82ea8f99e0874c`
- Implementation commit pushed before this report: `c294a8696312a0bba4a6883af094d354561a3601`
- Remote branch before report publication: `c294a8696312a0bba4a6883af094d354561a3601`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- New PR this turn: `NO`
- Amended existing PR this turn: `YES`
- Merge or auto-merge performed: `NO`

## Changes made

- Added Agent HTTP reads for locales, navigation containers, navigation items,
  and container item lists under `/api/agent/v1`.
- Added Agent locale create/update/delete and navigation container/item
  create/update/delete/move mutations with typed request and response models,
  exact scopes, idempotency headers, row versions, mutation/delete quotas, and
  semantic action contracts.
- Added migration `050_001` after `049_001`. It extends
  `content.site_locale`, `content.navigation`, and `content.navigation_item`
  through the existing product substrate with bounded labels, navigation row
  versions, maintained `parent_key`, and the deferrable unique sibling
  constraint `content.navigation_item_sibling_position`.
- Added/redefined the application-owned PostgreSQL functions
  `control.slaif_agent_resource_constraints`,
  `control.slaif_agent_idempotency_complete`,
  `control.slaif_agent_structural_lock`,
  `content.slaif_agent_page_effective_route`,
  `content.slaif_agent_navigation_validate_target`, all Agent locale,
  navigation, and navigation-item functions, and compatible Editor navigation
  projections. The Agent runtime receives only the narrow wrapper `EXECUTE`
  grants declared in `db/privileges.py`; the internal item apply helper is not
  granted to the Agent role.
- Added downgrade preflight compatibility for both the 049 page-structure
  state and the new 050 state, including safe refusal before public COW
  disable when new state cannot be represented.
- Regenerated canonical `contracts/openapi/agent-v1.json`, updated API/testing
  documentation, and extended the real public NGINX/Compose acceptance journey.

## Files changed

The implementation commit changed exactly:

- `contracts/openapi/agent-v1.json`
- `docs/API.md`
- `docs/TESTING.md`
- `oap/active`
- `oap/orders/077-g-agent-locale-and-navigation-semantics.md`
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py`
- `services/backend/src/slaif_agent_site/agent_api/models.py`
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`
- `services/backend/src/slaif_agent_site/agent_state/reads.py`
- `services/backend/src/slaif_agent_site/bootstrap/service.py`
- `services/backend/src/slaif_agent_site/content_model/service.py`
- `services/backend/src/slaif_agent_site/content_model/site_data_models.py`
- `services/backend/src/slaif_agent_site/control_api/route_policy.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/050_001_agent_locale_navigation.py`
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

## Acceptance-criteria evidence

### Locale and navigation contract

- The public Agent journey configures a second enabled locale, switches the
  workspace default, observes the visible COW default, and restores/removes
  workspace-only locale state without changing canonical locale state.
- Navigation containers have bounded labels/settings, immutable site/key
  identity, positive row versions, and dependency-denied deletion.
- Items support PAGE, safe INTERNAL, and allowlisted HTTPS EXTERNAL targets;
  page targets are same-site and non-tombstoned. Labels and locale bindings
  are bounded and validated at both HTTP and PostgreSQL boundaries.
- Item create, update, and move use optional mutually exclusive before/after
  anchors. Positions are server-owned, dense sibling order; parent changes
  reject foreign containers, self/descendant cycles, excessive depth, and
  invalid anchors.
- Page deletion remains blocked by a visible navigation page reference;
  locale disable/delete rejects active page, item, redirect, translation, and
  other relevant localized references; default locale invariants are enforced
  transactionally.

### Authority, COW, and semantic integrity

- Locale reads require `site:read`; navigation reads require
  `navigation:read`; locale mutations require `locale:configure`; navigation
  container create/update/delete require `navigation:create`,
  `navigation:write`, and `navigation:delete` respectively; item create,
  update, and move require `navigation:write`, and item delete requires
  `navigation:delete`.
- Lower presets and narrowed resource constraints fail closed. The trusted
  database boundary enforces locale/navigation allowlists, visible-resource
  maxima, depth, route-prefix, ordinary request/mutation quotas, and delete
  quotas. Unknown or malformed resource constraints are rejected.
- Every mutation uses one operation UUID, positive expected row version where
  applicable, one wrapper-owned quota charge, and one same-transaction
  semantic audit row. Replays return the stored result without a second COW
  operation, version, quota, or audit row; digest mismatch is stable 409.
- Agent records are read and changed only through capability-bound public COW
  functions. Canonical site/default locale state, another workspace, another
  site, and private foundation relations/functions remain outside Agent
  authority.
- Page, locale, navigation, and navigation-item structural operations join
  the deterministic workspace+site `page-structure` advisory lock after the
  existing workspace lifecycle lock. No Python list-then-write or timing-sleep
  correctness path was added.

### Races, cancellation, and migration

- Real multi-connection PostgreSQL/public Agent tests cover page deletion versus
  navigation reference creation, locale disable versus page/reference
  creation, concurrent default switches, opposing item moves/cycle attempts,
  sibling reorder/create collisions, and cancellation while default/reorder
  operations wait on the structural lock.
- The focused race test passed with one coherent serialized winner/loser,
  stable errors, no deadlock, no residual quota/idempotency/audit/COW rows, and
  successful retry after cancellation.
- The focused migration downgrade/upgrade selection passed with `2 passed`;
  data-bearing 049/050 round trips preserve compatible state, while unsafe
  public COW downgrade refuses before mutation.
- The full Agent mutation suite is included in the final integration run and
  the final full integration suite passed `158` tests.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 265 files already formatted.
- `uv run --frozen mypy`: PASSED — 248 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 521 tests, 1 existing Starlette/httpx deprecation warning.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 158
  tests in 21m14s.
- Focused Agent locale/navigation journey: PASSED — `1 passed, 36
  deselected`.
- Focused structural race/cancellation test: PASSED — `1 passed, 36
  deselected`.
- Focused migration downgrade/upgrade selection: PASSED — `2 passed`.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  58 tests.
- `python tools/check_repository.py`: PASSED — repository policy.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; CLI
  11.16.0.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 373 files, 0
  issues.
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`:
  PASSED.
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
- `sudo -n sh tools/compose/smoke.sh slaif071localtest`: PASSED — clean
  Compose deployment, public Agent locale/navigation acceptance, restart,
  recovery, edge, packaging, security, and browser checks; final
  `compose-smoke: OK`.

No required local gate was skipped, weakened, replaced, or treated as passed
from an incomplete run.

## GitHub CI / required checks

For implementation head `c294a8696312a0bba4a6883af094d354561a3601`, CI
workflow run `33899544940` and CodeQL workflow run `33899544816` were
inspected. Every current check was terminal `pass`:

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

`gh pr checks 74` showed all listed checks as `pass`. PR #74 is currently
`OPEN`, `MERGEABLE`, and `CLEAN`; the coding agent did not merge it.

## Local setup / dependencies

- Existing frozen uv and pnpm environments were used.
- Disposable PostgreSQL fixtures and the clean Compose stack used passwordless
  sudo only for routine test infrastructure.
- No production dependency, image, lockfile, exception, or foundation version
  changed. Foundation use remains through qualified `agentcow.postgres` public
  APIs.
- No production systems, data, credentials, capabilities, cookies, or private
  artifact URLs were accessed, printed, or committed.

## Documentation and governance

- `oap/active` and the exact 077-g order bytes were committed byte-for-byte as
  supplied by strategy. Coding did not author, rewrite, or supersede either
  strategic artifact.
- No architecture, constitution, communication protocol, historical report,
  prior order, or unrelated strategic artifact was rewritten.
- This report is the sole report publication file and is intended to be
  committed as a report-only child of the literal implementation SHA.

## Safety and scope confirmations

- Unrelated files changed: `NO`.
- Production systems/data accessed: `NO`.
- Real secrets/capabilities/cookies/private credentials printed or committed:
  `NO`; tests used disposable fixtures and fake credentials.
- Required checks skipped, weakened, or replaced: `NO`.
- Scope deviation: `NO`; no redirect Agent API, dynamic Render/router
  behavior, composition/design/Puck, media/MCP, freeze/review/promotion,
  078+, cleanup, refactor, dependency, image, exception, architecture, or
  historical-artifact work was added.
- Extra objective PR: `NO`.
- Coding-agent merge or auto-merge: `NO`.
- Report publication commit changes only this report: `YES`.

## Known limitations / completion condition

No 077-g implementation blocker remains. PR #74 remains open because coding
agents never merge objective PRs and `COMPLETE` is not strategic acceptance.
Objective 077 remains open until this slice and the remaining ordered 077
scope are accepted through the repository governance process.

Objective 077 / PR #74 may be declared complete only when strategy
independently verifies this report-only `SELF` child, its exact parent/path,
and all fresh report-head checks, then obtains the required human review,
merges PR #74 to verified remote `main`, and verifies the merged main state.
Until that strategic/human merge and verification occurs, this is a delivered
077-g implementation round, not objective acceptance.

Report publication commit: SELF
