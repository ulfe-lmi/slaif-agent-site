# OAP Work Order — 072-n

## Objective

Continue Objective 072 on PR #66. Refresh the same human-authorized, seven-day,
exact Chrome `.64` exception from 31 to 41 findings after current Grype DB drift.
Repair only supply-chain governance; leave the known Compose route failure for
072-o. Do not merge.

## Verified state

- Amend only PR #66 / `oap/072-browser-worker-real-playwright`; no new PR.
- Start at report-only head `e849ea2380ff2056ae724ec957a59c1187209f0c`;
  its sole parent is implementation `e40fbbb379e8819feb81c3feb9a57102cf0de3e8`.
  Main remains `082f2359b0c4d59b692580d17992c35d46183b12`.
- Current CI is red on Compose's known browser-preview 404 and supply-chain only.
- Fresh Grype reports 10 additional Critical findings for exact PURL
  `pkg:generic/chrome@152.0.7977.64`, all fixed at unpublished official `.65`:
  `CVE-2026-79058`, `CVE-2026-79090`, `CVE-2026-79148`, `CVE-2026-79200`,
  `CVE-2026-79232`, `CVE-2026-79235`, `CVE-2026-79257`, `CVE-2026-79275`,
  `CVE-2026-79282`, `CVE-2026-79290`.
- Google official known-good/latest-patch metadata still lists `.64`; raw `.65`
  object availability alone is not a qualified release. Human temporary risk
  acceptance, issue #67, owner and `2026-09-04` expiry remain in force.

## Requirements and acceptance

1. Add exactly those 10 exception entries: total 41 unique IDs, exact `.64`
   PURL, `browser-worker`, `human:project-owner`, issue #67, created
   `2026-08-28`, expires `2026-09-04`, same bounded rationale. No other scope.
2. Update open issue #67 from 31 to 41, explain current DB drift, list an ID set
   exactly equal to the exception file, and preserve mitigations/removal trigger.
   Verify remote issue state/count/set deterministically through `gh`.
3. Preserve unused/stale/near-match/wrong-severity/32nd-or-42nd fail-closed rules
   and visible per-finding PURL/exception evidence. Update exact-set and synthetic
   42nd tests; no scanner/DB/SBOM/severity/threshold weakening.
4. Run focused policy/evidence/repository tests and exactly one fresh complete
   supply-chain run. Require 41 Critical, 41 excepted, zero unexcepted for
   browser-worker and zero unexcepted elsewhere; reproducibility/licenses pass.
5. Require fresh GitHub supply-chain and every non-Compose check to pass. Compose
   is expected to remain red on the separately bounded 072-o route defect; do
   not rerun broad local Compose or alter its product/test code here.

## Scope and workflow

Only exception JSON, exact tests/docs, issue #67, strategic order/active/report.
No route/token/Web/Render/dispatcher/worker/runtime, migration, dependency,
public retrieval, GC/source/review/promotion, second PR, merge or release.

Commit/push unchanged order and `oap/active`, then repair. Publish exactly
`oap/reports/072-n-refresh-browser-exception-41.md` as report-only child with
literal implementation parent and `Report publication commit: SELF`; signal
exact FIFO `OK`.

Report issue comparison, exact 41 IDs/PURL/expiry, scanner DB/totals, fail-closed
tests, one expensive run, current checks including known Compose failure, files/
SHAs, no extra PR and no merge. Objective 072 remains `PARTIAL`.
