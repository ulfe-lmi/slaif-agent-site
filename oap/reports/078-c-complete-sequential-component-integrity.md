# OAP Coding-Agent Report — 078-c

## Work order

- Identifier: `078-c`
- Work-order file: `oap/orders/078-c-complete-sequential-component-integrity.md`
- Work-order SHA-256: `4cf75182295b07f293928b29147b831d263d9b6da9c24c0af9b7f7d95f0d8694`
- `oap/active` bytes: `078-c\n`
- `oap/active` SHA-256: `2c7e1fb828187b295169c6f450fd4dbe413e18330d6bc48b63c4c110ded6c427`
- Numeric objective: `078` (this report completes only the activated `078-c` round)
- PR mode: `AMEND_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Completed the sequential component-integrity layer on the existing Objective
078 PR. The production Web renderer is now exercised behaviorally through
React static markup, and canonical RichText, Statistics, Timeline, and FAQ
fixtures round-trip through the production Puck adapter while preserving IDs,
hierarchy, slots, order, schema version, and props. Markup-like text is escaped
as text and malformed nested/executable values are rejected before rendering.

The trusted PostgreSQL component functions now compute semantic destinations
after excluding the moving row, so forward and backward anchor moves produce
the exact requested order. Create, move, and delete resequencing advances only
rows whose durable order/parent/slot changed, including timestamps and positive
row versions. An already-satisfied move is a documented deliberate versioned
no-op with one normal quota/audit event; replay through the same idempotency key
returns the original response without another mutation.

Component page limits are distinct: `max_components_per_page` is page-local,
while `max_visible_components` counts components across all pages accessible to
the capability. Move depth checks now include the deepest descendant of an
existing subtree and the architecture hard maximum. Denied cross-page/deep
resource operations leave component rows, versions, quotas, idempotency, audit,
and COW operation state unchanged.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77) — `OPEN`
- Base/head branches: `main` / `oap/078-agent-composition-design-semantics`
- Required starting remote SHA: `1f6aea32338218f57c6324c9f94f9cab8ac8fb29`
- Base remote SHA: `ae3a4a681bb888260192b7bb1b2a337b4906828d`
- Implementation head SHA: `bdfa80e091bcc01f52209044ec94f68d6fff9ebd`
- Implementation commit pushed: `bdfa80e`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal verified from GitHub after publication)
- New PR this round: NO; existing PR amended: YES
- Merge or auto-merge performed: NO

## Changes made

- Added `apps/web/tests/renderer-behavior.test.ts`, which executes the real
  `renderComponent` React boundary with `renderToStaticMarkup`, checks visible
  semantic tags/text for all four structured catalog fixtures, verifies safe
  escaping, and proves malformed nested data is rejected by production Puck.
- Added the permitted root contract wrapper
  `tests/contracts/renderer-behavior.test.ts`; the deployment workspace
  manifest remains byte-for-byte policy-compliant and no dependency was added.
- Added `content.slaif_agent_component_reposition` to compute final positions
  from the remaining sibling sequence and update only changed rows with
  `row_version + 1` and `updated_at = now()`.
- Added `content.slaif_agent_component_resequence` for post-delete dense
  ordering with the same changed-row version/timestamp discipline.
- Reworked component create/move/delete to use those helpers, resolve anchors
  after logical removal, handle append and same-position moves deterministically,
  validate the complete moving subtree depth, and keep invalid operations before
  quota consumption.
- Changed visible-component creation checks to count all accessible pages while
  retaining a separate destination-page limit; component listing no longer
  misuses `max_visible_components` as a per-page limit.
- Added real PostgreSQL Agent HTTP proofs for every required ordering intent,
  create-before-anchor and delete rebalance versions/timestamps, no-op replay,
  cross-parent/cross-slot moves, cross-page visible limits, foreign/inaccessible
  exclusion, deepest-subtree depth denial, and unchanged durable state.
- Preserved 078-b catalog-v1 authority/hash/generator, typed Agent contract,
  deterministic migration snapshot, nested validation, design-prop denial,
  Editor/Puck compatibility, supply-chain policy, and all stated non-goals.

## Files changed

The exact implementation diff from the required starting report head to
`bdfa80e` contains only these paths:

- `apps/web/tests/renderer-behavior.test.ts`
- `oap/active`
- `oap/orders/078-c-complete-sequential-component-integrity.md`
- `services/backend/src/slaif_agent_site/db/alembic/versions/060_001_agent_component_semantics.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `tests/contracts/renderer-behavior.test.ts`

## Acceptance-criteria evidence

### Executable catalog-to-Puck-to-Web parity

- PASS — The real production Puck adapter round-trips catalog-valid RichText,
  Statistics, Timeline, and FAQ fixtures with exact normalized identity,
  hierarchy, slot, order, schema version, and props preservation.
- PASS — The real production React renderer is executed through
  `renderToStaticMarkup`; RichText emits visible paragraph/strong markup,
  Statistics emits `dt`/`dd`, Timeline emits heading/paragraph, and FAQ emits
  summary/answer content.
- PASS — Markup-like fixture text is escaped (`&lt;b&gt;...`) and no raw
  script/style/markup element is emitted.
- PASS — Unknown nested keys, missing structured fields, wrong shapes, and
  `vbscript:` executable content are rejected by Puck before rendering.
- PASS — Python/PostgreSQL acceptance remains covered by the existing canonical
  nested-schema tests, while the executable Puck/Web test uses those same
  catalog-defined shapes.

### Exact semantic ordering

- PASS — Public Agent HTTP proves `[A,B,C]` intent for A-before-C, A-after-B,
  C-before-A, C-after-A, adjacent forward/backward moves, append, and an
  already-satisfied same-position move; every result has exact IDs and dense
  `0..n-1` order keys.
- PASS — Public Agent HTTP proves cross-parent move and cross-slot moves into
  Columns `col-1` and `col-2`, including exact source/destination sequences.
- PASS — Create-before-anchor inserts at the requested semantic position;
  delete rebalancing closes the gap without leaving duplicates.
- PASS — Both anchors remain mutually exclusive and confined to the same
  site/page/parent/slot; cycle and invalid-parent behavior remains fail-closed.
- PASS — Same-position no-op behavior is deterministic: the requested row
  advances one version and receives one normal mutation/audit event; replay
  returns the original response and leaves durable state unchanged on replay.

### Row-version truth and durable atomicity

- PASS — Affected sibling rows advance positive row versions and timestamps on
  create, move, and delete rebalancing; unchanged rows retain their versions
  and creation timestamps.
- PASS — Public Agent list responses expose the resulting versions and dense
  order consistently after each tested operation.
- PASS — Idempotency replay returns the originating stored response without a
  second component/version/quota/audit/COW change.
- PASS — Each requested structural action produces one semantic audit event;
  deterministic sibling rebalance does not create misleading user actions.

### Distinct resource and depth bounds

- PASS — `max_components_per_page` is evaluated against the destination page.
- PASS — `max_visible_components` is evaluated across all pages accessible to
  the capability; two accessible pages consume one shared budget rather than
  resetting the limit per page.
- PASS — Foreign-site and inaccessible-page components are excluded from the
  visible count and cannot influence the Agent’s allowed budget.
- PASS — Existing subtree moves are checked using destination parent depth plus
  the deepest descendant height, with the architecture hard maximum enforced.
- PASS — Denied visible-limit and deep-subtree operations leave tree rows,
  row versions, mutation/delete quotas, idempotency, audit, and COW operation
  state unchanged.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED — 44 packages checked.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED — 531 passed, 1 warning, 22.89s.
- Focused catalog/API/DB/Render/legacy suite: PASSED — 43 passed, 1 warning, 120.75s.
- Focused ordering/resource suite: PASSED — 4 passed, 44.15s.
- Focused cross-parent/cross-slot suite: PASSED — 1 passed, 12.01s.
- Focused executable Web/Puck renderer test: PASSED — 3 tests.
- `uv run --frozen ruff check services/backend tools tests/repository`: PASSED.
- `uv run --frozen ruff format --check services/backend tools tests/repository`: PASSED — 280 files formatted.
- `uv run --frozen mypy`: PASSED — 262 source files.
- `uv run --frozen python -m tools.generate_component_catalog --check`: PASSED.
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`: PASSED.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 58 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; 422 Markdown files scanned.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues in 416 files.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED — all 10 workspace projects.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — all workspace package tests, web tests, browser-worker
  tests, and 3 root contract files/7 root contract tests; the new executable
  renderer test contributed 3 tests.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `git diff --check`: PASSED.

The full multi-hour local backend integration suite was intentionally not
rerun: the activated order explicitly requires focused sequential PostgreSQL
proofs and says not to use a full integration rerun as their substitute. The
normal current-head PostgreSQL CI matrix below supplied broad qualification.
No focused required gate was skipped or left pending at implementation-head
drafting.

## GitHub CI / required checks

Observed for implementation head
`bdfa80e091bcc01f52209044ec94f68d6fff9ebd` on PR #77; all current-head
checks were terminal and green before report publication:

- Analyze (actions): SUCCESS
- Analyze (javascript-typescript): SUCCESS
- Analyze (python): SUCCESS
- CodeQL: SUCCESS
- Compose and edge packaging: SUCCESS
- Dependency review: SUCCESS
- Detect supported languages: SUCCESS
- Foundation PostgreSQL 14: SUCCESS
- Foundation PostgreSQL 15: SUCCESS
- Foundation PostgreSQL 16: SUCCESS
- Foundation PostgreSQL 17: SUCCESS
- Foundation PostgreSQL 18: SUCCESS
- Markdown: SUCCESS
- Mermaid: SUCCESS
- Node contracts: SUCCESS
- Python 3.12 quality and package: SUCCESS
- Python 3.13 quality and package: SUCCESS
- Python 3.14 quality and package: SUCCESS
- Repository policy: SUCCESS
- Supply-chain evidence: SUCCESS

- All required current-head checks green at implementation drafting: YES.
- A report-only commit may cause a fresh CI run; per protocol no post-report
  check wait or repository mutation is performed.

## Local setup / dependencies

- Used exact uv 0.12.5, disposable local PostgreSQL, Node 24.14.1, and pnpm
  11.22.0.
- No production dependency, lockfile, hosted service, image, or architecture
  exception was added.
- No production system, credential, capability, cookie, or private artifact was
  accessed or printed.

## Documentation

- Added durable executable renderer and sequential-integrity test evidence.
- No architecture, constitution, protocol, prior order, or prior report was
  edited.

## Safety and scope confirmations

- Unrelated files changed: NO.
- New or extra PR: NO.
- Coding-agent merge or auto-merge: NO.
- Activated order/active content edited after selection: NO; strategy-authored
  bytes were committed unchanged.
- New dependency or hosted service: NO.
- Production secrets/systems accessed: NO.
- Test/Markdown/security policy weakened: NO.
- Report-publication commit changes only this report: YES.

## Known limitations / blockers

- This report completes only `078-c`; numeric Objective 078 remains open and
  PR #77 remains `OPEN` for strategic acceptance.
- The five concurrent component race cases are explicitly the next dependency-
  correct round and are not implemented here.
- Full clean Compose/NGINX/browser/restart/isolation acceptance remains later
  work, despite the CI packaging check passing.
- New catalog breadth, theme/design-system/global-region work, media bytes,
  MCP, freeze/review/promotion, site reset, and release claims remain outside
  this order.

The strongest reason not to accept numeric Objective 078 yet is that the
required concurrency proof and the broader end-to-end isolation/browser
acceptance scenario remain unimplemented by explicit order, not because this
sequential-integrity round lacks passing evidence.

## Completion condition

This coding round is complete when this report-only `SELF` commit is pushed as
the direct child of implementation SHA `bdfa80e`, verified as the sole changed
path and the remote PR #77 head, and the exact FIFO response `OK` is sent.
Objective 078 is not accepted or merged by this agent; strategy retains sole
authority to review, accept, and merge.
