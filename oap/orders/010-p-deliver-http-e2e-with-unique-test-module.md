# OAP Work Order — 010-p

## Objective

Amend PR `#15` to deliver the preserved, locally passing `010-o` parser and
real PostgreSQL/ASGI implementation. Resolve only the mypy duplicate-module
basename by renaming the integration test to
`test_control_auth_http_integration.py`, update exact references, rerun all
mandatory focused gates, push, and obtain a 20/20 green report head.

## GitHub objective state

- Numeric objective/round: `010` / `010-p`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15` — <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch/base: `oap/010-installation-local-auth` / `main`
- Required starting PR/report head:
  `0f644250ab88b1fdadbd220d7dfafe31a76a5501`
- `010-o` transcript-only implementation head:
  `6e2b7d955aaf2dca0f480efe2151ab7764c23887`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

Before push, reverify current remote main/head when network is available. No
new PR, rebase, force-push, merge, close, auto-merge, or unrelated action.

## Preserved strategic input

The shared checkout intentionally contains these uncommitted, authorized,
locally proven `010-o` changes:

```text
.github/workflows/ci.yml
services/backend/src/slaif_agent_site/control_api/database.py
services/backend/src/slaif_agent_site/identity/sessions.py
services/backend/tests/unit/test_sessions.py
services/backend/tests/integration/test_control_auth_http.py
```

Preserve and deliver them. They passed parser/unit tests, 203 backend unit
tests, and the complete six-file PostgreSQL set (39 tests); only mypy rejects
the unit and integration files sharing basename `test_control_auth_http`.

## Allowed scope and exact resolution

```text
.github/workflows/ci.yml
services/backend/src/slaif_agent_site/control_api/database.py
services/backend/src/slaif_agent_site/identity/sessions.py
services/backend/tests/unit/test_sessions.py
services/backend/tests/integration/test_control_auth_http.py       # rename away
services/backend/tests/integration/test_control_auth_http_integration.py
tools/check_repository.py                                          # only exact required-file reference if present
tests/repository/test_repository_policy.py                         # matching policy fixture only if needed
docs/API.md                                                        # only if test filename is documented
oap/active
oap/orders/010-p-deliver-http-e2e-with-unique-test-module.md
oap/reports/010-p-deliver-http-e2e-with-unique-test-module.md
```

Rename the integration file; do not add `__init__.py`, change mypy config,
exclude tests, alter import mode, or weaken type checking. Update the
PostgreSQL 14–18 CI path and any exact repository-policy reference to the new
filename. No product behavior beyond the preserved parser/test-injection fix.

## Moderate autonomy and completion rule

- Target: 20 minutes; hard stop: 40 minutes.
- No arbitrary local attempt cap; fix in-scope rename/reference failures until
  all mandatory evidence passes, with no unchanged blind reruns.
- Do not push until mypy, complete unit suite, and complete six-file PostgreSQL
  set all pass with the renamed file.
- One initial CI generation; one corrective code generation only for a genuine
  clean-environment/reference defect; never workflow-rerun.
- No local Compose, supply-chain/image, Node, browser, or full DB matrix.

## Requirements and acceptance

1. Preserve bounded `split("_", 3)` session and `split("_", 2)` CSRF parsing,
   strict grammar, production randomness, deterministic underscore/hyphen
   corpus, revoke-result correction, and constructor-only test entropy injection.
2. Rename only the integration test to a unique module basename and preserve
   every real setup/login/session/logout/CSRF/expiry/replay/row-state assertion.
3. Run and pass `uv run --frozen mypy` with no exclusions or duplicate module.
4. Run and pass the full backend unit suite and all six PostgreSQL integration
   files locally, using the renamed file.
5. PostgreSQL 14–18 CI each runs the renamed HTTP integration alongside the
   other five files; all 20 report-head checks pass with no rerun.
6. No UI/edge/dependency/migration/grant/adjacent feature or test weakening.
7. Exactly PR #15 amended; implementation/report commits and `SELF` parentage
   follow protocol.

Run Ruff/format/mypy/compile, repository policy, parser/session/HTTP unit,
complete six-file disposable PostgreSQL, exact paths/prior hashes, secret scan,
no conflict markers, changed-doc/report Markdownlint `--no-globs`, and
`git diff --check`. Lint the completed report before publication.

## Safety, workflow, and report

Fake secrets and disposable PostgreSQL only; no production access or secret/
cookie/DSN/raw error output. Preserve governance, architecture, OAP and all
accepted auth boundaries.

Amend only the existing PR. Atomically publish exactly:

```text
oap/reports/010-p-deliver-http-e2e-with-unique-test-module.md
```

The report-only `SELF` commit must parent the literal implementation head.
Report rename/reference diff; preserved parser/real-ASGI behavior; complete
local/mypy/six-file/five-version/20-check results; paths/hashes/corrections;
no-workflow-rerun/no-new-PR/no-merge state; and
`Report publication commit: SELF`.
