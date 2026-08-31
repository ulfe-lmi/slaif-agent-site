# OAP Work Order — 076-t

## Objective and authoritative starting state

Continue numeric Objective `076` by amending only PR
[#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72), branch
`oap/076-agent-model-content-semantics`, base `main`; do not create another PR
and do not merge. The required starting remote report head is
`cbf17fe029a6e81fe1eadb23a00432eb618f2b62`, whose sole parent is the
076-s implementation commit `f27e8336cbd73cc7c13802efed74f0619a7a7b16`.
Remote `main` remains `0e83b26bf9a9f63bff6756d65cbfd527d215ec51`.
At activation, PR #72 is OPEN, MERGEABLE/CLEAN, and all 20 required checks on
the starting report head are successful.

Rounds 076-q through 076-s genuinely close trusted-database resource and
optimistic-version enforcement for all six content-type/field-definition CRUD
mutations. Preserve them. The next dependency-correct production slice is to
make the durable semantic audit identity and delete resource budget truthful,
strict, and inseparable from those operations before extending the same
pipeline to content items, translations, relations, and collection views.

## Verified implementation anchors and defect

- `services/backend/src/slaif_agent_site/db/alembic/versions/041_001_agent_semantic_audit.py`
  is revision `043_001`. It adds only `audit.agent_mutation.action` with
  `LEGACY_MUTATION`; its 11-argument completion function validates only a
  six-action allowlist and generic 2xx status, calls the older completion, then
  updates the audit row. It does not persist or couple HTTP method or quota
  kind and remains callable as a bypass.
- `025_001_agent_mutation_surface.py` owns the original 10-argument completion
  and audit row (`operation_id`, capability/workspace/site, resource,
  request digest, response status). The legacy completion is still needed for
  existing non-generalized item/page/component creates, but it must not be a
  way to complete type/field operations without the strict semantic contract.
- `039_001_complete_session_authority_and_proof.py` owns
  `control.slaif_agent_quota_consume`. Its delete branch enforces
  `delete_quota` but ignores persisted resource constraint `max_deletes`.
- `044_001_agent_resource_constraints.py` is the current migration head and
  exposes the owner-only trusted resource helper returning `max_deletes` along
  with the other validated constraints. Reuse that source of truth; do not
  add a permissive second parser.
- `agent_state/mutations.py::_complete` currently calls the 11-argument
  semantic completion with action only. `execute_agent_mutation` already uses
  one `quota_kind` for reservation and knows status/action/resource.
  `agent_api/agent_http.py::_execute_mutation` already has the real
  `request.method` and passes the quota kind.
- Reuse the real PostgreSQL mutation fixtures in
  `services/backend/tests/integration/test_agent_mutations.py`, including the
  human-issued capability helpers, actual Agent FastAPI handlers, two runtime
  pools/connections, owner assertion reads, COW reviewer operation inspection,
  and migration round-trip pattern.
- A new migration must advance the head from `044_001` to `045_001`; update
  all exact migration-head/history, package-inventory, bootstrap/readiness,
  and integration fixtures in this same round. Do not create a predictable
  follow-up CI repair for stale `044_001` expectations.

## Bounded production requirements

1. Add one forward/reversible `045_001` migration that durably records the
   exact HTTP method and quota kind on `audit.agent_mutation`. Existing rows
   must retain an explicit honest legacy classification (or an equally honest
   nullable/versioned representation); never fabricate historical method or
   quota facts. New semantic rows must be constrained to the supported values.

2. Replace the action-only completion path with one typed strict completion
   contract carrying capability, site, workspace, idempotency key/digest,
   operation, response body/status, resource type/ID, semantic action, HTTP
   method, and quota kind. The database must independently enforce the exact
   six-way mapping:

   - `CONTENT_TYPE_CREATED` / `FIELD_DEFINITION_CREATED`: matching resource,
     `POST`, status `201`, quota kind `mutation`;
   - `CONTENT_TYPE_UPDATED` / `FIELD_DEFINITION_UPDATED`: matching resource,
     `PATCH`, status `200`, quota kind `mutation`;
   - `CONTENT_TYPE_DELETED` / `FIELD_DEFINITION_DELETED`: matching resource,
     `DELETE`, status `200`, quota kind `delete`.

   It must also reject a response body whose action, operation identity, or
   record ID contradicts the supplied completion. Preserve atomic idempotency
   completion plus exactly one audit insert. Replay returns the original
   status/body/operation and creates no second audit/COW operation or
   mutation/delete charge.

3. Remove the action-only completion as an effective runtime bypass. Preserve
   the older completion only where current non-type/field production routes
   still require it, but make it fail closed for `content_type` and
   `field_definition`; those resources must use the strict completion. Apply
   exact runtime/PUBLIC grants and keep direct audit table UPDATE/DELETE (and
   unauthorized SELECT) unavailable to long-lived roles. Do not break the
   current item/page/component create routes that still carry honest legacy
   classification pending their own 076/077/078 generalization.

4. Pass `request.method` and the same `quota_kind` used by
   `execute_agent_mutation` through the typed Python boundary into the strict
   database completion. Centralize/validate the six action contracts rather
   than scattering permissive strings. Preserve cancellation rollback,
   mismatch behavior, error envelopes, action response bodies, COW context,
   server-owned operation IDs, and all 076-q/s resource/version behavior.

5. Enforce immutable resource constraint `max_deletes` transactionally in the
   database quota boundary, in addition to `delete_quota`. The effective
   delete allowance is the tighter applicable bound. `0` denies all deletes;
   missing `max_deletes` preserves the ordinary delete quota. Use the trusted
   validated constraint helper/current COW context and a row-locking/atomic
   counter update so concurrent delete requests cannot exceed the bound.
   Malformed constraints fail closed. A denied, failed, mismatched, replayed,
   cancelled, stale, dependency-blocked, or wrong-authority operation leaves no
   extra delete counter, idempotency completion, audit row, or COW residue.

6. Downgrade must restore the exact pre-045 audit schema, completion signatures,
   function bodies, owners, and grants needed by revision 044. Upgrade after
   downgrade must restore strict enforcement without losing supported legacy
   rows. Keep all SECURITY DEFINER search paths fixed and use no dynamic SQL.

## Required production-facing and PostgreSQL proof

Add focused real-PostgreSQL tests that fail if the production functions or
Agent REST wiring are removed. They must use real human-issued capabilities and
the actual Agent application/HTTP handlers for positive product behavior; no
service/ORM/SQL helper may stand in for the claimed Agent operation. Direct SQL
is allowed only for neutral setup, adversarial runtime-function calls, and
owner assertion reads.

- Execute all six type/field actions and assert, for each first request, the
  exact response/action/status/resource/operation and one durable audit row
  containing exact capability/site/workspace, request digest, resource ID/type,
  action, HTTP method, response status, and quota kind.
- Replay each representative action without a second audit/COW operation or
  mutation/delete charge; changed-body reuse must be 409 with no residue.
- As `slaif_agent_runtime`, prove the legacy and action-only completion paths
  cannot complete type/field work, and prove the strict completion rejects
  every material action/resource/method/status/quota/body mismatch. Prove audit
  append-only privilege denial.
- With `delete_quota` above the resource bound and `max_deletes=1`, race two
  valid deletes of independent resources through two real connections. Exactly
  one succeeds, one receives the stable quota denial, `delete_used` is exactly
  one, and only the winner has idempotency/audit/COW residue. Also prove
  `max_deletes=0`, missing-bound fallback, and replay behavior.
- Exercise 044→045, 045→044→045 with existing legacy and new semantic
  audit rows, exact function definitions/owners/grants, current Alembic head,
  and COW still enabled/hardened.

The focused HTTP test may use the production ASGI application against real
PostgreSQL, as existing mutation integration tests do. The final Objective 076
round will still require the consolidated public-NGINX/restart proof; do not
claim that final edge acceptance here.

## Verification and acceptance

Run focused tests first, then all changed-surface tests and the full current
Python quality/unit/integration/PG14–18, Agent/Editor regressions, migration/
bootstrap/privilege/package contracts, Node contracts, repository/Markdown/
Mermaid/supply-chain gates, and one clean relevant Compose/edge gate. Inspect
and repair in-scope CI failures on this same branch. Report exact commands,
counts, PostgreSQL versions, skips, and every required check state; pending,
skipped, or not run is not pass.

Acceptance for this round requires production code plus committed tests for
all requirements above. Do not return `PARTIAL` merely because the work is
difficult or lengthy. `PARTIAL`/`BLOCKED` is permitted only with a precise
external or technical blocker and evidence of the attempts made. An
unexplained early no-op return is an execution-control failure and must not be
repeated.

## Scope, non-goals, and safety

Do not add content-item/translation/relation/collection-view CRUD in this
round; those are the next 076 production slices. Do not change pages,
navigation, composition, design, media, MCP, browser/review/promotion, public
OpenAPI/NGINX contract, architecture/governance, dependencies, workflows,
production/release claims, or prior immutable orders/reports. Preserve the
recovered 076-l and accepted 076-q/s behavior. No production secret, system,
credential, data, or deployment access. Routine PostgreSQL/Compose/tool setup
belongs to the disposable executor VM and passwordless sudo, not the human.

## GitHub and immutable report contract

Fetch/reconcile GitHub, verify the named open PR/branch/head, amend only that
branch, commit the exact activated order and `oap/active` unchanged with the
implementation, push, and never create/close/merge another PR. After all
non-report work is pushed, publish exactly
`oap/reports/076-t-couple-semantic-audit-and-delete-quota.md` as the final
report-only child. Include literal 40-hex implementation SHA,
`Report publication commit: SELF`, exact migration/schema/functions/grants/
Python changes/tests/checks/skips/risks, no extra PR/no merge, and an explicit
statement that Objective 076 remains open for items/translations/relations/
views and consolidated public OpenAPI proof. Make no post-report mutation or
push; signal exact FIFO `OK` and return to waiting.
