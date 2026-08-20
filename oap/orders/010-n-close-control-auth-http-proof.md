# OAP Work Order — 010-n

## Objective

Amend PR `#15` to close the backend Control authentication HTTP boundary with
real PostgreSQL-backed ASGI flows and complete cookie/header/error security.
Repair missing duplicate-header rejection, auth-error no-store/noindex headers,
logout status/CSRF semantics, production/local cookie tests, and every unproven
setup/login/session/logout row outcome.

Do not add Next.js UI, NGINX/Compose configuration, OIDC, MFA, login rate
limiting, durable audit events, sites, memberships, capabilities, publication,
or another feature.

## GitHub objective state

- Numeric objective/round: `010` / `010-n`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15` — <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch/base: `oap/010-installation-local-auth` / `main`
- Current main: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR/report head:
  `04fc450cb144c91e9d42f78cf527afe759631155`
- `010-m` implementation head:
  `12bf357bd232081e5feb068b85443f1a7dab20ce`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

No new PR, rebase, force-push, merge, close, auto-merge, or unrelated action.

## Strategic findings

1. The only real PostgreSQL-backed HTTP assertion added in `010-m` is
   `GET /api/control/v1/setup/status`. Setup, login, session, logout, cookie,
   and CSRF behavior are tested only with permissive fakes.
2. No test covers setup POST success/failure/replay/concurrency or proves
   identity/session rows; no real login→session→logout flow exists.
3. `_cookie_values` reads one combined header and ignores malformed cookie
   fragments; duplicate raw `Cookie` headers are not explicitly rejected.
4. FastAPI binds `X-CSRF-Token` to one string without rejecting duplicate raw
   header instances.
5. `_secure_headers(response)` applies only to the normal route response. When
   a route raises, the global error handler creates a new response and auth
   failures can lose Cache-Control/Pragma/X-Robots-Tag.
6. Logout defaults to HTTP 200 with a JSON null body rather than an explicit
   empty 204 response.
7. Wrong/missing CSRF currently maps to authentication-required 401. Use one
   non-enumerating 403 authorization denial for syntactically complete logout
   attempts that fail CSRF; missing/invalid session on session inspection stays
   401. Do not leak session existence through different CSRF details.
8. Documentation/report wording must recognize that NGINX's existing
   `/api/control/` route makes these backend endpoints externally reachable in
   the default topology even though no human UI/E2E proof exists yet.

## Moderate autonomy and completion rule

- Target: 45 minutes; hard stop: 70 minutes.
- Audit the complete route/error/cookie/test slice first.
- No arbitrary local attempt cap. Fix in-scope failures until the complete
  local unit and PostgreSQL/ASGI set passes; no unchanged blind reruns.
- Do not push while a required PR-affected auth test is known failing.
- One initial CI generation; one corrective code generation only for a genuine
  clean-environment/version-only defect; never workflow-rerun.
- No broad local supply-chain/image, Node, browser, or full DB matrix.

## Allowed scope

```text
services/backend/src/slaif_agent_site/control_api/auth_http.py
services/backend/src/slaif_agent_site/control_api/app.py
services/backend/src/slaif_agent_site/control_api/database.py
services/backend/src/slaif_agent_site/errors.py
services/backend/tests/unit/test_control_auth_http.py
services/backend/tests/unit/test_errors.py
services/backend/tests/unit/test_health_apps.py
services/backend/tests/integration/test_control_auth_http.py
services/backend/tests/integration/test_control_database_integration.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/integration/test_local_identity.py
services/backend/tests/integration/test_human_session.py
services/backend/tests/integration/test_local_authentication.py
.github/workflows/ci.yml
tools/check_repository.py
tests/repository/test_repository_policy.py
README.md
docs/API.md
docs/INSTALLATION_SETUP.md
docs/LOCAL_AUTHENTICATION.md
docs/OPERATIONS.md
oap/active
oap/orders/010-n-close-control-auth-http-proof.md
oap/reports/010-n-close-control-auth-http-proof.md
```

Use the minimum subset. No migration, grant, dependency/lock, web/Next.js,
edge/Compose config, or adjacent product module may change unless real
PostgreSQL proof exposes a direct defect in existing `012_001`; report before
broadening.

## Requirements

### 1. Strict request credential parsing

Inspect raw ASGI headers. Reject multiple `Cookie` header instances, duplicate
expected cookie names within one header, malformed cookie pairs, both local and
production session/CSRF names, multiple `X-CSRF-Token` headers, empty tokens,
and unexpected alternate-name ambiguity before semantic authority. Do not
silently take first/last. Ignore unrelated well-formed cookies only when they
cannot affect authentication.

Keep safe `GET session` session-cookie-only. For `POST logout`, require exactly
one expected session cookie, one expected CSRF cookie, and one CSRF header;
constant-time header/cookie compare plus session-bound CSRF service validation.
Every CSRF denial returns the same 403 envelope and never revokes or clears a
valid session. Session inspection denial remains one 401 envelope.

### 2. Error-response security headers

Ensure every success and every validation/auth/authz/service/internal error
under `/api/control/v1/setup`, `/login`, `/session`, `/logout`, and setup status
includes:

```text
Cache-Control: private, no-store
Pragma: no-cache
X-Robots-Tag: noindex, nofollow, noarchive
```

Implement narrowly in shared error handling or a Control auth middleware so
other APIs retain current behavior. Preserve request IDs and stable envelopes;
never include request body, cookie, header token, username, password, digest,
driver detail, or internal exception.

### 3. Exact cookies and logout

Test exact separate `Set-Cookie` headers for local and production modes:
expected names, Path `/`, no Domain, session HttpOnly, CSRF non-HttpOnly,
SameSite Lax/stricter, production Secure and `__Host-`, bounded Max-Age. No token
in JSON. Failure emits no auth cookie.

Make successful logout return an explicitly empty HTTP 204 response with the
secure headers and two matching delete-cookie headers. Correct replay with the
same manually supplied already-revoked credentials remains externally
idempotent as defined by session service. Wrong CSRF returns 403 with no clear.

### 4. Complete unit/ASGI fake coverage

Use strict fakes that reject wrong secrets and record calls. Cover all five
routes, setup success/failure/session-issuance failure, login success/all denial
classes, safe session, logout success/replay, missing/duplicate/alternate/
malformed/cross-session CSRF and cookie inputs, production/local cookie flags,
validation secret suppression, no-store error headers, no-cookie-on-failure,
and disabled docs URLs. Do not use 43 repeated characters that bypass actual
session token grammar without a corresponding real-service test.

### 5. Real PostgreSQL-backed ASGI integration

Add `test_control_auth_http.py` using the actual ControlDatabase, setup-token
bootstrap, Argon2 service, session functions, and ASGI app. Prove:

```text
uninitialized status with unavailable/available setup token
setup success creates exactly one active LOCAL administrator and one session
setup token is absent from URL/response and replay/concurrent second setup fails
session GET returns minimal context without CSRF
valid logout revokes exactly that session; replay/CSRF denial row outcomes
fresh login creates a new session and exact cookies
wrong/unknown/disabled login creates no session
cross-session CSRF cannot revoke either session
expired/revoked session cannot inspect/logout as valid
every failure leaves exact identity/session/setup state expected
```

Run this with bootstrap, local identity, human session, local auth, and Control
integration locally and in every PostgreSQL 14–18 CI job. Preserve all existing
tests and exactly 20 check names.

### 6. Documentation and claim honesty

Correct docs/README to say backend Control auth endpoints are routed by the
existing default edge but no Next.js human setup/login UI, clean Compose auth
journey, or browser E2E has been proven. Keep rate limiting/audit/OIDC/MFA/sites
explicitly absent. Preserve the centered 400×400 logo unchanged.

## Observable acceptance criteria

1. All credential/header/cookie ambiguities fail closed before authority;
   CSRF denials are uniform 403 and do not revoke/clear.
2. Auth success/failure responses carry exact no-store/noindex headers; secrets
   never appear in bodies/URLs/logs/errors.
3. Local/production issue and clear-cookie headers and 204 logout are exact.
4. Real PostgreSQL ASGI setup→session→logout and login→session flows pass with
   precise row-state proof, including replay/concurrency/substitution/denials.
5. Complete six-file integration set passes locally and on PostgreSQL 14–18;
   no affected test is omitted from CI.
6. No migration/grant/dependency/UI/edge/adjacent feature enters.
7. Exactly PR #15 is amended; report head is 20/20 green, no workflow rerun,
   report-only `SELF` is correct.

## Verification required

Run complete focused unit/ASGI tests, then the six-file disposable PostgreSQL
set through the actual app until green after concrete fixes. Run Ruff/format/
mypy/compile, repository/error/route/schema checks, secret/repr/log/URL/cookie
scans, explicit changed-doc/report Markdownlint `--no-globs`, exact paths/prior
hashes, no conflict markers, and `git diff --check`.

Do not run broad supply-chain/image, Node, browser, or full local DB version
matrix. GitHub runs all six integration files across PostgreSQL 14–18 and the
complete 20 checks. Lint exact final report content before publication.

## Safety, workflow, and report

Fake secrets and disposable PostgreSQL only; no production access or secret/
cookie/DSN/raw error output. Preserve governance, architecture, OAP, setup/
identity/session/role boundaries.

Amend only the existing PR. Atomically publish exactly:

```text
oap/reports/010-n-close-control-auth-http-proof.md
```

The linted report-only `SELF` commit must parent the literal implementation
head. Report strict parsing/errors/cookies/headers; full real ASGI flow and row
outcomes; complete local/five-version CI and 20 report-head checks; corrections/
paths/hashes/skips; no-workflow-rerun/no-new-PR/no-merge state; and
`Report publication commit: SELF`.
