# OAP 083-6-c execution report — close publication protocol (CLOSURE_ONLY) (COMPLETE)

## 0. Status

| Field | Value |
| --- | --- |
| Round | 083-6-c (numeric objective 083, increment 6, round letter c) — CLOSURE_ONLY, transcript-only |
| Order | `oap/orders/083-6-c-close-publication-protocol.md` (174 lines, 11046B) |
| Order SHA-256 | `e5d90924a2882ae96a7dcc75af57fdabb0324c4ed57f5ddbd8a74e3f447ddc5b` |
| `oap/active` bytes | `083-6-c` + LF (8 bytes, hex `3038332d362d630a`) |
| PR mode | AMENDED_EXISTING_PR (PR #110; branch `oap/083-6-a-stabilize-frozen-review-controls`; base `main` at `f35ec75319afd966d02ee2b7b8cb1db1eb4cd144`; starting remote head = b report-only S `e128177270dbace463fdf095a3e8bfa2a39160b1`, sole parent the tested I `a4206939bc971012be327564dd8d3bcb3db892b0`) |
| Status | **COMPLETE** at literal non-report commit J `bcad00f2d37ec65ed7efff0dfa875ca61eaf4ada`: F1 same-filesystem complete prelint and atomic rename executed (section 3); F2 finite b-report corrections recorded with actual evidence (section 4); F3 exact full-tree equivalence proven and qualified local results carried as historical subjects (section 5); F4 fresh c-S final CI requirement stated and honestly pending at publication (section 6). Zero product/test/doc/config/dependency/workflow change; this round is transcript-only. |
| Literal implementation SHA | `bcad00f2d37ec65ed7efff0dfa875ca61eaf4ada` (J; this round is transcript-only, so J is the round's implementation head) |
| Report publication commit | SELF (this report; sole path; first parent exactly J `bcad00f2d37ec65ed7efff0dfa875ca61eaf4ada`) |

## 1. Identity, control handshake, governing reads

- ONE c control OK: root writer PID 784345 wrote exactly 2 bytes `4f4b` (no LF)
  to strategic `control.fifo` (inode 4470111) at 2026-10-26T03:22:56.235818Z and
  closed (receipt `/tmp/oap-083-6-c/control-written.json`); consumed ONCE by the
  primary reader at 2026-10-26T03:22:56Z. No control replay.
- The b final OK was received by root at 2026-10-26T02:55:30.605348Z; root
  reader 78363 is TERMINAL and was never polled or replayed. No `response.fifo`
  write of any kind occurred during c until this final publication.
- Read FULL: this c order; the finite root review
  `workorders/083-6-b-published-report-evidence-adjudication-2026-10-26.md`;
  all a/b orders and a/b reports (prior rounds); coding AGENTS/protocol and
  compact architecture. Full `ARCHITECTURE.md` NOT loaded.
- The b final report (652L/47105B, SHA-256
  `c6780288e520ad7317e12fe3b8847bac99a4fa7e03a30ec0c8cbe765935b8bcd`, at S
  `e1281772`) was fully read by root with remote sole parent/path/bytes
  independently verified. It remains IMMUTABLE. Its b-S all-30 checks and the
  actual current six-image artifact 12625340443 (SHA-256
  `5bf718caa8b8c3a77b4ffbc327020ea8bbcc4dcc26dd55a2ff2d00ddac9d558f`; 53
  checksums / 54 files; zero raw Critical/ignored/exceptions; 19 High full
  six-tuples equal accepted 107) are b-S evidence, NOT future c-S proof.

## 2. PR and source identities

- PR #110 (OPEN, unique 083/6), base `main` at `f35ec753...`, head branch
  `oap/083-6-a-stabilize-frozen-review-controls`. Fetch/reconcile at round
  start: remote head = b S `e1281772...`, state OPEN.
- J (this round's non-report implementation commit):
  `bcad00f2d37ec65ed7efff0dfa875ca61eaf4ada`, first parent exactly b S
  `e1281772...`, changing ONLY the c order (added) and `oap/active`
  (modified) — full-tree proof in section 5.
- c S (report-only): sole changed path = this report; first parent exactly J.
- Pushed commits this round: J `bcad00f2d37ec65ed7efff0dfa875ca61eaf4ada`
  (order + active, committed 2026-10-26T03:27:10Z and pushed to the remote
  branch in the same owned invocation) and this report-only S (commit SHA
  recorded in the F1 sidecar at push time; remote verified).
- Actual J current-CI observation (full coding protocol; this is an ACTUAL
  observation at J, not the c-S requirement): at 2026-10-26T03:35:08Z, of the
  25 check-runs created at J, 18 are COMPLETED/SUCCESS and 7 are
  in_progress; the remaining required checks were not yet created at the
  observation instant. J is a transcript-only intermediate commit; the
  mandatory fresh all-30 CI proof is required at c-S (section 6) and may
  honestly be pending at publication.
- No implementation, runtime, dependency, test, current-document or feature
  edit in J or S; CLOSURE_ONLY applies to all c work.

## 3. F1 — same-filesystem complete prelint and atomic publication (corrected protocol)

- b publication deviation (disclosed; no retrospective claim cures it): the
  complete b draft was linted at `/tmp/oap-083-6-b/report-draft-b-v1.md`
  (st_dev 43), then copied to a different-filesystem repository temp (st_dev
  2304) and renamed. The complete bytes were linted zero and published
  atomically, but the linted path was NOT the same-filesystem temp. The b
  report says "no protocol incidents"; that is corrected HERE in this new
  report only (F2.9).
- c execution (all actual; no hypothetical commands/exits):
  - COMPLETE report temp created directly inside repository `oap/reports/`:
    `.083-6-c-close-publication-protocol.md.tmp.20261026T0331` (hidden temp;
    refuse-if-exists; no formal-path draft chunks).
  - Same-filesystem proof: `st_dev(temp)` = 2304 and
    `st_dev(oap/reports)` = 2304, verified equal (recorded in
    `/tmp/oap-083-6-c/f1-publication-sidecar.json`, 0600).
  - Exact repository lint on THAT exact complete temp file (command on one
    line): `npx --yes markdownlint-cli2@0.23.2 --config /home/janezp/codex-work/slaif-agent-site/.markdownlint-cli2.jsonc --no-globs /home/janezp/codex-work/slaif-agent-site/oap/reports/.083-6-c-close-publication-protocol.md.tmp.20261026T0331`
    - Attempt 1 (after st_dev fill-in): native rc 1 — 2×MD050/strong-style,
      both caused by the underscore-bearing draft token on that very line,
      not by substantive content; output preserved unmodified at
      `/tmp/oap-083-6-c/lint-attempt1.log`.
    - After replacing that token with this narrative, the FINAL complete-file
      lint of the same temp file: native rc 0, "Linting: 1 file",
      "Summary: 0 issues" (full output in the sidecar). Content changed after
      attempt 1, so the complete same file was re-linted; the final lint
      covers the exact final bytes.
  - SHA256 of the complete linted temp was recorded; the SAME file was then
    closed, fsynced, atomically renamed (same inode/filesystem, no
    cross-filesystem copy) to
    `oap/reports/083-6-c-close-publication-protocol.md`; the parent directory
    was fsynced; the post-rename SHA256 was verified identical to the
    pre-rename SHA256 (both values recorded in the sidecar; the final blob
    hash is independently computable from this commit).
  - No lint of a different copy, no partial publication, no prior overwrite.

## 4. F2 — finite b-report corrections (recorded in this new report; b immutable)

- F2.1 non-Error thrown values (b section 3): such values ARE temporarily
  captured in memory during classification; the supported privacy property is
  no raw diagnostic serialization or persistence, not "never stored at all".
  The typed fixed fallback (`unclassified body failure`) and failure-presence
  flags are unchanged and sound.
- F2.2 atomic tuple lineage and governance ordinal (b sections 4/8.3): the
  atomic same-moment `{wrappers, distinct, missingId}` in-page tuple is the
  R3/`71ba816b` committed implementation (the fix was identified during the
  R2 WIP review; b section 4's "root-identified R2 fix" phrasing is corrected
  to R3). WHOLE2's governance Puck contract was the FOURTH A420 governance
  invocation — after the f1 prerequisite, the f2 prerequisite, and WHOLE1's
  governance phase — not the third; WHOLE1 remains a FAILED whole invocation
  despite its passing browser phase.
- F2.3 WHOLE2 creation window (b section 8.3): the INITIAL 15 containers were
  created 2026-10-26T02:24:26.303..692Z (secrets-init
  02:24:26.303483003Z through nginx/browser-worker 02:24:26.692Z, per the
  watcher's first samples). Mid-run recreations carry NEW container IDs and
  later creation times (control-api 02:38:18.751850776Z; render-api
  02:39:09.176592117Z and 02:40:21.211538399Z; all tracked in the watcher).
  b's "ALL containers created 02:24:26.303-26.692Z" is overbroad; no
  unchanged-container lineage is claimed.
- F2.4 diagnostic retention (b sections 4/8.2/10.3): f2's private governance
  JSON is retained, 674B, full SHA-256
  `23b77907e021d414db7be10c8c0f484f4849ca75e8926d6da222b63517b211c8`.
  WHOLE2 does NOT retain that JSON: `tools/compose/e2e.sh` reuses its
  temporary output directory across separate Playwright invocations and
  deletes it in cleanup; no WHOLE2 governance JSON is counted as evidence,
  and packaging has no governance diagnostics. b section 10.3's v2
  blanket-retention claim is unsupported and is not repeated; no "every
  terminal path exercised" claim is made. The REQUIRED B2 diagnostic baseline
  JSON is actually retained: 674B, SHA-256
  `c42fc13c893c818cd1ffdc4c6f141a17a1c86c74a6fd0b26b9ae33aba3be8f8c`
  (`b2-run/output-preserved/...`), verified this round. The f1 deletion and
  the B2 metadata limits stand; no file was ever reconstructed.
- F2.5 I24a LOCAL6 carry (b section 11): the historical I24a LOCAL6 is
  carried through the enumerated accepted transcript-only I24a-to-f35 edge
  plus the exact f35-to-S permitted path/mode/blob edges (section 5). Fresh
  b/c-S CI six-image scans are SEPARATE current mandatory evidence, NOT the
  source of a historical local carry. Neither is called a local rerun at
  A420; no vulnerability recency is carried.
- F2.6 teardown semantics (b section 13): the focused f1/f2 harnesses do NOT
  tear down at END via a smoke EXIT trap; each next gate tears down at START
  (`down --volumes` then `up -d --wait` per invocation). WHOLE runs DO clean
  up on EXIT. Actual fresh-START provenance (raw per-container resolved image
  IDs/creation times captured while the owned stack was live) and the final
  02:52:40Z zero-owned-resources check control; no invented timing.
- F2.7 dependency count (b section 14.1): the backend has NINE direct
  main-group Python dependencies, not six — AGENTS lists foundation plus six;
  main-group `alembic==1.19.1` and `sqlalchemy==2.0.52` additionally exist
  (actual `pyproject.toml` `[project] dependencies` at J, verified this
  round). Test-group `httpx`/`certifi` are excluded from the application
  venv; the separate system pip 25.0.1 and its ensurepip bootstrap wheel
  contain affected certifi 2024.08.30 twice (section 7).
- F2.8 C1 unit timing (b section 9): the a-round clean ALL31 unit timing was
  867 passed / 3 warnings / 34.60s (a-round I9d subject); the current b clean
  ALL31 unit timing was 867 passed / 3 warnings / 33.56s (A420 subject).
  Both numbers remain correct for their actual subjects and are not
  interchangeable.
- F2.9 b publication deviation: as disclosed in section 3. The b report's
  "No protocol incidents" statement is corrected here; no protocol-clean
  claim is made for b. This transcript-only c round exists to close that
  protocol gap.

## 5. F3 — exact full-tree equivalence and carried subjects

- J vs b S full-tree comparison (ALL paths; no exclude-all-OAP shortcut;
  `git diff --minimal` name-status + raw): EXACTLY 2 paths differ —
  ADDED `oap/orders/083-6-c-close-publication-protocol.md` (100644, blob
  `5ed4bb9`, 174/0) and MODIFIED `oap/active` (100644 → 100644, blob
  `83b5d09` → `c657ce0`, 1/1). Every other path/mode/type/blob is identical
  to b S — production/builders/locks/policy, the two named tests, the two
  current docs, and all prior transcripts included.
- c S vs J: EXACTLY 1 path (this report, 100644). No other identity changes;
  had any appeared, this round would have STOPPED before publication per
  order.
- Cumulative vs base main `f35ec753` at c S: exactly the two named tests, the
  two current docs, and SEVEN transcript identities (a/b/c orders, a/b/c
  reports, `oap/active`); production/config/locks/migrations/generated/
  workflow ZERO. Test gross 672/700 and docs gross 76/100 unchanged.
- Carried under this exact equivalence — HISTORICAL executions at their
  literal subjects, NOT rerun at J/S:
  - A420 CLEAN ALL31 (clean isolated worktree): 31/31 native 0, overall 0;
    unit 867 passed / 3 warnings / 33.56s (window
    2026-10-26T01:37:57.736698..01:43:49.256881Z).
  - A420 two FULL focused parity invocations: f1 142708ms native 0 (log
    10307B, SHA-256 `7c47d7d16ad399b44cc87bbe7c98c428c1962429fdf24fd11c567ca65f3f8772`),
    f2 139084ms native 0 (log 17756B, SHA-256
    `0f9b6f3148904ee4cb611dee3eb4d8dbeb50d56d768cf2510e01e44d25dfcf37`).
  - A420 corrected WHOLE2 (root decision 2026-10-26T02:22:06Z): native 0,
    40 browser records / 19 projects / 49 packaging tests / `compose-smoke:
    OK` (log 60779B, SHA-256
    `c7059c941fed22fd2b72f23206daea4847bb5787b7b9c951b92235584631c5a9`).
  - B2 actual ONE diagnostic suite (subject R3 `71ba816b`): NONREPRO
    (category D); the 674B JSON is retained (F2.4).
  - R6 controlled native transport proof (a round, attempt3 PASSED): carried
    only via the byte-identical submit-response binding core in the parity
    spec (verified in the b round).
  - I24a FULL 347 + coherent RC7 + OpenAPI 0-diff and I24a LOCAL6: via the
    established exact transcript-only chain — EDGE 1 I24a `24a43335` (tree
    `e59de814`) → f35: EXACTLY 4 paths (active modified; ADDED 083-5-f order,
    083-5-e report, 083-5-f report); EDGE 2 f35 → A420 `a4206939`: EXACTLY 8
    paths (2 tests, 2 docs, active, a order, b order, a report); all 100644,
    no mode changes; production/builders/locks/policy EMPTY on both edges;
    prior 083/5 transcript blobs byte-identical f35 vs A420.
- Preserved failures (never overwritten, never aggregate-passed): WHOLE1
  FAILED (measured wrapper umask-077 leak; controlled child-umask-022
  packaging check 49/49 native 0, log 706B SHA-256
  `540724199f5e9939dceb01eb4aa816becf314427c149ec0b0b1ca86041f7fe97`); I9d
  WHOLE FAILED (governance Puck expected 2 received 5,
  2026-10-25T23:47:17Z, log 42439B SHA-256
  `7cdf1c5bf11493d095f11f8563dbe4940a580c4969b756fd83ee3a82930bc2d8`);
  contaminated-checkout ALL31 (21/29/31 human3-only); R5 preflight failures;
  B2 initial failed launch; the b scratch lint first-attempt failure.
  Original 600s CI stall, 5-wrapper over-add, and double-iframe-POST causes
  remain UNKNOWN; no flake/benign labels.
- No local ALL31/browser/Compose/DB/supply pipeline rerun is authorized or
  executed in c; no source/install/checkout mutation of any worktree in
  active runtime; no runtime/setup work is part of c.

## 6. F4 — fresh c-S final CI (requirements; honestly pending at publication)

- Mandatory at c-S: FRESH all 20 required check names from a plus ALL 10
  PG14..18 A/B children COMPLETED/SUCCESS; fresh actual CI Compose
  (40 browser / 19 projects / 49 packaging / footer OK) and six-image
  artifact/provenance with current Critical 0, no ignored, exceptions EMPTY,
  and the 19 inherited High full six-tuple comparison; unchanged five argv
  (85+45 per PG) and 15m budgets intact; strict ruleset 20934043 / apps
  15368 except CodeQL 57789, no bypass. No skipped/neutral/missing/failed/
  cancelled/pending qualifies.
- b-S all-30 checks and artifact 12625340443 are b-S evidence ONLY; they are
  not reused as final c-S current proof, and unchanged CI is not rerun.
- At the honest publication instant the fresh c-S run may be pending; root
  independently waits. This report is NEVER amended after S to fill future-S
  results.

## 7. Security (actual, as observed; no closure claim)

- Advisory #17 (GHSA-6q48-6c7w-9gw2; locked `certifi 2026.7.22` is
  test-group-only; patched 2026.10.19) stays OPEN. No dismiss/suppress/
  release-readiness claim.
- Actual backend image bytes (b round bounded probe: unstarted container
  create/export/remove of image `sha256:3bf5e87a...`): system pip 25.0.1
  (`pip-25.0.1.dist-info/METADATA`, SHA-256
  `4fa7318cf30f979db7cec45c12cbbc2b4f88a15f12eefbf59a6291d0a03af926`)
  vendors affected `certifi 2024.08.30` (`__init__.py`, 94B, SHA-256
  `a7f19866b8d4c0f0548692e5099a066f49a2281292a83032642e43bc8baa6c74`), and
  the ensurepip bootstrap wheel (1841526B, SHA-256
  `c46efd13b6aa8279f33f2864459c8ce587ea6a1a59ee20de055868d8f7688f7f`)
  contains hash-identical certifi members — two copies. Mode caveat stands:
  the inventory's `mode` fields are local-extraction modes (probe umask 077 +
  `os.lstat`); original image modes UNRECORDED.
- Nine direct main-group dependencies (F2.7); the app venv excludes test
  groups; no observed product pip/TLS invocation; absence of observed
  invocation is NOT universal unreachability.
- Scanner "Critical 0" in six-image scans is NOT equivalent to
  known-critical closure. The next separate bounded security increment
  (remediate the test lock and the measured installed/bootstrap pip copies)
  remains required before foundation qualification or new features; OS trust
  roots, other alerts, and full MVP/release criteria remain open. No
  certifi/uv.lock/pip/image/pin/scanner/exception edit under c.

## 8. Footprint and transcript identities (actual, measured)

- Seven exact transcript identities at c S: a order (298L), b order
  (325L/19930B), c order (174L/11046B, SHA-256
  `e5d90924a2882ae96a7dcc75af57fdabb0324c4ed57f5ddbd8a74e3f447ddc5b`),
  a report (540L/37334B, SHA-256
  `23c7dfc32d0cc5c807d11ef17c8e2ea745283976fa8b1411f40e73d43127e1ea`),
  b report (652L/47105B, SHA-256
  `c6780288e520ad7317e12fe3b8847bac99a4fa7e03a30ec0c8cbe765935b8bcd`), this
  c report (final line/byte count recorded in the F1 sidecar), and
  `oap/active` (`083-6-c` + LF). No other OAP content changes.
- New c transcript lines: order 174 + this report = pair total recorded in
  the F1 sidecar, within the order's 250..500 bound; no proof packing and no
  duplication of the historical 47105-byte b prose beyond the finite
  corrections in section 4.

## 9. Owned runtime state at publication

- c performed NO runtime work (transcript-only). Owned `slaif0835` stack
  state: the 2026-10-26T02:52:40Z read-only check (zero containers / zero
  volumes) is the LAST OBSERVED b-round state; it is carried as such and is
  NOT claimed as a freshly verified current c-round state (c performed no new
  runtime probe). Clean isolated worktree retained (disposable). Foreign
  containers/projects never touched; user `.codex/`, `CODEX-SESSIONS.md` and
  `codex.sh` preserved.

## 10. Confirmations

- AMENDED_EXISTING_PR; same PR #110; no new PR/branch/semantic family; no
  merge, auto-merge, close, or self-acceptance by this agent.
- Zero product/test/doc/config/dependency/migration/workflow edits in c
  (section 5 full-tree proof); no new test/doc identity; no reporter change;
  no assertion/timeout/retry change of any kind.
- All a/b oracles, acceptances, security/privacy boundaries and non-goals
  remain binding and preserved; the b report is immutable and unamended.
- No production secrets or production systems accessed; no setup or
  dependency change (no install, no lock change, no environment or toolchain
  mutation) in this round.
- No report of hypothetical commands/exits: every stated result above is
  actual, with recorded native results and evidence paths.
- FIFO protocol: the ONE c control OK consumed once; no early receipt ACK;
  no old-signal replay; the exact 2-byte `OK` (no LF) is written to
  `response.fifo` only AFTER this report-only S is pushed and the remote
  head/parent/sole-path/exact-bytes are verified, then the writer closes.

## 11. Limitations, blockers, remaining criteria

- Fresh c-S all-30 CI + CI Compose whole + six-image supply: PENDING at
  publication (section 6); recorded honestly, never back-filled.
- Advisory #17 OPEN with affected bytes verified present (two copies);
  runtime reachability UNKNOWN; the next bounded security increment is
  required.
- The b publication deviation is disclosed (sections 3 and 4); no
  protocol-clean claim is made for b.
- The full 083 product objective and release criteria remain incomplete and
  active; numeric 083 stays open under future orders.
