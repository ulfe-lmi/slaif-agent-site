# OAP Work Order — 072-q

## Objective

Continue Objective 072 on PR #66. Add the missing durable, least-privilege
binding required for restart-safe browser artifact retrieval: persist the
worker request UUID with each registered artifact and expose one exact
capability-confined Agent-runtime lookup used by an internal service method.
Keep the public byte route returning 404 until 072-r. Do not merge.

## Verified state

- Amend only PR #66 / `oap/072-browser-worker-real-playwright`; no new PR.
- Start at green report-only head `9ad30a48c093fc1c3fe3f96c2c45c84064a60bfe`;
  its sole parent is implementation `63998f16e056f10bce6c5dff4ea9f28a76662ace`.
  Main remains `082f2359b0c4d59b692580d17992c35d46183b12`;
  all 20 required checks pass.
- Durable dispatch and six private artifacts pass through real `.64` Chromium.
  Worker persisted metadata binds `requestId`, but migration 035 stores no
  worker request ID. `BrowserWorkerClient.retrieve` requires it, so later Agent
  retrieval cannot honestly reconstruct the authenticated internal request.
- Public metadata/listing is capability confined; the byte endpoint deliberately
  remains 404. The exact 41-entry temporary `.64` exception/issue #67 expire
  `2026-09-04`; preserve them.
- Immutable 072-p report corrections for continuity: actual delivery mode was
  `AMENDED_EXISTING_PR`, not `CREATED_NEW_PR`; actual final report/check head was
  `9ad30a48...`, not the cited intermediate `e9a8b0a6...`.

## Requirements

1. Add one deterministic forward Alembic migration after current head 036. Add
   non-null `worker_request_id UUID` to browser artifacts with exact integrity/
   indexing needed for retrieval. Fresh-install migration is authoritative;
   downgrade removes only new objects safely. Do not expose the field publicly.
2. Extend the Agent-owned artifact-register function and dispatcher call so the
   verified signed worker result's exact request UUID is stored atomically with
   artifact metadata and terminal completion. Same artifact replay must require
   the same request UUID; mismatch fails without partial registration/completion.
3. Add one narrow SECURITY DEFINER retrieval-binding function taking trusted
   capability/site/workspace/delegator/run/artifact IDs and returning only the
   exact internal worker retrieval fields: request/run/site/workspace/artifact,
   kind/MIME/digest/size/target/route digest/retention/visibility. Require current
   capability/workspace/site authority, terminal `COMPLETED`, retained run and
   artifact, exact private visibility and bindings. Foreign/random/revoked/
   expired/nonterminal/cross-site inputs return no row.
4. Owner and grants follow existing migration hardening: Agent runtime receives
   EXECUTE only; PUBLIC and every unrelated role are revoked; no direct table
   DML/SELECT expansion; browser worker remains DB-less.
5. Add an internal `AgentBrowserRunService` retrieval method that performs the
   exact lookup, constructs `BrowserWorkerArtifactMetadata` without leaking
   internal IDs publicly, invokes the existing authenticated worker client, and
   returns bounded verified bytes plus safe MIME/digest metadata. Missing binding
   maps non-leaking not-found; worker/storage/digest failure maps unavailable.
   Do not connect the public HTTP route in this round.

## Acceptance and verification

- Unit tests cover exact metadata construction, client call, size/digest/MIME,
  cancellation, not-found/unavailable mapping and no secret/internal-field logs.
- Real PostgreSQL tests cover migration up/down, atomic register+complete,
  idempotent exact replay, request-ID mismatch rollback, current-authority and
  cross-site/nonterminal/retention negatives, grants and pool cleanup.
- Focused integration proves completed artifact binding survives Agent and
  worker restart and internal authenticated retrieval returns byte-identical
  content; public byte route remains 404 for both real and random IDs.
- Run focused/full backend, migration/privilege/PostgreSQL 14–18, Node/contracts,
  repository/packaging policy, one clean Compose regression, current supply-
  chain, Markdown/Mermaid and every fresh GitHub check. No unchanged reruns;
  report failures/skips/retries literally.

## Scope and workflow

Only forward migration/grants, dispatcher registration parameter, internal
retrieval service/binding/contracts/tests/docs, transcript. No public endpoint/
stream, worker runtime/store/network, browser token/route, exception expansion,
GC/source/review/promotion, dependency, second PR, merge or release.

Commit/push unchanged order and `oap/active`, then implementation. Publish
exactly `oap/reports/072-q-durable-artifact-retrieval-binding.md` as report-only
child with literal implementation parent and `Report publication commit: SELF`;
signal exact FIFO `OK`.

Report schema/signature/grants/atomicity and restart evidence; public-still-404;
tests/CI; exception status; corrected 072-p facts; files/migration/SHAs; no extra
PR and no merge. Objective 072 remains `PARTIAL` pending 072-r public retrieval
and final review.
