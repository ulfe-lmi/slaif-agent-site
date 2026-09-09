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
The mutable governance amendment is formatted. Immutable 078-j remains
byte-for-byte untouched because the requested human one-newline override has
not arrived through control FIFO. Consequently Markdownlint is intentionally
not green for that one immutable order error; no bypass is active.

## Verification state

Focused Agent authority, migration, Editor, unit, Puck, and renderer tests are
run after the repairs. The final report records exact commands and results.
No theme or later feature was added, no historical order/report was rewritten,
and no merge or auto-merge was performed. The remaining action is the human
newline decision, followed by the required final Markdown/CI verification.
