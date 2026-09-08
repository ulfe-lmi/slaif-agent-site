# OAP Work Order — 078-i

## Objective and authoritative state

Implement the bounded site-theme token data plane on the existing Objective-078
PR: one typed theme schema, capability-bound Agent discovery/read/update,
strict COW/version/scope/idempotency/audit/concurrency semantics, and shared
Render/Web/Puck consumption. This round does not implement global regions,
header/footer architecture or per-page style.

- Numeric objective: `078`; round: `078-i`; mode: `AMEND_EXISTING_PR`.
- Repository: `ulfe-lmi/slaif-agent-site`.
- Existing PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77),
  `main` <- `oap/078-agent-composition-design-semantics`; create no new PR.
- Verified remote `main`: `ae3a4a681bb888260192b7bb1b2a337b4906828d`.
- Required starting PR head: report-only commit
  `8d634a9aca227366c0e65d2785aa241532a6b9d4`; its sole changed path is the
  immutable 078-h report and its parent is implementation commit
  `7597975cfff30a1f31eab4f4d5871695e3ef7fcb`.
- All 20 required checks on that exact head are green. Preserve accepted
  078-a through 078-h component/catalog/local-design behavior and authority.
- Numeric Objective 078 remains open and PR #77 must not be merged this round.

## 1. Product-owned theme schema

Add one deterministic machine-readable `theme-schema/v1` authority, generated
or exact-drift-checked across Python, PostgreSQL, TypeScript/Puck, Render/Web and
Agent OpenAPI. Expose:

```text
GET /api/agent/v1/theme-schema
GET /api/agent/v1/theme
PATCH /api/agent/v1/theme
```

Both reads require `theme:read`. PATCH requires `theme-tokens:write`; reserve
`theme-global:write` for the later global-region/header/footer architecture
unless an exact global-only field is deliberately introduced here. The typed
schema and response must be closed OpenAPI, never `dict[str, Any]`.

Theme state is a singleton per site/workspace projection with stable ID,
immutable site ID, `theme-schema/v1`, positive row version and timestamps. Its
bounded groups are:

- palette: approved product-owned accessible palette preset/role tokens;
- typography: locally packaged/system-approved family and bounded scale/weight
  tokens, never a remote font or arbitrary family/string;
- layout: approved content width, spacing and grid-gap tokens; and
- shape: approved radius and shadow tokens.

Choose a small documented useful MVP token vocabulary compatible with the
existing design-system tokens. Palette combinations must have product-validated
contrast for their declared roles; do not accept arbitrary CSS, selectors,
custom properties, raw styles, remote URLs/fonts, uncontrolled color strings,
breakpoints, code or executable values. If bounded canonical color values are
needed internally, callers select stable token/preset keys and never submit raw
CSS syntax.

The schema publishes exact defaults, enum values, accessibility/contrast class,
renderer version and compatibility versions. Unknown/missing/malformed keys,
wrong schema version and prototype/executable input fail closed.

## 2. Fix the legacy theme substrate

The existing migration-020 theme model/functions are shallow, lack row version
and allow open JSON; `slaif_theme_get` is declared `STABLE` while attempting an
INSERT. Replace that behavior through an append-only migration from current head:

- GET is truly read-only and never lazily writes, charges quota, creates audit,
  touches COW or changes timestamps;
- existing sites receive a deterministic valid default theme through safe
  backfill/provisioning, and newly created sites receive the same default as a
  platform initialization rather than an editorial read side effect;
- existing valid theme data is deterministically normalized/migrated or the
  upgrade fails with an actionable validation error; never silently discard
  user state or use `CASCADE` data loss;
- add positive row version and schema/renderer version continuity;
- legacy Editor/Puck theme reads/updates use the same validator and workspace
  semantics, with their existing human permission boundary preserved; and
- downgrade restores exact prior functions/columns/data representation needed
  by the previous revision, with a data-bearing downgrade/re-upgrade proof.

Preserve setup/control/runtime/reviewer credentials, COW hardening, owners,
fixed `search_path`, PUBLIC revocation and least-privilege grants. Control's
online role must not acquire general content DML merely to provision defaults.

## 3. Agent theme mutation semantics

PATCH is a partial group/token update with an explicit positive expected row
version and `Idempotency-Key`. The trusted server resolves site/workspace/
operation and the DB helper reasserts active capability/workspace state,
`theme-tokens:write`, resource constraints and the exact schema after the
workspace lifecycle/structural lock.

One successful PATCH atomically produces one row-version increment, mutation
quota charge, idempotency completion, COW operation and semantic audit event:

```text
THEME_UPDATED  theme  PATCH  200  mutation
```

Replay returns the exact stored response with no second effect; same key with a
different request is 409. Stale version, invalid/unsupported token, missing
scope, narrowed palette/typography/token resource policy, quota exhaustion,
foreign site/workspace, revoked/expired/frozen/non-active state and cancellation
leave row/version/quota/idempotency/audit/COW exactly unchanged. A byte-
equivalent no-effect PATCH follows the no-effect convention established in
078-h rather than manufacturing a theme event.

Serialize competing theme writes deterministically. Two concurrent PATCHes with
one expected version must produce exactly one 200 and one 409 under a real
PostgreSQL barrier, with one durable effect. Independent workspaces/sites remain
concurrent and invisible.

## 4. Shared Puck/Render/Web behavior

Puck obtains its theme controls from the same schema; Puck permissions remain
UX and the Editor server rejects crafted invalid/unauthorized data. Theme state
is normalized product data, not an opaque Puck blob.

Render projection must include the exact visible theme record/version. Web
applies it through trusted predeclared classes/assets/CSS generated by product
code, not unsafe inline arbitrary CSS. Public, active preview and later snapshot
paths share that renderer; this round proves canonical and workspace preview
separation. Theme changes must visibly affect representative palette,
typography, layout and shape output in authenticated preview while anonymous
public output remains canonical.

Add executable React/SSR and Puck round-trip tests for every token group,
including safe escaping/no style or credential injection. A source regex, JSON
presence or projection-only 200 is insufficient.

## 5. Acceptance evidence

Through public Agent HTTP against real PostgreSQL with human-issued capabilities:

1. exact theme schema/default state is discovered without any read side effect;
2. L3 updates representative tokens from all four groups, reads the exact new
   version, and Render/Web preview visibly uses them;
3. L1/L2 and narrowed/missing-scope capabilities are denied; L3 cannot use
   `theme-global:write` as a substitute and an unrelated L4-only scope cannot
   bypass `theme-tokens:write`;
4. foreign site/workspace/theme IDs remain invisible; canonical and another
   workspace/site remain unchanged;
5. invalid palette/contrast/font/layout/shape/raw CSS/color/font URL/device/
   executable/version/resource/quota/idempotency cases fail with exact stable
   errors and no residue;
6. replay/no-effect/stale/cancellation semantics and direct-runtime helper
   authority are exact;
7. deterministic concurrent same-version PATCH has one winner; and
8. Editor/Puck uses the same normalized contract without gaining publication or
   canonical-write authority.

Update route policy and canonical generated Agent OpenAPI bidirectionally.
Update `docs/API.md`, design/theme/testing docs, README/MVP ledgers only for
implemented source-revision behavior; keep global regions/header/footer/page
style, Objective 078 and MVP partial.

Run focused schema/theme/Agent/Editor/COW/scope/resource/idempotency/audit/
concurrency/cancellation/migration/privilege/Render/Puck/Web tests; affected
Agent/Editor integration; generated drift/policy/OpenAPI; Python unit/repository
and Node gates; quality/Markdown/Mermaid; and all current-head GitHub checks.
Pending/skipped is not pass. A later combined design acceptance round may own
the full clean Compose/browser workflow; do not substitute broad runtime volume
for missing focused theme proof.

## Non-goals and safety

- No global regions, header/footer architecture, `theme-global:write`, page
  style, missing catalog component breadth, media bytes, MCP, exact-Agent-
  workspace Puck, freeze/review/promotion, source/sweep, site reset or release
  claim.
- No arbitrary CSS/JS/HTML/raw font/color/URL/breakpoint/component code,
  dependency/image/architecture/security exception, broad refactor, historical
  artifact edit, test weakening, production access or merge.
- Preserve issue #67 closure and zero-Critical supply-chain policy.

Routine PostgreSQL/Node/testing setup belongs to the passwordless-sudo
disposable executor environment; do not transfer it to the human.

## GitHub workflow and immutable report

Fetch and verify the exact existing PR/branch/head, then amend only PR #77.
Commit this order and exact `oap/active` unchanged with the bounded feature,
push, inspect and repair only in-scope CI failures, create no PR and never merge.

Publish exactly `oap/reports/078-i-add-bounded-site-theme-tokens.md` as the
final report-only child of a literal pushed implementation SHA with `Report
publication commit: SELF`. Report exact PR/SHAs/files; theme schema/default/
migration and read purity; route/OpenAPI/scopes; public Agent/DB/Puck/Render/Web
positive and hostile evidence; concurrency/cancellation/accounting/isolation;
tests/checks/skips; docs/safety; remaining global/page-style/catalog work; and
the strongest reason Objective 078 is not yet acceptable. Make no post-report
push, signal exact FIFO `OK`, then wait.
