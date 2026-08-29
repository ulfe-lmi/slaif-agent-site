# OAP Work Order — 072-j

## Objective and authority

Continue Objective 072 on PR #66. The human's explicit temporary Critical-risk
acceptance remains in force for the same isolated Chrome `.64` browser-worker.
Refresh the documented seven-day exception from 19 to exactly the 31 Critical
IDs now reported by the newer Grype database. Restore the supply-chain gate
without weakening exact-match, unused/stale, expiry, or new-finding failure.
Do not add product behavior and do not merge.

## Verified state

- Amend only PR #66 / `oap/072-browser-worker-real-playwright`; no new PR.
- Start at report-only head `06e604491e02915f6b9df677a13830ed432e4bb4`;
  its sole parent is implementation `d52cc5f4631c8184711f212cf02add1587d582c0`.
  Main remains `082f2359b0c4d59b692580d17992c35d46183b12`.
- 072-i correctly pinned official stable CfT `152.0.7977.64`, revision
  `1669021`, SHA-256
  `8b592f066af71f054aab2cc80fc26f73c775c6d44ebb99d16ade924b24756c2e`,
  created issue #67, and added 19 exact exceptions expiring `2026-09-04`.
- Fresh Grype DB `v6.1.9`, built `2026-08-28T09:21:39Z`, reports 12 additional
  Critical IDs for the same exact PURL `pkg:generic/chrome@152.0.7977.64`, all
  fixed at `.65`: `CVE-2026-78900`, `CVE-2026-78904`, `CVE-2026-78985`,
  `CVE-2026-79128`, `CVE-2026-79129`, `CVE-2026-79130`, `CVE-2026-79131`,
  `CVE-2026-79140`, `CVE-2026-79149`, `CVE-2026-79150`, `CVE-2026-79152`,
  `CVE-2026-79188`. They are the sole current unexcepted failures.
- The raw `.65` storage URL returns 200, but `.65` is absent from Google's
  official known-good and per-version metadata. Do not treat an unlisted object
  as a qualified release or change the runtime in this round.

## Requirements and acceptance

1. Update issue #67 to record the database drift, all 31 exact IDs, and that the
   same human authorization, owner, mitigations, expiry and official-metadata
   removal trigger apply. Preserve its open state.
2. Add exactly 12 exception entries so the file contains exactly 31 unique
   entries, all with the same exact `.64` PURL, `browser-worker` scope,
   `human:project-owner`, issue #67 reference, `2026-08-28` creation,
   `2026-09-04` expiry, and bounded rationale. Change no other exception.
3. Keep every Critical finding/PURL/status visible in evidence. Preserve the
   rule that every exception must match a real Critical and that any unused,
   wrong-PURL/version/scope/severity, expired, duplicate, or additional 32nd
   Critical fails closed. Add/update exact-set and synthetic-32nd regression
   tests; do not weaken scanner, DB freshness, SBOM, severity, threshold, or CI.
4. Run focused exception/policy/evidence/repository tests, then exactly one
   complete clean supply-chain execution with a fresh current DB. It must show
   31 Critical, 31 excepted, zero unexcepted for browser-worker and zero
   unexcepted for every other image. Reproducibility/license/notices pass.
5. The `.64` runtime implementation is unchanged; independently require the
   fresh GitHub `Compose and edge packaging` check and all other required checks
   to pass. Do not rerun unchanged broad local Compose or CI jobs unless an
   evidenced infrastructure failure occurs.

## Non-goals and workflow

No runtime binary/pin, migrations/DB grants, auth/token/COW/Render, sandbox/
network/artifact policy, dispatcher/public retrieval/GC/source/review/promotion,
dependency, telemetry, release, architecture, second PR, merge, or auto-merge.

Commit/push unchanged 072-j order and `oap/active`, then the exact exception/
issue/test/docs repair. Publish exactly
`oap/reports/072-j-refresh-temporary-browser-exception.md` as report-only child
with literal implementation parent and `Report publication commit: SELF`;
signal exact FIFO `OK`.

Report issue update; exact 31 IDs/PURL/count/expiry; scanner DB and visible
excepted/unexcepted totals; fail-closed regressions; commands and one expensive
run; all CI; files; PR/base/branch/SHAs; no extra PR and no merge. Objective 072
remains `PARTIAL` pending dispatch/public retrieval.
