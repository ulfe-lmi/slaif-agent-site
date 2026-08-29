# OAP Work Order — 077-a (inert until activated)

## Contract and objective

Implement the contractual Agent information-architecture surface: pages,
hierarchy/routes, navigation and items, redirects, locale configuration and
dynamic collection detail routing. Links: §§19.2/19.4, 21.7/21.9/21.10,
24.6, 52.5; requires 076.

## Production requirements

- Add missing COW data/service contracts for navigation items, redirects and
  bounded locale state with immutable site associations and cycle/duplicate/
  reserved-route/redirect-loop constraints.
- Add typed Agent page exact-read/update/delete/move/restore; navigation
  container/item CRUD+move; redirect CRUD; locale configuration; collection
  listing/detail route-template semantics required by dynamic News.
- Use the generalized 075 COW/idempotency/audit/policy/quota pipeline and
  server-owned context for every mutation. Route changes may propose redirects
  only when the capability has the redirect scope.
- Extend Render projection/router for validated dynamic detail routes without
  arbitrary query/route execution and with canonical/preview parity.

## Acceptance and anti-bypass

Real capability/public API tests construct and mutate a hierarchy, nav item,
redirect, locale, collection listing and `/news/{slug}` detail projection;
canonical remains unchanged until later promotion. Negative tests cover cycles,
depth, duplicate/reserved/cross-site routes, redirect loops, wrong scopes,
foreign IDs, quotas, replay/mismatch, frozen state and missing item. Renderer
must 404 unknown/unpublished resources and use declared bounded view fields.

No direct SQL/service/fixture call may perform claimed Agent operations. Run
real PostgreSQL, public Render/Agent HTTP, OpenAPI drift, full relevant
Compose/CI. No composition/design/media, MCP, review/promotion or source tools.
Binary done is the complete named public surface and negative evidence. Report
`077-a-agent-site-structure-semantics.md` with SELF; no merge/extra PR.
