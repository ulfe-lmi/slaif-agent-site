# OAP Work Order — 077-z

## Objective and protocol-final PR state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`fe55f85de566ee9c13f47184e51a31a2ddb8a061`, whose sole parent is 077-y
implementation `227eaa1e78f35b4d9bedb685f0a0a5514dcc4c29`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

This is the protocol-final Objective-077 round. There is no `077-aa`. PR #74 is
feature-frozen. Complete only: (1) the exact locale-neutral INTERNAL Render
regression below; (2) final hostile Objective-077 audit; (3) truthful README/
MVP/PR reconciliation; and (4) exact-head verification. Do not add feature
scope. If a further substantive Objective-077 defect is found and cannot be
safely repaired within this frozen round, report a precise blocker for human
decision rather than hiding it or inventing another letter.

## 1. Repair locale-neutral INTERNAL Render semantics

Migration 058 calls `slaif_render_internal_target_exists` with
`coalesce(item.locale,p_locale)` and the helper requires the target page's
locale to equal that value. A navigation item whose optional locale is `NULL`
is visible across selected locales and retains its declared fixed INTERNAL
route. It must not be reinterpreted as a route in the currently selected page
locale. Today a valid global `/docs` target backed by the default-locale static
page can make a valid `sl-SI` page fail Render.

Append an exact reversible correction:

- locale-specific INTERNAL items must resolve their fixed concrete route in
  that exact enabled item locale;
- locale-neutral INTERNAL items may resolve their exact declared route against
  any enabled same-site static page in the current canonical/preview status
  set, and remain visible from another selected locale without route rewriting;
- selected locale still controls item visibility and label resolution exactly
  as before; the target remains the stored normalized path;
- absent, ambiguous, dynamic, reserved, foreign, deleted or unavailable-for-
  the-current-Render-status targets fail closed with no partial projection;
- canonical cannot accept a route backed only by DRAFT; preview may accept
  PUBLISHED/DRAFT according to its existing status set; and
- mutation-time global graph validation and all 057/058 page/navigation
  dependency rules remain unchanged.

Include real PostgreSQL canonical and preview tests for a locale-neutral
default-locale target rendered from `sl-SI`, a locale-specific target, status
differences, ambiguity/corruption, reserved/dynamic/foreign negatives, pool
reuse, and upgrade/downgrade/re-upgrade privileges. This is a defect repair,
not locale-aware target rewriting or a new navigation feature.

## 2. Final hostile Objective-077 audit

Audit the complete current PR—not only 077-z—and map every activated order
077-a through 077-z to production and executable evidence. Treat all reports as
claims. Reconcile remote PR identity/head/parents/diff/checks independently and
state the strongest reason not to merge.

The audit must explicitly prove or mark unresolved:

### Public Agent information architecture

- exact page list/read/create/update/delete/move/restore and derived hierarchy/
  route semantics;
- bounded locale create/read/update/delete/default/ordering;
- navigation container/item list/read/create/update/delete/move/reorder;
- redirect list/read/create/update/delete and exact status/location;
- dynamic collection listing and terminal `{slug}` detail routing with exact
  view/type/item/version/filter/status/localized projection; and
- canonical, human preview, run-bound browser preview and NGINX/Web behavior
  over the same workspace.

### Negative authority and integrity

- lower/wrong scope, foreign site/workspace/resource, client-selected context,
  frozen/non-ACTIVE workspace, stale version, quota exhaustion, replay and
  same-key/different-request mismatch;
- duplicate/reserved/malformed routes, hierarchy cycles/depth/dynamic-leaf,
  locale bounds, navigation cycles/dense order/dangling PAGE and INTERNAL
  references, redirect collision/loop/chain/target dependencies;
- dynamic static overlap/ambiguity, zero/multiple/wrong detail binding,
  filter-excluded/stale/foreign/deleted/wrong-status item/view/type/translation,
  malformed slug/query/projection, and executable/raw-query denial;
- canonical/other-workspace/other-site isolation, semantic audit identity,
  quota/idempotency/COW atomicity, cancellation cleanup and restart recovery;
  and
- deterministic route/page/navigation/redirect/type/item concurrency with no
  timing-sleep proof or allowed-state assertion that omits final durable state.

### Contracts, runtime and supply chain

- production handlers, route policy and canonical Agent OpenAPI are
  bidirectionally exact, with no undocumented or schema-only route;
- Render uses coherent repeatable-read canonical/COW snapshots, exact reader
  roles, one trusted component/CSS path, correct locale/privacy headers, and no
  UUID/token/Flight leakage in visitor HTML;
- migrations 049–059 (or final head used for this correction) install from
  clean state and downgrade/re-upgrade without data/grant/function loss;
- Control/Agent/Editor/Render/reviewer/setup authority boundaries are not
  weakened by this PR; no raw SQL, reviewer/publish, identity, schema-create or
  canonical-write authority entered Agent paths;
- Chrome for Testing remains `152.0.7977.82`, exceptions remain empty, Apache
  Ubuntu and PostgreSQL Alpine/libcurl qualifications remain exact, and all six
  images have zero Critical findings; and
- no 078 composition/design/Puck, 079 media, 080 MCP, 081 exact-workspace Puck,
  082+ freeze/review/promotion, 087 source/sweep, release claim, dependency or
  unrelated cleanup entered PR #74.

Audit anti-bypass: public Agent/Editor/Render/NGINX/browser evidence must fail
if the corresponding production route/function/renderer/browser execution is
removed. Direct owner SQL is only neutral fixture/corruption/assertion support,
not claimed product behavior.

Record transcript anomalies without rewriting history:

- 077-b's immutable-order Markdown failure and the explicit human-authorized
  one-line correction reconciled by 077-c;
- intermediate blocked 077-l through 077-r findings and their later repairs;
- 077-p's literal implementation-SHA typo (`20c238909b7e7d...`) versus its
  authoritative actual report parent
  `20c238909b7be7d0cc65894cdd93c4c29ace4b57`, already acknowledged by 077-q;
  and
- every order/report is unique, report-only publication commits are preserved,
  and no historical order/report is silently edited beyond the recorded 077-c
  human override.

## 3. Reconcile truth documents and PR presentation

Preserve historical evidence; update current-state classifications rather than
rewriting prior audits.

- Update `oap/MVP-PROGRESS.md` from its stale 076/`077-t` baseline to this
  Objective-077 source revision. Mark only the bounded 077 information-
  architecture contract `COMPLETE — E2E PROVEN` if the audit actually proves
  it. Keep the contractual MVP verdict `NOT COMPLETE` and retain 078–091 as
  remaining/new-PR work.
- Update `oap/MVP-CONTRACT-AUDIT.md` audit date/source baseline, the page/
  navigation/redirect/dynamic Render row, narrow-objective evidence, and active/
  remaining sequence. Do not upgrade composition/design/media/MCP/Puck/review/
  promotion/source/reconstruction/expiry/backup/final-MVP rows without their
  own evidence.
- Update README current-status/run/development wording to credit the real
  merged-prefix 074–076 and this revision's capability-bound page/locale/
  navigation/redirect/dynamic Render behavior, while clearly saying PR #74 is
  awaiting strategic acceptance at report time and review snapshots,
  promotion/publication and later MVP work remain absent. Remove stale claims
  that all deeper Agent semantics are merely queued; retain pre-alpha/not-
  release-ready wording.
- Reconcile any directly affected API/testing/migration-head documentation if
  stale, but do not perform a general documentation rewrite.
- Replace PR #74's stale `077-a` title/body with a concise full Objective-077
  summary, exact implemented scope, major negative/concurrency/evidence,
  security-maintenance result, remaining 078+ non-goals, and current
  verification. Do not claim merge or MVP completion.
- Keep GitHub issue #67 open. Strategy closes it only after PR #74 merge is
  verified on remote `main`.

Wording must remain true both immediately before merge and once this exact
source revision is contained in `main`: distinguish source-revision evidence
from strategic merge state without embedding a false permanent "currently
unmerged" assertion.

## 4. Protocol-final verification and report

Run focused 059 locale-neutral INTERNAL Render/migration/privilege tests, then
the complete current gates: all Python quality/unit/integration; PG14–18;
Node/renderer/browser; repository/Markdown/Mermaid; generated OpenAPI/policy
drift; clean Compose public Agent/Editor/Render/NGINX/browser/restart/recovery;
all six zero-Critical supply-chain evidence; and every current-head GitHub
check. No skipped/pending/superseded result is pass.

Commit this exact order and `oap/active=077-z` unchanged, amend only PR #74,
create no PR and never merge. Publish exactly
`oap/reports/077-z-final-hostile-objective-audit.md` as the report-only child
of a literal implementation/reconciliation SHA with `Report publication
commit: SELF`.

The report is the durable final audit. Include:

- exact remote/PR/head/parent/transcript reconciliation and anomalies;
- requirement-by-requirement PASS/FAIL/UNPROVEN matrix with production files,
  test names, intended interfaces and exact results;
- the 059 correction and migration/grant/downgrade evidence;
- exact route/OpenAPI inventories and changed-file/non-goal audit;
- full local commands/counts, current-head checks, six-image findings;
- final truth-document/README/PR-body changes;
- secrets/production/scope/no-extra-PR/no-merge confirmations; and
- a binary `OBJECTIVE_077_ACCEPTANCE_CANDIDATE=YES|NO` plus the strongest reason
  not to merge.

`YES` is permitted only if every Objective-077 criterion is proved and no
required work remains. It does not mean merged or MVP complete. `PARTIAL`/
`BLOCKED` requires a concrete unresolved technical/product blocker. No
post-report push; signal exact FIFO `OK`, then wait for strategy's independent
review and merge decision.
