# OAP Work Order — 072-o

## Objective

Continue Objective 072 on PR #66. Fix the real browser-preview 404 by defining
and using one canonical route representation across Agent API, DB/digest/token,
shared TypeScript contracts, worker URL and Web-to-Render binding. Non-root
trailing slashes canonicalize away; root remains `/`. Prove durable dispatch
reaches real `COMPLETED`. Do not add public artifact-byte retrieval or merge.

## Verified state and root cause

- Amend only PR #66 / `oap/072-browser-worker-real-playwright`; no new PR.
- Start at report-only head `92d385c70321cf09eb2beb561860c2a211560d5f`;
  its sole parent is implementation `fcf8cf43c889588e7c6818396a740ef59010b00d`.
  Main remains `082f2359b0c4d59b692580d17992c35d46183b12`.
- Supply-chain and all non-Compose checks pass. Compose alone fails with
  `BROWSER_NAVIGATION_HTTP_404` on the known-good seeded `/s/demo/` path.
- Python `normalize_preview_route` and TypeScript
  `normalizeBrowserPreviewRoute` preserve `/s/demo/`. Worker navigates
  `/preview/<workspace>/s/demo/`; Next catch-all params reconstruct
  `browserRoute` as `/s/demo`; Render exact expected-binding comparison rejects
  signed `/s/demo/`. The test now fails immediately and safely, proving this
  product boundary mismatch rather than a missing page.
- The exact 41-entry temporary Chrome `.64` exception and issue #67 expire
  `2026-09-04`; preserve them. Any new unexcepted finding fails closed.

## Requirements

1. Define canonical route semantics in both shared implementations: validate as
   today; remove trailing `/` characters from a non-root pathname; keep `/`;
   preserve safe percent-encoded path spelling and sorted canonical query.
   Examples: `/s/demo/ -> /s/demo`, `/s/demo/?b=2&a=1 -> /s/demo?a=1&b=2`,
   `/ -> /`. Duplicate separators/traversal/encoded separators remain rejected.
2. Require Python/TypeScript parity tests over root, trailing slash, query,
   Unicode/percent encoding and hostile cases. Generated/JSON contracts and
   route-byte bounds remain consistent; no client may choose a second form.
3. Use the shared TypeScript normalizer in the server-only Web preview boundary
   (add only an internal workspace dependency if needed). Canonicalize the
   reconstructed path/query before passing `browser_route` to Render. Agent
   create, stored route, SHA-256 digest, token claim, dispatcher request, worker
   URL and Render expected binding must all use the same canonical bytes.
4. Preserve exact signed route binding: a token for canonical `/s/demo` cannot
   render another path/query/site/workspace/run, and trailing-slash aliases must
   not consume a token twice or create two idempotency digests/runs. Do not
   weaken one-time nonce, 404 non-leakage, site resolution, COW context, Host,
   URL/network or credential policy.
5. Keep 072-m fail-fast terminal diagnostics. If any runtime attempt fails,
   report the bounded state/code immediately rather than polling blindly.

## Acceptance and verification

- Focused Python/TS/Web/worker/Render unit and real PostgreSQL tests prove
  canonical parity, one idempotent run for slash aliases, exact digest/token/
  DB/request binding, replay/tamper denial and unchanged canonical content.
- One clean Compose run proves public NGINX creation with `/s/demo/`, observed
  `QUEUED -> RUNNING -> COMPLETED`, real `.64` Chromium COW overlay, nonempty PNG
  plus heading/structure summaries, atomic DB metadata, two-run isolation,
  Agent/worker restart recovery, hostile-network/credential/cleanup invariants,
  and public artifact bytes still unavailable.
- Run focused/full backend and Node gates, repository/packaging/Compose policy,
  exactly one clean Compose regression with nine Playwright projects, current
  supply-chain evidence, Markdown/Mermaid and all fresh GitHub checks. No
  unchanged broad retry loop; report failures/skips/retries literally.

## Scope and workflow

Change only shared route contracts/tests, Agent route normalization/digest if
needed, Web preview binding/dependency, worker URL tests, directly necessary
docs and Compose regression. No migration/grant, dispatcher redesign, worker
runtime/network/store, exception expansion, dependency outside internal
workspace package, public retrieval, GC/source/review/promotion, second PR,
merge, auto-merge or release.

Commit/push unchanged order and `oap/active`, then repair. Publish exactly
`oap/reports/072-o-canonical-preview-route.md` as report-only child with literal
implementation parent and `Report publication commit: SELF`; signal exact FIFO
`OK`.

Report canonical examples/parity, root cause, exact route/digest/token bindings,
E2E states/artifacts/restarts, tests/CI, exception status, files/locks/SHAs, no
extra PR and no merge. Objective 072 remains `PARTIAL` pending public artifact
retrieval and final review.
