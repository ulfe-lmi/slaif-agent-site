# OAP Work Order — 075-a

## Contract and objective

Begin the missing contractual COW editable-domain substrate with one bounded
core-content slice: site-confined translations and normalized relations plus
their shared write/freeze validators. Links: Architecture §§16.2, 16.9,
16.12, 21.2–21.5, 34.6, 42.3. Objective 074 is merged.

## GitHub objective state and verified baseline

- Numeric objective `075`, round `075-a`, mode `CREATE_NEW_PR`; create exactly
  one new PR from remote `main`
  `ef456e63abadddfc7d90794c03be3a63677c87f9`, suggested branch
  `oap/075-editable-domain-substrate`. No Objective 075 PR exists.
- Current COW schema has content types, fields and items but no
  `content_item_translation` or normalized `item_relation`; field definitions
  have no explicit immutable site association. Current item values are bounded
  JSON only and are not validated against proposed field definitions/versions.
- Collection query DSL, navigation items, redirects, locales, proposed side
  effects and broader composition/theme/media validators remain later 075
  continuations; do not absorb them into this turn.

## Production requirements

- Add fixed platform COW tables/models/functions for localized item values and
  normalized item relations. Every row carries immutable `site_id`; composite
  FKs/triggers prevent cross-site type/field/source/target/translation links;
  relevant FKs are promotion-safe/deferrable; ordering/cardinality/version and
  uniqueness are bounded. No per-domain table or Agent DDL.
- Repair `field_definition` site confinement safely in a forward migration,
  including deterministic backfill/fail-closed inconsistency handling and
  composite constraints. Preserve current IDs/API compatibility.
- Implement product-owned validators for field primitive configuration,
  required/localized/cardinality rules, item values against exact proposed
  definition version, locale-tagged translations, and relation target type/
  field/cardinality/site integrity. Reject unknown fields, executable values,
  dangling/cross-site references and stale/incompatible definition versions.
  The same functions/services must be callable by Editor now and reusable by
  later Agent, Render, freeze and promotion code.
- Add Editor API/shared-service exact read/create/update/delete for translations
  and relations plus corrected item validation, using the existing HUMAN
  workspace resolution, shared lock, site policy, durable idempotency and same-
  transaction semantic audit. Do not expose Agent routes yet.

## Acceptance and anti-bypass

Real PostgreSQL and public Editor tests create/update/read/delete translations
and relations in HUMAN COW workspaces and prove exact overlay/canonical/other-
workspace/other-site behavior, Puck/item regressions, idempotent replay/
mismatch, semantic audit, cancellation/pool cleanup, reviewer promotion/discard
compatibility and grants. Negative matrix covers wrong site/type/field/item/
locale/target, stale definition, required/localized/cardinality violations,
unknown/executable/unbounded values, FK/delete ordering and zero residue.
Migration upgrade/downgrade/upgrade and COW hardening/PG14–18 pass. Physical
schema changes are this trusted release only; semantic types remain rows.

No collection-query/nav/redirect/locale/proposed-side-effect/composition/theme/
media expansion, Agent REST, MCP, source, freeze or publication. Do not add a
dependency or hosted service, edit architecture/prior artifacts, access
production or merge. Binary done for this round is the complete core-content
slice above; Objective 075 remains open for deliberately smaller `b..` slices.

Run focused tests first, then full Python quality/unit/integration, migration/
privilege/PG matrix, Node/Editor/Puck/Render regression, clean Compose relevant
path and every required CI check. Create/push one PR, never merge. Publish
exactly `oap/reports/075-a-complete-editable-domain-substrate.md` as the final
report-only child with literal implementation SHA, SELF, exact PR/base/head/
files/migration/grants/commands/results/skips/security/limitations, no extra PR.
