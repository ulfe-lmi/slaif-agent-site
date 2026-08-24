# OAP Work Order — 069-a

## Objective

Close the confirmed Agent semantic-read runtime gap with the smallest bounded
correction: every semantic family created by objective 067 must be readable
through the public capability-authenticated Agent API from the capability's
own COW workspace, using the real least-privileged Agent identity, with
workspace overlay precedence and canonical fallback.

## GitHub objective state

- Numeric objective: `069`; round: `069-a`.
- Mode: `CREATE_NEW_PR`; create exactly one new objective PR from the verified
  remote `main` produced by accepted objective 068.
- Verified base SHA at activation:
  `b6946d84b72b44f15548235e3936d4e4202c587e` (merged Objective 068 / PR #59).
- No 069 objective PR may exist at activation. Re-fetch GitHub and report any
  live-state difference before implementation.

## Strategic pre-activation transcript renumbering

The human authorized insertion of this semantic-read objective as 069. Before
activation, strategy renumbered only the inert, never-activated future order
files and their internal future-sequence references:

- prior 069 through 077 are now 070 through 078;
- media upload is 070, render is 071, browser worker is 072, freeze is 073,
  accept/discard is 074, dynamic News is 075, destructive isolation is 076,
  conflict is 077, and documentation truth pass is 078;
- activated historical orders/reports were not edited.

Commit those strategic-owned renames/content bytes unchanged on this objective
PR. Extend repository-policy recognition of the inert current future range from
`066–077` to `066–078`, with a focused policy test proving inactive 078 is
accepted without a report while active/historical correlation rules remain
unchanged. Do not otherwise rewrite, implement, or activate objectives 070–078.

## Confirmed pre-objective finding

The existing Agent GET routes authenticate a capability but then call the
ordinary app-level `ContentModelService` backed by the normal Agent pool. The
representative route `GET /api/agent/v1/content-model/types` calls
`ContentModelService.list_types()`, which executes
`content.slaif_content_type_list(uuid)` without an `asyncpg_cow_session`.
Production Agent requests use `slaif_agent_login` with inherited
`slaif_agent_runtime`; that role is deliberately granted the bounded Agent
mutation wrappers, not the generic Editor/Control content-model functions.
Consequently the current hardened route has both a concrete EXECUTE-privilege
failure and no capability-workspace COW read context. Existing 067 real-
PostgreSQL evidence proves mutation/overlay state through trusted fixtures,
not read-after-write through the public Agent GET API.

This objective corrects that read contract. It does not reopen or invalidate
the accepted mutation scope of objective 067.

## Bounded public route surface

Repair the existing semantic GET routes:

- `GET /api/agent/v1/content-model/types`
- `GET /api/agent/v1/content-model/types/{type_id}`
- `GET /api/agent/v1/content-items/types/{type_id}`
- `GET /api/agent/v1/pages/`
- `GET /api/agent/v1/media/`

Add only the two missing list routes needed to read every semantic family
created by objective 067:

- `GET /api/agent/v1/content-model/types/{type_id}/fields`, requiring
  `content-model:read`
- `GET /api/agent/v1/pages/{page_id}/components`, requiring
  `composition:read`

Preserve session/permission discovery and the five 067 mutation routes. Update
route policy, OpenAPI/contract fixtures, documentation, and tests for this
exact surface.

## Required runtime design

1. Authenticate the bearer capability once and derive immutable `site_id`,
   `workspace_id`, and effective scopes only from that trusted context. No
   client header, query, path, body, local state, or database setting may
   select site/workspace/operation authority.
2. Execute semantic reads on the existing Agent pool under a request-scoped
   foundation COW context whose `session_id` is the capability's real
   `control.workspace.id`. Use a fresh internal server operation UUID only if
   the foundation adapter requires it to establish context; a GET must not
   reserve/complete idempotency, append Agent mutation audit, or leave a
   pending COW operation.
3. Add the smallest Agent-specific semantic read service/session abstraction.
   It must use the same already-acquired COW connection; it must not acquire a
   second ordinary pool connection or fall back to the app-level generic
   service.
4. Add narrow Agent read wrappers for exactly the required families: content
   type list/get, field-definition list, content-item list, page list,
   composition list, and media list. Every wrapper must be owner-defined,
   `SECURITY DEFINER`, use fixed `search_path = pg_catalog`, bind its supplied
   site and parent/resource identifiers to the active workspace represented by
   `current_setting('app.session_id')`, and read COW overlay plus canonical
   fallback through the foundation-managed semantic relations.
5. Revoke PUBLIC and grant `slaif_agent_runtime` EXECUTE only on those narrow
   read wrappers. Do not grant it any generic Editor/Control content function,
   table DML, canonical/base/change-table access, reviewer/lifecycle authority,
   arbitrary SQL/DDL, or Control/audit table access.
6. Fail closed when the workspace is missing, inactive, expired, wrong-site,
   belongs to another context, or when a type/page/other parent is outside the
   capability site/workspace. Return the existing stable not-found/
   authorization/unavailable envelope without leaking existence across sites
   or workspaces.
7. Overlay semantics are mandatory: a workspace-created or workspace-modified
   value shadows canonical immediately; unchanged canonical rows remain
   visible as fallback; a workspace tombstone is not resurrected from
   canonical; ordering and existing active/deleted filtering remain stable.
8. Remove the Agent app's ordinary semantic-service fallback from these GET
   paths. An omitted authentication/COW-context step must fail closed rather
   than issue a canonical-only query.

## Required real-PostgreSQL/public-HTTP proof

Use production Agent application wiring, a capability-authenticated HTTP
client, `slaif_agent_login`/`slaif_agent_runtime`, and real PostgreSQL/COW—not
only fakes or direct service calls. At minimum prove:

1. POST the full representative 067 chain—content type, field, content item,
   page, composition node—then GET every created family through the public
   Agent API and observe the workspace values immediately.
2. Seed canonical content, modify or shadow a representative canonical value
   in the Agent workspace through the trusted supported COW fixture/path, and
   prove the public Agent GET returns the overlay value rather than stale
   canonical state while owner/canonical inspection remains unchanged.
3. Prove canonical fallback for unchanged content through at least content
   type, page/composition, and media families.
4. Prove workspace A cannot read workspace B's overlay within the same site,
   including a deliberately colliding semantic key/slug or resource UUID
   where the model permits it. Prove a site-A capability cannot read or use
   site-B type/page/parent resources. Return non-leaking stable outcomes and
   leave no state residue.
5. Prove insufficient read scope for every route family, malformed resource
   identifiers, inactive/expired/revoked capability or workspace, and direct
   Agent-role invocation with forged/missing/wrong-site COW context all fail
   closed.
6. Assert the effective database identity on the public route is
   `slaif_agent_login` with only `slaif_agent_runtime`; inspect exact function
   EXECUTE grants and negative table/generic-function/reviewer/control
   authority.
7. Assert GETs create no Agent idempotency row, mutation audit row, or new
   pending COW operation; canonical/base/change tables remain inaccessible.
8. Prove success, failure, cancellation, and pool reuse clean all
   session/operation settings so one workspace cannot bleed into another.

The proof must include at least content type and page/composition as distinct
semantic families; the full 067 chain requirement above is the acceptance
baseline, not optional stretch coverage.

## Acceptance criteria

- A real hardened capability can read back all five 067-created semantic
  families through the public Agent API without privilege errors.
- GET results are evaluated in that capability's workspace COW context, with
  overlay precedence, tombstone behavior, and canonical fallback proven.
- Another workspace or site cannot observe or influence the first workspace's
  overlay, and error behavior does not disclose foreign resource existence.
- `slaif_agent_runtime` receives only the explicit narrow Agent read wrappers;
  no generic Editor/Control or broader database authority is added.
- Read requests create no mutation/idempotency/audit/pending-operation state,
  and request context cannot survive pool release.
- Existing Agent mutation behavior and accepted 068 human/Puck behavior remain
  green and unchanged outside necessary contract/fixture updates.

## Explicit non-goals

- No new Agent mutations, update/delete API, raw SQL, workspace lifecycle,
  freeze/review/accept/discard/promotion/publication, capability/user
  management, media upload, renderer, browser worker, Puck, or deployment
  redesign.
- No grant of generic content-model functions to Agent and no Editor/Control
  credential use in Agent request handling.
- No reopening of objective 067's accepted mutation result or objective 068's
  accepted human-editor scope.
- No implementation of the newly renumbered inert objectives 070–078; their
  strategic order content is transcript-only in this PR.
- No hostile-public-SaaS or production-readiness claim.

## Verification, documentation, and workflow

Run and report exact focused Agent HTTP/unit/route-policy/OpenAPI tests, real
PostgreSQL identity/privilege/COW integration tests, existing 067 mutation
regression tests, backend quality, repository policy, packaging, migration,
security/supply-chain/license/docs checks, PostgreSQL 14–18 CI, Compose smoke
where repository-required, and `git diff --check`. Mark every skipped,
not-run, blocked, failed, or pending item honestly.

Also run the focused repository-policy test for the extended 066–078 inert
range and verify the final filesystem contains exactly one 069 active order,
exactly one inert order for each 070–078 objective, no stale pre-insertion
future filename, and no accidental report/activation for 070–078.

Update durable Agent API/security/architecture-adjacent implementation docs so
the route list, read scopes, real runtime identity, workspace overlay,
canonical fallback, isolation, and least-privilege boundary are accurate. Do
not claim later media/render/review/promotion objectives.

Create exactly one fresh 069 branch/PR from verified post-068 `main`, implement
only this order, push, and never merge. Commit this activated order and exact
`oap/active` without changing strategic-owned bytes. Publish
`oap/reports/069-a-agent-semantic-cow-reads.md` as the final report-only commit
with `Report publication commit: SELF`; verify its first parent is the literal
implementation head and remote PR head is the report commit before signaling.
Report branch/base/PR, SHAs, route-to-service-to-function trace, effective DB
identity, exact grants/denials, overlay/fallback/isolation evidence, tests/CI,
limitations, and `RESULT=OK|PARTIAL|BLOCKED|FAILED`, then signal exact FIFO
`OK`.
