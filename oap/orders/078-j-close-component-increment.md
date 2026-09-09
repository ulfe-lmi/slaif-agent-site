# OAP Work Order — 078-j: close PR 77 at its human-defined boundary

## Verified state and controlling human override

- Numeric objective: 078; round: 078-j; increment: 078/1.
- Mode: AMEND_EXISTING_PR; PR [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77).
- Head branch: `oap/078-agent-composition-design-semantics`; base: `main`.
- Verified remote main/base: `ae3a4a681bb888260192b7bb1b2a337b4906828d`,
  Objective 077 / PR #74 merged 2026-09-08T05:04:55Z.
- Starting PR head: `127d7f13c6e7e139af94792739e46ffe57cf843a`,
  report-only child of 078-i implementation
  `567973e1897ff0ec1cc5017704dd7b914a88d6da`.
- Refreshed PR size: 90 files, +26,328/-4,509; all 20 checks SUCCESS.
- Existing active 078-i returned exact FIFO OK; coder is waiting. Use this same
  session. No replacement/subagent, new PR, merge or auto-merge in this round.

The human now freezes PR #77 to bounded component composition/data plane plus
component-local design. No site-theme functionality belongs in this PR, even
though 078-i was already delivered before the override. Human reviewability
supersedes the old one-numeric-objective/one-PR convention. Read and publish
`oap/governance/2026-09-09-bounded-semantic-pr-increments.md`; this prospective
amendment controls conflicting previous governance. Preserve all immutable
orders/reports and their history. Remaining Objective 078 continues in a new
PR from verified main after PR #77 is accepted and merged.

## 1. Remove only the deferred theme implementation

Preserve 078-i implementation SHA and report/order in Git history; record their
deferred status in a current increment ledger. Reverse the product, test and
generated/doc changes introduced by implementation commit
`567973e1897ff0ec1cc5017704dd7b914a88d6da` so the retained product baseline
matches 078-h `7597975cfff30a1f31eab4f4d5871695e3ef7fcb`, then apply only
these necessary repairs. Keep 078-i order/report byte-for-byte; do not reverse
their transcript publication or restore active to an old ID. Use a normal new
reversal commit, not reset/rebase/force-push/history rewriting. Do not drop or
downgrade any running valuable database: verification uses disposable fixtures.
The preserved theme commit can later be deliberately reused on a new branch.

Prove no new Agent theme/schema routes, migration 062 theme behavior, theme
controls/assets or theme-only contracts remain in PR #77's final product diff.
Legacy theme behavior already in main is not new work to fix here.

## 2. Confirmed DB property-removal bypass (A)

Strategic independently reproduced this on current head in a disposable real
PostgreSQL DB: direct `slaif_agent_runtime` calls removed `Button.variant`,
`Image.aspectRatio` and `CollectionGrid.columns` with no corresponding L3
scope; each call succeeded and advanced version 1 to 2. Diagnostic:
`/tmp/slaif-strategic-authority-3tLQVd/probe.py` (read-only reference for you).

Anchor: migration 061 `control.slaif_agent_component_authorize_update`
iterates only `jsonb_each(p_new_props)`, while
`content.slaif_agent_component_update` replaces the whole props document.

Derive changes over the union of old and new keys, distinguishing absent from
JSON null. Enforce exact content/design/variant/layout/responsive authority for
ADD, CHANGE and REMOVE, including nested responsive overrides and map-to-scalar
replacement. Unchanged properties require no write scope. An operation changing
or removing existing responsive overrides requires the responsive authority as
well as the property's authority. Keep unsupported props fail-closed.

Preserve public partial-merge semantics; do not introduce a new removal API
unless required to represent an already-supported operation. A direct helper
must not escape the same trusted authority. Add direct runtime hostile tests
for removal of each three named properties, other optional local design
properties, responsive removal, JSON null and unchanged values. Assert denial
preserves rows/versions/quotas/idempotency/audit/COW operations; exact authorized
removal and valid content edits must still work.

## 3. Confirmed CREATE design bypass (B)

The same strategic diagnostic used only L2-equivalent scopes and obtained HTTP
201 for all three named design props; direct runtime CREATE also succeeded.
Anchor: Agent create and migration-060 `slaif_agent_component_create` require
only `component-structure:create`, while catalog-v1's historical content
classification does not reflect current design authority.

Require structure-create plus the same property-derived L3 scopes for any
caller-supplied initial design value. Explicitly supplying a default design
value is still selecting it and requires that property's scope. Server-owned
defaults may initialize omitted design values under structure authority; they
must be fixed trusted defaults, documented, and cannot be caller-controlled.
Handle required design props (Columns.count, Spacer.size) so legitimate L2
structural creation can use approved defaults, and L3 may supply other approved
values. Preserve content fields that are inherently part of creating structure;
do not gratuitously require content-write in addition to structure-create.

Apply the rule to every currently supported local design property, including
responsive values and narrowed resource choices, through HTTP and trusted DB.
Use the existing semantic create route and immutable catalog/design authority;
no ad hoc duplicated classification. Repair by a new append-only migration
after the retained 061 head (062 may be reused for a clearly named authority
repair once deferred theme 062 is removed from the product tree). Preserve
migration-060 and catalog-v1 frozen bytes.

Add narrowed human-issued L2/L3 public HTTP and direct runtime tests for at least
Button.variant, Image.aspectRatio, CollectionGrid.columns; ADD/CHANGE/REMOVE
must share one authority table. Use neutral media/view fixtures, no media
implementation. Prove L2 default structure create works, L2 supplied design is
403, L3 exact scope succeeds, missing responsive scope fails, and denials leave
all durable effects unchanged.

## 4. Replay/no-effect and OpenAPI correctness

Strategic independently reproduced a valid Heading PATCH returning 200 followed
by an identical same-key replay returning 409. The no-effect path prechecks the
old expected version before resolving the existing idempotency record.

Consult durable replay/mismatch state before fresh-state optimistic/no-effect
classification. Within the serialized mutation transaction derive effect,
scopes and expected version from the actual current row. Do not rely on an
HTTP pre-read to decide no-effect, bypass validation or accept stale state.
Prove replay still returns the original result after subsequent edits/deletion,
and a same-key/different-body request returns mismatch. A fresh stale no-op
must conflict; a valid unchanged request consumes no mutation quota/audit/COW
effect and has exact replay accounting. Direct helper and HTTP must agree.

The ordinary `x-slaif-conditional-scopes` metadata currently means "when field
supplied" while runtime uses "when value changes." Make the machine-readable
representation explicit about change/presence, CREATE initial selection,
REMOVE, and responsive transition conditions. Keep exact bidirectional drift
validation with route policy and trusted derivation. Do not weaken runtime
least privilege to fit a simpler schema.

Add focused regressions for the demonstrated replay, no-op concurrent edit,
unknown-null field attempted as no-effect, and each authority condition.

## 5. Governance and current truth reconciliation

This is specifically authorized governance work, not permission to alter
historical artifacts. Commit the strategic-authored amendment unchanged. Add a
short prospective precedence notice/reference in current repository
`AGENTS.md` and `OAP-COMMUNICATION-coding-agent.md`; align maintained
`oap/strategic-instructions` copies and strategic notices from
`/home/ubuntu/codex-supervision/slaif-agent-site`. Add the amendment copy as
needed so their relative references resolve. Do not rewrite prior orders or
reports or imply the old rule never existed.

Create a concise current `oap/INCREMENTS.md` ledger: Objective 078/1 = PR77
component + local design, closing/review pending; 078-i theme SHA preserved,
removed/deferred; next increment = site-theme tokens in a NEW PR after merge.
Objective 078 remains PARTIAL. Order modes, not letters alone, determine new
PR creation; continue NNN-L IDs and strategic merge ownership.

Reconcile current README/API/testing/MVP truth and PR #77 title/body with the
actual retained component/local-design revision. MVP-PROGRESS and
MVP-CONTRACT-AUDIT must state Objective 077 is MERGED/accepted, correct main/base
ae3a4a6, PR77 is open pending strategic acceptance, A/B/replay defects have only
the status supported by tests, and theme work is deferred. Preserve historical
claims as dated evidence, not current truth. Do not describe later objectives
081+ as unfinished parts of this PR or claim full Objective 078 completion.
`oap/active` stays exactly 078-j; final report must match it.

Record final diff size split into production, migration, test, generated and
OAP/docs categories. The large existing increment is a human-authorized closure
exception; no more feature accumulation.

## Verification and stopping rule

Write failing baseline regressions before the repairs and record observed
failures/successful final results. Exercise actual public HTTP and direct
runtime-role calls, not only Python functions or source-string checks. Run
focused A/B/replay/no-effect/narrowed-scope tests; existing component
concurrency/cancellation/migration/privilege and executable Render/Web/Puck
regressions; the affected Agent integration once; generated/policy/quality/docs
checks and required CI. Ensure these critical component regressions are run by
a current CI job (the older PostgreSQL job list omitted test_agent_mutations;
add a targeted component selection if necessary). No unrelated gate weakening.

Check the retained local-design renderer/Puck behavior for regressions induced
by this repair. No global theme, regions/header/footer, new component breadth,
media, MCP, exact-workspace Puck, lifecycle, publication or other feature work.

Use enough local fix/test iterations to finish the specified repairs; do not
return a premature PARTIAL without a concrete technical blocker. Complete
in-scope failures yourself. Passwordless sudo/routine setup remains executor
work. Do not merge; strategy will perform ONE final whole-PR hostile audit.

Publish `oap/reports/078-j-close-component-increment.md` as the final
report-only child of a literal implementation SHA with `Report publication
commit: SELF`. Include baseline and repaired results for A/B/OpenAPI/replay,
source/function anchors, changed effects, scope-trim proof and preserved theme
SHA, governance/truth changes, exact checks/tests, final size categories,
remaining increment scope and strongest reason to reject. Push and verify
report-only parent/path/remote head, send exact FIFO OK, then wait.

