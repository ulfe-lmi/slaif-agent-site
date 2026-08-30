# OAP Work Order — 075-h

## Objective and verified state

Amend only PR #71 / `oap/075-editable-domain-substrate`; no new PR/merge.
Required starting head `3b590a4133989afa445ba00377d6b9a0a68ca64d`,
sole parent `b630b6cf3b8ebf35cb03deed41c20a7b42a5e517`; main/base
`ef456e63abadddfc7d90794c03be3a63677c87f9`; all 20 checks are green.
Product implementation and evidence for 075-a..g are strategically satisfactory.
Repair only the final transcript/publication violation.

## Forensic fact and required correction

Do not edit any earlier order or report. The new 075-h report must state:

- 075-g implementation consists of product commits
  `9293102cdeb9c743adfb19d6d2bb7c316a6dc34b` and
  `b630b6cf3b8ebf35cb03deed41c20a7b42a5e517`;
- publication commit `3b590a4133989afa445ba00377d6b9a0a68ca64d` has parent
  `b630b6cf3b8ebf35cb03deed41c20a7b42a5e517` but changes three paths:
  `oap/active`, `oap/orders/075-g-close-agent-binding-definition-and-localization.md`,
  and `oap/reports/075-g-close-agent-binding-definition-and-localization.md`;
- therefore 075-g did not satisfy the report-only SELF rule, even though its
  report file itself has not been rewritten and product/check evidence remains
  valid. Preserve Git history; this append-only correction does not pretend the
  violation never occurred.

## Exact workflow and acceptance

1. Commit this exact unchanged 075-h order and `oap/active` as the only changes
   in the 075-h implementation/transcript commit. No product/doc/policy/test/
   migration/dependency/prior artifact changes.
2. Verify live PR identity, all 075 orders/reports/history, current product head
   ancestry, and all current required checks. No broad local suite rerun is
   required; run repository policy, Markdownlint on this order/report content,
   `git diff --check`, and exact commit/path/parent inspections.
3. Publish exactly one new report
   `oap/reports/075-h-reconcile-final-report-publication.md` in a final commit
   that changes only that report and whose sole parent is the literal 40-hex
   075-h implementation/transcript commit. Make no later push.

The report includes exact PR/base/head/commits/path lists, the 075-b and 075-g
protocol deviations and their existing 075-c/075-h corrections, current 075
product conclusion, commands/checks/skips, no extra PR/merge/release and
`Report publication commit: SELF`. Signal only after remote verification.
