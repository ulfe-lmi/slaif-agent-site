# OAP Coding-Agent Report — 010-p

## Work order

- Identifier: `010-p`; work-order file:
  `oap/orders/010-p-deliver-http-e2e-with-unique-test-module.md`; numeric
  objective: `010`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Delivered the preserved URL-safe token parser and real PostgreSQL-backed
Control authentication HTTP proof. Renamed the integration test to the unique
module `test_control_auth_http_integration.py`, resolving mypy without package
markers, exclusions, configuration changes, or weakened coverage. The complete
unit and six-file PostgreSQL suites pass locally, PostgreSQL 14–18 CI runs the
renamed test, and all 20 implementation-head checks are green.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#15](https://github.com/ulfe-lmi/slaif-agent-site/pull/15); state: `OPEN`
- Base/head branches: `main` / `oap/010-installation-local-auth`
- Starting remote SHA: `0f644250ab88b1fdadbd220d7dfafe31a76a5501`
- Implementation head SHA: `c3d47a734dc296794de8d07dc4049cecf352fbbd`
- Report publication commit: SELF
- Implementation commit pushed before report:
  `c3d47a734dc296794de8d07dc4049cecf352fbbd`; report
  parent=implementation SHA
- New PR this turn: no; amended existing: yes; merge performed: NO;
  auto-merge enabled: NO; workflow rerun: NO

## Changes made

- Corrected strict session and CSRF parsing with bounded splits that preserve
  the complete 43-character unpadded URL-safe Base64 secret, including `_` and
  `-`, while retaining version, type, public-ID, alphabet, decode, and decoded-
  length validation.
- Added deterministic round-trip coverage for underscores at the first,
  middle, and last valid encoded positions; hyphens; both URL-safe characters;
  representative byte patterns; and `b"\xff" * 32`. Added malformed separator,
  padding, whitespace, and trailing-data denials.
- Added a narrow constructor-only session entropy injection at
  `ControlDatabase`; production remains immutable `secrets.token_bytes` with
  exact 32-byte/256-bit validation.
- Corrected `HumanSessionService.revoke` to reject a false database revoke
  result for a previously active expired/disabled session while preserving
  idempotent replay for credentials already marked revoked.
- Added the actual FastAPI/ControlDatabase/Argon2/session/PostgreSQL flow with
  deterministic underscore-bearing credentials and exact setup, identity,
  session, login, CSRF, logout, replay, expiry, disabled-user, and row-state
  assertions.
- Renamed only the new integration test from the colliding
  `test_control_auth_http.py` basename to
  `test_control_auth_http_integration.py`. Updated the PostgreSQL 14–18 CI
  command to run that renamed sixth file alongside the existing five.

## Acceptance-criteria evidence

- Every formatter-produced credential in the deterministic URL-safe corpus
  round-trips; malformed boundaries produce the constant credential error.
- Actual setup and login routes issue underscore-bearing session and CSRF
  credentials that session inspection and logout parse successfully.
- Concurrent setup yields exactly one active LOCAL administrator and one
  session. Setup-token replay, wrong/unknown/disabled login, cross-session,
  missing, and duplicate CSRF preserve exact expected row state.
- Safe session inspection requires no CSRF and returns no CSRF material. Valid
  logout is an empty 204, revokes exactly its session, and replay is idempotent;
  revoked/expired credentials cannot inspect or logout as active.
- The renamed complete six-file set passes locally and runs in every PostgreSQL
  14–18 CI job. Strict fake cookie/header/no-store/noindex/204 behavior remains
  green in the complete unit suite.
- Production randomness, roles, grants, migrations, dependencies, edge, UI,
  and adjacent features are unchanged. Exactly PR #15 was amended.

## Local verification

- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 98 files.
- `uv run --frozen mypy`: PASSED — 88 source files, no exclusions.
- `uv run --frozen pytest services/backend/tests/unit -q`: PASSED — 203 passed
  in 10.07 seconds.
- Complete renamed six-file disposable PostgreSQL selection: PASSED — 39
  passed in 148.87 seconds.
- `python -m compileall -q services/backend/src services/backend/tests tools
  tests/repository`: PASSED.
- `python tools/check_repository.py`: PASSED.
- Exact old/new integration paths, CI reference, governance/prior hashes,
  conflict-marker scan, changed-order Markdownlint, and `git diff --check`:
  PASSED.
- Secret/URL behavior is asserted by actual setup requests and responses; only
  fake credentials and disposable database locators were used.
- Broad local Compose, supply-chain/image, Node, browser, and PostgreSQL-version
  matrix commands were not run, as ordered.

## Corrections during proof

- Replaced an initially incorrect test-only secret-suffix assertion that used
  unrestricted `rsplit`, the same conceptual mistake under repair, with a
  fixed grammar-offset assertion.
- Adjusted the expired-session fixture to move created, last-seen, recent-auth,
  and absolute-expiry timestamps together so it satisfies the existing
  `user_session_time_order` database constraint.
- The corrected actual-service flow then exposed the ignored `revoked=false`
  result; the in-scope service correction was made before the final single-file
  and six-file passing runs. No unchanged failed test was rerun.

## GitHub CI / required checks

- CI run `32417577700`: SUCCESS — Repository policy, Markdown, Mermaid, Node
  contracts, Python 3.12/3.13/3.14 quality and package, Compose and edge
  packaging, supply-chain evidence, dependency review, and Foundation
  PostgreSQL 14/15/16/17/18 all passed.
- CodeQL run `32417577811`: SUCCESS — Detect supported languages, Analyze
  actions, Analyze javascript-typescript, Analyze python, and CodeQL passed.
- Each PostgreSQL 14–18 job ran
  `test_control_auth_http_integration.py` with the other five required files.
- Named implementation-head checks: 20 passed, zero pending, zero failed.
- Workflow reruns: zero; corrective CI generations: zero.

## Local setup / documentation / safety

- Used only fake credentials and disposable local PostgreSQL databases. No
  production system, production data, secret store, or unrelated host resource
  was accessed.
- No dependency, migration, grant, UI, edge, or documentation change was
  required. Product docs contained no parser-limitation claim to remove.
- Unrelated files changed: no. Required scope deviation: no. Secret exposure:
  no. Production access: no. Extra PR: NO. Merge: NO. Activated order and
  pointer were committed byte-identically.

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
  `ca1802cca5ba5f6d1b9875d9d67af3b853c564e5e374274c946e1e781b7f6d28`
- Activated pointer:
  `5d9efcba5bca3ba87458b9067c4c86ba641fe0d0f073fd80297e4d8e798e031b`
- Prior 010-o report:
  `9ec3795c6bf9e719829f15e5c87f32e87d26b167d7ba76f0975ced274da71fda`

## Known limitations / blockers

- No 010-p implementation blocker remains. Publication, acceptance, next-work
  selection, and merge remain strategic-model authority.
