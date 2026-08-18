# OAP Coding-Agent Report — 009-c

## Work order

- Identifier: `009-c`
- Work-order file:
  `oap/orders/009-c-complete-control-readiness-fixture.md`
- Numeric objective: `009`
- PR mode: `AMEND_EXISTING_PR`
- PR result: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

PR `#14` now has the one authorized fixture-only permission correction:
`_set_control_mode` adds `DAC_READ_SEARCH` alongside its existing `FOWNER`.
It still uses `--network none`, `--read-only`, `--cap-drop ALL`, UID/GID
`0:0`, the exact isolated Control-secret volume, and its bounded Python chmod
program. An exact command-level unit contract proves that boundary and the
absence of `DAC_OVERRIDE` or any additional capability.

All directly affected static checks passed. The one authorized sudo fixture
attempt then passed baseline and the complete wrong-login, wrong-role,
unreadable-secret, unsafe-marker, and migration-mismatch sequences. It entered
`stopped-postgres` and failed safely while awaiting the expected bounded
readiness state:

```text
control-readiness-fixture: FAILED stage=stopped-postgres operation=await-readiness reason=timeout
```

The same process continued across an execution-client disconnect and returned
its own exit result; the disconnect did not terminate or cause the fixture
failure. The exact cleanup audit found no container, volume, or network with
the `slaif009cfix` prefix. No second fixture or equivalent Docker reproduction
ran.

The single implementation commit was pushed to the existing PR. GitHub
independently completed the same stages and emitted the same safe timeout:
19 checks passed and `Compose and edge packaging` alone failed. Both open
CodeQL alert counts are zero. The one-attempt, one-implementation, and
one-check-generation caps are exhausted, so the round is necessarily
`PARTIAL`.

No product source, Control behavior, credential policy, role, pool, migration,
Compose service capability/topology, secret mount, dependency, workflow,
Dockerfile, documentation, or adjacent authentication scope changed.

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
- Remote base SHA at activation and report time:
  `ab3db28f573b62130b93ae082a196e8ca9f8b424`
- Head branch: `oap/009-control-database-readiness`
- Starting remote/report head:
  `fd878f148613b29b8ea21acf3d8734d20f6be585`
- Previous 009-b implementation head:
  `c7dbd0f3da7a4cdf582da340a3c5b2d39223b9e4`
- 009-c implementation head:
  `ae7f283037c86799f0971400b83f6afcf249c976`
- Report publication commit: SELF
- Remote PR head after report publication: SELF
- Implementation commit pushed before this report:
  `ae7f283037c86799f0971400b83f6afcf249c976` —
  `Complete Control readiness fixture permissions`
- Implementation commit first parent:
  `fd878f148613b29b8ea21acf3d8734d20f6be585`
- 009-c implementation diff: 4 files, 267 insertions, 1 deletion
- Cumulative PR implementation at report time: 37 files, 4,691 insertions,
  142 deletions
- New PR created this round: no
- Existing PR amended this round: yes
- Force push performed: no
- Merge performed: NO
- Auto-merge enabled: NO
- PR closed: NO

GitHub search returned exactly one objective-009 PR: open PR `#14` with the
required base, branch, and title. The PR body was updated through the REST API
after the older CLI edit path failed on GitHub's deprecated Projects-classic
GraphQL field. The verified body records the exact local/GitHub timeout,
19/1 check state, exhausted caps, and absence of product changes.

## Changes made

### Minimal helper-only correction

Only the ephemeral command created by `_set_control_mode` gained one
capability:

```text
--cap-drop ALL --cap-add DAC_READ_SEARCH --cap-add FOWNER
```

The helper retains all of its prior confinement:

- disposable `docker run --rm` execution;
- `--network none`;
- read-only container root;
- all capabilities dropped before the two explicit additions;
- UID/GID `0:0`;
- only `<project>_control-secret:/secrets` mounted;
- Python as the entrypoint; and
- a constant-path chmod program bounded to the requested numeric mode.

`DAC_OVERRIDE` was not added. No Compose service capability, application
process, credential rule, or runtime path changed.

### Exact static contract

`tests/packaging/test_compose_policy.py` now intercepts the helper invocation
and asserts its complete argument vector. This proves the exact isolated
volume, network, root filesystem, capability, identity, entrypoint, image, and
chmod-program boundary. Since the expected vector contains only
`DAC_READ_SEARCH` and `FOWNER` after `--cap-drop ALL`, an unexpected
`DAC_OVERRIDE` or any other capability fails the test.

All 009-b allowlisted, secret-free diagnostic tests remain intact. The real
`compose.yaml` remained byte-unchanged from the starting implementation head;
both its rendered configuration and exact policy validation passed.

## Files changed before report publication

- `oap/active`
- `oap/orders/009-c-complete-control-readiness-fixture.md` (new)
- `tests/packaging/test_compose_policy.py`
- `tools/compose/control_readiness.py`

These are exactly the four authorized pre-report paths. This report is the
sole fifth path in its mandatory report-only commit.

## Governance and prior-artifact integrity

The governing sources and every prior objective-009 artifact remained
byte-identical:

- `AGENTS.md` SHA-256:
  `9b5995dd14574f853b34c08c0378c901d6b197a3073556c779c6588bd4ac4e4e38`
- `OAP-COMMUNICATION-coding-agent.md` SHA-256:
  `e6150d6efb5a64e7f8af29b00514776972d4f98a0632281ddc260110c6374604`
- `ARCHITECTURE.md` SHA-256:
  `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- `SECURITY.md` SHA-256:
  `ec327af34d13406b560f75834d8bbda685f81dad17fd400cce0c5b6b8df4e23c`
- 009-a order SHA-256:
  `35ec043c1b40867137523d4377d47f0365c068816a2c563347f9916af2b5f132`
- 009-a report SHA-256:
  `86d28ac72a9958efa642b0ff4d149db156048a1f91aae1940ae1358a0c660658`
- 009-b order SHA-256:
  `5d3782228d16caaf2fd81e9c787c6709406e5218594f1b0cfab787aa2cd52050`
- 009-b report SHA-256:
  `625533ef2691725c130076277b41d0fd36c58a8411dff096d08df95be43d6465`
- Activated 009-c order SHA-256:
  `f16a19ca6bdd553591d85bd71fbf06ca93e31d69cca1254392b89322223d1024`

No narrower applicable `AGENTS.md` or `AGENTS.override.md` exists.

## Targeted sudo fixture attempt ledger

### Attempt 1 — sole and final permitted run

- Start: `2026-08-17T23:43:29Z`
- End: `2026-08-17T23:45:33Z`
- Duration: 124.103 seconds
- Exit: 1
- Exact command:
  `sudo python tools/compose/control_readiness.py slaif009cfix`
- Disposable project: `slaif009cfix`
- Printed and completed stages: baseline, wrong-login, wrong-role,
  unreadable-secret, unsafe-marker, and migration-mismatch.
- Entered stage: stopped-postgres.
- Failure category:
  `stage=stopped-postgres operation=await-readiness reason=timeout`.
- Recovery stage printed/completed: no.
- Secret, child command, stdout, stderr, locator, driver exception, or
  container environment exposed: no.
- Execution-client interruption: the client disconnected after the
  stopped-postgres stage had printed, but the same background process remained
  live and returned the bounded failure and timestamps when reattached. No new
  process or attempt was started.
- Diagnosis or subsequent change: none, as required after the sole attempt.
- First cleanup query without `sudo`: not evidence; Docker socket access was
  denied for all three read-only queries.
- Exact repeated cleanup audit with `sudo`: PASS — no container, volume, or
  network with the `slaif009cfix` prefix remained.

Targeted sudo fixture attempts: exactly 1 of 1 allowed. No second fixture,
manual mutation, or equivalent Docker reproduction ran.

## Stage and negative-state evidence

- Baseline: PASS — printed only after direct Control readiness, liveness,
  NGINX readiness, and isolated-mount assertions completed.
- Wrong login: PASS — the script advanced only after bounded
  `configuration_invalid` readiness, Control liveness 200, NGINX unready,
  exact credential restoration, and return to ready completed.
- Wrong role: PASS — the script advanced only after bounded `role_mismatch`
  readiness, Control liveness 200, NGINX unready, exact role restoration, and
  return to ready completed.
- Unreadable secret: PASS — the new helper changed/restored the mode; bounded
  `configuration_invalid` readiness, Control liveness 200, NGINX unready,
  recreation, and return to ready completed before the next stage printed.
- Unsafe marker: PASS — bounded `bootstrap_unsafe` readiness, Control
  liveness 200, NGINX unready, bootstrap restoration, and return to ready
  completed before the next stage printed.
- Migration mismatch: PASS — bounded `migration_mismatch` readiness, Control
  liveness 200, NGINX unready, migration restoration, and return to ready
  completed before stopped-postgres printed.
- Stopped PostgreSQL: FAIL — the first await-readiness operation timed out;
  subsequent liveness/NGINX assertions did not run and are not passing
  evidence.
- Recovery: NOT RUN — no recovery-stage line printed after the stopped-
  PostgreSQL failure.

## Acceptance-criteria evidence

### Criterion 1 — unique existing PR amended once

- Result: PASS
- Evidence: PR `#14` remains the sole objective-009 PR with the required open,
  non-draft/base/head/title state. Exactly one 009-c implementation commit and
  one automatic check generation were pushed. No force push, extra PR, merge,
  close, auto-merge, or prior-artifact edit occurred.

### Criterion 2 — helper-only authority correction

- Result: PASS
- Evidence: only `_set_control_mode` received `DAC_READ_SEARCH`. Its exact
  confined command is unit-tested. Product source and `compose.yaml` are
  unchanged; no production capability gained authority.

### Criterion 3 — exact static contract and safe diagnostics

- Result: PASS
- Evidence: 11 packaging tests plus 2 subtests passed, including the complete
  helper argument vector and retained allowlisted/secret-free diagnostics.
  Compose rendering/policy checks passed against unchanged production config.

### Criterion 4 — one complete targeted run and cleanup

- Result: FAIL
- Evidence: exactly one attempt ran and exact cleanup passed. It completed
  through migration-mismatch but timed out during stopped-postgres; final
  recovery therefore did not run.

### Criterion 5 — rejection, fail-closed behavior, and recovery

- Result: PARTIAL
- Evidence: wrong login, wrong role, unreadable secret, unsafe marker, and
  migration mismatch all completed their fail-closed liveness/readiness/NGINX
  and restoration contracts. Stopped-PostgreSQL assertions and final recovery
  did not complete and are not claimed.

### Criterion 6 — 20 green checks and zero alerts

- Result: FAIL
- Evidence: 19 checks succeeded and the Compose job alone failed with the
  exact local timeout category. Repository and objective-branch open CodeQL
  alert counts were both zero.

### Criterion 7 — OAP correlation and publication

- Result: PASS through report publication.
- Evidence: `oap/active` is exactly `009-c\n`; all three rounds correlate to
  PR `#14` and the same branch; prior artifacts are unchanged; this report is
  a final report-only SELF commit whose first parent is the literal 009-c
  implementation head.

## Local verification

- `uv run --frozen pytest -q tests/packaging/test_compose_policy.py`: PASSED —
  11 passed and 2 subtests passed in 0.06 seconds.
- `uv run --frozen ruff check tools/compose/control_readiness.py
  tests/packaging/test_compose_policy.py`: PASSED.
- `uv run --frozen ruff format --check tools/compose/control_readiness.py
  tests/packaging/test_compose_policy.py`: PASSED — 2 files already formatted.
- `uv run --frozen mypy`: PASSED — no issues in 66 source files.
- `uv run --frozen python -m py_compile
  tools/compose/control_readiness.py`: PASSED.
- `python tools/check_repository.py`: PASSED — `PASS repository policy`.
- Cached `markdownlint-cli2` 0.23.2 on this immutable report: PASSED —
  0 errors.
- Post-report `python tools/check_repository.py`: PASSED —
  `PASS repository policy`.
- `docker compose config --quiet`: PASSED.
- `python tools/compose/verify.py --root .`: PASSED — `compose-policy: OK`.
- `git diff --check`: PASSED before the implementation commit.
- Active-pointer, activated-order hash, exact allowed-path, prior-artifact,
  unchanged-Compose, staged-scope, remote-head, and commit-parent checks:
  PASSED.
- First non-sudo cleanup audit: BLOCKED — permission denied on the Docker
  socket; it was not used as cleanup evidence.
- Exact sudo cleanup audit: PASSED — containers `NONE`, volumes `NONE`,
  networks `NONE` for prefix `slaif009cfix`.
- Sole targeted fixture attempt: FAILED safely as recorded above.
- Local `tools/supply_chain/run.sh`: NOT RUN — explicitly forbidden.
- Local full image/SBOM/Grype or reproducibility gate: NOT RUN — explicitly
  forbidden.
- Local full Compose smoke: NOT RUN — explicitly forbidden.
- Local full Python matrix: NOT RUN — explicitly forbidden.
- Local full PostgreSQL matrix: NOT RUN — explicitly forbidden.
- Second fixture/manual Docker reproduction: NOT RUN — explicitly forbidden.

No failed, incomplete, unavailable, skipped, pending, or not-run item above is
represented as passing evidence.

## GitHub CI / required checks

- Ordinary CI run: `32081948153` — FAILURE
- CodeQL run: `32081948157` — SUCCESS
- Check state observed for implementation head:
  `ae7f283037c86799f0971400b83f6afcf249c976`
- Analyze (actions): SUCCESS — 44s
- Analyze (javascript-typescript): SUCCESS — 1m03s
- Analyze (python): SUCCESS — 52s
- CodeQL aggregate: SUCCESS — 2s
- Dependency review: SUCCESS — 4s
- Detect supported languages: SUCCESS — 6s
- Foundation PostgreSQL 14: SUCCESS — 50s
- Foundation PostgreSQL 15: SUCCESS — 53s
- Foundation PostgreSQL 16: SUCCESS — 48s
- Foundation PostgreSQL 17: SUCCESS — 54s
- Foundation PostgreSQL 18: SUCCESS — 52s
- Markdown: SUCCESS — 5s
- Mermaid: SUCCESS — 44s
- Node contracts: SUCCESS — 1m03s
- Python 3.12 quality and package: SUCCESS — 28s
- Python 3.13 quality and package: SUCCESS — 31s
- Python 3.14 quality and package: SUCCESS — 30s
- Repository policy: SUCCESS — 8s
- Compose and edge packaging: FAILURE — 2m22s
- Supply-chain evidence: SUCCESS — 4m42s
- Totals: 19 successful, 1 failed, 0 cancelled, 0 skipped, 0 pending
- All required checks green: NO
- Open repository/PR CodeQL alerts: 0
- Open objective-branch CodeQL alerts: 0
- Workflow reruns requested: 0
- The report-only SELF commit may trigger fresh checks. Those future results
  are not claimed here and cannot repair the known implementation-head
  failure.

GitHub's Compose log independently records:

```text
control-readiness-stage: baseline
control-readiness-stage: wrong-login
control-readiness-stage: wrong-role
control-readiness-stage: unreadable-secret
control-readiness-stage: unsafe-marker
control-readiness-stage: migration-mismatch
control-readiness-stage: stopped-postgres
control-readiness-fixture: FAILED stage=stopped-postgres operation=await-readiness reason=timeout
```

No command, child output, locator, password, username, container environment,
or driver exception accompanies that line.

The successful implementation-head supply-chain artifact is:

- Artifact ID: `9305484234`
- Name:
  `supply-chain-evidence-ebeb5aa7d94e1ae1b40ea2016d5a6e30b526a2d4`
- Size: 1,673,940 bytes
- Created: `2026-08-17T23:52:40Z`
- Expires: `2026-08-31T23:52:39Z`
- Expired at report time: `false`

## Local setup / dependencies

- The sole fixture used the pre-existing passwordless-sudo Docker Engine path.
- The fixture built/started only its exact disposable project graph and
  removed its exact containers, networks, volumes, and orphans.
- The existing frozen uv environment was used.
- New package/system dependency installation: none.
- Production dependency or lockfile change: none.
- Docker daemon, host, or durable setup change: none.
- Local supply-chain/scanner execution: none.

## Documentation impact

No durable product, configuration, deployment, operations, API, security, or
architecture behavior changed, so no product documentation was edited. The
immutable 009-c order and this report record the fixture correction and exact
remaining stopped-PostgreSQL limitation. All accepted 009-a documentation
remains unchanged.

## Safety and scope confirmations

- Unrelated files changed: no.
- Changes outside the activated paths: no.
- 009-a and 009-b orders/reports edited: NO; all hashes are recorded above.
- Earlier OAP artifact edited: NO.
- Activated order or `oap/active` authored/modified by coding agent: NO; both
  strategic artifacts were committed byte-for-byte.
- Production secrets, systems, credentials, or data accessed: no.
- Real DSN/password/token/cookie/private artifact URL printed or committed:
  no.
- Diagnostic child command/stdout/stderr printed: no.
- Product source, identity/role validation, pool, migration, health contract,
  Compose topology, secret generator/mount, or production capability changed:
  no.
- `DAC_OVERRIDE` added to `_set_control_mode`: NO.
- Wrong credential or role accepted: no.
- Authentication or adjacent product scope added: no.
- Dependency, lockfile, workflow, Dockerfile, image, scanner, supply-chain
  policy, notice, exception, architecture, security, or protocol changed: no.
- Targeted sudo fixture cap exceeded: NO — exactly 1 attempt.
- Implementation commit/check-generation cap exceeded: NO — exactly 1 before
  this mandatory report-only commit.
- GitHub workflow rerun: NO.
- Local full supply-chain/image gate, full Compose smoke, or full matrix run:
  NO.
- Broad Docker prune, reset, clean, checkout, destructive cleanup, or force
  push performed: no.
- Extra objective-009 PR created: NO.
- PR merged by coding agent: NO.
- PR closed by coding agent: NO.
- Auto-merge enabled by coding agent: NO.
- Report-publication commit changes only this report file: yes.

## Known limitations / blockers

- The sole local fixture and GitHub's independent fixture both timed out at
  `stopped-postgres/await-readiness` after completing every earlier stage.
- Stopped-PostgreSQL liveness/NGINX assertions and final recovery are not-run
  evidence, so the complete Control-readiness fixture is not proven.
- The activated order forbids diagnosis, a second fixture attempt, an
  equivalent Docker reproduction, a second implementation, and a workflow
  rerun after this failure. No cause or correction is inferred here.
- PR `#14` remains unmergeable by policy with one failed check. The coding
  agent has not merged, closed, or enabled auto-merge.

## Recommended strategic follow-up

Review the matching local and GitHub stopped-PostgreSQL timeout evidence and
decide whether to activate another tightly bounded objective-009 diagnostic
round. Any further Docker reproduction, timeout investigation, fixture change,
or check generation requires new strategic scope. Independently verify this
SELF report commit, its first parent, attempt/check caps, exact cleanup, single-
PR correlation, and unchanged prior artifacts before any acceptance decision.
