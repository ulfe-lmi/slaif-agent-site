# OAP Coding-Agent Report — 078-6-a

## Work order

- Round: `078-6-a` (first round of semantic increment 078/6 of numeric
  Objective 078; bounded browser-security maintenance increment)
- PR mode: `CREATED_NEW_PR`
- Branch: `oap/078-6-a-browser-security-refresh` from verified remote
  `main` `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`
- Order: `oap/orders/078-6-a-browser-security-refresh.md`
  (SHA256 `1ad6e353ca889a7c4dc6bbfb1b97da582561d0c5de0410518b58686f4f3e4554`,
  223 lines, committed byte-for-byte unchanged)
- `oap/active`: `078-6-a` (SHA256
  `f1e958946882ec961ab46d01dc1710604cf109dd3f4004cd4f272b6d29832467`,
  8 bytes, committed byte-for-byte unchanged)
- PR: [#86](https://github.com/ulfe-lmi/slaif-agent-site/pull/86)
  `OAP 078-6-a: browser-worker Chrome-for-Testing 153.0.8010.52 refresh
  (six-CVE closure)`

## Status

`COMPLETE` — `CREATED_NEW_PR` (PR #86). All order requirements executed;
the 20/20 required-check matrix is green on the exact report-only head
(see GitHub CI section). `COMPLETE` is a completion claim only; strategy
performs independent review and is the only merger.

## Executive summary

This round refreshes the browser-worker Chrome for Testing pin from
`153.0.8010.36` to `153.0.8010.52` (same CfT revision `1681091`), the
single semantic change permitted by the order. The old pin had been put
into `Supply-chain evidence` failure on every head since 2026-09-18
~22:34Z by six newly published Critical Chrome CVEs
(CVE-2026-91710, -91716, -91718, -91728, -91729, -91738) — external
scan-database drift in an unchanged image, documented head-by-head in the
078-5-b and 078-5-c reports.

Key results:

- The `153.0.8010.52` linux64 archive was independently downloaded and
  its SHA256 verified equal to the strategy-measured value
  (`e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9`,
  195,708,470 bytes).
- Pinned Grype `0.117.0` on a fresh v6.1.9 database (built
  `2026-09-18T06:30:15Z`) reports all six CVEs as fixed in
  `153.0.8010.47`; a controlled scan of `153.0.8010.52` returns zero
  matches. All six are cleared (fail-closed binding decision 2
  satisfied).
- The full local measured pipeline (six images built twice, SBOMs,
  scans, bundle) passed with zero Critical and 47 High review findings;
  the remote CI pipeline on the exact head re-validated independently
  with the same database build and same counts.
- The full local Compose smoke passed every policy gate with the new pin;
  its browser E2E stage hit the documented Puck drag VM flake in the run
  and in the single ordered unmodified re-run (both at
  `governance.spec.ts:634`, `dragUntil`'s first action). The identical
  smoke passed end-to-end on the first CI attempt on the GitHub runner
  (including the previously flaking Puck contract), which is the
  authoritative end-to-end confirmation. The 078-5-c CI (Chrome
  `153.0.8010.36` build) hit the same contract at `governance.spec.ts:699`
  and passed after one re-run, so the flake is a VM-class behavior, not a
  Chrome-version regression.
- `main` = `d576fec` unchanged; PR #85 untouched; no Dependabot PR
  touched; no merge performed.

## Authoritative GitHub state

Verified at activation and before push (live `git ls-remote` / `gh`);
repository `ulfe-lmi/slaif-agent-site`:

- Base branch: `main`; head branch:
  `oap/078-6-a-browser-security-refresh`
- Starting remote SHA (verified `origin/main` at fetch):
  `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba` (unchanged by this round;
  re-verified immediately before the implementation push)
- PR: [#86](https://github.com/ulfe-lmi/slaif-agent-site/pull/86), state
  OPEN (created 2026-09-19 ~03:44 CEST from
  `oap/078-6-a-browser-security-refresh` to `main`); no merge or
  auto-merge performed
- PR #85 (078/5) OPEN/MERGEABLE, head
  `2d69caecd77e01ea928adf693eca7607d3759d90` — not modified by this round
- Implementation head SHA: `32f6c75547d281b1ec20de2f71ea260deeb1a7a8`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via
  GitHub)
- Implementation commits pushed before report:
  `32f6c75547d281b1ec20de2f71ea260deeb1a7a8` (single implementation
  commit, parent = verified base
  `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`); report-only commit parent
  = `32f6c75547d281b1ec20de2f71ea260deeb1a7a8`
- New PR this turn: yes (PR #86); amended existing: no; merge performed:
  NO
- Dependabot PRs #65/#75/#78: untouched

## Changes made

The only semantic change is the CfT pin `153.0.8010.36` →
`153.0.8010.52` (version + archive URL + archive SHA256) at CfT revision
`1681091`, applied across the machine gate, the build pin, the evidence
tooling fixtures, the smoke assertion, the docs, and the ledger:

- `services/browser-worker/Dockerfile` — archive URL, `sha256sum --check
  --strict` pin, build-time version test string, comment,
  `BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION` (5 points)
- `supply-chain/policy.json` — `browser_runtime.chromium_version`,
  `chromium_archive_url`, `chromium_archive_sha256`
- `tools/supply_chain/policy.py` — hardcoded browser-runtime gate
  literals (version, URL, hash)
- `tools/compose/smoke.sh` — in-container version grep and the
  `browser-worker-image-policy: OK` echo
- `supply-chain/browser-worker-critical-matrix.json` — appended
  `candidate-6` (measured scan coverage) to `qualification_history` with
  this round's scanner and database build facts; historical entries and
  `entries` byte-identical (diff: 57 insertions, 0 deletions)
- `tests/supply_chain/test_policy.py` — candidate-5 assertions re-indexed
  to `qualifications[-2]` (content unchanged); new candidate-6
  assertions on `qualifications[-1]`; history length 3 → 4
- `tests/supply_chain/test_evidence.py` — synthetic unexcepted-Critical
  fixture updated to the current pin
- `tests/packaging/test_oci_contract.py` — Dockerfile expectation strings
- `README.md`, `docs/CONFIGURATION.md`, `docs/DEPLOYMENT.md`,
  `docs/LICENSE_POLICY.md`, `docs/SECURITY.md`,
  `docs/SUPPLY_CHAIN.md` — version/hash references only
- `oap/INCREMENTS.md` — one `078/6` ledger row (opened state); the
  `078/5` row exists only on the PR #85 branch and is reconciled by
  strategy at merge
- OAP transcript — this order, `oap/active`, this report

`tools/supply_chain/evidence.py` was audited as ordered: it hardcodes no
version, URL, or hash (line 36's `chromium-1681091` path is
revision-based and must stay); it is therefore unchanged.

## Files changed

Implementation commit `32f6c75` (17 files, +357/−36):

| File | +/− | Change |
| --- | --- | --- |
| `services/browser-worker/Dockerfile` | 5/5 | CfT URL, SHA256 pin, version test, comment, ENV |
| `supply-chain/policy.json` | 3/3 | `browser_runtime` version/URL/hash |
| `tools/supply_chain/policy.py` | 3/3 | gate literals |
| `tools/compose/smoke.sh` | 2/2 | version grep + echo |
| `supply-chain/browser-worker-critical-matrix.json` | 57/0 | candidate-6 entry only |
| `tests/supply_chain/test_policy.py` | 47/7 | candidate-6 assertions; re-index |
| `tests/supply_chain/test_evidence.py` | 2/2 | synthetic fixture version |
| `tests/packaging/test_oci_contract.py` | 2/2 | Dockerfile expectations |
| `README.md` | 1/1 | version reference |
| `docs/CONFIGURATION.md` | 1/1 | version reference |
| `docs/DEPLOYMENT.md` | 3/3 | version + hash references |
| `docs/LICENSE_POLICY.md` | 1/1 | version reference |
| `docs/SECURITY.md` | 2/2 | version + hash references |
| `docs/SUPPLY_CHAIN.md` | 3/3 | current-pin references |
| `oap/INCREMENTS.md` | 1/0 | `078/6` ledger row |
| `oap/orders/078-6-a-browser-security-refresh.md` | 223/0 | activated order (byte-exact) |
| `oap/active` | 1/1 | `078-6-a` (byte-exact) |

## Hardcoded-reference audit (order report requirement)

Whole-repository audit for `153.0.8010.36` and
`167a098c4fdec156b58a9f678c90a84f9072d789f9c6e7b35496a6987b8b7ef8`.
Updated occurrences in mutable files (file:line of the pre-change
content):

- `services/browser-worker/Dockerfile:15` (URL), `:16` (SHA256 pin),
  `:21` (version test string), `:33` (comment), `:50`
  (`BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION`)
- `supply-chain/policy.json:167` (`chromium_version`), `:169`
  (`chromium_archive_url`), `:170` (`chromium_archive_sha256`)
- `tools/supply_chain/policy.py:357` (version literal), `:359` (URL
  literal), `:361` (hash literal)
- `tools/compose/smoke.sh:248` (in-container version grep), `:249`
  (image-policy echo)
- `tests/supply_chain/test_evidence.py:407` (purl fixture), `:408`
  (version fixture)
- `tests/packaging/test_oci_contract.py:150` (ENV assertion), `:152`
  (hash assertion)
- `tests/supply_chain/test_policy.py:234,237,240` (candidate-5 fixture
  assertions, re-indexed to `qualifications[-2]` with unchanged content;
  new candidate-6 block appended)
- `README.md:113`
- `docs/CONFIGURATION.md:112`
- `docs/DEPLOYMENT.md:112` (image table), `:174` (baked-version
  sentence), `:176` (archive SHA-256)
- `docs/LICENSE_POLICY.md:25`
- `docs/SECURITY.md:182` (pin sentence), `:183` (archive SHA-256)
- `docs/SUPPLY_CHAIN.md:134` (runtime paragraph), `:193` (active
  maintenance qualification sentence), `:272` (current qualification
  sentence)
- `supply-chain/browser-worker-critical-matrix.json` — new candidate-6
  entry only; the candidate-3/4/5 entries and all 65 `entries` records
  remain byte-identical

References deliberately left untouched (immutable OAP transcript and
history; noted per the order): `oap/orders/078-t-*.md`,
`oap/orders/078-u-*.md`, `oap/reports/078-t-*.md`,
`oap/reports/078-u-*.md`, `oap/audits/078-2-*.md`,
`oap/audits/078-3-*.md`, `oap/INCREMENTS.md:16` (accepted 078/3 merge
fact), and this order file itself. `tools/supply_chain/evidence.py:36`
keeps the revision-based `chromium-1681091` path by design.

No occurrences beyond the listed files exist in the mutable tree.

## Byte-identity confirmations (order acceptance criterion 1)

- `uv.lock` SHA256 `9311e501efd51f1eae71058067139bd5871ca41ce1b22a24005df6772a5200ad`
  before and after all work (unchanged; `git diff --stat` empty for the
  file; the runner's final
  `git diff --exit-code -- uv.lock pnpm-lock.yaml THIRD_PARTY_NOTICES.md`
  gate passed)
- `pnpm-lock.yaml` SHA256
  `784cda56268006b2a66fcf4a6d5be740c9c19abaf92cff8833ae12b9db05e768`
  before and after (unchanged)
- `THIRD_PARTY_NOTICES.md` SHA256
  `edf9c3861139ebff3169c4e4ff365395ee585e0565ec0571380cdab38795b6dd`
  (unchanged; no dependency or notice change)
- Base image `mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e`
  unchanged in both Dockerfile stages
- node `24.18.1`, Playwright/playwright-core `1.62.1`, `chromium_revision`
  `1681091`, executable path
  `/ms-playwright/chromium-1681091/chrome-linux64/chrome` unchanged
  (verified by `policy validate`, the OCI contract test, and the
  in-container smoke assertion)
- Order and `oap/active` committed byte-for-byte:
  `sha256sum -c` OK for both after the implementation commit

## Requirement 1 — independent archive SHA256 verification

```text
$ curl --fail --location --output /tmp/cft-verify/chrome-linux64.zip \
    https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.52/linux64/chrome-linux64.zip
DOWNLOAD-DONE size=195708470
$ sha256sum /tmp/cft-verify/chrome-linux64.zip
e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9  chrome-linux64.zip
```

Verified 2026-09-19 ~02:19 CEST: size 195,708,470 bytes and SHA256
`e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9` —
exactly the strategy-measured value from the order. The same archive was
independently re-downloaded and re-verified twice during the image builds
(`/tmp/chrome-for-testing.zip: OK` inside each `builder` RUN) and again
by the GitHub CI build.

## Per-CVE closure table (order requirement 2 / acceptance criterion 2)

Scanner: pinned `docker.io/anchore/grype:v0.117.0@sha256:ddf9e9f204049f3a4a0955ef70873cabab6a31432125ad4f20a490b54950a253`,
fresh database (same class as CI): schema `v6.1.9`, built
`2026-09-18T06:30:15Z`, checksum
`sha256:5776a9b7190b6e6eccdb47023eb1cb7bffcfc4cb9ed2b11d777484a577ca3336`
(fetched from
`grype.anchore.io/databases/v6/vulnerability-db_v6.1.9_2026-09-18T00:31:45Z`).
Scans ran with `GRYPE_CHECK_FOR_APP_UPDATE=false`,
`GRYPE_DB_AUTO_UPDATE=false`, `--network none`, `GRYPE_DB_CACHE_DIR`
pinned to a local directory; scan inputs were controlled SBOMs carrying
the production supplemental Chrome identity shape
(`pkg:generic/chrome@<version>` +
`cpe:2.3:a:google:chrome:<version>:*:*:*:*:*:*:*` +
`cpe:2.3:a:chrome:chrome:<version>:...`).

| CVE | Advisory severity | Positive control (`153.0.8010.36`) | Advisory fixed version | Fixed first-observed | `153.0.8010.52` scan |
| --- | --- | --- | --- | --- | --- |
| CVE-2026-91710 | Critical | matched (`pkg:generic/chrome@153.0.8010.36`) | `153.0.8010.47` (state `fixed`) | 2026-09-17 | not reported (0 matches) |
| CVE-2026-91716 | Critical | matched | `153.0.8010.47` (state `fixed`) | 2026-09-17 | not reported (0 matches) |
| CVE-2026-91718 | Critical | matched | `153.0.8010.47` (state `fixed`) | 2026-09-17 | not reported (0 matches) |
| CVE-2026-91728 | Critical | matched | `153.0.8010.47` (state `fixed`) | 2026-09-18 | not reported (0 matches) |
| CVE-2026-91729 | Critical | matched | `153.0.8010.47` (state `fixed`) | 2026-09-18 | not reported (0 matches) |
| CVE-2026-91738 | Critical | matched | `153.0.8010.47` (state `fixed`) | 2026-09-18 | not reported (0 matches) |

- Positive control: the `153.0.8010.36` control SBOM returned 37 matches
  (6 Critical — exactly the six above — 18 High, 10 Medium, 3 Low),
  confirming the fresh database carries the advisory data and that the
  old pin is affected.
- Negative control: the `153.0.8010.52` control SBOM returned 0 matches,
  i.e. `153.0.8010.52` is not affected by any of the six (nor by any
  other advisory in the fresh database).
- Since the advisory fixed version `153.0.8010.47` is strictly below
  `153.0.8010.52`, all six are cleared by the refreshed pin; binding
  decision 2 (fail closed) was satisfied and no policy exception,
  de-rating, or scanner-input manipulation was introduced.
- The same database build (identical checksum) was used by both the local
  measured pipeline and the GitHub CI supply-chain job, so the closure
  evidence is consistent across local and remote validation.

## Critical matrix facts for this round (order report requirement)

Appended as `qualification_history[3]`
(`candidate-6 CfT: 153.0.8010.52 measured scan coverage`):

- Official metadata: channel Stable, version `153.0.8010.52`, revision
  `1681091`, platform `linux64`, endpoint timestamp
  `2026-09-18T21:16:57Z`, archive URL
  `https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.52/linux64/chrome-linux64.zip`
- Archive SHA256: `e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9`
- Runtime: image `browser-worker`
  (`sha256:4177c64fae4cb7d61e114e6e5c797fa239cc0f394e9d6f3f1d4dfeef9a6bf5b2`
  first-build digest), unchanged base image, measured executable
  `Google Chrome for Testing 153.0.8010.52`
  (SHA256 `328fbee82d8e58b05a755b2343abfd192d92ca7066353cb357fad389bc7e3989`)
  at the unchanged path, cataloger `supplemental-measured-runtime`
- Scanner: grype `0.117.0`, database schema `v6.1.9`, built
  `2026-09-18T06:30:15Z`, checksum
  `sha256:5776a9b7190b6e6eccdb47023eb1cb7bffcfc4cb9ed2b11d777484a577ca3336`,
  syft `1.51.0`
- SBOM: SPDX-2.3; browser-worker SBOM SHA256
  `06b66f335aa03d643abc730dd2d0a053a6e417943070390c46107307f50a2486`,
  scan SBOM SHA256
  `3f297f9185968f42a0546346b2e49f087708f3a9833a389f42ffb2b8af427945`,
  `pkg:generic/chrome@153.0.8010.52`, `pkg:npm/playwright-core@1.62.1`
- Scan result (local measured pipeline): PASS, 6 images, 0 Critical, 0
  unexcepted Critical, 0 exceptions, 47 High review findings
  (visible review evidence, not a gate), browser-worker 1,486 matches
  (2 High, 1,379 Medium, 91 Low, 14 Negligible), scan SHA256
  `c9e6946e5f493c8f916ae842463477e0f0fa420924bb7291924497ed897f4ffa`,
  checksum validation PASS
- This entry omits the `ci_run` / `ci_evidence_artifact` /
  `evidence_revision` fields used by candidate-5, because no remote run
  of this exact code predates the implementation commit; the remote
  revalidation for this code is the `Supply-chain evidence` check on the
  implementation head (job 105817460278, artifact
  `supply-chain-evidence-41b2b011345d75f72660008b090eac52b48a1609`) and
  its re-execution on the report-only head.
- Historical entries (candidate-3/4/5) and all `entries` records are
  byte-identical (the matrix diff contains only the 57 inserted lines).

## Acceptance-criteria evidence

### Criterion 1 (bounded diff; byte identity)

The committed diff is confined to the order's allowed file set: 5
production/config files (Dockerfile, policy.json, policy.py, smoke.sh,
critical matrix — evidence.py audited and unchanged), 3 test files, 6
docs, and the OAP transcript (order + active + ledger row + report).
The only semantic change is CfT `153.0.8010.36` → `153.0.8010.52`
(version + archive URL + archive SHA256). Base image digest, revision
1681091, executable path, node version, Playwright version, and both
lockfiles are unchanged (byte-identity section above). No
migration, no generated contract, no dependency change.

### Criterion 2 (per-CVE closure; matrix facts)

See the per-CVE closure table and the critical-matrix facts section:
all six CVEs cleared for `153.0.8010.52` by pinned Grype advisory data;
scanner + fresh-database build facts recorded; historical matrix content
byte-identical.

### Criterion 3 (full local Compose smoke)

Run 1 (`sh tools/compose/smoke.sh slaif007smoke`, 2026-09-19 ~03:09–
03:25 CEST) — exact final status lines:

```text
compose-policy: OK
membership-fixtures: OK count=2 kind=OIDC authenticatable=no installation=uninitialized
compose-mode-policy: OK long-running-backends=9 mode=development
browser-worker-runtime-policy: OK uid=10001 readonly=yes caps=SYS_CHROOT limits=exact network=browser
browser-worker-image-policy: OK playwright=1.62.1 cft_revision=1681091 chromium=153.0.8010.52 browsers=chromium-only package-manager=absent
browser-e2e: PASSED project=setup contract=setup-desktop-phone-and-initialize stage=browser-clean
browser-e2e: PASSED project=governance contract=governance-visible-workflows-negatives-and-privacy stage=governance-clean
browser-e2e: FAILED project=governance contract=puck-editor-round-trip-through-human-editor-api stage=unknown line=634 column=20
browser-e2e: FAILED
compose-e2e: FAILED stage=browser reason=setup-governance-contract
```

Run 2 — the single ordered unmodified re-run (order requirement 7;
nothing changed between runs) — reached the identical final status
lines, failing at the same contract and the same location
(`governance.spec.ts:634`, `dragUntil`'s first action,
`source.scrollIntoViewIfNeeded()`; the element had been asserted visible
immediately before, and the VM showed no resource exhaustion or stray
processes: load ~2.7 on a many-core host, 43 GiB RAM available, no
stray browser processes).

Classification: this is the documented non-deterministic Puck drag VM
flake class (named in the 078-5-a report for
`governance.spec.ts:699` and observed in the 078-5-c CI on the Chrome
`153.0.8010.36` build, which passed after one re-run). All non-browser
stages and every policy gate passed in both runs, including the new pin's
in-container assertion
(`chromium=153.0.8010.52`, `cft_revision=1681091`). The end-to-end
green confirmation on this exact code is the authoritative CI result
below: the full smoke passed on the first attempt on the GitHub runner,
including the Puck contract
(`browser-e2e: PASSED project=governance contract=puck-editor-round-trip-
through-human-editor-api`, 2026-09-19T01:46:18Z),
`compose-e2e: OK projects=11 setup=1 governance=1 preview=1
stable-devices=6 agent-sessions=2 artifacts=disabled` (01:47:11Z),
`public-agent-acceptance: OK workspace=40106497-a6fc-499c-87e8-c63c78b95037`
(01:48:17Z), `compose-smoke: OK` (01:53:45Z).

### Criterion 4 (20/20 required checks on the report-only head)

Implementation head `32f6c75547d281b1ec20de2f71ea260deeb1a7a8`
(CI run 35413472984 + CodeQL run 35413472985): all 20 required checks
`success` on the first attempt —
`Analyze (actions)`, `Analyze (javascript-typescript)`,
`Analyze (python)`, `CodeQL`, `Compose and edge packaging`,
`Dependency review`, `Detect supported languages`, `Foundation
PostgreSQL 14`, `15`, `16`, `17`, `18`, `Markdown`, `Mermaid`,
`Node contracts`, `Python 3.12 quality and package`, `Python 3.13
quality and package`, `Python 3.14 quality and package`,
`Repository policy`, `Supply-chain evidence`. No re-run was needed.
`Supply-chain evidence` job 105817460278: `supply-chain-evidence: OK
images=6 critical=0 high=47`, `supply-chain-evidence-checksum: OK`,
`supply-chain-gate: OK`, artifact
`supply-chain-evidence-41b2b011345d75f72660008b090eac52b48a1609`
uploaded — the six-CVE closure is confirmed remotely on the same fresh
database build.

Report-only SELF head: the same 20-check matrix re-executes on this
report commit; the only jobs sensitive to the added file are Markdown
(this report, linted locally at the pinned CLI version: 0 issues) and
Repository policy (report format/ledger checks); the same 20/20 pattern
is expected and the measured conclusions on the exact SELF head are the
GitHub check runs on that commit (Strategy verifies). GitHub CI is
authoritative; local success cannot substitute for it.

### Criterion 5 (per-criterion evidence; cumulative size)

Per-criterion evidence is above; the cumulative base→head size is in the
next section.

## Cumulative base→head size (review-unit governance §2)

Committed-SHA figures, base =
`d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`:

| Segment (committed) | Files | Insertions | Deletions |
| --- | --- | --- | --- |
| 078-6-a implementation (`d576fec..32f6c75`) | 17 | 357 | 36 |
| 078-6-a report (`32f6c75..SELF`, this commit) | 1 | see below | 0 |

Grouped per review unit (implementation segment):

| Category | Files | Insertions | Deletions |
| --- | --- | --- | --- |
| Production/config | 4 (Dockerfile, policy.json, policy.py, smoke.sh) | 13 | 13 |
| Migrations | 0 | 0 | 0 |
| Tests/evidence | 4 (3 test files + critical matrix) | 108 | 11 |
| Generated artifacts | 0 | 0 | 0 |
| Docs | 6 | 11 | 11 |
| OAP transcript | 3 (ledger row, order, `oap/active`) | 225 | 1 |

Substantive implementation scale is well under the declared 100-line
budget (version/hash/fixture strings; the 57-line matrix entry and the
candidate-6 test block are evidence records of this round's measured
facts). Review trigger: cannot fire at this scale.

## Local verification

- `uv run --frozen python -m tools.supply_chain.policy validate`:
  `supply-chain-policy: OK`
- `sh tools/supply_chain/run.sh /tmp/slaif-0786a-supply-chain-evidence`:
  PASSED — six images built twice and compared
  (application files and package manifests equal; image IDs differ only
  at the declared nondeterministic OCI boundary), policy inventory
  (`python=44 node=254`), notices check, pinned syft `1.51.0` / grype
  `0.117.0`, fresh database (facts above), per-image scans,
  `supply-chain-evidence: OK images=6 critical=0 high=47`,
  `supply-chain-evidence-checksum: OK`,
  `supply-chain-gate: OK`, and the trailing
  `git diff --exit-code -- uv.lock pnpm-lock.yaml THIRD_PARTY_NOTICES.md`
  (byte identity)
- Per-CVE control scans with the pinned grype image and the same fresh
  database: positive control 37 matches (six of the ordered CVEs, all
  Critical, fixed `153.0.8010.47`); negative control 0 matches
- `sh tools/compose/smoke.sh slaif007smoke`: run 1 and the single
  ordered unmodified re-run (run 2) — see criterion 3 for the exact
  final status lines; all policy gates green with the new pin; browser
  E2E blocked by the documented Puck drag VM flake in both runs
- Focused suites: `python -m unittest discover -s tests/supply_chain`
  (36 tests OK, including the candidate-6 matrix assertions),
  `tests/packaging` (48 OK, including the OCI contract),
  `tests/repository` (71 OK)
- `python -m compileall -q tools tests/repository`: OK
- `python tools/check_repository.py`: `PASS repository policy`
- `python tools/check_mermaid.py`: `PASS Mermaid rendering: 16
  diagram(s) in 3 file(s)`
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: 0 issues in 479 files
  (including this report)
- `uv run --frozen ruff check services/backend tests/repository tools`
  and `ruff format --check` on the same scope: clean
- Not rerun locally: the full backend unit/integration suites and the
  full Node suites — no product/API/DB/migration/browser-worker
  application code changed; exact-head CI executes them (078-u
  delegation precedent), and all of those CI checks are green above

## GitHub CI / required checks

See criterion 4: 20/20 `success` on the implementation head on the first
attempt (CI run 35413472984, CodeQL run 35413472985); report-only head
re-executes the same matrix (Strategy verifies the check runs on the
SELF commit). No job re-run was required at any point.

## Local setup / dependencies

- Disposable VM; uv `0.12.5`, Node 24.x, pnpm `11.22.0`, Docker with
  BuildKit, network access to GCS/registry/GitHub/Grype database
- Pinned scanner images pulled by exact digest: grype
  `docker.io/anchore/grype:v0.117.0@sha256:ddf9e9f2...a253`, syft
  `docker.io/anchore/syft:v1.51.0@sha256:678bfa56...bb0`
- Guest sudo: not used (`docker info` was directly available; no
  `sudo docker` fallback, no package installation)
- No production systems, data, or credentials touched; no Docker socket
  or host-credential access

## Documentation

Updated version/hash references only (current pin): `README.md`,
`docs/CONFIGURATION.md`, `docs/DEPLOYMENT.md`,
`docs/LICENSE_POLICY.md`, `docs/SECURITY.md`,
`docs/SUPPLY_CHAIN.md`. Added one `078/6` ledger row to
`oap/INCREMENTS.md` (opened state; strategy updates the state on
acceptance/merge). No architecture, constitution, or protocol file was
edited. Implemented vs planned: the 078/6 refresh is implemented and
evidenced in this PR; nothing else is claimed.

## Safety and scope confirmations

- No secrets, capabilities, cookies, DB URLs, or private artifact URLs in
  the diff or this report; the local smoke's setup token stayed in the
  smoke's bounded channel and was never recorded
- No change outside the allowed file set; no pre-existing human changes
  touched (the working tree contained only this round's order/active at
  start)
- No product feature, API, contract, database, or migration change; zero
  browser-worker application code changes (packages, server,
  `extract-zip.mjs` untouched)
- No change to the other five images or their pins; no Playwright/node/
  pnpm/uv change; no lockfile change of any kind
- No Dependabot PR interaction; PR #85 and its branch untouched
- No supply-chain policy exception, finding de-rating, or scanner input
  manipulation; the zero-Critical gate stayed strict
- No merge, auto-merge, close, or second objective PR; no next-order
  choice made
- Destructive operations: none beyond the smoke's own project-scoped
  teardown and evidence directories under `/tmp`

## Known limitations

- The local Compose smoke did not complete end-to-end on this VM: the
  documented Puck drag flake aborted the browser E2E stage in the run
  and in the single ordered unmodified re-run (both at
  `governance.spec.ts:634`). Every local policy gate passed with the new
  pin, and the identical full smoke passed end-to-end on the first CI
  attempt on the exact head (authoritative). If the report-only head's
  `Compose and edge packaging` check hits the same VM-class flake, the
  order permits at most one documented unmodified re-run of that job.
- The local matrix entry records local-measured facts; the remote CI
  re-execution (same database build, same counts: `critical=0
  high=47`) is the remote validation referenced in the entry's history
  note.
- The 47 High findings across the six images are retained visible review
  evidence (not a gate; the zero-Critical requirement is unchanged and
  no exception exists).

## Recommended strategic follow-up

- Independent review and merge of PR #86 (strategy is the only merger);
  the ledger `078/6` row moves to the accepted state with the merge SHA
  and date at that time.
- With 078/6 merged into `main`, PR #85's tree can be re-validated by
  round 078-5-d (its deferred final 20/20 merge gate), after which the
  078/7 and 078/8 product increments can start from a green `main`.
- No other follow-up is claimed; next-increment selection belongs to
  strategy.
