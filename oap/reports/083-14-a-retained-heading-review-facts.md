# OAP 083-14-a — retained Heading review facts

- Order: `oap/orders/083-14-a-retained-heading-review-facts.md`
  (7848 bytes, SHA256 `ed7792bc602bcd76cd60d95d1fad46059905d70a9f0e7b054a58e98363d49368`),
  published byte-exact with `oap/active` = `083-14-a`.
- PR mode: `CREATE_NEW_PR`
- PR: #123 <https://github.com/ulfe-lmi/slaif-agent-site/pull/123>
  (ONE draft PR, branch
  `oap/083-14-a-retained-heading-review-facts`, base `main`, state
  OPEN/draft)
- Result: COMPLETE for the 083-14-a contract: all three bounded
  criteria are implemented, every local gate is native-pass at the
  implementation head, and the fresh GitHub CI plus CodeQL on the
  implementation head are fully successful (exact run and job
  identities below).
- Repo: `https://github.com/ulfe-lmi/slaif-agent-site`
- Order-specified base: `2ac24ea3ad4047827f4c594185ffa795ccd98853`
  (verified remote main when the order was received)
- Verified base at publication: `1a633f57d828b099111b7b3dc3dc4ceafb9982b0`
  (remote main after PR #122, the separately published Apache pin
  maintenance round, merged; reconciled per the same-order lift
  instruction. The product diff is unchanged relative to the
  order-specified base; the three Apache files are byte-identical to
  the merged maintenance and therefore carry no diff in this PR)
- Implementation head SHA:
  `f4e1a7109c8db5dd6cb1cf23cd5e6f045ca8141f`
  (`oap(083-14-a): retain heading row effects in the immutable
  review`, parent = verified base
  `1a633f57d828b099111b7b3dc3dc4ceafb9982b0`)
- Report publication commit: SELF
- Pushed commits: implementation commit
  `f4e1a7109c8db5dd6cb1cf23cd5e6f045ca8141f` + the report-only
  SELF commit recorded below

## Pushed commits

1. `f4e1a7109c8db5dd6cb1cf23cd5e6f045ca8141f` —
   `oap(083-14-a): retain heading row effects in the immutable
   review` (sole parent: verified base
   `1a633f57d828b099111b7b3dc3dc4ceafb9982b0`).
2. The report-only SELF commit recorded by this publication (sole
   parent: the implementation head; changes only this report).

## What this round implements

Binds the exact recorded `heading-row-effect/v1` facts of reviewed
operations to the immutable review created by the real freeze worker,
and exposes them through the existing authorized human review boundary.

1. **New forward migration `081_001_retained_heading_review_facts`**
   (`services/backend/src/slaif_agent_site/db/alembic/versions/081_001_retained_heading_review_facts.py`,
   new file):
   - Owner-owned `control.heading_review_retention`
     (`schema_version retained-heading-facts/v1`, snapshot binding,
     operation-manifest digest, `fact_count`, `facts_bytes`,
     `facts_digest` over the 070 canonical serialization of the stored
     facts array); `REVOKE ALL ... FROM PUBLIC` and explicit revocation
     from every runtime role — the table stays owner-restricted.
   - Capture definer `control.slaif_review_retain_heading_facts
     (p_workspace_id uuid, p_site_id uuid) -> text` (EXECUTE:
     `slaif_review_worker` only), invoked inside the locked freeze
     transaction after snapshot+companion completion and before job
     `SUCCEEDED`:
     re-resolves the trusted snapshot pointer (COMPLETE + exact
     digest + site + workspace re-bind), re-resolves the companion
     manifest with column-qualified `snapshot_id` predicates and exact
     digest/site/workspace checks, selects only
     `f.operation_id = ANY(reviewed operation_ids)`, requires each
     selected fact to carry the 9-field completion identity
     (operation/family/principal/**resource type**/resource — the
     resource type checked family-specific: `composition_node` for
     `agent`, `editor.sites` for `human_editor`, the existing 083-13-b
     wire values), re-asserts the 16384-octet props image ceiling on
     the selected rows, orders deterministically (`component_id,
     row_version_before, operation_id` — no causal claim across
     unrelated components), and applies, in this order: a 256-record
     budget on the whole site/workspace fact set before selection, a
     total-byte bound on the exact selected records BEFORE
     materialization or aggregation (the UTF-8 codepoint count of each
     selected fact's two props images — a conservative canonical-byte
     lower bound that can never refuse an in-budget set), then the
     1048576 canonical-UTF-8-byte ceiling with a 079-style cheap
     lower-bound pre-check and the authoritative exact canonical
     measurement. Every inconsistency raises a `P0001` class
     (`HEADING_RETENTION_*`) that rolls back the whole freeze.
   - Read definer `control.slaif_review_heading_effects_read
     (p_workspace_id uuid, p_site_id uuid, p_snapshot_id uuid,
     p_user_account_id uuid) -> jsonb` (EXECUTE: `slaif_control` only):
     without `p_snapshot_id` the read follows the trusted workspace
     pointer; with it, the exact requested snapshot row's own
     site/workspace association is checked. Missing retention row →
     `status: unavailable, reason: pre_feature_snapshot` (distinct from
     a captured empty set `status: captured, facts: []`). Uniform
     `P0002` (`REVIEW_READ_UNAVAILABLE`) → 404 on every gate failure.
     Every served record is re-checked at read time against the
     companion's completion identities, including the family-specific
     resource type; the served set never claims every prior workspace
     fact was reviewed.
   - Downgrade: unconditional `HEADING_RETENTION_DOWNGRADE_UNSUPPORTED`
     (`P0001`) — no supported downgrade.
2. **Freeze wiring** (`review_worker/freeze_job.py`): `phase =
   "retention"` between `complete` and `SUCCEEDED` in the same locked
   transaction; all five `HEADING_RETENTION_*` classes map to
   `HEADING_RETENTION_FAILED` terminal job state.
3. **Authorized product read** (`control_api/`):
   `HUMAN_AGENT_WORKSPACE_HEADING_EFFECTS_READ_SQL` +
   `human_agent_workspace_review_heading_effects_read()` (database.py),
   route `GET /api/control/v1/sites/{site_id}/workspaces/{workspace_id}/review/heading-effects/`
   with optional `?snapshot_id=` (workspace_http.py), route-policy
   entry `workspace:read-all` (route_policy.py). Same human membership
   gate, uniform 404 mapping and no-logging behavior as the existing
   review document route.
4. **Operator downgrade preflight** (`bootstrap/service.py`):
   `_assert_no_retained_heading_review_facts_downgrade` runs FIRST in
   `downgrade()` (retention table presence → refuse before any effect);
   the 081 Alembic body is the second line of defense.
5. **Phase-gated privileges** (`db/privileges.py`): the two 081
   functions are granted exactly at or after head 81 (and with an
   unknown head, mirroring the 079 `REVIEWED_OPERATION_BINDING_*`
   pattern); historical-phase databases are not an error. The verifier
   is phase-aware: head ≥ 81 requires both objects with the exact
   grants; a known head < 81 requires their ABSENCE
   (`unexpected-retained-facts-object`).
6. **CI matrix wiring** (`.github/workflows/ci.yml` +
   `tests/repository/test_foundation_ci.py`): the new native module is
   the 9th TC module in the foundation PostgreSQL Group B command
   (runs on all ten PG14–18 matrix jobs).
7. **Public-edge E2E evidence** (`tests/e2e/review-surface.spec.ts`):
   new test `review-surface-retained-heading-effects` inside the
   existing `review-surface` Compose project (the 19-project matrix is
   unchanged): one real heading row created in a real Agent workspace,
   edited once through the Agent API (intermediate value) and once
   through the Human-on-Agent Editor API (final value), real freeze to
   REVIEW, then the retained read through the public NGINX edge:
   current-pointer read verified byte-for-byte against the durable
   retention row (fact_count/facts_bytes/facts_digest), exact
   per-fact shape (9 keys, exact component, row-transition versions
   (1,2)/(2,3), families `agent`/`human_editor`, principal types
   `capability`/`human_user`, before/after props images including the
   intermediate value), named-`snapshot_id` read, cross-workspace and
   unknown-snapshot uniform 404s, captured-empty second workspace,
   nonmember/wrong-site/fresh-workspace uniform 404 matrix, 422
   malformed snapshot id, read side-effect-free fingerprint, and 405
   for non-GET verbs.
8. **Docs**: `docs/SECURITY.md` (retention table owner-restriction,
   definer grants, read-time re-check, uniform 404, log redaction),
   `docs/TESTING.md` (native module + fault test + E2E coverage),
   `docs/OPERATIONS.md` (downgrade refusal + phase-aware privileges),
   oap ledgers (083/14 in flight; 083/13 merged record preserved).

## Contract evidence per item

### 1. Freeze and immutable binding

- `services/backend/tests/integration/test_retained_heading_review_facts.py::test_real_lifecycle_retains_exact_heading_facts`:
  real Agent + Human-on-Agent HTTP edits (two families, one heading,
  intermediate value differing from the final value, final props
  returning to the original), real freeze through the worker pool;
  exact durable bytes asserted: retention row bound to the exact
  snapshot id/digest, site, workspace and operation-manifest digest;
  `fact_count == 3`; each stored record carries the exact 9-field
  completion identity (family/principal/resource) matching the
  trusted completion; before/after props images and row versions
  (1,2),(2,3),(3,4) preserved including the intermediate fact;
  deterministic ordering asserted.
- Pre-publication binding/budget hardening (ROOT pre-publication
  check, same a turn, verified final source):
  (a) the capture now selects and requires the snapshot row's own
  `workspace_id` equal to the bound workspace in addition to
  COMPLETE/digest/site (`HEADING_RETENTION_BINDING`); (b) both
  identity checks (capture per-fact and read-time re-check) now
  require `resource_type` from the stored 079 identity, matched
  family-specific (`composition_node`/`editor.sites`) — the 079
  identity stores all nine keys and the prior draft compared five;
  (c) a total-byte bound over the exact selected records
  (codepoint count of the two props images, a conservative
  canonical-byte lower bound) is enforced BEFORE `jsonb_agg`
  materialization/aggregation, with the post-aggregation exact
  canonical measurement retained as the authoritative gate. The
  full native integration and the public-edge E2E re-ran on the
  corrected source (local verification below).
- Bounded over-budget refusals (record ceiling, per-value 16384-octet
  props image, pre-aggregate total-byte bound, 1 MiB canonical byte
  ceiling with lower-bound pre-check) refuse with `P0001` classes;
  the whole locked freeze transaction rolls back — proven by the
  fixture-only fault instrumentation test (below) and the budget
  probe test.
- `...::test_freeze_retention_fault_rolls_back_whole_locked_transaction`:
  fixture-only fault armed AFTER the real snapshot/manifest staging and
  BEFORE terminal job success; the freeze fails atomically — snapshot
  row, pointer, companion and job state all restored, earlier mutation
  facts intact, and a coherent retry completes the review.

### 2. Read, privacy and compatibility

- `...::test_real_lifecycle_retains_exact_heading_facts` (reopen
  section): the exact retained review is reopened through the
  authorized product read (fresh Control database + client per call)
  after cleanup, after a real human ACCEPT with COW settlement and a
  subsequent same-site publication, and after a real DISCARD with COW
  settlement (separate workspaces); the served facts, digest and
  snapshot identity are byte-identical to the durable row; the
  retained review of the discarded workspace survives the settlement.
- Pre-feature vs captured-empty: `...::test_pre_feature_unavailable_and_captured_empty`
  proves a frozen review with no heading edits serves `captured` +
  `facts: []`, and a staged pre-feature snapshot serves
  `unavailable/pre_feature_snapshot` (distinct envelope, no oracle).
- Uniform unavailable behavior: different site, nonmember, wrong-site
  binding and unknown workspace all get the identical 404 envelope
  (native matrix in the same test); the public edge repeats the matrix
  in the E2E test above.
- Compatibility: old snapshot v1/v2 bytes, render/media, manifests and
  digests are untouched by 081 (no historical DDL beyond the new
  objects); existing accept inputs, approval API, eligibility and
  worker gates are unchanged (the full historical round-trip suite
  passes at the new head — see local verification).
- Privacy: the retention table has no role grants (owner only); the
  read is exposed only through the worker capture definer and the
  control read definer behind the human membership gate; read results
  and errors carry no capability/log material (uniform 404).

### 3. Prove the real lifecycle

- The native lifecycle test (item 1) plus `...::test_retention_read_time_identity_recheck_refuses_divergence`
  (read-time re-check of every served record against the companion
  identities; a diverged stored record is refused uniformly, never
  served) and the E2E public-edge test (item 7) together cover: real
  Agent + Human-on-Agent HTTP, distinct same-heading reviewed
  operations with an intermediate value, real freeze, exact durable
  bytes/identity with trusted completion and the public operation
  set, separate real accept/discard workspaces with real COW
  settlement, reopen after cleanup/publication/fresh connection,
  unavailable-vs-captured-empty, bounded authorization/binding/
  over-budget refusals, and the atomic fault rollback.
- Downgrade preservation/refusal:
  `test_database_bootstrap.py::test_clean_migration_current_repeat_downgrade_and_rebuild`
  (operator preflight refuses at the current 081 head before any
  effect; state exactly as found) and
  `test_heading_row_effects.py::test_facts_authority_boundaries_and_downgrade_ratchet`
  (081 body refuses the first direct step; staged released 080 head
  refuses 080→079 via the 080 body; staged 079 head refuses 079→078
  via the 079 body).

## Diagnostic evidence (preserved)

All logs under `/tmp/oap-083-14-a-control/logs/` (executor-owned,
preserved byte-exact; subjects and outcomes exactly as recorded):

- `full-integration-1.log` — full `pytest
  services/backend/tests/integration -q` on the owned PG18 while the
  phase-gated privileges fix was still incomplete (worker capture
  definer still listed in the unconditional grant set). Native result:
  **64 failed, 406 passed in 4244.23s**. Failure list preserved at
  `full-integration-1-failed.txt`. Tracebacks show two classes:
  (a) `UndefinedFunctionError: control.slaif_review_*... does not
  exist` at historical-head reconciles (the incomplete phase gating),
  and (b) current-head pins at `080_001` asserting the pre-081 head.
- `rerun64-1.log` — first focused rerun of the exact 64 on a partially
  fixed tree; 21 of the first 23 tests still failed with
  `UndefinedFunctionError: control.slaif_review_retain_heading_facts
  (uuid, uuid) does not exist`, isolating the residual unconditional
  grant entry (stop was a controlled stop; the log is preserved as
  partial adverse evidence).
- Teardown incident (environmental, not product): the stopped rerun's
  in-flight fixture never finalized, leaving one disposable test
  database plus its eleven `fixture_*` login roles; the two following
  single-test runs failed ONLY at the shared product-role drop
  (`DependentObjectsStillExistError`, privileges for the abandoned
  database). The abandoned database and the eleven exact fixture login
  roles (verified: created by that run, no active sessions) were
  removed; an 8x single-test loop then passed cleanly
  (`teardown-loop-1..8.log`, all `1 passed`). No product change
  resulted.
- `rerun64-2.log` — focused rerun of the exact 64 previously failed
  tests on the final code: **64 passed in 639.10s, native 0**.
- `local-compose-1.log` — a local Compose smoke that, due to a
  command-construction error, ran against the wrong checkout (a
  pre-existing separate working tree, not this round's subject). It
  was stopped and its stack torn down before any state-changing
  stage beyond the read-only e2e matrix; the canonical tree was
  verified unmodified by the run. Not evidence for this round.
- `local-compose-2.log` — correct checkout, first draft of the new
  E2E test: the test executed and failed at
  `expect(Number(countA)).toBeGreaterThan(0) | Received: 0` —
  component CREATION alone records no 080 heading row effect (the
  recorder observes heading ROW transitions). Honest diagnostic; the
  test flow was corrected to real component updates (Agent + Editor
  PATCHes) and the static gates re-run green.
- `local-compose-3.log` — correct checkout, second draft of the new
  E2E test: the side-effect-free fingerprint assertion failed because
  its baseline was taken before the second workspace's own freeze
  (`4|4|4` vs `5|5|5`). Honest diagnostic; the baseline moved to
  immediately before the read loop and the static gates were re-run
  green.
- `local-compose-4.log` — first full run of the final code plus final
  E2E test (pre-reconciliation base): all 19 E2E projects **PASSED**
  (including `review-surface-retained-heading-effects` through the
  public NGINX edge), media-e2e, governance-e2e and every post-E2E
  stage OK. The run then exited non-zero at its final stage — a clean
  rebuild of the pre-existing Apache edge image — because the
  base-main pin `apache2=2.4.58-1ubuntu8.19` had been superseded by
  `2.4.58-1ubuntu8.20` in the official Ubuntu noble archive.
  `infra/` was byte-identical to the verified base for this round, so
  the failure is upstream archive drift, not this round's diff. That
  pin repair was scope-stopped as maintenance under the November 26
  rhythm and was published separately as PR #122 (merged at verified
  main `1a633f57d828b099111b7b3dc3dc4ceafb9982b0`); this PR carries
  no Apache-file diff.
- Reconciliation of the same checkout to the verified main
  `1a633f57` (same-order lift): the pre-reconciliation worktree was
  preserved byte-exact on a local-only backup ref; the branch was
  reset to the verified main and exactly the 33 product paths were
  restored (30 modified + 3 new). The three local Apache trial files
  were verified byte-identical to the merged #122 maintenance and
  were dropped from the product diff. The order file (SHA256
  `ed7792bc602bcd76cd60d95d1fad46059905d70a9f0e7b054a58e98363d49368`)
  and `oap/active` (`083-14-a`) are byte-exact on the new base.
- `local-compose-5-mislaunched-path.log` — a smoke launch whose
  environment PATH lacked the pinned Node toolchain
  (`pnpm: not found`); stopped before any state-changing stage.
  Launcher error, not product evidence.
- `full-integration-3.log` / `local-compose-7.log` — full
  integration (owned PG18) and full Compose launches started BEFORE
  the ROOT pre-publication 081 correction landed, i.e. on the
  pre-correction source. Both were stopped (integration after
  repeated SIGINT deferral by in-flight asyncpg waits, verified exact
  child SIGKILL; compose at the `up --wait` stage) so that final
  evidence can run on the corrected source; both logs are preserved
  as partial diagnostic runs. The integration stop left one exact
  abandoned per-test fixture on the owned PG18
  (`slaif_test_9a88608277` plus its eleven `fixture_*` login roles,
  verified: created by that run, zero active backends) which was
  dropped; the owned fixture was re-verified clean (zero
  `slaif_test_%` databases, zero `fixture_*` roles) before the final
  runs started. No product change resulted.
- `local-compose-4.log` Apache drift root cause (see above) and
  `local-compose-6.log` (full `compose-smoke: OK` on the reconciled
  tree, pre-081-correction backend image — superseded by
  `local-compose-8.log`) are preserved as labeled diagnostics.

## Local verification at the implementation head

Owned disposable PostgreSQL 18 on `[::1]:5432` (single serial runner
at a time), uv 0.12.5, frozen installs:

- `uv run --frozen pytest services/backend/tests/integration -q`
  (final code, pre-reconciliation base, `full-integration-2.log`):
  **470 passed in 4087.38s (1:08:07), native 0** — zero
  failed/error/traceback lines in the preserved log.
- `uv run --frozen pytest services/backend/tests/integration -q`
  (FINAL corrected source on the verified `1a633f57` base, owned
  PG18, `full-integration-4.log`): **470 passed in 4251.28s
  (1:10:51), native 0** — zero failed/error/traceback lines in the
  preserved log.
- Static gates re-run on the reconciled tree
  (`final-static-reconciled.log` / `final-static-reconciled2.log` /
  `final-static-reconciled3b.log` / `final-static-reconciled4.log`),
  then re-run after the pre-publication 081 correction
  (`final-static-corrected.log`), all native 0:
  `uv lock --check`, `uv sync --frozen --all-groups`, `ruff check`,
  `ruff format --check`, `mypy` (no issues), `uv build`, all ten
  process smokes `CHECK_OK`, `compileall`, `unittest discover
  tests/repository`, `tools/check_repository.py` (the post-#122
  policy), `tools/check_mermaid.py` (16 diagrams), markdownlint (0
  issues), `pnpm lint` / `pnpm format:check` / `pnpm typecheck`.
- `uv run --frozen pytest services/backend/tests/unit tests/repository
  -q` (reconciled tree, including the #122 policy tests): **910
  passed, 29 subtests passed in 33.14s, native 0** (re-confirmed
  after the 081 correction).
- `uv run --frozen ruff check services/backend tests/repository
  tools`: all checks passed; `uv run --frozen ruff format --check ...`:
  all formatted (`static gates this session`).
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: success
  (`static-final-build.log`).
- Ten process smokes (`uv run --frozen python -m
  slaif_agent_site.<service> --check`): all `CHECK_OK`
  (`static-final-smokes.log`).
- Preparation checks: `python3 -m compileall -q tools
  tests/repository` rc 0; `python3 -m unittest discover -s
  tests/repository -p 'test_*.py'` OK rc 0; `python3
  tools/check_repository.py` rc 0; `python3 tools/check_mermaid.py` rc
  0 (`static-final-prep.log`).
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: **0 issues in 0
  files (648 linted)** (`static-final-markdownlint.log`).
- Node frozen gate (Node 24.22.1, pnpm 11.22.0): `pnpm lint` rc 0,
  `pnpm format:check` rc 0, `pnpm typecheck` rc 0 — includes
  `tsc --project tests/e2e/tsconfig.json --noEmit` covering the new
  E2E test (`static-final-node-lint.log`,
  `static-final-node-format.log`, `static-final-node-typecheck.log`).
- The Apache pin drift repair identified during this round was
  scope-stopped under the November 26 rhythm and published
  separately as PR #122 (merged at verified main
  `1a633f57d828b099111b7b3dc3dc4ceafb9982b0`); this PR carries no
  Apache-file diff. The local diagnosis remains on record: the
  current exact archive version was `2.4.58-1ubuntu8.20`
  (`apt-cache policy` inside the exact
  `ubuntu:24.04@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517`
  base image, in both noble-updates and noble-security), with the
  `openssl=3.0.13-0ubuntu3.16` and `apt=2.8.4ubuntu0.1` pins still
  current, verified by a clean `docker build -f
  infra/apache/Dockerfile` (39s; `apachectl -t` -> `Syntax OK`) and
  the packaging unit contract (9/9 OK, including
  `test_apache_qualification_is_exact_and_uses_fixed_ubuntu_packages`).
- `sh tools/compose/smoke.sh slaif00714d` (local Compose through
  NGINX, final code + final E2E; `local-compose-4.log`): all 19 E2E
  projects PASSED including
  `review-surface-retained-heading-effects`; media-e2e, governance-e2e
  and the post-E2E tail OK; run exit non-zero only at the pre-existing
  Apache image rebuild (upstream pin drift, above).
- `sh tools/compose/smoke.sh slaif00714e` (full local Compose run on
  the reconciled tree whose Apache files are the merged #122
  maintenance; `local-compose-6.log`): **`compose-smoke: OK`** —
  all 19 E2E projects PASSED (including
  `review-surface-retained-heading-effects`), media-e2e,
  governance-e2e, Apache `apachectl -t` `Syntax OK`, and 77/77
  packaging tests OK. NOTE: this run's backend image predates the
  pre-publication 081 correction and is superseded by the final run
  below.
- `sh tools/compose/smoke.sh slaif00714g` (clean full local Compose
  run on the FINAL corrected source; `local-compose-8.log`):
  **`compose-smoke: OK`** — all 19 E2E projects PASSED (including
  `review-surface-retained-heading-effects`), media-e2e and
  governance-e2e OK, Apache `apachectl -t` `Syntax OK`, and
  77/77 packaging tests OK.

## GitHub CI evidence

All at the implementation head
`f4e1a7109c8db5dd6cb1cf23cd5e6f045ca8141f` (the PR head at run
start; the report-only commit changes no product bytes):

- CI run 46018198291 (`CI` workflow): **completed success** — every
  job `pass`:
  Foundation PG Group A PostgreSQL 14/15/16/17/18 (5m47s–10m10s),
  Foundation PG Group B PostgreSQL 14/15/16/17/18 (14m23s–24m1s;
  Group B carries the 9-module native command including the new 081
  retained-heading module), Foundation PostgreSQL 14/15/16/17/18
  aggregators, Compose and edge packaging (18m11s; the 19-project
  E2E matrix including
  `review-surface-retained-heading-effects`), Supply-chain evidence
  (13m43s; six-image build/scan), Python 3.12/3.13/3.14 quality and
  package, Markdown, Mermaid, Node contracts, Repository policy,
  Dependency review.
- CodeQL run 46018198274: **completed success** —
  Analyze (actions), Analyze (javascript-typescript), Analyze
  (python) all pass.
- PR 123 check rollup at the implementation head: `gh pr checks 123`
  reports 30 check runs, all `pass`, zero failures or pending; the
  PR remains OPEN/DRAFT — acceptance and merge belong to ROOT
  alone.

### Limits (GitHub)

- This report records the state observed for the literal
  implementation head before the report commit; the report push may
  trigger fresh CI on the report head, which strategy independently
  waits/verifies. Pending/missing/cancelled/failed is never reported
  as success.
- The Compose, supply-chain and matrix subjects above are the exact
  run and job identities at the implementation head; ROOT
  independently verifies them on final SELF.

## Exact changed paths (33)

The three Apache files
(`infra/apache/Dockerfile`, `supply-chain/policy.json`,
`tests/packaging/test_oci_contract.py`) are byte-identical to the
merged #122 maintenance on the base and therefore carry NO diff in
this PR.

Modified (30): `.github/workflows/ci.yml`, `docs/OPERATIONS.md`,
`docs/SECURITY.md`, `docs/TESTING.md`, `oap/INCREMENTS.md`,
`oap/MVP-PROGRESS.md`, `oap/active`
(byte-exact active pointer),
`services/backend/src/slaif_agent_site/bootstrap/service.py`,
`services/backend/src/slaif_agent_site/control_api/database.py`,
`services/backend/src/slaif_agent_site/control_api/route_policy.py`,
`services/backend/src/slaif_agent_site/control_api/workspace_http.py`,
`services/backend/src/slaif_agent_site/db/privileges.py`,
`services/backend/src/slaif_agent_site/review_worker/freeze_job.py`,
`services/backend/tests/integration/test_agent_page_style.py`,
`services/backend/tests/integration/test_cache_outbox_consumer.py`,
`services/backend/tests/integration/test_control_database_integration.py`,
`services/backend/tests/integration/test_database_bootstrap.py`,
`services/backend/tests/integration/test_editable_domain_proof.py`,
`services/backend/tests/integration/test_heading_row_effects.py`,
`services/backend/tests/integration/test_human_agent_session_control.py`,
`services/backend/tests/integration/test_media_workspace_privileges.py`,
`services/backend/tests/integration/test_real_human_discard.py`,
`services/backend/tests/integration/test_reviewed_operation_binding_authority.py`,
`services/backend/tests/integration/test_trusted_completion_upgrade_preservation.py`,
`services/backend/tests/unit/test_control_database.py`,
`services/backend/tests/unit/test_foundation_contract.py`,
`services/backend/tests/unit/test_health_apps.py`,
`services/backend/tests/unit/test_route_policy.py`,
`tests/e2e/review-surface.spec.ts`, `tests/repository/test_foundation_ci.py`.

New (3):
`oap/orders/083-14-a-retained-heading-review-facts.md` (byte-exact
order, 133 lines),
`services/backend/src/slaif_agent_site/db/alembic/versions/081_001_retained_heading_review_facts.py`
(672 lines, including the pre-publication hardening),
`services/backend/tests/integration/test_retained_heading_review_facts.py`
(1459 lines).

## Scope, secrets, production, skips, extra PR, no-merge

- Scope: exactly the active 083-14-a contract; one forward migration
  (including the same-turn pre-publication hardening ordered by
  ROOT: snapshot workspace binding in the capture, the
  family-specific `resource_type` identity check in both manifest
  identity comparisons, and the pre-aggregate total-byte bound on
  the selected records), freeze/read wiring, phase-gated
  privileges, in-scope head-bump test maintenance for the new head
  (current-head pins, the 081 preflight/body refusal ordering in two
  downgrade-ratchet tests, and the CI TC-module count), truthful
  docs, and the E2E public-edge test. No other product behavior
  changed. The Apache pin repair is NOT in this diff (separate
  merged PR #122); the implementation is the 33 product paths on
  the verified `1a633f57` base.
- No new actor authority: stored facts stay owner-restricted; the only
  new EXECUTE grants are the worker capture definer and the control
  read definer, phase-gated, with no PUBLIC grants and no raw
  retention-table SELECT for any runtime role.
- The pre-existing Apache pin drift (upstream noble archive
  superseded `2.4.58-1ubuntu8.19` while this round was in flight,
  breaking the pre-existing Apache image build for every checkout)
  was diagnosed locally with exact archive evidence, then
  scope-stopped as maintenance under the November 26 rhythm and
  published separately as PR #122 (merged). This diff contains no
  packaging, pin, scanner, policy-logic or image-structure change.
- No dependency refresh, scanner change, foundation upgrade, private
  foundation SQL, generalized history, first-touch reconstruction,
  causal closure, selection, re-review lifecycle changes, MCP/renderer
  or release changes.
- No secret material in code, fixtures, logs or this report; fixture
  credentials live only in test process environments; negative-path
  tests use test voice.
- No production systems, data or credentials were touched; only
  explicitly owned disposable resources (owned PG18 fixture, owned
  Compose projects on this VM, owned Docker images).
- No skipped, missing or blocked gate is claimed as passed; every
  diagnostic failure above is recorded with its preserved log and the
  exact subsequent green rerun subject.
- Exactly ONE draft PR for this increment; no merge, auto-merge, force
  push, history rewrite or second PR.

## Known limitations

- The E2E public-edge test exercises the retained read through NGINX
  in the Compose matrix (local + CI); deeper browser render variants
  of the review document are unchanged and remain covered by the
  pre-existing review-surface/freeze/frozen-parity projects.
- Retention captures heading row effects of reviewed operations only
  (the order's bounded contract); non-heading content changes and
  non-reviewed operations remain outside the retained set by design.
