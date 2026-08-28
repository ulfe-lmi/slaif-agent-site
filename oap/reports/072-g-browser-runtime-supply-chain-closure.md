# OAP implementation report — 072-g

ID: `072-g`

Order: `oap/orders/072-g-browser-runtime-supply-chain-closure.md`

Result: `BLOCKED`

PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66)

PR mode: `AMENDED_EXISTING_PR`

Repository: `ulfe-lmi/slaif-agent-site`

Base: `main` (`082f2359b0c4d59b692580d17992c35d46183b12`)

Head branch: `oap/072-browser-worker-real-playwright`

072-f report head: `bc7a79b9b9f9a3893e05d3f4464387721ce59ea7`

Implementation commit: `6c1d4de200604a8595c94f86c6aaf23e1bc8b661`

Report publication commit: SELF

## Work performed

- Added `describe_manifest_difference`, a bounded reproducibility diagnostic
  that reports only section, normalized path, type, mode, size, symlink target,
  normalized metadata, and SHA-256 fingerprints for the first mismatch. It
  never prints artifact contents, credentials, or source payloads.
- Added a regression test proving the diagnostic is hash/path-only.
- Ran one complete reproducibility diagnostic (both Python builds and both
  complete Node/workspace builds). It passed; no differing path or hash could
  be collected. The earlier 072-f CI mismatch (`Web/browser normalized output
  manifests differ`) therefore did not reproduce under the exact current
  head. The diagnostic is now in place to expose the first concrete path/hash
  if it recurs, rather than hiding an executable or dependency mismatch.
- Reconciled official upstream metadata before any upgrade: npm reports
  `playwright-core` and `@playwright/test` `1.62.1` as the current `latest`
  stable release. Chrome for Testing's official known-good-version manifest
  contains no scanner-suggested `151.0.7922.173` or `152.0.7977.65` release.
  The existing exact `151.0.7922.72` URL/hash and Playwright base therefore
  cannot be safely advanced to an official qualified fixed runtime in this
  order.
- Did not guess a version, add a CVE exception, pin/rollback the scanner
  database, hide packages, omit SBOM entries, weaken thresholds, or use
  `continue-on-error`. No runtime, target, sandbox, credential, network,
  artifact, COW, or public queued-run behavior was changed in this slice.

## Blocking evidence

The unmodified current Grype database rejects the pinned worker image with
these 27 unexcepted Critical findings:

`CVE-2026-19149`, `CVE-2026-19157`, `CVE-2026-19164`, `CVE-2026-19166`,
`CVE-2026-19170`, `CVE-2026-19175`, `CVE-2026-76035`, `CVE-2026-76036`,
`CVE-2026-78909`, `CVE-2026-78935`, `CVE-2026-78937`, `CVE-2026-78939`,
`CVE-2026-78945`, `CVE-2026-78948`, `CVE-2026-78951`, `CVE-2026-78964`,
`CVE-2026-79012`, `CVE-2026-79026`, `CVE-2026-79043`, `CVE-2026-79047`,
`CVE-2026-79052`, `CVE-2026-79056`, `CVE-2026-79064`, `CVE-2026-79078`,
`CVE-2026-79091`, `CVE-2026-79111`, and `CVE-2026-79189`.

Scanner fixed-version data identifies the affected browser as Chrome
`151.0.7922.72`, with fixes at later versions, and identifies the base image's
Ubuntu packages as fixed only in later package releases. Those releases are
not present in the official upstream metadata checked above, while the
Playwright npm channel has no newer stable release. A second complete local
supply-chain execution was not launched because no qualified exact upgrade
was available; launching another unchanged scan would not remove the blocker.

## Verification

Passed locally: reproducibility helper tests (6), supply-chain policy and OCI
tests (32 combined), repository policy, `git diff --check`, and the prior
072-f complete worker/contract, sandbox, Compose, artifact, restart, hostile
network, COW, public-queue, packaging, process, Node, Python, Mermaid, and
Markdown gates. The 072-f clean Compose regression passed after the transient
Puck retry and remains preserved evidence.

Fresh CI run `33132053272` for this 072-g report head passed repository policy,
Node contracts, Python 3.12/3.13/3.14, Foundation PostgreSQL 14–18, Compose
and edge packaging, Markdown, Mermaid, and dependency review. CodeQL run
`33132053290` passed all language analyses. Supply-chain job `98723629869`
failed on the same 27 Critical browser-runtime findings. No check was skipped
except the normal CodeQL meta check; no failure was hidden or retried.

## Preserved boundaries and non-goals

The real confined Chromium worker remains Playwright `1.62.1`, Chrome for
Testing `151.0.7922.72` (SHA-256
`08254455dc5154fefa0165dc1dea16e496c8298f98c14d89bf38463810d21649`),
Chromium slot `1234`, Linux/amd64, official base
`mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e`,
and seccomp profile SHA-256
`294a5523dd03c8dad52215d7970d38711b03f7e6624e09f2ff109ea3628a645c`.
Sandbox, fixed-origin/default-deny networking, descriptor-confined
credentials, immutable private artifacts, and public runs remaining `QUEUED`
are unchanged. No dispatcher, database completion/artifact registration,
public artifact bytes, GC, source crawling, six-target sweep, review,
publication, extra PR, merge, auto-merge, release, or credential exposure was
performed.

Objective 072 remains `PARTIAL`: durable dispatch and public retrieval are
intentionally pending, and this 072-g runtime closure is blocked by the
absence of an official fixed upstream release compatible with the exact
scanner findings.
