# OAP Work Order — 078-5-c: news-journey evidence pin correction (breadcrumb nav)

- Identifier: `078-5-c` (increment-qualified; third round of semantic
  increment 5 of numeric Objective 078; same-PR continuation of `078-5-b`)
- PR mode: AMENDED_EXISTING_PR
- Branch: `oap/078-5-a-global-regions-header-footer` (unchanged)
- PR: `#85` — `OAP 078-5-a: site-global regions and header/footer
  management`

## Verified current state (verified at activation, from live GitHub only)

- `main` = `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba` (unchanged;
  strategy-verified at activation)
- PR #85 open, mergeable, not a draft; head
  `e856034da31d0ff3e6df855a264b24907b4d6191` (078-5-b report-only commit,
  parent = `11cc318490677eef5f885da933b37ef31c4b51ff`, 078-5-b
  implementation head); base `main` at `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`
- 078-5-b report published as `BLOCKED` (Blocker B-2): the ordered pin
  `2` at line 1335 (news journey) contradicts the 078-5-a ordered
  Breadcrumb behavior. Live-captured evidence in that report proves the
  news journey's browser page — the news **detail** page, a child of the
  news listing page — renders exactly three `nav` elements
  (`aria-label` values `Site`, `Language`, `Breadcrumb`; the breadcrumb
  carries one ancestor link plus the current non-linked page). Every
  other structure-summary field is byte-identical to the pinned dict
  (live-captured dict in the 078-5-b report). The component journey page
  (line 2067) is parentless, so its pin `2` is correct as shipped.
  pin `2` is correct as shipped.
- CI run 35401349705 on `11cc318`: 18/20 green; `Compose and edge
  packaging` failed solely at the deterministic
  `news-browser-structure-evidence-invalid` assertion (all 11 browser
  projects green); `Supply-chain evidence` failed on six newly published
  Critical CVEs in the unchanged browser-worker image
  (CVE-2026-91710, CVE-2026-91716, CVE-2026-91718, CVE-2026-91728,
  CVE-2026-91729, CVE-2026-91738) — external scan-database drift, proven
  unrelated to this increment (identical image/check passed on the 078-5-a
  heads)

## Strategic decision recorded (Blocker B-2 resolution)

Strategy selects option 1 of the 078-5-b report: **correct the
evidence pin**. The breadcrumb on pages with an ancestor chain is ordered
product behavior — 078-5-a binding design decision 5 mandates
"Breadcrumbs derived from the current page's ancestor chain …
`aria-label="Breadcrumb"`", and the 078-5-a E2E suite already proves
breadcrumb rendering and click-through on child pages. The 078-5-b report
records that the 078-5-a report's "no ancestors" statement was false for
the news journey page (the immutable 078-5-a report is preserved as
written). Rendering suppression (option 2) would violate decision 5 and
break passing 078-5-a evidence; it is rejected.

## Objective

Change exactly one line in
`tools/compose/public_agent_acceptance.py` so the news journey's
structure-summary expectation asserts the ordered post-feature DOM:
`"navigation": 2` changed to `"navigation": 3`. No other change.

## Binding decisions

1. Exactly one line change in
   `tools/compose/public_agent_acceptance.py` as of head
   `e856034da31d0ff3e6df855a264b24907b4d6191`: in the news journey
   structure expectation (`_run_dynamic_news_edge_journey`, line 1335):
   `"navigation": 2` changed to `"navigation": 3`.
2. Line 2067 (component journey) stays `"navigation": 2` — unchanged.
3. No other line of that file changes; no other file changes.

## Bounded scope — allowed file set (acceptance criterion 1 pins this)

- `tools/compose/public_agent_acceptance.py` — exactly the one line
  change above
- OAP transcript: this order, `oap/active`, this report

## Explicit non-goals

- No product code, migration, config, generated-contract, or doc change
- No other evidence field, journey, or assertion change
- No browser-stack, dependency, or image change (the supply-chain CVE
  drift is a separate strategic increment — 078/6 browser security
  refresh from verified main; do not touch it in this round)
- No Dependabot PR interaction

## Requirements

1. Make exactly the one line change of binding decision 1.
2. Run the full local Compose smoke journey
   (`sh tools/compose/smoke.sh slaif0075a` run class) and record the
   final status lines: all browser projects PASS, `compose-e2e: OK`,
   `public-agent-acceptance: OK`.
3. Run `python tools/check_repository.py` (PASS).
4. Commit the implementation change (implementation head), push, then make
   the report-only `SELF` commit (parent = this round's implementation
   head).
5. Commit the activated order and `oap/active` for this round
   byte-for-byte unchanged with the implementation.

## Observable acceptance criteria

1. This round's diff is exactly one line in exactly one file (`"navigation": 2`
   to `"navigation": 3` in the news journey structure summary; the
   component journey line untouched).
2. The full local Compose smoke run passes end-to-end, including
   `public-agent-acceptance: OK` (exact final status lines recorded).
3. On the exact report-only head of this round: `Compose and edge
   packaging` is green, and every required GitHub check is successful
   EXCEPT `Supply-chain evidence`, which is expected red solely due to the
   documented external CVE drift (the six CVE-2026-917xx items in the
   unchanged browser-worker image; resolution is the separate 078/6
   browser security refresh increment, merged before this PR's final
   merge gate). The report must record each check's conclusion on the
   exact head.
4. The report contains per-criterion evidence (pass/fail/skip/not-run)
   and the cumulative base→head size grouped per review-unit governance
   §2 (base = `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`).

## Verification

Local: full Compose smoke journey; repository policy check.
Remote: required CI matrix on the exact head; Strategy independently
reviews the one-line round diff plus the cumulative 078-5-a + 078-5-b +
078-5-c diff. The PR's final 20/20 merge gate is deferred to the
post-078/6 round (078-5-d) which re-verifies the full matrix after the
browser security refresh merges into main.

## Security

No authority, scope, or trust surface changes. No assertion is weakened
beyond correcting one stale structural pin to the ordered post-feature
DOM value proven by live capture. No secrets in diff or report.

## GitHub workflow

AMENDED_EXISTING_PR: same branch
`oap/078-5-a-global-regions-header-footer`, PR #85, base
`d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`. All commits pushed; report
commit is `SELF`; Strategy is the only merger (merge deferred per the
verification section).

## Report requirements

Standard OAP report template plus explicitly:

- the exact one-line diff;
- the final status lines of the local Compose smoke run;
- the conclusion of every required GitHub check on the exact report-only
  head;
- confirmation that no other evidence field or assertion changed;
- the cumulative base→head size grouped per review-unit governance §2
  (this round's delta and the 078-5-a + 078-5-b + 078-5-c cumulative).

## Predeclared review budget (review-unit governance §1)

- Production/config files: 0 (one evidence-tool file, one line)
- Migrations: 0
- Test/evidence footprint: existing frozen journey re-run (no new tests)
- Generated-contract footprint: none
- Docs footprint: none
- OAP transcript footprint: order + report
- Expected substantive implementation scale: 1 line
- Review trigger: cannot fire; cumulative size is 078-5-a + 078-5-b plus
  one line.
