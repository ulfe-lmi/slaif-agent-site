# OAP Coding-Agent Report — 010-n

## Work order

- Identifier: `010-n`; work-order file:
  `oap/orders/010-n-close-control-auth-http-proof.md`; numeric objective: `010`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Hardened the bounded Control authentication HTTP surface with strict raw
Cookie and CSRF-header parsing, uniform CSRF authorization denials, exact
no-store/noindex handling for success and error responses, explicit empty 204
logout, exact local/production cookie behavior, strict fake coverage, and
honest external-routing documentation. Real PostgreSQL-backed ASGI proof then
exposed a pre-existing session-token parser defect in an adjacent module that
this work order explicitly excludes. The defect prevents valid randomly issued
URL-safe credentials containing underscores from authenticating. It was not
hidden with controlled randomness or repaired outside scope.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#15](https://github.com/ulfe-lmi/slaif-agent-site/pull/15); state: `OPEN`
- Base/head branches: `main` / `oap/010-installation-local-auth`
- Starting remote SHA: `04fc450cb144c91e9d42f78cf527afe759631155`
- Implementation head SHA: `b62a441165f4f9e84f9e33e5d6ea431e9f7c2b36`
- Report publication commit: SELF
- Implementation commit pushed before report:
  `b62a441165f4f9e84f9e33e5d6ea431e9f7c2b36`; report
  parent=implementation SHA
- New PR this turn: no; amended existing: yes; merge performed: NO;
  auto-merge enabled: NO; workflow rerun: NO

## Changes made

- Inspected raw ASGI headers and rejected multiple Cookie headers, malformed
  pairs, duplicate names, alternate local/production credential names, and
  missing, duplicate, non-ASCII, empty, or whitespace-padded CSRF headers.
- Kept safe session inspection session-cookie-only. Logout now compares the
  CSRF cookie/header in constant time, maps syntactically complete CSRF
  denials to one 403 envelope, and never clears cookies on denial.
- Added narrowly scoped middleware and error-handler behavior so all five
  Control auth paths carry exact private/no-store, pragma, and robots headers
  on success, validation, authentication, authorization, service, and
  internal-error responses.
- Made successful logout an empty 204 with two matching delete-cookie headers.
- Replaced permissive HTTP fakes with strict call-recording fakes and covered
  all routes, failure classes, cookie modes, ambiguity cases, replay, disabled
  docs URLs, error headers, and secret suppression.
- Corrected README/API/setup/authentication/operations documentation: the
  existing NGINX route exposes these backend endpoints, while no Next.js UI,
  clean Compose auth journey, or browser E2E exists. Rate limiting, durable
  audit, OIDC, MFA, sites, and memberships remain absent.

## Acceptance-criteria evidence

- Criteria 1–3: satisfied by strict unit/ASGI-fake coverage. Credential
  ambiguity fails before service calls; CSRF denials are uniform 403 and do
  not revoke or clear; local/production issue/delete cookies and empty 204
  logout are asserted exactly; all auth success/error responses carry the
  required security headers.
- Criterion 4: not satisfied. An actual disposable-PostgreSQL ASGI flow exposed
  the parser blocker before the required complete row-state proof could pass.
- Criterion 5: not satisfied. The five pre-existing integration files pass
  locally and in PostgreSQL 14–18 CI, but the required sixth
  `test_control_auth_http.py` cannot honestly be committed as passing until the
  parser is repaired. The workflow was not broadened to claim missing proof.
- Criterion 6: satisfied. No migration, grant, dependency, UI, edge, or
  adjacent product module changed.
- Criterion 7: partially satisfied. Exactly PR #15 was amended; the
  implementation head reached 20/20 green with no workflow rerun, but the
  required six-file semantics are absent and therefore completion is not
  claimed.

## PostgreSQL diagnostic and blocker

- A temporary real-service ASGI integration used the actual
  `ControlDatabase`, setup-token bootstrap, Argon2 identity service, session
  service, application, and disposable PostgreSQL database.
- Fresh issued tokens intermittently failed setup/session/logout flows when a
  valid URL-safe secret contained `_`. Direct inspection showed
  `parse_session_token()` and `parse_csrf_token()` in
  `services/backend/src/slaif_agent_site/identity/sessions.py` call unrestricted
  `split("_")`; an underscore in the encoded secret creates excess parts and
  raises `SessionCredentialError`.
- The minimal repair is bounded splitting that preserves the encoded secret,
  followed by unit and real PostgreSQL regression proof. That adjacent module
  is absent from 010-n allowed scope, and the sole broadening exception applies
  only to a direct defect in `012_001`. The temporary failing test was removed;
  no failing gate, deterministic safe-randomness bypass, or out-of-scope repair
  was pushed.

## Local verification

- Focused Control auth/error/health unit selection: PASSED — 27 passed in
  1.01 seconds.
- Five existing PostgreSQL integration files (`control_database_integration`,
  `database_bootstrap`, `local_identity`, `human_session`, and
  `local_authentication`): PASSED — 38 passed in 147.94 seconds.
- Temporary actual-service PostgreSQL ASGI diagnostic: FAILED as expected at
  valid session/CSRF token parsing when generated URL-safe secret material
  contained `_`; diagnosed before retry and not rerun unchanged.
- `uv run --frozen ruff check` on changed Python files: PASSED.
- `uv run --frozen ruff format --check` on changed Python files: PASSED — three
  files already formatted.
- `uv run --frozen mypy`: PASSED — 87 source files.
- `python -m compileall -q services/backend/src services/backend/tests/unit`:
  PASSED.
- `python tools/check_repository.py`: PASSED.
- Explicit changed-document/order Markdownlint `--no-globs`: PASSED — zero
  issues.
- Conflict-marker scan and `git diff --check`: PASSED.
- Skipped required test: the permanent sixth PostgreSQL ASGI integration file,
  blocked by the excluded parser defect above. Broad Node, browser, supply-chain,
  image, and local PostgreSQL-version matrix commands were not run, as ordered.

## GitHub CI / required checks

- CI run `32413969989`: SUCCESS — Repository policy, Markdown, Mermaid, Node
  contracts, Python 3.12/3.13/3.14 quality and package, Compose and edge
  packaging, supply-chain evidence, dependency review, and Foundation
  PostgreSQL 14/15/16/17/18 all passed.
- CodeQL run `32413970051`: SUCCESS — Detect supported languages, Analyze
  actions, Analyze javascript-typescript, Analyze python, and CodeQL all passed.
- Named implementation-head checks: 20 passed, zero pending, zero failed.
- These checks ran the unchanged five-file PostgreSQL selection, not the missing
  sixth real-ASGI file; green CI is not presented as criterion 5 evidence.

## Local setup / documentation / safety

- Used only fake credentials and a disposable local PostgreSQL service. No
  production system, production data, secret store, or external product service
  was accessed. No dependency was added or installed for the implementation.
- Documentation updated: `README.md`, `docs/API.md`,
  `docs/INSTALLATION_SETUP.md`, `docs/LOCAL_AUTHENTICATION.md`, and
  `docs/OPERATIONS.md`.
- Unrelated files changed: no. Required scope deviation: no. Secret exposure:
  no. Production access: no. Extra PR: NO. Merge: NO. Activated order and active
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
  `7afb2c3ee8711ebf6065f1e45341eff6e6ee3853a4a00a439bb5c30c5cae6d2a`
- Activated pointer:
  `5d44743acd6b3cac66903be02987d00665a3b84f33941015e68e578088e0024c`
- Prior 010-m report:
  `cd1d99a5e60715ac1de342bc7381f62eceaa17054ec1a442d7a204585518178e`

## Known limitations / blockers

- Completion requires strategic authorization to repair and regress
  `identity/sessions.py`, then add the permanent real PostgreSQL ASGI file and
  six-file PostgreSQL 14–18 CI selection.
- Publication, acceptance, scope activation, and merge remain strategic-model
  authority.
