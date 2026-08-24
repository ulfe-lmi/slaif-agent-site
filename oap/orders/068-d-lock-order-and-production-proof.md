# OAP Work Order — 068-d

## Objective

Continue objective 068 on PR #59. Preserve the now-working, human-approved
Puck 0.20.2 editor-only style CSP exception and visible add/move/save/reload
flow. Correct the HUMAN workspace transaction lock ordering and replace the
remaining overstated or indirect evidence with exact production-login,
production-application, public-HTTP, real-PostgreSQL proof. Do not merge.

## Verified starting state and PR mode

- Numeric objective: `068`; round: `068-d`.
- Mode: `CONTINUE_SAME_PR`; amend only PR #59 on
  `oap/068-puck-editor`. Do not create another PR.
- Begin from the verified remote 068-c report head
  `69df1dbdde2ecbfb0bdf86f753b3dde0b5f566db`; its first parent is the
  reported implementation head
  `04fffbe03dd1cbf6b1a3c43d7dad412f7b0c7008`.
- PR #59 is open, non-draft, mergeable, uniquely targets `main`, and its
  verified remote head is that report commit. Base remains `main` at
  `0969cbd46f5ba07182a2f2e3ea8ea80b2d021750` unless live GitHub differs;
  report any difference before implementation.
- 068-c made genuine progress: exact browser evidence established that Puck
  requires runtime inline style attributes and inline style elements; the
  accepted editor-only style exception works; scripts and public surfaces
  remain strict; visible Puck add/reorder/save/reload succeeds. Do not reopen
  that architecture decision.

## Strategic review findings to correct

The 068-c report cannot yet be accepted as complete for two narrow reasons.

First, `control.slaif_human_editor_workspace_assert` currently validates
mutable workspace/session/site/account/permission state before taking the
shared workspace advisory transaction lock. A mutation that waits behind a
lifecycle or authority change can therefore retain pre-lock validation and
continue after the state changed. COW-context shape and equality may be
validated before locking; every mutable authority and lifecycle fact must be
read under the lock used by mutation and completion.

Second, `test_human_editor_workspace.py` uses fixture logins followed by
`SET ROLE` and mostly calls wrappers/services directly. It does not prove the
fixed production login identities, production application wiring, and public
Editor HTTP chain it claims. Several denial/cleanup cases are conflated or
absent, and the browser proof checks two identical Sections and order keys but
does not identify which stable component ID moved. Correct the proof rather
than broadening the product.

## Required implementation

1. In the HUMAN database assertion path, parse and validate the server-owned
   COW setting UUIDs and require `app.session_id == p_workspace_id` plus a
   non-null operation UUID before the lock. When `p_lock` is true, acquire the
   workspace advisory transaction lock immediately after that immutable
   context validation and before checking any mutable workspace, human
   session, account, site, membership, permission, status, or expiry state.
   Re-read all such state under the acquired lock. Preserve the same shared
   lock key and transaction scope used by mutation/idempotency completion; do
   not introduce a second locking scheme.
2. Add a deterministic two-connection real-PostgreSQL race proof. Connection A
   holds the exact workspace lock and changes one live lifecycle/authority fact
   in the same transaction. Connection B begins an assertion or public
   mutation and demonstrably waits; after A commits, B must re-read the state
   under the lock and fail closed. Prove exact zero content mutation, HUMAN
   audit, idempotency, and pending/completed COW-operation residue from B. Do
   not use timing-only sleeps as the assertion of blocking.
3. Provision and connect through the fixed production login identities
   `slaif_control_login` with membership in `slaif_control` and
   `slaif_editor_login` with membership in `slaif_editor_runtime`. Instantiate
   the production Control and Editor database classes and the production
   Editor application factory with their real pools/settings. Assert
   `session_user`, `current_user`, and exact required membership at runtime.
   Fixture-owner setup is allowed only for fixture provisioning and independent
   after-the-fact observation, never as the request identity.
4. Through public Editor HTTP routes and those production applications, prove
   the supported page and composition mutation chain: page create/read/update
   and delete where the current contract supports them; component add/read,
   props update, move/reorder, and delete. Immediately read after each
   representative write through Editor HTTP in the same HUMAN workspace.
   Prove overlay precedence, canonical fallback, and owner-observed canonical
   rows unchanged until later review/promotion. Keep site, human session,
   permission, workspace, and operation context server-owned.
5. Give each denial an isolated precondition and assertion. In particular:
   reactivate membership before testing revoked session; test absolute session
   expiry independently; test inactive workspace and expired workspace
   independently; test wrong site and wrong human; test missing/revoked
   membership or permission; test a different otherwise-valid workspace; test
   a forged workspace setting; and explicitly attempt COW with the human
   authentication session UUID as `session_id`. Every case must fail without
   cross-site/workspace leakage and with exact zero new content, audit,
   idempotency, or COW-operation residue.
6. Prove idempotency replay returns the identical status/body and creates no
   second mutation, COW operation, or audit row. Prove digest mismatch, forced
   handler rollback, and forced completion/audit failure leave exact unchanged
   content, idempotency, audit, and COW-operation counts. A failed request must
   not strand an `IN_PROGRESS` or equivalent record. Use exact expected counts
   and operation IDs, not aggregate `>=` checks.
7. Add a pure public GET proof outside an active mutation: overlay values win,
   canonical rows remain fallback when no overlay exists, and the GET creates
   no idempotency, audit, or pending/completed COW operation. Prove success,
   handler failure, cancellation, and subsequent pool reuse clear
   `app.session_id` and `app.operation_id`; no request may inherit another
   request's workspace or operation context.
8. Independently assert the exact effective grants/denials. Control may resolve
   HUMAN workspace authority but perform no content DML. Editor may execute
   only the generic Editor semantic API plus the narrow HUMAN assertion,
   idempotency, and audit wrappers required here. It must have no direct
   Control/audit/content base/change-table DML and no reviewer, setup,
   canonical-write, Agent-wrapper, lifecycle-management, or promotion
   authority. Do not broaden roles to make tests pass.

## Exact Puck and CSP acceptance hardening

- Preserve the implemented editor route policy:
  `style-src 'self'`, `style-src-elem 'self' 'unsafe-inline'`, and
  `style-src-attr 'unsafe-inline'`, with strict nonce-bound/self-only script
  policy and no script `unsafe-inline` or `unsafe-eval`.
- Preserve strict public/default, renderer, Agent/API, 404, and unrelated
  admin policy; authenticated editor routing, cookie/CSRF, no-store/noindex,
  normalized catalogue/schema, and trusted renderer boundaries remain intact.
- In the strict Compose Playwright path, capture the first visible-Puck-added
  Section's stable component ID and normalized parent/slot/order/props after
  its first save. Add the second Section through visible Puck UI, move the
  first through visible Puck interaction, save, and prove that same first ID
  moved from order 0 to order 1 while the new second ID is order 0. Prove the
  exact structure remains identical after reload and that the browser observer
  has zero relevant CSP, console, page, request, or server failures.
- The claimed component add and move must not use mutation APIs, direct state
  dispatch, or seeded composition. Site and empty-page setup may continue to
  use supported APIs.
- Make the owner-side Compose postcheck assert the exact expected fresh-run
  HUMAN audit action sequence/count, idempotency count, operation IDs/states,
  and no residue for page create, two component adds, and one move. Replace the
  current `>= 4` aggregate evidence with the exact contract.

## Documentation

Keep the accepted compatibility statement and exact route/directive scope:

> Puck 0.20.2 requires runtime inline styling for parts of its editor UI. The
> authenticated editor therefore receives the minimum required style-policy
> exception, while scripts and the public rendering surface retain stricter CSP
> controls.

Correct any test/role documentation that calls fixture-login `SET ROLE` proof
the fixed production login path. Document the lock-before-mutable-check
invariant and the exact production HTTP/identity evidence. Do not call the CSP
decision temporary.

## Explicit non-goals

- No further inline-style investigation, Puck fork/patch, script CSP
  relaxation, public-renderer relaxation, raw HTML/CSS/JavaScript props,
  executable components, or arbitrary user/Agent code.
- No Agent semantic-read correction planned for objective 069.
- No review snapshot/freeze/accept/discard/promotion/publication, public
  renderer implementation, media upload, browser worker, responsive preview,
  or workspace-management UI.
- No database role broadening, direct canonical writes, schema redesign,
  second workspace model, new authentication system, or unrelated refactor.
- Do not replace targeted evidence with another broad test harness or mock-only
  proof.

## Verification and acceptance gate

Run the focused migration/function and deterministic concurrency tests; fixed
production-login database assertions; production-app public Editor HTTP chain;
exact privileges, isolation, idempotency/audit/COW residue, rollback, cleanup,
overlay/fallback tests; exact Puck/CSP Playwright contract; existing Editor and
Agent regressions; complete backend and Node quality/tests; repository,
packaging, migration, markdown, license, supply-chain, security, and docs
checks; PostgreSQL 14–18 CI; a fresh accepted-name disposable Compose smoke;
and `git diff --check`.

Accept only when the lock race fails closed, the public HTTP requests run as
the fixed production login/role pairs, all cases above have exact assertions,
the same visible Puck component ID is proven moved and retained after reload,
the working CSP boundary is unchanged, and every required remote check is
successful with none missing, failed, cancelled, or pending. Report every
failure, skip, unavailable case, and pending check honestly.

Commit and push only to PR #59's existing branch; never merge. Publish
`oap/reports/068-d-lock-order-and-production-proof.md` as the final report-only
commit with `Report publication commit: SELF`; its first parent must be the
literal reported implementation head. Verify remote PR identity/base/head and
report parent before signaling exact FIFO `OK`. Report the lock chronology and
race evidence; route-to-capability/workspace/service/database trace; effective
login/role/grants; exact public HTTP mutation/read, COW/canonical,
idempotency/audit/isolation/cleanup counts; stable Puck IDs and gestures; final
CSP directives/scope; all local and CI results; limitations; and
`RESULT=OK|PARTIAL|BLOCKED|FAILED`.
