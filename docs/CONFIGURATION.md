# Backend configuration contract

## Administration shell

The administration shell has no client-configurable API origin. It uses
same-origin requests under `/api/control/v1`, keeps the selected site in the
canonical `/admin/sites/{site_id}` URL, and does not persist site, permission,
session, or capability claims in browser storage. NGINX remains the only
published origin in the default topology.

Tailwind CSS is compiled into the application build. The in-repository UI
primitives and exact Radix primitive dependency require no CDN, font host,
telemetry endpoint, hosted account, or runtime package service.

The current Python backend has shared typed configuration for long-running
services, separate Control, Editor, Agent, Render, and Media online database
models, and separate typed configuration for explicit one-shot database
bootstrap. Each service owns its fixed database login and pool; Media also
owns a validated absolute local store root and bounded upload limit.

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

## Media service configuration

`MediaSettings` uses the `SLAIF_MEDIA_` prefix. Outside explicit test mode its
DSN must be the mounted mode-`0400` `/run/slaif-media/media-dsn` file and the
identity is fixed to `slaif_media_login`/`slaif_media`. The local store root
defaults to `/var/lib/slaif/media` and must be absolute; invalid or unwritable
storage makes Media readiness unavailable without exposing the path.

| Variable | Local value/default | Contract |
| --- | --- | --- |
| `SLAIF_MEDIA_DSN_FILE` | `/run/slaif-media/media-dsn` | Dedicated Media-owned locator file. |
| `SLAIF_MEDIA_EXPECTED_DATABASE` | `slaif` | Fixed target outside tests. |
| `SLAIF_MEDIA_EXPECTED_LOGIN` | `slaif_media_login` | Fixed Media login outside tests. |
| `SLAIF_MEDIA_EXPECTED_PRIVILEGE_ROLE` | `slaif_media` | Fixed sole product role. |
| `SLAIF_MEDIA_ROOT` | `/var/lib/slaif/media` | Absolute private content-addressed root; never an HTTP alias. |
| `SLAIF_MEDIA_MAX_UPLOAD_BYTES` | `104857600` | Bounded 1–500 MiB upload limit. |

The reference NGINX and Apache adapters keep the global request-body limit at
1 MiB and scope the larger `104857600 + 262144` byte allowance to `/media/`.
The extra 256 KiB is bounded multipart framing/metadata overhead for the
default 100 MiB file limit; deployments changing the Media file limit must
review the corresponding edge limit rather than relaxing unrelated routes.

## Browser preview credential configuration

Agent and Render each have one absolute reference to the same isolated signing
file; the secret value itself is never an environment variable. Reference
Compose uses:

| Variable | Local value | Consumer/contract |
| --- | --- | --- |
| `SLAIF_AGENT_BROWSER_SIGNING_KEY_FILE` | `/run/slaif-browser-signing/signing-key` | Agent signer only |
| `SLAIF_RENDER_BROWSER_SIGNING_KEY_FILE` | `/run/slaif-browser-signing/signing-key` | Render verifier only |

The networkless one-shot initializer creates exactly one
`sbk1:<16-hex-key-id>:<43-base64url-secret>` value. The directory must be a
non-symlink mode-`0700` directory owned by the process UID and the file a
regular non-symlink mode-`0400` file with that same owner. Reads use a directory
descriptor plus relative `O_NOFOLLOW` open and bounded ASCII size. Missing,
wrong-mode, wrong-owner, symlinked, malformed, or extra-file state fails the
browser-signing readiness probe. `--check` validates only the absolute reference
and does not read or create a key.

The algorithm (`HS256`), token/type/deployment/audience/contract versions,
60-second maximum TTL, 4,096-byte token maximum, claims, and dedicated Web and
Render header names are fixed trusted code/contract facts, not environment
settings. Web and the browser worker have no key setting or mount.

## Browser worker configuration

The browser worker and dormant Agent-side client share one independently
generated service credential; it is not the Agent capability, preview signing
key, Render token, or human session. Reference Compose uses:

| Variable | Local value | Consumer/contract |
| --- | --- | --- |
| `SLAIF_AGENT_BROWSER_WORKER_SERVICE_CREDENTIAL_FILE` | `/run/slaif-browser-worker/worker-token` | Agent client, read-only |
| `SLAIF_AGENT_BROWSER_WORKER_ENDPOINT` | `http://browser-worker:3100` | Fixed internal Agent client origin |
| `BROWSER_WORKER_SERVICE_CREDENTIAL_FILE` | `/run/slaif-browser-worker/worker-token` | Worker verifier, read-only |
| `BROWSER_WORKER_ARTIFACT_ROOT` | `/var/lib/slaif/browser-artifacts` | Absolute private worker-only store |
| `BROWSER_WORKER_PREVIEW_ORIGIN` | `http://web:3000` | Fixed operator-owned internal navigation origin |
| `SLAIF_BROWSER_PREVIEW_AUTHORITY` | `localhost:8080` | Web-only trusted site-resolution authority for browser-token mode |
| `BROWSER_WORKER_CHROMIUM_EXECUTABLE` | `/ms-playwright/chromium-1669021/chrome-linux64/chrome` | Image-fixed executable |
| `BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION` | `152.0.7977.64` | Readiness version assertion |

The Agent API's durable browser dispatcher is enabled by default in the
development Compose profile. Its bounded settings are `SLAIF_AGENT_DISPATCHER_ENABLED`,
`SLAIF_AGENT_DISPATCHER_POLL_INTERVAL_SECONDS` (0.05–10),
`SLAIF_AGENT_DISPATCHER_BACKOFF_SECONDS` (0.1–30),
`SLAIF_AGENT_DISPATCHER_LEASE_SECONDS` (1–60),
`SLAIF_AGENT_DISPATCHER_RENEWAL_INTERVAL_SECONDS` (below the lease),
`SLAIF_AGENT_DISPATCHER_WORKER_TIMEOUT_SECONDS` (5–120),
`SLAIF_AGENT_DISPATCHER_CONCURRENCY` (1–2), and
`SLAIF_AGENT_DISPATCHER_SHUTDOWN_TIMEOUT_SECONDS` (0.1–30). The dispatcher
uses only the Agent pool, signing key, and internal worker credential; it does
not expose these values or any run payload in readiness output.

The one-shot initializer writes exactly
`sbws1:<16-hex-key-id>:<43-base64url-secret>` into a mode-`0700`
UID-10001 directory with one mode-`0400`, single-link regular file. Both
runtimes use descriptor-confined no-follow reads. Missing, malformed,
symlinked, broad-mode, wrong-owner, or extra-link state makes Agent client or
worker readiness unavailable. No plaintext worker secret is accepted from an
environment variable.

Target descriptors, request/result/artifact bounds, routes, result HMAC facts,
active-attempt limit, zero queue depth, and retention interval are fixed shared
contract data rather than caller settings. Web and Render do not mount the
worker credential or artifact root; the worker does not mount the preview
signing key.

An environment file is never loaded implicitly. Setting `SLAIF_ENV_FILE`
opts in to one absolute file only in `development`; `test` and `production`
reject it. Normal production deployments should use a mounted secret file.
The direct secret and secret-file reference are mutually exclusive.

Production startup fails closed when the public URL uses HTTP, secure cookies
are disabled, a secret is absent/weak, a secret file cannot be read, or another
field is invalid. The emitted configuration error is constant and does not
contain the rejected value. Secret values use Pydantic `SecretStr` and remain
masked in representations and JSON serialization.

The setting is named `APP_SECRET` as the future application/service-secret
slot. Session credentials currently use independently generated 256-bit values
and SHA-256 digests; the app secret is not used to recover or store plaintext.
There is no password-policy, Argon2-cost, initial-username, or administrator
configuration input; the validated policy and production hash profile are
fixed in trusted code.

Local credential verification uses the fixed RFC 9106 LOW_MEMORY Argon2id
profile and a source-reviewed equal-cost dummy hash. Argon2 cost is not an
environment setting; changing it requires trusted code and migration/testing
work. There is no rate-limit, login-audit, OIDC, MFA, or HTTP-login setting in
this baseline.

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

All expose `/health/live` and `/health/ready`; Render additionally exposes the
internal-only resolver documented in [API](API.md). Their public docs,
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

## Render database configuration

`RenderDatabaseSettings` is owned by `render_api`, uses `SLAIF_RENDER_`, and
fixes login `slaif_public_login`, privilege role `slaif_public_reader`, default
locator `/run/slaif-render/render-dsn`, and application name
`slaif-render-api`. Development and production use an absolute, process-owned,
mode-`0400` locator file; production requires verified-full TLS and an absolute
root certificate. Direct DSNs are test-only and restricted to loopback or
`.test`. Check mode validates the static contract without reading the file or
opening a connection. Reference Compose mounts only the isolated
`render-secret` volume at `/run/slaif-render`, read-only. Missing, empty,
symlinked, broad-mode, wrong-owner, wrong-login, wrong-role, or unavailable
locator state makes Render readiness fail closed and consequently makes Web and
NGINX readiness fail.

## Editor database configuration

`EditorDatabaseSettings` is owned by `editor_api`, uses `SLAIF_EDITOR_`, and
fixes login `slaif_editor_login`, privilege role `slaif_editor_runtime`,
default locator `/run/slaif-editor/editor-dsn`, and application name
`slaif-editor-api`. The Editor process opens this pool for authorized human
content and composition COW operations, while its separate Control pool handles
human session and site authorization. Compose mounts only `editor-secret` at
`/run/slaif-editor` for the Editor process. The editor readiness probe executes
the bounded page-list function and fails closed on missing content migrations,
wrong identity, or unavailable database state. `--check` validates both typed
settings without reading either locator or opening a connection.

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
- `SLAIF_BOOTSTRAP_SETUP_TOKEN_TTL_MINUTES` optionally sets a 5–60 minute
  lifetime for explicit setup-token issuance; the default is 30.
- `SLAIF_BOOTSTRAP_SETUP_URL` optionally sets the absolute HTTP(S) `/setup`
  URL printed separately from a newly issued token; it cannot carry
  credentials, a query, or a fragment.
- `SLAIF_BOOTSTRAP_DEMO_SEED` defaults to `false`. It may be true only with the
  local secret manifest and a loopback `/setup` URL. Reference Compose enables
  it to create the exact fresh active `demo` site before token output.

The local stack uses bootstrap `production` mode because both database locators
are mounted files. Its long-running services use `development` mode
with the loopback HTTP URL. `test` remains restricted to automated tests and
explicit test overlays; the pre-alpha stack does not falsely claim production
configuration while authentication, application secrets, secure cookies, and
TLS are deliberately absent.

Direct locator fields are restricted to disposable `test` mode. There is no
shared `SLAIF_DATABASE_URL`, default credential, implicit environment file, or
module-import connection. See [database bootstrap](DATABASE_BOOTSTRAP.md) for
commands and marker semantics.

Setup-token configuration belongs only to the one-shot bootstrap package. It
does not put a token in an environment variable or URL, grant direct table
access to Control, or enable an online setup endpoint. The code/test-only
consumer uses the already-isolated Control credential and two narrow
functions. See
[installation setup](INSTALLATION_SETUP.md).

## Deferred configuration

The installation-bound `control.site_policy` singleton stores a bounded
`max_sites` quota (default 100,
valid range 1 through 1000). It is owner-managed installation policy, not an
environment variable or caller-controlled site-create field. Site keys,
locales, hostnames, and path prefixes are normalized by trusted Control code;
there is no wildcard-domain, trusted-proxy, or forwarded-header setting in
this round.

The default initializer generates service DSN files and copies only each
process's exact locator into its separate one-file mounted volume; online
processes never see the master volume. Media and browser-artifact storage are
local and private by default. Identity providers, browser source origins,
durable dispatcher/lease wiring, trusted proxies, CORS, jobs, metrics, and
later distributed storage backends remain deferred under their process-
specific architecture work orders.
Server-side session persistence, expiry, recent-auth, CSRF credential policy,
and cookie value objects are implemented in 010-e. HTTP authentication routes,
OIDC, MFA, rate limiting, and durable auth audit remain deferred. Capability-
bound preview-run HTTP, run-token Render verification, and direct authenticated
worker execution are implemented without a dispatcher. Authentication E2E uses the
fixed localhost deployment URL and a mode-0600 temporary secret file; it adds no
product runtime setting.

## Human-session policy

The server-side foundation uses `HumanSessionPolicy` in trusted code, not
environment-selected caller input. Defaults are a 300-second touch interval,
1,800-second idle timeout, 28,800-second absolute lifetime, and 900-second
recent-auth window. Validation requires `0 < touch < idle < absolute` and
`0 < recent-auth <= absolute`. PostgreSQL database time decides expiry and
recent-auth; application wall-clock injection is not used for authorization.

The HTTP layer uses the value-object contract: HTTP-only,
`SameSite=Lax`, `Path=/`, no Domain, and Max-Age no greater than absolute
lifetime. Production uses `Secure` and `__Host-slaif_session`; development
local uses non-Secure `slaif_session`. CSRF is a separate `sas2_csrf_...`
credential and is required for every future state-changing cookie-authenticated
Control call. State-changing authentication verifies both bound credentials
before its single persistence finalization; denied requests do not touch the
session row.
