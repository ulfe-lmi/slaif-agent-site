# OAP Work Order — 075-c

## Objective and verified state

Amend only PR #71 / `oap/075-editable-domain-substrate`; no new PR/merge.
Required starting head `76ca21f7dade11dad322e3e1202c3fa308d1511d`,
sole parent `ef607ce8c57328a98d7f2c3c9672b37b7861c245`; base/main
`ef456e63abadddfc7d90794c03be3a63677c87f9`; all 20 current checks are
green. The translations/relations slice is accepted. Continue Objective 075
with one bounded collection-view/query-contract slice and append a protocol
correction; do not expand to other remaining entities.

## Mandatory forensic correction

Do not edit any earlier report. Record in the new 075-c report that:

- 075-b was first published at
  `f5b4a096f1b186e0588ee698f2e0718f30cd8b06`, parent implementation
  `acd64245f92a67e0f33b9a5e28068b88afdcc6de`;
- implementation `ef607ce8c57328a98d7f2c3c9672b37b7861c245` was then pushed after
  report publication, and the same report file was rewritten at
  `76ca21f7dade11dad322e3e1202c3fa308d1511d`;
- therefore 075-b was not immutable and its current file is a corrected
  reconstruction, not the original publication artifact. This violates OAP;
  Git history is preserved and future reports must remain append-only.

## Collection/query production requirements

- Complete the existing COW `collection_view` contract with immutable site/type
  confinement, exact type definition version, bounded declarative filter/sort/
  projection/pagination and deterministic validation. No SQL, executable
  expression or arbitrary operator.
- Implement one shared typed query DSL/validator used at Editor write time,
  Render projection, freeze and later promotion/Agent paths. Allowlist logical
  depth/count, field/value operators by primitive, relation traversal depth if
  contractually needed, sortable/filterable/projected fields, locale behavior,
  order determinism, result/page limits and cost bounds. Reject unknown,
  localized misuse, reserved metadata spoofing and stale definition versions.
- Make collection-view create/read/update/delete use exact site/type context,
  required idempotency/audit/COW shared lock, optimistic row version and stable
  404/409/422/503 envelopes. Preserve current IDs/routes where compatible.
- Render executes only validated canonical form, parameterized and bounded;
  canonical and workspace projections remain identical apart from COW context.
  No raw SQL or client-selected columns/order snippets.
- Migration upgrade/downgrade restores the exact pre-slice collection-view
  functions/schema/grants and works with reconciled COW. No historical
  migration edits or new scope; existing `collection-view:read/create/write/
  delete` permissions are authoritative.

## Required evidence and anti-bypass

- Real authenticated Editor HTTP in a HUMAN COW workspace creates type/fields/
  items/view, lists/gets/updates/deletes with replay/mismatch/stale-version,
  renders a collection through real Render in workspace mode, proves canonical
  unchanged, then promotes one fixture and verifies canonical Render. Audit,
  idempotency, operation and site/workspace facts are exact.
- Negative tests cover cross-site type/view/field/item, unknown/executable/raw-
  SQL operator/value, invalid primitive operator, excessive logical/relation
  depth, fields/count/limit/cost, localized/reserved metadata, stale definition/
  row version, nonmember/scope/CSRF, cancellation/pool cleanup and zero residue.
- Test the same shared validator in Editor and Render; deleting/replacing either
  production validation path must fail. Do not seed the claimed view via SQL or
  call internal services for the actor behavior.
- Run focused tests, 040→new-head→040 migration round trip, full Python quality/
  unit/integration/PG14–18, Editor/Render/Puck/Agent regressions, Node, clean
  relevant Compose and all 20 CI checks. Report exact commands/counts/skips.

## Scope and report

No navigation item/redirect/locale/proposed-side-effect/composition/theme/media,
Agent REST/OpenAPI/MCP, freeze/publication, dependency, architecture/prior
artifact, production/release. Objective 075 remains open for later bounded
substrate slices.

Publish exactly
`oap/reports/075-c-collection-query-contract-and-forensic-correction.md` once,
as immutable report-only child of literal 40-hex implementation SHA. Include
forensic facts, exact PR/base/head/commits/files/migration/API/validator/Render/
tests/checks/skips/risks/no extra PR/no merge and SELF; never mutate it later.
