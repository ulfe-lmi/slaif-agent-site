# OAP Work Order — 077-a

## Objective

Correct all documentation to accurately reflect implemented vs scaffolded
functionality, replacing overclaimed MVP progress statements.

## GitHub objective state

- Numeric objective: `077`; round: `077-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR

## Verified current state

- After objectives 065–076 merge, most core verticals should be functional.
- `MVP-PROGRESS.md` claims "~100%" based on stale interface-presence evidence.
- README states "All core architectural components are implemented and wired."
- `CRITICAL.md` queue understates systemic issues found in closure audit.

## Required changes

1. Rewrite `oap/MVP-PROGRESS.md`: per-phase honest status backed by merged
   PR references and passing E2E names; distinguish IMPLEMENTED_PROVEN /
   IMPLEMENTED_PARTIAL / STUB / NOT_IMPLEMENTED.
2. Update README implementation-status section: remove blanket claims; list
   what works with evidence links (PR numbers, test names).
3. Update `CRITICAL.md`: close resolved items; add any remaining known gaps
   (e.g., selective acceptance UI absent, OIDC absent, Prometheus absent).
4. Update user manual if behavior changed (Puck editor usage, media upload,
   agent workflow).
5. Ensure docs do NOT claim: production-ready, certified, hostile-SaaS-safe,
   or more browser compatibility than tested targets prove.
6. Run markdownlint; fix all warnings.

## Explicit non-goals

- Do NOT change executable code except doc-referenced config comments.
- Do NOT add new features.
- Do NOT update ARCHITECTURE.md (human-facing; separate authority).

## Acceptance criteria

- Every MVP matrix row cites merged PR + test name as evidence.
- No overclaim language remains.
- Known limitations explicitly listed.
- markdownlint passes.
- Documentation matches observable behavior.

## Report

Publish `oap/reports/077-a-documentation-truth-pass.md` with SELF report
commit parenting implementation SHA.
