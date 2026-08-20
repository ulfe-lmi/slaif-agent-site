# OAP Coding-Agent Report — 010-f

## Work order

- Identifier: `010-f`
- Work-order file: `oap/orders/010-f-repair-session-proof-and-ci.md`
- Numeric objective: `010`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Repaired the 010-e session slice in the existing PR. Migration and privilege
inventories now include the session relation and four lifecycle functions.
Human-session semantics now expose separate safe authentication,
CSRF-bound state-changing authentication, and CSRF-bound idempotent revoke.
The service runs constant-time digest comparison on the real authorization
paths inside transaction scopes while PostgreSQL performs the locked lookup and
recheck. Tests and documentation were extended for substitution, expiry,
recent-auth, touch, revoke, concurrency, cancellation, and role-denial cases.

The two permitted focused PostgreSQL session invocations were consumed. The
first exposed a stale owner-inspection connection; the second exposed a test
fixture timestamp-order violation. Both were diagnosed and corrected, but the
order forbids a third focused invocation. The fresh lifecycle command completed
after its tool output was truncated, so its final result was not captured as
local evidence. GitHub PostgreSQL 14–18 all passed. Compose remains failed in
its existing migration-mismatch fixture timeout, so this round is PARTIAL.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: `#15` — <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- State: `OPEN`, non-draft, `MERGEABLE`, merge state `UNSTABLE`
- Base/head: `main` / `oap/010-installation-local-auth`
- Starting remote `main` SHA: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Starting remote PR/report head: `ac246252d7bdc2c09af299732cfd045befa2d305`
- Implementation head SHA: `238ccf060d7c863c4e55859a1b7b1dc8be23e8cc`
- Report publication commit: SELF
- No merge, force-push, auto-merge, close, or extra PR performed.

## Changes made

- Added the safe `slaif_authenticate_human_session` function and Control grant.
- Expanded state-changing resolve to return stored defense digests while its
  row lock remains held; the service compares both session and CSRF digests
  with `secrets.compare_digest` before returning context.
- Made revoke a locked, CSRF-aware owner function that returns defense digests,
  prevents wrong-CSRF mutation, and remains externally idempotent for a valid
  revoked session.
- Updated `HumanSessionService` with explicit `authenticate`,
  `authenticate_state_changing`, and `revoke(token, csrf_token)` methods.
- Repaired strict relation/function inventories and added deterministic
  integration/unit evidence plus safe-vs-state-changing documentation.

## Files changed

- `oap/active`
- `oap/orders/010-f-repair-session-proof-and-ci.md`
- `services/backend/src/slaif_agent_site/db/alembic/versions/010_001_human_session.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/identity/sessions.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/integration/test_human_session.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `services/backend/tests/unit/test_sessions.py`
- `docs/LOCAL_AUTHENTICATION.md`
- `docs/DATABASE_ROLES.md`

## Acceptance-criteria evidence

1. **Migration/privilege inventories:** strict local relation inventory was
   repaired; GitHub Foundation PostgreSQL 14, 15, 16, 17, and 18 all passed.
   The local lifecycle command was run once but its final result was not
   captured after tool-output truncation.
2. **Constant-time authorization:** unit spy test passed and observed calls on
   safe authentication, CSRF-bound authentication, and revoke; production
   service methods call `constant_time_digest_equal` inside transactions.
3. **CSRF split:** safe `authenticate(token)` accepts no CSRF argument;
   `authenticate_state_changing(token, csrf)` and `revoke(token, csrf)` require
   the bound proof. Unit and focused integration assertions cover missing,
   wrong, and cross-session CSRF.
4. **Negative/expiry/race evidence:** executable integration coverage includes
   malformed/unknown/wrong secrets, disabled user, idle/absolute expiry,
   recent-auth transition, touch threshold, wrong-CSRF revoke, concurrent
   resolve/revoke, cancellation under a row lock, and role denial. The two
   focused runs failed before reaching all assertions due the diagnosed test
   defects; no successful local end-to-end session run is claimed.
5. **No revival/overextension:** migration constraints and test assertions
   cover absolute expiry, monotonic touch, immutable recent-auth, and terminal
   revoke behavior; local post-repair integration proof remains pending.
6. **Scope:** no adjacent product feature, dependency, route, UI, edge,
   Compose, OIDC, MFA, site, membership, capability, or publication feature
   was introduced.
7. **PR/transcript:** exactly PR #15 was amended; one implementation commit
   was pushed; no workflow rerun was used; report publication follows below.

## Local verification

- `uv run --frozen ruff format ...`: PASSED — affected files formatted.
- `uv run --frozen ruff check ...`: PASSED.
- `uv run --frozen mypy`: PASSED — no issues in 80 files.
- `uv run --frozen pytest -q services/backend/tests/unit/test_sessions.py services/backend/tests/unit/test_foundation_contract.py services/backend/tests/unit/test_control_database.py`: PASSED — 37 tests.
- `python -m compileall -q tools tests/repository services/backend/src/slaif_agent_site`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 50 tests.
- `python tools/check_repository.py`: PASSED.
- `npx --yes markdownlint-cli2@0.23.2 --no-globs docs/LOCAL_AUTHENTICATION.md docs/DATABASE_ROLES.md docs/OPERATIONS.md migrations/alembic/README.md`: PASSED — 4 files.
- `git diff --check`: PASSED.
- `uv run --frozen pytest -q services/backend/tests/integration/test_database_bootstrap.py services/backend/tests/integration/test_control_database_integration.py`: RUN ONCE; final tool result was not captured after output truncation, so NOT VERIFIED locally.
- Focused `test_human_session.py`: exactly 2 post-repair invocations, both FAILED before complete assertions; no third attempt.
- Broad local Compose, supply-chain/image, Node, browser, and full DB matrix: NOT RUN per order.

## GitHub CI / required checks

Implementation-head CI run `32396499223` and CodeQL run `32396499152` were the
single new generation; no reruns:

- SUCCESS: Python 3.12 quality/package; Python 3.13 quality/package; Python
  3.14 quality/package; Node contracts; Repository policy; Markdown; Mermaid;
  Dependency review; Supply-chain evidence; Foundation PostgreSQL 14, 15, 16,
  17, and 18; CodeQL.
- FAILURE: Compose and edge packaging — `control-readiness-fixture` timed out
  during the existing `migration-mismatch` stage after the stack became
  healthy (`control-readiness-fixture: FAILED ... reason=timeout`).
- All jobs completed; no pending or cancelled job is presented as passing.

## Documentation and setup

No new dependency or package was installed. Documentation now distinguishes
safe reads from CSRF-protected state changes, documents constant-time digest
checks and transaction locking, and retains the explicit statement that no
HTTP route, middleware, cookie emission, UI, OIDC, MFA, or security-event
store exists yet.

## Hashes and immutable protocol evidence

- Activated order SHA256: `d4afe4c92a5c5ec0589cb0e44e15cd99eb5210bfe20392829ea4a75bd4c64e72`
- Root `AGENTS.md`: `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`: `ffa3e2bf7998c1274543dc76f22f4b19655d2d209fdbde2a020eff8fa47d83b8`
- `ARCHITECTURE-for-agents.md`: `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Full `ARCHITECTURE.md` source hash (not loaded): `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- Prior 010-e implementation/report preserved: implementation
  `1d74623e069515bb9a8574ed0bf58d64a77fb9c2`, report publication
  `ac246252d7bdc2c09af299732cfd045befa2d305`.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production systems/credentials/secrets/capability tokens/cookies/private
  URLs accessed or committed: NO.
- Required tests skipped/not run: lifecycle local result unverified due tool
  truncation; complete session proof unverified because the order capped the
  two failed focused attempts; broad suites explicitly prohibited.
- Extra objective PR: NO. Coding-agent merge/acceptance: NO.
- Activated order and active pointer edited: NO; exact strategic bytes were
  committed unchanged.
- Final report commit changes only this report: YES; its first parent is the
  implementation SHA above.

## Limitation / strategic follow-up

Compose’s migration-mismatch readiness fixture still times out despite all
PostgreSQL matrix jobs passing. A continuation should investigate that existing
Compose fixture and rerun the focused session test after the two diagnosed test
fixes; this round deliberately did not exceed its database or CI budgets.
