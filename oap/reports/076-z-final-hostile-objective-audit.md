# OAP Implementation Report — 076-z

## Result

- Order: `076-z`
- Work-order file: `oap/orders/076-z-final-hostile-objective-audit.md`
- Order SHA-256: `a4435937cf0458ec46ad8bcc5e47158d4b34ab022253eb2cf715f21732b10bbb`
- Numeric objective: `076`
- Outcome: `COMPLETE`
- Delivery mode: `AMENDED_EXISTING_PR`
- Repository: `ulfe-lmi/slaif-agent-site`
- Pull request: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72)
- PR state at implementation-head verification: `OPEN`, `MERGEABLE`, `CLEAN`
- Branch: `oap/076-agent-model-content-semantics`
- Base: `main`
- Required starting remote report head: `8475973d3375197709c80f4bbd7b08581203704d`
- Required starting-head sole parent: `92fba838f55ca0bbe62397594bbfbd7c11da6681`
- Starting remote `main`: `0e83b26bf9a9f63bff6756d65cbfd527d215ec51`
- Literal implementation SHA: `2c6800b568e7b4028bdadb3b73382d5447238ad1`
- Implementation parent: `8475973d3375197709c80f4bbd7b08581203704d`
- Implementation commits pushed in this round: `2c6800b568e7b4028bdadb3b73382d5447238ad1`
- `oap/active` at implementation commit: exact bytes `076-z\n`
- Report publication commit: SELF

The active order’s final hostile audit is complete. The implementation repairs
the database dependency race contract, strengthens the public acceptance
ledger, mechanically closes the OpenAPI/policy/handler inventory, and records
the complete Objective 076 evidence. PR #72 remains unmerged as required;
acceptance and merge remain strategic authority decisions.

## Exact bounded changes

The implementation commit contains only the activated 076-z scope, its exact
strategy selector/order bytes, and the required report inputs:

- `services/backend/src/slaif_agent_site/db/alembic/versions/048_001_agent_relations_and_collection_views.py`
  adds the shared workspace dependency lock, exact type/field dependency
  guards, concurrent value-key validation, and repaired current wrappers
  without creating a new migration head.
- `services/backend/src/slaif_agent_site/content_model/service.py`,
  `errors.py`, and `agent_api/agent_http.py` preserve the
  stable `FIELD_DEPENDENCIES` and `TYPE_DEPENDENCIES`
  public 422 errors.
- `services/backend/src/slaif_agent_site/agent_api/app.py` performs
  the bidirectional live-handler, route-policy, and canonical OpenAPI
  inventory check and publishes exact mutation/idempotency metadata.
- `contracts/openapi/agent-v1.json`, `contracts/README.md`,
  and `docs/API.md` record the generated contract and dependency-safe
  public behavior.
- `services/backend/tests/integration/test_agent_mutations.py` adds
  the direct-wrapper/public-HTTP dependency matrix and real two-connection
  races; `services/backend/tests/unit/test_agent_openapi.py` covers
  the new contract declarations.
- `tools/compose/public_agent_acceptance.py` now asserts an exact
  semantic audit multiset, idempotency/COW siblings, revocation no-residue
  behavior, and the dependency error code.

No historical order/report, architecture, constitution, protocol, or
repository policy was rewritten. The order and selector were materialized with
their exact bytes and committed unchanged.

## Objective 076 criterion ledger

### 1. Concurrency-safe type and field dependency guards

- Type deletion now rejects any visible same-site field, active item,
  collection view, translation reachable from its items, or relation reachable
  from its items before quota, idempotency completion, audit, or COW mutation.
- Field deletion now uses structural predicates for nonlocalized values,
  localized translation values, exact normalized relation field IDs, recursive
  filter field nodes, exact sort fields, and exact projection-array members.
  Substring matches are not used.
- Content item, translation, relation, and collection-view mutations enter the
  same deterministic workspace lock contract before the dependency check and
  preserve their row/definition locks, scope/resource/quota checks,
  cancellation rollback, and COW writes.
- The database value-key helper closes the check-then-delete gap for
  concurrent item and translation writes.
- Direct wrapper controls and public Agent HTTP controls are covered by
  `test_agent_final_dependency_matrix_and_two_connection_delete_races`.
  It exercises relation-vs-field, translation/item-value-vs-field,
  view-vs-field, and field/view/item-vs-type races, with one coherent winner
  and a stable loser.
- The same test proves each dependency class blocks deletion with stable 422
  codes and no quota/audit/idempotency/COW residue, then deletes in dependency
  order while preserving the observer workspace. The migration
  round-trip test `test_agent_048_data_bearing_round_trip_preserves_relations_views_and_audit`
  and fresh Compose initialization verify the current 048 function/grant/check
  contract and data-bearing behavior.

### 2. Public acceptance and OpenAPI evidence

- The clean public journey now records and verifies an exact multiset of all
  30 successful semantic type/field/item/translation/relation/view mutations.
  Each expected row includes capability public ID, site, workspace, operation
  ID, resource type and ID, request digest, semantic action, HTTP method,
  response status, quota kind, and idempotency key; each actual row must have
  completed idempotency and its corresponding COW operation.
- The journey explicitly includes item-relation and collection-view actions,
  replay/mismatch and denial no-residue checks, and a revoked primary
  capability request through public NGINX. Revocation returns 401 and leaves
  audit and idempotency counts unchanged.
- Existing lower-preset, resource, quota, wrong-site/path, stale,
  dependency, publication-absence, restart, NGINX outage/recovery,
  canonical/observer isolation, other-site/workspace, and tombstone proofs
  remain in the clean acceptance.
- The generated artifact `contracts/openapi/agent-v1.json` has
  SHA-256 `d7f120cbba9ed83982d51220dc41fee41efcb440d02e0f12a392717f983d8a48`,
  23 paths, 43 operations, 21 mutations, and 45 component schemas.
  Production handlers, every current Agent route policy, and the canonical
  artifact are compared in both directions. Bearer security, exact scopes,
  mutation/idempotency declarations, request-body shape, success schemas and
  stable error statuses are checked. Generic FastAPI docs remain disabled and
  public NGINX bytes match the committed artifact.

### 3. Hostile audit of the complete Objective 076 contract

All activated order files `076-a` through `076-z` and their
reports were reviewed against the constitution, compact architecture, route
policy, contract audit, and the complete PR diff. The criterion families close
as follows:

- Field primitive discovery and exact type, field, item, translation, relation,
  and collection-view list/get/create/update/delete surfaces are implemented
  in the Agent routers and covered by the Agent mutation/route-policy tests.
  Typed stable errors include auth, scope, resource, not-found, stale,
  dependency, quota, and validation cases.
- Distinct scopes, lower-preset denial, immutable IDs/keys, resource
  allowlists, type/field limits, delete-enabled behavior, mutation quota, and
  max-delete quota are enforced at the trusted database boundary. The focused
  resource tests and the full 23-test Agent mutation suite passed.
- Trusted site/workspace/operation/capability context, ACTIVE/delegator/revoke/
  expiry/freeze checks, COW-only writes, no raw SQL/DDL/code/primitive
  registration, and no canonical/publication/user authority remain enforced by
  the existing authority descriptors, route policy, wrappers, and hostile
  integration tests.
- Shared 075 validators, current definition/row versions, parent version
  increments, stale cleanup, dependency guards, and cancellation behavior are
  covered by the validator regressions, CRUD tests, migration round trips, and
  real connection races.
- Canonical isolation, other-workspace/site isolation, true item tombstones,
  restart persistence, idempotent replays/mismatches, one wrapper-owned charge,
  strict semantic audit identity, append-only audit privileges, legacy audit
  separation, and migration data safety are proven by
  `test_agent_semantic_reads_use_cow_overlay_fallback_and_isolation`,
  `test_agent_canonical_item_delete_is_a_real_cow_delete_and_isolated`,
  `test_semantic_audit_contract_is_strict_and_reversible`, the
  migration round-trip tests, and the clean public acceptance.
- Deterministic OpenAPI, exact route-policy drift, public NGINX behavior,
  patched PostgreSQL Compose behavior, zero unexcepted Critical findings,
  no new vulnerability exception, and PG14–18 coverage are closed by the
  generated-contract checks, clean Compose smoke, fresh supply-chain evidence,
  and all terminal remote checks below.

### 4. Reconciliation and termination

The earlier exceptions were not silently credited:

- 076-q was `PARTIAL` because an unrelated governance browser check
  failed. Later ordered work reran that gate; the current Compose/edge check
  is green.
- 076-w was `BLOCKED` by the then-current supply-chain vulnerability
  result, and 076-x was `BLOCKED@@ by the immutable PostgreSQL image’s
  unexcepted Critical findings. The fresh 076-z supply-chain run now passes
  with zero unexcepted Critical findings across all six project-owned images.
- 076-y was `COMPLETE` for its acceptance slice. This final order
  closes the reserved hostile audit and dependency/openapi evidence work.

No 077+ behavior was added: pages/navigation/redirects, composition/design,
media, MCP, review/promotion, and lifecycle remain outside Objective 076.
The strongest remaining reason not to merge within Objective 076 is none; the
PR is ready for independent strategic review. This is not a merge declaration.

## Verification evidence

### Local repository and application gates

The required local gates completed successfully:

- `uv lock --check` and `uv sync --frozen --all-groups`.
- `uv run --frozen ruff check services/backend tests/repository tools`.
- `uv run --frozen ruff format --check services/backend tests/repository tools`.
- `uv run --frozen mypy`: no issues in 246 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  517 passed.
- `uv run --frozen pytest services/backend/tests/integration`:
  138 passed.
- Focused OpenAPI/route-policy tests: 8 passed; focused dependency/race and
  regression tests passed; the full Agent mutation suite: 23 passed.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-076z`:
  source and wheel artifacts built.
- `python -m compileall -q tools tests/repository`: passed;
  repository unittest discovery: 58 passed; repository policy: passed;
  Mermaid: 16 diagrams / 366 Markdown files scanned; Markdownlint: 0 issues
  across 360 files.
- All ten documented frozen-uv process `--check` smokes passed:
  control API, Editor API, Agent API, Render API, MCP adapter, media service,
  review worker, scheduler, media GC, and bootstrap.
- Node `v24.14.1` and pnpm `11.22.0` were used. Frozen
  install, lint, format check, typecheck, test, build, and JSON license
  inventory all passed; TypeScript was `6.0.3`.

### Clean Compose and supply chain

The clean command
`sg docker -c 'bash tools/compose/smoke.sh slaif007z'` passed with
the final line `compose-smoke: OK`. Its public acceptance included:

`public-agent-acceptance: OK workspace=9da27cac-4355-4636-8a83-a37afff70948 types=2 fields=3 items=2 translations=1 relations=1 views=1 pages=1 components=1 openapi=exact restart=verified nginx-outage=verified crud=public quotas=mutation-429,max-delete-429 dependency-delete=422 tombstones=verified`

The fresh full local supply-chain command
`sg docker -c 'bash tools/supply_chain/run.sh /tmp/slaif-supply-chain-076z-final'`
passed with:

- `supply-chain-evidence: OK images=6 critical=41 high=102`.
- `supply-chain-evidence-checksum: OK`.
- `supply-chain-gate: OK evidence=/tmp/slaif-supply-chain-076z-final`.
- The evidence bundle’s six project-owned image IDs were:
  Apache `sha256:4b8026e111cc4ab4b82e56d9ee9e804eea9f29c7a466e492c038c17b9c52ce90`,
  backend `sha256:b5f8f0e3d415cab9bed3ec6c7b0fbd079accff95fc98379c88d72ae75406790b`,
  browser-worker `sha256:3993733e982b0916a4e22fc81d3d0eb3f28f68e8fb3bae455975b7913104f6d2`,
  NGINX `sha256:cb089775b057c3d000b62db9baae932f83b8c2369401e42699512d81a8b8477f`,
  PostgreSQL `sha256:83c291f4c0b9157993fb1a52b54c3fc4d6afbedacf8fd22192f9e093cecbdfc0`,
  and web `sha256:c292a010519ec9df26ecc0ef798644dbe0866917d66ef2b78101b30e4979f1a8`.
- The fresh Grype database checksum was
  `sha256:0c38b7025406d1b7a3041cc144ef7abb0523859d57633c6ed39578027a0676ec`.
  The 41 Critical findings are the existing approved browser-image findings;
  unexcepted Critical is zero and no exception or threshold was changed.

### Authoritative GitHub checks

At implementation SHA `2c6800b568e7b4028bdadb3b73382d5447238ad1`,
run 33595956148 plus the CodeQL run, every required check was terminal
success:

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

PR #72 reported `OPEN`, `MERGEABLE`, and
`CLEAN` after the matrix completed. No required check was pending,
failed, cancelled, skipped, or missing.

## Setup, dependencies, and safety

- Local verification used uv `0.12.5`, Node `24.14.1`,
  pnpm `11.22.0`, TypeScript `6.0.3`, Docker, and
  disposable PostgreSQL/fake credentials only.
- No production system, production data, credential store, Docker socket
  outside the authorized disposable Compose checks, real secret, capability,
  cookie, private URL, or database credential was accessed, printed, or
  committed.
- No unrelated dependency, entity, migration head, trust boundary,
  deployment topology, architecture rule, vulnerability exception, cleanup,
  refactor, feature, or release claim was added.
- No required verification was skipped, weakened, replaced, or converted into
  an exception. No extra PR was created. The coding agent did not merge,
  auto-merge, close, release, or publish the objective PR.
- The implementation commit contains the exact active selector and order bytes;
  no strategy-owned bytes were edited in place.
- Durable API documentation and contract documentation were updated for the
  changed dependency/error/OpenAPI behavior.

## Completion condition

The coding execution for 076-z is complete. Objective 076 / PR #72 may be
declared complete only after the strategy authority independently reviews this
report, confirms the terminal green remote state at the report head, and makes
the separate strategy-owned acceptance/merge decision. PR #72 itself remains
open and unmerged; no merge was performed by the coding agent.
