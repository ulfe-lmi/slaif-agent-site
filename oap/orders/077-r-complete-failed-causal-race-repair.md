# OAP Work Order — 077-r

## Recovery status and verified state

This is execution recovery for the unfinished 077-q substance, not a new
ordinary feature slice. Amend only
[PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), branch
`oap/077-agent-site-structure-semantics`, base `main`; create no PR and never
merge. Required starting remote report head is
`3d946e60f240aaa77ebd72e0921eb9fe5bf8e41a`, whose sole parent is 077-q
implementation `ba0c7e20e37ccbef526d57ee6acfa9b3f8778f74`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

077-q correctly repaired preview row-lock authorization but returned before
repairing ordinary in-scope code defects and its report incorrectly says the
causal preview proof passes. The retained test still calls
`release_snapshot.set()` before awaiting the Agent commits. Do not return
`PARTIAL`/`BLOCKED` for the known failures below: they are implementation work,
not an external blocker. Finish them, the post-tentative locale cancellation,
and actual lifespan proof before reporting.

## 1. Use pre-statement locks where snapshot freshness matters

An advisory lock acquired inside a mutating SQL wrapper does not by itself
guarantee that the wrapper's statement snapshot was taken after the competing
transaction committed. The earlier global exclusive lifecycle key masked this.

Restore a narrow trusted pre-statement acquisition for structural mutations:

1. lifecycle key namespace 280 in shared mode;
2. workspace+site structure key namespace 994 in exclusive mode;
3. only then execute the page/locale/navigation/redirect mutating wrapper as a
   new SQL statement with a fresh `READ COMMITTED` snapshot.

Use one trusted helper/path shared by Agent and Editor; do not duplicate
resource authorization or domain validation in Python. Capability/session/site
authentication occurs first; the lock helper may only derive/validate the
trusted workspace/site context and acquire locks. SQL wrappers must retain
their own lock/validation defense in depth. Keep lock order identical across
interfaces and do not pre-lock read-only routes or unrelated content writes.

Re-run the exact page-delete versus redirect-target-update race in both forced
serializations. Redirect update first must commit, then page delete returns
200. Page delete first must return the stable dependency conflict (409), then
redirect update returns 200. A true absent/invisible page remains 404; stale
version remains 409. Capture the exact SQLSTATE/call stack if any valid ordering
still returns 404, repair the function rather than expanding accepted statuses.

Also repair the earlier page/navigation create/delete and Editor/Agent races;
the complete `test_editor_agent_structural_races_share_workspace_site_lock`
must pass without weakening assertions. Prove no route/redirect/navigation/
page, quota, idempotency, audit or COW residue for losers/cancellations.

## 2. Serialize content-type dependency creation/deletion explicitly

The independently reproduced `race_view_and_type` produced two successes:
`CONTENT_TYPE_DELETED` (200) and `COLLECTION_VIEW_CREATED` (201), leaving a view
bound to a deleted type. Migration 048 overrides the type-delete wrapper without
the 047 type-definition advisory key, while collection-view create uses a
different per-view key.

Introduce/reuse one deterministic workspace+type dependency lock, acquired as
a separate trusted statement before the wrapper, for both:

- content-type update/delete and any operation that creates/deletes a direct
  type dependency; and
- collection-view create/update/delete at minimum.

Retain the same lock inside wrappers for defense in depth, but do not claim it
alone supplies the fresh post-wait snapshot. Review the already ordered field-
and item-versus-type races for the same masking pattern; use the common parent
lock wherever a type can be deleted concurrently with a new field/item/view/
translation/relation dependency. Avoid a new global workspace-exclusive lock.

Use deterministic two-connection barriers for both commit orders. Exactly one
operation succeeds; the other is stable 404/409/422 as semantically applicable;
the final type/dependency graph is valid. Direct trusted wrapper attempts and
public Agent HTTP must agree. Retry after loser rollback remains valid and
charges/audits exactly once.

## 3. Replace, do not retain, the false causal preview test

With 054's no-touch shared-row recheck and the pre-statement structural lock:

- establish the preview `REPEATABLE READ` snapshot using actual structure data;
- pause Render;
- execute and **fully await successful durable Agent commits while Render is
  still paused**;
- independently assert those after-values are committed;
- only then release Render;
- require the paused projection's page/locale/navigation/composition/theme/
  bindings/route result to be the complete before-state and a fresh render to
  be the complete after-state, including the new redirect result.

Delete or rewrite the release-before-await block; it cannot remain described as
causal evidence. Keep the valid canonical companion and explicit
`READ COMMITTED` mixed-state negative control, and make the preview case fail if
production isolation is downgraded. No timing sleeps establish order.

## 4. Finish cancellation and restart requirements

Add the exact post-tentative locale test: pause after the production locale SQL
wrapper and graph validation return but before generic completion/audit; cancel;
prove rollback of locale/default/effective routes/redirect/navigation/quota/
idempotency/audit/COW; retry the identical key successfully.

Retain direct post-cancel pool assertions for canonical/preview. Add an actual
Render application/database-adapter lifespan stop and fresh start, then resolve
the same durable authorized overlay and unchanged canonical state. A new service
object within one unchanged lifespan is not restart evidence. Preserve browser
one-time cancellation/consume semantics.

## 5. Preserve security and contract closure

All current image work is closed for this slice: Ubuntu Apache and Postgres
`libcurl=8.22.0-r0`, all six images zero Critical, empty exceptions. Do not
modify pins/policy unless a genuinely new current-head failure requires it.

Run the two exact formerly failing tests first; deterministic forced-order
dependency/structure races; causal preview+canonical+negative control;
post-tentative locale; pool/lifespan/browser tests; then full Agent/Editor/
Render/bootstrap integration, migration/privilege, Python quality/unit/
integration, Node, PG14–18, repository/Markdown/Mermaid, clean Compose/public
journeys/Apache parity, complete supply chain, and all current-head CI. Push
before observing CI; repair in-scope failures. No pending/skipped/superseded
result is pass.

No dynamic `{slug}`/collection detail; no new public feature/route; no 078
composition/design/Puck; no media/MCP/freeze implementation/review/promotion/
source/sweep/076; no architecture/historical order/report edit/general refactor/
production/release/exception/issue closure. Preserve all accepted 077 behavior,
054 authorization, migration 053, public browser workflow, redirect headers/
statuses, and site/workspace/canonical isolation. GitHub issue #67 stays open
until verified Objective 077 merge.

Commit this exact order and `oap/active` unchanged, push only the existing PR,
create no PR, never merge. Publish exactly
`oap/reports/077-r-complete-failed-causal-race-repair.md` as a report-only
child of a correct literal implementation SHA with
`Report publication commit: SELF`. Include exact pre-statement/inside-wrapper
lock keys/order; both forced outcomes; common type-dependency lock coverage;
causal commit-before-release chronology; post-tentative rollback/retry; actual
lifespan restart; commands/counts/current checks; security preservation; no
secret/scope/extra PR/merge/exception; remaining dynamic/final 077 scope; and
strongest reason not to accept.

Do not signal completion until production fixes and tests exist and both
formerly failing suites pass, unless a genuinely external DB/GitHub/tool outage
prevents execution. An ordinary failing test, coding difficulty, or newly
understood in-scope defect is not `BLOCKED`; repair it within this turn.
