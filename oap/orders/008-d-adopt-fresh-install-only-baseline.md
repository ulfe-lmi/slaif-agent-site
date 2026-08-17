# OAP Work Order — 008-d

## Objective

Amend PR `#11` to adopt the human-confirmed product truth that there are no
existing installations or persistent databases to migrate. Restore the
objective-008 product tree to the accepted 008-a supply-chain implementation,
remove the obsolete mandatory Trixie-to-Alpine transition gate introduced by
008-b, discard the uncommitted 008-c prototype exactly, and document that the
initial supported PostgreSQL baseline is a fresh Alpine-created volume.

This is the terminal correction for objective `008`. Do not perform another
compatibility experiment, migration, guard design, image change, or broad local
supply-chain run.

## Human domain decision

The human owner explicitly confirmed:

> There are zero existing installations and zero persisted user databases.
> All supported installations will be fresh.

Therefore:

- Trixie-created raw-volume compatibility is not a product requirement;
- the first supported database baseline is
  `postgres:18.6-alpine3.23` at the currently pinned digest;
- supported in-place updates must remain within the compatible Alpine/musl
  family unless a future separately designed logical migration says otherwise;
- raw volume reuse across glibc/musl families is unsupported;
- 008-b/008-c remain immutable audit evidence, not mandatory product behavior.

## Hard execution budget

- Target executor duration: at most 30 minutes.
- Targeted compatibility attempts: 0.
- Local `tools/supply_chain/run.sh`: 0.
- Local full Python/PostgreSQL/Compose matrices: 0.
- Maximum implementation commits/check generations: 1, plus the final
  report-only commit.

If exact rollback/scope cannot be established safely, report `PARTIAL` rather
than exploring.

## GitHub objective state

- Numeric objective: `008`
- Execution round: `008-d`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#11`
- Existing PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/11>
- Required head branch: `oap/008-supply-chain-build-gates`
- Base branch: `main`
- Current remote PR head:
  `e816700c9077d7cb00d6cdb945793076f142aa1f`
- Previous delivered implementation head:
  `c141ce8f6d73ebb290f6054429e138223bd103fa`
- Required PR title:
  `[OAP 008] Add reproducible supply-chain and SBOM gates`

Preserve all 008-a/008-b/008-c orders and reports exactly. No new PR or merge.

## Known local recovery state

The 008-c report truthfully records an uncommitted prototype in exactly:

```text
docs/DEPLOYMENT.md
docs/OPERATIONS.md
services/backend/src/slaif_agent_site/bootstrap/service.py
services/backend/src/slaif_agent_site/db/collation.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/unit/test_process_entrypoints.py
tests/packaging/postgres-base-transition.sh
tests/packaging/test_postgres_base_transition.py
```

Before editing, inspect the current worktree and confirm every dirty byte maps
to that coding-agent-owned prototype and no human/unrelated change exists.
Then restore the tracked paths to the current remote PR head and remove only
the untracked `collation.py`. Do not use a broad reset/clean/checkout or remove
any other path.

## Required final-tree correction

Restore all non-OAP product/policy/test/documentation changes introduced by
the 008-b implementation commits to their exact 008-a state. Concretely:

- remove the mandatory historical transition step from CI;
- remove the historical transition record/validator from machine policy;
- remove the transition shell/static tests;
- remove detailed upgrade-compatibility documentation that implies legacy
  installation support;
- retain all 008-a supply-chain, reproducibility, license, SBOM, vulnerability,
  evidence, OCI-label, notice, and scanner behavior unchanged.

Do not revert or edit any OAP order/report. Do not rewrite history. Use one
ordinary additive commit whose final tree restores the relevant product paths.

Add only a concise documentation clarification, if not already expressible by
the restored text:

```text
Initial supported PostgreSQL installations are fresh Alpine/musl volumes.
Raw data volumes are not portable between glibc and musl image families.
No legacy installation or cross-family migration is supported in this
pre-alpha release. Never delete a non-disposable volume merely to bypass this
boundary; future real migrations require a separately tested logical process.
```

The clarification must not add a runtime guard or migration promise.

Container OS/runtime SBOM evidence remains a 14-day CI artifact. Keep the
existing explicit rule that durable license text/notice/source-offer review is
required before any image publication; do not build release packaging here.

## Allowed path scope

Only these non-OAP paths may differ from the current remote head:

```text
.github/workflows/ci.yml
README.md
docs/DEPLOYMENT.md
docs/OPERATIONS.md
docs/SUPPLY_CHAIN.md
supply-chain/policy.json
tests/packaging/postgres-base-transition.sh        (delete)
tests/packaging/test_postgres_base_transition.py  (delete)
tests/supply_chain/test_policy.py
tools/supply_chain/policy.py
```

Plus `oap/active`, the new 008-d order, and final 008-d report. Prefer the
smallest exact set. No application/backend code, Dockerfile, Compose file,
lock, scanner/evidence runner, exception, notice inventory, migration, role,
service, image, network, volume, or action pin may change.

## Verification discipline

Run only:

- worktree-recovery scope/hash inspection;
- focused policy/repository/packaging tests affected by removing the obsolete
  transition requirement;
- policy/notice drift checks;
- Ruff/format only if Python policy code changes;
- Markdown on changed docs;
- `git diff --check` and exact final-tree comparison proving all retained 008-a
  implementation paths match their intended state.

Do not run locally:

```text
transition fixture
tools/supply_chain/run.sh
image reproducibility/SBOM/Grype gate
full Compose smoke
full Python matrix
full PostgreSQL matrix
```

GitHub runs the unchanged full check set once on the implementation commit.

## Acceptance criteria

1. PR `#11` remains the unique objective-008 PR and is amended once; no new PR,
   force push, merge, exception, or prior-artifact edit occurs.
2. The 008-c uncommitted prototype is removed exactly with no unrelated
   worktree loss.
3. The final non-OAP tree retains all 008-a supply-chain functionality and no
   longer carries a mandatory unsupported legacy transition gate.
4. Documentation states fresh Alpine-only initial support and no cross-libc raw
   volume portability/migration promise.
5. No transition/full supply-chain/matrix test runs locally; the report has an
   exact attempt/command ledger.
6. All GitHub checks on the implementation and final report head succeed with
   zero open CodeQL alerts.
7. `oap/active` is `008-d`, all four rounds correlate uniquely, and report
   publication follows protocol 1.2.

## GitHub workflow

Fetch/verify PR `#11`, clean only the recorded local prototype, amend the same
branch with one implementation/orchestration commit, and never create another
PR or merge.

## Required report

Atomically publish exactly:

```text
oap/reports/008-d-adopt-fresh-install-only-baseline.md
```

Use protocol 1.2 in full. Include the human decision, exact restored/deleted
paths, prototype cleanup evidence, local-command restraint, final tree
comparison, GitHub checks, scope/security/no-merge confirmations, literal
implementation head, and `Report publication commit: SELF`.
