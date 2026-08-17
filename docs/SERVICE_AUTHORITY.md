# Backend service authority skeleton

The backend shares one Python distribution but has ten separately startable
process identities. The immutable descriptors in `authority.py` now map to the
exact password-free PostgreSQL privilege-role names without storing a locator
or credential.

| Process | Listener | Lifecycle | Authority class | Database privilege role |
| --- | --- | --- | --- | --- |
| `control-api` | Edge-routed HTTP | HTTP | Control | `slaif_control` |
| `editor-api` | Edge-routed HTTP | HTTP | Editor COW runtime | `slaif_editor_runtime` |
| `agent-api` | Edge-routed HTTP | HTTP | Agent COW runtime | `slaif_agent_runtime` |
| `render-api` | Internal-only HTTP | HTTP | Render reader | `slaif_public_reader`, `slaif_preview_reader` |
| `mcp-adapter` | Edge-routed HTTP | HTTP | Internal HTTP client | None |
| `media-service` | Edge-routed HTTP | HTTP | Media | `slaif_media` |
| `review-worker` | None | Worker | Reviewer | `slaif_reviewer` |
| `scheduler` | None | Worker | Scheduler | `slaif_scheduler` |
| `media-gc` | None | Worker | Media GC | `slaif_gc` |
| `bootstrap` | None | One-shot | Setup owner | `slaif_owner` |

The role manifest, flags, schema owners, COW hardening, and independent
privilege verifier are implemented. Online credential creation/distribution
and pools are not; no long-running process currently opens a database
connection. Bootstrap alone loads its separate one-shot locator.

## Structural boundaries

- Bootstrap alone may receive setup-owner authority. It is not a long-running
  service, and cluster provisioning remains a separate stronger command.
- Review worker alone may later receive reviewer/promotion authority. It has no
  public route.
- Agent API and Editor API use distinct conceptual COW runtime classes. Neither
  receives canonical-write, reviewer, or setup authority.
- MCP adapter has an internal HTTP/client class and no database class. It must
  delegate semantic authorization to the Agent API when that behavior exists.
- Render API is internal-only and its two future database roles are read-only.
- Control, scheduler, media-GC, and media service retain only their narrow
  future classes.
- Worker/bootstrap processes cannot be passed to the shared HTTP application
  factory. HTTP processes cannot be passed to the worker lifecycle.
- There is no generic all-authority descriptor or dependency locator.

Agent-facing identity is not authority to accept, publish, mint capabilities,
run SQL/Alembic, or select site/workspace/operation context from a request.

## Enforcement still required later

Code descriptors do not provide security by themselves. This baseline now
tests PostgreSQL roles and grants, but production separation still requires
separate credentials, internal service authentication, network policy, edge
routing, secret mounts, and deployment topology. Those mechanisms are not
claimed by this skeleton. See [database roles](DATABASE_ROLES.md).

The only current HTTP behavior is correlated, redacted, typed liveness and
readiness. Health evidence is not product readiness or publication authority.
