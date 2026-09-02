# OAP Work Order — 076-z

## Final Objective 076 closure round

Amend only PR [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72),
branch `oap/076-agent-model-content-semantics`, base `main`; no new PR and no
merge. Required starting report head:
`8475973d3375197709c80f4bbd7b08581203704d`, sole parent
`92fba838f55ca0bbe62397594bbfbd7c11da6681`; remote `main` remains
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. All 20 required checks on the
076-y report head are terminal success; PR is OPEN, MERGEABLE/CLEAN.

This is the last valid letter for numeric Objective 076. Do not create `aa`, a
new PR, or a no-op completion report. Preserve all accepted 076 behavior. Fix
the concrete final defects below, then perform a hostile audit of the complete
Objective 076 contract and PR diff against every activated order 076-a through
076-z, the project constitution, compact architecture, and
`oap/MVP-CONTRACT-AUDIT.md`. Use the remaining turn autonomously to repair any
additional in-objective defect the audit proves. Do not expand into Objective
077 behavior.

## 1. Concurrency-safe type/field dependency guards

Strategic review verified the current unreleased revision-047 wrappers are
incomplete:

- `slaif_agent_content_type_delete` checks only visible content items; it can
  mark a type deleted while fields or collection views survive.
- `slaif_agent_field_definition_delete` checks only nonlocalized item JSON; it
  can delete a localized field used by translations, a reference field used by
  normalized relations, or a field referenced by collection-view filter/sort/
  projection data.
- Several dependent create/update wrappers do not share a lock with field
  deletion, so a check-then-delete race can admit a new dependency after the
  check.

Repair the unreleased migration/function contract (no unnecessary new head):

1. Type DELETE must reject any visible same-site field definition, content
   item, or collection view under the type. Also fail closed on any surviving
   translation/relation reachable through its items. Only a dependency-empty
   type may transition to the established content-type tombstone. Denial occurs
   before quota/idempotency completion/audit/COW residue.
2. Field DELETE must reject exact visible dependencies:
   - nonlocalized `content_item.values` containing its key;
   - localized `content_item_translation.localized_values` containing its key;
   - any `item_relation.field_definition_id` equal to it;
   - any same-type collection view whose recursive filter clause has exact
     `field=<key>`, whose sort field equals the key, or whose projection fields
     array contains the key.
   Use structural JSON predicates, never substring matching. Denial is stable
   `422`/`FIELD_DEPENDENCIES` with zero unintended residue.
3. Serialize dependency creation/update against field/type deletion using one
   deterministic lock/order contract. Item create/update, translation create/
   update, relation create/update, and view create/update must either commit
   before deletion and be observed by its guard, or wait until deletion and
   fail; no dangling/hidden dependency or deadlock. Preserve optimistic row/
   definition locking, quotas, resource/scope checks and cancellation rollback.
4. Add real two-connection races for at least relation-vs-field-delete,
   translation/item-value-vs-field-delete, view-vs-field-delete, and field/
   view/item-vs-type-delete. Exactly one valid outcome wins; the loser is a
   stable dependency/not-found/stale denial and final state is referentially
   coherent. Include direct wrapper and public Agent HTTP controls.
5. Real REST tests independently prove each dependency class blocks field/type
   deletion, exact quota/audit/idempotency/COW zero residue on denial, then
   dependency-order deletion succeeds and canonical/other workspace/site remain
   unchanged. Migration 048→047→048 and fresh upgrade retain the repaired
   definitions, exact owners/grants/checks and data-bearing audit behavior.

## 2. Strengthen public acceptance and OpenAPI evidence

- Replace the public acceptance script’s weak audit assertion (`some action
  LIKE CONTENT_% exists`) with an exact expected multiset for every semantic
  type/field/item/translation/relation/view first mutation it performs. Assert
  exact capability/site/workspace/operation/resource ID+type/request digest/
  action/method/status/quota kind, idempotency completion and corresponding COW
  operation. Replays/mismatches/denials add no second mutation/delete/audit/COW
  residue. Include item-relation and collection-view actions explicitly.
- After public Control revocation, use the revoked capability through public
  NGINX and require stable `401` with no residue. Retain lower-preset, resource,
  quota, wrong-site/path, dependency, publication absence, restart, NGINX
  outage/recovery, canonical/other-workspace/site and tombstone proofs. Frozen,
  expired and delegator-loss fail-closed evidence may remain real PostgreSQL
  integration setup until their human lifecycle surfaces are implemented by
  later objectives; do not claim Objective 082 lifecycle behavior here.
- Mechanically compare the canonical OpenAPI path+method inventory to every
  current Agent route policy and production FastAPI handler in both directions.
  For every operation assert correct bearer security, exact
  `x-slaif-required-scopes`, mutation/idempotency declaration, request-body and
  success/error schemas/statuses. No handler missing from schema and no schema-
  only route. Preserve byte drift, public-NGINX exact bytes, no internal models,
  disabled generic docs and supply-chain exact-path policy.
- Re-run the clean public journey against the exact patched PostgreSQL overlay
  and current committed OpenAPI after dependency repair. It must fail if any
  production route/wrapper/audit/openapi/NGINX/restart behavior is removed.

## 3. Hostile audit of every Objective 076 contract

Read every activated 076 order/report and independently inspect the full PR
diff from base. Build a criterion ledger in the final report, not vague prose.
For each contract family below cite production files, decisive tests and exact
results, or fix the gap before reporting complete:

- field primitive discovery; type/field/item/translation/relation/view exact
  list/get/create/update/delete routes and typed stable errors;
- distinct scopes and lower-preset denial; immutable type ID/key/resource
  limits; max types/fields; delete-enabled/ordinary/max-delete quotas;
- trusted capability/site/workspace/operation context, ACTIVE/delegator/
  revoke/expiry/freeze checks, no raw SQL/DDL/code/primitive registration/
  canonical/publication/user authority;
- shared 075 validators, current definition/row versions, parent version
  increments, stale cleanup, dependency and concurrency safety;
- COW-only writes, canonical/other-workspace/site isolation, true tombstones,
  cancellation and restart persistence;
- one atomic wrapper-owned charge, idempotency first/replay/mismatch, strict
  action/resource/method/status/quota audit identity, append-only privileges,
  legacy separation and migration upgrade/downgrade data safety;
- deterministic canonical OpenAPI, exact route-policy drift and public NGINX
  contract; clean Compose patched PostgreSQL image, zero unexcepted Critical,
  no new exception, PG14–18 and all required checks.

Explicitly reconcile every earlier `PARTIAL`/`BLOCKED`/overclaim and identify
the strongest remaining reason not to merge. Do not credit a narrow test for a
broader criterion. Verify no unrelated dependency/entity/migration/trust/
deployment change, secret, production access, architecture weakening or
release overclaim. Objective 076 covers Agent model/content/view/relation REST
and OpenAPI only; pages/navigation/redirects are 077, composition/design 078,
media 079, MCP 080 and lifecycle later.

## 4. Final verification and termination

Run focused dependency/race/audit/OpenAPI/public tests, complete Agent mutation
and 075 validator/query regressions, then full Python quality/unit/integration/
PG14–18, Node, contract drift, repository/Markdown/Mermaid, migration/
privilege/package, clean Compose/edge/Apache/restart/outage and fresh full
supply-chain. Wait for every required report-head check; none may be pending,
failed, cancelled or missing.

Report `COMPLETE` only if every activated Objective 076 criterion is genuinely
closed and the strongest reason not to merge is none within Objective 076.
`PARTIAL`/`BLOCKED` must name a concrete external/technical or unfixable
contract blocker and attempted evidence. Do not stop because work/tests are
long, context is large, or CI needs an in-scope repair. Do not weaken a test,
guard, scanner, exception, OpenAPI or authority boundary to finish. If a real
unresolved issue remains, preserve PR #72 open for strategic/human escalation;
never invent another ID.

## Scope and immutable report

No Objective 077+ entity/feature, no MCP/review/promotion/source expansion, no
new dependency/image variant/exception, architecture/governance/prior artifact
edit, production or release claim. No production secret/system/data access;
routine setup uses executor sudo.

Commit exact order+`oap/active` unchanged with all final implementation/tests,
push only the existing branch, no extra PR/no merge. Publish exactly
`oap/reports/076-z-final-hostile-objective-audit.md` as the final report-only
child of the literal implementation SHA with `Report publication commit:
SELF`. Include the full criterion ledger; exact files/functions/routes/
artifacts/image hashes; local commands/counts/skips; every current check;
all prior correction/blocker closure; scope/security/no-secret/no-extra-PR/
no-merge confirmations; and an explicit strategic merge recommendation or
precise blocker. No post-report push; signal exact FIFO `OK` and wait.
