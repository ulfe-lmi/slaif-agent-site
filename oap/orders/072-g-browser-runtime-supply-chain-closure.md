# OAP Work Order — 072-g

## Objective

Continue Objective 072 on PR #66. Repair the two independently verified
supply-chain blockers in the 072-f browser-worker implementation: nondeterministic
Web/browser build output and Critical vulnerabilities in the pinned browser
runtime. Preserve the real confined worker and all 072-f trust boundaries. Do
not add dispatch, database completion, public artifact retrieval, source tools,
or any other product behavior. Do not merge.

## Verified current state

- Numeric objective: `072`; round: `072-g`; mode: `AMEND_EXISTING_PR`.
- Amend only PR #66 on `oap/072-browser-worker-real-playwright`; create no PR.
- Remote main remains
  `082f2359b0c4d59b692580d17992c35d46183b12`.
- Begin from remote report head
  `bc7a79b9b9f9a3893e05d3f4464387721ce59ea7`. It changes only
  `oap/reports/072-f-real-playwright-worker-private-artifacts.md`; its sole
  parent is implementation head
  `b946d266bf59c9c74893d2a8a17e7893950eccc1`.
- PR #66 is open, non-draft, mergeable, and `UNSTABLE`. Every current-head
  required check is green except `Supply-chain evidence`.
- Final-head CI run `33130838123`, job `98719719107`, fails before scanning with
  `reproducibility: ERROR: Web/browser normalized output manifests differ`.
- Implementation-head CI run `33128732237`, job `98712983967`, reached scanning
  and rejected 27 unexcepted Critical findings in the browser-worker image:
  `CVE-2026-19149`, `CVE-2026-19157`, `CVE-2026-19164`, `CVE-2026-19166`,
  `CVE-2026-19170`, `CVE-2026-19175`, `CVE-2026-76035`, `CVE-2026-76036`,
  `CVE-2026-78909`, `CVE-2026-78935`, `CVE-2026-78937`, `CVE-2026-78939`,
  `CVE-2026-78945`, `CVE-2026-78948`, `CVE-2026-78951`, `CVE-2026-78964`,
  `CVE-2026-79012`, `CVE-2026-79026`, `CVE-2026-79043`, `CVE-2026-79047`,
  `CVE-2026-79052`, `CVE-2026-79056`, `CVE-2026-79064`, `CVE-2026-79078`,
  `CVE-2026-79091`, `CVE-2026-79111`, and `CVE-2026-79189`.
- The 072-f clean Compose job passed the real sandboxed worker, COW preview,
  hostile probes, artifact persistence/restart, public queued-run separation,
  nine existing Playwright projects, and packaging/runtime policy. Preserve
  that evidence; do not redesign the worker while repairing its runtime.

## Bounded requirements

### 1. Diagnose and remove nondeterminism

- Reproduce the manifest mismatch from the exact current head. Make the
  reproducibility harness report a bounded, secret-safe list of the first
  differing normalized paths and their hashes when outputs differ, so the
  failure is actionable without dumping file contents or credentials.
- Identify the actual volatile build output or uncontrolled input. Fix the
  build or normalize only metadata proven semantically irrelevant. Never
  exclude executable assets, dependency/browser files, configuration, source
  maps used for release evidence, or arbitrary mismatches merely to make the
  comparison green.
- Prove two independent clean invocations of the complete reproducibility
  check, each of which performs its required paired builds, produce identical
  normalized Web and browser-worker manifests.

### 2. Replace vulnerable pins with qualified fixed runtime

- Before rebuilding, use current official upstream release/security metadata
  and the scanner's fixed-version data to select the smallest practical stable
  upgrade that resolves all listed Critical findings. Do not guess versions.
- Keep exact immutable pins and hashes. Upgrade the Playwright package/test
  version, product `playwright-core`, compatible Ubuntu Playwright base image
  digest, Chrome/Chromium artifact version/revision/URL/SHA/executable mapping,
  target descriptors, seccomp provenance, lockfile, inventory, SBOM policy,
  notices, and documentation together wherever compatibility requires it.
- Retain Node 24, Linux/amd64 qualification, Chromium-only product runtime,
  sandbox enabled, non-root/read-only/dropped-capability confinement, fixed
  origin/default-deny networking, credential isolation, and immutable private
  artifact behavior. Do not add Firefox/WebKit product binaries.
- Run the unmodified current scanner database and require zero unexcepted
  Critical findings for every image. No CVE exception/allowlist, severity
  downgrade, scanner/database pin or rollback, package hiding, SBOM omission,
  image exclusion, threshold weakening, or `continue-on-error` is permitted.

### 3. Verification and retry discipline

- Use focused diagnostics and targeted unit/image checks between expensive
  runs. Perform at most two new complete local supply-chain executions: one
  diagnostic/qualification run and one final clean confirmation. If the second
  still fails for a materially new reason, stop and report it rather than
  launching another broad retry loop.
- Run the affected Node contracts, worker unit/contract/artifact tests,
  repository/packaging/license policy, exact production-image sandbox launch,
  direct real Web/Render COW preview, hostile-network probes, cleanup/restart,
  and public-runs-still-queued checks.
- Run one clean Compose regression including the existing nine Playwright
  projects after the final pins are selected. Do not rerun an unchanged failed
  job as a substitute for a code fix; one unchanged retry is allowed only for
  a clearly evidenced infrastructure flake.
- Push the repair and allow every fresh required GitHub check to finish. All
  checks, including `Supply-chain evidence`, must be present and successful;
  report failures, skips, retries, and not-run work literally.

## Scope and non-goals

Limit changes to browser/runtime pins and image, reproducibility diagnostics and
normalization, directly affected locks/policy/inventory/notices/docs, and focused
tests. Do not change migrations 035/036, database roles/functions/grants,
capability or preview-token semantics, COW/render behavior, public Agent route
state, Media, Puck, review, promotion, publication, or unrelated dependencies.

Do not implement the queued-run dispatcher, leases, durable completion/artifact
registration, public artifact bytes, GC, source crawling, six-target product
sweep, or review integration. Public Agent runs must remain `QUEUED`. No hosted
service, telemetry, second PR, merge, auto-merge, or release action.

## Workflow and report

Fetch/reconcile GitHub, require the named open PR and exact starting head, and
amend only its branch. Commit/push the unchanged strategic 072-g order and
`oap/active`, then the bounded repair/tests/docs. Publish exactly
`oap/reports/072-g-browser-runtime-supply-chain-closure.md` as a report-only
child with `Report publication commit: SELF` and the literal 40-hex
implementation parent; signal exact FIFO `OK`; do not merge.

The report must state the root cause and exact differing paths/hashes for the
reproducibility failure; old/new package, browser, revision, URL, SHA, base-image
digest, seccomp, Node/platform facts; official/fixed-version selection evidence;
scanner database/result and confirmation that no exception/gate weakening was
used; sandbox/network/credential/artifact/public-queue invariants; exact local
commands/results and expensive-run count; all current CI checks; changed files
and lock deltas; PR/base/branch/all SHAs; no extra PR; and no merge. Objective
072 remains `PARTIAL` even if this repair slice is complete because durable
dispatch and public retrieval are still intentionally pending.
