# OAP Coding-Agent Report — 078-u

## Work order

- Identifier: `078-u`
- Work-order file: `oap/orders/078-u-close-browser-scan-coverage-gap.md`
- Numeric objective: `078`; maintenance increment `078/3`
- PR mode: `AMENDED_EXISTING_PR`
- Existing PR: [#80](https://github.com/ulfe-lmi/slaif-agent-site/pull/80)

## Status

`COMPLETE`

## Executive summary

The 078-t report's apparent zero-Critical result was correctly found to be
unqualified: Syft 1.51.0 emitted no Chrome artifact for the 153 executable in
the exact SBOM supplied to Grype. This continuation repaired that gap on the
same PR. The production image now measures the real executable and adds one
explicitly attributed Chrome component to both the retained SPDX inventory and
the exact Syft JSON consumed by Grype.

The component is bound to the real image ID, executable path, measured version,
executable SHA-256, official CfT archive URL/SHA-256, and both Google Chrome
CPEs. Finalization and bundle validation fail closed for missing, duplicate,
conflicting, or mismatched browser identity. The fresh actual six-image scan
passed with zero unexcepted Critical findings. The Playwright 1.62.1
base/package and all browser confinement remain unchanged.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#80](https://github.com/ulfe-lmi/slaif-agent-site/pull/80), `OPEN`,
  non-draft, mergeable, clean
- Base/head: `main` /
  `oap/078-3-browser-security-refresh`
- Verified base `main` SHA:
  `a9d3e6800d5e8b5fd5c9cd9e0be5010184058c6b`
- Starting report-only head:
  `51affbe941bb26d397e0a9a6e1f7b7612c5f383f`
- Starting implementation parent:
  `fa2a841a5a0c7ea1610a6ecd4cc2b7b318f12242`
- Implementation commits pushed this round:
  `6eaa29fad674b6988361be04976df5d9d365cd9a`,
  `07416579e0f6b431e0cc09cf7df2c3c367b57f3d`
- Implementation head SHA:
  `07416579e0f6b431e0cc09cf7df2c3c367b57f3d`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (to be derived and verified)
- New PR this round: no
- Amended existing PR this round: yes, PR #80 only
- Merge or auto-merge performed: `NO`

The PR description was updated through the REST API after the GitHub CLI
GraphQL edit encountered the repository's deprecated classic-project field.
The REST body was read back and contains the actual 078-u repair summary and
evidence, not the work-order text.

## Changes made

- Inspected the pinned Syft output and confirmed its native binary catalogers
  recorded the Chrome 153 file as an unowned ELF without a Chrome artifact;
  Chrome 152 was natively identified, so the limitation is version-specific in
  the pinned cataloger behavior.
- Added a measured-runtime identity command and runner step. Each clean
  browser-worker build executes the image's configured `chrome --version` and
  hashes the configured executable; both reproducible builds must agree on all
  non-image-ID identity fields.
- Added one supplemental Chrome binary artifact to the Syft scan SBOM and one
  SPDX package linked to the existing executable file. The package uses PURL
  `pkg:generic/chrome@153.0.8010.36` and the exact Google Chrome CPEs, with
  `NOASSERTION` license values and explicit supplemental provenance.
- Added exact fail-closed validation for both SBOM forms, image binding,
  executable SHA-256, version, source archive, path, CPE/PURL identity,
  package/file relationships, and index identity.
- Added `chrome` to the browser-worker expected SBOM components and changed the
  summary from the hardcoded empty-browser claim to measured-and-scan-bound.
- Changed the qualification matrix to retain 078-t as
  `INCOMPLETE`/`UNQUALIFIED` and record the measured 078-u qualification as the
  passing candidate with remote image/SBOM/scan identities.
- Preserved the existing failed-run diagnostic collector, original exit-code
  handling, 153 pin, Playwright base/package, exceptions, thresholds,
  confinement, and all product behavior.

## Files changed

- `README.md`
- `docs/SUPPLY_CHAIN.md`
- `oap/INCREMENTS.md`
- `oap/MVP-CONTRACT-AUDIT.md`
- `oap/MVP-PROGRESS.md`
- `oap/active`
- `oap/orders/078-u-close-browser-scan-coverage-gap.md`
- `supply-chain/browser-worker-critical-matrix.json`
- `supply-chain/policy.json`
- `tests/supply_chain/test_evidence.py`
- `tests/supply_chain/test_policy.py`
- `tools/supply_chain/evidence.py`
- `tools/supply_chain/run.sh`

Implementation diff from the starting u head: 13 files, 965 insertions, 77
deletions. The prior `oap/reports/078-t-qualify-browser-security-update.md`
was not edited.

## Acceptance-criteria evidence

### Browser inventory and provenance

- Official references: [Chrome Stable release](https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0808145027.html),
  [CfT Stable metadata](https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json),
  and the [official Linux64 archive](https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.36/linux64/chrome-linux64.zip).
- Exact archive SHA-256:
  `167a098c4fdec156b58a9f678c90a84f9072d789f9c6e7b35496a6987b8b7ef8`.
- Measured image executable:
  `/ms-playwright/chromium-1681091/chrome-linux64/chrome`.
- Measured version: `Google Chrome for Testing 153.0.8010.36`.
- Executable SHA-256:
  `79a4ebf6da53e4ceab11844257aabc5166f17b595dc694d6382cbee8ff50565f`.
- Exact base remains
  `mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e`;
  `playwright-core` remains `1.62.1`.
- Remote final CI artifact contains exactly one `chrome` artifact in the
  Grype-input SBOM, `foundBy=supplemental-measured-runtime`, the measured path,
  both CPEs, the exact PURL, archive provenance, and executable SHA-256.

### Fail-closed sensitivity

- Missing Chrome from an otherwise valid bundle fails before qualification with
  the expected SBOM-component/coverage error.
- Mismatched executable hash and measured version fail closed in focused tests.
  A native or duplicate browser identity also fails rather than being merged.
- The actual pinned Grype `0.117.0` with the fresh v6.1.9 database scanned the
  controlled known-vulnerable Chrome `152.0.7977.82` SBOM and returned 1,566
  matches, including all 26 expected Critical IDs, all against
  `pkg:generic/chrome@152.0.7977.82`. The ordinary `finalize_bundle` gate
  rejected that bundle with the listed unexcepted-Critical error.
- The actual 153 production image pipeline supplied the supplemental component
  to Grype and returned 1,436 matches with zero Critical findings. No scan
  output was stubbed and no expected result was hardcoded into the gate.

### Production qualification

- Local updated runner: six reproducible image pairs, Grype `0.117.0`, Syft
  `1.51.0`, database v6.1.9 built `2026-09-10T06:30:24Z`, database checksum
  `sha256:ce7ae6d4f7fb81029fc3bd1891b6b441f96bac4e278519743e4768eebd805e69`,
  zero Critical, 43 High review findings, and checksum validation passed.
- Local browser-worker scan: 1,436 matches; 0 Critical, 2 High, 1,328 Medium,
  92 Low, 14 Negligible.
- Remote final CI browser-worker image:
  `sha256:76a6af77bb0eb1dce3d18368ca5f008c3c963a4daf865351d32dc6c08e484132`.
  Remote final artifact:
  `supply-chain-evidence-f8a4e3edf36daaee357a5511b872d6f59c0668f8`.
- Remote final normalized SPDX SHA-256:
  `19aed3549217a554b5c1bf74c7ee8635c99cc44e9bc3c36aca00d0382c66857a`.
- Remote final Grype-input SBOM SHA-256:
  `6ddf7a3735628fcb4093ccf19d8b5d6c9de49f21654fef581d9e824bb69c26aa`.
- Remote final normalized scan SHA-256:
  `71891e3a80bb07c0f0be648bc69eee774c9a228e251e4a98da7196d5679a8eb4`.
- Remote final `validate-bundle` passed. The current matrix also retains the
  earlier same-code successful remote qualification run `34467063708` and its
  measured identities; the final run `34468435175` independently revalidated
  the same pipeline after matrix reconciliation.

### Existing security boundaries

- The browser-worker image and final Compose CI proof retain UID 10001,
  read-only root, dropped capabilities plus only `SYS_CHROOT`, exact seccomp,
  no-new-privileges, browser-only network membership, bounded resources,
  Chromium-only product payload, no database/host/Docker mounts, separate
  credentials, private immutable artifacts, quotas, and no runtime downloader
  or package manager.
- The existing failed-run collector remains separately labeled,
  checksummed, bounded, safety-filtered, and unable to create a success
  manifest. The prior t report and historical qualification records remain
  immutable.

## Local verification

- `python -m unittest tests.supply_chain.test_evidence tests.supply_chain.test_policy tests.supply_chain.test_failure_diagnostics tests.packaging.test_oci_contract`: PASSED — 37 tests
- `uv run --frozen ruff check ...` on changed Python/test tooling: PASSED
- `uv run --frozen ruff format --check ...` on changed Python/test tooling: PASSED
- `python tools/check_repository.py`: PASSED
- `python tools/compose/verify.py --root .`: PASSED
- `python -m tools.supply_chain.policy validate`: PASSED
- `sh -n tools/supply_chain/run.sh`: PASSED
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues in 462 files
- `sh tools/supply_chain/run.sh /tmp/slaif-078u-supply-chain-evidence-run3`: PASSED — six images, measured browser identity, zero Critical, bundle checksum OK
- `python -m tools.supply_chain.evidence validate-bundle --evidence /tmp/slaif-078u-supply-chain-evidence-run3`: PASSED as part of the runner
- Actual pinned Grype positive/negative controls described above: PASSED
  positive qualification and PASSED expected rejection of the vulnerable
  negative control
- Unchanged full local product/DB suites were not rerun, as 078-u explicitly
  delegates broad qualification to exact-head CI; the remote full matrix below
  passed.

## GitHub CI / required checks

State observed for implementation head
`07416579e0f6b431e0cc09cf7df2c3c367b57f3d`:

- CI run [34468435175](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34468435175): `SUCCESS`
  - Repository policy: `SUCCESS`
  - Node contracts: `SUCCESS`
  - Python 3.12 quality and package: `SUCCESS`
  - Python 3.13 quality and package: `SUCCESS`
  - Python 3.14 quality and package: `SUCCESS`
  - Foundation PostgreSQL 14: `SUCCESS`
  - Foundation PostgreSQL 15: `SUCCESS`
  - Foundation PostgreSQL 16: `SUCCESS`
  - Foundation PostgreSQL 17: `SUCCESS`
  - Foundation PostgreSQL 18: `SUCCESS`
  - Compose and edge packaging: `SUCCESS`
  - Supply-chain evidence: `SUCCESS`
  - Markdown: `SUCCESS`
  - Mermaid: `SUCCESS`
  - Dependency review: `SUCCESS`
- CodeQL run [34468435148](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34468435148): `SUCCESS`
  - Detect supported languages: `SUCCESS`
  - Analyze (actions): `SUCCESS`
  - Analyze (python): `SUCCESS`
  - Analyze (javascript-typescript): `SUCCESS`
  - CodeQL: `SUCCESS`
- All required implementation-head checks were green at drafting: yes.
- Report-only publication may trigger a new check set; those report-head checks
  are not claimed until independently verified by strategy.

## Local setup / dependencies

- Used the existing frozen uv `0.12.5`, Node `24.14.1`, pnpm `11.22.0`, and
  TypeScript `6.0.3` environment.
- Used passwordless sudo only for routine Docker/browser/scanner work and
  disposable local test resources. No production system or credential was
  accessed.
- No dependency lockfile, production dependency, hosted service, exception,
  scanner suppression, or infrastructure requirement was added.

## Documentation

Updated current README, supply-chain, increment, MVP audit/progress, policy,
and qualification records. Documentation distinguishes the unqualified t
attempt from the measured u qualification and retains the contractual MVP and
Objective 078 `PARTIAL` status.

## Safety and scope confirmations

- Unrelated files changed: `NO`; all 13 files are directly scoped scanner,
  evidence, policy, current-doc, test, or transcript files.
- Production secrets accessed: `NO`.
- Production systems accessed: `NO`.
- Required ordered tests/checks skipped: `NO`; unchanged broad local suites
  were expressly not required by 078-u and remote CI supplied them.
- Scope deviation: `NO`; no application feature, SQL, content-model,
  page-style, global/catalog, MCP/media/Puck/lifecycle, dependency, or
  confinement work was added.
- Extra objective PR: `NO`; PR #80 is the sole Objective-078/3 PR.
- Coding-agent merge: `NO`.
- Activated `078-u` order and `oap/active` edited: `NO`; exact bytes were
  committed unchanged.
- Prior 078-t report/historical orders edited: `NO`.
- Report commit changes only the new u report: `YES`.

## Known limitations / blockers

- PR #80 remains open pending strategy's independent review and merge.
- This report's post-publication `SELF` checks are not claimed here; strategy
  must verify them.
- Objective 078 and the contractual MVP remain `PARTIAL`. This round closes
  browser scan completeness only and does not complete deferred product or
  operational objectives.
- High and lower findings remain visible review evidence; zero Critical does
  not mean vulnerability-free.

## Recommended strategic follow-up

Verify the report-only `SELF` parent/head and its checks. If they remain green
and the strategic review accepts the measured inventory, negative control,
remote qualification, and unchanged scope, strategy may merge PR #80. The
coding agent did not merge it.
