# OAP Coding-Agent Report — 009-a

## Work order

- Identifier: `009-a`
- Work-order file:
  `oap/orders/009-a-control-database-readiness-boundary.md`
- Numeric objective: `009`
- PR mode: `CREATE_NEW_PR`
- PR result: `CREATED_NEW_PR`

## Status

PARTIAL

## Executive summary

PR `#14` wires the first online database authority only into Control API. One
isolated read-only file supplies `slaif_control_login`; a Control-owned frozen
settings model and bounded asyncpg lifespan pool verify the database, login,
and exact sole `slaif_control` membership on every new connection. Alembic head
`007_001` adds one zero-argument, owner-defined, read-only readiness function
and no table or product behavior. Control liveness stays process-only while
readiness validates the exact packaged head, safe bootstrap marker, and pinned
foundation identity through that function.

Focused local tests and one PostgreSQL 16.14 run passed. The third permitted
local database/Compose attempt could not start because the ordinary VM user
lacked Docker-socket access; the budget prohibited rerunning it with verified
working passwordless `sudo`. The first GitHub Compose generation exposed and
the one permitted corrective commit fixed a real isolated-volume ownership
ordering defect without adding a capability.

On final implementation head
`f8c87dbead42383f7f810a3ba8ff631a04e14a04`, clean Compose startup, Control
database readiness, mount baseline, edge headers, login policy, all PostgreSQL
14–18 gates, every Python/Node/repository/documentation gate, supply-chain
evidence, and CodeQL passed. The corrected Compose job then failed inside the
targeted fixture immediately after printing
`control-readiness-stage: wrong-login`. The fixture deliberately suppresses
subprocess output, so GitHub does not identify the exact failing subcommand.
The two-implementation-commit/check-generation cap is exhausted; a third fix
is forbidden. Final state is therefore 19 successful checks, one failed check,
zero open CodeQL alerts, and this mandatory `PARTIAL` report.

No setup, authentication, identity, user, session, site, workspace,
capability, content, review, publication, or other product route was added.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: `14`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/14>
- PR state at report time: `OPEN`
- Draft at report time: `false`
- Mergeable at report time: `MERGEABLE`
- Merge state at report time: `UNSTABLE` because one check failed
- Required title:
  `[OAP 009] Wire Control API database readiness boundary`
- Base branch: `main`
- Starting and current remote base SHA:
  `ab3db28f573b62130b93ae082a196e8ca9f8b424`
- Head branch: `oap/009-control-database-readiness`
- Starting branch SHA:
  `ab3db28f573b62130b93ae082a196e8ca9f8b424`
- Implementation head SHA:
  `f8c87dbead42383f7f810a3ba8ff631a04e14a04`
- Report publication commit: SELF
- Remote PR head after report publication: SELF
- Implementation commits pushed before the report commit:
  - `07c389ee589383472b540b80aeb0544a8bc0382f` —
    `Wire Control database readiness boundary`
  - `f8c87dbead42383f7f810a3ba8ff631a04e14a04` —
    `Initialize isolated Control secret before ownership transfer`
- Implementation diff: 34 files, 2,956 insertions, 142 deletions
- Force push performed: no
- Merge performed: NO
- Auto-merge enabled: NO
- PRs `#12` and `#13` modified or otherwise acted on: NO

GitHub search and PR metadata showed exactly one objective-009 PR with the
required base, head, title, open state, and non-draft state. The PR body records
the final 19/1 check state, corrective commit, exhausted caps, and unresolved
fixture stage.

## Changes made

### Isolated Control credential

- Added the `control-secret` named volume.
- The networkless one-shot initializer copies only the already generated
  `service-control-dsn` value to `control-dsn`; it neither changes nor prints
  that value.
- A fresh empty mount remains root-owned only until its single file is created
  and transferred to UID 10001. Final directory policy is `0700` and
  `10001:10001`; final file policy is `0400` and UID 10001.
- Repeated initialization compares the isolated value with the master source
  and fails closed on mismatch.
- Control mounts only `/run/slaif-control` read-only. It does not mount the
  administrator password, provisioner/owner locators, master secret directory,
  another service locator, host paths, or Docker socket.
- No other long-running process mounts the isolated file or loads the
  `SLAIF_CONTROL_` prefix.

### Typed settings and pool lifecycle

- Added frozen `ControlDatabaseSettings` inside `control_api`, separate from
  shared `ServiceSettings`.
- Development/production require an absolute file. Explicit test mode alone
  permits a direct local or `.test` fake locator.
- Pool size, connect/acquire/command/shutdown timeouts, idle lifetime,
  statement/lock/idle-transaction limits, application name, database, login,
  role, and locator sources are bounded and validated.
- Production requires `sslmode=verify-full`, an absolute `sslrootcert`, and
  explicit `target_session_attrs=read-write`; untrusted session options and
  identity weakening are rejected.
- Locator values remain `SecretStr` and configuration failures are constant.
- `ControlDatabase` creates its asyncpg pool only inside the package-local app
  lifespan. Its per-connection initializer verifies database, session user,
  current user, and exact effective membership of only `slaif_control` among
  every product role.
- The adapter exposes only `start`, `stop`, and the typed readiness probe; no
  raw pool, arbitrary SQL, task registry, or global locator was added.
- Normal, timeout, exception, and cancellation shutdown paths are bounded.
- `python -m slaif_agent_site.control_api --check` validates both typed models
  without reading the locator file, opening a network connection, creating a
  pool, binding a port, or mutating state.

### Migration, grants, and readiness

- New deterministic Alembic head: `007_001`, after `006_001`.
- Added exactly one function:
  `control.slaif_control_readiness()`.
- The function is zero-argument, SQL `STABLE`, `PARALLEL RESTRICTED`,
  `SECURITY DEFINER`, owned by `slaif_owner`, and fixed to
  `search_path=pg_catalog`; all relations are fully qualified.
- It returns only schema revision, marker revision/state/safety, and foundation
  distribution/version. It reads only owner-controlled version/marker state
  and performs no write.
- `PUBLIC` execute is revoked. Only `slaif_control` receives schema usage and
  function execute. It receives no direct marker/version-table access.
- The product privilege reconciler preserves exactly that surface, and the
  independent verifier checks owner, search path, security-definer state,
  exact grant, denial matrix, and function count.
- Downgrade removes the function and the Control schema usage grant.
- `/health/live` remains database-independent. `/health/ready` contains one
  `database` component and exposes only bounded reasons:
  `configuration_invalid`, `connection_unavailable`, `identity_mismatch`,
  `role_mismatch`, `migration_mismatch`, `unsafe_marker`,
  `foundation_mismatch`, `timeout`, or `shutdown`.
- NGINX startup and ongoing health include proxied Control readiness.

### Tests, policy, fixture, and documentation

- Added Control settings, pool, health/lifespan, migration/function, role
  denial, and live integration coverage.
- Added a bounded targeted Compose fixture for clean readiness, exact mount and
  unrelated-UID denial, wrong login, wrong role, unreadable file, unsafe
  marker, migration mismatch, stopped PostgreSQL, recovery, and NGINX
  behavior. It is invoked by the existing full CI smoke.
- Updated static Compose policy and repository inventory/link policy for the
  exact new files and boundary.
- Added `docs/DATABASE_CONNECTIONS.md` and updated current-state configuration,
  bootstrap, roles, deployment, operations, service-authority, migration, and
  README documentation.
- No dependency, lockfile, Dockerfile, workflow, image, supply-chain policy,
  architecture, security, protocol, content-schema, or foundation-package
  change was made.

## Files changed before report publication

- `README.md`
- `compose.yaml`
- `docs/CONFIGURATION.md`
- `docs/DATABASE_BOOTSTRAP.md`
- `docs/DATABASE_CONNECTIONS.md` (new)
- `docs/DATABASE_ROLES.md`
- `docs/DEPLOYMENT.md`
- `docs/OPERATIONS.md`
- `docs/SERVICE_AUTHORITY.md`
- `migrations/alembic/README.md`
- `oap/active`
- `oap/orders/009-a-control-database-readiness-boundary.md` (new)
- `services/backend/src/slaif_agent_site/application.py`
- `services/backend/src/slaif_agent_site/control_api/__main__.py`
- `services/backend/src/slaif_agent_site/control_api/app.py`
- `services/backend/src/slaif_agent_site/control_api/config.py` (new)
- `services/backend/src/slaif_agent_site/control_api/database.py` (new)
- `services/backend/src/slaif_agent_site/db/alembic/versions/007_001_control_readiness.py`
  (new)
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/tests/integration/test_control_database_integration.py`
  (new)
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/unit/test_control_config.py` (new)
- `services/backend/tests/unit/test_control_database.py` (new)
- `services/backend/tests/unit/test_foundation_contract.py`
- `services/backend/tests/unit/test_health_apps.py`
- `services/backend/tests/unit/test_process_entrypoints.py`
- `tests/packaging/test_compose_policy.py`
- `tests/packaging/test_local_secrets.py`
- `tests/repository/test_repository_policy.py`
- `tools/check_repository.py`
- `tools/compose/control_readiness.py` (new)
- `tools/compose/smoke.sh`
- `tools/compose/verify.py`
- `tools/local_secrets/initialize.py`

Every path is within the activated order's allowed scope.

## Governance integrity

The governing sources remained byte-identical:

- `AGENTS.md` SHA-256:
  `9b5995dd14574f853b34c08c0378c901d6b197a3073556c779c6588bd4ac4e4e38`
- `OAP-COMMUNICATION-coding-agent.md` SHA-256:
  `e6150d6efb5a64e7f8af29b00514776972d4f98a0632281ddc260110c6374604`
- `ARCHITECTURE.md` SHA-256:
  `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- `SECURITY.md` SHA-256:
  `ec327af34d13406b560f75834d8bbda685f81dad17fd400cce0c5b6b8df4e23c`
- Activated order SHA-256:
  `35ec043c1b40867137523d4377d47f0365c068816a2c563347f9916af2b5f132`

No narrower applicable `AGENTS.md` or `AGENTS.override.md` exists.

## Focused database / Compose attempt ledger

### Attempt 1 — focused PostgreSQL 16.14

- Start: `2026-08-17T22:39:05Z`
- End: `2026-08-17T22:39:13Z`
- Duration: 8 seconds
- Exit: 1
- Command:
  `PGPASSWORD=qualification-admin PGHOST=127.0.0.1 PGPORT=5432 PGDATABASE=qualification PGUSER=postgres uv run --frozen pytest -q services/backend/tests/integration/test_control_database_integration.py services/backend/tests/integration/test_database_bootstrap.py::test_clean_migration_current_repeat_downgrade_and_rebuild`
- Result: 2 passed, 2 failed.
- Cause 1: the new ACL assertion omitted PostgreSQL's inherent explicit owner
  execute entry; database truth was owner plus the sole non-owner
  `slaif_control` grant.
- Cause 2: the pre-existing repeat test observed a transient 65 ms host-clock
  reversal in `updated_at`; all verifier state before that assertion passed.
- Subsequent change: corrected the test to assert the exact owner plus Control
  ACL. No product change or clock workaround was introduced.

### Attempt 2 — focused PostgreSQL 16.14 rerun

- Start: `2026-08-17T22:39:49Z`
- End: `2026-08-17T22:39:58Z`
- Duration: 9 seconds
- Exit: 0
- Command: identical to attempt 1.
- Result: 4 passed in 7.62 seconds.
- Subsequent change: none; focused database evidence was green.

### Attempt 3 — targeted local Compose fixture

- Start: `2026-08-17T22:44:18Z`
- End: `2026-08-17T22:44:19Z`
- Duration: under 1 second
- Exit: 1
- Command: `python tools/compose/control_readiness.py slaif009local`
- Stage reached: none; it failed before `control-readiness-stage: baseline`.
- Cause: the ordinary local user could not access the Docker socket.
  Read-only diagnosis showed unprivileged `docker info` was denied while
  `sudo docker info` succeeded against Docker Engine 29.1.3.
- Cleanup: the exact fixture cleanup ran; a read-only audit found no
  `slaif009local` container, volume, or network.
- Subsequent change/rerun: none. The work-order cap prohibited a fourth
  database/Compose attempt, including a `sudo` rerun.

Maximum attempts reached: yes, exactly 3. Status is therefore necessarily
`PARTIAL` even apart from the final CI failure.

## GitHub check-generation ledger

### Implementation generation 1

- Head: `07c389ee589383472b540b80aeb0544a8bc0382f`
- Ordinary CI run: `32078349833`
- CodeQL run: `32078349890` — SUCCESS
- Compose result: FAILURE during initial startup because `secrets-init` exited
  1 before PostgreSQL started.
- Root cause: a new empty Docker volume is already an existing root-owned
  mount. The initializer transferred the directory to UID 10001 before writing
  its file, then lacked write authority under its intentionally narrow
  `CHOWN` plus `DAC_READ_SEARCH` capability set.
- Corrective change: commit
  `f8c87dbead42383f7f810a3ba8ff631a04e14a04` keeps an empty mount root-owned
  through file creation, transfers the file and directory afterward, fails on
  unexpected nonempty state, adds a mounted-directory-shape regression test,
  and does not add `DAC_OVERRIDE`, `FOWNER`, or another capability.
- The new push cancelled only the still-running supply-chain job from this
  superseded generation; completed jobs were not represented as final-head
  evidence.

### Implementation generation 2 — final implementation head

- Head: `f8c87dbead42383f7f810a3ba8ff631a04e14a04`
- Ordinary CI run: `32078665032` — FAILURE due one job
- CodeQL run: `32078665058` — SUCCESS
- Corrective evidence: `secrets-init`, PostgreSQL/bootstrap, Control pool,
  Control and NGINX health, static/live topology, edge headers, database-login
  policy, secret-file policy, and targeted fixture baseline all passed.
- Residual failure: after the exact line
  `control-readiness-stage: wrong-login`, the targeted fixture emitted only
  `control-readiness-fixture: FAILED` and exited. The fixture catches
  `FixtureError` and intentionally discards child output, so the authoritative
  log cannot distinguish its file-replacement, Control-recreation, readiness,
  liveness, or NGINX assertion substep.
- Cleanup: the outer smoke has an exact-project `EXIT` trap that runs Compose
  `down --volumes --remove-orphans` for its positive and negative project
  names. No broad prune exists.
- Subsequent change: none; both allowed implementation commits/check
  generations were consumed. A third implementation commit is forbidden.

## Acceptance-criteria evidence

### Criterion 1 — one required non-draft PR

- Result: PASS
- Evidence: exactly one open, non-draft objective-009 PR exists as `#14`, with
  base `main`, required branch/title, two bounded implementation commits, and
  the versioned order/pointer. No merge or auto-merge occurred.

### Criterion 2 — one isolated Control credential/authority

- Result: PARTIAL
- Evidence: static policy, packaging tests, clean Compose initialization, the
  targeted fixture baseline, and Control readiness passed. They prove the sole
  mount, final ownership/modes, no master mount/environment locator, and exact
  Control login/role at baseline. The fixture failed when beginning its wrong-
  login mutation, so the complete live negative sequence is not passing
  evidence.

### Criterion 3 — bounded lifespan-owned pool

- Result: PASS
- Evidence: unit tests prove import/check mode is connection-free, settings
  and pool bounds are applied, exact identity/combined-role rejection works,
  acquire/start/close timeout and cancellation paths are sanitized, no raw
  adapter methods exist, and lifespan exceptions close. Final clean Compose
  reached `database=ok`.

### Criterion 4 — sole narrow migration function

- Result: PASS
- Evidence: focused PostgreSQL 16.14 and all GitHub PostgreSQL 14–18 gates
  passed function owner, `SECURITY DEFINER`, `search_path=pg_catalog`, stable/
  parallel behavior, exact owner plus Control ACL, denial matrix, no direct
  marker read, packaged head, repeat/downgrade/rebuild, and no product table.

### Criterion 5 — truthful sanitized health

- Result: PASS for unit/integration and clean baseline; PARTIAL for the full
  Compose failure sequence.
- Evidence: unit/integration tests passed liveness/readiness split, exact
  marker/migration/foundation facts, stable reasons, timeout, and shutdown.
  Clean Compose proved Control and proxied NGINX ready. The fixture did not
  finish every requested negative state.

### Criterion 6 — complete Compose success/failure fixture

- Result: FAIL
- Evidence: clean startup and baseline passed, but final GitHub Compose job
  failed immediately after entering `wrong-login`; later wrong role, unreadable
  secret, marker, migration, stopped-database, and recovery stages did not run.

### Criterion 7 — other boundaries remain green

- Result: PASS for every independently executed gate.
- Evidence: static topology denies Control settings/mounts to siblings; all
  Python, Node, repository, edge baseline, dependency, and supply-chain gates
  passed. No dependency/image/workflow/security policy changed. The one failed
  Compose fixture prevents a claim that the complete topology gate is green.

### Criterion 8 — 20 green checks and zero alerts

- Result: FAIL
- Evidence: 19 succeeded, one failed, zero pending/skipped/cancelled on the
  final implementation head. Open repository and objective-branch CodeQL alert
  counts were both zero.

### Criterion 9 — exact documentation/pre-alpha claim

- Result: PASS
- Evidence: affected Markdown passed locally and in GitHub. Documentation
  states the exact Control-only connection, grant, mount, TLS, lifecycle,
  health, failure, and future-process pattern while retaining pre-alpha,
  fresh-install-only, and no-auth/product-route limitations.

### Criterion 10 — OAP correlation/protocol

- Result: PASS through report publication.
- Evidence: `oap/active` is exactly `009-a\n`; exactly one matching immutable
  order and this one report exist; prior artifacts are unchanged; the report
  is a final report-only SELF commit whose first parent is the literal
  implementation head.

## Local verification

- Focused new unit/packaging bundle for Control configuration, pool, health,
  entrypoint, package graph, local secrets, and Compose policy: PASSED —
  100 passed, 2 subtests passed.
- `uv run --frozen pytest -q services/backend/tests/unit tests/repository
  tests/packaging`: PASSED — 197 passed, 39 subtests passed in 10.91 seconds.
- `uv run --frozen pytest -q services/backend/tests/unit/test_control_config.py
  services/backend/tests/unit/test_control_database.py
  services/backend/tests/unit/test_health_apps.py
  services/backend/tests/unit/test_process_entrypoints.py`: PASSED — 81 passed
  in 8.62 seconds after the final production-locator tightening.
- `uv run --frozen pytest -q tests/packaging/test_local_secrets.py
  tests/packaging/test_compose_policy.py`: PASSED — 11 passed, 2 subtests
  passed after the corrective ownership-order change.
- Focused PostgreSQL command and result: see attempt ledger — final rerun 4
  passed in 7.62 seconds on PostgreSQL 16.14.
- `uv run --frozen ruff check` on all affected Python paths: PASSED.
- `uv run --frozen ruff format --check` on all affected Python paths: PASSED —
  final checks reported 30 files formatted and later affected subsets clean.
- `uv run --frozen mypy`: PASSED — no issues in 66 source files.
- An earlier unsupported file-list-only mypy invocation failed because the
  repository test layout produced duplicate basename/untyped installed-package
  diagnostics. The integration test received a unique basename; the supported
  repository-wide mypy command above passed and is the authoritative result.
- `python tools/check_repository.py`: PASSED — `PASS repository policy`.
- `docker compose config --quiet`: PASSED.
- `python tools/compose/verify.py --root .`: PASSED — `compose-policy: OK`.
- `sh -n tools/compose/smoke.sh`: PASSED.
- `python -m py_compile tools/compose/control_readiness.py
  tools/compose/verify.py tools/local_secrets/initialize.py`: PASSED.
- `env -u SLAIF_CONTROL_DSN -u SLAIF_CONTROL_DSN_FILE uv run --frozen python
  -m slaif_agent_site.control_api --check`: PASSED —
  `control-api: CHECK_OK` without a locator read or connection.
- Initial `pnpm exec markdownlint-cli2 ...`: NOT RUN — command unavailable in
  the installed workspace, exit 1.
- Initial ephemeral Markdown invocation without `--no-globs`: INVALID LOCAL
  INVOCATION — repository options expanded into generated/dependency trees and
  reported third-party errors; no product file was changed from that output.
- `npx --yes markdownlint-cli2@0.20.0 --no-globs` on the 10 affected Markdown
  files: PASSED — 10 files, 0 errors.
- `git diff --check`: PASSED before each implementation commit.
- Final branch, remote SHA, active pointer, order hash, report-collision,
  staged-scope, and allowed-path checks: PASSED.
- Local full `tools/supply_chain/run.sh`: NOT RUN — explicitly forbidden.
- Local six-image reproducibility/SBOM/Grype gate: NOT RUN — explicitly
  forbidden.
- Local full Compose smoke: NOT RUN — explicitly forbidden.
- Local full Python 3.12–3.14 matrix: NOT RUN — explicitly forbidden.
- Local full PostgreSQL 14–18 matrix: NOT RUN — explicitly forbidden; only
  PostgreSQL 16.14 ran locally.

No skipped, unavailable, invalid, pending, or failed command above is
represented as passing evidence.

## GitHub CI / required checks

- Ordinary CI run: `32078665032` — FAILURE
- CodeQL run: `32078665058` — SUCCESS
- Check state observed for implementation head:
  `f8c87dbead42383f7f810a3ba8ff631a04e14a04`
- Analyze (actions): SUCCESS — 39s
- Analyze (javascript-typescript): SUCCESS — 1m2s
- Analyze (python): SUCCESS — 51s
- CodeQL aggregate: SUCCESS — 2s
- Dependency review: SUCCESS — 7s
- Detect supported languages: SUCCESS — 6s
- Foundation PostgreSQL 14: SUCCESS — 1m14s
- Foundation PostgreSQL 15: SUCCESS — 50s
- Foundation PostgreSQL 16: SUCCESS — 47s
- Foundation PostgreSQL 17: SUCCESS — 47s
- Foundation PostgreSQL 18: SUCCESS — 53s
- Markdown: SUCCESS — 6s
- Mermaid: SUCCESS — 49s
- Node contracts: SUCCESS — 1m6s
- Python 3.12 quality and package: SUCCESS — 32s
- Python 3.13 quality and package: SUCCESS — 33s
- Python 3.14 quality and package: SUCCESS — 36s
- Repository policy: SUCCESS — 7s
- Compose and edge packaging: FAILURE — 1m26s
- Supply-chain evidence: SUCCESS — 4m47s
- Totals: 19 successful, 1 failed, 0 cancelled, 0 skipped, 0 pending
- All required checks green: NO
- Open repository CodeQL alerts: 0
- Open objective-branch CodeQL alerts: 0
- The report-only SELF commit may trigger fresh checks. Those future results
  are not claimed here and cannot repair the known implementation-head failure.

The successful final-head supply-chain artifact is:

- Artifact ID: `9304436480`
- Name:
  `supply-chain-evidence-277f622e056af41f274405b215cb8ce0c97d8869`
- Size: 1,673,993 bytes
- Created: `2026-08-17T23:06:44Z`
- Expires: `2026-08-31T23:06:43Z`
- Expired at report time: `false`

## Local setup / dependencies

- The existing frozen uv environment and local PostgreSQL 16.14 qualification
  service were used; no dependency or lockfile changed.
- `npx --yes markdownlint-cli2@0.20.0` populated only the ordinary local npm
  execution cache; no repository dependency or lockfile changed.
- Read-only Docker diagnosis used ordinary `docker info` and `sudo docker
  info`; no container or Compose rerun followed and no host configuration was
  changed.
- New package/system dependency installation: none.
- Durable setup change: none.
- Local supply-chain/image build: none.

## Documentation impact

`docs/DATABASE_CONNECTIONS.md` now owns the complete Control connection
contract: mount/role identity, local versus production TLS, settings, bounded
pool/session lifecycle, readiness function, stable failure behavior, and the
requirements another process must satisfy before receiving a credential.

README, configuration, database bootstrap/roles, deployment, operations,
service-authority, and Alembic source documentation now reflect the one
implemented Control-only online boundary. They continue to state that setup,
authentication, users, sessions, sites, product routes, and publication do not
exist and that the stack is pre-alpha/fresh-install-only.

## Safety and scope confirmations

- Unrelated files changed: no.
- Changes outside the activated allowed path families: no.
- Earlier OAP order/report edited: NO.
- Activated order or `oap/active` authored/modified by coding agent: NO; both
  strategic artifacts were committed byte-for-byte.
- Production secrets, systems, credentials, or data accessed: no.
- Real DSN/password/token/cookie/private artifact URL printed or committed:
  no; tests use fake/disposable values and health/log output is sanitized.
- Production dependency or lockfile changed: no.
- Dockerfile, workflow, image pin, scanner, notice, exception, architecture,
  security, protocol, content schema, or foundation package changed: no.
- Setup/auth/user/session/site/workspace/capability/content/review/publication
  behavior added: no.
- Agent/editor/reader/reviewer/scheduler/media/GC/Web/MCP/browser database
  credential or pool added: no.
- Raw SQL/product route/global pool registry added: no.
- Local work-order attempt cap exceeded: NO — exactly 3 database/Compose
  attempts.
- Implementation commit/check-generation cap exceeded: NO — exactly 2 before
  this mandatory report-only commit.
- Local full supply-chain, full Compose smoke, or full matrix run performed:
  NO.
- Broad reset, clean, checkout, prune, or destructive cleanup performed: no.
- Extra objective-009 PR created: NO.
- PR `#12` or `#13` acted on: NO.
- Force push performed: NO.
- PR merged by coding agent: NO.
- Auto-merge enabled by coding agent: NO.
- Report-publication commit changes only this report file: yes.

## Known limitations / blockers

- The targeted Compose fixture fails immediately after entering the
  `wrong-login` stage. Because its safe wrapper suppresses child output, the
  exact failed subcommand is not remotely observable from this generation.
- The wrong-login, wrong-role, unreadable-secret, unsafe-marker,
  migration-mismatch, stopped-PostgreSQL, NGINX-negative, and recovery sequence
  is therefore incomplete passing evidence. Only clean baseline behavior is
  proven in the final Compose run.
- Local Docker verification could not start under the ordinary user, and the
  three-attempt cap prohibited using the verified sudo path for a fourth run.
- Both permitted implementation commits/check generations are consumed. A new
  strategic amendment is required to authorize further diagnosis and repair.
- The repository remains pre-alpha; successful health, database, scanner, and
  supply-chain evidence is not authentication, product readiness,
  certification, publication authority, or deployment approval.

## Recommended strategic follow-up

Activate a bounded objective-009 amendment that permits one diagnostic
Compose run with the available passwordless-sudo Docker path and one corrective
commit. Temporarily preserve safe fixture diagnostics that identify only the
failed stage/subcommand category—not subprocess output, locator, password, or
driver text—then repair and rerun the complete wrong-login through recovery
sequence. Independently verify this SELF report commit, its first parent, the
single-PR correlation, and the known failed check before deciding acceptance.
The coding agent has not merged or enabled auto-merge.
