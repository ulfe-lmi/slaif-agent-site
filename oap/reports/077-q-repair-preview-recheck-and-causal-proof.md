# OAP Coding-Agent Report — 077-q

## Work order

- Identifier: `077-q`
- Work-order file: `oap/orders/077-q-repair-preview-recheck-and-causal-proof.md`
- Work-order SHA-256: `ad7a954f028767acfc5b84a854ec9e7491cf62e262518224c803adf9a5ef11b6`
- Active SHA-256: `35129a6c5873cfbdbf9cc89c0fd8247a086b6c2a081074c752c0d27dfd43eb30`
- Numeric objective: `077`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`BLOCKED`

## Executive summary

The 077-p shared lifecycle-lock and Postgres security repairs are preserved.
This continuation separates short preview touch authorization from the long
Render COW recheck, removes the redundant Python pre-lock path, and makes the
causal preview/canonical/`READ COMMITTED` proof pass. Cancellation tests now
directly inspect checked-out connection state after cancellation.

Two concrete blockers remain. The existing structural race suite still has
contract regressions after the shared lifecycle change: one dependency race
allows two apparent winners where one loser must be 404/409, and the Editor /
Agent page-delete race returns `RESOURCE_NOT_FOUND` (404) where the established
contract permits 200/409. The exact post-tentative-locale cancellation proof is
also not yet implemented. No false passing assertion or broad lock-policy
weakening was committed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), `OPEN`, not
  merged
- Base/head: `main` /
  `oap/077-agent-site-structure-semantics`
- Starting remote report head:
  `61e6931b4ce5587816f07516217060a3071439c8`
- Implementation head SHA:
  `ba0c7e20e37ccbef526d57ee6acfa9b3f8778f74`
- Parent of implementation:
  `61e6931b4ce5587816f07516217060a3071439c8`
- 077-p reconciliation: the 077-p report contains a one-character typo in
  its literal implementation SHA; Git parentage is authoritative and the
  actual parent here is `20c238909b7be7d0cc65894cdd93c4c29ace4b57`.
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- New PR: no; existing PR amended: yes; merge/auto-merge: NO

## Changes made

- Added migration `054_001` with a private preview authorization helper and
  two fixed wrappers: touch authorization and no-touch COW recheck.
- Touch mode keeps the short serialized session touch and uses a shared
  workspace row lock; recheck mode uses shared session/workspace row locks and
  performs no update/touch. The old broad preview grant was revoked; only the
  two narrow wrappers are granted to `slaif_preview_reader`.
- Render now calls the touch wrapper before COW and the no-touch wrapper inside
  the repeatable-read COW transaction.
- Removed 077-p's redundant Python structural pre-locks. Database wrappers
  remain authoritative for lifecycle-shared then namespace-994
  structure-exclusive ordering.
- Added direct post-cancellation connection assertions for transaction state,
  `READ COMMITTED`, cleared transaction-local context and connection usability.
- Preserved the exact Postgres `libcurl=8.22.0-r0` overlay and all six-image
  zero-Critical supply-chain evidence.

## Files changed

- `services/backend/src/slaif_agent_site/db/alembic/versions/054_001_preview_recheck_modes.py`
- `services/backend/src/slaif_agent_site/render_api/projection.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`
- `services/backend/src/slaif_agent_site/editor_api/database.py`
- `services/backend/tests/integration/test_render_structure_router.py`
- `services/backend/tests/integration/test_render_projection_integration.py`
- `services/backend/tests/integration/test_render_preview_session_lock.py`
- exact strategy bytes: `oap/orders/077-q-repair-preview-recheck-and-causal-proof.md`,
  `oap/active`

## Acceptance-criteria evidence

### Preview authorization and causal proof

- `054_001` creates internal authorization plus fixed touch/recheck wrappers;
  preview role grants are limited to the wrappers. The recheck uses `FOR SHARE`
  on session/workspace rows and never updates `last_seen_at` or recent-auth.
- Causal preview proof passes with an actual query over locale, navigation,
  redirect and page-resolution data; public Agent page/navigation/redirect
  commits are awaited before Render release; paused preview observes the full
  before-state and fresh preview observes the after-state.
- Canonical companion passes using an atomic owner-fixture update; paused
  canonical observes the before page/navigation and fresh canonical observes
  the after redirect.
- Explicit `READ COMMITTED` negative control passes by observing the staged
  mixed before/after state.
- Focused causal Render test: PASSED.

### Cleanup and restart evidence

- Canonical and human-preview cancellation focused tests now check a newly
  checked-out connection for no active transaction, `READ COMMITTED`, empty
  `app.session_id`, `app.operation_id`, `app.visible_operations` and
  `app.capability_id`, usable SQL, unchanged residue and successful follow-up
  projection.
- Existing browser before-consume/no-event, after-consume/exactly-one-event and
  replay-denied tests remain unchanged and green.
- Exact post-tentative-locale cancellation after the production locale wrapper
  returns, before generic completion/audit, is still missing and is a blocker.

### Structural race blockers

- Full backend integration after the 077-p lock repair: 168 passed, 2 failed.
- `test_agent_final_dependency_matrix_and_two_connection_delete_races` fails
  in `race_view_and_type`: the observed responses contain no permitted loser
  status where one 404/409/422 loser is required. Its teardown also exposed a
  database-role cleanup dependency after the failed path.
- `test_editor_agent_structural_races_share_workspace_site_lock` fails in the
  dependent page-delete/update race with Agent `RESOURCE_NOT_FOUND` (404),
  outside the established 200/409 outcome contract.
- Focused reruns reproduce the structural-race failures. These are not being
  relabeled as acceptable concurrency outcomes.

### Supply-chain evidence

- Complete run:
  `sh tools/supply_chain/run.sh /tmp/slaif-077p-supply-chain-evidence`
  ended `supply-chain-gate: OK images=6 critical=0 high=42` and checksum OK.
- Postgres retained the official Alpine 3.23 index
  `sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f`
  and exact `libcurl=8.22.0-r0` overlay. Two reproducible builds and
  normalized application/package manifests passed; Postgres Critical count is
  zero.
- Apache Ubuntu, Postgres, backend, browser-worker, NGINX and web SBOM/license
  inventory and current Grype evidence all completed with zero Critical.

## Local verification

- Direct lock-contract test: passed.
- Preview session-lock tests: 2 passed.
- Render projection cancellation tests: 2 passed.
- Causal Render snapshot/canonical/negative-control test: passed.
- Locale structural race focused test: passed.
- Package/policy/evidence tests: 35 passed.
- Ruff check/format: passed for changed code.
- Full integration: 168 passed, 2 failed as listed above.
- Complete supply-chain runner: passed, six images, zero Critical.
- Previous clean Compose/public Agent/browser/Apache evidence remains green;
  current-head CI after this push is not yet counted as pass.

## GitHub CI / required checks

The implementation head `ba0c7e20e37ccbef526d57ee6acfa9b3f8778f74` was
pushed before CI observation. The report-only child has not yet been pushed;
no current-head check is counted as pass here.

## Scope, safety, and completion boundary

- No secrets, capabilities, cookies, production systems/data, extra PR, merge,
  release or issue closure occurred.
- No dynamic `{slug}` collection-detail behavior, 078 composition/design/Puck,
  media/MCP/freeze implementation/review/promotion/source/sweep/076 work was
  added.
- No exception, scanner suppression, severity override, lock-policy weakening
  or false-positive acceptance was used.
- The strongest reason not to accept is the two reproducible structural race
  contract failures plus the missing post-tentative-locale cancellation proof.
  Objective 077-q / PR #74 can be declared complete only when those race
  outcomes are repaired without weakening isolation, the tentative-locale
  cancellation/retry and full pool/lifespan evidence is green, all current
  checks are green, and strategy independently accepts the final bounded
  scope. The coding agent is not authorized to merge.

No extra PR was created. No merge or auto-merge was performed.
