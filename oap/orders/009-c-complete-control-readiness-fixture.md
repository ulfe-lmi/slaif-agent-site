# OAP Work Order — 009-c

## Objective

Amend PR `#14` with the single fixture-only permission correction identified
by 009-b, then run one complete Control-readiness fixture from baseline through
all negative states and recovery. No product behavior, credential policy,
Compose service capability, or adjacent authentication scope may change.

## Hard execution budget

- Target executor duration: at most 20 minutes; hard stop at 25 minutes.
- Targeted sudo fixture attempts: exactly 1 maximum.
- Implementation commits/check generations: 1 maximum.
- GitHub workflow reruns: 0; report a genuine external failure rather than
  extending this turn.
- Local full supply-chain/Image/SBOM/Grype runs: 0.
- Local full Compose smoke: 0.
- Local full Python/PostgreSQL matrices: 0.

If the single targeted fixture attempt does not complete successfully, publish
`PARTIAL` with the safe stage/operation/reason and stop. Do not diagnose with a
second Docker attempt and do not make a second implementation generation.

## GitHub objective state

- Numeric objective: `009`
- Execution round: `009-c`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#14`
- Existing PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/14>
- Required branch: `oap/009-control-database-readiness`
- Base branch: `main`
- Current remote/report head:
  `fd878f148613b29b8ea21acf3d8734d20f6be585`
- 009-b implementation head:
  `c7dbd0f3da7a4cdf582da340a3c5b2d39223b9e4`
- Required title: `[OAP 009] Wire Control API database readiness boundary`

PR `#14` is the unique objective-009 PR. Preserve the 009-a and 009-b orders
and reports exactly. Do not create another PR, force-push, merge, close, or
enable auto-merge.

## Strategic context and verified failure

009-b safely diagnosed and corrected the original wrong-login fixture failure.
Its second and final permitted local run, independently reproduced by GitHub,
passed baseline, wrong-login, and wrong-role, then failed at:

```text
stage=unreadable-secret operation=set-file-mode reason=command-failed
```

The disposable `_set_control_mode` helper drops all capabilities and adds only
`FOWNER`, but the isolated secret file is below a `0700` directory owned by UID
10001. The helper running as UID 0 therefore lacks directory traversal after
capabilities are dropped. `_replace_control_file` already demonstrates the
relevant confined helper pattern and includes `DAC_READ_SEARCH`.

This is a test-fixture helper defect, not a Control application or production
container defect. The fixed Control login/role checks, liveness/readiness
contract, isolated secret mount, and production capability sets must remain
unchanged.

## Bounded scope

Change only:

```text
tools/compose/control_readiness.py
tests/packaging/test_compose_policy.py
oap/active
oap/orders/009-c-complete-control-readiness-fixture.md
oap/reports/009-c-complete-control-readiness-fixture.md
```

No other path may change.

## Non-goals

- Do not change Control API source, config, database/pool behavior, migrations,
  roles, readiness reasons, or health endpoints.
- Do not change `compose.yaml`, any service capability, secret initializer or
  mount, dependency, lockfile, workflow, Dockerfile, image, supply-chain
  policy, documentation, architecture, security policy, or prior OAP artifact.
- Do not add authentication, setup, user, site, or workspace behavior.
- Do not broaden diagnostics or print subprocess commands/output.
- Do not run a second targeted fixture attempt, an equivalent manual Docker
  reproduction, or any broad local gate.

## Requirements

### A. Minimal helper-only correction

Add `DAC_READ_SEARCH` only to the ephemeral `docker run` command created by
`_set_control_mode`, retaining `--network none`, `--read-only`, `--cap-drop
ALL`, `FOWNER`, UID/GID `0:0`, the exact isolated volume mount, and the bounded
Python chmod program.

Do not add `DAC_OVERRIDE` to this helper and do not modify any Compose service
capability. The helper exists only to create an unreadable/readable fixture
state and is not part of the product runtime.

Extend the static/unit contract to prove the exact helper command contains
only the required confined boundary and that the production Compose file is
unchanged. Retain all 009-b allowlisted, secret-free diagnostics.

### B. One final targeted fixture run

After directly affected static checks pass, run exactly once:

```text
sudo python tools/compose/control_readiness.py slaif009cfix
```

The run must complete and print every stage:

```text
baseline
wrong-login
wrong-role
unreadable-secret
unsafe-marker
migration-mismatch
stopped-postgres
recovery
```

For each negative state, verify the fixture's existing contract: Control
liveness remains 200, database readiness is 503 with its exact bounded reason,
NGINX reports the dependency unready, restoration converges, and final recovery
returns ready. The success summary must remain exact and cleanup must leave no
container, network, or volume with the `slaif009cfix` prefix.

If any stage fails, record only the safe stage/operation/reason, clean up,
publish `PARTIAL`, and stop. No second attempt is authorized.

### C. GitHub and immutable report

If the single local run passes, push one implementation/orchestration commit.
Allow the unchanged complete 20-check GitHub set to run once. Do not rerun or
regenerate it in this turn. A repository failure is `PARTIAL`; a pending check
at the hard stop is reported honestly for strategic follow-up.

The report must include start/end/duration for the one fixture attempt, every
completed stage, cleanup evidence, exact safe diagnostics if it fails,
confirmation that no broad local gate ran, and exact GitHub check state.

## Acceptance criteria

1. PR `#14` remains the unique objective-009 PR and is amended once; no new PR,
   force push, prior-artifact edit, merge, close, or auto-merge occurs.
2. Only the disposable `_set_control_mode` helper receives
   `DAC_READ_SEARCH`; product/Compose authority and all 009-a behavior remain
   unchanged.
3. Static tests prove the helper's exact confined command and retain the
   allowlisted secret-free diagnostic contract.
4. At most one targeted sudo fixture run occurs and it completes baseline,
   every negative state, and recovery with exact cleanup.
5. Wrong credentials/roles remain rejected; Control remains live while
   readiness/NGINX fail closed with bounded reasons and recover cleanly.
6. All 20 GitHub checks pass and there are zero open CodeQL alerts before
   strategic merge.
7. `oap/active` is `009-c`, all three rounds correlate uniquely to PR `#14`,
   and final report publication follows protocol 1.2.

## Verification required

Run only:

- the directly affected packaging/static tests;
- Ruff and format check on the two changed Python files;
- mypy;
- `python -m py_compile tools/compose/control_readiness.py`;
- repository/Compose policy checks that do not start the full stack;
- `docker compose config --quiet`;
- `git diff --check` and exact allowed-path/prior-artifact checks;
- the one authorized targeted sudo fixture command above;
- the one automatic GitHub 20-check generation.

Do not run locally:

```text
tools/supply_chain/run.sh
full image/SBOM/Grype gate
full Compose smoke
full Python matrix
full PostgreSQL matrix
```

## Documentation required

No product documentation change is expected because this is a fixture-only
correction. Do not edit documentation unless an unexpected product defect is
found; if that occurs, stop and report instead of expanding scope.

## Safety / security constraints

Use only the fake disposable project and exact cleanup. Never print a locator,
password, command containing secret material, subprocess stdout/stderr,
container environment, or driver exception. Preserve fixed login/role
validation, isolated mounts, liveness/readiness failure behavior, and all
production capability sets.

## Local execution capability

- Routine local setup remains the coding agent's responsibility.
- Passwordless sudo and Docker are already verified.
- No new package or service installation should be necessary.
- Do not transfer routine execution to the human or strategic model.

## GitHub workflow

Fetch and verify PR `#14`, amend only its existing branch with one
implementation commit, and never create another PR or merge. Commit the
strategic order and `oap/active` unchanged with the implementation. Publish the
report as the final report-only `SELF` commit whose first parent is the literal
implementation head.

## Required report

Atomically publish exactly:

```text
oap/reports/009-c-complete-control-readiness-fixture.md
```

Use protocol 1.2 in full. Include the single-attempt ledger, exact helper
change, complete stage/recovery evidence or bounded failure, cleanup, local-run
restraint, GitHub checks/alerts, allowed-path/prior-artifact integrity,
single-PR/no-merge confirmations, literal implementation head, and
`Report publication commit: SELF`.
