# OAP Work Order — 008-c

## Objective

Amend PR `#11` with the smallest safe resolution of the proven PostgreSQL
incompatibility: the one-shot Compose bootstrap must detect an unavailable or
mismatched database collation version before any provisioning/migration/COW
mutation, fail with the existing constant safe CLI error, and prevent NGINX/
application readiness while leaving the old volume recoverable with its exact
Trixie image.

Do not implement migration, dump/restore, collation refresh, reindex, image
rollback, vulnerability exception, or data deletion.

## Hard execution budget

- Target executor duration: at most 45 minutes.
- Maximum targeted transition attempts: 2.
- Maximum implementation commits/check generations: 2.
- Local `tools/supply_chain/run.sh` executions: 0.
- Local full image/SBOM/Grype, Python matrix, PostgreSQL matrix, or complete
  Compose smoke executions: 0.

If the cap is reached, report `PARTIAL`; do not expand the solution.

## GitHub objective state

- Numeric objective: `008`
- Execution round: `008-c`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#11`
- Existing PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/11>
- Required head branch: `oap/008-supply-chain-build-gates`
- Base branch: `main`
- Required PR title:
  `[OAP 008] Add reproducible supply-chain and SBOM gates`
- Current remote PR head:
  `691ebf1f0aeef122ee1eaf9aca0f111fc9125ccf`
- Previous implementation head:
  `c141ce8f6d73ebb290f6054429e138223bd103fa`
- Required delivery: amend PR `#11`; no new PR or merge.

008-b proved that a Trixie-created 18.6 volume remains physically readable on
Alpine 18.6 but is not collation-compatible: stored glibc version `2.41` has no
actual version under Alpine, and PostgreSQL warns on every connection. The
008-b report is `PARTIAL`; its exact test evidence and failed mandatory Compose
check must remain immutable.

## Allowed path scope

Only these path families may change, plus the new OAP order/report and active
pointer:

```text
.github/workflows/ci.yml
README.md
docs/CONFIGURATION.md
docs/DEPLOYMENT.md
docs/OPERATIONS.md
services/backend/src/slaif_agent_site/bootstrap/service.py
services/backend/src/slaif_agent_site/db/collation.py
services/backend/src/slaif_agent_site/db/__init__.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/unit/test_process_entrypoints.py
tests/packaging/postgres-base-transition.sh
tests/packaging/test_postgres_base_transition.py
tests/repository/test_repository_policy.py
tools/check_repository.py
oap/active
oap/orders/008-c-fail-closed-on-collation-incompatible-volume.md
oap/reports/008-c-fail-closed-on-collation-incompatible-volume.md
```

Prefer fewer paths. Do not change a Dockerfile, Compose topology/image,
lockfile, migration, role/grant model, supply-chain scanner/evidence code,
policy exception, vulnerability threshold, notice inventory, product service,
or prior OAP artifact.

## Requirements

### A. Read-only collation preflight

Add a small typed database-collation preflight called at the very beginning of
the explicit local `compose` bootstrap, before `provision(...)`, Alembic,
foundation deployment, role/login reconciliation, or marker mutation.

It must:

- connect only through the already validated provisioner/read-only inspection
  boundary;
- verify the expected database identity;
- read encoding, locale provider, collation, ctype, stored collation version,
  and actual collation version using PostgreSQL-version-compatible catalog
  logic across the supported PostgreSQL 14–18 matrix;
- accept an unversioned deterministic `C`/`POSIX`-class state only when the
  database reports it consistently;
- otherwise require a nonempty actual version exactly equal to the stored
  version;
- reject unavailable, mismatched, malformed, unsupported-provider, or
  ambiguous state with a stable internal reason category and no locale/user/
  credential leakage at the CLI boundary;
- perform no SQL mutation, role change, `SET ROLE`, schema change, refresh,
  reindex, or repair.

The public CLI remains exactly the constant failure:

```text
Database bootstrap failed.
```

Structured internal tests may assert stable non-secret reason codes; ordinary
logs/errors must not expose DSNs/passwords.

### B. Transition fixture becomes a fail-closed success test

Retain the exact old/new image and disposable volume fixture from 008-b, but
change its expected contract:

1. Build the exact accepted Trixie volume/bootstrap/data state.
2. Start Alpine on the unchanged volume only long enough to exercise the
   bootstrap preflight.
3. Require bootstrap to exit nonzero with the constant safe error before any
   product/bootstrap mutation.
4. Require dependent application/NGINX readiness to remain unavailable where
   the CI fixture models that dependency.
5. Verify the expected collation incompatibility reason through test-only
   non-secret evidence and retain the PostgreSQL warning as supporting proof.
6. Stop Alpine without repair.
7. Restart the exact old Trixie image on the same volume and prove all marker,
   roles/logins, privileges, rows, constraints, index/query digest, and locale
   facts are unchanged and valid.
8. Clean up only exact disposable resources.

The test should exit zero only when this protective refusal and recovery proof
both succeed. A compatible fresh Alpine-initialized database must still pass
normal Compose bootstrap and reach `EMPTY_SAFE safe=true`.

### C. Regression tests

Cover at minimum:

- exact stored/actual match accepted;
- actual version unavailable rejected;
- stored/actual mismatch rejected;
- consistent unversioned C/POSIX accepted;
- malformed/unknown provider rejected;
- database-name mismatch rejected;
- preflight occurs before a mocked/probed provisioning mutation;
- failure leaves bootstrap marker/roles/data unchanged;
- PostgreSQL 14–18 compatible query/function fallback behavior;
- constant CLI failure and no secret/DSN in error/log output.

Do not weaken the 008-b transition facts. The original in-place transition
remains documented as unsupported.

### D. Documentation and future migration boundary

Document:

- current clean Alpine installations remain supported;
- an old Trixie volume is detected and refused before mutation;
- the operator can recover by restarting the exact historical Trixie image;
- logical dump/restore or another migration procedure is not implemented in
  this objective and must be separately designed/tested before use;
- no volume should be deleted merely to bypass the guard;
- durable OS/runtime notice/source-offer review is still required before image
  publication.

Do not present fail-closed refusal as transition compatibility.

## Attempt ledger and run discipline

The report must list every targeted attempt with duration, stage, result, root
cause, change afterward, and confirm zero local full supply-chain runs.

Run focused tests first. Push only after the targeted transition/fresh-Alpine
tests pass. GitHub then runs the unchanged complete 20-check set once. At most
one corrective implementation commit is allowed for a genuine in-scope CI
defect. External setup failures may be rerun on the same head without code
change.

## Acceptance criteria

1. PR `#11` remains the unique objective-008 PR and is amended; no new PR,
   merge, exception, force push, or prior-artifact edit occurs.
2. Compose bootstrap performs the read-only collation preflight before any
   database mutation.
3. The exact incompatible Trixie volume is rejected with constant safe output,
   dependent readiness stays blocked, and no bootstrap/data/role state changes.
4. Restarting the exact Trixie image proves the volume remains fully
   recoverable with identical state/data/index/locale evidence.
5. Fresh Alpine and supported PostgreSQL 14–18 states still bootstrap/validate
   successfully; all preflight negative cases fail closed.
6. No repair/migration/reindex/refresh/deletion or supply-chain redesign is
   introduced.
7. The mandatory transition CI check now succeeds because the protective
   refusal is the expected safe behavior; all 20 checks are successful and
   open CodeQL alerts are zero.
8. Execution stays within budget and the complete attempt ledger is reported.
9. `oap/active` is `008-c`, all three rounds correlate uniquely, and final
   report publication follows protocol 1.2.

## Verification required

Run only focused collation/bootstrap unit/integration tests, the targeted
transition fixture, affected packaging/repository/Ruff/format/Markdown checks,
and `git diff --check`. Do not run locally:

```text
tools/supply_chain/run.sh
full image reproducibility/SBOM/Grype gate
full Python matrix
full PostgreSQL matrix
full Compose smoke
```

The unchanged complete gates run once in GitHub CI.

## Safety / security constraints

Use fake credentials and exact disposable resource names. No broad prune or
ordinary volume access. Never print secret material. The guard must remain
read-only and must not convert a warning into silent acceptance.

## GitHub workflow

Fetch/verify PR `#11`, amend its existing branch, respect the caps, and never
create another PR or merge.

## Required report

Atomically publish exactly:

```text
oap/reports/008-c-fail-closed-on-collation-incompatible-volume.md
```

Use protocol 1.2 in full. Include preflight ordering/evidence, transition and
recovery facts, attempt ledger, focused-test restraint, full GitHub results,
scope/security/no-merge confirmations, literal implementation head, and
`Report publication commit: SELF`.
