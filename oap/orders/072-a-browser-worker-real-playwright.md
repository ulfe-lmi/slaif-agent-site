# OAP Work Order — 072-a

## Objective

Create exactly one Objective 072 PR that replaces the health-only browser
worker and fake browser routes with a real, confined Playwright Chromium
preview runner. An authenticated Agent capability must request a bounded,
idempotent, durable preview run; Agent API must derive site/workspace/route and
mint a short-lived run-bound preview credential; the database-free worker must
open only that authorized preview in a fresh context, collect curated
diagnostics, store immutable private artifacts, destroy the context, and return
results only through capability-authorized Agent API routes. Prove network,
credential, artifact, quota, cancellation, and cross-site isolation through
real PostgreSQL, public NGINX, the production worker image, and actual browser
execution. Do not implement source crawling, review, or publication. Do not
merge.

## GitHub objective state and verified starting point

- Numeric objective: `072`; round: `072-a`.
- Mode: `CREATE_NEW_PR`; create exactly one new Objective 072 branch and PR
  from remote main
  `082f2359b0c4d59b692580d17992c35d46183b12`.
- Objective 071 PR #62 is merged. Its final report head
  `ea2717a980fafd2d74edc51bad0e668dd1b98da7` is contained by main.
  No Objective 072 PR exists; reconcile GitHub again before mutation.
- `services/browser-worker` is a Node health-only server. Its Alpine image has
  no Playwright package or browser binary and no runtime artifact volume.
- `packages/browser-tool-contracts` is metadata-only. The Python
  `browser_worker/browser_http.py` mounted into Agent API accepts caller-chosen
  workspace/route/targets, performs no capability authentication, queues
  nothing, launches no browser, and returns fabricated completion.
- Agent capability authentication, COW writes/reads, idempotency, and fixed
  runtime identity are real. Capability/workspace tables do not yet carry
  browser limits or browser-run/artifact records.
- Objective 071 provides authenticated human preview plus typed Render
  projection and shared SSR. It does not provide a browser-run credential and
  correctly forbids the worker from receiving a human cookie or Agent token.
- Compose places Agent API and browser worker on an internal browser network;
  the worker has no database secret/network, host mount, Docker socket, or
  edge exposure. It also cannot yet reach a dedicated preview origin.
- Root Playwright `1.62.1` is currently test-only; supply-chain documentation
  explicitly states that the product browser-worker image contains no browser
  binary and must be deliberately requalified when runtime browsing exists.

## Required trust flow

```text
Agent capability
  -> public NGINX
  -> Agent API authentication/scope/quota/idempotency
  -> durable site/workspace-bound browser run
  -> short-lived signed run credential and internal service request
  -> database-free browser worker
  -> fresh confined Chromium context
  -> dedicated internal Web preview origin
  -> private immutable artifacts and bounded diagnostics
  -> authenticated Agent API status/artifact retrieval
```

- External callers provide only a normalized site-relative route, one supported
  target, and a bounded allowlist of curated result types. They never provide
  site ID, workspace ID, absolute URL/origin, internal credential, browser
  command, JavaScript, artifact path, or database operation ID.
- Agent API derives capability/site/workspace and all quotas from trusted
  database context. The client idempotency key is not a run UUID.
- Browser worker receives no Agent capability, human session/cookie, database
  locator, reviewer/setup identity, signing key, or publication authority. It
  receives only one opaque run-bound preview credential plus internal request
  authentication and bounded job data.
- Browser output is advisory evidence only. Success cannot freeze, review,
  accept, publish, mutate content, or execute an external side effect.

## Bounded scope and non-goals

Change only browser contracts, Agent browser orchestration/routes/database
adapter, one forward migration, preview run-credential verification in
Web/Render, worker runtime/image/artifact store, isolated secret/volume/network
wiring, directly necessary docs, and focused/unit/integration/E2E/packaging/
supply-chain tests.

- No source-origin crawling/fetching, DNS allowlist UI, private institutional
  origins, downloads, authenticated source sites, or `source:inspect` behavior.
- No full six-target responsive sweep. Runtime may implement the named Chromium
  desktop/tablet/mobile targets; Firefox/WebKit remain CI-only unless exact
  evidence proves a deliberate runtime addition. Do not claim more.
- No raw Playwright API, arbitrary URL/navigation, `page.evaluate` exposed to
  callers, shell, file URL, JavaScript expression, extension/plugin, persistent
  browser profile, arbitrary request headers/cookies, trace/video/download, or
  unrestricted DOM retention.
- No human browser artifact UI, review-snapshot attachment, freeze, acceptance,
  discard, promotion, publication, public artifact/media URL, artifact GC
  deletion, distributed queue/backend, or multi-node claim.
- No database role or DB network/mount in browser worker. No reviewer, setup,
  Control, Editor, Render DSN, host filesystem, Docker socket, or edge network.
- Do not alter migrations 006 through 034. Add deterministic forward migration
  035 only, with one Alembic head.
- No hosted browser/service, telemetry, account-bound runtime, unpinned browser,
  mutable base image, or unreviewed license/dependency.

## 1. Public Agent browser contract

Replace the fake internal router on Agent API with capability-authenticated
semantic routes under `/api/agent/v1/`:

- create a preview run;
- get one run status/result;
- list that run's bounded artifact metadata; and
- retrieve one artifact through authenticated streaming when still retained.

Use typed extra-forbid request/response schemas and stable error envelopes.
Require `preview:inspect`; require `Idempotency-Key` on run creation; apply the
same capability lifecycle/site/workspace recheck and shared workspace lock
discipline as accepted Agent operations. Same key+digest returns the same run;
same key+different request returns 409. Missing/invalid auth/key is 401/400,
scope denial 403, invisible foreign run/artifact 404, quota/concurrency 429,
invalid route/target/schema 422, and temporary worker/storage failure 503.

The request may contain only:

- normalized product route relative to the capability's site;
- one runtime-supported stable target from the shared target map;
- requested curated artifacts/diagnostics from an exact allowlist; and
- bounded optional wait/poll preference that cannot exceed server policy.

Reject absolute/scheme-relative URLs, authority/host, traversal, reserved app/
internal/API paths, query credentials, fragments, duplicate/unknown fields,
oversized body, unsupported target/artifact, and any caller site/workspace/run/
origin/viewport dimensions.

## 2. Durable run, job, idempotency, quota, and audit state

Add migration 035 for bounded `control.browser_run`, `control.browser_artifact`,
browser idempotency/job state, and append-only `audit.browser_event` as needed.
Use UUIDs, immutable site/workspace/capability/delegator association, normalized
route/target, request digest, state, attempts/lease, summary, error code,
artifact counts/bytes, timestamps/expiry, and strict constraints/indexes.

- Run states are explicit and monotonic, such as QUEUED, RUNNING, COMPLETED,
  FAILED, TIMED_OUT, and CANCELLED. No client may choose or mutate state.
- Create run, reserve browser/screenshot/artifact quotas, idempotency mapping,
  durable job, and semantic/browser audit atomically or not at all.
- Claim/lease uses a narrow owner-defined function with `FOR UPDATE SKIP LOCKED`
  and permits only preview jobs. Multiple Agent API replicas cannot execute the
  same run concurrently. Expired leases may retry with a fresh context under a
  bounded attempt count; terminal runs never retry or widen policy.
- Agent runtime receives only exact browser enqueue/claim/complete/read
  functions required for this orchestration, not generic job/browser tables,
  arbitrary Control updates, scheduler, reviewer, setup, or artifact-GC
  authority. Browser worker receives none of these grants.
- Add explicit immutable capability browser limits (run count, screenshots,
  artifact bytes, routes/targets, concurrency, duration) with conservative
  defaults and persist/evaluate them server-side. Extend trusted capability
  context; never trust request limits. Existing capabilities receive bounded
  defaults through migration.
- Completion metadata is accepted only for the exact leased run and signed
  internal worker response; the database rechecks capability/workspace/site
  state before making results visible. A freeze/revoke/expiry while queued or
  running prevents a result from becoming newly retrievable.
- Browser reads/runs never create COW content operations and never use content
  mutation idempotency/audit tables.

The browser worker remains DB-less. A bounded dispatcher owned by Agent API or
another existing Agent-authority process may claim preview jobs and call the
worker. It must be restart-safe: queued/expired-lease runs remain durable and
are recovered/retried without an in-memory-only authority decision. Do not add
a new DB credential to the worker to simplify dispatch.

## 3. Run-bound preview and internal authentication

Add generated, file-backed secrets with exact ownership/mode/no-symlink policy:

1. Agent API-to-worker request/callback authentication, available only to those
   processes and one-shot initialization; and
2. a preview-run signing key available to the trusted Agent API signer and
   Web/Render verifiers, but not to the browser worker.

After run creation, Agent API mints a short-lived opaque or signed credential
bound to deployment, site, workspace, capability, run ID, normalized route,
target, expiry, nonce, and artifact policy. The worker may present it only in a
dedicated internal header when loading the fixed preview origin. It cannot
change any bound field or mint another token.

- Add a browser-preview authorization path to Web/Render separate from human
  preview. It validates the run credential before choosing COW context and
  rechecks current capability/workspace/site/run state under the workspace
  shared lock on the projection transaction.
- The browser receives neither Agent Authorization header nor human cookie.
  The run token never enters URL, HTML, DOM, screenshot, accessibility/DOM
  artifact, console, request log, browser storage, referrer, or returned body.
- Internal service auth is startup-validated, descriptor-confined, constant-
  time, and rejects missing/empty/duplicate/wrong credentials before body use.
  No test-mode or empty-secret bypass may support a runtime claim.
- Use one fixed internal preview base URL configured by operator/deployment and
  combined server-side with the normalized route. Caller input never becomes
  an origin or absolute URL.
- Web/Render must not expose a general signed-preview endpoint or let a browser
  token authorize human/Agent API/database routes.

## 4. Real Playwright worker and bounded execution

Use one exact Playwright package/browser/image release, pinned by package lock
and immutable OCI digest, compatible with project Node policy. Update image
SBOM/license/NOTICE/vulnerability and platform qualification. No browser
download occurs at runtime.

Implement internal service-authenticated worker routes only:

- submit one preview run;
- inspect one run for dispatcher/recovery;
- retrieve one private artifact for authenticated Agent API proxying; and
- health/live/readiness that verifies browser executable, sandbox/launch,
  artifact store, target map, service auth, and confinement marker.

For every attempt:

- create a fresh browser and isolated context with no persistent profile,
  cookies, service worker, permissions, downloads, or prior storage;
- map the named target from one shared immutable descriptor table; callers
  cannot provide viewport/device values;
- attach the run credential only to the authorized preview origin, navigate
  one bounded route, wait for an explicit stable page condition, and apply
  navigation/action/total timeouts;
- collect only requested curated evidence: PNG screenshot; bounded accessible
  role/name snapshot; sanitized structural/heading/link/media/overflow summary;
  console error/warning summaries; and failed request URL class/status without
  bodies or credentials;
- redact sensitive query/header/cookie/token data and bound strings, entries,
  DOM depth, URLs, bytes, screenshot dimensions, and total artifacts;
- close page/context/browser and remove temporary files on success, timeout,
  navigation failure, disconnect, cancellation, callback failure, and process
  shutdown; every retry uses a fresh context; and
- return a stable typed summary. It never returns arbitrary DOM, HTML, browser
  handles, raw response bodies, storage state, or executable data.

Bound runtime configuration for maximum concurrent contexts, queue depth,
attempts, run duration, navigation timeout, screenshot count, per-artifact and
per-run bytes, route count, and worker memory/PIDs. Reject overload before
browser launch with 429/typed internal result. A hung run is killed within the
bounded deadline without leaving Chromium processes.

## 5. Private immutable artifact store

Mount a dedicated private browser-artifact volume only to browser worker and
one-shot ownership initialization. Do not reuse public Media or private Media
upload paths. Store artifacts under server-derived site/workspace/run/type/
target and SHA-256 identity using descriptor-confined no-follow operations,
exclusive staging, no-replace publication, restrictive owner/mode, fsync, and
bounded race handling equivalent to accepted immutable Media principles.

- Artifact metadata records digest, size, MIME, type, target, route digest,
  created/expiry, and run/site/workspace; never absolute path.
- Existing valid digest reuse is verified; symlink, non-regular, extra-hardlink,
  corrupt, wrong-size/digest/mode/owner, ancestor replacement, and traversal
  fail closed without overwrite.
- Failed database completion may leave only a private unreferenced artifact for
  later GC. Do not implement physical artifact GC in this objective.
- Agent API retrieval reauthenticates current capability and exact run/site/
  workspace visibility, checks retention, and streams through an authenticated
  internal worker call with no direct volume mount or edge path. Wrong/expired/
  foreign IDs return non-leaking 404.
- Artifacts are never promoted to site Media, made public, served by NGINX, or
  used as publication authority.

## 6. Browser network and process confinement

Keep browser worker non-root, read-only root, dropped capabilities, bounded
tmpfs/resources, no Docker socket, host/repository mount, DB/Control/Render/
reviewer secret, and no edge exposure. Add only narrowly necessary internal
networks for Agent control and fixed Web preview origin.

- Browser requests are intercepted/default-denied. Permit only the exact Web
  preview origin and same-origin Next/static/product requests required by that
  page. Recheck every redirect; deny extra hosts/schemes/ports and credentials.
- Explicitly deny loopback, link-local, metadata, host gateway, private Docker
  service names except the one preview origin, Agent API, browser worker,
  Control, Editor, Render, Media internal service, PostgreSQL, Docker API,
  `file:`, `data:` navigation, WebSocket, downloads, and external Internet.
- Do not rely solely on hostname substring checks. Normalize URL, credentials,
  scheme, host, port, DNS/IP class, redirects, and encoded forms. The fixed
  Compose service origin may be allowed by exact operator configuration; that
  does not permit caller-selected private hosts.
- Prove browser JavaScript/navigation cannot reach Agent API even though worker
  control traffic may share a network. Product service-auth headers are never
  exposed to page requests.
- Readiness fails if Chromium cannot launch sandboxed, artifact ownership is
  wrong, default-deny interception is absent, or required fixed origin is
  invalid.

## 7. Contracts, tests, and observable proof

Replace scaffold contracts with versioned typed run/target/artifact/diagnostic
schemas shared between Agent API and worker. Reject unknown versions/fields and
test serialization parity. Update OpenAPI/API-client/MCP documentation only for
implemented Agent REST behavior; MCP tool implementation may remain later but
must not claim availability.

Required executable proof includes:

1. real capability through public NGINX creates a preview run with exact scope,
   idempotency, site/workspace, quotas, and durable QUEUED/RUNNING/terminal
   transitions; status survives Agent API/worker restart or lease recovery;
2. production worker image launches real Chromium, renders the Objective 071
   workspace preview, returns a nonempty valid PNG plus requested bounded
   accessibility/diagnostic artifacts, and closes all contexts/processes;
3. screenshot/diagnostic digest, size, MIME, metadata, path confinement,
   private modes, fsync, retrieval bytes, and database rows agree; no public
   route or direct volume access exists;
4. same idempotency digest returns one run/artifact set; mismatch 409;
   concurrent duplicate dispatch executes once; quota/concurrency/queue/artifact
   limits fail with no partial durable or filesystem state;
5. missing/wrong scope, revoked/expired capability, frozen/revoked/expired
   workspace, wrong site/workspace/capability/run/artifact, forged run token,
   expired token, wrong route/target, replayed credential, and callback forgery
   fail closed without cross-state or artifact visibility;
6. deterministic freeze/revocation race pauses run creation/dispatch/completion
   under the shared workspace lock, changes authority, resumes, and proves no
   newly visible result/audit mismatch;
7. hostile route/url matrix rejects absolute, scheme-relative, userinfo,
   encoded traversal, fragment/query token, localhost variants, IPv4/IPv6,
   metadata/link-local/private, DNS/redirect escape, file/data/javascript,
   internal service names, arbitrary headers/cookies, and unsupported targets;
8. browser-page probes fail to reach PostgreSQL, Agent/Control/Editor/Render/
   Media internal endpoints, worker control API, Docker/host/filesystem, and
   public Internet, while the exact preview and required same-origin assets
   succeed;
9. two sequential runs prove no cookie/local/session storage/cache/service-
   worker/permission/context leak; cancellation, timeout, crash/retry, failed
   navigation, oversized artifact, disconnect, and shutdown leave no Chromium,
   temp file, token, lease, or pool bleed;
10. clean Compose exposes only NGINX, worker has no DB secret/network/mount,
    worker readiness proves real browser/confinement, and the public Agent run
    journey plus authenticated artifact retrieval works byte-for-byte; and
11. PostgreSQL 14–18, all Node/Python/repository/package/security/license/SBOM/
    vulnerability gates, and existing Puck/Render/Media/Agent tests remain
    green. CI failure artifacts stay private and do not become product output.

Use real PostgreSQL identities, actual production worker image/browser, public
NGINX for Agent requests, and the internal preview route for Chromium. Unit or
mock-only browser proof is insufficient.

## Acceptance criteria

- Browser worker is a real pinned Playwright runtime, not a health stub, and has
  no database, capability, human-cookie, signing, reviewer, host, Docker, or
  publication authority.
- Agent capability can request and retrieve only its own bounded preview run and
  private immutable artifacts; site/workspace/quota/idempotency are server-owned.
- The worker can navigate only the exact run-bound preview origin/route in a
  fresh context and cannot reach internal/private/external targets.
- Screenshot and diagnostics are real, bounded, redacted, digest-verified,
  private, retained, and never public Media or publication authority.
- Durable state survives restart/lease retry without duplicate execution or
  in-memory-only authority; all failure/cancellation paths clean resources.
- Existing human preview, canonical render, Agent COW, Puck, Media, edge, and
  security behavior remains green with no source/sweep/review/promotion scope.

## Verification, documentation, and workflow

Run and report focused contract/policy/credential/URL/artifact/store/worker/
dispatcher tests; real Agent API/PostgreSQL/queue/idempotency/quota/race tests;
actual worker-image Chromium integration; clean Compose public-NGINX Agent run
and private artifact retrieval; process/context/network cleanup; all backend
unit/repository/integration gates; CI-scope Ruff/format/Mypy/build/process;
complete Node gates; browser/image SBOM/license/vulnerability/reproducibility;
PostgreSQL 14–18; Markdown/Mermaid; and every fresh GitHub required check.

Update API, browser contracts, configuration, service authority, security,
deployment, operations, testing, scaling, supply-chain, license/NOTICE, and
user-facing implemented-versus-planned text exactly where behavior changes.
Document runtime-supported targets and limitations honestly. Do not claim
source crawling, six-target runtime sweep, artifact GC, review integration,
publication, distributed scale, or production readiness.

Create one fresh Objective 072 branch and PR from exact remote main. Commit the
exact strategic 072-a order and `oap/active` bytes unchanged, then bounded
implementation/tests/docs. Push all non-report work, inspect and safely repair
only in-scope failures, and never merge or enable auto-merge.

Publish exactly `oap/reports/072-a-browser-worker-real-playwright.md` as one
report-only child with `Report publication commit: SELF`. Its first parent must
be the literal implementation-head SHA. Verify remote PR/head/parent/path, then
signal exact FIFO `OK`.

The report must state `COMPLETE|PARTIAL|BLOCKED|FAILED`; PR/base/branch/all
SHAs; exact external/internal flow; roles/grants/job/idempotency/quota and run
state chronology; credential claims and mounts; target/URL/network policy;
browser/image/package versions/digests/licenses/SBOM; artifact store state;
site/workspace/race/restart/cancellation evidence; files/dependencies/migration/
docs; every local/CI result/intermediate failure; limitations/non-goals; no
extra PR; and no merge.
