# OAP Work Order — 082-a (inert until activated)

## Contract and objective

Implement real freeze and immutable review state after the complete editable
surface exists. Links: §§10 I-9, 16.6, 17.4–17.6, 28.2–28.3, 52.6. Requires
081; one new objective PR when activated.

## Production requirements

- Add durable transactional review jobs and a non-listening review worker with
  its own narrow credentials/claims. Human Control freeze requires authenticated
  site membership, `workspace:freeze`, CSRF and exact site/workspace binding.
- In one Control transaction, revoke all capabilities, mark `FREEZING`, and
  enqueue the unique freeze job. The worker then acquires the product exclusive
  workspace lock after shared mutations drain and rechecks state.
- Retrofit every Agent, Editor/Puck, Media and any batch/import editorial
  mutation transaction to acquire the same
  product shared workspace advisory lock before its in-transaction ACTIVE
  state recheck; current Agent idempotency begin does not do this, so status
  checks alone are not freeze-drain evidence. Preserve one lock order.
- Materialize a new immutable `review_snapshot` row containing exact canonical
  revision, operation/dependency closure and watermark, all normalized editable
  site state, validation report, catalog/renderer/composition/Puck/content-model
  versions, media references, selected completed browser evidence and digest.
  Define one canonical serialization and independently recomputable digest;
  cross-check foundation operations/dependencies/watermark exactly against
  semantic audit. No long-lived Control/runtime/reviewer role has snapshot
  UPDATE/DELETE authority; PostgreSQL owner compromise remains out of scope.
- Define freeze policy for outstanding browser/source runs: bounded wait or
  cancel, and attach only server-selected completed evidence. Never snapshot a
  mutable/pending artifact claim.
- Transition to `REVIEW` only after successful complete snapshot. Freeze retry
  is idempotent; crash/validation failure cannot create a falsely reviewable
  partial object.
- Render/Web review mode reads only the snapshot, never the live COW overlay or
  later canonical state. Add semantic diff/review summary and responsive human
  review UI; no accept/discard behavior yet.

## Acceptance and anti-bypass

Real public lifecycle proof races an in-flight Agent mutation against freeze:
the mutation either commits before the snapshot or is denied. New requests with
the revoked capability return 401; an already-authenticated race losing the
in-transaction ACTIVE recheck returns 409. The final snapshot digest/projection
is exact and stable across canonical changes/restarts, and product DB roles
cannot mutate it. Cross-site,
nonmember, wrong permission, CSRF, foreign snapshot/workspace, duplicate job,
failed validation and worker crash are fail-closed. Browser/media references
remain private and exact.

The test must fail if snapshot insertion or snapshot rendering is removed; a
status flag or copied test fixture is not acceptance. Run real PostgreSQL,
worker credentials/Compose wiring, concurrency/restart, public NGINX
desktop+phone review, Render and full relevant Compose/CI. No promotion/
discard/selective accept. Report
`082-a-immutable-freeze-review-snapshot.md` with SELF; no merge/extra PR.
