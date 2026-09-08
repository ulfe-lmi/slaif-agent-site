# OAP Coding-Agent Report — 077-d

## Work order

- Identifier: `077-d`
- Work-order file: `oap/orders/077-d-repair-page-authority-and-structure-proof.md`
- Numeric objective: `077`
- Work-order SHA-256: `0094457c33323a0cac803dec6ed1049fc9299d8a32b6d3a92d89aefe371b49e6`
- `oap/active` SHA-256: `6e52faba59df4bf523314aef5d722538c514e2651836da4df789eae5a365d9d0`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`COMPLETE`

## Executive summary

Objective 077’s active 077-d order repaired the five concrete 077-a page-slice
defects without widening the objective. Page deletion/restoration is now a
product-owned COW soft tombstone with exact optimistic versions and route reuse;
all page authority validates existing enabled same-site locales without creating
locale configuration; route templates and moves are honest bounded contracts;
conditional `route:write` authority is declared in route policy, enforced by the
handler and database, and emitted in canonical OpenAPI; and real multi-connection
race, cancellation, migration, downgrade, Render, and public NGINX evidence was
added.

The implementation is unchanged after the final local and remote verification.
It is committed and pushed as `daad2a51c61830b4093950e904d9f052fa0a7840`.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74)
- PR state: `OPEN`, unmerged
- Base/head: `main` / `oap/077-agent-site-structure-semantics`
- Starting remote report head: `ba6edf7a07156db0748c860b1264c903a436a01d`
- Starting remote `main`: `067676314e0d9664d40cb8514ea549b966a4eb2d`
- Implementation head SHA: `daad2a51c61830b4093950e904d9f052fa0a7840`
- Implementation head parent: `ba6edf7a07156db0748c860b1264c903a436a01d`
- Implementation commit pushed before this report: `daad2a51c61830b4093950e904d9f052fa0a7840`
- Remote branch after implementation push: `daad2a51c61830b4093950e904d9f052fa0a7840`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- New PR this turn: `NO`
- Amended existing PR this turn: `YES`
- Merge or auto-merge performed: `NO`

## Changes made

- Replaced Agent page deletion’s hard delete/private COW lookup with a
  product-owned `content.page.deleted_at` tombstone. Delete increments the
  page row version, returns the deleted typed record, preserves the page ID,
  and remains quota/audit/idempotency controlled. Restore clears the tombstone,
  increments the version, revalidates locale, parent, subtree, constraints,
  and route uniqueness, and fails atomically on route reuse or invalid parent.
- Removed production dependencies on `content.page_changes`, `_cow_deleted`,
  `_cow_order`, and other private foundation relations/columns. Production
  source and migration SQL contain no such dependency; owner-only tests inspect
  COW internals only for isolation/residue assertions.
- Made locale validation-only for page authority. Create, route-affecting
  update, move, delete, restore, Agent reads, Editor projections, and Render
  require an existing enabled same-site locale. No Agent page path inserts or
  configures locale rows.
- Restricted `route_template` to `NULL` or exact `{slug}` and removed ignored
  `before_page_id`/`after_page_id` move inputs. Move now persists only an exact
  parent change and its derived-route effect.
- Added route-policy conditional scope declarations and deterministic
  `x-slaif-conditional-scopes` OpenAPI metadata. Metadata-only PATCH remains
  `page:write`; supplied `slug`, `locale`, or `route_template` additionally
  require `route:write` in the handler and trusted database function.
- Preserved workspace/site structural advisory-lock ordering and added real
  multi-connection tests for route-update/move, competing cycle moves, restore
  versus route reuse, and cancellation while waiting on the structural lock.
- Repaired migration 049 in place, including product-column/COW reconciliation,
  active-route uniqueness, explicit Editor projections, privileges/function
  signatures, and atomic downgrade preflight for 049-only page data.
- Extended the public Compose Agent acceptance through NGINX for page lifecycle,
  canonical independence, Agent restart, and Render restart.

## Files changed

The implementation commit changed exactly:

- `contracts/openapi/agent-v1.json`
- `docs/API.md`
- `oap/active`
- `oap/orders/077-d-repair-page-authority-and-structure-proof.md`
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py`
- `services/backend/src/slaif_agent_site/agent_api/app.py`
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`
- `services/backend/src/slaif_agent_site/content_model/page_models.py`
- `services/backend/src/slaif_agent_site/content_model/service.py`
- `services/backend/src/slaif_agent_site/control_api/route_policy.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/049_001_agent_page_structure.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/render_api/projection.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_render_projection_integration.py`
- `services/backend/tests/unit/test_agent_openapi.py`
- `services/backend/tests/unit/test_content_model_models.py`
- `services/backend/tests/unit/test_route_policy.py`
- `tools/compose/public_agent_acceptance.py`

The report-only child must change exactly this report file.

## Acceptance-criteria evidence

### Product-owned deletion and restoration

- `test_agent_page_structure_hierarchy_routes_and_cow_lifecycle`: passed. A
  canonical page and workspace-created page retain the same ID through delete
  and restore; tombstones are absent from Agent reads; versions and replay
  semantics are exact; canonical state remains unchanged.
- `test_agent_page_tombstone_route_reuse_and_locale_authority`: passed. A
  tombstone is absent from list/get, its route can be reused by a new page, and
  restoring the old ID returns stable 409 without residue.
- `test_canonical_projection_is_site_confined_and_typed`: passed with direct
  owner-seeded tombstone proof. Active Render treats a tombstoned page as
  absent.
- Migration and COW functions use `deleted_at` on the product page domain and
  no private foundation change-table behavior.

### Locale authority

- The page authority function validates only `content.site_locale`; it never
  inserts, enables, disables, defaults, reorders, renames, or deletes a locale.
- Unknown and disabled locale create attempts return domain validation and the
  focused HTTP proof verifies no page, quota, audit, idempotency, COW, or locale
  residue.
- The shared integration fixture now explicitly seeds `en-US` and `en`; no
  implicit locale creation was restored.

### Route and move contract

- Model, database check constraint, and migration validation accept only
  `NULL` or exact `{slug}`. Unit tests reject static, renamed, wildcard,
  repeated, and nonterminal forms.
- `MovePageRequest`, handler, wrapper, OpenAPI, documentation, and tests expose
  only `parent_id` and positive `expected_row_version`.
- `test_agent_page_route_patch_and_move_race_has_serialized_outcome` and the
  competing-move test passed with stable serialized outcomes.

### Conditional authorization and OpenAPI

- `test_agent_page_patch_route_scope_is_conditional` passed: metadata-only
  PATCH works with `page:write`; route-field PATCH without `route:write` is 403
  with no durable idempotency result; both scopes permit route changes.
- Route-policy tests pass for the declaration and field-to-scope resolution.
- The canonical generated contract contains exactly:

  ```json
  {
    "when_fields": ["slug", "locale", "route_template"],
    "required_scopes": ["route:write"]
  }
  ```

- The live public OpenAPI bytes match `contracts/openapi/agent-v1.json`.

### Transaction, race, cancellation, and migration proof

- Four real PostgreSQL multi-connection tests passed: route PATCH versus move,
  competing cycle-capable moves, restore versus same-route replacement, and
  cancellation while waiting on the structural lock. The barrier observes
  database lock state cooperatively; no timing sleep is used for race ordering.
- `test_agent_049_downgrade_rejects_page_data_atomically` passed: route-template
  data causes `049_DOWNGRADE_PAGE_DATA_PRESENT` before teardown and leaves
  version/data usable and unchanged.
- `test_agent_049_plain_page_data_downgrade_and_upgrade_preserves_data` passed:
  an exact 048-compatible data-bearing database downgrades and re-upgrades with
  page data intact.
- Existing 046/047 and 048 data-bearing migration round-trip tests passed.

### Public-edge and isolation proof

- The extended public Compose acceptance passed through NGINX with:
  `page-delete-restore=verified`, `canonical-independence=verified`, and
  `render-restart=verified`.
- The proof exercised real capability-authenticated create, metadata update,
  parent-only move, tombstone, same-ID restore, route reuse/restore conflict,
  cleanup, Agent restart, and Render restart. The workspace-created published
  page remained absent from the canonical public route.
- Full Compose smoke passed, including browser/device, role/privilege,
  recovery, edge, negative-bootstrap, secret-file, artifact, and packaging
  checks.

## Local verification

- `python -m compileall -q tools tests/repository services/backend/src`:
  PASSED.
- `uv run --frozen python -m unittest discover -s tests/repository -p 'test_*.py'`:
  PASSED — 58 tests.
- `python tools/check_repository.py`: PASSED — repository policy.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams, 373 Markdown files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 367 files, 0
  issues.
- `uv lock --check && uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 264 files formatted.
- `uv run --frozen mypy`: PASSED — 247 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`:
  PASSED — 520 tests, 26 subtests, 1 existing Starlette/httpx deprecation
  warning.
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED — 148
  tests in 18m50s. An earlier serial run exposed two stale `en`-locale fixture
  assumptions; the fixture was corrected to seed that locale explicitly, the
  two tests passed independently, and this complete rerun passed cleanly.
- `uv run --frozen pytest tests/packaging tests/supply_chain -q`: PASSED — 81
  tests, 54 subtests.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — source and
  wheel distributions built.
- `pnpm install --frozen-lockfile`: PASSED — pnpm 11.22.0.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — production build, package tests, web 9 tests, browser
  worker 10 tests, and contract tests 4 passed.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED — license inventory emitted with no
  policy failure.
- `uv run --frozen python -m <process> --check` for control API, Editor API,
  Agent API, Render API, MCP adapter, media service, review worker, scheduler,
  media GC, and bootstrap: PASSED — all ten `CHECK_OK`.
- `sudo -n sh tools/compose/smoke.sh slaif071d`: PASSED — clean Compose stack,
  public page lifecycle, NGINX canonical independence, Agent/Render restarts,
  recovery, security, packaging, and 47 packaging tests; final
  `compose-smoke: OK`.

The initial bare `/usr/bin/python` process-check invocation was not a product
failure: the system interpreter could not import the uv-managed package. The
same ten required checks were rerun successfully in the frozen uv environment.
An exploratory parallel integration invocation also hit shared disposable-role
contention; it was not used as evidence, and the complete serial suite above
passed.

Required verification was not weakened, replaced, or omitted. The separate
full supply-chain evidence/image qualification was not rerun locally beyond
the required focused supply-chain tests and clean Compose build; the order
preserves the qualified Chrome `.82` evidence and the remote required gate ran.

## GitHub CI / required checks

For implementation head `daad2a51c61830b4093950e904d9f052fa0a7840`, CI run
`33857642874` and CodeQL run `33857642891` were inspected. Every observed
current-head check was terminal `SUCCESS` / pass:

- Analyze (actions)
- Analyze (javascript-typescript)
- Analyze (python)
- CodeQL
- Compose and edge packaging
- Dependency review
- Detect supported languages
- Foundation PostgreSQL 14
- Foundation PostgreSQL 15
- Foundation PostgreSQL 16
- Foundation PostgreSQL 17
- Foundation PostgreSQL 18
- Markdown
- Mermaid
- Node contracts
- Python 3.12 quality and package
- Python 3.13 quality and package
- Python 3.14 quality and package
- Repository policy
- Supply-chain evidence

All required checks at the implementation head were green: `YES`. The
report-only commit will create a fresh check set; strategy must independently
verify that report `SELF` is the remote PR head and that its current checks are
terminal success.

## Local setup / dependencies

- Existing uv and pnpm environments were used; frozen lockfiles remained
  unchanged.
- The disposable PostgreSQL fixture and Docker/Compose stack were operated
  with passwordless sudo for routine test infrastructure only.
- No production dependency, image, lockfile, exception, or foundation version
  was added or changed.
- Foundation use remains through qualified `agentcow.postgres` public APIs.

## Documentation

- `contracts/openapi/agent-v1.json` was regenerated from the live Agent app.
- `docs/API.md` documents the corrected tombstone, locale, route-template,
  conditional-scope, parent-only move, and restore-version contracts.
- No architecture, constitution, communication protocol, historical report, or
  prior strategic order was rewritten.

## Safety and scope confirmations

- Unrelated files changed: `NO`.
- Production systems/data accessed: `NO`.
- Production secrets, real capabilities, cookies, private credentials, and
  private artifact URLs printed or committed: `NO`; Compose used disposable
  fixture credentials and opaque in-memory tokens.
- Required checks skipped, weakened, or replaced: `NO`.
- Scope deviation: `NO`; no locale CRUD, navigation, redirect, dynamic Render,
  composition redesign, media/MCP, freeze/review/promotion, 078+, cleanup,
  refactor, or unrelated feature work was added.
- Extra objective PR: `NO`.
- Coding-agent merge or auto-merge: `NO`.
- Activated order/active authored or selected by coding: `NO`; exact strategic
  bytes were committed unchanged.
- Report publication commit changes only this report: `YES`.

## Known limitations / blockers

No 077-d implementation blocker remains. PR #74 remains open because coding
agents never merge objective PRs and `COMPLETE` is not strategic acceptance.
The remaining broader Objective 077 page/navigation/redirect/Render scope is
not implemented by this order and requires later bounded strategic authority.

## Recommended strategic follow-up

Verify this report-only `SELF` child, its parent and exact path, and the fresh
report-head required checks. Objective 077 / PR #74 can be declared complete
only after strategy independently accepts the 077-d diff and report, verifies
the report-head checks, obtains the required human review, merges the existing
PR to remote `main`, and verifies the merged main state. Until then this is a
delivered 077-d implementation round, not objective acceptance.

Report publication commit: SELF
