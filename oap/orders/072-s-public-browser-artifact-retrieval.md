# OAP Work Order — 072-s

## Objective

Continue Objective 072 on PR #66. Implement the final public Agent boundary for
private browser artifacts: capability-authenticated, run/site/workspace-bound
byte retrieval proxied through the Agent API to the authenticated DB-less worker.
Restore/strengthen full end-to-end byte, restart, privacy and negative proof.
Declare Objective 072 complete only if every original browser objective gate and
all current checks pass. Do not merge.

## Verified state

- Amend only PR #66 / `oap/072-browser-worker-real-playwright`; no new PR.
- Start at green report-only head `02ec60520d21fa542c85c73f2509bd61ee34a3a4`;
  its sole parent is implementation `88149e051e4cc53036779edb07c6afe42806dea4`.
  Main remains `082f2359b0c4d59b692580d17992c35d46183b12`;
  all 20 required checks pass.
- Real capability creation, durable dispatch, `.64` Chromium COW rendering,
  atomic completion, six private artifacts and restart-safe worker storage pass.
  Migration 037 persists exact worker request UUID and exposes a least-privilege
  Agent-only retrieval binding; internal service retrieval verifies MIME/size/
  SHA. Public byte GET still deliberately returns 404.
- The 41 exact `.64` exceptions and issue #67 are human-approved through
  `2026-09-04`; preserve them. Official qualified `.65+` or expiry requires
  removal/upgrade; any new unexcepted finding fails closed.

## Public retrieval contract

1. Wire `GET /api/agent/v1/preview-runs/{run_id}/artifacts/{artifact_id}` to the
   existing internal retrieval service. Authenticate the capability and require
   `preview:inspect`; derive site/workspace/delegator from trusted context; never
   accept them, request UUID, path, MIME, digest or storage locator from caller.
2. Return 200 only for an exact current-authority, terminal-COMPLETED, retained
   PRIVATE artifact binding. Proxy the already bounded verified bytes with exact
   allowlisted `Content-Type`, deterministic length and digest/ETag metadata;
   apply `Cache-Control: private, no-store`, `Pragma: no-cache`, and
   `X-Robots-Tag: noindex, nofollow, noarchive`. No redirect, public URL, Range/
   partial contract, Media promotion, filesystem path or direct volume access.
3. Preserve stable non-leaking semantics: malformed/invalid/revoked/expired
   capability follows existing 401; missing scope 403; authenticated random/
   foreign/cross-site/wrong-run/wrong-artifact/nonterminal/expired/inactive
   binding is indistinguishable 404; internal worker/storage/digest/MIME failure
   is safe 503 with no partial body or binding details.
4. Bound memory/body/latency using existing artifact/client limits and request
   timeout. Cancellation/client disconnect must cleanly end proxy work without
   changing DB/artifact state. Never log capability, worker token, request UUID,
   storage path, sensitive route/query or artifact bytes.

## Required executable proof

- Unit/contract tests cover headers/body/type/digest, exact error mapping,
  cancellation, worker corruption/unavailability, zero partial response and no
  internal-field serialization.
- Real PostgreSQL tests cover exact binding plus valid-other-capability/site/
  workspace/run/artifact, random IDs, nonterminal, revoked/expired authority,
  frozen workspace and expired retention; reads create no COW operation/audit
  mutation or publication authority.
- One clean public-NGINX Compose E2E, run with available passwordless sudo,
  must create two real Agent runs, observe QUEUED→RUNNING→COMPLETED, list six
  metadata records, retrieve all six through public Agent routes, and verify
  byte count/SHA/MIME agreement. Decode PNG (nonempty, 1440×900) and validate
  heading/structure summaries contain the COW overlay while canonical public
  output does not.
- Retrieve the same artifact after Agent API restart and after browser-worker
  restart and prove byte-identical content. Prove valid foreign capability and
  random/wrong bindings are non-leaking, revoked token denied, worker outage is
  503 while canonical site stays available, and recovery restores bytes.
- Retain hostile URL/network, forged/expired/replayed/wrong-route/wrong-target
  credential, context/storage bleed, Chromium cleanup, private mode/link/digest,
  secret redaction and NGINX-only-public-port tests. A fake browser, fake bytes,
  direct internal call or direct volume read cannot satisfy the E2E.

## Final verification and docs

- Run focused/full backend, migration/privilege/PostgreSQL 14–18, Node/contracts/
  Web/worker, repository/packaging policy, exactly one clean full Compose with
  nine Playwright projects, current supply-chain, Markdown/Mermaid and every
  fresh GitHub check. No unchanged reruns; report attempts/failures/skips.
- Update API/security/config/operations/testing/service-authority docs to state
  exact implemented private retrieval, retention/errors/limits and non-goals.
  Do not claim source crawling, review attachment, GC, public Media or release.

## Scope and workflow

Only Agent retrieval HTTP/service wiring, response/tests/Compose proof/docs and
transcript. No schema/migration/grant change, dispatcher/worker runtime/network/
store redesign, exception expansion, source tools/six-target runtime sweep,
MCP/review/promotion/publication, unrelated dependency, second PR, merge,
auto-merge or release.

Commit/push unchanged order and `oap/active`, then implementation. Publish
exactly `oap/reports/072-s-public-browser-artifact-retrieval.md` as report-only
child with literal implementation parent and `Report publication commit: SELF`;
signal exact FIFO `OK`.

Report public contract/errors/headers/limits; exact E2E run/artifact/byte/restart/
negative evidence; all tests/current CI; exception status; files/docs/SHAs; no
extra PR and no merge. Use `COMPLETE` for Objective 072 only if the full original
072 contract is now proved; otherwise `PARTIAL` with exact remaining gap.
