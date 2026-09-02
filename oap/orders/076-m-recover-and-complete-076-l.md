# OAP Work Order — 076-m execution-control recovery

## Identity, mode, and diagnosis

This is the immutable bookkeeping continuation required to complete the failed
076-l slice; it is **not** a new decomposition or reduced substitute.
AMEND_EXISTING_PR #72 only, branch
`oap/076-agent-model-content-semantics`, base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`, required starting remote head
`65027b93fa8e3931bf3f3a4641d336cfaeea5bea` (076-l report-only commit; parent
transcript `6ed97acf89877e365f908e6119d95e6df486e294`). No new PR, merge, rebase, or
prior-order/report edit.

The human explicitly authorized the strategic model to implement this recovery
directly after the executor-control failure. No coding agent is launched,
queued, resumed, or signaled; no FIFO handshake applies to this exceptional
round. The strategic model publishes this order/active record, performs the
bounded implementation and verification, and records the exception honestly in
the report. Normal strategic/executor separation resumes after this recovery.

076-l was sufficiently bounded and had no technical blocker. Its transcript
proves the old executor ran as `gpt-5.6-luna`/high, read the active/order, then
committed transcript, wrote PARTIAL, pushed, signaled, and ran **no** code
inspection, repository diagnosis, PostgreSQL command, edit, or test. Last-turn
usage was about 277K of a 475K window, so context exhaustion is ruled out.
Strategic diagnosis also proved passwordless sudo, uv 0.12.5, PostgreSQL 16
client/server and port 5432 healthy, correct clean tracked branch/head, full
filesystem authority, and no order contradiction. The old session additionally
spawned duplicate control-FIFO readers after unblock. That process tree was
terminated; a briefly attempted replacement was also terminated after the human
clarified that agent launches require explicit approval. There are zero FIFO
readers. Treat risk as a reason to test, not a reason to stop before attempting
work.

## Concrete implementation anchors

- Edit the unmerged migration
  `services/backend/src/slaif_agent_site/db/alembic/versions/044_001_agent_resource_constraints.py`.
- Its current owner-only helper is
  `control.slaif_agent_resource_constraints(p_site_id uuid)` returning one row:
  `allowed_type_ids uuid[]`, `allowed_type_keys text[]`,
  `max_content_types integer`, `max_fields_per_type integer`,
  `delete_enabled boolean`, `max_deletes integer`; PUBLIC and Agent/Editor/
  Control direct EXECUTE are revoked.
- The exact pre-044 guarded create wrapper to preserve is in
  `026_001_agent_site_binding.py`: public signature
  `content.slaif_agent_content_type_create(uuid,text,jsonb,text,jsonb)`, owner
  `SECURITY DEFINER`, fixed `pg_catalog` search path, calls
  `control.slaif_agent_require_cow_site(p_site_id)`, then delegates to
  `content.slaif_agent_unchecked_content_type_create(...)`, and is granted only
  to `slaif_agent_runtime`. Its underlying semantic insert/return behavior was
  introduced in `025_001_agent_mutation_surface.py`; do not duplicate or weaken
  it.
- Existing deterministic transaction-lock conventions include
  `pg_advisory_xact_lock(hashtextextended(...))` in revisions 028/030/039/042;
  revision 042 uses fixed entity namespaces for navigation/redirects. Derive
  this lock from the valid trusted `app.session_id` plus a fixed content-type
  namespace, never from caller site/key alone, and take it before count+insert.
- Reuse `services/backend/tests/integration/test_agent_mutations.py`: `_seed`
  creates the real migrated site/workspace/capability; `_agent_settings`,
  `role_pool("slaif_agent_runtime")`, `asyncpg_cow_session`, the direct wrapper
  call near the existing type-create proof, and owner/reviewer assertion paths
  are established anchors. Two distinct runtime connections/operations must
  drive the race.
- 044 downgrade currently only drops the helper. Extend it to drop the 044
  replacement create wrapper, recreate the exact 026 guarded wrapper body and
  PUBLIC/runtime grants, then drop the helper; upgrade→downgrade→upgrade must
  preserve the contract.

## Required 076-l production behavior

Replace only the existing-signature
`content.slaif_agent_content_type_create` in revision 044:

1. Preserve and invoke trusted COW/site validation and the unchecked semantic
   function; preserve input validation, row shape, errors and COW behavior.
2. Read typed constraints only through the owner-only helper. An empty/missing
   allowlist is unrestricted inside existing scope/quota authority; a nonempty
   `allowed_type_keys` must contain `p_key` or fail closed before DML.
3. Parse trusted workspace UUID from `app.session_id`, take the deterministic
   transaction advisory lock, then count ACTIVE content types through the
   current COW overlay visible in this session. If non-NULL
   `max_content_types` is already reached, fail closed before insert. Never
   inspect raw base/change tables as owner and never count another workspace.
4. Revoke PUBLIC on the replacement and preserve only the pre-044 Agent runtime
   EXECUTE grant. Runtime still cannot call the helper or read constraints/base/
   change/audit directly.
5. Make downgrade restore the exact pre-044 function, ownership behavior and
   grants described above.

Do not substitute Python/HTTP prechecks for this DB authority; existing HTTP
checks remain defense in depth.

## Mandatory focused PostgreSQL proof

Add a focused real-PostgreSQL test (dedicated test or clearly isolated test in
`test_agent_mutations.py`) proving all of these against migrated revision 044:

- allowed key succeeds and a key outside a nonempty allowlist is denied with no
  COW residue;
- exact sequential maximum allows the last slot and rejects the next;
- two distinct connections/operations racing one remaining slot produce
  exactly one commit and one stable denial, with exact final visible ACTIVE
  count and no losing residue;
- a valid direct `slaif_agent_runtime` wrapper call cannot bypass allowlist or
  maximum, and runtime lacks helper EXECUTE;
- canonical and another workspace/site remain unchanged/invisible; and
- downgrade→upgrade restores the exact create signature, grant and behavior.

Run Ruff on changed files, the focused test on PostgreSQL 16, and the migration
roundtrip. Use passwordless sudo/local services autonomously. Fix focused
failures until green. Do not run broad suites or rerun unchanged CI in this
recovery turn; after one finished implementation push, inspect initial PR checks
and report pending honestly.

## Termination, non-goals, and report

Do not publish the report or signal response until **both** the production
function exists and the required focused PostgreSQL proof exists and passes.
PARTIAL/BLOCKED is permitted only for a concrete external or technical blocker
after attempted-command evidence, with exact command/error/root cause and why
safe local remediation failed. Complexity, coordination, perceived SQL risk,
or desire for another round are not blockers.

No type update/delete, field wrapper, audit/quota coupling, HTTP/OpenAPI change,
other entity, dependency, CI workflow, docs/governance, broad refactor,
production access, or release claim. Publish exactly
`oap/reports/076-m-recover-and-complete-076-l.md` as an immutable report-only
child of a literal 40-hex implementation SHA. Include exact PR/base/start/head,
diagnosis acknowledgement, function/helper/lock/grant/downgrade details, files,
commands/results/race outcomes, check state/skips, no extra PR/no merge/no
secrets, and `Report publication commit: SELF`; no post-report push.
