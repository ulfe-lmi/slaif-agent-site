# MVP Progress Tracker

This tracker uses the contract-audit status vocabulary rather than file
presence or completion estimates. The authoritative baseline is
[`MVP-CONTRACT-AUDIT.md`](MVP-CONTRACT-AUDIT.md), updated for the protocol-final
Objective-078-j source revision developed in PR #77 on 2026-09-09. GitHub's PR
state and merge commit are authoritative for whether that revision is contained
in `main`; its verified main base is the accepted Objective-077 source
revision, `ae3a4a681bb888260192b7bb1b2a337b4906828d`.

## Current verdict

**CONTRACTUAL MVP NOT COMPLETE.** Merged Objectives 065–076 prove narrow,
bounded contracts; the Objective-077 source revision provides complete evidence
for its bounded page/locale/navigation/redirect/dynamic-Render information
architecture; and the Objective-078-j source revision provides complete
evidence for the bounded Agent component/local-design data plane on open PR #77. The active
078-g added bounded local design semantics, and 078-j repairs exact
property-level authority, initial design selection, removal/replay semantics,
and current OpenAPI truth; the focused public-Agent/PostgreSQL/Render/Web/Puck evidence is not credited until
all gates complete. Objective 078 remains partial because site-global theme,
global-region behavior and the later review lifecycle, publication,
reconstruction, or final MVP contract are not proven. PR acceptance and merge
state remain external GitHub/OAP facts.

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

## Objective 077 source revision

The protocol-final 077 source revision on [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74)
maps the immutable 077-a through 077-z transcript to executable Agent,
Editor, Render, NGINX/browser, migration, concurrency, recovery, contract, and
hostile-negative evidence for bounded pages, locales, navigation, redirects,
and dynamic collection rendering. Its narrow information-architecture
contract is **COMPLETE — E2E PROVEN** at the source revision. GitHub records
whether strategic acceptance has placed it in `main`. The contractual MVP
remains **NOT COMPLETE**.

## Objective 078 source revision

The 078-j source revision on [PR #77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77)
maps the immutable 078-a through 078-f transcript to the existing public Agent
and shared Render/Web/browser boundaries. Its bounded component slice is
**COMPLETE — E2E PROVEN** at the open-PR source revision: a clean NGINX-only
workflow creates and reads an empty-to-nested Section/Container/Heading/RichText
composition, updates content props, moves with semantic anchors, preserves
IDs/props/hierarchy/order/versions across Agent/Render/Web restarts, deletes
leaves then parents, and proves private browser artifacts, hostile negatives,
idempotency/audit/quota/COW isolation, and canonical non-change. The active
078-g added the typed `design-system/v1` authority and bounded local
variant/layout/responsive mutation; 078-j repairs its exact property-level
scope/OpenAPI truth, initial design selection, removal/replay/no-effect
semantics, and classifies the existing Button/Image/CollectionGrid visual
properties. Focused public-Agent/PostgreSQL/Render/Web/Puck evidence is
required before crediting this repaired design slice. Site-global theme, global-region,
exact-workspace Puck, review, promotion, and publication remain
**PARTIAL/NOT IMPLEMENTED**; this does not claim that PR #77 has merged or that
the contractual MVP is complete.

## Active and remaining sequence

The active transcript pointer remains `078-j` until strategy selects and signals
the next objective. The source revisions have complete bounded 077 evidence and
complete bounded 078 component evidence; acceptance and containment in `main`
are determined by OAP and GitHub state, not this document. All later order files
remain inert until strategy selects and signals them.

| Order | Contractual scope | Current status |
|---|---|---|
| 077 | Agent page, navigation, redirect, and bounded dynamic collection Render semantics | COMPLETE — E2E PROVEN at 077-z source revision; consult authoritative PR/main state for merge |
| 078 | Agent composition and design semantics; bounded component data plane | PARTIAL — component/local-design slice and 078-j authority/replay repairs are on open PR #77 pending strategic acceptance; site-theme/global-region scope remains deferred |
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
