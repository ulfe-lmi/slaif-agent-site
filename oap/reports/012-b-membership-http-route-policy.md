# OAP Coding-Agent Report — 012-b

## Work order

- Identifier: `012-b`; work-order file:
  `oap/orders/012-b-membership-http-route-policy.md`; numeric objective: `012`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Amended the existing objective-012 PR with a fail-closed Control HTTP surface
for the built-in role/permission catalogs and site membership lifecycle. The
change also repairs the underlying transaction so actor authority is locked and
rechecked before mutation and inactive responses report the target user's real
Platform Administrator fact. An immutable typed route-policy registry now
covers every actual Control and Editor route exactly and makes missing, stale,
duplicate, or structurally inconsistent declarations fail application startup
and repository tests.

The implementation generation completed 20/20 GitHub checks successfully. No
corrective generation or workflow rerun was required.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#24](https://github.com/ulfe-lmi/slaif-agent-site/pull/24); state: `OPEN`,
  merge state `CLEAN`, mergeable, ready/non-draft, zero reviews
- Base/head branches: `main` / `oap/012-membership-rbac`
- Starting remote SHA: `b6ed1080dd0f6036207b7a7c0d960267d3289fbb`
- Implementation head SHA: `68e6484d4630a506f6e1f99e932f1e518172ed13`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified after push)
- Implementation commit pushed:
  `68e6484d4630a506f6e1f99e932f1e518172ed13`; report
  parent=implementation SHA
- New PR this turn: no; amended existing PR: yes; workflow rerun: NO;
  corrective implementation generation: NONE; merge/close/auto-merge: NO

## Lock and trusted-context repair

- `slaif_membership_put` locks the active site, actor and target users in UUID
  order, actor and target Platform Administrator assignments in UUID order,
  actor and target memberships in UUID order, and their override rows in stable
  order before authority evaluation or mutation. The site lock serializes all
  product membership mutations for the same site.
- Actor account state, global-administrator assignment, effective membership,
  permissions, ceiling, and version are evaluated from the locked transaction
  state. A concurrent actor downgrade, permission deny, account disable, or
  membership reversal cannot race through a grant with stale authority.
- The target Platform Administrator fact is calculated independently. Active
  and inactive membership get/list/mutation responses return the target's real
  fact, never the actor's fact.
- Transaction rollback, deadlock, and serialization failures map to the stable
  `CONFLICT` service reason. The post-mutation membership record is fetched in
  the same transaction.

## Route and policy inventory

Exactly seven authenticated Control routes were added:

| Method | Path | Policy and result |
| --- | --- | --- |
| `GET` | `/api/control/v1/roles` | Bound session; exact built-in role catalog. |
| `GET` | `/api/control/v1/permissions` | Bound session; exact permission catalog. |
| `GET` | `/api/control/v1/sites/{site_id}/memberships` | Platform Administrator or active same-site `membership:manage` plus `role:manage`; deterministic list. |
| `GET` | `/api/control/v1/sites/{site_id}/memberships/{user_id}` | Same authority; exact same-site record. |
| `POST` | `/api/control/v1/sites/{site_id}/memberships` | Same authority plus bound CSRF; creates one active membership and returns `201`. |
| `PATCH` | `/api/control/v1/sites/{site_id}/memberships/{user_id}` | Same authority plus bound CSRF and required expected version; complete replacement. |
| `DELETE` | `/api/control/v1/sites/{site_id}/memberships/{user_id}` | Same authority plus bound CSRF and required expected version; semantic deactivation, never hard delete. |

- The immutable registry contains 25 declarations: 23 Control policies and two
  Editor health policies. It covers four health endpoints, five Control setup/
  login/session endpoints, nine Platform Administrator site/domain endpoints,
  two authenticated catalogs, and five site-authorized membership route-method
  pairs.
- Each declaration binds process, exact method/path template, read/mutation
  class, session and CSRF requirements, authority kind, policy kind, and exact
  permission tuple. Registry construction rejects unknown/non-site permissions,
  duplicates, malformed paths, and inconsistent session/CSRF/authority shapes.
- Startup recursively inventories actual FastAPI routes and rejects missing,
  stale, duplicate, or handler-shape-mismatched declarations. Agent routes are
  not an entry in this Control/Editor registry. Unregistered `HEAD` and
  `OPTIONS` requests receive `405`.

## Request, response, and status inventory

- Create requires target UUID, exact built-in role, ceiling 0–4 within that
  role's default, and explicit complete allow/deny permission sets. Update also
  requires positive expected version and exact status. Delete requires a
  positive expected-version query value and retains role, ceiling, and
  overrides while setting `INACTIVE`.
- Request models are frozen and reject extra/forged fields, unknown roles or
  permissions, overlapping allow/deny sets, omitted replacement sets, invalid
  ceilings, and invalid versions with `422`.
- Responses deterministically expose site and target UUIDs, role, explicit and
  effective ceilings, status, version, sorted explicit allow/deny sets, sorted
  effective permissions, target Platform Administrator fact, and timestamps.
- Authentication and site selection remain server trusted. Reads require a
  current strict session; mutations require the same session and CSRF binding.
  Non-administrator actors must have a current active membership and both
  management permissions. Self-mutation is denied at HTTP and database policy.
- Stable errors are `401` for missing/invalid sessions, `403` for denied
  authority or CSRF, `404` for unknown/inactive/cross-site resources, `409` for
  stale or concurrent mutation, `422` for malformed input, and `503` for
  unavailable database/service state. SQL and foreign-site details are not
  exposed.

## Files changed

- Database/domain: revision `014_001`, human-authorization catalog, models,
  service, exports, and Control database adapter protocol.
- HTTP/policy: Control membership routes, immutable route-policy registry,
  Control and Editor application wiring, and private-path classification.
- Verification/policy: route-policy unit tests, real PostgreSQL Control HTTP and
  concurrency tests, expanded RBAC concurrency/target-fact tests, health and
  package inventories, repository policy/checker, and the existing five-version
  CI integration selection.
- Documentation: `README.md`, `docs/API.md`, `docs/AUTHORIZATION.md`,
  `docs/DATABASE_ROLES.md`, `docs/OPERATIONS.md`, `docs/SECURITY.md`,
  `docs/SITES.md`, and `migrations/alembic/README.md`.
- Strategic-owned transcript committed byte-identically: `oap/active` and
  `oap/orders/012-b-membership-http-route-policy.md`.

## Acceptance-criteria evidence

### Criterion 1 — serialized actor authority and correct target facts

PASSED. Real PostgreSQL tests hold actor membership, override, and account rows,
confirm the grant waits through `pg_stat_activity`, commit revocation, and
observe fail-closed denial with the target unchanged. Grant-first and reversed
actor/target updates have serial outcomes without deadlock. Active and inactive
ordinary/administrator targets return their own exact administrator fact.

### Criterion 2 — exactly seven safe authenticated routes

PASSED. Route inventory tests assert the exact seven additions. Real HTTP tests
cover catalogs, list/get/create/update/deactivate, complete replacement,
semantic deactivation, deterministic response shape, session/CSRF requirements,
malformed input, and stable error mapping.

### Criterion 3 — complete exact Control/Editor policy declarations

PASSED. The startup validator proves exact actual/declaration equality for both
processes. Synthetic undeclared, duplicate, invalid authority/session/CSRF,
unknown-permission, wrong-mutation, and missing-request-handler cases fail
closed; Agent routes remain outside this registry.

### Criterion 4 — intended administrator, owner, and bounded-manager scope

PASSED. Real HTTP tests prove first-owner bootstrap and cross-site Platform
Administrator behavior, same-site Owner management, lower-role and inactive
denial, publish authority orthogonality, and a manager bounded by explicit
role/permission/ceiling authority. Cross-site reads are `404` and unauthorized
writes are `403` without substitution detail.

### Criterion 5 — bounded scope and unchanged adjacent behavior

PASSED. No UI, Compose, browser, dependency, lockfile, identity, content/COW,
publication execution, or packaging implementation changed. Existing auth,
site, render, package, repository, and supply-chain gates remained green.

### Criterion 6 — one ready PR and current-head evidence

PASSED. PR #24 alone remains open, ready, mergeable, and clean on the existing
objective branch. The implementation head completed 20/20 checks successfully;
no workflow rerun, extra PR, merge, close, or auto-merge occurred.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED — 44 packages checked.
- Changed-file `uv run --frozen ruff check ...`: PASSED.
- Changed-file `uv run --frozen ruff format --check ...`: PASSED — 19 paths
  already formatted.
- `uv run --frozen mypy`: PASSED — 115 source files checked.
- `python -m compileall -q services/backend/src services/backend/tests tools
  tests/repository`: PASSED.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 338 tests in 11.97 seconds.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  52 tests.
- Initial `uv run --frozen pytest services/backend/tests/integration`:
  FAILED — 65 passed, four failed, one setup error in 346.86 seconds. Every
  failure was a PostgreSQL TCP connection reset, with no assertion mismatch.
  The local PostgreSQL 16 service remained online with zero restarts, six of
  100 connections, ample memory/disk, and no crash/panic log.
- Focused confirmation of all affected bootstrap, demo-seed, and actor-lock
  tests: PASSED — seven tests in 35.96 seconds. This was run after diagnosis;
  no code or expectation changed and the unchanged broad suite was not blindly
  rerun.
- Focused real PostgreSQL RBAC plus Control HTTP after implementation fixes:
  PASSED — eight tests in 36.52 seconds.
- Exact grant-first serialization case: PASSED — one test in 4.63 seconds.
- Exact migration upgrade/repeat/downgrade/rebuild plus function/grant/catalog
  inventory: PASSED — two tests in 14.93 seconds.
- `python tools/check_repository.py`: PASSED.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-012b`: PASSED —
  source and wheel distributions built.
- Changed Markdown/order lint with
  `npx --yes markdownlint-cli2@0.23.2 --config
  /tmp/slaif-markdownlint-changed.yaml '*.md'` over nine same-filesystem copied
  files: PASSED — nine files selected, zero issues.
- `git diff --check` and staged diff check: PASSED.
- Immutable-governance hashes and active/order identity: PASSED.
- Conflict and changed-content locator/secret scans: PASSED. Matches in the
  broader repository were existing explicit fake test DSNs and scan tooling;
  no real secret was printed or committed.
- Deliberately not run per order: local Node, Compose, Playwright/browser,
  image, and broad SBOM. Their authoritative GitHub jobs ran and passed where
  applicable.

## GitHub CI / required checks

- Implementation workflow run `32450407963`; all 20 implementation-head checks
  reached terminal `SUCCESS` with zero failed, pending, cancelled, skipped, or
  missing checks. No workflow rerun or corrective generation occurred.
- SUCCESS: Repository policy; Node contracts; Python 3.12, 3.13, and 3.14
  quality and package; Foundation PostgreSQL 14, 15, 16, 17, and 18; Compose
  and edge packaging; Supply-chain evidence; Markdown; Mermaid; Dependency
  review; Detect supported languages; Analyze actions; Analyze python; Analyze
  javascript-typescript; CodeQL.
- All required green at report drafting: yes.
- The report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Existing frozen uv/Python toolchain, local disposable PostgreSQL 16 service,
  Node/npm access for the exact Markdown checker, and GitHub CLI were used.
- No sudo installation was needed. No dependency, lockfile, service topology,
  or durable setup change was introduced.

## Documentation

- Durable documentation now specifies the exact route/request/response/status
  contracts, route-policy coverage, session/CSRF and same-site authority,
  lock ordering and concurrency behavior, target administrator facts, semantic
  deactivation, least-privilege grants, operational diagnostics, and remaining
  pre-alpha limitations.
- Documentation does not claim UI, invitations, custom roles, workspace/
  capability editing, content/COW mutation, or publication execution.

## Safety and scope confirmations

- Unrelated files changed or discarded: no. Prior orders/reports changed: no.
- Activated order or `oap/active` edited by coding agent: no; their exact
  strategic bytes were only committed.
- Production systems/data/credentials, Docker socket, or unrelated host files
  accessed: no. Production secrets accessed, printed, or committed: no.
- Required tests skipped/not run: yes, only the local Node, Compose,
  Playwright/browser, image, and broad-SBOM work explicitly prohibited by this
  order; authoritative unchanged GitHub jobs supplied that evidence.
- Scope deviation: no. Dependencies/lockfiles changed: no.
- Extra objective PR: NO. Workflow rerun: NO. Corrective generation: NONE.
  Coding-agent merge/close/auto-merge: NO.
- Report commit changes only this report: yes.

## Immutable hashes

- `AGENTS.md`:
  `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`:
  `00bdd82fcec0afaf65d2fbc2a2f9fa43a7d4e9e254d7a262bea0c5bae3be6b8a`
- `ARCHITECTURE-for-agents.md`:
  `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Activated work order:
  `7a2dc46bd95a7ce7caa201ffd9540e6e0987f15e64129c961ef648a412fd8dff`
- Activated pointer:
  `3e55df0e0968cf55146cf8bb3937bde9c72b55b0bfc08f4258806cb541fb48f3`

## Known limitations / blockers

- No blocker remains for 012-b. The broad local integration invocation had
  transient connection-reset failures; every affected test passed in the
  diagnosed focused confirmation, and the clean GitHub PostgreSQL 14–18 jobs
  all passed the complete selected database gate.
- Membership UI, invitations, custom roles, workspace/capability editing,
  content/COW mutation, and publication execution remain unimplemented by
  design. Any further objective-012 continuation is selected only by strategy.

## Recommended strategic follow-up

Independently verify the report-only head and the implementation generation's
20/20 evidence. Only the strategic model may accept or merge PR #24, select or
split another work order, or declare the roadmap complete.
