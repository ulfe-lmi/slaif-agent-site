# OAP Work Order — 084-a (inert until activated)

## Contract and objective

Prove conflict safety through the real immutable-review and accept lifecycle,
not only foundation helpers. Links: §§17.4, 29.4–29.5, 42.3, 53.5. Requires
083 and real Agent update semantics.

## Required scenario

1. Canonical row/site revision A exists.
2. Human creates workspaces W and X from A; real Agent capabilities change the
   same row differently through public PATCH.
3. Freeze both and record immutable snapshots based on A.
4. Accept X through public human Control/review worker; canonical becomes B.
5. Attempt to accept W. It must reject before mutation with the architecture-
   defined `SITE_REVISION_CHANGED` or structured conflict state, retain W's
   snapshot/pending work, and leave canonical exactly B.
6. Generate a new immutable W snapshot against revision B while retaining its
   old first-touch row baseline; acceptance must reach the foundation and fail
   with structured `BASE_ROW_CHANGED`, still without changing B.
7. Prove a non-overlapping active workspace can be regenerated/refrozen against
   B and accepted without erasing X, consistent with conservative MVP review.

## Anti-bypass and negatives

No direct reviewer helper/CAS/unit-only substitute; actor mutations, freeze and
accept use public product surfaces and real worker. Assert public HTML,
canonical DB, snapshot revisions/digests, job/workspace states and audit.
Exercise simultaneous worker claims, duplicate accept, worker crash/cancel,
pending-state retention, absence of success audit/outbox, foreign snapshot/
site, nonpublisher and forbidden overwrite policy. Inspect grants/config/source
to prove no public overwrite path.

Run real PostgreSQL concurrency, NGINX, Render, review worker and full relevant
Compose/CI. No automatic rebase/field merge/conflict-resolution UI. Binary done
means silent last-writer-wins is impossible on the actual accept path. Report
`084-a-conflict-safe-review-lifecycle.md` with SELF; no merge/extra PR.
