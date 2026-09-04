# Control HTTP API

## Current-human administration reads

`GET /api/control/v1/me/sites` requires a valid human session and returns a
deterministically ordered, server-filtered site summary list. Platform
Administrators receive all sites, including archived status, with an explicit
global flag and null membership fields. Ordinary active users receive only
active sites with active memberships and their role, membership version,
ceilings, and safe site summary fields.

`GET /api/control/v1/sites/{site_id}/my-authority` returns only the current
human's authority for the path-selected site. A global administrator receives
no synthetic membership and an empty permission list; an ordinary member
receives effective permission keys. Neither route accepts user, role,
permission, Host, forwarded, query-authority, or mutation input. Stable statuses
are `401`, constant `404`, and `503`; responses are private/no-store/noindex and
contain no profile, credential, token, cookie, digest, or database locator.

The Control service exposes a bounded local-authentication boundary under
`/api/control/v1`. Existing NGINX routing makes these backend endpoints
externally reachable in the default topology. Interactive Swagger/ReDoc and
generic FastAPI documentation URLs remain disabled; the versioned Agent
contract is deliberately exposed at the public path documented below.

- `GET /setup/status` returns only `initialized` and `setup_available`.
- `POST /setup` consumes the one-time setup token and creates the first local administrator.
- `POST /login` authenticates a local administrator.
- `GET /session` returns bounded identity, recent-auth, and expiry information.
- `POST /logout` requires the session cookie, CSRF cookie, and matching `X-CSRF-Token` header.

Successful setup and login set bounded-lifetime session and CSRF cookies. Production uses
`__Host-slaif_session` and `__Host-slaif_csrf` with `Secure`, `Path=/`, no `Domain`, and
`SameSite=Lax`; development uses the equivalent non-secure names. Credentials, setup tokens,
and cookie values are never returned in response bodies or errors.

The Next.js setup/login/admin UI and clean Compose authentication journey use
these same-origin routes. Six self-hosted Playwright browser/device projects
prove setup, login, authenticated admin, and logout through NGINX. Rate
limiting, durable authentication audit, OIDC, and MFA remain absent.

## Role, permission, and membership API

The catalog routes require one current human session and no CSRF. Membership
reads require a current Platform Administrator or an active site member holding
both `membership:manage` and `role:manage`. Mutations additionally require the
bound CSRF cookie/header proof and reassert authority under database locks.

| Route | Success | Request contract |
| --- | --- | --- |
| `GET /roles` | 200 | none; immutable seven-role defaults and ceilings |
| `GET /permissions` | 200 | none; immutable categories, assignability, delegation level, and default roles |
| `GET /sites/{site_id}/memberships` | 200 | none |
| `GET /sites/{site_id}/memberships/{user_id}` | 200 | none |
| `POST /sites/{site_id}/memberships` | 201 | target user, role, explicit ceiling, complete disjoint allow/deny sets |
| `PATCH /sites/{site_id}/memberships/{user_id}` | 200 | positive expected version, role, ceiling, `ACTIVE` or `INACTIVE`, complete replacement overrides |
| `DELETE /sites/{site_id}/memberships/{user_id}?expected_version=N` | 200 | positive expected version; semantic deactivation, never hard delete |

POST cannot set site, actor, status, expected/result version, effective
permissions, administrator fact, or timestamps. PATCH takes the target only
from the path and cannot set those trusted/result fields. Responses contain
only site/user UUIDs, role, explicit/effective ceilings, lifecycle/version,
sorted overrides/effective permissions, the target's current global
administrator fact, and safe timestamps. They contain no identity profile,
session, CSRF, credential, digest, SQL, or locator.

Session failures are 401; CSRF, self-change, inactive/lower/beyond-authority,
and nonassignable override denials are 403; invisible site/user/membership and
cross-site substitution are 404; duplicate creation and stale/concurrent
versions are 409; malformed/extra/unknown values are 422; persistence/pool/
timeout failures are 503. Successes and errors are private/no-store/noindex and
request-ID correlated. Publication remains an explicit permission independent
of role ceiling or edit authority.

The responsive admin client validates catalog and membership responses, sorts
memberships by exact user UUID, and sends only these documented request shapes
with same-origin credentials and the existing CSRF proof. A stale-version 409
refreshes the current server record. Client-hidden self controls and
permission-driven read-only states are usability measures, not authorization.
The client accepts only an existing user UUID; it does not create identities,
invitations, login credentials, or custom roles.

## Route-policy registry

Every actual Control and Editor handler has one immutable declaration keyed by
process, method, and normalized path template. It records read/mutation class,
session and CSRF requirements, global/site authority kind, policy kind, and
exact permissions. Health has the only shared system exemption. Tests compare
the actual FastAPI inventory against the registry and fail on missing,
duplicate, stale, method/path-mismatched, unknown-permission, or request-shape
declarations. HEAD and OPTIONS are not registered handler methods and retain
their deterministic framework 405 behavior. The registry audits enforcement;
handlers and database policy remain authoritative.

## Human Editor API and Puck composition editor

Editor routes use the same human session cookie and CSRF proof as Control; they
never accept Agent capabilities. The server rechecks site membership and the
required permission on every request, resolves an ACTIVE, unexpired HUMAN
workspace owned by that human and site, and opens a bounded COW session on the
separate Editor runtime pool. Every state-changing route also requires a
bounded `Idempotency-Key`; replay is stable, digest mismatch is rejected, and
the mutation plus HUMAN audit record commit atomically. Responses and errors
are private, no-store, noindex, and request-ID correlated.

| Route | Success | Request contract |
| --- | --- | --- |
| `POST /api/editor/v1/sites/{site_id}/pages/` | 201 | bounded page model |
| `GET /api/editor/v1/sites/{site_id}/pages/{page_id}` | 200 | none |
| `POST /api/editor/v1/sites/{site_id}/pages/{page_id}/composition/components` | 201 | trusted catalog type, bounded props, parent/slot/order |
| `GET /api/editor/v1/sites/{site_id}/pages/{page_id}/composition/` | 200 | none |
| `PATCH /api/editor/v1/sites/{site_id}/pages/{page_id}/composition/components/{node_id}` | 200 | bounded props and optional slot/order |
| `POST /api/editor/v1/sites/{site_id}/pages/{page_id}/composition/components/{node_id}/move` | 200 | same-page parent, slot/order |
| `DELETE /api/editor/v1/sites/{site_id}/pages/{page_id}/composition/components/{node_id}` | 204 | none |

The admin route `/admin/sites/{siteId}/pages/{pageId}/edit` loads this normalized
composition through the Editor API, adapts it to the pinned
`@measured/puck@0.20.2` catalog, and saves a normalized round trip. Component
IDs, schema versions, parent IDs, slots, order keys, and trusted props remain
outside Puck metadata and are reconciled against server records. Unknown
component types, executable prop names, arbitrary code, CSS, packages, and SQL
are rejected. A selected component can be moved among its current siblings
with the accessible `Move up`/`Move down` controls; those controls dispatch
Puck's same-zone reorder action with history recording and never replace the
controlled data directly. Selection follows the moved component at its
destination, and the move participates in Puck's visible undo/redo history
without creating another semantic editor operation. A later deliberate human
selection always takes precedence and releases that temporary continuity.
This order does not implement publication, preview authority,
workspace-management UI, freeze/review/promotion, responsive preview, or new
catalog/storage types.

## Private human Media API

The edge-routed Media service owns immutable bytes and human workspace metadata
references. The former metadata-only Editor `POST .../media/register` route is
removed; no route claims an upload before validated bytes exist.

| Public route | Success | Contract |
| --- | --- | --- |
| `POST /media/v1/sites/{site_id}/assets` | 201 | exactly one filename-bearing multipart part named `file`, bounded `alt_text`, optional bounded JSON `metadata`, CSRF-bound human session, `media:upload`, and `Idempotency-Key` |
| `GET /media/v1/sites/{site_id}/assets/{media_id}/content` | 200 | authenticated human session, `media:read`, workspace-aware metadata lookup, immutable byte stream |

Uploads stream into private staging, SHA-256 hash and signature-sniff against
the declared MIME, then publish under a digest-only key before the metadata
reference is recorded in the server-selected HUMAN workspace via COW and the
exact media idempotency/HUMAN-audit envelope. A database failure after object
publication may leave an unreferenced private object for later Media GC; it is
not public or described as transactionally rolled back.

Only PNG and JPEG are enabled in this slice. SVG, empty/unknown/spoofed
content, traversal names, oversized/truncated bodies, foreign sites, and
missing/corrupt/symlink objects fail closed. Missing/invalid idempotency is
400, authentication is 401, CSRF/permission failures are non-leaking 403/404,
malformed content is 422, edge/application size failures are 413, and only
storage/database failures are 503. Byte responses are private,
no-store, `nosniff`, digest ETagged, exact-length, and never expose a path or
anonymous URL. Metadata reference deletion remains a workspace tombstone and
never unlinks bytes. Agent upload, public media, thumbnails, GC, transcoding,
object storage, and publication are later work.

Puck 0.20.2 requires runtime inline styling for parts of its editor UI. The
authenticated editor surface therefore receives the minimum required
`style-src-attr 'unsafe-inline'` and `style-src-elem 'self' 'unsafe-inline'`
exceptions. `script-src` remains self-plus-request-nonce, and public renderer,
Control/Agent API, and unrelated admin surfaces retain the strict self-only
style policy. No user-controlled raw CSS/style payload is accepted.

## Capability-bound Agent semantic API

### Deterministic public Agent contract

`GET /api/agent/v1/openapi.json` is unauthenticated and returns the exact
committed bytes of [`contracts/openapi/agent-v1.json`](../contracts/openapi/agent-v1.json).
It grants no operation authority. The document is OpenAPI 3.1, contains only
the versioned Agent paths, uses the `AgentCapability` bearer scheme with
empty OpenAPI bearer requirement values, and publishes exact operation scopes
in `x-slaif-required-scopes`. Mutations require a bounded `Idempotency-Key`
header in the contract. Conditional mutation scope requirements are published
in `x-slaif-conditional-scopes` with their exact triggering request fields.
Regenerate and check it with the commands in
[`contracts/README.md`](../contracts/README.md).

The Agent API authenticates a bearer capability and derives the site and
workspace exclusively from that trusted capability. Semantic GETs and bounded
mutations use different server paths: reads enter one request-scoped COW
session and call only Agent-owned read wrappers; mutations additionally reserve
and complete durable idempotency/audit state.

The capability-bound read surface is:

| Route | Success | Required scope |
| --- | --- | --- |
| `GET /api/agent/v1/content-model/types` | 200 | `content-model:read` |
| `GET /api/agent/v1/content-model/primitives` | 200 | `validation:read` |
| `GET /api/agent/v1/content-model/types/{type_id}` | 200 | `content-model:read` |
| `GET /api/agent/v1/content-model/types/{type_id}/fields` | 200 | `content-model:read` |
| `GET /api/agent/v1/content-items/types/{type_id}` | 200 | `content-item:read` |
| `GET /api/agent/v1/pages` (trailing slash alias) | 200 | `page:read` |
| `GET /api/agent/v1/pages/{page_id}` | 200 | `page:read` |
| `GET /api/agent/v1/pages/{page_id}/components` | 200 | `composition:read` |
| `GET /api/agent/v1/media/` | 200 | `media:read` |

Read results use the capability's workspace overlay: workspace-created or
modified rows shadow canonical rows, unchanged canonical rows remain fallback,
and COW tombstones remain absent. Site, parent, and resource IDs are checked
against the trusted workspace context; foreign-site/workspace resources return
the stable not-found envelope. Reads create no idempotency row, mutation audit
row, or pending COW operation, and the foundation context is cleared before the
Agent pool connection is reused.

Page records expose normalized slug/parent metadata, an optional `route_template`,
the server-derived `effective_route`, and `deleted_at` on a deleted record.
Routes are derived from an already-enabled site locale and the ancestor
hierarchy; `route_template` is either absent or the terminal literal `{slug}`.
Page operations never create or configure locales. Page deletes are workspace
COW tombstones; restore requires the tombstone's exact row version and restores
the same page ID and prior hierarchy. Tombstoned pages are absent from Agent
reads and active Render, while canonical state remains unchanged until review
and promotion.

The bounded mutation surface is:

| Route | Success | Request body |
| --- | --- | --- |
| `POST /api/agent/v1/content-model/types` | 201 | `CreateContentTypeRequest` |
| `POST /api/agent/v1/content-model/types/{type_id}/fields` | 201 | `CreateFieldDefinitionRequest` |
| `PATCH /api/agent/v1/content-model/types/{type_id}` | 200 | `UpdateContentTypeRequest` |
| `PATCH /api/agent/v1/content-model/types/{type_id}/fields/{field_id}` | 200 | `UpdateFieldDefinitionRequest` |
| `DELETE /api/agent/v1/content-model/types/{type_id}` | 200 | `DeleteDefinitionRequest` |
| `DELETE /api/agent/v1/content-model/types/{type_id}/fields/{field_id}` | 200 | `DeleteDefinitionRequest` |
| `POST /api/agent/v1/content-items/types/{type_id}` | 201 | `CreateContentItemRequest`; its `type_id` must match the path |
| `PATCH /api/agent/v1/content-items/{item_id}` | 200 | `AgentUpdateContentItemRequest` |
| `DELETE /api/agent/v1/content-items/{item_id}` | 200 | `DeleteContentItemRequest` |
| `POST /api/agent/v1/content-items/{item_id}/translations` | 201 | `CreateTranslationRequest` |
| `PATCH /api/agent/v1/content-items/{item_id}/translations/{translation_id}` | 200 | `UpdateTranslationRequest` |
| `DELETE /api/agent/v1/content-items/{item_id}/translations/{translation_id}` | 200 | `DeleteTranslationRequest` |
| `POST /api/agent/v1/content-items/{item_id}/relations` | 201 | `CreateRelationRequest` |
| `PATCH /api/agent/v1/content-items/{item_id}/relations/{relation_id}` | 200 | `UpdateRelationRequest` |
| `DELETE /api/agent/v1/content-items/{item_id}/relations/{relation_id}` | 200 | `AgentDeleteRequest` |
| `POST /api/agent/v1/collection-views/types/{type_id}` | 201 | `CreateCollectionViewRequest` |
| `PATCH /api/agent/v1/collection-views/{view_id}` | 200 | `UpdateCollectionViewRequest` |
| `DELETE /api/agent/v1/collection-views/{view_id}` | 200 | `AgentDeleteRequest` |
| `POST /api/agent/v1/pages` (trailing slash alias) | 201 | `CreatePageRequest` |
| `PATCH /api/agent/v1/pages/{page_id}` | 200 | `UpdatePageRequest` |
| `DELETE /api/agent/v1/pages/{page_id}` | 200 | `AgentDeleteRequest` |
| `POST /api/agent/v1/pages/{page_id}:move` | 200 | `MovePageRequest` (parent-only hierarchy move) |
| `POST /api/agent/v1/pages/{page_id}:restore` | 200 | `RestorePageRequest` with the exact tombstone row version |
| `POST /api/agent/v1/pages/{page_id}/components` | 201 | `CreateCompositionNodeRequest` |

Every mutation requires an `Idempotency-Key` containing 1–128 bounded ASCII
key characters. The response is `{ "record": <semantic record>,
"operation_id": <UUID> }`. A replay with the same capability, key, route,
and request digest returns the stored response; reusing a key with another
digest returns `409 IDEMPOTENCY_MISMATCH`. Missing and malformed keys return
`IDEMPOTENCY_KEY_REQUIRED` and `IDEMPOTENCY_KEY_INVALID` respectively.

The trusted server selects one workspace/session UUID and operation UUID,
executes the semantic call inside `asyncpg_cow_session`, and records the
idempotency result and audit event in the same transaction. The Agent role has
no direct control-table DML, content base/change-table access, reviewer
authority, SQL/DDL route, or lifecycle route. Created records are visible in
the workspace overlay and remain absent from canonical content until a later
human-only lifecycle order; this round does not implement freeze, accept,
discard, review, or publication routes.

Definition deletion is dependency-safe. Type deletion rejects visible fields,
items, collection views, and any surviving item translations or relations;
field deletion rejects exact nonlocalized/localized value keys, normalized
relations, and recursive view filter, sort, or projection references. These
denials are stable `422` responses with `TYPE_DEPENDENCIES` or
`FIELD_DEPENDENCIES`, consume no quota, and leave no idempotency, audit, or COW
residue. All model/content dependency writes share one transaction-scoped
workspace lock, so a concurrent creator and deletion has one committed winner
and a coherent loser result.

### Capability-bound browser preview runs

The public Agent surface now wires the shared `browser-preview/v1` contract to
the durable browser-run functions. Every route requires the same bearer
capability and `preview:inspect`; create also requires `Idempotency-Key`.

| Route | Success | Contract |
| --- | --- | --- |
| `POST /api/agent/v1/preview-runs` | 202 | exactly `version`, normalized `route`, one approved target, and unique bounded evidence |
| `GET /api/agent/v1/preview-runs/{run_id}` | 200 | current capability-bound status or terminal result |
| `GET /api/agent/v1/preview-runs/{run_id}/artifacts` | 200 | retained private metadata only |
| `GET /api/agent/v1/preview-runs/{run_id}/artifacts/{artifact_id}` | 200 | retained PRIVATE bytes with exact MIME, length, digest ETag, and private/no-store/noindex headers; invisible bindings are 404 and worker/storage failures are 503 |

Create derives all site/workspace/delegator/run/operation/quota/digest facts on
the server. `STARTED` and same-digest `REPLAY` return the same durable QUEUED
body without double reservation. Mismatch is 409, enforced quota 429, missing
scope 403, current authentication failure 401, malformed key 400, schema/route
validation 422, invisible binding 404, and database failure 503. Responses are
private/no-store and contain no capability, request digest, worker URL, lease,
SQL, role, or preview credential. The former unauthenticated
`/internal/browser/v1` Agent routes were removed.

The shared signer issues a short-lived opaque `sbp1` HMAC-SHA256 credential for
the durable dispatcher from exact durable run facts. Public create never mints
or returns it. A browser navigation may carry it only in
`X-SLAIF-Browser-Preview`; Web forwards it server-side only in
`X-SLAIF-Browser-Run-Token`. Render verifies signature/lifetime and all
bindings, then migration 036 consumes the nonce and rechecks the active
capability/workspace/site/QUEUED-or-RUNNING run under the shared workspace lock
before COW projection. Human preview remains cookie-bound and mutually
exclusive with browser-token mode.

The internal browser worker now implements three non-edge POST routes:
`/internal/browser/v1/attempts`, `/internal/browser/v1/attempts/inspect`, and
`/internal/browser/v1/artifacts/retrieve`. They require the isolated
`X-SLAIF-Browser-Worker-Token` service credential before body parsing and use
extra-forbid `browser-worker/v1` contracts. Submit returns a signed typed
result; retrieval requires every exact artifact binding and returns private
bytes only to the trusted Agent-side client. The durable Agent dispatcher binds
the worker request UUID and atomically completes the run. The capability-
authenticated public artifact route proxies only retained PRIVATE bindings with
bounded bytes, allowlisted MIME, exact length, digest ETag, `nosniff`, and
private/no-store/noindex headers. Missing or foreign bindings are 404; worker,
storage, or digest failures are 503. Range, redirects, public URLs, source
browsing, GC, review integration, and publication remain absent.

## Site governance API

Every route requires a current server-side human session. Site creation and
archive require Platform Administrator authority; archive also requires recent
authentication. Detail/domain reads require `site:read`, profile updates
require `site-policy:manage`, and domain mutations require
`site-domain:manage`, unless the caller is a Platform Administrator. Safe GETs
do not use CSRF; every mutation requires the bound CSRF cookie and one matching
`X-CSRF-Token` header.

| Route | Success | Request body |
| --- | --- | --- |
| `GET /sites` | 200 | none |
| `POST /sites` | 201 | `site_key`, `display_name`, `default_locale` |
| `GET /sites/{site_id}` | 200 | none |
| `PATCH /sites/{site_id}` | 200 | `display_name`, `default_locale` |
| `POST /sites/{site_id}/archive` | 200 | none |
| `GET /sites/{site_id}/domains` | 200 | none |
| `POST /sites/{site_id}/domains` | 201 | `hostname`, `path_prefix`, `is_primary` |
| `PUT /sites/{site_id}/domains/{domain_id}` | 200 | `hostname`, `path_prefix`, `is_primary` |
| `DELETE /sites/{site_id}/domains/{domain_id}` | 204 | none |

Bodies are frozen extra-forbid models and cannot select IDs, lifecycle state,
revisions, catalog version, timestamps, routing Host/path, or authorization
context. Server code parses the path UUID, resolves it through the semantic
service, and creates the active `SiteContext`; handlers never construct one.
Responses contain only the safe site/domain record fields documented in
[Sites](SITES.md).

Authentication failures are 401; authorization and CSRF failures 403; absent
or cross-site resources 404; duplicates, quota, primary-domain rules, and
archived state 409; validation 422; persistence unavailability 503. Every
success and error is `private, no-store`, `noindex`, and carries one request ID.
Errors use the stable envelope and reveal no credential or cross-site detail.

## Human Agent session Control API

Authenticated Site Owners use these site-bound routes with the normal session
cookie and CSRF proof. Workspace creation applies the requested preset/scopes,
source-origin and quota bounds through owner-defined Control functions. A
capability response contains its opaque bearer token exactly once; later reads
return metadata only, and revocation immediately invalidates Agent requests.

| Route | Success | Request |
| --- | --- | --- |
| `POST /sites/{site_id}/workspaces/` | 201 | bounded title, preset, TTL, scopes, origins, constraints, quotas |
| `GET /sites/{site_id}/workspaces/{workspace_id}` | 200 | metadata only |
| `POST /sites/{site_id}/workspaces/{workspace_id}/capabilities/` | 201 | no body; one-time token response |
| `GET /sites/{site_id}/workspaces/{workspace_id}/capabilities/` | 200 | metadata only, never secrets |
| `POST /sites/{site_id}/workspaces/{workspace_id}/capabilities/{capability_id}/revoke` | 200 | no body |

The Agent API authenticates the same site/workspace capability and rechecks
active workspace, site, delegator account, expiry, and revocation state. It has
no Control-table or reviewer authority. Freeze, review, promotion, and discard
are intentionally not exposed by this surface.

Authentication returns the immutable normalized source origins, resource
constraints, and request/mutation/delete/upload budgets issued with the
workspace. Every authenticated request consumes one request unit atomically;
the five existing Agent create routes consume one mutation unit only after a
new idempotency reservation, so retries do not double-charge. Exhausted
budgets return `429` without exposing secrets. Human Agent create/issue/revoke
actions append secret-free rows to the append-only audit stream.

## Internal Render projection API

Render exposes typed, private projection routes on its internal listener:

| Route | Contract |
| --- | --- |
| `POST /internal/render/v1/site-context` | bounded authority/path routing context |
| `POST /internal/render/v1/page` | published canonical page projection |
| `POST /internal/render/v1/preview` | authorized HUMAN workspace overlay projection |

Page responses contain site/revision, normalized route/locale, page metadata,
a bounded normalized composition tree, catalog/schema versions,
theme/navigation data, and same-site bounded collection bindings. Collection
editorial fields are returned only below each item's explicit `values` object;
reserved identity metadata cannot be overwritten by content values. Render
returns JSON only; Web owns HTML and uses the trusted React catalog renderer.
Unknown, archived, unpublished, wrong-site, ambiguous, malformed, or
cross-workspace resources fail closed without partial data.

The preview route accepts an untrusted workspace UUID only after the internal
Web request is authenticated with the file-backed service credential and the
human session proof is authorized by the fixed `preview:inspect` database
function. HUMAN, AGENT, and IMPORT workspaces are eligible only for their
authorized human creator/delegator; SYSTEM workspaces are denied. The
authorization applies the normal absolute-expiry, idle-expiry, revocation,
account/site/workspace, membership, touch, and recent-auth policy. A preview
touch advances only `last_seen_at`; it never renews or changes `recent_auth_at`.
Canonical and preview use separate read-only pools. Preview reasserts the complete
mutable authority on the COW connection under the workspace shared advisory
lock before reading content, then leaves no mutation, idempotency, or audit
residue. Every internal response is private/no-store, noindex, and
request-ID correlated. NGINX and Apache reject direct `/internal/` requests.

Web calls the fixed internal URLs server-side with a short timeout. The
service credential and human session proof never enter browser JavaScript,
HTML, query strings, storage, logs, or artifacts. Public catch-all pages and
`/preview/{workspace_id}/{site_path...}` render the same trusted React
component implementation. Only an exact matched site root without a page may
use the routing shell; deeper unknown, unpublished, or deleted routes are 404.
Preview responses are additionally private, no-store, and `noindex`. Public
rendering does not emit a media URL until public media finalization exists;
trusted image nodes use an honest non-broken placeholder meanwhile.
