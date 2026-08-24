# OAP Work Order — 077-a

## Objective

Prove that two workspaces editing the same canonical row produce a
structured conflict on second acceptance, with canonical preserved and
no silent overwrite.

## GitHub objective state

- Numeric objective: `077`; round: `077-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR

## Verified current state

- Architecture §18 mandates two-workspace conflict demonstration.
- Promotion service handles `CowConflictError` (from 074).
- No dedicated E2E proof exists.

## Required changes

1. Add integration/E2E test `tests/integration/conflict_two_workspaces.spec.ts`:
   - seed canonical site with content item having editable title;
   - create workspace A; agent A updates title to "Alpha";
   - create workspace B (before A accepts); agent B updates same title to
     "Beta";
   - freeze A; accept A → succeeds; canonical title = "Alpha";
   - freeze B; attempt accept B → conflict raised;
   - verify workspace B enters CONFLICTED state;
   - verify canonical title remains "Alpha";
   - verify structured error returned (BASE_ROW_CHANGED);
   - discard B; canonical still "Alpha".
2. Also test non-overlapping concurrent changes succeed independently.
3. Assert no data corruption: row count unchanged; audit trail intact.

## Explicit non-goals

- Do NOT implement automatic rebase or field-level merge.
- Do NOT implement conflict-resolution UI.
- Do NOT test selective acceptance.

## Acceptance criteria

- Conflicting second acceptance blocked with structured error.
- Canonical data intact throughout.
- Non-overlap concurrency proven safe.
- CI green.

## Report

Publish `oap/reports/077-a-concurrent-conflict-e2e.md` with SELF report
commit parenting implementation SHA.
