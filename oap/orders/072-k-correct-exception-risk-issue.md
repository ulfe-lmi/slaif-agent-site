# OAP Work Order — 072-k

## Objective

Continue Objective 072 on PR #66. Correct the externally authoritative risk
record for the human-authorized temporary browser exception. Issue #67 still
states 19 findings although 072-j and the green repository gate now cover 31.
Update that one issue to match exact current evidence; change no product or
supply-chain implementation. Do not merge.

## Verified state

- Amend only PR #66 / `oap/072-browser-worker-real-playwright`; no new PR.
- Start at green report-only head
  `1d2c5bb9773c2f6cdf1380cc7d99dc3984cc0515`; its sole parent is
  `e8bb8528d9683db03fe9ef48cc425bca7959a918`. Main remains
  `082f2359b0c4d59b692580d17992c35d46183b12`.
- All 20 current required checks pass. The exception file has exactly 31 unique
  IDs for `pkg:generic/chrome@152.0.7977.64`, `browser-worker`, expiry
  `2026-09-04`, reference issue #67.
- Independent `gh issue view 67` shows the issue body still says “19” and omits
  the 12 IDs added in 072-j. The 072-j report's claim that it was updated is
  false; activated report remains immutable.

## Requirements and acceptance

1. Update only issue #67. State 31 exact findings and list all IDs exactly as
   `supply-chain/vulnerability-exceptions.json`; explain the 12-entry increase
   came from Grype DB drift during 072-i; preserve human authorization, exact
   `.64` runtime/PURL, isolated-worker mitigations, owner, expiry, and mandatory
   qualified-official `.65+` removal trigger. Keep the issue open.
2. Verify through a fresh `gh issue view 67 --json body,state,url` that the
   remote issue—not local prose—has state OPEN, count 31, and an ID set exactly
   equal to the exception file. Report a deterministic comparison result.
3. Change no existing repository file except committing the unchanged strategic
   072-k order and `oap/active`, then the required report. Do not rerun broad
   local builds/Compose/supply-chain: current implementation and checks are
   unchanged. Require all fresh GitHub checks on the transcript/report head to
   finish successfully; report any failure honestly.

## Workflow and report

No code, dependency, exception, test, docs, runtime, issue creation, PR creation,
merge, auto-merge, release, or unrelated external action.

Publish exactly `oap/reports/072-k-correct-exception-risk-issue.md` as a
report-only child with literal implementation parent and
`Report publication commit: SELF`; signal exact FIFO `OK`. Report the issue URL,
before/after count, exact-set comparison, issue state, repo paths/SHAs, every
current CI check, no extra PR and no merge. Objective 072 remains `PARTIAL`.
