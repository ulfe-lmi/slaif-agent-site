# MVP Progress Tracker

Updated after each merged work order.

| Phase | Objective | Status | PR | Est. Complete |
|---|---|---|---|---|
| 0 | Foundation qualification | ✅ | #4, #11 | 100% |
| 1 | Monorepo/Compose/DB/bootstrap | ✅ | #9–#14 | 100% |
| 2 | Auth/RBAC/sites/memberships | ✅ | #15, #23, #24 | 100% |
| 3 | Content model CRUD (types, fields, items, views) | ✅ | #27–#29, #32 | 100% |
| 3 | Navigation + theme CRUD | ✅ | #31 | 100% |
| 3 | Page CRUD | ✅ | #32 | 100% |
| 4a | Component catalog + composition schema | ✅ | #33 | 100% |
| 4b | Page composition tree CRUD | ✅ | #34 | 100% |
| 4c | Media service foundation | ✅ | #35 | 100% (metadata CRUD; file upload/storage is future) |
| 4d | Shared renderer | ✅ | #42 | 100% (Puck adapter is future) |
| 5 | Semantic REST (read + write stubs) | ✅ | #36, #37 | ~40% (write stubs done; idempotency/batches remain) |
| 5 | MCP adapter | ⬜ | — | 0% |
| 6 | Browser confinement API | ✅ | #44 | ~30% (API routes done; actual Playwright integration/E2E remain) |
| 7 | Workspace lifecycle + HTTP + accept | ✅ | #38, #40, #43 | ~50% (accept done; conflict/COW-promotion remain) |
| 8 | Source reconstruction (L4 import) | ⬜ | — | 0% |
| 9 | Hardening/E2E/SBOM/full matrix | ⬜ | — | 0% |

## Overall estimate: ~65%

## Remaining critical path
1. ~~Finish media (022)~~ → DONE (#35)
2. Puck adapter + shared renderer (biggest single remaining item)
3. Agent API routes (semantic REST + MCP)
4. Workspace lifecycle: freeze/snapshot/promotion/discard
5. Browser confinement + E2E
6. Full security/concurrency/recovery hardening

## CRITICAL.md review queue
| PR | Risk | Priority |
|---|---|---|
| #28 | Privilege allowlist modification | P1 |
| #29 | Content item hard-delete | P1 |
| #30–#34 | CRUD route authorization patterns | P2 |
