# OAP Work Order — 075-d

## Objective and verified state

Amend only PR #71 / `oap/075-editable-domain-substrate`; no new PR/merge.
Required starting report head
`a20fb6e92bab9b60a897494291a3a45a290373f6`, sole parent
`35203a9cf4ddb162218792e486917cf168d254ac`; main/base
`ef456e63abadddfc7d90794c03be3a63677c87f9`; all 20 checks are green.
075-c is immutable and its persistence/validator slice is useful, but strategic
review found its Render-execution claims too broad. Repair only that divergence.

## Exact defects to repair

1. `validate_query_contract()` calls `_walk()` with a tuple of the four specs,
   but `_walk` traverses dict/list only. Depth/clause/executable-fragment checks
   therefore never traverse the top-level query documents. Traverse all
   supported containers and bound total nodes/bytes as well as per-list count.
2. Render manually rejects filter members beyond `status`/`slug` and pagination
   beyond `limit` before invoking the shared validator, even though the shared
   contract allows field clauses, `and`/`or`/`not` and `offset`. Remove
   divergent duplicate policy; one shared validator/canonical form is
   authoritative in Editor and Render.
3. The shared validator permits declared nonlocalized primitive sort fields,
   but Render rejects every sort except `slug`/`id`; Render also ignores
   pagination offset and fetches/truncates before correct filtering/sorting.
   Implement the exact bounded semantics or narrow the persisted contract only
   where Architecture permits. MVP News requires deterministic
   `published_at`-style field sorting, so content-field sort cannot be removed.
4. Render must compare collection-view `definition_version` with the exact
   active content-type definition version before execution, use parameterized
   queries only, enforce canonical/preview status policy, and never return an
   incorrect partial result because an internal prefilter cap was reached.

## Required execution semantics and proof

- Support deterministic status/slug and bounded field clauses for the declared
  primitive operators, one documented recursively bounded logical form,
  projection, content-field/slug sort with direction and stable ID tie-break,
  offset+limit. Validate operator value type against primitive/enum bounds;
  reject SQL/comment/control/executable fragments anywhere in nested data.
- Bound database candidate count/cost explicitly. If the safe cap would make
  results incomplete, fail closed with a stable query-cost error rather than
  silently return the first physical rows. No dynamic SQL identifiers or
  caller SQL snippets.
- Real PostgreSQL/public Editor+Render integration persists a News-like view
  with multiple items whose physical/slug order differs from a datetime or
  integer field; exercise logical filter, ascending/descending field sort,
  offset/limit and exact projection in canonical and workspace modes. Assert
  expected ordered IDs/values and status isolation. Change one spec and prove
  COW/canonical independence and replay.
- Negative matrix: nested over-depth/over-count/over-bytes, executable fragment
  at every container depth, wrong primitive value/operator, localized/reserved/
  unknown sort/filter/projection, stale definition, offset/limit/cost overflow,
  malformed stored JSON and cross-site view/type. Editor rejects before write;
  Render fails closed if malformed data exists; zero audit/idempotency/COW
  residue for rejected writes.
- Unit-test shared validator and actual evaluator/compiler together so removing
  either path fails. Run full Python quality/unit/integration/PG14–18,
  Editor/Render/Puck/Agent regression, Node, one clean relevant Compose and all
  20 current checks. Record exact commands/counts/skips.

## Scope and report

No new entity/domain/API scope, navigation/redirect/locale/proposed-side-effect/
composition/theme/media, Agent REST/MCP, freeze/publication, dependency,
architecture/prior report edit, production/release. Objective 075 remains open
for later bounded substrate slices.

Publish exactly
`oap/reports/075-d-align-query-validation-and-render-execution.md` once as an
immutable report-only child of literal 40-hex implementation SHA. Correct 075-c
overstatements; include exact PR/base/head/commits/files/query semantics/tests/
checks/skips/risks/no extra PR/no merge and SELF. No post-report push.
