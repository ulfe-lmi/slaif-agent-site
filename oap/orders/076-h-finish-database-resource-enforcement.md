# OAP Work Order — 076-h

## Objective and verified state

Amend only PR #72 / `oap/076-agent-model-content-semantics`; no new PR/merge.
Required remote start head is 076-g report commit
`701d1e447c2d4e8d460a46402529d62d1892b4d9`, sole parent implementation
`5571d4a8b9226211b4b0a8742e65f72489a3b925`; base/main is
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. 076-g added only revision
`044_001` with `control.slaif_agent_resource_constraints()` and truthfully left
every wrapper/concurrency proof incomplete. Independent review found the helper
also has default PUBLIC EXECUTE, accepts a non-UUID operation string, does not
bind a requested site, validates only top-level keys, and can expose constraints
outside an intended wrapper. This round repairs 044 in place (unmerged branch)
and completes the DB resource slice; audit coupling remains separate.

## Required implementation

1. Harden 044's helper contract. It must be owner-defined/fixed-signature,
   derive workspace from valid UUID `app.session_id`, require valid UUID
   `app.operation_id`, accept/bind the wrapper's `p_site_id`, reuse or exactly
   preserve `slaif_agent_require_cow_site`, validate the complete six-key JSON
   schema/types/bounds/UUIDs, and return typed values suitable for wrappers.
   Revoke PUBLIC immediately. Do not grant direct helper execution to runtime;
   wrappers may invoke it as owner. No caller-selected workspace/capability or
   constraint GUC is authority and no function reveals raw constraints.
2. In the same reversible 044 revision replace all six existing public-signature
   Agent type/field create/update/delete wrappers. Each first validates trusted
   COW+site, then enforces applicable `allowed_type_ids`/`allowed_type_keys`;
   deletes require `delete_enabled`; type create enforces visible ACTIVE
   `max_content_types`; field create enforces visible `max_fields_per_type` for
   its active type. Preserve definition versions, dependency checks, validation,
   row shapes, site confinement and all pre-044 behavior.
3. Serialize count/create decisions using deterministic transaction advisory
   locks keyed by trusted workspace and entity class, plus type for fields.
   Count via the active COW overlay seen by runtime (including tombstones), never
   owner-bypass reads of raw canonical/base/change tables. Parallel calls with
   one slot cannot both commit. Leave `max_deletes` structurally validated but
   unenforced until the audit/quota round.
4. Explicitly revoke PUBLIC on helper and replacement wrappers, grant runtime
   only the six wrappers it already had, preserve Editor/Control grants, and
   prove runtime cannot SELECT workspace constraints/base/change/audit or call
   the helper directly. Downgrade restores exact pre-044 definitions/grants and
   drops only 044 objects.

## Required focused proof

Add a dedicated real-PostgreSQL integration module, not assertions appended to
an unrelated one-test file. Prove: malformed session/operation UUIDs; unknown/
malformed constraint values; correct site/workspace/delegator state; helper
PUBLIC/runtime denial; ID/key allow/deny for every applicable update/delete/
create; delete-disabled; exact sequential maxima; overlay tombstone count; and
two independent connections racing one remaining type slot and one field slot,
with exactly one success, one stable denial, exact visible maximum and no
residue. Direct wrapper invocation under valid runtime COW must be unable to
bypass every constraint. Upgrade→downgrade→upgrade must preserve function/grant
contract.

Run Ruff for changed files, the new focused integration module on PostgreSQL
16, the existing content-model COW/mutation integration modules, and migration
roundtrip. Use passwordless sudo/local DB as needed. Work autonomously through
up to five implementation/test repair cycles; expected SQL coordination or a
failing focused test is not a blocker and is not grounds for another helper-only
PARTIAL report. Do not rerun the broad matrix or unchanged CI jobs in this turn;
push the finished slice once, inspect initial GitHub checks, and report pending
honestly. Binary done is hardened non-callable helper + all six wrappers + the
focused security/concurrency proof.

## Non-goals and report

No audit schema/completion/quota coupling, OpenAPI artifact/public E2E, new
semantic family, items/translations/relations/views, pages/navigation/
composition/design/media/MCP/review, dependency, CI workflow, architecture,
prior transcript edit, production/release claim, or broad refactor. Existing
HTTP checks remain defense in depth. Objective 076 remains open.

Publish exactly
`oap/reports/076-h-finish-database-resource-enforcement.md` once as report-only
child of literal 40-hex implementation SHA. Include PR/base/start/head, exact
044 helper/wrapper/grant/lock/downgrade details, files, every command/result,
race counts, failed/skipped/pending checks, limitations, no extra PR/no merge/no
secrets, and `Report publication commit: SELF`; no post-report push.
