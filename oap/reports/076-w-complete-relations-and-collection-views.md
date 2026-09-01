# OAP Implementation Report — 076-w

## Delivery

- Order: `076-w`, `oap/orders/076-w-complete-relations-and-collection-views.md`.
- Delivery class: `AMENDED_EXISTING_PR`.
- Status: `BLOCKED`.
- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72), OPEN, non-draft, branch `oap/076-agent-model-content-semantics`, base `main`.
- Starting remote report head: `afe8d7a01621a7fabf4640c539332ecfd7e0d0f6`.
- Starting report parent / accepted 076-v implementation: `3833e994255262cd12de281a9fe1dd257662a9b9`.
- Remote `main` at activation: `0e83b26bf9a9f63bff6756d65cbfd527d215ec51`.
- Literal implementation SHA: `2332b0026203fbb99fe385106c0c0fa398042347`.
- Implementation parent: `afe8d7a01621a7fabf4640c539332ecfd7e0d0f6`.
- Pushed implementation commit: `2332b0026203fbb99fe385106c0c0fa398042347`.
- `oap/active` is committed as the exact selector `076-w`.
- The exact activated order is committed unchanged.
- Report publication commit: SELF

## Implemented scope

The implementation is bounded to the active order and preserves the existing Agent COW, idempotency, semantic-audit, and quota pipeline.

- Added Agent relation routes:
  - `GET|POST /api/agent/v1/content-items/{item_id}/relations`.
  - `GET|PATCH|DELETE /api/agent/v1/content-items/{item_id}/relations/{relation_id}`.
  - Reads use `content-item:read`; mutations use `relationship:write`.
  - All mutations require `Idempotency-Key`.
  - PATCH and DELETE require positive row versions.
  - DELETE returns the exact pre-delete `RelationRecord` with HTTP 200 and durable replay.
- Added Agent collection-view routes:
  - `GET|POST /api/agent/v1/collection-views/types/{type_id}`.
  - `GET|PATCH|DELETE /api/agent/v1/collection-views/{view_id}`.
  - Exact scopes are `collection-view:read`, `collection-view:create`, `collection-view:write`, and `collection-view:delete`.
  - All mutations require `Idempotency-Key`; PATCH and DELETE require positive row versions; DELETE returns the exact pre-delete `CollectionViewRecord` with HTTP 200 and durable replay.
- Added migration `048_001_agent_relations_and_collection_views`.
  - Capability-bound relation and collection-view wrappers enforce site, workspace, capability, delegator/state, scope, resource allowlists, optimistic versions, dependencies, deterministic transaction locks, and wrapper-owned mutation/delete quotas.
  - Relation create/update validate current source and target definitions, same-site relation fields, target-type allowlists, cardinality, position, and metadata bounds.
  - Collection-view create/update resolve the current same-site type, persist the server-selected definition version, validate the complete resulting bounded query, and reject stale definitions, raw/executable fragments, localized or unsupported fields, invalid operators, projection, pagination, depth, and size.
  - Semantic completion and the audit constraint add exactly `ITEM_RELATION_CREATED|UPDATED|DELETED` and `COLLECTION_VIEW_CREATED|UPDATED|DELETED` with the required resource, method, status, and quota mappings. Legacy completion continues to reject these resources.
  - Privilege inventory and grants include only the intended Agent wrappers; internal assertion/validation helpers remain unavailable to the Agent role.
- Repaired stale cleanup semantics without weakening current-definition create/update validation.
  - Item and translation reads expose authorized stale data and persisted row/type versions.
  - Stale translation and item DELETE operations are allowed after scope, resource, site, workspace, row-version, dependency, and delete-quota checks.
  - Relations and views can be inspected and deleted while stale, without reinterpreting old payloads.
- Added the missing two-connection translation PATCH race proof. Two distinct Agent app instances produce exactly one HTTP 200 and one stable HTTP 409 at one expected row version.
- Updated the migration graph, readiness/fixture expectations, route-policy inventory, and health-route inventory to `048_001`.
- No page, navigation, composition, design, media, MCP, browser, review, promotion, dependency, architecture, governance, or prior-artifact work was added.

## Changed files

- `oap/active`.
- `oap/orders/076-w-complete-relations-and-collection-views.md`.
- `services/backend/src/slaif_agent_site/agent_api/agent_http.py`.
- `services/backend/src/slaif_agent_site/agent_api/models.py`.
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`.
- `services/backend/src/slaif_agent_site/agent_state/reads.py`.
- `services/backend/src/slaif_agent_site/control_api/route_policy.py`.
- `services/backend/src/slaif_agent_site/db/alembic/versions/048_001_agent_relations_and_collection_views.py`.
- `services/backend/src/slaif_agent_site/db/privileges.py`.
- `services/backend/tests/integration/test_agent_mutations.py`.
- Migration/readiness fixture updates in `services/backend/tests/integration/test_control_database_integration.py`, `test_database_bootstrap.py`, `test_editable_domain_proof.py`, `test_human_agent_session_control.py`, `services/backend/tests/unit/test_control_database.py`, and `test_foundation_contract.py`.
- `services/backend/tests/unit/test_health_apps.py` and `test_route_policy.py`.

## Verification evidence

Local verification used disposable PostgreSQL and fake test credentials only.

- Focused relation/view Agent REST CRUD, replay/mismatch, semantic audit, quotas, COW, two-connection view PATCH race, and stale dependency cleanup: PASS.
- Focused two-connection translation PATCH race using two Agent app instances: PASS; one 200, one 409, one row-version increment and no losing residue.
- `uv lock --check`: PASS.
- `uv sync --frozen --all-groups`: PASS.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASS.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASS.
- `uv run --frozen mypy`: PASS.
- `uv run --frozen pytest services/backend/tests/unit`: PASS, 456 tests.
- `uv run --frozen pytest services/backend/tests/integration`: PASS, 135 tests in 963.98 seconds.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASS; source and wheel built.
- `python -m compileall -q tools tests/repository`: PASS.
- Repository unittest discovery: PASS, 58 tests.
- `python tools/check_repository.py`: PASS.
- `python tools/check_mermaid.py`: PASS, 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASS, 354 files and 0 issues.
- Node 24.14.1 and pnpm 11.22.0 were used; the frozen Node lint, format, typecheck, test, build, and license commands all passed. TypeScript was 6.0.3.
- All ten documented process `--check` smokes passed through `uv run --frozen`: control API, Editor API, Agent API, Render API, MCP adapter, media service, review worker, scheduler, media GC, and bootstrap.
- The bare system-interpreter form of those Python smokes could not import the uv-managed package; no implementation gate was substituted or skipped.

## Remote check state

At the final remote observation, PR #72 head was `2332b0026203fbb99fe385106c0c0fa398042347`, OPEN and MERGEABLE, with merge state `UNSTABLE` solely because of the failed supply-chain check.

- Analyze (actions): PASS.
- Analyze (javascript-typescript): PASS.
- Analyze (python): PASS.
- CodeQL: PASS.
- Compose and edge packaging: PASS.
- Dependency review: PASS.
- Detect supported languages: PASS.
- Foundation PostgreSQL 14: PASS.
- Foundation PostgreSQL 15: PASS.
- Foundation PostgreSQL 16: PASS.
- Foundation PostgreSQL 17: PASS.
- Foundation PostgreSQL 18: PASS.
- Markdown: PASS.
- Mermaid: PASS.
- Node contracts: PASS.
- Python 3.12 quality and package: PASS.
- Python 3.13 quality and package: PASS.
- Python 3.14 quality and package: PASS.
- Repository policy: PASS.
- Supply-chain evidence: FAIL.

The failed job is [Supply-chain evidence](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/33564975422/job/100045949127). Its static policy, dependency inventory, notices, reproducible Python/Node artifacts, image builds, and Compose-related work completed, but the Grype scan reported `postgres: unexcepted Critical vulnerabilities: CVE-2026-63073` for the immutable configured PostgreSQL image. This is an external vulnerability-database/image-state failure, not a failure of the 076-w implementation. The order prohibits dependency, production, and release changes; no image pin, vulnerability exception, or security policy weakening was made.

## Governance confirmations and blocker

- No immutable historical order or prior report was edited.
- No second PR was created.
- PR #72 was not merged, closed, or auto-merged.
- No production system, production data, credential store, or real secret was accessed.
- No required local check was skipped; the only documented command adjustment was using the frozen uv interpreter context for Python package entry points.
- No post-report implementation change is authorized.

Objective 076’s relation/view implementation, translation race repair, and stale cleanup are substantively complete. Objective 070 is not in this order’s scope.

The remaining blocker is the required remote supply-chain failure on `CVE-2026-63073`. Clearing it requires a fresh strategic/security decision about the pinned PostgreSQL image or a valid security-maintained image update/exception outside this order. The coding agent is authorized only to remain idle until that external condition changes, then rerun the required remote gates and amend this report through the proper OAP continuation if strategy issues one.

Objective 076 / PR #72 can be declared complete only when the required remote supply-chain evidence check is green, all other required checks remain green at the same final report head, and strategy independently completes its final consolidated public OpenAPI/NGINX/restart acceptance and hostile audit. This coding report does not claim acceptance or merge.
