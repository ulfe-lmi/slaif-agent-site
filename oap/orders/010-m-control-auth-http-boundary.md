# OAP Work Order — 010-m

## Objective

Amend PR `#15` with the complete backend Control HTTP authentication boundary:
safe initial-setup status/consumption, local login plus session issuance, safe
session inspection, CSRF-bound logout, exact production/development cookies,
stable secret-safe errors, and executable database/HTTP security tests.

Also add the one still-missing credential-service cancellation regression.
Do not add Next.js setup/login pages, general auth middleware for future site
routes, NGINX/Compose path changes, OIDC, MFA, user management, sites,
memberships, capabilities, publication, or audit-event persistence.

## GitHub objective state

- Numeric objective/round: `010` / `010-m`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15` — <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch/base: `oap/010-installation-local-auth` / `main`
- Current main: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR/report head:
  `30a27d306776322e1300beaa7894e245f1a01b5c`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

PR `#15` is the unique objective PR. No new PR, rebase, force-push, merge,
close, auto-merge, or unrelated action.

## Current state and boundary

Setup-token/first-admin, local credential verification, and human session/CSRF
services are implemented and proven. The Control app still exposes only health
routes. Shared FastAPI handlers suppress validation inputs/details, docs/OpenAPI
URLs are disabled, access logging is off, and production settings already
require HTTPS, strong app secret, and secure cookies.

This round wires only the authentication endpoints and their internal
dependencies. It does not claim a usable human web UI or production-ready
internet authentication. Application/database login throttling and durable
security-event audit remain explicitly deferred to later security/audit work;
do not silently implement a process-local rate limiter or depend on edge-only
authorization semantics.

## Moderate autonomy and completion rule

- Target: 55 minutes; hard stop: 80 minutes.
- Audit route/cookie/error/adapter contracts and tests before broad execution.
- No arbitrary local attempt cap. Diagnose/fix in-scope failures until all
  focused local evidence passes; no unchanged blind reruns.
- Do not push with a known failing PR-affected auth/identity/session test.
- One initial CI generation; one corrective code generation only for a genuine
  clean-environment/version issue; never workflow-rerun.
- No broad local supply-chain/image, Node, browser, or full DB matrix.

## Allowed scope

```text
services/backend/src/slaif_agent_site/db/alembic/versions/012_001_control_auth_http.py
services/backend/src/slaif_agent_site/db/privileges.py
services/backend/src/slaif_agent_site/identity/models.py
services/backend/src/slaif_agent_site/identity/authentication.py
services/backend/src/slaif_agent_site/identity/sessions.py
services/backend/src/slaif_agent_site/control_api/app.py
services/backend/src/slaif_agent_site/control_api/database.py
services/backend/src/slaif_agent_site/control_api/config.py
services/backend/src/slaif_agent_site/control_api/auth_http.py
services/backend/src/slaif_agent_site/errors.py
services/backend/tests/unit/test_control_auth_http.py
services/backend/tests/integration/test_control_auth_http.py
services/backend/tests/unit/test_identity_authentication.py
services/backend/tests/unit/test_control_database.py
services/backend/tests/unit/test_health_apps.py
services/backend/tests/unit/test_foundation_contract.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/integration/test_local_identity.py
services/backend/tests/integration/test_human_session.py
services/backend/tests/integration/test_local_authentication.py
services/backend/tests/integration/test_control_database_integration.py
.github/workflows/ci.yml
tools/compose/control_readiness.py
tests/packaging/test_compose_policy.py
tools/check_repository.py
tests/repository/test_repository_policy.py
README.md
migrations/alembic/README.md
docs/CONFIGURATION.md
docs/INSTALLATION_SETUP.md
docs/LOCAL_AUTHENTICATION.md
docs/OPERATIONS.md
docs/API.md
oap/active
oap/orders/010-m-control-auth-http-boundary.md
oap/reports/010-m-control-auth-http-boundary.md
```

Use the minimum subset; equivalent focused route/test module names are fine.
Do not change dependencies/locks, web/Next.js, edge/Compose configuration,
another service, or adjacent product modules.

## Required HTTP contract

Use these exact versioned Control routes:

```text
GET  /api/control/v1/setup/status
POST /api/control/v1/setup
POST /api/control/v1/login
GET  /api/control/v1/session
POST /api/control/v1/logout
```

Keep `/docs`, `/redoc`, and `/openapi.json` unavailable externally. Internal
`app.openapi()` must expose typed route/error/response contracts for tests.

### Setup status and setup

- Add a narrow `012_001` owner function if required to return only
  `initialized` and database-clock `setup_available`; never return token digest,
  generation, expiry, user, or internal state. Control-only execute, fixed
  search path, no direct table grant, exact downgrade/inventory.
- `GET setup/status` is unauthenticated and returns only the two booleans with
  private/no-store/noindex headers.
- `POST setup` accepts setup token, username, password, display name, optional
  email in JSON body only; never URL/query/header. Reuse the proven atomic
  first-admin operation, then issue a fresh human session for that user.
- Invalid/expired/revoked/replayed/concurrent/initialized setup shares one
  stable public failure and emits no cookie. If administrator creation commits
  but later session issuance fails, report one stable service failure; do not
  pretend setup rolled back. The new administrator can subsequently log in.
- After success, setup status is closed and replay cannot create another user.

### Login

- `POST login` accepts bounded normalized username/password JSON and calls the
  proven credential service, then creates a fresh session only after success.
- Unknown/wrong/disabled/non-local/malformed/internal/database failure returns
  one authentication envelope/status without existence/hash/status detail and
  without cookies/session rows.
- Do not echo, serialize, log, or include username/password in errors. Existing
  validation handler must suppress raw input, including malformed JSON/body.
- Do not impose new-account password policy on login credentials.

### Session inspection and logout

- `GET session` authenticates only the opaque HTTP-only session cookie via the
  safe/read session method. It does not require/accept CSRF and returns only
  minimal typed identity/session ID or public ID as policy permits,
  `recent_auth`, and absolute expiry—never session/CSRF token/digest.
- `POST logout` requires exactly one expected session cookie, exactly one
  expected CSRF cookie, and one `X-CSRF-Token` header. Reject duplicates,
  alternate production/development cookie-name confusion, missing/malformed/
  unequal header-cookie proof, wrong/cross-session proof, and invalid session
  before revoke. Compare header/cookie with `secrets.compare_digest`, then call
  the session service's CSRF-bound revoke.
- Correct logout revokes idempotently according to the service contract and
  clears both cookies with matching path/security/SameSite attributes. A wrong
  CSRF attempt must not revoke or clear the valid browser session.

## Cookie and response security

On setup/login success set exactly two cookies:

```text
production: __Host-slaif_session + __Host-slaif_csrf, Secure, Path=/, no Domain
local/test:  slaif_session + slaif_csrf, non-Secure, Path=/, no Domain
session: HttpOnly
CSRF: non-HttpOnly by design, same-origin double-submit value
both: SameSite=Lax or stricter, bounded Max-Age <= absolute session lifetime
```

No token in response JSON, URL, redirect, local/session storage, logs, traces,
or error details. Add `Cache-Control: private, no-store`, appropriate `Pragma`,
and `X-Robots-Tag: noindex, nofollow, noarchive` to setup/login/session/logout
responses, including errors where practical. Do not add permissive CORS.

Reject ambiguous duplicate cookie/header inputs before semantic authority.
Cookie parsing must not silently accept the last duplicate. Development cookie
behavior must not overclaim production security.

## Service/error architecture

- Add typed HTTP orchestration/dependencies without giving Web/MCP/other
  processes DB credentials.
- Extend the Control adapter protocol/fakes explicitly for setup status,
  first-admin, credential auth, session create/safe auth/state-changing auth,
  and revoke as used; no hidden `Any` bypass of service boundaries.
- Map domain failures to stable architecture-shaped error envelopes with
  request correlation and no internal exception/driver/cookie detail.
- Preserve liveness independence and readiness failure behavior.
- Add the missing unit regression proving `asyncio.CancelledError` from local
  credential lookup/CAS propagates and does not trigger dummy retry/CAS/session.

## Required executable evidence

Unit/ASGI tests must prove:

- exact route set, methods, schemas, disabled public docs;
- setup status safe shape and headers;
- setup success/failure/replay/concurrency mapping and no token leakage;
- login success/denial and cookie attributes in production/local modes;
- no cookie/session creation on denial;
- GET session uses no CSRF and exposes minimal response;
- logout valid, duplicate/missing/wrong/cross-session CSRF, cookie-name
  confusion, idempotency, clear-cookie attributes, and unchanged state on deny;
- validation/malformed body suppresses plaintext/password/token;
- database/service/cancellation failures are stable and secret-safe.

Disposable PostgreSQL/ASGI integration must run setup→session, logout/replay,
fresh login→session, wrong/unknown/disabled denial, CSRF substitution, expiry/
revoke, and prove exact identity/session row outcomes. Run the existing five
identity/session/auth/bootstrap/control files plus the new HTTP integration
together locally and in each PostgreSQL 14–18 CI job.

## Documentation and claim discipline

Update README/API/setup/local-auth/config/operations/migration docs from
“health-only/no auth routes” to the exact implemented backend API. Continue to
say no human Next.js setup/login UI, NGINX/Compose end-to-end auth proof, OIDC,
MFA, app/database login rate limiting, durable security-event audit, sites, or
user management exists. Preserve the 400×400 centered logo block unchanged.

## Observable acceptance criteria

1. Setup token is body-only, one-use, and closes setup; success issues one
   session, failure/replay leaks nothing and issues none.
2. Login denials are non-enumerating and secret-safe; success alone creates a
   session and exact cookies.
3. Safe session GET needs no CSRF; every state-changing logout requires the
   correct session-bound double-submit CSRF and cannot be bypassed with
   duplicate/alternate cookies.
4. Cookie flags/names/clearing/no-store/noindex are correct for production and
   local modes; no token appears in body/URL/log/error/storage.
5. Cancellation and service/database failures propagate/map safely without
   partial session/identity mutation.
6. Existing and new complete integration sets pass locally and on PostgreSQL
   14–18; all other required checks pass.
7. No Next.js/edge/Compose/adjacent feature or dependency enters.
8. Exactly PR #15 is amended; report head is 20/20 green, no workflow rerun,
   report-only `SELF` is correct.

## Verification required

Run focused unit/ASGI tests, then complete disposable-PostgreSQL identity/
session/auth/HTTP integration until green after concrete fixes. Run affected
Ruff/format/mypy/compile, migration/object/grant/repository/packaging checks,
secret/repr/log/URL/cookie scans, explicit changed-doc/report Markdownlint
`--no-globs`, exact paths/prior hashes, no conflict markers, and
`git diff --check`.

Do not run broad supply-chain/image, Node, browser, or full local DB version
matrix. Run local Compose only if a packaged-head fixture changes. GitHub runs
the updated PostgreSQL 14–18 set and complete 20 checks. Lint the exact final
report before publication.

## Safety, workflow, and report

Fake credentials/tokens and disposable PostgreSQL only; no production access or
secret output. Preserve governance, architecture, OAP history, setup/identity/
session/role boundaries.

Amend only the existing PR. Atomically publish exactly:

```text
oap/reports/010-m-control-auth-http-boundary.md
```

The linted report-only `SELF` commit must parent the literal implementation
head. Report endpoints/schemas/errors/cookies/headers; all setup/login/session/
logout/CSRF/cancellation cases; exact row outcomes; complete local/five-version
CI and 20 report-head checks; corrections/paths/hashes/skips; no-workflow-rerun/
no-new-PR/no-merge state; and `Report publication commit: SELF`.
