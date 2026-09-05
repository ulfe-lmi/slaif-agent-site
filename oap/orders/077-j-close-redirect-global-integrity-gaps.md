# OAP Work Order — 077-j

## Objective and verified PR state

Close the concrete global-integrity and evidence gaps found by independent
review of 077-i. Amend only
[PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), branch
`oap/077-agent-site-structure-semantics`, base `main`; no new PR and no merge.
Required starting remote report head:
`afacfb33fa56b1489ee9983b61d3b097f1d752b4`, whose sole parent is 077-i
implementation `f76ec0da661261da9d2c4760b5ae66b2ff4f750a`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

Preserve all valid 077-a through 077-i behavior. The redirect public surface is
present, but 077-i is not accepted because its capability-filtered graph
validation and narrow test evidence do not prove the ordered global invariants.
This is a redirect repair only; dynamic Render remains next.

## 1. Global graph integrity cannot be capability-filtered

Current Agent create/update/delete calls
`slaif_redirect_validate_state(..., true)`, which skips redirects outside the
calling capability's locale/route constraints. A capability can therefore
rename or retarget a visible redirect while a hidden redirect depends on its
old source, leaving the workspace's complete graph dangling or cyclic even
though its filtered subgraph passed.

Separate authorization visibility from structural integrity:

- authenticate/authorize the requested redirect and validate its source/target/
  locale/route-prefix/resource bound through the capability;
- after the tentative COW mutation, validate the complete visible workspace
  redirect/page graph for that site, including resources hidden from this
  capability, under the shared structural lock;
- rollback the whole mutation on any global dangling target, source/page
  collision, ambiguous fallback, cycle or chain overflow; and
- return one stable non-leaking conflict/domain denial without disclosing the
  hidden redirect ID, path, locale or target.

Update/delete must simulate the actual resulting graph rather than relying on
an overbroad path-only precheck. A delete/update is allowed when locale fallback
or another exact route still satisfies every incoming edge; it is denied only
when the complete post-mutation graph would be invalid. Preserve exact row
versions, quota/idempotency/audit rollback and canonical isolation.

Add a restricted-capability public Agent test with hidden route-prefix and
locale redirects that attempts source update, target update and delete. Prove
it cannot corrupt the hidden graph, receives no hidden identifiers/details,
and leaves no quota/idempotency/audit/COW residue. Also prove a globally valid
mutation is not rejected merely because unrelated hidden redirects exist.

## 2. Use one authoritative resource-constraint parser

Migration 051 introduces `control.slaif_agent_redirect_constraints`, a second
copy of most resource JSON parsing. It does not validate every nonredirect
array member as strictly as the authoritative
`control.slaif_agent_resource_constraints`, creating drift and a trusted-wrapper
bypass for malformed mixed constraints.

The unmerged migration 050 parser already includes `max_visible_redirects`.
Make redirect wrappers consume that one authoritative full validator, either
directly or through a thin projection that calls it and adds no duplicate JSON
parsing. Remove the duplicated parser body. A malformed type/page/navigation/
locale/delete constraint must fail closed before redirect behavior even when
HTTP model validation is bypassed; every existing page/model/navigation caller
must continue to accept `max_visible_redirects`.

Add database-level mixed malformed-constraint tests plus fresh 049→050→051,
050→051 upgrade, downgrade/re-upgrade, owner/search-path/grant and privilege
evidence. No private foundation relations/functions or data loss.

## 3. Supply the missing concurrency and cancellation proof

077-i added one large Agent redirect test and reused earlier structural tests;
it did not add the specifically ordered redirect cross-interface/page races or
redirect graph cancellation proof. Add deterministic real PostgreSQL tests,
through production Agent HTTP and Editor HTTP where applicable, for:

- Agent redirect-source create/update racing Editor page create/route update;
- Agent page move/restore racing Editor or Agent redirect-source creation;
- Agent page delete/route update racing an internal redirect target;
- Agent redirect delete racing an Editor/Agent dependent redirect create;
- restricted Agent source update racing a hidden Editor redirect dependency;
- cancellation while waiting on the structural lock; and
- cancellation after tentative graph mutation but before completion/audit.

Use database lock/event barriers, never timing sleeps. Every result must be a
coherent serialization: no route/redirect collision, no dangling target, no
cycle, no hidden-resource leak, no deadlock, and zero unintended page/redirect/
quota/idempotency/audit/COW residue for the loser/cancelled request. The same
idempotency key must remain usable after rollback where contractually valid.

Make these tests fail if Editor redirects use a separate lock, if page guards
run outside the mutation lock/transaction, or if Agent graph validation filters
hidden rows. Neutral owner SQL may seed/assert only and cannot perform claimed
Agent/Editor behavior.

## Verification and scope

Repair migration 051/functions/tests in place where safe; preserve the five
public redirect routes, typed schemas, exact scopes/actions/errors, HTTPS and
static/internal target grammar, locale fallback, page dependencies, route
prefix, max-visible bound, canonical OpenAPI and public NGINX journey. Update
docs only if externally observable semantics change.

Run focused global-graph/resource/race/cancellation/migration tests, full Agent
and Editor integration, Python quality/unit, OpenAPI/route-policy, PG14–18,
repository/Markdown/Mermaid, Node, clean Compose public acceptance and all
current required CI. Preserve Chrome `152.0.7977.82`, zero current Critical and
empty exceptions.

No dynamic Render/list/detail routing; no locale/navigation/page feature beyond
the exact coupling repair; no composition/design/Puck/media/MCP/freeze/review/
promotion/source/sweep or 078+ work. No dependency/image/exception/
architecture/historical artifact/general refactor/issue closure/production
claim or production access. Do not reopen 076.

Verify/update only PR #74. Commit this exact order and `oap/active` unchanged
with the bounded repair/tests, push, create no PR, never merge/auto-merge, and
repair only in-scope current-head failures.

Publish exactly
`oap/reports/077-j-close-redirect-global-integrity-gaps.md` as the final
report-only child of a literal implementation SHA with `Report publication
commit: SELF`. Include exact commits/files/functions/parser/grants; complete-
graph versus authorization visibility design; hidden dependency/fallback
outcomes; all required Agent/Editor/page/redirect races and cancellation;
quota/idempotency/audit/COW/isolation/migration evidence; commands/counts/skips/
current checks; no private dependency/scope drift/new PR/merge/exception/
secret; remaining Objective 077 scope; and strongest reason not to accept.

`PARTIAL`/`BLOCKED` requires a concrete external/technical blocker with exact
attempted evidence. Do not return early because tests or CI are long. No
post-report push. Signal exact FIFO `OK`, then wait for strategic review.
