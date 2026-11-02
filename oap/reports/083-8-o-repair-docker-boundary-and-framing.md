# 083-8-o terminal execution report (PARTIAL)

- Order: 083-8-o-repair-docker-boundary-and-framing.md
- Order: 261L / 18147B, sha256
  ace0b3c67cc1a99e5b748049214c48159e0c10d636cdeb8cac868e55cdd92ca5
- Control: one exact OK (2 bytes, hex 4f4b, no LF) to own reader
  65294 / python PID 3894036 / bash 3894035; capture6 inode
  13509116, 2 bytes 4f4b plus EOF at 12:16:22.783144Z; reader
  terminal native 0 (chunk 55af17).
- Mode: AMENDED_EXISTING_PR; PR112 open; base main; branch
  oap/083-8-a-qualify-public-whole-session.
- Base main sha: 40cd172109a22ef5f342589b59a4293f35379651
- Worktree: /home/janezp/codex-work/slaif-agent-site-083-8-j
  (local alias oap/083-8-j-execution).
- Status: PARTIAL.

## Heads and commits

- Starting head: Sn 053d7a5a0c7305b1b488ef5d646a2edf25a75212
  (n report-only SELF, sole parent In
  8106ee91da4562bac184d8ccff73e393e2983c21).
- Literal implementation head: To
  f9233864f1d4620d4e76eab71bf825c94aadf791, tree
  9c9e0476a19f8253f880b2e61d1e97b8ab6b5604, sole parent Sn. To is
  a NONACCEPTED partial checkpoint: it publishes the attempted
  bounded work, is not a successful Io, is not acceptance, and
  authorizes no further implementation.
- To staged map: exactly 4 paths (tools/compose/verify.py,
  tests/packaging/test_compose_smoke_contract.py, the immutable o
  order, oap/active); every staged blob equal to its hash-object
  (9e86eafa / 93ab3937 / e30bd999 / b18c7e3e); index empty before
  staging; raw status clean after commit.
- To push: bare, native 0 (053d7a5 to f923386); remote verified by
  ls-remote and GitHub API: parents [Sn], exactly 4 files, remote
  blob shas and raw content bytes equal the worktree (verify.py
  fc4dd4e2..., test module d4f4a0bc...).
- Complete leaf map Sn to To: 1162 to 1163 leaves; exactly the 4
  paths above changed; all other leaves identical (ROOT receipt
  /tmp/oap-083-8-o-control/root-To-independent-checkpoint-review.json).
- Report publication commit: SELF (sole NEW o report, sole parent
  To; the actual SHA is the remote PR head after the SELF push;
  receipts returned separately; nothing here preclaims it).
- Pushed commits this closure: To (NONACCEPTED partial
  source/transcript), SELF (report-only).

## Applied work (only the two authorized paths)

- verify.py fc4dd4e22a24d303d92b24a06241fa39803360483caa2c53ec8e9b43fe172557:
  _lifecycle_project_mounts now consumes the pinned docker CLI
  v28.0.0 template inspector single formatter footer LF separately
  from per-row LFs: the footer is required; zero mounts render the
  footer alone and project to []; a missing or duplicated footer,
  or any blank data line, is malformed and is never stripped. The
  stale empty-mount comment was replaced with the official
  inspector.go source reference.
- Test module
  d4f4a0bccb5ef55870fa90624e9835d8ba22e9fd475811be2a14659cc20c46c2:
  F1: the make_driver PATH now places the shim bin dir
  unconditionally before the interpreter dir and the inherited
  PATH. One new real-driver regression
  (test_real_driver_shim_wins_over_shared_interpreter_docker): a
  private 0700 directory holds a disposable python symlink
  (disposable interpreter entry) beside a poison docker executable
  (touch $LIFECYCLE_SHIM_STATE/poison-ran, exit 0);
  mock.patch.object(sys, "executable", ...) makes the production
  make_driver treat that shared directory as the interpreter dir;
  the real driver (sh, real smoke.sh helper_run, active=0) runs;
  the assertions are returncode 0, poison marker absent, and the
  shim-written run-argv exact (9 entries, -c body as one
  argument). It passed in both pytest runs. The old-priority
  failure remains static inference (the poison would resolve
  before the shim and no run-argv evidence would be written); it
  is not an observed old-code execution.
  F2: the SHIM mount branch emits the row LF plus the single
  footer LF; MOUNTS_LINE is now the framed one-mount text;
  _fake_docker and run_chain take a mounts_text parameter; the
  mount test extends to valid zero/one/two frames, validly framed
  field negatives, four malformed frames (missing footer,
  duplicated footer, blank data line, empty), and zero/two real
  producer/reader/auditor round-trips through the actual chain.
- Frozen and unchanged at To (blob/leaf verified): smoke.sh
  831a3cc8..., TESTING.md 70fe07b2..., qualification 1844L
  45cf7967..., repository tests 432L 56fdc040..., ci 469L
  23ee9bc9..., run.sh 477L 8b4a5e88..., all pins, locks, SDK and
  CI unchanged.

## Forecast sequence (honest, as executed)

- Deviation: the /tmp/oap-083-8-o/forecast/ candidate mirrors
  (test.candidate 53901B, verify.py.candidate 108536B, 0600 under
  a 0700 directory) were written BEFORE the complete in-memory
  forecast. They are preserved unchanged, were never
  executed/imported/compiled/formatted/linted, and no additional
  mirror/helper/builder was created.
- Measurement 1 (chunk 1776ef): family 3598, margin 2, one known
  89-char line, source 5833 default / 5829 minimal. This was NOT
  a complete forecast: the formatting allowance and the known
  line fix were still open.
- Refined candidate (second forecast call): family 3596, zero
  lines over 88, NO explicit formatter reserve; source 5831 /
  5827.
- Applied byte-exact (chunk 2bca92): family 3596; frozen shas
  re-verified.
- Optional formatter construction (chunk ec34e6, native 0, log
  10869b88 42B "1 file reformatted, 1 file left unchanged"): the
  test module MOUNTS_LINE collapsed 3 to 1 lines and one blank
  line was removed; family 3596 to 3593. This correction happened
  after the source write and is not a retro-approval of the
  unreserved 3596.
- Actual pytest invocations in o: exactly two.

## Ordered affected passes (exact argv; two authorized, exhausted)

Every quality call: approved PATH (Node 24.22.1 bin first, then
toolchain), UV_PYTHON 3.13.18, UV_PROJECT_ENVIRONMENT worktree
.venv, UV_PYTHON_DOWNLOADS=never, umask 077, fresh EXCL 0600 logs
under the 0700 gates parent, bounded timeout -k5, native
unmasked, quality LAST, yield <=60000 including polls. The
pytest child ran with explicit umask 022; log creation preceded
the child mask.

Pass 1 (source before the one-line wiring repair):

- c1 ruff check: native 0 (chunk 9e06e6); log o-pass1-c1-ruff-check.log
  inode 13509726, 19B, sha 82b3e6a6..., "All checks passed!".
- c2 ruff format --check: native 0 (chunk fdb546); log 13509727,
  28B, sha 7f2ab934..., "352 files already formatted".
- c3 sh -n smoke.sh: native 0 (chunk 6224bc); log 13509728, 0B,
  sha e3b0c442....
- c4 attempt 1 (chunk 79a408): PRE-exec launcher construction
  failure, os.path.S_ISREG AttributeError (S_ISREG lives in the
  stat module, not posixpath); it repeats the n 9406b3 error
  class; the pytest child never ran; the 0B log was created EXCL
  before the assert.
- c4 attempt 2 (chunk 285425): native 1, wall 8.4584s; log
  13509772, 5688B, sha 43618c92...; 118 collected, 117 passed,
  1 failed, 8.16s. Failure: the zero round-trip meta carried the
  standard mount because _fake_docker still returned the
  MOUNTS_LINE literal (the mounts_text parameter was declared but
  not wired into the fake body). The 0B log was reopened
  non-EXCL (O_WRONLY|O_NOFOLLOW, pre-size-0 asserted) for this
  attempt, not recreated EXCL.
- One-line content repair (authorized named in-scope repair):
  return 0, MOUNTS_LINE became return 0, mounts_text (sole
  occurrence); family unchanged at 3593.

Pass 2 (source-changed, full 4 commands):

- c1 ruff check: native 0; log o-pass2-c1-ruff-check.log
  inode 13513324, 19B, sha 82b3e6a6...
- c2 ruff format --check: native 0 (chunk 1e2acb); log 13513325,
  28B, sha 7f2ab934...
- c3 sh -n smoke.sh: native 0 (chunk 5c0734); log 13513326, 0B,
  sha e3b0c442...
- c4 pytest (chunk fda94e): native 1, wall 8.6761s; log
  13513362, 5599B, sha 709af7b6...; 118 collected, 117 passed,
  1 failed, 8.31s. Failure: the row2 named-mount row begins with
  SEP and renders SIX fields; verify.py line 462 rejects the
  field count in the two iteration; the zero iteration precedes
  it and passed. This is NOT a demonstrated zero-frame parser
  defect.
- Per the order, the second pass failure stops: no third pass and
  no further product edits occurred.

ROOT fixture audit (recorded as next-letter repair requirements,
no current edits): field_bad3/4 have FOUR fields so the
type/bool oracle is not reached; field_bad6 has FIVE fields and
fails bool rather than extra count. row2 must drop its leading
SEP (data-verified: name plus 4 values = 5 fields, and the
two-frame wire text then parses to two well-formed rows).

## Boundary metadata (honest shared snapshots)

Both passes: HEAD Sn 053d7a5 / tree 9203fad1 at every boundary;
raw status constant (M active, M test module, M verify.py, ?? o
order); the four source hashes stable within each pass (the test
module hash changed only at the wiring repair between passes:
5958536e in pass 1, d4f4a0bc in pass 2).

- Pass 1: BEFORE-0 12:37:24.905274Z, BEFORE-1 12:37:38.369548Z,
  BEFORE-2 12:37:45.393036Z, BEFORE-3 12:37:54.692419Z,
  AFTER-4 12:38:33.207035Z.
- Pass 2: BEFORE-0 12:39:26.320612Z, BEFORE-1 12:39:41.350709Z,
  BEFORE-2 12:39:46.897376Z, BEFORE-3 12:39:57.389316Z,
  AFTER-4 12:40:12.961453Z.
- Tool wall-time fields for c1-c3 (both passes) reported 0.0001s;
  recorded as observed, a tool timing quirk, not a duration claim.
- UNOBSERVED, not reconstructed: ruff version, sh -n and uv
  versions, per-command elapsed beyond the wall-time fields.

## Criteria status (honest)

- I1 scoped source completion: PARTIAL. The two authorized paths
  are applied and UNVERIFIED: both authorized affected passes
  failed at c4; the next letter owns the fixture repairs and
  re-qualification.
- I2 Im checkpoint: not applicable. No transcript-only
  intermediate exists; To is the NONACCEPTED partial
  source/transcript checkpoint.
- I3 affected checks: FAILED (pass 1 c4 native 1; pass 2 c4
  native 1; c1-c3 native 0 both passes).
- I4 / I5 (ALL31 at To / WHOLE / LOCAL6): NOT_RUN; no runtime
  inputs created.
- I6 If carry: old-ENV carry only. Literal If
  0f63e82d28ce714470577af998d2dca3df835a34 Q80/FULL363/P7
  remains historical old-environment applicability; current host
  3.13.18 and backend image 3.12.16 / Node 24.22.1 differ.
- I7 final SELF fresh CI: UNOBSERVED. No CI at To was run or
  observed; the last observed CI state is the In 29/30 terminal
  with the Compose-and-edge-packaging FAILURE (job 125251193179,
  run 41437596353).
- I8 this report: PARTIAL, published per the o publication
  contract; push/API/wire/reader receipts returned separately.
- P1-P7: the local portions remain in the 117-pass set; final
  product-level acceptance remains with ROOT.

## Budget maps (measured at To with literal SHAs)

- Family (4 files) versus Sg 89ab5ec8...: 3593 gross (smoke
  284/41, test 1249/4, verify 1982/4, TESTING 29/0) versus HARD
  3600; pre-format was 3596.
- Source versus main 40cd1721...: 22 paths / 5828 gross default
  and 5824 gross under --minimal (uv.lock algorithm difference
  only: minimal 39+35 versus default 41+37, same bytes) versus
  HARD 6000; both labeled, no extra headroom.
- Five-doc exact set versus D18 d18b6e4c...: 285 gross versus
  HARD 500 (TESTING.md frozen).
- Paths at To: 52 = 22 source + 30 current a-o transcript (15
  orders + 14 reports + active); 53 at SELF (max). The 550
  orders+reports count observed mid-round counts ALL repo
  transcript history, not the current objective; it is qualified,
  not a cap input.
- Chunk 94e4ec committed successfully but its later cap block used
  the literal nonexistent revision To; the resulting fatal
  bad-revision and awk zeros are NOT cap proofs. The 7f677f
  literal-SHA map is the actual.

## Preserved deviations and errata (index)

o (this round):

- Write-before-forecast mirrors preserved at
  /tmp/oap-083-8-o/forecast/ (never executed; see forecast
  section).
- The refined 3596 candidate carried no explicit formatter
  reserve; the construction call measured the actual -3.
- 79a408 PRE-exec os.path.S_ISREG launcher failure (repeats the
  n 9406b3 class); 285425 reused the 0B log non-EXCL with a
  pre-size-0 assert; actual pytest invocations exactly two.
- Pass 1 c4 failure: fake mounts_text wiring omission. Pass 2 c4
  failure: row2 six-field fixture.
- Tool wall-time field 0.0001s for c1-c3 recorded as observed.

n / m / l / k / j / f and earlier:

- See the immutable n report aa5db567... (266L/12387B, including
  its forward errata: 71 RUN not 71 passed, If-only carry, n 117
  at Sm+WIP, ALL31 at In, the 11-request yield index, the 54c410
  assert omission, the open-time reader metadata), m
  a3f72229..., l, k, j, f reports and the ROOT control receipts
  (9k / 9l / 9j / 9f / 9g / 9n / 9o); not duplicated here.

## Claims and limits

- PARTIAL only. No acceptance, no merge, no all-green, no
  cause-fixed, no new product qualification. The source is
  UNVERIFIED: the two authorized affected passes failed at c4 and
  the next letter owns the fixture repairs.
- No CI rerun or cancel was performed; no ALL31, WHOLE, LOCAL6 or
  SELF current-6 execution occurred in o.
- Full product goal remains ACTIVE (D5 to 084 to 080 real MCP
  through 091; the human owns intent, domain, risk, release).
- The next letter is authorized by ROOT alone after verified o
  closure; no anticipated next letter was implemented.

## Publication procedure

- To push and remote verification: completed before this report
  (receipts in the heads section).
- This report: exclusive 0600 TEMP in the worktree reports
  directory, full literal read after any edit, pinned Node
  24.22.1 markdownlint-cli2 0.23.2 no-globs actual 0 / 1 file /
  zero issues, same-inode atomic rename with file and parent
  fsync, canonical exclusive O_EXCL copy before wire.
- SELF commit, SELF push, API byte proof, one response OK, and
  the fresh exclusive control reader are executed after this
  report; their actual receipts are returned separately. No
  preclaim of them in this text.
