# OAP Work Order — 077-q

## Objective and verified state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`61e6931b4ce5587816f07516217060a3071439c8`. Its actual sole parent is 077-p
implementation `20c238909b7be7d0cc65894cdd93c4c29ace4b57`. The immutable
077-p report contains a one-character typo (`...b7e7...`) in that literal SHA;
do not edit it. Record this reconciliation in the 077-q report and use Git
parentage as authoritative. Remote `main` remains
`067676314e0d9664d40cb8514ea549b966a4eb2d`.

Accept the 077-p shared advisory-lock and Postgres zero-Critical repairs for
progression, not objective completion. Repair the remaining preview row-lock
blocker, remove the pre-lock regression, and finish the causally valid Render/
cancellation evidence. No dynamic `{slug}` behavior.

## 1. Separate short touching authorization from long read-only recheck

The exact remaining blocker is migration 034's
`control.slaif_render_preview_authorize`: the second call inside the preview
COW/`REPEATABLE READ` transaction holds `FOR UPDATE` on `control.workspace`
and `control.user_session` until rendering ends. Agent mutation calls
`control.slaif_agent_require_cow_site`, which requires `FOR SHARE` on that same
workspace row, so it cannot commit while Render is paused even after the
advisory lifecycle lock was corrected.

Implement one authoritative authorization policy with two narrow entry points:

- initial authorization/touch: short autocommit transaction, lifecycle shared
  advisory lock, serialized session touch where required;
- in-snapshot recheck: no touch/update, lifecycle shared advisory lock, session
  and workspace shared row locks only, identical identity/site/workspace/
  membership/permission/state/expiry/recent-auth decisions.

A safe pattern is a private SECURITY DEFINER helper parameterized internally by
touch mode plus two fixed public wrappers; untrusted callers must not select an
arbitrary lock/touch mode. Render preview role receives EXECUTE only on the two
narrow wrappers, not the private helper or control tables. The second Render
call must use the no-touch recheck.

Shared row locks must allow Agent/Editor `FOR SHARE` state rechecks while still
blocking concurrent workspace-status or session-revocation UPDATE until the
current preview finishes. Do not remove the second authorization, weaken state/
membership checks, make preview renewal extend recent auth, or expose a token/
row oracle. Preserve browser authorization independently.

Use an exact reversible migration unless a provably safe amendment to an
unmerged migration covers both fresh install and upgrade paths. Verify owner,
`search_path`, `PUBLIC` denial, preview-only grants, data preservation and
downgrade/re-upgrade restoration.

## 2. Remove the Python pre-lock regression, retain DB lock order

077-p added pre-reservation structural locks in
`agent_state/mutations.py` and `editor_api/database.py`. The existing SQL
wrappers already take lifecycle-shared then structure-exclusive before content
mutation reads. The duplicate Python pre-lock changes race ordering and caused
two established tests to return 404 where stale/concurrent outcomes must be
200/409.

Remove the redundant Python pre-lock path unless evidence proves one exact
operation performs a content decision before its SQL wrapper. If such an
operation exists, move that decision behind the database lock rather than
globally pre-locking every structural request. Retain migration 028/050 shared
lifecycle mode and namespace-994 exclusive structural serialization.

Restore and prove the existing contracts:

- `test_agent_final_dependency_matrix_and_two_connection_delete_races`;
- `test_editor_agent_structural_races_share_workspace_site_lock`;
- stale version/idempotency loser is 409, invisible truly absent resource is
  404, exactly one permitted winner, and no dependency/route corruption;
- no reservation/quota/audit/COW residue for loser/cancellation.

## 3. Complete the causal snapshot proof

After the row-lock repair, retain Render paused after an actual query against
the selected structure and fully await public Agent/Editor commits before
release. Assert the commits are durably visible on a separate connection while
Render remains paused. Then:

- preview `REPEATABLE READ` returns a complete page/locale/navigation/
  composition/theme/binding/route before-state;
- a fresh preview returns the complete after-state, including redirect decision;
- canonical remains unchanged for workspace writes;
- a canonical companion, using one atomic owner fixture update solely to model
  a promotion commit, returns complete before then complete after state; and
- an explicit `READ COMMITTED` negative control with the same staged query
  boundary observes mixed/after data and therefore fails the coherence
  assertion, proving the production isolation level matters.

No timing sleep is ordering evidence. Do not retain the old release-before-
commit false-positive test as satisfying this contract.

## 4. Complete cancellation/pool/lifespan and tentative-locale proof

For cancelled canonical and human preview after transaction/recheck context is
established, check out connections from the same pools and assert no open
transaction, default `READ COMMITTED`, empty session/operation/visible-
operations/capability context, usable SQL, and unchanged COW/audit/quota/
idempotency state. Then render successfully.

Exercise a real Render app/database-adapter lifespan stop and fresh start and
resolve the same durable authorized overlay plus unchanged canonical state.
Preserve browser before-consume/no-event and after-consume/one-event/replay-
denied behavior.

Add the missing post-tentative locale cancellation: pause after the production
locale SQL wrapper returns and graph validation has succeeded but before generic
completion/audit; cancel; prove exact rollback of locale/default/effective
routes/redirect/navigation/quota/idempotency/audit/COW; retry the identical key
successfully.

## 5. Preserve cleared security gates

Do not alter the now-qualified images except to fix an actual current-head
failure. Preserve:

- Ubuntu 24.04 Apache: zero Critical;
- Postgres Alpine 3.23 exact `libcurl=8.22.0-r0`: zero Critical;
- all six images: zero unexcepted Critical, empty exception set;
- Chrome `152.0.7977.82`, SBOM/license/reproducibility evidence and exact pins.

Run focused preview recheck/lock/race/snapshot/negative-control/cancellation/
lifespan/locale tests; the two regressed structural suites; full Agent/Editor/
Render/bootstrap integration; migrations/privileges; Python quality/unit/
integration; Node; PG14–18; repository/Markdown/Mermaid; clean Compose/public
journeys/Apache parity; complete supply chain; then all current-head CI. Push
before observing CI and repair only in-scope failures. No pending/skipped/
superseded result is pass.

## Boundaries and report

No dynamic `{slug}`/collection detail; no new public route or feature; no 078
composition/design/Puck; no media/MCP/freeze implementation/review/promotion/
source/sweep/076; no architecture/historical order/report edit/general refactor/
production/release/exception/issue closure. Preserve all accepted 077 behavior,
public Agent browser workflow, redirect statuses/headers, migration 053 locale
integrity and canonical/site/workspace isolation. GitHub issue #67 stays open
until verified Objective 077 merge.

Commit this exact order and `oap/active` unchanged, push only the existing PR
branch, create no PR, and never merge/auto-merge. Publish exactly
`oap/reports/077-q-repair-preview-recheck-and-causal-proof.md` as the final
report-only child of a literal implementation SHA with
`Report publication commit: SELF`. Include 077-p SHA reconciliation; exact
wait graph and authorization row/advisory modes; wrappers/grants/migration;
restored 200/409 race outcomes; causal commit-before-release timeline and
`READ COMMITTED` negative; direct post-cancel pool state; actual lifespan
restart; post-tentative locale rollback/retry; security gate digests/results;
commands/counts/skips/current checks; no secret/scope/extra PR/merge/exception;
remaining dynamic/final 077 scope; and strongest reason not to accept.

`PARTIAL`/`BLOCKED` requires a concrete external or technical blocker with
exact attempted evidence. Do not return because tests/Compose/CI are long. No
post-report push. Signal exact FIFO `OK`, then wait for strategic review.
