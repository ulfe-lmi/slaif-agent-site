# OAP Work Order — 068-e

## Objective

Continue objective 068 on PR #59. Retain the accepted 068-d lock ordering,
production-login/public-HTTP evidence, exact COW/audit/idempotency proof,
server-refresh stable-ID fix, visible Puck adds, and editor-only CSP policy.
Replace the test-specific hard-coded reorder control with a reusable,
accessible Puck-native sibling reorder interaction and prove it through the
same strict browser path. Do not merge.

## Verified starting state and disposition of 068-d

- Numeric objective: `068`; round: `068-e`.
- Mode: `CONTINUE_SAME_PR`; amend only PR #59 on
  `oap/068-puck-editor`. Do not create another PR.
- Begin from verified remote 068-d report head
  `d8c11fe7ca7e196e818c01d4df9f45694201232a`; its only parent is the
  implementation head `a54e3832e53d95908f04c028c0884ba59aee3c45` and it
  changes only `oap/reports/068-d-lock-order-and-production-proof.md`.
- PR #59 remains open, non-draft, mergeable, on the expected base/head. Base
  remains `main` at `0969cbd46f5ba07182a2f2e3ea8ea80b2d021750` unless live
  GitHub differs; report any difference before implementation.
- Strategically accepted from 068-d: lock-before-mutable-check chronology;
  deterministic advisory-lock race; isolated authority/lifecycle denials;
  fixed production Control/Editor login and public HTTP chain; exact overlay,
  canonical, residue, privilege, and Compose evidence; Puck remount from
  normalized server state; stable-ID assertions; and the approved CSP scope.
  Do not reopen or redesign those areas.
- 068-d is not accepted as complete because `moveFirstRootComponent`,
  `data-testid="puck-action:move-first-down"`, and deprecated
  `renderHeaderActions` implement a test-shaped operation that can only swap
  the first two root entries. Its click handler rewrites controlled data and
  remounts Puck instead of using Puck's reorder action/history path. Green
  browser and CI evidence does not make that a general editor capability.

## Required Puck correction

1. Remove the hard-coded `moveFirstRootComponent` helper, the
   `puck-action:move-first-down` control/test coupling, and direct
   `setData`/render-key mutation used specifically to reorder. Keep the
   server-response remount behavior only where needed to adopt normalized
   server IDs after a save.
2. Implement reusable accessible `Move up` and `Move down` sibling controls for
   the component currently selected through Puck. Use Puck 0.20.2's supported
   public integration surface: prefer native pointer/keyboard DnD if it is
   reliable; otherwise use the modern Puck override/plugin plus `usePuck`
   action path and dispatch Puck's `reorder` action with the selected item
   selector, exact zone, source index, destination index, and history
   recording. Do not use deprecated `renderHeaderActions`, direct controlled
   data replacement, test-only DOM hooks, test-side dispatch, or Editor
   mutation APIs for the claimed reorder.
3. The controls must be product-general, not tailored to the E2E fixture. They
   must operate on any selected component within its current sibling zone,
   support more than two siblings, preserve component IDs/props/parent/slot,
   disable `Move up` at the first boundary and `Move down` at the last boundary,
   and fail closed when no component is selected or its zone cannot be
   resolved. Support root and normalized nested slot sibling zones wherever
   the existing Puck data mapping exposes those zones; do not invent a second
   composition model.
4. Preserve Puck's ordinary header actions, publish/save control, undo/redo
   history, selection, permissions, and accessible names. Do not set every
   Puck permission to `true` merely to make the test pass; omit redundant
   overrides or set only a capability proven necessary. No deprecated Puck
   warning or other unexpected console output may remain.
5. Keep the normalized catalogue/schema and trusted renderer as the only
   component boundary. Puck metadata, selectors, actions, and internal IDs
   must not leak into normalized props or enable raw HTML, CSS, JavaScript, or
   executable components.

## Exact browser and unit proof

- Keep site and empty-page setup through supported APIs, but add both Sections
  through the visible Puck drawer.
- After the first visible add/save, capture its normalized stable ID at root
  order 0. Add the second Section visibly, select the first component through
  the rendered Puck UI, invoke the visible general `Move down` control, and
  prove Puck's displayed order changes before save. Do not select a hidden
  test hook or call dispatch from Playwright.
- Save visibly, GET through the public same-origin Editor API, and prove the
  same first ID is now order 1, the second ID is order 0, and IDs, parent,
  slot, type, props, and ordering remain identical after reload.
- Preserve the exact fresh-run operation evidence: one page create, two
  component adds, and one component move; exactly four successful HUMAN audit,
  idempotency, and COW operations; no extra/no-op move, replay, pending state,
  or residue.
- Add focused unit/component coverage for selection and action derivation:
  no selection, first/last boundaries, middle item among at least three
  siblings, exact same-zone Puck reorder payload/history, and a nested sibling
  zone if represented by the current adapter. The tests must fail against the
  removed hard-coded first-pair implementation.
- The strict observer must see zero relevant CSP violations, console warnings
  or errors, page errors, failed requests, or server errors.

## Security and compatibility invariants

- Preserve editor CSP exactly as accepted:
  `style-src 'self'`, `style-src-elem 'self' 'unsafe-inline'`, and
  `style-src-attr 'unsafe-inline'`; scripts remain nonce-bound/self-only with
  no `unsafe-inline` or `unsafe-eval`.
- Preserve strict public renderer/default/API/Agent/404/unrelated-admin CSP,
  editor authentication, cookie/CSRF, no-store/noindex, server-owned HUMAN
  workspace, idempotency, audit, database roles, and canonical isolation.
- No further Puck CSP investigation or package fork/patch is required. No
  dependency change is expected.

## Documentation

Describe the actual general interaction: a selected Puck component can be
reordered among siblings through accessible Puck controls backed by Puck's
reorder/history action. Do not claim native drag if the accepted interaction
is the accessible action. Remove wording that implies only the first root pair
can be moved. Keep the accepted Puck 0.20.2 CSP compatibility decision intact.

## Explicit non-goals

- No Agent semantic-read correction planned for objective 069.
- No further lock/database identity/evidence redesign unless a regression from
  this exact UI change is found.
- No Puck fork/patch, script CSP relaxation, public CSP relaxation, raw markup,
  arbitrary styles/scripts, executable components, or direct API-seeded move.
- No general page-builder feature expansion beyond reusable sibling reorder;
  no review/promotion/publication, renderer, media, browser worker, responsive
  preview, or workspace-management UI.

## Verification and report

Run focused Puck adapter/action tests, TypeScript/lint/format/build/test, the
strict real Playwright add/select/reorder/save/reload contract, exact Compose
postchecks, relevant Editor regressions, full backend unit/repository and real
PostgreSQL integration suites, repository/packaging/docs/security/supply-chain
checks, PostgreSQL 14–18 CI, a fresh accepted-name disposable Compose smoke,
and `git diff --check`. Report every failure, skip, unavailable case, and
pending check honestly.

Accept only when no test-specific reorder implementation remains, the visible
general control routes through Puck's own reorder/history action, stable IDs
and exact operation counts pass after reload, accepted CSP/database behavior
is unchanged, and every required remote check is successful with none missing,
failed, cancelled, or pending.

Commit and push only to PR #59's existing branch; never merge. Publish
`oap/reports/068-e-general-puck-reorder-action.md` as the final report-only
commit with `Report publication commit: SELF`; its first parent must be the
literal reported implementation head. Verify remote PR identity/base/head and
report parent before signaling exact FIFO `OK`. Report the Puck selection and
action trace, exact dispatch payload/history and boundaries, visible gestures,
stable normalized IDs/order, exact mutation/audit/idempotency/COW counts, CSP
and authority invariants, all local and CI evidence, limitations, and
`RESULT=OK|PARTIAL|BLOCKED|FAILED`.
