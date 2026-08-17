# Alembic source location

The executable Alembic environment is packaged at
`services/backend/src/slaif_agent_site/db/alembic` so clean wheel installs retain
the migration graph. The root `alembic.ini` points to that canonical tree.
