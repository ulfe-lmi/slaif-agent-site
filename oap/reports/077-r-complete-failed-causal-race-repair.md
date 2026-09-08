# OAP Coding-Agent Report — 077-r

## Work order

- Identifier: `077-r`
- Work-order file: `oap/orders/077-r-complete-failed-causal-race-repair.md`
- Work-order SHA-256: `0c5f8409813ab20218de760011d620ecf0a043331412d7bb3243f25b90ae656a`
- Active SHA-256: `5206473873ffb25e08a45ac0ba7a44faea97411442391007e6909b71a0ee8810`
- Numeric objective: `077`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`BLOCKED`

## Executive summary

The 077-q causal preview/canonical/`READ COMMITTED` proof is now green. The
077-r pre-statement lock path is implemented: structural Agent/Editor writes
hold lifecycle-shared and structure-exclusive session locks before their COW
transaction snapshot, and a common type-dependency lock covers content-type
and direct dependency races. The dependency matrix race now passes.

One concrete structural contract defect remains: the full Editor/Agent
structural race still returns `RESOURCE_NOT_FOUND` (404) for the Agent page
delete in the dependent page-delete/redirect-update race, where the required
outcomes are 200 or stable 409. The exact post-tentative-locale cancellation
and actual Render lifespan restart proof are also unfinished. No accepted
status was broadened and no false proof was retained.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), `OPEN`, not
  merged
- Base/head: `main` /
  `oap/077-agent-site-structure-semantics`
- Starting remote report head:
  `3d946e60f240aaa77ebd72e0921eb9fe5bf8e41a`
- Implementation head SHA:
  `46ff188b91074c02ba95e8e5fc39e57781fe41f0`
- Parent of implementation:
  `3d946e60f240aaa77ebd72e0921eb9fe5bf8e41a`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- New PR: no; existing PR amended: yes; merge/auto-merge: NO

## Changes made

- Added the shared `prelocked_cow_session` path: session-level lifecycle-shared
  and structure/type-dependency-exclusive locks are held before the COW
  transaction starts, while the SQL wrappers retain their own defense-in-depth
  locks.
- Applied the common structural pre-lock to Agent and Editor page/locale/
  navigation/redirect mutations.
- Added common type-dependency pre-lock propagation for content types, fields,
  items, translations, relations and collection views.
- Preserved the 054 preview touch/recheck split, causal snapshot proof and
  Postgres `libcurl=8.22.0-r0` security overlay from 077-q.

## Acceptance-criteria evidence

### Causal snapshot and negative control

- The preview proof establishes an actual locale/navigation/redirect/page
  query, pauses Render, awaits all three public Agent commits, then releases
  Render. It passes with complete before-state and fresh after-state.
- The canonical companion performs one atomic owner-fixture update and passes
  complete before-state/after-redirect assertions.
- The explicit `READ COMMITTED` control observes the staged mixed state and
  passes as a negative control.
- Focused causal Render test: PASSED.

### Lock and dependency races

- Direct dependency matrix race:
  `test_agent_final_dependency_matrix_and_two_connection_delete_races` now
  PASSES after the common type-dependency lock.
- The remaining failure is
  `test_editor_agent_structural_races_share_workspace_site_lock`: in the
  dependent page-delete/redirect-target-update race, the Agent page-delete
  response is `404 RESOURCE_NOT_FOUND`; the required stable outcomes are
  200 for the page-delete winner or 409 for the dependency loser.
- The failure reproduces in a focused rerun after pre-statement locking. It is
  not accepted as a valid race outcome and has not been hidden by widening the
  assertion.

### Security gate preservation

- The complete 077-p supply-chain run remains green: six images, zero Critical,
  high-review findings only, reproducibility and checksum evidence passed.
- Ubuntu Apache and the Postgres Alpine 3.23 `libcurl=8.22.0-r0` overlay were
  not changed by this continuation.

### Remaining required evidence

- Post-tentative-locale cancellation after graph validation and before generic
  completion/audit, with exact rollback and same-key retry: not yet complete.
- Actual Render application/database-adapter stop and fresh-start proof for the
  durable human preview overlay: not yet complete.
- Full current-head CI after this implementation/report push: not yet observed.

## Local verification

- Causal preview/canonical/negative-control focused test: passed.
- Render projection cancellation tests with direct clean-pool assertions: 2
  passed.
- Preview session lock tests: 2 passed.
- Dependency matrix race: passed.
- Remaining Editor/Agent structural race: failed with the exact 404 above.
- Package/policy/evidence tests and changed-code Ruff gates: passed.
- Complete supply-chain evidence from 077-p: passed, zero Critical.
- Earlier full integration run remains 168 passed with the two 077-p race
  failures; the dependency failure was subsequently fixed, while the Editor/
  Agent 404 remains reproduced.

## Scope, safety, and completion boundary

- No secrets, capabilities, cookies, production systems/data, extra PR, merge,
  release or issue closure occurred.
- No dynamic `{slug}` collection-detail behavior, 078 composition/design/Puck,
  media/MCP/freeze implementation/review/promotion/source/sweep/076 work was
  added.
- No exception, scanner suppression, severity override or broad lock-policy
  weakening was used.
- The strongest reason not to accept is the reproducible 404 structural race
  contract failure, followed by the missing post-tentative-locale and actual
  lifespan evidence. Objective 077-r / PR #74 can be declared complete only
  when the race returns the required 200/409 outcomes, those cancellation and
  restart proofs pass, all current checks are green, and strategy accepts the
  bounded scope. The coding agent is not authorized to merge.

No extra PR was created. No merge or auto-merge was performed.
