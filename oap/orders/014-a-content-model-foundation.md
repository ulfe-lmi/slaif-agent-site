# OAP Work Order — 014-a

## Objective

Create the configurable content model database foundation: Alembic migrations
for `content.content_type`, `content.field_definition`, and
`content.content_item` as COW-enabled tables; shared scope-catalog TypeScript
constants for agent delegation levels L1–L4; and a Python field-primitive enum.
No HTTP routes yet — this objective is data layer + contracts only.

## GitHub objective state

- Numeric objective: `014`; round: `014-a`
- Mode: `CREATE_NEW_PR`; **exactly one new PR**
- Existing PR/URL: N/A (new)
- Required head or NEW: NEW
- Base: `main` at merge commit `cb1dcb877591f51a111c447080752cd77fa5f8a7`

Fetch/verify remote main is at or ahead of this SHA. Start from current origin/main.

## Strategic context — verified current state

The repository has completed phases 0–2 of the architecture implementation
sequence. The `content` PostgreSQL schema exists but contains zero tables.
The COW foundation (`agentcow.postgres`) is qualified, deployed in bootstrap,
and its `enable_cow_schema` function wraps existing tables into
`<name>_base` / `<name>_changes` / view triplets. No content model tables,
field primitives, or scope catalog constants exist yet.

The architecture specifies 17 field primitives:
short_text, long_text, rich_text, integer, decimal, boolean, date, datetime,
url, email, enum, media, document, reference, multi_reference, location,
object, repeatable_object.

Agent delegation levels map to scopes per ARCHITECTURE-for-agents.md §5.

## Bounded scope

Create exactly these:

1. **Alembic migration `016_001_content_model_tables.py`** creating three
   tables in schema `content` with columns matching ARCHITECTURE-for-agents.md
   §10 logical model. All UUID PKs, immutable site_id FKs to control.site,
   timestamps, row_version, workspace/audit provenance columns. Composite
   unique constraints on (site_id,key) / (type_id,key) / (site_id,type_id,slug).
2. **Bootstrap update** adding these three table names to the COW enable flow
   so `enable_cow_schema(schema="content")` wraps them after Alembic runs.
3. **Python module** `services/backend/src/slaif_agent_site/content_model/primitives.py`
   containing a `FieldPrimitive(StrEnum)` with all 17 members and validation
   that no primitive accepts executable code.
4. **TypeScript package** `packages/scope-catalog/src/index.ts` replacing the
   scaffold with typed constants for READ, L1_WRITE through L4_WRITE scope
   arrays exactly matching the architecture catalog, plus a `DELEGATION_LEVELS`
   record mapping level→scope set.
5. **Unit tests** for the Python enum and TS package verifying exact member sets.
6. **Integration test** proving the three new content tables are COW-enabled
   (have `_base` and `_changes` companions) after bootstrap completes.

## Explicit non-goals

- No HTTP routes (agent/editor/control API changes).
- No workspace/capability creation or management logic.
- No Puck/composition/component changes.
- No browser/media/review worker changes.
- No dependency additions or lockfile changes.
- No documentation beyond docstrings/comments within changed files.

## Concrete requirements

### Migration details
- Revision string: `"016_001"`; down_revision: `"015_001"`.
- Tables must be created inside `op.execute()` raw SQL (not `op.create_table()`)
  because COW requires specific column ordering and constraints.
- Every table has: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`,
  `site_id UUID NOT NULL REFERENCES control.site(id)`,
  `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`,
  `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`.
- `content_type`: add `key TEXT NOT NULL`, `labels JSONB NOT NULL DEFAULT '{}'`,
  `slug_pattern TEXT NOT NULL`, `status TEXT NOT NULL DEFAULT 'ACTIVE'`,
  `definition_version INTEGER NOT NULL DEFAULT 1`, `settings JSONB NOT NULL DEFAULT '{}'`.
  Unique: `(site_id, key)`.
- `field_definition`: add `type_id UUID NOT NULL REFERENCES content.content_type(id)`,
  `key TEXT NOT NULL`, `label TEXT NOT NULL`, `field_type TEXT NOT NULL`,
  `required BOOLEAN NOT NULL DEFAULT false`, `localized BOOLEAN NOT NULL DEFAULT false`,
  `cardinality INTEGER NOT NULL DEFAULT 1`, `position INTEGER NOT NULL DEFAULT 0`,
  `validation JSONB NOT NULL DEFAULT '{}'`, `ui_options JSONB NOT NULL DEFAULT '{}'`,
  `definition_version INTEGER NOT NULL DEFAULT 1`. Unique: `(type_id, key)`.
- `content_item`: add `type_id UUID NOT NULL REFERENCES content.content_type(id)`,
  `slug TEXT NOT NULL`, `status TEXT NOT NULL DEFAULT 'DRAFT'`,
  `type_definition_version INTEGER NOT NULL`, `values JSONB NOT NULL DEFAULT '{}'`,
  `row_version INTEGER NOT NULL DEFAULT 1`. Unique: `(site_id, type_id, slug)`.

### Bootstrap integration
After Alembic migration 016_001 runs, the bootstrap's `enable_cow_schema` call
must include these three tables in its output list. Verify by checking that the
returned array from `enable_cow_schema` contains all three names when the
content schema has them.

### Scope catalog
Export these named arrays (exact strings, one per line):
```typescript
export const AGENT_READ_SCOPES = [...] as const;
export const AGENT_L1_WRITE_SCOPES = [...] as const;
export const AGENT_L2_WRITE_SCOPES = [...] const;
export const AGENT_L3_WRITE_SCOPES = [...] as const;
export const AGENT_L4_WRITE_SCOPES = [...] as const;
export const DELEGATION_LEVELS = { 1: [...], 2: [...], 3: [...], 4: [...] } as const;
```

### Field primitive enum
All 17 values from the architecture. Each member name equals its value string.
Include a classmethod `is_executable(v: str) -> bool` returning False for all
current members (future executable primitives must be explicitly opted in).

## Observable acceptance criteria

1. `uv run --frozen pytest services/backend/tests/unit/test_field_primitives.py` passes.
2. `pnpm --filter @slaif-agent-site/scope-catalog test` passes.
3. `uv run --frozen pytest services/backend/tests/integration/test_content_model_cow.py`
   passes against a real PostgreSQL instance.
4. `python tools/check_repository.py` passes.
5. Full CI matrix (all 20 checks) passes on the PR head.

## Required tests / CI / E2E evidence

Run before pushing:
- `pnpm lint && pnpm format:check && pnpm typecheck && pnpm test && pnpm build`
- `uv sync --frozen --all-groups && uv run --frozen pytest services/backend/tests/ -x`
- `python tools/check_repository.py`
- Integration tests requiring PostgreSQL may use the CI runner's service containers.

## Documentation

No external docs required. Docstrings should reference architecture sections.

## Safety / security / secrets / data / deployment constraints

- Migration uses only additive DDL (CREATE TABLE). No ALTER/DROP on existing tables.
- All FKs point to `control.site(id)` or `content.content_type(id)` which are
  already protected by existing bootstrap privilege hardening.
- No secrets, credentials, tokens, URLs, or production identifiers in any file.
- The `FieldPrimitive.is_executable()` method returns False for every current
  member; there is no path to make it return True without modifying source code.

## Local capability

Routine setup belongs to executor; passwordless sudo exists. Install any
needed packages in the VM only. Do not transfer setup work to human.

## GitHub workflow

1. Fetch and verify origin/main is at least at `cb1dcb877591f51a111c447080752cd77fa5f8a7`.
2. Create fresh branch `oap/014-content-model-foundation`.
3. Implement bounded scope.
4. Run all verification commands locally.
5. Commit intended work (implementation commit).
6. Push branch.
7. Create exactly one new PR via `gh pr create` targeting main.
8. Never merge, close, or auto-merge.
9. Inspect checks; repair in-scope failures within turn if needed.

## Exact final-report contract

Preserve activated order and `oap/active` bytes. Atomically publish:

```
oap/reports/014-a-content-model-foundation.md
```

Report-only `SELF` commit parents the literal implementation SHA. Report:
branch, PR number/URL, base/head, literal implementation SHA, summary, files
changed, exact test commands/results, setup/deps used, docs impact, safety
confirmations, skipped/blocked items, risks/follow-up. Signal FIFO `OK` only
after report and claimed remote state exist.
