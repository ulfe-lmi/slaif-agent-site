# Objective 078/1 — 078-k closure evidence

This executor-owned evidence supplements the immutable strategic audit
[`078-1-final-hostile-audit.md`](078-1-final-hostile-audit.md). It does not
rewrite that audit, choose acceptance, or claim completion of Objective 078.

## F1 — full validation before projection

`063_001_component_audit_repairs.py` replaces the design validator so unknown
properties, JSON null, nested executable values, invalid alignment maps, and
fractional integer design values fail before responsive collapse. The Python
generated authority performs the same checks. Public HTTP and runtime-role
regressions cover Button alignment injection, unknown null, and fractional
Grid columns with unchanged state.

## F2 — responsive CREATE

The 063 CREATE replacement invokes the full design validator instead of the
scalar validator. Focused public HTTP and runtime-role tests prove responsive
Button, Image, and CollectionGrid CREATE with exact scalar plus responsive
scopes, deny missing responsive scope, and retain L2 omitted defaults for
Columns and Spacer.

## F3 — real renderer cascade

The production renderer now emits the documented mobile fallback, CSS applies
tablet values through mobile unless a mobile value overrides them, and CSS
defines Section variants, responsive Spacer sizes, primary/auto resets, and
bounded integer design behavior. The diagnostic CSS probe reports Section
narrow `768px`, Grid `4/2/2` columns at desktop/tablet/mobile, and Spacer
mobile-xl `32px`. The added Playwright preview test asserts computed styles,
not class names, at 1440, 900, and 390 pixels.

## F4 — human Editor/Puck

The human site authority now returns effective permissions to the Editor
composition route. CREATE and PATCH derive component-local design permissions
from the shared design authority before invoking the legacy Editor wrapper;
platform administrators retain their existing bypass. The 063 legacy wrappers
use the full responsive design validator, and the Puck round-trip test saves,
reloads, and preserves a responsive Section variant through production Editor
HTTP.

## F5 — migration reversibility

The 062 downgrade now restores the prior 061 component UPDATE definition and
runtime grant in addition to CREATE and authority. The 063 downgrade restores
the 061 validator, 062 component wrappers, and 060 Editor wrappers from their
immutable migration sources. The migration round-trip tests inspect function
definitions/grants and re-upgrade without data loss.

## F6 — current truth

README, MVP progress/audit, and the increment ledger state that Objective 077
and PR #74 were accepted and merged on 2026-09-08 at `ae3a4a6`. PR #77 remains
the open 078/1 component/local-design increment; theme, page-style, catalog,
and later 081+ work remain separate. The PR description is updated to match
the retained behavior and 078-k audit closure.

## F7 — lint and immutable artifact boundary

    The new whole-file ignores and repository-policy allowlisting were removed.
The mutable governance amendment is formatted. At the time of 078-k,
immutable 078-j remained byte-for-byte untouched because the requested human
one-newline override had not arrived through control FIFO. The later 078-m
governance record contains the explicit approval and exact one-byte correction;
no bypass is active.

## Verification state

Focused Agent authority, migration, Editor, unit, Puck, and renderer tests are
run after the repairs. The final report records exact commands and results.
No theme or later feature was added, no historical order/report was rewritten,
and no merge or auto-merge was performed. The remaining action was the human
newline decision, followed by the final Markdown/CI verification in 078-m.

## 078-l continuation evidence

The active 078-l continuation adds only the missing component MOVE and safe
downgrade proof. Migration `064_001_component_move_responsive.py` replaces the
Agent MOVE validator with the full trusted design validator while passing the
unchanged property state for a structure-only move. Its downgrade guard refuses
responsive breakpoint maps or the alignment extension before replacing any
older function, data, or grant state.

The following required proofs pass against real PostgreSQL and public Agent
HTTP: `test_agent_component_responsive_moves_preserve_props_and_authority`
(responsive Button, Image, and CollectionGrid moves across parents and slots,
narrowed structure-only authority, value-write denial, replay, stale version,
cancellation rollback, and direct runtime MOVE); and
`test_agent_064_component_downgrade_guards_and_round_trips_contract` (scalar
061-to-060 round-trip, exact function/grant repeatability, and atomic refusal
with responsive maps plus alignment). The component-focused selection passes
24 tests; the full Python unit/repository selection passes 538 tests; mypy
passes 268 files; and full Python Ruff/format, lock, repository-policy, and
Mermaid checks pass.

The frozen Node sequence passes on Node 24.14.1 and pnpm 11.22.0, including
install, lint, format, typecheck, test, build, and license inventory. At the
078-l report head, Markdownlint still reported the then-pending 078-j error;
078-m records its approved correction and final closure CI remains required.
Objective 078 remains PARTIAL pending strategic merge and later increments.

## 078-m strategic acceptance addendum

Human approval and strategy's technical acceptance are recorded in
`oap/governance/2026-09-09-078-j-whitespace-override.md` and
`oap/audits/078-1-strategic-acceptance.md`. The corrected 078-j bytes have
SHA-256 `942bb3f53507e76eb87559afb34f1ca3eb8bcabd59f7ac4e3a006b8d44189796`
and differ from the original only by deletion of its final LF. The 078-m order
requires no product change: only that approved historical whitespace correction,
the governance/transcript records, current-ledger reconciliation, and final
CI/merge evidence are in scope. Strategy accepted the product implementation
at `6e41a5201215015e48d266995242b9c58067b95c`; PR #77 remains open until the
final closure head is verified and merged by strategy.

## 078-m execution boundary

The approved 078-j correction is byte-exact and the strategic acceptance
records are present. Repository-wide Markdownlint now reports exactly one
issue in the consumed immutable order
`oap/orders/078-m-finalize-approved-whitespace-and-merge-evidence.md:4`
(`MD034/no-bare-urls`). The coding agent cannot edit an activated order or add
a lint bypass, so this is a strategy-artifact blocker rather than a product
failure. No product code, dependency, historical report, or other order was
changed.
