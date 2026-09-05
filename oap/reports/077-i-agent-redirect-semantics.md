# OAP Coding-Agent Report — 077-i

## Work order

- Identifier: `077-i`
- Work-order file: `oap/orders/077-i-agent-redirect-semantics.md`
- Numeric objective: `077`
- Work-order SHA-256: `3eeeb17c4b6835d5dfbdeb557c3585031880ef4aeb32b915b589012af6c7f585`
- `oap/active` bytes: `077-i` followed by LF (`30 37 37 2d 69 0a`)
- `oap/active` SHA-256: `59570e288b1bf4de30619fcf0aa061c57bfdbe39ca2ee71f97e82b6ef95a19ab`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`COMPLETE`

## Executive summary

The active 077-i order is complete. PR #74 now contains the typed public
Agent redirect contract, PostgreSQL-enforced route/target/locale/graph and
dependency semantics, and the shared workspace+site structural serialization
required by the order. The existing page, locale, navigation, browser,
ledger, bootstrap and protocol work was preserved.

The implementation and proof commits are pushed at
`f76ec0da661261da9d2c4760b5ae66b2ff4f750a`, directly on the required 077-h
report head `c27b25da904bf76bf8a58617607d36825072d573`. Focused redirect and
race coverage, all local Python and Node gates, clean public Compose proof,
and every current GitHub CI/CodeQL check are green.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74)
- PR state: `OPEN`, unmerged
- Base/head: `main` / `oap/077-agent-site-structure-semantics`
- Starting remote report head: `c27b25da904bf76bf8a58617607d36825072d573`
- Starting remote `main`: `067676314e0d9664d40cb8514ea549b966a4eb2d`
- Literal implementation SHA: `f76ec0da661261da9d2c4760b5ae66b2ff4f750a`
- Implementation parent: `7eb12a026901c5e28fe4915791ccaaa6b17508a0`
- Implementation commits pushed before this report:
  `13b7d3836827d5f91c23073c8163e0155b8a567a`,
  `12eaaf8cd35bd62e4128798d742d62a9fe6ce159`,
  `1083cb47094df9ba75e507050f953d2e24f196da`,
  `7eb12a026901c5e28fe4915791ccaaa6b17508a0`,
  `f76ec0da661261da9d2c4760b5ae66b2ff4f750a`
- Report publication commit: `SELF`
- New PR this turn: `NO`
- Amended existing PR this turn: `YES`
- Merge or auto-merge performed: `NO`

## Changes made

- Added typed Agent `GET`/`POST /api/agent/v1/redirects` and typed
  `GET`/`PATCH`/`DELETE /api/agent/v1/redirects/{redirect_id}` handlers,
  exact scope policy, idempotency enforcement, positive row-version checks,
  server operation UUIDs, standard envelopes, and
  `REDIRECT_CREATED`/`REDIRECT_UPDATED`/`REDIRECT_DELETED` contracts.
- Added strict normalized source and target validation: absolute safe source
  paths, reserved/traversal/encoded/control/executable rejection, HTTPS-only
  external targets, exact static-page or redirect internal targets, locale
  fallback rules, no self/cycles/dangling targets, and a bounded graph depth
  of 16.
- Added immutable site confinement, enabled same-site locale and capability
  filtering, `route_prefix`, `max_visible_redirects`, delete-enabled/delete
  quota enforcement, and no hidden-resource inference.
- Added source/page route collision guards, page-target dependency guards,
  redirect dependent-delete denial, and all mutation replay/mismatch safety.
- Serialized Agent and Editor redirect and page structural writes with the
  application-owned workspace+site lock after the workspace lifecycle lock.
  The old site-only redirect lock is not used by the production definitions.
- Added migration `051_001_agent_redirect_semantics` over the fixed
  `content.redirect` table. It preserves compatible data and Editor
  projections, restores prior function identities on downgrade, and defines
  the narrow Agent wrappers, parser, validation, visibility, graph, page
  guard, target-dependency and source-dependency helpers.
- Regenerated canonical Agent OpenAPI and updated route policy, integration
  tests, and public Compose acceptance proof. No dynamic Render, composition,
  media, MCP, freeze/review, 076, or 078+ work was added.

## Files changed

The implementation/proof commits changed exactly:

- `contracts/openapi/agent-v1.json`
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py`
- `services/backend/src/slaif_agent_site/agent_api/models.py`
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`
- `services/backend/src/slaif_agent_site/agent_state/reads.py`
- `services/backend/src/slaif_agent_site/content_model/service.py`
- `services/backend/src/slaif_agent_site/content_model/site_data_models.py`
- `services/backend/src/slaif_agent_site/content_model/site_data_validators.py`
- `services/backend/src/slaif_agent_site/control_api/route_policy.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/050_001_agent_locale_navigation.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/051_001_agent_redirect_semantics.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/bootstrap/service.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_control_api.py`
- `services/backend/tests/integration/test_bootstrap.py`
- `services/backend/tests/integration/test_editable_content.py`
- `services/backend/tests/integration/test_session_lifecycle.py`
- `services/backend/tests/unit/test_agent_route_policy.py`
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_manifest.py`
- `services/backend/tests/unit/test_health.py`
- `services/backend/tests/unit/test_site_data_validators.py`
- `tests/repository/test_repository.py`
- `tools/compose/public_agent_acceptance.py`

The strategic `oap/active` and 077-i order bytes were committed unchanged;
this report is the only file added by the final report-only commit.

## Acceptance-criteria evidence

### Public contract and authorization

- The five required redirect routes are present in the canonical OpenAPI and
  route-policy inventory. Reads require `redirect:read`; create, update and
  delete require their exact mutation scope.
- Mutations require `Idempotency-Key`; update/delete require an exact positive
  row version. Replay does not add a version, quota, audit or COW effect, and
  mismatches are stable conflicts. Responses use typed records and
  server-owned operation UUIDs with the three exact redirect action names.
- `delete_enabled`, `max_deletes`, request, mutation and visible-resource
  limits are enforced in the trusted capability/database path.

### Route, target, locale and graph integrity

- Sources are normalized absolute paths and reject root when unsupported,
  reserved control paths, repeated/dot/encoded separators, query/fragment,
  backslash, wildcard/template/control/space and executable syntax.
- Internal targets resolve exactly to a visible same-site non-tombstoned
  static page route or visible redirect under deterministic locale fallback;
  external targets require HTTPS. Self-targets, cycles, dangling targets,
  ambiguous locale matches and chains over 16 are rejected.
- Locale values are enabled, visible, same-site and capability-allowed.
  Source uniqueness is per visible site+locale and route-prefix and
  `max_visible_redirects` constraints count only capability-visible rows.
  Restricted capabilities cannot read or infer hidden rows.

### Dependencies and concurrency

- Page create/route change/move/restore and delete guards reject redirect
  source collisions and internal targets that would become dangling.
  Redirect delete rejects visible incoming dependents. Updates revalidate the
  complete affected graph and dependencies in PostgreSQL.
- The real PostgreSQL Agent test
  `test_agent_redirect_crud_graph_constraints_and_page_dependencies` passed,
  including CRUD, unsafe/HTTP/executable/reserved inputs, internal chain,
  dangling/cycle/collision/dependent-delete checks, source-update races,
  dependent-delete races and concurrent maximum-visible creation. The shared
  structural-lock integration coverage also passed cancellation while waiting,
  rollback/no-residue assertions and successful retry; redirect graph
  mutations use the same transaction/lock primitive.
- Agent and Editor page/locale/navigation/redirect writes use the same
  workspace+site structural lock. Foreign workspace/site and hidden-resource
  checks remain site-confined; no direct service or owner SQL substitutes for
  public Agent proof.

### Database, COW and public proof

- Migration `051_001` adds the Agent wrappers
  `slaif_agent_redirect_list`, `slaif_agent_redirect_get`,
  `slaif_agent_redirect_create`, `slaif_agent_redirect_update`, and
  `slaif_agent_redirect_delete`. Shared helpers include
  `slaif_agent_redirect_constraints`, `slaif_redirect_is_visible`,
  `slaif_redirect_source_conflict`, `slaif_redirect_static_target_exists`,
  `slaif_redirect_validate_input`, `slaif_redirect_validate_state`,
  `slaif_redirect_page_guard`, `slaif_redirect_page_target_dependency`, and
  `slaif_redirect_source_dependency`.
- Functions are owned by `slaif_owner`, have explicit fixed search paths,
  PUBLIC access revoked, and only narrow wrapper `EXECUTE` is granted to
  `slaif_agent_runtime`; Editor/control grants remain separate. The existing
  redirect table and projections are reused, and downgrade/upgrade evidence
  passed without discarding redirect data.
- The final local Compose run passed public Agent create/list/get/update/delete,
  locale-specific and fallback route proof, dependency and restart checks,
  audit, canonical/other-workspace/site isolation, NGINX public routing,
  browser evidence, recovery, security and packaging.

## Local verification

- `uv lock --check`: PASSED — 45 packages resolved.
- `uv sync --frozen --all-groups`: PASSED — 44 packages checked.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 266 files formatted.
- `uv run --frozen mypy`: PASSED — 249 files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 522 tests, one existing Starlette/httpx deprecation warning.
- `uv run --frozen pytest services/backend/tests/integration`: the initial
  run had 160 passed and one stale expected-050 fixture failure; the fixture
  was corrected to the current 051 head and the failed test reran PASSED.
  All 161 integration tests therefore passed across the complete run and
  correction rerun.
- Full Agent mutation coverage: PASSED — 38 tests. Full human Editor
  production HTTP coverage: PASSED — 4 tests. Focused migration checks:
  PASSED — 2 tests.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  58 tests.
- `python tools/check_repository.py`: PASSED — repository policy.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 377 files,
  0 issues.
- `uv run --frozen python tools/contracts/generate_agent_openapi.py --check`:
  PASSED.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — source
  and wheel distributions built.
- Node/pnpm gates all PASSED: `node --version` `v24.14.1`, `pnpm --version`
  `11.22.0`, `pnpm install --frozen-lockfile`, `pnpm lint`,
  `pnpm format:check`, `pnpm typecheck`, `pnpm test`, `pnpm build`, and
  `pnpm licenses list --json`. Typecheck and test were rerun sequentially
  after an initial parallel Next build-cache contention.
- All ten required process checks via
  `uv run --frozen python -m <process> --check`: PASSED with `CHECK_OK`.
- `sudo -n sh tools/compose/smoke.sh slaif007ci`: PASSED — final
  `compose-smoke: OK`, including public acceptance, restart/recovery, edge,
  database-role, browser, packaging and secret-policy checks.

No required local gate was skipped, weakened, replaced, or inferred from an
incomplete result. Bare direct `python -m` smoke was not used as evidence in
the src-layout checkout; the required frozen project invocation passed.

## GitHub CI / required checks

At implementation head
`f76ec0da661261da9d2c4760b5ae66b2ff4f750a`, the current PR check rollup is
terminal success for every check:

- Analyze (actions), Analyze (javascript-typescript), Analyze (python), and
  CodeQL
- Dependency review and Detect supported languages
- Foundation PostgreSQL 14, 15, 16, 17 and 18
- Markdown, Mermaid, Node contracts, Repository policy and Supply-chain
  evidence
- Python 3.12 quality and package, Python 3.13 quality and package, and
  Python 3.14 quality and package
- Compose and edge packaging

The final Compose rerun completed successfully; no current required check is
pending, skipped, failed or cancelled at the implementation head.

## Scope, safety and completion boundary

- No production system, credential store, real secret, capability, cookie,
  private artifact URL or Docker socket was accessed for production purposes.
  Compose used disposable local test resources and fake credentials.
- No dependency, architecture, policy, historical strategic artifact or
  immutable order was rewritten. No extra PR was created, and no merge,
  auto-merge, release, issue closure or production readiness claim was made.
- The only remaining Objective 077 work is strategic review of the open PR;
  dynamic Render routing remains a later slice. Objective 077-i / PR #74 is
  complete for coding-agent purposes when this report-only commit is the
  remote PR head and the exact FIFO `OK` is delivered. Strategy alone may
  independently accept and merge the PR after reviewing the evidence; this
  agent is not authorized to merge it.
