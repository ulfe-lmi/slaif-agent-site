# OAP Report — 076-i

ID: 076-i  
Order: `oap/orders/076-i-harden-resource-helper.md`  
Result: PARTIAL  
Delivery: AMENDED_EXISTING_PR

Repository: `ulfe-lmi/slaif-agent-site`  
PR: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72) (OPEN)  
Base: `main` (`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`)  
Starting report head: `fcf8594f6a71e6f4d676af9e9403aacd4ce85afb`  
Transcript commit: `243fc46`  
Final implementation SHA: `334b35ea536c83ce2b9b1d466b078c5256084a54`  
Report publication commit: SELF

## Implemented

Revision 044 now exposes only owner-defined
`control.slaif_agent_resource_constraints(uuid)`; it derives workspace from
trusted `app.session_id`, parses UUID session/operation settings safely, binds
the requested site through `slaif_agent_require_cow_site`, validates top-level
constraint keys, returns typed allowlists/maxima/delete fields, and revokes
PUBLIC and runtime-role execution. Downgrade removes the exact signature.

## Verification and limitations

- Ruff passed.
- `uv run --frozen pytest services/backend/tests/integration/test_content_model_cow.py -q` — `1 passed`.
- Full helper malformed-value/role-denial/downgrade-roundtrip module was not
  added; existing six wrappers do not yet invoke serialized DB maxima. No
  concurrency or wrapper-bypass proof is claimed, and final report-head CI was
  not awaited in this round.

No merge, acceptance, second PR, post-report push, architecture/constitution/
protocol edit, production access, or real secret/capability/cookie/token was
used. Prior reports were not edited.

Report publication commit: SELF
