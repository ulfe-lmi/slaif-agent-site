# OAP Coding-Agent Report — 010-a

## Work order

- Identifier: `010-a`
- Work-order file:
  `oap/orders/010-a-installation-state-setup-token-foundation.md`
- Numeric objective: `010`
- PR mode: `CREATE_NEW_PR`
- PR result: `CREATED_NEW_PR`

## Status

COMPLETE

## Executive summary

PR `#15` establishes only the owner-controlled installation-state and
setup-token issuance foundation. Alembic head `008_001` adds one constrained
singleton `control.installation_state` relation. The one-shot bootstrap owner
can ensure, rotate, revoke, or inspect a setup token through a row-locked
transactional service and explicit CLI command. No runtime role receives table
access.

Tokens use the fixed public prefix `slaif_setup_v1_` plus 32 bytes/256 bits of
cryptographic randomness encoded as 43 unpadded URL-safe Base64 characters.
Only a 32-byte SHA-256 digest and database-clock timestamps are persisted.
Plaintext remains a `SecretStr`, is excluded from result representation and
serialization, and is intentionally unwrapped only for one labeled stdout line
after successful issue or rotation.

Focused tests prove initial issue, repeated ensure without disclosure,
concurrent single issuance, expiry without sleeping, atomic rotation, old-token
invalidation, idempotent revoke, bounded status, initialized-state failure,
migration lifecycle, and denial to every runtime/reviewer role. PostgreSQL
integration invocation 1 passed 30 tests on local PostgreSQL 16.14. Invocation
2 passed the directly corrected initialized-state test.

The first GitHub CI generation exposed one strict-mypy issue in an integration
test's tuple of unannotated async lambdas. A bounded second implementation
commit replaced that test loop with three explicit awaited calls. Full local
strict mypy and the affected PostgreSQL test passed, and the second GitHub
generation passed all 20 checks. No workflow rerun was requested. Repository
and objective-branch open CodeQL alert counts are zero.

No user, password, token consumer, initialization action, session, cookie,
CSRF, route, UI, site, membership, identity provider, or Compose startup wiring
was added. First-user consumption remains assigned to `010-b`; HTTP setup and
default startup wiring remain assigned to `010-d` on this same unmerged PR.

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
- Starting objective branch: absent locally and remotely
- Initial implementation commit:
  `edf5fbb77cc2331a57dde86c85839cc6aaffc407` —
  `Establish installation setup-token foundation`
- Correction commit:
  `179e347e57f9e9544a1dc3dcc799b90b6cbf01ac` —
  `Type initialized setup lifecycle checks`
- Literal 010-a implementation head:
  `179e347e57f9e9544a1dc3dcc799b90b6cbf01ac`
- Report publication commit: SELF
- Remote PR head after report publication: SELF
- Implementation-head first parent:
  `edf5fbb77cc2331a57dde86c85839cc6aaffc407`
- Initial implementation first parent:
  `d4d1c7b7fd27ad2245f0b1224792a252d5274b5c`
- Implementation diff: 22 files, 1,467 insertions, 43 deletions
- New PR created this round: exactly one
- Force push performed: no
- Merge performed: NO
- PR closed: NO
- Auto-merge enabled: NO

GitHub was checked before branch creation: the required branch did not exist
and objective-010 PR search returned none. PRs `#12` and `#13` were not
modified, commented on, closed, rebased, merged, or otherwise acted upon.

## Changes made

### Installation-state migration

Revision `008_001`, directly after `007_001`, creates only
`control.installation_state` and seeds its one uninitialized row. Its columns
are:

- `singleton boolean` primary key with a true-only constraint;
- nullable `initialized_at timestamptz`;
- nullable `setup_token_digest bytea`;
- nullable `setup_token_issued_at timestamptz`;
- nullable `setup_token_expires_at timestamptz`;
- non-null `setup_token_generation bigint` defaulting to zero; and
- non-null `updated_at timestamptz` using the database clock.

Named database constraints enforce a true singleton, exactly 32 digest bytes,
all-null/all-present token material, expiry later than issuance, no token on an
initialized installation, and a non-negative generation. The migration assigns
ownership to `slaif_owner`, revokes `PUBLIC`, adds no grant or function, and
downgrades by dropping only this table.

The clean privilege inventory now expects this owner-only relation in
`EMPTY_SAFE` and future `HARDENED` states. Existing generic validation still
rejects any runtime/reviewer relation privilege. Integration tests proved
every non-owner product role receives `InsufficientPrivilegeError` for both
read and mutation and proved an injected `slaif_control` grant makes validation
unsafe.

### Cryptographic token contract

`bootstrap/setup_token.py` provides:

- generation through `secrets.token_bytes(32)` with an injectable test
  boundary;
- a strict ASCII prefix/shape validator before SHA-256 digesting;
- a pure digest helper returning exactly 32 bytes;
- `secrets.compare_digest` verification with fail-closed malformed inputs; and
- constant public-safe validation errors that never include presented input.

No dependency was added. Tests generate deterministic tokens at runtime from
injected bytes; no valid fixed token literal or plaintext snapshot is
committed.

### Owner-only lifecycle

`ensure_setup_token`, `rotate_setup_token`, and `revoke_setup_token` use
`owner_connection`, one PostgreSQL transaction per mutation, and
`SELECT ... FOR UPDATE` before deciding. Issuance/expiry uses
`CURRENT_TIMESTAMP`; configured lifetime is bounded to 5–60 minutes with a
30-minute default.

- Ensure issues and increments generation only if no unexpired token exists.
  Otherwise it returns bounded facts without generating or revealing a token.
- Rotate replaces the digest atomically, advances generation, and returns only
  the new plaintext once.
- Revoke clears digest/issued/expiry without initializing and repeated revoke
  is idempotent.
- Status returns only initialized, token-present, token-expired, expiry, and
  generation facts.
- Issue, rotate, and revoke fail closed once `initialized_at` is non-null.
  No 010-a function sets `initialized_at`.

`SetupTokenResult` excludes its `SecretStr` field from repr and Pydantic
serialization. It has no digest field.

### Explicit CLI and configuration

`python -m slaif_agent_site.bootstrap setup-token` defaults to ensure and has
mutually exclusive `--rotate`, `--revoke`, and `--status` actions. A fresh
plaintext appears exactly once on its own `setup-token-secret:` stdout line.
The separately validated absolute HTTP(S) `/setup` URL has no credentials,
query, or fragment and is printed on its own line without the token. Existing
unexpired state emits bounded recovery guidance requiring explicit rotation.
Failures retain the constant `Database bootstrap failed.` stderr contract.

`python -m slaif_agent_site.bootstrap --check` still returns before loading
settings, connecting, generating randomness, mutating, or printing a secret.
The setup command is not connected to default Compose startup.

### Tests, repository policy, and documentation

New focused unit and PostgreSQL integration suites cover cryptography,
secret-safe models, configuration, CLI output, migration constraints,
ownership, denial, privilege drift, lifecycle, concurrency, and non-leakage.
Migration-head compatibility fixtures were updated from `007_001` to
`008_001`.

The repository checker requires the new module, migration, tests, and
`docs/INSTALLATION_SETUP.md`. Database bootstrap, configuration, operations,
and Alembic documentation now describe the implemented foundation and clearly
state that no token consumer, first administrator, served `/setup` handler, or
automatic startup issuance exists. The committed work order and verified PR
body explicitly assign later behavior to `010-b` and `010-d` on the same PR.

## Files changed before report publication

- `docs/CONFIGURATION.md`
- `docs/DATABASE_BOOTSTRAP.md`
- `docs/INSTALLATION_SETUP.md` (new)
- `docs/OPERATIONS.md`
- `migrations/alembic/README.md`
- `oap/active`
- `oap/orders/010-a-installation-state-setup-token-foundation.md` (new)
- `services/backend/src/slaif_agent_site/bootstrap/__main__.py`
- `services/backend/src/slaif_agent_site/bootstrap/config.py`
- `services/backend/src/slaif_agent_site/bootstrap/service.py`
- `services/backend/src/slaif_agent_site/bootstrap/setup_token.py` (new)
- `services/backend/src/slaif_agent_site/db/alembic/versions/008_001_installation_state.py`
  (new)
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/tests/integration/test_control_database_integration.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/integration/test_installation_setup.py` (new)
- `services/backend/tests/unit/test_bootstrap_setup_token.py` (new)
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `tests/repository/test_repository_policy.py`
- `tools/check_repository.py`
- `tools/compose/control_readiness.py`

The Control database unit/integration tests, foundation contract, and Compose
readiness fixture are outside the expected path list but directly necessary to
keep the existing revision-exact lower-layer contract at new head `008_001`.
No Control authority, route, topology, or product behavior changed. This report
is the sole additional path in its mandatory report-only commit.

## Governance and artifact integrity

- `AGENTS.md` SHA-256:
  `9b5995dd14574f853b34c08c0378c901d6b197a3073556c779c6588bd4ac4e4e38`
- `OAP-COMMUNICATION-coding-agent.md` SHA-256:
  `e6150d6efb5a64e7f8af29b00514776972d4f98a0632281ddc260110c6374604`
- `ARCHITECTURE.md` SHA-256:
  `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- `SECURITY.md` SHA-256:
  `ec327af34d13406b560f75834d8bbda685f81dad17fd400cce0c5b6b8df4e23c`
- Activated 010-a order SHA-256:
  `f0ed7175b183483940d14c1cd4cd207864f2110e945f54485d1ec982c0c7bd26`
- Active pointer bytes: exactly `010-a\n` (`30 31 30 2d 61 0a`)

No narrower applicable instruction file exists. Governance, prior OAP orders,
prior reports, and all objective-009 product files outside the explicit
revision-compatibility updates remained unchanged.

## Attempt and generation ledger

### Local verification attempt 1

- Repository policy: passed.
- Initial broad unit/repository run: 179 passed, 22 subtests passed, 1 failed
  in 10.61 seconds.
- Failure: a test asserted that the empty malformed input string was absent
  from a constant error string; the empty string is mathematically contained
  in every string. Production behavior was correct.
- Direct test-only correction: condition that non-leak assertion on non-empty
  malformed inputs.
- Focused token suite after correction: 14 passed in 0.09 seconds.
- Final broad unit/repository run: 180 passed, 22 subtests passed in 9.98
  seconds.

### PostgreSQL integration invocation 1 of 2

- Exact argv: `uv run pytest -q
  services/backend/tests/integration/test_database_bootstrap.py
  services/backend/tests/integration/test_installation_setup.py
  services/backend/tests/integration/test_control_database_integration.py`
- Environment: existing disposable local PostgreSQL fixture credential was
  supplied without printing it.
- PostgreSQL: 16.14 on `127.0.0.1:5432`.
- Result: 30 passed in 62.78 seconds.
- Fixture cleanup: passed through fixture teardown; disposable databases and
  login roles were removed.

### GitHub check generation 1 of 2

- Implementation SHA: `edf5fbb77cc2331a57dde86c85839cc6aaffc407`
- Started: `2026-08-18T01:14:01Z`
- CI run: `32087473544`; later cancelled automatically after correction push.
- CodeQL run: `32087473571`; success, completed at `01:15:09Z`.
- Direct evidence: Python 3.12/3.13/3.14 jobs each failed strict mypy in
  18–19 seconds at
  `test_installation_setup.py:207: Call to untyped function (unknown) in typed
  context [no-untyped-call]`.
- Workflow rerun requested: no.

### Direct correction and PostgreSQL invocation 2 of 2

- Change: replace the untyped async-lambda loop with three explicit awaited
  lifecycle calls; no production source or assertion semantics changed.
- `uv run mypy`: success, no issues in 70 source files.
- Exact integration argv: `uv run pytest -q
  services/backend/tests/integration/test_installation_setup.py::test_issue_repeat_rotate_expire_revoke_and_initialized_lifecycle`
- Result: 1 passed in 1.40 seconds.
- Correction SHA: `179e347e57f9e9544a1dc3dcc799b90b6cbf01ac`
- Committed: `2026-08-18T01:15:48Z`.

### GitHub check generation 2 of 2

- Implementation SHA: `179e347e57f9e9544a1dc3dcc799b90b6cbf01ac`
- CI run `32087595637`: success; `01:16:00Z`–`01:20:39Z`.
- CodeQL run `32087595643`: success; `01:16:00Z`–`01:17:12Z`.
- All 20 check runs: success.
- Workflow rerun requested: no.

Caps used: 2 of 2 implementation commits/check generations, 2 of 2 focused
PostgreSQL invocations, and 0 of 1 permitted external-only workflow reruns.

## Acceptance-criteria evidence

### Criterion 1 — exactly one new objective PR

- Result: PASS
- Evidence: PR `#15` is the sole objective-010 PR, open and non-draft with the
  exact required title/base/head. Its branch started at verified remote main.
  No force push, extra PR, merge, close, auto-merge, or action on PR `#12` or
  `#13` occurred.

### Criterion 2 — singleton migration and zero runtime access

- Result: PASS
- Evidence: migration/static/integration tests prove one head, exact columns,
  constraints, row, owner, downgrade/rebuild/repeat-upgrade behavior, no user
  or session relation/function, `PUBLIC` revoke, all-role denial, and
  fail-closed privilege validation. GitHub PostgreSQL 14–18 all passed.

### Criterion 3 — 256-bit digest-only token contract

- Result: PASS
- Evidence: generation requests exactly 32 random bytes from `secrets`, the
  versioned format is strictly validated, SHA-256 produces the only persisted
  token representation, comparison uses `compare_digest`, and only the
  explicit one-shot owner result can carry masked plaintext.

### Criterion 4 — transactional lifecycle and concurrency

- Result: PASS
- Evidence: every mutation locks the singleton in one transaction and uses the
  database clock. Integration tests prove ensure, exactly-one concurrent issue,
  repeat, expiry, rotate, old-digest invalidation, revoke/idempotence, status,
  generation, and initialized-state failure without sleeps.

### Criterion 5 — non-leakage

- Result: PASS
- Evidence: plaintext is excluded from repr/serialization/database/status and
  occurs once only in the intentional fresh CLI stdout line. Shape/error, URL,
  locator, digest, existing/revoke/status output, and committed token-literal
  scans passed.

### Criterion 6 — no later-round behavior

- Result: PASS
- Evidence: `--check` remains side-effect-free and scans/source review show no
  consumer, initialization setter, user/password, session/CSRF, route/UI,
  identity, site, or Compose wiring.

### Criterion 7 — honest documentation

- Result: PASS
- Evidence: new installation setup documentation plus updated bootstrap,
  configuration, operations, and migration docs distinguish the implemented
  issuance foundation from planned consumption, first administrator, served
  `/setup`, and startup issuance. The committed order and PR body explicitly
  map these to `010-b` and `010-d` on the same unmerged PR.

### Criterion 8 — GitHub checks, alerts, and protocol

- Result: PASS through report publication.
- Evidence: all 20 implementation-head checks passed; repository and branch
  open CodeQL alerts are zero. This report is a final SELF commit whose first
  parent is the literal implementation head.

## Local verification

- `uv run ruff format --check services/backend/src services/backend/tests
  tests/repository tools`: PASSED — 80 files already formatted.
- `uv run ruff check services/backend/src services/backend/tests
  tests/repository tools`: PASSED.
- `uv run mypy` after the direct correction: PASSED — no issues in 70 source
  files.
- Earlier targeted source-only mypy: PASSED — no issues in 53 source files.
- `uv run python tools/check_repository.py`: PASSED —
  `PASS repository policy`.
- `uv run pytest -q services/backend/tests/unit
  tests/repository/test_repository_policy.py`: final PASSED — 180 passed and
  22 subtests passed in 9.98 seconds.
- PostgreSQL invocation 1: PASSED — 30 passed in 62.78 seconds.
- PostgreSQL invocation 2: PASSED — 1 passed in 1.40 seconds.
- `uv run python -m compileall -q services/backend/src
  services/backend/tests tests/repository tools`: PASSED.
- `uv run python -m slaif_agent_site.bootstrap --check`: PASSED — exact stdout
  `bootstrap: CHECK_OK`.
- Migration graph assertion: PASSED — head/history exactly
  `008_001, 007_001, 006_001`.
- Setup-token-shaped literal scan: PASSED — no 43-character token-shaped
  literal after the public prefix.
- New secret-sink pattern scan: PASSED.
- No-later-round source scan: PASSED.
- `docker compose config --quiet`: PASSED; Compose remained unchanged.
- `git diff --check` and staged diff check: PASSED.
- Active-pointer/order hash, allowed-path, governance, remote-head, PR
  identity, commit-parent, and clean-worktree checks: PASSED.
- Local Markdown linter: NOT RUN — the CLI is not installed and the order
  forbids a Node install; GitHub's required Markdown check passed.
- Local full supply-chain/image/SBOM/Grype gate: NOT RUN — explicitly
  forbidden; GitHub supply-chain evidence passed.
- Local full Compose smoke: NOT RUN — explicitly forbidden.
- Local full Python/PostgreSQL matrices: NOT RUN — explicitly forbidden.
- Local Node install/build/test and Playwright: NOT RUN — explicitly
  forbidden.

No failed, skipped, pending, unavailable, or not-run item above is represented
as passing local evidence.

## GitHub CI / required checks

- CI run: `32087595637` — SUCCESS
- CodeQL run: `32087595643` — SUCCESS
- Implementation head checked:
  `179e347e57f9e9544a1dc3dcc799b90b6cbf01ac`
- Analyze (actions): SUCCESS — 36s
- Analyze (javascript-typescript): SUCCESS — 1m2s
- Analyze (python): SUCCESS — 51s
- CodeQL aggregate: SUCCESS — 3s
- Compose and edge packaging: SUCCESS — 2m51s
- Dependency review: SUCCESS — 7s
- Detect supported languages: SUCCESS — 5s
- Foundation PostgreSQL 14: SUCCESS — 57s
- Foundation PostgreSQL 15: SUCCESS — 57s
- Foundation PostgreSQL 16: SUCCESS — 1m6s
- Foundation PostgreSQL 17: SUCCESS — 58s
- Foundation PostgreSQL 18: SUCCESS — 56s
- Markdown: SUCCESS — 5s
- Mermaid: SUCCESS — 52s
- Node contracts: SUCCESS — 56s
- Python 3.12 quality and package: SUCCESS — 33s
- Python 3.13 quality and package: SUCCESS — 31s
- Python 3.14 quality and package: SUCCESS — 28s
- Repository policy: SUCCESS — 8s
- Supply-chain evidence: SUCCESS — 4m19s
- Totals: 20 successful, 0 failed, 0 cancelled, 0 skipped, 0 pending
- All required implementation-head checks green: YES
- Open repository CodeQL alerts: 0
- Open objective-branch CodeQL alerts: 0
- Workflow reruns requested: 0
- The report-only SELF commit may trigger fresh checks. Those future results
  are not claimed here; the strategic model must independently verify them.

The successful implementation-head supply-chain artifact is:

- Artifact ID: `9307310866`
- Name:
  `supply-chain-evidence-c2b4e173fcef43251488f4949c04093988659b23`
- Size: 1,681,356 bytes
- Created: `2026-08-18T01:20:35Z`
- Expires: `2026-09-01T01:20:33Z`
- Expired at report time: `false`

## Local setup / dependencies

- Existing frozen uv environment used; no Python/Node dependency changed.
- Existing local PostgreSQL 16.14 service used with disposable fixture
  databases and fake test login roles.
- New package or system installation: none.
- Production dependency or lockfile change: none.
- Docker/Compose mutation: none; configuration parsing only.
- Production system, data, credential, or service accessed: none.

## Documentation impact

Created `docs/INSTALLATION_SETUP.md` and updated configuration, database
bootstrap, operations, and Alembic source documentation. They describe
operator-secret handling, one-time disclosure, explicit rotation recovery,
owner-only authority, and the absence of a current consumer/administrator/
HTTP/startup path. They do not claim authentication or initialized installation
is complete.

## Safety and scope confirmations

- Unrelated feature/refactor work: no.
- Expected-path exceptions: only revision-exact lower-layer tests/tool noted
  above; directly required by head `008_001`.
- Activated order or `oap/active` authored/modified by coding agent: NO; both
  strategic artifacts were committed byte-for-byte.
- Earlier OAP artifact edited: NO.
- Real secret, setup token, digest, DSN, password, cookie, private URL, or
  production data printed or committed: no.
- Token in environment variable, URL, query, fragment, cookie, log, exception,
  repr, serialization, fixture literal, or database plaintext: no.
- Runtime/reviewer access to installation state: no.
- Agent/publication/identity/session/migration authority expanded: no.
- User, password, token consumer, initialized setter, session, cookie, CSRF,
  route, UI, OIDC, site, membership, or Compose startup behavior added: no.
- Dependency, lockfile, workflow, Dockerfile, image, service authority,
  architecture, security, or protocol changed: no.
- PostgreSQL integration cap exceeded: NO — exactly 2 invocations.
- Implementation/check-generation cap exceeded: NO — exactly 2.
- GitHub workflow rerun: NO.
- Local forbidden supply-chain, image, full Compose, full matrix, Node install,
  or Playwright run: NO.
- Destructive reset/clean/checkout, broad prune, force push, extra objective PR,
  merge, close, or auto-merge: NO.
- PR `#12` or `#13` acted upon: NO.
- Report-publication commit changes only this report file: yes.

## Known limitations / blockers

- None within activated 010-a scope.
- The setup URL is deliberately not served. There is no token consumer, first
  administrator, initialization action, authentication, session, or default
  issuance wiring until later authorized rounds.
- `COMPLETE` means the requested remote state and evidence exist; it does not
  mean strategic acceptance and does not authorize this coding agent to merge.

## Recommended strategic follow-up

Independently verify this SELF report commit and parent, the singleton
constraints/owner/denial boundary, token entropy/digest/non-leak contract,
transaction/concurrency evidence, two-generation ledger, 20 implementation-head
checks, zero alerts, exact caps, sole-PR correlation, and unchanged prior
artifacts. The strategic model alone decides whether to activate `010-b` on PR
`#15`; no merge is authorized by this report.
