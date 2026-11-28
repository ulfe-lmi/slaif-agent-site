# OAP Coding-Agent Report — 080-b

## Work order

- Identifier: `080-b`; work-order file: `oap/orders/080-b-verify-fixed-mcp-audit-fields.md` (canonical bytes, SHA256 `76465fbe60d31a6403d74b2e336f8717fa40be3895c9bbcb3bb0327e597de265`, committed unchanged); numeric objective 080, increment 080/1
- PR mode: AMENDED_EXISTING_PR (one same-PR repair round on PR #125)

## Status
COMPLETE

## Executive summary
Closed the live CodeQL `py/log-injection` finding (alert #13, open on the 080-a synthetic merge `1de69cef0b2b78b3d89bf286113c1dc5af8f4597`, sink `mcp_adapter/mcp_http.py:391`) in source: the audit operation for successful MCP dispatches is now constructed from fixed server literals in each recognized result branch, so no caller-derived method text can reach the `mcp_operation` audit field or the log sink. The focused audit test proves each of the three successful operations (`server/discover`, `tools/list`, `tools/call:site.describe`) emits exactly its fixed literal with the validated site/workspace identities, and that synthetic ordinary caller markers used as the JSON-RPC id never enter any log field or log text. The change is confined to the scoped MCP logger, its focused unit test, and the b transcript. All bounded local gates pass on the b implementation head; the a native subjects (owned-PG18 475-test suite on both a heads, official `mcp==2.3.0` interchange PASS, full Compose smoke `SMOKE_RC=0` with 19 projects) are retained as a-round evidence; GitHub CI and CodeQL on the b head are recorded below.

## CodeQL finding and causal fix

- Live instance: alert #13, rule `py/log-injection`, open on the exact 080-a synthetic merge `1de69cef0b2b78b3d89bf286113c1dc5af8f4597`; the a-round SARIF analysis (2267895158) traces the flow from the parsed caller method (line 449) through the success-path operation expression (line 673) into `event_fields` (line 378) and the `LOGGER.info` sink (line 391). The prior instance, alert #12, was already fixed in a superseded analysis.
- Root cause: the success path computed `operation = f"tools/call:{TOOL_NAME}" if rpc_method == "tools/call" else rpc_method`, so the caller-supplied (string-typed) method text was the logged value for the discover/list branches. Although dispatch is only reached for the three recognized methods, the source-level data flow from caller text to the log sink is real, and the analysis identifies exactly that one flow; the current SARIF identifies no separate identity-field source.
- Fix (source, bounded): each recognized result branch now assigns a fixed server operation literal — `server/discover`, `tools/list`, and `tools/call:site.describe` (the last via the fixed `TOOL_NAME` constant) — and the audit call uses that branch-local literal. No caller-derived text, client RPC id, capability, source URL, raw upstream body, or caller-provided destination reaches audit or diagnostic logging. The typed UUID `site_id`/`workspace_id` fields, the existing request identity, statuses, and duration are unchanged.
- CodeQL workflow, query selection, severity, reporting, checks, and policies are untouched: no dismissal, suppression, exclude rule, disabled check, token, or dependency workaround. The b CodeQL run analyzes the new synthetic merge and its `py/log-injection` outcome is recorded under GitHub CI.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #125, <https://github.com/ulfe-lmi/slaif-agent-site/pull/125>, state OPEN (draft)
- Base branch: `main` (verified `f370c647fcca3e4a027b96dbb6d82575d817cbe5`); head branch: `oap/080-a-capability-bound-mcp-discovery` (same isolated checkout and branch as 080-a)
- Required a head preserved: report-only `f18d7d42cf623e08db390d0d9dd5dc7f1980760b` with sole implementation parent `850f98793058352ffffa87d0ac363a1941705a21`; the a order, a report, and all pushed history are preserved in branch ancestry
- All required checks on the b implementation head are green at drafting: CI run 46139286294 completed `success` with all 25 jobs `success` (including the ten actual PG14–18 matrix jobs and the fresh six-image supply-chain evidence), CodeQL run 46139286287 completed `SUCCESS`, and `gh pr checks 125` reports 30 check runs, all `pass`
- Implementation commits pushed before this report: the b implementation commit `186e4a8a55427b8c37033853197239f520a50ae8` (new commit on the same branch; no force-push, no history rewrite); report parent = b implementation SHA
- New PR this turn: no; amended existing: yes (same branch/PR); merge performed: NO

## Changes made

- `services/backend/src/slaif_agent_site/mcp_adapter/mcp_http.py`: in the successful dispatch section, the audit operation is now a fixed server literal assigned inside each recognized result branch (`server/discover`, `tools/list`, `tools/call:site.describe`); the previous expression that selected the caller's parsed method for the discover/list branches is removed. No other behavior changed: the wire contract, tool set, authorization, fixed Agent API GET, quota, transport bounds, and HTTP status mapping are untouched.
- `services/backend/tests/unit/test_mcp_discovery.py`: the focused audit test `test_logging_correlates_operation_site_and_workspace_only` now performs all three successful operations with three distinct synthetic ordinary caller markers as the JSON-RPC id and asserts that each emits exactly one audit record carrying its expected fixed operation literal, the validated `SITE_ID`/`WORKSPACE_ID`, both statuses, and an integer duration, and that no caller marker, bearer, upstream path, or client info enters any log field or the captured log text. All other a tests are unchanged.
- `oap/orders/080-b-verify-fixed-mcp-audit-fields.md` (new in tree): canonical b order bytes, committed unchanged.
- `oap/active`: canonical `080-b` bytes (6-byte line), committed unchanged.

## Files changed

1. `oap/active`
2. `oap/orders/080-b-verify-fixed-mcp-audit-fields.md` (new)
3. `services/backend/src/slaif_agent_site/mcp_adapter/mcp_http.py`
4. `services/backend/tests/unit/test_mcp_discovery.py`

## Verification

### Bounded local gates on the b implementation head

- `uv run --frozen pytest services/backend/tests/unit/test_mcp_discovery.py -q`: PASSED (37 passed, including the extended audit test)
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED (947 passed)
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED
- `uv run --frozen mypy`: PASSED (340 files, no issues)
- 10 process smokes (`python -m slaif_agent_site.<module> --check` for control_api, editor_api, agent_api, render_api, mcp_adapter, media_service, review_worker, scheduler, media_gc, bootstrap): all `CHECK_OK`
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED (0 issues, 656 files)

### Retained a-round native subjects (unchanged by the b fix)

- Owned-PG18 integration: `475 passed` on implementation head `23419e2` (4124.72s) and on corrected a head `850f987` (5000.20s), both `INTEGRATION_RC=0` (logs `integration-first.log`, `integration-second.log`).
- Official `mcp==2.3.0` interchange smoke: `PASS discovery+list+site.describe@2026-07-28 tools=1` (`interchange-second.log`); credential only in that client process environment.
- Full Compose smoke: `SMOKE_RC=0` with `compose-e2e: OK projects=19` (`compose-smoke-second.log`), including the three MCP NGINX contracts, six stable profiles, real media acceptance, 084 overlap proof, retained Heading reads, two isolated browser runs, and Apache syntax.

### GitHub CI / required checks on the b implementation head

- CI run 46139286294 on the b implementation head `186e4a8a55427b8c37033853197239f520a50ae8` (conclusion `success`, 25/25 jobs `success`): Supply-chain evidence `success` (fresh six-image supply evidence); Compose and edge packaging `success` (full 19-project E2E matrix through public NGINX, including the three MCP contracts, six stable profiles, overlapping review, retained Heading reads, real media acceptance, two isolated browser runs, and Apache syntax, plus packaging unit tests); Node contracts `success`; Repository policy `success`; Markdown `success`; Mermaid `success`; Dependency review `success`; Python 3.12 / 3.13 / 3.14 quality and package `success`; Foundation PG Group A PostgreSQL 14/15/16/17/18 `success`; Foundation PG Group B PostgreSQL 14/15/16/17/18 `success` (the ten actual PG14–18 matrix jobs); Foundation PostgreSQL 14/15/16/17/18 `success`.
- `gh pr checks 125` on the b head: every listed check `pass` (30 check runs, zero fail/pending/cancelled at drafting), including the four CodeQL jobs (Analyze actions, Analyze javascript-typescript, Analyze python, CodeQL aggregate) and Detect supported languages.
- All required green at drafting: yes (every required check on the b implementation head reports pass).
- Report-only commit may trigger fresh checks; strategy verifies SELF.
- CodeQL: b run 46139286287 `SUCCESS` on the b synthetic merge (head `186e4a8a55427b8c37033853197239f520a50ae8`); the live `py/log-injection` instance (alert #13, open on the a synthetic merge `1de69cef0b2b78b3d89bf286113c1dc5af8f4597`) is now `fixed` by the source correction: no open `py/log-injection` instance remains and the b analysis introduced no new instance. Pre-existing unrelated alert #5 (`py/partial-ssrf`, created 2026-08-22, legacy scaffold path) remains open and untouched by this repair.
- The 080-a head runs (CI 46136580734, CodeQL 46136580735, both SUCCESS on `f18d7d4`) remain the a-round check evidence.

### Local setup / dependencies

- uv 0.12.5; frozen lock unchanged; no dependency changes (no `pyproject.toml`/`uv.lock`/`pnpm-lock.yaml` changes in the b commit).
- Owned disposable PostgreSQL 18.6 fixture at `/tmp/oap-080-a-pg18` on `[::1]:5432` retained from the a round (no b-round DB rerun; the retained a native subjects stand and the b head's PG matrix ran via GitHub CI).
- Node v24.22.0 with pnpm 11.22.0 (repo-frozen); pinned `markdownlint-cli2@0.23.2` for the report lint.

### Documentation

- No product documentation changes in the b round: the fix is confined to audit-field construction in the scoped MCP logger and its focused unit test. `docs/API.md` already documents the fixed-field audit logging with the caller-controlled JSON-RPC id excluded, and the b change preserves that documented behavior.

## Safety and scope confirmations

- Unrelated files changed: no (4 scoped paths only; verified staged set).
- The b change is confined to logging and tests plus the b transcript; the public MCP wire contract, tools set, authorization, dispatch, quota, and HTTP behavior are unchanged (a tests preserved and passing).
- No CodeQL dismissal, suppression, exclude rule, disabled check, workflow/query/policy change, token, or dependency workaround.
- Production secrets accessed: no; production systems accessed: no.
- Required tests skipped/not run: no bounded gate skipped; the a native PG18 and official-client subjects are retained by order rather than rerun, and the full Compose/CI matrix reruns on the b head via GitHub CI.
- Extra objective PR: NO; coding-agent merge: NO (PR remains draft).
- Activated order/active edited: NO (canonical b bytes committed, SHA256 verified).
- Report commit changes only this report: yes (staged set verified before commit).
- Credentials: fixture credential hygiene preserved; no credential bytes in this report, in Git, or in the removed owned diagnostic artifacts (080-a cleanup verified by scan).

## Known limitations / blockers

- None. The b repair is the single permitted same-PR repair for the live `py/log-injection` instance.

Implementation head SHA: 186e4a8a55427b8c37033853197239f520a50ae8
Report publication commit: SELF
