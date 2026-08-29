# OAP implementation report — 072-h

ID: `072-h`

Order: `oap/orders/072-h-qualified-stable-browser-runtime.md`

Result: `BLOCKED`

PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66)

PR mode: `AMENDED_EXISTING_PR`

Repository: `ulfe-lmi/slaif-agent-site`

Base: `main` (`082f2359b0c4d59b692580d17992c35d46183b12`)

Head branch: `oap/072-browser-worker-real-playwright`

Starting 072-g report head: `63ea4df47edd2098b6ef8c4cf40ad24711c326e9`

Implementation commit: `fac4f0974033b180807f424536730ffc885d90f6`

Report publication commit: SELF

## Finding matrix and diagnostics

`supply-chain/browser-worker-critical-matrix.json` is the bounded
machine-readable matrix. It records every Critical finding from the pinned
baseline and both evaluated candidates: ID, artifact/package, installed
version, binary/package ecosystem, namespace, fixed versions, match type,
secret-safe location, and whether it is Chrome/Chromium bytes or a base OS
library. The captured scanner is Grype `0.117.0`, vulnerability DB `v6.1.9`,
built `2026-08-27T09:17:14Z`.

The baseline `151.0.7922.72` image has 27 Critical Chrome findings. Six old
IDs (`CVE-2026-19149`, `19157`, `19164`, `19166`, `19170`, `19175`) are fixed
at `151.0.7922.109`; the remaining 21 are fixed at later `151.0.7922.169`
or `152.0.7977.65`. All baseline locations are
`/ms-playwright/chromium-1234/chrome-linux64/chrome`; no base OS library was
the source of these Critical findings.

The 072-g bounded reproducibility diagnostic now reports the first differing
normalized section/path and only type, mode, size, normalized metadata,
symlink target, and SHA-256 fingerprints. One complete diagnostic (both
Python builds and both complete Node/workspace builds) passed, so the earlier
CI manifest mismatch did not reproduce and no executable/dependency output was
excluded or normalized speculatively.

## Candidate evaluation

Candidate 1 was the official stable Chrome for Testing release from Google's
`last-known-good-versions-with-downloads.json`: version `152.0.7977.64`,
revision `1669021`, timestamp `2026-08-27T22:25:50.454Z`, linux64 URL
`https://storage.googleapis.com/chrome-for-testing-public/152.0.7977.64/linux64/chrome-linux64.zip`,
SHA-256 `8b592f066af71f054aab2cc80fc26f73c775c6d44ebb99d16ade924b24756c2e`.
Its complete candidate image build and targeted Grype scan found 19 Critical
Chrome findings, all fixed only at `152.0.7977.65`; it was rejected.

Candidate 2 was the official Google Chrome Stable glibc Debian package
`google-chrome-stable 152.0.7977.64-1`, exact pool URL
`https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_152.0.7977.64-1_amd64.deb`,
SHA-256 `4eae0736a812d9bc851cd2937f7af00e47dbaf8305845eed452703ff009873c7`.
Its complete candidate image build and targeted Grype scan produced the same
19 Critical Chrome findings, fixed only at `.65`; it was rejected. The
temporary Dockerfile experiment was fully reverted. No third candidate was
attempted.

Official npm metadata still reports `playwright-core` and `@playwright/test`
`1.62.1` as latest stable, so no Playwright upgrade was guessed. The official
CfT stable channel exposes `.64`, not scanner-fixed `.65`; no qualified exact
runtime can meet the zero-Critical gate under this order's no-exception rule.

## Preserved runtime and boundaries

The branch retains Playwright `1.62.1`, Chrome for Testing `151.0.7922.72`,
Chromium slot `1234`, Linux/amd64, base
`mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e`,
and seccomp profile SHA-256
`294a5523dd03c8dad52215d7970d38711b03f7e6624e09f2ff109ea3628a645c`.
Sandbox launch, fixed Web origin/default-deny URL policy, descriptor-confined
credentials, non-root/read-only/dropped-capability/resource confinement,
immutable private artifacts, restart retrieval, COW preview behavior, and
public runs remaining `QUEUED` are unchanged. No exception, ignore, severity
downgrade, scanner/database pin, package hiding, SBOM omission, threshold
weakening, or `continue-on-error` was used.

## Verification and CI

Local focused checks passed: reproducibility helpers (6), supply-chain policy
and OCI tests (32), repository policy, JSON validation, and `git diff --check`.
The prior 072-f clean Compose evidence remains valid, including real sandboxed
worker execution, nine Playwright projects, hostile probes, artifact restart
and privacy checks, secret recovery, and public queued-run separation.

Fresh CI run `33134161356` for implementation `fac4f097…` passed repository
policy, Node contracts, Python 3.12/3.13/3.14, Foundation PostgreSQL 14–18,
Compose and edge packaging, Markdown, Mermaid, and dependency review. CodeQL
run `33134161376` passed all language analyses. Supply-chain job
`98730280266` failed with the same 27 Critical baseline findings. The final
report-only head receives the normal fresh CI rerun; no result is being
represented as a pass until GitHub records it.

No final complete supply-chain run for an accepted candidate was launched:
both permitted candidates were rejected by targeted scans, and the order
requires stopping rather than a third candidate or an unchanged broad retry.

## Scope and non-goals

Changed files in this slice are the strategic 072-h order/active, the bounded
reproducibility diagnostic/test already required by 072-g, and the critical
finding matrix. No migration, database role/function/grant, capability or
preview-token semantics, COW/Render behavior, dispatcher, lease recovery,
durable completion/artifact registration, public bytes, GC, source crawling,
six-target sweep, review, publication, extra PR, merge, auto-merge, release,
or credential exposure was performed.

Objective 072 remains `PARTIAL`: durable dispatch and public retrieval remain
intentionally pending, and this 072-h runtime slice is `BLOCKED` because both
evidence-selected official stable candidates retain unexcepted Critical Chrome
findings.
