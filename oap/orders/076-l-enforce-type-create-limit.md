# OAP Work Order — 076-l

## State and objective

AMEND_EXISTING_PR #72 only; branch
`oap/076-agent-model-content-semantics`, base
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`, required start head
`787505bfd0dc12e095503e3cbee66346b21b522f` (076-k report; parent transcript
`d58ae1e1001eb5f35cabd427959bcde8f53cfed7`). No new PR/merge.

Implement exactly one production function in unmerged revision 044: replace
the existing-signature `content.slaif_agent_content_type_create` so it calls
the typed owner-only resource helper, rejects a key outside a nonempty
`allowed_type_keys`, and enforces `max_content_types` against ACTIVE types
visible in the trusted COW session. Serialize count+insert with one deterministic
transaction advisory lock derived from trusted `app.session_id`; direct runtime
calls and concurrent HTTP calls cannot bypass the maximum. Preserve every
pre-044 validation, site/COW rule, return shape and grant; revoke PUBLIC.
Downgrade restores the exact old create function/grant.

Add one focused real-PostgreSQL test covering: allowed/disallowed key; exact
sequential maximum; two connections racing one remaining slot yield one success
and one stable denial; exact visible final count/no residue; direct wrapper
bypass denial; and helper not executable by runtime. Reuse existing mutation
fixtures. Run Ruff and only that test on PostgreSQL 16 plus 044 downgrade/
upgrade. Fix focused failures; no broad suite or CI rerun. Do not return before
both function and test exist unless a genuine external DB/tool outage occurs.

Non-goals: update/delete/field wrappers, audit, HTTP/OpenAPI changes, other
entities/deps/docs/governance. Publish immutable
`oap/reports/076-l-enforce-type-create-limit.md` as report-only child of literal
40-hex implementation SHA; exact commands/results/check state, SELF, no extra
PR/no merge/no secrets/no post-report push.
