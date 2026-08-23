# OAP Work Order — 065-a

## Objective

Reissue the runtime-wiring objective under the clean OAP numeric range
`065–077`, and fix the runtime service wiring so that the Editor API and Agent
API can actually serve content-model CRUD operations. The prior unmerged PR
`#55` used the legacy identifier `023-a` and is superseded by this reissued
objective; its implementation was never merged to `main`.

The current closure sequence is renumbered as follows: `023→065`, `024→066`,
`025→067`, `026→068`, `027→069`, `028→070`, `029→071`, `030→072`,
`031→073`, `032→074`, `033→075`, `034→076`, and `035→077`. Preserve the
sequence and update only the current OAP transcript identifiers; historical
merged PR labels and reports remain historical evidence.

Currently, all content-model
routes fail at runtime because `ControlDatabase.content_model_service()`
does not exist, and the Agent API's `app.state.content_model_service` is
never set. Additionally, `browser_router` is included twice in the Agent
API app.

## GitHub objective state

- Numeric objective: `065`; round: `065-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR
- Base: `main` at the current remote default-branch head
- Superseded PR: `#55` / `oap/023-a-fix-runtime-service-wiring` (closed before
  this objective is signaled)

## Verified current state

- `ControlDatabase` has `human_session_service()`, `site_service()`,
  and `human_authorization_service()` but NOT `content_model_service()`.
- Editor API routes call `database.content_model_service()` → AttributeError at runtime.
- Agent API routes call `request.app.state.content_model_service` → AttributeError at runtime.
- `agent_api/app.py` includes `browser_router` twice.
- `agent_api/app.py` never sets `app.state.content_model_service`.

## Required changes

1. Replace the legacy current transcript files with the already-published
   renumbered files in this working tree: remove legacy current orders
   `023-a` through `035-a`, retain their content under `065-a` through
   `077-a`, and update all internal current-sequence references accordingly.
   Do not rewrite historical reports or merged PR history.
2. Update repository-policy/documentation expectations that refer to the
   current unexecuted range `024–035` so they refer to `066–077`; do not
   broaden policy exemptions.
3. Add `content_model_service()` method to `ControlDatabase` (and to its
   Protocol if one exists) that returns a `ContentModelService` instance
   backed by the same connection pool.
4. In `agent_api/app.py`: remove the duplicate `browser_router` include;
   set `app.state.content_model_service` to a `ContentModelService` instance
   during app creation.
5. In `editor_api/app.py`: ensure `app.state.content_model_service` is also set.
6. Verify that all existing tests still pass.
7. Add one integration test proving that `ContentModelService` is reachable
   from both the editor and agent app contexts.

## Explicit non-goals

- Do NOT implement COW session integration (separate objective).
- Do NOT implement capability auth (separate objective).
- Do NOT change route policies.
- Do NOT add new features.

## Acceptance criteria

- All existing tests pass.
- `ControlDatabase` has a `content_model_service()` method.
- Current OAP transcript contains exactly one current order for each of
  `065–077`, with no legacy current-sequence order `023–035` remaining.
- `agent_api/app.py` includes `browser_router` exactly once.
- Both editor and agent apps set `app.state.content_model_service`.
- No runtime AttributeError when accessing content-model routes.

## Report

Publish `oap/reports/065-a-fix-runtime-service-wiring.md` with the
report-only SELF commit parenting the implementation SHA.
