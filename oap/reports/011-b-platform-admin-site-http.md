# OAP Coding-Agent Report — 011-b

## Work order

- Identifier: `011-b`; work-order file:
  `oap/orders/011-b-platform-admin-site-http.md`; numeric objective: `011`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Amended the unique objective-011 PR with the exact nine authenticated Platform
Administrator site/domain routes, a reusable strict human-session/CSRF helper,
an owner-defined active-administrator authorization function, active trusted
site-context and domain-list services, and database-level stale-context archive
protection. Real PostgreSQL/FastAPI tests cover two-site lifecycle, quota,
normalization, cross-site substitution, authorization, CSRF, private headers,
revoked/expired sessions, persistence failure, and stale pre-archive contexts.

Implementation and all code/security/packaging checks passed. Completion is
`PARTIAL` because Markdownlint fails on line 25 of the immutable strategy-owned
work order: its prose line begins literal `#23,` and triggers MD018. The coding
agent preserved the activated order byte-identically and did not weaken lint.
GitHub therefore completed 19/20 checks successfully with Markdown failed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#23](https://github.com/ulfe-lmi/slaif-agent-site/pull/23); state: `OPEN`,
  ready/non-draft
- PR title: `[OAP 011] Establish sites and trusted resolution`
- Base/head branches: `main` / `oap/011-sites-trusted-resolution`
- Starting remote SHA: `5aa4dd9c32852f40a5ffe60dd2b239871525ff16`
- Implementation head SHA: `da8cfe5bf9663d3a7acc4172f60436e5e0854a7c`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commit pushed before report:
  `da8cfe5bf9663d3a7acc4172f60436e5e0854a7c`; report
  parent=implementation SHA
- New PR this turn: no; amended existing: yes; PR body updated: yes; marked
  ready/non-draft: yes; merge performed: NO; auto-merge enabled: NO; workflow
  rerun: NO

## Changes made

- Added reusable strict safe-read session authentication and state-changing
  session-plus-bound-CSRF proof, preserving existing setup/login/session/logout
  contracts. Site successes and errors receive private/no-store/noindex headers.
- Added an owner-defined fixed-search-path function that authorizes only an
  active user with a current `control.platform_administrator` row. Control has
  exact execute only; no generic query or relation grant was exposed.
- Added exactly nine `/api/control/v1/sites` method routes for create/list/get,
  profile update, idempotent archive, and domain list/create/replace/delete.
  Frozen extra-forbid models and server-parsed UUIDs exclude caller-owned IDs,
  status, revisions, catalog version, timestamps, and routing authority.
- Added trusted active-context and domain-list functions/service methods.
  Archived sites remain inspectable but all later profile/domain mutation is a
  stable conflict.
- Amended unmerged revision `013_001`: update, domain add/replace, and domain
  remove now lock and reassert active status within their own transaction.
  Cross-site domain mismatch returns constant not-found; primary removal and
  inactive state return conflict; downgrade and exact grants were updated.
- Added real FastAPI plus actual-`slaif_control` PostgreSQL evidence and direct
  stale-context semantic tests. Added the HTTP suite to PostgreSQL 14–18 without
  changing the 20 check names.
- Updated PR body and durable API, site, database-role, operations, and README
  documentation. No UI, edge, Compose, dependency, seed, membership, content,
  workspace, DNS, public rendering, or publication behavior was added.

## Files changed

- `.github/workflows/ci.yml`, `README.md`
- `docs/API.md`, `docs/SITES.md`, `docs/DATABASE_ROLES.md`,
  `docs/OPERATIONS.md`
- `oap/active`, `oap/orders/011-b-platform-admin-site-http.md`
- `services/backend/src/slaif_agent_site/control_api/app.py`, `auth_http.py`,
  `database.py`, `site_http.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/013_001_site_foundation.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/sites/models.py`, `service.py`
- `services/backend/tests/integration/test_sites.py`,
  `test_site_control_http_integration.py`
- `services/backend/tests/unit/test_control_database.py`,
  `test_foundation_contract.py`, `test_health_apps.py`
- `tests/repository/test_repository_policy.py`, `tools/check_repository.py`

## Route and status inventory

- `GET /sites`: 200; `POST /sites`: 201
- `GET /sites/{site_id}`: 200; `PATCH /sites/{site_id}`: 200
- `POST /sites/{site_id}/archive`: 200
- `GET /sites/{site_id}/domains`: 200;
  `POST /sites/{site_id}/domains`: 201
- `PUT /sites/{site_id}/domains/{domain_id}`: 200;
  `DELETE /sites/{site_id}/domains/{domain_id}`: 204
- Stable mapping: authentication 401; administrator/CSRF 403; missing or
  cross-site resource 404; duplicate/quota/primary/archived conflict 409;
  request/domain validation 422; persistence unavailable 503.

## Acceptance-criteria evidence

### Criterion 1 — nine administrator-only routes and CSRF

- PASSED implementation evidence. Source inventory contains exactly nine route
  decorators. Real HTTP tests prove the setup-created Platform Administrator can
  exercise every method; safe GET succeeds without CSRF; every mutation rejects
  missing, malformed/wrong, or duplicate CSRF. Valid non-administrator receives
  403; unauthenticated, invalid, revoked, expired, duplicate-cookie, and
  alternate-mode-cookie requests receive 401.

### Criterion 2 — context and substitution safety

- PASSED. Bodies reject extra/caller-owned identity and revision fields before
  persistence. Handlers resolve server-parsed path UUIDs through get plus the
  database-created active context. A Site-A path with Site-B domain UUID returns
  constant 404 and leaves both mappings unchanged. Errors contain no credential,
  user marker, SQL, driver, or locator detail.

### Criterion 3 — transactional active recheck

- PASSED. Database functions lock and reassert active state for profile update,
  mapping add, replace, and remove. A direct semantic test retains one active
  context, archives the site, then proves all four operations conflict without
  changing profile or mappings. Archive remains idempotent and row-preserving.

### Criterion 4 — existing boundaries and bounded scope

- PASSED. Combined bootstrap/setup/identity/auth/session/Control/site suites
  pass. Exact function/grant and relation inventories pass. All five PostgreSQL
  matrix jobs, existing Compose, Node, supply-chain, repository, Mermaid,
  Python, and CodeQL checks pass. No prohibited product/dependency scope entered.

### Criterion 5 — PR state and CI

- PARTIAL. Exactly PR #23 was amended and made ready/non-draft; no new PR,
  rerun, merge, close, or auto-merge occurred. Implementation-head CI is 19/20:
  only Markdown failed on immutable order line 25 MD018. Achieving 20/20 requires
  strategy-owned correction/resolution of that artifact; coding cannot edit it.

## Local verification

- `uv lock --check`; `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository
  tools`: PASSED — 108 files.
- `uv run --frozen mypy`: PASSED — 97 source files.
- `python -m compileall -q services/backend/src services/backend/tests tools
  tests/repository`: PASSED.
- `uv run --frozen pytest -q services/backend/tests/unit tests/repository
  tests/packaging`: PASSED — 352 tests and 56 subtests.
- Combined PostgreSQL 16 run of database bootstrap, installation setup, local
  identity/authentication, human session, Control auth HTTP/database, sites,
  and site Control HTTP: PASSED — 53 tests.
- Final focused site HTTP lifecycle test after successful PUT/204 additions:
  PASSED — 1 test.
- `python tools/check_repository.py`: PASSED.
- Changed durable docs Markdownlint 0.23.2 with `--no-globs`: PASSED — zero
  issues across five files.
- Activated-order Markdownlint with `--no-globs`: FAILED — exactly
  `oap/orders/011-b-platform-admin-site-http.md:25:1 MD018`, context begins
  `#23, never merge/close/auto-me...`. The immutable order was not edited.
- `git diff --check`, conflict-marker scan, exact route inventory, strategic
  hashes, and sensitive-diff scan: PASSED.
- Local Node, browser/Playwright, Compose, and broad image/SBOM suites: NOT RUN
  as explicitly prohibited/unchanged by the work order. Their authoritative
  GitHub jobs ran; Node, Compose, and supply-chain all passed.

## GitHub CI / required checks

- Initial and only CI run: `32433423200`; CodeQL run: `32433423181`.
- SUCCESS: Repository policy; Dependency review; Mermaid; Node contracts;
  Python 3.12, 3.13, and 3.14 quality/package; Foundation PostgreSQL 14, 15,
  16, 17, and 18; Compose and edge packaging; Supply-chain evidence; Detect
  supported languages; Analyze actions; Analyze python; Analyze
  javascript-typescript; CodeQL aggregate.
- FAILURE: Markdown — exact log reports only immutable work order line 25,
  MD018/no-missing-space-atx.
- Implementation-head state: 19 successful, one failed, zero pending,
  cancelled, skipped, or missing.
- All required green at drafting: no.
- Corrective code generations: zero. Workflow reruns: zero.
- The report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Used existing disposable PostgreSQL test infrastructure and fake credentials.
  No sudo setup or package installation was required.
- No dependency or lockfile changed. Transient Markdownlint used the already
  approved exact CLI and committed no output.

## Documentation

- Documented exact routes, statuses, bodies, safe response fields,
  session+CSRF+active-administrator chain, stable errors/private headers,
  normalization/quota, transactional archive/no-delete behavior, role grants,
  and institutional-tenancy limitation.
- Explicitly deferred UI, membership/RBAC, demo seed, anonymous routing/render,
  DNS, content, workspaces, publication, hostile tenancy, and production-ready
  claims.

## Safety and scope confirmations

- Unrelated files changed: no. `test_health_apps.py` was directly affected and
  updated only to enumerate the newly ordered Control route templates.
- Production secrets accessed: no; production systems/data accessed: no.
- Required tests skipped/not run: no. Explicitly prohibited unchanged local
  suites are recorded above and ran authoritatively in GitHub.
- Scope deviation: no. Extra objective PR: NO. Coding-agent merge: NO.
  Auto-merge: NO. Workflow rerun: NO.
- Activated order/active edited: NO; committed byte-identically.
- Report commit changes only this report: yes.
- Credential, cookie, token, hash, DSN, SQL detail, cross-site detail, or secret
  exposure: no.

## Immutable hashes

- `AGENTS.md`:
  `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`:
  `00bdd82fcec0afaf65d2fbc2a2f9fa43a7d4e9e254d7a262bea0c5bae3be6b8a`
- `ARCHITECTURE-for-agents.md`:
  `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Activated work order:
  `9af8550e4731939c9d1f60d93a1a62bbf5d967f3833bae6133595e73aac4cea8`
- Activated pointer:
  `c050b517a63f73852c333f8a5f2ae49a3ecb5ae52712f7e401b23b18db0b67e6`
- Prior 011-a report:
  `cd385606398afa529d58baa469c5e7f9b4c22b094f6a1a44363865135debea7d`

## Known limitations / blockers

- Blocker: the immutable activated order contains the sole Markdownlint error.
  The coding agent cannot edit strategy-owned order bytes or weaken CI. A later
  authorized strategic action must resolve this before 20/20 can be claimed.
- Site UI, membership/RBAC, demo seed, anonymous public rendering/routing,
  edge multi-site proof, DNS automation, content, workspaces, and publication
  remain absent by design.

## Recommended strategic follow-up

Resolve the strategy-owned Markdown artifact, then independently review the
implementation and decide whether to activate bounded 011-c on this same PR.
