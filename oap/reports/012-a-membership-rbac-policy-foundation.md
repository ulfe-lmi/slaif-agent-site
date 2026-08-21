# OAP Coding-Agent Report — 012-a

## Work order

- Identifier: `012-a`; work-order file:
  `oap/orders/012-a-membership-rbac-policy-foundation.md`; numeric objective:
  `012`
- PR mode: `CREATED_NEW_PR`

## Status

COMPLETE

## Executive summary

Established the non-HTTP, site-scoped human membership and RBAC foundation.
Revision `014_001` adds owner-controlled normalized catalogs, seven built-in
roles, memberships, permission overrides, fixed-search-path authorization and
actor-aware mutation functions, and least-privilege grants. Frozen typed
application models expose only server-created trusted site context and stable
fail-closed service reasons. Exact catalog, role, isolation, publication,
atomicity, concurrency, lifecycle, migration, and privilege evidence is
executable against PostgreSQL.

The initial fresh GitHub generation exposed one locale-dependent ordering bug
in all five PostgreSQL jobs. The failure was diagnosed before any retry, and
the order-authorized corrective generation made textual SQL ordering explicit
with `COLLATE "C"`. The fresh corrective generation completed 20/20 green with
no workflow rerun.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#24](https://github.com/ulfe-lmi/slaif-agent-site/pull/24); state: `OPEN`,
  merge state `CLEAN`, mergeable, ready/non-draft, zero reviews
- Base/head branches: `main` / `oap/012-membership-rbac`
- Starting remote SHA: `8517b7bff703b31504a868144f3526c5e0a93228`
- Implementation head SHA: `f9354c20cb5d05cf49e14f11ec260ecb15f877aa`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified after push)
- Implementation commits pushed:
  `d09f68e4dd7c9f90ee440efa05afd7f3698d16ba`,
  `f9354c20cb5d05cf49e14f11ec260ecb15f877aa`; report
  parent=implementation SHA
- New PR: yes, exactly one; amended another PR: no; workflow rerun: NO;
  corrective implementation generation: ONE; merge/close/auto-merge: NO

## Schema and constraint inventory

- `control.permission`: stable text primary key, bounded label/description and
  category, nullable delegation level constrained to 0–4, site-assignable,
  installation-only, and system-only flags with mutually consistent checks.
- `control.human_role`: stable text primary key, bounded metadata, default
  ceiling constrained to 0–4, and built-in marker.
- `control.human_role_permission`: composite role/permission primary key with
  restrictive foreign keys and allow-only defaults.
- `control.site_membership`: composite site/user primary key, restrictive
  foreign keys, built-in role, explicit 0–4 ceiling, exact `ACTIVE|INACTIVE`
  status, positive monotonic version, and creation/update timestamps.
- `control.site_membership_permission_override`: composite membership-bound
  identity plus permission key, exact `ALLOW|DENY` effect, timestamps, and a
  composite restrictive foreign key preventing cross-site substitution.
- All five relations are non-COW and owner controlled. Runtime roles have no
  direct relation privileges. Revision `014_001` has deterministic upgrade,
  repeat, downgrade, and rebuild behavior.

## Catalog and role-default inventory

- The executable catalog contains the exact architecture scope keys grouped as
  common read, L1, L2, L3, L4, human-only site governance,
  installation-only, and system-only. Installation/system rows are not site
  assignable and have no agent delegation level.
- Exact built-in roles and ceilings: `SITE_OWNER` 4, `SITE_ARCHITECT` 4,
  `SITE_DESIGNER` 3, `SITE_EDITOR` 2, `CONTENT_EDITOR` 1, `REVIEWER` 0, and
  `VIEWER` 0. Platform Administrator is not a site role.
- Defaults are exact cumulative read/L1–L4 editorial tiers. Viewer is read
  only; Reviewer adds audit/review-wide visibility without edit or publish;
  Architect has L1–L4 without publish; Owner adds site governance, membership,
  role, workspace/capability, policy, audit, domain, and publish authority.
- Permission and role matrices exist in immutable Python constants and seeded
  migration rows; unit, integration, bootstrap inventory, and repository tests
  make drift fail CI. Database-returned textual arrays use explicit C collation
  for deterministic cross-locale ordering.

## Function and grant inventory

- Owner-defined functions provide effective membership, authorization,
  catalog inspection, membership get/list, and actor-aware membership put.
  They use fixed `pg_catalog` search paths and typed fixed parameters; no raw
  SQL, native connection, relation, or arbitrary evaluator is exposed.
- `slaif_control` receives execute only on the named human-RBAC function
  signatures. Agent, editor, public, preview, render, reviewer, scheduler,
  media, and media-GC roles receive neither relation access nor function
  execution. Setup/owner authority remains separate.
- A narrow Control database factory creates `HumanAuthorizationService` from
  the existing Control pool. No HTTP route or listener was added.

## Authorization and mutation evidence

| Boundary | Executable result |
| --- | --- |
| Effective authority | Role defaults union allowed site-assignable overrides minus denied overrides; deny wins. |
| Trusted context | Frozen user/site/role/version/explicit and effective ceiling/permission/admin facts; no request constructor or credential material. |
| Site and state | Active user, site, membership, exact association, permission, and current version are rechecked from database state. |
| Failure surface | Unknown, inactive, stale, cross-site, and unauthorized cases map to stable `NOT_FOUND`, `DENIED`, `CONFLICT`, or `UNAVAILABLE` without leaked SQL or foreign-site detail. |
| Publication | Architect ceiling 4 lacks publish by default; an authorized allow adds only publish; deny removes Owner publish without changing ceiling or editorial scopes. |
| Platform Administrator | Can bootstrap the first Owner through the existing global assignment but still receives active trusted site context and never becomes a delegatable site role. |
| Member management | Owner acts only within held site authority; lower roles, self-mutation, cross-site substitution, inactive targets, and beyond-authority role/permission/ceiling grants fail closed. |
| Lifecycle | Deactivation preserves the membership row and version history and immediately denies authorization. |
| Atomicity | Expected-version updates increment once; row locks serialize competitors; stale/concurrent, cancellation, injected, constraint, and authorization failure leave membership and overrides unchanged. |

## Files changed

- Database/application: revision `014_001`, privilege inventories,
  `human_authorization` catalog/models/service, and the narrow Control service
  factory.
- Verification/policy: unit and PostgreSQL integration tests, bootstrap and
  privilege inventories, repository policy, repository checker, and the
  existing five-version CI command.
- Documentation: `README.md`, `docs/AUTHORIZATION.md`, `docs/API.md`,
  `docs/DATABASE_ROLES.md`, `docs/OPERATIONS.md`, `docs/SECURITY.md`,
  `docs/SITES.md`, and `migrations/alembic/README.md`.
- Strategic-owned transcript committed byte-identically: `oap/active` and
  `oap/orders/012-a-membership-rbac-policy-foundation.md`.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository
  tools`: PASSED — 133 files already formatted.
- `uv run --frozen mypy`: PASSED — 111 source files checked.
- `python -m compileall -q tools tests/repository`: PASSED.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 333 tests plus 22 subtests.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  52 tests.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 65
  tests in 319.33 seconds.
- Combined bootstrap, Control, and RBAC integration selection: PASSED — 30
  tests.
- Focused RBAC integration before publication: PASSED — 3 tests in 11.69
  seconds after the corrective change; the earlier focused catalog/matrix run
  also passed 7 selected cases.
- Migration upgrade/repeat/downgrade/rebuild check: PASSED; final recheck passed
  in 10.68 seconds.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — source and
  wheel distributions built.
- `python tools/check_repository.py`: PASSED.
- Changed-Markdown lint with
  `npx --yes markdownlint-cli2@0.23.2 --no-globs <nine changed files>`:
  PASSED — zero errors before report publication.
- `git diff --check`: PASSED throughout implementation.
- Immutable-governance hashes and active/order identity: PASSED.
- Conflict and locator inspection: PASSED. Secret scan: PASSED; only explicit
  fake test DSNs were present, with no real secret printed or committed.
- Local unchanged Mermaid corpus rendering: FAILED with the pre-existing
  renderer message `[object Object]`; no Mermaid diagram changed. The fresh
  authoritative GitHub Mermaid check passed.
- Deliberately not run per order: local Node, Compose, Playwright/browser,
  image, and broad SBOM. Their unchanged authoritative GitHub jobs ran and
  passed where applicable.

## Correction and GitHub CI investigation

- Initial implementation run `32446395824` and CodeQL run `32446395783`
  reached terminal state. Fifteen checks passed; PostgreSQL 14–18 each failed
  the same catalog-order assertion. No workflow rerun was requested.
- Failed-job inspection showed the exact first mismatch at catalog index 47:
  PostgreSQL default collation returned `media:gc` before
  `media-metadata:write`, unlike Python's normative code-point order.
- Corrective commit `f9354c20cb5d05cf49e14f11ec260ecb15f877aa`
  added explicit `COLLATE "C"` to deterministic permission/role ordering in
  the migration-defined functions. No policy, expectation, or test was
  weakened.
- Fresh main workflow run `32446908810`; CodeQL run `32446908931`.
- SUCCESS (20): Repository policy; Node contracts; Python 3.12, 3.13, and
  3.14; Foundation PostgreSQL 14, 15, 16, 17, and 18; Compose and edge
  packaging; Supply-chain evidence; Markdown; Mermaid; Dependency review;
  Detect supported languages; Analyze actions, python, and
  javascript-typescript; CodeQL.
- Corrective implementation-head state: 20 successful, zero failed, pending,
  cancelled, skipped, or missing. Workflow rerun: NO.
- The report-only commit may trigger fresh checks; strategy verifies SELF.

## Acceptance criteria

- Deterministic normalized non-COW catalog/membership schema and exact least
  privilege: PASSED.
- Seven roles, exact scope/default matrices, ceilings, and separated global,
  site, installation, system, and agent-delegation authority: PASSED.
- Immutable trusted context and fail-closed site/user/status/version policy,
  with publication orthogonal to ceiling: PASSED.
- Actor-aware, self/cross-site/beyond-authority-safe atomic mutation under
  conflict, concurrency, cancellation, and failure: PASSED.
- No HTTP/UI/Compose/dependency or adjacent implementation scope: PASSED.
- Exactly one ready objective-012 PR from verified main, no rerun or merge, and
  implementation-head CI at 20/20: PASSED.
- Correct final report-only commit topology: PASSED after publication
  verification.

## Safety, scope, dependencies, and documentation

- Unrelated human work changed or discarded: no. Prior OAP artifacts changed:
  no. Activated order/pointer edited by coding agent: no.
- Production systems, data, credentials, Docker socket, or unrelated host
  files accessed: no. Secrets printed or committed: no.
- Dependencies or lockfiles changed: no. Routine new setup dependencies: none;
  the existing disposable local PostgreSQL and frozen project toolchain were
  used.
- HTTP, UI, invitations, custom roles, workspaces, capabilities, content/COW,
  publication execution, Compose/edge, and identity/session behavior changed:
  no.
- Documentation records role/default/ceiling policy, permission categories,
  Platform Administrator separation, overrides/publication, lifecycle,
  versioning, cross-site/self-escalation denial, grants, institutional-tenancy
  limitation, and the deliberately unimplemented surfaces.
- Extra PR: NO. Workflow rerun: NO. Corrective generation count: ONE. Merge:
  NO. Auto-merge: NO. Close: NO.
- Report-only commit changes only this new report: yes.

## Immutable hashes

- `AGENTS.md`:
  `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`:
  `00bdd82fcec0afaf65d2fbc2a2f9fa43a7d4e9e254d7a262bea0c5bae3be6b8a`
- `ARCHITECTURE-for-agents.md`:
  `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Activated work order:
  `3c3ba5c3f3b88c229b627a3998f6ea3012f53c4e53baf589553747161afbdb40`
- Activated pointer:
  `a61d596d9d747af3ef3125c30bf40c64332ac5030fd0c9692e4712803647b746`

## Known limitations / blockers

- No blocker remains for 012-a. Authenticated Control HTTP and route-policy
  declaration remain reserved for 012-b; cross-site API/Compose security
  closure remains reserved for 012-c. Membership UI, invitations, custom
  roles, workspaces, capabilities, content, and publication execution remain
  unimplemented by design.

## Recommended strategic follow-up

Independently verify the report-only head and final 20/20 implementation
evidence. Only the strategic model may accept or merge PR #24, choose or split
the next work order, or declare the roadmap complete.
