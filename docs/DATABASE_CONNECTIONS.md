# Online database connection boundary

Control, Editor, and Agent API each own separate online PostgreSQL connection
boundaries. Control reports bootstrap/database readiness and owns the initial
local-administrator operation. Editor uses a separate runtime pool for
human-authorized content COW calls and a separate Control pool for session/site
authorization; each Editor request resolves a real HUMAN workspace and uses
Editor-only workspace, idempotency, and audit functions. Agent owns one typed
lifespan pool and uses it only for capability-authenticated semantic COW reads,
mutations, and their narrow idempotency/audit functions; reads use one
request-scoped COW connection without durable mutation state. It does not
expose a SQL endpoint or lifecycle, review, promotion, or publication authority.

## Authority map

```text
secrets-init (one-shot writer)
  |
  | copies only service-control-dsn
  v
control-secret named volume
  |
  | read-only /run/slaif-control/control-dsn
  v
control-api as UID 10001
  |
  | authenticates as slaif_control_login
  | exact sole membership: slaif_control
  v
three narrow control functions
  |
  | SECURITY DEFINER, owner slaif_owner
  | fixed search_path=pg_catalog
  | readiness is read-only; setup pair owns one atomic mutation
  v
bounded readiness or atomic initial identity result
```

Agent follows a separate credential path. `secrets-init` copies only
`service-agent-dsn` into the isolated `agent-secret` volume, mounted read-only
at `/run/slaif-agent/agent-dsn` only by Agent API. Agent validates the fixed
`slaif_agent_login`/`slaif_agent_runtime` identity on every pooled connection
and exposes only its typed `cow_pool()` boundary to the semantic read and
mutation executors. The read executor binds all wrapper calls to one
request-scoped `asyncpg_cow_session` and never falls back to the ordinary
application content service.
Control and Agent never share a locator, pool, native connection, or
credential volume.

Editor follows two bounded credential paths. `secrets-init` copies only
`service-editor-dsn` into the isolated `editor-secret` volume, mounted
read-only at `/run/slaif-editor/editor-dsn` by Editor API. Editor validates the
fixed `slaif_editor_login`/`slaif_editor_runtime` identity for its content pool.
The same process separately mounts `control-secret` for Control's human session
and site authorization pool; it never uses the Control pool for content
functions. Editor and Agent never share a locator, pool, native connection, or
credential volume.

Media follows a third isolated credential path. `secrets-init` copies only
`service-media-dsn` into `media-secret`, mounted read-only at
`/run/slaif-media/media-dsn` by Media service. The fixed
`slaif_media_login`/`slaif_media` pool validates database identity on every
connection and performs human session/site authorization, COW metadata
registration, and authorized metadata lookup only through named owner-defined
functions. Media bytes are held in the private `media-data` volume, initialized
by the networkless secrets process for UID 10001 and shared only with Media GC;
NGINX and Apache never mount or alias it.

Render follows two isolated read paths. `secrets-init` copies only the fixed
public-reader locator into `render-secret` and the fixed preview-reader locator
into `render-preview-secret`. Render validates both identities on pooled
connections: canonical requests use `slaif_public_login`/`slaif_public_reader`
and preview requests use `slaif_preview_login`/`slaif_preview_reader`. Preview
also receives exact `EXECUTE` on the owner-defined human-session/workspace
authorization function and opens one COW session only after that function
returns trusted workspace/site values. Web receives no database locator; it
and Render share only a separate high-entropy file-backed Render-call
credential mounted read-only from `render-auth-secret`.

The master `local-secrets` volume still contains PostgreSQL administrator,
bootstrap owner, login-password, and future-service files. Control does not
mount that volume. Its isolated directory is mode `0700`, owned by
`10001:10001`; `control-dsn` is mode `0400`, owned by UID 10001. Only the
networkless initializer writes the isolated volume. Control mounts it
read-only. An unrelated UID, every other long-running service, Web, MCP,
browser worker, and NGINX cannot read it. The Docker socket and host paths are
not mounted.

Bootstrap provisions and authenticates the same fixed login from the master
secret manifest without needing the isolated runtime mount. The generated
password remains cryptographic and unchanged during the copy. Repeated
initialization requires the isolated value to match and fails closed rather
than silently replacing a mismatch. No environment variable contains a DSN or
password.

## Control-only typed settings

`ControlDatabaseSettings` is frozen, uses only `SLAIF_CONTROL_`, and lives in
the Control package. Shared `ServiceSettings` and other process packages do not
load it. Development and production require one absolute mounted file;
explicit test mode alone permits a local or `.test` fake direct locator.

The model validates database/login/role identity, min/max pool size,
connection/acquire/command/shutdown timeouts, inactive lifetime, statement,
lock, idle-transaction timeouts, and a bounded application name. Outside tests
the login and role are fixed to `slaif_control_login` and `slaif_control`.
Secret values use `SecretStr`; locator resolution errors are constant.

The local self-hosted demo uses the private Compose database network and
permits its documented non-TLS `postgres` locator. Production files must use
`sslmode=verify-full`, provide an absolute root certificate reference, and
require a read-write PostgreSQL target. Caller-controlled options, session SQL,
`search_path`, application-name replacement, target weakening, fragments,
wrong identities, and unexpected ports are rejected. This validates a
configuration contract; TLS certificate distribution/automation remains an
operator responsibility and is not implemented here.

`python -m slaif_agent_site.control_api --check` validates the typed boundary
without reading the locator file, opening a network connection, creating a
pool, running SQL, binding a port, or mutating state.

## Pool lifecycle and session admission

The pool is created only inside the package-local Control FastAPI lifespan,
after ordinary service and Control settings validate. Importing modules or
constructing the app has no connection side effect. Existing pinned
`asyncpg==0.31.0` is used directly; there is no ORM, session registry, global
pool, raw client dependency, or SQL endpoint.

Defaults are deliberately bounded:

| Property | Default |
| --- | --- |
| Pool minimum / maximum | 1 / 4 |
| Connect / acquire / command | 3.0s / 1.5s / 2.0s |
| Inactive connection lifetime | 60s |
| Shutdown drain | 5s |
| Statement / lock timeout | 2000ms / 500ms |
| Idle transaction timeout | 2000ms |
| Application name | `slaif-control-api` |

asyncpg applies the trusted session defaults when creating a connection. Its
per-new-connection initializer checks:

- current database equals the configured target;
- `session_user` and `current_user` equal the expected login;
- effective membership among all product roles is exactly
  `slaif_control`; and
- owner, Reviewer, Agent, Editor, reader, scheduler, media, and GC authority is
  absent.

A wrong or combined credential is never admitted. The pool drains on normal
shutdown and lifespan exceptions. Cancellation is propagated after bounded
cleanup; an over-time close terminates the pool. The adapter exposes only
start, stop, its typed readiness probe, and the typed initial-local-
administrator operation—no raw/native pool or arbitrary execute/fetch method.
Password hashing completes before the setup transaction takes the singleton
lock.

## Readiness function and health semantics

Alembic revision `007_001` creates exactly one no-argument function:
`control.slaif_control_readiness()`. It is owned by `slaif_owner`, stable,
parallel-restricted, `SECURITY DEFINER`, and fixed to
`search_path=pg_catalog`. All table references are fully qualified. `PUBLIC`
execute is revoked; schema usage and function execute are granted only to
`slaif_control`. No service role receives direct `SELECT` or mutation authority
on `control.bootstrap_readiness`, `control.alembic_version`,
`control.installation_state`, `control.user_account`, or
`control.platform_administrator`.

The function returns one bounded row containing the actual Alembic revision,
marker revision, readiness state, safe flag, foundation distribution, and
foundation version. It accepts no site, workspace, session, operation, request,
or caller-controlled value and performs no write.

Revision `009_001` adds `control.slaif_initial_setup_lock()` and
`control.slaif_complete_initial_local_administrator(...)`. They share the same
owner, fixed search path, full qualification, `PUBLIC` revoke, and Control-only
execute rules. The first locks and returns bounded installation proof state;
the second locks again, rechecks expiry/generation/digest, inserts the identity
and administrator assignment, initializes, and clears token material. Neither
grants direct relation access. See
[local authentication](LOCAL_AUTHENTICATION.md).

`/health/live` remains process-only. `/health/ready` includes exactly one
Control component named `database` and returns 200 only when:

- pool startup and per-connection identity verification succeeded;
- both revision facts equal the single packaged head;
- marker state is `EMPTY_SAFE` or `HARDENED` with `safe=true`; and
- foundation distribution/version match the pinned qualification.

Otherwise readiness is 503 with one bounded reason:
`configuration_invalid`, `connection_unavailable`, `identity_mismatch`,
`role_mismatch`, `migration_mismatch`, `unsafe_marker`,
`foundation_mismatch`, `timeout`, or `shutdown`. Exception text, SQL, schema
internals beyond the stable `database` component, host, user, locator, and
password are never returned. A failed database does not make liveness fail.

Compose starts Control only after bootstrap completes. NGINX waits for Control
health initially and its own ongoing health check includes the proxied Control
readiness path. Wrong login/role, unreadable file, unsafe marker, migration
mismatch, or stopped PostgreSQL therefore leaves Control and NGINX unready.
Neither process repairs the database or broadens a grant.

## Requirement before another process connects

Another process may receive a database credential only through a separate
architecture/work order that repeats, rather than shares, this pattern:

1. one fixed login and one fixed least-privilege role;
2. one isolated file mount not visible to siblings;
3. one process-owned typed settings model and lifespan pool;
4. exact per-connection identity and forbidden-authority checks;
5. only trusted bounded functions/relations required by that process;
6. explicit `PUBLIC` revoke, grant/denial verification, timeout and cleanup
   tests;
7. stable sanitized health behavior without publication authority; and
8. updated Compose, documentation, cross-process negative tests, and full CI.

Network membership, a generated future DSN, or a conceptual role in
`authority.py` is not permission to connect. In particular, Editor, Render,
MCP, Media, Review, Scheduler, GC, Web, and browser processes remain
database-credential-free in this implementation.
