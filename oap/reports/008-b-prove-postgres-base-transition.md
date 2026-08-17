# OAP Coding-Agent Report — 008-b

## Work order

- Identifier: 008-b
- Work-order file: `oap/orders/008-b-prove-postgres-base-transition.md`
- Numeric objective: 008
- PR mode: AMENDED_EXISTING_PR
- Report drafted: 2026-08-17T21:07:08Z

## Status

PARTIAL

## Executive summary

Amended the existing objective-008 PR with one mandatory, exact, disposable
test of the persistent PostgreSQL volume transition from the previously
accepted Debian/Trixie image to the Alpine image proposed in 008-a.

The test establishes a mixed result. PostgreSQL 18.6 Alpine starts read/write
on the unchanged PostgreSQL 18.6 Trixie-created volume without initialization,
upgrade, repair, collation refresh, reindex, or dump/restore. It also restarts
on that same volume. The migration and bootstrap markers, all fixed product
roles and logins, current privilege validation, representative Unicode/
numeric/timestamp/JSONB rows, primary and foreign keys, the ordered-text index,
control-data compatibility fields, and deterministic data and order-query
digests all survive exactly.

The transition is nevertheless not compatible under the work order's
fail-closed locale contract. Trixie initialized database `slaif` with libc
provider `c`, `en_US.utf8` collation and ctype, and stored/actual collation
version `2.41`. Alpine preserves the stored `2.41` value but cannot report an
actual version. It emits this warning on connections before and after restart:

```text
database "slaif" has no actual collation version, but a version was recorded
```

The normalized locale fact changed from
`stored=2.41|actual=2.41` to `stored=2.41|actual=`. The ordered query happened
to produce the same digest in this fixture, but that does not override missing
collation compatibility metadata or the server warning. Per the work order,
no third attempt, image redesign, exception, database repair, automatic
migration, or broader remediation was performed. Strategic/human choice is
required, and the status is therefore `PARTIAL`.

The old/current image pair is immutable in machine policy and the old image is
explicitly historical evidence, not a current build input. CI runs the test as
a mandatory non-optional step after the unchanged clean Compose smoke. Durable
documentation states that the exact in-place transition is blocked and that
image publication separately requires durable OS/runtime license, notice, and
source-offer review rather than relying on a 14-day CI artifact.

Two targeted local attempts and exactly two implementation commits/check
generations were used. The first attempt exposed one pre-transition locale-
query cast defect and was corrected. The second completed the transition and
proved the genuine incompatibility. The first GitHub generation reproduced
the incompatibility but also exposed runner-sensitive temporary-credential
cleanup; the single permitted corrective commit made cleanup exact and
runner-safe. The final generation reproduced the same incompatibility with
successful cleanup. Nineteen of 20 checks passed, including the complete
supply-chain evidence job; only the mandatory Compose/transition check failed.
Open branch and repository CodeQL alert counts are zero.

This report is the final repository mutation for the round. Checks on the
report-containing `SELF` head cannot be embedded in this immutable report and
will be observed without rewriting it before the FIFO response.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: 11
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/11>
- PR state at report time: OPEN
- PR readiness at report time: non-draft
- PR merge state at report time: UNSTABLE, due solely to the mandatory failed
  transition check
- Required and actual PR title:
  `[OAP 008] Add reproducible supply-chain and SBOM gates`
- Base branch: `main`
- Head branch: `oap/008-supply-chain-build-gates`
- Starting remote PR head / 008-a report SHA:
  `f83c13243694b990231936bfec77dd0b7569c554`
- Previous 008-a implementation head:
  `9c732921e6c04eb21bf385cdd5964055bd8ed3eb`
- Implementation head SHA:
  `c141ce8f6d73ebb290f6054429e138223bd103fa`
- Implementation commits pushed before the report commit:
  - `dba2dd8bb9361716f0fd7713e7ebc1149b5b26c3` —
    `Prove PostgreSQL base transition incompatibility`
  - `c141ce8f6d73ebb290f6054429e138223bd103fa` —
    `Make transition cleanup runner-safe`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal SHA derived from
  GitHub)
- Report commit first parent: same as Implementation head SHA
- Existing objective PR amended: yes
- New PR created this round: no
- Other objective-008 PRs found: none
- Other open PRs: Dependabot PR #12 and PR #13; neither is objective 008 and
  neither was modified
- Force push performed: NO
- Merge performed: NO
- Auto-merge enabled: NO
- PR #5 or PR #7 modified: NO

The PR body was amended to state the exact transition failure and merge
blocker. It does not claim that the transition or all CI checks pass.

## Exact transition identity and method

The tested source was:

```text
docker.io/library/postgres:18.6-trixie@sha256:06cad38a5d9f5d24b4d83d86def30795d5e4b757fedbf5281172b576dedcd941
```

The tested target was:

```text
docker.io/library/postgres:18.6-alpine3.23@sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f
```

Both exact readable-tag-plus-top-level-digest references were pulled and
verified before each targeted run. The machine policy records them under the
single exact key `postgres-18.6-trixie-to-alpine3.23`, requires purpose
`persistent-volume-compatibility`, requires the target to equal the current
`oci_sources.postgres`, and rejects the historical source as a current build
input. Mutation tests reject changes to source, target, or purpose.

The shell fixture accepts only a bounded lowercase-alphanumeric prefix that
starts with `slaif008transition`. It fails on a collision instead of deleting
an existing resource, then creates only one exact network, one exact named
data volume, exact prefixed containers, and one system temporary credential
directory. The ordinary Compose volumes are never inspected or mounted.

The accepted backend image generated 23 fake credential/DSN files without
printing their values. The old official PostgreSQL entrypoint initialized the
new named volume using its actual default locale behavior. The fixture then
ran the current `python -m slaif_agent_site.bootstrap compose` one-shot and
proved:

```text
compose-bootstrap: OK revision=006_001 state=EMPTY_SAFE safe=true
validate: OK revision=006_001 state=EMPTY_SAFE safe=true
local-login-validate: OK principals=10 authenticated=10
```

The test-only `transition_test` schema is outside the protected empty `content`
schema. It contains five parent rows and six child rows with Unicode text,
default-collated ordered text, exact numeric values, timestamp-with-time-zone
values, JSONB values, primary keys, a foreign key, and a two-column ordered-text
index. The test obtains data and order-query SHA-256 values without hashing or
printing credentials.

The old server was stopped cleanly with exit code zero and its container was
removed while the exact data volume remained. Alpine then received the same
volume and the same fake credential directory. The command does not invoke an
initializer, `pg_upgrade`, dump/restore, reindex, collation refresh, or any
repair. It records all after-state facts, reruns bootstrap `validate`, reruns
the current local-login violation and authentication validation without
mutation, stops Alpine cleanly, starts it again unchanged, and repeats the
essential facts. Targeted log patterns fail on locale/collation/version/index/
data-directory incompatibility or panic.

Cleanup always targets the exact names. The final CI log confirms removal of
all exact containers, network, volume, and credential directory after the
intentional compatibility failure.

## Transition results

### PostgreSQL and control data

- Old executable: `postgres (PostgreSQL) 18.6 (Debian 18.6-1.pgdg13+2)`.
- New executable: `postgres (PostgreSQL) 18.6`.
- Both servers reached healthy read/write state.
- The Alpine server stopped cleanly and reached healthy read/write state on a
  second start.
- Old/new/restart static control facts matched:
  - `pg_control version number=1800`
  - `Catalog version number=202506291`
  - `Maximum data alignment=8`
  - `Database block size=8192`
  - `WAL block size=8192`
  - `Bytes per WAL segment=16777216`
  - `Float8 argument passing=by value`
  - `Data page checksum version=1`
- The database system identifier remained identical within each attempt. It
  was `7675106430308253741` in local attempt 2 and
  `7675109326883684397` in the final independent CI fixture.

### Locale and collation

Before transition:

```text
encoding=UTF8|provider=c|locale=|collate=en_US.utf8|ctype=en_US.utf8|stored=2.41|actual=2.41
```

After transition and after Alpine restart:

```text
encoding=UTF8|provider=c|locale=|collate=en_US.utf8|ctype=en_US.utf8|stored=2.41|actual=
```

Result: FAILED. PostgreSQL warned that `slaif` has no actual collation version
although a version was recorded. The warning appeared on the first Alpine
start and the second Alpine start, locally and in both GitHub generations. No
warning was suppressed or accepted.

### Marker, roles, privileges, and authentication

The following marker remained identical before, after, and after restart:

```text
alembic=006_001|migration=006_001|state=EMPTY_SAFE|safe=true
```

The exact role/login inventory remained:

```text
slaif_agent_login,slaif_agent_runtime,slaif_bootstrap_login,slaif_control,
slaif_control_login,slaif_editor_login,slaif_editor_runtime,slaif_gc,
slaif_gc_login,slaif_media,slaif_media_login,slaif_owner,
slaif_preview_login,slaif_preview_reader,slaif_public_login,
slaif_public_reader,slaif_reviewer,slaif_reviewer_login,slaif_scheduler,
slaif_scheduler_login
```

Current non-mutating product privilege validation returned safe after
transition. `local_login_violations` remained empty, and all ten fixed fake
credentials authenticated as their exact principals before and after.

### Representative data, constraints, and indexes

The normalized structure fact was identical before, after, and after restart:

```text
parent_rows=5|child_rows=6|constraints=3|order_index=true
```

The deterministic values were identical before, after, and after restart:

- representative data SHA-256:
  `d5b893a42f029627ba209424653097ff1c4d993aea20992ea6bd8d3da5483b78`
- indexed order-query SHA-256:
  `c6c53b0c442f1229d9dabd62be65f0fb9eff98ab40818b5a903dc98deb042cfd`

These equal digests prove this fixture's data and query result did not drift.
They do not prove collation safety in the face of the missing actual version
and repeated server warning.

## Attempt ledger

### Attempt 1

- Prefix: `slaif008transitiona1`
- Start: `2026-08-17T20:51:44Z`
- End: `2026-08-17T20:52:09Z`
- Duration: 25 seconds
- Result: FAIL (test-harness defect, before image transition)
- Exact stage reached: old/new exact pulls verified; 23 fake credential files
  generated; old Trixie server healthy; `006_001`/`EMPTY_SAFE` bootstrap
  complete; five parent/six child representative rows created; non-mutating
  bootstrap validation passed; all ten local logins validated/authenticated.
- Root cause: the locale query attempted to concatenate PostgreSQL catalog
  type `"char"` (`datlocprovider`) without an explicit text cast, so PostgreSQL
  reported `operator is not unique: unknown || "char"`.
- Change afterward: added the unambiguous `datlocprovider::text` cast only.
- Cleanup: PASSED and independently verified absent container, network, volume,
  and temporary credential directory.
- Local full image/SBOM/Grype runner executed: NO.

### Attempt 2

- Prefix: `slaif008transitiona2`
- Start: `2026-08-17T20:52:44Z`
- End: `2026-08-17T20:53:21Z`
- Duration: 37 seconds
- Result: FAIL (genuine transition incompatibility)
- Exact stage reached: complete test, including clean old stop, first Alpine
  start, all after-state validations/comparisons, clean Alpine stop, second
  Alpine start, repeated essential comparisons, log inspection, and cleanup.
- Root cause: stored glibc collation version `2.41` had no actual version on
  Alpine, and PostgreSQL repeatedly emitted the exact warning quoted above.
- Preserved evidence: control fields, marker, 20 exact roles/logins, privilege
  validation, ten authentications, row counts, constraints, index validity,
  data digest, and order digest all matched.
- Change afterward: documentation recorded the incompatibility and publication
  boundary; no transition test logic, image, database, exception, or repair
  changed.
- Cleanup: PASSED and independently verified absent container, network, volume,
  and temporary credential directory.
- Local full image/SBOM/Grype runner executed: NO.

### Attempt 3

- Not run.
- Reason: attempt 2 established the genuine incompatibility. The work order
  requires `PARTIAL` and prohibits remediation after that result.
- Local full image/SBOM/Grype runner executed: NO.

## GitHub generation ledger

### Generation 1

- Implementation head:
  `dba2dd8bb9361716f0fd7713e7ebc1149b5b26c3`
- CI workflow run: `32068501970`
- CodeQL workflow run: `32068502294`
- Created: `2026-08-17T20:56:49Z`
- Result: CI FAILURE; CodeQL SUCCESS.
- Compose job: `95506057628`, FAILED after 2 minutes 18 seconds.
- Exact transition result: reproduced local attempt 2. Clean Compose smoke
  passed first; locale comparison and Alpine logs failed; all data/security
  comparisons passed; Alpine restarted.
- Additional CI defect: the initial cleanup implementation reported aggregate
  cleanup failure on the non-root hosted runner after the intended transition
  failure. Its per-resource commands were suppressed in this first generation,
  so the exact subcommand was not overclaimed. The runner-sensitive ownership
  restoration was removed in favor of deleting exact mounted contents and
  using passwordless `sudo rmdir` only for the validated temporary directory;
  cleanup diagnostics were made explicit.
- Corrective implementation commit afterward: yes, the single permitted
  cleanup-only commit.
- Other ordinary jobs: 14 of 14 SUCCESS, including Supply-chain evidence.
- CodeQL checks: all three language analyses and aggregate SUCCESS.
- Evidence artifact:
  `supply-chain-evidence-bc1602ad173f8fb33f545f9012cfc54b524f99e6`,
  artifact ID `9300951034`, 1,661,848 bytes, expires
  `2026-08-31T21:01:22Z`.

### Generation 2 (final implementation head)

- Implementation head:
  `c141ce8f6d73ebb290f6054429e138223bd103fa`
- CI workflow run: `32068950119`
- CodeQL workflow run: `32068950193`
- Created: `2026-08-17T21:01:50Z`
- Result: CI FAILURE; CodeQL SUCCESS.
- Compose job: `95507475307`, FAILED after 2 minutes 29 seconds.
- Exact transition result: clean Compose smoke passed; both exact images and
  bootstrap passed; locale fact and warning reproduced; control, marker,
  roles, structure, data, order, and restart comparisons passed.
- Cleanup result: PASSED exactly — containers, network, volume, and credential
  directory removed.
- Corrective implementation commit afterward: NO; the sole remaining failure
  is the work-order-defined incompatibility and must not be repaired here.
- Other ordinary jobs: 14 of 14 SUCCESS, including Supply-chain evidence.
- CodeQL checks: all three language analyses and aggregate SUCCESS.
- Evidence artifact:
  `supply-chain-evidence-14b48939746ec108d6d96588407237ea42dd0a3f`,
  artifact ID `9301107475`, 1,662,039 bytes, created
  `2026-08-17T21:06:16Z`, expires `2026-08-31T21:06:16Z`.

No third check generation was created.

## Changes made and files changed

The two implementation commits changed 11 paths, with 958 insertions and one
deletion relative to the 008-a report head:

- Mandatory CI integration: `.github/workflows/ci.yml`.
- Exact transition policy: `supply-chain/policy.json` and
  `tools/supply_chain/policy.py`.
- Bounded integration/static tests:
  `tests/packaging/postgres-base-transition.sh`,
  `tests/packaging/test_postgres_base_transition.py`, and
  `tests/supply_chain/test_policy.py`.
- Exact limitation and release-evidence documentation:
  `docs/DEPLOYMENT.md`, `docs/OPERATIONS.md`, and
  `docs/SUPPLY_CHAIN.md`.
- Strategic transcript, committed exactly as activated: `oap/active` and
  `oap/orders/008-b-prove-postgres-base-transition.md`.
- This SELF publication adds only
  `oap/reports/008-b-prove-postgres-base-transition.md`.

No Compose file, Dockerfile, lock, exception file, scanner/evidence runner,
notice, service, application source, migration, bootstrap behavior, role,
network, volume, port, secret topology, action pin, prior order, or prior report
changed.

## Acceptance-criteria evidence

### Criterion 1

- Result: PASSED.
- Evidence: PR #11 remains the unique objective-008 PR and uses the required
  open, non-draft, base/head/title identity. No new PR, merge, auto-merge,
  force push, exception, or prior-report edit occurred.

### Criterion 2

- Result: PASSED for the bounded data/start condition.
- Evidence: the exact old-image-initialized volume started read/write on the
  exact new image without initialization, repair, upgrade, dump/restore,
  reindex, collation refresh, or data loss. Alpine also restarted on the
  unchanged volume.

### Criterion 3

- Result: FAILED.
- Evidence: the stored locale remained libc `c`/`en_US.utf8` with version
  `2.41`, while Alpine returned no actual collation version and repeatedly
  emitted the exact warning. This is the decisive reason for `PARTIAL`.

### Criterion 4

- Result: PASSED for observed state preservation.
- Evidence: `006_001`, `EMPTY_SAFE safe=true`, all exact roles/logins,
  privilege validation, ten authentications, five/six rows, three validated
  key constraints, valid/ready order index, both deterministic digests, and
  static control fields survived transition and restart.

### Criterion 5

- Result: PASSED on the final implementation head.
- Evidence: the test is a mandatory non-optional Compose-job step, accepts only
  a validated unique prefix, fails on collision, uses fake secrets, prints no
  secret/DSN values, never targets an ordinary project volume, and the final
  CI log proves exact cleanup even after intentional failure.

### Criterion 6

- Result: PARTIAL.
- Evidence: old/current references and their relationship are immutable in
  policy; all focused local tests and 19 final GitHub checks passed; both open
  CodeQL alert counts are zero. The twentieth check cannot be green because its
  new mandatory transition assertion correctly rejects the incompatible
  collation state. No weakening was applied.

### Criterion 7

- Result: PASSED.
- Evidence: documentation states only the exact observed transition boundary,
  forbids in-place use of Alpine with a Trixie-created operator volume, avoids
  proposing an unapproved repair, and makes durable OS license/notice/source-
  offer review a prerequisite before image publication.

### Criterion 8

- Result: PASSED.
- Evidence: executor duration stayed below 60 minutes; two of three targeted
  attempts, two of two implementation commits/check generations, and zero of
  zero authorized local full supply-chain runs were used. No third attempt or
  generation occurred.

### Criterion 9

- Result: PASSED subject to final remote publication verification.
- Evidence: `oap/active` contains exactly `008-b`; both rounds correlate with
  objective 008; 008-a artifacts are unchanged. This report-only SELF commit
  records literal implementation parent
  `c141ce8f6d73ebb290f6054429e138223bd103fa`; its exact remote one-file delta
  will be verified before FIFO `OK`.

## Focused local verification

### Static transition and policy tests

```text
sh -n tests/packaging/postgres-base-transition.sh
uv run --frozen python -m compileall -q \
  tools/supply_chain/policy.py \
  tests/supply_chain/test_policy.py \
  tests/packaging/test_postgres_base_transition.py
uv run --frozen python -m unittest \
  tests.packaging.test_postgres_base_transition \
  tests.supply_chain.test_policy
uv run --frozen python -m tools.supply_chain.policy validate
```

Results: shell syntax passed; compile passed; 17 focused packaging/policy tests
passed; machine policy validation passed. The final full standard-library
supply-chain unit discovery ran 30 tests and passed.

Static tests prove exact old/current references in script/policy/Compose, the
historical-not-current boundary, drift rejection, mandatory CI invocation,
prefix/cleanup contract, and absence of broad prune, upgrade, dump/restore,
initializer-argument, reindex, or collation-refresh commands.

### Affected packaging and repository checks

```text
uv run --frozen python -m unittest discover \
  -s tests/packaging -p 'test_*.py'
uv run --frozen python -m unittest discover \
  -s tests/repository -p 'test_*.py'
uv run --frozen python tools/check_repository.py
```

Results: 21 packaging tests passed; 45 repository tests passed; repository
policy passed. The cleanup-only correction reran all 21 packaging tests and
repository policy successfully.

### Ruff, formatting, Markdown, and whitespace

```text
uv run --frozen ruff check \
  tools/supply_chain/policy.py \
  tests/supply_chain/test_policy.py \
  tests/packaging/test_postgres_base_transition.py
uv run --frozen ruff format --check \
  tools/supply_chain/policy.py \
  tests/supply_chain/test_policy.py \
  tests/packaging/test_postgres_base_transition.py
npx --yes markdownlint-cli2@0.23.2 \
  docs/DEPLOYMENT.md docs/OPERATIONS.md docs/SUPPLY_CHAIN.md
git diff --check
```

Results: Ruff passed; all three changed Python files were formatted; Markdown
completed without findings; diff whitespace passed.

### Targeted integration

```text
sudo -E sh tests/packaging/postgres-base-transition.sh \
  slaif008transitiona1
sudo -E sh tests/packaging/postgres-base-transition.sh \
  slaif008transitiona2
```

Results: both nonzero as recorded in the complete attempt ledger. Attempt 1
was the corrected pre-transition query defect. Attempt 2 was the authoritative
local incompatibility result and completed exact cleanup. Independent checks
confirmed both attempt prefixes left no container, network, data volume, or
credential directory.

## Deliberately not run locally

The hard work-order budget explicitly prohibited these local commands/gates,
and none was run:

- `tools/supply_chain/run.sh`
- two-build five-image reproducibility suite
- six-image SBOM/Grype suite
- full Python 3.12–3.14 local matrix
- full PostgreSQL 14–18 local matrix
- full clean/restart/failure Compose smoke

This restraint is not represented as passing local evidence. The unchanged
gates ran in GitHub generation 2: every one passed except the mandatory
transition assertion inside Compose/packaging. No required scanner, SBOM, or
regression job was skipped by GitHub.

## Final implementation-head GitHub checks

1. Analyze (actions) — SUCCESS
2. Analyze (javascript-typescript) — SUCCESS
3. Analyze (python) — SUCCESS
4. CodeQL — SUCCESS
5. Compose and edge packaging — FAILURE, exact required collation blocker;
   cleanup SUCCESS
6. Dependency review — SUCCESS
7. Detect supported languages — SUCCESS
8. Foundation PostgreSQL 14 — SUCCESS
9. Foundation PostgreSQL 15 — SUCCESS
10. Foundation PostgreSQL 16 — SUCCESS
11. Foundation PostgreSQL 17 — SUCCESS
12. Foundation PostgreSQL 18 — SUCCESS
13. Markdown — SUCCESS
14. Mermaid — SUCCESS
15. Node contracts — SUCCESS
16. Python 3.12 quality and package — SUCCESS
17. Python 3.13 quality and package — SUCCESS
18. Python 3.14 quality and package — SUCCESS
19. Repository policy — SUCCESS
20. Supply-chain evidence — SUCCESS

Branch open code-scanning alerts: zero. Repository open code-scanning alerts:
zero. No pending, cancelled, skipped, or failed check is represented as
passing. The failed Compose conclusion is retained deliberately and is the
merge blocker.

## Setup and dependencies

- No OS, Python, npm, product, runtime, or repository dependency was installed
  or added.
- No lockfile changed.
- Existing local uv, Docker, Python, Node/npm tooling, and the accepted backend
  image were used.
- Passwordless `sudo` was used only for exact disposable Docker fixtures and
  the exact temporary credential-directory removal contract.
- Both PostgreSQL images were pulled by exact public top-level digest.
- No hosted service, account, credential, cloud API key, subscription, or
  production resource was used.

## Documentation impact

Deployment and operations documentation now state that the current Alpine
image is qualified only for a fresh Alpine-initialized local volume, not as an
in-place replacement for the exact historical Trixie volume. They record the
exact preserved facts, exact locale failure, and prohibition on automatic
repair or volume discard. Supply-chain documentation records the historical
policy boundary and requires durable OS/runtime license text, notice, and
source-offer review before image publication. It does not claim release,
legal, or production readiness.

## Safety and scope confirmations

- Allowed path scope respected: YES.
- `compose.yaml` or Dockerfile changed: NO.
- Product/application behavior changed: NO.
- Database migration/bootstrap/role semantics changed: NO.
- Normal operator volume inspected or mutated: NO.
- New image, dependency, lock, exception, scanner, or notice added: NO.
- License or vulnerability exception added: NO.
- Action pin, matrix, or existing gate weakened: NO.
- Local full supply/SBOM/Grype runner executed: NO.
- Local full Python/PostgreSQL matrix or Compose smoke executed: NO.
- Targeted transition attempts: 2 of maximum 3.
- Implementation commits/check generations: 2 of maximum 2.
- Fake secret values, DSNs, passwords, or tokens printed: NO.
- Production system, data, credentials, or unrelated Docker resource accessed:
  NO.
- Broad Docker prune or unrelated resource deletion: NO.
- Activated order or pointer edited by the coding agent: NO; exact strategic
  bytes were committed.
- 008-a order/report or other prior artifact edited: NO.
- Extra branch or PR created: NO.
- Force push, merge, auto-merge, release, signing, tag, deployment, or setting
  change performed: NO.
- Report publication commit changes only this report: YES, to be verified
  locally and remotely before FIFO response.
- Report first parent is the literal implementation head: YES, to be verified
  locally and remotely before FIFO response.

## Limitations and blocker

The exact Trixie-to-Alpine in-place persistent-volume transition is blocked.
The physical data files remain readable in the tested environment and all
sample/state evidence survives, but Alpine lacks an actual collation version
for the stored glibc `en_US.utf8` version. PostgreSQL warns on every tested
connection and after restart. Under the work order, this is not a safe
transition.

No conclusion is offered about which strategic remedy should be selected.
Potential image-family rollback, deliberate data migration, or explicit human
acceptance would each require authority and scope beyond 008-b. No automatic
repair, collation refresh, reindex, upgrade, dump/restore, exception, image
change, or data deletion was attempted.

The existing 008-a supply-chain evidence still reports zero Critical and 35
High findings for the current six-image set, but it does not resolve persistent
volume compatibility. Its OS/runtime inventory is a 14-day CI artifact, not a
durable release notice/source-offer package. Both limitations remain visible
for strategic/human decision.

## Strategic follow-up

- Independently review PR #11, both implementation commits, the two local
  attempts, both GitHub generations, final Compose log, exact warning,
  preserved state/digests, successful cleanup, final supply artifact, zero
  CodeQL alerts, and report-only head/parent.
- Choose whether to retain/revert the Alpine image, authorize a separately
  designed data migration, or make another explicit human decision. The coding
  agent does not recommend or implement that strategic choice in this order.
- Decide acceptance and merge separately. The coding agent did not merge,
  enable auto-merge, publish, release, sign, deploy, or choose another work
  order.
