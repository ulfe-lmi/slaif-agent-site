# OAP Coding-Agent Report — 077-v

## Work order

- Identifier: `077-v`
- Work-order file: `oap/orders/077-v-repair-preview-parity-evidence.md`
- Numeric objective: `077`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Restored the same versioned renderer stylesheet on canonical and preview SSR,
made preview HTML use the selected locale and page-derived title, and added
privacy/CSS/renderer-parity assertions. Replaced broad browser-artifact cleanup
with capability-bound public list/retrieve evidence, binding and denial checks,
and retained audit/artifact assertions. Added real localized fallback,
deterministic preview/browser cancellation, one-use browser authorization, and
dynamic preview-versus-Agent mutation race evidence. The substantive 077-u
implementation remains intact; no new Objective-077 feature area was added.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), `OPEN`
- Base/head branches: `main` / `oap/077-agent-site-structure-semantics`
- Starting remote SHA: `6891cf26f7ff5d498fe5561ccfae3ea13826d101`
- Implementation head SHA: `217641d6cf546f4ec1175bad7dd93e6b02189a95`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (to be derived from GitHub)
- Implementation commit pushed before report: `217641d6cf546f4ec1175bad7dd93e6b02189a95`
- Report parent must equal the implementation SHA above; new PR this turn: `NO`
- Amended existing PR: `YES`; merge performed: `NO`

## Changes made

- Added `apps/web/public/renderer-v1.css` and shared `RENDERER_STYLESHEET`
  constant; canonical and preview consume the same renderer CSS.
- Added preview `lang`, bounded page title, stylesheet delivery, and preserved
  server-rendered private/no-store/noindex/no-Flight behavior.
- Added computed-style, stylesheet, locale, title, localized-content, class
  parity, and UUID/credential/Flight leakage checks in Web/Playwright/Compose
  evidence.
- Extended browser evidence with stylesheet/lang/detail computed-style summary.
- Allowed only the bounded same-origin renderer stylesheet in browser policy.
- Changed dynamic public acceptance to retrieve exact capability-bound artifacts,
  verify digests/metadata/evidence/binding/denials/replay and retained events,
  prove selected-locale fallback/fail-closed behavior, and remove audit/filesystem
  deletion cleanup.
- Added deterministic PostgreSQL preview cancellation and Agent mutation race
  assertions, including connection/context reuse and durable idempotency/audit/
  quota state.
- Updated the smoke contract test for the baseline-aware retained artifact
  count; this was the only corrective change after the first smoke attempt.
- Committed the exact strategy-authored `oap/orders/077-v...md` and `oap/active`
  bytes unchanged.

## Files changed

- `apps/web/app/layout.tsx`
- `apps/web/app/preview/[workspaceId]/[[...sitePath]]/route.tsx`
- `apps/web/next.config.mjs`
- `apps/web/public/renderer-v1.css`
- `apps/web/src/renderer/styles.ts`
- `apps/web/tests/surface.test.mjs`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_render_browser_preview.py`
- `services/browser-worker/src/evidence.ts`
- `services/browser-worker/src/url-policy.ts`
- `services/browser-worker/tests/contracts.test.mjs`
- `tests/e2e/preview.spec.ts`
- `tests/packaging/test_compose_smoke_contract.py`
- `tools/compose/public_agent_acceptance.py`
- `tools/compose/smoke.sh`
- `oap/orders/077-v-repair-preview-parity-evidence.md`
- `oap/active`

## Acceptance-criteria evidence

### Criterion 1 — Public/preview renderer and CSS parity

- `public-agent-news-edge: OK` verified default and non-default dynamic detail
  routes, localized HTML, UUID/token/Flight-free HTML, byte-identical
  stylesheet delivery, and canonical renderer parity.
- `browser-e2e` preview passed computed renderer style/class equality between
  preview and canonical fixture equivalents; Web surface and browser-worker
  contract tests passed.
- The renderer remains one trusted component implementation; no CSP relaxation
  or leakage-negative relaxation was introduced.

### Criterion 2 — Browser evidence and cleanup

- Public Agent artifact list/retrieve checks passed for exact heading and
  structure artifacts, SHA-256/size/mime/visibility/route/target bindings,
  expected localized title/content and computed style, random/foreign
  capability denial, and idempotent replay.
- Durable event assertion passed with `ENQUEUED:LEASED:COMPLETED:
  PREVIEW_TOKEN_CONSUMED:ARTIFACT_REGISTERED = 1:1:1:1:2`.
- Clean Compose smoke passed retained artifact checks, outage/recovery,
  restart, revocation, private headers and no broad cleanup.

### Criterion 3 — Fallback, cancellation and race evidence

- Full integration `test_public_agent_builds_news_dynamic_listing_and_detail_render`
  passed localized fallback, missing-default fail-closed output, human preview
  cancellation with unchanged durable mutation state and reusable pool context,
  and deterministic dynamic preview-versus-Agent mutation ordering.
- Full integration `test_browser_token_projects_only_bound_overlay_and_is_one_time`
  passed dynamic snapshot cancellation, consumed one-use retry denial,
  newly-authorized recovery render, canonical/workspace isolation and clean
  COW operation state.
- The complete backend integration suite passed, including all existing
  concurrency, cancellation, COW, isolation and render tests.

### Criterion 4 — Continuity and gates

- Existing page/locale/navigation/redirect, dynamic query-bound, stale-definition,
  OpenAPI, migration, COW and restart contracts remained green.
- No new dependency, image, route, primitive, operator, architecture artifact,
  or historical order/report mutation was introduced.

## Local verification

- `node --test services/browser-worker/tests/contracts.test.mjs apps/web/tests/surface.test.mjs`: **PASSED** — 14 tests.
- `uv run --frozen pytest -q services/backend/tests/integration/test_agent_mutations.py::test_public_agent_builds_news_dynamic_listing_and_detail_render services/backend/tests/integration/test_render_browser_preview.py::test_browser_token_projects_only_bound_overlay_and_is_one_time`: **PASSED** — 2 tests in 18.69s.
- `uv lock --check`; `uv sync --frozen --all-groups`; Ruff check/format; mypy: **PASSED**.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: **PASSED** — 522 tests in 22.44s.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: **PASSED** — wheel and sdist.
- `uv run --frozen pytest services/backend/tests/integration`: **PASSED** — 173 tests in 1504.27s (25:04).
- Full frozen Node gate at Node `v24.14.1` / pnpm `11.22.0` (install, lint,
  format, typecheck, test, build, license inventory): **PASSED**; all listed
  package licenses were approved.
- Repository policy suites: **PASSED** — repository 58, packaging 48,
  supply-chain 34 tests; `python tools/check_repository.py` passed.
- `python tools/check_mermaid.py`: **PASSED** — 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: **PASSED** — 0 issues in
  403 files.
- `sh tools/compose/smoke.sh slaif007vdbg5`: **PASSED** on the clean rerun;
  48 packaging contract tests passed and all public/edge/browser/recovery
  proofs passed. The first attempt reached the end of runtime validation but
  failed only on the stale literal smoke-contract marker; the in-scope test
  expectation was corrected and the clean rerun passed.
- `sh tools/supply_chain/run.sh /tmp/slaif-077-v-supply-1788796127958540244`:
  **PASSED** — 6 images, 0 critical vulnerabilities, 42 high findings,
  checksum evidence passed. An earlier invocation was rejected because its
  output directory already existed; it was rerun with a unique path.
- PostgreSQL 14–18 version matrix: **PASSED** in current-head GitHub CI.

## GitHub CI / required checks

Observed for implementation head `217641d6cf546f4ec1175bad7dd93e6b02189a95`
before report publication: every current check was `pass`; no required check
was pending, missing, cancelled or failed.

- CI: Repository policy; Node contracts; Python 3.12, 3.13 and 3.14 quality
  and package; Foundation PostgreSQL 14, 15, 16, 17 and 18; Compose and edge
  packaging; Supply-chain evidence; Markdown; Mermaid; Dependency review.
- CodeQL: Detect supported languages; Analyze (actions); Analyze
  (javascript-typescript); Analyze (python); CodeQL.

The current CI run was `34142355622`; the current CodeQL run was
`34142355591`. The report-only commit may trigger a fresh check run; strategy
must independently verify that report-head run.

## Local setup / dependencies

- Used the existing frozen uv environment and lockfile with repository-required
  uv `0.12.5`; no dependency or lockfile change.
- Used Node `24.14.1`, pnpm `11.22.0`, local disposable PostgreSQL/Compose,
  Playwright browser fixtures, and fake credentials only.
- Supply-chain builds/scans used the repository-pinned images and generated
  evidence in a disposable `/tmp` directory; no production service or secret
  was accessed.

## Documentation

- No durable product/architecture/API/setup behavior documentation required a
  change beyond the executable contract and OAP transcript for this bounded
  repair. The versioned renderer stylesheet is documented by its source
  comment and exercised by executable tests.

## Safety and scope confirmations

- Unrelated files changed: **NO**; all 17 paths are required by `077-v`, its
  executable evidence, or its exact OAP transcript.
- Production secrets accessed: **NO**. Production systems accessed: **NO**.
- Required tests skipped/not run: **NO**. The PostgreSQL version matrix ran in
  authoritative GitHub CI; local integration used its disposable configured
  database rather than serially duplicating all five matrix environments.
- Scope deviation: **NO**; no 078+ work, new public route, dependency, image,
  primitive, operator, architecture change, or cleanup feature.
- Extra objective PR: **NO**. Coding-agent merge: **NO**.
- Activated order/active edited: **NO**; exact strategy bytes were committed.
- Report commit changes only this new report: **YES**.

## Known limitations / blockers

- No technical blocker remains for `077-v` after the verified implementation
  and current-head gates. PR #74 remains open because strategy must independently
  review the cumulative Objective 077 evidence and perform any acceptance/merge
  decision; the coding agent is prohibited from merging it.

## Recommended strategic follow-up

Independently review this report and the cumulative 077 transcript/diff/checks.
If satisfied, strategy may accept and merge PR #74 under OAP governance; no
additional implementation is authorized or indicated by this round.
