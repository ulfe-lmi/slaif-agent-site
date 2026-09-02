# OAP Work Order — 076-u

## Objective and authoritative starting state

Continue Objective `076` by amending only PR
[#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72), branch
`oap/076-agent-model-content-semantics`, base `main`; no new PR and no merge.
Required starting remote report head:
`7dfeab7d9f3b20ed322cac4e959d7538f27431f2`, whose sole parent is the
accepted 076-t implementation commit
`c5b104f1fd567086ce9a24ecfc4bbeb5bb838c65`. Remote `main` remains
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. At activation PR #72 is OPEN,
MERGEABLE/CLEAN and all 20 required checks on the 076-t report head are
successful.

076-t is closed: preserve its strict six-action audit contract, exact method/
status/quota identity, legacy separation, and transactional `max_deletes`.
The next dependency-correct production slice is complete Agent content-item
REST semantics. This round must also close the still-unmet 076-e authority
contract that direct `slaif_agent_runtime` content wrappers cannot bypass the
same trusted resource/quota enforcement used by normal HTTP execution. Do not
carry that control defect into translations, relations, or views.

## Verified implementation anchors and current defects

- `agent_api/agent_http.py` exposes only item list and create at
  `/api/agent/v1/content-items/types/{type_id}`. There is no exact item GET,
  PATCH, or DELETE. Create checks only path/body type equality and does not
  apply the type resource helper in the handler.
- `AgentCowContentModelService.create_item_for_site` in
  `agent_state/mutations.py` calls the old Agent wrapper with hard-coded
  `type_definition_version=1`; it bypasses the shared 075 field/value validator
  and is wrong after a definition version changes.
- The shared production models and validators already exist in
  `content_model/item_models.py`, `content_model/validators.py`, and
  `ContentItemMixin` in `content_model/service.py`. Editor item CRUD already
  uses them. Reuse the same validation law; do not create an Agent-only weaker
  interpretation.
- `025_001_agent_mutation_surface.py` owns the old item-create wrapper;
  `039_001_complete_session_authority_and_proof.py` owns item list and quota;
  `040_001_editable_domain_substrate.py` supplies site-confined/current-
  definition item, translation, and relation substrate. Current migration head
  is `045_001`.
- Generic `execute_agent_mutation` consumes quota before calling the granted
  content wrapper. A holder of the Agent runtime role can call the granted
  type/field/item wrappers directly inside COW and avoid that separate quota
  call. This contradicts the activated 076-d/e direct-wrapper anti-bypass
  contract even though external clients cannot submit SQL.
- The current strict audit migration recognizes only type/field actions.
  Extend it deliberately for item actions; do not revert to the legacy
  completion or nullable semantic identity.
- Reuse the real human-issued-capability/PostgreSQL/COW/HTTP fixtures in
  `services/backend/tests/integration/test_agent_mutations.py`, plus existing
  075 Editor validator and migration round-trip evidence.

## Production requirements

### 1. Complete intended Agent item REST surface

Provide deterministic typed routes for:

- list items of an exact type (preserve the compatible existing path);
- create an item under an exact type;
- exact item GET;
- PATCH item with a mandatory positive `expected_row_version`;
- DELETE item with a mandatory positive expected row version, returning the
  exact deleted/tombstoned workspace record and status `200` for durable replay.

Use `content-item:read`, `content-item:create`, `content-item:write`, and
`content-item:delete` exactly. Every mutation requires `Idempotency-Key` and
uses stable response/error models. Never trust a body/path type, site,
workspace, operation, capability, or definition version selected by the
caller. Preserve stable 403 resource/scope denial, invisible 404, 409 stale/
dependency/idempotency conflict, 422 domain validation, 429 quota, and 503
infrastructure semantics.

### 2. Shared model validation and optimistic concurrency

Create and update must execute the same 075 production validation used by the
Editor: exact ACTIVE same-site type and current `definition_version`; exact
field set; required/localized/cardinality/primitive/validation rules; bounded
JSON/text/status; no executable/unknown/localized-in-base value. Persist the
server-resolved current type definition version at create and never silently
rewrite an existing stale item version. A later definition bump without an
approved mapping makes update fail closed with no residue.

PATCH locks and compares the exact visible item row version after the
deterministic workspace/item lock; one of two concurrent same-version updates
may commit and the other must receive a stable conflict. DELETE is a COW
workspace tombstone/operation, never canonical direct DML. It must reject
wrong site/type/workspace, stale version, and visible translation/relation
dependencies rather than orphaning them. Canonical and other workspaces/sites
remain unchanged.

### 3. Trusted database resource and quota authority

Add one reversible forward migration from `045_001` (normally revision
`046_001`) that makes the effective Agent content wrapper boundary enforce its
own trusted capability/workspace/site/type and quota authority atomically.
The design may replace signatures or introduce narrow replacement wrappers,
but these invariants are mandatory:

- all granted Agent type-create/update/delete, field-create/update/delete, and
  new item-create/update/delete wrappers derive the COW workspace from trusted
  context, bind an explicit authenticated capability to that workspace/site,
  enforce persisted `allowed_type_ids`/`allowed_type_keys`, and consume exactly
  the correct `mutation` or `delete` budget inside the wrapper transaction;
- normal HTTP execution does not double-charge; replay/mismatch never enters
  or recharges a wrapper; failed validation/stale/dependency/cancellation rolls
  the wrapper charge back;
- a direct Agent-runtime wrapper invocation can no longer mutate without the
  same resource, ordinary quota, `max_deletes`, state, delegator, site and
  workspace enforcement. Old bypassable signatures have no Agent/PUBLIC
  execute authority;
- type/field/item Agent read wrappers also enforce the persisted type
  allowlists before disclosure; HTTP checks remain defense in depth;
- page/component legacy create behavior remains operational and may retain the
  existing generic quota path pending Objectives 077/078; do not silently
  broaden this round into those entities.

Use the 044 trusted resource helper and 045 quota function rather than a second
permissive parser. Preserve deterministic locks, fixed `pg_catalog` search
paths, runtime-only execute grants, COW hardening, and exact downgrade
restoration. If the cleanest implementation changes the internal wrapper
signature, update the privilege manifest and every caller/test consistently;
these are internal DB contracts and no raw DB interface is public.

### 4. Strict item audit and idempotency

Extend the strict semantic contract, audit check, typed Python mapping and
completion function with exactly:

- `CONTENT_ITEM_CREATED` ↔ `content_item`, `POST`, `201`, `mutation`;
- `CONTENT_ITEM_UPDATED` ↔ `content_item`, `PATCH`, `200`, `mutation`;
- `CONTENT_ITEM_DELETED` ↔ `content_item`, `DELETE`, `200`, `delete`.

Every first successful item mutation has one server-owned operation UUID, one
COW operation, one completed idempotency record, one exact audit row, and one
appropriate charge in the same transaction. Audit must retain exact
capability/site/workspace/digest/resource/action/method/status/quota fields.
Replay returns the original body/status/operation with no second residue;
changed digest returns 409. The legacy 10-argument completion must reject item
resources after this migration. Strict database completion must reject every
action/resource/method/status/quota/body mismatch.

## Required real proof

Positive behavior must use a real human-issued capability and the actual Agent
application/HTTP handlers against real PostgreSQL. Direct SQL is allowed only
for neutral canonical fixture setup, adversarial least-privilege calls, and
owner/reviewer assertions; no service/ORM/SQL/test helper may perform the item
behavior being claimed.

- With a properly scoped L1 capability, list/create/get/update/delete an item;
  verify exact versions, overlay visibility, replay/mismatch, item actions,
  idempotency/audit/quota/COW records and canonical/other-workspace/site
  independence. Restart persistence remains part of the final public-NGINX
  closure, not a claim from an ASGI-only test.
- Prove required/localized/unknown/invalid primitive/executable/unbounded
  values, wrong body/path/type, disallowed type ID/key, stale definition, stale
  row version, duplicate slug, wrong site/workspace, missing/wrong scope,
  revoke/expiry/freeze/delegator loss and cancellation fail with zero unintended
  residue. Reuse existing generic authority tests where they genuinely cover a
  case; add item-specific evidence where the resource relationship matters.
- Race two same-version PATCHes through distinct connections: exactly one
  update and one conflict. Prove delete dependency denial with existing
  translation and inbound/outbound relation fixtures, then successful delete
  after dependencies are removed. Prove `delete_quota` and `max_deletes` with
  item DELETE and replay.
- As `slaif_agent_runtime`, attack old/new read and mutation wrappers directly:
  absent/wrong capability, wrong COW workspace/site/type, type allowlist,
  exhausted mutation/delete/max-delete budget, and malformed constraint must
  not disclose or mutate. Successful direct calls, if the intended wrapper
  contract permits them, must charge exactly once and remain confined; no
  bypassable old signature may retain execute.
- Exercise 045→046 and 046→045→046 with existing type/field/item/audit/COW
  state; verify functions, definitions, owners, grants, audit checks, current
  Alembic head, privilege manifest, package inventory, and hardened readiness.

## Verification and termination condition

Run focused tests, all Agent mutation and 075 validation regressions, then full
Python quality/unit/integration/PG14–18, Editor/Render regressions, migration/
bootstrap/privilege/package tests, Node contracts, repository/Markdown/Mermaid/
supply-chain gates, and one clean relevant Compose/edge gate. Inspect and repair
in-scope CI on the same branch. Update every exact migration-head/history/
package/readiness fixture in this round. Report exact commands/counts/versions/
skips and all current required checks; skipped/pending/not-run is not pass.

Do not return before the production item GET/PATCH/DELETE, wrapper-authority
repair, strict item audit, and focused real-PostgreSQL tests exist. `PARTIAL` or
`BLOCKED` requires a precise external/technical blocker and attempted evidence;
difficulty, context length, or a long test is not a blocker. If executor/session
pathology causes an unexplained no-op return, stop rather than manufacturing a
smaller repetition.

## Scope and non-goals

No Agent translation/relation/collection-view routes yet; those remain the next
076 slices. No page/navigation/redirect/composition/design/media/MCP/browser/
review/promotion expansion, public OpenAPI/NGINX final proof, dependency,
architecture/governance/workflow, prior artifact edit, production or release
claim. Do not change Editor behavior except shared-validator/internal wrapper
compatibility required to preserve it. Do not add a new item-count resource key
without strategic approval; current type allowlists plus mutation/delete/
`max_deletes` are the bounded contract for this slice. No production secrets,
systems, data or credentials. Routine tools/DB/Compose belong to the executor
VM and passwordless sudo.

## GitHub and immutable report contract

Fetch/reconcile the named open PR and exact head, amend only its branch, commit
the exact activated order and `oap/active` unchanged with implementation, push,
and never create/close/merge another PR. After all non-report work is remote,
publish exactly `oap/reports/076-u-complete-agent-content-item-crud.md` as the
final report-only child of a literal 40-hex implementation SHA, with
`Report publication commit: SELF`. Include exact routes/models/migration/
functions/signatures/grants/audit/quota/files/tests/checks/skips/risks, no
extra PR/no merge, and state that translations, relations, views and final
public OpenAPI proof remain open. No post-report mutation/push; signal exact
FIFO `OK` and return to waiting.
