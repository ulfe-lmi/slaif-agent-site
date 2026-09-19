# OAP Work Order — 078-7-b: build reproducibility repair and current-truth residual (same PR)

- Identifier: `078-7-b` (increment-qualified; continuation round of
  semantic increment 7 of numeric Objective 078)
- PR mode: AMEND_SAME_PR
- Branch: `oap/078-7-a-catalog-content-collection-components`
  (existing; PR #87)
- PR title: unchanged (`OAP 078-7-a: catalog content and collection
  components (CallToAction, ContactBlock, CollectionSearch,
  CollectionFilter, RelatedItems)`)

## Verified current state (verified at activation, from live GitHub and
the current tree only)

- `main` = `2746c9f08c00fd84dff59bfd1536ce7319e16ff9` (unchanged since
  078-7-a activation)
- PR #87 is OPEN; report-only head
  `898360fc74b64fcfc3138ce469ff38cdf95a82b2` over implementation head
  `137abbcacc5a6a129beae2297bc958c949061c72`
- CI run 35434859847 on the report-only head: **19 of 20 required
  checks successful; `Supply-chain evidence` FAILED** at the
  reproducibility assertion
  (`tools/supply_chain/reproducible.py`):
  `Web/browser normalized output manifests differ:
  section=web_distribution
  path=apps/web/.next/standalone/apps/web/.next/server/app/[...sitePath]/
  page_client-reference-manifest.js
  first=sha256=4e5068128c69efca8e59bb66f32f47a31478bc76fb9b6381865429f41c4b69df
  second=sha256=8cc61861e3144402fa093ba07c3cc5f184ac4405cfa9ff24274ebedaac1646f5`
  (both size 8857 bytes)
- The identical code PASSED the same check at the implementation head
  (check run 105873682238, 09:12:57Z-09:23:59Z on
  `137abbcacc5a6a129beae2297bc958c949061c72`). The report-only commit
  adds only this transcript file and cannot change a build, therefore
  the failure is a **probabilistic build nondeterminism introduced by
  the 078-7-a implementation**: the site dynamic route
  (`[...sitePath]`) now carries client references (the bounded
  CollectionSearch/CollectionFilter client-state components) and its
  `page_client-reference-manifest.js` is not byte-stable across
  repeated builds on a loaded runner
- Strategy independently verified at the 078-7-a head: catalog exactly
  22 to 27 with the five expected types; all four generator targets
  zero-diff on re-run; `060_001` diff is the baked JSON plus its SHA
  guard only; versioned OpenAPI canonically byte-identical to the base
  after stripping `x-slaif-*` extensions, 45 to 45 paths, no new scope
  strings, and the only delta is the +19/+19 audit enumerations
  (exactly the 19 new properties of the five new types on the existing
  `/api/agent/v1/components/{component_id}/patch` path using the
  existing `component-content-props:write` scope); fail-closed facet
  validation wired on both Agent and human Puck write paths; renderer
  client-state pattern is `useState`-only with no I/O and native input
  caps; preview route passes `clientState={false}`
- Strategic adjudication of the two recorded 078-7-a deviations, which
  close without rework in this round: (a) the OpenAPI deviation from
  decision 8 is **ACCEPTED** — the literal byte-identity clause
  conflicts with the repository's own frozen drift gates, the
  change is fully characterized and bounded as verified above, the
  decision-8 intent (no new routes, scopes, or documentation) holds
  exactly, and the enumerated-extension growth pattern has precedent
  (078-j/078-k); (b) the PARTIAL browser-proof model is **ACCEPTED**
  as sufficient for increment 078/7 — the production logic module,
  production markup, input caps, and hostile rejections were all
  executed, only the React wiring layer is simulated by the documented
  harness, and an E2E proof of the interactive state machine on a
  data-bearing product surface is architecturally impossible within
  Objective 078 (flight-free preview contract; no
  publication/promotion surface). This limitation is recorded for
  closure when a publication/promotion surface exists
- Residual stale current-truth surfaces found by strategic review that
  the 078-7-a R-doc-1 five-surface definition missed (exact list in
  requirement 2 below)
- Objective 078: increments 078/1-078/6 accepted and merged; numeric
  078 remains PARTIAL

## Strategic rejection of head 898360f (finite checklist)

PR #87 is REJECTED at its current report-only head
`898360fc74b64fcfc3138ce469ff38cdf95a82b2`. The implementation is
otherwise accepted as characterized above. This round closes exactly
two defects; no other scope enters.

1. **D1 (blocking): web build reproducibility regression.** The
   standalone web distribution is not byte-stable across repeated
   builds of the same commit. A green check re-run on the same head is
   NOT acceptable evidence: the gate is probabilistically flaky by
   construction of the defect, and merging it would make the
   supply-chain gate unreliable for every subsequent PR and main run.
   The defect must be repaired and proven.
2. **D2 (blocking): residual stale current-truth surfaces.** Four
   objective-state descriptions remain false after the 078/5 and
   078/6 merges (requirement 2). Known-false current-state prose must
   not reach main.

## Objective

Make PR #87 mergeable: (D1) repair the build nondeterminism on the
site dynamic route's client-reference manifest so the repository's
reproducibility contract holds deterministically, without weakening
any gate; (D2) correct the residual current-truth surfaces with
durable wording per the 078-z governance protocol.

## Bounded scope

- D1: the web build/renderer module boundary only (renderer component
  imports, Next.js/webpack build configuration, or an equivalent
  determinism fix at the build level). The coding agent chooses the
  minimal approach and records the rationale.
- D2: documentation only; exactly the four surfaces in requirement 2.
- The report-only commit for this round and `oap/active`.

## Explicit non-goals

- **No changes to `tools/supply_chain/*`, `tests/supply_chain/*`, or
  `.github/workflows/ci.yml`** — no normalization entries, no path
  exclusions, no assertion relaxation. The fix is in the build, not
  the gate. If after genuine effort the only workable repair lies in
  the supply-chain tooling contract (for example a provably
  semantically identical ordering variance that the existing
  normalization mechanism is designed for), STOP before committing any
  tooling change, do not commit the partial state, and report
  BLOCKED with the full analysis: which bytes differ between two
  divergent builds, why they differ, why they are harmless, and the
  proposed tooling contract change. Strategy adjudicates tooling
  contract changes separately.
- No renderer behavior change: the rendered markup, filtering
  semantics, input caps, static preview variants, and flight-free
  preview contract are unchanged
- No VideoEmbed/MapBlock, no Gallery/LogoGrid/DocumentList, no media
  (078/8 and 079 remain separate)
- No new public endpoint, no new scope, no OpenAPI route or
  enumeration change, no new migration, no dependency or lockfile
  change
- No interaction with Dependabot PRs; no change to `main`; no edit of
  any historical order or report

## Requirements

0. **D1 analysis and repair.** Identify the byte-variation class in
   `apps/web/.next/standalone/apps/web/.next/server/app/[...sitePath]/
   page_client-reference-manifest.js` (capture a real byte diff
   between two divergent local builds if the local environment
   reproduces it; otherwise demonstrate the class from the CI
   evidence and the build internals). Implement the minimal repair so
   the manifest — and the whole `web_distribution` tree — is
   byte-identical across repeated builds of the same commit.
1. **D1 evidence.** (a) Three consecutive full local runs of
   `python -m tools.supply_chain.reproducible --root . --output
   <fresh-directory>` all green (each run performs two Python builds
   and two Node builds); (b) the full local gate green, including the
   full Compose smoke with all 12 browser projects (the
   `preview-filtering` project included); (c) the `Supply-chain
   evidence` check successful on the new exact report-only head in
   GitHub CI.
2. **D2 repair, exactly these surfaces, durable wording only**
   (identify increment/PR and verified merge facts; GitHub remains
   authoritative for live acceptance and merge state; no ephemeral
   wording that becomes false when a PR merges):
   1. `README.md` (Objective-078/4 capability-table row, line ~275):
      the clause "global regions/catalog remain deferred at
      increment `078-5-a`" is false — 078/5 is accepted and merged in
      PR #85 at `2746c9f08c00fd84dff59bfd1536ce7319e16ff9` on
      2026-09-19. State the verified merge fact and that increment
      078/7 is opened at `078-7-a` (PR #87); GitHub authoritative.
   2. `oap/MVP-PROGRESS.md` ("Active and remaining sequence", lines
      ~112-114): "078/1, 078/2, 078/3, and 078/4 are all accepted and
      merged; the next Objective-078 product increment starts at
      `078-5-a`" is false — 078/1 through 078/6 are accepted and
      merged (verified SHAs per `oap/INCREMENTS.md`); increment 078/7
      is opened at `078-7-a` (PR #87); GitHub authoritative.
   3. `oap/MVP-PROGRESS.md` (status table, row 078, line ~122): the
      row ends at 078/4 with "global-region/catalog scope remains
      deferred, starting at `078-5-a`" — extend with the verified
      078/5 (PR #85 at `2746c9f08c00fd84dff59bfd1536ce7319e16ff9`)
      and 078/6 (PR #86 at
      `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`) merge facts and
      state that increment 078/7 is opened at `078-7-a` (PR #87).
   4. `oap/INCREMENTS.md` (the `Next` ledger row, line 23): "Remaining
      078 scope after 078/5" is stale — the remaining scope is after
      078/7.
   No other prose restructuring anywhere.
3. Local verification: full gate (lock/sync/lint/format/typecheck/
   unit/integration/build/contracts) plus the full Compose smoke
   (`sh tools/compose/smoke.sh <project>` run class) end-to-end;
   record exact final status lines. A documented Puck-drag VM flake
   class permits at most one unmodified re-run, documented.
4. Commit the implementation, push, then make the report-only `SELF`
   commit (parent = this round's implementation head), with this
   order and `oap/active` committed byte-for-byte unchanged.

## Observable acceptance criteria

1. D1 proven: the byte-variation class is identified and recorded;
   three consecutive local `tools/supply_chain.reproducible` runs are
   green; no file under `tools/supply_chain/`, `tests/supply_chain/`,
   or `.github/workflows/` changed; the full local gate and Compose
   smoke are green.
2. D2 proven: the four surfaces carry the verified merge facts with
   durable wording; no other prose change; the 078/7 ledger row in
   `oap/INCREMENTS.md` remains the standard "PR pending; strategy
   owns acceptance and merge" line for the in-flight increment.
3. No renderer behavior change: `pnpm test` (including
   `apps/web/tests/renderer-behavior.test.ts`) and the
   `preview-filtering` Playwright project pass with the same
   contracts as 078-7-a; the preview remains flight-free.
4. On the exact new report-only head, all 20 required GitHub checks
   are successful, including `Supply-chain evidence`; the report
   records every check's conclusion.
5. The report contains per-criterion evidence and the cumulative
   base-to-head size grouped per review-unit governance section 2
   (base = `2746c9f08c00fd84dff59bfd1536ce7319e16ff9`).

## Predeclared review budget (review-unit governance section 1)

- Production/config files: at most 5 (renderer module boundary and/or
  Next.js/webpack build configuration; the pure-logic filter module
  may be touched only if the repair requires it and behavior is
  provably unchanged)
- Migrations: 0
- Test/evidence footprint: at most 3 files (determinism or
  regression pins if genuinely necessary)
- Generated-contract footprint: 0 (OpenAPI and catalog unchanged)
- Docs footprint: 4 files (D2 surfaces)
- OAP transcript footprint: order + active + report
- Expected substantive implementation scale: under 1.0k lines
- Review trigger: not expected to fire; if the D1 repair proves
  architecturally larger, STOP and report BLOCKED with the analysis
  rather than expanding scope

## Security

No new authority surface. The D1 repair changes how the build is
assembled, not what the product does: no new routes, scopes,
endpoints, or data access; the client-state pattern remains
I/O-free; the flight-free preview contract is preserved and must
remain verifiable by the existing smoke checks. No secrets in diff or
report.

## GitHub workflow

AMEND_SAME_PR: push the new implementation commit(s) to the existing
branch `oap/078-7-a-catalog-content-collection-components` (PR #87,
title unchanged); the report-only commit is `SELF`; Strategy is the
only merger.

## Report requirements

Standard OAP report template plus explicitly:

- the D1 byte-variation analysis: which bytes differ between two
  divergent builds (or the demonstrated class when local
  reproduction is load-dependent), why the 078-7-a change introduced
  it, the chosen repair and why it is minimal, and why the
  reproducibility contract now holds
- the three consecutive local `tools/supply_chain.reproducible` run
  results (exact command and output lines)
- the D2 before/after for each of the four surfaces
- confirmation that `tools/supply_chain/`, `tests/supply_chain/`, and
  `.github/workflows/` are byte-identical to the 078-7-a head
- the exact final status lines of the full local Compose smoke run
- the conclusion of every one of the 20 required checks on the exact
  new report-only head
- the cumulative base-to-head size grouped per review-unit
  governance section 2 (base =
  `2746c9f08c00fd84dff59bfd1536ce7319e16ff9`)

## Local authority

Standard executor authority in the disposable VM: packages, Docker,
browser tooling, test execution, CI log retrieval. Guest sudo only if
genuinely required; record any use.
