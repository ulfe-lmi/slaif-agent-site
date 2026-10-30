# OAP 083-8-g execution report: P7 truth-doc correction, owned export-container disposal evidence, and remaining-gates handoff

## 0. Header facts

- Round: 083-8-g (final strategic order of increment 083/8); mode CLOSURE_ONLY.
- Order: `oap/orders/083-8-g-truth-and-remaining-gates.md` (295 lines,
  content SHA256 `a80631e99604cc025435eec522282c8c0506249df473c823ff5d5d4da406f9fd`).
- PR: `AMENDED_EXISTING_PR` #112,
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/112>, state open;
  branch `oap/083-8-a-qualify-public-whole-session`; base main
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0` (unchanged this round).
- Starting remote SHA (Sf): `48e24f3513dbeed8197f78706a3f6e818894d75a`
  (f report-only SELF, verified remote head at round start).
- Literal implementation SHA (I_g): `4abcad4ee100898f259f3d19fe9de7d6c9268c07`
  (committed 2026-10-27T23:14:38Z; tree `5c69dbd957f0d0a614b621071868a0c69136bd6f`;
  sole parent Sf).
- Report publication commit: SELF (this report; sole parent literal I_g).
- Pushed commits this round: I_g (implementation, all nonreport work) and
  SELF (report-only, sole changed path this report).
- Status: PARTIAL.
- Control: one exact ASCII OK (2 bytes `4f4b`, no LF) consumed
  2026-10-27T22:54:40.568020Z on the verified control FIFO; response OK
  sent once after the remote proofs in section 4.

## 1. Exact I_g changes (all nonreport work)

### 1.1 The five allowed paths (sole diff vs Sf; vs I_f additionally the f report)

| Path | Sf blob | I_g blob | I_g content SHA256 (16) | Lines | Gross |
| --- | --- | --- | --- | --- | --- |
| docs/FOUNDATION_INTEGRATION.md | 7dd6ee5b | 25296ce1 | 90557161ed90640a | 276 | 24 (18+/6-) |
| docs/TESTING.md | dd2aa4a7 | df5e8578 | e4fe91edafd188fd | 415 | 12 (12+/0-) |
| tools/supply_chain/run.sh | 1ed9fb95 | 9d9b8feb | 8b4a5e88c0b2519a | 477 | 54 (48+/6-) |
| oap/orders/083-8-g-truth-and-remaining-gates.md | - | 843af5bd | a80631e99604cc02 | 295 | added |
| oap/active | 5fa47422 | 6fc126b6 | (content `083-8-g`) | 1 | changed |

Total new source gross vs Sf: 90 (activated cap 250; docs 36 <= 120;
run.sh 54 <= 80). No other leaf differs (ROOT-verified complete map,
section 2 G3).

### 1.2 Footprint accounting (actual, with preserved errata)

- Original exact five-doc set (FOUNDATION_INTEGRATION.md, TESTING.md,
  SUPPLY_CHAIN.md, oap/INCREMENTS.md, oap/MVP-PROGRESS.md): actual
  181 gross vs D18 at I_g (ROOT authoritative grouping, cap 500).
  DATABASE_CONNECTIONS.md (9 gross) belongs to the f pin-family 111, not
  the original five; the accidental all-four-docs sum of 181 is a numeric
  coincidence, not an identity proof.
- Cumulative paths: starting Sf 31 TOTAL (18 nontranscript + 13 OAP);
  I_g 33 TOTAL (19 + 14); after this report 34 TOTAL (19 + 15), the
  permitted maximum for this increment.
- Erratum (recorded with actual clocks in the forecast file): an early
  forecast wrote "34 substantive" (wrong wording: 34 is the TOTAL path
  count) and "192" (a conservative sum of round grosses, NOT the
  measured cumulative); the authoritative direct base D18 -> I_g docs
  diff is 163+/18- = 181 gross because g rewrites lines already added in
  the PR.

### 1.3 Frozen identities verified at I_g (byte-identical to I_f)

- Qualification module 1844 lines, content SHA256
  `45cf79671261212c19143315daeaecfc1b01b1e48d0b3c2cdf9e85cf881563a8`.
- `tests/repository/test_foundation_ci.py` content SHA256
  `56fdc0407d4ac44fb7a3f31b2fae8b4bed5174bdbb17862b2333a2ca89481bc3`.
- `.github/workflows/ci.yml` content SHA256
  `23ee9bc96c9d66b2fa4b3770da66bcc6de0f4babc7aa4d2e4a0b7ea6f18ec735`.
- `uv.lock` content SHA256 `9b6124bcac0e2d4f...`; `pyproject.toml`
  `d332be1d4fbed068...`; registry foundation 0.2.0 and asyncpg 0.32.0
  exact existing lock; every package/artifact unchanged; no new
  upgrade/install variant/SDK monkeypatch.

### 1.4 run.sh v2 behavior (export_rootfs + fallback cleanup ONLY)

No build/scan/dependency/semantics changes. For each successful OWN
export-container create:

- The actual create stdout ID is captured; the process ledger holds the
  actual ID; inspect, export, and removal (normal path AND already-owned
  fallback) all use the SAME ID; the chosen name is retained as metadata.
- Before export/removal, ownership evidence is written into the EXISTING
  bundle (unique per image/attempt):
  `manifests/export-container-<image>-<attempt>.json` (id, name,
  immutable `image_id`, `image_reference`, created, Mounts
  type/name/source/destination/mode/rw; NO Config.Env/secrets/token
  contents) and
  `manifests/export-container-<image>-<attempt>.cleanup.txt`
  (container_id, container_name, rm_volumes_native, actual 0 and
  failures). Records land BEFORE the existing finalize/validate, so the
  existing forbidden-marker scan and SHA256SUMS cover them (index.json
  schema unchanged; lifecycle files are auto-checksummed, not index
  fields). No new helper library/controller/service.
- Removal uses `docker container rm --volumes` on the own container only
  (removes attached anonymous volumes; not named ones;
  <https://docs.docker.com/reference/cli/docker/container/rm/>); the
  native is retained (no swallow); nonzero -> stderr message + explicit
  exit with that native (fail-stop; on_exit fallback runs).
- Fallback `cleanup()`: `rm --force --volumes` for ledgered
  positively-owned containers; failure native echoed to stderr and the
  loop continues to dispose remaining owned objects; no bundle writes
  after finalize (a successful on_exit mutates nothing already
  checksummed).
- No prune, global selector, foreign container/volume, service DB, or
  historical orphan sweep anywhere.

### 1.5 Documentation corrections (G1)

- `docs/FOUNDATION_INTEGRATION.md` P7 bullet (was lines 222-231),
  corrected against the ROOT-verified I_f source review:
  (a) the I_f scratch returned normally with four known pending
  operations and three relation pairs in the public
  `(depends_on, operation_id)` direction (`core.py` lines 1428..1440,
  `operations.py` lines 575..584); the printed `reversed_present=True`
  is a scratch artifact because its own expected-pairs block used the
  opposite convention - not an API reversal or a failed qualification -
  and no promotion or full-graph proof occurred; (b) the frozen 0.2.0
  changes-table primary key is `(session_id, operation_id,
  ORIGINAL_PK...)`, so `ordinal_position >= 3` removes the two internal
  bookkeeping prefixes rather than skipping any original 1-2 column
  primary-key table, and the dirty-changes enumeration returns
  changes-table names; (c) the composite-FK per-column/single-column
  UNION edge concern (`cow_sql_functions.py` lines 1745..1800) is kept as
  a separate bounded source lead, not an observed UUID/TEXT exception or
  a general graph verdict from P7; (d) the I_f fixture has composite
  `(site_id, id)` foreign keys - a single UUID primary key is not a
  single-column foreign key; (e) the executed scratch, orders, and
  reports are preserved unchanged.
- `docs/TESTING.md` 083/8 section: appended the qualification subject
  (generic whole-session COW promotion mechanism through the public
  `agentcow.postgres` 0.2.0 API on an owned disposable cluster; this
  increment does not implement or accept actual product publication,
  complete U/audit or causal closure, or MVP), the I_f carry rule (I_f
  results carry only under the increment's identity/scope gates, labeled
  I_f, no later PASS claimed before its own fresh run), and the remaining
  acceptance requirements (fresh LOCALWHOLE and LOCAL6 supply-chain
  evidence runs bound to the actual tested implementation SHA, each
  reported when and if executed). No future-PASS or product claim.

### 1.6 PRIMARY-owned declared image-volume inspection (read-only)

- Reference: `docker.io/library/postgres:18.6-alpine3.23@sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f`
  (exact `oci_sources.postgres` from `supply-chain/policy.json`, as read
  by run.sh).
- `docker image inspect` native 0 at 2026-10-27T23:01:19Z; actual
  declared metadata `Config.Volumes = {"/var/lib/postgresql": {}}` - the
  actual declared key (NOT `/var/lib/postgresql/data`); raw JSON
  `/tmp/oap-083-8-g/pg-inspect.json`; record file
  `/tmp/oap-083-8-g/pg-image-volumes-inspection.txt`
  (SHA256 `f270f89489fad62f...`).
- No container was created or started; no runtime leak claim is made.

## 2. G1-G9 status per original order

### G1 Truth - SATISFIED

Both docs at I_g correctly explain the physical PK prefix and the public
pair direction/limited P7 result, with historical artifacts preserved
(sections 1.5, 1.6). ROOT source review: G1 satisfied.

### G2 Safe verification disposal - source + CI pre-delete records qualified; local actual absence UNPROVEN

- Source: section 1.4; ROOT full read plus failure-path audit
  (`root-peer-frozen-export-cleanup-source-adjudication.json`, peer
  SHA256 `a23d142633bc14af...`, 14 lines) accepted with qualifiers.
- CI (ROOT-reviewed facts, cited as ROOT measurements, not new executor
  observations): the I_g packaging job executed run.sh v2 and produced
  24 new lifecycle files (12 export-container `.json` + 12 `.cleanup.txt`)
  inside the validated six-image artifact 12779410274 (78 members / 77
  payload hashes; 0 Critical / 0 ignored / exceptions EMPTY; the same 19
  inherited High as full 6-tuples; 19 High remain visible evidence - no
  blanket license or global-clean claim).
- The 12 CI pre-delete ID/Mounts records plus rm0 are NOT post-absence
  proof; raw image IDs differ / normalized equal (ROOT fact). Local
  PRIMARY post-terminal absence proof remains required and was not run.

### G3 Identity/scope - SATISFIED

ROOT independently verified remote I_g `4abcad4e` / tree `5c69dbd9`,
sole parent Sf, PR112 open/exact base/branch/main D18; complete 1131
leaf map vs Sf (exactly the 5 allowed changes) and vs I_f (those 5 plus
the f report) with ALL other mode/type/blob equal; local changed bytes
match remote (section 1.3 freezes the qualification/CI/lock identities).

### G4 Affected checks - QUALIFIED at literal I_g (actual results)

| Check | Exact argv (gate-wt at I_g) | Actual clock (UTC) | Native | Limitation |
| --- | --- | --- | --- | --- |
| C1b sh syntax | `sh -n tools/supply_chain/run.sh` (direct, no pipe) | 23:21:28Z (ns 1793143288229577197 -> 1793143288241145959) | 0 | both streams saved (0B, `e3b0c442...`); supersedes original C1 |
| C2 supply-chain tests | `uv run --frozen pytest tests/supply_chain` | 23:18:19-20Z | 0 | 43 passed in 0.77s; saved log is tail-5 only |
| C3 repository policy | `python tools/check_repository.py` | 23:18:20-26Z | 0 | PASS; saved log is tail-5 only |
| C4 repo-global markdownlint | `npx --yes markdownlint-cli2@0.23.2 '**/*.md'` (exact repo config) | 23:19:12-30Z (ns 1793143152601466887 -> 1793143170026189508) | 0 | 573 files, 0 issues; full raw log `8b867d93...` |

- Original C1 (23:18:19Z) used `sh -n ... | tee`: tee native 0 was saved
  but the sh -n child native is UNKNOWN (pipe); the preserved unknown is
  qualified by the single ROOT-approved C1b direct capture (native 0).
  No other check was rerun for permission receipts.
- C1-C3 started 23:18:19 after ROOT's independent gate observation
  23:17:48.398704 and under the activated g check authorization, and
  before the explicit note (note read 23:18:39); actual timing is
  reported, not re-sequenced.
- C4 count delta vs the f round (571 -> 573) = f report + g order (both
  now tracked at I_g); 6 ignored paths on both sides.

### G5 Fresh LOCALWHOLE - NOT RUN

- At most two scratch runner paths were authorized
  (`/tmp/oap-083-8-g/whole-g.sh`, `/tmp/oap-083-8-g/local6-g.sh`;
  planning 240/180, hard 350 each / 600 aggregate).
- v1 staging 257 lines (SHA256 `a9d751da6a404f...`) was FULL-read by
  ROOT with eight finite items (A-H: trap arming before ownership,
  signal-path sweep while child live, set -e expected-failure aborts,
  missing sixth postgres tag, running-only observer/mutable image ref,
  raw-byte absence, cleanup ordering, finite bounds).
- v2 staging 428 lines / 15114 bytes (SHA256 `67a53a3e7e9b...`) was
  FULL-read by ROOT; static adjudication found seven remaining defects,
  including the CRITICAL false-coverage-PASS path (docker events default
  text output vs JSON parser, mixed event types, request-only process
  cleanup) plus raw-byte, phase-deadline, and post-facts gaps.
- CAP STOP: 428 exceeds the activated 350 hard cap and was measured
  AFTER the staging write (a staging write is still a write). Staging
  preserved; never installed to a final path; no further runner writes
  or trials; complete actual+remaining forecast submitted (WHOLE v3
  natural ~551 + LOCAL6 planned ~300 = ~851 vs 600; ROOT decides
  continuation - planned h, not executor choice).
- No WHOLE execution at I_g; both old LOCALWHOLE carries remain VOID.

### G6 Fresh LOCAL6 - NOT RUN

- Plan only, never written to disk: actual owner-PID receipt binding
  (child shell PID = run.sh `$$` = run_identity; no timeout-wrapper PID
  conflation), separate wrapper-control vs pipeline-bundle directories
  (bundle dir stays absent/not-symlink until run.sh creates it; wrapper
  never writes there), bounded watchdog (TERM at nominal 5400, KILL +5,
  natives retained), bundle-record-level owned absence proof (daemon
  health + positive control + specific not-found + exact subject, raw
  bytes per subject), residual sweep bounded to exact
  `slaif-supply-<pid>-` selectors, no extra validate-bundle invocation.
- No LOCAL6 execution at I_g; old LOCAL6 carry remains VOID.

### G7 Carry applicability - SATISFIED as precisely-labeled I_f carry

Unaffected actual I_f evidence (ALL31 except changed-document checks,
the additional Python checks, Q80, FULL363, P7 characterization, and the
fresh I_f ALL31 cmd6 OpenAPI zero-diff proof) carries only under the
exhaustive G3 identity gate, cited with ACTUAL I_f subjects/times/hashes
from the f report and ROOT proof indexes (referenced, not duplicated
here). Nothing is relabeled as executed I_g; this carry is
source-identity reasoning for documentary/verification-cleanup changes,
not a waiver of any functional criterion. FULL363 remains actual
complete unfiltered proof, not a selected substitute.

### G8 Final SELF CI - I_g current green (ROOT facts); final SELF CI PENDING

- Current I_g CI: all 20 strict names/correct apps + 10 PG children
  SUCCESS; live policy unchanged (ROOT-reviewed fact).
- Actual CI checkout for the packaging artifact: `035d3eee` with merge
  parents D18 + I_g and tree I_g - NOT a literal-I_g checkout (caveat
  preserved). CI artifact rm0 is not actual post-absence.
- Final SELF CI on this report-only commit: pending at publication time
  (report-only delta; no semantic change). Required regardless of local
  carry; this report does not claim it.

### G9 Publication - THIS REPORT

Formal report-only publication per protocol (sections 3-4).

## 3. Evidence indexes (g scratch `/tmp/oap-083-8-g/`)

- Image inspection: `pg-inspect.json`, `pg-image-volumes-inspection.txt`
  (`f270f894...`).
- G4: `affected-Ig/c1b-sh-n.stdout.log` + `c1b-sh-n.stderr.log` (0B each,
  `e3b0c442...`), `c2-pytest-supply-chain.log` (tail-5),
  `c3-check-repository.log` (tail-5), `c4-markdownlint.log` (`8b867d93...`,
  full raw), source-fact lines in the same directory.
- Forecasts (all preserved with actual clocks/errata):
  `g-phase-a-forecast.txt` (201L, `99f084e3...`, dated erratum section),
  `wholesale-local6-plan-forecast.txt` (108L, `9400d1ba...`),
  `wholesale-local6-actual-remaining-forecast.txt` (201L, `b722c562...`).
- Source-rejected drafts (never executed): `whole-g.sh.staging` (257L,
  `a9d751da...`), `whole-g.sh.v2.staging` (428L, `67a53a3e...`).
- Procedural-deviation artifacts (preserved): `build-candidates.py`,
  `candidates/` (nonexecuting planning copies).
- ROOT proof indexes (ROOT measurements/reviews, cited):
  `root-Ig-applied-source-and-scope-adjudication.json`,
  `root-G4-postsource-facts.json`,
  `root-G4-native-adjudication-and-one-C1-decision.txt`,
  `root-G4-qualified-C1b-and-postsource-review.json`,
  `root-Ig-CI-six-image-artifact-independent-review.json`,
  `root-Ig-CI-packaging-raw-independent-review.json` (+ run/jobs/checks
  artifacts and raw packaging log in the same directory),
  `root-peer-frozen-export-cleanup-source-adjudication.json`,
  `root-peer-WHOLE-capture-lifecycle-source-adjudication.json`,
  `root-WHOLE-first257-source-review.txt`,
  `root-WHOLE-v2-428-static-adjudication.txt`,
  `root-WHOLE-v2-428-cap-stop.txt`,
  `root-g-PARTIAL-closure-and-prospective-h-decision.txt`.
- Unchanged carry: f report
  `oap/reports/083-8-f-upgrade-released-driver-and-qualify.md` (671L,
  `dae88a51...`) plus its receipt/proof indexes; no full historical
  ALL31 output duplicated here.

## 4. Procedure, publication, and remote proof

1. Same-filesystem TEMP prepared inside `oap/reports/`; exact repository
   markdownlint CLI 0.23.2 `--no-globs` on the SAME complete final TEMP:
   native 0, one file, zero issues (any edit re-linted; see publication
   receipt facts recorded in the scratch before rename).
2. Pre-hash/inode/size of the complete closed TEMP, explicit file fsync,
   same-inode atomic rename to the sole report path, parent-directory
   fsync; actual UTC + `time.time_ns()` raw-ns in the receipt (correcting
   the f receipt errata of missing raw-ns and missing report-file fsync).
3. Report-only commit with sole parent literal I_g
   `4abcad4ee100898f259f3d19fe9de7d6c9268c07` and sole changed path this
   report; pushed to the PR branch.
4. Remote proof (verified before the single response OK): PR112 head =
   SELF SHA, SELF parent = literal I_g, sole report path present, report
   bytes identical to the linted TEMP (SHA256 match).
5. ONE exact ASCII OK (2 bytes, no LF) written to the verified live
   response FIFO (inode 4470112; ROOT sole g response reader
   18531/PID2871616 verified pending) and closed; no replay.
6. One byte-retaining control reader opened after the response (bytes +
   EOF + status captured separately; never `read &&`).

## 5. Procedural deviations (actual, preserved, not retroapproved)

1. Standalone builder: `build-candidates.py` was written and executed at
   23:07:59 BEFORE the complete forecast existed; the activated order
   permits only the two prospective scratch executable runner paths and
   direct guarded tool operations. Preserved; never re-executed; later
   mechanical edits were direct guarded edits.
2. Synthetic payload simulation at 23:08:36: an unnecessary mirror
   selftest. Preserved; no repeats. The first bad-extraction compile
   native 1 (test-harness truncation, not source) is preserved; the
   corrected compile 0 is syntax-only; no synthetic payload result is
   gate proof.
3. Before-write measurement failures: the v2 source corrections were
   applied to the repo by direct guarded edits BEFORE a complete
   in-memory v2 candidate measurement (the v2 forecast section carried
   planning estimates; post-edit measurement at 23:13:44Z showed 90
   gross, within caps; I_g committed 23:14:38Z). The 428-line staging
   was written before the cap assertion (CAP STOP). This report does not
   claim all source statics "always passed" and does not claim staging
   was written only after a successful cap assertion.
4. Clock errata: the v2 forecast header "23:20:00Z" was a FUTURE
   hardcoded time (actual file final mtime 23:14:29.183Z; ROOT read the
   file at actual 23:14:25Z); the first header "23:09:00Z" is
   approximate vs the actual first write 23:10:11.569Z. Dated erratum
   recorded in the forecast; no invented times afterward.
5. Counting errata: "34 substantive" was wrong (34 is the TOTAL path
   count, 19 nontranscript + 15 OAP); "192" was a round-gross sum, not
   the measured cumulative (measured 181); original five-doc set
   composition corrected per ROOT (section 1.2).
6. G4 C1 pipe: original C1 saved tee native 0 with sh native UNKNOWN;
   qualified by the single approved C1b (direct, no pipe, native 0). No
   other check rerun.
7. Source-rejected drafts (257 v1, 428 v2) were never executed; no
   functional trial, no Docker/SDK/DB run of any runner.

## 6. Limitations and unresolved criteria

- G5/G6 NOT RUN: fresh LOCALWHOLE and fresh LOCAL6 at literal I_g remain
  required for COMPLETE; this PARTIAL report does not claim them. The
  local PRIMARY post-terminal absence proof of owned export
  containers/volumes (G2/G6) is unproven outside the CI execution
  (section 2 G2).
- G8: final SELF CI on the report-only commit pending at publication.
- No generic qualification-to-product, U/audit, causal-closure, or MVP
  completion claim is made anywhere in this report; increment 083/8 is
  PARTIAL and not accepted.
- The planned strategic next round 083-8-h (AMEND the same PR112,
  CLOSURE_ONLY) is NOT active. A small bounded change in existing
  verification tools at actual owned creation/disposal points is
  anticipated in that future order after formal g review; the executor
  did not start or choose it. No cap expansion was authorized by note.

## 7. Confirmations

- Scope: exactly the three allowed substantive paths plus the g
  transcript/active at I_g; this report adds only the report path. No
  product function, migration, dependency, CI-selector, authority, or
  lock change. No new helper library/controller/framework; the
  source-rejected runner drafts were never executed.
- Secrets: none in any artifact; fake credentials only; no capability,
  cookie, DB URL, setup, or private-artifact credential exposed. The
  run.sh bundle records exclude Config.Env/secrets/token contents;
  Mounts.source intentionally retains allowed
  `/var/lib/docker/volumes/...` host paths (safe allowed metadata, not
  absence of all host paths).
- Production: untouched. Skip/extra-PR: none; one PR (#112) amended; no
  merge, no auto-merge, no acceptance, no next-objective advance.
- This round is verification/truth work only; diagnostics are not
  qualification, cause closure, or merge permission.
