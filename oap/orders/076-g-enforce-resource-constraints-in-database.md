# OAP Work Order — 076-g

## Objective and verified state

Amend only PR #72 / `oap/076-agent-model-content-semantics`; no new PR and no
merge. Required starting remote head is the 076-f report commit
`2fa2119707b27ee980466bcb6378064ac41a7f90`, whose sole parent is transcript
commit `e88492e2a0919728892db858d28f6d52a1167895`; base/main remains
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. Round 076-f implemented no product
change because its combined DB-resource/audit request was too broad. That is
not an external blocker: this round implements only DB-enforced resource
constraints. Record that 076-f's report used a short implementation SHA; do not
edit it, and use literal 40-hex SHAs in this report.

## Required production change

Add exactly one reversible Alembic revision after `043_001` that makes the
existing type/field Agent wrappers enforce immutable workspace resource
constraints inside PostgreSQL, where direct runtime calls cannot bypass them.

- Add owner-defined, fixed-signature helper logic that derives the workspace
  only from trusted `app.session_id`, requires valid `app.operation_id`, and
  verifies site, ACTIVE/unexpired workspace, delegator/account/site state using
  the established `control.slaif_agent_require_cow_site` contract. A caller-
  supplied workspace/capability/GUC payload is never authority.
- Parse only the already established keys `allowed_type_ids`,
  `allowed_type_keys`, `max_content_types`, `max_fields_per_type`,
  `delete_enabled`, and `max_deletes`; malformed types, invalid UUIDs, unknown
  keys, negative maxima, or corrupt legacy JSON fail closed. Do not add keys or
  reinterpret missing constraints as denial when current empty-constraint
  behavior means unrestricted within scopes/quotas.
- Replace or wrap the six existing content-type/field-definition create,
  update, and delete functions without changing their public signatures.
  Enforce type IDs/keys on every applicable action, `delete_enabled` on both
  deletes, max visible ACTIVE types on create, and max visible fields for that
  ACTIVE type on field create. Preserve all existing site, COW, definition-
  version, dependency, validation, and return semantics.
- Serialize relevant create/count decisions with deterministic transaction
  advisory locks keyed by trusted workspace and, for fields, type; concurrent
  public or direct-wrapper calls must not overrun a maximum. Count the current
  COW overlay visible through the session, including its inserted/updated/
  tombstoned state, not canonical/base tables through a privileged bypass.
- `max_deletes` is only structurally validated in this round; durable per-
  capability delete counting belongs with audit/quota coupling in 076-h.
  Existing HTTP checks stay as defense in depth and must not become authority.
- Keep helper ownership/search path/grants least-privilege: Agent runtime gets
  EXECUTE only on intended wrappers, no constraint-table reads, base/change
  access, audit access, reviewer/control authority, or owner privileges.
- Downgrade must restore the exact pre-076-g functions/grants and remove only
  this revision's helper objects; migration upgrade/downgrade/upgrade must work.

## Focused proof and binary done

Add real PostgreSQL integration tests proving all of the following through
both the public Agent mutation path and direct `slaif_agent_runtime` wrapper
calls under a valid COW session:

1. allowed ID/key permits the bound type and rejects another type/key;
2. delete-disabled rejects type and field deletes without COW residue;
3. max-type and max-field sequential boundaries are exact;
4. two concurrent creates at one remaining slot yield exactly one commit and
   one stable denial, with visible count at the maximum and no residue;
5. tombstones/overlay visibility do not falsely consume a freed slot;
6. malformed stored constraints and cross-workspace/site substitution fail
   closed; and
7. runtime cannot read the stored constraints or bypass wrapper enforcement.

Run only proportionate post-change evidence in this turn: Ruff on changed
Python, the focused unit/integration files against PostgreSQL 16, migration
upgrade/downgrade/upgrade, and directly affected Agent/Editor regression tests.
Push once, let GitHub run the full matrix, inspect its initial state, and do not
rerun unchanged failures or spend hours duplicating the final objective gate.
Any in-scope deterministic failure may be fixed once before the report; report
everything else honestly as pending/failed. Binary done for 076-g is production
DB enforcement plus the seven focused proofs; audit coupling is not required.

## Non-goals and final report

Do not change audit schema/completion coupling, HTTP/OpenAPI surface, semantic
entity families, items/translations/relations/views, pages/navigation/
composition/design/media/MCP/review, dependencies, architecture, prior orders/
reports, CI workflows, release claims, or production state. Objective 076 stays
open for 076-h audit coupling and later API slices.

Publish exactly
`oap/reports/076-g-enforce-resource-constraints-in-database.md` as an immutable
report-only child of a literal 40-hex implementation SHA. Include exact PR/
base/start/head, migration/helper/wrapper/grant/locking behavior, files, every
focused command and result, concurrency outcomes, skips/pending CI, limitations,
no extra PR/no merge/no secrets, and `Report publication commit: SELF`; no
post-report push.
