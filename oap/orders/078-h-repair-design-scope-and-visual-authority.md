# OAP Work Order — 078-h

## Objective and authoritative state

Repair the component-design least-privilege and OpenAPI truth defects found in
078-g on the existing Objective-078 PR. Make design-only, content-only, mixed
and responsive PATCH authority exactly match the changed normalized properties,
and classify currently exposed visual props as design rather than L1 content.

- Numeric objective: `078`; round: `078-h`; mode: `AMEND_EXISTING_PR`.
- Repository: `ulfe-lmi/slaif-agent-site`.
- Existing PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77),
  `main` <- `oap/078-agent-composition-design-semantics`; create no new PR.
- Verified remote `main`: `ae3a4a681bb888260192b7bb1b2a337b4906828d`.
- Required starting PR head: report-only commit
  `8d956e428c119be037d74cd9d4c7c89beb9ffb83`; its sole changed path is the
  immutable 078-g report and its parent is implementation commit
  `dc5e2b863dc786445fd05a80c3029edef37d8b7e`.
- All 20 required checks on that exact report head are green. Green CI does not
  cure the scope/contract defects below.
- Preserve accepted 078-a through 078-f behavior and valid 078-g design-system,
  responsive normalization, renderer/Puck, concurrency/cancellation and
  migration foundations. Objective 078 remains open; do not merge PR #77.

## Exact defects

1. Agent `PATCH /components/{component_id}` calls
   `_require_scope(context, "component-content-props:write")` before deriving
   scopes, and route policy declares that fixed scope. Thus a narrowly delegated
   design-only capability is denied even when it has every scope required by the
   actual design-only change. This contradicts the ordered union-of-changed-
   paths contract.
2. Generated `x-slaif-component-design-scopes` lists
   `responsive-design:write` for every property because the descriptor says the
   property is responsive. Runtime requires it only when the submitted value is
   a responsive map. OpenAPI therefore overstates scalar requirements and is not
   an exact description of enforcement.
3. `component-props:write` appears in docs/types but no design-system property
   uses it, so the positive/missing-scope criterion was not actually proven.
4. Existing catalog props with visual meaning remain L1 content in runtime:
   `Button.variant`, `Image.aspectRatio`, and `CollectionGrid.columns`. L1 can
   currently change component variants/layout despite the architecture placing
   variants and design at L3.

## Required repair

### 1. Exact changed-property scope union

Remove the unconditional content-write requirement from the public handler,
route policy and trusted database update path. Authenticate and bind the
capability/site/workspace normally, read the exact visible component, derive
changed-property authority from trusted design/catalog data, then require:

- content-only change -> `component-content-props:write` only;
- general local design change -> `component-props:write` only;
- variant change -> `component-variant:write` only;
- layout change -> `layout:write` only;
- responsive-map value -> its property scope plus
  `responsive-design:write`;
- mixed request -> the deterministic union of all applicable scopes.

A no-effective-change PATCH must have a documented least-authority rule and
must not become a way to consume or create misleading mutations. Prefer a
byte-equivalent idempotent unchanged response with no quota/audit/COW effect;
if preserving the existing deliberate versioned-no-op convention is necessary,
name and justify the required scope explicitly and test it.

The trusted PostgreSQL helper must derive the same union and remain safe when
invoked directly as `slaif_agent_runtime`; no Python-only scope boundary and no
caller-supplied classification. Missing any one scope denies before quota,
idempotency completion, audit or COW mutation.

### 2. Correct visual-property classification

Extend `design-system/v1` only through its deterministic source/generator and
drift checks so currently public visual props have the correct authority:

- `Button.variant` -> `component-variant:write`;
- `Image.aspectRatio` -> `component-props:write` (or `layout:write` only if the
  design authority consistently classifies aspect ratio as layout; prefer the
  former to make the architecture's general component-design scope real);
- `CollectionGrid.columns` -> `layout:write`.

Add at least one safe, catalog/design-declared general component property such
as bounded radius or shadow only if needed to establish meaningful
`component-props:write`; it must use existing token vocabularies and trusted
renderer classes, never raw values. Do not enable the current free-form
`Section.background` until the later bounded global theme/palette contract can
replace arbitrary strings.

For every newly classified property, decide explicitly whether responsive maps
are supported. If supported, Render/Web CSS and Puck must implement the exact
desktop/tablet/mobile semantics; if scalar-only, the design-system descriptor
and OpenAPI must say so and responsive objects must be rejected. L1 content
updates to labels/text/href/alt remain allowed but cannot change these visual
properties. Preserve valid previously stored scalar values through the same
renderer/backward reader.

### 3. Exact route-policy/OpenAPI contract

Represent property-dependent authority bidirectionally in route policy and
generated OpenAPI without pretending all properties share one fixed scope.
The extension must distinguish at least:

- scalar required scope(s);
- whether a responsive map is allowed; and
- the additional responsive scope when such a map is supplied.

An empty ordinary `x-slaif-conditional-scopes` plus a contradictory custom
table is not sufficient. Extend route-policy validation as needed so production
handler, trusted derivation and canonical OpenAPI drift together. No
undocumented production route or schema-only operation.

### 4. Hostile acceptance

Through public Agent HTTP against real PostgreSQL, use deliberately narrowed
human-issued capabilities to prove independently:

- design-only scalar PATCH succeeds without content or responsive scope;
- responsive design PATCH succeeds without content scope but only with both
  property and responsive scopes;
- content-only PATCH succeeds without any L3 design scope;
- mixed content+variant+layout/general+responsive PATCH requires the exact
  union; remove each scope one at a time and assert 403 plus unchanged props,
  version, quota, idempotency, audit and COW operations;
- L1 cannot change Button variant, Image aspect ratio, CollectionGrid columns,
  or any new general design token, while authorized L3 operations succeed;
- direct runtime-helper calls with each missing scope fail identically;
- scalar values are not misdetected as responsive, malformed/custom device maps
  fail, and replay/mismatch/stale/cancellation/concurrent-winner behavior remains
  exact; and
- Render/Web and Puck visibly/structurally implement each newly classified
  property and preserve it on round-trip.

Use real media/view fixture records only as neutral prerequisites for Image and
CollectionGrid; do not implement Agent media upload or new collection behavior.
Update focused docs to stop claiming `component-props:write` behavior until it
is genuinely executable and make scalar-versus-responsive requirements exact.

## Verification and non-goals

Run focused public Agent/DB scope and unchanged-state tests, direct-runtime
tests, deterministic concurrent/cancellation regression, Puck/Render/Web
behavior, design generator/OpenAPI/route policy, migration/downgrade privilege,
Python unit/repository and Node gates, quality/Markdown/Mermaid and all
current-head GitHub checks. Pending/skipped is not pass. Do not substitute a
multi-hour broad suite for missing focused authority evidence.

No site-global theme/page style/global regions/header/footer, catalog breadth,
media bytes, MCP, exact-Agent-workspace Puck, freeze/review/promotion,
source/sweep, site reset, dependency/image/architecture/security exception,
broad refactor, historical artifact edit, test weakening, production access or
merge. Preserve issue #67 closure and zero-Critical supply-chain policy.

Routine PostgreSQL/Node/testing setup belongs to the passwordless-sudo
disposable executor environment; do not transfer it to the human.

## GitHub workflow and immutable report

Fetch and verify the exact existing PR/branch/head, then amend only PR #77.
Commit this order and exact `oap/active` unchanged with the bounded repair,
push, inspect and repair only in-scope CI failures, create no PR and never merge.

Publish exactly
`oap/reports/078-h-repair-design-scope-and-visual-authority.md` as the final
report-only child of a literal pushed implementation SHA with `Report
publication commit: SELF`. Report exact PR/SHAs/files; before/after scope table;
route-policy/OpenAPI representation; each narrowed capability and direct-DB
result with unchanged effects; visual property Render/Puck proof; exact tests/
checks/skips; docs/safety; remaining theme/global/catalog work; and the
strongest reason Objective 078 is not yet acceptable. Make no post-report push,
signal exact FIFO `OK`, then wait.
