# OAP Execution Report — 078-h

## Identity and delivery

- Order: `078-h-repair-design-scope-and-visual-authority`
- Objective: `078`; round: `078-h`; mode: `AMEND_EXISTING_PR`
- Repository: `slaif-agent-site`
- PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77), open, not merged
- Base: `main`; head branch: `oap/078-agent-composition-design-semantics`
- Starting remote head: `8d956e428c119be037d74cd9d4c7c89beb9ffb83`
- Implementation commit: `7597975cfff30a1f31eab4f4d5871695e3ef7fcb`
- Implementation parent: `8d956e428c119be037d74cd9d4c7c89beb9ffb83`
- Report publication commit: `SELF`
- Pushed implementation commit: `7597975cfff30a1f31eab4f4d5871695e3ef7fcb`
- Result: `COMPLETE` for this bounded continuation; Objective 078 remains open

The committed `oap/active` bytes are exactly `078-h\n`. The committed order
bytes are unchanged from the selected order; their SHA-256 is
`350523c93f33651091b9a2e220f089b6723bca732745e46bb3ea523387737c64`.

## Defects repaired

- Removed the unconditional `component-content-props:write` requirement from
  Agent component PATCH and from the trusted PostgreSQL authority path.
  Content-only, general design, variant, layout, and responsive-map changes
  now require only the exact union derived from changed normalized properties.
- Added exact route-policy property conditions using `props.<name>` paths and
  component-type qualifiers. Generated OpenAPI now has no fixed PATCH scope;
  ordinary `x-slaif-conditional-scopes` identifies scalar triggering scopes,
  while `x-slaif-component-property-scopes` records supported status, scalar
  scopes, responsive-map allowance, and additional responsive scope. Runtime
  OpenAPI validators require both representations to match the route policy
  and shared generated authority.
- Extended the deterministic design authority with existing visual properties:
  `Button.variant` uses `component-variant:write`, `Image.aspectRatio` uses
  `component-props:write`, and `CollectionGrid.columns` uses `layout:write`.
  Existing `Section.background` remains explicitly unsupported and fail-closed.
  Generator drift checks cross-validate all catalog properties and approved
  alignment extensions without changing immutable `catalog-v1` bytes.
- Added trusted renderer, CSS, Puck controls, and round-trip coverage for the
  newly classified Button, Image, and CollectionGrid properties at fixed
  desktop/tablet/mobile labels. Scalar values do not acquire responsive scope;
  responsive maps are normalized and rendered with safe product classes.
- Added a no-effect idempotency completion function and privilege-manifest
  entry. An empty/byte-equivalent PATCH checks the exact row version, returns
  the unchanged record, consumes no mutation quota, and creates no semantic
  audit or COW mutation while retaining exact replay.
- Preserved valid scalar legacy values, content-only L1 updates, COW binding,
  resource restrictions, optimistic concurrency, cancellation rollback,
  idempotency, audit, quota, migration ownership, and 078-a through 078-g
  behavior. No dependency or lockfile change was made.
- Updated `README.md`, `docs/API.md`, `docs/TESTING.md`,
  `oap/MVP-PROGRESS.md`, and `oap/MVP-CONTRACT-AUDIT.md` for the repaired
  local-design slice only. No historical order or report was edited.

## Public PostgreSQL acceptance

The complete affected Agent integration was run serially against disposable
real PostgreSQL with public Agent HTTP and human-issued test capabilities:

- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -q`:
  66 passed in 703.86 seconds.
- The dedicated 078-h test proves design-only scalar PATCH without content or
  responsive scope; responsive design without content and with its additional
  scope; content-only L1 success; mixed Image content/general, Button
  content/variant/responsive, and CollectionGrid content/layout/responsive
  missing-scope denials with unchanged props, versions, quota, idempotency,
  audit, and COW state; L1 denial of all three visual properties; malformed
  custom device maps; and no-effect replay/accounting.
- The same test proves direct `slaif_agent_runtime` helper denial for missing
  variant, responsive, and layout scopes, plus neutral real media/view
  prerequisites without adding media or collection behavior.
- Existing component CRUD, 078-g design discovery, resource, concurrency,
  cancellation, and runtime-helper regressions: 5 passed.
- Control database privilege/migration integration: 4 passed.
- Clean current-head migration downgrade/rebuild: 1 passed.
- 060 component migration round-trip: 1 passed.
- Focused design/OpenAPI/route-policy unit tests: 17 passed.
- Unit projection tests: 5 passed. Direct Web renderer Vitest: 5 passed.
- Composition-schema Puck tests: 11 passed; component-catalog tests: 8 passed.
- Web typecheck and production build passed; Puck round-trip preserves the
  newly classified visual properties exactly.

## Local verification

- `uv lock --check`, `uv sync --frozen --all-groups`: passed.
- Full Python unit suite: 480 passed, one existing Starlette deprecation
  warning; mypy passed 265 source files; Ruff check and format passed for 284
  files.
- Repository policy and repository unittest suite: policy passed; 58 tests
  passed.
- Generated design-system/catalog/OpenAPI drift checks: passed.
- Node `v24.14.1`, pnpm `11.22.0`; frozen install, lint, format check,
  recursive typecheck, full `pnpm test`, standalone `pnpm build`, and license
  inventory passed. The full Node test included workspace, browser-worker,
  Web, Puck, catalog, and contract tests.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: source and wheel
  built successfully.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: 0 issues in 426 files.
- `python tools/check_mermaid.py`: 16 diagrams in 3 files passed; 432 Markdown
  files scanned.
- All ten frozen process `--check` commands returned `CHECK_OK`.
- No fixture database or fixture login roles remained after the serial tests.

## GitHub authoritative state

At final implementation-head inspection, PR #77 was `OPEN`,
`mergeStateStatus=CLEAN`, and head was
`7597975cfff30a1f31eab4f4d5871695e3ef7fcb`. All required checks passed. The
Compose job initially reported only `agent-readiness-timeout` during a
post-restart acceptance poll after every prior Compose/browser check had
passed; the exact failed job was rerun without repository changes and passed.

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
| Compose and edge packaging | pass after exact-job rerun |
| Supply-chain evidence | pass |
| Markdown | pass |
| Mermaid | pass |
| Dependency review | pass |
| Detect supported languages | pass |
| CodeQL | pass |
| Analyze (actions) | pass |
| Analyze (javascript-typescript) | pass |
| Analyze (python) | pass |

No required check was pending, skipped, failed, cancelled, or missing at final
implementation-head inspection.

## Scope, safety, and completion boundary

- No production dependency, lockfile, immutable catalog-v1 bytes, historical
  migration 060, architecture policy, security policy, or acceptance boundary
  was weakened. No real credentials, capabilities, cookies, or locators were
  printed or committed.
- No extra PR was created. PR #77 was not merged or auto-merged.
- Objective 078 remains broader than this round. Site-global theme tokens,
  global regions, header/footer architecture, exact Agent-workspace Puck
  editing, media references, MCP parity, freeze/review, promotion,
  publication, reconstruction, cleanup, backup/restore, and final MVP proof
  remain outside this order.
- This 078-h round is complete only as a bounded execution round after the
  strategic authority reviews this report. Objective 078 / PR #77 can be
  declared complete only when its remaining ordered scope is separately
  satisfied and strategically accepted; the coding agent does not merge it.
