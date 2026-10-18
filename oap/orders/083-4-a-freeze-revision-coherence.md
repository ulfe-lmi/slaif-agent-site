# OAP Work Order — 083-4-a: freeze-time canonical revision coherence

> STATUS: ACTIVATED strategic order. Operative only after exact active
> 083-4-a and this round control FIFO OK. Timing is in the strategic ledger.

## Identity and verified predecessor

ID083-4-a, numeric083 increment4, CREATE_NEW_PR from freshly verified main.
Exactly one new PR/branch `oap/083-4-a-freeze-revision-coherence`; no other PR.
PR title `OAP 083-4-a: freeze-time canonical revision coherence (083/4)`.
Verified remote base `c5b5d425b9600ef7ee85c22453bb4122bf1fbfa9` at
2026-10-18T04:54:28Z. PR102 accepted/MERGED04:38:55Z; parents214909f3 and
accepted S-e70d807a0 (all20PR checks SUCCESS, firstattempt). Postmerge
CI39097820342 and CodeQL39097820344 both completed SUCCESS at exact base,
run_attempt1, independently verified04:53:53Z. Push roster18SUCCESS plus
intentional Dependency review SKIPPED; separate PR CodeQL aggregate absent.
Remote main and no existing083/4 PR/order/report reverified. These push
conditions do not relax the20 final-PR check requirements below.
Human full-product goal remains
active; numeric083 remains PARTIAL. This is one prerequisite, not completion
of generic immutable review, publication or conflict lifecycle.

Human requires sole visible executor in same tmux window's other pane,
exact `codex --yolo --profile qwen-neumann`; no provider/model override.
Actual repo `/home/janezp/codex-work/slaif-agent-site`; strategy
`/home/janezp/codex-supervision/slaif-agent-site`. Verify actual FIFO objects
there. Coding reads control/writes response, exact ASCII OK/4f4b/noLF.
Only act after this round signal and exact active083-4-a; never select bymtime.
Read coding AGENTS/protocol, compact architecture and relevant governance.
Do not open full ARCHITECTURE.md. Preserve untracked .codex/,codex.sh and
CODEX-SESSIONS.md. Routine setup/DB/services/packages belong to executor.

## Concrete problem, semantic contract and scope

Source at PR102 final implementation f459ad38 (unchanged in this family):
070_001 materializer reports ws.base_site_revision, established at workspace
creation. Freeze worker obtains exclusive workspace lock but visibly no
canonical site-revision lock around materialization+snapshot completion.
Acceptance `_verify_snapshot` compares rematerialized digest before reporting
stored/current revision mismatch. Reproduce exact behavior before correction;
these source findings are not invented runtime observations.

Required result: a freeze at canonical revision B retains coherent reviewed
content and B as its review base, even if workspace creation was A. A concurrent
same-site publication is serialized with freeze materialization/completion.
Post-freeze revision drift C produces SITE_REVISION_CHANGED before digest
rematerialization can obscure the stale-review reason. Preserve original
first-touch COW baselines and all old snapshot bytes/digests. No rebase.

Bounded implementation areas: new developer migration075_001 replacing only
the affected product freeze/materializer SQL as necessary; freeze worker,
acceptance preflight revision-error ordering; exact bootstrap/head/privilege
pins; focused unit/integration/public E2E evidence; truthful narrow docs.
Never edit old migration bodies to hide deployed behavior. Document exact
new SQL functions/grants and justify every edge; no new runtime authority.

## Requirements and non-goals

1. Capture current canonical site revision within the same transaction that
   materializes the workspace and completes the immutable snapshot/REVIEW state.
   Acquire established workspace lock then canonical site-row lock in an order
   consistent with acceptance; retain the site lock through snapshot/job commit.
   Bound lock waits, preserve cancellation/rollback/job recovery. Do not hold
   unnecessary site locks while waiting on unrelated browser evidence. Explain
   lock ordering across workspace row, advisory lock, site row and foundation
   locks, and prove no same-site freeze/accept deadlock in the ordered cases.
2. Do not overwrite workspace.creation/base revision or first-touch foundation
   row/schema baseline to make the new snapshot current. Existing review payload
   base_site_revision means reviewed canonical revision, as architecture already
   requires. Keep provenance/original workspace revision distinguishable where
   existing APIs expose it. Re-materialization uses the same locked revision
   meaning; no synthesized digest equivalence or normalization of real changes.
3. Before replay normalization/digest comparison in acceptance preflight,
   validate stored snapshot/site/workspace binding and trusted stored revision
   against locked current revision. If unequal, preserve stable error
   SITE_REVISION_CHANGED and no canonical mutation/media finalization/revision/
   terminal-accept/audit/outbox effect. Preserve the final atomic reviewer
   transaction revision gate independently; no TOCTOU weakening.
4. Old immutable snapshots remain unchanged and viewable under existing auth.
   An old stale snapshot remains stale; do not rewrite it or promote based on
   newly observed content. Preserve strict requested snapshot_id/digest/summary
   acknowledgement, current snapshot selection and membership/recent-auth gates.
5. New migration upgrade/downgrade and privileges fail closed; downgrade
   restores exact preceding function definitions/ownership/search_path/grants.
   Foundation remains public registry0.2.0 with frozen locks; no private SQL,
   monkeypatch, upgraded dependency, relaxed FK or overwrite conflict policy.
6. Explicit non-goals: model/content/style payload expansion; frozen dynamic
   rendering; operation/dependency/audit completeness repairs; re-review UI or
   multiple-snapshot lifecycle; generic page-DML promotion; MCP/source/News/GC/
   backup/dependabot; browser/security pin refresh; topology/new services;
   agent routes/capability catalog/renderer/Puck. Known foundation composite-FK
   dependency limitation remains disclosed; composition-only proof is scoped.
7. Preserve all architecture authority/privacy boundaries: server-owned context,
   every online human/agent write via workspace, separate roles, human-only
   reviewer-atomic publication, immutable media/private artifacts, browser
   observational confinement, no new credentials/outbound/telemetry/license.

## Observable acceptance and evidence

A. Reproduce an actual public authenticated two-workspace composition scenario:
   W created/edited at A; a different authorized human workspace publishes
   an unrelated composition change to B; W then freezes. Frozen document must
   retain B and the meaningful visible B-plus-W content, with byte-valid digest.
   Displayed reviewed/current revisions agree before another publication.
   Never use a test-only actor or hidden canonical SQL mutation for the proof;
   fixture setup alone may use privileged seed code. Keep public origin through
   NGINX in browser E2E. No broader generic-model readiness claim.
B. A controlled database concurrency test blocks a real same-site accept and
   freeze in each ordering: if accept wins, snapshot records new revision and
   its content; if freeze wins, snapshot completes coherently before acceptance
   progresses. No mixed revision/content, deadlock or indefinite unbounded test.
   Use synchronization on actual production lock surface, no sleep-only race.
C. After freeze, a valid different workspace accepts C. Approval of old snapshot
   is refused with SITE_REVISION_CHANGED, not digest error. Prove canonical
   bytes/revision/audit/outbox unchanged by the refused attempt; pending W rows
   remain. Preserve the existing safe recovery state, no re-review feature yet.
D. Prove first-touch touched-row baseline unchanged across the B freeze using
   public frozen foundation conflict inspection and before/after facts. A
   concurrent change to a touched row still reports BASE_ROW_CHANGED; do not
   substitute an unrelated-row test or force generic page-DML acceptance through
   the known dependency bug. Preserve human/capability/site-negative tests.
E. Cancellation/DB failure before completion rolls back snapshot insertion and
   REVIEW/job terminal together; no site lock leaked. Reclaimed freeze remains
   idempotent. Exercise existing browser evidence drain/cancel and worker retry
   semantics without broad behavior changes. Old snapshot remains byte-identical.
F. Migration roundtrip, exact privilege delta/no extra roles, all current local
   Python/process/Node/preparation gates, complete unfiltered integration directory
   including new cases, complete public Compose/six-device smoke, and all20 named
   required GitHub checks on final report-only head. Report actual collection
   count/results, failures/skips honestly. No arbitrary CI reruns until green.
   Contracts/packages/locks/pins unchanged; recursively stripped OpenAPI digest
   remains921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83.

Required final-PR check roster (20; independently verified live main ruleset
20934043 at the preceding merge; reconcile any actual policy change):

- `Analyze (actions)`
- `Analyze (javascript-typescript)`
- `Analyze (python)`
- `CodeQL`
- `Compose and edge packaging`
- `Dependency review`
- `Detect supported languages`
- `Foundation PostgreSQL 14`
- `Foundation PostgreSQL 15`
- `Foundation PostgreSQL 16`
- `Foundation PostgreSQL 17`
- `Foundation PostgreSQL 18`
- `Markdown`
- `Mermaid`
- `Node contracts`
- `Python 3.12 quality and package`
- `Python 3.13 quality and package`
- `Python 3.14 quality and package`
- `Repository policy`
- `Supply-chain evidence`

Every name must be COMPLETED/SUCCESS at exact final report SHA, correct
integration application (15368; aggregate CodeQL57789), no missing/neutral/
skipped/cancelled/pending result. Report actual workflow run IDs and attempts,
not nonexistent check-run attempt fields. No deterministic rerun until green.
One genuine documented CI-flake rerun of an unchanged head is permitted only
with original log/cause and exact attempt; never relabel a deterministic defect.

## Budget, docs, GitHub and exact handoff

Predeclared estimate: up to6 substantive production/config files including
1migration, up to12 test/pin files,0generated, up to6docs,3transcript paths.
Target <=1600 substantive implementation/test lines excluding necessary exact
SQL downgrade restoration; itemize that duplication separately. Review trigger
20–30production files or several thousand substantive lines requires explicit
strategic reassessment before broadening. No new semantic family. At trigger
close coherent increment; do not hide size through many small continuations.

Docs must explain frozen review revision versus creation/first-touch baseline,
what this repair proves and the remaining complete-snapshot/render/operation/
conflict work. No numeric083 COMPLETE, MVP/release-ready or generic-page-DML
accept claim. Reconcile current-truth surfaces only as needed with durable PR
references; no historical transcript edits. Unit tests must fail when the new
revision/lock safeguard is removed, not merely inspect matching constants.

Fetch/reconcile verified main, new branch/PR; commit activated unchanged order
and active; bounded implementation/test/docs commits; push exactly one PR, no
merge/auto-merge. Name all required commands/actual exits and any environment
repairs. No exception authority. On outside-scope failure preserve evidence and
return honest status rather than expanding scope or discarding failure history.

Final report exact basename083-4-a-freeze-revision-coherence.md, status one enum,
branch/PR/base/literal40hex Implementation head SHA, Report publication commit:
SELF, order hash/active bytes, percriterion source/test/log/CI/runattempt proof,
full grouped budget/variance, security/known limitations. Lint complete report
with exact repository markdownlint config before same-filesystem atomic publish.
Commit/push report-only child as finalS whose firstparent is literalI; verify
remote head/parent/solepath/bytes before exactresponseOK. No repository mutation
followsS. Block on control again; only strategy reviews/accepts/merges/advances.
