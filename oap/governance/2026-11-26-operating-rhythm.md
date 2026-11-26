# Human amendment: operating rhythm

Effective 2026-11-26, approved by the human project owner. This is a
prospective amendment to OAP Protocol 1.2 and both role constitutions,
adopted at the 2026-11-25 development pause on the external reviewer's
recommendation. Earlier orders, reports, state records and the pause record
remain historical records. Every unchanged OAP law continues: immutable
activated orders and published reports, exact wire discipline, reports as
claims, independent GitHub verification before acceptance, and strategic-only
merge. This amendment changes rhythm, not evidence standards. Nothing here
weakens any acceptance gate, hostile-negative requirement, supply-chain
policy, or the rule that only the human authorizes MVP/release claims.

## 1. Bounded repair rounds

An implementation round that fails strategic review receives at most **one**
same-increment repair round. If the repair round also fails review, strategy
must either (a) record a deliberate, reasoned abandonment of the increment
per protocol and reassess scope, or (b) stop and escalate to the human with
the exact findings. Iterating repair letters as the default response to
review failure is prohibited. The 083/13 experience (round `a` failed on a
real provenance defect, round `b` repaired and merged) is the model case for
the bound working as intended.

## 2. Maintenance is not a product increment

Dependency refreshes, CVE remediations, pin bumps, scanner-coverage repairs,
and installer-copy remediations are **maintenance rounds**, not numbered
product increments. Strategy batches them into one scheduled maintenance PR
per calendar month at most (plus immediate rounds only for a Critical with a
known exploitation path in the deployed configuration), using an unprefixed
`maint-YYYY-MM` order ID under the same order/report/acceptance discipline.
Maintenance rounds never carry product behavior changes, and product
increments never carry opportunistic dependency changes. New CVEs surfacing
while no round is active are recorded as notes for the next maintenance
round, not activated.

## 3. Durable state excludes ephemera

`STATE.md`, orders, reports, ledgers and governance records contain only
durable resumption facts: objective/increment identity, verified SHAs, PR
identity, acceptance state, explicit human decisions, and open findings.
Session handles, PIDs, FIFO inodes, lock inodes, packet digests of prompt
deliveries, pane identifiers and similar runtime ephemera are never written
to durable records; they may exist only in `/tmp` wire records with the round
and are summarized in durable state at most as a closed/verified outcome.
GitHub plus `oap/` must remain sufficient to reconstruct full project state
without any live session — the external reviewer demonstrated this
reconstruction in under one hour on 2026-11-26.

## 4. Review queues are consumed on schedule

Any queue that records deferred human or strategic review (for example the
CRITICAL.md pattern) gets a named owner, a review-by date at creation, and a
scheduled drain at least once per maintenance cycle. A queue entry older
than one cycle without review is escalated to the human as a process defect,
not left to fossilize. The 2026-11-26 external closure of CRITICAL.md
(`87e77a5a2b7e35c3bcf6c4a40bb1dcdd05484d3b`) is the reference disposition.

## 5. Resumption under this amendment

The first strategic actor resuming after the 2026-11-25 pause reads this
amendment together with `oap/governance/2026-11-25-development-pause.md`,
verifies GitHub `main` against that record, and applies this rhythm
prospectively to all subsequent planning, activation, review and state
keeping. Historical oversized state files may be condensed into their
durable facts as a documentation-only action before the next activation;
history is preserved, not rewritten.
