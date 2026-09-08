# OAP Coding-Agent Report — 077-w

## Work order

- Identifier: `077-w`
- Work-order file: `oap/orders/077-w-repair-render-css-locale-parity.md`
- Numeric objective: `077`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Repaired the remaining renderer parity defect without changing product data
semantics or adding a feature. The renderer stylesheet is now loaded by the
shared trusted rendered surface rather than the global root layout, and its
rules explicitly reset canonical Tailwind preflight differences while preserving
the existing trusted renderer styles. The shared rendered root carries the
exact projection locale; preview retains its exact document locale, while the
canonical root document remains the application-level `en` shell.

The disposable Compose evidence now renders equivalent canonical and workspace
preview fixtures on a separate `parity` site with localized `sl-SI` content,
layout, CollectionList, CollectionGrid and CollectionDetail nodes. Browser
evidence compares actual computed desktop/mobile style values, confirms
stylesheet loading, checks privacy and admin/auth non-regression, and preserves
all prior 077-v evidence. No 078+ behavior was introduced.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), `OPEN`
- Base/head branches: `main` / `oap/077-agent-site-structure-semantics`
- Starting remote report head: `b336ca9dbf1c39ed7fb17f4845743f3bb5f2f8df`
- Implementation head SHA: `6c264b1c876f5467a6b8e57a4f81051fd5e20b18`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (to be derived from GitHub)
- Implementation commit pushed before report: `6c264b1c876f5467a6b8e57a4f81051fd5e20b18`
- New PR this turn: `NO`; amended existing PR: `YES`; merge performed: `NO`

The remote branch had already advanced with the identical 077-w implementation
tree before local publication; the authoritative remote commit above is used as
the implementation head. No force push or duplicate objective PR was created.

## Changes made

- Removed the renderer stylesheet from the global root layout and from the
  preview route head; the shared `renderProjection` output now emits the one
  stylesheet link for actual renderer responses.
- Added `renderer-surface` markup with the exact projection locale and made the
  versioned renderer CSS self-contained: scoped body surface styling, box-model
  and border resets against canonical Tailwind preflight, explicit typography,
  collection card/detail rules, nested layout rules and the existing mobile
  breakpoint.
- Expanded the real Playwright parity evidence to compare page title,
  CollectionList/Grid article and text styles, CollectionDetail, nested Grid,
  stylesheet readiness and locale semantics at desktop and mobile widths.
- Added a disposable `parity` site fixture with equivalent `en`/`sl-SI`
  canonical and preview content and preserved the demo-site namespace for the
  existing public Agent acceptance.
- Updated the durable smoke browser fixture to target the parity workspace/site
  consistently; no product route or browser authorization contract changed.
- Updated source and packaging contract assertions for scoped renderer loading,
  exact language placement and parity fixture routing.

## Files changed

- `apps/web/app/layout.tsx`
- `apps/web/app/preview/[workspaceId]/[[...sitePath]]/route.tsx`
- `apps/web/public/renderer-v1.css`
- `apps/web/src/renderer/components.tsx`
- `apps/web/tests/surface.test.mjs`
- `tests/e2e/preview.spec.ts`
- `tests/packaging/test_compose_smoke_contract.py`
- `tools/compose/e2e.sh`
- `tools/compose/smoke.sh`
- `oap/orders/077-w-repair-render-css-locale-parity.md`
- `oap/active`

## Acceptance-criteria evidence

### Criterion 1 — Self-contained CSS and locale semantics

- The actual shared renderer emits `/renderer-v1.css` once and the root layout
  no longer loads it globally; admin/auth/setup pages therefore retain their
  application stylesheet surface.
- The canonical and preview `renderer-surface` roots carry their exact
  projection locale. The clean Compose browser proof passed canonical and
  preview `sl-SI` routes with localized page/item content; preview document
  language was `sl-SI`, and canonical content-root language was `sl-SI`.
- Canonical and preview both use the same trusted `renderProjection` component
  implementation and the same versioned stylesheet. No CSP relaxation,
  `unsafe-inline`, identifier-negative relaxation, or new dependency was used.

### Criterion 2 — Computed canonical/preview parity

- The clean Compose/NGINX/Web Playwright proof compared actual computed values
  and classes for the page `h1`, nested layout Grid, CollectionList article/
  `h2`/summary, CollectionGrid article/`h2`/summary and CollectionDetail.
- Desktop evidence used the same 1440x900 viewport; mobile evidence used the
  same 390x800 viewport. All canonical/preview evidence objects matched,
  including box sizing, borders, backgrounds, padding, typography, line-height,
  grid layout and mobile single-column behavior.
- The confined browser observed a loaded stylesheet (`link.sheet` present), and
  the renderer stylesheet request remained same-origin and allowlisted.

### Criterion 3 — Privacy and non-regression

- Canonical and preview response-body checks passed with no internal UUID,
  capability/credential or Next Flight metadata leakage; preview remained
  private, no-store, noindex and CSP-compatible.
- Existing redirect/status/query, restart, public Agent dynamic rendering,
  browser evidence, artifact retention/denial, COW isolation and outage
  behavior passed in the clean smoke.
- Actual `/admin` and `/login` browser pages passed with zero renderer
  stylesheet links and no renderer surface.

### Criterion 4 — Scope and continuity

- No SQL, migration, OpenAPI, dynamic data, browser retention/auth,
  dependency/image, architecture or 078+ feature change was made.
- Chrome `152.0.7977.82`, empty vulnerability exceptions and issue #67 were
  preserved. The complete current-head CI matrix passed.

## Local verification

- `node --test apps/web/tests/surface.test.mjs services/browser-worker/tests/contracts.test.mjs`: **PASSED** — 14 tests.
- `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`, `pnpm build`, and the approved `pnpm licenses list --json` inventory: **PASSED** at Node `v24.14.1` / pnpm `11.22.0`.
- `uv lock --check`, frozen sync, Ruff check/format, mypy, unit/repository
  tests and package build: **PASSED** — 522 unit/repository tests; wheel and
  sdist built.
- `uv run --frozen pytest -q services/backend/tests/integration/test_render_browser_preview.py services/backend/tests/integration/test_render_projection_integration.py`: **PASSED** — 4 tests in 38.11s.
- `uv run --frozen pytest services/backend/tests/integration`: **PASSED** —
  173 tests in 1504.27s (25:04); no backend product source changed in 077-w.
- Repository policy suites: **PASSED** — repository 58, packaging 48 and
  supply-chain 34 tests; `python tools/check_repository.py` passed.
- `python tools/check_mermaid.py`: **PASSED** — 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: **PASSED** — 0 issues in
  405 files.
- `sh tools/compose/smoke.sh slaif007wdbg5`: **PASSED** on the final clean
  run. `compose-e2e` passed 11 projects, including the new computed parity and
  localized fixture; public Agent acceptance, browser artifact durability,
  recovery, edge, security, Apache and 48 packaging contract tests passed.
- `sh tools/supply_chain/run.sh /tmp/slaif-077-w-supply-1788814514671805722`:
  **PASSED** — 6 images, 0 critical vulnerabilities, 42 high findings and
  checksum evidence passed.

Earlier diagnostic attempts were not treated as passes: the first parity test
failed because its two desktop captures used different viewport widths; a
manual reproduction initially lacked the smoke harness OIDC fixtures; two
clean-smoke attempts then exposed fixture namespace/site-binding collisions.
Those were corrected within this order, and the final clean smoke above passed
from a fresh disposable deployment.

## GitHub CI / required checks

Observed for implementation head `6c264b1c876f5467a6b8e57a4f81051fd5e20b18`:
all current checks are `pass`; none is pending, missing, cancelled or failed.

- CI run `34150509551`: Repository policy; Node contracts; Python 3.12,
  3.13 and 3.14 quality/package; Foundation PostgreSQL 14, 15, 16, 17 and
  18; Compose and edge packaging; Supply-chain evidence; Markdown; Mermaid;
  Dependency review.
- CodeQL run `34150509564`: Detect supported languages; Analyze (actions);
  Analyze (javascript-typescript); Analyze (python); CodeQL.

The first remote Compose attempt failed, with no failure log available through
the CLI; the exact failed job was rerun in place. Its rerun job
`101868741466` completed successfully in 9m55s. The final remote check state
above is authoritative and green.

## Local setup / dependencies

- Used the repository’s frozen uv `0.12.5` environment, Node `24.14.1`, pnpm
  `11.22.0`, disposable local PostgreSQL/Compose and pinned Playwright.
- No dependency, lockfile, image, production secret or production system was
  accessed or changed. Test credentials and site fixtures were fake and
  disposable.

## Documentation

- The executable renderer and OAP transcript are self-documenting through the
  versioned stylesheet comment, source/Playwright/Compose assertions, exact
  order and report. No broader product or architecture documentation changed.

## Safety and scope confirmations

- Unrelated files changed: **NO**; all 11 paths are required by `077-w`, its
  executable evidence, or the exact OAP transcript.
- Production secrets accessed: **NO**. Production systems accessed: **NO**.
- Required tests skipped/not run: **NO**. The five-version PostgreSQL matrix
  and all current remote checks ran in GitHub CI; local integration used the
  repository’s disposable configured database.
- Scope deviation: **NO**; no product behavior, dependency, route, migration,
  architecture or later-objective work was added.
- Extra objective PR: **NO**. Coding-agent merge: **NO**.
- Activated order/active edited: **NO**; strategy-authored bytes were committed
  unchanged.
- Report commit changes only this new report: **YES**.

## Known limitations / blockers

- No technical blocker remains for 077-w. PR #74 is still `OPEN`; strategy
  must independently review the cumulative Objective-077 transcript, evidence,
  scope and acceptance before deciding whether to accept and merge. The coding
  agent does not merge OAP PRs.

## Recommended strategic follow-up

Perform the independent hostile audit of the cumulative 077 rounds and this
report. If satisfied, strategy may accept and merge PR #74; no additional
implementation is indicated by this continuation.
