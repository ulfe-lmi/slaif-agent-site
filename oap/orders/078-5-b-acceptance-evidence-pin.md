# OAP Work Order — 078-5-b: acceptance evidence pin for the ordered header shell

- Identifier: `078-5-b` (increment-qualified; second round of semantic
  increment 5 of numeric Objective 078; same-PR continuation of `078-5-a`)
- PR mode: AMENDED_EXISTING_PR
- Branch: `oap/078-5-a-global-regions-header-footer` (unchanged)
- PR: `#85` — `OAP 078-5-a: site-global regions and header/footer
  management`

## Verified current state (verified at activation, from live GitHub only)

- `main` = `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba` (unchanged since the
  078-z merge; strategy-reverified against live GitHub at activation)
- 078-5-a was activated 2026-09-17 (PR #85, CREATE_NEW_PR); implementation
  commit `64dea09f49c39acdcd65a84ce9f4968b6268b304` (48 files, +5146/-74)
- 078-5-a report published as `BLOCKED` with Blocker B-1; report-only
  commit `5cf6a2d1c88106c0a8228d1b0e1b7c513362291b` (adds exactly
  `oap/reports/078-5-a-global-regions-header-footer.md`, +788; parent =
  implementation head); PR #85 head is that report commit; base is
  `main` at `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`; PR is open,
  mergeable, not a draft
- Blocker B-1 (as published): the ordered site Header shell (order
  078-5-a, binding design decision 5) deterministically adds two `nav`
  elements to every rendered page (`nav[aria-label="Site"]` +
  `nav[aria-label="Language"]`), while the frozen 077u acceptance journey
  `tools/compose/public_agent_acceptance.py` still pins
  `"navigation": 0` in two structure expectations (line 1335, news
  journey; line 2067, component journey); the required CI check
  `Compose and edge packaging` failed on the 078-5-a heads solely for
  this reason (deterministic
  `news-browser-structure-evidence-invalid`), with all 11 browser
  projects and the remaining 19 required checks green
- All other journey evidence fields are unaffected per the published
  report's full local browser runs
- The 078-5-a implementation otherwise satisfies order 078-5-a scope and
  acceptance criteria, subject to Strategy's independent review of the
  full increment at the 078-5-b head

## Objective

Resolve Blocker B-1 by amending exactly the two stale frozen structure
evidence pins in `tools/compose/public_agent_acceptance.py` so the
acceptance journey asserts the post-feature DOM contract (two `nav`
elements per page under the ordered defaults), without changing any other
journey logic, evidence field, product code, or expectation.

## Strategic context

- Same-PR continuation round under the 2026-09-09 and 2026-09-14
  amendments: `078-5-b` amends branch and PR #85 of `078-5-a`. The 078-5-a
  report is immutable and is not rewritten by this round.
- The DOM change is not an implementation accident: order 078-5-a binding
  design decision 5 mandates a site Header shell with navigation on every
  public/preview/review render. The journey predates this feature
  (created for 077u); its `"navigation": 0` pins are no longer truthful
  invariants.
- This order supersedes the 078-5-a non-goal "No source tools" solely for
  this file and these two lines. Nothing else is relaxed.
- This is an evidence-pin correction, not an assertion weakening: the
  journey still asserts the exact post-feature structure, and every other
  evidence field remains pinned unchanged.

## Binding decisions

1. Exactly two line changes in
   `tools/compose/public_agent_acceptance.py` as of head
   `64dea09f49c39acdcd65a84ce9f4968b6268b304`:
   - news journey structure expectation (line 1335):
     `"navigation": 0` changed to `"navigation": 2`
   - component journey structure expectation (line 2067):
     `"navigation": 0` changed to `"navigation": 2`
2. No other line of that file changes; no other file changes.
3. No product code, migration, config, generated-contract, or doc change
   in this round.

## Bounded scope — allowed file set (acceptance criterion 1 pins this)

- `tools/compose/public_agent_acceptance.py` — exactly the two line
  changes above
- OAP transcript: this order, `oap/active`, this report

## Explicit non-goals

- No other evidence field, journey, or assertion changes
- No product code changes; no new feature
- No migration, dependency, lockfile, workflow, ruleset, or catalog
  change
- No doc changes (078-5-a docs stand as published)
- No Dependabot PR interaction

## Requirements

1. Make exactly the two line changes of binding decision 1.
2. Run the full local Compose smoke journey (the same
   `sh tools/compose/smoke.sh slaif0075a` run class as recorded in the
   078-5-a report) and record the final status lines: all browser
   projects PASS, `compose-e2e: OK`, `public-agent-acceptance: OK`.
3. Run `python tools/check_repository.py` (PASS).
4. Commit the implementation change (implementation head), push, then
   make the report-only `SELF` commit (parent = this round's
   implementation head).
5. Commit the activated order and `oap/active` for this round
   byte-for-byte unchanged with the implementation.

## Observable acceptance criteria

1. This round's diff is exactly two lines in exactly one file (both
   `"navigation": 0` to `"navigation": 2` in the two structure
   summaries).
2. No other file is touched by this round.
3. The full local Compose smoke run passes end-to-end, including
   `public-agent-acceptance: OK` (exact final status lines recorded).
4. Every required GitHub check is successful on the exact report-only
   head of this round — in particular `Compose and edge packaging` is
   green.
5. The report contains per-criterion evidence (pass/fail/skip/not-run)
   and the cumulative base→head size grouped per review-unit governance
   §2 (base = `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`).

## Verification

Local: full Compose smoke journey (all browser projects + compose-e2e +
public-agent-acceptance); repository policy check.
Remote: full required CI matrix green on the exact head; Strategy
independently reviews the two-line round diff plus the cumulative
078-5-a + 078-5-b diff before acceptance.

## Security

No authority, scope, or trust surface changes in this round. No journey
assertion other than the two ordered-feature pins is weakened. No secrets
in diff or report.

## GitHub workflow

AMENDED_EXISTING_PR: same branch
`oap/078-5-a-global-regions-header-footer`, PR #85, base
`d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`. All commits pushed; report
commit is `SELF`; Strategy is the only merger.

## Report requirements

Standard OAP report template plus explicitly:

- the exact two-line diff;
- the final status lines of the local Compose smoke run;
- the status of every required GitHub check on the exact report-only
  head;
- confirmation that no other evidence field or assertion changed;
- the cumulative base→head size grouped per review-unit governance §2
  (this round's delta and the 078-5-a + 078-5-b cumulative).

## Predeclared review budget (review-unit governance §1)

- Production/config files: 0 (one evidence-tool file, two lines)
- Migrations: 0
- Test/evidence footprint: existing frozen journey re-run (no new tests)
- Generated-contract footprint: none
- Docs footprint: none
- OAP transcript footprint: order + report
- Expected substantive implementation scale: 2 lines
- Review trigger: cannot fire; cumulative size is 078-5-a plus two lines
