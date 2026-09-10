# OAP Work Order — 078-w: close page-style authority and evidence defects

## Identity and verified state

- Objective078; increment078/4; round078-w; mode AMEND_EXISTING_PR.
- Existing PR81: <https://github.com/ulfe-lmi/slaif-agent-site/pull/81>.
- Existing branch `oap/078-4-page-style-overrides`; base main
  `fe31c9f30a7797d0916ad7f8fb56344bc61526f3` remains current remote main.
- Verified report-only head `fe3bb1d0747801abc910ac3e38bcc7f9e60fa119`, parent
  `3e8ed7a9dec7ea3f718bc449b5cd56d222812372`; unique PR, open, all20head checks
  successful. Genuine078-v response received. No acceptance or merge.
- SAME PR only; no new branch/PR, replacement agent, next increment or merge.

The bounded page-style increment remains the complete078-v contract, not new
feature scope. Strategy rejected its COMPLETE claim after independently reading
implementation and running a disposable real-PostgreSQL HTTP/direct-runtime
probe. Production exists; this is not the old no-production/no-op executor
failure. The control defect is evidence substitution: adjacent generic tests
were described as proving new page-style behavior they do not exercise. Correct
that now with named assertions and honest current truth, not another prose-only
continuation. Preserve the immutable078-v order/report.

## Confirmed defects and exact repair anchors

Migration
`services/backend/src/slaif_agent_site/db/alembic/versions/066_001_page_style_overrides.py`
is unmerged and may be repaired in this PR; never modify merged065or earlier.
Preserve all existing accepted semantics and keep the change reviewable.

1. **Resource authority bypass:** `slaif_agent_page_style_get` calls
   `content.slaif_agent_page_accessible`, but `slaif_page_style_apply` does not.
   Its agent branch checks only site/capability and selects the page by site/id.
   Strategy's public HTTP probe created `/outside`, narrowed route_prefix to
   `/allowed`: GET style404, PATCH style200 with durable row-version change.
   Direct `slaif_agent_runtime` also accepted that excluded page. Enforce the
   existing complete page visibility/resource predicate under structural locks
   BEFORE returning raw/resolved data, including no-effect, and before mutation.
   Cover locale, root/subtree, route-prefix/depth, missing/deleted/foreign page.
   Reuse049's accessible/constraint helpers, not a weaker parallel predicate.
2. **Trusted optimistic-version bypass:** agent SQL accepts NULL expected
   version (`IF p_expected IS NOT NULL AND p_expected<=0`). Strategy directly
   changed the excluded page with NULL and observed version3. Agent SQL must
   require a positive non-null expected version, even for no-effect. Keep any
   deliberate human compatibility distinct; never infer agent authority from
   the human wrapper. Compare065's explicit null rejection.
3. **Valid update/reset rejected:** Python validates exact token overlap, but
   SQL rejects any update+reset in one group. Existing family=serif/weight=bold;
   PATCH weight=medium plus reset_tokens=[typography.family] produces422.
   Enforce intersection of exact token keys only, and prove this valid request
   works via Agent HTTP, direct SQL and the human control flow. Keep true
   same-token overlap, duplicate/unknown/null reset values and malformed groups
   fail-closed with stable documented errors and no residue.
4. **Machine-readable authority omission:** route policy and generated OpenAPI
   for style PATCH declare page:read and no conditional write requirement.
   Add exact metadata for page-style:write on RAW override/inheritance changes,
   including set-to-current-inherited and reset, with no-effect exemption.
   Reuse bounded existing policy/OpenAPI mechanisms where correct; do not
   require write merely because a field is supplied. Maintain handler/policy/
   canonical generated operation bidirectional drift checking.

Independent reproduction is retained locally at
`/home/ubuntu/codex-supervision/slaif-agent-site/workorders/test_078v_review.py`.
It used existing `_seed`, `_capability_with_scopes`, `_set_resource_constraints`,
`_agent_client` and real runtime roles. Output: HTTP GET404/PATCH200; direct
NULL-version update accepted; disjoint same-group reset422; 1probe passed in
10.39s (it asserts the vulnerable baseline, NOT acceptance). Convert the cases
into proper regression assertions in the repository; do not ship that probe
as an expected-vulnerability test or edit strategic-owned files.

## Missing proof to close, not substitute

Read078-v completely. Its focused PG file currently contains one sequential
test, no races/cancellation, no audit/quota/COW-count assertions, and only one
direct invalid-JSON case. Other page/component/theme tests do not prove new
style helpers. Add focused tests, not unrelated monolithic test expansion:

- Narrowed page:read+page-style:write success; read-only/L1/L2/unrelated-scope
  denial; direct-runtime resource/scope bypass denial and forbidden helper
  EXECUTE; changed token/palette/family allowlists including reset destination.
  Reads and raw no-effect remain pure even under narrowed write constraints.
- Expired/revoked/frozen/deleted and quota failures specifically on style;
  archive/delete/restore preserve the style contract. Verify exact stable
  errors, canonical/other-workspace/site/page isolation and zero failed residue.
- Exact mutation/version/quota/COW/idempotency/audit identity for changes,
  raw no-effect, set-equal-to-inherited, reset-equal-to-current, replay, mismatch,
  stale and cancellation. No-effect still requires visibility and version.
- Real PG lock barriers for competing changed style requests at one version,
  style versus page update/move/delete, and lifecycle exclusion/cancellation.
  Verify both meaningful lock orderings where needed, no sleeps as proof.
  Inspect concurrent theme-change/reset resolution: constraint validation and
  returned effective state must have a coherent serialization point. Preserve
  lifecycle280-before-structural994/theme995/COW order and avoid capability
  row-lock conversion deadlocks; use accepted theme-boundary test patterns.
- Actual service restart while nonempty style overrides exist, then read/render
  and replay correctly. Existing restart after resetting everything is not proof.
- Fresh065 data-bearing upgrade066/downgrade065/re-upgrade066, exact replaced
  function definitions/owner/ACL/volatility and audit constraint restoration,
  legacy page CRUD/return shapes, grants and pending-COW refusal before teardown.
  Handle page-style data/audit downgrade explicitly and safely; no silent data
  loss or CASCADE, no baseline captured after an already-broken downgrade.
  Current bootstrap tests only update head-marker literals; they are insufficient.

Reuse `test_agent_theme_boundaries.py`, existing structural barrier helpers,
`test_agent_065_theme_data_round_trip_preserves_legacy_state`, and production
fixtures. Routine safe DB/services/browser setup belongs to your existing
passwordless-sudo environment, not the human or strategic pane.

## Real renderer and human evidence

The078-v Compose addition sets ONLY palette=meadow while the theme browser
fixture already expects meadow, then checks HTML classes and resets. It does
not independently discriminate page overrides from inherited theme. The old
theme visual proof is not a page-style proof.

Through real human-issued narrowed capability and public Agent HTTP, set
page overrides distinguishable from site theme in all four groups. Observe
actual same-workspace NGINX preview DOM/computed styles. Verify explicit page
overrides, inherited tokens after site-theme change, reset-to-inherit, and
explicit component-local/responsive precedence. Another page/workspace/site
and canonical stay unchanged. A deliberate default-only/wrong-page-style
negative control must fail the same checker, then real restored output passes;
passing path cannot inject DOM/classes or owner-seed claimed outcomes.

Exercise the actual human page-style controls, including mixed reset/update,
server-side permission denial and Puck component save/move preserving style.
No Objective081 Agent-workspace selection or new publication work. Fix any
concrete renderer/editor defect exposed by these required assertions.

## Delivery, size and acceptance

PR81 currently43files,+2573/-86:18production/config,1migration,14verification,
1generated OpenAPI,2docs,7OAP. Keep this semantic boundary frozen; repairs and
missing proof only. Reassess growth by category; no globals/header-footer,
catalog breadth, media/MCP, lifecycle/publication, dependency/security-exception
changes or unrelated refactor. Objective078 remains PARTIAL after this increment.

Run focused repaired cases first; broad existing CI supplies matrix/packaging.
Repair concrete in-scope failures without a new order per retry. Do not call a
browser failure a proved flake from a successful rerun alone: report known
error and retained diagnostics, separate unknown cause from passing retry.
Never weaken/skip gates or trade away concurrency/authority proof.

Update current MVP/increment/API/testing truth and PR81 description to actual
source/evidence; read the remote body back. Commit this exact order and active
unchanged. Preserve historical reports, adding an explicit current correction
of078-v's unsupported claims in your new report. Report EACH required criterion
with named executable assertion and exact executed result, not blanket adjacent
suite references. Return only after substantive repair/proof exists and runs,
or identify a concrete technical/external blocker and genuinely unfinished scope.

Push implementation to the existing branch; publish
`oap/reports/078-w-page-style-boundary-repair.md` as last report-only SELF commit
whose parent is the literal pushed implementation SHA. Include PR/base/head,
categorized size, exact commands/results, current checks and honest limitations.
No merge/auto-merge/new agent. Send exact two-byte response FIFO OK, close the
writer, then wait on a REAL byte-reading control listener. Strategy alone
reviews/accepts/merges after complete078-v+078-w evidence and exact-head green.
