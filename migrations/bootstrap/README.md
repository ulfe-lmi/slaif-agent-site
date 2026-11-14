# Cluster provisioning boundary

The executable password-free role manifest and reconciliation code live in
`services/backend/src/slaif_agent_site/db/roles.py`. No SQL file here contains
a password, default credential, or environment-specific database name.

See `docs/DATABASE_ROLES.md` and `docs/DATABASE_BOOTSTRAP.md` for the operator
contract and commands.

Revision `079_001` (increment 083/12) is the ordered head. It carries the
078 durable trusted mutation completion journal plus the reviewed-operation
binding: each new review snapshot atomically stores an immutable
reviewed-operations/v1 companion manifest, and the human accept entry point
binds the approval to the exact snapshot and its manifest (dual digest).
While that binding exists, the operator downgrade (the disposable
verification operation documented in `docs/DATABASE_BOOTSTRAP.md`) refuses
before the readiness PENDING marker, before the content COW disable, and
before any migration step, for any head retaining the 079 binding (current
or later); the 079_001 Alembic downgrade body is the unconditional refusal
for direct migration invocations. The 078 completion-provenance refusal and
the 077_001 media-isolation downgrade guard remain as earlier lines of
defense for direct migration invocations at their released heads. The
operator upgrade keeps its existing no-pending COW precondition. No new
operator command or target argument is introduced, and downgrade never
deletes durable completion, manifest, audit, or idempotency history.
