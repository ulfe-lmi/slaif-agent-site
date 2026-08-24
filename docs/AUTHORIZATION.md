# Human site authorization

The current-human admin read model is UX support, not an authority source.
Trusted session code supplies the user UUID and FastAPI parses the site UUID
only from the route. Owner-controlled fixed-search-path functions filter global
or exact active-membership facts; `slaif_control` receives EXECUTE only and no
direct relation grant. URL selection and client visibility never authorize a
crafted API call.

Revision `014_001` provides site-scoped human membership and built-in
role-based authorization. Control exposes the bounded catalog and membership
HTTP surface described in [the API guide](API.md). The responsive administration
UI consumes that exact surface for existing user UUIDs and never substitutes
client-side role logic for server authorization.

## Built-in roles

| Role | Ceiling | Defaults |
|---|---:|---|
| Site Owner | 4 | L1–L4 editorial authority, one-site governance, membership/role, workspace/capability policy, audit, domains, and publish |
| Site Architect | 4 | L1–L4 editorial authority; no membership or publish by default |
| Site Designer | 3 | Common read plus L1–L3 |
| Site Editor | 2 | Common read plus L1–L2 |
| Content Editor | 1 | Common read plus L1 |
| Reviewer | 0 | Common read, validation/preview, all-workspace read, and audit read |
| Viewer | 0 | Common read only |

The exact permission keys and tier boundaries are executable constants in
`human_authorization.catalog` and immutable migration rows. Platform
Administrator is absent from the site-role catalog. It is global installation
authority that may assign the first Site Owner, never a site-role shortcut or
agent-delegatable authority.

## Effective permission rules

Effective permissions are role defaults union valid `ALLOW` overrides minus
`DENY` overrides. `DENY` wins. Only site-assignable catalog permissions may be
allowed. Installation and system permissions—including identity, migrations,
COW administration, jobs, GC, backup/restore, component code, server
configuration, and secrets—cannot be membership-granted.

The effective delegation ceiling is the lower of the role default and stored
explicit ceiling. It constrains later delegation; it implies no permission.
Ceiling 4 never implies `site:publish`. Architect lacks publish by default, an
authorized override can add only publish, and a deny can remove Owner publish
without changing its ceiling or editorial scopes.

## Lifecycle and transactional policy

A membership is keyed by exact site and user, references a built-in role, is
`ACTIVE` or `INACTIVE`, and has a monotonically increasing version. Updates
require the expected version and replace all overrides atomically. Deactivation
preserves the row and immediately denies authorization.

Every mutation uses one lock order: active site; actor and target user rows in
UUID order; their current Platform Administrator assignments; actor and target
membership rows; then their override rows. It evaluates authority only after
those locks are held. A revocation, disable, downgrade, ceiling reduction, or
permission removal that commits first therefore denies a later grant. A grant
that holds the locks first completes before a waiting revocation, giving both
commits one serial explanation. Cancellation, timeout, deadlock, or
serialization failure rolls back the complete target mutation.

Non-administrators
cannot change themselves, cross sites, exceed their authority, grant system
permissions, or grant publication without holding it. Disabled users cannot be
activated. Stale/concurrent, cancelled, constraint, and policy failures roll
back without partial override changes.

`HumanSiteContext` is immutable and constructed only from trusted database
results. It contains user/site IDs, built-in role, membership version,
explicit/effective ceiling, effective permissions, and the existing global
administrator fact for that target. Active and inactive results never copy the
actor's administrator status. It contains no cookie, token, digest, credential,
or request-selected identity. Unknown, inactive, stale, and cross-site cases
share the stable denial boundary.

## HTTP authorization chain

`GET /roles` and `GET /permissions` require a current human session and expose
only immutable built-in facts. Membership reads require either a current global
Platform Administrator assignment or the exact site's active membership with
both `membership:manage` and `role:manage`. Mutations also require the one bound
CSRF decision and reassert actor authority inside the database transaction.
Path UUIDs are parsed input, not authority: Control resolves the active site and
current server-side membership version before use. Deactivation is HTTP
`DELETE` semantics but updates the row to `INACTIVE`; it never hard-deletes it.

Site governance uses the same reusable current-site chain. Reads require
`site:read`, profile writes `site-policy:manage`, and domain writes
`site-domain:manage`. The server fetches the current membership version and
calls the database permission function immediately before the operation.
Inactive, disabled, stale, archived-for-member, unknown, and cross-site
authority fails closed. Create and archive remain global, and archive also
checks recent authentication after the atomic session/CSRF decision.

## Database authority and limitations

The owner controls all five catalog/membership relations. `slaif_control` has
no direct relation access and receives only named function execution. Agent,
editor, public/preview reader, reviewer, scheduler, media, and GC roles have
neither relation access nor RBAC function execution.

Capability-authenticated browser reservation is a separate Agent boundary. The
trusted capability fixes site, workspace, delegator, scopes, expiry, approved
Chromium targets, total/concurrent run limits, screenshot and artifact-byte
budgets, route/evidence bounds, duration, and attempts. External create input
contains only contract version, normalized route, one target, and unique
allowlisted evidence. The database obtains the shared workspace lock and then
rechecks `preview:inspect`, capability, workspace, site, and immutable binding
before reserving a run. Caller-supplied site/workspace/delegator facts cannot
widen authority. Run and retained artifact reads repeat the exact binding and
return non-leaking absence.

This remains trusted institutional multi-site tenancy, not hostile public SaaS
isolation or RLS. The membership UI does not provision identities or implement
invitations or custom roles. Browser HTTP dispatch, worker execution, and
publication execution remain unimplemented.
