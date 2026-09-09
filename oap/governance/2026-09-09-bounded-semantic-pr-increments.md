# Human amendment: bounded semantic PR increments

Effective 2026-09-09, approved by the human project owner. This is a prospective
amendment to OAP Protocol 1.2 and both role constitutions. Earlier orders,
reports and the prior one-objective/one-PR rule remain historical records.

The controlling invariant is now **one bounded semantic merge increment = one
PR**. A numeric objective may span multiple sequential PRs. Retain unique
`NNN-L` order/report IDs and monotonically advancing letters across its PRs.
The order's explicit `CREATE_NEW_PR` or `AMEND_EXISTING_PR` mode, increment
identity, verified base and named PR/branch control delivery; the letter alone
no longer determines PR creation. Never have two active execution increments.
Do not advance the numeric objective until all its contractual increments have
been accepted and merged. Do not invent letters after z; escalate if exhausted.

Strategy declares each PR's bounded semantic contract, owns acceptance and
merge, and reassesses cumulative PR size at roughly 20–30 implementation files
or several thousand substantive changed lines. These are review triggers:
record the reason for any exception, separating production code, migrations,
tests, generated contracts and orchestration/docs. Small rounds do not excuse
an unreviewable cumulative PR. Finish a coherent increment and merge it once
its contract and all required checks pass, even when the numeric objective has
remaining scope. The next increment starts from verified current remote main.

All unchanged OAP laws continue: exact FIFO OK, atomic order/active publication,
immutable orders/reports, reports as claims, report-only SELF commit with exact
implementation parent, independent GitHub review, tests/security/isolation,
and strategic-only merge. Current governance may gain this explicit amendment;
historical orders/reports may not be rewritten. Executor does not choose a new
increment, expand scope, accept or merge itself.

For Objective 078 increment 1, PR #77 is frozen to bounded component composition
and component-local design semantics, plus necessary defect repairs, evidence,
truth reconciliation and this amendment. The already-delivered 078-i theme
implementation is not accepted into this increment: remove its product diff
without deleting its commits or immutable order/report. Record its preserved
commit and defer reuse/review to a new theme PR from main after PR #77 merges.
No global theme/regions/header-footer/media/MCP/exact-workspace Puck/lifecycle/
publication or other later functionality may enter PR #77.

Track objective status separately from each increment's PR acceptance, merge
SHA/time, verified main and remaining scope. `oap/active` names the latest
activated round until the next activation; it does not itself claim an open PR
or objective completion. Use a current increment ledger and truth documents
to record accepted/merged/deferred state. The final report names only its actual
increment and evidence, never claims broader Objective 078 completion.

