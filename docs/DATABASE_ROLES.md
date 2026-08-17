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

The clean revision has no `content` view, so it grants no runtime or reader
relation access. Grants are applied only to objects that actually exist.

## Login-principal design

Privilege roles never contain passwords. An institution creates one distinct
login principal per service credential, grants that principal exactly one
privilege role, and configures the future pool to activate only that role.
Render uses two principals because canonical and preview access differ. A
setup-owner login is one-shot and is never mounted into an online process.

The disposable integration suite creates fake login principals with exactly
one membership each. Product privilege roles may not be members of any other
role; the verifier rejects direct or transitive authority paths. External
login principals being members of one product role are expected. Credential
creation and distribution for the default stack are deferred.

## Operator and owner separation

Role creation is a cluster-level operation. The explicit `provision` command
requires a principal with `CREATEROLE` or superuser authority, validates the
target database, creates/reconciles the password-free roles, removes any role
inherited by a product privilege role, grants database `CONNECT`/`CREATE` only
to `slaif_owner`, and revokes default `PUBLIC` schema access. It never creates a
login, password, or default credential.

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
- clean-baseline object inventory.

Diagnostics identify a role, object, and privilege category, but never include
a password, locator, unrelated database metadata, or query result. Foundation
validation remains a separate required check; the product verifier supplements
it and does not reinterpret private foundation objects.
