# OAP Coding-Agent Report — 078-p

## Work order

- Identifier: `078-p`; work-order file: `oap/orders/078-p-bounded-site-theme-tokens.md`; numeric objective: 078, increment 2
- PR mode: `CREATED_NEW_PR`

## Status

COMPLETE

## Executive summary

Implemented the bounded `theme-schema/v1` site-theme data plane from verified
merged `main`, including append-only migration `065_001`, deterministic pure
defaults, public Agent discovery/read/PATCH, trusted SQL validation and COW
mutation semantics, human Editor/Puck controls, shared Render/Web projection,
generated OpenAPI/schema artifacts, and public acceptance evidence.

The only implementation defect found during verification was the human Editor
service passing Python dictionaries directly to asyncpg `jsonb` parameters. It
was corrected by serializing those four bounded groups with canonical JSON.
No product architecture or scope was expanded.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#79](https://github.com/ulfe-lmi/slaif-agent-site/pull/79), `OPEN`, `CLEAN`
- Base/head: `main` / `oap/078-2-site-theme-tokens`
- Starting remote SHA: `3cae3d6cef2a92e7068856d21bc9a47b8190c22e`
- Implementation head SHA: `b89ef7bce4026db8377c782e2c6bfa13ce5cc8c1`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (verified from GitHub after publication)
- Implementation commits pushed before report: `b89ef7bce4026db8377c782e2c6bfa13ce5cc8c1`; report parent will equal this SHA
- New PR this turn: yes, exactly one; amended existing PR: no; merge performed: NO

## Changes made

- Added the closed schema-derived palette, typography, layout, and shape token vocabulary with generated JSON/TypeScript authority.
- Added migration `065_001` after the verified `064_001` head, preserving valid legacy theme data through downgrade/re-upgrade and restoring legacy function/grant contracts.
- Added Agent `GET /api/agent/v1/theme-schema`, `GET /api/agent/v1/theme`, and `PATCH /api/agent/v1/theme` with scope/resource/version/idempotency/COW/quota/audit/race handling.
- Added human Editor/Puck schema-derived controls and human COW save/reset behavior.
- Added fixed product-owned renderer classes and computed-style coverage for canonical and authenticated preview output.
- Updated generated OpenAPI, route/privilege/repository checks, documentation, OAP ledgers, public acceptance, and smoke assertions.

## Files changed

The implementation commit changes exactly 54 paths:

- `README.md`
- `apps/web/app/styles.css`
- `apps/web/public/renderer-v1.css`
- `apps/web/src/admin/api.ts`
- `apps/web/src/admin/composition-editor.tsx`
- `apps/web/src/renderer/components.tsx`
- `apps/web/src/sites/render.ts`
- `apps/web/tests/renderer-behavior.test.ts`
- `apps/web/tests/surface.test.mjs`
- `contracts/openapi/agent-v1.json`
- `docs/API.md`
- `docs/TESTING.md`
- `oap/INCREMENTS.md`
- `oap/MVP-CONTRACT-AUDIT.md`
- `oap/MVP-PROGRESS.md`
- `oap/active`
- `oap/audits/078-1-merge-acceptance.md`
- `oap/orders/078-p-bounded-site-theme-tokens.md`
- `packages/composition-schema/src/index.ts`
- `packages/composition-schema/src/puck-adapter.ts`
- `packages/composition-schema/src/theme-schema-v1.json`
- `packages/composition-schema/src/theme-schema.ts`
- `packages/composition-schema/tests/puck-adapter.test.ts`
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py`
- `services/backend/src/slaif_agent_site/agent_api/models.py`
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`
- `services/backend/src/slaif_agent_site/agent_state/reads.py`
- `services/backend/src/slaif_agent_site/agent_state/workspace_models.py`
- `services/backend/src/slaif_agent_site/bootstrap/service.py`
- `services/backend/src/slaif_agent_site/content_model/nav_models.py`
- `services/backend/src/slaif_agent_site/content_model/service.py`
- `services/backend/src/slaif_agent_site/content_model/theme.py`
- `services/backend/src/slaif_agent_site/control_api/route_policy.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/065_001_bounded_theme_tokens.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/editor_api/nav_theme_http.py`
- `services/backend/src/slaif_agent_site/render_api/projection.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_control_database_integration.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/integration/test_editable_domain_proof.py`
- `services/backend/tests/integration/test_human_agent_session_control.py`
- `services/backend/tests/integration/test_render_projection_integration.py`
- `services/backend/tests/unit/test_agent_openapi.py`
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `services/backend/tests/unit/test_health_apps.py`
- `services/backend/tests/unit/test_route_policy.py`
- `tests/e2e/governance.spec.ts`
- `tests/e2e/preview.spec.ts`
- `tools/check_repository.py`
- `tools/compose/public_agent_acceptance.py`
- `tools/compose/smoke.sh`
- `tools/generate_theme_schema.py`

## Acceptance-criteria evidence

### Criterion 1 — public read/PATCH, defaults, COW, rendering, isolation

- Public Compose acceptance passed `theme-schema`, deterministic default read,
  changed public PATCH, exact replay, and readback through NGINX.
- The focused PostgreSQL Agent test passed defaults, version 2 mutation,
  replay, no-effect, and COW projection checks; Render integration passed
  changed preview theme versus unchanged canonical theme.
- Full Compose browser acceptance passed the human Editor/Puck theme update,
  authenticated preview projection, canonical non-change, and deterministic
  reset.

### Criterion 2 — scope, resource, lifecycle, and quota boundaries

- Focused Agent PostgreSQL coverage passed narrowed token/palette resource
  denial and unrelated `theme-global:write` substitution denial, with exact
  `403` outcomes; invalid and stale requests passed `422`/`409` outcomes.
- Existing full Agent integration and public acceptance retained the broader
  capability, site/workspace, lifecycle, quota, and canonical-isolation gates.

### Criterion 3 — closed validation and trusted boundaries

- Schema-derived enum validation, extra-key rejection, raw-style rejection,
  and malformed input paths are covered by the closed Pydantic/OpenAPI and
  migration SQL validators; focused Agent HTTP coverage passed invalid enum
  rejection with `422`.
- Generated schema and OpenAPI checks passed bidirectional drift validation;
  no arbitrary CSS, colors, URLs, fonts, breakpoints, JavaScript, or executable
  transform is accepted.

### Criterion 4 — idempotency, no-effect, concurrency, and recovery

- Focused Agent integration passed exact replay/no-effect accounting and the
  same-version race with one `200` winner, one `409` loser, one COW operation,
  and one semantic audit/idempotency effect.
- Full Compose public acceptance passed restart, outage, recovery, durable
  COW/browser, artifact, and canonical-independence checks.

### Criterion 5 — Editor/Puck, shared renderer, and browser computed styles

- `human-editor-theme-is-preview-scoped-and-computed` passed in the public
  authenticated preview fixture, asserting computed palette color, typography,
  width, spacing, grid gap, radius, and shadow for all declared token families.
- The test also passed canonical default-class/non-change assertions and reset
  the disposable COW theme through the public Editor API. Shared renderer unit
  coverage passed fixed class generation without unsafe inline styles.

### Criterion 6 — migration and operational contract

- `test_agent_065_theme_data_round_trip_preserves_legacy_state` passed valid
  data-bearing downgrade from `065_001` to `064_001`, upgrade back to head,
  and exact legacy data/function/grant preservation.
- Full integration and Compose smoke passed current-head readiness, role
  separation, secret-file policy, edge, Apache, and recovery checks.

### Criterion 7 — complete verification gates

- All required local frozen Python, Node, repository, supply-chain, Mermaid,
  Markdown, package, and Compose gates passed.
- Remote PR CI and CodeQL are green for implementation head `b89ef7b`.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED.
- `uv run --frozen mypy`: PASSED — no issues in 270 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED — 539 passed, 1 warning, 23.72s.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 206 passed, 1911.00s.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — sdist and wheel built.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 58 passed.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files, CLI 11.16.0.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues in 450 files.
- `node --version` / `pnpm --version`: PASSED — Node `v24.14.1`, pnpm `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `uv run --frozen python tools/generate_theme_schema.py --check`: PASSED.
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`: PASSED.
- `python -m tools.supply_chain.policy validate`: PASSED.
- `uv run --frozen python -m tools.supply_chain.policy notices --check`: PASSED — 298 components.
- `sh tools/compose/smoke.sh slaif007theme24`: PASSED — full Compose/NGINX/Apache/public-Agent/browser/restart/recovery smoke and 48 smoke tests.

## GitHub CI / required checks

All required checks were observed `SUCCESS` for implementation head
`b89ef7bce4026db8377c782e2c6bfa13ce5cc8c1` before report drafting:

- [Repository policy](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786810)
- [Detect supported languages](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428597/job/102512787116)
- [Node contracts](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786427)
- [Analyze (actions)](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428597/job/102512834106)
- [Analyze (python)](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428597/job/102512834051)
- [Analyze (javascript-typescript)](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428597/job/102512834142)
- [Python 3.12 quality and package](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512787635)
- [Python 3.13 quality and package](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786599)
- [Python 3.14 quality and package](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786629)
- [Foundation PostgreSQL 14](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786654)
- [Foundation PostgreSQL 15](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786935)
- [Foundation PostgreSQL 16](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786882)
- [Foundation PostgreSQL 17](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786707)
- [Foundation PostgreSQL 18](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786861)
- [Compose and edge packaging](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786753)
- [Supply-chain evidence](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786720)
- [Markdown](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512787039)
- [Mermaid](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786724)
- [Dependency review](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34365428534/job/102512786700)
- [CodeQL](https://github.com/ulfe-lmi/slaif-agent-site/runs/102513027904)

All required green at drafting: yes. The report-only commit may trigger fresh
checks; strategy must independently verify the SELF head.

## Local setup / dependencies

- Used the repository-pinned uv `0.12.5`, Node 24, pnpm `11.22.0`, disposable
  PostgreSQL/Compose services, Playwright browsers, Mermaid CLI, and existing
  test fixtures.
- No production dependency, hosted service, production resource, or real
  secret was added or accessed. No setup escalation was needed.

## Documentation

- Updated `README.md`, `docs/API.md`, and `docs/TESTING.md` for the bounded
  theme contract and its limitations.
- Reconciled `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`, and
  `oap/MVP-CONTRACT-AUDIT.md` to PR #77’s accepted merge and active 078/2.
- Committed `oap/audits/078-1-merge-acceptance.md` unchanged, plus the active
  order and `oap/active` bytes unchanged.

## Safety and scope confirmations

- Unrelated files changed: NO. The 54-path diff is the ordered single
  theme-schema/DB/API/renderer/editor/evidence merge unit.
- Production secrets accessed: NO. Production systems accessed: NO.
- Required tests skipped/not run: NO. The exact required local and remote gates
  ran; the report distinguishes narrow focused proofs from full gates.
- Scope deviation: NO. Remaining global-region/page-style/catalog,
  exact-workspace Puck, media/MCP, review, promotion, publication, and later
  objective work was not added.
- Extra objective PR: NO. Coding-agent merge: NO.
- Activated order/active edited by coding: NO; strategy-provided bytes were
  committed unchanged.
- Report commit changes only this report: YES.

## Known limitations / blockers

The coding order has no remaining blocker. Numeric Objective 078 remains
`PARTIAL`; global regions, page style, catalog expansion, exact Agent-workspace
Puck, review/freeze, promotion/publication, and later objectives remain outside
this increment. Strategy acceptance and merge of PR #79 are still pending.

## Recommended strategic follow-up

Strategy should independently verify the report-only SELF parent/head and then
choose acceptance/merge. No coding-agent merge or broader 078 completion claim
is authorized by this report.
