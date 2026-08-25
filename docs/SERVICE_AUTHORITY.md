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

The role manifest, local login principals, schema owners, COW hardening,
independent privilege verifier, container networks, and edge routing are
implemented. Control API receives `slaif_control_login`, Editor API receives
the distinct `slaif_editor_login` for content COW plus Control's separate human
authorization pool, and Agent API receives `slaif_agent_login`; each opens only
its bounded lifespan-owned pools and declared least-privilege functions.
Bootstrap alone mounts the stronger one-shot locators. Web, MCP, and browser
worker remain database-credential-free.

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
- Control has only readiness-function authority. Scheduler, media-GC, and
  media service retain only their narrow future classes.
- Worker/bootstrap processes cannot be passed to the shared HTTP application
  factory. HTTP processes cannot be passed to the worker lifecycle.
- There is no generic all-authority descriptor or dependency locator.

Agent-facing identity is not authority to accept, publish, mint capabilities,
run SQL/Alembic, or select site/workspace/operation context from a request.

Media service is human-authenticated and owns only immutable local byte staging,
content-addressed publication, and the narrow Media metadata/auth functions.
It never accepts Agent capabilities, chooses a workspace from a request, serves
anonymous bytes, or receives reviewer/publication authority.

## Deployment enforcement

Code descriptors do not provide security by themselves. Compose now separates
edge, application, database, and browser networks. Initializer/PostgreSQL/
bootstrap use the private master secret volume; initializer copies only the
Control and Editor DSNs into their separate volumes, mounted read-only only by
their owning processes. Only NGINX publishes loopback port 8080. Browser
worker is on an internal network shared only with Agent API and has no
database, edge, host, mount, Docker-socket, Playwright, or browser-command
authority. See [deployment](DEPLOYMENT.md),
[database connections](DATABASE_CONNECTIONS.md), and
[database roles](DATABASE_ROLES.md).

Internal service authentication, pools for non-Editor/Agent processes, browser
sandbox and egress enforcement, production TLS automation, and product
authorization remain later work. Network membership alone is not authority.

The Agent database role has an exact durable browser-run function surface. The
public capability-authenticated Agent routes now use only authenticate, begin,
get, and artifact-list; byte retrieval remains an honest 404. Claim, renew,
release, complete, and artifact-register remain internal adapter primitives for
a later Agent-owned dispatcher. Agent has no direct Control/audit table grant,
and public create never receives a worker or signing credential.

Agent and Render alone load the same isolated file-backed browser signing key.
Agent owns signing; Render owns verification plus one exact preview-reader DB
function that consumes/rechecks a nonce digest under the workspace lock. Web
sees only a request-scoped signed token header and forwards it server-side; it
does not have the key. The browser worker still has no database credential,
signing key, Playwright package, browser binary, or artifact mount.

The Agent HTTP behavior additionally includes the capability-authenticated
bounded COW semantic read and create surfaces documented in [the API guide](API.md).
Agent GETs use the real `slaif_agent_login`/`slaif_agent_runtime` identity,
workspace overlay precedence, canonical fallback, and narrow read wrappers;
they do not create mutation/idempotency/audit state. Control readiness includes
its database boundary; Control liveness remains
process-only. Health evidence is not product readiness or publication
authority.
