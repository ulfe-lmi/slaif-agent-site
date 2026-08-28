# Render resolution security boundary

The admin shell stores no session token, CSRF token, user UUID, permission list,
or selected site in local/session storage. Requests are same-origin,
credential-bound, no-store reads. Missing sessions redirect to login; direct
foreign/unknown site URLs render one constant state without caller-data
fallback. Tailwind is local build-time CSS and the Radix primitive is
self-hosted; there are no remote fonts, icons, scripts, telemetry, or origins.

Human authorization rechecks active user, active site, active membership,
exact site association, current membership version, and permission inside the
database boundary. Cross-site substitution, self-escalation, stale versions,
nonassignable permissions, and beyond-actor ceilings fail closed. Publication
is independent and never follows from editing or delegation level. See [Human
site authorization](AUTHORIZATION.md).

Control membership reads authenticate the strict human cookie once, resolve an
active site through trusted persistence, and require global administrator or
both membership-management permissions. POST, PATCH, and semantic DELETE use
the atomic session-plus-CSRF helper and then repeat actor authorization under
the mutation function's canonical row locks. Client Host, forwarded headers,
body IDs, roles, and versions never establish site authority. All catalog,
membership, validation, and error responses are private/no-store/noindex and
carry one request ID without foreign-site or credential detail.

Site profile and domain routes use server-fetched current membership
permissions. No request can provide an actor, permission, membership version,
or recent-auth override. Archive requires current global authority and current
recent authentication at the server; the confirmation dialog is usability
protection, not authority.

Clean Compose E2E uses two fixed OIDC fixture identities with a reserved
non-routable issuer. The smoke harness is their only insertion point; neither
bootstrap, migrations, Compose configuration, nor product source creates them.
They have no local credentials, administrator assignment, or enabled OIDC login
and are destroyed with disposable volumes. Their UUIDs are non-secret metadata
passed through the existing mode-0600 E2E channel; session, CSRF, setup-token,
password, and database locators remain excluded from arguments and artifacts.

The clean browser gate performs successful governance mutations only through
visible UI controls. Direct request calls are limited to concurrency setup,
crafted negative requests, and read verification. It proves missing/wrong CSRF,
self-change, system-scope, ceiling, stale-version, cross-site, unknown, and
archived-route failures leave state unchanged. NGINX response checks require one
edge request ID, strict self-only CSP without unsafe inline/eval or remote
origins on public rendering and unrelated admin/API routes, and a narrowly
scoped authenticated Puck editor style exception (`style-src-attr` and
`style-src-elem` `unsafe-inline` only), and
private/no-store/noindex API responses. Secret values are absent from URL, DOM,
storage, observed request URLs, console, and retained artifacts; screenshots,
traces, videos, and HTML reports are disabled locally.

The internal Render API owns separate canonical and preview connection pools.
The canonical pool uses only `slaif_public_login`/`slaif_public_reader`; the
preview pool uses only `slaif_preview_login`/`slaif_preview_reader`. Both pool
initializers verify database, login/current-user, and exact membership before
readiness succeeds. Preview additionally has only the owner-defined
`slaif_render_preview_authorize` function. That wrapper applies idle and
absolute expiry, revocation, account/site/workspace state, membership, and
touch/recent-auth semantics. Preview touch updates only `last_seen_at` and
never renews `recent_auth_at`. The wrapper acquires the shared workspace
advisory lock before mutable row inspection; the projection transaction
reasserts the same authority on its own preview connection and holds that
lock before any content read. Locator and driver details are never returned
or logged.

The role has no direct `control` relation access and no site management,
administrator, session, setup, migration, or publication function. It can call
only the two active site resolver functions. Resolution derives site identity
from normalized authority/path input and returns routing facts, not
authorization. Caller-provided identity, workspace, preview, membership, and
capability headers have no meaning. Web calls its single fixed URL with only
the actual request Host and path, no cookies, authorization, forwarded
identity, or caller-selected base URL. NGINX and Apache explicitly reject
`/internal/`; Control, Agent, Editor, and MCP expose no route to it.

Compose gives Render two isolated read-only locator files containing only the
public-reader and preview-reader DSNs. A third isolated file contains only the
high-entropy Web-to-Render credential and is mounted read-only to Web and
Render. Render does not mount the master or Control secret volume; Web and the
edge have no database locator. Missing/invalid locators or service credentials
fail closed at startup or request authentication through Render→Web→NGINX.
The Web reader validates the same process-owned directory, regular-file,
no-symlink, mode, owner, and bounded nonempty ASCII policy once at startup;
Render middleware never rereads an environment-selected path per request.

The Media service is a separate human-authenticated boundary. Its only
database authority is the fixed `slaif_media_login`/`slaif_media` identity and
named owner-defined session, workspace, COW metadata, idempotency, and audit
functions. Upload bytes are streamed to private digest-only storage after
signature validation; the client MIME and filename never select a filesystem
path. Authorized reads require metadata visible in the caller's active HUMAN
workspace and never serve the volume through NGINX/Apache. SVG and anonymous
media are disabled, and a database failure after private object publication
leaves only an unreferenced orphan for later Media GC.

Media workspace assertions acquire the same transaction-scoped advisory lock
used by human/editor mutation envelopes before checking mutable membership,
workspace, session, site, and permission state. The local store opens the root,
staging directory, digest ancestors, and final object with directory-relative
`O_NOFOLLOW` descriptors, verifies private modes/types and content, fsyncs
staged bytes/object/directories in publication order, and never recursively
retries a destination race. Global edge request bodies remain strict; the
larger allowance is confined to `/media/`.

Same-digest publication takes an exclusive advisory lock on the verified
digest-prefix directory only, with a bounded two-second acquisition timeout.
The directory itself is the lock primitive, so no lock artifact is exposed or
left stale after process death; the lock is released before database
registration. Multipart owns an `O_CREAT|O_EXCL|O_NOFOLLOW` read/write staging
descriptor from creation through publication and never path-reopens it for
production writes.

Browser preview-run contracts now have one immutable `browser-preview/v1`
version shared by Python and TypeScript. External create data is extra-forbid:
it accepts only a bounded normalized route, one approved Chromium target, and
a unique allowlisted evidence list. Absolute/scheme-relative origins,
traversal, fragments, credential-shaped query data, identifiers, viewport
overrides, headers/cookies, JavaScript, and browser commands are rejected.
Canonical serialization fixes evidence order before SHA-256 request digesting.

Migration `035_001` persists only capability limits, run/idempotency/lease
state, private artifact metadata, and append-only browser events. It stores no
artifact path, URL, credential, cookie, header, command, or bytes. Agent runtime
has exact owner-function execution and no direct relation access; all other
online roles are denied. Begin takes the shared workspace advisory lock before
authority recheck and quota reservation. Claim/renew/release/completion and
artifact registration recheck current authority and exact leases. Revocation
therefore prevents later artifact registration and visibility. The worker
remains DB-less. Direct internal execution is implemented with an isolated
service credential, exact Playwright/Chromium runtime, fixed target descriptors,
sandboxed fresh contexts, default-deny request interception, and a private
immutable artifact filesystem. No durable dispatcher, database completion/
registration, public bytes, source browsing, artifact GC, review, or
publication behavior is implemented.

Public Agent preview-run routes now use this durable boundary and remain
truthfully QUEUED without a dispatcher. Public bodies cannot select authority,
run IDs, viewports, origins, credentials, headers, cookies, or commands.
Create/replay is transactional; status/artifact metadata reads are non-mutating;
byte retrieval is always a non-leaking 404 until a later store exists. The old
unauthenticated fabricated browser router is absent.

The `sbp1` preview credential uses fixed HMAC-SHA256, type, deployment, audience,
contract version, key ID, and canonical payload. It binds capability/site/
workspace/run, normalized route, target, evidence/artifact/duration limits,
issued/short expiry, and a 128-bit nonce. Verification computes the signature
with `hmac.compare_digest`, rejects duplicate/unknown/oversized/future/expired/
changed facts, and stores only the nonce SHA-256 digest. Migration 036 consumes
the nonce once and rechecks current authority/run state under the shared lock.
The token is accepted only in dedicated Web/Render headers and never in URL,
cookie, DOM, storage, response, log, database, report, or screenshot.

The signing file is generated once as `sbk1:<key-id>:<256-bit-secret>`, in a
mode-`0700` UID-10001 directory with one mode-`0400` file. Agent and Render mount
that volume read-only. Web, worker, NGINX, Control, Editor, Media, MCP,
Scheduler, Reviewer, and GC do not mount it. Missing/bad key makes the Agent and
Render browser-signing readiness component unavailable; canonical and human
preview code paths retain their separate authorization semantics.

Worker authentication is checked in constant time from exact raw headers before
the body is read. Duplicate/missing/malformed credentials, ambiguous transfer
framing, non-canonical JSON, unknown fields, overload, and changed bindings fail
closed. Signed results bind request/run/site/workspace/capability/operation/
lease/attempt/route/target and expire within 60 seconds. Neither response nor
stable error includes a credential, token, nonce, query, path, SQL, role, or
foreign identifier.

Chromium runs non-root with its sandbox enabled. Compose drops all capabilities
then adds only `SYS_CHROOT`, applies the exact upstream Playwright seccomp
profile, no-new-privileges, read-only root, 64 MiB scratch tmpfs, 128 MiB shm,
256 PIDs, 768 MiB memory, and one CPU. Each attempt uses a fresh browser,
context, page, and temporary profile with cookies, permissions, storage,
service workers, downloads, trace, video, and extensions disabled. The preview
credential is attached only to the first exact document request and stripped
from assets, redirects, results, logs, and artifacts.

The worker artifact root is descriptor-anchored and mode `0700`. Files are
server-named, mode `0600`, single-link, SHA-256-addressed, exclusively staged,
fsynced, and published without replacement. Sidecar metadata contains exact
non-secret bindings and no absolute path. Retrieval revalidates metadata,
owner/mode/link count/size/digest/expiry and is internal only.
