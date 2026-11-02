# 083-8-n terminal execution report (PARTIAL)

- Order: 083-8-n-bound-test-umask-and-qualify-source.md
- Order: 245L / 16870B, sha256
  bb7d38364d085aca1d58454593005aafa8ac6dff29ea85042ac4911a5a1e15eb
- Control: one exact OK (2 bytes, hex 4f4b, no LF) to own reader
  96881 / PID 3866463; capture5 inode 13499230, sha256
  565339bc4d33d72817b583024112eb7f5cdf3e5eef0252d6ec1b9c9a94e12bb3,
  2 bytes 4f4b plus EOF at 11:23:00.043166Z; reader terminal
  native 0.
- Mode: AMENDED_EXISTING_PR; PR112 open; base main; branch
  oap/083-8-a-qualify-public-whole-session.
- Base main sha: 40cd172109a22ef5f342589b59a4293f35379651
- Worktree: /home/janezp/codex-work/slaif-agent-site-083-8-j
  (local alias oap/083-8-j-execution).
- Status: PARTIAL.

## Heads and commits

- Starting head: Sm a72a4a736109d7c9cde2c31208a04f023cdc70a6
  (m report-only SELF; sole parent Tm
  e3e3dcf0796e848e307d1df5154fb9c9683f95e4).
- Literal implementation head: In
  8106ee91da4562bac184d8ccff73e393e2983c21, tree
  dcbbead607c4557ee8d063be8e576e33ca6f347b, sole parent Sm.
- In staged map: exactly 6 paths (4 frozen WIP plus n order
  plus active); every staged blob equal to hash-object; raw
  status clean after commit; no transcript-only intermediate.
- In push: bare, native 0 (a72a4a7 to 8106ee9); remote verified
  via ls-remote and GitHub API (parents [Sm], exactly 6 files);
  PR112 open / base main / head In.
- Complete leaf map Sm to In: 1160 to 1161 leaves; exactly 6
  changed; all other leaves identical (sorted ls-tree diff:
  5 modified pairs plus 1 added).
- In-tree content hashes byte-exact: smoke.sh 831a3cc8...,
  verify.py c7c073be..., test module ee21cfec..., TESTING.md
  70fe07b2..., n order bb7d3836..., active 0c5c6900... (full
  hashes in the In checkpoint return).
- Report publication commit: SELF (sole NEW n report, sole
  parent In; actual SHA is the remote PR head after the SELF
  push; receipt returned separately; nothing here preclaims it).
- Pushed commits this closure: In (source checkpoint), SELF
  (report-only).

## The one fresh full pytest (changed environment)

- Subject: uv run --frozen pytest tests/packaging
  tests/supply_chain (exact m argv), child-only umask 022.
- 19-line transparent inline log-plus-exec launcher (recorded
  in the In checkpoint return; stdlib only; no new file):
  parent umask 077, verified 0700 euid parent, EXCL 0600 log,
  fstat verified, dup2 to stdout and stderr, child umask 022,
  exec timeout -k5 1800.
- OWN tool native 0; wall 8.45s; BEFORE boundary
  11:27:39.659215Z / AFTER 11:29:44.619133Z (HEAD Sm / tree
  641f1d54 / 6 intended paths / 4 hashes exact at both).
- Result: 117 passed in 8.08s; 0 failed / 0 skipped / 0 xfail /
  0 deselected (Python 3.13.18, pytest 9.1.1). The m mode
  assertion (0o700 versus 0o755) passes under mask 022.
- Log: /tmp/oap-083-8-n/gates/n-pass-4-pytest-childumask022.log,
  1544B, sha256
  802d19dbe85f0b08dc226108d81f1db2768d900eb85bcd13944fbd6ff3059444,
  regular 0600 euid under 0700 parent, verified after child.
- This is a historical local actual at the n moment; it does
  NOT prove the CI extractor result (current CI failed below).

## m three static carries (not rerun; not claimed at n/In)

- ruff check cfae19 / native 0 (19B, sha 82b3e6a6...), ruff
  format --check a79c24 / native 0 (28B, sha 7f2ab934...),
  sh -n smoke 2a61b6 / native 0 (0B, sha e3b0c442...);
  executed at Sl plus four WIP during m (10:44:08/37/53Z).
- Carry preconditions verified actual: exact 4 WIP hashes;
  worktree versus Sl differs only by the 4 WIP plus m
  transcript; Sl..Sm committed only 3 m transcript paths; full
  raw status with no new untracked source; exact m argv/tools/
  PATH/UV env; frozen four unchanged. No receipt-only repeat.

## Original-a ALL31 at ONE clean In (31/31 native 0)

- Exact original order/argv from the a order (index
  d043b036...; original order sha 843a6acd... verified);
  DIRECT per command, one quality per tool call, quality LAST,
  bounded timeout -k5, native unmasked, no post-echo/pipe/
  aggregation, no controller file.
- Each command: 13-line inline launcher; parent umask 077; log
  EXCL 0600 under 0700 euid parent /tmp/oap-083-8-n/all31;
  child umask 022; exec timeout; all 31 logs verified regular
  0600 euid after execution; no public logs.
- Shared boundaries: BEFORE 11:42:19.448895Z / AFTER
  11:54:05.266064Z; HEAD In / tree dcbbead6 at both; raw
  status clean at both; source frozen while children live.
- Environment: plain python resolves to the approved venv
  3.13.18; uv 0.12.5; node v24.22.1 (approved bin first);
  pnpm 11.22.0; UV_PYTHON / UV_PROJECT_ENVIRONMENT /
  UV_PYTHON_DOWNLOADS=never; locked plugins per the n run log
  (anyio 4.14.2, asyncio 1.4.0).
- Actuals (private log sha256 prefix / size, all native 0):
  - c01 uv lock --check: resolved 45 packages; 9f9cadb2 / 28B
  - c02 uv sync --frozen --all-groups: 44 packages checked;
    3a76845f / 30B
  - c03 ruff check: all checks passed; 82b3e6a6 / 19B
  - c04 ruff format --check: 339 files formatted;
    ff05b88c / 28B
  - c05 mypy: no issues in 317 source files; b8b75a52 / 45B
  - c06 pytest unit plus repository: 869 passed, 9 warnings,
    39.01s; 65b2d360 / 10083B
  - c07 uv build: sdist plus wheel to
    /tmp/slaif-agent-site-distributions; 856083db / 255B
  - c08-c17 ten app --check: all CHECK_OK
    (709e2c58 / 0caeea60 / bdefceea / 86fd69b6 / 0e648523 /
    3a839840 / bb316dcd / 7c23c62c / d21236ec / 8f399ea1)
  - c18 node --version: v24.22.1; 249baf63 / 9B
  - c19 pnpm --version: 11.22.0; a8608bac / 8B
  - c20 pnpm install --frozen-lockfile: done in 2.3s;
    aa2b456b / 1293B
  - c21 pnpm lint: eslint max-warnings 0 plus web lint;
    1dcc531f / 198B
  - c22 pnpm format:check: all matched files Prettier-clean;
    2649fa51 / 423B
  - c23 pnpm typecheck: all projects done; 8622df6b / 1141B
  - c24 pnpm test: browser-tool-contracts 24/24,
    composition-schema 19/19, root 36/36; e3b308ec / 12419B
  - c25 pnpm build: apps/web build done; f3d3f3c0 / 2689B
  - c26 pnpm licenses list --json: license JSON;
    0dc5e2e9 / 109086B
  - c27 compileall -q: quiet 0B; e3b0c442
  - c28 unittest discover: 88 tests OK in 0.297s;
    c4ee7315 / 187B
  - c29 check_repository: PASS repository policy;
    d2795d51 / 23B
  - c30 check_mermaid: 16 diagrams in 3 files, 609 Markdown
    files scanned, CLI 11.16.0; de5be4a7 / 94B
  - c31 markdownlint-cli2 0.23.2 all md: 603 files,
    0 issues; 411f1d8a / 293B

## Current In CI (terminal, authoritative)

- Workflow terminal: 30 checks, 29 SUCCESS, 1 FAILURE.
- FAILURE: Compose-and-edge-packaging, job 125251193179,
  run 41437596353. Peer safe failure excerpt: final unittest
  packaging 71 passed / 2 failures / 7 errors.
- ROOT source-backed candidate defects, recorded for the next
  order and NOT proven as exact cause; no local probe or
  source fix was authorized under n:
  - make_driver interpreter parent precedes the Docker shim in
    PATH, so the CI default Python may find real Docker; the
    exact CI-resolved binary is not yet proved.
  - Official Docker CLI v28.0.0 inspector.go
    (cli/command/inspect/inspector.go L103-105 / L124-125)
    appends LF unconditionally after the template; the current
    mount template adds row LF and the parser does not consume
    the formatter footer; current mocks are not wire-faithful.
- No broad cause-fixed / all-runtime / all-CI-pass claim.
  The n 117 local actual does not prove the CI 71 result.
  Final SELF fresh all-20-plus-10-plus-current-6 remains
  mandatory.

## Criteria status (honest)

- I1 scoped source completion: PARTIAL. Scope held (same
  4 files plus exact transcript); caps fit (below); source
  delivered in In; c07 build applicability actual; ALL31 at
  In actual.
- I2 Im checkpoint: NOT applicable. In was created directly as
  the source checkpoint (no transcript-only intermediate); no
  Im exists.
- I3 affected checks: local actuals as above (n pytest
  117/117 native 0; ALL31 31/31 native 0). CI authoritative:
  1 job FAILED; local success does not replace it.
- I4 / I5 (WHOLE / LOCAL6): NOT_RUN; no runtime inputs
  created; construction authority withheld pending ROOT
  CI-defect adjudication.
- I6 If carry: old-ENV carry only. Literal If 0f63e82d...
  Q80/FULL363/P7 applicability is ROOT-approved as historical
  old environment (old 70729 runner, Python 3.13.14
  subjects). Current host 3.13.18 and the actual product
  backend image 3.12.16 / Node 24.22.1 differ; fresh In
  Q/FULL/P7 required and NOT yet run.
- I7 final SELF fresh CI: NOT_RUN. Before SELF exists, checks
  are UNOBSERVED, not actual PENDING proof.
- I8 this report: published per the n publication contract;
  push/API/wire/reader receipts returned separately.
- P1-P7: local portions exercised within the n pass and the
  ALL31 actuals; final product-level acceptance remains with
  ROOT.

## Budget maps (measured, In)

- Family (4 files) versus Sg 89ab5ec8...: 3466 gross (3417/49)
  versus HARD 3600.
- Source versus main 40cd1721...: 22 paths / 5701 gross
  (default diff) versus HARD 6000; 5697 gross under
  --minimal (uv.lock algorithm difference only: minimal 39+35
  versus default 41+37, same bytes). Both labeled; no cap
  reset, no extra headroom.
- Five-doc exact set versus D18 d18b6e4c...: 285 gross
  (247/38) versus HARD 500.
- Paths at In: 50 = 22 source plus 13 orders plus 13 reports
  plus active plus n order; the n report brings exactly 51
  (max) at SELF.

## Preserved deviations and errata (index)

n (this round):

- Launcher construction failures (pre-exec; no ordered run):
  9406b3 (os.path.S_ISREG AttributeError; left 0B log renamed
  preserved as n-launcher-failed-construction-0B.log, sha
  e3b0c442) and 98e7ef (makedirs FileExistsError on the
  existing base). The recorded 19-line launcher is the one
  that exec'd.
- Metadata 175690: anyio.__version__ and
  asyncio.__version__ AttributeError inside echoes; outer 0
  does not make version claims valid; preserved as metadata
  error only. Locked plugin versions per the n pytest log
  (anyio 4.14.2, asyncio 1.4.0).
- Early exec yield_time_ms 120000 (c01-c05) and write_stdin
  polls 180000 (c05, c06): actual waits bounded, parameter
  deviation retained; later calls used <=60000.
- Source count erratum: --minimal 5697 / default 5701;
  uv.lock algorithm difference only; root 23784d assert
  mistake noted.

m / l / k / j / f and earlier:

- See the immutable m (a3f72229...), l, k, j, f reports and
  the ROOT control receipts (9k / 9l / 9j / 9f / 9g); not
  duplicated here. Inherited key facts: m pass 117/116 plus
  1 (extractor mode under umask 077) and the wire scratch
  syntax error (pre-FIFO); l canonical copy omission plus
  late repair 9dadd2 (precheck plus redirect, not O_EXCL);
  k cap overrun 3200 greater than 2900 and 5435 greater than
  5200 with missed 2700 forecast; j late 2100 forecast,
  checkout-discard, failed replay d95c8f, global-pattern kill
  06:39:06, unqualified extras e373e6 / 60ac4d / adf5ca, push
  wrapper.

## Claims and limits

- PARTIAL only. No acceptance, no merge, no all-green, no
  cause-fixed, no exception-safety, no universal no-secrets or
  no-foreign-cleanup claim, no new product qualification.
- The n 117 and ALL31 are historical local actuals at In; the
  current CI failure is authoritative and unresolved here.
- WHOLE / LOCAL6 NOT_RUN; no runtime inputs created.
- The next order is authorized by ROOT alone after formal n
  closure; no anticipated next letter was implemented.
- Full product goal remains ACTIVE (D5 to 084 to 080 real MCP
  through 091; the human owns intent, domain, risk, release).

## Publication procedure

- In push and remote verification: completed before this
  report (actual receipts in the heads section).
- PR body terminal rewrite: completed via GitHub API PATCH at
  12:03:35Z before the SELF commit (honest n terminal state).
- This report: exclusive 0600 TEMP in the worktree reports
  directory, full literal read after any edit, pinned Node
  24.22.1 markdownlint-cli2 0.23.2 no-globs actual 0 / 1 file /
  zero issues, same-inode atomic rename with file and parent
  fsync, canonical exclusive O_EXCL copy before wire.
- SELF commit, SELF push, API byte proof, one response OK, and
  the fresh exclusive control reader are executed after this
  report; their actual receipts are returned separately. No
  preclaim of them in this text.
