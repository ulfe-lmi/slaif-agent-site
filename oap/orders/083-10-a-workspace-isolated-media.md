# 083-10-a — isolate media metadata and reference changes in workspaces

This order takes effect only after atomic canonical publication, selection by
active and one exact strategic control OK. ROOT owns design, scope, acceptance
and merge. PRIMARY owns implementation, verification, Git/PR/report and response.
Use the existing visible PRIMARY pane21; PEER17 is read-only unless ROOT assigns
a separate bounded task. No hidden agent. No new CLI/profile/effort change;
restart an actually crashed CLI only as codex --yolo --profile early-beta.

## Identity and independently verified starting state

Objective083 remains unfinished. Semantic increment083/10, round083-10-a,
CREATE_NEW_PR, exactly one NEW PR. Required branch:
oap/083-10-a-workspace-media-isolation. Base main:
d888b37ffe3b3685c3743dd054a953e148d6dbf2, tree
84c3a45fd12b9fb696b5ddd1fa09aec6d84649dc. Reconcile live GitHub before edits;
return unexpected base/PR changes to ROOT, never reset or silently rebase.
Repository: <https://github.com/ulfe-lmi/slaif-agent-site>.

PR112, increment083/8, was accepted/merged2026-11-12T08:58:50Z; ROOT verified
default main and exact parents[40cd1721,83c0606e]/reviewed tree. Its own20 required
named/app checks and10 actual PG14..18 children all passed, full Compose and
fresh six-image evidence independently reviewed. All failed/qualified history
and the immutable report's governance erratum remain; no product/MVP claim.

083/9 is ALREADY USED: PR113 was accepted/merged2026-11-02T04:20:53Z as
40cd172109a22ef5f342589b59a4293f35379651, the Node/Brotli/Chrome/Python security
prerequisite. Preserve its orders/reports and083-9-a checkout. Never reuse9.
Open Dependabot PR105/114/115 are unrelated; do not merge, close or amend them.

Use a fresh standalone clone at
/home/janezp/codex-work/slaif-agent-site-083-10-a from the verified remote base,
not a shared worktree that changes the dirty human checkout's refs. The target
was absent at preparation. Preserve all earlier checkouts/evidence/human files,
codex.sh and refs; no reset/stash/rebase/force/prune/foreign cleanup.

Canonical OAP remains /home/janezp/codex-work/slaif-agent-site/oap. After valid
control OK, read its exact active and unique order. Copy THIS order and active
byte-exact into the fresh clone for versioned publication; never author them.
There is no oap directory under the strategic workspace. Read coding AGENTS,
coding communication protocol, compact architecture and applicable nested law.
Do not open full ARCHITECTURE.md without direct HUMAN instruction.
Actual FIFOs are /home/janezp/codex-supervision/slaif-agent-site/control.fifo
(inode4470111) and response.fifo in that SAME parent (inode4470112), real FIFO
dev2304. Verify actual type/identity before I/O; never create guessed ordinary
files or use /home/janezp/control.fifo or /home/janezp/response.fifo.

## Human behavior and bounded semantic contract

Uploading an asset or changing its editorial metadata/references in workspace A
must affect A only until authorized human promotion. Another same-site workspace,
canonical APIs, public pages and public media authorization must remain unchanged.
Discard removes only pending editorial effects. Immutable bytes may be shared;
shared bytes never authorize site-wide pending metadata or public visibility.

Repair the complete existing MediaAsset path coherently: registration, metadata
updates/reference deletion, pending lookup, private preview, frozen media closure,
finalization, atomic publication, replay, deduplication and failure rollback.
Use the EXISTING COW MediaAsset/public content view and supported public
agentcow.postgres high-level sessions/reviewer. Do not create a bespoke parallel
workspace-metadata overlay or depend on private foundation tables/undocumented SQL.
Normal trusted view DML does not require inventing a new SQL-callable SDK API.

Current source facts, not fresh HTTP/ACL results:068 human/agent registration
and metadata update explicitly target media_asset_base despite surrounding COW
sessions.031 reference deletion targets the content view.069 lawfully permits
human Editor changes in an AGENT workspace. The media finalizer currently expects
a base asset and marks public status before the actual reviewer transaction.
Tests asserting same-site pending-upload visibility encode the defect; they do
not redefine architecture. Preview/frozen view readers already exist but must
be proven with newly pending assets, not presumed correct from comments.

## Implementation requirements

1. Add a new ordered platform migration after076, anticipated077_001. Never edit
   historical migrations. Make existing online human/agent registration and
   metadata/reference changes go through the authorized workspace's COW view,
   with trusted server-owned site/workspace/operation context and lifecycle lock.
   Preserve actual scope, quota, idempotency, validation and audit envelopes.
   No ordinary upload/update/delete may directly write canonical base metadata.
2. Keep existing HTTP contracts and authority boundaries. Human upload,
   human metadata PATCH/reference DELETE and agent upload/read retain their
   existing semantic endpoints. Preserve the lawful human-on-AGENT path and all
   three existing audit families. A no-effect dedupe is not fabricated as a new
   foundation operation; audit completion must remain honest and atomic.
3. Preserve canonical-asset deduplication and existing stable asset IDs. An
   existing visible asset may be reused according to the current documented
   no-op dedupe contract; explicit metadata edits remain workspace changes.
   Fresh identical-byte proposals in different workspaces must not expose each
   other's pending metadata. Replays must preserve the original result/identity.
   If acceptance races on site revision, first-touch or uniqueness, fail safely
   with an honest typed conflict/validation result, not silent overwrite or
   rewriting approved IDs. Do not require both conflicting proposals to publish.
4. Preserve the immutable MediaStore, content hashes, byte integrity, staging/
   public/private-artifact separation, one-link store rules and retention.
   No new storage layout, mutable bytes or physical byte-GC work. Byte preparation
   may precede promotion only under the harmless-unreferenced-orphan rule;
   public HTTP must not serve an uncommitted/unapproved asset merely because a
   copied object exists. Do not equate shared bytes with one staging inode.
   Necessary retention-aware discard/cleanup adjustments for this media path
   are in scope; a general byte-reclamation/GC service is not.
5. Resolve pending assets from the correct authorized workspace/frozen binding.
   Active preview and immutable frozen media authorization must remain private,
   site/workspace/snapshot-bound and digest-gated through cleanup and replay.
   Preserve v2 snapshot format, exact keys/versions, retained historical reads,
   common renderer and existing media replay/inverse normalization. No new
   manifest/version or approximation of preview is authorized here.
6. Move publication-derived metadata/public-status mutation into the ACTUAL
   reviewer transaction with foundation promotion, site revision, promotion audit,
   workspace/job success and cache outbox. The prior pre-transaction base mark
   is not an accepted implementation. Prepare/copy bytes separately; inside the
   real reviewer transaction use least-authority product helpers and the real
   reviewer connection. Keep deferred constraints and conflict_policy="error".
   No nested fake COW, private foundation SQL or independently committed mark.
7. Verify actual direct grants/NOINHERIT behavior. Runtime/editor/control/media
   processes must not gain canonical publication authority. Consciously revoke
   or confine the unwired legacy canonical creator; preserve lawful one-shot
   trusted initialization. Publication-derived helper execution belongs to the
   separately authorized reviewer transaction, not an agent-facing process.
8. Fresh installation and upgrade from the baseline must preserve existing
   canonical media and retained review snapshots. Do not re-COW an enabled table,
   clone a private pending-row guard or remove pending history without proving
   the need and supported lifecycle behavior. Follow platform migration policy.
   Test/document downgrade or explicit fail-closed refusal; never silently
   restore unsafe canonical-write authority or discard data for reversibility.

## Review budget and non-goals

Planning footprint: production/config5..10 files, one new migration,
tests/evidence4..8 paths, generated contracts0, docs3..5, OAP order/active/report3;
approximately1000..2500 substantive added/removed lines. This is a review plan,
not a quota to game. Count all changed files and gross lines from the verified
base, grouped by these categories, including meaningful evidence and generated
changes. At20..30 implementation files or several thousand substantive lines,
give ROOT the actual cumulative scope and remaining coherent closure forecast
before adding adjacent work. Never pack/minify/hide evidence to fit a cap.

Expected inspection closure: latest media SQL definitions/grants; media_service
database/media_http/finalize; Editor mutation envelope and content-model service;
Agent media registration; review_worker snapshot/accept transaction; current076
private/frozen media authorizers; bootstrap/readiness and affected media tests.
Function signatures/adapters may stay unchanged where actual proof supports it.
Internal SQL signatures, callers and grants may change as needed to enforce
the trusted context; unchanged HTTP semantics do not freeze those internals.
Do not infer that a new parameter is mandatory merely from old function arity:
verify supported server-owned transaction context and all site/operation guards.

Non-goals: D5 immutable operation/audit manifest, exact approved-U enforcement,
causal graph/selective UI,071 read-model replacement, conflict feature family,
new fields/components/MCP/import, byte-GC/backup, redesign of media storage,
new HTTP routes, new role family, dependency/lock/browser/image refresh,
infrastructure/workflow redesign, hosted services or release claims. Preserve
foundation PyPI agent-cow-postgresql==0.2.0 and frozen registry hashes. Necessary
focused test wiring in the existing CI matrix is allowed; no matrix reduction,
skip, weakened oracle, suppression or vulnerability exception.

## Acceptance and executable proof

A1: Unique fresh correct PR/base/branch; exact activated transcript; grouped
bounded diff and honest docs. No other PR or prior report/order is changed.

A2: Real human and agent upload on fresh baseline demonstrate the premature
canonical/same-site visibility defect before the fix. Preserve exact source,
commands and actual red result; do not fake the regression by missing helpers.
On repaired code, real HTTP + real COW prove pending metadata/reference writes
in A, while canonical and SAME-SITE workspace B remain unchanged. Test both
fresh pending assets and edits/deletion of an existing canonical asset. Preserve
cross-site/scope/role/state/idempotency/quota denials and normal no-op dedupe.

A3: Human Editor lawfully PATCHes/DELETEs an agent-uploaded asset in its AGENT
workspace; the correct workspace read sees it, another same-site workspace and
canonical do not. Actual proper audit families and transaction atomicity remain;
no claim that all historical audits equal current pending operation U.

A4: Through public NGINX, pending private media and real rendered preview work;
freeze with the actual worker captures correct immutable descriptors/inventory/
digest; frozen reads remain authorized and stable after lawful edits elsewhere,
discard or promotion cleanup. The frozen workspace itself remains read-only.
Test private/public/cross-site/snapshot substitution denials.
Keep current desktop/tablet/phone and six stable engine pairings meaningful.

A5: Actual human accept with the real review worker publishes metadata/reference
effects and public status atomically, matching approved frozen media and bytes.
NEW pending assets become publicly readable only after committed acceptance;
existing canonical assets keep their prior public authorization/values while
workspace edits or deletion are pending. Discard leaves
canonical/other workspaces/retained review bytes intact. Accept/discard/replay and
idempotency remain honest. Same-hash concurrent workspace proposals and delayed
acceptance produce supported dedupe or safe drift/conflict/uniqueness behavior,
never silent overwrite/ID rewrite. Include multi-workspace before/after values.

A6: Inject a failure at the real media-mark/promotion transaction boundary in
trusted disposable tests, retaining the actual worker/reviewer/COW transaction.
Prove no partial canonical media/content, revision, promotion audit, successful
workspace/job or outbox commit; pending state is preserved. Legitimate failed-job
handling may be separately visible and must be described honestly. A pre-copied
orphan is not publicly readable and is not falsely called collected. No production
test-control endpoint or mock foundation can substitute for this rollback proof.

A7: Actual privilege tests and fresh/upgrade/migration-rollback-or-refusal tests
prove least authority, no canonical online bypass and preservation of existing
media/retained v2 snapshots. Source grant declarations alone are insufficient.

A8: Run complete current Python, process, Node and preparation gates specified
by coding AGENTS with frozen versions/locks, plus the FULL current backend DB
integration suite on PostgreSQL18 and focused new media/role/concurrency tests
on each PostgreSQL14..18. Wire meaningful media regressions into the existing
PG matrix where missing; run actual current commands and report direct natives.
Historical If/FULL or PR112 runtime passes are not fresh proof for changed code.
Run fresh full Compose through public NGINX at the new implementation, retaining
real fixture outputs and cleanup. Required CI/CodeQL, current20 named/app gates,
all10 actual PG children, full Compose and fresh six-image evidence remain
mandatory. No pass for missing/skipped/pending/failed work or inferred counts.

## Runtime autonomy and failure handling

Routine tooling, browsers, PostgreSQL, packages and safe local services belong
to the coding agent, not the human or ROOT. Use existing approved frozen tools
where available; own safe installation/setup when needed. Prevent package hooks
from restarting global services (NEEDRESTART_MODE=l). No production credentials,
foreign Docker socket/context, global daemon restart, bridge/firewall/prune,
global process scan or unrelated cleanup. Use fresh owned private test resources
and known rootless-engine patterns; prove actual identity/ownership before action,
bound child lifetimes, retain direct native/EOF/reap and healthy owned cleanup.

Normal in-scope implementation, meaningful focused diagnosis and verification
can proceed without repeated per-command approval. Record actual failures and
fix causes; do not rerun merely for green or fabricate prior qualification.
Preserve old engines' evidence and all old attempts. A real protected-resource,
unsafe-authority, external-access or architecture ambiguity returns facts to
ROOT; routine setup and our mistakes are not human permission/installer chores.

## GitHub, documentation, report and exact synchronization

Fetch/reconcile the exact remote base; create the one fresh branch/PR, no amend
of PR112/113 or bot PRs. Commit activated order and active unchanged. Push only
literal git push -u origin HEAD:refs/heads/oap/083-10-a-workspace-media-isolation.
Keep PR body current and concise: behavior, actual tests, risks and limitations.
Update relevant media/security/testing/operations docs and versioned increment/
MVP ledgers:083/8 merged atd888b37f,083/9 already merged at40cd,083/10 current;
do not claim D5, complete083, MVP, byte-GC, release or product completion.

Inspect and repair safe in-scope CI failures; return precise facts for scope
or policy issues. Do not cancel a running subject just to push another receipt.
Before the final report, all non-report implementation/transcript state and the
correct PR must already exist remotely. Report each A1..A8 result with actual
source/command/native/environment/evidence, failed/skipped/not-run/pending work,
grouped scope, setup, migration/privileges, docs, unresolved risk and PR identity.
Do not repeat the entire prior26-round history or overclaim from a narrow test.

Publish exactly one immutable reports/083-10-a-workspace-isolated-media.md,
with literal Implementation head SHA and Report publication commit: SELF.
Lint its complete same-filesystem TEMP using the exact repository configuration
with --no-globs and the literal file, require native0/one file/zero issues,
then fsync/atomic rename and identical execution/canonical copies. Final SELF
commit changes ONLY that report and has the literal implementation sole parent.
Push and independently verify actual PR head, parent, path and exact bytes.
Never edit activated order, active content or published reports.

Then send ONE response containing exactly two ASCII bytes: `OK` (hex `4f 4b`),
with no newline or other content, to the actual response FIFO in the strategic
workspace, inode4470112/dev2304. Close the writer and record native. Do not fsync a
FIFO, replay control/response or create a competing reader. Report-head CI may
still be pending truthfully; ROOT independently waits/reviews its OWN checks,
artifact, scope and policy before strategic-only merge and remote-main proof.
No executor merge/auto-merge. Full product goal remains active afterward.
