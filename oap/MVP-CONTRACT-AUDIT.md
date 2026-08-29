# Contract-First MVP Audit

**Audit date:** 2026-08-30  
**Authoritative implementation baseline:** `bcaddc41f9ef4e779dd1a8c9a41eb08462250d53` (`origin/main`, Objective 072 merged)  
**Normative contract:** `ARCHITECTURE.md`, Revision 2.1, read in full  
**Verdict:** **CONTRACTUAL MVP NOT COMPLETE**

This document supersedes the current-state conclusions and queue in
`oap/MVP-CLOSURE-AUDIT.md` while preserving that earlier audit as historical
evidence. A completed narrow objective is not evidence for a broader product
capability. Percentages and file presence are not acceptance evidence.

## Status vocabulary

- `COMPLETE — E2E PROVEN`: merged production behavior exercised through its
  intended product boundary with relevant negative evidence.
- `IMPLEMENTED — E2E PENDING`: production behavior exists on `main`, but the
  contractual end-to-end proof is incomplete.
- `PARTIAL`: a safe useful subset exists, but the architecture promises more.
- `SCAFFOLD ONLY`: types/routes/helpers/status values exist without an honest
  production lifecycle.
- `NOT IMPLEMENTED`: the required production behavior is absent.
- `CONTRACT/PLANNING CONFLICT`: planning or status documents contradict the
  architecture or actual code.

## Contract matrix

| Architecture | Material requirement | Actor / intended interface | Current implementation and proof | Status | Responsible objective and final evidence |
|---|---|---|---|---|---|
| §§6.3, 7, 42.1, 43 | PyPI-only qualified COW foundation, locked hashes, public APIs, PostgreSQL 14–18, licenses/SBOM | Build/runtime | `pyproject.toml`, `uv.lock`, frozen CI, foundation matrix and supply-chain gates | COMPLETE — E2E PROVEN | Retain every CI gate through final Objective 091 |
| §§6.2, 13, 32.2, 46, 52.1 | Clean one-command self-hosted stack, NGINX-only port, Apache adapter, one-time setup | Operator / public NGINX | Compose smoke, real setup/login, edge and Apache tests | COMPLETE — E2E PROVEN | Final clean-clone proof in 090/091 |
| §§18, 32–33, 52.2 | Site-scoped users, roles, memberships, ceilings, multi-site denial | Human Control/Web | Real Control/RBAC data and public governance E2E including cross-site negatives | COMPLETE — E2E PROVEN | Regressions retained; phone acceptance controls added by 082–083 |
| §§15.2, 18–20, 24.2 | Human creates an AGENT workspace and one-time capability, monitors/revokes it | Human Control/Web | `workspace_http.py` and `capability_http.py` exist but are not installed by `control_api/app.py`; no AI Sessions UI; handlers bypass established authorization/site/CSRF policy | SCAFFOLD ONLY | 074; public NGINX E2E must fail if routes/UI/real capability issuance are removed |
| §§16.2, 21, 51.1 | Configurable types, fields, items, translations, relations and collection views as COW data | Human Editor and Agent semantic APIs | Core types/fields/items/views and Editor CRUD exist; translation/relation and several architectural editable entities are absent | PARTIAL | 075 substrate, then 076–079 external interfaces |
| §§15.4, 24.4–24.5 | Agent model/content semantic CRUD with scopes, COW, validation, idempotency and audit | External agent / REST/OpenAPI | Seven narrow COW semantic reads plus discovery and five create-only mutations are real; update/delete, exact item/page/media reads, field CRUD, translations, relations and collection-view writes are missing; normal resource/delete quotas are absent | PARTIAL | 076; positive/negative public Agent REST proof, no direct service/SQL substitute |
| §§15.4, 21.7–22.5, 24.6–24.7 | Agent pages/routes/navigation/redirects/composition/design/media-reference semantics | External agent / REST/OpenAPI | Agent can create a page and component only; no public Agent update/delete/move/restore, navigation, redirect, view, theme/global-region or complete media-reference surface | PARTIAL | 077–079; real capability/COW/idempotency/audit E2E |
| §§24.1, 51.1 | Versioned deterministic Agent OpenAPI describes the real public semantic contract | External agent / OpenAPI | Application factory sets `openapi_url=None`; no generated OpenAPI artifact exists | NOT IMPLEMENTED | 076–080; published schema drift-tests every actual route/security/error contract |
| §25, §51.1 | Curated MCP model/content/composition/design and browser tools delegate to Agent API | External agent / real MCP | Custom `/mcp/v1/tools` lists five reads; `/call` accepts caller-chosen method/path, references absent production configuration and uses a test-only HTTP dependency; no real call test or write-tool proof | SCAFFOLD ONLY | 080; real MCP client tools/list and tools/call E2E through NGINX, with no DB/internal bypass |
| §§14.3, 22.4, 42.4, 52.6 | Human Puck edits the same normalized composition and exact Agent workspace under server policy | Human Web/Puck → Editor API | Objective 068 proves real Puck editing, but its resolver selects/creates a separate HUMAN workspace rather than the Agent workspace later reviewed | PARTIAL | 081 exact-workspace proof; 084/088 reuse it for human adjustment |
| §§14.4, 15.5, 52.6 | Shared trusted canonical and active-workspace renderer | Visitor/human preview / Web+Render | Objective 071 proves canonical and active COW preview with shared renderer, strict authorization and noindex/no-store | IMPLEMENTED — E2E PENDING | Review-snapshot render mode is absent and belongs to 082 |
| §§15.7, 30, 52.7–52.8 | Immutable media bytes, private staging, public finalization, replaceable store | Agent/human Media service and review worker | Objective 070 proves immutable human upload/CAS safety; Agent upload/reference semantics, anonymous canonical-reference-gated bytes, real image rendering and promotion finalization are absent | PARTIAL | Agent media in 079; public finalization/rendering and rollback in 083 |
| §§15.8, 28.1, 30.6, 52.7 | Real confined preview browser runs and private immutable artifacts | External agent / Agent preview routes | Objective 072 proves real Chromium, capability-bound durable runs, six artifacts, retrieval, restart/outage/revoke/foreign negatives, and canonical independence | COMPLETE — E2E PROVEN | Preserve; do not restart or replace 072 |
| §§23, 24.8, 25.2, 42.4, 51.1 | Approved-origin source inspection and quota-controlled responsive sweep | Level-4 agent / curated REST+MCP | No source tools or source-run production path; preview contract runs one route/target and has no product responsive-sweep orchestration | NOT IMPLEMENTED | 087; DNS/redirect/egress negatives plus real multi-target observation |
| §§26–27, 42.3, 52.8 | Every Agent mutation is durably idempotent and semantically audited in the COW transaction | External agent / semantic services | Durable idempotency/audit is proven only for the five Objective 067 create routes; other promised mutations do not exist | PARTIAL | 076–079 extend the invariant; 091 audits route coverage |
| §§10 I-9, 17.5, 28.2, 52.6 | Freeze drains writes, revokes capability and creates immutable complete review snapshot rendered thereafter | Human Control → review worker → Render | `review_snapshot` table/job/worker/path do not exist; current freeze SQL immediately flips status; Agent mutations lack the shared freeze lock | NOT IMPLEMENTED | 082; race-safe freeze, immutable projection/digest/audit closure and snapshot rendering E2E |
| §§15.9, 29.1–29.3, 52.3 | Human-only full accept and discard execute real reviewer COW lifecycle atomically | Human Control → review worker | Control lifecycle routes are not installed; SQL helpers change status only; review worker is idle; `promotion.py` helper is disconnected | SCAFFOLD ONLY | 083; exact snapshot, one reviewer transaction, canonical/public/media/audit proof |
| §§17.4, 29.4, 42.3, 53.5 | Reviewed snapshot cannot silently overwrite later canonical state | Human accept lifecycle | Low-level foundation conflict tests exist, but no immutable-snapshot accept lifecycle exists | NOT IMPLEMENTED | 084 immediately after 083; stale-revision and foundation-row conflicts through product surfaces |
| §§21.6, 42.4, 52.5, 53.2 | Level 4 dynamically creates News/list/detail/navigation without Alembic and publishes after review | External agent + human / product surfaces | Old planned News proof assumed operations and same-workspace Puck behavior that do not exist | NOT IMPLEMENTED | 085 after 074–084; no ORM/SQL/fixture/internal-API mutation |
| §§42.3, 42.5, 53.4 | Legitimate Level-4 agent destructively deletes all editable site state only in its workspace | External agent / Agent API | Existing tests use direct COW SQL for tombstones or cover only five creates; no complete destructive Agent surface | NOT IMPLEMENTED | 086; real Agent DELETE/reset, canonical/other-site/users unchanged, real discard |
| §§23, 42.6, 51.1, 52.6, 53.3 | One fixture reconstruction with dynamic model, source inspection, responsive iteration, Puck adjustment and promotion | Level-4 agent + human / source+semantic+preview+review interfaces | Absent and incorrectly classified as post-MVP in `POST-MVP-WORK-ORDERS.md` | CONTRACT/PLANNING CONFLICT | 088 after 074–087; production interfaces only and code/schema unchanged |
| §§38, 41, 52.8 | Durable jobs, expiry, cleanup and multiple worker claims | Scheduler/review/GC workers | Browser queue is real; generic review/scheduler/media-GC processes remain idle placeholders and no general `control.job` lifecycle exists | PARTIAL | 082–083 introduce review jobs; 089 closes expiry/GC/multi-worker recovery |
| §§39, 42.2, 52.8 | Coordinated database/media backup and clean restore test | Operator tooling | Documentation discusses policy, but no backup/restore tools or real restored-product test exist; current recovery test is object-level scaffold | NOT IMPLEMENTED | 090; clean restore verifies canonical sites, RBAC, audit, media, privilege hardening and invalid credentials |
| §§14.10, 42.4, 52.2 | Critical governance works on phone; six stable Playwright projects cover real product flows | Human public UI | Six projects run current auth/admin flows; review/accept/discard do not exist and therefore are not proven responsively | PARTIAL | 082–083 add review flows; 091 reruns final product matrix |
| §§51–52 | MVP/release claims match checked-out product | Human/docs | `MVP-PROGRESS.md` says `~100%`, README says all core components are implemented, and reconstruction is labeled post-MVP | CONTRACT/PLANNING CONFLICT | 073 corrects current truth; 091 alone may declare MVP complete |

## Narrowest statements proven by Objectives 065–072

| Objective | What its merged evidence actually proves | It does not prove |
|---|---|---|
| 065 | Runtime ContentModelService wiring and removal of duplicate Agent browser router | Full Agent semantics or product lifecycle |
| 066 | Real capability authentication/lifecycle checks and deployed Agent edge boundary | Human workspace/capability issuance or full semantic authority |
| 067 | Five capability-bound, COW-confined, idempotent, audited create operations: type, field, item, page, component | Update/delete; views/navigation/redirects/theme/media refs; complete Agent API |
| 068 | Real Puck human composition editing through Editor API and normalized composition | Full Agent/Puck parity or review/publication |
| 069 | Seven narrow capability-bound COW read routes and tombstone/workspace identity behavior | Full discovery/read surface or mutations |
| 070 | Immutable content-addressed media upload/storage and lifecycle safety | Promotion-time public media finalization or complete Agent media semantics |
| 071 | Canonical and authorized active-workspace projection through the shared renderer | Immutable review-snapshot rendering or publication |
| 072 | Real confined Chromium preview execution, durable runs and private artifact retrieval | Source inspection, responsive sweep orchestration, MCP completeness or publication |

Historical objectives remain complete for those narrow scopes. None may be
used to mark the broader row complete.

## Dependency-correct remaining sequence

The planned order files are inert until strategy refreshes exact GitHub state,
selects `oap/active`, and signals them. No E2E may provide the actor's product
behavior through direct SQL, ORM, internal service calls, privileged human
routes, filesystem injection or test-only mutation helpers.

```text
073 truthful audit/control-state repair
  -> 074 human Agent workspace/capability product surface
      -> 075 complete editable-domain substrate and shared validators
          -> 076 Agent model/content/view/relation REST+OpenAPI
              -> 077 Agent page/navigation/redirect semantics
                  -> 078 Agent composition/design semantics
                      -> 079 Agent media semantics
                          -> 080 real curated MCP semantic parity
                              -> 081 human edits exact Agent workspace in Puck
                                  -> 082 immutable freeze/review snapshot
                                      -> 083 real accept/discard/promotion/media publication
                                          -> 084 conflict-safe lifecycle proof
                                              -> 085 dynamic News vertical
                                                  -> 086 destructive Agent isolation
                              -> 087 approved-source tools and responsive sweep
                                          -> 088 contractual fixture reconstruction
                                      -> 089 expiry/cleanup/multi-worker lifecycle
                                          -> 090 backup/restore operational proof
                                              -> 091 final hostile MVP truth gate
```

Objectives 084–087 have independent implementation portions but must not run
before every prerequisite their acceptance proof consumes is merged. One
numeric objective remains one PR; `b..z` continuations may repair the same PR.

## Anti-bypass acceptance law

For every major proof, delete or replace the production feature with a fake
success and confirm the test would fail. In particular:

- Agent semantic tests authenticate a real human-created capability and use
  public Agent REST or MCP; fixture setup may seed neutral canonical input but
  cannot perform the claimed Agent behavior.
- Freeze proof fails if immutable snapshot creation or snapshot rendering is
  removed.
- Promotion proof verifies canonical database state and public rendering after
  acceptance, and canonical non-change after discard/failure.
- Browser/source proof fails if real browser execution disappears.
- Destructive proof fails if any required Agent DELETE operation disappears.
- Conflict proof exercises the real freeze/accept worker path, not a standalone
  CAS or reviewer helper.
- Reconstruction creates its dynamic model/site state through semantic product
  interfaces, not a pre-baked model or fixture injection.

## Binary MVP-complete gate

Only Objective 091 may change the verdict to complete, and only after every
matrix row required by §§51.1 and 52 is `COMPLETE — E2E PROVEN` on remote
`main`; all required CI is green; the clean Compose/restore/product E2E runs;
the temporary Chrome exception is removed or remains valid under an explicit
unexpired human decision; and README/progress/roadmap claims match observed
behavior. Checked boxes, report `COMPLETE`, helper-level tests and green CI do
not substitute for the checked-out product.
