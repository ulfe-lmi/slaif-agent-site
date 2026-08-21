# OAP Coding-Agent Report — 011-d

## Work order

- Identifier: `011-d`; work-order file:
  `oap/orders/011-d-demo-edge-compose-proof.md`; numeric objective: `011`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Completed the planned final objective-011 round on the unique existing PR.
State-changing session classification now uses PostgreSQL time returned with the
locked inspection. Reference Compose derives an exact one-file Render locator,
seeds only the exact fresh demo site, and runs database-aware Render without a
fallback. Database-free Web resolves actual Host/path through the fixed internal
Render endpoint and renders routing facts only; both supported edges deny the
internal path.

The final GitHub head passed all 20 checks. Its clean Compose job passed the
complete browser, routing, restart, secret, corruption, readiness, negative
bootstrap, edge, Apache, packaging, and leakage gates. Earlier clean executions
identified three test-harness defects: a raw React SSR text assertion, returning
from the routing shell before logout, and dependency startup during deliberate
locator corruption. Each was diagnosed and corrected without a workflow rerun.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#23](https://github.com/ulfe-lmi/slaif-agent-site/pull/23); state: `OPEN`,
  merge state `CLEAN`, ready/non-draft, no reviews
- Base/head branches: `main` / `oap/011-sites-trusted-resolution`
- Starting remote SHA: `a4d65b343ac802975d03478f1101828c28f1204f`
- Implementation head SHA: `9101911a7396c9f1228a8bef32a8086d069171eb`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commits pushed before report:
  `bca7704aef174d40e9438937fd0dbf9b0170baf8`,
  `ace7c150858683ae039f852ac2c518317488d405`,
  `9101911a7396c9f1228a8bef32a8086d069171eb`; report
  parent=implementation SHA
- New PR this turn: no; amended existing: yes; PR body updated: yes; kept
  ready/non-draft: yes; merge performed: NO; auto-merge enabled: NO; workflow
  rerun: NO

## Changes made

- Replaced application-clock wrong-CSRF classification with
  `CURRENT_TIMESTAMP` returned by the same locked inspection statement. Far
  ahead/behind clock fixtures prove only database time controls 401 versus 403.
- Generalized local secret initialization with isolated
  `/run/slaif-render/render-dsn`. It byte-matches `service-public-dsn`, is the
  only file, uses directory `0700` and file `0400`, and belongs to UID/GID
  `10001` as applicable. Unexpected, mismatched, or unreadable state fails.
- Added the `render-secret` named volume: initializer read/write, Render
  read-only, no other service mount. Render receives only fixed
  `SLAIF_RENDER_*` file/identity values and always starts its database-aware
  application. Check mode remains connection- and file-read-free.
- Added typed `SLAIF_BOOTSTRAP_DEMO_SEED=false`. True is accepted only with the
  local manifest and loopback `/setup`. Reference Compose enables it.
  Transactional seeding locks installation state, creates only exact active
  `demo` in an empty uninitialized catalog, is concurrently idempotent for the
  exact row, fails on unexpected state, rolls back on failure, and skips after
  initialization.
- Added a server-only Web client fixed to
  `http://render-api:8000/internal/render/v1/site-context`, with short timeout,
  no-store, omitted credentials, no forwarded identity, and only actual Host
  and path. Added an accessible routing-context shell for resolved routes while
  preserving the localhost landing and explicit setup/login/admin pages.
- Unknown non-loopback root Hosts now resolve through Render or return 404;
  invalid, unknown, archived, forged-header, reserved, ambiguous, and prefix-
  boundary substitutions fail closed. NGINX and Apache reject `/internal/`.
- Extended setup E2E to render the pre-setup demo at desktop and 320 px, create
  a second site/domain with the real session and CSRF, prove local/custom Host
  resolution and negatives, archive it, and preserve the existing login/logout
  qualification.
- Extended clean smoke with exact Render-secret inventory/value/ownership and
  cross-UID denial, restart persistence, no token reissue/reseed, deliberate
  Render locator corruption with Render/Web/NGINX failure and recovery, concise
  `negative-bootstrap: correctly blocked`, and locator scans.
- Updated API, sites, configuration, deployment, operations, security, and
  README claims. The shell is explicitly routing evidence, not content or
  publication.

## Files changed

- `README.md`, `compose.yaml`
- `apps/web/app/page.tsx`, `app/health/ready/route.ts`,
  `app/[...sitePath]/page.tsx`, `src/sites/render.ts`, `src/sites/shell.tsx`,
  `tests/surface.test.mjs`
- `docs/API.md`, `docs/SITES.md`, `docs/CONFIGURATION.md`,
  `docs/DEPLOYMENT.md`, `docs/OPERATIONS.md`, `docs/SECURITY.md`
- `infra/nginx/nginx.conf`, `infra/apache/slaif-agent-site.conf`
- `services/backend/src/slaif_agent_site/bootstrap/{config,service}.py`,
  `identity/sessions.py`, `render_api/__main__.py`
- `services/backend/tests/unit/test_bootstrap_setup_token.py`,
  `test_sessions.py`; `services/backend/tests/integration/test_demo_seed.py`
- `tests/e2e/setup.spec.ts`; `tests/packaging/test_compose_policy.py`,
  `test_local_secrets.py`
- `tools/local_secrets/initialize.py`, `tools/compose/{verify.py,smoke.sh}`
- `oap/active`, `oap/orders/011-d-demo-edge-compose-proof.md`

## Acceptance-criteria evidence

### Criterion 1 — database-clock session classification

- PASSED. The mutation inspection selects the locked row and
  `CURRENT_TIMESTAMP` together. A database clock fixed in 2000 classifies a
  current row with wrong CSRF as 403 despite the application being far ahead;
  a database clock fixed in 2100 classifies expiry as 401 despite the
  application being far behind. Existing constant-time, cancellation,
  rollback, redaction, one-finalization, and denial-snapshot tests remain green.

### Criterion 2 — isolated Render locator and fail-closed readiness

- PASSED. Static and running Compose prove one `render-dsn`, exact byte match,
  directory `0700` owner/group `10001:10001`, file `0400` owner `10001`, and
  unrelated UID denial. Only initializer and Render mount the volume at the
  required read/write and read-only modes. Final CI deliberately corrupts the
  locator and records `render=unhealthy web=503 nginx=unhealthy`, then restores
  the exact value and returns the whole graph to healthy. No fallback remains.

### Criterion 3 — exact fresh-demo seed

- PASSED. Real PostgreSQL covers empty/disabled, exact idempotence,
  concurrency, mismatch without overwrite, injected failure rollback, and
  post-initialization skip. The inserted row is exactly `demo`,
  `SLAIF Demo Site`, `en`, active, with generated identity and server defaults;
  no domain, administrator, membership, content, capability, or publication
  record is seeded. Restart retains the administrator/site state and emits the
  setup token only once.

### Criterion 4 — trusted routing and edge behavior

- PASSED. Final NGINX E2E renders demo before setup at desktop and 320 px,
  creates a distinct second site and `sites.test/team` mapping through the
  authenticated API/CSRF boundary, and renders the correct key through local
  and custom routes. Wrong Host, unknown root, `/team-other`, forged site
  header, archive, unknown route, and public internal endpoint return 404.
  Web holds no DB credential and does not use forwarded Host or client-selected
  internal URLs. Apache syntax and equivalent internal exclusion pass.

### Criterion 5 — clean Compose proof and concise failure evidence

- PASSED authoritatively. Final GitHub Compose job ran the clean stack, all
  established Playwright browser/device projects, restart, six Control
  readiness failures/recovery, secret and database policy, Render corruption/
  recovery, expected broken bootstrap, image/log locator scans, NGINX/Apache
  syntax, and packaging tests. It printed one concise
  `negative-bootstrap: correctly blocked` marker and finished
  `compose-smoke: OK`. No test artifact or credential was retained.

### Criterion 6 — bounded scope and unique green PR

- PASSED. No dependency, lockfile, image/base version, role name, host port,
  content/COW, membership, workspace/capability, Puck, media, browser-worker,
  or publication behavior changed. Only PR #23 was amended and remains ready.
  Final implementation-head CI is 20/20 successful, with no workflow rerun,
  new PR, merge, close, or auto-merge.

## Local verification

- `uv lock --check`; `uv sync --frozen --all-groups`: PASSED — 45 resolved,
  44 checked packages.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository
  tools`: PASSED — 115 files.
- `uv run --frozen mypy`: PASSED — 104 source files.
- `python -m compileall -q tools tests/repository`: PASSED.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 329 tests in 11.14 seconds.
- `uv run --frozen pytest services/backend/tests/integration`: 61 PASSED and
  one local PostgreSQL connection timeout after 324.79 seconds; the exact
  affected archive test then PASSED in 3.91 seconds. An earlier focused run had
  the same environment-level connection reset and passed immediately when run
  alone. All five authoritative PostgreSQL versions passed.
- Focused session/bootstrap/Render/packaging suites: PASSED — 72 tests and 19
  subtests; focused site/session/seed/Render integration: 11 passed plus the
  diagnosed connection reset, whose exact case passed on rerun.
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED — 30
  tests.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  52 tests; `python tools/check_repository.py`: PASSED.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-011d`: PASSED — sdist
  and wheel.
- All ten `uv run --frozen python -m slaif_agent_site.<process> --check`
  commands: PASSED; Render check did not read or connect.
- Node `24.14.1`, pnpm `11.22.0`; frozen install, lint, format, typecheck, test,
  build, and license inventory: PASSED. Web and browser tests passed; contract
  Vitest passed 2/2.
- Changed-file Markdownlint 0.23.2: PASSED; authoritative full Markdown CI:
  PASSED. `python tools/check_mermaid.py` failed locally because the cached
  Puppeteer renderer returned opaque `[object Object]` even for a two-node
  fixture; no diagram changed and authoritative Mermaid CI PASSED.
- `python tools/compose/verify.py --root .`, shell syntax, `git diff --check`,
  immutable hashes, and secret/locator policy checks: PASSED.
- Local clean Compose generation 1: FAILED at the new custom-host assertion;
  diagnosis showed React SSR inserts markup between literal and dynamic text.
  Generation 2 after stage instrumentation: FAILED at the same exact raw-HTML
  assertion, confirming the diagnosis. The assertion was corrected without a
  third local generation, as required. Final authoritative GitHub clean Compose
  passed the corrected flow and all later gates.

## GitHub CI / required checks

- Implementation run `32439725097`: 19 successes, Compose failure at
  `logout-closure`; the new routing path passed but the test had not returned to
  `/admin` before clicking Sign out. Workflow rerun: NO.
- Corrected run `32440165325`: browser and routing passed; Compose then failed
  because deliberate Render-secret corruption caused an implicit dependency
  restart to run `secrets-init`, which correctly rejected the corrupt derived
  file. Workflow rerun: NO.
- Final run `32440533840` plus CodeQL run `32440533820`: 20/20 SUCCESS.
- SUCCESS: Repository policy; Node contracts; Python 3.12, 3.13, and 3.14;
  Foundation PostgreSQL 14, 15, 16, 17, and 18; Compose and edge packaging;
  Supply-chain evidence; Markdown; Mermaid; Dependency review; Detect supported
  languages; Analyze actions, python, and javascript-typescript; CodeQL.
- Final Compose job duration: 5 minutes 35 seconds. Evidence markers include
  `compose-e2e: OK projects=6 setup-viewports=2 artifacts=disabled`, six named
  login browser/device successes plus setup, `render-secret-policy: OK`,
  `render-locator-failure: correctly blocked render=unhealthy web=503
  nginx=unhealthy`, `negative-bootstrap: correctly blocked`, and
  `compose-smoke: OK`.
- Implementation-head state: 20 successful, zero failed, pending, cancelled,
  skipped, or missing. All required green at drafting: yes.
- The report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Used the existing disposable local PostgreSQL service, fake credentials,
  Docker/Compose, Playwright browsers, uv 0.12.5, Node 24.14.1, pnpm 11.22.0,
  and transient exact Markdown/Mermaid tools. Refreshed the local Puppeteer
  browser cache while diagnosing its renderer failure. No production service,
  credential, or data was accessed.
- No production dependency, lockfile, image, base version, external service,
  host port, or generated repository artifact changed.

## Documentation

- Documented the demo flag and fresh-only matrix, isolated Render locator,
  startup/readiness failure propagation, fixed internal Web→Render flow,
  local/custom-host examples, API-created second site, negative smoke marker,
  and restart/cleanup behavior.
- Explicitly documents that the shell proves routing context only. Actual site
  content/content models, memberships/RBAC, site-management UI, editor/Puck,
  workspaces, agent capabilities, review/publication, DNS automation, and
  hostile tenancy are not implemented.

## Safety and scope confirmations

- Unrelated files changed: no. Production secrets/systems/data accessed: no.
- Required tests skipped/not run: no. Two authorized local Compose generations
  ran and their failures are reported; the final authoritative clean generation
  ran and passed in GitHub.
- Scope deviation: no. Extra objective PR: NO. Coding-agent merge: NO.
  Auto-merge: NO. Workflow rerun: NO.
- Activated order/active edited: NO; committed byte-identically.
- Report commit changes only this report: yes.
- Credential, cookie, setup token, digest, DSN, private locator, or private
  artifact exposure: no.

## Immutable hashes

- `AGENTS.md`:
  `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`:
  `00bdd82fcec0afaf65d2fbc2a2f9fa43a7d4e9e254d7a262bea0c5bae3be6b8a`
- `ARCHITECTURE-for-agents.md`:
  `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Activated work order:
  `211060f0072a102432019928333662acae6302ba5b5d4defb81a5de7efd74fb3`
- Activated pointer:
  `5a7eb8b9997f1fa281b2c3fe4bb0385c80ef337f81ae30ccc9615fb64d78cdbb`

## Known limitations / blockers

- No blocker remains for this bounded round. Local Mermaid rendering and local
  PostgreSQL connection stability limitations are recorded above; authoritative
  Mermaid and five-version database CI passed.
- This final objective-011 round implements trusted routing evidence only. The
  deferred product areas listed above remain deliberately absent.

## Recommended strategic follow-up

Independently review this report, the final implementation diff, the exact
secret/seed/routing boundaries, and final 20/20 CI. This was the strategically
planned final objective-011 round; only the strategic model may accept/merge it
or activate the next bounded work order.
