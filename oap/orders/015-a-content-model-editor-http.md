# OAP Work Order — 015-a

## Objective

Build the Editor API HTTP routes for content type and field definition CRUD
(create, list, get, update, delete) with server-side authorization, Pydantic
models, and PostgreSQL stored functions. No agent API or workspace/COW session
integration yet — this objective is the human editor surface only.

## GitHub objective state

- Numeric objective: `015`; round: `015-a`
- Mode: `CREATE_NEW_PR`; **exactly one new PR**
- Existing PR/URL: N/A (new)
- Required head or NEW: NEW
- Base: `main` at merge commit `1c6f6a4e17d7dba7d50deae3374473334fda40cb`

Fetch and verify origin/main is at or ahead of this SHA. Start from current origin/main.

## Strategic context — verified current state

The `content.content_type` and `content.field_definition` tables exist as
COW-enabled tables from migration 016_001. The `FieldPrimitive` StrEnum is
implemented in `services/backend/src/slaif_agent_site/content_model/primitives.py`.
The scope catalog TypeScript package exports all delegation levels.

The Editor API currently has zero domain routes — it only exposes health.
The Control API has a working site CRUD pattern in `control_api/site_http.py`
and `sites/service.py` using SECURITY DEFINER stored functions. The route
policy system validates that every mutating route declares required permissions.

## Bounded scope

Create exactly:

1. **Alembic migration `017_001_content_model_functions.py`** creating
   SECURITY DEFINER functions in schema `content` for:
   - `content_type_create(site_id UUID, key TEXT, labels JSONB, slug_pattern TEXT, settings JSONB) RETURNS content_type_row`
   - `content_type_list(site_id UUID) RETURNS TABLE(...)`
   - `content_type_get(type_id UUID) RETURNS content_type_row`
   - `content_type_update(type_id UUID, labels JSONB, slug_pattern TEXT, settings JSONB) RETURNS content_type_row`
   - `content_type_delete(type_id UUID) RETURNS void`
   - `field_definition_create(type_id UUID, key TEXT, label TEXT, field_type TEXT, required BOOLEAN, localized BOOLEAN, cardinality INT, position INT, validation JSONB, ui_options JSONB) RETURNS field_definition_row`
   - `field_definition_list(type_id UUID) RETURNS TABLE(...)`
   - `field_definition_get(field_id UUID) RETURNS field_definition_row`
   - `field_definition_update(field_id UUID, label TEXT, required BOOLEAN, localized BOOLEAN, cardinality INT, position INT, validation JSONB, ui_options JSONB) RETURNS field_definition_row`
   - `field_definition_delete(field_id UUID) RETURNS void`

   All functions must:
   - Set `search_path = pg_catalog` for security;
   - Be owned by `slaif_owner`;
   - Have EXECUTE granted to `slaif_editor_runtime` and `slaif_control`;
   - REVOKE ALL from PUBLIC;
   - Validate that `field_type` matches a value in `FieldPrimitive` values;
   - Return structured error codes (`RBAC_DENIED`, `NOT_FOUND`, `CONFLICT`) via RAISE EXCEPTION.

2. **Pydantic models** `services/backend/src/slaif_agent_site/content_model/models.py`:
   - `CreateContentTypeRequest(key: str, labels: dict[str,str], slug_pattern: str, settings: dict)`
   - `UpdateContentTypeRequest(labels, slug_pattern, settings)` (all optional)
   - `ContentTypeRecord(id, site_id, key, labels, slug_pattern, status, definition_version, settings, created_at, updated_at)`
   - `CreateFieldDefinitionRequest(type_id, key, label, field_type: FieldPrimitive, required, localized, cardinality, position, validation, ui_options)`
   - `UpdateFieldDefinitionRequest(label, required, localized, cardinality, position, validation, ui_options)` (all optional)
   - `FieldDefinitionRecord(...)` matching DB columns

3. **Service layer** `services/backend/src/slaif_agent_site/content_model/service.py`:
   - `ContentModelService(pool)` following the same pattern as `SiteService`;
   - Methods for each CRUD operation calling the corresponding SQL function;
   - Error enum with `NOT_FOUND`, `CONFLICT`, `UNAVAILABLE`;
   - `_content_type(row)` / `_field_definition(row)` row mappers returning typed records.

4. **Editor API router** `services/backend/src/slaif_agent_site/editor_api/content_http.py`:
   Routes under `/api/editor/v1/sites/{site_id}/content-model/...`:
   - `POST   /types` → create content type
   - `GET    /types` → list types for site
   - `GET    /types/{type_id}` → get single type
   - `PATCH  /types/{type_id}` → update type
   - `DELETE /types/{type_id}` → delete type
   - `POST   /types/{type_id}/fields` → create field
   - `GET    /types/{type_id}/fields` → list fields for type
   - `GET    /fields/{field_id}` → get single field
   - `PATCH  /fields/{field_id}` → update field
   - `DELETE /fields/{field_id}` → delete field

5. **Route policy declarations** adding entries for each new route to the
   Editor API policy table with appropriate mutation class and required permissions.

6. **Integration tests** proving:
   - Create/list/get/update/delete content type through HTTP with authenticated platform admin;
   - Create/list/get/update/delete field definition through HTTP;
   - 404 for nonexistent IDs; 409 for duplicate key;
   - Non-admin user receives 403 on all routes;
   - Invalid `field_type` value returns 422;
   - All functions validate search_path security.

7. **Unit tests** for models validation and service error mapping.

## Explicit non-goals

- No Agent API routes or capability authentication.
- No COW workspace/session integration (these are canonical-only operations).
- No content item CRUD (that's a future objective).
- No collection view CRUD.
- No Puck/composition changes.
- No frontend UI changes.
- No dependency additions.

## Concrete requirements

### Migration details
- Revision string: `"017_001"`; down_revision: `"016_001"`.
- Each function must be created inside `op.execute()` raw SQL.
- The `content_type_delete` function should perform a soft-delete by setting status to 'DELETED' rather than hard DELETE, preserving audit trail.
- The `field_definition_delete` function should also soft-delete by setting a `deleted_at TIMESTAMPTZ` column (add this column to the migration if it doesn't exist).

### Route policy
Each route needs an entry in the route policy table. Use:
- `RouteAuthorityKind.SITE_PERMISSION`
- Required permission keys matching the scope catalog (e.g., `"content-model:create"`)
- CSRF required for mutations

### Service pattern
Follow the existing `SiteService` pattern exactly: asyncpg pool injection,
SQL constant strings at module top, typed record mappers, stable error enum.

## Observable acceptance criteria

1. All new unit tests pass: `uv run --frozen pytest services/backend/tests/unit/test_content_model_models.py`.
2. All new integration tests pass: `uv run --frozen pytest services/backend/tests/integration/test_content_model_http.py`.
3. Existing integration tests still pass: `uv run --frozen pytest services/backend/tests/integration/test_database_bootstrap.py`.
4. `python tools/check_repository.py` passes (route policy coverage check).
5. Full CI matrix passes.

## Required tests / CI / E2E evidence

Run before pushing:
- `pnpm lint && pnpm format:check && pnpm typecheck && pnpm test && pnpm build`
- `uv sync --frozen --all-groups && uv run --frozen pytest services/backend/tests/unit/ -x`
- `uv run --frozen pytest services/backend/tests/integration/test_database_bootstrap.py -x`
- Integration tests for content model HTTP require PostgreSQL service containers.

## Documentation

No external docs required. Docstrings reference architecture sections.

## Safety / security / secrets / data / deployment constraints

- All functions use `SET search_path = pg_catalog` to prevent search_path hijacking.
- Soft deletes preserve data for audit; no hard DELETE of editorial data.
- Route authorization requires SITE_PERMISSION authority kind; non-admin users cannot access any content model route.
- No secrets, tokens, or production identifiers in code.

## Local capability

Routine setup belongs to executor; passwordless sudo exists.

## GitHub workflow

1. Fetch and verify origin/main is at least at `1c6f6a4e17d7dba7d50deae3374473334fda40cb`.
2. Create fresh branch `oap/015-content-model-http`.
3. Implement bounded scope.
4. Run all verification commands locally.
5. Commit implementation.
6. Push branch.
7. Create exactly one new PR via `gh pr create` targeting main.
8. Never merge, close, or auto-merge.
9. Inspect checks; repair in-scope failures within turn if needed.

## Exact final-report contract

Preserve activated order and `oap/active` bytes. Atomically publish:

```
oap/reports/015-a-content-model-editor-http.md
```

Report-only `SELF` commit parents the literal implementation SHA. Report branch,
PR number/URL, base/head, literal implementation SHA, summary, files changed,
test commands/results, safety confirmations, skipped/blocked items, risks/follow-up.
Signal FIFO `OK` only after report and claimed remote state exist.
