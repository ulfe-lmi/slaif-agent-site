# OAP Work Order — 086-a (inert until activated)

## Contract and objective

Prove a legitimately authorized Level-4 external agent can destroy every
editable site-domain entity through the public Agent interface while COW,
site, identity and canonical boundaries hold. Links: §§10, 19.4, 21.11,
42.3/42.5, 52.3, 53.4. Requires 075–084 and 085 baseline.

## Required product proof

Seed neutral canonical sites A and B with types/fields/items/translations/
relations/views, pages/components, navigation/items, redirects, locales,
theme/global regions and media references. Human creates a Level-4 workspace
for A. Using only its real capability and public Agent DELETE/move/reset
semantics, delete all editable A state. Workspace preview becomes empty/broken
as expected while canonical/public A, all B state, users/memberships/roles and
physical schema remain byte/row/HTML equivalent. Then human uses the real
discard lifecycle and canonical remains unchanged.

## Anti-bypass and negatives

Direct SQL, ORM, service/repository calls, human/admin mutation routes, internal
endpoints and test-only deletion helpers are forbidden for the destructive
behavior. The test must fail if any required Agent destructive route is removed.
Assertion-only owner reads and neutral fixture setup are allowed. Prove Level 3
and narrowed L4/delete-budget denials; protected identity/site/schema/public
media deletion denial; foreign site/workspace IDs; replay/mismatch; failure/
cancellation residue; no audit gaps; no cross-workspace visibility.

Run real PostgreSQL, public Agent/preview/Control through NGINX, Media, discard,
full relevant Compose/CI. No acceptance of destroyed state is required. Binary
done is exhaustive external destructive authority plus canonical/site/identity
confinement. Report `086-a-real-destructive-agent-isolation.md` with SELF; no
merge/extra PR.
