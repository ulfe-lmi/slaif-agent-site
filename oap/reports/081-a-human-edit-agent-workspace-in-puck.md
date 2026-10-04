# OAP Coding-Agent Report — 081-a

## Work order

- Identifier: `081-a` (flat legacy format; the first semantic increment of
  numeric Objective 081 — human Puck editing in the exact Agent workspace,
  081/1)
- Work-order file: `oap/orders/081-a-human-edit-agent-workspace-in-puck.md`
- Work-order sha256: `4298015f41778051ad66886caabd0d4d6f60b86623bd6697b7d22bf3fb96c277`
  (re-verified with `sha256sum` at report drafting)
- `oap/active` bytes: `081-a\n` (hex `3038312d610a`)
- PR mode: CREATED_NEW_PR

## Status
COMPLETE

## Executive summary
Implemented 081/1: humans open and edit the exact Agent workspace in Puck.
A new reversible migration `069_001` adds
`control.slaif_human_agent_workspace_editor_assert` (COW-context integrity,
advisory lock 280, fail-closed ACTIVE/unexpired/delegator-or-admin-or-
`workspace:read-all` predicate with the per-route human permission ceiling,
uniform non-leaking denial) plus the mirrored agent idempotency pair on the
existing human-editor idempotency table; `028_001` is untouched. The Editor
API accepts an optional `X-Editor-Workspace: <uuid>` header: presence selects
the AGENT-workspace path (malformed values are 400 before any DB access),
absence keeps the legacy HUMAN resolution byte-identical. The Puck/UI surface
adds an "Open in Puck" action on ACTIVE Agent workspaces, a workspace landing
page that names the exact workspace, and a prominently displayed
"Agent workspace" banner in the editor; saves store workspace/draft (never
promote) with the HUMAN session as audit actor and no capability token ever
minted or visible in the browser. The R4 current-truth docs were updated in a
separate docs commit using PR number 96. All R6 evidence ran: the predicate
unit + real-PostgreSQL matrix, the integration suite (mutation in the exact
workspace, legacy HUMAN regression pin, idempotency replay, lock-280
serialization), and the new desktop+tablet E2E through public NGINX
(exact-workspace convergence + fail-closed negatives). Two in-scope CI
repairs occurred after the implementation push, both disclosed: commit F
fixed a Prettier formatting violation in the new E2E spec that failed the
Node contracts check at the docs head, and the Compose job at the final head
failed only on the documented Puck-drag flake class (governance
`dragUntil`, `.puck-trusted-component` count 1 -> 4, the only failed job,
before the preview project) — the order's one documented unmodified CI
re-run (1/1) was invoked for it; the final implementation head F is 20/20
green on CI (details under GitHub CI).

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number/URL/state: `#96` (OPEN) — `https://github.com/ulfe-lmi/slaif-agent-site/pull/96`
- Base/head branches: `main` / `oap/081-a-human-edit-agent-workspace-in-puck`
- Starting remote SHA (verified base, post-079/3 merge): `550c42c387bcddf12356ba2db299ef5bf99dd818`
- Transcript commit T (order + active bytes, committed unchanged): `9df503b1c07bded2dc341e353f563a84447b9e5e`
- Implementation commits: I `e4d917a36a3f55348178a5db1bb487e8992ac0f6` (implementation), D `e45b1328b97b69887c029de5630140e728397839` (R4 docs, PR #96), F `7d7d6f0c8dc8712945d26ca5e47225ea50e0ceec` (CI in-scope repair, Prettier line-joining in the new E2E spec only)
- Implementation head SHA: `7d7d6f0c8dc8712945d26ca5e47225ea50e0ceec` (F; all non-report work)
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified via GitHub)
- Report parent = F = implementation head SHA
- New PR this turn: yes (exactly one); amended existing: no; merge performed: NO

## Changes made

- R1: `services/backend/src/slaif_agent_site/db/alembic/versions/
  069_001_human_agent_workspace_editor.py` (new, 243 lines, reversible):
  `control.slaif_human_agent_workspace_editor_assert(p_workspace_id,
  p_human_user_id, p_site_id, p_human_session_id, p_permission_key, p_lock)`
  (`SECURITY DEFINER`, `SET search_path = pg_catalog`): COW-context integrity
  (`app.session_id` parses to the asserted workspace UUID;
  `app.operation_id` present; violation `22023` with the same internal
  error class/text family as the HUMAN path), `pg_advisory_xact_lock(
  hashtextextended(p_workspace_id::text, 280))` when `p_lock`, the exact
  order-named workspace predicate (id/site/`actor_type='AGENT'`/
  `status='ACTIVE'`/unexpired/site ACTIVE/delegator account ACTIVE/session
  unrevoked and within `absolute_expires_at`), the authorization predicate
  (delegator `COALESCE(delegator_id, created_by)` OR
  `control.platform_administrator` OR `workspace:read-all` in
  `slaif_effective_human_membership`; AND per-route
  `p_permission_key = ANY(effective_permissions)`), uniform non-leaking
  `P0002` denial identical for cross-site/nonmember/unauthorized/nonexistent
  (no existence oracle), and `REVOKED`/`EXPIRED`/any non-ACTIVE denied via
  the `status='ACTIVE'` predicate. Plus
  `slaif_human_agent_editor_idempotency_begin/complete` mirroring the 028
  pair (same record table, internally calling the new assert). Downgrade
  drops exactly the three created functions.
- R1 grants: `services/backend/src/slaif_agent_site/db/privileges.py`
  (+24) grants EXECUTE of the three new functions to the editor runtime
  role, paralleling the 028 grants; `bootstrap/service.py` (+1) adds
  `069_001` to the downgrade-compatible revision set (079-1 precedent).
- R2: `editor_api/mutations.py` (+10): `validate_editor_workspace_header`
  (strict UUID `fullmatch` parse; absent -> legacy path; malformed ->
  `ValueError` before any DB access). `control_api/site_authority.py`
  (+21/−4): the central Editor dependency now parses the header first
  (malformed -> `MalformedRequestError` re-raised as 400
  `MALFORMED_REQUEST` instead of the legacy 503 collapse); presence sets the
  agent-workspace flag and skips the legacy HUMAN resolution; the COW
  context derives only from the asserted result. `editor_api/database.py`
  (+21/−3): `request_content_service` selects the agent assert /
  agent idempotency SQL pairs on the `agent_workspace` flag (per-route
  `p_lock` semantics unchanged: mutations locked, reads unlocked); HUMAN
  path SQL and behavior byte-identical.
- R3: `apps/web/src/admin/agent-sessions.tsx` (+8): "Open in Puck" action
  on each ACTIVE Agent workspace row (server remains authoritative; every
  request re-asserts). New `apps/web/app/admin/sites/[siteId]/workspaces/
  [workspaceId]/edit/page.tsx` (+21) landing route + `apps/web/src/admin/
  workspace-editor-landing.tsx` (+89): names the exact workspace (title),
  lists the site's editor pages, deep-links into Puck with
  `workspace`/`workspaceTitle` params; fail-closed message when the
  workspace is not editable. `apps/web/app/admin/sites/[siteId]/pages/
  [pageId]/edit/page.tsx` (+22/−2): parses + strictly validates the
  workspace params (UUID pattern; title truncated to 128) and passes them
  to the editor. `apps/web/src/admin/composition-editor.tsx` (+20): holds
  the selection for the editing session (module-level
  `setEditorWorkspace`, cleared on unmount) and renders the prominent
  "Agent workspace" banner (marker + title + workspace/draft-never-publish
  note). `apps/web/src/admin/api.ts` (+50/−1): `editorRequest` sends
  `X-Editor-Workspace` on all Editor calls when a selection is held
  (headerless requests unchanged); `listEditorPages` with strict response
  parsing (requests `/pages/` with the trailing slash — the no-slash form
  307-redirected to a broken absolute Location behind the NGINX
  `proxy_set_header Host $host`, fixed, disclosed below). `apps/web/app/
  styles.css` (+52): banner/landing styling (responsive).
- R4: `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`, `README.md`,
  `oap/MVP-CONTRACT-AUDIT.md` (commit D; the exact order-named verbatim
  replacements with the verified 079/3 merge fact — accepted and merged in
  PR #95 at `550c42c387bcddf12356ba2db299ef5bf99dd818` on 2026-10-04 — the
  078 COMPLETE / 079 COMPLETE (scoped) reclassified statuses, the 081/1
  in-flight form at `081-a` (PR #96), the D5 roadmap resequence annotation,
  and the durable-wording rules; this PR is not stated as accepted/merged).
- R5: no Agent API change; `contracts/openapi/agent-v1.json` and the
  catalog/design-system artifacts byte-identical to base (proof under
  Criterion 6); generator gates zero-diff.
- R6: new `services/backend/tests/unit/test_editor_workspace_header.py`
  (header parse contract: absent, 2 well-formed, 12 malformed — all before
  any DB access); extended
  `services/backend/tests/integration/test_human_editor_workspace.py`
  (+91: agent-workspace ID in the header denied on the HUMAN path); new
  `services/backend/tests/integration/test_human_agent_editor_workspace.py`
  (923 lines, 3 tests): the real-PostgreSQL R1 predicate matrix (delegator
  allowed; platform admin allowed; `workspace:read-all` member allowed;
  nonmember/role-ceiling/other-delegator denied with the identical
  `P0002` text as an unknown workspace; cross-site == unknown byte-identical;
  REVOKED/EXPIRED/session-revoked/COW-context violations identical
  non-leaking), the exact-workspace mutation flow (HUMAN audit actor,
  idempotency replay exact, two concurrent humans serialize on lock 280),
  and the server-authoritative HTTP selection (legacy headerless regression
  pin, HUMAN-workspace-ID-in-header denied, malformed 400, COW context from
  the asserted result only); new `tests/e2e/agent-workspace-puck.spec.ts`
  (629 lines at F, 2 contracts x desktop+tablet through public NGINX —
  assertion list under Criteria 3/4); `playwright.config.ts` (+12) registers
  `agent-workspace-puck-desktop` / `agent-workspace-puck-tablet`
  (governance-dependent); `tools/compose/e2e.sh` (+10/−1) runs the two
  projects and updates the OK line to `projects=15 ... agent-workspace-
  puck=2`; `tests/packaging/test_compose_smoke_contract.py` (+7/−2) updates
  the governance-dependent project topology pin 8 -> 10 and the two project
  names.
- Disclosed adaptations (bounded, each necessary, none a product-scope
  change):
  1. `bootstrap/service.py`: `069_001` added to the downgrade-compatible
     revision set (1 line; 079-1 precedent for new migrations).
  2. `control_api/site_authority.py`: `MalformedRequestError` re-raise so a
     malformed `X-Editor-Workspace` value is 400 `MALFORMED_REQUEST` before
     any workspace DB access (previously the site layer collapsed it to
     503); the headerless path is unaffected (no header -> no parse error).
  3. `apps/web/src/admin/api.ts` `listEditorPages`: trailing slash on
     `/pages/` (no-slash 307 produced a broken absolute `Location` behind
     NGINX `proxy_set_header Host $host`).
  4. E2E/harness registration: `playwright.config.ts` two new projects,
     `tools/compose/e2e.sh` invocation + OK line, packaging topology pin
     8 -> 10 with the two project names (mechanical, forced by the new
     projects).
  5. `tools/compose/smoke.sh` (2 lines): the `human-editor-envelope`
     sub-checks are scoped `AND workspace.actor_type = 'HUMAN'` — 081-a
     legitimately introduces human editor mutations inside AGENT workspaces
     (the R6.3 convergence scenario runs on the demo site), so the
     unscoped demo-site count/sequence check would false-fail; the HUMAN
     envelope itself (8 rows, exact sequence, 9 idempotency rows) is
     asserted unchanged.
  6. E2E negative-fixture teardown (inside the new spec): the forged
     cross-site fixture (site + workspace + capability + audit row) is
     deleted at test end — platform administrators see every site in
     `/me/sites` ordered by `site_key` (C collation), so a `081neg-`
     fixture site would otherwise sort first and poison later e2e phases
     that select a site by position.
  7. Commit F: Prettier line-joining in the new E2E spec only (3
     insertions / 11 deletions, no semantic change) — the Node contracts
     CI check failed `pnpm format:check` on that file at the docs head;
     reproduced locally, fixed with the repo Prettier (3.9.6), full Node
     gate re-run green.

## Files changed
base -> implementation head numstat:

Base `550c42c387bcddf12356ba2db299ef5bf99dd818` -> implementation head F
`7d7d6f0c8dc8712945d26ca5e47225ea50e0ceec` (exact measured
`git diff --numstat`: 35 files, +2814/−105; the report file itself is
added by the SELF commit and is not counted here):

| Category | Files | +lines | -lines |
|---|---|---|---|
| Production/config | 12 | 339 | 10 |
| Migrations | 1 | 243 | 0 |
| Tests/evidence | 16 | 1759 | 36 |
| Generated artifacts | 0 | 0 | 0 |
| Docs | 4 | 31 | 22 |
| OAP transcript | 2 | 442 | 37 |
| TOTAL | 35 | +2814 | -105 |

Category membership (079-3-a table convention): Production/config =
`apps/web/app/admin/sites/[siteId]/pages/[pageId]/edit/page.tsx` (22/2),
`apps/web/app/admin/sites/[siteId]/workspaces/[workspaceId]/edit/page.tsx`
(21/0), `apps/web/app/styles.css` (52/0), `apps/web/src/admin/
agent-sessions.tsx` (8/0), `apps/web/src/admin/api.ts` (50/1), `apps/web/
src/admin/composition-editor.tsx` (20/0), `apps/web/src/admin/
workspace-editor-landing.tsx` (89/0), `services/backend/src/slaif_agent_
site/bootstrap/service.py` (1/0), `services/backend/src/slaif_agent_site/
control_api/site_authority.py` (21/4), `services/backend/src/slaif_agent_
site/db/privileges.py` (24/0), `services/backend/src/slaif_agent_site/
editor_api/database.py` (21/3), `services/backend/src/slaif_agent_site/
editor_api/mutations.py` (10/0). Migrations = `db/alembic/versions/
069_001_human_agent_workspace_editor.py` (243/0). Tests/evidence =
`playwright.config.ts` (12/0), `tests/e2e/agent-workspace-puck.spec.ts`
(629/0), `tests/integration/test_human_agent_editor_workspace.py` (923/0),
`tests/integration/test_human_editor_workspace.py` (91/0), `tests/unit/
test_editor_workspace_header.py` (50/0), the eight mechanical alembic
head-pin updates `068_001 -> 069_001` (`tests/integration/test_agent_
mutations.py` 11/11, `test_agent_page_style.py` 3/3, `test_control_
database_integration.py` 3/3, `test_database_bootstrap.py` 6/6, `test_
editable_domain_proof.py` 1/1, `test_human_agent_session_control.py` 1/1,
`tests/unit/test_control_database.py` 5/5, `tests/unit/test_foundation_
contract.py` 3/1), `tests/packaging/test_compose_smoke_contract.py` (7/2),
`tools/compose/e2e.sh` (10/1), `tools/compose/smoke.sh` (4/2). Docs = the
four R4 surfaces. OAP transcript = order (441/36) + active (1/1); report
via SELF.

## Pre-declared budget check (order Section 10 vs measured)

Measured against the cumulative base -> implementation-head numstat (table
above), grouped per the 2026-09-14 review-unit governance Section 2
categories.

- Production/config: predeclared at most 12; actual 12 (within budget).
  Predeclared names present: `editor_api/database.py` (the central Editor
  dependency wiring is `control_api/site_authority.py`), `editor_api/
  mutations.py`, `privileges.py`, `bootstrap/service.py` (post-harden grant
  list + downgrade-compatible set), `admin/api.ts`, `composition-editor.
  tsx`, `agent-sessions.tsx`, and the page edit route
  (`pages/[pageId]/edit/page.tsx`). The two additional files are the R3
  surfaces the order names behaviorally: the new workspace landing route
  page (`workspaces/[workspaceId]/edit/page.tsx` — the "Open in Puck"
  target that names the exact workspace) and its client component
  `workspace-editor-landing.tsx`, plus `styles.css` (the R3 prominent
  marker styling).
- Migrations: predeclared 1; actual 1 (within budget): `069_001`,
  functions only, reversible.
- Tests/evidence: predeclared at most 6; actual 16 (EXCEEDED by 10,
  disclosed and itemized): the four predeclared files (new integration test
  `test_human_agent_editor_workspace.py`; existing human-editor workspace
  test extension `test_human_editor_workspace.py`; new E2E spec
  `agent-workspace-puck.spec.ts`; header-parse unit
  `test_editor_workspace_header.py`) plus twelve mechanical files: the
  eight 1-11-line alembic head-pin updates `068_001 -> 069_001` forced by
  the new head, `playwright.config.ts` (two project registrations),
  `tools/compose/e2e.sh` (invocation + OK line), and
  `tests/packaging/test_compose_smoke_contract.py` (topology pin 8 -> 10 +
  the two project names).
- Generated artifacts: predeclared 0; actual 0 (within budget):
  OpenAPI/catalog/design-system byte-identical (Criterion 6).
- Docs: predeclared at most 4; actual 4 (within budget): `README.md`,
  `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`, `oap/MVP-CONTRACT-AUDIT.md`.
- OAP transcript: order + active + report (within budget).
- Substantive implementation-line scale: predeclared at most 1.5k; actual
  582 (Production/config insertions 339 + migration 243), within budget.
- Fresh single-family PR: yes. Cumulative base -> head is 35 files /
  +2814 (dominated by the 441-line strategic order transcript and the
  923 + 629-line new test files); the ~20-30 file / several-thousand-line
  threshold is a REVIEW TRIGGER, not a quota, per Section 1 of the
  amendment — disclosed for strategy adjudication; no adjacent feature, no
  second objective family.

## Acceptance-criteria evidence
### Criterion 1 (migration up/down clean; R1 predicate matrix green; privilege gate green)

- Migration `069_001` applies and downgrades cleanly on the disposable
  local PostgreSQL: the integration suite upgrades through the new head and
  the downgrade path drops exactly the three created functions — covered by
  `uv run --frozen pytest services/backend/tests/integration -q`: PASSED
  (239 passed in 2495.13s (0:41:35); log `/tmp/081a-int-full.log`; final
  tree, after every fix).
- R1 predicate matrix (R6.1), all cases executed on real PostgreSQL in
  `test_human_agent_editor_workspace.py::test_human_agent_editor_assert_
  predicate_matrix`: creator/delegator allowed; platform admin allowed;
  `workspace:read-all` member allowed; nonmember denied; member without
  `workspace:read-all` who is not the creator denied (SITE_EDITOR role
  ceiling); role-ceiling denial (VIEWER lacking the route permission
  key); cross-site denied with the SAME sqlstate + message as an unknown
  workspace (byte-compared, non-leaking); other delegator's workspace
  denied identically; REVOKED denied; EXPIRED denied; revoked session
  denied; COW-context violations raise `22023` with the internal
  error text (mapped to the same safe HTTP error class as the HUMAN path —
  no client-visible text distinguishing the two paths). Header-level
  malformed cases (12 values) in
  `test_editor_workspace_header.py` (unit) plus the unknown/revoked/expired
  HTTP cases in the E2E negatives (Criterion 4). All PASSED in the unit
  and integration runs cited under Local verification.
- Privilege gate: `verify_database_privileges` (from `slaif_agent_site.
  db.privileges`) runs the post-harden grant validation — including
  EXECUTE of the three new functions for the editor runtime role,
  paralleling the 028 grants — in `test_database_bootstrap` (asserting
  `product_privileges_validated`) with `069_001` at the alembic head:
  PASSED within the 239-passed integration run.

### Criterion 2 (integration R6.2 green: exact-workspace mutation, legacy HUMAN pin, idempotency, lock 280)

- `test_human_agent_editor_workspace.py` (3 tests), real PostgreSQL, all
  PASSED within the 239-passed integration run:
  - `test_human_agent_editor_assert_predicate_matrix`: the Criterion-1
    matrix at the DB layer.
  - `test_human_agent_editor_idempotency_audit_and_lock_serialization`:
    an Agent workspace is created; a human opens it via the Editor API
    with the header; the mutation lands in the AGENT workspace
    (`page_composition_changes.session_id = workspace id`) with the
    HUMAN `human_user_id`/site in `audit.human_editor_mutation` (never an
    Agent capability); idempotency replay returns the exact first response
    (same digest/key, no second audit row); two concurrent humans on the
    same Agent workspace serialize on advisory lock 280 (no lost update,
    ordered audit rows).
  - `test_editor_http_workspace_selection_is_server_authoritative`: the
    headerless legacy path still resolves/creates the HUMAN workspace
    (regression pin: byte-identical resolution behavior), a HUMAN
    workspace ID in the header is denied, malformed headers are 400 before
    DB access, and the COW context derives only from the asserted result.

### Criterion 3 (E2E R6.3 green: exact-workspace convergence, every named assertion)

- Carrier: `tests/e2e/agent-workspace-puck.spec.ts` contract
  `agent-workspace-puck-exact-workspace-convergence`, projects
  `agent-workspace-puck-desktop` (Desktop Chrome 1280x720) and
  `agent-workspace-puck-tablet` (iPad gen 7), through public NGINX on a
  real Compose stack; run by `tools/compose/e2e.sh` inside the Compose
  smoke. Assertion list (per viewport, all PASSED):
  1. Compose admin login usable; one-time `sas2_` capability secret shown
     then hidden (count 0).
  2. `GET /api/control/v1/sites/{site}/workspaces/` 200; the created Agent
     workspace (title `081 E2E convergence <project> <hex>`) listed,
     `status ACTIVE`; AI Sessions row shows "Open in Puck" with the exact
     `href=/admin/sites/{site}/workspaces/{ws}/edit`.
  3. Agent REST with the capability: session 200; pages 200; `POST .../
     components` (Heading) 201 with a UUID id.
  4. Landing page: h1 = workspace title; exactly one "home" page link; the
     edit href carries `workspace=<agentWorkspaceId>` and
     `workspaceTitle=<encoded title>`.
  5. Puck editor: "Page composition" heading visible; `.agent-workspace-
     banner` visible with marker "Agent workspace" + the exact title
     (workspace prominently named, distinct from the human flow).
  6. One workspace/timeline: exactly 3 `.puck-trusted-component` nodes
     (2 seed + the Agent-created Heading); the Agent node is present and
     last before the move.
  7. Human reorders the Agent Heading up in Puck (move-up enabled, move-
     down disabled at top); "Save composition" -> 200 and "Composition
     saved and reloaded from the server." shown; after reload the banner
     still shows the exact workspace, 3 components, Agent Heading at the
     new (top) position.
  8. Human Editor API read with `X-Editor-Workspace`: 200, 3 nodes, Agent
     node at the new order.
  9. Agent REST read with the capability: 200, normalized composition
     EQUAL to the human read (same normalized result both ways).
  10. Preview render 200 with the Agent Heading visible (preview parity
      with the edited workspace).
  11. Canonical public read 200 with the Agent Heading count 0 — canonical
      DB unchanged: psql (owner) asserts the admin's HUMAN-workspace count
      unchanged, `page_composition_base` row count unchanged, the base
      home Heading `props` byte-identical, `page_composition_changes` for
      the Agent session > 0, every `human_editor_mutation` row for the
      workspace has `human_user_id = admin` and the site (HUMAN audit
      actor), idempotency rows > 0, and exactly one AGENT workspace with
      the session title.
  12. No capability token in the browser: the `sas2_` token is absent from
      `localStorage`, `sessionStorage`, and `document.cookie`.
  13. No classified browser failures (`failures() == []`).
- Execution: full Compose smoke `sh tools/compose/smoke.sh slaif007e081`
  rc=0 (`compose-smoke: OK`; log `/tmp/081a-smoke-7.log`;
  `compose-e2e: OK projects=15 ... agent-workspace-puck=2 ...`) on the docs
  tree D; then re-verified on the FINAL bytes (F) on a fresh stack
  `slaif008f01` (setup + governance + the two agent-workspace-puck
  projects): 4/4 contracts PASSED, teardown with volumes (log
  `/tmp/081a-final-byte-reverify.log`, `FINAL_BYTE_REVERIFY_OK`).

### Criterion 4 (E2E negatives R6.4 green, non-leaking)

- Carrier: same spec, contract `agent-workspace-puck-fail-closed-negatives`,
  same two projects, all PASSED (smoke 7 at D; 4/4 fresh-stack re-verify at
  F). Assertion list (per viewport):
  1. Real Agent workspace created; "Open in Puck" visible; the owner's
     read of the exact workspace 200 (positive pin).
  2. Non-leaking reference: admin GET composition with an unknown random
     workspace ID -> 503 `SERVICE_UNAVAILABLE` (the R1-assert denial class
     for callers who pass site auth).
  3. Forged cross-site workspace (fixture `081neg-<hex>` ACTIVE site +
     workspace, created directly): identical {status, code, message} to
     the reference — no existence/status oracle.
  4. Nonmember (fixture user one, no demo-site membership): uniformity
     probe over real/unknown/forged workspace values -> identical denial
     (site-layer 404 before any workspace resolution).
  5. Unauthorized member (fixture user two, demo-site VIEWER without the
     delegation): uniformity probe over real/unknown/forged values ->
     identical 503 denial.
  6. REVOKED workspace -> identical to the reference; EXPIRED workspace
     -> identical to the reference.
  7. CSRF failure: state-changing POST component without an
     Origin/Referer pair -> 403 `AUTHORIZATION_DENIED`.
  8. Crafted/malformed headers (`not-a-uuid`, 37-char UUID, 32-hex) ->
     400 `MALFORMED_REQUEST` before any lookup.
  9. The denied flows created nothing: `human_editor_idempotency` count 0
     for forged/revoked/expired workspaces.
  10. No classified browser failures; fixture teardown removes the forged
      site/workspace/audit/capability rows (disclosed adaptation 6).

### Criterion 5 (headerless byte-identical legacy behavior pin)

- No header -> `validate_editor_workspace_header(None) is None` (unit pin)
  and the site-authority path calls the unchanged
  `resolve_human_editor_workspace` (diff inspection: the legacy branch is
  the pre-existing call, unchanged).
- Integration regression pin:
  `test_editor_http_workspace_selection_is_server_authoritative` (legacy
  headerless resolve/create HUMAN workspace) + the extended
  `test_human_editor_workspace.py` HUMAN-path suite: PASSED (239-passed
  integration run).
- E2E: the unchanged governance contract
  `puck-editor-round-trip-through-human-editor-api` (headerless Puck
  round trip through the human editor API) and the unchanged
  agent-sessions/preview/stable-device projects all PASSED in smoke 7
  (projects=15 OK line) and in the fresh-stack F re-verify (setup +
  governance green).
- Smoke `human-editor-envelope: OK workspace=HUMAN active audit=idempotent
  sequence=page-create,theme-update,page-style-update,page-style-update,
  component-add,component-add,component-move,component-add count=9`
  (smoke 7; the HUMAN envelope asserted unchanged, scoped per disclosed
  adaptation 5).

### Criterion 6 (OpenAPI + catalog byte-identical; generator gates zero-diff)

- `uv run --frozen python -m tools.contracts.generate_agent_openapi
  --check`: PASSED (zero-diff); `python tools/generate_component_catalog.
  py --check`: PASSED; `python tools/generate_design_system.py --check`:
  PASSED (final tree D; F changes no Python/generator input).
- Strip-identity proof (re-verified at drafting, both sides, canonical
  JSON after removing every `x-slaif-*` key): sha256 base
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83` =
  sha256 head (identical); 47 paths at base and head.
- `git diff base..head -- contracts/openapi/agent-v1.json packages/
  component-catalog/src/catalog-v1.json packages/composition-schema/src/
  catalog-v1.json packages/composition-schema/src/design-system-v1.json`:
  empty (byte-identical).

### Criterion 7 (R4 docs, durable wording, adversarial sweep)

- All four surfaces updated in commit D with the verified immutable merge
  facts only (079/3 accepted and merged in PR #95 at
  `550c42c387bcddf12356ba2db299ef5bf99dd818` on 2026-10-04; catalog 32/32)
  and the standard in-flight form for 081/1 at `081-a` (PR #96):
  `oap/INCREMENTS.md` header + 079/3 row + Next row; `oap/MVP-PROGRESS.md`
  sequence paragraph + 078/079 rows + 081 row; `README.md` Objective-078/1
  paragraph + delivery-sequence row + planned-product-work prepend;
  `oap/MVP-CONTRACT-AUDIT.md` authoritative-source revision + media row 42
  evidence cell + 081 row 40 + D5-resequenced roadmap block with the
  annotation. No line states this PR as accepted/merged.
- Adversarial sweep for stale 079/3 in-flight wording:
  `git grep -nE '079/3 (is |remains |still )?(opened|pending|in flight)'
  -- '*.md'` (excluding the immutable `oap/orders/` + `oap/reports/`
  history): no matches (rc=1). The 081 in-flight lines use exactly the
  standard form: INCREMENTS Next row, CONTRACT-AUDIT row 40 ("081/1 in
  flight at `081-a` (PR #96); 084/088 reuse it for human adjustment"),
  MVP-PROGRESS row 081 ("PARTIAL — 081/1 is opened at `081-a` (PR #96)").
- 078/079 statuses exactly as reclassified (numeric 078 COMPLETE; numeric
  079 COMPLETE (scoped), 083-bound retention/GC excluded) in every row.

### Criterion 8 (R7 constraints)

- `uv.lock` and `pnpm-lock.yaml` byte-identical to base (`git diff`
  empty — re-verified at drafting).
- No changes under `tools/supply_chain/`, `tests/supply_chain/`, or
  `.github/workflows/` (diff empty). No new dependency (Node/Python lock
  files untouched; no new package manifest entry).
- No new HTTP routes beyond the two admin UI pages (server routes: the
  Editor API surface is unchanged — the header is an optional input to
  existing session-authenticated routes; no new scope strings: the
  scope catalog and the Agent OpenAPI scope sets are unchanged, 47 paths).
- `028_001` unmodified: `git diff base..head -- '*028_001*'` empty.
- No secrets in diff or report (E2E fixture credentials are the
  compose-stack fake placeholders; the one-time capability token is a
  per-run generated fixture value asserted absent from browser storage).

### Criterion 9 (CI: all 20 required checks at the report-relevant heads)

- Superseded docs head D `e45b1328b97b69887c029de5630140e728397839`:
  `Node contracts` FAILURE (Prettier `format:check` on the new E2E spec —
  a genuine in-scope formatting defect, not a flake; fixed by commit F);
  the remaining jobs of that run were CANCELLED by GitHub on the
  superseding push (standard run-supersession; no result recorded).
- Implementation head F `7d7d6f0c8dc8712945d26ca5e47225ea50e0ceec`
  (run 37207897814, created 2026-10-04T14:04:10Z): all 20-check roster.
  First pass: `Compose and edge packaging` FAILURE at 14:08:24Z with the
  documented Puck-drag flake signature — governance project contract
  `puck-editor-round-trip-through-human-editor-api` at
  `governance.spec.ts:733`, `expect(locator('.puck-trusted-component')).
  toHaveCount(1)` Expected 1 / Received 4 (the `dragUntil` max-attempts
  signature), before the `preview` project ever ran, the only failed job
  in the run; all 19 other checks of the run subsequently reached
  terminal SUCCESS (14:10-16:18Z; Foundation PostgreSQL 14-18 and
  Supply-chain evidence were the long jobs). Matching the documented
  flake class from 078/7-078/8 and 079/1 R10, and per the order's flake
  policy (Section 8; one documented unmodified re-run, documented flake
  class only), the ONE permitted unmodified re-run (1/1) of the failed
  job was invoked on run 37207897814 at 16:18 local; no code changed
  for it.
- Final observed state at F (20-check roster, after the single
  documented unmodified re-run of the failed Compose job,
  14:18:34Z-14:30:46Z; the full 15-project e2e suite re-executed green —
  the previously failed governance
  `puck-editor-round-trip-through-human-editor-api` contract PASSED, the
  four agent-workspace-puck contracts PASSED,
  `compose-e2e: OK projects=15 ... agent-workspace-puck=2 ...`,
  `compose-smoke: OK`): all 20 checks SUCCESS —
  `Analyze (actions)`: SUCCESS, `Analyze (javascript-typescript)`:
  SUCCESS, `Analyze (python)`: SUCCESS, `CodeQL`: SUCCESS, `Compose and
  edge packaging`: SUCCESS, `Dependency review`: SUCCESS, `Detect
  supported languages`: SUCCESS, `Foundation PostgreSQL 14`: SUCCESS,
  `Foundation PostgreSQL 15`: SUCCESS, `Foundation PostgreSQL 16`:
  SUCCESS, `Foundation PostgreSQL 17`: SUCCESS, `Foundation PostgreSQL
  18`: SUCCESS, `Markdown`: SUCCESS, `Mermaid`: SUCCESS, `Node
  contracts`: SUCCESS, `Python 3.12 quality and package`: SUCCESS,
  `Python 3.13 quality and package`: SUCCESS, `Python 3.14 quality and
  package`: SUCCESS, `Repository policy`: SUCCESS, `Supply-chain
  evidence`: SUCCESS — no FAILURE/CANCELLED/PENDING remaining at the
  implementation head.
- Local corroboration that the flake is environment-timing, not this
  diff: the same governance contract PASSED on the final F bytes in the
  fresh local stack re-verify (16:07 local, `slaif008f01`) and in smoke 7
  (D tree); the headerless flow is code-identical for F vs base in every
  DOM/request path (banner/header/param logic is inert without the
  selection).

## Local verification
Final tree F (Python gates run at the identical Python tree D — F changes
one TypeScript E2E spec file only; Node gates re-run in full at F):

- `uv lock --check`: PASSED
- `uv sync --frozen --all-groups`: PASSED
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED
- `uv run --frozen mypy`: PASSED (292 source files)
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`:
  PASSED — 773 passed, 26 subtests passed in 32.60s (re-run at drafting on
  the final head F; log `/tmp/081a-unit-re1.log`; includes the 17-case
  header matrix and the privilege-validation assertions)
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED
  (239 passed in 2495.13s (0:41:35); final-tree run after every fix; log
  `/tmp/081a-int-full.log`)
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED
- `python -m compileall -q tools tests/repository`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED
  (49 tests; the topology pin 8 -> 10 + project names)
- `uv run --frozen python tools/generate_component_catalog.py --check`:
  PASSED (zero-diff)
- `uv run --frozen python tools/generate_design_system.py --check`: PASSED
  (zero-diff)
- `uv run --frozen python -m tools.contracts.generate_agent_openapi
  --check`: PASSED (zero-diff)
- `python tools/check_repository.py`: PASSED
- `python tools/check_mermaid.py`: PASSED
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED (tracked files;
  this report's dotfile draft linted on a non-hidden copy, 0 issues)
- Process smokes (`python -m slaif_agent_site.{control_api,editor_api,
  agent_api,render_api,mcp_adapter,media_service,review_worker,scheduler,
  media_gc,bootstrap} --check`): all 10 PASSED
- `node --version` / `pnpm --version`: v24.14.1 / 11.22.0
- `pnpm install --frozen-lockfile`: PASSED
- `pnpm lint`: PASSED (re-run at F, green)
- `pnpm format:check`: PASSED at F (FAILED at D — the F fix; re-run green)
- `pnpm typecheck`: PASSED (workspace + root + tests/e2e tsconfig; re-run
  at F)
- `pnpm test`: PASSED (re-run at F)
- `pnpm build`: PASSED (re-run at F)
- `pnpm licenses list --json`: PASSED (permissive-only policy unchanged;
  re-run at F)
- `sh tools/compose/smoke.sh slaif007e081`: PASSED rc=0 (final-tree run 7
  on D; log `/tmp/081a-smoke-7.log`; 15 E2E projects; my two contracts
  4/4; `human-editor-envelope: OK`; `compose-smoke: OK`)
- Fresh-stack final-byte re-verify at F (`slaif008f01`; setup and
  governance plus the agent-workspace-puck-desktop and
  agent-workspace-puck-tablet projects): PASSED 4/4 contracts, stack torn
  down with volumes (log `/tmp/081a-final-byte-reverify.log`)

Honest local iteration history (disclosed): smoke runs 1-2 failed my two
new projects (pre-fix locator/order-count defects in the new spec, fixed
in-tree); run 3 failed the pre-existing media-publication project because
the negative test's forged `081neg-` fixture site outlived the test and
poisoned position-based site selection (fixed: in-spec fixture teardown,
disclosed adaptation 6); run 5 failed `human-editor-envelope` because the
R6.3 convergence scenario legitimately adds human editor mutations inside
the Agent workspace on the demo site (fixed: HUMAN scoping, disclosed
adaptation 5); run 6 failed the packaging topology pin (fixed: 8 -> 10
disclosed adaptation 4); run 7 fully green. After D, CI surfaced the
Prettier formatting defect (fixed: F, full Node gate re-run green) and the
documented dragUntil flake (one unmodified re-run, 1/1). No assertion was
ever weakened to obtain a pass; every fix is disclosed above.

## GitHub CI / required checks

- State observed for superseded docs head D `e45b1328b97b69887c029de5630140e728397839`: `Node contracts` FAILURE (Prettier formatting of the new E2E spec — in-scope defect fixed by F); all other jobs of the run CANCELLED by GitHub supersession on the F push (no recorded results; not used as evidence).
- State observed for implementation head F `7d7d6f0c8dc8712945d26ca5e47225ea50e0ceec` (run 37207897814, exact 20-check roster of the base commit), including the single documented unmodified re-run of the failed Compose job (flake policy 1/1 consumed, 14:18:34Z-14:30:46Z, full 15-project e2e re-executed green): all 20 checks SUCCESS — `Analyze (actions)`: SUCCESS, `Analyze (javascript-typescript)`:
  SUCCESS, `Analyze (python)`: SUCCESS, `CodeQL`: SUCCESS, `Compose and
  edge packaging`: SUCCESS, `Dependency review`: SUCCESS, `Detect
  supported languages`: SUCCESS, `Foundation PostgreSQL 14`: SUCCESS,
  `Foundation PostgreSQL 15`: SUCCESS, `Foundation PostgreSQL 16`:
  SUCCESS, `Foundation PostgreSQL 17`: SUCCESS, `Foundation PostgreSQL
  18`: SUCCESS, `Markdown`: SUCCESS, `Mermaid`: SUCCESS, `Node
  contracts`: SUCCESS, `Python 3.12 quality and package`: SUCCESS,
  `Python 3.13 quality and package`: SUCCESS, `Python 3.14 quality and
  package`: SUCCESS, `Repository policy`: SUCCESS, `Supply-chain
  evidence`: SUCCESS — no FAILURE/CANCELLED/PENDING remaining at the
  implementation head.
- All required green at drafting: yes (F: 20/20 terminal SUCCESS, no FAILURE/CANCELLED/PENDING).
- Report-only commit (SELF) may trigger fresh checks at the report head;
  strategy independently waits/verifies SELF per the protocol.

## Local setup / dependencies

- No new packages, no lockfile changes. Existing toolchain: uv 0.12.5,
  Node 24.x (v24.14.1), pnpm 11.22.0, Docker Compose (smoke stack
  `slaif007e081` for runs 1-7 plus the fresh final-byte re-verify stack
  `slaif008f01`, each torn down with volumes), local disposable
  PostgreSQL for the integration suite (fake fixture credentials),
  Playwright 1.62.1 via the smoke browser projects,
  `markdownlint-cli2@0.23.2` via npx (temporary, no production
  dependency). Passwordless guest sudo was not needed for this round.

## Documentation

- R4 four surfaces as itemized under Changes made (commit D); durable
  wording per 079/1 R9: no live-state claims outside the standard
  in-flight row form; immutable merge facts only; this PR not stated as
  accepted/merged; `oap/active` semantics preserved. Implemented-vs-
  planned distinction preserved; adversarial sweep clean (Criterion 7).

## Safety and scope confirmations

- Unrelated files changed: no (every changed path is R1-R6 scoped or one
  of the seven individually disclosed adaptations; the eight head-pin
  updates are mechanical alembic-head follows).
- Production secrets accessed: no; production systems accessed: no
  (compose stacks with fake fixture credentials only; local disposable
  PostgreSQL only).
- Required tests skipped/not run: no (every R6-named evidence ran: unit
  matrix, real-PostgreSQL integration, desktop+tablet E2E convergence +
  negatives, headerless pins, byte-identity proofs; the full local gate
  and the full Compose smoke completed).
- Scope deviation: none beyond the disclosed adaptations (each
  individually justified under Changes made); no product-scope change, no
  weakening of validation/tests/auth/conflict behavior.
- Extra objective PR: NO; coding-agent merge: NO (PR #96 left OPEN).
- Activated order/active edited: NO (T commits the exact strategic bytes;
  sha256 + hex re-verified at drafting).
- Report commit changes only this report: yes (staged diff verified
  before commit).
- Flake policy: exactly ONE unmodified CI re-run invoked (the Compose
  failed job at F, documented dragUntil class, run 37207897814, 1/1); the
  F commit is an in-scope repair, not a flake re-run. No other re-runs.

## Known limitations / blockers

- CI at F first pass: `Compose and edge packaging` failed ONLY on the
  documented Puck-drag flake class (governance `dragUntil`,
  `governance.spec.ts:733`, Expected 1 / Received 4 — the max-attempts
  signature; before the preview project; no other job in the run failed).
  The order's one documented unmodified re-run was invoked for it. Local
  evidence on the exact F bytes (fresh-stack re-verify 4/4 incl. the same
  governance contract; smoke 7 on the code-identical D tree) supports
  environment-timing classification. The re-run PASSED (Compose SUCCESS
  at 14:30:46Z, full suite green); the one-per-order flake budget is now
  consumed, so any recurrence of this class in a future round is a real
  failure for strategy to adjudicate (fix in code or BLOCKED).
- The full Compose smoke was last run on D (run 7); at F the full Node
  gate and a fresh-stack re-verify of setup + governance + the two new
  projects were re-run (4/4), and CI's Compose job is the full-suite
  authority at F. No other gate was re-run at F because F changes one
  TypeScript E2E spec file (Prettier line-joining only, no semantic
  change — the diff is 3 insertions / 11 deletions of line-joining).
- 081-a introduces human editor mutations inside AGENT workspaces as a
  legitimate class (the R6.3 scenario); the smoke's `human-editor-
  envelope` check is HUMAN-scoped for that reason (disclosed adaptation
  5). Any future increment that relies on the demo-site mutation counts
  should account for this class.
- The E2E negative-fixture teardown (disclosed adaptation 6) deletes the
  forged fixture rows at test end; it is test-infrastructure cleanup
  inside the new spec, not a product behavior.
- No other blockers.

## Recommended strategic follow-up
None required for this increment; 081/1 evidence is in the PR for
independent review and merge per the order. The dragUntil flake class
remains environment-bound (079/1 R10 stabilized it but VM timing still
occasionally crosses the render race); strategy may wish to note the
consumed 081-a re-run budget when reviewing.
