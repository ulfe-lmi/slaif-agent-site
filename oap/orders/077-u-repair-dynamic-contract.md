# OAP Work Order — 077-u

## Objective and frozen PR state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`1704b312b13f6d8b3aa1714305d40d11a6cac309`, whose sole parent is 077-t
implementation `b76bf2f7379460658c39176fe6c058dd0515edb0`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

The human has frozen PR #74. This is a defect-and-missing-evidence repair of
the already-activated 077-t contract, not new Objective-077 feature scope.
After this round strategy will perform the final hostile whole-objective audit
and truth-document reconciliation. Do not add an adjacent feature, general
refactor, or later-objective work.

077-t's report is structurally valid and its 055 downgrade restoration is
accepted for progression, but its `COMPLETE` claim is not accepted. Strategic
source/evidence review found the concrete defects below, and the report itself
admits that the required local public NGINX HTML journey was not run.

## 1. Repair the production defects

### 1.1 Preserve every database query bound with localized projections

Migration 056's wrapper reconstructs `filtered_projection` with only the
nonlocalized fields before calling the prior validator. That discards unknown
projection-object members and removes localized entries from the prior
validator's full-document size/node/16-field checks. A projection containing
only localized fields can therefore bypass the intended projection count and
serialized-contract checks at the trusted database boundary.

Replace this with one exact database validator that:

- validates the original four JSON documents, including their original shape,
  keys, serialized-byte bound, recursive depth/node bound, duplicate entries
  and at most 16 total projection fields;
- permits an existing same-type localized field only in projection;
- continues to reject localized filter/sort, reserved/unknown fields and every
  hostile SQL/JS/prototype/template/executable value;
- preserves owner/search-path/PUBLIC/runtime privilege boundaries and exact
  downgrade restoration; and
- cannot be bypassed by direct invocation of the public Agent mutation's
  trusted SQL function even if Python/Pydantic validation is absent.

Add real PostgreSQL regression cases for extra projection keys, more than 16
localized fields, oversized localized-only projection input, mixed localized/
nonlocalized duplicates, non-string values and hostile content. Prove rejection
leaves no view, quota, idempotency or audit residue. Do not weaken the existing
Python validator; both boundaries must agree.

### 1.2 Reject stale content-item definitions during Render

`_collection_bindings` currently does not select or compare
`content_item.type_definition_version`. A stale item can therefore render if
its surviving values happen to validate under the current fields. Require the
item's stored definition version to equal both the active type definition and
the collection view's definition version. Wrong/stale items make the dynamic
detail 404/fail closed and never appear in list/grid. Add canonical and preview
tests, including a neutral-owner corruption fixture; do not repair or migrate
the item during a read.

### 1.3 Repair non-default-locale dynamic routing and remove grammar drift

The SQL resolver compares routes case-insensitively because stored BCP-47 tags
retain case, while Python `_dynamic_route_parameter` uses case-sensitive
`matched_route.startswith(prefix)`. A valid stored locale such as `sl-SI` and
normalized request `/sl-si/news/item` therefore resolves in SQL and then fails
in Python.

Make the selected non-default locale dynamic route work with the established
locale/effective-route contract while preserving strict slug matching and 404
for malformed paths. Remove the second Python regex as an independent route-
grammar authority: the trusted database resolver must remain authoritative,
and Python may only extract/check consistency of the already-validated result.
Do not introduce a third Web grammar or accept uppercase/encoded/extra/path
segments as item slugs.

Prove exact selected-locale output and explicit default-locale fallback. A
missing selected-locale translation may fall back to the default translation;
missing or invalid required output after that fallback must fail closed.

### 1.4 Do not regress pre-077-t static CollectionDetail behavior

077-t added an unconditional `CollectionDetail` 404 when there is no dynamic
route parameter. Its order required exact binding for dynamic pages; it did not
authorize removal of existing static-page CollectionDetail behavior. Restore
the pre-077-t static behavior under the existing bounded view semantics while
retaining exactly-one-detail/exact-slug behavior for dynamic pages. Add a
regression test that would fail on 077-t's unconditional check. Do not invent a
new static-detail API or composition model.

### 1.5 Remove internal UUIDs from rendered public/preview HTML

`apps/web/src/renderer/components.tsx` currently emits `data-site-id` and
`data-node-id`. That contradicts 077-t's explicit actual-HTML acceptance claim
that the trusted list/detail result contain no token, internal identifier or
raw JSON. Remove internal UUID-bearing HTML attributes from public and preview
SSR while retaining harmless stable component-type diagnostics if needed.
Internal IDs may remain server-side projection metadata and React-only keys;
they must not be serialized into visitor HTML. Add Web-level assertions using
actual UUID fixture values, not only generic substring checks.

## 2. Supply the missing intended-interface proof

077-t added a public Agent ASGI test followed by direct
`RenderProjectionService` calls. It did not exercise run-bound browser preview
or NGINX -> Web HTML, and its report explicitly says a separate local NGINX
capture was not rerun. Green generic Compose packaging cannot substitute for
this feature journey.

Extend the existing public Compose acceptance machinery (prefer
`tools/compose/public_agent_acceptance.py`, `tools/compose/smoke.sh`, existing
restart helpers and existing browser-preview credential flow) so one clean
Compose run proves through port 8080:

1. a real human-issued L4 capability creates the News type, localized fields,
   PUBLISHED/DRAFT/ARCHIVED items and translations, bounded view, listing and
   `{slug}` detail pages, trusted CollectionList/CollectionDetail nodes and
   navigation exclusively through public Agent HTTP;
2. public NGINX -> Web preview HTML for listing, default-locale detail and a
   non-default-locale detail contains the expected sorted/localized title and
   summary and trusted renderer markup, with no capability/browser/human token,
   workspace/site/item/node UUID, internal projection JSON or secret;
3. the run-bound browser-preview credential resolves only its exact dynamic
   workspace/site/route, retains existing one-use/replay behavior, and wrong
   site/workspace/route/human/browser credentials are absent/404/denied without
   disclosing which association was wrong;
4. canonical HTML/route bytes are unchanged and Agent-created listing/detail/
   navigation remain absent before later human promotion;
5. Agent item slug, status and translation mutations through public HTTP move
   exact route availability and visible text as specified, while old,
   ARCHIVED, filter-excluded and unknown detail paths are 404; and
6. restart/recreate of Agent API, Render API and Web preserves the same
   workspace dynamic result and all isolation. Use bounded readiness polling,
   never a timing sleep as correctness evidence.

Use the actual edge and Web renderer; a direct service call, mock projection,
static fixture HTML or schema/route existence assertion is only supplemental.
Do not place capability or preview credentials in URL, HTML, logs, screenshots
or report output.

## 3. Supply the missing race and cancellation proof

077-t added no focused dynamic Render concurrency/cancellation test. Add real
PostgreSQL, two-connection/task evidence with deterministic events, transaction
or advisory-lock barriers—never sleep-based ordering—for:

- detail Render versus item slug/status/translation mutation;
- detail Render versus item delete;
- detail Render versus collection-view/type-definition change or deletion;
- detail Render versus dynamic page route move; and
- cancellation after the exact page/detail snapshot is established but before
  projection completes.

Every race must yield one coherent before snapshot, coherent after snapshot or
404 as appropriate—never a page/item/view/translation mix. Cancellation must
close the read transaction and COW/session context, leave pools reusable,
consume no mutation quota/idempotency/audit, preserve one-use browser-token
semantics, and permit a later successful render. Assertions that accept any
status without validating final durable state are not evidence.

## 4. Hostile route/binding matrix and continuity

Complete focused regression coverage for malformed/overlong/encoded/extra-
segment slugs; static/dynamic ambiguity; zero/multiple/wrong detail nodes;
foreign/deleted/stale view/type/item/translation/component associations;
filter exclusion; canonical DRAFT/ARCHIVED/unknown 404; preview ARCHIVED/
unknown 404; undeclared projection; localized filter/sort; arbitrary query
string and executable query attempts. Preserve route/page/locale/navigation/
redirect/COW/lifecycle/lock/audit/quota/idempotency/canonical-isolation behavior.

No public Agent route is expected. Independently prove production handlers,
route-policy declarations and canonical generated OpenAPI remain bidirectionally
identical. No schema-only or undocumented route may appear.

## 5. Verification, scope and report

Run the focused migration/query/render/Web/browser/Compose/race/cancellation
tests first, then the complete current gates required by 077-t: PG14-18,
Python quality/unit/integration, Node lint/format/typecheck/test/build/license,
repository/Markdown/Mermaid, exact clean Compose/restart/edge journey and full
six-image zero-Critical supply-chain evidence. Push before observing CI and
repair only in-scope failures. Required pending/skipped/superseded results are
not pass.

Do not add composition update/move/delete/design/Puck scope from 078; media 079;
MCP 080; Agent-workspace Puck 081; freeze/review/promotion 082+; source/sweep
087; primitives/operators/dependencies/images/exceptions/architecture changes;
or general cleanup. Preserve Chrome `152.0.7977.82`, all six zero-Critical
images, empty vulnerability exceptions and open GitHub issue #67. Do not edit
historical orders/reports or final Objective-077 truth ledgers in this repair;
strategy will order the final hostile audit/reconciliation separately.

Commit this exact order and `oap/active` unchanged, amend only PR #74, create no
PR and never merge. Publish exactly
`oap/reports/077-u-repair-dynamic-contract.md` as the final report-only child of
a literal implementation SHA with `Report publication commit: SELF`. Report
the exact production defect corrections; database validator and privilege
proof; dynamic/default/non-default/static paths; public Agent operation
inventory; NGINX/Web HTML evidence and secret/UUID negatives; browser credential
cases; workspace/site/canonical/restart isolation; every race/cancellation
barrier and terminal state; exact commands/counts/skips/current-head checks;
scope/no-secret/no-extra-PR/no-merge confirmations; and the strongest remaining
reason not to accept Objective 077.

Do not return early for an ordinary implementation/test/CI failure or task
size. `PARTIAL`/`BLOCKED` requires a concrete external outage or an unresolved
architecture/product decision. No post-report push; signal exact FIFO `OK`,
then wait for strategic review.
