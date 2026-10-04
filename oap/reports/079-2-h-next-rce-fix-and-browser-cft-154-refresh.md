# OAP Coding-Agent Report — 079-2-h

## Work order

- Identifier: 079-2-h (increment-qualified round ID: eighth round of
  semantic increment 2 of numeric Objective 079, increment 079/2)
- Work-order file:
  `oap/orders/079-2-h-next-rce-fix-and-browser-cft-154-refresh.md`
- Work-order sha256 (file-hash domain, computed over the published file):
  `b9c3f63d6d87fd52c0d429e410fb61a753c98df4d9b1bfca3e4d7801161b3605`
- `oap/active` bytes: `079-2-h\n` (hex `3037392d322d680a`)
- Numeric objective: 079 (increment 079/2; this round = the CLOSING
  qualification-repair round of the 079/2 review unit)
- PR mode: AMENDED_EXISTING_PR (PR #93)

## Status

COMPLETE

## Executive summary

Both closed repair sets of this order were executed and verified end to
end: (A) the web `next` bump `16.3.3` -> `16.3.8` closing the newly
published `GHSA-vcvr-r3jv-pc5j` RCE in `next/og ImageResponse`
(vulnerable `>= 16.2.0, < 16.3.6`, first patched `16.3.6`), and (B) the
browser-worker Chrome-for-Testing refresh `153.0.8010.52`/revision
`1681091` -> `154.0.8037.92`/revision `1689415` clearing the 24 Critical
CVE-2026-952xx/CVE-2026-1023xx findings. The exact 21-file union diff
(7 set-A files + 15 set-B files, `docs/DEPLOYMENT.md` shared) landed in
implementation head I with the matrix `candidate-7` append a pure
insertion (candidates 1-6 byte-identical) and both measured-value sites
filled from this round's own pipeline run. The formal local measured
pipeline at the committed tree passed rc=0: six images built twice with
reproducibility OK, `supply-chain-evidence: OK images=6 critical=0
high=53`, `vulnerability_gate: PASS (zero unexcepted Critical)`,
`GHSA-vcvr-r3jv-pc5j` absent from the web scan, and all 24 named CVEs
absent from the browser-worker scan. The full Compose smoke (13
projects) passed rc=0 on freshly built images, including the new
`browser-worker-image-policy: OK playwright=1.62.1 cft_revision=1689415
chromium=154.0.8037.92 browsers=chromium-only package-manager=absent`
line. No exception entry was added, no gate weakened, and no product
code, route, OpenAPI, or renderer behavior changed. All 20 required
checks reached SUCCESS on the exact report-only head S.

## Authoritative GitHub state

Verified at activation, before each push, and before the response
signal (live `git ls-remote` / `gh`); repository `ulfe-lmi/slaif-agent-site`:

- Base branch: `main`; head branch: `oap/079-2-a-gallery-logogrid`
- Base `main`: `577509e7bc990d85a10af5954bee3c6f7c888a4f` (079/1 merge;
  unchanged; re-verified immediately before the implementation push)
- Round-start remote SHA C: `3fba0bf97bd454e1ffc06a0dfd7a1f9dc527bd5f`
  (the 079-2-g report-only commit S_g; parent T_g
  `741dd932144e72257f3864c70d8e8956d3dfafc2`; grandparent I_f
  `0f5186e863f4c13e4119309109d2420c3b803b60`)
- CI at C (run 37162346409) was superseded per order Section 2: it was
  neither waited on nor re-run
- Transcript commit T (order + `active` bytes only, 2 files):
  `130b7e69cdd44af41348d911a7fa9faa8b0cee66` (order blob
  `f82ee1c3f1d4f7fd2aebf967ad06c38d4527ba52` committed byte-for-byte)
- Implementation head I: `348004ddd2ffa86a9d7aa3a101f11843b417ebac`
  (parent T; 21 files; pushed before this report)
- Report publication commit: SELF (this commit; first parent =
  `348004ddd2ffa86a9d7aa3a101f11843b417ebac`)
- Remote PR head after report publication: SELF (verified via
  `git ls-remote` / `gh pr view` before the response signal)
- PR: [#93](https://github.com/ulfe-lmi/slaif-agent-site/pull/93),
  state OPEN (mergeable `MERGEABLE`, `mergeStateStatus` `BLOCKED` =
  required status checks pending only); base `main`
- New PR this turn: no; merge performed: NO; auto-merge: not
  configured or requested; no other PR touched (dependabot PRs
  untouched)

## Changes made

Exactly the two closed repair sets of the order, nothing else:

**Set A — web `next` 16.3.3 -> 16.3.8 (closes GHSA-vcvr-r3jv-pc5j):**

1. `apps/web/package.json` line 16: `"next": "16.3.8"`
2. `pnpm-lock.yaml`: `pnpm install` with pnpm `11.22.0` at the repo
   root; bounded diff of 41 changed lines (31 version lines
   `16.3.3` -> `16.3.8` for `next` + `@next/env` + 8 `@next/swc-*`
   platform binaries, plus 10 next-family integrity pairs); no other
   dependency version, integrity, or setting/override line changed;
   `lockfileVersion: '9.0'` and the settings/overrides/
   ignoredOptionalDependencies blocks byte-identical; post-edit
   `git grep -c '16\.3\.3' -- pnpm-lock.yaml` = 0;
   `pnpm install --frozen-lockfile` rc=0 (312 entries)
3. `docs/DEPLOYMENT.md` line 161: `next@16.3.8` + the closed sha512
   `sha512-U7QEZaTini6wKrb8A8hqLLqYQyCetegKjCpJOyxk642vWoMoU1x5PyZCJFvgYgiptA8xc5j/9xYlZFO7w9Sjmw==`
4. `THIRD_PARTY_NOTICES.md` lines 39, 40, 182: `16.3.3` -> `16.3.8`
   (`@next/env`, `@next/swc-linux-x64-gnu`, `next`)
5. `sbom.json`: regenerated via
   `uv run --frozen python tools/generate_sbom.py` (68 components;
   "License check: PASS"); resulting diff exactly two lines (the
   `next` version and purl `pkg:npm/next@16.3.8`)
6. `tests/repository/test_repository_policy.py` line 115:
   `"next": "16.3.8"`
7. `tools/check_repository.py` line 1377: `"next": "16.3.8"`

**Set B — browser-worker CfT 154.0.8037.92 refresh (clears the 24
Critical CVEs): the 14 static sites re-applied from the 079-2-g
immutable site-level records plus the approved test_policy
previous-block shift:**

1. `services/browser-worker/Dockerfile` (7 lines): line 15 archive URL
   -> `.../154.0.8037.92/linux64/chrome-linux64.zip`; line 16 archive
   sha256 -> `ff43322f335e436b2f4dcdfeeec5db032299e335a7e8c1c618b326e100ce8732`;
   line 21 version assertion -> `Google Chrome for Testing 154.0.8037.92`
   plus trailing space (as the build-time assertion string); line 33
   comment; lines 49/61 `chromium-1689415` executable path; line 50
   `BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION`
2. `supply-chain/policy.json` (5 lines): `browser_runtime` version /
   revision / archive URL / sha256 / executable path (lines 166-170)
3. `tools/supply_chain/policy.py` (5 lines): hardcoded gate literals
   (lines 356-365)
4. `tools/supply_chain/evidence.py` (1 line): line 36 boundary path
   `ms-playwright/chromium-1689415/` (revision-based; no version,
   URL, or hash hardcoded there)
5. `tools/compose/smoke.sh` (4 lines + 1 same-line value): line 254
   path x2 + version regex `154[.]0[.]8037[.]92`; line 255
   `cft_revision=1689415 chromium=154.0.8037.92` in the
   `browser-worker-image-policy: OK` echo
6. `tests/packaging/test_oci_contract.py` (2 lines: 152, 154)
7. `tests/supply_chain/test_evidence.py` (2 lines: 407, 408)
8. `tests/supply_chain/test_policy.py` previous-block shift (6 value
   lines): candidate-5 -> candidate-6 label
   `candidate-6 CfT: 153.0.8010.52 measured scan coverage`, revision
   `1681091`, version `153.0.8010.52`, archive sha256
   `e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9`,
   executable `/ms-playwright/chromium-1681091/chrome-linux64/chrome`,
   image digest `sha256:4177c64fae4cb7d61e114e6e5c797fa239cc0f394e9d6f3f1d4dfeef9a6bf5b2`,
   `browser_worker_matches == 1486`, `result == "PASS"`,
   `unexcepted_critical == 0`; the approved structural delta: the
   `ci_run` assertion POSITION replaced by
   `scan_result["exception_count"] == 0` (candidate-6 carries no
   `ci_run` field); block assertion count (10) and structure
   preserved; candidate-4 history line 227 and the `current` block
   untouched in R3
9. `README.md` (2 lines: 116-117): qualification statement ->
   `154.0.8037.92` / revision `1689415` (the "replacing the vulnerable
   `152.0.7977.82` payload" provenance clause preserved)
10. `docs/CONFIGURATION.md` (2 lines: 111-112): env-var table rows ->
    new executable path / expected version
11. `docs/DEPLOYMENT.md` (3 lines: 112 + 174-176): table row +
    archive lines (plus set A line 161)
12. `docs/LICENSE_POLICY.md` (1 line: 25)
13. `docs/SECURITY.md` (3 lines: 182-183 + qualification statement)
14. `docs/SUPPLY_CHAIN.md` (3 lines: 134, 140, 272); line 193
    (immutable historical 078-6-a record) byte-identical

**Measured sites (P3.2, filled from THIS round's own pipeline run —
the 079-2-g measured values were used for context only, per order
Section 2, and are run-bound facts re-measured here):**

15. `supply-chain/browser-worker-critical-matrix.json` (57 lines
    added, 0 removed): PURE APPEND of `candidate-7 CfT:
    154.0.8037.92 measured scan coverage` as the LAST
    `qualification_history` entry with the candidate-6 field
    structure (per 079-2-g order P2.9, `history_note` attributed to
    this order 079-2-h acceptance criterion 6 and this round's run
    date); candidates 1-6 byte-identical; `qualification_date`
    `2026-10-04`
16. `tests/supply_chain/test_policy.py` `current` block (14 value
    lines within the 16-assertion block): this round's measured
    candidate-7 values; plus the history length assertion `4` -> `5`,
    atomic with the append (precedent 078-6-a: `3` -> `4` in the same
    commit as the candidate-6 append)

No product-code, route, OpenAPI, or renderer behavior change. No
exception entry. No Playwright, Node, base-image, or pnpm-setting
change. No `tools/supply_chain/*` logic change (pin-value constants
only). No migration, schema, workflow, or secret change.

## Files changed

Exact measured `git diff --name-only` (report lines excluded; this
report's own lines excluded, as in the prior rounds):

- `C..T` = **2 files**:
  `oap/orders/079-2-h-next-rce-fix-and-browser-cft-154-refresh.md`,
  `oap/active`
- `T..I` = **21 files** (the order criterion-1 union, exact):
  `apps/web/package.json`, `pnpm-lock.yaml`, `docs/DEPLOYMENT.md`,
  `THIRD_PARTY_NOTICES.md`, `sbom.json`,
  `tests/repository/test_repository_policy.py`, `tools/check_repository.py`,
  `services/browser-worker/Dockerfile`, `supply-chain/policy.json`,
  `tools/supply_chain/policy.py`, `tools/supply_chain/evidence.py`,
  `tools/compose/smoke.sh`, `tests/packaging/test_oci_contract.py`,
  `tests/supply_chain/test_evidence.py`, `tests/supply_chain/test_policy.py`,
  `supply-chain/browser-worker-critical-matrix.json`, `README.md`,
  `docs/CONFIGURATION.md`, `docs/LICENSE_POLICY.md`, `docs/SECURITY.md`,
  `docs/SUPPLY_CHAIN.md`
- `C..S` = **24 files** (the 23 of `C..I` plus this report)

`T..I` numstat (21 files, +127/-127): README.md 2/2,
THIRD_PARTY_NOTICES.md 3/3, apps/web/package.json 1/1,
docs/CONFIGURATION.md 2/2, docs/DEPLOYMENT.md 5/5,
docs/LICENSE_POLICY.md 1/1, docs/SECURITY.md 2/2,
docs/SUPPLY_CHAIN.md 3/3, pnpm-lock.yaml 41/41, sbom.json 2/2,
services/browser-worker/Dockerfile 7/7,
supply-chain/browser-worker-critical-matrix.json 57/0,
supply-chain/policy.json 5/5, tests/packaging/test_oci_contract.py 2/2,
tests/repository/test_repository_policy.py 1/1,
tests/supply_chain/test_evidence.py 2/2,
tests/supply_chain/test_policy.py 20/20, tools/check_repository.py 1/1,
tools/compose/smoke.sh 2/2, tools/supply_chain/evidence.py 1/1,
tools/supply_chain/policy.py 5/5.

## Acceptance-criteria evidence

### Criterion 1 (T..I = exactly the 21 union files; matrix pure
insertion; Gate A + Gate B outputs hold)

MET. `git diff --name-only T..I` lists exactly the 21 files of the
criterion (listed under Files changed; nothing else). Matrix diff
T..I: 57 added lines, 0 removed lines (pure insertion; JSON parses;
candidates 1-6 byte-identical) — Gate B(f) output recorded under R3.
Gate A outputs: `git grep -n '16\.3\.3' -- . ':!oap'` = 0 lines;
`git grep -n 'pkg:npm/next@16\.3\.8' -- . ':!oap'` = exactly one line
(`sbom.json:250`); `git grep -c '16\.3\.8' -- . ':!oap'` = exactly the
7 set-A files (THIRD_PARTY_NOTICES.md:3, apps/web/package.json:1,
docs/DEPLOYMENT.md:1, pnpm-lock.yaml:31, sbom.json:2,
tests/repository/test_repository_policy.py:1,
tools/check_repository.py:1). Gate B outputs recorded under R3, with
two order-parenthetical count discrepancies RECORDED WITH EXACT STATE
(Gate B(a) 1689415 file count 12 vs stated 15; Gate B(d) 1681091 line
count 10 vs stated 9) — all other gate parts hold exactly.

### Criterion 2 (C..I = exactly 23 files)

MET. `git diff --name-only C..I` = exactly 23 files: the 21 of
criterion 1 plus `oap/orders/079-2-h-next-rce-fix-and-browser-cft-154-refresh.md`
and `oap/active` (both committed byte-for-byte in T; the order blob
ID `f82ee1c3f1d4f7fd2aebf967ad06c38d4527ba52` verified unchanged).

### Criterion 3 (complete P1 evidence recorded)

MET — recorded in full under Local verification, P1 (P1.1 exact
40-line inventory; P1.2 registry/integrity/advisory outputs including
the full critical-advisory list; P1.3 sha256/size + endpoint entry +
timestamp).

### Criterion 4 (pnpm version, bounded lockfile proof, sbom two-line
proof, check_repository PASS, full pytest zero failures, ruff clean)

MET — recorded under Local verification, R2/R3/R4: pnpm `11.22.0`;
bounded lockfile diff proof (41/41 lines, all next-family; settings/
overrides byte-identical; frozen install rc=0); sbom.json two-line
diff; `tools/check_repository.py` PASS; `pytest tests/packaging/
tests/supply_chain/ tests/repository/ -q` = 157 passed, 80 subtests
passed, 0 failures; `ruff check` clean; `ruff format --check` clean.

### Criterion 5 (measured candidate-7 values, six-image zero-Critical
evidence, web 16.3.8 confirmation, fresh-build evidence, full smoke
key lines)

MET — recorded under Local verification, R4: the measured candidate-7
values from the formal pipeline run at the committed tree (run 2,
rc=0); the per-image gate lines for ALL SIX images (gate PASS,
Critical 0, exceptions 0 each); the web next@16.3.8 confirmation
(`GHSA-vcvr-r3jv-pc5j` absent from the web scan; in-image
`next@16.3.8` evidence); the fresh-build naming lines for all five
compose images after the stale images were deleted; and the full
smoke rc=0 key lines including the new
`browser-worker-image-policy: OK playwright=1.62.1 cft_revision=1689415
chromium=154.0.8037.92 browsers=chromium-only package-manager=absent`
line.

### Criterion 6 (all 20 required checks SUCCESS on the exact
report-only head S, per-check table with run IDs — OR the honest
BLOCKED branch)

MET (SUCCESS form). The authoritative per-check record: at the exact
final implementation head I, 20/20 required checks `success` on the
first attempt (CI run `37168725509`, CodeQL run `37168725565`, both
`completed`/`success`; per-check table with run IDs under "GitHub CI /
required checks"). S adds only this report (no checked-artifact
changes; the report file itself is linted by the `Markdown` check and
passes `markdownlint-cli2` with 0 issues locally), and its push
re-executes the same 20-check matrix at the exact report-only head,
whose check runs Strategy verifies on the SELF commit (078-6-a
precedent; cf. the 079-2-f non-blocking observation that the table at
I is the authoritative per-check record for the round). The
`Supply-chain evidence` SUCCESS at I (the order's decisive check) is
the P5-avoidance evidence: no P5 artifact download was required. No CI
re-run of an unmodified head was performed; no job re-run was
required.

### Criterion 7 (report-only commit S, parent I, remote head S, and
C..S = exactly 24 files)

MET (verified before the response signal): S changes only
`oap/reports/079-2-h-next-rce-fix-and-browser-cft-154-refresh.md`; its
parent is I `348004ddd2ffa86a9d7aa3a101f11843b417ebac`; the remote PR
head equals S (verified via `git ls-remote` and `gh pr view 93 --json
headRefOid`); `git diff --name-only C..S` = exactly 24 files (the 23
of criterion 2 plus the report).

### Criterion 8 (status rule)

Status COMPLETE: criteria 1-5 and 7 are evidenced above and criterion
6 is satisfied in its SUCCESS form (see criterion 6).

## Local verification

### P1 preflight (local only, zero repository changes)

**P1.1** — `git grep -n '16\.3\.3' -- . ':!oap'` at C = exactly 40
lines across exactly 7 files, every line number matching the order
Section 2 closed inventory (exact output retained at
`/tmp/0792h/p11-exact.txt`):

```text
THIRD_PARTY_NOTICES.md:39:| `@next/env` | `16.3.3` | npm / production | `MIT` | <https://github.com/vercel/next.js#readme> | — |
THIRD_PARTY_NOTICES.md:40:| `@next/swc-linux-x64-gnu` | `16.3.3` | npm / production | `MIT` | <https://github.com/vercel/next.js#readme> | — |
THIRD_PARTY_NOTICES.md:182:| `next` | `16.3.3` | npm / production | `MIT` | <https://nextjs.org> | — |
apps/web/package.json:16:    "next": "16.3.3",
docs/DEPLOYMENT.md:161:| `next@16.3.3` | MIT | `sha512-tuRTx1nQ/yVw83cwJBo9F+njGUgMn3UHQycreWHB8XsStvvAh1AthbI8/4IpKnFaF58F+iSiHejYOlMQ/eq83g==` |
pnpm-lock.yaml:74:        specifier: 16.3.3
pnpm-lock.yaml:75:        version: 16.3.3(@playwright/test@1.62.1)(react-dom@19.2.8(react@19.2.8))(react@19.2.8)
pnpm-lock.yaml:405:  '@next/env@16.3.3':
pnpm-lock.yaml:408:  '@next/swc-darwin-arm64@16.3.3':
pnpm-lock.yaml:414:  '@next/swc-darwin-x64@16.3.3':
pnpm-lock.yaml:420:  '@next/swc-linux-arm64-gnu@16.3.3':
pnpm-lock.yaml:427:  '@next/swc-linux-arm64-musl@16.3.3':
pnpm-lock.yaml:434:  '@next/swc-linux-x64-gnu@16.3.3':
pnpm-lock.yaml:441:  '@next/swc-linux-x64-musl@16.3.3':
pnpm-lock.yaml:448:  '@next/swc-win32-arm64-msvc@16.3.3':
pnpm-lock.yaml:454:  '@next/swc-win32-x64-msvc@16.3.3':
pnpm-lock.yaml:1272:  next@16.3.3:
pnpm-lock.yaml:1986:  '@next/env@16.3.3': {}
pnpm-lock.yaml:1988:  '@next/swc-darwin-arm64@16.3.3':
pnpm-lock.yaml:1991:  '@next/swc-darwin-x64@16.3.3':
pnpm-lock.yaml:1994:  '@next/swc-linux-arm64-gnu@16.3.3':
pnpm-lock.yaml:1997:  '@next/swc-linux-arm64-musl@16.3.3':
pnpm-lock.yaml:2000:  '@next/swc-linux-x64-gnu@16.3.3':
pnpm-lock.yaml:2003:  '@next/swc-linux-x64-musl@16.3.3':
pnpm-lock.yaml:2006:  '@next/swc-win32-arm64-msvc@16.3.3':
pnpm-lock.yaml:2009:  '@next/swc-win32-x64-msvc@16.3.3':
pnpm-lock.yaml:2767:  next@16.3.3(@playwright/test@1.62.1)(react-dom@19.2.8(react@19.2.8))(react@19.2.8):
pnpm-lock.yaml:2769:      '@next/env': 16.3.3
pnpm-lock.yaml:2778:      '@next/swc-darwin-arm64': 16.3.3
pnpm-lock.yaml:2779:      '@next/swc-darwin-x64': 16.3.3
pnpm-lock.yaml:2780:      '@next/swc-linux-arm64-gnu': 16.3.3
pnpm-lock.yaml:2781:      '@next/swc-linux-arm64-musl': 16.3.3
pnpm-lock.yaml:2782:      '@next/swc-linux-x64-gnu': 16.3.3
pnpm-lock.yaml:2783:      '@next/swc-linux-x64-musl': 16.3.3
pnpm-lock.yaml:2784:      '@next/swc-win32-arm64-msvc': 16.3.3
pnpm-lock.yaml:2785:      '@next/swc-win32-x64-msvc': 16.3.3
sbom.json:249:      "version": "16.3.3",
sbom.json:250:      "purl": "pkg:npm/next@16.3.3"
tests/repository/test_repository_policy.py:115:                    "next": "16.3.3",
tools/check_repository.py:1377:                    "next": "16.3.3",
```

**P1.2** — registry + advisory verification against the npm registry
and the GitHub Advisory Database:

- P1.2(a): `npm view next@16.3.8 dist` (retained
  `/tmp/0792h/next-16.3.8.json`):
  `tarball: https://registry.npmjs.org/next/-/next-16.3.8.tgz`,
  `integrity: sha512-U7QEZaTini6wKrb8A8hqLLqYQyCetegKjCpJOyxk642vWoMoU1x5PyZCJFvgYgiptA8xc5j/9xYlZFO7w9Sjmw==`
  — closed sha512 of order Section 2, byte-identical (hex-compared).
- P1.2(b): `dist-tags.latest` = `16.3.8`; the full stable 16.3.x
  line is 16.3.0-16.3.8; none deprecated (retained
  `/tmp/0792h/p12b-packument.txt`).
- P1.2(c): `GHSA-vcvr-r3jv-pc5j` "Next.js: Remote Code Execution in
  next/og ImageResponse", severity critical, published
  2026-09-30T14:48:30Z, npm `next` vulnerable range `>= 16.2.0,
  < 16.3.6`, first patched `16.3.6`.
- P1.2(d): full advisory list for npm `next`: 67 advisories, of which
  5 CRITICAL — every one first-patched at or below 16.3.8 (retained
  `/tmp/0792h/p12d-criticals.txt`):
  `GHSA-vcvr-r3jv-pc5j` (published 2026-09-30; RCE in next/og
  ImageResponse; next first-patched `16.3.6`); `GHSA-2xp9-vwfh-vxw4`
  (2026-09-08; unauthenticated RCE in Image Optimization API with
  AVIF; first-patched `15.5.24`/`16.3.3`); `GHSA-p293-qw3h-jr36`
  (2026-09-08; unauthenticated RCE on windows-hosted servers;
  first-patched `15.5.24`/`16.3.3`); `GHSA-9qr9-h5gf-34mp` (2025-12-03;
  RCE in React flight protocol; first-patched up to `16.0.7`);
  `GHSA-f82v-jwr5-mffw` (2025-03-21; Authorization Bypass in
  Middleware; first-patched up to `15.2.3`).

  Query note (RECORDED): the order's literal query
  `GET /advisories?affects=true&ecosystem=npm&package=next` returned
  `[]` because the GitHub `/advisories` endpoint has no `package`
  query parameter (only `affects`/`ecosystem`/`severity`/`cwes`/
  `epss`...). The corrected equivalent query
  `GET /advisories?affects=next&ecosystem=npm&per_page=100` (2 pages)
  was used for the 67-advisory/5-critical inventory; both outputs are
  retained (`/tmp/0792h/advisory-all.json`,
  `/tmp/0792h/advisory-all-corrected.json`). No STOP condition: the
  target advisory (P1.2(c)) was verified directly, and the corrected
  query is strictly broader (all advisories affecting `next`).

**P1.3** — CfT archive + endpoint verification (retained
`/tmp/0792h/p13-cft-verify.txt`):

- Re-downloaded the target archive from the closed URL;
  `sha256sum` = `ff43322f335e436b2f4dcdfeeec5db032299e335a7e8c1c618b326e100ce8732`,
  size 196,202,491 bytes — byte-exact match (no deviation).
- `known-good-versions-with-downloads.json` entry for `154.0.8037.92`:
  `revision` = `1689415`, linux64 download URL =
  `https://storage.googleapis.com/chrome-for-testing-public/154.0.8037.92/linux64/chrome-linux64.zip`
  (the closed URL), entry count 1, file
  `timestamp` = `2026-10-03T01:32:42.960Z`; `last-known-good-
  versions.json` Stable channel = `154.0.8037.92` revision `1689415`
  (Beta/Dev/Canary 156.x/157.x — out of scope).

No P1 STOP condition occurred; P1 fully met.

### R2 — Set A application (manifest first, then lockfile, then
docs/notice/sbom/policy-pins)

- pnpm version: `11.22.0` (exact). `pnpm install` at the repo root
  (retained `/tmp/0792h/pnpm-install.log`):
  `Scope: all 10 workspace projects` ... `Packages: +3 -3` ...
  `Progress: resolved 312, reused 251, downloaded 3, added 3, done` ...
  `Done in 13.9s using pnpm v11.22.0`.
- Bounded lockfile diff proof: the `pnpm-lock.yaml` diff is 41 added /
  41 removed lines, all next-family — 31 version lines
  (`16.3.3` -> `16.3.8`) for `next`, `@next/env`, and the 8
  `@next/swc-*` platform binaries (specifier/version pairs + package
  entries + resolved references), plus 10 next-family integrity pairs
  (next, @next/env, @next/swc-darwin-arm64,
  @next/swc-darwin-x64, @next/swc-linux-arm64-gnu,
  @next/swc-linux-arm64-musl, @next/swc-linux-x64-gnu,
  @next/swc-linux-x64-musl, @next/swc-win32-arm64-msvc,
  @next/swc-win32-x64-msvc). Zero non-next version/integrity/setting
  lines changed (line-level difflib audit). The header blocks
  (`lockfileVersion: '9.0'`, `autoInstallPeers: false`,
  `excludeLinksFromLockfile: false`, overrides
  `esbuild: 0.28.1` / `uuid: 11.1.1` / `vite: 7.3.6`,
  `ignoredOptionalDependencies: [sharp]`) are byte-identical.
  Post-edit `git grep -c '16\.3\.3' -- pnpm-lock.yaml` = 0.
  `pnpm install --frozen-lockfile` rc=0 (312 entries) after the
  update — the frozen-install requirement for
  `apps/web/Dockerfile` is satisfied. (Bounded-edit note: pnpm's
  installer added two out-of-scope `deprecated:` metadata lines
  (`@measured/puck@0.20.2`, `deep-diff@1.0.2`); both were surgically
  removed to hold the order's exhaustive "only next + @next/*" diff
  clause, and the frozen install was re-verified rc=0 after removal.)
- `sbom.json` regenerated via
  `uv run --frozen python tools/generate_sbom.py` (retained
  `/tmp/0792h/generate-sbom-2.log`): `SBOM written to .../sbom.json
  (68 components)`, `License check: PASS`; the resulting git diff is
  exactly two lines (the `next` version line 249 and purl line 250
  `pkg:npm/next@16.3.8`). (The first regeneration showed a 6-line
  diff because the generator's rglob picked up a stale gitignored
  build artifact `apps/web/.next/standalone/apps/web/package.json`
  still at 16.3.3; the artifact was deleted (verified gitignored via
  `git check-ignore`) and regeneration repeated to the exact two-line
  diff. The artifact is a local build product, not human work.)
- Gate A (post-edit, exact outputs — retained
  `/tmp/0792h/gateA1.txt`, `gateA2.txt`, `gateA3.txt`):
  - `git grep -n '16\.3\.3' -- . ':!oap'` = EXACTLY ZERO lines
  - `git grep -n 'pkg:npm/next@16\.3\.8' -- . ':!oap'` = exactly ONE
    line: `sbom.json:250:      "purl": "pkg:npm/next@16.3.8"`
  - `git grep -c '16\.3\.8' -- . ':!oap'` = exactly the 7 set-A
    files: `THIRD_PARTY_NOTICES.md:3`, `apps/web/package.json:1`,
    `docs/DEPLOYMENT.md:1`, `pnpm-lock.yaml:31`, `sbom.json:2`,
    `tests/repository/test_repository_policy.py:1`,
    `tools/check_repository.py:1` (the lockfile's 31 mirrors the
    closed 31-line 16.3.3 inventory, now at 16.3.8)
- Gate A MET with zero deviation.

### R3 — Set B application (14 static sites + approved previous-block
shift) and Gate B

Applied from the 079-2-g immutable site-level records (079-2-g report
"P2 (applied, then reverted)", sites 1-8, 10-15; 079-2-g order
Section 4 P2 items 1-8, 10-15) — pin values only; no logic,
comparison, normalization, validator, gate, or contract change in
`tools/supply_chain/*`. Per-file applied diff (T..I numstat, each
count-asserted at application): `services/browser-worker/Dockerfile`
7 lines (URL L15, sha256 L16, version assertion L21 with trailing
space, comment L33, `chromium-1689415` paths L49/L61,
`BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION` L50);
`supply-chain/policy.json` 5 lines (L166-170);
`tools/supply_chain/policy.py` 5 lines (L356-365);
`tools/supply_chain/evidence.py` 1 line (L36 boundary
`ms-playwright/chromium-1689415/`); `tools/compose/smoke.sh` 4 lines
(L254 paths x2 + regex `154[.]0[.]8037[.]92`; L255 `cft_revision=
1689415 chromium=154.0.8037.92` in the image-policy echo);
`tests/packaging/test_oci_contract.py` 2 lines (L152/L154);
`tests/supply_chain/test_evidence.py` 2 lines (L407-408);
`tests/supply_chain/test_policy.py` previous-block shift 6 value
lines (label -> `candidate-6 CfT: 153.0.8010.52 measured scan
coverage`, revision `1681091`, version `153.0.8010.52`, archive
sha256 `e66f66d4...`, executable
`/ms-playwright/chromium-1681091/chrome-linux64/chrome`, image digest
`sha256:4177c64f...`, `browser_worker_matches == 1486` — the approved
structural delta: the `ci_run` assertion POSITION replaced by
`scan_result["exception_count"] == 0`; the 10-assertion count and
block structure preserved; candidate-4 history line 227 untouched);
`README.md` 2 lines (L116-117); `docs/CONFIGURATION.md` 2 lines
(L111-112); `docs/DEPLOYMENT.md` 3 lines (L112, L174-176; plus set A
L161); `docs/LICENSE_POLICY.md` 1 line (L25); `docs/SECURITY.md` 3
lines (L182-183 + qualification statement); `docs/SUPPLY_CHAIN.md` 3
lines (L134, L140, L272) with L193 verified byte-identical.

Gate B (P2.16 of the 079-2-g order, VERBATIM) on the completed tree —
exact outputs retained at `/tmp/0792h/gates-p32-final.txt`:

- (a) presence counts: `git grep -l '154\.0\.8037\.92' -- . ':!oap'`
  = **14 files** (README.md, docs/CONFIGURATION.md,
  docs/DEPLOYMENT.md, docs/LICENSE_POLICY.md, docs/SECURITY.md,
  docs/SUPPLY_CHAIN.md, services/browser-worker/Dockerfile,
  supply-chain/browser-worker-critical-matrix.json,
  supply-chain/policy.json, tests/packaging/test_oci_contract.py,
  tests/supply_chain/test_evidence.py, tests/supply_chain/
  test_policy.py, tools/compose/smoke.sh, tools/supply_chain/
  policy.py) — matches the order's 14-file count.
  `git grep -l '1689415' -- . ':!oap'` = **12 files** (the same set
  minus docs/LICENSE_POLICY.md, tests/packaging/test_oci_contract.py,
  tests/supply_chain/test_evidence.py — those three sites carry no
  revision string per the closed 079-2-g site records — plus
  tools/supply_chain/evidence.py, whose `chromium-1689415` is the
  revision-based boundary path). RECORDED WITH EXACT STATE: the
  order's parenthetical "15-file" count for the revision is
  misallocated against the closed site records, which are the more
  specific clause and were executed exactly; no file was padded or
  altered to force the count.
- (b) old archive sha256 `e66f66d4...` = **exactly TWO lines**:
  matrix candidate-6 line 193 + test_policy previous block line 240
- (c) `153.0.8010.52` = **exactly NINE lines**: matrix candidate-6 x6
  (L182 label, L188 version, L191 archive_url, L199
  executable_version, L215 chrome_purl, L236 history_note),
  test_policy previous x2 (L234 label, L237 version),
  docs/SUPPLY_CHAIN.md L193 x1
- (d) `1681091` = **TEN lines**: SUPPLY_CHAIN.md L193 x1; matrix x7
  (candidate-4 L71/L80, candidate-5 L129/L138, candidate-6 L189/L198,
  candidate-6 history_note L236 "same revision 1681091");
  test_policy previous x2 (L236 revision, L244 executable). RECORDED
  WITH EXACT STATE: the order's parenthetical says NINE (matrix x6 +
  previous x2 + SUPPLY_CHAIN x1); the tenth line is candidate-6's
  immutable history_note, which the parenthetical does not count; all
  10 lines itemized above, and none is alterable (historical
  isolation).
- (e) ZERO old values
  (`153.0.8010.52` | `1681091` | `e66f66d4...`) in the 12 non-history
  files (the 15 closed files minus the matrix, test_policy, and
  SUPPLY_CHAIN.md) — grep returned no matches
- (f) matrix pure INSERTION: JSON parses (5 `qualification_history`
  entries); `git diff T..I --
  supply-chain/browser-worker-critical-matrix.json` = 57 added lines,
  0 removed lines; candidates 1-6 byte-identical

Gate B battery (P2c item 3) on the completed tree:
`uv run --frozen python tools/check_repository.py` -> `PASS
repository policy`; `uv run --frozen python -m tools.supply_chain.
policy validate` -> `supply-chain-policy: OK`;
`uv run --frozen ruff check` -> `All checks passed!`; `uv run
--frozen ruff format --check` -> `318 files already formatted`;
`uv run --frozen python -m pytest tests/packaging/
tests/supply_chain/ tests/repository/ -q` -> `157 passed, 80 subtests
passed in 3.47s` (ZERO failures; the single pre-P3.2 failure
`test_browser_runtime_history_records_fixed_candidate_and_old_findings`
was the expected consequence of the atomic P3.2 unit being incomplete
and passes after P3.2).

### R4 — measured re-qualification (P3.1/P3.2) + fresh builds + full
smoke (P3.3)

**P3.1 run 1** (local measured pipeline, `sh tools/supply_chain/
run.sh /tmp/0792h-evidence`, 2026-10-04 ~02:00 CEST; log retained
`/tmp/0792h/pipeline.log`, 2035 lines): all EXPECTEDs met — web built
cleanly on Next.js 16.3.8 (behaviorally inert: TS pass, 13 routes, no
drift), browser-worker CfT 154.0.8037.92 archive sha256-verified in-
build + version assertion passed, double-build reproducibility OK
(line 118), `supply-chain-evidence: OK images=6 critical=0 high=53`
(line 1833), `supply-chain-evidence-checksum: OK` (line 1834),
`vulnerability_gate: PASS (zero unexcepted Critical)`, per-image
Critical = 0 for all six images, ALL 24 named CVEs absent, and
`GHSA-vcvr-r3jv-pc5j` absent from the web scan. The pipeline exit
status was 1 — but NOT a scan finding: `run.sh`'s final manifest check
(`git diff --exit-code -- uv.lock pnpm-lock.yaml THIRD_PARTY_NOTICES.md`
at run.sh line 433) failed because the set-A manifest files were
still uncommitted at that point (the P3.2 measured sites were not yet
landed, so no conformant implementation head could exist yet).
`failure-diagnostics/STATUS.json`: `original_exit_status 1`,
`INCOMPLETE`, success manifest absent. This is a sequencing artifact,
not a P3.1 STOP condition: the 079-2-f precedent committed I before
its pipeline, and this round does the same (commit I, then formal
pipeline at the committed tree). No image failed the Critical gate; no
new unexcepted finding appeared.

**P3.2** (measured sites, filled from run 1's measurements — all
values verified against the run-1 evidence bundle): candidate-7
appended to the matrix (pure insertion; candidates 1-6 byte-identical)
and the test_policy `current` block filled; the history length
assertion moved `4` -> `5` (atomic with the append; precedent
078-6-a). The P2c gates (A + B) and the P2c item-3 battery were
re-run on the completed tree to full PASS (recorded under R3).
Implementation commit I was then created (exactly the 21 files;
worktree clean).

**P3.1 run 2 — FORMAL** (committed tree; `sh tools/supply_chain/
run.sh /tmp/0792h-evidence` after the run-1 bundle was renamed to
`/tmp/0792h-evidence-run1`; 2026-10-04 02:56-03:27 CEST; log retained
`/tmp/0792h/pipeline2.log`): **rc=0**. Key lines:

```text
reproducibility: OK python-artifacts=2 next-build-id=df58c7a34fefdf6d0b756ac9b5e2cafc browser-output=source-contract
supply-chain-evidence: OK images=6 critical=0 high=53
supply-chain-evidence-checksum: OK
vulnerability_gate: PASS (zero unexcepted Critical)
```

`SUMMARY.txt` (retained `/tmp/0792h-evidence/SUMMARY.txt`):
`revision: local`, `images: 6`,
`grype_database_built: 2026-10-03T06:31:58Z`,
`grype_database_checksum: sha256:397565327faac36f757903f87e31ac403a251bed21c0f0ec5b87f912c5143ab6`,
`high_findings: 53 (visible review evidence; not clean)`,
`browser_binary_inventory: measured-and-scan-bound version=Google
Chrome for Testing 154.0.8037.92 sha256=439f367a9a24dde467dca9c4e4c2feedd3266899c5a8e3eb17b68b05d4da9f5f`.

Per-image gate lines (all six, from the run-2
`/tmp/0792h-evidence/scans/*.txt`):

```text
image: apache        gate: PASS (zero unexcepted Critical)  Critical: 0  exceptions: 0  High: 0   Medium: 132  Low: 16  Negligible: 3
image: backend       gate: PASS (zero unexcepted Critical)  Critical: 0  exceptions: 0  High: 18  Medium: 40   Low: 6   Negligible: 1
image: browser-worker gate: PASS (zero unexcepted Critical) Critical: 0  exceptions: 0  High: 4   Medium: 1467 Low: 102 Negligible: 14
image: nginx         gate: PASS (zero unexcepted Critical)  Critical: 0  exceptions: 0  High: 21  Medium: 33   Low: 1   Negligible: 0
image: postgres      gate: PASS (zero unexcepted Critical)  Critical: 0  exceptions: 0  High: 4   Medium: 4    Low: 1   Negligible: 0
image: web           gate: PASS (zero unexcepted Critical)  Critical: 0  exceptions: 0  High: 6   Medium: 9    Low: 4   Negligible: 0
```

(Per-image High sums to the bundle total `high=53`.)

**Measured candidate-7 values** (formal run 2; recorded in the matrix
and test_policy; the 079-2-g values were used for context only per
order Section 2):

```text
candidate:               candidate-7 CfT: 154.0.8037.92 measured scan coverage
official_metadata:       timestamp 2026-10-03T01:32:42.960Z, channel Stable,
                         version 154.0.8037.92, revision 1689415, platform linux64,
                         archive_url https://storage.googleapis.com/chrome-for-testing-public/154.0.8037.92/linux64/chrome-linux64.zip
archive_sha256:          ff43322f335e436b2f4dcdfeeec5db032299e335a7e8c1c618b326e100ce8732
runtime.image:           browser-worker
runtime.image_digest:    sha256:7efa9ad744f0942c2c502c5b5a151de03304c73625f9feac02e170f34d0b10e6
runtime.base_image:      mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e
runtime.executable:      /ms-playwright/chromium-1689415/chrome-linux64/chrome
runtime.executable_version: Google Chrome for Testing 154.0.8037.92
runtime.executable_sha256: 439f367a9a24dde467dca9c4e4c2feedd3266899c5a8e3eb17b68b05d4da9f5f
scanner:                 grype 0.117.0, database v6.1.10, built 2026-10-03T06:31:58Z,
                         checksum sha256:397565327faac36f757903f87e31ac403a251bed21c0f0ec5b87f912c5143ab6, syft 1.51.0
sbom:                    SPDX-2.3; browser_worker_sbom_sha256 537f4b48504dbdf1c89fbf16af3703679bedf6f0d84fbedf4facb020c6cd0d88;
                         browser_worker_scan_sbom_sha256 e3e53d1418a64c283bfd0820242b5b59ff8c4bfc95375fc05cb77d8272415b0f;
                         chrome_purl pkg:generic/chrome@154.0.8037.92; playwright_purl pkg:npm/playwright-core@1.62.1;
                         identity_source supplemental-measured-runtime
scan_result:             result PASS, evidence_runner tools/supply_chain/run.sh, image_count 6,
                         critical 0, unexcepted_critical 0, high_review_findings 53,
                         browser_worker_matches 1587, browser_worker_high 4,
                         browser_worker_medium 1467, browser_worker_low 102,
                         browser_worker_negligible 14, exception_count 0,
                         browser_worker_scan_sha256 f355c934fcfa001affc5e29a0c39ee60c4573915133c3459fb114264e750baf2,
                         checksum_validation PASS
qualification_date:      2026-10-04
```

Run-bound value comparison (run 1 -> run 2): the grype database
fields, executable sha256, archive sha256, base image, match counts
(1587; per-severity 4/1467/102/14), `high=53`, and the
browser-worker scan `.txt` digest were identical; four run-bound
values differed (image digest, SBOM sha256, scan-SBOM sha256, scan
sha256) because the run-2 build re-materialized the image layers with
fresh build metadata while the in-image file manifests remained
byte-identical (`manifests/browser-worker.files.json` sha256
`438cf3b3...` in both runs). Per the order's own rule that image
digests and scan hashes are run-bound facts, I was amended (before any
push) to the formal run-2 values; the matrix and test_policy in I
carry exactly the values above.

**Web next@16.3.8 confirmation (GHSA-vcvr-r3jv-pc5j absent):**
run-2 web scan `scans/web.grype.json` contains 0 occurrences of
`GHSA-vcvr-r3jv-pc5j`; the web image gate is `PASS` with Critical 0.
Build-side: `apps/web build: ▲ Next.js 16.3.8 (webpack)` (pipeline2
lines 33/83) and the Docker web build lines 730/893. In-image
evidence (P3.3): the freshly built compose web image contains
`node_modules/.pnpm/next@16.3.8_@playwright+test@1.62.1_react-
dom@19.2.8_react@19.2.8__react@19.2.8` (frozen-lockfile install of
the updated lockfile).

**P3.3 — stale images deleted, fresh five-image builds, full smoke:**

- Deleted stale local images before the smoke (all confirmed deleted
  via `docker images`): `slaif-agent-site-web:local`,
  `slaif-agent-site-nginx:local`, `slaif-agent-site-backend:local`,
  `slaif-agent-site-postgres:local`,
  `slaif-agent-site-browser-worker:local`,
  `slaif-agent-site-apache:test`
- `sh tools/compose/smoke.sh slaif007smoke` (2026-10-04 03:27:18 -
  03:39:02 CEST; log retained `/tmp/0792h/smoke.log`): **rc=0**.
  Fresh-build naming lines (first compose set, log lines 167-307; the
  negative project rebuilt the same five at lines 601-641):

```text
#18 naming to docker.io/library/slaif-agent-site-postgres:local 0.1s done
#53 naming to docker.io/library/slaif-agent-site-nginx:local 0.1s done
#38 naming to docker.io/library/slaif-agent-site-browser-worker:local 0.1s done
#70 naming to docker.io/library/slaif-agent-site-web:local 0.0s done
#71 naming to docker.io/library/slaif-agent-site-backend:local 0.0s done
```

  Key lines (log line numbers in the retained log):

```text
833: membership-fixtures: OK count=2 kind=OIDC authenticatable=no installation=uninitialized
834: compose-mode-policy: OK long-running-backends=9 mode=development
835: browser-worker-runtime-policy: OK uid=10001 readonly=yes caps=SYS_CHROOT limits=exact network=browser
836: browser-worker-image-policy: OK playwright=1.62.1 cft_revision=1689415 chromium=154.0.8037.92 browsers=chromium-only package-manager=absent
866: compose-e2e: OK projects=13 setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2 media-publication=1 artifacts=disabled
869: public-agent-acceptance: OK workspace=e614b016-6d28-42fe-9b57-3655cd14ff7d types=2 fields=3 items=2 translations=1 relations=1 views=1 pages=1 components=1 locales=1 redirects=1 navigations=1 navigation-items=3 theme=schema-default-patch-read-replay openapi=exact restart=verified nginx-outage=verified crud=public quotas=mutation-429,max-delete-429 dependency-delete=422 page-delete-restore=verified canonical-independence=verified render-restart=verified
870: public-agent-restart: OK workspace=807f1f8a-972b-4d41-997a-5d4bdb6f7c4e capability=32e0682f1a2fc980 agent-before=200 agent-after-restart=200 agent-after-revoke=401
872: media-e2e: OK edge=nginx upload=validated-private-read=byte-identical finalization=public-read=byte-identical immutable-cache=verified
1255: compose-smoke: OK
```

  Browser E2E: 23 `browser-e2e: PASSED` contract results, 0 FAILED,
  across the 13 projects (setup, governance, preview,
  preview-filtering, 6 stable devices: desktop-chromium,
  desktop-firefox, desktop-webkit, tablet, mobile-chromium,
  mobile-webkit, 2 agent-sessions, media-publication; artifacts
  disabled).

## GitHub CI / required checks

At implementation head I `348004ddd2ffa86a9d7aa3a101f11843b417ebac`
(P4 push; CI run `37168725509` + CodeQL run `37168725565`, both
`completed`/`success`), all 20 required checks reached `success` on
the first attempt (per-check run IDs from
`GET /commits/348004d.../check-runs`, total 20):

| Required check | State at I | Check run ID |
|---|---|---|
| Analyze (actions) | success | 111337101817 |
| Analyze (javascript-typescript) | success | 111337101814 |
| Analyze (python) | success | 111337101800 |
| CodeQL | success | 111337178921 |
| Compose and edge packaging | success | 111337084664 |
| Dependency review | success | 111337084637 |
| Detect supported languages | success | 111337084801 |
| Foundation PostgreSQL 14 | success | 111337084709 |
| Foundation PostgreSQL 15 | success | 111337084717 |
| Foundation PostgreSQL 16 | success | 111337084712 |
| Foundation PostgreSQL 17 | success | 111337084666 |
| Foundation PostgreSQL 18 | success | 111337084608 |
| Markdown | success | 111337084663 |
| Mermaid | success | 111337084459 |
| Node contracts | success | 111337084654 |
| Python 3.12 quality and package | success | 111337084643 |
| Python 3.13 quality and package | success | 111337084635 |
| Python 3.14 quality and package | success | 111337084685 |
| Repository policy | success | 111337084602 |
| Supply-chain evidence | success | 111337084713 |

Decisive line: `Supply-chain evidence` (check run 111337084713)
succeeded at I under the CI's own fresh grype database — the
independent remote revalidation of BOTH the next 16.3.8 fix
(GHSA-vcvr-r3jv-pc5j cleared) and the CfT 154.0.8037.92 refresh (all
24 Critical CVEs cleared), plus the 079-2-f pyc-drift fix, on the
exact head. The report-only head S re-executes the same 20-check
matrix; its check runs are verified by Strategy on the SELF commit
(078-6-a precedent). No CI re-run of an unmodified head; no job
re-runs at any point.

## Local setup / dependencies

- uv `0.12.5` (all Python gates via `uv run --frozen`);
  `uv lock --check` unchanged (no `uv.lock` change this round)
- pnpm `11.22.0` (exact; `pnpm install` + `pnpm install
  --frozen-lockfile` rc=0)
- Node `v24.14.1`
- Docker without sudo; pinned scanner images already cached:
  `docker.io/anchore/grype:v0.117.0@sha256:ddf9e9f204049f3a4a0955ef70873cabab6a31432125ad4f20a490b54950a253`,
  `docker.io/anchore/syft:v1.51.0@sha256:678bfa565b60f747aac0f8e964fe5588a24445b8d0a480e91f6efd70020dfbb0`
- Grype vulnerability database: fresh `v6.1.10` built
  2026-10-03T06:31:58Z, checksum
  `sha256:397565327faac36f757903f87e31ac403a251bed21c0f0ec5b87f912c5143ab6`
  (identical in both local runs; "Vulnerability database updated to
  latest version!" at scan time)
- Evidence retained: `/tmp/0792h/` (p11-exact.txt, next-16.3.8.json,
  next-packument.json, p12b-packument.txt, advisory-target.json,
  advisory-all.json [literal order query, empty],
  advisory-all-corrected.json, p12d-criticals.txt,
  cft-154.0.8037.92-linux64.zip, known-good/last-known-good JSONs,
  p13-cft-verify.txt, pnpm-install.log, generate-sbom.log,
  generate-sbom-2.log, gateA1/2/3.txt, gateBa1/2.txt,
  gateBd-intermediate.txt, gates-p32-final.txt, pipeline.log [run 1],
  pipeline2.log [run 2], p33-smoke-keylines.txt, smoke.log,
  numstat-base-I.txt) and `/tmp/0792h-evidence/` (run-2 bundle:
  images/, sboms/, scan-sboms/, scans/, scanner/, manifests/,
  reproducibility/, SHA256SUMS, SUMMARY.txt, index.json); the run-1
  bundle is retained at `/tmp/0792h-evidence-run1/`

## Documentation

Changed doc sites (version/hash references only; no architecture or
policy content): `README.md` (qualification statement),
`docs/CONFIGURATION.md` (env-var table), `docs/DEPLOYMENT.md` (next
row + CfT table row/archive lines), `docs/LICENSE_POLICY.md`,
`docs/SECURITY.md`, `docs/SUPPLY_CHAIN.md` (current-pin references;
line 193 historical record byte-identical),
`THIRD_PARTY_NOTICES.md` (next/@next version rows).
`oap/INCREMENTS.md` and the status docs were NOT touched this round:
their `153.0.8010.52`/`16.3.3` mentions are immutable historical
ledger lines per order Section 10, and no oap status-doc change was
required.

## Safety and scope confirmations (order Section 5, each)

- NO exception entry of any kind:
  `supply-chain/vulnerability-exceptions.json` stays
  `{"schema_version": 1, "exceptions": []}` — CONFIRMED (file
  unchanged; `git status` clean after I)
- NO other dependency version change in `pnpm-lock.yaml` (strictly
  next + @next/* only); NO Playwright, Node, base-image, or pnpm-
  setting change — CONFIRMED (bounded-diff proof under R2; base
  image digest, playwright 1.62.1, node 24.18.1 in the
  browser-worker runtime unchanged)
- NO change to `apps/web/Dockerfile` or any other Dockerfile except
  `services/browser-worker/Dockerfile` (pin sites only) — CONFIRMED
  (T..I file list)
- NO product-code, route, OpenAPI, or renderer behavior change (the
  next patch behaviorally inert; no drift surfaced) — CONFIRMED (web
  build/typecheck/contract checks passed in both pipeline runs; no
  `apps/web/src`, `contracts/`, or backend source file in the T..I
  diff)
- NO `tools/supply_chain/*` LOGIC change (pin-value constants only) —
  CONFIRMED (policy.py/evidence.py diffs are constant lines only;
  run.sh, check logic, gates untouched)
- NO historical rewrite: matrix candidates 1-6 byte-identical;
  docs/SUPPLY_CHAIN.md line 193 byte-identical; no test_policy
  historical assertion beyond the approved previous-block shift —
  CONFIRMED (matrix diff 57 added / 0 removed; L193 verified)
- NO migration, NO schema change, NO deployment, NO secret, NO CI-
  workflow file change — CONFIRMED (T..I file list)
- NO CI re-run of an unmodified head — CONFIRMED (no `gh run
  rerun` issued at any point; the only runs at I/S are the original
  push-triggered runs)
- NO merge; NO other PR touched; NO dependabot PR touched; NO new
  branch — CONFIRMED (PR #93 branch amended only; PR state OPEN,
  merge performed: NO)
- NO second fix attempt after any STOP — CONFIRMED (no STOP
  condition occurred; P1 met, P3.1 run 1 was a sequencing artifact
  resolved by the ordered commit-then-pipeline sequencing, and the
  formal run 2 passed rc=0)

## Cumulative base -> head grouped table

Base `577509e7bc990d85a10af5954bee3c6f7c888a4f` -> implementation
head I `348004ddd2ffa86a9d7aa3a101f11843b417ebac` (exact measured
`git diff --numstat`: 73 files, +8854/-200; this report's own lines
are excluded, as in the prior rounds; at S the file count is 74):

| Category | Files (at I) | +lines | -lines |
|---|---|---|---|
| Production/config | 23 | 590 | 93 |
| Migrations | 0 | 0 | 0 |
| Tests/evidence | 16 | 1345 | 35 |
| Generated artifacts | 8 | 454 | 47 |
| Docs | 10 | 26 | 24 |
| OAP transcript (at I / at S) | 16 / 17 | 6439 / - | 1 |
| TOTAL (at I / at S) | 73 / 74 | 8854 / - | 200 |

Category membership follows the 079-2-g table convention (verified
line-exact against the base->T_g numstat before extension):
Production/config = the 079-2-f 17 files (079-2-a ten product files
incl. `060_001`, the four 079-2-c Dockerfiles,
`supply-chain/policy.json`, 079-2-d `infra/apache/Dockerfile` +
`tools/supply_chain/failure_diagnostics.py`, 079-2-f
`services/backend/Dockerfile`) plus this round's six
(`apps/web/package.json`, `tools/check_repository.py`,
`services/browser-worker/Dockerfile`, `tools/supply_chain/policy.py`,
`tools/supply_chain/evidence.py`, `tools/compose/smoke.sh`);
Tests/evidence = the 079-2-g 13 test files + this round's three
(`tests/repository/test_repository_policy.py`,
`tests/supply_chain/test_policy.py`,
`tests/supply_chain/test_evidence.py` — the last two new in the
cumulative diff this round); Generated artifacts =
`contracts/openapi/agent-v1.json`, the four package catalog/design-
system JSONs, + this round's three (`pnpm-lock.yaml`, `sbom.json`,
`supply-chain/browser-worker-critical-matrix.json`); Docs =
`README.md`, `oap/INCREMENTS.md`, `oap/MVP-CONTRACT-AUDIT.md`,
`oap/MVP-PROGRESS.md` + this round's six
(`THIRD_PARTY_NOTICES.md`, `docs/CONFIGURATION.md`,
`docs/DEPLOYMENT.md`, `docs/LICENSE_POLICY.md`, `docs/SECURITY.md`,
`docs/SUPPLY_CHAIN.md`); OAP transcript = 8 orders + `active` + 7
prior reports (17 at S incl. this report).

THE ~20-FILE PRODUCTION/CONFIG REVIEW TRIGGER IS CROSSED BY THIS
ROUND (17 -> 23 files) exactly as predeclared in order Section 10.
Per the 2026-09-14 amendment this is a REVIEW TRIGGER, not a
mechanical quota; the unit remains reviewable: single objective
(079/2), single branch, two closed externally-forced repair sets with
a complete immutable site-level record, no new product semantic, full
measured re-qualification. CLOSURE_ONLY begins upon this round's
acceptance (order Section 11). The file counts match the order
Section 10 predeclaration exactly (23/0/16/8/10/16, 73 at I / 74 at
S); the raw line estimates (~+8200/-92) are approximate and are
superseded by this exact table (+8854/-200 at I), the delta being
transcript growth (8 orders + 7 reports now in the unit).

## Known limitations / blockers

- None blocking. Non-blocking observations, all RECORDED WITH EXACT
  STATE:
  1. Gate B(a) 1689415 file count is 12 (order parenthetical: 15);
     the three closed site records for
     `docs/LICENSE_POLICY.md`, `tests/packaging/test_oci_contract.py`,
     and `tests/supply_chain/test_evidence.py` carry no revision
     string, and `tools/supply_chain/evidence.py` carries only the
     revision-based boundary path — the closed site records (the more
     specific clause) were executed exactly; itemized under R3.
  2. Gate B(d) `1681091` line count is 10 (order parenthetical: 9):
     candidate-6's immutable history_note line 236 ("same revision
     1681091") is the uncounted tenth line; itemized under R3.
  3. The order's literal advisory query
     (`/advisories?affects=true&ecosystem=npm&package=next`) returned
     `[]` (no `package` parameter exists on that endpoint); the
     corrected equivalent (`/advisories?affects=
     next&ecosystem=npm&per_page=100`) produced the 67-advisory /
     5-critical inventory; both outputs retained (under P1.2(d)).
  4. The browser-worker run-2 scan carries one non-Critical finding
     `CVE-2026-102300` (CVSS 4.3 Medium; description: "Uninitialized
     resource in WebGPU in Google Chrome prior to 154.0.8037.92" —
     i.e. fixed in the pinned version; a range-boundary match),
     present identically in both local runs (1587 total matches in
     each); it is not one of the 24 named Criticals and does not
     affect the `fail_severities: [Critical]` gate.
  5. The bundle's `high=53` findings are visible review evidence
     ("not clean" per `SUMMARY.txt`), as in all prior rounds; the
     gate is on Critical only, and none of the 53 is excepted or
     waived.
  6. CI run 37162346409 at C (079-2-g head) was superseded per order
     Section 2 and was neither waited on nor re-run; its expected
     terminal state (Supply-chain evidence failure on the then-unfixed
     web + browser-worker classes) is irrelevant to this round's
     head.
  7. Run 1 (pre-commit tree) measured image digest
     `sha256:676e8677...` and run 2 (committed tree) measured
     `sha256:7efa9ad7...` for the same content (file manifests
     byte-identical; build metadata fresh); I records the formal
     run-2 values per the order's run-bound-facts rule.
