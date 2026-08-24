# OAP Work Order — 068-b

## Objective

Correct objective 068 on its existing PR so the human Puck editor uses a real,
server-owned HUMAN workspace and proves add/move/save through the visible Puck
UI under the enforced CSP. Close the exact authority, audit/idempotency, and
evidence gaps identified in strategic review; do not merge.

## GitHub objective state

- Numeric objective: `068`; round: `068-b`.
- Mode: `CONTINUE_SAME_PR`; amend only PR #59 and its existing
  `oap/068-puck-editor` branch. Do not create another PR.
- Base remains `main`; begin from the verified remote 068-a report head
  `f1511075937e66fe2fba9b80947c9027411e63f8`, whose first parent is
  implementation head `8405e4c44c62903a96051b883aef1f06497b39af`.
- PR: `https://github.com/ulfe-lmi/slaif-agent-site/pull/59`.

## Verified strategic findings

The 068-a report is honestly `PARTIAL`; green CI does not close these findings.

1. `control_api/site_authority.py` passes the authenticated human
   `HumanSessionContext.session_id` to
   `EditorDatabase.request_content_service()`, which uses that UUID as
   `asyncpg_cow_session.session_id`. A human authentication session is not a
   `control.workspace` and is not the architecture's COW workspace UUID.
2. The Editor app installs an ordinary app-level `ContentModelService` fallback
   outside request COW context. This is not a fail-closed workspace contract.
3. No 068-a path resolves/reasserts an ACTIVE, unexpired, site-bound HUMAN
   workspace owned by the authenticated human. The 068-a report itself lists
   workspace lifecycle as unimplemented. The resulting ad-hoc COW session has
   no governed review/promotion identity.
4. The wired Editor mutation path does not provide the architecture-required
   durable idempotency and same-transaction HUMAN audit envelope comparable to
   the real Agent mutation path.
5. `tests/e2e/governance.spec.ts` creates and moves components with direct
   `page.request` Editor API calls before Puck is opened. It then saves an
   unchanged tree, so it does not prove add/move via the visible Puck UI.
6. The same test explicitly allowlists `/style-src/`. Puck 0.20.2 emits a real
   inline-style CSP violation, and its installed runtime contains inline style
   properties/style mutations. The test cannot redefine that violation as
   success. Normative architecture requires CSP avoiding unsafe inline.
7. Puck 0.20.2 is currently the latest upstream package version. The dependency
   vulnerability and notice drift were corrected on 068-a; preserve the pinned
   `uuid: 11.1.1` override and green supply-chain state without exceptions.

## Required correction

### 1. Real human workspace authority

- Replace use of the authentication session UUID as COW session ID with an
  actual `control.workspace.id` whose `actor_type` is HUMAN, `site_id` is the
  authorized route site, `created_by` is the authenticated user, and state is
  ACTIVE and unexpired.
- Site/workspace/operation context remains server-owned and fail-closed. Do not
  accept or trust a workspace UUID from a browser header, query, path, body,
  local storage, or Puck data. Do not synthesize an unregistered COW UUID.
- Implement only the smallest Control-owned server-side resolve/create and
  persisted binding needed for the current authenticated human/site Editor
  flow. Reuse the existing workspace model/lifecycle substrate. Do not add the
  human workspace-management UI, freeze, snapshot, review, accept, discard,
  promotion, preview, or publication in this round.
- A valid binding must survive the Puck page's separate GET/POST/PATCH/move/
  DELETE requests and reloads while the human session remains valid. A session
  editing two sites must never reuse one site's workspace for the other.
- Before entering COW and inside each mutation transaction, reassert exact
  human/session/user/site/workspace association, ACTIVE/unexpired state, and
  current human permission. Obtain the architecture's shared workspace lock for
  mutations. Revoked/expired/wrong-site/wrong-user state fails closed.
- Enter `asyncpg_cow_session` with the resolved workspace UUID and a
  server-generated operation UUID. Never use Control credentials for content
  functions, and never give Editor reviewer/setup/canonical authority.
- Remove the app-level ordinary content-service fallback. Editor semantic
  handlers must have a successfully established request-scoped workspace
  service or fail unavailable/denied; an omitted authorization/context step
  must not fall through to canonical reads or writes.

### 2. Atomic Editor mutation envelope

- Every state-changing Editor semantic route exposed by the now-production
  Editor app, including all page/composition operations used by Puck, must use
  durable request idempotency with a bounded `Idempotency-Key`, digest mismatch
  rejection, stable replay, and a server-owned operation UUID. Do not rely only
  on the browser's `pending` flag.
- In the same PostgreSQL transaction as each COW mutation, append a durable
  HUMAN audit record identifying operation, human actor, workspace, site,
  action/resource type and resource ID, digest, and result. Do not log raw
  payloads, cookies, CSRF values, credentials, or secrets.
- Narrow SECURITY DEFINER wrappers may access only the exact Control/audit state
  needed to validate the HUMAN workspace and complete idempotency/audit. Revoke
  PUBLIC; grant only the exact Editor runtime functions. Editor receives no
  direct Control/audit table DML and no generic Agent wrappers.
- Failed validation, permission, wrong-site/workspace, conflict, or audit/
  idempotency completion must roll back both COW change and durable envelope.
- GETs in the same human flow must read the resolved workspace overlay with
  canonical fallback. They must not read canonical-only when the workspace has
  a changed value and must not create audit/idempotency/operation state.

### 3. Real Puck UI and CSP proof

- Remove the CSP console-error allowlist and any comment that treats a blocked
  inline style as acceptable. Do not add `unsafe-inline`, report-only CSP,
  console suppression/monkey-patching, weakened edge headers, or test-only
  bypasses.
- Make the integrated Puck interaction compatible with the normative CSP. A
  reviewed bounded package patch/adaptation is acceptable only if it preserves
  upstream license/provenance, is frozen and documented, removes the violating
  inline-style behavior for the supported editor path, and is covered by
  dependency/build/E2E evidence. Do not silently maintain an unbounded fork.
- If no CSP-compatible Puck 0.20.2 path is technically viable without weakening
  the architecture, stop and report `BLOCKED` with exact source/browser evidence
  and the smallest human risk decision; do not fake completion.
- Rewrite the Playwright 068 path so component add and move occur through visible
  Puck controls/drag/keyboard interactions after the editor opens. API setup may
  create the site/page, but it must not perform the component add or move being
  claimed as Puck evidence.
- Save via the visible editor action, reload, and inspect the public same-origin
  Editor API response to prove persisted IDs, parent, slot, order, type/schema,
  and props. Assert zero unexpected console errors, page errors, failed requests,
  server errors, and CSP violations.

## Required real-PostgreSQL evidence

Use production application factories/wiring and actual local login roles, not
only fakes/unit tests. At minimum prove:

1. authenticated human + authorized site resolves a real ACTIVE HUMAN workspace;
2. Editor content calls use `slaif_editor_login`/`slaif_editor_runtime`, while
   human/site/workspace authority uses only the Control pool;
3. create page/component, update/move/delete as representative operations,
   immediate GET observes overlay state and canonical fallback;
4. owner/public canonical inspection remains unchanged before promotion;
5. durable idempotency replay/mismatch and one same-transaction HUMAN audit row;
6. forced failure rolls back COW, idempotency completion, and audit;
7. wrong site, wrong human, other workspace, inactive/expired workspace, and
   forged workspace context are denied without leakage;
8. human auth session UUID is not used as a COW session and has no orphan COW
   operations;
9. context/pool cleanup prevents workspace/operation bleed into a reused
   connection; and
10. exact PostgreSQL EXECUTE grants and direct table/base/change/reviewer denial
    for Editor and Control identities.

Run focused tests plus full relevant backend unit/integration, Node adapter/UI,
repository/packaging/markdown/license/supply-chain, `git diff --check`, and the
complete disposable Compose smoke/Playwright gate. Preserve PostgreSQL 14–18 CI.

## Explicit non-goals

- No Agent API/read correction from the planned objective 069.
- No new component types, raw HTML/CSS/JS props, responsive preview, renderer,
  media, browser-worker, review snapshot, freeze, promotion, publication, or
  production-readiness claims.
- No broad workspace lifecycle/UI redesign and no capability changes.
- No CSP weakening, dependency-policy exception, hosted/account-bound service,
  or broader database role.

## Acceptance gate

This round is acceptable only if all of the following are true:

- PR #59 remains the unique 068 PR and this is a continuation on its branch.
- Puck add/move/save/reload is proven through the visible UI under the enforced
  CSP with no violation allowlist.
- Every Editor semantic request is bound to the correct real HUMAN workspace;
  overlay reads/writes, canonical fallback, canonical non-mutation, isolation,
  idempotency, audit, transactionality, and pool cleanup are proven with real
  PostgreSQL/runtime identities.
- No client chooses trusted workspace/operation context, no Control content DML
  is introduced, and no Editor canonical/reviewer/setup authority exists.
- Required local and remote checks are successful with none missing, failed,
  cancelled, or pending. Green CI alone remains insufficient.

## Workflow and report

Re-read all activated 068 orders and the 068-a report. Implement only this
continuation, commit/push to the existing branch, and never merge. Publish
`oap/reports/068-b-human-workspace-and-puck-proof.md` as the final report-only
commit with `Report publication commit: SELF`; its first parent must be the
literal implementation head. Report exact PR/base/head, files, migration and
grant deltas, route-to-workspace trace, identity evidence, COW/canonical/audit/
idempotency/isolation proof, Puck/CSP evidence, all test/CI states, limitations,
and `RESULT=OK|PARTIAL|BLOCKED|FAILED`, then signal exact FIFO `OK`.
