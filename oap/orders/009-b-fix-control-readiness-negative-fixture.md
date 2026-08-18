# OAP Work Order — 009-b

## Objective

Amend PR `#14` to diagnose and fix the single failing Control readiness
negative fixture, then prove the complete wrong-login through recovery
sequence. Preserve the accepted Control credential/pool/function/readiness
implementation unless the diagnostic identifies a genuine product defect.

No authentication or adjacent scope may be added.

## Hard execution budget

- Target executor duration: at most 30 minutes.
- Targeted sudo fixture attempts: at most 2.
- Implementation commits/check generations: 1.
- Local full supply-chain/Image/SBOM/Grype runs: 0.
- Local full Compose smoke: 0.
- Local full Python/PostgreSQL matrices: 0.

If two targeted attempts do not produce a passing full fixture, report
`PARTIAL`; do not continue.

## GitHub objective state

- Numeric objective: `009`
- Execution round: `009-b`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#14`
- Existing PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/14>
- Required branch: `oap/009-control-database-readiness`
- Base branch: `main`
- Current remote head:
  `e3a5ed2e3408fc3a0d49933f5d5a6bcc934c2b3e`
- Previous implementation head:
  `f8c87dbead42383f7f810a3ba8ff631a04e14a04`
- Required title: `[OAP 009] Wire Control API database readiness boundary`

Preserve the 009-a order/report exactly. Do not create a new PR or merge.

## Verified failure boundary

On the final 009-a implementation head:

- clean Compose startup is green;
- isolated Control secret, pool, database function, readiness, NGINX, role,
  mount, and ordinary secret policies are green;
- 19 of 20 checks pass and CodeQL alerts are zero;
- `Compose and edge packaging` fails immediately after printing
  `control-readiness-stage: wrong-login`;
- the fixture catches every subprocess failure as one generic `FixtureError`
  and discards child output, so GitHub cannot distinguish file replacement,
  container recreation, health convergence, liveness, or NGINX assertion.

Source review shows the product intentionally keeps the app live and returns
`configuration_invalid` when a DSN's username differs from the fixed Control
login. The diagnostic must determine whether the failure is in the fixture or
that product contract.

## Allowed path scope

Prefer changing only:

```text
tools/compose/control_readiness.py
tests/packaging/test_compose_policy.py
tests/packaging/test_local_secrets.py
services/backend/tests/unit/test_control_database.py
services/backend/tests/unit/test_control_config.py
services/backend/src/slaif_agent_site/control_api/config.py
services/backend/src/slaif_agent_site/control_api/database.py
docs/DATABASE_CONNECTIONS.md
docs/OPERATIONS.md
oap/active
oap/orders/009-b-fix-control-readiness-negative-fixture.md
oap/reports/009-b-fix-control-readiness-negative-fixture.md
```

Product source changes are allowed only if the diagnostic proves the fixture
correctly exposed a real Control failure. Do not change migration, roles,
Compose topology, secret generator/mount, dependency, lockfile, workflow,
Dockerfile, supply-chain policy, image, or prior artifact.

## Requirements

### A. Safe diagnostic categories

Before the first targeted run, change the fixture error boundary so a failure
emits only stable, non-secret categories such as:

```text
stage=wrong-login
operation=replace-file | recreate-control | await-readiness |
          assert-liveness | assert-nginx | restore
reason=command-failed | timeout | malformed-response | state-mismatch
```

Do not print the subprocess command, stdout/stderr, container environment,
locator path contents, DSN, user password, driver exception, or arbitrary
child text. Add unit/static tests proving diagnostics are allowlisted and
secret-free.

### B. One diagnostic run with known working Docker authority

Run exactly once initially with the verified passwordless-sudo Docker path and
one exact disposable project prefix. Record the stage/operation/reason and
cleanup.

Use that evidence to make one minimal fix:

- if fixture-only, change only the fixture/test contract;
- if product behavior, change only the Control config/pool behavior necessary
  to preserve liveness plus bounded `configuration_invalid` readiness;
- do not relax fixed login/role validation or accept a wrong credential.

### C. One final targeted verification

Run the fixture once more with sudo. It must complete every stage:

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

For every negative state, Control liveness stays 200, database readiness is
503 with the exact bounded reason, NGINX dependency response is unready, and
recovery returns ready. Exact cleanup must pass.

No third local fixture attempt is permitted.

### D. GitHub and report

Push one implementation/orchestration commit after the final targeted run is
green. GitHub runs the unchanged complete 20-check set once. External setup
failures may be rerun on the same head; a repository failure requires
`PARTIAL`, not another implementation generation.

The report must include both attempts with timestamps/durations, exact safe
diagnostic categories, root cause, fix, cleanup, and confirmation that no
broad local gate ran.

## Acceptance criteria

1. PR `#14` remains the unique objective-009 PR and is amended once; no new PR,
   merge, force push, or prior-artifact edit occurs.
2. Fixture diagnostics identify a stable stage/operation/reason without child
   output or secret leakage.
3. Exactly two or fewer sudo fixture attempts run; the final attempt completes
   all negative and recovery stages.
4. Wrong credentials/roles remain rejected; Control liveness and sanitized
   readiness behavior match the architecture.
5. The accepted 009-a implementation boundaries remain intact and no adjacent
   product/auth scope is added.
6. All 20 GitHub checks pass with zero open CodeQL alert.
7. `oap/active` is `009-b`, both rounds correlate uniquely, and final report
   publication follows protocol 1.2.

## Verification required

Run only the safe diagnostic/static tests, at most two targeted sudo fixture
runs, directly affected unit/packaging checks, Ruff/format/mypy on changed
Python, docs if changed, repository policy, and `git diff --check`.

Do not run locally:

```text
tools/supply_chain/run.sh
full image/SBOM/Grype gate
full Compose smoke
full Python matrix
full PostgreSQL matrix
```

## Safety constraints

Use fake disposable resources and exact cleanup. Never print a locator,
password, command containing secret material, or child output. Do not weaken
identity, role, mount, health, or NGINX failure behavior.

## GitHub workflow

Fetch/verify PR `#14`, amend its existing branch with one implementation
commit, and never create another PR or merge.

## Required report

Atomically publish exactly:

```text
oap/reports/009-b-fix-control-readiness-negative-fixture.md
```

Use protocol 1.2 in full. Include the diagnostic/attempt ledger, exact fix,
complete negative/recovery evidence, local-run restraint, GitHub checks,
scope/security/no-merge confirmations, literal implementation head, and
`Report publication commit: SELF`.
