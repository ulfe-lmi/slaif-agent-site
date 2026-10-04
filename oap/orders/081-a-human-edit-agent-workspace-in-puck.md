# OAP Work Order — 081-a: human Puck editing in the exact Agent workspace

> Strategic work order. Executor: coding agent. Reviewer/acceptor/merger:
> strategic model. This order is IMMUTABLE once activated; corrections,
> if ever needed, use the next letter (081-b) and a new order.

## 1. Identifier and mode

- Round ID: `081-a` (flat legacy format; the first semantic increment of
  numeric Objective 081 uses the legacy `NNN-L` namespace per
  `governance/2026-09-14-increment-qualified-round-ids.md`; a later second
  increment would use `081-2-a`).
- Objective: 081 (081/1 — human Puck editing in the exact Agent workspace).
- PR mode: CREATE_NEW_PR.
- Branch: `oap/081-a-human-edit-agent-workspace-in-puck`, created from
  verified current `main` = `550c42c387bcddf12356ba2db299ef5bf99dd818`
  (the 079/3 merge commit, re-verified against live GitHub at activation).
- PR title: `OAP 081-a: human Puck editing in the exact Agent workspace
  (081/1)`.
- Expected PR number: next available (GitHub assigns; create exactly one
  PR; do not create, amend, or touch any other PR; dependabot PRs
  #83/#90/#94 are out of scope and are never touched).
- Dependency correction versus the inert preplanned file: the preplan
  stated "Requires 074–080". Strategy independently verified on
  2026-10-04 that 080 (MCP parity) is NOT an architectural prerequisite
  for 081: the 081 acceptance path uses the human session, the Editor
  API, the existing Agent REST semantics (069/075–077), and preview
  rendering; no MCP surface is exercised. Per human decision D5
  (2026-09-20), 080 is resequenced after 084. This order proceeds from
  074–079 (all merged).

## 2. Verified current state (strategy-verified 2026-10-04 against live
GitHub and the local checkout at this exact head)

- Remote `main` = `550c42c387bcddf12356ba2db299ef5bf99dd818` (079/3 merge
  commit, merged 2026-10-04T08:43:30Z; post-merge check runs at this head:
  18 success + 1 skipped, none pending).
- 079/1 PR #92 MERGED at `577509e7bc990d85a10af5954bee3c6f7c888a4f`
  (2026-09-22); 079/2 PR #93 MERGED at
  `c149c39e66978c9ee53a7d92300a64e4297cfa56` (2026-10-04); 079/3 PR #95
  MERGED at `550c42c387bcddf12356ba2db299ef5bf99dd818` (2026-10-04). No
  OAP product PR is currently open (dependabot #83/#90/#94 only).
- Numeric Objective 078 = COMPLETE (reclassified 2026-10-04 by post-merge
  strategy bookkeeping after independent evidence verification, per human
  D1; catalog 32/32). Numeric Objective 079 = COMPLETE (scoped; the
  083-bound public-namespace retention/GC is explicitly excluded).
- `oap/active` = `079-3-a` (last activated round; protocol-correct idle
  state until this activation).
- Component catalog: 32 types (architecture minimum met); OpenAPI
  `contracts/openapi/agent-v1.json` has 47 paths; strip-identity sha256
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
  (after stripping `x-slaif-*`).
- Current Puck/Editor truth (verified in source at this head):
  - 068 proves real Puck editing of the normalized composition through
    the session-authenticated Editor API (`/api/editor/v1/...`), the
    shared renderer, and the Puck adapter.
  - The human editor envelope (migration `028_001`) is HUMAN-workspace
    ONLY: `slaif_human_editor_workspace_resolve` finds-or-creates the
    user's latest ACTIVE HUMAN workspace (L2 preset, 8h TTL);
    `slaif_human_editor_workspace_assert` requires
    `actor_type='HUMAN'`, `created_by = human`, latest-active-HUMAN-
    workspace, membership `p_permission_key`, session validity, and an
    optional `p_lock` on advisory-lock key
    `hashtextextended(workspace_id::text, 280)`;
    `slaif_human_editor_idempotency_begin/complete` internally call that
    assert.
  - Consequence: an AGENT workspace cannot be opened or edited in Puck
    today; the human always edits a separate HUMAN workspace
    (MVP-CONTRACT-AUDIT row 40: PARTIAL, "081 exact-workspace proof").
  - Established authorization precedent for human operations on AGENT
    workspaces (migration `038_001`, `slaif_human_agent_workspace_get`):
    `COALESCE(delegator_id, created_by) = user OR platform_administrator
    OR 'workspace:read-all' IN effective_permissions`, plus
    `actor_type='AGENT'`, ACTIVE, not expired.
  - Shared advisory-lock contract: `acquire_workspace_lifecycle_lock`
    takes `pg_advisory_xact_lock_shared` on key
    `hashtextextended(workspace_id::text, 280)`; the 028 editor assert
    takes the xact lock on the same key under `p_lock`. Agent mutations
    do not yet take this lock (that retrofit is 082/1 scope, out of
    scope here).
- Migration head: `068_001_media_publication_core` (in-place adapted in
  079/3). This order's new migration is `069_001`.
- E2E precedents: `tests/e2e/agent-sessions.spec.ts`; 068/078-4 public
  NGINX human Editor/Puck plus Agent-workspace evidence; `reporter.mjs`
  conventions.
- Flake policy: at most ONE documented unmodified CI re-run, and only for
  the documented flake class with its exact failure signature; any other
  recurrence is a real failure — fix in code or report BLOCKED.

## 3. Strategic context

- The defining workflow is the human-governed review/publication
  lifecycle: the Agent edits a workspace, the human inspects and adjusts
  that same workspace, and only then does the human publish decision
  happen. Today Puck editing always lands in a separate HUMAN workspace,
  so the reviewed artifact is never the exact Agent workspace that was
  worked in — this breaks the defining workflow and blocks 084
  (conflict-safe lifecycle) and 088 (fixture reconstruction with human
  Puck adjustment) from reusing it.
- 081/1 is the next bounded unit on the safety-critical path (human D5,
  2026-09-20): 079 media (done) → 081 exact-Agent-workspace Puck → 082
  freeze/review (pre-split direction 082/1–2) → 083
  accept/discard/promotion (pre-split direction 083/1–2–3) → 084
  conflict-safe → 080 MCP parity → 085 onward. The 082/083 split
  directions are strategy-approved but their work-order contents are NOT
  advance-accepted; each activation re-verifies source, dependencies,
  review budget, and semantic separability.
- This order is ONE semantic family: human-authorized exact-workspace
  editing through the existing Editor API and Puck. No
  freeze/review/promotion/publication (082/083/084), no Agent-side lock
  retrofit (082/1), no snapshot/review UI (082/2).

## 4. Bounded scope

One new bounded human-editor envelope for AGENT workspaces (SQL +
Editor API + Puck UI), plus the post-079/3 current-truth reconciliation
(R4).

## 5. Explicit non-goals

- No freeze, REVIEW, accept/discard, promotion, or publication behavior
  (082/083/084).
- No Agent-mutation shared-lock retrofit; no durable review job/worker;
  no `review_snapshot` (082).
- No MCP surface change (080 is resequenced after 084).
- No component-catalog, renderer, composition-schema, or Puck-adapter
  changes (catalog stays 32/32; adapter unchanged).
- No media semantics change (079 scope is closed).
- No behavior change to the HUMAN-workspace editor flow: the legacy path
  (no workspace selection) must remain byte-identical — same
  resolve/assert/idempotency functions, same responses.
- No new HTTP routes, no new scopes/permissions, no new dependencies, no
  lockfile or supply-chain changes.
- No dependabot PRs.

## 6. Requirements

### R1 - Human-authorized AGENT-workspace editor envelope (new migration
`069_001`)

Create `services/backend/src/slaif_agent_site/db/alembic/versions/069_001_human_agent_workspace_editor.py`
(reversible downgrade: drop exactly what this migration creates):

1. `control.slaif_human_agent_workspace_editor_assert(p_workspace_id uuid, p_human_user_id uuid, p_site_id uuid, p_human_session_id uuid, p_permission_key text, p_lock boolean) RETURNS void`,
   `LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog`,
   structurally mirroring `control.slaif_human_editor_workspace_assert`:
   - COW context integrity: `app.session_id` must parse as the UUID of
     `p_workspace_id` and `app.operation_id` must be present (violation:
     same internal error class as the HUMAN path; the HTTP layer maps
     both paths to the SAME safe error text as existing editor failures
     — do not add client-visible error text distinguishing the two
     workspace paths).
   - If `p_lock` is true, take
     `pg_advisory_xact_lock(hashtextextended(p_workspace_id::text, 280))`
     — same key, same lock semantics as the 028 editor assert (preserves
     one lock order).
   - Workspace predicate (all required, fail-closed):
     `workspace.id = p_workspace_id`,
     `workspace.site_id = p_site_id`,
     `workspace.actor_type = 'AGENT'`,
     `workspace.status = 'ACTIVE'`,
     `workspace.expires_at > CURRENT_TIMESTAMP`, site ACTIVE, delegator
     account ACTIVE (`COALESCE(delegator_id, created_by)`), session not
     revoked and within `absolute_expires_at`.
   - Authorization:
     `COALESCE(workspace.delegator_id, workspace.created_by) = p_human_user_id`
     OR the user is in `control.platform_administrator` OR
     `'workspace:read-all' = ANY(effective_permissions)` via
     `control.slaif_effective_human_membership(p_human_user_id, p_site_id)`;
     AND (platform admin OR
     `p_permission_key = ANY(effective_permissions)`) — the per-route
     permission key still enforces the human's own role ceiling
     regardless of the workspace's delegation preset.
   - Non-leaking: cross-site, nonmember, or unauthorized callers receive
     the same generic denial as a nonexistent workspace (no
     existence/status oracle).
   - `status = 'ACTIVE'` alone guarantees denial of REVOKED/EXPIRED and
     of any future non-ACTIVE state (FREEZING/REVIEW/terminal).
2. `control.slaif_human_agent_editor_idempotency_begin(...)` and
   `control.slaif_human_agent_editor_idempotency_complete(...)`,
   mirroring the 028 idempotency pair in signature and record semantics
   but internally calling the new assert. Reuse the existing human-editor
   idempotency record table (records are already scoped by workspace +
   session); no new table.
3. No modification of any `028_001` function (immutable merged
   behavior).
4. Update `privileges.py` (and the bootstrap post-harden grant list where
   the 028 functions were granted) so the editor runtime role has EXECUTE
   on the new functions, paralleling the 028 grants exactly; re-run the
   privilege-validation gate.

### R2 - Editor API workspace selection (stateless, server-authoritative)

- Add an optional request header `X-Editor-Workspace: <uuid>` to the
  Editor API (session-authenticated). Presence selects the AGENT-
  workspace path; absence keeps the existing HUMAN-workspace resolution
  byte-identical.
- Server-side, for every Editor request (reads and mutations), when the
  header is present: validate UUID format before any DB access
  (malformed: same safe error as an invalid editor request, no DB
  roundtrip); run the R1 assert inside the request transaction with the
  same `p_lock` semantics the HUMAN path uses per route (mutations:
  locked; reads: unlocked); derive the COW context
  (`app.session_id`/`app.operation_id`) ONLY from the asserted result —
  the raw client value is never trusted as COW context.
- A header naming a HUMAN workspace must be denied (the assert requires
  `actor_type='AGENT'`); the headerless legacy flow is the only path to
  HUMAN workspaces.
- All existing Editor routes (composition read / component CRUD / move,
  theme, page style, global regions, items, views, pages, navigation,
  media metadata) participate through the central dependency; no
  per-route logic changes.
- Idempotency: mutations in the selected workspace use the R1 agent
  idempotency pair; the audit actor is the HUMAN `human_session_id`
  (never an Agent capability); no capability token is minted, forwarded,
  or visible in the browser; Puck save semantics remain
  save-workspace/draft (never promotion).

### R3 - Puck/UI: open and name the exact workspace

- AI Sessions surface: an explicit "Open in Puck" action for each AGENT
  workspace (the server remains authoritative for eligibility; the UI
  renders the action for ACTIVE Agent workspaces; every subsequent
  request re-asserts).
- The editor page accepts the workspace selection; the Puck editor holds
  it for the editing session, sends `X-Editor-Workspace` on all Editor
  calls, and displays the selected workspace prominently (workspace
  title plus an "Agent workspace" marker), clearly distinct from the
  human-workspace flow.
- Navigation/naming must never confuse canonical, HUMAN-workspace, or
  Agent-workspace state (editor header shows the exact workspace being
  edited; save = save workspace/draft).
- Responsive per architecture §7: full Puck desktop+tablet required,
  phone best-effort.

### R4 - Current-truth documentation (durable wording; post-079/3
reconciliation)

Exactly four surfaces, minimal edits. Verified immutable facts to use
(strategy-verified against GitHub at activation): 079/3 accepted and
merged in PR #95 at `550c42c387bcddf12356ba2db299ef5bf99dd818` on
2026-10-04. `PR #NN` below = the PR number GitHub assigns to THIS PR at
creation time (record it exactly in the report and in every doc line
that uses it).

- (a) `oap/INCREMENTS.md`: header — replace "Objective 078 is
  `PARTIAL`" and "the three remaining catalog types and real Image
  rendering are 079-bound by dependency audit" with the post-079/3 truth
  (078/1–078/9 closed; the 079-bound catalog types closed by 079/1–3,
  catalog 32/32; numeric 078 COMPLETE per the 2026-10-04
  reclassification; numeric 079 COMPLETE scoped, 083-bound
  retention/GC excluded). 079/3 row → "Accepted and merged in PR #95 at
  `550c42c387bcddf12356ba2db299ef5bf99dd818` on 2026-10-04; 079/3 is
  closed". Next row → 079/3 closed, 078/079 status per the header, and
  "the next bounded increment is 081 (human Puck editing in the exact
  Agent workspace), opened at `081-a` (PR #NN)".
- (b) `oap/MVP-PROGRESS.md`: "Active and remaining sequence" paragraph —
  replace "increment 079/3 (DocumentList + document class) is opened at
  `079-3-a` (PR #95)" with "increment 079/3 (DocumentList + document
  class) is accepted and merged in PR #95 at
  `550c42c387bcddf12356ba2db299ef5bf99dd818` on 2026-10-04 (catalog
  32/32)". 078 row → status COMPLETE carrying the verified increment
  facts and ending "numeric 078 COMPLETE (reclassified 2026-10-04 by
  post-merge strategy bookkeeping after independent evidence
  verification per human D1)". 079 row → "COMPLETE (scoped) — 079/1 …;
  079/2 …; 079/3 is accepted and merged in PR #95 at
  `550c42c387bcddf12356ba2db299ef5bf99dd818` on 2026-10-04; the 083-
  bound public-namespace retention/GC is explicitly excluded". 081 row →
  append "081/1 is opened at `081-a` (PR #NN)" in the standard in-flight
  form.
- (c) `README.md`: Objective-078/1 paragraph — replace "numeric
  Objective 078 remains PARTIAL with catalog scope remaining for a later
  bounded increment" with "numeric Objective 078 is COMPLETE: the
  078-bound catalog scope was closed by increments 079/1-3 (catalog
  32/32), accepted and merged in PRs #92/#93/#95". Delivery-sequence row
  — replace "increment 079/3 (DocumentList + document class) is opened
  at `079-3-a` (PR #95)" with "increment 079/3 (DocumentList + document
  class) is accepted and merged in PR #95 at
  `550c42c387bcddf12356ba2db299ef5bf99dd818` on 2026-10-04 (catalog
  32/32)". Planned product work row — prepend "Puck editing in the exact
  Agent workspace (081), " to the list.
- (d) `oap/MVP-CONTRACT-AUDIT.md`: header "Authoritative audited source
  revision" → verified merged `main`
  `550c42c387bcddf12356ba2db299ef5bf99dd818` as of the 081 current-truth
  reconciliation (2026-10-04), with the 078-z (2026-09-14) baseline
  retained as historical. Media row (42) evidence cell → replace "079/3
  is opened at `079-3-a` (PR #95): document class (bounded PDF policy +
  DocumentList, catalog 32 at PR head; E2E evidence in PR, acceptance
  strategy-owned)" with "079/3 is accepted and merged in PR #95 at
  `550c42c387bcddf12356ba2db299ef5bf99dd818` on 2026-10-04 (document
  class: bounded PDF policy + DocumentList, catalog 32/32; E2E-proven,
  strategy-verified)"; status stays PARTIAL (promotion-time
  finalization, anonymous public reads, rollback, and retention/GC
  remain 083-bound); next cell → drop the in-flight 079/3 clause, keep
  the 083 items. 081 row (40) next cell → "081/1 in flight at `081-a`
  (PR #NN); 084/088 reuse it for human adjustment". Roadmap block →
  resequence per human D5 (079 → 081 → 082 → 083 → 084 → 080 → 085
  onward) with a short annotation "080 MCP parity resequenced after 084
  (no 081–084 dependency on 080; human decision D5, 2026-09-20)" and
  "082/083 pre-split directions are strategy-approved, contents not
  advance-accepted".
- Durable-wording rule per 079/1 R9: no live-state claims outside the
  standard in-flight row form; GitHub authoritative for live
  acceptance/merge state; immutable merge facts only; `oap/active`
  defined as "last activated round until next activation"; do NOT state
  that this PR is accepted or merged inside this PR; the next merge must
  not make committed truth false.

### R5 - OpenAPI and generated contracts

No Agent API change: `contracts/openapi/agent-v1.json` must remain
byte-identical (47 paths; strip-identity sha256 unchanged). The Editor
API is session-authenticated and is not part of the public OpenAPI
document. All generator `--check` gates remain zero-diff.

### R6 - Evidence (all actually executed, honestly reported)

1. Unit matrix for the R1 assert predicate: creator allowed; platform
   admin allowed; `workspace:read-all` member allowed; nonmember denied;
   member without `workspace:read-all` who is not the creator denied;
   role-ceiling denial (member lacking the route permission key);
   cross-site denied with the SAME response as unknown workspace;
   REVOKED denied; EXPIRED denied; malformed header rejected before any
   DB access; HUMAN-workspace ID in the header denied; revoked session
   denied.
2. Integration (real PostgreSQL): Agent workspace created; a human opens
   it via the Editor API with the header; a mutation lands in the Agent
   workspace with a HUMAN audit actor; the legacy headerless path still
   resolves/creates the HUMAN workspace (regression pin); idempotency
   replay exact; two concurrent humans on the same Agent workspace
   serialize on lock 280.
3. E2E (public NGINX, real Compose stack; desktop+tablet required, phone
   best-effort): create a real Agent workspace + capability; the Agent
   creates a component via REST with the capability; the human visibly
   opens that exact workspace in Puck (workspace named in the UI); the
   human changes/reorders a component; save/reload; the Agent REST read
   AND the preview render both show the same normalized result; canonical
   DB unchanged; assert one workspace/timeline, HUMAN audit actor, and no
   capability token in the browser.
4. E2E negatives: forged workspace ID (another site), nonmember,
   unauthorized member, revoked workspace, expired workspace, CSRF
   failure, crafted/malformed header — all denied fail-closed with the
   non-leaking response.

### R7 - Hard constraints

No supply-chain/workflow/lockfile changes; no new dependencies; no new
HTTP routes or scopes; no modification of any `028_001` function; no
change to the HUMAN-workspace flow; no secrets in diff or report;
catalog/OpenAPI byte-identity per R5.

## 7. Acceptance criteria (observable)

1. Migration `069_001` applies and downgrades cleanly; the R1 assert
   predicate matrix (R6.1) is green; the privilege gate is green.
2. Integration (R6.2) green, including the legacy HUMAN-path regression
   pin and the HUMAN audit-actor assertion.
3. E2E (R6.3) green: the exact-workspace convergence scenario with every
   named assertion (one workspace/timeline, HUMAN actor, no capability
   token in the browser, canonical unchanged).
4. E2E negatives (R6.4) green with non-leaking denials.
5. Headerless requests behave byte-identically to the legacy path
   (behavior pin).
6. OpenAPI and catalog byte-identical (R5); generator gates zero-diff.
7. All four R4 doc surfaces updated with durable wording; an adversarial
   sweep for stale "079/3 opened/pending/in flight" wording returns
   nothing; 078/079 statuses exactly as reclassified.
8. R7 constraints hold (lockfiles byte-identical; no
   route/scope/dependency change).
9. CI: all 20 required checks successful on the exact report-only head
   (strategy verifies independently).

## 8. Verification and workflow

- Local authority as usual (packages, browsers, databases, services,
  tests, CI logs are yours).
- GitHub: create branch + PR from verified `main` (post-079/3); push
  every commit; on completion commit the activated order, `oap/active`
  (= `081-a`), and the report to the PR branch WITHOUT changing
  strategic-owned order/active content; the file
  `oap/orders/081-a-human-edit-agent-workspace-in-puck.md` on the PR
  branch is THIS activated order (byte-identical; record its sha256 in
  the report). The report publication commit is report-only with
  `Report publication commit: SELF`; its parent is the literal
  implementation-head SHA.
- Do not merge; strategy is the only merger.
- Flake policy per Section 2 (one documented unmodified re-run,
  documented flake class only).

## 9. Report requirements

`oap/reports/081-a-human-edit-agent-workspace-in-puck.md`: work-order
file + sha256, `oap/active` bytes, PR/branch/head SHAs (base, start,
implementation head, SELF), per-requirement evidence (R1-R7) with exact
command outputs, the OpenAPI/catalog byte-identity proof (sha256), the
E2E assertion list with results, honest status (COMPLETE only if every
requirement's named evidence actually ran — otherwise PARTIAL/BLOCKED
with the exact gap), cumulative base->head size table grouped per
2026-09-14 review-unit governance Section 2 (base =
`550c42c387bcddf12356ba2db299ef5bf99dd818`), predeclared-budget check,
safety/scope confirmations, and the exact CI state at the implementation
head.

## 10. Predeclared review budget (2026-09-14 review-unit governance
Section 1)

- Production/config: at most 12 files (migration `069_001`;
  `editor_api/database.py`; the central Editor dependency/app wiring
  (one file); `editor_api/mutations.py`; `privileges.py` and the
  bootstrap post-harden grant list where applicable; `admin/api.ts`;
  `composition-editor.tsx`; `agent-sessions.tsx`; the page edit route
  where applicable).
- Migrations: 1 (`069_001`, functions only, reversible).
- Tests/evidence: at most 6 files (new integration test; existing human-
  editor workspace test extension; new E2E spec or
  `agent-sessions.spec.ts` extension; header-parse unit where
  separated).
- Generated artifacts: 0 (OpenAPI/catalog byte-identical).
- Docs: at most 4 files (README, INCREMENTS, MVP-PROGRESS,
  MVP-CONTRACT-AUDIT).
- OAP transcript: order + active + report.
- Substantive implementation-line scale: at most 1.5k.
- Fresh single-family PR; the ~20-30 file / several-thousand-line
  threshold remains a REVIEW TRIGGER, not a quota; CLOSURE_ONLY per
  Section 3 of the amendment if the trigger is crossed or a completion
  claim is rejected.

## 11. Review-unit governance (2026-09-14 amendment, in force)

- Every strategic review of this PR calculates base -> current head
  CUMULATIVE size, grouped per Section 2.
- If strategy rejects a completion claim after substantive
  implementation, or the cumulative trigger is crossed, the PR enters
  CLOSURE_ONLY (Section 3) — no new semantic family, no adjacent
  feature, no opportunistic scope.
- On rejection, strategy publishes one finite checklist of unresolved
  criteria with the exact executable evidence for each (Section 4). A
  later report may claim COMPLETE only if every named criterion was
  actually executed.
- Separable functionality starts from verified merged main in another
  PR (Section 5).
