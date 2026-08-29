# OAP Work Order — 072-m

## Objective

Continue Objective 072 on PR #66. Repair the durable-dispatch Compose E2E route
fixture and its silent terminal polling. Prove the dispatcher reaches real
`COMPLETED` with the seeded COW preview. Change product code only if executable
evidence shows a product defect; otherwise keep this test-only. Do not add public
artifact-byte retrieval and do not merge.

## Verified state and root cause

- Amend only PR #66 / `oap/072-browser-worker-real-playwright`; no new PR.
- Start at report-only head `8ad0d59f22976fe088e311349839757b6b754d63`;
  its sole parent is dispatcher implementation
  `330d3115e3ac3e44cb277a6905d40e708f85e4da`. Main remains
  `082f2359b0c4d59b692580d17992c35d46183b12`.
- Every current required check passes except `Compose and edge packaging`.
  Both local and CI dispatch reached terminal `BROWSER_NAVIGATION_HTTP_404`.
- The smoke fixture submits `/s/demo/home`; the existing preview E2E and
  canonical checks prove the seeded demo route is `/s/demo/`. The script then
  polls up to 180 seconds while ignoring an already-terminal non-COMPLETED
  result, hiding the exact error until timeout.
- Dispatcher unit/integration gates and all other CI pass. The 31-entry temporary
  exception/issue #67 remain valid through `2026-09-04`; preserve them.

## Requirements and acceptance

1. Bind the dispatcher and direct-worker fixtures to the exact same known-good
   seeded route `/s/demo/` (or derive it once from the fixture's authoritative
   site-domain/page data). Remove the guessed `/home` suffix. Keep route,
   route-digest, signed credential, worker request and DB row identical.
2. Make polling stop immediately on `FAILED|TIMED_OUT|CANCELLED`, printing only
   a bounded safe state/error code/message before failing. Never print tokens,
   IDs beyond test run identity, URLs with queries, headers, DB locators or
   artifact bytes. Retain the bounded overall timeout.
3. Add a focused regression proving the seeded route resolves through the
   browser credential while `/s/demo/home` fails safely, and that terminal
   non-success cannot be mistaken for progress. Do not relax 404/token/route
   binding or make Render accept nonexistent paths.
4. One clean Compose run must prove public NGINX create, observed
   `QUEUED -> RUNNING -> COMPLETED`, real `.64` Chromium, COW overlay not
   canonical, nonempty PNG plus two summaries, atomic DB metadata, two-run
   isolation, Agent/worker restart recovery, hostile-network/credential/cleanup
   invariants, and public artifact bytes still unavailable.
5. Run focused tests, repository/packaging policy, one clean Compose regression,
   current supply-chain gate, and all fresh GitHub checks. No unchanged reruns;
   report failures/skips literally.

## Scope and workflow

Prefer only `tools/compose/smoke.sh` plus directly necessary focused tests/docs.
No dispatcher redesign, migration/grant, auth/token/Render policy weakening,
worker/runtime/network/artifact, exception, dependency, public retrieval, GC,
source/review/promotion, second PR, merge, auto-merge or release.

Commit/push unchanged 072-m order and `oap/active`, then the minimal repair.
Publish exactly `oap/reports/072-m-repair-dispatch-preview-route.md` as a
report-only child with literal implementation parent and
`Report publication commit: SELF`; signal exact FIFO `OK`.

Report proven root cause; route/digest consistency; terminal diagnostic
behavior; exact E2E states/artifacts/restarts; tests/CI; exception status;
files/SHAs; no extra PR and no merge. Objective 072 remains `PARTIAL` pending
public artifact retrieval and final review.
