# OAP Work Order — 083-a (inert until activated)

## Contract and objective

Implement human-only full accept and discard through the real reviewer COW
transaction, binding the exact 082 snapshot to canonical publication. Links:
§§10 I-6/I-7, 15.9, 16.8/16.12, 29, 30.5, 52.3. Requires 082.

## Production requirements

- Add Control accept/discard routes and responsive UI with human session, CSRF,
  exact site/workspace/snapshot ID+digest and recent-auth. Accept requires both
  `workspace:accept` and `site:publish`; discard requires `workspace:discard`.
  Agent capability is never accepted.
- Enqueue idempotent durable jobs. Review worker alone enters the reviewer
  transaction, locks workspace/site revision, verifies state, immutable
  snapshot digest/base revision/versions/operation closure/audit/validation.
  One `asyncpg_cow_reviewer` transaction explicitly calls
  `commit_session(..., defer_fk_constraints=True, conflict_policy="error")`
  and contains COW commit, revision, promotion audit, workspace/job state and
  outbox; the current detached `promotion.py` wrapper is insufficient.
- Accept atomically promotes exactly reviewed COW state, increments canonical
  revision, writes durable promotion audit/terminal job/workspace state and
  outbox. Finalize required media bytes idempotently before commit; failure may
  leave only harmless GC-able digest objects, never partial canonical state.
- Add canonical-reference-gated anonymous public media reads and real renderer
  image URLs/`img` output only after acceptance, with immutable headers and
  inaccessible orphan bytes. Mount only the required media authority in the
  review worker.
- Current public rendering is intentionally `force-dynamic`/`no-store`; either
  preserve and prove that honest no-cache behavior or implement a retrying
  invalidation consumer. An unconsumed outbox row is not cache invalidation.
- Discard invokes real foundation discard, preserves canonical, marks terminal
  state/audit and schedules staging/private retention cleanup.
- Crash/retry, cancellation and duplicate requests are idempotent; structured
  revision/conflict/validation failures preserve snapshot and pending work.

## Acceptance and anti-bypass

Through public human routes, accept a real Agent+Puck workspace and verify both
canonical DB projection and public HTML changed to the reviewed state, media
bytes became public, audit/revision/state are exact and Agent remains revoked.
Discard a separate real workspace and prove canonical/public/media unchanged
and overlay discarded. Inject failures before/after media copy, during reviewer
transaction, audit/site revision/terminal update, worker death and simultaneous
duplicate claims; no double revision/audit/outbox or partial publication. Deny
agent token, nonpublisher, wrong site/
snapshot, stale revision, CSRF and replay mismatch.

Tests must fail if reviewer commit/discard, public rendering or media
finalization is replaced by status success. No direct SQL/helper may perform
the claimed lifecycle; owner SQL is assertion/fault injection only. Run real
PostgreSQL, public NGINX desktop+phone, worker concurrency/restart, Media,
Render, full Compose/CI. No selective acceptance/rebase. Report
`083-a-real-accept-discard-promotion.md` with SELF; no merge/extra PR.
