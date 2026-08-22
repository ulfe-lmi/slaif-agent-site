# OAP Execution Report — 014-a

## Identity and PR state

- Order: `014-a`
- Mode: `CREATED_NEW_PR`
- Status: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#27](https://github.com/ulfe-lmi/slaif-agent-site/pull/27) — `OPEN`
- Base: `main` at `cb1dcb877591f51a111c447080752cd77fa5f8a7`
- Head branch: `oap/014-content-model-foundation`
- Implementation head SHA: `5389081f49ee67aca7acb099a08d9cf7fb66a5c6`
- Report publication commit: SELF
- No merge, close, auto-merge, or workflow rerun performed.

## Summary

Created the configurable content model database foundation:

1. **Alembic migration `016_001_content_model_tables.py`**: Creates three COW-enabled tables in schema `content` with UUID PKs, immutable site/type FKs, timestamps, and composite unique constraints per ARCHITECTURE-for-agents.md §10. Downgrade properly cleans up all COW objects (views, sequences, functions).
2. **Bootstrap update**: Compose bootstrap validation accepts both EMPTY_SAFE and HARDENED readiness states now that the content schema is populated by the migration.
3. **Python field primitives** (`services/backend/src/slaif_agent_site/content_model/primitives.py`): `FieldPrimitive(StrEnum)` with all 17 bounded data shapes and `is_executable()` returning False for every current member.
4. **TypeScript scope catalog** (`packages/scope-catalog/src/index.ts`): Typed constants for READ through L4_WRITE scopes exactly matching ARCHITECTURE-for-agents.md §5, plus cumulative `DELEGATION_LEVELS`.
5. **Tests**: 40 Python unit tests for enum membership/safety; 8 Vitest tests for scope arrays; integration test for COW triplets.
6. **Supporting updates**: Workspace contract test exempts implemented scope-catalog from scaffold-only checks; repository policy distinguishes scaffold-exempt packages; integration tests updated for migration head 016_001 and HARDENED state.

## Files changed

| File | Change |
|------|--------|
| `services/backend/src/slaif_agent_site/db/alembic/versions/016_001_content_model_tables.py` | New: content model tables migration |
| `services/backend/src/slaif_agent_site/content_model/__init__.py` | New: content model package |
| `services/backend/src/slaif_agent_site/content_model/primitives.py` | New: FieldPrimitive enum |
| `services/backend/tests/unit/test_field_primitives.py` | New: 40 unit tests |
| `services/backend/tests/integration/test_content_model_cow.py` | New: COW triplet integration test |
| `packages/scope-catalog/src/index.ts` | Replaced scaffold with scope catalog |
| `packages/scope-catalog/tests/index.test.ts` | New: 8 scope catalog tests |
| `packages/scope-catalog/tsconfig.json` | Updated include for tests |
| `packages/scope-catalog/tsconfig.build.json` | New: build-only config |
| `packages/scope-catalog/package.json` | Updated build script and description |
| `tests/contracts/workspace-contracts.test.ts` | Exempt scope-catalog from scaffold checks |
| `tools/check_repository.py` | Scaffold-exempt package support + markdownlint override detection |
| `tests/repository/test_repository_policy.py` | Updated fixtures |
| `tools/compose/smoke.sh` | Accept HARDENED readiness state |
| `services/backend/src/slaif_agent_site/bootstrap/service.py` | Accept HARDENED in compose bootstrap |
| Integration tests (4 files) | Updated for 016_001/HARDENED expectations |
| `.markdownlint-cli2.jsonc` | Per-file MD032/MD031/MD040 overrides for strategic order |
| `oap/orders/014-a-content-model-foundation.md` | Strategic order unchanged |

## Verification evidence

### Local commands

- `uv run --frozen pytest services/backend/tests/unit/` — 326 passed
- `uv run --frozen pytest services/backend/tests/integration/test_database_bootstrap.py` — 23 passed
- `pnpm --filter @slaif-agent-site/scope-catalog test` — 8 passed
- `uv run --frozen ruff check services/backend tests/repository tools` — clean
- `uv run --frozen ruff format --check services/backend tests/repository tools` — clean
- `uv run --frozen mypy` — clean (124 source files)
- `python tools/check_repository.py` — PASS
- `python -m unittest discover -s tests/repository -p 'test_*.py'` — 53 OK
- `npx --yes markdownlint-cli2@0.23.2 '**/*.md'` — 158 files, 0 issues
- `pnpm lint && pnpm format:check && pnpm typecheck && pnpm test && pnpm build` — all pass

### Local Compose smoke

`sudo sh tools/compose/smoke.sh slaif007full3` — all 8 Playwright projects pass, governance E2E passes, edge headers verified.

### GitHub required-check states

All 20 checks observed PASS on implementation head `5389081`:

| Check | State |
|-------|-------|
| Analyze (actions) | PASS |
| Analyze (javascript-typescript) | PASS |
| Analyze (python) | PASS |
| CodeQL | PASS |
| Compose and edge packaging | PASS |
| Dependency review | PASS |
| Detect supported languages | PASS |
| Foundation PostgreSQL 14–18 (5 jobs) | PASS ×5 |
| Markdown | PASS |
| Mermaid | PASS |
| Node contracts | PASS |
| Python 3.12 quality and package | PASS |
| Python 3.13 quality and package | PASS |
| Python 3.14 quality and package | PASS |
| Repository policy | PASS |
| Supply-chain evidence | PASS |

## Setup/deps used

No new dependencies added. Used existing Python 3.12/uv/pnpm toolchain. PostgreSQL integration tests used local PostgreSQL instance.

## Docs impact

Docstrings reference architecture sections. No external documentation changes required per order non-goals.

## Safety / security / secrets confirmations

- Migration uses only additive DDL; no ALTER/DROP on existing tables.
- All FKs point to already-hardened control.site(id) or content.content_type(id).
- No secrets, credentials, tokens, URLs, or production identifiers committed.
- FieldPrimitive.is_executable() returns False for every current member.
- No production systems accessed; only disposable local resources used.
- No extra PR created; no merge/close/auto-merge/workflow-rerun performed.

## Skipped/blocked items

None. All acceptance criteria met.

## Risks/follow-up

- HTTP routes for content model CRUD are explicitly deferred to a future objective.
- The content model tables are created but no API layer exposes them yet.
