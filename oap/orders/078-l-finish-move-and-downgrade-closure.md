# OAP Work Order — 078-l: finish F2 and F5 closure

- Objective 078; increment 078/1; round 078-l; AMEND_EXISTING_PR.
- PR [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77), branch
  `oap/078-agent-composition-design-semantics`; base main
  `ae3a4a681bb888260192b7bb1b2a337b4906828d`.
- Verified starting head `3662dd79fd44d44f403edcfcb8da88e600297a6f`,
  report-only child of `b57b35c5d51594a2cd7a027a48de22cc406df883`.
- Required checks: 19 SUCCESS, Markdown FAILURE solely immutable 078-j MD012.
- Existing session only. Scope remains frozen component/local design.
- Strategy has verified A/B/replay, F1 injection rejection, F2 responsive
  CREATE, F3 actual Chromium CSS and F4 Editor/Puck closure. Do not reopen them.
  This is targeted closure of the SAME final audit, not another general audit.

## F2 residual: responsive Agent MOVE

Strategic independently reran
`/tmp/slaif-strategic-authority-3tLQVd/probe.py` with explicit
component-structure:move and all design scopes. Responsive Button, Image and
CollectionGrid CREATE return 201; each subsequent Agent MOVE returns 422.
The Agent MOVE function from 060 still calls scalar
`slaif_agent_component_validate` on the responsive props. 063 fixes CREATE
and Editor wrappers but misses this Agent path.

Replace only that validation with the complete trusted design validator. Moving
unchanged design state requires structure-move, not design-write scopes.
Preserve exact sibling/parent/slot/order/versions, audit/quota/idempotency and
cycle/depth/resource checks. Add real PostgreSQL public Agent tests for all
three component types moving within and across parents/slots, with responsive
props preserved; a structure-only narrowed capability may arrange existing
design but cannot change its values. Replay/stale/cancellation and direct
runtime MOVE must agree. Keep canonical and other workspaces unchanged.

## F5 residual: exact downgrade and incompatible data

078-k's 063 data test uses only scalar Columns.count=2 and downgrades to 062.
It does not prove the requested safe 061->060 boundary for data that needs the
design reader. 061 downgrade still blindly installs scalar validators.

Add a concrete data-bearing test with responsive maps and alignment extension,
then downgrade through 061 to 060. Refuse incompatibility atomically before
dropping/replacing functions or losing data (or implement an already-supported
backward reader without expanding scope). Prove Alembic revision, affected
function definitions/grants, and data/versions are unchanged on refusal.
For compatible data, compare exact prior CREATE/UPDATE/authority definitions
and grants before upgrade vs after downgrade, not only source substrings, then
re-upgrade successfully. Repair only what those tests expose. No migration
data loss, no unreviewed theme or new feature.

## Current truth and F7

Strategy has edited the current MVP-PROGRESS and MVP-CONTRACT-AUDIT text in the
checkout to remove the erroneous suggestion PR77 merged and explicitly record
merged Objective077/PR74 at ae3a4a6. Preserve and commit those edits. Finish
only any residual contradictory current-status wording: 078/1 remains OPEN,
F2/F5 are pending this proof, and later objectives are not PR77 scope.
Set references to the current 078-l source and active pointer truthfully;
do not rewrite historical orders/reports or the original strategic audit.

F7's human approval to remove one final blank from immutable 078-j remains
pending. Do not edit it or reintroduce a lint bypass. Mutable governance was
correctly formatted. If the approval is still absent after the technical
repairs, return a truthful BLOCKED report naming only that decision. Do not
claim all checks green or merge.

## Verification and delivery

Run focused new F2/F5 tests, existing component selection once, relevant
generated/quality/Node checks, and current CI. No full unrelated local suite
or new expensive Compose scenario is required; CI retains deployed regression
coverage. Local tools/setup remain executor responsibility.

Amend only PR77, commit this exact order/active and current truth edits, push,
and publish `oap/reports/078-l-finish-move-and-downgrade-closure.md` as a
report-only SELF child of the literal implementation SHA. Update executor
audit-closure evidence with exact test/command/results and residual F7 status.
No new functionality, PR, merge, agent replacement, security/test exception or
historical rewrite. Signal exact FIFO OK and wait after publication.
