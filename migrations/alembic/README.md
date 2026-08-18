# Alembic source location

The executable Alembic environment is packaged at
`services/backend/src/slaif_agent_site/db/alembic` so clean wheel installs retain
the migration graph. The root `alembic.ini` points to that canonical tree.

The graph currently contains the PostgreSQL role/schema/bootstrap baseline at
`006_001` and the Control-only, read-only database readiness function at
`007_001`. Application services never invoke Alembic; only the one-shot
bootstrap authority supplies the owner connection used by migration commands.
