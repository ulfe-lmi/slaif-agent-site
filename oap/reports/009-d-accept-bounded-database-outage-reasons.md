# OAP Coding-Agent Report — 009-d

## Work order

- Identifier: `009-d`
- Work-order file:
  `oap/orders/009-d-accept-bounded-database-outage-reasons.md`
- Numeric objective: `009`
- PR mode: `AMEND_EXISTING_PR`
- PR result: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

PR `#14` now accepts the two documented bounded database-outage reasons only
for the stopped-PostgreSQL fixture stage. A pure strict predicate accepts an
exact single reason or an explicit frozen set. The stopped-database call site
passes exactly `frozenset({"connection_unavailable", "timeout"})`; every other
negative call site continues to pass its one exact string reason.

Focused tests prove that both permitted reasons match only a 503
`not_ready` response with an `unavailable` database component. They reject
`probe_error`, `shutdown`, an unknown reason, null reason, a missing database
component, a malformed document, and a 200 response. They also prove that a
single `connection_unavailable` expectation does not accept `timeout`.

The sole authorized sudo fixture passed baseline, wrong-login, wrong-role,
unreadable-secret, unsafe-marker, migration-mismatch, stopped-postgres, and
recovery. It verified stopped-database liveness 200, NGINX unready, PostgreSQL
restart/health, restored Control/NGINX readiness, and printed the exact success
summary. Exact cleanup left no project container, volume, or network.

The single implementation commit was pushed to the existing PR. All 20
GitHub checks passed, including the independent complete Compose fixture and
supply-chain evidence. Repository/PR and branch open CodeQL alert counts are
zero. No workflow rerun, second fixture, manual Docker reproduction, second
implementation generation, extra PR, merge, close, or auto-merge occurred.

No Control product code, timeout, reason vocabulary, credentials, roles,
migrations, pool behavior, production authority, Compose configuration,
documentation, dependency, workflow, or adjacent authentication behavior
changed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: `14`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/14>
- PR state at report time: `OPEN`
- Draft at report time: `false`
- Mergeable at report time: `MERGEABLE`
- Merge state at report time: `CLEAN`
- Required title:
  `[OAP 009] Wire Control API database readiness boundary`
- Base branch: `main`
- Remote base SHA at activation and report time:
  `ab3db28f573b62130b93ae082a196e8ca9f8b424`
- Head branch: `oap/009-control-database-readiness`
- Starting remote/report head:
  `aa3a6837165f6d306a893576d5b57ea4ac05e8b5`
- Previous 009-c implementation head:
  `ae7f283037c86799f0971400b83f6afcf249c976`
- 009-d implementation head:
  `a9b11ff768c9019c60e73bbb4d16172517a05c3b`
- Report publication commit: SELF
- Remote PR head after report publication: SELF
- Implementation commit pushed before this report:
  `a9b11ff768c9019c60e73bbb4d16172517a05c3b` —
  `Accept bounded Control outage reasons`
- Implementation commit first parent:
  `aa3a6837165f6d306a893576d5b57ea4ac05e8b5`
- 009-d implementation diff: 4 files, 350 insertions, 26 deletions
- Cumulative PR implementation at report time: 38 files, 5,467 insertions,
  142 deletions
- New PR created this round: no
- Existing PR amended this round: yes
- Force push performed: no
- Merge performed: NO
- PR closed: NO
- Auto-merge enabled: NO

GitHub search returned exactly one objective-009 PR: open PR `#14` with the
required base, branch, and title. Its verified REST body records the exact
predicate, local complete fixture, 20/20 green checks, zero alerts, exhausted
caps, and absence of product changes.

## Changes made

### Exact bounded outage predicate

`tools/compose/control_readiness.py` now defines:

```text
DATABASE_OUTAGE_REASONS = frozenset({"connection_unavailable", "timeout"})
```

The pure `readiness_matches` predicate accepts three deliberately bounded
expectation forms:

- `None` requires status 200, document status `ready`, and the exact database
  component `{component: database, status: ok, reason: null}`;
- a string requires status 503, document status `not_ready`, database status
  `unavailable`, and exact equality to that one reason; and
- a frozen set requires the same strict 503/document/component state and a
  reason contained in that explicit set.

Non-dictionary documents, non-list component collections, and a missing
database component return no match. The waiting loop retains its bounded
deadline and allowlisted `timeout` fixture failure.

Only the stopped-PostgreSQL call site changed from the single
`CONNECTION_UNAVAILABLE` string to `DATABASE_OUTAGE_REASONS`. Wrong-login,
wrong-role, unreadable-secret, unsafe-marker, and migration-mismatch retain
their existing exact single-reason calls. Ready checks remain exact.

### Focused strictness tests

`tests/packaging/test_compose_policy.py` now proves:

- the outage set is exactly `connection_unavailable` plus `timeout`;
- each of those reasons matches the strict 503/not-ready/unavailable shape;
- `probe_error`, `shutdown`, `unknown`, and null do not match;
- a 200 response does not match even if its body carries `timeout`;
- an absent database component does not match;
- a malformed non-document does not match; and
- a single `connection_unavailable` expectation does not accept `timeout`.

All prior allowlisted secret-free diagnostics, target-only recreation, helper
capability confinement, and Compose topology tests remain green.

## Files changed before report publication

- `oap/active`
- `oap/orders/009-d-accept-bounded-database-outage-reasons.md` (new)
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
- 009-c order SHA-256:
  `f16a19ca6bdd553591d85bd71fbf06ca93e31d69cca1254392b89322223d1024`
- 009-c report SHA-256:
  `57dcb0b00ea56f4b790740c11412e639956dd7a961c1a8efe41db7870a66b73d`
- Activated 009-d order SHA-256:
  `882b53a3f8af992a3e487993374792da0e6d4ef869bf909a50a540c515465674`

No narrower applicable `AGENTS.md` or `AGENTS.override.md` exists.

## Targeted sudo fixture attempt ledger

### Attempt 1 — sole and final permitted run

- Start: `2026-08-18T00:02:58Z`
- End: `2026-08-18T00:05:13Z`
- Duration: 134.955 seconds
- Exit: 0
- Exact command:
  `sudo python tools/compose/control_readiness.py slaif009dfix`
- Disposable project: `slaif009dfix`
- Printed stages, in order: baseline, wrong-login, wrong-role,
  unreadable-secret, unsafe-marker, migration-mismatch, stopped-postgres,
  recovery.
- Exact success summary:
  `control-readiness-fixture: OK mount=isolated identity=exact failures=6
  recovery=clean`
- Secret, child command/output, locator, driver exception, or container
  environment exposed: no.
- Exact sudo cleanup audit: PASS — containers `NONE`, volumes `NONE`, and
  networks `NONE` for prefix `slaif009dfix`.

Targeted sudo fixture attempts: exactly 1 of 1 allowed. No second fixture,
manual mutation, or equivalent Docker reproduction ran.

## Stage and negative-state evidence

- Baseline: PASS — direct Control readiness, liveness, NGINX readiness, and
  exact isolated-mount assertions completed.
- Wrong login: PASS — bounded `configuration_invalid` readiness, Control
  liveness 200, NGINX unready, exact credential restoration, and return to
  ready completed.
- Wrong role: PASS — bounded `role_mismatch` readiness, Control liveness 200,
  NGINX unready, exact role restoration, and return to ready completed.
- Unreadable secret: PASS — bounded `configuration_invalid` readiness,
  Control liveness 200, NGINX unready, mode restoration/recreation, and return
  to ready completed.
- Unsafe marker: PASS — bounded `unsafe_marker` readiness, Control liveness
  200, NGINX unready, bootstrap restoration, and return to ready completed.
- Migration mismatch: PASS — bounded `migration_mismatch` readiness, Control
  liveness 200, NGINX unready, migration restoration, and return to ready
  completed.
- Stopped PostgreSQL: PASS — a strict bounded outage reason matched while
  Control readiness remained 503, Control liveness remained 200, and NGINX
  reported the dependency unready.
- Recovery: PASS — PostgreSQL restarted and became healthy; Control returned
  to exact ready/liveness state and NGINX returned ready.
- Cleanup: PASS — exact project resources were absent after exit.

## Acceptance-criteria evidence

### Criterion 1 — unique existing PR amended once

- Result: PASS
- Evidence: PR `#14` remains the sole objective-009 PR with the required open,
  non-draft/base/head/title state. Exactly one 009-d implementation commit and
  one automatic check generation were pushed. No force push, extra PR, merge,
  close, auto-merge, or prior-artifact edit occurred.

### Criterion 2 — outage-only exact reason set

- Result: PASS
- Evidence: only stopped-postgres passes the exact two-reason frozen set.
  Every other negative stage passes its existing single reason. Product and
  Compose behavior are unchanged.

### Criterion 3 — strict predicate rejection tests

- Result: PASS
- Evidence: focused tests passed both documented outage reasons and rejected
  third/unknown/null reasons, missing component, malformed document, status
  200, and a timeout against the single connection-unavailable expectation.

### Criterion 4 — one complete targeted run and cleanup

- Result: PASS
- Evidence: exactly one run printed all eight stages, completed stopped-
  database liveness/NGINX assertions and recovery, emitted the exact success
  summary, and left no exact-prefix Docker resources.

### Criterion 5 — all prior negative and confinement evidence

- Result: PASS
- Evidence: every prior credential, role, secret, marker, migration,
  confinement, and diagnostic test remained green locally and in GitHub's
  independent complete Compose job.

### Criterion 6 — 20 green checks and zero alerts

- Result: PASS
- Evidence: all 20 implementation-head checks succeeded. Repository/PR and
  objective-branch open CodeQL alert counts were both zero.

### Criterion 7 — OAP correlation and publication

- Result: PASS through report publication.
- Evidence: `oap/active` is exactly `009-d\n`; all four rounds correlate to
  PR `#14` and the same branch; prior artifacts are unchanged; this report is
  a final report-only SELF commit whose first parent is the literal 009-d
  implementation head.

## Local verification

- `uv run --frozen pytest -q tests/packaging/test_compose_policy.py`: PASSED —
  12 passed and 8 subtests passed in 0.06 seconds.
- `uv run --frozen ruff check tools/compose/control_readiness.py
  tests/packaging/test_compose_policy.py`: PASSED.
- `uv run --frozen ruff format --check tools/compose/control_readiness.py
  tests/packaging/test_compose_policy.py`: PASSED — 2 files already formatted.
- `uv run --frozen mypy`: PASSED — no issues in 66 source files.
- `uv run --frozen python -m py_compile
  tools/compose/control_readiness.py`: PASSED.
- `python tools/check_repository.py`: PASSED — `PASS repository policy`.
- `docker compose config --quiet`: PASSED.
- `python tools/compose/verify.py --root .`: PASSED — `compose-policy: OK`.
- `git diff --check`: PASSED before the implementation commit.
- Active-pointer, activated-order hash, exact allowed-path, prior-artifact,
  unchanged-Compose, staged-scope, remote-head, and commit-parent checks:
  PASSED.
- Sole targeted fixture: PASSED with all eight stages and exact summary.
- Exact sudo cleanup audit: PASSED — no exact-prefix resource remained.
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

- Ordinary CI run: `32083157131` — SUCCESS
- CodeQL run: `32083157129` — SUCCESS
- Check state observed for implementation head:
  `a9b11ff768c9019c60e73bbb4d16172517a05c3b`
- Analyze (actions): SUCCESS — 39s
- Analyze (javascript-typescript): SUCCESS — 53s
- Analyze (python): SUCCESS — 43s
- CodeQL aggregate: SUCCESS — 2s
- Compose and edge packaging: SUCCESS — 3m12s
- Dependency review: SUCCESS — 7s
- Detect supported languages: SUCCESS — 3s
- Foundation PostgreSQL 14: SUCCESS — 51s
- Foundation PostgreSQL 15: SUCCESS — 56s
- Foundation PostgreSQL 16: SUCCESS — 55s
- Foundation PostgreSQL 17: SUCCESS — 47s
- Foundation PostgreSQL 18: SUCCESS — 55s
- Markdown: SUCCESS — 8s
- Mermaid: SUCCESS — 59s
- Node contracts: SUCCESS — 1m12s
- Python 3.12 quality and package: SUCCESS — 33s
- Python 3.13 quality and package: SUCCESS — 33s
- Python 3.14 quality and package: SUCCESS — 34s
- Repository policy: SUCCESS — 7s
- Supply-chain evidence: SUCCESS — 4m54s
- Totals: 20 successful, 0 failed, 0 cancelled, 0 skipped, 0 pending
- All required checks green: YES
- Open repository/PR CodeQL alerts: 0
- Open objective-branch CodeQL alerts: 0
- Workflow reruns requested: 0
- The report-only SELF commit may trigger fresh checks. Those future results
  are not claimed here; the strategic model must independently verify them.

GitHub's independent Compose log records every stage and the exact summary:

```text
control-readiness-stage: baseline
control-readiness-stage: wrong-login
control-readiness-stage: wrong-role
control-readiness-stage: unreadable-secret
control-readiness-stage: unsafe-marker
control-readiness-stage: migration-mismatch
control-readiness-stage: stopped-postgres
control-readiness-stage: recovery
control-readiness-fixture: OK mount=isolated identity=exact failures=6 recovery=clean
```

No command, child output, locator, password, username, container environment,
or driver exception accompanies that output.

The successful implementation-head supply-chain artifact is:

- Artifact ID: `9305861237`
- Name:
  `supply-chain-evidence-0841e6fe385fb2cb87ab30a97fdce8afb644194c`
- Size: 1,674,344 bytes
- Created: `2026-08-18T00:10:42Z`
- Expires: `2026-09-01T00:10:41Z`
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

No documentation change was needed. Existing durable documentation already
defines both `connection_unavailable` and `timeout` as bounded fail-closed
database reasons and requires stopped PostgreSQL to leave Control/NGINX
unready. No product or operational contract changed.

## Safety and scope confirmations

- Unrelated files changed: no.
- Changes outside the activated paths: no.
- 009-a through 009-c orders/reports edited: NO; all hashes are recorded above.
- Earlier OAP artifact edited: NO.
- Activated order or `oap/active` authored/modified by coding agent: NO; both
  strategic artifacts were committed byte-for-byte.
- Production secrets, systems, credentials, or data accessed: no.
- Real DSN/password/token/cookie/private artifact URL printed or committed:
  no.
- Diagnostic child command/stdout/stderr printed: no.
- Product source, timeout, reason vocabulary, identity/role validation, pool,
  migration, health contract, Compose topology, secret generator/mount, or
  production capability changed: no.
- Earlier single-reason negative contract broadened: no.
- `probe_error`, `shutdown`, missing database, malformed response, HTTP 200,
  or unknown reason accepted as an outage: no.
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

- None within the activated 009-d scope.
- `COMPLETE` means the requested remote state and evidence exist; it does not
  mean strategic acceptance or authorize the coding agent to merge.

## Recommended strategic follow-up

Independently verify this SELF report commit, its first parent, the complete
fixture evidence, all 20 implementation-head checks, zero alerts, exact caps,
single-PR correlation, and unchanged prior artifacts. The strategic model
alone decides whether objective 009 is accepted and whether PR `#14` may be
merged.
