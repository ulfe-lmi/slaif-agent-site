# OAP Work Order — 012-c

## Objective and final-round contract

Complete objective 012 on existing PR #24 with real NGINX/Playwright evidence
for the authenticated role/permission and site-membership APIs, using disposable
test-only non-authenticatable OIDC fixture identities. Close user-facing and
durable documentation claims so implemented RBAC APIs are not described as
absent. This is the planned final round; do not add membership UI or product user
management.

- Numeric objective: `012`; round: `012-c`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#24](https://github.com/ulfe-lmi/slaif-agent-site/pull/24)
- Base/head: `main` / `oap/012-membership-rbac`
- Required starting remote head:
  `44bad40aa648f32521a7216e44ffb04af256993e`
- 012-b implementation parent:
  `68e6484d4630a506f6e1f99e932f1e518172ed13`
- Verified state: open, ready/non-draft, mergeable, no reviews/threads; correct
  report-only head/parent; current-head CI is 20/20 successful with zero pending,
  failed, cancelled, skipped, or missing checks.

Fetch and verify this exact open PR/head. Amend only PR #24, keep it ready, and
never create another PR, merge, close, auto-merge, or workflow-rerun.

## Product and test boundaries

012-a/b already implement the non-COW catalogs, seven roles, membership policy,
serialized actor authority, target-correct contexts, seven Control routes, and
exact route declarations with real PostgreSQL/FastAPI tests. Clean Compose has
only the setup-created local Platform Administrator; there is intentionally no
user-creation API yet.

For end-to-end proof only, the smoke harness may insert fixed UUID OIDC fixture
accounts directly into its disposable clean test database before initial setup.
They have no password/local username/session/Platform Administrator assignment,
cannot authenticate while OIDC is disabled, are not product/demo/bootstrap seed
data, and disappear with the smoke project's volumes. Default `docker compose
up` outside the smoke harness must never create them.

## Bounded scope

```text
tools/compose/{smoke,e2e}.sh
tests/packaging/test_compose_smoke_contract.py
tests/e2e/{setup.spec,support}.ts
apps/web/app/page.tsx
apps/web/tests/surface.test.mjs
README.md
docs/{API,AUTHORIZATION,DEPLOYMENT,OPERATIONS,SECURITY,SITES,TESTING}.md
oap/active
oap/orders/012-c-membership-compose-security-closure.md
oap/reports/012-c-membership-compose-security-closure.md
```

Use the minimum subset. No backend/domain/schema/migration/role/permission/API/
route-policy/secret topology/Compose service/network/volume/edge config,
dependency/lock/image, production/demo seed, membership UI, user CRUD,
invitation/email, OIDC login, custom role, content/COW, workspace/capability,
publication, or adjacent feature may change. Preserve every prior order/report.

## Requirements

### 1. Disposable E2E fixture identities

Extend the bounded smoke/E2E harness so, after clean Compose is healthy but
before the initial browser setup action, it transactionally inserts exactly two
fixed, documented OIDC `user_account` fixtures through the disposable PostgreSQL
test administrator:

- distinct fixed UUIDs/subjects/display names;
- `identity_kind=OIDC`, ACTIVE, no local username/normalized username/password
  hash/email, and no Platform Administrator or membership row initially;
- a clearly invalid/non-routable fixture issuer and no usable credential; and
- collision/unexpected pre-existing state fails rather than overwrites.

Validate project/container name before Docker execution and use fixed SQL/
parameters without shell interpolation into SQL. Assert installation remains
uninitialized and the fixture accounts cannot use local login. Pass their UUIDs
to Playwright through the existing mode-0600 E2E secret channel as non-secret
fixture metadata; never place setup/session/CSRF/password material in command
arguments, logs, URLs, artifacts, or repository files.

After E2E, use owner-side test assertions only to verify expected membership
site/role/status/version rows and absence of fixture Platform Administrator/local
credentials. The normal smoke cleanup must destroy the project volumes. Add a
static contract proving fixture insertion exists only in the smoke/E2E harness,
not bootstrap, migrations, Compose, or product source.

### 2. Real NGINX membership/RBAC browser/API flow

Extend only the existing `setup` Playwright project/spec, preserving all six
stable login browser/device projects and their existing coverage. Through
`http://localhost:8080` and the browser's real setup-created session/cookies:

1. complete existing one-time setup and retain the bound CSRF cookie;
2. `GET /roles` and `/permissions`; verify seven exact roles/ceilings/defaults,
   stable catalog fields, nonassignable system/install scopes, private headers,
   and no credential/user-profile data;
3. obtain the pre-seeded `demo` site and the existing API-created second site;
4. create one fixture user's membership on both sites with different roles and
   ceilings, then list/get each and prove exact site-specific results;
5. create the second fixture on only one site and prove the other site returns
   constant 404 rather than cross-site detail;
6. update one membership with exact version and publication override, verify
   publish changes independently, then prove stale version returns 409;
7. prove missing/wrong CSRF returns 403 without version/state change, self-
   membership mutation returns 403, and installation/system override or ceiling
   beyond authority returns 403;
8. semantically DELETE/deactivate with exact version, verify incremented version,
   retained row/overrides, empty effective permissions, and later authorization
   denial; and
9. retain existing routed-site, archive, session-cookie, logout, replay, console,
   network, responsive/320 px, keyboard, and secret non-leak assertions.

Do not implement a fixture login or UI. Use `page.request` only with same-origin
cookies and the explicit CSRF header for mutations. Any expected 4xx response
must be classified in the existing browser observation harness rather than
silently ignoring unrelated console/network failures.

### 3. Compose/runtime policy proof

The same clean smoke generation must prove:

- only NGINX publishes 8080; Control route-policy startup validation is active;
- all seven routes traverse NGINX and retain one edge request ID plus private/
  no-store/noindex application headers;
- fixture insertion does not alter setup-token one-use behavior, demo seed,
  Render locator, restart fingerprints, or the established fail-closed Render
  corruption/recovery and broken-bootstrap tests;
- stop/start retains membership rows and does not recreate fixture users or
  reissue setup material;
- image history, rendered Compose, logs, HTML, and Playwright outputs contain no
  DB locator, setup/session/CSRF/password, or usable fixture credential; and
- concise markers report membership E2E success without printing UUIDs or
  identity details.

Keep the current negative-bootstrap and Render-recovery logic unchanged except
for mechanical invocation/signature changes required by E2E metadata. Do not
add a host port, fixture service, owner credential mount, or public test endpoint.

### 4. Truthful product status and durable docs

The localhost landing page currently lists `Membership/RBAC` under “Still
deliberately absent.” Correct it to state that secure setup/session, trusted
multi-site routing, Platform Administrator site/domain APIs, site-scoped built-
in RBAC/membership APIs, publication separation, and route-policy declarations
are implemented. Deferred text must specifically retain site/membership UI,
invitations, custom roles, content models/content, workspaces/capabilities,
editing/Puck, review, and publication execution. Do not imply production
readiness or that publication itself exists.

Add source/browser assertions that fail if RBAC/membership APIs are again called
absent or if UI/content/publication execution are overclaimed. Align README and
durable API/authorization/deployment/testing/operations/security/site docs only
where necessary. Clearly label fixture identities as disposable test harness
state, never demo/product users.

## Acceptance criteria

1. Disposable non-authenticatable OIDC fixtures exist only inside the clean
   smoke database and are safely destroyed; no product/default user is added.
2. Real NGINX browser/API E2E proves catalogs plus two-site different-role
   membership lifecycle, CSRF/self/cross-site/system/ceiling/version negatives,
   deactivation, response privacy, and no credential leakage.
3. Existing setup/auth/routing/Render recovery/negative bootstrap/six browser
   projects/restart/secret boundaries remain green and only NGINX publishes.
4. Landing and durable docs accurately distinguish implemented RBAC APIs from
   absent UI/invitations/custom roles/content/workspaces/publication execution.
5. No backend/schema/API/topology/dependency or adjacent product scope enters.
6. PR #24 alone remains ready with correct report-only structure and current-
   head CI 20/20 green, no workflow rerun/new PR/merge/auto-merge.

## Verification, autonomy, and report

Target 45 minutes; hard stop 70 minutes. Front-load shell syntax, fixed SQL/
fixture-scope review, focused packaging/source tests, and full Node lint/format/
type/test/build before one clean local Compose generation. One additional clean
generation is allowed only after a concrete diagnosed fix; no unchanged retry.
Run changed Markdown/order/report lint, repository/packaging checks,
`git diff --check`, immutable hashes, and secret/locator scans. Do not run local
PostgreSQL matrices, backend refactors, browser-worker/source experiments,
images, Mermaid, or broad SBOM; GitHub supplies unchanged gates.

Push one coherent implementation generation after local green and inspect all
GitHub checks. One corrective generation is allowed only for a concrete clean-
runner/browser-platform defect; never workflow-rerun or weaken tests. At the
hard boundary publish honest pushed `PARTIAL`. Routine tooling belongs to the
disposable VM with passwordless sudo; access no production credential/system/
data.

Preserve prior transcript bytes; commit this order and `oap/active`
byte-identically; amend only PR #24 and never merge. Atomically publish exactly:

```text
oap/reports/012-c-membership-compose-security-closure.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
PR/head/draft; fixture creation/destruction/no-credential proof; exact
role/permission/two-site membership and negative matrices; landing/docs truth;
clean Compose/Playwright six-project/restart/recovery/secret commands, markers,
results, and timings; current 20-check state; corrections/failures/skips;
security/scope/dependencies; hashes; and explicit no-new-PR/no-rerun/no-merge.
Signal exact FIFO `OK` only after report and claimed remote state exist.
