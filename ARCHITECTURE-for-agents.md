# SLAIF Agent-Site architecture — compact agent edition

**Status:** Proposed, normative agent edition

**Source:** `ARCHITECTURE.md`, Revision 2.1, 2026-08-17

**Source SHA-256:** `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`

**Repository/product:** `slaif-agent-site` / SLAIF Agent-Site

**License:** Apache-2.0

**Foundation:** PyPI `agent-cow-postgresql==0.2.0`, MIT, imports
`agentcow`/`agentcow.postgres`

This is the default architecture specification for AI agents. It preserves the
source's normative decisions, invariants, boundaries, lifecycle, interfaces,
data model, security/privacy/operations rules, tests, acceptance criteria,
ADRs, and limitations in compact form. It omits diagrams, citations, repeated
rationale, and reader-oriented examples. The full source remains a human-facing
record. **Only a direct instruction from the human/user authorizes an agent to
load `ARCHITECTURE.md`.** If this edition is absent, insufficient, ambiguous,
or conflicts with another governing document, stop the affected work and
escalate; do not open the full source without that direct instruction and do not
invent or weaken architecture.

## 1. Product contract, goals, non-goals

SLAIF Agent-Site is a fully self-hosted, agent-first, human-governed platform in
which humans and external AI agents build/redesign/manage websites in isolated
workspaces, inspect the actual responsive result, and publish only after
authorized human review. Agent-Site is the product. SLAIF Agent-State is its
internal reusable workspace/capability/delegation/audit/review/promotion/expiry/
cleanup subsystem and is extracted only after a second non-website consumer.
`agent-cow-postgresql` is the separate generic logical PostgreSQL COW substrate.

Core security contract: a request authorized solely by an Agent-Site agent
capability can modify only its deployment-, site-, and workspace-bound isolated
state. It cannot write canonical content; publish; accept/discard/freeze/create
workspaces; mint/revoke capabilities; manage sites/domains/users/memberships/
roles/identity; run raw SQL or physical schema migrations; register executable
field/query/component primitives; edit source/CSS/JS/packages/edge/container/
infrastructure; read secrets; or execute production side effects.

Product/engineering goals:

- Clone plus `docker compose up --build` runs the complete demonstrator at
  `http://localhost:8080` without account, subscription, hosted service, cloud
  key, DNS/wildcard, or manual Python/Node/browser/PostgreSQL/NGINX/extension
  install. Public/admin/Puck/preview/API/workers/browser/DB/media run locally.
- Multiple institutionally trusted sites, site-scoped users/roles/delegation,
  configurable content types/fields, normalized page composition, Puck human
  editing, semantic REST/OpenAPI and MCP, immutable media, private previews,
  curated Playwright feedback, and human-only conflict-safe publication.
- Nontechnical users choose four understandable agent delegation presets.
  Level 4 can reconstruct a site within bounded field/component/design/query
  primitives. Humans and agents mutate one normalized composition; canonical,
  active-preview, and immutable-review rendering use one trusted renderer and
  component implementation.
- Use high-level `asyncpg_cow_session`/`asyncpg_cow_reviewer`, native PostgreSQL
  transactions, stateless services where practical, one PostgreSQL deployment
  with role/schema boundaries, reproducible locks/images, invariant tests,
  Puck-independent persistence, independently scalable browser workers, and
  application-owned security policy rather than edge rules.

Contractual non-goals: new DB engine; physical/full DB clones; raw agent SQL;
agent DDL/Alembic; agent-defined executable primitive/query/component/code/CSS/
JS/template/package/plugin; WordPress compatibility/ecosystem parity; arbitrary
HTML or unrestricted Playwright/evaluation/URL/`file://`; agent publication;
guaranteed merge resolution; hostile public SaaS or mutually hostile tenant
isolation; guaranteed narrow-phone Puck ergonomics; transactional arbitrary
external services; custom model/agent runtime; mandatory hosted LLM; protection
from malicious infrastructure/PostgreSQL owner/promotion worker; replacement
for PostgreSQL backup/PITR.

## 2. Fixed decisions and hard constraints

| Area | Normative decision |
|---|---|
| Repository | New monorepo `slaif-agent-site`; internal Agent-State, separate foundation |
| Foundation | PyPI `agent-cow-postgresql==0.2.0`; exact registry artifact hashes in committed `uv.lock`; GitHub only source/provenance/issues |
| Database/isolation | Ordinary self-hosted PostgreSQL; logical per-workspace COW |
| Edge | NGINX OSS default/reference; Apache HTTP Server 2.4 supported adapter; no product semantics at edge |
| Web/editor | One self-hosted Next.js/React/TypeScript app; Puck behind product adapter/schema; Tailwind OSS, shadcn/ui source, Radix |
| Backend | FastAPI, asyncpg, typed domain/contracts |
| Browser | Playwright E2E plus separately confined internal visual/source worker; curated tools only |
| Queue | PostgreSQL durable transactional claims; no mandatory Redis/RabbitMQ/Kafka |
| Media | Immutable content-addressed `MediaStore`; local volume default; shared filesystem or approved self-hosted backend at scale |
| Packaging | OCI images plus Compose Specification; only NGINX publishes a demo host port |
| APIs | REST/OpenAPI canonical; MCP delegates to the same semantic services |
| Editing | Every online human/agent editorial write uses a workspace |
| Publication | Reviewer authority absent from agent-facing processes; human-only atomic promotion |
| Site model | Multi-site-capable v1; site-confined institutional tenancy, not hostile SaaS |
| Site schema | Configurable model stored as data; Alembic only developer-controlled platform releases |
| Editable surface | Content/model/structure/composition/theme/responsive values, never executable implementation |
| Preview | Same code/projection as public rendering; stable snapshot for review |
| Runtime/license | Fully self-hosted; no required hosted/account-bound/proprietary service; Agent-Site Apache-2.0 |

Allowed dependency-license families normally: Apache-2.0, MIT, BSD-2/3-Clause,
ISC, PostgreSQL License, PSF, or explicitly reviewed permissive licenses.
AGPL, SSPL, BUSL/BSL, Elastic License, Commons Clause, noncommercial,
source-available/field-of-use-restricted, commercial-only, or account-bound
runtime dependencies require explicit human-approved architecture revision.
Tailwind Plus/commercial templates are excluded. OCI OS/browser licenses require
SBOM/third-party inventory and normal institutional review.

Foundation boundary and qualification:

- Product code wraps public `agentcow.postgres` APIs only. Product services,
  user/site policy, tokens, UI, migrations, edge, Puck, browser, and media never
  move into the foundation. Never depend on private tables or undocumented SQL.
- Normal development/CI/release/deployment forbids Git/VCS URL/branch/tag/SHA,
  local path/editable checkout, mutable/unhashed direct wheel, or fallback for
  the foundation. `uv sync --frozen` must prove registry-only resolution.
- Before initial use/upgrade: verify exact PyPI version exists and is non-yanked;
  freeze wheel/sdist hashes; verify public APIs and Python/PostgreSQL matrix;
  rerun DB/privilege/concurrency/cancellation/conflict/promotion/packaging tests;
  verify MIT/dependencies/SBOM/attribution; reject mutable/unlocked sources.
- Relied-on APIs/semantics: `deploy_cow_functions`, `enable_cow_schema`,
  `harden_cow_schema`, `validate_cow_schema_privileges`,
  `asyncpg_cow_session`, `asyncpg_cow_reviewer`, operation/dependency/conflict
  inspection, deterministic ordering, first-touch row/schema baselines, whole
  and selective atomic commit/discard, `CowConflictError`, setup/runtime/reviewer
  role separation, pool/cancellation cleanup, FK-aware multi-table promotion.
- COW is a live-base logical overlay: base table becomes `<name>_base`, session
  mutations `<name>_changes`, app target a view. Creation copies no rows;
  untouched canonical rows can change; first touch captures the baseline;
  promotion locks/checks touched rows/schema; unrelated canonical changes can
  survive. Never call an active workspace a frozen backup. Stable approval
  begins only with the immutable review snapshot.
- PostgreSQL custom settings are context, not credentials. Only trusted server
  code selects session UUID; database credentials never leave services;
  external callers never access `CowSession.native` or arbitrary SQL.

## 3. Non-negotiable invariants

1. Agent API has no setup owner, reviewer, direct base/change-table, schema
   `CREATE`, control-plane workspace/capability/publication authority.
2. Trusted server derives site, workspace/session UUID, and operation UUID;
   none may be selected by untrusted header/query/path/body/MCP input.
3. No agent-authenticated route can accept/publish/discard/freeze a workspace.
4. One capability maps to exactly one deployment, site, workspace UUID,
   delegator, immutable effective scope/resource/quota set, and expiry.
5. All online editorial writes, including human forms and Puck, execute through
   `asyncpg_cow_session`; unsafe canonical write-through-view is disabled.
6. Accepted operation set, canonical changes, site revision, audit, and terminal
   state commit or roll back atomically.
7. Public product promotion always uses `conflict_policy="error"`; overwrite
   compatibility is never exposed.
8. Media bytes are immutable/content-addressed; edits change references.
9. Freeze revokes capability, obtains an application-owned exclusive workspace
   lock after all shared mutation locks drain, then materializes an immutable
   digested review snapshot. Approval names that snapshot, never a live overlay.
10. Editorial authority never includes source/templates/code, arbitrary CSS/JS,
    dependencies, physical schema, edge/container config, identity, or secrets.
11. Every operation receives trusted `SiteContext`; IDs/routes/hosts/body values
    cannot cross sites; parent/child constraints and negative tests enforce it.
12. Content model changes are workspace data; they never invoke Alembic.
13. Field/component/query implementations are trusted versioned code. Users and
    agents instantiate/configure only allowlisted primitives and components.
14. Browser tools observe only bound preview and approved source origins;
    worker has no DB/content-write/canonical/reviewer/identity/infrastructure
    authority.
15. Screenshot/accessibility/diagnostic/sweep success is evidence only, never
    publication authority.
16. Puck and agent operations converge on one versioned product-owned normalized
    composition; all render contexts share trusted React implementations.
17. Multi-site support makes no hostile-tenancy guarantee.

When convenience conflicts with any boundary, the boundary wins.

## 4. Actors, processes, and authority

Actors: Visitor reads a trusted host/path-selected canonical site; Platform
Administrator initializes/creates sites/configures identity/quotas/owners; Site
Owner governs one site; human architect/designer/editor edits authorized human
workspaces; delegator creates bounded agent workspace; separately authorized
reviewer/publisher freezes/reviews/accepts/selectively accepts/discards; Reviewer
or Viewer may inspect/comment without implicit publish; external agent uses only
semantic REST/MCP plus capability; system administrator operates/backups/
upgrades; promotion worker holds reviewer authority; scheduler claims lifecycle/
browser/validation jobs but never publishes; browser worker observes previews/
approved sources without DB/publication; import tool writes only Level 4
workspace data.

Processes may share code/image but must use separate commands and credentials:

| Process | Exposure / authority / responsibility |
|---|---|
| NGINX OSS | Sole externally bound demo service (`8080`; production `80/443`); TLS/routing/limits/compression/logging/load balancing; no product secrets except TLS/config and no auth/session/content/publish semantics |
| Web | Via edge; no direct DB-write authority; public SSR, admin, Puck, preview/review shell |
| Control API | Via edge; control-schema only; human auth, installation/sites/domains/users/memberships/roles, workspace/capability lifecycle, review requests |
| Editor API | Via edge; editor COW runtime; authorized human semantic model/content/composition writes and audit |
| Agent API | Via edge; agent COW runtime; capability-authenticated semantic writes and browser-job requests |
| MCP adapter | Via edge; no DB; exact HTTP mapping to Agent API |
| Media service | Via edge; narrow media metadata/store authority; validated immutable upload and authorized reads |
| Render API | Internal; read-only canonical/workspace/snapshot projections and trusted route/site resolution |
| Browser worker | Internal; run-bound preview/source credential only; isolated Playwright contexts and private artifacts |
| Review worker | Internal/no listener; sole reviewer DB role; freeze/snapshot/validate/conflict/promote/discard/media/cache |
| Scheduler/job worker | Internal; queue/lifecycle authority; no reviewer credential |
| Media/artifact GC | Internal; reference inspection/delete authority only; never deletes referenced/retained objects |
| Bootstrap/migration | One-shot setup owner; Alembic, COW deploy/enable/harden/validate, grants, seed, setup token |
| PostgreSQL | Internal network only; durable control/content/audit/COW/jobs |

Web and MCP have no DB credentials. Browser worker has no DB, human cookie,
agent capability, reviewer credential, repository/host mount, Docker socket, or
unrestricted internal route. Setup owner is absent from every long-running
service. Agent/editor runtime credentials are distinct; review worker alone has
reviewer credentials. NGINX is the sole default published process.

Code ownership vocabulary: Agent-State may know principal/site/workspace/
capability/scope/operation/resource/review snapshot/promotion/conflict/expiry/
audit. Site modules may know content type/field/item/relation/page/composition/
component/navigation/theme/media/locale/redirect. Puck adapter knows Puck but
owns no persistence/auth/publication. Browser worker knows approved routes/
origins but no DB/publication. Foundation knows no product concept.

Repository target is the source architecture's monorepo: root governance,
Compose/locks/config; `apps/web`; backend and browser-worker services; shared
composition/component/content-model/scope/browser-contract/API packages;
OpenAPI/MCP/JSON Schema contracts; Alembic/bootstrap/seed migrations; NGINX/
Apache/PostgreSQL/Compose/production infra; demo/import/backup/restore/license/
browser-policy tools; E2E/contract/integration/security/concurrency/packaging/
recovery/license tests; threat/security/access/user/API/content/composition/
component/Puck/browser/promotion/operations/scaling/backup/license/comparison/
demo documentation. Preserve these ownership boundaries as implementation grows.

## 5. Human RBAC and agent delegation

Human roles are site-scoped governance assignments; one user may differ by
site. `control.site_membership`, not a global role field, is authoritative.
Publication is orthogonal to editing. Custom role design is follow-up; built-in
roles plus explicit overrides suffice for MVP.

| Human role | Delegation ceiling | Publish/default authority |
|---|---:|---|
| Platform Administrator | Policy-defined on assigned sites; installation authority never delegatable | Publication separately granted; installation/sites/identity/quotas/owner assignment |
| Site Owner | Level 4 | Yes by default; full one-site governance |
| Site Architect | Level 4 | Optional; models/global structure/design/import; no user management unless separate |
| Site Designer | Level 3 | Optional; composition/variants/responsive/theme |
| Site Editor | Level 2 | Optional; pages/routes/navigation/redirects/existing collections |
| Content Editor | Level 1 | Optional; existing item values/translations/media/component content props |
| Reviewer | None by default | Publish only if separate; read preview/diff/validation/audit/comment |
| Viewer | None | Read-only admin |

Effective agent scopes = requested preset ∩ delegator's delegatable site scopes
∩ site policy ∩ resource constraints ∩ system safety ceiling. Persist result
immutably on workspace/capability.

Preset behavior:

- **L1 Content Editor:** read site/model/items/views/pages/composition/navigation/
  media/theme/catalog; create/write/delete item values; translations; bounded
  media and metadata/reference deletion; SEO; existing component content props;
  inspect own preview. Cannot create/delete/move normal pages, routes/navigation,
  models/fields, structure, theme, header/footer.
- **L2 Site Editor = L1 + information architecture:** create/archive/restore/
  delete/move pages; routes/redirects/navigation; collection views over existing
  types; add/remove/move approved structural components; relationships. Cannot
  define fields/types, broad design, or global design.
- **L3 Site Designer = L1–2 + composition/design:** catalog component types/
  variants; columns/grids/heroes/galleries/accordions/cards/lists; page layout;
  reusable allowed compositions; bounded local/site tokens and responsive props;
  quota-controlled sweeps. Cannot models/fields, global header/footer
  architecture, code, or server behavior.
- **L4 Site Architect = L1–3 + whole structured site:** create/change/delete
  content types/fields/relations/views; declarative mappings; global theme;
  approved colors/typography/spacing/radii/widths/shadows; header/footer/global
  regions; locales; import manifests; replace hierarchy/navigation; reset all
  workspace site content; reconstruct approved source via confined tools. Still
  no executable primitives/operators/components/code, Alembic, arbitrary
  origins, identities, infrastructure, or publication.

Exact initial agent scope catalog:

```text
READ: site:read content-model:read content-item:read collection-view:read
page:read composition:read navigation:read translation:read media:read
theme:read redirect:read component-catalog:read preview:inspect validation:read

L1 WRITE: content-item:create content-item:write content-item:delete
translation:write media:upload media-metadata:write media-reference:delete
component-content-props:write seo:write preview:inspect

L2 WRITE: page:create page:write page:delete page:restore page:move route:write
redirect:create redirect:write redirect:delete navigation:create
navigation:write navigation:delete collection-view:create collection-view:write
collection-view:delete component-structure:create component-structure:delete
component-structure:move relationship:write

L3 WRITE: composition:write component-props:write component-variant:write
layout:write responsive-design:write page-style:write theme-tokens:write
preview:responsive-sweep

L4 WRITE: content-model:create content-model:write content-model:delete
field-definition:create field-definition:write field-definition:delete
content-model:mapping site-structure:write global-region:create
global-region:write global-region:delete header-footer:write theme-global:write
locale:configure site-import:validate site-import:apply source:inspect
site-reset:workspace
```

Never present in an agent capability: `site:create/archive/delete`,
`site-domain:manage`, `workspace:create/freeze/accept/accept-selective/discard`,
`capability:create/revoke`, `site:publish`, `membership:manage`, `role:manage`,
`identity:configure`, `installation:manage`, `schema:migrate`,
`component-code:install`, `server:configure`, `secret:read`, `audit:delete`.
Human-only scope catalog: the site/workspace/capability/publication/membership/
role scopes above plus `workspace:read-all`, `site-policy:manage`,
`audit:read`, `audit:export`; possession still requires human RBAC/policy.
System-only: `schema:migrate`, `cow:deploy/harden/validate`, `job:claim`,
`browser:internal-preview/internal-source`, `media:gc`, `artifact:gc`,
`backup:run`, `restore:run`.

Any preset may narrow locales, page subtree/route prefix, content types, media
MIME/bytes, deletes, operations, records, duration, browser runs/screenshots/
routes/targets/bytes/concurrency, and approved source origin/subdomains.
`preview:inspect` can be any level; full sweep is costly L3/4; `source:inspect`
is L4 and inert without a human-approved source origin.

## 6. Capability, authorization, idempotency, quotas

Opaque token: `sas2_<public-id>_<secret>`, with random lookup ID and at least
256-bit random secret; no cleartext site/session/scope/expiry. Store public ID,
fast constant-time digest (optional HMAC pepper), site/workspace/delegator,
effective scopes/constraints/approved origins/browser limits, creation/expiry/
revocation/last-use, and request/upload/browser/screenshot budgets. Display
plaintext once with API/MCP URLs, expiry, preset/scope summary, preview,
approved origin/targets, and suggested instructions; never persist/log it.

Authentication: parse version/public ID; controlled lookup; compare digest;
verify unrevoked/unexpired, workspace `ACTIVE`, valid delegator/site, budget;
produce immutable trusted auth context; enter COW with server-resolved UUID;
reassert active state inside mutation transaction; perform semantic operation.
Revocation rejects new requests immediately; already-open transactions may
finish before freeze's exclusive lock.

Authorization composes route scope, resource constraint, trusted site-bound
lookup/cross-site denial, browser origin/target/quota, and domain/model/query/
composition invariants. Every mutating route explicitly declares scopes; CI
enumerates handlers and fails omissions. Policy chain: authenticated identity →
trusted site/domain → membership/role → delegation ceiling → workspace scopes →
capability scopes → route → resource → domain invariant.

Every mutation/model transform/browser-job request requires `Idempotency-Key`.
Map `(capability_id,key)` to server-owned operation UUID or stable browser run,
request digest, and stored result. Same digest returns result; different payload
returns `409 IDEMPOTENCY_MISMATCH`. Client key is never PostgreSQL operation
UUID. Optional `X-Agent-Task-Group` is audit metadata only. Bounded batches are
single-transaction/all-or-nothing with one operation UUID; long browser jobs are
asynchronous. Selective acceptance selects operation UUIDs and dependency
closure, never arbitrary audit events.

Suggested default one-hour quotas: 2,000 requests; 250 mutations; 100 MB upload;
500 created/100 deleted records; 10 concurrent requests; 20 browser runs; 50
screenshots; 10 routes/sweep. Site policy/preset configures limits; large Level
4 import receives explicit larger limits, never unlimited. Agent capability is
never placed in preview URL/cookie/local/session storage/screenshot/trace; Agent
API exchanges authorized browser request for run-bound internal credential.

## 7. Website data, composition, design, Puck, rendering

Editable layers: (1) content—items/values/relations/translations/media; (2)
information architecture—types/fields/views/pages/routes/navigation/redirects;
(3) normalized component instances/slots/order/bindings/variants; (4) global
theme/header/footer/regions/typography/palette. Layer 5—React/Puck adapter,
field/query implementations, backend/CSS, physical DB schema, packages/plugins,
edge/containers/browser policy/auth—is trusted code and never editorial.

Fixed generic product entities: Site, Locale, ContentType, FieldDefinition,
ContentItem, ContentItemTranslation, ItemRelation, CollectionView, Page,
PageComposition, ComponentInstance, Navigation/Item, MediaAsset, Redirect,
Theme, ProposedSideEffect. `News`, `Event`, `Person`, `Project`, `Publication`,
`Course`, etc. are rows, not physical tables. Every editorial object has UUID,
immutable site association, timestamps, row version, workspace/audit provenance.

Initial code-defined field primitives:

```text
short_text long_text rich_text integer decimal boolean date datetime url email
enum media document reference multi_reference location object repeatable_object
```

Each defines storage, JSON Schema, editor, validation, localization, indexing/
query support, rendering, agent discovery. L4 configures/instantiates only.

Hybrid model:

- `content_type`: site, stable key/labels/slug pattern/status/settings,
  monotonically increasing definition version.
- `field_definition`: type/site, key/label/primitive, required/localized/
  cardinality/position, bounded validation/UI options, version.
- `content_item`: site/type/slug/status/type-definition version, nonlocalized
  JSONB values, timestamps/row version; translations live per locale.
- Referential fields normalize into `item_relation` with source/field/target/
  position/bounded metadata and enforce site/type integrity.
- `collection_view` binds a type to bounded filter/sort/projection/pagination
  DSL; never raw SQL. Operators/depth/fields/results/complexity/cost/time/index
  policy are allowlisted.

Definition change increments version and reports affected items as compatible,
defaultable, transformable, or invalid. Optional-field addition needs no
transform. Renames and compatible changes use explicit declarative mappings;
arbitrary transformation code is forbidden. Generated validators run on human
forms, agent requests, preview projection, freeze, and promotion. “Add News” is
one workspace's data: type/fields, view, listing/detail composition/pages,
navigation, items, validation and responsive inspection—never Alembic/table DDL.

Page hierarchy/route/locale validation requires per-site+locale uniqueness, no
cycle, bounded depth, reserved paths, no redirect loop, canonical-locale rules.
Route changes may propose redirect only with `redirect:write`.

Normalized composition—not an opaque/unversioned Puck blob—is authoritative.
Contract `site-composition/v1` contains page/root and stable component nodes
with ID, trusted type/schema version, parent, slot, order key, validated props.
Logical storage is `page`, `page_composition`, `component_instance`, optionally
normalized prop references. Render cache is not authoritative. Stable IDs and
semantic create/update/move/delete enable audit, conflict boundaries, Puck
round-trip, and selective dependency analysis. Clients state semantic relative
move intent; server assigns/rebalances order and checks depth/slot/count/cycles.
Deletion is a workspace tombstone/operation; canonical hard delete occurs only
through promotion where policy permits; audit and retained media are not hard
deleted by content APIs.

Generic data-driven components bind validated collection views to declared
fields. Server verifies same-site view/type/fields/projection/component schema,
bindings, and query policy; input never contains SQL.

Initial trusted catalog minimum:

| Category | Components |
|---|---|
| Layout | `Section`, `Container`, `Columns`, `Grid`, `Stack`, bounded `Spacer` |
| Basic | `Heading`, `RichText`, `Image`, `Gallery`, `VideoEmbed`, `Quote`, `Button`, `CallToAction` |
| Data | `CollectionList`, `CollectionGrid`, `CollectionDetail`, `CollectionSearch`, `CollectionFilter`, `RelatedItems` |
| Institutional | `Hero`, `Statistics`, `Timeline`, `LogoGrid`, `DocumentList`, `ContactBlock`, `MapBlock`, `FAQ` |
| Global | `Header`, `Footer`, `Breadcrumbs`, `LanguageSwitcher` |

Domain labels such as NewsList normally compile to generic collection
components. Each catalog entry defines type/schema version, variants, settings
and localized-content JSON Schemas, trusted renderer, Puck mapping,
accessibility, deterministic migration, allowed slots/children/depth,
responsive props, and optional data binding. Editorial callers may select
approved variants/tokens/columns/aspect/alignment/spacing; reject raw CSS/style/
JS/event handlers/arbitrary iframe/template/package/source/executable prop or
query expression.

Theme is bounded structured palette, locally packaged approved typography,
layout width/spacing/grid gap, shape radius/shadow, and header/footer variants.
Responsive props use stable `desktop`/`tablet`/`mobile` token maps; callers
cannot define CSS, breakpoints, remote fonts, or Playwright devices. Promotion
checks meaningful-image alt text, headings, link text, token contrast,
keyboard-safe components, autoplay, language, and labels; policy classifies
hard errors versus human-acknowledged warnings.

Puck consumes generated trusted catalog config. `PuckCompositionAdapter` maps
stable normalized IDs/slots/props/versions both ways. Puck permissions are UX;
crafted Editor API calls receive the same server authorization and validation.
Puck `onPublish` means **Save workspace/draft**, never promotion. Upgrades need
adapter round-trip/permission/persistence/E2E plus deterministic migration or
backward reader.

Every workspace records component-catalog, renderer, composition-schema,
content-model, and Puck-adapter versions. Incompatible deployments block review
until migration/recreation. Public, active preview, and immutable review use
the same requested route, component tree, CSS, and content projection; only
render context differs. Preview can never be an approximation of production.

Trusted hostname/path mapping selects canonical site. Default preview path is
`/preview/<workspace-id>/<site-route>`; optional production subdomain is
`<workspace-id>.preview.example.si`. Human preview authorization is separate
from capability and checks site membership/workspace access. Browser gets a
short-lived site/workspace/run/expiry-bound internal credential, no agent token
or human cookie. Never put token in URL/storage/source/analytics/HTML/referrer.

Public cache key uses canonical site revision. Active-preview key includes
workspace/watermark/route/locale/catalog/composition/content-model versions.
Review renders `review_snapshot_id`, not overlay. Preview defaults
`Cache-Control: private, no-store`, `X-Robots-Tag: noindex, nofollow, noarchive`,
no preview sitemap. Public immutable assets cache long; promotion increments
site revision and emits cache invalidation.

Responsive contract: public site, login/dashboard/site selection, capability
create/revoke, preview/review/accept/discard, and common content forms are
desktop/tablet/phone required. Full Puck is desktop/tablet required and phone
best-effort only as E2E proves. Global theme/architecture editing is not a
narrow-phone MVP requirement; critical governance remains phone-usable.

## 8. Workspace lifecycle, freeze, review, promotion

Workspace types: `AGENT`, `HUMAN`, `IMPORT`, rare trusted `SYSTEM`; UUID is COW
session ID and immutable `site_id`; all capabilities/runs/artifacts/events/
snapshots/jobs inherit association.

Lifecycle:

```text
CREATING -> ACTIVE | FAILED
ACTIVE -> ACTIVE | REVOKED | EXPIRED | FREEZING
REVOKED|EXPIRED -> FREEZING -> REVIEW
REVIEW -> ACCEPT_QUEUED | SELECTIVE_ACCEPT_QUEUED | DISCARD_QUEUED
ACCEPT_* -> PROMOTING -> ACCEPTED | CONFLICTED | REVIEW
DISCARD_QUEUED -> DISCARDING -> DISCARDED
CONFLICTED -> REVIEW; REVIEW -> DISCARDED; accepted/discarded terminal
```

Only ACTIVE accepts writes. Revoked/expired reject. Browser jobs require policy;
source additionally origin+scope. FREEZING denies new requests and drains via
lock. REVIEW is read-only. Only human control action queues accept/selective
accept. Terminal requests idempotent; terminal history immutable; retention is
policy-defined.

Active overlay follows current canonical rows not touched by workspace. Display
base/current site revisions and warn on concurrent canonical change. During
active work coarse revision drift is advisory; first-touch row conflicts are
authoritative. Freeze records current canonical revision; MVP requires it
unchanged until acceptance, else re-review.

Application lock contract uses transaction-scoped PostgreSQL advisory locks in
a dedicated namespace: every mutation obtains
`control.lock_workspace_shared(uuid)` then rechecks state; freeze marks
`FREEZING`, obtains `control.lock_workspace_exclusive(uuid)`, waits existing
transactions, denies new ones, then snapshots. Foundation H07/promotion locks
remain authoritative; product lock defines lifecycle/snapshot boundary.

Immutable snapshot includes site profile/theme/locales; content types/fields/
versions; items/translations/relations; collection query specs; pages/normalized
trees; navigation/redirects/media references; operation set/dependency graph;
validation; completed selected browser evidence/private artifact references;
catalog/composition/renderer/content-model/Puck versions; canonical revision;
watermark and digest. Later canonical drift requires new snapshot, never mutation
of old snapshot.

Review UI shows rendered site; model/field/mapping, item/relation, resource,
composition/theme/navigation/responsive/media summaries; semantic timeline and
resource diff; screenshots/diagnostics/accessibility/sweep/Puck link; warnings/
deterministic validation; conflicts; permission/quota and agent/source/browser
metadata; accept/selective/discard. Active artifacts are not approval. Selective
preview may render causally closed operations with foundation visibility filter;
whole session is default.

L4/high-delete acceptance should require recent auth, explicit summary
acknowledgement, typed confirmation for site-wide replacement, and optional
second publisher by policy. These supplement isolation; visual green never
substitutes.

Full acceptance, in one `asyncpg_cow_reviewer` transaction:

1. claim/mark job; require workspace REVIEW; obtain exclusive product lock;
2. lock canonical site-revision row and require equality to approved snapshot;
3. verify snapshot digest, operation/dependency closure, audit, renderer/catalog/
   composition/Puck/content-model versions;
4. rerun model/item/mapping/relation/query/component-binding/route/locale/
   accessibility/site/media validation under trusted site/snapshot context;
5. inspect foundation conflicts, lock session/dirty tables, and commit with
   deferred FKs and `conflict_policy="error"`;
6. increment canonical revision, append promotion audit, mark workspace/job
   accepted/completed, and emit cache outbox; commit all or roll back all;
7. finalize media idempotently; harmless precommit public orphan is GC'd.

Selective acceptance uses causally closed operation IDs and foundation
`commit_operations`; UI explains dependent operations and rebase semantics.
Discard atomically discards pending operations, marks DISCARDED, revokes tokens,
schedules staging/artifact cleanup, retains audit.

If canonical revision differs: stop before mutation with
`409 SITE_REVISION_CHANGED`, return to re-review/new snapshot. Repeat foundation
row/schema conflict checks under lock. `CowConflictError` rolls back everything,
leaves canonical/pending state intact, returns structured
`BASE_ROW_CHANGED|BASE_ROW_DELETED|BASE_ROW_CREATED|BASE_SCHEMA_CHANGED`, and
sets CONFLICTED/REVIEW. Validation failure also changes no canonical row and
keeps review/correction path. Never expose overwrite. MVP remedies are discard,
fresh/reapplied workspace, manual workspace correction, or selective
non-conflicting closure; semantic rebase/field merge/repair session are later.
Acceptance never replaces a DB/schema/site copy.

FKs for page/navigation/component hierarchies and cyclic relationships are
`DEFERRABLE INITIALLY IMMEDIATE`; promotion uses deferred constraints and
transaction-end integrity. Schema cycles/promotion require integration tests.

Physical platform migrations: stop new workspaces; freeze/accept/discard active;
require no pending COW; Alembic as owner; upgrade/deploy foundation; enable new
content tables; reharden/revalidate privileges; smoke test; resume. Incompatible
upgrade with pending state fails rather than inventing baselines.

## 9. Backend/domain service contracts

Shared Python package exposes separate entry points for control/editor/agent/
render/MCP/media/review/scheduler/GC/bootstrap. Shared code owns typed domain,
RBAC/delegation, model/query/item/relation/composition/component/theme/media
validation, shared TS contracts, DB adapters, audit, digest, errors, OpenAPI.
Each service owns handlers/credentials.

- **Control:** human auth; one-time setup/OIDC; sites/domains/memberships/roles/
  delegation; workspaces/capabilities/scopes/revoke/freeze; accept/discard jobs;
  status/changes/conflicts/audit/browser evidence. No content DML/reviewer cred.
- **Editor:** human cookie+CSRF; membership/workspace/edit scope; server-derived
  session; shared commands; Puck/forms to normalized model; COW+same-tx HUMAN
  audit; no canonical direct write.
- **Agent:** opaque capability→trusted site/workspace; state/expiry/scope/quota/
  filters; server operation IDs; semantic model/item/page/component/navigation/
  theme/media-reference writes through COW; same-tx audit; policy-checked browser
  jobs; stable errors. Reject SQL/DDL/JS/arbitrary URL/DB identity.
- **Render:** internal read-only canonical/no COW, authorized active workspace,
  optional selected operations, or immutable snapshot; trusted route/site,
  bounded collections, content model, composition/theme/navigation/redirect/
  locale/media projection.
- **MCP:** same capability; curated tools via internal HTTP to Agent API only;
  no DB/browser direct auth/business logic/publication; REST/OpenAPI is truth.
- **Media:** bounded streaming hash/MIME validation; immutable store; authorized
  metadata/reference workflow; public/staging/private reads; ownership; no
  workspace artifact made public automatically.
- **Browser:** fresh context/run; service preview credential; screenshots,
  accessibility/DOM, console/failed-request/link/media/overflow/heading checks,
  responsive sweep; approved-origin source only; private artifacts; destroy
  context/credential. No DB/write/reviewer/host/Docker/unrestricted network.
- **Review:** claim jobs; freeze/snapshot; inspect operations/dependencies/
  conflicts/audit; deterministic validation; advisory browser evidence;
  atomic promotion/discard/status/revision/audit/media/cache. No listener.
- **Scheduler:** request-time expiry remains authoritative; enqueue expiry/
  cleanup/validation/browser/retry; detect stale/stuck; never promote/no reviewer.
- **GC:** remove expired unreferenced staging/temp/public/private artifacts only
  after retention; never canonical reference or retained review evidence.

## 10. PostgreSQL architecture and logical data model

One DB, schemas: `control` (identity/session/capability/jobs/policy), `content`
(all editable platform+configurable site data; only COW-enabled schema), `audit`
(append-only semantic/security/promotion/job/browser), `agentcow` (foundation),
and Alembic metadata outside protected content. This permits capability assert,
quota, COW mutation, and audit in one runtime transaction, and promotion/state/
audit in one reviewer transaction—no distributed coordinator.

Every site-owned control/content/workspace/media/browser/audit object has
immutable `site_id` or equivalent. Parent/child/site FKs, composite uniqueness,
and repository methods requiring trusted `SiteContext` prevent mismatch. Do not
claim PostgreSQL RLS until agent-cow compatibility and invariants are implemented
and tested.

Fixed COW content tables: `locale`, `page`, `page_composition`,
`component_instance`, `navigation`, `navigation_item`, `redirect`, `theme`,
`media_asset`, `proposed_side_effect`. Configurable COW tables: `content_type`,
`field_definition`, `content_item`, `content_item_translation`, `item_relation`,
`collection_view`. Control installation/sites/domains/users/roles/memberships/
workspaces/capabilities/idempotency/snapshots/jobs/browser records are not COW.

Database roles:

| Role | Allowed | Explicitly denied |
|---|---|---|
| `slaif_owner` | One-shot ownership, migrations, COW deploy/enable/harden | Long-running requests |
| `slaif_control` | Narrow control tables/functions | Content DML, reviewer/setup |
| `slaif_editor_runtime` | Authorized human COW view CRUD + audit function | Base/change/canonical/reviewer/schema create |
| `slaif_agent_runtime` | Capability assert + COW view CRUD + audit function | Base/change/canonical/reviewer/schema create |
| `slaif_public_reader` | Canonical view SELECT without session | DML/internal tables |
| `slaif_preview_reader` | Trusted session view SELECT | DML/internal tables |
| `slaif_reviewer` | Controlled inspect/commit/discard/terminal/audit | Runtime view DML, setup, arbitrary control update |
| `slaif_scheduler` | Expiry/job enqueue/claim as needed | Content read/write/promotion |
| `slaif_gc` | Reference projection and GC records | Content DML/promotion |

`PUBLIC` gets no avoidable schema/function authority; bootstrap revokes defaults.
Browser/Web/MCP have no DB role. Media has only narrow functions. `control`
owns narrowly granted SECURITY DEFINER functions for capability/state/audit/
terminal transitions and product workspace locks. Runtime receives only required
`EXECUTE`.

Bootstrap sequence after Alembic: deploy COW functions; enable `content`
excluding Alembic metadata, allowing deferred FKs and forbidding unsafe canonical
writes; harden for editor/agent runtime and reviewer; run privilege validation
and require safe; then apply and independently validate read/control/scheduler
grants. First trusted content table must not run without validated hardening.

Logical control model (constraints/FKs/site confinement required):

```text
installation_state(id singleton PK, initialized_at?, setup_token_digest?,
  setup_token_expires_at?, configuration_version)
site(id UUID PK, key UNIQUE, name, status, canonical_revision,
  component_catalog_version, content_model_revision, default_locale, timestamps)
site_domain(id, site_id, hostname, path_prefix?, is_primary, created_at,
  UNIQUE(hostname,path_prefix))
user_account(id, identity_kind LOCAL|OIDC, local_username?, password_hash?,
  oidc_issuer?, oidc_subject?, email?, display_name, status, created/last_login,
  UNIQUE(oidc_issuer,oidc_subject)); local uniqueness separate; email mutable
role / permission / role_permission = inspectable built-in catalog;
  code route/scope declarations remain enforcement truth
site_membership(site_id,user_id,role_key,delegation_ceiling,
  permission_overrides,status,timestamps, PK(site_id,user_id))
workspace(id UUID=COW session PK, site_id, created_by, actor_type, title,
  task_description, approved_source_origins, delegation_preset,
  effective_scopes, resource_constraints, browser_limits, status,
  base_site_revision, operation_watermark, catalog/composition/Puck/content-model
  versions, created/expires/frozen/accepted/discarded timestamps, version)
review_snapshot(id,site_id,workspace_id,snapshot_digest,
  canonical_site_revision,operation_ids,operation_watermark,catalog/renderer/
  composition/Puck/content-model versions,normalized_site,validation_report,
  browser_evidence,created_at,created_by_job); immutable
capability(id,site_id,workspace_id,public_id UNIQUE,secret_digest,delegator_id,
  scopes,constraints,origins,browser_limits,timestamps,request/upload/browser/
  screenshot limits+counts)
idempotency_record(capability_id,key,request_digest,operation_id,status,body,
  created_at, PK(capability_id,key))
browser_run(id,site_id,workspace_id,requester capability/user?,type PREVIEW|SOURCE,
  status,targets,routes,origins,quota,summary,timestamps,last_error?)
browser_artifact(id,site_id,workspace_id,run_id,type,digest,metadata,created,expires)
job(id,type,site_id,workspace_id,requested_by,idempotency_key UNIQUE,payload,state,
  attempts,available/locked/created/completed timestamps,locked_by,last_error)
```

Logical audit model:

```text
semantic_event(event_id,sequence,time,site/workspace/capability/delegator/
 operation/request/trace IDs,actor,method,route,resource/action,row versions,
 before/after digests,redactable patch,scope,status,previous-event digest)
promotion_event(id,site,workspace,job,requester,action,selected operations,
 foundation result,site revisions before/after,time,hash-chain digests)
security_event(login/token issuance/revoke/denial/expiry/suspicious summaries)
job_event / browser_event(explicit run/target/route/origin/summary/artifact refs)
```

Runtime cannot update/delete audit. Mutation+semantic event share one
transaction; mutation without audit fails. Pre-promotion cross-check: every
selected foundation operation has semantic event unless explicitly system;
every event operation exists; ordering and final digests align; selection is
causally closed. Browser-only evidence has no fake foundation operation. Never
record capability/internal preview/artifact token or unrestricted trace.
Public content patches may be full; sensitive fields redact/encrypt/hash by
policy. DB owner compromise remains outside cryptographic guarantee.

Logical COW content model (all UUID PK, timestamps/row version/provenance as
applicable; cross-site child/reference prevented by composite FK/trigger):

```text
content_type(id,site_id,key,labels,slug_pattern,status,definition_version,
 settings,timestamps, UNIQUE(site_id,key))
field_definition(id,site_id,type_id,key,label,field_type,required,localized,
 cardinality,position,validation,ui_options,definition_version,timestamps,
 UNIQUE(type_id,key))
content_item(id,site_id,type_id,slug,status,type_definition_version,values JSONB,
 timestamps,row_version)
content_item_translation(id,site_id,item_id,locale,localized_values JSONB,
 timestamps,row_version, UNIQUE(item_id,locale))
item_relation(id,site_id,source_item_id,field_definition_id,target_item_id,
 position,metadata)
collection_view(id,site_id,key,type_id,filter_spec,sort_spec,projection_spec,
 pagination_spec,timestamps)
page / page_composition
component_instance(id,site_id,page_id,parent_component_id,slot_key,
 component_type_key,component_schema_version,order_key,props JSONB,
 timestamps,row_version)
component_prop_reference? / navigation / navigation_item / locale / media_asset /
redirect / theme / proposed_side_effect
```

## 11. Public REST/OpenAPI and MCP contracts

All public APIs use `/v1`, domain concepts, UUIDs, typed schemas, stable error
codes, idempotency for mutations, optional ETags/row versions, scope/resource
checks before DB, and repeated promotion validation. Generated OpenAPI comes
from the same handlers.

Control API representative contract:

```text
POST /api/control/v1/login
POST|GET /api/control/v1/sites
GET|PATCH /api/control/v1/sites/{site_id}
GET|POST /api/control/v1/sites/{site_id}/memberships
PATCH|DELETE /api/control/v1/sites/{site_id}/memberships/{user_id}
GET /api/control/v1/roles
GET /api/control/v1/permissions
POST|GET /api/control/v1/sites/{site_id}/workspaces
GET /api/control/v1/workspaces/{id}
POST /api/control/v1/workspaces/{id}/capabilities
POST /api/control/v1/capabilities/{id}/revoke
POST /api/control/v1/workspaces/{id}/freeze
GET /api/control/v1/workspaces/{id}/changes|operations|conflicts|browser-runs
POST /api/control/v1/workspaces/{id}/accept|accept-operations|discard
GET /api/control/v1/jobs/{id}
GET /api/control/v1/audit
```

Editor API mirrors domain CRUD under an authorized application workspace ID:
pages and `:move`/`:restore`; content types/fields/items/views; page composition
and component add/update/move/delete; navigation/redirects; theme/global regions.
Path workspace ID is never trusted DB context; server resolves authorized UUID.

Agent discovery:

```text
GET /api/agent/v1/session|permissions|site-model|component-catalog|theme-schema|
validation-rules
GET /api/agent/v1/content-model/field-types
```

Agent semantic API:

```text
GET|POST /api/agent/v1/content-types
GET|PATCH|DELETE /api/agent/v1/content-types/{type_id}
POST /api/agent/v1/content-types/{type_id}/fields
PATCH|DELETE /api/agent/v1/fields/{field_id}
GET|POST /api/agent/v1/content-types/{type_id}/items
GET|PATCH|DELETE /api/agent/v1/content-items/{item_id}
GET|POST|PATCH|DELETE /api/agent/v1/collection-views/...

GET|POST /api/agent/v1/pages
GET|PATCH|DELETE /api/agent/v1/pages/{id}
POST /api/agent/v1/pages/{id}:move|:restore
GET /api/agent/v1/pages/{id}/composition
POST /api/agent/v1/pages/{id}/components
PATCH|DELETE /api/agent/v1/components/{id}
POST /api/agent/v1/components/{id}/move
GET /api/agent/v1/navigation
PUT /api/agent/v1/navigation/{id}
POST /api/agent/v1/navigation/{id}/items
PATCH|DELETE /api/agent/v1/navigation-items/{id}
GET|POST|PATCH|DELETE /api/agent/v1/redirects/...
GET /api/agent/v1/design-system|component-catalog|theme|global-regions
PATCH /api/agent/v1/theme|global-regions/{id}
POST|GET /api/agent/v1/media
GET|PATCH|DELETE /api/agent/v1/media/{id}
POST /api/agent/v1/import-manifests:validate|:apply
POST /api/agent/v1/batches
```

No physical `/news`/`events`/`people` APIs. Every call validates site/workspace,
state/scope/constraints/quota/idempotency, model/catalog/schema/row versions,
component/binding/structure rules.

External browser operations expose only stable product actions for preview
screenshot/snapshot/console/network/link/media/overflow/heading/responsive
sweep/artifacts and authorized source open/snapshot/screenshot/links/metadata/
asset. Caller supplies normalized bound path/target or source-relative request,
never workspace/origin/internal credential/arbitrary URL. Raw internal API only:

```text
POST /internal/browser/v1/preview-runs
POST /internal/browser/v1/source-runs
GET  /internal/browser/v1/runs/{run_id}
```

Never expose raw Playwright commands, `page.evaluate`, JS, arbitrary navigation,
or `file://`.

Batch limits body/operations, one transaction/operation UUID/all-or-nothing,
and contains semantic operations not arbitrary URLs. Browser/model jobs have
bounded idempotent asynchronous inputs.

Stable error envelope contains `error.code`, safe message, request ID, optional
operation ID/details. Status semantics: 400 malformed; 401 invalid/expired/
revoked capability; 403 scope/resource denial; 404 invisible in bound site/
workspace; 409 frozen/idempotency/resource/promotion conflict; 413 too large;
422 domain/schema validation; 429 quota/rate; 503 temporary worker/DB/browser.

Agent API has no publish/accept/discard/create-workspace/mint/manage-users/
roles/run-sql/run-alembic/run-shell/install-component/register-primitive/
evaluate-JS/open-arbitrary-URL/change-server endpoint.

MCP tool families exactly delegate to Agent API HTTP:

```text
site.describe/list_locales/get_structure
model.list_field_types/list_content_types/create_content_type/add_field/
 update_field/validate
content.list_items/create_item/update_item/delete_item
page.create/move/delete
component.add/update/move/delete
design.get_catalog/get_theme/update_theme; media.upload
preview.open/screenshot/snapshot/console_errors/network_failures/check_links/
 check_media/check_overflow/check_heading_structure/run_responsive_sweep/
 list_artifacts
source.open/snapshot/screenshot/extract_links/extract_metadata/fetch_asset
```

MCP cannot override site/workspace/origin, access DB/browser directly, create
different auth semantics, or publish. Visual result is MCP image when supported
or private artifact ID + short-lived authenticated URL/structured summary,
never public media. Model/client confirmation may exist but safety never depends
on it. Capability is vendor-neutral and REST remains available.

## 12. Media, browser, import, and side effects

`MediaStore` supports immutable put/open/exists/unreferenced-delete/authenticated
read. Implementations: `LocalVolumeMediaStore` default demo/single-host;
`SharedFilesystemMediaStore` multi-node; later approved permissive self-hosted
object store. Storage namespaces: bounded temp upload; workspace staging by
workspace/digest; private browser artifacts by workspace/run/digest; public by
digest prefix. DB stores digest, never absolute path.

Upload: bounded streaming temp + SHA-256; content MIME not filename; prohibit
types; dimensions/pages/decompression bounds; optional malware scan; atomic
rename into staging; COW MediaAsset reference; same-tx audit. SVG initially
disabled or sanitized. Preview-media read checks authorized human, visible
workspace reference, and workspace/public ownership; edge never exposes staging
or artifact directories directly.

Before DB promotion: enumerate selected references, verify staging, hard-link/
copy digest to public idempotently, then promote. Failed DB commit may leave only
harmless unreferenced public object for GC. Public URLs use digest/immutable
cache; edge proxies media unless explicit safe shared filesystem.

Delete changes/removes references. Public byte deletion waits for zero canonical
reference, historical-retention clearance, long GC window, and backup policy.
Private screenshot/trace/DOM/accessibility/report artifacts are immutable,
workspace/run/type/target/route/source/digest/expiry-recorded, never promoted as
site media, and available only to authorized human or short-lived requesting
capability result. GC never removes retained review/current authorized result.
Do not use foundation blob subsystem.

Level 4 reconstruction may inspect only human-approved source, discover
primitives/model/catalog/theme, build types/items/views/pages/composition/
navigation/media/theme/redirects, reset workspace, and iterate on own responsive
preview. Every write still uses semantic API. Optional importer emits neutral
bounded manifest in disposable container and never writes canonical content.

Source policy records origin/subdomain/max pages/bytes/redirects/downloads/time;
links cannot widen it; authenticated sources require separate human design.
Server-side browser/fetch must reject loopback, link-local, metadata, private
addresses by default; re-resolve DNS/recheck redirect targets; bound response/
MIME/time; require administrator allowlist for private institutional hosts; use
separate egress proxy/network with no DB/control/reviewer/Docker/host access;
fresh nonpersistent context; CPU/memory/time/page/screenshot/trace/download
quotas; never Agent API network identity. `source:inspect` alone is insufficient
without approved origin.

Stable visual targets: `desktop-chromium`, `desktop-firefox`,
`desktop-webkit`, `tablet`, `mobile-chromium`, `mobile-webkit`, mapped to pinned
Playwright descriptors. Product runtime may initially policy-limit subset, but
E2E defines all six. Sweep reports console/failed requests/broken links/missing
media/horizontal overflow/heading/accessibility plus private artifacts; quality
evidence never authorization.

Active workspaces propose, never execute, external side effects through COW
`ProposedSideEffect`; review/promotion creates canonical outbox; trusted
dispatcher executes after acceptance. MVP suppresses email/subscriber notices/
webhooks/search indexing; preview analytics off/tagged; sitemap/cache events only
after promotion. Source downloads remain private until explicitly validated and
ingested as workspace media. Never expose DNS/payment/invitation/email/arbitrary
webhook/package/shell tools.

## 13. Deployment, edge, configuration, startup, authentication

Reference Compose services: nginx, web, control-api, editor-api, agent-api,
render-api, mcp-adapter, media-service, browser-worker, review-worker, scheduler,
media-gc, bootstrap, PostgreSQL. Use health checks, health/completion
dependencies, named volumes, internal networks plus restricted browser network
and enforceable egress, explicit non-root users, read-only roots/dropped
capabilities where practical, release image digests. No DB host port. Profiles:
default complete demo/browser; e2e runner+fixtures; dev mounts/hot reload; backup
one-shot tools. Browser image is pinned/reproducible/license-scanned.

NGINX routes `/api/agent/`, `/api/editor/`, `/api/control/`, `/mcp/`, `/media/`,
and `/` to respective services; forwards trusted proxy/request ID data and
disables buffering where streaming/MCP/Next.js requires. It may do TLS, body/
rate limits, compression, caching, request IDs, load balance—never capability,
site, preview, content, auth, or publication semantics. Apache 2.4 adapter uses
standard OSS proxy/headers/rewrite/SSL/compression modules and exposes identical
application paths. Application policy must remain correct if edge changes.

Single host: TLS edge → containers → PostgreSQL/local media volumes → independent
backup. Scale: edge/ingress + stateless app replicas, separately scaled
browser/review/job workers claiming PostgreSQL jobs, institutionally operated HA
PostgreSQL, shared MediaStore. No NGINX Plus or hosted component is required;
Compose is reference packaging, not ceiling.

Only NGINX publishes port 8080 locally. Public host/path maps through normalized
trusted `site_domain`; local extra sites may use `/s/<slug>/`. Forged Host never
grants membership/preview.

Required environment/configuration contract:

```text
SLAIF_MODE SLAIF_AUTH_MODE SLAIF_PUBLIC_URL SLAIF_SECRET_KEY
SLAIF_DATABASE_URL_* (or generated service credentials)
SLAIF_MEDIA_ROOT SLAIF_MEDIA_STORE_BACKEND
SLAIF_DEFAULT_SESSION_TTL SLAIF_MAX_SESSION_TTL
SLAIF_AUDIT_RETENTION_DAYS SLAIF_STAGING_RETENTION_DAYS
SLAIF_BROWSER_ARTIFACT_RETENTION_DAYS SLAIF_BROWSER_MAX_CONCURRENCY
SLAIF_BROWSER_EGRESS_PROXY SLAIF_SOURCE_DEFAULT_DENY
SLAIF_OIDC_ISSUER SLAIF_OIDC_CLIENT_ID SLAIF_OIDC_CLIENT_SECRET_FILE (OIDC)
```

Each service validates initialization/setup state, auth-mode consistency,
correct DB role/schema privileges, media permissions, browser network/service
credential/resources/artifact namespace, source default-deny, public URL/cookie
scheme, TTLs, catalog/composition/Puck/content-model/browser-target versions,
and foundation version. Demo may bootstrap generated secrets; production mounts
operator-managed secret files. Never commit secrets.

One-command startup must: pull/build pinned app/browser images; start/health DB;
run Alembic; deploy/enable/harden COW; grants/privilege validation; optional demo
seed; create only a digest of an expiring one-use setup token if uninitialized;
start APIs/media/browser/review/scheduler/GC/web/render/Puck; start NGINX as sole
host service; print readiness and plaintext setup URL/token only when needed.
No manual first-start migration. Failed privilege validation blocks Agent API/
review readiness; failed browser sandbox/egress marker blocks browser readiness
without exposing listener.

`/health/live` and `/health/ready` readiness covers DB, schema revision, COW
deployment/privilege marker, catalog/composition/Puck/content-model/Playwright
compatibility, appropriate media write, and browser liveness/auth/sandbox/
egress/artifact access.

Local auth is default so no external IdP is required. Never ship permanent
default admin. On uninitialized install bootstrap generates random expiring
one-use token, stores digest, prints operator setup URL/token; `/setup` consumes
it while atomically creating first Platform Administrator/initialized state,
destroys token, permanently closes route. Documented one-shot Compose
`create-admin` may be fallback. Production refuses absent/expired/reused token,
weak signing secrets, insecure cookies on public hostname, default DB passwords.

OIDC is optional; immutable identity key is `(issuer, subject)`, never email.
Human browser session uses HTTP-only, production Secure, SameSite=Lax-or-stricter
cookie; CSRF for state-changing control; short inactivity; recent-auth for risky
acceptance; approved memory-hard password hashing; no local-storage token.
Internal network plus separate DB creds is not enough for sensitive internal
HTTP: use generated service secret locally and mutual authentication as
appropriate in production. Render/raw browser APIs are not edge-routed; browser
credential is short-lived/run-bound and never human/agent credential.

Admin IA: Dashboard, Sites, Content, Content Models, Pages, Structure, Design,
Media, AI Sessions, Reviews, Users & Permissions, Audit, Settings. Dashboard
surfaces site status/workspaces/conflicts/publication/browser/audit. Site
selection derives membership. Setup appears only with valid one-time state.

## 14. Security, validation, privacy

Threat actors: agent is untrusted and may be hostile; delegator may err;
semantic gateway, promotion worker, DB owner, and host admin have increasing
trust. Protect canonical/unpublished content, media/private artifacts, identity/
membership, capabilities, audit, reviewer/DB/signing secrets, backups. Host/DB
owner/malicious review worker and mutually hostile co-tenants are explicitly
outside agent-isolation guarantee; conventional hardening/backups still apply.

Required mitigations by threat:

- Session/workspace/site/Host substitution: server-derived COW/site context,
  normalized trusted domain mapping, membership/capability checks, site-scoped
  queries/composite constraints/negative tests.
- Canonical/publish/scope/role escape: distinct credentials/processes, no agent
  control route, route+resource policy before DB, human-only role APIs.
- Token theft/replay: high entropy, TTL, one-time display, redaction, revoke,
  quotas, idempotency. Prompt injection remains isolated and human-reviewed.
- SQL/context/code/component/Puck abuse: typed parameterized semantic APIs, no
  native/raw interface, safe COW scope validation, backend policy, bounded
  primitives/schemas, no executable input.
- Freeze/promotion races/partial failure/audit omission: state transition plus
  shared/exclusive product locks, foundation locks/conflict check, one reviewer
  transaction, same-tx audit and pre-promotion cross-check.
- XSS/CSS/media: structured allowlisted rich text/rendering; no raw style/code;
  MIME/signature/dimension/decompression/SVG policy; immutable digests.
- Preview/setup leakage/takeover: auth/noindex/no-store/no token URL, one-time
  expiring operator token and closed setup route.
- SSRF/browser/file/session/artifact/worker escalation: explicit origin,
  DNS+redirect+egress enforcement, no private/link-local/metadata/file by default,
  fresh contexts, no persistent cookies, separate non-root/read-only/resource-
  limited network/container, no DB/Docker/mount, private expiring artifacts.
- Resource/zombie abuse: bounded model/query/page/batch/media/browser quotas,
  cancellation/timeouts, scheduler TTL/idempotent cleanup.
- Side-effect/reviewer/setup credential escape: proposal/outbox; worker-only
  reviewer and one-shot owner; secrets absent from agent/API images.
- Edge difference never removes application policy. Backup loss requires
  independent tested recovery.

Rich text uses structured portable representation and allowlist; reject scripts,
handlers, style, executable URL, unapproved iframe, arbitrary HTML. URLs allow
https, policy-approved http, mailto, tel, relative; reject javascript, file, and
data except controlled image ingestion; safe external-link `rel`. Media validates
size/signature/extension/dimensions/pixels/archive/PDF pages; SVG sanitize or
disable. Structural policy bounds pages/depth/components/types/fields/object
depth/definition/query complexity/result/time/rich text/navigation/batch/deletes/
redirects/import URLs/browser routes/targets/runs/screenshots/downloads/bytes/
time/concurrency. Theme rejects invalid/inaccessible colors, remote/uninstalled
font, unsupported token, CSS, arbitrary breakpoint. Model/composition rejects
unknown/recursive/duplicate/cross-site/dangling/unbounded/executable/bad-version
input. Server schemas always authoritative over generated clients.

Security headers: CSP avoiding unsafe inline, `X-Content-Type-Options: nosniff`,
Referrer-Policy, Permissions-Policy, production HSTS, frame-ancestors; tested
through both edge adapters. No session token in query. Preview/setup strict
no-store/noindex. Client-forgeable headers never authenticate.

Privacy/default network: no telemetry and no outbound application call except
operator action or policy-authorized recorded/quota-limited source job. SLAIF
does not proxy AI conversations; user chooses agent/data disclosure. Capability
is secret. Configure/minimize audit retention. Private unpublished screenshots/
traces/DOM/accessibility/source/diagnostics may contain sensitive data: private
namespace/auth reads/site retention+quota/redaction, no telemetry/public path;
never retain browser profile/credentials.

Production hardening before exposure: complete setup; strong local auth or OIDC;
real TLS; internal DB; service secrets; non-root/read-only/capability and CPU/
memory/PID limits; backups/retention/quotas/rate limits; enforced browser egress
and isolated mount-free network; shared media at multi-node; edge headers/body/
buffer/trusted-proxy review; restore test; disable demos; privilege validation.

## 15. Observability, jobs, reliability, backup/recovery

Every request correlates request/trace IDs, site/workspace where applicable,
capability public ID never secret, mutation operation ID, browser run/target,
delegator. JSON logs include service/route/status/latency/workspace/scope/site/
operation/browser/artifact/egress/DB/promotion result; exclude secrets,
passwords, DB URLs, cookies, sensitive payloads, source/internal credentials,
artifact retrieval tokens. Logs rotate and never replace durable semantic audit.

Metrics: active workspaces/expired tokens/status/scope denials/operations/
promotion duration/conflicts/discards/queue/failures/media/cleanup/DB pool/sites
and policy classes/browser queue+contexts+duration+targets+timeouts+denials+
artifact bytes/model validation/query cost. Prometheus-compatible optional; no
mandatory Prometheus container.

PostgreSQL `control.job` is durable queue. Workers claim with `FOR UPDATE SKIP
LOCKED`. Types: FREEZE_FINALIZE, ACCEPT_SESSION, ACCEPT_OPERATIONS,
DISCARD_SESSION, EXPIRE_SESSION, VALIDATE_CONTENT_MODEL, BROWSER_PREVIEW_RUN,
BROWSER_SOURCE_RUN, RESPONSIVE_SWEEP, MEDIA_GC, ARTIFACT_GC, CACHE_INVALIDATE,
AUDIT_EXPORT. Terminal job uniqueness is workspace+action; browser/model key
digests site/workspace watermark/action/routes/targets/origin/payload. Transient
DB/network/browser retries bounded exponential; conflicts terminal; validation
returns REVIEW; invariant/program bug fails for operator; no retry widens policy
or changes conflict mode; every browser retry uses fresh context. Multiple
worker pools claim transactionally; only review worker has reviewer authority.

Reliability:

- API crash rolls back transaction; idempotency record commits with mutation or
  neither. Promotion worker/connection crash rolls back all; lease expires/retry.
- Edge/web restart leaves DB/media durable. Scheduler downtime cannot bypass
  request-time expiry; cleanup resumes.
- Media copy failure precedes DB commit; copied orphan harmless. Cache outbox
  retries after canonical acceptance and temporary staleness is possible.
- Browser failure records bounded error/private safe artifacts, destroys
  context, optionally retries fresh, never rolls back workspace or publishes;
  reviewer sees missing evidence and policy requires rerun/acknowledgment.
- Model validation failure remains isolated and correctable/discardable.
- Setup create-admin and initialized state are atomic; restart is fully
  initialized or valid/new-token uninitialized, never half-open.

Production DB: regular base/logical backup plus WAL/PITR, encryption, off-host
retention, tested restore. Demo may provide pg_dump tools but docs must describe
stronger PITR. Back up public media; staging shorter policy; private artifacts
only if audit policy and never with usable expired URLs. Control/audit are DB;
optional append-only exports. Suggested deployment targets RPO 15 min/RTO 4 h,
not source-code guarantees.

Restore into clean deployment must prove canonical sites/domain routes/render;
models/items/compositions/themes/relations; identities/memberships/roles/
ceilings; initialized state/no stale setup token; accepted audit; safe capability
invalidate/restore policy; media digests; private retained artifacts and expired
credential privacy; COW hardening validation.

Operational runbooks:

- Capability leak: revoke, freeze, inspect, discard/review, rotate related human
  creds if needed, audit redaction failures.
- Stuck promotion: inspect job/transactions/locks, retry only if terminal not
  committed, rely on idempotency, never overwrite.
- Privilege failure: keep services stopped; owner fixes one transaction;
  reharden/revalidate before resume.
- Missing media: block promotion, restore/reupload matching digest, validate;
  never substitute bytes under digest.
- Suspected browser SSRF/escape: stop source claims/revoke service creds,
  isolate workers, preserve evidence, inspect egress/DNS/redirect/container,
  rotate preview credentials, patch and rerun cross-network tests.
- Stuck browser: inspect lease/context/quota/artifacts; terminate bounded
  context; retry fresh without widening; terminal failure visible, no publish.
- Setup-token exposure: invalidate; issue new only if uninitialized; unexpected
  initialization requires isolate/audit/recover; verify setup closed.
- Cross-site incident: revoke sessions/capabilities, freeze/preserve evidence,
  find missing context/query/host/constraint, assess all sites/restore, add
  negative regression before service restoration.

## 16. Performance, scale, upgrade

Expected institutional workload is tens/hundreds of workspace operations and
thousands, not billions, of rows/site; browser work is dominant burst. Logical
COW is default. Index changes/session ID/operation order/PK/site-content/type-
definition/item-status/relation/component/page-parent-slot-order/route-locale/
audit workspace-operation columns and explicitly declared indexable JSONB
projections. Profile canonical and workspace reads separately. Agents cannot
create physical indexes; query DSL exposes only platform-declared indexable
fields.

Initial policy defaults: 20 active workspaces/deployment with per-site bounds;
one actively mutating L4 import/site; max workspace 8 h; default agent 1 h;
retained review 7 d; per-site browser concurrency/artifact bytes. These are
policy, not foundation limits.

Distinct asyncpg pools: agent runtime, canonical read, preview read, control,
small reviewer. Browser has no DB pool; scale via job claims, bounded contexts,
resource limits and replicas. Stateless HTTP replicas require DB-backed
capability/idempotency, shared media, atomic worker claims, and no in-memory
authority at NGINX/Apache. Site quotas cover workspaces/browser/media/requests/
model size. Sensitive/large sites may get dedicated deployment/DB profile.

Product upgrade: backup DB/media; stop new workspaces; finish/discard incompatible
sessions; migration/bootstrap; validate foundation/application privileges;
deploy; smoke; resume. Catalog/component/Puck/content-model upgrades need
versioned deterministic migrations or backward readers; never silently replace
storage with undocumented Puck data. Field/query upgrades are trusted platform
releases. Incompatible active/review workspaces block or migrate. Playwright
package/browsers/target map/image upgrade together with full device/security
suite. Foundation upgrade additionally follows §2 registry/source/license/
pending-state/full-test/lock qualification.

## 17. Verification, CI, supply chain

Test layers: unit (policy/validators/mappings/query/composition/token/routes);
contract (OpenAPI/MCP/composition/component/browser schemas); DB integration
(COW/audit/roles); concurrency (freeze/write/overlap/non-overlap/cancellation);
E2E (setup/sites/users/Puck/agent visual loop/review/terminal); security
(workspace/site/role/scope/XSS/browser/token/artifact); packaging (fresh
Compose); license (locks/images); recovery; accessibility/responsive.

Mandatory invariant tests:

1. Agent runtime cannot read base/change or call commit/discard; Control cannot
   content DML; public reader cannot write; missing session context fails.
2. Client workspace UUID cannot select DB context; agent token cannot call
   acceptance; agent can delete all editable workspace data while canonical,
   users, other sites remain; discard restores absence of pending work.
3. Workspaces are mutually invisible; conflicting promotion preserves canonical
   and pending; nonoverlap preserves concurrent accepted changes; cancellation
   rolls all tables back; mutation/audit atomic.
4. Discard removes pending content/staging; accepted media cannot overwrite;
   preview requires auth/noindex.
5. L1 cannot L2–4; delegator cannot exceed ceiling; L4 cannot publish/code/DDL;
   Site A capability/member/Host cannot read/write/admin/preview Site B.
6. L4 creates News/model/items/view/page/navigation as data without Alembic and
   cannot add field primitive/query operator.
7. Puck and agent produce the same normalized composition; crafted hidden Puck
   action is denied by server.
8. Browser cannot DB/Docker/host/file/unauthorized origin; contexts/artifacts do
   not leak; browser success cannot accept/publish.
9. One-time setup cannot be reused; clean clone starts one command.

Playwright config defines all six stable targets. E2E traverses public NGINX,
not internal-only substitutes, and covers setup/local auth/site membership/
roles/delegation/dynamic News/Puck add-move-responsive+denial/capability issue-
use-revoke-freeze/screenshot-snapshot-sweep/network confinement/media/
review-promotion-discard-conflict/destructive isolation. Critical mobile:
login/site select/capability create-revoke/preview/review/accept-discard/users-
permissions/common content edit; full Puck desktop/tablet; phone only proven
claims.

Destructive demonstration test seeds canonical, L4 deletes all models/items/
pages/components/navigation/redirects/theme/media references, verifies broken
workspace but unchanged canonical, discards, verifies canonical/pending state.
Whole-site reconstruction fixture authorizes source, uses curated source tools,
creates full structured site and responsive iterations, makes one human Puck
edit, freezes/accepts, checks route/content coverage and no code/schema changes.

CI failure artifacts retain HTML report, first retry/failure trace, screenshots,
useful video, console/network logs, stable target and revision under private
retention. Pixel baselines only stable catalog/nav/header/footer/admin/Puck/
representative fixtures, not arbitrary generated sites; use structure+human
review there. Compose acceptance command is
`docker compose --profile e2e run --rm e2e` against isolated DB/volumes and no
hosted secret; path covers setup/login/site/capability/agent model-content-
composition/visual preview/discard/health.

CI supply-chain must inventory Python/Node, generate OCI SBOMs including
Playwright browsers/OS, fail unapproved licenses/unpinned direct deps, prove
foundation registry+hash lock and reject VCS/direct/local/editable, preserve
NOTICE/attribution, detect accidental hosted SDK/account config/outbound default
telemetry, and scan images for release-policy critical vulnerabilities. No PR
may silently add hosted DB, cloud-only object store, proprietary auth, forbidden
server license, external telemetry, or paid API; requires explicit architecture
decision and cannot replace self-hosted default.

## 18. Implementation sequence and contractual MVP

Phases preserve this order:

0. qualify/freeze/attribute PyPI foundation and hardening/matrix;
1. monorepo/Compose/edges/DB/web/backend/media/browser images/bootstrap/health/
   one-time setup/one-command startup;
2. local auth/OIDC contract/sites/memberships/roles/workspaces/capabilities/four
   presets/site-resource-browser quotas;
3. bounded field catalog/configurable models/items/relations/query views/
   versions/mappings/News-without-Alembic;
4. normalized composition/Puck/catalog/responsive/shared renderer/theme/media/
   admin UI;
5. semantic REST/OpenAPI/MCP/audit/scopes/quotas/batches/idempotency/staging/
   import manifest;
6. confined browser visual loop/private artifacts/source tools/E2E;
7. freeze/snapshot/diff/conflicts/validation/full accept-discard/publication/
   user-permission/audit UI/cache/media finalization;
8. whole-site source reconstruction with dynamic model/responsive iteration/
   human Puck adjustment/preservation report;
9. full device/security/cross-site/concurrency/browser/backup/scale/license/SBOM/
   nontechnical demo hardening.

Contractual MVP includes every item above needed for: named product/repo;
self-hosted one-command Compose; default NGINX plus Apache example; secure setup;
site-scoped users/built-ins/membership/ceilings; multi-site schema+demo site;
four presets; configurable types/fields/items/relations/views; normalized
composition+Puck; shared renderer+catalog; semantic REST/OpenAPI+MCP; internal
curated Playwright and six E2E targets; immutable media/private artifacts;
capability TTL/revoke; audit; private preview+immutable review; full accept/
discard; conflict-safe promotion; destructive demo; one dynamic-model fixture
reconstruction with responsive loop.

Strong follow-up only: selective operation UI/preview; two-person approval;
richer mappings; tested RLS; distributed shared media; Firefox/WebKit runtime
agent feedback beyond CI; custom roles; field-level rebase; WordPress adapter;
second non-site consumer and potential Agent-State extraction.

## 19. Acceptance criteria

Architecture is implemented only when demonstrable:

- **Installation:** clean clone/one Compose command; no hosted account/service;
  only NGINX 8080; internal browser included; expiring setup, no default admin;
  Apache preserves contract.
- **Administration/sites:** platform admin creates site/owner; owner manages
  membership/ceilings; roles vary by site; non-member denied other site admin/
  workspace/preview; critical review/publication works desktop+phone.
- **Safety:** agent cannot publish/select session/use SQL/Alembic/register code/
  arbitrary JS/origin/manage identity; Agent API lacks reviewer calls; total
  workspace destruction leaves canonical/users intact; conflicts/failures never
  overwrite/partially mutate; browser pass never publishes.
- **Delegation:** four documented presets; ceiling enforced; publish separate;
  L4 reconstructs without code authority.
- **Dynamic model:** L4 builds News fields/items/view/list/detail/page/nav with no
  Alembic; all items/bindings validate against versions; no executable primitive
  or query operator; physical schema developer-only.
- **Builder/renderer:** Puck edits with server-backed restrictions; Puck/agent
  equivalent normalized ops; same public/preview components; source site can be
  rebuilt in preview by L4; preview private/noindex.
- **Visual loop:** agent screenshot/accessibility only own preview; bounded
  desktop/tablet/mobile; browser cannot DB/Docker/host/private origin; source
  constrained; artifacts private/immutable/scoped/retained.
- **Operations/scale:** every mutation auditable; expiry/revoke and idempotent
  cleanup; documented/tested backup restore; license+SBOM pass; stateless HTTP
  replicas behind OSS edge; safe multi-worker claims; shared MediaStore swap
  preserves semantics.

Reference demonstrations: setup and seeded site; L4 dynamically adds News and
responsive evidence then Puck/human publish decision; approved-origin complete
reconstruction with audit/Puck/freeze/review; destructive workspace leaves live
site/users/other sites unchanged then discard; two workspaces edit same title,
accept A and B reports conflict without canonical change.

## 20. Architecture decisions (ADRs)

1. **Separate product/foundation:** registry-installed generic package; product
   monorepo; reusable quality/release separation and no Git build dependency.
2. **Logical COW on self-hosted PostgreSQL:** meets isolation/promotion and
   clone-and-run/permissive requirements; hosted branch systems are prior art.
3. **All online edits in workspaces:** one auditable secured promotion boundary.
4. **NGINX OSS reference, Apache adapter:** familiar open deployment and OSS
   scale; security remains edge-independent.
5. **One renderer/catalog:** preview fidelity is a core property.
6. **Puck authoring, not persistence/authority:** mature UX behind stable product
   schemas/audit/policy/upgrades.
7. **Content types are data:** varied domains without predicting tables or agent
   migration authority.
8. **Bounded structured primitives; no agent code:** broad design without RCE.
9. **Four presets over granular scopes:** understandable UX plus composable
   server policy; separate human RBAC.
10. **Publication orthogonal/human-only:** defining governance boundary.
11. **Multi-site v1:** institutional requirement, no hostile-tenancy claim.
12. **Playwright dual-use:** E2E plus actual agent-rendered feedback.
13. **Curated browser tools:** raw automation is not a security boundary.
14. **PostgreSQL queue:** transactional creation/claims and fewer components.
15. **Immutable MediaStore:** local simplicity and scale backend substitution.
16. **Alembic only platform schema:** site modeling remains reviewable data.
17. **One DB/separate schemas+roles:** runtime/audit/promotion atomicity without
    distributed transactions.

## 21. Known limitations and claim discipline

1. Logical COW is live-base overlay, not frozen DB snapshot; untouched canonical
   changes may be observed; row conflict uses current/first-touch baseline, not
   full history; table promotion locks may constrain writers.
2. Configurable model is bounded by implemented primitives/query language;
   agents cannot create executable fields/operators/components; JSONB needs
   deliberate indexing/query limits; model changes may need mappings and validly
   fail/conflict.
3. Puck adapter/version maintenance is permanent; narrow-phone full Puck is not
   guaranteed without E2E.
4. Playwright costs CPU/memory and requires quota/scaling; automated heuristics
   cannot judge beauty; human review remains.
5. Constrained crawling cannot reproduce authenticated/highly stateful/
   inaccessible sources.
6. Multi-site is institutional application tenancy, not hostile SaaS/per-tenant
   crypto boundary.
7. Local media volume is not horizontally shared; configure shared MediaStore.
8. Automated field-level merge is absent from first release.
9. Infrastructure compromise is outside capability guarantee.

Never hide these limitations or describe planned/prototype/narrowly tested work
as complete, production-ready, certified, hostile-tenant-safe, or more
responsive/browser-compatible than executable evidence proves.

Future Agent-State consumers may include experiment management, research data
catalogs, knowledge bases, events, structured documents, administration, and
scientific metadata. Extract only after a second real non-website consumer.

## 22. Canonical product wording

One sentence: **SLAIF Agent-Site is a self-hosted platform where humans and AI
agents can build, redesign, and manage websites in isolated workspaces, inspect
the real responsive result, and publish only after human review.**

Security wording: **A request authorized solely by an Agent-Site agent
capability can modify only the capability's site-bound workspace. It cannot
write canonical content, manage users, run physical schema migrations, alter
executable code, or publish.**

Foundation wording: **The project does not claim to invent copy-on-write. The
PyPI distribution `agent-cow-postgresql` supplies generic database isolation;
Agent-State binds temporary authority to it; Agent-Site makes it a complete
human-governed autonomous website-design platform.**
