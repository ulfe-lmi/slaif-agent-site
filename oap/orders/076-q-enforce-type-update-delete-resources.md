# OAP Work Order — 076-q

## State and objective

AMEND_EXISTING_PR #72 only, branch
`oap/076-agent-model-content-semantics`, base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`, required start report head
`4c148cfd2f4e2fd5770ab70ae0a9d67242493de4` with implementation parent
`1a74ae193ef9ca835b5420b6d671491dde0a755d`. All 20 report-head checks pass.
No new PR or merge. The recovered type-create/resource/restart slice is closed;
do not revisit it absent a real regression.

Complete only trusted-database resource enforcement and conflict safety for
content-type update/delete. Field wrappers, audit-column coupling and final
OpenAPI/public closure remain later 076 rounds.

## Production requirements

Edit unmerged revision `044_001_agent_resource_constraints.py` to replace the
existing public signatures:

- `content.slaif_agent_content_type_update(uuid,uuid,jsonb,text,jsonb,integer)`
- `content.slaif_agent_content_type_delete(uuid,uuid,integer)`

Preserve `SECURITY DEFINER`, fixed search path, typed return rows, trusted
`slaif_agent_require_cow_site`, site/status/dependency semantics and only the
existing Agent runtime EXECUTE grant; revoke PUBLIC/all other product roles.

For both functions, load and lock the exact visible ACTIVE type for this site
before mutation. Check the expected definition version after the row lock so
two concurrent operations cannot both pass a pre-lock check. Then call the
owner-only typed resource helper. A nonempty `allowed_type_ids` must contain the
persisted ID and a nonempty `allowed_type_keys` must contain the persisted key;
empty/missing lists remain unrestricted inside scopes/quotas. Delete additionally
fails closed when `delete_enabled` is explicitly false. Enforce before DML and
leave no losing COW operation. Preserve delete dependency denial. Do not enforce
`max_deletes` here; durable delete counting remains coupled to audit/quota in a
later round.

Extend 044 downgrade to restore the exact pre-044 update/delete bodies and
grants, then restore type-create and drop the helper in dependency-safe order.
Upgrade→downgrade→upgrade must work with COW enabled.

## Intended-interface and negative proof

Add focused real-PostgreSQL coverage using the existing Agent mutation fixture:

1. A real capability creates a type through Agent HTTP, then PATCH updates it
   under allowed ID/key with exact version/action/resource/status; replay is
   byte/operation identical and adds no COW/audit/quota residue, while changed
   payload under the same key is rejected.
2. ID-allowed/key-disallowed and key-allowed/ID-disallowed cases are denied by
   the DB wrapper, including direct runtime invocation that bypasses HTTP
   prechecks; no residue or cross-site/workspace disclosure.
3. `delete_enabled=false` denies public and direct deletes with no residue;
   enabling it permits exact-version deletion through Agent HTTP, consumes only
   delete quota, records the delete action once, creates the workspace tombstone,
   and leaves canonical/other workspaces unchanged.
4. Two distinct connections/operations racing the same expected update version
   yield exactly one success and one stable stale/conflict denial, with one
   version increment and no losing operation.
5. Existing type dependencies still deny deletion; stale version and wrong
   site/type remain fail-closed. Downgrade/re-upgrade restores exact grants and
   resource enforcement.

Neutral owner setup/assertions are allowed; product behavior must use public
Agent HTTP or the explicitly required direct-wrapper anti-bypass call, never
ORM/service/direct SQL as a substitute. Run Ruff/format, the focused tests on
PostgreSQL 16, the complete Agent mutation integration module and MyPy. Do not
rerun broad Compose/CI locally; push finished code once and inspect fresh CI.

## Termination and report

Do not publish a report before both production wrappers and focused proof exist
and pass. PARTIAL/BLOCKED requires an exact attempted command/error and concrete
external or technical blocker; complexity or perceived SQL risk is not one.
No field/API/OpenAPI/audit schema/dependency/workflow/docs/governance/production
change or prior transcript edit.

Publish exactly
`oap/reports/076-q-enforce-type-update-delete-resources.md` as report-only child
of literal implementation SHA with functions/grants/downgrade, public/direct/
race/idempotency/audit/quota evidence, commands/checks/skips, SELF, no extra PR/
merge/secrets/post-report push. Then signal exact FIFO `OK` and return to one
control reader.
