# OAP Work Order — 073-a

## Objective and GitHub mode

Create exactly one new Objective 073 PR from verified remote `main` after
Objective 072 merge `bcaddc41f9ef4e779dd1a8c9a41eb08462250d53`. Materially
publish the hostile contract audit and dependency-correct MVP queue, remove
false completion claims, and make repository policy recognize the new inert
orders. This is governance/documentation only; do not implement product code.

## Required state and scope

Strategy has already authored `oap/MVP-CONTRACT-AUDIT.md`, this order, and the
inert `074-a` through `091-a` order files. Commit those exact bytes unchanged.
Delete the superseded inert 073–078 order files exactly as present in the diff.
Preserve all activated/completed orders and reports, especially 065–072.

Update only the following non-strategic artifacts as needed:

1. `oap/MVP-PROGRESS.md`: remove percentages and `~100%`; use the audit status
   vocabulary, merged evidence, current gaps, and exact 074→091 sequence.
2. `README.md`: remove the claim that all core components are implemented;
   distinguish the proven 065–072 slices from missing Agent semantics, MCP,
   review/promotion, source/reconstruction and operations. Preserve mission and
   architecture wording.
3. `oap/POST-MVP-WORK-ORDERS.md`: move source reconstruction out of post-MVP;
   remove already-completed/now-MVP items; retain only genuine §51.2 or
   production follow-ups.
4. Add a short supersession notice to `oap/MVP-CLOSURE-AUDIT.md` pointing to
   the new baseline without rewriting its historical findings.
5. Update repository policy/tests so the exact planned range 074–091 is
   recognized as inert, unique, separate Markdown files and no old queued
   073–078 assumptions remain.

## Acceptance and anti-overclaim rules

- `oap/MVP-CONTRACT-AUDIT.md` maps material §51/§52 requirements to actor,
  interface, implementation/proof, status, objective, gap and final evidence.
- Every completed 065–072 objective is credited only for its narrow proven
  behavior; no broad capability becomes complete because files/routes exist.
- Reconstruction is contractual MVP Objective 088, not post-MVP.
- The queue forbids SQL/ORM/internal-service/privileged/test-helper substitutes
  for behavior claimed to be performed by an external agent or human UI.
- No `MVP COMPLETE`, `100%`, production-ready, hostile-SaaS, or unproved
  browser claim remains.
- Run repository policy/unit checks, Markdownlint and Mermaid validation.
  No broad product/Compose/browser/database run is required for docs-only work.

## Non-goals and safety

No product source, migration, dependency, lockfile, workflow, architecture,
constitution, prior report/order, GitHub issue, credential, release or merge.
Do not activate or execute future order files. No second PR.

## Report

Publish exactly `oap/reports/073-a-repair-mvp-control-state.md` as an immutable
report-only child of the literal implementation SHA. Include PR/branch/base,
exact files, audit/status/queue corrections, commands/results, current checks,
skips, no product change, no extra PR and no merge; use SELF protocol.
