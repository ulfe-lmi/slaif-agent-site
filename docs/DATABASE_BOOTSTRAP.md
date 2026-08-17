# Database bootstrap and migration baseline

The implemented database path is an explicit one-shot maintenance boundary. It
does not add an online pool, product route, authentication, product-domain
table, deployment stack, or runnable site.

## Dependencies and migration graph

Migration execution uses exact `alembic==1.19.1` and
`sqlalchemy==2.0.52`. SQLAlchemy is confined to Alembic with an asyncpg dialect
and `NullPool`; application and foundation operations continue to use asyncpg.
The migration source is packaged under
`slaif_agent_site/db/alembic`, and root `alembic.ini` contains no URL or
credential.

There is one head:

```text
006_001 (head)
```

It creates `control`, `content`, and `audit`, owned by `slaif_owner`.
Alembic state is `control.alembic_version`. The only product table is
`control.bootstrap_readiness`; `content` and `audit` are empty. Unsafe default
schema, table, sequence, and function privileges are revoked. The foundation
creates its public `agentcow` objects only when reconciliation is explicitly
requested.

## Configuration

Bootstrap configuration is separate from `ServiceSettings` and uses only the
`SLAIF_BOOTSTRAP_` prefix.

| Variable | Required for | Contract |
| --- | --- | --- |
| `SLAIF_BOOTSTRAP_MODE` | Every database command | `test` or `production`; no default. |
| `SLAIF_BOOTSTRAP_EXPECTED_DATABASE` | Every database command | Exact validated database name checked after connection. |
| `SLAIF_BOOTSTRAP_PROVISIONER_DSN_FILE` | `provision` | Absolute mounted secret file for cluster-provisioner access. |
| `SLAIF_BOOTSTRAP_OWNER_DSN_FILE` | Owner commands | Absolute mounted secret file for the one-shot owner principal. |

Direct `SLAIF_BOOTSTRAP_PROVISIONER_DSN` and
`SLAIF_BOOTSTRAP_OWNER_DSN` inputs exist only for generated disposable tests;
production rejects them. A locator file contains one PostgreSQL DSN and a
trailing newline is ignored. No default DSN, user, database, or password is
provided.

Pydantic secret values are masked. Configuration/connection/action failures
from the CLI print only `Database bootstrap failed.` and exit nonzero. The
readiness marker stores versions, a constrained state, evidence flags, and
generic object fingerprints, never a locator or credential.

## Commands

The no-op smoke remains database-free:

```bash
python -m slaif_agent_site.bootstrap --check
```

With the variables above supplied by the operator environment:

```bash
python -m slaif_agent_site.bootstrap provision
python -m slaif_agent_site.bootstrap upgrade
python -m slaif_agent_site.bootstrap current
python -m slaif_agent_site.bootstrap bootstrap
python -m slaif_agent_site.bootstrap validate
```

Running the module without a command prints usage and performs no mutation.
`provision` is the only cluster-role command. `upgrade` reaches the one Alembic
head. `bootstrap` repeats `upgrade`, deploys/reconciles COW, applies the
state-specific grants and validation, and publishes the safe marker last.
`current` is read-only and includes `state=PENDING`, `state=EMPTY_SAFE`, or
`state=HARDENED`. `validate` independently reproduces the applicable proof and
fails if database truth, object fingerprints, and the marker disagree.

Downgrade and rebuild are disposable verification operations, not a production
rollback promise:

```bash
python -m slaif_agent_site.bootstrap downgrade --confirm-disposable
python -m slaif_agent_site.bootstrap rebuild --confirm-disposable
```

They are tested on disposable empty databases, including an idempotently
deployed foundation schema. Production uses forward maintenance migrations and
restores from a validated backup when the release plan requires recovery.

## Reconciliation and marker semantics

The ordered path is:

1. provision or independently validate the role boundary;
2. upgrade Alembic as `slaif_owner`;
3. call public `deploy_cow_functions(...)` in a transaction;
4. call public `enable_cow_schema(...)` for `content` with deferred FKs enabled
   and unsafe canonical writes disabled;
5. inventory `content` through generic PostgreSQL catalogs;
6. when the inventory is empty, revoke all non-owner content and foundation
   service authority and run only the independent safe-empty verifier;
7. otherwise call public `harden_cow_schema(...)`, apply grants, and run public
   `validate_cow_schema_privileges(...)` plus the independent verifier;
8. fingerprint the generic content and foundation object inventories and
   update `control.bootstrap_readiness` as the last transaction action.

Before every attempt, the marker is made unsafe. Deployment may remain
idempotently installed after a later step fails. Enablement, hardening, product
grants, validation, and final marker publication share a transaction, so an
injected failure rolls them back. A repeat repairs safely and a successful
repeat does not add objects or change migration head.

The marker records revision `006_001`, distribution
`agent-cow-postgresql`, version `0.2.0`, state-specific evidence flags, generic
content/foundation object counts and SHA-256 fingerprints, overall safety, and
update time. Database constraints admit exactly these combinations:

| State | Content evidence | Foundation table evidence | Product evidence | Safe |
| --- | --- | --- | --- | --- |
| `PENDING` | No published inventory | Hardening and foundation validation false | Validation false | false |
| `EMPTY_SAFE` | Exactly zero schema-scoped objects | Hardening and foundation table validation false/not applicable | Safe-empty privileges validated | true |
| `HARDENED` | Nonzero fingerprinted inventory | Hardening and foundation validation true | Product privileges validated | true |

`PENDING` permits only the foundation-deployed flag to reflect an idempotent
partial step. It can never be safe. `EMPTY_SAFE` is not a waiver and does not
claim that foundation table privileges were validated: there is no content
table, view, sequence, routine, type, operator, collation, statistics object,
or text-search object to harden. All non-owner roles lack content schema usage
and creation, and Reviewer has no foundation function surface. The deployed
foundation inventory is fingerprinted and protected from `PUBLIC` and service
roles.

The qualified foundation still rejects direct hardening of zero COW tables,
so the empty branch deliberately does not call hardening or foundation table
validation. Any content object makes that branch inapplicable and forces the
public hardening path. Adding, removing, or renaming an object after reconcile
changes the stored generic fingerprint and makes `validate` fail closed. An
explicit repeat reconcile may advance only `updated_at`; the migration head,
object inventory, grants, and state do not drift.

The owner alone can read or update the marker in this baseline; it is not yet
an online readiness probe.

## Future migration rule

A future physical `content` migration must first make readiness `PENDING`, run
in maintenance mode, create only trusted platform tables, call public
enablement with deferred FKs and unsafe canonical writes disabled, rerun
hardening and both validators, and publish `HARDENED` with new fingerprints.
The database must not remain or return `EMPTY_SAFE` while any object exists. A
migration must not rely on broad default privileges or accept DDL from a
human/agent/site request. Configurable content types and fields remain data,
not migrations.
