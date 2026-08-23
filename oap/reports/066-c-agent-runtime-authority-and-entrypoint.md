# OAP Coding-Agent Report — 066-c

## Work order

- Identifier: `066-c`
- Work-order file: `oap/orders/066-c-agent-runtime-authority-and-entrypoint.md`
- Numeric objective: `066`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Closed the remaining Agent API authority and deployment gap on existing PR #57.
Agent API now uses fixed `slaif_agent_login` / `slaif_agent_runtime`
settings, its own file-backed Agent DSN, a real owned database pool and
lifespan, and the real `agent_api.create_app()` from its module entrypoint.

Capability lookup is shared through a neutral semantic helper and remains
bounded to the existing capability/workspace read surface. PostgreSQL grants
now give only the Control and Agent runtime roles the required SELECT/USAGE
authority; Agent runtime cannot execute Control setup/workspace functions or
write Control relations.

Compose now creates and mounts a private Agent DSN only to `agent-api`, while
Control and Render mounts remain separate. NGINX preserves Agent API paths and
provides exact health aliases. The complete local Compose smoke, including
browser E2E, recovery, secret isolation, edge headers, and Apache validation,
passes.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#57](https://github.com/ulfe-lmi/slaif-agent-site/pull/57)
- PR state: `OPEN`
- Base/head branches: `main` / `oap/066-capability-auth`
- Starting remote SHA for this continuation: `d32f0d134de29bc04141a9135656437ee8e18896`
- Base remote SHA: `6552ee74e9046bb86e57d68acdef6acd0b0d1c07`
- Implementation head SHA: `925d2a052b18f06a7bf44e5f5fec882436035a31`
- Implementation commits pushed this round: `d9c08222ecac40b81298deca74fcb6d0e44d51e6`, `925d2a052b18f06a7bf44e5f5fec882436035a31`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified after publication)
- Prior 066-a/066-b implementation and report history preserved: yes
- Report parent must equal implementation SHA: yes
- New PR this turn: no
- Amended existing PR: yes, PR #57 only
- Merge performed: NO

## Changes made

- Added typed `AgentDatabaseSettings` with fixed Agent identity, mounted-file
  production locator validation, test locators, TLS requirements, bounded pool
  settings, and constant-safe configuration failures.
- Replaced the ControlDatabase-backed Agent adapter with an Agent-owned pool
  and shared neutral capability lookup record/helper.
- Added Agent identity initialization/readiness checks and fail-closed
  unavailable, timeout, wrong-identity, wrong-role, and missing-locator paths.
- Changed `agent_api.__main__` to construct the real app/lifespan and preserve
  `--check` without opening a database connection.
- Extended privilege application/validation so only `slaif_control` and
  `slaif_agent_runtime` receive capability/workspace SELECT and Control schema
  USAGE; Control functions remain Control-only.
- Added Agent secret initialization, `/run/slaif-agent/agent-dsn`, Compose
  volume/environment wiring, topology validation, and secret-isolation tests.
- Added exact Agent health aliases and prefix-preserving Agent API proxying in
  NGINX.
- Added Agent identity/privilege, entrypoint, factory, package, deployment,
  and real PostgreSQL regression evidence.

## Files changed this round

- `compose.yaml`
- `infra/nginx/nginx.conf`
- `oap/active` and `oap/orders/066-c-agent-runtime-authority-and-entrypoint.md`
  were committed in the implementation transcript with the exact strategic
  066-c bytes.
- `services/backend/src/slaif_agent_site/agent_api/__main__.py`
- `services/backend/src/slaif_agent_site/agent_api/app.py`
- `services/backend/src/slaif_agent_site/agent_api/config.py`
- `services/backend/src/slaif_agent_site/agent_api/database.py`
- `services/backend/src/slaif_agent_site/agent_state/capability_auth.py`
- `services/backend/src/slaif_agent_site/control_api/database.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/tests/integration/test_capability_authentication.py`
- `services/backend/tests/unit/test_agent_config.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `services/backend/tests/unit/test_process_entrypoints.py`
- `tests/packaging/test_compose_policy.py`
- `tests/packaging/test_local_secrets.py`
- `tools/compose/verify.py`
- `tools/local_secrets/initialize.py`

## Acceptance-criteria evidence

### Criterion 1 — Normal Agent startup uses the full factory/lifespan and serves routes

- PASSED. `python -m slaif_agent_site.agent_api --check` returns
  `agent-api: CHECK_OK`; normal-run unit coverage patches only Uvicorn and
  verifies the real FastAPI app object and configured bind values.
- Local `sudo sh tools/compose/smoke.sh slaif007c` starts the complete Compose
  deployment with the real Agent entrypoint, waits for Agent health, and
  passes all edge/browser/recovery stages.
- The public NGINX route `/api/agent/v1/session` reaches the Agent app and
  returns its sanitized 401 response for missing credentials.

### Criterion 2 — Agent identity and capability lookup are distinct from Control

- PASSED. The real PostgreSQL test connects with the seeded
  `slaif_agent_login`, verifies session/current identity and membership in
  `slaif_agent_runtime`, and authenticates a seeded capability through the
  factory-managed Agent pool.
- Compose mounts `agent-secret:/run/slaif-agent:ro` only to Agent API and
  `control-secret:/run/slaif-control:ro` only to Control API; local inspect
  confirmed these mounts are separate.
- Agent environment contains only `SLAIF_AGENT_*` database settings; no
  Control DSN/login/fallback is present.

### Criterion 3 — Effective privilege is exactly bounded

- PASSED. Agent runtime has SELECT on `control.capability` and
  `control.workspace`, no INSERT privilege, and no Control setup or workspace
  function EXECUTE privilege in the real PostgreSQL regression.
- Bootstrap effective privilege validation passes with Agent schema USAGE and
  the bounded relation surface; no Control role grant was broadened beyond the
  capability read surface.
- Full database integration and Compose login/role policy tests pass.

### Criterion 4 — Credential failures are fail-closed and sanitized

- PASSED. Valid capability returns the correct immutable site/workspace/scope
  context; malformed, unknown, wrong-secret, revoked, and expired credentials
  return 401.
- Missing locator, unavailable database, and wrong-role settings return 503 or
  startup/readiness failure as appropriate, without token, DSN, SQL, driver, or
  filesystem details.
- The complete public edge smoke confirms Agent health aliases and request
  routing; local test asserts the public Agent route returns 401 rather than an
  edge 404.

### Criterion 5 — Scope, transcript, and deployment diff are bounded

- PASSED. No physical migration, dependency, raw agent SQL, mint/revoke,
  user-management, publication, COW mutation, MCP, browser, or reviewer
  behavior was added.
- The only deployment changes are the Agent credential volume/configuration,
  exact health aliases, and the required entrypoint/runtime wiring.

## Local verification

- `uv --version`: PASSED — uv `0.12.5`.
- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED — 186 files formatted.
- `uv run --frozen mypy`: PASSED — 174 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`: PASSED — 411 tests, 26 subtests.
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED — 94 tests.
- Focused Agent identity/entrypoint/privilege/secret/Compose regression command: PASSED — 64 tests, 8 subtests.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-066c-final.GRMo4f`: PASSED — sdist and wheel built.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 53 tests.
- `python tools/check_repository.py`: PASSED — repository policy.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; 192 Markdown files scanned.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 186 files, 0 issues.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `python tools/compose/verify.py`: PASSED — rendered topology.
- `sudo sh tools/compose/smoke.sh slaif007c`: PASSED — clean deployment,
  browser E2E, six stable devices, governance, secret policy, restart/recovery,
  render failure/recovery, negative bootstrap, Apache syntax, and cleanup.
- Package-aware process smoke for all ten prescribed modules using
  `uv run --frozen python -m ... --check`: PASSED — all ten returned `CHECK_OK`.

## GitHub CI / required checks

State observed for implementation head `925d2a052b18f06a7bf44e5f5fec882436035a31`:

- Analyze (actions): PASS
- Analyze (javascript-typescript): PASS
- Analyze (python): PASS
- CodeQL: PASS
- Compose and edge packaging: PASS on the superseding rerun after the prior
  implementation-head failure identified the missing exact Agent health aliases.
- Dependency review: PASS
- Detect supported languages: PASS
- Foundation PostgreSQL 14: PASS
- Foundation PostgreSQL 15: PASS
- Foundation PostgreSQL 16: PASS
- Foundation PostgreSQL 17: PASS
- Foundation PostgreSQL 18: PASS
- Markdown: PASS
- Mermaid: PASS
- Node contracts: PASS
- Python 3.12 quality and package: PASS
- Python 3.13 quality and package: PASS
- Python 3.14 quality and package: PASS
- Repository policy: PASS
- Supply-chain evidence: PASS
- All required checks green at drafting: YES.
- Report-only commit may trigger fresh checks; strategy must verify SELF independently.

## Local setup / dependencies

- Used uv `0.12.5`, Node `24.14.1`, pnpm `11.22.0`, disposable PostgreSQL,
  and an isolated Docker Compose project `slaif007c`.
- The unprivileged Docker attempt was denied by the local Docker socket; the
  explicitly ordered disposable smoke was then run through the permitted local
  Docker operator path and passed.
- The exact local Compose project containers, networks, volumes, and generated
  secrets were removed by the smoke trap.
- No production secret, system, or data was accessed; no dependency or lockfile
  changed.

## Documentation

- No durable product prose change was required; configuration and deployment
  behavior is documented by the typed settings, Compose verifier, and tests.
- This immutable OAP report is the required execution evidence artifact.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no.
- Production systems accessed: no.
- Required tests skipped/not run: no.
- Scope deviation: no.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated 066-c order content edited by coding agent: NO.
- Activated 066-c selector content edited by coding agent: NO.
- Report commit changes only this report: YES.

## Strategic selector timing note

During this continuation, strategy published the next selector value `066-d`
and its new order in the worktree before this 066-c response was sent. Those
strategic-owned bytes were preserved untouched, were not read or executed, and
were not included in the 066-c implementation/report commits. The remote 066-c
transcript remains anchored at the committed `066-c` selector/order until
strategy independently advances the next round.

## Known limitations / blockers

- Agent content mutation/COW writes, publication, review, promotion, and MCP
  behavior remain outside objective 066.
- The Agent runtime currently has the bounded capability/read and existing COW
  role surface; broader Agent content semantics remain future ordered work.

## Recommended strategic follow-up

Independently review PR #57, the authority/grant evidence, the Compose/edge
smoke result, the 066-a/066-b limitation closure, and report ancestry. Merge
only after strategic acceptance; coding-agent `COMPLETE` and green CI are not
acceptance.
