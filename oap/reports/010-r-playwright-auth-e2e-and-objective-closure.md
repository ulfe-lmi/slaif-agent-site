# OAP Coding-Agent Report — 010-r

## Work order

- Identifier: `010-r`; work-order file:
  `oap/orders/010-r-playwright-auth-e2e-and-objective-closure.md`; numeric
  objective: `010`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Restored the established `slaif007*` safe Compose project family and completed
objective 010 with exact Playwright 1.62.1 infrastructure, strict nonce-based
edge CSP, corrected auth UI behavior, and a secret-safe real NGINX/Compose
setup/login/admin/logout workflow. Setup passed at desktop and phone widths;
login, authenticated administration, keyboard interaction, generic failure,
duplicate-submit prevention, and logout passed on all six required projects.
The final implementation passed every required local gate and its single
initial GitHub CI generation passed 20/20 checks. No corrective CI generation
or workflow rerun was used.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#15](https://github.com/ulfe-lmi/slaif-agent-site/pull/15); state: `OPEN`
- PR title: `[OAP 010] Establish secure installation and local authentication`
- Base/head branches: `main` / `oap/010-installation-local-auth`
- Starting remote SHA: `819d204c2e00c07632d57ca70d31cd0d4b01cfcc`
- Starting authoritative main SHA:
  `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Implementation head SHA: `543249885cb013523fdee9ddc7a07fd84e4771fc`
- Report publication commit: SELF
- Implementation commits pushed before report:
  `6a2626df14ee04d0be9022bd339f7ac60fd66eda` and
  `543249885cb013523fdee9ddc7a07fd84e4771fc`; report
  parent=implementation SHA
- New PR this turn: no; amended existing: yes; PR body updated: yes; merge
  performed: NO; auto-merge enabled: NO; workflow rerun: NO

## Changes made

- Added exact root development dependency `@playwright/test==1.62.1`, its
  frozen lock entries, Apache-2.0 attribution, inventory policy, and generated
  third-party notices. Official npm metadata and integrity were verified; the
  dependency and matching browsers are test-only and absent from product
  images.
- Added one setup project and the exact six stable projects:
  `desktop-chromium`, `desktop-firefox`, `desktop-webkit`, `tablet`,
  `mobile-chromium`, and `mobile-webkit`. Configuration uses one worker, zero
  retries, bounded timeouts, localhost NGINX only, and no retained screenshot,
  trace, video, or storage state.
- Added a generic secret-safe reporter and mode-0600 JSON credential channel.
  The setup token and fake password are never command-line arguments or printed
  values. A unique temporary output directory and credential file are removed
  on success, failure, interruption, and cancellation.
- Browser-proved landing, setup desktop/320px, one-time initialization,
  cookie metadata, setup closure/token replay rejection, wrong-password
  accessibility, duplicate-submit prevention, authenticated admin, direct
  unauthenticated redirect, keyboard-visible focus, responsive overflow, and
  logout/session revocation.
- Corrected setup/login pending and availability behavior with synchronous
  duplicate-request guards, disabled controls, focused live error status, and
  removal of the raw account UUID from the operator surface.
- Added a strict per-request nonce contract from NGINX or Apache to dynamic
  Next rendering. CSP retains no `unsafe-inline`, `unsafe-eval`, wildcard,
  external script, or remote font allowance.
- Restored `slaif007[a-z0-9]*` beside the existing narrow `slaif009*` and
  `slaif010*` selector families, with exact positive and unsafe-name negative
  regression coverage.
- Integrated the browser workflow into the existing Compose/edge CI job using
  Node 24, pnpm 11.22.0, frozen install, and exact matching Chromium, Firefox,
  and WebKit installation. Exactly 20 check names remain.
- Updated README, API, configuration, deployment, setup, local-authentication,
  operations, and supply-chain documentation. The 400×400 README logo remains.
- Replaced PR #15's stale 010-a-only body with an accurate concise summary of
  the complete activated objective-010 implementation and limitations.

## Acceptance-criteria evidence

1. Selector contract tests and direct validation passed for `slaif007ci`,
   `slaif009local`, and `slaif010local`; empty, uppercase, separator, glob,
   broad, and unrelated names remain rejected.
2. Playwright 1.62.1 official npm provenance, Apache-2.0 licensing, exact
   integrity lock entries, 192-component notices, policy, inventory, and SBOM
   gates passed. No hosted service or production dependency was introduced.
3. Clean `slaif009rfinal` Compose proof passed setup at desktop and phone
   widths plus login/admin/logout on all six named projects through
   `http://localhost:8080`, with zero unexpected browser, page, console,
   same-origin network, resource, or overflow failure.
4. Browser assertions proved token-in-body-only, no secrets in post-navigation
   URL/DOM/browser storage, safe session/CSRF cookie metadata, and revocation.
   No auth artifact was retained; final output and temporary-file scans passed.
5. Real browser hydration and form handlers passed under the strict nonce CSP.
   Pending, initialized, unavailable, error-focus, keyboard, and responsive
   states are executable browser proof rather than source-only claims.
6. Full Node, Python, PostgreSQL auth integration, packaging, repository,
   Compose, and supply-chain gates passed. Only NGINX publishes a host port.
7. Durable documentation and the PR body match implemented local-auth scope and
   explicitly exclude adjacent features.
8. Exactly PR #15 was amended. The implementation head completed 20/20 checks
   successfully with zero failed, cancelled, skipped, or pending checks, zero
   workflow reruns, and no blocker to strategic review.

## Local verification

- `node --version`; `pnpm --version`; `pnpm install --frozen-lockfile`:
  PASSED — Node 24.14.1 and pnpm 11.22.0.
- `pnpm lint`; `pnpm format:check`; `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — web 5, browser-worker 1, contracts 2.
- `pnpm build`: PASSED — all Next routes dynamically rendered.
- `pnpm licenses list --json`; `pnpm inventory`: PASSED.
- `pnpm exec playwright --version`: PASSED — 1.62.1.
- `pnpm exec playwright install --with-deps chromium firefox webkit`: PASSED;
  exact matching local browsers and required OS packages installed. One
  transient CDN DNS failure was diagnosed and the installer completed on its
  own alternate source without a changed test rerun.
- `uv lock --check`; `uv sync --frozen --all-groups`: PASSED with uv 0.12.5.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository
  tools`: PASSED — 110 files.
- `uv run --frozen mypy`: PASSED — 88 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 258 tests.
- `python -m compileall -q services/backend/src services/backend/tests tools
  tests/repository`: PASSED.
- PostgreSQL 16 run of `test_database_bootstrap.py`, `test_local_identity.py`,
  `test_human_session.py`, `test_local_authentication.py`,
  `test_control_database_integration.py`, and
  `test_control_auth_http_integration.py`: PASSED — 39 tests.
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED —
  29 tests in the final Compose run.
- `python -m unittest discover -s tests/supply_chain -p 'test_*.py'`: PASSED —
  29 tests.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  52 tests; `python tools/check_repository.py`: PASSED.
- `python tools/supply_chain/check_policy.py`; inventory and
  `generate_notices.py --check`: PASSED — Python 44, Node 148, total 192.
- `tools/supply_chain/run.sh /tmp/slaif-010r-evidence-final-20260821`:
  PASSED — six reproducible images, critical=0, policy-accepted high=51,
  checksum OK.
- `uv build --out-dir /tmp/slaif-010r-distributions`: PASSED — source and
  wheel distributions.
- `sudo tools/compose/smoke.sh slaif009rfinal`: PASSED — setup plus six browser
  projects, CSP/edge, database-login, secrets, readiness failures/recovery,
  restart, broken-bootstrap negative, Apache/NGINX syntax, 29 packaging tests,
  and bounded project cleanup; `compose-smoke: OK`.
- Changed-document/order Markdownlint 0.23.2 with `--no-globs`: PASSED — zero
  issues across ten files. The exact final report was separately linted before
  publication.
- Secret/artifact/URL/storage/network scans, exact paths and prior hashes,
  conflict-marker scan, clean status, and `git diff --check`: PASSED.
- Skipped required local tests: none.

## Diagnosed failures and CI generations

- The first exploratory `slaif010rsmoke` run completed all browser stages but
  an established readiness fixture rejected that project prefix. The fixture
  was outside scope; the required clean run used established safe family
  `slaif009rfinal` and passed. No unchanged failing test was rerun.
- Real browser proof initially exposed CSP-blocked Next hydration. The edge-to-
  Next per-request nonce contract fixed the cause without weakening CSP.
- The browser observer initially treated expected negative-auth 401 navigation
  cancellation as an unexpected failure. It was narrowed only to the explicit
  negative endpoints and browser cancellation conditions; all other errors
  remain fatal.
- A pre-commit supply-chain wrapper produced valid evidence but its final
  clean-tree assertion reported the intentionally uncommitted lock/notices
  diff. It was rerun after commit and passed. The final implementation head was
  then run again after the output-cleanup correction and passed.
- Initial GitHub CI generation: CI run `32427372397` and CodeQL run
  `32427372264`; 20 successful checks. Corrective code generations: zero.
  Workflow reruns: zero.

## GitHub CI / required checks

- Successful checks: CodeQL aggregate; Analyze actions; Analyze python;
  Analyze javascript-typescript; Detect supported languages; Repository
  policy; Dependency review; Mermaid; Markdown; Node contracts; Python 3.12,
  3.13, and 3.14 quality/package; Foundation PostgreSQL 14, 15, 16, 17, and 18;
  Supply-chain evidence; Compose and edge packaging.
- Implementation-head state: 20 successful, zero failed, cancelled, skipped,
  or pending.
- The report-only commit intentionally changes only this immutable report. Its
  final 20-check state is verified below before the FIFO response.

## Local setup / documentation / safety

- Used passwordless `sudo` only for disposable local browser dependencies and
  Docker/Compose/PostgreSQL test infrastructure. Matching Playwright browsers
  were installed for the normal and root test users required by the local
  execution path.
- Only fake credentials and project-scoped disposable data were used. No
  production system, data, credential, protected resource, external
  authenticated service, Docker socket in a product container, or unrelated
  host file was accessed.
- Unrelated files changed: no. Required scope deviation: no. Secret exposure:
  no. Production access: no. Skipped required test: no. Extra PR: NO. Merge:
  NO. Auto-merge: NO. Activated order and pointer were committed
  byte-identically.
- No site, workspace, OIDC, MFA, login-rate-limit, durable audit, editor,
  review, publication, or runtime browser-tool scope was added.

## Immutable hashes

- `AGENTS.md`:
  `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`:
  `00bdd82fcec0afaf65d2fbc2a2f9fa43a7d4e9e254d7a262bea0c5bae3be6b8a`
- `ARCHITECTURE.md`:
  `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- `ARCHITECTURE-for-agents.md`:
  `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Activated work order:
  `f23afe45393a2c8d646d310b8378373c0d69398bb5fcca84cfaba185799b29e6`
- Activated pointer:
  `d26dd779b0a1bea0037b7832c2c23fa3a306348824315ece4d78920f66b1c8fc`
- Prior 010-q report:
  `768c4df48ff039521f5df1e86efe4a0c0f4480b4416a71d012c3569e1594f503`

## Known limitations / blockers

- Implemented authentication remains local administrator only. OIDC, MFA,
  login rate limiting, durable security audit, sites, workspaces, editing,
  review, publication, and runtime agent browser tools remain unimplemented.
- Local HTTP proves the required non-Secure cookie behavior; production Secure
  cookie attributes remain unit/contract-proven because browsers cannot set
  Secure cookies through the required localhost HTTP test endpoint.
- Blockers: none. Acceptance and merge remain exclusively strategic-model
  authority.
