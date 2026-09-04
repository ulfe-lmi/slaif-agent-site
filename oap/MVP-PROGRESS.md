# MVP Progress Tracker

This tracker uses the contract-audit status vocabulary rather than file
presence or completion estimates. The authoritative baseline is
[`MVP-CONTRACT-AUDIT.md`](MVP-CONTRACT-AUDIT.md), evaluated against merged
Objective 076 commit `067676314e0d9664d40cb8514ea549b966a4eb2d` on
2026-09-02.

## Current verdict

**CONTRACTUAL MVP NOT COMPLETE.** Merged Objectives 065–076 prove narrow,
bounded contracts, with 073 repairing current-state claims and 074–076 adding
real Agent control and model/content semantics. None of those slices alone
proves the broader product capability, review lifecycle, or publication
contract.

## Merged narrow slices

| Objectives | Narrow evidence credited | Status |
|---|---|---|
| 065–066 | Runtime ContentModel wiring and capability/Agent edge checks | COMPLETE — E2E PROVEN |
| 067 | Five capability-bound, COW-confined, idempotent, audited create operations | COMPLETE — E2E PROVEN |
| 068 | Human Puck composition editing through the Editor boundary | COMPLETE — E2E PROVEN |
| 069 | Seven capability-bound COW reads and workspace/tombstone identity behavior | COMPLETE — E2E PROVEN |
| 070 | Immutable content-addressed media upload and lifecycle safety | COMPLETE — E2E PROVEN |
| 071 | Canonical and authorized active-workspace rendering | COMPLETE — E2E PROVEN |
| 072 | Confined Chromium runs, durable artifacts, retrieval, restart/outage/revoke negatives | COMPLETE — E2E PROVEN |

These statuses are narrow evidence claims. They do not make Agent semantics,
MCP, review snapshots, promotion, publication, source reconstruction, or
operations complete.

## Merged 073–076 prefix

These rows are credited from the merged GitHub PRs and their production-boundary
evidence, not from the existence of files or the confidence of an execution
report.

| Objective | Merged evidence credited | Status |
|---|---|---|
| 073 / [PR #69](https://github.com/ulfe-lmi/slaif-agent-site/pull/69) | Truthful MVP audit/control-state and roadmap repair, merged as `74d9c189fe241356fbe03f2632197ecbb1ce53a3` | COMPLETE — CURRENT-STATE AUDITED |
| 074 / [PR #70](https://github.com/ulfe-lmi/slaif-agent-site/pull/70) | Public human Agent workspace/capability issuance, site/CSRF/policy authority, idempotency, audit, revoke, and restart proof, merged as `ef456e63abadddfc7d90794c03be3a63677c87f9` | COMPLETE — E2E PROVEN |
| 075 / [PR #71](https://github.com/ulfe-lmi/slaif-agent-site/pull/71) | Editable-domain substrate, validators, query contract, locale/navigation/redirect integrity, production COW upgrade, and Agent binding, merged as `0e83b26bf9a9f63bff6756d65cbfd527d215ec51` | COMPLETE — E2E PROVEN |
| 076 / [PR #72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72) | Capability-bound Agent model/type/field/item/translation/relation/collection-view REST semantics, strict policy/audit/COW/concurrency, canonical OpenAPI, public NGINX evidence, and PostgreSQL 14–18 CI, merged as `067676314e0d9664d40cb8514ea549b966a4eb2d` | COMPLETE — E2E PROVEN |

## Active and remaining sequence

The current active order is `077-b` on [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
which remains open and unmerged. The broader 077 page/navigation/redirect/
Render contract remains `PARTIAL` on current `main`; the unmerged 077-a page
slice is evidence under strategic review, not merged product truth. All later
order files remain inert until strategy selects and signals them.

| Order | Contractual scope | Current status |
|---|---|---|
| 077 | Agent page, navigation, and redirect semantics | ACTIVE — PR #74 OPEN/UNMERGED; 077-b prerequisite round |
| 078 | Agent composition and design semantics | PARTIAL |
| 079 | Agent media semantics and references | PARTIAL |
| 080 | Real MCP semantic parity | SCAFFOLD ONLY |
| 081 | Human Puck editing in the exact Agent workspace | PARTIAL |
| 082 | Immutable freeze and review snapshot | NOT IMPLEMENTED |
| 083 | Real human accept/discard promotion lifecycle | SCAFFOLD ONLY |
| 084 | Conflict-safe review lifecycle | NOT IMPLEMENTED |
| 085 | Dynamic News product vertical | NOT IMPLEMENTED |
| 086 | Destructive Agent isolation proof | NOT IMPLEMENTED |
| 087 | Approved-origin source tools and responsive sweep | NOT IMPLEMENTED |
| 088 | Contractual fixture reconstruction | NOT IMPLEMENTED |
| 089 | Expiry, cleanup, and worker-claim lifecycle | PARTIAL |
| 090 | Backup and restore operational proof | NOT IMPLEMENTED |
| 091 | Final hostile MVP truth gate | NOT IMPLEMENTED |

This document does not activate any order. Objective 088 is a contractual MVP
objective, not post-MVP work.

## Evidence policy

Acceptance requires production behavior through its intended public boundary,
relevant negative evidence, and the architecture invariants. A green check or
the existence of a route, type, helper, or order file is not evidence that the
corresponding contractual capability is complete.
