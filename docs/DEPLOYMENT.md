# Local Compose deployment skeleton

The implemented default deployment starts every planned process identity,
establishes the database foundation, and exposes bounded services through
NGINX. It implements local setup/authentication, canonical page projection,
authenticated active-workspace preview, trusted SSR rendering, and direct
confined browser-worker evidence execution; review, promotion, publication,
durable browser dispatch/registration, and public media finalization remain
separate objectives.

## Prerequisites and startup

Use a Linux host with Docker Engine and the Compose v2 plugin. The validated
development environment used Docker Engine `29.1.3` and Compose `2.40.3`; the
files use standard Compose Specification features including long-form
`depends_on` health conditions.

On first startup, bootstrap prints the credential-free `/setup` URL and the
one-time setup token once. Open the URL, enter the token in the setup form,
create the local administrator, and then use `/login`; never place the token in
a URL, shell argument, log, screenshot, or trace.

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

The first start creates the named volumes, generates private local database
files plus separate public/preview Render locators and a Web-to-Render
credential, plus one browser signing key isolated to Agent and Render,
initializes PostgreSQL, seeds the exact fresh `demo` site, and runs the one-shot
bootstrap. A returning start validates and reuses credentials and data, does
not reissue the setup token, skips seed enforcement after setup, and starts the
same service graph.

### PostgreSQL baseline

Initial supported PostgreSQL installations use fresh volumes created by the
project-owned security overlay over the exact official PostgreSQL 18.6
Alpine/musl base pinned in this repository. The overlay installs only the
signed exact OpenSSL package revisions recorded in supply-chain policy. Raw
database volumes are not portable between glibc and musl image families, and
this pre-alpha release has no legacy-installation or cross-family migration
support. Never delete a
non-disposable volume merely to bypass this boundary; a future real migration
requires a separately designed and tested logical process.

## Implemented public surface

| Path | Upstream | Current behavior |
| --- | --- | --- |
| `/` | Web | Accessible pre-alpha deployment-status page. |
| `/health/live`, `/health/ready` | Web | Bounded Web process health only. |
| `/s/demo/` and other resolved paths | Web→Render | Canonical published page HTML from a typed Render projection; only an exact matched site root without a page uses the routing shell, while deeper unknown/unpublished paths return 404. |
| `/preview/{workspace_id}/...` | Web→Render | Mutually exclusive human-session or run-bound signed-browser-header workspace overlay; private/no-store/noindex and never public cacheable. |
| `/api/control/` | Control API | Prefix-stripped health plus authenticated setup/session, site/domain, RBAC catalog, and membership routes; readiness includes one database component. |
| `/api/editor/health/` | Editor API | Exact liveness/readiness aliases. |
| `/api/editor/v1/` | Editor API | Prefix-preserving human Editor API routes. |
| `/api/agent/` | Agent API | Prefix-stripped health, bounded COW routes, capability-authenticated preview-run create/status/private-metadata routes, and retained PRIVATE artifact-byte retrieval; no lifecycle/publication route exists. |
| `/mcp/` | MCP adapter | Prefix-stripped health routes only. |
| `/media/` | Media service | Prefix-stripped health plus authenticated private upload/immutable-byte routes; no direct volume serving. |

Unknown product and API paths return 404. `/internal/` is explicitly rejected
at both supported edges. Render, PostgreSQL, bootstrap,
workers, and browser worker are not routed. Health is process evidence, not
product readiness or publication authority.

NGINX replaces any caller request ID with one bounded 32-character lowercase
hexadecimal ID, passes that value upstream, hides an upstream response field,
and returns exactly one authoritative `X-Request-ID`. The Apache reference uses
the same replace/hide/single-response contract with `mod_unique_id`'s bounded
safe identifier. Both edges set one self-hosted baseline CSP for page, API, and
404 responses: scripts, styles, fonts, connections, and ordinary resources are
limited to self; images additionally permit `data:`; base URIs, objects, and
framing are denied; forms are limited to self. The authenticated Puck editor
route is the one documented style-only exception: it adds
`style-src-attr 'unsafe-inline'` and `style-src-elem 'self' 'unsafe-inline'`
for Puck's runtime UI styling while retaining nonce-bound self-only scripts.
There is no wildcard, external origin, unsafe-eval allowance, reporting
endpoint, or telemetry, and public rendering remains strict.

The current page is server-rendered and has no interactive client behavior.
The strict `script-src 'self'` deliberately does not authorize Next.js inline
hydration data; a future interactive UI must adopt a reviewed nonce or hash
design rather than weaken this baseline.

## Service and image inventory

| Services | Image | Runtime user | Networks | Persistent/private mount |
| --- | --- | --- | --- | --- |
| `secrets-init` | Backend | root with only `CHOWN` and `DAC_READ_SEARCH` added | none | master/isolated secrets plus Media/browser-artifact ownership handoff, read/write |
| `postgres` | PostgreSQL | official entrypoint drops to PostgreSQL user | database | PostgreSQL data; local secrets read-only |
| `bootstrap` | Backend | `10001:10001` | database | local secrets read-only |
| `control-api` | Backend | `10001:10001` | edge, database | isolated Control secret, read-only |
| Control/Agent/Render/MCP HTTP services | Backend | `10001:10001` | exact edge/application/database/browser memberships | no artifact mount; Agent/Render alone mount signing key, Agent alone also mounts worker credential |
| Editor HTTP service | Backend | `10001:10001` | edge/database plus isolated Control/Editor secrets | no media volume |
| Media HTTP service | Backend | `10001:10001` | edge/database plus isolated Media secret | private `media-data` only; initialized `0700` for UID 10001 |
| Three Python workers | Backend | `10001:10001` | database | media volume on media-GC only |
| `browser-worker` | Playwright 1.62.1 / Chromium 152.0.7977.64 | `10001:10001` | browser only | read-only worker credential; writable private browser artifacts |
| `web` | Next.js | `10001:10001` | edge, application, browser | read-only `render-auth-secret` credential |
| `nginx` | NGINX Open Source | `101:101` | edge only | none |

All Compose containers use a read-only root filesystem, drop all default Linux
capabilities, and enable `no-new-privileges`. Narrow tmpfs mounts support
runtime scratch paths. PostgreSQL and the initializer add only the capabilities
needed for initialization and file ownership. There is no source bind mount,
Docker socket, host network, or privileged container.

The browser worker additionally uses the exact Playwright seccomp profile and
adds only `SYS_CHROOT` after dropping all capabilities so Chromium's user-
namespace sandbox can chroot. It is limited to one CPU, 768 MiB memory, 256
PIDs, 128 MiB shm, and a private 64 MiB tmpfs. Weakening to `--no-sandbox`,
seccomp-unconfined, privileged mode, or broad capabilities is unsupported.

The reference edge keeps a 1 MiB global request-body limit. Only `/media/`
receives the bounded 105119744-byte allowance needed for a 100 MiB file plus
256 KiB multipart overhead; Control, Editor, Agent, MCP, Web, and unrelated
paths retain the strict global limit.

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
| `mcr.microsoft.com/playwright:v1.62.1-noble` | `sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e` | Apache-2.0 application package plus inventoried Ubuntu/runtime aggregation | amd64, arm64 |
| `postgres:18.6-alpine3.23` base | `sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f` | PostgreSQL | official multi-platform index; derived by `infra/postgres/Dockerfile` |
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
installed in product images. `@playwright/test==1.62.1` is an Apache-2.0
test runner. The product worker declares exact Apache-2.0
`playwright-core==1.62.1` and bakes only Chromium revision 1234
(`152.0.7977.64`). The exact amd64 Chrome-for-Testing archive SHA-256 is
`8b592f066af71f054aab2cc80fc26f73c775c6d44ebb99d16ade924b24756c2e`.
Firefox, WebKit, the headless-shell duplicate, npm, and Corepack are removed
from the runtime image. The product worker is currently qualified only on
`linux/amd64`; an arm64 browser payload is not claimed.

Updates require a scoped work order, registry/version/license/platform review,
replacement top-level digest, clean builds, the complete packaging test, and
the normal dependency/security gates. Never refresh a digest without reviewing
the readable tag it is meant to freeze.

## Network and credential topology

The named internal networks express current and future connection direction;
network membership does not grant application authority.

Control validates its exact public route-policy declarations at startup. The clean
Compose browser proof reaches all seven catalog and membership routes through NGINX;
each response retains the single edge request ID and private/no-store/noindex policy.
Its two fixed OIDC identities exist only in that disposable test database, have no
usable credential or administrator assignment, and are removed with its volumes.

- `edge`: NGINX, Web, and the five externally routed API processes.
- `application`: Web to Render, plus MCP internal HTTP access.
- `database`: PostgreSQL and only processes whose architecture may later use a
  database. Implemented Control, Editor, Agent, Render, and Media processes open
  only their isolated least-privilege pools; network membership gives every
  other process no credential or database authority.
- `browser`: Agent API, Web, and browser worker. It is internal; Web is the
  worker's only browser origin. The worker has no PostgreSQL, edge, host,
  repository, or Docker-socket path.

The private `local-secrets` volume contains a PostgreSQL administrator password,
ten distinct fixed-login passwords, provisioner/owner DSNs, and nine service
DSNs. Files are mode `0400`; PostgreSQL's password belongs to UID 999
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

The separate `editor-secret` volume contains exactly one `editor-dsn`, copied
byte-for-byte from the generated `slaif_editor_login` locator. Editor API mounts
it read-only at `/run/slaif-editor` and uses the `slaif_editor_runtime` role for
content COW calls. It also mounts `control-secret` only for human session,
site, and permission authorization; the two pools and credentials remain
separate. No Agent capability or publication authority is present.

The separate `render-secret` volume contains exactly one `render-dsn`, and
`render-preview-secret` contains exactly one `preview-dsn`; each is byte-
identical to its fixed generated reader locator. Their directories are mode
`0700`, files are mode `0400`, and both belong to `10001:10001`. Only the
initializer mounts them read/write; Render mounts both read-only. The separate
`render-auth-secret` volume contains exactly one high-entropy `render-token`
file and is mounted read-only to Web and Render. Web reaches Render over the
application network and has no database credential. NGINX, Control, agents,
browser, and workers receive no Render locator or service credential.

The separate `browser-signing-secret` volume contains exactly one generated
`signing-key` file in the fixed `sbk1` format. Its directory is mode `0700` and
file mode `0400`, both owned by `10001:10001`. Initializer alone writes it;
Agent and Render mount it read-only. Web receives a signed run token only in one
incoming request header and forwards it to Render in a different dedicated
server-side header, but Web cannot sign or verify it. Browser worker, NGINX,
Control, Editor, Media, MCP, Scheduler, Reviewer, GC, PostgreSQL, and bootstrap
do not mount the signing volume.

Institutional deployments may replace the generator with externally managed
files that use the same names and fixed principal model. They must preserve
ownership/mode policy and arrange their own one-shot validation. The default
generator is local convenience, not a production secret-management claim.

## Apache HTTP Server alternative

NGINX Open Source is the default edge. `infra/apache` supplies a syntax-tested
Apache HTTP Server 2.4 reference with the same health aliases, preserved
versioned API prefixes, upstreams,
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
