# OAP Work Order — 078-b

## Objective and authoritative state

Repair the unaccepted `078-a` catalog/contract slice on the existing Objective
078 PR. This round establishes one deterministic component-catalog authority,
exact schema enforcement, and Render/Web parity. It does not add the later
theme/global/design feature scope or attempt the still-required component race
and full Compose acceptance rounds.

- Numeric objective: `078`; round: `078-b`; mode: `AMEND_EXISTING_PR`.
- Repository: `ulfe-lmi/slaif-agent-site`.
- Existing PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77),
  `main` <- `oap/078-agent-composition-design-semantics`; create no new PR.
- Verified remote `main`: `ae3a4a681bb888260192b7bb1b2a337b4906828d`.
- Required starting PR head: report-only commit
  `4d81ca24e6d7bb05f78fd6d051ba2e51a988cd27`; its sole changed path is the
  unique 078-a report and its parent is implementation commit
  `98dd8d824aee0ff1bb458bde41cca1419adab144`.
- All 20 current-head GitHub checks are green. Green CI does not cure the
  substantive gaps below.
- `078-a` remains unaccepted and numeric Objective 078 remains open.

The 078-a order named `oap/reports/078-a-agent-component-semantics.md` while
the uniquely published report followed the order basename at
`oap/reports/078-a-agent-composition-design-semantics.md`. Preserve both
immutable historical artifacts and do not manufacture a second 078-a report;
this order records that prior naming inconsistency as reconciled transcript
history. Publish 078-b under the exact matching basename named below.

## Why 078-a is insufficient

Independent review established these exact defects:

1. Python and TypeScript currently happen to serialize equal catalog documents
   (SHA-256 `7c41038528b290936e94f9c7f3238f7e7d9ff78e2e264c833acf7e240beceb07`),
   but they remain separately hand-authored and no test/generator checks their
   byte- or semantic equality. The Node test checks only enum membership.
2. Migration `060_001_agent_component_semantics.py` imports
   `catalog_document()` from mutable current application code. A later catalog
   edit can therefore change what an old migration installs on a clean
   database, violating deterministic append-only migration history.
3. `AgentComponentCatalogResponse.components` is
   `tuple[dict[str, Any], ...]`; generated OpenAPI consequently exposes an
   `additionalProperties: true` object instead of the exact public descriptor.
4. `AgentCreateCompositionNodeRequest` inherits legacy Editor
   `CreateCompositionNodeRequest`, so public Agent OpenAPI and request parsing
   still accept ignored raw `order_key`. Agent ordering must be semantic.
5. The current catalog declares `RichText.content` as an object, and the clean
   fixture stores `{type: paragraph, children: [...]}`, but Web `RichText`
   renders every non-string/non-array object as empty. Other object/array props
   (`Statistics`, `Timeline`, `FAQ`) have no exact nested shape, only generic
   JSON and forbidden-marker scanning. This is not an exact prop schema and can
   persist data whose visual meaning is absent or ambiguous.
6. `content.slaif_agent_component_update` checks design-key changes only while
   iterating keys already present in `old.props`, then calls the validator with
   `p_allow_design=true`. A caller of the granted trusted helper can add a
   previously absent design-only prop despite holding only
   `component-content-props:write`; Python currently masks the database bypass.

## Required repair

### 1. One versioned catalog authority and deterministic migration

Create one committed, machine-readable, deterministic `catalog-v1` source of
truth (or an equivalently strict generated source) from which Python, the
TypeScript package, Agent discovery, PostgreSQL seed/validation, Render and Web
derive their exact definitions. It must define type/category/schema version,
slots/child limits, binding and authority classes, and complete prop schemas.

- Eliminate independently maintained rule copies. If generated Python/TS/SQL
  artifacts remain, add a deterministic generator plus a check mode that fails
  on any byte/semantic drift and wire it into the existing repository/Node or
  contract gate.
- Make catalog-v1 immutable as a version. A future catalog change must create a
  new version/migration, not silently change the clean-install result of 060.
- Migration 060 must install exactly its reviewed catalog-v1 bytes without
  importing a mutable current-runtime catalog definition. Preserve packaging
  and clean-install behavior.
- Prove Python, PostgreSQL discovery, TypeScript/Puck and Render consume or
  exactly match the same catalog document. A test that checks only counts,
  type names or metadata enums is insufficient.
- Do not add the architecture's missing catalog breadth in this repair; later
  Objective-078 work will add catalog entries together with their trusted
  renderers/design contracts.

### 2. Exact bounded prop schemas and renderer parity

For every currently exposed catalog-v1 prop, encode and enforce enough type,
requiredness, enum, numeric/string/array bounds, nested object keys/items and
localization/authority metadata that accepted data has deterministic meaning.
Unknown nested keys and unbounded generic objects/arrays must fail closed.

In particular, establish one bounded structured RichText representation that
is consistent with existing valid stored fixtures and with the Puck adapter,
Python, trusted PostgreSQL, Render projection and Web renderer. Preserve valid
existing rows through an explicit backward reader or deterministic migration;
do not silently blank them or reinterpret arbitrary shapes. Add exact bounded
item schemas for Statistics, Timeline and FAQ matching what the trusted Web
renderers actually consume. Keep raw HTML, style/CSS, executable URLs,
handlers, code, template/query expressions and prototype keys impossible at
every nesting depth.

For each accepted current component, a catalog-valid fixture must pass Python
and PostgreSQL validation and render equivalent non-empty semantic output in
Render/Web. A deliberately malformed nested fixture must be rejected before
persistence by both public Agent validation and the trusted DB boundary.

### 3. Database authority-class enforcement

Repair the trusted PATCH helper so `component-content-props:write` can change
only catalog-declared content props even when the helper is invoked directly as
`slaif_agent_runtime`. Adding, changing or removing a design-only prop must be
denied at the database boundary. Preserve valid partial PATCH merge behavior,
required props, row-version conflicts, quota/idempotency/audit atomicity and
legacy Editor/Puck authority through their distinct trusted path.

Add a real PostgreSQL runtime-role regression that bypasses Python and attempts
to add an absent design prop; assert exact denial and unchanged props, row
version, quota, audit and COW operation state. Also prove a valid content-only
PATCH still succeeds.

### 4. Exact public Agent contract

- Replace open-ended catalog response dictionaries with explicit frozen public
  models for component and prop descriptors, including nested schema metadata;
  generated OpenAPI must set `additionalProperties: false` at every descriptor
  layer and accurately describe nullable/bounded fields.
- Define the Agent create request independently from the legacy Editor request
  or otherwise remove `order_key` completely from the Agent body/OpenAPI.
  Retain only semantic before/after anchors; sending `order_key` must receive
  422 and create no record/quota/audit/COW operation.
- Preserve legacy Editor/Puck request compatibility. Do not remove its internal
  ordering contract in this round.
- Preserve handler/route-policy/OpenAPI bidirectional inventory and exact
  served canonical OpenAPI bytes.

## Acceptance evidence

Add focused deterministic tests proving:

- generator/check mode detects a one-byte or semantic Python/TS/catalog drift;
- clean migration 060 and downgrade/re-upgrade reproduce the reviewed immutable
  catalog-v1 document and existing data remains valid;
- Agent catalog JSON equals the canonical document and its OpenAPI descriptor is
  closed/typed rather than open-ended;
- raw `order_key` is rejected through public Agent HTTP without side effects;
- all current catalog prop schemas have explicit bounded nested semantics;
- canonical RichText and each structured-array fixture render meaningful,
  equivalent output rather than an empty placeholder;
- public and direct-runtime malformed nested props/design-prop bypasses are
  rejected with durable state unchanged; and
- legacy Editor/Puck composition tests remain green.

Run focused catalog/generator/OpenAPI/Render/Web/Puck tests, the focused real
PostgreSQL migration/runtime-role tests, full Python unit/repository and Node
contract suites, formatting/type checks, generated drift checks and all
current-head GitHub checks. State exact results and all skips/pending failures.
Do not spend this round rerunning the full multi-hour integration suite merely
as a substitute for the missing focused proofs; run broader affected tests only
as needed and let the normal PostgreSQL CI matrix provide broad qualification.

## Non-goals and continuing requirements

- No theme/design-system/global-region/header-footer/responsive-design mutation,
  new component breadth, media bytes, MCP, exact-workspace Puck workflow,
  freeze/review/promotion, source/sweep, site reset or release claim.
- Do not implement 078-a's five focused component concurrency cases or full
  public Compose/preview/browser/restart/isolation scenario in this round;
  they remain mandatory next dependency-correct acceptance work, not waived.
- No new dependency/image/architecture/security exception, broad refactor,
  historical order/report edit, Markdown/test/security weakening, production
  system/data/credential or merge.
- Preserve issue #67 closure and zero-Critical supply-chain policy.

Routine tools, PostgreSQL, Node and tests belong to the passwordless-sudo
disposable executor environment; do not transfer setup to the human.

## GitHub workflow and immutable report

Fetch and verify the exact existing PR/branch/head, then amend only PR #77 on
its existing branch. Commit this activated order and exact `oap/active`
unchanged with the bounded repair, push, inspect and repair only in-scope CI
failures, create no PR and never merge.

Publish exactly
`oap/reports/078-b-repair-catalog-authority-and-render-parity.md` as the final
report-only child of a literal pushed implementation SHA with `Report
publication commit: SELF`. Report exact branch/base/PR/SHAs/files; authority
source/generation/drift/migration determinism; exact prop/RichText/Web behavior;
DB runtime-role denial and unchanged side effects; public Agent/OpenAPI raw-rank
denial; migration/Editor compatibility; exact tests/checks/skips; safety/scope;
remaining concurrency/Compose/design scope; and the strongest reason this round
or Objective 078 should not yet be accepted. Make no post-report push, signal
exact FIFO `OK`, then wait.
