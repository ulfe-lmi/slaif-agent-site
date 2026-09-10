# OAP Coding-Agent Report — 078-r

## Work order

- Identifier: `078-r`; work-order file: `oap/orders/078-r-close-theme-render-and-final-evidence.md`
- Numeric objective: 078; increment: 078/2; round: 078-r
- PR mode: `AMEND_EXISTING_PR`
- Exact order SHA-256: `e479161810598d32634d498b3e306a43c871aefcabe78ef9b0c222148ea354eb`
- Active pointer bytes: `078-r\n`; active SHA-256: `db043e4f76e72c42868cfa1ec70d91a3fa3ba2e72455762ac50cb295d2d2f028`

## Status

COMPLETE

This completes the bounded 078/2 site-theme increment only. Numeric Objective
078 remains `PARTIAL`; global regions, page style, catalog expansion, and later
review/publication work remain outside this order.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#79](https://github.com/ulfe-lmi/slaif-agent-site/pull/79), `OPEN`
- Base/head: `main` / `oap/078-2-site-theme-tokens`
- Starting remote SHA: `ce255470e76d4639d436d4ace6b19a8cd858c0d1`
- Literal implementation SHA: `9d9e6470efb69e4e410191be026666d94ef323d3`
- Implementation commit parent: `ce255470e76d4639d436d4ace6b19a8cd858c0d1`
- Report publication commit: `SELF`
- Report-only commit parent: the literal implementation SHA above
- Remote PR head before report publication: `9d9e6470efb69e4e410191be026666d94ef323d3`
- `CREATED_NEW_PR`: NO; `AMENDED_EXISTING_PR`: YES; extra PR: NO
- Merge or auto-merge: NO

The implementation commit changes 15 paths relative to the starting PR head,
with `899` insertions and `211` deletions. The groups are two runtime/migration
paths, five verification paths, six durable documentation/truth paths, and two
OAP transcript paths. No generated contract file or dependency lock changed.

## Exact changes

- The 065 theme mutation now acquires the pure workspace lifecycle advisory
  lock `280`, then theme lock `995`, before invoking the capability helper’s
  row-locking and scope checks. Public and direct-runtime barriers prove that a
  mutation waiting on lifecycle does not hold or wait on a granted theme lock.
- Theme race proof now gates first and second arrivals separately, exercises both
  arrival orderings, selects changed values from the actual winner’s remaining
  presets, and cancels a genuinely changing request without residue.
- Migration 065 now moves both replaced idempotency completion functions into
  its private legacy schema and restores the original objects on downgrade,
  alongside the three previously preserved legacy functions.
- The migration proof captures a fresh 064 baseline before 065 is applied and
  compares function definition, signature, owner, ACL, volatility, and the
  semantic audit constraint after restoration, while preserving valid data.
- Renderer CSS uses fixed root-scoped semantic roles and low-specificity theme
  defaults. Explicit local and responsive gap/button variants retain meaning;
  palette foreground/background roles are computed for ocean, meadow, and
  ember. The generic renderer link selector no longer overrides button roles.
- Browser proof asserts actual computed palette, typography, width, spacing,
  gap, radius/shadow, reset, local precedence, responsive precedence, and
  numeric AA contrast for primary, secondary, and ghost roles.
- Public acceptance now sends the real human-issued Agent capability’s theme
  PATCH through the same workspace’s authorized NGINX Render/browser-worker
  path, validates private screenshot/summary artifacts, and verifies Agent
  restart plus exact idempotent replay retain the theme/version.
- Compose artifact counts were updated for the four additional same-workspace
  browser artifacts. Current API, testing, README, MVP, increment, and PR
  description truth were reconciled without editing historical q artifacts.

## Acceptance evidence

### Lifecycle ordering, races, and cancellation

- Focused test `test_theme_mutation_waits_on_lifecycle_before_theme_for_public_and_runtime`
  passed for both public HTTP and direct runtime calls.
- Focused test `test_theme_races_use_database_barrier_and_cancel_without_residue`
  passed with exact two-waiter barriers, reversed arrival order, one `200`, one
  `409`, one durable effect per race, stale-version behavior, and unchanged
  cancellation accounting.
- The prior passing 078-q implementation was not reimplemented or broadened.

### Exact migration restoration

- `test_agent_065_theme_data_round_trip_preserves_legacy_state` passed from a
  fresh migration state upgraded to 064, captured before 065, upgraded through
  065, and downgraded back to 064.
- The five replaced functions and `audit.agent_mutation_semantic_shape` were
  restored exactly by the contract tuple comparison; valid legacy theme data
  survived the round trip and private legacy schema isolation remained intact.
- Pending-COW downgrade rejection and no-data-loss proof passed.

### V1 renderer

- The retained CSS reproducer changed from `24px`/green ghost to `0px` desktop,
  `8px` mobile, and transparent ghost background.
- The preview browser test passed computed assertions for all three palettes,
  all three semantic button roles, numeric contrast, configured token groups,
  default reset tokens, and local/responsive precedence.
- The existing human Editor/Puck preview test passed with explicit local grid
  `md` retaining `16px` over a theme `sm` default, while canonical ocean output
  and reset behavior remained isolated.

### V2 same-workspace Agent result

- Clean local Compose `slaif007r4` passed the public Agent acceptance path. The
  real Agent capability PATCHed the theme, then the browser worker rendered the
  same `workspace_id` through public NGINX; the database binding and private
  screenshot/JSON artifact metadata were checked.
- The same acceptance passed exact theme replay after Agent restart and
  readback of the retained row/version. Existing human Editor/Puck controls and
  permissions remained unchanged.
- Canonical and other-workspace/site isolation, no-store/noindex private
  preview behavior, and browser artifact credential negatives passed.

### Firefox diagnosis

- Historical run [34367041990](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34367041990),
  job `102518331881`, retained only the generic
  `responsive-admin-keyboard-read-states-and-logout` `browser-response`
  category at `auth.spec.ts:79`; the archived artifact inventory contained no
  browser trace, response URL, status, or endpoint evidence. The exact failed
  request therefore cannot be reconstructed from GitHub’s retained evidence.
- The same code passed the other five device projects in that historical run,
  passed the clean local Compose matrix, and passed the exact desktop-Firefox
  project in the successful remote Compose rerun. No response suppression,
  weaker assertion, skipped Firefox project, or blind retry policy was added;
  the evidence supports a transient CI/request timing failure rather than a
  reproducible product defect.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED.
- `uv run --frozen mypy`: PASSED; no issues in 271 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED;
  `540 passed`, one existing deprecation warning, `24.37s`.
- Focused migration/lock/race command: PASSED; `2 passed`, `21.65s`.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED;
  `58` tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED; 16 diagrams in 3 files, CLI 11.16.0.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED; 0 issues in 455 files.
- `node --version`: `v24.14.1`; `pnpm --version`: `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `sh tools/compose/smoke.sh slaif007r4`: PASSED; V1/V2 browser evidence,
  desktop Chromium/Firefox/WebKit, tablet, mobile Chromium/WebKit, Agent
  browser projects, restart/outage/recovery, edge/media/secret/artifact/
  privilege checks, Apache validation, and 48 final smoke tests.

The unchanged substrate’s full integration qualification was already green on
the verified 078-q implementation head; this round added and passed the
focused migration/authority/concurrency tests and the required current-head
remote matrix rather than redundantly repeating the 33-minute full local suite.

## GitHub required checks

All required checks are `SUCCESS` on implementation head
`9d9e6470efb69e4e410191be026666d94ef323d3`:

- CI run [34424987610](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34424987610):
  Repository policy job `102761400231`; Dependency review `102761368956`;
  Node contracts `102761369352`; Python 3.12 `102761369510`; Python 3.13
  `102761369647`; Python 3.14 `102761369631`; PostgreSQL 14 `102761389448`;
  PostgreSQL 15 `102761397993`; PostgreSQL 16 `102761390983`; PostgreSQL 17
  `102761369555`; PostgreSQL 18 `102761369749`; Compose/edge
  `102761368167`; supply-chain `102761388535`; Markdown `102761388644`;
  Mermaid `102761398253`.
- CodeQL run [34424987593](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34424987593):
  Detect supported languages `102708213886`; Analyze actions `102708244772`;
  Analyze Python `102708244773`; Analyze JavaScript/TypeScript `102708244910`.
- The first CI attempt failed only because Compose timed out waiting for Agent
  readiness after a restart. Rerunning the failed Compose job without code
  changes produced the successful Compose job above in `10m04s`; all other
  checks remained green.

## Documentation and scope confirmations

- Current `docs/API.md` records `theme:read` for PATCH and conditional
  `theme-tokens:write` only for changed values; no-effect PATCH remains read
  authorized.
- `README.md`, `docs/TESTING.md`, `oap/INCREMENTS.md`,
  `oap/MVP-PROGRESS.md`, `oap/MVP-CONTRACT-AUDIT.md`, and the PR description
  describe 078-r evidence and preserve the global `PARTIAL` boundary.
- Historical 078-p/q orders, reports, and audits were not edited.
- No dependency, architecture, constitution, security policy, production
  credential, external secret, publication, lifecycle, freeze/review,
  global-region, page-style/catalog, media/MCP, exact-workspace Puck, or
  unrelated cleanup scope was added.
- No real secret, capability, cookie, DB URL, private preview credential, or
  artifact URL was committed or printed.
- No merge or auto-merge was performed. Objective 078-r is complete only for
  its bounded increment; final acceptance/merge remains strategic authority.

## Completion condition

Objective 078/2 and PR #79 may be declared complete for this bounded increment
when the strategic authority independently accepts this report and merges PR #79
after verifying the remote head remains `9d9e6470efb69e4e410191be026666d94ef323d3`.
The numeric Objective 078 and contractual MVP must remain `PARTIAL` until their
separately ordered global-region/page-style/catalog, review, publication, and
later objective requirements are accepted.
