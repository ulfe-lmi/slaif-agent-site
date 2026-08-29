# OAP Work Order — 085-a (inert until activated)

## Contract and objective

Prove the defining dynamic News vertical through intended product interfaces.
Links: §§9.3, 21.6, 42.4, 52.5, 53.2. Requires 074–084 all merged.

## Required product proof

In a clean Compose environment, a human uses Control/Web to create a bounded
Level-4 workspace/capability. An external client uses public Agent REST with
idempotency to create News type and title/body/published-at fields, a bounded
collection view, at least two items, listing page/component, dynamic detail
experience, navigation item and any needed media/design binding. It requests a
real Objective-072 preview artifact. The human opens the same normalized
composition in Puck, makes one visible edit, freezes the immutable snapshot,
reviews it, accepts it, and public `/news` plus `/news/{slug}` render the exact
reviewed content. Physical Alembic/schema revision is unchanged by the task.

## Anti-bypass and negatives

No ORM, SQL, repository/service call, privileged human mutation API, internal
endpoint, filesystem edit, pre-baked News model or post-setup fixture injection
may perform behavior attributed to the agent. Neutral users/site/catalog and
assertion-only DB reads are allowed. Test wrong lower-level scopes, cross-site
IDs, invalid field/item/view/binding, idempotency replay/mismatch, canonical
unchanged before accept, frozen Agent denial and no agent publication.

The E2E must fail if any production semantic operation, real browser execution,
Puck save, snapshot, reviewer promotion or public Render projection disappears.
Run through NGINX with real PostgreSQL/Media/worker; retain artifacts and all
required CI. Production fixes are allowed only for defects exposed in this
already-implemented vertical, not to bypass prerequisites. Binary done is the
entire agent→human→public chain. Report
`085-a-dynamic-news-product-vertical.md` with SELF; no merge/extra PR.
