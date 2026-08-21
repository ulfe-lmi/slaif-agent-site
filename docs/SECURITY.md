# Render resolution security boundary

Human authorization rechecks active user, active site, active membership,
exact site association, current membership version, and permission inside the
database boundary. Cross-site substitution, self-escalation, stale versions,
nonassignable permissions, and beyond-actor ceilings fail closed. Publication
is independent and never follows from editing or delegation level. See [Human
site authorization](AUTHORIZATION.md).

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
