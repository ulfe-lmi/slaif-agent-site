# OAP Work Order — 068-a

## Objective

Integrate the Puck editor UI into the Next.js admin so a human can open a
page composition, edit it visually with Puck, save through the normalized
composition API, and verify round-trip fidelity.

## GitHub objective state

- Numeric objective: `068`; round: `068-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR
- Base: current main (after prior merge)

## Verified current state

- `packages/composition-schema/src/puck-adapter.ts` contains type conversion
  only; no Puck npm dependency exists in `apps/web`.
- No editor page/route renders Puck.
- Composition CRUD routes exist but require runtime service wiring from 065-a.

## Required changes

1. Add `@measured/puck` (verify latest version) to `apps/web`
   dependencies with locked version in `pnpm-lock.yaml`.
2. Create an admin route `/admin/sites/[siteId]/pages/[pageId]/edit` that:
   - fetches normalized composition via Editor API,
   - converts to Puck format using the adapter,
   - renders Puck editor with trusted catalog components,
   - on save converts back and PATCHes composition API.
3. Verify round-trip: normalized → Puck → normalized produces identical
   semantic tree (IDs, types, slots, order, props).
4. Add Playwright test: login, open page editor, add component, move it,
   save, reload, verify persisted structure.
5. Server must remain authoritative: crafted client payloads violating schema
   are rejected (existing policy tests still pass).

## Explicit non-goals

- Do NOT implement agent-side composition changes (separate).
- Do NOT add new component types to the trusted catalog.
- Do NOT implement responsive preview inside the editor.
- Do NOT change composition storage schema.

## Acceptance criteria

- Puck dependency installed and locked.
- Admin page loads Puck editor for an existing page composition.
- Save persists normalized composition; reload shows same structure.
- Round-trip identity test passes.
- Playwright E2E passes in CI.
- No raw HTML/CSS/JS props accepted beyond existing schema limits.

## Report

Publish `oap/reports/068-a-puck-editor-ui.md` with SELF report commit
parenting implementation SHA.

## Activation addendum — authoritative constraints

This inert preplanned order is amended before activation. These constraints
are part of 068-a and resolve the underspecified UI, authority, and round-trip
requirements above.

### Repository, live state, and authority

- Repository: `/home/ubuntu/codex-work/slaif-agent-site`.
- At activation, remote `main` is expected to be the verified 067 merge
  `0969cbd46f5ba07182a2f2e3ea8ea80b2d021750`; fetch and report any live
  difference. No 068 objective PR exists; create exactly one fresh PR.
- Obey repository `AGENTS.md`, `OAP-COMMUNICATION-coding-agent.md`, and the
  compact normative `ARCHITECTURE-for-agents.md`. Strategic owns acceptance and
  merge; the coding agent implements and reports, and never merges.
- Human Puck editing is a site-authorized, session-authenticated Editor API
  workflow. The browser must use same-origin session cookies and the existing
  CSRF channel for every state-changing Editor request. Do not introduce a
  capability token, client-selected authority, alternate auth store, CORS
  exception, or direct database access.

### Exact bounded objective

Add a human admin route
`/admin/sites/[siteId]/pages/[pageId]/edit` that loads the existing page
composition through the Editor API, renders it through Puck using only the
trusted component catalog, and persists edits back through the existing
normalized composition endpoints. The route is a UI/editor integration only:
do not add Agent API mutations, workspace lifecycle, publication, preview
authority, responsive preview, new catalog types, or composition storage
schema.

### Required implementation behavior

1. Add `@measured/puck` at a specifically verified, compatible, permissively
   licensed version. Record it in `apps/web/package.json` and the frozen
   `pnpm-lock.yaml`; verify package provenance/license and do not add a hosted,
   account-bound, telemetry-required, or incompatible dependency silently.
2. Extend `packages/composition-schema/src/puck-adapter.ts` only as needed to
   make the normalized composition the authority. A normalized node's `id`,
   `componentType`, `schemaVersion`, `parentId`, `slotKey`, `orderKey`, and
   props must survive normalized → Puck → normalized conversion exactly.
   Adapter bookkeeping such as node IDs must never leak into persisted props;
   unknown/untrusted component types and forbidden props must fail closed.
3. Bind the editor page to the `siteId` and `pageId` route parameters and fetch
   composition from the existing Editor API path
   `/api/editor/v1/sites/{site_id}/pages/{page_id}/composition/`. Enforce
   server-provided response validation, no-store behavior, loading/error/save
   states, and an accessible admin shell consistent with existing UI patterns.
4. Configure Puck from the existing trusted catalog/renderer definitions only.
   Every rendered editor component must remain within the catalog and existing
   schema limits; do not accept raw HTML/CSS/JS, arbitrary React components,
   executable props, or client-provided component definitions. Keep the
   existing trusted renderer as the semantic rendering authority.
5. Save through existing Editor API operations and the existing CSRF/session
   authority. Reconcile add/update/move/delete changes deterministically,
   preserving IDs, parent relationships, slots, order keys, and props. Do not
   pretend a local Puck state change is persisted until the server succeeds;
   surface conflict, validation, permission, authentication, and unavailable
   errors without claiming success. Avoid duplicate writes on double-submit and
   refresh authoritative composition after a successful save.
6. Add focused adapter tests proving exact tree/metadata/props round-trip,
   stable ordering, nested parent/slot preservation, unknown-type rejection,
   and no ID/metadata leakage. Add UI/API tests for loading, save success,
   server rejection, and duplicate-submit protection.
7. Add a real Playwright E2E path through the existing setup/login and edge
   stack: open an authorized existing page editor, add a catalog component,
   move it to a different valid slot/order, save, reload, and verify the
   persisted normalized structure (including IDs, parents, slots, order, and
   props). The test must assert no unexpected console/network/server errors and
   must exercise the real same-origin Editor API/CSRF path.
8. Update truthful API/UI/architecture-facing docs and route-policy/contract
   fixtures where required. Do not claim Agent writes, responsive preview,
   publication, promotion, or production readiness.

### Acceptance and security gate

- Exactly one new 068 PR exists and it is based on current remote `main`.
- The admin route loads a real existing composition and renders only trusted
  catalog components.
- Round-trip tests prove semantic identity for IDs, types, schema, hierarchy,
  slots, order, and props; persisted reload proves the same through the edge.
- All saves use the existing human session/CSRF and Editor API permissions;
  crafted payloads, unknown component types, forbidden props, wrong-site/page
  resources, and unauthenticated/insufficient-authority actions are rejected
  by server policy. No public or Agent authority is expanded.
- Required checks, focused tests, full relevant backend/Node tests, contract
  and documentation checks, `git diff --check`, and the repository's complete
  disposable smoke/E2E gate are reported exactly. Green CI is necessary but
  strategic diff/security/scope review remains required.

### Workflow and report contract

Fetch current remote main, create one fresh 068-a branch/PR, implement only
this order, push, and never merge. Commit the activated order and exact
`oap/active` bytes without editing strategic content. Publish the immutable
report as the final report-only commit; verify its remote head is the report
commit and its first parent is the literal implementation head before signaling
the response FIFO. Report PR/base/head, files, behavior, exact test statuses,
dependency/license provenance, authority/security boundaries, limitations, and
`RESULT=OK|PARTIAL|BLOCKED|FAILED`.
