# OAP Work Order — 076-r

## State and objective

AMEND_EXISTING_PR #72 only on
`oap/076-agent-model-content-semantics`; required start report head
`cbbe4d9e47744e9ddb187cecd84a304cc5ae2b7d`, implementation parent
`6e89e1b22ad3fc7ece312a8d74f7fc6e7c59c432`, base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. All 20 current-head checks pass.
No new PR/merge. Type create/update/delete resource enforcement is closed.

Complete only trusted-database resource enforcement and concurrency safety for
field-definition creation. Field update/delete, audit-column coupling and final
OpenAPI/public closure remain later 076 rounds.

## Production requirements

In unmerged revision `044_001_agent_resource_constraints.py`, replace the exact
existing signature
`content.slaif_agent_field_definition_create(uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb)`.

Preserve trusted COW/site validation, exact parent ACTIVE type/site check,
semantic field validation/return shape, `SECURITY DEFINER`, fixed search path,
and only Agent runtime EXECUTE; revoke PUBLIC/all other product roles.

Load and lock the visible parent type, then call the owner-only typed resource
helper. A nonempty `allowed_type_ids` must contain the persisted parent ID and a
nonempty `allowed_type_keys` must contain its persisted key. Parse workspace
only from trusted `app.session_id`; take a deterministic transaction advisory
lock keyed by workspace plus parent type before count+insert. Count only field
definitions visible through this workspace's COW overlay for that site/type.
When non-NULL `max_fields_per_type` is reached, fail before DML. Concurrent
public/direct calls with one remaining slot must yield exactly one commit and
one stable denial, with no losing COW operation. Empty/missing constraints stay
unrestricted inside existing scope/quota authority.

Extend 044 downgrade to restore the exact pre-044 field-create body/grants in
dependency-safe order. Upgrade→downgrade→upgrade must restore enforcement while
COW remains enabled.

## Intended-interface and negative proof

Use the real Agent mutation fixture and prove:

1. A real capability creates a parent type and fields through Agent HTTP under
   matching parent ID/key constraints; exact sequential maximum allows the last
   slot and rejects the next without idempotency/audit/quota/COW residue.
2. ID-allowed/key-disallowed and key-allowed/ID-disallowed are rejected by the
   DB wrapper, including direct `slaif_agent_runtime` calls that bypass HTTP.
3. Two distinct connections/operations racing one remaining field slot under
   the same workspace/type produce one success, one resource-limit denial,
   exact visible count and one additional COW operation.
4. Wrong site/type, inactive/deleted/stale parent and another workspace/site
   remain fail-closed/invisible; canonical remains unchanged.
5. Public create success/replay is byte/operation identical and consumes/audits
   once. Downgrade restores exact signature/grants and re-upgrade re-enforces.

Neutral owner setup/assertions are allowed; product behavior under proof uses
Agent HTTP or the expressly required direct-wrapper anti-bypass call, never an
internal substitute. Run Ruff/format, focused PostgreSQL 16 tests, the complete
Agent mutation module and MyPy. Do not run broad local Compose/CI; push once and
inspect fresh CI.

## Termination and report

Do not report before the wrapper and focused proof exist/pass. PARTIAL/BLOCKED
requires exact attempted-command evidence and a concrete blocker; complexity is
not one. No field update/delete, audit schema, HTTP/OpenAPI shape, dependency,
workflow/docs/governance/production change or prior transcript edit.

Publish exactly `oap/reports/076-r-enforce-field-create-resources.md` as a
report-only child of literal implementation SHA with wrapper/grants/downgrade,
public/direct/race/idempotency/audit/quota evidence, tests/checks/skips, SELF,
no extra PR/merge/secrets/post-report push. Signal exact FIFO `OK`, then return
to one control reader.
