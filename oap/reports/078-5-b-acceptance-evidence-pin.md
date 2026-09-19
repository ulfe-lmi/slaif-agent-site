# OAP Coding-Agent Report — 078-5-b

## Work order

- Identifier: `078-5-b` (increment-qualified; second round of semantic
  increment 5 of numeric Objective 078; same-PR continuation of `078-5-a`)
- Work-order file: `oap/orders/078-5-b-acceptance-evidence-pin.md`
- Numeric objective: 078 (increment 5)
- PR mode: AMENDED_EXISTING_PR (branch
  `oap/078-5-a-global-regions-header-footer`, PR `#85`)

## Status
BLOCKED (ordered two-line change implemented, committed and pushed exactly
as ordered; acceptance criterion 3 cannot pass because the ordered binding
value contradicts the 078-5-a ordered breadcrumb nav on the news journey's
child page — one strategic decision required, Blocker B-2 below)

## Executive summary
Executed order 078-5-b literally: exactly the two ordered line changes in
`tools/compose/public_agent_acceptance.py` (line 1335 news journey and line
2067 component journey, `"navigation": 0` to `"navigation": 2`), no other
line or file changed, activated order and `oap/active` committed
byte-for-byte unchanged, implementation pushed to the 078-5-a branch,
amending PR #85.

The full local Compose smoke run then failed deterministically at
`public-agent-acceptance: FAILED reason=news-browser-structure-evidence-invalid`
(all 11 browser projects and `compose-e2e` green). Per order discipline the
executor did not alter the ordered value. Live diagnostic evidence (fresh
disposable compose stack, current-tree images) proves the ordered pin `2`
is off by exactly one for the news journey page: the actual browser
structure summary is `navigation: 3`, because the news journey's browser
page is the news **detail page**, a child of the news listing page, and the
078-5-a ordered render-time Breadcrumbs (078-5-a binding design decision 5:
"Breadcrumbs derived from the current page's ancestor chain …
`aria-label=\"Breadcrumb\"`") adds a third `nav` to any page with
ancestors. The component journey page has no parent, so its pin `2` is
correct as ordered. Every other evidence field matches the pinned dict
exactly (live-captured).

This round therefore cannot reach acceptance criterion 3 (full smoke green)
or 4 (all 20 required checks green) under the ordered value; the
deterministic failure is in the ordered binding value, not in the
implementation of this order. Blocker B-2 requests the strategic decision:
correct the news-journey pin to `3` (evidence-pin-only follow-up order), or
rule the breadcrumb rendering an implementation defect requiring a bounded
product amendment order. The executor cannot make either choice. A second,
unrelated, out-of-scope failure is also recorded: `Supply-chain evidence`
failed on the implementation head on six newly published Critical CVEs in
the unchanged browser-worker image (external scan-database drift; the same
image passed this check on the 078-5-a head 2026-09-17).

## Authoritative GitHub state

- Remote `main` = `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba` (verified via
  `git ls-remote origin main` at activation; unchanged at drafting).
- Branch `oap/078-5-a-global-regions-header-footer` before this round:
  `5cf6a2d1c88106c0a8228d1b0e1b7c513362291b` (078-5-a report-only SELF).
- PR `#85` state at activation: OPEN, MERGEABLE, base `main` at
  `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`, not a draft.
- This round's pushed commits (branch head after push):
  `11cc318490677eef5f885da933b37ef31c4b51ff` (implementation).
- 078-5-a implementation SHA (invariant reference):
  `64dea09f49c39acdcd65a84ce9f4968b6268b304`.
- **Literal implementation SHA (this round):
  `11cc318490677eef5f885da933b37ef31c4b51ff`**
- Report publication commit: SELF (this commit; parent =
  `11cc318490677eef5f885da933b37ef31c4b51ff`; changes only this report).
- No merge, no auto-merge, no close; PR remains OPEN; Strategy is the only
  merger.

## Changes made (this round)

Exactly the ordered two-line evidence-pin amendment (binding decision 1),
no other product/tool/doc/contract/config change:

```diff
diff --git a/tools/compose/public_agent_acceptance.py b/tools/compose/public_agent_acceptance.py
@@ -1332,7 +1332,7 @@ def _run_dynamic_news_edge_journey(
                 },
                 "htmlLang": selected_locale,
                 "main": 1,
-                "navigation": 0,
+                "navigation": 2,
                 "rendererStylesheets": 1,
                 "sections": 0,
             }:
@@ -2064,7 +2064,7 @@ def _run_component_browser_proof(
             "detailStyle": None,
             "htmlLang": "en",
             "main": 1,
-            "navigation": 0,
+            "navigation": 2,
             "rendererStylesheets": 1,
             "sections": 1,
         },
```

## Files changed

This round (`git diff --numstat
5cf6a2d1c88106c0a8228d1b0e1b7c513362291b..11cc318490677eef5f885da933b37ef31c4b51ff`):

- `tools/compose/public_agent_acceptance.py` +2/−2 (the ordered two lines)
- `oap/orders/078-5-b-acceptance-evidence-pin.md` +162 (activated order,
  committed byte-for-byte unchanged; sha256 pre/post commit:
  `1d2d00afaf1033b2c8692f350c50496b6f852b76682092565bd3fe362d3cde6d`)
- `oap/active` +1/−1 (content `078-5-b`; sha256 pre/post commit:
  `aff9d45a134bdba49b252affd7f472405c420bf86e56142512b68367846ed56e`)

Plus this report (report-only SELF commit).

## Acceptance-criteria evidence

### Criterion 1 (round diff exactly two lines in one file)
PASS. `git diff` between the pre-round branch head and the implementation
SHA touches exactly the two ordered lines in
`tools/compose/public_agent_acceptance.py` (line 1335, line 2067), both
`"navigation": 0` → `"navigation": 2`. Exact diff recorded above.

### Criterion 2 (no other file touched by this round)
PASS. The implementation commit contains only the two-line evidence-tool
change plus the OAP transcript (order + `oap/active`), which the order's
bounded scope explicitly allows ("OAP transcript: this order, `oap/active`,
this report"). No product code, migration, config, generated contract,
lockfile, workflow, or doc file is touched.

### Criterion 3 (full local Compose smoke passes end-to-end)
FAIL — deterministic, caused by the ordered binding value itself (see
Blocker B-2 for the live evidence). Exact final status lines of
`sh tools/compose/smoke.sh slaif0075a` (run 2026-09-19 00:01 CEST,
current tree with the ordered two-line change in effect; log retained as
`/tmp/smoke-0785b.log`, 792 lines):

```text
compose-policy: OK
membership-fixtures: OK count=2 kind=OIDC authenticatable=no installation=uninitialized
compose-mode-policy: OK long-running-backends=9 mode=development
browser-worker-runtime-policy: OK uid=10001 readonly=yes caps=SYS_CHROOT limits=exact network=browser
browser-worker-image-policy: OK playwright=1.62.1 cft_revision=1681091 chromium=153.0.8010.36 browsers=chromium-only package-manager=absent
browser-e2e: OK
browser-e2e: OK
browser-e2e: OK
browser-e2e: OK
compose-e2e: OK projects=11 setup=1 governance=1 preview=1 stable-devices=6 agent-sessions=2 artifacts=disabled
public-agent-acceptance: FAILED reason=news-browser-structure-evidence-invalid
```

The four `browser-e2e: OK` wave lines stand for the 20 per-contract
`browser-e2e: PASSED` lines across all 11 projects (setup; governance ×2
contracts; preview ×7 contracts incl. both global-regions contracts;
desktop-chromium/desktop-firefox/desktop-webkit/tablet/mobile-chromium/
mobile-webkit; agent-desktop-chromium + agent-mobile-chromium ×2 contracts
each); every PASSED line is retained verbatim in the 792-line log.
`compose-e2e: OK`. The failure is the single deterministic assertion
identified in Blocker B-2; it is the same failure point as the 078-5-a
head, now reached with the ordered pin `2` instead of `0` because the
actual value on the news detail page is `3`.

### Criterion 4 (every required GitHub check successful on report-only head)
NOT SATISFIED under the ordered value. Observed on the implementation head
(all 20 check runs complete): 18/20 successful; `Compose and edge
packaging` failed at the same deterministic
`news-browser-structure-evidence-invalid` assertion (identical mechanism,
same run class as CI); `Supply-chain evidence` failed on six newly
published Critical CVEs in the unchanged browser-worker image — an
external scan-database drift, not a regression of this round (evidence
under "GitHub CI / required checks"). The round diff is two
evidence-pin lines; no product/dependency/workflow surface changed.

### Criterion 5 (report contains per-criterion evidence and cumulative
size grouped per review-unit governance §2)
PASS. Per-criterion evidence above; cumulative base→head size below.

## Cumulative base→head size (review-unit governance §2)

Committed-SHA figures, base = `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`:

| Segment (committed) | Files | Insertions | Deletions |
| --- | --- | --- | --- |
| 078-5-a implementation (`d576fec..64dea09`) | 48 | 5146 | 74 |
| 078-5-a report (`64dea09..5cf6a2d`) | 1 | 788 | 0 |
| 078-5-b implementation (`5cf6a2d..11cc318`) | 3 | 165 | 3 |
| 078-5-b report (`11cc318..SELF`, this commit) | 1 | see below | 0 |

Grouped per review unit at the 078-5-b implementation head
(`d576fec..11cc318`, 51 files, +6098/−76):

- OAP transcript (orders + active + reports): 252 + 162 + 788 + 1/1 (the
  single `oap/active` line is counted once at cumulative level)
- Evidence tool (078-5-b, this round): `tools/compose/public_agent_acceptance.py` +2/−2
- 078-5-a production/config data plane (migration, region models, service,
  bootstrap, privileges, route_policy, Python catalog, agent_state,
  agent_http): 738 + 294 + 43 + 1 + 10 + 40 + 2/2 + 37 + 11 + 46 = 1222
- 078-5-a render projection (Python): 270
- 078-5-a scope catalog (TS + test): 1 + 2/1
- 078-5-a composition schema (module + export + test): 206 + 1 + 108
- 078-5-a web renderer/shell/styles/tests: 190 + 202/13 + 25 + 3/2 + 6/1 + 6/2 + 110
- 078-5-a admin/Puck (editor + api client): 254/1 + 32
- 078-5-a generated contracts (OpenAPI): 477
- 078-5-a tests (backend unit/integration + Playwright): 223 + 809 + 468 + 36 pin-change lines
- 078-5-a docs (README + 3 OAP ledgers): 8/6 + 4/3 + 5/5 + 3/2

This round's delta is confined to: one evidence-tool file (+2/−2) and the
OAP transcript (order +162, `oap/active` +1/−1, this report). No
production/config file, migration, generated contract, dependency, or doc
change in this round.

## Blocker (strategic decision required)
### B-2 — ordered pin `2` contradicts the 078-5-a ordered breadcrumb nav
on the news journey's child page (actual `navigation` = 3)

The order's premise — "two `nav` elements per page under the ordered
defaults" — holds for pages without ancestors, but not for pages with an
ancestor chain. The news journey's browser page is exactly such a page, so
the ordered pin cannot pass; the component journey's pin is correct.

**Live evidence (disposable compose stack `slaif007dbg2`, 2026-09-19
00:13–00:21 CEST; backend/web images cached from the current tree, i.e.
identical 078-5-a render code as implementation head `64dea09`; setup
stage passed; the `governance` evidence site fixture was created and left
ACTIVE — one governance sub-test failed on residual state from an aborted
first attempt and is irrelevant to the news journey, which uses the
`demo` site; stack torn down afterwards).**

1. Actual `structure-summary` evidence for the news journey browser page
   (route `/s/demo/sl-si/news-<tag>/published`, workspace preview render of
   the sl-SI news detail page) — captured verbatim from the
   `public_agent_acceptance.py` artifact verification path:

   ```json
   {
     "articles": 1,
     "collectionDetails": 1,
     "components": 1,
     "detailStyle": {
       "borderTopStyle": "solid",
       "display": "block",
       "paddingTop": "24px"
     },
     "htmlLang": "sl-SI",
     "main": 1,
     "navigation": 3,
     "rendererStylesheets": 1,
     "sections": 0
   }
   ```

   Every field except `navigation` is byte-identical to the ordered pinned
   dict; the sole mismatch is `navigation`: actual `3` vs ordered pin `2`.

2. Actual `structure-summary` for the top-level (parentless) theme journey
   page captured in the same run: `navigation: 2` — confirming the order's
   premise for parentless pages.

3. Rendered page HTML (same page, captured from the identical preview URL
   the browser run targets) contains exactly three `nav` elements:

   ```html
   <main class="renderer-surface …" lang="sl-SI" data-render-mode="preview" aria-labelledby="page-title">
   <nav aria-label="Breadcrumb" class="renderer-region-breadcrumbs">
   <ol>
   <li>
   <a href="../../sl-SI/news-<tag>">Novice</a>
   </li>
   <li aria-current="page">Podrobnosti</li>
   </ol>
   </nav>
   <h1 id="page-title">Podrobnosti</h1>
   <div data-component="CollectionDetail">
   …
   </main>
   ```

   The extra nav is the site breadcrumb; it links the parent listing page
   ("Novice", the sl-SI news listing) and marks the current detail page
   ("Podrobnosti") non-linked, exactly as 078-5-a binding design decision 5
   specifies. The header contributes `nav[aria-label="Site"]` (default
   institutional header has one site-key entry; the projection requires
   1–12 header entries) and `nav[aria-label="Language"]` (always rendered);
   the default single-column footer has zero links and an empty note, so it
   contributes no nav.

**Root cause (all in shipped 078-5-a code, implementation head `64dea09`):**

- The news journey creates the detail page as a child of the listing page
  (`"parent_id": listing_id`, acceptance script), so the rendered page has
  a non-empty ancestor chain.
- `renderProjection` (apps/web/src/renderer/components.tsx) renders
  `SiteBreadcrumbs` — `nav[aria-label="Breadcrumb"]` — whenever
  `projection.ancestors.length > 0`.
- `projection.ancestors` comes from `content.slaif_page_ancestor_chain`
  (render_api/projection.py), which walks `parent_id` over the COW view
  `content.page`; in the workspace preview render the session GUC
  (`app.session_id`) is set to the workspace UUID, so both the detail page
  and its parent listing (workspace overlay rows) are visible and the chain
  returns the listing.
- Order 078-5-a binding design decision 5 explicitly mandates this
  behavior: "Breadcrumbs derived from the current page's ancestor chain
  (localized titles, ancestor pages linked via their effective routes,
  current page final and non-linked, `aria-label=\"Breadcrumb\"`)". The
  078-5-a implementation is order-compliant; the third nav is ordered
  product behavior, not a regression.

**Recorded correction of the 078-5-a report (for Strategy's record only;
the immutable 078-5-a report is not rewritten):** its Blocker B-1 section
stated that "the checked pages have no ancestors, so no breadcrumb nav".
That is true of the component journey page but false of the news journey
page, which is a child page; the news detail page renders the breadcrumb
nav. This round's live evidence supersedes that claim.

**Component journey (line 2067):** its page is created without a parent, so
ancestors are empty and no breadcrumb renders; the ordered pin `2` is
correct as-is (corroborated by the live-captured top-level page dict).

**Requested strategic decision (one of):**

1. **Correct the evidence pin** (recommended minimal path): a follow-up
   order (e.g. `078-5-c`, AMENDED_EXISTING_PR, same branch/PR) changing
   line 1335 only, `"navigation": 2` → `"navigation": 3`, leaving line 2067
   at `2`. No product change; the full smoke and the `Compose and edge
   packaging` check are then expected green (all other fields live-verified
   matching above).
2. **Rule the breadcrumb an implementation defect** against 078-5-a
   decision 5 and issue a bounded product amendment order for the PR (e.g.
   suppress the breadcrumb in this render context, or otherwise reconcile
   decision 5 with the two-nav premise). The executor cannot make this
   product/architecture call; if chosen, the evidence pins must then be
   re-pinned against the amended DOM in a further evidence round.

No other evidence field, journey, or assertion is affected; no product
code change is made or needed in this round.

## Local verification

- `sh tools/compose/smoke.sh slaif0075a` (full run class of the 078-5-a
  report; ordered verification item 1): status lines recorded under
  criterion 3 — all 11 browser projects PASS, `compose-e2e: OK`,
  `public-agent-acceptance: FAILED reason=news-browser-structure-evidence-invalid`
  (deterministic; Blocker B-2).
- `python tools/check_repository.py`: `PASS repository policy` (ordered
  verification item 2).
- Diagnostic live capture (Blocker B-2): disposable compose stack
  `slaif007dbg2` (`docker compose -p slaif007dbg2 up -d --wait`, all
  services healthy), setup stage passed
  (`browser-e2e: PASSED project=setup`) and the `governance` fixture site
  created, then the acceptance journey driven
  from the working tree with an evidence-capture wrapper (captures the
  parsed structure-summary dicts and the rendered page HTML; no repo file
  modified). Stack torn down (`down -v`) after capture.
- Order+active integrity: sha256 of the order file and `oap/active`
  verified identical before and after the implementation commit (values
  above).

## GitHub CI / required checks

Drafting-time state on implementation head
`11cc318490677eef5f885da933b37ef31c4b51ff` (CI run 35401349705 + CodeQL
run 35401349704, both triggered by the push; all 20 check runs complete):

- **18/20 successful**: Analyze (actions), Analyze
  (javascript-typescript), Analyze (python), CodeQL, Dependency review,
  Detect supported languages, Foundation PostgreSQL 14, 15, 16, 17, 18,
  Markdown, Mermaid, Node contracts, Python 3.12/3.13/3.14 quality and
  package, Repository policy.
- **2/20 failed**:
  - `Compose and edge packaging` — deterministic, Blocker B-2. Failing
    step "Run clean deployment, topology, edge, and failure smoke", job
    log lines (2026-09-18T22:28:47Z / 22:29:02Z):

    ```text
    compose-e2e: OK projects=11 setup=1 governance=1 preview=1 stable-devices=6 agent-sessions=2 artifacts=disabled
    public-agent-acceptance: FAILED reason=news-browser-structure-evidence-invalid
    ```

    Same assertion and same all-11-projects-green context as the local
    run; the failure is the ordered pin value, not the implementation of
    this order.
  - `Supply-chain evidence` — out-of-scope external failure, NOT caused
    by this round's diff. Failing step "Build reproducible artifacts,
    SBOMs, scans, and evidence", job log line (2026-09-18T22:34:41Z):

    ```text
    supply-chain-evidence: ERROR: browser-worker: unexcepted Critical vulnerabilities: CVE-2026-91710, CVE-2026-91716, CVE-2026-91718, CVE-2026-91728, CVE-2026-91729, CVE-2026-91738
    ```

    Six newly published Critical CVEs in the unchanged browser-worker
    image (scan-database drift, "moving target" class). The identical
    browser-worker image and check passed on the 078-5-a report head
    `5cf6a2d1c88106c0a8228d1b0e1b7c513362291b` (CI run 35194386018,
    completed 2026-09-17T07:24Z: `Supply-chain evidence success`);
    078-5-a's 48-file diff and this round's 2-line diff touch no
    browser-worker, dependency, lockfile, or image surface. Resolving
    it requires a dependency/image or scan-policy decision (strategic
    scope; e.g. a Playwright/browser-worker update order or an explicit
    policy exception). Flagged here for Strategy alongside B-2; a plain
    job retry against the current CVE database would fail identically.
- 0 pending, 0 skipped, 0 cancelled on the implementation head.
- Report-only SELF head: the same 20 check runs re-execute; the same two
  failures are expected (Compose deterministic; Supply-chain
  deterministic against the current CVE database) while all other 18 are
  expected green — the SELF commit changes only this report file, which
  is markdownlint-clean (linted locally at the pinned CLI version before
  commit).
- GitHub CI is authoritative; local success cannot substitute for it.

## Local setup / dependencies

- No new dependencies, no lockfile change, no host package install;
  `uv.lock` and `pnpm-lock.yaml` byte-identical to base.
- Docker/Compose disposable stack only; browser artifacts disabled in the
  smoke; no hosted service, no production system, no production
  credential touched.
- Guest sudo: not required this round (images already built and cached
  during 078-5-a).

## Documentation

- No doc change this round (order non-goal; 078-5-a docs stand as
  published). This report is the only new durable file.

## Safety and scope confirmations

- The ordered two lines are applied exactly; the executor did NOT
  unilaterally change the ordered binding value to the observed actual
  (`3`) — that is a strategic decision (Blocker B-2).
- No other evidence field, journey, or assertion changed (git diff is
  exactly two lines; live-captured dict confirms every other field
  matches).
- No assertion weakening: the pins remain exact-structure assertions; this
  round neither loosened nor tightened any check beyond the ordered bytes.
- No secrets, capabilities, cookies, DB URLs, or private artifact URLs in
  this diff or report (fixture identifiers only; captured HTML contains a
  per-run workspace tag slug, not a UUID, and no credential material).
- No production systems, data, or credentials accessed; no unrelated host
  files touched; no Docker socket usage.
- No merge, no auto-merge, no close of PR #85; no second objective PR; no
  next-order choice made.
- 078-5-a order, 078-5-a report, and all prior orders/reports/active
  history immutable and untouched.

## Known limitations / blockers

- Blocker B-2 (above) blocks acceptance criteria 3 and 4 until Strategy
  decides between the two options; the round is otherwise complete.
- `Supply-chain evidence` is red on the implementation head due to six
  newly published Critical CVEs in the unchanged browser-worker image
  (CVE-2026-91710/91716/91718/91728/91729/91738) — external
  vulnerability-database drift, not caused by this round or 078-5-a (both
  diffs leave browser-worker/dependency/image surfaces untouched; the same
  check passed on the 078-5-a head). Out of this round's bounded scope;
  requires a strategic dependency or scan-policy decision.
- The acceptance journey's structure pins are exact-dict assertions: any
  future ordered DOM change to rendered shells (regions, breadcrumbs,
  switcher) must be accompanied by a corresponding ordered evidence-pin
  round to keep the Compose check meaningful.
- Playwright evidence is local Compose (NGINX-fronted) plus the remote CI
  browser matrix; no hosted browser service used.

## Recommended strategic follow-up

- Preferred: `078-5-c` (AMENDED_EXISTING_PR, same branch/PR) ordering the
  single line 1335 correction `"navigation": 2` → `"navigation": 3`
  (line 2067 stays `2`), which the live evidence shows is sufficient for a
  fully green full smoke and `Compose and edge packaging`.
- Alternative: bounded product amendment order per option 2 of Blocker
  B-2, if Strategy rules the breadcrumb rendering a defect of the 078-5-a
  implementation.
