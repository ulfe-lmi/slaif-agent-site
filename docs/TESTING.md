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
