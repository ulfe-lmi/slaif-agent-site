# OAP Work Order — 076-s

## State and objective

AMEND_EXISTING_PR #72 only on
`oap/076-agent-model-content-semantics`; required start report head
`2acc1bef79c056a96e21b6258321c4cefcd006d0`, implementation parent
`422e240831dabdc596a18f6684ea38744f66d06c`, base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. All 20 current-head checks pass.
No new PR/merge. Type CRUD and field create resource enforcement are closed.

Complete only trusted-database resource and optimistic-version enforcement for
field-definition update/delete. Durable audit method/status/quota coupling and
final OpenAPI/public closure remain later 076 rounds.

## Production requirements

In unmerged revision `044_001_agent_resource_constraints.py`, replace exact
signatures:

- `content.slaif_agent_field_definition_update(uuid,uuid,uuid,text,boolean,boolean,integer,integer,jsonb,jsonb,integer)`
- `content.slaif_agent_field_definition_delete(uuid,uuid,uuid,integer)`

Preserve `SECURITY DEFINER`, fixed search path, exact typed return rows, trusted
COW/site/parent relationship, semantic field validation, dependency behavior,
and only Agent runtime EXECUTE; revoke PUBLIC/all other product roles.

Take the established deterministic definition lock for workspace/type/field,
then load+lock the exact visible field joined to an ACTIVE same-site parent.
Check expected definition version only after locking so concurrent same-version
operations cannot both commit. Invoke the owner-only typed resource helper: a
nonempty `allowed_type_ids` must contain the persisted parent ID and a nonempty
`allowed_type_keys` its persisted key. Delete additionally denies when
`delete_enabled=false`. Enforce before DML; failed/stale/denied calls leave no
COW operation. Preserve deletion denial when visible items use the field. Leave
`max_deletes` for the later audit/quota coupling round.

Extend 044 downgrade to restore exact pre-044 field update/delete bodies and
grants in dependency-safe order; upgrade→downgrade→upgrade must restore guarded
enforcement with COW enabled.

## Intended-interface and negative proof

Using the real Agent mutation fixture, prove:

1. Real Agent HTTP creates parent+field, PATCH updates under matching parent
   ID/key constraints with exact version/action/resource/status; replay is
   byte/operation identical and changed-body reuse is rejected without residue.
2. ID-allowed/key-disallowed and key-allowed/ID-disallowed fail inside the DB,
   including direct runtime-wrapper bypass of HTTP; wrong site/type/field and
   inactive/deleted parent fail closed without disclosure/residue.
3. `delete_enabled=false` denies public and direct field deletion; enabling it
   permits exact-version Agent HTTP deletion, consumes only delete quota,
   records one delete action, creates the field tombstone, and leaves canonical/
   other workspaces unchanged.
4. Two distinct connections/operations racing the same field expected version
   yield exactly one update and one stable stale/conflict denial, one version
   increment and one added COW operation.
5. A visible content item using the field still blocks deletion. Downgrade
   restores exact signatures/grants; re-upgrade restores resource enforcement.

Neutral setup/assertions are allowed; product behavior uses public Agent HTTP
or the expressly required direct-wrapper anti-bypass call, never an internal
substitute. Run Ruff/format, focused PostgreSQL 16 tests, the complete Agent
mutation module and MyPy. Do not run broad local Compose/CI; push once and
inspect fresh CI.

## Termination and report

Do not report before both wrappers and focused proof exist/pass. PARTIAL/
BLOCKED requires exact attempted-command evidence and a concrete blocker;
complexity is not one. No audit schema, HTTP/OpenAPI shape, dependency,
workflow/docs/governance/production change or prior transcript edit.

Publish exactly `oap/reports/076-s-enforce-field-update-delete-resources.md` as
report-only child of literal implementation SHA with wrappers/grants/downgrade,
public/direct/race/idempotency/audit/quota evidence, tests/checks/skips, SELF,
no extra PR/merge/secrets/post-report push. Signal exact FIFO `OK`, then return
to one control reader.
