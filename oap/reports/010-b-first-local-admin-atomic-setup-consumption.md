# OAP Coding-Agent Report — 010-b

## Work order

- Identifier: `010-b`
- Work-order file:
  `oap/orders/010-b-first-local-admin-atomic-setup-consumption.md`
- Numeric objective: `010`
- PR mode: `AMEND_EXISTING_PR`
- PR result: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

PR `#15` now contains the first local human identity/password boundary and an
atomic, code/test-only setup-token consumer. Alembic head `009_001` adds the
constrained `control.user_account` and `control.platform_administrator`
relations plus two narrow owner-created setup functions. A typed Control
adapter operation validates semantic input, hashes the password before taking
the database lock, compares the setup token in application code through the
010-a `secrets.compare_digest` helper, and completes user creation,
administrator assignment, installation initialization, and setup-token
clearing in one transaction.

The exact new runtime dependency is `argon2-cffi==25.1.0` from PyPI. Production
uses `PasswordHasher.from_parameters(RFC_9106_LOW_MEMORY)`: Argon2id version
19, time cost 3, memory cost 65,536 KiB, parallelism 4, 16-byte random salt,
and 32-byte hash. Password input is a bounded `SecretStr`; only a
self-describing hash reaches PostgreSQL. The lock contains hashes for all
artifacts, and generated notices record MIT for `argon2-cffi` and its bindings,
MIT-0 for `cffi`, and BSD-3-Clause for `pycparser`.

Disposable PostgreSQL evidence proves exact ownership/grants/denials, valid
atomic setup, one-use replay failure, malformed/wrong/expired/revoked failure
equivalence, exactly-one concurrent winner, uniqueness rollback with a valid
retry, cancellation rollback, and future OIDC `(issuer, subject)` uniqueness.
The two permitted local integration invocations passed 6 and 30 tests on
PostgreSQL 16.14. Final focused unit/repository verification passed 182 tests
and 22 subtests. Strict mypy, Ruff, compile, repository, migration/package,
license, frozen-install, Compose-configuration, and diff checks passed.

The single GitHub generation passed all 20 checks, including Python 3.12–3.14,
PostgreSQL 14–18, Alpine Compose/edge packaging, Markdown, dependency review,
the full supply-chain/SBOM scan, and all CodeQL analyses. No workflow rerun or
correction commit was needed. The objective-branch open code-scanning alert
count is zero.

No setup/login/logout or user-management route, browser session, cookie, CSRF,
recent-auth, UI, site, membership, capability, publication, OIDC flow/network
behavior, or default Compose issuance/operator wiring was added. Sessions
remain assigned to 010-c; the browser/NGINX/Compose operator flow remains
assigned to 010-d. Local authentication is not browser-usable in this round.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: `15`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- PR state at report time: `OPEN`
- Draft at report time: `false`
- Mergeable at report time: `MERGEABLE`
- Merge state at report time: `CLEAN`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`
- Base branch: `main`
- Starting and final remote base SHA:
  `d4d1c7b7fd27ad2245f0b1224792a252d5274b5c`
- Head branch: `oap/010-installation-local-auth`
- Starting remote/report head:
  `aec0f719042494b9c63a9496204e41fd19326767`
- Implementation commit pushed:
  `85a21636a97f33a5c3c5816fc7939c08250db49c` —
  `OAP 010-b: add atomic initial local administrator`
- Literal 010-b implementation head:
  `85a21636a97f33a5c3c5816fc7939c08250db49c`
- Report publication commit: SELF
- Remote PR head after report publication: SELF
- Implementation-head first parent:
  `aec0f719042494b9c63a9496204e41fd19326767`
- Implementation diff: 30 files, 2,171 insertions, 90 deletions
- New PR created this round: no
- Existing PR amended this round: yes
- Objective-010 PR count: exactly one
- Force push performed: no
- Merge performed: NO
- PR closed: NO
- Auto-merge enabled: NO

GitHub was reconciled before editing and again before the implementation
commit. PR `#15` remained the sole PR with the required objective branch,
title, and base. PRs `#12` and `#13` were not modified, commented on, closed,
rebased, merged, or otherwise acted upon.

## Changes made

### Qualified Argon2 dependency and policy

The runtime dependency baseline now includes exact
`argon2-cffi==25.1.0`. `uv.lock` resolves it only from
`https://pypi.org/simple` and records:

- direct sdist SHA-256:
  `694ae5cc8a42f4c4e2bf2ca0e64e51e23a040c6a517a85074683d3959e1346c1`;
- direct universal wheel SHA-256:
  `fdc8b074db390fccb6eb4a3604ae7231f219aa669a2652e0f20e16ba513d5741`;
- `argon2-cffi-bindings==25.1.0` sdist SHA-256:
  `b957f3e6ea4d55d820e40ff76f450952807013d361a65d7f28acc0acbf29229d`;
  and
- hashed platform-wheel inventories for the bindings and `cffi` across the
  supported Python/platform matrix.

There is no VCS, direct-URL, local-path, or editable dependency. The generated
application inventory classifies `argon2-cffi` and its bindings as MIT,
`cffi==2.1.1` as MIT-0, and `pycparser==3.0` as BSD-3-Clause. MIT-0 was added to
the existing permissive automatic-license list after the initial notice check
correctly rejected the previously unknown new transitive license. Notice
generation, notice check, and supply-chain policy validation then passed.

The strategically authorized direct dependency baseline line in `AGENTS.md`,
package metadata fixtures, repository dependency policy, lockfile, and
`THIRD_PARTY_NOTICES.md` were updated together. No second password library or
hosted identity dependency was added.

### Password and semantic identity service

The new product-owned identity module provides:

- ASCII local usernames matching
  `[A-Za-z][A-Za-z0-9._-]{2,62}`;
- deterministic lowercase normalized usernames shared by Python/PostgreSQL;
- bounded, trimmed display names and optional normalized profile emails;
- `SecretStr` password and setup-token fields excluded from repr and
  serialization;
- a bounded identity result that contains no password hash, setup digest, or
  token; and
- a password service with stable hash, verify, and `check_needs_rehash`
  contracts.

Password policy requires 12–1,024 characters, at most 4,096 UTF-8 bytes,
rejects NUL and equality to the normalized username, and deliberately has no
mandatory character classes. Production constructs the RFC 9106 low-memory
profile directly and exposes no environment/configuration override. Tests can
only lower cost by injecting an explicitly test-owned hasher instance. Correct
and incorrect verification use one boolean contract; library exceptions become
constant safe behavior. The password service is not re-exported from the
identity package root and is imported by no process other than Control's
database implementation.

### Identity persistence and migration

Revision `009_001`, directly after `008_001`, creates exactly the permitted
objects:

- `control.user_account`;
- `control.platform_administrator`;
- `control.slaif_initial_setup_lock()`; and
- `control.slaif_complete_initial_local_administrator(bigint, bytea, uuid,
  text, text, text, text, text)`.

`user_account` has an application-supplied UUID, bounded identity kind and
status, mutable display/email profile data, timestamps, and mutually exclusive
identity shapes. A `LOCAL` row requires the exact ASCII username/normalized
form plus an Argon2id v19 `m=65536,t=3,p=4`, salt-16/hash-32 encoded shape and
cannot contain OIDC keys. An `OIDC` row requires bounded issuer/subject and
cannot contain local username or password hash. Unique constraints cover the
normalized local username and non-null `(oidc_issuer, oidc_subject)`. Email is
not an identity key. Platform Administrator is a separate installation-level
assignment, with no site role on the user relation.

All new relations/functions are owned by `slaif_owner`. `PUBLIC` is revoked.
No runtime/reviewer role receives direct relation access. Function execute is
granted only to `slaif_control`; all other roles are denied. Both functions
are `SECURITY DEFINER`, `VOLATILE`, `PARALLEL UNSAFE`, fixed to
`search_path=pg_catalog`, use fully qualified objects, and contain no dynamic
SQL. Downgrade removes the completion function, lock function, assignment, and
identity relation in dependency order.

### Atomic Control operation

`ControlDatabaseAdapter` exposes one new semantic operation and still exposes
no pool, native connection, generic SQL, execute, or fetch surface. The
operation:

1. receives an already validated typed request and validates/digests token
   shape;
2. validates and hashes the password outside the locked transaction;
3. allocates the UUID through trusted server code;
4. acquires one Control pool connection and opens one transaction;
5. calls the lock function and receives only initialized/expiry/generation plus
   the stored digest;
6. uses the 010-a helper backed by `secrets.compare_digest` for the primary
   application comparison;
7. calls the completion function in the same transaction with expected
   generation and presented digest race guards;
8. inserts one active local user and one Platform Administrator assignment;
9. sets `initialized_at` with `CURRENT_TIMESTAMP` and clears digest, issued,
   and expiry fields atomically; and
10. returns only bounded identity/profile/status/time facts.

The completion function independently locks and rechecks uninitialized state,
token presence, database-clock expiry, generation, and digest before writing.
Malformed, wrong, expired, revoked, replayed, initialized, uniqueness, and
other database failures become exactly `Initial setup failed.` without driver
detail. `CancelledError` is preserved and transaction rollback is allowed to
complete normally.

### Tests, repository policy, and documentation

New unit coverage proves production Argon2 parameters/hash shape/random salts,
correct/wrong verification, rehash behavior, bounded policy, test injection,
constant library failures, username/profile validation, and secret-safe
serialization. Control unit coverage proves the semantic transaction and
arguments, constant wrong-token behavior, UUID ownership, no plaintext in
database arguments, and no raw public surface.

New PostgreSQL integration coverage proves exact migration objects, owners,
function properties/signatures/ACLs, relation denial for every product role,
Control-only setup execution, future OIDC key uniqueness, atomic success,
constant invalid-state failures, replay, concurrency, rollback/retry, and
cancellation. Existing bootstrap, installation, Control, package, health, and
revision-exact tests were updated to `009_001`.

Repository policy requires every new module/migration/test/doc, the exact
dependency, and the Control-only password/consumer import boundary. Static and
runtime route checks still expose only `/health/live` and `/health/ready`.

`docs/LOCAL_AUTHENTICATION.md` records the profile and approximately 64 MiB
per-concurrent-hash operational implication without claiming immutable Python
strings can be wiped. Installation, connection, bootstrap, configuration,
operations, and migration docs distinguish the semantic code/test consumer
from deferred sessions and browser/operator flow.

## Files changed before report publication

- `AGENTS.md`
- `THIRD_PARTY_NOTICES.md`
- `docs/CONFIGURATION.md`
- `docs/DATABASE_BOOTSTRAP.md`
- `docs/DATABASE_CONNECTIONS.md`
- `docs/INSTALLATION_SETUP.md`
- `docs/LOCAL_AUTHENTICATION.md` (new)
- `docs/OPERATIONS.md`
- `migrations/alembic/README.md`
- `oap/active`
- `oap/orders/010-b-first-local-admin-atomic-setup-consumption.md` (new)
- `pyproject.toml`
- `services/backend/src/slaif_agent_site/control_api/database.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/009_001_local_identity.py`
  (new)
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/identity/__init__.py` (new)
- `services/backend/src/slaif_agent_site/identity/models.py` (new)
- `services/backend/src/slaif_agent_site/identity/passwords.py` (new)
- `services/backend/tests/integration/test_control_database_integration.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/integration/test_local_identity.py` (new)
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `services/backend/tests/unit/test_health_apps.py`
- `services/backend/tests/unit/test_identity_password.py` (new)
- `supply-chain/policy.json`
- `tests/repository/test_repository_policy.py`
- `tools/check_repository.py`
- `tools/compose/control_readiness.py`
- `uv.lock`

`test_foundation_contract.py` is a revision/package-metadata compatibility
update explicitly permitted by the work order's revision-exact exception.
`test_health_apps.py` is the minimum Protocol fake update needed when the typed
Control adapter acquired its semantic method. No health route invokes the
operation. This report is the sole additional path in its mandatory
report-only commit.

## Governance and artifact integrity

- `AGENTS.md` pre-authorized-edit SHA-256:
  `9b5995dd14574f853b34c08c0378c901d6b197a3073556c779c6588bd4ac4e4e38`
- `AGENTS.md` final SHA-256 after the explicitly authorized direct-dependency
  baseline edit:
  `dbf75301405937815d65093da30d2ca38fd04e9f8ed198cf56239adc1764e462`
- `OAP-COMMUNICATION-coding-agent.md` SHA-256:
  `e6150d6efb5a64e7f8af29b00514776972d4f98a0632281ddc260110c6374604`
- `ARCHITECTURE.md` SHA-256:
  `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- `SECURITY.md` SHA-256:
  `ec327af34d13406b560f75834d8bbda685f81dad17fd400cce0c5b6b8df4e23c`
- Activated 010-b order SHA-256:
  `b548023ef90eda5f08b888fae5c2c417be1e077d52530a0995c79dbb18180748`
- Preserved 010-a order SHA-256:
  `f0ed7175b183483940d14c1cd4cd207864f2110e945f54485d1ec982c0c7bd26`
- Preserved 010-a report SHA-256:
  `efe9e2d5770d322393b39dec3597001dbc33d6d1b76c4f2a82a40d9c53a0946e`
- Active pointer bytes: exactly `010-b\n` (`30 31 30 2d 62 0a`)

No narrower applicable instruction file exists. The activated order and
active pointer were committed byte-for-byte as supplied by the strategic
model. Protocol, architecture, security policy, 010-a order/report, earlier
OAP artifacts, and unrelated product files remained unchanged.

## Attempt and generation ledger

### Activation and elapsed budget

- Strategic artifact timestamp/activation basis:
  `2026-08-18T01:34:31Z`.
- Implementation committed: `2026-08-18T02:04:01Z`.
- Implementation-head CI completed: `2026-08-18T02:09:24Z`.
- Activation through authoritative green implementation checks: 34m53s,
  within the 45-minute target and 60-minute hard stop.

### Dependency/license attempt

- `uv lock --upgrade-package argon2-cffi`: succeeded and selected exact
  `25.1.0` from PyPI.
- `uv sync --frozen --all-groups`: succeeded.
- Initial generated-notice attempt: failed safely because new transitive
  `cffi` reported MIT-0 and that permissive identifier was not yet in policy.
- In-scope resolution: inspect installed metadata, add MIT-0 to the permissive
  application allowlist, regenerate notices, and retain all four new
  components in attribution.
- Final notice check and supply-chain policy validation: passed.

### Local static/unit attempts

- Initial package/unit/repository selection: 88 passed, 22 subtests passed,
  1 failed in 2.79s.
- Failure: built-wheel metadata expected list omitted the newly added direct
  `argon2-cffi` requirement. The built distribution itself was correct.
- Resolution: update the exact package metadata fixture; repeated selection
  passed 89 tests and 22 subtests in 2.68s.
- An exploratory path-targeted mypy invocation reported six protocol-attribute
  test typing errors and one standalone `conftest` discovery error. The test
  now narrows the injected protocol implementation with `isinstance`; the
  repository's canonical strict `uv run --frozen mypy` command passed with no
  issues in 76 source files.
- A final pre-commit authority tightening removed password-service package-root
  re-exports and expanded repository policy. Its first format check correctly
  reported one blank-line formatting change; Ruff formatted it. Final canonical
  formatting/lint/type/repository checks passed.
- Final focused unit/repository selection on the literal implementation head:
  182 passed, 22 subtests passed in 10.25s.

### PostgreSQL integration invocation 1 of 2

- Exact argv: `uv run --frozen pytest -q
  services/backend/tests/integration/test_local_identity.py`
- Environment: existing disposable local PostgreSQL fixture credential was
  supplied without printing it.
- PostgreSQL: 16.14 on `127.0.0.1:5432`.
- Result: 6 passed in 10.99 seconds.
- Evidence: DDL/owners/grants/denials/OIDC, valid atomic setup, equal bounded
  failures, replay, concurrency, uniqueness rollback/retry, and cancellation.
- Fixture cleanup: passed; disposable databases and test roles were removed.

### PostgreSQL integration invocation 2 of 2

- Exact argv: `uv run --frozen pytest -q
  services/backend/tests/integration/test_installation_setup.py
  services/backend/tests/integration/test_control_database_integration.py
  services/backend/tests/integration/test_database_bootstrap.py`
- Result: 30 passed in 65.16 seconds.
- Evidence: 010-a lifecycle compatibility, Control readiness/identity/denial,
  migration repeat/downgrade/rebuild, marker and role/privilege matrix.
- Fixture cleanup: passed; disposable databases and test roles were removed.

### GitHub check generation 1 of 2 allowed

- Implementation SHA: `85a21636a97f33a5c3c5816fc7939c08250db49c`
- CI run `32090489065`: success; `2026-08-18T02:04:13Z`–
  `2026-08-18T02:09:24Z` (5m11s).
- CodeQL run `32090489196`: success; `2026-08-18T02:04:14Z`–
  `2026-08-18T02:05:20Z` (1m06s).
- All 20 check runs: success.
- Workflow rerun requested: no.
- Second implementation commit/check generation used: no.

Caps used: 1 of 2 implementation commits/check generations, 2 of 2 focused
PostgreSQL integration invocations, and 0 of 1 external-only workflow reruns.

## Acceptance-criteria evidence

### Criterion 1 — amend the unique objective PR only

- Result: PASS
- Evidence: PR `#15` remains the sole objective-010 PR, open and non-draft with
  the exact base/head/title. One normal push amended the existing branch. No
  replacement PR, force push, merge, close, auto-merge, or Dependabot action
  occurred.

### Criterion 2 — qualified exact memory-hard dependency

- Result: PASS
- Evidence: project and lock require exact `argon2-cffi==25.1.0` from PyPI with
  hashed sdist/wheel records. Frozen install, repository dependency policy,
  generated notices, direct/transitive license validation, Python 3.12–3.14
  package jobs, Alpine Compose build, dependency review, and supply-chain
  evidence all passed.

### Criterion 3 — fixed Argon2id profile and bounded secret handling

- Result: PASS
- Evidence: source constructs `PasswordHasher` from
  `RFC_9106_LOW_MEMORY`; unit tests prove v19/m65536/t3/p4/salt16/hash32,
  random salts, correct/wrong verify, rehash behavior, bounded character/byte
  policy, injected test-only cost, and stable exception/non-leak behavior.
  Database parameters contain only the resulting hash.

### Criterion 4 — constrained minimal migration and least privilege

- Result: PASS
- Evidence: offline/package graph and PostgreSQL tests prove single head
  `009_001`, exact two relations/two functions, LOCAL/OIDC shapes and unique
  keys, Argon hash constraint, application UUID, owner, fixed search path,
  `PUBLIC` revoke, exact Control execute grants, no direct table access, all
  other role denial, and downgrade/rebuild/repeat behavior. GitHub PostgreSQL
  14–18 all passed.

### Criterion 5 — atomic one-use setup and fail-closed rollback

- Result: PASS
- Evidence: integration tests prove one valid token creates exactly one active
  LOCAL user and one administrator assignment, initializes once, clears all
  token fields, and returns no hash/digest. Malformed, wrong, expired, revoked,
  replayed, initialized, concurrent-loser, uniqueness, and cancellation paths
  use the bounded failure and preserve transactional state; valid retry after
  uniqueness rollback succeeds.

### Criterion 6 — OIDC key only, no OIDC behavior

- Result: PASS
- Evidence: database tests insert future OIDC-shaped rows, reject duplicate
  `(issuer, subject)`, and prove local/password columns remain null. Source and
  configuration scans show no discovery, callback, provider setting, client,
  network call, or email-as-identity behavior.

### Criterion 7 — later-round exclusions preserved

- Result: PASS
- Evidence: route inventory remains exactly `/health/live` and
  `/health/ready`; source/repository scans show no setup/login/logout route,
  session, cookie, CSRF, recent-auth, user management, UI, site, membership,
  capability, publication, or Compose startup flow. Documentation assigns
  session behavior to 010-c and UI/NGINX/Compose behavior to 010-d.

### Criterion 8 — documentation, checks, alerts, and protocol

- Result: PASS through report publication.
- Evidence: local documentation/repository checks passed and GitHub Markdown
  passed. All 20 implementation-head checks succeeded, open objective-branch
  code-scanning alerts are zero, the report records the literal implementation
  head, and this is the final SELF report commit.

## Local verification

- `uv lock --check`: PASSED — frozen resolution is current.
- `uv sync --frozen --all-groups`: PASSED — 44 packages checked after exact
  lock resolution.
- `uv run --frozen python -m tools.supply_chain.policy notices --check`:
  PASSED — 189 components.
- `uv run --frozen python -m tools.supply_chain.policy validate`: PASSED —
  `supply-chain-policy: OK`.
- Installed metadata inspection: PASSED — `argon2-cffi`/bindings MIT,
  `cffi` MIT-0, `pycparser` BSD-3-Clause.
- `uv run --frozen ruff format --check services/backend tests/repository tools
  migrations`: final PASSED — 89 files already formatted.
- `uv run --frozen ruff check services/backend tests/repository tools
  migrations`: final PASSED.
- `uv run --frozen mypy`: final PASSED — no issues in 76 source files.
- `uv run --frozen python -m compileall -q services/backend/src
  services/backend/tests tests/repository tools migrations`: PASSED.
- Final focused unit/repository command over identity, setup-token, Control and
  shared config/database/health/package/role/authority/entrypoint tests plus
  repository policy: PASSED — 182 tests and 22 subtests in 10.25 seconds.
- PostgreSQL invocation 1: PASSED — 6 passed in 10.99 seconds.
- PostgreSQL invocation 2: PASSED — 30 passed in 65.16 seconds.
- Package build/offline Alembic checks inside the foundation contract suite:
  PASSED — built wheel/sdist contain the new modules and exact direct metadata;
  head/history are `009_001, 008_001, 007_001, 006_001`.
- `uv run --frozen python tools/check_repository.py`: PASSED —
  `PASS repository policy`.
- `uv run --frozen python tools/check_mermaid.py`: PASSED.
- Authority/no-route/no-session source scans: PASSED — password/consumer source
  use is confined to Control database; only two health decorators exist; no
  new setup/login/logout/session/cookie/CSRF source exists.
- Dependency source/hash and setup-token/password-hash literal review: PASSED.
- `docker compose config --quiet`: PASSED; Compose remained unchanged.
- `git diff --check` and staged diff check: PASSED.
- Active-pointer/order/prior-artifact hashes, allowed paths, governance,
  remote-head, PR identity, commit-parent, sole-PR, and clean-worktree checks:
  PASSED.
- Local Markdown linter: NOT RUN — the work order forbids local Node
  invocation; GitHub's required Markdown check passed.
- Local full supply-chain/image/SBOM/Grype gate: NOT RUN — explicitly
  forbidden; GitHub supply-chain evidence passed.
- Local full Compose smoke: NOT RUN — explicitly forbidden; GitHub Compose and
  edge packaging passed.
- Local full Python/PostgreSQL matrices: NOT RUN — explicitly forbidden;
  GitHub Python 3.12–3.14 and PostgreSQL 14–18 passed.
- Local pnpm/Node application suite and Playwright: NOT RUN — explicitly
  forbidden; GitHub Node contracts passed.

No failed, skipped, pending, unavailable, or not-run item above is represented
as passing local evidence.

## GitHub CI / required checks

- CI run: `32090489065` — SUCCESS
- CodeQL run: `32090489196` — SUCCESS
- Implementation head checked:
  `85a21636a97f33a5c3c5816fc7939c08250db49c`
- Analyze (actions): SUCCESS — 43s
- Analyze (javascript-typescript): SUCCESS — 51s
- Analyze (python): SUCCESS — 56s
- CodeQL aggregate: SUCCESS — 2s
- Compose and edge packaging: SUCCESS — 2m39s
- Dependency review: SUCCESS — 5s
- Detect supported languages: SUCCESS — 5s
- Foundation PostgreSQL 14: SUCCESS — 1m10s
- Foundation PostgreSQL 15: SUCCESS — 56s
- Foundation PostgreSQL 16: SUCCESS — 52s
- Foundation PostgreSQL 17: SUCCESS — 54s
- Foundation PostgreSQL 18: SUCCESS — 50s
- Markdown: SUCCESS — 7s
- Mermaid: SUCCESS — 51s
- Node contracts: SUCCESS — 1m11s
- Python 3.12 quality and package: SUCCESS — 25s
- Python 3.13 quality and package: SUCCESS — 30s
- Python 3.14 quality and package: SUCCESS — 34s
- Repository policy: SUCCESS — 11s
- Supply-chain evidence: SUCCESS — 5m07s
- Totals: 20 successful, 0 failed, 0 cancelled, 0 skipped, 0 pending
- All required implementation-head checks green: YES
- Open objective-branch code-scanning alerts: 0
- Workflow reruns requested: 0
- The report-only SELF commit may trigger fresh checks. Those future results
  are not claimed here; the strategic model must independently verify them.

The successful implementation-head supply-chain artifact is:

- Artifact ID: `9308243647`
- Name:
  `supply-chain-evidence-53296f3880307c05214e0a0d625025b239d21a64`
- Size: 1,705,031 bytes
- Created: `2026-08-18T02:09:18Z`
- Expires: `2026-09-01T02:09:16Z`
- Expired at report time: `false`

## Local setup / dependencies

- Exact production dependency added: `argon2-cffi==25.1.0` from PyPI.
- Frozen uv environment updated with `argon2-cffi-bindings==25.1.0`,
  `cffi==2.1.1`, and `pycparser==3.0`; all artifacts are hashed.
- Existing uv `0.12.5` was used for resolution/frozen sync.
- Existing local PostgreSQL 16.14 service was used with disposable fixture
  databases and generated fake test login roles.
- New system package or `sudo`-level setup: none.
- Node package installation: none.
- Docker/Compose mutation: none; configuration parsing only.
- Production system, data, credential, account, or service accessed: none.

## Documentation impact

Created `docs/LOCAL_AUTHENTICATION.md` and updated installation setup,
database connection/bootstrap, configuration, operations, and migration docs.
They document username identity, Argon profile/memory, immutable-string
limitation, atomic transaction/grants, OIDC key-only persistence, and exact
deferred boundaries. They state explicitly that only semantic code/tests can
create the first administrator, no HTTP setup/login route or default issuance
exists, sessions/CSRF/recent-auth wait for 010-c, UI/NGINX/Compose flow waits
for 010-d, and no OIDC authentication exists.

Generated attribution now includes the direct password dependency and all new
transitive application components/licenses. No documentation claims browser-
usable authentication, production readiness, or strategic acceptance.

## Safety and scope confirmations

- Unrelated feature/refactor work: no.
- Expected-path exceptions: only the revision/package contract test and health
  Protocol fake noted above; both were directly necessary and bounded.
- Activated order or `oap/active` authored/modified by coding agent: NO; both
  strategic artifacts were committed byte-for-byte.
- Earlier OAP artifact edited: NO.
- Governance edited: only the work-order-authorized exact direct dependency
  baseline line in `AGENTS.md`; architecture, protocol, and security remained
  unchanged.
- Real secret, setup token, digest, DSN, password, hash tied to a real secret,
  cookie, session, private URL, or production data printed or committed: no.
- Fake deterministic token/password material exposed in normal test output: no.
- Password/setup token in URL, environment, cookie, log, exception, repr,
  serialization, fixture literal, or database plaintext: no.
- Direct runtime/reviewer relation access: no.
- Password/consumer authority imported outside Control database: no.
- Agent/editor/reader/reviewer/scheduler/media/GC identity or setup authority
  added: no.
- Session, cookie, CSRF, recent-auth, route, UI, OIDC flow, site, membership,
  capability, publication, or Compose startup behavior added: no.
- Dependency and lockfile changed: yes, exactly the authorized Argon2 package
  plus its registry-resolved permissive transitive dependencies and evidence.
- Workflow, Dockerfile, image definition, service topology, architecture,
  security policy, or OAP protocol changed: no.
- PostgreSQL integration cap exceeded: NO — exactly 2 invocations.
- Implementation/check-generation cap exceeded: NO — 1 of 2 used.
- GitHub workflow rerun: NO.
- Local forbidden full supply-chain/image, full Compose, full matrix, Node, or
  Playwright run: NO.
- Destructive reset/clean/checkout, broad prune, force push, extra objective PR,
  merge, close, or auto-merge: NO.
- PR `#12` or `#13` acted upon: NO.
- Report-publication commit changes only this report file: yes.

## Known limitations / blockers

- None within activated 010-b scope.
- The semantic operation has no HTTP caller. There is no usable setup or login
  route, server-side session, cookie, CSRF, recent-auth, user-management UI,
  default issuance, or NGINX/Compose operator flow yet.
- OIDC support is limited to persistence constraints for a future stable key;
  there is no provider configuration, discovery, callback, validation, or
  network behavior.
- `COMPLETE` means the requested remote state and implementation-head evidence
  exist. It does not mean strategic acceptance and does not authorize this
  coding agent to merge.

## Recommended strategic follow-up

Independently verify this SELF report commit and first parent, the exact
Argon2 profile/dependency hashes/licenses, `009_001` constraints and function
grants, application-side constant-time proof plus database race guards,
success/replay/concurrency/rollback/cancellation evidence, single green check
generation, zero alerts, exact caps, sole-PR correlation, and preserved 010-a
artifacts. The strategic model alone decides whether to activate 010-c on PR
`#15`; no merge is authorized by this report.
