# OAP Work Order — 068-f

## Objective

Continue objective 068 on PR #59. Preserve all accepted 068-d/068-e CSP,
database, production-identity, public-HTTP, normalized persistence, stable-ID,
general sibling-action, and exact Compose evidence. Correct one narrow Puck
state defect: after a sibling reorder, keep the moved component selected at
its destination and prove undo/redo plus boundary-state continuity. Do not
merge.

## Verified starting state and finding

- Numeric objective: `068`; round: `068-f`.
- Mode: `CONTINUE_SAME_PR`; amend only PR #59 on
  `oap/068-puck-editor`. Do not create another PR.
- Begin from verified remote 068-e report head
  `149d387319eb395aa83f56bbe6ed66ca5237f4ef`; its only parent is the
  implementation head `ae6505888fae78923164e823c7214f4ae17e62a2` and it
  changes only `oap/reports/068-e-general-puck-reorder-action.md`.
- PR #59 remains open, non-draft, mergeable, and on the expected base/head.
  Base remains `main` at `0969cbd46f5ba07182a2f2e3ea8ea80b2d021750` unless
  live GitHub differs; report any difference before implementation.
- Retain 068-e's reusable selected-component controls, modern
  `overrides.headerActions`/`createUsePuck` integration, exact same-zone
  `reorder` action with `recordHistory: true`, fail-closed derivation, root and
  nested zone coverage, and removal of the hard-coded first-pair control.
- Independent source review confirms a remaining gap. In Puck 0.20.2,
  `reorderAction` delegates to `moveAction`; the moved data changes but
  `state.ui.itemSelector` is not moved. Puck's store then recomputes
  `selectedItem` from that unchanged source index. The current control
  dispatches only `reorder`, so after moving index 0 to 1 it selects the sibling
  now at index 0 rather than retaining the component the human moved. Existing
  E2E stops after the DOM order change and does not expose this.

## Required correction

1. Route each accessible sibling move through public typed Puck actions only:
   dispatch the existing same-zone `reorder` action with history recording,
   then update Puck UI selection to the moved component's destination selector
   (`destinationZone`, `destinationIndex`) using Puck's public `setUi` action.
   The selection-only action must not create a second history entry. Do not
   use direct controlled-data replacement, render-key mutation, DOM state,
   test dispatch, or Editor mutation APIs for reorder/selection.
2. Make the action sequence reusable for both `Move up` and `Move down`, root
   and current normalized nested sibling zones, and any list length. Preserve
   fail-closed behavior for missing/stale selection, unresolved zones,
   boundary actions, and denied drag permission.
3. Preserve the moved component's stable ID, selected state, parent, slot,
   type, props, and zone after move, undo, and redo. Boundary controls must
   track that same selected component: after moving the first of two down,
   `Move up` is enabled and `Move down` disabled; after undo the inverse is
   true; after redo the moved component is again selected at the last boundary.
4. Keep the server-response remount only for adopting normalized server IDs
   after save. Do not remount Puck to implement reorder, selection, undo, or
   redo. Preserve default permissions and ordinary Puck header/save/history
   controls.

## Exact proof

- Extend focused action tests to assert the ordered public dispatch plan:
  one history-recording `reorder` followed by one selection-only `setUi` with
  the exact destination selector; cover up/down, root, nested same-zone,
  first/last boundaries, stale/no selection, and at least three siblings.
- In the strict browser path, keep both visible Puck adds and first-save stable
  ID capture. Select the first component visibly, click general `Move down`,
  prove displayed order changes and the same component remains selected by the
  new boundary state (`Move up` enabled, `Move down` disabled).
- Use Puck's visible Undo control and prove the displayed order and boundary
  state return while the same stable component remains selected; use visible
  Redo and prove the moved order and boundary state return. Do not invoke
  Puck dispatch from Playwright.
- Save only the final redone state, then prove the same normalized IDs,
  parent/slot/type/props/order after public Editor GET and reload.
- Preserve exactly one page create, two component adds, and one component move;
  exactly four successful HUMAN audit, idempotency, and COW operations. Undo/
  redo before save must not create backend operations or residue.
- Preserve zero relevant CSP violations, console warnings/errors, page errors,
  failed requests, and server errors.

## Security, scope, and documentation

- Preserve the accepted editor-only style CSP and strict script/public/API
  policies exactly. No Puck fork/patch, dependency change, raw markup/style/
  script, executable component, authority, role, workspace, or database change.
- Do not revisit the lock/runtime proof or Agent semantic reads.
- Update docs only if needed to state that selection follows the moved
  component and reorder participates in Puck undo/redo history. Do not broaden
  claims beyond tested sibling zones.
- No unrelated UI or page-builder feature, review/promotion/publication,
  renderer, media, browser worker, preview, or workspace-management work.

## Verification and report

Run focused composition/Puck tests; web lint/typecheck/test/build; the strict
real browser add/select/move/undo/redo/save/reload contract; exact Compose
postchecks; relevant Editor regressions; full backend unit/repository and real
PostgreSQL integration suites; repository/packaging/docs/security/
supply-chain checks; PostgreSQL 14–18 CI; a fresh accepted-name disposable
Compose smoke; and `git diff --check`. Report failures, skips, unavailable
evidence, and pending checks honestly.

Accept only when the same moved stable component remains selected through move,
undo, and redo; boundary controls track it; Puck history contains only the
semantic reorder; final normalized persistence and exact four-operation
evidence pass; prior CSP/database guarantees remain unchanged; and every
required remote check is successful with none missing, failed, cancelled, or
pending.

Commit and push only to PR #59's existing branch; never merge. Publish
`oap/reports/068-f-preserve-puck-selection-and-history.md` as the final
report-only commit with `Report publication commit: SELF`; its first parent
must be the literal reported implementation head. Verify remote PR identity,
base/head, report path/parent, and remote blob before signaling exact FIFO
`OK`. Report exact move/setUi payloads and history behavior, visible selection/
boundary/undo/redo trace, stable normalized IDs/order, exact backend operation
counts, unchanged CSP/authority invariants, all local and CI evidence,
limitations, and `RESULT=OK|PARTIAL|BLOCKED|FAILED`.
