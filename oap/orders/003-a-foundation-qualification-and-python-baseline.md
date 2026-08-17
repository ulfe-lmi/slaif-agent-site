# OAP Work Order — 003-a

## Objective

Create exactly one new GitHub pull request that qualifies the architecture-
selected `agent-cow-postgresql==0.2.0` PyPI foundation and establishes the
minimal reproducible Python backend project baseline for SLAIF Agent-Site.

This objective proves dependency source/integrity, public API compatibility,
supported Python/PostgreSQL baselines, packaging, and downstream ownership
boundaries. It must not begin application services or product database schema.

## GitHub objective state

- Numeric objective: `003`
- Execution round: `003-a`
- PR mode: `CREATE_NEW_PR`
- Existing PR: N/A
- Required head branch: `oap/003-foundation-python-baseline`
- Base branch: `main`
- Required PR title: `[OAP 003] Qualify foundation and add Python baseline`
- Required PR readiness: non-draft (`draft: false`)
- Repository: `ulfe-lmi/slaif-agent-site`
- Repository URL: `https://github.com/ulfe-lmi/slaif-agent-site`

## Strategic context

Objectives `000`–`002` established governance, the architecture, professional
repository documentation/CI/CodeQL, and Mermaid validation. The approved
long-term roadmap begins product implementation with Architecture Phase 0:
qualify the generic COW foundation before building any product-owned service,
schema, authorization path, or UI.

The product must consume the published PyPI distribution, import only public
`agentcow.postgres` APIs, and freeze exact registry artifacts in `uv.lock`.
GitHub remains source/provenance/issues only; normal development, CI, release,
and deployment must never use a Git/VCS, branch, commit, direct-URL,
local-path, or editable foundation dependency.

## Current verified state

The strategic model independently verified before activation:

- Remote default branch: `main`
- Remote `main` SHA:
  `c2038f0c14ac9eba5ca997fe3ae1a343e1869fd4`
- Objective `002` PR `#3` is merged and remote `main` includes the accepted
  Mermaid syntax repair and render gate.
- Open pull requests: none
- Current merged OAP active identifier: `002-a`
- `main` CI, CodeQL, Dependency Review, Mermaid, repository policy, and
  Dependabot initialization are successful.
- CodeQL open alerts: zero at reconciliation time.
- Repository has no `pyproject.toml`, `uv.lock`, backend package, application
  dependency, product build, or product test suite.
- Existing Python files are repository-policy/Mermaid tooling only.

Current PyPI verification for `agent-cow-postgresql`:

```text
latest/version selected: 0.2.0
yanked: false
Requires-Python: >=3.10,<3.15
wheel: agent_cow_postgresql-0.2.0-py3-none-any.whl
wheel SHA-256: c469d24700fabb93a58f464d3539a32e936097f93035a95f193062859546f5b1
sdist: agent_cow_postgresql-0.2.0.tar.gz
sdist SHA-256: eae8d434d2fc03c4faa08b44b4863fc8f8efb44ee33eaad3adc22e7eb96a062c
source repository: https://github.com/jpers1/agent-cow-postgresql
upstream: https://github.com/trail-ml/agent-cow-python
```

The package declares optional SQLAlchemy/asyncpg dependencies rather than
making them unconditional. Inspect the actual public asyncpg API and declare
only the direct test/development dependencies genuinely needed for this
qualification. Do not infer private behavior from package tables.

Current tooling qualified for this objective:

```text
uv CLI: 0.12.5
uv_build: 0.12.5, if selected after official build-backend verification
astral-sh/setup-uv action:
  20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
product Python baseline proposed here: >=3.12,<3.15
CI Python versions: 3.12, 3.13, 3.14
PostgreSQL qualification versions: 14, 15, 16, 17, 18
```

If PyPI, action, `main`, or package public API state differs materially at
execution time, report the difference and proceed only when this objective
remains architecture-compatible. Do not silently upgrade the foundation.

## Required final tracked paths

The final PR diff against `main` must contain exactly these twenty paths:

```text
.github/dependabot.yml
.github/workflows/ci.yml
AGENTS.md
CONTRIBUTING.md
NOTICE
README.md
docs/FOUNDATION_INTEGRATION.md
oap/active
oap/orders/003-a-foundation-qualification-and-python-baseline.md
oap/reports/003-a-foundation-qualification-and-python-baseline.md
pyproject.toml
services/backend/src/slaif_agent_site/__init__.py
services/backend/src/slaif_agent_site/agent_state/__init__.py
services/backend/src/slaif_agent_site/agent_state/foundation.py
services/backend/tests/conftest.py
services/backend/tests/integration/test_foundation_postgres.py
services/backend/tests/unit/test_foundation_contract.py
tests/repository/test_repository_policy.py
tools/check_repository.py
uv.lock
```

Do not add generated caches, coverage, build output, environment files,
database dumps, downloaded distributions, wheel/sdist artifacts, or temporary
PostgreSQL state.

## Scope

### A. Reproducible root Python project

- Add one root PEP 621 `pyproject.toml` for the pre-alpha Agent-Site backend
  package using a qualified permissive build backend.
- Set product Python range to `>=3.12,<3.15` and a clearly pre-release/internal
  version such as `0.0.0`; do not imply published product maturity.
- Configure the package source at
  `services/backend/src/slaif_agent_site` and tests beneath
  `services/backend/tests`.
- Declare `agent-cow-postgresql==0.2.0` as the exact production foundation
  dependency with no source override.
- Add minimal exact/bounded development groups for pytest/async testing,
  formatting/lint/type checks, build, and qualification dependencies. Avoid
  FastAPI, SQLAlchemy application use, Alembic, browser, Node, or unrelated
  framework dependencies.
- Generate and commit `uv.lock` using exact uv `0.12.5`; ensure registry source
  URLs and artifact hashes include the verified foundation wheel/sdist.

### B. Product-owned foundation adapter boundary

Create a deliberately small module at:

```text
services/backend/src/slaif_agent_site/agent_state/foundation.py
```

It must:

- import only documented public symbols from `agentcow.postgres`;
- centralize the product's dependency surface without copying foundation code;
- expose/import the Architecture Section 7.1 capabilities needed by future
  bootstrap/runtime/reviewer implementations, or a typed/validated subset with
  an explicit qualification inventory;
- contain no site/user/capability/content policy, no SQL, no private table/
  function name, no DB credential, and no runtime canonical-write escape;
- avoid a misleading wrapper that changes transaction ownership or conflict
  defaults; product-specific safe invocation arrives in later objectives.

Package `__init__.py` files must remain minimal and not create service/global
connection state.

### C. Unit and metadata qualification

Add unit tests that verify:

- installed distribution version is exactly `0.2.0`;
- expected `agentcow`/`agentcow.postgres` import paths and public symbols exist;
- adapter references only approved public imports and exposes no native/private
  SQL/table dependency;
- package metadata and `requires-python` are compatible with the product range;
- the final lock resolves the foundation from PyPI registry artifacts with the
  two verified SHA-256 digests and no VCS/path/editable/direct URL;
- package/build metadata, version, README/license links, and source layout are
  coherent;
- a wheel and sdist for Agent-Site build and contain only intended backend
  package files/metadata, not tests/secrets/caches/OAP documents.

Tests should use public metadata/APIs rather than freeze incidental private
implementation details.

### D. PostgreSQL foundation qualification

Add a downstream integration test using a disposable database/schema that
exercises public foundation behavior sufficient for product adoption:

- setup/deploy functions;
- enable one representative table/schema with unsafe canonical writes off;
- harden setup/runtime/reviewer roles and validate effective privileges;
- enter an asyncpg COW session using server/test-selected session and operation
  UUIDs;
- prove workspace write isolation and canonical unchanged before review;
- inspect operations through a public API;
- use public reviewer API for conflict-safe full promotion and discard in
  bounded representative cases;
- prove missing session context/runtime base-table/reviewer privilege paths
  fail closed;
- ensure pooled/cancelled test connections return without leaked context.

Run this same downstream qualification against PostgreSQL 14, 15, 16, 17,
and 18 in GitHub CI. Keep exhaustive product roles/schema/promotion/concurrency
coverage assigned to objectives 006 and 041; this test is a package-adoption
gate, not their substitute.

### E. CI and repository policy

Extend `.github/workflows/ci.yml` with SHA-pinned, least-privilege jobs for:

1. Python quality/package across Python 3.12, 3.13, and 3.14:
   - exact setup-uv action SHA with `version: "0.12.5"`;
   - `uv sync --frozen` using all required development groups;
   - lint/format-check/type-check according to the selected configuration;
   - unit/metadata tests;
   - product wheel/sdist build and content inspection;
   - no committed/generated diff.
2. Foundation PostgreSQL qualification across 14–18 using disposable service
   databases and fake test credentials only.

Preserve existing Repository policy, Markdown, Mermaid, Dependency Review,
CodeQL triggers/permissions/concurrency/pins and all security constraints.
Use `ubuntu-24.04`, explicit timeouts, `persist-credentials: false`, no secret,
no `pull_request_target`, and no mutable action reference.

Add this approved action pin to repository policy:

```text
astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
```

Update `tools/check_repository.py` and isolated policy tests to:

- require `pyproject.toml`, `uv.lock`, foundation doc/adapter/tests;
- validate setup-uv pin/release comment;
- inspect both `pyproject.toml` and `uv.lock` for exact registry-only foundation
  source and verified artifact hashes;
- reject Git/VCS, direct URL, local path, editable, missing exact version,
  missing hash, or unapproved registry forms through positive/negative fixtures;
- remain extensible for later manifests and dependency upgrades.

Update Dependabot with a weekly grouped `pip` entry rooted at `/`, bounded PR
limit, while retaining GitHub Actions updates. Dependabot does not replace the
locked/frozen qualification gate.

### F. Documentation and attribution

Add `docs/FOUNDATION_INTEGRATION.md` covering:

- verified distribution/version/artifact hashes, Python/PostgreSQL matrices;
- public symbols/product reliance and logical live-base overlay semantics;
- product versus Agent-State versus foundation ownership boundaries;
- server-selected context and why foundation settings are not authentication;
- qualification commands/results and future upgrade gate;
- registry-only/no-VCS rule and source/provenance links;
- MIT/upstream attribution and limitations/deferred product hardening.

Update:

- `NOTICE` from “planned foundation” to accurately record the integrated PyPI
  dependency and MIT/upstream attribution;
- `README.md` current status, repository map, preparation/CI checks, and
  delivery sequence—still state that no runnable product/Compose/API exists;
- `AGENTS.md` and `CONTRIBUTING.md` with exact frozen install/unit/integration/
  lint/type/build commands and the rule that future product work extends these
  gates.

## Non-goals

- No FastAPI, Uvicorn, SQLAlchemy application layer, Alembic, product database
  schemas/roles, site/content/workspace/capability behavior, service entrypoint,
  REST/MCP route, Next.js/Node workspace, Dockerfile, Compose, NGINX, browser,
  media, job worker, review/promotion product code, or runtime secrets.
- No private foundation table/function/SQL, copied upstream implementation, or
  source checkout used in normal build/tests.
- No foundation version change from `0.2.0`.
- No claim that this downstream smoke suite replaces the later security,
  privilege, cancellation, conflict, or concurrency objectives.
- No package publication, release, issue, tag, extra PR, merge, or auto-merge.

## Acceptance criteria

1. Exactly one non-draft PR exists with the required title/base/head and final
   diff contains exactly the twenty allowed paths.
2. `uv sync --frozen` succeeds from a clean environment for Python 3.12–3.14;
   no resolver/lock mutation occurs.
3. `pyproject.toml` declares exactly `agent-cow-postgresql==0.2.0` from PyPI;
   `uv.lock` contains the verified wheel/sdist SHA-256 hashes and no forbidden
   source form.
4. The adapter and contract tests use only documented public foundation APIs,
   contain no private SQL/table dependency, and preserve transaction/conflict
   semantics rather than pretending to implement product policy.
5. PostgreSQL 14–18 downstream qualification succeeds for deploy/enable/
   harden/privilege/session isolation/operation/reviewer promotion/discard/
   missing-context and cleanup baseline.
6. Agent-Site wheel/sdist build reproducibly with intended contents and
   Apache-2.0 metadata; foundation MIT/upstream attribution is present.
7. Repository policy negative fixtures fail every prohibited dependency source
   and missing-hash/version case.
8. README/docs/NOTICE/AGENTS/CONTRIBUTING accurately distinguish implemented
   Python foundation from all still-planned product/runtime behavior.
9. All final-head checks succeed: existing repository/Markdown/Mermaid/
   Dependency Review/CodeQL plus Python quality/package and PostgreSQL matrix;
   no required check is failed, skipped, cancelled, missing, or pending.
10. Architecture and every objective `000`–`002` order/report remain unchanged;
    `oap/active` is `003-a` with unique order/report correlation.
11. Final remote head is the report-only `SELF` commit whose first parent is
    the report's literal implementation head.
12. No secret, production access, hosted runtime, product service/schema/UI,
    non-permissive dependency, or scope drift is introduced.

## Verification required

At minimum run and report exact outcomes for the selected equivalent commands:

```bash
uv --version
uv lock --check
uv sync --frozen --all-groups
uv run ruff check services/backend tests/repository tools
uv run ruff format --check services/backend tests/repository tools
uv run pytest services/backend/tests/unit tests/repository
uv run pytest services/backend/tests/integration
uv build
python tools/check_repository.py
python tools/check_mermaid.py
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
git diff --check origin/main...HEAD
git diff --name-only origin/main...HEAD
```

Adapt the exact group/type-check command to the selected current tool while
keeping frozen reproducibility. Also verify:

- clean-cache/fresh-environment frozen install;
- lock source/artifact hashes and absence of forbidden forms;
- built wheel/sdist metadata/content;
- package/version/license/source metadata;
- public symbol inventory and no private SQL/table names;
- all PostgreSQL matrix jobs and negative privileges/context cases;
- deterministic dependency/license inventory;
- Markdown/fence/link checks and focused secret scan;
- exact twenty-path scope and unchanged prior architecture/OAP hashes;
- unique PR/body/base/head/draft/auto-merge identity;
- every final-head GitHub check and CodeQL alert state;
- report commit parent/report-only delta and clean synchronized worktree.

If an integration test cannot run locally, use passwordless sudo/disposable
PostgreSQL/Docker as appropriate. A local skip is not passing evidence; the
corresponding GitHub matrix must run and succeed before acceptance.

## Safety / security constraints

- Use fake disposable PostgreSQL credentials/data only; never production.
- Do not print package index credentials, database URLs with real secrets, or
  environment tokens.
- Do not add private package indexes, source overrides, arbitrary install
  hooks, mutable actions, or hosted/account-bound services.
- Run package build/test code only in the disposable execution environment.
- Preserve all architecture/OAP authority, no-merge, and transcript rules.

## Local execution capability

- Routine uv/Python/PostgreSQL/build/test setup belongs to the coding agent.
- Passwordless `sudo`, Docker, and local disposable services are available.
- Do not transfer installation, matrix diagnosis, or CI-log inspection to the
  human or strategic model.

## GitHub workflow

1. Fetch and verify authoritative `main`, no existing objective `003` PR, and
   merged objective `002` state.
2. Preserve this activated order and `oap/active`; create the required fresh
   branch from current `origin/main`.
3. Implement only the twenty allowed paths and stage explicit paths only.
4. Run all local verification, commit/push implementation, and create exactly
   one non-draft PR.
5. Inspect and repair every in-scope CI/matrix/CodeQL failure on the same PR.
6. Record the literal implementation head and atomically publish the report.
7. Commit only the report, push it, verify `SELF`, and inspect final-head
   checks before exact FIFO `OK`.
8. Never merge, enable auto-merge, create another PR, or choose `004-a`.

## Required report

Atomically publish exactly:

```text
oap/reports/003-a-foundation-qualification-and-python-baseline.md
```

Use the full protocol 1.2 report structure. Include exact PR/commit/path
identity; uv/build/tool versions; PyPI filenames/hashes/source; `pyproject` and
lock evidence; public API/adapter inventory; Python/PostgreSQL matrix results;
package artifact content/metadata; every dependency/license/repository-policy
negative; docs/NOTICE impact; all local commands and final-head checks;
CodeQL alert state; setup performed; application/runtime features explicitly
not implemented; and every scope/secret/production/extra-PR/no-merge
confirmation.

Publish the report atomically, commit it alone, push it, verify the remote
head/first-parent/report-only delta, then send exactly two ASCII bytes `OK` to
`response.fifo` with no newline.
