# OAP Coding-Agent Report — 078-9-a

## Work order

- File: `oap/orders/078-9-a-osm-layer-contract.md` (committed byte-for-byte
  unchanged with the implementation commit)
- SHA-256: `fe9ede16bb5dd3eee82c1d3ea59819c59c1d3814eea8e967f496089e519d0680`
  (18,245 bytes, 348 lines)
- `oap/active` committed bytes: `078-9-a` + LF (8 bytes),
  SHA-256 `8debb8e4b458cc440a200a4373b3d777127ab241aa3dde8ddea167540f6e3eef`
- Mode: `CREATE_NEW_PR`; branch
  `oap/078-9-a-osm-layer-contract`; base = verified remote `main`

## Status

**COMPLETE** — every requirement's named evidence actually ran (R1–R6,
acceptance 1–10; the exact CI state at the implementation head is recorded
below, and this report-only SELF commit triggers a fresh 20-check run that
strategy verifies independently).

Report publication commit: SELF

## Authoritative GitHub state

- Base / starting remote `main`:
  `ddd1559f021762316f5a64989a307355acb4aab2` (PR #88 merge commit,
  verified against live GitHub at activation; post-merge checks all
  successful, none pending).
- Branch: `oap/078-9-a-osm-layer-contract` (created from that SHA).
- PR: #89 —
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/89> (created by the
  executor; state open; strategy owns acceptance and merge).
- Implementation head (literal):
  `40d986825556057862bde8a3c3ea11d243463b35`
  (commit 1 `6c223d8` implementation; commit 2 `40d9868` in-scope
  repair of a CodeQL security finding raised by the first head).
- GitHub reconciliation at activation: only Dependabot PRs #75/#83/#84
  open; no objective PR existed; `gh pr create` created exactly one PR.

## Executive summary

The MapBlock provider contract now carries the three layer values the
live OpenStreetMap embed endpoint actually supports:
`{mapnik, cyclemap, transportmap}`. The legacy identifiers `cycle` /
`transport` (which the provider's registry lookup silently falls back to
`mapnik` for) are rejected fail-closed by catalog validation on both the
Agent and Editor paths. The hermetic contract tests were corrected in
place (the hermetic provider fixture itself is unchanged). A new
live-provider observation spec (`tests/e2e/live-osm-provider.spec.ts`)
was executed locally against the real provider — it is not referenced by
any `testMatch` project in `playwright.config.ts` and is not invoked by
`smoke.sh`/`e2e.sh`, so the deterministic CI contract stays hermetic per
the 078/8 design. The post-merge current-truth drift (078/8 rows in
`oap/INCREMENTS.md`, `README.md`, `oap/MVP-PROGRESS.md`) is repaired with
durable wording, and the inert preplanned `079-a` order was retired
byte-identical to `oap/governance/superseded-preplanned/`. No new
functionality, dependency, migration file, route, port, scope, or
lockfile change.

## R1 evidence — corrected provider contract (three-value allowlist)

- `services/backend/src/slaif_agent_site/content_model/bounded_embed.py`:
  `MAP_LAYERS = ("mapnik", "cyclemap", "transportmap")` (1-line change);
  `DEFAULT_MAP_LAYER = "mapnik"` and the canonical URL form unchanged
  (default emits no `layer` parameter).
- `apps/web/src/renderer/components.tsx`:
  `EMBED_MAP_LAYERS = new Set(["mapnik", "cyclemap", "transportmap"])`
  (1-line change); `EMBED_MAP_DEFAULT_LAYER` unchanged.
- Catalog source of truth
  `packages/component-catalog/src/catalog-v1.json`: `MapBlock.layer`
  `enum_values` → `["mapnik", "cyclemap", "transportmap"]` (1-line
  change).
- Regenerated artifacts (generator write modes, no hand edits):
  - `uv run --frozen python tools/generate_component_catalog.py`
    (rewrote `component_catalog.py` `_CATALOG_JSON`,
    `packages/component-catalog/src/index.ts` — byte-identical after
    regen — and `packages/composition-schema/src/catalog-v1.json`).
  - In-place `060_001` regeneration: `_CATALOG_V1_JSON` rebuilt from the
    source document with `json.dumps(document, ensure_ascii=True,
    sort_keys=True, separators=(",", ":"))` and
    `CATALOG_V1_REVIEWED_SHA256` recomputed →
    `ed73fa4fa2207da9008582b4cc3a48aa2fd22b0814a804e0c634142d7e14d1ca`
    (was `eecacea44de0698b665219d9f94b508485fb4cbe51e6ab80df2ab53312075169`);
    all other file content byte-identical (diff: exactly 2 lines).
  - `uv run --frozen python -m tools.contracts.generate_agent_openapi`
    (write mode): `contracts/openapi/agent-v1.json` regenerated —
    byte-identical to base (the MapBlock prop enum is not exposed in the
    OpenAPI document; validation is catalog-side), so the delta is zero,
    which is within the ordered `x-slaif-*`-only delta.
- Generator `--check` gates afterwards, all zero-diff (exact outputs):
  - `uv run --frozen python tools/generate_component_catalog.py --check`
    → `component-catalog: OK catalog-v1 Python/TypeScript semantic
    equality`
  - `uv run --frozen python -m tools.contracts.generate_agent_openapi
    --check` → `agent-openapi: OK contracts/openapi/agent-v1.json`
  - `uv run --frozen python tools/generate_design_system.py --check` → OK
  - `uv run --frozen python tools/generate_theme_schema.py --check` → OK
- Catalog-count pins verified UNCHANGED (29 types; the four pin files
  have empty diffs against base):
  - `packages/component-catalog/tests/index.test.ts`
    (`COMPONENT_CATALOG_DOCUMENT.components` and
    `DESIGN_SYSTEM_DOCUMENT.components` → `toHaveLength(29)`)
  - `packages/composition-schema/tests/puck-adapter.test.ts` (29)
  - `services/backend/tests/unit/test_component_catalog.py`
    (`assert len(COMPONENT_CATALOG) == 29`)
  - `tools/compose/public_agent_acceptance.py` (29-type pin; executed
    green in the Compose smoke, `public-agent-acceptance: OK`)
- Fail-closed rejection of the old values (existing bounded semantics,
  extended unit negatives with the exact error key
  `embed.layer-unknown` / `ERROR_LAYER_UNKNOWN`):
  `services/backend/tests/unit/test_bounded_embed.py` now includes
  `({"bbox": _bbox(), "layer": "cycle", "title": "T"},
  ERROR_LAYER_UNKNOWN)` and the identical case for `"transport"`. The
  Agent and Editor paths both enforce via the same catalog validation
  (`slaif_agent_component_validate` / editor composition validation);
  the hostile-write E2E suite in `tests/e2e/preview.spec.ts` (Agent and
  Editor valid MapBlock creates plus the rejection suite) passed in the
  Compose smoke with the corrected pins.
- No-persistence proof (both parts, exact results):
  1. Repository grep (committed tree, base → implementation head):
     `git grep -nIE 'layer[":= ]+["'\'']?(cycle|transport)["'\'']?|["'\'']layer["'\'']\s*:\s*["'\''](cycle|transport)["'\'']' -- .`
     (exact-layer-value forms) matches, excluding the immutable OAP
     transcript, only the two intentional fail-closed unit negatives
     (`test_bounded_embed.py` lines 333–334). The only other repository
     occurrence of the old values is the immutable historical report
     `oap/reports/078-8-a-bounded-embed-family.md` (excluded, immutable)
     and the order file itself. Fixtures/seeds: zero matches. Full
     disclosure recorded in `/tmp/oap-078-9a/nopersistence-grep.out`.
  2. Compose runtime scan on a fresh volume (stack `slaif0075c`,
     bootstrap from zero; content: setup + parity E2E fixtures and the
     live-observation workspaces created by the live spec):
     `SELECT count(*) ... WHERE props->>'layer' IN ('cycle','transport')`
     over `content.page_composition`, `content.page_composition_base`,
     and `content.page_composition_changes` → **0 / 0 / 0** (total 0).
     Stored MapBlock distribution: COW layer holds exactly
     `<default>`|1, `cyclemap`|1, `transportmap`|1 (all valid values).
     No content migration was performed.

## R2 evidence — hermetic contract tests (CI, values corrected)

- `services/backend/tests/unit/test_bounded_embed.py`: `MAP_LAYERS` pin
  updated; canonical-URL pins for `cyclemap`
  (`...&layer=cyclemap`) and `transportmap` (`...&layer=transportmap`);
  default `mapnik` still emits no `layer` parameter (existing pin);
  no-tracking loop updated; valid-props fixtures updated; the two
  fail-closed negatives above added.
- `apps/web/tests/renderer-behavior.test.ts`: `layer: "cyclemap"` fixture
  and exact markup pin `&amp;layer=cyclemap` updated (the `mapDefault`
  no-layer-parameter pin is unchanged).
- `tests/e2e/preview.spec.ts`: the hermetic embed pins updated — map
  iframe `src` pin (`&amp;layer=cyclemap` / `&layer=cyclemap`), the Agent
  valid MapBlock create (`layer: "cyclemap"`, idempotency key
  `oap-0788a-embed-map-${tag}`) and the Editor valid MapBlock create
  (`layer: "cyclemap"`). The hermetic provider-fixture contract itself
  (route.fulfill for the three CSP-allowlisted hosts) is UNCHANGED.
- Results (local, before PR publication — same suites run by CI):
  - `uv run --frozen pytest services/backend/tests/unit
    tests/repository` → `594 passed, 1 warning in 26.18s`
  - `pnpm exec vitest run apps/web/tests/renderer-behavior.test.ts`
    → `Test Files 1 passed (1); Tests 12 passed (12)`
  - `tests/e2e/preview.spec.ts` (project `preview`, incl. the corrected
    `bounded-embed-family-renders-canonically-and-rejects-hostile-writes`
    contract) → PASSED in the full Compose smoke (see below).
- OpenAPI:
  - strip-identity (all `x-slaif-*` keys stripped, canonical
    `json.dumps(sort_keys=True, separators=(",", ":"))`, SHA-256):
    base `df755623744785fdaf5f342268165fe7b7be9f352f276b56e2337692cae671da`
    = head `df755623744785fdaf5f342268165fe7b7be9f352f276b56e2337692cae671da`
    (identical).
  - Full-file SHA-256 base = head:
    `efbaccc2195f4a2a2863486cce9b383d9106a7badf7ea875041b11cf42fef097`
    (byte-identical; stronger than the ordered strip-identity).
  - Paths: 45 (base) = 45 (head).
  - Drift gate: `uv run --frozen python -m
    tools.contracts.generate_agent_openapi --check` → OK (also re-verified
    in the Compose smoke / CI `Node contracts` and
    `Python * quality and package` jobs, all green at the implementation
    head).

## R3 evidence — live provider observation (local execution)

Header-documented provider dependency; NOT referenced by any
`testMatch` project in `playwright.config.ts` (verified: the 13 projects
match only `setup`, `governance`, `preview`, `collection-filtering`,
`auth`, `agent-sessions` spec files) and NOT invoked by
`tools/compose/e2e.sh` or `smoke.sh` (both run only the named 12
projects). Real Compose environment, real network, no route mocking of
`www.openstreetmap.org`; the spec asserts hosts/paths only and records
host + pathname only, so no provider key material can enter the
artifacts (verified: `grep -c apikey evidence.json` → 0).

Executor's own fresh probes (2026-09-20, before the spec run;
`/tmp/oap-078-9a/probes-0789a.out`):

```text
https://tile.openstreetmap.org/12/1871/1081.png
  → http=200 type=image/png size=6987
https://api.thunderforest.com/cycle/12/1871/1081.png
  → http=200 type=image/png size=41622
https://api.thunderforest.com/styles/transport/style.json
  → http=401 (raw curl has no key — EXPECTED: the OSM-supplied key is
     injected by the provider's own embed bundle; the iframe-level
     observation below is the executable R3 evidence)
https://www.openstreetmap.org/export/embed.html?bbox=-12.5,55,-12.4,55.1&layer=mapnik
  → <title>OpenStreetMap Embedded</title>
```

Spec execution (fresh Compose stack `slaif0075c`, real network;
`pnpm exec playwright test --config <throwaway local-execution config>`
with the committed `playwright.config.ts` untouched):

```text
✓ 1 [live-osm] › tests/e2e/live-osm-provider.spec.ts:83:1 › live OSM
  embed: layer-specific upstreams, legacy cycle falls back to mapnik
  (5.5s)
1 passed (6.6s)
```

Observed request evidence (from the committed spec run;
`evidence.json`, 2026-09-20T12:50:19Z; per-frame attribution via
`request.frame()`):

- `mapnik` (src without `layer` parameter): 27 provider requests —
  25 × `GET tile.openstreetmap.org/12/<x>/<y>.png` → 200 (layer-specific
  upstream REQUIRED host `tile.openstreetmap.org` ✓) + 2 ×
  `www.openstreetmap.org` embed assets → 200.
- `cyclemap`: 27 provider requests — 25 ×
  `GET api.thunderforest.com/cycle/12/<x>/<y>.png` → 200 (host
  `api.thunderforest.com`, path prefix `/cycle/` ✓) + 2 ×
  `www.openstreetmap.org` embed assets → 200.
- `transportmap`: 12 provider requests —
  `GET api.thunderforest.com/styles/transport/style.json` → 200, plus
  `styles/transport/icons.json`, `styles/transport/patterns.png` and
  other `/styles/transport/`-prefixed assets → 200 (path prefix
  `/styles/transport/` ✓) + 2 × `www.openstreetmap.org` embed assets.
- Each iframe's frame document title asserted to be
  `OpenStreetMap Embedded`.
- Provider-level negative control (bare
  `https://www.openstreetmap.org/export/embed.html?bbox=-12.5,55,-12.4,55.1&layer=cycle`
  loaded directly): 21 provider requests — 18 ×
  `tile.openstreetmap.org` tiles → 200 (mapnik fallback observed ✓) and
  **0** `api.thunderforest.com` requests — documents that the legacy
  identifier silently fell back to the standard map.

Screenshots (Playwright test-results artifacts, per layer + negative
control):
`live-osm-mapnik.png`, `live-osm-cyclemap.png`,
`live-osm-transportmap.png`, `live-osm-legacy-cycle-fallback.png` under
`/tmp/slaif-playwright-live/live-osm-provider-live-OSM-b9a8c--cycle-falls-back-to-mapnik-live-osm/`
(local-execution output dir; not committed).

Disclosure — two in-round spec repairs (both in the ordered evidence
file; no product code involved):

1. After the first failed local run, the cross-origin iframe URL was
   found to settle after `goto` returns (about:blank at snapshot time);
   the frame lookup now polls (`expect.poll`, 15s) for the frame URL.
2. The first implementation head (`6c223d8`) recorded request query
   strings in `evidence.json`, which would have carried the
   OSM-bundle-supplied public `apikey=…` query parameter; per R6
   (no provider keys in diff or report) and the order's
   assert-hosts/paths-only rule, the spec now records host + pathname
   only, and the first head's CodeQL
   `Insecure temporary file` finding (see GitHub CI section) was
   resolved by moving artifact writes from a literal `/tmp`-derived
   path to the Playwright test-results artifacts API
   (`testInfo.outputDir` / `testInfo.outputPath`). The final live run
   above was executed with the exact code at the implementation head,
   and re-verified on a fresh stack (scan results in R1).

The provider was available; no PARTIAL/BLOCKED condition occurred.

## R4 evidence — current-truth reconciliation (durable wording)

Exactly five surfaces, minimal edits; verified merge facts only
(PR #88 merged at `ddd1559f021762316f5a64989a307355acb4aab2` on
2026-09-19 — re-verified against live GitHub at activation):

- (a) `oap/INCREMENTS.md` 078/8 row → "Accepted and merged in PR #88 at
  `ddd1559f021762316f5a64989a307355acb4aab2` on 2026-09-19; 078/8 is
  closed".
- (b) `oap/INCREMENTS.md` `Next` row → standard in-flight form for
  `078-9-a` ("Opened at `078-9-a` from verified remote main
  `ddd1559f021762316f5a64989a307355acb4aab2`; PR pending; strategy owns
  acceptance and merge") plus the ordered 079-bound sentence
  (no further ordinary 078 product increments planned; Gallery,
  LogoGrid, DocumentList, real Image are 079 increments per the human
  directive of 2026-09-20; numeric 078 remains PARTIAL until
  implemented and proven; COMPLETE only after independent
  verification).
- (c) `README.md` capability row: "increment 078/8 (bounded embed
  family) is opened at `078-8-a` (PR #88)" → "increment 078/8 (bounded
  embed family) is accepted and merged in PR #88 at
  `ddd1559f021762316f5a64989a307355acb4aab2` on 2026-09-19"; the
  GitHub-authoritative sentence kept.
- (d) `oap/MVP-PROGRESS.md`: sequence sentence and 078 status row — the
  078/8 "opened at `078-8-a` (PR #88)" clause replaced with the merged
  wording in both; 078 status stays PARTIAL with the 079-bound
  remainder clause.
- (e) `oap/MVP-CONTRACT-AUDIT.md` and `CRITICAL.md` (repository root):
  verify-only —
  `grep -n '078-8-a\|PR #88\|078/8\|layer\|embed' oap/MVP-CONTRACT-
  AUDIT.md CRITICAL.md` returned no stale current-state claim; no edit
  made (within the ordered docs budget).

Durable-wording rule: the merge-fact consistency checker
(`tools/check_repository.py::check_merge_facts`) is green (the new
078/8 row's (SHA, date) pair is recorded in the INCREMENTS ledger and
every scanned multi-SHA paragraph is skipped per the checker's
ambiguity rule); the next merge must not make committed truth false
(the `Next` row uses only the standard in-flight form). Adversarial
sweep: `git grep -n 'opened at \`078-8-a\`'` and `git grep -n 'PR
pending'` over the committed tree return only the ordered in-flight
`Next` row (078-9-a) and the immutable historical transcript — no 078/8
"PR pending" / "opened at `078-8-a`" claim remains.

## R5 evidence — governance hygiene (079-a retirement)

- `git mv oap/orders/079-a-agent-media-semantics.md
  oap/governance/superseded-preplanned/079-a-agent-media-semantics.md`
  — committed as a pure rename:
  `git diff --cached --stat` → `1 file changed, 0 insertions(+), 0
  deletions(-)` (content byte-identical; the move is the supersession
  marker).
- New `oap/governance/superseded-preplanned/README.md` (18 lines):
  why the file moved (unique order-identifier-per-file enforcement in
  `tools/check_repository.py`), that the next activation is `079-a` per
  the human directive of 2026-09-20 (D2), that this preplanned content
  is superseded by the 079 order published when `079-a` is activated,
  and that `080-a`..`091-a` remain inert in `oap/orders/`.
- `080-a`..`091-a` untouched.
- `python tools/check_repository.py` → `PASS repository policy`
  (orders-directory uniqueness restored; `active` `078-9-a` has exactly
  one order) and `npx --yes markdownlint-cli2@0.23.2 "oap/**/*.md"` →
  `0 issues` after the move.

## R6 evidence — hard constraints

- No new dependency: `pyproject.toml` and `uv.lock` byte-identical to
  base; `pnpm-lock.yaml` byte-identical to base (all in the empty-diff
  file set; `uv lock --check` OK; `pnpm install --frozen-lockfile` OK).
- No supply-chain/workflow change: `tools/supply_chain/`,
  `tests/supply_chain/`, `.github/workflows/` untouched; Dependabot PRs
  #75/#83/#84 not touched.
- No new route, port, or scope string: the diff contains no
  route/endpoint/scope changes (verified by inspection of the full
  diff; the only new file with runtime behavior is the unreferenced
  local-execution evidence spec).
- No Alembic migration file: the `060_001` change is the ordered
  in-place catalog regeneration (same revision, same file); migration
  count unchanged.
- No CSP change: the layer values do not affect
  `frame-src` (hosts unchanged); no CSP strings in the diff.
- No provider keys or secrets in the diff or report: the live spec
  records host + pathname only (`grep -c apikey evidence.json` → 0);
  no `apikey`/token/secret strings in the diff; this report quotes
  hosts and path prefixes only.
- License gate: `pnpm licenses list --json` → 8 distinct licenses
  (MIT 207, Apache-2.0 20, ISC 10, CC-BY-4.0 1, BSD-2-Clause 6,
  BSD-3-Clause 3, BlueOak-1.0.0 1, 0BSD 1); no forbidden license class.

## Full Compose smoke (acceptance 5 / R3 environment)

`sh tools/compose/smoke.sh slaif0075a` (disposable fresh stack per run;
fresh volume per run):

- Attempt 1: FAILED at `browser-e2e: project=governance
  contract=puck-editor-round-trip-through-human-editor-api`
  (`governance.spec.ts:709` `dragUntil`) — the documented pre-existing
  Puck-drag VM flake class (078-8-a report: same class hit local
  smoke4 and CI run 35453903907; 078-7-b and 078-5-a recorded the same
  class), occurring while the integration suite was running in
  parallel on this VM. Local re-runs are free per the order's flake
  policy (which governs CI).
- Attempt 2 (same conditions): FAILED at the identical contract and
  line (`line=709`) — same documented class under the same parallel
  load.
- Attempt 3 (after the integration suite completed; VM idle):
  **PASSED** — `browser-e2e: OK` for all 12 projects
  (`compose-e2e: OK projects=12 setup=1 governance=1 preview=1
  preview-filtering=1 stable-devices=6 agent-sessions=2
  artifacts=disabled`), including the corrected
  `bounded-embed-family-renders-canonically-and-rejects-hostile-writes`
  contract (project `preview`) and `public-agent-acceptance: OK` (29
  catalog types), then `compose-smoke: OK`. Zero `FAILED` lines in the
  green run's log. No code fix was applicable or made for the flake
  class; no CI re-run was consumed by it.

The R3 live observation additionally ran on a further fresh disposable
stack (`slaif0075c`) after the green smoke (recorded in R3).

## Local verification

All commands from the repository root; uv `0.12.5`, Node `v24.14.1`,
pnpm `11.22.0`, TypeScript `6.0.3`; integration on the disposable local
PostgreSQL `127.0.0.1:5432` (fake credentials, `PGDATABASE=qualification`
matching CI):

- `uv lock --check` → OK
- `uv sync --frozen --all-groups` → `Checked 44 packages` (no drift)
- `uv run --frozen ruff check services/backend tests/repository
  tests/packaging tests/supply_chain tools migrations` → OK
- `uv run --frozen ruff format --check services/backend
  tests/repository tests/packaging tests/supply_chain tools
  migrations` → OK
- `uv run --frozen mypy` → OK (no findings)
- `uv run --frozen pytest services/backend/tests/unit
  tests/repository` → `594 passed, 1 warning in 26.18s`
- `uv run --frozen pytest services/backend/tests/integration` →
  `235 passed in 2299.28s (0:38:19)`
- `uv run --frozen pytest tests/packaging` → `48 passed, 38 subtests
  passed in 1.21s`
- `uv build --out-dir /tmp/slaif-agent-site-distributions` → built
  `slaif_agent_site-0.0.0.tar.gz` and
  `slaif_agent_site-0.0.0-py3-none-any.whl`
- Four generator `--check` gates → all OK (exact outputs in R1)
- Ten process smokes
  (`python -m slaif_agent_site.<module> --check` for `control_api`,
  `editor_api`, `agent_api`, `render_api`, `mcp_adapter`,
  `media_service`, `review_worker`, `scheduler`, `media_gc`,
  `bootstrap`) → all `CHECK_OK`
- `python -m compileall -q tools tests/repository` → OK
- `python -m unittest discover -s tests/repository -p 'test_*.py'` →
  `Ran 71 tests … OK`
- `python tools/check_repository.py` → `PASS repository policy`
- `python tools/check_mermaid.py` → `PASS Mermaid rendering: 16
  diagram(s) in 3 file(s); 501 Markdown file(s) scanned; CLI 11.16.0`
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` → `0 issues in 0
  files` (494 files)
- Node gate: `pnpm install --frozen-lockfile` OK; `pnpm lint` OK
  (root + `@slaif-agent-site/web`); `pnpm format:check` OK;
  `pnpm typecheck` OK (all workspaces + root + `tests/e2e`);
  `pnpm test` OK (recursive: scope-catalog 8, browser-tool-contracts
  24, component-catalog 8, composition-schema 19, contracts 17,
  renderer-behavior 12 — all passed; `pnpm build` incl. Next.js OK);
  `pnpm licenses list --json` OK (see R6).

## GitHub CI / required checks

20 required checks = 15 CI jobs + 5 CodeQL checks.

Superseded first implementation head `6c223d8` (run 35509721420):

- 14/15 CI jobs success on first attempt;
  `Python 3.13 quality and package` failed in the `astral-sh/setup-uv`
  action BEFORE any code step ran (`Fetching manifest data from
  https://raw.githubusercontent.com/astral-sh/versions/main/v1/uv.ndjson
  … ##[error]fetch failed`; all lint/type/test/build steps `skipped`;
  sibling `Python 3.12`/`3.14` jobs at the same head succeeded) — a
  transient runner network/infrastructure failure, not a code failure.
  The one permitted unmodified re-run was used: `gh run rerun
  35509721420 --failed` → the job passed on attempt 2; that head ended
  15/15 CI.
- CodeQL at that head: all 4 analysis jobs success, but the CodeQL
  summary check FAILED with a genuine new finding:
  `Insecure temporary file` — "Insecure creation of file in the os temp
  dir" at `tests/e2e/live-osm-provider.spec.ts:284` (the
  `/tmp`-derived artifact write). Per the order's flake policy this was
  a real failure → fixed in code (artifact writes moved to the
  Playwright test-results artifacts API; no product code involved),
  re-verified locally on a fresh stack, and pushed as commit `40d9868`.

Implementation head `40d986825556057862bde8a3c3ea11d243463b35`
(run 35511813488): 20/20 required checks `success` at report
publication time — 15/15 CI jobs
(`Repository policy`, `Node contracts`, `Python 3.12/3.13/3.14 quality
and package`, `Foundation PostgreSQL 14/15/16/17/18`,
`Compose and edge packaging`, `Supply-chain evidence`, `Markdown`,
`Mermaid`, `Dependency review`) + 5/5 CodeQL
(`Detect supported languages`, `Analyze (python)`,
`Analyze (javascript-typescript)`, `Analyze (actions)`, `CodeQL`
summary check — no new alerts). No CI re-run was invoked at the
implementation head; the one documented unmodified re-run was consumed
by the documented infrastructure flake at the superseded first head
(disclosed above).

The report-only SELF commit (this report) triggers a fresh 20-check run
for the identical build (a report-only commit changes only this
transcript); strategy independently verifies the SELF head.

## Local setup / dependencies

- Passwordless guest sudo: not required; all setup (disposable
  PostgreSQL, Docker stacks, Playwright browsers present at
  `~/.cache/ms-playwright` chromium 1234 = the pinned revision for
  Playwright `1.62.1`) was executor work.
- No production systems, production data, or production credentials
  touched. All credentials are disposable local/fixture values.
- Disposed: all Compose stacks (`slaif0075a` ×3 runs, `slaif0075b`,
  `slaif0075c`) torn down with `down --volumes --remove-orphans`; all
  setup-token/secret temp files removed after use.
- Local execution of the R3 spec used a throwaway Playwright config in
  `/tmp/oap-078-9a/` (NOT committed; the committed
  `playwright.config.ts` has no project referencing the new spec).

## Documentation

- Durable docs updated in the same PR: `oap/INCREMENTS.md`,
  `README.md`, `oap/MVP-PROGRESS.md` (R4), new
  `oap/governance/superseded-preplanned/README.md` (R5).
- Architecture/constitution/protocol files untouched (the active order
  requires no governance change beyond the ordered R5 retirement note).
- `oap/MVP-CONTRACT-AUDIT.md` / `CRITICAL.md`: verified, no stale
  claim found, no edit (R4e).

## Files changed (base → implementation head, cumulative)

Base `ddd1559f021762316f5a64989a307355acb4aab2` → implementation head
`40d986825556057862bde8a3c3ea11d243463b35` (commits `6c223d8`,
`40d9868`): 17 files, 686 insertions(+), 29 deletions(-).

| File | + / - | Category |
| --- | --- | --- |
| `services/backend/src/slaif_agent_site/content_model/bounded_embed.py` | 1 / 1 | production/config |
| `apps/web/src/renderer/components.tsx` | 1 / 1 | production/config |
| `services/backend/src/slaif_agent_site/content_model/component_catalog.py` | 1 / 1 | production/config (generated) |
| `services/backend/src/slaif_agent_site/db/alembic/versions/060_001_agent_component_semantics.py` | 2 / 2 | production/config + generated (in-place) |
| `services/backend/tests/unit/test_bounded_embed.py` | 14 / 9 | tests/evidence |
| `apps/web/tests/renderer-behavior.test.ts` | 2 / 2 | tests/evidence |
| `tests/e2e/preview.spec.ts` | 4 / 4 | tests/evidence |
| `tests/e2e/live-osm-provider.spec.ts` | 286 / 0 | tests/evidence (new) |
| `packages/component-catalog/src/catalog-v1.json` | 1 / 1 | generated (source) |
| `packages/composition-schema/src/catalog-v1.json` | 1 / 1 | generated |
| `packages/component-catalog/src/index.ts` | 0 / 0 | generated (byte-identical after regen) |
| `contracts/openapi/agent-v1.json` | 0 / 0 | generated (byte-identical) |
| `oap/INCREMENTS.md` | 2 / 2 | docs |
| `README.md` | 1 / 1 | docs |
| `oap/MVP-PROGRESS.md` | 3 / 3 | docs |
| `oap/governance/superseded-preplanned/README.md` | 18 / 0 | docs (new) |
| `oap/orders/079-a-agent-media-semantics.md` → `oap/governance/superseded-preplanned/079-a-agent-media-semantics.md` | 0 / 0 (pure rename, byte-identical) | docs (R5) |
| `oap/orders/078-9-a-osm-layer-contract.md` | 348 / 0 | OAP transcript (strategic, byte-for-byte) |
| `oap/active` | 1 / 1 | OAP transcript (strategic, byte-for-byte) |

(17 tracked content files + the rename pair counted once.)

## Cumulative base→head size (review-unit governance section 2)

Committed-SHA figures, base =
`ddd1559f021762316f5a64989a307355acb4aab2` (verified `main`):

| Segment (committed) | Files | Insertions | Deletions |
| --- | --- | --- | --- |
| 078-9-a implementation (`ddd1559..40d9868`, this report's parent) | 17 | 686 | 29 |
| 078-9-a report (`40d9868..SELF`, this commit) | 1 | (this file) | 0 |

Cumulative grouped per review unit, per 2026-09-14 review-unit
governance section 2 categories:

| Category | Files | Insertions | Deletions |
| --- | --- | --- | --- |
| Production/config | 4 (`bounded_embed.py`, `components.tsx`, `component_catalog.py`, in-place `060_001`) | 5 | 5 |
| Migrations | 0 (the in-place `060_001` regeneration is dually listed under production/config and generated artifacts per the order's own budget; no new migration file) | 0 | 0 |
| Tests/evidence | 4 (all ordered) | 306 | 15 |
| Generated artifacts | 4 (`catalog-v1.json` ×2, `agent-v1.json`, in-place `060_001` dually listed; `index.ts` and `agent-v1.json` regenerated byte-identical → 0/0) | 2 | 2 |
| Docs | 5 (INCREMENTS, README, MVP-PROGRESS, new superseded-preplanned README; the 079-a move is a byte-identical rename) | 24 | 6 |
| OAP transcript | 2 (order + active; the report arrives in this SELF commit) | 349 | 1 |
| **Total** | **17** | **686** | **29** |

Budget check (predeclared, order Section 10): production/config 4 of at
most 4; migrations 0; tests/evidence 4 of at most 4; generated
artifacts 4 of at most 4 (two of the four are byte-identical after
regeneration); docs 4 of at most 4 (+ the R5 rename, which the order
itself prescribes); OAP transcript = order + active + report.
Substantive implementation scale: 686 insertions total of which 286 are
the new ordered evidence spec; all categories within the predeclared
budget. The 17-file cumulative total is below the ~20–30-file review
trigger; no new semantic family was added at any point — the entire
diff is the one ordered maintenance increment plus its ordered
evidence.

## Safety and scope confirmations

- Only the activated order `078-9-a` was executed; no next-order
  choice, no second objective PR, no other PR touched (Dependabot
  #75/#83/#84 untouched).
- The strategic order and `oap/active` were committed byte-for-byte
  unchanged (SHA-256 verified before and after commit:
  `fe9ede16…d0680` / `8debb8e4…eef`).
- No merge, auto-merge, close, or branch deletion performed; strategy
  is the only merger.
- No real secrets, capabilities, cookies, DB URLs, or preview
  credentials committed or printed; fixture credentials only
  (`fixture-compose-auth-password-123` is the repo's documented
  disposable compose fixture, identical to `tools/compose/e2e.sh`).
  No capability, token, or provider API key appears in the diff or
  this report.
- No production systems/data/credentials accessed; no Docker socket
  use beyond the ordered disposable Compose stacks; no unrelated host
  files touched.
- No skips: every claimed suite ran and passed as recorded; the one
  skipped-class event (CodeQL findings) was a genuine finding and was
  fixed in code, not skipped.
- Lockfiles byte-identical to base; no gate/workflow/dependency
  changes; no new route/port/scope/migration/dependency (R6).

## Known limitations / blockers

- None blocking. Disclosed non-idealities: (1) the R3 live spec was
  repaired twice within the round (frame-URL settling; artifact path /
  CodeQL finding) — both repairs confined to the ordered evidence
  file, disclosed with the executing run above, and re-verified on a
  fresh stack with the final code; (2) two of three local smoke
  attempts hit the documented pre-existing Puck-drag flake class under
  parallel integration load — the third (VM-idle) attempt is the green
  record; (3) the one documented CI re-run was consumed by a transient
  `setup-uv` runner network failure at the superseded first head (all
  code steps had not yet run); the implementation head is clean
  without any re-run.
