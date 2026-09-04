# Contract-First MVP Audit

**Audit date:** 2026-09-02
**Authoritative implementation baseline:** `067676314e0d9664d40cb8514ea549b966a4eb2d` (`origin/main`, Objective 076 merged)
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
| §§15.2, 18–20, 24.2 | Human creates an AGENT workspace and one-time capability, monitors/revokes it | Human Control/Web | Merged Objective 074 / [PR #70](https://github.com/ulfe-lmi/slaif-agent-site/pull/70) proves the public Control workspace/capability issuance path, site/CSRF/policy authority, one-time capability use, durable idempotency/audit/revoke behavior, and Control+Agent restart proof | COMPLETE — E2E PROVEN | Preserve the merged 074 evidence; later review/publication authority remains separate |
| §§16.2, 21, 51.1 | Configurable types, fields, items, translations, relations and collection views as COW data | Human Editor and Agent semantic APIs | Merged Objective 075 / [PR #71](https://github.com/ulfe-lmi/slaif-agent-site/pull/71) proves the editable-domain substrate, bounded validators/query contract, locale/navigation/redirect integrity, production COW upgrade, and Agent binding; later semantic families remain separately scoped | COMPLETE — E2E PROVEN | Preserve 075 production-boundary evidence; 076 extends its public Agent surface |
| §§15.4, 24.4–24.5 | Agent model/content semantic CRUD with scopes, COW, validation, idempotency and audit | External agent / REST/OpenAPI | Merged Objective 076 / [PR #72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72), merged as `067676314e0d9664d40cb8514ea549b966a4eb2d`, proves capability-bound public REST model/type/field/item/translation/relation/collection-view semantics with strict scopes/resources/quotas, COW, idempotency, semantic audit, concurrency, and public NGINX/PG14–18 evidence | COMPLETE — E2E PROVEN | Preserve 076 evidence; broader 077–079 page/composition/media semantics remain partial |
| §§15.4, 21.7–22.5, 24.6–24.7 | Agent pages/routes/navigation/redirects/composition/design/media-reference semantics | External agent / REST/OpenAPI | Current `main` contains the pre-077 boundary and the broader contract remains partial. 077-a page structure evidence is on unmerged [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), currently in 077-b prerequisite review; it is not merged product truth | PARTIAL | Active 077-b prerequisites, then later 077 page review defects and 078–079 bounded surfaces |
| §§24.1, 51.1 | Versioned deterministic Agent OpenAPI describes the real public semantic contract | External agent / OpenAPI | Merged Objective 076 / [PR #72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72) provides the canonical generated Agent OpenAPI through the public path, with bidirectional production-handler/route-policy/schema drift checks and required mutation metadata | COMPLETE — E2E PROVEN | Preserve 076 OpenAPI evidence; MCP parity remains Objective 080 and is not implied by OpenAPI completion |
| §25, §51.1 | Curated MCP model/content/composition/design and browser tools delegate to Agent API | External agent / real MCP | Custom `/mcp/v1/tools` lists five reads; `/call` accepts caller-chosen method/path, references absent production configuration and uses a test-only HTTP dependency; no real call test or write-tool proof | SCAFFOLD ONLY | 080; real MCP client tools/list and tools/call E2E through NGINX, with no DB/internal bypass |
| §§14.3, 22.4, 42.4, 52.6 | Human Puck edits the same normalized composition and exact Agent workspace under server policy | Human Web/Puck → Editor API | Objective 068 proves real Puck editing, but its resolver selects/creates a separate HUMAN workspace rather than the Agent workspace later reviewed | PARTIAL | 081 exact-workspace proof; 084/088 reuse it for human adjustment |
| §§14.4, 15.5, 52.6 | Shared trusted canonical and active-workspace renderer | Visitor/human preview / Web+Render | Objective 071 proves canonical and active COW preview with shared renderer, strict authorization and noindex/no-store | IMPLEMENTED — E2E PENDING | Review-snapshot render mode is absent and belongs to 082 |
| §§15.7, 30, 52.7–52.8 | Immutable media bytes, private staging, public finalization, replaceable store | Agent/human Media service and review worker | Objective 070 proves immutable human upload/CAS safety; Agent upload/reference semantics, anonymous canonical-reference-gated bytes, real image rendering and promotion finalization are absent | PARTIAL | Agent media in 079; public finalization/rendering and rollback in 083 |
| §§15.8, 28.1, 30.6, 52.7 | Real confined preview browser runs and private immutable artifacts | External agent / Agent preview routes | Objective 072 proves real Chromium, capability-bound durable runs, six artifacts, retrieval, restart/outage/revoke/foreign negatives, and canonical independence | COMPLETE — E2E PROVEN | Preserve; do not restart or replace 072 |
| §§23, 24.8, 25.2, 42.4, 51.1 | Approved-origin source inspection and quota-controlled responsive sweep | Level-4 agent / curated REST+MCP | No source tools or source-run production path; preview contract runs one route/target and has no product responsive-sweep orchestration | NOT IMPLEMENTED | 087; DNS/redirect/egress negatives plus real multi-target observation |
| §§26–27, 42.3, 52.8 | Every Agent mutation is durably idempotent and semantically audited in the COW transaction | External agent / semantic services | Merged Objective 076 / [PR #72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72) completes the model/type/field/item/translation/relation/collection-view mutation families with exact idempotency, semantic audit, COW, quota, and concurrency evidence; the broader 077–079 page/composition/design/media mutation surface remains partial | PARTIAL | 077–079 extend the invariant; Objective 091 audits complete route coverage |
| §§10 I-9, 17.5, 28.2, 52.6 | Freeze drains writes, revokes capability and creates immutable complete review snapshot rendered thereafter | Human Control → review worker → Render | `review_snapshot` table/job/worker/path do not exist and current freeze SQL does not create an immutable snapshot. Agent mutations now use the shared workspace mutation lock, but full freeze drain/snapshot rendering remains absent | NOT IMPLEMENTED | 082; race-safe freeze, immutable projection/digest/audit closure and snapshot rendering E2E |
| §§15.9, 29.1–29.3, 52.3 | Human-only full accept and discard execute real reviewer COW lifecycle atomically | Human Control → review worker | Control lifecycle routes are not installed; SQL helpers change status only; review worker is idle; `promotion.py` helper is disconnected | SCAFFOLD ONLY | 083; exact snapshot, one reviewer transaction, canonical/public/media/audit proof |
| §§17.4, 29.4, 42.3, 53.5 | Reviewed snapshot cannot silently overwrite later canonical state | Human accept lifecycle | Low-level foundation conflict tests exist, but no immutable-snapshot accept lifecycle exists | NOT IMPLEMENTED | 084 immediately after 083; stale-revision and foundation-row conflicts through product surfaces |
| §§21.6, 42.4, 52.5, 53.2 | Level 4 dynamically creates News/list/detail/navigation without Alembic and publishes after review | External agent + human / product surfaces | Old planned News proof assumed operations and same-workspace Puck behavior that do not exist | NOT IMPLEMENTED | 085 after 074–084; no ORM/SQL/fixture/internal-API mutation |
| §§42.3, 42.5, 53.4 | Legitimate Level-4 agent destructively deletes all editable site state only in its workspace | External agent / Agent API | Existing tests use direct COW SQL for tombstones or cover only five creates; no complete destructive Agent surface | NOT IMPLEMENTED | 086; real Agent DELETE/reset, canonical/other-site/users unchanged, real discard |
| §§23, 42.6, 51.1, 52.6, 53.3 | One fixture reconstruction with dynamic model, source inspection, responsive iteration, Puck adjustment and promotion | Level-4 agent + human / source+semantic+preview+review interfaces | Absent and incorrectly classified as post-MVP in `POST-MVP-WORK-ORDERS.md` | CONTRACT/PLANNING CONFLICT | 088 after 074–087; production interfaces only and code/schema unchanged |
| §§38, 41, 52.8 | Durable jobs, expiry, cleanup and multiple worker claims | Scheduler/review/GC workers | Browser queue is real; generic review/scheduler/media-GC processes remain idle placeholders and no general `control.job` lifecycle exists | PARTIAL | 082–083 introduce review jobs; 089 closes expiry/GC/multi-worker recovery |
| §§39, 42.2, 52.8 | Coordinated database/media backup and clean restore test | Operator tooling | Documentation discusses policy, but no backup/restore tools or real restored-product test exist; current recovery test is object-level scaffold | NOT IMPLEMENTED | 090; clean restore verifies canonical sites, RBAC, audit, media, privilege hardening and invalid credentials |
| §§14.10, 42.4, 52.2 | Critical governance works on phone; six stable Playwright projects cover real product flows | Human public UI | Six projects run current auth/admin flows; review/accept/discard do not exist and therefore are not proven responsively | PARTIAL | 082–083 add review flows; 091 reruns final product matrix |
| §§51–52 | MVP/release claims match checked-out product | Human/docs | Merged Objective 073 / [PR #69](https://github.com/ulfe-lmi/slaif-agent-site/pull/69) repaired the README and current-state claims to describe truthful interim 065–072 evidence and preserve the not-complete/future sequence; this round updates the ledgers to the later 076 baseline and keeps reconstruction and final release proof in the MVP contract | COMPLETE — CURRENT-STATE AUDITED | Objective 091 alone may declare the contractual MVP complete or production-ready |

## Narrowest statements proven by Objectives 065–076

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
| 073 | Truthful current-state audit, README/roadmap repair, and dependency-correct sequencing | Any product-completion or release claim |
| 074 | Real public human Agent workspace/capability issuance, policy/CSRF/site authority, idempotency, audit, revoke, and Control+Agent restart proof | Review, promotion, publication, or complete Agent semantic API |
| 075 | Complete editable-domain substrate and bounded validators/query contract with production COW upgrade and Agent binding | Complete public Agent model/content/page/composition/media/MCP surface |
| 076 | Public capability-bound Agent model/type/field/item/translation/relation/collection-view REST semantics, strict scopes/resources/quotas/idempotency/audit/COW/concurrency, generated OpenAPI, public NGINX evidence, and PG14–18 CI | Page/navigation/redirect/composition/design/media completion, MCP parity, review, promotion, or MVP completion |

Historical objectives remain complete for those narrow scopes. None may be
used to mark the broader row complete.

## Completed prefix and dependency-correct remaining sequence

The planned order files are inert until strategy refreshes exact GitHub state,
selects `oap/active`, and signals them. No E2E may provide the actor's product
behavior through direct SQL, ORM, internal service calls, privileged human
routes, filesystem injection or test-only mutation helpers.

```text
COMPLETED ON REMOTE MAIN:
073 truthful audit/control-state repair
  -> 074 human Agent workspace/capability product surface
      -> 075 complete editable-domain substrate and shared validators
          -> 076 Agent model/content/view/relation REST+OpenAPI

ACTIVE / REMAINING:
077 page/navigation/redirect semantics (077-b active on unmerged PR #74)
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
