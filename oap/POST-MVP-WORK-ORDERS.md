# Post-MVP Work Orders — Proposed

These are objectives beyond the contractual MVP scope.
Each needs your confirmation before activation.

## Priority 1: Security Hardening (blocks production)

| # | Objective | Scope | Est. Effort |
|---|---|---|---|
| P1-01 | Replace capability auth placeholder (#36 P0) | Implement real SECURITY DEFINER token validation against `control.capability` table using HMAC digest comparison | 1 objective |
| P1-02 | MCP adapter SSRF deep audit (#45 P0) | Add egress proxy integration, DNS rebinding protection, response size limits | 1 objective |
| P1-03 | Workspace route policy coverage (#40) | Wire workspace routes into `validate_route_policy_coverage` with proper test fixtures | 1 objective |
| P1-04 | Content item soft-delete (#29) | Change hard-delete to workspace tombstone per architecture §8 | 1 objective |

## Priority 2: Feature Completion (needed for full product)

| # | Objective | Scope | Est. Effort |
|---|---|---|---|
| P2-01 | Agent write mutations + idempotency integration | Wire IdempotencyStore into agent API write routes; replace stubs with real COW session writes | 2–3 objectives |
| P2-02 | Puck editor UI integration | Connect Puck editor component to composition API endpoints in the Next.js admin | 2 objectives |
| P2-03 | Selective acceptance implementation | Implement operation dependency graph and partial commit via `asyncpg_cow_reviewer.commit_operations` | 2 objectives |
| P2-04 | Conflict resolution UI | Show conflicts in admin, allow discard/review/new-workspace flow | 1 objective |
| P2-05 | Real file upload for media | Binary upload endpoint with streaming hash, MIME sniffing, storage backend | 2 objectives |

## Priority 3: Production Readiness

| # | Objective | Scope | Est. Effort |
|---|---|---|---|
| P3-01 | OIDC identity provider integration | Optional OIDC auth mode alongside local auth | 2 objectives |
| P3-02 | Backup/PITR documentation + tooling | pg_dump scripts, WAL archiving config, tested restore procedure | 1 objective |
| P3-03 | Prometheus metrics export | Optional metrics endpoint with architecture §15 metric set | 1 objective |
| P3-04 | Source reconstruction (L4 import) | Approved-origin crawling, bounded manifest generation, L4 import pipeline | 3–4 objectives |
| P3-05 | Custom roles + permission overrides UI | Admin UI for managing role permissions beyond built-in catalog | 2 objectives |

## Total estimated: ~25 additional objectives beyond MVP
## Calendar estimate: ~10–15 working days at current pace

## Recommended order
Start with all P1 items (4 objectives) — these are security blockers.
Then P2-01 and P2-02 (4 objectives) — these make the product actually usable.
Then remaining P2 items as needed.
