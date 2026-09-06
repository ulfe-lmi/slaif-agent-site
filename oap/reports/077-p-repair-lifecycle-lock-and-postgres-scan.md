# OAP Coding-Agent Report — 077-p

## Work order

- Identifier: `077-p`
- Work-order file: `oap/orders/077-p-repair-lifecycle-lock-and-postgres-scan.md`
- Work-order SHA-256: `2f617df5e579dc3adbeceb2b04082f848b8a6eca9afd4c66bcd537b29bb15bf2`
- Active SHA-256: `ff595bf67d8b27f0060ca48c0c519bb72ada3e8a94c8cf5a372dfc1b2de4b2c4`
- Numeric objective: `077`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`BLOCKED`

## Executive summary

The Postgres supply-chain blocker is repaired with the minimum exact Alpine
3.23 standard-repository overlay: `libcurl=8.22.0-r0`. The complete
six-image supply-chain gate now passes with zero Critical findings, including
reproducible Postgres builds, SBOM/license evidence and the current Grype scan.

The lifecycle contract is also corrected in the authoritative fresh-install
migrations: active Agent/Editor lifecycle acquisition is shared, while the
workspace/site structural key remains exclusive. Agent and Editor structural
mutations now acquire lifecycle-shared plus structural-exclusive locks before
their COW mutation envelope, so the lock order is established before mutation
reads. A direct PostgreSQL lock-contract test passes.

Objective 077-p remains blocked on the required causal product proof. With the
lock repair, a temporary causal test established an actual Render structure
query, paused the repeatable-read preview, started three public Agent commits,
and awaited those commits before releasing Render. The Agent requests still
timed out and returned `SERVICE_UNAVAILABLE`; they did not durably commit while
the snapshot was paused. The existing structural race suite also exposed two
404 outcomes where its accepted contract is 200/409. The causal proof and race
contract therefore cannot be claimed complete without further in-scope
investigation of COW operation visibility/transaction ordering.

No false-positive snapshot test, exception, scanner suppression, or policy
weakening was committed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), `OPEN`, not
  merged
- Base/head: `main` /
  `oap/077-agent-site-structure-semantics`
- Starting remote report head:
  `be6e40d540ab769edcdfb7d90f1bea7808eb9eb1`
- Implementation head SHA:
  `20c238909b7e7d0cc65894cdd93c4c29ace4b57`
- Parent of implementation:
  `be6e40d540ab769edcdfb7d90f1bea7808eb9eb1`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- New PR: no; existing PR amended: yes; merge/auto-merge: NO

## Changes made

- Changed migration 028 human Editor active-workspace acquisition to
  `pg_advisory_xact_lock_shared`.
- Changed migration 050 Agent capability and structural lifecycle acquisition
  to shared mode while retaining exclusive namespace-994 structural locking.
- Added pre-snapshot lifecycle-shared/structural-exclusive acquisition for
  Agent page/locale/navigation/redirect mutations and Editor structural
  permissions.
- Added a real PostgreSQL lock-contract test that inspects the installed
  function definitions and proves two connections can acquire the active
  lifecycle shared lock concurrently.
- Added the exact Alpine 3.23 `libcurl=8.22.0-r0` overlay and installed-version
  assertion to the official PostgreSQL 18.6 image; updated policy and package
  contract facts.
- Committed the exact strategy bytes for `077-p` and `oap/active` unchanged.

## Files changed

- `services/backend/src/slaif_agent_site/db/alembic/versions/028_001_human_editor_workspace_envelope.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/050_001_agent_locale_navigation.py`
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`
- `services/backend/src/slaif_agent_site/editor_api/database.py`
- `services/backend/tests/integration/test_render_preview_session_lock.py`
- `infra/postgres/Dockerfile`
- `supply-chain/policy.json`
- `tests/packaging/test_oci_contract.py`
- `docs/SUPPLY_CHAIN.md`
- exact strategy bytes: `oap/orders/077-p-repair-lifecycle-lock-and-postgres-scan.md`,
  `oap/active`

## Acceptance-criteria evidence

### Lifecycle lock repair

- Migration 028 `control.slaif_human_editor_workspace_assert(..., p_lock=true)`
  now uses lifecycle shared mode.
- Migration 050
  `control.slaif_agent_require_capability(uuid,text)` and
  `control.slaif_agent_structural_lock(uuid)` now use lifecycle shared mode
  before the namespace-994 exclusive structural key.
- Agent structural mutation types and Editor structural permissions acquire
  the same shared-then-exclusive order before reservation/validation reads.
- `test_active_workspace_lifecycle_lock_is_shared`: PASSED.
- Existing exclusive-lock Render/freeze wait tests remain green in the focused
  `test_render_preview_session_lock.py` run: 2 passed.

### Causal snapshot blocker

The temporary attempted proof used an actual query over locale, navigation,
redirect and page-resolution data, paused Render, launched public Agent page,
navigation and redirect mutations, awaited all three responses, and released
Render only after the awaited commits. The mutations did not reach durable
completion; the request responses became `SERVICE_UNAVAILABLE` after the
long-running wait. The attempted chronology was not retained as a passing test.

The pre-existing focused test still passes only because it releases Render
before awaiting the mutation results; it remains known false-positive evidence
and is not claimed for this order. The canonical companion, negative
`READ COMMITTED` control, exact post-tentative-locale cancellation, and full
causal pool/lifespan proof remain incomplete for this concrete technical
reason.

### Postgres security overlay

- Official base remained
  `docker.io/library/postgres:18.6-alpine3.23@sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f`.
- Independently observed amd64 base manifest:
  `sha256:8810a63e526404041442acb4d96b8d882dffd544df9c43f2ea59deac2004628f`.
- Alpine 3.23 standard repository candidate:
  `libcurl=8.22.0-r0`; Alpine 3.24 was also inspected but was not needed.
- Two reproducible Postgres builds completed. Image manifest-list digests:
  `sha256:b8e07c604019a8d2e3fa3f091a5933db5103f48790f0f19a3fde8602bdf8523f`
  and
  `sha256:28256d0aaa57d30dd2a47f70b73bdb1c8975d362ce5ea6edf61c9d15ee5deaa1`.
- Normalized reproducibility evidence: application files equal and package
  manifests equal.
- Complete run:
  `sh tools/supply_chain/run.sh /tmp/slaif-077p-supply-chain-evidence`
  ended `supply-chain-gate: OK evidence=/tmp/slaif-077p-supply-chain-evidence`.
- All six images: zero Critical; High review count 42. Postgres specifically:
  zero Critical, 3 High, 4 Medium, 1 Low, 3 Unknown.

## Local verification

- Supply-chain policy validation: PASSED.
- Targeted package/policy/evidence tests: 35 passed.
- Ruff check and format: PASSED.
- Direct lock-contract test: PASSED.
- Existing locale/race focused test: PASSED.
- Full backend integration run after the lock-mode change: 168 passed, 2
  failed. The two failures were
  `test_agent_final_dependency_matrix_and_two_connection_delete_races` and
  `test_editor_agent_structural_races_share_workspace_site_lock`; both exposed
  a 404 where the existing contract accepts 200/409. Focused reruns reproduced
  the structural-race 404.
- Focused causal snapshot attempt: BLOCKED with the exact
  `SERVICE_UNAVAILABLE` result described above.
- Earlier complete Python, Node, Compose, browser and Apache evidence from
  077-o remains valid for unchanged paths; the current supply-chain run also
  rebuilt all six images and passed its complete gate.

## GitHub CI / required checks

The implementation head `20c238909b7e7d0cc65894cdd93c4c29ace4b57` was pushed
before CI observation. The report-only child has not yet been pushed; no
current-head check is counted as pass here. The remote PR remained open and
unmerged at report preparation.

## Scope, safety, and completion boundary

- No secrets, capabilities, cookies, production systems/data, extra PR, merge,
  release or issue closure occurred.
- No dynamic `{slug}` collection-detail behavior, 078 composition/design/Puck,
  media/MCP/freeze implementation/review/promotion/source/sweep/076 work was
  added.
- No vulnerability exception, scanner suppression, severity override or
  required-check weakening was used.
- The strongest reason not to accept is the concrete causal proof failure and
  the two resulting structural race-contract regressions after changing the
  lifecycle mode. Objective 077-p / PR #74 can be declared complete only when
  public Agent/Editor commits durably complete during a real paused
  repeatable-read preview, the complete before/after and negative isolation
  proofs pass, post-cancellation/lifespan/tentative-locale evidence is green,
  the structural 404 regressions are resolved, all current checks are green,
  and strategy independently accepts the bounded scope. The coding agent is
  not authorized to merge.

No extra PR was created. No merge or auto-merge was performed.
