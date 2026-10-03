# OAP Work Order — 079-2-g (browser-worker Chrome-for-Testing 154.0.8037.92
refresh; 079/2 continuation)

> **STATUS: ACTIVATED — operative order.** Published atomically by
> strategy 2026-10-04 to
> `oap/orders/079-2-g-browser-cft-154-refresh.md` with
> `oap/active` = `079-2-g`, as a same-PR continuation of `079-2-a` through
> `079-2-f` (PR #93). It closes the now-sole remaining gate failure of the
> 079/2 review unit: 24 newly published Critical CVEs against the pinned
> Chrome for Testing `153.0.8010.52` in the browser-worker image
> (external scan-database drift in an unchanged image — the same failure
> class as the 078/6 increment). The named backend pyc drift defect is
> already fixed and CI-proven at head `0f5186e`; a green
> `Supply-chain evidence` at this round's head re-confirms it
> end-to-end. The coding agent executes under the normal OAP execution
> contract; strategy remains reviewer/acceptor/merger.

## 1. Identifier and mode

- ID: `079-2-g` (increment-qualified round ID: seventh round of semantic
  increment 2 of numeric Objective 079; same PR as the 079-2-a/b/c/d/e/f
  rounds).
- Mode: CONTINUATION (same branch, same PR). CREATE_NEW_PR: no.
- PR: #93 (`079-2-a: Gallery + LogoGrid media-reference list components
  (079/2)`), branch `oap/079-2-a-gallery-logogrid`, base `main`.
- Do not create, amend, close, or touch any other PR.

## 2. Verified current state (strategy-verified 2026-10-04 against the
079-2-f failure artifact, live GitHub, and the live Chrome-for-Testing
endpoint)

- Remote `main` = `577509e7bc990d85a10af5954bee3c6f7c888a4f`
  (unchanged).
- PR #93 is OPEN, `mergeable: MERGEABLE`,
  `mergeStateStatus: BLOCKED`. Round-start remote head
  `C = 6a46120b75706ef84ee581287b56a2c36a5f9912` (079-2-f report-only
  commit; parent `I_f = 0f5186e863f4c13e4119309109d2420c3b803b60`).
  Chain to base `577509e` previously verified; local worktree clean at
  `C`.
- 079-2-f status is BLOCKED at its P5 branch with the named backend drift
  FIXED and CI-proven at `I_f` (strategy independently re-verified from
  the failure artifact: double-build manifests 0 only_first / 0
  only_second / 0 field differences for all six images, backend
  2821/2821; zero drift lines in the job log). The SOLE remaining gate
  failure is a NEW external class (CI run `37156984390`, job
  `111302265733`, log line 2441, 2026-10-03T22:11:38.2007452Z, 28 seconds
  after the grype database updated): `browser-worker: unexcepted
  Critical vulnerabilities` — exactly 24 Critical CVEs, ALL against the
  single artifact `chrome@153.0.8010.52` (the SHA-256-verified Chrome for
  Testing binary pinned in `services/browser-worker/Dockerfile`, CfT
  revision `1681091`, archive sha256
  `e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9`):
  CVE-2026-102304, CVE-2026-102306, CVE-2026-102308, CVE-2026-102309,
  CVE-2026-102316, CVE-2026-102331, CVE-2026-95277, CVE-2026-95281,
  CVE-2026-95283, CVE-2026-95284, CVE-2026-95299, CVE-2026-95310,
  CVE-2026-95311, CVE-2026-95313, CVE-2026-95318, CVE-2026-95325,
  CVE-2026-95329, CVE-2026-95331, CVE-2026-95339, CVE-2026-95347,
  CVE-2026-95349, CVE-2026-95350, CVE-2026-95356, CVE-2026-95357.
  Grype fix records from the artifact: 18 fixed in `154.0.8037.57`, 6
  fixed in `154.0.8037.92`. `supply-chain/vulnerability-exceptions.json`
  is EMPTY; policy `fail_severities: [Critical]`,
  `unfixed_critical_still_fails: true` — none of the 24 is excepted.
- Strategy CfT pre-verification (2026-10-04 ~00:40 CEST, endpoint
  `https://googlechromelabs.github.io/chrome-for-testing/
  last-known-good-versions.json`, file timestamp
  2026-10-03T01:32:42Z): the **Stable** channel is
  `154.0.8037.92` at revision `1689415` (Beta/Dev/Canary are 156.x/
  157.x — out of scope). linux64 archive URL:
  `https://storage.googleapis.com/chrome-for-testing-public/
  154.0.8037.92/linux64/chrome-linux64.zip`; strategy-measured SHA-256
  `ff43322f335e436b2f4dcdfeeec5db032299e335a7e8c1c618b326e100ce8732`
  (196,202,491 bytes, measured 2026-10-04 00:36 CEST). You must
  independently re-verify this hash in P1; a mismatch means STOP and
  report BLOCKED (do NOT pin a different hash).
- Closed old-value inventory at `C` (strategy-verified):
  `git grep -n '153\.0\.8010\.52\|1681091\|e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9'
  -- . ':!oap'` = exactly 60 lines across exactly 15 files:
  `README.md` (2), `docs/CONFIGURATION.md` (2), `docs/DEPLOYMENT.md` (4),
  `docs/LICENSE_POLICY.md` (1), `docs/SECURITY.md` (2), `docs/
  SUPPLY_CHAIN.md` (4), `services/browser-worker/Dockerfile` (7),
  `supply-chain/browser-worker-critical-matrix.json` (13),
  `supply-chain/policy.json` (5), `tests/packaging/
  test_oci_contract.py` (2), `tests/supply_chain/test_evidence.py` (2),
  `tests/supply_chain/test_policy.py` (8), `tools/compose/smoke.sh` (2),
  `tools/supply_chain/evidence.py` (1), `tools/supply_chain/policy.py`
  (5).
- History-isolation rule: most old-value references are CURRENT-state
  pins to update, but the following are IMMUTABLE historical evidence
  and MUST remain byte-identical: (i) matrix
  `qualification_history` entries candidate-3/4/5/6 in their entirety
  (this includes the matrix lines carrying `1681091`,
  `153.0.8010.52`, and `e66f...`: candidate-4 lines 71/80, candidate-5
  lines 129/138, candidate-6 lines 182/188/189/191/193/198/199/215/236
  at `C`); (ii) `tests/supply_chain/test_policy.py` assertions that
  verify historical entries (after this round, the `previous` =
  `qualifications[-2]` block asserts the candidate-6 values, which
  legitimately contain the old version/revision/sha); (iii)
  `docs/SUPPLY_CHAIN.md` line 193 (the 078-t historical narrative).
  The matrix update is a PURE APPEND of a candidate-7 entry at the end
  of `qualification_history`.
- Precedent: increment 078/6 (round 078-6-a, PR #86, accepted/merged at
  `0faebd98`) resolved the identical failure class (newly published
  Critical CVEs against the pinned CfT) by a version+hash refresh within
  the established qualification mechanism.

## 3. Strategic context

- The 079/2 review unit is one finite externally-forced
  packaging/security qualification away from closure: all product work
  (Gallery/LogoGrid, catalog 31, bounded error vocabulary, fail-closed
  renderers, exact OpenAPI delta) is delivered and CI-proven; the Alpine
  and apache pin repairs are CI-proven; the backend pyc drift is fixed
  and CI-proven at `I_f`. The browser-worker image, however, carries a
  pinned browser binary with 24 unexcepted Critical CVEs — a safety
  defect of the shipped artifact and a hard gate failure.
- Decision, recorded: OPTION (a) version refresh (NOT the
  time-boxed-exception regime): a patched Stable release exists
  (`154.0.8037.92`, grype-attested fixing release for all 24 CVEs), so
  the 072-i/j/n exception mechanism (for no-fix cases) is NOT used;
  `supply-chain/vulnerability-exceptions.json` stays EMPTY. The refresh
  follows the 078-6-a mechanism exactly (CfT version + archive sha256 +
  revision + executable path + policy/matrix/test/doc pins + smoke
  assertion + measured re-qualification entry).
- Review-unit governance: this round crosses the ~20-file
  production/config review trigger (17 -> 21 files). Per the 2026-09-14
  amendment the unit enters CLOSURE_ONLY upon this round's acceptance:
  the trigger is a review trigger, not a quota; strategy's cumulative
  review finds the unit still a single semantic family plus
  externally-forced qualification repairs, and no new semantic family
  enters. After this round, only finite defect/evidence work may occur
  in this PR.

## 4. Bounded scope (exactly)

- P1 (preflight, ZERO repository changes):
  1. P1.1 Run the closed inventory grep of Section 2 at `C`; record the
     exact output; it must be exactly the 60 lines across the 15 closed
     files (per-file counts as stated). Any deviation: STOP, report
     BLOCKED.
  2. P1.2 Download the target archive from the closed URL; record
     `sha256sum` and byte size; it MUST be
     `ff43322f335e436b2f4dcdfeeec5db032299e335a7e8c1c618b326e100ce8732`
     and 196,202,491 bytes. Any mismatch: STOP, report BLOCKED (do NOT
     pin a different hash).
  3. P1.3 Query the CfT `known-good-versions-with-downloads.json`
     endpoint (closed URL); verify the `154.0.8037.92` entry:
     `revision` = `1689415`, linux64 download URL = the closed URL;
     record the entry and the `last-known-good-versions.json`
     `timestamp` field. Any deviation: STOP, report BLOCKED.
- P2 (the pin refresh, exactly the 15 closed files):
  1. `services/browser-worker/Dockerfile` (7 lines at `C`: 15, 16, 21,
     33, 49, 50, 61): archive URL -> the closed 154.0.8037.92 URL;
     archive sha256 -> `ff43322f335e436b2f4dcdfeeec5db032299e335a7e8c1c618b326e100ce8732`;
     version assertion string -> `Google Chrome for Testing 154.0.8037.92` + one trailing space (as today); the comment line ->
     154.0.8037.92 / CfT revision 1689415;
     `BROWSER_WORKER_CHROMIUM_EXECUTABLE` ->
     `/ms-playwright/chromium-1689415/chrome-linux64/chrome`;
     `BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION` -> `154.0.8037.92`;
     the `COPY --from=builder` destination ->
     `/ms-playwright/chromium-1689415/chrome-linux64`.
  2. `supply-chain/policy.json` (5 lines, 166-170):
     `chromium_revision` -> `1689415`; `chromium_version` ->
     `154.0.8037.92`; `chromium_executable` ->
     `/ms-playwright/chromium-1689415/chrome-linux64/chrome`;
     `chromium_archive_url` -> the closed URL; `chromium_archive_sha256`
     -> `ff43322f...`.
  3. `tools/supply_chain/policy.py` (5 lines, 356-365): the matching
     five validation constants.
  4. `tools/supply_chain/evidence.py` (1 line, 36): the browser-worker
     boundary directory -> `ms-playwright/chromium-1689415/`.
  5. `tools/compose/smoke.sh` (2 lines, 254-255): the `chrome --version`
     regex -> `^Google Chrome for Testing 154[.]0[.]8037[.]92 *$`; the
     OK echo -> `cft_revision=1689415 chromium=154.0.8037.92`
     (all other fields of that line unchanged).
  6. `tests/packaging/test_oci_contract.py` (2 lines, 152, 154):
     `BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION=154.0.8037.92`; the
     archive sha256 assertion -> `ff43322f...`.
  7. `tests/supply_chain/test_evidence.py` (2 lines, 407-408): the
     chrome purl/version fixture -> `154.0.8037.92`.
  8. `tests/supply_chain/test_policy.py` (the two qualification
     assertion blocks only): the `previous` block (currently asserting
     candidate-5) -> assert the candidate-6 values read from the matrix
     (candidate label `candidate-6 CfT: 153.0.8010.52 measured scan
     coverage`, revision `1681091`, version `153.0.8010.52`, archive
     sha256 `e66f...`, executable
     `/ms-playwright/chromium-1681091/chrome-linux64/chrome`, image
     digest `sha256:4177c64fae4cb7d61e114e6e5c797fa239cc0f394e9d6f3f1d4dfeef9a6bf5b2`,
     and its existing measured scan fields — preserving the current
     assertion structure and line count); the `current` block
     (currently asserting candidate-6) -> assert the measured candidate-7
     values (same key structure, values from P3's measured pipeline run:
     endpoint timestamp, revision `1689415`, version `154.0.8037.92`,
     archive sha256 `ff43322f...`, executable
     `/ms-playwright/chromium-1689415/chrome-linux64/chrome`, the NEW
     browser-worker image digest and executable sha256 measured from the
     built image, the fresh grype database schema/built/checksum, the
     new `chrome_purl` `pkg:generic/chrome@154.0.8037.92`, and the
     measured scan_result fields). No other test change.
  9. `supply-chain/browser-worker-critical-matrix.json` (PURE APPEND):
     add `candidate-7 CfT: 154.0.8037.92 measured scan coverage` as the
     LAST entry of `qualification_history`, with the candidate-6 field
     structure and measured values: `official_metadata` (the two closed
     endpoint URLs, the recorded endpoint `timestamp`, channel Stable,
     version, revision `1689415`, platform linux64, the closed
     `archive_url`); `archive_sha256` `ff43322f...`; `runtime` (image
     `browser-worker`, the NEW measured `image_digest`, the unchanged
     base image, the new executable path, `executable_version`
     `Google Chrome for Testing 154.0.8037.92`, the NEW measured
     `executable_sha256`); `scanner` (grype 0.117.0, fresh measured
     `database_schema`/`database_built`/`database_checksum`, syft
     1.51.0); `sbom` (SPDX-2.3, `chrome_purl`
     `pkg:generic/chrome@154.0.8037.92`, `chrome_version`, the
     unchanged playwright purl); `scan_result` (result PASS,
     evidence_runner, image_count 6, critical 0, unexcepted_critical 0,
     measured `high_review_findings`, measured browser-worker match
     counts, exception_count 0, measured `browser_worker_scan_sha256`,
     checksum_validation PASS); `qualification_date` `2026-10-04`;
     `history_note` stating: the 079-2-g refresh pins CfT
     154.0.8037.92 (revision 1689415) and clears all 24
     Critical CVE-2026-952xx/CVE-2026-1023xx findings first published
     on/around 2026-09-30 (fixed in 154.0.8037.57/154.0.8037.92 per the
     pinned Grype advisory data), with pinned Grype 0.117.0 on the fresh
     database; local measured pipeline run; final remote revalidation
     is the Supply-chain evidence required check on the exact report-
     only head per order 079-2-g acceptance criterion 6; no exception
     added and no gate weakened. Entries candidate-3/4/5/6 remain
     byte-identical.
  10. `README.md` (lines 116-117): current qualification statement ->
     154.0.8037.92 / revision 1689415 (the "replacing the vulnerable
     152.0.7977.82 payload" provenance clause stays).
  11. `docs/CONFIGURATION.md` (lines 111-112): the two env-var table
     rows -> new executable path / expected version.
  12. `docs/DEPLOYMENT.md` (lines 112, 174-176): current-state table
     row + the exact archive SHA-256 statement -> 154.0.8037.92 /
     1689415 / `ff43322f...`.
  13. `docs/LICENSE_POLICY.md` (line 25): current statement ->
     154.0.8037.92.
  14. `docs/SECURITY.md` (lines 182-183): current statement ->
     154.0.8037.92 / 1689415 / `ff43322f...`.
  15. `docs/SUPPLY_CHAIN.md` (lines 134, 140, 272): current-state
     statements -> 154.0.8037.92 / 1689415 / new executable directory;
     line 193 (078-t historical narrative) stays byte-identical.
  16. POST-EDIT gates (all must hold; record exact outputs):
     (a) `git grep -c '154\.0\.8037\.92' -- . ':!oap'` shows the new
     version in exactly these files: README.md, docs/CONFIGURATION.md,
     docs/DEPLOYMENT.md, docs/LICENSE_POLICY.md, docs/SECURITY.md,
     docs/SUPPLY_CHAIN.md, services/browser-worker/Dockerfile,
     supply-chain/browser-worker-critical-matrix.json,
     supply-chain/policy.json, tests/packaging/test_oci_contract.py,
     tests/supply_chain/test_evidence.py, tests/supply_chain/
     test_policy.py, tools/compose/smoke.sh, tools/supply_chain/
     policy.py (14 files); `git grep -c '1689415' -- . ':!oap'`
     additionally shows `tools/supply_chain/evidence.py` (15 files).
     (b) `git grep -n 'e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9'
     -- . ':!oap'` = exactly TWO lines: the matrix candidate-6
     `archive_sha256` line and the test_policy `previous`-block
     candidate-6 sha assertion.
     (c) `git grep -n '153\.0\.8010\.52' -- . ':!oap'` = exactly NINE
     lines: five in the matrix candidate-6 entry (candidate label,
     version, archive_url, executable_version, chrome_purl), three in
     the test_policy `previous` block (candidate label, version,
     chrome_purl), one in docs/SUPPLY_CHAIN.md line 193.
     (d) `git grep -n '1681091' -- . ':!oap'` = exactly NINE lines: six
     in the matrix (candidate-4 revision+executable, candidate-5
     revision+executable, candidate-6 revision+executable), two in the
     test_policy `previous` block (revision, executable), one in
     docs/SUPPLY_CHAIN.md line 193.
     (e) ZERO occurrences of any old value in the 12 non-history files
     (the 15 closed files minus the matrix and
     docs/SUPPLY_CHAIN.md).
     (f) the matrix file parses as JSON; `git diff C..I --
     supply-chain/browser-worker-critical-matrix.json` shows a PURE
     INSERTION (only added lines) — no historical entry line modified.
     Any gate failure: STOP, report BLOCKED.
- P3 (measured re-qualification + fresh builds + full smoke):
  1. Run the local measured pipeline for the browser-worker image with
     the refreshed pin (the `tools/supply_chain/run.sh` backend-of-
     truth flow used for candidate-6: build the browser-worker image
     from the refreshed Dockerfile, measure the image digest, the
     executable sha256 and `chrome --version`, run the pinned Grype
     0.117.0 scan with the freshly updated database, and record the
     exact measured values). EXPECTED: `chrome --version` = `Google
     Chrome for Testing 154.0.8037.92`; zero Critical findings on the
     browser-worker image (the 24 named CVEs absent — they are fixed in
     this version); record the full scan_result fields.
  2. Fill the candidate-7 matrix entry and the test_policy `current`
     block with the measured values (P2.8/P2.9), then run the P2.16
     post-edit gates.
  3. Force fresh builds of ALL FIVE affected compose images (delete the
     stale local images first; the browser-worker must pick up the new
     CfT) and run the FULL Compose smoke (all 13 projects) to rc=0 with
     the key lines recorded — including the NEW
     `browser-worker-image-policy: OK playwright=1.62.1 cft_revision=
     1689415 chromium=154.0.8037.92 browsers=chromium-only package-
     manager=absent` line and the unchanged apache edge image on
     `openssl=3.0.13-0ubuntu3.16` (layer-cached provenance from the
     079-2-d smoke log is acceptable, as in 079-2-f).
- P4: push the branch; the final head must have ALL 20 required checks
  SUCCESS (in particular `Supply-chain evidence` must pass at the exact
  final head with the refreshed pin — this also re-confirms the pyc
  drift fix end-to-end under the updated grype database; if it fails,
  see P5).
- P5: if and only if `Supply-chain evidence` fails at the final head:
  download its failure-diagnostics artifact, record its exact contents
  (for a drift recurrence: the file-level diff from the retained
  manifests; for a scan recurrence: the exact CVE list and artifact
  files), then STOP and report BLOCKED with that evidence and an
  explicit escalation. No second fix attempt is permitted this round
  under any outcome.
- P6: publish the round report (see Section 9) as a report-only commit
  (`Report publication commit: SELF`) on the same branch.

## 5. Explicit non-goals

- NO exception entries: `supply-chain/vulnerability-exceptions.json`
  stays EMPTY (a patched Stable exists; the 072-i/j/n time-boxed
  exception regime is for no-fix cases only).
- No change to the Playwright base image (`v1.62.1-noble` digest pin),
  node, pnpm, playwright-core, lockfiles, or any application code.
- No change to any Dockerfile other than `services/browser-worker/
  Dockerfile`; no change to `services/backend/Dockerfile`.
- No change to `tools/supply_chain/` logic beyond the five policy.py
  constants and the one evidence.py boundary directory (pin values only;
  the comparison, normalization, validator, gate, and contract are
  untouched; the double-build reproducibility gate is NOT weakened).
- No historical rewrite: matrix candidate-3/4/5/6 byte-identical;
  docs/SUPPLY_CHAIN.md line 193 byte-identical; no OAP transcript edit
  beyond this round's own order/active/report.
- No product code, migration, workflow, or other documentation change
  beyond P2.
- No CI re-run is permitted for an unmodified head (flake policy); a new
  pushed head supersedes.
- If any P1 expectation deviates (hash, endpoint, inventory): no
  implementation under any outcome (Section 4 P1).
- Do not touch dependabot PRs. Do not merge. `active` is replaced by
  this order per protocol.

## 6. Requirements

### R1 - P1 preflight (local only, zero repository changes)

Execute P1.1, P1.2, P1.3 in order and record all evidence (exact grep
output; archive sha256 + size; endpoint entry + timestamp). Any
deviation: STOP and report BLOCKED; do not proceed to R2.

### R2 - Pin refresh (only if R1 passes)

Apply exactly the 15-file change of Section 4 P2 with all P2.16 post-
edit gates; then run `uv run --frozen python tools/check_repository.py`
(must PASS) and `uv run --frozen pytest tests/packaging/
tests/supply_chain/ -q` (must pass); then `uv run --frozen ruff check`
and `uv run --frozen ruff format --check` on the touched Python paths
(must be clean). Record all results.

### R3 - Measured re-qualification + fresh builds + full smoke (P3)

Execute P3.1-P3.3 and record the measured candidate-7 values, the
zero-Critical scan evidence, the fresh-build naming lines for all five
images (browser-worker with the new CfT), and the full smoke rc=0 key
lines including the new browser-worker-image-policy line.

### R4 - Push and CI (P4)

Push the implementation commit of this round to the same branch. Verify
(and report) the terminal state of ALL 20 required checks on the exact
final head, with the per-check table and run IDs. If `Supply-chain
evidence` fails, execute P5 and stop.

### R5 - Report (P6)

Publish `oap/reports/079-2-g-browser-cft-154-refresh.md` as a report-
only commit (SELF) whose parent is this round's implementation head.

## 7. Acceptance criteria (observable)

Let T = this round's transcript commit (order + `oap/active` bytes
only), I = this round's implementation head, S = the report-only commit,
C = `6a46120b75706ef84ee581287b56a2c36a5f9912`.

1. `git diff --name-only T..I` lists exactly the 15 closed files of
   Section 4 P2 (and nothing else); the matrix diff is a pure insertion
   (P2.16(f)); the old-value post-edit greps (P2.16(b)-(e)) hold with
   the recorded outputs.
2. `git diff --name-only C..I` lists exactly 17 files: the 15 of
   criterion 1 plus
   `oap/orders/079-2-g-browser-cft-154-refresh.md` and `oap/active`.
3. The complete P1 evidence (P1.1 exact 60-line inventory, P1.2
   sha256/size match, P1.3 endpoint entry + timestamp) is recorded in
   the report.
4. The `tools/check_repository.py` PASS, the pytest result, and the ruff
   clean result are recorded in the report.
5. The measured candidate-7 values (image digest, executable sha256,
   `chrome --version`, grype database fields, scan_result fields), the
   zero-Critical browser-worker scan evidence, the fresh-build
   evidence for all five images, and the full smoke rc=0 key lines
   (including the new browser-worker-image-policy line) are recorded in
   the report.
6. All 20 required checks SUCCESS on the exact report-only head S
   (per-check table with CI/CodeQL run IDs) — OR, if and only if
   `Supply-chain evidence` failed at I, an honest BLOCKED with the exact
   P5 artifact evidence.
7. S changes only
   `oap/reports/079-2-g-browser-cft-154-refresh.md`; its parent is I;
   the remote PR head equals S; and `git diff --name-only C..S` lists
   exactly 18 files (the 17 of criterion 2 plus the report).
8. Status is COMPLETE only if criteria 1-5 and 7 are evidenced AND
   criterion 6 is satisfied in its SUCCESS form; otherwise BLOCKED/
   PARTIAL with the exact gap.

## 8. Verification and workflow

- Commit the strategy-published order and `oap/active` bytes exactly
  (blob sha256 verified against the published files) as the transcript-
  only commit T before the implementation commit I; then the report-only
  commit S. One round, one implementation commit; no merge by the
  executor.
- Local, in order: P1.1 closed inventory grep; P1.2 archive hash
  verification; P1.3 endpoint verification (STOP gate); P2 edits +
  P2.16 post-edit gates (R2) + `uv run --frozen python
  tools/check_repository.py` + targeted pytest + ruff; P3.1 measured
  pipeline run; P3.2 matrix/test measured values; P3.3 fresh builds +
  `sh tools/compose/smoke.sh <project>` full smoke (R3); `npx --yes
  markdownlint-cli2@0.23.2` on the report file (zero issues).
- Push, then poll required checks on the exact head until all are
  terminal; report the per-check table with run IDs; if
  `Supply-chain evidence` failed, download its failure-diagnostics
  artifact and execute P5 before the report.
- GitHub workflow: push to the existing branch only.

## 9. Report requirements

`oap/reports/079-2-g-browser-cft-154-refresh.md` must state: identifier
and mode (CONTINUATION, PR #93); the work-order sha256 (file-hash
domain; the git blob ID may be noted alongside); the `oap/active` bytes
and hex; exact transcript commit T, round implementation head I, and
report SELF; the per-file diff summary of the 15-file change (file:line
per site for the 7 Dockerfile lines, the 5 policy.json lines, the 5
policy.py lines, the 1 evidence.py line, the 2 smoke.sh lines, the 2+2
test lines, the pure-insertion matrix append, and the doc lines); the
exact P1 evidence; the P2.16 post-edit gate outputs (the three old-
value grep outputs with their closed line sets, and the new-value file
counts); the `tools/check_repository.py` PASS, pytest, and ruff
evidence; the measured candidate-7 values and the zero-Critical scan
evidence; the fresh-build evidence for all five images and the full
smoke key lines; the complete 20-check per-check table at the exact
final head with run IDs (or, for an honest BLOCKED, the P5 artifact
evidence); the cumulative base->head size table per the 2026-09-14
review-unit governance (base `577509e` -> final head, grouped:
production/config, migrations, tests/evidence, generated artifacts,
docs, OAP transcript; state the review-trigger position: cumulative
production/config 21 files / ~+630 raw lines, trigger crossed by this
round, CLOSURE_ONLY begins upon acceptance); confirmation that no
product code changed, that no exception was added
(`vulnerability-exceptions.json` still empty), that the reproducibility
gate was NOT weakened, that no historical entry was rewritten (matrix
candidate-3/4/5/6 byte-identical; docs/SUPPLY_CHAIN.md line 193
byte-identical), and that no `tools/supply_chain/*` logic changed; and
an honest status.

## 10. Predeclared review budget (2026-09-14 review-unit governance)

- Production/config: 4 NEW files (`services/browser-worker/Dockerfile`,
  `tools/supply_chain/policy.py`, `tools/supply_chain/evidence.py`,
  `tools/compose/smoke.sh`) plus the existing `supply-chain/policy.json`
  -> cumulative 21 files / ~+630 raw lines. Migrations: 0.
- Tests/evidence: 2 NEW files (`tests/supply_chain/test_evidence.py`,
  `tests/supply_chain/test_policy.py`) plus the existing
  `tests/packaging/test_oci_contract.py` and the matrix qualification
  evidence -> cumulative ~15 files / ~+1345 raw lines.
- Generated artifacts: 0. Docs: 5 NEW files (`docs/CONFIGURATION.md`,
  `docs/DEPLOYMENT.md`, `docs/LICENSE_POLICY.md`, `docs/SECURITY.md`,
  `docs/SUPPLY_CHAIN.md`) plus the existing `README.md` -> cumulative 9
  files.
- OAP transcript: this order + one new round report + `active`
  replacement.
- Cumulative after this round (base `577509e` -> final head): approx.
  66 files, ~+7400/-92 (approximate predeclared estimate; the exact
  final table belongs in the report). REVIEW TRIGGER: the ~20-file
  production/config threshold is CROSSED by this round (17 -> 21); per
  the 2026-09-14 amendment the unit enters CLOSURE_ONLY upon this
  round's acceptance (the trigger is a review trigger, not a quota —
  strategy's cumulative review: single semantic family plus
  externally-forced qualification repairs; the unit remains reviewable;
  no new semantic family enters, and none may enter after this round).

## 11. Review-unit governance (2026-09-14 amendment, in force)

This round completes the finite, named, externally forced packaging/
security defect of the 079/2 review unit (24 Critical CVEs on the
pinned CfT binary), following the accepted 078/6 mechanism. No new
semantic family, no adjacent feature, no opportunistic scope. The
079-2-a/b/c/d/e/f rounds are immutable records; their evidence is
adopted by this order. The P1 preflight gate is binding: no
implementation without a fully passing P1. If P5 is triggered, the
round ends in BLOCKED with escalation; any fix beyond this closed
15-file pin refresh (including any exception entry or gate change)
requires a new strategy round and, if structural, human authorization.
CLOSURE_ONLY begins upon this round's acceptance (trigger crossed);
after it, only finite defect/evidence work may occur in this PR. The
reproducibility gate is never waived, and a green merge is never
obtained by re-running until luck.
