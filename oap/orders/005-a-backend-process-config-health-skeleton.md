# OAP Work Order — 005-a

## Objective

Create exactly one new GitHub pull request that establishes separately
startable backend HTTP/worker/bootstrap process skeletons plus shared typed
configuration, authority descriptors, safe errors, request correlation,
redacted JSON logging, and liveness/readiness primitives.

This objective makes process/credential boundaries explicit before any product
schema, database connection, authentication, semantic route, worker job, or
publication behavior exists.

## GitHub objective state

- Numeric objective: `005`
- Execution round: `005-a`
- PR mode: `CREATE_NEW_PR`
- Existing objective PR: N/A
- Required head branch: `oap/005-backend-process-skeleton`
- Base branch: `main`
- Required PR title: `[OAP 005] Add backend process and health skeletons`
- Required PR readiness: non-draft (`draft: false`)
- Repository: `ulfe-lmi/slaif-agent-site`

## Strategic context

Objectives `003` and `004` are merged. The repository now has a reproducible
Python backend package and Node/TypeScript contract workspace, but no product
process can start. Architecture Sections 11 and 15 require authority-separated
processes even when they share one Python package/image. Establishing those
boundaries now prevents later feature routes from implicitly receiving the
wrong credential/dependency class.

## Current verified state

- Remote `main` SHA:
  `579546098f91e17405f51ed5e409547affca63f0`
- Objective `004` PR `#6` is merged with its complete OAP transcript.
- Current merged active identifier: `004-a`.
- One unrelated automated Dependabot PR `#5` remains open. Do not modify,
  update, close, merge, comment on, or reuse it.
- `main` has the exact Python/pnpm locks and all current CI/CodeQL gates, but no
  FastAPI/Uvicorn/Pydantic settings dependency, product process package,
  service configuration, health route, or worker entrypoint.

Current direct versions selected after PyPI compatibility/license review:

```text
fastapi==0.141.1                  MIT, Python >=3.10
uvicorn==0.52.3                  BSD-3-Clause, Python >=3.10
pydantic==2.13.4                 MIT, Python >=3.9
pydantic-settings==2.15.0        MIT, Python >=3.10
asyncpg==0.31.0                  Apache-2.0, existing qualified lock record
httpx==0.28.1                    BSD-3-Clause, test group only
```

Use no FastAPI `standard`/`all` extra and no Uvicorn `standard` extra. Do not
select pydantic-settings cloud secret-manager extras. The runtime must remain
account-free and minimal.

Reverify versions/compatibility at execution time without silently changing
the selected versions. Report a material registry/API discrepancy.

## Required final tracked paths

The final PR diff against `main` must contain exactly these fifty-three paths:

```text
AGENTS.md
CONTRIBUTING.md
README.md
docs/CONFIGURATION.md
docs/SERVICE_AUTHORITY.md
oap/active
oap/orders/005-a-backend-process-config-health-skeleton.md
oap/reports/005-a-backend-process-config-health-skeleton.md
pyproject.toml
services/backend/src/slaif_agent_site/agent_api/__init__.py
services/backend/src/slaif_agent_site/agent_api/__main__.py
services/backend/src/slaif_agent_site/agent_api/app.py
services/backend/src/slaif_agent_site/application.py
services/backend/src/slaif_agent_site/authority.py
services/backend/src/slaif_agent_site/bootstrap/__init__.py
services/backend/src/slaif_agent_site/bootstrap/__main__.py
services/backend/src/slaif_agent_site/config.py
services/backend/src/slaif_agent_site/control_api/__init__.py
services/backend/src/slaif_agent_site/control_api/__main__.py
services/backend/src/slaif_agent_site/control_api/app.py
services/backend/src/slaif_agent_site/correlation.py
services/backend/src/slaif_agent_site/editor_api/__init__.py
services/backend/src/slaif_agent_site/editor_api/__main__.py
services/backend/src/slaif_agent_site/editor_api/app.py
services/backend/src/slaif_agent_site/errors.py
services/backend/src/slaif_agent_site/health.py
services/backend/src/slaif_agent_site/logging.py
services/backend/src/slaif_agent_site/mcp_adapter/__init__.py
services/backend/src/slaif_agent_site/mcp_adapter/__main__.py
services/backend/src/slaif_agent_site/mcp_adapter/app.py
services/backend/src/slaif_agent_site/media_gc/__init__.py
services/backend/src/slaif_agent_site/media_gc/__main__.py
services/backend/src/slaif_agent_site/media_service/__init__.py
services/backend/src/slaif_agent_site/media_service/__main__.py
services/backend/src/slaif_agent_site/media_service/app.py
services/backend/src/slaif_agent_site/render_api/__init__.py
services/backend/src/slaif_agent_site/render_api/__main__.py
services/backend/src/slaif_agent_site/render_api/app.py
services/backend/src/slaif_agent_site/review_worker/__init__.py
services/backend/src/slaif_agent_site/review_worker/__main__.py
services/backend/src/slaif_agent_site/scheduler/__init__.py
services/backend/src/slaif_agent_site/scheduler/__main__.py
services/backend/src/slaif_agent_site/worker.py
services/backend/tests/unit/test_authority.py
services/backend/tests/unit/test_config.py
services/backend/tests/unit/test_correlation_logging.py
services/backend/tests/unit/test_errors.py
services/backend/tests/unit/test_foundation_contract.py
services/backend/tests/unit/test_health_apps.py
services/backend/tests/unit/test_process_entrypoints.py
tests/repository/test_repository_policy.py
tools/check_repository.py
uv.lock
```

Do not add database migrations/schema, HTTP business routes, process Docker
files, generated OpenAPI files, environment files, log output, caches, pid
files, sockets, or any extra module/config path.

## Scope

### A. Exact minimal runtime dependencies

Update `pyproject.toml`/`uv.lock` so production dependencies are exactly:

- existing `agent-cow-postgresql==0.2.0`;
- `asyncpg==0.31.0` as an explicit product dependency rather than qualification
  only;
- FastAPI/Uvicorn/Pydantic/pydantic-settings at the exact versions above.

Move/remove the duplicate asyncpg qualification declaration as appropriate so
dependency ownership is clear. Add exact HTTPX `0.28.1` to tests only. Preserve
uv 0.12.5, build backend, Python range, frozen sources/hashes, and all quality/
foundation gates. No optional cloud/standard extras or new hosted SDK.

### B. Process authority descriptors

Implement a typed, immutable authority model in `authority.py` that enumerates
the ten process kinds and their conceptual credential/dependency class:

```text
control-api
editor-api
agent-api
render-api
mcp-adapter
media-service
review-worker
scheduler
media-gc
bootstrap
```

The mapping must encode the architecture boundary without storing credentials:

- bootstrap alone may later receive setup-owner authority;
- review worker alone may later receive reviewer authority;
- agent/editor are distinct COW runtime authority classes;
- control, scheduler, GC, media and render have only their narrow future class;
- MCP has internal HTTP/client authority and no DB class;
- no process combines setup, reviewer, and agent-facing authority;
- worker/bootstrap processes have no external listener;
- the model is testable and is not mistaken for actual authentication/grants.

Do not introduce a generic “all authority” container or dependency locator.

### C. Typed configuration

Implement Pydantic Settings-based configuration that:

- supports explicit `development`, `test`, and `production` modes;
- uses `SLAIF_` environment names and has no automatic cloud/account secret
  integration;
- validates public URL/scheme/host, bind host/port, log level/format,
  environment-file opt-in for development only, and bounded shutdown/readiness
  settings;
- models sensitive values with secret-safe types/repr/serialization and
  supports mounted secret-file references rather than requiring plaintext env;
- provides deterministic fake/test settings with no production secret;
- fails closed in production on weak/default/missing secret or unsafe public
  HTTP/cookie-relevant configuration;
- does not add or connect database URLs yet—only future authority/config slots
  documented as unimplemented.

No configuration exception/log/error may print a secret value.

### D. Shared HTTP application primitives

Implement:

- FastAPI application factory bound to one `ProcessKind`/authority descriptor;
- `/health/live` and `/health/ready` only, with stable typed schemas and
  injected async readiness probes that expose bounded component/status/reason
  but no credential/internal exception;
- default docs/OpenAPI route exposure disabled on deployed app skeletons while
  allowing deterministic in-process `app.openapi()` contract tests;
- structured application error envelope matching Architecture Section 24.10,
  safe `AppError` hierarchy and validation/error handlers;
- request ID/trace ID context middleware: validate bounded caller request ID or
  generate server value, never trust caller site/workspace/operation context,
  echo safe request ID header, and always reset contextvars;
- standard-library JSON log formatter/config with recursive key/value
  redaction for authorization/cookie/password/secret/token/capability/database
  URL/session/internal credential patterns, bounded values, correlation fields,
  and no full request/response payload;
- clean lifespan startup/shutdown and test dependency injection with no global
  pool/client/secret side effect at import.

### E. HTTP process packages

For each of control, editor, agent, render, MCP, and media service:

- expose a package-local `create_app()` using shared factory and exact process
  kind;
- support `python -m slaif_agent_site.<process>` through Uvicorn with typed
  settings and no import-string reload magic in production;
- expose only health routes in this objective;
- bind in development/test only when explicitly invoked; tests use ASGI
  transport and do not open external ports;
- include no DB connection, product route, auth, CORS wildcard, or placeholder
  endpoint that could be mistaken for implemented behavior.

Render API is documented internal-only; MCP has no DB authority; Agent API has
no reviewer/setup/canonical path.

### F. Non-listening worker/bootstrap entrypoints

Implement review-worker, scheduler, media-GC, and bootstrap module entrypoints
using shared `worker.py` lifecycle:

- no HTTP listener or Uvicorn import/use;
- explicit `--check`/equivalent safe configuration-and-authority startup smoke
  that exits successfully without DB/job/business work;
- normal run waits for cancellation/shutdown through injected placeholder
  runner and clearly logs `NOT_IMPLEMENTED`/idle skeleton status without busy
  loop or claiming product readiness;
- signal/shutdown behavior is deterministic and import has no side effect;
- bootstrap remains a one-shot skeleton with no migration/COW/role mutation.

### G. Tests and repository policy

Add unit/contract tests proving:

- exact process inventory and authority separation/prohibited combinations;
- all six apps have exactly live/ready routes, hidden external docs/OpenAPI,
  correct process identity, typed response/error schemas;
- readiness aggregate success/failure/timeout/error sanitization;
- config parsing/production failure/redacted representation/secret-file rules;
- correlation validation/generation/propagation/reset under concurrency;
- recursive JSON log redaction/bounds and no secret/error/payload leak;
- error handlers map stable codes/status/request IDs and sanitize validation;
- all ten `python -m ... --check` or app factory entrypoint smoke paths complete
  without binding a port/connecting DB/mutating state;
- HTTP app processes and non-listening worker processes cannot be wired to a
  forbidden authority class.

Update the existing package artifact expectations in
`test_foundation_contract.py` to accept exactly the new intended package files
while retaining rejection of tests/OAP/caches/secrets and all foundation
metadata/source tests.

Extend repository policy and isolated tests to require the process/config/
docs/test files, exact direct runtime/test dependencies, no forbidden extras/
cloud SDKs, authority process set, and absence of accidental service routes/
database configuration where a bounded static check is reliable.

### H. Durable documentation

Add:

- `docs/CONFIGURATION.md`: implemented settings, environment/secret-file
  rules, modes/defaults/production failures, process invocation/check commands,
  and explicitly deferred DB/identity/service behavior;
- `docs/SERVICE_AUTHORITY.md`: process inventory, listener status, conceptual
  future credential class, allowed/forbidden authority, and reminder that code
  descriptors do not replace DB grants/network/service auth.

Update README current status/repository map/CI, AGENTS and CONTRIBUTING exact
commands/process boundaries. Keep all runtime/product behaviors honest and
do not edit Architecture/foundation/Node contract docs/NOTICE.

## Non-goals

- No Alembic, PostgreSQL application connection/pool/config, control/content/
  audit schema, role grant, bootstrap mutation, site/user/workspace/capability,
  authentication/session/CSRF, semantic API/MCP tool, media bytes, browser,
  job queue, Puck/web UI, Compose/Docker/NGINX/Apache, metrics, OpenTelemetry,
  cache, publication/review, or external service.
- No public OpenAPI/docs listener, permissive CORS, wildcard trusted proxy,
  default production secret, `.env` committed, cloud secret-manager extra,
  Uvicorn standard extra, or FastAPI CLI/cloud dependency.
- No action on unrelated Dependabot PR `#5`.
- No extra PR/branch, merge, auto-merge, issue, release, tag, deployment, or
  GitHub setting change.

## Acceptance criteria

1. Exactly one non-draft objective `005` PR exists with required identity and
   final diff contains exactly the fifty-three allowed paths.
2. Frozen uv lock resolves exact minimal runtime/test dependencies only from
   PyPI with hashes and keeps foundation/Node locks and architecture unchanged.
3. Six HTTP apps start in-process with only typed live/ready routes, hidden
   public docs/OpenAPI routes, correct process identity, and no DB/network/
   product behavior.
4. Four worker/bootstrap entrypoints are non-listening, import-side-effect-free,
   support safe check/start-stop tests, and perform no product mutation.
5. Authority mapping makes forbidden combinations structurally/testably absent:
   Agent cannot receive reviewer/setup/canonical; MCP no DB; bootstrap/reviewer
   unique; no generic all-authority object.
6. Production config fails closed for missing/weak/unsafe values; secrets and
   validation exceptions are redacted from repr/log/error/JSON.
7. Request/trace correlation is bounded, reset under concurrency, and never
   treats caller site/workspace/operation headers as trusted context.
8. Error/health/log contracts are stable, typed, bounded, and tested for
   failures/timeouts/redaction.
9. Package artifacts contain exactly intended expanded backend modules and no
   tests/OAP/cache/secret; Python 3.12–3.14 quality/package and PostgreSQL 14–18
   foundation matrices remain green.
10. Repository-policy positives/negatives enforce the new process/dependency/
    configuration boundary; Node contract checks and three-language CodeQL stay
    green.
11. Docs/README/governance accurately state the skeleton and deferred features.
12. `oap/active` is `005-a`, unique order/report correlation holds, prior OAP
    artifacts are unchanged, and final head is report-only `SELF`.
13. All final-head checks succeed with zero unresolved CodeQL alert; unrelated
    PR `#5` remains untouched.

## Verification required

Run and report exact outcomes for:

```bash
uv lock --check
uv sync --frozen --all-groups
uv run --frozen ruff check services/backend tests/repository tools
uv run --frozen ruff format --check services/backend tests/repository tools
uv run --frozen mypy
uv run --frozen pytest services/backend/tests/unit tests/repository
uv build
python tools/check_repository.py
python tools/check_mermaid.py
pnpm install --frozen-lockfile
pnpm check
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
git diff --check origin/main...HEAD
git diff --name-only origin/main...HEAD
```

Also verify:

- exact PyPI versions/licenses/sources/hashes and absence of forbidden extras;
- clean production-only wheel install/import plus package content/metadata;
- all ten entrypoint/app-factory smoke paths with no ports/DB/state mutation;
- app route/OpenAPI inventory and error/health JSON schemas;
- config/secret/log/correlation negative/concurrency fixtures;
- authority truth table and forbidden dependency wiring;
- Python/PostgreSQL/Node/CodeQL full regression matrices;
- exact fifty-two pre-report/fifty-three final paths and protected hashes;
- focused secret scan, PR identity/body, final checks/alerts, report parent/
  delta, clean synchronized worktree.

Application domain/database/auth/UI behavior is `NOT IMPLEMENTED/NOT RUN`, not
passed. Worker smoke is lifecycle evidence only, not job processing.

## Safety / security constraints

- Use fake test secrets and in-memory/injected probes only; no production or
  external system.
- Never log/print real or fake secret values in evidence.
- Do not create a DB connection or product credential in this objective.
- Do not weaken existing dependency/action/license/quality/OAP gates.

## Local execution capability

Routine Python/dependency/process/test setup and CI diagnosis belong to the
coding agent in its disposable VM. Do not transfer them to the human or
strategic model.

## GitHub workflow

Create `oap/005-backend-process-skeleton` from current remote main. Preserve
the active order/pointer, implement only the fifty-two pre-report paths, run
all checks, push and create one non-draft PR, then repair in-scope failures on
that same PR. Atomically publish the report as the fifty-third path in a final
report-only `SELF` commit. Never touch PR `#5`, merge, auto-merge, create a
second PR, or choose `006-a`.

## Required report

Atomically publish exactly:

```text
oap/reports/005-a-backend-process-config-health-skeleton.md
```

Use full protocol 1.2. Include exact dependency/source/license/lock evidence;
process/listener/authority/config inventories; route/OpenAPI/error/health/log/
correlation tests; entrypoint lifecycle results; package artifacts; all local
and GitHub matrices/alerts; untouched PR #5; setup; deferred features; exact
scope and safety/no-merge confirmations. Signal FIFO `OK` only after verified
report-only publication.
