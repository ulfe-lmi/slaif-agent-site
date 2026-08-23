# OAP Work Order — 066-c

## Objective

Amend existing PR #57 to close the remaining Agent API authority gap found in
strategic review: `066-b` wires a factory/lifespan adapter, but that adapter
constructs `ControlDatabase` with the `slaif_control_login` / Control DSN
authority, while the normative process map assigns Agent API the distinct
`slaif_agent_runtime` authority. Compose mounts the Control DSN only to
Control API. In addition, `slaif_agent_site.agent_api.__main__` still calls the
generic health-only `run_http_process()` and therefore does not serve the
factory-created Agent routes or run their capability-database lifespan.

Make the production Agent API use its own least-privilege runtime credential
and the real Agent application factory, without giving agent-authenticated
callers any Control API authority.

## Strategic context and verified current state

- Numeric objective `066` remains unresolved and unmerged; this is the third
  same-PR continuation after `066-a` and `066-b`.
- PR #57 is OPEN on `oap/066-capability-auth`; report-head is `d32f0d1`, whose
  parent is implementation `0d75fe2`; the report and prior orders are
  immutable. Remote `main` is `6552ee7`.
- `066-b`'s focused PostgreSQL/ASGI test proves the factory only when supplied
  with test `ControlDatabaseSettings`; it does not prove production Agent
  identity or deployment secret wiring.
- `agent_api` authority is `AGENT_COW_RUNTIME` / `slaif_agent_runtime` in
  `authority.py`; `ControlDatabaseSettings` is fixed to
  `slaif_control_login` / `slaif_control` outside test mode.
- `compose.yaml` gives `control-api` the `/run/slaif-control/control-dsn`
  volume and does not give that volume to `agent-api`.
- `agent_api.__main__` invokes `run_http_process(ProcessKind.AGENT_API)`, the
  health-only shared runner, rather than constructing `agent_api.create_app()`.

## GitHub objective state

- Numeric objective: `066`; round: `066-c`
- Mode: `AMEND_EXISTING_PR`; existing PR #57 only
- Branch: `oap/066-capability-auth`
- Base: current remote `main`; preserve all prior objective history

## In scope

1. Add a typed, fail-closed Agent runtime database configuration/lifecycle
   seam with the fixed `slaif_agent_login` / `slaif_agent_runtime` identity,
   a separately mounted Agent DSN/secret path, and production-safe locator
   validation analogous to the existing process-owned database settings.
2. Refactor or replace the capability-authentication adapter so the Agent API
   uses only that Agent runtime authority. It must not instantiate or receive
   `ControlDatabaseSettings`, `ControlDatabase`, the Control DSN, or the
   `slaif_control` login in production. Keep capability authentication bounded
   to the existing semantic lookup and immutable context.
3. Reconcile database grants and effective-privilege validation so the Agent
   runtime has exactly the capability-assert/read authority required by the
   normative architecture, plus its already-authorized Agent COW/audit
   surface, and no Control API user/session/site/membership/mint/revoke/
   setup/function authority. Do not silently broaden `slaif_control`.
4. Wire disposable/development deployment configuration and `compose.yaml`
   so secret initialization creates the Agent DSN, only `agent-api` mounts the
   Agent credential, only `control-api` mounts the Control credential, and
   health/readiness remains sanitized and fail-closed.
5. Change the Agent process entrypoint to construct and serve the real
   `agent_api.create_app()` with its lifespan, settings, routers, capability
   authentication, and readiness. Preserve the existing `--check` contract
   without opening a database during check mode.
6. Replace the current test fixture's Control-role assumption with production
   factory/lifecycle evidence using the Agent runtime identity (or a narrowly
   equivalent test fixture that proves the identity/privilege boundary). Cover
   valid, malformed, unknown, wrong-secret, revoked, expired, unavailable,
   wrong-role, and missing-credential fail-closed cases; prove the served
   process uses the real factory and never substitutes `app.state.database`.

## Explicit non-goals

- Do not create a second PR, change token format/digest semantics, or edit the
  immutable `066-a`/`066-b` orders or reports.
- Do not add agent content mutations, COW write operations, publication,
  review/promotion, MCP/browser-worker behavior, user management, capability
  minting/revocation, or unrelated process redesign.
- Do not grant the Agent runtime Control API functions, broad Control tables,
  raw SQL/DDL, schema migration, or infrastructure authority. No request,
  header, path, body, or agent-supplied value may select identity or workspace.
- Do not use the Control secret as an Agent fallback, duplicate a credential
  into both services, log DSNs/tokens, or weaken production TLS/locator rules.
- Do not merge PR #57 or activate `067-a`; only strategic review may do so.

## Observable acceptance criteria

- A normal production-style `python -m slaif_agent_site.agent_api` startup
  constructs the full Agent app, owns its capability dependency, and serves
  `/health/live`, `/health/ready`, and Agent routes through the same factory /
  lifespan used by the integration test.
- The Agent process connects successfully with the fixed Agent login and
  privilege role, and its control lookup works for a valid seeded capability;
  the Control login/DSN is absent from Agent configuration and mounts.
- Effective privilege evidence proves Agent runtime access is limited to the
  bounded capability assertion and existing Agent COW/audit authority; it
  cannot call Control API mutation/session/setup/mint/revoke functions or
  write Control tables. Control API retains its own independent authority.
- Valid credentials return the correct immutable site/workspace context;
  malformed, unknown, wrong-secret, revoked, and expired credentials return
  401; unavailable/misconfigured/missing/wrong-identity control state returns
  sanitized 503 or startup failure as appropriate, never leaking tokens,
  DSNs, SQL, driver, or filesystem details.
- The integration and entrypoint tests exercise the actual factory/lifespan,
  Agent-role identity, secret mount/config boundary, and no post-construction
  state replacement.
- The diff remains limited to Agent runtime configuration/adapter/entrypoint,
  exact grants and their validator, deployment secret wiring, tests, and this
  OAP evidence. No unrelated dependency, migration, trust, or product scope
  change appears.

## Required verification

- Run focused Agent factory/entrypoint/identity/privilege tests with
  disposable PostgreSQL, then the full backend unit/repository and integration
  suites.
- Run ruff, formatting, mypy, package build, repository policy, Mermaid,
  Markdown, frozen Node lint/format/typecheck/test/build/license, and all
  package-aware process checks.
- Run the complete Compose/edge deployment smoke and verify Agent/Control
  secret mounts and health behavior independently.
- Independently inspect final authority descriptors, settings validators,
  effective grants, entrypoint/lifespan, response sanitization, and the final
  diff for Control-role leakage or fallback paths.

## Security, documentation, and report

- Preserve fail-closed server-owned site/workspace context and constant-safe
  token comparison. Never return or log token plaintext/digest, DSN, SQL,
  driver, role locator, or secret path details.
- Update configuration/deployment documentation only where the new Agent
  credential boundary is required for truth; do not broaden prose scope.
- Publish `oap/reports/066-c-agent-runtime-authority-and-entrypoint.md` in a
  report-only commit after implementation. Include exact PR/branch/SHA
  ancestry, every acceptance criterion, identity/grant evidence, all local and
  GitHub checks, prior 066-a/066-b limitations, honest skips/limitations, and
  follow-up. Report syntax must use `Report publication commit: SELF` with the
  implementation SHA as its literal parent.

## Authority and workflow

- Strategic model owns this order, `oap/active`, FIFO, review, acceptance,
  merge, and advancement.
- Coding agent owns only bounded implementation, tests, commits, push, and the
  immutable `066-c` report; it must not edit activated orders/active or merge.
- After activation, consume exact control-FIFO `OK`, amend PR #57, publish the
  report-only child, verify remote report state, and send exact response-FIFO
  `OK` only after that verification.
