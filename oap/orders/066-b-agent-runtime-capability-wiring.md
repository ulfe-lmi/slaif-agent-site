# OAP Work Order — 066-b

## Objective

Amend PR #57 to wire capability authentication through the real Agent API
application factory and lifecycle. The valid/negative capability evidence in
`066-a` currently replaces `app.state.database` with a test-only
`ControlDatabase`; production `create_agent_app()` still installs
`AgentDatabase`, which has no `authenticate_agent_capability()` method. Close
that runtime gap without broadening agent authority.

## Strategic context and verified current state

- Objective `066-a` remains unresolved and unmerged on PR #57.
- PR #57 implementation head is `25317bf`; report commit `039583c` is its
  report-only child. The report and implementation are immutable; this round
  amends the same objective branch/PR and must not create a second PR.
- Remote `main` is `6552ee7`; the strategic selector is being advanced from
  `066-a` to this continuation only after the strategic review found the
  runtime-wiring gap.
- `agent_api.create_app()` installs the bounded `AgentDatabase` in
  `app.state.database`.
- `ControlDatabase.authenticate_agent_capability()` exists and the prior test
  passes only after manually assigning a `ControlDatabase` to
  `app.state.database`; that is not production process evidence.

## GitHub objective state

- Numeric objective: `066`; round: `066-b`
- Mode: `AMEND_EXISTING_PR`; existing PR #57 only
- Branch: `oap/066-capability-auth`
- Base: current remote `main`; preserve the existing implementation/report
  history and amend the same objective branch.

## In scope

1. Wire a real, server-owned capability-authentication dependency into the
   Agent API application factory and lifecycle so a normally constructed Agent
   API can authenticate against the existing control capability boundary.
2. Preserve the least-privilege design: capability validation may read only
   the required existing control relations through the bounded service; the
   agent must not gain raw SQL, user-management, capability-minting/revocation,
   schema-migration, publication, or infrastructure authority.
3. Keep the existing 401 behavior for malformed/unknown/wrong/revoked/expired
   credentials and sanitized 503 behavior for unavailable control state.
4. Replace the test-only `app.state.database` substitution with evidence that
   uses the same production factory/lifecycle wiring, allowing only ordinary
   configuration or test-fixture injection at the documented ownership seam.
5. Add or update regression coverage proving the actual Agent API factory
   exposes the authentication method and the valid/negative/503 paths still
   pass without post-construction state replacement.

## Explicit non-goals

- Do not add a second PR, change the token format, add a physical migration,
  alter capability minting/revocation, or broaden the existing two-table
  SELECT grant.
- Do not implement agent content mutations, COW sessions, publication,
  review/promotion, MCP changes, browser-worker behavior, or unrelated process
  features.
- Do not replace the server-owned control boundary with agent-side raw SQL or
  request-derived trust.
- Do not edit the immutable `066-a` order or report; corrections/evidence for
  this gap belong to `066-b` and its new report.
- Do not merge the PR or activate `067-a`; only the strategic model may do so.

## Observable acceptance criteria

- A normally constructed and started Agent API application, using its
  production factory/lifecycle and configured disposable PostgreSQL, returns
  HTTP 200 for a valid seeded capability with the correct workspace context.
- The same production-wired application returns HTTP 401 for malformed,
  unknown, wrong-secret, revoked, and expired credentials, and HTTP 503 for
  unavailable control state without leaking secrets or infrastructure details.
- The regression test does not patch `app.state.database` after app creation to
  install the capability verifier; any dependency injection must exercise the
  same production ownership/lifecycle path.
- The Agent API still exposes only bounded semantic capability authentication;
  no raw pool, locator, SQL, capability minting, user management, migration,
  or publication authority is exposed to the agent.
- The diff remains limited to this runtime wiring, its tests, and honest OAP
  evidence; no unrelated migration/dependency/trust change appears.

## Required verification

- Run the focused real-PostgreSQL/ASGI capability test with the production
  Agent API factory and lifecycle, plus the full backend unit and integration
  suites.
- Run ruff, formatting, mypy, repository policy, package/build, Markdown,
  Mermaid, and required frozen Node checks.
- Independently inspect the final app factory/lifespan, dependency ownership,
  privilege boundary, error mapping, and test for any post-construction state
  substitution.

## Security, documentation, and report

- Preserve fail-closed site/workspace context and sanitized authentication
  errors; never log or return token plaintext, digest, SQL, driver, or locator
  details.
- Update durable documentation only if runtime behavior was previously stated
  inaccurately; do not broaden scope for prose cleanup.
- Publish `oap/reports/066-b-agent-runtime-capability-wiring.md` in a
  report-only commit after the implementation amendment. Include the exact
  PR/branch, implementation-head SHA, literal report parent, `SELF` syntax,
  report-only tree proof, every acceptance criterion's evidence, all local and
  GitHub check statuses, the prior 066-a limitation, and honest follow-up.

## Authority and workflow

- The strategic model owns this continuation order, active selector, FIFO,
  review, acceptance, merge, and advancement.
- The coding agent owns only bounded implementation, tests, commits, push, and
  the immutable `066-b` report; it must not edit activated orders/active or
  merge PR #57.
- After activation, consume the exact control-FIFO `OK`, amend PR #57, publish
  the report-only child, and send the exact response-FIFO `OK` only after the
  remote report state is verified.
