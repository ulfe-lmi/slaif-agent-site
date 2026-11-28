# OAP Coding-Agent Report — 080-a

## Work order

- Identifier: `080-a`; work-order file: `oap/orders/080-a-real-mcp-semantic-parity.md` (canonical bytes, SHA256 `6e347de6c12ed26e2f978479b0c6feee7b21a878e3758e73cd4fc0ed29c40195`, 9182 bytes, committed unchanged); numeric objective 080, increment 080/1
- PR mode: CREATED_NEW_PR

## Status
COMPLETE

## Executive summary
Replaced the dead `/mcp/v1` MCP scaffold with the single `POST /mcp/` endpoint on the MCP 2026-07-28 Streamable HTTP (JSON mode) wire contract, exposing exactly one capability-bound read-only tool, `site.describe`. Every valid request authenticates through the one fixed, quota-charged `GET /api/agent/v1/session` dispatch with its own product capability bearer; responses are `no-store`; audit logging uses fixed fields only and never records the bearer, payload, cookies, the caller-controlled JSON-RPC id, source URLs, or raw upstream output. The old caller-controlled dispatch surface, static `/tools` catalog, and obsolete versioned MCP health stub are removed; retired routes stay 404 publicly and on the service. Full local gates (unit, repository, owned-PG18 integration, 10 process smokes, packaging, Markdown, full frozen Node set, full Compose smoke with all 19 E2E projects) pass, plus an official `mcp==2.3.0` client interchange smoke against the disposable deployment. One draft PR was created; every GitHub CI/CodeQL check on the implementation head passes (below).

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #125, <https://github.com/ulfe-lmi/slaif-agent-site/pull/125>, state OPEN (draft)
- Base branch: `main` (starting remote SHA `f370c647fcca3e4a027b96dbb6d82575d817cbe5`); head branch: `oap/080-a-capability-bound-mcp-discovery`
- Implementation head SHA: `850f98793058352ffffa87d0ac363a1941705a21`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (derived via GitHub after push)
- Implementation commits pushed before report: 2 (`23419e293aa18d97a6925b76e81a9f78afe828ea`, then `850f98793058352ffffa87d0ac363a1941705a21` as a normal follow-up commit; both preserved in branch ancestry, no amend or force-push); report parent = implementation SHA
- New PR this turn: yes (one draft PR); amended existing: no; merge performed: NO

## Changes made

- `services/backend/src/slaif_agent_site/mcp_adapter/mcp_http.py`: removed the old `POST /mcp/v1/call` dispatch surface, custom static `/tools` catalog, and obsolete versioned MCP health stub; implemented the single `POST /` MCP endpoint (2026-07-28 JSON mode): bounded strict-UTF-8 JSON body with top-level field restriction, protocol/header binding (`MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name`), supported-version and method error shapes, `server/discover` / `tools/list` / `tools/call` only, exactly one read-only tool `site.describe` with closed empty arguments, complete `no-store` results with server identity metadata, pre-issued product bearer validated by the pure product `validate_token_format` before the fixed dispatch (no quota consumed on refusal), 401/429 preservation with the Bearer challenge, fail-closed 503 on upstream error/invalid/oversized/timeout without upstream text, Origin refusal before dispatch, and fixed-field audit logging. The concurrency slot is held until the blocking stdlib transport actually ends via an executor-future completion callback (repeated cancellation cannot release early or await a settled future; submission failure releases immediately). Follow-up commit `850f987`: an explicit `null` (or any non-object) `arguments` field is refused with `-32602` instead of being normalized to the empty object (an omitted field remains valid), and the bounded request parse rejects the non-JSON `NaN`/`Infinity`/`-Infinity` literals as parse errors before any dispatch.
- `services/backend/src/slaif_agent_site/mcp_adapter/app.py`: `create_app(settings, readiness_probes, upstream_base, upstream_timeout_seconds, max_upstream_concurrency)` with construction-time validation of the structurally fixed upstream base; `run_mcp_process` keeps `--check` health-only. No `ServiceSettings` field added; no DB class; no runtime httpx.
- `services/backend/src/slaif_agent_site/mcp_adapter/__init__.py`, `__main__.py`: exports and process entry.
- `services/backend/tests/unit/test_mcp_discovery.py` (new): 37 unit/contract tests against the real application with a bounded stdlib HTTP emulation of the one fixed upstream, including focused coverage that explicit-null `arguments` never dispatches and that non-finite JSON constants are refused as parse errors (see Acceptance-criteria evidence).
- `services/backend/tests/unit/test_health_apps.py`: MCP route inventory updated to the single `/` endpoint (shared health routes preserved).
- `tests/e2e/mcp-discovery.spec.ts` (new): three public-NGINX E2E contracts (see Acceptance-criteria evidence).
- `playwright.config.ts`: `agent-desktop-chromium` `testMatch` extended to `(agent-sessions|mcp-discovery)\.spec\.ts`; all 19 E2E projects preserved, no new runner wiring.
- Docs: `docs/API.md` (new capability-bound MCP discovery API section), `docs/SERVICE_AUTHORITY.md` (structural dispatch boundary), `docs/TESTING.md` (080/1 unit/E2E/official-client smoke summary), `docs/user-manual/README.md` (MCP row).
- OAP status: `oap/INCREMENTS.md` and `oap/MVP-PROGRESS.md` record the verified 084/1 merge in PR #124 at `f370c647fcca3e4a027b96dbb6d82575d817cbe5` plus 080/1 in-flight delivery; `oap/MVP-CONTRACT-AUDIT.md` reconciles the MCP row (historical scaffold text preserved; status `SCAFFOLD ONLY` to `PARTIAL`; broader semantic parity left open).
- `oap/active` and `oap/orders/080-a-real-mcp-semantic-parity.md`: committed at canonical bytes (verified SHA256 above; `active` = `080-a\n`).

## Files changed

1. `docs/API.md`
2. `docs/SERVICE_AUTHORITY.md`
3. `docs/TESTING.md`
4. `docs/user-manual/README.md`
5. `oap/INCREMENTS.md`
6. `oap/MVP-CONTRACT-AUDIT.md`
7. `oap/MVP-PROGRESS.md`
8. `oap/active`
9. `oap/orders/080-a-real-mcp-semantic-parity.md`
10. `playwright.config.ts`
11. `services/backend/src/slaif_agent_site/mcp_adapter/__init__.py`
12. `services/backend/src/slaif_agent_site/mcp_adapter/__main__.py`
13. `services/backend/src/slaif_agent_site/mcp_adapter/app.py`
14. `services/backend/src/slaif_agent_site/mcp_adapter/mcp_http.py`
15. `services/backend/tests/unit/test_health_apps.py`
16. `services/backend/tests/unit/test_mcp_discovery.py` (new)
17. `tests/e2e/mcp-discovery.spec.ts` (new)

## Acceptance-criteria evidence
### Criterion 1 — one tool, one transport (scaffold removed, 2026-07-28 JSON mode)

- Result: PASSED.
- Unit (37 tests, all passed): discover/list/call result shapes with `resultType:"complete"`, `supportedVersions:["2026-07-28"]`, `capabilities:{"tools":{}}`, fixed instructions, `ttlMs:0`, `cacheScope:"private"`, server identity metadata; exactly one tool `site.describe` with `inputSchema {"type":"object","additionalProperties":false}` and read-only annotations; text content is canonical compact JSON of the typed structured result.
- Error shapes: unknown method `404 -32601`; header/body protocol mismatch `-32020`; unsupported version `-32022` with `data{supported,requested}`; malformed/missing `Mcp-Method` `-32020`; missing `clientCapabilities` `-32602`; unknown top-level field and notification refusal `400 -32600`; invalid id refusal; strict UTF-8/JSON bounded parse failures `-32700` including a 100,000-element deep-nesting overflow; `Origin` present → `403` before dispatch; non-POST `405` with `Allow: POST`; retired `/mcp/v1/call|tools|health/live` and legacy spellings `404` publicly through NGINX and on the service; shared health and `/mcp/health/ready` preserved (unit + E2E `ready` 200).
- Evidence: `services/backend/tests/unit/test_mcp_discovery.py` (37 tests, all passed); E2E legacy-route and `405` assertions in `tests/e2e/mcp-discovery.spec.ts`.

### Criterion 2 — per-request capability, fixed quota-charged dispatch, no-store, safe logs

- Result: PASSED.
- Unit: exactly one upstream dispatch per valid request carrying its own bearer (path `/api/agent/v1/session`, method GET, no other headers selectable); pre-dispatch bearer structure and product `sas2_` format refusals without any upstream call; upstream `401` → `401` + `WWW-Authenticate: Bearer` with fixed message (no upstream text); upstream `429` → `429 -32600`; upstream error/invalid JSON/oversized/timeout → `503 -32603` without upstream body or path in logs; all responses `Cache-Control: no-store`. (Re-verified on the corrected head.)
- Audit correlation: `_log_mcp_event` logs only the fixed operation class, HTTP status, upstream status, duration, and the validated site/workspace UUIDs; an ordinary caller marker used as the JSON-RPC id is proven absent from every event field and captured log text while the fixed fields are present.
- E2E: the exact finite request-quota budget (REST comparator plus discover, list, call, one more REST = five valid requests against a configured cap of five; the sixth is `429` with `QUOTA_EXCEEDED`, pre-dispatch refusals consume nothing even after exhaustion) and the quota-one proof (first legitimate MCP call succeeds with `structuredContent.request_quota === 1` cap, next MCP call `429 -32600`, REST comparator `429`) both pass through public NGINX; `request_quota` is asserted unchanged (fixed configured cap) across all responses.
- Evidence: unit suite (all passed); E2E contracts 1 and 3 (passed in the full Compose smoke rerun, `compose-smoke-second.log`).

### Criterion 3 — structurally fixed dispatch, bounded input, fail-closed

- Result: PASSED.
- Unit: upstream base is structurally fixed (four invalid injected bases → construction-time `ValueError`); bounded streamed request body (oversized body refused before parse); finite upstream timeout (slow upstream → `503`); bounded upstream response parse (invalid/oversized → `503`); deterministic safe errors only; concurrency slot held until the blocking transport actually ends — repeated cancellation of the handler task before a slow 0.6 s transport finishes cannot release the slot early (second request blocked until completion) and a request after completion proves the slot was released exactly once.
- Evidence: unit suite (all passed on the corrected head), including `test_concurrency_slot_is_held_until_cancelled_transport_ends`.

### Criterion 4 — unit/contract negative fixtures (no dispatch)

- Result: PASSED.
- Bounded negative fixtures for caller-provided dispatch fields (unknown top-level fields, unknown tool name, forbidden/non-empty arguments, explicit-null arguments, invalid cursor), malformed/mismatched protocol metadata, Origin, unknown tool, and unexpected arguments all refuse with the fixed error codes and provably dispatch no upstream request (upstream request counters assert zero additional calls). Each non-finite JSON constant literal (`NaN`, `Infinity`, `-Infinity`) is refused with `-32700` without any upstream call; the omitted-arguments positive call remains dispatching.

### Criterion 5 — public NGINX E2E with real capabilities

- Result: PASSED.
- Three contracts in `tests/e2e/mcp-discovery.spec.ts` run through public NGINX in the `agent-desktop-chromium` project: (1) discover/list/call with the REST comparator verifying the exact approved discovery fields (site, workspace, scopes, catalog/schema versions, constraints, origins, quota cap) under the exact finite budget, retired-route `404`s, `GET` `405`, `/mcp/health/ready` 200, real UI revocation → MCP `401` with Bearer challenge and credential absent from the response body, absent/malformed credential `401`; (2) two independently UI-minted capabilities (L1 and L4 with an approved-origin and `max_content_types:100` constraint) in independent workspaces prove per-request authority and revocation isolation; (3) the quota-one exhaustion proof. All three passed in the full Compose smoke rerun (`browser-e2e: PASSED ... mcp-capability-bound-discovery-list-and-call-through-nginx`, `mcp-per-request-authority-follows-its-own-capability`, `mcp-bounded-request-quota-exhaustion-preserves-429`).
- Official current client interchange: a disposable `mcp==2.3.0` client (isolated venv, credential only in that process environment) completed `server/discover`, `tools/list`, and `site.describe` against the owned deployment over public NGINX: `PASS discovery+list+site.describe@2026-07-28 tools=1`.
- Diagnostic note (honestly preserved): the first full Compose smoke run failed `SMOKE_RC=1` on exactly these three E2E contracts (first `server/discover` returned 400). Root cause was a committed-spec request-builder defect: `mcpBody` spread the `io.modelcontextprotocol/*` metadata keys as siblings of `params` instead of nesting them under `params._meta`, so the adapter correctly answered `400 -32602 params._meta must be an object` (reproduced with the exact wire capture on a fresh stack). The same builder also made the REST `429` assertion expect a JSON-RPC code where the product error envelope (`error.code: "QUOTA_EXCEEDED"`) is returned. Both were corrected in the spec (product code was not at fault); the corrected contracts pass in a fresh-stack targeted rerun (3/3) and in the full Compose smoke rerun (`SMOKE_RC=0`, `compose-e2e: OK projects=19`). The first interchange invocation was also made with a malformed endpoint URL (missing trailing slash; the SDK warned about the redirect and did not follow it) and recorded `SAFE refused:code=-32600`; the corrected invocation against the canonical `http://localhost:8080/mcp/` endpoint produced the PASS line above.

### Criterion 6 — full preserved matrix and gates

- Result: PASSED locally (GitHub CI states below).
- Full Compose smoke rerun `sh tools/compose/smoke.sh slaif007e2e080a`: `SMOKE_RC=0` with `compose-e2e: OK projects=19` — all 19 E2E projects, six stable device profiles, real media approval, 084 overlap proof, retained Heading reads, review-surface and accept/discard lifecycles, two isolated browser worker runs, Apache syntax, deployment/topology/edge/failure smokes, public agent acceptance/restart, and packaging unit tests.
- Full owned-PG18 integration: `uv run --frozen pytest services/backend/tests/integration -q` on the owned disposable PostgreSQL 18.6 fixture (`[::1]:5432`) ran on both pushed heads: first head `23419e2` `475 passed in 4124.72s (1:08:44)` native exit 0 (log `integration-first.log`); corrected head `850f987` rerun `475 passed in 5000.20s (1:23:20)`, native exit 0 (log `integration-second.log`).
- Unit/repository: `uv run --frozen pytest services/backend/tests/unit tests/repository`: 946 passed on the first head; 947 passed (37 MCP tests) on the corrected head.
- Quality/package/process/Markdown/Node: see Local verification.
- All current PostgreSQL 14–18 jobs, the 20 required checks, CodeQL, and fresh six-image supply evidence: GitHub CI on the implementation head (states below).

## Local verification

- `uv lock --check`: PASSED
- `uv sync --frozen --all-groups`: PASSED
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED (re-verified on the corrected head)
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED (re-verified on the corrected head)
- `uv run --frozen mypy`: PASSED (340 files, no errors; re-verified on the corrected head)
- `uv run --frozen pytest services/backend/tests/unit tests/repository` (corrected head): PASSED (947 passed; first head: 946 passed)
- `uv run --frozen pytest services/backend/tests/integration -q` (owned PG18, `PGHOST=::1 PGPORT=5432`): PASSED on first head `23419e2` (475 passed in 4124.72s; log `integration-first.log`, `INTEGRATION_RC=0`); PASSED on corrected head `850f987` (`475 passed in 5000.20s (1:23:20)`; log `integration-second.log`, `INTEGRATION_RC=0`)
- 10 process smokes (`python -m slaif_agent_site.<module> --check` for control_api, editor_api, agent_api, render_api, mcp_adapter, media_service, review_worker, scheduler, media_gc, bootstrap): all `CHECK_OK` (re-run on the corrected head)
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED (re-run on the corrected head)
- `python -m compileall -q tools tests/repository`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED (102 OK)
- `python tools/check_repository.py`: PASSED
- `python tools/check_mermaid.py`: PASSED (16 diagrams)
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED (0 issues)
- `pnpm install --frozen-lockfile`: PASSED (unchanged lock; `node_modules` already present)
- `pnpm lint`: PASSED (re-verified after the E2E spec correction)
- `pnpm format:check`: PASSED (re-verified)
- `pnpm typecheck`: PASSED (re-verified)
- `pnpm test`: PASSED (re-verified)
- `pnpm build`: PASSED (re-verified)
- `pnpm licenses list --json`: PASSED (re-verified)
- `sh tools/compose/smoke.sh slaif007e2e080a` (first run): FAILED (`SMOKE_RC=1`) — diagnostic; cause and correction documented under Criterion 5
- `sh tools/compose/smoke.sh slaif007e2e080a` (rerun on the corrected subject): PASSED (`SMOKE_RC=0`, `compose-e2e: OK projects=19`; log `compose-smoke-second.log`)
- Official `mcp==2.3.0` interchange smoke against the owned deployment over NGINX: PASSED (`PASS discovery+list+site.describe@2026-07-28 tools=1`; credential only in the client process environment; log `interchange-second.log`; first malformed-URL invocation preserved as diagnostic `SAFE refused:code=-32600`)

## GitHub CI / required checks

- CI/CodeQL runs on the superseded first head `23419e2` (CodeQL SUCCESS; CI CANCELLED when the follow-up commit landed) are diagnostic only. The authoritative runs are on the implementation head `850f98793058352ffffa87d0ac363a1941705a21` (CI run 46129951925, CodeQL run 46129951932).
- CI run 46129951925 (conclusion SUCCESS, 25/25 jobs): Supply-chain evidence SUCCESS (fresh six-image supply evidence); Compose and edge packaging SUCCESS (full 19-project E2E matrix through public NGINX plus packaging unit tests, including the three corrected MCP contracts); Node contracts SUCCESS; Repository policy SUCCESS; Markdown SUCCESS; Mermaid SUCCESS; Dependency review SUCCESS; Python 3.12 / 3.13 / 3.14 quality and package SUCCESS; Foundation PG Group A PostgreSQL 14/15/16/17/18 SUCCESS; Foundation PG Group B PostgreSQL 14/15/16/17/18 SUCCESS; Foundation PostgreSQL 14/15/16/17/18 SUCCESS.
- CodeQL run 46129951932 (conclusion SUCCESS): Analyze (actions) SUCCESS; Analyze (javascript-typescript) SUCCESS; Analyze (python) SUCCESS.
- `gh pr checks 125` on the implementation head: every listed check `pass` (31 check runs, zero fail/pending/cancelled at drafting time).
- All required green at drafting: yes (every required check on the implementation head reports pass; the first-head runs are diagnostic/superseded as noted).
- Report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- uv 0.12.5; frozen lock unchanged; no new dependencies (no `pyproject.toml`/`uv.lock`/`pnpm-lock.yaml` changes in these implementation commits).
- Owned disposable PostgreSQL 18.6 fixture at `/tmp/oap-080-a-pg18` on `[::1]:5432` (trust auth, fixture role); the foreign `127.0.0.1:5432` endpoint was never touched.
- Node v24.22.0 with pnpm 11.22.0 (repo-frozen); TypeScript 6.0.3; Docker 29.1.3 with compose 2.40.3; disposable Compose project `slaif007e2e080a` (torn down with volumes after the smoke).
- Official MCP client proof: isolated venv at `/tmp/oap-080-a-peer-client` with `mcp==2.3.0` (not part of the product tree).

## Documentation

- `docs/API.md`: new "Capability-bound MCP discovery API" section (single `POST /mcp/`, 405/404/403 behaviors, pre-issued bearer as the supported strategy, fixed dispatch with quota-once semantics, "request_quota is the fixed configured cap; this resource does not expose remaining consumption", status preservation, error codes, no-store, fixed-field logging with the caller-controlled JSON-RPC id excluded).
- `docs/SERVICE_AUTHORITY.md`: MCP structural boundary — dispatch fixed to `GET /api/agent/v1/session`; requests can never select host/method/path/query/headers beyond the validated bearer.
- `docs/TESTING.md`: 080/1 unit suite, E2E contracts, and official-client smoke summary.
- `docs/user-manual/README.md`: MCP row updated to the single `POST /mcp/` endpoint.
- `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`, `oap/MVP-CONTRACT-AUDIT.md`: 084/1 merge recorded at the verified base; 080/1 in-flight row; MCP audit row reconciled with historical text preserved and broader semantic parity left open.

## Safety and scope confirmations

- Unrelated files changed: no (17 scoped paths only; verified staged set).
- Production secrets accessed: no; production systems accessed: no.
- Required tests skipped/not run: no — every order-required local gate ran; the first Compose smoke failure is preserved and diagnosed, with the corrected rerun passing.
- Scope deviation: no (no new packages, dependencies, migrations, infrastructure, scopes, or tools; no mutating/browser tools; no capability-minting changes).
- Extra objective PR: NO; coding-agent merge: NO (PR remains draft).
- Activated order/active edited: NO (canonical bytes committed, SHA256 verified).
- Report commit changes only this report: yes (staged set verified before commit).
- Credentials: test fixture credentials exist only in the repo-committed E2E secret channel and disposable test process environments; the one-time capability token for the official-client smoke existed only in that client process environment; no credential bytes appear in this report, logs cited, or Git.

## Known limitations / blockers

- The first Compose smoke run (`SMOKE_RC=1`) and the first malformed-URL interchange invocation are diagnostic evidence of the corrected spec defect and endpoint usage; the corrected subject passes the full smoke natively. The CI run on the first implementation head was cancelled by the follow-up push (superseded, diagnostic); the follow-up commit is a normal new commit with no amend and no force-push, keeping every pushed commit in branch ancestry.
- One governance-spec contract (`governance-visible-workflows-negatives-and-privacy`, membership-add step) failed once with a strict-mode violation (two `role="status"` elements) during a standalone diagnostic rerun on a fresh stack; it passed in both full Compose smoke runs. This is an existing-spec timing observation outside the 080-a scope (file untouched by this round); recorded for transparency, no product or spec change made.
- Broader MCP semantic parity (model/content/composition/design/browser tool families, SSE, subscriptions, OAuth discovery) remains open per the order and the contract audit.

## Recommended strategic follow-up
None from the executor. Strategy decides amend/merge on PR #125 after independent review of the report, diff, and CI on the implementation head and SELF.
