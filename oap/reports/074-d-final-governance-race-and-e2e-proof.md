# OAP implementation report — 074-d

- ID/order: `074-d-final-governance-race-and-e2e-proof`
- Mode: `AMENDED_EXISTING_PR`
- Result: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#70](https://github.com/ulfe-lmi/slaif-agent-site/pull/70) (OPEN, unmerged)
- Base: `main`
- Starting report head: `29b7c74d3d2021ece8cf6c2d05db6e1828bde2d1`
- Implementation SHA: `4b508c0ab39971077d0e45f16ac5a6710f975adb`
- Report publication commit: SELF

## Corrections delivered

- Completed the final 039 workspace and capability authority model. Workspace
  listing now permits the creator, an active Platform Administrator, or an
  active site member with `workspace:read-all`; capability list/get/create/
  revoke recheck active account, site, workspace, delegator membership,
  current delegation ceiling, and their named permission at the exact bound
  site/workspace. Foreign and inactive identifiers fail without existence
  leakage. Audit rows use the authenticated Site Owner governor actor.
- Replaced the 039 COW site guard with an immediate semantic-DML recheck of
  active session binding, account/site/workspace state, delegator membership,
  current ceiling, and Platform Administrator authority while preserving the
  trusted UUID GUCs, site binding, idempotency behavior, and zero transaction
  residue. The integration proof deactivates the delegator before the
  semantic wrapper and observes the required denial.
- Made the downgrade chain explicit and reversible. The targeted
  `039 -> 038 -> 037` test verifies 039 additions are absent at 037, restores
  the exact revision-037 authentication function/body/owner, PUBLIC revoke,
  and Agent grant, then upgrades and reconciles back to 039 with the expected
  migration/readiness truth.
- Added decisive lifecycle coverage for omitted versus explicit-empty/narrow
  scopes, duplicate and above-ceiling rejection, all four preset ceilings,
  distinct creator/governor authority, missing/inactive/foreign denial, CSRF,
  and audit actor identity. Public Agent-session E2E titles are project-unique
  and revoke/status assertions are scoped to the created session, eliminating
  cross-project desktop/phone races. L1 and L4 flows cover exact scopes,
  constraints, dismiss/reload rediscovery, revoke, 401, restart recovery, and
  token absence from browser-visible state.

## Correction to 074-c report

The 074-c report overstated completion: its claims that all four presets,
membership authority, restart evidence, and downgrade-to-037 proof were
complete were not supported by the required final permissioned-list,
semantic-COW recheck, targeted downgrade, and paired public desktop/phone
evidence. This 074-d report makes those claims only after the repairs and
evidence recorded here; the earlier report is unchanged.

## Exact changed surfaces

`services/backend/src/slaif_agent_site/db/alembic/versions/038_001_human_agent_session_control_plane.py`,
`services/backend/src/slaif_agent_site/db/alembic/versions/039_001_complete_session_authority_and_proof.py`,
`services/backend/tests/integration/test_human_agent_session_control.py`,
`tests/e2e/agent-sessions.spec.ts`, `tools/compose/e2e.sh`, and the immutable
074-d order/active transcript.

## Evidence

- Focused Agent-session integration tests: 3 passed, including the distinct
  Site Architect/Site Owner authority proof, semantic COW recheck denial,
  exact scope/preset/ceiling cases, audit actor, CSRF/foreign denial, and
  `039 -> 038 -> 037 -> 039` migration round trip.
- Local Python gates passed: frozen lock/sync, Ruff check and format, mypy,
  491 unit/repository tests plus 26 subtests, 114 integration tests,
  reproducibility/evidence tests (20), repository policy tests (54), Mermaid
  rendering (16 diagrams), Markdown lint (292 files), all ten process
  `--check` smoke commands, and `uv build` source/wheel artifacts.
- Local Node gates passed on Node `v24.14.1` and pnpm `11.22.0`: lint,
  format-check, typecheck, tests, build, and license inventory. Playwright
  collection includes both Agent-session projects and two contracts each.
- GitHub required check-runs on implementation SHA `4b508c0` all completed
  successfully: Repository policy, language detection, Node contracts, Python
  3.12/3.13/3.14 quality/package, PostgreSQL 14/15/16/17/18, Compose and edge
  packaging, Supply-chain evidence, Markdown, Mermaid, Dependency review,
  and CodeQL (including JavaScript/TypeScript, Python, and Actions analyses).
  Compose and edge packaging passed the public NGINX desktop/phone Agent
  session contracts and restart/revocation recovery.

## Scope and safety confirmations

- Only 074-d was executed. `oap/active` and the immutable order bytes were
  committed unchanged with the implementation. Pushed implementation commits
  are `af9fc5f` and `4b508c0`; this report is exactly one report-only child.
- PR #70 was amended; no second objective PR, merge, auto-merge, release,
  hosted service, dependency, production access, architecture/constitution,
  or prior-report edit occurred. No checks were skipped, pending, cancelled,
  or treated as pass without completion.
- No real secret, capability plaintext, cookie, private URL, credential, or
  retained token was committed or printed. The coding agent did not merge the
  PR and selected no subsequent order.
