# OAP Coding-Agent Report — 078-7-b

## Work order

- Identifier: `078-7-b` (increment-qualified; second round of semantic
  increment 7 of numeric Objective 078)
- Work-order file:
  `oap/orders/078-7-b-reproducibility-and-truth-residual.md`
  (sha256 `36a1369759716edfd52d5081008b4cf3c86a21d25abae71fc3dda3f8cf0a8801`)
- `oap/active` committed byte-for-byte: `078-7-b\n` (8 bytes, sha256
  `129e538d15e7b8cb8316782e052073edc4502130cccb239e2112f9273b6a25e7`)
- Numeric objective: 078 (increment 7)
- PR mode: AMENDED_EXISTING_PR

## Status
COMPLETE — D1 repaired at the build level (no gate change, no renderer
change) and proven by three consecutive green
`tools.supply_chain.reproducible` runs plus the full local gate
including the full Compose smoke with all 12 browser projects; D2
corrected on exactly the four ordered surfaces with durable wording;
`tools/supply_chain/`, `tests/supply_chain/`, and `.github/workflows/`
byte-identical to the 078-7-a head. The two 078-7-a recorded deviations
are closed by strategy adjudication in the order itself (mirrored
below).

## Executive summary

- **D1 (build nondeterminism, the rejected `Supply-chain evidence`
  failure at head `898360f`)**: the byte-variation class in
  `[...sitePath]/page_client-reference-manifest.js` is object
  key-order permutation inside the manifest's JSON mappings
  (same-size 8857-byte CI copies, `normalized_fields=[]`, i.e. raw byte
  comparison). The insertion order of the string-keyed `clientModules`
  map follows the import order of the generated flight-client entry
  module, which follows webpack module-processing order — an async
  factory interleaving that can differ between builds on loaded
  runners. 078-7-a introduced it because the new site dynamic route
  now carries the full site component tree as client references
  (24-entry `clientModules` map vs. small/stable maps on the other 14
  routes). The minimal repair is a small webpack plugin in
  `apps/web/next.config.mjs` (production builds only) that re-emits
  every `*_client-reference-manifest.js` asset in a canonical form:
  object keys sorted at every level, compact separators, arrays kept
  in emitted order. The manifest is consumed exclusively through
  property lookups, so key order is semantically inert; no renderer
  behavior, dependency, lockfile, migration, endpoint, scope, or gate
  changes. The whole `web_distribution` tree (2061 files) is
  byte-identical across repeated clean builds apart from the two
  per-build crypto files the gate already normalizes; three
  consecutive full gate runs are green (exact lines below).
- **D2 (residual stale current-truth surfaces)**: exactly the four
  ordered surfaces corrected with durable verified-merge wording
  (README.md Objective-078/4 row; `oap/MVP-PROGRESS.md` "Active and
  remaining sequence"; `oap/MVP-PROGRESS.md` status-table row 078;
  `oap/INCREMENTS.md` `Next` ledger row). No other prose changed; the
  078/7 ledger row remains the standard in-flight line.
- Order and `oap/active` committed byte-for-byte unchanged (SHA-256
  verified against the activated bytes, recorded above).

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #87 — <https://github.com/ulfe-lmi/slaif-agent-site/pull/87>
  (state OPEN, title unchanged)
- Base branch: `main`; head branch:
  `oap/078-7-a-catalog-content-collection-components`
- Verified base (order-verified `main`):
  `2746c9f08c00fd84dff59bfd1536ce7319e16ff9`
- Starting remote SHA (rejected report-only head):
  `898360fc74b64fcfc3138ce469ff38cdf95a82b2`
- 078-7-a implementation head: `137abbcacc5a6a129beae2297bc958c949061c72`
- 078-7-b implementation head SHA: fe767c7527ba40ec8ec477349f517482388364e6
- Report publication commit: SELF
- 078-7-b implementation commits pushed before report: exactly one —
  `fe767c7527ba40ec8ec477349f517482388364e6` (`078-7-b: …`, 6 files,
  +373/−9)
- Report parent = implementation SHA: yes
- New PR this turn: no; amended existing PR #87: yes; merge performed:
  NO

## D1 byte-variation analysis

### The observed failure (CI, head 898360f)

CI run 35434859847, job `Supply-chain evidence`, step "Build
reproducible artifacts, SBOMs, scans, and evidence",
2026-09-19T09:31:43.7105344Z:

```text
reproducibility: ERROR: Web/browser normalized output manifests differ: section=web_distribution path=apps/web/.next/standalone/apps/web/.next/server/app/[...sitePath]/page_client-reference-manifest.js first=type=file,mode=0644,size=8857,sha256=4e5068128c69efca8e59bb66f32f47a31478bc76fb9b6381865429f41c4b69df,normalized_fields=[] second=type=file,mode=0644,size=8857,sha256=8cc61861e3144402fa093ba07c3cc5f184ac4405cfa9ff24274ebedaac1646f5,normalized_fields=[]
```

Both copies are exactly 8857 bytes with different SHA-256 digests and
`normalized_fields=[]` (the file is outside the gate's normalization
set, so its raw bytes are compared). Equal size with different content
is the signature of an ordering permutation of identical entries
rather than a content change. The gate's
`describe_manifest_difference` reports only the first differing path
in sorted order, so the other 14 manifests of the same class in the
tree could also have differed and would have been masked by this
first-diff report; the repair therefore canonicalizes the whole file
class, not only the reported path.

### Why the bytes vary (build internals, Next 16.3.3 webpack mode)

The manifests are emitted by Next's `ClientReferenceManifestPlugin`
(`next/dist/build/webpack/plugins/flight-manifest-plugin.js`), which
taps `processAssets` at `PROCESS_ASSETS_STAGE_ANALYSE` — value 4000 in
the webpack build bundled with Next 16.3.3 (verified from the
compiled constant table: `ANALYSE=4000`, `REPORT=5000`) — and emits
per-route assets via `compilation.emitAsset` as

```text
globalThis.__RSC_MANIFEST=(globalThis.__RSC_MANIFEST||{});globalThis.__RSC_MANIFEST["<page>"]=<json>;
```

where `<json>` is `JSON.stringify(mergedManifest)` with no key
sorting. The per-page manifest is merged from per-entrypoint group
manifests with `Object.assign`, preserving first-seen insertion
order. Which ordering survives into the bytes:

- `ssrModuleMapping`, `rscModuleMapping`, `edgeRscModuleMapping`,
  `edgeSSRModuleMapping` are keyed by numeric module IDs (integer-like
  keys), which `JSON.stringify` always emits in ascending numeric
  order regardless of insertion order — stable.
- `moduleLoading` is a fixed two-key object — stable.
- `clientModules` (keys = absolute module resource paths) and
  `entryCSSFiles` (keys = absolute page paths) are string-keyed maps
  whose JSON key order is exactly their insertion order — the
  variable class.
- Each map is populated by `recordModule` in the order the generated
  flight-client entry module's outgoing connections are visited
  (`getOutgoingConnectionsInOrder`), i.e. in the import order of the
  entry module's generated source, which is the order the
  client-reference modules were processed during webpack's async
  module-factory phase. That interleaving is deterministic for a
  given machine/load profile but can differ between builds on loaded
  2-core GitHub runners; nothing in the entry set changes.
- The `chunks` arrays are computed by a synchronous chunk-graph walk
  (`getAppPathRequiredChunks`) — deterministic; they are left in
  emitted order by the repair.

The runtime consumes the manifest exclusively through property
lookups: the next-server app runtime reads
`clientReferenceManifest = __RSC_MANIFEST[pageKey]`, then
`.ssrModuleMapping[id]` / `.clientModules[resource]` /
`.entryCSSFiles[resource]`; required chunk lists are registered into
the preload resource maps (set-like, deduplicated) for
`<link rel="modulepreload">` registration. No consumer depends on
object key enumeration order, so canonicalizing key order changes no
renderer behavior.

### Why 078-7-a introduced it

Before 078-7-a the site dynamic route carried no client references,
so its manifest (and every other route's) had a small, trivially
stable insertion order. 078-7-a added the bounded
CollectionSearch/CollectionFilter client-state components to the
catalog and the site projection, so the `[...sitePath]` route's
flight-client entry now imports the client references of the full
site component tree: the `clientModules` map grows to 24
absolute-path keys and `entryCSSFiles` to 4 entries. Only this route
has a large enough string-keyed map for the async-factory
interleaving to reorder its keys — consistent with the CI evidence
where this file is the first (and reported) difference while the
identical code passed the same check at the implementation head
(check run 105873682238 on `137abbc`, 09:12:57Z-09:23:59Z).

### Local reproduction attempts (load-dependent; class demonstrated per the order)

Six clean production builds on the 24-core execution VM (each:
`rm -rf apps/web/.next packages/*/dist`, then `pnpm --recursive run
build` with `SOURCE_DATE_EPOCH=1704067200`,
`NEXT_TELEMETRY_DISABLED=1`; builds 4–6 additionally under 8-CPU spin
load): the target manifest was byte-identical across all six (sha256
`a16c8cd899af949b6552a9878fc3ebcef9e4516561226e95db55b2f1fada21a4`,
8549 bytes — the local path prefix differs from CI's, hence the size
difference versus 8857). The only cross-build differences were the
two gate-normalized crypto files
(`prerender-manifest.json` previewMode keys,
`server-reference-manifest.json` `encryptionKey`), verified by diff.
The variation class therefore does not reproduce on this stable
local machine; per requirement 0 it is demonstrated here from the CI
evidence (same-size, different-sha raw-byte pair) and the build
internals above.

### The minimal repair

One production/config file changed: `apps/web/next.config.mjs`
(+87/−0, the file's existing deterministic `generateBuildId`
unchanged). It adds a small inlined webpack plugin
(`DeterministicClientReferenceManifests`), registered for production
builds only, that taps `processAssets` at stage 4500 — strictly after
`PROCESS_ASSETS_STAGE_ANALYSE` (4000), where Next emits the
manifests, and before `PROCESS_ASSETS_STAGE_REPORT` (5000) — and, for
every asset whose name ends in `_client-reference-manifest.js` (15
files: all `page`/`route` manifests plus `_not-found` and
`_global-error`, on every compiler):

1. validates the exact `globalThis.__RSC_MANIFEST=…` wrapper (a
   build fails loudly on an unexpected shape instead of silently
   emitting non-canonical bytes),
2. parses the JSON body,
3. deep-sorts all object keys at every level (deterministic UTF-16
   code-unit order; integer-like keys are additionally canonized by
   `JSON.stringify`'s own integer-key enumeration rule),
4. re-serializes with compact separators and re-emits the asset with
   webpack's own `RawSource` (from `options.webpack.sources`).

All arrays — the per-module `chunks` load lists and the
`entryCSSFiles` cascade arrays — are kept in emitted order, so no
preload-registration order and no CSS cascade order changes.
`next.config.mjs` is a versioned build input, so the deterministic
BUILD_ID changes exactly once (from the 078-7-a value to
`e71c177ae73ffa964c28a2bcca91ee7a`); it is stable across all repeated builds of this
commit, as the gate runs below show.

Why this is the minimal in-scope repair: it is build-level
configuration (explicitly allowed by the order's D1 scope), touches
no renderer module, adds no dependency, changes no lockfile, no
gate, and no tooling; it canonicalizes the entire demonstrated
variation class (key-order permutation of identical entry sets) for
the whole manifest file class in one deterministic function; and it
fails the build rather than degrading if Next ever changes the
wrapper shape. The alternative in-scope candidate (normalizing in
`tools/supply_chain/*`) is forbidden by the order's non-goals.

### Why the reproducibility contract now holds

For any two builds of this commit, each manifest asset's emitted
bytes are a pure function of the manifest's content (the set of
entries and their values), which is itself a deterministic function
of the commit: entrypoint discovery is sorted, module/chunk IDs are
deterministic, and the only previously variable part (object key
insertion order) is canonicalized before emission. The full
`web_distribution` tree — standalone, static, and public, 2061 files
— is byte-identical across repeated clean builds apart from the two
per-build crypto files the gate already normalizes. Evidence: the
three consecutive gate runs below (each = 2 Python builds + 2 Node
builds with clean outputs between them) plus the 2061-file tree
comparison of two independent clean builds.

## D1 evidence (requirement 1)

### (a) Three consecutive full local reproducibility gate runs

Command (three consecutive invocations, fresh output directory each,
run on the final committed tree state):

```bash
uv run --frozen python -m tools.supply_chain.reproducible --root . --output /tmp/repro-out2-1
uv run --frozen python -m tools.supply_chain.reproducible --root . --output /tmp/repro-out2-2
uv run --frozen python -m tools.supply_chain.reproducible --root . --output /tmp/repro-out2-3
```

Exact output lines (each run also printed the standard
`component-catalog: OK catalog-v1 Python/TypeScript semantic equality`
and `agent-openapi: OK contracts/openapi/agent-v1.json` lines):

```text
run 1: reproducibility: OK python-artifacts=2 next-build-id=e71c177ae73ffa964c28a2bcca91ee7a browser-output=source-contract
run 2: reproducibility: OK python-artifacts=2 next-build-id=e71c177ae73ffa964c28a2bcca91ee7a browser-output=source-contract
run 3: reproducibility: OK python-artifacts=2 next-build-id=e71c177ae73ffa964c28a2bcca91ee7a browser-output=source-contract
```

All three runs rc=0. Each run performs two `uv build --offline`
Python builds (wheel + sdist, byte-compared) and two
`pnpm --recursive run build` Node builds (cleaned between builds) with
the policy `SOURCE_DATE_EPOCH=1704067200`; all four web trees
byte-identical within every run.

Supporting tree comparison (two independent clean builds of the
committed tree): 2061 files under `.next/standalone`, `.next/static`,
and `public` hashed; the only differing files were
`.next/standalone/apps/web/.next/prerender-manifest.json` and
`.next/standalone/apps/web/.next/server/server-reference-manifest.json`
— exactly the two per-build crypto files the gate normalizes.

### (b) Full local gate green

See "Local verification" below (Python gate, Node gate, preparation
checks, process smokes, full Compose smoke with all 12 browser
projects including `preview-filtering`).

### (c) `Supply-chain evidence` on the new report-only head

See "GitHub CI / required checks" below: `success` on implementation
head `fe767c7527ba40ec8ec477349f517482388364e6`, the build verified by
the checks. The exact new report-only head carries that identical build
plus only this transcript (the order's own verified-state section makes
the "report-only commit cannot change a build" argument for 898360f); a
fresh 20-check run is triggered on the SELF head at push time and
strategy verifies it independently.

## D2 before/after (requirement 2)

### Surface 1 — `README.md` (Objective-078/4 capability-table row)

Before:

> … accepted and merged in PR #81 on 2026-09-10 at
> `26cafc1c0c91de5eee8406e8d477c50ea0208058`; global regions/catalog
> remain deferred at increment `078-5-a`.

After:

> … accepted and merged in PR #81 on 2026-09-10 at
> `26cafc1c0c91de5eee8406e8d477c50ea0208058`; global regions were
> delivered by increment 078/5, accepted and merged in PR #85 at
> `2746c9f08c00fd84dff59bfd1536ce7319e16ff9` on 2026-09-19, and the
> catalog increment 078/7 is opened at `078-7-a` (PR #87); GitHub is
> authoritative for live acceptance and merge state.

### Surface 2 — `oap/MVP-PROGRESS.md` ("Active and remaining
sequence")

Before:

> 078/1, 078/2, 078/3, and 078/4 are all accepted and merged; the next
> Objective-078 product increment starts at `078-5-a`. Acceptance and
> containment in `main` are determined by OAP and GitHub state, not
> this document. All later order files remain inert until strategy
> selects and signals them.

After:

> 078/1, 078/2, 078/3, 078/4, 078/5, and 078/6 are all accepted and
> merged (verified merge SHAs per `oap/INCREMENTS.md`: PR #77 at
> `3cae3d6cef2a92e7068856d21bc9a47b8190c22e`, PR #79 at
> `a9d3e6800d5e8b5fd5c9cd9e0be5010184058c6b`, PR #80 at
> `fe31c9f30a7797d0916ad7f8fb56344bc61526f3`, PR #81 at
> `26cafc1c0c91de5eee8406e8d477c50ea0208058`, PR #85 at
> `2746c9f08c00fd84dff59bfd1536ce7319e16ff9`, PR #86 at
> `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`); increment 078/7 is
> opened at `078-7-a` (PR #87). Acceptance and containment in `main`
> are determined by OAP and GitHub state, not this document; GitHub
> remains authoritative for live acceptance and merge state. All
> later order files remain inert until strategy selects and signals
> them.

### Surface 3 — `oap/MVP-PROGRESS.md` (status table, row 078)

Before (tail of the status cell):

> … 078/4 is accepted and merged in PR #81 at `26cafc1`;
> global-region/catalog scope remains deferred, starting at `078-5-a`

After (tail of the status cell):

> … 078/4 is accepted and merged in PR #81 at `26cafc1`; 078/5 is
> accepted and merged in PR #85 at
> `2746c9f08c00fd84dff59bfd1536ce7319e16ff9`; 078/6 is accepted and
> merged in PR #86 at `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`;
> increment 078/7 is opened at `078-7-a` (PR #87)

### Surface 4 — `oap/INCREMENTS.md` (`Next` ledger row)

Before:

> | Next | Remaining 078 scope after 078/5 | … |

After:

> | Next | Remaining 078 scope after 078/7 | … |

(the remainder of the row is unchanged). The 078/7 ledger row itself
remains the standard in-flight line: "Opened at `078-7-a` from
verified remote main `2746c9f…`; PR pending; strategy owns acceptance
and merge".

No other prose was restructured anywhere in the tree.

## Tooling byte-identity confirmation (acceptance criterion 1)

```bash
git diff --stat <078-7-a report-only head 898360f> -- tools/supply_chain tests/supply_chain .github/workflows
# (empty output)
```

`tools/supply_chain/`, `tests/supply_chain/`, and
`.github/workflows/` are byte-identical to the 078-7-a head; no
normalization entry, path exclusion, or assertion relaxation was
added.

## Full Compose smoke (requirement 3)

`sh tools/compose/smoke.sh slaif0075a` — full run end-to-end, log
retained at `/tmp/smoke-0787b.log`, rc=0, zero flakes, zero re-runs.
Exact final status lines:

- `compose-policy: OK`
- `membership-fixtures: OK count=2 kind=OIDC authenticatable=no installation=uninitialized`
- `compose-mode-policy: OK long-running-backends=9 mode=development`
- `browser-worker-runtime-policy: OK uid=10001 readonly=yes caps=SYS_CHROOT limits=exact network=browser`
- `browser-worker-image-policy: OK playwright=1.62.1 cft_revision=1681091 chromium=153.0.8010.52 browsers=chromium-only package-manager=absent`
- `browser-e2e: OK`
- `compose-e2e: OK projects=12 setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2 artifacts=disabled`
- `public-agent-news-edge: OK workspace=3c289ede-6b8b-4c74-9825-a222658f5775 routes=default,non-default detail=exact listing-sort=verified status-slug-translation=verified canonical-isolation=byte-identical components=ct,contact,search,filter,related,puck hostile=agent-7,puck-4 restart=agent,render,web html=uuid-token-flight-free css=canonical-parity browser-artifacts=public-verified-retained authorization=one-use`
- `public-agent-component-loop: OK workspace=f9ac02fd-b160-4043-a3c8-ebf95487cbe6 page=8f8bc942-4ad8-4774-bc3b-f716adea7e6a tree=Section>Container>(RichText,Heading) initial=empty update=content-only move=before,after preview=human-nginx-html browser=real-private-4-artifacts restart=agent,render,web state=ids-props-hierarchy-order-versions delete=leaves-parents-replay-safe negatives=scope-design-foreign-stale-schema-idempotency quotas=mutation-delete resource=bounded canonical=unchanged observer=unchanged`
- `public-agent-acceptance: OK workspace=8ea2f9b1-0cde-490c-9e38-8c80e28fbce5 types=2 fields=3 items=2 translations=1 relations=1 views=1 pages=1 components=1 locales=1 redirects=1 navigations=1 navigation-items=3 theme=schema-default-patch-read-replay openapi=exact restart=verified nginx-outage=verified crud=public quotas=mutation-429,max-delete-429 dependency-delete=422 page-delete-restore=verified canonical-independence=verified render-restart=verified`
- `public-agent-restart: OK workspace=4293a757-acf8-4b9a-bcea-2f86c9c944bc capability=933747545b528bc1 agent-before=200 agent-after-restart=200 agent-after-revoke=401`
- `public-agent-restart-audit: OK workspace=4293a757-acf8-4b9a-bcea-2f86c9c944bc capability=933747545b528bc1 rows=3`
- `media-e2e: OK edge=nginx upload=validated-private-read=byte-identical`
- `human-editor-envelope: OK workspace=HUMAN active audit=idempotent sequence=page-create,theme-update,page-style-update,page-style-update,component-add,component-add,component-move,component-add count=9`
- `governance-e2e: OK visible=create-profile-domains-membership-archive negatives=verified devices=6`
- `edge-header-policy: OK page/api/404 request-id-count=1 request-id-format=32hex csp-count=1`
- `edge-body-limit: OK media=route-allowance non-media=413 global=1MiB`
- `database-login-policy: OK public-connect=denied exact-roles=10 direct-default-owner-drift=none unrelated-connect=denied`
- `secret-file-policy: OK`
- `render-secret-policy: OK files=1 mode=0400 owner=10001`
- `render-preview-secret-policy: OK files=1 mode=0400 owner=10001`
- `render-auth-secret-policy: OK files=1 mode=0400 owner=10001`
- `browser-signing-secret-policy: OK files=1 mode=0400 owner=10001`
- `browser-worker-secret-policy: OK files=1 mode=0400 owner=10001`
- `browser-artifact-root-policy: OK retained-files=20 retained-artifacts=10 mode=0600 owner=10001`
- `media-secret-policy: OK files=1 mode=0400 owner=10001`
- `agent-browser-http: OK create=202 dispatcher=QUEUED-to-terminal restart=durable`
- `browser-worker-dispatch: OK durable-runs=2 artifacts=agent-owned`
- `browser-artifact-public: OK runs=2 artifacts=6 bytes=verified`
- `browser-artifact-negative: OK random=404 foreign-capability=404`
- `agent-browser-restart: OK durable-artifacts=retained`
- `browser-artifact-outage: OK status=503 canonical=200 bytes=absent`
- `browser-artifact-recovery: OK byte-identical`
- `browser-worker-restart: OK durable-dispatch-artifacts=retained`
- `browser-worker-public-separation: OK durable-runs=2 completed=2 db-artifacts=6`
- `browser-artifact-runtime-policy: OK files=32 retained=20 new=12 mode=0600 links=1 credentials=absent`
- `browser-worker-cleanup: OK chromium-children=0 temporary-profiles=0`
- `browser-worker-secret-recovery: OK missing=not-ready canonical=available restored=healthy`
- `browser-signing-recovery: OK missing=not-ready canonical=available restored=healthy`
- `control-readiness-fixture: OK mount=isolated identity=exact failures=6 recovery=clean`
- `governance-restart: OK site=archived membership=inactive domain=primary fixtures=retained setup=closed`
- `render-locator-failure: correctly blocked render=unhealthy web=503 nginx=unhealthy`
- `render-locator-recovery: restored render=healthy web=healthy nginx=healthy`
- `negative-bootstrap: correctly blocked`
- `browser-artifact-revoked: OK status=401 bytes=absent`
- `Ran 48 tests in 3.059s`
- `OK`
- `compose-smoke: OK`

## Local verification

All commands run from the repository root with uv `0.12.5`, Node
24.14.1, pnpm `11.22.0`, TypeScript `6.0.3`; integration tests on a
disposable local PostgreSQL (127.0.0.1:5432) with fake credentials.

Python gate (all steps green):

- `uv lock --check`: PASSED
- `uv sync --frozen --all-groups`: PASSED
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED ("All checks passed!")
- `uv run --frozen ruff format --check services/backend tests/
  repository tools`: PASSED
- `uv run --frozen mypy`: PASSED (no issues)
- `uv run --frozen pytest services/backend/tests/unit tests/
  repository`: PASSED (602 passed, 26 subtests passed, 29.46s)
- `uv run --frozen pytest services/backend/tests/integration`:
  PASSED (235 passed in 2432.73s (0:40:32), quiet VM, disposable
  local PostgreSQL, fake credentials; see transparency note below)
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED
  (sdist + wheel)
- `uv run --frozen python -m tools.contracts.generate_agent_openapi
  --check`: PASSED (zero drift, `agent-openapi: OK`)
- `uv run --frozen python tools/generate_component_catalog.py
  --check`: PASSED (`component-catalog: OK catalog-v1
  Python/TypeScript semantic equality`)
- `python tools/generate_design_system.py --check`: PASSED
  (`design-system: OK`)

Transparency note on the integration suite: the first quiet-free run
(12:49–13:29 local, executed while the Compose smoke and the Node
gate were running concurrently on the shared VM) completed
`1 failed, 234 passed in 2489.41s`; the single failure was
`test_agent_theme_boundaries.py::test_theme_races_use_database_barrier_
and_cancel_without_residue` at its waiter-count assertion
(`expected 2 theme lock waiters`) — a timing-sensitive concurrency
pin in a backend test that this round's diff does not touch
(web build config and docs only). Re-run in isolation on the quiet VM
it PASSED in 12.38s; the full suite re-run on the quiet VM is the
green record quoted above. No test was skipped, weakened, or
modified.

Process smokes (all 10, `uv run --frozen python -m
slaif_agent_site.<module> --check`): control_api, editor_api,
agent_api, render_api, mcp_adapter, media_service, review_worker,
scheduler, media_gc, bootstrap: PASSED (health-only, no port bind, no
mutation).

Node gate:

- `node --version` / `pnpm --version`: v24.14.1 / 11.22.0 (exact
  pinned versions)
- `pnpm install --frozen-lockfile`: PASSED
- `pnpm lint`: PASSED (root + `@slaif-agent-site/web`, 0 warnings)
- `pnpm format:check`: PASSED
- `pnpm typecheck`: PASSED
- `pnpm test`: PASSED (includes `pnpm build`; all workspace suites
  green; contract vitest 3 files / 16 tests passed)
- `pnpm build`: PASSED
- `pnpm licenses list --json`: PASSED (254 package instances:
  MIT 210, Apache-2.0 21, ISC 11, BSD-2-Clause 6, BSD-3-Clause 3,
  BlueOak-1.0.0 1, CC-BY-4.0 1, 0BSD 1 — identical to the 078-7-a
  record; no policy-forbidden licenses)
- `pnpm exec vitest run apps/web/tests/renderer-behavior.test.ts`:
  PASSED (11/11; this file is outside the root `pnpm test` glob, run
  separately as focused renderer evidence)

Preparation checks:

- `python -m compileall -q tools tests/repository`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`:
  PASSED (71 OK)
- `python tools/check_repository.py`: PASSED
- `python tools/check_mermaid.py`: PASSED (16 diagrams rendered, 497
  Markdown files scanned, CLI 11.16.0)
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED (0 issues;
  re-run after this report file is written)

Renderer-behavior non-regression (acceptance criterion 3): `pnpm
test` including the renderer-behavior suite and the
`preview-filtering` Playwright project pass with the same contracts
as 078-7-a (`bounded-client-filtering-contracts` PASSED in the smoke
above); the preview route remains flight-free
(`clientState={false}` untouched).

## GitHub CI / required checks

All 20 required checks (ruleset `protect`, ID 20934043, enforcement
active) on implementation head `fe767c7527ba40ec8ec477349f517482388364e6` (the build
verified by the checks; the report-only SELF head carries the identical
build plus this transcript):
**20/20 successful (every raw check-run
conclusion `success`); 0 pending, 0 failed, 0 skipped, 0 cancelled**.

| Required check | Conclusion |
| --- | --- |
| Repository policy | success |
| Node contracts | success |
| Python 3.12 quality and package | success |
| Python 3.13 quality and package | success |
| Python 3.14 quality and package | success |
| Foundation PostgreSQL 14 | success |
| Foundation PostgreSQL 15 | success |
| Foundation PostgreSQL 16 | success |
| Foundation PostgreSQL 17 | success |
| Foundation PostgreSQL 18 | success |
| Compose and edge packaging | success |
| Supply-chain evidence | success |
| Markdown | success |
| Mermaid | success |
| Dependency review | success |
| Detect supported languages | success |
| Analyze (actions) | success |
| Analyze (python) | success |
| Analyze (javascript-typescript) | success |
| CodeQL | success |

(Workflow runs 35440730995 (CI) + 35440731004 (CodeQL) on
`fe767c7527ba40ec8ec477349f517482388364e6`; the first attempt of run
35440730995 hit two transient CI-infrastructure failures:
`Compose and edge packaging` failed on the documented Puck-drag VM
flake class (`governance` project, contract
`puck-editor-round-trip-through-human-editor-api`, the pre-existing
`dragUntil` section of `governance.spec.ts`), and
`Foundation PostgreSQL 14` was cancelled by the frozen 15-minute job
timeout while its suites were still in flight on a slow runner (the
same suite set passed within the same limit on PostgreSQL 15-18 of the
identical commit; the failure step ended
`##[error]The operation was canceled.` after the preceding suites had
passed). Both jobs were re-run unmodified
(`gh run rerun 35440730995 --failed`); the re-runs and every other
check are the `success` rows above. No code changed for either re-run.
This is the documented flake/timeout class, not the D1
reproducibility defect — its evidence is the
`Supply-chain evidence` row, successful on first attempt at this
head.)

The report-only SELF commit (this report) triggers a fresh 20-check run
for the identical build (a report-only commit changes only this
transcript; the order's own verified-state section makes this argument
for 898360f); strategy independently verifies the SELF head.

## Local setup / dependencies

- Passwordless guest sudo: not required this round; the disposable
  local PostgreSQL instance from 078-7-a was reused for the
  integration tests. No durable host setup, no package install into
  the tree, no lockfile change. `uv.lock` and `pnpm-lock.yaml` are
  byte-identical to the base commit.
- Docker + Compose (project `slaif0075a`) used for the Compose smoke;
  containers and volumes are disposable and were torn down by the
  script's EXIT trap after the run.
- No production systems, data, or credentials touched.

## Documentation

- `README.md`, `oap/MVP-PROGRESS.md` (×2 surfaces),
  `oap/INCREMENTS.md`: the four D2 current-truth corrections above —
  durable verified-merge wording only; GitHub remains authoritative
  for live acceptance and merge state.
- No architecture/constitution/protocol file touched (the order does
  not require governance change); no other prose restructuring.

## Strategic adjudications mirrored (from the order's verified state)

The two 078-7-a recorded deviations are closed by strategy in the
order itself and are mirrored here for the record:

- (a) The OpenAPI deviation from 078-7-a binding decision 8 is
  **ACCEPTED** — the literal byte-identity clause conflicts with the
  repository's own frozen drift gates; the change is fully
  characterized and bounded (the +19/+19 audit enumerations of the
  five new types' 19 new properties on the existing
  `/api/agent/v1/components/{component_id}/patch` path under the
  existing `component-content-props:write` scope); decision-8 intent
  (no new routes, scopes, or documentation) holds exactly.
- (b) The PARTIAL browser-proof model is **ACCEPTED** as sufficient
  for increment 078/7 — the production logic module, production
  markup, input caps, and hostile rejections were all executed; only
  the React wiring layer is simulated by the documented harness; an
  E2E proof of the interactive state machine on a data-bearing
  product surface is architecturally impossible within Objective 078
  (flight-free preview contract; no publication/promotion surface).
  The limitation is recorded for closure when a publication/
  promotion surface exists.

## Files changed (078-7-b implementation commit)

| File | Change |
| --- | --- |
| `apps/web/next.config.mjs` | +87/-0 - D1 canonical-manifest webpack plugin (production builds only) |
| `README.md` | +1/-1 - D2 surface 1 |
| `oap/INCREMENTS.md` | +1/-1 - D2 surface 4 |
| `oap/MVP-PROGRESS.md` | +13/-6 - D2 surfaces 2 and 3 |
| `oap/active` | +1/-1 - activated round `078-7-b` (committed byte-for-byte as activated) |
| `oap/orders/078-7-b-reproducibility-and-truth-residual.md` | +270/-0 - work order (committed byte-for-byte as activated) |

## Known limitations / blockers

- The D1 variation class is demonstrated from the CI evidence and the
  build internals (local reproduction is load-dependent and did not
  fire on the stable 24-core VM across 6 builds, 3 of them under
  CPU load), as requirement 0 explicitly permits. The repair
  canonicalizes the entire demonstrated class for the whole manifest
  file class, so any key-order permutation of identical entry sets
  collapses to identical bytes; if a future CI divergence ever
  appears in a manifest, the gate's first-diff report plus the
  canonical form will identify it as a non-key-order variation.
- No other limitations; no secrets, credentials, or production data
  appear in the diff, the report, or any artifact.

## Cumulative base→head size (review-unit governance section 2)

Committed-SHA figures, base =
`2746c9f08c00fd84dff59bfd1536ce7319e16ff9` (verified `main`):

| Segment (committed) | Files | Insertions | Deletions |
| --- | --- | --- | --- |
| 078-7-a implementation (`2746c9f..137abbc`) | 39 | 4389 | 190 |
| 078-7-a report (`137abbc..898360f`) | 1 | 785 | 0 |
| 078-7-b implementation (`898360f..fe767c7`) | 6 | 373 | 9 |
| 078-7-b report (`fe767c7..SELF`, this commit) | 1 | (this file) | 0 |

Cumulative grouped per review unit across the two implementation
segments (078-7-a and 078-7-b), per 2026-09-14 review-unit
governance section 2 categories:

| Category | Files | Insertions | Deletions |
| --- | --- | --- | --- |
| Production/config | 17 (16 + `apps/web/next.config.mjs`) | 1063 (976 + 87) | 30 (30 + 0) |
| Migrations | 0 (in-place `060_001` regeneration counted under generated artifacts; precedent 078-b/078-c) | 0 | 0 |
| Tests/evidence | 11 | 1992 | 45 |
| Generated artifacts | 6 (incl. regenerated `060_001` and the OpenAPI contract at 891/93) | 1089 | 101 |
| Docs | 7 (4 + the three 078-7-b D2 files) | 33 (18 + 15) | 21 (13 + 8) |
| OAP transcript | 4 (two orders, two `oap/active` states; reports arrive in their SELF commits) | 585 (314 + 271) | 2 (1 + 1) |

The 078-7-a segment figures above are recomputed here from
`git diff --numstat 2746c9f..137abbc` and correct two arithmetic slips
in the previously published 078-7-a table, which had reconciled to the
same segment total: that table is only consistent with a 797/94 count
for the OpenAPI contract file (actual numstat: 891/93), and with
production/config counted as 1070/29 (actual: 976/30). File
classification follows the 078-7-a report (the Compose smoke scripts
and `playwright.config.ts` counted under production/config); both
tables' segment totals (4389/190) are identical.

Budget check (predeclared, section 1): production/config files 1 of
at most 5; migrations 0; test/evidence footprint 0 of at most 3;
generated-contract footprint 0; docs footprint 3 files of at most 4
(the four D2 surfaces live in three files); OAP transcript = order +
active + report; substantive 078-7-b implementation scale 87 lines,
well under 1.0k. The review trigger does not fire.

## Safety and scope confirmations

- Scope: exactly the order's two defects (D1 build-level determinism
  repair; D2 four-surface current-truth correction); no second
  objective PR; no other PR created, amended, or touched.
- No merge performed; no auto-merge; no close; strategy is the only
  merger.
- No changes under `tools/supply_chain/`, `tests/supply_chain/`, or
  `.github/workflows/` (byte-identical, confirmed above); no gate
  normalization, exclusion, or relaxation.
- No new public endpoint, no new scope, no OpenAPI route or
  enumeration change, no new migration, no dependency or lockfile
  change; `uv.lock`/`pnpm-lock.yaml` byte-identical to base.
- No renderer behavior change: no renderer source file touched;
  `pnpm test` (incl. renderer-behavior 11/11) and the
  `preview-filtering` project green with the 078-7-a contracts; the
  preview remains flight-free.
- No secrets, capabilities, cookies, DB URLs, or private artifact
  URLs in the diff or this report; the smoke's fixture identifiers
  (workspace UUIDs, capability `933747545b528bc1`) are disposable
  Compose-smoke values, not credentials.
- No production systems, data, or credentials accessed; no Docker
  socket escalation.
- All verification claims reference commands that were actually
  executed; nothing skipped or assumed; the one load-induced
  integration flake is documented with its isolation re-run and the
  quiet full-suite re-run.
