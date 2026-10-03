# OAP Coding-Agent Report — 079-2-c

## Work order

- Identifier: 079-2-c (increment-qualified round ID: third round of
  semantic increment 2 of numeric Objective 079, increment 079/2)
- Work-order file: `oap/orders/079-2-c-alpine-pin-repair.md`
- Work-order sha256: `1e994d8baf8e81dda40f3af26fe6fc131c2bc520e29678210b01aeb232745609`
- `oap/active` bytes: `079-2-c\n` (hex `3037392d322d630a`)
- Numeric objective: 079 (increment 079/2; this round = corrected
  closed-scope Alpine pin repair completing the 2026-10-03 strategy scope
  decision)
- PR mode: AMENDED_EXISTING_PR (PR #93)

## Status
BLOCKED

## Executive summary
The corrected closed 17-line / six-file pin repair was executed exactly as
authorized: the pre-edit unscoped inventory matched the closed Section 2
list exactly; all 17 lines (24 occurrences) were replaced `3.5.8-r0` ->
`3.5.9-r0`; the post-edit inventory is empty; repository policy PASSED; the
targeted packaging + supply-chain unit tests PASSED (23 passed, 34
subtests); P2 resolution evidence is the two recorded 079-2-b probes (both
Alpine base images, both rc=0); all four affected images were freshly built
(the old-pin local images were deleted first) and the full Compose smoke
(13 projects) ran to rc=0 with every required key line. Implementation head
I was pushed. At I, CI shows 18/20 SUCCESS and — decisively — the original
Alpine apk failure class is GONE: both failing jobs built every Alpine
image successfully. The two required build checks then failed on TWO NEW,
DISTINCT failure classes, each outside this order's closed scope:
(A) `Compose and edge packaging` fails building the explicitly out-of-scope
`infra/apache/Dockerfile` edge target because the Ubuntu noble archive no
longer provides the pinned `openssl=3.0.13-0ubuntu3.15` — another external
package rotation of the same class as the Alpine one, previously masked
because the job aborted at the nginx target before ever reaching apache;
(B) `Supply-chain evidence` fails on the backend image with
`normalized application-file drift` — a double-build reproducibility gate
that was unreachable while the backend build failed at the apk step. A
local double-build reproduction at I (exact CI build arguments) is
byte-identical across all 2821 application files, so the CI drift is
intermittent, not deterministic. Per order §5 STOP clause ("or if any other
failure class appears: stop and report BLOCKED with the exact evidence; do
not improvise alternatives") and §11, the executor stops and reports
BLOCKED with the exact evidence. Repairing either failure class requires
scope this order does not grant (apache Dockerfile / ubuntu policy entries /
supply-chain tooling are all explicitly non-goals).

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#93](https://github.com/ulfe-lmi/slaif-agent-site/pull/93), state OPEN (mergeable)
- Base/head branches: `main` <- `oap/079-2-a-gallery-logogrid`
- Base `main`: `577509e7bc990d85a10af5954bee3c6f7c888a4f` (unchanged)
- Round-start remote SHA (079-2-b report-only commit):
  `d5c24bc0d73651558bc3654035932348070512f5`
- Transcript commit T (order + `active` bytes only, 2 files):
  `503b7cb2a5ce9c337c771d85d7fc00811e57a473`
- Implementation head SHA: `7efcece05390728018a86ab00bd0fc983888b2e7`
  (parent T; pushed before this report)
- Report publication commit: SELF (first parent =
  `7efcece05390728018a86ab00bd0fc983888b2e7`)
- Remote PR head after report publication: SELF (literal derived via GitHub
  by strategy)
- New PR this turn: no; merge performed: NO

## Changes made

1. Transcript commit T: strategy-published order and `oap/active` bytes
   committed exactly (blob sha256 verified against the published files).
2. Implementation commit I: exactly the 17 line replacements of P1
   (24 occurrences of the exact string `3.5.8-r0`, one or two per line) —
   file:line per site (pre-edit line numbers):
   - `apps/web/Dockerfile` lines 7, 36 (apk installs, 2 occurrences each)
   - `infra/nginx/Dockerfile` lines 16, 17 (apk installs)
   - `infra/postgres/Dockerfile` lines 20, 22 (apk installs) + 23, 25
     (exact-installed-version assertions, now reading `3.5.9-r0`)
   - `services/backend/Dockerfile` lines 6, 36 (apk installs, 2
     occurrences each)
   - `supply-chain/policy.json` lines 127, 131, 136, 138, 143
     (`alpine_package_overrides.images` install entries for backend, nginx,
     postgres (x2 lines), web)
   - `tests/packaging/test_oci_contract.py` lines 80, 82 (the two pinned
     assertion strings in
     `test_postgres_overlay_is_exact_and_does_not_rebuild_postgres`)
   No product code, no other pin, no other policy section, no other test,
   no base image, no Dockerfile structure was changed.
3. This report (via the SELF report-only commit).

## Files changed

- `git diff --name-only T..I` = exactly the six P1 files;
  `git diff --stat T..I` = 6 files changed, 17 insertions(+), 17 deletions(-)
  (Criterion 1)
- `git diff --name-only d5c24bc..I` = exactly eight files: the six P1
  files + `oap/orders/079-2-c-alpine-pin-repair.md` + `oap/active`
  (Criterion 2)
- `git diff --name-only d5c24bc..S` will list exactly nine files (the eight
  plus this report) — verified before the response signal (Criterion 7)

## Acceptance-criteria evidence
### Criterion 1 (T..I = exactly six files / 17 lines)

- SATISFIED — `git diff --stat 503b7cb..7efcece`:
  `apps/web/Dockerfile | 4 ++--`, `infra/nginx/Dockerfile | 4 ++--`,
  `infra/postgres/Dockerfile | 8 ++++----`, `services/backend/Dockerfile |
  4 ++--`, `supply-chain/policy.json | 10 +++++-----`,
  `tests/packaging/test_oci_contract.py | 4 ++--`; total 17 insertions / 17
  deletions = 17 changed lines.

### Criterion 2 (d5c24bc..I = exactly eight files)

- SATISFIED — name-only diff lists exactly: the six P1 files,
  `oap/orders/079-2-c-alpine-pin-repair.md`, `oap/active` (verified after
  push; worktree clean).

### Criterion 3 (grep outputs, check_repository PASS, targeted pytest)

- SATISFIED — all recorded in Local verification: pre-edit unscoped grep =
  exactly the 17 closed-list lines (rc=0); post-edit grep = zero matches
  (rc=1, empty output); `tools/check_repository.py` = `PASS repository
  policy` (rc=0); targeted pytest = `23 passed, 34 subtests passed`
  (rc=0).

### Criterion 4 (P2 citation of the 079-2-b probes)

- SATISFIED — cited in Local verification: 079-2-b report, Criterion 2 /
  Local verification — probe on `node:24.14.1-alpine3.23@sha256:8510330d...`
  and on `python:3.12.12-alpine3.23@sha256:2d91681153...`, both
  `apk --timeout 30 add --no-cache 'libcrypto3=3.5.9-r0' 'libssl3=3.5.9-r0'`,
  both rc=0 with the apk transaction output recorded in that immutable
  report. No re-run was performed (order: re-run optional).

### Criterion 5 (fresh-build evidence + full smoke key lines)

- SATISFIED — recorded in Local verification: the four old-pin local images
  were deleted before the smoke; the smoke log shows all four images
  (re)built from the new pin (exact apk `3.5.9-r0` transaction lines and
  `naming to ... :local done` lines with log line numbers) and the full
  smoke reached rc=0 with the required key lines
  (`compose-e2e: OK projects=13 ...`, `media-e2e: OK ...`,
  `public-agent-acceptance: OK ...`, `compose-smoke: OK`).

### Criterion 6 (all 20 required checks SUCCESS on the exact report-only head S)

- NOT SATISFIED — at implementation head I (the round head before S), CI
  run `37148750609` + CodeQL run `37148750584`: 18 SUCCESS, 2 FAILURE.
  The original Alpine apk failure class is resolved (every Alpine image
  built in both jobs). Both failures are NEW, distinct, out-of-scope
  classes — see Failure class A and Failure class B. The order's §5 STOP
  clause applies ("or if any other failure class appears: stop and report
  BLOCKED with the exact evidence; do not improvise alternatives");
  repairing them requires scope this order does not grant.

### Criterion 7 (S report-only; parent I; remote head S; nine-file diff)

- PENDING at drafting — S is created and pushed after this section is
  written; verified before the response signal: S changes only this report,
  first parent = I, remote PR head = S, `git diff --name-only d5c24bc..S` =
  exactly nine files.

### Criterion 8 (honest status)

- BLOCKED — Criterion 6 is not evidenced; the exact gap is Failure class A
  and Failure class B.

## Failure class A — `Compose and edge packaging` (apache Ubuntu pin, explicitly out of scope)

- CI run `37148750609`, job `111277991401` (11m11s) at head I:
  - All five compose images built successfully from the new pin (log lines:
    `#46 naming to docker.io/library/slaif-agent-site-nginx:local done`
    1908; `#52 ... postgres:local 0.0s done` 2036; `#58 ...
    backend:local done` 2065; `#72 ... web:local done` 2232; `#76 ...
    browser-worker:local done` 2252) — the Alpine repair is effective in CI.
  - Stack stages proceeded (e.g. log line 2723: `database-login-policy: OK
    public-connect=denied exact-roles=10 ...`).
  - The standalone edge target build then failed: log line 3108:
    `#7 ERROR: process "/bin/sh -c apt-get update && apt-get install
    --no-install-recommends --yes 'apache2=2.4.58-1ubuntu8.15'
    'apache2-bin=2.4.58-1ubuntu8.15' 'apache2-data=2.4.58-1ubuntu8.15'
    'apache2-utils=2.4.58-1ubuntu8.15' 'openssl=3.0.13-0ubuntu3.15' &&
    a2dissite 000-default && a2enmod deflate headers proxy proxy_http
    unique_id && rm -rf /var/lib/apt/lists/* /var/cache/apt/*" did not
    complete successfully: exit code: 100`, with the exact apt error at log
    line 3107: `E: Version '3.0.13-0ubuntu3.15' for 'openssl' was not
    found` (package `openssl` "not available ... missing, obsoleted, or only
    available from another source" in the noble archive).
- The pinned versions are at `infra/apache/Dockerfile` lines 17-21
  (`apache2{,-bin,-data,-utils}=2.4.58-1ubuntu8.15`,
  `openssl=3.0.13-0ubuntu3.15`); the `ubuntu_package_overrides` policy
  entries and the apache OCI-contract test assertions are the paired
  surfaces of the same pin.
- This is the same defect class as the Alpine rotation (externally rotated
  package index vs an exact-version pin), but in the apache (Ubuntu)
  Dockerfile. At every previous head of this branch, this job aborted at
  the nginx target (Alpine apk failure) before ever reaching the apache
  target, so the apache defect was masked; at I it is now exposed.
- Scope: order §2 ("infra/apache/Dockerfile and
  services/browser-worker/Dockerfile contain no libcrypto/libssl pin or apk
  line at all (verified at d5c24bc) and are OUT of scope") and §5 ("MUST NOT
  be touched"; "No change to any other section of supply-chain/policy.json
  (scanner_tools, oci_sources, ubuntu_package_overrides, browser_runtime, or
  any other key)"; "No change to any test other than the two assertion
  lines of tests/packaging/test_oci_contract.py (lines 80 and 82)").

## Failure class B — `Supply-chain evidence` (backend double-build reproducibility drift, intermittent)

- CI run `37148750609`, job `111277991443` (2m23s) at head I:
  - Log line 867: `supply-chain-evidence: ERROR: backend: normalized
    application-file drift` (job exit 1).
  - The gate (`tools/supply_chain/run.sh` + `tools/supply_chain/evidence.py`
    `compare-builds`): builds each image TWICE with `--no-cache` and
    identical build args (backend is FIRST in the sequence, line 371),
    exports each rootfs via `docker export` of a created container, and
    requires the normalized rootfs manifests to be equal. For `backend` the
    application-file boundary is `opt/slaif/` (`IMAGE_PREFIXES`), every file
    is sha256'd, and `normalize_runtime_file` applies NO normalization for
    backend (it only normalizes five Next.js manifests for web). The CI
    error is specifically the file-manifest comparison
    (`first_files != second_files`); the normalized SBOM package signatures
    MATCHED (no `normalized SBOM package drift` error).
  - The run stopped at the first image; the remaining images (including
    apache) were never attempted in this job.
  - Failure-diagnostics artifact
    `supply-chain-failure-diagnostics-adb9235ad5ea98d079cbc1f0e0112216336c3f93`
    (downloaded): `STATUS.json` = `{"qualification": "UNQUALIFIED",
    "status": "INCOMPLETE", "success_manifest": "ABSENT",
    "original_exit_status": 1}` plus `backend.raw.syft.json` /
    `backend.raw.spdx.json` / `normalized-backend.syft.json` (second build
    only) — the first/second rootfs file manifests are NOT included in the
    artifact, so the specific CI-drifted file cannot be named from the
    artifact alone.
- Local reproduction at I (exact CI build arguments, revision = I): two
  `docker build --pull --no-cache` builds of `services/backend/Dockerfile`
  (tags `diag-0792c-backend-{first,second}`), `docker container create` +
  `docker export` of each (mirroring `export_rootfs`),
  `python -m tools.supply_chain.evidence rootfs-manifest --image-name
  backend` on both rootfs tars: 2821 entries each; `only_first: []`;
  `only_second: []`; `differing: 0` — byte-identical application files
  locally. The drift is therefore INTERMITTENT (environment/timing
  dependent on the CI runner), not a deterministic content mismatch at this
  tree. Diagnostic images and tars were deleted after the reproduction
  (build logs + manifests retained in `/tmp/0792c-backend-*`).
- The pin change cannot be the cause of a `/opt/slaif/` file drift: the
  changed layers are the apk layers (packages under `/usr/lib`); the
  compared boundary is `/opt/slaif/` only; the CI SBOM package level
  matched; and the local double build at the bumped pin is
  byte-identical. This gate had been unreachable since the Alpine
  rotation because the backend build failed at the apk step on every
  previous head.
- Scope: any fix would require changes to `services/backend/Dockerfile`
  beyond its two pinned lines and/or to `tools/supply_chain/*`
  normalization/diagnostics — all explicitly forbidden by order §5. This is
  a supply-chain build-reproducibility decision for strategy.

## Local verification
All on the round tree (repo root), 2026-10-03, in the order §8 sequence:

- R1.1 PRE-EDIT `git grep -n '3.5.8-r0' -- . ':!oap'` (round-start tree):
  exactly the 17 lines of the closed Section 2 list —
  `apps/web/Dockerfile:7,36`; `infra/nginx/Dockerfile:16,17`;
  `infra/postgres/Dockerfile:20,22,23,25`; `services/backend/Dockerfile:6,36`;
  `supply-chain/policy.json:127,131,136,138,143`;
  `tests/packaging/test_oci_contract.py:80,82` (rc=0; full line content
  recorded in the transcript of this round; per-file match counts
  2/2/4/2/5/2). No deviation -> proceeded.
- R1.2 Applied exactly the 17 line replacements (24 occurrences of the
  exact string, guarded per file: 2/2/4/2/5/2 lines; 4/2/4/4/8/2
  occurrences).
- R1.3 POST-EDIT identical unscoped grep: ZERO matches, empty output,
  rc=1 (recorded).
- R1.4 `uv run --frozen python tools/check_repository.py`: PASSED
  (`PASS repository policy`, rc=0).
- R1.5 `uv run --frozen pytest tests/packaging/test_oci_contract.py
  tests/supply_chain/test_policy.py -q`: PASSED (`23 passed, 34 subtests
  passed in 0.69s`, rc=0).
- R1.6 P2 citation: see Criterion 4 (079-2-b report, both probes, both rc=0;
  no re-run).
- R2 pre-step: `docker rmi slaif-agent-site-web:local
  slaif-agent-site-nginx:local slaif-agent-site-backend:local
  slaif-agent-site-postgres:local` — all four old-pin local images deleted
  (deleted image IDs: web 8883bf5e9490, nginx bb92d756b549, backend
  735ec019548b, postgres 716b7163a43f); only `browser-worker:local` and
  `apache:test` remained (both outside the pin scope).
- R2 `sh tools/compose/smoke.sh slaif0078c` (full log
  `/tmp/0792c-smoke-1.log`): rc=0. Fresh-build evidence (log line numbers):
  - postgres: line 158 `[postgres 2/2] RUN apk add ... 'libcrypto3=3.5.9-r0'
    'libcurl=8.22.0-r0' 'libssl3=3.5.9-r0' && test ... = "3.5.9-r0" ...`
    with lines 159-160 `Upgrading libcrypto3 (3.5.7-r0 -> 3.5.9-r0)` /
    `Upgrading libssl3 (3.5.7-r0 -> 3.5.9-r0)`; `naming to
    ...slaif-agent-site-postgres:local 0.0s done` line 252 (the exact
    installed-version assertions passed inside the build).
  - nginx: lines 168-170 apk `3.5.9-r0` (`3.5.5-r0 -> 3.5.9-r0`); `naming to
    ...slaif-agent-site-nginx:local 0.0s done` line 285.
  - backend (secrets-init runtime/builder): lines 187-189 and 215-217
    (`3.5.5-r0 -> 3.5.9-r0`); `naming to ...slaif-agent-site-backend:local
    done` line 395.
  - web (runtime + builder): lines 194-196 and 209-211 (`3.5.6-r0 ->
    3.5.9-r0`); `naming to ...slaif-agent-site-web:local done` line 473.
  - Required key lines: line 988 `compose-e2e: OK projects=13 setup=1
    governance=1 preview=1 preview-filtering=1 stable-devices=6
    agent-sessions=2 media-publication=1 artifacts=disabled`; line 991
    `public-agent-acceptance: OK workspace=a2b11174-57eb-4aaf-b594-c9ab586307cd
    ... openapi=exact restart=verified nginx-outage=verified ...
    render-restart=verified`; line 994 `media-e2e: OK edge=nginx
    upload=validated-private-read=byte-identical
    finalization=public-read=byte-identical immutable-cache=verified`; line
    1373 `compose-smoke: OK`; `SMOKE_RC=0`.
- Failure-class-B local reproduction (diagnostic, no repo change): two
  `--no-cache` backend builds at I + `docker export` + `rootfs-manifest`
  (commands in Failure class B) -> 2821/2821 entries, 0 differing.
- `npx --yes markdownlint-cli2@0.23.2 --no-globs <this report's temp
  path>`: 0 issues (before the atomic rename).
- Not run (not in the order's §8 sequence and not named by R1-R4): the full
  Python/Node local gates — the 17-line diff touches no product code, no
  Python/Node source, and no lockfile; the order-named local gates
  (check_repository, targeted pytest) ran and passed, and the GitHub
  Python/Node quality gates are SUCCESS at head I (see table below).

## GitHub CI / required checks
State observed for implementation head
`7efcece05390728018a86ab00bd0fc983888b2e7` (CI run `37148750609`, started
2026-10-03T19:40:42Z, completed 2026-10-03T19:53:41Z, conclusion
failure; CodeQL run `37148750584`, conclusion success; observed
2026-10-03, all checks terminal):

| Required check | State (head 7efcece) |
|---|---|
| Compose and edge packaging | FAILURE (CI 37148750609, job 111277991401, 11m11s — all five compose images built OK; standalone `target apache` apt failure `E: Version '3.0.13-0ubuntu3.15' for 'openssl' was not found` (out-of-scope infra/apache/Dockerfile; Failure class A) |
| Dependency review | SUCCESS (CI 37148750609, job 111277991405, 6s) |
| Foundation PostgreSQL 14 | SUCCESS (CI 37148750609, job 111277991517, 11m47s) |
| Foundation PostgreSQL 15 | SUCCESS (CI 37148750609, job 111277991471, 10m52s) |
| Foundation PostgreSQL 16 | SUCCESS (CI 37148750609, job 111277991448, 12m55s) |
| Foundation PostgreSQL 17 | SUCCESS (CI 37148750609, job 111277991502, 12m49s) |
| Foundation PostgreSQL 18 | SUCCESS (CI 37148750609, job 111277991440, 9m56s) |
| Markdown | SUCCESS (CI 37148750609, job 111277991378, 10s) |
| Mermaid | SUCCESS (CI 37148750609, job 111277991356, 40s) |
| Node contracts | SUCCESS (CI 37148750609, job 111277991201, 1m30s) |
| Python 3.12 quality and package | SUCCESS (CI 37148750609, job 111277991444, 33s) |
| Python 3.13 quality and package | SUCCESS (CI 37148750609, job 111277991394, 49s) |
| Python 3.14 quality and package | SUCCESS (CI 37148750609, job 111277991386, 40s) |
| Repository policy | SUCCESS (CI 37148750609, job 111277991348, 10s) |
| Supply-chain evidence | FAILURE (CI 37148750609, job 111277991443, 2m23s — `backend: normalized application-file drift` at the first image in its sequence; intermittent (local double build byte-identical); artifact adb9235... (Failure class B) |
| Analyze (actions) | SUCCESS (CodeQL 37148750584, job 111278016916, 32s) |
| Analyze (javascript-typescript) | SUCCESS (CodeQL 37148750584, job 111278016915, 51s) |
| Analyze (python) | SUCCESS (CodeQL 37148750584, job 111278016950, 1m48s) |
| CodeQL | SUCCESS (CodeQL 37148750584, 3s) |
| Detect supported languages | SUCCESS (CodeQL 37148750584, job 111277990980, 6s) |

- All required green at drafting: NO — 18 SUCCESS, 2 FAILURE (both NEW
  out-of-scope failure classes; the original Alpine apk failure class is
  resolved at this head — no apk resolution error appears in either job).
- The report-only SELF commit will trigger fresh runs; per protocol §9 the
  report states the terminal table for the literal implementation head I
  and does not predict fresh runs; strategy independently verifies the
  report head.
- No CI re-run was invoked (flake policy: the single allowed unmodified
  re-run is reserved for the documented 079/1 `dragUntil` class; the
  observed failures are not that class).

## Local setup / dependencies

- Docker: `docker rmi` of the four old-pin local images; fresh `docker
  compose build --pull` (inside the smoke) of all four affected images; two
  extra `--no-cache` diagnostic backend builds + `docker export` for the
  failure-class-B reproduction (diagnostic images and rootfs tars deleted
  after use; build logs `/tmp/0792c-backend-build{1,2}.log` and manifests
  `/tmp/0792c-backend-{first,second}.files.json` retained).
- Smoke stack `slaif0078c` (torn down by the smoke script at completion).
- No new packages or services; no sudo setup needed. No production systems,
  data, or credentials touched; no secrets in the diff or this report.

## Documentation

- None this round (order §5 non-goal: no current-truth documentation
  changes; the pin repair is not an increment-level documentable fact).

## Safety and scope confirmations

- Unrelated files changed: NO — on the remote this round changed exactly:
  T (2 transcript files), I (the six P1 files), S (this report).
- Production secrets accessed: NO; production systems accessed: NO.
- Required tests skipped/not run: NO for the order's §8-named sequence
  (every named command ran: pre-edit grep, replacements, post-edit grep,
  check_repository, targeted pytest, fresh builds + full smoke,
  markdownlint); the broader local gates are not named by this order and
  the diff touches no product/Python/Node source — CI quality gates at I
  are SUCCESS and recorded above.
- Scope deviation: NO — exactly the 17 closed-list lines; `infra/apache/
  Dockerfile`, `services/browser-worker/Dockerfile`, all other policy.json
  sections, and all other tests untouched; the §5 STOP clause was honored
  when the two new failure classes appeared (no improvised fix, no
  out-of-scope repair commit).
- Extra objective PR: NO; coding-agent merge: NO; dependabot PRs untouched.
- Activated order/`oap/active` edited: NO — committed byte-identical
  (order blob sha256 `1e994d8baf8e81dda40f3af26fe6fc131c2bc520e29678210b01aeb232745609`
  verified on the committed blob; active `079-2-c\n` = hex
  `3037392d322d630a` verified on the committed blob).
- Report commit changes only this report: yes (verified before the response
  signal).

## Cumulative base->head size (2026-09-14 review-unit governance Section 2)
Base `577509e7bc990d85a10af5954bee3c6f7c888a4f` -> implementation head I
`7efcece05390728018a86ab00bd0fc983888b2e7` (exact measured diff: 42 files,
+3875/-89; the order's §10 predeclared estimate was 43 files / ~+4190/-90 —
the exact table is authoritative per the order):

| Category | Files | +lines | -lines |
|---|---|---|---|
| Production/config | 15 | 549 | 69 |
| Migrations | 0 | 0 | 0 |
| Tests/evidence | 12 | 1285 | 9 |
| Generated artifacts | 5 | 354 | 4 |
| Docs | 4 | 8 | 6 |
| OAP transcript | 6 (3 orders + active + 2 prior reports) | 1679 | 1 |

Production/config = the 079-2-a ten files + the four Dockerfiles +
`supply-chain/policy.json` (15 files / +549 substantive lines — exactly the
order's predeclared 15 files / ~549 lines). The ~20-30 implementation-file /
several-thousand-line review trigger is NOT crossed; CLOSURE_ONLY does not
begin.

## Known limitations / blockers

- BLOCKING (Criterion 6): two new, distinct, out-of-scope failure classes
  at head I — (A) `Compose and edge packaging`: the out-of-scope
  `infra/apache/Dockerfile` edge target cannot build because the Ubuntu
  noble archive no longer provides the pinned `openssl=3.0.13-0ubuntu3.15`
  (`E: Version '3.0.13-0ubuntu3.15' for 'openssl' was not found`; job
  111277991401 log 3108ff; pins at lines 17-21; masked at all previous
  heads by the nginx-target Alpine failure); (B) `Supply-chain evidence`:
  intermittent `backend: normalized application-file drift` in the
  double-build reproducibility gate (job 111277991443 log 867; first image
  in its sequence; local double build at I byte-identical 2821/2821; the
  failure-diagnostics artifact does not include the first/second file
  manifests, so the CI-drifted file cannot be named). Both classes require
  repairs (apache pin + policy/test surfaces; supply-chain
  reproducibility/diagnostics) that order §5 explicitly forbids in this
  round; per the §5/§11 STOP clauses the executor reports and returns the
  decision to strategy.
- The 17-line Alpine repair itself is complete and verified: local
  (R1.1-R1.6 + R2 full evidence above) and CI (every Alpine image builds in
  both failing jobs; no apk resolution error anywhere in either log).
- The supply-chain job stopped at backend, so its later images (including
  apache) were not evaluated in that run; the compose job independently
  demonstrates the apache failure.

## Recommended strategic follow-up

1. Apache (Ubuntu) pin repair order: unscoped inventory of the pinned apt
   versions in `infra/apache/Dockerfile` (lines 17-21:
   `apache2{,-bin,-data,-utils}=2.4.58-1ubuntu8.15`,
   `openssl=3.0.13-0ubuntu3.15`) against the current noble archive, plus
   the paired `supply-chain/policy.json` `ubuntu_package_overrides`
   entries and the apache assertions in
   `tests/packaging/test_oci_contract.py` — the same defect class as the
   Alpine rotation (externally rotated index vs exact-version pin).
2. Backend reproducibility-drift investigation order (supply-chain
   tooling): first, extend the failure-diagnostics artifact to include the
   first/second rootfs file manifests so the non-deterministic file class
   can be named; the local double build at I is byte-identical (2821/2821)
   and the CI SBOM package level matched, pointing at an intermittent
   environment/timing-dependent cause (e.g. bytecode/wheel-build metadata
   path) rather than tree content.
3. State for acceptance: once classes A and B are resolved by follow-up
   orders, this branch should be able to reach 20/20 without further
   changes to the 17 lines (subject to class B's intermittency); the 079/2
   product implementation (079-2-a) remains otherwise fully delivered and
   locally verified.
