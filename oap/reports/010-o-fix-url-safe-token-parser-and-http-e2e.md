# OAP Coding-Agent Report — 010-o

## Work order

- Identifier: `010-o`; work-order file:
  `oap/orders/010-o-fix-url-safe-token-parser-and-http-e2e.md`; numeric
  objective: `010`
- PR mode: `AMENDED_EXISTING_PR`

## Status

BLOCKED

## Executive summary

Completed and verified the authorized parser, service, unit, PostgreSQL-ASGI,
and CI-selection changes locally. The new real-app flow passes, as do all 203
unit tests and the required six-file PostgreSQL set (39 tests). The unchanged
mandatory mypy command deterministically rejects the required unit and
integration files because both are named `test_control_auth_http.py` and the
test directories are not Python packages. Every clean resolution requires a
path outside 010-o's exact allowed scope. No exclusion or weakened type gate
was introduced, and the known-failing affected gate was not pushed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#15](https://github.com/ulfe-lmi/slaif-agent-site/pull/15); state: `OPEN`
- Base/head branches: `main` / `oap/010-installation-local-auth`
- Starting remote SHA: `372ff15139eea2f5dcda5b978bf07c62ec3d51b8`
- Implementation head SHA: `6e2b7d955aaf2dca0f480efe2151ab7764c23887`
- Report publication commit: SELF
- Implementation commit pushed before report:
  `6e2b7d955aaf2dca0f480efe2151ab7764c23887`; report
  parent=implementation SHA
- The implementation commit contains only the byte-identical activated order
  and pointer. Verified product/test/workflow changes remain preserved locally
  and uncommitted because pushing them would knowingly fail the required mypy
  gate.
- New PR this turn: no; amended existing: yes; merge performed: NO;
  auto-merge enabled: NO; workflow rerun: NO

## Locally completed changes

- `identity/sessions.py`: bounded session parsing with `split("_", 3)` and CSRF
  parsing with `split("_", 2)`, preserving the complete URL-safe secret while
  retaining all existing grammar/decode validation.
- `identity/sessions.py`: require a successful revoke result for a previously
  active session, while preserving correct replay for an already-revoked
  credential. Actual PostgreSQL proof found that the previous service ignored
  `revoked=false` for an expired session.
- `control_api/database.py`: narrow constructor-only injectable session entropy
  function; immutable production default remains `secrets.token_bytes`, with
  the existing exact 32-byte validation in `HumanSessionService`.
- `test_sessions.py`: deterministic round-trip corpus with underscore at the
  first, middle, and last valid encoded positions; hyphen; both URL-safe
  characters; and `b"\xff" * 32`, plus separator/padding/whitespace/trailing
  negative cases.
- New actual PostgreSQL-backed `test_control_auth_http.py`: setup-token status,
  concurrent setup, exactly one administrator/session, secret absence,
  underscore-bearing issuance, session inspection, denied login state,
  fresh login, cross/missing/duplicate CSRF, logout/replay, revoked/expired
  inspection/logout, disabled login, and exact row-state assertions through the
  actual FastAPI app, ControlDatabase, Argon2, and session functions.
- `.github/workflows/ci.yml`: adds the sixth HTTP integration file to the
  unchanged PostgreSQL 14–18 job while preserving exactly 20 check names.

## Acceptance-criteria evidence

- Criteria 1, 2, 4, and 5 pass locally through the parser corpus, strict unit
  suite, and actual PostgreSQL/ASGI flow. Production randomness, migration,
  role, cookie/header, no-store/noindex, CSRF, and 204 behavior remain intact.
- Criterion 3 passes locally: all six required integration files complete with
  39 passing tests. It cannot be published to five-version CI without knowingly
  publishing the mypy duplicate-module failure.
- Criterion 6 passes locally: no UI, edge, dependency, migration, grant, or
  adjacent feature was added.
- Criterion 7 is blocked: exactly PR #15 was amended and no workflow was rerun,
  but the complete local implementation cannot become a green report head under
  the current allowed paths.

## Exact blocker

The required command reports:

```text
services/backend/tests/unit/test_control_auth_http.py: error: Duplicate module
named "test_control_auth_http" (also at
"services/backend/tests/integration/test_control_auth_http.py")
```

Mypy identifies adding `__init__.py`, changing package-base configuration, or
excluding one file as resolution classes. The first two require unlisted paths
(`services/backend/tests/integration/__init__.py` and/or configuration); the
third would weaken mandatory coverage. Renaming the strategically required
integration file would violate the work order. Strategic authorization of the
minimal package marker is required.

## Local verification

- Parser/session/database/HTTP unit selection: PASSED — 50 passed in 0.93
  seconds.
- Complete backend unit suite: PASSED — 203 passed in 11.58 seconds.
- New actual PostgreSQL HTTP file alone after concrete assertion and fixture
  timestamp corrections: PASSED — one passed in 4.20 seconds.
- Complete required six-file disposable PostgreSQL set: PASSED — 39 passed in
  149.82 seconds.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 98 files.
- `python -m compileall -q services/backend/src services/backend/tests tools
  tests/repository`: PASSED.
- `python tools/check_repository.py`: PASSED.
- `git diff --check`: PASSED.
- `uv run --frozen mypy`: FAILED only with the duplicate module diagnostic
  above. A diagnostic run excluding the pre-existing unit basename passed all
  other 87 source files; that exclusion was not committed or proposed as a
  solution.
- Broad supply-chain/image, Node, browser, and local PostgreSQL-version matrix
  commands were not run, as ordered.

## GitHub CI / required checks

- The pushed implementation/transcript head contains no product/test/workflow
  changes, so GitHub checks validate the previously green product state only.
- No CI claim is made for the preserved local 010-o implementation or the new
  sixth integration file.
- No workflow rerun or corrective generation was used.

## Local setup / documentation / safety

- Used only fake credentials and disposable local PostgreSQL databases. No
  production system, secret store, or unrelated host resource was accessed.
- No dependency was installed or changed. No documentation needed correction;
  the parser limitation existed only in the prior OAP report, not product docs.
- Local uncommitted authorized paths are intentionally preserved for the next
  strategic continuation. Unrelated files changed: no. Scope deviation: no.
  Secret exposure: no. Extra PR: NO. Merge: NO.

## Immutable hashes

- `AGENTS.md`:
  `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`:
  `00bdd82fcec0afaf65d2fbc2a2f9fa43a7d4e9e254d7a262bea0c5bae3be6b8a`
- `ARCHITECTURE.md`:
  `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- `ARCHITECTURE-for-agents.md`:
  `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- `docs/assets/slaif-logo.svg`:
  `0760613aca18ace80d559686e98ec640f9f85caa163c5338c28e73b57b9c7a08`
- Activated work order:
  `b6f48cee245e1fcdce11e4ac8bee50a2c32410112d959111857d6cdae4be4f65`
- Activated pointer:
  `403ea790d24a43145ff6a8c9293d86d26ce6e14bdb081fd116d9bcb1e0a08412`
- Prior 010-n report:
  `58047b9882e82749d3a6c0d884ce1a103dbc60f38fc337817f7f73919cc8cad0`

## Known limitations / blockers

- The locally passing implementation is not delivered remotely until strategy
  authorizes the minimal test-package resolution and all mandatory gates pass.
- Publication, acceptance, next-scope activation, and merge remain
  strategic-model authority.
