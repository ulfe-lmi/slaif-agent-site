# Cluster provisioning boundary

The executable password-free role manifest and reconciliation code live in
`services/backend/src/slaif_agent_site/db/roles.py`. No SQL file here contains
a password, default credential, or environment-specific database name.

See `docs/DATABASE_ROLES.md` and `docs/DATABASE_BOOTSTRAP.md` for the operator
contract and commands.
