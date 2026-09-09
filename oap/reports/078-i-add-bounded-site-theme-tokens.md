# OAP Execution Report — 078-i

## Identity and delivery

- Order: `078-i-add-bounded-site-theme-tokens`
- Objective: `078`; round: `078-i`; mode: `AMEND_EXISTING_PR`
- Repository: `slaif-agent-site`
- PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77), open, not merged
- Base: `main`; head branch: `oap/078-agent-composition-design-semantics`
- Starting remote head: `8d634a9aca227366c0e65d2785aa241532a6b9d4`
- Implementation commit: `567973e1897ff0ec1cc5017704dd7b914a88d6da`
- Implementation parent: `8d634a9aca227366c0e65d2785aa241532a6b9d4`
- Report publication commit: `SELF`
- Pushed implementation commit: `567973e1897ff0ec1cc5017704dd7b914a88d6da`
- Result: `COMPLETE` for this bounded continuation; Objective 078 remains open

The committed `oap/active` bytes are exactly `078-i\n`. The committed order
bytes are unchanged from the selected order; their SHA-256 is
`bf8d41bfdcd2a600874cbe8c6481d857ec3e0292185d3b0403c303b24286aa21`.

## Implemented bounded slice

- Added the closed, product-owned `theme-schema/v1` authority in
  `packages/composition-schema/src/theme-schema-v1.json`, with an exact Python
  drift check and schema-derived Puck controls. The vocabulary is fixed to an
  AA-validated palette preset, local typography family/scale/weight,
  content-width/spacing/grid-gap, and radius/shadow tokens. It accepts no raw
  CSS, colors, selectors, font URLs/families, breakpoints, device maps, code,
  or executable values.
- Added typed, extra-forbidden Python models for the full theme record,
  schema response, partial group/token request, and typed Agent mutation
  response. Theme records carry a stable ID, immutable site ID, schema and
  renderer versions, positive row version, four normalized groups, and
  timestamps.
- Added append-only migration
  `services/backend/src/slaif_agent_site/db/alembic/versions/062_001_bounded_theme_tokens.py`.
  It safely normalizes valid legacy JSON, rejects malformed existing state
  without silent loss, adds schema/renderer/row-version continuity, replaces
  the lazy-write `STABLE` legacy read with a read-only projection, and keeps
  the legacy Editor wrapper on the same validator. It tears down/rebuilds only
  an empty theme COW table through the foundation public API when required and
  fails closed on pending theme changes.
- Missing new-site defaults are returned by a deterministic, read-only
  product projection with stable site-derived identity; the first real Agent
  or Editor write materializes the projection through the COW view. Reads do
  not insert, charge quota, audit, change timestamps, or create COW state.
- Added Agent `GET /api/agent/v1/theme-schema`, `GET /api/agent/v1/theme`,
  and `PATCH /api/agent/v1/theme`. Reads require `theme:read`; PATCH requires
  `theme-tokens:write`, never accepts `theme-global:write` as a substitute,
  and uses the existing idempotency/COW mutation executor.
- Added a trusted PostgreSQL Agent read/update authority that reasserts
  capability/site/workspace/lifecycle state, exact token schema, row version,
  resource allowlists, mutation quota, and a workspace+site theme advisory
  lock. A successful changed PATCH increments one row version, consumes one
  mutation quota, records one COW operation, completes one idempotency row,
  and emits `THEME_UPDATED / theme / PATCH / 200 / mutation`. Replay, no-op,
  stale, invalid, denied, quota, and cancelled paths leave durable state
  unchanged as applicable.
- Extended bounded theme resource constraints:
  `allowed_theme_palette_presets`,
  `allowed_theme_typography_families`, and `allowed_theme_tokens`.
  Python, the common PostgreSQL constraint projection, and the theme helper
  validate these allowlists against the same fixed vocabulary.
- Updated route policy and regenerated the canonical Agent OpenAPI in both
  directions. Theme schemas and mutation responses are closed and typed; the
  active route inventory now contains the two reads and one PATCH.
- Render now projects the complete typed theme record and version through
  canonical and authorized preview paths. Web applies only fixed
  `renderer-theme-*` classes for palette, typography, layout, and shape; no
  inline style or caller-controlled CSS is introduced. The human Puck surface
  exposes controls generated from the same schema and saves through the
  existing Editor permission/COW boundary.
- Updated only current API/testing/README/MVP ledger documentation. No
  historical order/report, architecture, security policy, dependency, or
  global-region/header/footer/page-style artifact was changed.

## Acceptance and regression evidence

All affected integration was run serially against disposable real PostgreSQL
with the public Agent/Render/Editor boundaries and exact product roles.

- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -q`:
  69 passed in 794.73 seconds. This includes all prior Agent component/design
  behavior and the 078-i migration/theme tests.
- Final focused serial command covering the current worktree:
  `test_agent_062_theme_data_round_trip_preserves_legacy_state`,
  `test_agent_theme_schema_defaults_and_bounded_mutation_are_cow_bound`,
  `test_agent_theme_same_version_race_has_one_cow_winner`, the full Render
  projection integration file, and both human Editor integration files:
  10 passed in 113.62 seconds.
- Theme acceptance proves exact schema/default discovery with read purity;
  all four group updates; stable version/identity; COW workspace projection;
  replay; byte-equivalent no-effect response and accounting; stale version;
  invalid enum; resource narrowing; `theme-global:write` substitution denial;
  and a deterministic same-version race with one 200/one 409 and one durable
  effect.
- `uv run --frozen pytest services/backend/tests/integration/test_render_projection_integration.py -q`:
  2 passed in 19.98 seconds before the final focused rerun; the final focused
  command above re-ran both tests after all current-source changes. It proves
  canonical default versus authenticated HUMAN preview theme separation and
  exact projection row/version fields through the Render HTTP surface.
- `uv run --frozen pytest services/backend/tests/integration/test_human_editor_production_http.py services/backend/tests/integration/test_human_editor_workspace.py -q`:
  5 passed in 55.89 seconds; final focused command reran both suites after all
  current-source changes.
- `uv run --frozen pytest services/backend/tests/integration/test_database_bootstrap.py -q`:
  29 passed in 355.43 seconds.
- `uv run --frozen pytest services/backend/tests/integration/test_full_stack_integration.py services/backend/tests/integration/test_render_projection_integration.py services/backend/tests/integration/test_control_database_integration.py -q`:
  13 passed in 59.36 seconds.

## Local verification

- `uv lock --check`: passed.
- `uv sync --frozen --all-groups`: passed.
- Full Python Ruff check and format check: passed; mypy passed with no issues
  in 267 source files.
- `uv run --frozen pytest services/backend/tests/unit -q`: 481 passed, one
  existing Starlette deprecation warning.
- `python tools/check_repository.py`: repository policy passed.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: 58 passed.
- `uv run --frozen python tools/generate_theme_schema.py --check`: passed.
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`:
  passed.
- `node --version`: `v24.14.1`; `pnpm --version`: `11.22.0`.
- Frozen pnpm install, `pnpm lint`, `pnpm format:check`, `pnpm typecheck`,
  `pnpm test`, standalone `pnpm build`, and `pnpm licenses list --json`:
  passed. The full Node test includes the recursive workspace/browser suites
  plus the root contract tests; the production Web build completed
  successfully.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-078-i`: source and
  wheel built successfully.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: 0 issues in 428 files.
- `python tools/check_mermaid.py`: 16 diagrams in 3 files passed; 434 Markdown
  files scanned.
- All ten frozen backend process `--check` commands returned `CHECK_OK` when
  run through `uv run --frozen`.
- No fixture databases, fixture roles, staging files, real credentials,
  capabilities, cookies, or database locators were committed or printed.

## GitHub authoritative state

At final implementation-head inspection, PR #77 was `OPEN`,
`mergeStateStatus=CLEAN`, and head was
`567973e1897ff0ec1cc5017704dd7b914a88d6da`. The complete required current-head
set was green: 20 successful, 0 pending, 0 skipped, 0 cancelled, and 0
failing. This includes CodeQL actions/JavaScript/Python, Compose and edge
packaging, dependency review, supported-language detection, PostgreSQL 14,
15, 16, 17, and 18, Markdown, Mermaid, Node contracts, Python 3.12/3.13/3.14
quality and package, repository policy, and supply-chain evidence.

## Scope and completion boundary

- No extra PR was created. PR #77 was not merged or auto-merged.
- No production dependency or lockfile changed. Product roles, COW
  hardening, PUBLIC revocation, foundation public-API boundaries, and the
  078-a through 078-h component/design behavior remain preserved.
- This round does not implement global regions, header/footer architecture,
  page style, missing catalog breadth, media bytes/references, MCP parity,
  exact Agent-workspace Puck editing, freeze/review, promotion, publication,
  source reconstruction, cleanup, backup/restore, or a final MVP/release
  claim.
- Objective 078 / PR #77 can be declared complete only after all remaining
  ordered 078 scope is separately implemented, verified through its required
  public boundaries, reviewed and accepted by strategy, and merged by the
  strategic authority. The coding agent does not merge the PR.
