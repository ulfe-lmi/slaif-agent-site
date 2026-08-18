# Backend configuration contract

The current Python backend has shared typed configuration for health-only
long-running skeletons, a separate Control-only online database model, and
separate typed configuration for explicit one-shot database bootstrap. Control
API is the only online process that connects to PostgreSQL. No process
authenticates a caller, exposes a product API, or runs a product job.

## Loading rules

`ServiceSettings` reads only variables with the `SLAIF_` prefix. It has no
cloud secret-manager integration and does not contact an account-bound service.
Process identity is selected by trusted module code and cannot be changed by an
environment variable or request.

| Variable | Default | Contract |
| --- | --- | --- |
| `SLAIF_MODE` | `development` | One of `development`, `test`, or `production`. |
| `SLAIF_PUBLIC_URL` | `http://localhost:8080` | HTTP(S) URL without credentials, query, or fragment. Production requires HTTPS. |
| `SLAIF_BIND_HOST` | `127.0.0.1` | Bounded host/IP used only when an HTTP module is explicitly started. |
| `SLAIF_BIND_PORT` | `8000` | Integer from 1 through 65535. |
| `SLAIF_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `SLAIF_LOG_FORMAT` | `json` | JSON is the only implemented log format. |
| `SLAIF_ENV_FILE` | unset | Absolute path loaded only as an explicit development opt-in. |
| `SLAIF_APP_SECRET` | unset | Secret-safe value; production requires one strong secret source. |
| `SLAIF_APP_SECRET_FILE` | unset | Absolute mounted-file alternative to the plaintext variable. |
| `SLAIF_SECURE_COOKIES` | `false` | Must be `true` in production. No session behavior exists yet. |
| `SLAIF_SHUTDOWN_TIMEOUT_SECONDS` | `15` | Bounded integer from 1 through 120. |
| `SLAIF_READINESS_TIMEOUT_SECONDS` | `2.0` | Per-probe bound from 0.05 through 30 seconds. |

An environment file is never loaded implicitly. Setting `SLAIF_ENV_FILE`
opts in to one absolute file only in `development`; `test` and `production`
reject it. Normal production deployments should use a mounted secret file.
The direct secret and secret-file reference are mutually exclusive.

Production startup fails closed when the public URL uses HTTP, secure cookies
are disabled, a secret is absent/weak, a secret file cannot be read, or another
field is invalid. The emitted configuration error is constant and does not
contain the rejected value. Secret values use Pydantic `SecretStr` and remain
masked in representations and JSON serialization.

The setting is named `APP_SECRET` only as a future application/service-secret
slot. No current route consumes it, and no test value is a production secret.

## Process checks and starts

Every process supports a safe configuration/authority check:

```bash
python -m slaif_agent_site.control_api --check
python -m slaif_agent_site.editor_api --check
python -m slaif_agent_site.agent_api --check
python -m slaif_agent_site.render_api --check
python -m slaif_agent_site.mcp_adapter --check
python -m slaif_agent_site.media_service --check
python -m slaif_agent_site.review_worker --check
python -m slaif_agent_site.scheduler --check
python -m slaif_agent_site.media_gc --check
python -m slaif_agent_site.bootstrap --check
```

Check mode does not bind a port, connect to a database, run a job, or mutate
state. Control check mode validates the typed locator reference but does not
read that file. Without `--check`, the six HTTP modules start Uvicorn using an
app object and the configured bind values:

```bash
python -m slaif_agent_site.control_api
python -m slaif_agent_site.editor_api
python -m slaif_agent_site.agent_api
python -m slaif_agent_site.render_api
python -m slaif_agent_site.mcp_adapter
python -m slaif_agent_site.media_service
```

Those apps expose only `/health/live` and `/health/ready`. Their public docs,
ReDoc, and OpenAPI routes are disabled, although deterministic in-process tests
can call `app.openapi()`.

Review worker, scheduler, and media-GC start as cancellation-aware idle
`NOT_IMPLEMENTED` skeletons without a listener or busy loop. Bootstrap now
requires an explicit database subcommand; running it without one cannot mutate
state.

## Control database configuration

`ControlDatabaseSettings` exists only in `control_api`, uses the
`SLAIF_CONTROL_` prefix, and is frozen. It does not extend `ServiceSettings` or
provide a generic database locator. Compose supplies:

| Variable | Local value/default | Contract |
| --- | --- | --- |
| `SLAIF_CONTROL_MODE` | `development` | `development`, `test`, or `production`; direct locators are test-only. |
| `SLAIF_CONTROL_DSN_FILE` | `/run/slaif-control/control-dsn` | Absolute mode-`0400`, Control-owned regular file. Required outside tests. |
| `SLAIF_CONTROL_EXPECTED_DATABASE` | `slaif` | Validated target database. |
| `SLAIF_CONTROL_EXPECTED_LOGIN` | `slaif_control_login` | Fixed outside explicit test mode. |
| `SLAIF_CONTROL_EXPECTED_PRIVILEGE_ROLE` | `slaif_control` | Fixed in every mode. |
| `SLAIF_CONTROL_POOL_MIN_SIZE` / `MAX_SIZE` | `1` / `4` | Minimum 1, maximum 16, and minimum cannot exceed maximum. |
| `SLAIF_CONTROL_ACQUIRE_TIMEOUT_SECONDS` | `1.5` | Bounded pool-acquire timeout. |
| `SLAIF_CONTROL_COMMAND_TIMEOUT_SECONDS` | `2.0` | Bounded asyncpg command timeout. |
| `SLAIF_CONTROL_CONNECT_TIMEOUT_SECONDS` | `3.0` | Bounded connection establishment timeout. |
| `SLAIF_CONTROL_SHUTDOWN_TIMEOUT_SECONDS` | `5.0` | Bounded pool-drain timeout before termination. |
| `SLAIF_CONTROL_MAX_INACTIVE_CONNECTION_LIFETIME_SECONDS` | `60.0` | Bounded idle connection lifetime. |
| `SLAIF_CONTROL_STATEMENT_TIMEOUT_MS` | `2000` | Server-side statement timeout. |
| `SLAIF_CONTROL_LOCK_TIMEOUT_MS` | `500` | Server-side lock timeout. |
| `SLAIF_CONTROL_IDLE_TRANSACTION_TIMEOUT_MS` | `2000` | Server-side idle-transaction timeout. |
| `SLAIF_CONTROL_APPLICATION_NAME` | `slaif-control-api` | Bounded trusted session label. |

Production locator files must use PostgreSQL `sslmode=verify-full`, provide an
absolute `sslrootcert`, and require `target_session_attrs=read-write`. The
documented local demo alone permits the internal `postgres` host with TLS
disabled. Query options that can inject session SQL, override search paths,
weaken target selection, or replace the trusted application name are rejected.
Explicit test mode permits only local or `.test` fake direct locators.

The locator uses `SecretStr`, is never emitted through repr/JSON/errors/health,
and is resolved only inside Control lifespan startup. See
[database connections](DATABASE_CONNECTIONS.md) for pool and failure semantics.

## One-shot database configuration

`BootstrapSettings` is defined only inside the bootstrap package. It does not
extend or reuse the `SLAIF_` service namespace and is not imported by an online
process. It validates the exact target database and separates a stronger
cluster-provisioner locator from the setup-owner locator.

Production accepts only absolute mounted secret files:

- `SLAIF_BOOTSTRAP_MODE=production`;
- `SLAIF_BOOTSTRAP_EXPECTED_DATABASE`;
- `SLAIF_BOOTSTRAP_PROVISIONER_DSN_FILE` for `provision` only; and
- `SLAIF_BOOTSTRAP_OWNER_DSN_FILE` for migration, status, COW, and validation.
- `SLAIF_BOOTSTRAP_LOCAL_SECRETS_DIR` for the local Compose command's fixed
  ten-login password manifest.

The local stack uses bootstrap `production` mode because both database locators
are mounted files. Its health-only long-running services use `development` mode
with the loopback HTTP URL. `test` remains restricted to automated tests and
explicit test overlays; the pre-alpha stack does not falsely claim production
configuration while authentication, application secrets, secure cookies, and
TLS are deliberately absent.

Direct locator fields are restricted to disposable `test` mode. There is no
shared `SLAIF_DATABASE_URL`, default credential, implicit environment file, or
module-import connection. See [database bootstrap](DATABASE_BOOTSTRAP.md) for
commands and marker semantics.

## Deferred configuration

The default initializer generates future service DSN files, but only the exact
Control DSN is copied into a separate mounted volume. All other online service
database locators/pools, identity providers, browser sources,
media stores, service authentication, trusted proxies, CORS, sessions, jobs,
metrics, and product feature settings are not implemented. They must be added
later under their process-specific authority and architecture work orders.
