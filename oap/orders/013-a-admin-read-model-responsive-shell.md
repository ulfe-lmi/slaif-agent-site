# OAP Work Order — 013-a

## Objective and new-PR contract

Create the unique objective-013 PR and establish the safe responsive
administration foundation: current-human site/authority read models, qualified
self-hosted UI dependencies, product-owned accessible primitives, authenticated
admin layout/dashboard, URL-owned site selection, and a responsive site
switcher. This round is read-only after login; site mutations are 013-b,
membership mutations are 013-c, and full Playwright/accessibility/security
closure is 013-d on the same PR.

- Numeric objective: `013`; round: `013-a`
- PR mode: `CREATE_NEW_PR`
- Existing objective-013 PR: none
- Base and verified remote main:
  `main` at `bea5894a48f3d57666b87194df0c76cdb091f215`
- Required branch: `oap/013-responsive-admin`
- Required title: `[OAP 013] Build responsive administration workflows`

PR #24 is merged and remote main contains its exact objective head. Unrelated
Dependabot PRs #12/#13 remain open; do not incorporate, amend, close, or merge
them. Create exactly one new ready/non-draft PR, never merge/close/auto-merge,
and never create a second objective-013 PR.

## Strategic context and boundaries

Current main has secure setup/login/session/CSRF, Platform Administrator site/
domain APIs, site-scoped built-in RBAC/membership APIs, exact Control/Editor
route declarations, Render routing shells, and clean Compose E2E. The Web
`/admin` surface only shows session facts and logout. Existing `GET /sites` is
Platform-Administrator-only; ordinary Site Owners/Viewers need a safe server-
filtered site list and own-authority read model before a site switcher can exist.

Client visibility is UX, never authorization. Every direct URL/API call remains
server-authorized. Site selection belongs in the URL/server response, not a
trusted local-storage/cookie/header/body claim. Web remains DB-credential-free.

## Bounded scope

Expected areas (minimum coherent subset; equivalent focused names allowed):

```text
services/backend/src/slaif_agent_site/db/alembic/versions/015_001_admin_read_model.py
services/backend/src/slaif_agent_site/db/privileges.py
services/backend/src/slaif_agent_site/human_authorization/**
services/backend/src/slaif_agent_site/control_api/{app,database,current_human_http,route_policy,auth_http}.py
services/backend/tests/unit/{test_current_human,test_route_policy,test_health_apps}.py
services/backend/tests/integration/{test_current_human_control_http,test_human_rbac}.py
services/backend/tests/integration/{test_database_bootstrap,test_control_database_integration}.py
.github/workflows/ci.yml
apps/web/package.json
package.json
pnpm-lock.yaml
apps/web/postcss.config.mjs and Tailwind-compatible CSS/config
apps/web/src/components/ui/**
apps/web/src/admin/**
apps/web/app/admin/**
apps/web/app/styles.css only for compatible shared tokens/base behavior
apps/web/tests/**
tests/contracts/** only for shared response fixtures if needed
supply-chain/** and THIRD_PARTY_NOTICES.md only for exact dependency policy/evidence
tools/check_repository.py
tests/repository/test_repository_policy.py
docs/{ADMIN,API,AUTHORIZATION,CONFIGURATION,SECURITY,TESTING}.md
README.md
oap/active
oap/orders/013-a-admin-read-model-responsive-shell.md
oap/reports/013-a-admin-read-model-responsive-shell.md
```

No site/domain/archive mutation UI, membership mutation UI, user creation/
invitation, custom roles, content editor/model/pages, Puck, workspace/capability,
agent/review/audit UI, publication, Compose/edge topology, demo seed, OIDC/MFA,
dependency upgrade unrelated to the admin UI, external font/icon/CDN/telemetry,
or adjacent product feature. Do not edit prior OAP artifacts.

## Requirements

### 1. Current-human site and authority read model

Add revision `015_001` after `014_001` with the minimum owner-controlled,
fixed-search-path, `PUBLIC`-revoked, exact-Control-granted read functions needed
for:

```text
GET /api/control/v1/me/sites
GET /api/control/v1/sites/{site_id}/my-authority
```

`/me/sites` authenticates the current human session. A current Platform
Administrator receives all sites, including archived status for governance,
with no synthetic site membership. An ordinary active user receives only sites
where both site and membership are ACTIVE. Results are deterministic and expose
only safe summary fields: site UUID/key/display name/status/default locale/
canonical revision plus optional current role, membership version, explicit/
effective ceiling, and Platform Administrator flag.

`/my-authority` resolves the server-parsed path site and current human only.
Platform Administrator may inspect any existing site and receives an explicit
global-admin fact without a fabricated role/membership/ceiling. A normal user
receives a result only for its exact active site membership, including current
role/version/ceilings/effective permission keys. Unknown, archived-for-member,
inactive, disabled, or cross-site cases return constant 404/403 without another
site's membership facts.

Neither route accepts a user ID, role, site ID outside the path, Host,
forwarded header, query authority, permission claim, expected version, or
mutation input. Both require one valid session, no CSRF, use private/no-store/
noindex headers and one request ID, and map 401/404/503 safely. They expose no
username/email/password/session/cookie/token/digest/DB locator.

Amend the route registry with exactly these two authenticated read declarations.
Add exact relation/function/grant/route inventories, upgrade/repeat/downgrade/
rebuild, cross-site, role variance, Platform Administrator without membership,
archived/inactive, disabled-user, cancellation, and redaction tests using actual
`slaif_control` on PostgreSQL 14–18. No direct relation access is granted.

### 2. UI dependency qualification and reproducibility

Add only the minimum actually used permissive dependencies for the architecture-
mandated admin stack:

- Tailwind CSS OSS integrated into the existing Next.js build without CDN;
- in-repository shadcn/ui-style source components owned/reviewed by this repo,
  not a runtime service or opaque generated persistence layer; and
- only the exact Radix primitives used for keyboard/focus-safe site switching
  or mobile navigation.

Use official npm registry packages, exact versions in `pnpm-lock.yaml`, and
verify package existence, integrity, license, transitive inventory, Node 24/
React/Next compatibility, server/client boundary, build, and no install/
postinstall telemetry. Do not upgrade Next/React/Playwright or add unused UI/
icon/animation/form/state libraries. Use local SVG/logo and system/local fonts;
no remote assets.

Update license policy/third-party notices/SBOM inputs only where exact new
packages require it. All must be allowed permissive licenses and work fully
self-hosted. Preserve strict nonce CSP: no unsafe-inline/eval, CSS-in-JS runtime,
inline style requirement, arbitrary HTML, or external origin.

### 3. Product-owned accessible admin primitives

Create a small in-repo component layer sufficient for this round—buttons,
links, cards, badges/status, form/select trigger as needed, skeleton/loading,
empty/error panel, desktop sidebar/top bar, and Radix-backed mobile navigation/
site switcher. Keep components typed, composable, visually coherent with the
SLAIF design/logo, and independent from persistence/authorization.

Use semantic HTML, landmarks, one H1, visible labels, skip link, keyboard focus,
Escape/focus-return for overlays, no focus traps outside an open dialog, minimum
touch targets, reduced-motion respect, color/token contrast, and no horizontal
overflow at 320 px. Icon-only controls require accessible names. Do not rely on
color or hidden client controls for safety.

Tailwind/admin tokens must not break the existing public landing, setup/login,
routing shell, strict CSP, or current responsive styles. Avoid a broad public-
site redesign.

### 4. Authenticated admin shell, dashboard, and URL-owned site switcher

Replace the placeholder `/admin` view with an authenticated responsive shell
that uses same-origin `credentials: same-origin` fetches to the current session
and new read routes. It must never expose or persist the session token, CSRF
token, user UUID, permissions, or selected site in local/session storage.

Required behavior:

- missing/expired/revoked session redirects safely to `/login` without flashing
  protected data; logout retains bound CSRF and cookie clearing;
- dashboard shows truthful implemented state, site count/status summaries,
  current session/recent-auth summary, and clear next actions—no invented
  content/workspace/review metrics;
- site switcher lists only server-returned sites, marks archived/global-admin/
  member role facts honestly, is keyboard/phone usable, and navigates by URL;
- `/admin/sites/{site_id}` (or one equivalent canonical URL) loads the current
  server authority and a read-only site overview; direct unknown/non-member IDs
  show a constant access/not-found state and never fallback to URL data;
- navigation exposes implemented Dashboard, Sites, and Users & Permissions
  destinations as appropriate for current authority; planned Content/Models/
  Pages/Structure/Design/Media/AI Sessions/Reviews/Audit may appear only as
  clearly disabled “planned” items, never working/fake links;
- Platform Administrator sees governance affordances based on the explicit
  global flag; ordinary members see only permissions returned for that site;
  controls hidden by UX would still be server-denied if crafted; and
- loading, zero-site, zero-membership, archived, 401, 403/404, 409, 422, 503,
  and network failure have stable non-leaking states without infinite spinners.

This round has no create/update/delete form. Do not add a client-auth token,
client role calculation, global mutable authority store, service worker, or
telemetry.

### 5. Executable evidence

Backend unit/integration must prove both routes for Platform Administrator,
Owner/Architect/Viewer with different sites, inactive/disabled/archived/cross-
site users, forged inputs, exact response fields/ordering/private headers, and
least privilege. Route-policy actual/declaration equality remains exact.

Web/Node tests must cover response validation, same-origin request options,
session redirect, URL-owned selection, permission-driven navigation, Platform
Administrator without membership, member-only sites, direct access denial,
loading/empty/error/archived states, overlay keyboard/focus semantics, no
storage/token/remote origin, CSP-compatible build output, 320 px structural
contract, and no regression to public/auth surfaces. Use component/server render
tests available in the existing toolchain; do not add a large testing library
only for this round.

Run complete Node lint/format/type/test/build and license inventory. Add the new
backend integration file to PostgreSQL 14–18 without removing existing tests or
changing the established 20 check names. Local Compose/Playwright are deferred
to 013-d; GitHub's unchanged packaging job must remain green.

### 6. Documentation and claim discipline

Document the admin information architecture, implemented/read-only round,
current-human API schemas/statuses, URL site-selection model, server-versus-UX
authorization, responsive/accessibility conventions, UI dependency/license/
self-hosting choices, and loading/error behavior. State exactly that site and
membership mutations remain API-only until 013-b/c, user creation/invitations/
custom roles are absent, and content/Puck/workspaces/review/publication are not
implemented.

## Acceptance criteria

1. Two server-owned read routes return only the current human's globally or
   site-authorized summaries with exact least privilege and cross-site denial.
2. Tailwind, in-repo shadcn-style source, and only used Radix primitives are
   exact, permissive, locked, self-hosted, CSP-compatible, and supply-chain
   qualified.
3. `/admin` and canonical site overview provide authenticated responsive,
   keyboard-accessible dashboard/navigation/site switching with truthful
   loading/empty/error/archived states and URL-owned selection.
4. Client visibility never becomes authority; no token/permission/site claim is
   trusted or stored, and direct crafted access is server-denied.
5. No mutation UI/Compose/browser/content/workspace/review/dependency-upgrade or
   adjacent scope enters; current product flows remain green.
6. Exactly one ready objective-013 PR exists with correct report-only structure
   and current-head CI 20/20 green, no rerun/merge/auto-merge.

## Verification, autonomy, and report

Target 65 minutes; hard stop 90 minutes. Audit API response and UI dependency/
CSP plans before mutation. Run focused backend and real PostgreSQL tests; Ruff
check/format on all changed Python/test/tool files; mypy/compile; migration and
grant inventory; full pnpm frozen install/lint/format/type/test/build/licenses;
repository/packaging/supply-policy checks; changed Markdown/order/report lint;
`git diff --check`; dependency/remote-origin/telemetry/secret scans. Do not run
local Compose, Playwright/browser, images, or broad SBOM beyond established
policy commands.

No blind reruns. Fix diagnosed local defects within scope, then push one coherent
initial generation. One corrective generation is allowed only for a concrete
clean-runner/PostgreSQL/browser-engine build defect; never workflow-rerun or
weaken tests/CSP/auth. Publish honest `PARTIAL` at the hard stop. Use passwordless
sudo only in the disposable VM; access no production credential/system/data.

Create the exact branch and one ready PR from verified main, commit intended
paths only, preserve order/active bytes, and never merge. Atomically publish:

```text
oap/reports/013-a-admin-read-model-responsive-shell.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
PR/head/draft; migration/function/grant/route and response matrices; dependency/
version/license/integrity inventory; component/admin route/state/accessibility/
storage/CSP evidence; exact local commands; five-version and 20-check state;
corrections/failures/skips; docs/security/scope; hashes; and explicit no-extra-
PR/no-rerun/no-merge. Signal exact FIFO `OK` only after report and claimed
remote state exist.
