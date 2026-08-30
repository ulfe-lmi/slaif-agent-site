# OAP Work Order — 076-n strategic recovery follow-up

## State and authority

AMEND_EXISTING_PR #72 only, required start head
`e80f8e367ddd68315dea7e9b6a56b77e4aafafd4`, parent implementation
`9127cd33bb1791fcd78a877cc39992b8e079ee5e`, base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. This is the minimum CI repair
after the human-authorized strategic 076-m implementation. The human authorized
the strategic model to fix this directly; launch/signal no agent and do not
merge.

## Verified failure and required repair

Current-head CI run `33339518098` fails Python 3.12/3.13/3.14 identically because
repository tests still encode migration head `042_001` and omit already-added
043/044 migration files from wheel/sdist inventories. Exact failures are four
Control readiness cases returning `migration_mismatch`, package-file inventory
missing `041_001_agent_semantic_audit.py` and
`044_001_agent_resource_constraints.py`, and Alembic graph expecting 042 rather
than actual linear head 044.

Update only stale test/packaging expectations:

- Control unit and integration readiness fixtures use current schema/marker
  `044_001` where the test intends a current migration; preserve intentional
  mismatch cases.
- Bootstrap/editable-domain/session integration expectations and CLI output use
  current head `044_001`.
- Wheel and sdist exact inventories include the physical 043 semantic-audit
  filename and 044 resource-constraint migration.
- Alembic contract expects head/history `044_001`, `043_001`, `042_001`, then
  the existing chain.

Do not change production code, migration semantics, dependencies, workflows,
prior transcript, or weaken exact inventories/readiness checks. Run Ruff/format,
the complete unit+repository suite, affected integration tests, MyPy, package
build/inventory proof and repository policy. Push once; inspect fresh CI without
rerunning superseded jobs.

Publish `oap/reports/076-n-repair-current-migration-contracts.md` as report-only
child of literal implementation SHA, recording exact tests/checks, human-
authorized strategic exception, SELF, no agent/FIFO/new PR/merge/secrets or
post-report push.
