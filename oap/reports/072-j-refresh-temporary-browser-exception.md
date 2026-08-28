# OAP implementation report — 072-j

ID: `072-j`

Order: `oap/orders/072-j-refresh-temporary-browser-exception.md`

Result: `COMPLETE`

PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66)

PR mode: `AMENDED_EXISTING_PR`

Repository: `ulfe-lmi/slaif-agent-site`

Base: `main` (`082f2359b0c4d59b692580d17992c35d46183b12`)

Head branch: `oap/072-browser-worker-real-playwright`

Starting 072-i report head: `06e604491e02915f6b9df677a13830ed432e4bb4`

Implementation commit: `e8bb8528d9683db03fe9ef48cc425bca7959a918`

Report publication commit: SELF

## Issue and exception refresh

Issue [#67](https://github.com/ulfe-lmi/slaif-agent-site/issues/67) remains
open and now records the Grype database drift, all 31 exact findings, the same
explicit human:project-owner authorization, isolated-worker mitigations,
2026-09-04 expiry, and removal trigger when qualified official stable `.65+`
metadata is published. The runtime remains official Chrome for Testing
`152.0.7977.64`, revision `1669021`, linux/amd64, URL
`https://storage.googleapis.com/chrome-for-testing-public/152.0.7977.64/linux64/chrome-linux64.zip`,
SHA-256
`8b592f066af71f054aab2cc80fc26f73c775c6d44ebb99d16ade924b24756c2e`.

The exception file now has exactly 31 unique entries, one each for
`CVE-2026-78900`, `CVE-2026-78904`, `CVE-2026-78909`, `CVE-2026-78935`,
`CVE-2026-78937`, `CVE-2026-78939`, `CVE-2026-78945`, `CVE-2026-78948`,
`CVE-2026-78951`, `CVE-2026-78964`, `CVE-2026-78985`, `CVE-2026-79012`,
`CVE-2026-79026`, `CVE-2026-79043`, `CVE-2026-79047`, `CVE-2026-79052`,
`CVE-2026-79056`, `CVE-2026-79064`, `CVE-2026-79078`, `CVE-2026-79091`,
`CVE-2026-79111`, `CVE-2026-79128`, `CVE-2026-79129`, `CVE-2026-79130`,
`CVE-2026-79131`, `CVE-2026-79140`, `CVE-2026-79149`, `CVE-2026-79150`,
`CVE-2026-79152`, `CVE-2026-79188`, and `CVE-2026-79189`.
Every entry has exact affected PURL `pkg:generic/chrome@152.0.7977.64`, scope
`browser-worker`, approver `human:project-owner`, issue #67 reference, created
`2026-08-28`, expires `2026-09-04`, and bounded rationale naming the unavailable
stable fix, isolated internal worker defenses, and temporary human acceptance.

## Fail-closed evidence contract

Evidence finalization retains each Critical finding's ID, exact PURL, scope, and
exception status, severity totals, affected PURL, and exception count. Every
exception must match an actual current Critical finding by exact ID/PURL/scope;
unused, stale, wrong-PURL/version/scope/severity, duplicate, near-match, and
synthetic additional 32nd findings fail closed. The gate wording remains
`zero unexcepted Critical`, never `zero Critical`. Exact-set and synthetic-32nd
regressions cover this contract.

## Supply-chain evidence

Exactly one complete clean local run was executed:
`tools/supply_chain/run.sh /tmp/slaif-072j-evidence`.
It passed reproducibility, frozen dependency/source/license/notices checks,
both clean browser-worker builds and the `.64` archive checksum, all six image
SBOMs/scans, and the fresh Grype `0.117.0` database `v6.1.9` built
`2026-08-28T09:21:39Z`. Final output was
`supply-chain-evidence: OK images=6 critical=31 high=99`; the browser-worker
evidence contains exactly 31 Critical findings, all 31 `excepted`, zero
unexcepted, and affected PURL `pkg:generic/chrome@152.0.7977.64`.
`validate-bundle --evidence /tmp/slaif-072j-evidence` and checksum validation
also passed. No scanner, database freshness, SBOM, threshold, or severity rule
was weakened, and no additional broad run was performed.

## Verification

Focused policy/evidence tests passed: 25 tests, including exact 31-entry set,
retained finding/status/PURL evidence, and synthetic 32nd Critical rejection.
Repository preparation and package gates passed: repository policy, compileall,
54 repository unit tests, Markdown and Mermaid checks, Python frozen lock/sync,
Ruff, format, mypy, distributions, all 476 backend/repository unit tests and
111 integration tests, and Node 24.14.1 / pnpm 11.22.0 install, lint, format,
typecheck, tests, build, and license inventory.

Fresh GitHub CI run `33217232303` for implementation `e8bb852` passed every
required job, including Supply-chain evidence, Compose and edge packaging,
Node contracts, Python 3.12/3.13/3.14, Foundation PostgreSQL 14–18, Repository
policy, Dependency review, Markdown, and Mermaid. CodeQL run `33217232467`
passed all analyses. No required check was skipped, hidden, or pending at
report publication.

## Scope and boundaries

Changed files are the 072-j order/active transcript, the exact vulnerability
exception set, evidence regression tests, and current supply-chain guidance.
The `.64` runtime implementation is unchanged from 072-i. No migration, DB
grant, auth/token/COW/Render, sandbox/network/artifact, dispatcher, public
retrieval, GC/source/review/promotion, dependency, telemetry, release, extra
PR, merge, auto-merge, or credential exposure was performed. PR #66 remains
open and unmerged. Objective 072 remains `PARTIAL`, pending dispatch and public
retrieval.
