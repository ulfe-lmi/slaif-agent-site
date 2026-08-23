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
