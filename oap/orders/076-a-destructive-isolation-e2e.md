# OAP Work Order — 076-a

## Objective

Prove that a Level-4 agent deleting ALL editable workspace data (models,
items, pages, compositions, navigation, redirects, theme, media references)
leaves canonical site, users, and other sites completely unchanged; then
discard restores clean state.

## GitHub objective state

- Numeric objective: `076`; round: `076-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR

## Verified current state

- Architecture §18 mandates destructive demonstration test.
- No such test exists.
- Depends on working COW mutations (067) and accept/discard (074).

## Required changes

1. Add E2E/integration test `tests/integration/destructive_isolation.spec.ts`:
   - seed canonical site with content across multiple types/pages/nav/media;
   - create second site to verify cross-site isolation;
   - create L4 workspace;
   - agent deletes every editable entity within its site/workspace;
   - verify workspace reads return empty/deleted state;
   - verify canonical site unchanged (all content intact);
   - verify other site unchanged;
   - verify users/memberships unchanged;
   - discard workspace;
   - verify canonical still unchanged; workspace terminal.
2. Also verify attempted deletion of protected entities (users, roles,
   another site's content) returns proper authorization errors.
3. Assert no physical table dropped/altered (Alembic revision unchanged).

## Explicit non-goals

- Do NOT test partial/selective acceptance.
- Do NOT implement soft-delete policy changes.
- Do NOT test concurrent conflicting promotions (separate).

## Acceptance criteria

- Full workspace deletion provably contained.
- Cross-site isolation holds under aggressive deletion.
- Discard restores clean state.
- Alembic schema unchanged.
- CI green.

## Report

Publish `oap/reports/076-a-destructive-isolation-e2e.md` with SELF report
commit parenting implementation SHA.
