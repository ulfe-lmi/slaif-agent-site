# OAP 083-5-e execution report — restore PostgreSQL overlay availability and final gates

## 0. Status

| Field | Value |
| --- | --- |
| Round | 083-5-e (numeric objective 083, increment 5, round letter e) — CLOSURE_ONLY |
| Order | `oap/orders/083-5-e-restore-postgres-overlay-and-final-gates.md` (240 lines, committed unchanged with the e implementation commit) |
| Order SHA-256 | `7edacf25d1b44fdd23c8fbf3559c71dee45fac7eefa23ff249ddec72bdcf5368` |
| `oap/active` bytes | `083-5-e\n` (8 bytes: `3038332d352d650a`) |
| PR mode | AMEND_EXISTING_PR (PR #107, no new PR, never merged) |
| Status | **COMPLETE** — every executable e criterion actually executed and qualified at literal I `24a4333` (section 6: G1 ALL31, G2 FULL 347 + coherent RC7, G3 WHOLE, G4 OpenAPI, G5 fresh local ALL6; section 4 repair; section 5 diagnosis/context). The final report-only-S CI check table is recorded exactly as observed at the publication instant (PENDING per the order's explicit "SELF checks may honestly be pending at publication; root independently waits" allowance) and this report is NEVER amended after S to fill future-S results. COMPLETE is evidence, not acceptance. |
| d report | `oap/reports/083-5-d-isolate-qualification-and-truthful-review.md` at S `5fc12ddb8db72d3717825b5ca8488cd779b3a172` (remote bytes SHA-256 `95d46196e693a0d21aedac80d63e4b2eb3690c8ae165c17ed2bbc1087a9279df`) — IMMUTABLE, never edited; the root d-review corrections are applied in section 3 of this report only. |
| Report publication commit | SELF (this report; sole path; first parent exactly I `24a4333569be6f2201f94c07be56d702cb1a33da`) |

## 1. Identity, control handshake

- ID: 083-5-e, numeric objective 083, increment 5, CLOSURE_ONLY, AMEND_EXISTING_PR,
  same PR #107 / branch `oap/083-5-a-faithful-frozen-review` / base main
  `4bf74fdc8e74323045a7f8830cf393493e75fe0d`.

- Order (read FULL, immutable): 240 lines, SHA-256
  `7edacf25d1b44fdd23c8fbf3559c71dee45fac7eefa23ff249ddec72bdcf5368`,
  `oap/orders/083-5-e-restore-postgres-overlay-and-final-gates.md`.

- Active: `oap/active` = `083-5-e` + LF, 8 bytes, hex `3038332d352d650a`.

- This round's NEW control FIFO OK consumed 2026-10-25T16:40:40Z (payload `4f 4b`,
  exactly 2 bytes, no LF; receipt `/tmp/oap-083-5-e/control-ok-receipt.txt`).
  The d final handshake (response OK 2026-10-25T16:36:11.666457Z, sole root reader
  52653 terminal 0) is complete and was NEVER replayed. No response-FIFO write of any
  kind occurred during e until this final publication.

- Root d-handoff review read FULL:
  `workorders/083-5d-handoff-review-and-083-5e-prospective-decision-2026-10-25.md`
  (74 lines). Its required corrections are applied in section 3.

- Runtime clarification read FULL:
  `workorders/083-5e-isolated-database-port-compatibility-decision-2026-10-25.md`
  (55 lines) — the isolated qualification network context decision applied in
  sections 5/7.

## 2. PR and source identities

- PR #107 (OPEN, unique 083), branch `oap/083-5-a-faithful-frozen-review`, base main
  `4bf74fdc8e74323045a7f8830cf393493e75fe0d` (verified unchanged throughout e).

- Starting remote S (d report-only): `5fc12ddb8db72d3717825b5ca8488cd779b3a172`
  (remote bytes verified equal to local before e implementation).

- Pushed e implementation commit (first-parent chain from starting S):
  - `24a4333569be6f2201f94c07be56d702cb1a33da` — libcurl 8.22.0-r0 -> 8.23.0-r0
    forward repair + e order + active (6 paths: `infra/postgres/Dockerfile`,
    `supply-chain/policy.json`, `tests/packaging/test_oci_contract.py`,
    `docs/SUPPLY_CHAIN.md`, `oap/active`, e order).

- LITERAL IMPLEMENTATION I: `24a4333569be6f2201f94c07be56d702cb1a33da`
  (tree `e59de814afd7a334f9e37c482961fc4b1962a7c6`; clean worktree
  `/home/janezp/codex-work/slaif-agent-site-i-e-final`, derived via git metadata,
  0 dirty paths at every gate boundary).

- Report publication commit: SELF (report-only; first parent exactly I).

## 3. d-report corrections (required in e; d never edited)

Root read the full 526-line d report; the following corrections apply to NEW e
reporting only (the published d report remains immutable):

1. d section 10 "CI 22+2" was wrong: the actual CI at d-I was 25 jobs with
   23 SUCCESS + 2 FAIL (Compose + Supply-chain); CodeQL comprises 4 workflow
   jobs plus a separate app CodeQL check (5 checks total). All 30 current-S
   checks need SUCCESS; the original contract is 20 required names + 10
   internal PG children.
2. d section 11 transcript: the transcript is NINE files at d-S (a/b/c/d
   orders+reports = 8 plus active = 1), not ten; the maximum was NINE, not ten.
   e adds the order + report, making ELEVEN at e-S (named maximum 11).
3. d G1 actual first command started 16:14:20.482563532Z (not 16:14:14, which
   was the manifest directory launch instant). The earlier c4e CMD 09 orphan
   disappearance was observed; spontaneous termination was NOT proved.
   Discarded source-mixed attempts are never final. Exact checkout chronology
   from actual tool calls: commit `c4e6606` at 15:56:02, `1384944` at 15:48:47.
4. d G4 log contains result lines only, with no claimed exact command header;
   the actual function call/output supplies the module argv, native 0, and the
   root receipt. Stated accordingly in this report's G4 section.
5. d section 9 overclaims corrected here: no exact rotation interval is
   established (only the measured bracket: same source built at I5 CI ~14:30Z
   and failed at c4e CI 15:59:01Z); "unchanged rerun cannot pass" is NOT
   established (two fetches do not prove an immutable future condition; the
   old 8.22 asset still returned HTTP 200 and was never claimed purged); and
   "ABI-consistent" is only an advertised SONAME fact, not runtime
   compatibility proof. Distinctions preserved: index-data SHA
   `a9e37a02e9e650f2029891f4e82c13e753751bbd0cb971c2c305034b28f0f6d8` (extracted
   APKINDEX data) vs tarball wrapper SHA; index `C:Q1DLQrtkoWtPiGrkrdimiRkh9NgEs=`
   is an APK checksum, NOT the archive SHA-256; `c856d762...` is the source
   COMMIT, NOT a package SHA-256; package build timestamp 2026-10-25T15:50:38Z
   is BUILD time, not a publication/rotation time; Last-Modified
   2026-10-25T15:52:37Z is index metadata, not direct installation evidence.
6. d did NOT establish that its 503 shares the cause with c's I5 G2 `.E`, nor
   did it disprove all environment issues. The ACTUAL current-cause diagnosis
   (d-round 55443 dedicated context) is completed in section 5: deterministic
   TEST-mode DSN port-guard rejection. c's I5 `.E` remains a separate run with
   an unestablished cause; no same-cause claim is made.
7. The fresh RC7 at c-I5 was NOT qualified; the d report's reference to "c
   coherent RC7 at I5" as fresh proof is incorrect. b scoped history is not
   fresh final proof. Fresh coherent RC7 is re-run at I in section 6.
8. This report supplies the full R1-R9 / A-F / RC1-RC9 inherited evidence index
   (section 9) with criterion-by-criterion source/test/log/hash/native outcome
   and scope, honest not-runs included, and no adjacent/scoped evidence
   relabelled as complete.

## 4. e narrow repair — libcurl 8.22.0-r0 -> 8.23.0-r0 (exact named paths only)

### 4.1 Measured upstream state (re-confirmed BEFORE editing)

- Official `https://dl-cdn.alpinelinux.org/alpine/v3.23/main/x86_64/APKINDEX.tar.gz`,
  fetched 2026-10-25T16:43:26Z (and re-fetched for stability): HTTP/2 200,
  etag `"6ade25c5-7fd3a"`, Last-Modified `Sun, 25 Oct 2026 15:52:37 GMT`,
  content-length 523578; extracted APKINDEX data SHA-256
  `a9e37a02e9e650f2029891f4e82c13e753751bbd0cb971c2c305034b28f0f6d8` —
  identical to the order and to the root independent review
  (`/tmp/oap-083-5-d/strategic-libcurl-index-and-asset-independent-review.json`).
  The tarball wrapper SHA-256 is a distinct object
  (`af8c1e4af0cdb9cb18c8bbbc38e557b26051b4e2a312ca2c478fda621d3ac24d`,
  stable across both e-round fetches).
- Current index lists libcurl `8.23.0-r0` ONLY (S:364575); 8.22.0-r0 and
  8.20.0-r0 are absent from the index. The other overlay pins remain present:
  `brotli-libs 1.2.1-r0`, `libcrypto3 3.5.9-r0`, `libssl3 3.5.9-r0`.
- Asset `https://dl-cdn.alpinelinux.org/alpine/v3.23/main/x86_64/libcurl-8.23.0-r0.apk`:
  HTTP/2 200, 364575 bytes, SHA-256
  `d35e08ce3bafbcaf1a68512ac31483bd93e795ad5e8d8bfd76ada3106d81b569` — matches
  the order. Receipt: `/tmp/oap-083-5-e/libcurl-8.23-availability-receipt-e.json`.
- Scope honesty: the asset SHA is provenance evidence, not permission for a new
  download mechanism; installation still goes through the SAME existing signed
  Alpine v3.23/main repository with apk signature/package verification inside
  the image build.

### 4.2 Exact change (6 paths; no other source touched by the repair)

- `infra/postgres/Dockerfile`: pin `'libcurl=8.22.0-r0'` -> `'libcurl=8.23.0-r0'`
  and the in-build installed-version assertion `= "8.22.0-r0"` ->
  `= "8.23.0-r0"` (lines 23/27). FROM base index digest
  `697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f`,
  `brotli-libs=1.2.1-r0`, `libcrypto3=3.5.9-r0`, `libssl3=3.5.9-r0`, the
  `--repository=https://dl-cdn.alpinelinux.org/alpine/v3.23/main` pin, and all
  other assertions unchanged.
- `supply-chain/policy.json:143`: `"libcurl=8.22.0-r0"` -> `"libcurl=8.23.0-r0"`
  (matching policy pin; JSON re-validated).
- `tests/packaging/test_oci_contract.py:83`: exact contract expectation
  `libcurl=8.22.0-r0` -> `libcurl=8.23.0-r0`; all denial checks
  (no `apk upgrade`, exact repository URL, other pins) preserved.
- `docs/SUPPLY_CHAIN.md`: current-status sentence updated to `8.23.0-r0` with
  precise package provenance (archive SHA-256, same signed standard
  repository). Historical OAP/browser qualification entries remain byte-exact.
- `oap/active` + e order committed with the implementation (strategic bytes).

No `--allow-untrusted`, no direct-APK workaround, no URL fallback, no vendoring,
no repository widening, no OS move, no package removal, no blanket upgrade, no
browser/Next/server/foundation/OS/OpenSSL/brotli pin change, no new
service/role/authority/license exception/feature.

### 4.3 Local proof at the repaired source

- Image build from the updated Dockerfile (worktree 5fc12dd + working-tree
  repair, pre-commit): apk upgraded `libcurl (8.20.0-r0 -> 8.23.0-r0)` and all
  four in-build installed-version tests passed (the build fails otherwise);
  manifest `sha256:dcbbd3c0e384e1dee91f6ad6584925cce042f5cc79f087e0df1894827120c4f3`,
  config `sha256:3b842d91af003c13d2a066c0556c0c4494ba6604595380e9df994706641248c3`.
  HONEST SCOPE: that build was logged through `docker build ... | tail -25`, so
  the recorded 0 is the `tail` exit, NOT the immediate docker-build child exit;
  completion is proven by the exported image and the subsequent runtime probe.
  The final ALL6 qualification (section 6, G5) captures actual child exits.
- Disposable runtime probe of that image (with `POSTGRES_PASSWORD` set):
  `PostgreSQL 18.6` started, `database system is ready to accept connections`,
  live `select version()` OK; authoritative `/lib/apk/db/installed` versions
  `brotli-libs=1.2.1-r0`, `libcrypto3=3.5.9-r0`, `libcurl=8.23.0-r0`,
  `libssl3=3.5.9-r0` (record `/tmp/oap-083-5-e/installed-versions-probe.txt`).
  A second probe without the password env exited (container not running; outer
  shell 0 is NOT an exec 0) — preserved as a distinct failed probe.
- Focused packaging contract at the repaired source:
  `uv run --frozen pytest tests/packaging` -> 49 passed, 38 subtests passed,
  actual child 0 (log `/tmp/oap-083-5-e/packaging-focused-attempt1.log`,
  17:01:38-39Z).

## 5. G2 503 diagnosis and the isolated qualification context (zero product change)

### 5.1 Scoped failure proof preserved (d round)

- Recovered original targeted-503 tool output (root-provided,
  `/tmp/oap-083-5-e/recovered-d-targeted-503-tool-output.json`,
  call_9c7c06988721fe1f at 16:21:12.223Z): expected 202, got 503,
  `test_agent_browser_http.py:280`, 1 failed in 15.39s; no underlying exception
  exposed in that log. Used as scoped failure proof only.
- d FULL attempt history (preserved, section 7 of the d report): attempt 1
  exit 1 in <8s zero output (cause UNKNOWN, unproven venv race); attempt 2
  347 collected then systematic first-module F pattern, TERM 143, no final
  summary (not inferred).

### 5.2 e focused strict single-test reproduction (serial, owned 55443 cluster)

- `PGHOST=127.0.0.1 PGPORT=55443 PGUSER=postgres PGPASSWORD=qualification-admin
  PGDATABASE=postgres uv run --frozen pytest
  services/backend/tests/integration/test_agent_browser_http.py -rA --tb=long -x`
  at I 43cd5454/tree a05d30ff, strictly serial (no concurrent owned pipeline),
  16:51:08-16:51:27Z: `1 failed, 1 error in 17.16s`, `SINGLE_CHILD_EXIT=1`
  (log `/tmp/oap-083-5-e/g2-diag/single-attempt1.log`). The 503 reproduces on
  the dedicated cluster with NO concurrent load — persistence, not transient
  host load of that window.

### 5.3 Two DISTINCT findings (both preserved; neither alone is the full story)

(a) Teardown role-dependency ERROR on an OLDER OWNED leftover: the same run's
fixture teardown raised
`DependentObjectsStillExistError('role "slaif_gc" cannot be dropped because some
objects depend on it')`. Measured cluster state (preserved in
`/tmp/oap-083-5-e/g2-diag/leftover-metadata-preserved.sql` and the role/DB
queries of the same window): one leftover disposable DB
`slaif_test_cf74e336d7` (owned by `postgres`, 0 user tables, plpgsql only) plus
its 11 `fixture_*_cf74e336d7` login roles, members of the 11 cluster-global
product roles — leftover of the d-round SIGTERM-interrupted run; the failing
test's own DB (`slaif_test_fa6760bece`) and its fixture logins had been
dropped by its teardown before the global-role drop failed on the older
leftover's membership. This proves owned-cluster leftover/dependency state; it
does NOT by itself explain the 503 (the 503 occurred before teardown).

(b) The 503 itself is a deterministic DSN configuration rejection. Scratch-only
instrumented driver (NOT shipped; no repo writes;
`/tmp/oap-083-5-e/g2-diag/diag_driver.py`, run
`/tmp/oap-083-5-e/g2-diag/driver-run1.log` 17:01:08-17:01:25Z at 43cd)
replicated the conftest fixture + `_seed` + app flow and measured, safely:
runtime-login identity OK with `slaif_agent_runtime` membership;
`SELECT count(*) FROM control.browser_run` refused with
`InsufficientPrivilegeError(42501)` (EXPECTED least-privilege, not a defect —
no grant made); `control.slaif_agent_browser_run_begin` exists with EXECUTE for
`slaif_agent_runtime` (proacl `slaif_owner=X/slaif_owner`,
`slaif_agent_runtime=X/slaif_owner`); a wrong-signature function probe raised
`UndefinedFunctionError(42883)` (guessed signature, NOT missing-API proof);
then, after the app lifespan: `pool_none=True`,
`reason=configuration_invalid`, readiness `unavailable/configuration_invalid`,
and both preview-run POSTs returned 503 `SERVICE_UNAVAILABLE`. Driver exit 0 is
diagnostic completion, NOT a passing product test.

- Root independently confirmed the discriminator:
  `AgentDatabaseSettings._validate_locator`
  (`services/backend/src/slaif_agent_site/agent_api/config.py:203`) rejects any
  explicit DSN port outside `{None, 5432}` EVEN in TEST mode (the host
  validation branch is never reached for 55443); the control/editor/render/
  review/media configs carry corresponding 5432 guards. The fixture settings
  construct an explicit `...@127.0.0.1:55443/...` locator, so
  `AgentDatabaseConfigurationError` is raised BEFORE `create_pool`, leaving the
  pool `None` and every request 503. The isolated 55443 host endpoint was
  therefore never a valid application test locator.
- Scope honesty: this establishes the cause of the MEASURED e/d-attempt 503s in
  the 55443 context. It does NOT establish that every older c-I5 `.E` error
  had this cause (separate run, separate environment, unestablished), and it
  does not disprove every other possible environment defect. No flake,
  transient, or benign label is attached to any historical attempt.

### 5.4 Isolated qualification network context (root decision; zero product change)

Per `workorders/083-5e-isolated-database-port-compatibility-decision-2026-10-25.md`:
a fully isolated OWNED context in which `127.0.0.1:5432` reaches ONLY the owned
disposable PG 18.6; host shared 5432 untouched; all port guards, roles, grants,
constraints, timeouts, pins preserved; NO test-mode validator relaxation, NO
product source change for this finding.

- The invalid owned 55443 cluster (`slaif-integration-pg-18-0835d`,
  `451c65f8b0...`, created 2026-10-25T15:45:53.37144506Z, anonymous volume
  `44f15ff1...`, loopback 127.0.0.1:55443) was decommissioned ONLY after
  metadata preservation and confirmation of no live owned children
  (final inspect: `/tmp/oap-083-5-e/owned-55443-final-inspect.txt`;
  leftover state: `leftover-metadata-preserved.sql`).
- New owned cluster `slaif-pg-e-186` (`447cf85041...`, created
  2026-10-25T17:10:59.214428179Z): image
  `postgres:18.6-alpine3.23@sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f`
  (local, no pull; same base digest pinned by the overlay), named volume
  `slaif-pg-e-186-data -> /var/lib/postgresql`, `POSTGRES_DB=qualification`,
  admin `postgres` with the conftest fixture default constant, and
  `HostConfig.PortBindings={}` — NO host port at all. First launch with
  `/var/lib/postgresql/data` mount failed (PG 18+ image requires the mount at
  `/var/lib/postgresql`; exit 1, log preserved in the container history) and is
  preserved as a failed attempt.
- Runner `slaif-runner-e` (base `python:3.13-slim`
  `sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f`):
  `--network=container:slaif-pg-e-186` (shares ONLY the owned PG network
  namespace), same-path mounts of the source worktree,
  `/home/janezp/.local/share/uv` (uv-managed CPython 3.13.14 gnu) and
  `/home/janezp/.local/bin/uv` (uv 0.12.5 exact), env
  `PGHOST=127.0.0.1 PGPORT=5432 PGUSER=postgres PGPASSWORD=qualification-admin
  PGDATABASE=qualification`. From inside the runner, `127.0.0.1:5432` reaches
  only the owned PG. Host shared cluster `slaif-integration-pg-0833b`
  (127.0.0.1:5432) NOT modified. Provenance:
  `/tmp/oap-083-5-e/isolated-context-provenance.json` and
  `/tmp/oap-083-5-e/g2-full-24a/live-provenance.json`.
- Focused strict proof in the corrected context at the SAME failing source
  43cd5454 (worktree mounted; in-runner git absent, so source identity is
  host-side): `uv run --frozen pytest
  services/backend/tests/integration/test_agent_browser_http.py -rA --tb=long`
  -> **2 passed in 22.19s, `FOCUSED_CHILD_EXIT=0`, no teardown ERROR**
  (`/tmp/oap-083-5-e/g2-diag/focused-isolated-run1.log`, 17:11:40-17:12:04Z).
  This is the expected-202 + clean-fixture-teardown proof required before full
  gates; it is scoped proof at the old I, NOT final qualification at the new I.
- Earlier failed probes preserved: `driver-run1-namederror.log`
  (missing-import NameError, own DB/roles cleaned), the no-password probe
  (container-not-running), and the aborted G2 launch whose redirect failure
  prevented execution (no container ran; re-launched cleanly).

## 6. Local final gates at literal I 24a4333 (clean immutable worktree
`/home/janezp/codex-work/slaif-agent-site-i-e-final`, derived via git metadata,
HEAD/tree recorded at start and end of each gate, 0 dirty)

### G1 ALL31 (standing 31 commands, IN ORDER) — QUALIFIED at I

- Manifest `/tmp/oap-083-5-e/final-I-24a-all31/` (unique; no overwrite of any
  earlier attempt). All 31 commands, each immediate child exit captured (no
  pipeline, no tail substitution): **31/31 EXIT=0, `ALL31_OVERALL_EXIT=0`,
  wrapper child 0**; 17:14:28.849Z -> 17:20:22.564Z.
- Source identity immutable across the run: start
  `SOURCE_HEAD=24a4333569be6f2201f94c07be56d702cb1a33da` /
  `SOURCE_TREE=e59de814afd7a334f9e37c482961fc4b1962a7c6`, end identical,
  `WORKTREE_DIRTY=0`.
- venv/dependency setup included (CMD 02 `uv sync --frozen --all-groups` EXIT 0)
  per the order's ALL31-before-FULL rule.
- Fractional-timestamp interpretation (root adjudicated; receipts
  `strategic-G1-fraction-format-adjudication.json` +
  `strategic-current-date-fraction-format-probe.json`): the v2 runner stamps
  with `date +%Y-%m-%dT%H:%M:%S.%6NZ`. The host `date` (uutils coreutils
  0.8.0, current SHA-256 `48893b0f...`) emits `%6N` as a VARIABLE-WIDTH
  nanosecond integer WITHOUT leading zeros (probe: at one instant
  `%N=014293694` / `%6N=14293694` / `%9N=014293694`, exit 0), so 8-digit
  fractions in the raw manifest (e.g. `17:14:29.62811270Z`) are actually
  `.062811270`. Read naively as fixed-width that produced the apparent
  regressions in the CMD 03-05 line pairs (CMD 03's EXIT appearing ~0.42s
  before its START). Left-padding every fraction to 9 digits, ALL 64
  manifest timestamps (31 START + 31 EXIT + overall/head/dirty lines) are
  strictly MONOTONIC with sane per-command durations (CMD 03 ruff check
  ~202ms, CMD 04 ~142ms, CMD 05 mypy 29.3s, CMD 06 unit pytest 37.7s). The
  RAW manifest is preserved byte-exact (SHA-256
  `4c1335d7c56b14a4fe00ef8748607d972c82dca04f2c59a593024f05839e73b2`) and
  is NEVER rewritten. Historical limit: the date binary hash was not
  captured at 17:14, so this is a consistent-with-emitter interpretation
  corroborated by the current emitter probe + exact runner source — NOT a
  claim of historical binary identity, and no clock-regression or
  concurrency-cause is inferred or invented. The exact synchronous argv per
  command, every immediate native 0, the 31 unique per-command stdout logs
  (cmd-01 `Resolved 45 packages`, cmd-03 `All checks passed!`, cmd-04
  `338 files already formatted`, cmd-05 `Success: no issues found in 316
  source files`, cmd-06 `867 passed, 3 warnings in 33.65s`, ...), the
  overall 0, and start/end I/tree/clean-0 are the qualification; NO G1
  rerun is required or performed on metadata alone.

### G2 FULL unfiltered backend integration (fresh, complete) at I

- Exact unfiltered command in the isolated context (section 5.4):
  `uv run --frozen pytest services/backend/tests/integration -rA --tb=short`
  with `PGHOST=127.0.0.1 PGPORT=5432 PGUSER=postgres
  PGPASSWORD=qualification-admin PGDATABASE=qualification` inside the owned
  netns; worktree I mounted at the same path; immediate child exit captured as
  `G2_CHILD_EXIT`.
- Launch provenance `/tmp/oap-083-5-e/g2-full-24a/launch.log` (source
  HEAD/tree/dirty at start, runner base image ID, PG container ID/created/
  empty port bindings, runner container ID) and live provenance
  `/tmp/oap-083-5-e/g2-full-24a/live-provenance.json` (runner/PG state,
  in-runner pytest PID+argv, no credentials).
- RESULT: **QUALIFIED at I.** collected 347 — **347 passed, 0 failed / 0
  error / 0 skipped, in 3688.19s (1:01:28), `G2_CHILD_EXIT=0`**; start
  2026-10-25T17:21:44Z.062, end 18:23:16Z.822. Source identity identical at
  start and end (HEAD `24a4333…` / tree `e59de814…`, dirty 0). Final log
  `/tmp/oap-083-5-e/g2-full-24a/g2-full-24a-run1.log` (SHA-256
  `e84be97bbc31ca63bec5aeddab107c062407f736abbb27e2e84e8acb3698ef1a`),
  runner `6a48c3ec…` terminal ExitCode=0 (FinishedAt 18:23:16.825Z), live
  provenance recorded terminal. Root independent qualification:
  `strategic-24a-FULL347-and-RC7-independent-review.json` (23 named
  criterion cases). Named case identification from the `-rA` log: section
  9.7 — incl. BOTH coherent RC7 tests (retained-v2-FIRST + SEPARATE genuine
  v1-only 075 restore/re-upgrade) actually PASSED in this run; no redundant
  standalone RC7 rerun is required. The earlier c-I5 interrupted G2
  (native 143, cause UNKNOWN) and d 43cd G2 (invalid 55443 context, cause
  now measured in section 5) remain distinct preserved failures, never
  relabelled.

### G3 WHOLE (sh tools/compose/smoke.sh slaif0835) at I

- **QUALIFIED at I.** Exact literal command `sh tools/compose/smoke.sh
  slaif0835` in the clean immutable worktree, unique attempt directory
  `/tmp/oap-083-5-e/final-I-24a-g3-whole/`, log `g3-whole-24a-run1.log`
  (final 65318 B, SHA-256
  `94517f6fe1c79ca7881cae8b85c300fb9d64acda73e5f11010bb2987e16e247f` —
  root-independent receipt
  `strategic-24a-WHOLE0835-independent-review.json`),
  `G3_WHOLE_NATIVE_EXIT=0` (immediate child exit; setsid-detached; node
  v24.22.0/pnpm 11.22.0 on PATH), 2026-10-25T18:28:37Z.167 ->
  18:47:30Z.978 (18 min 53 s). Source identity identical at start and end
  (HEAD `24a4333…` / tree `e59de814…`, dirty 0; host clean). Fresh stack
  from source: `compose-policy: OK`, down --volumes + build --pull +
  up --wait (all six images built from the I source — including the PG image
  with the e-repaired libcurl 8.23.0-r0 overlay, whose in-build
  installed-version assertions passed). Edge configuration checks: nginx
  `-t` `Syntax OK` and the existing `apachectl -t` `Syntax OK` — both are
  edge CONFIGURATION checks; the actual HTTP/browser traffic in this run is
  the NGINX edge (no live Apache HTTP parity is claimed).
- `compose-e2e: OK projects=19` — setup=1, governance=1, preview=1,
  preview-filtering=1, stable-devices=6 (desktop chromium/firefox/webkit,
  tablet, mobile chromium/webkit), agent-sessions=2, agent-workspace-puck=2,
  freeze-review-snapshot=1, review-surface=1, accept-lifecycle=1,
  discard-lifecycle=1, media-publication=1, artifacts=disabled. 40
  browser-e2e contracts PASSED, 0 FAILED.
- ALL6 meaningful frozen targets: `frozen-review-parity-six-stable-pairings`
  PASSED `stage=phase=cleanup action=close elapsed=130830ms` — all six
  stable pairings inside the preserved 600s ceiling (the bS timeout did not
  recur; stage marker honestly scoped as stage-entry cumulative elapsed, not
  per-phase wall history). This contract also executes the actual deployed-
  worker BOTH hashes (spec 1930-2002: real Agent IMAGE TINY_PNG + DOCUMENT
  PDF uploads, real browser run 202/QUEUED + quota 429, workerPng/workerPdf
  sha256 == upload digests + sizeBytes + type) and the terminal BOTH bytes
  (spec 2561-2615: frozen bytes byte-identical through terminal discard),
  plus the RC3 W2 publication block (spec 2262-2562).
- D2 E2E text execution: `accept-lifecycle` project PASSED including
  `negative: digest mismatch and agent capability are uniform denials;
  drift removes the control` — the strict new clause "acceptance is blocked.
  The frozen review remains visible." rendered in the live browser (the
  current execution of the D2 E2E text; G1 CMD 24 pnpm test is unit-surface
  only, section 9.5).
- `media-publication` PASSED (`media-publication-core-human-agent-preview-
  finalize-public-hostile`); `media-e2e: OK edge=nginx upload=validated
  private-read=byte-identical finalization=public-read=byte-identical
  immutable-cache=verified` — private BOTH IMAGE+DOCUMENT bytes verified
  end to end.
- Public acceptance: `public-agent-news-edge: OK` (exact listing, hostile
  uuid-token-flight-free html, canonical isolation byte-identical),
  `public-agent-component-loop: OK`, `public-agent-acceptance: OK` (full
  acceptance proof incl. `openapi=exact` — the actual generated Agent
  OpenAPI zero-diff inside the WHOLE), `public-agent-restart: OK` /
  `-audit: OK rows=3`, `human-editor-envelope: OK count=9`,
  `governance-e2e: OK devices=6 users=4`.
- Post-e2e security predicates ALL OK: `edge-header-policy: OK page/api/404
  request-id-count=1 request-id-format=32hex csp-count=1`, `edge-body-limit:
  OK media=route-allowance non-media=413 global=1MiB`, `database-login-policy:
  OK public-connect=denied exact-roles=11 direct-default-owner-drift=none
  unrelated-connect=denied`, `secret-file-policy: OK`, render/render-
  preview/render-auth/browser-signing secret policies `OK files=1 mode=0400
  owner=10001`, `browser-artifact-root-policy: OK retained-files=24
  retained-pairs=12 freeze-run=CANCELLED:0/1 fixture-map=fixed12plus-state-
  bound-freeze mode=0600 owner=10001` (the state-bound finite fixture
  contract, smoke.sh:759-772, exercised for real on a fresh volume: the
  unique `082 E2E freeze %` run reached terminal CANCELLED, so the bound
  optional contributed 0/1 and the exact fixed-12 expectation N=24 /
  screenshot=3 matched; the COMPLETED branch remains validated by the
  live-SQL + dry-run matrix at c-I5, §6d history),
  `browser-artifact-runtime-policy: OK files=36 retained=24 new=12 mode=0600
  links=1 credentials=absent`, `browser-artifact-revoked: OK status=401
  bytes=absent`, `browser-artifact-outage: OK status=503 canonical=200
  bytes=absent`, `browser-artifact-recovery: OK byte-identical`,
  `browser-worker-restart: OK durable-dispatch-artifacts=retained`,
  `browser-artifact-public: OK runs=2 artifacts=6 bytes=verified`,
  `control-readiness-fixture: OK mount=isolated identity=exact failures=6
  recovery=clean`, `governance-restart: OK site=archived membership=inactive
  domain=primary fixtures=retained setup=closed`, packaging unit suite
  (`python -m unittest discover -s tests/packaging`) `Ran 49 tests in 0.460s`
  OK (the 38 subtests are counted internally by unittest), and final
  `compose-smoke: OK`.
- Both edge headers verified (nginx public edge in all e2e/acceptance phases;
  the 404 + header policy asserted against the edge). No assertion weakened;
  no unknown console error occurred. Prior mixed/interrupted attempts (d
  section 7) remain failed history, never relabelled.

### G4 generated Agent OpenAPI zero-diff at I

- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`
  at I: **QUALIFIED** — `component-catalog: OK` + `agent-openapi: OK
  contracts/openapi/agent-v1.json`, actual child 0 (G4_START
  2026-10-25T17:51:05Z, unique log `/tmp/oap-083-5-e/final-I-24a-g4/openapi-check-24a.log`; module
  argv + immediate child exit recorded; no command header is claimed inside
  the log — the call/output supplies the argv). Honest attempt history:
  attempt 1 FAILED (node missing on PATH, `FileNotFoundError: 'node'` in the
  component-catalog check) and is preserved as
  `openapi-check-24a-attempt1-node-missing.log`; the final attempt uses a
  unique filename (c-era lesson applied).

### G5 fresh local ALL6 six-image at I

- **QUALIFIED at I.** Exact command
  `GITHUB_SHA=24a4333569be6f2201f94c07be56d702cb1a33da sh
  tools/supply_chain/run.sh /tmp/oap-083-5-e/final-I-24a-g5-all6/evidence-24a-run1`
  in the clean immutable worktree (unique attempt directory, setsid-detached,
  node v24.22.0/pnpm 11.22.0/uv 0.12.5 on PATH): 2026-10-25T18:49:30Z.656 ->
  19:17:41Z.916 (28 min 11 s), `G5_PIPELINE_NATIVE_EXIT=0` (immediate child
  exit), log `g5-all6-24a-run1.log` (SHA-256
  `72ad0a980a037ebe18d88d36e256efbcdf459d9afa659500ac9dc3e3792ab2c1`).
  Source identity identical at start and end (HEAD `24a4333…` / tree
  `e59de814…`, dirty 0; host clean).
- Pipeline: `supply-chain-policy: OK`, `dependency-inventory: OK
  python=44 node=254`, `third-party-notices: OK components=298`,
  `reproducibility: OK python-artifacts=2 next-build-id=08b75e387e59741e5475d141d3ab03f5
  browser-output=source-contract` (every image built TWICE, normalized
  package/app-file equality; raw OCI image IDs differ honestly),
  `supply-chain-evidence: OK images=6 critical=0 high=19`,
  `supply-chain-evidence-checksum: OK` (53 checksums / 54 files),
  `supply-chain-gate: OK`. The six images were built from the I source with
  `--pull --no-cache` + pinned SOURCE_DATE_EPOCH/SLAIF_IMAGE_CREATED and
  `SLAIF_IMAGE_REVISION=24a43335…` (evidence `revision` bound to literal I).
- Scans (Grype v0.117.0/b5fa92bb + Syft v1.51.0/2293641e, fresh v6.1.10
  database built 2026-10-25T06:27:34Z checksum `4bdb4292…`,
  age 12.83h): all six images `critical_findings: []` /
  `unexcepted_critical: 0`; `exception_counts: {license: 0,
  vulnerability: 0}` (EMPTY — no exceptions); severity totals High 19 /
  Medium 1857 / Low 157 / Unknown 6 / Negligible 18. The 19 High are the full
  six-tuple inventory (image, id, pkg, version, type, purl) inherited from
  the prior FAILED census/attempt (candidate ea586641 / artifact
  12593246129: backend 1 zlib, browser-worker 4, postgres 7, web 7) with 0
  new — review inventory, NOT exceptions, and not a comparison against a
  prior successful bundle.
- Original 31 Critical matches (30 distinct IDs; CVE-2026-111497 counted
  twice for nginx + postgres `brotli-libs 1.2.0-r0`): the ORIGINAL same-ID+
  same-package matches are ABSENT at ANY severity in all six fresh scans
  (measured above from the census
  `/tmp/oap-083-5-b/candidate-ea586641-independent-all-six-critical-census.
  json`). Honest residual note: the same CVE-2026-111497 ID still matches at
  MEDIUM severity in DIFFERENT packages on the Debian-based images (apache
  `libbrotli1 1.1.0-2build2`, browser-worker `libbrotli1 1.1.0-2build2` +
  `nodejs 24.18.1-1nodesource1`, fix state not-fixed) — base-image Medium
  inventory, not the original Alpine brotli-libs Critical matches.
- Browser identity (measured runtime, scan-bound): Google Chrome for Testing
  `156.0.8078.47`, executable
  `/ms-playwright/chromium-1706539/chrome-linux64/chrome` SHA-256
  `230f0db8c5086182f46c59c867c0d461eb525d6552dfad226ea6b4d9ec249db2`,
  source archive SHA-256 `e6c94490f0b6b337225aeb2d2a5034858516b7017356980ba94f5176d8774a50`,
  browser-worker image `sha256:5ef40d70c468e3cfa0fbcbf69b46ad95945e208df821b652624344a500ec2457`.
  PG image carries the e-repaired `libcurl=8.23.0-r0` overlay (in-build
  assertion passed); NGINX `1.30.6-alpine3.24`; web Next `16.4.1` with the
  ignored-Sharp boundary intact (no Sharp/libvips/optimizer); foundation
  exact frozen PyPI `agent-cow-postgresql 0.2.0`.
- Root independent qualification: `strategic-24a-LOCAL6-independent-review.
  json` (53 checksums/54 files verified; all 6 raw Critical 0 / ignored 0;
  index counts agree; 19 High full tuples inherited / 0 new; original 31
  same ID+pkg absent ANY severity; 6 normalized 2-build package/app-file
  equal; Chrome identity + SPDX containment + Grype input bound to source
  I; PG libcurl 8.23 / NGINX 1.30.6 / Next 16.4.1 / no-Sharp / foundation
  0.2.0 verified). The CI artifact (section 8) is CI-scoped evidence and is
  NOT substituted for this fresh local ALL6; the c-J2 local bundle is a
  distinct earlier identity, never relabelled.

### RC7 coherent retained-v2-first / separate v1-only restore at I

- **Satisfied by the fresh full G2 at I** (the order's RC7 cases live inside
  the unfiltered integration directory): `fts::test_076_001_round_trip_
  retained_v2_and_exact_restore` (retained-v2 downgrade refusal FIRST with
  zero effects, migration AND bootstrap operator path refused BEFORE effects;
  catalog/owner/search_path/direct+effective ACLs/readiness/COW/revision/
  rows asserted) and `fts::test_075_001_v1_only_downgrade_roundtrip_
  disposable` (SEPARATE genuine v1-only disposable DB: exact 075 restore
  incl. OID, byte-identical v1 row, working constructors, re-upgrade
  reproduces head), plus baseline `fts::test_075_001_round_trip_exact_
  restore_and_locked_materializer` — all three PASSED in the fresh 347/347
  run (section 9.7; actual counts/exits: 347 passed, G2_CHILD_EXIT=0, 3688.19s).
  Fresh at I; b/c scoped history not relabelled; `docs/OPERATIONS.md:208-228`
  operator truth unchanged at I.

## 7. Owned runtime state at publication

- Owned isolated qualification context: PG `slaif-pg-e-186`
  (`447cf85041…`, postgres:18.6-alpine3.23@`697c180d…`, named volume
  `slaif-pg-e-186-data`, `HostConfig.PortBindings={}` — NO host port) remains
  as recorded at publication (disposable; the only long-lived owned e
  container). The G2 runner `slaif-runner-e` (`6a48c3ec…`) is terminal
  (ExitCode=0) and REMOVED after final log capture. All G3/G5 pipeline
  containers are temporary and removed by their own cleanup; the G3
  `slaif0835` compose stack is fully down (smoke final cleanup, verified
  zero `slaif0835*` containers after G3).
- No owned e container ever bound a host port. Host shared cluster
  `slaif-integration-pg-0833b` (127.0.0.1:5432) and all other projects'
  containers/DBs/roles/connections were never touched by e.
- The decommissioned 55443 cluster (`451c65f8…`) leftover metadata is
  preserved (section 5.3); its disposable DB/roles remain in the
  DECOMMISSIONED volume only (volume removed with the container) — no foreign
  objects.
- Exact owned state verified at the publication instant (2026-10-25 ~19:2x
  Z): LIVE owned containers = `slaif-pg-e-186` only (Up, `5432/tcp` exposed
  inside its own network namespace, `HostConfig.PortBindings={}` — no host
  port). TERMINATED/REMOVED owned containers: G2 runner `slaif-runner-e`
  (6a48c3ec, ExitCode 0, removed after final log capture); the entire G3
  `slaif0835` compose stack (down by smoke final cleanup, verified zero
  `slaif0835*` containers); all G5 pipeline temporary containers (syft/grype
  runs, rootfs exports, build scratch — removed by run.sh cleanup, verified
  zero `slaif-supply*/syft*/grype*` containers). TERMINATED owned
  processes: G2 pytest/uv (runner terminal), G3 smoke (child 0), G5
  pipeline (child 0); no owned runner/process remains live. No foreign
  process is claimed or disturbed; other projects' containers
  (`slaif-integration-pg-0833b`, `slaif-054a-pg17`, asset-reservation, etc.)
  untouched.

## 8. GitHub CI at literal I 24a4333 (actual runs/jobs)

- CI run `40215464740` (pull_request, head 24a4333, created 17:14:04Z,
  TERMINAL `completed`/`success` 17:31:28Z). All 25 jobs COMPLETED/SUCCESS
  (job IDs are the actual GitHub job databaseIds):

  | Job (actual name) | Job ID | Conclusion |
  | --- | --- | --- |
  | Compose and edge packaging | 121235536010 | success |
  | Python 3.12 quality and package | 121235536130 | success |
  | Python 3.13 quality and package | 121235536270 | success |
  | Python 3.14 quality and package | 121235536133 | success |
  | Node contracts | 121235536189 | success |
  | Repository policy | 121235536196 | success |
  | Dependency review | 121235536207 | success |
  | Markdown | 121235536367 | success |
  | Mermaid | 121235536364 | success |
  | Supply-chain evidence | 121235536185 | success |
  | Foundation PG Group A PostgreSQL 14 | 121235536557 | success |
  | Foundation PG Group A PostgreSQL 15 | 121235536416 | success |
  | Foundation PG Group A PostgreSQL 16 | 121235536328 | success |
  | Foundation PG Group A PostgreSQL 17 | 121235536335 | success |
  | Foundation PG Group A PostgreSQL 18 | 121235536143 | success |
  | Foundation PG Group B PostgreSQL 14 | 121235536238 | success |
  | Foundation PG Group B PostgreSQL 15 | 121235536407 | success |
  | Foundation PG Group B PostgreSQL 16 | 121235536257 | success |
  | Foundation PG Group B PostgreSQL 17 | 121235536345 | success |
  | Foundation PG Group B PostgreSQL 18 | 121235536566 | success |
  | Foundation PostgreSQL 14 (aggregator) | 121238316353 | success |
  | Foundation PostgreSQL 15 (aggregator) | 121238316343 | success |
  | Foundation PostgreSQL 16 (aggregator) | 121238316317 | success |
  | Foundation PostgreSQL 17 (aggregator) | 121238316316 | success |
  | Foundation PostgreSQL 18 (aggregator) | 121238316366 | success |

  The 10 internal PG children (Group A/B x PG 14..18) each ran their exact
  split commands (A = 4+81=85 selected, B = 24+9+12=45 selected) on their
  own disposable PostgreSQL services; the five aggregator names
  `Foundation PostgreSQL 14..18` are the required-check names (fail-closed
  over both groups). Together with the 10 other required names above this is
  the original 20 required names + 10 internal PG children at CURRENT I.
  No job used continue-on-error/retries; no unchanged-head rerun occurred.
- CodeQL run `40215464714`: TERMINAL `completed`/`success` — all 4 workflow
  jobs SUCCESS (Detect supported languages 121235536022, Analyze (python)
  121235565158, Analyze (javascript-typescript) 121235565167, Analyze
  (actions) 121235565285) plus the app CodeQL check SUCCESS (root observed);
  the c-era legacy-067-ID high alert did not recur (section 9.4).
- Supply-chain artifact at I: `12607746889` (8945684B zip, SHA-256
  `b7ef1e59a688dbb2bca0fe3271d2140aab790bb8c6dcd83829e5ec5b1e503064`),
  actual CI merge-commit M `8b7d557395562f280e1c66f2916ff21def6f136f`
  (parents main 4bf74fdc + I 24a4333; remote M tree `e59d...` == I tree
  `e59de814...`). Root independent review: 53/53 checksums, all 6 raw scans
  0 Critical / 0 exceptions, 19 High full tuples inherited from the prior
  FAILED census (no new, 0 exceptions), original 31 same ID+pkg absent at any
  severity, Chrome SPDX contains file SHA `230f0db8...`, PG image libcurl
  8.23 present (receipt
  `tmp0835e/strategic-24a-artifact-12607746889-independent-six-image-review.json`).
  SCOPE: CI-only, NOT fresh local ALL6 / WHOLE / FULL / final-S acceptance.
- Current S (final) check table: recorded at publication exactly as observed
  after the final report-only S push — all 20 required names + 10 internal
  PG children must be COMPLETED/SUCCESS at CURRENT S (strict 20934043 / apps
  15368+57789; no bypass); missing/neutral/skipped/pending/failed/cancelled
  never qualify. If not terminal at the publication instant, the table
  honestly records PENDING; this report is NEVER amended after S to fill
  future-S results (the order: SELF checks may honestly be pending at
  publication; root independently waits).

## 9. Complete inherited evidence index (a/b/c/d -> e, criterion by criterion)

Scope rule applied throughout: each entry cites the ORIGINAL proof (round,
concrete source/test names with line anchors at 24a where the cited file is
the proof surface, log file, source SHA, native result as recorded in the
cited round's immutable report) and its state at e. Line anchors are from the
clean 24a tree (`e59de814afd7a334f9e37c482961fc4b1962a7c6`), verified at
drafting time; the secondary READONLY criterion index
(`/tmp/oap-083-5-e/pane21-criterion-source-index.md`, audited head 24a,
2026-10-25T18:17:27Z) corroborates the name/anchor map — the index alone is
not runtime success or acceptance. "Re-verified at 24a" means actually
re-executed in this round at literal I `24a4333` (G1/G2/G3/G4/G5/CI as
marked); "carried" means the original scoped proof stands as immutable
history and is NOT relabelled as fresh. The fresh full G2 at I ran with
`-rA`, so its final log identifies each named case by PASSED line (section
9.7); the fresh G3 WHOLE at I supplies the actual six-target / private BOTH
bytes / W2 / terminal artifacts (section 6, G3). Local final gates run at the
LITERAL I; only the current-S CI check table belongs to the final report-only
S. Acceptance/scope authority for any gap is ROOT's (per the R2 adjudication
record `workorders/083-5e-R2-sibling-binding-audit-adjudication-2026-10-25.md`);
this section indexes existing proof only and waives nothing.

Abbreviations for anchors at 24a: `fts` =
`services/backend/tests/integration/test_freeze_review_snapshot.py`;
`par` = `services/backend/tests/integration/test_frozen_review_parity.py`;
`rha` = `services/backend/tests/integration/test_real_human_accept.py`;
`spec` = `tests/e2e/frozen-review-parity.spec.ts`; `med` =
`tests/e2e/media-publication.spec.ts`; `076` =
`services/backend/src/slaif_agent_site/db/alembic/versions/076_001_faithful_frozen_review.py`;
`proj` = `services/backend/src/slaif_agent_site/render_api/projection.py`;
`fs` = `services/backend/src/slaif_agent_site/render_api/frozen_source.py`.

### 9.1 a-order R1-R9 (a-report §5, oap/reports/083-5-a-faithful-frozen-review.md)

- R1 (complete domain inventory + every consumed input): inventory materialized
  in `review_worker/snapshot.py` (v2 capture) and the 076 materializer (`076`);
  the RC1 family assertions at `fts:6888+` (FAMILY_MAP at `fts:8452+`) assert
  the exact retained key set `{state_version, workspace_id, site_id, site,
  base_site_revision, operation_watermark, workspace_versions, locales, theme,
  regions, navigation, redirects, pages, page_compositions, content,
  proposals, media_inventory, media}`. Original proof: a-I `565c99c` fresh
  unfiltered `full-integration-final4.log` (329 passed / 4244.32s /
  PYTEST_EXIT:0), incl. `fts::test_freeze_lifecycle_worker_snapshot` (419;
  real control enqueue + real worker claim + real run, v2 payload with the
  complete family set) and `fts::test_review_endpoint_frozen_read_media_urls_and_role_denials`
  (4352; retained 23-digit fraction `0.10000000000000000000001` survives
  JSONB -> exact-number round trip with stored-digest equality asserted);
  20/20 CI SUCCESS at the a head (run 39243413638 attempt 2 + CodeQL
  39243413388). Carried; re-verified at 24a by G1 CMD 05/06 (mypy 0;
  unit/repository pytest 0) and fresh G2 -rA (9.7).
- R2 (trusted SQL materialization + Python validation; sibling binding):
  `proj` `review()` exact-number path (2208-2232) + `fs` admission (digest
  over canonical text, normalized_state identity, workspace_versions pins,
  media_references list<->dict, browser_evidence). Original proof:
  `fts::test_rc1_public_agent_and_editor_capture_retained_families` (6888)
  and `fts::test_rc1_numeric_approval_composition_only_workspace` (9274) —
  b-era focused `rc1-focused-run18.log` @ `866830bbf0edc8a4` 1 PASS 18.57s
  NATIVE_EXIT=0 (original run18 2 PASS 35.77s pre-md5-fix preserved); the
  R2 sibling-binding audit (229L) + root adjudication: the allowed form is
  immutable ID/row/write binding via trusted same-workspace COMPLETED emitter
  plus membership SQL, terminal fact guards, and 14-column retention/current
  positive proof (NOT whole-row digest); audit G1/G2 are
  completion-boundary test gaps with trusted emitter/read/approval gates (not
  automatic product defects); audit G4 lacks a real-SQL browser negative —
  limitation reported honestly, no waiver. Re-verified at 24a by fresh G2
  -rA (both RC1 tests PASSED, 9.7) and G1 CMD 05/06. Numeric clarification
  (recorded in b workorders): raw payload/digest exact across
  projection+approval; the separate derived int/float render copy preserves
  live behavior — no new public precision claim.
- R3 (trusted projection reuse for canonical/preview/review; six-target
  fidelity): `proj` single `_query` engine (1909) with canonical(2118)/
  preview(2141)/review(2154); `fs` shared ports (page_effective_route 2721,
  resolve_page_route 2792, _internal_target_exists 2867,
  navigation_resolved_items 2907, new_route_memo 2533). Original proof:
  `par::test_live_sql_common_port_route_navigation_differential` (234) +
  real-PG differential catalog; b RC2 focused `parity-focused-run7.log` @
  `649e999f439b2408` 2 PASS 41.41s NATIVE_EXIT=0 (G10/G11); six-target public
  E2E `spec` (matrix `spec:66-74`, six config device pairings). Re-verified at
  24a: the differential + real-SQL cases PASSED in fresh G2 -rA (9.7); the
  unit surface via G1 CMD 24 (`pnpm test` 0 — web + browser-worker suites);
  the six-target E2E execution is the fresh G3 WHOLE at I (section 6).
- R4 (trusted route normalization, hierarchy/dynamic {slug}, locale):
  shared `_query` assembly (`proj` 1985-2115); dynamic {slug} locale
  switching: `proj::_locale_switcher` (1209) is called with
  `current_route=route` (2005) — the CONCRETE matched route — and
  `switcher_href` link construction lives in the shared port + web switcher
  hrefs. Original proof: a-report §5-B E2E (static/list/detail routes,
  multiple items/locales, selected-locale + default fallback, query
  sort/filter/projection/pagination, related items, navigation/redirect/
  switcher, regions/media, non-default page-style precedence across all six
  stable targets; assertions inspect content/order/route parameters and
  computed CSS) at the a head; `par::test_common_consumer_collection_binding_
  variants` (831; six List/Grid/Search/Filter/Detail/RelatedItems variants,
  locale selection + default fallback, COLLATE "C" filter_fields). Re-verified
  at 24a: binding-variant case PASSED in fresh G2 -rA; E2E half in fresh G3.
- R5 (frozen projection reads the authorized stored snapshot; immutable
  drift): `proj::review()` (2154-2262; `slaif_review_projection_authorize`
  sole SQL authority, preview_pool, FOR SHARE, `parse_snapshot_text`,
  FrozenRenderSurface, `SiteContext._from_frozen` sealed) + `fs` zero-SQL
  frozen fetchers (3330-3549) + web `sites/review-page.ts`
  (fetchReviewDocument + siteLocalPath, captured-key authority, foreign key
  refused). Original proof: `fts::test_frozen_drift_invariance_offline_live_and_discard_repeat`
  (4790) — STATIC-ASGI scope per its docstring (projection JSON + 18 sealed
  live reads + terminal discard repeat; the rendered-output half lives in
  `spec` RC3 block 2262-2562); `fts::test_076_001_round_trip_retained_v2_and_exact_restore`
  (2574) frozen-read sections. Re-verified at 24a: 4790 + 2574 PASSED in
  fresh G2 -rA; rendered half in fresh G3 WHOLE.
- R6 (typed media/document validation, confined worker private bytes):
  `fts::test_rc1_public_agent_and_editor_capture_retained_families` (6888;
  12 uploads: 2 component-referenced, 9 field-only, 1 unrelated private;
  selected closure asserted) + `fts::test_freeze_media_reference_row_tamper_matrix`
  (10020) + `par::test_sibling_mismatch_recomputed_digest_admission_refusal`
  (3806). Original proof: a-report §5-R6 + b RC4 `test_media_service.py::test_
  private_media_bytes_human_preview_bound_worker_frozen_review` (731 at 24a)
  — `media-focused-run1.log` 1 PASS 138.22s NATIVE_EXIT=0 (root independently
  verified the native event at 2026-10-25T02:59:37.220Z; ASGI-labeled media
  integration tests — manual sign/claim — are SQL/HTTP negative proof, NOT a
  deployed-worker substitution). Re-verified at 24a: 731 + 10020 + 3806
  PASSED in fresh G2 -rA; actual deployed-worker BOTH bytes in fresh G3
  (spec 1930-2002) and terminal BOTH bytes (spec 2561-2615).
- R7 (snapshot state/catalog/renderer/composition validation + legacy
  compatibility + hostile no-effects): `fs` admission version gates;
  `fts::test_v1_stored_workflow_read_refusal_discard_recreation` (5552;
  genuine v1 bytes via real 075 materializer + verbatim base 075 builder,
  byte-identical v1 through upgrade, 076 gate refuses frozen render, real
  accept refused with stable code BEFORE any effect, discard + fresh
  recreation); web legacy view `sites/review-page.ts:253-262` (stored
  state_version single selector; v2 refusal cannot fall back; unknown
  refused) + v1 reader `sites/review-projection.ts:905`; hostile no-effects
  `fts:9784/9908/10020`. Original proof: a-report §5-R7 + b RC6
  `hostile-run4.log` @ `1ac8db18e72613fe` 1 PASS 20.30s NATIVE_EXIT=0 (E-D3
  media-reference-row tamper full matrix), `hostile-run5.log` @
  `fcf4ffaa7843ad2a` 1 PASS 13.77s NATIVE_EXIT=0 (G13 stored-digest
  co-tamper refusal), `hostile-run6.log` second launch 1 PASS 13.62s
  NATIVE_EXIT=0 (first launch's missing-exit caveat preserved). Re-verified
  at 24a: 5552 + 10020 + 9784 + 9908 PASSED in fresh G2 -rA (9.7).
- R8 (coherent freeze revision, workspace/advisory/site lock, admitted-work
  bounds, preserved lifecycle): `fs` MAX_NAVIGATION_ITEMS_PER_GROUP +
  `_check_family_caps` + MAX_CANDIDATES; `par::test_common_port_admitted_work_
  bounds` (1124; 256-item single group, real 255/256/257 admission seam),
  `par::test_family_cap_gate_refuses_before_group_allocation` (1654),
  `par::test_media_cross_check_runs_after_cap_gate` (1906),
  `par::test_rc8_captured_chain_raw_depth_and_byte_budget_wiring` (4198;
  valid 16-edge/17-node chain, raw depth 7/8 byte-exact, depth-9 refusal at
  the real materializer gate, N-1/N/N+1 strict < 8 MiB production constant at
  4593, per-node normalized type/schema/parent/slot/order/props vs raw facts
  4477-4502); lifecycle `fts::test_concurrent_claim_and_stale_recovery` (340),
  `test_lock_serialization_and_r4_shared_lock` (693),
  `test_first_touch_conflict_baseline_survives_freeze` (3955),
  `test_freeze_site_lock_failure_rollback_no_leaked_lock` (4151),
  `test_forced_validation_failure_leaves_freezing` (574). Original proof:
  a-report §5-R8 + b RC8 `rc8-capture-focused-run5.log` @ `a82be261aca7c697`
  1 PASS 39.03s NATIVE_EXIT=0 (run3 pad / run4 polymorphic-SQL failures
  preserved as history); secondary 8 MiB audit
  `rc8-8mib-audit-primary-review-2026-10-25.md` (corrected envelope verified,
  lawful upper < 8 MiB; guard unreachable from constraint-compliant inputs as
  defense-in-depth; F1/F2 reachability terms kept OPEN). The R3 audit + root
  source review of 24a confirm the per-node normalized assertions and the
  strict budget inequality already exist at I — no product repair ordered.
  Re-verified at 24a: all named cases PASSED in fresh G2 -rA (9.7).
- R9 (migration 076_001 + coherent rollback + truthful operator
  instructions): `076` (only migration; upgrade from 075 exact);
  `fts::test_075_001_round_trip_exact_restore_and_locked_materializer` (1649),
  `fts::test_076_001_round_trip_retained_v2_and_exact_restore` (2574;
  retained-v2 downgrade refusal FIRST, no effects; exact 075 restoration with
  a SEPARATE genuine v1-only fixture; constructor/pin restore identity;
  effective-role + ACL proof), `fts::test_075_001_v1_only_downgrade_roundtrip_disposable`
  (3065; SEPARATE genuine v1-only disposable DB: 075 restore exact catalog
  incl. OID, byte-identical v1 row, working constructors, re-upgrade
  reproduces head); `docs/OPERATIONS.md:208-228` corrected downgrade-refusal
  operator path; `test_database_bootstrap.py` retained-v2 preflight refusal
  with unchanged readiness/COW/revision/catalog/snapshot bytes;
  `test_foundation_contract.py` pins foundation exact frozen PyPI 0.2.0.
  Original proof: a-report §5-R9; b RC7 scoped history only (NOT fresh final
  proof — section 3.7). FRESH at I 24a: both coherent RC7 tests PASSED in
  the fresh full G2 -rA (9.7); root receipt
  `strategic-24a-FULL347-and-RC7-independent-review.json` (23 named
  criterion cases) — no redundant standalone RC7 rerun is required.

### 9.2 a-order A-F (a-report §5)

- A (new-format capture: real Agent AND human Editor mutations create
  well-formed snapshots): `fts::test_rc1_public_agent_and_editor_capture_
  retained_families` (6888; docstring 6890-6935: actual public AGENT HTTP —
  2 content types/8+5 fields incl. media MULTI/localized/base shapes, 3+2
  items incl. DRAFT + exact raw base numbers, en/sl-SI translations,
  relations, views with filter/sort/projection/pagination, 4 pages +
  public-API deletion tombstone, 7+ components, non-default raw page style,
  theme, locale, redirect, nav, region variant, 12 media uploads; actual
  authorized human EDITOR HTTP via 069_001 envelope; REAL freeze worker on
  the SAME candidate; proposals retained non-executed with no-effects oracles;
  honest fixture-setup labeling) + numeric sibling `fts:9274`. Original
  proof: a-report §5-A at the a head + b RC1 focused (above). Re-verified at
  24a: fresh G2 -rA (both PASSED, 9.7); fresh G3 at I re-runs the public
  capture phases.
- B (public NGINX E2E: active preview vs immutable review, ALL6 engines,
  controls, locale clicks, hydrated transport): `spec::frozen-review-parity-
  six-stable-pairings` (1460; Phase A active preview / Phase B immutable
  review, per engine/target+route fingerprint equality, media URL
  normalization, byte-identical frozen bytes, run-unique site; the W1
  workspace editorial facts are made via REAL public Agent API — the public-
  Agent claim is scoped to W1 editorial-actor changes. The FINAL canonical
  block installs a bounded run-unique canonical INITIAL fixture through the
  trusted psql setup authority (`seedCanonicalFixture`, spec:1096, called at
  2661): honest label per the source docstring — test-data setup, NOT online
  publication evidence; no workspace is created, nothing frozen or accepted,
  the site revision does not move, and no W1 private asset is referenced.
  The canonical six-target render/controls/locale proof (canonicalPhase,
  spec:1391, called at 2670, after the real W1 terminal discard + pending
  cleanup) uses that honestly seeded canonical fixture; NO generic
  page/model DML publication is claimed from canonicalPhase. The W2
  unrelated publication remains the real qualified public theme path
  (spec:2262+); 600s budget with measured phase annotation) +
  `tests/e2e/freeze-review-snapshot.spec.ts` (+246/−1 at a) +
  `tests/e2e/review-surface.spec.ts` (+105/−4 at a) + `apps/web/tests/
  review-surface.test.mjs` (real v2 client against the actual read-model
  document; v1 facts honest; unknown stored versions refused). Original
  proof: a-report §6 attempt 7 final (clean a head, base-allowed name
  `slaif071smoke`, 2026-10-19T10:56:46Z start, `compose-e2e: OK projects=19`
  — 39 browser contracts 0 failures incl. six stable devices —
  `public-agent-acceptance` OK, SMOKE_EXIT:0, log finalized 11:12:17Z;
  attempts 1-6 preserved as test-side/stale-expectation history) + b RC2
  `e2e-parity18-pass-evidence.log` (E2E_PARITY18_EXIT:0 at then-current
  source) + c §6c/§6d I/I2 routing + artifact-baseline repairs. Re-verified
  at 24a: fresh G3 WHOLE at I (section 6) is the current ALL6 proof.
- C (unrelated valid canonical publish coexists; freeze immutability):
  `fts::test_frozen_drift_invariance_offline_live_and_discard_repeat` (4790;
  static-ASGI scope — projection JSON + sealed live reads + terminal discard
  repeat; rendered-output half in `spec` RC3 block 2262-2562: W2
  create/capability/unrelated-theme publication/freeze/accept through the
  real qualified path, stored row bytes exact after W2 (spec 2426), retained
  controls after W2 (2491-2499), W1 pending nonempty-before-discard
  (2503+), terminal discard + repeat) + `rha::test_accept_worker_drift_zero_
  mutation` (1373). Re-verified at 24a: 4790 + 1373 PASSED in fresh G2 -rA;
  rendered half in fresh G3.
- D (counterfactuals: meaningful tests fail on captured-item omission/stub):
  `par::test_omission_stub_counterfactuals` (1987; reversible seams,
  FAIL-for-intended-reason per case, byte-identical restore, no contamination,
  case 9 frozen-side via real materializer + admission seam) + unit vectors
  `tests/backend/.../test_render_projection.py` (+899/−1 at a: bounded
  serializer exact N/N-1/N+1 dict 7/array 3/nested 15, raw depth 8/9,
  leaf 1/chain 17/18, 1001-digit numeric at the 8 MiB bound, float decode vs
  stdlib live-JSON reference, raw Decimal scale unmutated, route-memo
  total-work bounds, admission negatives, NULL-helper/final-guard depth
  paths), `test_snapshot_v2_canonical.py` (+222), `test_render_projection_
  media.py` (+219/−20: six-pin exactness, row-vs-payload identity, unique
  inventory/site/storage-key binding, malformed shapes all empty-result);
  the 076 materializer RAISEs `SNAPSHOT_VALIDATION_FAILED` at 23 sites and
  `fts::test_forced_validation_failure_leaves_freezing` (574) proves a forced
  validation failure leaves the workspace FREEZING (no partial completion).
  Original proof: a-report §5-D + b RC5 (a-round isolated-omission suite
  rc5-verify1..8 logs retained unchanged at b head; b hostile no-effects
  matrix extended the set). Re-verified at 24a: 1987 + 574 PASSED in fresh
  G2 -rA; unit vectors in every G1 CMD 06 run (0 at I).
- E (negative/security/lifecycle proof): `fts::test_freeze_endpoint_http_
  authorization_csrf_and_state_matrix` (828), `test_freeze_over_budget_
  content_types_refused_no_effects` (9784), `test_freeze_stale_catalog_
  schema_version_refused_no_effects` (9908), `test_freeze_media_reference_
  row_tamper_matrix` (10020), `test_v1_stored_workflow_read_refusal_discard_
  recreation` (5552), `test_review_endpoint_frozen_read_media_urls_and_role_
  denials` (4352), `test_two_workspace_revision_coherence_and_stale_refusal`
  (3284), `test_same_site_accept_freeze_serialization_both_orderings` (3563);
  `rha::test_reviewer_grant_matrix` (556), `test_control_accept_route_
  authority_matrix` (941), `test_accept_worker_stored_digest_cotamper_
  refused` (1779), `test_promote_workspace_retired` (1758); `med` hostile
  sections (cross-site byte read 1847+, corrupt/restart/denied contexts
  1957-2147); role/token/session negatives (unknown/revoked/expired/
  recency-failed sessions, cross-site and cross-workspace bindings, foreign
  digest/nonce/attempt, credential-shape 401 vs denial 404, no-touch
  last_seen_at equality). Original proof: a-report §5-E incl. the `fn3`
  frozen media gate actual-SQL matrix (PG14 + PG18, 43 unique count rows each
  — 3 declared positive / 40 negative — 0 mismatches, child psql exit 0;
  logs `fn3-probe-v3-corrected-pg14-first-independent-owned.log`,
  `fn3-probe-v3-corrected-pg18-first-independent-owned.log`) + b RC6 hostile
  runs (above). Re-verified at 24a: fresh G2 -rA re-runs the full
  integration negative matrix (9.7); E2E hostile/revoked contexts in fresh
  G3.
- F (required full gates: all31, fresh full integration, coherent RC7, whole
  Compose/edge/six-device, OpenAPI 0, six-image, honest reporting): this
  round's obligation is section 6 at literal I 24a4333 + section 8 CI at the
  final report-only S; status per gate in section 6. Format note per root
  review: a pointer to a prior round's COMPLETE report is NOT accepted as
  criterion evidence in place of the concrete source/test/log/hash/native
  results given above; the a-report's own §7.2 records no CI state at the a
  final S (PENDING at publication), and no round's COMPLETE status is cited
  here as acceptance.

### 9.3 b-order RC1-RC9 (b-report §5, oap/reports/083-5-b-qualify-faithful-frozen-review.md)

- RC1 (A/R1/R2 actual public capture + sibling binding): b scoped proof
  `rc1-focused-run18.log` @ `866830bbf0edc8a4` 1 PASS 18.57s NATIVE_EXIT=0
  (original run18 2 PASS 35.77s pre-md5-fix preserved) +
  `test_rc1_numeric_approval_composition_only_workspace` PASS in the same
  log; genuine Oct-25 current proof identified in the b-report correction
  set (public run5 `831cd2d3` native 0: BOTH worker hashes, all6
  canonical/preview/review, W2 + terminal 14-column invariance). Re-verified
  at 24a: fresh G2 -rA (both RC1 tests PASSED, 9.7) + fresh G3 public
  capture phases.
- RC2 (B/R3/R4 common consumer + six-target fidelity): b scoped proof
  `parity-focused-run7.log` @ `649e999f439b2408` 2 PASS 41.41s NATIVE_EXIT=0
  (G10 `par:3276`, G11 `par:3806`) + six-target E2E contract `spec` (see 9.2
  B). Re-verified at 24a: G10/G11 + differential (`par:234`) PASSED in fresh
  G2 -rA; six-target E2E in fresh G3.
- RC3 (C/R5 immutable drift + terminal rendering): b scoped proof (a-round
  qualified suite at the a head, 20/20 CI SUCCESS; drift/discard/
  unavailable-retrieval cases in `fts` roundtrip + terminal sections).
  Re-verified at 24a: `fts:4790` (static-ASGI half) PASSED in fresh G2 -rA;
  rendered half (W2 publication, stored row bytes, terminal discard repeat)
  in fresh G3 (`spec` 2262-2562, terminal BOTH bytes 2561-2615).
- RC4 (R6 confined worker private bytes — ACTUAL deployed worker): b scoped
  proof `media-focused-run1.log` 1 PASS 138.22s NATIVE_EXIT=0 (ASGI-labeled
  integration test, honestly scoped) + `spec:1930-2002` actual worker BOTH
  hashes (real public Agent IMAGE TINY_PNG + DOCUMENT makePdf uploads,
  content_hash asserted at upload; real browser preview run 202/QUEUED,
  quota 429 on the second request; COMPLETED wait; then boundMedia reads:
  workerPng sha256 == pngDigest + sizeBytes + image/png AND workerPdf
  sha256 == pdfDigest + sizeBytes + document — the actual deployed worker's
  byte reads) + frozen identical bytes after freeze + terminal discard
  (Phase B media byte-identity block + `fts:4790` sealed-read invariance).
  Re-verified at 24a: `med::test_private_media_bytes_human_preview_bound_
  worker_frozen_review` equivalent `test_media_service.py:731` PASSED in
  fresh G2 -rA; deployed-worker BOTH bytes + terminal BOTH bytes in fresh G3.
- RC5 (D counterfactuals): b scoped proof (a-round isolated-omission suite
  rc5-verify1..8 logs retained unchanged at b head; b hostile no-effects
  extended the set). Re-verified at 24a: `par:1987` + `fts:574` PASSED in
  fresh G2 -rA; unit counterfactual vectors in G1 CMD 06 (0 at I).
- RC6 (E/R7 stored legacy compatibility + hostile no-effects): b scoped
  proof `hostile-run4/5/6` (above, NATIVE_EXIT=0 where captured; run6 first
  launch caveat preserved) + a-round E-matrix suite at the a head.
  Re-verified at 24a: `fts:5552/9784/9908/10020/4352` PASSED in fresh G2 -rA
  (9.7).
- RC7 (R9 coherent rollback + truthful operator instructions): b scoped
  history ONLY (NOT fresh final proof — section 3.7); OPERATIONS.md false
  operator path corrected at `ea58664` (`docs/OPERATIONS.md:208-228` at 24a).
  FRESH at I 24a: both coherent RC7 tests — retained-v2-FIRST
  (`fts:2574`) + SEPARATE genuine v1-only 075 restore/re-upgrade
  (`fts:3065`, plus baseline `fts:1649`) — PASSED in the fresh full G2 -rA
  (9.7); root receipt with 23 named criterion cases. No redundant rerun
  required.
- RC8 (R8 admitted-work bounds + preserved lifecycle): b scoped proof
  `rc8-capture-focused-run5.log` @ `a82be261aca7c697` 1 PASS 39.03s
  NATIVE_EXIT=0 + secondary 8 MiB audit (lawful upper < 8 MiB; guard
  unreachable from constraint-compliant inputs, defense-in-depth; F1/F2
  reachability terms OPEN). Re-verified at 24a: `par:1124/1654/1906/3276/4198`
  and the lifecycle set PASSED in fresh G2 -rA (9.7); R3 audit + root source
  review: normalized per-node assertions + strict budget inequality present
  at I, no repair ordered.
- RC9 (F complete exact gates + honest reporting): NOT RUN under b
  (strategic pivot: known-failing images); b's final-31 attempt-2 at
  candidate I (CMD 01-20 EXIT 0 before root-directed stop at CMD 21; attempt
  1 preserved; CMD 08/09 octal-label metadata caveat disclosed; NO
  all-31-pass claim) remains failed/partial history. Superseded: this round
  section 6 at literal I + section 8 at final S.

### 9.4 c-order security/compatibility + final gates (c-report §4-§7)

- CodeQL test-only repair (finding 121131460161, no suppression): c §4.1 —
  `fts` F3 performs a real trusted PUBLIC read-back of
  `/api/agent/v1/global-regions` BEFORE the freeze (same admission surface
  the product uses) and asserts the exact stored footer id against that live
  trusted value; 067 SQL default-id semantics untouched; exact legacy-ID
  equality + closed-shape assertions kept; stale `usedforsecurity=False`
  comment corrected; the rejected 189-line custom MD5 oracle preserved at
  `/tmp/oap-083-5-c/rejected-custom-md5-oracle-attempt-309604b6.*` (reverted
  before J). Re-verified at 24a: CodeQL run 40215464714 SUCCESS (section 8).
- Parity timeout stage instrumentation (sanitized, existing spec, +214/−12):
  c §4.2 — single `stage` annotation replaced in place at every phase
  boundary (phase/engine/target/route-ordinal/action + cumulative ms only;
  no URLs/IDs/tokens; `bodyCompleted` guard preserves the last failing stage
  marker; no timeout/retry/config/reporter/coverage change; stage-entry
  cumulative elapsed honestly scoped, not per-phase wall history). Carried
  unchanged at 24a; exercised in fresh G3 (six-target pairings inside the
  600s ceiling at c-I5: 132176ms stage=cleanup).
- Security pin repairs: c §4.3 — Chrome for Testing `156.0.8078.47`/rev
  `1706539` (archive SHA-256 `e6c94490f0b6b337225aeb2d2a5034858516b7017356980ba94f5176d8774a50`,
  in-image executable SHA-256 `230f0db8c5086182f46c59c867c0d461eb525d6552dfad226ea6b4d9ec249db2`);
  NGINX `1.30.6-alpine3.24` (NGINX-ONLY 3.24; index digest
  `sha256:47928bf6...`) + brotli-libs 1.2.1-r0 overlay; PG digest KEPT
  `sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f`
  (18.6-alpine3.23) + brotli-libs 1.2.1-r0; Next `16.4.1` (+ `@next/env`, 8
  `@next/swc-*` entries, 2 metadata-only lines) with `ignoredOptionalDependencies:
  [sharp]` + `images.unoptimized: true` untouched; per-image exact Alpine
  registry enforcement with 6 meaningful negatives. The PG overlay libcurl
  term is the ONE e-scoped forward repair (section 4, 8.22.0-r0 -> 8.23.0-r0
  at the exact named paths); ALL other pins unchanged at 24a — re-verified
  by G1 CMD 01/02 (frozen lock/sync 0), G1 CMD 26 (licenses 0), and the
  section 8 artifact scans.
- 31-Critical census mapping (browser 26 + nginx 2 + postgres 1 + web 2;
  backend/apache 0; 31 matches, not 31 unique CVEs): c §5. Superseded at 24a
  by the CI artifact: all 6 raw scans 0 Critical / 0 exceptions, original 31
  same ID+pkg absent at any severity, 19 High full tuples inherited from the
  prior FAILED census (candidate ea586641 / artifact 12593246129; not a
  comparison against a prior successful bundle), 0 exceptions (section 8,
  root receipt).
- Docs corrections (153/155/156 attribution: 078-u = 153.0.8010.36 PR #80
  merged 2026-09-10 at `fe31c9f3`; separate 155.0.8059.84 = 083-3/PR #102
  candidate-8; current 156 PINNED with its own qualification measured at
  c-J2/I and at e's fresh local ALL6 pending/section 6 G5; ignored Sharp):
  c §4.4. Carried byte-exact in history; current docs corrected in c.
- J/I5-era WHOLE/RC7/CI history (c §6-§7): carried as immutable history —
  I5 WHOLE qualified at `d88ceaa` (G3_WHOLE_NATIVE_EXIT=0,
  `frozen-review-parity-six-stable-pairings` 132176ms, state-bound
  browser-artifact baseline freeze-run=CANCELLED:0/1 N=24/screenshot=3, all
  post-e2e security predicates OK); I5 G2 FULL interrupted (native 143,
  cause UNKNOWN, 902B log SHA `aee19918...`); I5 fresh six-image NOT RUN;
  I5 CI 17 SUCCESS / PG14,15,18 CANCELLED (15m budget, cause UNKNOWN).
  Failures preserved, never relabelled.

### 9.5 d-order D1/D2 + gates (d-report §5-§8)

- D1 (isolated CI PG groups A/B, fail-closed aggregator, 10 internal
  children + 5 required aggregator names): d §5 — `ci.yml` +100/−2 = 102
  GROSS; two explicit child jobs (`foundation-pg-group-a`/`-b`) + aggregator
  keeping the exact required name `Foundation PostgreSQL ${{ matrix.postgresql }}`
  (derives exactly the five PG 14..18 names); Group A = exact generic
  foundation command + exact 19-file bootstrap/privilege command (4+81=85
  per version), Group B = exact component/theme/page-style commands
  (24+9+12=45 per version), all five argvs byte-identical to the pre-split
  job; JOB-level `if: always()` + step-level always + env-passed needs
  results; fail-closed aggregate script exits 0 ONLY on (success,success);
  5-minute aggregator = NEW tighter budget (no timeout raised); proof
  `tests/repository/test_foundation_ci.py` (398L at 24a, stdlib-only, 15
  tests: exact names/matrices, child isolation, 85+45 split via folded-scalar
  extraction, aggregator semantics, no-scheduling-weakening invariants,
  ACTUAL extracted script executed over cross values — (success,success)
  sole exit 0, 15 negatives + 3 unset-env subtests + 7 in-memory workflow
  mutations each with baseline positive control and REQUIRED predicate
  rejection; the root-required predicate fix removed the tautological
  artificial raise at `43cd545`). Re-executed at 24a: CI run 40215464740 —
  all Foundation PG Group A/B children PG14-18 and the five aggregator
  names SUCCESS (section 8; 30/30 at I).
- D2 (truthful retained-review/manual/banner copy + strict blocked-warning
  assertion): d §6 — four named files: `docs/user-manual/README.md` Review
  Page (drift remedy = fresh/reapplied workspace + discard where appropriate;
  re-review/multiple-snapshot lifecycle = planned, not yet available;
  retained immutable snapshot history readable under existing
  authorization/retention, never automatically published; "reviewing itself
  does not publish"), `apps/web/app/review/[workspaceId]/[[...sitePath]]/
  route.tsx` public banner ("acceptance is blocked. The frozen review
  remains visible." — order ID removed), `apps/web/src/admin/
  workspace-review.tsx` DriftBanner (contiguous "acceptance is blocked"
  preserved), `tests/e2e/accept-lifecycle.spec.ts` drift test (entire new
  stable clause "acceptance is blocked. The frozen review remains visible.",
  exact:false substring matching the dynamic revision prefix;
  psql canonical_revision+1 drift injection, absent accept button, visible
  warning, `stopObserving()).toEqual([])` and all other assertions
  unchanged). Statics at d-I: prettier/tsc/eslint/markdownlint native 0.
  EXECUTION DISTINCTION: the D2 E2E text execution (the strict
  blocked-warning clause rendered in the live browser) runs in the WHOLE
  compose-e2e `accept-lifecycle` project — the fresh G3 at I is the current
  execution; G1 CMD 24 (`pnpm test`) is the UNIT surface only (web +
  browser-worker suites) and does NOT execute that E2E clause. d's
  mid-attempt compose-e2e (source-mixed WHOLE) completed all 19 projects OK
  incl. accept-lifecycle — scoped evidence from an interrupted attempt,
  never final. Re-verified at 24a: fresh G3 (section 6).
- G1 ALL31 at 43cd: d §7 — qualified at I `43cd5454` (FINAL attempt: all 31
  EXIT 0, ALL31_OVERALL_EXIT=0, wrapper child 0, 16:14:14→16:19:26Z,
  SOURCE_HEAD/TREE/DIRTY recorded); the two earlier source-mixed attempts
  (1705c3f, c4e6606) preserved as failed history with the fast-forward
  execution error disclosed. SUPERSEDED by the fresh 24a G1 (section 6,
  qualified at literal I).
- G2/G3/G4/G5/RC7 at 43cd: d §7 — G2 on the invalid dedicated 55443 context
  (attempt 1 exit 1 <8s zero output, cause UNKNOWN; attempt 2 targeted 503
  at `test_agent_browser_http.py:280`, stopped by strategic close, final
  summary NOT produced) — the 503 cause is now MEASURED (section 5:
  deterministic TEST-mode DSN port-guard rejection, zero product change);
  G3 source-mixed only; G4 qualified at 43cd (component-catalog OK +
  agent-openapi OK, actual child 0, exact command in log header); G5 NOT
  RUN (libcurl stage); RC7 NOT RUN fresh (proven inside the FULL suite,
  which did not complete). All five are re-run FRESH at literal I 24a4333
  in this round (section 6): G2 now QUALIFIED (347/347, 9.7), G3/RC7/
  G5 per section 6.
- Dedicated 55443 cluster: d §8 — decommissioned in e after metadata
  preservation (section 5.4); its deterministic invalidity is the measured
  port-guard rejection.

### 9.6 e-order specific criteria

- Narrow libcurl forward repair at exact named paths (8.22.0-r0 ->
  8.23.0-r0): section 4 (QUALIFIED locally at repaired source: build +
  runtime probe + focused packaging 49 passed / 38 subtests child 0;
  CI-verified at 24a: Compose + Supply-chain SUCCESS).
- G2 preview-runs 503 diagnosis with safe class/phase discrimination BEFORE
  full qualification: section 5 (measured: `AgentDatabaseSettings.
  _validate_locator` rejects DSN port not in {None, 5432} even in TEST
  mode — `agent_api/config.py:203` — deterministic
  `AgentDatabaseConfigurationError` before pool creation; zero product
  change).
- Isolated owned qualification context exposing 127.0.0.1:5432 to the
  owned PG only; host shared 5432 untouched; actual provenance: section 5.4 /
  §7. Expected 202 + clean fixture teardown first: section 5.4 (2 passed /
  22.19s / FOCUSED_CHILD_EXIT=0 at 43cd, scoped, NOT final).
- ALL31 complete BEFORE FULL G2; G2/G3/G5 SERIAL; final worktree immutable
  at ONE literal I: section 6 (sequence honored; G1 -> G2 -> G3 -> G5).
- Fresh COMPLETE UNFILTERED backend integration incl. all new cases on the
  dedicated cluster + coherent RC7: section 6 G2 / 9.7 (QUALIFIED at I).
- WHOLE literal `sh tools/compose/smoke.sh slaif0835` ALL phases / BOTH
  edges / ALL6 meaningful frozen targets / private BOTH IMAGE+DOCUMENT
  bytes + OpenAPI 0 + fresh local ALL6 at the SAME literal I: section 6
  G3/G4/G5.
- Final S: 20 required names + 10 internal PG children SUCCESS at CURRENT S;
  strict 20934043 / apps 15368+57789; no bypass: section 8 (may honestly
  remain PENDING at publication; never amended after S).
- Full R1-R9/A-F/RC1-RC9 evidence index with honest not-runs: this section.
- d-report corrections in the NEW report only: section 3.

### 9.7 Fresh full G2 -rA case identification at literal I 24a

Command (unfiltered, plugin-free except locked asyncio/anyio, isolated
context section 5.4): `uv run --frozen pytest services/backend/tests/
integration -rA --tb=short`. Result: **collected 347 — 347 PASSED, 0
failed / 0 error / 0 skipped, in 3688.19s (1:01:28), G2_CHILD_EXIT=0**
(start 2026-10-25T17:21:44Z.062, end 18:23:16Z.822; runner 6a48c3ec
terminal ExitCode=0; log SHA-256 `e84be97bbc31ca63bec5aeddab107c062407f736abbb27e2e84e8acb3698ef1a`;
source identity identical at start/end; root independent receipt
`strategic-24a-FULL347-and-RC7-independent-review.json` with 23 named
criterion cases). Named cases identified by their PASSED -rA lines:

| Case family | Test (file:line at 24a) | -rA result |
| --- | --- | --- |
| RC1 / public capture (A/R1/R2) | `fts::test_rc1_public_agent_and_editor_capture_retained_families` (6888) | PASSED |
| RC1 / numeric approval sibling | `fts::test_rc1_numeric_approval_composition_only_workspace` (9274) | PASSED |
| common real-SQL differential (R3/RC2) | `par::test_live_sql_common_port_route_navigation_differential` (234) | PASSED |
| RC2 G10/G11 real surfaces + sibling mismatch | `par::test_query_candidate_bound_admitted_real_surfaces` (3276); `par::test_sibling_mismatch_recomputed_digest_admission_refusal` (3806) | PASSED / PASSED |
| RC5 counterfactuals (D) | `par::test_omission_stub_counterfactuals` (1987) | PASSED |
| RC5 / forced validation failure | `fts::test_forced_validation_failure_leaves_freezing` (574) | PASSED |
| RC7 retained-v2-FIRST coherent rollback (R9) | `fts::test_076_001_round_trip_retained_v2_and_exact_restore` (2574) | PASSED |
| RC7 SEPARATE genuine v1-only 075 restore/re-upgrade | `fts::test_075_001_v1_only_downgrade_roundtrip_disposable` (3065) | PASSED |
| RC7 baseline roundtrip | `fts::test_075_001_round_trip_exact_restore_and_locked_materializer` (1649) | PASSED |
| RC8 admitted-work bounds + 8 MiB read-admission wiring | `par::test_rc8_captured_chain_raw_depth_and_byte_budget_wiring` (4198); `par::test_common_port_admitted_work_bounds` (1124); `par::test_family_cap_gate_refuses_before_group_allocation` (1654); `par::test_media_cross_check_runs_after_cap_gate` (1906) | PASSED |
| RC4 integration ASGI side (R6) | `test_media_service.py::test_private_media_bytes_human_preview_bound_worker_frozen_review` (731) | PASSED |
| RC3 static-ASGI drift half (R5/C) | `fts::test_frozen_drift_invariance_offline_live_and_discard_repeat` (4790) | PASSED |
| RC6 legacy v1 + hostile no-effects (R7) | `fts::test_v1_stored_workflow_read_refusal_discard_recreation` (5552); `fts::test_freeze_media_reference_row_tamper_matrix` (10020); `fts::test_freeze_over_budget_content_types_refused_no_effects` (9784); `fts::test_freeze_stale_catalog_schema_version_refused_no_effects` (9908) | PASSED |
| E matrix role denials | `fts::test_review_endpoint_frozen_read_media_urls_and_role_denials` (4352) | PASSED |
| C drift zero-mutation | `rha::test_accept_worker_drift_zero_mutation` (1373) | PASSED |
| R8 lock/lifecycle | `fts::test_lock_serialization_and_r4_shared_lock` (693); `fts::test_freeze_site_lock_failure_rollback_no_leaked_lock` (4151); `fts::test_concurrent_claim_and_stale_recovery` (340) | PASSED |

Scope notes: this is the integration directory proof only — the DEPLOYED-
WORKER BOTH bytes, the rendered six-target E2E, and the terminal BOTH bytes
remain the fresh G3 WHOLE obligations (section 6); unit counterfactual
vectors (9.2 D) re-ran in G1 CMD 06. No test was skipped, xfail-marked, or
weakened; the command is the exact unfiltered directory command.

## 10. Footprint, forecasts, variances (actual, measured)

- Root uniform minimal inventory at committed I 24a (17:16:59, clean
  `-i-e-final` worktree verified): **32868 gross production+tests under the
  unchanged 33000 ceiling** (within the order's 32868..32980 projection for
  the 8..120 repair forecast), docs **164/12** names (separate from the
  33000 production+tests ceiling), transcript **TEN** at I (a/b/c/d
  orders+reports = 8 plus the e order = 1 plus active = 1; the e report does
  not exist at I) and **ELEVEN** only at the final report-only S (e report
  added; named maximum 11), unknown 0. The e repair added +8 GROSS in
  PROD+TESTS ONLY over d's 32860 (the libcurl 8.23.0-r0 pin/assertion lines
  in `infra/postgres/Dockerfile`, `supply-chain/policy.json`,
  `tests/packaging/test_oci_contract.py`), exactly inside the recorded 8..20
  pin-repair forecast; docs moved 160 -> 164 (same 12 names) and are
  tracked separately, NOT counted in the 33000 gross.
- No new source identity, family, individual cap, or generated contract
  identity was created or consumed; the unused preview-page reservation is
  retained. Individual caps (collection-filter-components 160, combined
  edges 80, privileges 180, worker contracts 16, renderer behavior 300)
  unchanged.
- Forecast remainder at publication: 0 — no gate exposed a named-family
  defect; no additional source, test, or generated-contract change was
  required beyond the committed I. Inventory at I (root-measured)
  32868 gross prod+tests / 43+34 names, docs 164/12, unknown 0; nothing was
  added or removed after I.
- Estimates are uncertainty, never per-file caps or permission to pack/delete
  proof. No cap/authority change occurred.

## 11. Strongest reason not to merge

- This round is CLOSURE_ONLY on a PARTIAL history: even if every e gate
  passes at 24a, the original numeric-083 / MVP / product-completion scope
  remains explicitly unfinished (orders/reports preserve the downstream 084..
  091 MVP/ops/recovery/honest-release scope; no project/release completion or
  deployment claim is made here).
- Known retained limitations (not cured by e): private-artifact
  cancel-after-publish orphan DETECTION exists but PREVENTION does not (no GC
  feature in this increment; downstream 089/091); re-review/re-freeze
  lifecycle not delivered (retained review history is the current behavior);
  historical CI variances (PG14/15/18 cancellations in earlier rounds, c-I5
  G2 `.E` with unestablished cause, d 503 in the invalid 55443 context)
  remain disclosed history, not retroactively cured; R2 audit G1/G2
  completion-boundary test gaps and G4 real-SQL browser-negative coverage gap
  remain root-adjudicated items; 19 inherited High findings remain review
  inventory (not exceptions).
- Acceptance/merge is root's exclusive act after independent review of all
  orders/diff/architecture/security/privacy/docs/tests/scope/checks/policy;
  green CI and this COMPLETE report are necessary evidence, not acceptance.

## 12. Confirmations

- Same PR #107, AMEND_EXISTING_PR, one bounded semantic increment; no new PR,
  no merge, no auto-merge, no close, no next-ID selection by the executor.
- Order + active committed byte-unchanged with the implementation; all prior
  orders/reports/active history immutable (a/b/c/d reports and orders never
  edited; corrections applied in this NEW report only).
- No test weakening, no assertion removal, no skip/retry wrapper, no
  timeout/coverage/permission/condition/ruleset change, no workflow edit,
  no scanner omission/ignore/dismissal/reclassification/exception, no
  security/authority/network-confinement change, no port-guard relaxation,
  no product implementation change for the 503 finding (zero product lines),
  no pin change other than the exact authorized libcurl forward repair,
  no Sharp/libvips/optimizer/feature addition, no new dependency.
- No secret/capability/cookie/DSN/credential material in any report, log, or
  artifact (fixture constants only; PGPASSWORD redacted from provenance
  env lists).
- No human setup/terminal recruitment; owned setup performed by the executor
  with actual recorded outputs; protected production/data/credentials never
  touched; other projects' containers/DBs/roles/connections untouched;
  shared cluster 127.0.0.1:5432 never modified.
- No healthy Codex session restarted; primary 17 / secondary 21 remain the
  sole owners as assigned; secondary scratch-only (read-only source/CI/
  artifact audit; no product/runtime/DB/Git/FIFO writes).
- Every failed/partial attempt preserved with actual native exit and source
  identity: d 503 targeted output, e single-attempt1 (503 + teardown
  ERROR), driver-run1-namederror, no-password probe, first PG mount failure,
  aborted G2 launch, G4 attempt 1 (node missing); no unchanged-head CI
  rerun; no flake/benign/transient label attached to any preserved failure.
- Final response OK is sent exactly once, only after this immutable
  report-only S is pushed and remotely verified (the d-round invalid early
  ACK is never repeated).
