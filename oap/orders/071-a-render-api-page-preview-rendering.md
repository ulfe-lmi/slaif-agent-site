# OAP Work Order — 071-a

## Objective

Create exactly one Objective 071 PR that implements the first real canonical
page and authenticated active-workspace preview rendering path. Render API must
produce a typed, read-only, site-confined page projection; the Web application
must render that projection with the same trusted React component catalogue
already used by Puck. Prove canonical/overlay isolation, private preview
authorization, real least-privileged PostgreSQL identities, strict public and
preview security headers, and full HTML through public NGINX. Do not implement
review snapshots, browser-worker automation, promotion, or adjacent closure
objectives. Do not merge.

## GitHub objective state and verified starting point

- Numeric objective: `071`; round: `071-a`.
- Mode: `CREATE_NEW_PR`; create exactly one new Objective 071 branch and PR
  from remote main
  `88decb8f59894672d4c63cc7434196749b424647`.
- Objective 070 PR #61 is merged. Its report head
  `dabe3f2abb147db0c831f2834d313c337a0715c3` is contained by that main
  merge. No Objective 071 PR currently exists; reconcile GitHub again before
  mutation.
- Render API is real but narrow: it owns one fixed
  `slaif_public_login`/`slaif_public_reader` pool and only
  `POST /internal/render/v1/site-context`. It does not project pages,
  compositions, bindings, themes, or workspace overlays.
- Web calls that site-context endpoint server-side and displays a truthful
  routing shell. Its catch-all route does not render editorial content.
- The trusted React component renderer exists at
  `apps/web/src/renderer/components.tsx` and Puck imports it, but it renders
  only part of the current catalogue, silently returns `null` for unknown
  types, treats rich text inconsistently with its schema, and is not yet used
  by public/preview routes.
- Current read-role hardening grants canonical/preview readers `SELECT` only on
  COW content views, not base/change tables or DML. Compose provisions both
  public and preview logins, but Render's isolated secret/config/runtime wires
  only the public locator. No preview authorization or COW session exists.
- Current public/preview page schema is `content.page` plus
  `content.page_composition`; collection views and items exist as bounded data.
  Review snapshot/promotion and public media finalization do not yet exist.
- The stale inert draft's proposal to render React HTML inside Python, accept a
  workspace UUID as trusted context, and add an NGINX route to an internal
  Render endpoint is explicitly superseded by this finalized order. Render
  returns projection JSON; Web alone returns HTML; untrusted identifiers are
  authorized before COW context; Render remains unreachable from the edge.

## Human-authorized strategic governance correction

The human directly authorized one correction to strategy-authored historical
prose: no prose line may begin with a hash character. Two exact uncommitted
strategic changes are present before activation and must be preserved without
further editing:

- `oap/orders/070-d-media-cross-worker-publication-race-proof.md` wraps the
  sentence as `... unchanged on` followed by `PR #61, ...`; its corrected
  SHA-256 is
  `ba7b2ccba238d65d9ff96c0d1ddba8dfc85feb57e9d057ccf9ab65220ea2500c`.
- `.markdownlint-cli2.jsonc` removes the now-unneeded exact 070-d MD018
  override and returns to SHA-256
  `796ac74a922107b0d8ddefbf5cf1bf842f6feda2e103b33841f540e1135e8ea0`.

These are human-authorized governance corrections, not Render implementation.
After fetching remote main, require that they are the only pre-existing local
diffs. Create the Objective 071 branch at exact remote main while preserving
them. Commit them unchanged with the exact activated 071-a order and
`oap/active` in a distinct first governance/transcript commit. Do not edit any
other prior order/report, do not reintroduce a lint exception, and report the
before/after hashes and authorization explicitly.

## Correct architecture and trust flow

The required request flow is:

```text
visitor or authenticated human browser
  -> public NGINX
  -> Next.js Web route
  -> authenticated internal Web-to-Render request
  -> Render canonical or preview read identity
  -> trusted site/page/workspace projection
  -> shared trusted React renderer in Web
  -> complete escaped HTML response
```

- Render API owns data projection and read identities, not React rendering.
- Web owns SSR HTML and uses one renderer implementation for public, preview,
  and Puck component previews. Do not duplicate component HTML in Python.
- NGINX exposes Web routes only. It must not proxy any Render internal route.
- A workspace UUID in a browser path is an untrusted lookup key. It becomes
  COW context only after current human session, site, workspace, membership,
  permission, lifecycle, and expiry authorization returns the same trusted
  site/workspace values.
- Network membership alone is not authentication. Web-to-Render calls require
  a generated, file-backed, constant-time-checked internal service credential
  available only to Web, Render, and one-shot initialization. Never expose it
  to browser JavaScript, HTML, logs, URLs, traces, or another service.

## Bounded scope and non-goals

Change only Render API/config/database/projection code, the Web server-only
Render client/routes/trusted renderer/styles, one new forward migration if
needed for a narrow preview authorization wrapper, isolated secret/Compose
wiring, directly necessary edge/security/config/API/testing documentation, and
focused/unit/integration/E2E/packaging tests.

- No review-snapshot rendering, frozen snapshot schema, review UI, selected
  operation projection, freeze, accept, discard, promotion, conflicts, cache
  outbox, public media finalization, media GC, browser-worker implementation,
  source inspection, screenshots, responsive-sweep jobs, dynamic News end-to-
  end fixture, destructive test, or release documentation pass.
- No public or NGINX route to Render API; no direct browser call to Render; no
  host port or extra external listener.
- No arbitrary HTML, `dangerouslySetInnerHTML`, executable rich text, runtime
  JSX/JavaScript/CSS, inline style props, remote fonts, raw SQL/query input,
  unknown components, or caller-provided internal URL.
- No Agent capability accepted by human preview and no human cookie forwarded
  to browser workers. Agent/browser preview credentials remain Objective 072.
- No component catalogue definition expansion, Puck persistence redesign,
  physical content-model tables, dependency addition, hosted service, or
  renderer-package refactor unless a minimal extraction is strictly necessary
  to use the same pure React code in Puck and SSR.
- Do not alter migrations 006 through 031. Any database change is one new
  deterministic forward migration with one Alembic head.

## 1. Typed canonical and preview projection

Retain the existing site-context endpoint and add internal, extra-forbid typed
projection endpoints under `/internal/render/v1/`:

1. canonical projection accepts normalized authority/path and derives active
   site, matched site prefix, locale, and page route server-side;
2. preview projection accepts the same route plus an untrusted workspace lookup
   and current human session proof from authenticated Web, then derives the
   trusted site/workspace through the authorization boundary before any COW
   session is opened.

Use stable endpoint names and document them. Responses are bounded JSON, never
HTML, and include at minimum:

- render mode, site ID/key and canonical revision;
- requested/matched route, locale, page ID/title/status/row version;
- composition/catalog/schema versions and a deterministic normalized component
  tree with stable IDs, slots, order, schema versions, validated props, and
  resolved bounded data bindings;
- only the theme/navigation/media-reference data needed by the current trusted
  components, with no storage path, database identity, token, or secret.

Canonical projection uses only the canonical public-reader pool with no COW
setting and returns only publicly renderable canonical pages. Draft/deleted/
unknown/wrong-site routes return non-leaking 404. Preview uses the authorized
workspace overlay with canonical fallback; draft overlay pages may render, and
overlay tombstones must hide canonical rows. Reads create no COW operation,
idempotency row, audit event, or mutation.

Route resolution must be deterministic and bounded. Support the current page
slug/locale model honestly; do not claim nested route, redirect, or locale
behavior that the schema does not implement. Reject traversal, reserved
application prefixes, duplicate/ambiguous page routes, invalid locale, and
inactive site. Page ID alone must never bypass route/site confinement.

Validate projection defensively: same site/page for every node and binding;
known catalogue type and matching schema version; bounded count/depth/props;
no cycle, missing parent, cross-page parent, duplicate ID/order ambiguity, bad
slot, unknown executable prop, or unsupported version. Child ordering is
stable by parent/slot/order plus deterministic tie-breaker. Malformed canonical
or overlay data fails closed without partially rendering or leaking data.

For `CollectionList`, `CollectionGrid`, and `CollectionDetail`, resolve the
declared collection-view reference only within the same site/workspace and
return a bounded item projection. Implement only an already-defined safe query
subset; unsupported filter/sort/projection syntax fails closed rather than
becoming raw SQL or silently broadening results. Enforce catalogue/item/view
limits and deterministic order. This is representative binding support, not
the dynamic News vertical.

## 2. Real least-privileged identities and COW semantics

- Keep canonical reads on fixed `slaif_public_login` with sole membership in
  `slaif_public_reader`.
- Add a separate Render-owned preview pool using fixed
  `slaif_preview_login` with sole membership in `slaif_preview_reader`; never
  reuse the public pool or Editor/Agent/Control/reviewer/setup credentials.
- Provision and mount both isolated DSN files only to Render and one-shot
  secret initialization. Web receives no database locator.
- Preview projection enters one `asyncpg_cow_session` only after trusted
  authorization, with session ID equal to the returned workspace UUID. It
  performs read-only view queries, rolls back/cleans context on success,
  denial, exception, disconnect, and cancellation, and leaves the pool reusable
  without site/workspace/operation bleed.
- Add only the narrow owner-defined preview-authorization function(s) required
  to validate a human session and existing workspace/site context. Grant only
  exact `EXECUTE` to the preview role. Do not grant generic Control tables,
  generic content functions, base/change tables, sequences, DML, reviewer,
  setup, capability-mint, or lifecycle mutation authority.
- Authorization must require active account/session/site/membership, current
  `preview:inspect`, existing authorized workspace, matching site/creator or
  explicit all-workspace read authority, ACTIVE lifecycle, and unexpired
  workspace. It must not create/resolve a new editor workspace on GET.
- Prove the public reader cannot see workspace overlay state or set a useful
  Render COW projection; prove preview reader cannot DML, inspect base/change,
  call Editor/Agent mutation, lifecycle, reviewer, or generic Control APIs.

## 3. Internal service authentication and Web routes

- Generate one high-entropy Render-call credential during one-shot local secret
  initialization and materialize process-owned read-only copies for Web and
  Render. Existing secret mode, no-symlink, ownership, one-shot, networkless,
  rotation/readiness, and no-extra-mount policies remain enforced.
- Authenticate the internal request in constant time before parsing/using
  projection authority. Reject missing, duplicate, malformed, or wrong
  credentials with a stable non-leaking outcome. Never use an environment
  plaintext secret in production mode.
- Web's canonical catch-all calls canonical projection server-side and renders
  the result. The loopback setup landing behavior remains available only under
  its established trusted condition.
- Add a specific authenticated human route shaped like
  `/preview/{workspace_id}/{site_path...}`. It reads the HTTP-only human session
  cookie only on the server, never sends it to client code/storage, and calls
  preview projection. Missing session returns 401/login-safe behavior; wrong
  site/workspace/membership or invisible resources return non-leaking 404;
  expired/revoked authority fails closed.
- Do not place human session, internal service credential, capability, or
  workspace authority in query strings, HTML, React props sent to client code,
  local/session storage, cache keys visible to clients, logs, or browser
  artifacts.

## 4. One trusted React renderer and complete HTML

Use the existing pure React renderer as the single component implementation for
Puck preview and public/active-preview SSR. Remove client-only marking from pure
renderer code if needed, without breaking Puck's client boundary.

- Build the normalized tree once from the typed projection and recursively
  render children by declared slot and deterministic order.
- Implement rendering for every current component definition in
  `COMPONENT_CATALOG`; do not modify the catalogue to make the test easier.
  Context-dependent components receive only trusted projected data.
- Unknown type/schema/slot or malformed binding must fail the page closed; do
  not silently return `null` and omit content.
- React escaping is authoritative. Structured rich text renders through an
  explicit safe allowlist without raw HTML. URLs/media references are validated
  same-origin/product routes; reject executable/data/file URLs and event/style
  props. No inline styles or scripts are generated from editorial data.
- Public and preview use the same renderer functions, CSS classes, catalogue
  versions, and normalized ordering. Add renderer contract tests that fail if
  Python trusted component types, TypeScript catalogue, Puck adapter, and SSR
  renderer drift.
- Return a complete semantic Next.js HTML document through NGINX with page
  title, language, one main region, stable headings/content/order, accessible
  images/links/lists, and no hydration/console/CSP failure relevant to the
  rendered page.

## 5. Headers, cache, CSP, and edge confinement

- Canonical public responses may use a canonical-revision-aware ETag/cache
  policy but must never cache workspace state. Unknown/inactive/unpublished
  pages are non-leaking 404.
- Every preview response, including error/redirect, uses
  `Cache-Control: private, no-store`, `Pragma: no-cache`, and
  `X-Robots-Tag: noindex, nofollow, noarchive`; no preview sitemap.
- Preserve strict script policy. Public and preview renderer use class-based
  styling and do not inherit the editor-only Puck style exception. No new
  `unsafe-inline`/`unsafe-eval` script capability and no public style-policy
  relaxation.
- NGINX and Apache continue routing application pages to Web. Add no Render
  proxy location. Prove external attempts to `/internal/render/`,
  `/render/internal/`, and the concrete projection endpoints cannot reach
  Render or disclose internal status/body.
- Render retains private/no-store/noindex response headers on all internal
  routes and binds no host port. Browser-visible security headers remain
  correct through both edge adapters.

## 6. Required proof

Add focused unit/contract tests and real PostgreSQL/public-edge evidence:

1. exact public and preview login identities, sole memberships, function grants,
   and denials for DML/base/change/generic Control/Editor/Agent/reviewer/setup;
2. canonical published page plus nested trusted components renders expected
   escaped headings/content/order through NGINX and a real browser;
3. real human-authenticated workspace edit appears immediately in preview but
   not canonical; untouched canonical nodes fall back; a workspace tombstone is
   absent only in preview; no COW/idempotency/audit residue;
4. two workspaces and two sites cannot cross-read; wrong workspace/site, missing
   session, revoked/expired session, inactive membership/site, expired/revoked
   workspace, forged service credential, and arbitrary page UUID fail closed;
5. representative collection list/grid/detail binding resolves same-site
   workspace-aware items with deterministic bounds and rejects cross-site view,
   unsupported query, missing item, and excessive limits;
6. every catalogue component has one SSR implementation; malformed tree,
   unknown type/version/slot, cycle, cross-page parent, unsafe URL/prop/rich
   text, and executable markup are rejected without raw HTML/script/style;
7. public strict CSP, preview no-store/noindex, editor-specific CSP isolation,
   no token leakage, no Render edge route, and internal service-secret file/
   mount/mode/ownership/rotation/readiness contracts;
8. cancellation/disconnect and projection/database errors close response/pools,
   clear COW settings, and return stable 404/401/503 outcomes without partial
   HTML or cross-request bleed; and
9. clean Compose starts with only NGINX published, public and authenticated
   preview HTML work through NGINX, direct Render access is impossible, and
   prior Puck/Agent/Media/security E2E remains green.

Use actual HTTP routes and real PostgreSQL roles for authority claims. Unit
tests or interface existence alone are insufficient. Browser acceptance must
inspect rendered DOM text/order, response headers, console errors, failed
requests, unsafe elements/attributes, and canonical-versus-preview state.

## Acceptance criteria

- Public visitors receive real canonical HTML generated by trusted React from a
  site-confined Render projection; Render itself returns no duplicated HTML.
- Authenticated authorized humans receive current workspace-overlay HTML with
  canonical fallback, while public canonical output remains unchanged.
- Preview IDs are authorized before COW selection; cross-site/workspace and
  expired/revoked authority fail closed.
- Canonical and preview pools use exact separate read-only identities with no
  write/reviewer/setup/base/change authority and no context bleed.
- Public/preview/Puck use one catalogue/renderer; data is escaped and no
  arbitrary executable markup, style, script, URL, or unknown component runs.
- Preview is private/noindex/no-store; public CSP stays strict; Render remains
  internal and service-authenticated.
- The human-authorized 070-d line correction and removal of its obsolete lint
  override are committed exactly; all other historical artifacts remain
  unchanged.
- All focused, full, Compose, browser, PostgreSQL 14–18, repository, dependency,
  license, supply-chain, and fresh GitHub checks pass.

## Verification, documentation, and workflow

Run and report exact focused Python/Node renderer/projection/auth tests; full
backend unit/repository/integration suites; frozen Python quality/mypy/build and
all process checks; all frozen Node lint/format/type/test/build/license gates;
new migration head/clean upgrade/downgrade-upgrade and privilege validation;
static NGINX/Apache/Compose/secret policy; clean Compose and Playwright through
public NGINX; PostgreSQL 14–18; Markdown/Mermaid; supply-chain/SBOM; and every
fresh GitHub required check. Mark retries, failures, skips, and not-run items
honestly.

Update API, configuration, database-role/connection, service-authority,
security, deployment, testing, operations, and user-facing implemented-versus-
planned text only where behavior changes. Remove stale claims that editorial
rendering is absent, but do not claim snapshots, publication, browser-worker
agent feedback, public media finalization, nested route/localization breadth,
or release readiness beyond executable proof.

Create one fresh Objective 071 branch and PR from exact remote main; no existing
Objective 071 PR may be reused. Commit the strategic governance/transcript
correction first, then bounded implementation/tests/docs. Push all non-report
work, inspect and safely repair only in-scope CI failures, and never merge or
enable auto-merge.

Publish exactly
`oap/reports/071-a-render-api-page-preview-rendering.md` as one report-only
child with `Report publication commit: SELF`. Its first parent must be the
literal reported implementation-head SHA. Verify remote PR/head/parent/path,
then signal exact FIFO `OK`.

The report must state `COMPLETE|PARTIAL|BLOCKED|FAILED`; PR/base/branch and all
SHAs; the human-authorized governance hashes; exact projection/auth/COW/SSR
flow; route and header matrix; Render/Web identities/grants/secret mounts;
canonical/preview/site/workspace/binding/tree/security evidence; files,
dependencies, migrations, docs; every local and CI result/intermediate failure;
limitations/non-goals; no extra PR; and no merge.
