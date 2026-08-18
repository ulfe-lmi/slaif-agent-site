# OAP Work Order — 009-d

## Objective

Amend PR `#14` so the Control-readiness fixture accepts the two already
documented, bounded database-outage reasons only during the stopped-PostgreSQL
stage, then run the complete fixture once through recovery. Do not change
Control product behavior, timeout values, or any production authority.

## Hard execution budget

- Target executor duration: at most 20 minutes; hard stop at 25 minutes.
- Targeted sudo fixture attempts: 1 maximum.
- Implementation commits/check generations: 1 maximum.
- GitHub workflow reruns: 0.
- Broad local gates, supply-chain/image scans, full Compose smoke, and full
  Python/PostgreSQL matrices: 0.

If the sole fixture attempt fails, publish `PARTIAL` with its safe category and
stop. No second attempt, manual Docker reproduction, second fix, or check
generation is authorized.

## GitHub objective state

- Numeric objective: `009`
- Execution round: `009-d`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#14`
- Existing PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/14>
- Required branch: `oap/009-control-database-readiness`
- Base branch: `main`
- Current remote/report head:
  `aa3a6837165f6d306a893576d5b57ea4ac05e8b5`
- 009-c implementation head:
  `ae7f283037c86799f0971400b83f6afcf249c976`
- Required title: `[OAP 009] Wire Control API database readiness boundary`

PR `#14` is the unique objective-009 PR. Preserve every 009-a through 009-c
order/report exactly. Do not create another PR, force-push, merge, close, or
enable auto-merge.

## Strategic context and verified diagnosis

009-c passed baseline, wrong-login, wrong-role, unreadable-secret,
unsafe-marker, and migration-mismatch. Both its sole local run and GitHub then
timed out while the fixture awaited only `connection_unavailable` after
stopping PostgreSQL.

The product contract intentionally exposes both stable reasons:

```text
connection_unavailable
timeout
```

`ControlDatabase.readiness()` returns the former for a prompt asyncpg/OS
connection failure and the latter for a bounded acquire/command timeout. The
shared readiness wrapper also returns bounded `timeout` when its two-second
probe deadline wins. `docs/DATABASE_CONNECTIONS.md`, `docs/OPERATIONS.md`, and
009-a require both reasons and require only that stopped PostgreSQL makes
Control readiness 503, keeps liveness 200, and makes NGINX unready.

The fixture's exact-one-reason expectation was therefore narrower than the
implemented and documented fail-closed contract. Product code, settings, and
documentation are not defective and must not change.

## Bounded scope

Change only:

```text
tools/compose/control_readiness.py
tests/packaging/test_compose_policy.py
oap/active
oap/orders/009-d-accept-bounded-database-outage-reasons.md
oap/reports/009-d-accept-bounded-database-outage-reasons.md
```

No other path may change.

## Non-goals

- Do not change Control API/application/config/database/health source,
  connection or readiness timeout values, exception classification, pool
  behavior, credentials, roles, migrations, or reason vocabulary.
- Do not change `compose.yaml`, any service or helper capability, secret
  initializer/mount, dependency, lockfile, workflow, Dockerfile, image,
  supply-chain policy, documentation, architecture, security policy, or prior
  OAP artifact.
- Do not weaken wrong-login, wrong-role, unreadable-secret, unsafe-marker, or
  migration-mismatch to accept multiple reasons.
- Do not accept `probe_error`, `shutdown`, a missing database component, a 200
  response, or any unbounded/unknown reason for the outage stage.
- Do not add authentication or adjacent product behavior.

## Requirements

### A. Exact outage predicate

Make the smallest fixture-only change so `_wait_readiness` can match a bounded
set of expected reasons while retaining its current exact status/document/
database-component checks.

At the stopped-PostgreSQL call site only, accept exactly:

```text
{connection_unavailable, timeout}
```

All other negative stages must continue to accept exactly their existing
single documented reason. Ready state must still require status 200,
`status=ready`, `database.status=ok`, and a null reason.

Add focused unit/static tests proving both outage reasons match only a 503
`not_ready`/database-unavailable response; an unknown or third reason, absent
component, malformed response, and 200 response do not match. Retain all
009-b/009-c secret-free diagnostics and exact helper confinement tests.

### B. One complete targeted fixture run

After focused static checks pass, run exactly once:

```text
sudo python tools/compose/control_readiness.py slaif009dfix
```

It must complete and print every stage:

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

It must still prove liveness 200 and NGINX unready during stopped PostgreSQL,
restart PostgreSQL, await container health, return Control/NGINX to ready, emit
the exact success summary, and leave no container, network, or volume with the
`slaif009dfix` prefix.

If it fails, record only the allowlisted stage/operation/reason, clean up,
publish `PARTIAL`, and stop.

### C. GitHub and immutable report

If the local run passes, push one implementation/orchestration commit and let
the unchanged complete 20-check GitHub set run once. Do not rerun it. A
repository failure is `PARTIAL`; pending checks at the hard stop are reported
honestly for strategic follow-up.

## Acceptance criteria

1. PR `#14` remains the unique objective-009 PR and is amended once; no new PR,
   force push, prior-artifact edit, merge, close, or auto-merge occurs.
2. Only the stopped-PostgreSQL fixture stage accepts exactly
   `connection_unavailable` or `timeout`; every other reason contract remains
   exact and no product/Compose behavior changes.
3. Focused tests prove strict 503/not-ready/database-unavailable matching and
   reject all broader states/reasons.
4. At most one targeted sudo fixture run occurs and completes every stage,
   stopped-database liveness/NGINX assertions, recovery, and exact cleanup.
5. All prior credential, role, secret, marker, migration, confinement, and
   secret-free diagnostic evidence remains green.
6. All 20 GitHub checks pass with zero open CodeQL alerts before strategic
   merge.
7. `oap/active` is `009-d`, all four rounds correlate uniquely to PR `#14`,
   and report publication follows protocol 1.2.

## Verification required

Run only the directly affected packaging/static tests, Ruff/format on the two
changed Python files, mypy, Python compile, repository/Compose static policy,
`docker compose config --quiet`, exact allowed-path/prior-artifact checks,
`git diff --check`, the one authorized fixture command, and the one automatic
GitHub check generation.

Do not run locally:

```text
tools/supply_chain/run.sh
full image/SBOM/Grype gate
full Compose smoke
full Python matrix
full PostgreSQL matrix
```

## Documentation required

None. Current documentation already lists both bounded reasons and states that
stopped PostgreSQL leaves Control and NGINX unready. Do not edit it.

## Safety / security constraints

Use only the fake disposable project and exact cleanup. Never print a locator,
password, child command/output, container environment, driver exception, or
unbounded observed value. Preserve fixed login/role validation, mount/helper
confinement, fail-closed status, and every production capability set.

## Local execution capability

Passwordless sudo and Docker are already verified. Routine execution remains
with the coding agent; no package installation or human terminal work should
be required.

## GitHub workflow

Fetch/verify PR `#14`, amend only its existing branch with one implementation
commit, and never create another PR or merge. Commit the strategic order and
`oap/active` unchanged with the implementation. Publish the report as the
final report-only `SELF` commit whose parent is the literal implementation
head.

## Required report

Atomically publish exactly:

```text
oap/reports/009-d-accept-bounded-database-outage-reasons.md
```

Use protocol 1.2 in full. Include the one-attempt ledger, exact reason
predicate, complete stage/liveness/NGINX/recovery/cleanup evidence or bounded
failure, local-run restraint, GitHub checks/alerts, allowed-path and prior-
artifact integrity, single-PR/no-merge confirmations, literal implementation
head, and `Report publication commit: SELF`.
