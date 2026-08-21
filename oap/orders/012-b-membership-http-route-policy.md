# OAP Work Order — 012-b

## Objective and existing-PR contract

Amend objective-012 PR #24 with the authenticated Control HTTP surface for
role/permission inspection and site membership lifecycle, plus a deterministic
Control/Editor route-policy declaration registry. Before exposure, repair two
012-a trusted-context/concurrency findings: serialize actor-authority state with
membership mutation and report the target's—not actor's—Platform Administrator
fact for inactive results.

Cross-site Compose/Playwright proof and user-facing status closure remain the
planned 012-c round on this same PR. Do not add membership UI here.

- Numeric objective: `012`; round: `012-b`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#24](https://github.com/ulfe-lmi/slaif-agent-site/pull/24)
- Base/head: `main` / `oap/012-membership-rbac`
- Required starting remote head:
  `b6ed1080dd0f6036207b7a7c0d960267d3289fbb`
- 012-a implementation parent:
  `f9354c20cb5d05cf49e14f11ec260ecb15f877aa`
- Verified state: open, ready/non-draft, mergeable, no reviews/threads; report-
  only head and parent are correct; current-head CI is 20/20 successful with
  zero pending/failed/cancelled/missing checks.

Fetch and verify the exact open PR/branch/head. Amend only PR #24, keep it ready,
and never create another PR, merge, close, auto-merge, or workflow-rerun.

## Strategic findings and trust boundaries

012-a established the exact catalogs, seven built-in roles, membership/
override persistence, `HumanSiteContext`, and actor-aware mutation function.
Two issues must be repaired:

1. a non-administrator actor's user row, membership row, and override rows are
   read for authority without row locks; a concurrent disable/deactivation/
   downgrade can race an in-flight grant;
2. the INACTIVE return branch fills `platform_administrator` from
   `actor_admin`, which describes the actor rather than the target named by the
   returned context.

Membership HTTP is human Control authority. Session cookie and CSRF proof are
authentication, not site authority. Path/body UUIDs never become context until
server lookup and current authorization succeed. Platform Administrator remains
global installation authority; ordinary site roles never become global or
agent authority. Publication remains an explicit permission.

## Bounded scope

```text
services/backend/src/slaif_agent_site/db/alembic/versions/014_001_human_rbac.py
services/backend/src/slaif_agent_site/human_authorization/**
services/backend/src/slaif_agent_site/control_api/{app,auth_http,database,membership_http,route_policy}.py
services/backend/src/slaif_agent_site/editor_api/app.py only for route-policy registration
services/backend/tests/unit/{test_human_authorization,test_control_auth_http,test_health_apps,test_route_policy}.py
services/backend/tests/integration/{test_human_rbac,test_membership_control_http}.py
services/backend/tests/integration/{test_database_bootstrap,test_control_database_integration,test_control_auth_http_integration}.py
.github/workflows/ci.yml
tools/check_repository.py
tests/repository/test_repository_policy.py
docs/{API,AUTHORIZATION,DATABASE_ROLES,SECURITY,OPERATIONS,SITES}.md
README.md
oap/active
oap/orders/012-b-membership-http-route-policy.md
oap/reports/012-b-membership-http-route-policy.md
```

Use the minimum coherent subset. No Web/UI, Compose/edge, Playwright/browser,
demo seed, user CRUD/invitation/email, OIDC, custom role designer, site create/
domain behavior, workspace/capability, content/COW, editor CRUD, audit-event
store, publication execution, RLS, dependency/lock, image, or adjacent feature.
Do not edit prior activated orders or reports.

## Requirements

### 1. Serialize actor authority and correct trusted target facts

Amend the still-unmerged `014_001` membership mutation function coherently. Use
one documented lock order that includes the active site, actor and target user
rows, actor membership row when non-administrator, actor override rows, and
target membership row before effective-authority evaluation or mutation. Avoid
deadlock-prone inconsistent user ordering; concurrent operations over reversed
actor/target pairs must either serialize or fail/retry safely, never authorize
from stale state.

Required semantics:

- if actor disable, membership deactivation/downgrade, ceiling reduction,
  permission DENY, or management/publish removal commits first, a subsequent
  grant using the old authority is denied and changes nothing;
- if an already-authorized mutation holds the relevant locks first, concurrent
  revocation waits, then both commits have a serial explanation—no grant occurs
  after revocation is visible;
- cancellation/deadlock/serialization/timeout maps safely and leaves all target
  membership/override state atomic;
- Platform Administrator checks use the locked active actor row and current
  assignment; no username/session/client claim substitutes; and
- all active and inactive returned `HumanSiteContext` fields describe the
  target. `platform_administrator` is computed from the target's current global
  assignment, never copied from actor authority. Inactive contexts remain empty-
  permission/non-authorizing evidence only.

Add deterministic PostgreSQL concurrency tests for actor membership revoke,
actor permission/ceiling reduction, actor account disable, reversed actor/
target updates, cancellation, and both target-admin/actor-admin combinations.
Retain exact expected-version and cross-site behavior.

### 2. Reusable route-policy declaration registry

Add one typed immutable registry that declares authorization policy for every
non-health Control and Editor route by exact process, HTTP method, normalized
path template, mutation/read class, session requirement, CSRF requirement,
global/site authority kind, and required permission where applicable.

At minimum support explicit policy kinds for one-time setup, public login/setup
status, authenticated session read, bound-session CSRF/logout, Platform
Administrator, authenticated catalog read, and site-permission authorization.
Health `/health/live|ready` may use one explicit shared system exemption; do not
silently skip arbitrary paths/methods. HEAD/OPTIONS generated behavior must be
handled deterministically.

Retrofit declarations for all existing Control auth and nine site-management
routes and the health-only Editor app, then declare every new membership route.
The registry is an auditable enforcement contract, not a replacement for real
handler authentication/authorization.

CI/repository tests must enumerate actual FastAPI routes and fail on missing,
duplicate, stale, method/path-mismatched, unknown-permission, or policy/handler-
shape declarations. A synthetic undeclared mutating Control or Editor route
must fail. No Agent/MCP/Render/Media route enters this registry yet.

### 3. Exact membership HTTP contract

Expose exactly these new Control routes under `/api/control/v1`:

```text
GET    /roles
GET    /permissions
GET    /sites/{site_id}/memberships
GET    /sites/{site_id}/memberships/{user_id}
POST   /sites/{site_id}/memberships
PATCH  /sites/{site_id}/memberships/{user_id}
DELETE /sites/{site_id}/memberships/{user_id}?expected_version=<positive int>
```

Roles/permissions require a valid human session but no CSRF and return only the
immutable built-in catalog/default matrix/assignability/ceiling facts; no raw DB
metadata or mutation exists. Membership reads require current Platform
Administrator or an active site membership with both `membership:manage` and
`role:manage`. All mutations additionally require the bound CSRF proof and rely
on the same transaction's actor-aware database policy.

Use frozen extra-forbid typed request/response models:

- POST body names `target_user_id`, built-in role, explicit ceiling, and
  disjoint allow/deny permission sets; it creates only and carries no expected
  version/status/site ID;
- PATCH path owns target ID; body requires current expected version plus role,
  ceiling, desired `ACTIVE|INACTIVE`, and complete replacement allow/deny sets;
- DELETE requires a positive `expected_version`, performs semantic
  deactivation/no hard delete, and returns the resulting safe inactive record or
  context with its incremented version;
- bodies cannot set actor, site, membership version result, effective
  permissions, Platform Administrator flag, timestamps, installation/system
  scopes, cookie/session context, or other user/site fields.

Responses expose only user UUID, site UUID, role, explicit/effective ceiling,
status/version, explicit overrides/effective permission keys, timestamps where
already safe, and target Platform Administrator fact if needed. They contain no
username/email/password/session/cookie/token/digest/SQL/locator.

### 4. Authentication, site authority, and stable errors

Use the existing strict session helper: safe GET uses one authenticated session;
POST/PATCH/DELETE uses one atomic session+CSRF decision. Do not duplicate cookie
parsing or touch denied sessions. Resolve the path site through trusted
persistence and current ACTIVE state; never trust Host, forwarded headers,
query/body site ID, client role, or expected version as authority.

For a non-administrator, derive current membership version server-side and call
the database authorization function for both management permissions immediately
before reading. Mutations still reassert/lock authority in the mutation function.
Platform Administrator uses the existing current global assignment plus trusted
site lookup; it does not need or gain a synthetic site role.

Stable mapping:

```text
invalid/expired/revoked session -> 401
CSRF or current authority/self-escalation/beyond-authority denial -> 403
unknown/invisible site, user, membership, or cross-site substitution -> 404
duplicate create, stale expected version, concurrent conflict -> 409
malformed/extra/unknown role/permission/ceiling/version -> 422
database/pool/timeout -> 503
```

All catalog/membership responses and errors are private/no-store/noindex with
one request ID. Do not reveal whether a hidden user/membership belongs to
another site.

### 5. Executable HTTP, registry, and concurrency evidence

Using real migrated PostgreSQL, actual `slaif_control`, real sessions/CSRF, and
the actual FastAPI app, prove at least:

- setup-created Platform Administrator reads catalogs and creates the first
  Owner membership on two sites;
- that Owner lists/gets and manages another member only on its own site;
- lower roles, inactive memberships, disabled users, archived sites,
  unauthenticated sessions, wrong/duplicate/missing CSRF, and self mutation are
  denied with exact status and no state change;
- the same user has different roles/ceilings on two sites and Site-A path/body/
  target/version/override substitution cannot read or mutate Site B;
- POST rejects duplicate membership; PATCH/DELETE require exact version,
  increment once, and stale/concurrent requests return 409;
- installation/system permission overrides and permission/ceiling beyond actor
  remain 403; publication grant/deny changes only publication;
- actor-authority revocation/disable concurrency follows the serialization law
  in §1 and target Platform Administrator facts are correct in active/inactive
  responses;
- malformed bodies/path/query, unknown role/permission, and forbidden response
  fields are handled safely;
- each success/error has private headers/request ID and no credential/SQL/foreign
  data; and
- exact actual-route registry coverage passes, while synthetic undeclared/
  mismatched mutation fails and other service routes gain no authority.

Run existing setup/auth/site/RBAC suites together. Add the new HTTP integration
suite to PostgreSQL 14–18 while preserving all prior files and exactly 20 check
names.

### 6. Documentation

Document the seven routes, request/response/status/version contract, role and
permission catalog visibility, global-admin versus site-manager chain, CSRF,
lock/serialization and target-context semantics, deactivation/no-delete,
route-policy registry, publication separation, and cross-site denial. State
that membership UI, invitations, custom roles, content, workspaces,
capabilities, and publication execution remain absent until later work.

## Acceptance criteria

1. Actor authority is locked/rechecked transactionally and all returned context
   facts describe the target; concurrency/revocation cannot authorize stale
   grants.
2. Exactly seven new authenticated routes implement safe catalog and membership
   lifecycle with correct 401/403/404/409/422/503 semantics and no hard delete.
3. Every actual non-health Control/Editor route has one exact policy declaration;
   undeclared/stale/mismatched mutation fails CI without weakening enforcement.
4. Platform Administrator and site Owner can perform only their intended scope;
   self/cross-site/beyond-authority/version/CSRF negatives are executable and
   publication stays orthogonal.
5. No UI/Compose/browser/dependency/adjacent scope enters; existing auth/site/
   Render/packaging behavior remains green.
6. PR #24 alone remains ready with correct report-only structure and current-
   head CI 20/20 green, no workflow rerun/new PR/merge/auto-merge.

## Verification, autonomy, and report

Target 60 minutes; hard stop 85 minutes. Audit lock ordering, route inventory,
and request/error matrices before broad execution. Run focused unit plus real
PostgreSQL RBAC/concurrency/Control HTTP suites; Ruff check and Ruff-format over
all changed Python/test/tool files; mypy/compile; migration repeat/downgrade/
rebuild and exact function/grant/catalog inventory; repository/packaging policy;
changed Markdown/order/report lint; `git diff --check`; immutable hash, conflict,
and secret/locator scans. Do not run local Node, Compose, Playwright/browser,
images, or broad SBOM; unchanged GitHub jobs are authoritative.

No blind reruns. Fix diagnosed in-scope local defects without arbitrary attempt
caps, but publish honest `PARTIAL` at the hard stop. Push one coherent initial
generation after local green. One corrective generation is allowed only for a
concrete clean-runner/PostgreSQL-version defect; never workflow-rerun or weaken
policy/tests. Use passwordless sudo only inside the disposable coding VM; access
no production credential/system/data.

Preserve prior transcript bytes, commit this order and `oap/active`
byte-identically, amend only PR #24, and never merge. Atomically publish exactly:

```text
oap/reports/012-b-membership-http-route-policy.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
PR/head/draft; lock/context repair and concurrency evidence; exact route/policy/
request/status/response inventories; local commands/results; five-version and
20-check state; corrections/failures/skips; docs/security/scope/dependencies;
hashes; and explicit no-new-PR/no-rerun/no-merge. Signal exact FIFO `OK` only
after report and claimed remote state exist.
