# OAP Work Order — 011-d

## Objective and final-round intent

Complete objective 011 on existing PR #23: use PostgreSQL time for the remaining
session/CSRF classification decision, wire Render's fixed public-reader locator
through an isolated Compose secret, seed one explicit fresh-demo site safely,
and prove real multi-site host/path/local routing through NGINX and the Web→Render
boundary. This is the planned final round for sites/trusted resolution; repair
any concrete in-scope defect within the bounded turn rather than deferring known
acceptance work.

- Numeric objective: `011`; round: `011-d`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#23](https://github.com/ulfe-lmi/slaif-agent-site/pull/23)
- Base/head: `main` / `oap/011-sites-trusted-resolution`
- Required starting remote head:
  `a4d65b343ac802975d03478f1101828c28f1204f`
- 011-c implementation head:
  `703bcbfcfb42b5c304c63e61e5bc06df22ec4a02`
- Verified state: open, ready/non-draft, mergeable, no reviews/threads; report-
  only head has the correct parent; current-head CI is 20/20 successful with
  zero pending/failed/cancelled/missing checks.

Fetch and verify the exact open PR/branch/head. Amend only PR #23, keep it ready,
and never create another PR, merge, close, auto-merge, or workflow-rerun.

## Current architecture and non-goals

011-a–c provide normalized site/domain persistence, trusted `SiteContext`,
Platform Administrator HTTP, atomic session+CSRF proof, resolver-only Render,
and exact public-reader functions. Render is intentionally health-only in the
current development Compose because 011-c was forbidden to distribute its
locator. Once this round mounts the locator, remove that temporary fallback:
missing/unsafe/wrong Render credentials must make readiness fail closed.

This round demonstrates routing identity, not content/Puck/publication. The
public result is a small trusted server-rendered active-site context shell. It
must not invent content storage, direct canonical editing, membership/RBAC,
workspaces/capabilities, preview/review, media, browser tools, DNS automation,
or production-ready/hostile-tenancy claims. Site-management UI is objective 013;
do not add it here.

## Bounded scope

```text
services/backend/src/slaif_agent_site/identity/sessions.py
services/backend/src/slaif_agent_site/bootstrap/{config,service,__main__}.py
services/backend/src/slaif_agent_site/render_api/{__main__,config,database}.py
services/backend/tests/unit/{test_sessions,test_bootstrap_*,test_render_*}.py
services/backend/tests/integration/{test_human_session,test_sites,test_render_site_resolution,test_demo_seed}.py
tools/local_secrets/initialize.py
tests/packaging/{test_local_secrets,test_compose_policy,test_compose_smoke_contract,test_edge_contract}.py
tools/compose/{verify,smoke,e2e}.py|.sh
compose.yaml
apps/web/app/** and apps/web/src/sites/**
apps/web/tests/**
tests/e2e/{setup,support}.ts and playwright.config.ts only if required
infra/nginx/** and infra/apache/** only for verified routing/header parity
.github/workflows/ci.yml only to include a focused new test in existing jobs
docs/{API,SITES,CONFIGURATION,DEPLOYMENT,OPERATIONS,SECURITY,TESTING}.md
README.md
oap/active
oap/orders/011-d-demo-edge-compose-proof.md
oap/reports/011-d-demo-edge-compose-proof.md
```

Use the minimum coherent subset. No dependency/lock/image/base-image version,
database role name, new host port, external service, telemetry, content/COW,
membership, workspace/capability, Puck, browser-worker authority, or publication
change. Preserve every activated order and published report byte-identically.

## Requirements

### 1. Preserve database-clock session semantics

011-c correctly eliminated the double finalization, but its wrong-CSRF path uses
`datetime.now(UTC)` to distinguish an expired current session. Replace that
application-clock comparison with PostgreSQL `CURRENT_TIMESTAMP` obtained in
the same inspection transaction/statement as the locked session row. Do not
rewrite already-merged migration 010; use a bounded query/wrapper or amend the
unmerged 013 revision only if truly necessary.

Valid session + bad CSRF remains 403; expired/revoked/idle/disabled session is
401 even when CSRF is bad; persistence failure is 503. No denial mutates the
session row, and success still finalizes exactly once. Add regression evidence
with application time skewed far ahead and behind database time, proving status
classification depends only on returned database time and retains constant-time
secret comparisons, cancellation, rollback, and redaction.

### 2. Isolate and mount the Render locator

Generalize the existing one-shot local-secret initializer narrowly so it creates
and validates a second isolated directory containing exactly one file:

```text
/run/slaif-render/render-dsn
```

Its value must byte-match the already generated `service-public-dsn`; directory
mode/owner and file mode/owner follow the established non-root private contract
(directory accessible only by application UID; file regular, no symlink, mode
0400, owned by application UID). The Render volume must contain no Control,
owner, provisioner, PostgreSQL, runtime, reviewer, or other login material. The
Control volume and master local-secrets behavior remain unchanged and idempotent.

Add a named `render-secret` volume. Mount it read-only only in `render-api`, set
the fixed `SLAIF_RENDER_*` identity/mode/file variables, and do not mount master
`local-secrets` there. Web, NGINX, Control, agents, browser, and workers receive
no Render DB credential. Static and running Compose verification must prove the
exact mount/network/UID/file count/mode/owner/value and cross-UID denial.

Remove 011-c's development health-only locator fallback. Render always starts
its configured database-aware app; missing, empty, symlinked, broad-mode,
wrong-owner, wrong-login, wrong-role, or unavailable locator makes Render
readiness fail and prevents Web/NGINX readiness. `--check` remains connection-
free and does not read the file.

### 3. Explicit, fresh-install-only demo seed

Add typed `SLAIF_BOOTSTRAP_DEMO_SEED`, default `false`. It may be `true` only
with the existing local secret manifest and a loopback `/setup` URL; invalid
combinations fail with the constant bootstrap configuration error. Set it true
only in reference Compose. No general production default or hidden seed occurs.

During one-shot Compose bootstrap, after migrations/privileges validate and
before setup-token output, transactionally ensure exactly one initial active
site when the installation is still uninitialized and otherwise empty:

```text
site_key=demo
display_name=SLAIF Demo Site
default_locale=en
```

Use server-generated identity/default revisions/catalog version and the trusted
semantic/owner boundary; no fixed UUID or direct client authority. The local
`/s/demo/` mapping is implicit and needs no fake DNS/domain row. Repeated
bootstrap before setup is idempotent only for the exact matching active seed.
Unexpected other/mismatched/archived pre-setup site state fails closed rather
than overwriting. Once installation setup is complete, later bootstrap skips
seed enforcement entirely so administrators may update/archive the demo site.
Disabled seeding creates nothing. Failure rolls back site state and prevents
setup/readiness success.

Prove clean, disabled, idempotent-uninitialized, mismatch, rollback, concurrent,
and post-initialization cases using real PostgreSQL. The demo seed never creates
an administrator, domain, membership, content, capability, or published data.

### 4. Trusted Web→Render public routing shell

Web remains DB-credential-free. Add a server-only, fixed internal Render client
that calls only `http://render-api:8000/internal/render/v1/site-context`, with a
short timeout, no cookies/authorization/forwarded user headers, no client-
derived URL, and `no-store`. It sends only the normalized routing inputs required
by Render. Do not expose the internal endpoint in browser JavaScript or proxy it
through a public API.

Preserve the existing localhost root landing and the specific `/setup`, `/login`,
and `/admin` pages. Add the smallest root optional-catch-all or equivalent
server route so other requests derive authority/path from the actual server
request and render a trusted accessible shell only after Render returns an
active context. The shell may show product name, site key, canonical revision,
locale, and matched host/prefix; it must not claim or fabricate content. It must
have a visible H1, usable keyboard/focus/viewport layout, no horizontal overflow,
and no credential/private data.

Required behavior:

- `localhost /s/demo/` resolves the controlled seed;
- a second API-created site resolves through local `/s/<key>/`;
- a persisted custom hostname/path prefix resolves through the same shell;
- longest segment boundary is preserved;
- unknown/archived/reserved/ambiguous/bad Host/path returns 404, never a site
  guessed from URL slug or forwarded/body/header site ID;
- Render unavailable/misconfigured fails closed and does not show a site shell;
- unknown non-loopback Host does not receive the localhost product landing; and
- direct `/internal/render/v1/site-context` remains unreachable through either
  NGINX or Apache.

Do not use `X-Forwarded-Host`, query/body site IDs, or a user-controlled internal
base URL as authority. NGINX/Apache may forward ordinary Host/path/request ID,
but all product resolution remains in Render. No product semantics move into
edge configuration.

### 5. Clean Compose and multi-site end-to-end proof

Extend the one-command clean smoke and existing six-project Playwright flow
without adding a hosted secret or host port:

1. clean Compose builds and becomes healthy with only NGINX at
   `127.0.0.1:8080`;
2. before human setup, `/s/demo/` renders through NGINX on desktop and 320px
   phone while root setup remains available;
3. setup creates the Platform Administrator through the existing browser flow;
4. that authenticated browser/API session, with real bound CSRF, creates a
   second site plus domain mapping through the nine Control routes;
5. local paths for both sites and custom Host+path return the correct distinct
   site keys; wrong Host, prefix-boundary substitution, forged site headers,
   archived/unknown route, and public internal-Render path fail closed;
6. stop/start preserves secrets and sites, does not reissue the setup token, and
   does not reseed/overwrite initialized state; and
7. Render locator removal/corruption makes Render/Web/NGINX not ready while no
   credential/DSN appears in image history, rendered Compose, logs, HTML, or
   Playwright artifacts.

Exercise NGINX as authoritative E2E edge and retain Apache configuration/build/
syntax plus equivalent static/runtime proxy semantics. Keep all six stable
Playwright project names and current auth coverage. Tests must not depend on
external DNS; use an explicit Host header for custom-domain proof.

The deliberate broken-bootstrap negative smoke currently floods successful CI
with repeated `service "bootstrap" didn't complete successfully` lines. Capture
that expected command output, verify the failure is specifically the safe
bootstrap gate and NGINX stayed down, then print one clear marker such as
`negative-bootstrap: correctly blocked`. Preserve useful diagnostics on an
unexpected result without leaking locators. Do not weaken or remove the negative
test.

### 6. Documentation and claim discipline

Document the exact demo flag/fresh-only behavior, isolated Render locator,
startup/readiness failure modes, internal Web→Render flow, public local/custom-
host examples, API-created second-site demonstration, negative smoke marker,
and cleanup/restart commands. State that the shell proves routing context only;
content models, actual site content, memberships/RBAC, editor/Puck, workspaces,
agent capabilities, review/publication, DNS automation, and hostile tenancy are
not implemented. Keep the canonical product/security wording and README logo
unchanged.

## Acceptance criteria

1. Session/CSRF classification uses database time under application clock skew,
   with one finalization on success and no row mutation on denial.
2. Render always uses only its exact isolated public-reader locator in Compose;
   missing/wrong secret fails Render→Web→NGINX readiness closed.
3. Explicit fresh-demo seeding is safe, idempotent before setup, skipped after
   initialization, and creates only the one expected site.
4. Real NGINX E2E proves demo, second-site local path, custom Host/prefix,
   boundaries, negative routes, restart persistence, and six browser projects;
   only NGINX publishes 8080 and internal Render is never public.
5. Expected broken-bootstrap output is concise while the fail-closed assertion
   remains executable; no credential appears in config/history/log/HTML/output.
6. No adjacent product/dependency scope enters; docs remain honest; PR #23 alone
   is ready with a correct report-only head and current CI 20/20 green, without
   workflow rerun/new PR/merge/auto-merge.

## Verification, autonomy, and report

Target 65 minutes; hard stop 90 minutes. Front-load static config/unit/DB/Web
tests and build before one clean local Compose generation. One additional clean
Compose generation is allowed only after a concrete diagnosed fix; never loop or
rerun unchanged. Run affected Ruff/format/mypy/compile, real PostgreSQL session/
seed/resolver/API tests, full Node lint/format/type/test/build, packaging/repo/
edge/secret checks, Markdown/Mermaid if changed, Apache/NGINX syntax, secret/
locator scans, `git diff --check`, and exact transcript/hash checks. Run the
ordered six-project Compose E2E. Do not run unrelated browser-worker/source/
image experiments or broad manual SBOM beyond established CI.

Push one coherent initial implementation generation after local green and
inspect full GitHub CI. One corrective code generation is permitted only for a
specific clean-run/platform/check failure; no workflow rerun. No blind retries,
test weakening, fallback readiness, or hiding failures. Use passwordless sudo
inside the disposable VM for routine tooling; access no production credential,
system, or data. At the hard boundary publish honest pushed `PARTIAL` evidence.

Preserve all prior orders/reports; commit this order and `oap/active`
byte-identically. Keep PR #23 ready and never merge. Atomically publish exactly:

```text
oap/reports/011-d-demo-edge-compose-proof.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
PR/head/draft state; database-clock proof; secret file/volume/mount/UID/mode and
denial inventory; seed transaction/state matrix; Web/Render/edge routing matrix;
exact Compose/Playwright six-project/restart/failure/log results and timings;
local commands; five-version/20-check state; corrections/skips/failures; docs/
scope/dependencies/security; hashes; and explicit no-new-PR/no-rerun/no-merge.
Signal exact FIFO `OK` only after report and claimed remote state exist.
