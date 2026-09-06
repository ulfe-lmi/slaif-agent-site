# OAP Work Order — 077-s

## Execution-control recovery and verified state

This remains completion of the failed 077-q/077-r repair, not ordinary feature
decomposition. Amend only
[PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), branch
`oap/077-agent-site-structure-semantics`, base `main`; create no PR and never
merge. Required starting remote report head is
`eb82a11ae7cc98a981e63c4d4fd9adf0234159a1`, whose sole parent is 077-r
implementation `46ff188b91074c02ba95e8e5fc39e57781fe41f0`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

077-r violated its explicit no-early-return condition: it fixed the type/view
dependency race but returned `BLOCKED` on one ordinary in-scope race and left
two explicitly required tests unwritten. Do not create another no-op report.
Do not return until the exact page/redirect race is 200/409, post-tentative
locale cancellation exists, actual Render lifespan restart exists, focused/full
tests pass, and current-head CI is resolved, unless a genuine external service/
DB/tool outage prevents execution.

## 1. Diagnose and repair the transient page-delete P0002

Exact strategic reproduction at current head:

- `test_editor_agent_structural_races_share_workspace_site_lock` races Agent
  DELETE of page `P` against Agent PATCH of redirect `R` from target `P.route`
  to external HTTPS behind the namespace-994 barrier.
- Redirect update returns 200 and commits; page delete returns 404
  `RESOURCE_NOT_FOUND`.
- Owner inspection afterward shows `P` still present as the workspace page
  change at row version 1, and `R` present at row version 2 with the external
  target.
- In a new trusted COW transaction with the same workspace/site/capability,
  `content.slaif_agent_page_delete(site,P,1)` succeeds and returns the expected
  tombstone (the diagnostic transaction was rolled back).

Thus 404 is not valid absence. Capture the exact originating P0002 message and
function during the concurrent request before error translation. Instrument
only tests/internal diagnostics; do not leak DB messages publicly. Inspect:

- `content.slaif_agent_page_delete` and its 051 base;
- `slaif_redirect_page_target_dependency`;
- `slaif_redirect_page_guard` / `slaif_redirect_validate_state`;
- `slaif_redirect_source_conflict` and
  `slaif_redirect_static_target_exists`; and
- effective-route evaluation over COW-created/tombstoned rows.

Force both serialization orders deterministically, not by scheduler luck:

1. redirect update commits first; page delete must then return 200;
2. page delete evaluates first while dependency exists; it must return stable
   409 and leave the page, after which redirect update returns 200.

Use the trusted pre-statement lifecycle-shared/structure-exclusive lock and a
fresh wrapper statement snapshot. Repair any helper that treats a concurrently
hidden/tombstoned iterator row as a top-level PAGE_NOT_FOUND; complete-graph
validation must skip a row already excluded from the resulting graph while
still failing closed on genuine corruption. Do not catch all exceptions,
convert real absence to conflict, expose hidden IDs, accept 404 in the race, or
remove dependency validation.

The full Editor/Agent structural suite must pass unchanged. Prove exact final
page/redirect state, one permitted winner, no dangling edge, correct
idempotency/quota/audit/COW rollback and same-key usability.

## 2. Finish post-tentative locale cancellation

Implement the already specified focused test using the production Agent HTTP
executor. Pause only after `AgentCowContentModelService.update_locale` (or the
exact production locale service method) has returned from the SQL wrapper and
migration 053 graph validation, but before generic idempotency completion and
audit. Cancel the request, release the event, and prove:

- target and former-default locale rows/versions/default flags unchanged;
- effective routes, navigation and redirects unchanged and valid;
- mutation/delete quota unchanged;
- no idempotency completion/reservation, semantic audit or COW operation
  residue; and
- retry with the identical idempotency key succeeds exactly once with the
  expected row versions/quota/audit/operation identity.

This is ordinary test/implementation work, not a blocker.

## 3. Finish actual Render lifespan restart proof

Using real PostgreSQL public/preview pools and the production Render app
factory, start the application lifespan, render the durable human-authorized
workspace overlay and canonical page through the internal HTTP route, stop the
lifespan/database adapter completely, start a fresh Render app/adapter instance,
and render the same overlay/canonical state again. Assert authorization,
no-store/noindex, site/workspace isolation and cleared connection context. A
new service object inside one lifespan is insufficient.

Preserve and rerun the now-correct causal preview/canonical/`READ COMMITTED`
proof from 077-r. Verify its source literally awaits successful durable Agent
commits before `release_snapshot.set()`; remove the historical false block if
still present or make it an explicitly non-acceptance regression that cannot be
misread as proof.

## 4. Preserve closed repairs and finish gates

Preserve 054 touch/recheck lock modes/grants; shared lifecycle + pre-statement
structural/type locks; common type dependency coverage; migration 053; public
Agent-created browser proof; exact redirect statuses/headers; Ubuntu Apache and
Postgres libcurl overlays; all six images zero Critical; empty exceptions.

Run the exact structural race repeatedly in both forced orders; dependency
matrix; post-tentative cancellation; lifespan restart; causal Render and pool
cleanup; full Agent/Editor/Render/bootstrap integration; migrations/privileges;
Python quality/unit/integration; Node; PG14–18; repository/Markdown/Mermaid;
clean Compose/public journeys/Apache parity; full supply chain; then all current-
head CI. Push before CI and repair only in-scope failures. No pending/skipped/
superseded result counts as pass.

No dynamic `{slug}`/collection detail; no new public feature/route; no 078
composition/design/Puck; no media/MCP/freeze implementation/review/promotion/
source/sweep/076; no architecture/historical order/report edit/general refactor/
production/release/exception/issue closure. GitHub issue #67 remains open until
verified Objective 077 merge.

Commit this exact order and `oap/active` unchanged, push only the existing PR,
create no PR, never merge. Publish exactly
`oap/reports/077-s-finish-race-cancellation-restart-recovery.md` as a report-
only child of a correct literal implementation SHA with
`Report publication commit: SELF`. Include exact P0002 origin/root cause/fix;
both forced 200/409 outcomes; full unchanged-suite result; post-tentative
rollback/retry counts; real app stop/start HTTP evidence; causal source order;
commands/counts/all current checks; security preservation; no secret/scope/
extra PR/merge/exception; remaining dynamic/final 077 scope; strongest reason
not to accept.

`BLOCKED` is permitted only for a named external outage/access failure after
the production fixes and tests have actually been attempted. A reproducible
code defect, failed assertion, difficult debugging, long test, or remaining
in-scope implementation is not a blocker and must not end this turn.
