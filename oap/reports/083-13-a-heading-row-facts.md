# 083-13-a — capture exact row effects for heading edits

- Order: `oap/orders/083-13-a-heading-row-facts.md`
  (8937B, SHA256 `9358fc711b13c50ca66923aa055c5ead1e4cff40202e14a830f7a78ca7061486`,
  committed byte-exact with this round's `oap/active` = `083-13-a`).
- Mode: `CREATED_NEW_PR` — PR 119 <https://github.com/ulfe-lmi/slaif-agent-site/pull/119> (OPEN/DRAFT), branch
  `oap/083-13-a-heading-row-facts`, base `main`
  `eadca4e2c279d2e1dda8917a24058841a2ed9f93` (PR #118 merge, verified
  `git ls-remote origin main` before branch creation).
- Starting remote head: `eadca4e2c279d2e1dda8917a24058841a2ed9f93`.
- Literal implementation SHA: `fd084fa777c0a0e88366399c9db595c44c4e2d87`
  (25 paths vs base, +2363/-61; pushed and verified remote via
  `git ls-remote origin oap/083-13-a-heading-row-facts`).
- Report publication commit: SELF
- Result: COMPLETE for the 083-13-a contract: all frozen local
  gates native-pass on the owned disposable resources and the
  full GitHub CI matrix on the implementation head is green
  (subjects identified exactly below).

## Pushed commits

1. `87d5a124e43cd339d198e35ec14deb2d99258c41` — `oap(083-13-a): capture
   exact heading-props row effects (migration 080) with first-touch, race,
   attribution, and authority proofs`.
2. `fd084fa777c0a0e88366399c9db595c44c4e2d87` — `oap(083-13-a): re-emit
   editor node update from the 063-final composition source` (bounded
   repair of the 080 re-emission source; see the GitHub CI section).

## Grouped diff

- **New forward migration**
  `services/backend/src/slaif_agent_site/db/alembic/versions/080_001_heading_row_effect.py`:
  `audit.heading_row_effect` (versioned `heading-row-effect/v1`, family
  `agent`/`human_editor`, fixed `heading_props` kind, site/workspace/
  component binding, `row_version_before/after` with the exact `+1`
  shape, bounded object-typed props images at the existing 060
  16384-octet ceiling, capability/human principal pairing, owner-only,
  no PUBLIC/role access) plus the owner-only, context-bound,
  reservation-bound `control.slaif_heading_row_effect_record` helper;
  both trusted editorial writer definers (062 Agent
  `content.slaif_agent_component_update` and the Editor
  `content.slaif_composition_node_update`) are re-emitted from the
  final live sibling sources — the 062_001 Agent body and the
  060_001 Editor composition block repaired by 063_001 (the
  design-aware validator calls) — with the bounded same-statement
  `prior`/`post` CTE capture for the Heading case only (non-heading
  writes stay byte-identical pre-080, verified by diffing the runtime
  definer bodies against the base) and are re-secured to the exact
  existing ownership and EXECUTE grant surface. All existing migrations are
  byte-for-byte untouched.
- **Bootstrap operator ratchet**
  `services/backend/src/slaif_agent_site/bootstrap/service.py`:
  `downgrade()` first checks the 080 surface (`to_regclass`) and
  refuses with `BootstrapStateError` before the readiness PENDING
  marker, before the content COW disable and before any migration
  step; the 080_001 Alembic downgrade body is the explicit fail-closed
  refusal for direct migration invocations.
- **New focused integration module**
  `services/backend/tests/integration/test_heading_row_effects.py`
  (seven real native tests; both HTTP paths at real login boundaries;
  real freeze/accept/discard lifecycles; public typed
  conflicts/operations; owner fixture reads only for verification).
- **CI wiring** `.github/workflows/ci.yml` +
  `tests/repository/test_foundation_ci.py`: the new module is the
  eighth exact module path of the trusted mutation-completion (TC)
  command under the existing PG14-18 matrix (no `-k`, no bypass).
- **Direct-call test flow repair**
  `services/backend/tests/integration/test_agent_mutations.py`: the
  runtime-authority test's direct definer Heading call now performs the
  real `slaif_agent_idempotency_begin` for its own operation before the
  update, mirroring the production flow (the 080 trusted record is
  bound to the in-progress same-operation reservation; see
  limitations).
- **Head ripples**: migration-head assertions in
  `tests/unit/test_foundation_contract.py`,
  `tests/unit/test_control_database.py` and ten integration modules
  (readiness rows, `_head` expectations, bootstrap CLI stdout strings,
  downgrade-refusal targets, upgrade-preservation revision).
- **Durable docs** (same-PR behavior/ops/limitation documentation):
  `docs/SECURITY.md` (the heading row effect boundary: versioned
  evidence shape, owner-only authority, context/reservation binding,
  no-effect/replay/rollback behavior, the reserved-completion
  contract, pilot limits, downgrade ratchet), `docs/OPERATIONS.md`
  (the `080_001` bootstrap downgrade ratchet in the existing
  076-078 paragraph style), `docs/TESTING.md` (the new focused
  module's seven proofs and its CI wiring).
- **OAP carry-forward**: `oap/INCREMENTS.md` + `oap/MVP-PROGRESS.md`
  record the PR #118 / `eadca4e2` merge of 083/12 and the in-flight
  083/13 row; `oap/active` and the strategic order byte-for-byte.

## Contract evidence

### 1. Actual mutation boundary (source-anchored, observed natively)

- **Agent path (062)**: the deployed
  `content.slaif_agent_component_update(p_site_id, p_component_id,
  p_props, p_expected)` takes the 050 structural locks, pre-reads the
  row into `old`, enforces the exact `row_version = p_expected` guard
  on the UPDATE (stale -> `P0004`), validates the design system,
  checks no-effect BEFORE any write (identical props complete with the
  trusted `no_effect` disposition and no DML), then re-reads the row
  after the write for the wire response. The trusted pre-write row is
  the row image the UPDATE itself guarded; the HTTP response record is
  the post-write re-read.
- **Editor path (060)**: the deployed
  `content.slaif_composition_node_update(p_node_id, p_props,
  p_slot_key, p_order_key)` keeps its historical no-version-predicate
  body (the pilot observes and records, it does not harden the Editor
  version contract); the returned record omits `row_version` and the
  wire layer renders the constant `row_version=1` (preserved).
- The 080 capture therefore records, inside ONE statement of the
  definer that performs the write, a `prior` CTE image (read before the
  data-modifying `post` CTE per documented WITH execution order) and
  the `post` CTE `RETURNING` image - the exact DML before/after pair,
  not a service-read guess and not a response-only value.

### 2. Transactional bounded product-owned evidence

- One row per successful changed heading-props write, inserted in the
  SAME transaction as the COW write, the family audit row and the
  idempotency completion (the recorder runs from inside the definer
  body); a rolled-back request leaves no row (late stale refusal
  proves it), a replay returns the stored body before completion (no
  second row), and the genuine Agent no-effect path completes with
  the `no_effect` disposition and no row.
- Binding: server operation id (primary key), family, site, workspace,
  component, exact `+1` version pair, bounded props images, capability
  (agent) or human principal RESOLVED FROM the in-progress reservation
  row (human_editor), `heading-row-effect/v1` schema version.
  Sensitivity/retention: the table stores bounded component props
  pairs (editorial content already retained in COW/canonical state)
  under the existing `audit` retention policy; append-only, owner-
  owned; runtime roles cannot SELECT/INSERT/UPDATE/DELETE (denied at
  real logins, asserted in `test_facts_authority_boundaries_and_
  downgrade_ratchet`) and no role has EXECUTE on the recorder; the
  recorder refuses any call outside its own COW session context
  (workspace+operation GUC match), outside a matching in-progress
  reservation, or against a non-matching current row image - there is
  no general-purpose fact insert.
- Two same-resource writes under different operations retain both
  transitions with exact chaining (agent then editor, and agent
  twice); the primary key makes a same-operation double record
  impossible inside the transaction.

### 3. First-touch qualification (owned native PG18)

- Control case (`test_first_touch_conflict_control_case`): W1 and W2
  (same site) both commit first touches before the winner is
  accepted; W2 publishes through REAL freeze + human accept; the four
  distinct sources are each observed through a supported read path
  (canonical at first touch, W1's earlier value, W2's published value,
  W1's actual new value); the typed public conflict is exactly one
  `BASE_ROW_CHANGED` on `page_composition` for the component, and both
  W1 transitions keep their exact facts.
- Proved observation (and recorded limitation): the second write's
  DML pre-image is the workspace's OWN effective COW row at write time
  (the value that workspace wrote earlier), NOT the concurrently
  published canonical row and not the session's first-touch baseline:
  the same-statement capture records the row the mutation actually
  applied to; divergence from the published row is observed through
  the typed public conflict, whose keys/kind are evidence of its own
  contract while the baseline bytes carry their own proof (the first
  write's `props_before` equals the canonical first-touch row).
- Separate first-write race
  (`test_first_write_race_at_statement_boundary`): the loser is paused
  exactly between the deployed definer's pre-read and its UPDATE by
  faithfully replaying the definer's own statements (exact 050 lock
  statements, pre-read, exact version-guarded UPDATE) as the real
  `slaif_agent_runtime` role in a real COW session; the sibling's real
  HTTP first touch plus REAL freeze + human acceptance then publishes;
  the loser's exact stale-version UPDATE affects zero rows, the real
  definer call is refused `P0004`, no fact and no completion exist for
  the refused attempts, and the corrected fresh write's before-image
  is the published row - false-fact absence asserted.

### 4. Attribution and isolation (owned native PG18)

- Enrolled human editor + real Agent capability; both HTTP paths at
  real login boundaries; same-resource sequential edits chain exactly
  across families (agent fact -> editor fact, `props_before` of the
  second equals `props_after` of the first).
- Actually withheld write: the late stale-version request is refused
  and rolls back - no fact, no completion, and the corrected retry
  records exactly one fact.
- Cross-site denial at BOTH real login boundaries (Agent capability
  bound to another site; Editor session enrolled on another site) with
  no recorded effects; cross-workspace binding of the capability is
  enforced by the definer's site/workspace predicates.
- Pilot boundary: a Section props write through the same Agent path
  completes normally and records NO fact (heading-props family only).
- Legal discard: the real freeze + human discard lifecycle removes the
  pending COW rows (public operations empty) while the committed facts
  remain; an old workspace without facts is unknown (no synthetic
  history).
- After rollback of a refused request, the before/after payloads of
  any recorded fact are unchanged (exact chaining assertions).

## Verification (native, owned disposable resources)

- Owned PostgreSQL 18.6 fixture at `[::1]:5432` (explicitly passed to
  every invocation; single runner; trust auth, fake credentials;
  datadir `/tmp/oap-083-12-c-pg/pg18/data`).
- Focused new module: `pytest services/backend/tests/integration/
  test_heading_row_effects.py` -> **7 passed** (PYTEST_RC=0,
  `logs/heading4-full.log`); diagnostic earlier native runs
  `heading1..3.log` preserved (3/5/6 passed while fixture edges were
  repaired).
- Complete frozen PG18 integration suite at `87d5a12`: `pytest
  services/backend/tests/integration` -> **460 passed, 0 failed**
  (PYTEST_RC=0, 77 min, `logs/pg18-full2.log`); the earlier full
  run (`logs/pg18-full.log`, 459 passed / 1 failed) preserved as the
  diagnostic that exposed the direct-definer contract edge; the
  repaired focused rerun is `logs/agent-mutations-repair.log`
  (1 passed, PYTEST_RC=0).
- Repair focused verification at `fd084fa` (the Compose 422
  reproduction, clean of instrumentation): the exact governance
  e2e scenario (Section create + responsive `variant` map PATCH
  through the real Editor HTTP boundary) now returns **200**
  (`logs/fix-repro-clean.log`, PYTEST_RC=0; the failing `422
  DOMAIN_VALIDATION_FAILED` reproduction and the base-`eadca4e2`
  200 control run are preserved in `logs/repro-422-*.log`); focused
  `test_heading_row_effects.py` -> **7 passed**
  (`logs/fix-heading-module.log`); focused
  `test_human_editor_production_http.py` + `test_agent_mutations.py`
  -> **78 passed** (`logs/fix-editor-agent-modules.log`); runtime
  definer diff against base shows exactly the four intended
  additions (DECLARE image pair + Heading branch per definer), the
  design-aware validator header now identical to base.
- Complete frozen PG18 integration suite at `fd084fa` (final):
  `pytest services/backend/tests/integration` -> **460 passed,
  0 failed** (PYTEST_RC=0, 1h16m26s, `logs/fix-pg18-full.log`).
- Static/packaging at `fd084fa`: `uv lock --check` OK; `uv sync
  --frozen --all-groups` (the environment used for every frozen
  invocation); `uv run --frozen ruff check services/backend
  tests/repository tools` all checks passed; `ruff format --check`
  357 files already formatted; `uv run --frozen mypy` no issues in
  335 source files; `uv build` wheel+sdist OK (`logs/fix-static.log`,
  `logs/fix-prep-smokes.log`).
- Preparation at `fd084fa`: `python -m compileall -q tools
  tests/repository` OK; `python -m unittest discover -s
  tests/repository -p 'test_*.py'` 94 OK; `python
  tools/check_repository.py` PASS; `python tools/check_mermaid.py`
  PASS (16 diagrams in 3 files; 650 Markdown files scanned; CLI
  11.16.0); `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` 0
  issues in 642 files; ten process smokes all OK (`logs/
  fix-prep-smokes.log`, `logs/fix-mermaid.log`, `logs/
  fix-markdownlint.log`).
- Node frozen gate at `fd084fa` (Node 24.22.1, pnpm 11.22.0,
  TS 6.0.3): `pnpm install --frozen-lockfile`, `pnpm lint`,
  `pnpm format:check`, `pnpm typecheck`, `pnpm test`, `pnpm
  build`, `pnpm licenses list --json` -> all native 0 (`logs/
  fix-node-gate.log`).
- Unit + repository at `fd084fa`: **902 passed** (PYTEST_RC=0,
  `logs/fix-unit-repo.log`); the same unit/repository,
  preparation, ten-smoke and Node-gate set at `87d5a12` was all
  green as recorded (`logs/node-gate.log` for that head's Node
  gate; `logs/pg18-full2.log` and `logs/unit-repo.log` for its
  suite/unit numbers).
- GitHub CI, draft PR #119, two implementation commits:
  - Run **45619434903** (head `87d5a12`, CodeQL **45619434965**):
    terminal `failure`, 23/24 jobs successful. Successful: Python
    3.12/3.13/3.14 quality and package, Repository policy, Dependency
    review, Markdown, Mermaid, Node contracts, Supply-chain
    evidence, all five Foundation PG Group A children (14-18), all
    five Foundation PG Group B children (14-18, the TC command with
    the new module as eighth path), and the five Foundation
    PostgreSQL 14-18 children. Failed: **Compose and edge
    packaging** (job 139223317811) - `browser-e2e: FAILED
    project=governance
    contract=puck-editor-round-trip-through-human-editor-api
    stage=unknown line=947 column=31 ... Expected: 200 |
    Received: 422` (full log preserved at
    `ci-compose-fail.log`).
  - Root cause (diagnosed natively on owned PG18 and reproduced
    200-on-base / 422-on-branch with the identical real Editor HTTP
    flow): the 080 re-emission of
    `content.slaif_composition_node_update` was sliced from the raw
    `060_001` source instead of the final live `063_001`-repaired
    Editor composition block, silently reverting the design-aware
    `slaif_agent_component_validate_design` call from the deployed
    Editor boundary; the strict pre-063 validator then refused the
    responsive `variant` map with `P0003 COMPONENT_PROP_TYPE`
    (mapped to a codeless domain validation 422). The agent update
    definer (062 source) was verified unaffected.
  - Repair commit `fd084fa` re-emits from the 063-final source;
    run **45628278802** (head `fd084fa`, 13:54:00Z-14:16:57Z,
    CodeQL **45628277868**): terminal `success` - all 25 jobs
    successful: **Compose and edge packaging** (job
    139254243092, the previously failing contract now green with
    real browser evidence through NGINX), Supply-chain evidence
    (139254242272), Python 3.12/3.13/3.14 quality and package,
    Repository policy, Dependency review, Markdown, Mermaid, Node
    contracts, all five Foundation PG Group A children (14-18), all
    five Foundation PG Group B children (14-18, the TC command with
    the new module as eighth path) and the five Foundation
    PostgreSQL 14-18 children. CodeQL 45628277868 `success`
    (actions/js/python analyses).

## Scope / secret / production / skip confirmations

- Scope: exactly the 083-13-a contract (items 1-4); no public history
  endpoint, no backfill, no global lock/isolation change, no private
  foundation storage query (all evidence through real HTTP envelopes,
  the public canonical projection, typed public conflicts/operations,
  product journals/control tables and owner fixture verification
  reads), no SDK change, no new dependency, no production access, no
  unrelated fixes.
- All existing migrations byte-for-byte untouched (only
  `080_001_heading_row_effect.py` is new); no public review rendering/
  snapshot/companion format, reviewer eligibility, promotion/selection,
  supported scope or row-conflict policy change; the Editor definer's
  historical no-version-predicate body is preserved (observed, not
  hardened); the Agent rv guard is preserved as deployed.
- No secrets in the diff/logs (fake fixture credentials only); no
  capability material in URLs/logs.
- No skip/pending/not-run in the claimed local set; CI subjects
  identified exactly per commit above.
- No second PR, no merge, no auto-merge, no history rewrite, no close
  of another PR; `COMPLETE` means executed, not accepted.

## Limitations and next coverage

- The trusted writer definers' Heading case now completes only inside
  a COW session whose in-progress same-operation idempotency
  reservation exists (agent ledger / human-editor ledger); both
  production HTTP paths always begin their reservation before the
  definer call, so no supported flow is affected. A direct definer
  invocation without that reservation fails closed for the Heading
  case (no unprovenanced heading write can complete); non-heading
  writes keep the pre-080 contract byte-for-byte.
- The Editor path has no version gate (historical body preserved); its
  before-image is exact by the same-statement capture, but a stale
  editor request is not refused by a version precondition - that
  contract is outside this increment.
- The pilot records heading-props writes only; complete producer
  coverage (all mutation families/components), exact retained review
  projections and semantic causal closure belong to later increments;
  partial rollout must not be read as full producer coverage.
- Pre-080 heading writes have no recorded facts (no backfill); an old
  workspace without facts is unknown.
- The second-write DML pre-image reflects the workspace's own COW row,
  not concurrently published canonical values (item 3, proved above).
