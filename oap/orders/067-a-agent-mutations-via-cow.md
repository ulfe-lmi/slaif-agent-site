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
