# OAP Coding-Agent Report — 008-c

## Work order

- Identifier: `008-c`
- Work-order file:
  `oap/orders/008-c-fail-closed-on-collation-incompatible-volume.md`
- Numeric objective: `008`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

The exact incompatible Trixie-created volume was successfully refused by a
local read-only collation-preflight prototype before provisioning, migration,
COW deployment, privilege reconciliation, or readiness-marker mutation. The
CLI emitted only `Database bootstrap failed.`, the fixture kept modeled
application/NGINX readiness blocked, and test-only evidence classified the
failure as `actual-version-unavailable`.

The same local attempt proved that catalog locale facts, control data, marker,
roles, role attributes, privileges, rows, constraints, index validity, and
query digests were unchanged by the refusal. Restarting the exact Trixie image
on the same volume restored actual collation version `2.41` and revalidated all
of that state.

However, the fresh-Alpine sub-check then failed with the constant bootstrap
error. The fixture did not capture a structured fresh-state reason before its
exact cleanup. Read-only image inspection showed the exact Alpine image uses
`LANG=en_US.utf8`; the likely cause is that its fresh unversioned locale state
does not satisfy the prototype's narrow C/POSIX-name whitelist, but that cause
was not directly proven. Both permitted targeted attempts had been consumed,
so no third attempt, relaxation, image change, or repair was performed.

Because the required fresh-Alpine success was not established, the prototype
and its documentation were not committed or pushed. Only the immutable
strategic work order and `oap/active` were committed unchanged, and PR `#11`
was updated to record the partial outcome. The remote product implementation
therefore remains at the 008-b behavior and its mandatory Compose transition
check remains failed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: `11`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/11>
- PR state at report time: `OPEN`
- Draft at report time: `false`
- Merge state at report time: `UNSTABLE`
- Base branch: `main`
- Head branch: `oap/008-supply-chain-build-gates`
- Starting remote SHA: `691ebf1f0aeef122ee1eaf9aca0f111fc9125ccf`
- Implementation head SHA: `e888e00eaf33b8cea6edb8e8dd2b661721f5b899`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal SHA verified after
  push)
- Implementation commits pushed before the report commit: none; the failing
  product prototype was not pushed
- Orchestration-only commit pushed before the report commit:
  `e888e00eaf33b8cea6edb8e8dd2b661721f5b899` —
  `Record OAP 008-c partial execution order`
- Report commit first parent: same as Implementation head SHA
- Created a new PR this turn: no
- Amended existing PR this turn: yes
- Force push performed: no
- Merge performed: NO
- Auto-merge enabled: NO

The PR title remained exactly
`[OAP 008] Add reproducible supply-chain and SBOM gates`. The PR body was
amended to state the local guard/recovery result, fresh-Alpine blocker,
two-attempt cap, absence of a pushed prototype, and absence of repair or merge.

## Changes made

### Delivered remotely

- Committed the strategic model's exact `008-c` work order without editing its
  content.
- Advanced the strategic model's exact `oap/active` content from `008-b` to
  `008-c`.
- Updated PR `#11`'s body with the truthful partial execution finding.
- Did not alter any product, workflow, dependency, image, migration, scanner,
  exception, notice, or prior OAP report on the remote branch.

### Local prototype not delivered

A bounded local prototype was implemented and tested in the following allowed
paths, but deliberately left uncommitted because the fresh-Alpine acceptance
test failed:

- `services/backend/src/slaif_agent_site/db/collation.py`
- `services/backend/src/slaif_agent_site/bootstrap/service.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/unit/test_process_entrypoints.py`
- `tests/packaging/postgres-base-transition.sh`
- `tests/packaging/test_postgres_base_transition.py`
- `docs/DEPLOYMENT.md`
- `docs/OPERATIONS.md`

The prototype contained:

- PostgreSQL 14, 15–16, and 17–18 catalog-query branches that avoid referring
  to unavailable columns/functions;
- one validated provisioner connection and one read-only transaction;
- stable non-secret rejection categories;
- exact-version-match and bounded unversioned C/POSIX evaluation;
- preflight invocation before `provision(settings)` in explicit Compose
  bootstrap;
- unit coverage for match, unavailable actual version, mismatch, C/POSIX,
  malformed state, unknown provider, database mismatch, version-specific query
  selection, read-only transaction use, ordering, and constant CLI behavior;
- a transition fixture that proves refusal/no-mutation, exact old-image
  recovery, dependent-readiness blocking, and fresh-Alpine behavior;
- locally drafted operator documentation matching that prototype.

No part of this local prototype is claimed as remotely delivered behavior.

## Files changed remotely before report publication

- `oap/active`
- `oap/orders/008-c-fail-closed-on-collation-incompatible-volume.md`

The orchestration commit contains 242 insertions and 1 deletion across exactly
those two paths. Its first parent is
`691ebf1f0aeef122ee1eaf9aca0f111fc9125ccf`.

## Governance integrity

The governing files were reread before execution and remained byte-identical
at report drafting:

- `AGENTS.md` SHA-256:
  `9b5995dd14574f853b34c08c0378c901d6b197a3073556c779c6588bd4ac4e4e38`
- `OAP-COMMUNICATION-coding-agent.md` SHA-256:
  `e6150d6efb5a64e7f8af29b00514776972d4f98a0632281ddc260110c6374604`
- `ARCHITECTURE.md` SHA-256:
  `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- `SECURITY.md` SHA-256:
  `ec327af34d13406b560f75834d8bbda685f81dad17fd400cce0c5b6b8df4e23c`
- Activated work-order SHA-256:
  `682db2ca01c181fb808cd553a57e35a1a17282e11566ceefdcc44792a1810dc3`

No narrower `AGENTS.md` or `AGENTS.override.md` exists.

## Acceptance-criteria evidence

### Criterion 1 — unique PR and safe amendment

- Result: PASS
- Evidence: PR `#11` remained the only objective-008 PR, open and non-draft,
  with the required title/base/head. No new PR, merge, auto-merge, force push,
  exception, or prior-artifact edit occurred.

### Criterion 2 — read-only preflight before mutation

- Result: PARTIAL
- Evidence: the local prototype used the validated provisioner connection,
  opened `transaction(readonly=True)`, and invoked the preflight before
  `provision(settings)`. Unit testing proved a rejection yielded call order
  `preflight` only, with the mocked provisioning mutation never called.
- Limitation: this implementation was not pushed because criterion 5 failed.

### Criterion 3 — refuse the exact incompatible volume without mutation

- Result: PARTIAL
- Evidence: targeted attempt 2 produced:
  `bootstrap-refusal exit=nonzero cli-output=constant-safe`,
  `dependent-readiness application=blocked nginx=blocked`, and
  `collation-preflight-test-evidence: reason=actual-version-unavailable`.
- Evidence: Alpine reported
  `encoding=UTF8|provider=c|locale=|collate=en_US.utf8|ctype=en_US.utf8|stored=2.41|actual=`
  and PostgreSQL emitted the expected warning that the database had no actual
  collation version although a version was recorded.
- Evidence: all no-mutation comparisons passed for locale catalog, control,
  marker, role names, role-state digest, privilege digest, structure, data
  digest, and order digest.
- Limitation: this fixture behavior exists only in the unpushed prototype.

### Criterion 4 — exact Trixie recovery

- Result: PARTIAL
- Evidence: attempt 2 restarted the exact old digest against the unchanged
  volume and recovered
  `stored=2.41|actual=2.41`.
- Evidence: `validate: OK revision=006_001 state=EMPTY_SAFE safe=true` and
  `local-login-validate: OK principals=10 authenticated=10` both passed.
- Evidence: every recovery comparison passed: locale, locale catalog, control,
  marker, roles, role state, privileges, structure, data, and index/query order.
- Limitation: this proof was local and the passing fixture was not pushed.

### Criterion 5 — fresh Alpine and PostgreSQL 14–18 remain supported

- Result: FAILED
- Evidence: pure/unit catalog selection covered PostgreSQL 14, 15, 16, 17,
  and 18 query shapes, and a real local integration test accepted an
  unversioned `C` database state.
- Evidence: the existing remote PostgreSQL 14–18 foundation/bootstrap jobs all
  passed, but they ran the unchanged remote 008-b implementation.
- Failure: after exact Trixie recovery passed, the attempt-2 fresh Alpine
  container reached database health and `python -m slaif_agent_site.bootstrap
  compose` emitted `Database bootstrap failed.` instead of the required
  safe-empty success.
- Limitation: exact structured fresh-state reason and catalog facts were not
  captured before exact cleanup. A third run was forbidden by the attempt cap.

### Criterion 6 — no repair, migration, refresh, reindex, or deletion

- Result: PASS
- Evidence: no migration procedure, dump/restore, `pg_upgrade`, collation
  refresh, reindex, image rollback automation, exception, or operator-volume
  deletion was implemented or run. Only exact disposable test resources were
  removed.

### Criterion 7 — all 20 GitHub checks successful

- Result: FAILED
- Evidence: 19 of 20 checks succeeded on remote head
  `e888e00eaf33b8cea6edb8e8dd2b661721f5b899`.
- Evidence: `Compose and edge packaging` failed after its clean Compose smoke
  passed because the unchanged remote 008-b transition fixture reproduced the
  stored `2.41` versus unavailable actual-version mismatch.
- Evidence: open CodeQL alerts were zero for both the repository and the
  objective branch.

### Criterion 8 — budget and attempt ledger

- Result: PASS
- Evidence: exactly two targeted attempts ran; no third attempt ran. Zero
  local complete supply-chain, image/SBOM/Grype, full Python matrix, full
  PostgreSQL matrix, or full Compose smoke runs occurred.
- Evidence: zero product implementation commits/check generations were pushed;
  one orchestration-only check generation ran.
- Evidence: the order appeared at `2026-08-17T21:21:10Z`; remote CI evidence
  was terminal before `2026-08-17T21:45:46Z`, within the 45-minute target.

### Criterion 9 — OAP correlation and report protocol

- Result: PASS
- Evidence: `oap/active` is exactly `008-c`; the work order correlates to the
  same numeric objective, branch, and PR as 008-a/008-b; the earlier reports
  remain immutable. This report is published as a final report-only SELF
  commit whose first parent is the literal implementation head.

## Targeted attempt ledger

### Attempt 1 of 2

- Prefix: `slaif008transitionc1`
- Start: `2026-08-17T21:34:31Z`
- End: `2026-08-17T21:34:54Z`
- Duration: 23 seconds
- Exit: 1
- Stage reached: `record-before`, before stopping Trixie or starting Alpine
- Result: test-harness failure
- Root cause: the new privilege-state digest concatenated PostgreSQL internal
  `"char"` fields (`pg_class.relkind` and `pg_default_acl.defaclobjtype`)
  without explicit text casts, producing an ambiguous `text || "char"`
  operator error.
- Change afterward: added `::text` to those two test-only fields.
- Safety: old exact image initialized and bootstrapped only the disposable
  volume; cleanup passed for containers, network, both exact volumes, and fake
  credentials. Alpine was never started.

### Attempt 2 of 2

- Prefix: `slaif008transitionc2`
- Start: `2026-08-17T21:35:39Z`
- End: `2026-08-17T21:36:31Z`
- Duration: 52 seconds
- Exit: 1
- Stage reached: fresh-Alpine bootstrap after successful refusal and recovery
- Result: core refusal/recovery passed; required fresh-Alpine check failed
- Root cause proven for incompatible volume:
  `actual-version-unavailable` with stored version `2.41`.
- Root cause of fresh failure: not directly captured; likely an overly narrow
  treatment of the exact Alpine image's unversioned `en_US.utf8`/musl state,
  inferred from the code path and image environment, not claimed as proof.
- Change afterward: none. The attempt cap was reached, so the prototype was not
  relaxed, committed, pushed, or rerun.
- Safety: cleanup passed for all exact containers, network, transition/fresh
  volumes, and fake credentials.

### Attempt 2 exact preservation evidence

- Database system identifier: `7675117487980412973`
- Marker before/refused/recovery:
  `alembic=006_001|migration=006_001|state=EMPTY_SAFE|safe=true`
- Role-state SHA-256 before/refused/recovery:
  `5078e3a6f30308ba04a3064d0e46d047093b2def95db29b96b7365d763dae89a`
- Privilege SHA-256 before/refused/recovery:
  `773ebbc872ffdac0e7c771b6c821ddb0dff5309c377115c19019a345f4d02f33`
- Data SHA-256 before/refused/recovery:
  `d5b893a42f029627ba209424653097ff1c4d993aea20992ea6bd8d3da5483b78`
- Ordered-index query SHA-256 before/refused/recovery:
  `c6c53b0c442f1229d9dabd62be65f0fb9eff98ab40818b5a903dc98deb042cfd`
- Structure before/refused/recovery:
  `parent_rows=5|child_rows=6|constraints=3|order_index=true`
- All 20 expected fixed role/login names were identical.
- All control facts were identical: control version `1800`, catalog version
  `202506291`, maximum alignment `8`, database/WAL blocks `8192`, WAL segment
  `16777216`, float8 by value, and checksums version `1`.

## Local verification

- `sh -n tests/packaging/postgres-base-transition.sh`: PASSED.
- `uv run --frozen pytest -q services/backend/tests/unit/test_process_entrypoints.py tests/packaging/test_postgres_base_transition.py`:
  first run FAILED — 50 passed, 1 failed, 18 subtests passed; the only failure
  was a static expectation of 10 literal Compose dependency conditions where
  YAML anchors leave 6 literal conditions.
- Same focused command after correcting only that expectation: PASSED —
  51 passed, 18 subtests passed.
- `PGHOST=127.0.0.1 PGPORT=5432 PGDATABASE=qualification PGUSER=postgres
  PGPASSWORD=qualification-admin uv run --frozen pytest -q
  services/backend/tests/integration/test_database_bootstrap.py::test_collation_preflight_accepts_c_locale_across_supported_postgres`:
  PASSED — 1 passed. The password was a fixed fake local qualification value.
- Final combined focused unit/integration/packaging command: PASSED — 52 passed,
  18 subtests passed.
- `uv run --frozen ruff check` on the five affected Python paths: PASSED.
- `uv run --frozen ruff format --check` on the same paths: PASSED — 5 files
  already formatted.
- `uv run --frozen mypy` on the new collation source, bootstrap service, and
  unit test: PASSED — no issues in 3 source files.
- An earlier direct mypy invocation that also named the integration test was
  NOT VALID as a repository result: it could not resolve the existing
  top-level `conftest` import when invoked in that nonstandard form. The
  supported focused source/unit invocation above passed.
- `python tools/check_repository.py`: PASSED — `PASS repository policy`.
- `uv run --frozen pytest -q tests/repository tests/packaging`: PASSED —
  68 passed, 57 subtests passed.
- `npx --yes markdownlint-cli2@0.22.0 ':docs/DEPLOYMENT.md'
  ':docs/OPERATIONS.md' --config .markdownlint-cli2.yaml --no-globs`:
  PASSED — 2 files, 0 errors.
- `pnpm exec markdownlint-cli2 ...`: NOT RUN successfully — the command was not
  present in the frozen workspace; no lockfile or package manifest was changed.
- `git diff --check`: PASSED.
- Targeted attempt 1: FAILED as recorded above; cleanup PASSED.
- Targeted attempt 2: FAILED at fresh Alpine as recorded above; incompatible
  refusal/no-mutation and exact Trixie recovery subcontracts PASSED; cleanup
  PASSED.
- Local `tools/supply_chain/run.sh`: NOT RUN — explicitly forbidden.
- Local two-build image reproducibility gate: NOT RUN — explicitly forbidden.
- Local six-image SBOM/Grype gate: NOT RUN — explicitly forbidden.
- Local full Python matrix: NOT RUN — explicitly forbidden.
- Local full PostgreSQL matrix: NOT RUN — explicitly forbidden.
- Local full Compose smoke: NOT RUN — explicitly forbidden.
- Third targeted transition/fresh attempt: NOT RUN — attempt cap reached.

No skipped, pending, missing, blocked, or not-run item above is represented as
passing evidence.

## GitHub CI / required checks

- Ordinary CI run: `32072247231`
- CodeQL run: `32072246835`
- Check state observed for implementation head:
  `e888e00eaf33b8cea6edb8e8dd2b661721f5b899`
- Analyze (actions): SUCCESS — 43s
- Analyze (javascript-typescript): SUCCESS — 51s
- Analyze (python): SUCCESS — 49s
- CodeQL aggregate: SUCCESS — 2s
- Dependency review: SUCCESS — 7s
- Detect supported languages: SUCCESS — 5s
- Foundation PostgreSQL 14: SUCCESS — 47s
- Foundation PostgreSQL 15: SUCCESS — 48s
- Foundation PostgreSQL 16: SUCCESS — 54s
- Foundation PostgreSQL 17: SUCCESS — 55s
- Foundation PostgreSQL 18: SUCCESS — 54s
- Markdown: SUCCESS — 7s
- Mermaid: SUCCESS — 42s
- Node contracts: SUCCESS — 1m18s
- Python 3.12 quality and package: SUCCESS — 26s
- Python 3.13 quality and package: SUCCESS — 26s
- Python 3.14 quality and package: SUCCESS — 29s
- Repository policy: SUCCESS — 7s
- Supply-chain evidence: SUCCESS — 4m56s
- Compose and edge packaging: FAILURE — 2m18s
- All required checks green for the implementation head at report drafting:
  no (19 success, 1 failure)
- Open repository CodeQL alerts: 0
- Open objective-branch CodeQL alerts: 0
- Report-only commit may trigger fresh checks: strategic model must verify the
  SELF commit without rewriting this report.

The Compose log proved `compose-smoke: OK` before the unchanged 008-b
transition fixture failed. That fixture again recorded stored collation version
`2.41`, unavailable actual version under Alpine, identical marker/roles/control/
data/index facts, Alpine restart, and exact cleanup. This is the expected remote
state because the failing 008-c prototype was not pushed.

The successful supply-chain artifact was:

- Artifact ID: `9302276865`
- Name:
  `supply-chain-evidence-6bf760c6c47a9f0b2c554104ac27cb1d30831be0`
- Size: 1,661,983 bytes
- Created: `2026-08-17T21:44:34Z`
- Expires: `2026-08-31T21:44:32Z`
- Expired at report time: `false`

## Local setup / dependencies

- Used the existing local PostgreSQL qualification service on
  `127.0.0.1:5432`; no durable database configuration was changed.
- Used passwordless `sudo` only for the bounded Docker backend build and two
  exact disposable transition attempts.
- `sudo docker compose build secrets-init` rebuilt only
  `slaif-agent-site-backend:local` from current local source for fixture use.
  No reproducibility or release image build was run.
- `npx --yes markdownlint-cli2@0.22.0` populated only the ordinary local npm
  execution cache; no repository dependency or lockfile changed.
- No package, production dependency, system service, or durable host
  configuration was installed or changed.

## Documentation

`docs/DEPLOYMENT.md` and `docs/OPERATIONS.md` were drafted locally to document
the intended refusal/recovery boundary, fresh-Alpine support, no-delete rule,
absence of migration, and durable OS/runtime notice/source-offer requirement.
Those drafts were not pushed because the behavior they described did not pass
the fresh-Alpine qualification. The remote documentation therefore remains
truthful for the delivered 008-b implementation.

The PR body, which is GitHub metadata rather than a product documentation file,
was updated to state the partial 008-c result and unpushed status.

## Safety and scope confirmations

- Unrelated files changed: no. All local prototype paths were explicitly
  allowed by the work order; only OAP order/active paths were committed.
- Local uncommitted prototype remains in the disposable checkout: yes, clearly
  listed above and not represented as delivered.
- Production secrets accessed: no.
- Production systems accessed: no.
- Real external services used for fixture data: no.
- Fake credentials used: yes.
- Credentials, DSNs, passwords, or private artifact URLs printed: no.
- Agent capability placed in URL, storage, screenshot, trace, or log: no.
- Required tests skipped/not run: yes — only the work-order-forbidden full local
  gates and the cap-forbidden third attempt, all explicitly recorded.
- Scope deviation: no.
- Dockerfile, Compose topology/image, lockfile, migration, role/grant model,
  supply-chain policy/scanner/evidence code, exception, vulnerability threshold,
  notice inventory, and product service changed remotely: no.
- Migration, dump/restore, refresh, reindex, repair, rollback automation, or
  data deletion performed: no.
- Broad Docker prune performed: no.
- Exact disposable cleanup passed after both attempts: yes.
- Extra PR created for same numeric objective: NO.
- PR merged by coding agent: NO.
- Auto-merge enabled by coding agent: NO.
- Activated order and `oap/active` edited by coding agent: NO.
- Earlier OAP order/report edited: NO.
- Report-publication commit changes only this report file: yes.

## Known limitations / blockers

1. The required fresh Alpine bootstrap did not pass the local prototype, so no
   safe implementation was delivered.
2. The fresh failure's structured reason/catalog tuple was not captured before
   cleanup. The CLI correctly remained constant; a future test-only probe must
   capture that non-secret evidence before cleanup.
3. Read-only inspection of the exact Alpine image shows `LANG=en_US.utf8`.
   Whether its fresh, fully unversioned musl-backed state is an acceptable
   deterministic C/POSIX-class state requires explicit strategic treatment and
   renewed qualification. The coding agent did not broaden acceptance based on
   inference alone.
4. The targeted-attempt cap is exhausted for 008-c. A new activated work order
   is required for another run.
5. Remote CI remains 19/20 because the mandatory transition gate still tests
   the immutable 008-b incompatibility behavior.

## Recommended strategic follow-up

If another amendment is authorized, first require test-only capture of the
fresh Alpine catalog tuple and stable rejection reason before Compose bootstrap.
Then explicitly decide whether the exact Alpine/musl `en_US.utf8` unversioned
state qualifies as the permitted deterministic C/POSIX class or whether a
different already-in-scope initialization policy is required. Grant a new,
small targeted-attempt budget for that decision and the unchanged exact
transition/recovery proof. Do not accept a general unversioned non-C locale,
weaken the stored/actual mismatch guard, or introduce repair/migration as an
incidental workaround.
