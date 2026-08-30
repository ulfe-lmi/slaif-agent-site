# OAP Work Order — 075-b

## Objective and verified state

Amend only PR #71,
<https://github.com/ulfe-lmi/slaif-agent-site/pull/71>, branch
`oap/075-editable-domain-substrate`; no new PR/merge. Required starting report
head `7f2b191e71a75df2f0b32c1d7e1df9860389cbcf`, sole parent full
implementation `4c0b706f0dcfc57b41d539f210a5ea8fffb85f61`; base/main
`ef456e63abadddfc7d90794c03be3a63677c87f9`. 075-a is honestly PARTIAL:
eight full integration tests failed, Python CI failed/pended, no translation or
relation product path was executed, and its report used a short SHA.

## Exact remediation

1. Revert all edits to historical migration
   `014_001_human_rbac.py`. Do not invent `relationship:read`; it is absent from
   the architecture's exact scope catalog. Relation reads use the existing
   `content-item:read` (and appropriate human permission); writes retain
   `relationship:write`. Restore `human_authorization/catalog.py` exactly
   unless a non-architecture change is independently necessary.
2. Update every legitimate migration-head/readiness/fixture expectation to
   `040_001` and repair the semantic-read regression. Full suite must be green;
   do not label failures “legacy” or leave pending checks.
3. Make translation/relation PATCH and DELETE concurrency-safe with required
   optimistic `expected_row_version`/equivalent semantics and stable 409 on
   mismatch, not ambiguous 404. Define whether localized-values PATCH replaces
   the complete locale value map or merges it; implement/document/test one
   deterministic contract and validate the resulting full value set.
4. Validate relation update as strongly as create: same-site source/field/
   target; field belongs to source type; only reference/multi-reference;
   optional allowlisted target types; bounded metadata/position; `reference`
   cardinality exactly one and `multi_reference` count never exceeds configured
   cardinality. Enforce race-safely under transaction/row lock so concurrent
   creates cannot exceed cardinality. FK/unique/check errors map to stable
   validation/conflict envelopes with zero residue, never generic 503.
5. Strengthen field primitive/cardinality configuration used by this slice:
   reference versus multi-reference cardinality and target-type constraints are
   bounded and declarative. Item/translation validation uses exact current
   definition version and rejects unknown/localization-mismatched/executable/
   required/cardinality-invalid values. Preserve future mapping work as later
   scope; do not pretend arbitrary model-change migration is complete.
6. Make 040 downgrade restore the exact pre-040 field-definition and Agent
   function signatures/bodies/owners/grants before removing `site_id`; remove
   only 040 tables/triggers/constraints. Add targeted `040→039→040` proof with
   real field create/list and privilege/readiness/COW checks at both revisions.
7. Export the new typed models intentionally and keep route/service/docs naming
   consistent. No direct base/change-table privilege or Control content DML.

## Required real product evidence

- Add a real PostgreSQL Editor HTTP integration using an authenticated HUMAN
  workspace, human session+CSRF, public route handlers, required
  Idempotency-Key, and actual COW/reviewer roles. Create type/fields/items,
  translations and relations; list/get/update/delete; replay and mismatch;
  preview workspace overlay; prove canonical/other-workspace/other-site
  unchanged; promote one fixture and discard another; assert semantic audit and
  idempotency exactly match operations.
- Negative matrix: nonmember/wrong permission/CSRF, cross-site item/field/
  target/route substitution, wrong source parent, invalid locale/value/target
  type/cardinality/position/metadata, stale row version, duplicate relation,
  delete dependency/FK ordering, cancellation/pool cleanup and direct role/
  function/grant denial. Every rejected case leaves COW/audit/idempotency and
  canonical state unchanged.
- Add focused validator/unit tests plus migration downgrade proof. Run full
  Python quality, all unit/repository, complete integration, PG14–18, Editor/
  Puck/Render/Agent regressions, Node, one clean relevant Compose, Markdown/
  Mermaid/supply-chain and all 20 GitHub checks. Record exact commands/counts/
  skips; no pending/failed/missing check is acceptable.

## Scope and report

Only finish the 075-a translations/relations/core validators slice and its
tests/docs/migration compatibility. No navigation/redirect/locale/query DSL/
proposed-side-effect/composition/theme/media/Agent REST/MCP/freeze/publication,
dependency, architecture/prior artifact, production/release. Objective 075
remains open for later bounded substrate continuations after this slice passes.

Publish exactly `oap/reports/075-b-complete-core-domain-proof.md` as immutable
report-only child of literal 40-hex implementation SHA. Correct 075-a evidence/
SHA/CI claims; include exact PR/base/head/commits/files/migration/grants/API
semantics/tests/checks/skips/risks/no extra PR/no merge and SELF.
