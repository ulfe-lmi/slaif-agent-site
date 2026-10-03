# OAP Work Order — 079-2-h (web next RCE fix 16.3.8 + browser-worker
# Chrome-for-Testing 154.0.8037.92 refresh; closing round for 079/2)

> Strategic work order. Executor: coding agent. Reviewer/acceptor/merger:
> strategic model. This order is IMMUTABLE once activated; corrections,
> if ever needed, use the next letter (079-2-i) and a new order.

## 1. Identifier and mode

- Round ID: `079-2-h` (increment-qualified; eighth round of semantic
  increment 2 of numeric Objective 079; increment 079/2)
- Objective: 079 (079/2 — Gallery/LogoGrid media increment; this round is
  the CLOSING qualification-repair round of the 079/2 review unit)
- PR mode: AMENDED_EXISTING_PR — PR #93
  (`ulfe-lmi/slaif-agent-site`), branch `oap/079-2-a-gallery-logogrid`
- This round combines exactly TWO closed repair sets. Both are required
  for the `Supply-chain evidence` gate to pass at any final head of this
  unit (verified: with only set A, the browser-worker 24-CVE class still
  fails under the current grype database; with only set B, the web
  next@16.3.3 Critical still fails). They are therefore ONE round, not
  two. Neither set is mergeable on its own; this is the round that makes
  the 079/2 unit's final head gate-green.

## 2. Verified current state (strategy-verified 2026-10-04 against the
live GitHub and local checkout)

- Remote `main` = `577509e7bc990d85a10af5954bee3c6f7c888a4f` (079/1
  merge; unchanged).
- PR #93: OPEN, `mergeable: MERGEABLE`, `mergeStateStatus: BLOCKED`,
  base `main`, head `oap/079-2-a-gallery-logogrid`.
- Round-start SHA
  `C = 3fba0bf97bd454e1ffc06a0dfd7a1f9dc527bd5f` (the 079-2-g
  report-only commit S_g; parent `T_g = 741dd932144e72257f3864c70d8e8956d3dfafc2`;
  grandparent `I_f = 0f5186e863f4c13e4119309109d2420c3b803b60`).
- CI at S_g (run 37162346409) was still executing when this order was
  written; its expected terminal state is a `Supply-chain evidence`
  FAILURE on the web image (the next@16.3.3 Critical below). Do NOT wait
  for it, do NOT re-run CI on S_g; it is superseded by this round's
  head.
- Round 079-2-g result (immutable report
  `oap/reports/079-2-g-browser-cft-154-refresh.md`, BLOCKED): P1 fully
  met (60-line/15-file closed inventory exact; archive byte-exact
  sha256 `ff43322f335e436b2f4dcdfeeec5db032299e335a7e8c1c618b326e100ce8732`,
  196,202,491 bytes; CfT endpoint entry 154.0.8037.92 / revision
  1689415 / timestamp 2026-10-03T01:32:42.960Z); the 14 static P2 sites
  were applied, validated (`policy validate` OK, check_repository PASS,
  ruff clean, 85+54 tests passed with 1 expected failure), then REVERTED
  (no implementation head I_g exists); the local measured pipeline
  (pinned Grype 0.117.0 on a fresh v6.1.10 database built
  2026-10-03T06:31:58Z) proved the browser-worker refresh end-to-end
  (ZERO Critical; all 24 named CVEs absent; double-build reproducibility
  clean for all six images, backend 2821/2821) and then FAILED on a NEW
  external class in the web image: `GHSA-vcvr-r3jv-pc5j` on
  `next@16.3.3`.
- The new web Critical (verified by strategy 2026-10-04 against the
  GitHub advisory API): `GHSA-vcvr-r3jv-pc5j`, "Next.js: Remote Code
  Execution in next/og ImageResponse", severity critical, npm
  `next` vulnerable range `>= 16.2.0, < 16.3.6`, first patched version
  `16.3.6`, published 2026-09-30. Registry-verified: the latest stable
  16.3.x release is `16.3.8` (npm dist-tag `latest` = 16.3.8);
  `next@16.3.8` tarball
  `https://registry.npmjs.org/next/-/next-16.3.8.tgz` with integrity
  `sha512-U7QEZaTini6wKrb8A8hqLLqYQyCetegKjCpJOyxk642vWoMoU1x5PyZCJFvgYgiptA8xc5j/9xYlZFO7w9Sjmw==`.
  Strategy DECISION (recorded): version bump to `16.3.8`, NOT an
  exception entry — a fixed version exists, the advisory is a
  network-exploitable RCE (AV:N/PR:N), and the exception regime remains
  reserved for cases where no fix exists or where the fix carries
  disproportionate risk (precedent 072-i/j/n; cf. the 078-6-a
  version-refresh-over-exception decision).
- Closed inventory of `16.3.3` at C (strategy-verified by git grep;
  40 lines across exactly 7 files): `THIRD_PARTY_NOTICES.md` 3 lines
  (39, 40, 182); `apps/web/package.json` 1 line (16);
  `docs/DEPLOYMENT.md` 1 line (161); `pnpm-lock.yaml` 31 lines (74, 75,
  405, 408, 414, 420, 427, 434, 441, 448, 454, 1272, 1986, 1988, 1991,
  1994, 1997, 2000, 2003, 2006, 2009, 2767, 2769, 2778, 2779, 2780,
  2781, 2782, 2783, 2784, 2785); `sbom.json` 2 lines (249, 250);
  `tests/repository/test_repository_policy.py` 1 line (115);
  `tools/check_repository.py` 1 line (1377). NO historical
  next@16.3.3 narrative exists anywhere (there is no prior next bump to
  preserve).
- The 15-file CfT closed set of 079-2-g (unchanged from that order):
  `services/browser-worker/Dockerfile`, `supply-chain/policy.json`,
  `tools/supply_chain/policy.py`, `tools/supply_chain/evidence.py`,
  `tools/compose/smoke.sh`, `tests/packaging/test_oci_contract.py`,
  `tests/supply_chain/test_evidence.py`, `tests/supply_chain/
  test_policy.py`, `supply-chain/browser-worker-critical-matrix.json`,
  `README.md`, `docs/CONFIGURATION.md`, `docs/DEPLOYMENT.md`,
  `docs/LICENSE_POLICY.md`, `docs/SECURITY.md`, `docs/SUPPLY_CHAIN.md`.
  The exact site-level values are recorded immutably in 079-2-g order
  Section 4 P2 (`oap/orders/079-2-g-browser-cft-154-refresh.md`,
  committed on this branch) and in the 079-2-g report section "P2
  (applied, then reverted)" (per-file sites 1-15). Apply from those
  records; do not re-derive them.
- The 079-2-g measured candidate-7 values (image digest
  `sha256:9f062348550320cfa773bb8d58e6d726dd932601a4ea0b7199996247acfbcf79`,
  executable sha256 `439f367a9a24dde467dca9c4e4c2feedd3266899c5a8e3eb17b68b05d4da9f5f`,
  grype DB v6.1.10 / 2026-10-03T06:31:58Z / checksum
  `sha256:397565327faac36f757903f87e31ac403a251bed21c0f0ec5b87f912c5143ab6`,
  and the full scan_result fields) are recorded in the 079-2-g report
  for context ONLY: image digests, scan hashes and grype-database fields
  are run-bound facts and MUST be re-measured in this round's own
  pipeline run. Do not copy them into the matrix or the tests.
- `supply-chain/vulnerability-exceptions.json` is EMPTY
  (`{"schema_version": 1, "exceptions": []}`) and must remain empty.
- `pnpm-lock.yaml` header: `lockfileVersion: '9.0'`, settings
  `autoInstallPeers: false`, `excludeLinksFromLockfile: false`,
  overrides `esbuild: 0.28.1` / `uuid: 11.1.1` / `vite: 7.3.6`,
  `ignoredOptionalDependencies: [sharp]`. These must be byte-identical
  after your lockfile update. `apps/web/Dockerfile` builds with
  `pnpm install --frozen-lockfile` — your lockfile MUST satisfy a
  frozen install of the updated manifest.
- The root `sbom.json` is generated by `tools/generate_sbom.py`
  (reads the package.json manifests + `uv.lock`); it is NOT
  check_repository-validated, so it must be regenerated, not hand-
  edited.
- `oap/active` bytes at activation: `079-2-h\n`.

## 3. Strategic context

The 079/2 review unit (PR #93) has passed through seven rounds
(079-2-a..g): the Gallery/LogoGrid implementation (079-2-a) plus six
externally-forced qualification repairs (Alpine pin rotation, backend
Dockerfile pin omission, Ubuntu noble openssl rotation, backend pyc
double-build drift x2, and the Chrome-for-Testing 154.0.8037.92
refresh whose local proof was completed in 079-2-g). Two independent
external events now gate the unit's final head: (A) the newly published
critical RCE in `next@16.3.3` (fixed in 16.3.6; latest stable 16.3.8)
in the web image, and (B) the 24 Critical CVEs in CfT 153.0.8010.52 in
the browser-worker image (fixed in 154.0.8037.57/154.0.8037.92; the
refresh mechanism was proven locally in 079-2-g). Both fixes are
externally-forced, finite, and belong to the unit's existing repair
family; neither is a new product semantic. This round applies both
closed sets, re-measures the qualification pipeline, and is the
CLOSING round: upon its acceptance the production/config review
trigger (~20 files) is crossed and CLOSURE_ONLY begins (Section 10/11).
After this round the 079/2 unit contains no further planned work; if
its final head is gate-green with 20/20 required checks, the unit is
complete and mergeable.

## 4. Bounded scope (exactly)

Let T = this round's transcript commit, I = this round's
implementation head, S = the report-only commit, C =
`3fba0bf97bd454e1ffc06a0dfd7a1f9dc527bd5f`.

- P1 (preflight, ZERO repository changes):
  1. P1.1 Run the closed inventory grep of Section 2 at C:
     `git grep -n '16\.3\.3' -- . ':!oap'` — it must return EXACTLY the
     40 lines across the 7 closed files (per-file counts as stated).
     Any deviation: STOP, report BLOCKED.
  2. P1.2 Registry + advisory verification (record exact outputs):
     (a) `next@16.3.8` present at
     `https://registry.npmjs.org/next/16.3.8`; its `dist.integrity`
     MUST equal the closed sha512 in Section 2; its `dist.tarball`
     MUST be `https://registry.npmjs.org/next/-/next-16.3.8.tgz`;
     (b) the packument `dist-tags.latest` MUST be `16.3.8` (record the
     full 16.3.x stable list); (c) the GitHub advisory
     `GHSA-vcvr-r3jv-pc5j` MUST still report npm `next` range
     `>= 16.2.0, < 16.3.6`, first patched `16.3.6`; (d) query ALL
     GitHub advisories affecting npm `next`
     (`/advisories?affects=true&ecosystem=npm&package=next`), record
     every CRITICAL one with its first-patched version; EVERY CRITICAL
     advisory's first-patched version must be <= `16.3.8`. Any
     mismatch: STOP, report BLOCKED (do NOT pin a different
     version).
  3. P1.3 CfT re-verification: re-download the closed 154.0.8037.92
     linux64 archive; sha256 MUST be
     `ff43322f335e436b2f4dcdfeeec5db032299e335a7e8c1c618b326e100ce8732`
     and 196,202,491 bytes; the CfT `known-good-versions-with-
     downloads.json` entry for 154.0.8037.92 must carry revision
     `1689415` and the closed linux64 URL; record the
     `last-known-good-versions.json` timestamp. Any deviation: STOP,
     report BLOCKED. (If the CfT Stable channel has moved forward
     since 2026-10-03, that is OUT OF SCOPE: the closed pin remains
     154.0.8037.92. A newly published CfT Critical would surface at
     P3.1 and triggers the P3.1 STOP rule, not a Silent repin.)
- P2a (set A — the web next RCE fix; exactly 7 files):
  1. `apps/web/package.json` line 16: `"next": "16.3.3"` ->
     `"next": "16.3.8"`.
  2. `pnpm-lock.yaml`: run the repository's `pnpm install` at the repo
     root (record the exact pnpm version used). The diff must be
     BOUNDED: only the `next` and `@next/*` (env + swc platform
     binaries) entries moving 16.3.3 -> 16.3.8 and their resolution
     references; NO other dependency version, integrity, or
     setting/override change anywhere in the lockfile;
     `lockfileVersion` and the settings/overrides/ignoredOptional-
     Dependencies blocks byte-identical. Post-edit: `git grep -c
     '16\.3\.3' -- pnpm-lock.yaml` = 0.
  3. `docs/DEPLOYMENT.md` line 161: `next@16.3.3` + old sha512 ->
     `next@16.3.8` + the closed sha512 of Section 2.
  4. `THIRD_PARTY_NOTICES.md` lines 39, 40, 182: `16.3.3` -> `16.3.8`
     (@next/env, @next/swc-linux-x64-gnu, next).
  5. `sbom.json`: AFTER the lockfile update, regenerate via
     `uv run --frozen python tools/generate_sbom.py` (record its
     output including the license check). The resulting diff must be
     EXACTLY two lines: the `next` version and purl (now
     `pkg:npm/next@16.3.8`).
  6. `tests/repository/test_repository_policy.py` line 115:
     `"next": "16.3.3"` -> `"next": "16.3.8"`.
  7. `tools/check_repository.py` line 1377: `"next": "16.3.3"` ->
     `"next": "16.3.8"`.
- P2b (set B — the browser-worker CfT 154.0.8037.92 refresh; exactly
  the 15 closed files of 079-2-g, re-applied from the immutable
  site-level records cited in Section 2):
  1. Apply the 14 STATIC sites exactly as recorded (079-2-g report
     "P2 (applied, then reverted)", sites 1-8, 10-15; 079-2-g order
     Section 4 P2 items 1-8, 10-15): pin values only; no logic,
     comparison, normalization, validator, gate, or contract change in
     `tools/supply_chain/*`.
  2. `tests/supply_chain/test_policy.py` `previous` block shift
     (candidate-5 -> candidate-6), as recorded in the 079-2-g report
     site 8: label `candidate-6 CfT: 153.0.8010.52 measured scan
     coverage`, revision `1681091`, version `153.0.8010.52`, archive
     sha256 `e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9`,
     executable `/ms-playwright/chromium-1681091/chrome-linux64/chrome`,
     image digest
     `sha256:4177c64fae4cb7d61e114e6e5c797fa239cc0f394e9d6f3f1d4dfeef9a6bf5b2`,
     `browser_worker_matches == 1486`, `result == "PASS"`,
     `unexcepted_critical == 0`, `exception_count == 0`. APPROVED
     structural delta (the ONLY permitted test-structure change this
     round): candidate-6 carries no `ci_run` field (it predates remote
     revalidation), so the `ci_run` assertion POSITION is replaced by
     the gate field assertion `scan_result["exception_count"] == 0`;
     the assertion count of the block (10) and the overall assertion
     structure are preserved.
  3. The TWO measured-value sites are deferred to P3.2 (filled with
     THIS round's own measurements): (a) the pure APPEND of
     `candidate-7 CfT: 154.0.8037.92 measured scan coverage` as the
     LAST `qualification_history` entry with the candidate-6 field
     structure (per 079-2-g order P2.9, with `history_note` attributed
     to THIS order 079-2-h acceptance criterion 6 and this round's
     run date; candidates 1-6 byte-identical); (b) the
     `test_policy` `current` block with this round's measured values.
- P2c (post-edit gates; ALL must hold; record exact outputs):
  1. Gate A (set A): `git grep -n '16\.3\.3' -- . ':!oap'` = EXACTLY
     ZERO lines; `git grep -n 'pkg:npm/next@16\.3\.8' -- . ':!oap'` =
     exactly ONE line (sbom.json); `git grep -c '16\.3\.8' -- . ':!oap'`
     shows the version in exactly these 7 files:
     apps/web/package.json, pnpm-lock.yaml, docs/DEPLOYMENT.md,
     THIRD_PARTY_NOTICES.md, sbom.json,
     tests/repository/test_repository_policy.py,
     tools/check_repository.py.
  2. Gate B (set B): the P2.16 gates (a)-(f) of the 079-2-g order
     Section 4 P2.16, VERBATIM (identical final state): (a) the 14-
     file / 15-file presence counts for 154.0.8037.92 / 1689415; (b)
     old archive sha256 = exactly TWO lines (matrix candidate-6 +
     test_policy previous block); (c) 153.0.8010.52 = exactly NINE
     lines (matrix candidate-6 x5, test_policy previous x3,
     docs/SUPPLY_CHAIN.md line 193); (d) 1681091 = exactly NINE lines
     (matrix x6, test_policy previous x2, docs/SUPPLY_CHAIN.md line
     193); (e) ZERO old values in the 12 non-history files; (f)
     matrix pure INSERTION (JSON parses; diff C..I shows only added
     lines).
  3. `uv run --frozen python tools/check_repository.py` -> PASS;
     `uv run --frozen pytest tests/packaging/ tests/supply_chain/
     tests/repository/ -q` -> all pass (ZERO failures);
     `uv run --frozen ruff check` -> clean;
     `uv run --frozen python -m tools.supply_chain.policy validate`
     -> OK.
- P3 (measured re-qualification + fresh builds + full smoke):
  1. P3.1 Run `sh tools/supply_chain/run.sh /tmp/0792h-evidence`
     (same backend-of-truth flow as candidate-6/079-2-g;
     `SLAIF_IMAGE_REVISION=local`). EXPECTED: (a) ALL SIX images gate
     PASS with ZERO unexcepted Critical — web now on next@16.3.8
     (GHSA-vcvr-r3jv-pc5j absent) and browser-worker on
     154.0.8037.92 (all 24 named CVEs absent); (b) double-build
     reproducibility PASS for all six images; (c) browser-worker
     measured values recorded: `chrome --version` = `Google Chrome
     for Testing 154.0.8037.92` (plus one trailing space, as the
     build-time assertion string), NEW image digest, NEW executable
     sha256, grype database schema/built/checksum, full scan_result
     fields, SBOM/scan sha256 fields. If ANY image fails the Critical
     gate or ANY new unexcepted finding appears: STOP, record the
     exact evidence (log lines + failure-diagnostics files), report
     BLOCKED with explicit escalation. No second fix attempt.
  2. P3.2 Fill the candidate-7 matrix entry and the test_policy
     `current` block with THIS round's measured values (P2b item 3);
     re-run the P2c gates (A + B) on the completed tree; re-run the
     P2c item-3 gate battery (check_repository / pytest / ruff /
     policy validate) to full PASS.
  3. P3.3 Force fresh builds of ALL FIVE affected compose images
     (delete the stale local images first; web picks up next@16.3.8
     via frozen lockfile install; browser-worker picks up the new CfT)
     and run the FULL Compose smoke (all 13 projects) to rc=0 with
     key lines recorded — including the NEW
     `browser-worker-image-policy: OK playwright=1.62.1 cft_revision=
     1689415 chromium=154.0.8037.92 browsers=chromium-only package-
     manager=absent` line.
- P4: push the branch; the final head must have ALL 20 required checks
  SUCCESS (in particular `Supply-chain evidence` must pass at the
  exact final head under the CI's own fresh grype database — this
  re-validates BOTH the next 16.3.8 fix and the CfT 154.0.8037.92
  refresh end-to-end, plus the 079-2-f pyc-drift fix; if it fails,
  see P5).
- P5: if and only if `Supply-chain evidence` fails at the final head:
  download its failure-diagnostics artifact, record its exact contents
  (for a scan recurrence: the exact CVE/GHSA list and artifact files;
  for a drift recurrence: the file-level diff from the retained
  manifests), then STOP and report BLOCKED with that evidence and an
  explicit escalation. No second fix attempt is permitted this round
  under any outcome.
- P6: publish the round report (see Section 9) as a report-only commit
  (`Report publication commit: SELF`) on the same branch.

## 5. Explicit non-goals

- NO exception entry of any kind: `supply-chain/vulnerability-
  exceptions.json` stays `{"schema_version": 1, "exceptions": []}`.
- NO other dependency version change in `pnpm-lock.yaml` (strictly
  next + @next/* only); NO Playwright, Node, base-image, or pnpm-
  setting change; NO change to `apps/web/Dockerfile` or any other
  Dockerfile except `services/browser-worker/Dockerfile` (pin sites
  only, per P2b).
- NO product-code, route, OpenAPI, or renderer behavior change: the
  next patch must be behaviorally inert; if the web build,
  typecheck, or any contract check surfaces ANY drift, STOP and
  report BLOCKED — do not adapt product code.
- NO `tools/supply_chain/*` LOGIC change (pin-value constants only,
  exactly as P2b specifies); NO gate, contract, policy, or
  normalization change.
- NO historical rewrite: matrix candidates 1-6 byte-identical;
  docs/SUPPLY_CHAIN.md line 193 byte-identical; no test_policy
  historical assertion beyond the approved previous-block shift.
- NO migration, NO schema change, NO deployment, NO secret, NO CI-
  workflow file change.
- NO CI re-run of an unmodified head; NO merge; NO other PR touched;
  NO dependabot PR touched; NO new branch.
- NO second fix attempt after any STOP (P1/P3.1/P5).

## 6. Requirements

### R1 - P1 preflight (local only, zero repository changes)

Execute P1.1-P1.3 in order and record the exact outputs in the
report. Any STOP condition: halt, publish the report with the exact
deviation, signal OK.

### R2 - Set A (only if R1 passes)

Apply P2a items 1-7 in order (manifest first, then lockfile, then
docs/notice/sbom/policy-pins). Record the pnpm version, the bounded
lockfile diff summary, and the Gate A outputs.

### R3 - Set B (only if R2 passes)

Apply P2b items 1-2 (the 14 static sites + the approved test_policy
previous-block shift). Run P2c Gate B (parts b-f; part a and Gate A
re-checked in P3.2 after the measured sites land).

### R4 - Measured re-qualification + fresh builds + full smoke (P3)

Execute P3.1-P3.3 and record: the measured candidate-7 values, the
zero-unexcepted-Critical scan evidence for ALL SIX images (per-image
gate lines), the web next@16.3.8 confirmation (the
GHSA-vcvr-r3jv-pc5j finding absent), the fresh-build naming lines for
all five images, and the full smoke rc=0 key lines including the new
browser-worker-image-policy line. Complete P3.2 (measured sites) and
the full P2c battery to PASS before P4.

### R5 - Push and CI (P4)

Push the branch; wait for ALL 20 required checks to reach a terminal
state on the exact report-only head S; record the per-check table
with CI/CodeQL run IDs.

### R6 - Report (P6)

Publish the round report (Section 9) as the report-only commit.

## 7. Acceptance criteria (observable)

1. `git diff --name-only T..I` lists EXACTLY the 21 union files
   (set A 7 + set B 15, minus the shared `docs/DEPLOYMENT.md`):
   apps/web/package.json, pnpm-lock.yaml, docs/DEPLOYMENT.md,
   THIRD_PARTY_NOTICES.md, sbom.json,
   tests/repository/test_repository_policy.py,
   tools/check_repository.py, services/browser-worker/Dockerfile,
   supply-chain/policy.json, tools/supply_chain/policy.py,
   tools/supply_chain/evidence.py, tools/compose/smoke.sh,
   tests/packaging/test_oci_contract.py, tests/supply_chain/
   test_evidence.py, tests/supply_chain/test_policy.py,
   supply-chain/browser-worker-critical-matrix.json, README.md,
   docs/CONFIGURATION.md, docs/LICENSE_POLICY.md, docs/SECURITY.md,
   docs/SUPPLY_CHAIN.md — and nothing else; the matrix diff is a
   pure insertion (Gate B(f)); Gate A and Gate B outputs hold as
   recorded.
2. `git diff --name-only C..I` lists exactly 23 files: the 21 of
   criterion 1 plus `oap/orders/079-2-h-next-rce-fix-and-browser-
   cft-154-refresh.md` and `oap/active`.
3. The complete P1 evidence (P1.1 exact 40-line inventory, P1.2
   registry/integrity/advisory outputs including the full critical-
   advisory list, P1.3 sha256/size + endpoint entry + timestamp) is
   recorded in the report.
4. The pnpm version, the bounded lockfile diff proof (no non-next
   version change; settings/overrides byte-identical), the sbom.json
   two-line diff proof, the check_repository PASS, the full pytest
   result (zero failures), and the ruff clean result are recorded.
5. The measured candidate-7 values (image digest, executable sha256,
   `chrome --version`, grype database fields, full scan_result
   fields), the zero-unexcepted-Critical evidence for ALL SIX images,
   the web next@16.3.8 confirmation, the fresh-build evidence for all
   five images, and the full smoke rc=0 key lines are recorded.
6. All 20 required checks SUCCESS on the exact report-only head S
   (per-check table with CI/CodeQL run IDs) — OR, if and only if
   `Supply-chain evidence` failed at I, an honest BLOCKED with the
   exact P5 artifact evidence.
7. S changes only
   `oap/reports/079-2-h-next-rce-fix-and-browser-cft-154-refresh.md`;
   its parent is I; the remote PR head equals S; and
   `git diff --name-only C..S` lists exactly 24 files (the 23 of
   criterion 2 plus the report).
8. Status is COMPLETE only if criteria 1-5 and 7 are evidenced AND
   criterion 6 is satisfied in its SUCCESS form; otherwise BLOCKED/
   PARTIAL with the exact gap.

## 8. Verification and workflow

- Local gates in the order P2c item 3 (check_repository, pytest,
  ruff, policy validate) after each of R2/R3/R4 as specified; the
  measured pipeline is the backend of truth and supersedes local
  scans.
- Push via the normal branch; the remote head after push must be the
  exact I (after P4) and then the exact S (after P6).
- `Report publication commit: SELF` — verify before the response
  signal that the remote PR head is that report-only commit and its
  parent is the literal reported implementation-head SHA I.
- The exact 2-byte OK is written to `response.fifo` only after the
  immutable report + claimed remote state exist.

## 9. Report requirements

`oap/reports/079-2-h-next-rce-fix-and-browser-cft-154-refresh.md`:
work-order identification (identifier, order file path + sha256,
active bytes hex, numeric objective, increment, PR mode); Status
(COMPLETE/BLOCKED/PARTIAL); executive summary; authoritative GitHub
state (repo, PR, base/head branches, base main SHA, round-start C,
transcript commit T full SHA, implementation head I full SHA or the
explicit NONE decision with reason, report commit SELF + parent,
remote head, new-PR/merge statements); changes made; files changed
(the three name-only diffs C..T, T..I, C..S with exact file counts);
acceptance-criteria evidence per criterion (MET/NOT MET/RECORDED
WITH EXACT STATE/PARTIALLY MET with the exact state); local
verification (P1.1-P1.3 exact outputs; R2 pnpm version + bounded
lockfile diff proof + Gate A; R3 site-by-site application record +
Gate B; R4 pipeline log identity, per-image gate lines, measured
candidate-7 values, web confirmation, reproducibility lines, fresh-
build naming lines, smoke key lines); GitHub CI/required-checks
table (or the P5 BLOCKED evidence); local setup/dependencies (evidence
paths retained in /tmp/0792h*); documentation (which docs sites
changed); safety and scope confirmations (per Section 5, each
CONFIRMED/NO); cumulative base->head grouped table (Section 10
schema, exact numstat, report lines excluded); known limitations /
blockers; recommended strategic follow-up (only if BLOCKED).

## 10. Predeclared review budget (2026-09-14 review-unit governance)

Expected grouped size at I (base `577509e` -> I), approximate,
superseded by the exact numstat table at review:

| Category | Files (at I) | Est. +/- lines |
|---|---|---|
| Production/config | 23 | ~+595 / -92 |
| Migrations | 0 | 0 / 0 |
| Tests/evidence | 16 | ~+1370 / -12 |
| Generated artifacts | 8 | ~+430 / -12 |
| Docs | 10 | ~+18 / -16 |
| OAP transcript (at T / at S) | 16 / 17 | ~+5900 / +6600 |
| TOTAL (at I / at S) | 73 / 74 | ~+8200 / ~+8900 raw |

Delta this round vs S_g: +6 production/config (apps/web/package.json,
tools/check_repository.py, services/browser-worker/Dockerfile,
tools/supply_chain/policy.py, tools/supply_chain/evidence.py,
tools/compose/smoke.sh), +3 tests/evidence
(tests/repository/test_repository_policy.py, tests/supply_chain/
test_policy.py and tests/supply_chain/test_evidence.py — the last two
NEW in the diff this round), +3 generated (pnpm-lock.yaml, sbom.json,
browser-worker-critical-matrix.json), +6 docs (README.md already in
the diff at S_g; no oap status-doc change is required — their
153.0.8010.52/16.3.3 mentions are immutable historical ledger lines),
+16/+17 transcript. THE ~20-FILE PRODUCTION/CONFIG REVIEW
TRIGGER IS CROSSED BY THIS ROUND (17 -> 23 files). Per the
2026-09-14 amendment this is a REVIEW TRIGGER, not a mechanical quota;
the unit remains reviewable because: single objective (079/2), single
branch, two closed externally-forced repair sets with a complete
immutable site-level record, no new product semantic, full measured
re-qualification. CLOSURE_ONLY BEGINS UPON THIS ROUND'S ACCEPTANCE
(Section 11).

## 11. Review-unit governance (2026-09-14 amendment, in force)

This round is the CLOSING round of the 079/2 review unit. Upon
strategic acceptance: (1) the production/config review trigger is
recorded as crossed (17 -> 23 files); (2) CLOSURE_ONLY begins — no
new semantic family, no adjacent feature, no opportunistic scope, no
next-objective work may enter PR #93; only finite defects/evidence
required to make the already-added behavior safe, correct and
reviewable; separable functionality starts from verified merged main
in another PR (the 079/3 increment per the approved sequence); (3) if
strategic review REJECTS a completion claim, Strategy publishes ONE
finite checklist of unresolved criteria with the executable evidence
required for each, and a later report may claim COMPLETE only if
every named criterion was actually executed; (4) the acceptance
record will state: verified base, accepted exact head, cumulative
base->head diff, grouped size, whether review triggers fired, why the
unit remains reviewable, when CLOSURE_ONLY began, and explicit
confirmation that no new semantic family entered after closure-only.
Errata context for the acceptance record: 079-2-g produced no
implementation head (14 files applied, validated, then reverted
before the P3.1 web-image failure); its measured values are run-bound
and were NOT carried into this round; this round re-measures at its
own head.
