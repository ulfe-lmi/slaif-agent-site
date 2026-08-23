# OAP Work Order — 023-a

## Objective

Fix the runtime service wiring so that the Editor API and Agent API can
actually serve content-model CRUD operations. Currently, all content-model
routes fail at runtime because `ControlDatabase.content_model_service()`
does not exist, and the Agent API's `app.state.content_model_service` is
never set. Additionally, `browser_router` is included twice in the Agent
API app.

## GitHub objective state

- Numeric objective: `023`; round: `023-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR
- Base: current main

## Verified current state

- `ControlDatabase` has `human_session_service()`, `site_service()`,
  and `human_authorization_service()` but NOT `content_model_service()`.
- Editor API routes call `database.content_model_service()` → AttributeError at runtime.
- Agent API routes call `request.app.state.content_model_service` → AttributeError at runtime.
- `agent_api/app.py` includes `browser_router` twice.
- `agent_api/app.py` never sets `app.state.content_model_service`.

## Required changes

1. Add `content_model_service()` method to `ControlDatabase` (and to its
   Protocol if one exists) that returns a `ContentModelService` instance
   backed by the same connection pool.
2. In `agent_api/app.py`: remove the duplicate `browser_router` include;
   set `app.state.content_model_service` to a `ContentModelService` instance
   during app creation.
3. In `editor_api/app.py`: ensure `app.state.content_model_service` is also set.
4. Verify that all existing tests still pass.
5. Add one integration test proving that `ContentModelService` is reachable
   from both the editor and agent app contexts.

## Explicit non-goals

- Do NOT implement COW session integration (separate objective).
- Do NOT implement capability auth (separate objective).
- Do NOT change route policies.
- Do NOT add new features.

## Acceptance criteria

- All existing tests pass.
- `ControlDatabase` has a `content_model_service()` method.
- `agent_api/app.py` includes `browser_router` exactly once.
- Both editor and agent apps set `app.state.content_model_service`.
- No runtime AttributeError when accessing content-model routes.

## Report

Publish `oap/reports/023-a-fix-runtime-service-wiring.md` with the
report-only SELF commit parenting the implementation SHA.
