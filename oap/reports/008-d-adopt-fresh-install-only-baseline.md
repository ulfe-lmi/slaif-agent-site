# OAP Coding-Agent Report — 008-d

## Work order

- Identifier: `008-d`
- Work-order file:
  `oap/orders/008-d-adopt-fresh-install-only-baseline.md`
- Numeric objective: `008`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

PR `#11` now reflects the human-confirmed product truth that objective 008 has
no existing installations or persisted user databases to migrate. The exact
uncommitted 008-c prototype was removed without losing unrelated work. All
008-b transition-specific workflow, policy, test, and documentation changes
were then removed in one ordinary additive implementation commit.

The final non-OAP tree is the accepted 008-a implementation plus two concise
documentation additions: fresh PostgreSQL installations start on the pinned
Alpine/musl baseline, raw glibc/musl data volumes are not portable, this
pre-alpha release offers no legacy or cross-family migration, and image
publication needs durable OS/runtime license, notice, and source-offer review
beyond the 14-day CI evidence artifact.

No compatibility experiment, migration, runtime guard, image change, broad
local supply-chain run, full matrix, or full Compose run was performed. Focused
local checks passed. All 20 GitHub checks passed on implementation head
`9ffdab2f93ac8bf68b8ebc44c076febbf4810e7e`, and open CodeQL alerts were zero
for both the repository and the objective branch.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: `11`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/11>
- PR state at report time: `OPEN`
- Draft at report time: `false`
- Merge state at report time: `CLEAN`
- Base branch: `main`
- Base branch remote SHA at report time:
  `cc09342664a8ce60414474fd8d308ee459cd0dda`
- Head branch: `oap/008-supply-chain-build-gates`
- Starting remote SHA: `e816700c9077d7cb00d6cdb945793076f142aa1f`
- Implementation head SHA:
  `9ffdab2f93ac8bf68b8ebc44c076febbf4810e7e`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal SHA derived from
  GitHub)
- Implementation commits pushed before the report commit:
  `9ffdab2f93ac8bf68b8ebc44c076febbf4810e7e` —
  `fix: adopt fresh PostgreSQL baseline`
- Report commit first parent: same as Implementation head SHA
- Created a new PR this turn: no
- Amended existing PR this turn: yes
- Force push performed: no
- Merge performed: NO
- Auto-merge enabled: NO

The PR title remained exactly
`[OAP 008] Add reproducible supply-chain and SBOM gates`. The PR body was
amended before report publication to remove the superseded 008-b/008-c blocker
language and record the fresh-install decision, exact restoration, local
verification, 20 successful checks, and zero open CodeQL alerts.

## Changes made

### Exact 008-c prototype recovery

Before cleanup, the tracked dirty set was exactly the seven recorded prototype
paths plus strategic `oap/active`, and the untracked set was exactly the
prototype `collation.py` plus the strategic 008-d work order. The prototype
module was a regular file, not a symlink. No staged changes existed.

The following tracked prototype paths were restored from the then-current
remote PR head `e816700c9077d7cb00d6cdb945793076f142aa1f`:

- `docs/DEPLOYMENT.md`
- `docs/OPERATIONS.md`
- `services/backend/src/slaif_agent_site/bootstrap/service.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/unit/test_process_entrypoints.py`
- `tests/packaging/postgres-base-transition.sh`
- `tests/packaging/test_postgres_base_transition.py`

Only the untracked prototype file
`services/backend/src/slaif_agent_site/db/collation.py` was removed. A
post-cleanup status proof showed the only tracked dirty path was `oap/active`,
the only untracked path was the 008-d order, and `collation.py` was absent.
No broad reset, clean, checkout, or unrelated removal was used.

### Exact 008-b product-tree correction

The 008-b non-OAP delta was identified exactly against accepted 008-a
implementation head `9c732921e6c04eb21bf385cdd5964055bd8ed3eb`.
The following paths were restored byte-for-byte to their 008-a blobs:

- `.github/workflows/ci.yml`
- `docs/OPERATIONS.md`
- `supply-chain/policy.json`
- `tests/supply_chain/test_policy.py`
- `tools/supply_chain/policy.py`

The following obsolete transition-only files were deleted:

- `tests/packaging/postgres-base-transition.sh`
- `tests/packaging/test_postgres_base_transition.py`

`docs/DEPLOYMENT.md` and `docs/SUPPLY_CHAIN.md` were restored to 008-a and then
received only the two authorized documentation additions. The implementation
tree comparison between 008-a head and 008-d implementation head reported only
those two documentation files as different. The backend tree was unchanged
from the pre-execution remote head, and searches outside `oap/` found no
historical-transition policy key, transition-test name, exact old Trixie
digest, Trixie-to-Alpine requirement, or persistent-volume blocker text.

### Human decision adopted

- There are zero existing installations and zero persisted user databases.
- The first supported PostgreSQL baseline is the currently pinned
  `postgres:18.6-alpine3.23` image and a volume freshly initialized by it.
- Raw data-volume reuse between glibc and musl image families is unsupported.
- A future cross-family migration requires a separately designed and tested
  logical process; this round implements or promises none.
- Immutable 008-b and 008-c orders/reports remain audit evidence, not runtime
  behavior or mandatory CI gates.

## Files changed before report publication

- `.github/workflows/ci.yml`
- `docs/DEPLOYMENT.md`
- `docs/OPERATIONS.md`
- `docs/SUPPLY_CHAIN.md`
- `oap/active`
- `oap/orders/008-d-adopt-fresh-install-only-baseline.md`
- `supply-chain/policy.json`
- `tests/packaging/postgres-base-transition.sh` (deleted)
- `tests/packaging/test_postgres_base_transition.py` (deleted)
- `tests/supply_chain/test_policy.py`
- `tools/supply_chain/policy.py`

The implementation commit contains 209 insertions and 692 deletions across
exactly those 11 paths. Its first parent is
`e816700c9077d7cb00d6cdb945793076f142aa1f`. `README.md` and every other
allowed or non-allowed product path were untouched.

## Governance integrity

The governing files remained byte-identical at final-tree verification:

- `AGENTS.md` SHA-256:
  `9b5995dd14574f853b34c08c0378c901d6b197a3073556c779c6588bd4ac4e4e38`
- `OAP-COMMUNICATION-coding-agent.md` SHA-256:
  `e6150d6efb5a64e7f8af29b00514776972d4f98a0632281ddc260110c6374604`
- `ARCHITECTURE.md` SHA-256:
  `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- `SECURITY.md` SHA-256:
  `ec327af34d13406b560f75834d8bbda685f81dad17fd400cce0c5b6b8df4e23c`
- Activated work-order SHA-256:
  `7f16dccb08b08fc925bc6d8dc13e1cd388597e8d287df8519b1443f90ccda496`

No narrower `AGENTS.md` or `AGENTS.override.md` exists.

## Acceptance-criteria evidence

### Criterion 1 — unique PR and one safe amendment

- Result: PASS
- Evidence: GitHub search returned exactly one objective-008 PR: open,
  non-draft PR `#11`, base `main`, head
  `oap/008-supply-chain-build-gates`, with the required title. Exactly one
  implementation commit/check generation was pushed in 008-d. No new PR,
  force push, merge, auto-merge, exception, or prior-artifact edit occurred.

### Criterion 2 — exact 008-c prototype cleanup

- Result: PASS
- Evidence: the pre-cleanup tracked/untracked sets matched the work order
  exactly, and no staged or human/unrelated change existed. Seven tracked
  prototype paths were restored individually from the current remote head;
  only the exact untracked `collation.py` was removed. The post-cleanup status
  contained only the strategic active pointer and work order.

### Criterion 3 — 008-a supply-chain behavior without transition gate

- Result: PASS
- Evidence: exact blob comparison proved the retained workflow, operations,
  machine policy, policy test, and policy implementation match 008-a.
  Transition shell/static tests are absent. A full non-OAP tree comparison
  against 008-a reports only the two authorized documentation additions.
  Focused tests and all unchanged remote full gates passed.

### Criterion 4 — truthful fresh-Alpine documentation

- Result: PASS
- Evidence: `docs/DEPLOYMENT.md` states the fresh Alpine/musl baseline, raw
  glibc/musl non-portability, no pre-alpha legacy/cross-family migration, the
  no-delete rule for non-disposable volumes, and the requirement for a future
  separately tested logical migration.
- Evidence: `docs/SUPPLY_CHAIN.md` states that a 14-day CI artifact is not a
  durable release notice/source-offer bundle and cannot alone authorize image
  publication.

### Criterion 5 — exact local restraint and command ledger

- Result: PASS
- Evidence: compatibility attempts: 0. Local transition fixtures: 0. Local
  `tools/supply_chain/run.sh`: 0. Local image reproducibility/SBOM/Grype gates:
  0. Local full Compose smoke: 0. Local full Python matrices: 0. Local full
  PostgreSQL matrices: 0. Only the focused commands listed below ran.

### Criterion 6 — GitHub checks and CodeQL

- Result: PASS for the literal implementation head.
- Evidence: all 20 checks succeeded on
  `9ffdab2f93ac8bf68b8ebc44c076febbf4810e7e`; ordinary CI run
  `32074034087` and CodeQL run `32074034169` both completed successfully.
  GitHub reported zero open CodeQL alerts repository-wide and zero on the
  objective branch.
- SELF qualification: the report-only commit necessarily does not exist while
  its immutable contents are composed. In addition to protocol 1.2's required
  strategic verification, the coding agent will withhold FIFO `OK` until the
  SELF head's GitHub checks are terminal and successful; the report will not be
  rewritten to record its own future SHA or check run.

### Criterion 7 — four-round OAP correlation and protocol

- Result: PASS
- Evidence: `oap/active` is exactly the bytes `008-d\n`. The repository holds
  exactly the expected 008-a, 008-b, 008-c, and 008-d order files; the earlier
  three immutable reports are unchanged. All four rounds correlate to numeric
  objective `008`, PR `#11`, and the same head branch. This new report is
  published as a final report-only SELF commit whose first parent is the
  literal implementation head.

## Local verification

- Worktree dirty-path, file-type, and SHA-256 inspection before cleanup:
  PASSED — every dirty byte was owned by the recorded 008-c prototype or the
  strategic 008-d transcript; no unrelated/human change was present.
- Explicit post-cleanup status and absence checks: PASSED — exact strategic
  OAP paths remained and `collation.py` was absent.
- `git diff --name-status 9c732921e6c04eb21bf385cdd5964055bd8ed3eb --`
  on the nine affected non-OAP paths: PASSED — only `docs/DEPLOYMENT.md` and
  `docs/SUPPLY_CHAIN.md` differ.
- `git hash-object` versus `git rev-parse 9c732921e6c04eb21bf385cdd5964055bd8ed3eb:<path>`
  for the retained workflow, operations, policy JSON, policy test, and policy
  implementation: PASSED — all five matched.
- Explicit absence checks for both transition-test files and the prototype
  module: PASSED.
- `rg` for transition policy/test/digest/blocker terms outside `oap/`: PASSED
  — no matches.
- `uv run --frozen python -m tools.supply_chain.policy validate`: PASSED —
  `supply-chain-policy: OK`.
- `uv run --frozen python -m tools.supply_chain.policy notices --check`:
  PASSED — `third-party-notices: OK components=185`.
- `uv run --frozen pytest -q tests/supply_chain/test_policy.py
  tests/repository tests/packaging`: PASSED — 76 passed, 55 subtests passed.
- `python tools/check_repository.py`: PASSED — `PASS repository policy`.
- `uv run --frozen ruff check tools/supply_chain/policy.py
  tests/supply_chain/test_policy.py`: PASSED.
- `uv run --frozen ruff format --check tools/supply_chain/policy.py
  tests/supply_chain/test_policy.py`: PASSED — 2 files already formatted.
- `npx --yes markdownlint-cli2@0.22.0 ':docs/DEPLOYMENT.md'
  ':docs/SUPPLY_CHAIN.md' --config .markdownlint-cli2.yaml --no-globs`:
  PASSED — 2 files, 0 errors.
- `git diff --check`: PASSED.
- Final active-pointer, governance-hash, report-collision, backend-tree,
  retained-blob, branch-sync, and staged-scope checks: PASSED.
- Local PostgreSQL compatibility attempt or transition fixture: NOT RUN — zero
  attempts required and explicitly forbidden.
- Local `tools/supply_chain/run.sh`: NOT RUN — explicitly forbidden.
- Local image reproducibility/SBOM/Grype gate: NOT RUN — explicitly forbidden.
- Local full Compose smoke: NOT RUN — explicitly forbidden.
- Local full Python matrix: NOT RUN — explicitly forbidden.
- Local full PostgreSQL matrix: NOT RUN — explicitly forbidden.

No skipped, pending, missing, blocked, or not-run item above is represented as
passing evidence.

## GitHub CI / required checks

- Ordinary CI run: `32074034087` — SUCCESS
- CodeQL run: `32074034169` — SUCCESS
- Check state observed for implementation head:
  `9ffdab2f93ac8bf68b8ebc44c076febbf4810e7e`
- Analyze (actions): SUCCESS — 46s
- Analyze (javascript-typescript): SUCCESS — 46s
- Analyze (python): SUCCESS — 57s
- CodeQL aggregate: SUCCESS — 3s
- Dependency review: SUCCESS — 7s
- Detect supported languages: SUCCESS — 6s
- Foundation PostgreSQL 14: SUCCESS — 52s
- Foundation PostgreSQL 15: SUCCESS — 48s
- Foundation PostgreSQL 16: SUCCESS — 50s
- Foundation PostgreSQL 17: SUCCESS — 1m14s
- Foundation PostgreSQL 18: SUCCESS — 50s
- Markdown: SUCCESS — 7s
- Mermaid: SUCCESS — 50s
- Node contracts: SUCCESS — 1m11s
- Python 3.12 quality and package: SUCCESS — 31s
- Python 3.13 quality and package: SUCCESS — 1m9s
- Python 3.14 quality and package: SUCCESS — 30s
- Repository policy: SUCCESS — 5s
- Compose and edge packaging: SUCCESS — 2m3s
- Supply-chain evidence: SUCCESS — 4m43s
- Totals: 20 successful, 0 failed, 0 cancelled, 0 skipped, 0 pending
- All required checks green for the implementation head at report drafting:
  yes
- Open repository CodeQL alerts: 0
- Open objective-branch CodeQL alerts: 0
- Report-only commit may trigger fresh checks: strategic model must verify the
  `SELF` commit without rewriting this report. The coding agent will also
  verify those checks before sending FIFO `OK` for this stricter work order.

The successful supply-chain artifact is:

- Artifact ID: `9302874131`
- Name:
  `supply-chain-evidence-274d880a464cfd910ab2b014cddccd1194d40a9d`
- Size: 1,661,675 bytes
- Created: `2026-08-17T22:06:01Z`
- Expires: `2026-08-31T22:06:00Z`
- Expired at report time: `false`

## Local setup / dependencies

- `uv run --frozen` used the already synchronized frozen environment; no
  dependency or lockfile changed.
- `npx --yes markdownlint-cli2@0.22.0` used/populated only the ordinary local
  npm execution cache; no repository dependency or lockfile changed.
- Packages, production dependencies, system services, or durable host
  configuration installed or changed: none.
- `sudo`-level setup performed: none.
- Docker or PostgreSQL service used locally in this round: none.
- Durable setup changes committed/documented: none.

## Documentation

`docs/DEPLOYMENT.md` now truthfully defines fresh Alpine/musl PostgreSQL
volumes as the initial supported baseline and rejects raw cross-libc volume
portability or an implied migration promise. It preserves non-disposable data
and reserves any real future migration for separate design and testing.

`docs/SUPPLY_CHAIN.md` retains the publication boundary: time-bounded CI
inventory is evidence, not durable license/notice/source-offer packaging and
not publication authority. No release packaging was added.

No architecture, API, dependency, image, runtime, setup, security, migration,
or operating claim beyond those authorized clarifications changed.

## Safety and scope confirmations

- Unrelated files changed: no.
- Local uncommitted prototype remains: no; it was removed exactly as ordered.
- Production secrets accessed: no.
- Production systems accessed: no.
- Production or user data accessed: no.
- Credentials, DSNs, passwords, capability tokens, private artifact URLs, or
  session cookies printed or committed: no.
- Required tests skipped/not run: no. The broad local gates explicitly
  forbidden by the work order were not run; the unchanged full GitHub set ran
  and passed.
- Scope deviation: no.
- Changes outside the allowed non-OAP path list: no.
- Application/backend code, Dockerfile, Compose file, lockfile, scanner,
  evidence runner, notice inventory, action pin, image, migration, role/grant,
  service, network, volume, capability, authorization, or exception changed:
  no.
- Compatibility experiment, runtime guard, migration, dump/restore,
  `pg_upgrade`, collation refresh, reindex, repair, volume initialization,
  operator-volume deletion, or image change performed: no.
- Broad reset, clean, checkout, prune, or destructive cleanup performed: no.
- Exact prototype cleanup authorized by the work order: yes.
- Earlier OAP order/report edited: NO.
- Activated order or `oap/active` edited by coding agent: NO; both strategic
  artifacts were committed byte-for-byte.
- Extra PR created for the same numeric objective: NO.
- PR merged by coding agent: NO.
- Auto-merge enabled by coding agent: NO.
- Force push performed: NO.
- Report-publication commit changes only this report file: yes.

## Known limitations / blockers

- There is no implementation blocker for the human-confirmed fresh-install
  product baseline.
- Raw database-volume reuse across glibc/musl families remains unsupported.
  Any future requirement needs a separate logical-migration architecture,
  implementation, and qualification; this round provides none.
- The repository remains pre-alpha. Passing CI and scanner evidence is
  time-bounded engineering evidence, not legal certification, publication
  authority, production readiness, or a durable release notice/source-offer
  bundle.

## Recommended strategic follow-up

Independently verify the immutable SELF commit, its first parent and sole path,
the final report-head check suite, PR diff, and zero-alert state. The strategic
model then decides acceptance and merge; the coding agent has not merged or
enabled auto-merge.
