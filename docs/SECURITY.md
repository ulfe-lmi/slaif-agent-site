# Render resolution security boundary

The admin shell stores no session token, CSRF token, user UUID, permission list,
or selected site in local/session storage. Requests are same-origin,
credential-bound, no-store reads. Missing sessions redirect to login; direct
foreign/unknown site URLs render one constant state without caller-data
fallback. Tailwind is local build-time CSS and the Radix primitive is
self-hosted; there are no remote fonts, icons, scripts, telemetry, or origins.

Human authorization rechecks active user, active site, active membership,
exact site association, current membership version, and permission inside the
database boundary. Cross-site substitution, self-escalation, stale versions,
nonassignable permissions, and beyond-actor ceilings fail closed. Publication
is independent and never follows from editing or delegation level. See [Human
site authorization](AUTHORIZATION.md).

Control membership reads authenticate the strict human cookie once, resolve an
active site through trusted persistence, and require global administrator or
both membership-management permissions. POST, PATCH, and semantic DELETE use
the atomic session-plus-CSRF helper and then repeat actor authorization under
the mutation function's canonical row locks. Client Host, forwarded headers,
body IDs, roles, and versions never establish site authority. All catalog,
membership, validation, and error responses are private/no-store/noindex and
carry one request ID without foreign-site or credential detail.

Clean Compose E2E uses two fixed OIDC fixture identities with a reserved
non-routable issuer. The smoke harness is their only insertion point; neither
bootstrap, migrations, Compose configuration, nor product source creates them.
They have no local credentials, administrator assignment, or enabled OIDC login
and are destroyed with disposable volumes. Their UUIDs are non-secret metadata
passed through the existing mode-0600 E2E channel; session, CSRF, setup-token,
password, and database locators remain excluded from arguments and artifacts.

The internal Render API owns one `slaif_public_login` connection pool with the
sole `slaif_public_reader` membership. Pool initialization verifies database,
login/current-user, and exact membership before readiness succeeds. Locator and
driver details are never returned or logged.

The role has no direct `control` relation access and no site management,
administrator, session, setup, migration, or publication function. It can call
only the two active site resolver functions. Resolution derives site identity
from normalized authority/path input and returns routing facts, not
authorization. Caller-provided identity, workspace, preview, membership, and
capability headers have no meaning. Web calls its single fixed URL with only
the actual request Host and path, no cookies, authorization, forwarded
identity, or caller-selected base URL. NGINX and Apache explicitly reject
`/internal/`; Control, Agent, Editor, and MCP expose no route to it.

Compose gives Render one isolated, read-only locator file containing only the
public-reader DSN. It does not mount the master or Control secret volume. Web
and the edge have no database locator, and readiness fails closed through
Render→Web→NGINX if the Render locator is missing or invalid.
