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
externally reachable in the default topology. Public OpenAPI and documentation
URLs remain disabled.

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

## Internal Render resolution API

Render exposes exactly one non-health route on its internal listener:
`POST /internal/render/v1/site-context`. Its extra-forbid body contains only
`authority` and `path`. The response contains the resolved active site UUID,
key, canonical revision, default locale, and matched hostname/path prefix; it
contains no lifecycle, user, workspace, capability, preview, or publication
authority. Invalid, reserved, unknown, and archived inputs share 404; ambiguity
is 409 and persistence failure is 503. All responses are private/no-store,
noindex, and request-ID correlated. No edge or public route targets it.

The database-free Web server is its only routing-shell client. It calls the
fixed `http://render-api:8000/internal/render/v1/site-context` URL with a short
timeout, `no-store`, no cookies or authorization, and only the actual request
Host/path. The browser never receives the internal URL. Successful resolution
renders routing facts only; failure returns 404, while Render unavailability
makes Web readiness fail with 503. NGINX and Apache reject direct `/internal/`
requests.
