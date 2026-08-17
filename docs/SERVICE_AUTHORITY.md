# Backend service authority skeleton

The backend shares one Python distribution but has ten separately startable
process identities. The immutable descriptors in `authority.py` record future
dependency and credential classes without storing credentials.

| Process | Listener | Lifecycle | Conceptual authority class | Future database class |
| --- | --- | --- | --- | --- |
| `control-api` | Edge-routed HTTP | HTTP | Control | Control only |
| `editor-api` | Edge-routed HTTP | HTTP | Editor COW runtime | Editor COW runtime |
| `agent-api` | Edge-routed HTTP | HTTP | Agent COW runtime | Agent COW runtime |
| `render-api` | Internal-only HTTP | HTTP | Render reader | Read-only render projection |
| `mcp-adapter` | Edge-routed HTTP | HTTP | Internal HTTP client | None |
| `media-service` | Edge-routed HTTP | HTTP | Media | Media metadata only |
| `review-worker` | None | Worker | Reviewer | Reviewer only |
| `scheduler` | None | Worker | Scheduler | Queue/lifecycle only |
| `media-gc` | None | Worker | Media GC | Reference inspection/delete only |
| `bootstrap` | None | One-shot | Setup owner | Setup owner only |

The table describes intended future wiring, not implemented grants. No current
process opens a database connection or receives a product credential.

## Structural boundaries

- Bootstrap alone may later receive setup-owner authority. It is not a
  long-running service.
- Review worker alone may later receive reviewer/promotion authority. It has no
  public route.
- Agent API and Editor API use distinct conceptual COW runtime classes. Neither
  receives canonical-write, reviewer, or setup authority.
- MCP adapter has an internal HTTP/client class and no database class. It must
  delegate semantic authorization to the Agent API when that behavior exists.
- Render API is internal-only and its future database class is read-only.
- Control, scheduler, media-GC, and media service retain only their narrow
  future classes.
- Worker/bootstrap processes cannot be passed to the shared HTTP application
  factory. HTTP processes cannot be passed to the worker lifecycle.
- There is no generic all-authority descriptor or dependency locator.

Agent-facing identity is not authority to accept, publish, mint capabilities,
run SQL/Alembic, or select site/workspace/operation context from a request.

## Enforcement still required later

Code descriptors do not provide security by themselves. Production separation
must also be enforced by PostgreSQL grants, separate credentials, internal
service authentication, network policy, edge routing, secret mounts, process
commands, and deployment topology. None of those mechanisms is claimed by this
skeleton.

The only current HTTP behavior is correlated, redacted, typed liveness and
readiness. Health evidence is not product readiness or publication authority.
