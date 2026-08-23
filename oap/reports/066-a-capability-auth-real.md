# OAP Coding-Agent Report — 066-a

## Work order

- Identifier: `066-a`
- Work-order file: `oap/orders/066-a-capability-auth-real.md`
- Numeric objective: `066`
- PR mode: `CREATED_NEW_PR`

## Status

COMPLETE

## Executive summary

Implemented real capability authentication for the Control database boundary.
The implementation validates the exact bearer token format, performs a
parameterized lookup by public ID, compares the complete presented-token digest
in constant time, enforces revocation and expiry, and returns the existing
immutable `AgentCapabilityContext`. Invalid credentials produce the Agent API's
sanitized 401 response; unavailable database state produces a sanitized 503.

The control role now has SELECT-only access to the two existing control
relations required for this lookup; no migration, dependency, or broader role
authority was added. Real disposable-PostgreSQL and ASGI boundary tests cover
the valid, malformed, unknown, wrong-secret, revoked, and expired paths.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#57](https://github.com/ulfe-lmi/slaif-agent-site/pull/57)
- PR state: `OPEN`
- Base/head branches: `main` / `oap/066-capability-auth`
- Starting remote SHA: `6552ee74e9046bb86e57d68acdef6acd0b0d1c07`
- Implementation head SHA: `25317bf7f15b3fe2c490890de118b38fcdcf1a18`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified after publication)
- Implementation commits pushed before report: `25317bf7f15b3fe2c490890de118b38fcdcf1a18`
- Report parent must equal implementation SHA: yes
- New PR this turn: yes
- Amended existing PR: no
- Merge performed: NO

## Changes made

- Added `ControlDatabase.authenticate_agent_capability()` with token parsing,
  parameterized lookup, constant-time digest comparison, lifecycle checks, and
  immutable trusted-context construction.
- Changed Agent API authentication failures to the existing 401
  authentication envelope and kept database failures sanitized as 503.
- Granted `slaif_control` SELECT-only access to `control.workspace` and
  `control.capability`, and extended effective privilege validation accordingly.
- Added real PostgreSQL plus Agent HTTP boundary coverage for all required
  credential cases and unavailable-database behavior.
- Updated the existing ControlDatabase public-surface unit expectation for the
  new method.

## Files changed

- `oap/active` (strategic-authored selector committed byte-for-byte)
- `oap/orders/066-a-capability-auth-real.md` (strategic-authored order committed byte-for-byte)
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py`
- `services/backend/src/slaif_agent_site/control_api/database.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/tests/integration/test_capability_authentication.py`
- `services/backend/tests/unit/test_control_database.py`

## Acceptance-criteria evidence

### Criterion 1 — Valid stored capability returns the trusted context

- PASSED. `test_capability_authentication_positive_negative_and_expiry_paths`
  seeds a real `control.capability` row, authenticates through
  `ControlDatabase`, and verifies capability, site, workspace, and scope values.
- The same test calls `/api/agent/v1/session` through ASGI with the real
  ControlDatabase adapter and receives HTTP 200 with the bound workspace.

### Criterion 2 — Invalid, unknown, incorrect, revoked, and expired credentials fail closed

- PASSED. The real PostgreSQL/ASGI test verifies malformed, unknown public ID,
  wrong secret, revoked, and expired credentials each return HTTP 401.
- The direct adapter assertions verify the same negative cases return no
  context.

### Criterion 3 — Secret and infrastructure details are not exposed

- PASSED. The test asserts presented tokens and digest wording are absent from
  denial responses, and the unavailable-pool response is HTTP 503 without a
  database locator or token.
- The implementation does not log or include token, digest, SQL, driver, or
  locator details.

### Criterion 4 — Authentication uses real lookup, digest comparison, and lifecycle checks

- PASSED. `CAPABILITY_AUTHENTICATION_SQL` uses `$1` for the public-ID lookup and
  enforces `revoked_at IS NULL` and `expires_at > CURRENT_TIMESTAMP`.
- The complete presented token is hashed with the existing helper and compared
  with the stored digest through the existing constant-time helper; the checks
  are also revalidated before context construction.

### Criterion 5 — Scope is bounded and no physical migration or unrelated trust change is present

- PASSED. The staged diff contains no Alembic migration, dependency, route
  family, publication, workspace lifecycle, MCP, browser, or infrastructure
  change. The only additional authority is the required SELECT-only access to
  the two existing control relations.

## Local verification

- `uv --version`: PASSED — uv `0.12.5`.
- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED.
- `uv run --frozen mypy`: PASSED — 171 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`: PASSED — 407 tests, 26 subtests.
- `uv run --frozen pytest services/backend/tests/integration/test_capability_authentication.py -q`: PASSED — 1 test.
- `uv run --frozen pytest services/backend/tests/integration -q`: first run had 90 passed and 4 setup errors because the disposable default PostgreSQL database contained a stale `agentcow` schema owned by `postgres`; after inspecting that exact schema (only foundation metadata objects) it was removed with the local test cleanup command `sudo -u postgres psql --no-psqlrc -X -d postgres -v ON_ERROR_STOP=1 -c 'DROP SCHEMA "agentcow" CASCADE'`, then the exact command was rerun and PASSED — 94 tests.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-066.9Zfsnd`: PASSED — sdist and wheel built.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 53 tests.
- `python tools/check_repository.py`: PASSED — repository policy.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; 188 Markdown files scanned.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 182 files, 0 issues.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- Literal process smoke command using system `python -m ... --check`: FAILED for all ten modules because the src-layout package is not on system Python's import path from repository root; no code was changed for this environment-only invocation failure.
- Frozen package-aware equivalent, `uv run --frozen python -m ... --check` for all ten prescribed modules: PASSED — every process returned `CHECK_OK`.

## GitHub CI / required checks

State observed for implementation head `25317bf7f15b3fe2c490890de118b38fcdcf1a18`:

- Analyze (actions): PASS
- Analyze (javascript-typescript): PASS
- Analyze (python): PASS
- CodeQL: PASS
- Compose and edge packaging: PASS
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

- Used the repository-pinned uv, Python, Node, and pnpm toolchains.
- Used disposable local PostgreSQL fixtures and removed only the identified
  stale foundation schema from the local default test database.
- No production dependency, lockfile, hosted service, secret, or infrastructure
  change.
- Temporary package distributions were written under `/tmp`; no build outputs
  were committed.

## Documentation

- No durable product documentation change was required by this implementation.
- The immutable OAP report is the required execution evidence artifact.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no.
- Production systems accessed: no.
- Required tests skipped/not run: no; the system-Python smoke invocation failed
  due to src-layout environment resolution, and its frozen package-aware
  equivalent passed.
- Scope deviation: no.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated order content edited by coding agent: NO.
- Active selector content edited by coding agent: NO.
- Report commit changes only this report: YES.

## Known limitations / blockers

- The Agent API process factory remains the bounded process skeleton established
  by the preceding runtime-wiring objective; this round validates the real
  ControlDatabase adapter at the Agent HTTP boundary but does not add a new
  AgentDatabase lifecycle or runtime credential wiring beyond this order.
- The full product publication, workspace COW mutation, and reviewer workflows
  remain outside this bounded objective.

## Recommended strategic follow-up

Independently review PR #57, its privilege-boundary addition, and the report
ancestry; merge only if strategically accepted. The next bounded runtime order
should explicitly reconcile Agent API process wiring with the capability
authentication adapter before exposing the complete service as production-ready.
