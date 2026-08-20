# OAP Coding-Agent Report — 010-q

## Work order

- Identifier: `010-q`; work-order file:
  `oap/orders/010-q-auth-ui-compose-operator-flow.md`; numeric objective: `010`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Implemented the bounded self-hosted setup/login/admin/logout operator flow,
automatic one-time Compose setup-token output, exact Control API edge routing,
and a secret-safe real Compose authentication journey. The complete affected
local verification, including one clean real Compose run, passed. The initial
CI generation found one formatter defect, which was corrected in the order's
single permitted corrective code generation. That corrective generation then
exposed a distinct compatibility defect: `tools/compose/smoke.sh` rejects the
established CI project name `slaif007ci` because its new safety allowlist omits
the `slaif007` prefix. Nineteen checks passed and Compose failed before setup.
No unauthorized third code generation or workflow rerun was performed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#15](https://github.com/ulfe-lmi/slaif-agent-site/pull/15); state: `OPEN`
- Base/head branches: `main` / `oap/010-installation-local-auth`
- Starting remote SHA: `f23a0d7cdb582c767c130012874a99238ab8d9e7`
- Implementation head SHA: `662a8a2b02d534ba7f423a456ab7f7cc7e6ab034`
- Report publication commit: SELF
- Implementation commits pushed before report:
  `2eea53f5c8a2553edb0f64ef13cc073646e1e813` and
  `662a8a2b02d534ba7f423a456ab7f7cc7e6ab034`; report
  parent=implementation SHA
- New PR this turn: no; amended existing: yes; merge performed: NO;
  auto-merge enabled: NO; workflow rerun: NO

## Changes made

- Made Compose bootstrap distinguish initialized, fresh-token, and existing-
  token states. A fresh installation prints the localhost setup URL and secret
  exactly once; initialized/existing states do not re-disclose plaintext, and
  existing-token recovery points to explicit trusted rotation.
- Added unit coverage for all three Compose bootstrap states.
- Corrected NGINX and Apache mappings for the two Control health endpoints and
  the exact `/api/control/v1/` namespace while rejecting the broader fallback.
- Added responsive Next routes for `/`, `/setup`, `/login`, and `/admin`, with
  labeled forms, correct autocomplete, pending submission guards, generic
  failures, keyboard-visible focus, reduced-motion handling, and 320-pixel
  layout support.
- Added same-origin setup/login/session/logout client behavior, secure-cookie
  selection from the actual page protocol, bounded cookie parsing, safe admin
  session summary, CSRF-backed logout, and client redirects.
- Added a standard-library, cookie-jar-based Compose authentication helper and
  integrated setup, status, session, logout, relogin, and wrong-password proof
  through localhost without printing credentials, cookies, headers, or raw
  responses.
- Updated operator, setup, authentication, deployment, configuration, API, and
  operations documentation to describe implemented behavior and retain honest
  limitations.
- Applied the formatter-produced correction to
  `tests/packaging/test_edge_contract.py` after the initial CI failure.

## Acceptance-criteria evidence

- Fresh Compose bootstrap and token output semantics are covered by 17 passing
  setup-token unit tests and exercised by the real Compose smoke.
- NGINX/Apache exact health and v1 contracts pass the affected packaging tests;
  the real Compose run passed NGINX routing and Apache syntax/config checks.
- The Node gate passed, including five web surface tests and a successful Next
  production build containing `/`, `/setup`, `/login`, and `/admin`.
- The real project-scoped Compose run `slaif009qsmoke` passed the complete
  secret-safe authentication journey, edge, database-login, secrets,
  readiness, restart, broken-bootstrap negative, and 27 packaging-test stages.
- No Playwright, browser binary/image, dependency, lockfile, migration, grant,
  OIDC, MFA, rate-limit, audit, or adjacent-product change was added.
- Exactly PR #15 was amended, but the required 20/20 report-head condition was
  not achieved because the corrective implementation head has one failed
  Compose check.

## Local verification

- `pnpm install --frozen-lockfile` and `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — web 5, browser-worker 1, contract 2.
- `pnpm build`: PASSED — all four operator routes built.
- `uv run --frozen pytest
  services/backend/tests/unit/test_bootstrap_setup_token.py -q`: PASSED — 17.
- `uv run --frozen pytest
  services/backend/tests/unit/test_installation_setup.py -q`: PASSED — 4.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED after the formatter correction.
- `uv run --frozen mypy`: PASSED — 88 source files.
- `python -m compileall -q services/backend/src services/backend/tests tools
  tests/repository`: PASSED.
- `python tools/check_repository.py`: PASSED.
- Affected edge/Compose/OCI packaging selection: PASSED — 27 tests in the
  final real Compose run.
- `sudo tools/compose/smoke.sh slaif009qsmoke`: PASSED —
  `compose-auth-smoke: OK` and `compose-smoke: OK`; bounded cleanup completed.
- Explicit changed-document/order Markdownlint with `--no-globs`: PASSED.
- Secret/log/URL/storage scans, governance hashes, exact paths, conflict-marker
  scan, and `git diff --check`: PASSED.
- Playwright and browser matrices: NOT RUN, as explicitly ordered.
- Broad local supply-chain/image evidence and PostgreSQL-version matrix: NOT
  RUN, as explicitly excluded beyond the existing Compose smoke.

## Diagnosed failures and correction limit

- A first non-privileged Compose attempt stopped at local Docker-socket
  permission before mutation. The authorized passwordless-`sudo` run was used.
- The first real Compose run passed authentication, then exposed that
  `control_readiness.py` only accepts the repository's established safe project
  prefixes. The smoke selector was bounded to those project families, and the
  final clean `slaif009qsmoke` run passed.
- Initial CI failed Python 3.12/3.13/3.14 quality and Compose because one new
  edge-contract expression was not formatter-produced. The exact full CI Ruff
  scope and formatter were run, and the single permitted corrective code
  generation pushed the formatter-only commit.
- Corrective CI then invoked `sh tools/compose/smoke.sh slaif007ci` and failed
  immediately with `compose-smoke: unsafe project name` (exit 2). The selector
  accepts `slaif009*` and `slaif010*` but accidentally omits the long-standing
  CI-safe `slaif007*` prefix. The direct fix is unambiguous, but it would require
  a second corrective code generation, beyond the order's explicit limit.
- No unchanged failed test or workflow was rerun. No third implementation push
  was made with the known failing affected gate.

## GitHub CI / required checks

- Corrective CI run `32420309413`: 15 CI jobs settled; Repository policy,
  Markdown, Mermaid, Node contracts, Python 3.12/3.13/3.14 quality and package,
  supply-chain evidence, dependency review, and Foundation PostgreSQL
  14/15/16/17/18 passed. Compose and edge packaging FAILED for the diagnosed
  `slaif007ci` allowlist omission.
- CodeQL run `32420309412`: Detect supported languages, Analyze actions,
  Analyze javascript-typescript, Analyze python, and aggregate CodeQL passed.
- Named implementation-head checks: 19 passed, zero pending, one failed.
- Workflow reruns: zero; corrective code generations: exactly one.
- Report-head checks cannot be truthfully claimed 20/20 green while the
  implementation defect remains.

## Local setup / documentation / safety

- Used passwordless `sudo` only for disposable local Docker/Compose test
  infrastructure. Only fake credentials and project-scoped disposable data
  were used; cleanup completed.
- No production system, production data, protected credential, secret store,
  unrelated host resource, or external authenticated service was accessed.
- Documentation was updated in the same implementation commit and does not
  claim Playwright or unimplemented authentication features.
- Unrelated files changed: no. Required scope deviation: no. Secret exposure:
  no. Production access: no. Skipped required local test: no. Extra PR: NO.
  Merge: NO. Activated order and pointer were committed byte-identically.

## Immutable hashes

- `AGENTS.md`:
  `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`:
  `00bdd82fcec0afaf65d2fbc2a2f9fa43a7d4e9e254d7a262bea0c5bae3be6b8a`
- `ARCHITECTURE.md`:
  `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- `ARCHITECTURE-for-agents.md`:
  `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Activated work order:
  `9c47bcecfc0d9de7b9b3a82708f66672e3eb56fcf57d027f5f45a55455090592`
- Activated pointer:
  `9555e02317fab37bc858ced3abbdba0e8ef6334462443565e4d2f0cc7e8b6afe`
- Prior 010-p report:
  `1ae8643229f6e9de3841eef7822686751331307e6e1becb8ca13d1a0b0b21db6`

## Known limitations / blockers

- `tools/compose/smoke.sh` must restore acceptance of the established safe
  `slaif007*` CI project family. The present order's one corrective code
  generation is exhausted, so strategic continuation authority is required.
- The required 20/20 green report head is therefore not achieved. Acceptance,
  continuation selection, publication, and merge remain strategic-model
  authority.
