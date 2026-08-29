# OAP Work Order — 089-a (inert until activated)

## Contract and objective

Close contractual durable lifecycle operations: expiry, cleanup, review/media/
artifact GC and safe multi-worker claims. Links: §§15.10–15.11, 17.3, 30.8,
38, 41, 52.8. Requires 083 and 087.

## Production requirements and proof

Replace idle scheduler/media-GC placeholders with narrow-credential durable
workers. Request-time expiry remains fail-closed; scheduler idempotently marks/
queues expired workspace retention/discard policy without reviewer authority.
Use transactional `SKIP LOCKED` claims, leases, retries, cancellation and
restart recovery. GC deletes only abandoned staging/private artifacts after
retention and never canonical/referenced/snapshot-retained bytes or audit.
Multiple scheduler/review/browser/GC workers must not double-apply terminal
actions or widen authority.

Real-clock/controlled-time and PostgreSQL tests cover active→expired→retained→
discard/cleanup, revoked/frozen/accepted states, stuck leases, concurrent claims,
worker crash, replay, partial file failure and safe retry. Media/artifact
reference races and cross-site retention are negative-tested; canonical/public
state remains correct. Compose restart exposes truthful readiness and no host
port. No production credentials, premature deletion or publication.

Binary done requires live non-listening workers and idempotent end-to-end
cleanup, not state enums or mocked queues. Run full relevant DB/media/browser/
Compose/CI. No backup/restore or new product semantics. Report
`089-a-lifecycle-expiry-cleanup-workers.md` with SELF; no merge/extra PR.
