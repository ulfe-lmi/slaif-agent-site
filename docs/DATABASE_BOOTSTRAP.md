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
readiness marker stores versions and booleans, never a locator or credential.

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
head. `bootstrap` repeats `upgrade`, deploys/reconciles COW, applies product
grants, runs both validators, and publishes the safe marker last. `current` is
read-only. `validate` fails if database truth and the marker disagree.

Downgrade and rebuild are disposable verification operations, not a production
rollback promise:

```bash
python -m slaif_agent_site.bootstrap downgrade --confirm-disposable
python -m slaif_agent_site.bootstrap rebuild --confirm-disposable
```

They are tested before foundation/content objects are added. Production uses
forward maintenance migrations and restores from a validated backup when the
release plan requires recovery.

## Reconciliation and marker semantics

The ordered path is:

1. provision or independently validate the role boundary;
2. upgrade Alembic as `slaif_owner`;
3. call public `deploy_cow_functions(...)` in a transaction;
4. call public `enable_cow_schema(...)` for `content` with deferred FKs enabled
   and unsafe canonical writes disabled;
5. call public `harden_cow_schema(...)` with only Editor/Agent runtime and
   Reviewer roles in an explicit transaction;
6. apply grants only to current product objects;
7. call public `validate_cow_schema_privileges(...)` and the independent
   product verifier;
8. update `control.bootstrap_readiness.safe` as the last transaction action.

Before every attempt, the marker is made unsafe. Deployment may remain
idempotently installed after a later step fails. Enablement, hardening, product
grants, validation, and final marker publication share a transaction, so an
injected failure rolls them back. A repeat repairs safely and a successful
repeat does not add objects or change migration head.

The marker records revision `006_001`, distribution
`agent-cow-postgresql`, version `0.2.0`, deployment/hardening/validation flags,
and update time. Its constraint forbids `safe=true` unless every state flag is
true. The owner alone can read or update it in this baseline; it is not yet an
online readiness probe.

## Empty-content limitation

The qualified foundation `harden_cow_schema(...)` rejects a schema with zero
COW-enabled tables. This revision is also prohibited from adding a production
`content` table. Consequently, `upgrade` succeeds on the clean baseline, but
the current clean `bootstrap` command deliberately stops after safe foundation
deployment with `cow_deployed=true`, all later flags false, and `safe=false`.
It emits the constant failure and never fabricates hardening evidence.

The integration gate proves the complete sequence using a disposable
qualification-only table, then removes the database. That table is absent from
the migration and distributions. Resolving clean-baseline safe readiness needs
a strategic choice: add the first authorized content migration, qualify a
foundation API that supports empty-schema hardening, or explicitly redefine
empty hardening as not applicable. This PR does none of those silently.

## Future migration rule

A future physical `content` migration must run in maintenance mode, create only
trusted platform tables, call public enablement with deferred FKs and unsafe
canonical writes disabled, rerun hardening and both validators, and grant each
new view/function explicitly. It must not rely on broad default privileges or
accept DDL from a human/agent/site request. Configurable content types and
fields remain data, not migrations.
