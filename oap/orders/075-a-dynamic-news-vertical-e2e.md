# OAP Work Order — 075-a

## Objective

Prove the defining MVP vertical: an external agent uses REST API to create
a "News" content type, fields, items, listing/detail pages, navigation link,
and composition nodes entirely as workspace data; human reviews rendered
result; accepts; public site shows News.

## GitHub objective state

- Numeric objective: `075`; round: `075-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR

## Verified current state

- Prior objectives deliver: runtime wiring (065), capability auth (066),
  COW mutations (067), Puck UI (068), media (070), render (071),
  freeze/snapshot (073), accept/promotion (074).
- No single test exercises this full chain through public APIs.

## Required changes

1. Add comprehensive Playwright E2E test `tests/e2e/news-vertical.spec.ts`:
   - setup admin, site, owner user;
   - owner delegates L4 workspace to test agent capability;
   - agent authenticates with real capability token;
   - agent POSTs content-type "news", fields title/body/published_at;
   - agent creates 2 news items;
   - agent creates page `/news`, composition with CollectionList binding;
   - agent creates detail page template with CollectionDetail;
   - agent adds nav link to header navigation;
   - agent requests browser preview screenshot (from 072);
   - human logs into Puck editor, makes small text edit, saves;
   - human freezes workspace (073);
   - human accepts workspace (074);
   - public GET `/news` returns listing with items;
   - public GET `/news/{slug}` returns detail content;
   - canonical tables contain news data; workspace cleaned up.
2. Test asserts NO Alembic migration was generated (schema unchanged).
3. Test runs in CI against real Compose stack.

## Explicit non-goals

- Do NOT add source reconstruction/import.
- Do NOT test responsive sweep (separate).
- Do NOT test destructive isolation (separate).

## Acceptance criteria

- Single E2E proves full agent-create → human-edit → publish → public-visible.
- No schema migrations needed for News creation.
- CI green including this test.

## Report

Publish `oap/reports/075-a-dynamic-news-vertical-e2e.md` with SELF report
commit parenting implementation SHA.
