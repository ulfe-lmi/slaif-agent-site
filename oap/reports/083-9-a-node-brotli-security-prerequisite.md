# OAP 083-9-a execution report: Node and Brotli runtime security prerequisite, closed PARTIAL by ROOT security finding

## 0. Header facts

- Round: 083-9-a of numeric objective 083 (unresolved), semantic
  increment 083/9, mode `CREATE_NEW_PR`. Closed PARTIAL by ROOT
  strategic decision at 2026-10-30T04:43:48Z after the material
  browser-security finding (section 4). Not accepted; not merged;
  `NEEDS_NEXT_ORDER`: bounded browser security fix as ROOT 083-9-b on
  the same PR113.
- Order: `oap/orders/083-9-a-node-brotli-security-prerequisite.md`
  (299 lines, 17563 bytes, content SHA256
  `bda7e86fad1229e3eea93497f4136c0d633ac57b9c67990ece694c3089846ea1`,
  blob `4a82557568c03d791b389dbf2e83ad70f1faa42a`), copied byte-exact
  into the fresh worktree for transcript publication; activated
  2026-10-30T02:05:24.215545Z with one exact control OK (2 bytes
  `4f4b`, no LF, native 0, closed 2026-10-30T02:05:28.677986Z) consumed
  by the existing primary control reader session 68477 (wrapper 864383
  / head 864387, control FIFO inode 4470111), which retained
  `/tmp/oap-083-8-i/next-control-signal.bin` and its `.native` sidecar.
- PR: `CREATE_NEW_PR` #113
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/113>, state OPEN,
  mergeable, base main
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0` (D18, unchanged at round
  start and at report preparation), head branch
  `oap/083-9-a-remediate-node-brotli-runtime`, fresh clean worktree
  `/home/janezp/codex-work/slaif-agent-site-083-9-a`.
- Starting remote SHA (main D18):
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0`, independently rechecked
  before branching and again at report preparation (`git ls-remote`).
- Literal implementation SHA (I9):
  `db37a4659277c3a405e375e05acc12c446a2a452` (tree
  `59e56fdf3b622c9951fbef96082a9ccefe11bd83`, committed
  2026-10-30T04:19:39Z), fourth and final source commit of the chain
  `3747d31b85b1a415760e843d33e6f5787111dc36` (committed
  2026-10-30T03:22:35Z) -> `c445af6fbe979b39476a08765f48f88cf2dd97e5`
  (committed 2026-10-30T04:03:48Z) -> `596147a22b8ef060243f0846852a20f653d89d02`
  (committed 2026-10-30T04:12:16Z) -> I9. No amend, force-push, or
  rebase at any point.
- Report publication commit: SELF (this report; sole parent literal I9
  `db37a4659277c3a405e375e05acc12c446a2a452`; sole new path this
  report).
- Pushed commits this round: the four source commits above, then SELF
  (report-only).
- Status: PARTIAL (ROOT strategic decision; not accepted; not merged).

## 1. Source state: exact scoped changes versus D18

Thirteen paths differ from D18 at I9 (`git diff` name-status/numstat,
read-only): eleven source paths, the activated order (added), and
`oap/active` (1+/1-):

- `apps/web/Dockerfile` 3+/3-
- `docs/DEPLOYMENT.md` 1+/1-
- `docs/SUPPLY_CHAIN.md` 17+/9-
- `oap/INCREMENTS.md` 3+/2-
- `oap/MVP-PROGRESS.md` 2+/2-
- `oap/active` 1+/1-
- `oap/orders/083-9-a-node-brotli-security-prerequisite.md` 299+/0-
- `services/browser-worker/Dockerfile` 43+/4-
- `supply-chain/policy.json` 8+/2-
- `tests/packaging/test_oci_contract.py` 15+/1-
- `tests/supply_chain/test_policy.py` 18+/0-
- `tools/compose/smoke.sh` 2+/2-
- `tools/supply_chain/policy.py` 18+/3-

- Source gross versus D18: 159 natural lines (130 added / 29 removed)
  across the eleven source paths, versus planning 400 / HARD 600. No
  force-fit, packing, generated mirror, or proof deletion.
- No `uv.lock`, `pnpm-lock.yaml`, CI workflow, selector, app
  package/dependency, lock, helper source path, or infrastructure
  change; no new branch or second PR.
- Browser freeze held: CfT `156.0.8078.47` / revision `1706539` /
  pinned archive hash, Playwright `1.62.1` / Noble base, the six
  targets, sandbox, egress, and user `10001` are byte-preserved; no
  browser code change occurred under round a.

Per-path substance:

- `apps/web/Dockerfile`: both stages moved to
  `node:24.22.1-alpine3.23@sha256:0468540aa58203ff9e40c2aab3907c52644ab818af6176b1c70a026137dc92a2`
  with a provenance comment (CVE-2026-111497 fixed release).
- `services/browser-worker/Dockerfile`: official Node 24.22.1
  linux-x64 `.tar.gz` (SHA256
  `eb6728e77c576a35162c122c45ccadf224d89ff00abc8dae46cc2897c6002d7c`)
  installed to `/usr/local` in builder and runtime; obsolete NodeSource
  `nodejs` removed with valid apt argv; fixed
  `libbrotli1=1.1.0-2ubuntu0.1` (Noble) installed from the Noble repo
  overlay before affected use with exact version gate; npm/npx/
  corepack/pnpm/pnpx and the legacy `/usr/lib/node_modules/corepack`
  tree removed from the runtime (builder Corepack/pnpm retained for the
  frozen lockfile build); upstream LICENSE retained; truthful
  inventory comments (no fake dpkg metadata, no wrapper).
- `supply-chain/policy.json` and `tools/supply_chain/policy.py`: exact
  Node 24.22.1 literals (web digest; worker archive URL + SHA256),
  required `archive_url`/`archive_sha256` keys with exact validation,
  browser-worker Ubuntu override (install `libbrotli1=1.1.0-2ubuntu0.1`,
  remove `nodejs`); all other pins, scanner, license, vulnerability,
  and exception policies preserved; no exception added.
- `tools/compose/smoke.sh`: the worker image-content guard is
  fail-closed on the first failed conjunct (`sh -exc`; public fixed
  paths and versions only), asserting installed Node 24.22.1, runtime
  npm/corepack absence at both `/usr/local` and the legacy
  `/usr/lib` locations, and entire `/ms-playwright` tree removal
  before the exact CfT payload copy; every other oracle intact.
- `tests/packaging/test_oci_contract.py`: guard extended to require
  whole-tree `/ms-playwright` removal (the old glob literal must now
  fail) plus removed-tool assertions.
- `tests/supply_chain/test_policy.py`: meaningful negative cases
  added (stale Node version, unapproved archive URL, wrong 64-hex
  SHA); existing tests and oracles preserved.
- `docs/DEPLOYMENT.md`, `docs/SUPPLY_CHAIN.md`, `oap/INCREMENTS.md`,
  `oap/MVP-PROGRESS.md`: exact versions/provenance, the bounded
  negative guards, and verification PENDING stated truthfully;
  sequencing 083/7 accepted/merged, 083/8 PR112 OPEN ON HOLD with
  round i PARTIAL, 083/9 in flight; no invented permission gate.
- `docs/TESTING.md`, `THIRD_PARTY_NOTICES.md`, `sbom.json`: unchanged
  (no necessary change this round).

## 2. N1-N6 evidence (truthful)

### N1 PR/base, scoped source and size, preservation - met at source level, pending ROOT acceptance

- Exactly one new PR from verified remote main D18, on the order-named
  branch, in a fresh clean worktree; `git status` clean at report
  preparation.
- Thirteen paths, source gross 159 versus planning 400 / HARD 600
  (section 1); locks, CI, authority, and infrastructure untouched.
- The PR112 checkout, its 264-line verify.py WIP, all history, and the
  human files (`.codex/`, `CODEX-SESSIONS.md`, `codex.sh` untracked)
  are preserved and untouched; no reset, force, amend, rebase, clean,
  or foreign deletion.

### N2 Fixed Node/Brotli copies and provenance, honest inventory - PARTIAL

- Source-level fixed copies: web registry digest
  `sha256:0468540a...dc92a2` (public registry metadata verified
  before build - a metadata-only observation, not built-binary
  proof); worker official `.tar.gz` downloaded bytes verified
  (58,290,700 bytes) with inner `bin/node` 126,879,696 bytes /
  `e32e2d16081cf644f88392934288086e7662529d0d43277c34f7aad2207cfafb`
  and LICENSE 157,609 bytes /
  `5888dbb9a1d2b18f2c3e6c5f6af1b39de658372b402a0577b002777f14c62ace`
  compared byte-identical to the previously verified xz payload
  (ROOT-verified); obsolete NodeSource binary removed; fixed
  `libbrotli1=1.1.0-2ubuntu0.1`; honest docs (verification PENDING).
- CI Supply job at I9 actually built all six images and scanned the
  built artifact 12954930004: no CVE-2026-111497 match in any of the
  six images, scanner Critical 0, ignored 0, empty exception sets
  (section 5 of the order satisfied at CI-artifact level).
- Unmet: the order additionally requires fixed-copy provenance beyond
  scanner absence - runtime executable path/version/hash/provenance at
  user 10001 and every actual loaded/embedded decoder copy proven by
  the two-image probes (N4). Those probes are NOT RUN (section 6), so
  N2 is PARTIAL, not met.

### N3 Fresh ALL31 and affected checks - PARTIAL (affected checks passed; fresh ALL31 NOT RUN)

- Fresh ALL31 (the order's 31 exact local commands): NOT RUN. The
  31-command runner (planning 120 / HARD 160) was constructed in
  memory only; unit 1 (header/source-identity block) was delivered
  for ROOT review and was not approved; no runner file was ever
  written or executed. No ALL31 pass is claimed.
- Necessary affected checks were run once per source commit with
  bare immediate-child natives, full streams, real UTC plus raw
  `time.time_ns()`, and source SHA256 binding; logs retained under
  `/tmp/oap-083-9-a/logs/`:
  - I9 boundary (2026-10-30T03:13-03:14Z): ruff check native 0; ruff
    format --check native 0 (351 files); compileall native 0;
    unittest packaging first run FAILED (errors=2, `node` missing
    from PATH) then one environment-change re-run with Node v24.22.1
    scratch on PATH: 49 tests, 0 failures, native 0; unittest
    supply_chain 44 tests OK native 0; markdownlint-cli2 0.23.2
    repo-config 560 files, 0 issues, native 0.
  - Full-scope re-run (03:19:45-03:20:02Z): ruff check 0, ruff
    format 0, compileall 0, sh -n 0 (pipeline native - see erratum),
    packaging 49/0 0, supply 44/0 0, markdownlint 560 files 0 issues
    0. This whole-suite re-run was unnecessary and is disclosed
    without retroactive approval.
  - Bare sh -n correction (03:21:23Z): native 0; smoke.sh SHA256
    `b2d719d472f4d6cce08379a0c885232b767fd5b0810b91b8dd772e0230236652`
    identical pre/post.
  - c445af6f boundary (04:03Z): ruff check 0, format 0, compileall 0,
    sh -n 0, packaging 49/0 0, supply 44/0 0; eleven-path source
    manifest identical pre/post.
  - 596147a2 boundary (04:11Z): sh -n bare 0; packaging 49/0 0;
    smoke.sh SHA256 `7e988a7d851a5dba50371e14ef24e20ad75faea671f49b84fe56542cfba35660`
    identical pre/post.
  - db37a465 boundary (04:19Z, final): ruff check 0; ruff format
    --check 0 (351 files); unittest packaging 49/0 0 (Node v24.22.1
    PATH); worker Dockerfile SHA256 `d7fe02fe41a7d4b7093782c366eeca5aa5665431f6745dd0db2db4027308bf5b`
    and test_oci_contract.py SHA256
    `755a7b11ccca6d284367f1c6e546e77f349bfed4406e5eb2dfde1ba460697371`
    identical pre/post.

### N4 Approved two-image runtime probes - NOT RUN

- `verify-node.sh` (planning 220 / HARD 350) was never written; no
  Docker build, start, probe, or cleanup happened in this round; no
  ownership, bounded-execution, cleanup, or absence claim is made.

### N5 Required checks, packaging, six-image evidence, full High comparison - PARTIAL

- At I9 (runs created 2026-10-30T04:19:46Z, observed 2026-10-30T04:53Z
  via the GitHub API, read-only): 30 check runs - 30 completed/
  success, 0 failure/pending/cancelled. All 20 branch-protected
  required strict checks green: Repository policy, Node contracts,
  Python 3.12/3.13/3.14 quality and package, Foundation PostgreSQL
  14-18, Compose and edge packaging (job 123889588964, 17m4s),
  Supply-chain evidence (job 123889589372, 11m40s), Markdown, Mermaid,
  Dependency review, Detect supported languages, Analyze (actions /
  python / javascript-typescript), CodeQL. All 10 actual PG children
  green (Foundation PG Group A and Group B, PostgreSQL 14-18).
- Supply artifact 12954930004 (zip SHA256
  `19fe161cf51503c305f2fc3dd19fb4398be3365f796976a5c51dbea89df1b20d`,
  53 checksum payloads, exact payload set excluding self): scanner
  severities apache Negligible 3 / Low 17 / Medium 171; backend
  Medium 11 / Unknown 2 / Negligible 1 / High 1; browser-worker
  Medium 1609 / Negligible 14 / Low 134 / High 33; nginx Medium 3;
  postgres Medium 5 / Unknown 2 / High 7 / Low 1; web Medium 3 / High
  1. Critical 0 in all six images; ignored 0 in all six; exception
  sets empty; no CVE-2026-111497 anywhere.
- Full High comparison against the qualified historical 19: 13
  retained, 6 removed (five `node@24.14.1` web binary tuples
  CVE-2026-48617/-48937/-56846/-56848/-58043 plus
  `zlib@1.3.2-r0` alpine-3.23.4), and 29 NEW - all
  `chrome@156.0.8078.47` tuples: CVE-2026-118314, -118315, -118317,
  -118320, -118327, -118328, -118329, -118331, -118334, -118336,
  -118338, -118339, -118341, -118343, -118344, -118345, -118346,
  -118347, -118348, -118349, -118350, -118351, -118352, -118353,
  -118354, -118356, -118357, -118358, -118359.
- Scanner severity facts are unchanged: scanner "Critical 0" is not a
  vendor-Critical-none claim. Three of the 29 new (CVE-2026-118331,
  CVE-2026-118344, CVE-2026-118348) are vendor-CRITICAL in Google's
  2026-10-27 stable-channel desktop release (52 security fixes;
  fixed Linux version 156.0.8078.73). The official CfT last-known-
  good JSON (document timestamp 2026-10-29T22:14:17.810Z) now lists
  stable 156.0.8078.80 / revision 1706539 with linux64 archive
  <https://storage.googleapis.com/chrome-for-testing-public/156.0.8078.80/linux64/chrome-linux64.zip>;
  its archive SHA256 is NOT_YET_VERIFIED - no hash was fabricated and
  the new patch is not locally or CI qualified.
- The 29 new High findings require ROOT review; they are not
  auto-accepted, suppressed, or excepted. N5 is PARTIAL: the required
  set is green at I9, but the final SELF CI is fresh/unknown at
  publication and the new Highs remain unresolved pending 083-9-b;
  green CI alone is never acceptance.

### N6 Truthful docs/report/publication/synchronization - in progress with this report

- Docs updated truthfully (section 1); this report; publication,
  remote proof, and FIFO steps in section 5 (prospective at this
  commit, actuals in the closure message); no historical edits.

## 3. CI as actually observed (GitHub API, read-only)

- D18/Sh baseline (as recorded in the order): 28 success + 2 failure
  in run 40981094419 - Supply-chain evidence job 123821259915 (web
  Node 24.14.1 Critical CVE-2026-111497; artifact 12945032923,
  11213308 bytes, SHA256
  `fcd9e822cbe67b67a54c837d6fe66d9f759e45f63fae586bc429118e76235139`)
  and Compose and edge packaging job 123821259675 (media-publication
  final console tuple: source other / message other-browser-error /
  len 79 / https; root cause UNKNOWN; strict console assertions and
  privacy redaction not weakened; not labeled infrastructure).
- I9 3747d31b (run 40997109751): Supply job 123872681880 and Compose
  job 123872681719 FAILED after the SHA-verified xz download:
  `tar -xJf` exec native 2 (no xz native in the base image).
- c445af6f (packaging job 123884441651, FAILED): both image builds
  succeeded and services were healthy; compose-policy OK, membership
  OK, mode OK, review-worker-media-boundary OK,
  browser-worker-runtime-policy OK at 04:07:07.3098243Z; then exit 1
  at 04:07:08.6735079Z before browser-worker-image-policy OK - the
  fail-closed worker image guard failed, failing conjunct initially
  unknown.
- 596147a2 xtrace (job 123887220516, run 41001590079, later cancelled
  by replacement): 04:16:17.9535773Z `+test 2 -eq 1` - the first
  directory-count conjunct failed: a leftover directory inside
  `/ms-playwright` (extra directory name unknown; no claim made).
- db37a465 (runs 41002277149 + 41002277202, created
  2026-10-30T04:19:46Z): 30 check runs, 30 completed/success
  (section 2 N5). The 596147a2 CodeQL workflow run 41001590070 also
  completed/success.
- ROOT independent policy review
  (`/tmp/oap-083-9-a/root-db37-required20-plus10-independent-policy-review.json`,
  2026-10-30T04:55:24.788454Z) confirms the 20 correct-app required
  checks plus the 10 actual PG children all success at db37a465;
  qualification: implementation only - no final SELF/checks/runtime
  acceptance; material vendor-critical Chrome / new 29 High merge
  hold remains.

## 4. Security finding and the next bounded order

- ROOT material finding (scan review 2026-10-30T04:40:49.746213Z;
  close directive 2026-10-30T04:43:48.827458Z): 29 NEW High tuples,
  all `chrome@156.0.8078.47`, of which three
  (CVE-2026-118331, CVE-2026-118344, CVE-2026-118348) are
  vendor-CRITICAL per the Google 2026-10-27 stable-channel desktop
  release
  (<https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_0562499947.html>),
  52 security fixes, fixed Linux version 156.0.8078.73. Official CfT
  last-known-good metadata
  (<https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json>,
  document timestamp 2026-10-29T22:14:17.810Z) now lists stable
  156.0.8078.80 / revision 1706539 with linux64 archive
  <https://storage.googleapis.com/chrome-for-testing-public/156.0.8078.80/linux64/chrome-linux64.zip>;
  archive SHA256 NOT_YET_VERIFIED. No exploit or affected-code
  execution; the new patch is not locally or CI qualified.
- The 9a browser freeze is immutable: no browser code change under
  round a; the pinned CfT 156.0.8078.47 bytes remain in source.
- NEEDS_NEXT_ORDER: ROOT 083-9-b, bounded browser security fix on the
  SAME PR113 (amend same branch/PR per the increment-qualified round
  law): verify the official 156.0.8078.80 linux64 archive SHA256 from
  the official source before use, update the worker pin plus coupled
  policy/smoke/test literals, re-run necessary affected checks, then
  the remaining full gates (fresh ALL31, two-image probes, mandatory
  final CI, High re-audit, final SELF CI). No new order or signal
  until ROOT.
- PR112 remains OPEN ON HOLD / INACTIVE (not abandoned, not
  accepted); it resumes only by ROOT 083-8-j with a history-
  preserving main merge after 083/9 is accepted, merged, and remote
  main verified. Numeric 083 and the full product remain unresolved;
  no 084 advancement, no release or qualification claim, no cap
  retro-waiver, no history rewrite.

## 5. Procedure, publication, and remote proof

Done this round (actual receipts retained under
`/tmp/oap-083-9-a/` and `/tmp/oap-083-9-a/logs/`):

1. Activation: order byte-exact (299 lines / 17563 bytes, content
   SHA256 `bda7e86fad1229e3eea93497f4136c0d633ac57b9c67990ece694c3089846ea1`);
   one exact control OK (2 bytes `4f4b`, native 0, closed
   2026-10-30T02:05:28.677986Z) consumed by the existing control
   reader session 68477; no replay.
2. Four source commits pushed with bare push natives; remote branch
   head verified after each push (`git ls-remote`); ROOT
   independently verified full leaf maps (13 paths versus D18 at I9;
   6 paths at c445af6f; one character at 596147a2; 2 paths at
   db37a465).
3. Necessary affected checks at each source commit boundary
   (section 2 N3) with full streams, immediate child natives, raw
   `time.time_ns()`, and source SHA256 binding.
4. CI observations via the GitHub API, read-only (sections 2 N5 and
   3); Supply artifact 12954930004 reviewed by ROOT plus a secondary
   read-only audit
   (`/tmp/oap-083-9-a/root-current-security-artifact-initial-scan-review.json`).
5. No acceptance, merge, runtime work, local WHOLE/LOCAL6 (not
   required or claimed for this bounded two-image increment), Docker,
   or report/OK action before this publication.

To be executed before the single response OK (prospective at this
commit; actuals reported in the closure message):

1. The complete TEMP
   `oap/reports/.083-9-a-node-brotli-security-prerequisite.temp.md`
   linted with the exact repository markdownlint-cli2 0.23.2
   `--no-globs`: native 0, one file, zero issues, on the SAME
   complete bytes to be published.
2. Pre-hash/inode/size plus actual UTC and raw `time.time_ns()`;
   explicit file fsync; same-inode atomic rename to the sole report
   path in the PR worktree; parent-directory fsync; post-rename
   SHA256 compared equal to the linted TEMP.
3. Byte-exact report copy published to the canonical OAP root
   `/home/janezp/codex-work/slaif-agent-site/oap/reports/`
   (untracked in the PR112 checkout; not committed there); both final
   files' SHA256 equal to the linted TEMP.
4. Report-only SELF commit: sole parent literal I9
   `db37a4659277c3a405e375e05acc12c446a2a452`; sole new path this
   report; pushed with a bare push native.
5. Explicit remote proof: the actual PR API head SHA compared with
   SELF (rechecked if stale); SELF sole parent I9; sole report path
   present (`git diff --name-only I9..SELF`); remote report
   bytes/hash equal to the linted TEMP; PR113 OPEN with base main
   `d18b6e4c9423f61de99b516be90619bf2ab5d3e0`, unmerged.
6. ONE exact ASCII OK (2 bytes `4f4b`, no LF) written to the
   verified response FIFO inode 4470112 (ROOT sole 9-a response
   reader session 51936, OS PID 875352) and the writer closed; NEVER
   fsync a FIFO; no replay; no historical reader polled.
7. Exactly ONE byte-retaining next control reader retained: existing
   session 68477 (wrapper 864383 / head 864387) on control FIFO
   inode 4470111, retaining
   `/tmp/oap-083-8-i/next-control-signal.bin` and its `.native`
   sidecar; handle/PID/paths reported in the closure message.

## 6. Limitations and unresolved criteria

- N2 PARTIAL: runtime fixed-copy provenance (two-image probes) NOT
  RUN; CI-artifact scanner absence is not the full N2 contract.
- N3 PARTIAL: fresh ALL31 NOT RUN; the 31-command runner was drafted
  in memory only (unit 1 delivered for review, not approved) and was
  never written or executed; affected checks passed at each source
  boundary.
- N4 NOT RUN: `verify-node.sh` was never written; no Docker build,
  probe, or cleanup of any kind.
- N5 PARTIAL: required 20 + 10 PG children green at I9; final SELF CI
  fresh/unknown at publication; the 29 new Chrome High tuples remain
  unresolved and require ROOT review (no suppression, exception, or
  oracle weakening); vendor Chrome merge hold remains.
- Acceptance path: ROOT 083-9-b bounded browser security fix on the
  same PR113 (official archive SHA256 verified first), then the
  remaining gates; ROOT alone accepts and merges. No success claim
  anywhere in this report.

## 7. Forward errata (carried; no historical edits)

1. Push natives: the c445af6f push actual bare `git push` native 0 is
   in the 04:03:50Z journal; the 596147a2 push was captured as
   `push | tail` (tail native 0, not the git push native). Remote
   publication was independently proven via `git ls-remote` and ROOT
   leaf maps; no retry.
2. c445af6f changed six total paths (five gzip-specific plus
   `tools/compose/smoke.sh` legacy Corepack removal proof), not five.
3. The 03:21:23Z bare sh -n log line
   `time_ns_start=1793330483769867825000000` is a padded/formatted
   clock value, not raw `time.time_ns()`; later receipts use actual
   `time.time_ns()` (for example 1793333001473249187,
   1793333513595629370, 1793333958224886802).
4. Early piped captures (the 03:13Z sh -n via pipeline; the initial
   `uv sync | tail`) recorded wrapper/tail natives, not child
   natives; later rounds recaptured with bare commands plus immediate
   child natives (logs 09/10/12/13).
5. The 03:22Z printed smoke hash text "cce08779" was not a
   comparison; the remote blob matches the actually tested
   `b2d719d472f4d6cce08379a0c885232b767fd5b0810b91b8dd772e0230236652`.
6. 083/8-i response FIFO: the first writer delivered the exact OK
   before `os.fsync` on the FIFO fd raised EINVAL (a FIFO is never
   fsynced); the blocked duplicate writer (session 20633) was
   terminated (native 143) having written zero bytes; no replay.
7. The c445af6f packaging CI failure was the fail-closed image guard
   conjunct; xtrace identified the first directory-count conjunct
   (leftover directory under `/ms-playwright`; name unknown, no
   claim); fixed at db37a465 by whole-tree removal.
8. The I9 CI xz root cause: no xz native in the worker base (tar exec
   native 2) after a SHA-verified download; repaired with the
   official `.tar.gz` (SHA256 `eb6728e7...` verified).

## 8. Confirmations

- Scope: this round's commits change only the thirteen paths of
  section 1 (source plus order plus active) and this report (SELF).
  No other source, test, doc, dependency, lock, CI selector,
  authority, or infrastructure change. The PR112 checkout, its
  264-line WIP, all history, and the human files (`.codex/`,
  `CODEX-SESSIONS.md`, `codex.sh`) are preserved untouched. No second
  PR, no merge, no auto-merge, no reset/force/amend/rebase/clean or
  deletion of preserved history.
- Secrets: none in any artifact; no capability, cookie, DB URL,
  setup credential, or private-artifact content; no
  secret/Env/Args/Cmd/full-inspect logging; no exploit or
  proof-of-concept execution; external fetches limited to official
  archive/registry/metadata verification.
- Production: untouched; no production, deployment, or credential
  work.
- Local setup: uv 0.12.5; Python 3.13.14 (uv-managed, frozen lock);
  Node v24.22.1 official tar.gz (SHA256 `eb6728e7...` verified) at
  disposable scratch `/tmp/oap-083-9-a/verify/` on PATH for checks;
  pnpm 11.22.0 with the frozen lockfile; markdownlint-cli2 0.23.2 via
  npx on the Node v24.22.0 scratch from 083-8-h. No product
  dependency or lock change.
- Docs: `docs/DEPLOYMENT.md`, `docs/SUPPLY_CHAIN.md`,
  `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md` updated truthfully with
  verification PENDING; `docs/TESTING.md` intentionally unchanged.
- No complete-083, MVP, release, qualification, acceptance, merge, or
  next-objective advance claim.
