# OAP Work Order — 012-a

## Objective and new-PR contract

Create the unique objective-012 PR and implement the non-HTTP foundation for
site-scoped human membership and built-in RBAC: deterministic permission/role
catalogs, active/inactive memberships, bounded delegation ceilings, explicit
permission overrides, publication authority independent from editing/delegation,
immutable trusted human-site authorization context, and transactional actor-
aware membership policy.

This is the first of three planned bounded rounds. Authenticated Control HTTP
and the route-policy declaration registry are 012-b; cross-site API/Compose
security closure is 012-c. Do not implement either here.

- Numeric objective: `012`; round: `012-a`
- PR mode: `CREATE_NEW_PR`
- Existing objective-012 PR: none
- Base branch and verified remote main:
  `main` at `8517b7bff703b31504a868144f3526c5e0a93228`
- Required branch: `oap/012-membership-rbac`
- Required title: `[OAP 012] Establish site membership and RBAC`

PR #23 for objective 011 is merged and its head is contained by remote main.
Unrelated Dependabot PRs #12 and #13 remain open; do not modify, supersede,
close, merge, or incorporate them. Create exactly one new objective-012 PR,
ready/non-draft. Never merge, close, auto-merge, or create a second PR.

## Strategic context and hard boundaries

Current main has active/archived sites, domains, normalized trusted
`SiteContext`, global `control.platform_administrator`, secure human sessions +
CSRF, Platform Administrator site/domain APIs, an isolated public Render
resolver, and multi-site routing proof. It has no site membership, human role
catalog, site-scoped permission evaluator, or delegation ceiling.

Human RBAC and agent delegation are separate. A user may have different roles
per site. Global user status grants no site authority. `platform_administrator`
is installation authority and is never an agent-delegatable/site-role shortcut.
Publication is an explicit human permission, never implied by edit rights or
delegation level. Agent capabilities/workspaces do not exist yet.

Multi-site remains institutionally trusted application tenancy, not hostile
public SaaS, RLS, or a cryptographic tenant boundary.

## Bounded scope

Expected areas (use the minimum coherent subset; equivalent focused names are
allowed):

```text
services/backend/src/slaif_agent_site/db/alembic/versions/014_001_human_rbac.py
services/backend/src/slaif_agent_site/db/privileges.py
services/backend/src/slaif_agent_site/human_authorization/**
services/backend/src/slaif_agent_site/control_api/database.py only for a narrow service factory
services/backend/tests/unit/test_human_authorization.py
services/backend/tests/unit/{test_foundation_contract,test_control_database}.py
services/backend/tests/integration/test_human_rbac.py
services/backend/tests/integration/{test_database_bootstrap,test_control_database_integration}.py
.github/workflows/ci.yml
tools/check_repository.py
tests/repository/test_repository_policy.py
migrations/alembic/README.md
docs/{AUTHORIZATION,DATABASE_ROLES,SITES,SECURITY,API,OPERATIONS}.md
README.md
oap/active
oap/orders/012-a-membership-rbac-policy-foundation.md
oap/reports/012-a-membership-rbac-policy-foundation.md
```

No HTTP route, Web/UI, Compose/edge, demo seed, auth/session/cookie/CSRF change,
custom role designer, invitation/email, identity creation, OIDC, workspace,
capability/token, content/COW, editor, review/promotion, audit-event store, RLS,
site deletion, dependency/lock, image, or adjacent feature may change.

## Requirements

### 1. Deterministic non-COW catalog and membership schema

Add revision `014_001` after `013_001`. Add owner-controlled, non-COW Control
objects equivalent to:

```text
permission:
  stable key PK; bounded label/description; category;
  agent delegation level 0..4 or NULL; site-assignable flag;
  installation/system-only flags that cannot be membership-granted

human_role:
  stable built-in key PK; bounded label/description;
  default delegation ceiling 0..4; immutable built-in marker

human_role_permission:
  role_key + permission_key PK/FKs; allow-only deterministic defaults

site_membership:
  site_id + user_account_id PK/FKs with RESTRICT;
  built-in role key; explicit delegation ceiling 0..4;
  ACTIVE|INACTIVE status; monotonically increasing version;
  created/updated timestamps

site_membership_permission_override:
  site_id + user_account_id + permission_key PK/composite FK;
  ALLOW|DENY effect; created/updated timestamps
```

Equivalent normalized naming is acceptable. Do not use a mutable free-form JSON
permission bag, global role field on `user_account`, site-less membership,
cascade deletion, or COW. Enforce cross-site parent identity, exact statuses,
bounded keys/text/versions/ceilings, unique active assignment, and deterministic
downgrade/rebuild. Runtime roles receive no direct relation access.

Seed exactly the architecture's built-in human roles:

```text
SITE_OWNER ceiling 4
SITE_ARCHITECT ceiling 4
SITE_DESIGNER ceiling 3
SITE_EDITOR ceiling 2
CONTENT_EDITOR ceiling 1
REVIEWER ceiling 0
VIEWER ceiling 0
```

Do not seed Platform Administrator as a site role. Catalog rows and built-in
role defaults change only through platform migrations; expose no runtime create,
rename, delete, or default-permission mutation function.

### 2. Exact permission catalog and role defaults

Use the exact stable scope keys and tier boundaries in
`ARCHITECTURE-for-agents.md` §5 as the single normative catalog: common READ,
L1/L2/L3/L4 editorial scopes and the human-only site/workspace/capability/
membership/role/publication/policy/audit scopes. Preserve their spelling; do not
invent aliases or compress them into one coarse `can_edit` permission.

Classify installation/system-only scopes so membership and overrides can never
grant installation management, identity configuration, schema/COW operations,
job claims, GC, backup/restore, component code, secret access, or any other
system authority. Agent-forbidden scopes remain nondelegatable even when a human
holds them.

Deterministic role defaults:

- VIEWER: common read-only site/admin discovery, no write/governance/publish;
- REVIEWER: read/validation/preview plus review-wide read/audit visibility, no
  edit/delegation/publish by default;
- CONTENT_EDITOR: common read + exact L1 writes;
- SITE_EDITOR: common read + L1–L2 writes;
- SITE_DESIGNER: common read + L1–L3 writes;
- SITE_ARCHITECT: common read + L1–L4 writes, without membership/identity or
  publish by default;
- SITE_OWNER: all site-assignable editorial tiers plus one-site governance,
  membership/role management, workspace/capability governance, site policy,
  audit, domain management, and `site:publish` by default.

Installation site creation/archive and identity/installation management remain
global Platform Administrator operations, not membership defaults. Add an exact
code constant/fixture and migration/inventory tests so catalog or role-default
drift fails CI.

### 3. Effective authority and immutable trusted context

Implement frozen typed models and a server-created `HumanSiteContext` containing
only trusted facts: active user ID, active site ID, built-in role, membership
version, explicit/effective ceiling, effective permission set, and whether the
actor is the global Platform Administrator. It has no public constructor from a
request DTO and contains no cookie/token/digest/credential.

Effective membership authority is:

```text
role defaults UNION permitted ALLOW overrides MINUS DENY overrides
```

with DENY winning. ALLOW may include only site-assignable catalog permissions;
it can never grant installation/system-only authority. Effective delegation
ceiling is bounded by role default, stored explicit ceiling, and (for later
delegation) the actor's own ceiling/site policy. Ceiling 4 never implies
publication. `site:publish` must be tested orthogonally for every role/override.

Authorization must re-check ACTIVE user, ACTIVE site, ACTIVE membership, exact
site association, permission key, and current membership version using database
time/row state. Unknown/inactive/cross-site cases return one constant denial
without revealing another site or role. Global Platform Administrator may
authorize installation/site-governance operations through its existing current
assignment but must still receive a trusted active site context and must never
become agent-delegatable.

### 4. Actor-aware transactional membership policy

Add a narrow Control-only semantic service and fixed-search-path owner-defined
functions for role/permission inspection; membership get/list; authorize; and
membership create/update/deactivate with explicit permission overrides.

Mutation functions take trusted actor user + active site + target user and
reassert authority inside the same transaction under row locks. Required rules:

- only current Platform Administrator or an active membership with both
  membership/role-management authority may mutate memberships;
- non-administrators cannot act outside their site, modify their own membership,
  grant a role permission they do not effectively hold, grant an ALLOW for a
  non-site-assignable permission, or grant ceiling above both their own and the
  target role's default;
- an editor/reviewer/viewer cannot manage roles, ceilings, overrides, or publish;
- publication can be separately granted/denied only by an actor who currently
  holds `site:publish`, and it never changes ceiling/edit permissions;
- inactive/disabled target users cannot be activated as members;
- updates use an expected membership version and increment exactly once;
- create/update/deactivate and all override replacement are atomic; cancellation,
  conflict, constraint, or authorization failure changes nothing; and
- no function hard-deletes membership/catalog/audit-relevant rows.

Use stable typed `NOT_FOUND|DENIED|CONFLICT|UNAVAILABLE` service reasons without
SQL/driver/ID/role/other-site detail. Do not expose native connections, arbitrary
permission evaluation, relation access, or raw SQL to HTTP callers.

### 5. Executable persistence and security evidence

Using actual `slaif_control` on disposable PostgreSQL, prove at least:

- one active user holds different roles/ceilings/overrides on two sites and
  authorization never crosses them;
- every built-in role's exact effective permission set and ceiling matches the
  normative matrix;
- publication is independent: Architect ceiling 4 lacks it by default, an
  authorized explicit grant adds only publish, and DENY removes Owner publish
  without reducing Owner ceiling/editorial scopes;
- Platform Administrator can assign the first Owner; Owner can manage another
  member only within owned authority; all lower roles and self-escalation fail;
- actor cannot grant permission/ceiling it lacks, cannot grant installation/
  system scopes, and cannot substitute Site B target/member/override IDs;
- inactive membership, disabled user, archived site, stale expected version,
  concurrent updates, cancellation, and injected failure are atomic/fail closed;
- deactivation preserves history and immediately denies new authorization;
- catalogs/defaults survive upgrade, repeat, downgrade, and rebuild exactly;
  and
- Control has only named functions; agent/editor/public/preview/reviewer/
  scheduler/media/GC lack all membership/catalog relation and function access.

Add `test_human_rbac.py` to PostgreSQL 14–18 without removing any existing test
and preserve exactly the established 20 check names.

### 6. Documentation

Document role/default-permission/ceiling matrix, permission categories,
Platform Administrator separation, effective override rules, publication
orthogonality, active/inactive lifecycle, optimistic versioning, cross-site and
self-escalation denials, exact DB grants, and institutional-tenancy limitation.
State that no membership HTTP/UI, invitations, custom roles, workspaces,
capabilities, content, or publication execution exists yet.

## Acceptance criteria

1. Deterministic non-COW catalogs and membership/override tables migrate and
   validate with exact least privilege and no direct runtime relation access.
2. Seven built-in roles, exact architecture scope catalog/default matrices, and
   ceilings are executable constants; no global/site/system authority is
   conflated.
3. Immutable trusted `HumanSiteContext` and effective policy fail closed across
   site/user/status/version boundaries; publish remains independent of ceiling.
4. Actor-aware mutations prevent self/cross-site/beyond-authority escalation and
   are atomic under concurrency/cancellation/failure.
5. No HTTP/UI/Compose/dependency/adjacent scope enters; existing site/auth/
   Render/packaging behavior remains green.
6. Exactly one new ready objective-012 PR exists from verified main; report-only
   structure is correct and current-head CI reaches 20/20 with no workflow
   rerun/merge/auto-merge.

## Verification, autonomy, and report

Target 55 minutes; hard stop 80 minutes. Audit the catalog/matrix/function/grant
design before DB execution. Run focused unit/property-style truth tables and
real PostgreSQL bootstrap/auth/site/RBAC integration; Ruff check + Ruff-format
over every changed Python/test/tool file; mypy/compile; migration upgrade/
downgrade/rebuild and exact inventory; repository/packaging policy; changed
Markdown/order/report lint; `git diff --check`; conflict, immutable-hash, and
secret/locator scans. Do not run local Node, Compose, Playwright/browser, image,
or broad SBOM; unchanged GitHub jobs are authoritative.

No blind unchanged reruns. Diagnose and fix in-scope local defects without an
arbitrary attempt cap, but stop at the hard boundary with honest pushed
`PARTIAL`. Push one coherent initial implementation generation after local
green. One corrective generation is allowed only for a concrete clean-runner or
PostgreSQL-version defect; never press workflow rerun or weaken policy/tests.

Routine PostgreSQL/tool setup belongs to the disposable coding VM with
passwordless sudo. Access no production credentials, data, systems, or secrets.

Fetch/reconcile main, create the exact branch and one ready PR, commit intended
paths only, and never merge. Preserve strategic order/active bytes. Atomically
publish exactly:

```text
oap/reports/012-a-membership-rbac-policy-foundation.md
```

The final report-only `SELF` commit must parent the literal implementation SHA.
Report branch/base/PR/head/draft; schema/table/constraint/catalog/role-default/
function/grant inventories; authorization/mutation/concurrency matrices; exact
local commands/results; five-version and all-20 check state; corrections/skips/
failures; docs/security/scope/dependencies; hashes; and explicit no-extra-PR/no-
rerun/no-merge state. Signal exact FIFO `OK` only after report and claimed
remote state exist.
