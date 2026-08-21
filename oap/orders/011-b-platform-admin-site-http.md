# OAP Work Order — 011-b

## Objective and PR mode

Amend the unique objective-011 PR with the authenticated, browser-session
Control HTTP surface for Platform Administrators to create, inspect, update,
archive, and manage domain mappings for sites. Preserve the trusted site
foundation from 011-a and close its stale-context archive race. Do not add the
demo seed, public renderer routing, edge changes, or Compose multi-site proof;
those are deliberately reserved for bounded round 011-c on this same PR.

- Numeric objective: `011`; execution round: `011-b`
- PR mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- Existing PR: [#23](https://github.com/ulfe-lmi/slaif-agent-site/pull/23)
- Base/head: `main` / `oap/011-sites-trusted-resolution`
- Required starting remote head:
  `5aa4dd9c32852f40a5ffe60dd2b239871525ff16`
- 011-a implementation parent:
  `388244d03854ca7932fb25addd0a7b8be2a2da71`
- Verified current state: correct report-only head and parent; 20/20 current-head
  checks successful; no reviews or review threads; mergeable; PR remains draft
  contrary to 011-a's ready/non-draft requirement.

Fetch and verify this exact open PR/branch/head before editing. Amend only PR
#23, never merge/close/auto-merge it, and mark it ready/non-draft after the
implementation is pushed. Later 011-c may continue amending a ready PR.

## Strategic context and boundaries

011-a added non-COW `site_policy`, `site`, and `site_domain`, shared
normalization, a server-created immutable `SiteContext`, Control-only semantic
functions/service, and two-site/quota/privilege tests. It deliberately exposed
no HTTP site route. Current human HTTP provides one-time setup, local login,
server sessions, recent-auth state, strict cookie parsing, and CSRF-protected
logout. The initial user is assigned `control.platform_administrator`.

Platform Administrator is installation authority and may govern sites. Host or
path selection still grants no authority. Site membership/RBAC is objective
012; the responsive Sites/Users UI is objective 013. This round supplies only
the authenticated semantic Control API needed by those layers.

## Bounded scope

Expected areas (minimum coherent subset; equivalent focused names allowed):

```text
services/backend/src/slaif_agent_site/control_api/{app,auth_http,database,site_http}.py
services/backend/src/slaif_agent_site/identity/** only for a reusable safe HTTP helper
services/backend/src/slaif_agent_site/sites/{models,service}.py
services/backend/src/slaif_agent_site/db/alembic/versions/013_001_site_foundation.py
services/backend/src/slaif_agent_site/db/privileges.py
services/backend/tests/unit/test_site_unit.py
services/backend/tests/integration/test_sites.py
services/backend/tests/integration/test_site_control_http_integration.py
services/backend/tests/integration/test_control_auth_http_integration.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/integration/test_control_database_integration.py
.github/workflows/ci.yml
tools/check_repository.py
tests/repository/test_repository_policy.py
docs/{API,SITES,DATABASE_ROLES,SECURITY,OPERATIONS}.md
README.md
oap/active
oap/orders/011-b-platform-admin-site-http.md
oap/reports/011-b-platform-admin-site-http.md
```

Do not change web/Next.js, NGINX/Apache, Compose, images, dependencies/locks,
setup/login credential semantics, session token format, membership/roles,
workspaces/capabilities, content/COW, public rendering, DNS, RLS, deletion, or
other product modules. Do not add a public anonymous site endpoint or seed.

## Requirements

### 1. Reusable human request authentication and administrator authority

Factor or extend the existing Control HTTP boundary so every new route uses the
same strict session-cookie policy as `/session` and the same bound CSRF-cookie +
single `X-CSRF-Token` policy as `/logout`:

- safe `GET` requests authenticate the server-side human session and require no
  CSRF;
- every state-changing site/domain request authenticates the session and its
  bound CSRF proof before domain work;
- malformed/duplicate/alternate-mode cookies fail 401; missing, duplicate,
  malformed, or mismatched CSRF fails 403;
- session/user/token values never enter errors, logs, response bodies, URLs, or
  route parameters; and
- all site-admin responses, including errors, are `private, no-store` and
  `noindex` while retaining the existing stable error envelope/request ID.

Add an owner-defined, fixed-search-path, `PUBLIC`-revoked, exact-Control-granted
semantic function/method that authorizes only an ACTIVE user with a current
`control.platform_administrator` assignment. A valid session without that
assignment receives constant 403. Do not infer administrator authority from
username, setup history, email, cookie presence, Host, or client claims. Do not
grant relation access or expose a generic authorization query/native pool.

Keep auth and authorization helpers narrow and typed. Existing setup/login/
session/logout behavior and their security headers must remain byte-for-byte
compatible at the HTTP contract level.

### 2. Typed Platform Administrator site API

Expose exactly these semantic Control routes under `/api/control/v1`:

```text
GET    /sites
POST   /sites
GET    /sites/{site_id}
PATCH  /sites/{site_id}
POST   /sites/{site_id}/archive
GET    /sites/{site_id}/domains
POST   /sites/{site_id}/domains
PUT    /sites/{site_id}/domains/{domain_id}
DELETE /sites/{site_id}/domains/{domain_id}
```

Use frozen extra-forbid request/response models and UUID parsing. `POST /sites`
returns 201; successful deletion returns 204; other success codes must be
documented and stable. Responses may expose only the existing safe site/domain
record fields. No body may select `site_id`, `domain_id`, status, revision,
catalog version, timestamps, or authorization context. No route accepts a Host,
path, header, query, or body value as site authority.

Resolve every path site UUID through a trusted database/service lookup after
Platform Administrator authorization. Mutations must receive a server-created
active `SiteContext`; do not expose or use `_from_database` in handlers and do
not fabricate routing fields from client data. Add the smallest semantic
Control-context lookup/list-domain operation needed if the current service
cannot do this cleanly. Archived sites remain inspectable to Platform
Administrators but cannot be updated or have mappings added/changed/removed.

Map validation to 422, missing/invisible site or mismatched domain to constant
404, duplicate/quota/primary/state conflicts to 409, authentication to 401,
authorization/CSRF to 403, and unavailable persistence to 503. Never disclose
whether another untrusted identifier belongs to another site.

### 3. Close the 011-a stale-context archive race

`slaif_site_domain_remove` currently locks a site by ID but does not re-check
`status='ACTIVE'`; a stale `SiteContext` obtained before archive can therefore
delete a non-primary mapping afterward. Repair the database function and
semantic behavior so every profile/domain mutation reasserts ACTIVE under the
site row lock in its own transaction. Prove update, add, replace, and remove all
fail without mutation after archive, even when the caller retained a previously
valid context. Preserve idempotent archive and archive-without-row-deletion.

Because `013_001` is unmerged within this objective PR, amend that revision
coherently rather than creating a new post-013 migration. Update deterministic
downgrade, exact function/grant inventories, readiness, and bootstrap tests.

### 4. Executable HTTP/security evidence

Using real migrated PostgreSQL, actual `slaif_control`, and the real FastAPI
application, prove at least:

- first setup/login session is a Platform Administrator and can create/list/get,
  update, archive, and manage domains for two sites;
- unauthenticated, invalid/revoked/expired session, duplicate-cookie, and valid
  non-administrator requests fail with the exact 401/403 distinction;
- all mutations reject missing/wrong/duplicate CSRF while authenticated `GET`
  works without CSRF;
- extra fields and attempts to supply IDs/status/revisions/catalog fields are
  rejected before persistence;
- normalized duplicate key/domain/prefix, quota, primary mapping, and archived
  state return the documented stable conflict behavior;
- a Site-A route with Site-B `domain_id` returns constant 404 and changes
  neither site;
- stale pre-archive contexts cannot update/add/replace/remove anything;
- cancellation/database failure rolls back and returns no driver, SQL, DSN,
  cookie, token, hash, or cross-site detail;
- new paths carry one request ID plus private/no-store/noindex headers on success
  and every error; and
- Agent/Editor/public/MCP services have no site-lifecycle route or newly granted
  function/relation access.

Add the new HTTP integration suite to every PostgreSQL 14–18 matrix job while
preserving exactly the established 20 check names and every existing test file.
Keep request counts bounded and deterministic.

### 5. Documentation

Document the exact route/status/schema contract, session+CSRF+Platform
Administrator authority chain, archive/no-delete semantics, local quota and
normalization behavior, and institutional-tenancy limitation. State plainly
that UI, memberships/RBAC, demo seed, anonymous rendering/routing, DNS
automation, content, workspaces, and publication remain absent. Do not claim
that this API makes the application multi-tenant or production-ready.

## Acceptance criteria

1. Exactly the nine routes exist and every one requires a current Platform
   Administrator; state changes additionally require bound CSRF.
2. Path/body/Host/header substitution cannot forge site context or mutate a
   different site; stable errors reveal no cross-site or credential detail.
3. Every site/domain mutation rechecks ACTIVE transactionally, including the
   stale-context-after-archive case; archive deletes no row.
4. Existing auth, setup, database roles, resolver, quota, and Compose behavior
   remain green; no UI/edge/seed/membership/content/dependency scope enters.
5. PR #23 alone is amended and made ready/non-draft; no workflow rerun, new PR,
   merge, close, or auto-merge occurs; its report-only head is structurally
   correct and current-head CI reaches 20/20 green (strategy may wait on checks
   triggered by the report commit).

## Verification and autonomy

Target 50 minutes; hard stop 75 minutes. Inspect first, then run focused unit
and real-PostgreSQL site/auth HTTP suites. Run affected Ruff/format/mypy/compile,
migration upgrade/downgrade/rebuild/function/grant inventories, repository and
packaging-policy checks, changed-doc/order/report Markdownlint `--no-globs`,
`git diff --check`, conflict-marker and secret/locator scans. Do not run local
Playwright, Compose, browsers, broad image/SBOM, or unchanged Node suites; their
GitHub jobs remain authoritative. No blind unchanged reruns. Diagnose and fix
in-scope local failures without an arbitrary attempt cap, but stop at the hard
time boundary with an honest pushed `PARTIAL` report if necessary.

Push one coherent implementation generation and inspect its complete GitHub
checks. One corrective code generation is allowed only for a concrete
clean-environment/PostgreSQL-version/check defect; never press workflow rerun.
Do not weaken tests, checks, auth, headers, constraints, or errors to obtain
green.

Routine packages, PostgreSQL, compilers, and test services belong to the
disposable coding VM; passwordless sudo is available. Do not transfer setup or
log gathering to the human. Access no production system, credential, data, or
secret.

## GitHub workflow and immutable report

Verify and check out PR #23's exact remote branch/head; preserve all activated
order/report bytes; implement; commit only intended paths; push; update the
existing PR body if needed; mark it ready/non-draft; inspect checks; never create
a PR or merge. Atomically publish exactly:

```text
oap/reports/011-b-platform-admin-site-http.md
```

The last pushed commit before FIFO `OK` changes only this report and uses:

```text
Implementation head SHA: <literal 40-hex parent>
Report publication commit: SELF
```

Report exact PR/branch/base/head and draft state; commits; route/status/model
inventory; administrator/auth/CSRF/context/error/header evidence; stale-context
repair; schema/function/grant delta; exact local commands/results; five-version
and 20-check state; failures/skips/corrections; docs/scope/security/dependencies;
order/active/report hashes; and explicit no-new-PR/no-rerun/no-merge state. Commit
and push the strategic-owned order and `oap/active` byte-identically with the
objective transcript. Signal exact FIFO bytes `OK` only after the immutable
report and claimed remote state exist.
