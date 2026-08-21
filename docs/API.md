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
site-management HTTP routes and membership management also remain absent.

## Internal site service boundary

The Control process now has a typed, database-backed semantic service for
creating, reading, listing, updating, and archiving sites; managing domain
mappings; and resolving trusted request host/path inputs. This is an internal
application boundary only: objective 011-a adds no public HTTP endpoint and no
request may supply a site UUID as routing authority. Trusted server code
derives an immutable `SiteContext` after successful resolution. See
[Sites](SITES.md) for normalization and resolution rules.
