# OAP Work Order — 078-6-a: browser-worker Chrome-for-Testing refresh (six-CVE closure)

- Identifier: `078-6-a` (increment-qualified; first round of semantic
  increment 6 of numeric Objective 078)
- PR mode: CREATE_NEW_PR
- Branch: `oap/078-6-a-browser-security-refresh` (new, from verified main)
- PR title: `OAP 078-6-a: browser-worker Chrome-for-Testing 153.0.8010.52
  refresh (six-CVE closure)`

## Verified current state (verified at activation, from live GitHub and the
live Chrome-for-Testing endpoint only)

- `main` = `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba` (`git ls-remote`
  2026-09-19 02:09 CEST)
- PR #85 (078/5) OPEN/MERGEABLE; round 078-5-c accepted by Strategy at
  2026-09-19 02:12 CEST (report-only head
  `2d69caecd77e01ea928adf693eca7607d3759d90`, parent
  `63ca6a77567f71477bd51b9617560cfef387a224`); PR #85's final 20/20 merge
  gate is deferred to round 078-5-d, which runs only after this increment
  merges into main
- The pinned Chrome for Testing `153.0.8010.36` (CfT revision 1681091) in
  the browser-worker image fails `Supply-chain evidence` on every head
  since 2026-09-18 ~22:34Z with exactly six newly published Critical
  CVEs: CVE-2026-91710, CVE-2026-91716, CVE-2026-91718, CVE-2026-91728,
  CVE-2026-91729, CVE-2026-91738. This is external scan-database drift in
  an unchanged image, documented head-by-head in the 078-5-b and 078-5-c
  reports (e.g. CI run 35407368224, job 105799799859, on head
  `2d69cae`). A plain retry fails identically.
- Strategy pre-verification (2026-09-19 ~02:11 CEST): the CfT Stable
  channel is `153.0.8010.52` at the same revision 1681091
  (`last-known-good-versions-with-downloads.json`, endpoint timestamp
  2026-09-18T21:16:57Z). linux64 archive:
  `https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.52/linux64/chrome-linux64.zip`;
  strategy-measured SHA256 `e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9`
  (195,708,470 bytes). You must independently re-verify this hash; a
  mismatch means STOP and report BLOCKED (do not pin a different hash).
- Precedent: increment 078/3 (rounds 078-t/078-u) established the
  standalone CfT replacement on top of the pinned Playwright 1.62.1 noble
  base. This increment refreshes version + hash only, within that same
  mechanism.

## Strategic context

This is increment 078/6 per the strategic re-plan (amendment 2026-09-19,
`workorders/078-remaining-scope-audit-2026-09-14.md` §6). It unblocks:
(a) the 078-5-d merge gate of PR #85 (the PR tree must contain the
refreshed pin for `Supply-chain evidence` to pass) and (b) the remaining
078/7 and 078/8 product increments, which require a green main.

## Objective

Refresh the browser-worker Chrome for Testing binary from
`153.0.8010.36` to `153.0.8010.52` (same CfT revision 1681091), clear all
six Critical CVEs against the pinned Grype with a fresh database, and
reach a full 20/20 required-check matrix green on the exact report-only
head. Base image, Playwright, node, lockfiles, application code, and every
confinement surface remain unchanged.

## Binding decisions

1. The target version is exactly `153.0.8010.52` (CfT Stable at
   activation; same revision 1681091). Do not choose any other version in
   this round.
2. Fail closed: if the pinned Grype with a fresh database does not confirm
   that all six CVEs are cleared for `153.0.8010.52` (any one still
   reported for the browser-worker image), do not pick another version
   and do not add any policy exception. Report BLOCKED with the scan
   evidence and stop; Strategy decides the next step.
3. Unchanged and byte-identical: base image
   `mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e`,
   node `v24.18.1`, Playwright/playwright-core `1.62.1`,
   `pnpm-lock.yaml`, `uv.lock`.
4. Unchanged: `chromium_revision` 1681091 and the executable path
   `/ms-playwright/chromium-1681091/chrome-linux64/chrome`. Only the
   version, archive URL, and archive SHA256 change.
5. No policy exception, no finding de-rating, no scanner input
   manipulation (078-u precedent stands).

## Bounded scope — allowed file set

- `services/browser-worker/Dockerfile` — CfT URL, archive SHA256 pin with
  `sha256sum --check --strict`, version test string,
  `BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION`, comments
- `supply-chain/policy.json` — `browser_runtime` block:
  `chromium_version`, `chromium_archive_url`, `chromium_archive_sha256`
- `tools/supply_chain/policy.py` — the hardcoded browser-runtime gate
  (version and URL literals)
- `supply-chain/browser-worker-critical-matrix.json` — append the new
  selection round to `qualification_history` following the existing
  schema, recording scanner name/version and database build facts for
  this round; historical entries and `entries` stay byte-identical
- `tools/compose/smoke.sh` — the version grep (line 248) and the
  `browser-worker-image-policy: OK` echo line
- `tools/supply_chain/evidence.py` — only if it hardcodes the version,
  URL, or hash (line 36's path is revision-based and must stay); audit
  and report either way
- `tests/supply_chain/test_policy.py`, `tests/supply_chain/test_evidence.py`,
  `tests/packaging/test_oci_contract.py` — version/URL/hash fixtures
- `README.md`, `docs/CONFIGURATION.md`, `docs/DEPLOYMENT.md`,
  `docs/LICENSE_POLICY.md`, `docs/SECURITY.md`, `docs/SUPPLY_CHAIN.md` —
  version/hash references only
- `oap/INCREMENTS.md` — add the 078/6 row per the existing ledger
  convention
- OAP transcript: this order, `oap/active`, this report

Audit the whole repository for further hardcoded
`153.0.8010.36` / `167a098c4fdec156b58a9f678c90a84f9072d789f9c6e7b35496a6987b8b7ef8`
references. Fix occurrences in mutable files and list them in the report.
References inside immutable OAP transcript files (orders/reports) stay
untouched; note them in the report.

## Explicit non-goals

- No product feature, API, contract, database, or migration change
- No browser-worker application code change (packages, server,
  `extract-zip.mjs`) — expected zero; if the refresh forces one, report
  BLOCKED before making it
- No change to the other five images (backend, web, postgres, apache,
  nginx) or their pins
- No Playwright, node, pnpm, or uv change; no lockfile change of any kind
- No Dependabot PR interaction (#65/#75/#78 stay untouched)
- No change to PR #85 or its branch
- No supply-chain policy exception

## Requirements

1. Independently download the CfT `153.0.8010.52` linux64 archive and
   verify its SHA256 equals
   `e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9`
   (size 195,708,470 bytes). On mismatch: STOP, report BLOCKED.
2. Per-CVE closure evidence: for each of the six CVEs, record the pinned
   Grype advisory data (affected and fixed version ranges) demonstrating
   that `153.0.8010.52` is not affected. Use the same pinned Grype binary
   and fresh database class as CI.
3. Apply the version + hash updates across the full allowed file set,
   including the hardcoded-reference audit above.
4. Rebuild the browser-worker image locally and run the full local Compose
   smoke (`sh tools/compose/smoke.sh <main project>` run class)
   end-to-end: all browser projects PASS, `compose-e2e: OK`,
   `public-agent-acceptance: OK`. On pre-078/5 main the global-nav
   structure pins are the pre-feature values; the existing pins are
   correct on main, so the acceptance journey must pass unmodified.
5. `python tools/check_repository.py` PASS.
6. Commit the implementation (with this order and `oap/active`
   byte-for-byte unchanged), push, open the PR, then make the report-only
   `SELF` commit (parent = this round's implementation head).
7. Wait for the full CI matrix on the report-only head. If a
   non-deterministic VM flake of the documented Puck drag class hits, at
   most one unmodified re-run of the failed job, documented in the
   report.

## Observable acceptance criteria

1. The diff is confined to the allowed file set; the only semantic change
   is CfT `153.0.8010.36` → `153.0.8010.52` (version + archive URL +
   archive SHA256). Base image digest, revision 1681091, executable path,
   node version, Playwright version, and both lockfiles are unchanged
   (byte-identity check recorded).
2. Per-CVE evidence: all six CVE-2026-917xx items recorded as cleared for
   `153.0.8010.52` by pinned Grype advisory data; the critical matrix
   carries this round's scanner + database build facts; historical matrix
   content byte-identical.
3. The full local Compose smoke passes end-to-end (exact final status
   lines recorded).
4. On the exact report-only head, all 20 required GitHub checks are
   successful — including `Supply-chain evidence`. No exception is
   permitted for this increment.
5. The report contains per-criterion evidence and the cumulative
   base→head size grouped per review-unit governance §2 (base =
   `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`).

## Predeclared review budget (review-unit governance §1)

- Production/config files: 6 expected (Dockerfile, policy.json, critical
  matrix, policy.py, smoke.sh, plus evidence.py only if the audit
  requires it)
- Migrations: 0
- Test/evidence footprint: 3 test-file fixture updates; no new tests
- Generated-contract footprint: none (no OpenAPI change)
- Docs footprint: 6 files, version/hash references only
- OAP transcript footprint: order + active + report
- Expected substantive implementation scale: under 100 lines
  (version/hash/fixture strings)
- Review trigger: cannot fire at this scale

## Security

No confinement change: exactly one browser directory under
`/ms-playwright`, uid 10001, readonly rootfs, capability drop-all plus
`CAP_SYS_CHROOT`, exact resource limits, seccomp profile,
no-new-privileges, browser-only network. No supply-chain gate weakening —
the zero-Critical requirement stays strict; only the verified upstream
binary version and its hash change. No secrets in diff or report.

## GitHub workflow

CREATE_NEW_PR: new branch `oap/078-6-a-browser-security-refresh` from
`d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`; open the PR with the title
above and a body referencing this order per repository convention; push
all commits; the report commit is `SELF`; Strategy is the only merger.

## Report requirements

Standard OAP report template plus explicitly:

- the independently verified archive SHA256 (must equal the
  strategy-measured value; record the verification command and output);
- the per-CVE closure table (six CVEs → advisory evidence);
- the scanner name/version and database build facts recorded in the
  critical matrix for this round;
- the complete list of updated hardcoded references (file:line),
  including any found beyond the file set listed above;
- byte-identity confirmation for `uv.lock` and `pnpm-lock.yaml`;
- the exact final status lines of the local Compose smoke run;
- the conclusion of every one of the 20 required checks on the exact
  report-only head;
- the cumulative base→head size grouped per review-unit governance §2.

## Local authority

Standard executor authority in the disposable VM: packages, Docker,
browser tooling, test execution, CI log retrieval. Guest sudo only if
genuinely required; record any use.
