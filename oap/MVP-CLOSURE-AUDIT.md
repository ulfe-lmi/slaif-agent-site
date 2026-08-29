# MVP Closure Audit — Adversarial Implementation vs Architecture

**Date**: 2026-08-23
**Authoritative SHA**: 212390f (main)
**Auditor**: Strategic model (independent, adversarial)

---

## 1. Verdict

**The contractual MVP is NOT complete.**

> **Superseded baseline (2026-08-30):** This historical audit and its findings
> are retained as evidence. Current status, scope, and queue truth are
> superseded by [`oap/MVP-CONTRACT-AUDIT.md`](MVP-CONTRACT-AUDIT.md), which is
> evaluated against merged Objective 072 commit
> `bcaddc41f9ef4e779dd1a8c9a41eb08462250d53`.

The repository contains architecture-scaffold code for every subsystem,
but the majority of §51.1 contractual-MVP behaviors are stubs, metadata-only
implementations, or missing entirely. The `oap/MVP-PROGRESS.md` claim of
"~100%" is based on interface-presence tests and import checks, not on
working product functionality exercised through public API paths.

---

## 2. §51.1 Contractual MVP Matrix

Each row maps to a §51.1 bullet. Classification uses the strictest evidence.

| # | §51.1 Requirement | Classification | Evidence |
|---|---|---|---|
| 1 | Product named `slaif-agent-site` | ✅ IMPLEMENTED_AND_E2E_PROVEN | Repo name, CI, Compose project name |
| 2 | Self-hosted one-command Compose stack | ✅ IMPLEMENTED_AND_E2E_PROVEN | `compose.yaml`, smoke.sh passes, CI verifies |
| 3 | NGINX OSS edge + Apache example | ✅ IMPLEMENTED_AND_E2E_PROVEN | `infra/nginx/`, `infra/apache/`, CI checks |
| 4 | Secure local first-run admin setup | ✅ IMPLEMENTED_AND_E2E_PROVEN | Setup flow tested in CI and manually |
| 5 | Site-scoped users, roles, memberships, ceilings | ✅ IMPLEMENTED_AND_E2E_PROVEN | Migration 014, RBAC tests |
| 6 | Multi-site schema + one seeded demo site | ⚠️ PARTIAL | Schema exists; no seeded demo site in Compose |
| 7 | Four agent delegation presets | ✅ IMPLEMENTED | Scope catalog, presets defined; not E2E-proven through agent API |
| 8 | Configurable content types, fields, items, relations, views | ⚠️ PARTIAL | DB tables exist; Editor API routes exist; **routes fail at runtime** because `ControlDatabase.content_model_service()` doesn't exist; **Agent API write routes are 503 stubs** |
| 9 | Normalized composition model + Puck human editor | ❌ STUB | Composition CRUD routes exist but call `app.state.content_model_service` which is never set; **no Puck dependency in web app**; no Puck editor UI |
| 10 | Shared public/preview renderer + trusted catalog | ❌ NOT_IMPLEMENTED | Render API only resolves site context; no page rendering; no preview rendering |
| 11 | Agent REST/OpenAPI and MCP tools for model/content/composition/design | ❌ STUB | Agent API read routes return data from ContentModelService but **all write routes return 503**; MCP adapter is a thin HTTP proxy with no real mutation tools; **no OpenAPI schema generation** |
| 12 | Internal Playwright browser worker with screenshot/diagnostic/responsive tools | ❌ STUB | `browser-worker/src/server.ts` is a health-check-only HTTP server; **no Playwright import**; no screenshot/snapshot/diagnostic capability |
| 13 | Desktop Chromium/Firefox/WebKit, tablet, mobile E2E targets | ⚠️ PARTIAL | Playwright config defines 8 projects; CI runs them; **they test auth/admin UI, not the agent content/composition flow** |
| 14 | Immutable media + private browser artifacts | ❌ METADATA_ONLY | Media metadata CRUD exists; **no binary upload, no content-addressed storage, no immutable byte handling**; browser artifacts don't exist because browser worker is a stub |
| 15 | Capability TTL/revoke | ⚠️ PARTIAL | Capability table and revoke route exist; **no TTL enforcement** (no scheduler integration); **auth is placeholder** (agent_http.py uses no real token validation) |
| 16 | Semantic audit | ⚠️ PARTIAL | AuditEvent class with hash-chain exists; **not integrated into any mutation path**; no audit table in DB |
| 17 | Private preview + immutable review snapshot | ❌ NOT_IMPLEMENTED | No snapshot creation code; no immutable evidence bundle; no preview rendering |
| 18 | Full accept/discard | ⚠️ PARTIAL | Accept/discard routes exist; **they only update workspace status**; no actual COW promotion or discard is invoked |
| 19 | Conflict-safe promotion | ⚠️ PARTIAL | Promotion service wraps `asyncpg_cow_reviewer`; **never called from any HTTP route or integration test with real DB**; mocked tests only |
| 20 | Destructive demo | ❌ NOT_IMPLEMENTED | No test or demonstration of workspace destruction leaving canonical unchanged |
| 21 | One fixture reconstruction | ❌ NOT_IMPLEMENTED | No source inspection, no reconstruction pipeline, no fixture |

---

## 3. §52 Acceptance Criteria Matrix

| §52 | Criterion | Classification | Gap |
|---|---|---|---|
| 52.1 | Clean clone + `docker compose up --build` | ✅ PROVEN | CI + local verification |
| 52.1 | No hosted dependency | ✅ PROVEN | |
| 52.1 | Only NGINX publishes 8080 | ✅ PROVEN | |
| 52.1 | Browser worker internal | ⚠️ STUB | Health-check server exists; no actual browser |
| 52.1 | One-time admin setup | ✅ PROVEN | |
| 52.1 | Apache alternative | ✅ PROVEN | |
| 52.2 | Admin creates site + assigns owner | ✅ PROVEN | |
| 52.2 | Site Owner manages memberships/ceilings | ✅ PROVEN | |
| 52.2 | Different roles on different sites | ✅ PROVEN | |
| 52.2 | Non-member cannot access another site | ✅ PROVEN | |
| 52.2 | Review/publication on desktop+phone | ❌ NOT_PROVEN | No publication flow to test |
| 52.3 | Agent cannot publish | ⚠️ TRIVIALLY_TRUE | True because agent write routes are 503 stubs, not because of security enforcement |
| 52.3 | Agent cannot choose session UUID | ⚠️ TRIVIALLY_TRUE | No session selection exists at all |
| 52.3 | Agent cannot use SQL | ⚠️ TRIVIALLY_TRUE | No SQL path exists |
| 52.3 | Agent cannot run Alembic/register code | ⚠️ TRIVIALLY_TRUE | |
| 52.3 | Agent API process cannot call reviewer | ⚠️ TRIVIALLY_TRUE | |
| 52.3 | Workspace deletion doesn't affect canonical | ❌ NOT_PROVEN | No COW workspace writes exist to test |
| 52.3 | Conflict cannot overwrite canonical | ❌ NOT_PROVEN | |
| 52.3 | Failed promotion leaves canonical unchanged | ❌ NOT_PROVEN | |
| 52.3 | Browser sweep doesn't publish | ❌ NOT_PROVEN | No browser sweep exists |
| 52.4 | Four presets map to scopes | ✅ IMPLEMENTED | |
| 52.4 | Cannot delegate above ceiling | ✅ IMPLEMENTED | |
| 52.4 | Publication separate from editing | ✅ IMPLEMENTED | |
| 52.4 | L4 reconstructs but can't edit code | ⚠️ NOT_PROVEN | No reconstruction exists |
| 52.5 | L4 creates News without Alembic | ❌ NOT_PROVEN | Agent write stubs prevent this |
| 52.5 | Items validate against definition versions | ⚠️ PARTIAL | Validation code exists; never exercised E2E |
| 52.5 | Agents cannot add executable primitives | ✅ IMPLEMENTED | FieldPrimitive enum |
| 52.5 | Schema changes developer-controlled | ✅ IMPLEMENTED | |
| 52.6 | Human edits through Puck | ❌ NOT_IMPLEMENTED | No Puck dependency or editor |
| 52.6 | Puck and agents persist same composition | ❌ NOT_IMPLEMENTED | |
| 52.6 | Public and preview use same components | ❌ NOT_IMPLEMENTED | No renderer |
| 52.6 | Source reconstructed via L4 | ❌ NOT_IMPLEMENTED | |
| 52.6 | Preview private and not indexed | ❌ NOT_IMPLEMENTED | No preview exists |
| 52.7 | Agent screenshots own preview | ❌ STUB | Browser worker is health-check only |
| 52.7 | Quota-controlled sweeps | ❌ NOT_IMPLEMENTED | |
| 52.7 | Browser can't reach PG/Docker/host | ⚠️ TRIVIALLY_TRUE | No browser exists to test |
| 52.7 | Source constrained to approved origin | ❌ NOT_IMPLEMENTED | |
| 52.7 | Artifacts private/immutable/scoped | ❌ NOT_IMPLEMENTED | |
| 52.8 | Audit identifies every mutation | ⚠️ PARTIAL | AuditEvent class exists; not integrated |
| 52.8 | Expiry/revocation works | ⚠️ PARTIAL | Routes exist; no scheduler enforcement |
| 52.8 | Cleanup idempotent | ⚠️ PARTIAL | |
| 52.8 | Backup/restore documented+tested | ⚠️ PARTIAL | Docs exist; not tested |
| 52.8 | License audit passes | ✅ PROVEN | |
| 52.8 | OCI SBOMs generated | ✅ IMPLEMENTED | generate_sbom.py |
| 52.8 | Stateless replicas behind NGINX | ✅ IMPLEMENTED | |
| 52.8 | Multiple workers claim jobs safely | ⚠️ PARTIAL | Job queue exists; not tested under load |
| 52.8 | Shared MediaStore replaceable | ❌ NOT_IMPLEMENTED | No MediaStore abstraction |

---

## 4. Defining Vertical Status (§9.3)

| Step | Status | Blocker |
|---|---|---|
| 1. Jane logs in, selects site | ✅ Works | — |
| 2. Jane creates Site Architect workspace | ⚠️ Route exists, not E2E-tested | — |
| 3. System creates workspace UUID + capability | ⚠️ Route exists, not E2E-tested | — |
| 4. Jane gives capability to agent | ⚠️ Token format exists | Auth placeholder |
| 5. Agent discovers primitives/model/catalog | ❌ 503 | Agent API read routes don't connect to service |
| 6. Agent creates types/items/pages/composition via semantic tools | ❌ 503 | Write routes are stubs |
| 7. Agent requests Playwright screenshots | ❌ STUB | Browser worker has no Playwright |
| 8. Published site unchanged | ❌ NOT_PROVEN | No workspace writes exist to test isolation |
| 9. Jane opens composition in Puck | ❌ NOT_IMPLEMENTED | No Puck editor |
| 10. System creates immutable snapshot | ❌ NOT_IMPLEMENTED | |
| 11. Jane accepts or discards | ⚠️ Route exists | No actual COW promotion |
| 12. Review worker promotes atomically | ❌ NOT_PROVEN | Service exists; never called from HTTP path |

**Defining vertical: 2/12 steps work. 10/12 are stubs, not implemented, or unproven.**

---

## 5. §53 Demonstration Status

| Demo | Status | Blocker |
|---|---|---|
| 53.1 Start | ✅ Works | — |
| 53.2 Dynamic News | ❌ BLOCKED | Agent write stubs |
| 53.3 Whole-site reconstruction | ❌ NOT_IMPLEMENTED | Multiple missing subsystems |
| 53.4 Destructive safety | ❌ BLOCKED | No COW workspace writes |
| 53.5 Concurrent conflict | ❌ BLOCKED | No COW workspace writes |

---

## 6. Security / P0 Blockers

| ID | Description | Source |
|---|---|---|
| S1 | Capability auth placeholder — `agent_http.py` has `_authenticate()` that checks `Bearer sas2_` prefix but never validates against DB or checks expiry/revocation | #36 |
| S2 | MCP adapter SSRF — CodeQL flagged; mitigated with path allowlist but needs human review | #45 |
| S3 | `ControlDatabase.content_model_service()` doesn't exist — editor API routes will crash at runtime | This audit |
| S4 | Agent API browser_router included twice in app.py | This audit |
| S5 | No TTL enforcement — capability expiry is stored but never checked | This audit |

---

## 7. Stubs, Mocks, and Placeholders

| File | What it claims | What it actually does |
|---|---|---|
| `agent_api/agent_http.py` | Agent semantic API | Read routes call `app.state.content_model_service` (never set); write routes return 503 |
| `browser_worker/src/server.ts` | Playwright browser worker | Health-check-only HTTP server; no Playwright import |
| `media_service/app.py` | Media service | Health-check-only; no upload/storage/serve |
| `render_api/site_http.py` | Page renderer | Only resolves site context; doesn't render pages |
| `editor_api/*.py` routes | Content CRUD | Call `database.content_model_service()` which doesn't exist on ControlDatabase |
| `agent_state/promotion.py` | COW promotion | Wraps asyncpg_cow_reviewer but never called from any HTTP route |
| `agent_state/idempotency.py` | Persistent idempotency | In-memory dict; lost on restart |
| `agent_state/audit.py` | Semantic audit | In-memory class; no DB table; not integrated into mutations |
| `packages/composition-schema/src/puck-adapter.ts` | Puck adapter | Type conversion only; no Puck dependency or editor |
| `mcp_adapter/mcp_http.py` | MCP tools | Read-only proxy; no mutation tools |

---

## 8. Documentation Discrepancies

| Document | Claims | Reality |
|---|---|---|
| `MVP-PROGRESS.md` | ~100% | ~15% of contractual MVP behavior works |
| `CRITICAL.md` | 17 review items | Accurate but understated — the real issue is systemic |
| README | "All core architectural components are implemented and wired together" | Components exist as code but most are not wired to work at runtime |

---

## 9. Dependency Graph of Remaining Work

<!-- markdownlint-disable MD040 -->

```
<!-- markdownlint-enable MD040 -->
P1-A: Fix ControlDatabase.content_model_service()
      └── Editor API routes actually work
      └── Agent API read routes actually work

P1-B: Agent API real mutations via COW sessions
      ├── Requires: P1-A (service wiring)
      ├── Requires: Capability auth (replace placeholder)
      └── Enables: Dynamic News, destructive demo, conflict demo

P1-C: Capability auth (real token validation)
      ├── Requires: Capability table (exists)
      └── Enables: Agent API auth

P2-A: Puck editor UI
      ├── Requires: Puck npm dependency
      ├── Requires: Composition API (exists, needs P1-A fix)
      └── Enables: §52.6 human editing

P2-B: Media binary upload/storage
      ├── Requires: Storage backend
      └── Enables: §52.7 media immutability

P2-C: Render API (actual page rendering)
      ├── Requires: Shared renderer components (exist)
      └── Enables: Preview, review snapshots

P3-A: Browser worker with real Playwright
      ├── Requires: Playwright dependency in browser-worker
      └── Enables: §52.7 visual loop

P3-B: Review snapshot + promotion integration
      ├── Requires: P1-B (COW sessions)
      ├── Requires: P3-A (browser evidence)
      └── Enables: §52.3 conflict safety, §53 demos
```

---

## 10. Items Deferred to §51.2 (NOT MVP blockers)

- Selective acceptance UI (selective accept route exists but UI is §51.2)
- Selective preview
- Two-person approval
- Richer declarative model-change mappings
- PostgreSQL RLS
- Distributed shared media backend
- Firefox/WebKit runtime agent feedback beyond CI
- Custom human role designer
- Field-level rebase
- WordPress adapter
- Second non-website consumer / Agent-State extraction

---

## 11. Evidence-Based Percentages

| Dimension | Percentage | Basis |
|---|---|---|
| Architecture coverage (code exists for each component) | ~85% | Most modules/files exist; some are health-check-only shells |
| Contractual MVP implementation (code does what §51.1 requires) | ~20% | DB schema, auth, RBAC, basic CRUD work; COW integration, agent mutations, Puck, renderer, media, browser, promotion are stubs or missing |
| End-to-end MVP evidence (defining vertical works through public APIs) | ~5% | Only steps 1 (login) and partial 2 (workspace creation route) work; steps 3-12 are stubs or missing |
| Production/internet-exposure readiness | ~10% | Auth, RBAC, CSP, edge config work; but capability auth is placeholder, no real mutations, no media, no rendering |

---

## 12. Recommended Closure Sequence

### Priority A: Fix runtime wiring (blocks everything else)

1. Add `content_model_service()` to ControlDatabase
2. Fix duplicate browser_router include in agent app
3. Wire ContentModelService into app.state for agent/editor APIs

### Priority B: Capability auth (security blocker)

4. Implement real token validation against control.capability table
5. Add TTL enforcement

### Priority C: Agent API mutations via COW sessions

6. Wire agent write routes to ContentModelService via asyncpg_cow_session
7. Add persistent idempotency (PostgreSQL-backed)
8. Add semantic audit integration

### Priority D: Puck editor

9. Add @pucklabs/puck dependency to web app
10. Create Puck editor page using composition API
11. Verify round-trip through UI

### Priority E: Media binary upload

12. Add multipart upload endpoint to media service
13. Content-addressed storage (SHA-256 digest → filesystem)
14. Serve media through authenticated routes

### Priority F: Render API

15. Implement page composition rendering using shared renderer
16. Add preview rendering with workspace COW context

### Priority G: Browser worker with real Playwright

17. Add Playwright dependency to browser-worker
18. Implement screenshot/snapshot/diagnostic execution
19. Store artifacts as immutable workspace-scoped objects

### Priority H: Review snapshot + real promotion

20. Implement freeze: drain writes → create snapshot → revoke capabilities
21. Implement accept: call promotion service with real reviewer
22. Implement discard: call discard service
23. Add conflict detection and structured error response

### Priority I: Demos

24. Dynamic News E2E test
25. Destructive safety E2E test
26. Concurrent conflict E2E test
27. One fixture reconstruction test
