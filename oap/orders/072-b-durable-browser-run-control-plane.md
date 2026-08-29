# OAP Work Order — 072-b

## Objective

Continue Objective 072 on the existing PR #66. Complete the durable,
least-privileged Agent-side browser-run control plane that the real Playwright
worker will consume in the next same-PR continuation: versioned shared
contracts, capability-derived browser limits, idempotent preview-run enqueue and
status/artifact authorization, narrow PostgreSQL state/functions/audit, and
run-bound credential signing/verification primitives. Remove the fake browser
responses. Do not attempt Chromium or artifact filesystem implementation in
this round, do not claim Objective 072 complete, and do not merge.

## Verified starting state and transcript correction

- Numeric objective: `072`; round: `072-b`.
- Mode: `AMEND_EXISTING_PR`; amend only PR #66 on
  `oap/072-browser-worker-real-playwright`. Create no new PR.
- Begin from verified remote 072-a report head
  `fef8f6214494fa53a1e5194927d8b04ef58d244d`; its sole parent is
  `c31b0bb8bb357ed5e3f1398ac02369f5c76c9830` and its sole changed path
  is `oap/reports/072-a-browser-worker-real-playwright.md`.
- Remote main remains
  `082f2359b0c4d59b692580d17992c35d46183b12`; PR #66 is open,
  non-draft, and mergeable. Reconcile live GitHub before mutation.
- The immutable 072-a report is truthful about substantive incompleteness but
  violates the report contract by writing the short value `c31b0bb` where a
  literal 40-hex implementation SHA was required. Do not edit that report.
  Record the exact full parent above in the 072-b report and identify this as
  the append-only correction.
- The 072-a branch contains only the activated order/active commit and report;
  the worker, fake Python browser router, contracts, schema, and runtime remain
  unchanged from main.

## Bounded scope and sequencing

This is the control-plane foundation round of the already-activated 072-a
objective. Change only:

- shared browser run/target/artifact/diagnostic contracts;
- migration 035 and exact privilege validation;
- Agent capability context/database/browser service/public routes;
- server-only run-credential signer/verifier primitives and secret
  configuration/initialization needed for a later worker round;
- direct tests and exact API/security/database/config/testing documentation.

Explicitly leave for the next continuation on this same PR:

- Playwright package/browser/image and worker runtime;
- worker internal submit/status/artifact endpoints and callback;
- private artifact filesystem/volume;
- dispatcher execution/lease retry against the worker;
- browser network interception/confinement and process cleanup; and
- clean real-Chromium public-NGINX run/artifact E2E.

The public create route may durably return QUEUED. It must never fabricate a
completed run or artifact. Status must report the truthful durable state. Do
not add a temporary in-memory worker or relaxed auth substitute.

All 072-a non-goals remain: no source crawling, arbitrary URL, six-target
runtime sweep, review/promotion/publication, public artifacts, GC deletion,
hosted service, worker DB, or dependency in this round. Do not edit migrations
006 through 034, activated 072-a order, or published 072-a report. No extra PR
and no merge.

## 1. Versioned shared contracts

Replace metadata-only `browser-tool-contracts` with one versioned, extra-forbid
contract used by Agent API and the future worker. Define and validate:

- stable runtime target enum for only the Chromium targets approved for first
  runtime delivery, with immutable product-owned descriptors kept separate
  from caller input;
- curated requested evidence enum: screenshot, accessibility summary,
  structural/heading/link/media/overflow summary, console summary, and failed-
  request summary;
- normalized preview-run request containing route, target, and evidence only;
- durable state enum and create/status/result schemas;
- artifact metadata type/MIME/digest/size/target/expiry schema;
- stable internal run specification and completion/callback schema for the next
  round; and
- contract version constants and deterministic JSON serialization/digest.

Reject unknown versions/fields, arbitrary viewport, absolute URL/origin,
workspace/site/capability/run IDs in external create input, headers/cookies,
JavaScript/browser commands, duplicate evidence, excessive values, and
unsupported targets. Add TypeScript tests plus Python parity/generated-schema
tests; do not hand-maintain unchecked divergent facts.

## 2. Migration 035 durable state and limits

Add one deterministic forward migration 035 with one Alembic head. Introduce
the minimum durable tables/columns needed for browser preview runs:

- capability browser limits with conservative non-null defaults;
- browser-run/idempotency record bound immutably to capability, site,
  workspace, delegator, normalized route, target, request digest, state,
  attempts/lease, quota reservation, result/error summary, timestamps and
  expiry;
- private artifact metadata bound to run/site/workspace/capability with digest,
  type, MIME, size, target, route digest, created/expiry and terminal visibility;
  no absolute path or public URL; and
- append-only browser audit/event rows for enqueue, claim/lease, terminal
  completion/failure/cancellation and artifact registration.

Use strict UUID/FK/site-workspace/run constraints, unique idempotency and lease
keys, state/transition checks, digest/size/time bounds, indexes, and deletion
policy that cannot cascade away audit. Browser run/artifact state is not COW
content and cannot publish.

Add exact owner-defined functions for Agent runtime only:

- begin/replay/mismatch and atomically reserve run/quotas;
- get one capability-visible run and artifact metadata;
- claim/renew/finish preview-only run leases for the future Agent-owned
  dispatcher; and
- register terminal worker result/artifacts only for the exact leased run after
  current capability/workspace/site recheck.

Every mutable function takes the workspace shared advisory transaction lock
before mutable checks. Use `FOR UPDATE SKIP LOCKED` only in the exact preview
claim function. Grant only exact `EXECUTE` to `slaif_agent_runtime`; revoke
PUBLIC and deny direct browser tables/sequences, generic jobs, scheduler,
reviewer, Control, setup, and arbitrary audit operations. Public/preview/
Editor/Media roles receive no browser mutation authority. Browser worker has no
database identity.

## 3. Capability-derived authorization, quotas, and idempotency

Extend trusted `AgentCapabilityContext` and capability authentication to return
validated browser limits/resource facts. Never parse limits from headers/body.
At minimum enforce per-capability total runs, screenshots, artifact bytes,
route/evidence counts, maximum duration, target allowlist, and concurrent
nonterminal runs. Existing capabilities receive conservative defaults.

Run creation must:

1. authenticate the capability through the existing real Agent database
   identity;
2. require `preview:inspect` and ACTIVE/unexpired/unrevoked capability,
   workspace and site;
3. validate normalized route/target/evidence against shared contracts;
4. require and validate `Idempotency-Key`, derive a request digest and
   server-owned run UUID;
5. acquire the shared workspace lock and recheck current authority;
6. atomically reserve quotas, create QUEUED run/idempotency/audit state or
   return a replay; and
7. return only stable public run metadata, never internal credential or DB
   details.

Same key+same digest returns the same run and does not double-reserve. Same key
with another digest returns 409. Concurrent requests serialize to one run.
Quota denial is 429 with no partial idempotency/audit/run residue. A read creates
no mutation/audit/COW operation.

## 4. Public Agent routes and fake-route removal

Expose capability-authenticated routes under `/api/agent/v1/preview-runs` for
create, status, artifact metadata list, and future artifact retrieval. Reuse the
existing Agent auth/error/request-ID/security middleware and NGINX Agent path.
All get/list/retrieval lookups require exact current capability/site/workspace
association and retention; foreign/missing/expired IDs return non-leaking 404.

Until the worker continuation registers a terminal result:

- create returns 202/QUEUED with polling location or established typed body;
- status truthfully remains QUEUED or claimed test state;
- artifact list is empty; retrieval is 404; and
- worker-unavailable dispatch does not silently mark success.

Remove the fabricated Python `internal/browser` router from Agent API. Do not
leave an unauthenticated endpoint that accepts caller workspace/route/targets.
Internal worker routes belong to the Node worker in the next round and are not
edge exposed.

Stable errors: auth 401, scope 403, malformed/idempotency 400, invisible 404,
mismatch/state conflict 409, schema/route/target 422, quota/concurrency 429,
database unavailable 503. No error contains capability, digest, SQL, role,
internal URL, signing key, or foreign identifier.

## 5. Run-bound credential foundation

Implement a server-only signer/verifier for the later browser run credential,
without yet dispatching it. Use a generated file-backed HMAC/signing key with
startup validation, descriptor/no-follow/type/mode/owner checks, constant-time
verification, fixed algorithm/version/audience, bounded lifetime, and rotation-
safe key identifier if needed.

The signed payload is immutable and binds deployment/audience, capability,
site, workspace, run, normalized route, target, evidence/artifact limits,
issued/expiry and nonce. Reject missing/duplicate/malformed/expired/future/
wrong-audience/wrong-signature/extra-field tokens and route/target changes.
Never expose a token in the public Agent response, URL, log, report, fixture
output, browser storage, or database plaintext. Store only safe token/key
digests/identifiers if persistence is necessary.

Wire secret initialization and isolated mounts only as far as needed for Agent
API signer and future Web/Render verifier. Do not mount the signing key to the
browser worker. Do not yet enable a Web/Render browser-preview path unless an
internal test uses the verifier without claiming browser execution.

## 6. Real PostgreSQL and security proof

Add real PostgreSQL/public Agent HTTP tests using `slaif_agent_login` and
ordinary capabilities/workspaces/sites:

1. create/replay/mismatch, concurrent same-key serialization, exact run/audit/
   idempotency/quota counts, and zero COW content operations;
2. missing/wrong scope, revoked/expired capability, inactive/expired/revoked
   workspace/site, wrong-site route/resource, forged client site/workspace/run,
   malformed/absolute/traversal/internal route, target/evidence/limit errors;
3. total/concurrent/screenshot/artifact quota failures with no residue and
   independent capability/workspace quotas;
4. two sites/two workspaces/two capabilities cannot read each other's run or
   artifact metadata; random UUIDs are non-leaking 404;
5. deterministic workspace freeze/revoke race: hold exclusive lock, start run
   creation, prove wait, change authority, release, deny with no residue;
6. narrow function ownership/search path/grants and explicit direct table/
   sequence/generic job/Control/reviewer/setup/other-role denials;
7. claim lease uniqueness, expired lease bounded retry, max attempts, terminal
   idempotency, callback/result signature rejection, and no result visibility
   after capability/workspace revocation; and
8. signer/verifier vectors, tampering, expiry, audience, route/target/artifact
   binding, file-policy failures, redaction, and no plaintext persistence.

Static/source/unit tests alone are insufficient for identity/grant/quota/
isolation claims. Public route tests must traverse the real Agent app, and clean
Compose must prove fake internal routes are unreachable and only NGINX publishes.

## Acceptance criteria

- PR #66 contains a real durable capability/site/workspace-bound QUEUED browser
  run control plane with exact idempotency, quotas, lease state, artifact
  metadata schema and audit, but makes no false browser-completion claim.
- External callers cannot choose site/workspace/origin/absolute URL/viewport/
  run ID or retrieve another run/artifact.
- Agent runtime has only narrow browser functions; browser worker remains
  unchanged, DB-less, and health-only in this foundation round.
- Run credentials are correctly signed/bound/verified and never public or
  available to the worker as a signing secret.
- Fake unauthenticated browser responses are removed; all public routes use real
  capability auth and stable errors.
- Full prior Agent/Render/Puck/Media behavior and all required CI remain green.
- The immutable 072-a short-SHA defect is append-only corrected in the 072-b
  report using the literal parent
  `c31b0bb8bb357ed5e3f1398ac02369f5c76c9830`.

## Verification, documentation, and workflow

Run and report focused contracts/signer/policy/routes tests; real PostgreSQL
capability/idempotency/quota/lease/race/privilege tests; full backend unit/
repository/integration; CI-scope Ruff/format/Mypy/build/process; complete Node
gates; migration head/upgrade/downgrade and PostgreSQL 14–18; static Compose/
edge/secret/mount policy and clean Compose without browser claims; Markdown/
Mermaid; supply-chain; and every fresh GitHub required check.

Update API, authorization, configuration, database roles/connections, service
authority, security, testing, operations, and browser contract docs only for
the durable foundation now implemented. Keep browser worker, screenshot,
artifact bytes, confinement, and readiness documented as pending until the
next continuation proves them.

Commit/push the exact strategic 072-b order and active bytes unchanged on
PR #66, then bounded implementation/tests/docs. The final 072-b report should use
`PARTIAL` for the numeric objective while stating whether every 072-b criterion
is complete; no acceptance/merge is implied.

Publish exactly `oap/reports/072-b-durable-browser-run-control-plane.md` as one
report-only child with `Report publication commit: SELF` and a literal 40-hex
implementation parent. Verify remote PR/head/parent/path, then signal exact
FIFO `OK`. Do not merge.

The report must state PR/base/branch/all full SHAs; the 072-a append-only SHA
correction; exact schema/functions/grants; contract/routes/idempotency/quota/
lease/race/signer evidence; worker-still-stub limitations; files/dependencies/
migration/docs; every local/CI result/intermediate failure; no extra PR; and no
merge.
