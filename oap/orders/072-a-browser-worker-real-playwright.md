# OAP Work Order — 072-a

## Objective

Replace the browser worker health-check stub with a real Playwright-backed
worker supporting bounded screenshot/snapshot/console/network diagnostics
against authorized preview targets.

## GitHub objective state

- Numeric objective: `072`; round: `072-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR

## Verified current state

- `browser-worker/src/server.ts` is health-check HTTP server only.
- No Playwright import or browser launch code exists.
- Internal contract `POST /internal/browser/v1/preview-runs` defined but not
  implemented.

## Required changes

1. Install pinned Playwright in browser-worker with reproducible image build.
2. Implement `POST /internal/browser/v1/preview-runs` accepting bounded run
   spec (target URL/path, viewport target, artifact types requested).
3. Worker launches fresh isolated Chromium context per run; navigates;
   captures screenshot, accessibility snapshot, console errors, failed
   requests; stores artifacts as immutable private objects scoped to
   workspace/run/digest.
4. Enforce per-run timeout (default 30s), max concurrent contexts, max
   artifact bytes; reject excess with 429.
5. Return structured result with run_id, artifact references, summary.
6. Worker has NO database credential; receives short-lived preview token
   from Agent API exchange (or documented interim if auth wiring deferred —
   state honestly in report).
7. Integration test: seed page, issue preview-run, assert artifacts exist,
   screenshot non-empty, console captured, context destroyed after run.

## Explicit non-goals

- Do NOT implement source-origin crawling (separate L4 objective).
- Do NOT implement responsive sweep across all six targets (separate).
- Do NOT allow arbitrary URL navigation — only approved preview targets.
- Do NOT give browser worker DB access.

## Acceptance criteria

- Real Chromium screenshot produced for a seeded page.
- Artifacts stored immutably and referenced by digest.
- Timeout/quota violations return structured errors.
- No DB credentials accessible from browser worker process.
- Tests pass in CI.

## Report

Publish `oap/reports/072-a-browser-worker-real-playwright.md` with SELF
report commit parenting implementation SHA.
