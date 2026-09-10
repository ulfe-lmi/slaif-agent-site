# OAP Work Order — 078-s: prove actual Agent theme output

- Objective078; increment078/2; round078-s; AMEND_EXISTING_PR.
- Existing [PR #79](https://github.com/ulfe-lmi/slaif-agent-site/pull/79),
  branch `oap/078-2-site-theme-tokens`; base `main`.
- Verified main `3cae3d6cef2a92e7068856d21bc9a47b8190c22e`.
- Starting report head `7803a6e4c8a6a7136fd1897210190a859855cbc4`, report-only
  child of implementation `9d9e6470efb69e4e410191be026666d94ef323d3`.
- PR79 remains open; no new PR or agent. Numeric078 remains PARTIAL.

## Evidence-only closure; do not reopen verified production repairs

Strategic review has verified the R lifecycle-before-theme lock, exact function
preservation, and CSS repair. Independent Chromium computes Grid0px desktop/
8px mobile and transparent ghost. Independent real-PostgreSQL lifecycle/race
tests pass2/2. D1/D2 had already been independently reproduced and closed.
Preserve those implementations; this order adds missing acceptance assertions
and accurate diagnostic/current-documentation evidence, not another feature.
If this focused production-boundary proof exposes an actual theme defect,
repair it minimally in scope; do not mock or bypass the failing product path.

## 1. V2 still does not assert the selected theme appears

`_run_primary_theme_browser_proof` currently validates workspace binding, PNG
signature, artifact hashes, main-count1 and one stylesheet. It never checks a
theme token or rendered style. It would pass if Agent preview always used the
canonical ocean defaults while Agent GET/theme returned meadow.

The new `preview.spec.ts` token test injects DOM nodes and changes className
using page.evaluate. Retain that as useful CSS-level qualification, but it is
not proof of product behavior through the Agent interface. The existing HUMAN
Editor test is also not a substitute for the Agent workspace path.

Close precisely this gap using a real human-issued capability and the existing
public Agent/NGINX/authorized preview/browser path:

- PATCH representative values in palette, typography, layout and shape through
  the actual public Agent API; retain its returned record/version/workspace.
- Observe the SAME workspace's real rendered HTML and browser DOM without
  changing DOM/classes/styles or seeding theme outcomes with owner SQL. Assert
  actual expected theme classes and computed style values; use existing
  approved components created through Agent APIs when needed to observe
  shape/shadow/gap. No new component or product browser tool is needed.
- Prove canonical and other workspace/site still use their original theme,
  and preview stays private/no-store/noindex. Preserve the existing real Agent
  restart/readback/exact replay test.
- Demonstrate the test detects wrong output: temporarily exercise a local
  negative control where Render projects canonical/default theme for the Agent
  workspace and show this exact acceptance assertion fails, then restore the
  unmodified production implementation. A controlled test fixture/mutation is
  acceptable only for proving test sensitivity, never the passing product path.
- Keep capability/cookies/preview credentials out of URLs/logs/committed files
  and public artifacts. Use existing secure fixture plumbing; no raw browser
  execution API, new authority, or Objective081 workspace-selection feature.

## 2. Restore the required final re-upgrade assertion

R correctly starts `test_agent_065_theme_data_round_trip_preserves_legacy_state`
from genuine064 and compares all five functions/semantic constraint. However,
it removed the final upgrade back to head. Add that final064→065 step and
assert valid theme data, new schema/function contracts and applicable privilege/
readiness continuity after re-upgrade. Preserve fresh baseline, exact downgrade
checks, and pending-COW safety. Run this focused test; no full33-minute local
integration rerun for this evidence-only change.

## 3. Honest, useful failure evidence without suppressions

R could not reconstruct the historical Firefox failing endpoint because no
request/trace detail was retained. Passing reruns do NOT prove its cause was
transient infrastructure. Preserve the historical failure and state precisely:
exact cause unknown/not reproduced; current targeted runs passed. Do not invent
certainty or keep repeating a historical diagnosis that cannot be recovered.

Make the minimal safe diagnostic improvement for future response failures in
the existing E2E observer/reporter: preserve method, numeric status and a closed
route-family classification, without raw URL/query/path identifiers, payload,
headers, cookies or credentials. Keep the original failure assertion effective;
add focused sanitization/known-failure tests. No broad observability refactor,
raw trace uploads, weakening of redaction, ignored failures or retry-until-green.
If a current required check actually fails, diagnose its concrete evidence and
make only the necessary scoped repair; do not manufacture a new exception.

## Verification and current truth

Run the focused real Agent-to-preview proof, its negative control, the one
migration round-trip test, diagnostic tests, affected quality checks and all
required exact-head CI. CI may provide broad matrix/Compose qualification;
avoid duplicating unchanged full local suites. All required checks must pass
before strategic merge. Report exact commands, assertions, revisions and honest
pass/fail/skip/pending status, not inherited suite totals as proof.

Reconcile current API/testing/README/MVP/increment and whole-PR descriptions.
In particular, docs/API.md still says the order does not implement site-global
theme tokens immediately after describing their implementation; fix that stale
non-goal while retaining global regions/header-footer/page-style/catalog and
later objectives as deferred. Do not alter historical orders/reports. A final
report-only SELF head, not its implementation parent, is the merge-gated head.

PR is62files,+7376/-625 including generated contracts/tests/OAP. No new semantic
family may enter it. No global regions/page style/catalog/media/MCP/exact-workspace
Puck/lifecycle/publication, dependency upgrade, security exception, gate weakening
or unrelated cleanup. Existing coder only; routine safe setup remains its
passwordless-sudo responsibility. Stop on actual external/safety blockers, not
mere missing evidence this order explicitly asks you to implement.

Commit exact order and active078-s with scoped proof/docs changes; push PR79.
Publish `oap/reports/078-s-prove-agent-theme-output.md` as the final report-only
SELF child of the literal pushed implementation SHA, with each criterion's
actual evidence, files/size, current checks and remaining limitations. Lint
Markdown before publication. Never merge/auto-merge/create another PR.
Send exact responseFIFO OK only after remote report publication, then wait with
the real byte-consuming control listener. Open-only `exec 3<...` is not a reader.
