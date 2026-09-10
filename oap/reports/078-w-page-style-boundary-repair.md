# OAP Execution Report — 078-w: page-style authority and evidence repair

## Identity and status

- Objective: 078; increment: 078/4; continuation: 078-w.
- Mode: `AMENDED_EXISTING_PR`.
- Status: `COMPLETE` for the bounded 078-w execution scope.
- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: [#81](https://github.com/ulfe-lmi/slaif-agent-site/pull/81), open; no merge or auto-merge performed.
- Branch: `oap/078-4-page-style-overrides`.
- Verified base: `fe31c9f30a7797d0916ad7f8fb56344bc61526f3`.
- Starting remote report head: `fe3bb1d0747801abc910ac3e38bcc7f9e60fa119`.
- Final pushed implementation head: `51e2a78b1fe5c6ca5d4a74a151e039e496157a28`.
- Implementation parents: `df00009f2ffa8cd7a798a777319cd01a15e4e777`, then
  `51e2a78b1fe5c6ca5d4a74a151e039e496157a28` is the final smoke-contract
  repair commit.
- Report publication commit: `SELF`.
- Report-only commit parent: `51e2a78b1fe5c6ca5d4a74a151e039e496157a28`.
- Active bytes committed unchanged: ASCII `078-w\n`.
- Active SHA-256: `57a668842f5d2b98d355b79fb7c0ca50c99616a1eacc3728231611def5de52ef`.
- Exact 078-w order SHA-256:
  `953bccf17369e6db2544a0ca354e3fd226d7d2102aea1f68cf02ab0c68e3cfcf`.

Objective 078 remains `PARTIAL` at the numeric-objective level. Strategy alone
reviews, accepts, and merges the bounded increment. `COMPLETE` here means that
the activated 078-w repair order was executed and its required remote evidence
was delivered; it does not mean accepted or merged.

## Executive summary

The sole blocker was a strategy/evidence boundary defect in the unmerged
078-v page-style implementation, not a need to reimplement the media-store or
page-style data plane. An independent real-PostgreSQL probe found four concrete
issues: Agent PATCH bypassed the full page visibility/resource predicate,
Agent SQL accepted a null expected row version, SQL rejected a valid update plus
reset of disjoint tokens in one group, and route/OpenAPI metadata did not state
the conditional `page-style:write` authority. The 066 downgrade also required
an explicit fail-safe for non-empty page-style data and style audit rows.

The continuation repaired those boundaries, retained the immutable 078-v order
and report, added named authority/accounting/migration/restart/race tests, and
replaced the weak page-style browser proof with distinguishable all-group
computed-style evidence. The existing human audit invariant was updated for
the newly exercised page-style mutation. No new semantic family or PR was
created.

## Authoritative GitHub state

- Final PR head read back from GitHub as
  `51e2a78b1fe5c6ca5d4a74a151e039e496157a28`.
- PR state read back as `OPEN`; base is `main` at the verified base above.
- The PR description was updated and read back. It identifies 078-w, the four
  repaired defects, downgrade safety, named local evidence, the final
  implementation lineage, and the no-merge boundary.
- The first post-df implementation workflow (`34505044140`) exposed one
  concrete failure in the existing Compose human audit invariant: it still
  expected the pre-page-style five-event sequence. Its retained log showed all
  browser/public Agent/media assertions passed. The in-scope smoke assertion
  was repaired and the final workflow below was run on the new head.

### Final required checks

All current required checks for final head `51e2a78` were terminal and
successful in workflow `34507904184` (CodeQL workflow `34507904137`):

- Repository policy: `pass`.
- Detect supported languages: `pass`.
- Node contracts: `pass`.
- Python 3.12 quality and package: `pass`.
- Python 3.13 quality and package: `pass`.
- Python 3.14 quality and package: `pass`.
- Foundation PostgreSQL 14: `pass`.
- Foundation PostgreSQL 15: `pass`.
- Foundation PostgreSQL 16: `pass`.
- Foundation PostgreSQL 17: `pass`.
- Foundation PostgreSQL 18: `pass`.
- Compose and edge packaging: `pass`.
- Supply-chain evidence: `pass`.
- Markdown: `pass`.
- Mermaid: `pass`.
- Dependency review: `pass`.
- CodeQL: `pass`.
- Analyze (actions): `pass`.
- Analyze (python): `pass`.
- Analyze (javascript-typescript): `pass`.

GitHub remains authoritative if any later check or branch-head state changes.

## Changes delivered

### Production and contract boundary

- `066_001_page_style_overrides.py` now checks full Agent page accessibility
  under the existing lifecycle and page-structure barriers before returning or
  mutating style state, requires a positive non-null Agent expected version,
  rejects only exact update/reset token intersections, serializes style theme
  resolution against theme mutation, and refuses downgrade when page-style data
  or style audit rows would be lost.
- `control_api/route_policy.py`, `agent_api/app.py`, and generated
  `contracts/openapi/agent-v1.json` publish and validate the exact
  `x-slaif-page-style-authority` metadata: base `page:read`, changed-state
  `page-style:write`, raw override/inheritance basis, nine set/reset tokens,
  exact-overlap rule, and the no-effect exemption.

### Verification and browser evidence

- `test_agent_page_style.py` now names focused proofs for resource/version/
  mixed-reset authority, migration round trip and downgrade safety,
  no-effect mutation/audit accounting, narrowed token/reset constraints,
  quota/lifecycle/revocation, restart with non-empty overrides,
  delete/restore preservation, workspace/site isolation, and deterministic
  style-v-style and style-v-page update/move/delete races.
- `test_agent_openapi.py` asserts the complete page-style authority extension
  and generated-contract shape.
- `tests/e2e/preview.spec.ts` sets all four page-style groups through the real
  Agent API, checks same-authorized-workspace NGINX preview classes and
  computed values, records component-local gap precedence, and resets to
  inherited site-theme output.
- `tests/e2e/governance.spec.ts` exercises the human page-style controls and
  verifies page style survives the real Puck save/move/reload workflow.
- `tools/compose/public_agent_acceptance.py` now uses distinguishable page
  overrides, reads them after Agent/render/web restarts, and verifies full
  reset-to-inherit output.
- `tools/compose/smoke.sh` counts and classifies the additional legitimate
  human page-style audit/idempotency event in the exact mutation sequence.

### Durable current truth

- Current README, API/testing guidance, increment ledger, MVP progress, and
  contract audit identify 078-w as the active page-style authority/evidence
  continuation and explicitly preserve 078-v as immutable historical truth.
- No historical order or report was rewritten. No credentials, capabilities,
  cookies, database URLs, or production data were exposed.

Final PR size from verified merged base, including the preceding 078-v
implementation and this continuation: 49 files, approximately +4,155/−115.
This remains one semantic page-style boundary and its required evidence; no
global regions, catalog breadth, media/MCP, review/publication, dependency,
or unrelated cleanup scope was added.

## Acceptance-criterion evidence

1. **Resource authority and page isolation.**
   `test_page_style_visibility_version_and_mixed_reset_authority` creates an
   excluded `/outside` page, narrows `route_prefix`, and asserts both HTTP GET
   and PATCH return 404; direct Agent SQL returns `PAGE_NOT_FOUND`; foreign
   site/page access returns 404; and the canonical page base is unchanged.
   The existing 049 accessibility helper is reused under lifecycle 280 and
   structural 994 locks.

2. **Agent optimistic version authority.**
   The same focused test calls the trusted Agent SQL wrapper with a null
   expected version and asserts stable `ROW_VERSION_REQUIRED`, while the
   human wrapper remains a distinct compatibility path. HTTP requests use the
   typed positive Agent request model.

3. **Exact update/reset semantics.**
   The focused test proves Agent HTTP and direct SQL accept typography weight
   update plus family reset in one request, with one row-version increment and
   the expected raw/resolved result. The original focused test retains the
   true same-token overlap rejection and malformed/null input denial.

4. **Machine-readable authority.**
   `test_page_style_contract_is_page_bound_and_resettable` asserts the exact
   generated authority extension, required base scope, changed scope, token
   vocabulary, reset field, overlap rule, and no-effect quota/audit/COW
   exemption. The runtime route-policy/OpenAPI bidirectional validators pass.

5. **Scope, resource constraints, lifecycle, and accounting.**
   `test_page_style_accounting_constraints_lifecycle_restart_and_restore`
   proves read-only no-effect success without mutation/audit charge, changed
   state charging exactly one mutation/audit/idempotency result, unrelated
   scope denial, token and palette allowlists including reset destination,
   quota 429 with unchanged raw state, expired/frozen/archived/revoked 401
   denials, same-site other-workspace confinement, foreign-site/page denial,
   restart readback, and raw override preservation through delete/restore.

6. **Versioned COW/idempotency/replay behavior.**
   The existing page-style focused test proves changed replay byte equality,
   idempotency mismatch, stale version conflict, read-authorized no-effect,
   reset-to-inherit, and no durable direct-SQL residue after rollback. The
   accounting test checks no-effect and failure counters explicitly.

7. **Database lock and cancellation boundary.**
   `test_page_style_structural_races_serialize_with_page_operations` uses the
   PostgreSQL advisory lock table as a barrier and proves one winner/one stale
   loser for style-v-style and style-v-page update/move/delete. The lifecycle
   and theme barrier test proves the 280 lifecycle wait and 995 theme wait;
   no timer is used as race proof. The full backend suite also passed all
   existing cancellation/concurrency coverage.

8. **Migration safety and legacy continuity.**
   `test_page_style_066_round_trip_preserves_legacy_data_and_blocks_loss`
   performs a fresh data-bearing 065-to-066-to-065-to-066 round trip, checks
   legacy page fields and empty style defaults, owners/volatility/search-path/
   ACLs, Agent/Editor grants, and the audit semantic constraint. It proves
   pending-COW downgrade refusal and non-empty page-style data downgrade
   refusal, preventing silent loss.

9. **Renderer and human evidence.**
   The final clean Compose run passed all 11 browser projects. The
   `agent-theme-patch-renders-in-the-same-authorized-workspace` proof observed
   all nine distinguishable page-style classes and computed styles through the
   same NGINX preview, showed a component-local grid gap remaining authoritative,
   and verified full reset to inherited site-theme values. The human Puck test
   and updated smoke invariant passed the page-style control, audit, and
   composition-preservation paths.

## Exact local verification

The following required gates completed successfully on the final implementation
lineage:

- `uv lock --check`.
- `uv sync --frozen --all-groups`.
- `uv run --frozen ruff check services/backend tests/repository tools`.
- `uv run --frozen ruff format --check services/backend tests/repository tools`.
- `uv run --frozen mypy` — no issues in 274 files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository` —
  541 passed, one existing deprecation warning.
- `uv run --frozen pytest services/backend/tests/integration` — 221 passed in
  35m17s.
- `uv build --out-dir /tmp/slaif-agent-site-distributions` — source and wheel
  built.
- Frozen `uv` process smoke for all ten configured processes — every process
  returned `CHECK_OK`. The unwrapped host `python -m` form was not importable
  from this checkout; the repository-installed frozen invocation was used.
- `python -m unittest discover -s tests/repository -p 'test_*.py'` — 58 passed.
- `python -m unittest discover -s tests/packaging -p 'test_*.py'` — 48 passed.
- `python tools/check_repository.py` — `PASS repository policy`.
- `python tools/check_mermaid.py` — 16 diagrams rendered across 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` — 0 issues.
- `pnpm lint` — pass.
- `pnpm format:check` — pass.
- `pnpm typecheck` — pass, including E2E TypeScript.
- `pnpm test` — pass: package/browser tests and 11 contract tests.
- `pnpm build` — pass.
- `pnpm licenses list --json` — pass.
- `sh tools/compose/smoke.sh slaif007v` — final run passed browser projects,
  public Agent acceptance, human audit sequence, media, edge, recovery,
  negative-bootstrap, Apache/NGINX validation, artifact revocation, and
  packaging; final output was `compose-smoke: OK`.

## Governance and safety confirmations

- Only the unique order selected by `oap/active` was executed.
- The exact order and active content were committed unchanged; coding did not
  edit historical orders or reports.
- Only existing PR #81 and its existing branch were used. No extra objective
  PR, branch, merge, auto-merge, release, or acceptance action was performed.
- The passing 078-v implementation was not reimplemented; the changes are the
  ordered authority, evidence, migration-safety, and current-truth repair.
- No production systems, production data, real credentials, capability URLs,
  cookies, or private artifact URLs were accessed or printed.
- No verification gate was skipped, weakened, suppressed, or replaced by a
  local result. GitHub’s final head checks are all green as listed above.
- The final worktree was clean before this report-only publication commit.

## Completion condition

Objective 078/PR #81 may be declared complete only when strategy independently
confirms the exact remote PR head is the report-only `SELF` commit for this
report, confirms all required GitHub checks remain green, reviews the named
078-v plus 078-w evidence and preserved scope, and accepts/merges PR #81 under
OAP authority. The coding agent has not and will not perform that acceptance or
merge.
