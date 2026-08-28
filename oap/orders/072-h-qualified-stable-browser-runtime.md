# OAP Work Order — 072-h

## Objective

Continue Objective 072 on PR #66. Resolve the remaining browser-image Critical
vulnerability gate by selecting and fully qualifying an official stable,
glibc-based Chromium runtime. First classify the scanner findings precisely;
then evaluate no more than two evidence-selected candidates. Preserve all 072-f
worker behavior and confinement. Do not implement dispatch or other features.
Do not merge.

## Verified state and strategic correction

- Mode: `AMEND_EXISTING_PR`; amend only PR #66, branch
  `oap/072-browser-worker-real-playwright`; create no PR.
- Begin from remote 072-g report head
  `63ea4df47edd2098b6ef8c4cf40ad24711c326e9`; its sole parent is
  `6c1d4de200604a8595c94f86c6aaf23e1bc8b661`, and it changes only
  `oap/reports/072-g-browser-runtime-supply-chain-closure.md`.
- Remote main is `082f2359b0c4d59b692580d17992c35d46183b12`.
  PR #66 is open, non-draft, mergeable, and `UNSTABLE`; all current checks pass
  except `Supply-chain evidence`, which rejects the same 27 Critical IDs listed
  in 072-g. No reproducibility mismatch recurred; the safe diagnostic remains.
- Official npm still identifies Playwright `1.62.1` as current stable. Do not
  invent a Playwright version.
- Independent strategic verification of Google's live official
  `last-known-good-versions-with-downloads.json` shows stable Chrome for Testing
  `152.0.7977.64`, revision `1669021`, timestamp
  `2026-08-27T22:25:50.454Z`. The branch remains on `151.0.7922.72`.
  The scanner advertises some fixes at `151.0.7922.173` or `152.0.7977.65`,
  neither currently present in that stable channel. The untested `.64` stable
  runtime may reduce but might not eliminate findings; determine this with
  evidence, not assumptions.

## Requirements

1. Capture a bounded machine-readable scanner matrix for the browser-worker:
   each Critical ID, matched package/artifact and installed version, ecosystem/
   distro namespace, fixed version, match type/location, and whether the finding
   belongs to Chrome/Chromium bytes or base OS libraries. Add a secret-safe CI
   summary/artifact sufficient to diagnose future failures; do not print file
   contents, credentials, or absolute private paths.
2. Before building, use only official stable upstream metadata, exact artifact
   availability/hashes, current scanner fixed-version data, and official distro
   security/package metadata to choose candidates. At most two candidates may
   receive complete image scans:
   - first preference: official stable CfT `152.0.7977.64` on a compatible,
     fully security-updated, immutable-digest glibc base; or
   - if evidence predicts/observes unresolved findings, an official stable
     glibc distribution Chromium package/runtime with exact immutable repository
     snapshot/version/hashes and a smaller auditable dependency surface.
   Do not use Beta/Dev/Canary, nightly/snapshot, mutable `latest`, musl, hosted
   browser service, or an unverified download.
3. Keep `@playwright/test` and `playwright-core` at exact stable-compatible
   versions; align them only if an official stable Playwright release actually
   appears during the turn. Update image digest, browser version/revision/URL/
   SHA/executable, lock/policy/SBOM/inventory/notices/docs and exact tests
   together. Explain every source and lock delta.
4. A candidate is acceptable only if the unmodified current Grype database
   reports zero unexcepted Critical findings for every image and the existing
   supply-chain/reproducibility/license policies pass. No exception, ignore,
   severity change, database pin/rollback, package hiding, SBOM/image omission,
   threshold weakening, or `continue-on-error`.
5. The accepted candidate must pass the real production-image sandbox launch,
   exact fixed target mapping, direct Web/Render COW preview, PNG and curated
   evidence, hostile URL/network denial, no credential leakage, two-run cleanup,
   cancellation/failure, restart-safe private artifact retrieval, resource and
   Compose confinement, public runs still `QUEUED`, worker/unit/contracts,
   Node/packaging/repository policy, and one clean nine-project Compose run.
6. Run one final complete local supply-chain execution for the selected
   candidate and wait for all fresh GitHub checks. Use targeted candidate scans
   before that. Do not launch repeated unchanged broad runs. If neither of the
   two evidence-selected official stable candidates can meet the zero-Critical
   gate, leave the branch in the safest coherent state (do not retain a failed
   experiment), publish the exact candidate/finding matrix, and report
   `BLOCKED` without a third candidate.

## Scope and non-goals

Limit changes to browser base/runtime and pins, scanner diagnostics/evidence,
locks/policy/inventory/notices/docs, and directly affected tests. Preserve
migrations 035/036, DB roles/functions/grants, capability/preview-token/COW/
Render semantics, fixed origin/default-deny network, sandbox/non-root/read-only/
capability/resource boundaries, credential isolation, immutable private
artifacts, and public queued-run behavior.

Do not add dispatcher/leases/durable completion/artifact registration/public
bytes/GC/source crawling/six-target product sweep/review/promotion/publication,
unrelated dependencies, telemetry, another PR, merge, auto-merge, or release.

## Workflow and report

Commit/push the unchanged 072-h order and `oap/active`, then the bounded repair.
Publish exactly `oap/reports/072-h-qualified-stable-browser-runtime.md` as a
report-only child with literal implementation-parent SHA and
`Report publication commit: SELF`; signal exact FIFO `OK`; do not merge.

Report the complete Critical finding matrix; candidate decision and both
candidate results if two were needed; exact old/new browser, base, packages,
versions, revisions, URLs, hashes, Playwright/Node/platform/seccomp facts;
scanner DB/result and proof of no weakening; runtime/confinement/Compose/public-
queue evidence; commands, retries, skips, files, locks/docs, every current CI
check, PR/base/branch/all SHAs, no extra PR, and no merge. Objective 072 remains
`PARTIAL` even if this runtime slice succeeds because durable dispatch/public
retrieval remain pending.
