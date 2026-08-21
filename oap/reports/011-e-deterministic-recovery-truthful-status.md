# OAP Coding-Agent Report — 011-e

## Work order

- Identifier: `011-e`; work-order file:
  `oap/orders/011-e-deterministic-recovery-truthful-status.md`; numeric
  objective: `011`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Implemented both bounded repairs on the unique existing objective-011 PR.
Render-locator recovery now proves the restored locator, transitions and
boundedly waits for Render, Web, and NGINX in dependency order, preserves the
master secret and site fingerprints, and only then runs the global Compose
assertion. The landing page now distinguishes implemented trusted multi-site
routing and site/domain APIs from the actual deferred product areas.

GitHub's authoritative clean Compose job passed the complete corruption,
fail-closed propagation, ordered recovery, negative-bootstrap, and final smoke
flow. The round remains PARTIAL because the implementation-head CI finished at
17 successful and three failed checks: all three Python versions found the same
single Ruff E501 line in the new static test. The order allowed one
implementation generation and directed a PARTIAL report rather than another
CI loop after a newly encountered clean-runner defect, so no corrective
generation or workflow rerun was made.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#23](https://github.com/ulfe-lmi/slaif-agent-site/pull/23); state: `OPEN`,
  ready/non-draft, mergeable at inspection, no reviews
- Base/head branches: `main` / `oap/011-sites-trusted-resolution`
- Starting remote SHA: `e3edde2ac3f914172552bf62338c875d0a02028f`
- Implementation head SHA: `a724ed04ddfd7d82cf6539c838ff701412f4c062`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified after push)
- Implementation commit pushed:
  `a724ed04ddfd7d82cf6539c838ff701412f4c062`; report
  parent=implementation SHA
- New PR this turn: no; amended existing: yes; PR body updated: yes; kept
  ready/non-draft: yes; merge performed: NO; auto-merge enabled: NO; workflow
  rerun: NO

## Prior failure and root cause

- Report-head run `32441050912`, job `96651664648`, had 19 successes and one
  failure. Its Compose log showed all dependencies recovering but the immediate
  global `docker compose up --wait` still observing the deliberately stale
  NGINX `unhealthy` state.
- The recovery path previously recreated Render after restoring the locator and
  relied on Compose to clear downstream health automatically. It did not wait
  for Render, Web, then NGINX before the global assertion.
- The landing page also incorrectly listed bare `sites` as absent after
  objective 011 had implemented site persistence, trusted resolution/routing,
  and Platform Administrator site/domain APIs.

## Changes made

- Added a reusable bounded health wait (40 attempts, two seconds each) with a
  concise, secret-free terminal diagnostic naming only service, health, and
  attempt count.
- After restoring the master-derived Render locator, byte-compares it against
  `service-public-dsn`, recreates only Render without dependencies, waits for
  Render, restarts/waits for Web, then restarts/waits for NGINX.
- Captures and rechecks master-secret, Render-locator, and exact site-catalog
  fingerprints plus the single setup-token log count before and after the
  global Compose wait. No initializer, bootstrap, setup, or seed operation is
  invoked by the recovery sequence.
- Retained the exact `render-locator-failure`, `negative-bootstrap`, and
  `compose-smoke: OK` markers and added one stable
  `render-locator-recovery: restored render=healthy web=healthy nginx=healthy`
  marker.
- Added a static recovery contract covering bounded logic, dependency order,
  marker uniqueness, no-dependency Render recreation, and Render/site
  fingerprint assertions.
- Replaced the landing status copy with implemented secure local setup/server-
  side sessions, trusted multi-site identity/routing, and Platform
  Administrator site/domain APIs. Deferred copy now names membership/RBAC,
  site-management UI, content models/content, workspaces/capabilities,
  editing/Puck, review, and publication.
- Added source tests that require the implemented/deferred distinction, reject
  bare sites/routing as deferred, and reject content/publication as
  implemented.

## Files changed

- `tools/compose/smoke.sh`
- `tests/packaging/test_compose_smoke_contract.py`
- `apps/web/app/page.tsx`
- `apps/web/tests/surface.test.mjs`
- `oap/active`
- `oap/orders/011-e-deterministic-recovery-truthful-status.md`

## Acceptance-criteria evidence

### Criterion 1 — deterministic recovery

- PASSED authoritatively in GitHub. The clean Compose job printed the existing
  fail-closed marker at `03:09:39`, the new ordered-recovery marker at
  `03:10:00`, the negative-bootstrap marker at `03:10:16`, and
  `compose-smoke: OK` at `03:10:20`.
- The corruption still produced exactly `render=unhealthy web=503
  nginx=unhealthy`. Recovery passed the locator byte comparison, bounded
  Render→Web→NGINX waits, fingerprint/token-count checks, the following global
  wait, and every later smoke stage on the same clean GitHub project.
- Local clean generation 1 did not reach recovery because the invocation used
  a `slaif010...` project accepted by the smoke wrapper but rejected by the
  pre-existing readiness fixture. Generation 2 used a valid unique
  `slaif009...` project; Compose reported all 28 containers healthy, then the
  first pre-existing landing-page curl received `connection reset by peer`
  before the recovery stage. No unchanged third local run was made.

### Criterion 2 — truthful landing status

- PASSED. Web source tests require every implemented and deferred phrase and
  fail if bare sites/site routing return to deferred status or if content
  models/publication become implemented claims.
- Full Node lint, formatting, typecheck, tests, and build passed locally and
  the GitHub Node-contract job passed.

### Criterion 3 — bounded scope

- PASSED. No backend, domain, schema, migration, secret topology, edge config,
  dependency, lockfile, image, API, route, or feature behavior changed. Prior
  order/report files remain byte-identical.

### Criterion 4 — unique ready green PR

- PARTIAL. PR #23 alone remains open and ready, with no new PR, merge,
  auto-merge, close, or workflow rerun. GitHub finished at 17/20 successful,
  not the required 20/20, because all three Python jobs rejected one 89-column
  assertion in `test_compose_smoke_contract.py`.

## Local verification

- `sh -n tools/compose/smoke.sh`: PASSED.
- `python -m unittest tests.packaging.test_compose_smoke_contract`: PASSED —
  3 tests.
- Focused Web lint/typecheck/test: PASSED — surface tests 6/6.
- `pnpm lint`; `pnpm format:check`; `pnpm typecheck`; `pnpm test`;
  `pnpm build`: PASSED.
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED —
  31 tests.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  52 tests; `python tools/check_repository.py`: PASSED.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 115 tracked
  Markdown files, zero issues.
- `git diff --check`, shell syntax, immutable hashes, and changed-scope review:
  PASSED.
- Clean Compose generation 1: FAILED before product tests because the supplied
  `slaif010...` project name is outside the readiness fixture's existing
  allowlist. This was a concrete invocation diagnosis, not an unchanged retry.
- Clean Compose generation 2: browser E2E 7/7, edge/database/secret policy, and
  28-container startup passed; FAILED before the corruption/recovery section
  when the initial localhost landing curl received a connection reset. The
  stack cleaned up. Per the order, no third local generation ran.
- Not run: unrelated PostgreSQL matrices, backend suites, browser-worker
  experiments, broad SBOM, or image experiments. The required full Python Ruff
  path including `tests/packaging` was inadvertently omitted locally; GitHub
  caught its one E501 failure.

## GitHub CI / required checks

- Implementation workflow run `32442084589`; CodeQL run `32442084615`.
- SUCCESS (17): Repository policy; Node contracts; Foundation PostgreSQL 14,
  15, 16, 17, and 18; Compose and edge packaging; Supply-chain evidence;
  Markdown; Mermaid; Dependency review; Detect supported languages; Analyze
  actions, python, and javascript-typescript; CodeQL.
- FAILURE (3): Python 3.12, 3.13, and 3.14 quality/package. Each failed in Ruff
  on the same `E501 Line too long (89 > 88)` at
  `tests/packaging/test_compose_smoke_contract.py:64`; no other failure was
  reported before that fail-fast step.
- Compose passed in 5m37s. Evidence included `browser-e2e: OK`,
  `compose-e2e: OK projects=6 setup-viewports=2 artifacts=disabled`, exact
  corruption failure, ordered recovery, negative bootstrap, and final smoke
  markers.
- Final implementation-head state: 17 successful, three failed, zero pending,
  cancelled, skipped, or missing. Workflow rerun: NO.
- The report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Used the existing disposable Docker/Compose and Playwright environment with
  fake local credentials. No production service, credential, system, or data
  was accessed.
- No package, production dependency, lockfile, image/base version, hosted
  service, host port, or generated repository artifact changed or installed.

## Documentation

- Product-status prose on the localhost landing surface was corrected because
  that is the exact user-facing contradiction in scope.
- No README or durable architecture/operations document contained the same
  contradiction, so none was changed.

## Safety and scope confirmations

- Unrelated files changed: no. Production secrets/systems/data accessed: no.
- Required tests skipped/not run: the full local Python Ruff path was omitted;
  the authoritative equivalent ran and failed as reported. Two authorized
  local Compose generations ran; neither reached local recovery, while the
  authoritative GitHub clean generation passed it completely.
- Scope deviation: no. Extra objective PR: NO. Coding-agent merge: NO.
  Auto-merge: NO. Workflow rerun: NO.
- Activated order/active edited by coding agent: NO; committed byte-identically.
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
  `c1b7289b9bc2541eaf5311ea2cbd77d5579e6777bb8aa1f749197291ba97b1a4`
- Activated pointer:
  `703be3c4f464fd300c38beee13f192949f0a6c860ceadb34f34dc68118efd615`

## Known limitations / blockers

- One mechanical Ruff E501 failure remains in the new static packaging test,
  causing three required Python checks to fail. Fixing it requires a new
  strategic continuation because this order's single pushed implementation
  generation has been consumed and it forbids entering another CI repair loop
  after the diagnosed clean-runner defect.
- The authoritative clean Compose evidence proves the requested recovery
  behavior. The local edge connection-reset race occurred before that path and
  remains separately recorded rather than hidden by another retry.

## Recommended strategic follow-up

Activate a minimal continuation on PR #23 to format the single overlong test
assertion and obtain a fresh 20/20 current-head result. Only the strategic model
may choose that continuation, accept/merge the PR, or activate different work.
