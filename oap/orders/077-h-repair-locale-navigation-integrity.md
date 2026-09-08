# OAP Work Order — 077-h

## Objective and verified PR state

Repair the concrete locale/navigation integrity defects found by independent
review of 077-g. Amend only
[PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), branch
`oap/077-agent-site-structure-semantics`, base `main`; no new PR and no merge.
Required starting remote report head:
`6ca6977420e76dbda5ef0f8d53b78c3e3b39ac5e`, whose sole parent is 077-g
implementation `c294a8696312a0bba4a6883af094d354561a3601`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

All 20 required checks on the 077-g report head are terminal success. Preserve
the existing public operations and all accepted 077-a through 077-f behavior.
This is a production integrity repair, not redirect or Render expansion.

## 1. Close every navigation resource-constraint bypass

The exact item read wrapper currently returns a same-site item without resolving
its parent navigation against `allowed_navigation_ids` and
`allowed_navigation_keys`. Navigation and item delete wrappers enforce the ID
allowlist inconsistently and can bypass a key-only restriction.

For every list/get/create/update/move/delete of a navigation or item, resolve
the exact visible parent navigation under the immutable capability constraints
inside PostgreSQL. Enforce both key and ID restrictions consistently. Exact
reads of disallowed resources are non-leaking 404; mutations are stable 403/404
according to the established contract and leave no quota/audit/idempotency/COW
residue. A direct trusted-wrapper call cannot bypass the HTTP check.

`max_visible_locales`, `max_visible_navigations`, and
`max_visible_navigation_items` must count the capability-visible constrained
set, not unrelated hidden site resources. Define item maximum consistently
across all allowed containers for that capability, or rename/document a clear
per-container bound; list/create semantics may not disagree. Prove a capability
restricted to one navigation remains usable when other hidden navigations and
items exist, without leaking their count or identity.

## 2. Make locale mutation/version semantics exact

- Remove `tag` from the Agent locale PATCH request, service wrapper, SQL
  signature, OpenAPI and tests. The tag is immutable after create; accepting an
  equal tag and ignoring it is not an honest public operation. Editor behavior
  is unchanged unless needed for shared integrity.
- Reject empty locale and navigation-container PATCH requests before quota,
  idempotency completion, audit or row-version changes.
- When locale create/update selects a new default, every previous visible
  default row changed to non-default must increment its row version and
  `updated_at` in the same transaction. A client holding its old version must
  then receive a stale conflict. The semantic event/response/review diff must
  make the multi-row default switch auditable rather than hiding it as an
  unchanged secondary resource.
- Maintain exactly one enabled visible default under concurrent create/update,
  replay, cancellation and failure. Canonical control/default state and other
  workspaces/sites remain unchanged before promotion.

## 3. Localized labels must reference configured locales

Every locale key in navigation-container `labels` and navigation-item `labels`
must name an existing enabled same-site visible locale and satisfy the
capability allowed-locale constraint. Enforce at schema and trusted PostgreSQL
boundaries for create/update. Locale disable/delete must treat all such label
keys as exact references in addition to item.locale, pages, redirects and item
translations. Use structural JSON key predicates, never substring matching.

Unknown, disabled, foreign or disallowed label locales fail atomically with no
residue. Switching the default does not rewrite labels. Add positive
multi-locale labels and negative dependency evidence.

## 4. Navigation targets cannot be unsafe or dangling

- Until a later redirect route is implemented, an INTERNAL navigation target
  must resolve to one exact visible, non-tombstoned static page effective route
  in the same site/workspace/allowed locale and route-prefix constraint. It may
  not target an undeclared path, a dynamic `{slug}` template, API/admin/
  preview/internal route, query/fragment trick, encoded separator, URL or
  executable syntax. Later redirect integration may deliberately broaden this
  to a validated redirect source/target.
- EXTERNAL targets default to HTTPS only. Do not accept HTTP absent an explicit
  implemented site policy; none exists in the current contract. Reject
  protocol-relative, credential-bearing, control-character, malformed or
  executable URLs. These are links, not source-inspection authority.
- PAGE targets keep exact same-site visible page IDs and must respect the page/
  route/locale resource constraints, not only site equality.

Prove unknown internal routes and HTTP external targets fail at the public API
and trusted wrapper with zero residue. Ensure public documentation matches the
actual target grammar.

## 5. Separate PATCH from move and preserve optimistic ordering

Current item PATCH accepts parent/anchor fields and the shared apply function
re-ranks/appends an item even for a labels-only update. Remove parent and
before/after fields from PATCH; PATCH changes only target/labels/locale plus
expected row version and preserves parent/position exactly. Reject empty PATCH.

Only `POST /navigation-items/{id}:move` may change parent/order. Make its
parent intent unambiguous: either require the nullable `parent_id` field to be
explicit, or use fields-set handling so omission preserves the current parent
while explicit null means root. Before/after anchors remain mutually exclusive,
same-container and same-target-parent.

Every sibling whose position changes due to create/move/delete/rebalance must
receive an incremented row version and updated timestamp. Deletion compacts the
remaining sibling order densely. A stale client for any shifted sibling must
fail rather than overwrite the new order. The initiating operation remains one
semantic operation, but its complete multi-row effect must be visible in COW/
review evidence and must not masquerade as unchanged rows.

Test labels-only PATCH no-reorder, root/parent reorder, move across parents,
create insertion, delete compaction, stale shifted sibling, replay, rollback at
quota/audit failure, maximum position/depth, and cancellation. Final sibling
positions are dense, unique and deterministic.

## 6. One structural lock across Agent and Editor writes

Migration 050 retains legacy Editor locale/navigation-item functions using the
old site-only `_navigation` advisory key, while Agent page/locale/navigation
uses the workspace+site structural lock. This permits an authorized human
Editor mutation in the same workspace to race an Agent page delete, locale
disable/default switch, or navigation reorder and violate the invariant.

All online Editor and Agent page/locale/navigation/navigation-item mutation
functions that can affect routes, default locale, page references, hierarchy or
order must acquire the same application-owned workspace+site structural lock
after the existing workspace lifecycle shared lock. Reuse one helper and one
documented lock order; remove obsolete parallel lock keys for these operations.
Do not give Editor Agent capability requirements or Agent human session
authority—share serialization only, preserving separate authorization/audit
paths.

Add deterministic real-PostgreSQL cross-interface races using production Agent
and Editor HTTP in the same workspace for page-delete versus item-create,
locale-disable versus localized item/page create, and Agent versus Editor item
move/reorder. No timing sleeps. Final state must preserve references/default/
order and both authority models. Also prove different workspaces/sites remain
independent and freeze lock ordering does not deadlock.

## Database, OpenAPI and acceptance

Repair unreleased migration 050 and associated models/services/functions/
privileges in place where safe. Preserve data-bearing 049→050, public COW
disable/downgrade/re-upgrade, compatible Editor projections, exact owners/
search paths/grants, and fail-before-mutation downgrade for unrepresentable
state. No private foundation relation/function dependency or runtime raw SQL.

Regenerate canonical Agent OpenAPI and exact route-policy drift checks for the
narrowed PATCH/move/locale schemas. Extend public NGINX/Compose acceptance and
real capability PostgreSQL tests for every positive and negative above,
canonical/other-workspace/site isolation, restart, scopes/resources, quotas,
idempotency, semantic audit and cancellation. Neutral owner SQL may seed and
assert only; direct service/SQL/Editor substitution cannot prove Agent behavior.

Run focused locale/navigation/resource/target/order/cross-interface race tests,
full Agent mutation and integration suites, migration/privilege/PG14–18,
Python quality/unit, OpenAPI, repository/Markdown/Mermaid, Node, clean Compose,
and all current CI. Preserve Chrome `152.0.7977.82`, zero current Critical and
the empty exception set.

## Non-goals and immutable report

No Agent redirect CRUD or redirect-loop behavior yet; no dynamic collection
Render/router; no composition/design/Puck/media/MCP/freeze/review/promotion/
source/sweep or 078+ work. No dependency/image/exception/architecture/
historical artifact/general refactor/issue closure/production/release claim or
production access. Do not reopen 076.

Verify/update only PR #74 and its branch. Commit this exact order and active
selector unchanged with the bounded repair/tests/docs; push; create no PR;
never merge/auto-merge; repair only in-scope current-head failures.

Publish exactly `oap/reports/077-h-repair-locale-navigation-integrity.md` as the
final report-only child of a literal implementation SHA with `Report
publication commit: SELF`. Include exact PR/commits/files/migration/functions/
indexes/grants/routes/OpenAPI; every closed bypass; default-secondary version/
audit behavior; label and target integrity; PATCH/move/order semantics;
Agent/Editor shared-lock races; quota/idempotency/audit/COW/isolation/
cancellation/downgrade evidence; commands/counts/skips/current checks; no scope
drift/private dependency/new PR/merge/exception/secret; remaining 077 scope;
and strongest reason not to accept this slice.

`PARTIAL`/`BLOCKED` requires a concrete external/technical blocker with exact
attempted evidence. Do not return early because tests or CI are long. No
post-report push. Signal exact FIFO `OK`, then wait for strategic review.
