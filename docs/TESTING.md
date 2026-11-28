# Testing

## Administration read model and shell

Backend tests cover the current-human site and authority read functions against a
disposable PostgreSQL database, including Platform Administrator behavior, ordinary
memberships, archived and disabled records, deterministic ordering, cross-site denial,
and exact grants. Unit and repository tests keep the HTTP route-policy inventory and
migration/privilege manifests exact.

The web source-contract tests exercise the same-origin, no-store read requests, response
validation, session redirect, canonical URL selection, loading/empty/ error/archived
copy, keyboard-managed Radix site switcher, responsive 320 px layout rules, and the
absence of browser storage, remote origins, or telemetry. The normal Node gate also runs
lint, formatting, type checking, package tests, the production build, and license
inventory.

Repository and supply-chain gates pin the administration build to Tailwind CSS 3.4.19,
PostCSS 8.5.26, and Autoprefixer 10.5.4. They reject Tailwind 4, `@tailwindcss/postcss`,
Lightning CSS, remote CSS origins, and unfrozen UI packages. The Node license inventory
must contain no MPL license family.

The clean Compose browser sequence is deliberately ordered: `setup` initializes
once, Chromium `governance` performs the only UI mutations, and the six stable
desktop/tablet/mobile projects depend on governance and remain read-only. The
governance project creates and archives a site, changes profile/domains, manages
an existing-user membership, exercises optimistic conflict recovery and crafted
server denials, and checks CSP/privacy through NGINX. Each stable project proves
dashboard, switcher, site overview/settings/membership reads, keyboard dialog
behavior, 44 px critical targets, 320 px overflow safety where applicable,
reduced motion, and logout. Stop/start fingerprints then verify site, domain,
membership, fixture, setup, and secret persistence. These automated checks are
bounded executable evidence, not an accessibility or security certification.

The governance Puck scenario creates an empty page through the Editor API only,
then adds two trusted Sections through the visible drawer. It selects a
component through the rendered Puck UI and uses the visible accessible `Move up`
and `Move down` sibling controls, backed by Puck's reorder/history action. The
controls derive the selected component's exact sibling zone and index, disable
at the first/last boundary, and are not limited to a particular fixture or
pair of components. After Move down, the selected component remains selected at
the destination boundary; visible Undo and Redo restore the prior/moved order
and selection boundary without backend operations. The scenario saves only the
final redone state, reloads the composition, and verifies the same stable
first-component ID moved from order 0 to order 1, the second ID at order 0,
normalized server records, workspace overlay, HUMAN audit, and idempotency
evidence. It then explicitly selects the other visible component and verifies
that deliberate selection remains stable and controls reflect its inverse
boundary; later moves may bind continuity to a new selection. The final editor
response must carry only the documented style-only
CSP exception; scripts remain nonce-bound and the observer fails on any CSP
console violation, unexpected console/page/network failure, or server error.
Public and unrelated admin policies remain strict.

The backend production-chain integration uses the fixed
`slaif_control_login`/`slaif_control` and
`slaif_editor_login`/`slaif_editor_runtime` identities, the real database
classes and Editor application factory, and public Editor HTTP routes. It
proves page CRUD, component add/update/move/delete, replay/mismatch, canonical
fallback versus overlay, exact audit/idempotency counts, and no direct
content-base or control-table access by the runtime roles.

The Media integration uses a real `slaif_media_login` pool, ordinary human
site memberships, real session/CSRF/RBAC state, disposable filesystem
staging/object directories, and multipart HTTP. It proves signature-bound
PNG/JPEG upload, digest-only keys, private byte headers, canonical fallback,
idempotent replay, concurrent same-byte deduplication, mismatch, missing-key,
ordinary permission/isolation failures, Editor metadata patch/reference
delete retention, injected post-publish DB-failure orphan behavior, and no
staging residue. Store unit tests cover ancestor/final symlinks, non-regular
objects, corrupt reuse, descriptor reads/closure, modes, readiness failure,
and publication fsync hooks. Multipart tests split adversarial boundaries and
prove duplicate/length/truncation/oversize/cancellation cleanup. A real
PostgreSQL two-connection race proves the Media workspace assertion waits on
the shared workspace lock before revocation is evaluated. Compose/edge tests
keep `/media/` as a proxy-only route with no volume alias or host mount and
prove the larger request-body allowance is route-scoped. The lifecycle proof
also covers the exact filename-bearing `file` part, Viewer upload denial,
revoked session, revoked/expired workspace, and archived-site outcomes with
no idempotency/audit residue.

Media workspace isolation adds fresh-pending oracles on both channels: a
pending upload is readable with exact bytes in its own workspace while a
same-site second workspace, the canonical base, and the sessionless public
route for that previously unpublished digest all stay
404/empty - pending metadata cannot revoke a digest that is already
legitimately public; a lawful human Editor PATCH/DELETE on an
agent-uploaded asset in its AGENT workspace is visible only to that workspace,
with the preserved agent `MEDIA_UPLOADED` audit row and exactly the two
`HUMAN_EDITOR` mutation audit rows; existing canonical assets keep their prior
public authorization through pending edits, and same-hash dedupe keeps stable
ids. The real review-worker regressions cover the grant matrix, freeze/accept/
replay idempotency, NEW pending same-hash typed conflict with full rollback,
failure after BOTH the promotion and the in-transaction mark (exact pending-row
preservation, promoted composition absent from the base, and an actual public
read proving the orphan is not served before recovery and serves exact bytes
after it), typed media-closure publication including non-canonical UUID
spellings, and the 077 privilege module (worker-only helper denials,
missing-helper readiness refusal, effective schema-USAGE usability with its
negative, and coherent historical 076 then 077 phase), and the
migration preservation module (a genuine 076->077 normal-operator upgrade
path with nonempty media plus a retained `review-snapshot/v2`, and the
unconditional 077 downgrade refusal; the fresh current-head install is
covered by the existing fresh-install/privilege/bootstrap cases). The ten
selected regression modules run unfiltered in each PostgreSQL 14..18 Group B
child of the existing CI matrix (five Group B executions) alongside the
older media selections; all ten actual Group A/Group B required CI children
remain required, but only the Group B children run the ten selected regression
modules (several pre-existed; the new item is their unfiltered Group B
selection). The `media-publication` spec has its own Compose project selection;
the full existing `freeze-review-snapshot` project (which selects both the
freeze-review-snapshot and frozen-review-parity specs) is what supplies all
SIX stable target/engine pairings (three engine families) - not six
distinct engine families, and not each media file running sixfold. This is
source scope; pass counts are reported per that selection rather than as a
six-engine claim.

The Media store unit suite additionally runs two independent store instances
in separate threads, pauses the winner after final-link visibility and before
staging unlink, proves the loser waits and reuses the one-link object, proves a
different digest progresses under its own prefix lock, and proves bounded lock
timeout cleanup. The production parser writes through the pinned staging
descriptor returned by the store; path replacement is rejected by inode
comparison.

## Canonical and active-preview rendering

Render projection tests validate normalized site-prefix routing, published
canonical selection, bounded composition trees, catalogue/schema/slot checks,
safe same-origin props/URLs, explicit collection projection fields, reserved
metadata isolation, and same-site binding limits. PostgreSQL integration
provisions the separate public and preview roles, validates the exact preview
authorization function and denied direct relation/DML paths, and proves that
a HUMAN workspace COW overlay is visible only through authenticated preview
while canonical output remains unchanged. Preview authorization also covers
idle/absolute expiry and revocation, with the in-transaction recheck held
under the workspace shared lock. Unit and Compose policy tests cover missing,
empty, duplicate, wrong, correct, symlinked, mode-invalid, and owner-invalid
Render credentials. Web tests preserve 401/404/503 distinctions for the
server-only client, exact-root shell fallback, canonical-first non-loopback
root resolution, strict public CSP, and absence of session/service credentials
from client-visible output or artifacts.

The dynamic collection proof builds a News model, localized fields, published/
draft/archived items, bounded view, listing/detail pages, trusted collection
nodes, and navigation through the public Agent API. It proves sorted listing,
exact-slug detail binding, canonical draft/archive/unknown 404s, translation
fallback, renamed-item route movement, and unchanged canonical visibility.
Migration tests also prove the 054-to-055-to-054-to-055 function-definition,
grant, and data round trip.

## Bounded page-style override acceptance

The focused PostgreSQL page-style proof creates pages through the public Agent
API, reads pure inherited defaults, sets representative values in all four
existing theme groups, and verifies raw overrides, resolved values, page row
versions, replay, stale/foreign-page confinement, and the read-authorized
no-effect path. It also proves exact reset overlap, strict positive Agent
versions, full page resource visibility, narrowed token and reset-destination
constraints, unrelated-scope denial, quota/lifecycle/revocation failures,
delete/restore preservation, no-effect mutation/audit accounting, service
restart with non-empty overrides, direct-runtime/helper privileges, and the
066 fresh legacy round trip with pending/data-bearing downgrade refusal. Real
PostgreSQL barriers cover competing style changes and style versus page
update/move/delete plus lifecycle/theme serialization. The browser proof
asserts all four effective page-style groups and computed styles in the same
authorized NGINX preview, then resets to site-theme inheritance; human
Editor/Puck controls and composition persistence are exercised separately.
CI runs this focused gate across PostgreSQL 14–18; Compose acceptance extends
the same-workspace public Agent preview path through NGINX.

The 078-x continuation additionally captures a genuinely fresh 065 baseline
before applying 066, compares restored function definitions byte-for-byte with
owner/ACL/volatility/configuration and the audit constraint, isolates audit-only
downgrade refusal, cancels after real style DML and verifies rollback/retry,
checks exact audit/idempotency identity, and exercises both lock orderings with
page update/move/delete plus concurrent theme-change/reset serialization. The
human proof includes viewer denial and a same-group update/reset request.
The 078-y continuation adds the omitted inherited-only browser negative and
real resumed-inheritance proof, requires two distinct blocked backends before
releasing the concurrent theme barrier, and cancels a public Agent style
request while it waits on the prelocked mutation path, verifying rollback,
accounting, COW, and idempotency reuse.

## Bounded Agent component data-plane acceptance

The public Agent Compose acceptance creates a fresh human-issued L2 workspace
and capability, fetches the committed OpenAPI/session/permissions/catalog
contracts, and creates a new page through NGINX. It proves an initially empty
composition followed by a semantic `Section -> Container -> Heading` tree with
a RichText leaf, exact per-node reads, content-only Heading PATCH, before/after
sibling moves, dense order keys, positive row versions, and the four durable
`COMPONENT_CREATED`/`COMPONENT_UPDATED`/`COMPONENT_MOVED`/`COMPONENT_DELETED`
audit actions. It renders the changed page through authenticated human preview
HTML and a real run-bound Chromium worker, retrieving four private JSON
artifacts with matching heading/structure evidence and empty console/failed-
request evidence.

While the tree exists, the proof restarts `agent-api`, `render-api`, and `web`
one at a time and compares public Agent state and preview HTML after every
restart. It rejects parent deletion with children, stale versions, catalog
type/slot/schema/design/raw-order inputs, foreign site/workspace/page/node/
parent/sibling substitutions, idempotency mismatch, lower-scope structure
writes, and exhausted mutation/delete/resource budgets; each negative checks
the unchanged component tree and durable audit/idempotency counts. It deletes
leaves before parents, verifies 404/absence and preview removal, replays one
delete without a second effect, and confirms canonical HTML, another workspace
on the site, another site, and site records remain unchanged. The clean smoke
keeps this four-artifact proof alongside the existing six-artifact browser
fixture and retains all prior acceptance gates.

The focused design-semantics integration adds a real PostgreSQL/public-Agent
slice on the same normalized tree. It fetches the exact typed
`design-system/v1` document, changes Section/Container/Grid/Heading and the
existing Button/Image/CollectionGrid visual properties, and proves exact
scalar versus responsive scopes, mixed-property denials with unchanged
props/version/quota/idempotency/audit/COW state, L1 visual denials, direct
runtime-helper denial, malformed device input, no-op replay/accounting,
Puck round-trip validation, Render/Web responsive consumption, and resource
narrowing. A deterministic PostgreSQL barrier proves one optimistic design
PATCH winner and one `409` loser; a cancelled design PATCH leaves state
unchanged. These focused tests run serially because the disposable fixture
provisions shared product role names; concurrent test-file execution is not
valid evidence.

## Bounded site-theme token acceptance

The 078/2 theme proof uses a fresh human-issued capability and real PostgreSQL
through public Agent HTTP. It discovers the closed `theme-schema/v1` contract,
reads deterministic defaults without changing the theme row, updates
representative palette, typography, layout, and shape tokens, and verifies
versioned COW state, Render projection, trusted Web classes, and human
Editor/Puck schema-derived controls. It rejects missing or substitute scopes,
foreign workspace/site state, raw CSS/color/font/device/executable/version
input, narrowed palette/typography/token resource policies, stale versions,
quota exhaustion, idempotency mismatch, and cancellation with no durable
residue. Replay and byte-equivalent updates are exact no-effect operations;
same-version PostgreSQL PATCH races have one winner and one `409` loser, with
lifecycle advisory lock `280` proven before theme lock `995` for public and
direct-runtime paths.
Migration tests capture a genuine fresh-064 baseline, preserve valid legacy
theme data through downgrade/re-upgrade, restore every replaced function and
the semantic constraint exactly, and retain least-privilege/private-schema
boundaries. The retained renderer regression is covered through computed
Chromium colors and dimensions for all three palettes, numeric AA contrast for
primary/secondary/ghost roles, local/responsive precedence, and reset tokens.
The same real Agent workspace is then PATCHed through public NGINX and rendered
by the authorized preview path. Browser DOM and computed-style assertions
verify all four changed groups, same-workspace output, canonical/other-site
isolation, private preview headers, and a same-URL wrong-theme sensitivity
control before the real response is restored. The authorized browser worker
also retains private screenshot/summary artifacts, and Agent restart plus exact
idempotent replay retain its theme/version. The historical Firefox
response-category failure retained no endpoint/status artifact; its exact cause
is unknown/not reproduced, while current targeted desktop-Firefox runs pass.
No response suppression or retry weakening is used.

## Browser-run contract and durable control-plane proof

Python and TypeScript tests compare one committed language-neutral
`browser-preview/v1` fact document, exact targets/evidence/states/bounds, one
canonical serialization vector, and its SHA-256 digest. Extra-field and unsafe
route cases cover foreign versions/targets/states, duplicate evidence,
absolute/scheme-relative origins, traversal, fragments, credential query data,
viewport/ID/header/cookie/JavaScript/browser-command input, and malformed or
out-of-policy stored capability limits.

Real PostgreSQL tests use `slaif_agent_login`/`slaif_agent_runtime`, two sites,
two workspaces, and multiple capabilities. They prove concurrent same-key
serialization produces exactly one run/idempotency/enqueue event; replay and
mismatch are stable; total/concurrent/screenshot/artifact/target/route/evidence/
duration limits leave zero residue; authority and cross-site substitutions fail
closed; freeze/revocation waits behind the shared lock and rechecks; and
cancellation rolls back with a reusable pool connection. Separate lease tests
prove `SKIP LOCKED`, expiry retry, maximum-attempt termination, renew/release,
invalid transition/metadata denial, one private artifact registration event,
idempotent terminal completion, revoked visibility denial, read-only audit/COW
silence, exact function ownership/search path, and direct-relation/other-role
denials. Owner connections seed inputs and inspect counts only; every claimed
browser mutation executes through the Agent functions.

Public Agent HTTP integration proves 202 create, exact same-body replay,
mismatch, missing/invalid key, schema denial, scope, quota, two-site/two-
workspace/capability isolation, random IDs, empty artifact metadata, byte 404,
restart durability, revocation, fake-route absence, shared-lock race recheck,
exact `(run,idempotency,artifact,event)` counts, and no COW operation.
Dispatcher unit coverage proves bounded settings, run/lease/site/workspace
bindings, short-lived preview credentials, and disabled lifecycle behavior.
The public Agent Compose acceptance additionally configures a second locale and
workspace default, exercises navigation container/item CRUD with page,
internal static-page, and HTTPS external targets, verifies configured-locale
labels, nested placement, shifted row versions, and relative reorder across an
Agent restart, then removes the workspace-only rows and checks canonical
locale/navigation tables remain unchanged.
The clean Compose smoke additionally proves queued-to-terminal dispatch,
restart durability, atomic artifact registration, and real Chromium COW
preview completion before the direct worker artifact/replay checks.

Credential unit tests fix one deterministic token SHA-256 vector and cover
descriptor-confined key reads, modes/owner/symlink/format, duplicate JSON keys,
unknown algorithm/version/key/audience/contract, wrong signature, future/
expiry, oversize, and every changed binding. Real Render PostgreSQL/HTTP tests
prove the dedicated header, one-time nonce, exact preview-role function grant,
overlay-only projection, unchanged canonical output, tamper/expiry/foreign/
route/target/evidence/artifact/duration denial, replay denial, and revocation
between consumption and the under-lock COW recheck. Existing human preview
tests remain unchanged and green.

Compose policy and smoke prove only Agent/Render/initializer mount the signing
volume, unrelated UID denial, real NGINX Agent create/poll plus Agent restart,
missing-key readiness failure with canonical rendering still available, key
restoration, and the DB-less/key-less worker boundary.

The shared `browser-worker/v1` tests cover exact Python/TypeScript facts,
canonical request digest parity, three immutable target descriptors, raw-header
constant-time service authentication before body parsing, canonical framing,
signed result binding, first-document-only preview-header forwarding,
redirect/subresource stripping, hostile URL policy, sanitization, overload,
active inspection, disconnect cancellation, and slot cleanup.

Artifact-store tests cover exclusive bounded staging, fsync and no-replace
publication, deterministic reuse, concurrent publication, exact restart
retrieval, descriptor anchoring across root replacement, mode/owner/link/
digest/size/MIME/expiry checks, symlink/hardlink/traversal/corruption/quota
denial, and absence of partial staging state.

Clean Compose additionally launches the actual production image's sandboxed
Chromium against the real PostgreSQL COW preview. Two sequential direct Agent-
client attempts produce six artifacts including decodable PNG and heading/
structure summaries, observe the overlay, preserve canonical output, verify
signed results and byte retrieval after worker restart, and reject replay,
forgery, expiry, wrong route, and wrong target without artifact publication.
Runtime proof checks the exact seccomp/capability/resource/network/mount/image
inventory, no credential/log/artifact leakage, zero residual Chromium children,
worker-secret failure/recovery, and continued public `QUEUED` runs with zero DB
artifact rows.

## Frozen-review parity control reliability diagnostics (083/6-a)

The frozen-review parity spec (the six stable engine/target pairings
across the active-preview and immutable-review surfaces) submits the
shared same-path control form through real native button clicks.
083/6-a adds bounded, secret-safe operation-level diagnostics to that
sequence after the postmerge 600 s CI stall (run 40231055425, last
stage `phaseB/firefox/Desktop Firefox/controls` entered at 38868 ms
cumulative):

- The single `stage` test annotation (the CI reporter reads the first
  matching annotation) is extended with a fixed-enum `op` field and a
  bounded `flags` field: leg states `r/n/c` (0 pending, 1 ok, 2
  rejected), the observed numeric POST status, `navreq`/`mainframe`
  booleans, and relative ms. It never carries URLs, IDs, tokens, DOM,
  bodies, or a growing annotation list.
- Every response/navigation/click leg of every control submission
  carries an explicit diagnostic deadline of at most 30000 ms plus an
  actual AbortSignal. On first failure the operation is frozen (the
  first-failure leg state is snapshotted before abort/drain), pending
  sibling waits are aborted and drained in a bounded way, and only a
  sanitized fixed-enum-class/leg/flags error propagates; the raw
  Playwright message, cause, and call log are never rethrown or
  logged.
- A fixed secret-free in-page sentinel (a per-document marker
  installed by a context init script) is proven a non-empty value
  before each click and is required to change after each same-path
  POST, so a genuinely fresh main document is asserted even when the
  URL is unchanged. Only boolean results cross back to the test
  process as diagnostic output.
- Pairing failure priority is body, then the observer-collector
  assertion, then context close; the original collector assertion is
  retained whenever the body passed, and no later failure replaces an
  earlier first failure.
- The control POST response matcher binds the main-frame navigation
  request, the POST method, and the same expected URL; an iframe/fetch
  or unrelated same-URL response is not accepted.

These are diagnostic bounds on the existing harness only: no product
behavior, global 600000 ms test budget, retry, project, descriptor,
config, or CI budget change. Two bounded full local trials at the
instrumented baseline (fresh stack each) passed (141830 ms and 142929
ms, native exit 0); the postmerge CI stall was not reproduced locally
and its cause remains unknown.

## Governance drag outcome synchronization and teardown first-error preservation (083/6-b)

The governance Puck drag helpers previously allowed up to four
non-idempotent insertion attempts, each followed by its own readiness
check, so a not-yet-ready insertion could be followed by another. A fresh
whole-stack run at 083/6-a failed the rendered-count contract
(expected 2, received 5); the mechanism is unknown. Bounded passive
diagnostics (private bounded JSON: wrapper count, distinct
component-instance count, missing-identity count and relative ms at
existing gesture attempts/readiness boundaries, one atomic in-page
read, no raw IDs) were added at a recorded revision; the ONE
authorized fresh setup+governance diagnostic suite passed with both
insertions ready on the first gesture (0 to 1, then 1 to 2, wrappers
equal to distinct instances throughout), so the mismatch did not
reproduce and its cause remains unknown. The B3 repair makes each
requested insertion perform the one real existing gesture and then
establish the exact target state under the existing configured 8 s
expectation budget before any possibility of another side-effectful
gesture; an unresolved outcome fails with the preserved diagnostics
instead of replaying the insertion. Legal starting counts (0 before
the first insertion, 1 before the second) are asserted. The outer
parity teardown and the canonical/private pairing cleanups now
preserve the first captured failure through all closes, report close
failures with fixed-enum output only when the body passed, and never
serialize an arbitrary non-Error thrown value. All original
assertions, budgets, and retry configuration are unchanged.
## Public whole-session promotion qualification (083/8)

A new integration module
(`services/backend/tests/integration/test_foundation_whole_session_qualification.py`,
16 tests) is configured to qualify the generic whole-session COW promotion
mechanism through the public `agentcow.postgres` 0.2.0 API on an owned
disposable cluster: two whole mixed-FK deferred sessions with canonical
absence and unchanged-seed oracles before approval plus in-scope
`operations()` checks inside the reviewer body; empty/coalesced/net-zero
sessions; row- and genuine schema-conflict refusal assertions; the deferred
physical two-table cycle versus the non-deferred pre-promotion refusal and
the SET-CONSTRAINTS-IMMEDIATE dangling-state refusal; and three
terminal-window outcomes (escaped postcondition refusal, positive task
cancellation, backend termination) each asserting the promotion rolls back
with no leaked transaction, locks, or nonempty stale COW context (frozen
0.2.0 semantics treat NULL and `''` as clean). The module creates its own
disposable database/schema/roles per session, asserts in-window
`idle in transaction` state and live locks on the exact reviewer backend,
and checks the pools are reusable afterward under the same deferred mode.
CI is configured to run it as the fourth exact pytest command of the
Python integration job group B (existing three commands, 45 tests:
component 24 + theme 9 + page-style 12, unchanged; group A 85 unchanged) on
PostgreSQL 14-18; no existing selection, budget, matrix, or aggregator
changed, and actual per-version Q and SELF results are reported evidence.
The P7 composite-FK `dependencies()` characterization is scratch-only and
outside the CI selection. No backend application source or migration
changed in this increment. The only workflow change in the early rounds
083-8-a through 083-8-f was the ordered fourth exact command of group B,
and the only dependency change there was the released asyncpg driver pin
`0.31.0` -> `0.32.0` (round 083-8-f) with its exact lock, pin, metadata,
notices, SBOM, and documentation reconciliation. Later rounds changed
only build, test, tooling, and documentation files: the opt-in compose
smoke lifecycle and control-readiness evidence contract with its
packaging checks, runtime image/browser/security pin repairs, and
supply-bundle evidence tooling changes.

The qualification subject is the generic whole-session COW promotion
mechanism through the public `agentcow.postgres` 0.2.0 API on an owned
disposable cluster; this increment does not implement or accept actual
product publication, complete U/audit or causal closure, or MVP.
Actual I_f results (per-version Q passes on PostgreSQL 14..18, the
unfiltered backend integration run, and the I_f CI outcomes) carry into
later rounds only under the increment's identity/scope gates, labeled
as I_f evidence, and no later PASS is claimed before its own fresh
run. The increment's remaining acceptance requirements are fresh
LOCALWHOLE and LOCAL6 supply-chain evidence runs bound to the actual
tested implementation SHA, each reported when and if executed.

Under the 2026-11-13 qualified-source correction, the foundation pin and this
qualification module's frozen anchors advance from 0.2.0 to 0.2.1 in the
current 083-10-a source; the recorded 0.2.0 results above remain the 083/8
evidence and are not relabeled, and actual 0.2.1 results are reported when the
fresh current runs execute.

## Opt-in Compose smoke lifecycle evidence (083-8-k)

`sh tools/compose/smoke.sh <project> --lifecycle <absolute-evidence-dir>`
opts into the bounded lifecycle evidence contract; without the flag the
smoke never invokes lifecycle operations and its default helper argv,
stdout/stderr, and exit semantics are unchanged. Capture mode proves both
namespaces fresh before any disposal-capable trap, durably records each
helper container's full created ID before start, and never adopts a
failed create's stdout as an owned ID. Body results are exposed to caller
denial/value branches only after the complete receipt chain parses and
validates, with an executed-container terminal state (any 0..255 exit,
including a genuine 97 or 125/126/127) distinguished from a docker-level
start failure by that authoritative state. Post-absence is proven with a
matchable full-ID query, and each failed capture/cleanup/absence native is
recorded independently. Metadata stays an allowlist (ID/name, immutable
image digest plus reference, Created, minimal State, mount
name/source/destination/type/RW with an empty tmpfs source accepted and
the template sentinel rejected, scoped labels); Config.Env/Args/Cmd, full
inspect output, secrets, DSNs, and artifact bytes are never retained.

`tests/packaging/test_compose_smoke_contract.py` exercises the real
verify.py producers/readers/auditors and the real smoke.sh helper and
final callers with only the external Docker boundary mocked, including
the full 0..255 producer round-trip, failed-create foreign-ID rejection,
rm/absence-failure retention, and the real denial and value caller
blocks. No product runtime run is executed by these tests; the fresh
whole-session and LOCAL6 runs remain ordered later steps and nothing here
is an acceptance or a future PASS claim.

## Trusted mutation completion provenance (083-11-a)

The trusted mutation completion provenance increment (083-11-a, revision
`078_001`) adds bounded regression coverage across all three audit
families and all six deployed completion variants: the agent 13-argument semantic completion,
the agent 10-argument explicit no-effect completion, the agent 10-argument
legacy completion (no current Python caller; the deployed trusted boundary
is proven at runtime through the exact runtime SQL constants and the real
COW envelope), the HUMAN editor completions for HUMAN and for AGENT
workspaces, and the human media upload completion. The focused PostgreSQL
proofs use real HTTP or the real runtime COW context, real fixture roles,
and the public `agentcow.postgres` API on the disposable cluster: a
separate agent write, a HUMAN editor write in a HUMAN workspace, a HUMAN
editor write in an AGENT workspace, and a human media upload each leave
exactly one trusted completion with the correct family, principal,
reservation, and family-audit relationship; an agent upload followed by a
lawful human PATCH/DELETE of the same asset in its AGENT workspace leaves
three distinct completions on the same resource (agent, human_editor,
human_editor) with no fourth family and no resource-uniqueness rule, and
the actual multirow navigation move (three row position/version changes)
leaves one operation completion whose primary resource is not claimed as
a full row footprint.

The semantics proofs distinguish the explicit trusted no-effect decision
from ordinary completion: an ordinary zero-COW-row media dedupe completes
as `completed` with no fabricated COW operation, while only the explicit
agent no-effect path is journaled `no_effect`; same-payload/key replays
retain the original body, operation, and completion without a new journal
identity, a changed payload/key remains the current conflict, and failed
or rolled-back requests leave no new completion. The global identity
proofs cover cross-family same-operation duplicate refusals (including a
trusted historical fixture of a pre-078 completed ledger without a journal
row that must block a new other-family completion), a concurrent
same-operation race with real observed overlap that leaves exactly one
winner journal identity while the loser adds zero rows and rolls back its
own effects without forcing one SQLSTATE across isolation or constraint
paths, direct role denials of journal SELECT/INSERT/UPDATE/DELETE/TRUNCATE
and helper EXECUTE for every online role, and completion-context
mismatches (missing or wrong session/operation, site/workspace/principal/
reservation) that roll back all COW, family audit, reservation, and
journal effects. The failure and retention proofs inject a late failure at
the completion boundary inside the actual mutation transaction and
exercise real cancellation and owned-connection loss, asserting rollback
of COW pending changes, idempotency, family audit, and journal plus pool
cleanup, with no production test-control endpoint and no mocked
foundation.

Fresh install and the QUIESCENT 077-to-078 operator upgrade (with its
existing no-pending COW precondition satisfied) preserve canonical and
pending data, old family audit/idempotency/replay, and retained snapshots
byte-for-byte, with no historical completion backfilled; a separate
PENDING-work case proves the normal refusal preserves pending, canonical,
and history state unchanged — the upgrade never accepts pending work.
The real accept and discard paths leave new completion facts intact after
pending cleanup and replay.
The 077 media-isolation downgrade refusal stays a real historical proof at
the released 077, and the 078 completion-provenance downgrade is refused
by the operator before the readiness PENDING marker, the content COW
disable, and any migration step whenever the journal table exists (current
or later head, journal empty or not), with the 078_001 Alembic downgrade
body as the unconditional defense for direct migration invocations. The
new regression modules (completion semantics, completion authority,
producer families, late failure, and upgrade preservation) run unfiltered
in the existing PostgreSQL 14..18 Group B children alongside the existing
selections; the producer-families module also carries the integrated
legacy 10-argument agent boundary cases, and the mixed-workspace media
cases remain in the existing isolation module.  No existing selection,
budget, matrix, aggregator, or required check identity changes, and no
permanent sixth CI module or workflow redesign is introduced. The increment adds no snapshot format,
review manifest, exact-U promotion, history UI, SDK, dependency, browser,
GC, or lifecycle change; the qualified baseline (PyPI
`agent-cow-postgresql` 0.2.1, Chrome for Testing 157.0.8103.78,
Playwright 1.62.1) is unchanged. Full PostgreSQL 14..18 matrix
qualification is required and is reported as the repository CI executes
the full children; acceptance state is tracked in the OAP ledgers, and
nothing here claims D5, MVP, or product completion.

## Reviewed whole-session operation binding (083/12)

The reviewed-operation binding increment (083/12, revision `079_001`)
adds bounded regression coverage for the reviewed-operations/v1
companion manifest: a real freeze atomically stores the manifest with
the snapshot (the exact public operation IDs, the actual foundation
dependency pairs, and one verified provenance record per pending set
U member — the trusted 078 completion identity for journaled
mutation operations (Agent, HUMAN Editor, Media), or the versioned
`proposed-effect/v1` trusted producer record for the Control-only
proposed-side-effect producer — written by the real trusted
constructor in the same transaction as its COW insert into the
product-owned `control.proposed_effect_completion` row and never
inferred from private COW change rows — proven by a real freeze/
accept whose public U mixes both forms and four typed refusals of
forged provenance: a producer record relabeling a mutation-table
operation, a forged service principal on the real producer
operation, an extra resource id with no prospective row, and
owner-forged producer rows on a journaled operation as conflicting
provenance), and the real accept requires the explicit
dual-digest approval (snapshot digest plus manifest digest bound to the
snapshot ID) that the reviewer transaction re-verifies against the live
companion, the durable journal, and the workspace before publication.
The focused PostgreSQL proofs use the real HTTP, runtime pool, and
worker paths on the disposable cluster: freeze and accept for the Agent,
HUMAN Editor, HUMAN-on-AGENT, and human Media families; a
mixed-family same-resource superseding chain ending net-zero; an actual
multirow navigation move with one completion; dedupe,
explicit-no-effect, and empty-U behavior; replay and
repeated/superseding writes; two same-site workspaces with isolated
pending sets; and digest determinism for the same format and inputs.
The negative proofs cover wrong, stale, and missing digest denials;
malformed, over-budget, and legacy-ineligible manifest rejections;
whole-workspace orphan and conflicting prospective provenance
detection with legitimate outside-U dedupe staying legal; direct role
denials of manifest DML, reads, and helper EXECUTE for unentitled
roles; and the non-bypassability of the old 072 accept signatures
(owner-internal inner enqueue with no role EXECUTE, typed legacy
refusals, and the real worker payload defense).

The write-time collision regression covers both insertion orders
against the real paths. The ordinary-first constructor refusal
precedes its own COW and producer writes. The journal guard of
the trusted-first order can run after the ordinary COW rows of
that write, and the whole ordinary transaction rolls back. The
freeze-drain regression holds a real open Control COW session
through the freeze, drains it into U, pairs the real worker's
exclusive workspace-lock wait to the exact holding backend, and
requires a typed denial for a new proposal after the
transition. The stored distinct-binding regression calls the
trusted completion definer as the real review-worker login
against owner-forged stored rows. The four refusals are a
local-workspace row bound to a second real site, the real
producer operation bound to a real sibling workspace of the
same site, a distinct shape-compliant service principal on the
real operation, and one 078-journaled operation with a trusted
row only in the sibling workspace. A labeled owner insert also
proves the producer-constant CHECK refusal with its exact
constraint and no row. After each refusal the test asserts the
exact claimed job state, the unchanged public U, and no
partial publication state, and it recovers through the
legitimate real freeze job.

Inside the still-open reviewer transaction, the SDK promotion
runs first and the exact pending check follows the SDK call,
before the native commit. The SDK result must show the exact
applied IDs, and the following public pending read must be
empty. Separately, the existing
unreviewed-pending refusal proves the approved universe against
the live U. It shows that the approved set cannot be widened
inside the reviewer transaction. The new-pending same-hash
conflict refuses the deterministic collision. The durable
approval replay gate is proven by the enqueue idempotency,
tampered-approval, and re-review stale-approval cases. A stale,
different, or legacy-shape approval is a typed refusal that
never fills in from current state. The promotion receipt
carries the exact applied IDs and both approval digests, and
legacy rows keep the new fields NULL.

The receipt-read proof covers the absent, exactly-one, and
bounded-ambiguity projection. The worker keeps its existing
promotion INSERT, and direct audit-promotion SELECT is denied.
The uncertain-outcome reconciliation proves success only on the
full fingerprint. That fingerprint is the matching single
receipt, the exact terminal workspace and job, and the one
exact published outbox event. A proven durable rollback rests
on the durable absence of both the receipt and the publication
outbox together with the same job still claimed by its
claimant. Retry then follows the fault's eligibility and
attempt budget, and a contradictory result defers to
stale-claim handling. The completed-body cleanup and the
deferred COMMIT rejection are distinct proofs. The cleanup case
runs a real post-commit pool reset after a completed body and
recovers success from the exact durable fingerprint. The
deferred COMMIT rejection is definitive and terminal, with no
retry and the whole atomic bundle rolled back.

Fresh install at 079, the QUIESCENT 078-to-079 operator upgrade (the
078-era journal, family, snapshot, and canonical history preserved
byte-for-byte, with the companion-less historical snapshot still
readable through a NULL manifest projection), the pending-work
refusals from real 078 and 077 heads, and both the operator and
direct-Alembic 079 downgrade refusals are proven before any effect.
The historical 077-to-078 upgrade proof keeps its retained review
history genuine (a v2 built by the real trusted materializer and the
released 077-era completion definer under the real freeze job
lifecycle, plus the faithful 075-contract v1 document), because the
current freeze worker carries the 079 companion step and cannot run at
the released 077 head. The new modules (the reviewed operation
binding proofs and its role-authority proofs) run unfiltered in the
existing PostgreSQL 14..18 Group B children
alongside the existing selections. The write-time collision,
freeze-drain, stored distinct-binding, replay-gate, and
uncertain-outcome regressions extend those existing increment
modules (the reviewed operation binding module, the real human
accept module, and the role-authority module) and add no new
modules, so no existing selection, budget,
matrix, aggregator, or required check identity changes, and the policy
suite pins the exact module lists with omission negatives. The
increment adds no row-history API, all-semantic causal graph,
dependency, or lifecycle change; the only review-surface change is
the companion-less accept ineligibility presentation (the historical
companion-less snapshot renders an explicit explanation with the
existing discard / fresh-workspace guidance and no accept control,
proven end to end, while the companion-bearing snapshot keeps the
real accept flow). The Compose e2e media-publication cycles seed
their preview workspace with genuine editorial operations through
the real editor session and trusted definer envelope, each carrying
real completion provenance (the earlier seed wrote COW rows with no
reservation or completion, which the whole-workspace provenance
check refuses); the canonical-versus-overlay differences, redirects,
filtering, and all three real media cycles are preserved. The
forward-only repair of the historical 017 content-type update
function is proven by a real HUMAN-on-AGENT model PATCH through the
repaired function with its COW, provenance, and authorization
behavior intact. The qualified baseline (PyPI `agent-cow-postgresql` 0.2.1,
Playwright 1.62.1) is unchanged; the round c security refresh
re-pins the browser payload to Chrome for Testing `158.0.8127.88`
(CfT revision `1727472`) through the coordinated SHA-256-verified
source, policy, and guard refresh documented in the supply-chain
docs, replacing `157.0.8103.78` (CfT revision `1717349`). Full PostgreSQL 14..18 matrix
qualification is required and is reported as the repository CI
executes the full children; acceptance state is tracked in the OAP
ledgers, and nothing here claims D5, MVP, or product completion.

## Exact heading-props row effects (083/13)

The heading row effect pilot (083/13, revision `080_001`) adds the
focused `test_heading_row_effects.py` module with twelve real native
tests on the disposable cluster, both HTTP paths at real login
boundaries and the real freeze/accept/discard lifecycles:

- Agent path (062): two same-resource writes under different
  operations retain both transitions with exact chaining (the first
  write's before image is the canonical row at first touch, the
  second's before image is the first's after image and version). The
  HTTP-level no-effect completion (identical props) records the
  trusted `no_effect` disposition and no fact. A real first write
  followed by a late request at the stale version is refused, rolls
  back, and leaves no fact and no completion; the corrected retry
  records exactly one fact.
- Editor path (060, Human-on-Agent): the real logged-in PATCH
  records a fact whose human principal is resolved from the
  in-progress human-editor reservation; the wire keeps the
  historical constant `row_version=1`; a replay returns the stored
  body before completion and never re-runs the definer, so it adds
  no second fact.
- First-touch control (item 3): two same-site workspaces both commit
  first touches before the winner is accepted; the winner publishes
  through REAL freeze + human accept; the four distinct sources
  (canonical at first touch, W1's earlier value, W2's published
  value, W1's actual new value) are each observed through a
  supported read path; the typed public conflict is exactly one
  `BASE_ROW_CHANGED` on the component; and both W1 transitions keep
  their exact facts. The second write's DML pre-image is proven to
  be the workspace's own effective COW row at write time — neither
  the concurrently published canonical row nor the session's
  first-touch baseline (the pilot's recorded observation limit).
- First-write race (item 3): the loser is paused exactly between the
  deployed definer's in-command read and its UPDATE by a
  fixture-only wrapper parked INSIDE the real
  `slaif_agent_component_validate_design` call (the wrapper is
  reinstalled from the live catalog and the original definition is
  restored on every exit, so the real command runs unchanged apart
  from the rendezvous). For the Agent path the observed parked
  backend is the request's own runtime login in the fixture
  database, with the definer's workspace structural locks (shared
  workspace key + exclusive page-structure key) already granted
  before the in-command read while the rendezvous request is
  pending. The Human-on-Agent Editor path takes no page-structure
  lock, but its request's state-changing workspace assert holds
  the workspace advisory key exclusively and its idempotency
  INSERT holds FOR KEY SHARE on the shared site row through the
  `control.human_editor_idempotency.site_id` reference to
  `control.site`. In the interval the sibling workspace's real
  HTTP first touch plus a REAL freeze are started, and the test
  observes the RESOLVED order instead of any fixture deadline: the
  parked command's transaction-scoped site-row lock (the Agent's
  pre-park FOR SHARE from the 039 require-cow-site recheck inside
  the pre-validator authorize; the Editor's FK row lock) blocks
  the freeze's real materializer at its site-row FOR UPDATE, so
  the test observes the exact native blocking edge (the freeze's
  reviewer backend waiting on the parked transaction id), proves
  the canonical row is still the pre-publication row, releases
  the real command and observes its ACTUAL outcome: the Agent's
  version-guarded UPDATE SUCCEEDS (200) against the
  pre-publication row - the "stale" expectation succeeds because
  the DML is deterministically ordered before the sibling
  publication - and the Editor's unversioned write lands with
  the constant wire `row_version=1`. Only then do the unblocked
  freeze and the real acceptance publish B, and each workspace's
  typed public surface records exactly one `BASE_ROW_CHANGED`
  conflict against the parked operation; the Agent's single fact
  keeps the pre-publication image pair (before = A at version 1,
  after = its merged value at version 2) and the Editor's single
  fact keeps the actual same-statement pre-publication image
  pair, while the effective COW view keeps the workspace's own
  merged value at its own version although the base moved to the
  published B. The ten-second product lock budget is not the
  oracle: only the observed native lock edge or the completed
  real job decides.
- Commit-time completion binding (item 1): a direct real-role
  definer invocation that records a Heading fact without a genuine
  completed 078 completion is refused at the actual COMMIT by the
  deferred constraint check (P0001) and the bounded observation
  verifies no residue — no fact, no staged COW change, no
  completion, no reservation — while the amended authority test's
  positive path performs the real 13-argument completion in the
  same COW session and commits.
- Rollback after a real write and evidence insertion (item 2):
  through each actual HTTP mutation envelope a fixture-only
  AFTER INSERT journal barrier witnesses, in the SAME transaction
  and before a bounded rendezvous, that the heading fact is
  staged and its after image matches the staged COW row; it then
  forces a real late completion failure (Agent envelope, HTTP
  503) or a real task cancellation (Editor envelope). The exact
  durable state (view row, pending operations, facts, family
  audit, completion journal, reservation) is compared before and
  after and is byte-for-byte unchanged, an independent
  connection proves the staged rows invisible before the
  transaction ends, and the same body + idempotency key retry
  succeeds with exactly one completed fact and one family event;
  an ordinary retry of the successful result remains inert.
- Pilot scope boundaries (item 4): an unchanged-props Editor
  write and a structural-only Editor write (the order key — the
  seeded heading sits in its Section's only allowed slot, so a
  slot change is outside the supported domain here) keep their
  legacy behavior and record no fact; a mixed props+structural
  change records the exact props pair (and claims nothing about
  the structural history); and the ordinary Human workspace path
  keeps its existing behavior byte-for-byte and records nothing.
- Attribution and isolation (item 4): same-resource sequential edits
  chain exactly across families (Agent then Human-on-Agent);
  cross-site denial is proven at BOTH real login boundaries (an
  Agent capability bound to another site, and an Editor session
  enrolled on another site) with no recorded effects; a Section
  props write through the same Agent path completes normally and
  records no fact (heading-props family only); the real freeze +
  human discard lifecycle removes the pending COW rows (public
  operations empty) while the committed facts remain; an old
  workspace without facts is unknown (no synthetic history).
- Authority and bounded format: every runtime role is denied the
  facts table and the owner-only recorder at real logins (no role
  EXECUTE at all); an owner call outside the trusted COW session
  context is refused before any effect (no general-purpose fact
  insert); a 16385-octet props image is refused by the table's own
  CHECK (23514); and the downgrade ratchet refuses at the operator
  level and at the direct-Alembic level, with the staged 079 head
  proving the 079 body's own refusal still intact behind it.

The module runs unfiltered as the eighth exact module path of the
trusted mutation-completion (TC) command in the existing PostgreSQL
14..18 Group B children, with no `-k` selection.

## Retained heading review facts (083/14)

The retained heading review facts increment (083/14, revision
`081_001`) binds the already-recorded `heading-row-effect/v1` facts
of reviewed operations to the immutable review. The focused
`test_retained_heading_review_facts.py` module adds six real native
tests on the disposable cluster:

- Real lifecycle (item 3): distinct same-Heading reviewed
  operations through the real Agent and Human-on-Agent HTTP paths,
  including an intermediate value that differs from the final value
  (the final props return to the original). A real freeze retains
  the exact ordered records (field-for-field the 080 facts, bound to
  the exact site/workspace/snapshot id and digest and the reviewed
  operation manifest digest); the trusted 078 completion and the
  public operation manifest set corroborate the identity. A real
  human accept in one workspace and a real human discard in a second
  settle the COW state, and BOTH retained reviews are reopened
  afterwards through the authorized product read with a fresh
  service connection — first via the current trusted pointer and
  then by the exact named snapshot (`?snapshot_id=`), which
  re-checks the snapshot row's own site/workspace association
  (a snapshot bound to the other workspace of the same site, and an
  unknown id, take the uniform 404). The retained bytes, digest and
  the original snapshot and media identity are unchanged by the
  publication.
- Pre-feature vs captured empty (item 2): a real freeze with no
  heading edits captures an explicitly empty set (`captured`, empty
  facts array, the exact canonical bytes of `[]`); the same review
  with no retention row — the shape of a pre-feature snapshot —
  answers `unavailable` with `pre_feature_snapshot`, and the two
  stay distinguished while the old review document is preserved.
- Budget and binding refusals (items 1 and 3): an owner-seeded
  over-budget coherent fact set (257 records, each with its real
  078 completion binding in the same transaction) refuses the whole
  freeze with no snapshot, no companion, no retention row, the
  workspace still FREEZING and the facts intact; a real 1-fact
  freeze then succeeds, and making the stored companion identity
  disagree with the fact's principal refuses the trusted capture
  (`HEADING_RETENTION_BINDING_MISMATCH`, P0001) before any write,
  leaves the existing retention row untouched, makes the authorized
  human read uniformly unavailable through the same bounded fixture
  (the read-time identity recheck), and serves the unchanged
  captured set again once the exact stored identity is restored.
- Exact pre-aggregation byte budget: 34 real same-heading Agent
  edits (each a distinct near-maximum props value under the Agent
  API props byte cap, the schema max_length and the 16384-octet
  per-value cap) sit below the 256-record cap while their EXACT
  canonical encoded array total (the 070 serializer ASCII-escapes
  each 3-byte test character to a 6-byte sequence) crosses the
  1 MiB ceiling - the a-round codepoint estimate of the two props
  texts still passes, so the refusal is established at the
  pre-aggregation check on the shared record projection, with no
  partial freeze or review state; a 24-edit legal set well under
  the ceiling is captured, and its stored facts_bytes equals the
  independently measured pre-assembly total (the post-assembly
  equality invariant the definer enforces).
- Atomic rollback after manifest staging (item 3): a fixture-only
  armed AFTER INSERT trigger on the companion table — installed
  before the real freeze and restored on every exit — fires
  inside the freeze transaction when the manifest row is staged
  (after the snapshot row, before the terminal job success), so
  the whole locked transaction rolls back: the snapshot,
  pointer, companion, retention and job state all roll back with
  the earlier mutation facts intact, and the supported retry
  path (the FREEZING re-enqueue claim) completes with the exact
  retained set.
- Authority and downgrade ratchet (items 1 and 3): the retention
  table is owner-only across every role (no PUBLIC, no role
  grants), the capture definer is worker-only and the read definer
  control-only at real logins, and the downgrade is refused at both
  the operator preflight and the direct-Alembic level
  (`HEADING_RETENTION_DOWNGRADE_UNSUPPORTED`, P0001) with the head
  and every object left exactly as found.

The module runs unfiltered as the ninth exact module path of the
trusted mutation-completion (TC) command in the existing PostgreSQL
14..18 Group B children, with no `-k` selection.

## Same-workspace human re-review (084/1)

The same-workspace human re-review increment (084/1, revision
`082_001`) joins the stale-site-revision refusal, the
`BASE_ROW_CHANGED` boundary and the retained per-snapshot heading
facts through one same-workspace human re-review with both snapshots
retained. The focused `test_same_workspace_re_review.py` module adds
four real native tests on the disposable cluster:

- Whole-session lifecycle (criteria 1-4): W and X edit the SAME
  Heading differently at revision A through actual Agent mutation
  contexts (distinct capabilities, distinct operation IDs) and both
  freeze against A through the real human definer and the real
  worker. Approving X publishes canonical B reflecting only X's
  edit (exact canonical row and revision, zero W publication).
  W's A-snapshot approval through the same real path fails durably
  with `SITE_REVISION_CHANGED` (job terminal FAILED, workspace back
  in read-only review, edit and original snapshot intact, no
  canonical write, no new publication audit or cache outbox). The
  real human re-review of W (verified stale: the durable failed
  ACCEPT job for the exact snapshot with its payload site and both
  digests matching the stored snapshot digest and the companion
  manifest digest, whose own `snapshot_digest` must match) atomically
  advances the trusted pointer to a new immutable W snapshot at B
  with a valid digest and W's pending edit as the review content,
  while the A snapshot, stored payload, digest and per-snapshot
  companion evidence are retained byte-for-byte; the same W
  first-touch baseline, operation identity and heading row effects
  persist, the capabilities stay revoked, the regular review read
  and the unqualified heading-facts read follow the trusted pointer,
  and the exact prior snapshot still renders with its ORIGINAL
  retention evidence (both snapshots reviewed the same operation, so
  the served facts agree). A broken base node (labeled fixture
  corruption, removed before the retry) refuses the whole locked
  finalization and rolls it back atomically (no snapshot, pointer
  unchanged, job terminal FAILED), and the operational retry
  succeeds with exactly one new job. The old identity is then
  refused WITHOUT a new approval job, and approving W's B snapshot
  with both current digests reaches the existing whole-session
  `conflict_policy="error"` boundary: the durable
  `BASE_ROW_CHANGED` outcome, workspace CONFLICTED, exact canonical
  B row and revision unchanged, and still no W publication audit or
  outbox.
- Endpoint gate matrix (criterion 5): the real HTTP surface of the
  new route — unauthenticated/invalid session uniform 401,
  state-changing without (or with the wrong) CSRF 403, the strict
  one-field body (extra or missing field 422), a human without the
  required `workspace:freeze` authority uniformly 404 (stable code,
  indistinguishable from a foreign workspace), the exact
  site/workspace binding (another site, unknown workspace, crafted
  ids), the NULL pointer shape (the strict body rejects a NULL
  snapshot with 422 and the inner transition returns the typed
  `RE_REVIEW_SNAPSHOT_NULL`, P0002 refusal before any state read),
  and the stale matrix (a named snapshot the pointer no longer
  selects is 409 in every state, the fresh-workspace
  never-failed-accept shape is the typed unverified refusal, and a
  repeat during FREEZING returns the SAME live job while a stale
  name still refuses).
- Guarded downgrade refusal (safe compatibility guard): the direct
  Alembic downgrade is refused BEFORE any effect, atomically, for
  both shapes — a re-review retained multiple snapshots
  (`RE_REVIEW_DOWNGRADE_RETAINED_MULTI_SNAPSHOT`) and a re-review
  still in flight (`RE_REVIEW_DOWNGRADE_IN_FLIGHT`) — with the head,
  every function, the retained snapshots, job, capability and
  workspace state left exactly as found (byte-for-byte snapshot
  comparison), and the refusal proven on the real reached
  two-snapshot state (a real re-review completed, then a rolled-back
  second finalization for the in-flight shape).
- Safe rollback in the single-snapshot state: with no re-review ever
  run the downgrade restores the exact 071_001 read model and the
  exact 070_001 freeze body (the restored prosrc carries no 082
  bytes and the original plain post-branch read is restored), drops
  the two 082 functions, and the 081
  downgrade ratchet remains the next line of defense.

The module runs unfiltered as the ninth exact module path of the
workspace media, role, freeze, promotion and rollback command (M)
in the existing PostgreSQL 14..18 Group B children, with no `-k`
selection. The real same-workspace case is also in the public NGINX
E2E suite (`freeze-review-snapshot` spec): W and X edit the same
seeded Heading through real Agent HTTP PATCH, X is approved through
the real human endpoint, W's A approval fails durably, the new
re-review route is exercised through the authenticated browser
session (CSRF, nonmember, wrong-site, stale-name and strict-body
gates), the re-review points the current review to the B snapshot
with both snapshots retained, the retained heading-facts read is
proven through the authorized endpoint, the old identity is refused
without a job, the B approval reaches the CONFLICTED boundary with
the structured `BASE_ROW_CHANGED` job outcome, and the public site
through the NGINX origin still shows X's edit only. The
authenticated NGINX review renderer is exercised for the A review
and, after the re-review, for the B review (exact banner digest,
coherent drift, the rendered Heading), and the exact-id internal
Render review path is exercised for the earlier frozen A review
after the trusted pointer moved to B (and for the B review): the
earlier frozen page remains available through the existing
authorized route, with no new public history UI.
