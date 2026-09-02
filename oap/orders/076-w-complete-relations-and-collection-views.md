# OAP Work Order — 076-w

## Objective and authoritative starting state

Continue Objective `076` by amending only PR
[#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72), branch
`oap/076-agent-model-content-semantics`, base `main`; no new PR and no merge.
Required starting remote report head:
`afe8d7a01621a7fabf4640c539332ecfd7e0d0f6`, whose sole parent is the
accepted 076-v implementation commit
`3833e994255262cd12de281a9fe1dd257662a9b9`. Remote `main` is
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. At activation PR #72 is OPEN,
MERGEABLE/CLEAN and all 20 required report-head checks are successful.

Preserve 076-v’s real item COW deletion, exact database scope checks, parent
definition-version increments, and translation CRUD. The next and final
production-entity slice for Objective 076 is complete normalized item-relation
and collection-view REST semantics. This round also closes two precise review
gaps before final public OpenAPI proof: 076-v did not add its ordered
two-connection translation update race, and stale-definition data is currently
uninspectable/undeletable through translation/item delete paths, preventing the
contractual destructive cleanup workflow.

## Verified substrate and repair anchors

- `content_model/models.py`, `EditableDomainMixin`, and migration 040 provide
  site-confined `item_relation` records plus shared reference/multi-reference,
  target-type, cardinality, metadata, position, row-version, and current-item
  validation used by the Editor. No Agent relation route/wrapper exists.
- `content_model/view_models.py`, `CollectionViewMixin`, migration
  `041_001_collection_query_contract.py`, and the shared query validator provide
  bounded versioned `collection_view` CRUD for the Editor. No Agent view route/
  wrapper exists.
- Agent routes now use exact capability context, COW, internal wrapper-owned
  quotas, strict audit completion and stable errors. Extend that one pipeline;
  do not create a second mutation/idempotency implementation.
- Current migration head is `047_001`; add one reversible successor and update
  every exact graph/package/readiness/privilege fixture in the same round.
- 076-v’s translation test proves sequential stale conflict but not a real
  two-connection same-version race. Add the missing proof; do not edit its
  immutable report.
- Translation list/get/delete and item delete currently require an item’s
  stored definition version to equal the now-current type version. That is
  correct for create/update validation but wrong for inspection and deletion:
  after a field-model change, callers must be able to discover and delete stale
  translations/relations/items/views in dependency order. Deletion must never
  silently rewrite or validate stale payload as current.

## Required stale-data cleanup semantics

- Item and translation create/update remain current-definition-only. Relation
  create/update and view create/update are current-definition-only.
- Read/list/get may return a site/workspace/resource-authorized stale item,
  translation, relation or view together with its persisted version fields;
  it must never reinterpret the old payload under the new definition.
- DELETE of a stale translation, relation, item, or collection view is allowed
  when exact scope/resource/site/workspace/row version/dependency/delete quota
  checks pass. Deletion removes data and does not need a mapping because it
  cannot create invalid surviving content.
- Dependency order is deterministic: relations/translations/views first, then
  items, then fields/types where otherwise allowed. Add one real cleanup proof
  that changes a field definition, discovers stale dependent data, deletes it
  through Agent REST, and reaches an empty deletable type without owner/service
  mutation shortcuts. Canonical and other workspaces/sites stay unchanged.

## Complete normalized relation REST semantics

Add typed exact routes:

```text
GET|POST /api/agent/v1/content-items/{item_id}/relations
GET|PATCH|DELETE /api/agent/v1/content-items/{item_id}/relations/{relation_id}
```

- GET uses `content-item:read`; POST/PATCH/DELETE use
  `relationship:write`. Every mutation requires `Idempotency-Key`; PATCH and
  DELETE require a positive expected row version; DELETE returns the exact
  pre-delete record with status `200` for durable replay.
- Reuse `CreateRelationRequest`, `UpdateRelationRequest`, `RelationRecord` and
  the shared 075 validation law. Add only an Agent delete request model if
  needed. Source, field and target are exact visible same-site rows; the field
  belongs to the source type and is `reference` or `multi_reference`; source
  and target definitions are current for create/update; target type satisfies
  the field allowlist; cardinality, position and metadata bounds are enforced.
- Trusted wrappers enforce exact scope, capability/workspace/site/delegator/
  state, source and target type ID/key resource allowlists, row versions, and
  wrapper-owned quota. Create/update consume `mutation`; delete consumes
  `delete` including `delete_enabled`, `delete_quota`, and `max_deletes`.
- Serialize create/cardinality and update races under deterministic
  workspace/source/field/relation transaction locks. Concurrent single-
  reference or maximum-cardinality creates cannot both pass. Wrong source/
  relation path, cross-site/workspace/target, disallowed source/target type,
  dangling or stale create/update, and direct wrong-scope wrapper use fail with
  zero residue.
- Strict audit mappings are exactly
  `ITEM_RELATION_CREATED|UPDATED|DELETED` ↔ `item_relation` ↔
  `POST/201/mutation`, `PATCH/200/mutation`, `DELETE/200/delete`.
  Legacy completion rejects the resource.

## Complete collection-view REST semantics

Add typed exact routes, preserving the established Editor-compatible shape:

```text
GET|POST /api/agent/v1/collection-views/types/{type_id}
GET|PATCH|DELETE /api/agent/v1/collection-views/{view_id}
```

- Use exact `collection-view:read|create|write|delete` scopes. Every mutation
  requires `Idempotency-Key`; PATCH/DELETE require positive row version;
  DELETE returns the pre-delete record with `200` replay.
- Reuse `CreateCollectionViewRequest`, `UpdateCollectionViewRequest`,
  `CollectionViewRecord`, `CollectionViewMixin`, and the one shared bounded
  query contract. Server resolves the exact ACTIVE same-site type and current
  definition version; a client-supplied version is only an optional optimistic
  precondition, never trusted persistence context. Persist the actual current
  definition version.
- Validate allowlisted filter operators/fields, sort, projection, pagination,
  complexity/depth/size/result bounds, nonlocalized/indexable constraints and
  no raw SQL/executable expression. Update validates the complete resulting
  view, not only changed fragments, and fails if the view’s definition is stale.
- Trusted wrappers enforce exact scope, capability/workspace/site/delegator/
  state, parent type ID/key allowlists, row/definition versions, deterministic
  locks, and wrapper-owned quotas. Create/update consume `mutation`; delete
  consumes `delete` plus deletion constraints. Direct wrapper calls cannot
  bypass them. Reads expose only authorized parent types.
- Strict audit mappings are exactly
  `COLLECTION_VIEW_CREATED|UPDATED|DELETED` ↔ `collection_view` ↔
  `POST/201/mutation`, `PATCH/200/mutation`, `DELETE/200/delete`.
  Legacy completion rejects the resource.

## Tests and acceptance evidence

Positive claims must use real human-issued capabilities and the actual Agent
HTTP application against real PostgreSQL. Direct SQL is limited to neutral
canonical setup, adversarial least-privilege calls and owner/reviewer
assertions; no helper may perform the claimed Agent mutation.

- Relation: create/list/get/update/delete through REST; exact record/version,
  first/replay/mismatch, strict audit/idempotency/quota/COW, canonical/other-
  workspace/site isolation and restart-stable persistence. Negative matrix
  covers scopes, source/path/field/target/site/type allowlists, stale items/
  fields/row versions, primitive/target/cardinality/position/metadata,
  revoke/expiry/freeze/delegator loss, delete limits, cancellation and direct
  wrapper/grant abuse. Two-connection tests prove row update locking and
  reference/cardinality create serialization.
- Collection view: create/list/get/update/delete through REST; exact persisted
  definition/row versions, replay/mismatch/audit/quota/COW/isolation. Negative
  matrix covers scopes/resources/site/path/type/stale row+definition, unknown/
  localized/nonindexable fields, operators/depth/complexity/pagination,
  executable/raw query input, duplicate key, revoke/expiry/freeze/delegator,
  delete limits, cancellation and direct wrapper/grant abuse. Race two PATCHes
  at one row version; exactly one commits.
- Translation correction: race two distinct real connections/Agent app
  instances PATCHing the same translation and expected row version. Exactly one
  returns `200`, one stable `409`, one version increment, one mutation charge,
  one audit/idempotency/COW operation, and no losing residue. Correct 076-v’s
  proof overclaim append-only in the 076-w report.
- Stale cleanup: execute the dependency-order REST deletion described above and
  prove true COW deletes plus canonical/other-workspace independence.
- Migration: exercise 047→048 and 048→047→048 with existing semantic and
  legacy audit/content/COW state; exact functions/checks/owners/grants/head/
  readiness/hardening. Validate PUBLIC and irrelevant roles remain denied.

Run focused tests, complete Agent mutation and 075 query/domain regressions,
then full Python quality/unit/integration/PG14–18, Editor/Render, migration/
bootstrap/privilege/package, Node, repository/Markdown/Mermaid/supply-chain,
and one clean relevant Compose/edge gate. Repair in-scope CI on the same branch.
Report exact commands/counts/versions/skips and every required check; pending,
skipped or not-run is not pass.

## Termination, scope and report

Do not return before both full production entity surfaces, the missing
translation race, stale cleanup repair and focused PostgreSQL tests exist.
`PARTIAL`/`BLOCKED` requires a precise external/technical blocker and attempted
evidence; difficulty or test duration is not a blocker. Another unexplained
no-op result is an execution-control failure.

No page/navigation/redirect/composition/design/media/MCP/browser/review/
promotion, final public OpenAPI/NGINX proof, dependency, architecture/
governance/workflow, prior artifact edit, production or release claim. Preserve
Editor behavior and page/component legacy paths. No production secret/system/
data/credential access; routine tooling belongs to executor sudo.

Commit the exact activated order and `oap/active` unchanged with implementation
on the same branch; push; never create/close/merge another PR. Publish exactly
`oap/reports/076-w-complete-relations-and-collection-views.md` as the final
report-only child of the literal implementation SHA with
`Report publication commit: SELF`. Include exact routes/models/migration/
functions/scopes/grants/audit/quota/tests/checks/skips/risks, append-only
correction of 076-v’s missing race proof, no extra PR/no merge, and state that
only consolidated public OpenAPI/NGINX/restart acceptance plus final hostile
audit remain. No post-report push; signal exact FIFO `OK` and wait.
