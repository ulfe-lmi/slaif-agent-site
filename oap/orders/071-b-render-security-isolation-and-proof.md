# OAP Work Order — 071-b

## Objective

Continue Objective 071 on the existing PR #62. Preserve 071-a's genuine typed
Render projection, separate reader pools, Web-owned shared React SSR, internal
credential, clean Compose/browser path, and human-authorized governance
correction. Repair only the concrete authorization, projection-integrity,
route/error, secret-loading, media-reference, and evidence gaps found in
strategic source review. Do not redesign rendering, add adjacent lifecycle
features, or merge.

## Verified starting state and findings

- Numeric objective: `071`; round: `071-b`.
- Mode: `AMEND_EXISTING_PR`; amend only PR #62 on
  `oap/071-render-api-page-preview`. Create no new PR.
- Begin from verified remote 071-a report head
  `36f7007d761a41af143f6239792077a7671ea94b`; its sole parent is final
  implementation head `bd4679aa3ee78f41dc54b9270a5b28e2951e0091`
  and its sole changed path is
  `oap/reports/071-a-render-api-page-preview-rendering.md`.
- Remote main remains
  `88decb8f59894672d4c63cc7434196749b424647`; PR #62 is open,
  non-draft, and mergeable. Report-head CI was still finishing when this round
  was selected; reconcile it but do not mistake green CI for acceptance.
- 071-a is genuine progress and must be retained: JSON-only canonical/preview
  projection; React HTML only in Web; separate public/preview pools and DSNs;
  migration 032 narrow wrapper; generated Web-to-Render secret; Render edge
  denial; full catalogue renderer; 106 integration tests; clean eight-project
  browser/Compose smoke; and fresh implementation-head CI.
- Finding 1 — migration 032 validates only absolute session expiry. It omits
  the established idle timeout and touch/finalization semantics used by
  `HumanSessionService`, so an idle-expired human session may authorize preview.
- Finding 2 — preview authorization occurs on one acquired connection, which is
  released, then COW projection opens a separate transaction/connection. A
  session/workspace/membership/site can be revoked between those steps. The
  authorization is neither reasserted nor held under the workspace shared lock
  in the transaction that reads the overlay.
- Finding 3 — `RenderServiceAuthenticationMiddleware` rereads a path from the
  environment on every request instead of using the startup-validated secret;
  it does not validate no-symlink/type/mode/owner at use time, and a missing
  token makes the expected byte string empty, so one empty credential header
  can compare successfully. Web's reader similarly lacks runtime file policy
  validation. Test mode bypasses authentication wholesale rather than proving
  missing/duplicate/wrong/correct credentials.
- Finding 4 — composition slot validation compares each child's `slot_key` to
  the child's own allowed slots. Slots belong to the parent. This can reject a
  valid child under `Hero.content` and accept an invalid child slot under a
  parent that does not expose it.
- Finding 5 — collection binding builds reserved identity fields and then
  expands editorial item values over them, allowing values named `id`, `slug`,
  or `status` to spoof projection metadata. A declared `projection_spec` is
  syntax-checked but ignored, so unprojected values are returned.
- Finding 6 — the public catch-all falls back to `SiteContextShell` for every
  unresolved path within an active site. Unknown or unpublished subpaths can
  therefore return 200 instead of non-leaking 404. The non-loopback root page
  also does not first attempt canonical page projection.
- Finding 7 — projection prop defense checks only top-level forbidden keys and
  URL prefixes, not required/types/enums/bounds or nested executable keys/
  values. Site catalogue version is not read/checked; response versions are
  hardcoded.
- Finding 8 — `Image` emits `/media/{uuid}`, which is not the implemented Media
  route. Canonical public media finalization remains intentionally absent, so
  the renderer must not emit a broken or falsely public URL.
- Finding 9 — the real PostgreSQL file has two expected-path tests only. It does
  not prove idle/revoked authority, race recheck, Agent/import workspace human
  preview, second site/workspace isolation, tombstone/fallback, read residue,
  or the claimed DML/base/change/generic-function denials. Browser changes only
  update the canonical demo heading; no real authenticated Playwright preview
  navigation proves overlay HTML and headers.

## Bounded scope and non-goals

Change only migration 032 by a new forward migration 033 if SQL behavior must
change, Render auth/projection/config/database code, server-only Web Render
client/routes/renderer, exact secret/edge/Compose policy, focused tests, and
directly necessary docs. Preserve the 071-a route families and architecture.

- Do not edit migrations 006 through 032; use one forward migration 033 with
  one Alembic head if required.
- No review snapshot, freeze, review UI, accept/discard/promotion, conflict,
  public media publication/finalization, browser-worker implementation,
  capability preview credential, source inspection, dynamic News vertical,
  destructive test, dependency addition, or broad renderer redesign.
- Do not alter the component catalogue to make validation pass. Do not expose
  Render at NGINX/Apache or accept raw SQL/HTML/JS/CSS.
- Preserve the human-authorized 070-d prose correction, removal of the obsolete
  MD018 override, activated 071-a order, and published 071-a report unchanged.
- No extra PR and no merge.

## 1. Exact human-session semantics and race-safe preview reads

- Make the narrow Render preview authorization use the same idle timeout,
  absolute expiry, revocation, active-account, and touch/finalization semantics
  as normal read-only human session authentication. Do not grant the preview
  role direct generic session-finalizer authority; encapsulate it in the exact
  owner-defined Render wrapper and pass only validated bounded policy values.
- A first authorization may derive the trusted site/workspace UUID, but the
  COW read transaction must reassert the complete mutable authority on its own
  connection before any content query, acquire the accepted workspace shared
  advisory transaction lock, and keep it through projection completion. Use
  the trusted UUID returned by authorization, not the raw request UUID, for COW
  context. No content read may occur between context setup and in-transaction
  reauthorization.
- Add a deterministic race: pause preview after initial authorization but
  before its transaction recheck; revoke/expire the session, deactivate
  membership/site, or revoke/expire the workspace; resume and prove denial with
  zero content leak, COW operation, idempotency, or audit residue.
- Permit human-authorized preview of active `HUMAN`, `AGENT`, and `IMPORT`
  workspaces where the current user is creator/delegator or has
  `workspace:read-all` plus `preview:inspect`; continue denying `SYSTEM`, wrong
  site, inactive/expired/revoked state, or absent authority. Do not create a
  workspace on GET.
- Reuse and clean the preview pool after success, denial, exception, timeout,
  disconnect, and cancellation with no retained COW settings or transaction.

## 2. Fail-closed internal credential

- Resolve and validate the Render service credential once during application
  startup through the typed settings boundary. Pass immutable secret bytes to
  middleware; never reread an environment-selected path per request.
- Validate regular file, no symlink, exact private mode and owner, nonempty
  bounded ASCII shape, and process-owned secret directory. Render readiness/
  startup must fail closed when the credential is missing or invalid.
- Middleware must reject zero, duplicate, malformed, wrong, and empty headers.
  There must be no empty-secret equality path. Compare only well-formed values
  in constant time and return a non-leaking 401 before body parsing.
- Apply equivalent file validation in the Web server-only reader. Do not expose
  the token to browser bundles, serialized props, HTML, URLs, logs, or errors.
- Dedicated unit and running-Compose tests must exercise real authentication in
  test/dev mode; a general test bypass may remain only for unrelated app-factory
  tests that inject an explicit fake database and cannot support the auth
  boundary, and those tests must not be cited as credential proof.

## 3. Correct composition and catalogue validation

- Validate a child's slot against its parent's catalogue `allowedSlots`; root
  nodes use the explicit root/default contract. Enforce parent `maxChildren`,
  same site/page, cycle/depth/count, deterministic order/tie-break, and no
  unreachable nodes.
- Validate every component against the current trusted catalogue schema:
  exact catalogue and component schema versions, required fields, declared
  prop names, types, enums, numeric bounds, references, object/array depth and
  size. Recursively reject executable keys, unsafe schemes, raw HTML/style/
  handlers, and unsupported values. Do not rely on Puck having produced the
  row.
- Read and require the site's actual component catalogue version rather than
  hardcoding a response version. Add a cross-language contract test that fails
  if backend validation, TypeScript catalogue, Puck adapter, and SSR renderer
  type/version/slot/limit facts drift.
- Add valid nested-slot and invalid parent-slot tests, including
  `Hero.content`, `Columns.col-1..4`, root/default behavior, nested unsafe
  object/array props, missing/extra/wrong-type props, and version mismatch.

## 4. Collection projection integrity

- Return immutable metadata (`id`, `slug`, `status`, type/site as needed)
  separately from editorial values. Editorial JSON must never overwrite
  reserved metadata; adjust the React collection renderer to consume the
  explicit values namespace.
- Enforce `projection_spec`: return only allowlisted requested fields, reject
  unknown/non-string/duplicate/excessive fields, and preserve bounded result
  count/order. Define and test the empty/default projection behavior honestly.
- Keep all view/item lookups same-site and current COW context, verify type IDs,
  apply the supported status/slug/sort subset, and fail closed on unsupported
  filter/sort/pagination/projection syntax. Do not add raw SQL or a general
  query engine.
- Prove malicious values named `id`, `slug`, `status`, `site_id`, or `values`
  cannot spoof metadata and unprojected sensitive fixture values do not appear
  in JSON or HTML.

## 5. Public route, error, and media honesty

- Canonical projection is attempted for non-loopback root-host `/` as well as
  catch-all site routes. Preserve the setup landing page only under its exact
  established loopback condition.
- Allow the routing-context shell only at an exact matched site root that has no
  published page. Any deeper unknown, deleted, draft-only, malformed, reserved,
  or ambiguous page route must return 404, not a 200 shell. Add root and deeper
  route tests through both Web and public NGINX.
- Preserve internal 401/404/503 distinctions through the server-only client so
  missing session, invisible resource, and Render unavailability are not all
  silently collapsed into the same result. Browser-visible responses remain
  non-leaking and preview headers apply to every outcome.
- Replace the nonexistent `/media/{uuid}` output. Active human preview may use
  the exact authenticated Media route bound to projected site/media identity.
  Canonical rendering must emit an image only when a future/public projection
  explicitly marks bytes public; until public media finalization exists, fail
  the component safely or render an honest non-broken placeholder without
  claiming a public URL. Do not implement publication in this round.
- Fix duplicate static IDs or other deterministic accessibility defects when
  rendering repeated trusted components; preserve React escaping and strict
  public/preview CSP.

## 6. Real proof matrix

Extend real PostgreSQL, HTTP, and Playwright evidence to cover:

1. exact public/preview identities and grants; public canonical-only behavior;
   preview DML/base/change/sequence/generic content/Control/Editor/Agent/
   reviewer/setup denials;
2. valid, idle-expired, absolute-expired, revoked, malformed, and wrong-secret
   sessions; inactive account/membership/site; expired/revoked workspace;
3. two sites and at least two workspaces, including one Agent or Import
   workspace visible to its authorized human but never to another site/user;
4. canonical fallback for untouched rows, overlay update, overlay-created page,
   and tombstone/deletion isolation with canonical unchanged;
5. deterministic post-authorization revocation race and pool/context reuse,
   with exact before/after COW/idempotency/audit counts;
6. correct and incorrect parent slots, schema/catalog/props/tree bounds, reserved
   collection fields, projection enforcement, unsupported query, and cross-site
   view/item denial;
7. missing/empty/duplicate/wrong/correct service credentials and invalid file/
   directory/symlink/mode/owner cases in unit and running Compose;
8. root canonical page, exact no-page site root shell, deeper unknown route 404,
   unpublished page 404, Render 503 behavior, and external internal-route denial;
9. real Playwright login followed by navigation to the actual preview route;
   prove overlay title/content/order in DOM, canonical unchanged in a separate
   navigation, private/no-store/noindex headers, strict CSP, no relevant console
   or failed-request errors, and no credential/session token in DOM/URL/storage;
10. repeated catalogue components, safe rich text/links, media placeholder or
    authorized preview route, and absence of executable/raw inline content.

Do not use owner SQL as a substitute for public request authorization. Owner may
seed or inspect exact residue only. Unit/interface/source assertions alone are
insufficient for the runtime claims above.

## Acceptance criteria

- Idle-expired or concurrently revoked authority cannot read preview; complete
  authorization is rechecked under lock in the projection transaction.
- Service authentication has no missing/empty/symlink/mode/owner bypass and is
  validated at startup, not from a per-request environment path.
- Parent-slot and full catalogue prop/version validation are correct and
  cross-language drift fails tests.
- Collection metadata cannot be spoofed and projection fields are enforced.
- Only exact site roots may fall back to the routing shell; unknown deeper
  routes are 404 and non-loopback root canonical pages render.
- No broken/falsely public media URL is emitted; public media finalization
  remains out of scope.
- Real PostgreSQL and Playwright prove canonical/preview/tombstone/fallback,
  multi-site/workspace/session isolation, headers/CSP, and no residue/leak.
- All accepted 071-a and prior Puck/Agent/Media contracts remain green with no
  adjacent lifecycle feature or dependency/trust expansion.

## Verification and workflow

Run and report focused auth/race/projection/tree/catalog/collection/Web/renderer
tests; complete backend unit/repository/integration suites; CI-scope Ruff over
services/backend, repository, packaging, supply-chain, tools, and migrations;
Mypy/build/process checks; complete Node gates; clean Compose and eight-project
browser smoke; the new authenticated preview Playwright path; migration head/
upgrade/downgrade and privilege validation; PostgreSQL 14–18; Markdown/Mermaid;
supply-chain; and every fresh GitHub required check. Record every initial 071-a
failure and every 071-b failure/retry honestly.

Update docs only where session semantics, route fallback, collection shape,
media limitation, service-secret validation, or proof claims become more exact.
Do not edit the immutable 071-a report; this report must explicitly identify
which 071-a claims were too broad and what evidence newly establishes them.

Commit/push the exact strategic 071-b order and active bytes unchanged on the
same branch, then bounded implementation/tests/docs. Publish exactly
`oap/reports/071-b-render-security-isolation-and-proof.md` as one report-only
child with `Report publication commit: SELF`; verify its literal parent and
remote path/head before signaling exact FIFO `OK`. Do not merge.

The report must state result/status, PR/base/branch/all SHAs, exact fixes,
authorization/lock chronology, credential loading state machine, catalogue/
slot/prop and collection schema, route/error/media matrix, real identity/grant/
site/workspace/session/race/residue/browser evidence, files/dependencies/
migrations/docs, every local/CI result/intermediate failure, limitations/non-
goals, and no new PR/merge.
