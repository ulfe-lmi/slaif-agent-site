# OAP Coding-Agent Report — 011-a

## Work order

- Identifier: `011-a`; work-order file:
  `oap/orders/011-a-site-domain-context-foundation.md`; numeric objective:
  `011`
- PR mode: `CREATED_NEW_PR`

## Status

COMPLETE

## Executive summary

Created the unique objective-011 PR and implemented its bounded persistence and
trusted-resolution foundation. Revision `013_001` adds owner-only non-COW site,
domain-mapping, and installation-bound quota data; exact Control-only semantic
functions; deterministic shared normalization; an immutable server-created
`SiteContext`; and fail-closed hostname/path/local-site resolution. PostgreSQL
tests prove concurrent quota enforcement, two-site isolation, archive/no-delete,
primary mapping rules, cancellation rollback, and the exact denial matrix.
Public site CRUD HTTP/UI, membership, content, DNS automation, and edge routing
remain deferred. The single initial GitHub generation passed 20/20 checks.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#23](https://github.com/ulfe-lmi/slaif-agent-site/pull/23); state: `OPEN`
  (draft)
- PR title: `[OAP 011] Establish sites and trusted resolution`
- Base/head branches: `main` / `oap/011-sites-trusted-resolution`
- Starting remote SHA: `ffe9c868353e521dffed88dc623ea9704a7c813c`
- Implementation head SHA: `388244d03854ca7932fb25addd0a7b8be2a2da71`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commit pushed before report:
  `388244d03854ca7932fb25addd0a7b8be2a2da71`; report
  parent=implementation SHA
- New PR this turn: yes; amended existing: no; merge performed: NO;
  auto-merge enabled: NO; workflow rerun: NO

## Changes made

- Added deterministic migration `013_001` after `012_001` with
  `control.site_policy`, `control.site`, and `control.site_domain`, exact
  constraints/indexes, restrictive ownership/grants, nine bounded
  `SECURITY DEFINER` functions, and deterministic downgrade.
- Enforced an installation-bound `max_sites` default of 100, bounded 1–1000,
  by locking its singleton before counting/inserting so concurrent creation
  cannot exceed quota.
- Added shared typed normalization for lowercase bounded site keys, IDNA ASCII
  hostnames and separated authority ports, canonical path prefixes/request
  paths, reserved product namespaces, and a deterministic BCP47-like locale
  subset.
- Added frozen request/result models and a frozen, slots-based `SiteContext`
  whose public constructor fails; only a private trusted database-result
  factory creates it.
- Added the Control-only semantic service for create/get/list/update/archive,
  domain put/update/remove, normal resolution, and local `/s/<key>` resolution.
  Site-owned mutations require trusted context and stable safe errors.
- Added exhaustive unit and PostgreSQL integration coverage, including
  Unicode/IDNA equivalence, malformed routing input, path boundaries, reserved
  namespaces, two-site substitution, primary reassignment/removal, revisions,
  archive persistence, cancellation, quota concurrency, and all role denials.
- Added the site integration suite to all PostgreSQL 14–18 matrix jobs without
  changing the established 20 check names.
- Updated repository/package inventory and durable site, API, configuration,
  role, operations, migration, and status documentation.

## Files changed

- `.github/workflows/ci.yml`
- `README.md`
- `docs/API.md`, `docs/CONFIGURATION.md`, `docs/DATABASE_ROLES.md`,
  `docs/OPERATIONS.md`, `docs/SITES.md`
- `migrations/alembic/README.md`
- `oap/active`, `oap/orders/011-a-site-domain-context-foundation.md`
- `services/backend/src/slaif_agent_site/control_api/database.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/013_001_site_foundation.py`
- `services/backend/src/slaif_agent_site/sites/__init__.py`, `models.py`,
  `normalization.py`, `service.py`
- `services/backend/tests/unit/test_site_unit.py`,
  `test_control_database.py`, `test_foundation_contract.py`
- `services/backend/tests/integration/test_sites.py`,
  `test_database_bootstrap.py`, `test_control_database_integration.py`
- `tests/repository/test_repository_policy.py`, `tools/check_repository.py`

## Acceptance-criteria evidence

### Criterion 1 — deterministic persistence and privilege boundary

- PASSED. Clean migration, repeat, downgrade, rebuild, strict relation/function
  inventory, ownership, grants, readiness, and setup constraints passed on
  disposable PostgreSQL 16 locally and PostgreSQL 14–18 in GitHub.
- Only `slaif_owner` has relation access. `slaif_control` has the exact nine
  new function signatures; agent, editor, readers, reviewer, scheduler, media,
  and GC lack relation/function authority.

### Criterion 2 — one normalization contract

- PASSED. Seventy-two focused unit/integration tests cover site-key and locale
  equivalence; Unicode/IDNA/case/trailing-dot hosts; port separation; IP,
  wildcard, malformed, and overlong denial; dot/encoded/backslash/repeated
  path denial; root/prefix boundaries; and platform/local namespace denial.

### Criterion 3 — trusted immutable resolver result

- PASSED. Public `SiteContext()` construction raises. Trusted host/path inputs
  resolve only active persisted sites by unique longest prefix; local routing
  derives the key only from `localhost /s/<key>`. The `/s` namespace cannot
  fall through to a normal domain mapping. Resolution conveys no authorization.

### Criterion 4 — cross-site/quota/archive/cancellation negatives

- PASSED. Actual-Control tests prove atomic concurrent quota failure, two-site
  host/prefix/local isolation, cross-site domain-ID substitution denial,
  primary removal refusal, archive without deletion, server-owned revisions,
  and cancellation/constraint rollback without partial site/domain state.

### Criterion 5 — bounded scope and unchanged existing behavior

- PASSED. Existing bootstrap, installation setup, local identity,
  authentication, session, Control database, and Control HTTP integration all
  passed together with the new site suite. No web, edge, Compose topology,
  dependency/lock, membership, content/COW, RLS, deletion, or auth semantics
  changed.

### Criterion 6 — one PR and complete CI

- PASSED. Exactly PR #23 was created from the required main SHA. Its
  implementation head passed 20/20 checks in one initial generation with no
  workflow rerun or corrective code generation.

## Local verification

- `uv lock --check`; `uv sync --frozen --all-groups`: PASSED — frozen
  environment unchanged.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository
  tools`: PASSED — 106 files.
- `uv run --frozen mypy`: PASSED — 95 source files.
- `python -m compileall -q tools tests/repository services/backend/src
  services/backend/tests`: PASSED.
- `uv run --frozen pytest -q services/backend/tests/unit tests/repository
  tests/packaging`: PASSED — 348 tests and 56 subtests.
- Combined PostgreSQL 16 run of `test_database_bootstrap.py`,
  `test_installation_setup.py`, `test_local_identity.py`,
  `test_local_authentication.py`, `test_human_session.py`,
  `test_control_auth_http_integration.py`,
  `test_control_database_integration.py`, and `test_sites.py`: PASSED — 50
  tests.
- Final focused `test_site_unit.py` plus PostgreSQL `test_sites.py`: PASSED —
  72 tests.
- `python tools/check_repository.py`: PASSED.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-011a`: PASSED —
  source and wheel distributions.
- Node 24.14.1 / pnpm 11.22.0: frozen install, lint, format check, typecheck,
  test, build, and license JSON inspection all PASSED.
- Changed-document/order Markdownlint 0.23.2 with `--no-globs`: PASSED — zero
  findings across eight files. The exact final report was separately linted
  before publication.
- `git diff --check`, conflict-marker scan, exact branch/base/order/pointer
  hashes, and clean post-implementation status: PASSED.
- `python tools/check_mermaid.py`: FAILED locally — Mermaid CLI 11.16.0
  returned the same opaque `[object Object]` browser error for all 12 existing
  diagrams, including 11 untouched architecture diagrams. Cached Chrome 131
  and 152 binaries launched independently; explicit executable selection did
  not change the result. GitHub's independent Mermaid check PASSED on the exact
  implementation head. No source weakening or unchanged CI rerun was used.
- Local Playwright/browser, Compose, and broad supply-chain/image runs: NOT RUN
  as the work order explicitly prohibited local browser and broad image work
  and required Compose only for migration-readiness diagnosis. GitHub's
  authoritative existing Compose and supply-chain jobs both PASSED.

## GitHub CI / required checks

- Initial CI run: `32431140901`; initial CodeQL run: `32431140933`.
- SUCCESS: Repository policy; Dependency review; Mermaid; Markdown; Node
  contracts; Python 3.12, 3.13, and 3.14 quality/package; Foundation PostgreSQL
  14, 15, 16, 17, and 18; Compose and edge packaging; Supply-chain evidence;
  Detect supported languages; Analyze actions; Analyze python; Analyze
  javascript-typescript; CodeQL aggregate.
- Implementation-head state: 20 successful; zero failed, cancelled, skipped,
  pending, or missing.
- All required green at drafting: yes.
- Corrective code generations: zero. Workflow reruns: zero.
- The report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Used the existing disposable local PostgreSQL fixture service and fake
  credentials. No passwordless-sudo package installation was needed.
- No dependency or lockfile changed. Transient exact Mermaid and Markdown CLI
  packages used the established preparation tooling and added no production
  dependency or repository output.

## Documentation

- Added `docs/SITES.md` and updated API, configuration, database-role,
  operations, migration, and README truth. Documentation covers schema,
  normalization, trusted resolver, `/s/<key>`, quota, archive/no-delete,
  least privilege, institutional-tenancy limits, and every deferred surface.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no; production systems/data accessed: no.
- Required tests skipped/not run: no. Work-order-prohibited local browser and
  broad image checks were not required local tests; GitHub ran their existing
  authoritative jobs successfully.
- Scope deviation: no. The permitted equivalent focused unit name
  `test_site_unit.py` avoids a strict-mypy duplicate-module collision while
  retaining required integration filename `test_sites.py` in every matrix job.
- Extra objective PR: NO. Coding-agent merge: NO. Auto-merge: NO.
- Activated order/active edited: NO; both were committed byte-identically.
- Report commit changes only this report: yes.
- Secrets/capabilities printed, logged, or committed: no.

## Immutable hashes

- `AGENTS.md`:
  `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`:
  `00bdd82fcec0afaf65d2fbc2a2f9fa43a7d4e9e254d7a262bea0c5bae3be6b8a`
- `ARCHITECTURE-for-agents.md`:
  `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Activated work order:
  `42a7e62350f5ffae09392fac9a00aed65c0b6f39cce97ef390cf3b8d1a813545`
- Activated pointer:
  `cf73a0a8cbaacf788dc456c5a35e41f6dc0518bfd1eac86930b14f13ec6f2581`

## Known limitations / blockers

- Site management has no HTTP route or UI. Membership/RBAC, workspaces,
  content/COW data, public/admin resolver routes, demo seeding, edge multi-site
  proof, DNS automation, redirects, hostile-tenancy claims, and deletion remain
  unimplemented by design.
- The local Mermaid renderer limitation is fully disclosed above and did not
  reproduce in authoritative GitHub CI.
- Blockers: none. Acceptance and merge remain exclusively strategic-model
  authority.

## Recommended strategic follow-up

Independently review PR #23 and this report. Strategy alone decides whether to
activate a bounded 011-b continuation on the same branch/PR.
