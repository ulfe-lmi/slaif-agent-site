# OAP Execution Report — 083-3-d: Python security pin and qualification closure

- ID: `083-3-d`; Objective 083, semantic increment 3; CLOSURE_ONLY.
- Mode: `AMENDED_EXISTING_PR`.
- Status: `PARTIAL` (definitive full local integration gate not
  green at I-d; pre-existing out-of-scope test assertion defect, section 9.1;
  implementation unchanged).
- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: [#102](https://github.com/ulfe-lmi/slaif-agent-site/pull/102), state OPEN, branch
  `oap/083-3-a-cache-outbox-consumer`, base `main`.
- Starting remote head (report-only S-c):
  `c78afd5f3411d3d42d95cfec67329c2d12c1d5d9`; S-c parent / c implementation
  head `33d38966c79fb4387eba279872f2000b1adcf6f0`; verified main
  `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`.
- Transcript T-d: `a6f2c7cedf3c0b364e8d8764ea3f640b33dc2b3d` (activated order and
  `oap/active` bytes only, unchanged).
- Implementation head SHA (I-d): `fe79b3af3a345df869e20fbfa0557e6b03ce7c9f`.
- Report publication commit: SELF.
- Pushed commits this round: T-d `a6f2c7c`, I-d `fe79b3a`.
- Activated order: `oap/orders/083-3-d-python-security-closure.md`,
  SHA-256 `9bebb5211518da868ca01bfc81702e80b1cee3520f7f4e51f392d2b8917dff37`.
- Active file bytes: `083-3-d\n`, hex `3038332d332d640a` (verified by xxd).
- Control FIFO OK: exact `4f4b` (2 ASCII bytes, no LF) received
  2026-10-18T00:30:03Z by the persistent foreground reader (receipt-3);
  `active` reread and matched this order exactly before execution.

## 1. Preflight, identity and registry reverification

GitHub reconciled read-only: PR #102 open on the required branch with base
`main`; S-c is the exact starting head; no duplicate increment PR; no existing
`083-3-d` report. T-d committed and pushed first with byte-identical order and
active content.

The exact registry target was independently reverified read-only on
2026-10-18 (~00:33–00:34Z) against `registry-1.docker.io` (auth token, `curl -L`
for blobs):

- multi-platform index
  `sha256:1fd55c2f838c4f76262f9eeed899ff9168ea96ac383c61667d6f204325e1f169`
  (registry header digest matched the locally computed blob hash);
- linux/amd64 manifest
  `sha256:9ce5a4e59b833c002e1c4196c60ec0b38977e3235d626298ba7ffe2e64f5a30c`
  (header matched local blob hash);
- amd64 config
  `sha256:56d444819cc60d5188b3e0d64396cf76a0b3e64a952836cb3155f6dc5a7e80b9`
  (registry location header matched the locally computed blob hash); config environment
  `PYTHON_VERSION=3.12.15`,
  `PYTHON_SHA256=c2c4321961fab0fb999d66e0cecf521c2ab3994c7992873ea99e306c1094fd5a`;
- source revision `2a3b794c223ab067d122719541cdd54a068732a5`, directory
  `3.12/alpine3.23`; PSF license attribution preserved.
- Local `docker run` of the pre-pulled amd64 image printed
  `Python 3.12.15`. Identity matched the order exactly; no substitution was
  needed.

## 2. Exact change set (five non-transcript files)

| File | Change |
| --- | --- |
| `services/backend/Dockerfile` | Provenance comment line 1 and both FROM literals (lines 2, 25): `python:3.12.12-alpine3.23@sha256:2d916811...` replaced with `python:3.12.15-alpine3.23@sha256:1fd55c2f...`. uv frozen install, package overlays, paths, deterministic metadata, non-root user and confinement preserved. |
| `supply-chain/policy.json` | Only `oci_sources.python` set to the same exact target; Apache 8.17, OpenSSL, Chrome and every other field untouched. |
| `docs/DEPLOYMENT.md` | Only the current Python image/version/digest table row (line 142). |
| `supply-chain/browser-worker-critical-matrix.json` | One candidate-8 qualification record appended to `qualification_history` (all five prior records, `entries`, `scanner` and `schema_version` verified byte-identical by re-dump comparison before write). |
| `tests/supply_chain/test_policy.py` | History length 5 to 6; `previous` block now exactly candidate-7 values; `current` block exactly measured candidate-8 values. No assertion weakened. |

`git diff --stat` against T-d: 5 files, +82/-25. Zero residual
`3.12.12`/`2d916811` references in the three pinned files.

## 3. C-3 evidence integrity — explicit correction of the immutable c report

The immutable c report (unchanged here) states the isolated integration run was
cancelled at 51/320 with 0 failures. That is not what the retained evidence
shows, and is corrected as follows:

- The preserved c log
  (`/tmp/oap-083-3-d/evidence/c-isolated-log-preserved-20261018T003213Z.txt`,
  SHA-256
  `de69c98eac4dfd6dc6e5aefd8a80d7c1dc6697e51330aba8af93070718f3e470`)
  contains an `F` marker at test 55, and its retained content covers roughly
  100 tests (last write 00:31:16Z). The c report's 51/320-with-0-failures
  statement is therefore not supported by its own retained log.
- The c cancellation killed wrapper PID 1237264; the real children, uv
  `1237274` and pytest `1237281` (reparented to init), kept running until d
  killed them at 2026-10-18T00:32:28Z (verified gone; pre-kill ps snapshot
  `orphan-ps-before.txt` shows etime 29:05 at 00:32:13Z, consistent with the
  retained START 00:03:07Z). One orphaned `slaif_test_*` database was dropped;
  no `slaif%` login roles remained.
- The c kill time is only derivable (about 00:11Z from 51 tests at the measured
  ~10 s/test pace); the exact kill time is NOT RETAINED. The F's test identity
  is NOT RETAINED (pytest `-q` prints failure detail only in the final summary,
  which the killed run never wrote).
- Only the HUMAN can approve a vulnerability exception. The c report's
  suggested "strategic exception" wording granted no such authority, and none
  was exercised.

## 4. Stale disposable fixture state — discovery, root cause, cleanup

A new d-local finding, fully within the disposable test infrastructure (no
product, privilege or test-code change):

- The first full isolated integration run (2026-10-18T00:35:40Z to
  01:41:48Z, exit 1) completed 316 passed and 4 errors. All four errors are in
  `services/backend/tests/integration/test_foundation_postgres.py`, all at
  session-scoped `foundation_database` fixture setup, all with the exact
  signature `asyncpg.exceptions.InsufficientPrivilegeError: permission denied
  for schema agentcow` (full traces preserved in
  `/tmp/oap-083-3-d/integration-full.log`). The fixture deploys the
  `agentcow.postgres` foundation COW functions as a fresh ordinary
  `qualification_setup_<suffix>` role; the error means the `agentcow` schema
  already existed, owned by another (dead) role.
- An immediate targeted rerun of the same module before any cleanup failed
  4/4 with the identical signature (reproducible; not load-related).
- Container inspection of disposable PostgreSQL 18.6
  `slaif-integration-pg-0833b` (provisioned 2026-10-17T22:24:45Z during the b
  round) found schemas `agentcow` and `qualification_8e37024a8bd0` plus three
  login roles (`qualification_setup/runtime/reviewer_8e37024a8bd0`), all owned
  by the dead role `qualification_setup_8e37024a8bd0`. This is exactly the
  residue of a force-killed integration session whose fixture teardown
  (`DROP OWNED BY ... CASCADE` + `DROP ROLE`) never ran.
- Attribution by elimination: b's immutable report records b's local
  integration run as CANCELLED mid-run at b's closure (b response OK
  2026-10-17T23:31:31Z). That run started after 22:24:45Z and, at the measured
  ~10.7 s/test pace, had passed the foundation module (tests ~201, around
  23:01Z) before its cancellation, and never completed. The retained c log
  proves c's run was killed at roughly 100 tests, before the foundation module
  was reached, so c cannot have created this state. No other integration
  session ran on this container between the two. The session uuid suffix is not
  recorded in any retained log, so the attribution to b's killed run is by this
  causal chain, not by a recorded identifier; b's exact kill time is NOT
  RETAINED.
- Cleanup (executor-owned disposable test state, logged in
  `/tmp/oap-083-3-d/evidence/stale-foundation-state-cleanup.log`):
  `DROP OWNED BY` (CASCADE) for the three dead roles, then `DROP ROLE` for
  each, all exit 0; post-check shows 0 `qualification_%`/`agentcow` schemas
  and 0 `qualification%` roles.
- Post-cleanup targeted rerun: 4/4 passed in 1.31 s (exit 0).
- The definitive full isolated run (320 tests, no concurrent load) follows in
  section 9. The 316+4 result of run 1 is retained as-is and is NOT aggregated
  with the clean rerun as a single passing full run.

## 5. Measured six-image qualification (pipeline exit 0)

Fresh full pipeline (`tools/supply_chain/run.sh`), window
2026-10-18T00:36:56Z to 01:03:30Z (log head/tail), `PIPELINE_EXIT:0`,
tag prefix `slaif-supply-1265319-`, double builds retained for
reproducibility. Terminal lines:

- `supply-chain-evidence: OK images=6 critical=0 high=43`
- `supply-chain-evidence-checksum: OK`
- `supply-chain-gate: OK evidence=/tmp/oap-083-3-d/evidence-run-d`

Scanner and database provenance: Grype 0.117.0 (image
`sha256:ddf9e9f204049f3a4a0955ef70873cabab6a31432125ad4f20a490b54950`,
source commit `b5fa92bbcbef655497e3be840a2f718380e2cdd3`) and Syft 1.51.0
(image `sha256:678bfa565b60f747aac0f8e964fe5588a24445b8d0a480e91f6efd70020dfbb0`,
source commit `2293641e3bd628a01bb37639318d62c0ebe89b39`); Grype database
v6.1.10 built `2026-10-17T06:27:09Z`, checksum
`sha256:4c2b8b0cd02313f74a50c81c457796660c4997565cc2ff211e09cc1880205c10`,
valid, age 18.604 h at validation. Exception sets: 0 vulnerability,
0 license.

Per image (image_id / local reference / severity counts / unexcepted Critical):

| Image | Base | image_id | Findings (C/H/M/L/N/U) | Unexp. Critical |
| --- | --- | --- | --- | --- |
| apache | ubuntu:24.04@sha256:33ceb719... | sha256:c3a3fa4c... | 0/0/195/17/3/0 | 0 |
| backend | python:3.12.15-alpine3.23@sha256:1fd55c2f... | sha256:f4d796e1... | 0/1/15/1/1/0 | 0 |
| browser-worker | playwright:v1.62.1-noble@sha256:dcc5531e... | sha256:b7bdedc5... | 0/4/1594/107/14/0 | 0 |
| nginx | nginx:1.29.7-alpine3.23@sha256:e7257f1e... | sha256:a9814c3f... | 0/24/31/1/0/1 | 0 |
| postgres | postgres:18.6-alpine3.23@sha256:697c180d... | sha256:7dbde783... | 0/7/5/1/0/0 | 0 |
| web | node:24.14.1-alpine3.23@sha256:8510330d... | sha256:3a4e9318... | 0/7/9/4/0/0 | 0 |

High review findings total 43 (visible review evidence; not a clean claim).
Low 131, Medium 1849, Negligible 18, Unknown 1 (bundle `severity_totals`).

CVE dispositions (exact, per strategy's scope clarification):

- CVE-2026-19445 is absent from the PATCHED BACKEND: 0 matches against
  `pkg:generic/python@3.12.15` (the interpreter this round upgrades from
  3.12.12).
- CVE-2026-19445 is NOT globally absent: four Medium-severity distribution
  matches remain in the browser-worker image (Ubuntu noble
  `python3.12 3.12.3-1ubuntu0.15` packages `python3.12`,
  `python3.12-minimal`, `libpython3.12-stdlib`, `libpython3.12-minimal`).
  They are disclosed here and do not trigger the Critical-only policy. No
  browser OS repair or exception was authorized or performed.
- CVE-2026-103628: 0 matches in all six refreshed scans.

Identities and hashes (full values in the evidence index; 16-hex prefixes
shown): scan SHA-256 apache `d0da099c`, backend `cec86af2`, browser-worker
`484f0828`, nginx `bb896225`, postgres `34b61ce1`, web `50bb34d6`; SBOM SHA-256
apache `11c94119`, backend `aca18e3a`, browser-worker `2aab416c`, nginx
`ce3db771`, postgres `fb4a0ac3`, web `cb44b48a`; scan-SBOM SHA-256 apache
`213835b6`, backend `938474f5`, browser-worker `541657dd`, nginx `e8eab6ba`,
postgres `a669566c`, web `752c6553`. `index.json` SHA-256
`88c675d3fbc5dcbef26ca82cd08f0471a947adb1e5122af9146b2b37b3046da0`;
`SHA256SUMS` SHA-256 `760fb79d9fc028dbdb3faa958d4fadaf18f1f07322b2f1bf7fafd111bc84b04c`.

SBOM identities: backend Python PURL `pkg:generic/python@3.12.15`;
browser-worker Chrome PURL `pkg:generic/chrome@155.0.8059.84` and Playwright
`pkg:npm/playwright-core@1.62.1`; Apache installed 4x
`2.4.58-1ubuntu8.17`. Bundle browser binary inventory (measured):
`Google Chrome for Testing 155.0.8059.84`, executable SHA-256
`b866a2964538c825538c454de4867973b926650da57ec12dc3328807d768247b`.

Reproducibility (honest characterization): all six images show
`application_files_equal=true` and `package_manifests_equal=true` with
`image_ids_equal=false` — normalized application/package-level
reproducibility within the pre-existing Docker/OCI layer-timestamp boundary;
the images are not bit-identical.

Strategy's independent bundle review
(`/tmp/oap-083-3-d/bundle-independent-review.json`): all 53 checksum entries
verified, all six raw scans Critical 0 / High 43 / exceptions 0, database
fresh, backend binary-classified Python 3.12.15 with CVE-2026-19445 absent,
browser Chrome for Testing 155.0.8059.84 with CVE-2026-103628 absent, index
SHA `88c675d3...` matching, read-only `validate-bundle` exit 0, actual Syft
python3.12 binary SHA-256
`bbe1110dea5ad4c33d3a74cac9ba40e3a8c0831b17d18aba7431fd4931bdfaa7` recorded.

Candidate-8 record appended with the measured values above
(`qualification_date 2026-10-18`; official CfT metadata timestamp
`2026-10-17T09:18:35.172Z` as recorded in the b round; archive SHA-256
`cf0f049892dea22e6a6db26d47ed0d7776b7158edcbec4634086633df8bafcbc`;
`image_digest sha256:3d66c69ff3bc28b86f5781f4bb5a1af6d90c92b7d94766614cddc2834a903007`;
1719 browser-worker matches; 43 high review findings; `checksum_validation
PASS`). `test_policy.py` now asserts the record. Post-edit rerun:
`uv run --frozen pytest tests/supply_chain tests/packaging -q`
86 passed + 54 subtests, exit 0.

## 6. Backend runtime evidence from the fresh image

From `slaif-agent-site-backend:local` freshly built by the d smoke (not the
cleaned pipeline tags):

- `python3 --version` prints `Python 3.12.15`.
- `/usr/local/bin/python3.12` (14000 bytes, upstream build 2026-10-01)
  SHA-256 `bbe1110dea5ad4c33d3a74cac9ba40e3a8c0831b17d18aba7431fd4931bdfaa7`
  — identical to the Syft-measured binary hash in the pipeline bundle and in
  strategy's independent review.
- `/usr/local/lib/libpython3.12.so.1.0` SHA-256
  `9a81341e676a200bb0d00d6093220b5fb017c3026b0fd7802a253d38901d7c70`.
- `ssl.OPENSSL_VERSION`: `OpenSSL 3.5.9 29 Sep 2026`.
- Evidence file: `/tmp/oap-083-3-d/backend-runtime-evidence.txt`.

## 7. Complete Compose smoke (all 19 projects)

`tools/compose/smoke.sh slaif007smoke0833d`, START 2026-10-18T01:15:34Z,
`SMOKE_D_EXIT:0` at 01:33:29Z, log
`/tmp/oap-083-3-d/compose-smoke.log`. All six images built fresh (no stale
reuse); overlap with the integration run used separate fixture databases, as
explicitly authorized.

- `browser-worker-image-policy: OK playwright=1.62.1 cft_revision=1697595
  chromium=155.0.8059.84 browsers=chromium-only package-manager=absent`
- `compose-e2e: OK projects=19 setup=1 governance=1 preview=1
  preview-filtering=1 stable-devices=6 agent-sessions=2 agent-workspace-puck=2
  freeze-review-snapshot=1 review-surface=1 accept-lifecycle=1
  discard-lifecycle=1 media-publication=1 artifacts=disabled`
- All six stable devices passed (desktop Chromium/Firefox/WebKit, tablet,
  mobile Chromium/WebKit); browser e2e projects all PASSED;
  `media-e2e: OK`, `human-editor-envelope: OK`, `governance-e2e: OK devices=6
  users=4`, `edge-header-policy: OK`, `edge-body-limit: OK`,
  `database-login-policy: OK exact-roles=11`, all secret-file policies OK,
  browser artifact/restart/recovery/outage/secret-recovery stages OK,
  `control-readiness-fixture: OK failures=6 recovery=clean`,
  `render-locator-recovery: restored render=healthy web=healthy nginx=healthy`,
  `negative-bootstrap: correctly blocked`.
- Apache adapter: built on `apache2=2.4.58-1ubuntu8.17`
  (+bin/data/utils) and `openssl=3.0.13-0ubuntu3.16`; `apachectl -t`
  `Syntax OK`; `nginx -t` successful; `compose-smoke: OK`.
- No project filters; no omitted later stages; overall exit 0.

## 8. Standing checks on a clean tracked verification copy (I-d tree)

Copy created by `git archive` of `fe79b3af3a345df869e20fbfa0557e6b03ce7c9f`
into `/tmp/slaif-verify-d` (tree
`acb8bc7746610d7887a315a09e9c2c8a6b221f31`; 1081 tracked files; strategy
independently verified identity). No untracked runtime artifacts present. All
31 commands exited 0 (log `/tmp/oap-083-3-d/verify-d-gates.log`):

- Python: `uv lock --check`; `uv sync --frozen --all-groups`;
  `uv run --frozen ruff check services/backend tests/repository tools`;
  `ruff format --check` (same paths); `uv run --frozen mypy` (Success, 310
  source files); `uv run --frozen pytest services/backend/tests/unit
  tests/repository -q` (788 passed + 26 subtests); `uv build --out-dir
  /tmp/slaif-agent-site-distributions-d`.
- Process smoke: all ten `python -m slaif_agent_site.<module> --check`
  commands exit 0.
- Node: `node --version` (24.x), `pnpm --version` (11.22.0), `pnpm install
  --frozen-lockfile`, `pnpm lint`, `pnpm format:check`, `pnpm typecheck`,
  `pnpm test`, `pnpm build`, `pnpm licenses list --json` (full JSON retained
  at `/tmp/oap-083-3-d/verify-d-licenses.json`).
- Preparation: `python -m compileall -q tools tests/repository`; `python -m
  unittest discover -s tests/repository -p 'test_*.py'` (71 tests, OK);
  `python tools/check_repository.py` (PASS); `python tools/check_mermaid.py`
  (exit 0 with a temporary `kernel.apparmor_restrict_unprivileged_userns=0`
  relaxation for rendering; original value 1 restored and verified on every
  exit path); `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` (533 files,
  0 issues).

Contracts and OpenAPI identity: `contracts/` and `packages/` are not in the
diff; the recursively stripped OpenAPI digest (all `x-slaif-` keys removed at
every nesting level, lists recursed, `sort_keys=True` compact separators,
default ASCII, UTF-8, no trailing newline) recomputed at I-d equals
`921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83` exactly.

## 9. Integration suite — complete history (no skips, no filter reduction)

- Run 1 (full, 2026-10-18T00:35:40Z to 01:41:48Z, exit 1): 316 passed,
  4 errors — the four foundation errors documented in section 4 (stale
  pre-existing fixture state, not a product failure).
- Targeted module rerun pre-cleanup (01:42:37Z, exit 1): 4 errors, identical
  signature (reproducible evidence).
- Stale-state cleanup (section 4), then targeted module rerun (01:44:49Z,
  exit 0): 4 passed.
- Run 2 (definitive full, START 2026-10-18T01:45:07Z,
  `INTEG_FINAL_EXIT:1 2026-10-18T02:53:13Z`, duration 4081.34 s, no
  concurrent smoke or build load, tree `fe79b3af`, log
  `/tmp/oap-083-3-d/integration-final.log` SHA-256
  `5f94be98b491434ed67b05f99743d19c5cefd89a965d0c9cab910bf3c74e63b7`,
  archived and hash-checked by strategy): `1 failed, 319 passed in
  4081.34s (1:08:01)`; command `uv run --frozen pytest
  services/backend/tests/integration -q` with `set -o pipefail` and
  `${PIPESTATUS[0]}`. The four foundation tests that errored in run 1 all
  passed in-suite after the section-4 cleanup, confirming the fix under the
  real 320-test session interaction. The single `F` is ordinal 230 of the
  collected order (three full 72-result rows, then thirteen dots and `F`):
  `services/backend/tests/integration/test_human_editor_production_http.py::test_editor_agent_structural_races_share_workspace_site_lock`.
- Isolated single-node retest of that node after the full run
  (START 02:54:38Z, `RETEST_EXIT:1 2026-10-18T02:55:04Z`, `1 failed in
  24.19s`, fresh fixture database, no concurrent load, log
  `/tmp/oap-083-3-d/integration-single-retest.log`): identical assertion at
  line 1405 with the identical ordered status pair. A pass in isolation
  would not erase the failed full run; this one failed identically.

No child-unchecked cancellation; every run's real exit is recorded above via
pipefail/PIPESTATUS.

### 9.1 Failure classification — pre-existing out-of-scope test defect

- Observed terminal race (test barrier releases both production calls
  against the shared structural advisory lock):
  `POST /api/agent/v1/pages/{id}:restore` -> `409`
  `{"code":"RESOURCE_CONFLICT"}` and `POST /api/agent/v1/redirects` -> `201`
  `REDIRECT_CREATED`. Exactly one winner and a clean conflict on the loser:
  correct serialized product behavior.
- The failing assertion (`test_human_editor_production_http.py:1405`,
  continuation line 1407) is
  `assert sorted((agent_restore.status_code, agent_restore_redirect.status_code)) in ([200, 409], [409, 201])`.
  The literal `[409, 201]` is an unreachable sorted output: the ascending
  sort of any `(409, 201)` pair is `[201, 409]`. Under the product's
  exactly-one-winner behavior the test can therefore pass only when the
  restore side wins the race, and is guaranteed to fail whenever the
  redirect-create side wins.
- A second latent instance of the same unreachable `[409, 201]` alternative
  exists at line 1586 (redirect-delete vs dependent-create race,
  `in ([200, 409], [200, 422], [409, 201])`); it is never executed in either
  run because the line-1405 failure aborts the test first.
- Provenance: the file was last modified by `d2bc4fb` (Objective 078-x) and
  is untouched by PR #102 and this round (`git diff HEAD --stat` empty). The
  defect predates this increment and is outside d's closed five-file scope;
  no test, application, gate or configuration change was made or is
  authorized in this round.
- Scheduling evidence: the same node passed in run 1 (restore side won the
  race there) and failed identically in run 2 and in the isolated retest
  (redirect side won). The pattern matches a race-outcome-dependent test
  with a dead expected-pair branch, not a product regression introduced by
  the five-file change set.
- CI distinction: `.github/workflows/ci.yml` at I-d contains no reference to
  `test_human_editor_production_http.py` in any integration job file list
  (grep: no match), so the 20/20 CI SUCCESS at I-d and the local
  full-directory exit 1 are complementary evidence, not a contradiction.
- The finite correction (replace the unreachable `[409, 201]` literals with
  the reachable `[201, 409]` outcomes at both sites) is a test-code change
  for the next activated continuation; it is not performed here.
- Consequence: the definitive full local integration gate is not green at
  I-d; this round therefore closes as PARTIAL with all other gates exactly
  as recorded above.

## 10. GitHub required checks at I-d `fe79b3af`

| Check | Run ID | State at I-d |
| --- | --- | --- |
| Analyze (actions) | 117557474016 | SUCCESS |
| Analyze (javascript-typescript) | 117557474004 | SUCCESS |
| Analyze (python) | 117557473928 | SUCCESS |
| CodeQL | 117557555605 | SUCCESS |
| Compose and edge packaging | 117557452278 | SUCCESS |
| Dependency review | 117557452137 | SUCCESS |
| Detect supported languages | 117557451995 | SUCCESS |
| Foundation PostgreSQL 14 | 117557452229 | SUCCESS |
| Foundation PostgreSQL 15 | 117557452250 | SUCCESS |
| Foundation PostgreSQL 16 | 117557452236 | SUCCESS |
| Foundation PostgreSQL 17 | 117557452259 | SUCCESS |
| Foundation PostgreSQL 18 | 117557452262 | SUCCESS |
| Markdown | 117557452203 | SUCCESS |
| Mermaid | 117557452185 | SUCCESS |
| Node contracts | 117557452091 | SUCCESS |
| Python 3.12 quality and package | 117557452212 | SUCCESS |
| Python 3.13 quality and package | 117557452196 | SUCCESS |
| Python 3.14 quality and package | 117557452138 | SUCCESS |
| Repository policy | 117557452247 | SUCCESS |
| Supply-chain evidence | 117557452122 | SUCCESS |

All twenty required names terminal SUCCESS observed before report
publication; run IDs and observed SHA `fe79b3af3a345df869e20fbfa0557e6b03ce7c9f`
recorded above. No deterministic rerun performed; the single documented CI
flake allowance remains unused (all prior c I/S CI and CodeQL runs verified
at run_attempt=1). The one locally failed file,
`test_human_editor_production_http.py`, is not in any CI integration job
file list, so these CI results do not cover it; see section 9.1.

## 11. PR description

Updated on 2026-10-18 (~01:47Z) via REST PATCH to PR #102 per d4.9: actual
delivered behavior across the four rounds, anonymous public surfaces
described separately from capability-scoped private workspace/review surfaces
with no public-rendering-needs-capability implication, the Python 3.12.15 pin
with the CVE-2026-19445 backend-absence/browser-worker Medium-disclosure
distinction, observed validation (local gates, six-image qualification,
19-project smoke, CI per head), and the bounded-increment limitation. No new
issue, comment or PR; no predicted-green language.

## 12. Budget (recomputed against the verified c baseline)

This round (d): 2 production/config (`services/backend/Dockerfile`,
`supply-chain/policy.json`), 0 migrations, 2 tests/evidence
(`supply-chain/browser-worker-critical-matrix.json`,
`tests/supply_chain/test_policy.py`), 1 docs (`docs/DEPLOYMENT.md`),
3 transcript paths (order-d, report-d, active overlap).

Cumulative base `214909f` to S-d: 49 files = 12 production/config + 1 existing
migration, 18 tests/evidence, 9 docs, 9 transcript, 0 generated — exactly the
order's expected values; zero variance. Itemization at I-d (48 files; the
report adds the 49th transcript path):

- 12 production/config: `infra/apache/Dockerfile`,
  `services/backend/Dockerfile`, `services/backend/src/slaif_agent_site/bootstrap/service.py`,
  `services/backend/src/slaif_agent_site/db/privileges.py`,
  `services/backend/src/slaif_agent_site/review_worker/config.py`,
  `services/backend/src/slaif_agent_site/review_worker/outbox_consumer.py`,
  `services/backend/src/slaif_agent_site/review_worker/worker.py`,
  `services/browser-worker/Dockerfile`, `supply-chain/policy.json`,
  `tools/compose/smoke.sh`, `tools/supply_chain/evidence.py`,
  `tools/supply_chain/policy.py`.
- 1 migration: `services/backend/src/slaif_agent_site/db/alembic/versions/074_001_cache_outbox_consumer.py`.
- 18 tests/evidence: 9 integration tests, 3 unit tests, 2 e2e specs,
  `tests/packaging/test_oci_contract.py`, 2 `tests/supply_chain` tests,
  `supply-chain/browser-worker-critical-matrix.json`.
- 9 docs: `README.md`, 5 `docs/*.md`, `oap/INCREMENTS.md`,
  `oap/MVP-CONTRACT-AUDIT.md`, `oap/MVP-PROGRESS.md`.
- 9 transcript: `oap/active`, 4 orders (a-d), 4 reports (a-d).

## 13. Scope, security and completion confirmations

- Diff from starting head changes only the five named files plus order/active
  transcript bytes; untracked `.codex/`, `CODEX-SESSIONS.md`, `codex.sh`
  preserved and never staged.
- No vulnerability/license exception; no gate weakening; no dependency,
  lockfile, workflow, role, migration or topology change; foundation remains
  registry `agent-cow-postgresql==0.2.0` with frozen hashes.
- No new PR, no merge, no auto-merge, no PR closure; no edits to earlier
  orders or reports (c correction is stated here, in the new report only).
- No secrets, production systems or protected resources touched; all local
  setup (Node 24 toolchain PATH, uv 0.12.5, disposable PostgreSQL container,
  pinned scanner images) is routine executor authority.
- Initial failure disclosed: the first packaging/supply-chain targeted run
  exited 1 because two `test_browser_archive_extractor` tests invoke
  `node` and the session PATH lacked the Node 24 toolchain directory; the
  re-run with the correct PATH passed 86 + 54 subtests on the same tree.
- No repository mutation follows S-d.

## Limitations and open items

- Status is PARTIAL, not COMPLETE: the definitive full local integration
  directory at I-d exited 1 (319 passed, 1 failed) on a pre-existing
  out-of-scope test assertion defect (section 9.1, two sites, one latent).
  The implementation is unchanged; the finite two-site test correction
  belongs to the next activated continuation. No result is aggregated or
  re-labelled; run 1's 316+4 and run 2's 319+1 stand separately.
- Checks newly started by the report-only S push are honestly pending in this
  report; strategy verifies all twenty independently at S.
- Four Medium browser-worker CVE-2026-19445 distribution matches remain
  disclosed (Critical-only policy; no exception; no browser OS repair
  authorized).
- The b/c acceptance obligations (whole-round scope, final 20/20 at the final
  report-only head) remain with strategy; this round does not claim
  whole-product readiness.
