# OAP Work Order — 076-a

## Contract and objective

Begin the contractual Agent REST/OpenAPI completion with one bounded slice:
the generalized mutation/policy/OpenAPI foundation and complete content-type/
field semantics. Links: §§15.4, 21.3–21.5, 24.1–24.5, 26–27, 52.5.
Objective 075 is merged as
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`.

## GitHub objective state and verified baseline

- Numeric objective `076`, round `076-a`, mode `CREATE_NEW_PR`; create exactly
  one new PR from remote `main`
  `0e83b26bf9a9f63bff6756d65cbfd527d215ec51`, suggested branch
  `oap/076-agent-model-content-semantics`. No Objective 076 PR exists.
- Agent currently has capability-authenticated list/get/create content types,
  list/create fields, plus five-create idempotency/audit machinery. There is no
  type update/delete, field exact-read/update/delete, typed generalized
  update/delete result, external OpenAPI, or honest Agent route-policy coverage.
- Items/translations/relations/views remain later 076 continuations; do not
  absorb them into this turn.

## Production requirements

- Add typed field-primitive discovery and exact list/get/create/update/delete
  routes for content types and field definitions. Preserve existing compatible
  paths where possible; every route uses stable versioned request/response/error
  models. Field update/delete uses exact type/site relationship and optimistic
  definition/row version; no executable primitive/mapping/code registration.
- Generalize Objective 067's create-only pipeline into one typed semantic
  mutation contract supporting create/update/delete status/body/resource/action
  shapes while preserving capability-derived site/workspace, product shared
  lock, ACTIVE+delegator recheck, server operation UUID, durable idempotency/
  replay mismatch, same-transaction semantic audit and COW-only writes. A
  replay never double-consumes request/mutation/delete quota.
- Enforce immutable capability resource constraints plus request/mutation/
  create/delete quotas at route and transaction boundaries. Correct distinct
  scope requirements (`field-definition:*`, relation/view scopes) and Agent
  route-policy classification/coverage; no SYSTEM_HEALTH exemption.
- Apply Objective 075 field/model/site/definition validators at write time and
  make them reusable by freeze/promotion. Type/field deletion is dependency-
  aware and cannot orphan items, views, relations or translations silently.
- Expose deterministic versioned Agent OpenAPI through the public product path
  and commit/generated drift evidence as repository policy requires. It lists
  real security, idempotency, scope, schema and stable errors; no DB/COW/internal
  credential concepts. Production FastAPI remains no-docs unless the bounded
  schema endpoint is deliberately enabled.

## Acceptance and anti-bypass

A real human-issued L4 capability through public NGINX discovers primitives,
performs type/field CRUD, restarts Agent, reads the same overlay, and proves
canonical/other-workspace/site independence, replay/mismatch, row/definition
versions, request/mutation/delete quota and exact operation/audit action/resource
records. A lower preset is denied. Public OpenAPI exactly matches route/schema/
security/error inventory and fails drift tests.

Negative proof covers missing/wrong scopes (distinct content-model and field-
definition scopes), resource/type limits, delete dependencies/quota, wrong
site/workspace/type/path IDs, invalid primitive/validation/cardinality/target
type, stale versions, active membership/ceiling races, frozen/expired/revoked
state, idempotency mismatch, direct runtime wrapper misuse and zero residue.

No service/ORM/SQL/test helper may perform Agent behavior; neutral canonical
setup and assertion-only owner reads are allowed. Run focused tests, then full
Python quality/unit/integration/PG14–18, public HTTP/OpenAPI, migration/
privilege/route-policy, Node, one clean relevant Compose and every required
check. No items/translations/relations/views, pages/navigation/composition/
design/media/MCP/review, dependency, architecture/prior artifact, production/
release. Objective 076 remains open for bounded continuations.

Create/push one PR, never merge. Publish exactly
`oap/reports/076-a-agent-model-content-semantics.md` once as an immutable final
report-only child with literal 40-hex implementation SHA, SELF, exact PR/base/
head/commits/files/migration/grants/routes/OpenAPI/tests/checks/skips/risks/no
extra PR. No post-report push.
