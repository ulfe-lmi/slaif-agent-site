# OAP Work Order — 072-f

## Objective

Continue Objective 072 on PR #66. Replace the health-only Node browser-worker
placeholder with a real, pinned, confined Playwright Chromium worker that can
execute one internally authenticated preview attempt, collect only curated
bounded evidence, persist immutable private artifacts, and return a signed typed
result to an Agent-side client. Qualify this worker directly against the real
Web/Render COW preview path and production image. Do not yet dispatch, claim,
complete, or expose public Agent runs; those durable orchestration and public
retrieval steps remain the final same-PR continuation. Do not merge.

## Verified current state

- Numeric objective: `072`; round: `072-f`.
- Mode: `AMEND_EXISTING_PR`; amend only PR #66 on
  `oap/072-browser-worker-real-playwright`. Create no new PR.
- Begin from verified remote 072-e report head
  `76e0f0a45dc8120ace8b7b7c4c5a29b29398ab4a`; its sole parent is
  implementation head `eb5c7d51fcbeee98251c63f427fdb806db6a0ac1`
  and its sole changed path is
  `oap/reports/072-e-canonical-browser-token-encoding.md`.
- Remote main remains
  `082f2359b0c4d59b692580d17992c35d46183b12`; PR #66 is open,
  non-draft, and mergeable. Reconcile live GitHub and require the 072-e
  report-head checks to be fully green before mutation.
- Rounds 072-c through 072-e are genuine and retained: versioned browser
  contracts, durable migration-035 run/artifact state, least-privilege Agent
  functions, public capability-authenticated queued-run routes, canonical
  run-bound preview credentials, migration-036 Render authority, Web/Render COW
  projection, and isolated signing-key mounts.
- `services/browser-worker` remains a Node health stub on a pinned Alpine base.
  It has no Playwright dependency, Chromium binary, service credential,
  execution route, artifact volume, target policy, or confinement readiness.
  Public Agent-created runs therefore remain truthfully `QUEUED`.
- Root E2E uses exact `@playwright/test==1.62.1`; `playwright` and
  `playwright-core` 1.62.1 are already frozen transitively, but the product
  worker declares no runtime dependency and the current supply-chain policy
  correctly requires an empty worker browser inventory. Deliberately requalify
  the product worker rather than silently inheriting the test dependency.

## Required trust boundary for this round

```text
direct trusted Agent worker client
  -> isolated file-backed internal service credential
  -> internal browser-worker request
  -> opaque canonical run-bound preview credential
  -> fresh confined Chromium browser/context/page
  -> fixed operator-owned Web preview origin
  -> Render workspace COW projection
  -> curated bounded evidence
  -> immutable private worker-only artifact volume
  -> signed typed worker response and authenticated internal byte retrieval
```

The public Agent route is deliberately not connected to this flow yet. The
worker receives no Agent capability, human cookie/session, database locator,
preview signing key, reviewer/setup identity, publication authority, arbitrary
URL, arbitrary header/cookie, browser command, JavaScript, viewport, or path.

## Bounded scope and non-goals

Change only the browser-worker package/runtime/image, exact shared internal
worker contracts and target descriptors, an Agent-side worker client that is
not scheduled or invoked by public routes, one-shot worker-service secret and
artifact-volume initialization/mounts, worker confinement/network/resource
policy, directly necessary supply-chain/license/config/security/operations docs,
and focused/unit/integration/Compose/image tests.

Do not change migration 035 or 036, database functions/grants/roles, durable run
state, Agent capability authentication, public Agent route behavior, Web/Render
credential semantics, token claims/TTL/nonce, COW behavior, Puck, Media, review,
promotion, or publication.

Do not add an Agent background task, dispatcher loop, job claim/renew/release,
database completion/artifact registration, public artifact byte retrieval,
lease recovery, artifact GC, source crawling, source origins, a six-target
runtime sweep, Firefox/WebKit product binaries, hosted browser/service,
telemetry, another PR, or merge. Public runs must still remain `QUEUED` after
this round.

## 1. Exact product Playwright runtime

- Declare one exact production worker dependency compatible with the existing
  frozen Playwright 1.62.1 contract. Do not use a range, mutable browser
  download, or runtime install. The lockfile may change only to materialize the
  browser-worker importer and directly required exact packages; explain every
  lock delta.
- Build from an immutable digest-pinned compatible OCI base and bake exactly the
  required Chromium binary and OS libraries into the worker image. No browser,
  npm package, or OS package download may occur at runtime.
- Keep Node 24 policy compatibility. Run as the existing dedicated non-root UID,
  use a read-only root filesystem, dropped capabilities, no-new-privileges,
  bounded writable tmpfs, explicit PID/memory/CPU/shm limits, and no host,
  repository, Docker socket, database network, or unrelated secret mount.
- Launch Chromium with its sandbox enabled. Do not add `--no-sandbox`, disable
  site isolation, expose debugging ports, install extensions/plugins, or grant
  broad Linux capabilities merely to make the browser start. If the pinned
  runtime cannot pass a real sandboxed launch under this boundary, stop and
  report the exact blocker rather than weakening confinement.
- Update browser/image inventory, license/NOTICE, SBOM, vulnerability,
  reproducibility, and repository policies from the old empty-browser claim to
  the exact qualified Chromium/package facts. Firefox and WebKit remain absent
  from the product worker.

## 2. Internal service authentication and contracts

- Add one high-entropy one-shot file-backed worker-service credential available
  only to Agent API and browser worker. Initializer alone writes it; both
  runtime mounts are read-only. Web, Render, Control, Editor, Media, MCP,
  reviewer, scheduler, GC, NGINX, and browser page receive no copy.
- Validate the secret with descriptor-confined regular-file, owner, mode,
  no-symlink, exact format/length, and startup readiness checks. No plaintext
  environment secret, test-mode bypass, empty-secret fallback, logging, or
  reflection is allowed.
- Authenticate missing/empty/duplicate/malformed/wrong credentials in constant
  time before reading or parsing a request body. Bound request bytes and reject
  ambiguous transfer/content-length framing.
- Version exact extra-forbid submit, active-run inspection, typed result, signed
  response, artifact metadata, and artifact-byte retrieval contracts shared by
  the Agent client and worker. Bind request/response to deployment, request ID,
  run/site/workspace/capability/operation/lease attempt, route digest, target,
  evidence, artifact and duration policy, timestamp/expiry, and the opaque
  preview credential. The worker never parses or verifies preview-token claims.
- Authenticate the worker result cryptographically with the internal service
  secret and require the Agent client to verify the exact request/result body
  binding before accepting it. Stable errors and logs contain no credential,
  token, nonce, URL query, filesystem path, SQL, role, or foreign identifier.
- Production may contain the bounded Agent client/configuration for this
  protocol, but no route, lifespan task, timer, or startup hook may call it in
  this round.

## 3. Real bounded execution

Implement internal worker routes for one authenticated preview attempt, bounded
active-attempt inspection, exact private artifact retrieval, and live/ready
health. These routes are internal only and must not be edge-routed.

For each accepted attempt:

- Reject overload before browser launch using fixed conservative maximum active
  contexts and queue depth. Bind navigation, action, and total deadlines; bound
  request bytes, output strings/items, screenshot count/dimensions, per-artifact
  and total bytes, and worker process/PID usage.
- Map only `desktop-chromium`, `tablet`, and `mobile-chromium` through one shared
  immutable descriptor table. No caller viewport/device override is accepted.
- Start a fresh sandboxed browser and isolated context with no persistent
  profile, prior cache/storage, cookies, permissions, service workers,
  downloads, trace, video, extension, or reused page. Each retry is a new
  browser/context.
- Construct the navigation URL from one startup-validated fixed internal Web
  preview base origin plus server-derived workspace/route facts. Caller input
  never becomes an origin or absolute URL.
- Attach `X-SLAIF-Browser-Preview` only to the exact initial authorized preview
  document request. Never attach internal service auth, Agent auth, cookies, or
  arbitrary headers to any page request. Strip the preview credential from
  redirects and subresources, and never place it in a URL, DOM, referrer,
  storage, screenshot, diagnostic, console entry, artifact, result, or log.
- Wait for an explicit production page-stability condition and collect only the
  requested allowlisted evidence: nonempty valid PNG screenshot and bounded
  sanitized accessibility, structure, heading, link, media, overflow, console,
  or failed-request summaries. Store summary artifacts as canonical bounded
  JSON or text. Never return raw HTML/DOM, response bodies, storage state,
  unrestricted accessibility tree, executable data, or browser handles.
- On success, timeout, navigation failure, disconnect, cancellation, malformed
  result, client disconnect, and SIGTERM, close page/context/browser and remove
  temporary files. No Chromium child, profile, token, temp file, queue slot, or
  in-memory attempt may bleed into the next run.

## 4. URL, request, and network confinement

- Install default-deny Playwright request interception before creating the page
  or navigating. Permit only the exact configured Web preview origin, the exact
  bound preview document route, and narrowly required same-origin Next/static
  assets. Recheck every redirect and block unexpected methods, credentials,
  schemes, hosts, ports, paths, WebSockets, downloads, and external Internet.
- Reject or abort loopback aliases, link-local, metadata, host gateway,
  private/unroutable IP forms, embedded userinfo, malformed/encoded authority,
  `file:`, `data:` navigation, `javascript:`, scheme-relative URLs, Agent,
  worker, Control, Editor, Render, Media, PostgreSQL, Docker API, and arbitrary
  Docker service names. Do not rely on substring matching.
- Keep the Compose browser network internal. Add only the exact Web preview
  service connectivity required by Chromium. Browser worker remains off the
  database and edge networks. Agent control connectivity may share the internal
  browser network, but actual browser-page probes must fail to reach Agent or
  the worker control API while the authenticated Agent client can reach the
  worker.
- Use layered browser/container policy rather than request interception alone
  where the pinned runtime supports it. The fixed preview origin is an
  operator-owned deployment fact and cannot be widened by request data.
- Readiness must fail if the configured origin is invalid, service auth or
  artifact root is unavailable, Chromium executable/target map is wrong, a
  sandboxed launch fails, or the default-deny confinement self-check fails.

## 5. Immutable private artifact store

- Mount a dedicated browser-artifact volume writable only by the non-root
  worker after one-shot ownership initialization. Agent, Web, edge, Media,
  Render, databases, and other services receive no direct mount.
- Use a fixed validated root and a server-derived namespace containing exact
  site/workspace/run/artifact/kind/target/route-digest/SHA identity. Prefer a
  flat or otherwise descriptor-confined layout that has no attacker-replaceable
  dynamic ancestor. Reject traversal and caller path fragments.
- Write through exclusive bounded staging, stream SHA-256 and size, fsync data
  and containing directory, publish atomically without replacement, and set
  restrictive exact ownership/modes. Verify existing digest reuse byte-for-byte.
- Reject symlink, non-regular, extra-hardlink, corrupt, wrong-size/digest,
  wrong-owner/mode, root/ancestor replacement, and publication races without
  overwrite or partial final state. Failed attempts may leave no temp file;
  failed later database registration in 072-g may leave only an immutable
  unreferenced artifact for future GC.
- Persist enough immutable non-secret worker metadata to retrieve an artifact
  after worker restart by exact authenticated IDs and to verify digest, size,
  MIME, type, target, route digest, created time, and expiry. Never persist an
  absolute path, token, capability secret, human cookie, or internal credential.
- Internal retrieval returns exact bytes only while retained and after service
  authentication. It is not edge-routed. Artifacts remain `PRIVATE`, never
  Media, publication input, or public URLs. Do not implement physical GC.

## 6. Required executable proof

- Unit/contract tests prove exact schema parity, target mapping, body/auth
  framing, constant-time secret handling, signed response binding, URL and
  redirect policy, redaction/bounds, queue/timeout/cancellation cleanup, and no
  raw automation surface.
- Artifact-store tests prove immutable write/reuse/read/restart, byte/digest/
  MIME agreement, modes/ownership/fsync/atomicity, symlink/hardlink/corruption/
  traversal/root-race rejection, concurrent publication, quota failure, and no
  partial temp/final state.
- Actual production worker image launches the pinned sandboxed Chromium and
  executes a direct service-authenticated run against the real Web/Render COW
  preview with a deterministic fake signed run credential and real PostgreSQL.
  It must produce a nonempty decodable PNG plus at least two requested
  nontrivial curated summaries, with exact metadata and retrieval bytes.
- The browser test proves workspace overlay output is observed while canonical
  state is unchanged; forged/expired/replayed/wrong-route or wrong-target token
  attempts fail without artifact publication.
- Hostile URL/page probes fail to reach Agent, worker control, Control, Editor,
  Render, Media, PostgreSQL, Docker/host/file, loopback/metadata/private targets,
  or public Internet. Exact preview and required same-origin assets succeed.
  No product credential appears in captured requests, console, artifacts,
  diagnostics, DOM, screenshot, process arguments, or logs.
- Two sequential attempts plus timeout, cancellation, navigation failure,
  client disconnect, and worker restart prove no context/storage/cookie/process/
  temp/credential bleed and retained artifact retrieval remains exact.
- Static and runtime Compose proof confirms only NGINX publishes; worker is
  non-root/read-only/dropped-capability/resource-bounded, has only worker auth
  and artifact mounts, no database/signing/Agent/human/reviewer/Media secrets,
  and public Agent runs remain durable `QUEUED` with empty artifact metadata and
  404 byte retrieval because no dispatcher is active.

Run focused worker/client/contract/policy/store tests; real PostgreSQL and
production-image Chromium integration; full Node gates; directly affected
Python/unit/integration tests; repository/packaging/Compose policy and a clean
Compose regression including existing nine Playwright projects; all process
checks; image/license/NOTICE/SBOM/vulnerability/reproducibility gates;
Markdown/Mermaid; and every fresh GitHub required check. Record every failure,
retry, skip, and not-run result honestly.

Update API/configuration/service-authority/security/deployment/operations/
testing/scaling/supply-chain/license documentation exactly where runtime facts
change. State that direct worker execution is implemented but durable dispatch,
DB completion/registration, public artifact bytes, source tools, six-target
runtime sweep, review integration, artifact GC, and publication remain pending.

## Workflow and report

Commit and push the exact strategic 072-f order and active bytes unchanged on
PR #66, then the bounded implementation/tests/docs. Publish exactly
`oap/reports/072-f-real-playwright-worker-private-artifacts.md` as one
report-only child with `Report publication commit: SELF` and a literal 40-hex
implementation parent. Report status remains `PARTIAL` for Objective 072 while
stating whether the 072-f worker slice is complete. Verify remote parent/path/
head, signal exact FIFO `OK`, and do not merge.

The report must state PR/base/branch/all SHAs; exact Playwright/package/browser/
base-image versions and digests; internal auth/request/response flow; target and
URL policy; sandbox/container/network facts; artifact namespace/atomicity/modes/
digest/retrieval; real browser and COW evidence; cleanup/restart/hostile-probe
results; public runs still queued; files/dependencies/lock/docs; every local and
CI result; no extra PR; and no merge.
