# OAP Coding-Agent Report — 009-b

## Work order

- Identifier: `009-b`
- Work-order file:
  `oap/orders/009-b-fix-control-readiness-negative-fixture.md`
- Numeric objective: `009`
- PR mode: `AMEND_EXISTING_PR`
- PR result: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

PR `#14` now has safe, allowlisted Control-readiness fixture diagnostics and a
proven fixture-only correction for the 009-a wrong-login failure. Diagnostics
emit only an allowlisted stage, operation, and reason; arbitrary locator-like
input collapses to constant fallback categories, and child commands/stdout/
stderr are never printed.

Sudo fixture attempt 1 identified the original failure exactly as
`stage=wrong-login operation=recreate-control reason=command-failed`. The
Control product behavior was not the defect. A minimal `--no-deps` change now
force-recreates only Control during deliberate unhealthy states rather than
re-evaluating its one-shot Compose dependency graph.

Sudo fixture attempt 2 then passed baseline, the complete wrong-login sequence,
and the complete wrong-role sequence. It entered `unreadable-secret` and failed
at its first `set-file-mode` helper command with the same bounded
`command-failed` reason. Static source review indicates that helper runs with
`FOWNER` but lacks the `DAC_READ_SEARCH` directory traversal authority needed
to reach a file below the `0700`, UID-10001 volume root. This is a fixture
helper boundary, not a Control product relaxation.

Both authorized fixture attempts are consumed. The order permits one minimal
fix and forbids a third attempt, so no second helper fix was made. The sole
009-b implementation commit was pushed. GitHub independently reproduced the
same progress and same safe unreadable-secret failure: 19 checks passed, the
Compose check alone failed, supply-chain evidence passed, and open CodeQL alert
counts are zero. The round is therefore necessarily `PARTIAL`.

No Control settings, pool, readiness, credential, role, migration, Compose
topology, secret generator/mount, dependency, workflow, Dockerfile, or product/
authentication behavior changed.

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
- Starting remote head:
  `e3a5ed2e3408fc3a0d49933f5d5a6bcc934c2b3e`
- Previous implementation head:
  `f8c87dbead42383f7f810a3ba8ff631a04e14a04`
- 009-b implementation head:
  `c7dbd0f3da7a4cdf582da340a3c5b2d39223b9e4`
- Report publication commit: SELF
- Remote PR head after report publication: SELF
- Implementation commit pushed before this report:
  `c7dbd0f3da7a4cdf582da340a3c5b2d39223b9e4` —
  `Diagnose Control readiness fixture failures`
- Implementation commit first parent:
  `e3a5ed2e3408fc3a0d49933f5d5a6bcc934c2b3e`
- 009-b implementation diff: 4 files, 451 insertions, 40 deletions
- Cumulative PR implementation at report time: 36 files, 3,950 insertions,
  142 deletions
- New PR created this round: no
- Existing PR amended this round: yes
- Force push performed: no
- Merge performed: NO
- Auto-merge enabled: NO
- PRs `#12` and `#13` modified or otherwise acted on: NO

GitHub metadata and search showed the same unique open, non-draft objective-009
PR with the required base, branch, and title. The PR body now records both
attempts, the proven fix, exact final failure, 19/1 check state, zero alerts,
exhausted caps, and absence of product changes.

## Changes made

### Allowlisted diagnostic boundary

`tools/compose/control_readiness.py` now owns three immutable allowlists:

- stages: `setup`, `baseline`, `wrong-login`, `wrong-role`,
  `unreadable-secret`, `unsafe-marker`, `migration-mismatch`,
  `stopped-postgres`, `recovery`, and `cleanup`;
- operations: `initialize`, `build-images`, `start-fixture`,
  `await-readiness`, `await-container`, `assert-liveness`, `assert-nginx`,
  `assert-mount`, `stop-control`, `replace-file`, `recreate-control`,
  `change-role`, `set-file-mode`, `change-marker`, `stop-postgres`,
  `start-postgres`, `restore`, and `cleanup`;
- reasons: `command-failed`, `timeout`, `malformed-response`, and
  `state-mismatch`.

Every subprocess remains captured. A failure stores no command or child text
and prints only:

```text
control-readiness-fixture: FAILED stage=<allowlisted> operation=<allowlisted> reason=<allowlisted>
```

Unexpected runtime input falls back to `stage=setup operation=initialize
reason=state-mismatch`; it is never interpolated. JSON/health parsing,
convergence, command, and state assertions map to their bounded category.
Restoration and cleanup failures are reported separately without replacing the
original safe failure.

The fixture now marks every operation in baseline, all negative stages, and
recovery. A managed targeted run brings up the exact Compose graph needed for
the NGINX dependency assertions and always performs exact-project volume/
orphan cleanup. The existing-CI mode restores Control/database state after a
success or failure.

### Minimal proven fixture fix

`_recreate_control()` now invokes:

```text
docker compose ... up -d --force-recreate --no-deps control-api
```

The command still creates a new Control process so its lifespan rereads the
isolated credential, but deliberately unhealthy credentials no longer cause
Compose to traverse or reevaluate the one-shot bootstrap dependency graph. No
service, dependency definition, production container capability, mount, role,
or Control application behavior changed.

Attempt 2 advancing from `wrong-login` through `wrong-role` proves this was the
correct fixture-only repair for the 009-a failure. The product continued to
reject the wrong login as `configuration_invalid`, reject the wrong effective
role as `role_mismatch`, keep liveness 200, make readiness/NGINX unavailable,
and recover to ready before advancing stages.

### Static tests

`tests/packaging/test_compose_policy.py` now proves:

- the exact safe diagnostic line;
- arbitrary locator-like values do not appear and collapse to constants;
- unexpected `FixtureError` input becomes `state-mismatch`;
- the reason allowlist is exact;
- source contains no `print(result.stdout` or `print(result.stderr` path; and
- Control recreation uses the exact `--no-deps` target-only command.

No product source or documentation needed a behavior change because the first
diagnostic proved the original failure was orchestration-only.

## Files changed before report publication

- `oap/active`
- `oap/orders/009-b-fix-control-readiness-negative-fixture.md` (new)
- `tests/packaging/test_compose_policy.py`
- `tools/compose/control_readiness.py`

All four paths are in the preferred activated scope. This report is the sole
fifth path in its mandatory report-only commit.

## Governance and prior-artifact integrity

The governing sources and immutable 009-a artifacts remained byte-identical:

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
- Activated 009-b order SHA-256:
  `5d3782228d16caaf2fd81e9c787c6709406e5218594f1b0cfab787aa2cd52050`

No narrower applicable `AGENTS.md` or `AGENTS.override.md` exists.

## Targeted sudo fixture attempt ledger

### Attempt 1 — diagnostic

- Start: `2026-08-17T23:20:12Z`
- End: `2026-08-17T23:21:29Z`
- Duration: 76.69 seconds
- Exit: 1
- Exact command:
  `sudo python tools/compose/control_readiness.py slaif009bdiag`
- Disposable project: `slaif009bdiag`
- Completed stage: baseline.
- Failure category:
  `stage=wrong-login operation=recreate-control reason=command-failed`.
- Secret/child output exposed: no.
- Diagnosis: file replacement completed, but the general Compose
  force-recreation command failed before Control health was queried. The
  failure was fixture orchestration, not the expected Control
  `configuration_invalid` contract.
- Minimal subsequent change: add `--no-deps` only to the target Control
  force-recreation command and a static command-contract test.
- Cleanup audit: PASS — no container, volume, or network with the exact
  `slaif009bdiag` prefix remained.

### Attempt 2 — final permitted verification

- Start: `2026-08-17T23:26:18Z`
- End: `2026-08-17T23:27:23Z`
- Duration: 64.88 seconds
- Exit: 1
- Exact command:
  `sudo python tools/compose/control_readiness.py slaif009bdiag`
- Disposable project: `slaif009bdiag`
- Passed stages: baseline, wrong-login, and wrong-role.
- Entered stage: unreadable-secret.
- Failure category:
  `stage=unreadable-secret operation=set-file-mode reason=command-failed`.
- Secret/child output exposed: no.
- Static source diagnosis: the mode helper mounts the isolated volume and runs
  as `0:0` after dropping all capabilities, then adds only `FOWNER`. The file
  is below a `0700` directory owned by UID 10001, so the helper lacks directory
  traversal. A future fixture-only correction can add `DAC_READ_SEARCH` to
  this helper; it must not alter the production service capability set.
- Subsequent change: none. This was the second/final attempt and the order
  requires `PARTIAL` rather than another fix or run.
- Cleanup audit: PASS — no container, volume, or network with the exact
  `slaif009bdiag` prefix remained.

Targeted sudo fixture attempts: exactly 2 of 2 allowed. No third fixture,
manual mutation, or equivalent Docker reproduction ran.

## Acceptance-criteria evidence

### Criterion 1 — unique PR amended once

- Result: PASS
- Evidence: PR `#14` remains the only objective-009 PR, with the required open,
  non-draft/base/head/title state. Exactly one 009-b implementation commit and
  one check generation were pushed. No force push, extra PR, merge,
  auto-merge, or prior-artifact edit occurred.

### Criterion 2 — stable secret-free diagnostics

- Result: PASS
- Evidence: static tests passed the exact allowlists, output line, arbitrary
  locator-like fallback, reason normalization, and absence of child-output
  printing. Both local attempts and GitHub produced only bounded categories.

### Criterion 3 — at most two attempts and complete final fixture

- Result: FAIL
- Evidence: exactly two attempts ran, both cleaned up exactly. Attempt 2 passed
  baseline, wrong-login, and wrong-role, then failed at unreadable-secret/
  set-file-mode. Unsafe-marker, migration-mismatch, stopped-PostgreSQL, and
  final recovery did not run and are not passing evidence.

### Criterion 4 — wrong credentials/roles remain rejected

- Result: PASS for the requested wrong-login and wrong-role product behavior.
- Evidence: attempt 2 could advance only after each negative readiness,
  liveness, NGINX, restoration, and ready check passed. No settings/pool/product
  source changed, and all unit/PostgreSQL gates remained green.

### Criterion 5 — 009-a boundaries intact

- Result: PASS
- Evidence: the implementation commit changes only fixture orchestration/
  diagnostics, its packaging tests, and strategic transcript. No product,
  Compose, secret initializer, mount, role, migration, dependency, workflow,
  Dockerfile, documentation, or authentication path changed.

### Criterion 6 — 20 green checks and zero alerts

- Result: FAIL
- Evidence: 19 checks succeeded and the Compose job alone failed at the exact
  local attempt-2 category. Repository and objective-branch open CodeQL alert
  counts were both zero.

### Criterion 7 — OAP correlation and publication

- Result: PASS through report publication.
- Evidence: `oap/active` is exactly `009-b\n`; 009-a and 009-b correlate to
  PR `#14`/the same branch; the 009-a order/report are unchanged; this report is
  a final report-only SELF commit with the literal implementation head as its
  first parent.

## Local verification

- Pre-attempt diagnostic test:
  `uv run --frozen pytest -q tests/packaging/test_compose_policy.py` — PASSED,
  9 passed and 2 subtests passed.
- Pre-attempt diagnostic static checks: affected Ruff passed; format initially
  identified one mechanical line wrap, then `uv run --frozen ruff format`
  corrected it; final format check passed.
- Pre-attempt `uv run --frozen mypy`: PASSED — no issues in 66 source files.
- Pre-attempt `python -m py_compile tools/compose/control_readiness.py`:
  PASSED.
- After the minimal fix,
  `uv run --frozen pytest -q tests/packaging/test_compose_policy.py`: PASSED —
  10 passed and 2 subtests passed.
- Final affected tests:
  `uv run --frozen pytest -q tests/packaging/test_compose_policy.py
  tests/packaging/test_local_secrets.py`: PASSED — 13 passed and 2 subtests
  passed in 0.55 seconds.
- Final `uv run --frozen ruff check tools/compose/control_readiness.py
  tests/packaging/test_compose_policy.py`: PASSED.
- Final `uv run --frozen ruff format --check
  tools/compose/control_readiness.py tests/packaging/test_compose_policy.py`:
  PASSED — 2 files already formatted.
- Final `uv run --frozen mypy`: PASSED — no issues in 66 source files.
- Final `python -m py_compile tools/compose/control_readiness.py`: PASSED.
- Final `python tools/check_repository.py`: PASSED —
  `PASS repository policy`.
- Final `docker compose config --quiet`: PASSED.
- Final `python tools/compose/verify.py --root .`: PASSED —
  `compose-policy: OK`.
- `git diff --check`: PASSED before the sole implementation commit.
- Active-pointer, unique-order, report-collision, allowed-scope, prior-artifact,
  remote-head, staged-scope, and exact cleanup checks: PASSED.
- Targeted fixture attempt 1: FAILED safely as recorded above.
- Targeted fixture attempt 2: FAILED safely as recorded above.
- Local `tools/supply_chain/run.sh`: NOT RUN — explicitly forbidden.
- Local full image/SBOM/Grype or reproducibility gate: NOT RUN — explicitly
  forbidden.
- Local full Compose smoke: NOT RUN — explicitly forbidden.
- Local full Python matrix: NOT RUN — explicitly forbidden.
- Local full PostgreSQL matrix: NOT RUN — explicitly forbidden.

No failed, incomplete, unavailable, skipped, pending, or not-run item above is
represented as passing evidence.

## GitHub CI / required checks

- Ordinary CI run: `32080568454` — FAILURE
- CodeQL run: `32080568442` — SUCCESS
- Check state observed for implementation head:
  `c7dbd0f3da7a4cdf582da340a3c5b2d39223b9e4`
- Analyze (actions): SUCCESS — 37s
- Analyze (javascript-typescript): SUCCESS — 51s
- Analyze (python): SUCCESS — 49s
- CodeQL aggregate: SUCCESS — 2s
- Dependency review: SUCCESS — 4s
- Detect supported languages: SUCCESS — 4s
- Foundation PostgreSQL 14: SUCCESS — 51s
- Foundation PostgreSQL 15: SUCCESS — 53s
- Foundation PostgreSQL 16: SUCCESS — 49s
- Foundation PostgreSQL 17: SUCCESS — 54s
- Foundation PostgreSQL 18: SUCCESS — 48s
- Markdown: SUCCESS — 8s
- Mermaid: SUCCESS — 40s
- Node contracts: SUCCESS — 59s
- Python 3.12 quality and package: SUCCESS — 25s
- Python 3.13 quality and package: SUCCESS — 32s
- Python 3.14 quality and package: SUCCESS — 33s
- Repository policy: SUCCESS — 8s
- Compose and edge packaging: FAILURE — 1m53s
- Supply-chain evidence: SUCCESS — 5m24s
- Totals: 19 successful, 1 failed, 0 cancelled, 0 skipped, 0 pending
- All required checks green: NO
- Open repository CodeQL alerts: 0
- Open objective-branch CodeQL alerts: 0
- The report-only SELF commit may trigger fresh checks. Those future results
  are not claimed here and cannot repair the known implementation-head failure.

GitHub's Compose log independently records:

```text
control-readiness-stage: baseline
control-readiness-stage: wrong-login
control-readiness-stage: wrong-role
control-readiness-stage: unreadable-secret
control-readiness-fixture: FAILED stage=unreadable-secret operation=set-file-mode reason=command-failed
```

No command, child output, locator, password, username, container environment,
or driver exception accompanies that line.

The successful final-head supply-chain artifact is:

- Artifact ID: `9305083723`
- Name:
  `supply-chain-evidence-53eecfe9ddc2a95622209cb2a2a47b54b2887ddb`
- Size: 1,674,111 bytes
- Created: `2026-08-17T23:33:51Z`
- Expires: `2026-08-31T23:33:49Z`
- Expired at report time: `false`

## Local setup / dependencies

- Both authorized fixture commands used the pre-existing passwordless-sudo
  Docker Engine path. No Docker daemon or host configuration changed.
- The fixture built/started only its exact disposable project graph and removed
  its exact containers, networks, volumes, and orphans after each attempt.
- The existing frozen uv environment was used; no package, production
  dependency, or lockfile changed.
- New package/system dependency installation: none.
- Durable setup change: none.
- Local supply-chain/scanner execution: none.

## Documentation impact

No durable product, configuration, deployment, operations, API, security, or
architecture behavior changed, so no product documentation was edited. The
immutable 009-b order and this report record the diagnostic behavior and
remaining fixture limitation. The accepted 009-a connection documentation
remains exact.

## Safety and scope confirmations

- Unrelated files changed: no.
- Changes outside the preferred activated paths: no.
- 009-a order/report edited: NO; both hashes are recorded above.
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
- Wrong credential or role accepted: no.
- Authentication or adjacent product scope added: no.
- Dependency, lockfile, workflow, Dockerfile, image, scanner, supply-chain
  policy, notice, exception, architecture, security, or protocol changed: no.
- Targeted sudo fixture cap exceeded: NO — exactly 2 attempts.
- Implementation commit/check-generation cap exceeded: NO — exactly 1 before
  this mandatory report-only commit.
- Local full supply-chain/image gate, full Compose smoke, or full matrix run:
  NO.
- Broad Docker prune, reset, clean, checkout, destructive cleanup, or force
  push performed: no.
- Extra objective-009 PR created: NO.
- PR `#12` or `#13` acted on: NO.
- PR merged by coding agent: NO.
- Auto-merge enabled by coding agent: NO.
- Report-publication commit changes only this report file: yes.

## Known limitations / blockers

- The unreadable-secret mode helper cannot traverse the isolated volume's
  `0700`, UID-10001 root with its current fixture-only capability set. This is
  the safe diagnostic inference from the exact `set-file-mode` command failure
  and source; child details were correctly suppressed.
- Because attempt 2 stopped there, unreadable-secret readiness/liveness/NGINX
  assertions, unsafe-marker, migration-mismatch, stopped-PostgreSQL, and final
  recovery remain not-run in this round.
- Both local attempts and the one implementation/check generation are
  exhausted. Further implementation requires a new strategic amendment.
- PR `#14` remains unmergeable by policy with one failed check. The coding
  agent has not merged or enabled auto-merge.

## Recommended strategic follow-up

Activate one further tightly bounded objective-009 amendment. Add only
`DAC_READ_SEARCH` to the disposable `_set_control_mode` helper command (not to
any Compose service), retain `FOWNER`, and run one complete targeted sudo
fixture through unreadable-secret, marker, migration, stopped-PostgreSQL, and
recovery. If green, push one correction and require all 20 checks plus zero
alerts. Independently verify this SELF report commit, its first parent, single-
PR correlation, exact attempt caps, and unchanged 009-a artifacts before any
acceptance decision.
