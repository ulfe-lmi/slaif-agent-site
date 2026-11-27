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

The faithful frozen review read reuses the preview-reader identity and one
owner-defined authorization function as its single authority: live session
checks (idle/absolute expiry, revocation, account/site/workspace state,
membership), the v2 supported-format gate over the snapshot's stored trusted
version pins, and the site/workspace binding to the stored COMPLETE
`review-snapshot/v2` row. Every refusal is a uniform 404; the frozen review
media URLs are snapshot-scoped private byte paths authorized only for the
same human session against the snapshot's stored frozen media map, so a
review never depends on current canonical media references and the anonymous
public digest URL is never offered in review mode. The confined browser run
byte path never forwards a human cookie or Agent capability: Render verifies
and consumes the run credential and records its digest, verified expiry,
nonce, and attempt in one transaction, and the Media service re-checks that
trusted binding by digest only (it receives the existing credential solely to
hash it and holds no signing key).

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
workspace (human session) or the bound AGENT workspace (capability); pending
workspace writes are isolated from other workspaces and from the canonical
state until promotion, and frozen/active preview reads are private,
workspace/snapshot-bound, and digest-gated. The only public media surface is
the sessionless content-addressed digest route, which serves only media the
reviewer transaction has marked public atomically with promotion. Pre-commit
byte preparation is idempotent: if acceptance aborts, a newly copied digest
lacking committed canonical public authorization is an unserved orphan,
whereas an already-public digest retains its existing authorization, and a
database failure after private object publication leaves only an
unreferenced orphan for later Media GC. The reviewer-only in-transaction
helper (`slaif_media_publicize_promoted`, EXECUTE to `slaif_review_worker`
only, direct content-schema USAGE for resolution only) is a mechanism of the
review transaction, not a publication authority for the media, human,
editor, or agent processes. SVG is disabled, and private, staging, and
artifact reads are never served anonymously; approved public digest reads
are intentionally anonymous (content-addressed and digest-gated). The
immutable storage directories are never exposed as static directories;
authorized Media service byte responses are proxied through the edge.

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
immutable artifact filesystem. Durable dispatch, database completion/
registration, and capability-authenticated private artifact bytes are
implemented. Source browsing, artifact GC, review, and publication behavior
remain unimplemented.

Public Agent preview-run routes now use this durable boundary. Public bodies
cannot select authority,
run IDs, viewports, origins, credentials, headers, cookies, or commands.
Create/replay is transactional; status/artifact metadata reads are non-mutating;
byte retrieval is capability-authenticated and remains a non-leaking 404 for
missing, foreign, expired, revoked, nonterminal, or cross-site bindings. Only
retained PRIVATE artifacts are proxied after worker size/MIME/digest
verification; the old unauthenticated fabricated browser router is absent.

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

The current maintenance pin is the official Chrome for Testing
`158.0.8127.88` archive at CfT revision `1727472`, verified by SHA-256
`59e3b43f8b3aaa292238fbdcfb36a93127debd53e212510dcdc2cc8812b4b57e` and kept
separate from the Playwright bundle-directory label. The Playwright package and
base image remain at the exact qualified `1.62.1` versions.
The 083-9-c round remediates CVE-2026-115557: the backend base moves to the
digest-pinned official `python:3.12.16-alpine3.23` (fixed upstream in
3.12.16), and the browser worker purges the seven inherited Ubuntu Python 3.12
packages from both stages. Acceptance of the final implementation commit
requires fresh required checks, a fresh local runtime probe, and the current
six-image CI at the final gates.

The worker artifact root is descriptor-anchored and mode `0700`. Files are
server-named, mode `0600`, single-link, SHA-256-addressed, exclusively staged,
fsynced, and published without replacement. Sidecar metadata contains exact
non-secret bindings and no absolute path. Retrieval revalidates metadata,
owner/mode/link count/size/digest/expiry and is internal only.

The trusted mutation completion provenance boundary (revision `078_001`,
increment 083-11-a) records one durable completion identity per newly
completed editorial mutation, in the same transaction as its COW mutation,
family audit, and idempotency completion. The `mutation-completion/v1`
journal is keyed by the trusted operation ID and carries the family
(`agent`, `human_editor`, or `media`; a lawful HUMAN edit inside an AGENT
workspace is `human_editor`, not a fourth family), site, workspace, the
actual capability or human principal (a row check binds agent rows to a
capability with no human and human_editor/media rows to a human with no
capability), a bounded opaque SHA-256 request identity and digest, the
primary resource attribution, and the honest disposition. Raw client key
bytes, tokens, cookies, private URLs, and response bodies never enter the
record; response bodies and row values stay where they are already
retained, and the primary resource attribution is not a full changed-row
footprint, a causal graph, or a promotion receipt. The journal table is
owner-only and the owner-only completion helper grants EXECUTE to no
runtime role: no runtime role gains journal SELECT or DML, forged family
or principal selection, or canonical, reviewer, or schema authority; the
ten online control, editor, agent, reviewer, review-worker, public-reader,
preview-reader, scheduler, media, and GC roles are all denied, and PUBLIC
has no access. Replays
return the stored original result and create no new completion; the same
operation cannot complete again under another family or identity, while
repeated edits of the same resource by different operations or families
remain legal. Read access stays narrowly trusted with no new HTTP API, and
completions recorded before the migration are not backfilled and are not
retroactively made eligible: the absence of historical provenance is
unknown, not proof of no effect or corruption. While the durable journal
exists, downgrade is refused before effects for any head retaining the
078 provenance (current or later, journal empty or not): the operator path
refuses before the readiness PENDING marker, before the content COW
disable, and before any migration step, and the 078_001 Alembic downgrade
body is an unconditional explicit refusal for direct migration
invocations. The 077_001 media-isolation downgrade guard and its Alembic
body remain the historical line of defense, and downgrade never deletes
durable completion, audit, or idempotency history or restores the
pre-removal media authority.

The reviewed-operation binding boundary (revision `079_001`, increment
083/12) closes the approval bypass. Each new review snapshot carries an
immutable reviewed-operations/v1 companion manifest — the exact public
operation IDs, the actual foundation dependency pairs, and one
verified provenance record for every member of the pending set U:
the trusted 078 completion identity for ordinary journaled mutation
operations (Agent, HUMAN Editor, Media), or the versioned
`proposed-effect/v1` trusted producer record for the Control-only
proposed-side-effect producer — a product-owned prospective
completion row (`control.proposed_effect_completion`) that the real
trusted producer writes in the same transaction as its COW insert,
binding the server COW operation, the stored site/workspace, the
constant producer name, the service principal (a fact the caller
cannot select), and the exact created resource IDs. The
producer table CHECK keeps the producer and principal-type
columns fail-closed to the single product constant, so no
stored row can carry a distinct producer family. The
producer constructor takes the shared workspace lifecycle
lock before its first state read and any write. That lock
uses the same transaction-scoped key and ordering as the
normal online writes and the freeze. The freeze's
exclusive lock on the same key waits for the in-flight
shared holders, and a write that starts after the
transition is refused. The same-operation collision is
refused at the write in both orders. In the ordinary-first
order, the constructor refuses an operation id already
carried by the durable 078 journal, or by a trusted record
with a different site, workspace, producer, or principal
binding, before its own COW, journal, and producer writes.
In the trusted-first order, the mirrored owner-internal
guard (SECURITY INVOKER, no grants, no raw table access)
refuses the same collision on the 078 journal write. That
guard can run after the ordinary COW rows of the write and
rolls the whole ordinary transaction back. The record is
derived field-for-field from that row and is never inferred from
private COW change-row membership — stored atomically with the
snapshot by the trusted completion function, and
the human accept entry point requires an explicit approval binding the
snapshot ID to both the stored snapshot digest and the manifest digest.
The reviewer transaction re-verifies the binding against the live
companion, the durable journal, and the workspace state before
publication: wrong, stale, or missing digests are typed refusals, the
old 072 accept signatures cannot enqueue (the inner transport is
owner-internal with no role EXECUTE, and the legacy call paths are
dropped or typed refusals), and the real worker payload is defended in
depth. The accept approval is durable and typed. The
enqueued job payload carries the exact snapshot ID, stored
snapshot digest, manifest digest, actor, and site. An
idempotent replay returns a live job only on an exact
full-tuple match, so a stale, different, or legacy-shape
approval is a typed refusal that never fills in from
current mutable state. Inside the still-open reviewer
transaction, the SDK promotion runs first and the exact
pending check follows the SDK call, both before the native
COMMIT and before any revision or audit effect. The result
must show exactly the approved operation universe applied
to exactly that session, with the pending remainder
explicitly empty. The promotion receipt gains the new
applied-identity fields (``applied_operation_ids``,
``manifest_id``, ``manifest_digest``). Only those fields on
legacy receipts stay NULL, and they are never backfilled.
The companion table is owner-only, and the narrow projections
grant EXECUTE only to the roles that need them (the read projection to
control and review-worker, the identity, provenance, and
companion-completion functions to review-worker); the
promotion-receipt read definer, granted to the worker only,
is the worker's receipt read path, and the worker retains
its existing promotion INSERT authority while direct
audit.promotion SELECT is denied. No runtime role
gains companion or journal table SELECT or DML, and the standalone
companion-less completion loses its last online EXECUTE so no online
role can create a companion-less snapshot again. The receipt
read returns only SQL absent, exactly one stored row, or a
bounded no-data ambiguity marker. At a commit-boundary
error, the exact single receipt, the accepted workspace, the
succeeded job, and the matching single outbox event prove
success. A proven durable rollback rests on the durable
absence of both the receipt and the publication outbox
together with the same job still claimed by its claimant.
Retry then follows the fault's eligibility and attempt
budget, and a contradictory result defers to the claim
function's stale-claim handling. No new public job state
and no raw audit grant are added. At and after this
head the control role additionally holds direct content-schema USAGE
for resolution only, so the Control process can resolve the public
COW session's qualified trusted producer call; the privilege
reconciliation demands that usage only at or after the 079 head, and
no content table, sequence, or CREATE grant is added. The
final canonical byte budget, the manifest element budgets,
and the whole-workspace fact ceiling keep their existing
values. The staged type and shape guards refuse malformed
input at an earlier typed stage, before any array-specific
operation can see it. The manifest is a
bounded approval receipt, not a full semantic graph, row history, or
causal record; a companion-less historical snapshot remains readable
but can no longer be accepted at this head (discard and re-freeze is
the path). While the durable binding exists, downgrade is refused
before effects for any head retaining it (current or later): the
operator path refuses before the readiness PENDING marker, before the
content COW disable, and before any migration step, and the 079_001
Alembic downgrade body is an unconditional explicit refusal for direct
migration invocations. The 078 and 077 downgrade guards remain earlier
lines of defense, and downgrade never deletes durable completion,
manifest, audit, or idempotency history.

The heading row effect boundary (revision `080_001`, increment
083/13) is the bounded same-transaction row-effect pilot for the
single existing heading-props edit case. A successful changed
heading-props write through either trusted editorial boundary — the
062 Agent component update definer or the 060 Editor composition
node update definer — records exactly one durable product-owned row
effect in `audit.heading_row_effect` in the SAME transaction as the
COW write, the family audit row, and the idempotency completion. The
images are captured by the definer itself inside one statement: a
`prior` CTE holds the pre-write row and the data-modifying `post`
CTE performs the byte-identical original write with `RETURNING`, so
the recorded before image is the exact DML pre-image, not a service
read or a response value. The pair is read under the statement's
shared snapshot of the real COW view; a shared statement snapshot
does not promise a general CTE evaluation order, and the view does
not expose the foundation's first-touch baseline bytes, so nothing
beyond the recorded pair is claimed. The evidence is versioned
(`heading-row-effect/v1`) and bound to the server operation id
(primary key), the actual mutation family, the site/workspace/
component, the exact `+1` version pair, and the object-typed props
images bounded by the existing composition 16384-octet ceiling. An
Agent fact is bound to the capability; a Human-on-Agent Editor fact
is bound to the human principal RESOLVED FROM the actual in-progress
human-editor idempotency reservation row, never from caller-supplied
values. A fact requires actually distinct before and after props in
the write, decided on the ACTUAL same-statement image pair: the
Agent definer only reaches the recorded write after its own
no-effect short-circuit (identical props return without any DML),
and the Editor branch records only when the captured before/after
props are `IS DISTINCT FROM` each other — the earlier validation
snapshot can diverge from the statement's view (for example a
sibling publication between the pre-read and the write), so it is
never the decision input. The Editor capture is scoped to the
intended Human-on-Agent surface: only the session's own
`actor_type = 'AGENT'` COW workspace records; an ordinary Human
workspace keeps its legacy write byte-for-byte and records nothing.
An unchanged-props or structural-only DML keeps the legacy behavior
and records nothing; a mixed props+structural change records the
exact props pair and makes no claim about the structural history.
The table is owner-owned with no PUBLIC or role access:
every runtime role is denied SELECT, INSERT, UPDATE and DELETE, and
the owner-only recorder
`control.slaif_heading_row_effect_record` has no role EXECUTE at
all. Before any effect the recorder requires the exact COW session
context (the `app.session_id` / `app.operation_id` GUCs naming the
same workspace and operation), the claimed after image matching the
current session view of the row, and an in-progress same-operation
family-ledger reservation; a genuine no-effect completion records
no row, a replay returns the stored body before completion without
re-running the definer, and a rolled-back request leaves no row.
No fact can commit unbound: a `DEFERRABLE INITIALLY DEFERRED`
constraint trigger re-checks at COMMIT time, for every fact
inserted by the transaction, that the same operation has a genuine
completed 078 completion — the exact `audit.mutation_completion`
row (operation, family, site, workspace, actual principal, resource
type and id, disposition `completed`; the resource type is the
existing wire value, `composition_node` for the Agent boundary and
`editor.sites` for the Editor composition route), the matching
family audit row (`audit.agent_mutation` /
`audit.human_editor_mutation`), and the family ledger reservation in
completed state. A missing or mismatched completion refuses the
commit (`HEADING_EFFECT_COMPLETION_UNBOUND`, P0001) and rolls back
the staged COW change and the fact together; the check function is
owner-only with no role EXECUTE and no new grant surface.
The Heading case therefore completes only inside a COW session that
holds its in-progress same-operation idempotency reservation: both
production HTTP paths always begin their reservation before the
definer call, so no supported flow is affected, while a direct
definer invocation without that reservation fails closed for the
Heading case. Non-heading writes keep the pre-080 definer bodies
byte-for-byte (the pilot observes and records; it does not harden
the Editor's historical no-version-predicate body or change the
Agent's existing version guard), and the re-emitted writer
definers keep the exact existing ownership and EXECUTE grant
surface. This is a bounded pilot: there is no public history
endpoint, no retroactive backfill (pre-080 heading writes are
unknown, not proof of no effect), no global lock or isolation
change, no new dependency, and no foundation change. While the
durable table exists, downgrade is refused before effects for any
head retaining the 080 surface (current or later): the operator
path refuses before the readiness PENDING marker, before the
content COW disable, and before any migration step, and the
080_001 Alembic downgrade body
(`HEADING_ROW_EFFECT_DOWNGRADE_UNSUPPORTED`, P0001) is an
unconditional explicit refusal for direct migration invocations.
The 079, 078 and 077 downgrade guards remain earlier lines of
defense, and downgrade never deletes durable row-effect,
completion, manifest, audit, or idempotency history.

The retained heading review facts (revision `081_001`, increment
083/14) bind the already-recorded `heading-row-effect/v1` facts of
reviewed operations to the immutable review created by the actual
freeze worker. Capture happens INSIDE the one locked freeze
transaction, after the snapshot, the companion reviewed-operations
manifest and the REVIEW transition, and before the job's SUCCEEDED
terminal, so the retained set is atomic with the review it
describes: the owner-only definer
`control.slaif_review_retain_heading_facts` (EXECUTE for
`slaif_review_worker` only) re-resolves the snapshot from the
workspace's trusted pointer — never a caller-selected id — re-binds
its exact digest, and re-resolves the companion manifest of that
exact snapshot, so the stored row is bound to the exact site,
workspace, snapshot id and digest and the reviewed-operation
manifest digest. Every candidate fact (the product-owned
`audit.heading_row_effect` rows of the same site and workspace)
is selected from the actual reviewed operation set — the exact
companion's stored `operation_ids` — so the retained set is that
reviewed selection only, never "every prior workspace fact".
Every selected fact must carry the manifest's completion identity
of its operation — family, principal (capability for `agent`,
human user for `human_editor`) and resource (the component)
field-for-field the identity's — or the capture refuses
(`HEADING_RETENTION_BINDING_MISMATCH`) before any write; a fact
whose operation is outside the reviewed set is not retained and not
claimed as reviewed. A known inconsistent binding or a budget
violation (at most 256 records, checked on the whole genuine fact
set of the exact site/workspace before selection and
materialization, each selected props image at most 16384 octets
re-asserted on the trusted path, the EXACT canonical UTF-8 byte
size of the selected record array enforced as the first byte gate
— the selected record shape is written once as a
migration-local shared projection consumed by two separate
statements (first the exact byte total - the canonical per-record
bytes plus the two array brackets and one comma between every pair
of adjacent records, the exact pre-assembly encoded size, so no
in-budget set is ever refused by the measurement - and only after
it passes, the aggregation of the same projection, so the two
measures cannot drift and an over-ceiling set is refused before
the array is built), with the whole
ordered facts array at most 1048576 exact canonical UTF-8 bytes,
whose post-assembly measurement must equal that pre-assembly total
exactly, alongside the same cheap conservative lower-bound
pre-check the 079 companion uses) refuses the entire
locked freeze transaction (`HEADING_RETENTION_OVER_BUDGET`), leaving
no snapshot, no companion, no retention row and no REVIEW state
while the earlier committed mutation facts stay intact. Stored bytes
are derived entirely on the trusted path from the stored rows; the
worker supplies only the workspace and site. Every record preserves
the full checked image pair, the row versions and the exact
operation identity — including intermediate facts for reviewed
operations when the final props return to their original value.
Ordering is deterministic without a causal claim: the known per-row
transition orders each component's facts by `row_version_before`
with a native-UUID `component_id`/`operation_id` tie-break. The
stored row carries an explicit `retained-heading-facts/v1` version,
the ordered facts array, its count, its exact canonical byte count
and a SHA-256 digest over the 070 canonical serialization for
deterministic exact read and replay. The retained facts are review
evidence attached to the immutable review: they are never an input
to the existing accept approval (snapshot id + domain digest +
manifest digest), which is preserved byte-for-byte.

The single table `control.heading_review_retention` is owner-owned
with no PUBLIC or role grants; the two definers are the only
exposure. The human read
`control.slaif_review_heading_effects_read` (EXECUTE for
`slaif_control` only) reuses the existing authorized review
boundary — the same uniform gate class as the 071 review read
model, behind the Control process's human membership check — so
current human membership (or platform administration) and the named
snapshot's site/workspace association are re-checked against the
resolved snapshot row's own site and workspace, and a different
site, an unauthorized caller, an unknown id or a missing review
all take the existing uniform 404 behavior with no oracle. The
current review follows the trusted pointer; the optional named
snapshot argument makes the retained lookup bind the EXACT
requested snapshot, whose site/workspace association is checked
against the snapshot row itself, so a retained review can be
reopened independently of the pointer. The served row is bound to
its exact companion (manifest digest, site, workspace) and every
served record is re-checked at read time against the companion's
completion identities (operation, family, principal, resource), so
the served set is exactly the retained reviewed-operation subset;
a pre-feature snapshot
(frozen before this revision) is represented as `status:
unavailable` with the reason `pre_feature_snapshot`, while a
genuinely captured empty set is `status: captured` with an empty
facts array — the two stay distinguished in the response. The
document is narrow (binding, digest, count and the retained facts)
and is never echoed into error responses: every refusal is the one
stable class the HTTP layer maps to the uniform 404. No new actor
authority is added; the accept inputs, approval API, eligibility
and worker gates are unchanged.

While the durable table exists, downgrade is refused before effects
for any head retaining the 081 surface (current or later): the
operator path refuses before the readiness PENDING marker, before
the content COW disable, and before any migration step, and the
081_001 Alembic downgrade body
(`HEADING_RETENTION_DOWNGRADE_UNSUPPORTED`, P0001) is an
unconditional explicit refusal for direct migration invocations.
The 080, 079, 078 and 077 downgrade guards remain earlier lines of
defense, and downgrade never deletes durable retention, row-effect,
completion, manifest, audit, or idempotency history.
