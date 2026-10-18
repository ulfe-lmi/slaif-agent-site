# OAP Work Order — 083-5-a: complete frozen inputs and faithful review rendering

> STATUS: ACTIVATED only after exact active083-5-a and this round's control
> FIFO OK. Earlier draft files and completed round083-4-a are not execution.

## Identity, authority and verified predecessor

ID083-5-a, numeric083 increment5, CREATE_NEW_PR. Existing PR N/A; head NEW.
Create exactly one branch `oap/083-5-a-faithful-frozen-review` and one PR titled
`OAP 083-5-a: complete frozen inputs and faithful review rendering (083/5)`.
Base is freshly reconciled remote main, independently verified as
`4bf74fdc8e74323045a7f8830cf393493e75fe0d` on2026-10-18. PR106 was accepted
and merged10:17:47Z, with all20 required checks successful on report-only
head `eca30683886774051e03a4cba28359d07dab0802`; literal implementation
`fc6752b42056f23465e8d8770af13eff7cea3ca3`. Merge tree equals accepted head.
Postmerge CodeQL39118686136 attempt1 SUCCESS; CI39118686133 attempt1 was
still running at preactivation review. This is an observation, not a failed
gate or permission to bypass a later failure. Reconcile its terminal outcome
before delivery; notify strategy if it fails. No current083 product PR is open;
Dependabot103/104/105 remain HOLD. Do not amend merged PR106 or PR102.

Sole executor remains visible in same tmux window's other pane, exactly
`codex --yolo --profile qwen-neumann`. Human profile overrides default model
allocation; no hidden/additional executor or provider/model override.
Repo `/home/janezp/codex-work/slaif-agent-site`; strategic workspace
`/home/janezp/codex-supervision/slaif-agent-site`. Verify actual control.fifo
and response.fifo there. Coding reads control/writes response, exact ASCII
OK/4f4b/noLF. Read coding AGENTS/protocol, compact architecture, current
governance and applicable nested instructions. Never open full ARCHITECTURE.md.
Preserve untracked .codex/,CODEX-SESSIONS.md,codex.sh. Executor owns routine
packages, browser, DB, Docker, services, fixtures, logs and tests; not human.

## Problem and bounded semantic contract

At verified predecessor,075 materializer plus Python snapshot whitelist omit
model/type/field/item/translation/relation/view inputs and per-page styling.
The production Web review projection matches literal routes, supplies empty
bindings/route parameters and substitutes site theme for page style. Its
string-only format check does not establish version support. These are
source findings; reproduce them through meaningful regression evidence.

Required behavior: a newly frozen snapshot retains the complete existing
site's domain inputs needed for review, and its static and dynamic pages
render the same meaningful result as the trusted active-preview projector,
using frozen inputs alone and the same trusted React renderer/components.
Render routes, locales, collection queries/bindings, page-style precedence,
navigation, regions and media faithfully. Canonical drift cannot change that
frozen result. One coherent format/reader increment includes both capture
and consumption; adding SQL fields without retaining/rendering them is not
completion. No static-only substitute for the dynamic contract.

This increment does not close numeric083. Exhaustive immutable operation/
dependency/audit binding, durable semantic timeline/resource diff after pending
cleanup, generic full-session page-DML publication qualification and re-review
remain subsequent separately ordered increments. Existing protections remain;
do not invent completeness claims for those unfinished families.

## Implementation requirements

R1. Inventory the actual current domain schema and every input consumed by
trusted rendering/validation before editing. Capture site profile, all site
locales and their metadata, theme/global regions, full relevant page records
including raw style_overrides and row versions, normalized composition,
navigation definitions/items, redirects, types/field definitions and versions,
items/translations/relations, complete bounded view/query specifications and
versions, media metadata/reference closure and proposed-side-effect data for
review. Do not execute proposals. Retain all existing relevant statuses and
fields; omission of a deleted/nonrenderable record from the render set must
not erase required retained review/domain information. Inventory actual storage
for mappings/version facts; do not invent nonexistent columns or declare an
uninspected family irrelevant. Distinguish domain inventory from renderable
rows and from promotion's authorized media-reference set.

R2. Trace each new field through trusted SQL materialization, Python validation/
normalization, stored immutable payload, canonical digest, read model, trusted
projection, Web response and approval revalidation. The current whitelist must
not drop it. Use a new explicit supported snapshot format. Bind required
version, validation, media-reference and selected completed-browser-evidence
sibling facts explicitly by digest or verified immutable ID/row binding;
document exactly what the digest covers and what the row binding guarantees.
Do not treat a content-only digest as proof of every sibling. Keep evidence
private and distinguish advisory evidence from publication authority.

R3. Reuse the trusted projection/query/validation behavior for canonical,
preview and frozen review. A narrow extraction of shared pure domain helpers
or an explicit data-source boundary with database and frozen implementations
is in scope. Keep domain semantics in their existing ownership layer. Do not
create a second independent TypeScript query/filter/sort/locale/style engine,
copy SQL semantics into unchecked ad-hoc rules, or fake a database by matching
SQL strings to guessed rows. Prove the real common implementation executes.
Precomputation is acceptable only if every supported request/route/locale and
interaction is faithfully represented under explicit bounds; a handful of
pre-rendered fixture pages cannot replace the required general behavior.

Before substantial product edits, write the source-backed input/consumer map,
chosen shared-projection design, compatibility path and estimated grouped
footprint to `/tmp/oap-083-5-a/design-and-budget.md` for strategic inspection.
This is executor evidence, not authority to change the order or roadmap.

R4. Preserve trusted route normalization, hierarchy/dynamic {slug} resolution,
detail not-found/ambiguity handling, locale selection/fallback/switching,
redirects, ancestors, navigation/regions and site-relative review links. Use
the same collection query validators, type/definition checks, candidate and
result bounds, filters/sort/projection/pagination and component binding
semantics as active rendering, including CollectionList/Grid/Detail/Search/
Filter/RelatedItems. Preserve existing supported search/filter interactions;
do not claim new query features. Preserve raw page overrides and exact trusted
site/page/responsive precedence. Same renderer/tree/CSS/content is required;
only explicit render-context metadata, private URLs and review banners differ.

R5. Frozen projection may read the authorized stored snapshot and necessary
human authorization/current-drift metadata only; never live canonical/COW
content, a live media-descriptor lookup, or an active-preview fallback. Media
bytes remain immutable and authorized reads may use existing private media
service checks. A narrow authorized read-only projection route on an existing
service is permitted if required; justify exact route/schema/grant deltas and
test them. No new service/listener/credential/topology or Control content DML.
No bypass of membership, workspace/site binding, CSRF on mutations, recent
authentication, snapshot_id/digest/summary acknowledgement or final atomic
revision gate. Client-provided context never becomes trusted DB identity.

R6. Validate typed media/document references through actual field/component
schemas, including localized/nested supported values and regions. Freeze
retains required immutable metadata/digests/ownership. Never promote every
visible asset, every UUID-looking value or private browser/source artifact.
Unrelated private assets must remain private; unauthorized/cross-site refs fail
closed. Define inventory versus selected references explicitly. Preserve media
finalization's idempotent crash replay; any private-to-public normalization is
limited to the exact authorized reference set and status transition, not
arbitrary content/metadata drift. Do not change media bytes or broaden authority.

R7. New snapshots must validate supported state/catalog/renderer/composition/
content-model/Puck/design versions and required inputs at capture, read and
approval. Unknown/incompatible/malformed formats fail closed, never fallback
constants, empty bindings or partial success. Preserve old snapshot bytes,
digests, selected evidence and terminal history. Maintain an explicit legacy
reader for stored v1 facts and label its incomplete rendering honestly; never
infer omitted data from current content. Old v1 snapshots cannot qualify for
the new complete-input approval contract. Return a clear stable compatibility
refusal before media/canonical effects, with a documented supported recovery
through a freshly created/reapplied workspace; do not silently migrate/approve
old immutable bytes. Retain authorized view/discard. Preserve revision-drift
error precedence and existing request binding. No new re-review lifecycle here.

R8. Preserve083/4's coherent freeze revision and workspace/advisory/site lock
order, mutation/browser drain, cancellation/recovery and original first-touch
baselines. All captured domain data must correspond to the same frozen
workspace and locked canonical review revision. Bound snapshot record count,
serialized bytes, nesting and projection/query work before unbounded
aggregation/allocation. Reuse product limits with a documented finite snapshot
budget; reject excess with an honest stable failure, no silent truncation or
skipping invalid rows. Bound per-request projection cost even for retained data.

R9. Use new developer migration076_001 and only additional migration(s) if
strictly necessary for this contract and reported within budget. Never edit
old migration bodies or immutable OAP artifacts. Demonstrate upgrade from075,
exact function ownership/search_path/ACL deltas and downgrade restoration;
never reinterpret retained v2 rows as v1 during rollback. Refuse incompatible
downgrade or retain a safe supported reader explicitly, with tested operator
instructions. No new runtime role, broad SECURITY DEFINER edge or private
foundation metadata. Foundation stays exact PyPI0.2.0/frozen hashes, public APIs
only, error conflicts, unchanged FK constraints. Existing composite-FK public
dependency-inspection defect remains disclosed; no patch/monkeypatch/private
SQL/Git dependency/upgrade or workaround enters this increment.

## Finite acceptance and required evidence

A. New format capture: real Agent and human Editor workspace mutations create
or change model/fields, items, translation, relation, view/filter/sort/projection,
page/composition, non-default page/responsive style, and image/document refs.
Prove actual retained values/versions/digests, not counts or key presence.
Trace each R1 family and R2 sibling binding with an explicit source/test map.
Use fixture seeding only for setup; hidden canonical SQL/test-only actor is
not a substitute for the public mutation/freeze/review workflow.

B. Public NGINX E2E compares active preview with immutable review for meaningful
static/list/detail routes and multiple items/locales, selected-locale values
plus default fallback, actual query sort/filter/projection/pagination, related
items, search/filter interaction, navigation/redirect/switcher, region/media
and non-default desktop/tablet/mobile page-style precedence. Use all six stable
targets. Assertions inspect content/order/route parameters and computed CSS,
not merely screenshots, response200 or nonempty bindings. Cover the remaining
binding types in production-level integration/contract tests. Keep real shared
renderer/components, auth, no-store/noindex and private media/artifacts.

C. Another authorized workspace publishes an unrelated valid canonical change
after freeze through the existing qualified publication path. Stored payload,
digest, captured domain values, frozen route projections and meaningful rendered
output remain unchanged; separately named current revision/drift may change.
Retain immutable content/projection after terminal discard and pending cleanup;
existing qualified composition acceptance can supply accepted-history proof.
Do not claim full semantic timeline/diff retention or generic page-DML
publication from this test. No live fallback, even when live content/media
descriptor retrieval is deliberately made unavailable in a focused proof.

D. Counterfactual regression evidence: meaningful tests fail if a captured item
field/translation, model/view version, relation, raw/resolved page style,
binding or shared projection execution is omitted/replaced with a stub.
Use isolated copies or reversible test instrumentation; restore exact source
and prove no contamination of another live test. Do not mutate protected
production data or add test-only policy bypasses to the shipped product.

E. Negative/security/lifecycle proof: missing required input, unknown version,
malformed/dangling/cross-site binding, stale definition, wrong site/workspace,
snapshot/digest mismatch, over-budget snapshot/query, unauthorized media and
legacy approval all refuse without canonical/revision/audit/outbox/accepted
effects. Test actual legacy bytes/read/discard/approval refusal, supported
recreation and rollback behavior. Preserve original touched-row baselines,
coherent freeze/accept serialization and cancellation/failed-freeze rollback.
No wrong-site/role/token oracle or leaked private source/browser artifact.

F. Required full gates: all31 standing commands below, the fresh complete
unfiltered backend integration directory including all new cases, exact
migration/ACL roundtrip, complete public Compose/edge/six-device smoke and
every20 final-PR check successful at final report-only SHA. Focused passing
subsets cannot replace the full directory or whole smoke. Preserve every
failed attempt and its exact tested identity/command/exit/count; unknown cause
stays unknown. Do not aggregate separate partial runs into a full pass.

Standing31 commands (repo root; exact pinned tools per coding AGENTS):

```bash
uv lock --check
uv sync --frozen --all-groups
uv run --frozen ruff check services/backend tests/repository tools
uv run --frozen ruff format --check services/backend tests/repository tools
uv run --frozen mypy
uv run --frozen pytest services/backend/tests/unit tests/repository
uv build --out-dir /tmp/slaif-agent-site-distributions
python -m slaif_agent_site.control_api --check
python -m slaif_agent_site.editor_api --check
python -m slaif_agent_site.agent_api --check
python -m slaif_agent_site.render_api --check
python -m slaif_agent_site.mcp_adapter --check
python -m slaif_agent_site.media_service --check
python -m slaif_agent_site.review_worker --check
python -m slaif_agent_site.scheduler --check
python -m slaif_agent_site.media_gc --check
python -m slaif_agent_site.bootstrap --check
node --version
pnpm --version
pnpm install --frozen-lockfile
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
pnpm build
pnpm licenses list --json
python -m compileall -q tools tests/repository
python -m unittest discover -s tests/repository -p 'test_*.py'
python tools/check_repository.py
python tools/check_mermaid.py
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
```

Also `uv run --frozen pytest services/backend/tests/integration` and full
`sh tools/compose/smoke.sh slaif0835` with isolated disposable fixtures/volumes.
Record actual per-command exit, Python/PG/Node/pnpm/uv versions and full source
identity. Existing CI's PG matrix does not currently select the freeze module;
do not claim new cases ran all PG versions from unrelated matrix success.
No CI/test/workflow/timeout/quota weakening to manufacture completion. Product
snapshot/query budgets are actual fail-closed domain limits, not test waivers.

Required20 names, each COMPLETED/SUCCESS at final report-only SHA:

- Analyze (actions)
- Analyze (javascript-typescript)
- Analyze (python)
- CodeQL
- Compose and edge packaging
- Dependency review
- Detect supported languages
- Foundation PostgreSQL 14
- Foundation PostgreSQL 15
- Foundation PostgreSQL 16
- Foundation PostgreSQL 17
- Foundation PostgreSQL 18
- Markdown
- Mermaid
- Node contracts
- Python 3.12 quality and package
- Python 3.13 quality and package
- Python 3.14 quality and package
- Repository policy
- Supply-chain evidence

Reconcile live strict ruleset20934043 and integration app IDs15368/57789;
no missing/neutral/skipped/pending/cancelled/failed result qualifies. Record
workflow run IDs and actual attempts, not nonexistent check-run attempt fields.
No deterministic unchanged-head reruns until green. One genuine documented
CI-flake rerun requires original logs/cause and exact attempt. Final report
records actual implementation-head observations; SELF checks may honestly be
pending and strategy independently waits. No report amendment for later CI.

## Budget, explicit non-goals and documentation

Predeclared estimate: up to16 production/config files, including1 migration
(second only if necessary and explicitly justified); up to16 test/pin files,
up to4 generated contract files, up to6 current docs,3 OAP transcript paths.
Expected substantive scale approximately1800–2400 production/migration lines
plus1800–2400 test lines; necessary exact SQL downgrade duplication itemized
separately, not hidden. Generated contract and moved-code volume count too.
The several-thousand-line review trigger is likely: provide an early cumulative
grouped inventory/design map before crossing3000 changed substantive lines or
20 implementation files. At the trigger enter CLOSURE_ONLY, notify strategy
and retain only this finite capture/render contract and its evidence. Strategy
will reassess coherent reviewability before acceptance. Do not silently add
families, choose a new ID/PR or use tiny rounds to hide cumulative size.

The capture and rendering portions stay together because the new immutable
format must have its faithful supported consumer. This is a reason for early
strategic size review, not an exemption from it. If the contract cannot remain
reviewable, return accurate partial evidence for a strategic split decision;
do not trade away dynamic fidelity, complete inputs or compatibility to pass.

Explicit non-goals: exhaustive operation/dependency/audit-set closure; replacing
071 backing-table timeline/diff implementation; generic page-DML promotion or
foundation dependency workaround; re-review/multiple snapshot selection;
new primitives/catalog/query features; MCP/source/News/reconstruction/GC/backup;
human content management forms/navigation redesign; browser/dependency/security
pin refresh; Dependabot; new services/topology/credentials. Necessary shared
projection extraction and format compatibility are in scope, broad cleanup not.

Preserve all architecture invariants: every online write through workspace,
server-owned site/session/operation context, human-only reviewer-atomic
publication, immutable media/private evidence, separate runtime/reviewer/setup
authority, browser observation/confinement, no arbitrary code/CSS/SQL or new
outbound/telemetry/hosted/license/dependency. No architecture/security exception
authority. Root architecture/constitution/protocol sources stay unchanged.

Update snapshot/render/upgrade/security/operations docs and truthful current
increment/readiness surfaces, including accepted PR106 and this increment.
Document format/bounds/legacy view/refusal/recreation, exact digest versus row
bindings, private media/reference semantics and query reuse. Generated API
contracts must match any strictly necessary read route change; Agent/MCP
contracts otherwise unchanged and report stripped identity separately. Never
claim numeric083/MVP/product/release completion. Remaining full product work
includes immutable operation/audit closure/re-review and all planned downstream
MCP, News, destructive isolation, source/reconstruction, lifecycle/recovery/
backup/final hostile gates, named repeatable_object and required human UI.

## GitHub workflow and exact handoff

Fetch/reconcile remote base; new branch and exactly one PR for083/5. Commit
activated order/active unchanged, bounded implementation/tests/docs, push and
inspect/repair in-scope CI. No merge/auto-merge/acceptance/next-ID selection.
Routine local setup remains executor-owned with passwordless guest sudo;
never access production systems/data/secrets or unrelated host credentials.

Final report exact basename083-5-a-faithful-frozen-review.md; enum status;
PR/branch/base/starting40hex/literal Implementation head SHA; Report publication
commit: SELF; unchanged order hash/active bytes; R1–R9/A–F evidence map;
actual source/test/CI/log paths/hashes/commands/exits/counts/attempts/failures;
grouped cumulative base-to-head budget/variance/moves/duplication; exact route/
schema/grant/version/compatibility decisions; security and remaining limits.
COMPLETE only if all named criteria actually executed. Never invent a PR,
future CI success, unspecified cause or generalized product completion.

Lint complete report temp with exact repository Markdownlint config before
same-filesystem atomic publish; never overwrite an existing report. Commit
only the new report as child S of literal I, push, verify exact remote
head/parent/sole path/bytes, then exact responseOK. No repository mutation
after S. Return to control wait. Strategy independently reviews, accepts,
merges and verifies remote main; OK never means approval.
