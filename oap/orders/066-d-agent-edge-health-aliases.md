# OAP Work Order — 066-d

## Objective

Amend existing PR #57 to close the remaining deployed Agent edge-routing
failure found in required CI after 066-c: the public health contract requires
`/api/agent/health/live` and `/api/agent/health/ready`, while the prefix-
preserving Agent route is required for `/api/agent/v1/*`. Restore both
contracts with exact, bounded NGINX locations and prove them in the complete
Compose smoke.

## Strategic context and verified current state

- Numeric objective `066` remains unresolved and unmerged; this is the fourth
  same-PR continuation after `066-a`, `066-b`, and `066-c`.
- PR #57 is OPEN on `oap/066-capability-auth`; remote head is implementation
  `d9c08222ecac40b81298deca74fcb6d0e44d51e6`, parent `d32f0d134de29bc04141a9135656437ee8e18896`.
  Remote `main` is `6552ee74e9046bb86e57d68acdef6acd0b0d1c07`.
- Required workflow run `32647260924` completed with all checks passing except
  `Compose and edge packaging`. Its authoritative failure was the CI smoke
  probe `GET /api/agent/health/live` returning 404. The same run passed
  PostgreSQL 14–18, Node contracts, supply-chain evidence, analysis, quality,
  package, policy, Markdown, Mermaid, and dependency checks.
- The local disposable smoke had covered `/api/agent/v1/session` and therefore
  missed the required health alias. The current worktree has an uncommitted
  candidate adding exact health aliases; it is not accepted until this order's
  evidence is complete.

## GitHub objective state

- Numeric objective: `066`; round: `066-d`
- Mode: `AMEND_EXISTING_PR`; existing PR #57 only
- Branch: `oap/066-capability-auth`
- Base: current remote `main`; preserve all prior objective history

## In scope

1. Keep `/api/agent/health/live` and `/api/agent/health/ready` as exact NGINX
   locations proxying only to `/health/live` and `/health/ready` on `agent-api`.
2. Preserve the prefix-preserving `/api/agent/` proxy for Agent application
   routes, including `/api/agent/v1/session`, without weakening the exact health
   aliases or changing Control, Editor, MCP, Media, Preview, or Web routing.
3. Add or adjust only the narrow packaging/edge regression evidence needed to
   make both health aliases and a representative Agent route observable. The
   complete accepted smoke must prove health 200, unauthenticated Agent route
   401, and protected unknown/non-product Agent path 404 as applicable.
4. Run the repository's complete disposable Compose smoke with an accepted
   project name such as `slaif007dci`, plus targeted NGINX/packaging checks;
   preserve cleanup of the exact disposable project and its volumes/networks.

## Explicit non-goals

- Do not create a second PR, change Agent token or capability semantics, alter
  the Agent database authority/grants, or edit the immutable 066-a/066-b/066-c
  order/report content.
- Do not change application routes, health implementation, security headers,
  request-ID behavior, or unrelated proxy locations unless a targeted test
  proves a directly caused regression; escalate any such need.
- Do not broaden `/api/agent/` to arbitrary backend paths, expose health under a
  new public path, add fallback to the Control service/secret, merge PR #57, or
  activate `067-a`.

## Observable acceptance criteria

- `GET /api/agent/health/live` and `GET /api/agent/health/ready` return 200 via
  the public NGINX edge when the Agent service is healthy and retain the normal
  sanitized edge headers.
- `/api/agent/v1/session` reaches the real Agent application route through the
  prefix-preserving proxy and returns its expected unauthenticated 401; no
  Control API route or secret is involved.
- `/api/agent/tools` (or the repository's defined non-product negative route)
  remains 404, proving the fix does not turn the Agent location into an
  unrestricted path passthrough.
- The complete `tools/compose/smoke.sh` passes with the corrected tree,
  including health probes, edge headers, browser/governance contracts,
  secret/authority/failure smoke, and cleanup. The CI-required Compose and edge
  packaging check passes on the pushed implementation head.
- The diff is limited to the exact edge mapping and its regression evidence;
  no prior OAP order/report, unrelated dependency, migration, trust, secret,
  or product scope change appears.

## Required verification

- Run `sudo sh tools/compose/smoke.sh slaif007dci` (or another accepted
  `slaif007*`/`slaif009*`/`slaif010*` disposable name) and preserve the complete
  successful output, including the Agent health and edge-header probes.
- Run targeted packaging/config tests and `git diff --check`; rerun any local
  checks required by the changed files.
- Push the implementation, wait for the complete required GitHub check set, and
  independently verify that no check is failed, cancelled, missing, or pending.
- Independently inspect the final PR diff and confirm the exact health aliases,
  prefix-preserving Agent route, unchanged Control boundary, unique PR/head,
  and clean disposable resources.

## Security, documentation, and report

- Preserve server-owned routing, fail-closed health behavior, sanitized
  responses, request-ID/CSP policy, and the separate Agent/Control secret
  boundary. Do not log or expose DSNs, tokens, SQL, or internal service detail.
- No documentation change is needed unless the final routing truth requires a
  narrowly scoped correction.
- Publish `oap/reports/066-d-agent-edge-health-aliases.md` in a report-only
  commit after implementation. Include the failed 066-c CI evidence, exact
  route mapping, implementation/report SHA ancestry, all acceptance criteria,
  local smoke output, complete GitHub checks, honest limitations, and follow-up.
  Use `Report publication commit: SELF`; the report-only commit's literal
  parent must be the implementation-head SHA.

## Authority and workflow

- Strategic model owns this order, `oap/active`, FIFO, review, acceptance,
  merge, and advancement.
- Coding agent owns only the bounded edge fix, tests, implementation commit,
  push, and immutable 066-d report; it must not edit activated orders/active or
  merge.
- After activation, consume exact control-FIFO `OK`, amend PR #57, publish the
  report-only child, verify remote report state, and send exact response-FIFO
  `OK` only after that verification.
