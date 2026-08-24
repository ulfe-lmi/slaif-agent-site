# Alembic source location

The executable Alembic environment is packaged at
`services/backend/src/slaif_agent_site/db/alembic` so clean wheel installs retain
the migration graph. The root `alembic.ini` points to that canonical tree.

The graph currently contains the PostgreSQL role/schema/bootstrap baseline at
`006_001` and the Control-only, read-only database readiness function at
`007_001`, followed by the owner-only singleton installation state at
`008_001`, then constrained local/OIDC identity persistence and two narrow
atomic setup functions at `009_001`, followed by the non-COW opaque human
session relation and Control-only lifecycle functions at `010_001`, followed
by Control-only local credential lookup and password-hash compare-and-set
functions at `011_001`.
Revision `012_001` connects those authentication primitives to the bounded
Control HTTP surface without adding database objects. Revision `013_001` adds
the non-COW Control-owned site/domain foundation, the installation site quota,
and exact Control-only semantic functions for site lifecycle and trusted
resolution. It does not create content/workspace objects or public site HTTP
routes.
Revision `014_001` adds owner-controlled human permission/role catalogs,
site membership and overrides, and fixed Control authorization/mutation
functions. These objects are non-COW and grant runtime roles no direct relation
access. Membership mutation locks the active site, ordered actor/target user
and membership identities, administrator assignments, and overrides before
evaluating authority; inactive trusted results report the target's global
administrator fact.
Application services never invoke
Alembic; only the one-shot
bootstrap authority supplies the owner connection used by migration commands
and setup-token lifecycle operations.

The current single head is `035_001`. Revisions `015_001` through `034_001`
extend the same linear graph with current-human reads, COW content models and
semantic functions, workspace/capability state, Agent/Editor/Media boundaries,
and Render preview authorization. Revision `035_001` adds non-COW browser
limits, run/idempotency/lease/private-artifact metadata, append-only audit, and
nine exact Agent functions. It adds no HTTP route, worker database role,
artifact bytes, or browser execution.
