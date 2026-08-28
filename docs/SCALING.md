# Scaling boundaries

The reference deployment intentionally runs one browser-worker process with one
active Chromium context and zero queued attempts. This is a conservative
qualification boundary, not a throughput or availability claim. Public Agent
runs are not dispatched in this round, so increasing worker replicas cannot
increase public-run progress.

The default `browser-artifacts` volume is local to the Compose deployment and
mounted only by the worker. Immutable files survive worker restart, but a second
worker without the same private store cannot retrieve them. Do not add a shared
object store, public bucket, network filesystem, or artifact proxy implicitly.
A future scaling order must select an architecture-approved shared self-hosted
`MediaStore`-style backend, preserve exclusive no-replace writes and exact
digest/binding verification, and define orphan cleanup before replicas are
enabled.

Horizontal worker scaling also requires the deferred Agent-owned durable claim,
lease renewal/release, attempt completion, and artifact registration flow.
Database leases—not an in-memory worker queue—must allocate attempts. Each
retry still requires a new browser/context/page and an exact short-lived preview
credential. Replica count must never widen origin, egress, service-secret,
database, publication, or artifact visibility authority.

Until those pieces are ordered and proven, supported operation is one worker,
one active attempt, no queue, one fixed Web origin, three Chromium target
descriptors, private local artifacts, and no public dispatch or retrieval.
