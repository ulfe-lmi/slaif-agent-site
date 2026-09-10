# OAP Work Order — 078-u: close browser scan coverage gap

- Objective078; maintenance increment078/3; round078-u; AMEND_EXISTING_PR.
- Existing [PR #80](https://github.com/ulfe-lmi/slaif-agent-site/pull/80);
  branch `oap/078-3-browser-security-refresh`; base `main`.
- Verified main `a9d3e6800d5e8b5fd5c9cd9e0be5010184058c6b`.
- Starting report-only head `51affbe941bb26d397e0a9a6e1f7b7612c5f383f`,
  exact implementation parent `fa2a841a5a0c7ea1610a6ecd4cc2b7b318f12242`.
- No new PR, agent, browser version, exception or feature scope.

## Independently verified concrete defect

The153 payload/version/hash and unchanged confinement are real, but the zero
Critical scan claim is NOT sufficient: the deployed Chrome package disappeared
from the scanner input.

Strategy downloaded and checksum-verified both remote CI bundles:

- Previous run34446574327, artifact10140158625,
  `supply-chain-evidence-d09d870ccf7ed58e2b30a3f8551274893e7f28b5`:
  scan-sboms/browser-worker.syft.json contains binary `chrome`, version
  `152.0.7977.82`, purl `pkg:generic/chrome@152.0.7977.82`, CPE
  `cpe:2.3:a:google:chrome:152.0.7977.82:*:*:*:*:*:*:*`, bound to the real
  `/ms-playwright/chromium-1669021/chrome-linux64/chrome` location.
- Current run34459296125, artifact10145219093,
  `supply-chain-evidence-b44b75339acbcda35a259442c3228f793e88b0d3`:
  the same scanner-input file has NO Chrome/Chromium identity, only
  playwright-core among browser-related names. SPDX browser package count drops
  from521 to520 and generic packages from1 to0. Grype scans that Syft JSON,
  so it is not evaluating Chrome153. The current matrix explicitly admits
  missing Chrome identity. An executable hash alone is not a vulnerability scan.

Local copies, if still present:
`/tmp/slaif-078t-previous-evidence-MUF4HN` and
`/tmp/slaif-078t-evidence-mfRQxY`. Remote artifacts are authoritative.
The SUMMARY browser_binary_inventory line is hardcoded empty in evidence.py;
replace it with truthful validated inventory status, not another fixed PASS.

## Exact repair target

Repair browser inventory/scan completeness on this same PR; retain153.0.8010.36,
its verified archiveSHA256167a098c4fdec156b58a9f678c90a84f9072d789f9c6e7b35496a6987b8b7ef8,
Playwright1.62.1, base image, dependency locks and all confinement unchanged.
Do not revert paths merely to hide the problem, mislabel a binary version,
de-rate findings or manufacture a safe scanner entry from a policy string.

Inspect `tools/supply_chain/run.sh` generate_sbom/generate_scan_sbom and the
Grype `sbom:` input, evidence.py normalize/finalize/validate_expected_components,
policy.json expected components and browser runtime facts, current SPDX/Syft
JSON/image/rootfs manifests, and the pinned Syft binary-cataloger behavior.
Identify why native cataloging omitted153, or record the exact cataloger
limitation if its internals cannot be fully determined; fix the resulting gap.

Provide a deterministic artifact-bound browser identity in BOTH the SPDX
inventory and exact SBOM supplied to Grype. Native supported cataloging is
preferred; a clearly attributed supplemental component is acceptable if bound
to the actual image executable, measured version, executable hash, source
archive hash/provenance and correct Google Chrome identifiers. Preserve truthful
license provenance; do not invent a permissive license or claim Syft discovered
an entry supplied by the project. Avoid duplicate/conflicting browser identities.

The existing pinned Grype supports SBOM/PURL/CPE inputs, documented by
[Anchore scan-target guidance](https://oss.anchore.com/docs/guides/vulnerability/scan-targets/).
Use supported formats and actual matcher evidence, not a package label that
never participates in vulnerability matching. Retain the exact scan input
hash, image identity, measured executable facts and resulting match provenance.

Fail closed when the expected browser is absent from scanner input, version/
identity is unknown, the cataloged version/hash disagrees with the actual
binary, multiple identities conflict, or coverage cannot be established.
Missing browser identity MUST NOT become a successful zero-findings release
gate. Preserve all other OS/language package coverage and six-image policy.

## Required sensitivity and qualification proof

1. Unit/integration coverage removes the Chrome entry from an otherwise valid
   bundle and proves qualification fails; mismatched version/hash/identity
   cases fail too. Verified actual153 input is accepted for scanning.
2. Run the actual pinned Grype with the same fresh database against a controlled
   known-vulnerable Chrome152.0.7977.82 SBOM/CPE input. Prove it reports relevant
   Critical findings and that the ordinary unexcepted-Critical gate rejects
   them. This is a labeled negative control, never substituted for the passing
   production input. Do not stub scanner output or hardcode an expected PASS.
3. Run the actual production image→inventory→scan pipeline for153, prove its
   Chrome component is measured/artifact-bound and included in the exact Grype
   input, and obtain zero unexcepted Critical findings for all six images.
   Retain lower-severity findings, package identities and lookup provenance.
4. Preserve failed-run diagnostics, original failure exit codes and separate
   unqualified labeling. No scanner suppression, weakened gate, stale database,
   new exception, raw credential leak or missing-evidence success.

Run focused inventory/scanner/evidence/diagnostic policy tests first. No need
to redo unchanged full local product/DB suites or reimplement the browser
upgrade; required exact-head CI supplies broad qualification. If actual153
coverage reveals a genuine remaining vulnerability, report it precisely for
the minimum further remediation; never make it disappear through cataloging.

## Truth, publication and scope

Preserve the immutable078-t report and historical qualification records.
Append/currently distinguish its incomplete Chrome-coverage claim from the
new measured qualification; update current matrix/docs and PR description
honestly. The PR body should summarize actual changes/evidence, not just paste
the work order. Verify body readback before claiming it updated.

Commit exact order and active078-u, scoped scanner/evidence/tests/current docs;
push the same PR80. No application feature, SQL, page-style/global/catalog,
MCP/media/Puck/lifecycle work, dependency upgrade, confinement expansion or new
PR. Routine safe tools/scanner/image work belongs to the existing coder's
passwordless-sudo VM. Numeric078 remains PARTIAL; page-style draft remains inert.

Publish `oap/reports/078-u-close-browser-scan-coverage-gap.md` as final report-only
SELF child of the literal pushed implementation SHA. Include exact evidence
for inventory presence, measured version/hash binding, vulnerable negative
control, fresh actual153 scan, retained failures, checks, changes/size, limits
and unchanged scope. Lint Markdown before publication. Never merge/auto-merge.
Send exact responseFIFO OK after remote publication, then wait using the real
byte-reading control listener. Strategy alone accepts/merges exact-head green.
