# OAP Work Order — 072-l

## Objective

Continue Objective 072 on PR #66. Connect durable queued preview runs to the
qualified database-free browser worker through a bounded, restart-safe Agent API
dispatcher. Claim/renew/release leases, mint the existing run-bound preview
credential, verify the signed worker result, and atomically register exact
artifact metadata plus terminal state. Do not add public artifact-byte retrieval
yet. Do not merge.

## Verified state

- Amend only PR #66 / `oap/072-browser-worker-real-playwright`; no new PR.
- Start at green report-only head
  `b5430ccdbfdc7c410d3a318109c89945d9e80600`; its sole parent is transcript
  `503a1aec37c07cdd6d33bd421231f5babf0534f4`. Main remains
  `082f2359b0c4d59b692580d17992c35d46183b12`; all 20 checks pass.
- Migration 035 already provides least-privilege Agent-runtime claim, renew,
  release, completion and artifact-register functions with shared workspace
  locks, authority rechecks, bounded attempts and `SKIP LOCKED`; do not replace
  them or add a migration.
- Public capability-authenticated creation/status/artifact-metadata routes and
  canonical run-bound preview credentials are real. The `.64` worker/client,
  private store, fixed targets, signed response and internal retrieval are real.
  No production code currently claims or dispatches queued runs.
- The human-authorized 31-entry browser exception and issue #67 expire
  `2026-09-04`; preserve them exactly. Any new unexcepted finding fails closed.

## Required dispatcher contract

1. Add one Agent-owned dispatcher service started/stopped by Agent API lifespan,
   using its existing DB pool, signing key and worker client. Configuration must
   be typed/bounded and startup-validated: enabled demo default, poll/backoff,
   lease 1–60 s, renewal interval safely below lease, one conservative local
   concurrency, worker timeout within run duration, and bounded shutdown. No
   in-memory-only authority or new process/credential/network.
2. Claim exactly through `slaif_agent_browser_run_claim` with a fresh random
   lease ID. Build the worker request only from the trusted claim row and
   server configuration. Mint a fresh opaque credential bound to deployment,
   run/site/workspace/capability, route/digest, target, evidence policy, nonce,
   attempt and expiry. Never expose DB locator, Agent capability, human cookie,
   signing key, worker secret, arbitrary URL/header or caller limits.
3. Submit through the existing authenticated `BrowserWorkerClient`; verify its
   exact signed request/result binding. Renew the lease while work is live.
   Lost/expired/wrong lease, cancellation, shutdown or authority change must
   stop finalization and never make a result visible.
4. For a valid result, in one DB transaction register every exact returned
   artifact and complete the run. Revalidate unique kind/count, IDs, digest,
   size, MIME, target, route digest, retention and total reserved bytes before
   DB calls. Completion is visible only if every registration and terminal
   transition commits; otherwise none does. Private unregistered worker bytes
   may remain only as future-GC orphans.
5. Map bounded worker terminal results to `COMPLETED|FAILED|TIMED_OUT|CANCELLED`
   with safe summary/error vocabulary. Transient HTTP/overload/disconnect errors
   release for bounded retry; max attempts/timeouts remain DB-authoritative.
   Never retry a terminal run, change conflict/authority policy, or busy-loop.
6. Multiple Agent replicas must safely race claims without duplicate execution.
   Startup/restart recovers queued/expired leases; clean shutdown cancels work,
   closes client/tasks, and either safely releases a current lease or lets its
   bounded expiry recover it. Readiness/status must expose only non-secret
   dispatcher availability/counters, not identities or payloads.

## Acceptance and tests

- Unit tests cover configuration, request construction, signed binding,
  renewal, atomic finalization, transient/terminal mapping, cancellation,
  shutdown, lease loss and redaction.
- Real PostgreSQL tests prove single claim under concurrent replicas, expired-
  lease fresh-context recovery, no duplicate completion/artifacts, atomic
  register+complete rollback, attempt exhaustion, and freeze/revoke/expiry race
  preventing visibility/audit mismatch.
- One clean public-NGINX Compose E2E creates a capability run and observes
  `QUEUED -> RUNNING -> COMPLETED`, real `.64` Chromium COW preview, nonempty PNG
  plus two summaries, exact DB metadata/private bytes, Agent/worker restart
  recovery, two-run isolation, hostile-network/credential/cleanup invariants,
  and no canonical content or publication effect. Artifact bytes remain
  unavailable through public Agent/NGINX routes in this round.
- Run focused/full backend and Node gates, repository/packaging/Compose policy,
  one clean Compose regression with nine Playwright projects, process checks,
  current supply-chain evidence, docs/Markdown/Mermaid, and all fresh GitHub
  checks. No unchanged broad retry loop; report failures/skips literally.

## Scope, non-goals, workflow

Change only Agent dispatcher/config/lifespan/DB adapter, directly needed typed
contracts/tests/Compose health and accurate API/config/security/operations/
testing docs. No migration/grant expansion, worker runtime/store/network,
public artifact byte endpoint, direct volume mount, GC/source/six-target sweep,
MCP/review/promotion/publication, exception expansion, unrelated dependency,
second PR, merge, auto-merge or release.

Commit/push unchanged 072-l order and `oap/active`, then implementation. Publish
exactly `oap/reports/072-l-durable-browser-dispatch.md` as report-only child
with literal implementation parent and `Report publication commit: SELF`;
signal exact FIFO `OK`.

Report dispatcher lifecycle/lease/transaction/error contracts; runtime/E2E and
race evidence; exact tests/CI; exception status; files/config/docs; PR/base/
branch/SHAs; no extra PR and no merge. Objective 072 remains `PARTIAL` pending
public artifact retrieval and final end-to-end closure.
