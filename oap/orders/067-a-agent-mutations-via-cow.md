# OAP Work Order — 067-a

## Objective

Replace the Agent API write-route stubs with real COW-backed semantic
mutations through `asyncpg_cow_session`. This is the defining vertical:
an external agent must be able to create content types, fields, items,
pages, and composition nodes through the public Agent REST API, with
those writes going into the workspace COW overlay (not canonical).

## GitHub objective state

- Numeric objective: `067`; round: `067-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR

## Anti-false-positive clause

Authentication + scope checks + a `503` placeholder do NOT satisfy this
objective. Completion requires the public Agent API to perform real
validated workspace-only mutations through the `asyncpg_cow_session` path.
A mocked COW session in unit tests does not satisfy this objective.
At least one integration test must use a real PostgreSQL COW session.

## Required changes

1. Wire agent write routes to `ContentModelService` methods, but wrap
   the database calls in `asyncpg_cow_session` context so writes go to
   the workspace overlay, not canonical.
2. Accept `Idempotency-Key` header on all mutation routes.
3. Return the server-assigned operation UUID in mutation responses.
4. Add at least one integration test using real PostgreSQL + COW that:
   - Creates a workspace session
   - Creates a content type through the Agent API
   - Verifies the type exists in the workspace but NOT in canonical
   - Discards the session
   - Verifies canonical is unchanged

## Acceptance criteria

- Agent can POST to `/api/agent/v1/content-model/types` and get a 201.
- The created type exists only in the workspace COW overlay.
- Canonical tables are unchanged after workspace writes.
- Same Idempotency-Key returns the same result (idempotent replay).
- Different payload with same key returns 409 IDEMPOTENCY_MISMATCH.
- At least one test uses real PostgreSQL COW, not mocks.

## Activation addendum — authoritative constraints

This inert preplanned order is amended with the following requirements before
activation. They are part of 067-a and supersede any ambiguity above.

### Repository, live state, and authority

- Repository: `/home/ubuntu/codex-work/slaif-agent-site`.
- Obey repository `AGENTS.md`, `OAP-COMMUNICATION-coding-agent.md`, and the
  compact normative `ARCHITECTURE-for-agents.md`. Strategic owns scope,
  acceptance, and merge; coding implements and reports.
- At preparation, verified remote `main` is
  `e647fb850f963bf0e9793273b28fccf6e8811bc7` (merged PR #57); no 067 objective
  PR exists. Re-fetch at activation and report live differences.
- Objective 066 established the distinct `slaif_agent_runtime` identity,
  secret, lifecycle, entrypoint, grants, and edge health aliases. Agent API
  discovery/read routes are authenticated; its write routes are still 503
  placeholders. Preplanned 068-a through 077-a remain inert.

### Exact objective and bounded route surface

Replace the Agent write stubs with real, validated, workspace-only semantic
mutations through the public `asyncpg_cow_session` API. The bounded create
surface is:

- `POST /api/agent/v1/content-model/types`
- `POST /api/agent/v1/content-model/types/{type_id}/fields`
- `POST /api/agent/v1/content-items/types/{type_id}`
- `POST /api/agent/v1/pages/`
- `POST /api/agent/v1/pages/{page_id}/components`

Use existing request/record models and semantic `ContentModelService` methods.
Add only the smallest executor/session abstraction needed to run them on the
already-open COW connection; do not acquire a second ordinary pool connection
inside a COW mutation. Update route policy, OpenAPI/contract fixtures, and
focused tests for every route. No route in this surface may remain a stub.

### Required security and transaction behavior

1. Derive `site_id`, `workspace_id`, effective scopes, and operation UUID only
   from the trusted capability context. Reject client-selected session/site/
   operation/database identity and all raw SQL, DDL, base/change-table, or
   reviewer access.
2. Enforce each route's create scope, site/resource/model/parent/composition
   validation, and the existing fail-closed error envelope.
3. Require a valid `Idempotency-Key` on every mutation. Generate one server
   operation UUID and use it for the idempotency record, COW `operation_id`,
   audit, and response. Same capability+key+digest returns the stored result
   without another COW operation; a changed digest returns
   `409 IDEMPOTENCY_MISMATCH` without mutation.
4. Idempotency authority must be durable and transactionally safe across
   restarts/replicas. The existing in-memory helper is not production proof.
   Reuse an existing durable control mechanism or add the smallest
   developer-owned control-plane migration and narrow server function needed;
   do not place it in the COW content schema or grant arbitrary control-table
   DML to the Agent runtime.
5. Every mutation uses the Agent runtime pool and `asyncpg_cow_session` with
   the server-derived workspace and operation UUID. Prove cleanup on success,
   failure, cancellation, and pool reuse. Canonical remains untouched until
   the human-only lifecycle orders implement promotion.
6. Return the created semantic record plus a UUID `operation_id`; preserve
   stable validation, scope, conflict, unavailable, and idempotency errors.
7. Do not add create-workspace, freeze, accept, selective-accept, discard,
   publish, capability/user management, reviewer, or infrastructure routes.
   A disposable integration fixture may discard a session through trusted
   reviewer helpers; the public Agent API may not.

### Observable proof

- A valid authenticated L4 capability receives `201`, a semantic record, and
  `operation_id` for content-type creation.
- Real PostgreSQL integration uses the actual Agent runtime role and
  capability-authenticated HTTP route, not a mock COW session: create a
  workspace, create a type through the Agent API, observe it in that workspace
  overlay, prove canonical/base is unchanged, discard with a trusted fixture,
  and prove canonical remains unchanged.
- The proof ties the operation UUID to COW/audit evidence and proves the Agent
  runtime cannot read/write canonical/base/change tables or reviewer/control
  authority.
- Replay with the same key/digest returns the same result and operation UUID
  without a second pending operation; changed payload returns 409 and leaves
  state unchanged. Cover missing/invalid keys, insufficient scope, wrong-site
  resources, malformed bodies, and supported cancellation/pool cleanup.
- No new path can publish, accept, freeze, manage identities, run arbitrary
  SQL/DDL, register executable primitives, or change edge/container policy.

### Verification, docs, and workflow

Run and report exact results (or honestly mark skipped/not-run/blocked):
focused Agent HTTP/unit, route-policy, idempotency, content-model, real
PostgreSQL integration, backend quality, repository-required policy/security/
packaging checks, and `git diff --check`. Review the scoped diff for secrets,
unrelated files, direct dependencies, unnecessary migrations, and trust
expansion. Update durable API/contract documentation so the implemented
routes, idempotency response, and workspace-only semantics are truthful; do
not claim promotion, publication, full Agent API completion, or production
readiness.

Fetch current remote main, create exactly one fresh 067-a branch/PR, implement
only this order, push, and never merge. Commit the activated order and exact
`oap/active` without editing their strategic content. Publish the immutable
report as the final report-only commit; before signaling, verify the remote PR
head is that report commit and its first parent is the literal implementation
head. Report branch/base/PR, implementation SHA, `Report publication commit:
SELF`, files/behavior, exact tests and statuses, real COW/idempotency evidence,
setup/docs/security, limitations, and `RESULT=OK|PARTIAL|BLOCKED|FAILED`.
