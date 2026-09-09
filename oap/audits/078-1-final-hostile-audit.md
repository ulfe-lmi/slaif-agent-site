# PR 77 final hostile audit — increment 078/1

Strategic audit, 2026-09-09. Verified base/main:
`ae3a4a681bb888260192b7bb1b2a337b4906828d`. Audited PR head:
`6de7e088153b09cb0950d9b9b93e940ba535a4dd`; implementation parent:
`41b7f7d487c8f022537b34946e09c76a8a3fc7bf`. All 20 checks SUCCESS.

Boundary: component composition/data plane and component-local design only.
078-i theme product diff is removed; its commit and immutable transcript survive.
Current diff: 92 files, +24,270/-3,443 (including generated, test and OAP artifacts).
Verdict on this revision: **REJECT — repair findings below before merge**.
This is the requested whole-PR audit. Later review closes these findings and
checks regression/diff scope; it does not restart a broad objective audit.

## Independent verification

The strategic model ran its own disposable PostgreSQL/public HTTP diagnostic
before and after 078-j. A (design REMOVE) and B (L2 initial design CREATE) were
confirmed for Button.variant, Image.aspectRatio and CollectionGrid.columns.
At the audited revision, HTTP CREATE denies L2 with 403 and direct runtime
CREATE/REMOVE denies with AGENT_SCOPE_DENIED. Valid Heading PATCH replay changed
from the reproduced 200/409 bug to correct 200/200.

Report-only SELF parent/path, unchanged order hashes, immutable theme history,
current main/base and all 20 current-head checks were independently verified.
Existing code/test review covers COW isolation, semantic quotas/audit/idempotency,
workspace structural locks, true two-waiter race regressions, cancellation,
restart proof, catalog source/generation and the deployed component loop.

## Findings requiring closure

| ID | Finding and implementation evidence | Required closure |
|---|---|---|
| F1 | 061 design validation unconditionally removes alignment before checking the catalog. Direct runtime Button update persisted `alignment: {script: evil}` under content-only scopes. Python also strips alignment irrespective of component support. | Reject unknown property/type and validate the full JSON before any trusted projection; direct-runtime and HTTP regression with unchanged effects. |
| F2 | 062 CREATE calls scalar `slaif_agent_component_validate`. Strategic fully-authorized responsive CREATE for Button, Image and CollectionGrid all returned 422. | Use the same complete design validator and exact initial-authority rule; prove scalar/default/responsive creation through HTTP and runtime. |
| F3 | Actual Chromium computed styles: Section narrow has max-width none at all sizes; Spacer mobile-xl remains 16px; Grid desktop=4/tablet=2 becomes 1 on mobile despite declared fallback. No Section variant or responsive Spacer CSS selector exists. Responsive default/reset values also need complete mapping. | Every advertised existing local design choice must have its documented computed layout/style, including fallback and resetting to primary/auto/default. Real-browser computed-style tests, not class substring assertions. |
| F4 | Legacy Editor add/update/move in 060 still call scalar validation; Puck advertises responsive maps but Editor cannot save them. | Existing authorized human workspace/Puck saves supported design values through the production Editor path; same validator and correct human permissions. No new exact-Agent-workspace selection feature. |
| F5 | 062 downgrade restores CREATE and authority but leaves its replaced component UPDATE function at 062 semantics; the test checks only CREATE source. | Restore all changed 061 function definitions/privileges exactly and prove data-bearing downgrade/re-upgrade. Guard incompatible 061-to-060 design state without loss. |
| F6 | Current MVP docs still say GitHub records whether 077 merged and mix future 081+ into the reason 078 is partial; PR body emphasizes round history over the retained behavior. | State accepted merged PR74/main SHA as fact; distinguish increment 078/1, remaining 078 and later objectives; concrete PR description. |
| F7 | New whole-file Markdownlint ignores for 078-j and governance, plus repository-policy allowlisting, violate the human no-weakening instruction. Claimed hash verification is not implemented by the policy diff. | Remove new ignores/allowlisting, format mutable governance; final blank-line correction of immutable 078-j requires the narrowly requested human override. Preserve original in Git. |

## Scope and merge decision

No theme or later feature may be added to resolve these findings. The remaining
increment after PR77 is bounded site-theme tokens in a fresh PR from accepted
main. The existing cumulative size is a closure exception explicitly authorized
by the human, not a template for subsequent PRs. Merge only after these findings
are closed, required checks pass on the final head, truth agrees, and strategic
acceptance is recorded. Objective 078 remains PARTIAL after this increment.
