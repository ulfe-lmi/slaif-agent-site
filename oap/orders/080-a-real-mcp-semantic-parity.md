# OAP Work Order — 080-a (inert until activated)

## Contract and objective

Replace the custom/broken MCP scaffold with a real curated MCP product surface
delegating to the stable Agent REST semantics from 076–079. Links: §§15.6,
25, 51.1. Requires 079.

## Production requirements

- Implement a standards-conformant supported MCP transport and typed
  initialize/tools-list/tools-call behavior. Verify any new runtime dependency,
  permissive license, lock, image and notices; no hosted/account requirement.
- Bind each named tool to one server-defined method/path/schema. Remove caller-
  chosen arbitrary method/path forwarding. MCP has no DB/browser-worker calls
  and forwards the same capability, idempotency key, validation/conflict/error
  semantics to Agent API over fixed internal configuration.
- Cover discovery plus the contractual model/content/page/navigation/redirect/
  component/design/theme/media operations and existing preview-run/artifact
  operations. Objective 087 may later add source/sweep tools.
- Fix production configuration/dependency packaging and expose the endpoint
  through NGINX without placing secrets in URLs/logs/artifacts.

## Acceptance and anti-bypass

A real MCP client through public NGINX lists exact tools, creates/updates/reads/
deletes representative model/content/structure/composition/design state, runs
one preview observation, and observes the same workspace via REST. Tests fail
if the Agent REST operation disappears. Negative cases: unknown tool/argument,
method/path injection, cross-site/resource/scope denial, missing/revoked token,
idempotency mismatch, downstream 4xx fidelity, SSRF/internal host/path attempts,
and no DB authority/import.

No fake tool registry-only proof, direct service/SQL/internal call or bespoke
success response. Run MCP protocol/contract, public integration, production
image/frozen dependency/license, Compose/CI. No freeze/promotion/source import.
Binary done requires working semantic calls, not route presence. Report
`080-a-real-mcp-semantic-parity.md` with SELF; no merge/extra PR.
