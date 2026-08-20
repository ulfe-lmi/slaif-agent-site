# OAP Coding-Agent Report — 010-g

## Work order

- Identifier: `010-g`
- Work-order file: `oap/orders/010-g-close-session-authorization-proof.md`
- Numeric objective: `010`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Implemented the requested transaction-order repair in the existing session
foundation: Control now locks and inspects by public ID without mutation, the
application performs constant-time session/CSRF comparisons, and separate
Control-only finalizers recheck the digests and state before touch or authority.
The safe/state-changing/revoke service methods are explicit. The PostgreSQL
matrix command now includes `test_human_session.py`, and Compose recovery now
restores migration head `010_001`.

Static and unit evidence passed. The two permitted post-fix focused session
invocations reached the database and exposed timestamp fixture defects; both
were diagnosed and corrected, but no third attempt was permitted. The strict
bootstrap invocation and all five GitHub PostgreSQL jobs then exposed a
remaining downgrade defect: the migration omitted dropping the revised revoke
function, so rebuild fails with `DuplicateFunctionError`. This report is
truthfully `PARTIAL`; a continuation must add the missing downgrade drop and
rerun the bounded evidence.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: `#15` — <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- State: `OPEN`, non-draft, `MERGEABLE`, merge state `UNSTABLE`
- Base/head: `main` / `oap/010-installation-local-auth`
- Starting remote PR/report head: `3818eb071151177d4c8a1e2e8130c3b459916e84`
- Implementation head SHA: `e133a090b7271983679ce5369f9c4155bdb2c89a`
- Report publication commit: SELF
- No merge, force-push, auto-merge, close, or extra PR performed.

## Changes made

- Added locked `slaif_inspect_human_session` returning only Control-visible
  defense material and session state.
- Split mutation paths into `slaif_finalize_human_session` and
  `slaif_finalize_state_changing_human_session`; each rechecks row identity,
  digest, active user, revocation, expiry, and policy before touching.
- Made `slaif_revoke_human_session` a CSRF-bound finalization function with
  active-user/expiry checks and idempotent result.
- Updated `HumanSessionService` to compare fixed-size digests after inspect and
  before any finalizer call; unknown IDs execute dummy constant-time compares.
- Added unit call-order/no-finalize spies and repaired the focused fixture
  timestamp ordering.
- Added the session integration test to every PostgreSQL 14–18 CI job and
  corrected Compose readiness recovery to `010_001`.

## Files changed

- `.github/workflows/ci.yml`
- `oap/active`
- `oap/orders/010-g-close-session-authorization-proof.md`
- `services/backend/src/slaif_agent_site/db/alembic/versions/010_001_human_session.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/identity/sessions.py`
- `services/backend/tests/integration/test_human_session.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `services/backend/tests/unit/test_sessions.py`
- `tools/compose/control_readiness.py`
- `docs/LOCAL_AUTHENTICATION.md`
- `docs/DATABASE_ROLES.md`

## Acceptance-criteria evidence

1. **Transaction order:** unit spy passed and proves inspect → constant-time
   comparison → no finalizer on failed/unknown; valid paths call finalizers
   after comparisons. PostgreSQL execution is not complete because migration
   rebuild fails on the omitted revoke-function downgrade.
2. **Focused session proof:** exactly two post-fix invocations were made. The
   first failed on a `created_at <= last_seen_at` fixture violation; the second
   failed at the idle/touch boundary because the fixture aged `last_seen_at`
   to the two-second timeout. Both fixture defects are corrected locally, but
   no third run was made.
3. **CI session matrix:** workflow includes the session test for PostgreSQL
   14–18, but all five jobs fail before session execution with the same
   `DuplicateFunctionError` during migration rebuild.
4. **Compose recovery:** source now restores `010_001`; GitHub Compose and edge
   packaging passed in the single generation. The targeted local smoke was
   blocked during setup by the fixture project-name guard/Docker socket
   permission and was not rerun.
5. **Strict inventories:** static inventory/unit tests passed; strict local
   bootstrap command failed at rebuild due the missing downgrade drop, matching
   the CI diagnosis.

## Local verification

- `uv run --frozen ruff format --check ...`: PASSED.
- `uv run --frozen ruff check ...`: PASSED.
- `uv run --frozen mypy`: PASSED — 80 files.
- `uv run --frozen pytest -q services/backend/tests/unit/test_sessions.py services/backend/tests/unit/test_foundation_contract.py services/backend/tests/unit/test_control_database.py tests/packaging/test_compose_policy.py`: PASSED — 50 tests, 8 subtests.
- `python -m compileall -q tools tests/repository services/backend/src/slaif_agent_site`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 50 tests.
- `python tools/check_repository.py`: PASSED.
- Explicit changed-document Markdownlint with `--no-globs`: PASSED — 4 files.
- `git diff --check`: PASSED.
- `uv run --frozen pytest -q services/backend/tests/integration/test_human_session.py`: exactly 2 post-fix attempts; both FAILED on diagnosed timestamp fixtures; no third attempt.
- `uv run --frozen pytest -q services/backend/tests/integration/test_database_bootstrap.py`: FAILED during rebuild with duplicate `slaif_revoke_human_session`; final output was truncated, and CI provides the authoritative diagnosis.
- `python tools/compose/control_readiness.py ...`: BLOCKED at setup; Docker socket permission and local project-name guard prevented the smoke.
- Broad local supply-chain/image, Node, browser, and full DB matrix: NOT RUN per order.

## GitHub CI / required checks

Single authorized generation: CI `32398206626`, CodeQL `32398206184`; no
workflow rerun.

- SUCCESS: Python 3.12/3.13/3.14 quality/package, Node contracts, Repository
  policy, Markdown, Mermaid, Dependency review, Supply-chain evidence, Compose
  and edge packaging, and CodeQL.
- FAILURE: Foundation PostgreSQL 14, 15, 16, 17, and 18. Each reports
  `DuplicateFunctionError: function "slaif_revoke_human_session" already exists
  with same argument types` during migration rebuild, followed by the session
  test’s unavailable-session error.
- All jobs completed; no pending/cancelled state is presented as passing.

## Documentation and setup

No dependencies or packages were added. Documentation describes the inspect,
constant-time comparison, finalizer, CSRF split, and continued absence of HTTP
routes, middleware, cookie emission, UI, OIDC, MFA, security events, sites,
memberships, capabilities, and publication.

## Hashes and protocol evidence

- Activated order SHA256: `637aaca703e2be9e7bb18b2de7510a08da017417e3d45fb0692f8215034c4d19`
- Root `AGENTS.md`: `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`: `ffa3e2bf7998c1274543dc76f22f4b19655d2d209fdbde2a020eff8fa47d83b8`
- `ARCHITECTURE-for-agents.md`: `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Full `ARCHITECTURE.md` source hash (not loaded): `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- Prior 010-f implementation/report preserved: implementation
  `238ccf060d7c863c4e55859a1b7b1dc8be23e8cc`, report
  `3818eb071151177d4c8a1e2e8130c3b459916e84`.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production systems, credentials, secrets, capability tokens, cookies, and
  private URLs: NOT accessed or committed.
- Required tests not passing: focused session proof and PostgreSQL matrix are
  explicitly recorded; no retries/reruns were made.
- Extra objective PR: NO. Coding-agent merge/acceptance: NO.
- Activated order and active pointer content: unchanged and committed.
- Final report commit: changes only this report and has implementation SHA as
  its first parent.

## Limitation / strategic follow-up

The next continuation must add the missing
`DROP FUNCTION control.slaif_revoke_human_session(text, bytea, bytea)` to the
010-001 downgrade, then rerun the two focused session attempts and one strict
matrix/lifecycle proof. No further implementation or workflow rerun was
authorized in this round.
