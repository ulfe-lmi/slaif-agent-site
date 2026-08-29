# OAP Work Order — 072-r

## Objective

Continue Objective 072 on PR #66. Fix the proven dispatcher-to-migration 037
artifact-register argument-order mismatch, add a real PostgreSQL regression that
cannot be satisfied by mocks, and restore green durable dispatch/Compose. Keep
the public artifact-byte endpoint at 404 until 072-s. Do not merge.

## Verified state and root cause

- Amend only PR #66 / `oap/072-browser-worker-real-playwright`; no new PR.
- Start at report-only head `6be8a751039f49fef731fe2d3bafce543ffe8a86`;
  its sole parent is implementation `f40967d368cc229429ec52d59f71c5e3a4f4e994`.
  Main remains `082f2359b0c4d59b692580d17992c35d46183b12`.
- All current checks pass except Compose. Migration 037's function signature is
  `(run, lease, artifact, kind TEXT, worker_request_id UUID, mime, sha, size,
  target, route_digest, expires)`. Dispatcher currently supplies request UUID
  fourth and kind fifth. Real PostgreSQL therefore cannot resolve the function;
  the finalization transaction rolls back, the lease releases, and retry gets
  `BROWSER_NAVIGATION_HTTP_404` after the one-time token was consumed.
- Unit mocks missed this positional type/order defect. The schema, grants,
  retrieval binding and worker output are otherwise coherent. Preserve the
  exact 41-entry `.64` exception/issue #67 through `2026-09-04`.

## Requirements and acceptance

1. Put `artifact.kind.value` and `worker_request_id` in the exact migration-037
   positional order. Change no SQL signature/schema/grant unless executable
   evidence contradicts the verified root cause.
2. Add a focused dispatcher assertion for positional values/types and a real
   PostgreSQL integration that invokes dispatcher finalization through the
   actual function: six artifacts register atomically with one request UUID,
   terminal `COMPLETED` commits, exact replay is idempotent, swapped/mismatched
   request/kind rolls back with no terminal or partial metadata.
3. One clean Compose regression must prove real `.64` dispatch
   `QUEUED -> RUNNING -> COMPLETED`, six private artifacts, canonical unchanged,
   Agent/worker restart retention, hostile-network/credential/cleanup invariants,
   and public artifact bytes still 404. Render stage sequence reaches success
   once per attempt; no consumed-token retry.
4. Run focused/full backend, real PostgreSQL/migration/grants, Node/contracts,
   repository/packaging policy, exactly one clean Compose, current supply-chain,
   Markdown/Mermaid and every fresh GitHub check. No unchanged reruns; report
   failures/skips/retries literally.

## Scope and workflow

Prefer dispatcher call plus direct tests/docs/transcript only. No migration or
function redesign, public route/stream, worker runtime/store/network, browser
token/route, exception expansion, dependency, GC/source/review/promotion,
second PR, merge, auto-merge or release.

Commit/push unchanged order and `oap/active`, then repair. Publish exactly
`oap/reports/072-r-fix-artifact-register-call-order.md` as report-only child
with literal implementation parent and `Report publication commit: SELF`;
signal exact FIFO `OK`.

Report exact before/after positional contract; real DB atomicity; Compose states/
artifacts/restarts; public-still-404; tests/CI; exception status; files/SHAs; no
extra PR and no merge. Objective 072 remains `PARTIAL` pending 072-s public
retrieval and final review.
