# OAP Work Order — 009-a

## Objective

Create exactly one new pull request that wires the first online database
authority boundary: only the Control API receives its own file-backed
`slaif_control_login` credential, owns a bounded asyncpg pool lifecycle, and
reports database/bootstrap readiness through one narrowly granted read-only
database function.

Do not implement installation setup, users, passwords, login, sessions, CSRF,
OIDC, sites, workspaces, capabilities, or any product route. Those are split
into later objectives to keep this execution bounded.

## Hard execution budget

- Target executor duration: 45–90 minutes.
- Maximum focused database/Compose attempts: 3.
- Maximum implementation commits/check generations: 2.
- Local `tools/supply_chain/run.sh`: 0.
- Local full six-image/SBOM/Grype gate: 0.
- Local full Python and PostgreSQL matrices: 0.
- Local full clean/restart/failure Compose smoke: 0.

If the cap is reached, report `PARTIAL`; do not absorb authentication or other
adjacent scope.

## GitHub objective state

- Numeric objective: `009`
- Execution round: `009-a`
- PR mode: `CREATE_NEW_PR`
- Existing objective PR: N/A
- Required head branch: `oap/009-control-database-readiness`
- Base branch: `main`
- Required PR title: `[OAP 009] Wire Control API database readiness boundary`
- Required PR readiness: non-draft (`draft: false`)
- Repository: `ulfe-lmi/slaif-agent-site`
- Remote `main` SHA:
  `ab3db28f573b62130b93ae082a196e8ca9f8b424`

Objective `008` is merged with four immutable rounds. The supported initial
PostgreSQL baseline is a fresh Alpine/musl volume; no legacy/cross-libc raw
volume migration is supported or required. Preserve that decision.

Unrelated Dependabot PR `#12` and PR `#13` are open. Do not modify, comment on,
close, merge, reuse, or otherwise act on them.

## Strategic context

The Compose stack already creates exact password-free privilege roles and ten
distinct login principals. It generates future service DSN files, but no
long-running process receives one and no online pool exists. All six backend
HTTP apps currently expose only process health and report ready without an
application dependency.

Before identity/setup work, Control API must prove the complete pattern for:

```text
one process
one separately mounted credential
one exact login/privilege role
one bounded pool
one read-only readiness function
one fail-closed health dependency
```

This pattern must not become a generic locator that gives every process a
database credential.

## Allowed path scope

Keep changes within these paths/families plus the required OAP transcript:

```text
.github/workflows/ci.yml
AGENTS.md
CONTRIBUTING.md
README.md
compose.yaml
docs/CONFIGURATION.md
docs/DATABASE_BOOTSTRAP.md
docs/DATABASE_CONNECTIONS.md
docs/DATABASE_ROLES.md
docs/DEPLOYMENT.md
docs/OPERATIONS.md
docs/SERVICE_AUTHORITY.md
migrations/alembic/README.md
services/backend/src/slaif_agent_site/application.py
services/backend/src/slaif_agent_site/control_api/**
services/backend/src/slaif_agent_site/db/**
services/backend/tests/conftest.py
services/backend/tests/integration/**
services/backend/tests/unit/**
tests/packaging/**
tests/repository/test_repository_policy.py
tools/check_repository.py
tools/compose/**
tools/local_secrets/initialize.py
oap/active
oap/orders/009-a-control-database-readiness-boundary.md
oap/reports/009-a-control-database-readiness-boundary.md
```

No dependency or lockfile change is authorized. Do not edit Dockerfiles,
supply-chain policy/scanners/notices/exceptions, browser/Web/edge routes,
architecture/security/protocol files, content schema, foundation package, or
prior OAP artifacts. If a required path is missing, report rather than expand.

## Requirements

### A. Separate Control API secret mount

The default local deployment must expose exactly one Control API DSN file to
the Control API and no other database credential.

Use a separate named secret volume or an equivalently enforced single-file
subpath mount that passes live Docker inspection. The Control API container
must not be able to read:

- PostgreSQL administrator password;
- provisioner or setup-owner DSN;
- another service DSN/login password;
- the master local-secret directory;
- Docker socket or host paths.

The secret initializer may derive/copy the already generated fixed
`slaif_control_login` DSN into the isolated mount without printing or changing
its value. Requirements:

- cryptographically generated password remains the existing source;
- isolated directory/file ownership and mode are exact and idempotent;
- only initializer writes; Control API mounts read-only;
- bootstrap can provision/authenticate the same fixed login without needing
  the isolated runtime mount;
- no environment variable contains a plaintext DSN;
- an unrelated backend UID/process and every other long-running service is
  denied the file.

Do not redesign all service-secret distribution in this objective. Establish
the Control pattern only.

### B. Typed Control database configuration

Add a Control-specific frozen Pydantic settings model in the Control package,
not shared `ServiceSettings` and not a generic database locator.

It must:

- use a `SLAIF_CONTROL_` prefix;
- require an absolute mounted DSN file in production/development Compose;
- allow a direct fake locator only in explicit test mode;
- validate bounded pool min/max, acquire/command/connect timeout, application
  name, and expected database/login/privilege-role identities;
- reject credentials/query options that weaken TLS/target identity where
  relevant to production while permitting the documented internal local demo;
- use secret-safe types and constant configuration errors;
- never expose a raw locator/password through repr, JSON, logs, health, CLI,
  exception, or report.

No Agent, Editor, Render, MCP, Media, Review, Scheduler, GC, Web, or browser
settings model may load this prefix or file.

### C. Bounded asyncpg pool lifecycle

Implement a Control-owned adapter with no import-time side effects.

- Create the pool only inside the Control API lifespan after ordinary config
  is validated.
- Use existing exact asyncpg 0.31.0; no SQLAlchemy ORM/session or new driver.
- Bound pool sizes, connection/acquire/command timeouts, idle lifetime, and
  shutdown.
- On every newly created connection, verify expected database, session/login
  identity, effective membership in exactly `slaif_control`, and absence of
  owner/reviewer/agent/editor authority before admitting it to the pool.
- Apply safe session defaults such as application name and bounded statement/
  lock/idle-transaction timeouts without accepting caller-controlled SQL.
- Release/close cleanly on normal shutdown, startup failure, cancellation, and
  lifespan exception. No pool/client/task leaks across tests.
- Expose no `native`/raw SQL endpoint or global dependency locator.

The application runner must start the package-local Control app so this
lifespan is actually used. `python -m slaif_agent_site.control_api --check`
must remain no-network/no-connection/no-mutation while validating the
configuration boundary safely.

### D. Owner-created read-only readiness function

Add exactly one new Alembic revision/head after `006_001`. It may create only
the minimum read-only Control readiness function and necessary grant metadata;
no product table is authorized.

The function must:

- be owned by `slaif_owner`;
- be `SECURITY DEFINER` only if required, with fixed `search_path=pg_catalog`;
- return a bounded typed fact such as current migration revision, readiness
  state, safe boolean, foundation version, and/or a single readiness decision;
- read only the owner-controlled bootstrap marker/version state;
- accept no caller-supplied site/workspace/session/operation identifier;
- revoke `PUBLIC` and grant execute only to `slaif_control`;
- be unavailable to Agent, Editor, readers, Reviewer, Scheduler, Media, GC,
  unrelated logins, and MCP/Web/browser processes;
- have deterministic upgrade/downgrade and privilege-verifier coverage.

Do not grant direct marker-table SELECT merely for convenience if the narrow
function is sufficient. Do not weaken `EMPTY_SAFE`/`HARDENED` semantics.

### E. Readiness semantics

Control API `/health/live` remains independent of PostgreSQL. Its
`/health/ready` adds one injected `database` component.

Ready only when:

- pool startup and credential identity verification succeeded;
- the readiness function executes through the Control pool;
- database migration is at the exact packaged head;
- marker state is `EMPTY_SAFE` or `HARDENED` and `safe=true`;
- qualified foundation version matches current expectations.

Return stable bounded reason codes for unavailable connection, identity/role
mismatch, migration mismatch, unsafe/pending marker, timeout, and shutdown.
Never return exception text, SQL, schema object names beyond documented stable
component identity, DSN, host, user, password, or internal details.

Database failure must make Control readiness 503 and block NGINX dependency
readiness in Compose. It must not make liveness falsely fail.

### F. Compose and authority topology

- Mount only the isolated Control secret into `control-api`.
- Keep Control on its existing edge/database networks and sole process command.
- Preserve all service/network/port/capability/read-only/CSP/request-ID/base-
  image behavior.
- Update `depends_on`/health only as needed so bootstrap completion precedes
  Control pool startup and NGINX waits for true Control database readiness.
- A deliberately wrong login/role, unreadable secret, unsafe marker, stopped
  PostgreSQL, or migration mismatch must keep Control/NGINX unready without
  exposing the secret.
- Other HTTP services remain health-only and database-free.

### G. Tests

Add focused tests proving:

- Control settings direct/file/mode/bounds and redaction;
- no other process imports/loads Control DB settings or receives its mount;
- exact live mount ownership/read denial and no master-secret visibility;
- pool startup identity/role checks and rejection of wrong/combined/owner/
  reviewer credentials;
- pool cancellation/startup/shutdown/acquire cleanup;
- readiness function ownership, search path, `PUBLIC` revoke, exact grant, and
  denial matrix;
- liveness versus readiness success/failure/timeout/sanitization;
- migration upgrade/repeat/downgrade/rebuild and packaged head;
- Compose clean startup reaches Control `database=ok` and failure fixtures
  keep NGINX unavailable;
- no product route/table/SQL endpoint/auth behavior was introduced.

Run one focused disposable PostgreSQL version locally; GitHub runs the existing
PostgreSQL 14–18 matrix. Do not run all five locally.

### H. Documentation

Add `docs/DATABASE_CONNECTIONS.md` and update relevant current-state docs with:

- exact Control credential/pool/readiness ownership;
- secret mount and role identity;
- lifecycle/timeouts/failure behavior;
- readiness function/grant boundary;
- local versus production TLS/secret expectations;
- explicit statement that no setup/auth/user/session/site/product route exists;
- pattern requirements before another process receives a database credential.

Keep the project pre-alpha and fresh-install-only.

## Explicit non-goals

- No installation/user/password/setup token, login/logout, cookie, session,
  CSRF, recent-auth, OIDC, membership, site, workspace, capability, content,
  audit event, job, media, browser, review, promotion, or publication behavior.
- No database credential/pool for any process except Control API.
- No generic pool registry/service locator, raw SQL route, ORM, migration from
  request input, RLS claim, service authentication, TLS automation, or metrics.
- No dependency/base/scanner/image update, vulnerability/license exception,
  supply-chain redesign, or action on PR `#12`/`#13`.
- No second objective PR, merge, auto-merge, release, tag, or deployment.

## Attempt ledger and execution discipline

The report must list every focused database/Compose attempt, including failed
ones, with duration, stage, cause, and subsequent change. It must explicitly
confirm zero local full supply-chain and full matrix runs.

Use focused tests before the one implementation push. If a genuine in-scope CI
defect appears, one corrective commit is allowed. Do not respond by broadening
the objective.

## Acceptance criteria

1. Exactly one non-draft objective-009 PR exists with required identity and
   complete versioned OAP transcript; no merge by coding agent.
2. Only Control API receives one isolated read-only DSN file and only
   `slaif_control_login`/`slaif_control` authority; no master/other secret is
   readable.
3. Control pool is lifespan-owned, bounded, identity-verified, cancellation-
   safe, and absent at import/check mode.
4. The sole new migration adds one narrow read-only readiness function with
   exact owner/search-path/revoke/grant/denial behavior and no product table.
5. Control liveness remains process-only; readiness truthfully follows exact
   database/migration/marker/foundation state with sanitized bounded failures.
6. Compose clean start is green and wrong credential/role/marker/database
   failures block Control and NGINX readiness without secret leakage.
7. Other processes remain database-free and every accepted 008 supply-chain/
   topology/security invariant remains green.
8. Focused local verification stays within budget; GitHub's full 20-check set
   passes with zero CodeQL alerts.
9. Documentation is exact and makes no authentication/product-readiness claim.
10. `oap/active` is `009-a`, unique correlation holds, prior artifacts remain
    immutable, and report publication follows protocol 1.2.

## Verification required

Run only focused unit/integration/packaging tests for the Control config/pool/
function/mount/readiness boundary, one local disposable PostgreSQL major,
affected Ruff/format/mypy/repository/Markdown checks, `docker compose config`,
targeted Control startup/failure fixtures, and `git diff --check`.

Do not run locally:

```text
tools/supply_chain/run.sh
six-image SBOM/Grype or reproducibility gate
full Python 3.12–14 matrix
full PostgreSQL 14–18 matrix
full clean/restart/failure Compose smoke
```

The unchanged complete gates run once in GitHub CI.

## Safety / security constraints

Use fake disposable credentials/databases/volumes only. Never print a DSN or
password. Do not mount the master secret volume into Control. Resolve cleanup
targets exactly; no broad Docker prune. Fail closed on identity, marker,
migration, or secret ambiguity.

## Local execution capability

Routine asyncpg/PostgreSQL/Compose/test setup and CI diagnosis belong to the
coding agent in its disposable VM. Passwordless `sudo` is available.

## GitHub workflow

Create `oap/009-control-database-readiness` from current remote `main`, commit
the exact activated order/pointer with the implementation, push, and create
one non-draft PR. Never touch PR `#12`/`#13`, create another objective PR, or
merge.

## Required report

Atomically publish exactly:

```text
oap/reports/009-a-control-database-readiness-boundary.md
```

Use protocol 1.2 in full. Include the attempt ledger, migration/function/grant
facts, credential/mount/pool/readiness evidence, failure/cleanup results,
local-run restraint, full GitHub checks/artifact/alerts, exact scope, literal
implementation head, and `Report publication commit: SELF`.
