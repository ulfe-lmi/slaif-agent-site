# Human site authorization

Revision `014_001` provides the non-HTTP foundation for site-scoped human
membership and built-in role-based authorization. It adds no membership route
or UI.

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

Every mutation rechecks active actor, site, target, actor permissions, ceiling,
and target role under row locks in the same transaction. Non-administrators
cannot change themselves, cross sites, exceed their authority, grant system
permissions, or grant publication without holding it. Disabled users cannot be
activated. Stale/concurrent, cancelled, constraint, and policy failures roll
back without partial override changes.

`HumanSiteContext` is immutable and constructed only from trusted database
results. It contains user/site IDs, built-in role, membership version,
explicit/effective ceiling, effective permissions, and the existing global
administrator fact. It contains no cookie, token, digest, credential, or
request-selected identity. Unknown, inactive, stale, and cross-site cases share
the stable denial boundary.

## Database authority and limitations

The owner controls all five catalog/membership relations. `slaif_control` has
no direct relation access and receives only named function execution. Agent,
editor, public/preview reader, reviewer, scheduler, media, and GC roles have
neither relation access nor RBAC function execution.

This remains trusted institutional multi-site tenancy, not hostile public SaaS
isolation or RLS. Membership HTTP/UI, invitations, custom roles, workspaces,
capabilities, content, and publication execution are not implemented yet.
