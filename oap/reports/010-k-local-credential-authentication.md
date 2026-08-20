# OAP Coding-Agent Report — 010-k

## Work order

- Identifier: `010-k`; work-order file: `oap/orders/010-k-local-credential-authentication.md`; numeric objective: `010`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Added the Control-only local credential boundary at migration head `011_001`. Local login input is bounded and secret-safe; active LOCAL candidates use the real fixed RFC 9106 LOW_MEMORY Argon2id verifier, all absent/disabled/OIDC/malformed denials use an immutable equal-cost dummy hash, and successful rehash uses a guarded compare-and-set without holding a database transaction over Argon2. No HTTP route or session issuance was added.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR [#15](https://github.com/ulfe-lmi/slaif-agent-site/pull/15); state: `OPEN`
- Base/head branches: `main` / `oap/010-installation-local-auth`
- Starting remote SHA: `c534cdec5ef44add7cf2b0f35e54eba7b1459e71`
- Implementation head SHA: `fb19554bc91fdab2966750cfce5ba7f6a1582b6e`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- Implementation commits pushed before report: `b7fe3a19ad0d2fb06d10f365de0fde6f8488f7e9`, `7e3d88d2a258b4fbe4fd324900299a51c18874db`, `fb19554bc91fdab2966750cfce5ba7f6a1582b6e`; report parent=implementation SHA
- New PR this turn: no; amended existing: yes; merge performed: NO

## Changes made

- Added deterministic `011_001_local_authentication` lookup and password-hash compare-and-set functions, owner/grant/drop symmetry, strict hash-shape checks, and Control-only privilege inventory.
- Added typed `LocalLoginRequest`, `LocalAuthenticationResult`, constant `LocalAuthenticationError`, fixed dummy hash, actual/dummy verification, safe rehash CAS, and concrete `ControlDatabase.authenticate_local_login`.
- Added focused unit/integration proof, updated PostgreSQL CI coverage for local authentication, and derived Compose fixture restoration from canonical packaged migration sources.
- Documented Argon2 cost, enumeration limitations, Control authority, and deliberate absence of HTTP login/session/rate-limit/audit/OIDC/MFA/UI.

## Files changed

- `.github/workflows/ci.yml`
- `services/backend/src/slaif_agent_site/db/alembic/versions/011_001_local_authentication.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/identity/{__init__.py,authentication.py,passwords.py}`
- `services/backend/src/slaif_agent_site/control_api/database.py`
- `services/backend/tests/integration/{test_local_authentication.py,test_control_database_integration.py,test_database_bootstrap.py}`
- `services/backend/tests/unit/{test_identity_authentication.py,test_control_database.py,test_foundation_contract.py}`
- `tools/check_repository.py`, `tools/compose/control_readiness.py`, `tests/repository/test_repository_policy.py`
- `docs/CONFIGURATION.md`, `docs/DATABASE_ROLES.md`, `docs/LOCAL_AUTHENTICATION.md`, `docs/OPERATIONS.md`, `migrations/alembic/README.md`
- `oap/orders/010-k-local-credential-authentication.md` and `oap/active` were committed unchanged as the activated transcript.

## Acceptance-criteria evidence

### Criterion 1

- `011_001` creates only owner-controlled `SECURITY DEFINER` functions with `search_path=pg_catalog`, PUBLIC revoke, exact `slaif_control` execute, no direct relation grant; integration proves runtime/scheduler denial.

### Criterion 2

- Actual and dummy Argon2 paths are executable and spied in unit tests; unknown and wrong credentials return one constant `Local login failed.` error without hash/status detail.

### Criterion 3

- Valid credentials return only UUID/normalized username/rehash flag; rehash CAS is guarded by UUID, LOCAL, ACTIVE, and exact old hash. Login rehash hashing bypasses account-creation policy and no plaintext reaches SQL.

### Criterion 4

- Focused integration covers actual success, wrong/unknown denial, control-only function access, database bootstrap, and cancellation/negative boundaries inherited from the existing session/control suites; failed paths issue no session.

### Criterion 5

- Local bootstrap/auth/control integration and PostgreSQL CI 14–18 passed; Compose and edge packaging passed at packaged head `011_001`.

### Criterion 6

- No HTTP routes, session issuance, cookies, rate limiting, audit persistence, UI, OIDC, MFA, dependencies, or unrelated migrations were added.

### Criterion 7

- Exactly PR #15 was amended; final implementation CI/CodeQL are green; no workflow rerun, extra PR, merge, or auto-merge was performed.

## Local verification

- `uv run --frozen pytest -q services/backend/tests/integration/test_database_bootstrap.py services/backend/tests/integration/test_local_identity.py`: PARTIAL — 29 passed, one pre-existing out-of-scope local-identity relation-list expectation failed after the packaged session relation; no source change was made to that out-of-scope test.
- `uv run --frozen pytest -q services/backend/tests/integration/test_local_authentication.py`: PASSED — 2 passed (including after final hash-shape correction)
- `uv run --frozen pytest -q services/backend/tests/integration/test_control_database_integration.py`: PASSED — 3 passed
- `uv run --frozen pytest -q services/backend/tests/unit/test_foundation_contract.py services/backend/tests/unit/test_control_database.py services/backend/tests/unit/test_identity_authentication.py services/backend/tests/unit/test_identity_password.py tests/packaging/test_compose_policy.py`: PASSED — 56 passed, 8 subtests
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED — 26 tests
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 52 tests
- `uv run --frozen ruff check services/backend tests/repository tests/packaging tests/supply_chain tools migrations`: PASSED
- `uv run --frozen ruff format --check services/backend tests/repository tests/packaging tests/supply_chain tools migrations`: PASSED
- `uv run --frozen mypy`: PASSED — 84 source files
- `python -m compileall -q tools tests/repository services/backend/src/slaif_agent_site`: PASSED
- `python tools/check_repository.py`: PASSED
- `npx --yes markdownlint-cli2@0.23.2 --no-globs docs/LOCAL_AUTHENTICATION.md docs/DATABASE_ROLES.md docs/CONFIGURATION.md docs/OPERATIONS.md migrations/alembic/README.md oap/orders/010-k-local-credential-authentication.md`: PASSED — 0 issues
- `git diff --check`: PASSED

## GitHub CI / required checks

- Final implementation-head state observed: all completed checks SUCCESS.
- CI run `32406241459`: SUCCESS — Node contracts; Repository policy; Dependency review; Markdown; Foundation PostgreSQL 14–18; Python 3.12/3.13/3.14 quality/package; Compose and edge packaging; Supply-chain evidence; Mermaid.
- CodeQL run `32406241445`: SUCCESS.
- All required green at drafting: yes.
- Earlier initial generation `32405171872` failed on clean-checkout fixture import plus protocol/format issues; corrective generation `32405736565` passed fixture/format but exposed the adapter-protocol mypy issue. These were diagnosed and corrected in scope; no workflow rerun was invoked.
- Report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- No production systems, credentials, or new dependencies were accessed or installed. Disposable local PostgreSQL and existing frozen environment were used.

## Documentation

- Updated local-authentication, database-role, configuration, operations, and migration-head documentation honestly; no architecture/security boundary was weakened.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no; production systems accessed: no.
- Required tests skipped/not run: no for in-scope focused evidence; one out-of-scope local-identity expectation was observed failing and left unchanged.
- Scope deviation: no; extra corrective commits were limited to CI-exposed in-scope defects.
- Extra objective PR: NO; coding-agent merge: NO.
- Activated order/active edited: NO (committed exact strategic bytes).
- Report commit changes only this report: yes.

## Known limitations / blockers

- HTTP login/session issuance, rate limiting, audit, OIDC, MFA, and UI remain deliberately deferred.
- The existing out-of-scope `test_local_identity.py` relation-list expectation should be reconciled by a future scoped order if desired; CI does not run that file in this round.

## Recommended strategic follow-up

- Strategy may independently review and accept/merge PR #15; coding agent took no merge action.
