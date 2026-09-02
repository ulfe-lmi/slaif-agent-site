# OAP Work Order — 076-i

## Objective and verified state

Amend only PR #72 / `oap/076-agent-model-content-semantics`; no new PR/merge.
Required remote start head is 076-h report
`fcf8594f6a71e6f4d676af9e9403aacd4ce85afb`, sole parent transcript commit
`5e21ef151dedcb49d630f924d263d106eb70e02d`; base/main remains
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. 076-h made no product change and
again used a short report SHA; preserve it immutably and use literal 40-hex in
this report. This is one small safety repair only: harden and prove the unmerged
044 resource helper. Wrappers/concurrency/audit remain later rounds.

## Exact implementation

Edit revision `044_001_agent_resource_constraints.py` in place because it is
unmerged. Replace the current zero-argument raw-json helper with one owner-
defined fixed-signature helper taking `p_site_id uuid` and returning a typed
record or equivalent non-leaking values for exactly: allowed UUID type IDs,
allowed bounded type keys, optional nonnegative integer max content types,
optional nonnegative integer max fields per type, optional boolean delete
enabled, and optional nonnegative integer max deletes.

- Derive workspace only from `app.session_id`; parse both session and operation
  settings as UUIDs inside exception-safe logic; call/preserve
  `control.slaif_agent_require_cow_site(p_site_id)`; require the selected
  workspace ID/site to match and remain ACTIVE/unexpired with active site and
  delegator/account. No caller-provided workspace/capability/constraint payload.
- Accept `{}` as unrestricted/default. Reject non-object JSON, unknown keys,
  non-array allowlists, invalid UUIDs, empty/oversized/non-string keys,
  booleans masquerading as integers, negative or unreasonably large maxima, and
  wrong boolean types with stable fail-closed errors. Do not expose raw JSON.
- Immediately `REVOKE ALL` on the helper from PUBLIC and every runtime role;
  grant it to nobody. A later owner-defined wrapper can invoke it, but
  `slaif_agent_runtime`, Editor, Control, Render and public users cannot call it
  directly or SELECT `control.workspace.resource_constraints`.
- Downgrade drops the exact hardened signature and leaves no 044 object/grant.

## Focused proof and done

Add one focused real-PostgreSQL integration module that upgrades to 044 and
proves: valid empty and fully populated constraints return exact typed values;
invalid/missing session or operation UUID fails; wrong site/workspace/state
fails; every malformed key/value class fails; PUBLIC and each runtime role lack
helper EXECUTE and constraint-column SELECT; and downgrade→upgrade restores the
same signature/permissions. Run Ruff on changed files and only this focused
module on PostgreSQL 16. Fix failures autonomously; use passwordless sudo/local
DB if required. Push once, inspect initial CI without reruns, and report pending
honestly. Binary done is the hardened helper plus these focused tests; do not
return a transcript-only PARTIAL because no external blocker exists.

## Non-goals and report

Do not replace any type/field wrapper, add locks/counting, change HTTP/audit/
OpenAPI/semantic entities/dependencies/CI/docs/governance, edit prior transcript,
or run broad suites. Publish exactly
`oap/reports/076-i-harden-resource-helper.md` once as report-only child of a
literal 40-hex implementation SHA, with exact PR/start/head, signature/
validation/grants/downgrade, files, commands/results/skips/pending CI, no extra
PR/no merge/no secrets, and `Report publication commit: SELF`; no post-report
push.
