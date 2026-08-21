# Site and trusted resolution foundation

Objective 011-a implements the non-COW installation catalog for sites and
their request-domain mappings. The data lives in `control.site` and
`control.site_domain`; it is installation control data, not editorial content
and not an Agent-State workspace.

Human authority is site-scoped through active versioned memberships; one user
may hold different roles, ceilings, and overrides on different sites. Global
account status alone grants no site authority. See [Human site
authorization](AUTHORIZATION.md).

## Authority boundary

Only the owner role has direct relation access. The Control role can execute a
small fixed function surface for site lifecycle, domain mappings, and
resolution. The canonical Render credential (`slaif_public_reader`) can execute
only the two active hostname/path and local-key resolver functions; its
`SiteResolver` exposes only `resolve(authority, request_path)`. Other product
roles have neither relation nor site-function authority.
The Control application exposes the same boundary through the authenticated
Platform Administrator API documented in [API](API.md). Site membership
lifecycle is separately governed by global administrator or exact site-manager
authority. No anonymous site endpoint or site-management UI exists.

Site UUIDs, mapping UUIDs, revisions, timestamps, and lifecycle state are
server/database-owned. Request bodies cannot select routing identity. A
successful lookup creates an immutable `SiteContext` through a private
database-result factory; callers cannot construct one from untrusted values.

## Site lifecycle and quota

A site has a unique lowercase ASCII key, display name, active or archived
status, normalized default locale, catalog version, and non-negative canonical
and content-model revisions. Create, update, list, get, and archive operations
are bounded Control functions. There is no online delete operation and an
archived site cannot resolve.
Profile and domain mutations lock and re-check the site as active in their own
transaction, so a context retained before archive cannot mutate afterward.
Archive is idempotent and deletes neither site nor mapping rows.

The installation-bound `control.site_policy` singleton contains `max_sites`,
defaulting to 100 and bounded from 1 through 1000. Creation locks that row before counting sites, so
concurrent requests cannot exceed the quota. The quota is trusted
installation policy rather than request or environment input.

## Normalization

- Site keys are lowercase ASCII slugs, at most 63 characters.
- Hostnames are lowercased IDNA ASCII with one terminal dot removed. Schemes,
  user information, paths, stored ports, IP literals, malformed labels,
  wildcard labels, and overlong names are rejected. A request authority may
  contain a syntactically valid port, which is removed before matching.
- Path prefixes are canonical lowercase absolute paths without percent
  escapes, backslashes, dot segments, repeated or trailing slashes, query, or
  fragment. Root is valid; reserved application namespaces are rejected.
- Locale tags use a bounded canonical BCP 47-like representation.

Reserved path namespaces include API, administration, authentication, health,
internal, MCP, media, preview, setup, Next.js assets, and static assets. This
prevents a site mapping from shadowing trusted application routes.

## Resolution

Normal resolution accepts a trusted request authority and path, matches an
exact normalized hostname, and selects the unique longest matching path
prefix. Equal-best ambiguity fails closed. Only active sites are returned.

For local development, `localhost` can use `/s/<site-key>` and derives the key
from that trusted path form. It does not accept a caller-provided site UUID.
Reference Compose explicitly seeds the active `demo` site only while setup is
incomplete and the catalog is otherwise empty, so `/s/demo/` needs no domain
row. After setup, administrators may change or archive it and bootstrap does
not restore it. Web sends only the actual Host and path to its fixed internal
Render endpoint. A second API-created site can resolve through `/s/<key>/` or
an exact custom Host/path-prefix mapping; prefix matching preserves segment
boundaries. Wildcards, forwarded-header trust, DNS verification, redirects,
and production edge routing remain deferred.

## Deferred work

Site-management and membership UI, invitations/custom roles, workspaces,
content models, actual site content, editor/Puck, agent capabilities,
review/publication, DNS
automation, and deletion are not implemented. The accessible shell proves
routing context only; it is not a publication surface. This API does not make the application
production-ready or hostile-tenant-safe. Multi-site support remains trusted
institutional tenancy and does not claim hostile public-SaaS isolation.
