# MVP Progress Tracker

This tracker uses the contract-audit status vocabulary rather than file
presence or completion estimates. The authoritative baseline is
[`MVP-CONTRACT-AUDIT.md`](MVP-CONTRACT-AUDIT.md), evaluated against merged
Objective 072 commit `bcaddc41f9ef4e779dd1a8c9a41eb08462250d53`.

## Current verdict

**CONTRACTUAL MVP NOT COMPLETE.** Objectives 065–072 each prove a narrow,
bounded behavior. None of those slices alone proves the broader product
capability, review lifecycle, or publication contract.

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

## Dependency-correct planned sequence

The following order files are separate inert Markdown artifacts. They remain
inactive until strategy refreshes state, selects one exact `oap/active` value,
and sends the protocol signal.

| Order | Contractual scope | Current status |
|---|---|---|
| 074 | Human Agent workspace and capability control plane | SCAFFOLD ONLY |
| 075 | Complete editable-domain substrate and validators | NOT IMPLEMENTED |
| 076 | Agent model/content/view/relation REST and OpenAPI | PARTIAL |
| 077 | Agent page, navigation, and redirect semantics | PARTIAL |
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

No planned order above is activated by this document. Objective 088 is a
contractual MVP objective, not post-MVP work.

## Evidence policy

Acceptance requires production behavior through its intended public boundary,
relevant negative evidence, and the architecture invariants. A green check or
the existence of a route, type, helper, or order file is not evidence that the
corresponding contractual capability is complete.
