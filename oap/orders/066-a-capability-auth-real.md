# OAP Work Order — 066-a

## Objective

Replace the capability-authentication placeholder in `agent_http.py` with
real validation against the existing `control.capability` table. A valid
`sas2_<public_id>_<secret>` bearer token must yield the trusted capability
context used by Agent API authorization; malformed, unknown, incorrect,
revoked, and expired credentials must fail closed.

## Strategic context and verified current state

- Objective `065-a` is merged on remote `main` as PR #56, with `oap/active`
  currently set to `065-a` before this order is activated.
- The current transcript uses the clean `065–077` sequence; this order is the
  next numeric objective and must create exactly one new PR.
- `agent_http.py` checks the bearer prefix and calls
  `database.authenticate_agent_capability(auth_header)`, but the method is not
  implemented on `ControlDatabase`.
- Migration `024_001_workspace_lifecycle.py` creates `control.capability` with
  `public_id`, `secret_digest`, `workspace_id`, `scopes`, `expires_at`, and
  `revoked_at`, together with the capability ownership fields required by the
  trusted context.
- `agent_state/capability.py` provides token-format validation, SHA-256 digest
  computation, and constant-time digest comparison.
- `AgentCapabilityContext` is the existing immutable model and includes the
  capability, site, workspace, delegator, scope, creation, and expiry fields.

## GitHub objective state

- Numeric objective: `066`; round: `066-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR for objective `066`
- Base: current remote `main` after the accepted `065-a` merge
- Branch/PR identity is selected by the coding agent only within this order;
  the executor must not choose a roadmap, numeric ID, or merge action.

## In scope

1. Add `ControlDatabase.authenticate_agent_capability(auth_header)` using the
   existing control-database ownership boundary.
2. Parse the exact bearer/token structure using the existing capability
   helpers, look up by `public_id` with parameterized database access, compute
   the digest of the complete presented token, and compare it with the stored
   digest in constant time.
3. Enforce `revoked_at IS NULL` and `expires_at > now()` before constructing
   the immutable `AgentCapabilityContext` with the stored site, workspace,
   delegator, and scopes.
4. Preserve the Agent API distinction between authentication failure and a
   genuinely unavailable control database; do not expose driver, locator,
   token, digest, or SQL details in responses or logs.
5. Add tests for invalid format, unknown public ID, wrong secret, revoked
   capability, expired capability, and one valid capability returning the
   expected context. Exercise the real database path with the repository's
   disposable PostgreSQL integration fixture where the existing test boundary
   supports it.

## Explicit non-goals

- Do not change the physical schema, add an Alembic migration, alter the token
  generation format, or change capability minting/revocation semantics.
- Do not implement new scopes, workspace mutation, publication, review,
  promotion, user management, MCP policy, or browser-worker behavior.
- Do not give the agent raw SQL, control-database ownership, capability
  minting/revocation authority, or a way to bypass workspace/site context.
- Do not modify historical orders/reports, merge a PR, or activate `067-a`.
- Do not add dependencies, secrets, hosted services, or infrastructure
  changes.

## Observable acceptance criteria

- A valid stored capability authenticates and returns an
  `AgentCapabilityContext` with the correct capability/site/workspace/
  delegator/scopes/expiry values.
- Invalid format, unknown public ID, wrong secret, revoked capability, and
  expired capability each produce the existing authentication-failure
  behavior (HTTP 401 at the Agent API boundary).
- Token plaintext, public secret, and digest are absent from logs and error
  response bodies; database or driver details are not leaked.
- The implementation performs a real lookup, digest comparison, and
  revocation/expiry checks; a prefix check or request-derived context alone is
  not acceptable.
- No physical migration or unrelated route/trust-boundary change is present.

## Required verification

- Run the targeted capability unit/integration tests, including the six
  positive/negative cases above.
- Run the repository's backend lint, format, type, and full unit suites.
- Run the relevant real-PostgreSQL integration suite and repository policy
  checks; run the full required local Node/package/documentation checks when
  the repository workflow requires them.
- Independently inspect the final diff for parameterized SQL, fail-closed
  error handling, secret redaction, no migration/dependency changes, and
  exact scope compliance.

## Documentation and security

- Update documentation only if the implemented public behavior or security
  contract is otherwise inaccurate; do not broaden this objective for a prose
  cleanup.
- Preserve the architecture rules that all online writes and agent actions are
  workspace/site-confined, server-owned, capability-scoped, and fail-closed.
- Record every verification command and honest pass/fail/skip/not-run status in
  the executor report. Do not claim acceptance merely because CI is green.

## Report and handoff requirements

Publish `oap/reports/066-a-capability-auth-real.md` in the executor-owned
report-only commit after the implementation head. The report must include:

- order ID, PR URL/number, base/head branch, implementation-head SHA, and
  `Report publication commit: SELF`;
- the literal report-commit parent SHA and confirmation that the report-only
  commit changes only this report;
- files changed, each acceptance criterion's evidence, all local and GitHub
  checks with honest status, security/privacy review, scope/non-goal review,
  limitations, and follow-up recommendation;
- no executor merge claim: only the strategic model may accept and merge.

## Local authority and GitHub workflow

- The strategic model owns this order, `oap/active`, FIFO signaling, review,
  acceptance, merge, and advancement.
- The coding agent owns bounded implementation, disposable setup, tests,
  commits, push, and the immutable report; it must not edit this activated
  order, edit `oap/active`, choose another objective, or merge.
- After activation, signal the exact ASCII bytes `OK` on `control.fifo`, then
  wait for the exact `OK` response on `response.fifo`.
- The strategic model will independently verify the unique PR, remote commits,
  report ancestry/tree, diff, checks, reviews, mergeability, policy, and remote
  default branch before any merge.
