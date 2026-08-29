# OAP Work Order — 072-d

## Objective

Continue Objective 072 on PR #66. Wire the completed 072-c durable browser-run
foundation into real capability-authenticated Agent HTTP create/status/artifact-
metadata routes, remove the fabricated browser router, and implement the
file-backed run-bound preview credential signer plus Web/Render verification
path needed by the future worker. Runs must remain truthfully QUEUED and no
artifact bytes may exist until the next worker/dispatcher continuation. Do not
implement Playwright or merge.

## Verified starting state

- Numeric objective: `072`; round: `072-d`.
- Mode: `AMEND_EXISTING_PR`; amend only PR #66 on
  `oap/072-browser-worker-real-playwright`. Create no new PR.
- Begin from verified remote 072-c report head
  `449eeca6ded72be9f7059443c9a9a2989ebfee24`; its sole parent is
  implementation head `2505a98120e26f9fee3ea8d52fb291997ae676b4`
  and its sole changed path is
  `oap/reports/072-c-browser-contracts-and-durable-schema.md`.
- Remote main remains
  `082f2359b0c4d59b692580d17992c35d46183b12`; PR #66 is open and
  mergeable. Reconcile live GitHub before mutation.
- 072-c is genuine and retained: versioned cross-language contracts, migration
  035, capability browser limits, durable run/idempotency/lease/artifact
  metadata/audit state, exact Agent functions, revoked generic Agent table
  reads, and real PostgreSQL 14–18 proof are green.
- Agent API still mounts the fake Python `/internal/browser/v1` router and has
  no public preview-run routes. Browser worker remains health-only. No browser
  signing secret, browser-preview token, Web/Render browser-token path, worker
  dispatch, or artifact bytes exist.

## Bounded scope and deferrals

Change only Agent browser service/routes/database adapter, run credential
models/signer/config, Web/Render browser-preview verification, migration 036 if
a narrow Render authorization function is needed, secret initialization/
isolated mounts, shared contracts needed by these routes, focused tests, and
exact API/config/security/deployment/testing docs.

Do not change browser-worker source/image/package, add Playwright, mount an
artifact volume, create worker internal routes, dispatch/claim jobs, write
artifact bytes, expose artifact retrieval bytes, alter browser networks, or
claim browser execution. Those remain next same-PR rounds. No dependency or
lockfile change.

No source crawling, responsive sweep, review/promotion/publication, public
artifact/media URL, artifact GC, worker DB, extra PR, or merge. Do not edit
migrations 006–035 or prior activated orders/reports; add only forward migration
036 if required.

## 1. Capability-authenticated public Agent routes

Add typed routes under `/api/agent/v1/preview-runs`:

- `POST` create one durable run;
- `GET /{run_id}` return one current status/result;
- `GET /{run_id}/artifacts` list retained private artifact metadata; and
- `GET /{run_id}/artifacts/{artifact_id}` reserve the future byte retrieval
  contract but return non-leaking 404 while no worker bytes exist.

Use the real Agent capability middleware/context and migration 035 functions.
Require `preview:inspect` and `Idempotency-Key`; validate body through the
shared `browser-preview/v1` contract; derive capability/site/workspace/
delegator/limits and request digest server-side. The public request must not
contain authority IDs, absolute URL/origin, viewport, internal credential,
lease, run ID, header/cookie, or browser command.

Map durable outcomes exactly: STARTED/QUEUED returns 202, REPLAY returns the
same run/body without double reservation, MISMATCH 409, quota/concurrency 429,
scope 403, auth 401, malformed/key 400, schema/route/target 422, invisible 404,
database unavailable 503. Status and artifact metadata reads create no browser
event, idempotency, quota, or COW content operation.

Foreign/random/revoked/expired capability/site/workspace/run/artifact lookups
are non-leaking 404 or current auth failure. Never include worker URL, token,
lease, SQL, role, request digest, signer key, or foreign ID in a response/log.

Remove `browser_worker.browser_http` from Agent app and delete/retire its fake
queued/completed responses. No unauthenticated `/internal/browser/v1` route may
remain on Agent API. Internal worker routes belong only to the future Node
worker and remain absent this round.

## 2. Agent browser service and truthful no-worker behavior

Implement a typed Agent-side service around the migration 035 functions. It
must own validation, idempotency digest, begin/replay/mismatch, current status,
artifact metadata list, stable error mapping, and pool cleanup. It may expose
claim/complete adapter methods for tests/future dispatcher but must not start an
in-memory/background dispatcher or mark runs RUNNING/terminal in production.

Publicly created runs stay QUEUED. A missing worker is not a completed empty
result. Status remains durable across Agent API restart. Artifact list is empty
until exact metadata is registered through tested internal adapter functions;
byte retrieval remains 404. Health/readiness must not claim worker readiness.

Add deterministic real HTTP tests for create/replay/mismatch/quotas, restart,
two sites/workspaces/capabilities, scope/revoke/expiry/freeze race, status/list/
retrieval isolation, fake route absence, no COW residue, and exact row/audit/
quota counts. Use public NGINX in clean Compose for at least one real capability
create/poll journey.

## 3. Run-bound preview credential signer

Add one generated high-entropy file-backed signing key available only to Agent
API and Render verification, plus one-shot initializer. Web and browser worker
must not receive the signing key. Validate directory/file regularity, no symlink,
owner/mode, bounded ASCII/bytes, algorithm/version and startup readiness through
descriptor-confined reads. No plaintext environment key in production.

Implement an immutable signer/verifier with fixed HMAC algorithm and audience.
The token binds:

- deployment/audience and contract version;
- capability/site/workspace/run IDs;
- normalized route and target;
- evidence/artifact/duration limits;
- issued-at, short expiry, nonce and key identifier.

Use canonical serialization. Reject missing/duplicate/malformed/oversized,
unknown algorithm/version/key/audience, future/expired, wrong-signature,
replayed nonce where single use is required, and any changed binding in constant
time. Never store plaintext token in database, public response, URL, log, error,
report, screenshot, DOM or browser storage. The future dispatcher must mint it
from current durable run facts immediately before worker submission; public
create must not return it.

Provide deterministic Python test vectors and a neutral verifier contract for
Render. No browser-worker signing or verification exists yet.

## 4. Web/Render browser-preview verification path

Extend the Objective 071 preview path with a separate internal browser-token
mode while preserving human preview unchanged:

- a browser navigation may present the signed run token only in one dedicated
  header to Web;
- Web forwards it server-side to Render and never serializes/stores/logs it;
- Render verifies signature and all route/site/workspace/run bindings using the
  startup-loaded signing key;
- Render calls one narrow owner-defined migration 036 function through the
  preview role to recheck current capability/workspace/site/run state and
  `preview:inspect` under the workspace shared advisory transaction lock before
  selecting COW context; and
- only QUEUED/RUNNING exact unexpired runs may project. Terminal, foreign,
  revoked/expired/frozen/mismatched state is non-leaking denial.

Browser-token mode receives no human cookie or Agent capability. Human mode
continues using its existing session semantics. The token cannot authorize
Control/Editor/Agent/Media/internal Render APIs, another route, or another
workspace. No public URL contains it.

Do not navigate or execute a browser in this round. Unit and integration tests
may call the Web/Render path with deterministic fake signed tokens and real
PostgreSQL to prove overlay/canonical binding, expiry/tamper/foreign denial,
shared-lock race recheck, no COW residue, and human-preview regression.

## 5. Secret and Compose boundaries

Generate/mount the signing key only to Agent API and Render via isolated
read-only process-owned volumes; initializer alone may write. Web, worker,
NGINX, Control, Editor, Media, MCP, scheduler, reviewer and GC receive no key.
Existing Agent/Render DB and service secrets remain isolated. Update Compose
policy, secret tests, readiness failure/recovery and docs; only NGINX publishes.

No Agent capability, human cookie, Render service token or signing key may be
reused as another credential. Missing/bad signing key blocks Agent browser-run
signer readiness and Render browser-preview readiness without weakening normal
human preview or canonical public rendering.

## 6. Acceptance and proof

- Real public Agent routes create one durable QUEUED run with exact
  idempotency/quota/audit behavior and survive restart; no fake completion or
  artifact bytes are claimed.
- Every route is capability/site/workspace confined; foreign/random IDs and
  missing scope/revoked/expired/frozen authority fail closed with zero residue.
- Fake unauthenticated Agent browser routes are absent.
- Run tokens are startup-keyed, short-lived, fully bound, constant-time
  verified, never public/persisted plaintext, and cannot be widened/replayed.
- Real Render preview with a valid token sees only the bound workspace overlay;
  human preview and canonical state remain unchanged; tamper/expiry/route/site/
  run/capability races deny under lock.
- Signing key mounts and failure/recovery are exact; worker remains unchanged,
  health-only, DB-less, and without signing key or browser claim.
- Numeric Objective 072 remains PARTIAL after this route/credential round.

Run focused route/service/signer/config tests; real PostgreSQL Agent/Render/
race/isolation tests; full backend unit/repository/integration; CI-scope Ruff/
format/Mypy/build/process; complete Node gates; migration head/downgrade and
PostgreSQL 14–18; static and clean Compose secret/edge/restart regression;
Markdown/Mermaid; supply-chain; and every fresh GitHub required check. Record
all failures/retries/skips/not-run honestly.

Update API/auth/config/database-role/service-authority/security/deployment/
testing docs for implemented routes and credential verification. Continue to
state that worker execution, Playwright, artifacts, dispatch, confinement and
browser E2E are pending.

Commit/push the exact strategic 072-d order and active bytes unchanged on
PR #66, then bounded implementation/tests/docs. Publish exactly
`oap/reports/072-d-agent-browser-routes-and-preview-credential.md` as one
report-only child with `Report publication commit: SELF` and literal 40-hex
implementation parent. Report status remains `PARTIAL` for Objective 072 while
stating exact 072-d completion. Verify remote parent/path/head, signal exact
FIFO `OK`, and do not merge.

The report must state PR/base/branch/all SHAs; route/error/idempotency/quota/
isolation counts; signer/token/secret/mount and Render COW race evidence;
worker-still-stub limitations; files/dependencies/migrations/docs; every local/
CI result; no extra PR; and no merge.
