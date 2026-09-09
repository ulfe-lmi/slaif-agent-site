# OAP Execution Report — 078-g

## Identity and delivery

- Order: `078-g-add-bounded-component-design-semantics`
- Objective: `078`; round: `078-g`; mode: `AMEND_EXISTING_PR`
- Repository: `slaif-agent-site`
- PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77), open, not merged
- Base: `main`; head branch: `oap/078-agent-composition-design-semantics`
- Starting remote head: `7d64b72c2732b08d2222e3e5b9a49a3b33c8a565`
- Implementation commits: `9e45c38869eb352df7b3b753fd04b11f72b49179`, then
  the in-scope acceptance repair `dc5e2b863dc786445fd05a80c3029edef37d8b7e`
- Implementation parent: `9e45c38869eb352df7b3b753fd04b11f72b49179`
- Report publication commit: `SELF`
- Pushed implementation commits: `9e45c38869eb352df7b3b753fd04b11f72b49179`,
  `dc5e2b863dc786445fd05a80c3029edef37d8b7e`
- Result: `COMPLETE` for this bounded continuation; Objective 078 remains open

The committed `oap/active` bytes are exactly `078-g\n`. The committed order
bytes are unchanged from the selected order; their SHA-256 is
`f74a4d7eab71a7c77121e331fab00f6993e17ff1312e698d5e5720d673cdca1b`.

## Exact bounded changes

- Added the deterministic product-owned `design-system/v1` authority, bound to
  immutable `catalog-v1`, `site-composition/v1`, and `renderer-v1`. All 22
  catalog components are enumerated; only the seven currently supported local
  design components expose properties, and the remaining components explicitly
  expose empty design descriptors.
- Exposed `GET /api/agent/v1/design-system` with a typed closed response and
  `theme:read` capability policy. The authority contains only fixed
  desktop/tablet/mobile labels, bounded design tokens, variants, property
  types/defaults/requiredness/responsiveness, and property scopes. The
  component PATCH OpenAPI operation also publishes the generated exact
  property-level scope table in `x-slaif-component-design-scopes`.
- Extended the existing component PATCH boundary for bounded variant, layout,
  alignment, width, columns, gap, direction, spacer, and responsive values.
  The server and trusted PostgreSQL helper derive scopes from actual changed
  properties; mixed changes require the union. Responsive maps normalize to
  desktop/tablet/mobile order and use deterministic fallback. Caller labels,
  raw CSS/classes/selectors/styles, breakpoints, URLs, fonts, colors, HTML,
  code, and executable values are not accepted or exposed.
- Added append-only migration `061_001_agent_component_design_semantics` with
  trusted scope/resource authorization and complete merged-props validation at
  the database boundary. It preserves catalog-v1 and migration 060 bytes,
  preserves legacy compositions, and has a downgrade path restoring the prior
  component functions.
- Applied the same bounded design contract to Puck configuration, the trusted
  Render projection, Web component rendering, and safe responsive CSS. No new
  dependency or lockfile change was made.
- Updated the public Agent acceptance helper’s inherited design negative from
  the old 078-f `422 DOMAIN_VALIDATION_FAILED` expectation to the correct
  078-g `403 AUTHORIZATION_DENIED` result for its L2 capability. Its unchanged
  state assertion remains in place.
- Updated `README.md`, `docs/API.md`, `docs/TESTING.md`,
  `oap/MVP-PROGRESS.md`, and `oap/MVP-CONTRACT-AUDIT.md` only for this bounded
  local-design slice; site-global theme, global regions, header/footer,
  review, promotion, and publication remain partial or unimplemented.
- Committed the exact selected order and active pointer with the implementation;
  no historical order or report was edited.

## Acceptance evidence

- Public Agent HTTP against real disposable PostgreSQL fetched the exact typed
  design-system document, created representative Section/Container/Grid/
  Heading nodes, changed variant/width/columns/gap/alignment and all fixed
  responsive labels, and observed the same normalized records through exact
  reads and lists.
- The public integration proved mixed content-plus-design PATCH, L1 content
  success with design denial, L2 design denial, missing conditional scopes,
  direct runtime-helper denial, invalid responsive input, resource constraints,
  post-design structural create/move, Puck round-trip validation, and
  cancellation with unchanged props/version/quota/idempotency/audit/COW state.
- A deterministic PostgreSQL barrier proved two concurrent design PATCHes with
  one expected version produce exactly one `200` winner and one `409` loser;
  the winning row has one new version.
- Unit and Web renderer tests prove safe responsive classes/values for logical
  desktop/tablet/mobile rendering. The focused Render projection test accepts
  only bounded responsive maps and rejects malformed typed leaves.
- The final clean Compose/edge CI smoke passed, including the public Agent
  acceptance, all stable browser projects, topology/edge checks, and the
  inherited component loop. The stale inherited design expectation was the
  only initial remote failure; it was corrected in the second implementation
  commit and the fresh run passed.

## Local verification

- `uv lock --check`: passed.
- `uv sync --frozen --all-groups`: passed.
- `uv run --frozen ruff check services/backend tests/repository tools`: passed.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  passed; 284 files formatted.
- `uv run --frozen mypy`: passed; 265 source files.
- `uv run --frozen pytest services/backend/tests/unit -q`: 480 passed, one
  existing Starlette deprecation warning.
- `uv run --frozen pytest tests/repository -q`: 58 passed, 26 subtests passed.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: 58 passed.
- Full affected Agent integration:
  `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -q`:
  65 passed in 683.09 seconds.
- Focused final design integration:
  4 passed in 46.23 seconds.
- Affected control migration integration: 4 passed in 38.84 seconds.
- Affected bootstrap integration: 29 passed in 349.74 seconds.
- Affected editable-domain/session integration: 8 passed in 75.61 seconds.
- Affected Editor/Render integration: 7 passed in 76.98 seconds.
- Focused design/OpenAPI/policy/projection unit regressions: 33 passed.
- `python tools/check_repository.py`: `PASS repository policy`.
- `python tools/check_mermaid.py`: 16 diagrams in 3 files passed; 430 Markdown
  files scanned.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: 0 issues in 424 files.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: source distribution
  and wheel built successfully.
- Node `v24.14.1`, pnpm `11.22.0`; frozen install, lint, format check,
  recursive typecheck, full `pnpm test`, standalone `pnpm build`, and license
  inventory all passed. The full Node test command included the production
  Web build, all workspace tests, browser-worker tests, and contract tests.
- All ten frozen process `--check` smoke commands returned `CHECK_OK`.
- Generated design authority, catalog drift, and Agent OpenAPI checks passed.

## GitHub authoritative state

At final implementation-head inspection, PR #77 was `OPEN`,
`mergeStateStatus=CLEAN`, and head was
`dc5e2b863dc786445fd05a80c3029edef37d8b7e`. The fresh CI/CodeQL run for that
head had no pending, skipped, failed, cancelled, or missing required check:

| Check | State |
| --- | --- |
| Repository policy | pass |
| Node contracts | pass |
| Python 3.12 quality and package | pass |
| Python 3.13 quality and package | pass |
| Python 3.14 quality and package | pass |
| Foundation PostgreSQL 14 | pass |
| Foundation PostgreSQL 15 | pass |
| Foundation PostgreSQL 16 | pass |
| Foundation PostgreSQL 17 | pass |
| Foundation PostgreSQL 18 | pass |
| Compose and edge packaging | pass |
| Supply-chain evidence | pass |
| Markdown | pass |
| Mermaid | pass |
| Dependency review | pass |
| Detect supported languages | pass |
| CodeQL | pass |
| Analyze (actions) | pass |
| Analyze (javascript-typescript) | pass |
| Analyze (python) | pass |

## Scope, safety, and completion boundary

- No production dependency, lockfile, catalog-v1 bytes, historical migration
  060, architecture policy, security policy, or acceptance boundary was
  weakened. No production credentials, capabilities, cookies, or locators were
  printed or committed.
- No extra PR was created. PR #77 was not merged or auto-merged.
- Objective 078 is not a complete product objective yet. Site-global theme
  tokens, global regions, header/footer architecture, exact Agent-workspace
  Puck editing, media references, MCP parity, freeze/review, promotion,
  publication, reconstruction, cleanup, backup/restore, and final MVP proof
  remain outside this order.
- This bounded 078-g round can be declared complete only after the strategic
  authority independently accepts this report and decides that the open PR is
  ready for its separate merge decision. The coding agent does not merge it.
