# OAP Work Order — 068-g

## Objective

Continue objective 068 on PR #59. Preserve every accepted 068-d through 068-f
security, CSP, production-identity, public-HTTP, normalized persistence,
stable-ID, general sibling-reorder, and move/Undo/Redo result. Correct one
narrow remaining selection-lifecycle defect: after that continuity work has
served its purpose, an explicit user selection of another Puck component must
take precedence and must not snap back to the previously moved component. Do
not merge.

## Verified starting state and finding

- Numeric objective: `068`; round: `068-g`.
- Mode: `CONTINUE_SAME_PR`; amend only PR #59 on
  `oap/068-puck-editor`. Do not create another PR.
- Begin from verified remote 068-f report head
  `42ef4ace4a0f17fd939f6f2599d2663c701ce953`; its only parent is the
  implementation head `e46c89ba52090eb4cd3ee353756d2390962d555c` and it
  changes only `oap/reports/068-f-preserve-puck-selection-and-history.md`.
- PR #59 remains open, non-draft, mergeable, and on `main` /
  `oap/068-puck-editor`; reconcile live GitHub before editing and report any
  difference.
- 068-f correctly dispatches a history-recording Puck `reorder`, then a
  non-recording destination `setUi`, and uses the moved stable ID to repair
  selection across Puck data transitions including visible Undo/Redo.
- The remaining defect is concrete in
  `apps/web/src/admin/composition-editor.tsx`: `movedComponentId.current` is
  assigned when a move starts but is never released, while the repair effect
  depends on `itemSelector`. A later explicit click on another component
  changes `itemSelector`, reruns the effect, resolves the old moved ID, and
  dispatches `setUi` back to that old component. The user can therefore become
  trapped on the previously moved selection even though 068-f's move/Undo/Redo
  fixture passes.

## Strategic context

Puck must remain a functional authenticated human editor, not merely pass one
scripted gesture chain. Automatic selection continuity is valid only while
reconciling the moved component across the associated data/history transition;
it must never override a subsequent deliberate human selection. This is a
client-state lifecycle correction, not permission to redesign Puck integration
or change the accepted CSP decision.

## Bounded scope

Implement only the smallest supported Puck selection-lifecycle correction and
the evidence needed to prove it. Likely paths are the existing editor adapter,
its focused tests/helper if needed, the strict 068 browser contract, and
truthful API/testing documentation. Commit this order and exact `oap/active`
bytes unchanged with the implementation.

## Explicit non-goals

- No new PR, route, API, component family, catalogue feature, publication,
  preview, workspace-management UI, or responsive redesign.
- No CSP, script policy, authentication, authorization, capability, database,
  migration, role, privilege, COW, audit, idempotency, or operation-contract
  change.
- No Puck fork/patch, private store mutation, private history rewrite,
  `setHistories`, direct controlled-data replacement, `setData` reorder, or
  remount-based selection workaround.
- Do not weaken the accepted editor-only style exception or strict public
  renderer/script CSP.
- Do not merge or activate another objective.

## Requirements

1. Preserve 068-f's exact public action plan: one supported Puck `reorder` with
   `recordHistory: true`, followed by destination `setUi` with
   `recordHistory: false`; no additional history entry.
2. Preserve the same stable moved component selection after Move down, visible
   Undo, and visible Redo, including correct first/last boundary controls.
3. Bound automatic selection reconciliation to the associated data/history
   transitions. A subsequent explicit user selection of a different component
   must release or supersede the old moved-ID continuity state before any
   repair can snap it back.
4. After the explicit selection, the newly selected component must remain
   selected after React/Puck effects settle, and Move up/Move down controls
   must reflect its actual current selector and permissions.
5. A later independent reorder must be able to bind continuity to its newly
   selected component; do not solve this by permanently disabling continuity
   after the first move.
6. Fail closed for missing/stale IDs, selectors, permissions, root and nested
   zones, and boundaries. Do not synthesize authority or mutate composition
   data merely to repair selection.
7. Keep 068-f's Puck 0.20.2 history-debounce handling truthful. A test may wait
   for the documented history entry before visible Undo/Redo, but must not use
   timing to mask selection snap-back.

## Observable acceptance criteria

### Focused behavior

- Tests prove the exact two-action move plan and no second history record.
- Tests or a narrowly extracted lifecycle helper prove at minimum: continuity
  for the moved ID across data/history transitions; deliberate selection of a
  different ID releases/supersedes that continuity; the different selection
  remains stable; and a later move can bind a new ID.
- Existing root/nested, first/last/middle, stale/no-selection, permission, and
  stable-ID cases remain green.

### Strict browser path

Extend the existing real Puck/public-NGINX Objective 068 browser scenario; do
not substitute API-seeded gestures. It must still prove visible add, Move down,
settled history, visible Undo, visible Redo, final-only save, reload, normalized
stable IDs/order, CSP cleanliness, and exact four backend operations. In
addition, after Redo and before Save:

1. explicitly click/select the other visible component;
2. prove it remains selected after effects settle rather than snapping back;
3. prove its Move up/Move down boundary state is the inverse of the previously
   moved last component; and
4. save the unchanged final redone order and retain the exact normalized and
   four-operation evidence.

Use stable IDs and observable Puck state/controls, not class-name coincidence.
The strict observer must retain zero relevant CSP, console, page, network, and
server failures.

### Security and scope

- Diff confirms no CSP, backend, database, migration, role, privilege,
  dependency, lockfile, secret, deployment, or trust-boundary change.
- Editor authentication and normalized trusted rendering remain unchanged.
- No user/agent raw HTML, script, style, or executable component capability is
  introduced.

## Verification

At minimum run and report exact commands/results for:

- focused composition-schema/editor tests covering the lifecycle and action
  plan;
- web lint, typecheck, test, and production build;
- repository Node lint, format check, typecheck, test, build, and license
  evidence with the frozen lockfile;
- `git diff --check` and targeted checks proving no temporary diagnostics or
  forbidden Puck/history workaround remain;
- `sudo -n tools/compose/smoke.sh slaif009aa`, including the exact enhanced
  browser selection-release proof and all accepted postchecks;
- every fresh implementation-head GitHub check, with none missing, pending,
  failed, or cancelled before report publication.

Backend Python sources are not in scope. Fresh CI plus the complete accepted
068-f backend/integration evidence may be reused; if any backend, migration,
database, privilege, Compose contract, or Python path changes, stop and run the
complete relevant Python/repository gates and explain why.

## Documentation

Keep `docs/API.md` and `docs/TESTING.md` truthful: moved-component continuity
survives the associated reorder/Undo/Redo chain, but subsequent deliberate
human selection always takes precedence. Do not describe retained selection as
global pinning.

## Security and local authority

Use only the disposable local VM, local containers, test databases, and normal
GitHub workflow. No production credentials, systems, data, release, or merge
authority. Preserve least privilege and all accepted CSP boundaries.

## GitHub workflow

1. Reconcile PR #59 and exact starting report head.
2. Implement only this continuation on `oap/068-puck-editor`.
3. Commit/push implementation plus this exact order and exact active bytes.
4. Wait for and inspect every fresh implementation-head check.
5. Publish one immutable report-only child commit and push it.
6. Do not merge. Signal exact FIFO `OK` only after remote report verification.

## Required report

Publish exactly:

`oap/reports/068-g-release-explicit-puck-selection.md`

The report must state `COMPLETE` or `BLOCKED`, `RESULT=OK` or `RESULT=BLOCKED`,
PR/branch/base, implementation SHA, `Report publication commit: SELF`, exact
parent, files/diff, lifecycle design, explicit-selection evidence, enhanced
browser steps and stable IDs/boundaries, exact backend operation sequence/count,
CSP/security invariants, all commands/results, all fresh implementation-head
checks, intermediate failures, scope/non-goals, and confirmation that no merge
or extra PR occurred.
