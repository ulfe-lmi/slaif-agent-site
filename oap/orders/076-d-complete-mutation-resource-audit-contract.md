# OAP Work Order — 076-d

## Objective and verified state

Amend only PR #72 / `oap/076-agent-model-content-semantics`; no new PR/merge.
Required starting report head
`50c5c22fc708940e9abcda6fcfe6dfd74ed777c5`, sole parent
`0a9fa37ddfaaa4b8853257241be364f92465ff49`; base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. 076-c changed only strict
field-create scope plus four test lines; its claims about resource maxima,
semantic actions, OpenAPI artifact/public proof and all-green report-head CI
are unsupported. Do not edit that report; correct it append-only.

## This round: mutation/resource/audit contract only

1. Add a forward migration/generalized DB completion function and typed Python
   executor contract for exact semantic action, method/status, resource type/ID,
   capability/site/workspace/operation/request digest and quota kind. Allowlist
   the six type/field actions. Persist them durably in idempotency/audit; make
   migration reversible and long-lived roles unable to update/delete audit.
2. First call/replay semantics must be exact: create 201/mutation budget,
   update 200/mutation budget, delete 200 tombstone/delete budget; request budget
   is separately consumed at auth. Replay returns the original status/body/
   operation and consumes no second request? Request counting may count each
   HTTP retry per policy, but mutation/delete/audit/COW count exactly once.
   Mismatch/failure/quota denial rolls back the appropriate reservation/quota.
3. Define and validate immutable type/field resource constraints at capability
   creation/context boundary: bounded `allowed_type_ids`, `allowed_type_keys`,
   `max_content_types`, `max_fields_per_type`, and delete enable/count. Unknown/
   malformed constraint keys/types fail closed rather than being ignored.
   Enforce in Agent handlers and owner-defined COW wrappers under serialized
   count checks so concurrent creates cannot exceed maxima or bypass via direct
   function calls.
4. Complete stable errors: domain/constraint validation 422; policy/resource
   403; hidden/foreign 404; stale/dependency/idempotency conflict 409; quota
   429; infrastructure 503. Dependency-aware type/field delete must not orphan
   items/translations/relations/views and must leave exact pending state.

## Required real tests

- Add a new real PostgreSQL Agent integration that uses human-issued L4 and
  narrowed capabilities on the actual HTTP routes. Exercise type+field create/
  get/list/update/delete, replay/mismatch, stale versions, dependency failure,
  other workspace/site isolation and exact response/audit/idempotency/operation/
  request/mutation/delete counters/actions/status.
- Negative/concurrency matrix: max types/fields and concurrent over-limit
  creates, malformed/unknown constraint, allowlist IDs/keys, delete disabled/
  exhausted, wrong scope/site/path/type/field, invalid primitive/cardinality/
  target validation, membership/ceiling/revoke/freeze/expiry race, direct
  wrapper/grant abuse and cancellation. Every rejection has zero unintended
  COW/audit/idempotency/quota/canonical residue.
- Test migration upgrade/downgrade with existing audit rows and COW, exact
  function definitions/owners/grants, and append-only audit denial.
- Run focused tests then full Python quality/unit/integration/PG14–18, Agent/
  Editor regressions, Node, one clean relevant Compose and all 20 checks. Exact
  commands/counts/skips; wait for report-head CI rather than predict it.

## Scope and report

Preserve existing OpenAPI code but do not claim artifact/public OpenAPI closure
in this round; 076-e owns it. No items/translations/relations/views expansion,
pages/navigation/composition/design/media/MCP/review, dependency, architecture/
prior report edit, production/release. Objective 076 remains open.

Publish exactly
`oap/reports/076-d-complete-mutation-resource-audit-contract.md` once as an
immutable report-only child of literal 40-hex implementation SHA. Correct
076-c scope/evidence/CI claims; include exact PR/base/head/commits/files/
migration/resource/audit/tests/checks/skips/risks/no extra PR/no merge and SELF.
No post-report push.
