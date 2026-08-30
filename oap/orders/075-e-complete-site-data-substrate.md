# OAP Work Order — 075-e

## Objective and verified state

Amend only PR #71 / `oap/075-editable-domain-substrate`; no new PR/merge.
Required starting report head
`d84cf7aea64f235fef48b5e81ea7c39cb9bc3f81`, sole parent
`5fa544c9589263a851f36a7af8d41f5942babe3e`; base/main
`ef456e63abadddfc7d90794c03be3a63677c87f9`; all 20 checks are green.
Translations/relations and collection query execution are accepted. Complete
Objective 075 with the remaining fixed site-data substrate only.

## Production requirements

- Add COW-enabled, site-confined fixed platform data for:
  1. locales (bounded canonical tag, enabled/default/order/metadata; one default,
     site default consistency and no deletion while referenced);
  2. navigation items (site/navigation/parent/page association or safe bounded
     internal/external target, localized label data, stable order, depth/cycle/
     slot and cross-site constraints);
  3. redirects (site, normalized source route, safe target, status, locale,
     uniqueness, reserved paths and no direct/indirect loops/chains beyond
     policy);
  4. minimal `proposed_side_effect` workspace data with allowlisted inert kind,
     bounded payload and `PROPOSED` state only. It has no executor/dispatcher
     and can never send email/webhook/DNS/payment or publish in this objective.
- Every entity has immutable site association, UUID/row version/timestamps,
  composite/deferrable parent/reference FKs and deterministic COW promotion/
  discard ordering. No caller-selected schema/SQL/code.
- Implement shared locale/route/navigation/redirect/side-effect validators for
  Editor now and reuse by later Agent/Render/freeze/promotion. Normalize routes
  and locale tags once; reject encoded separators, control/space/backslash,
  unsafe schemes, host confusion, route/nav cycles, duplicate locale/source/
  positions and cross-site parents/pages/navigation.
- Add authenticated Editor exact read/create/update/delete/move APIs for locale,
  navigation item and redirect using existing human workspace, CSRF, named
  architecture permissions, shared lock, idempotency, audit and optimistic row
  versions. Proposed side effects need only a trusted internal service/schema
  contract unless a current product workflow already requires a human route.
- Preserve existing navigation container/page/theme behavior and route IDs.
  No dynamic detail routing or public Agent surface yet; Objective 077 owns it.

## Acceptance and anti-bypass

- Real PostgreSQL/public Editor HTTP in HUMAN COW workspaces: create/update/
  move/list/get/delete locales, nav tree/items and redirects; replay/mismatch/
  stale versions; workspace preview/service projection; canonical and other
  workspace/site unchanged; promote one and discard another; exact audit/
  idempotency/operation state. Seed/propose one inert side effect and prove it
  cannot execute or enter canonical/public behavior without later acceptance/
  dispatcher work.
- Negative matrix: nonmember/scope/CSRF; foreign site/nav/parent/page/locale;
  hierarchy/redirect cycles; reserved/duplicate/encoded/unsafe routes and URLs;
  deleting default/referenced locale or parent; invalid depth/order/metadata/
  kind/payload/state; stale versions; concurrency/cancellation/pool cleanup;
  direct role/grant denial and zero residue.
- Migration new-head→041→new-head works before and after COW reconcile,
  restoring exact 041 functions/schema/grants and privilege/readiness truth.
  Do not edit historical migrations.
- Run focused tests then full Python quality/unit/integration/PG14–18,
  Editor/Puck/Render/Agent regressions, Node, one clean relevant Compose,
  repository/Markdown/Mermaid/supply-chain and all 20 checks. Exact commands,
  counts and skips required; no pending/failure accepted.

## Scope and completion

No Agent REST/OpenAPI/MCP, dynamic detail renderer, composition/global design/
media expansion, side-effect execution, freeze/promotion, dependency, hosted
service, architecture/prior report edit, production/release. This is the final
planned Objective 075 substrate slice; binary objective completion requires all
075-a..e requirements and current green evidence together.

Publish exactly `oap/reports/075-e-complete-site-data-substrate.md` once as an
immutable report-only child of literal 40-hex implementation SHA, with exact
PR/base/head/commits/files/migration/grants/API/validation/tests/checks/skips/
risks/no extra PR/no merge and SELF. No post-report push.
