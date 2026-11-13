# Cluster provisioning boundary

The executable password-free role manifest and reconciliation code live in
`services/backend/src/slaif_agent_site/db/roles.py`. No SQL file here contains
a password, default credential, or environment-specific database name.

See `docs/DATABASE_ROLES.md` and `docs/DATABASE_BOOTSTRAP.md` for the operator
contract and commands.

Revision `078_001` (increment 083-11-a) is the ordered head carrying the
durable trusted mutation completion journal. While that journal exists,
the operator downgrade (the disposable verification operation documented
in `docs/DATABASE_BOOTSTRAP.md`) refuses before the readiness PENDING
marker, before the content COW disable, and before any migration step, for
any head retaining the 078 provenance (current or later, journal empty or
not); the 078_001 Alembic downgrade body is the unconditional refusal for
direct migration invocations, and the 077_001 media-isolation downgrade
guard remains. The operator upgrade keeps its existing no-pending COW
precondition. No new operator command or target argument is introduced,
and downgrade never deletes durable completion, audit, or idempotency
history.
