# 083-8-m terminal execution report (PARTIAL)

- Order: 083-8-m-qualify-frozen-candidate-with-node.md
- Order size: 245L / 16947B
- Order sha256:
  f8338660c4e5c3376c5b8aa25c5e98f7aa4e41f9e65c1304099ff5f705d4f158
- Control: one exact OK (2 bytes, hex 4f4b, no LF), closed
  10:41:41.363346Z, consumed by own reader 35889 (terminal
  native 0); capture4 inode 13494775, 2 bytes 4f4b plus EOF at
  10:41:41.363552Z, sha256
  565339bc4d33d72817b583024112eb7f5cdf3e5eef0252d6ec1b9c9a94e12bb3.
- Mode: AMENDED_EXISTING_PR; PR112 open; base main; branch
  oap/083-8-a-qualify-public-whole-session.
- Base main sha: 40cd172109a22ef5f342589b59a4293f35379651
- Worktree: /home/janezp/codex-work/slaif-agent-site-083-8-j
  (local alias oap/083-8-j-execution).
- Status: PARTIAL.

## Heads and commits

- Starting head: Sl 2bd14ebb4a764386495b2efbd11e3e2a7dad1537
  (l report-only SELF; sole parent Tl
  f94da5e2f663168ef37264d2d82f07429445d730; Tl parent Sk
  a3a2aa74f04f099463211ca8aa89151606260287).
- Literal implementation SHA: Im NOT CREATED. The single m
  ordered pass failed at command 4 (pytest native 1); the
  order first-failure stop applied; no source delivery.
- Truthful actual head at closure: Tm
  e3e3dcf0796e848e307d1df5154fb9c9683f95e4 (transcript-only
  checkpoint; exact m order plus active; no Im).
- Tm tree: 2052ddadaae4e17bac2ef43516a306416f63ff63
- Tm sole parent: Sl 2bd14ebb4a764386495b2efbd11e3e2a7dad1537
- Tm staged map: exactly 2 paths, byte-exact canonical, index
  otherwise empty (verified before commit):
  - oap/orders/083-8-m-qualify-frozen-candidate-with-node.md:
    245 lines added / 0 removed; blob
    3b39d00dc050a29843e0683c718f120a88e873fc; content sha256
    f8338660c4e5c3376c5b8aa25c5e98f7aa4e41f9e65c1304099ff5f705d4f158.
  - oap/active: 1 line added / 1 line removed; blob
    fa06bc2c58c5afaa8ea6443a792ffedc590127cd; content sha256
    fc8d7eaa05640ceffc8dfa75482a7ff828571357a8a880883c7f435c6b0b7241.
- Product blobs unchanged: diff Sl to Tm touches exactly the 2
  transcript paths; no source, test, or prior report changed.
- Report publication commit: SELF (report-only child of Tm;
  sole new path is this report; actual SHA is the remote PR
  head after the SELF push; receipt returned separately).
- Pushed commits this closure: Tm then SELF.
- Tm push (actual): bare, native 0, 2bd14eb to e3e3dcf;
  remote branch verified e3e3dcf via ls-remote; GitHub API:
  PR112 open, base main, head Tm; commit parents [Sl]; files
  exactly the 2 transcript paths (active 1/1, order 245/0).
- No source WIP published; no Im; no implementation commit
  this closure. Last implementation checkpoint remains Mj
  33b52e28619059fd5b44610a2a7dc525dba6103e (j round).

## Frozen WIP (uncommitted, unverified)

Four working-tree files remain dirty, frozen, unstaged, and
uncommitted; none staged, none committed, none published:

- tools/compose/smoke.sh: 1598L, sha256
  831a3cc894663899428a7fd64d93665d01a096784097686511d1c893842d2e19
- tools/compose/verify.py: 2874L, sha256
  c7c073bec1ad29be64cdcdcc774e64a83899ebd84c17a762e02f3ec7de4ce826
- tests/packaging/test_compose_smoke_contract.py: 1317L, sha256
  ee21cfec9567415813aac9d0ae68ce495ea9544971d8dc3bdc051e2f10e0c405
- docs/TESTING.md: 444L, sha256
  70fe07b29d7905746170857af51cf5a64f72893910a5004b17bf3fb699dca20d

Raw status at closure lists exactly these 4 files (M), nothing
else; the index is empty.

## m environment restoration (ENV-only order)

- Every quality call set: umask 077; approved PATH with
  /tmp/oap-083-9-a/verify/node-v24.22.1-linux-x64/bin first,
  then /tmp/oap-083-9-d/toolchain/bin;
  UV_PYTHON=/tmp/oap-083-9-c/py31318/install/bin/python3.13;
  UV_PROJECT_ENVIRONMENT set to the worktree .venv;
  UV_PYTHON_DOWNLOADS=never.
- Verified before the pass: node v24.22.1; uv 0.12.5;
  pnpm 11.22.0; venv interpreter Python 3.13.18 (inspected,
  not assumed).

## The one ordered affected pass (first-failure STOP)

Private 0600 streams under 0700 /tmp/oap-083-8-m/gates/:

- Command 1 ruff check: native 0; log m-pass-1-ruff-check.log,
  19B, sha256
  82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18.
- Command 2 ruff format --check: native 0; log
  m-pass-2-ruff-format-check.log, 28B (352 files already
  formatted), sha256
  7f2ab93433f9714756ebf76d1b866ab973c89474f671606677ed14c6e84dda16.
- Command 3 sh -n tools/compose/smoke.sh: native 0; log
  m-pass-3-sh-n.log, 0B (empty; sha256
  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855).
- Command 4 uv run --frozen pytest tests/packaging
  tests/supply_chain: NATIVE 1; log m-pass-4-pytest.log, 2979B,
  sha256
  577b848b34038e9c34a910bd969ecafc91b99b75ff48ef8f8e2e0a0beb106e2b.

- Result: 117 collected, 116 passed, 1 failed, 7.71s
  (Python 3.13.18, pytest 9.1.1).
- Failure: test_exact_safe_inventory_extracts_with_executable_
  mode in tests/packaging/test_browser_archive_extractor.py,
  line 50: extracted chrome-linux64/chrome mode 0o700 (448)
  versus asserted 0o755 (493).
- Node 24.22.1 was available for this pass; l's
  FileNotFoundError class of failure did not recur; the
  sibling extractor test passed; all 29 affected-module tests
  passed within the 116.
- 0o700 equals 0o755 masked by the mandated umask 077; the
  source applies the Node creation mode with the caller umask.
  The extractor and the failing test are frozen main-accepted
  code (b946d26, short; zero diff against main 40cd1721).
- NOT claimed as a proven production defect: the ENV
  disposition is under ROOT/peer review. No cause-fixed claim,
  no blame of accepted main, no future check PASS claim.
- Order first-failure stop applied: no second m pass, no
  repair, no rerun, no formatter, no source edit, no Im.
- Five boundaries measured around the pass; at each: HEAD Sl,
  tree 57b48f12 (short), frozen 4 WIP hashes exact.

## Criteria status (honest)

- I1 scoped source completion: PARTIAL. Scope held to the same
  4 files versus Sg; family gross 3466 (planning 3400 crossed
  at 3457 during l; the l complete-planning-forecast of 3518
  or less is preserved as an unverified claim per m order
  L68-69; the measured value fits HARD 3600). Source versus
  main: 22 paths / 5701 gross versus HARD 6000. Five-doc exact
  set versus D18: 285 versus HARD 500. Total paths: 48 at Tm
  (22 source plus 26 transcript), 49 at SELF (order max 49).
  Build applicability NOT_RUN (no Im). Remote Tm verified.
- I2 Im checkpoint: NOT_RUN (Im not created).
- I3 affected checks: actual natives as in the pass table
  (0 / 0 / 0 / 1); no fresh ALL31; NOT complete.
- I4 / I5 (Phase 2 scope): NOT_RUN.
- I6 literal If carry: NOT_RUN; literal If
  0f63e82d28ce714470577af998d2dca3df835a34 carry unchanged.
- I7 final SELF fresh CI: NOT_RUN; final SELF checks honestly
  PENDING and unobserved at publication.
- I8 this report: published per the m publication contract;
  SELF push, API byte proof, wire, and reader receipts are
  returned separately; nothing in this text preclaims them.

## Budget maps (measured, frozen candidate)

- Family (4 files) versus Sg: 3466 gross = docs/TESTING.md
  29/0 plus tests/packaging/test_compose_smoke_contract.py
  1132/4 plus tools/compose/smoke.sh 284/41 plus
  tools/compose/verify.py 1972/4 (added/removed; matches the
  l terminal measurement; unchanged by m).
- Source versus main 40cd1721: 22 paths / 5701 gross.
- Five-doc exact set versus D18: 285 (FOUNDATION_INTEGRATION
  108, TESTING 72, SUPPLY_CHAIN 96, INCREMENTS 5,
  MVP-PROGRESS 4).
- Transcript (exact activated a-m): 26 paths at Tm (13 orders
  plus 12 reports plus active), 27 at SELF.
- Frozen four unchanged (verified at stop): whole-session
  qualification 45cf7967 (short), test_foundation_ci
  56fdc040 (short, ends 81bc3), ci.yml 23ee9bc9 (short),
  run.sh 8b4a5e88 (short).

## Preserved deviations and errata (index)

m (this round):

- No new deviation: the stop is by design (order first-
  failure stop); exactly 4 ordered commands, no ad hoc
  probes.

l (carried; immutable l report at Sl):

- Formatter actual plus 234 (verify 148 plus test 86) versus
  the plus 0-30 forecast; recorded as underestimated.
- Complete planning forecast of 3518 or less: unverified
  claim, preserved as such.
- FULL reread after final edit: not observed; the full-read
  claim is qualified.
- Canonical copy omitted before wire; the late canonical
  repair 9dadd2 used precheck plus shell redirect, not O_EXCL
  (not exclusive; preserved, not retro-qualified).
- R2 note timestamp 10:11:25 inaccurate (R2 was fixed before
  pass 1; the printf note arrived after pass 2 commands 1-2).
- Wrong printf repair (second format argument), then correct
  single-format-argument fix; apply_patch wrong-path no-op;
  pass 2 incomplete (ruff 0 plus format 0, then aborted on
  the invalid printf) plus per-command metadata omissions;
  broad FIFO finds (deviation retained).
- pass 3: ruff 0 / format 0 / sh 0 / pytest 1 (Node
  FileNotFoundError class; 117 collected, 115 passed,
  2 failed, 8.41s; log 96902be3 short, 20634B).

k / j / f / g and earlier:

- See the immutable k, j, f, g reports and the ROOT control
  receipts (9k / 9l / 9j / 9f / 9g control directories); not
  duplicated here. Inherited key facts: k cap overrun
  3200 greater than 2900 and 5435 greater than 5200 with
  missed 2700 forecast and post-hard edits (09:16:32 and
  09:17:00); j late 2100 forecast, checkout-discard
  incident, failed replay d95c8f, global-pattern kill
  06:39:06, unqualified extra calls e373e6 / 60ac4d /
  adf5ca, push wrapper deviation.

## Tools, ownership, cleanup

- uv 0.12.5; Python 3.13.18 (venv inspected); Node 24.22.1
  (pass PATH and this report lint); pnpm 11.22.0 (verified,
  not a gate).
- Primary agent alone executed; no foreign process cleanup,
  no pattern kill, no deletion of retained evidence. (The
  06:39:06 global-pattern kill was a j deviation, indexed
  above.)
- Private streams: 0600 under 0700 /tmp/oap-083-8-m/gates/
  (4 pass logs plus this report lint log); l streams
  preserved.

## Claims and limits

- PARTIAL only. No Im, no source delivery, no acceptance, no
  merge, no all-green, no cause-fixed, no blame of accepted
  main, no full-product claim.
- The umask-077 versus extractor-mode interaction is
  unresolved; ENV disposition pending under ROOT/peer
  review.
- WIP uncommitted and unverified; final SELF CI PENDING and
  unobserved at publication.
- Prospective n (ENV-only: child pytest 022 / log parents
  077) is INERT; only after ROOT-verified m closure; no n
  work now.
- Full product goal remains ACTIVE (D5 to 084 to 080 real MCP
  through 091; the human owns intent, domain, risk, release).

## Publication procedure

- Tm push and remote verification: completed before this
  report (actual receipts in the heads section).
- PR body terminal rewrite: completed via GitHub API PATCH
  before the SELF commit; honest m terminal facts (head Tm,
  no Im, 117 / 116 plus 1 with the mode-assertion fact, umask
  077 context, frozen WIP, budgets, CI PENDING).
- This report: exclusive 0600 TEMP in the worktree reports
  directory, full literal read, pinned Node 24.22.1
  markdownlint-cli2 0.23.2 no-globs actual 0 / 1 file / zero
  issues, same-inode atomic rename with file and parent
  fsync, canonical exclusive O_EXCL copy before wire.
- SELF commit, SELF push, API byte proof, one response OK, and
  the fresh exclusive control reader are executed after this
  report; their actual receipts are returned separately. No
  preclaim of them in this text.
