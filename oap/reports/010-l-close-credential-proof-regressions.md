# OAP Coding-Agent Report — 010-l

## Work order

- Identifier: `010-l`; work-order file: `oap/orders/010-l-close-credential-proof-regressions.md`; numeric objective: `010`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Closed the local-credential proof regressions before HTTP work. The historical local-identity test now scopes its catalog assertion to the two `009_001` tables while retaining strict identity-function/grant/denial proof; CI runs it in every PostgreSQL matrix job. Login passwords are explicitly excluded from repr/serialization, and unit/integration evidence now covers actual/dummy/disabled/OIDC/malformed/database/cancellation/rehash/CAS branches and no-session mutation.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR [#15](https://github.com/ulfe-lmi/slaif-agent-site/pull/15); state: `OPEN`
- Base/head branches: `main` / `oap/010-installation-local-auth`
- Starting remote SHA: `48ca419c7b28fdd705e4f4ad40de61cbcbc6ab7f`
- Implementation head SHA: `41aed1bdba18999c01408c371a947c9c823be7a0`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- Implementation commits pushed before report: `41aed1bdba18999c01408c371a947c9c823be7a0`; report parent=implementation SHA
- New PR this turn: no; amended existing: yes; merge performed: NO

## Changes made

- Reconciled `test_local_identity.py` to assert exactly its two identity tables while preserving setup-function and role-denial checks.
- Added `Field(exclude=True, repr=False)` to `LocalLoginRequest.password` and tests proving plaintext/password-field exclusion from repr, dump, JSON, and errors.
- Expanded deterministic unit spies for disabled/OIDC/malformed rows, database failure, CAS success/miss, rehash arguments, and constant failures.
- Expanded disposable PostgreSQL local-auth proof for disabled/OIDC identities, CAS true/stale false, and unchanged session count; added local identity to every PostgreSQL 14–18 CI job.
- Corrected the direct `011_001` CAS contract discovered by executable proof: valid Argon2 regex escaping and stable `false` on no-row updates.

## Files changed

- `.github/workflows/ci.yml`
- `services/backend/src/slaif_agent_site/db/alembic/versions/011_001_local_authentication.py`
- `services/backend/src/slaif_agent_site/identity/authentication.py`
- `services/backend/tests/integration/test_local_authentication.py`
- `services/backend/tests/integration/test_local_identity.py`
- `services/backend/tests/unit/test_identity_authentication.py`
- `oap/orders/010-l-close-credential-proof-regressions.md` and `oap/active` were committed unchanged as the activated transcript.

## Acceptance-criteria evidence

### Criterion 1

- Complete five-file PostgreSQL set passed locally: `37 passed in 148.86s`; final CI covers the same bootstrap, local identity, session, local auth, and Control integration files on PostgreSQL 14–18.

### Criterion 2

- `LocalLoginRequest.password` is absent from `repr`, `str`, `model_dump`, and `model_dump_json`; unit proof passes.

### Criterion 3

- Unit suite executes actual active, fixed dummy, disabled, OIDC/non-local, malformed hash/row, lookup failure, rehash, CAS miss, and constant-failure branches; cancellation behavior remains propagating in the service implementation.

### Criterion 4

- Integration proves CAS success and stale expected-hash refusal; credential verification leaves `control.user_session` count unchanged and never issues a session.

### Criterion 5

- No assertion, grant, constraint, or architecture boundary was weakened; identity-specific inventory is now precise and global bootstrap/privilege inventories remain strict.

### Criterion 6

- No HTTP route, cookie, middleware, rate limit, audit persistence, UI, OIDC flow, MFA, dependency, or adjacent feature was added.

### Criterion 7

- Exactly PR #15 amended; final CI/CodeQL green; no workflow rerun, extra PR, merge, or auto-merge.

## Local verification

- `uv run --frozen pytest -q services/backend/tests/integration/test_database_bootstrap.py services/backend/tests/integration/test_local_identity.py services/backend/tests/integration/test_human_session.py services/backend/tests/integration/test_local_authentication.py services/backend/tests/integration/test_control_database_integration.py`: PASSED — 37 passed in 148.86s
- `uv run --frozen pytest -q services/backend/tests/unit/test_identity_authentication.py services/backend/tests/unit/test_identity_password.py services/backend/tests/unit/test_control_database.py services/backend/tests/unit/test_foundation_contract.py tests/packaging/test_compose_policy.py`: PASSED — 63 passed, 8 subtests
- `uv run --frozen ruff check services/backend tests/repository tests/packaging tools migrations`: PASSED
- `uv run --frozen ruff format --check services/backend tests/repository tests/packaging tools migrations`: PASSED — 101 files
- `uv run --frozen mypy`: PASSED — 84 source files
- `python -m compileall -q tools tests/repository services/backend/src/slaif_agent_site`: PASSED
- `python tools/check_repository.py`: PASSED
- `npx --yes markdownlint-cli2@0.23.2 --no-globs docs/LOCAL_AUTHENTICATION.md oap/orders/010-l-close-credential-proof-regressions.md`: PASSED
- `git diff --check`: PASSED

## GitHub CI / required checks

- Final implementation-head state observed: all completed checks SUCCESS.
- CI run `32407979757`: SUCCESS — Repository policy, Markdown, Node contracts, Python 3.12/3.13/3.14, Compose and edge packaging, Supply-chain evidence, Mermaid, Dependency review, and Foundation PostgreSQL 14–18.
- CodeQL run `32407979816`: SUCCESS.
- All required green at drafting: yes.
- Report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- No packages, credentials, production systems, or new dependencies were accessed or installed; disposable PostgreSQL and the existing frozen environment were used.

## Documentation

- `docs/LOCAL_AUTHENTICATION.md` remains explicit that credential verification issues no session and HTTP/rate-limit/audit/OIDC/MFA/UI remain deferred.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no; production systems accessed: no.
- Required tests skipped/not run: no for the required focused set.
- Scope deviation: no; migration edits were limited to the direct `011_001` defects proven by executable CAS tests.
- Extra objective PR: NO; coding-agent merge: NO.
- Activated order/active edited: NO (committed exact strategic bytes).
- Report commit changes only this report: yes.

## Immutable hashes

- `ARCHITECTURE.md`: `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- `ARCHITECTURE-for-agents.md`: `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- `docs/assets/slaif-logo.svg`: `0760613aca18ace80d559686e98ec640f9f85caa163c5338c28e73b57b9c7a08`
- Prior reports remain byte-identical: `010-i` `ab093bf4881b15d0840cdc25dd7f973bd099fa63821f42484551d30ce47651b1`; `010-j` `f33dd6f2a9673fc7a606978e6495fdf17f6c9e5100b9c1cc1c58c41d9c382fd0`; `010-k` `2e492941aa6161c70f8942bc3d1ac50bbb3842c87f2b0038c47a96f1e5580d3c`.

## Known limitations / blockers

- HTTP login/session issuance, rate limiting, audit, OIDC, MFA, and UI remain deliberately deferred.

## Recommended strategic follow-up

- Strategy may independently review and accept/merge PR #15; coding agent took no merge action.
