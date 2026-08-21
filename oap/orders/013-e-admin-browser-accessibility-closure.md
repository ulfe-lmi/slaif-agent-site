# OAP Work Order — 013-e

## Objective and final-round state

Complete objective 013 on PR #25 with authoritative NGINX/Playwright proof of
the responsive admin shell, site governance, and membership workflows across
desktop/tablet/phone, including keyboard/accessibility, crafted-request, strict
CSP, restart, and secret boundaries.

- Numeric objective: `013`; round: `013-e`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25)
- Base/head: `main` / `oap/013-responsive-admin`
- Required starting remote head:
  `e72a8baa39bc4bef1e2d9027d7f0dce3b945db75`
- 013-d implementation parent:
  `49a27296fd4cd2aa123657ff9ff50e37148b7d9c`
- Verified state: open, ready/non-draft, mergeable, no reviews/threads; correct
  report-only topology; current-head CI 20/20 successful; dependency graph
  remains architecture-allowed and MPL-free.

Fetch and verify the exact PR/head. Amend only PR #25; never create another PR,
merge, close, auto-merge, or workflow-rerun.

## Boundaries and sequencing

Add one `governance` Playwright project that depends on the existing `setup`
project and runs once in Chromium to mutate disposable state through the real
UI. Make the six existing stable browser/device projects depend on governance
and retain their exact names. They perform login/logout plus read-only admin
responsive/keyboard checks, so mutations never race across projects.

No backend/API/schema/migration/role/permission/dependency/lock/Compose service/
network/volume/edge change, user creation/invitation/custom role, content/Puck,
workspace/capability, review, or publication execution. Minimum UI/test-harness
fixes are allowed only when browser evidence exposes a concrete defect.

## Allowed scope

```text
playwright.config.ts
tests/e2e/{governance,auth,setup,support,reporter}.ts|.mjs
tools/compose/{e2e,smoke}.sh
tests/packaging/test_compose_smoke_contract.py
apps/web/src/admin/** and apps/web/app/admin/** only for diagnosed UI defects
apps/web/app/styles.css and apps/web/tests/** only for diagnosed responsive/accessibility defects
docs/{ADMIN,TESTING,SECURITY,OPERATIONS}.md and README.md
oap/active
oap/orders/013-e-admin-browser-accessibility-closure.md
oap/reports/013-e-admin-browser-accessibility-closure.md
```

## Requirements

### 1. Governance UI project

After setup and using the real setup-created Platform Administrator session,
exercise through visible controls—not direct success-path API calls:

1. dashboard and site switcher loading/empty/error-free state;
2. create a new site with key/name/locale and land on its canonical overview;
3. update profile/default locale;
4. add secondary and primary domain mappings, replace primary, verify list and
   local/custom route behavior, and remove a non-primary mapping;
5. open membership administration, verify exact role/permission catalog facts,
   add an existing disposable fixture UUID, edit role/ceiling, separately grant
   and deny publication, observe version changes, and semantically deactivate;
6. provoke one stale-version conflict through a crafted request, then verify UI
   refresh/recovery rather than overwrite;
7. prove self target, system permission, ceiling escape, missing/wrong CSRF,
   cross-site/non-member UUID, and direct hidden-control requests remain
   server-denied with no state change;
8. archive through the named confirmation dialog while recent auth is valid,
   verify no deletion and archived state/navigation; and
9. verify logout/relogin and stop/start retain site/membership/domain state
   without setup-token, demo-seed, or fixture recreation.

Direct `page.request` is allowed only for negative/concurrency setup that cannot
be produced through safe visible controls; every normal workflow must click/fill
the UI. Expected failures must be registered in the observation harness.

### 2. Six stable browser/device projects

Preserve `desktop-chromium`, `desktop-firefox`, `desktop-webkit`, `tablet`,
`mobile-chromium`, and `mobile-webkit`. After login, each must load dashboard,
open/close mobile or desktop navigation as applicable, switch to an existing
site, load overview/settings/membership read states, and logout. Do not mutate
shared governance state in these six projects.

On all applicable viewports prove one H1, landmarks, skip link, labelled
controls, visible focus, keyboard-only traversal, Escape/focus return, no focus
behind open dialogs, 44 px critical targets, no horizontal overflow at 320 px,
and reduced-motion-compatible behavior. Full Puck is out of scope.

### 3. Security/privacy/runtime closure

Through NGINX verify one edge request ID, strict CSP with no unsafe-inline/eval
or remote origin, private/no-store/noindex admin/API responses, no token/CSRF/
password/user authority in URL/DOM/storage/console/network logs/artifacts, no
client role/site trust, and direct non-member/unknown/archived URLs fail safely.

Retain all established setup/login/cookie/routing/membership fixture, Render
corruption/recovery, broken-bootstrap, restart fingerprint, only-NGINX-port,
image/log locator, and secret cleanup assertions. Add concise governance/admin
E2E markers without UUIDs or credentials. CI failure artifacts remain governed
by existing private retention; local test output retains no screenshots/traces.

### 4. Tests and docs

Update source/packaging contracts for exact project dependency order and marker
presence. Run full Node and repository/packaging checks before one clean local
Compose generation. A second clean generation is allowed only after a concrete
diagnosed defect; no unchanged retry. Do not run unrelated PostgreSQL matrices,
browser-worker/source experiments, images, Mermaid, or broad SBOM locally.

Document exact implemented admin workflows, device/keyboard evidence,
governance project sequencing, limitations, and honest deferred identity/
content/workspace/review/publication scope. Do not call automated checks a
security/accessibility certification.

## Acceptance and workflow

Acceptance requires the governance UI flow plus all six stable device projects,
crafted server negatives, responsive/accessibility/privacy/CSP/restart evidence,
no adjacent scope, and all 20 current-head checks green. Target 60 minutes; hard
stop 90 minutes.

Front-load static/Node tests, then clean Compose. Fix diagnosed defects within
scope. Push one coherent generation after local green; one corrective generation
only for a concrete clean-runner/browser-engine defect, never workflow-rerun or
test weakening. Publish honest `PARTIAL` at the hard stop. Access no production
credential/system/data.

Preserve prior transcript bytes and amend only PR #25. Atomically publish:

```text
oap/reports/013-e-admin-browser-accessibility-closure.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
project/device/workflow/negative/accessibility/privacy/CSP/restart matrices,
exact local and CI commands/timings, all 20 checks, corrections/skips/scope/
hashes, and no-new-PR/no-rerun/no-merge. Signal FIFO `OK` only after report and
claimed remote state exist.
