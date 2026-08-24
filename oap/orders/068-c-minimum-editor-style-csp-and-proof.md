# OAP Work Order — 068-c

## Objective

Continue objective 068 on PR #59 using the human-approved minimum style-only
CSP compatibility exception for the authenticated Puck editor. Complete the
real visible Puck add/move/save/reload proof and close the remaining HUMAN
workspace authority/evidence gaps. Do not merge.

## GitHub objective state

- Numeric objective: `068`; round: `068-c`.
- Mode: `CONTINUE_SAME_PR`; amend only PR #59 on
  `oap/068-puck-editor`. Do not create another PR.
- Begin from the verified remote 068-b report head
  `82790bd4692c0f2d80c4f70062687ace5900a069`, whose first parent is
  implementation head `a9db9faab5492783059637b940c760d2f116b800`.
- Base remains `main` at `0969cbd46f5ba07182a2f2e3ea8ea80b2d021750` unless
  live GitHub differs; report any difference before implementation.

## Human architecture decision

The human has accepted the smallest style-only CSP relaxation needed by Puck
0.20.2 on the authenticated human-facing Puck editor/admin surface. Preserve
the strictest practical CSP everywhere else.

Determine the minimum working style capability in this order:

1. Prefer `style-src-attr 'unsafe-inline'` only on the authenticated Puck
   editor surface, while keeping ordinary stylesheet elements/loading under
   `style-src-elem 'self'` / the existing self-only policy.
2. Only if browser evidence proves that insufficient because Puck requires
   inline `<style>` elements or equivalent runtime styling, add the minimum
   broader style exception needed, still limited to the authenticated
   editor/admin surface.
3. Do not patch or fork Puck merely to preserve `style-src 'self'` if the
   minimum style-only exception makes the real editor work.

This is an intentional compatibility decision, not a temporary workaround.
It authorizes no script relaxation, public-renderer relaxation, raw HTML,
arbitrary style/executable components, or broader backend authority.

## Required CSP implementation and proof

- Route the stricter public-site/renderer CSP and the authenticated Puck editor
  CSP deliberately. The exception must not spill to public renderer pages,
  public API responses, Agent API, or unrelated unauthenticated surfaces.
- Keep `script-src` strict. Never add `script-src 'unsafe-inline'`,
  `script-src 'unsafe-eval'`, wildcard script sources, report-only CSP, or CSP
  disablement.
- Start with style attributes only. Inspect the enforced response header and
  browser violations, and broaden style policy only if exact browser evidence
  proves Puck also requires style elements. Document the final directive and
  why narrower failed or succeeded.
- Editor authentication, cookie/CSRF controls, no-store/noindex headers, request
  IDs, normalized component catalog, trusted renderer, and server-owned
  workspace context remain unchanged and fail closed.
- Do not allow user/Agent-controlled raw HTML, JavaScript, arbitrary CSS/style
  payloads, executable component registration, or bypass of normalized schema
  validation. Agent-written normalized content must not be able to turn this
  editor-only policy into executable markup.
- Add policy tests that compare at least: authenticated Puck editor page,
  public renderer page, public/Agent API, and an unrelated admin/control page.
  Assert exact style directives, strict script directives, and absence of
  unnecessary relaxation outside the Puck surface.

## Real visible Puck acceptance path

Rewrite the 068 Playwright contract so setup may create the site and empty
page through supported APIs, but the component add and move/reorder claimed by
this objective occur only through visible Puck controls and drag/keyboard
interaction after the editor opens.

The test must prove, in order:

1. authenticated editor route loads and Puck becomes usable;
2. add a supported component through visible Puck UI;
3. add the required container/sibling through visible Puck UI as needed;
4. move or reorder the component through Puck interaction, not `page.request`
   mutation calls or direct application-state dispatch;
5. save through the visible editor action;
6. reload the page;
7. inspect the public same-origin Editor GET response and rendered UI to prove
   stable IDs, component type/schema, parent, slot, order, and normalized props;
8. observe zero relevant CSP violations, unexpected console errors, page
   errors, failed requests, or server errors.

Do not allowlist CSP messages, suppress/monkey-patch console output, seed the
claimed add/move through API calls, or merely save an unchanged tree. Preserve
test artifacts adequate to diagnose the actual gestures and final semantic
structure.

## Remaining HUMAN authority and evidence requirements

Preserve the 068-b real `control.workspace.id` binding, request-scoped Editor
COW service, fail-closed removal of ordinary content fallback, durable
idempotency, and same-transaction HUMAN audit. Correct and prove these exact
remaining boundaries:

1. Pass the route's required permission into the Editor request context and
   recheck it inside every mutation transaction at the database boundary,
   together with exact live human session/user/site/workspace association,
   ACTIVE/unexpired state, and the shared workspace lock. A prior Python
   authorization check alone is insufficient. Preserve platform-administrator
   semantics without silently granting an ordinary member missing permission.
2. Make first-use workspace resolution deterministic under concurrent requests
   so one human/site editing flow cannot split into two active bindings. Reuse
   one valid HUMAN workspace per human/site while active; separate sites never
   share it.
3. Add real PostgreSQL tests using production application factories and actual
   `slaif_control_login`/`slaif_control` plus
   `slaif_editor_login`/`slaif_editor_runtime`, not only fakes or owner calls.
   Prove page/component create, move/update/delete, immediate overlay GET,
   canonical fallback, and owner-visible canonical state unchanged.
4. Prove replay returns the identical status/body without a second COW
   operation or audit row; mismatch and forced completion/audit failure leave
   COW, idempotency, and audit unchanged. Do not rely on aggregate `>=` counts
   alone.
5. Prove wrong site, wrong human, revoked/expired session, inactive/expired
   workspace, revoked permission/membership, forged workspace setting, and a
   different workspace are denied without leakage or residue.
6. Prove authentication session UUID is never the COW workspace ID and has no
   orphan operation; prove success/failure/cancellation/pool reuse clear all COW
   context.
7. Inspect exact grants: Control resolves workspace but performs no content
   DML; Editor can execute only generic Editor semantic functions plus the
   narrow HUMAN assertion/idempotency/audit wrappers, with no direct Control,
   audit, canonical/base/change-table, reviewer, setup, Agent-wrapper, or
   lifecycle authority.
8. Reads in the same HUMAN workspace see overlay precedence and canonical
   fallback and create no idempotency/audit/pending-operation state.

Map expected client-addressable permission/workspace failures to stable,
non-leaking HTTP outcomes; infrastructure and invariant failures remain
sanitized and fail closed.

## Documentation

Document this accepted decision substantially as:

> Puck 0.20.2 requires runtime inline styling for parts of its editor UI. The
> authenticated editor therefore receives the minimum required style-policy
> exception, while scripts and the public rendering surface retain stricter CSP
> controls.

State the exact final directives and route scope. Do not call the accepted
decision a temporary hack. Keep limitations and unfinished later lifecycle,
render, review, promotion, and publication work truthful.

## Explicit non-goals

- No Agent semantic-read correction from planned objective 069.
- No Puck fork/package patch unless exact evidence proves the authorized CSP
  sequence cannot work and another human decision is required.
- No script CSP relaxation, public renderer relaxation, raw HTML/CSS/JS props,
  executable component registration, or arbitrary code.
- No freeze/snapshot/review/accept/discard/promotion/publication, media upload,
  renderer, browser worker, responsive preview, or workspace-management UI.
- No broadened database roles or direct canonical/reviewer/setup authority.

## Verification and acceptance gate

Run and report exact focused CSP/header route tests; Puck adapter/UI tests; the
strict real Playwright add/move/save/reload contract; real PostgreSQL HUMAN
workspace/identity/privilege/COW/idempotency/audit/isolation/cleanup tests;
existing Editor and Agent regressions; backend and Node quality; repository,
packaging, migration, markdown, license, supply-chain, security, and
documentation checks; PostgreSQL 14–18 CI; complete disposable Compose smoke;
and `git diff --check`. Report failures, skips, pending, or unavailable evidence
honestly.

Accept only when the visible Puck gestures pass under the final enforced CSP,
public/script policy remains strict as required, all HUMAN workspace runtime
properties above are proven with real roles/PostgreSQL, and every required
remote check is successful with none missing, failed, cancelled, or pending.

Commit and push only to PR #59's existing branch; never merge. Publish
`oap/reports/068-c-minimum-editor-style-csp-and-proof.md` as the final
report-only commit with `Report publication commit: SELF`; its first parent
must be the literal implementation head. Verify remote PR identity/base/head
and report parent before signaling exact FIFO `OK`. Report the final public vs
editor CSP directives, route scope, Puck gestures, route-to-workspace trace,
effective DB identities/grants, real COW/canonical/idempotency/audit/isolation
evidence, all tests/CI, limitations, and `RESULT=OK|PARTIAL|BLOCKED|FAILED`.
