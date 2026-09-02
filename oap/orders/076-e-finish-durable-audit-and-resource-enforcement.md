# OAP Work Order — 076-e

## Objective and verified state

Amend only PR #72 / `oap/076-agent-model-content-semantics`; no new PR/merge.
Required starting report head
`03bd0adf1412b08192b9b1fed388415c7ece4a3e`, sole parent
`d116aba77f745a4dc42f8aba6f9e7da09318d3ee`; base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. 076-d is PARTIAL and
truthfully lists missing durable audit and DB enforcement, but incorrectly says
all 20 implementation checks were complete; current report-head checks are
mostly in progress. Close only these limitations and correct evidence.

## Durable semantic audit

- Add a forward/reversible migration extending `audit.agent_mutation` and the
  idempotency completion function with an allowlisted semantic action and exact
  method/status where not already durable. Existing rows receive an explicit
  legacy classification or nullable-versioned representation without false
  invention. New type/field operations must persist one of the six exact
  actions plus capability/site/workspace/operation/resource/digest/status.
- Pass action/status/quota kind through typed executor into the DB function;
  DB independently rejects action/resource/status mismatches. Agent and all
  long-lived runtime roles cannot UPDATE/DELETE audit. Replay/mismatch/failure
  emits no second audit/action/COW operation and retains original status/body.
- Downgrade restores exact prior signature/schema/owner/grants and preserves or
  deliberately handles existing audit data under documented maintenance rules.

## Race-safe resource constraints and quotas

- Normalize/validate the supported type/field constraint schema once at
  capability issuance/context construction and freeze it recursively; unknown
  keys/types/negative/inconsistent maxima fail closed. No permissive ignored
  shape.
- Enforce allowed IDs/keys, `max_content_types`, `max_fields_per_type`, delete
  enable/count and request/mutation/delete quotas in owner-defined Agent COW
  wrappers/functions under deterministic per-workspace/type locking. Direct
  Agent-runtime wrapper calls and concurrent creates/deletes cannot bypass the
  same constraints. HTTP checks are defense in depth, not authority.
- Count the visible current workspace overlay correctly, not only canonical or
  another session. Failed/mismatched/replayed calls preserve counters; delete
  dependencies and quotas are atomic with the COW operation/audit.

## Required evidence

- New real PostgreSQL concurrency tests race type creates at max-types and field
  creates at max-fields; exactly the allowed number commits and the loser is
  stable 403/429/409 per contract with no residue. Direct wrapper attempts with
  foreign/forbidden type/key and delete-disabled constraints fail.
- Full public Agent integration exercises all six actions and verifies exact
  first/replay status/body/operation, request/mutation/delete counters,
  idempotency record and one durable semantic audit row/action each. Cover
  mismatch, validation, dependency, quota exhaustion, cancellation and rollback.
- Migration upgrade/downgrade/upgrade with existing legacy/new audit rows,
  function definitions/owners/grants and append-only denial. Add route/resource
  unit tests only as supplements.
- Run full post-change Python quality/unit/integration/PG14–18, Node, Agent/
  Editor regression, clean Compose, repository/Markdown/Mermaid/supply-chain
  and every required check. Wait for terminal current-head checks; exact
  commands/counts/skips. No reuse of pre-change suite as final proof.

## Scope and report

Preserve OpenAPI work without claiming final artifact/public-edge closure;
076-f owns it. No items/translations/relations/views, pages/navigation/
composition/design/media/MCP/review, dependency, architecture/prior report
edit, production/release. Objective 076 remains open.

Publish exactly
`oap/reports/076-e-finish-durable-audit-and-resource-enforcement.md` once as an
immutable report-only child of literal 40-hex implementation SHA. Correct 076-d
CI/limitations; include exact PR/base/head/commits/files/migration/functions/
constraints/concurrency/tests/checks/skips/risks/no extra PR/no merge and SELF.
No post-report push.
