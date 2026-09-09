# OAP Work Order — 078-g

## Objective and authoritative state

Add the first bounded Agent design layer on the existing Objective-078 PR: one
versioned design-system contract plus capability-bound component-local variant,
layout and responsive design mutation through the same normalized composition.
This round does not add site-global theme, page style, global regions,
header/footer architecture or media-dependent catalog breadth.

- Numeric objective: `078`; round: `078-g`; mode: `AMEND_EXISTING_PR`.
- Repository: `ulfe-lmi/slaif-agent-site`.
- Existing PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77),
  `main` <- `oap/078-agent-composition-design-semantics`; create no new PR.
- Verified remote `main`: `ae3a4a681bb888260192b7bb1b2a337b4906828d`.
- Required starting PR head: report-only commit
  `7d64b72c2732b08d2222e3e5b9a49a3b33c8a565`; its sole changed path is the
  immutable 078-f report and its parent is implementation commit
  `d8a292f7c7ebb8bc7bc42af84e4f36b8502be810`.
- Treat the 078-a through 078-f component data-plane/catalog/renderer/race/
  public-loop slice as closed unless this work exposes a regression.
- Numeric Objective 078 remains open and PR #77 must not be merged this round.

## 1. Versioned bounded design-system authority

Add one product-owned, deterministic, machine-readable `design-system/v1`
authority and expose it through:

```text
GET /api/agent/v1/design-system
```

The response requires `theme:read` (or a narrower existing read scope only if
the route-policy/OpenAPI contract documents it consistently), is bound to the
capability's site/catalog, and describes only code-defined safe choices:

- fixed responsive labels `desktop`, `tablet`, `mobile`; callers cannot define
  breakpoints or devices;
- bounded spacing/gap, width, alignment, column, radius, shadow and aspect-ratio
  tokens;
- exact per-component variants and the design properties each current catalog
  component supports;
- property type/default/requiredness/responsive behavior and the exact scope
  needed to change it; and
- design-system/catalog/composition/renderer versions needed for compatibility.

No CSS property/value language, arbitrary class name, selector, media query,
font URL, remote asset, raw color, HTML, code, expression, template, callback,
query or executable value may be accepted or exposed as an editable primitive.
The response must be explicit typed OpenAPI, not open dictionaries.

`catalog-v1` and its reviewed hash/migration 060 remain immutable. If current
catalog descriptors must change to encode design metadata, create an append-only
catalog version (for example `catalog-v2`) with a new deterministic migration,
generator/drift checks and backward reader. Do not silently edit catalog-v1
bytes or make historical migration 060 install different data. Define and test
the site/workspace upgrade rule: no active/review workspace may be silently
reinterpreted; compatible old normalized rows remain renderable and clean/new
workspaces bind the intended current version.

## 2. Component-local design mutation

Extend the existing exact Agent component PATCH rather than creating a raw
style endpoint. It may atomically change content and/or catalog-declared local
design props, but the server and trusted PostgreSQL helper derive and require
the union of scopes from the actual changed paths:

- content props: `component-content-props:write`;
- approved general component design props: `component-props:write`;
- variant selection: `component-variant:write`;
- structural layout choices such as columns/gap/width/alignment:
  `layout:write`;
- responsive desktop/tablet/mobile values: `responsive-design:write`.

Do not trust a caller-supplied authority/scope classification. A mixed request
requires every applicable scope. L1 retains existing content-only PATCH; L2
cannot change design; L3 may change the bounded local design fields; L4 inherits
L3. Keep `page-style:write`, `theme-tokens:write`, `theme-global:write`,
`global-region:*` and `header-footer:write` unused until their later operations
exist.

Use one exact optimistic row version, idempotency key, COW operation, quota
charge and `COMPONENT_UPDATED` semantic audit event per successful PATCH.
Replay is byte-equivalent/no second effect; mismatch is 409. Denied or malformed
design input changes no props/version/quota/idempotency/audit/COW state.
Cancellation rolls back all fields. Resource restrictions may narrow allowed
component types/variants/tokens/responsive editing; unknown constraint keys or
values fail closed.

At the trusted DB boundary validate the complete merged prop document against
the exact active catalog/design-system versions and derive all required scopes.
Direct runtime-helper invocation must not bypass a missing conditional scope.
Preserve site/workspace/page binding, frozen/non-active denial, catalog/schema
version checks and existing content-only behavior.

## 3. Normalized responsive and rendering contract

Represent responsive values as a stable bounded map keyed only by
`desktop`/`tablet`/`mobile`, with a documented deterministic cascade/fallback.
Do not store generated CSS, Puck blobs, arbitrary device widths or ad-hoc
breakpoint names. Values remain normalized catalog props and survive Puck
round-trip.

Render API and Web must consume the same normalized values and emit only trusted
classes/CSS variables selected by product code. Public, authenticated active
preview and browser preview use the same component implementation. Unknown or
wrong-version design data fails closed rather than disappearing silently.
Puck config must be generated from the same authority and expose only the
allowed variant/layout/responsive controls; Puck permissions are UX, while
Editor/Agent server validation remains authoritative.

## 4. Acceptance evidence

Through public Agent HTTP against real PostgreSQL with human-issued
capabilities, prove:

1. discovery returns the exact design-system document and current compatible
   catalog/version metadata;
2. L3 creates representative existing layout/content nodes, selects a component
   variant, changes width/columns/gap/alignment and desktop/tablet/mobile values,
   then exact-read/list/Render/Web observe the same normalized props/version;
3. a mixed content+design PATCH succeeds only for a capability holding every
   required scope;
4. L1 content-only PATCH still succeeds but its design/mixed request is denied;
   L2 design denial and each individually missing L3 conditional scope are
   proven;
5. direct `slaif_agent_runtime` helper attempts cannot bypass conditional
   scopes by adding/removing/changing a design, variant, layout or responsive
   field;
6. unknown token/variant/device/property, raw CSS/class/style/breakpoint/color/
   font/URL/executable/nested prototype input, stale version, foreign component,
   wrong catalog/design version, resource denial, quota exhaustion,
   replay/mismatch and cancellation are fail-closed with exact unchanged state;
7. Puck round-trip preserves exact normalized responsive/design props and
   crafted invalid Puck/Editor payload is rejected by the production server;
   and
8. two concurrent design PATCHes with one expected version yield one exact
   winner and one 409 loser under a deterministic PostgreSQL barrier, with one
   version/quota/idempotency/audit/COW effect.

Use executable Render/Web tests for representative values at all three logical
responsive labels. A source regex, schema existence or class-name snapshot alone
is not visual-semantic proof. A full clean Compose/browser workflow may be
reserved for the later combined design/theme acceptance round; this round must
still prove production public Agent + real PostgreSQL + trusted Render/Web
behavior locally/integration.

## Contracts, migration, docs and verification

Update production handlers, route policy and generated Agent OpenAPI with exact
conditional scopes and closed request/response schemas. Add append-only,
data-preserving downgrade/re-upgrade migration and exact owner/search-path/
PUBLIC/runtime grants if persistence or catalog version changes. Preserve
legacy valid compositions and Editor/Puck behavior.

Update `docs/API.md` and composition/design/testing documentation only for this
implemented local-design slice; keep theme/global regions/header/footer and
Objective 078 marked partial.

Run focused design-schema/validator/scope/resource/idempotency/audit/COW/
concurrency/cancellation/migration/privilege/Render/Puck/Web tests; full Agent
and Editor affected integration; generated catalog/OpenAPI/policy; Python unit/
repository and Node gates; formatting/typing/Markdown/Mermaid; and all
current-head GitHub checks. Pending/skipped is not pass. Do not use a broad
multi-hour suite as a substitute for focused proof.

## Non-goals and safety

- No site-global theme token mutation, theme schema/record API, page style,
  global regions, Header/Footer architecture, missing catalog component breadth,
  media bytes, MCP, exact-Agent-workspace Puck, freeze/review/promotion,
  source/sweep, site reset or release claim.
- No arbitrary CSS/JS/HTML/font URL/device/breakpoint/component code, dependency
  or image change, architecture/security exception, broad refactor, historical
  artifact edit, test weakening, production access or merge.
- Preserve issue #67 closure and zero-Critical supply-chain policy.

Routine PostgreSQL/Node/testing setup belongs to the passwordless-sudo
disposable executor environment; do not transfer it to the human.

## GitHub workflow and immutable report

Fetch and verify the exact existing PR/branch/head, then amend only PR #77.
Commit this order and exact `oap/active` unchanged with the bounded feature,
push, inspect and repair only in-scope CI failures, create no PR and never merge.

Publish exactly
`oap/reports/078-g-add-bounded-component-design-semantics.md` as the final
report-only child of a literal pushed implementation SHA with `Report
publication commit: SELF`. Report exact PR/SHAs/files; design authority and
version migration; route/OpenAPI conditional scopes; normalized responsive
contract; public Agent/DB/Render/Web/Puck positive and hostile evidence;
concurrency/cancellation/accounting; exact tests/checks/skips; docs/safety;
remaining theme/global/catalog work; and the strongest reason Objective 078 is
not yet acceptable. Make no post-report push, signal exact FIFO `OK`, then wait.
