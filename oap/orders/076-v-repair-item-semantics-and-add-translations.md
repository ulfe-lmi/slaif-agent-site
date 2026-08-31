# OAP Work Order — 076-v

## Objective and authoritative state

Amend only Objective 076 PR
[#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72), branch
`oap/076-agent-model-content-semantics`, base `main`; no new PR and no merge.
Required starting remote report head:
`c52d12a84e047268ca6f40a811178ae3bc7afe6a`, sole parent
`b66d9ff56e91a2a6c80c37a4b7e309d90740ab54`. Remote `main` remains
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. At activation PR #72 is OPEN,
MERGEABLE/CLEAN and all 20 required checks on the 076-u report head pass.

076-u performed substantial work and is not an executor-pathology/no-op turn,
but strategic review rejects its completion claim because its tests encode a
wrong deletion model and two earlier 076 contracts remain bypassable. Repair
those defects, then add the next dependency-correct Agent surface: complete
content-item translation REST semantics. Preserve accepted 076-q through 076-t
behavior and the useful portions of 076-u.

## Independently verified defects to repair

1. `046_001_complete_agent_content_item_crud.py` implements item DELETE as
   `UPDATE content.content_item SET status='DELETED'`. This is not the required
   COW deletion tombstone. Promotion would retain a canonical item row with an
   invented status, and type deletion continues to see that row as a permanent
   dependency. The 076-u test incorrectly asserts this status. A real DELETE
   against the COW view is required; return the pre-delete record for durable
   `200` replay while the visible row becomes absent.
2. `control.slaif_agent_require_capability(p_site_id)` binds capability/site/
   workspace/state/delegator but never checks the exact operation scope stored
   in `control.capability.scopes`. A direct Agent-runtime wrapper call can use a
   lower-scope active capability to invoke a higher-scope wrapper. HTTP scope
   checks do not close this database anti-bypass contract.
3. Agent field create/update/delete wrappers change a field definition without
   incrementing the parent `content_type.definition_version`. Consequently an
   item cannot become stale after a field-model change, contrary to the shared
   075 validator and architecture definition-version contract.
4. The immutable 076-u report ends with a stale sentence naming Objective 070 /
   PR #61. Do not edit it; explicitly correct that append-only reporting defect
   in the 076-v report.

## Repair requirements

### True COW item deletion

- Replace the item delete wrapper with deterministic lock/current-definition/
  row-version/resource/scope/delete-quota checks followed by `DELETE FROM
  content.content_item ... RETURNING` through the active COW view. It must
  create the foundation delete/tombstone operation, not a soft-status update,
  and must return the exact deleted record for the strict audit/idempotent HTTP
  response.
- Item list/get become absent in that workspace; replay remains `200` with the
  original body and no second charge/operation/audit. Canonical base and other
  workspaces/sites remain unchanged. A canonical item deleted in the workspace
  must produce a real COW delete operation while its base row remains intact.
- Visible translation or inbound/outbound relation dependencies still block
  item deletion. After they are removed, the item can be deleted; a type with
  no remaining visible items can subsequently be deleted. Remove the test
  assertion that `DELETED` is a valid content-item state.

### Exact scope at the trusted wrapper boundary

- Evolve the capability helper/wrappers so every Agent database read and
  mutation checks its exact required scope against a valid JSON-array
  `control.capability.scopes`, in addition to existing capability/workspace/
  site/state/delegator/resource/quota checks. Malformed scope storage fails
  closed.
- Existing mappings are exact: type list/get and field list/get use
  `content-model:read`; type create/write/delete use their corresponding
  `content-model:*`; field create/write/delete use the corresponding
  `field-definition:*`; item list/get/create/write/delete use the corresponding
  `content-item:*`. New translation wrappers use the translation scopes below.
- HTTP checks remain defense in depth. A direct runtime call with a real but
  wrong-scope capability must fail before disclosure, quota charge, or COW
  change. Correct-scope direct calls retain resource/quota confinement. PUBLIC
  and old bypass signatures receive no execute authority. Custom PostgreSQL
  settings remain trusted server-selected context, never credentials exposed
  to an external client.

### Parent content-model definition version

- Every successful field create, update, or delete must lock and increment the
  exact ACTIVE same-site parent content-type definition version atomically in
  the same COW operation/transaction. A failed, replayed, stale, denied, or
  cancelled field mutation changes neither parent nor field version.
- The item create wrapper persists the current post-field-change parent
  definition version. Later field change makes existing items stale; item
  update and translation/relation writes fail 422 until a future approved
  mapping/recreation path. Do not silently rewrite item versions.
- Prove concurrent field mutations serialize parent-version increments without
  lost updates and preserve field optimistic locking/resource limits.

## Complete Agent translation semantics

Add typed deterministic production routes under the exact item resource:

```text
GET|POST /api/agent/v1/content-items/{item_id}/translations
GET|PATCH|DELETE /api/agent/v1/content-items/{item_id}/translations/{translation_id}
```

- GET uses `translation:read`; POST/PATCH/DELETE use `translation:write` (the
  architecture exposes one translation write scope). Every mutation requires
  `Idempotency-Key`. PATCH and DELETE require a positive expected row version;
  DELETE returns the exact deleted record with `200` for replay.
- Reuse `CreateTranslationRequest`, `UpdateTranslationRequest`,
  `TranslationRecord`, shared `validate_values(..., localized=True)`, locale
  validation, exact current item/type definition checks, and site/item
  confinement from the 075 production substrate. Add only an Agent delete
  request model if needed. Translation values may contain only localized
  fields and must satisfy required/cardinality/primitive/bounds; base item
  values remain nonlocalized.
- Trusted read/mutation wrappers enforce the parent item’s type ID/key
  allowlists before disclosure/write, exact `translation:read|write` scope,
  site/workspace/capability/state/delegator, row version, and current definition.
  Create/update consume `mutation`; delete consumes `delete` and therefore
  `delete_quota` plus `delete_enabled`/`max_deletes`. Wrapper charge and COW
  write roll back together on every failure.
- Wrong site/item/translation path relationship is an invisible 404. Stable
  403 scope/resource denial, 409 row/idempotency conflict, 422 locale/value/
  stale-definition validation, 429 quota, and 503 infrastructure semantics
  must match the existing Agent envelope.

Extend the strict audit/check/Python contract exactly:

- `CONTENT_ITEM_TRANSLATION_CREATED` ↔ `content_item_translation`, `POST`,
  `201`, `mutation`;
- `CONTENT_ITEM_TRANSLATION_UPDATED` ↔ `content_item_translation`, `PATCH`,
  `200`, `mutation`;
- `CONTENT_ITEM_TRANSLATION_DELETED` ↔ `content_item_translation`, `DELETE`,
  `200`, `delete`.

The legacy completion must reject translation resources. First success has one
server operation, COW operation, idempotency row, exact semantic audit row and
charge in one transaction. Replay/mismatch/cancellation semantics remain exact.

## Migration and proof

Add one reversible migration from `046_001` (normally `047_001`). Update every
current-head/history/package/readiness/privilege fixture in the same round.
Downgrade restores exact 046 functions, audit constraint, owners and grants;
upgrade restores the repaired/item+translation contract with COW still enabled
and hardened. Fixed `pg_catalog` search paths, no dynamic SQL, no foundation-
private API.

Required tests use real human-issued capabilities and actual Agent HTTP against
real PostgreSQL for claimed behavior. Direct SQL is limited to neutral setup,
adversarial least-privilege calls, and owner/reviewer assertions.

- Replace the false soft-delete test with real canonical and workspace-created
  item COW-delete proof, response replay, foundation operation classification,
  base/other-workspace independence, dependency removal, and later type delete.
- For every existing type/field/item read and mutation wrapper, prove a real
  wrong-scope capability cannot call it directly; representative correct-scope
  direct calls charge/enforce once. Prove malformed scopes fail closed. Verify
  no old bypass signature/grant remains.
- Prove field create/update/delete increment parent version exactly once; stale
  item update and translation writes then fail with zero residue; concurrent
  field changes do not lose an increment.
- Through Agent REST, create/list/get/update/delete a translation with exact
  audit/idempotency/quota/COW evidence, replay/mismatch, row-version race,
  cross-workspace/site/item denial, allowed/disallowed parent type, missing/
  wrong scope, locale/localized/required/primitive/bounds failures, revoke/
  expiry/freeze/delegator loss, delete limits, dependency behavior, cancellation
  and canonical isolation. Reuse existing generic proofs only where they
  genuinely exercise the same production boundary.
- Exercise 046→047 and 047→046→047 with legacy and semantic audit rows,
  content state, exact functions/owners/grants/checks/head/readiness.

Run focused tests, complete Agent mutation and 075 validator regressions, then
full Python quality/unit/integration/PG14–18, Editor/Render, migration/bootstrap/
privilege/package, Node, repository/Markdown/Mermaid/supply-chain, and one clean
relevant Compose/edge gate. Repair in-scope CI on the same branch. Report exact
commands/counts/versions/skips and all current required checks; pending/skipped/
not-run is not pass.

## Termination, scope and report

Do not return before all three rejected 076-u defects, production translation
CRUD, and focused PostgreSQL tests exist. `PARTIAL`/`BLOCKED` requires a precise
external/technical blocker plus attempted evidence; difficulty or long tests
are not blockers. Another unexplained no-op return is an execution-control
failure, but substantial failed implementation evidence is reported honestly.

No Agent relations or collection views yet; combine those in the next 076
production slice. No page/navigation/redirect/composition/design/media/MCP/
browser/review/promotion, final public OpenAPI/NGINX proof, dependency,
architecture/governance/workflow, prior artifact edit, production or release
claim. Preserve Editor behavior and page/component legacy paths. No production
secret/system/data/credential access; routine VM setup uses executor sudo.

Commit the exact order and `oap/active` unchanged with implementation on the
same branch, push, never create/close/merge another PR, then publish exactly
`oap/reports/076-v-repair-item-semantics-and-add-translations.md` as a final
report-only child of the literal implementation SHA with
`Report publication commit: SELF`. Include exact repairs/routes/migration/
functions/scopes/grants/audit/quota/tests/checks/skips/risks, correct the 076-u
Objective 070/PR #61 typo append-only, and state relations/views/final OpenAPI
remain open. No post-report push; signal exact FIFO `OK` and wait.
