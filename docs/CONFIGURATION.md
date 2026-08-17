# Backend configuration contract

The current Python backend is a process and health-check skeleton. It has typed
local configuration, but it does not connect to PostgreSQL, authenticate a
caller, expose a product API, run a job, or perform bootstrap mutations.

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
state. Without `--check`, the six HTTP modules start Uvicorn using an app object
and the configured bind values:

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
`NOT_IMPLEMENTED` skeletons without a listener or busy loop. Bootstrap is a
one-shot `NOT_IMPLEMENTED` skeleton and returns without migration, COW, role,
or setup mutation.

## Deferred configuration

Database URLs, PostgreSQL pools/roles, identity providers, browser sources,
media stores, service authentication, trusted proxies, CORS, sessions, jobs,
metrics, and product feature settings are not implemented. They must be added
later under their process-specific authority and architecture work orders.
