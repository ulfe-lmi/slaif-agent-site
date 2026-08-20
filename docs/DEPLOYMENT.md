# Local Compose deployment skeleton

The implemented default deployment is a pre-alpha status and authority
skeleton. It starts every planned process identity, establishes the empty-safe
database foundation, and exposes health-only services through NGINX. It does
implements local setup/authentication but not sites, workspaces, editing, browser
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

The first start creates four named volumes, generates private local database
files, isolates the Control DSN, initializes PostgreSQL, and runs the one-shot
bootstrap. A returning start validates and reuses the credentials and data,
reruns the idempotent bootstrap proof, and then starts the same service graph.

### PostgreSQL baseline

Initial supported PostgreSQL installations use fresh volumes created by the
Alpine/musl image pinned in this repository. Raw database volumes are not
portable between glibc and musl image families, and this pre-alpha release has
no legacy-installation or cross-family migration support. Never delete a
non-disposable volume merely to bypass this boundary; a future real migration
requires a separately designed and tested logical process.

## Implemented public surface

| Path | Upstream | Current behavior |
| --- | --- | --- |
| `/` | Web | Accessible pre-alpha deployment-status page. |
| `/health/live`, `/health/ready` | Web | Bounded Web process health only. |
| `/api/control/` | Control API | Prefix-stripped health routes only; readiness includes one database component. |
| `/api/editor/` | Editor API | Prefix-stripped health routes only. |
| `/api/agent/` | Agent API | Prefix-stripped health routes only. |
| `/mcp/` | MCP adapter | Prefix-stripped health routes only. |
| `/media/` | Media service | Prefix-stripped health routes only. |

Unknown product and API paths return 404. Render, PostgreSQL, bootstrap,
workers, and browser worker are not routed. Health is process evidence, not
product readiness or publication authority.

NGINX replaces any caller request ID with one bounded 32-character lowercase
hexadecimal ID, passes that value upstream, hides an upstream response field,
and returns exactly one authoritative `X-Request-ID`. The Apache reference uses
the same replace/hide/single-response contract with `mod_unique_id`'s bounded
safe identifier. Both edges set one self-hosted baseline CSP for page, API, and
404 responses: scripts, styles, fonts, connections, and ordinary resources are
limited to self; images additionally permit `data:`; base URIs, objects, and
framing are denied; forms are limited to self. There is no wildcard, external
origin, unsafe inline/eval allowance, reporting endpoint, or telemetry.

The current page is server-rendered and has no interactive client behavior.
The strict `script-src 'self'` deliberately does not authorize Next.js inline
hydration data; a future interactive UI must adopt a reviewed nonce or hash
design rather than weaken this baseline.

## Service and image inventory

| Services | Image | Runtime user | Networks | Persistent/private mount |
| --- | --- | --- | --- | --- |
| `secrets-init` | Backend | root with only `CHOWN` and `DAC_READ_SEARCH` added | none | master local secrets and isolated Control secret, read/write |
| `postgres` | PostgreSQL | official entrypoint drops to PostgreSQL user | database | PostgreSQL data; local secrets read-only |
| `bootstrap` | Backend | `10001:10001` | database | local secrets read-only |
| `control-api` | Backend | `10001:10001` | edge, database | isolated Control secret, read-only |
| Five other Python HTTP services | Backend | `10001:10001` | exact edge/application/database memberships | media volume on Media only |
| Three Python workers | Backend | `10001:10001` | database | media volume on media-GC only |
| `browser-worker` | Browser placeholder | `10001:10001` | browser only | none |
| `web` | Next.js | `10001:10001` | edge, application | none |
| `nginx` | NGINX Open Source | `101:101` | edge only | none |

All Compose containers use a read-only root filesystem, drop all default Linux
capabilities, and enable `no-new-privileges`. Narrow tmpfs mounts support
runtime scratch paths. PostgreSQL and the initializer add only the capabilities
needed for initialization and file ownership. There is no source bind mount,
Docker socket, host network, or privileged container.

The long-running Python processes use truthful `development` mode and the
loopback public URL. `test` is not the shipped default, and the stack does not
claim production mode without its fail-closed HTTPS, cookie, and secret
requirements.

The reviewed OCI inputs are:

| Repository and readable version | Immutable top-level digest | License | Platforms reviewed |
| --- | --- | --- | --- |
| `python:3.12.12-alpine3.23` | `sha256:2d91681153dd4b8cdb52d4fd34a17b9edbafa4dd3086143cfd4b6c3a84c1acb0` | PSF | official multi-platform index |
| `ghcr.io/astral-sh/uv:0.12.5` | `sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1` | Apache-2.0 or MIT | amd64, arm64 |
| `node:24.14.1-alpine3.23` | `sha256:8510330d3eb72c804231a834b1a8ebb55cb3796c3e4431297a24d246b8add4d5` | MIT | official multi-platform index |
| `postgres:18.6-alpine3.23` | `sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f` | PostgreSQL | official multi-platform index |
| `nginx:1.29.7-alpine3.23` | `sha256:e7257f1ef28ba17cf7c248cb8ccf6f0c6e0228ab9c315c152f9c203cd34cf6d1` | two-clause BSD | official multi-platform index |
| `httpd:2.4.68-alpine3.23` | `sha256:4a15e9c73f25334bc03cfb3c692c9adfc103bb46ca89cee1f0b9a5fcbc7b21f6` | Apache-2.0 | official multi-platform index |

Project images apply exact Alpine security package revisions recorded in the
machine supply-chain policy. The Node runtime stages remove the unused bundled
npm CLI tree, the NGINX stage removes unused curl and its orphaned libraries,
and the Apache reference removes unused Perl. These removals do not change the
public edge, health, service, network, or secret topology.

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
  database. Control alone currently opens an online pool; network membership
  gives every other process no credential or database authority.
- `browser`: only Agent API and browser worker. It is internal and has no
  PostgreSQL, edge, host, filesystem, or Docker-socket path.

The private `local-secrets` volume contains a PostgreSQL administrator password,
ten distinct fixed-login passwords, provisioner/owner DSNs, and nine future
service DSNs. Files are mode `0400`; PostgreSQL's password belongs to UID 999
and bootstrap-readable files to UID 10001. The directory is mode `0710`, owned
by root and dedicated group 10002; only PostgreSQL and bootstrap receive that
supplemental traversal group. Only initializer, PostgreSQL, and bootstrap mount
this volume. No long-running application mounts this master volume.

The separate `control-secret` volume contains exactly one `control-dsn` file
copied byte-for-byte from the generated fixed `slaif_control_login` locator.
Its directory is mode `0700` and owned by `10001:10001`; its file is mode
`0400`, owned by UID 10001. Only initializer mounts it read/write. Control API
mounts it read-only at `/run/slaif-control`; every other long-running process
lacks the mount, and Control cannot see the master secret directory. The DSN
is never an environment value.

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

The reference listens on 8080 and is not part of Compose. Its CSP and
request-ID replacement/removal behavior is syntax- and contract-tested against
the NGINX policy. For production,
define a separately reviewed TLS virtual host, do not ship keys in an image,
and trust incoming forwarded headers only from explicitly configured proxies.
Edge configuration cannot replace application authentication or authorization.

## Scope and limitations

This topology is defense in depth, not a hostile multi-tenant isolation or
production certification. CI now creates six-image SPDX and vulnerability
evidence under the bounded [supply-chain policy](SUPPLY_CHAIN.md), but it does
not sign or publish release images. Service-to-service authentication,
non-Control online database credentials, production TLS automation, egress
policy enforcement, backups, rotation, metrics, release signing, and deployment
approval remain deferred.
See [operations](OPERATIONS.md) for lifecycle and failure handling.
