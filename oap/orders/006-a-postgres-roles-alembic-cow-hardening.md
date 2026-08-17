# OAP Work Order — 006-a

## Objective

Create exactly one new GitHub pull request that makes the PostgreSQL authority
boundary executable before product-domain development: establish deterministic
Alembic/bootstrap infrastructure, the product schemas and exact database-role
inventory, public-API-only `agent-cow-postgresql` deployment/enablement/
hardening, an independently verified privilege matrix, and a durable bootstrap
health marker.

This is a database platform and least-privilege slice. It must not add users,
sites, workspaces, capabilities, content-domain tables, online product routes,
publication behavior, or a deployable Compose stack.

## GitHub objective state

- Numeric objective: `006`
- Execution round: `006-a`
- PR mode: `CREATE_NEW_PR`
- Existing objective PR: N/A
- Required head branch: `oap/006-postgres-cow-bootstrap`
- Base branch: `main`
- Required PR title: `[OAP 006] Add PostgreSQL role and COW bootstrap baseline`
- Required PR readiness: non-draft (`draft: false`)
- Repository: `ulfe-lmi/slaif-agent-site`

## Strategic context

Objective `005` is accepted and merged. The repository has ten separately
startable backend process skeletons and conceptual authority descriptors, but
those descriptors are not database grants and no application migration,
product schema, role manifest, database configuration, bootstrap action, or
privilege marker exists. Architecture Sections 16.1, 16.3, 16.5, 16.11,
42.1–42.3, and Phase 1 require executable authority separation before a
product route or table can accidentally acquire the wrong privilege class.

The generic COW foundation remains `agent-cow-postgresql==0.2.0` from PyPI.
Use only the public surface centralized in
`slaif_agent_site.agent_state.foundation`; product runtime code must not query
or depend on undocumented foundation tables, functions, or SQL internals.

At strategic activation time, the current non-yanked PyPI releases selected
for the migration implementation are:

```text
alembic==1.19.1       MIT, Python >=3.10
sqlalchemy==2.0.52    MIT, Python >=3.7
```

Use SQLAlchemy only as the required Alembic migration substrate. Asyncpg
remains the application/database driver. Do not add psycopg, an ORM model
layer, a second pool implementation, or a cloud database SDK. Reverify the
selected releases, Python support, sources, hashes, dependency closure, and
licenses at execution time; report a material discrepancy rather than silently
selecting different versions.

## Current verified state

- Remote `main` SHA:
  `7db8f69134b2cbc482711f57f840989c2b6c0168`
- Objective `005` PR `#8` is merged; its report-containing head is present in
  remote `main` and the complete OAP transcript is versioned.
- `oap/active` currently names the merged identifier `005-a`; this activation
  changes it to `006-a`.
- PR `#7` is an unrelated open Dependabot TypeScript-major proposal. PR `#5`
  was closed without merge externally. Do not modify, comment on, close,
  reopen, merge, reuse, or otherwise act on either PR.
- The Python runtime is frozen to Python 3.12–3.14 and uv 0.12.5, with
  asyncpg 0.31.0 and the foundation 0.2.0 already direct runtime dependencies.
- Existing CI runs Python quality/package tests on 3.12–3.14 and the
  downstream foundation integration suite on PostgreSQL 14–18.
- `services/backend/tests/conftest.py` currently provisions disposable
  qualification setup/runtime/reviewer roles and one temporary COW table; it
  is evidence for the generic foundation only, not the Agent-Site role model.
- The production baseline has no `alembic.ini`, migration tree, `db` package,
  product schemas, product role provisioning, bootstrap database command,
  database locator, or database health marker.

## Allowed path scope

Keep the PR bounded to the following paths/families plus the required OAP
order, active pointer, and report:

```text
.github/workflows/ci.yml
AGENTS.md
CONTRIBUTING.md
README.md
alembic.ini
docs/CONFIGURATION.md
docs/DATABASE_BOOTSTRAP.md
docs/DATABASE_ROLES.md
docs/FOUNDATION_INTEGRATION.md
docs/SERVICE_AUTHORITY.md
migrations/alembic/**
migrations/bootstrap/**
oap/active
oap/orders/006-a-postgres-roles-alembic-cow-hardening.md
oap/reports/006-a-postgres-roles-alembic-cow-hardening.md
pyproject.toml
services/backend/src/slaif_agent_site/agent_state/foundation.py
services/backend/src/slaif_agent_site/authority.py
services/backend/src/slaif_agent_site/bootstrap/**
services/backend/src/slaif_agent_site/config.py
services/backend/src/slaif_agent_site/db/**
services/backend/tests/conftest.py
services/backend/tests/integration/**
services/backend/tests/unit/test_authority.py
services/backend/tests/unit/test_config.py
services/backend/tests/unit/test_foundation_contract.py
services/backend/tests/unit/test_process_entrypoints.py
tests/repository/test_repository_policy.py
tools/check_repository.py
uv.lock
```

Do not touch `ARCHITECTURE.md`, `SECURITY.md`, `NOTICE`, either OAP protocol,
Node/TypeScript packages or locks, existing HTTP app/health/error/logging/
correlation modules, Compose/container/edge files, or unrelated prior OAP
artifacts. If a genuinely necessary path is absent from this allowlist, stop
and report the reason rather than expanding scope silently.

## Scope and requirements

### A. Exact migration dependency boundary

- Add exact `alembic==1.19.1` and `sqlalchemy==2.0.52` production/bootstrap
  requirements and regenerate `uv.lock` with PyPI registry artifacts and
  hashes using exact uv 0.12.5.
- Preserve all existing exact runtime pins and groups. Do not add a driver
  other than the existing asyncpg, a SQLAlchemy ORM/product repository layer,
  an Alembic cloud integration, or a VCS/direct/local/editable dependency.
- The application service code continues to use asyncpg; SQLAlchemy is
  confined to deterministic Alembic execution and metadata-free migration
  operations in this objective.
- Extend package, repository-policy, frozen-install, license, and wheel/sdist
  expectations honestly for the new migration/bootstrap modules and files.

### B. Product schema and migration baseline

Create a conventional, reviewable Alembic environment with no secret or URL
embedded in `alembic.ini`. Connection configuration is injected by trusted
bootstrap code; import and offline inspection have no network or database side
effect.

The baseline migration must create exactly these product schema boundaries,
owned by the setup owner role:

```text
control
content
audit
```

The foundation deploys its own `agentcow` schema through its public API.
Place Alembic version state in an explicitly selected owner-only location, not
in a COW-enabled table. Revoke unsafe default `PUBLIC` schema/function
authority, including `CREATE` on the default public schema where supported by
the target database policy. Use fully qualified names and deterministic,
quoted identifiers rather than a mutable search path.

The only product table permitted in the clean baseline is a minimal
owner-controlled bootstrap/readiness marker under `control`, plus Alembic's
version table. The marker records at least the migration revision, qualified
foundation distribution/version, successful COW deployment/hardening/
privilege-validation state, and update time without storing a credential or
raw DSN. `content` and `audit` remain free of domain tables in a clean
production baseline.

Provide deterministic upgrade-to-head, repeat-upgrade/no-op, current-revision,
and validation behavior. A downgrade/rebuild path must be exercised only in a
disposable database and documented as development/release verification, not as
a production rollback promise. Do not invent product data migrations.

### C. Exact database authority inventory

Define one source-controlled role/privilege manifest aligned with the process
descriptors and Architecture Section 16.3:

```text
slaif_owner
slaif_control
slaif_editor_runtime
slaif_agent_runtime
slaif_public_reader
slaif_preview_reader
slaif_reviewer
slaif_scheduler
slaif_media
slaif_gc
```

MCP, Web, and browser worker have no database role. Keep role identifiers
separate from passwords/DSNs. Every product role must be non-superuser,
non-createdb, non-createrole, non-replication, and non-bypass-RLS, with no
membership path that combines setup, reviewer, agent-facing, or unrelated
authority. Do not create a generic all-authority role.

Role creation/reconciliation requires database-cluster provisioning authority
that is stronger than ordinary migrations. Model this as an explicit one-shot
operator/bootstrap boundary, never a long-running service capability. It must
be possible for an institution/DBA to pre-provision roles and then run the
owner-only migration/COW step. Do not ship a default password or assume that
the application owner can grant itself `CREATEROLE`.

Whether production credentials use direct login roles or separate login
principals over non-login privilege roles must be documented and tested. The
selected design must keep every service credential separate, prevent a
long-running process from receiving cluster-provisioner or owner credentials,
and support fake disposable test principals. Compose secret creation and
distribution remain objective `007`, not this PR.

### D. Bootstrap and COW reconciliation

Replace the bootstrap's non-mutating placeholder with an explicit one-shot
database bootstrap interface. Preserve:

```text
python -m slaif_agent_site.bootstrap --check
```

as a no-network, no-database, no-mutation configuration/authority smoke. Any
mutating operation must require an explicit subcommand/flag and complete as a
one-shot; starting bootstrap with ambiguous/default arguments must not silently
modify a database.

The trusted bootstrap sequence is:

1. verify/provision the role boundary through the explicitly stronger
   one-shot operator path, or validate that a DBA already provisioned it;
2. run Alembic to the requested head under setup-owner authority;
3. call `deploy_cow_functions(...)` through the qualified public adapter;
4. call `enable_cow_schema(...)` for `content` with
   `allow_deferred_fks=True` and
   `allow_unsafe_canonical_writes=False`;
5. call `harden_cow_schema(...)` with only editor/agent runtime roles and the
   reviewer role in their correct arguments;
6. apply the product-owned narrow grants/revokes for control, public/preview
   readers, scheduler, media, GC, and future audit functions without granting
   capabilities for objects that do not yet exist;
7. call `validate_cow_schema_privileges(...)` and an independent
   product-role verifier;
8. mark the bootstrap/readiness record safe only after every required check
   succeeds.

Steps that change schema/hardening state must use explicit transactions where
the public foundation contract requires them. A failure must roll back its
transaction, must not leave a truthful-looking safe marker, and must be
idempotently repairable. Re-running a successful bootstrap must not duplicate
objects, widen privileges, or change the migration head.

Do not use private foundation object names in application/runtime logic. A
qualification-only test may create and inspect a temporary representative COW
table and its documented generated relations to prove negative privileges;
that table must never ship in the clean migration baseline.

### E. Database configuration and secret boundary

Add typed, secret-safe configuration only to the one-shot database/bootstrap
path. It must support mounted absolute secret-file references and fake
disposable test inputs, validate the expected mode/role/database target, and
fail with a constant safe public/CLI error. No exception, repr, log, report,
test output, migration config, or marker may expose a password or raw DSN.

Do not add a shared `SLAIF_DATABASE_URL` consumed by every process. Cluster
provisioning/setup-owner inputs must not be fields loaded by Control, Editor,
Agent, Render, MCP, Media, Review, Scheduler, or GC startup. No long-running
process may import the provisioner/owner connection factory, and no pool is
created at module import. Service-specific runtime pools and readiness wiring
remain later objectives.

Use only fake local PostgreSQL credentials in tests. No production or external
database may be accessed.

### F. Independent privilege verification

Implement a product-owned verifier that reasons from PostgreSQL's effective
privileges, role membership, ownership, function execution, schema authority,
and relation DML. It supplements rather than replaces the foundation's
`validate_cow_schema_privileges` result.

Against a disposable representative COW table, prove at minimum:

- `PUBLIC` and every non-owner role lack schema `CREATE`, setup-owner
  ownership, and ungranted function authority;
- Agent and Editor runtime roles can operate COW views only inside a trusted
  foundation session transaction and fail closed without session context;
- Agent and Editor cannot read/write generated base/change relations, invoke
  reviewer commit/discard, deploy/enable/harden COW, or use owner authority;
- Agent and Editor remain distinct roles with no inheritance path between
  them;
- Reviewer can use only the controlled reviewer surface and cannot perform
  runtime view DML, schema setup, or arbitrary control-table updates;
- Control cannot mutate content;
- public reader is canonical read-only and preview reader is read-only; neither
  can mutate canonical, COW, control, or audit state;
- scheduler, media, and GC lack content DML and reviewer/setup authority;
- MCP, Web, and browser worker have no database credential/role entry;
- a cancelled runtime/reviewer transaction rolls back and pooled context is
  clean for the next borrower;
- repeated hardening remains safe and detects deliberate inherited or direct
  over-grants.

Privilege failure output must name the role/object/privilege category needed
for repair without printing a credential, DSN, or unrelated database metadata.

### G. Tests and CI

Keep the generic foundation qualification evidence and add separate
Agent-Site database-bootstrap tests. Do not quietly replace the four existing
foundation integration tests with product tests.

Required new test classes include:

- clean baseline migrate/current/repeat/downgrade/rebuild;
- role manifest flags, identities, ownership, and membership graph;
- bootstrap sequencing, marker truthfulness, failure rollback, and
  idempotence;
- representative-table enable/harden and the full positive/negative effective
  privilege matrix;
- missing context, cross-role setup/reviewer denial, direct over-grant and
  inherited over-grant detection;
- asyncpg cancellation, transaction ownership, connection release, and pool
  context cleanup;
- secret-file/constant-error/redaction and no-import-side-effect behavior;
- no migration URL, default password, private foundation import, product
  domain table, or long-running owner/provisioner configuration;
- exact package/repository/migration artifact boundaries.

Extend the PostgreSQL 14–18 CI matrix to run both the existing foundation suite
and the new database-bootstrap/privilege suite. Keep Python 3.12–3.14 quality,
package, repository, Node, Markdown, Mermaid, dependency review, and
three-language CodeQL gates green. No integration test may skip because Docker
or administrative setup was inconvenient; the coding VM has passwordless
`sudo` and disposable local PostgreSQL is the executor's responsibility.

### H. Durable documentation

Add `docs/DATABASE_BOOTSTRAP.md` and `docs/DATABASE_ROLES.md`. Document:

- exact roles, role attributes, ownership, memberships, schema/object grants,
  and denied combinations;
- the cluster-provisioner versus setup-owner versus long-running service
  boundary;
- migration revision/location and COW reconcile/harden/validate order;
- explicit commands for no-op check, provision/upgrade/validate/current status,
  and disposable downgrade/rebuild verification;
- secret-file requirements and absence of default credentials;
- marker/readiness semantics, idempotence, partial-failure recovery, and
  known deferred behavior;
- how future migrations must enable/harden newly added `content` tables and
  explicitly grant every new table/function rather than relying on broad
  defaults.

Update configuration, service-authority, foundation, README, AGENTS, and
CONTRIBUTING material only where necessary to describe implemented behavior
and exact verification. Continue to state that no product schema/domain route,
online pool, authentication, deployment stack, or runnable product exists.

## Explicit non-goals

- No installation-state/user/site/domain/locale/membership/role-assignment/
  workspace/capability/idempotency/job/browser/media/content-model/content-item/
  page/composition/navigation/theme/audit-event or other product-domain table.
- No human or agent product route, authentication, session/cookie/CSRF, OIDC,
  semantic service, MCP tool, media byte store, browser worker, Puck/Web UI,
  review/promotion job, cache, metrics, or external side effect.
- No long-running service database connection or health probe, shared
  connection locator, ORM repository, raw SQL endpoint, RLS claim, Compose,
  Dockerfile, NGINX, Apache, `.env`, default password, hosted database, cloud
  SDK, or production deployment.
- No automatic physical migration based on site/agent input and no migration
  authority in an Agent/Editor process.
- No GitHub setting, release, tag, deployment, issue, auto-merge, or action on
  PR `#5`/`#7`.

## Acceptance criteria

1. Exactly one non-draft objective `006` PR exists with the required branch,
   title, base, and versioned OAP transcript; no second objective PR or merge.
2. Alembic/SQLAlchemy and every existing Python dependency resolve at exact
   approved versions from PyPI with locked hashes; no second driver, ORM
   product layer, VCS/local source, hosted SDK, or unapproved license appears.
3. A clean disposable PostgreSQL 14–18 database deterministically reaches one
   documented Alembic head containing only the three product schemas,
   owner-only migration/bootstrap metadata, and public foundation objects; a
   repeat run is a no-op and a disposable downgrade/rebuild is proven.
4. The exact role inventory and membership/attribute manifest exists; no role
   combines setup, reviewer, agent/editor, control, reader, scheduler, media,
   or GC authority and no long-running process receives provisioner/owner
   configuration.
5. Bootstrap uses only public `agentcow.postgres` APIs, disables unsafe
   canonical writes, enables deferred-FK support, applies hardening in explicit
   transactions, is idempotent, and writes a safe marker only after foundation
   plus independent privilege validation succeeds.
6. The foundation verifier and independent PostgreSQL truth-table tests prove
   every required allow/deny edge on a disposable representative COW table,
   including missing context, base/change/reviewer/setup denial, read-only
   readers, no control content DML, and deliberate over-grant detection.
7. Cancellation/failure tests prove rollback, connection release/context
   cleanup, no partial truthful marker, and safe retry.
8. `bootstrap --check` remains no-network/no-mutation; mutating bootstrap
   behavior is explicit, one-shot, secret-file capable, constant-error safe,
   and never prints or serializes a password/raw DSN.
9. The clean production migration contains no product-domain table and no
   unexpected schema/object/grant; current application HTTP/worker boundaries
   remain unchanged except bootstrap's explicit one-shot implementation.
10. Existing foundation, Python, Node, repository, documentation, Mermaid,
    dependency-review, PostgreSQL 14–18, and CodeQL gates remain green, with
    the new database suite green rather than skipped.
11. Durable documentation matches exact implemented role/migration/bootstrap
    behavior and does not overclaim a deployable product or production-ready
    database topology.
12. `oap/active` is `006-a`, order/report correlation is unique, prior OAP
    artifacts are unchanged, and the final remote head is the report-only
    `SELF` commit whose first parent is the literal implementation head.

## Verification required

Run and report exact outcomes for at least:

```bash
uv --version
uv lock --check
uv sync --frozen --all-groups
uv run --frozen ruff check services/backend tests/repository tools migrations
uv run --frozen ruff format --check services/backend tests/repository tools migrations
uv run --frozen mypy
uv run --frozen pytest services/backend/tests/unit tests/repository
uv run --frozen pytest services/backend/tests/integration
uv build --out-dir /tmp/slaif-agent-site-distributions
python tools/check_repository.py
python tools/check_mermaid.py
pnpm install --frozen-lockfile
pnpm check
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
git diff --check origin/main...HEAD
git diff --name-only origin/main...HEAD
```

Also run and report:

- exact Alembic current/head/history and clean upgrade/repeat/downgrade/rebuild
  evidence on a disposable PostgreSQL database;
- independent PostgreSQL object owner, schema ACL, role attribute/membership,
  relation/function privilege, and unexpected-object inventories;
- representative COW session/read/reviewer paths plus every negative privilege
  edge and deliberate-overgrant detection;
- failure injection before marker publication and after a transactional
  hardening change, followed by safe retry;
- exact PostgreSQL 14–18 results locally where practical and in GitHub CI;
- clean production-only wheel install/import plus artifact inventory;
- dependency source/hash/license inventory and absence of psycopg/cloud/VCS/
  local sources;
- focused secret/default-password/DSN/private-foundation/DDL/role scan;
- protected-file and prior-OAP hashes, exact PR identity/body, final checks,
  CodeQL alerts, report commit parent/delta, and clean synchronized worktree.

A foundation test, migration check, or role assertion that is skipped/not run
is not passing evidence. Site/auth/content/API/Compose behavior is explicitly
`NOT IMPLEMENTED/NOT RUN`, not a success claim.

## Safety and security constraints

- Use only disposable local PostgreSQL instances and fake generated test
  credentials. Never access a production/external database or print a test
  credential into the report.
- Treat cluster-provisioner and setup-owner access as separate one-shot
  authority. No long-running process may import or load either credential.
- Fail closed on unknown role, migration, foundation, schema, marker, or
  privilege state. Never repair a failure by granting broader authority or by
  enabling unsafe canonical writes.
- Never modify foundation source/private objects, weaken current tests, or
  encode a default password/DSN.

## Local execution capability

Routine Alembic/Python/PostgreSQL/container installation, service startup,
role provisioning, database recreation, test diagnosis, and CI-log inspection
belong to the coding agent in its disposable VM. Passwordless `sudo` is
available. Do not transfer ordinary setup to the human or strategic model.

## GitHub workflow

Create `oap/006-postgres-cow-bootstrap` from current remote `main`. Preserve
the activated order/pointer bytes, implement only the bounded database
platform slice, run all required checks, push, and create exactly one non-draft
PR with the required title. Repair in-scope local/CI/CodeQL failures on that
same PR when safe. Never touch PR `#5` or `#7`, create another PR, merge,
enable auto-merge, or choose objective `007`.

## Required report

Atomically publish exactly:

```text
oap/reports/006-a-postgres-roles-alembic-cow-hardening.md
```

Use the complete protocol 1.2 report format. Include exact dependency/source/
license/hash evidence; Alembic head/history/object inventory; role attributes,
memberships, grants, and denied matrix; bootstrap sequence/commands/marker/
idempotence/failure-retry evidence; foundation public API and configuration
boundary; every local and GitHub test/check; no-skips and no-secret evidence;
deferred features; exact diff scope; unrelated-PR and no-merge confirmations.
Publish the final report-only `SELF` commit and verify its parent/path/remote
head before sending FIFO `OK`.
