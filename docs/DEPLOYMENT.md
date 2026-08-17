# Local Compose deployment skeleton

The implemented default deployment is a pre-alpha status and authority
skeleton. It starts every planned process identity, establishes the empty-safe
database foundation, and exposes health-only services through NGINX. It does
not implement setup, authentication, sites, workspaces, editing, browser
automation, review, or publication.

## Prerequisites and startup

Use a Linux host with Docker Engine and the Compose v2 plugin. The validated
development environment used Docker Engine `29.1.3` and Compose `2.40.3`; the
files use standard Compose Specification features including long-form
`depends_on` health conditions.

From a clean clone, run:

```bash
docker compose up --build
```

No `.env`, package installation, account, cloud API key, or manual secret
generation is required. Image and package downloads are build prerequisites.
When every dependency is healthy, open <http://localhost:8080/>. The binding is
loopback-only; no other host port is published.

For a bounded foreground readiness check, use:

```bash
docker compose up --build --wait
docker compose ps
```

The first start creates three named volumes, generates private local database
files, initializes PostgreSQL, and runs the one-shot bootstrap. A returning
start validates and reuses the credentials and data, reruns the idempotent
bootstrap proof, and then starts the same service graph.

## Implemented public surface

| Path | Upstream | Current behavior |
| --- | --- | --- |
| `/` | Web | Accessible pre-alpha deployment-status page. |
| `/health/live`, `/health/ready` | Web | Bounded Web process health only. |
| `/api/control/` | Control API | Prefix-stripped health routes only. |
| `/api/editor/` | Editor API | Prefix-stripped health routes only. |
| `/api/agent/` | Agent API | Prefix-stripped health routes only. |
| `/mcp/` | MCP adapter | Prefix-stripped health routes only. |
| `/media/` | Media service | Prefix-stripped health routes only. |

Unknown product and API paths return 404. Render, PostgreSQL, bootstrap,
workers, and browser worker are not routed. Health is process evidence, not
product readiness or publication authority.

## Service and image inventory

| Services | Image | Runtime user | Networks | Persistent/private mount |
| --- | --- | --- | --- | --- |
| `secrets-init` | Backend | root with only `CHOWN` and `DAC_READ_SEARCH` added | none | local secrets, read/write |
| `postgres` | PostgreSQL | official entrypoint drops to PostgreSQL user | database | PostgreSQL data; local secrets read-only |
| `bootstrap` | Backend | `10001:10001` | database | local secrets read-only |
| Six Python HTTP services | Backend | `10001:10001` | exact edge/application/database memberships | media volume on Media only |
| Three Python workers | Backend | `10001:10001` | database | media volume on media-GC only |
| `browser-worker` | Browser placeholder | `10001:10001` | browser only | none |
| `web` | Next.js | `10001:10001` | edge, application | none |
| `nginx` | NGINX Open Source | `101:101` | edge only | none |

All Compose containers use a read-only root filesystem, drop all default Linux
capabilities, and enable `no-new-privileges`. Narrow tmpfs mounts support
runtime scratch paths. PostgreSQL and the initializer add only the capabilities
needed for initialization and file ownership. There is no source bind mount,
Docker socket, host network, or privileged container.

The reviewed OCI inputs are:

| Repository and readable version | Immutable top-level digest | License | Platforms reviewed |
| --- | --- | --- | --- |
| `python:3.12.12-slim-bookworm` | `sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c` | PSF | amd64, arm64 and official additional targets |
| `ghcr.io/astral-sh/uv:0.12.5` | `sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1` | Apache-2.0 or MIT | amd64, arm64 |
| `node:24.14.1-bookworm-slim` | `sha256:b506e7321f176aae77317f99d67a24b272c1f09f1d10f1761f2773447d8da26c` | MIT | amd64, arm64, ppc64le, s390x |
| `postgres:18.6-trixie` | `sha256:06cad38a5d9f5d24b4d83d86def30795d5e4b757fedbf5281172b576dedcd941` | PostgreSQL | official multi-platform index |
| `nginx:1.29.6-alpine3.23` | `sha256:f46cb72c7df02710e693e863a983ac42f6a9579058a59a35f1ae36c9958e4ce0` | two-clause BSD | official multi-platform index |
| `httpd:2.4.66-alpine3.23` | `sha256:968c8b4098fcecb473762b45f6c541a3b2b2cfab2caccb1edbd2cece071ef160` | Apache-2.0 | official multi-platform index |

The new Web registry inputs are exact and frozen with these npm integrity
values:

| Package | License | npm integrity |
| --- | --- | --- |
| `next@16.3.1` | MIT | `sha512-hsAp0i7Rh+/dhe7DGIeN2YlpLM1DP4MNxti9EtDMtqcO612X81MvvEj388/oTce9U1EcEIOWDlGq0zRwrBKvuA==` |
| `react@19.2.8` | MIT | `sha512-PWaYA1L/q9u2u7xYQi+Y3L3Yfnie7XyLeaJICV1MGD6LprsBxcAqGjYyr0eY3p+QdsA+x/Irkt4Qif8D63+Sbw==` |
| `react-dom@19.2.8` | MIT | `sha512-rVprimfGBG3DR+Tq0IQG2DT5PxKth1WIGDmj5yPmlzr4YBe7uyE+Du4oVqTDXZSHGGGXRtTJEGSSePyQCMBglQ==` |
| `@types/react@19.2.18` | MIT | `sha512-AnzbBERsrLKtk2XSfTbYRLjQPdy116Sty4q+T+Bp3IC4l6jNBvreVPAHmpq9qhXQM7CXZPjLVmGMw9sy+hxQ3w==` |
| `@types/react-dom@19.2.4` | MIT | `sha512-Bsc+QHgp+P/F02XDzNCY9jnZNCUuLki36KT7VKrTXXLdHf+vHMNZnW1rVu5DNW/rCK+fya3DATySbLM4yhtKUw==` |

The transitive review explicitly accepts `caniuse-lite` browser-compatibility
data under CC-BY-4.0 and `tslib` under 0BSD. Their attribution-bearing package
metadata remains in the frozen install. The unused `sharp` image-optimization
optional dependency is denied by pnpm policy, and the status surface sets
unoptimized local images, so its LGPL libvips bundle is neither locked nor
installed. Optional Playwright peer metadata does not install Playwright or a
browser binary.

Updates require a scoped work order, registry/version/license/platform review,
replacement top-level digest, clean builds, the complete packaging test, and
the normal dependency/security gates. Never refresh a digest without reviewing
the readable tag it is meant to freeze.

## Network and credential topology

The named internal networks express current and future connection direction;
network membership does not grant application authority.

- `edge`: NGINX, Web, and the five externally routed API processes.
- `application`: Web to Render, plus MCP internal HTTP access.
- `database`: PostgreSQL and only processes whose architecture may later use a
  database. No online pool or service DSN is wired yet.
- `browser`: only Agent API and browser worker. It is internal and has no
  PostgreSQL, edge, host, filesystem, or Docker-socket path.

The private `local-secrets` volume contains a PostgreSQL administrator password,
ten distinct fixed-login passwords, provisioner/owner DSNs, and nine future
service DSNs. Files are mode `0400`; PostgreSQL's password belongs to UID 999
and bootstrap-readable files to UID 10001. The directory is mode `0710`, owned
by root and dedicated group 10002; only PostgreSQL and bootstrap receive that
supplemental traversal group. Only initializer, PostgreSQL, and bootstrap mount
this volume. No long-running application receives a DSN.

Institutional deployments may replace the generator with externally managed
files that use the same names and fixed principal model. They must preserve
ownership/mode policy and arrange their own one-shot validation. The default
generator is local convenience, not a production secret-management claim.

## Apache HTTP Server alternative

NGINX Open Source is the default edge. `infra/apache` supplies a syntax-tested
Apache HTTP Server 2.4 reference with the same prefix stripping, upstreams,
request/forwarded headers, response headers, compression, limits, and timeout
shape. It requires `mod_headers`, `mod_proxy`, `mod_proxy_http`,
`mod_unique_id`, and `mod_deflate` in addition to the official default modules.

The reference listens on 8080 and is not part of Compose. For production,
define a separately reviewed TLS virtual host, do not ship keys in an image,
and trust incoming forwarded headers only from explicitly configured proxies.
Edge configuration cannot replace application authentication or authorization.

## Scope and limitations

This topology is defense in depth, not a hostile multi-tenant isolation or
production certification. Service-to-service authentication, online database
credentials, TLS automation, egress policy enforcement, backups, rotation,
metrics, and full vulnerability/SBOM release policy remain deferred. See
[operations](OPERATIONS.md) for lifecycle and failure handling.
