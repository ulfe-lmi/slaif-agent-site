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
| `slaif_control` | Future Control API principal | No object grant yet; content DML and setup remain denied. |
| `slaif_editor_runtime` | Future Editor API principal | COW-view `SELECT`, `INSERT`, `UPDATE`, and `DELETE` after a table is enabled/hardened; no base/change, reviewer, or setup authority. |
| `slaif_agent_runtime` | Future Agent API principal | Same COW-view DML boundary as Editor under a distinct role; no base/change, reviewer, or setup authority. |
| `slaif_public_reader` | Future canonical render principal | `SELECT` on present COW views after product grant reconciliation; no DML or internal tables. |
| `slaif_preview_reader` | Future preview render principal | Read-only view access; a future trusted session wrapper must establish preview context. |
| `slaif_reviewer` | Future review-worker principal | Read-only COW views and only the foundation-controlled reviewer function surface; no runtime DML or setup. |
| `slaif_scheduler` | Future scheduler principal | No object grant yet; content and reviewer authority remain denied. |
| `slaif_media` | Future media-service principal | No object grant yet; content and reviewer authority remain denied. |
| `slaif_gc` | Future media-GC principal | No object grant yet; content and reviewer authority remain denied. |

MCP adapter, Web, and browser worker have no database privilege role. Render
will eventually use separate canonical and preview credentials rather than a
combined writer. No generic all-authority role exists.

The clean revision has no `content` object. In `EMPTY_SAFE`, every non-owner
role also lacks content schema `USAGE`/`CREATE`, and Reviewer has no foundation
schema/function surface. Grants are applied only after real objects exist and
the state reaches `HARDENED`.

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

The disposable integration suite creates fake login principals with exactly
one membership each. Product privilege roles may not be members of any other
role; the verifier rejects direct or transitive authority paths. External
login principals being members of one product role are expected. Future
service DSNs are generated but deliberately not distributed until online pools
exist.

## Operator and owner separation

Role creation is a cluster-level operation. The explicit `provision` command
requires a principal with `CREATEROLE` or superuser authority, validates the
target database, creates/reconciles the password-free roles, removes any role
inherited by a product privilege role, grants database `CONNECT`/`CREATE` only
to `slaif_owner`, and revokes default `PUBLIC` schema access. When and only when
the local secret directory is configured, it also creates/reconciles the fixed
login manifest, rotates those local passwords to mounted values, removes other
memberships, and grants each exact sole role. Institutional provisioning may
omit this local extension.

An institution may perform equivalent provisioning itself, then omit the
provisioner locator. Migration and COW operations use a separate connection
that must be or must be able to `SET ROLE slaif_owner`. No long-running process
loads either locator.

## Effective privilege verification

The product verifier reads PostgreSQL's effective truth through `pg_catalog`
and `has_*_privilege` functions. It checks:

- role flags and membership edges;
- schema and relation ownership;
- `PUBLIC` and non-owner schema creation;
- effective relation DML, including inherited grants;
- effective function execution and locked-down reviewer functions;
- exact empty-schema inventory and generic content/foundation object
  fingerprints;
- state-specific schema usage and Reviewer foundation authority.

Diagnostics identify a role, object, and privilege category, but never include
a password, locator, unrelated database metadata, or query result. Foundation
validation remains a separate required check in `HARDENED`; it is explicitly
not applicable and not claimed in `EMPTY_SAFE`. The product verifier never
reinterprets private foundation objects.
