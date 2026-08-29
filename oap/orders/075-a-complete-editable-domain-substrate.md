# OAP Work Order — 075-a (inert until activated)

## Contract and objective

Complete the missing contractual COW editable-domain substrate and shared
validators before exposing more Agent authority. Links: Architecture §§16.2,
16.9–16.12, 21, 34, 42.3; requires 074.

## Production requirements

- Add fixed platform COW tables/functions/models for content translations,
  normalized item relations, navigation items, redirects, bounded locale state
  and any minimal proposed-side-effect representation used by the MVP. Preserve
  immutable `site_id`, composite parent/child/reference confinement,
  deferrable-FK promotion safety, row/definition versions and COW hardening.
- Repair existing definitions where necessary, including explicit site
  confinement for fields and cross-entity relationships; no physical table per
  semantic type and no agent DDL.
- Implement product-owned shared validators for field definitions, item values
  and definition versions, translations/relations, bounded query DSL,
  page/route/nav/redirect cycles and uniqueness, component catalog props/slots/
  bindings, theme/responsive tokens and media references. These validators are
  reusable by Editor, Agent, Render, freeze and promotion.
- Complete trusted Editor/shared-service CRUD needed to prove the substrate,
  with human workspace/site policy and same-transaction audit/idempotency.

## Acceptance and anti-bypass

Real PostgreSQL integration creates/updates/deletes every entity in HUMAN COW
workspaces, proves overlay/canonical/other-site isolation, relation/FK/cycle/
version/query/component/theme/media validation, cancellation/pool cleanup,
promotion/discard compatibility and least-privilege grants across PG14–18.
Invalid/cross-site/executable/unbounded data leaves zero COW/audit/idempotency
residue. Physical schema changes are only this trusted Alembic release; a
semantic content type remains data.

No Agent REST expansion, MCP, source, freeze worker or publication in this
objective. Do not add generic entities not required by the contract. Binary
done means later Agent/freeze/promotion layers have one complete validated
editable projection rather than inventing storage during E2E work. Run full
database/migration/privilege/Editor/Render regression and required CI. Report
`075-a-complete-editable-domain-substrate.md` with SELF; no merge/extra PR.
