# OAP Work Order — 076-c

## Objective and verified state

Amend only PR #72 / `oap/076-agent-model-content-semantics`; no new PR/merge.
Required starting report head
`57f9052016830ea2fe43929d485167c26544e41b`, sole parent
`9dba1faf4349d3bfb6225ef233a0f65a9432c10e`; base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. 076-b report-head checks
were still pending when it claimed all-green, and its new behavior has no
committed functional/public/OpenAPI test. Finish only the type/field slice.

## Required corrections

1. Enforce exact scopes with no compatibility widening. Field creation requires
   `field-definition:create` only; `content-model:create` alone cannot create a
   field. Retain the exact read/write/delete scopes from Architecture.
2. Enforce immutable resource maxima/allowlists before and inside COW:
   allowed type IDs/keys, maximum visible content types, maximum fields per
   type, and delete policy/count. Malformed constraint shapes fail closed at
   capability issuance or stable 403/422, not permissive ignore. Concurrent
   creates serialize/count safely; direct wrapper calls cannot bypass limits.
3. Extend durable semantic audit/idempotency completion with an allowlisted
   semantic action (`CONTENT_TYPE_CREATED/UPDATED/DELETED`,
   `FIELD_DEFINITION_CREATED/UPDATED/DELETED`) in addition to resource type/ID,
   exact method/status/request digest/operation/capability/site/workspace. Pass
   the action explicitly through generalized executor and DB function. Upgrade/
   downgrade and old audit compatibility are deterministic; Agent cannot
   UPDATE/DELETE audit. Replay emits no second action/quota/operation.
4. Classify the OpenAPI endpoint truthfully: if public, give it an explicit
   public Agent-contract policy rather than Agent-capability authority; if
   capability-protected, authenticate it. Semantic routes declare sas2 bearer
   and exact scopes. Generate one deterministic committed Agent-v1 OpenAPI 3.1
   artifact and serve a deep-copy/byte-equivalent contract without mutating
   FastAPI's cached schema. Add generator/drift policy tests and keep docs UI
   disabled. Include stable error envelopes and Idempotency-Key on mutations.
5. Correct 076-a/b evidence in the new report without editing them: literal
   full SHA, report-head CI timing, absence of prior functional tests, and any
   intentional Markdown hard-break whitespace.

## Required real evidence

- Add real PostgreSQL public Agent HTTP integration: human-issued L4 token;
  field primitive/OpenAPI discovery; type+field create/get/list/update/delete;
  exact row/definition versions; replay/mismatch; restart and overlay read;
  canonical/other-workspace/site unchanged. Use the actual new routes and
  fixed Agent role/functions, not service calls.
- Negative matrix: a capability with only `content-model:create` cannot create
  fields; L1/L3/narrowed type allowlists/max types/max fields/delete-disabled/
  exhausted counters; wrong site/type/field/path; stale versions; invalid
  primitive/cardinality/target/validation; dependency-aware delete with item/
  view/relation; membership/ceiling/revoke/freeze/expiry race; direct wrapper/
  grant abuse. Assert zero COW/audit/idempotency/quota/canonical residue.
- Assert first-call and replay HTTP statuses, response bodies, semantic actions,
  counters and operation set exactly. Public NGINX desktop+phone or a bounded
  external client creates and mutates through edge, reads committed OpenAPI,
  restarts Agent, then revokes/401. Test contract artifact byte/semantic drift,
  route-policy coverage and security metadata.
- Run focused tests then full Python quality/unit/integration/PG14–18, Node,
  clean Compose, repository/Markdown/Mermaid/supply-chain and every required
  check. Wait for report-head checks independently; exact commands/counts/skips.

## Scope and report

No items/translations/relations/views expansion, pages/navigation/composition/
design/media/MCP/review, dependency, architecture/prior report edit,
production/release. Objective 076 remains open for bounded continuations.

Publish exactly `oap/reports/076-c-prove-type-field-openapi-and-audit.md` once
as immutable report-only child of literal 40-hex implementation SHA. Include
exact PR/base/head/commits/files/routes/scopes/resource/audit/OpenAPI/tests/
checks/skips/risks/no extra PR/no merge and SELF. No post-report push.
