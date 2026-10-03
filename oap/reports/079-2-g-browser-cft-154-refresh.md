# OAP Coding-Agent Report — 079-2-g

## Work order

- Identifier: 079-2-g (increment-qualified round ID: seventh round of
  semantic increment 2 of numeric Objective 079, increment 079/2)
- Work-order file:
  `oap/orders/079-2-g-browser-cft-154-refresh.md`
- Work-order sha256 (file-hash domain, computed over the published file):
  `caa04aefd6cdab58e3ac10d7680187ecff5e3a2f05891ad2c64febfda3265021`
  (git blob ID of the committed file: `91088c71354480147d704829934aa185626828b7`;
  different hash domains, byte-identical commit)
- `oap/active` bytes: `079-2-g\n` (hex `3037392d322d670a`)
- Numeric objective: 079 (increment 079/2; this round = the browser-worker
  Chrome-for-Testing `154.0.8037.92` pin refresh closing the
  now-sole remaining gate failure of the 079/2 review unit, per the
  recorded decision path of order §3)
- PR mode: AMENDED_EXISTING_PR (PR #93; NO implementation commit exists
  this round — the round ended BLOCKED at the P3.1 measured pipeline
  before a compliant implementation head could be produced; only the
  transcript and the report commits land on the branch this round)

## Status

BLOCKED

## Executive summary

The P1 preflight (order §4) was executed exactly as specified with ZERO
repository changes and met EVERY stated expectation: (P1.1) the closed
inventory grep at C returned exactly 60 lines across exactly 15 files with
the per-file counts as stated; (P1.2) the independently downloaded
`154.0.8037.92` linux64 archive is byte-exact
(sha256 `ff43322f335e436b2f4dcdfeeec5db032299e335a7e8c1c618b326e100ce8732`,
196,202,491 bytes — the strategy-measured value); (P1.3) the closed CfT
endpoint entry for `154.0.8037.92` carries revision `1689415` and the exact
linux64 archive URL, with `last-known-good-versions.json` timestamp
`2026-10-03T01:32:42.960Z`. P2 was then applied: 14 of the 15 closed files
(the two measured-value sites — the matrix `candidate-7` append and the
`test_policy` `current` block — are, per order §4 P3.2, filled with
measured pipeline values and were correctly deferred).

The P3.1 local measured pipeline (the `tools/supply_chain/run.sh`
backend-of-truth flow — six images built twice, SBOMs, pinned Grype
0.117.0 scan on a freshly updated database) then FAILED — in a NEW
external failure class, not the named one. The refreshed browser-worker
pin works exactly as designed: the browser-worker image scanned with ZERO
Critical / ZERO unexcepted Critical (gate PASS), all 24 named
CVE-2026-952xx/CVE-2026-1023xx findings ABSENT (fixed in
154.0.8037.57/154.0.8037.92), measured
`chrome --version` = `Google Chrome for Testing 154.0.8037.92`, and the
double-build reproducibility comparison passed for all six images
(backend 2821/2821 — the 079-2-f pyc-drift fix re-verified locally under
this run). The gate failed on the WEB image instead: one unexcepted
Critical, `GHSA-vcvr-r3jv-pc5j` on `next@16.3.3` (the web image's
Next.js product dependency; advisory fix `16.3.6`, first-observed
2026-09-30 — the same publication window as the 24 Chrome CVEs), reported
immediately after the pipeline's grype vulnerability database updated to
latest (log line 1818; error line 1819). This is a newly published
external Critical in an UNCHANGED image/lockfile — outside this order's
closed 15-file pin refresh (order §5 forbids any product-code, lockfile,
workflow, or other change beyond P2; §11: any fix beyond the closed
refresh, including any exception entry or gate change, requires a new
strategy round).

Consequences (recorded decision): (1) the ordered `candidate-7` matrix
entry requires a fully measured PASS across all six images
(`result: PASS`, `image_count: 6`, `critical: 0`), which the failed
pipeline cannot produce — a compliant implementation head I (the exact
15-file change with the pure matrix insertion and measured test values)
cannot be created; (2) pushing a non-conformant partial head was not
performed — the remote branch head remains C, and the CI
`Supply-chain evidence` check would fail on the web Critical anyway
(same pinned grype, advisory already in the public database); (3) the
14 applied P2 files were reverted to T (zero net repository change
beyond the transcript); (4) per the order's STOP/escalation governance
(§3, §11) and the 079-2-e precedent, this round ends BLOCKED with this
evidence and an explicit escalation. No exception was added
(`supply-chain/vulnerability-exceptions.json` remains empty), no gate was
weakened, no historical entry was touched, no `tools/supply_chain/*`
logic changed, no merge, no other PR touched.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#93](https://github.com/ulfe-lmi/slaif-agent-site/pull/93), state
  OPEN (`mergeable: MERGEABLE`, `mergeStateStatus: BLOCKED` on the
  failing required check from the prior head)
- Base/head branches: `main` <- `oap/079-2-a-gallery-logogrid`
- Base `main`: `577509e7bc990d85a10af5954bee3c6f7c888a4f` (unchanged)
- Round-start remote SHA C (079-2-f report-only commit):
  `6a46120b75706ef84ee581287b56a2c36a5f9912`
- Transcript commit T (order + `active` bytes only, 2 files; parent C):
  `741dd932144e72257f3864c70d8e8956d3dfafc2` (PUSHED)
- Implementation head SHA I: NONE — no implementation commit exists; the
  P3.1 measured pipeline failure (new external web Critical) stopped the
  round before the compliant 15-file implementation head could be
  produced (the two measured-value sites cannot be filled with measured
  PASS values)
- Report publication commit: SELF (first parent =
  `741dd932144e72257f3864c70d8e8956d3dfafc2`)
- Remote PR head after report publication: SELF
- New PR this turn: no; merge performed: NO

## Changes made

1. Transcript commit T: strategy-published order and `oap/active` bytes
   committed exactly (order file sha256
   `caa04aefd6cdab58e3ac10d7680187ecff5e3a2f05891ad2c64febfda3265021`
   verified on the published file; git blob ID
   `91088c71354480147d704829934aa185626828b7` on the committed blob;
   active bytes `079-2-g\n` = hex `3037392d322d670a` verified on the
   committed blob). PUSHED.
2. Implementation commit: NONE — see "P3.1" below; the 14 locally applied
   P2 files were reverted before any push (worktree clean at T).
3. This report (via the SELF report-only commit, parent T).

## Files changed

- `git diff --name-only C..T` = exactly two files:
  `oap/orders/079-2-g-browser-cft-154-refresh.md` + `oap/active`
  (transcript only).
- `git diff --name-only T..SELF` = exactly one file: this report.
- `git diff --name-only C..SELF` = exactly three files: the two transcript
  files + this report. Worktree clean at SELF.

## Acceptance-criteria evidence

### Criterion 1 (T..I = exactly the 15 closed files; matrix pure
insertion; post-edit greps)

NOT MET — no implementation head I exists. The 14 static P2 sites were
applied locally (verified pair-by-pair, count-exact) and the post-edit
gates P2.16(a)-(f) were not evaluated in full (they are, per order §8,
bound to the P3.2 measured-value completion, which did not occur). The
per-site applied diff is recorded under "P2 (applied, then reverted)".
The single failed test on the 14-file tree
(`test_browser_runtime_history_records_fixed_candidate_and_old_findings`)
is the expected consequence of the atomic P3.2 unit (matrix append +
both test-policy block shifts) being incomplete.

### Criterion 2 (C..I = exactly 17 files)

NOT MET — no implementation head I exists (consequence of criterion 1).

### Criterion 3 (complete P1 evidence recorded)

MET — see "Local verification" below: P1.1 exact 60-line output across
the 15 closed files (per-file counts matching the order exactly), P1.2
sha256/size exact match, P1.3 endpoint entry + timestamp.

### Criterion 4 (check_repository PASS, pytest, ruff recorded)

RECORDED WITH EXACT STATE — on the applied 14-file tree (before the
P3.1 pipeline, before revert): `tools/check_repository.py` ->
`PASS repository policy` (rc=0); `uv run --frozen pytest tests/packaging/ tests/supply_chain/ -q` -> `85 passed, 54 subtests passed,
1 failed` (the single failure is the expected test_policy history test of
criterion 1); `uv run --frozen ruff check` -> `All checks passed!`;
`uv run --frozen ruff format --check` on the five touched Python paths ->
`5 files already formatted`. Additionally
`uv run --frozen python -m tools.supply_chain.policy validate` ->
`supply-chain-policy: OK` immediately after the P2 edits. (The §8
gate-before-pipeline sequence was partially reordered: the pipeline was
launched after `policy validate` rather than after the full R2 gate
battery; the full battery's result on the 14-file tree is recorded here.
No gate was weakened.)

### Criterion 5 (measured candidate-7 values, zero-Critical scan, fresh builds, smoke key lines)

PARTIALLY MET, then BLOCKED. The browser-worker half of P3.1 is fully
evidenced (measured values below: version, image digest, executable
sha256, grype database fields, scan fields — ZERO Critical, all 24 named
CVEs absent). The full-pipeline `scan_result` (six images, `critical: 0`,
`result: PASS`) could NOT be produced: the web image failed the Critical
gate with the newly published `GHSA-vcvr-r3jv-pc5j` (`next@16.3.3`).
P3.3 (fresh five-image builds + full smoke) was not executed — the
ordered measured re-qualification prerequisite (P3.1/P3.2) did not
complete, and the round stopped.

### Criterion 6 (all 20 required checks SUCCESS at the exact report-only
head S — OR the honest P5 BLOCKED branch)

BLOCKED branch (honest): no compliant implementation head I exists, so
no per-check table at a final implementation head is produced; the
remote PR head remains C (the 079-2-f head, whose `Supply-chain evidence`
failure is the browser-worker class this round was designed to close and
which the local measured run proves closed for browser-worker). The local
measured pipeline — the identical `tools/supply_chain/run.sh`
backend-of-truth flow of the CI job, pinned Grype 0.117.0 on a freshly
updated database — failed on the NEW external web Critical before any
push; the exact evidence is recorded below (pipeline log line 1819,
retained failure diagnostics). A CI-executed re-confirmation is available
to strategy in the follow-up round (after the web fix, the same gate
revalidates the browser pin end-to-end).

### Criterion 7 (S report-only; parent rule; remote head S; C..S file
count)

S changes only this report; its parent is T (`741dd932144e72257f3864c70d8e8956d3dfafc2`)
— the transcript commit, because no implementation head I exists this
round (the 079-2-e precedent for parent selection); the remote PR head
equals S after push; `git diff --name-only C..S` lists exactly three
files (the two transcript files + this report) — the round produced no
implementation files. Verified before the response signal.

### Criterion 8 (honest status)

BLOCKED. Criteria 3 (P1) and 7 (S mechanics, with the documented parent
substitution) are evidenced; criterion 5 is partially evidenced
(browser-worker half complete); criteria 1/2 (the 15-file
implementation) and 6 (gate green at a final head) are NOT satisfiable
in this round because of the newly published external web Critical
outside the closed scope. Exact gap stated; escalation in the section
below.

## Local verification

### P1.1 — closed inventory grep at C (ZERO repository changes)

Command (order §4 P1.1, verbatim):

```bash
git grep -n '153\.0\.8010\.52\|1681091\|e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9' -- . ':!oap'
```

rc=0. Exact output (60 lines, exactly 15 files; per-file counts match
the order's closed inventory exactly — README 2, CONFIGURATION 2,
DEPLOYMENT 4, LICENSE_POLICY 1, SECURITY 2, SUPPLY_CHAIN 4, Dockerfile 7,
matrix 13, policy.json 5, test_oci_contract 2, test_evidence 2,
test_policy 8, smoke.sh 2, evidence.py 1, policy.py 5):

```text
README.md:116:The supply-chain policy qualifies Chrome for Testing `153.0.8010.52` at CfT
README.md:117:revision `1681091`, replacing the vulnerable `152.0.7977.82` payload. The
docs/CONFIGURATION.md:111:| `BROWSER_WORKER_CHROMIUM_EXECUTABLE` | `/ms-playwright/chromium-1681091/chrome-linux64/chrome` | Image-fixed executable |
docs/CONFIGURATION.md:112:| `BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION` | `153.0.8010.52` | Readiness version assertion |
docs/DEPLOYMENT.md:112:| `browser-worker` | Playwright 1.62.1 / Chrome for Testing 153.0.8010.52 (CfT revision 1681091) | `10001:10001` | browser only | read-only worker credential; writable private browser artifacts |
docs/DEPLOYMENT.md:174:`playwright-core==1.62.1` and bakes only Chrome for Testing `153.0.8010.52`
docs/DEPLOYMENT.md:175:(CfT revision `1681091`). The exact amd64 archive SHA-256 is
docs/DEPLOYMENT.md:176:`e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9`.
docs/LICENSE_POLICY.md:25:Testing `153.0.8010.52` from Google's exact SHA-256-verified archive over the
docs/SECURITY.md:182:`153.0.8010.52` archive at CfT revision `1681091`, verified by SHA-256
docs/SECURITY.md:183:`e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9` and kept
docs/SUPPLY_CHAIN.md:134:`153.0.8010.52` at CfT revision `1681091`. The exact linux/amd64 archive is
docs/SUPPLY_CHAIN.md:140:`/ms-playwright/chromium-1681091` tree during both clean image builds. The separate
docs/SUPPLY_CHAIN.md:193:`153.0.8010.52` at CfT revision `1681091`. The 078-t attempt is retained as
docs/SUPPLY_CHAIN.md:272:stable Chrome 152.0.7977.82 qualification; the current 153.0.8010.52
services/browser-worker/Dockerfile:15:      https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.52/linux64/chrome-linux64.zip \
services/browser-worker/Dockerfile:16:    && echo 'e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9  /tmp/chrome-for-testing.zip' \
services/browser-worker/Dockerfile:21:      = 'Google Chrome for Testing 153.0.8010.52 ' \
services/browser-worker/Dockerfile:33:# SHA-256-verified Chrome for Testing 153.0.8010.52 (CfT revision 1681091).
services/browser-worker/Dockerfile:49:    BROWSER_WORKER_CHROMIUM_EXECUTABLE=/ms-playwright/chromium-1681091/chrome-linux64/chrome \
services/browser-worker/Dockerfile:50:    BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION=153.0.8010.52 \
services/browser-worker/Dockerfile:61:COPY --from=builder --chown=10001:10001 /chrome-for-testing/chrome-linux64 /ms-playwright/chromium-1681091/chrome-linux64
supply-chain/browser-worker-critical-matrix.json:71:        "revision": "1681091",
supply-chain/browser-worker-critical-matrix.json:80:        "executable": "/ms-playwright/chromium-1681091/chrome-linux64/chrome",
supply-chain/browser-worker-critical-matrix.json:129:        "revision": "1681091",
supply-chain/browser-worker-critical-matrix.json:138:        "executable": "/ms-playwright/chromium-1681091/chrome-linux64/chrome",
supply-chain/browser-worker-critical-matrix.json:182:      "candidate": "candidate-6 CfT: 153.0.8010.52 measured scan coverage",
supply-chain/browser-worker-critical-matrix.json:188:        "version": "153.0.8010.52",
supply-chain/browser-worker-critical-matrix.json:189:        "revision": "1681091",
supply-chain/browser-worker-critical-matrix.json:191:        "archive_url": "https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.52/linux64/chrome-linux64.zip"
supply-chain/browser-worker-critical-matrix.json:193:      "archive_sha256": "e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9",
supply-chain/browser-worker-critical-matrix.json:198:        "executable": "/ms-playwright/chromium-1681091/chrome-linux64/chrome",
supply-chain/browser-worker-critical-matrix.json:199:        "executable_version": "Google Chrome for Testing 153.0.8010.52",
supply-chain/browser-worker-critical-matrix.json:215:        "chrome_purl": "pkg:generic/chrome@153.0.8010.52",
supply-chain/browser-worker-critical-matrix.json:236:      "history_note": "The 078-6-a refresh pins CfT 153.0.8010.52 (same revision 1681091) and clears all six Critical CVE-2026-917xx findings (fixed in 153.0.8010.47 per the pinned Grype advisory data) with pinned Grype 0.117.0 on the fresh v6.1.9 database built 2026-09-18T06:30:15Z. Local measured pipeline run; final remote revalidation is the Supply-chain evidence required check on the exact report-only head per order 078-6-a acceptance criterion 4. No exception added and no gate weakened."
supply-chain/policy.json:166:    "chromium_revision": "1681091",
supply-chain/policy.json:167:    "chromium_version": "153.0.8010.52",
supply-chain/policy.json:168:    "chromium_executable": "/ms-playwright/chromium-1681091/chrome-linux64/chrome",
supply-chain/policy.json:169:    "chromium_archive_url": "https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.52/linux64/chrome-linux64.zip",
supply-chain/policy.json:170:    "chromium_archive_sha256": "e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9",
tests/packaging/test_oci_contract.py:152:        self.assertIn("BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION=153.0.8010.52", runtime)
tests/packaging/test_oci_contract.py:154:            "e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9",
tests/supply_chain/test_evidence.py:407:                    "purl": "pkg:generic/chrome@153.0.8010.52",
tests/supply_chain/test_evidence.py:408:                    "version": "153.0.8010.52",
tests/supply_chain/test_policy.py:236:        self.assertEqual(previous["official_metadata"]["revision"], "1681091")
tests/supply_chain/test_policy.py:244:            "/ms-playwright/chromium-1681091/chrome-linux64/chrome",
tests/supply_chain/test_policy.py:258:            "candidate-6 CfT: 153.0.8010.52 measured scan coverage",
tests/supply_chain/test_policy.py:263:        self.assertEqual(current["official_metadata"]["revision"], "1681091")
tests/supply_chain/test_policy.py:264:        self.assertEqual(current["official_metadata"]["version"], "153.0.8010.52")
tests/supply_chain/test_policy.py:267:            "e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9",
tests/supply_chain/test_policy.py:271:            "/ms-playwright/chromium-1681091/chrome-linux64/chrome",
tests/supply_chain/test_policy.py:288:            current["sbom"]["chrome_purl"], "pkg:generic/chrome@153.0.8010.52"
tools/compose/smoke.sh:254:  'test "$(find /ms-playwright -mindepth 1 -maxdepth 1 -type d | wc -l)" -eq 1; test -x /ms-playwright/chromium-1681091/chrome-linux64/chrome; test ! -e /usr/bin/npm; test ! -e /usr/bin/corepack; test "$(node --version)" = v24.18.1; /ms-playwright/chromium-1681091/chrome-linux64/chrome --version | grep -Eq "^Google Chrome for Testing 153[.]0[.]8010[.]52 *$"'
tools/compose/smoke.sh:255:echo "browser-worker-image-policy: OK playwright=1.62.1 cft_revision=1681091 chromium=153.0.8010.52 browsers=chromium-only package-manager=absent"
tools/supply_chain/evidence.py:36:    "browser-worker": ("opt/slaif/", "ms-playwright/chromium-1681091/"),
tools/supply_chain/policy.py:356:        or browser_runtime["chromium_revision"] != "1681091"
tools/supply_chain/policy.py:357:        or browser_runtime["chromium_version"] != "153.0.8010.52"
tools/supply_chain/policy.py:359:        != "https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.52/linux64/chrome-linux64.zip"
tools/supply_chain/policy.py:361:        != "e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9"
tools/supply_chain/policy.py:365:        != "/ms-playwright/chromium-1681091/chrome-linux64/chrome"
```

### P1.2 — independent archive download + hash (ZERO repository changes)

```bash
$ curl --fail --location --retry 3 --output /tmp/0792g/cft-154.0.8037.92-linux64.zip \
    https://storage.googleapis.com/chrome-for-testing-public/154.0.8037.92/linux64/chrome-linux64.zip
$ sha256sum /tmp/0792g/cft-154.0.8037.92-linux64.zip
ff43322f335e436b2f4dcdfeeec5db032299e335a7e8c1c618b326e100ce8732  cft-154.0.8037.92-linux64.zip
$ stat -c '%s bytes' /tmp/0792g/cft-154.0.8037.92-linux64.zip
196202491 bytes
```

Verified 2026-10-04 ~00:55 CEST: SHA256
`ff43322f335e436b2f4dcdfeeec5db032299e335a7e8c1c618b326e100ce8732` and
196,202,491 bytes — EXACTLY the strategy-measured value from order §2.
(MET)

### P1.3 — CfT endpoint verification (ZERO repository changes)

- Closed endpoint
  `https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json`
  (retrieved 2026-10-04 ~00:52 CEST): the `154.0.8037.92` entry carries
  `revision: "1689415"` and the linux64 chrome download URL
  `https://storage.googleapis.com/chrome-for-testing-public/154.0.8037.92/linux64/chrome-linux64.zip`
  (the closed URL). (MET)
- `last-known-good-versions.json` `timestamp` field:
  `2026-10-03T01:32:42.960Z`; its Stable channel:
  `{"channel": "Stable", "version": "154.0.8037.92", "revision": "1689415"}`.
  (MET — matches the strategy-recorded timestamp 2026-10-03T01:32:42Z.)
- Cross-check (supplementary, not the closed URL):
  `last-known-good-versions-with-downloads.json` Stable entry lists the
  same linux64 URL for `154.0.8037.92` / revision `1689415`.
- No deviation in P1.1, P1.2, or P1.3 -> P2 authorized.

### P2 (applied, then reverted) — per-file sites

Applied 2026-10-04 ~01:00 CEST with exact count-verified string
replacements (each old string found exactly once unless noted); all 14
files below; the two measured-value sites (matrix append, test_policy
`current` block) deferred to P3.2 per order §8. After the P3.1 STOP, all
14 files were reverted to T (`git checkout -- <14 files>`; worktree
clean). Sites (file:line at C -> new value):

1. `services/browser-worker/Dockerfile`: line 15 archive URL ->
   `.../154.0.8037.92/linux64/chrome-linux64.zip`; line 16 archive sha256
   -> `ff43322f...`; line 21 version assertion ->
   `Google Chrome for Testing 154.0.8037.92` + trailing space (as
   before); line 33 comment -> 154.0.8037.92 / CfT revision 1689415;
   line 49 `BROWSER_WORKER_CHROMIUM_EXECUTABLE` ->
   `/ms-playwright/chromium-1689415/chrome-linux64/chrome`; line 50
   `BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION` -> `154.0.8037.92`; line 61
   `COPY --from=builder` destination ->
   `/ms-playwright/chromium-1689415/chrome-linux64`.
2. `supply-chain/policy.json` lines 166-170: `chromium_revision`
   `1689415`; `chromium_version` `154.0.8037.92`; `chromium_executable`
   `/ms-playwright/chromium-1689415/chrome-linux64/chrome`;
   `chromium_archive_url` closed URL; `chromium_archive_sha256`
   `ff43322f...`.
3. `tools/supply_chain/policy.py` lines 356-365: the matching five
   validation constants (pin values only; no logic change).
4. `tools/supply_chain/evidence.py` line 36: browser-worker boundary
   directory -> `ms-playwright/chromium-1689415/`.
5. `tools/compose/smoke.sh` lines 254-255: in-container executable path
   (both occurrences) -> chromium-1689415; version regex ->
   `^Google Chrome for Testing 154[.]0[.]8037[.]92 *$`; OK echo ->
   `cft_revision=1689415 chromium=154.0.8037.92` (all other fields of
   that line unchanged).
6. `tests/packaging/test_oci_contract.py` lines 152, 154: expected
   version assertion -> `154.0.8037.92`; archive sha256 assertion ->
   `ff43322f...`.
7. `tests/supply_chain/test_evidence.py` lines 407-408: chrome purl ->
   `pkg:generic/chrome@154.0.8037.92`; version -> `154.0.8037.92`.
8. `tests/supply_chain/test_policy.py` `previous` block (lines ~232-250):
   shifted to candidate-6 values (label `candidate-6 CfT: 153.0.8010.52
   measured scan coverage`, revision `1681091`, version
   `153.0.8010.52`, archive sha256 `e66f...`, executable
   `/ms-playwright/chromium-1681091/chrome-linux64/chrome`, image digest
   `sha256:4177c64fae4cb7d61e114e6e5c797fa239cc0f394e9d6f3f1d4dfeef9a6bf5b2`);
   the `ci_run` assertion position (candidate-6 has no `ci_run` field, as
   candidate-6 predates its remote revalidation) was replaced by the
   gate field `scan_result["exception_count"] == 0`, with
   `browser_worker_matches == 1486`, `result == "PASS"`,
   `unexcepted_critical == 0` retained — same assertion count (10) and
   structure. The `current` block (candidate-7, measured values) was
   deferred to P3.2 and NOT applied.
9. `supply-chain/browser-worker-critical-matrix.json`: PURE APPEND of the
   `candidate-7` entry deferred to P3.2 (measured values) and NOT
   applied.
10. `README.md` lines 116-117: qualification statement ->
    `154.0.8037.92` / revision `1689415` (the "replacing the vulnerable
    `152.0.7977.82` payload" provenance clause preserved).
11. `docs/CONFIGURATION.md` lines 111-112: env-var table rows -> new
    executable path / expected version.
12. `docs/DEPLOYMENT.md` line 112 (table row) and lines 174-176 (archive
    SHA-256 statement) -> 154.0.8037.92 / 1689415 / `ff43322f...`.
13. `docs/LICENSE_POLICY.md` line 25 -> 154.0.8037.92.
14. `docs/SECURITY.md` lines 182-183 -> 154.0.8037.92 / 1689415 /
    `ff43322f...`.
15. `docs/SUPPLY_CHAIN.md` lines 134, 140, 272 -> 154.0.8037.92 /
    1689415 / new executable directory; line 193 (078-t historical
    narrative) untouched.

R2 gate results on the applied 14-file tree: recorded under criterion 4.
Post-edit gates P2.16: (a)-(e) would evaluate old-value residues in the
two deferred sites (expected pre-P3.2); (f) matrix pure-insertion not
applicable (no matrix change applied). The historical-isolation rule
(order §2) was honored in every applied site: no candidate-3/4/5/6 matrix
line, no test_policy historical assertion, and no docs/SUPPLY_CHAIN.md
line 193 was modified by any applied edit.

### P3.1 — local measured pipeline (the CI backend-of-truth flow)

Command: `sh tools/supply_chain/run.sh /tmp/0792g-evidence`
(`GITHUB_SHA` unset -> `SLAIF_IMAGE_REVISION=local`, as for candidate-6's
local measured run). Log: `/tmp/0792g/pipeline.log`. Retained evidence:
`/tmp/0792g-evidence/` (including `failure-diagnostics/`).

- Pipeline terminal: FAILURE at the Critical gate (not a build or
  reproducibility failure). Exact lines:

  ```text
  1818: Vulnerability database updated to latest version!
  1819: supply-chain-evidence: ERROR: web: unexcepted Critical vulnerabilities: GHSA-vcvr-r3jv-pc5j
  ```

- Reproducibility (double-build comparison, all six images): PASSED
  before the scan phase (log line 118: `reproducibility: OK
  python-artifacts=2 next-build-id=615a954efe88239119f8f0a0bedb552d
  browser-output=source-contract`; retained manifests: backend 2821
  entries, browser-worker 478, web 3052, nginx 1, postgres 1, apache 199
  — first/second builds compared clean for every image; the backend
  pyc-drift fix from 079-2-f is re-verified locally under this run).
- Browser identity drift check (first vs second build): PASSED
  (all identity fields equal between builds).
- Browser-worker measured values (the P3.1 browser-worker EXPECTEDs, all
  MET):
  - `chrome --version` (build-time assertion + measured identity):
    `Google Chrome for Testing 154.0.8037.92`
  - First-build image digest:
    `sha256:9f062348550320cfa773bb8d58e6d726dd932601a4ea0b7199996247acfbcf79`
  - Measured executable
    `/ms-playwright/chromium-1689415/chrome-linux64/chrome`,
    executable sha256 `439f367a9a24dde467dca9c4e4c2feedd3266899c5a8e3eb17b68b05d4da9f5f`
    (cataloger `supplemental-measured-runtime`, embedded in the
    normalized SBOM)
  - Source archive sha256 in the measured identity: `ff43322f...`
    (matches P1.2)
  - Scan (pinned Grype 0.117.0, freshly updated database): browser-worker
    gate `PASS (zero unexcepted Critical)`; Critical 0, Critical
    exceptions 0; 1,587 total matches (4 High, 1,467 Medium, 102 Low, 14
    Negligible); ALL 24 named CVEs ABSENT (the refresh clears them, as
    attested by the pinned advisory data: fixed in
    154.0.8037.57/154.0.8037.92)
  - Grype database (fresh, fetched during the run): schema `v6.1.10`,
    built `2026-10-03T06:31:58Z`, checksum
    `sha256:397565327faac36f757903f87e31ac403a251bed21c0f0ec5b87f912c5143ab6`;
    syft 1.51.0
  - SBOM sha256 (browser-worker, normalized SPDX-2.3):
    `24cab651a3f9faecb2d148800cdb1010e26d4ba1ec8f708ffa086c5bdd2f00dd`;
    scan SBOM sha256
    `c4dbdca1a426f0c7200f55c78be3897ba7f2400c6d4a9a61b573042e38661ca6`;
    scan sha256 `0044ecb74f015a3bba4a67e839e0c98d18c302a64848e5baf2c0d0e11fdc84a8`
- THE BLOCKING FINDING (new external class, web image): one unexcepted
  Critical — `GHSA-vcvr-r3jv-pc5j` on artifact `next` version `16.3.3`
  (purl `pkg:npm/next@16.3.3`), advisory fix record: `fixed` in
  `16.3.6`, first-observed `2026-09-30`. The web image and its lockfile
  are UNCHANGED by this round (and by the base head's product code) —
  this is freshly published advisory data, the same external
  scan-database drift class as the 24 Chrome CVEs this round targets,
  but on a different package. Web scan totals for the record: 20 matches
  (1 Critical, 6 High, 9 Medium, 4 Low).
- Because the ordered `candidate-7` matrix entry requires
  `scan_result: result PASS, image_count 6, critical 0,
  unexcepted_critical 0`, and the ordered `test_policy` `current` block
  asserts those measured values, the P3.2 completion step is impossible
  with this pipeline outcome. Per the order's STOP governance
  (§3/§11) the round ended BLOCKED here; the 14 applied files were
  reverted; no second fix attempt was made (none is permitted, and no
  fix for `next@16.3.3` is inside the closed scope in the first place:
  it would require a product dependency/lockfile change or an exception
  entry — both forbidden to the executor by order §5/§11).

## GitHub CI / required checks

No implementation head I was pushed; the remote branch head remains C
`6a46120b75706ef84ee581287b56a2c36a5f9912`. No per-check table at a
final head is produced this round (criterion 6, BLOCKED branch). The
local measured pipeline — the identical `tools/supply_chain/run.sh`
backend-of-truth flow the CI `Supply-chain evidence` job executes, with
the pinned scanner images and a freshly updated database — is recorded
above as the authoritative local failure evidence (log lines 1818-1819;
retained `failure-diagnostics/` bundle in `/tmp/0792g-evidence/`).

## Local setup / dependencies

- Docker: the pipeline built all six images twice (`--pull --no-cache`,
  `SLAIF_IMAGE_REVISION=local`), then the `slaif-supply-1086734-*` tags
  were removed by the pipeline's own cleanup on exit; no compose stack
  was started (P3.3 not executed); no repository image tags touched.
- Evidence retained: `/tmp/0792g/` (`cft-154.0.8037.92-linux64.zip`
  [196,202,491 bytes, sha256 `ff43322f...`],
  `last-known-good-versions.json`,
  `known-good-versions-with-downloads.json`,
  `last-known-good-versions-with-downloads.json`, `p11-exact.txt`,
  `pipeline.log`) and `/tmp/0792g-evidence/` (full pipeline evidence:
  `images/*.json`, `manifests/*.files.json`, `sboms/*.spdx.json`,
  `scan-sboms/*.syft.json`, `scans/*.grype.json`, `scanner/`,
  `failure-diagnostics/`). Prior-round evidence retained at
  `/tmp/0792f/`, `/tmp/0792f-diag/`, `/tmp/0792e/`, `/tmp/0792d-*`.
- Tooling: uv 0.12.5 (frozen), docker/buildx, pinned
  `docker.io/anchore/grype:v0.117.0` /
  `docker.io/anchore/syft:v1.51.0` (digest-pinned, as in policy). No new
  packages or services. No production systems, data, or credentials
  touched; no secrets in the diff or this report.

## Documentation

- The 5 docs files + README sites were applied and then reverted with
  the rest of the 14 files (no documentation change landed this round).

## Safety and scope confirmations

- Unrelated files changed: NO — on the remote this round changed exactly:
  T (2 transcript files), SELF (this report). The repository tree is
  otherwise byte-identical to C (worktree clean; `C..SELF` = exactly
  three transcript files).
- Zero net implementation change: CONFIRMED (14 files applied, all
  reverted before any push; no implementation commit exists).
- No product code changed: CONFIRMED. No `tools/supply_chain/*` logic
  changed: CONFIRMED (the five policy.py constants and one evidence.py
  boundary directory were pin-value edits only, and were reverted; no
  comparison, normalization, validator, gate, or contract touched).
- No exception added: CONFIRMED — `supply-chain/vulnerability-exceptions.json`
  remains EMPTY (`{"schema_version": 1, "exceptions": []}`); the
  reproducibility gate was NOT weakened in any way: CONFIRMED.
- No historical entry rewritten: CONFIRMED — matrix candidate-3/4/5/6
  byte-identical (no matrix change applied at all);
  docs/SUPPLY_CHAIN.md line 193 byte-identical (verified by the
  historical-isolation check of the applied edits; no edit targeted it).
- No CI re-run invoked; no merge; no other PR touched; dependabot PRs
  untouched.
- Activated order/`oap/active` edited: NO — committed byte-identical
  (order file sha256
  `caa04aefd6cdab58e3ac10d7680187ecff5e3a2f05891ad2c64febfda3265021`
  verified on the published file; git blob ID
  `91088c71354480147d704829934aa185626828b7` on the committed blob;
  active `079-2-g\n` = hex `3037392d322d670a` verified on the committed
  blob).
- No second fix attempt made under any outcome: CONFIRMED.
- Report commit changes only this report: verified before the response
  signal.

## Cumulative base->head size (2026-09-14 review-unit governance
Section 2)

Base `577509e7bc990d85a10af5954bee3c6f7c888a4f` -> this round's final
non-report head T `741dd932144e72257f3864c70d8e8956d3dfafc2` (exact
measured diff, `git diff --numstat`: 53 files, +7544/-92; this
report's own lines are excluded, as in the prior rounds; at S the file
count is 54):

| Category | Files (at T) | +lines | -lines |
|---|---|---|---|
| Production/config | 17 | 568 | 71 |
| Migrations | 0 | 0 | 0 |
| Tests/evidence | 13 | 1320 | 10 |
| Generated artifacts | 5 | 354 | 4 |
| Docs | 4 | 8 | 6 |
| OAP transcript | 14 (7 orders + active + 6 prior reports) | 5294 | 1 |

This round adds no production/config, migration, test, generated, or
docs lines to the base->head cumulative (the 14 applied files were
reverted; no implementation commit exists): production/config remains
17 files / +568 raw lines, identical to the 079-2-f table. The ~20-file
production/config review trigger is therefore NOT crossed by this
round (nothing implementation-sized landed); the order's predeclared
crossing (17 -> 21 files, CLOSURE_ONLY upon acceptance) applies to the
refresh implementation when it lands in a follow-up round, where the
predeclared Section 10 estimate (approx. 66 files / ~+7400/-92 with the
refresh) remains the governing estimate. Note the measured +7544 at T
already exceeds ~+7400 in raw line count purely from OAP transcript
growth (7 orders + 6 prior reports = +5294 transcript lines); the
estimate was an approximate predeclaration and is superseded by these
exact tables. CLOSURE_ONLY does not begin until a conforming refresh
round is accepted.

## Known limitations / blockers

- BLOCKING (P3.1 gate failure, new external class): the local measured
  pipeline — the CI `Supply-chain evidence` backend of truth — failed
  with `web: unexcepted Critical vulnerabilities: GHSA-vcvr-r3jv-pc5j`
  (log line 1819, 2026-10-04 run; immediately after the grype database
  updated to latest, line 1818). The finding is
  `pkg:npm/next@16.3.3` in the web image (advisory fix `16.3.6`,
  first-observed 2026-09-30; `supply-chain/vulnerability-exceptions.json`
  is empty; policy `fail_severities: [Critical]`,
  `unfixed_critical_still_fails: true`). This is freshly published
  advisory data on an unchanged image/lockfile — the same external
  scan-database drift class as the 24 Chrome CVEs this round targets,
  on a different package. It makes the ordered `candidate-7` matrix
  entry (measured PASS, six images, zero Critical) and therefore the
  compliant 15-file implementation head impossible in this round, and
  the CI `Supply-chain evidence` check would fail at any pushed head
  until it is cleared.
- The browser-worker half of this round's objective IS delivered and
  proven locally (all P3.1 browser-worker EXPECTEDs met; all 24 named
  CVEs absent under the fresh database; double-build reproducibility
  clean for all six images including backend 2821/2821 — the 079-2-f
  pyc-drift fix re-verified). The measured values are recorded above and
  retained in `/tmp/0792g-evidence/` for the follow-up round (they must
  be re-measured there at the follow-up's own head, as the image digest
  and grype database fields are run-bound facts).
- Non-blocking observation: the `test_policy` `previous`-block
  candidate-6 shift (applied then reverted) replaced the `ci_run`
  assertion position with `scan_result["exception_count"] == 0`, because
  candidate-6 carries no `ci_run` field (it predates its remote
  revalidation, per the 078-6-a report); assertion count and structure
  were preserved. Flagged for strategy's review of the follow-up
  order.

## Recommended strategic follow-up

- A new bounded round (or pair of rounds) for the 079/2 review unit:
  (1) clear the new web Critical — a strategy-scoped choice between a
  product dependency bump of `next` from `16.3.3` to `>=16.3.6`
  (lockfile + product-code impact assessment; a product change, hence a
  fresh bounded order) or a time-boxed exception entry per the
  established regime (policy `maximum_exception_days: 90`; precedent
  072-i/j/n) — the executor may not choose between these (order §5/§11);
  (2) re-issue the 079-2-g CfT `154.0.8037.92` refresh (optionally
  folded into (1)): the mechanism is now locally proven end-to-end
  (P1 hash/endpoint verification, 14/15-file pin refresh applied and
  validated — `policy validate` OK, check_repository PASS, ruff clean,
  85+54 tests passing, browser-worker scan zero-Critical with all 24
  named CVEs absent, double-build reproducibility clean), so the
  re-issued round is a mechanical re-application plus a fresh measured
  pipeline and smoke. A green `Supply-chain evidence` at that round's
  head re-confirms, end-to-end, both the browser pin and the 079-2-f
  pyc-drift fix under the current grype database. The reproducibility
  gate is never waived, and a green merge is never obtained by
  re-running until luck.
