# OAP Work Order — 013-c

## Objective and PR state

Amend objective-013 PR #25 with responsive site governance workflows: safe
site detail/settings reads for authorized members, Site Owner profile/domain
management, Platform Administrator site creation, and recent-auth-protected
archive. Preserve server authorization as truth. Membership workflows remain
013-d and full Playwright/accessibility closure remains 013-e.

- Numeric objective: `013`; round: `013-c`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25)
- Base/head: `main` / `oap/013-responsive-admin`
- Required starting remote head:
  `377016298b6e37659b0a9eae6f640a7685fe3c88`
- 013-b implementation parent:
  `1ecf4d402b232bba64709ba63bd95c8300b93eb5`
- Verified state: open, ready/non-draft, mergeable, no reviews/threads; correct
  report-only topology; current-head CI 20/20 successful; installed Node graph
  contains no MPL package.

Fetch and verify the exact PR/head. Amend only PR #25; never create another PR,
merge, close, auto-merge, or workflow-rerun.

## Boundaries

Current site HTTP is Platform-Administrator-only. Architecture requires Site
Owner one-site governance. Use current session plus server-derived active site
membership/effective permissions; never trust hidden controls, URL UUID alone,
Host, body/query role, or client permission state. Platform Administrator
remains the only site creator/archiver. Archive requires current recent-auth at
the server, not merely UI confirmation.

No membership/user UI, invitation, custom role, content/Puck, workspace,
capability, review, publication, DNS automation, site deletion, dependency,
lock, Compose/edge topology, or adjacent feature.

## Allowed scope

```text
services/backend/src/slaif_agent_site/control_api/{site_http,site_authority,route_policy,auth_http}.py
services/backend/src/slaif_agent_site/human_authorization/** only for reusable current-site checks
services/backend/tests/unit/{test_route_policy,test_site_unit,test_control_auth_http}.py
services/backend/tests/integration/{test_site_control_http_integration,test_membership_control_http}.py
.github/workflows/ci.yml only if an existing integration list requires the same file
apps/web/src/admin/**
apps/web/src/auth/client.ts only for shared safe CSRF/session helpers
apps/web/src/components/ui/** only minimum existing-style form/dialog primitives
apps/web/app/admin/sites/**
apps/web/tests/**
tests/contracts/** only shared response validation if needed
docs/{ADMIN,API,AUTHORIZATION,SECURITY,SITES}.md
README.md
oap/active
oap/orders/013-c-site-management-workflows.md
oap/reports/013-c-site-management-workflows.md
```

No migration/schema or new dependency is expected. If a schema change appears
necessary, stop and report rather than inventing it.

## Requirements

### 1. Exact server authority matrix

Refactor one typed reusable Control helper rather than duplicating membership
logic. Apply this exact policy:

| Route | Platform Administrator | Active site member |
|---|---|---|
| `GET /sites/{id}` | allowed | requires `site:read` |
| `PATCH /sites/{id}` | allowed | requires `site-policy:manage` |
| `GET /sites/{id}/domains` | allowed | requires `site:read` |
| domain POST/PUT/DELETE | allowed | requires `site-domain:manage` |
| `POST /sites` | allowed | denied |
| `POST /sites/{id}/archive` | allowed + recent auth | denied |

Safe reads use one session authentication; mutations use one atomic
session+CSRF decision. Non-admin authorization uses server-fetched current
membership version and the existing database permission function immediately
before the operation. Archived/inactive/disabled/cross-site/unknown cases fail
closed. Update route-policy declarations to match actual permissions/mutation/
CSRF shapes exactly; synthetic undeclared/mismatched routes must still fail.

Archive must reject a valid but non-recent session with stable 403 and no state
change. Preserve idempotent archive only for a current recent-auth Platform
Administrator. Do not expose a recent-auth override, actor/site ID, membership
version, or permission in a request. Keep response/error headers private and
secret-safe.

### 2. Typed Web client and validation

Add strict runtime validation for site/domain success responses and stable error
classification. Every mutation uses same-origin credentials and the exact CSRF
cookie/header helper; no token/permission/site state enters storage. Prevent
double submission and stale response overwrites. Normalize only for display;
the backend remains authoritative for key/hostname/path/locale validation.

### 3. Responsive site workflows

Using the existing MIT-only Tailwind/admin primitives, implement:

- `/admin/sites`: server-returned site list with status/role/global facts,
  loading/empty/error states and links to canonical URL-owned selection;
- `/admin/sites/new`: Platform-Administrator-only form for site key, display
  name, and default locale; successful create navigates to the new site;
- `/admin/sites/{site_id}`: truthful overview with public local route,
  revision/locale/status/authority and permitted next actions;
- `/admin/sites/{site_id}/settings`: profile/default-locale update form,
  domain mapping list/create/replace/remove including primary semantics, and
  archive section visible only to Platform Administrators;
- archive confirmation that names the site, explains no deletion, requires an
  explicit confirmation interaction, checks recent-auth UI state, and still
  relies on the server 403 gate.

Site Owners with returned permissions can update profile/domain only on their
site. Architect/Editor/Viewer and non-members receive read-only or constant
access-denied states; crafted requests remain server-denied. Do not show a
control based on a client-invented role. Unknown/archived/409/422/503 states are
actionable and non-leaking. Successful archive updates navigation/status and
never deletes rows.

Forms and dialogs require labels, descriptions/errors, keyboard order, visible
focus, Escape/focus return, 320 px no-overflow/touch targets, reduced motion,
and no raw HTML/inline style/external assets. Preserve strict CSP and all public/
auth/admin-shell behavior.

### 4. Evidence

Real PostgreSQL/FastAPI tests must prove the authority matrix for Platform
Administrator, Owner, Architect, Viewer, non-member, inactive/disabled member,
archived/cross-site site, stale permission version, missing/wrong CSRF, and
non-recent archive. Prove unauthorized attempts invoke no site/domain mutation
and reveal no foreign detail.

Web tests must cover response validation, CSRF, double-submit, create/update/
domain/primary/remove/archive success and every stable error state, permission-
driven visibility, direct URL denial, no storage/token/remote origin, keyboard/
dialog semantics, and 320 px structure. Run full Node lint/format/type/test/
build/licenses and existing backend quality/integration selections. Do not run
local Compose or Playwright; 013-e owns browser closure, while GitHub's unchanged
Compose job must remain green.

### 5. Documentation

Document exact UI/API authority, site create/profile/domain/archive workflows,
recent-auth/CSRF/confirmation behavior, URL selection, error/recovery states,
and implemented-versus-deferred scope. State that domain rows do not automate
DNS, archive does not delete, membership UI remains 013-d, and content/Puck/
workspaces/review/publication remain absent.

## Acceptance and workflow

Acceptance requires exact server policy, functional responsive workflows,
server-denied crafted requests, no dependency/schema/adjacent scope, and all 20
checks green. Target 65 minutes; hard stop 90 minutes.

Run affected Ruff/format/mypy/compile and real PostgreSQL HTTP tests; full pnpm
frozen install/lint/format/type/test/build/licenses; repository/supply policy;
changed Markdown/order/report lint; `git diff --check`; CSP/storage/remote/
secret scans. No local Compose/Playwright/browser/images/broad SBOM. Push one
coherent generation after local green; one corrective generation only for a
concrete clean-runner/build defect, never workflow-rerun or test weakening.
Publish honest `PARTIAL` at the hard stop.

Preserve prior transcript bytes and amend only PR #25. Atomically publish:

```text
oap/reports/013-c-site-management-workflows.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
authority/route/form/state matrices, recent-auth/CSRF/crafted negatives,
responsive/accessibility/CSP evidence, exact commands, current 20 checks,
corrections/skips/scope/hashes, and no-new-PR/no-rerun/no-merge. Signal FIFO
`OK` only after report and claimed remote state exist.
