# Control HTTP API

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
limiting, durable authentication audit, OIDC, MFA,
and membership management remain absent.

## Platform Administrator site API

Every route below requires a current server-side human session whose active
user has a current `platform_administrator` assignment. Safe `GET` requests do
not use CSRF. Every state-changing request additionally requires the bound CSRF
cookie and exactly one matching `X-CSRF-Token` header.

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
