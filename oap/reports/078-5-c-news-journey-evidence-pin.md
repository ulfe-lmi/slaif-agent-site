# OAP Coding-Agent Report — 078-5-c

## Work order

- Identifier: `078-5-c` (increment-qualified; third round of semantic
  increment 5 of numeric Objective 078; same-PR continuation of
  `078-5-b`)
- Work-order file: `oap/orders/078-5-c-news-journey-evidence-pin.md`
- Numeric objective: 078 (increment 5)
- PR mode: AMENDED_EXISTING_PR (branch
  `oap/078-5-a-global-regions-header-footer`, PR `#85`)

## Status
COMPLETE (one-line correction implemented exactly as ordered; full local
Compose smoke green end-to-end including `public-agent-acceptance: OK`;
implementation and report pushed to PR #85; remote required checks on
record — the only red check is the documented external Supply-chain CVE
drift, which the order explicitly defers to the 078/6 increment)

## Executive summary
Executed order 078-5-c literally: exactly the one ordered line change in
`tools/compose/public_agent_acceptance.py` (news journey structure
expectation, line 1335, `"navigation": 2` to `"navigation": 3`), line
2067 (component journey) left at `2` as ordered, no other line or file
changed, activated order and `oap/active` committed byte-for-byte
unchanged, implementation pushed to the 078-5-a branch (PR #85 amended).

This correction implements Blocker-B-2 option 1 of the 078-5-b report, as
selected by Strategy: the news journey's browser page is the news detail
page, a child of the news listing page, and the 078-5-a ordered
breadcrumb (binding design decision 5) renders a third
`nav[aria-label="Breadcrumb"]` on pages with an ancestor chain. The
live-captured actual value (`navigation: 3`, all other fields identical)
from the 078-5-b report is now the asserted value.

The full local Compose smoke passes end-to-end for the first time since
078-5-a: all 11 browser projects, `compose-e2e: OK`, and
`public-agent-acceptance: OK`. This confirms (a) the corrected news-journey
pin `3` matches the rendered DOM, (b) the component-journey pin `2` is
correct for the parentless page, and (c) the remainder of the acceptance
journey (stages after the news structure check, not exercised locally
since 077u) passes against the post-078-5-a render surface. The single
required-check red remaining on this increment's head is the documented
external Supply-chain CVE drift (browser-worker image, six
CVE-2026-917xx items), which the order assigns to the separate 078/6
browser security refresh increment.

## Authoritative GitHub state

- Remote `main` = `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba` (verified via
  `git ls-remote origin main` at activation; unchanged at drafting).
- Branch `oap/078-5-a-global-regions-header-footer` before this round:
  `e856034da31d0ff3e6df855a264b24907b4d6191` (078-5-b report-only SELF).
- PR `#85` at activation: OPEN, MERGEABLE, not a draft, base `main`.
- 078-5-b implementation SHA:
  `11cc318490677eef5f885da933b37ef31c4b51ff`; 078-5-b report-only SELF:
  `e856034da31d0ff3e6df855a264b24907b4d6191`.
- 078-5-a implementation SHA (invariant reference):
  `64dea09f49c39acdcd65a84ce9f4968b6268b304`.
- This round's pushed commits (branch head after push):
  `63ca6a77567f71477bd51b9617560cfef387a224` (implementation), then this report (SELF).
- **Literal implementation SHA (this round): `63ca6a77567f71477bd51b9617560cfef387a224`**
- Report publication commit: SELF (this commit; parent =
  `63ca6a77567f71477bd51b9617560cfef387a224`; changes only this report).
- No merge, no auto-merge, no close; PR remains OPEN; Strategy is the
  only merger; the final 20/20 merge gate is deferred to the post-078/6
  round per the order's verification section.

## Changes made (this round)

Exactly the ordered one-line evidence-pin correction (binding decision 1),
no other product/tool/doc/contract/config change:

```diff
diff --git a/tools/compose/public_agent_acceptance.py b/tools/compose/public_agent_acceptance.py
@@ -1332,7 +1332,7 @@ def _run_dynamic_news_edge_journey(
                 },
                 "htmlLang": selected_locale,
                 "main": 1,
-                "navigation": 2,
+                "navigation": 3,
                 "rendererStylesheets": 1,
                 "sections": 0,
             }:
```

Binding decision 2: line 2067 (component journey) remains
`"navigation": 2` — untouched (the component journey page is parentless,
so two navs are its correct post-feature DOM; corroborated by the
live-captured top-level page dict in the 078-5-b report).

## Files changed

This round (`git diff --numstat
e856034da31d0ff3e6df855a264b24907b4d6191..63ca6a77567f71477bd51b9617560cfef387a224`):

- `tools/compose/public_agent_acceptance.py` +1/−1 (the ordered one line)
- `oap/orders/078-5-c-news-journey-evidence-pin.md` +162
  (activated order, committed byte-for-byte unchanged; sha256 pre/post
  commit: `bf8b6f9111fad33e816ca935bd96947352bc5650ba7d838cd357d278571cba17`)
- `oap/active` +1/−1 (content `078-5-c`; sha256 pre/post commit:
  `093b585750cae6d7a57ce748d060822ba7250abc0cd19b414bea6145e1b34b71`)

Plus this report (report-only SELF commit).

## Acceptance-criteria evidence

### Criterion 1 (round diff exactly one line in one file; component
journey line untouched)
PASS. `git diff` between the pre-round branch head and the implementation
SHA touches exactly line 1335 of
`tools/compose/public_agent_acceptance.py`
(`"navigation": 2` to `"navigation": 3`, news journey structure summary);
line 2067 is untouched. Exact diff recorded above.

### Criterion 2 (full local Compose smoke passes end-to-end)
PASS. `sh tools/compose/smoke.sh slaif0075a` (run 2 of 2; completed
2026-09-19 01:20:59 CEST; 1532-line log retained at
`/tmp/smoke-0785c.log`). Exact final status lines:

```text
browser-e2e: OK
browser-e2e: OK
browser-e2e: OK
browser-e2e: OK
compose-e2e: OK projects=11 setup=1 governance=1 preview=1 stable-devices=6 agent-sessions=2 artifacts=disabled
public-agent-acceptance: OK workspace=035bf229-6724-4549-a52f-7a0d63214d24 types=2 fields=3 items=2 translations=1 relations=1 views=1 pages=1 components=1 locales=1 redirects=1 navigations=1 navigation-items=3 theme=schema-default-patch-read-replay openapi=exact restart=verified nginx-outage=verified crud=public quotas=mutation-429,max-delete-429 dependency-delete=422 page-delete-restore=verified canonical-independence=verified render-restart=verified
OK
compose-smoke: OK
```

The four `browser-e2e: OK` wave lines stand for all 20 per-contract
`browser-e2e: PASSED` lines across all 11 projects (every PASSED line
retained verbatim in the log). Note for the record: the first run of this
round (log `/tmp/smoke-0785c-run1.log`) failed before any acceptance
stage at `browser-e2e: FAILED project=governance contract=puck-editor-round-trip-through-human-editor-api line=634 column=20` — the known
Puck drag-interaction VM flake class (same `dragUntil` family as the
078-5-a documented flake at `governance.spec.ts:699`; the failing line is
inside the spec's built-in 4-attempt drag retry helper). It is unrelated
to this round's diff (the acceptance script — the only product-adjacent
line changed — executes after all browser E2E waves and is not used by
any Playwright project). Per the documented flake discipline the run was
re-executed once, unmodified, and passed cleanly; no test or product code
was touched.

### Criterion 3 (report-only head: Compose green; every required check
successful except Supply-chain red solely on documented CVE drift)
PASS at the implementation head (recorded in full below); the report-only
SELF head re-runs the identical matrix (the SELF commit changes only this
report file, which is markdownlint-clean at the pinned CLI version —
0 issues — so the only job sensitive to it, Markdown, is expected green
exactly as on the implementation head). Measured per-check conclusions on
the implementation head, all 20 check runs: **19/20 success** — Analyze
(actions), Analyze (javascript-typescript), Analyze (python), CodeQL,
**Compose and edge packaging**, Dependency review, Detect supported
languages, Foundation PostgreSQL 14, 15, 16, 17, 18, Markdown, Mermaid,
Node contracts, Python 3.12/3.13/3.14 quality and package, Repository
policy — and **1/20 failure: Supply-chain evidence**, solely on the
documented external drift (six CVE-2026-917xx Criticals in the unchanged
browser-worker image; the order assigns resolution to the 078/6 browser
security refresh and defers the PR's final 20/20 merge gate to the
post-078/6 round). The Compose job's CI log proves the corrected pin on
the remote run: `compose-e2e: OK projects=11 ...` followed by
`public-agent-acceptance: OK workspace=94d9cd13-0c37-4588-b223-d559393893fe ...`
(2026-09-18T23:43:14Z / 23:44:21Z). One recorded transient: the first CI
run's Compose job failed before any acceptance stage on the documented
Puck drag VM flake (governance E2E, `governance.spec.ts:699` — the exact
078-5-a documented flake location); the failed job was re-run unmodified
and passed. No code change of any kind resulted from the re-run.

### Criterion 4 (report contains per-criterion evidence and cumulative
size grouped per review-unit governance §2)
PASS. Per-criterion evidence above; cumulative base→head size below.

## Cumulative base→head size (review-unit governance §2)

Committed-SHA figures, base = `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`:

| Segment (committed) | Files | Insertions | Deletions |
| --- | --- | --- | --- |
| 078-5-a implementation (`d576fec..64dea09`) | 48 | 5146 | 74 |
| 078-5-a report (`64dea09..5cf6a2d`) | 1 | 788 | 0 |
| 078-5-b implementation (`5cf6a2d..11cc318`) | 3 | 165 | 3 |
| 078-5-b report (`11cc318..e856034`) | 1 | 468 | 0 |
| 078-5-c implementation (`e856034..63ca6a7`) | 3 | 164 | 2 |
| 078-5-c report (`63ca6a77567f71477bd51b9617560cfef387a224..SELF`, this commit) | 1 | see below | 0 |

This round's delta: one evidence-tool line (+1/−1) and the OAP transcript
(order +162, `oap/active` +1/−1, this report). No production/config file,
migration, generated contract, dependency, or doc change in this round.
Grouping per review unit is unchanged from the 078-5-b report's grouping
(data plane, render projection, scope catalog, composition schema, web
renderer/shell/styles, admin/Puck, generated contracts, tests, docs, OAP
transcript); this round adds only the one evidence-tool line to the
cumulative evidence-tool total (`tools/compose/public_agent_acceptance.py`
at cumulative level: 078-5-b's +2/−2 plus this round's +1/−1 = +3/−3).

Measured cumulative at the 078-5-c implementation head (`git diff
--shortstat d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba..63ca6a77567f71477bd51b9617560cfef387a224`):
**53 files, +6728/−76**. The pairwise segment figures above are not
strictly additive because the single `oap/active` line is rewritten once
per round (each segment diff counts that line's rewrite, the cumulative
diff counts it once); the measured cumulative shortstat is the figure of
record. The report-only SELF commit adds one file (this report).

## Local verification

- `sh tools/compose/smoke.sh slaif0075a` (full run class; ordered
  verification item 1): PASS end-to-end (exact final status lines under
  criterion 2; run 1 flake and single clean re-run documented there).
- `python tools/check_repository.py`: `PASS repository policy`
  (ordered verification item 2), run with the ordered line in place.
- Order+active integrity: sha256 of the order file and `oap/active`
  verified identical before and after the implementation commit (values
  above).

## GitHub CI / required checks

Implementation head `63ca6a77567f71477bd51b9617560cfef387a224` (CI run
35405467301 + CodeQL run 35405467318, triggered by the push; 20 check
runs):

- **Final state after one documented job re-run: 19/20 success**, full
  list under criterion 3; sole failure: `Supply-chain evidence` (external
  CVE drift — see the 078-5-b report's evidence and this order's
  non-goals; deterministic against the current vulnerability database, so
  a retry cannot make it green).
- First-run record (transient): the Compose job failed at `browser-e2e:
  FAILED project=governance contract=puck-editor-round-trip-through-
  human-editor-api line=699 column=34` (job log 2026-09-18T23:27:07Z) —
  the documented Puck drag VM flake location (`governance.spec.ts:699`,
  078-5-a report), aborting the smoke before any acceptance stage; the
  two failed jobs (Compose + Supply-chain) were re-run unmodified via
  `gh run rerun --failed` at 01:39 CEST and settled 01:51 CEST with
  Compose `success` (job log: `compose-e2e: OK projects=11 ...` 23:43:14Z,
  `public-agent-acceptance: OK workspace=94d9cd13-...` 23:44:21Z) and
  Supply-chain `failure` (same six CVEs).
- CodeQL (4 checks) green from the first attempt.
- Report-only SELF head: same 20-check matrix re-executes; the only job
  sensitive to the added file is Markdown (this report, linted locally at
  the pinned CLI version: 0 issues); the same 19/20 pattern is expected
  and the measured conclusions on the exact SELF head are the GitHub
  check runs on that commit (Strategy verifies).
- GitHub CI is authoritative; local success cannot substitute for it.

## Local setup / dependencies

- No new dependencies, no lockfile change, no host package install;
  `uv.lock` and `pnpm-lock.yaml` byte-identical to base.
- Docker/Compose disposable stack only (cached 078-5-a-tree images; the
  round diff touches no image-built surface); browser artifacts disabled
  in the smoke; no hosted service, no production system, no production
  credential touched.
- Guest sudo: not required this round.

## Documentation

- No doc change this round (order non-goal; 078-5-a docs stand as
  published). This report is the only new durable file.

## Safety and scope confirmations

- The ordered one line is applied exactly; line 2067 and every other
  evidence field, journey, and assertion are untouched (git diff is
  exactly one line in the evidence tool).
- No assertion weakening: the pin is corrected to the ordered
  post-feature DOM value proven by live capture (078-5-b report,
  Blocker B-2); the journey still asserts the exact full structure dict.
- No browser-stack, dependency, image, or supply-chain change (the CVE
  drift is the separate 078/6 increment per the order's non-goals).
- No secrets, capabilities, cookies, DB URLs, or private artifact URLs in
  this diff or report.
- No production systems, data, or credentials accessed; no unrelated host
  files touched; no Docker socket usage.
- No merge, no auto-merge, no close of PR #85; no second objective PR; no
  next-order choice made.
- 078-5-a and 078-5-b orders, reports, and all prior transcript history
  immutable and untouched.

## Known limitations / blockers

- `Supply-chain evidence` remains red on this increment's heads due to
  six newly published Critical CVEs in the unchanged browser-worker image
  (CVE-2026-91710/91716/91718/91728/91729/91738) — external
  vulnerability-database drift, unrelated to this increment (documented
  in the 078-5-b report with head-by-head evidence). Per the order's
  non-goals this is the separate 078/6 browser security refresh
  increment; the PR's final 20/20 merge gate is deferred to the
  post-078/6 round (078-5-d).
- The Puck governance E2E drag interaction remains VM-flaky (known class;
  this round's run 1 hit it, run 2 passed). No test change is authorized
  or made in this round.
- Playwright evidence is local Compose (NGINX-fronted) plus the remote CI
  browser matrix; no hosted browser service used.

## Recommended strategic follow-up

Per the order: the PR's final 20/20 merge gate is deferred to the
post-078/6 round (078-5-d), which re-verifies the full matrix after the
browser security refresh (resolving the six CVE-2026-917xx items in the
browser-worker image) merges into main.
