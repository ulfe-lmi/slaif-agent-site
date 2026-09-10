# OAP Coding-Agent Report — 078-t

## Work order

- Identifier: `078-t`
- Work-order file: `oap/orders/078-t-qualify-browser-security-update.md`
- Numeric objective: `078` (maintenance increment `078/3`)
- PR mode: `CREATED_NEW_PR`

## Status

`COMPLETE`

## Executive summary

The vulnerable Chrome for Testing `152.0.7977.82` browser payload was replaced
with the official Stable `153.0.8010.36` payload at CfT revision `1681091`.
The exact Linux amd64 archive was downloaded, hashed, extracted, and checked
with the real binary version command. The existing Playwright 1.62.1 package,
base image, sandbox, capabilities, network boundaries, credentials, artifact
contracts, and product behavior were preserved.

The fresh six-image supply-chain qualification passed with zero unexcepted
Critical findings. The failed-scan path now retains bounded raw scanner JSON
and available scan SBOMs in a separate explicitly incomplete/unqualified
diagnostic bundle, with checksums and original exit status; it does not create
a success manifest or weaken the Critical gate.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#80](https://github.com/ulfe-lmi/slaif-agent-site/pull/80), `OPEN`,
  non-draft, mergeable, `CLEAN`
- Base/head: `main` / `oap/078-3-browser-security-refresh`
- Starting remote `main` SHA:
  `a9d3e6800d5e8b5fd5c9cd9e0be5010184058c6b`
- Implementation head SHA:
  `fa2a841a5a0c7ea1610a6ecd4cc2b7b318f12242`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (to be derived and verified)
- Implementation commit pushed before report:
  `fa2a841a5a0c7ea1610a6ecd4cc2b7b318f12242`
- Report parent must equal the implementation SHA above.
- New PR this turn: yes
- Amended existing PR this turn: no
- Merge or auto-merge performed: `NO`

## Changes made

- Reverified official Chrome Stable 153.0.8010.36 metadata and the official
  Linux64 archive. Frozen archive SHA-256:
  `167a098c4fdec156b58a9f678c90a84f9072d789f9c6e7b35496a6987b8b7ef8`.
- Updated the browser-worker Dockerfile to verify that archive and version,
  and installed it under `/ms-playwright/chromium-1681091` so the CfT revision
  is not confused with a Playwright bundle revision.
- Updated machine policy, runtime assertions, smoke assertions, supply-chain
  evidence boundaries, qualification matrix, and current configuration,
  deployment, license, security, README, increment, and MVP audit docs.
- Preserved the historical 152.0.7977.82 and earlier qualification records;
  the current qualification matrix records the new runtime, archive and
  executable hashes, image/SBOM/scan identities, scanner database, and counts.
- Added a bounded `failure-diagnostics` collector and CI upload path. Failure
  diagnostics are safety-filtered, checksummed, marked `INCOMPLETE` and
  `UNQUALIFIED`, retain the original exit status, and contain no `index.json`
  or `SUMMARY.txt`. Normal evidence remains success-only.
- No application SQL, content-model behavior, production dependency, lockfile,
  Playwright package/base version, exception, scanner threshold, or security
  boundary was changed.

## Files changed

- `.github/workflows/ci.yml`
- `README.md`
- `docs/CONFIGURATION.md`
- `docs/DEPLOYMENT.md`
- `docs/LICENSE_POLICY.md`
- `docs/SECURITY.md`
- `docs/SUPPLY_CHAIN.md`
- `oap/INCREMENTS.md`
- `oap/MVP-CONTRACT-AUDIT.md`
- `oap/MVP-PROGRESS.md`
- `oap/active`
- `oap/audits/078-2-strategic-acceptance.md`
- `oap/orders/078-t-qualify-browser-security-update.md`
- `services/browser-worker/Dockerfile`
- `supply-chain/browser-worker-critical-matrix.json`
- `supply-chain/policy.json`
- `tests/packaging/test_oci_contract.py`
- `tests/supply_chain/test_evidence.py`
- `tests/supply_chain/test_failure_diagnostics.py`
- `tests/supply_chain/test_policy.py`
- `tools/check_repository.py`
- `tools/compose/smoke.sh`
- `tools/supply_chain/evidence.py`
- `tools/supply_chain/failure_diagnostics.py`
- `tools/supply_chain/policy.py`
- `tools/supply_chain/run.sh`

Implementation commit size: 26 files, 601 insertions, 72 deletions.

## Acceptance-criteria evidence

### Browser source and runtime qualification

- Official sources reverified: [Chrome Stable channel release](https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0808145027.html),
  [CfT Stable metadata](https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json),
  and the [official Linux64 archive](https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.36/linux64/chrome-linux64.zip).
- Extracted archive reported `Google Chrome for Testing 153.0.8010.36` followed
  by the command's trailing space.
- The real image executable reported the same version at
  `/ms-playwright/chromium-1681091/chrome-linux64/chrome`.
- Qualified executable SHA-256 in the reproducible image manifest:
  `79a4ebf6da53e4ceab11844257aabc5166f17b595dc694d6382cbee8ff50565f`.
- Browser-worker image identity from the completed local six-image run:
  `sha256:d9d8c94e446fe60594f5de1b4f4461503145cdac48c907974789a2cee8f4abb8`.
- The exact Playwright base remained
  `mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e`;
  `playwright-core` remained `1.62.1` and Node remained `24.18.1`.
- The image launched a real Playwright page as UID 10001 with read-only root,
  all capabilities dropped except `SYS_CHROOT`, no-new-privileges, no network,
  bounded tmpfs/shm/PIDs/memory/CPU, and sandbox enabled.

### Security, preview, artifacts, and confinement

- The clean Compose smoke passed the exact UID, read-only root, capability,
  seccomp, resource, browser-only network, one-payload-directory,
  Chromium-only, no-package-manager and 153-version assertions.
- Same-workspace public Agent component and theme preview passed through
  NGINX with real browser observation, canonical independence, sensitive
  wrong-theme control, restart/recovery, cancellation, artifact privacy,
  quota, foreign-capability, credential, and outage negatives.
- Compose reported `compose-e2e: OK projects=11`, including setup, governance,
  preview, six stable device projects, and two Agent session projects.
- Artifact, browser-worker, Render/signing-secret, database-login, edge-header,
  body-limit, readiness, restart, outage, cleanup, and negative-bootstrap
  checks all passed; no production browser artifacts or credentials were
  exposed.

### Supply-chain evidence and failed-run retention

- Completed local `tools/supply_chain/run.sh` qualification: 6 images, fresh
  Grype `0.117.0` / Syft `1.51.0`, database schema `v6.1.9`, database built
  `2026-09-10T06:30:24Z`, database checksum
  `sha256:ce7ae6d4f7fb81029fc3bd1891b6b441f96bac4e278519743e4768eebd805e69`,
  zero Critical, 43 High review findings, and bundle checksum `OK`.
- Browser-worker scan: 1,436 matches; 0 Critical, 2 High, 1,328 Medium,
  92 Low, and 14 Negligible; zero unexcepted Critical and zero exceptions.
- Browser-worker normalized SBOM SHA-256:
  `43750485ca35cca8e904e2b76f09510c9a1b8ffaa4809532cea5a140d28c350b`.
  Scan SBOM SHA-256:
  `6ee948cb78e177c675d4ed4b69c614f70c31210ec79761d5d0d3ad6037724630`.
  Normalized scan SHA-256:
  `ad48ab16a2828e7c4c28e2a5f49df2a5926839dcec12afeb131818371cf9d5e1`.
- Two clean browser-worker builds had equal normalized package manifests and
  application files; the expected OCI image IDs differed only at the documented
  Docker/OCI timestamp boundary.
- Controlled runner failure retained the original exit status `127` and
  produced a checksummed diagnostic directory with `STATUS.json` marked
  `INCOMPLETE`/`UNQUALIFIED`, no success manifest, and no unsafe content.
  The dedicated retention unit test also proves raw safe output is retained
  and secret-marked output is filtered.
- CI normal evidence upload passed; the failure-diagnostics upload was
  correctly skipped on the successful run.

## Local verification

- `uv lock --check`: PASSED
- `uv sync --frozen --all-groups`: PASSED
- `uv run --frozen ruff check services/backend tests/repository tests/packaging tests/supply_chain tools migrations`: PASSED
- `uv run --frozen ruff format --check services/backend tests/repository tests/packaging tests/supply_chain tools migrations`: PASSED — 305 files formatted
- `uv run --frozen mypy`: PASSED — 271 source files
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED — 540 passed, one unrelated Starlette/httpx deprecation warning
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 215 passed in 2080.50 seconds
- `uv build --out-dir /tmp/slaif-agent-site-distributions-078t`: PASSED
- `python -m compileall -q tools tests/repository tests/packaging tests/supply_chain`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 58 tests
- `python tools/check_repository.py`: PASSED
- `python tools/check_mermaid.py`: PASSED — 16 diagrams, 466 Markdown files
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 0 issues in 460 files
- The ten exact `uv run --frozen python -m slaif_agent_site.* --check` commands for `control_api`, `editor_api`, `agent_api`, `render_api`, `mcp_adapter`, `media_service`, `review_worker`, `scheduler`, `media_gc`, and `bootstrap`: PASSED — 10/10 `CHECK_OK`
- `pnpm install --frozen-lockfile`: PASSED
- `pnpm lint`: PASSED
- `pnpm format:check`: PASSED
- `pnpm typecheck`: PASSED
- `pnpm test`: PASSED
- `pnpm build`: PASSED
- `pnpm licenses list --json`: PASSED
- `pnpm --filter @slaif-agent-site/browser-worker test`: PASSED — 10 tests
- Browser-related backend unit tests: PASSED — 44 tests
- Focused browser integration tests: PASSED — 6 tests in 63.50 seconds
- Focused packaging/supply-chain tests: PASSED — 38 tests
- `python tools/compose/verify.py --root .`: PASSED
- `sudo sh tools/compose/smoke.sh slaif007t`: PASSED — complete clean Compose,
  six stable device projects, same-workspace Agent theme/component preview,
  artifact, recovery, edge, and security proof
- `sudo docker build --pull --no-cache ... services/browser-worker/Dockerfile`: PASSED — real 153 binary launch and Playwright compatibility
- `sh -n tools/supply_chain/run.sh`: PASSED
- Controlled failure proof with missing `uv`: PASSED — original status and
  incomplete diagnostic retention verified
- An initial plain-system-Python process-smoke attempt failed before execution
  because that interpreter did not contain the project package; the mandated
  frozen-uv command above passed all ten checks.

## GitHub CI / required checks

State observed for implementation head
`fa2a841a5a0c7ea1610a6ecd4cc2b7b318f12242` before report publication:

- CI run [34459296125](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34459296125):
  `SUCCESS`
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
- CodeQL run [34459296133](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34459296133):
  `SUCCESS`
  - Detect supported languages: `SUCCESS`
  - Analyze (actions): `SUCCESS`
  - Analyze (python): `SUCCESS`
  - Analyze (javascript-typescript): `SUCCESS`
  - CodeQL: `SUCCESS`
- All required checks for the implementation head were green at drafting: yes.
- Report-only commit may trigger fresh checks; strategy must independently
  verify the report `SELF` head and its checks.

## Local setup / dependencies

- Used the existing frozen uv `0.12.5`, Node `24.14.1`, pnpm `11.22.0`, and
  TypeScript `6.0.3` environments.
- Used passwordless sudo for Docker, browser dependencies, disposable Compose,
  and local PostgreSQL-backed integration tests; no human setup was required.
- Downloaded only the official public CfT archive; the archive was not copied
  into the repository or image as a moving/runtime download.
- No production dependency, hosted service, lockfile, credential, or
  infrastructure requirement was added.

## Documentation

Updated current increment/MVP audit, configuration, deployment, license,
security, supply-chain, and README records. The docs distinguish the accepted
and merged PR #79 theme increment from the post-merge 152 security regression,
the active 153 maintenance qualification, historical qualification evidence,
and the unchanged contractual MVP `PARTIAL` state.

## Safety and scope confirmations

- Unrelated files changed: `NO`; all 26 files are direct browser pin,
  supply-chain evidence, test, workflow, transcript, or current-doc scope.
- Production secrets accessed: `NO`.
- Production systems accessed: `NO`.
- Required tests skipped/not run: `NO` for the ordered local and remote sets.
- Scope deviation: `NO`; no product feature, SQL, content-model, dependency,
  exception, threshold, or confinement expansion.
- Extra objective PR: `NO`; PR #80 is the sole new Objective-078/3 PR.
- Coding-agent merge: `NO`.
- Activated order/active edited: `NO`; exact bytes were committed unchanged.
- Supplied strategic audit edited: `NO`; exact bytes were committed unchanged.
- Report commit changes only this report: `YES`.

## Known limitations / blockers

- PR #80 remains open pending strategy’s independent review and merge; coding
  did not merge it.
- The report-head checks after the report-only commit are not claimed here;
  strategy verifies them independently as required by OAP.
- Objective 078 and the contractual MVP remain `PARTIAL`; this maintenance
  round qualifies the browser security update and does not complete deferred
  global-region, page-style, catalog, review, promotion, publication, MCP,
  Puck, or operational objectives.
- Grype still reports High and lower findings as visible review evidence; the
  gate passed because unexcepted Critical findings are zero, not because the
  image is vulnerability-free.

## Recommended strategic follow-up

Review the exact PR #80 diff, implementation parent, report `SELF` child,
post-report checks, and the unchanged acceptance boundaries. If all required
report-head checks remain green and the strategic review is satisfied, strategy
may merge PR #80; only then may a later bounded 078 continuation be selected.
