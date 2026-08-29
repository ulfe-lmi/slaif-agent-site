# OAP Work Order — 076-a (inert until activated)

## Contract and objective

Expose the smallest complete contractual Agent REST/OpenAPI model/content
surface over 075: types, fields, items, translations, relations and collection
views. Links: §§15.4, 21.3–21.6, 24.1–24.5, 26–27, 52.5; requires 075.

## Production requirements

- Add typed discovery/exact-read/create/update/delete routes for all named
  families and declarative model mappings actually needed by MVP.
- Generalize Objective 067's five-create pipeline for typed update/delete
  results while preserving capability-derived site/workspace, shared lock,
  ACTIVE recheck, server operation UUID, durable idempotency/replay mismatch,
  same-transaction semantic audit and COW-only writes.
- Enforce immutable capability resource constraints plus request/mutation/
  create/delete quotas at route and transaction boundaries. Correct distinct
  scope requirements (`field-definition:*`, relation/view scopes) and Agent
  route-policy classification/coverage; no SYSTEM_HEALTH exemption.
- Apply 075 validators at write time and again at freeze/promotion. Expose a
  deterministic versioned Agent OpenAPI document/artifact and drift tests; no
  storage/database concepts.

## Acceptance and anti-bypass

A real human-issued capability through public NGINX performs CRUD for each
family and proves overlay reads, canonical independence, replay/restart,
operation/audit completeness and exact OpenAPI. Negative tests cover scope/
ceiling/resource/delete quota, wrong site/workspace/parent/type, invalid model/
item/query/relation, cross-site targets, frozen/expired/revoked state,
idempotency mismatch and direct runtime-wrapper misuse with zero residue.

No service/ORM/SQL/test helper may perform Agent behavior; neutral canonical
setup and assertion-only owner reads are allowed. Run real PG14–18, public
HTTP/OpenAPI, route policy, migrations/privileges, full relevant Compose/CI.
No pages/navigation/composition/design/media/MCP/review. Binary done is the
complete named external surface. Report `076-a-agent-model-content-semantics.md`
with SELF; no merge/extra PR.
