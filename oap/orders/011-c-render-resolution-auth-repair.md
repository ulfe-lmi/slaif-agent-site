# OAP Work Order — 011-c

## Objective and PR state

Amend objective-011 PR #23 to repair the 011-b session/CSRF boundary and its
immutable-order Markdown gate, then add the least-privilege, read-only Render
API boundary that resolves normalized host/path input to a server-owned active
`SiteContext`. Do not add a demo seed, public web page, NGINX/Apache route, or
Compose secret/runtime wiring; those remain the final bounded 011-d round.

- Numeric objective: `011`; round: `011-c`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#23](https://github.com/ulfe-lmi/slaif-agent-site/pull/23)
- Base/head: `main` / `oap/011-sites-trusted-resolution`
- Required starting remote head:
  `8bf66f832dd83b7eb578904b483e53b8702d0229`
- 011-b implementation parent:
  `da8cfe5bf9663d3a7acc4172f60436e5e0854a7c`
- Verified state: open, ready/non-draft, mergeable, no reviews/threads; report
  commit is report-only with the correct parent. Current-head CI is final at
  19 successful / one failed / zero pending. Only Markdown failed, at immutable
  `oap/orders/011-b-platform-admin-site-http.md:25:1` (`MD018`) because the
  strategic-authored prose line begins the literal text `#23,`.

Fetch and verify this exact PR/head. Amend only it; keep it ready. Never create
another PR, merge, close, auto-merge, or rerun a workflow.

## Strategic findings and architecture boundary

011-b correctly added nine Platform Administrator routes, strict cookie/CSRF
input parsing, active administrator authorization, typed site/domain operations,
and transactional active rechecks. However, its state-changing helper first
calls safe `authenticate()`, then validates CSRF, then calls
`authenticate_state_changing()`. A denied request can therefore touch/extend a
valid human session before CSRF succeeds and a successful request finalizes the
session twice. This must be one classified, atomic credential decision with no
session-state change on denial.

The Render process is internal and currently health-only. It must gain only the
`slaif_public_reader` credential and read-only site resolver authority. It must
not import/use the Control database adapter, acquire site-management functions,
trust a caller-provided site UUID, infer membership, or become edge-accessible.
Host/path resolution selects public routing context only and grants no human,
preview, workspace, capability, or publication authority.

## Bounded scope

```text
.markdownlint-cli2.yaml
services/backend/src/slaif_agent_site/identity/sessions.py
services/backend/src/slaif_agent_site/control_api/auth_http.py
services/backend/src/slaif_agent_site/render_api/**
services/backend/src/slaif_agent_site/sites/{models,resolver,service}.py
services/backend/src/slaif_agent_site/db/alembic/versions/013_001_site_foundation.py
services/backend/src/slaif_agent_site/db/privileges.py
services/backend/tests/unit/{test_sessions,test_render_*,test_health_apps}.py
services/backend/tests/integration/{test_human_session,test_control_auth_http_integration,test_site_control_http_integration,test_render_site_resolution}.py
services/backend/tests/integration/{test_database_bootstrap,test_control_database_integration}.py
.github/workflows/ci.yml
tools/check_repository.py
tests/repository/test_repository_policy.py
docs/{API,SITES,DATABASE_ROLES,SECURITY,CONFIGURATION,OPERATIONS}.md
README.md
oap/active
oap/orders/011-c-render-resolution-auth-repair.md
oap/reports/011-c-render-resolution-auth-repair.md
```

Use the minimum coherent subset. No web/Next.js, NGINX/Apache, Compose, secret
initializer/volumes, bootstrap/demo seed, dependency/lock/image, membership/
RBAC, workspace/capability, content/COW, media, browser, or publication change.
Do not edit either activated 011-a/011-b order or any published report.

## Requirements

### 1. Resolve the immutable Markdown artifact without weakening general lint

The activated 011-b order is immutable and must remain byte-identical with SHA-
256 `9af8550e4731939c9d1f60d93a1a62bbf5d967f3833bae6133595e73aac4cea8`.
Do not change, rename, regenerate, or delete it; do not disable MD018 globally;
do not remove OAP/docs from Markdown CI.

Add the narrowest documented repository exception supported by the existing
Markdownlint tool: ignore exactly that one immutable file, analogous to the
existing named immutable 010-i report exception. Add/extend repository-policy
tests so the ignore is path-exact, explained, and cannot become a glob,
directory, current report, or general OAP exclusion. Prove another temporary or
fixture Markdown file with the same MD018 defect still fails. The new 011-c
order/report and every non-exempt Markdown file remain linted.

### 2. One atomic state-changing session/CSRF decision

Refactor the internal human-session service and Control HTTP helper so a
state-changing request performs exactly one persistence finalization after both
the session secret and its bound CSRF secret are proven. It must not call safe
`authenticate()` first and must not update `last_seen_at`, `recent_auth_at`,
expiry, revocation, or any session row on malformed/missing/wrong CSRF, invalid/
expired/revoked session, duplicate/alternate cookie, or duplicate header.

Use internal typed/classified failure semantics sufficient for HTTP to preserve:

```text
missing/malformed/unknown/wrong/expired/revoked session -> 401
valid current session but missing/malformed/mismatched CSRF -> 403
database/pool/timeout failure -> 503
```

Do not expose digest-comparison results, token existence, user/administrator
state, SQL/driver/locator details, or a new public credential oracle. Preserve
constant-time secret comparison, cancellation, transaction rollback, touch
interval/recent-auth behavior, and all setup/login/session/logout contracts.
Successful state-changing authentication returns one current immutable context
and touches/finalizes no more than once. Safe GET authentication remains one
safe finalization. Logout may retain its purpose-specific revoke flow.

Add real-PostgreSQL regression evidence that snapshots the session row before
each denial, proves it is byte/column unchanged afterward, and proves a success
advances only the expected fields once. Add a focused fake-adapter/call-count
test proving the HTTP helper does not invoke both authentication methods. Re-run
all existing human-session and Control/site HTTP tests.

### 3. Isolated public-reader Render database boundary

Implement a typed Render-owned database configuration/adapter/application
lifespan modeled on the established fail-closed service patterns but fixed to:

```text
login: slaif_public_login
privilege role: slaif_public_reader
default locator file: /run/slaif-render/render-dsn
application name: slaif-render-api
```

Test mode may accept an explicitly bounded loopback/test DSN. Development and
production require the fixed absolute mode-0400 file owned by the process UID;
production requires the existing verified TLS locator policy. Pool initialization
must prove database, login/current-user, and exactly one expected role; errors,
repr, logs, health, and CLI must never disclose the locator. Readiness must fail
closed on pool/config/role/migration/function mismatch and recover only through
normal restart/startup. Shutdown/cancellation must be bounded as for Control.

Do not wire this file or credential into Compose in this round. The `--check`
command must validate the static application/config contract without opening a
connection or requiring a mounted file.

### 4. Resolver-only persistence and domain service

Grant `slaif_public_reader` exact EXECUTE only on the minimum existing active
hostname/path and local-key resolver functions (or equivalent dedicated read-
only wrappers). It receives no site create/get/list/update/archive/domain-list/
domain-mutation/administrator function, no Control relation access, and no
runtime/reviewer authority. Other roles must not gain new authority. Amend the
still-unmerged `013_001` upgrade/downgrade and exact privilege inventories.

Extract or add a narrow resolver class usable by Render that exposes only:

```text
resolve(authority: str, request_path: str) -> immutable active SiteContext
```

Reuse exactly the 011-a normalization, reserved namespaces, longest boundary
match, ambiguity handling, archive filtering, localhost `/s/<key>` convention,
constant denial, acquisition timeout, cancellation, and safe error mapping. Do
not instantiate the broader site-management service over a public-reader pool.
No method accepts a site/domain UUID or authorization claim.

### 5. Internal Render resolution endpoint

Expose one and only one non-health route on Render:

```text
POST /internal/render/v1/site-context
```

The frozen extra-forbid request contains only `authority` and `path`; the
response contains only trusted active routing facts required for later public
rendering: site UUID/key, canonical revision, default locale, and matched
hostname/path prefix. Status is implicit ACTIVE and grants nothing. Invalid,
reserved, ambiguous, unknown, or archived input returns the same stable 404;
resolver conflict returns 409; persistence/configuration failure returns 503.
Responses and errors are `private, no-store` and `noindex`, with one request ID.

The endpoint remains on the internal Render network and is not routed by NGINX,
Apache, Web, Control, Agent, Editor, or MCP in this round. It must not honor
forwarded `site_id`, membership, workspace, preview, capability, or user headers
and must not expose a public route. Add route-inventory/edge-negative tests.

### 6. Executable evidence and documentation

Using real PostgreSQL and the actual public-reader login, prove two sites with
same-host distinct prefixes plus local `/s/<key>` resolve correctly; case/IDNA/
port/trailing slash normalize; longest segment boundary wins; `/site` differs
from `/site-other`; unknown/reserved/encoded/dot/backslash/forged ID inputs and
archived site return constant 404. Prove public reader cannot inspect site
relations or call any management/administrator function, and Control/other roles
retain their exact prior matrix. Exercise configuration identity mismatch,
missing/unsafe locator file, DB unavailable, cancellation, startup/readiness,
shutdown, and endpoint error redaction.

Add the Render integration suite to PostgreSQL 14–18 while preserving exactly
20 check names and all prior tests. Document the internal-only endpoint,
public-reader authority, config variable/file, normalized routing semantics,
and explicit absence of public rendering, edge wiring, demo seed, UI,
membership, content, workspaces, and publication.

## Acceptance criteria

1. State-changing site requests make one bound session+CSRF authentication
   decision; every denied attempt leaves the session row unchanged and maps to
   the correct stable 401/403/503 class.
2. The immutable 011-b order hash is unchanged; only its exact path is narrowly
   exempted, while MD018 remains enforced everywhere else and Markdown is green.
3. Render runs with only `slaif_public_reader`, exposes exactly one internal
   resolver route, and cannot call/read any Control management surface.
4. Two-site/longest-prefix/local/archive/reserved/cross-input tests return only
   immutable active context and never authorization.
5. No seed/web/edge/Compose/dependency/adjacent scope enters; existing auth/site/
   packaging behavior remains green.
6. PR #23 alone remains ready and is amended with a correct report-only head;
   current-head CI reaches 20/20 success with no rerun/new PR/merge/auto-merge.

## Verification, autonomy, and report

Target 50 minutes; hard stop 75 minutes. Inspect before editing. Run focused
unit plus real-PostgreSQL session/Control/Render/site suites; Ruff/format/mypy/
compile; migration upgrade/downgrade/rebuild and exact grant/function inventory;
repository/packaging-policy; full Markdownlint proving the exact exception;
changed docs/order/report lint; `git diff --check`; conflict-marker, immutable-
hash, route, and secret/locator scans. Do not run local Node, Compose,
Playwright/browser, images, or broad SBOM. GitHub supplies those unchanged jobs.
No blind reruns or test weakening. Fix diagnosed local defects without an
arbitrary attempt cap; at the hard boundary publish honest pushed `PARTIAL`.

Push one coherent implementation generation and inspect complete CI. At most
one corrective code generation for a concrete clean-environment/PostgreSQL-
version/check defect; never workflow-rerun. Routine VM setup belongs to the
coding agent with passwordless sudo; access no production system or secret.

Preserve prior transcript bytes; commit this order and `oap/active`
byte-identically. Keep PR #23 ready, push only its branch, never merge. Atomically
publish exactly:

```text
oap/reports/011-c-render-resolution-auth-repair.md
```

The last pushed report-only commit must parent the literal implementation SHA
and say `Report publication commit: SELF`. Report PR/head/draft state; exact
Markdown exception/hash proof; session call/row-state/status evidence; Render
config/pool/route/grant and two-site inventories; exact local commands/results;
five-version and 20-check state; corrections/failures/skips; docs/security/
scope/dependencies; hashes; and explicit no-new-PR/no-rerun/no-merge state.
Signal exact FIFO `OK` only after report and claimed remote state exist.
