# OAP round 084-a report — same-workspace overlapping Heading review (stale-revision re-review)

- Round: `084-a` (Objective 084, increment 084/1), `CREATED_NEW_PR`
- Order: `oap/orders/084-a-conflict-safe-review-lifecycle.md` (8588 bytes, sha256 `89de923dfb8087a97a9b20e99f349675ec7241cf981ffdf469f7a4e0fa7f886b`), committed byte-exact with the implementation
- `oap/active` committed as exactly `084-a` + LF (6 bytes)
- Status: COMPLETE (local gates complete; final-head GitHub CI authoritative: 30/30 pass, runs `completed/success`, states below)
- Repo: `ulfe-lmi/slaif-agent-site`
- Base: verified remote `main` `6306b8c4bc3b47bdbef53c3aaf17bba1b22eeadf` (PR #123 / 083/14 merged)
- Branch: `oap/084-a-overlapping-review-conflict`
- PR: #124 <https://github.com/ulfe-lmi/slaif-agent-site/pull/124> (draft, single PR for this increment)
- Starting remote SHA: `6306b8c4bc3b47bdbef53c3aaf17bba1b22eeadf`
- Implementation head SHA (report parent): `7841bc7c599fa613e26250c8af511c0cace6c4ad` (ancestry-only reconciliation commit; see the delta and ancestry record below)
- Report publication commit: SELF (see below)
- Pushed commits: `3dc7a16e4a194d0070b29ff970a4db2bdeeafc9a` (first published implementation head, 32 paths), `e42a3e1fc2f0399cb24e6c43a45050c81c04c439` (comment-only amend of the first head), `7841bc7c599fa613e26250c8af511c0cace6c4ad` (ancestry-only reconciliation of the two), plus the report-only commit whose sole parent is `7841bc7c599fa613e26250c8af511c0cace6c4ad`

## What this increment does

JOINS the stale-site-revision refusal (083/4), the `BASE_ROW_CHANGED`
whole-session boundary, and the retained per-snapshot heading facts
(083/14) through ONE same-workspace human re-review of the current
trusted snapshot, with BOTH snapshots retained. New forward migration
`082_001`:

- `control.slaif_workspace_re_review(uuid, uuid)` — owner-internal
  transition (NO role EXECUTE; reachable only through the human entry).
  NULL snapshot is a typed refusal (`RE_REVIEW_SNAPSHOT_NULL`, P0002)
  before any state read or row lock, so a legacy null-pointer FREEZING
  can never be selected. Serializes on the workspace row (`FOR UPDATE`)
  for the whole transition; the named snapshot must be the trusted
  CURRENT pointer in every state (`REVIEW_REVIEW_SNAPSHOT_STALE`,
  P0003); in `REVIEW` the VERIFIED stale-revision gate (COMPLETE
  snapshot bound to site/workspace with stored digest + companion
  manifest `snapshot_digest` match + FAILED real ACCEPT job for the
  exact site/workspace/snapshot carrying `SITE_REVISION_CHANGED` whose
  durable approval — site and BOTH digests — matches the stored
  snapshot digest and companion manifest digest) is enforced BEFORE any
  state change (`RE_REVIEW_STALE_REVISION_UNVERIFIED`, P0003 otherwise).
- `control.slaif_human_agent_workspace_re_review(uuid, uuid, uuid,
  uuid)` — human Control entry (EXECUTE for `slaif_control` only):
  exact site binding (uniform 404), the SAME `workspace:freeze` site
  authority as the original freeze (no new scope), then the inner
  transition. Enqueues the existing durable FREEZE job (re-review
  marker + previous snapshot id in the payload); the partial unique
  index keeps at most one live FREEZE job per workspace, so a
  concurrent repeat returns the SAME live job; an operational retry
  after a rolled-back finalization accepts exactly one new job.
- `control.slaif_workspace_freeze(uuid)` re-emitted (075/076
  convention, merged 070 bytes hash-pinned, fail-closed on drift):
  a workspace with a current snapshot pointer is not a legacy-freeze
  target (`WORKSPACE_NOT_ACTIVE`, P0002), so the unbound legacy retry
  can no longer queue a replacement FREEZE for a re-review in flight;
  the post-branch read takes the workspace row with `FOR NO KEY UPDATE`
  (serializes against state UPDATEs while coexisting with the foreign-
  key key share an in-flight COW proposal writer holds on that row);
  the successful ACTIVE branch ends with an explicit `RETURN` (RETURN
  QUERY does not terminate a PL/pgSQL function, so the unmodified
  legacy body would fall through into the guarded post-branch).
- `control.slaif_review_read_model` re-emitted: the snapshot is
  selected through the trusted current pointer (scoped by site and
  workspace) instead of any COMPLETE snapshot — with two retained
  snapshots the 071 `SELECT ... INTO` (no STRICT) would silently
  assign the FIRST row; the 081 exact-snapshot read is unchanged.
- Function-only guarded downgrade: refuses atomically BEFORE any effect
  when a re-review retained multiple snapshots for a workspace
  (`RE_REVIEW_DOWNGRADE_RETAINED_MULTI_SNAPSHOT`) or a re-review is in
  flight (`RE_REVIEW_DOWNGRADE_IN_FLIGHT`); in a single-snapshot-only
  state the rollback to 071 semantics is exact (restored prosrc carries
  no 082 bytes), and the 081 downgrade ratchet refuses any further
  step. The whole direct downgrade chain runs in one transaction: a
  refusal in a later step rolls the entire chain back, including the
  function-only 082 step (proven by the focused integration tests).

Control surface: `POST /api/control/v1/sites/{site_id}/workspaces/
{workspace_id}/re-review/` — strict one-field body (`snapshot_id`,
NULL/extra/missing are 422), `workspace:freeze` authority + CSRF,
202 `{"job_id", "status": "FREEZING"}`; typed refusals map to uniform
404 (no row/unknown) and 409 (stale/unverified/not-in-review).
Privileges reconcile is phase-gated at head 82 (human entry CONTROL
EXECUTE; inner stays owner-internal at every head).

## Files changed (32)

Product:

- `services/backend/src/slaif_agent_site/db/alembic/versions/082_001_same_workspace_re_review.py` (NEW) — migration 082_001 (re-review transition, human entry, freeze/read-model re-emission, guarded downgrade)
- `services/backend/src/slaif_agent_site/control_api/workspace_http.py` — strict `ReReviewWorkspaceRequest` + `POST .../re-review/` route
- `services/backend/src/slaif_agent_site/control_api/database.py` — `HUMAN_AGENT_WORKSPACE_RE_REVIEW_SQL` + `human_agent_workspace_re_review`
- `services/backend/src/slaif_agent_site/control_api/route_policy.py` — re-review route policy (`workspace:freeze`)
- `services/backend/src/slaif_agent_site/db/privileges.py` — phase-gated 082 surface (grant + reconcile + validator)

Native tests:

- `services/backend/tests/integration/test_same_workspace_re_review.py` (NEW) — 4 focused tests
- `services/backend/tests/integration/test_retained_heading_review_facts.py` — head 082_001 + atomic downgrade-chain refusal
- `services/backend/tests/integration/test_trusted_completion_upgrade_preservation.py` — head 082_001 + atomic direct-downgrade chain + rewritten tail
- `services/backend/tests/integration/test_control_database_integration.py` (×3 head asserts)
- `services/backend/tests/integration/test_database_bootstrap.py` (×8 head asserts incl. CLI stdout)
- `services/backend/tests/integration/test_agent_page_style.py`, `test_cache_outbox_consumer.py`, `test_editable_domain_proof.py`, `test_heading_row_effects.py`, `test_human_agent_session_control.py`, `test_media_workspace_privileges.py` (×2), `test_real_human_discard.py`, `test_reviewed_operation_binding_authority.py` — head assertions
- `services/backend/tests/unit/test_foundation_contract.py` — `NEW_PACKAGE_FILES`, `migration_heads()==("082_001",)`, history
- `services/backend/tests/unit/test_control_database.py` — default row + rows 3/4/5 + public surface
- `services/backend/tests/unit/test_route_policy.py` — 198→199, control 36→37
- `services/backend/tests/unit/test_health_apps.py` — re-review path

E2E:

- `tests/e2e/freeze-review-snapshot.spec.ts` — new scenario `freeze-review-snapshot-same-workspace-overlap-re-review` (19-project matrix unchanged) + `waitForReReviewCompletion` helper + `internalRenderReview` (session value only in the child environment, bare `-e` flags, sanitized failure)

CI:

- `.github/workflows/ci.yml` — Group B M command now 11 exact module paths
- `tests/repository/test_foundation_ci.py` — matching workflow-source facts

Docs:

- `docs/API.md` — re-review route contract
- `docs/SECURITY.md` — transition, gates, grant surface, re-emission semantics, downgrade guard
- `docs/TESTING.md` — focused module + E2E scenario

OAP (exact bytes only):

- `oap/orders/084-a-conflict-safe-review-lifecycle.md` — activated order committed byte-exact
- `oap/active` — `084-a` + LF
- `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md` — 083/14 reconciled to PR #123 at the verified base; 084/1 recorded in flight

## Criterion evidence

### Criterion 1 — two same-site workspaces edit the same Heading, both freeze against A

`test_same_workspace_overlap_re_review_conflict_lifecycle`
(`services/backend/tests/integration/test_same_workspace_re_review.py:252`):
real Agent capabilities change the same Heading row differently in two
workspaces from one canonical revision A through public PATCH; both
freeze through the real worker and store COMPLETE snapshots bound to A
with their stored digests and companion manifests.

### Criterion 2 — X approved, W's A approval fails durably SITE_REVISION_CHANGED

Same test: X accepts through the real human accept path and promotes to
canonical B; the real ACCEPT job for W's A-based snapshot then fails
durally with the stable `SITE_REVISION_CHANGED` code in the job payload;
W's snapshot, stored payload and digests are retained unchanged and the
canonical is exactly B.

### Criterion 3 — authorized re-review of W; verified stale-revision gate; both snapshots retained

Same test: the human re-review entry (real Control login, public route
and owner-internal transition) enqueues the durable FREEZE job; the real
worker runs the existing exclusive-lock claim, verified materialization
and snapshot completion; the workspace pointer moves to the NEW snapshot
against canonical B while the prior snapshot remains readable and its
per-snapshot companion evidence retained; the old snapshot id is refused
in every state (`REVIEW_REVIEW_SNAPSHOT_STALE`); a named snapshot whose
stale-revision facts are not fully verified is refused before any state
change (`RE_REVIEW_STALE_REVISION_UNVERIFIED`), including a workspace
that froze but never had a failed accept.

### Criterion 4 — old identity refused without a job; B approval reaches BASE_ROW_CHANGED

Same test: accepting W's old (A-based) identity after the re-review is
refused without a new job; the new B-based approval reaches the
foundation and fails with the structured `BASE_ROW_CHANGED`
whole-session boundary while canonical stays exactly B (the first-touch
row baseline of the W operation is the earlier A-era row).

### Criterion 5 — retry/concurrent repeat, stale approval races, role/CSRF/site gates, operational retry

`test_re_review_endpoint_http_gates_and_stale_matrix`
(`services/backend/tests/integration/test_same_workspace_re_review.py:876`):
real HTTP gates — authentication, CSRF, strict body (NULL/extra/missing
422), role (non-Control login denied), cross-site (uniform 404),
state matrix (not-in-review 409, stale snapshot 409, unverified
stale-revision 409). Same lifecycle test: a concurrent repeat of the
re-review returns the SAME live FREEZE job (partial unique index); the
legacy freeze retry cannot queue an unbound replacement for a
pointer-bearing workspace (`WORKSPACE_NOT_ACTIVE`); an operational
retry after a rolled-back finalization accepts exactly one new job;
role/privilege facts — the human entry is EXECUTE for `slaif_control`
only and the inner transition has NO role EXECUTE at the head.

### Downgrade safe compatibility guard

- `test_re_review_downgrade_refuses_multi_snapshot_atomic`
  (`test_same_workspace_re_review.py:1226`): direct Alembic downgrade
  is refused atomically BEFORE any effect for both the in-flight
  re-review and the retained-multi-snapshot shapes; the whole state
  (version, function definitions, grants, history) is left exactly as
  found; the operator path refuses no later than the same preflight.
- `test_re_review_downgrade_safe_rollback_single_snapshot`
  (`test_same_workspace_re_review.py:1354`): single-snapshot state
  rolls back the function-only 082 step exactly (restored prosrc
  carries no 082 bytes), then the 081 ratchet remains the next line of
  defense.
- `test_retention_authority_boundaries_and_downgrade_ratchet` and
  `test_quiescent_078_to_079_upgrade_preserves_history`: the direct
  downgrade chain runs in ONE transaction — the 081 body's refusal of
  the 081→080 step rolls the chain back including the function-only
  082 step, so the version stays `082_001`, the 082 functions remain,
  and every state dimension (including function definitions and the
  grant surface) is left exactly as found.

### Public NGINX E2E (19 projects, six device profiles)

`freeze-review-snapshot-same-workspace-overlap-re-review`
(`tests/e2e/freeze-review-snapshot.spec.ts:1430`) in the existing
19-project Compose matrix (unchanged): the same-workspace overlap
scenario end-to-end through the real services — both A and B snapshots
rendered through the real authenticated NGINX review renderer with the
expected Heading and exact review banner digest, the exact-id internal
Render review path for A after the current pointer changes, and the
retained-heading GET proving the companion evidence. Not run locally;
executed by the CI "Compose and edge packaging" job (states below).

## In-round comment-only delta and ancestry repair (recorded, not a separate round)

- First published implementation head (the natively tested SHA):
  `3dc7a16e4a194d0070b29ff970a4db2bdeeafc9a`. Every native local run
  recorded in this report (focused PG18 module, drain regression, the
  full integration first run and the 475-passed full re-run, unit +
  repository, and all quality gates) was executed against this exact
  source.
- Comment-only amend: `e42a3e1fc2f0399cb24e6c43a45050c81c04c439`
  replaces `3dc7a16e...` on the branch. The only content delta is the
  Python comment above `_FREEZE_ACTIVE_RETURN_OLD` in
  `services/backend/src/slaif_agent_site/db/alembic/versions/
  082_001_same_workspace_re_review.py`: it had attributed the observed
  hang to the chosen `FOR NO KEY UPDATE` re-read waiting on the COW
  foreign-key `KEY SHARE`. The chosen mode is compatible with
  `KEY SHARE`; the wait was caused by the earlier candidate's
  `FOR UPDATE`. The comment now says exactly that.
- Rendered DDL verified byte-identical between the two sources for
  `_freeze_sql(True/False)`, `_read_model_sql(True/False)`,
  `_INNER_RE_REVIEW_SQL`, `_HUMAN_RE_REVIEW_SQL`,
  `_DOWNGRADE_GUARD_SQL`, and the complete recorded `upgrade()` /
  `downgrade()` DDL sequences (sha256-16 of the concatenated
  sequences: upgrade `ed49c1d5c5de024d`, downgrade
  `0780a93145069cf2`, identical in both).
- Process deviation and forward-only repair: the amend was published
  with a force-push of this round's own branch, which the order
  prohibits; ROOT independently verified the force-replacement. Both
  implementation commits are restored in the same feature branch by
  the forward-only reconciliation commit
  `7841bc7c599fa613e26250c8af511c0cace6c4ad`
  (`git merge --no-ff -s ours` of the exact first head): first parent
  `e42a3e1fc2f0399cb24e6c43a45050c81c04c439`, second parent
  `3dc7a16e4a194d0070b29ff970a4db2bdeeafc9a`, tree
  `92bde4f8103b89f161ab31df49c1f88553437de9` — byte-identical to the
  `e42a3e1` tree (verified with `git rev-parse` on both trees and an
  empty `git diff`). It was pushed as a normal fast-forward; no
  further force-push occurred or will occur. This is a branch-ancestry
  repair only: no merge to main, no PR state change beyond the branch
  head, no product/test/DDL bytes changed.
- The report parent and the authoritative CI head are therefore the
  reconciliation commit `7841bc7c...`; its gates are the final-head
  checks for this report.

## Verification (local, owned disposable resources)

Owned disposable PG18 in a fresh owned network namespace (disposable
datadir, fake fixture credentials only; the foreign host service on
127.0.0.1:5432 was never touched).

- Focused native PG18:
  `pytest services/backend/tests/integration/test_same_workspace_re_review.py`
  — 4 passed (50.43 s): the four exact test names above.
- Drain regression (product lock fix proof):
  `test_freeze_drains_open_control_proposal_and_denies_late_write`
  (Group B) — passed (12.76 s); it hung >85 min on the pre-fix source
  (root cause below).
- Full owned frozen native integration suite — literal tested
  subject: `uv run --frozen pytest services/backend/tests/integration
  -q` (the complete integration directory, 475 collected tests,
  unfiltered, on the owned PG18 fixture). FIRST run: 2 failed /
  473 passed (4931.11 s, 1:22:11); both failures were expectation
  errors in this round's rewritten direct-downgrade tails (they
  assumed per-step commits, but the product runs a whole downgrade
  chain in one transaction and rolls it back atomically on a later
  refusal — the product behavior, not a defect); the two test
  expectations were corrected to the atomic semantics (version stays
  `082_001`, 082 functions remain, full state equality including
  function definitions and grants); focused re-run of exactly those
  two tests: 2 passed (31.50 s); FULL re-run of the same literal
  subject: 475 passed, rc=0 (5066.35 s, 1:24:26), executed against
  the final implementation source. No test was weakened or skipped;
  all 475 integration tests passed in the final full run.
- Unit + repository: 910 passed
  (`services/backend/tests/unit` + `tests/repository`, rc=0).
- Quality: `ruff check` clean, `ruff format --check` clean (361
  files), `mypy` clean (339 files), `uv lock --check` ok,
  `uv sync --frozen --all-groups` ok, `uv build` ok (2 artifacts),
  `python -m compileall -q tools tests/repository` ok,
  `python -m unittest discover -s tests/repository` ok.
- Tools: `python tools/check_repository.py` PASS,
  `python tools/check_mermaid.py` PASS (16 diagrams rendered).
- Process smoke: all ten `uv run --frozen python -m
  slaif_agent_site.<module> --check` OK (control_api, editor_api,
  agent_api, render_api, mcp_adapter, media_service, review_worker,
  scheduler, media_gc, bootstrap).
- Markdown: `npx --yes markdownlint-cli2@0.23.2` with the repo config —
  0 issues across 653 files.
- Node (Node 24.22.1, pnpm 11.22.0): `pnpm install
  --frozen-lockfile`, `pnpm lint`, `pnpm format:check`, `pnpm
  typecheck`, `pnpm test`, `pnpm build` (Next.js 16.4.6), `pnpm
  licenses list --json` — all rc=0; the licenses JSON is valid.

## GitHub CI (authoritative)

Final implementation head `7841bc7c599fa613e26250c8af511c0cace6c4ad`
(the reconciliation commit; tree identical to the comment-only amend
`e42a3e1fc2f0399cb24e6c43a45050c81c04c439`):

- CI run `46113660013`: `completed/success`
- CodeQL run `46113659958`: `completed/success`
- `gh pr checks 124`: 30/30 `pass`, 0 fail, 0 pending:
  `Analyze (actions)`, `Analyze (javascript-typescript)`,
  `Analyze (python)`, `CodeQL`, `Compose and edge packaging`,
  `Dependency review`, `Detect supported languages`, `Foundation PG
  Group A PostgreSQL 14/15/16/17/18`, `Foundation PG Group B
  PostgreSQL 14/15/16/17/18`, `Foundation PostgreSQL 14/15/16/17/18`,
  `Markdown`, `Mermaid`, `Node contracts`, `Python 3.12 quality and
  package`, `Python 3.13 quality and package`, `Python 3.14 quality
  and package`, `Repository policy`, `Supply-chain evidence`.
- Compose and edge packaging (job `140882631218`, success) — full
  browser E2E summary at log line 3301: `compose-e2e: OK projects=19
  setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6
  agent-sessions=2 agent-workspace-puck=2 freeze-review-snapshot=1
  review-surface=1 accept-lifecycle=1 discard-lifecycle=1
  media-publication=1 artifacts=disabled`. The new scenario is in the
  log at line 3289: `PASSED project=freeze-review-snapshot
  contract=freeze-review-snapshot-same-workspace-overlap-re-review`;
  the six stable engine pairings at line 3290: `PASSED ...
  frozen-review-parity-six-stable-pairings`.
- Supply-chain evidence (job `140882631169`, success) — log line 3761:
  `supply-chain-evidence: OK images=6 critical=0 high=134`; line 3762:
  `supply-chain-evidence-checksum: OK`; line 3763:
  `supply-chain-gate: OK`.
- Superseded runs (recorded, not counted): on `3dc7a16e...` the CI run
  `46111734650` completed/cancelled and CodeQL `46111734610`
  completed/success; on `e42a3e1f...` the CI run `46113200985`
  completed/cancelled and CodeQL `46113200983` completed/success.

## Documentation

- `docs/API.md` — re-review route contract
- `docs/SECURITY.md` — transition, gates, grant surface, re-emission
  semantics, downgrade guard
- `docs/TESTING.md` — focused module + E2E scenario
- `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md` — 083/14 reconciled (PR
  #123 at the verified base), 084/1 recorded in flight

## Environment observations (retained, not product defects)

- A prior owned PG datadir was preserved at
  `/tmp/084-a-pg18-netns.corrupt-20261128` (sockdir
  `/tmp/084-a-pgsock-netns.old-20261128`); a fresh owned netns fixture
  was used for all runs. pageinspect heap dumps from the preserved
  datadir proved unreliable (two versions of the same table showed
  different attribute counts, impossible in a healthy cluster) and were
  set aside.
- The one blocked local run (the 083/12 drain test hanging >85 min)
  had a definitive root cause proven from the server log plus lock
  experiments on the fresh fixture: PG18 PL/pgSQL `RETURN QUERY` does
  NOT terminate the function, so the legacy freeze body falls through
  the ACTIVE branch into the 082 guarded post-branch; the guarded
  read's full `FOR UPDATE` conflicts with the foreign-key KEY SHARE
  the uncommitted COW proposal-writer transaction holds on the
  workspace row (079 producer table FK), waiting on a transaction the
  test deliberately keeps open. Fix (implemented and verified):
  explicit `RETURN` after the successful ACTIVE enqueue plus
  `FOR NO KEY UPDATE` on the guarded post-branch read (row-lock
  matrix: postgresql.org/docs/18/explicit-locking.html#LOCKING-ROWS).

## Confirmations

- No merge to main, no auto-merge, no second PR for this
  increment; single draft PR (#124). ONE force-push occurred and
  violated the order's force-push prohibition (the in-round
  comment-only amend of this round's own freshly created branch);
  it is recorded above and repaired forward-only by the
  ancestry reconciliation commit. No other commit's history was
  rewritten and no other branch was touched; no further
  force-push was performed.
- No production systems, credentials or data touched; fixture
  credentials only, redacted from durable outputs
- No policy weakening, no new dependency, no skipped or pending gate
  claimed as pass
- No OAP strategic files edited beyond committing the exact order and
  active bytes; this report is the only strategic file this round owns
