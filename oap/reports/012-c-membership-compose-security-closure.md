# OAP Coding-Agent Report — 012-c

## Work order

- Identifier: `012-c`; work-order file:
  `oap/orders/012-c-membership-compose-security-closure.md`; numeric objective:
  `012`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Amended the existing objective-012 PR with disposable, non-authenticatable OIDC
fixture identities and real NGINX/Playwright proof of the implemented RBAC
catalog and site-membership APIs. The setup browser project now exercises exact
catalogs, different roles on two sites, versioned update/deactivation, and
CSRF/self/cross-site/system/ceiling negatives while retaining the established
six-browser login, routing, responsive, and secret-leak coverage.

The landing page and bounded durable documentation now distinguish the
implemented authenticated APIs from deferred membership UI, invitations,
custom roles, content, workspaces/capabilities, editing/Puck, review, and
publication execution. The final implementation generation completed all 20
GitHub checks successfully.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#24](https://github.com/ulfe-lmi/slaif-agent-site/pull/24); state: `OPEN`,
  merge state `CLEAN`, mergeable, ready/non-draft, zero reviews
- Base/head branches: `main` / `oap/012-membership-rbac`
- Starting remote SHA: `44bad40aa648f32521a7216e44ffb04af256993e`
- Implementation head SHA: `46dc01c239b482bbf6cb5fc82eb14737c715a91c`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified after push)
- Implementation commits pushed:
  `944cd27259e44f6efc22a5b0f6cf10dc5cdeae3a` and
  `46dc01c239b482bbf6cb5fc82eb14737c715a91c`; report
  parent=implementation SHA
- New PR this round: no; amended existing PR: yes; workflow rerun: NO;
  corrective implementation generation: ONE; merge/close/auto-merge: NO

## Fixture creation, confinement, and destruction

- After a clean healthy stack and before browser setup, the smoke harness uses
  the disposable PostgreSQL administrator to transactionally insert exactly two
  fixed ACTIVE OIDC accounts. Both have distinct fixed UUIDs, subjects, and
  display names, issuer `https://fixture.invalid`, and null local username,
  normalized username, password hash, and email.
- The transaction fails on an initialized installation, any administrator or
  membership row, or either fixed-account collision. It never updates an
  existing account.
- The accounts are not bootstrap/demo/product seed data. A static packaging
  contract proves both UUIDs are absent from Compose, migrations, and product
  backend source and that the only insert is in the smoke harness.
- Their UUIDs cross into Playwright only as non-secret JSON metadata in the
  existing mode-0600 secret file. Setup token, human password, session, and CSRF
  material remain out of command arguments, URLs, logs, and artifacts.
- Owner-side post-E2E assertions prove exactly two OIDC fixture accounts, no
  local credentials/email/Platform Administrator assignment, and exactly the
  expected three membership rows. Normal cleanup destroyed the exact project's
  containers and volumes locally and in CI; no `slaif012membership_*` volume
  remained after the local attempts.

## Browser/API evidence

- Catalog reads traverse NGINX using the real setup-created session and verify
  the exact seven roles, ceilings/default permissions, stable permission fields,
  nonassignable installation/system scopes, private response headers, and no
  credential/profile fields.
- The setup project discovers the demo site and API-created second site. Fixture
  one receives `CONTENT_EDITOR` on demo and `SITE_ARCHITECT` on second; fixture
  two receives `VIEWER` on demo only. List/get results remain exact per site,
  while fixture two on the second site receives constant `404`.
- An exact-version update adds only `site:publish` on the second-site
  membership and increments version 1→2. A stale version receives `409`.
  Missing and wrong CSRF receive `403` with the stored membership unchanged.
- Self-membership mutation and the nonassignable `schema:migrate` override
  receive `403`. A `VIEWER` ceiling above its role maximum is rejected by the
  existing request contract with `422`; this is input validation before actor
  authority and no backend contract was changed.
- Local login for the OIDC fixture username receives `401` and emits no session
  cookie. Semantic DELETE with exact version 2 returns INACTIVE version 3,
  retains role/ceiling/allow override, empties effective permissions, and later
  authorization remains denied.
- Every expected 4xx is registered with the browser observation harness. The
  existing routed-site, archive, cookie, logout/replay, console/network,
  keyboard, narrow-width, and secret non-leak assertions remain active.

## Compose/runtime evidence

- GitHub job `96684016588` ran the authoritative clean generation with the
  established safe `slaif007ci` project family and ended `compose-smoke: OK`.
- Markers included `membership-fixtures: OK count=2 kind=OIDC
  authenticatable=no installation=uninitialized`, all setup/desktop Chromium,
  Firefox, WebKit, tablet, mobile Chromium, and mobile WebKit projects PASSED,
  `compose-e2e: OK projects=6 setup-viewports=2 artifacts=disabled`, and
  `membership-e2e: OK fixtures=2 sites=2
  lifecycle=created-updated-deactivated privacy=verified`.
- The same run passed edge request-ID/header policy, exact database login
  policy, secret-file and Render-secret policy, Control readiness failures and
  recovery, stop/start fingerprints, membership persistence without fixture
  recreation or setup-material reissue, fail-closed Render locator corruption
  and recovery, and the broken-bootstrap negative.
- The existing topology check continued to prove only NGINX publishes loopback
  port 8080 and all Control route-policy declarations validate at startup.
  Image history, rendered configuration, logs, HTML, and Playwright output
  secret/locator scans passed.

## Landing page and documentation

- The localhost status surface now calls secure setup/session, trusted
  multi-site routing, Platform Administrator site/domain APIs, site-scoped
  built-in RBAC/membership APIs, publication separation, and route-policy
  declarations implemented.
- Its deferred list explicitly retains site/membership UI, invitations, custom
  roles, content models/content, workspaces/capabilities, editing/Puck, review,
  and publication execution. Source assertions prevent regression to calling
  the APIs absent or overclaiming UI/content/publication execution.
- `README.md` and bounded deployment, operations, security, and site documents
  now describe the Control HTTP surface and clearly label the identities as
  disposable test-harness state, never demo/product users.

## Files changed

- Harness/E2E: `tools/compose/smoke.sh`, `tools/compose/e2e.sh`,
  `tests/packaging/test_compose_smoke_contract.py`,
  `tests/e2e/setup.spec.ts`, and `tests/e2e/support.ts`.
- Status surface: `apps/web/app/page.tsx` and
  `apps/web/tests/surface.test.mjs`.
- Documentation: `README.md`, `docs/DEPLOYMENT.md`, `docs/OPERATIONS.md`,
  `docs/SECURITY.md`, and `docs/SITES.md`.
- Strategic-owned transcript committed byte-identically: `oap/active` and
  `oap/orders/012-c-membership-compose-security-closure.md`.

## Acceptance-criteria evidence

1. PASSED — the two non-login OIDC accounts exist only in the disposable smoke
   database, collision/non-fresh state fails, and cleanup destroys them.
2. PASSED — real NGINX browser/API E2E proves catalogs, two-site different-role
   lifecycle, privacy, CSRF/self/cross-site/system/ceiling/version negatives,
   semantic deactivation, denial, and no credential leakage.
3. PASSED — setup/auth/routing, six browser/device projects, stop/start,
   readiness, secret topology, Render failure/recovery, negative bootstrap, and
   NGINX-only publication remain green.
4. PASSED — landing and durable documentation separate implemented APIs from
   absent UI, invitations, custom roles, content/workspaces, and publication.
5. PASSED — no backend, schema, migration, API, topology, dependency, lockfile,
   product seed, or adjacent feature changed.
6. PASSED — PR #24 alone remains open, ready, mergeable, and clean with 20/20
   current-head checks green; no workflow rerun, extra PR, merge, or auto-merge.

## Local verification and exact outcomes

- `sh -n tools/compose/smoke.sh tools/compose/e2e.sh`: PASSED.
- `python -m unittest tests.packaging.test_compose_smoke_contract`: PASSED —
  four tests.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  52 tests.
- `python tools/check_repository.py`: PASSED.
- Exact CI Ruff commands over backend/repository/packaging/supply-chain/tools/
  migrations: PASSED; 137 files already formatted.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`, `pnpm format:check`, and `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — Web 6/6, browser worker 1/1, contract 2/2, including
  the production build invoked by the test script.
- `pnpm build`: PASSED independently after the test chain.
- Changed Markdown/order lint with
  `npx --yes markdownlint-cli2@0.23.2 --no-globs ...`: PASSED — six files,
  zero issues.
- `git diff --check` and staged diff check: PASSED.
- Immutable hashes, starting-parent topology, changed-content locator/secret
  review, exact remote head, and post-cleanup volume checks: PASSED.

## Corrections, failures, retries, and skips

- A first local Docker invocation failed before creating resources because the
  current user lacked Docker-socket permission. Per the local-autonomy contract,
  the clean generation was started with passwordless `sudo`; this was routine
  infrastructure setup, not an E2E generation retry.
- The first actual local generation reached a healthy 28-container stack, then
  the new fixture precondition referenced nonexistent `initialized`. Schema
  inspection identified `initialized_at`; the predicate was corrected and the
  focused shell/packaging gates passed before the permitted additional clean
  generation.
- That additional generation passed the complete new fixture/membership flow
  and all six browser/device projects, then the unchanged readiness helper
  rejected the ad hoc `slaif012membership` project family. The unnecessary
  wrapper-only family expansion was removed, restoring the established
  `007/009/010` contract. The retry cap was honored, so no third local clean
  generation ran. GitHub's authoritative established `slaif007ci` clean
  generation subsequently passed the entire smoke.
- The initial implementation head's Python 3.13 CI job failed only Ruff E501 on
  one 90-character packaging-test signature. Logs were inspected; the signature
  was wrapped, exact Ruff and packaging gates passed locally, and one permitted
  corrective implementation generation was pushed. No workflow rerun occurred.
- The first push attempt for that corrective commit failed before remote contact
  because DNS temporarily could not resolve GitHub. The authorized publication
  retry succeeded without changing the implementation.
- Required verification skipped: none. Deliberately not run per order: local
  PostgreSQL matrices, backend experiments, browser-worker experiments, broad
  image/SBOM generation, and Mermaid. GitHub supplied the unchanged authoritative
  database 14–18, image, supply-chain, and Mermaid gates.

## GitHub CI / required checks

- Final implementation workflow run `32452694963` plus CodeQL run
  `32452694981`; all 20 checks reached terminal `SUCCESS`, with zero failed,
  pending, cancelled, skipped, or missing checks.
- SUCCESS: Repository policy; Node contracts; Python 3.12, 3.13, and 3.14
  quality and package; Foundation PostgreSQL 14, 15, 16, 17, and 18; Compose
  and edge packaging; Supply-chain evidence; Markdown; Mermaid; Dependency
  review; Detect supported languages; Analyze actions; Analyze python; Analyze
  javascript-typescript; CodeQL.
- All required green at report drafting: yes. The report-only commit may trigger
  fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Existing frozen uv/Python and Node/pnpm toolchains, Docker/Compose via
  passwordless sudo, locally installed Playwright browser images in the built
  test container, exact Markdown checker, and GitHub CLI were used.
- No package, dependency, lockfile, service topology, or durable host setup was
  added or changed.

## Safety and scope confirmations

- Unrelated files changed or discarded: no. Prior orders/reports changed: no.
- Activated order or `oap/active` edited by coding agent: no; their exact
  strategic bytes were only committed.
- Production systems/data/credentials or unrelated host files accessed: no.
  The local Docker socket was used only through passwordless sudo for the
  explicitly required disposable test infrastructure.
- Real secrets accessed, printed, or committed: no. Fixture identities have no
  usable credential and UUIDs are non-secret test metadata.
- Scope deviation: no. Dependencies/lockfiles changed: no.
- Extra objective PR: NO. Workflow rerun: NO. Corrective generation: ONE.
  Coding-agent merge/close/auto-merge: NO.
- Report commit changes only this report: yes.

## Immutable hashes

- `AGENTS.md`:
  `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`:
  `00bdd82fcec0afaf65d2fbc2a2f9fa43a7d4e9e254d7a262bea0c5bae3be6b8a`
- `ARCHITECTURE-for-agents.md`:
  `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Activated work order:
  `23d26519c1f9092a13e410b58708bdf457d3a487bf6c6473f03c9cc0d3080702`
- Activated pointer:
  `894d647deaad609fccf1866aaa86cca0bb8f70b754004eb221592df0dc45d5f0`

## Known limitations / blockers

- No blocker remains for 012-c.
- Membership/site UI, invitations, custom roles, OIDC login, user CRUD,
  content/COW, workspaces/capabilities, editing/Puck, review, and publication
  execution remain unimplemented by design.

## Recommended strategic follow-up

Independently verify the report-only head and the implementation generation's
20/20 evidence. Only the strategic model may accept or merge PR #24, activate
another bounded work order, or declare the planned roadmap complete.
