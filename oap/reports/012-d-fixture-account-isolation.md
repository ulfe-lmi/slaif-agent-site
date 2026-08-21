# OAP Coding-Agent Report — 012-d

## Work order and status

- Identifier: `012-d`; work-order file:
  `oap/orders/012-d-fixture-account-isolation.md`
- PR mode: `AMENDED_EXISTING_PR`
- Status: COMPLETE

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`; PR
  [#24](https://github.com/ulfe-lmi/slaif-agent-site/pull/24); `OPEN`,
  ready/non-draft, `CLEAN`, mergeable, zero reviews
- Base/head: `main` / `oap/012-membership-rbac`
- Starting remote SHA: `b87626cb732279605400b011c5a51e085b7ac0b4`
- Implementation head SHA: `be48ec748163dc1ee02e740c593b2c401291574c`
- Report publication commit: SELF
- Implementation commit pushed:
  `be48ec748163dc1ee02e740c593b2c401291574c`; report
  parent=implementation SHA
- New PR: NO; workflow rerun: NO; corrective generation: NONE;
  merge/close/auto-merge: NO

## Exact repair

- The pre-insert transaction now rejects `EXISTS (SELECT 1 FROM
  control.user_account)`, so any pre-existing account fails the disposable
  fixture setup. It retains the uninitialized-installation, no-administrator,
  no-membership, fixed-value insert, transaction, and no-overwrite checks.
- The post-E2E owner query now requires exactly three total accounts. Exactly
  two must be the fixed ACTIVE OIDC identities with their expected IDs, issuer,
  subjects, and display names; null local username, normalized username,
  password hash, and email; and no administrator assignment.
- Exactly one account must be ACTIVE LOCAL with non-null local username,
  normalized username, and password hash, null OIDC issuer/subject, and the
  sole Platform Administrator assignment. The two disjoint classifications
  total three rows, excluding every additional identity/account row.
- The query emits only one boolean consumed by `grep`; it prints no ID,
  username, hash, token, or credential.
- Static packaging coverage requires the unrestricted any-user precondition,
  rejects regression to a fixed-ID-only precondition, and requires the exact
  total, OIDC/LOCAL, null/non-null password, and sole-administrator assertions.

## Files changed

- `tools/compose/smoke.sh`
- `tests/packaging/test_compose_smoke_contract.py`
- Strategic-owned bytes committed unchanged: `oap/active` and
  `oap/orders/012-d-fixture-account-isolation.md`

No product, backend, schema, migration, API, Web, Playwright, Compose topology,
documentation, dependency, lockfile, image, or prior OAP artifact changed.

## Required local verification

1. `sh -n tools/compose/smoke.sh`: PASSED.
2. `uv run --frozen ruff check
   tests/packaging/test_compose_smoke_contract.py`: PASSED.
3. `uv run --frozen ruff format --check
   tests/packaging/test_compose_smoke_contract.py`: PASSED — one file already
   formatted.
4. `python -m unittest tests.packaging.test_compose_smoke_contract`: PASSED —
   four tests in 0.153 seconds.
5. `git diff --check`: PASSED; staged diff check also PASSED.

The first combined local gate identified only an overlong new static-test line;
after wrapping it, Ruff format requested the assertion's canonical one-line
shape. Both were corrected before commit, and the five mandated checks then
passed together. Per the order, local Compose, Playwright, Node, PostgreSQL,
images, Mermaid, and SBOM were not run.

## GitHub CI

- Implementation workflow run `32453945519` and CodeQL run `32453945526`:
  all 20 checks terminal `SUCCESS`; zero failed, pending, cancelled, skipped,
  or missing.
- SUCCESS: Repository policy; Node contracts; Python 3.12, 3.13, and 3.14
  quality and package; Foundation PostgreSQL 14, 15, 16, 17, and 18; Compose
  and edge packaging; Supply-chain evidence; Markdown; Mermaid; Dependency
  review; Detect supported languages; Analyze actions; Analyze python; Analyze
  javascript-typescript; CodeQL.
- Real Compose job `96687515173` passed the strengthened SQL plus every retained
  membership, restart, secret, recovery, browser, and cleanup assertion.
- One read-only status poll encountered a transient GitHub API disconnect; the
  next 30-second poll succeeded. No workflow was rerun.
- The report-only commit may trigger fresh checks; strategy verifies SELF.

## Safety, setup, and scope

- Dependencies or setup installed: none. Lockfiles changed: no.
- Unrelated work discarded: no. Prior orders/reports changed: no.
- Activated order/pointer edited by coding agent: no; strategic bytes were only
  committed.
- Production systems, data, or credentials accessed: no. Secrets printed or
  committed: no.
- Required tests skipped: no. Explicitly prohibited local suites were not run.
- Extra PR: NO. Workflow rerun: NO. Merge/close/auto-merge: NO.
- Report commit changes only this report: yes.

## Immutable hashes

- `AGENTS.md`:
  `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`:
  `00bdd82fcec0afaf65d2fbc2a2f9fa43a7d4e9e254d7a262bea0c5bae3be6b8a`
- `ARCHITECTURE-for-agents.md`:
  `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Activated work order:
  `eebe6178d82adf2e75c1fe9fb052335bac2f7a16eaef8cf37635fa3203753ca7`
- Activated pointer:
  `7b2f7407154205d8cdfac95d9226b449007edda6ac2b581437f3982f2a608e66`

## Limitations and strategic follow-up

No blocker remains for 012-d. Independently verify the report-only head and
20/20 implementation evidence. Only strategy may accept or merge PR #24,
activate another order, or declare the roadmap complete.
