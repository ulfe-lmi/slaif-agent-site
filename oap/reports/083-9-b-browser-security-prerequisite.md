# OAP 083-9-b execution report: browser security prerequisite (Chrome CfT 156.0.8078.80 maintenance pin), closed PARTIAL at implementation F

## 0. Header facts

- Round: 083-9-b of numeric objective 083 (unresolved), semantic
  increment 083/9, mode `AMENDED_EXISTING_PR`. Closed PARTIAL at
  implementation F by ROOT direction (2026-11-01, after the fresh
  backend Python Critical finding, section 4). Not accepted; not
  merged; `NEEDS_NEXT_ORDER`: ROOT 083-9-c (backend Python 3.12.16 and
  Noble worker Python resolution) on the same PR113.
- Order: `oap/orders/083-9-b-browser-security-prerequisite.md`
  (363 lines, 22605 bytes, content SHA256
  `93600228041448d81bf2b1b78970874a4da4d773d17791a35d83b873c7196367`,
  blob `9138ec36b212cc33fb7f7898bb1506c8b939883a`), committed
  byte-exact at P1; activated 2026-10-30T05:21:53.673174Z with one
  exact control OK (2 bytes `4f4b`, no LF, native 0, closed
  2026-10-30T05:22:07.125298Z) consumed by the retained 083-9-a
  next-control reader (wrapper 989103 / head 989105, control FIFO
  inode 4470111), which retained
  `/tmp/oap-083-9-a/next-control-signal.bin` and its `.native`
  sidecar.
- PR: `AMENDED_EXISTING_PR` #113
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/113>, state OPEN,
  base main `d18b6e4c9423f61de99b516be90619bf2ab5d3e0` (D18, unchanged),
  head branch `oap/083-9-a-remediate-node-brotli-runtime`, worktree
  `/home/janezp/codex-work/slaif-agent-site-083-9-a`.
- Starting remote SHA (main D18):
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0`; round-start head P1
  `6fcad094f410d7495e9841496367c17dfe844423` (committed
  2026-10-30T05:40:06Z, tree `9704376efc19e8765d7886d028960ae0dc4e1b2b`).
- Literal implementation SHA (F):
  `8802e6abe8af76935ae862b42239a9504cf2e35d` (tree
  `b2a2981422ba8865b531bdae813f8cd5e71edb4f`, committed
  2026-11-01T18:58:22Z), sole parent P1. No amend, force-push, or
  rebase at any point.
- Pushed commits this round: P1 (source phase), F (Phase 2), then SELF
  (report-only).
- Report publication commit: SELF (this report; sole parent literal F
  `8802e6abe8af76935ae862b42239a9504cf2e35d`; sole new path this
  report).
- Status: PARTIAL (ROOT direction; not accepted; not merged).

## 1. Source state: exact scoped changes versus D18

Twenty paths differ from D18 at F (`git diff --numstat` versus D18,
read-only): sixteen source paths plus the two round orders (added),
the 083-9-a report (added), and `oap/active`:

- `README.md` 4+/3-
- `apps/web/Dockerfile` 3+/3-
- `docs/CONFIGURATION.md` 1+/1-
- `docs/DEPLOYMENT.md` 4+/4-
- `docs/LICENSE_POLICY.md` 1+/1-
- `docs/SECURITY.md` 2+/2-
- `docs/SUPPLY_CHAIN.md` 54+/18-
- `oap/INCREMENTS.md` 3+/2-
- `oap/MVP-PROGRESS.md` 2+/2-
- `oap/active` 1+/1-
- `oap/orders/083-9-a-node-brotli-security-prerequisite.md` 299+/0-
- `oap/orders/083-9-b-browser-security-prerequisite.md` 363+/0-
- `oap/reports/083-9-a-node-brotli-security-prerequisite.md` 464+/0-
- `services/browser-worker/Dockerfile` 47+/8-
- `supply-chain/browser-worker-critical-matrix.json` 60+/0-
- `supply-chain/policy.json` 11+/5-
- `tests/packaging/test_oci_contract.py` 17+/3-
- `tests/supply_chain/test_policy.py` 85+/4-
- `tools/compose/smoke.sh` 3+/3-
- `tools/supply_chain/policy.py` 21+/6-

- Source gross versus D18: 383 natural lines (318 added / 65 removed)
  across the sixteen source paths (the four transcript files - the two
  round orders, the 083-9-a report, and `oap/active` - excluded per
  ROOT metric), versus planning 400 / HARD 600 / max 24 paths.
- Round b delta (F versus P1): exactly three paths -
  `docs/SUPPLY_CHAIN.md` 27+/4-,
  `supply-chain/browser-worker-critical-matrix.json` 60+/0-,
  `tests/supply_chain/test_policy.py` 67+/4-. No Dockerfile, pin, or
  build-input change under b; README and every image input frozen at
  P1 (ROOT proof
  `/tmp/oap-083-9-b/root-P1-to-F-image-input-equivalence-review.json`:
  369 repository image inputs plus the six Dockerfiles,
  `.dockerignore` files, README, and auxiliary invocations all exact
  P1).
- No `uv.lock`, `pnpm-lock.yaml`, CI workflow, selector, app
  package/dependency, lock, helper source path, or infrastructure
  change; no new branch or second PR.
- Preserved byte-exact: all seven pre-existing critical-matrix history
  objects and all 65 finding objects (raw-object hash baseline
  `/tmp/oap-083-9-b/root-pre-candidate10-raw-history-baseline.json`);
  old test assertion bodies (guards re-anchored only).

Round b per-path substance (on top of the 083-9-a paths documented in
the 083-9-a report):

- `supply-chain/browser-worker-critical-matrix.json`: candidate-10
  history object appended (history 7 to 8; findings stay 65) recording
  the intermediate P1 qualification with only observed facts: CfT
  156.0.8078.80 / revision 1706539 (linux64 archive SHA256
  `b711c720f774be355197f32edf37e0651418ba036d92446ee2da19ac017540a7`,
  chrome executable SHA256
  `1bcad71ad1bff85955db13c6d8dd9f32374934d5a5cb079b526c46fb51f9bd97`),
  the P1 CI six-image facts (section 2 N5), the 20-strict-plus-10-PG
  success at P1, the local two-image runtime probe as a distinct
  local-only subject, and the explicit "intermediate P1 qualification"
  label with the durable final-gate requirement.
- `tests/supply_chain/test_policy.py`: history length guard 7 to 8;
  old candidate-7/8/9 negative anchors shifted one slot (`[-4]`,
  `[-3]`, `[-2]`), old bodies unchanged; new candidate-10 guard block
  asserting actual evidence (version/revision 1706539, archive and
  executable hashes, CI image digest, sbom + scan-sbom hashes, purl,
  1761 matches, High 4 of 13, Critical 0, scan sha, ci run, evidence
  revision, qualification date), the intermediate P1 label, and the
  literal P1 in history_note.
- `docs/SUPPLY_CHAIN.md`: candidate-10 intermediate P1 qualification
  paragraph with dated facts and the distinct local image IDs; both
  current-pin paragraphs state the durable requirement (final F/SELF
  gates require fresh required checks and six-image CI
  re-qualification), not a permanently-pending claim; no future-pass
  claim.

## 2. N1-N6 evidence (truthful)

### N1 same correct PR, cumulative scoped source and size - met at source level, pending ROOT acceptance

- One PR for increment 083/9 (PR113), amended same branch/PR under the
  increment-qualified round law; cumulative 20 paths versus D18
  (section 1); source gross 383 versus planning 400 / HARD 600;
  architecture/locks/CI/foundation/driver unchanged.
- ROOT independently verified the complete remote maps: 1118 leaves at
  P1; 1120 leaves at F with only the three expected files changed and
  all 1117 other mode/type/blob exact.
- PR112 checkout, its 264-line WIP, all history, and human files
  preserved untouched; no reset, force, amend, rebase, clean, or
  foreign deletion.

### N2 actual fixed Node/Brotli/Chrome bytes/provenance - pinned sources met; final F/SELF re-qualification outstanding

- Chrome 156.0.8078.80 / revision 1706539: official CfT linux64
  archive bytes verified before use (archive SHA256
  `b711c720f774be355197f32edf37e0651418ba036d92446ee2da19ac017540a7`);
  chrome executable SHA256
  `1bcad71ad1bff85955db13c6d8dd9f32374934d5a5cb079b526c46fb51f9bd97`
  measured from the P1 CI artifact and by the local probe; Playwright
  1.62.1 Noble base, user 10001, sandbox, and egress unchanged.
- Node 24.22.1 (web registry digest `sha256:0468540a...dc92a2`; worker
  official `.tar.gz`
  `eb6728e77c576a35162c122c45ccadf224d89ff00abc8dae46cc2897c6002d7c`)
  and fixed `libbrotli1=1.1.0-2ubuntu0.1`: as documented and CI-verified
  in the 083-9-a report; unchanged by b.
- The local P1 two-image runtime proof (N4) verified actual executable
  path/hash/version, Node/Brotli round-trip, decoder provenance,
  license hashes, runtime-tool absence, and Chrome facts.
- Unmet: the final gate is fresh re-qualification at the final SELF;
  the intermediate P1 observations do not carry as F proof, and the
  final F CI failed (N5), so the final six-image evidence is
  incomplete.

### N3 fresh ALL31 at final F plus meaningful affected checks - PARTIAL (affected checks qualified; fresh ALL31 NOT RUN)

- Fresh ALL31 (the order's 31 exact local commands): NOT RUN. The
  31-command runner (planning 120 / HARD 160) was constructed in
  memory only, with the order's exact argv and finite monotonic caps;
  ROOT directed STOP before any write/execution after the F CI
  failure; the draft is preserved as inert conversation data only; no
  runner file exists on disk. No ALL31 pass is claimed.
- Meaningful affected checks for the newly changed b files, run once
  on the precommit source bytes that were later published exactly as F
  (not a clean committed-F HEAD; the fresh ALL31 was to be the clean-F
  gate), full streams, immediate bare-child natives:
  - P1 boundary (2026-10-30, after the five-file pin unit): the
    missing Ruff check plus format scopes, the packaging suite, and
    the markdown scope re-qualified with Node v24.22.1 on PATH;
    qualified per ROOT review. The 083-9-a boundaries and receipts
    remain in the 083-9-a report; unchanged gates were not rerun for
    cleaner clocks.
  - F boundary (2026-11-01): `ruff check tests/supply_chain` native 0;
    `ruff format --check tests/supply_chain` first native 1 (the new
    candidate-10 guard had one collapsible line) - authorized in-scope
    format fix verified by `--diff` to be exactly that one collapse,
    re-run native 0; `ruff check` re-run native 0; `pytest
    tests/supply_chain` 44 passed, native 0; `markdownlint-cli2`
    0.23.2 under Node v24.22.1 native 0, 0 issues (the repository
    glob expanded the single-file argument to a full-repository run of
    563 files - a superset; erratum 9).
- Overlap disclosed; no grand total invented.

### N4 approved two-image local proofs and P1-to-F input equivalence - met at P1; final re-qualification outstanding

- `verify-node.sh` (350 lines, 18912 bytes, SHA256
  `7479267c6435921c4fa8d2672cd1e0d1a08bb79e9bfc8101cdbe92c9c2fa3cbc`)
  was constructed in memory, ROOT-approved line-for-line, exclusively
  written, and executed exactly once with bare bash at P1 source
  (2026-11-01T18:16:17Z to 18:20:07Z, raw ns 1793556977775810294 to
  1793557207771646796), script native 0:
  - two uniquely owned image refs built at P1 (web
    `sha256:8315ee8bcf6177a99c95e777a4c13b3d90226f2df0f62ef1133d9e50c1ea7f38`,
    worker
    `sha256:7704ac15be2e271f2fe3909d68640f26319cbcb8c0c73b78c0f494007f2bbf76`)
    - local-only subjects, never mixed with CI image identities;
  - source identity enforced at START and END (branch / head P1 /
    tree / clean); finite monotonic-capped windows; full streams in
    `/tmp/oap-083-9-b/verify-node/logs/` (36 files); created-container
    IDs persisted before start; safe immutable metadata before
    disposal; terminal state captured before rm; exact post-cleanup
    absence of the owned containers and refs; no foreign/shared
    resource touched, no sweep, no prune;
  - oracles passed: web musl Node (sha/size/version/license/brotli)
    and worker glibc Node (sha/size/version/license/brotli,
    `libbrotli1=1.1.0-2ubuntu0.1`, full `ldd` output, NodeSource
    inventory), runtime tool/library absence including both Corepack
    locations, single-browser tree, Chrome 156.0.8078.80 executable
    sha/version.
- P1-to-F image-input equivalence: verified (section 1); the literal
  P1 local observations carry to F under that equivalence, not as an
  F probe; no new local F runtime probe was run or authorized.
- Unmet: fresh final F/SELF re-qualification.

### N5 current final 20+10, packaging/six-image evidence, High/vendor-Critical review - NOT MET at F

- At P1 (CI run 41009725680; CodeQL separate workflow run
  41009725630; observed through 2026-10-30T06:00:03Z, ROOT verified):
  all 20 required strict checks and the 10 actual PG children success.
  Supply job 123912630228, artifact 12957452083 (zip SHA256
  `d55dafe328a7dad107146e3769832cd29ba8d1bbe7d936a1e02894ecc6cd34db`,
  53 checksum payloads): six-image scan with zero unexcepted Critical,
  zero exceptions, empty ignored sets; all 29 prior `156.0.8078.47`
  Chrome High six-tuples absent at every severity; zero new full High
  six-tuples; 13 inherited High review findings retained (backend 1,
  worker 4, postgres 7, web 1); worker 1761 matches (High 4 / Medium
  1609 / Low 134 / Negligible 14), ignored 0; CI worker image
  `sha256:7462572a3f5d4a5a1ff6ddaf71f49ee4c6aa51a5046d0e0aa8e62681d8a3093e`;
  DB built 2026-10-29T06:23:34Z with checksum
  `sha256:a5ad3344d964e4d1472fa615b0e70f87c27cd21470fede2a8fbf6e4c6c32c907`
  (age 23.474 h at CI validation time, not at append time).
- At F (CI run 41339340523, created 2026-11-01T18:58:40Z, plus CodeQL
  run 41339340499): as actually observed at report preparation, 30
  check runs - 29 success (all Foundation PG 14-18 groups, CodeQL +
  three analyzes, dependency review, Python quality/package, Compose
  and edge packaging job 124945822664 completed
  2026-11-01T19:14:35Z) and 1 FAILURE: Supply-chain evidence job
  124945822680 (completed 2026-11-01T19:10:14Z; section 4).
- The failure bundle is INCOMPLETE/UNQUALIFIED (success manifest
  ABSENT, original exit 1, all 37 failure-payload checksums/exact set
  verified by ROOT); it is not a complete licensed/scanned six-image
  success.
- The required final gate (all 20 strict + 10 PG success at the final
  SELF, fresh) is therefore NOT met; no scanner/license/vulnerability
  policy exception was added, proposed, or suppressed under b.

### N6 truthful docs/qualification history/report, exact remote publication and wire - in progress with this report

- Docs updated truthfully (section 1); candidate-10 recorded as
  intermediate P1 qualification; the 083-9-a report and all history
  unchanged; exact publication and wire in section 5 (prospective at
  this commit; actuals in the closure message).

## 3. CI as actually observed (GitHub API, read-only)

- D18 baseline and the I9..db37a465 history: as recorded in the
  083-9-a report (section 3 there); unchanged.
- P1 `6fcad094` (run 41009725680, created 2026-10-30): all 20 strict +
  10 PG success as of 2026-10-30T06:00:03Z (ROOT verified); Supply
  job 123912630228 success, artifact 12957452083 (section 2 N5).
- F `8802e6a` (run 41339340523 + CodeQL 41339340499, created
  2026-11-01T18:58:40Z): 30 check runs - 29 success, 1 failure
  (Supply-chain evidence job 124945822680) as of report preparation;
  run conclusion: failure.
- ROOT independent policy review at P1 (required 20 plus PG 10 all
  success) and the F failure-bundle review (all 37 failure-payload
  checksums/exact set; CI checkout merge M
  `6d56c404f756346e81d516f9d6936130f8f70843` with parents D18 + F and
  tree equal to the F tree) are retained under `/tmp/oap-083-9-b/`.

## 4. Fresh backend Python finding and the next bounded order

- F Supply-chain evidence job 124945822680 FAILED: unexcepted Critical
  in the backend, CVE-2026-115557 (python 3.12.15; CVSS 4.0 baseScore
  9.4; CWE-299; Grype records no fixed version; upstream CPython fix
  landed in 3.12.16). Failure diagnostics artifact 13097047617
  (10,630,240 bytes, SHA256
  `ea64e4dfc1fe975f9e863dbea734ab9a21a59eb90a1ff40a0d7a51323e34fe63`,
  member `backend.raw.grype.json`), ZIP retained.
- The same CVE also matches 4 Medium in the browser-worker image:
  python3.12 / python3.12-minimal / libpython3.12-stdlib /
  libpython3.12-minimal at 3.12.3-1ubuntu0.15, Grype not-fixed; the
  other four images show no same-CVE hits. The worker copies are not
  dismissed because the service runtime is Node or because there is no
  generic Python catalog entry; the base-image packages are real scan
  subjects.
- Official Ubuntu status for that worker package line is "Needs
  evaluation" (not fixed, not unaffected); ROOT researches the future
  083-9-c. Official `python:3.12.16-alpine3.23` tag metadata supplied
  by ROOT
  (`/tmp/oap-083-9-b/root-official-python31216-alpine323-tag-metadata.json`).
- The finding is outside the active b backend-source allowlist; no
  suppress, exception, CI rerun-until-green, or unapproved fix was
  performed under b.
- NEEDS_NEXT_ORDER: ROOT 083-9-c on the same PR113 - backend Python
  3.12.16 (fixed upstream) plus the resolved Noble worker Python line,
  then the remaining full gates (fresh ALL31 at final F, final
  two-image re-qualification, fresh final 20+10 and six-image CI, High
  re-audit, final SELF CI). No new order or signal until ROOT.
- PR112 remains OPEN ON HOLD / INACTIVE (not abandoned, not accepted);
  it resumes only by ROOT 083-8-j with a history-preserving main merge
  after 083/9 is accepted, merged, and remote main verified. Numeric
  083 and the full product remain unresolved; no 084 advancement, no
  release or qualification claim, no cap retro-waiver, no history
  rewrite.

## 5. Procedure, publication, and remote proof

Done this round (actual receipts retained under `/tmp/oap-083-9-a/`
and `/tmp/oap-083-9-b/`):

1. Activation: order byte-exact (363 lines / 22605 bytes, content
   SHA256 `93600228041448d81bf2b1b78970874a4da4d773d17791a35d83b873c7196367`);
   one exact control OK (2 bytes `4f4b`, no LF, native 0, closed
   2026-10-30T05:22:07.125298Z) consumed by the retained 083-9-a
   next-control reader; no replay.
2. P1 (committed 2026-10-30T05:40:06Z): five-file Chrome
   156.0.8078.80 pin unit (worker Dockerfile, policy.json, policy.py,
   test_oci_contract.py, test_policy.py) plus coupled docs and the
   order/active transcript; pushed to the same PR113. The executor's
   bare push native for P1 is not retained in a separate log file
   (disclosed); remote publication stands on `git ls-remote` and the
   ROOT 1118-leaf map with exact bytes.
3. F (committed 2026-11-01T18:58:22Z): candidate-10 matrix append,
   test re-anchor plus candidate-10 guard, current docs; bare push
   native 0 (`6fcad09..8802e6a`); remote branch head and PR API head
   verified at F immediately after push; ROOT verified the 1120-leaf
   map (only the three expected files changed; all 1117 others exact)
   and the P1-to-F image-input equivalence.
4. PR113 title/body updated around the final 083/9 increment with
   truthful remaining gates (REST PATCH native 0 after a GraphQL
   `projectCards` deprecation error on `gh pr edit`; erratum 14).
5. `verify-node.sh` constructed in memory, ROOT-approved, exclusively
   written, executed once (section 2 N4); ROOT accepted the P1 local
   runtime proof.
6. CI observations via the GitHub API, read-only (sections 2 N5, 3,
   4); the F failure artifact retained with the verified ZIP.
7. No acceptance, merge, ALL31 write/execution, runtime rerun, or
   report/OK action before this publication.

To be executed before the single response OK (prospective at this
commit; actuals reported in the closure message):

1. The complete TEMP
   `oap/reports/.083-9-b-browser-security-prerequisite.temp.md`
   linted with the exact repository markdownlint-cli2 0.23.2
   `--no-globs`: native 0, one file, zero issues, on the SAME complete
   bytes to be published.
2. Pre-hash/inode/size plus actual UTC and raw `time.time_ns()`;
   explicit file fsync; same-inode atomic rename to the sole report
   path in the PR worktree; parent-directory fsync; post-rename SHA256
   compared equal to the linted TEMP.
3. Byte-exact report copy published to the canonical OAP root
   `/home/janezp/codex-work/slaif-agent-site/oap/reports/` (untracked;
   not committed there); both final files' SHA256 equal to the linted
   TEMP.
4. Report-only SELF commit: sole parent literal F
   `8802e6abe8af76935ae862b42239a9504cf2e35d`; sole new path this
   report; pushed with a bare push native.
5. Explicit remote proof: the actual PR API head SHA compared with
   SELF (rechecked if stale); SELF sole parent F; sole report path
   present (`git diff --name-only F..SELF`); remote report bytes/hash
   equal to the linted TEMP; PR113 OPEN with base main
   `d18b6e4c9423f61de99b516be90619bf2ab5d3e0`, unmerged.
6. ONE exact ASCII OK (2 bytes `4f4b`, no LF) written to the verified
   response FIFO inode 4470112 (ROOT sole 9-b response reader, tool
   handle 73297 / OS PID 994488, verified live with lock held) and the
   writer closed; NEVER fsync a FIFO; no replay; on any post-write
   error, inspect the retained ROOT wire proof before any further
   attempt.
7. Exactly ONE byte-retaining next-control reader on control FIFO
   inode 4470111 retaining `/tmp/oap-083-9-b/next-control-signal.bin`
   and its `.native` sidecar; actual handle/PID/paths reported in the
   closure message; no nohup experiments.

## 6. Limitations and unresolved criteria

- N1: met at source level, pending ROOT acceptance and merge.
- N2: pinned Node/Brotli/Chrome sources met and CI-verified at P1;
  final F/SELF runtime re-qualification outstanding.
- N3 PARTIAL: fresh ALL31 NOT RUN at final F (runner in memory only;
  draft inert; no file written or executed); affected checks qualified
  to precommit bytes published exactly as F.
- N4: met at P1 (two-image proof accepted; input equivalence
  verified); final F/SELF re-qualification outstanding.
- N5 NOT MET at F: final 20+10 not all success (Supply-chain evidence
  failed, section 4); final six-image evidence INCOMPLETE (UNQUALIFIED
  failure bundle, success manifest ABSENT); final SELF CI fresh/unknown
  at publication.
- Acceptance path: ROOT 083-9-c (backend Python fix plus worker line
  resolution) on the same PR113, then the remaining gates; ROOT alone
  accepts and merges. Green CI alone never acceptance. No success claim
  anywhere in this report.

## 7. Forward errata (carried; no historical edits)

The 083-9-a forward-precision list and errata remain in its immutable
report; round b errata:

1. Grype parser first read used uppercase keys (Matches/Vulnerability/
   Severity) and printed MATCHES 0 / SEV {} - a read-only parser
   erratum; the actual keys are lowercase; worker 1761 matches (High
   4 / Medium 1609 / Low 134 / Negligible 14), ignored 0. No
   zero-vulnerability claim was made.
2. C2 candidate: 19516 Unicode codepoints / 19520 UTF-8 bytes (an
   early print said "19516 bytes").
3. verify-node runtime log count 36 files, not 35.
4. Successful normal cleanup DID dispose of the owned containers/refs;
   builds naturally populated the shared Docker build cache (no prune,
   no foreign deletion); the container sleep final ExitCode 137
   (stop-time kill) is separate from the probe exec native 0.
5. No AFTERSETUP runtime marker was emitted by verify-node; only the
   actual START and END source identities bound the read-only
   setup/build/probe/cleanup windows.
6. The Chrome version was asserted from the captured successful native
   but not echoed; no rerun for cosmetics.
7. Matrix append: no global re-serialization of the mixed-indentation
   file (surgical insertion plus semantic validation); the candidate-10
   Syft commit typo (39 hex) was corrected by reading GitCommit
   directly from the artifact `scanner/syft-version.txt`; the first
   correction attempt asserted good==bad, failed before write, and made
   no mutation.
8. P1 push native not retained as a separate executor log; remote
   publication stands on `git ls-remote` and the ROOT 1118/1120 leaf
   maps (no retry).
9. Markdown lint "563 files": the repository glob config expanded the
   single-file argument to a full-repository run (560 files at the
   083-9-a phase; +3 for the round b .md files) - a superset, 0
   issues, honestly reported.
10. CI query erratum: my statusCheckRollup filter
    `select(.context != null)` excluded CheckRuns (which carry `name`,
    not `context`) and printed empty; F CI was registered and in
    progress (runs 41339340523 + 41339340499); absence was never
    claimed from that filtered output.
11. Timeout wrapper: the installed `timeout` is uutils 0.8.0, which
    forwards TERM (an earlier false claim that it does not is
    corrected); on a deadline the observed wait status is the wrapper
    status (124/137) and the actual command native stays UNKNOWN
    unless separately observed; no disposal/retry on unknown.
12. Source budget: an early gross 353/362 excluded all oap paths
    (undercount 9 lines); the ROOT metric counts `oap/INCREMENTS.md`
    plus `oap/MVP-PROGRESS.md` and excludes only the four exact
    transcript files: current gross 383.
13. F-boundary affected checks ran on precommit worktree bytes later
    published exactly as F, not on a clean committed-F HEAD; the fresh
    ALL31 was to be the clean-F gate (NOT RUN).
14. `gh pr edit` failed on the deprecated GraphQL `projectCards`
    field; the PR title/body update was made via REST PATCH (native
    0), no retry loop.
15. The baseline raw-object parse first failed on the list shape
    (read-only); corrected and preserved honestly.
16. The ROOT diagnostic's own erratum is preserved: initial correct
    full download/hash verification 0, then combined Python native 1
    because an assumed success-bundle member path
    (`scans/backend.grype.json`) was used; the actual failure layout
    uses `backend.raw.grype.json`; no redownload or execution.

## 8. Confirmations

- Scope: this round's commits change only the five-file P1 pin unit,
  the three b paths of section 1, the order/active transcript, and
  this report (SELF); cumulative 20 paths versus D18 as listed. No
  Dockerfile/pin/build-input change under b; no other source, test,
  doc, dependency, lock, CI selector, authority, or infrastructure
  change. No second PR, no merge, no auto-merge, no reset/force/amend/
  rebase/clean or deletion of preserved history.
- Secrets: no real secret, capability, cookie, DB URL, setup
  credential, or private-artifact content in any artifact I produced;
  no Env/Args/Cmd/full-inspect/raw-private logging in the verify-node
  receipts; no exploit or proof-of-concept execution; external fetches
  limited to official archive/registry/metadata verification. I make no
  blanket no-secrets-in-every-artifact claim for ROOT artifacts.
- Production: untouched; no production, deployment, or credential
  work.
- Local setup: uv 0.12.5; Python 3.13.14 (uv-managed, frozen lock);
  Node v24.22.1 official tar.gz (SHA256 `eb6728e7...`) at disposable
  scratch `/tmp/oap-083-9-a/verify/`; pnpm 11.22.0 via the corepack
  cache with the frozen lockfile; markdownlint-cli2 0.23.2 via npx
  under Node v24.22.1. No product dependency or lock change.
- Docs: `docs/SUPPLY_CHAIN.md` updated truthfully with the
  intermediate P1 qualification and the durable final-gate
  requirement; no historical doc edited.
- No complete-083, MVP, release, qualification, acceptance, merge, or
  next-objective advance claim.
