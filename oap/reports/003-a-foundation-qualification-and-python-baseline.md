# OAP Coding-Agent Report — 003-a

## Work order

- Identifier: `003-a`
- Work-order file:
  `oap/orders/003-a-foundation-qualification-and-python-baseline.md`
- Numeric objective: `003`
- PR mode: `CREATED_NEW_PR`

## Status

COMPLETE

## Executive summary

Qualified the architecture-selected, non-yanked PyPI distribution
`agent-cow-postgresql==0.2.0` and added the minimal reproducible Python
backend package baseline. The final implementation head has an exact uv
`0.12.5` lock containing the verified foundation wheel and source-distribution
hashes, a deliberately small public-API adapter boundary, metadata/package and
repository-policy tests, and a disposable downstream PostgreSQL adoption test.

Fresh frozen installs and the unit/metadata/repository suite passed on CPython
3.12.3, 3.13.15, and 3.14.7. The integration suite passed locally and on
GitHub against PostgreSQL 14, 15, 16, 17, and 18. The implementation-head
GitHub inventory contained sixteen completed successful checks, including all
Python/PostgreSQL matrix rows, Dependency Review, Mermaid, Markdown, repository
policy, and CodeQL Actions/Python analysis. No Agent-Site service, product
schema, API, UI, Compose stack, or publication behavior was added.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: `4`
- PR URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/4`
- PR state at report time: `OPEN`
- PR title: `[OAP 003] Qualify foundation and add Python baseline`
- PR readiness at report time: non-draft (`draft: false`)
- PR mergeability at report time: `MERGEABLE`; merge-state status `CLEAN`
- Auto-merge request: none
- Base branch: `main`
- Head branch: `oap/003-foundation-python-baseline`
- Starting remote SHA: `c2038f0c14ac9eba5ca997fe3ae1a343e1869fd4`
- Implementation head SHA: `a90c3eb52ca9f856e86c658ab077520eadfec9a7`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (literal SHA derived from
  GitHub)
- Implementation commits pushed before the report commit:
  `a90c3eb52ca9f856e86c658ab077520eadfec9a7` (`OAP 003: qualify
  foundation and add Python baseline`)
- Report commit first parent: same as Implementation head SHA
- Created a new PR this turn: yes, exactly PR `#4`
- Amended existing PR this turn: no
- Merge performed: NO

## Changes made

- Added one root PEP 621 project at internal pre-alpha version `0.0.0`, with
  Python `>=3.12,<3.15`, Apache-2.0 metadata, the source root under
  `services/backend/src`, and the sole exact production requirement
  `agent-cow-postgresql==0.2.0`.
- Selected the permissively licensed exact build backend `uv_build==0.12.5`
  and bounded direct development groups for build, qualification, quality,
  and testing.
- Generated `uv.lock` with exact uv `0.12.5`. It has nineteen package records,
  resolves the foundation only from `https://pypi.org/simple`, and contains
  the verified PyPI wheel and source-distribution artifact hashes.
- Added `slaif_agent_site.agent_state.foundation`, which directly re-exports
  only the qualified documented `agentcow.postgres` symbols and records an
  explicit public inventory. It does not implement SQL, policy, credentials,
  connection state, transaction wrappers, private storage coupling, or a
  canonical-write escape.
- Added unit/metadata tests for exact installed versions, public imports,
  adapter AST/source constraints, Python compatibility, PEP 621/build
  metadata, registry-only lock integrity, and exact wheel/sdist contents and
  metadata.
- Added a disposable asyncpg/PostgreSQL adoption test with separate generated
  setup/runtime/reviewer roles. It covers deploy, schema enablement with unsafe
  canonical writes off, privilege hardening/validation, isolated workspace
  mutation, canonical state before review, operation/dependency/conflict
  inspection, full promotion/discard, missing context, runtime canonical-base
  denial, reviewer denial, cancellation rollback, and pooled context cleanup.
- Added Python 3.12/3.13/3.14 quality/package CI and PostgreSQL 14–18
  integration CI. Exact `astral-sh/setup-uv` and uv versions are pinned;
  existing repository, Markdown, Mermaid, Dependency Review, and CodeQL
  workflows remain present.
- Extended repository policy and negative fixtures for the setup-uv pin,
  required baseline files, exact foundation version/registry/artifacts/hashes,
  and rejected Git/VCS, direct URL, local path, editable, missing version,
  missing hash, wrong hash, and unapproved registry cases.
- Added grouped weekly root pip Dependabot proposals while preserving the
  GitHub Actions entry. Dependency automation remains a proposal and does not
  qualify a foundation upgrade.
- Added the foundation integration record and updated README, NOTICE, AGENTS,
  and CONTRIBUTING to distinguish the implemented package baseline from all
  still-planned product/runtime behavior and to preserve MIT downstream/
  upstream attribution.

## Files changed

The final PR diff against the starting `main` contains exactly these twenty
paths:

- `.github/dependabot.yml`
- `.github/workflows/ci.yml`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `NOTICE`
- `README.md`
- `docs/FOUNDATION_INTEGRATION.md`
- `oap/active`
- `oap/orders/003-a-foundation-qualification-and-python-baseline.md`
- `oap/reports/003-a-foundation-qualification-and-python-baseline.md`
- `pyproject.toml`
- `services/backend/src/slaif_agent_site/__init__.py`
- `services/backend/src/slaif_agent_site/agent_state/__init__.py`
- `services/backend/src/slaif_agent_site/agent_state/foundation.py`
- `services/backend/tests/conftest.py`
- `services/backend/tests/integration/test_foundation_postgres.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `tests/repository/test_repository_policy.py`
- `tools/check_repository.py`
- `uv.lock`

## Foundation and dependency evidence

- PyPI version: `0.2.0`; observed non-yanked.
- Foundation `Requires-Python`: `>=3.10,<3.15`; product range:
  `>=3.12,<3.15`.
- Foundation license expression: MIT.
- Foundation unconditional requirements: none.
- Foundation optional `sqlalchemy` extra: `sqlalchemy>=2.0.0` and
  `asyncpg>=0.29.0`; this product does not select that extra.
- Qualified wheel:
  `agent_cow_postgresql-0.2.0-py3-none-any.whl`, SHA-256
  `c469d24700fabb93a58f464d3539a32e936097f93035a95f193062859546f5b1`.
- Qualified source distribution: `agent_cow_postgresql-0.2.0.tar.gz`,
  SHA-256
  `eae8d434d2fc03c4faa08b44b4863fc8f8efb44ee33eaad3adc22e7eb96a062c`.
- Foundation PyPI registry source: `https://pypi.org/simple`; artifact URLs
  are immutable files.pythonhosted.org records in `uv.lock`.
- Downstream source/provenance:
  `https://github.com/jpers1/agent-cow-postgresql`.
- Upstream attribution: `https://github.com/trail-ml/agent-cow-python`.
- Locked records: `agent-cow-postgresql==0.2.0`, `asyncpg==0.31.0`,
  `build==1.5.0`, `colorama==0.4.6` (conditional), `iniconfig==2.3.0`,
  `librt==0.15.0`, `mypy==1.20.2`, `mypy-extensions==1.1.0`,
  `packaging==25.0`, `pathspec==1.1.1`, `pluggy==1.6.0`,
  `pygments==2.21.0`, `pyproject-hooks==1.2.0`, `pytest==9.1.1`,
  `pytest-asyncio==1.4.0`, `ruff==0.16.3`,
  `slaif-agent-site==0.0.0`, `typing-extensions==4.16.0`, and
  `uv-build==0.12.5`.
- Installed metadata license evidence: Agent-Site `Apache-2.0`, foundation
  `MIT`, asyncpg `Apache-2.0`, uv-build `MIT OR Apache-2.0`.

## Public API / adapter inventory

The adapter's exact documented-public inventory is:

- `CowConflict`
- `CowConflictError`
- `CowPostgresConfig`
- `CowPrivilegeValidation`
- `CowReviewer`
- `CowSession`
- `DiscardResult`
- `PromotionResult`
- `asyncpg_cow_reviewer`
- `asyncpg_cow_session`
- `deploy_cow_functions`
- `enable_cow_schema`
- `get_cow_conflicts`
- `get_operation_dependencies`
- `get_session_operations`
- `harden_cow_schema`
- `validate_cow_schema_privileges`

Whole-session and selective operation promotion/discard remain documented
methods of the public `CowReviewer` scope. The adapter does not wrap or alter
transaction ownership or the default `conflict_policy="error"` behavior.

## Package artifact evidence

- `uv build` produced `slaif_agent_site-0.0.0-py3-none-any.whl` and
  `slaif_agent_site-0.0.0.tar.gz` from the frozen environment.
- Wheel code contents were exactly the three intended package files:
  `slaif_agent_site/__init__.py`,
  `slaif_agent_site/agent_state/__init__.py`, and
  `slaif_agent_site/agent_state/foundation.py`, plus standard dist-info,
  LICENSE, and NOTICE metadata.
- Source-distribution files were exactly LICENSE, NOTICE, README, PKG-INFO,
  normalized/original build metadata, and those same three source files. It
  contained no test, OAP, cache, environment, coverage, key, or secret file.
- Built wheel metadata: name `slaif-agent-site`, version `0.0.0`, license
  expression `Apache-2.0`, Python `>=3.12,<3.15`, and the sole requirement
  `agent-cow-postgresql==0.2.0`.

## Acceptance-criteria evidence

### Criterion 1 — one exact non-draft PR and twenty-path final scope

- Result: PASSED.
- Evidence: GitHub PR `#4` is OPEN, non-draft, based on `main`, headed by
  `oap/003-foundation-python-baseline`, and titled exactly as ordered.
  Auto-merge is absent. The implementation diff had nineteen exact paths; the
  report-only `SELF` commit adds the twentieth and no other path.

### Criterion 2 — frozen Python 3.12–3.14 installs

- Result: PASSED.
- Evidence: independent new environments at
  `/tmp/slaif-oap003-python-final/python-3.12`, `python-3.13`, and
  `python-3.14` each completed `uv sync --frozen --all-groups` and the complete
  36-test/13-subtest unit/metadata/repository suite without lock mutation.
  GitHub Python 3.12, 3.13, and 3.14 quality/package matrix rows also completed
  successfully.

### Criterion 3 — exact registry-only foundation lock

- Result: PASSED.
- Evidence: `pyproject.toml` has exactly
  `agent-cow-postgresql==0.2.0`; the locked foundation package has only the
  approved PyPI registry source and the two exact artifact hashes above.
  Policy and contract tests reject/scan for forbidden source forms.

### Criterion 4 — documented public API and preserved semantics

- Result: PASSED.
- Evidence: AST/import identity tests validate the exact public inventory.
  Adapter source checks found no SQL verbs, native access, private base/change
  storage name, or private dotted symbol. It directly re-exports foundation
  objects and adds no transaction or conflict wrapper.

### Criterion 5 — PostgreSQL 14–18 adoption behavior

- Result: PASSED.
- Evidence: locally, four integration tests passed independently on each of
  PostgreSQL 14, 15, 16, 17, and 18. GitHub's five named foundation matrix rows
  all completed successfully. The tests cover every bounded behavior named in
  the work order, including negative privileges/context and cancellation/pool
  cleanup.

### Criterion 6 — intended package artifacts and attribution

- Result: PASSED.
- Evidence: product wheel/sdist built and exact-content tests passed. Metadata
  is pre-alpha `0.0.0`, Apache-2.0, Python `>=3.12,<3.15`, and one exact
  foundation requirement. NOTICE and the foundation record preserve MIT and
  both downstream/upstream provenance links.

### Criterion 7 — repository-policy negative fixtures

- Result: PASSED.
- Evidence: 30 isolated unittest cases passed. Pytest reported 36 total tests
  and 13 subtests for the combined unit/metadata/repository suite. Fixtures
  reject Git/VCS, direct URL, local path, editable, missing/wrong version,
  missing/wrong wheel/sdist hash, and unapproved registry forms.

### Criterion 8 — honest documentation

- Result: PASSED.
- Evidence: README, FOUNDATION_INTEGRATION, NOTICE, AGENTS, and CONTRIBUTING
  record the implemented foundation/Python baseline and commands while
  explicitly stating that no runnable product, API, Compose stack, product
  schema/roles, UI, or publication behavior exists.

### Criterion 9 — final implementation-head GitHub checks

- Result: PASSED.
- Evidence: at `2026-08-17T11:03:23Z`, raw GitHub check runs for literal
  implementation head `a90c3eb52ca9f856e86c658ab077520eadfec9a7` contained
  sixteen completed successful checks, listed below. No implementation-head
  check was failed, skipped, cancelled, missing, or pending. Open CodeQL alerts:
  zero.

### Criterion 10 — governance and earlier objectives preserved

- Result: PASSED.
- Evidence: `ARCHITECTURE.md`, `OAP-COMMUNICATION-coding-agent.md`, and every
  objective `000`–`002` order/report were byte-unchanged from `origin/main`.
  Strategic `oap/active` SHA-256 remained
  `f0790e558c38b566eac604bb97517eb2a26ac6c9a2c8ddc0f06e456160edf09d`;
  strategic order SHA-256 remained
  `3c88f8ee732396a4af4bd126a385c281788a9dab92b6649172070a5e1e100d50`.
  The active identifier is `003-a`, with one order and one final report.

### Criterion 11 — report-only `SELF` topology

- Result: PASSED by publication construction.
- Evidence: this immutable report records literal implementation head
  `a90c3eb52ca9f856e86c658ab077520eadfec9a7` and publication commit `SELF`.
  Its containing commit has that implementation head as first parent, changes
  only this report, and is pushed as the remote PR head before FIFO response.

### Criterion 12 — safety and bounded scope

- Result: PASSED.
- Evidence: exact twenty-path scope; focused diff secret scan passed; only fake
  disposable database credentials/data were used; no production or hosted
  runtime was accessed; no product service/schema/UI, non-permissive
  dependency, extra PR, merge, or auto-merge was introduced.

## Local verification

- `uv --version`: PASSED — `uv 0.12.5
  (x86_64-unknown-linux-gnu)`.
- `uv lock --check`: PASSED — resolved nineteen package records without
  changing `uv.lock`.
- `uv sync --frozen --all-groups`: PASSED — current environment checked all
  eighteen installed dependencies plus the editable product package.
- fresh `UV_PROJECT_ENVIRONMENT=... uv sync --frozen --all-groups --python
  3.12|3.13|3.14`: PASSED — new CPython 3.12.3, 3.13.15, and 3.14.7
  environments.
- corresponding fresh-environment `uv run --frozen pytest
  services/backend/tests/unit tests/repository -q`: PASSED on each Python —
  `36 passed, 13 subtests passed` on each interpreter.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository
  tools`: PASSED — eight included files already formatted; two unchanged
  legacy Mermaid implementation/test files are explicitly excluded because
  they were outside this exact-path work order.
- `uv run --frozen mypy`: PASSED — six source files checked with no issues.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 36 tests.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  30 tests.
- PostgreSQL 14 command, with fake PG environment and disposable Docker port
  `55414`, `uv run --frozen pytest services/backend/tests/integration -q`:
  PASSED — four tests.
- Equivalent PostgreSQL 15 command on port `55415`: PASSED — four tests.
- Equivalent PostgreSQL 16 command on port `55416`: PASSED — four tests.
- Equivalent PostgreSQL 17 command on port `55417`: PASSED — four tests.
- Equivalent PostgreSQL 18 command on port `55418`: PASSED — four tests.
- `uv build --out-dir /tmp/slaif-oap003-precommit-build`: PASSED — wheel and
  source distribution built.
- package wheel/sdist content and metadata inspection: PASSED — exact bounded
  contents and metadata stated above.
- `uv tree --frozen --all-groups --depth 2`: PASSED — deterministic direct and
  transitive inventory matched `uv.lock`.
- installed metadata license/dependency inspection with
  `importlib.metadata`: PASSED — evidence stated above.
- `sha256sum` on the two downloaded PyPI distributions: PASSED — exact hashes
  matched the work order and lock.
- `python -m compileall -q tools tests/repository services/backend`: PASSED.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 12 diagrams in two files; 21
  Markdown files scanned; Mermaid CLI 11.16.0.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 26 files, zero
  issues.
- Ruby YAML load of `.github/workflows/ci.yml` and
  `.github/dependabot.yml`: PASSED.
- `git diff --check`: PASSED.
- exact changed-path union before report: PASSED — nineteen ordered paths;
  final report adds only the twentieth permitted path.
- prior architecture/protocol/objectives `000`–`002` comparison with
  `origin/main`: PASSED — unchanged.
- focused high-signal diff secret scan: PASSED — no match.
- adapter SQL/private/native scan and public inventory import: PASSED.
- PR identity/base/head/title/draft/auto-merge/remote SHA query: PASSED.
- raw implementation-head GitHub check-run inventory: PASSED — every observed
  check completed successfully.
- CodeQL open-alert API query: PASSED — zero open alerts.

Development iterations retained for accuracy:

- `python -m pip install --user uv==0.12.5`: FAILED before implementation
  testing because Debian's PEP 668 externally-managed environment rejected
  direct pip installation. The agent installed exact uv with pipx instead.
- Initial combined pytest collection: FAILED with two import errors because
  repository root was not on pytest's import path. Added the explicit root
  `pythonpath`; the next run collected tests.
- Next combined pytest run: FAILED three assertions covering normalized
  `Requires-Python`, wheel directory entries, and a README-policy fixture.
  Tests were corrected to validate semantic metadata and exact file entries;
  every subsequent final run passed.
- Initial PostgreSQL 18 integration run: FAILED four tests because a
  session-scoped async fixture and function-scoped tests used different event
  loops. Set the explicit pytest async test loop scope to session; PostgreSQL
  18 and the complete 14–18 final matrix then passed.
- Initial Markdown check: FAILED one trailing blank-line issue in the new
  foundation document. Removed it; the final check reported zero issues.

## GitHub CI / required checks

- Check state observed for implementation head:
  `a90c3eb52ca9f856e86c658ab077520eadfec9a7` — all sixteen raw check
  runs completed `success`.
- `Detect supported languages`: SUCCESS — 4 seconds.
- `Analyze (actions)`: SUCCESS — 40 seconds.
- `Analyze (python)`: SUCCESS — 46 seconds.
- `CodeQL`: SUCCESS — 2 seconds.
- `Dependency review`: SUCCESS — 8 seconds.
- `Repository policy`: SUCCESS — 7 seconds.
- `Markdown`: SUCCESS — 7 seconds.
- `Mermaid`: SUCCESS — 49 seconds.
- `Python 3.12 quality and package`: SUCCESS — 15 seconds.
- `Python 3.13 quality and package`: SUCCESS — 12 seconds.
- `Python 3.14 quality and package`: SUCCESS — 14 seconds.
- `Foundation PostgreSQL 14`: SUCCESS — 28 seconds.
- `Foundation PostgreSQL 15`: SUCCESS — 22 seconds.
- `Foundation PostgreSQL 16`: SUCCESS — 27 seconds.
- `Foundation PostgreSQL 17`: SUCCESS — 23 seconds.
- `Foundation PostgreSQL 18`: SUCCESS — 24 seconds.
- CI workflow run: `32022898763`.
- CodeQL workflow run: `32022898790`.
- Open CodeQL alerts at report drafting: zero.
- All required checks green for the implementation head at report drafting:
  yes; no observed final implementation-head check was failed, skipped,
  cancelled, missing, or pending.
- Report-only commit may trigger fresh checks: strategic model must verify the
  `SELF` commit without rewriting this report.

## Local setup / dependencies

- Packages/tools/services installed or configured: Debian `pipx` plus its
  system dependencies; pipx-managed exact uv `0.12.5`; uv-managed CPython
  3.13.15 and 3.14.7; locked Python development environment; downloaded PyPI
  foundation wheel/sdist in `/tmp`; temporary product build artifacts in
  `/tmp`; PostgreSQL Docker images 14–18 for disposable local matrix testing.
- Existing versions used: system CPython 3.12.3, Docker 29.1.3, PostgreSQL
  client 16.14, Node/npm through the existing Mermaid/Markdown gates.
- `sudo`-level setup performed: `sudo apt-get install -y -qq pipx` installed
  pipx and Debian dependencies including `python3-venv`,
  `python3-argcomplete`, `python3-platformdirs`, `python3-userpath`, and
  `python3-psutil`; `sudo docker` created the five explicitly named disposable
  test containers.
- Cleanup: explicitly removed containers `slaif-oap003-pg14` through
  `slaif-oap003-pg18`, including their disposable database state. No
  repository build artifact or downloaded distribution was created.
- Durable setup changes committed/documented: `pyproject.toml`, `uv.lock`, CI,
  Dependabot, adapter/tests, repository policy, and documentation only.

## Documentation

- Added `docs/FOUNDATION_INTEGRATION.md` with exact PyPI artifacts and hashes,
  supported matrices, public API reliance, logical live-base semantics,
  ownership/authentication boundaries, commands, upgrade gate, attribution,
  and deferred hardening limitations.
- Changed NOTICE from planned use to exact integrated dependency and retained
  downstream/upstream MIT attribution.
- Updated README current status, delivery sequence, repository map, CI gates,
  Dependabot behavior, and explicit absence of a runnable product.
- Updated AGENTS and CONTRIBUTING with exact frozen install, lint, format,
  type, unit, integration, and build commands, plus the rule that later work
  extends rather than weakens these gates.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no.
- Production systems accessed: no.
- Hosted runtime/account-bound service used: no.
- Real external service used for product behavior: no; only PyPI/GitHub
  package/project metadata and the authorized repository were accessed.
- Required tests skipped/not run: no.
- Local PostgreSQL versions missing: no; all five ran and passed.
- GitHub checks missing/pending/failed/cancelled/skipped at implementation
  report drafting: no.
- Scope deviation: no.
- New application service, product schema/role, API, UI, Compose, browser,
  media, or publication behavior introduced: no.
- Foundation source checkout used by normal build/tests: no.
- Forbidden foundation dependency source used: no.
- New non-permissive dependency introduced: no.
- Activated order and `oap/active` bytes preserved: yes.
- Previous architecture/protocol/order/report artifacts changed: no.
- Extra PR created for same numeric objective: NO.
- PR merged by coding agent: NO.
- Auto-merge enabled by coding agent: NO.
- Activated order and `oap/active` edited by coding agent: NO.
- Report-publication commit changes only this report file: yes.

## Known limitations / blockers

- No blockers for this bounded objective.
- This is a foundation/package adoption gate, not a runnable Agent-Site
  implementation. FastAPI services, product database roles/schemas,
  capability authorization, immutable review snapshots, exhaustive
  privilege/conflict/concurrency/cancellation/promotion coverage, REST/MCP,
  Puck/UI, browser/media workers, Compose/NGINX, and publication remain
  intentionally deferred.
- `agent-cow-postgresql` settings remain trusted database context rather than
  caller authentication. Future product services must select site,
  workspace/session, and operation UUIDs after server-side authorization and
  must not expose raw SQL or `CowSession.native`.
- Report-only `SELF` may trigger fresh GitHub checks; their state is not
  predicted in this immutable report.

## Recommended strategic follow-up

Independently verify the `SELF` commit topology, exact twenty-path PR diff,
report-head checks, and architecture/public-API boundary. The strategic model
alone decides whether to merge, request a bounded continuation, abandon, or
escalate.
