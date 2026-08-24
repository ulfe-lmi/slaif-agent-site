# OAP Work Order — 068-h

## Objective

Continue objective 068 on PR #59. Preserve the accepted 068-g product
lifecycle correction. Close two narrow evidence gaps before merge: prove that
the other component is selected through a normally actionable human-facing
Puck click rather than Playwright's force bypass, and prove a later reorder
actually rebinds continuity to that newly selected component. This is an
evidence-focused continuation unless normal actionability exposes a real small
UI defect. Do not merge.

## Verified starting state and findings

- Numeric objective: `068`; round: `068-h`.
- Mode: `CONTINUE_SAME_PR`; amend only PR #59 on
  `oap/068-puck-editor`. Do not create another PR.
- Begin from verified remote 068-g report head
  `1e5845fef76635ee9e6b92e14cb7235138409cbe`; its only parent is
  implementation head `a64d173dde17e5b156c6b2ea47ccaf3285796e34` and it
  changes only `oap/reports/068-g-release-explicit-puck-selection.md`.
- PR #59 is open, non-draft, mergeable, and on `main` /
  `oap/068-puck-editor`; reconcile live GitHub before editing.
- 068-g's product logic is accepted: unchanged-data selection of another ID
  releases temporary continuity; data-changing reorder/Undo/Redo transitions
  retain the moved stable ID; each move assigns the currently selected ID.
- Evidence gap 1 is concrete: the strict browser path calls
  `otherPuckOverlay.click({ force: true })`. `force: true` bypasses normal
  actionability checks and therefore does not prove the authenticated human can
  actually click/select that Puck surface.
- Evidence gap 2 is concrete: the browser stops after inverse controls and the
  helper test covers only the release predicate. No test performs a later move
  with the newly selected component, so the report's claim that later moves can
  rebind continuity is source inference rather than observed behavior.

## Bounded scope

Prefer test/evidence changes only. Adjust product UI code only if a normal
stable-ID-backed click exposes a genuine actionability defect, and then make
the smallest supported Puck-compatible correction. Commit this exact order and
exact `oap/active` bytes with the implementation/evidence commit.

## Explicit non-goals

- No redesign of Puck, selection lifecycle, reorder actions, history, editor
  layout, catalogue, APIs, workspaces, publication, or preview.
- No forced/synthetic event, DOM `dispatchEvent`, evaluate-triggered click,
  private store call, private history rewrite, direct `setData`, remount, or
  API-seeded substitute for the required visible gestures.
- No CSP, script policy, authentication, authorization, backend, database,
  migration, role, privilege, COW, audit, idempotency, operation contract,
  dependency, lockfile, deployment, or trust-boundary change.
- No new PR, merge, or next objective activation.

## Requirements

1. Keep the 068-g lifecycle helper and production behavior unchanged unless a
   normally actionable click reveals a real narrowly fixable UI defect.
2. Select the other stable-ID component after the first Move/Undo/Redo chain
   using a normal Playwright click on a visible, attached, enabled, stable-ID-
   correlated Puck/user-facing element. Do not use `force: true` or another
   actionability bypass.
3. Prove after effects settle that the other component remains selected and
   has first-boundary controls (`Move up` disabled, `Move down` enabled).
4. While that other component is selected, invoke visible `Move down`. Prove
   displayed stable-ID order changes and the same newly moved component now
   has last-boundary controls. This is the observed rebind proof.
5. Wait for Puck 0.20.2's documented history entry, invoke visible Undo, and
   prove the final redone order is restored while the same second component
   remains selected at its restored first boundary. Do not invoke a backend
   save during these extra gestures.
6. Save only after that Undo, so persisted final order remains the accepted
   first-chain redone order. Retain exactly one page create, two component adds,
   one persisted component move, exact four HUMAN audit/idempotency/COW
   operations, and no extra operation from either Undo or the second move/Undo.
7. Preserve stable IDs, normalized semantics, all CSP/security observers,
   root/nested/general action tests, and no private Puck workaround.

## Observable acceptance criteria

- The strict real public-NGINX/Puck browser test contains no actionability
  bypass for the explicit second-component selection.
- The second component is selected by stable ID through a normal actionable
  click and remains selected after effects settle.
- The same second component visibly moves down, retains selection at the last
  boundary, then visible Undo restores it to the first boundary and restores
  the prior final order.
- The final save/reload retains the original accepted moved order and stable
  normalized IDs/semantics.
- Compose output retains exact operation sequence
  `page-create,component-add,component-add,component-move`, count 4, and zero
  extra audit/idempotency/COW residue from client-only gestures.
- Zero relevant CSP, console, page, request, network, or server failures.
- Diff confirms no backend/security/dependency/trust change and no temporary
  diagnostic remains.

## Verification

Run and report exact results for:

- focused composition-schema and web tests, lint, typecheck, and build;
- the enhanced strict browser test through
  `sudo -n tools/compose/smoke.sh slaif009aa`, including every stable-ID order
  and boundary assertion plus exact operation/CSP/postcheck output;
- frozen repository Node format/typecheck/test/build/license and relevant
  repository/doc/packaging gates; `git diff --check`;
- a targeted source assertion/search showing no `force: true` or equivalent
  bypass exists in the required explicit-selection/rebind path;
- every fresh implementation-head GitHub check, none missing, pending, failed,
  or cancelled before report publication.

Reuse accepted 068-f/068-g backend evidence because no backend/Python path is
in scope. If any backend, migration, database, privilege, Compose contract, or
Python path changes, stop and run the complete relevant Python/repository gates
and explain the expansion.

## Documentation

No documentation change is required if existing statements become fully
proved. If wording changes, keep it narrowly truthful about actionable human
selection and observed later-move rebinding.

## Security and local authority

Use only the disposable local VM, local containers/test databases, and normal
GitHub workflow. No production credentials, systems, data, release, or merge
authority. Preserve every accepted CSP and least-privilege boundary.

## GitHub workflow

1. Reconcile PR #59 and exact starting report head.
2. Implement only this same-PR evidence continuation.
3. Commit/push evidence/any necessary narrow fix plus this exact order and
   exact active bytes.
4. Wait for every fresh implementation-head check to succeed.
5. Publish one immutable report-only child commit and push it.
6. Do not merge. Signal exact FIFO `OK` only after remote report verification.

## Required report

Publish exactly:

`oap/reports/068-h-actionable-selection-and-rebind-proof.md`

The report must state `COMPLETE` or `BLOCKED`, `RESULT=OK` or `RESULT=BLOCKED`,
PR/branch/base, implementation SHA, `Report publication commit: SELF`, exact
parent, files/diff, whether product code changed, the normal actionable locator
and why it represents a human-facing Puck element, first chain and second
move/Undo stable-ID orders/boundaries, final persistence, exact four-operation
evidence, CSP/security invariants, commands/results, every fresh check,
intermediate failures, scope/non-goals, and confirmation of no merge/extra PR.
