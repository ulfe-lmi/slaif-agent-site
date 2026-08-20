# OAP Work Order — 010-r

## Objective

Complete numeric objective `010` on PR `#15`: restore the established
`slaif007*` safe Compose project family, add pinned self-hosted Playwright test
infrastructure, prove first setup plus login/session/logout through the actual
NGINX/Compose deployment on all six architecture browser/device targets, fix
browser-discovered auth UI/CSP/accessibility/responsive defects, update the PR
summary, and deliver a merge-ready 20/20-green report head.

Do not implement sites, memberships, capabilities, workspaces, OIDC, MFA,
login rate limiting, durable security audit, Puck, editing, review, publication,
or runtime agent browser tools. This is auth E2E and objective closure only.

## GitHub objective state

- Numeric objective/round: `010` / `010-r`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15` — <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch/base: `oap/010-installation-local-auth` / `main`
- Current main: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR/report head:
  `819d204c2e00c07632d57ca70d31cd0d4b01cfcc`
- `010-q` corrective implementation head:
  `662a8a2b02d534ba7f423a456ab7f7cc7e6ab034`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

PR `#15` remains the unique objective PR. No new PR, rebase, force-push,
merge, close, or auto-merge. The coding agent never merges; strategic review
does so only after final proof.

## Known CI repair

`tools/compose/smoke.sh`'s new safety selector accepts `slaif009*` and
`slaif010*` but omitted the repository's established CI project name
`slaif007ci`. Add `slaif007[a-z0-9]*` back to the same narrow allowlist and add
an exact positive regression while retaining rejection of empty, uppercase,
separator, shell/glob, broad, or unrelated names. Do not weaken destructive
target validation or change CI's established project name merely to evade the
defect.

## Moderate autonomy and completion rule

- Target: 70 minutes; hard stop: 100 minutes.
- Verify official registry metadata/license and select one stable compatible
  Playwright release before editing locks; pin it exactly.
- Audit browser secret/artifact policy, Compose lifecycle, CSP/hydration, and
  six-project flow before the first real run.
- No arbitrary local attempt cap. Diagnose and fix in-scope failures until one
  clean six-project real deployment run and all local gates pass; never repeat
  an unchanged command.
- Do not push with a known failing PR-affected test.
- One initial CI generation is expected; up to two corrective code generations
  are allowed only for distinct in-scope clean-environment/browser-engine
  defects after complete local proof. Never invoke workflow rerun.
- Do not broaden into runtime browser-worker tools or another feature.

## Allowed scope

```text
package.json
pnpm-lock.yaml
playwright.config.ts
tests/e2e/**
apps/web/app/**
apps/web/src/auth/**
apps/web/tests/**
apps/web/package.json
apps/web/Dockerfile
infra/nginx/nginx.conf
infra/apache/slaif-agent-site.conf
compose.yaml
tools/compose/smoke.sh
tools/compose/e2e.sh
tools/compose/auth_smoke.py
tools/compose/verify.py
tests/packaging/**
.github/workflows/ci.yml
tools/check_repository.py
tests/repository/test_repository_policy.py
tools/supply_chain/**
tests/supply_chain/**
supply-chain/policy.json
THIRD_PARTY_NOTICES.md
README.md
docs/API.md
docs/CONFIGURATION.md
docs/DEPLOYMENT.md
docs/INSTALLATION_SETUP.md
docs/LOCAL_AUTHENTICATION.md
docs/OPERATIONS.md
docs/SUPPLY_CHAIN.md
oap/active
oap/orders/010-r-playwright-auth-e2e-and-objective-closure.md
oap/reports/010-r-playwright-auth-e2e-and-objective-closure.md
```

Use the minimum subset. A focused E2E package/Dockerfile path under
`tests/e2e/` is permitted if the selected runner design requires it. No backend
migration/grant/auth semantics, production browser-worker implementation,
agent browser API, or unrelated package may change unless real browser proof
exposes a direct auth contract defect; report before broadening beyond scope.

## Requirements

### 1. Playwright dependency and self-hosted runner

Add `@playwright/test` as an exact test/dev dependency only. Verify it from the
official npm registry/project metadata, record permissive licensing, regenerate
the frozen pnpm lock, and update exact repository/supply-chain/notices policy.
No hosted browser grid/account/API key. No floating range, lifecycle script,
unapproved download, or production Web dependency.

Choose a reproducible runner that works locally and in GitHub:

- install the selected release's exact Chromium, Firefox, and WebKit binaries
  and required OS packages through its documented local/CI mechanism; or
- use the matching official Playwright OCI image pinned by immutable digest in
  a Compose `e2e` profile.

If an E2E image/service is added, it must be profile-only, non-root where the
official runtime permits, read-only/minimal mounts, no DB/service credentials,
no Docker socket, no host files, and access the deployment only through NGINX.
Update SBOM/license/image inventory honestly. Do not transform the health-only
runtime browser worker into agent tooling in this objective.

### 2. Stable six-project configuration

Define these exact stable project names mapped to pinned Playwright descriptors:

```text
desktop-chromium
desktop-firefox
desktop-webkit
tablet
mobile-chromium
mobile-webkit
```

Use the real NGINX base URL, bounded per-test/global timeouts, one worker for
stateful setup where needed, no retries that can hide deterministic failure,
and no external origin. A single setup project may initialize once before the
six projects; every target must independently prove login, authenticated admin,
and logout. Setup UI itself must be browser-proven at desktop and one phone-
class viewport before initialization.

### 3. Secret/private artifact policy

The setup token, password, session/CSRF cookies, request bodies, and headers may
not appear in test names, console output, HTML report, trace, screenshot, video,
CI artifact, environment dump, command line, process listing, or failure logs.

- Pass the token through a mode-0600 file/stdin or equivalent bounded secret
  channel; avoid command-line/plain exported-value exposure.
- Disable trace/video/screenshot capture for secret-bearing setup/login forms
  unless a tested redaction step removes values before capture; default to no
  retained auth artifacts for this objective.
- Use generic assertion messages and reporters that print no request/body/
  cookie detail.
- Cleanup token/cookie/storage-state/temp/profile files on success, failure, and
  cancellation. Do not upload auth artifacts.

Only fake/disposable CI credentials are used, but still preserve the product
secret boundary.

### 4. Real browser workflows

Through `http://localhost:8080` (or the internal NGINX service URL for a
profile-contained runner), prove:

1. Landing page renders without console/page/network errors and links setup/
   login.
2. Before initialization, setup status/UI is usable; desktop and phone layout
   have no horizontal overflow, clipped controls, missing labels, or unreachable
   submit.
3. Setup form submits the one-time token in request body only, creates the first
   administrator, redirects to `/admin`, and never places secrets in URL/DOM
   after navigation/storage.
4. Admin renders authenticated session summary; logout uses bound CSRF, returns
   to login, and session can no longer access admin.
5. Each of the six projects logs in with the fake administrator, reaches admin,
   performs keyboard-visible navigation, and logs out.
6. Wrong password shows one generic accessible error without user enumeration;
   duplicate submit is prevented.
7. Direct unauthenticated/expired-session admin visit redirects safely to login.
8. Setup is closed after initialization and token replay fails without another
   user/session.
9. Browser console errors, uncaught page errors, failed same-origin requests,
   broken resources, and horizontal overflow are zero for expected paths.

Assert cookies using browser context metadata without printing values: session
HttpOnly, CSRF not HttpOnly, SameSite, Path, local non-Secure; production Secure
attributes remain unit/contract-proven because local HTTP cannot set them.

### 5. UI/CSP/accessibility corrections

Use Playwright findings to correct in-scope UI, not weaken tests. In particular,
prove Next.js client hydration and form handlers work under the actual edge CSP;
do not add broad `unsafe-inline`, `unsafe-eval`, wildcard sources, remote fonts,
or external scripts. If Next requires a nonce, implement a bounded per-request
nonce/header contract consistently for NGINX and Apache and test it. Security-
critical auth remains backend-owned.

Ensure setup form becomes non-submittable when initialized or no token is
available, avoids duplicate network requests, focuses/announces errors, and
does not render raw account/session identifiers as the primary user-facing
identity when a safe username/display value is available. Preserve 320px+
responsive, contrast, labels/autocomplete, keyboard, and reduced-motion.

### 6. Compose/CI integration and existing fix

Restore `slaif007*` project allowlisting first. Run one clean project-scoped
deployment that combines the existing structural/auth smoke and Playwright
workflow before cleanup. The browser runner must not publish another host port;
only NGINX remains exposed.

Keep exactly 20 required check names. Extend the existing Compose/edge job or
Node job rather than adding an ungoverned check. Ensure its timeout is bounded
and realistic, browser installation is cached only through approved mechanisms,
and a failure does not automatically rerun. PostgreSQL 14–18 existing six-file
proof remains unchanged and green.

### 7. Final objective closure

Update README/docs to describe implemented one-command setup, local auth UI,
six-project E2E, limitations, and exact commands. Preserve the 400×400 README
logo. Do not claim production readiness, OIDC/MFA/rate-limit/audit/sites/
workspaces/editor/review/publication.

Update PR #15 body (same PR, no new PR) with an accurate concise summary of all
accepted objective-010 rounds and current verification, replacing the stale
010-a-only/deferred text. Do not claim merge or strategic acceptance.

## Observable acceptance criteria

1. `slaif007ci` and all established safe project families pass while unsafe
   project names remain rejected.
2. Exact pinned Playwright dependency/browser provenance/license/SBOM policy
   passes with no hosted or production dependency drift.
3. Setup is browser-proven desktop+phone; login/admin/logout pass on all six
   named projects through real NGINX/Compose with zero unexpected browser/
   network/overflow failures.
4. Auth secret values cannot enter retained artifacts/logs/URLs/storage; temp
   state is cleaned.
5. UI hydrates and operates under a strict CSP; accessibility/responsive/
   pending/error/initialized states are executable, not source-only claims.
6. Clean one-command Compose plus E2E and all existing Node/Python/PostgreSQL/
   packaging/supply-chain checks pass; only NGINX publishes a port.
7. PR body/docs match implemented scope and limitations; no adjacent feature.
8. Exactly PR #15 is amended; final report head has 20 successful, zero failed/
   cancelled/skipped/pending checks, no workflow rerun, correct report-only
   `SELF` parentage, and no blocker to strategic merge.

## Verification required

Run full affected Node frozen install/lint/format/typecheck/test/build, Playwright
install/version and six-project E2E, one clean Compose structural+auth+browser
flow, packaging/edge/repository/supply-chain policy, complete backend unit and
focused auth integration, Ruff/format/mypy/compile, license/notices/SBOM checks,
secret/artifact/storage/network scans, changed-doc/report Markdownlint
`--no-globs`, exact paths/prior hashes, no conflict markers, and
`git diff --check`.

GitHub runs the complete 20 checks including the six-project real browser gate.
Do not invoke workflow rerun. Lint the exact final report before publication.

## Safety, workflow, and report

Disposable deployment and fake credentials only; no production/external
authenticated service. Preserve governance, architecture, OAP, role/auth/
session/edge/browser boundaries and immutable earlier reports.

Amend only existing PR #15 and update its body; never merge. Atomically publish:

```text
oap/reports/010-r-playwright-auth-e2e-and-objective-closure.md
```

The linted report-only `SELF` commit must parent the literal implementation
head. Report selected Playwright/version/provenance; six projects; exact setup/
login/logout/browser/CSP/a11y/responsive/secret-artifact evidence; clean Compose;
all local and final-head 20 checks; CI correction generations; PR-body/docs/
paths/hashes/skips; no-workflow-rerun/no-new-PR/no-merge state; strongest
remaining limitation; and `Report publication commit: SELF`.
