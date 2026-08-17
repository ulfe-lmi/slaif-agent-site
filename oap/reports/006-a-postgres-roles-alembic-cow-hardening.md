# OAP Coding-Agent Report — 006-a

## Work order

- Identifier: 006-a
- Work-order file: `oap/orders/006-a-postgres-roles-alembic-cow-hardening.md`
- Numeric objective: 006
- PR mode: CREATED_NEW_PR
- Report drafted: 2026-08-17T13:29:44Z

## Status

PARTIAL

## Executive summary

Implemented and pushed the bounded PostgreSQL platform slice: exact non-login
privilege roles, separate provisioner and setup-owner boundaries, one packaged
Alembic head, the three product schema boundaries, an owner-only readiness
marker, public-foundation-only COW reconciliation, independent effective
privilege verification, secret-safe one-shot commands, durable documentation,
and separate PostgreSQL 14–18 CI coverage.

The representative-table path is fully green, including COW runtime/reviewer
behavior, every required deny edge, rollback/retry, combined-role and direct or
inherited over-grant detection, cancellation, and pool cleanup. The clean
production baseline deliberately remains unsafe: `agent-cow-postgresql==0.2.0`
raises `ValueError` when `harden_cow_schema(...)` receives an empty schema, while
this order forbids adding a production content table. The implementation
persists truthful deployment state, leaves hardening/validation/safe false,
emits only the constant CLI failure, and documents the strategic decision
needed. It does not fabricate a placeholder table or weaken the boundary.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: 9
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/9>
- PR state at report time: OPEN
- PR readiness at report time: non-draft
- PR merge state at report time: CLEAN and MERGEABLE
- Base branch: `main`
- Head branch: `oap/006-postgres-cow-bootstrap`
- Starting remote SHA: `7db8f69134b2cbc482711f57f840989c2b6c0168`
- Implementation head SHA: `65f8430be15780d3e7abcf804bd92ce1bb0f5c5e`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal SHA derived from GitHub)
- Implementation commits pushed before the report commit:
  `65f8430be15780d3e7abcf804bd92ce1bb0f5c5e` —
  `OAP 006: add PostgreSQL COW bootstrap baseline`
- Report commit first parent: same as Implementation head SHA
- Created a new PR this turn: yes
- Amended existing PR this turn: no
- Other objective-006 PRs found: none
- Merge performed: NO
- Auto-merge enabled: NO
- PRs #5 and #7 modified: NO

## Changes made

- Added exact `alembic==1.19.1` and `sqlalchemy==2.0.52` runtime/bootstrap
  dependencies and regenerated the uv 0.12.5 registry-only lock with hashes.
- Added a metadata-free, injected-connection Alembic environment with one head,
  `006_001`, packaged in the Python wheel and represented conventionally at
  repository root without a URL or credential.
- Added `control`, `content`, and `audit`, all owned by `slaif_owner`; the only
  clean product table is `control.bootstrap_readiness`, plus Alembic's version
  table. `content` and `audit` contain no domain table.
- Added the exact ten-role manifest. Every privilege role is password-free,
  `NOLOGIN`, `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, `NOINHERIT`,
  `NOREPLICATION`, and `NOBYPASSRLS`.
- Added explicit one-shot `provision`, `upgrade`, `bootstrap`, `validate`,
  `current`, confirmed-disposable `downgrade`, and confirmed-disposable
  `rebuild` commands while preserving mutation-free `--check`.
- Added separate production secret-file locators for provisioner and owner,
  exact database/authority validation, no defaults, masking, and constant CLI
  failure output.
- Added public `agentcow.postgres` deployment, enablement, hardening, and
  validation calls with deferred FKs enabled and unsafe canonical writes
  disabled. No private foundation module or object name is used in product
  logic.
- Added product-owned grant reconciliation and a PostgreSQL-truth verifier for
  role attributes, effective/transitive memberships, combined credentials,
  schema creation, owners, relations, sequences, functions, `PUBLIC`, and clean
  object inventory.
- Added disposable full-matrix tests and retained the four generic foundation
  tests separately. CI now executes both suites on PostgreSQL 14 through 18.
- Updated exact package/repository expectations and durable configuration,
  authority, role, bootstrap, foundation, contributor, and status docs.

## Files changed

- Workflow/governance: `.github/workflows/ci.yml`, `AGENTS.md`, `oap/active`,
  `oap/orders/006-a-postgres-roles-alembic-cow-hardening.md`.
- Packaging/migrations: `pyproject.toml`, `uv.lock`, `alembic.ini`,
  `migrations/alembic/README.md`, `migrations/alembic/__init__.py`,
  `migrations/bootstrap/README.md`.
- Backend source: `services/backend/src/slaif_agent_site/authority.py`,
  `services/backend/src/slaif_agent_site/bootstrap/__init__.py`,
  `services/backend/src/slaif_agent_site/bootstrap/__main__.py`,
  `services/backend/src/slaif_agent_site/bootstrap/config.py`,
  `services/backend/src/slaif_agent_site/bootstrap/service.py`, and every new
  file under `services/backend/src/slaif_agent_site/db/`.
- Tests/policy: `services/backend/tests/conftest.py`,
  `services/backend/tests/integration/test_database_bootstrap.py`,
  `services/backend/tests/unit/test_authority.py`,
  `services/backend/tests/unit/test_config.py`,
  `services/backend/tests/unit/test_foundation_contract.py`,
  `services/backend/tests/unit/test_process_entrypoints.py`,
  `tests/repository/test_repository_policy.py`, `tools/check_repository.py`.
- Documentation: `README.md`, `CONTRIBUTING.md`, `docs/CONFIGURATION.md`,
  `docs/DATABASE_BOOTSTRAP.md`, `docs/DATABASE_ROLES.md`,
  `docs/FOUNDATION_INTEGRATION.md`, `docs/SERVICE_AUTHORITY.md`.

## Acceptance-criteria evidence

### Criterion 1

- Result: PASSED.
- Evidence: exactly one objective-006 PR exists: open non-draft PR #9 with the
  required title, base `main`, head `oap/006-postgres-cow-bootstrap`, and
  implementation head `65f8430be15780d3e7abcf804bd92ce1bb0f5c5e`. No merge or
  second objective PR occurred.

### Criterion 2

- Result: PASSED.
- Evidence: exact direct pins are present. `uv.lock` resolves 41 packages and
  records only PyPI registry sources for foundation/Alembic/SQLAlchemy. Verified
  representative hashes are foundation wheel/source
  `c469d247...`/`eae8d434...`, Alembic wheel/source
  `b39018cb...`/`e0fca051...`, and SQLAlchemy universal-wheel/source
  `3b81b836...`/`5e2d4635...`. New closure licenses are Alembic MIT,
  SQLAlchemy MIT, Greenlet MIT AND PSF-2.0, Mako MIT, and MarkupSafe
  BSD-3-Clause. No second driver, cloud SDK, VCS, direct, local, or editable
  qualified dependency was found.

### Criterion 3

- Result: PASSED for the required database/migration baseline.
- Evidence: a clean disposable PostgreSQL 16 run produced exactly one head
  `006_001`, schemas `audit`, `content`, and `control` owned by `slaif_owner`,
  and only `control.alembic_version` and `control.bootstrap_readiness` among
  product relations. Repeat upgrade preserved marker time. Downgrade produced
  zero version rows and removed `content`/`audit`; rebuild restored `006_001`.
  Explicit reconcile deployed one `agentcow` schema with four relations and 23
  functions while leaving `content` empty and the marker truthfully unsafe.
  GitHub repeated both suites successfully on PostgreSQL 14, 15, 16, 17, and 18.

### Criterion 4

- Result: PASSED.
- Evidence: the disposable inventory found ten roles, every prohibited flag
  false, and no product-role membership edge. Every test service used a
  distinct fake login with one membership. The verifier rejects product roles
  that can set another role and non-provisioner principals that combine product
  authorities. Online process code imports no owner/provisioner locator.

### Criterion 5

- Result: PARTIAL due to the qualified foundation's empty-schema behavior.
- Evidence: the representative table passes public deploy, enable with
  `allow_deferred_fks=True` and `allow_unsafe_canonical_writes=False`, harden,
  product grants, foundation validation, independent validation, marker-last
  publication, and repeated idempotent reconciliation. On the mandated empty
  clean schema, public `harden_cow_schema(...)` rejects the state. The clean
  marker is exactly `cow_deployed=true`, `cow_hardened=false`,
  `privileges_validated=false`, `safe=false`; no truthful completion claim is
  possible without a strategic/foundation change.

### Criterion 6

- Result: PASSED against the qualification-only COW table.
- Evidence: tests prove runtime view DML only under a trusted session; no-context,
  base/change, setup, owner, reviewer, control, audit, and narrow-service access
  is denied; readers are read-only and canonical without preview context;
  reviewer promotion/discard succeeds only through its controlled surface.
  Direct base grants, inherited base grants, shared-principal combined roles,
  and foundation-relation over-grants are all detected.

### Criterion 7

- Result: PASSED.
- Evidence: injected failure after hardening and immediately before marker
  publication rolls back the transaction, retains no truthful-looking marker,
  and is followed by a safe retry and repeat. Cancelled runtime and reviewer
  transactions roll back; the next pool borrower has no open transaction or
  stale COW context.

### Criterion 8

- Result: PASSED.
- Evidence: `python -m slaif_agent_site.bootstrap --check` remains the exact
  database-free smoke. No-argument invocation exits 2 without mutation.
  Mutating commands are explicit one-shots; destructive development commands
  require `--confirm-disposable`. A real production secret-file CLI test ran
  upgrade/current and verified empty bootstrap exits 1 with exactly
  `Database bootstrap failed.` and no locator disclosure.

### Criterion 9

- Result: PASSED.
- Evidence: migration source contains one explicit product `CREATE TABLE`, the
  readiness marker. Clean object inventory contains no product-domain table.
  HTTP/worker behavior is unchanged apart from bootstrap's explicit one-shot
  implementation; no route, pool, ORM repository, RLS claim, Compose, or
  deployment behavior was added.

### Criterion 10

- Result: PASSED for implementation head.
- Evidence: all 18 GitHub status checks observed for
  `65f8430be15780d3e7abcf804bd92ce1bb0f5c5e` completed successfully, including
  Python 3.12–3.14, PostgreSQL 14–18, repository policy, Node, Markdown,
  Mermaid, dependency review, and CodeQL actions/JavaScript-TypeScript/Python.
  The repository had zero open code-scanning alerts at report drafting.

### Criterion 11

- Result: PASSED.
- Evidence: the new database bootstrap and roles records describe the exact
  commands, versions, owners, memberships, grants, denied combinations,
  marker semantics, recovery, future migration rule, and empty-schema limit.
  Status docs continue to say product routes/tables, online pools, Compose,
  authentication, and a runnable product are not implemented.

### Criterion 12

- Result: PASSED by this publication commit.
- Evidence: `oap/active` is exactly `006-a` with SHA-256
  `efb9a372058d707090e5c0fefc3f96f2a6ee894fd642642a277444ea935c7908`;
  the unique order has SHA-256
  `67cf1ab81382094795261e3a121f10f81b7bbb41e9aba10ae710a36f31fe3c5c`.
  The activated files were preserved rather than authored/edited by the coding
  agent. This report is the only path in `SELF`, whose first parent is the
  literal implementation head above.

## Local verification

- `uv --version`: PASSED — `uv 0.12.5`.
- `uv lock --check`: PASSED — resolved 41 packages.
- `uv sync --frozen --all-groups`: PASSED — checked 40 installed packages.
- `uv run --frozen ruff check services/backend tests/repository tools migrations`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools migrations`:
  PASSED — 64 files already formatted.
- `uv run --frozen mypy`: PASSED — no issues in 58 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 131 passed, none skipped.
- `PGHOST=127.0.0.1 PGPORT=5432 PGDATABASE=qualification PGUSER=postgres
  PGPASSWORD=<fake-local> uv run --frozen pytest services/backend/tests/integration`:
  PASSED — 14 passed, none skipped; four generic foundation plus ten
  Agent-Site database tests.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — wheel
  SHA-256 `19f44eafe45771f8f90583ee70892103ec73a5c170e8125509cce49ece0126f0`;
  sdist SHA-256
  `8bca873850d73773180d6870c146a161cfd4f2c99b5ca6a41464af0b0ad51123`.
- Clean temporary Python 3.12 venv plus
  `uv pip install --no-cache /tmp/slaif-agent-site-distributions/slaif_agent_site-0.0.0-py3-none-any.whl`:
  PASSED — 23 production packages installed, product/foundation/Alembic/
  SQLAlchemy imports reported versions `0.0.0`/`0.2.0`/`1.19.1`/`2.0.52`,
  packaged head was `006_001`, and inventory contained exactly 48 package files.
- `uv run --frozen alembic -c alembic.ini heads`: PASSED — `006_001 (head)`.
- `uv run --frozen alembic -c alembic.ini history --verbose`: PASSED — one
  revision, parent `<base>`.
- `PGHOST=unreachable.invalid PGPORT=1 PGDATABASE=must_not_connect uv run
  --frozen alembic -c alembic.ini upgrade head --sql`: PASSED without network —
  69 deterministic SQL lines, SHA-256
  `24147d9aa0986d847542c669ec23f884b670628c1d6508ba323e2a47b287b336`.
- Disposable lifecycle/object/ACL evidence program using the same production
  APIs: PASSED — exact head/owners/relations/flags/edges/no-op/downgrade/rebuild
  outputs are recorded under Criteria 3–5; all generated database, logins, and
  roles were removed afterward.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — Mermaid CLI 11.16.0 rendered 12
  diagrams in two files while scanning 36 Markdown files.
- `pnpm install --frozen-lockfile`: PASSED — pnpm 11.22.0, eight workspace
  projects, already up to date.
- `pnpm check`: PASSED — ESLint, Prettier, TypeScript build/typecheck, two Vitest
  tests, and final builds passed on Node 24.14.1.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED before report — 37
  files, zero issues. Generated `.venv` and `node_modules` directories were
  moved aside and restored so only repository Markdown was evaluated.
- `git diff --check origin/main...HEAD`: PASSED at implementation head.
- `git diff --name-only origin/main...HEAD`: PASSED — exactly the 39 intended
  implementation/order/active paths listed above.
- Focused second-driver/cloud SDK, private-foundation-import, product-domain-DDL,
  source/hash/license, locator, password, and DSN boundary scans: PASSED after
  manual review of the expected bootstrap-only locator files.
- Protected hashes: `ARCHITECTURE.md`
  `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`,
  `SECURITY.md`
  `ec327af34d13406b560f75834d8bbda685f81dad17fd400cce0c5b6b8df4e23c`,
  and `OAP-COMMUNICATION-coding-agent.md`
  `e6150d6efb5a64e7f8af29b00514776972d4f98a0632281ddc260110c6374604`
  are unchanged. `AGENTS.md` was updated only as explicitly required by the
  work order; final SHA-256 is
  `165230bd2798ecbbc84e941d1988e48026c06bb7445940b5202a84e3ddcee8b1`.

Product site/auth/content/API/Compose behavior is explicitly NOT IMPLEMENTED
and NOT RUN; it was not claimed as verification evidence.

## GitHub CI / required checks

- Check state observed for implementation head:
  `65f8430be15780d3e7abcf804bd92ce1bb0f5c5e`.
- Repository policy: SUCCESS.
- Node contracts: SUCCESS.
- Python 3.12 quality and package: SUCCESS.
- Python 3.13 quality and package: SUCCESS.
- Python 3.14 quality and package: SUCCESS.
- Foundation PostgreSQL 14: SUCCESS.
- Foundation PostgreSQL 15: SUCCESS.
- Foundation PostgreSQL 16: SUCCESS.
- Foundation PostgreSQL 17: SUCCESS.
- Foundation PostgreSQL 18: SUCCESS.
- Markdown: SUCCESS.
- Mermaid: SUCCESS.
- Dependency review: SUCCESS.
- CodeQL Detect supported languages: SUCCESS.
- CodeQL Analyze (actions): SUCCESS.
- CodeQL Analyze (javascript-typescript): SUCCESS.
- CodeQL Analyze (python): SUCCESS.
- CodeQL aggregate: SUCCESS.
- Open CodeQL/code-scanning alerts at report drafting: 0.
- Reviews and inline review comments at report drafting: none.
- All required checks green for the implementation head at report drafting: yes.
- Report-only commit may trigger fresh checks: strategic model must verify the
  `SELF` commit without rewriting this report.

## Local setup / dependencies

- Packages/tools/services installed or configured: uv 0.12.5 environment,
  Node 24.14.1/pnpm 11.22.0 workspace, transient markdownlint 0.23.2 and Mermaid
  CLI 11.16.0, local PostgreSQL 16.14, built distributions, and one isolated
  clean-wheel audit venv under `/tmp`.
- `sudo`-level setup performed: local PostgreSQL 16 was available/running and
  configured with a fake local administrator input and disposable
  `qualification` database for this execution; no external database was used.
- Durable setup changes committed/documented: dependency pins/lock, migration
  environment, database bootstrap/roles implementation, CI matrix, and docs.
  No local credential or generated build artifact was committed.

## Documentation

Added `docs/DATABASE_BOOTSTRAP.md` and `docs/DATABASE_ROLES.md`; updated README,
CONTRIBUTING, configuration, foundation, service-authority, and the explicitly
authorized AGENTS implementation note. Documentation states exact implemented
behavior and the empty-schema limitation without claiming an online database,
product domain, authentication, deployment stack, or runnable product.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no.
- Production systems accessed: no.
- External/production database accessed: no.
- Required tests skipped/not run: no. PostgreSQL 14/15/17/18 ran in GitHub CI;
  PostgreSQL 16 additionally ran locally.
- Scope deviation: no. The unresolved foundation behavior is reported rather
  than worked around outside scope.
- Secret/default credential committed or printed in this report: no.
- Private foundation API or undocumented object used by product logic: no.
- Product-domain table, route, pool, ORM repository, Compose, hosted service, or
  production deployment added: no.
- Prior OAP artifacts changed: no; the OAP diff before this report contained
  only the externally supplied active pointer and new 006-a order.
- Extra PR created for same numeric objective: NO.
- PR merged by coding agent: NO.
- Auto-merge enabled by coding agent: NO.
- Activated order and `oap/active` edited by coding agent: NO.
- Report-publication commit changes only this report file: yes.

## Known limitations / blockers

- The qualified public foundation API cannot harden an empty COW schema. The
  clean migration must remain domain-table-free, so clean `bootstrap` exits
  nonzero after successful foundation deployment and leaves the marker unsafe.
- A strategic decision is required before clean-baseline `safe=true` is
  possible: authorize the first real content-table migration, qualify a
  foundation release/API that truthfully supports empty-schema hardening, or
  explicitly redefine empty hardening as not applicable. This round does not
  choose among those architecture options.
- Online pools, per-service production credentials, readiness wiring, product
  tables/routes, authentication, Compose, and publication behavior remain later
  objectives and were neither implemented nor claimed.

## Recommended strategic follow-up

Review the `PARTIAL` result and choose the empty-schema resolution explicitly.
Do not merge on the assumption that the clean marker is safe; its false state is
intentional evidence of the unresolved foundation/order boundary.
