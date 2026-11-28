# 080-a — replace the MCP scaffold with one capability-bound discovery tool

## Identity and authority

Objective 080, increment 080/1, round `080-a`, `CREATE_NEW_PR`.
Use a fresh isolated checkout at
`/home/janezp/codex-work/slaif-agent-site-080-a`, branch
`oap/080-a-capability-bound-mcp-discovery`, based on verified GitHub `main`
`f370c647fcca3e4a027b96dbb6d82575d817cbe5`. No existing objective PR,
report, prior signal or remote branch. Create one draft PR against `main`.
This order replaces the inert preplan at the same path. The human approved
only the initial replacement and one read-only discovery tool.

084/1 is merged in PR #124 at that base. The critical closure in PR #120
and the current audit describe a dead MCP scaffold. The old handler has
an undeclared Agent API setting and accepts caller-controlled HTTP
dispatch inputs. Remove it. The authoritative Agent API operation for
this increment is the existing quota-charged
`GET /api/agent/v1/session` with `AgentDiscoveryResponse`. The Agent API
currently accepts that discovery for an otherwise valid capability and
derives site, workspace and permissions from the capability. Preserve
that behavior and its own lifecycle gate.

## One tool and one transport

1. Replace `mcp_adapter/mcp_http.py` and remove the complete old
   `POST /mcp/v1/call` dispatch surface and custom static `/tools`
   catalog. Remove the obsolete versioned MCP health stub and keep the
   shared health routes. Preserve the current public edge routing and
   process boundary. Both existing edge adapters strip the `/mcp/`
   prefix, so the public `POST /mcp/` should reach a single adapter path.
   The removed legacy paths must stay unavailable publicly and on the
   service itself. Keep health and readiness working, including
   `/mcp/health/ready`.
2. Implement the current MCP `2026-07-28` Streamable HTTP JSON mode.
   The modern version uses independently authenticated RPCs. Implement
   `server/discover`, `tools/list`, and `tools/call` only. This scope
   uses the stateless core, the required per-request metadata and
   matching routing headers, supported-version and method error shapes,
   and complete results with server identity metadata. Use the released
   request and response schemas, including `supportedVersions` and
   a capability of `tools: {}` in discovery. Declare exactly one
   read-only tool `site.describe` with an empty, closed arguments schema.
   Use a typed, bounded structured result from the canonical REST
   response and the text content needed for client interoperability.
   Avoid public or reused cache entries. Legacy handshake revisions,
   browser cross-origin access, server subscriptions, SSE and OAuth
   discovery are outside this increment. Document the pre-issued
   product bearer as the supported authorization strategy.
3. Every valid discovery, list and call must validate the current
   product capability through the one fixed Agent API GET and consume
   its existing request quota once. Use only a single well-formed
   product Bearer from the request's Authorization field. Agent API
   remains the authority for authenticity, expiry, revocation, trusted
   site/workspace, effective scopes, constraints and quotas. No
   authorization/session/connection cache. A new request always uses
   its own current capability. Return private, no-store responses.
   Correlate the authorized request with the existing server request
   identity and Agent API status and trusted site/workspace through
   safe application logging. Log fixed operation and status fields.
   Never record the bearer, request bodies, cookies, client RPC IDs,
   source URLs, or raw upstream error output in logs.
4. Make the dispatch structurally fixed to the existing internal Agent
   service's discovery resource. An app request can never choose a
   host, method, path, query, headers other than its validated bearer,
   site, workspace, or downstream body. Reuse an existing suitable
   bounded HTTP boundary or the standard library. Redirect following,
   ambient proxy routing, cookies, and credential reuse are disabled.
   Enforce bounded streamed request input and bounded upstream parsing,
   finite timeout and concurrency, and deterministic safe error
   handling. Validate the MCP metadata, preserve appropriate
   authentication and rate-limit status, and fail closed on invalid
   responses and upstream failure. Unexpected browser Origins are
   refused. This initial native-client-only scope may reject any
   present Origin. Keep all DB and review privileges and credential
   mounts absent from the adapter. Only the Agent API is its product
   data destination.

Use the current published requirements at the time of activation.
[Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
[Core message and metadata rules](https://modelcontextprotocol.io/specification/2026-07-28/basic/index)
[Discovery](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)
[Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)

## Evidence and scope

- Unit and contract coverage proves the one fixed mapping, validation
  and error mapping, bounded timeout and invalid response behavior,
  and former route removal including the public historical spelling.
  Use bounded negative fixtures for caller-provided dispatch fields,
  malformed or mismatched protocol metadata, Origin, unknown tool,
  and unexpected arguments. Those requests must not dispatch a tool.
  Do not construct a vulnerability reproduction of the retired code.
- In the existing public NGINX E2E suite, drive real modern MCP
  discovery, list and call with a client that follows the published
  wire contract. Independently read the same workspace via REST and
  verify the exact returned approved discovery fields, including site,
  workspace and effective scopes. Mint capabilities through real human
  Control. Use a second real capability to prove every request's
  context follows its own authority, and a real revocation to prove
  subsequent calls refuse. Prove absent credential, forbidden argument
  shapes, retired routes and the fixed request quota through the
  normal product path. Verify upstream refusal under bounded fixtures.
  Exercise the named tool rather than accepting registry presence.
  Use an official current client for an independent interchange smoke
  in the disposable test environment where available. Keep the
  committed E2E client and all runtime and workflow dependencies frozen.
- Preserve all 19 E2E projects, six stable profiles, the real
  media approval, 084 overlap proof, retained Heading reads, two
  isolated browser runs and Apache syntax. Test the unchanged
  sole-published-edge and process boundary. Run the full owned frozen
  PG18 integration, unit, repository, quality, package, process,
  Markdown and Node gates, all current PostgreSQL 14–18 jobs, the
  20 required checks, CodeQL, and fresh six-image supply evidence.
  Record exact commands, subjects, and pass/fail/skip/pending results.
- Update scoped API, security, and testing docs. Record the verified
  084/1 merge plus 080/1 in-flight delivery scope in
  `oap/INCREMENTS.md` and `oap/MVP-PROGRESS.md`. Reconcile the MCP audit
  row with regular code and evidence, preserving historical records
  and marking broader semantic parity open. No mutating or browser
  tools, other discovery tools, capability-minting changes, new scopes,
  packages, dependencies, migrations, new infrastructure, hosted
  services, maintenance, or release claims. Credentials remain confined
  to disposable test process environments, never shell arguments,
  logs, reports, browser artifacts or Git. Durable files contain only
  resumable facts. Stop for a genuine contract audit and actual code
  contradiction, required policy weakening, or any need for new human
  credentials, secrets or infrastructure.

## Delivery

Receive the one fresh ASCII `OK` and EOF, resolve the exact active
order, read the coding governance, and verify the named remote base.
Commit the unchanged order and active bytes with the scoped
implementation. Push normally and open one draft PR. Inspect CI and
repair in-scope issues within the round. Keep every pushed commit in
branch ancestry. No force push, strategic merge, second PR, or next
round activation.

Publish exactly one `oap/reports/080-a-real-mcp-semantic-parity.md`
with exact authoritative PR/branch/base, implementation and tests,
accepted scope, limitations and review evidence. Put the following
metadata on standalone lines with the literal forty-hex SHA filled in.

```text
Implementation head SHA: <forty-lowercase-hex SHA>
Report publication commit: SELF
```

Lint the complete temporary report using the exact repository config.
After the implementation head and PR are remote, publish the same
report bytes to the canonical and execution copies. The report-only
remote commit has the claimed implementation head as its sole parent.
Verify that exact remote PR head, send exact `OK` once to the verified
response FIFO with EOF, and stop. ROOT alone reviews, accepts and merges.
