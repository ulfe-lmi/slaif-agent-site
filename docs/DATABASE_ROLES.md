# PostgreSQL role boundary

Agent-Site defines ten password-free PostgreSQL privilege roles. The executable
manifest is `slaif_agent_site.db.roles.DATABASE_ROLES`; it is the only source
used by the provisioner and tests.

## Exact inventory

Every role is `NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
NOREPLICATION NOBYPASSRLS`.

| Privilege role | Credential consumer | Implemented baseline authority |
| --- | --- | --- |
| `slaif_owner` | One-shot bootstrap only | Own `control`, `content`, `audit`, their objects, and the `agentcow` deployment; run migrations and hardening. |
| `slaif_control` | Control API and human-session principal | `USAGE` on `control` plus execute on owner-defined readiness, setup, opaque-session, and local-credential lookup/compare-and-set functions; direct relation access, content DML, and reviewer/setup-owner authority remain denied. |
| `slaif_editor_runtime` | Future Editor API principal | COW-view `SELECT`, `INSERT`, `UPDATE`, and `DELETE` after a table is enabled/hardened; no base/change, reviewer, or setup authority. |
| `slaif_agent_runtime` | Agent API principal | COW-session semantic create wrappers for five bounded content routes, two narrow durable idempotency/audit functions, and no base/change, direct control-table, reviewer, or setup authority. |
| `slaif_public_reader` | Canonical Render principal | Exact execute on the two active site resolver functions, plus `SELECT` on present COW views after product grant reconciliation; no site relations, management functions, or DML. |
| `slaif_preview_reader` | Future preview render principal | Read-only view access; a future trusted session wrapper must establish preview context. |
| `slaif_reviewer` | Future review-worker principal | Read-only COW views and only the foundation-controlled reviewer function surface; no runtime DML or setup. |
| `slaif_scheduler` | Future scheduler principal | No object grant yet; content and reviewer authority remain denied. |
| `slaif_media` | Future media-service principal | No object grant yet; content and reviewer authority remain denied. |
| `slaif_gc` | Future media-GC principal | No object grant yet; content and reviewer authority remain denied. |

MCP adapter, Web, and browser worker have no database privilege role. Render
uses the canonical public-reader credential; future preview access remains a
separate credential rather than a combined writer. No generic all-authority
role exists.

The clean revision has no `content` object. In `EMPTY_SAFE`, every non-owner
role also lacks content schema `USAGE`/`CREATE`, and Reviewer has no foundation
schema/function surface. Grants are applied only after real objects exist and
the state reaches `HARDENED`.

Revision `010_001` adds the non-COW `control.user_session` relation. Control
receives only the five owner-created lifecycle functions for create, locked
inspection, safe finalization, state-changing finalization/CSRF validation,
and idempotent CSRF-bound revoke. Session and CSRF digests
are exactly 32 bytes; plaintext credentials never reach the database. Every
runtime, reviewer, reader, scheduler, media, and GC role has no relation or
function authority for these objects.

Revision `011_001` adds only `slaif_control` execution on local-login lookup
and password-hash compare-and-set functions. No role receives direct
`user_account` relation access; plaintext passwords never reach PostgreSQL.

Revision `013_001` adds the non-COW `control.site`, `control.site_domain`, and
installation-bound `control.site_policy` relations. Only `slaif_owner` owns or accesses the
relations directly. `slaif_control` receives execution on the exact bounded
site CRUD, active-context, domain-mapping/listing, archive, resolution, and
active Platform Administrator authorization functions; it receives no
table, sequence, or column grant. `slaif_public_reader` receives only
`slaif_site_resolve(text,text)` and `slaif_site_resolve_local(text)`; every
other runtime, reader, reviewer, scheduler, media, and GC role is denied site
relation and function authority. Site and
operation identifiers are generated or selected inside trusted server/database
code, and archive is the only exposed removal lifecycle.
Authorization joins the active user and current assignment inside one fixed-
search-path owner function; callers cannot infer authority from username,
setup history, cookies, Host, or client claims.

Revision `014_001` adds `control.permission`, `control.human_role`,
`control.human_role_permission`, `control.site_membership`, and
`control.site_membership_permission_override`. All are owner-controlled.
`slaif_control` receives only named catalog/context/authorize/membership
functions and no direct relation access. Every other runtime role has both
relation and RBAC-function authority revoked. The membership mutation function
locks the active site, actor/target users in UUID order, their administrator
assignments, memberships, and overrides before authority evaluation. Its
active and inactive trusted results compute Platform Administrator status from
the target. The authenticated Control HTTP layer calls only this named surface;
no HTTP handler receives a native connection or relation grant.

Revision `025_001` adds the control-plane `agent_idempotency` record and
append-only `audit.agent_mutation` evidence. The Agent role can invoke only
the begin/complete owner functions, which validate the capability/workspace
binding and write the result transactionally; it cannot insert, update, or
select either relation. The same revision adds five owner-defined
`content.slaif_agent_*` wrappers. Each requires the foundation COW session and
operation settings and validates site/resource/parent relationships before
performing one bounded semantic create.

Revision `026_001` places a guarded owner-defined layer over those wrappers;
revision `027_001` qualifies the page/composition function columns so runtime
output-variable names cannot make the human Editor API fail closed.
Revision `028_001` adds the narrow HUMAN Editor workspace assertion and
Editor-owned idempotency/audit functions; Editor still has no direct Control or
Audit table DML. Resolution serializes the site-and-human lookup so concurrent
requests reuse one active HUMAN workspace. Every Editor mutation transaction
passes its required permission key into the database boundary. The assertion
validates only immutable COW context before taking the shared workspace
advisory transaction lock; it then re-reads active membership, site, session,
workspace, permission, and operation state under that lock before mutation and
again before audit/idempotency completion. It resolves the active workspace
from `app.session_id`, requires a valid operation UUID and active non-expired
workspace, and rejects any supplied site UUID that differs from the workspace
site before delegation.

## Login-principal design

Privilege roles never contain passwords. The local deployment provisions this
fixed login-to-role manifest from generated file-backed passwords:

| Local login | Sole privilege membership |
| --- | --- |
| `slaif_bootstrap_login` | `slaif_owner` |
| `slaif_control_login` | `slaif_control` |
| `slaif_editor_login` | `slaif_editor_runtime` |
| `slaif_agent_login` | `slaif_agent_runtime` |
| `slaif_public_login` | `slaif_public_reader` |
| `slaif_preview_login` | `slaif_preview_reader` |
| `slaif_reviewer_login` | `slaif_reviewer` |
| `slaif_scheduler_login` | `slaif_scheduler` |
| `slaif_media_login` | `slaif_media` |
| `slaif_gc_login` | `slaif_gc` |

Every login is `LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT
NOREPLICATION NOBYPASSRLS`. Names and memberships are immutable code, not
caller input. PostgreSQL quotes password values from a bound parameter before
the trusted fixed-identifier statement is executed.

Render has two principals because canonical and preview access differ. The
setup-owner login is one-shot and is never mounted into an online process.

The default local login contract additionally fixes every principal at ten
connections, password validity `infinity`, and no per-role PostgreSQL settings.
Provisioning resets configuration drift rather than permitting a login to
inject `search_path` or another GUC. It removes direct database, product or
foundation schema, relation, relation-column, sequence, routine, and applicable
default ACLs; all access must be inherited through the sole non-admin
membership. A login that owns the product database or an object in `control`,
`content`, `audit`, or `agentcow` makes provisioning fail closed because
ownership is not silently reassigned.

The disposable integration suite creates fake login principals with exactly
one membership each. Product privilege roles may not be members of any other
role; the verifier rejects direct or transitive authority paths. External
login principals being members of one product role are expected. Future
service DSNs are generated but deliberately not distributed. Control's one
fixed DSN is the sole exception: the initializer copies it into a separate
Control-only volume for the implemented online pool.

## Operator and owner separation

Role creation is a cluster-level operation. The explicit `provision` command
requires a principal with `CREATEROLE` or superuser authority, validates the
target database, creates/reconciles the password-free roles, and removes any
role inherited by a product privilege role. It revokes database authority from
`PUBLIC`, grants `CONNECT` to the ten exact privilege roles, grants `CREATE`
only to `slaif_owner`, and grants `TEMPORARY` to none. When and only when the
local secret directory is configured, it also creates/reconciles the fixed
login manifest, rotates those local passwords to mounted values, removes other
memberships and direct ACLs, and grants each exact sole role. Institutional
provisioning may omit this local extension.

An institution may perform equivalent provisioning itself, then omit the
provisioner locator. Migration and COW operations use a separate connection
that must be or must be able to `SET ROLE slaif_owner`. No long-running process
loads either stronger locator; Control loads only its own fixed login locator.

## Effective privilege verification

The product and local-login verifiers read PostgreSQL's effective truth through
`pg_catalog`, raw ACL grantees, and `has_*_privilege` functions. They check:

- role flags and membership edges;
- schema and relation ownership;
- `PUBLIC` and non-owner schema creation;
- effective relation DML, including inherited grants;
- effective function execution and locked-down reviewer functions;
- exact empty-schema inventory and generic content/foundation object
  fingerprints;
- state-specific schema usage and Reviewer foundation authority;
- exact database ACLs, login ownership, defaults, settings, validity, and
  connection limits;
- effective database/schema/table/view/column/sequence/routine privilege
  equality between every fixed login and its sole privilege role.

Diagnostics identify a role, object, and privilege category, but never include
a password, locator, unrelated database metadata, or query result. Foundation
validation remains a separate required check in `HARDENED`; it is explicitly
not applicable and not claimed in `EMPTY_SAFE`. The product verifier never
reinterprets private foundation objects.
