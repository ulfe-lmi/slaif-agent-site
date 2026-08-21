# OAP Coding-Agent Report — 011-c

## Work order

- Identifier: `011-c`; work-order file:
  `oap/orders/011-c-render-resolution-auth-repair.md`; numeric objective: `011`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Amended the unique objective-011 PR with all three ordered repairs. Markdownlint
now ignores only the exact immutable 011-b order while MD018 remains enforced.
State-changing Control authentication proves the session and bound CSRF before
one finalization, preserves 401/403/503 classification, and leaves denial rows
unchanged. Render now has a fixed public-reader configuration/pool, a
resolver-only persistence service, and exactly one internal site-context route.

The first implementation generation exposed a clean-Compose compatibility
defect because the deliberately unwired Render locator made the existing
development scaffold unhealthy. After inspecting the completed failure log, one
corrective generation retained the health-only development Compose scaffold
until the fixed locator is mounted; it did not add Compose wiring or weaken the
configured Render database boundary. Corrected-head CI completed 20/20
successfully.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#23](https://github.com/ulfe-lmi/slaif-agent-site/pull/23); state: `OPEN`,
  ready/non-draft, no reviews
- Base/head branches: `main` / `oap/011-sites-trusted-resolution`
- Starting remote SHA: `8bf66f832dd83b7eb578904b483e53b8702d0229`
- Implementation head SHA: `703bcbfcfb42b5c304c63e61e5bc06df22ec4a02`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commits pushed before report:
  `1384f1aadb3a7051145417ec89b7b1b94c10127a`,
  `703bcbfcfb42b5c304c63e61e5bc06df22ec4a02`; report
  parent=implementation SHA
- New PR this turn: no; amended existing: yes; PR body updated: yes; kept
  ready/non-draft: yes; merge performed: NO; auto-merge enabled: NO; workflow
  rerun: NO

## Changes made

- Added the documented exact Markdownlint ignore for
  `oap/orders/011-b-platform-admin-site-http.md`; repository policy rejects
  broader order/report globs. The immutable file retained its required hash.
- Added internal typed session/CSRF failure reasons. Mutation HTTP helpers no
  longer call safe authentication first; valid mutation requests call only the
  bound state-changing method, and malformed/wrong CSRF is inspected without a
  persistence finalization or session-row mutation.
- Extracted `SiteResolver`, whose only public operation is normalized
  `resolve(authority, request_path)`. The broader Control service delegates its
  existing resolution behavior to this narrow class.
- Added fixed Render settings for `slaif_public_login`,
  `slaif_public_reader`, `/run/slaif-render/render-dsn`, and
  `slaif-render-api`, including safe file, test-locator, TLS, pool identity,
  readiness, cancellation, and bounded shutdown behavior.
- Granted the public reader exact schema usage and execute only on
  `slaif_site_resolve(text,text)` and `slaif_site_resolve_local(text)`. It has
  no Control relation, lifecycle, domain-management, administrator, identity,
  setup, migration, reviewer, or writer authority.
- Added `POST /internal/render/v1/site-context` with an extra-forbid two-field
  request and routing-facts-only response. It maps constant not-found to 404,
  ambiguity to 409, and persistence/configuration failure to 503, with private
  no-store/noindex and request-ID headers.
- Added unit, route-inventory, packaging-boundary, repository-policy, and real
  PostgreSQL public-reader tests. Added the Render integration module to the
  existing PostgreSQL 14–18 job without changing the 20 check names.
- Documented the internal API, normalized resolution, least-privilege role,
  locator contract, operations/security boundary, absent deployment wiring,
  and explicitly deferred product surfaces.

## Files changed

- `.github/workflows/ci.yml`, `.markdownlint-cli2.yaml`, `README.md`
- `docs/API.md`, `docs/CONFIGURATION.md`, `docs/DATABASE_ROLES.md`,
  `docs/OPERATIONS.md`, `docs/SECURITY.md`, `docs/SITES.md`
- `oap/active`, `oap/orders/011-c-render-resolution-auth-repair.md`
- `services/backend/src/slaif_agent_site/identity/sessions.py`,
  `control_api/auth_http.py`
- `services/backend/src/slaif_agent_site/render_api/{__init__,__main__,app,config,database,site_http}.py`
- `services/backend/src/slaif_agent_site/sites/{resolver,service}.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/013_001_site_foundation.py`,
  `db/privileges.py`
- `services/backend/tests/unit/test_control_auth_http.py`,
  `test_foundation_contract.py`, `test_health_apps.py`,
  `test_process_entrypoints.py`, `test_render_api.py`
- `services/backend/tests/integration/test_render_site_resolution.py`
- `tests/repository/test_repository_policy.py`, `tools/check_repository.py`

## Acceptance-criteria evidence

### Criterion 1 — one bound mutation decision and stable failures

- PASSED. The focused fake proves state-changing HTTP invokes only
  `authenticate_state_changing`, never both authentication methods. Existing
  real PostgreSQL snapshots prove malformed/wrong/unknown credentials leave
  digest, last-seen, absolute expiry, recent-auth, and revocation columns
  byte/column unchanged. A successful bound request performs one finalizer and
  returns one immutable context. Combined Control/site HTTP tests preserve 401
  session, 403 current-session CSRF, and 503 persistence classification.

### Criterion 2 — exact immutable Markdown repair

- PASSED. The 011-b order SHA-256 remains
  `9af8550e4731939c9d1f60d93a1a62bbf5d967f3833bae6133595e73aac4cea8`.
  Only that exact order path was added to ignores. Repository tests reject an
  order directory/glob or alternate report/order exclusion. A temporary
  non-exempt `#23, ...` fixture failed MD018 exactly; corrected-head GitHub
  Markdown succeeded.

### Criterion 3 — isolated Render public-reader authority

- PASSED. Settings and pool identity are fixed and secret-safe. Real PostgreSQL
  tests use the actual fixture login with sole `slaif_public_reader` membership,
  resolve through both exact functions, and receive insufficient-privilege for
  site relations, list/get management, and administrator authorization. Exact
  bootstrap privilege verification passes.

### Criterion 4 — routing behavior and no authorization

- PASSED. Real PostgreSQL covers two sites, same-host root and `/docs`, longest
  segment boundary, `/docs-other`, local `/s/<key>`, case/port/trailing-slash
  normalization, archive, reserved path, encoded dot, and backslash denial.
  Unit HTTP evidence proves forged site/workspace headers are ignored and the
  response contains only site UUID/key, canonical revision, locale, and matched
  host/prefix.

### Criterion 5 — bounded product scope

- PASSED. No seed, Web/Next.js, edge route, Compose configuration/volume/secret,
  dependency/lock/image, membership, content/COW, workspace/capability, media,
  browser, or publication implementation changed. Two mechanical existing-test
  inventories were updated solely because the ordered Render modules now ship
  and Render is the second intentionally asyncpg-owning online package.

### Criterion 6 — unique PR and complete CI

- PASSED. Only PR #23 was amended and kept ready. The implementation head is
  exactly `703bcbfcfb42b5c304c63e61e5bc06df22ec4a02`; corrected-head CI is
  20/20 successful. No PR creation, workflow rerun, merge, close, or auto-merge
  occurred.

## Local verification

- `uv lock --check`; `uv sync --frozen --all-groups`: PASSED — 45 resolved,
  44 checked packages.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository
  tools`: PASSED — 114 files.
- `uv run --frozen mypy`: PASSED — 103 source files.
- `python -m compileall -q tools tests/repository services/backend/src`:
  PASSED.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 326 tests.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 58
  tests in 253.20 seconds against disposable PostgreSQL 16.
- Combined focused session/Control/site/Render run: PASSED — 279 tests.
- Final focused Render/process/session/repository runs: PASSED — 78 tests plus
  22 subtests, and 36 Render/process tests after the CI correction.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-011c`: PASSED — sdist
  and wheel built.
- `python tools/check_repository.py`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  52 tests.
- Tracked-file Markdownlint 0.23.2: PASSED. Deliberate non-exempt MD018 fixture:
  FAILED as expected with exactly MD018. No fixture remained.
- `python tools/check_mermaid.py`: FAILED locally — Mermaid CLI 11.16.0 returned
  opaque `[object Object]` for all diagrams and for a separately diagnosed
  two-node fixture. No Mermaid source changed; authoritative corrected-head
  Mermaid CI succeeded.
- All ten `uv run --frozen python -m slaif_agent_site.<process> --check`
  commands: PASSED, including `render-api: CHECK_OK`; no locator was read and no
  connection opened.
- `git diff --check`, conflict-marker, sensitive-diff, remote-head, route,
  privilege, and immutable-hash checks: PASSED.
- Local Node, Compose, Playwright/browser, image, and broad SBOM suites: NOT RUN
  as explicitly prohibited by the work order. Their unchanged GitHub Node,
  Compose, and supply-chain jobs all ran and succeeded.

## GitHub CI / required checks

- First implementation CI run `32436152412`: 19 successes and one Compose
  failure; CodeQL run `32436152389`: success. Diagnosis: unwired Render locator
  caused the unchanged development Compose Render container to remain
  unhealthy. Workflow rerun: NO.
- One permitted corrective implementation generation was pushed. Corrected CI
  run `32436582555` and CodeQL run `32436582826` completed 20/20 SUCCESS.
- SUCCESS: Repository policy; Node contracts; Python 3.12, 3.13, and 3.14;
  Foundation PostgreSQL 14, 15, 16, 17, and 18; Compose and edge packaging;
  Supply-chain evidence; Markdown; Mermaid; Dependency review; Detect supported
  languages; Analyze actions, python, and javascript-typescript; CodeQL.
- Implementation-head state: 20 successful, zero failed, pending, cancelled,
  skipped, or missing. All required green at drafting: yes.
- The report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Used the existing disposable PostgreSQL service, fake credentials, uv 0.12.5,
  and exact transient Markdownlint/Mermaid tools. No sudo package installation
  was required.
- No production dependency or lockfile changed. No generated test/render output
  remains in the repository.

## Documentation

- Documented the internal endpoint and safe fields/statuses, resolver-only
  authority, exact public-reader grants, normalization behavior, Render locator
  and lifecycle, configured versus undeployed development behavior, and stable
  session/CSRF mutation semantics.
- Explicitly documents no public rendering, edge wiring, demo seed, UI,
  membership, content, workspace, capability, or publication behavior.

## Safety and scope confirmations

- Unrelated files changed: no. Existing package/process inventory tests changed
  only as mechanically required by ordered Render modules/asyncpg ownership.
- Production secrets accessed: no; production systems/data accessed: no.
- Required tests skipped/not run: no. Explicitly prohibited unchanged local
  suites are identified above and ran authoritatively in GitHub.
- Scope deviation: no. Extra objective PR: NO. Coding-agent merge: NO.
  Auto-merge: NO. Workflow rerun: NO.
- Activated order/active edited: NO; committed byte-identically.
- Report commit changes only this report: yes.
- Credential, cookie, token, digest, DSN, SQL/driver/locator, user, or private
  artifact exposure: no.

## Immutable hashes

- `AGENTS.md`:
  `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`:
  `00bdd82fcec0afaf65d2fbc2a2f9fa43a7d4e9e254d7a262bea0c5bae3be6b8a`
- `ARCHITECTURE-for-agents.md`:
  `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Activated work order:
  `208ebce8d1204b6efa2cc6285bf74143a1f84efe0c9415db0221621972c3e9fb`
- Activated pointer:
  `1ce0cc0538e5d0b2a9c0df13796331f6a783bf3d833d55f5770e40b53768eb56`
- Immutable 011-b order:
  `9af8550e4731939c9d1f60d93a1a62bbf5d967f3833bae6133595e73aac4cea8`

## Known limitations / blockers

- No blocker remains for this bounded round. Local Mermaid rendering was
  unavailable for an environment/tool reason recorded above; corrected-head
  authoritative Mermaid CI passed.
- The development Compose Render process remains intentionally health-only
  because this order forbids distributing/mounting its locator. Demo seed,
  public/edge rendering, UI, membership, content, workspaces, capabilities, and
  publication remain deferred.

## Recommended strategic follow-up

Independently review this report, implementation diff, exact grants, and
corrected 20/20 CI, then decide whether to activate the bounded 011-d
continuation on this same PR.
