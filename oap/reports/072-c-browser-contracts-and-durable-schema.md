# OAP Coding-Agent Report — 072-c

## Work order

- Identifier: `072-c`; numeric objective: `072`.
- Work-order file:
  `oap/orders/072-c-browser-contracts-and-durable-schema.md`.
- PR mode: `AMENDED_EXISTING_PR`.

## Status

PARTIAL

The bounded 072-c contracts/database slice is complete and verified. Numeric
Objective 072 remains PARTIAL because public Agent browser routes, credential
dispatch, the real Playwright worker/runtime image, artifact byte storage,
network confinement, source tools, and browser execution/E2E remain explicitly
deferred.

## Executive summary

Replaced the browser contract metadata scaffold with immutable
`browser-preview/v1` TypeScript and Python contracts, deterministic canonical
serialization and SHA-256 request digesting, and exact cross-language parity
tests. Added migration `035_001` with nine bounded capability browser-limit
fields, three non-COW Control relations, one append-only Audit relation, strict
constraints/indexes/bindings, nine exact Agent-executable owner functions, and
one ungranted private authority helper. Agent capability authentication now
returns validated immutable browser limits without direct Agent table reads.

Real PostgreSQL proof covers idempotency, quota reservation, lock/revocation
races, cancellation, lease retry/max attempts, artifact metadata, terminal
idempotency, isolation, and grants. Local PostgreSQL 14–18, the full integration
suite, clean Compose/Playwright, supply-chain evidence, and every fresh GitHub
check passed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: #66, <https://github.com/ulfe-lmi/slaif-agent-site/pull/66>.
- PR state at report drafting: `OPEN`, non-draft, `MERGEABLE`, merge-state
  `CLEAN`.
- Base branch: `main`; head branch:
  `oap/072-browser-worker-real-playwright`.
- Starting remote objective head:
  `3494447ac690fe37f877204153e54f84d0569d83`.
- Starting authoritative remote main:
  `082f2359b0c4d59b692580d17992c35d46183b12`.
- Implementation head SHA:
  `2505a98120e26f9fee3ea8d52fb291997ae676b4`.
- Report publication commit: SELF.
- Remote PR head after report publication: SELF (literal derived and verified
  after publication).
- Implementation commit pushed before report:
  `2505a98120e26f9fee3ea8d52fb291997ae676b4`
  (`feat(browser): add durable preview run contracts`).
- Report parent must equal implementation SHA: yes; verified after publication.
- New PR this turn: no. Existing PR amended: yes. Merge performed: NO.

## Changes made

### Versioned contracts

- Added one immutable `browser-preview/v1` contract version shared by
  TypeScript and Python.
- Limited first runtime targets to `desktop-chromium`, `tablet`, and
  `mobile-chromium`; no caller viewport/device override exists.
- Added nine curated evidence values: screenshot, accessibility, structure,
  heading, link, media, overflow, console, and failed-request summaries.
- Added extra-forbid bounded external create, public status/result, private
  artifact metadata, internal run specification, lease, and completion models
  and JSON-schema facts.
- External create accepts exactly `version`, normalized `route`, `target`, and a
  unique bounded `evidence` list. It rejects unknown fields/version/target,
  absolute or scheme-relative URLs, traversal, fragments, credential-shaped
  queries, authority IDs, viewport, headers/cookies, JavaScript, and commands.
- Canonical serialization fixes evidence order and key order. Python and
  TypeScript agree on digest vector
  `6ee9d361a4433878c18c6aa645c6872afae8bd31ac0e628e88f3d0eefa3405f4`.

### Migration 035 durable state

- Added nine non-null capability limits: total runs, concurrent runs,
  screenshots, artifact bytes, routes/run, evidence/run, duration, attempts,
  and allowed targets. Defaults are `20`, `2`, `50`, `104857600`, `10`, `9`,
  `120`, `3`, and all three approved Chromium targets, with conservative checks.
- Added `control.browser_run`, `control.browser_idempotency`,
  `control.browser_artifact`, and `audit.browser_event`; no COW content or
  publication state was added.
- Run state is exactly `QUEUED|RUNNING|COMPLETED|FAILED|TIMED_OUT|CANCELLED`.
  Constraints cover contract/route/evidence/digest/reservation/state/terminal/
  lease/attempt/size/time shapes.
- Composite foreign keys bind capability/workspace and
  workspace/site/delegator, then propagate the exact five-part run binding to
  idempotency, artifact, and audit rows. Audit references have no cascade
  deletion.
- Artifact rows contain only kind, MIME, digest, size, target, route digest,
  private visibility, and timestamps. They contain no path, URL, token, or
  bytes.
- Added deterministic claim/capability/retention/event indexes and one partial
  unique active-lease index. Migration `035_001` is the sole new migration and
  the single head; migrations `006_001` through `034_001` were not edited.

### Exact functions and grants

- Added nine exact functions executable by `slaif_agent_runtime` (owner retains
  implicit owner authority): capability authenticate; browser run begin, get,
  claim, renew, release, complete; artifact list; artifact register.
- Added one private owner helper for current browser authority; it is not
  executable by Agent or another service role.
- Every function is owner-defined, `SECURITY DEFINER`, and fixed at
  `search_path=pg_catalog`; PUBLIC execution is revoked.
- Begin acquires the shared workspace advisory transaction lock before mutable
  authority recheck, locks the capability/workspace, serializes idempotency,
  atomically enforces/reserves all quotas, and writes one run/idempotency/event.
- Claim uses deterministic `FOR UPDATE SKIP LOCKED`, bounded leases and attempts;
  renew/release/completion/artifact registration require exact current lease and
  current capability/workspace/site authority. Completion and same-artifact
  registration are idempotent only for identical facts.
- Agent direct `SELECT` on `control.workspace` and `control.capability` was
  removed. Agent has no direct access to the four browser relations, generic
  Control/job/reviewer/setup/audit relations/functions, COW base/change tables,
  or sequences.
- Control retains existing workspace/capability management reads but receives
  no browser relation/function grant. Editor, public reader, preview reader,
  Reviewer, Scheduler, Media, and GC likewise receive no browser relation or
  function authority. The browser worker remains DB-less.

### Trusted capability context

- Added frozen extra-forbid `BrowserCapabilityLimits` to
  `CapabilityAuthenticationRecord` and `AgentCapabilityContext`.
- Capability authentication now uses the exact owner function for Agent and
  validates every numeric relationship and allowed target returned from the DB.
  Null, malformed, unsupported-target, or internally inconsistent stored facts
  deny safely.
- Public Agent session/discovery response wiring is unchanged and exposes no
  counters, lease IDs, signing keys, SQL, roles, or foreign IDs.

## Files changed

- Contracts/package: `packages/browser-tool-contracts/package.json`,
  `packages/browser-tool-contracts/tsconfig.json`,
  `packages/browser-tool-contracts/tsconfig.build.json`,
  `packages/browser-tool-contracts/src/index.ts`,
  `packages/browser-tool-contracts/src/browser-preview-v1.json`, and
  `packages/browser-tool-contracts/tests/index.test.ts`.
- Python contracts/context: `services/backend/src/slaif_agent_site/browser_contracts.py`,
  `services/backend/src/slaif_agent_site/agent_state/capability_auth.py`,
  `services/backend/src/slaif_agent_site/agent_api/models.py`,
  `services/backend/src/slaif_agent_site/agent_api/database.py`, and
  `services/backend/src/slaif_agent_site/control_api/database.py`.
- Database: `services/backend/src/slaif_agent_site/db/alembic/versions/035_001_browser_run_control_plane.py`
  and `services/backend/src/slaif_agent_site/db/privileges.py`.
- Tests/policy: `services/backend/tests/unit/test_browser_contracts.py`,
  `services/backend/tests/unit/test_foundation_contract.py`,
  `services/backend/tests/unit/test_control_database.py`,
  `services/backend/tests/integration/test_browser_run_control_plane.py`,
  `services/backend/tests/integration/test_capability_authentication.py`,
  `services/backend/tests/integration/test_control_database_integration.py`,
  `services/backend/tests/integration/test_database_bootstrap.py`,
  `tests/contracts/workspace-contracts.test.ts`, and
  `tools/check_repository.py`.
- Documentation: `docs/API.md`, `docs/AUTHORIZATION.md`,
  `docs/DATABASE_BOOTSTRAP.md`, `docs/DATABASE_ROLES.md`, `docs/SECURITY.md`,
  `docs/SERVICE_AUTHORITY.md`, `docs/TESTING.md`, and
  `migrations/alembic/README.md`.
- Strategic transcript committed unchanged:
  `oap/orders/072-c-browser-contracts-and-durable-schema.md` and `oap/active`.
- Dependency and lock files changed: none.

## Acceptance-criteria evidence

### Criterion 1 — Versioned bounded cross-language contracts

- Result: PASSED.
- TypeScript package tests: 21 passed. Python browser-contract tests: 20 passed.
- Both languages compare the committed neutral fact document and exact digest
  vector. Tests cover extra fields, version/target/evidence/state bounds,
  oversized/foreign/credential/traversal input, and frozen models/schemas.

### Criterion 2 — Coherent migration 035 durable schema

- Result: PASSED.
- Clean upgrade, repeat upgrade/reconcile, independent privilege validation,
  full downgrade, rebuild, and single-head checks passed on PostgreSQL 14–18.
- Real schema evidence is four relations, nine capability-limit columns, nine
  Agent-executable functions, one private helper, and no public path/URL/bytes/
  publication state.

### Criterion 3 — Exact Agent function and privilege boundary

- Result: PASSED.
- Real `slaif_agent_login`/`slaif_agent_runtime` calls execute the nine exact
  functions. Function owner/search-path/SECURITY DEFINER/PUBLIC and service-role
  ACL facts were catalog-checked.
- Agent direct reads/DML on browser, capability, generic Control/audit, COW
  base/change, reviewer, and setup surfaces fail. Eight other non-owner service
  roles fail browser-function invocation and direct browser relation reads.

### Criterion 4 — Trusted capability browser limits

- Result: PASSED.
- Real capability authentication returns default validated limits and the exact
  allowed-target set inside trusted context while public discovery remains
  unchanged. Fake-record negatives prove null, unsupported, and relationally
  invalid values deny safely.

### Criterion 5 — Real PostgreSQL behavior

- Result: PASSED.
- Concurrent same-key calls produced exactly one run, one idempotency row, and
  one enqueue event; callers observed `STARTED` plus `REPLAY`. Different digest
  returned `MISMATCH` without residue.
- Each total/concurrent/screenshot/artifact/target/route/evidence/duration quota
  case produced exactly `(0 run, 0 idempotency, 0 event)` for its independent
  capability.
- Missing scope, revoked/expired capability, revoked/expired workspace, archived
  site, forged binding, and foreign/random IDs deny or return non-leaking
  absence. Shared-lock revocation race waited/rechecked and left `(0,0,0)`;
  cancellation rolled back and the same pool connection remained usable.
- Concurrent claim skipped a locked run. Lease expiry retried to attempt 2;
  expiry/max attempts ended `FAILED/MAX_ATTEMPTS`. Renew/release and invalid
  transition/metadata cases were exercised through runtime functions.
- Identical artifact registration produced one row and one audit event. Valid
  completion replay produced one terminal event. Revocation hid retained
  artifact metadata and denied later registration.
- Run/artifact reads added no browser event and no foundation COW operation.

## Local verification

- `uv --version`: PASSED — exact `uv 0.12.5`.
- `uv lock --check`: PASSED — 45-package resolution/44-package check; no lock
  change.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tests/packaging tests/supply_chain tools migrations`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tests/packaging tests/supply_chain tools migrations`:
  PASSED — 233 files formatted.
- `uv run --frozen mypy`: PASSED — 210 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED
  — 457 tests.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 109
  tests in 494.50 seconds.
- Focused
  `uv run --frozen pytest services/backend/tests/integration/test_database_bootstrap.py services/backend/tests/integration/test_capability_authentication.py services/backend/tests/integration/test_control_database_integration.py services/backend/tests/integration/test_browser_run_control_plane.py -q`:
  PASSED — 30 tests in 208.95 seconds.
- Focused browser PostgreSQL proof
  `uv run --frozen pytest services/backend/tests/integration/test_browser_run_control_plane.py -q`:
  PASSED — 2 tests.
- Local container matrix with
  `test_database_bootstrap.py test_browser_run_control_plane.py`: PASSED on
  PostgreSQL 14, 15, 16, 17, and 18 — 25 tests/version. Durations were 251.88,
  245.93, 247.97, 207.45, and 193.97 seconds respectively.
- First matrix preparation: FAILED before tests because PostgreSQL 18 changed
  its image data layout and the old `/var/lib/postgresql/data` tmpfs mount did
  not become ready. Retried with exact `/var/lib/postgresql` tmpfs; all five
  versions became ready.
- First parallel three-file matrix attempt: each version recorded 25 passed/1
  failed because the capability HTTP test correctly rejects mapped Agent DSN
  ports `55414`–`55418` instead of `5432`. No product code was weakened. It was
  rerun as the compatible 25-test/version matrix above; capability HTTP passed
  on local PostgreSQL 16 at port 5432 and in every isolated GitHub PostgreSQL
  14–18 job.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — wheel and
  sdist.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — exact `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED — all 10 workspace projects already
  current.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — browser contract package 21 tests; all other package,
  Web, worker, and root contract tests passed.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED — inventory produced; no dependency
  change.
- Initial Node/repository integration attempt: FAILED because repository policy
  still required the browser package to remain a scaffold, the new package
  tests were outside its TS project, and ESLint rejected one control-character
  regex. Fixed the exact implemented-package policy/build config and replaced
  the regex with code-point checks; complete Node and repository gates passed.
- `python -m compileall -q tools tests/repository tests/packaging tests/supply_chain`:
  PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 54
  tests.
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED — 39
  tests.
- `python -m unittest discover -s tests/supply_chain -p 'test_*.py'`: PASSED —
  29 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; 235
  Markdown files scanned; Mermaid CLI 11.16.0.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 229 files, zero
  issues.
- Bare `python -m slaif_agent_site.<process> --check` for all ten processes:
  FAILED because system Python does not install this checkout package. Retried
  through the frozen installed environment with
  `uv run --frozen python -m slaif_agent_site.<process> --check`: PASSED — all
  ten returned `CHECK_OK`; no listener or mutation was started.
- `python tools/compose/verify.py --root .`: PASSED — static policy, including
  browser-worker no-DB/no-mount boundary.
- `python -m tools.supply_chain.policy validate`: PASSED.
- First `sh tools/compose/smoke.sh slaif072c`: FAILED immediately on the
  harness's fixed project-name allowlist; no stack change. Retry with approved
  `slaif071oap072c` reached Docker and FAILED before container creation on local
  socket permission. Final
  `sudo env PATH="$PATH" sh tools/compose/smoke.sh slaif071oap072c`: PASSED —
  all 15 services, 9 Playwright projects, 6 stable device/browser projects,
  governance/Puck/preview/media/edge/login/secret/readiness/restart/recovery,
  negative bootstrap, Apache syntax, and NGINX syntax; cleanup removed the
  disposable project/volumes.
- `sh tools/supply_chain/run.sh <temporary>/evidence`: PASSED — reproducibility,
  dependency inventory, notices, six image SBOM/scan sets, checksums, zero
  critical and 51 policy-accepted high findings. Evidence:
  `/tmp/tmp.S8duoF9Xx1/evidence`.

## GitHub CI / required checks

State observed for implementation head
`2505a98120e26f9fee3ea8d52fb291997ae676b4`: all 20 reported checks completed
successfully; all required checks green at drafting: yes.

- `Repository policy`: SUCCESS.
- `Node contracts`: SUCCESS.
- `Python 3.12 quality and package`: SUCCESS.
- `Python 3.13 quality and package`: SUCCESS.
- `Python 3.14 quality and package`: SUCCESS.
- `Foundation PostgreSQL 14`: SUCCESS.
- `Foundation PostgreSQL 15`: SUCCESS.
- `Foundation PostgreSQL 16`: SUCCESS.
- `Foundation PostgreSQL 17`: SUCCESS.
- `Foundation PostgreSQL 18`: SUCCESS.
- `Compose and edge packaging`: SUCCESS.
- `Supply-chain evidence`: SUCCESS.
- `Markdown`: SUCCESS.
- `Mermaid`: SUCCESS.
- `Dependency review`: SUCCESS.
- `Detect supported languages`: SUCCESS.
- `Analyze (actions)`: SUCCESS.
- `Analyze (python)`: SUCCESS.
- `Analyze (javascript-typescript)`: SUCCESS.
- `CodeQL`: SUCCESS.

The report-only SELF commit may trigger fresh checks; strategy independently
verifies SELF.

## Local setup / dependencies

- Used exact existing uv/Node/pnpm/PostgreSQL/Docker/Playwright toolchain.
- Used passwordless sudo only for disposable Docker matrix/Compose access where
  the local Docker socket denied the unprivileged user.
- Pulled ordinary PostgreSQL 14–18 test images and used explicit disposable
  containers; all were removed. Clean Compose project and volumes were removed
  by the harness.
- No production dependency, Python lock, Node lock, Playwright dependency,
  browser binary/runtime image, hosted service, or account-bound runtime was
  added.

## Documentation

Updated only contract/database/authorization/security/testing documentation:
API, authorization, database bootstrap/roles, security, service authority,
testing, and Alembic README. All explicitly distinguish the implemented durable
foundation from deferred HTTP, credentials, worker, byte storage, confinement,
source, publication, and browser execution.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no. Production systems/data accessed: no.
- Real capability, cookie, DB URL, artifact URL, or private preview credential
  printed/committed: no; fixtures use fake disposable values.
- Required tests skipped/not run: no. Failures/retries are recorded above.
- Scope deviation: no. Agent HTTP routes, fake browser router/app wiring,
  browser-worker source/image/package, Playwright lock/dependency, Compose
  networks/volumes, Web/Render tokens, secret initialization, artifact bytes,
  source tools, and publication were unchanged.
- Extra objective PR: NO. Coding-agent merge/auto-merge/close: NO.
- Activated order/active edited by coding agent: NO; exact strategy-authored
  bytes were committed unchanged.
- Earlier orders/reports edited: no.
- Report commit changes only this report: yes (verified after commit).

## Known limitations / blockers

- Browser worker remains a health-only stub with no Playwright dependency or
  browser binary. No public/internal browser execution route, credential
  signing/exchange, Agent dispatcher wiring, artifact filesystem/bytes, egress
  confinement, source crawling, or browser E2E exists in this round.
- Durable queue/lease functions are implemented and proven only as a foundation
  for later same-PR wiring; callers cannot invoke them through public product
  APIs yet.
- Numeric Objective 072 therefore remains PARTIAL by order. The 072-c bounded
  slice has no blocker.

## Recommended strategic follow-up

Strategy may independently review this migration/function boundary and decide
whether the next Objective 072 continuation should wire the Agent-owned
dispatcher/credential boundary and real confined Chromium worker. Coding makes
no next-order, acceptance, merge, or release decision.
