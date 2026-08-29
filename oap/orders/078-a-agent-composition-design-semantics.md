# OAP Work Order — 078-a (inert until activated)

## Contract and objective

Complete external Agent normalized composition and design authority needed by
News, destructive safety and reconstruction. Links: §§21.8–22.7, 24.6,
52.5–52.7; requires 077.

## Production requirements

- Add component exact-read/update/delete/move and bounded structural create;
  validate trusted catalog type/version, parent slots, order/cycles/depth,
  props/variants/responsive tokens and collection/media bindings at write time.
- Add typed design-system, component-catalog and theme-schema discovery plus
  bounded theme, global-region, header/footer read/write operations. Reject raw
  CSS/JS, arbitrary fonts/breakpoints/code/packages/executable props.
- Implement a bounded `site-reset:workspace` only if it is the smallest safe
  way to express the architectural L4 reset; it must call the same semantic
  commands and audit deletions, never raw SQL.
- Extend 076 COW/shared-lock/idempotency/audit/quota/resource/route-policy and
  OpenAPI invariants to every new operation.

## Acceptance and anti-bypass

With a real public capability, create/update/move/delete component trees,
change theme/global design and bind collection/media references; prove exact
preview, canonical independence, replay/restart/audit. Negative tests cover
unknown/executable props, unsafe URL/font/CSS/JS, invalid slots/cycles/depth,
foreign view/media/page, wrong scopes/quotas/site, frozen/revoked state and
crafted Puck-equivalent requests.

No SQL/ORM/service/internal endpoint/test helper may perform Agent behavior.
Run real PostgreSQL and public Agent/preview/Render/OpenAPI, full relevant
Compose/CI. No media byte upload, MCP, freeze/promotion or source tools. Binary
done means complete composition/design semantics. Report
`078-a-agent-composition-design-semantics.md` with SELF; no merge/extra PR.
