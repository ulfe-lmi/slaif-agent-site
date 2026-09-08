# OAP Work Order — 077-e

## Objective and verified PR state

Close four residual page/route integrity defects found by independent review of
077-d. Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; no new PR and no
merge. Required starting remote report head:
`f2c46faded0d5bb99632c8c6aebdce7a28b5768a`, whose sole parent is 077-d
implementation `daad2a51c61830b4093950e904d9f052fa0a7840`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

Preserve all accepted 077-b/077-c Chrome, ledger and protocol-reconciliation
work and the valid 077-d soft-tombstone, locale-authority, parent-only move,
conditional-scope enforcement, race/cancellation and public acceptance repairs.
077-d's report-head checks were still running at initial review; its code is
independently insufficient regardless of eventual CI status for the exact
reasons below.

## Exact defects and required repairs

### 1. Uniqueness must follow hierarchy, not site-wide slug

Migration 049 currently replaces the legacy uniqueness constraint with a
partial unique index on `(site_id, locale, slug)` for active rows. That rejects
valid distinct routes such as `/research/news` and `/teaching/news`, even though
page slugs are segments and route uniqueness is derived from ancestors.

Replace this with a canonical active-sibling invariant—site, locale, normalized
parent identity and slug—or an equivalently exact database constraint that
allows the same segment under different parents while rejecting duplicate
siblings. Keep semantic effective-route validation authoritative for complete
static/dynamic route overlap in a workspace COW overlay. The structural lock
must serialize decisions that a physical canonical index cannot see across
overlay/base rows.

Real production Agent HTTP tests must prove:

- identical `news` slugs under two distinct same-locale parents succeed and
  expose distinct effective routes;
- duplicate active sibling slugs fail with stable conflict and zero quota/
  audit/idempotency/COW residue;
- tombstoned siblings release the route, while restore rechecks and conflicts
  if the sibling/route was reused;
- cross-locale and cross-site rows cannot interfere; and
- canonical promotion-time structure remains database-defended.

### 2. `{slug}` must be terminal in the hierarchy

The schema restricts the template token itself, but current hierarchy
validation permits a page with `route_template = "{slug}"` to have an active
child, yielding an illegal route such as `/news/{slug}/child`.

Reject any active child/descendant beneath a dynamic detail page and reject any
create, move, update or restore that would place a page below an active dynamic
ancestor. A page being changed to `{slug}` must have no active children.
Tombstoned children do not route but restoration must revalidate the invariant.
Enforce inside the trusted PostgreSQL structural lock/transaction, not only in
Pydantic or Render.

Add public Agent HTTP positives/negatives plus a deterministic multi-connection
race in which making a parent dynamic competes with creating/moving/restoring a
child. No timing sleeps; final state must have either the valid leaf template or
the valid child tree, never a nonterminal template or partial residue.

### 3. Downgrade cannot name private foundation relations/functions

Migration 049 no longer queries `page_changes` for runtime behavior, but its
downgrade still names `content.page_base` and invokes deployed SQL
`agentcow.teardown_cow`, which is not the public exported product API. This
contradicts the 077-d requirement and its report's broad no-private-dependency
claim.

Remove every private base/change relation name and unexported teardown call
from migration 049. The supported operator path is the product bootstrap's
documented public `agentcow.postgres.disable_cow_schema`/`disable_cow` API before
Alembic changes physical content tables. If migration 049 is invoked directly
while `content.page` is still a COW view, fail in a preflight before any DDL,
data, audit, function or privilege mutation with a stable operator-facing
message requiring the public disable/reconcile path. Do not rediscover or
reimplement foundation naming internals.

Test both paths on real PostgreSQL:

- direct downgrade with COW enabled refuses atomically and leaves revision,
  data, pending state and hardening usable;
- after public foundation disable with compatible data, 049→048 downgrade and
  048→049 upgrade preserve data/functions/owners/grants and re-harden safely;
- 049-only template/tombstone/PAGE-audit preflight still refuses before any
  mutation; and
- production source/migration scans contain no page `_base`/`_changes` or
  private `_cow_*` behavioral dependency.

Assertion-only owner tests may inspect internals to prove residue/isolation but
must not perform product behavior or drive migration logic.

### 4. Conditional-scope drift gate must be generic

077-d's handler is correctly driven by route policy, and OpenAPI emits the
policy condition, but current validation does not generically prove that
conditional scope names are valid or that every `when_fields` entry exists in
the actual operation request schema. A hard-coded page test can stay green
while policy/schema drift elsewhere is introduced.

Extend the route-policy/OpenAPI validation mechanism so that, for every Agent
route with conditional scopes:

- the route is an Agent capability mutation;
- static and conditional scopes are valid delegatable Agent scope keys;
- field/scope lists are nonempty, normalized, unique and nonoverlapping as
  appropriate;
- each trigger field is present in the actual typed request-body schema for
  that operation, resolving the generated schema reference deterministically;
- every production handler remains policy-driven for the condition; and
- canonical OpenAPI, route policy and live handler/request schema are compared
  in both directions.

Add synthetic negative tests for an unknown scope, unknown request field,
condition on a read/no-body route and mismatched canonical metadata. Preserve
the exact page PATCH behavior: title/status with `page:write`; slug/locale/
route-template additionally require `route:write` with no durable denial
residue.

## Verification and scope

Use real capability-authenticated production Agent HTTP for semantic evidence;
direct helpers are defense only. Run focused page hierarchy/template/
conditional-policy/migration tests, the complete Agent mutation/OpenAPI/
route-policy and integration suites, migration/privilege/PG14–18, Python
quality/unit, repository/Markdown/Mermaid, Node, and one clean relevant Compose
public acceptance if changed behavior reaches it. Required CI and supply-chain
remain authoritative. Preserve Chrome `152.0.7977.82`, zero current Critical
findings and the empty exception list.

No Agent locale CRUD, navigation, redirect, Render dynamic detail resolution,
composition/design/Puck/media/MCP/freeze/review/promotion/source/sweep or 078+
work. No dependency/image/exception/architecture/historical artifact change,
general refactor, issue closure, production/release claim, or production
system/data/secret access. Do not reopen 076.

## GitHub workflow and immutable report

Verify/update only the named existing PR/branch. Commit this exact order and
`oap/active` unchanged with the bounded repair/tests/docs, push, create no PR,
never merge or enable auto-merge, and repair only in-scope current-head failures.

Publish exactly `oap/reports/077-e-close-page-route-integrity-gaps.md` as the
final report-only child of a literal implementation SHA with `Report
publication commit: SELF`. Include exact commit/file/migration/function/index/
grant inventories; sibling-route and dynamic-leaf behavior; public foundation
disable/refusal paths; generic policy/schema/OpenAPI drift mechanism and
synthetic negatives; race/cancellation/residue/isolation evidence; commands/
counts/skips/current checks; no private dependency/scope drift/new PR/merge/
exception/secret confirmation; remaining Objective 077 scope; and strongest
reason not to accept the page slice.

`PARTIAL`/`BLOCKED` requires a concrete external/technical blocker with exact
attempted evidence. Do not return early because tests or CI are long. No
post-report push. Signal exact FIFO `OK`, then wait for strategic review.
