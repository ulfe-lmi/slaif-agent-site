# OAP Work Order — 076-b

## Objective and verified state

Amend only PR #72,
<https://github.com/ulfe-lmi/slaif-agent-site/pull/72>, branch
`oap/076-agent-model-content-semantics`; no new PR/merge. Required starting
report head `3beeafca2a9254c6d68d21ca5528efe970fdacc3`, sole parent full
implementation `2624c362fc091614fe7945bc74d77c8232acb712`; base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. 076-a has no committed
functional tests, uses a short report SHA, claims all checks while current
report-head checks were pending, and fails `git diff --check` on its prose.

## Required authority/policy repair

- Use only exact architecture scopes:
  - field reads: `content-model:read`;
  - field create: `field-definition:create`;
  - field update: `field-definition:write`;
  - field delete: `field-definition:delete`;
  - type update: `content-model:write`; type create/delete keep their exact
    scopes. Remove nonexistent `*:update` and `field-definition:read` names.
- Extend route-policy vocabulary with an explicit Agent-capability authority/
  policy class (not human session/CSRF and not SYSTEM_HEALTH exemption), mark
  every Agent read/mutation route including DELETE and bounded OpenAPI, and call
  `validate_route_policy_coverage` in Agent app construction. CI must fail on a
  missing/stale/duplicate/unclassified Agent route or mutation scope.
- Enforce capability resource constraints for this slice (allowlisted type IDs/
  keys where configured, maximum content types, fields per type, creates/
  deletes) together with immutable request/mutation/delete quotas. Server and
  DB wrappers remain site/workspace bound; policy denial precedes COW residue.

## Generalized mutation correctness

- Generalize the executor/completion boundary for operation kind/action,
  first-response HTTP status, replay status/body, resource identity and quota
  kind. PATCH is 200, create 201, delete has one documented 200 tombstone or
  204 contract; durable idempotency and semantic audit record the exact same
  status/action/resource. DELETE consumes delete budget (and request budget)
  without double-charging mutation/delete on replay; create/update use mutation
  budget. Mismatch/failure rolls back reservation and quota in the same COW
  transaction where applicable.
- Map domain VALIDATION to stable 422, NOT_FOUND non-leaking 404, scope/resource
  403, row/dependency/idempotency conflict 409, quota 429, infrastructure 503.
  Do not collapse asyncpg constraint/validation errors into availability.
- Type/field update/delete enforces exact site/type/path relationships,
  optimistic definition version, Objective-075 validators and dependency
  closure for items/translations/relations/views. Delete cannot orphan data;
  no raw SQL/DDL/component primitive registration.

## OpenAPI contract

- Produce one deterministic versioned Agent-only OpenAPI 3.1 artifact under the
  contract boundary and serve byte/semantic-equivalent JSON through public
  `/api/agent/v1/openapi.json`. Declare the `sas2_` HTTP bearer security scheme
  and per-route requirements, Idempotency-Key, exact scopes/errors/schemas and
  no DB/COW/internal credential concepts. OpenAPI itself may be public but is
  explicitly classified; docs UI remains disabled.
- Do not mutate FastAPI's cached global schema destructively per request. Add
  deterministic generation and drift tests so route/model/policy changes fail
  CI until the artifact is regenerated deliberately.

## Required anti-bypass evidence

- Real public NGINX lifecycle: human creates L4 capability; Agent discovers
  field primitives and OpenAPI; creates/gets/lists/updates/deletes type+fields;
  replays every mutation; restarts Agent and reads the same overlay; canonical/
  other workspace/site unchanged. A lower preset and narrowed resources fail.
- Assert exact response/audit/idempotency/COW operation/action/status/resource
  and request/mutation/delete counters for first call/replay/mismatch/failure.
  Exercise dependency-aware delete with item/view/relation fixtures, stale
  versions, invalid primitive/cardinality/target definition, foreign/path ID,
  membership/ceiling race, revoke/freeze/expiry and direct wrapper/grant misuse.
  Rejected cases leave zero residue.
- Tests must use public Agent routes for actor behavior; fixture SQL is neutral
  setup/assertion only. Add real PostgreSQL integration, route-policy/OpenAPI
  drift/unit, and public desktop/phone/restart proof. Run focused tests then full
  Python quality/unit/integration/PG14–18, Node, clean Compose, repository/
  Markdown/Mermaid/supply-chain and all 20 checks. Exact commands/counts/skips;
  no pending/failure accepted.

## Scope and report

No items/translations/relations/views expansion, pages/navigation/composition/
design/media/MCP/review, dependency, architecture/prior report edit,
production/release. Objective 076 remains open for bounded continuations.

Publish exactly `oap/reports/076-b-make-type-field-surface-real.md` once as an
immutable report-only child of literal 40-hex implementation SHA. Correct 076-a
SHA/CI/evidence claims; include exact PR/base/head/commits/files/routes/scopes/
mutation/OpenAPI/tests/checks/skips/risks/no extra PR/no merge and SELF. No
post-report push.
