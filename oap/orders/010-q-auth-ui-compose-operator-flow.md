# OAP Work Order — 010-q

## Objective

Amend PR `#15` with the complete self-hosted human authentication experience
short of Playwright: automatic first-start setup-token issuance, correct
NGINX/Apache Control-v1 routing, responsive accessible Next.js setup/login/
authenticated-admin/logout surfaces, and a secret-safe real Compose HTTP smoke
through `localhost:8080`.

Do not add Playwright/browser dependencies or claim browser/device E2E yet;
that is the next and final planned round `010-r`. Do not add sites,
memberships, capabilities, publication, OIDC, MFA, rate limiting, durable audit,
Puck, or another product feature.

## GitHub objective state

- Numeric objective/round: `010` / `010-q`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15` — <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch/base: `oap/010-installation-local-auth` / `main`
- Current main: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR/report head:
  `f23a0d7cdb582c767c130012874a99238ab8d9e7`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

PR `#15` is the unique objective PR and current head is 20/20 green. No new
PR, rebase, force-push, merge, close, auto-merge, or unrelated action.

## Current state and routing defect

The backend five-route authentication API and real PostgreSQL/ASGI proof are
complete. The web app remains a status skeleton. Compose bootstrap migrates and
hardens but does not issue the architecture-required first-start setup token.

NGINX currently uses:

```nginx
location /api/control/ {
    proxy_pass http://control-api:8000/;
}
```

That strips `/api/control/`; `/api/control/v1/login` reaches backend
`/v1/login` and fails. Preserve the full `/api/control/v1/...` application path
while retaining a separate working proxied health path. Apache must expose the
same contract. Security policy stays in the application.

## Moderate autonomy and completion rule

- Target: 65 minutes; hard stop: 90 minutes.
- Audit bootstrap output, edge rewrite, web forms, cookie/CSRF client flow, and
  Compose secret handling before execution.
- No arbitrary local attempt cap. Diagnose/fix in-scope failures until Node,
  backend policy, and one clean real Compose auth smoke pass; no unchanged
  blind reruns.
- Do not push with a known failing PR-affected gate.
- One initial CI generation; one corrective code generation only for a genuine
  clean-environment issue; never workflow-rerun.
- No Playwright, browser binaries/images, or new production dependency.

## Allowed scope

```text
services/backend/src/slaif_agent_site/bootstrap/__main__.py
services/backend/src/slaif_agent_site/bootstrap/service.py
services/backend/tests/unit/test_bootstrap_setup_token.py
services/backend/tests/integration/test_installation_setup.py
apps/web/app/page.tsx
apps/web/app/styles.css
apps/web/app/setup/**
apps/web/app/login/**
apps/web/app/admin/**
apps/web/src/auth/**
apps/web/tests/**
apps/web/package.json
apps/web/Dockerfile
infra/nginx/nginx.conf
infra/apache/slaif-agent-site.conf
compose.yaml
tools/compose/smoke.sh
tools/compose/auth_smoke.py
tools/compose/verify.py
tests/packaging/test_compose_policy.py
tests/packaging/test_edge_contract.py
tests/packaging/test_oci_contract.py
tools/check_repository.py
tests/repository/test_repository_policy.py
README.md
docs/API.md
docs/CONFIGURATION.md
docs/DEPLOYMENT.md
docs/INSTALLATION_SETUP.md
docs/LOCAL_AUTHENTICATION.md
docs/OPERATIONS.md
oap/active
oap/orders/010-q-auth-ui-compose-operator-flow.md
oap/reports/010-q-auth-ui-compose-operator-flow.md
```

Use the minimum subset. Equivalent focused web component/test paths are fine.
No dependency/lockfile, Playwright/browser-worker, migration/grant, other API,
site/domain, or unrelated product module may change.

## Requirements

### 1. Automatic one-command first-start setup token

After successful Compose provision/migrate/harden/validate, the one-shot
bootstrap command must:

- if uninitialized with no usable token, atomically issue one through the
  proven digest-only lifecycle and print exactly the setup URL plus plaintext
  token once to the operator's bootstrap container log;
- if an unexpired token already exists, succeed without rotating it, print no
  plaintext, and give the safe explicit rotate/recovery instruction;
- if initialized, succeed without issuing/printing a token and state that setup
  is closed; and
- never print digest, DSN, password, or token in failure/retry/status output.

`docker compose up --build` therefore meets the architecture first-run
contract. Keep explicit `setup-token --rotate|--revoke|--status` recovery.
Repeated/restarted bootstrap must be idempotent and never invalidate an
unconsumed token automatically.

Tests must cover first issue, existing token, expired replacement, initialized
skip, concurrent ensure, output redaction, failure, and restart behavior with
database-clock semantics. Do not persist plaintext anywhere except the one
operator log event.

### 2. Correct edge routing and parity

NGINX must route `/api/control/v1/...` to the backend with the full path
preserved. Keep a distinct `/api/control/health/live|ready` adapter to backend
`/health/live|ready`, or update health probes equivalently without exposing a
new route. Do not use a broad rewrite that can alias auth paths unexpectedly.

Apache 2.4 example must expose the same Control-v1 and health behavior using
standard OSS modules. Preserve request IDs, trusted proxy headers, body limits,
no buffering assumptions, security headers, and no product authorization at
the edge. Add exact positive and negative edge contract tests.

### 3. Responsive accessible web experience

Implement these routes in the existing Next.js application with no new UI
dependency:

```text
/                 truthful product/first-run entry and setup/login links
/setup            setup status + first-admin form
/login            local login form
/admin            authenticated session summary + logout
```

Use product styling and the existing local SLAIF asset. Requirements:

- desktop/tablet/phone responsive at 320px and wider; no horizontal overflow;
- semantic headings/landmarks, explicit labels, keyboard focus, status/error
  announcements, sufficient contrast, reduced-motion respect;
- correct `autocomplete` (`username`, `new-password`, `current-password`, name,
  email), password manager compatibility, and no password/token in URL;
- setup token is a password-like input and never copied into navigation/query;
- forms call same-origin `/api/control/v1` JSON routes; no external service;
- success follows minimal safe navigation (`/setup` or `/login` → `/admin`);
- `/admin` calls safe GET session, shows only minimal identity/recent-auth/
  expiry, and never renders session public ID unless required for user value;
- logout reads the expected CSRF cookie by exact name, sends one header, and
  clears client state after backend 204;
- generic failure messages; never render backend/internal/secret details;
- no localStorage/sessionStorage/analytics/remote font or token persistence.

Do not treat client route hiding as authorization; backend remains authority.
Handle uninitialized, initialized, authenticated, unauthenticated, expired,
network error, repeated submit, and pending states without duplicate actions.

### 4. Web unit/source proof

Create pure testable auth-client/cookie/state helpers and Node tests for exact
URLs/methods/body/header behavior, CSRF cookie parsing/duplicates/alternate
names, secret absence from URL/error/storage, pending-submit guard, redirect
decisions, and safe response parsing. Add source/DOM contract tests for route
presence, labels/autocomplete, accessibility/status, and responsive CSS. These
are not browser-E2E claims.

Keep TypeScript strict and update existing Node/prettier/eslint/build gates.
No new dependency or lockfile change.

### 5. Secret-safe real Compose auth smoke

Extend the clean Compose smoke to prove through the published NGINX port:

```text
bootstrap first-start log contains one setup URL/token
GET /setup UI and /api/control/v1/setup/status work through NGINX
POST setup through NGINX creates admin and cookies
GET session with cookie works without CSRF
POST logout with CSRF succeeds and clears
POST login succeeds and creates a new session
wrong login/CSRF denial stays secret-safe
restart bootstrap does not issue/rotate another token
only NGINX publishes a host port
```

Use a bounded stdlib helper and a mode-0600 temporary token/cookie file or
equivalent. Disable shell tracing around secret extraction/use. Never print the
token, password, cookies, headers, JSON body containing secrets, or raw
bootstrap logs. On failure emit only allowlisted stage/reason diagnostics and
perform bounded project-specific cleanup. CI fixtures are fake/disposable.

The normal operator running foreground Compose still sees the one-time token.
Do not hide it globally merely to simplify CI.

### 6. Documentation and honesty

Update README/setup/auth/API/config/deployment/operations for exact one-command
first run and UI/API flow. Remove stale “authentication not implemented” text.
State clearly: local setup/login UI and backend are implemented; no OIDC/MFA/
login rate limiting/durable auth audit/sites/workspaces/editor/review/
publication; no Playwright browser/device evidence until `010-r`. Preserve the
centered 400×400 README logo exactly.

## Observable acceptance criteria

1. Clean `docker compose up --build` prints one recoverable setup URL/token and
   reaches ready; restart is idempotent and initialized setup closes.
2. Control v1 and health routes work through NGINX and Apache contract tests
   without path stripping or edge-owned auth.
3. Setup/login/admin/logout UI is accessible, responsive by source/layout tests,
   same-origin, secret-safe, and uses exact cookies/CSRF/backend contracts.
4. Real Compose smoke completes setup→session→logout→login through NGINX without
   leaking fixtures and proves exact database/application state indirectly via
   API responses.
5. Node/backend/packaging/repository checks pass; no new dependency/lock,
   Playwright, or adjacent feature.
6. Existing parser/real-ASGI/PostgreSQL tests remain green on 14–18.
7. Exactly PR #15 is amended; report head is 20/20 green, no workflow rerun,
   report-only `SELF` is correct.

## Verification required

Run complete affected Node lint/format/typecheck/test/build, backend bootstrap/
setup focused tests, packaging/edge/repository tests, and exactly one clean
project-scoped Compose auth smoke after in-scope fixes. Run Ruff/format/mypy/
compile, secret/log/URL/storage scans, explicit changed-doc/report Markdownlint
`--no-globs`, exact paths/prior hashes, no conflict markers, and
`git diff --check`.

Do not add/run Playwright or browser matrices. Do not run broad local supply-
chain/image evidence beyond what the existing Compose smoke necessarily builds.
GitHub runs the complete 20 checks. Lint the final report before publication.

## Safety, workflow, and report

Disposable Compose/database and fake credentials only. Never expose test or
production token/password/cookie/DSN/raw logs. Preserve governance,
architecture, OAP, role/auth/session/edge boundaries.

Amend only the existing PR. Atomically publish exactly:

```text
oap/reports/010-q-auth-ui-compose-operator-flow.md
```

The linted report-only `SELF` commit must parent the literal implementation
head. Report bootstrap output semantics, edge paths, UI/accessibility/
responsive contracts, secret-safe Compose journey, exact local/CI results,
corrections/paths/hashes/skips, explicit no-Playwright claim, no-workflow-rerun/
no-new-PR/no-merge state, and `Report publication commit: SELF`.
