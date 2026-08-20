# OAP Coding-Agent Report — 010-m

## Work order

- Identifier: `010-m`; work-order file: `oap/orders/010-m-control-auth-http-boundary.md`; numeric objective: `010`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Implemented the bounded Control HTTP authentication boundary: setup status,
initial setup, local login, session inspection, and CSRF-protected logout. The
routes are internal-only with disabled public documentation URLs, secret-safe
responses, bounded cookies, stable error mapping, and a narrowly scoped
`012_001` setup-status function. CI and CodeQL are green.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR [#15](https://github.com/ulfe-lmi/slaif-agent-site/pull/15); state: `OPEN`
- Base/head branches: `main` / `oap/010-installation-local-auth`
- Starting remote SHA: `30a27d306776322e1300beaa7894e245f1a01b5c`
- Implementation head SHA: `12bf357bd232081e5feb068b85443f1a7dab20ce`
- Report publication commit: SELF
- Implementation commits pushed before report: `12bf357bd232081e5feb068b85443f1a7dab20ce`; report parent=implementation SHA
- New PR this turn: no; amended existing: yes; merge performed: NO

## Changes made

- Added `012_001_control_auth_http` setup-status function with owner-owned, public-revoked, Control-execute-only privileges.
- Added typed Control routes, stable headers/errors, production `__Host-` and local cookie contracts, duplicate/alternate-cookie rejection, CSRF comparison, and session revocation.
- Extended the Control adapter and database setup-status operation; preserved cancellation propagation.
- Added unit and PostgreSQL-backed HTTP boundary coverage, migration/package/repository inventories, CI matrix coverage, and durable API/setup/authentication documentation.

## Acceptance-criteria evidence

- Exact five routes are registered and present in internal `app.openapi()` while docs, ReDoc, and public OpenAPI URLs are disabled.
- Setup status is private/no-store/noindex and returns only bounded booleans.
- Setup/login issue bounded session and CSRF cookies without returning credential material; session inspection requires only the session cookie.
- Logout rejects missing, duplicate, alternate, malformed, or mismatched cookies/CSRF before revocation and clears both cookies on success.
- Migration and privilege inventories remain deterministic; no agent, editor, renderer, UI, NGINX, OIDC, MFA, rate-limit, or audit scope was added.
- Exactly PR #15 was amended; no merge or auto-merge was performed.

## Local verification

- `uv run --frozen pytest services/backend/tests/unit -q`: PASSED — 184 passed, 3 warnings.
- Focused auth/control/repository tests: PASSED — 91 passed, 22 subtests.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED — 98 files.
- `uv run --frozen mypy`: PASSED — 87 source files.
- `python -m compileall -q services/backend/src services/backend/tests tools tests/repository`: PASSED.
- `python tools/check_repository.py`: PASSED.
- Full disposable PostgreSQL selection reached 34 passing tests but was contaminated by orphaned fixture roles/databases, producing teardown/duplicate-role failures; no code retry was made against unchanged infrastructure.
- Repository-wide markdownlint wrapper expanded to all 2,660 Markdown files and did not complete locally; GitHub Markdown check passed.

## GitHub CI / required checks

- CI run `32410965430`: SUCCESS — Repository policy, Markdown, Node contracts, Python 3.12/3.13/3.14, Compose, Supply-chain evidence, Mermaid, Dependency review, and PostgreSQL 14–18.
- CodeQL run `32410965451`: SUCCESS; Analyze actions/javascript-typescript/python all passed.
- All required checks green at report drafting: yes.

## Local setup / documentation / safety

- No new dependencies, credentials, production systems, or external services were accessed.
- Documentation added/updated: `docs/API.md`, `docs/INSTALLATION_SETUP.md`, `docs/LOCAL_AUTHENTICATION.md`.
- Unrelated files changed: no. Required scope deviation: no. Extra PR: NO. Merge: NO. Activated order and active pointer were committed byte-identically.

## Immutable hashes

- `ARCHITECTURE.md`: `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- `ARCHITECTURE-for-agents.md`: `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- `docs/assets/slaif-logo.svg`: `0760613aca18ace80d559686e98ec640f9f85caa163c5338c28e73b57b9c7a08`
- Prior reports remain immutable.

## Known limitations / blockers

- Local PostgreSQL fixture cleanup was blocked by pre-existing orphaned role/database state; authoritative CI passed all PostgreSQL jobs.
- Publication, acceptance, and merge remain strategic-model authority.
