# Human amendment: increment-qualified round IDs

Effective 2026-09-14, approved by the human project owner. This is a
prospective amendment to OAP Protocol 1.2, the 2026-09-09 bounded-semantic-PR
amendment, and both role constitutions. Earlier orders, reports, audits, and
governance remain historical records; this amendment does not rewrite them.

On 2026-09-14 the human owner issued a directive authorizing the prospective
round-ID form `NNN-I-L` — numeric objective, semantic increment number,
lowercase round letter — alongside the existing legacy flat form `NNN-L`,
reserving `078-z` as the final legacy-format transition round of numeric
Objective 078 and starting the next Objective-078 product increment at
`078-5-a`.

## ID forms

- **Legacy flat:** `NNN-L` — zero-padded 3-digit numeric objective plus one
  lowercase round letter `a..z`. All historical identifiers remain immutable
  in this form.
- **Increment-qualified:** `NNN-I-L` — zero-padded 3-digit numeric objective,
  semantic increment number `I` (one or more decimal digits, no leading zero),
  and one lowercase round letter `L`. `078-5-a` is valid; `078-0-a` and
  `078-05-a` are invalid.

Both forms are valid identifiers for `oap/active`, order files, report files,
branches, and PR naming. Repository validation accepts both forms and groups
artifacts by the full identifier (legacy `NNN-L` or qualified `NNN-I-L`).

## Transition rules

- `078-z` is the reserved **final legacy-format round of numeric Objective
  078**; it is a control-plane governance transition only and contains no
  product functionality.
- 078/1 through 078/4 are historical accepted increments, merged at
  `3cae3d6cef2a92e7068856d21bc9a47b8190c22e`,
  `a9d3e6800d5e8b5fd5c9cd9e0be5010184058c6b`,
  `fe31c9f30a7797d0916ad7f8fb56344bc61526f3`, and
  `26cafc1c0c91de5eee8406e8d477c50ea0208058` respectively.
- After `078-z` merges, the next Objective-078 product increment starts at
  `078-5-a`, then `078-6-a`, `078-7-a`, and so on for each subsequent semantic
  increment.
- Objectives whose first increment already uses flat IDs keep that history
  (for example future `079-a`); a later second increment of such an objective
  uses the qualified form (`079-2-a`).
- No `aa`-style suffixes. Each increment-qualified namespace, and each legacy
  objective, has its own independent `a..z` sequence.
- Increment numbers correspond to the semantic increment ledger
  (`oap/INCREMENTS.md`) and are never reused or silently renumbered.
- If an increment's `a..z` sequence is exhausted, escalate; never invent wider
  suffixes.
- Qualified IDs appear only when a strategic order activates them; the coding
  agent never invents or chooses an ID in either form.

## Prospective effect

This directive is prospective. It does not rewrite, renumber, or reinterpret
historical orders, reports, audits, or governance. The 2026-09-09
bounded-semantic-PR-increments amendment remains in force; this amendment
refines the identifier namespace only. All unchanged OAP laws continue: exact
FIFO `OK`, atomic order/`active` publication, immutable orders/reports,
reports as claims, report-only `SELF` commit with exact implementation parent,
independent GitHub review, tests/security/isolation, and strategic-only merge.
